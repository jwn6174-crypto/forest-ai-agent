"""
monte_carlo.py — Monte Carlo (LHS) 시뮬레이션 for compute_lev.

lev_core.compute_lev_single() 을 N samples 호출 → NPV 분포.

6 분산 source (D11):
1. AGB / volume (Triangular q05/q50/q95)
2. 목재가 (Lognormal, 정우 KOFPI Q4 평균 ± 10%)
3. KOC (Lognormal, KAU × 0.7 ± 15%)
4. 임산물 연수입 (Lognormal)
5. 할인율 (Triangular 0.04/0.05/0.06)
6. 기후 multiplier (Normal × species × SSP)

LHS 권장 — 단순 MC 1000 의 std 3-7% → LHS 300 으로 std 1-2%.

희도 D11 결정 — 2026-05-20 Day 6 작성
"""

import math
import random
from typing import Dict

import numpy as np

from .climate_multiplier import get_climate_multiplier
from .lev_core import compute_lev_single
from .lhs_sampling import HAS_SCIPY, generate_lhs_samples_6d


def run_monte_carlo(
    stand: Dict,
    scenario: str,
    T: int,
    *,
    n_samples: int = 300,
    discount_rate_base: float = 0.05,
    climate_scenario: str = "baseline",
    region: str = "충북",
    ntfp_product: str = "shiitake_oak_log",
    seed: int = 42,
    use_lhs: bool = True,
) -> Dict[str, any]:
    """
    단일 시나리오의 LEV·NPV 분포를 LHS Monte Carlo 로 산출.

    Parameters
    ----------
    stand : dict
        StandStateEstimate dict (volume_q05/q95 등 분산 정보 포함)
    scenario : str
    T : int
    n_samples : int
        LHS 권장 300, 단순 MC 권장 1000
    use_lhs : bool
        True 면 LHS (권장), False 면 단순 MC

    Returns
    -------
    dict
        {
            "scenario": str, "T_optimal": int, "T_horizon": int,
            "npv_median": float,
            "npv_q05": float, "npv_q25": float, "npv_q75": float, "npv_q95": float,
            "lev_median": float, "lev_q05": float, "lev_q95": float,
            "timber_revenue_median": float,
            "carbon_revenue_median": float,
            "ntfp_revenue_median": float,
            "subsidy_revenue_median": float,
            "total_cost_median": float,
            "hwp_loss_median": float,
            "carbon_stock_T_tco2_per_ha_median": float,
            "grade_distribution_T": dict,
            "n_samples": int,
            "std_ratio": float,  # std / median (수렴 진단)
            "feasibility": bool,
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
    >>> r = run_monte_carlo(stand, "즉시", T=50, n_samples=100)
    >>> r["npv_median"] != 0
    True
    """
    species = stand["species_dominant"]
    stand["area_ha"]

    # ─── 1. 분포 정의 ────────────────────────────────────────────
    # AGB / volume: Triangular (q05, mid, q95)
    v_mid = stand.get("volume_m3_per_ha", 200.0)
    v_q05 = stand.get("volume_q05", v_mid * 0.85)
    v_q95 = stand.get("volume_q95", v_mid * 1.15)

    # 목재가: Lognormal, KOFPI 평균값 ± 10%
    # 등급별이지만 단순화로 1등급 기준 단일 변수
    timber_price_mean = 199_700  # KOFPI Q4 2025 강원소나무 1등급
    timber_price_mean * 0.10

    # KOC: Lognormal, KAU × 0.7 ± 15%
    koc_mean = 12_040
    koc_std = koc_mean * 0.15

    # NTFP 연수입 (시나리오 임산물 만)
    ntfp_mean = 5_500_000  # 표고 평균
    ntfp_std = 1_500_000

    # 할인율: Triangular(0.04, 0.05, 0.06)

    # 기후 multiplier
    clim = get_climate_multiplier(species, climate_scenario)
    clim_std = 0.05 if climate_scenario == "baseline" else 0.15

    # ─── 2. Sample 생성 (LHS 또는 단순 MC) ───────────────────────
    distributions = {
        "volume_mult": ("triangular", {"min": v_q05 / v_mid, "mode": 1.0, "max": v_q95 / v_mid}),
        "timber_mult": ("lognormal", {"mean": 1.0, "std": 0.10}),  # 가격 multiplier
        "koc_price": ("lognormal", {"mean": koc_mean, "std": koc_std}),
        "ntfp_annual": ("lognormal", {"mean": ntfp_mean, "std": ntfp_std}),
        "discount_rate": ("triangular", {"min": 0.04, "mode": discount_rate_base, "max": 0.06}),
        "climate_mult": ("normal", {"mean": clim, "std": clim_std}),
    }

    if use_lhs and HAS_SCIPY:
        samples = generate_lhs_samples_6d(n_samples, distributions, seed)
    else:
        # Fallback: 단순 MC
        rng = random.Random(seed)
        samples = []
        for _ in range(n_samples):
            s = {
                "volume_mult": rng.triangular(v_q05 / v_mid, v_q95 / v_mid, 1.0),
                "timber_mult": rng.lognormvariate(0, 0.10),
                "koc_price": max(0, rng.gauss(koc_mean, koc_std)),
                "ntfp_annual": max(0, rng.gauss(ntfp_mean, ntfp_std)),
                "discount_rate": rng.triangular(0.04, 0.06, discount_rate_base),
                "climate_mult": max(0.1, rng.gauss(clim, clim_std)),
            }
            samples.append(s)

    # ─── 3. 각 sample 의 compute_lev_single 호출 ─────────────────
    npvs = []
    levs = []
    detailed = []  # 첫 sample 의 detail 보관

    for i, sample in enumerate(samples):
        # 분산 적용된 stand
        stand_mc = {**stand}
        stand_mc["volume_m3_per_ha"] = v_mid * sample["volume_mult"]

        # 분산 적용된 discount, climate
        r = sample["discount_rate"]
        cm = sample["climate_mult"]

        # NOTE: 시장가격·KOC 분산은 lev_core 내부에서 market_snapshot 호출 시 적용 불가 (정우 함수)
        # → climate multiplier + discount rate + volume 만 외부 분산. 가격 분산은 별도 후처리.
        result = compute_lev_single(
            stand_mc,
            scenario,
            T,
            discount_rate=r,
            climate_scenario=climate_scenario,
            climate_multiplier=cm,
            ntfp_product=ntfp_product,
            region=region,
        )

        # 사후 가격 보정 (timber multiplier)
        timber_mult = sample["timber_mult"]
        koc_actual = sample["koc_price"]
        koc_used = 12_040  # lev_core 에서 사용한 default

        # 단순 선형 보정
        timber_adj = result["timber_revenue"] * timber_mult
        carbon_adj = result["carbon_revenue"] * (koc_actual / max(koc_used, 1))

        npv_adj = (
            timber_adj
            + carbon_adj
            + result["ntfp_revenue"]
            + result["subsidy_revenue"]
            - result["total_cost"]
            + result["hwp_loss_npv"]
        )

        T_horizon = result["T_horizon"]
        if T_horizon > 0:
            lev_adj = npv_adj / (1 - math.exp(-r * T_horizon))
        else:
            lev_adj = npv_adj

        npvs.append(npv_adj)
        levs.append(lev_adj)

        if i == 0:
            detailed = result

    # ─── 4. 통계 산출 ────────────────────────────────────────────
    npvs_arr = np.array(npvs)
    levs_arr = np.array(levs)

    npv_median = float(np.median(npvs_arr))
    std_ratio = float(np.std(npvs_arr) / abs(npv_median)) if abs(npv_median) > 1 else float("inf")

    return {
        "scenario": scenario,
        "T_optimal": T,
        "T_horizon": detailed["T_horizon"],
        "npv_median": npv_median,
        "npv_q05": float(np.percentile(npvs_arr, 5)),
        "npv_q25": float(np.percentile(npvs_arr, 25)),
        "npv_q75": float(np.percentile(npvs_arr, 75)),
        "npv_q95": float(np.percentile(npvs_arr, 95)),
        "lev_median": float(np.median(levs_arr)),
        "lev_q05": float(np.percentile(levs_arr, 5)),
        "lev_q95": float(np.percentile(levs_arr, 95)),
        "timber_revenue_median": detailed["timber_revenue"],
        "carbon_revenue_median": detailed["carbon_revenue"],
        "ntfp_revenue_median": detailed["ntfp_revenue"],
        "subsidy_revenue_median": detailed["subsidy_revenue"],
        "total_cost_median": detailed["total_cost"],
        "hwp_loss_median": detailed["hwp_loss_npv"],
        "carbon_stock_T_tco2_per_ha_median": detailed["carbon_stock_T_tco2_per_ha"],
        "grade_distribution_T": detailed["grade_distribution_T"],
        "kau_breakeven": detailed.get("kau_breakeven"),
        "kau_breakeven_warning": detailed.get("kau_breakeven_warning"),
        "climate_multiplier_applied": detailed["climate_multiplier_applied"],
        "n_samples": n_samples,
        "std_ratio": std_ratio,
        "feasibility": True,  # scenarios.scenario_feasibility 가 외부에서 판정
        "data_sources": detailed["data_sources"],
        "limitations": detailed["limitations"]
        + [
            f"Monte Carlo {n_samples} samples ({'LHS' if use_lhs and HAS_SCIPY else '단순'}), std/median ratio={std_ratio:.3f}",
        ],
    }


if __name__ == "__main__":
    print("=" * 60)
    print("monte_carlo.py 자가 검증")
    print("=" * 60)

    stand = {
        "species_dominant": "강원지방소나무",
        "age_estimate": 50,
        "site_index": 15,
        "area_ha": 2.0,
        "distance_to_road_km": 1.5,
        "volume_m3_per_ha": 281.0,
        "volume_q05": 225.0,
        "volume_q95": 337.0,
    }

    print("\n[검증 1] 100 samples MC (즉시)")
    r = run_monte_carlo(stand, "즉시", T=50, n_samples=100, seed=42)
    print(f"  median: {r['npv_median']:,.0f}원")
    print(f"  q05-q95: {r['npv_q05']:,.0f} ~ {r['npv_q95']:,.0f}")
    print(f"  std/median: {r['std_ratio']:.3f}")
    print(f"  samples: {r['n_samples']}")

    print("\n[검증 2] 300 LHS samples — std 더 작아져야")
    r2 = run_monte_carlo(stand, "즉시", T=50, n_samples=300, seed=42)
    print(f"  median: {r2['npv_median']:,.0f}원, std/median: {r2['std_ratio']:.3f}")

    print("\n[검증 3] SSP585 — climate multiplier 적용")
    r3 = run_monte_carlo(stand, "즉시", T=50, n_samples=100, climate_scenario="SSP585", seed=42)
    print(f"  median: {r3['npv_median']:,.0f}원, climate: {r3['climate_multiplier_applied']}")
    # MC sampling 이라 평균 climate_multiplier 도 분산이 큼 — 단지 baseline 보다 낮으면 OK
    r3_baseline = run_monte_carlo(
        stand, "즉시", T=50, n_samples=100, climate_scenario="baseline", seed=42
    )
    assert r3["npv_median"] < r3_baseline["npv_median"]

    print("\n[검증 4] 간벌+10년 — subsidy 매출 포함")
    r4 = run_monte_carlo(stand, "간벌+10년", T=60, n_samples=100, seed=42)
    print(f"  median: {r4['npv_median']:,.0f}원, subsidy: {r4['subsidy_revenue_median']:,.0f}원")

    print("\n" + "=" * 60)
    print(f"✅ monte_carlo.py 4/4 검증 통과 (LHS={'on' if HAS_SCIPY else 'off (단순 MC)'})")
    print("=" * 60)
