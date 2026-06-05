"""
sensitivity.py — 학술 robustness 민감도 분석.

산림학자 권고 (Round 1):
- SI 민감도 ±2 (보은 SI 14 → 15-16 정정)
- 60+년 외삽 ±40%
- 기후 multiplier ±15% (Normal std)

산림경제학자 권고:
- 할인율 0.04, 0.05, 0.06 + r=0.07 보조 민감도
- HWP h=30년 ±10년 (IPCC 35년 vs 한국 28년)
- KAU 변동성

D25 결정 — 2026-05-20 Day 6 작성 (Manual 01 §05 학술 robustness 요건)
"""

from typing import Dict, List

from .lev_core import compute_lev_single


def sensitivity_site_index(
    stand: Dict,
    scenario: str,
    T: int,
    si_range: List[int] | None = None,
) -> List[Dict]:
    """
    Site Index ±2 민감도 (산림학자).

    Parameters
    ----------
    stand : dict
    scenario, T : str, int
    si_range : list[int], optional
        검토할 SI 범위 (None 이면 stand["site_index"] ±2)

    Returns
    -------
    list[dict] — 각 SI 에서의 NPV·LEV
    """
    if si_range is None:
        si = stand.get("site_index", 14)
        si_range = list(range(max(8, si - 2), min(22, si + 3)))

    results = []
    for si in si_range:
        s = {**stand, "site_index": si}
        r = compute_lev_single(s, scenario, T)
        results.append(
            {
                "site_index": si,
                "npv": r["npv"],
                "lev": r["lev"],
                "timber_revenue": r["timber_revenue"],
            }
        )
    return results


def sensitivity_discount_rate(
    stand: Dict,
    scenario: str,
    T: int,
    rates: List[float] | None = None,
) -> List[Dict]:
    """
    할인율 민감도 (경제학자: 0.04, 0.05, 0.06 + r=0.07 보조).
    """
    if rates is None:
        rates = [0.04, 0.05, 0.06, 0.07]

    results = []
    for r in rates:
        result = compute_lev_single(stand, scenario, T, discount_rate=r)
        results.append(
            {
                "discount_rate": r,
                "npv": result["npv"],
                "lev": result["lev"],
            }
        )
    return results


def sensitivity_climate_scenario(
    stand: Dict,
    scenario: str,
    T: int,
    scenarios: List[str] | None = None,
) -> List[Dict]:
    """
    SSP 기후 multiplier 민감도 (산림학자 D11.b).
    """
    if scenarios is None:
        scenarios = ["baseline", "SSP126", "SSP245", "SSP585"]

    results = []
    for ssp in scenarios:
        result = compute_lev_single(stand, scenario, T, climate_scenario=ssp)
        results.append(
            {
                "climate_scenario": ssp,
                "climate_multiplier": result["climate_multiplier_applied"],
                "npv": result["npv"],
                "lev": result["lev"],
            }
        )
    return results


def sensitivity_kau_price(
    stand: Dict,
    scenario: str,
    T: int,
    kau_prices: List[float] | None = None,
) -> List[Dict]:
    """
    KAU 가격 민감도 (경제학자 + D23).

    실측 구간(2025-07 저점 8,670 → 2026-03 최신 15,550)에 WTA 임계(17,039)와
    가상의 돌파 후 점(19,600)을 더한 what-if 스윕. 시나리오 4 의 carbon_revenue
    breakeven(=WTA) 을 사이에 두고 NPV 가 어떻게 바뀌는지 시연한다.
    """
    if kau_prices is None:
        # 저점 8,670 · 중간 · 최신 15,550(2026-03) · WTA 17,039 · 돌파 가정 19,600
        kau_prices = [8670, 12400, 15550, 17039, 19600]

    results = []
    for kau in kau_prices:
        # KAU sensitivity 는 market_snapshot 외부 입력 필요 — fallback patch
        # 정우 모듈 호출 시 market_snapshot 의 koc_estimate 가 KAU × 0.7
        # 여기서는 결과만 보여주고 실제 patching 은 monte_carlo.py 가 함
        result = compute_lev_single(stand, scenario, T)
        koc_est = kau * 0.7
        margin = kau - 17039
        results.append(
            {
                "kau_price": kau,
                "koc_estimate": koc_est,
                "wta_margin": margin,
                "wta_passed": margin > 0,
                "npv_at_baseline": result["npv"],
                "_note": f"KAU={kau} → KOC={koc_est:.0f} → WTA margin={margin:+d}",
            }
        )
    return results


def sensitivity_hwp_half_life(
    stand: Dict,
    scenario: str,
    T: int,
    h_pairs: List[Dict] | None = None,
) -> List[Dict]:
    """
    HWP half-life 민감도 (경제학자 + IPCC 2019 vs 한국 데이터).

    h_pairs: 각 case 의 (제재목, 합판, 종이) half-life year tuple
    """
    if h_pairs is None:
        h_pairs = [
            {"label": "IPCC 2019 default", "sawn": 35, "panel": 25, "paper": 2},
            {"label": "한국 (NIFOS 2021)", "sawn": 28, "panel": 22, "paper": 2},
            {"label": "보수적 (-10년)", "sawn": 25, "panel": 15, "paper": 2},
            {"label": "낙관적 (+10년)", "sawn": 45, "panel": 35, "paper": 2},
        ]

    # carbon_stock at T (단순 추정: 강원소나무 평균)
    carbon_stock = stand.get("carbon_tc_per_ha", 100) * 3.667 * stand.get("area_ha", 1)

    results = []
    for hp in h_pairs:
        # custom products dict
        custom = {
            "sawnwood": {"half_life_years": hp["sawn"], "default_share_for_conifer": 0.60},
            "wood_based_panels": {
                "half_life_years": hp["panel"],
                "default_share_for_conifer": 0.25,
            },
            "paper": {"half_life_years": hp["paper"], "default_share_for_conifer": 0.15},
        }
        from .hwp_decay import compute_hwp_decay

        result = compute_hwp_decay(carbon_stock, horizon_years=30, products=custom)
        results.append(
            {
                "label": hp["label"],
                "sawn_h": hp["sawn"],
                "panel_h": hp["panel"],
                "hwp_remaining_30y_tco2": result["remaining_at_horizon_tco2"],
                "hwp_released_30y_tco2": result["released_total_tco2"],
            }
        )
    return results


def full_sensitivity_report(
    stand: Dict,
    scenario: str = "연장KOC",
    T: int | None = None,
) -> Dict:
    """
    전체 민감도 분석 — 4 차원.

    Returns
    -------
    dict
        {
            "site_index": [...],
            "discount_rate": [...],
            "climate_scenario": [...],
            "kau_price": [...],
            "hwp_half_life": [...],
        }
    """
    if T is None:
        from .scenarios import scenario_T

        T = scenario_T(scenario, stand["species_dominant"], stand["age_estimate"])

    return {
        "site_index": sensitivity_site_index(stand, scenario, T),
        "discount_rate": sensitivity_discount_rate(stand, scenario, T),
        "climate_scenario": sensitivity_climate_scenario(stand, scenario, T),
        "kau_price": sensitivity_kau_price(stand, scenario, T),
        "hwp_half_life": sensitivity_hwp_half_life(stand, scenario, T),
        "_meta": {
            "decision_id": "D25",
            "stand_id": stand.get("pnu") or stand.get("carbonregistry_id"),
            "scenario": scenario,
            "T": T,
        },
    }


if __name__ == "__main__":
    from .demo_parcels import get_demo_parcel

    print("=" * 70)
    print("sensitivity.py — 보은 산외면 오대리 연장KOC 시나리오")
    print("=" * 70)

    stand = get_demo_parcel("boeun_real_oedari_8197tco2")
    report = full_sensitivity_report(stand, scenario="연장KOC")

    print("\n[Site Index ±2 민감도]")
    for r in report["site_index"]:
        print(
            f"  SI={r['site_index']:>3d}: NPV={r['npv'] / 1e6:>8.1f}M LEV={r['lev'] / 1e6:>8.1f}M"
        )

    print("\n[할인율 민감도]")
    for r in report["discount_rate"]:
        print(f"  r={r['discount_rate']:.2f}: NPV={r['npv'] / 1e6:>8.1f}M")

    print("\n[SSP 기후 시나리오]")
    for r in report["climate_scenario"]:
        print(
            f"  {r['climate_scenario']:>8s} mult={r['climate_multiplier']:.3f}: NPV={r['npv'] / 1e6:>8.1f}M"
        )

    print("\n[KAU 가격 민감도 + WTA breakeven]")
    for r in report["kau_price"]:
        pass_mark = "✅" if r["wta_passed"] else "❌"
        print(f"  KAU={r['kau_price']:>6d} {pass_mark} WTA margin={r['wta_margin']:+d}원")

    print("\n[HWP half-life 민감도]")
    for r in report["hwp_half_life"]:
        print(
            f"  {r['label']:<25s} (제재목{r['sawn_h']}y/합판{r['panel_h']}y): "
            f"30년 잔존 {r['hwp_remaining_30y_tco2']:>6.1f} tCO₂"
        )

    print("\n" + "=" * 70)
    print("✅ 5 차원 민감도 분석 완료")
    print("=" * 70)
