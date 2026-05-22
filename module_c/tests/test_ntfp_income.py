"""test_ntfp_income.py — D13 NTFP 2024 보고서 reference."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ntfp_income import lookup_ntfp, compute_ntfp_npv


# [검증] 2024 보고서 reference 가격
def test_shiitake_mean_5_5M():
    r = lookup_ntfp("shiitake_oak_log", species_host="참나무류")
    assert r["mean"] == 5_500_000


def test_pine_mushroom_mean_1_5M():
    r = lookup_ntfp("pine_mushroom", species_host="강원지방소나무")
    assert r["mean"] == 1_500_000


# [검증] 산림학자 권고 — 송이 carbon impact 분리 (S5b)
def test_pine_mushroom_carbon_impact_negative():
    r = lookup_ntfp("pine_mushroom", species_host="강원지방소나무")
    assert "-15" in r["carbon_impact_on_pine"]


def test_shiitake_carbon_impact_positive():
    r = lookup_ntfp("shiitake_oak_log", species_host="참나무류")
    assert "+" in r["carbon_impact_on_pine"]


# [검증] host species 매칭
def test_pine_mushroom_only_applies_to_pine():
    r = lookup_ntfp("pine_mushroom", species_host="강원지방소나무")
    assert r["applicable_to_species"]


def test_pine_mushroom_not_applies_to_oak():
    r = lookup_ntfp("pine_mushroom", species_host="참나무류")
    assert not r["applicable_to_species"]


# [회귀] 15년 표고 NPV > 0
def test_shiitake_15yr_npv_positive():
    r = compute_ntfp_npv("shiitake_oak_log", duration_years=15, discount_rate=0.05)
    assert r["npv"] > 0


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
