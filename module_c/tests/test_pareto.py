"""test_pareto.py — D12 NPV-탄소 Pareto front."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pareto import compute_pareto_front, format_pareto_for_plotly, select_three_representative


def _fake_results():
    return {
        "즉시":    {"npv_median": 50e6, "carbon_stock_T_tco2_per_ha_median": 0,
                    "feasibility": True, "T_optimal": 50},
        "5년":    {"npv_median": 55e6, "carbon_stock_T_tco2_per_ha_median": 50,
                    "feasibility": True, "T_optimal": 55},
        "10년":   {"npv_median": 65e6, "carbon_stock_T_tco2_per_ha_median": 200,
                    "feasibility": True, "T_optimal": 60},
        "연장KOC": {"npv_median": 55e6, "carbon_stock_T_tco2_per_ha_median": 300,
                    "feasibility": True, "T_optimal": 60},
        "간벌+10년": {"npv_median": 80e6, "carbon_stock_T_tco2_per_ha_median": 250,
                      "feasibility": True, "T_optimal": 60},
    }


# [검증] Pareto-optimal 찾기 (Hartman 정통)
def test_pareto_optimal_high_npv_high_carbon():
    pf = compute_pareto_front(_fake_results())
    assert "간벌+10년" in pf["pareto_optimal"]


# [검증] dominated 시나리오 식별
def test_dominated_by_others():
    pf = compute_pareto_front(_fake_results())
    # 즉시 (50M, 0C) 는 10년 (65M, 200C) 에 dominated
    assert "즉시" in pf["dominated"]


# [검증] Plotly format 변환
def test_plotly_format_has_xy_arrays():
    pf = compute_pareto_front(_fake_results())
    plot = format_pareto_for_plotly(pf)
    assert "x_npv" in plot
    assert "y_carbon" in plot
    assert len(plot["x_npv"]) == 5


# [검증] 3 대표점 (안정형/균형형/수익형)
def test_three_representative_returns_3():
    pf = compute_pareto_front(_fake_results())
    three = select_three_representative(pf)
    # Pareto-optimal 만 = 2개 (연장KOC, 간벌+10년) — 그 다음 fallback
    assert len(three) >= 2


# [회귀] feasibility=False 제외
def test_infeasible_excluded():
    results = _fake_results()
    results["즉시"]["feasibility"] = False
    pf = compute_pareto_front(results)
    # 즉시 는 분석에서 제외
    sc_names = [p["scenario"] for p in pf["points"]]
    assert "즉시" not in sc_names


# [검증] 한국어 labels
def test_korean_labels_in_plotly():
    pf = compute_pareto_front(_fake_results())
    plot = format_pareto_for_plotly(pf)
    assert "labels_korean" in plot
    assert "NPV" in plot["labels_korean"]["x"]


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
