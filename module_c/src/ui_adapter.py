"""
ui_adapter.py — Module C 경제성 분석 결과를 ui(수범 Next.js)가 그리는 형식으로 변환.

이 모듈은 통합 파이프라인의 마지막 연결 고리다. 희도의 Module C
(`compute_lev_with_plan`) 가 산출한 LEVResult·Pareto·DraftPlanCard 를,
수범이 정의한 ui `Scenario[]` TypeScript 인터페이스에 정확히 맞춘 JSON 으로
변환한다.

해결하는 네 가지 불일치:
    1. 시나리오 식별자 — Module C 는 한국어("즉시"·"연장KOC"), ui 는 영어
       소문자("immediate"·"koc"). 양방향 매핑 테이블로 변환한다.
    2. 단위 — Module C 는 원(KRW), ui 는 만원. 1/10,000 로 나눈다.
    3. 파생 지표 — ui 가 요구하는 bankruptcyProb(NPV<0 확률)·paretoX(유동성
       점수)·kocEligible(KOC 적격)은 Module C 가 직접 내보내지 않으므로
       Monte Carlo 분포와 사업유형 매칭에서 계산한다.
    4. 비용 분해 — ui 는 harvestCost·regenCost 를 따로 요구하나 Module C 는
       cost_breakdown 으로 통합 보유하므로 항목을 합산·분리한다.

여섯 번째 시나리오("간벌+10년")는 ui 가 아직 5개 id 만 정의하므로,
"thinning" 이라는 새 id 로 내보낸다(수범에게 ui `Scenario.id` union 에
"thinning" 추가를 요청). ui 가 수용하기 전까지는 안전하게 표시된다.

희도 D127 결정 — 2026-05-31, Module A 도착 후 통합.
"""

from __future__ import annotations

# ── 시나리오 식별자 매핑 (Module C 한국어 ↔ ui 영어) ──────────────────────
_SCENARIO_ID_MAP: dict[str, str] = {
    "즉시": "immediate",
    "5년": "five_year",
    "10년": "ten_year",
    "연장KOC": "koc",
    "임산물": "ntfp",
    "간벌+10년": "thinning",  # ui types.ts 에 id 추가 요청 (수범)
}

# ui 표시용 한국어 이름·설명 (ScenarioTable 의 name·description 컬럼)
_SCENARIO_META: dict[str, dict[str, str]] = {
    "즉시": {
        "name": "즉시 벌채",
        "description": "올해 벌채 후 재조림 — 즉시 현금화",
    },
    "5년": {
        "name": "5년 후 벌채",
        "description": "5년 추가 성장으로 등급 상승 후 벌채",
    },
    "10년": {
        "name": "10년 후 벌채",
        "description": "10년 후 1등급 비율 최대화 후 벌채",
    },
    "연장KOC": {
        "name": "벌기령 연장 (KOC)",
        "description": "벌채 유예 + 산림탄소상쇄(KOC) 등록으로 탄소 수익",
    },
    "임산물": {
        "name": "임산물 병행",
        "description": "표고버섯 등 임산물 재배 + 자연벌기까지 유지",
    },
    "간벌+10년": {
        "name": "간벌 + 10년",
        "description": "솎아베기 보조사업 + 잔존목 10년 추가 성장",
    },
}

_WON_PER_MANWON = 10_000


def _to_manwon(won: float | None) -> float:
    """원(KRW)을 만원으로 변환한다 (ui 단위)."""
    if won is None:
        return 0.0
    return round(won / _WON_PER_MANWON, 1)


def _bankruptcy_prob(lev_result: dict) -> float:
    """NPV<0 확률(파산 확률)을 추정한다.

    Module C 의 Monte Carlo 가 npv_q05/q50/q95 분위수를 제공하므로,
    정규근사로 NPV<0 의 누적확률을 계산한다. 보수적으로 q05<0 이면
    최소 0.05 를 보장한다.
    """
    median = lev_result.get("npv_median", lev_result.get("npv_per_ha", 0))
    q05 = lev_result.get("npv_q05", median * 0.8)
    q95 = lev_result.get("npv_q95", median * 1.2)
    if median is None:
        return 0.0
    # 90% 예측구간 폭 → 표준편차 근사 (z=1.645)
    sigma = max((q95 - q05) / (2 * 1.645), 1.0)
    if median >= 0 and q05 >= 0:
        # 분포 전체가 양수 영역
        from math import erf, sqrt

        z = median / (sigma * sqrt(2))
        prob = 0.5 * (1 - erf(z))
        return round(max(prob, 0.0), 4)
    if median < 0:
        return round(min(0.95, 0.5 + abs(median) / (4 * sigma)), 4)
    # median ≥ 0 이지만 q05 < 0
    return round(max(0.05, 0.5 - median / (2 * sigma)), 4)


def _pareto_x(lev_result: dict, age_now: int) -> float:
    """유동성 점수(0=장기 보유, 1=즉시 현금화)를 계산한다.

    벌기 horizon(T - age_now)이 짧을수록 유동성이 높다. 30년을 최대
    유예로 보고 선형 정규화한다.
    """
    t_horizon = lev_result.get("T_horizon")
    if t_horizon is None:
        t_optimal = lev_result.get("T_optimal", age_now)
        t_horizon = max(t_optimal - age_now, 0)
    return round(max(0.0, 1.0 - t_horizon / 30.0), 3)


def _koc_eligible(scenario_kr: str, lev_result: dict) -> tuple[bool, str | None]:
    """KOC(산림탄소상쇄) 적격 여부와 방법론명을 판정한다.

    연장KOC 시나리오는 정의상 적격이며, 그 외 시나리오는 탄소 수익이
    발생하는 경우(KOC>WTA hurdle)에 한해 적격으로 본다.
    """
    if scenario_kr == "연장KOC":
        return True, "벌기령 연장을 통한 산림경영사업"
    if lev_result.get("carbon_revenue", lev_result.get("carbon_revenue_median", 0)) > 0:
        return True, "산림경영(탄소 수익 발생)"
    return False, None


def _harvest_regen_cost(lev_result: dict) -> tuple[float, float]:
    """cost_breakdown 을 ui 의 harvestCost·regenCost 로 분해한다."""
    breakdown = lev_result.get("cost_breakdown") or {}
    if breakdown:
        harvest = sum(breakdown.get(k, 0) for k in ("harvest", "skidding", "transport", "loading"))
        regen = breakdown.get("regen", 0)
        return _to_manwon(harvest), _to_manwon(regen)
    # cost_breakdown 이 없으면 total 을 7:3 으로 근사 분배
    total = lev_result.get("total_cost", lev_result.get("total_cost_median", 0))
    return _to_manwon(total * 0.7), _to_manwon(total * 0.3)


def to_ui_scenario(
    scenario_kr: str,
    lev_result: dict,
    *,
    age_now: int,
    recommended_kr: str | None = None,
) -> dict:
    """단일 Module C LEVResult 를 ui Scenario 객체로 변환한다."""
    median = lev_result.get("npv_median", lev_result.get("npv_per_ha", 0))
    q05 = lev_result.get("npv_q05", median * 0.8)
    q95 = lev_result.get("npv_q95", median * 1.2)

    koc_eligible, koc_method = _koc_eligible(scenario_kr, lev_result)
    harvest_cost, regen_cost = _harvest_regen_cost(lev_result)
    t_optimal = lev_result.get("T_optimal", age_now)
    meta = _SCENARIO_META.get(scenario_kr, {"name": scenario_kr, "description": ""})

    return {
        "id": _SCENARIO_ID_MAP.get(scenario_kr, scenario_kr),
        "name": meta["name"],
        "description": meta["description"],
        "harvestYear": (None if scenario_kr == "연장KOC" else max(t_optimal - age_now, 0)),
        "npv": {
            "p5": _to_manwon(q05),
            "p50": _to_manwon(median),
            "p95": _to_manwon(q95),
            "bankruptcyProb": _bankruptcy_prob(lev_result),
        },
        "timberRevenue": _to_manwon(
            lev_result.get("timber_revenue", lev_result.get("timber_revenue_median", 0))
        ),
        "carbonRevenue": _to_manwon(
            lev_result.get("carbon_revenue", lev_result.get("carbon_revenue_median", 0))
        ),
        "harvestCost": harvest_cost,
        "regenCost": regen_cost,
        "ntfpRevenue": _to_manwon(
            lev_result.get("ntfp_revenue", lev_result.get("ntfp_revenue_median", 0))
        ),
        "kocEligible": koc_eligible,
        "kocMethodology": koc_method,
        "paretoX": _pareto_x(lev_result, age_now),
        "recommended": (scenario_kr == recommended_kr),
    }


def to_ui_scenarios(
    package: dict,
    *,
    age_now: int,
) -> list[dict]:
    """compute_lev_with_plan() 전체 결과를 ui Scenario[] 로 변환한다.

    Parameters
    ----------
    package : dict
        `compute_lev_with_plan()` 의 반환 (results·pareto·draft_plan 포함).
    age_now : int
        현재 임령 (harvestYear·paretoX 계산용).

    Returns
    -------
    list[dict]
        ui `Scenario[]` 호환 JSON 배열. feasibility=False 시나리오는 제외.

    Examples
    --------
    >>> pkg = compute_lev_with_plan(stand)
    >>> scenarios = to_ui_scenarios(pkg, age_now=50)
    >>> scenarios[0]["id"]
    'immediate'
    """
    results = package.get("results", {})
    plan = package.get("draft_plan", {})
    recommended_kr = plan.get("recommended_scenario")

    ui_scenarios = []
    for scenario_kr, lev_result in results.items():
        if not lev_result.get("feasibility", True):
            continue  # 법정 벌기령 미달 시나리오는 ui 에서 숨김
        ui_scenarios.append(
            to_ui_scenario(
                scenario_kr,
                lev_result,
                age_now=age_now,
                recommended_kr=recommended_kr,
            )
        )
    return ui_scenarios


def to_ui_recommendation(package: dict) -> str | None:
    """ui ForestAnalysisResult.recommendation (권장 시나리오 id)."""
    plan = package.get("draft_plan", {})
    recommended_kr = plan.get("recommended_scenario")
    if recommended_kr is None:
        return None
    return _SCENARIO_ID_MAP.get(recommended_kr, recommended_kr)


def to_ui_offset_eligibility(package: dict) -> dict:
    """ui OffsetEligibility 객체로 변환한다."""
    plan = package.get("draft_plan", {})
    citations = plan.get("offset_citations") or []
    matched = [c.get("korean", c.get("code", "")) for c in citations if c]
    return {
        "eligible": len(matched) > 0,
        "matchedTypes": matched,
        "baselineCarbon": 0.0,  # api_server 의 forest_state.carbonPerHa 와 결합
        "additionalityCheck": len(matched) > 0,
        "nextSteps": plan.get("next_actions", []),
    }


if __name__ == "__main__":
    print("=" * 66)
    print("ui_adapter.py 자가 검증")
    print("=" * 66)

    # compute_lev_with_plan 반환 모사
    fake_package = {
        "results": {
            "즉시": {
                "npv_median": 660_000_000,
                "npv_q05": 460_000_000,
                "npv_q95": 860_000_000,
                "feasibility": True,
                "T_optimal": 50,
                "T_horizon": 0,
                "timber_revenue": 800_000_000,
                "carbon_revenue": 0,
                "ntfp_revenue": 0,
                "cost_breakdown": {"harvest": 50_000_000, "regen": 30_000_000},
            },
            "연장KOC": {
                "npv_median": 750_000_000,
                "npv_q05": 550_000_000,
                "npv_q95": 950_000_000,
                "feasibility": True,
                "T_optimal": 60,
                "T_horizon": 10,
                "timber_revenue": 900_000_000,
                "carbon_revenue": 50_000_000,
                "ntfp_revenue": 0,
            },
            "간벌+10년": {
                "npv_median": 800_000_000,
                "npv_q05": 650_000_000,
                "npv_q95": 950_000_000,
                "feasibility": True,
                "T_optimal": 60,
                "T_horizon": 10,
            },
            "즉시_불가": {  # feasibility=False 테스트
                "npv_median": 0,
                "feasibility": False,
            },
        },
        "draft_plan": {
            "recommended_scenario": "간벌+10년",
            "offset_citations": [{"code": "FM-Rotation", "korean": "벌기령 연장 산림경영"}],
            "next_actions": ["보은군산림조합 방문", "FGIS 임반 조회"],
        },
    }

    print("\n[검증 1] to_ui_scenarios — id 매핑 + 단위 변환")
    scenarios = to_ui_scenarios(fake_package, age_now=50)
    for s in scenarios:
        print(
            f"  {s['id']:<12s} {s['name']:<16s} "
            f"NPV p50={s['npv']['p50']:>10,.0f}만원 "
            f"파산확률={s['npv']['bankruptcyProb']:.2%} "
            f"{'✓권장' if s['recommended'] else ''}"
        )
    assert len(scenarios) == 3  # 불가 시나리오 제외
    assert scenarios[0]["id"] == "immediate"

    print("\n[검증 2] 간벌+10년 → thinning id")
    thinning = [s for s in scenarios if s["id"] == "thinning"]
    assert thinning, "간벌+10년 → thinning 변환 실패"
    print(f"  간벌+10년 → '{thinning[0]['id']}' (recommended={thinning[0]['recommended']})")

    print("\n[검증 3] KOC 적격 판정")
    koc = [s for s in scenarios if s["id"] == "koc"][0]
    print(f"  연장KOC: kocEligible={koc['kocEligible']}, 방법론='{koc['kocMethodology']}'")
    assert koc["kocEligible"]

    print("\n[검증 4] paretoX 유동성 점수")
    immediate = [s for s in scenarios if s["id"] == "immediate"][0]
    print(f"  즉시(T_horizon=0): paretoX={immediate['paretoX']} (즉시=1.0)")
    assert immediate["paretoX"] == 1.0

    print("\n[검증 5] recommendation + offset")
    rec = to_ui_recommendation(fake_package)
    offset = to_ui_offset_eligibility(fake_package)
    print(f"  권장 id: {rec}")
    print(f"  KOC 적격: {offset['eligible']}, 유형: {offset['matchedTypes']}")
    assert rec == "thinning"
    assert offset["eligible"]

    print("\n" + "=" * 66)
    print("✅ ui_adapter.py 5/5 검증 통과 (Module C ↔ ui 완전 호환)")
    print("=" * 66)
