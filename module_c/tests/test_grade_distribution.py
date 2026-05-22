"""test_grade_distribution.py — D14 Strategy 패턴."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from grade_distribution import (
    estimate_grade_distribution,
    HeuristicGD, WeibullGD, GRADE_BOUNDS_CM,
)


# [검증] 합 = 1.0
def test_sum_equals_one_small_dbh():
    d = estimate_grade_distribution(12.0)
    assert abs(sum(d.values()) - 1.0) < 0.05


def test_sum_equals_one_medium_dbh():
    d = estimate_grade_distribution(22.0)
    assert abs(sum(d.values()) - 1.0) < 0.05


def test_sum_equals_one_large_dbh():
    d = estimate_grade_distribution(40.0)
    assert abs(sum(d.values()) - 1.0) < 0.05


# [검증] DBH 증가 → 상위 등급 비율 증가
def test_large_dbh_has_more_premium_grades():
    d_small = estimate_grade_distribution(14.0)
    d_large = estimate_grade_distribution(34.0)
    premium_small = d_small["특용재"] + d_small["1등급"]
    premium_large = d_large["특용재"] + d_large["1등급"]
    assert premium_large > premium_small


# [검증] WeibullGD NotImplementedError (W4 협업 전)
def test_weibull_not_implemented():
    import pytest
    weibull = WeibullGD()
    try:
        weibull.estimate(20.0)
        assert False, "예상한 NotImplementedError 발생 안 함"
    except NotImplementedError:
        pass


# [회귀] HeuristicGD 정우 reference (DBH=20 → 1등급 ~10%)
def test_heuristic_dbh_20_reference():
    d = estimate_grade_distribution(20.0)
    assert d["1등급"] >= 0.05


# [검증] 6 등급 모두 포함
def test_six_grades_all_present():
    d = estimate_grade_distribution(20.0)
    expected = {"특용재", "1등급", "2등급", "3등급", "원주재", "원료재"}
    assert set(d.keys()) == expected


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
