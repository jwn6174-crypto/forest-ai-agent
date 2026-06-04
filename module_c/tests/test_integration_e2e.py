"""test_integration_e2e.py — A·B·C·D·ui 전체 파이프라인 통합 (D127).

정우 api_server.py 가 실제로 수행하는 흐름을 그대로 검증한다:
    forest_state(Module A·B) → stand_adapter → compute_lev_with_plan(C)
    → ui_adapter → ui Scenario[]

이 테스트는 정우 module_bd 의 임분수확표(parquet)를 필요로 하므로,
team_repo 전체가 있는 환경에서만 실행된다(없으면 skip).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

# 정우 module_bd 가 없으면 전체 모듈 skip
pytest.importorskip("module_bd.src.growth_predict")

from module_c.src import stand_adapter, ui_adapter  # noqa: E402
from module_c.src.compute_lev import compute_lev_with_plan  # noqa: E402


def _forest_state():
    """api_server.py 가 Module A·B 로 만드는 forest_state 모사."""
    return {
        "pnu": "4374533021100010000",
        "species": "강원지방소나무",
        "estimatedAge": 50,
        "areaHa": 2.0,
        "volumePerHa": 281.0,
        "volumeUncertainty": 42.0,
        "carbonPerHa": 132.0,
        "siteIndex": 15,
        "dataWarning": None,
    }


def test_e2e_forest_state_to_ui_scenarios():
    """전체 파이프라인 — forest_state → ui Scenario[]."""
    stand = stand_adapter.from_forest_state(_forest_state())
    package = compute_lev_with_plan(stand, use_monte_carlo=False)
    scenarios = ui_adapter.to_ui_scenarios(package, age_now=50)

    # 6 시나리오 모두 변환 (벌기령 도달 임지)
    assert len(scenarios) == 6
    ids = {s["id"] for s in scenarios}
    assert ids == {"immediate", "five_year", "ten_year", "koc", "ntfp", "thinning"}


def test_e2e_recommendation_not_null():
    stand = stand_adapter.from_forest_state(_forest_state())
    package = compute_lev_with_plan(stand, use_monte_carlo=False)
    rec = ui_adapter.to_ui_recommendation(package)
    assert rec is not None
    assert rec in {"immediate", "five_year", "ten_year", "koc", "ntfp", "thinning"}


def test_e2e_confidence_note_none_no_crash():
    """D127 회귀 — dataWarning=None 이어도 전체 파이프라인 동작."""
    fs = {**_forest_state(), "dataWarning": None}
    stand = stand_adapter.from_forest_state(fs)
    assert stand["confidence_note"] is None
    package = compute_lev_with_plan(stand, use_monte_carlo=False)
    scenarios = ui_adapter.to_ui_scenarios(package, age_now=50)
    assert len(scenarios) > 0


def test_e2e_module_a_satellite_path():
    """Module A StandStateEstimate → 전체 파이프라인."""
    module_a_output = {
        "pnu": "4374533021100010000",
        "geom_wkt": "POLYGON((127.73 36.58, 127.74 36.58, 127.74 36.59, 127.73 36.59, 127.73 36.58))",
        "area_ha": 25.6,
        "species_dominant": "신갈",  # Module A 키 → 신갈나무 매핑
        "age_estimate": 45,
        "volume_m3_per_ha": 215.0,
        "volume_q05": 148.0,
        "volume_q95": 285.0,
        "carbon_tc_per_ha": 96.0,
        "saturation_warning": False,
        "confidence_level": "high",
        "confidence_note": "유효 픽셀 1,240개",
    }
    stand = stand_adapter.from_module_a(module_a_output, site_index=12)
    assert stand["species_dominant"] == "신갈나무"
    # 신갈나무는 활엽수 — 임분수확표에 있어야 동작
    package = compute_lev_with_plan(stand, use_monte_carlo=False)
    scenarios = ui_adapter.to_ui_scenarios(package, age_now=45)
    assert len(scenarios) >= 1


def test_e2e_ui_scenario_all_fields_valid():
    """ui Scenario 의 모든 필드가 올바른 타입으로 채워지는지."""
    stand = stand_adapter.from_forest_state(_forest_state())
    package = compute_lev_with_plan(stand, use_monte_carlo=False)
    scenarios = ui_adapter.to_ui_scenarios(package, age_now=50)
    for s in scenarios:
        assert isinstance(s["id"], str)
        assert isinstance(s["npv"]["p50"], (int, float))
        assert isinstance(s["npv"]["bankruptcyProb"], (int, float))
        assert isinstance(s["kocEligible"], bool)
        assert isinstance(s["recommended"], bool)
        assert 0.0 <= s["paretoX"] <= 1.0


if __name__ == "__main__":
    funcs = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    passed = 0
    for f in funcs:
        try:
            f()
            print(f"  ✅ {f.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {f.__name__}: {type(e).__name__}: {str(e)[:60]}")
    print(f"\n{passed}/{len(funcs)} passed")
