"""
test_grade_distribution.py — grade_distribution() 단위 테스트.

두 종류로 구분:
  [검증] 물리 법칙·통계 항등식이 보증하는 값. 코드가 어기면 코드가 오류.
  [회귀] 현재 코드의 출력을 기준선으로 고정. 의도치 않은 변경 감지용.

D14 (Weibull 등급분포): NFI 7차 충북 46,722 그루 fit.
등급: 소경재 6-18cm / 중경재 18-30cm / 대경재 30cm+.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from grade_distribution import (
    grade_distribution,
    grade_distribution_trajectory,
)

GRADES = ['소경재', '중경재', '대경재']

# ────────────────────────────────────────────────
# [검증] 비율·정규화 항등식
# ────────────────────────────────────────────────

def test_proportions_sum_to_one():
    """등급 비율 합 ≈ 1 (6cm 이상 전체 커버, 정규화)."""
    r = grade_distribution(5, '혼효림(M)')
    total = sum(r['proportions'].values())
    # CDF(6)=0 부터 CDF(inf)=1 까지 → 합 ≈ 1
    assert 0.98 <= total <= 1.001, f"비율 합 {total}"


def test_counts_sum_matches_input():
    """등급별 본수 합 ≈ 입력 본수 (반올림 오차 내)."""
    n_total = 800
    r = grade_distribution(5, '혼효림(M)', n_total)
    count_sum = sum(r[g] for g in GRADES)
    # 반올림 오차 ±3 본 허용
    assert abs(count_sum - n_total) <= 3, f"본수 합 {count_sum} vs {n_total}"


def test_all_counts_nonnegative():
    """모든 등급 본수 ≥ 0."""
    r = grade_distribution(4, '활엽수림(H)', 1000)
    for g in GRADES:
        assert r[g] >= 0, f"{g} 본수 음수: {r[g]}"


# ────────────────────────────────────────────────
# [검증] 물리 법칙 — 영급과 대경재 단조성
# ────────────────────────────────────────────────

def test_daekyeong_increases_with_age():
    """영급 ↑ → 대경재 비율 ↑ (생장 물리 법칙, 2→6영급)."""
    prev = -1
    for ac in [2, 3, 4, 5, 6]:
        r = grade_distribution(ac, None, 1000)
        total = sum(r['proportions'].values())
        daekyeong_prop = r['proportions']['대경재'] / total
        assert daekyeong_prop >= prev, (
            f"{ac}영급 대경재 비율 {daekyeong_prop:.3f} < 이전 {prev:.3f}"
        )
        prev = daekyeong_prop


def test_young_stand_few_large_trees():
    """어린 임분 (2영급) 대경재 비율 ~0 (큰 나무 거의 없음)."""
    r = grade_distribution(2, None, 1000)
    total = sum(r['proportions'].values())
    daekyeong_prop = r['proportions']['대경재'] / total
    assert daekyeong_prop < 0.02, f"2영급 대경재 {daekyeong_prop:.3f} (너무 큼)"


def test_sokyeong_dominates_young():
    """어린 임분 (2영급) 소경재 우세 (대부분 작은 나무)."""
    r = grade_distribution(2, None, 1000)
    total = sum(r['proportions'].values())
    sokyeong_prop = r['proportions']['소경재'] / total
    assert sokyeong_prop > 0.9, f"2영급 소경재 {sokyeong_prop:.3f} (너무 작음)"


# ────────────────────────────────────────────────
# [검증] fallback 동작
# ────────────────────────────────────────────────

def test_imsang_group_no_fallback():
    """영급 × 임상 그룹 존재 → fallback 안 함."""
    r = grade_distribution(5, '혼효림(M)', 800)
    assert r['fallback'] is False
    assert r['group_key'] == "5_혼효림(M)"


def test_imsang_none_uses_age_fallback():
    """임상 None → 영급 fallback 사용."""
    r = grade_distribution(4, None, 1000)
    assert r['fallback'] is True
    assert '4' in r['group_key']


def test_missing_group_nearest_fallback():
    """존재하지 않는 영급 → 가장 가까운 영급 fallback."""
    # 15영급은 데이터 없음 → 가장 가까운 (최대 8영급) fallback
    r = grade_distribution(15, None, 1000)
    assert r['fallback'] is True
    # 본수 정상 산출
    assert sum(r[g] for g in GRADES) > 0


# ────────────────────────────────────────────────
# [검증] trajectory
# ────────────────────────────────────────────────

def test_trajectory_length():
    """trajectory 길이 = forecast_years 길이."""
    traj = grade_distribution_trajectory(
        age_class_now=4, imsang='혼효림(M)',
        n_per_ha_trajectory=[1200, 900, 700, 550],
        forecast_years=[0, 10, 20, 30],
    )
    assert len(traj) == 4


def test_trajectory_age_class_increases():
    """trajectory 영급 시간 따라 증가 (10년마다 +1영급)."""
    traj = grade_distribution_trajectory(
        age_class_now=4, imsang='혼효림(M)',
        n_per_ha_trajectory=[1200, 900, 700, 550],
        forecast_years=[0, 10, 20, 30],
    )
    age_classes = [t['age_class'] for t in traj]
    assert age_classes == [4, 5, 6, 7]


# ────────────────────────────────────────────────
# [회귀] 현재 출력 기준선 (의도치 않은 변경 감지)
# ────────────────────────────────────────────────

def test_regression_5yeong_honhyo_params():
    """5영급 혼효림 Weibull 모수 기준선 (shape 1.234, scale 12.02)."""
    r = grade_distribution(5, '혼효림(M)', 800)
    assert abs(r['shape'] - 1.234) < 0.01, f"shape {r['shape']}"
    assert abs(r['scale'] - 12.02) < 0.05, f"scale {r['scale']}"


def test_regression_5yeong_honhyo_counts():
    """5영급 혼효림 800본 등급별 본수 기준선."""
    r = grade_distribution(5, '혼효림(M)', 800)
    # 현재 출력: 소경 505, 중경 218, 대경 76
    assert r['소경재'] == 505, f"소경재 {r['소경재']}"
    assert r['중경재'] == 218, f"중경재 {r['중경재']}"
    assert r['대경재'] == 76, f"대경재 {r['대경재']}"


def test_regression_age_fallback_proportions():
    """영급 fallback 비율 기준선 (4영급: 소경 67.4%, 중경 25.8%, 대경 6.8%)."""
    r = grade_distribution(4, None, 1000)
    total = sum(r['proportions'].values())
    assert abs(r['proportions']['소경재'] / total - 0.674) < 0.01
    assert abs(r['proportions']['대경재'] / total - 0.068) < 0.01