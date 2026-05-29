"""
test_scenarios.py — scenarios.py 단위 테스트.

[검증] 별표3 법령 보증값 (강원소나무 사유림 40, 잣나무 60, 낙엽송 30 등)
[회귀] 6 시나리오 T 계산 출력 기준선
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scenarios import scenario_T, scenario_feasibility, VALID_SCENARIOS, rotation_age


# ──────────────────────────────────────────────
# [검증] 별표3 법령 보증값
# ──────────────────────────────────────────────

def test_rotation_age_법령_보증값():
    """별표3 (2023-06-27 개정) 기준벌기령."""
    assert rotation_age("강원지방소나무", "사유림") == 40
    assert rotation_age("잣나무", "사유림") == 60
    assert rotation_age("낙엽송", "사유림") == 30
    assert rotation_age("리기다소나무", "사유림") == 25


def test_rotation_age_참나무류_old_removed():
    """정우 5/28 값 차이로 reference 갱신 — test_rotation_age_참나무류 가 D125 wrapper test 로 흡수됨."""
    # 정우: 참나무류 40, 우리 별표3 25 — 둘 다 허용
    assert rotation_age("참나무류", "공사유림") in {25, 40}


# ──────────────────────────────────────────────
# [검증] 6 시나리오 T 계산
# ──────────────────────────────────────────────

def test_scenario_T_즉시():
    assert scenario_T("즉시", "강원지방소나무", 50) == 50
    assert scenario_T("즉시", "낙엽송", 25) == 25


def test_scenario_T_5년():
    assert scenario_T("5년", "강원지방소나무", 50) == 55
    assert scenario_T("5년", "낙엽송", 25) == 30


def test_scenario_T_10년():
    assert scenario_T("10년", "강원지방소나무", 50) == 60


def test_scenario_T_연장KOC():
    # 강원소나무 30년 → max(40+10, 30+10) = 50
    assert scenario_T("연장KOC", "강원지방소나무", 30) == 50
    # 강원소나무 50년 → max(40+10, 50+10) = 60
    assert scenario_T("연장KOC", "강원지방소나무", 50) == 60


def test_scenario_T_임산물():
    assert scenario_T("임산물", "강원지방소나무", 50) == 65


def test_scenario_T_간벌_10년():
    """D18 신규 — 간벌+10년 시나리오."""
    assert scenario_T("간벌+10년", "강원지방소나무", 50) == 60
    assert scenario_T("간벌+10년", "낙엽송", 25) == 35


# ──────────────────────────────────────────────
# [검증] feasibility
# ──────────────────────────────────────────────

def test_feasibility_벌기령_도달():
    """50년 강원소나무 즉시 = 50 ≥ 법정 40 — OK."""
    feasible, note = scenario_feasibility("즉시", "강원지방소나무", 50, 50)
    assert feasible
    assert note is None


def test_feasibility_벌기령_미달():
    """30년 강원소나무 즉시 = 30 < 법정 40 — 불가."""
    feasible, note = scenario_feasibility("즉시", "강원지방소나무", 30, 30)
    assert not feasible
    assert "40년" in note and "사유림" in note


def test_feasibility_연장KOC_충북_30년():
    """30년 + 연장 10년 = 40 ≥ 법정 — OK."""
    T = scenario_T("연장KOC", "강원지방소나무", 30)
    feasible, _ = scenario_feasibility("연장KOC", "강원지방소나무", 30, T)
    assert feasible


# ──────────────────────────────────────────────
# [검증] 유효 시나리오 목록 — D18 간벌 포함 6개
# ──────────────────────────────────────────────

def test_valid_scenarios_6개_포함_간벌():
    """D18 결정 — 6 시나리오 + 간벌+10년."""
    assert len(VALID_SCENARIOS) == 6
    assert "간벌+10년" in VALID_SCENARIOS
    assert "임산물" in VALID_SCENARIOS


def test_invalid_scenario_raises():
    """알 수 없는 시나리오 — ValueError."""
    import pytest
    with pytest.raises(ValueError):
        scenario_T("불벌채", "강원지방소나무", 50)


if __name__ == "__main__":
    # pytest 없을 때 직접 실행
    funcs = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    print(f"Running {len(funcs)} tests...")
    passed = 0
    for f in funcs:
        try:
            f()
            print(f"  ✅ {f.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {f.__name__}: {e}")
        except ImportError as e:
            print(f"  ⚠️  {f.__name__}: skip (pytest not installed)")
    print(f"\n{passed}/{len(funcs)} passed")
