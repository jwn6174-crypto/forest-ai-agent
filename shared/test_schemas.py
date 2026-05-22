"""
test_schemas.py — shared/schemas.py 추가분 (LEVResult 등 D9) 단위 테스트.

정우 D4 옵션 P2 패턴 검증 (가이드 호환 + 확장 Optional).

[검증] Manual 01 §4.1 명세 매칭
[회귀] D9 schema 출력 기준선
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from schemas import LEVResult, ComputeLEVRequest, DraftPlanCard


# ──────────────────────────────────────────────
# [검증] Manual 01 §4.1 필수 필드만으로 생성
# ──────────────────────────────────────────────

def _base_lev_result(**override):
    """D-fixture: 보은 50년 강원소나무 즉시 — 표준 LEVResult."""
    args = dict(
        scenario="즉시",
        T_optimal=50,
        npv_per_ha=15_000_000,
        npv_q05=10_000_000,
        npv_q95=22_000_000,
        lev_per_ha=12_000_000,
        timber_revenue=18_000_000,
        carbon_revenue=0,
        total_cost=3_000_000,
        carbon_stock_T=85.5,
        grade_distribution_T={"1등급": 0.3, "2등급": 0.5, "3등급": 0.2},
        feasibility=True,
    )
    args.update(override)
    return LEVResult(**args)


def test_lev_result_가이드_필수_필드만():
    r = _base_lev_result()
    assert r.scenario == "즉시"
    assert r.T_optimal == 50
    assert r.npv_per_ha == 15_000_000


def test_lev_result_확장_필드_포함():
    r = LEVResult(
        scenario="연장KOC",
        T_optimal=60,
        npv_per_ha=22_000_000,
        npv_q05=15_000_000, npv_q95=30_000_000,
        lev_per_ha=18_000_000,
        timber_revenue=25_000_000, carbon_revenue=3_500_000,
        total_cost=4_500_000,
        carbon_stock_T=156.2,
        grade_distribution_T={"특용재": 0.05, "1등급": 0.40, "2등급": 0.40, "3등급": 0.15},
        feasibility=True,
        cost_breakdown={"harvest": 1.2e6, "skidding": 1.1e6, "transport": 1.5e6,
                        "loading": 0.3e6, "regen": 0.7e6, "admin": 0.7e6},
        data_sources={"timber_price": "KOFPI Q4 2025",
                      "rotation": "별표 3 (2023-06-27)"},
        limitations=["60년 초과 외삽"],
        uncertainty_tier="med",
        kau_breakeven=15_000,
    )
    assert r.cost_breakdown["transport"] == 1.5e6
    assert r.uncertainty_tier == "med"
    assert r.kau_breakeven == 15_000


def test_lev_result_feasibility_false():
    """feasibility=False 시 note 제공."""
    r = _base_lev_result(feasibility=False, feasibility_note="T=30년 < 법정 40년")
    assert not r.feasibility
    assert "법정" in r.feasibility_note


def test_lev_result_uncertainty_tier_default():
    """기본 tier='med'."""
    r = _base_lev_result()
    assert r.uncertainty_tier == "med"


def test_lev_result_t_optimal_range():
    """T_optimal 0-200 범위 검증."""
    import pytest
    try:
        from pydantic import ValidationError
    except ImportError:
        return  # skip
    with pytest.raises(ValidationError):
        _base_lev_result(T_optimal=250)


# ──────────────────────────────────────────────
# [검증] ComputeLEVRequest
# ──────────────────────────────────────────────

def test_compute_lev_request_기본():
    req = ComputeLEVRequest(
        stand_state={"pnu": "4374025931200220000", "species_dominant": "강원지방소나무"},
        scenarios=["즉시", "10년", "연장KOC"],
    )
    assert len(req.scenarios) == 3
    assert req.discount_rate == 0.05
    assert req.n_monte_carlo == 1000


def test_compute_lev_request_invalid_scenario():
    """잘못된 시나리오명 — ValidationError."""
    import pytest
    try:
        from pydantic import ValidationError
    except ImportError:
        return
    with pytest.raises(ValidationError):
        ComputeLEVRequest(
            stand_state={},
            scenarios=["불벌채"],  # invalid Literal
        )


def test_compute_lev_request_6_시나리오_허용():
    """D18 — 간벌+10년 포함 6개 시나리오."""
    req = ComputeLEVRequest(
        stand_state={},
        scenarios=["즉시", "5년", "10년", "연장KOC", "임산물", "간벌+10년"],
    )
    assert len(req.scenarios) == 6


# ──────────────────────────────────────────────
# [검증] DraftPlanCard
# ──────────────────────────────────────────────

def _base_card(**override):
    args = dict(
        recommended_scenario="연장KOC",
        npv_median=22_000_000,
        npv_q05=15_000_000, npv_q95=30_000_000,
        age_now=50, legal_min_age=40,
        npv_uplift_label="+700만원/ha",
        reasons=["즉시 대비 NPV 700만원/ha 증가"],
        next_actions=["산림조합 컨설팅"],
        user_preference="균형",
    )
    args.update(override)
    return DraftPlanCard(**args)


def test_draft_plan_card_기본():
    card = _base_card()
    assert card.recommended_scenario == "연장KOC"
    assert len(card.reasons) >= 1


def test_draft_plan_card_offset_citations():
    card = _base_card(offset_citations=[
        {"code": "FM-Rotation", "korean": "벌기령 연장 산림경영"},
    ])
    assert card.offset_citations[0]["code"] == "FM-Rotation"


def test_draft_plan_card_user_preference_literal():
    """user_preference Literal 검증."""
    import pytest
    try:
        from pydantic import ValidationError
    except ImportError:
        return
    with pytest.raises(ValidationError):
        _base_card(user_preference="공격형")  # invalid


# ──────────────────────────────────────────────
# [회귀] D9 fixture 출력 기준선
# ──────────────────────────────────────────────

def test_d9_reference_lev_per_ha():
    """D9 fixture: 보은 50년 즉시 LEV = 12,000,000 (회귀)."""
    r = _base_lev_result()
    assert r.lev_per_ha == 12_000_000


def test_d9_reference_uplift_label():
    """D9 card fixture: +700만원/ha."""
    card = _base_card()
    assert "700만원" in card.npv_uplift_label


def test_lev_result_data_sources_dict_type():
    """data_sources 는 Dict[str, str] — 출처 추적."""
    r = LEVResult(
        scenario="즉시", T_optimal=50,
        npv_per_ha=15e6, npv_q05=10e6, npv_q95=20e6, lev_per_ha=12e6,
        timber_revenue=18e6, carbon_revenue=0, total_cost=3e6,
        carbon_stock_T=85.5,
        grade_distribution_T={"1등급": 1.0},
        feasibility=True,
        data_sources={"timber_price": "KOFPI Q4 2025"},
    )
    assert isinstance(r.data_sources, dict)
    assert r.data_sources["timber_price"].startswith("KOFPI")


def test_lev_result_grade_dist_sum_1():
    """grade_distribution_T 합이 약 1.0."""
    r = _base_lev_result(grade_distribution_T={
        "특용재": 0.05, "1등급": 0.30, "2등급": 0.32,
        "3등급": 0.24, "원주재": 0.09, "원료재": 0.01,
    })
    total = sum(r.grade_distribution_T.values())
    assert abs(total - 1.0) < 0.05


if __name__ == "__main__":
    funcs = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    print(f"Running {len(funcs)} schema tests...")
    passed = 0
    for f in funcs:
        try:
            f()
            print(f"  ✅ {f.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {f.__name__}: {e}")
        except ImportError:
            print(f"  ⚠️  {f.__name__}: skip")
    print(f"\n{passed}/{len(funcs)} passed")
