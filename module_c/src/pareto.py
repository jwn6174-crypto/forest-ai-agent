"""
pareto.py — Pareto front (NPV vs 누적 탄소격리).

D12 (산림경제학자): Hartman (1976) 정통 — NPV-탄소 단일 2축.
Risk 는 보조 error bar.

희도 D12 결정 — 2026-05-20 Day 6 작성
"""

from typing import Dict, List


def compute_pareto_front(
    lev_results: Dict[str, Dict],
) -> Dict[str, any]:
    """
    시나리오별 (NPV, 누적탄소) 점들의 Pareto front 산출.

    Parameters
    ----------
    lev_results : dict
        {scenario_name: LEVResult dict (Monte Carlo 결과)}

    Returns
    -------
    dict
        {
            "points": [
                {"scenario": str, "npv": float, "carbon_stock_T": float, ...},
                ...
            ],
            "pareto_optimal": List[str],  # Pareto frontier 위 시나리오명 list
            "dominated": List[str],
        }

    Examples
    --------
    >>> results = {
    ...     "즉시": {"npv_median": 50e6, "carbon_stock_T_tco2_per_ha_median": 0},
    ...     "10년": {"npv_median": 65e6, "carbon_stock_T_tco2_per_ha_median": 200},
    ...     "연장KOC": {"npv_median": 55e6, "carbon_stock_T_tco2_per_ha_median": 300},
    ... }
    >>> pf = compute_pareto_front(results)
    >>> "10년" in pf["pareto_optimal"]
    True
    """
    points = []
    for scenario, r in lev_results.items():
        if not r.get("feasibility", True):
            continue
        carbon = r.get("carbon_stock_T_tco2_per_ha_median", r.get("carbon_stock_T_tco2_per_ha", 0))
        npv = r.get("npv_median", r.get("npv", 0))
        points.append(
            {
                "scenario": scenario,
                "npv": npv,
                "carbon_stock_T": carbon,
                "npv_q05": r.get("npv_q05", npv),
                "npv_q95": r.get("npv_q95", npv),
                "T_optimal": r.get("T_optimal"),
                "lev": r.get("lev_median", r.get("lev", 0)),
            }
        )

    # Pareto frontier: NPV ↑ + carbon ↑ 둘 다 dominate 안 되는 점
    pareto_optimal = []
    dominated = []
    for i, p in enumerate(points):
        is_dominated = False
        for j, q in enumerate(points):
            if i == j:
                continue
            if q["npv"] >= p["npv"] and q["carbon_stock_T"] >= p["carbon_stock_T"]:
                if q["npv"] > p["npv"] or q["carbon_stock_T"] > p["carbon_stock_T"]:
                    is_dominated = True
                    break
        if is_dominated:
            dominated.append(p["scenario"])
        else:
            pareto_optimal.append(p["scenario"])

    return {
        "points": points,
        "pareto_optimal": pareto_optimal,
        "dominated": dominated,
        "n_scenarios": len(points),
    }


def format_pareto_for_plotly(pareto: Dict) -> Dict:
    """
    Plotly scatter trace 용 데이터 변환.

    수범 module_e 가 st.plotly_chart() 로 사용.
    """
    points = pareto["points"]
    return {
        "x_npv": [p["npv"] / 1e6 for p in points],  # 백만원 단위
        "y_carbon": [p["carbon_stock_T"] for p in points],
        "labels": [p["scenario"] for p in points],
        "error_x_q05": [(p["npv"] - p["npv_q05"]) / 1e6 for p in points],
        "error_x_q95": [(p["npv_q95"] - p["npv"]) / 1e6 for p in points],
        "is_pareto": [p["scenario"] in pareto["pareto_optimal"] for p in points],
        "labels_korean": {
            "x": "NPV (백만원/ha)",
            "y": "T시점 탄소 stock (tCO₂/ha)",
            "title": "5+1 시나리오 Pareto Front (NPV vs 탄소격리)",
            "note": "Pareto-optimal (파레토 우위) 점들이 산주의 trade-off 선택지.",
        },
    }


def select_three_representative(pareto: Dict) -> List[Dict]:
    """
    AI 엔지니어 권고 (D12): 산주에게는 Pareto front 전체 대신 3 대표점.

    "안정형 / 균형형 / 수익형" 라벨.
    """
    pareto_pts = [p for p in pareto["points"] if p["scenario"] in pareto["pareto_optimal"]]

    if not pareto_pts:
        pareto_pts = pareto["points"]

    if len(pareto_pts) <= 3:
        labels = ["안정형", "균형형", "수익형"][: len(pareto_pts)]
        sorted_pts = sorted(pareto_pts, key=lambda p: p["npv"])
        return [{**p, "_label": labels[i]} for i, p in enumerate(sorted_pts)]

    # 3+ 시나리오: 최저 NPV / 중간 / 최고 NPV
    sorted_pts = sorted(pareto_pts, key=lambda p: p["npv"])
    return [
        {**sorted_pts[0], "_label": "안정형 (탄소 우위)"},
        {**sorted_pts[len(sorted_pts) // 2], "_label": "균형형"},
        {**sorted_pts[-1], "_label": "수익형 (NPV 우위)"},
    ]


if __name__ == "__main__":
    print("=" * 60)
    print("pareto.py 자가 검증")
    print("=" * 60)

    fake = {
        "즉시": {
            "npv_median": 50_000_000,
            "carbon_stock_T_tco2_per_ha_median": 0,
            "feasibility": True,
            "T_optimal": 50,
        },
        "5년": {
            "npv_median": 55_000_000,
            "carbon_stock_T_tco2_per_ha_median": 50,
            "feasibility": True,
            "T_optimal": 55,
        },
        "10년": {
            "npv_median": 65_000_000,
            "carbon_stock_T_tco2_per_ha_median": 200,
            "feasibility": True,
            "T_optimal": 60,
        },
        "연장KOC": {
            "npv_median": 55_000_000,
            "carbon_stock_T_tco2_per_ha_median": 300,
            "feasibility": True,
            "T_optimal": 60,
        },
        "임산물": {
            "npv_median": 60_000_000,
            "carbon_stock_T_tco2_per_ha_median": 250,
            "feasibility": True,
            "T_optimal": 65,
        },
        "간벌+10년": {
            "npv_median": 80_000_000,
            "carbon_stock_T_tco2_per_ha_median": 250,
            "feasibility": True,
            "T_optimal": 60,
        },
    }

    pf = compute_pareto_front(fake)
    print(f"\n[검증 1] Pareto-optimal: {pf['pareto_optimal']}")
    print(f"  Dominated: {pf['dominated']}")
    # 간벌+10년 (NPV 80M + carbon 250) 는 Pareto-optimal
    assert "간벌+10년" in pf["pareto_optimal"]
    # 즉시 (NPV 50, carbon 0) 는 dominated (10년 65, 200 에 의해)
    assert "즉시" in pf["dominated"]

    print("\n[검증 2] Plotly format")
    plot_data = format_pareto_for_plotly(pf)
    print(f"  x range: {min(plot_data['x_npv']):.1f} ~ {max(plot_data['x_npv']):.1f}")
    print(f"  y range: {min(plot_data['y_carbon'])} ~ {max(plot_data['y_carbon'])}")
    assert len(plot_data["labels"]) == 6

    print("\n[검증 3] 3 대표점")
    three = select_three_representative(pf)
    for p in three:
        print(
            f"  {p['_label']}: {p['scenario']} NPV {p['npv'] / 1e6:.1f}M, C {p['carbon_stock_T']}"
        )
    assert len(three) == 3

    print("\n" + "=" * 60)
    print("✅ pareto.py 3/3 검증 통과")
    print("=" * 60)
