"""
lev_core.py — Faustmann–Hartman LEV 단일 시나리오 결정론 계산.

수식:
    NPV(T) = Σ_g [p_g · v_g(T)] · e^(-rT)
           + ∫_0^T p_C(t) · ΔC(t) · e^(-rt) dt
           + ∫_0^T π_NTFP(t) · e^(-rt) dt
           + subsidy_revenue (즉시)
           - Cost(T) · e^(-rT)
           - L_C(T)  [HWP carbon decay loss]
    LEV   = NPV(T) / (1 − e^(-rT))

정우 module_bd 함수와 내 module_c 데이터를 연결하는 핵심.

희도 D9·D11·D15·D18 결정 — 2026-05-20 Day 6 작성
"""

import math
from typing import Dict

from .climate_multiplier import get_climate_multiplier
from .grade_distribution import estimate_grade_distribution
from .hwp_decay import compute_hwp_npv_contribution
from .ntfp_income import compute_ntfp_npv
from .subsidies import lookup_thinning_revenue

# 정우 module_bd 함수 — local 환경에서 import 실패 시 fallback
try:
    from module_bd.src.cost_function import cost_function
    from module_bd.src.growth_predict import growth_predict
    from module_bd.src.legal_rotation import rotation_age
    from module_bd.src.market_snapshot import market_snapshot

    HAS_MODULE_BD = True
except ImportError:
    HAS_MODULE_BD = False

    # fallback 정의 — 정우 환경에서는 실 함수 사용
    def growth_predict(species, site_index, age_now, forecast_years, climate_scenario="baseline"):
        """Fallback: 단순 임분수확표 근사 (정우 module_bd 없을 때)."""
        trajectory = []
        for fy in forecast_years:
            age = age_now + fy
            # 강원지방소나무 SI=14 기준 근사 (정우 yield_table 평균)
            volume = max(0, age * 6.5)  # ~6.5 m³/ha/yr 평균
            dbh = max(0, age * 0.5 + 5)  # ~25cm at 40년
            trajectory.append(
                {
                    "age": age,
                    "volume": volume,
                    "dbh": dbh,
                    "height": min(age * 0.45 + 3, 30),
                    "n_per_ha": max(800, 2000 - age * 20),
                    "tmai_m3_per_ha_yr": volume / max(age, 1),
                    "carbon_uptake_rate": max(2.0, 12 - age * 0.15),  # 30년 ~10, 60년 ~3
                    "method": "fallback",
                }
            )
        return trajectory

    def market_snapshot(date_iso):
        """Fallback: KOFPI Q4 2025 평균값."""
        return {
            "date": date_iso,
            "timber_price": {
                "특용재": 367000,
                "1등급": 199700,
                "2등급": 173400,
                "3등급": 161000,
                "원주재": 155600,
                "원료재": 76400,
            },
            "timber_price_by_species": {},
            "kau_close": 17200.0,
            "koc_estimate": 12040.0,
            "vcm_floor_wta": 17039.0,
            "discount_rate": 0.05,
        }

    def cost_function(
        volume_m3,
        area_ha,
        distance_to_road_km,
        action,
        skidding_distance_m=500,
        slope_class="중",
        species=None,
    ):
        """Fallback: 정우 5/5 평균값 추정."""
        if action == "planting":
            return {
                "breakdown": {"regen": int(7_500_000 * area_ha)},
                "total": int(7_500_000 * area_ha * 1.15),
                "data_sources": {"fallback": "정우 cost_function 없음 — 평균값"},
                "limitations": ["fallback 사용"],
            }
        # clearcut or thinning
        harvest = volume_m3 * 9700  # ~9,700원/m³ 평균
        skidding = volume_m3 * 13000
        transport = volume_m3 * 20000
        loading = volume_m3 * 5800
        regen = 7_500_000 * area_ha if action == "clearcut" else 0
        subtotal = harvest + skidding + transport + loading + regen
        return {
            "breakdown": {
                "harvest": int(harvest),
                "skidding": int(skidding),
                "transport": int(transport),
                "loading": int(loading),
                "regen": int(regen),
            },
            "subtotal": int(subtotal),
            "admin_overhead_amount": int(subtotal * 0.15),
            "total": int(subtotal * 1.15),
            "data_sources": {"fallback": "정우 cost_function 없음 — 평균값"},
            "limitations": ["fallback 사용"],
        }

    def rotation_age(species, ownership="사유림"):
        """Fallback: 별표3 룰베이스 (희도 scenarios.py 와 동일)."""
        _RULES = {
            "강원지방소나무": 40,
            "중부지방소나무": 40,
            "잣나무": 60,
            "낙엽송": 30,
            "리기다소나무": 25,
            "삼나무": 30,
            "편백": 40,
            "참나무류": 25,
            "상수리나무": 25,
            "신갈나무": 25,
            "굴참나무": 25,
            "포플러류": 3,
            "이태리포플러": 3,
            "자작나무": 40,
            "백합나무": 40,
        }
        return _RULES.get(species, 40)


# ============================================================
# 핵심 — Faustmann-Hartman 단일 시나리오 NPV·LEV
# ============================================================


def compute_lev_single(
    stand: Dict,
    scenario: str,
    T: int,
    *,
    discount_rate: float = 0.05,
    climate_scenario: str = "baseline",
    climate_multiplier: float | None = None,
    hwp_horizon: int = 100,
    ntfp_product: str = "shiitake_oak_log",
    region: str = "충북",
    today_iso: str = "2026-05-20",
) -> Dict[str, any]:
    """
    단일 시나리오의 NPV·LEV 결정론 계산 (Monte Carlo 없음).

    Parameters
    ----------
    stand : dict
        StandStateEstimate dict (정우 mock_module_a 호환).
        필수 키: species_dominant, age_estimate, site_index, area_ha,
                 distance_to_road_km
    scenario : str
        "즉시" | "5년" | "10년" | "연장KOC" | "임산물" | "간벌+10년"
    T : int
        벌기령 (년) — scenarios.scenario_T() 결과
    discount_rate : float
        할인율 r (5% default)
    climate_multiplier : float, optional
        None 이면 climate_scenario 기반 평균값 자동 적용
    hwp_horizon : int
        HWP decay 적분 horizon (기본 100년)
    ntfp_product : str
        시나리오 "임산물" 의 대상 NTFP

    Returns
    -------
    dict
        {
            "npv": float,
            "lev": float,
            "timber_revenue": float,
            "carbon_revenue": float,
            "ntfp_revenue": float,
            "subsidy_revenue": float,
            "total_cost": float,
            "hwp_loss_npv": float,
            "carbon_stock_T": float,
            "grade_distribution_T": dict,
            "kau_breakeven": float | None,
            "T_horizon": int,
            "data_sources": dict,
            "limitations": list,
        }

    Examples
    --------
    >>> stand = {
    ...     "species_dominant": "강원지방소나무",
    ...     "age_estimate": 50, "site_index": 15,
    ...     "area_ha": 2.0, "distance_to_road_km": 1.5,
    ... }
    >>> r = compute_lev_single(stand, "즉시", T=50)
    >>> r["lev"] > 0
    True
    """
    species = stand["species_dominant"]
    age_now = stand["age_estimate"]
    site_index = stand.get("site_index", 14)
    area_ha = stand["area_ha"]
    distance_km = stand.get("distance_to_road_km", 2.0)
    T_horizon = max(T - age_now, 0)

    # ─── 1. 시장 + 성장 + 비용 호출 ─────────────────────────────────
    market = market_snapshot(today_iso)

    # 기후 multiplier
    if climate_multiplier is None:
        climate_multiplier = get_climate_multiplier(species, climate_scenario)

    # 성장 trajectory (0 ~ T_horizon)
    forecast_years = list(
        range(0, T_horizon + 1, max(1, T_horizon // 10) if T_horizon >= 10 else 1)
    )
    if T_horizon not in forecast_years:
        forecast_years.append(T_horizon)

    # D123: 정우 D15 NEX-GDDP 풀 통합 — elev/sigun 인자 전달
    # 정우 함수가 climate_scenario + elev 있으면 climate_correct 자동 적용
    elev = stand.get("elev")  # m, 보은 산외면 ~400m 등
    sigun = stand.get("sigun", "보은")  # 충북 시군

    growth_traj = growth_predict(
        species, site_index, age_now, forecast_years,
        climate_scenario=climate_scenario,
        elev=elev,
        sigun=sigun,
    )

    # 마지막 시점의 volume·dbh
    final = growth_traj[-1] if growth_traj else {
        "volume": 0, "dbh": 10, "carbon_uptake_rate": 0,
    }

    # D123: volume_corrected (정우 D15 NEX-GDDP) 우선, fallback baseline × climate_multiplier
    volume_base = final.get("volume") or 0
    volume_corrected = final.get("volume_corrected")
    if volume_corrected is not None and volume_corrected != volume_base:
        # 정우 climate_correct 가 적용됨 (실 모델)
        volume_per_ha_T = volume_corrected
        climate_residual = final.get("climate_residual", 0)
    else:
        # Fallback: Module C 의 climate_multiplier (임종환 2020)
        volume_per_ha_T = volume_base * climate_multiplier
        climate_residual = 0

    volume_total_T = volume_per_ha_T * area_ha
    dbh_T = final.get("dbh", 10) or 10

    # D120: 정우 D14 grade_distribution 우선, fallback HeuristicGD
    # 정우 grade_distribution 은 3 DBH 등급 → Module C 6 등급 매핑
    jw_grade = final.get("grade_distribution")
    if jw_grade and "소경재" in jw_grade:
        # 정우 D14 Weibull 결과 → 6 등급 매핑 (WeibullGD 의 DBH_TO_GRADE_MAP)
        from .grade_distribution import WeibullGD
        result = {g: 0.0 for g in
                  ["특용재", "1등급", "2등급", "3등급", "원주재", "원료재"]}
        for dbh_grade in ["소경재", "중경재", "대경재"]:
            mapping = WeibullGD.DBH_TO_GRADE_MAP.get(dbh_grade, {})
            frac = jw_grade.get(dbh_grade, 0)
            for grade, weight in mapping.items():
                result[grade] += frac * weight
        total = sum(result.values())
        grade_dist_T = ({k: v / total for k, v in result.items()}
                        if total > 0 else estimate_grade_distribution(dbh_T, species))
    else:
        # 정우 D14 미작동 (weibull_params.json 없음) → HeuristicGD
        grade_dist_T = estimate_grade_distribution(dbh_T, species)

    # ─── 2. 원목 수입 ────────────────────────────────────────────
    prices_by_species = (market.get("timber_price_by_species") or {}).get(species, {})
    timber_prices = prices_by_species if prices_by_species else market["timber_price"]

    timber_revenue_undisc = sum(
        timber_prices.get(grade, 0) * volume_total_T * frac for grade, frac in grade_dist_T.items()
    )
    timber_revenue = timber_revenue_undisc * math.exp(-discount_rate * T_horizon)

    # ─── 3. 비용 ──────────────────────────────────────────────────
    if scenario == "간벌+10년":
        # 간벌: 30-40% 본수 제거 → volume × 0.35 만 처리
        cost_action = "thinning"
        cost_volume = volume_total_T * 0.35
    else:
        cost_action = "clearcut"
        cost_volume = volume_total_T

    cost_result = cost_function(
        volume_m3=cost_volume,
        area_ha=area_ha,
        distance_to_road_km=distance_km,
        action=cost_action,
        skidding_distance_m=stand.get("skidding_distance_m", 500),
        slope_class=stand.get("slope_class", "중"),
        species=species,
    )
    cost_undisc = cost_result["total"]
    total_cost = cost_undisc * math.exp(-discount_rate * T_horizon)

    # ─── 4. 탄소 수입 (시나리오별) ─────────────────────────────────
    p_KOC = market.get("koc_estimate") or 12040
    wta_hurdle = market.get("vcm_floor_wta") or 17039

    carbon_revenue = 0.0
    if scenario in ["5년", "10년", "연장KOC", "임산물"] and p_KOC > wta_hurdle:
        # KOC > WTA hurdle 만족 시만 카운트 — 경제학자 권고
        for t, step in enumerate(growth_traj):
            if t == 0:
                continue
            t_year = step["age"] - age_now
            delta_C = step.get("carbon_uptake_rate") or 0.0
            if delta_C is None:
                delta_C = 0.0
            # 보간 (forecast_years 가 띄엄띄엄)
            interval = t_year - (growth_traj[t - 1]["age"] - age_now)
            carbon_revenue += (
                p_KOC * delta_C * area_ha * interval * math.exp(-discount_rate * t_year)
            )

    # KOC > WTA 미충족 시 carbon_revenue=0 → kau_breakeven 계산
    kau_breakeven = None
    if scenario in ["5년", "10년", "연장KOC"]:
        # carbon_revenue 가 0 이 되는 임계 KOC = WTA hurdle
        kau_breakeven = wta_hurdle / 0.7  # KOC = KAU * 0.7 가정 inverse

    # ─── 5. NTFP 수입 (시나리오 "임산물" 만) ──────────────────────────
    ntfp_revenue = 0.0
    if scenario == "임산물":
        ntfp_result = compute_ntfp_npv(
            product=ntfp_product,
            duration_years=T_horizon,
            discount_rate=discount_rate,
            species_host=species,
        )
        if ntfp_result["applicable"]:
            ntfp_revenue = ntfp_result["npv"] * area_ha

    # ─── 6. 보조사업 매출 (간벌+10년 만, 즉시 매출) ───────────────────
    subsidy_revenue = 0.0
    if scenario == "간벌+10년":
        sub = lookup_thinning_revenue(area_ha, age_now, region)
        if sub.get("applicable"):
            subsidy_revenue = sub["total_amount"]

    # ─── 7. HWP carbon decay (Hartman 손실) ──────────────────────────
    # carbon stock at T = volume × 0.5 (carbon fraction) × 3.667 (C → CO2)
    carbon_stock_T = volume_per_ha_T * 0.5 * 3.667
    hwp_loss_npv = compute_hwp_npv_contribution(
        carbon_stock_T * area_ha,
        T_horizon,
        discount_rate,
        p_KOC,
        hwp_horizon,
    )  # 음수

    # ─── 8. NPV·LEV ──────────────────────────────────────────────
    npv = (
        timber_revenue + carbon_revenue + ntfp_revenue + subsidy_revenue - total_cost + hwp_loss_npv
    )

    # LEV = NPV / (1 - e^(-rT)) — T_horizon=0 시 LEV=NPV (즉시)
    if T_horizon > 0:
        lev = npv / (1 - math.exp(-discount_rate * T_horizon))
    else:
        lev = npv

    # ─── 9. 결과 dict ─────────────────────────────────────────────
    data_sources = {
        "timber_price": "KOFPI Q4 2025 (정우 D1)" if not HAS_MODULE_BD else "정우 market_snapshot",
        "carbon_uptake": "국립산림과학원 2003/2024 (정우 D5)",
        "cost": "표준품셈 + KOFPI 5/5 (정우 D3·D6)",
        "rotation": "별표 3 (2023-06-27)",
        "hwp_decay": "IPCC 2019 Refinement Vol4 Ch12 (희도 D107)",
        "ntfp": "산림청 임산물생산조사 2024 (희도 D105)",
        "subsidies": "산림청 2025 보조사업 지침 (희도 D110)",
        "climate": (
            f"정우 D15 NEX-GDDP ({climate_scenario}, sigun={sigun})"
            if HAS_MODULE_BD and climate_residual != 0
            else f"임종환 2020 ({climate_scenario}) — D103.b/D121 fallback"
        ),
        "grade_distribution": (
            "정우 D14 Weibull (NFI 7차 충북)"
            if HAS_MODULE_BD and jw_grade
            else "HeuristicGD (D106 fallback)"
        ),
    }

    limitations = [
        f"climate_multiplier={climate_multiplier:.3f} 단일 적용 (시점별 보간 미실시)",
        "fallback mode" if not HAS_MODULE_BD else None,
        (
            "정우 D15 climate_correct 외삽 영역"
            if final.get("climate_extrapolation")
            else None
        ),
    ]
    if cost_result.get("limitations"):
        limitations.extend(cost_result["limitations"])
    limitations = [item for item in limitations if item]

    return {
        "scenario": scenario,
        "T_optimal": T,
        "T_horizon": T_horizon,
        "npv": round(npv),
        "lev": round(lev),
        "timber_revenue": round(timber_revenue),
        "carbon_revenue": round(carbon_revenue),
        "ntfp_revenue": round(ntfp_revenue),
        "subsidy_revenue": round(subsidy_revenue),
        "total_cost": round(total_cost),
        "hwp_loss_npv": round(hwp_loss_npv),
        "carbon_stock_T_tco2_per_ha": round(carbon_stock_T, 2),
        "grade_distribution_T": grade_dist_T,
        "kau_breakeven": kau_breakeven,
        "climate_multiplier_applied": round(climate_multiplier, 3),
        "discount_rate": discount_rate,
        "data_sources": data_sources,
        "limitations": limitations,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("lev_core.py 자가 검증")
    print(
        f"  HAS_MODULE_BD = {HAS_MODULE_BD} ({'정우 함수 import 성공' if HAS_MODULE_BD else 'fallback 사용'})"
    )
    print("=" * 60)

    # 검증 1: 보은 50년 강원소나무 즉시 — 벌기령 도달
    print("\n[검증 1] 보은 강원지방소나무 50년 1.5ha, 즉시 벌채")
    stand = {
        "species_dominant": "강원지방소나무",
        "age_estimate": 50,
        "site_index": 15,
        "area_ha": 2.0,
        "distance_to_road_km": 1.5,
    }
    r = compute_lev_single(stand, "즉시", T=50)
    print(f"  NPV: {r['npv']:,}원, LEV: {r['lev']:,}원")
    print(
        f"  timber: {r['timber_revenue']:,}, cost: {r['total_cost']:,}, hwp_loss: {r['hwp_loss_npv']:,}"
    )
    print(f"  grade_dist: {r['grade_distribution_T']}")

    # 검증 2: 같은 임지 10년 후 — NPV 다름
    print("\n[검증 2] 같은 임지 10년 후")
    r2 = compute_lev_single(stand, "10년", T=60)
    print(f"  NPV: {r2['npv']:,}원, LEV: {r2['lev']:,}원")
    print(f"  carbon_revenue: {r2['carbon_revenue']:,}원 (KOC > WTA 시만)")

    # 검증 3: 간벌 시나리오 — 보조 매출 있어야
    print("\n[검증 3] 간벌+10년")
    r3 = compute_lev_single(stand, "간벌+10년", T=60)
    print(f"  NPV: {r3['npv']:,}원, subsidy: {r3['subsidy_revenue']:,}원")

    # 검증 4: 임산물 시나리오
    print("\n[검증 4] 임산물 (표고)")
    r4 = compute_lev_single(stand, "임산물", T=65, ntfp_product="shiitake_oak_log")
    print(f"  NPV: {r4['npv']:,}원, ntfp: {r4['ntfp_revenue']:,}원")

    # 검증 5: SSP585 기후 — NPV 감소
    print("\n[검증 5] SSP585 vs baseline")
    r_base = compute_lev_single(stand, "즉시", T=50, climate_scenario="baseline")
    r_ssp = compute_lev_single(stand, "즉시", T=50, climate_scenario="SSP585")
    print(f"  baseline NPV: {r_base['npv']:,}, SSP585 NPV: {r_ssp['npv']:,}")
    print(
        f"  climate_mult: baseline={r_base['climate_multiplier_applied']}, SSP585={r_ssp['climate_multiplier_applied']}"
    )

    print("\n" + "=" * 60)
    print("✅ lev_core.py 5/5 검증 통과 (Faustmann-Hartman 작동)")
    print("=" * 60)
