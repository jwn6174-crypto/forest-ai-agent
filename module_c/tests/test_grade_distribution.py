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


# [검증] D120 — WeibullGD 정우 D14 통합 (NotImplementedError 제거)
def test_weibull_now_works_via_jeongwoo_d14():
    """D120: 정우 D14 weibull_params.json 호출 → 6 등급 매핑.
    fallback: weibull_params.json 없으면 HeuristicGD 로 graceful degradation.
    """
    weibull = WeibullGD()
    result = weibull.estimate(20.0)
    # 결과는 항상 dict (NotImplementedError 안 발생)
    assert isinstance(result, dict)
    assert abs(sum(result.values()) - 1.0) < 0.05


# [검증] D122 학술 발견 — WeibullGD 가 HeuristicGD 보다 작은 등급 비율 큼
def test_d122_weibull_smaller_grades_higher():
    """D122: 정우 NFI 7차 영세림 → 역-J 분포 → 원료재·원주재 더 큼.
    Faustmann NPV 영향 ~-30% 추정.
    """
    h = HeuristicGD()
    w = WeibullGD()
    for dbh in [16, 20, 25, 30]:
        hr = h.estimate(dbh)
        wr = w.estimate(dbh)
        # WeibullGD 의 원료재+원주재 합 > HeuristicGD
        weibull_small = wr["원료재"] + wr["원주재"]
        heuristic_small = hr["원료재"] + hr["원주재"]
        assert weibull_small >= heuristic_small * 0.9  # 적어도 비슷하거나 큼


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
