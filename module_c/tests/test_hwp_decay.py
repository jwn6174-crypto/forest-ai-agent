"""test_hwp_decay.py — IPCC 2019 Refinement reference 검증 (D15)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import math
from hwp_decay import (
    compute_hwp_remaining_fraction,
    compute_hwp_decay,
    compute_hwp_npv_contribution,
)


# [검증] IPCC 2019 reference half-life
def test_sawnwood_half_life_35y():
    f = compute_hwp_remaining_fraction(35.0)
    assert abs(f["sawnwood"] - 0.5) < 0.01


def test_panels_half_life_25y():
    f = compute_hwp_remaining_fraction(25.0)
    assert abs(f["wood_based_panels"] - 0.5) < 0.01


def test_paper_half_life_2y():
    f = compute_hwp_remaining_fraction(2.0)
    assert abs(f["paper"] - 0.5) < 0.01


# [검증] 한국 침엽수 분배 (60/25/15)
def test_total_remaining_share_at_t0():
    f = compute_hwp_remaining_fraction(0.0)
    assert abs(f["total_remaining_share"] - 1.0) < 0.01


def test_decay_30yr_reference():
    """80 tCO₂ × 30년 → 잔존 약 35.2 (제재목 55%·합판 43%·종이 0%)"""
    r = compute_hwp_decay(80.0, horizon_years=30)
    assert abs(r["remaining_at_horizon_tco2"] - 35.2) < 1.0


# [회귀] NPV 기여는 음수
def test_npv_contribution_negative():
    npv = compute_hwp_npv_contribution(80.0, 50, 0.05, 12040)
    assert npv < 0


def test_paper_almost_zero_at_30y():
    """종이는 30년 = 15 half-lives → 잔존 거의 0"""
    f = compute_hwp_remaining_fraction(30.0)
    assert f["paper"] < 0.001


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
