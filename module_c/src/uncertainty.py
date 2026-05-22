"""
uncertainty.py — q05-q95 폭 → tier {high/med/low} 자동 판정.

AI 엔지니어 deliberation 권고 (D14):
- q05-q95 폭 / median 비율 > 50% → high tier
- 산주 UI 에서 점추정 숨기고 구간 + 다음 step 1개 제시
- LLM prompt 에 uncertainty_tier 필드 주입

희도 D11.c 결정 — 2026-05-20 Day 6 작성
"""

from typing import Literal, Optional

UncertaintyTier = Literal["high", "med", "low"]


def classify_uncertainty(
    npv_median: float,
    npv_q05: float,
    npv_q95: float,
    *,
    high_threshold: float = 0.50,
    low_threshold: float = 0.15,
) -> UncertaintyTier:
    """
    q05-q95 폭 / |median| 비율로 tier 판정.

    Parameters
    ----------
    npv_median, npv_q05, npv_q95 : float
        Monte Carlo 분위수
    high_threshold : float
        폭/median 비율 > 이 값 → high. 기본 0.50 (AI 권고)
    low_threshold : float
        폭/median 비율 < 이 값 → low. 기본 0.15

    Returns
    -------
    "high" | "med" | "low"

    Examples
    --------
    >>> classify_uncertainty(15_000_000, 14_000_000, 16_000_000)
    'low'
    >>> classify_uncertainty(15_000_000, 5_000_000, 25_000_000)
    'high'
    """
    if npv_median == 0:
        return "high"

    width = npv_q95 - npv_q05
    ratio = abs(width / npv_median)

    if ratio > high_threshold:
        return "high"
    if ratio < low_threshold:
        return "low"
    return "med"


def generate_uncertainty_note(
    tier: UncertaintyTier,
    *,
    has_satellite_data: bool = False,
    has_nfi_match: bool = False,
    species: Optional[str] = None,
) -> str:
    """
    Tier 별 LLM-readable note — 다음 step 1개 제시.

    AI 권고: "정확한 값이 아니라 의사결정 참고용" + "LiDAR 측정 시 폭 절반" 같은
    구체적 다음 step.

    Examples
    --------
    >>> generate_uncertainty_note("high", has_satellite_data=False)
    '신뢰도 낮음: 위성 또는 NFI 표본점 측정 없음. 산림조합 현장 조사 시 NPV 추정 폭 절반 감소 예상.'
    """
    if tier == "low":
        return "신뢰도 높음: 데이터 충분."

    if tier == "med":
        if not has_satellite_data:
            return "신뢰도 보통: 위성 AGB 정밀화 시 추정 폭 약 30% 감소 예상."
        return "신뢰도 보통: 임령·site_index 정밀 조사로 보완 가능."

    # high tier
    if not has_satellite_data and not has_nfi_match:
        return (
            "신뢰도 낮음: 위성 또는 NFI 표본점 측정 없음. "
            "산림조합 현장 조사 시 NPV 추정 폭 절반 감소 예상."
        )
    if not has_satellite_data:
        return (
            "신뢰도 낮음: 위성 AGB 미적용 — 임령·체적 측정 직접 확인 필요. "
            "LiDAR 측정 시 폭 절반 감소 예상."
        )
    return "신뢰도 낮음: 가격·할인율 불확실성 큼. 시나리오 4 (연장KOC) 의 KAU 변동 영향 큼."


def get_uncertainty_summary(
    npv_median: float,
    npv_q05: float,
    npv_q95: float,
    **kwargs,
) -> dict:
    """
    classify_uncertainty + generate_uncertainty_note 한번에.

    Returns
    -------
    dict
        {
            "tier": "high" | "med" | "low",
            "note": str,
            "width_to_median_ratio": float,
            "show_point_estimate": bool,  # high 시 False
        }
    """
    tier = classify_uncertainty(npv_median, npv_q05, npv_q95)
    note = generate_uncertainty_note(tier, **kwargs)
    width = npv_q95 - npv_q05
    ratio = abs(width / npv_median) if npv_median != 0 else float("inf")

    return {
        "tier": tier,
        "note": note,
        "width_to_median_ratio": round(ratio, 3),
        "show_point_estimate": tier != "high",
    }


if __name__ == "__main__":
    print("=" * 60)
    print("uncertainty.py 자가 검증")
    print("=" * 60)

    # 검증 1: low (좁은 폭)
    print("\n[검증 1] 폭 13% — low")
    s = get_uncertainty_summary(15_000_000, 14_000_000, 16_000_000)
    print(f"  tier: {s['tier']}, ratio: {s['width_to_median_ratio']}")
    assert s["tier"] == "low"

    # 검증 2: med
    print("\n[검증 2] 폭 30% — med")
    s = get_uncertainty_summary(15_000_000, 12_000_000, 18_000_000)
    print(f"  tier: {s['tier']}, ratio: {s['width_to_median_ratio']}")
    assert s["tier"] == "med"

    # 검증 3: high (133%)
    print("\n[검증 3] 폭 133% — high")
    s = get_uncertainty_summary(15_000_000, 5_000_000, 25_000_000)
    print(f"  tier: {s['tier']}, ratio: {s['width_to_median_ratio']}")
    print(f"  note: {s['note']}")
    assert s["tier"] == "high"
    assert not s["show_point_estimate"]

    # 검증 4: 위성 데이터 없을 때 다음 step
    print("\n[검증 4] high tier + 위성 없음 → 산림조합 현장 조사")
    n = generate_uncertainty_note("high", has_satellite_data=False, has_nfi_match=False)
    print(f"  note: {n}")
    assert "산림조합" in n or "절반" in n

    print("\n" + "=" * 60)
    print("✅ uncertainty.py 4/4 검증 통과")
    print("=" * 60)
