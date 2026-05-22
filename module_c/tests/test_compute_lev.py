"""test_compute_lev.py — 진입점 + 6 시나리오 dispatch."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from module_c.src.compute_lev import compute_lev, compute_lev_with_plan  # noqa: E402
from module_c.src.demo_parcels import get_demo_parcel  # noqa: E402


# [검증] 6 시나리오 모두 반환
def test_six_scenarios_returned():
    stand = get_demo_parcel("boeun_pine_50y_2ha")
    r = compute_lev(stand, use_monte_carlo=False)
    assert "즉시" in r
    assert "간벌+10년" in r
    assert len(r) == 6


# [검증] 결정론 NPV 동일성 (seed 고정 불필요)
def test_deterministic_npv_reproducible():
    stand = get_demo_parcel("boeun_pine_50y_2ha")
    r1 = compute_lev(stand, use_monte_carlo=False)
    r2 = compute_lev(stand, use_monte_carlo=False)
    assert r1["즉시"]["npv"] == r2["즉시"]["npv"]


# [검증] feasibility 처리 — 30년 강원소나무 즉시
def test_30y_pine_immediate_infeasible():
    stand = get_demo_parcel("boeun_pine_30y_1.5ha")
    r = compute_lev(stand, scenarios=["즉시"], use_monte_carlo=False)
    assert not r["즉시"]["feasibility"]


# [검증] 30년 → 10년 연장 = 40년 = 법정 → feasible
def test_30y_pine_10yr_feasible():
    stand = get_demo_parcel("boeun_pine_30y_1.5ha")
    r = compute_lev(stand, scenarios=["10년"], use_monte_carlo=False)
    assert r["10년"]["feasibility"]


# [검증] Monte Carlo 변동성
def test_mc_has_quantiles():
    stand = get_demo_parcel("boeun_pine_50y_2ha")
    r = compute_lev(stand, scenarios=["즉시"], use_monte_carlo=True, n_samples=50)
    cell = r["즉시"]
    assert cell["npv_q05"] < cell["npv_median"] < cell["npv_q95"]


# [검증] compute_lev_with_plan 통합
def test_compute_lev_with_plan_returns_card():
    stand = get_demo_parcel("boeun_pine_50y_2ha")
    pkg = compute_lev_with_plan(stand, n_samples=50, use_monte_carlo=True)
    assert "results" in pkg
    assert "pareto" in pkg
    assert "draft_plan" in pkg
    assert pkg["draft_plan"]["recommended_scenario"]


# [회귀] 4 real polygon 모두 계산 가능
def test_real_polygons_all_compute():
    for pid in ["boeun_real_oedari_8197tco2", "jinan_real_waryongri_4671tco2"]:
        stand = get_demo_parcel(pid)
        r = compute_lev(stand, scenarios=["연장KOC"], use_monte_carlo=False)
        assert r["연장KOC"]["npv"] != 0


# [검증] 진안 낙엽송 (시도코드 45) demo 의 species - 이제 sample 에 없음, real 만 강원소나무
def test_jinan_real_polygon():
    stand = get_demo_parcel("jinan_real_waryongri_4671tco2")
    assert stand["species_dominant"] == "강원지방소나무"


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
