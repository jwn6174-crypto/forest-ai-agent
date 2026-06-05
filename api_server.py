"""
api_server.py — MOFOM AI Bridge: Python modules ↔ Next.js frontend

FastAPI 서버.  POST /analyze 엔드포인트로 ForestAnalysisResult JSON 반환.

모듈 연동 현황:
  Module A  PNU → 임야 상태 (지역별 mock, 실제 위성 모듈 대기)
  Module B  growth_predict()   ← 연동 완료
  Module C  Faustmann-Hartman NPV/6 시나리오/Pareto/추천  ← 연동 완료(D127)
            stand_adapter → compute_lev_with_plan → ui_adapter 흐름.
            오류 시에도 A·B·D 결과 보존(graceful degradation).
  Module D  market_snapshot(), cost_function()  ← 연동 완료

실행:
  python api_server.py
  또는
  uvicorn api_server:app --port 8001 --reload
"""

import os
import sys
import random
from functools import lru_cache
from pathlib import Path
from datetime import date

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# forest-ai-agent 루트를 Python 경로에 추가
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from module_bd.src.growth_predict import growth_predict
from module_bd.src.market_snapshot import market_snapshot


@lru_cache(maxsize=4)
def _market_snapshot_cached(date_iso: str):
    """market_snapshot 은 호출마다 data.go.kr 에 KAU 라이브 14회 요청(약 3.8s)을
    보낸다. 같은 날짜면 결과가 동일하므로 날짜별 1회만 실호출하도록 메모이즈해
    /analyze 가 요청마다 그 지연을 반복하지 않게 한다(D128 과 동일 처리)."""
    return market_snapshot(date_iso)

# Module C — Faustmann-Hartman 경제성 분석 (희도 D127 통합)
from module_c.src import stand_adapter, ui_adapter
from module_c.src.compute_lev import compute_lev_with_plan

app = FastAPI(title="MOFOM AI Bridge", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _warm_caches() -> None:
    """서버 부팅 시 무거운 1회성 비용을 모두 미리 치러 둔다 — 첫 사용자 요청이
    cold start 를 기다리지 않게 한다(약 10s → 부팅 때 1회). 데우는 대상:
      · api_server·lev_core 양쪽 market_snapshot 캐시(KAU 라이브 fetch 3.8s)
      · 임분수확표 로드 + growth_predict 캐시
      · Module C 전체 파이프라인(compute_lev_with_plan) + offset RAG 로드
    """
    try:
        _market_snapshot_cached(date.today().isoformat())      # api_server 경로 캐시
        # Module C 전체 파이프라인을 한 번 돌려 lev_core 의 market("2026-05-20")·
        # growth 캐시와 offset RAG 까지 모두 데운다(작은 샘플로 충분).
        warm_fs = {
            "pnu": "4374033021100010000", "species": "강원지방소나무",
            "estimatedAge": 50, "areaHa": 2.0, "volumePerHa": 281.0,
            "volumeUncertainty": 42.0, "carbonPerHa": 132.0, "siteIndex": 15,
            "dataWarning": None,
        }
        warm_stand = stand_adapter.from_forest_state(warm_fs)
        warm_pkg = compute_lev_with_plan(warm_stand, n_samples=8)
        ui_adapter.to_ui_offset_eligibility(warm_pkg)          # RAG 인용 로드
        print("[startup] 캐시 워밍 완료 — 첫 요청 cold start 제거")
    except Exception as e:  # 워밍 실패해도 서버는 정상 기동(요청 시 lazy 로드)
        print(f"[startup] 캐시 워밍 건너뜀: {e}")


# ─── Module A Mock: PNU → 임야 상태 ──────────────────────────────────────────

REGION_PROFILES = {
    "11": {"species": "강원지방소나무", "site_index": 12, "age": 45, "forest_type": "침엽수", "slope": "급",  "lat": 37.50, "lng": 128.50},
    "23": {"species": "잣나무",         "site_index": 14, "age": 38, "forest_type": "침엽수", "slope": "중",  "lat": 38.00, "lng": 127.80},
    "42": {"species": "낙엽송",         "site_index": 14, "age": 35, "forest_type": "침엽수", "slope": "중",  "lat": 37.20, "lng": 128.20},
    "43": {"species": "강원지방소나무", "site_index": 10, "age": 50, "forest_type": "침엽수", "slope": "급",  "lat": 37.40, "lng": 128.60},
    "44": {"species": "잣나무",         "site_index": 12, "age": 42, "forest_type": "침엽수", "slope": "중",  "lat": 36.80, "lng": 127.70},
    "45": {"species": "리기다소나무",   "site_index": 10, "age": 38, "forest_type": "침엽수", "slope": "완",  "lat": 36.50, "lng": 127.50},
    "46": {"species": "편백",           "site_index": 14, "age": 32, "forest_type": "침엽수", "slope": "완",  "lat": 34.80, "lng": 126.90},
    "47": {"species": "낙엽송",         "site_index": 12, "age": 30, "forest_type": "침엽수", "slope": "중",  "lat": 35.90, "lng": 128.10},
    "48": {"species": "강원지방소나무", "site_index": 12, "age": 45, "forest_type": "침엽수", "slope": "중",  "lat": 35.50, "lng": 128.40},
    "51": {"species": "잣나무",         "site_index": 14, "age": 40, "forest_type": "침엽수", "slope": "급",  "lat": 37.90, "lng": 127.40},
}

DEFAULT_PROFILE = {
    "species": "강원지방소나무", "site_index": 12, "age": 45,
    "forest_type": "침엽수", "slope": "중", "lat": 37.50, "lng": 128.00,
}

SPECIES_DEFAULTS = {
    "강원지방소나무": {"area_ha": 1.2, "distance_km": 15},
    "잣나무":         {"area_ha": 0.9, "distance_km": 12},
    "낙엽송":         {"area_ha": 1.5, "distance_km": 10},
    "리기다소나무":   {"area_ha": 2.0, "distance_km":  8},
    "편백":           {"area_ha": 0.8, "distance_km":  6},
}


def mock_module_a(pnu: str) -> dict:
    """PNU → 지역별 임야 프로파일 (Module A 대체)."""
    prefix = pnu[:2] if len(pnu) >= 2 else "43"
    profile = REGION_PROFILES.get(prefix, DEFAULT_PROFILE).copy()

    rng = random.Random(sum(ord(c) for c in pnu))
    profile["age"]         = max(20, profile["age"] + rng.randint(-5, 5))
    defaults = SPECIES_DEFAULTS.get(profile["species"], {"area_ha": 1.0, "distance_km": 15})
    profile["area_ha"]     = round(defaults["area_ha"] + rng.uniform(-0.2, 0.3), 2)
    profile["distance_km"] = defaults["distance_km"] + rng.randint(-2, 5)
    return profile


# ─── 등급별 재적 비율 추정 (Module B 출력 보완용) ─────────────────────────────

def estimate_grade_dist(dbh_cm: float) -> dict:
    """흉고직경(cm) → 6등급 재적 비율(%) 추정. GrowthForecast.gradeDistributionByYear 용."""
    if dbh_cm < 10:
        return {"teukYongJae": 0,  "grade1":  0, "grade2":  0, "grade3":  5, "wonJuJae": 25, "wonRyoJae": 70}
    if dbh_cm < 14:
        return {"teukYongJae": 0,  "grade1":  0, "grade2":  2, "grade3": 15, "wonJuJae": 43, "wonRyoJae": 40}
    if dbh_cm < 18:
        return {"teukYongJae": 0,  "grade1":  3, "grade2": 10, "grade3": 28, "wonJuJae": 42, "wonRyoJae": 17}
    if dbh_cm < 22:
        return {"teukYongJae": 1,  "grade1": 10, "grade2": 25, "grade3": 38, "wonJuJae": 22, "wonRyoJae":  4}
    if dbh_cm < 26:
        return {"teukYongJae": 2,  "grade1": 20, "grade2": 30, "grade3": 32, "wonJuJae": 14, "wonRyoJae":  2}
    if dbh_cm < 30:
        return {"teukYongJae": 4,  "grade1": 30, "grade2": 32, "grade3": 24, "wonJuJae":  9, "wonRyoJae":  1}
    return     {"teukYongJae": 7,  "grade1": 40, "grade2": 30, "grade3": 18, "wonJuJae":  4, "wonRyoJae":  1}


# ─── Request Model ────────────────────────────────────────────────────────────

# UI 인터랙티브 응답용 Monte Carlo 샘플 수 (환경변수로 튜닝).
# growth_predict·market_snapshot 메모이즈(D128·D132) 후 300 샘플도 약 0.3s 이므로
# 기본을 정확도 우선 300 으로 둔다. 더 빠르게 하려면 UI_MC_SAMPLES 로 낮춘다.
_UI_MC_SAMPLES = int(os.getenv("UI_MC_SAMPLES", "300"))


class AnalyzeRequest(BaseModel):
    pnu: str
    riskPreference: str = "balanced"  # safe | balanced | profit (ui 위험 선호)


# ─── /analyze ─────────────────────────────────────────────────────────────────

@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    pnu = req.pnu.strip()
    if not pnu:
        raise HTTPException(status_code=400, detail="PNU 코드가 필요합니다")

    today = date.today().isoformat()

    # ── Module A mock ─────────────────────────────────────────────────────────
    p           = mock_module_a(pnu)
    species     = p["species"]
    site_index  = p["site_index"]
    age_now     = p["age"]
    area_ha     = p["area_ha"]

    # ── Module D: 시장 데이터 (날짜별 메모이즈 — KAU 라이브 fetch 반복 제거) ──
    try:
        market = _market_snapshot_cached(today)
    except Exception:
        market = {
            "timber_price": {"특용재": 294300, "1등급": 199700, "2등급": 173400,
                             "3등급": 135800, "원주재": 85700, "원료재": 33800},
            "timber_price_by_species": {},
            "kau_close": 15550.0,
            "koc_estimate": 10885.0,
            "vcm_floor_wta": 17039.0,
            "discount_rate": 0.05,
        }

    timber_prices_kr = market.get("timber_price") or {}
    species_prices   = (market.get("timber_price_by_species") or {}).get(species, {})
    active_prices    = species_prices if species_prices else timber_prices_kr

    kau_close     = market.get("kau_close")    or 15550.0
    koc_estimate  = market.get("koc_estimate") or 10885.0
    discount_rate = market.get("discount_rate") or 0.05

    # ── Module B: 성장 예측 ───────────────────────────────────────────────────
    try:
        trajectory = growth_predict(
            species=species,
            site_index=site_index,
            age_now=age_now,
            forecast_years=[0, 5, 10, 20, 30],
            climate_scenario="baseline",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Module B (growth_predict) 오류: {e}")

    if not trajectory:
        raise HTTPException(status_code=500, detail="Module B가 빈 trajectory를 반환했습니다")

    cur     = trajectory[0]
    cur_vol = cur.get("volume") or 0.0
    cur_dbh = cur.get("dbh")   or 0.0

    # GrowthForecast — carbonPerHa: 현 시점부터의 누적 탄소 흡수량 (tCO2/ha)
    cum_carbon = []
    running, prev_rel = 0.0, 0
    for i, pt in enumerate(trajectory):
        rel = pt["age"] - age_now
        if i > 0:
            rate = pt.get("carbon_uptake_rate") or 0.0
            running += rate * (rel - prev_rel)
        cum_carbon.append(round(running, 2))
        prev_rel = rel

    # Module B 전체 trajectory 필드 추출
    data_method  = cur.get("method", "exact")
    data_warning = cur.get("warning")

    growth_forecast = {
        "years":                   [pt["age"] - age_now for pt in trajectory],
        "volumePerHa":             [round(pt.get("volume") or 0.0, 1) for pt in trajectory],
        "carbonPerHa":             cum_carbon,
        "carbonSequestration":     [round(pt.get("carbon_uptake_rate") or 0.0, 3) for pt in trajectory],
        "gradeDistributionByYear": [estimate_grade_dist(pt.get("dbh") or cur_dbh) for pt in trajectory],
        "climateScenario":         "SSP1-2.6",
        # Module B 전달 필드
        "dbhTrajectory":    [round(pt.get("dbh") or 0.0, 1) for pt in trajectory],
        "heightTrajectory": [round(pt.get("height") or 0.0, 1) for pt in trajectory],
        "nPerHaTrajectory": [round(pt.get("n_per_ha") or 0.0, 0) for pt in trajectory],
        "tmaiTrajectory":   [round(pt.get("tmai_m3_per_ha_yr") or 0.0, 2) for pt in trajectory],
        "dataMethod":       data_method,
        "dataWarning":      data_warning,
    }

    # ── ForestState ───────────────────────────────────────────────────────────
    agb_per_ha        = round(cur_vol * 0.45 * 1.2, 1)  # 용적밀도 × BEF (침엽수)
    stored_co2_per_ha = round(agb_per_ha * 0.5 * 44 / 12, 1)

    forest_state = {
        "pnu":               pnu,
        "species":           species,
        "estimatedAge":      age_now,
        "volumePerHa":       round(cur_vol, 1),
        "volumeUncertainty": round(cur_vol * 0.15, 1),
        "carbonPerHa":       stored_co2_per_ha,
        "agbPerHa":          agb_per_ha,
        "areaHa":            area_ha,
        "gradeDistribution": estimate_grade_dist(cur_dbh),
        "forestType":        p["forest_type"],
        "siteIndex":         site_index,
        "coordinates":       {"lat": p["lat"], "lng": p["lng"]},
        # Module B 현재 시점 추가 필드
        "tmaiNow":    round(cur.get("tmai_m3_per_ha_yr") or 0.0, 2),
        "heightNow":  round(cur.get("height") or 0.0, 1),
        "nPerHaNow":  round(cur.get("n_per_ha") or 0.0, 0),
        "dataMethod": data_method,
        "dataWarning": data_warning,
    }

    # ── Module D: MarketData ──────────────────────────────────────────────────
    market_data = {
        "kauPrice":    kau_close,
        "kocEstimate": koc_estimate,
        "timberPrices": {
            "teukYongJae": active_prices.get("특용재") or 294300,
            "grade1":      active_prices.get("1등급")  or 199700,
            "grade2":      active_prices.get("2등급")  or 173400,
            "grade3":      active_prices.get("3등급")  or 135800,
            "wonJuJae":    active_prices.get("원주재") or  85700,
            "wonRyoJae":   active_prices.get("원료재") or  33800,
        },
        "discountRate": discount_rate,
        "priceDate":    today,
        "vcmFloorWta":  market.get("vcm_floor_wta") or 17039,
    }

    # ── Offset Eligibility ────────────────────────────────────────────────────
    eligible = age_now >= 20 and cur_vol > 50
    offset_eligibility = {
        "eligible":           eligible,
        "matchedTypes":       ["KOC (산림탄소상쇄)"] if eligible else [],
        "baselineCarbon":     stored_co2_per_ha * area_ha,
        "additionalityCheck": True,
        "nextSteps": (
            ["산림탄소상쇄사업 등록 신청 (한국임업진흥원)",
             "현장 조사 및 임목 측정 (±10% 정밀도)",
             "모니터링 계획 수립 (5년 주기)"]
            if eligible else
            ["임목 성장 후 재평가 필요 (20년, 50 m³/ha 기준)"]
        ),
    }

    # ── Module C: 시나리오 NPV — 통합 완료 (희도 D127) ───────────────────────
    # forest_state(Module A·B) → Module C → ui Scenario[] 의 흐름을 잇는다.
    # Module C 오류 시에도 A·B·D 결과는 보존한다(graceful degradation).
    _PREF_MAP = {"safe": "위험회피", "balanced": "균형", "profit": "수익극대화"}
    user_pref = _PREF_MAP.get(req.riskPreference, "균형")

    try:
        # forest_state(camelCase) → Module C stand dict(snake_case, 15키)
        stand = stand_adapter.from_forest_state(forest_state)

        # 6 시나리오 × Monte Carlo(LHS) → NPV·Pareto·추천 카드.
        # 메모이즈(D128·D132) 덕에 300 샘플도 약 0.3s. UI_MC_SAMPLES 로 조정 가능.
        package = compute_lev_with_plan(
            stand,
            n_samples=_UI_MC_SAMPLES,
            user_preference=user_pref,
        )

        # Module C 결과 → ui Scenario[] 형식
        scenarios      = ui_adapter.to_ui_scenarios(package, age_now=age_now)
        recommendation = ui_adapter.to_ui_recommendation(package)

        # 8 사업유형 정밀 매칭 → offsetEligibility 교체(Module A baselineCarbon 결합)
        offset_from_c = ui_adapter.to_ui_offset_eligibility(package)
        offset_from_c["baselineCarbon"] = stored_co2_per_ha * area_ha
        offset_eligibility = offset_from_c

    except Exception as e:
        # Module C 가 실패해도 위성·성장·시장 결과는 그대로 반환
        print(f"[Module C] 경제성 분석 오류 — scenarios 생략: {e}")
        scenarios     = None
        recommendation = None

    return {
        "pnu":               pnu,
        "analyzedAt":        today + "T00:00:00Z",
        "state":             forest_state,
        "growth":            growth_forecast,
        "market":            market_data,
        "scenarios":         scenarios,
        "recommendation":    recommendation,
        "offsetEligibility": offset_eligibility,
    }


# ─── Health Check ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status":  "ok",
        "modules": {
            "A": "mock",
            "B": "growth_predict (live)",
            "C": "Faustmann-Hartman (live)",
            "D": "market_snapshot (live)",
        },
    }


if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8001, reload=True)
