"""test_draft_plan.py — DraftPlanCard 이중 표현 (경제학자 권고)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from module_c.src.draft_plan import create_draft_plan


def _stand():
    return {
        "species_dominant": "강원지방소나무", "age_estimate": 50, "site_index": 15,
        "area_ha": 2.0, "distance_to_road_km": 1.5, "confidence_level": "low",
    }


def _results():
    return {
        "즉시":   {"npv_median": 50e6, "npv_q05": 40e6, "npv_q95": 60e6,
                  "feasibility": True, "T_optimal": 50,
                  "carbon_revenue_median": 0, "carbon_stock_T_tco2_per_ha_median": 0},
        "10년":  {"npv_median": 65e6, "npv_q05": 50e6, "npv_q95": 80e6,
                  "feasibility": True, "T_optimal": 60,
                  "carbon_revenue_median": 0, "carbon_stock_T_tco2_per_ha_median": 200},
        "간벌+10년": {"npv_median": 80e6, "npv_q05": 65e6, "npv_q95": 95e6,
                     "feasibility": True, "T_optimal": 60,
                     "carbon_revenue_median": 0, "subsidy_revenue_median": 4.4e6,
                     "carbon_stock_T_tco2_per_ha_median": 250},
    }


# [검증] 산주 UI — 단순표시 + worst case (이중 표현)
def test_simple_npv_and_worst_case():
    card = create_draft_plan(_stand(), _results(), legal_min_age=40)
    assert card["npv_단순표시"] is not None
    assert card["npv_worst_case_10pct"] is not None


# [검증] uplift label
def test_uplift_label_has_won():
    card = create_draft_plan(_stand(), _results(), legal_min_age=40)
    assert "만원" in card["npv_uplift_label"] or "-" == card["npv_uplift_label"]


# [검증] uncertainty tier
def test_uncertainty_tier_present():
    card = create_draft_plan(_stand(), _results(), legal_min_age=40)
    assert card["uncertainty_tier"] in {"high", "med", "low"}


# [검증] 8 사업유형 매칭
def test_offset_citations_at_least_one():
    card = create_draft_plan(_stand(), _results(), legal_min_age=40)
    # 50년 강원소나무 → FM-Rotation 적격
    assert len(card["offset_citations"]) >= 1


# [검증] full_distribution 정책 부록
def test_full_distribution_for_policy():
    card = create_draft_plan(_stand(), _results(), legal_min_age=40)
    assert "npv_q05" in card["full_distribution"]
    assert "npv_q95" in card["full_distribution"]


# [검증] reasons 비어있지 않음
def test_reasons_at_least_one():
    card = create_draft_plan(_stand(), _results(), legal_min_age=40)
    assert len(card["reasons"]) >= 1


# [회귀] user_preference 적용
def test_preference_risk_averse():
    card = create_draft_plan(_stand(), _results(),
                              user_preference="위험회피", legal_min_age=40)
    assert card["user_preference"] == "위험회피"


# [회귀] D127 통합 — confidence_note=None 이어도 죽지 않음
def test_confidence_note_none_safe():
    """from_forest_state 가 dataWarning=None → confidence_note=None 을 넘겨도
    draft_plan 의 .startswith 호출이 안전해야 한다 (통합 검증에서 발견된 버그)."""
    stand = {**_stand(), "confidence_note": None}
    card = create_draft_plan(stand, _results(), legal_min_age=40)
    assert card["recommended_scenario"]  # 정상 생성


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
