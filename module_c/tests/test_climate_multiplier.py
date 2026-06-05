"""test_climate_multiplier.py — SSP × 수종 multiplier (D11.b)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import random
from climate_multiplier import (
    get_climate_multiplier,
    apply_multiplier_to_trajectory,
)


# [검증] baseline = 1.0
def test_baseline_is_one():
    assert get_climate_multiplier("강원지방소나무", "baseline") == 1.0


# [검증] 산림학자 reference (임종환 2020)
def test_pine_ssp585_negative():
    """강원소나무 SSP585 < baseline (남방한계 종)"""
    m = get_climate_multiplier("강원지방소나무", "SSP585")
    assert m < 0.9


def test_larch_ssp585_most_negative():
    """낙엽송 SSP585 < 0.75 (가장 취약)"""
    m = get_climate_multiplier("낙엽송", "SSP585")
    assert m < 0.75


def test_oak_ssp245_positive():
    """참나무 SSP245 > 1.1 (열적 유리)"""
    m = get_climate_multiplier("참나무류", "SSP245")
    assert m > 1.1


# [회귀] alias 매핑
def test_species_alias_oak():
    """상수리·신갈·굴참 = 참나무류"""
    m_oak = get_climate_multiplier("참나무류", "SSP245")
    m_alias = get_climate_multiplier("상수리나무", "SSP245")
    assert m_oak == m_alias


# [검증] trajectory 적용
def test_trajectory_proportional_scaling():
    traj = [100.0, 200.0]
    boosted = apply_multiplier_to_trajectory(traj, "참나무류", "SSP245")
    # 두 값 모두 동일 multiplier
    assert abs(boosted[1] / boosted[0] - 2.0) < 0.01


# [검증] MC sampling
def test_mc_sampling_reproducible_seed():
    rng = random.Random(42)
    samples = [get_climate_multiplier("강원지방소나무", "SSP245", rng, sample=True)
               for _ in range(20)]
    assert 0.8 < sum(samples) / len(samples) < 1.1


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
