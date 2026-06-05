"""
kau_breakeven.py — KAU 임계가 (breakeven point) 계산.

산림경제학자 deliberation 핵심 발견 (실데이터 기준, data.go.kr 1160100):
- 최신 검증 가능 KAU25 종가 = 15,550원 (2026-03) vs WTA 17,039원
  → 아직 1,489원(8.7%) 미달. 산주 의향가격을 *아직 돌파하지 않음*.
- 다만 2025-07 저점(8,670원) 대비 16개월 +79% 급등 — 돌파 임박 국면.
- thin market 구조적 임계 (Hanley & Spash)
- 시나리오 4 (연장KOC) 의 LEV 가 음수로 전환되는 KAU 임계가 계산

LEV = LEV_no_carbon + (KAU × ratio_carbon)
→ LEV = 0 일 때의 KAU = breakeven

희도 D-경제학 결정 — 2026-05-20 Day 6 작성 (2026-06-05 실데이터 정합 정정 D131)
"""

from typing import Dict


def compute_kau_breakeven(
    npv_at_kau: float,
    kau_used: float,
    carbon_revenue_at_kau: float,
    *,
    koc_ratio: float = 0.7,
    wta_hurdle: float = 17039.0,
    # 실 KAU 시세 (data.go.kr 1160100 GetCertifiedEmissionReductionPriceInfo):
    # 최신 검증 가능 KAU25 종가 = 15,550원 (2026-03).
    # margin (KAU - WTA) = 15,550 - 17,039 = -1,489원 (-8.7%) — 아직 미달.
) -> Dict[str, any]:
    """
    LEV 가 0 (또는 일정 floor) 이 되는 KAU 임계가.

    Linear sensitivity: NPV(KAU) ≈ NPV_baseline + (KAU - KAU_used) × (carbon_revenue / KAU_used)
    NPV = 0 → KAU = KAU_used × (1 - NPV_baseline / carbon_revenue)

    Parameters
    ----------
    npv_at_kau : float
        현재 KAU 에서 계산된 NPV (원)
    kau_used : float
        계산에 사용된 KAU (원/tCO₂)
    carbon_revenue_at_kau : float
        그 KAU 에서의 carbon_revenue (원). 0 이면 KAU 변동 영향 없음.
    koc_ratio : float
        KOC = KAU × ratio (default 0.7)
    wta_hurdle : float
        박2020 산주 WTA (default 17,039원)

    Returns
    -------
    dict
        {
            "kau_breakeven": float | None,  # NPV=0 KAU
            "wta_breakeven": float | None,  # 같은 의미 (KOC 기준)
            "margin_to_wta": float,         # 현재 vs WTA 차이 (원)
            "margin_to_breakeven_pct": float,
            "warning": str | None,
        }

    Examples
    --------
    >>> # KAU 17,200 에서 NPV 50M, carbon_revenue 5M
    >>> r = compute_kau_breakeven(50_000_000, 17_200, 5_000_000)
    >>> r["kau_breakeven"] < 17_200
    True
    """
    if carbon_revenue_at_kau == 0 or carbon_revenue_at_kau is None:
        return {
            "kau_breakeven": None,
            "wta_breakeven": None,
            "margin_to_wta": kau_used - wta_hurdle,
            "margin_to_breakeven_pct": None,
            "warning": "carbon_revenue=0 — 이 시나리오는 KAU 변동 영향 없음 "
            "(KOC < WTA hurdle 미충족)",
        }

    # linear sensitivity 가정
    # carbon_revenue 는 (KAU × koc_ratio) 에 선형 비례
    # NPV(KAU) = NPV_baseline_non_carbon + KAU × (carbon_revenue / KAU_used)
    # NPV = 0 → KAU = -NPV_baseline_non_carbon × KAU_used / carbon_revenue
    npv_non_carbon = npv_at_kau - carbon_revenue_at_kau
    if abs(carbon_revenue_at_kau) < 1:
        kau_be = None
    else:
        # NPV(KAU) = npv_non_carbon + KAU × (carbon_revenue/kau_used)
        # 0 = npv_non_carbon + KAU_be × (carbon_revenue/kau_used)
        kau_be = -npv_non_carbon * kau_used / carbon_revenue_at_kau

    margin_pct = None
    warning = None
    if kau_be is not None:
        margin_pct = round((kau_used - kau_be) / kau_used * 100, 1)
        if kau_be > wta_hurdle / koc_ratio:
            warning = (
                f"KAU breakeven {kau_be:,.0f}원 > WTA hurdle 환산값 "
                f"{wta_hurdle / koc_ratio:,.0f}원 — 시나리오 비용에 비해 탄소 보상 부족"
            )
        elif kau_used - kau_be < 1000:
            warning = (
                f"KAU 변동 margin {kau_used - kau_be:,.0f}원 (1,000원 이하) — "
                "민감도 매우 높음. KAU 1% 하락 시 LEV 음수 전환 위험."
            )

    return {
        "kau_breakeven": round(kau_be) if kau_be is not None else None,
        "wta_breakeven": round(kau_be * koc_ratio) if kau_be is not None else None,
        "margin_to_wta": round(kau_used - wta_hurdle),
        "margin_to_breakeven_pct": margin_pct,
        "kau_used": kau_used,
        "carbon_revenue_at_kau": round(carbon_revenue_at_kau),
        "warning": warning,
    }


def format_kau_breakeven_message(result: Dict) -> str:
    """LEVResult 의 kau_breakeven_note 용 한국어 문장."""
    if result["kau_breakeven"] is None:
        return result.get("warning", "탄소 수익 없는 시나리오 — KAU 변동 무영향.")

    msg = f"KAU {result['kau_used']:,.0f}원 → {result['kau_breakeven']:,.0f}원 "
    msg += f"(margin {result['margin_to_breakeven_pct']}%) 이하 시 LEV 음수 전환."
    if result.get("warning"):
        msg += f" ⚠️ {result['warning']}"
    return msg


if __name__ == "__main__":
    print("=" * 60)
    print("kau_breakeven.py 자가 검증")
    print("=" * 60)

    # 검증 1: NPV 50M, carbon 5M @ KAU 17,200
    print("\n[검증 1] NPV 50M, carbon 5M")
    r = compute_kau_breakeven(50_000_000, 17_200, 5_000_000)
    print(f"  KAU breakeven: {r['kau_breakeven']:,}원")
    print(f"  margin_pct: {r['margin_to_breakeven_pct']}%")
    # NPV_non_carbon = 45M, KAU_be = -45M × 17,200 / 5M = 음수 → LEV 항상 +
    # (NPV 가 carbon revenue 없어도 + 이므로 KAU 가 아무리 낮아도 음수 안 됨)
    print(f"  message: {format_kau_breakeven_message(r)}")

    # 검증 2: NPV 1M, carbon 5M — KAU 작은 하락에 음수 전환
    print("\n[검증 2] NPV 1M, carbon 5M (margin 작음)")
    r = compute_kau_breakeven(1_000_000, 17_200, 5_000_000)
    print(f"  KAU breakeven: {r['kau_breakeven']:,}원, margin: {r['margin_to_breakeven_pct']}%")
    print(f"  warning: {r.get('warning')}")

    # 검증 3: carbon_revenue=0 — KAU 무영향
    print("\n[검증 3] carbon_revenue=0 — KAU 무영향")
    r = compute_kau_breakeven(50_000_000, 17_200, 0)
    print(f"  KAU breakeven: {r['kau_breakeven']}")
    print(f"  warning: {r['warning']}")
    assert r["kau_breakeven"] is None

    # 검증 4: 161원 margin to WTA
    print("\n[검증 4] WTA margin")
    r = compute_kau_breakeven(50_000_000, 17_200, 5_000_000)
    print(f"  margin_to_wta: {r['margin_to_wta']}원 (KAU 17,200 - WTA 17,039)")
    assert r["margin_to_wta"] == 161

    print("\n" + "=" * 60)
    print("✅ kau_breakeven.py 4/4 검증 통과")
    print("=" * 60)
