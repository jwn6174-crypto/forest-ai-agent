"""test_recommend.py — Sharpe-like + user preference."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from recommend import recommend_scenario, get_recommendation_reasons, get_next_actions


def _fake():
    return {
        "즉시":   {"npv": 50e6, "npv_q05": 40e6, "npv_q95": 60e6,
                  "feasibility": True, "T_optimal": 50, "carbon_revenue": 0},
        "10년":  {"npv": 65e6, "npv_q05": 50e6, "npv_q95": 80e6,
                  "feasibility": True, "T_optimal": 60, "carbon_revenue": 0},
        "연장KOC": {"npv": 75e6, "npv_q05": 55e6, "npv_q95": 95e6,
                   "feasibility": True, "T_optimal": 60, "carbon_revenue": 5e6},
        "간벌+10년": {"npv": 80e6, "npv_q05": 65e6, "npv_q95": 95e6,
                     "feasibility": True, "T_optimal": 60, "subsidy_revenue": 4.4e6},
    }


# [검증] 수익극대화 → median 최대
def test_max_profit_picks_highest_median():
    r = recommend_scenario(_fake(), "수익극대화")
    assert r == "간벌+10년"


# [검증] 위험회피 → q05 최대
def test_risk_averse_picks_highest_q05():
    r = recommend_scenario(_fake(), "위험회피")
    assert r == "간벌+10년"


# [검증] 균형 — Sharpe-like
def test_balanced_returns_non_none():
    r = recommend_scenario(_fake(), "균형")
    assert r is not None


# [검증] reasons 비어있지 않음
def test_reasons_not_empty():
    r = get_recommendation_reasons("간벌+10년", _fake(), "균형",
                                    age_now=50, legal_min_age=40)
    assert len(r) >= 2


# [검증] next_actions 에 전화번호·URL (D20)
def test_next_actions_has_phone_url():
    acts = get_next_actions("간벌+10년", region="충북 보은")
    text = " ".join(acts)
    assert "산림조합" in text and "FGIS" in text


def test_next_actions_yeonjang_koc_has_carbon_center():
    acts = get_next_actions("연장KOC")
    text = " ".join(acts)
    assert "탄소" in text or "koreaforestcarbon" in text


# [회귀] 모든 시나리오 feasible=False 시 None
def test_all_infeasible_returns_none():
    results = _fake()
    for k in results:
        results[k]["feasibility"] = False
    assert recommend_scenario(results, "균형") is None


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
