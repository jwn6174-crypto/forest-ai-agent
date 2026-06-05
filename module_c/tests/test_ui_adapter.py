"""test_ui_adapter.py — Module C ↔ ui Scenario[] 호환 (D127)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from module_c.src.ui_adapter import (
    to_ui_scenarios,
    to_ui_scenario,
    to_ui_recommendation,
    to_ui_offset_eligibility,
    _to_manwon,
    _SCENARIO_ID_MAP,
)


def _fake_package():
    return {
        "results": {
            "즉시": {
                "npv_median": 660_000_000, "npv_q05": 460_000_000,
                "npv_q95": 860_000_000, "feasibility": True, "T_optimal": 50,
                "T_horizon": 0, "timber_revenue": 800_000_000,
                "carbon_revenue": 0, "ntfp_revenue": 0,
                "cost_breakdown": {"harvest": 50_000_000, "regen": 30_000_000},
            },
            "연장KOC": {
                "npv_median": 750_000_000, "npv_q05": 550_000_000,
                "npv_q95": 950_000_000, "feasibility": True, "T_optimal": 60,
                "T_horizon": 10, "carbon_revenue": 50_000_000,
            },
            "간벌+10년": {
                "npv_median": 800_000_000, "npv_q05": 650_000_000,
                "npv_q95": 950_000_000, "feasibility": True, "T_optimal": 60,
                "T_horizon": 10,
            },
            "불가시나리오": {"npv_median": 0, "feasibility": False},
        },
        "draft_plan": {
            "recommended_scenario": "간벌+10년",
            "offset_citations": [{"code": "FM-Rotation", "korean": "벌기령 연장 산림경영"}],
            "next_actions": ["보은군산림조합 방문"],
        },
    }


# [검증] 단위 변환 (원 → 만원)
def test_to_manwon():
    assert _to_manwon(660_000_000) == 66000.0
    assert _to_manwon(None) == 0.0


# [검증] 시나리오 id 매핑 (한글 → 영문)
def test_id_mapping_complete():
    assert _SCENARIO_ID_MAP["즉시"] == "immediate"
    assert _SCENARIO_ID_MAP["연장KOC"] == "koc"
    assert _SCENARIO_ID_MAP["간벌+10년"] == "thinning"
    assert len(_SCENARIO_ID_MAP) == 6


# [검증] feasibility=False 제외
def test_infeasible_excluded():
    scenarios = to_ui_scenarios(_fake_package(), age_now=50)
    ids = [s["id"] for s in scenarios]
    assert len(scenarios) == 3  # 불가 1개 제외
    assert "불가시나리오" not in ids


# [검증] 간벌 → thinning
def test_thinning_id():
    scenarios = to_ui_scenarios(_fake_package(), age_now=50)
    thinning = [s for s in scenarios if s["id"] == "thinning"]
    assert thinning
    assert thinning[0]["recommended"]


# [검증] ui Scenario 필수 필드 모두 존재
def test_all_ui_fields_present():
    scenarios = to_ui_scenarios(_fake_package(), age_now=50)
    for s in scenarios:
        for field in ["id", "name", "description", "harvestYear", "npv",
                      "timberRevenue", "carbonRevenue", "harvestCost",
                      "regenCost", "ntfpRevenue", "kocEligible", "paretoX",
                      "recommended"]:
            assert field in s, f"누락: {field}"
        for npv_field in ["p5", "p50", "p95", "bankruptcyProb"]:
            assert npv_field in s["npv"], f"npv 누락: {npv_field}"


# [검증] paretoX 유동성 (즉시=1.0)
def test_pareto_x_immediate():
    scenarios = to_ui_scenarios(_fake_package(), age_now=50)
    immediate = [s for s in scenarios if s["id"] == "immediate"][0]
    assert immediate["paretoX"] == 1.0


def test_pareto_x_koc_lower():
    scenarios = to_ui_scenarios(_fake_package(), age_now=50)
    koc = [s for s in scenarios if s["id"] == "koc"][0]
    assert koc["paretoX"] < 1.0  # 10년 유예 → 유동성 낮음


# [검증] KOC 적격
def test_koc_eligible():
    scenarios = to_ui_scenarios(_fake_package(), age_now=50)
    koc = [s for s in scenarios if s["id"] == "koc"][0]
    assert koc["kocEligible"]
    assert koc["kocMethodology"]


# [검증] harvestYear (연장KOC=None)
def test_harvest_year_koc_none():
    scenarios = to_ui_scenarios(_fake_package(), age_now=50)
    koc = [s for s in scenarios if s["id"] == "koc"][0]
    assert koc["harvestYear"] is None


def test_harvest_year_immediate_zero():
    scenarios = to_ui_scenarios(_fake_package(), age_now=50)
    immediate = [s for s in scenarios if s["id"] == "immediate"][0]
    assert immediate["harvestYear"] == 0


# [검증] cost 분해
def test_cost_breakdown_split():
    scenarios = to_ui_scenarios(_fake_package(), age_now=50)
    immediate = [s for s in scenarios if s["id"] == "immediate"][0]
    # harvest = harvest+skidding+transport+loading = 50M → 5000만원
    assert immediate["harvestCost"] == 5000.0
    assert immediate["regenCost"] == 3000.0


# [검증] recommendation
def test_recommendation():
    assert to_ui_recommendation(_fake_package()) == "thinning"


# [검증] offsetEligibility
def test_offset_eligibility():
    offset = to_ui_offset_eligibility(_fake_package())
    assert offset["eligible"]
    assert "벌기령 연장 산림경영" in offset["matchedTypes"]
    assert len(offset["nextSteps"]) > 0


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
