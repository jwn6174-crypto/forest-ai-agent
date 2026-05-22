"""test_lev_core.py — Faustmann-Hartman 본체 검증."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from module_c.src.lev_core import compute_lev_single


def _base(**override):
    """D-fixture: 보은 50년 강원소나무 — 벌기령 도달."""
    stand = {
        "species_dominant": "강원지방소나무", "age_estimate": 50, "site_index": 15,
        "area_ha": 2.0, "distance_to_road_km": 1.5, "skidding_distance_m": 500,
        "slope_class": "중",
    }
    args = dict(stand=stand, scenario="즉시", T=50, discount_rate=0.05)
    args.update(override)
    return compute_lev_single(**args)


# [검증] Faustmann LEV 식 항등성
def test_npv_immediate_equals_lev():
    """T_horizon=0 시 LEV = NPV"""
    r = _base()
    assert r["lev"] == r["npv"]


def test_npv_positive_for_mature_stand():
    """벌기령 도달 임지의 즉시벌채 NPV > 0"""
    r = _base()
    assert r["npv"] > 0


# [검증] 6 시나리오 분기
def test_jeungji_scenario():
    r = _base(scenario="즉시", T=50)
    assert r["scenario"] == "즉시"
    assert r["T_optimal"] == 50


def test_thinning_scenario_has_subsidy():
    """간벌+10년 시나리오는 보조 매출 있음"""
    r = _base(scenario="간벌+10년", T=60)
    assert r["subsidy_revenue"] > 0


# [검증] HWP loss 음수
def test_hwp_loss_negative():
    r = _base()
    assert r["hwp_loss_npv"] < 0


# [검증] 기후 시나리오 적용
def test_ssp585_reduces_volume_and_npv():
    base = _base(scenario="즉시", T=50, climate_scenario="baseline")
    ssp = _base(scenario="즉시", T=50, climate_scenario="SSP585")
    assert ssp["npv"] < base["npv"]
    assert ssp["climate_multiplier_applied"] < base["climate_multiplier_applied"]


# [검증] 등급분포 합 = 1.0
def test_grade_dist_sums_to_one():
    r = _base()
    total = sum(r["grade_distribution_T"].values())
    assert abs(total - 1.0) < 0.05


# [검증] data_sources 자동 출력
def test_data_sources_populated():
    r = _base()
    assert "timber_price" in r["data_sources"]
    assert "carbon_uptake" in r["data_sources"]
    assert "hwp_decay" in r["data_sources"]


# [회귀] cost 양수
def test_total_cost_positive():
    r = _base()
    assert r["total_cost"] > 0


# [검증] 면적 비례
def test_npv_scales_with_area():
    r1 = _base(stand={"species_dominant": "강원지방소나무", "age_estimate": 50,
                       "site_index": 15, "area_ha": 1.0, "distance_to_road_km": 1.5})
    r2 = _base(stand={"species_dominant": "강원지방소나무", "age_estimate": 50,
                       "site_index": 15, "area_ha": 2.0, "distance_to_road_km": 1.5})
    # 2배 면적 → 2배 근사 (선형 가정)
    assert 1.5 < r2["npv"] / max(r1["npv"], 1) < 2.5


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
