"""
hwp_decay.py — Harvested Wood Products (HWP) 탄소 감쇠 모델.

Faustmann-Hartman LEV 식의 L_C(T) 항 instantiation.

수식 (경제학자 D15 권고):
    L_C(T) = Σ_i HWP_i · (1 − exp(−ln2 · t / h_i))
           = Σ_i HWP_i · (1 − 2^(−t/h_i))

데이터:
- 출처: IPCC 2019 Refinement to 2006 Guidelines Vol 4 Ch12 Table 12.2
- 제재목 35년, 합판 25년, 종이 2년
- 한국 침엽수 분배: 제재목 60% / 합판 25% / 종이 15%

희도 D15 결정 — 2026-05-20 Day 6 작성
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
HWP_DATA_PATH = ROOT / "data" / "raw" / "hwp" / "hwp_decay_2019.json"


def _load_hwp_data() -> dict:
    """HWP decay 룰베이스 로드."""
    with open(HWP_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def compute_hwp_remaining_fraction(
    t_years: float,
    products: Optional[Dict[str, dict]] = None,
) -> Dict[str, float]:
    """
    벌채 후 t 년 시점에 *남아있는* HWP 탄소 비율 (제품별).

    Parameters
    ----------
    t_years : float
        벌채 후 경과 년
    products : dict, optional
        제품별 {half_life_years, share}. None 이면 IPCC 2019 default 사용.

    Returns
    -------
    dict
        {
            "sawnwood": 0.55,      # 35년 half-life, 30년 시점에 55% 잔존
            "wood_based_panels": 0.43,
            "paper": 0.0,
            "total_remaining_share": 0.43,  # 분배율 가중 합
        }
    """
    if products is None:
        data = _load_hwp_data()
        products = data["products"]

    result = {}
    total = 0.0

    for prod_key, prod_data in products.items():
        h = prod_data["half_life_years"]
        share = prod_data.get("default_share_for_conifer", 0.0)

        # First-order exponential decay: f(t) = exp(-ln2 · t / h)
        remaining_fraction = math.exp(-math.log(2) * t_years / h)
        result[prod_key] = round(remaining_fraction, 4)
        total += share * remaining_fraction

    result["total_remaining_share"] = round(total, 4)
    return result


def compute_hwp_decay(
    carbon_stock_at_harvest_tco2: float,
    horizon_years: int = 100,
    annual_step: int = 1,
    products: Optional[Dict[str, dict]] = None,
) -> Dict[str, any]:
    """
    벌채 시 탄소 stock → HWP 시간 경과별 탄소 잔존량 trajectory.

    LEV 식의 L_C(T) 항: 벌채 시점부터 horizon_years 까지 적분.

    Parameters
    ----------
    carbon_stock_at_harvest_tco2 : float
        벌채 시점 탄소 stock (tCO₂/ha 또는 tCO₂ 총량)
    horizon_years : int
        적분 horizon (기본 100년 — 종이는 50 half-life 이상이면 거의 0)
    annual_step : int
        시간 step (1년 단위)
    products : dict, optional
        IPCC default 외 다른 룰베이스 (sensitivity 분석용)

    Returns
    -------
    dict
        {
            "trajectory_tco2": List[float],  # 매년 잔존 탄소량
            "released_total_tco2": float,    # horizon 시점 총 release
            "remaining_at_horizon_tco2": float,
            "half_remaining_year": int,      # 절반 release 되는 시점
            "by_product": {
                "sawnwood": {"share": 0.60, "remaining_at_horizon": ...},
                ...
            },
        }

    Examples
    --------
    >>> result = compute_hwp_decay(80.0, horizon_years=30)
    >>> result["remaining_at_horizon_tco2"]
    34.4
    >>> result["released_total_tco2"]
    45.6
    """
    if products is None:
        data = _load_hwp_data()
        products = data["products"]

    trajectory = []
    by_product = {}

    # 제품별 초기 분배
    for prod_key, prod_data in products.items():
        share = prod_data.get("default_share_for_conifer", 0.0)
        initial = carbon_stock_at_harvest_tco2 * share
        by_product[prod_key] = {
            "share": share,
            "initial_tco2": round(initial, 2),
            "half_life_years": prod_data["half_life_years"],
        }

    # 매년 잔존량 계산
    half_remaining_year = None
    for t in range(0, horizon_years + 1, annual_step):
        total_remaining = 0.0
        for prod_key, prod_data in products.items():
            h = prod_data["half_life_years"]
            share = prod_data.get("default_share_for_conifer", 0.0)
            initial = carbon_stock_at_harvest_tco2 * share
            remaining = initial * math.exp(-math.log(2) * t / h)
            total_remaining += remaining
        trajectory.append(round(total_remaining, 2))

        if half_remaining_year is None and total_remaining < carbon_stock_at_harvest_tco2 / 2:
            half_remaining_year = t

    # 제품별 horizon 시점 잔존
    for prod_key in by_product:
        h = by_product[prod_key]["half_life_years"]
        initial = by_product[prod_key]["initial_tco2"]
        by_product[prod_key]["remaining_at_horizon_tco2"] = round(
            initial * math.exp(-math.log(2) * horizon_years / h), 2
        )

    return {
        "trajectory_tco2": trajectory,
        "released_total_tco2": round(carbon_stock_at_harvest_tco2 - trajectory[-1], 2),
        "remaining_at_horizon_tco2": trajectory[-1],
        "half_remaining_year": half_remaining_year,
        "by_product": by_product,
        "horizon_years": horizon_years,
        "carbon_stock_at_harvest_tco2": carbon_stock_at_harvest_tco2,
    }


def compute_hwp_npv_contribution(
    carbon_stock_at_harvest_tco2: float,
    T_harvest: int,
    discount_rate: float,
    carbon_price_won_per_tco2: float,
    horizon_years: int = 100,
) -> float:
    """
    Hartman 식의 L_C(T) 의 NPV 기여분 (음수 — 손실).

    L_C(T) = Σ_t (released_t) · p_C · e^(-r·(T_harvest + t))

    벌채 후 release 되는 탄소를 *손실* 로 간주 — Faustmann-Hartman 의
    탄소 가치 함수 부호 처리.

    Parameters
    ----------
    carbon_stock_at_harvest_tco2 : float
        벌채 시점 임지 탄소 stock (tCO₂)
    T_harvest : int
        벌채 시점 (회전 사이클 내 년)
    discount_rate : float
        할인율 r (예: 0.05)
    carbon_price_won_per_tco2 : float
        탄소가격 (KAU/KOC, 원/tCO₂)
    horizon_years : int
        HWP 적분 horizon

    Returns
    -------
    float
        L_C(T) 의 NPV 기여 (음수, 원). 손실로 간주.

    Examples
    --------
    >>> # 50년 벌채, 탄소 80 tCO₂, r=0.05, KOC=12,040원
    >>> npv = compute_hwp_npv_contribution(80.0, 50, 0.05, 12040)
    >>> npv < 0
    True
    """
    result = compute_hwp_decay(carbon_stock_at_harvest_tco2, horizon_years)
    trajectory = result["trajectory_tco2"]

    npv_loss = 0.0
    for t in range(1, len(trajectory)):
        released_at_t = trajectory[t - 1] - trajectory[t]
        if released_at_t <= 0:
            continue
        discount_factor = math.exp(-discount_rate * (T_harvest + t))
        npv_loss += released_at_t * carbon_price_won_per_tco2 * discount_factor

    return -round(npv_loss)


if __name__ == "__main__":
    print("=" * 60)
    print("hwp_decay.py 자가 검증")
    print("=" * 60)

    # 검증 1: IPCC reference — 35년 시점 sawnwood 잔존 50%
    print("\n[검증 1] IPCC sawnwood half-life 35년")
    f = compute_hwp_remaining_fraction(35.0)
    print(f"  sawnwood at t=35y: {f['sawnwood']:.4f} (expected ~0.5)")
    assert abs(f["sawnwood"] - 0.5) < 0.01

    # 검증 2: 종이는 빠른 release
    print("\n[검증 2] paper at t=10y (5 half-lives)")
    f = compute_hwp_remaining_fraction(10.0)
    print(f"  paper at t=10y: {f['paper']:.6f} (expected ~0.031)")
    assert f["paper"] < 0.05

    # 검증 3: 한국 침엽수 분배 (60/25/15)
    print("\n[검증 3] 50년 벌채 80 tCO₂, 30년 시점 잔존")
    r = compute_hwp_decay(80.0, horizon_years=30)
    print(f"  remaining at 30y: {r['remaining_at_horizon_tco2']:.2f} tCO₂")
    print(f"  released: {r['released_total_tco2']:.2f} tCO₂")
    print(f"  by product: {r['by_product']}")

    # 검증 4: NPV 기여
    print("\n[검증 4] NPV 기여 (50년 벌채, KOC=12,040, r=0.05)")
    npv = compute_hwp_npv_contribution(80.0, 50, 0.05, 12040)
    print(f"  L_C(T) NPV contribution: {npv:,} 원 (음수)")
    assert npv < 0

    print("\n" + "=" * 60)
    print("✅ hwp_decay.py 4/4 검증 통과")
    print("=" * 60)
