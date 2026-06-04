"""test_stand_adapter.py — Module A ↔ Module C 호환 (D127)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from module_c.src.stand_adapter import (
    from_module_a,
    from_forest_state,
    _to_bd_species,
    _pnu_to_sigun,
    _slope_to_class,
    get_satellite_uncertainty_note,
)


def _fake_module_a(**override):
    base = {
        "pnu": "4374533021100010000",
        "geom_wkt": "POLYGON((127.73 36.58, 127.74 36.58, 127.74 36.59, 127.73 36.59, 127.73 36.58))",
        "area_ha": 25.6,
        "species_dominant": "신갈",
        "age_estimate": 45,
        "agb_mg_per_ha": 142.0,
        "agb_q05": 98.0,
        "agb_q95": 188.0,
        "volume_m3_per_ha": 215.0,
        "volume_q05": 148.0,
        "volume_q95": 285.0,
        "carbon_tc_per_ha": 96.0,
        "saturation_warning": False,
        "confidence_level": "high",
        "confidence_note": "유효 픽셀 1,240개",
    }
    base.update(override)
    return base


# [검증] 수종 역매핑 (Module A 키 → 정우 B/D 정식명)
def test_species_mapping_pine():
    assert _to_bd_species("강원소나무") == "강원지방소나무"
    assert _to_bd_species("중부소나무") == "중부지방소나무"
    assert _to_bd_species("리기다") == "리기다소나무"


def test_species_mapping_oak():
    assert _to_bd_species("신갈") == "신갈나무"
    assert _to_bd_species("굴참") == "굴참나무"
    assert _to_bd_species("기본활엽") == "참나무류"


def test_species_mapping_unknown_passthrough():
    # 매핑 테이블에 없으면 그대로 통과
    assert _to_bd_species("강원지방소나무") == "강원지방소나무"


# [검증] PNU → 시군 추출
def test_pnu_to_sigun_boeun():
    assert _pnu_to_sigun("4374533021100010000") == "보은"


def test_pnu_to_sigun_fallback():
    assert _pnu_to_sigun(None) == "보은"
    assert _pnu_to_sigun("99999") == "보은"


# [검증] 경사도 → 표준품셈 등급
def test_slope_class():
    assert _slope_to_class(10) == "완"
    assert _slope_to_class(20) == "중"
    assert _slope_to_class(30) == "급"
    assert _slope_to_class(None) == "중"


# [검증] Module A → Module C stand dict (핵심)
def test_from_module_a_core_keys():
    stand = from_module_a(_fake_module_a(), site_index=14)
    # Module C 가 읽는 핵심 키 모두 존재
    for key in ["species_dominant", "age_estimate", "area_ha",
                "volume_m3_per_ha", "volume_q05", "volume_q95",
                "carbon_tc_per_ha", "confidence_level", "site_index",
                "distance_to_road_km", "sigun", "slope_class", "ownership"]:
        assert key in stand, f"누락 키: {key}"


def test_from_module_a_satellite_variance_preserved():
    # Module A 의 실 위성 분산이 그대로 전달 (mock ±20% 아님)
    stand = from_module_a(_fake_module_a())
    assert stand["volume_q05"] == 148.0
    assert stand["volume_q95"] == 285.0


def test_from_module_a_species_normalized():
    stand = from_module_a(_fake_module_a(species_dominant="신갈"))
    assert stand["species_dominant"] == "신갈나무"


def test_from_module_a_pydantic_object():
    # Pydantic 객체도 처리 (model_dump)
    class FakePydantic:
        def model_dump(self):
            return _fake_module_a()
    stand = from_module_a(FakePydantic())
    assert stand["species_dominant"] == "신갈나무"


# [검증] D126 — saturation 경고 → 산주 문장
def test_saturation_warning_note():
    stand = from_module_a(_fake_module_a(saturation_warning=True))
    note = get_satellite_uncertainty_note(stand)
    assert note is not None
    assert "GEDI" in note and "R²=-0.187" in note


def test_no_warning_returns_none():
    stand = from_module_a(_fake_module_a(saturation_warning=False, confidence_level="high"))
    assert get_satellite_uncertainty_note(stand) is None


# [검증] forest_state(camelCase) → stand dict
def test_from_forest_state():
    fs = {
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
    stand = from_forest_state(fs)
    assert stand["species_dominant"] == "강원지방소나무"
    assert stand["site_index"] == 15
    assert stand["volume_q05"] < 281.0 < stand["volume_q95"]


# [회귀] 통합 — Module A → adapter → compute_lev_single 동작
def test_integration_module_a_to_compute_lev():
    from module_c.src.lev_core import compute_lev_single
    stand = from_module_a(_fake_module_a(), site_index=14)
    result = compute_lev_single(stand, "즉시", T=45)
    assert "npv" in result
    assert result["npv"] != 0


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
        except Exception as e:
            print(f"  ⚠️  {f.__name__}: {type(e).__name__}: {str(e)[:50]}")
    print(f"\n{passed}/{len(funcs)} passed")
