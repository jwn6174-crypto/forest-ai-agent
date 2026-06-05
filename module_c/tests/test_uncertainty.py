"""test_uncertainty.py — D14 AI 엔지니어 tier 판정."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from uncertainty import (
    classify_uncertainty,
    generate_uncertainty_note,
    get_uncertainty_summary,
)


# [검증] tier 임계값
def test_tier_low_when_narrow():
    """폭 13% < 15% → low"""
    assert classify_uncertainty(100, 93, 107) == "low"


def test_tier_high_when_wide():
    """폭 >50% → high"""
    assert classify_uncertainty(100, 30, 170) == "high"


def test_tier_med_when_middle():
    """폭 30% → med"""
    assert classify_uncertainty(100, 85, 115) == "med"


# [검증] high tier → 점추정 숨김
def test_high_tier_hides_point_estimate():
    s = get_uncertainty_summary(100, 30, 170)
    assert not s["show_point_estimate"]


def test_low_tier_shows_point_estimate():
    s = get_uncertainty_summary(100, 93, 107)
    assert s["show_point_estimate"]


# [검증] note 에 다음 step 포함
def test_high_tier_note_has_next_step():
    n = generate_uncertainty_note("high", has_satellite_data=False, has_nfi_match=False)
    assert "산림조합" in n or "절반" in n or "LiDAR" in n


# [회귀] median = 0 → high
def test_zero_median_returns_high():
    assert classify_uncertainty(0, -10, 10) == "high"


if __name__ == "__main__":
    funcs = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    passed = 0
    for f in funcs:
        try:
            f()
            print(f"  ✅ {f.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {f.__name__}: {e}")
    print(f"\n{passed}/{len(funcs)} passed")
