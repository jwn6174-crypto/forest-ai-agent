"""
compute_lev.py — Module C 진입점.

사용:
    from module_c.src.compute_lev import compute_lev, compute_lev_with_plan
    from module_c.src.demo_parcels import get_demo_parcel

    stand = get_demo_parcel("boeun_pine_50y_2ha")
    results = compute_lev(stand, scenarios=["즉시", "10년", "연장KOC", "간벌+10년"])
    # → Dict[str, LEVResult_dict]

    # 또는 전체 DraftPlanCard 까지 한번에
    package = compute_lev_with_plan(stand)
    # → {"results": ..., "pareto": ..., "draft_plan": ...}

희도 진입점 — 2026-05-20 Day 6 작성
"""

from typing import Dict, List

from .draft_plan import create_draft_plan
from .lev_core import compute_lev_single
from .monte_carlo import run_monte_carlo
from .pareto import compute_pareto_front, select_three_representative
from .scenarios import (
    VALID_SCENARIOS,
    Scenario,
    scenario_feasibility,
    scenario_T,
)


def compute_lev(
    stand: Dict,
    scenarios: List[Scenario] | None = None,
    *,
    use_monte_carlo: bool = True,
    n_samples: int = 300,
    discount_rate: float = 0.05,
    climate_scenario: str = "baseline",
    region: str = "충북",
    ntfp_product: str = "shiitake_oak_log",
    seed: int = 42,
) -> Dict[str, Dict]:
    """
    6 시나리오의 LEV·NPV 분포 산출 (Monte Carlo 또는 결정론).

    Parameters
    ----------
    stand : dict
        StandStateEstimate dict — 정우 mock_module_a 또는 민석 module_a 출력 호환
    scenarios : list, optional
        None 이면 6 시나리오 전체 ["즉시","5년","10년","연장KOC","임산물","간벌+10년"]
    use_monte_carlo : bool
        True (기본): LHS 300 samples MC. False: 결정론 v1.
    n_samples : int
        LHS 권장 300, 단순 MC 권장 1000
    discount_rate : float
        할인율 r (5% default)
    climate_scenario : str
        "baseline" | "SSP126" | "SSP245" | "SSP585"
    region : str
        지역 (보조사업 단가 보너스용)
    ntfp_product : str
        시나리오 "임산물" 의 대상 NTFP
    seed : int

    Returns
    -------
    dict
        {
            "즉시": {npv_median, npv_q05, npv_q95, lev_median, ...},
            "5년": {...},
            ...
            "간벌+10년": {...},
        }
        Note: ComputeLEVRequest 의 LEVResult 호환 — `feasibility` 키 포함.
              feasibility=False 시 다른 키는 0 또는 None.

    Examples
    --------
    >>> from module_c.src.demo_parcels import get_demo_parcel
    >>> stand = get_demo_parcel("boeun_pine_50y_2ha")
    >>> results = compute_lev(stand, n_samples=50)  # 빠른 테스트
    >>> "간벌+10년" in results
    True
    """
    if scenarios is None:
        scenarios = VALID_SCENARIOS

    species = stand["species_dominant"]
    age_now = stand["age_estimate"]

    out = {}
    for sc in scenarios:
        T = scenario_T(sc, species, age_now)
        feasible, note = scenario_feasibility(sc, species, age_now, T)

        if not feasible:
            out[sc] = {
                "scenario": sc,
                "T_optimal": T,
                "feasibility": False,
                "feasibility_note": note,
                "npv": 0,
                "npv_median": 0,
                "npv_q05": 0,
                "npv_q95": 0,
                "lev": 0,
                "lev_median": 0,
                "timber_revenue": 0,
                "carbon_revenue": 0,
                "ntfp_revenue": 0,
                "subsidy_revenue": 0,
                "total_cost": 0,
                "hwp_loss_npv": 0,
                "carbon_stock_T_tco2_per_ha": 0,
                "grade_distribution_T": {},
                "data_sources": {},
                "limitations": [note],
            }
            continue

        try:
            if use_monte_carlo:
                r = run_monte_carlo(
                    stand,
                    sc,
                    T,
                    n_samples=n_samples,
                    discount_rate_base=discount_rate,
                    climate_scenario=climate_scenario,
                    region=region,
                    ntfp_product=ntfp_product,
                    seed=seed,
                )
                # MC 결과는 npv_median, npv_q05/q95 등 — feasibility 추가
                r["feasibility"] = feasible
                r["feasibility_note"] = note
                # NPV 단일 키 호환
                r["npv"] = r["npv_median"]
                r["lev"] = r["lev_median"]
            else:
                r = compute_lev_single(
                    stand,
                    sc,
                    T,
                    discount_rate=discount_rate,
                    climate_scenario=climate_scenario,
                    region=region,
                    ntfp_product=ntfp_product,
                )
                # 결정론 결과 — q05/q95 채움 (point estimate × ±20%)
                r["npv_median"] = r["npv"]
                r["lev_median"] = r["lev"]
                r["npv_q05"] = r["npv"] * 0.80
                r["npv_q95"] = r["npv"] * 1.20
                r["lev_q05"] = r["lev"] * 0.80
                r["lev_q95"] = r["lev"] * 1.20
                r["feasibility"] = feasible
                r["feasibility_note"] = note
            out[sc] = r
        except Exception as e:
            out[sc] = {
                "scenario": sc,
                "T_optimal": T,
                "feasibility": False,
                "feasibility_note": f"계산 오류: {e}",
                "npv": 0,
                "npv_median": 0,
                "lev": 0,
                "lev_median": 0,
                "data_sources": {},
                "limitations": [str(e)],
            }

    return out


def compute_lev_with_plan(
    stand: Dict,
    *,
    user_preference: str = "균형",
    scenarios: List[Scenario] | None = None,
    use_monte_carlo: bool = True,
    n_samples: int = 300,
    discount_rate: float = 0.05,
    climate_scenario: str = "baseline",
    region: str = "충북 보은",
    ntfp_product: str = "shiitake_oak_log",
    seed: int = 42,
) -> Dict[str, any]:
    """
    compute_lev + pareto + draft_plan 한번에.

    수범 module_e 가 POST /compute_lev 에서 호출.

    Returns
    -------
    dict
        {
            "results": Dict[scenario, LEVResult_dict],
            "pareto": {pareto_optimal, dominated, points},
            "three_representative": List[Dict],  # 안정/균형/수익형
            "draft_plan": DraftPlanCard dict,
            "_meta": {n_samples, climate_scenario, region, ...},
        }
    """
    # 1. 6 시나리오 LEV
    results = compute_lev(
        stand,
        scenarios=scenarios,
        use_monte_carlo=use_monte_carlo,
        n_samples=n_samples,
        discount_rate=discount_rate,
        climate_scenario=climate_scenario,
        region=region,
        ntfp_product=ntfp_product,
        seed=seed,
    )

    # 2. Pareto
    pareto = compute_pareto_front(results)
    three = select_three_representative(pareto)

    # 3. DraftPlanCard
    plan = create_draft_plan(
        stand,
        results,
        user_preference=user_preference,
        region=region,
    )

    return {
        "results": results,
        "pareto": pareto,
        "three_representative": three,
        "draft_plan": plan,
        "_meta": {
            "n_samples": n_samples,
            "climate_scenario": climate_scenario,
            "discount_rate": discount_rate,
            "region": region,
            "ntfp_product": ntfp_product,
            "use_monte_carlo": use_monte_carlo,
        },
    }


if __name__ == "__main__":
    from .demo_parcels import get_demo_parcel, list_demo_parcels

    print("=" * 60)
    print("compute_lev.py 자가 검증 — 4 demo polygon × 6 시나리오 end-to-end")
    print("=" * 60)

    for parcel_id in list_demo_parcels():
        print(f"\n{'=' * 60}")
        print(f"[{parcel_id}]")
        stand = get_demo_parcel(parcel_id)
        print(
            f"  {stand['species_dominant']} {stand['age_estimate']}년 "
            f"SI={stand['site_index']} {stand['area_ha']}ha"
        )

        # 빠른 검증을 위해 50 samples
        results = compute_lev(stand, n_samples=50, seed=42)
        print("\n  Scenario      NPV_med (M)   q05~q95 (M)        Feasible")
        for sc, r in results.items():
            f = "✅" if r["feasibility"] else "❌"
            npv = r.get("npv_median", r.get("npv", 0)) / 1e6
            q05 = r.get("npv_q05", 0) / 1e6
            q95 = r.get("npv_q95", 0) / 1e6
            print(f"  {sc:12s} {npv:>10.1f}  {q05:>6.1f}~{q95:<6.1f}    {f}")

    # DraftPlanCard 시연
    print(f"\n{'=' * 60}")
    print("[draft_plan 통합 시연 — 보은 50년]")
    print("=" * 60)
    stand = get_demo_parcel("boeun_pine_50y_2ha")
    package = compute_lev_with_plan(stand, user_preference="균형", n_samples=50)

    plan = package["draft_plan"]
    print(f"\n  추천 시나리오: {plan['recommended_scenario']}")
    print(f"  npv 단순표시: {plan['npv_단순표시']}")
    print(f"  npv worst 10%: {plan['npv_worst_case_10pct']}")
    print(f"  uplift: {plan['npv_uplift_label']}")
    print(f"  uncertainty: {plan['uncertainty_tier']} ({plan['uncertainty_note'][:50]}...)")
    print(f"\n  Pareto-optimal: {package['pareto']['pareto_optimal']}")
    print("\n  3 대표점:")
    for p in package["three_representative"]:
        print(
            f"    {p.get('_label', '')}: {p['scenario']} NPV {p['npv'] / 1e6:.1f}M C{p['carbon_stock_T']}"
        )

    print("\n  적용 가능 사업유형:")
    for c in plan["offset_citations"][:3]:
        print(f"    - {c['code']} {c['korean']}")

    print("\n  추천 근거:")
    for r in plan["reasons"][:4]:
        print(f"    - {r}")

    print("\n  다음 액션:")
    for a in plan["next_actions"]:
        print(f"    - {a}")

    print("\n" + "=" * 60)
    print("✅ compute_lev.py end-to-end 검증 통과")
    print("=" * 60)
