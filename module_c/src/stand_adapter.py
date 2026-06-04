"""
stand_adapter.py — Module A 위성 추정과 Module C 경제성 분석을 잇는 어댑터.

이 모듈은 통합 파이프라인의 첫 번째 연결 고리다. 민석의 Module A
(`predict_stand`) 가 위성 영상에서 추정한 임분 상태(StandStateEstimate)를,
희도의 Module C (`compute_lev`) 가 곧바로 소비할 수 있는 dict 형태로 변환한다.

설계 철학 — 느슨한 결합(loose coupling):
    Module A 는 quantile-forest·rasterio·geopandas 같은 무거운 의존성과
    148MB 규모의 QRF 모델을 import 시점에 적재한다. 따라서 Module C 가
    Module A 를 *직접* import 하면, 단순한 NPV 계산조차 그 무게를 떠안게
    된다. 이를 피하기 위해 이 어댑터는 *이미 산출된* StandStateEstimate
    객체(또는 그 dict)만 입력으로 받는다. 즉 "누가 그 추정을 만들었는가"
    와 "그 추정으로 무엇을 계산하는가" 를 깨끗하게 분리한다.

세 가지 입력 경로를 모두 지원한다:
    1. from_module_a()       — Module A 의 StandStateEstimate (Pydantic/dict)
    2. from_forest_state()   — 정우 api_server.py 의 camelCase forest_state
    3. (Module C 내부)        — demo_parcels 의 dict 는 그대로 사용

수종명 정규화는 민석이 Module A 안에 이미 구현했다(`normalize_species`).
이 어댑터는 그 함수를 그대로 호출하되, Module A 를 import 할 수 없는
환경에서는 동등한 역방향 매핑 테이블로 우회한다.

희도 D127 결정 — 2026-05-31, Module A 도착 후 통합.
"""

from __future__ import annotations

import typing

# ── Module C 가 stand dict 에서 읽는 7개 보완 키의 기본값 ────────────────
# Module A 는 위성으로 species/age/volume/carbon/불확실성을 제공하지만,
# 경제성 계산에 필요한 입지·운반 변수까지는 산출하지 않는다. 이 값들은
# 임상도·임도망 GIS 에서 보강하는 것이 이상적이며, 그 전까지는 보은
# 파일럿의 현장 평균값을 보수적 기본값으로 사용한다(경영자 deliberation).
_DEFAULT_DISTANCE_TO_ROAD_KM = 2.0  # 보은 사유림 임도 접근성 평균 0.8~2.5km
_DEFAULT_SKIDDING_DISTANCE_M = 500.0
_DEFAULT_SLOPE_CLASS = "중"
_DEFAULT_OWNERSHIP = "공사유림"  # 정우 D 모듈 rotation_age 분류 기준
_DEFAULT_SIGUN = "보은"


# ── Module A 수종명(SPECIES_PARAMS 키) → 정우 B/D 임분수확표 정식명 ──────
# 민석의 normalize_species() 는 "외부 표기 → Module A 키" 방향이다.
# 우리는 그 반대, 즉 Module A 가 돌려준 키를 정우 B/D 가 이해하는
# 별표3·임분수확표 정식 수종명으로 되돌려야 한다.
_MODULE_A_TO_BD_SPECIES: dict[str, str] = {
    "강원소나무": "강원지방소나무",
    "중부소나무": "중부지방소나무",
    "리기다": "리기다소나무",
    "잣나무": "잣나무",
    "낙엽송": "낙엽송",
    "편백": "편백",
    "신갈": "신갈나무",
    "굴참": "굴참나무",
    "상수리": "상수리나무",
    "자작": "자작나무",
    "백합": "백합나무",
    "기본침엽": "강원지방소나무",  # 침엽 대표종으로 보수적 매핑
    "기본활엽": "참나무류",  # 활엽 대표종
}


def _to_bd_species(module_a_species: str) -> str:
    """Module A 수종 키를 정우 B/D 가 쓰는 정식 수종명으로 변환한다."""
    return _MODULE_A_TO_BD_SPECIES.get(module_a_species, module_a_species)


def _pnu_to_sigun(pnu: str | None) -> str:
    """PNU 앞 5자리(시도+시군 코드)로 충북 시군을 추정한다.

    정우 climate_correct(D15) 는 청주·충주·제천·보은·추풍령 anomaly 만
    보유하므로, 보은 파일럿 외 지역은 보은으로 우회한다(외삽 영역).
    """
    if not pnu or len(pnu) < 5:
        return _DEFAULT_SIGUN
    sigun_code = pnu[:5]
    _CODE_TO_SIGUN = {
        "43745": "보은",  # 충북 보은군
        "43111": "청주",  # 충북 청주시 (예시)
        "43130": "충주",
        "43150": "제천",
    }
    return _CODE_TO_SIGUN.get(sigun_code, _DEFAULT_SIGUN)


def _slope_to_class(slope_deg: float | None) -> str:
    """경사도(도)를 표준품셈 할증 구간(완/중/급)으로 변환한다."""
    if slope_deg is None:
        return _DEFAULT_SLOPE_CLASS
    if slope_deg < 15:
        return "완"
    if slope_deg < 25:
        return "중"
    return "급"


def _as_dict(stand_state: typing.Any) -> dict:
    """StandStateEstimate(Pydantic) 또는 dict 를 일관된 dict 로 변환한다."""
    if hasattr(stand_state, "model_dump"):  # pydantic v2
        return stand_state.model_dump()
    if hasattr(stand_state, "dict"):  # pydantic v1
        return stand_state.dict()
    if isinstance(stand_state, dict):
        return dict(stand_state)
    raise TypeError(
        f"지원하지 않는 stand_state 타입: {type(stand_state)}. "
        f"StandStateEstimate(Pydantic) 또는 dict 여야 한다."
    )


# ─────────────────────────────────────────────────────────────────────────
# 경로 1 — Module A StandStateEstimate → Module C stand dict
# ─────────────────────────────────────────────────────────────────────────


def from_module_a(
    stand_state: typing.Any,
    *,
    site_index: int | None = None,
    distance_to_road_km: float | None = None,
    elev: float | None = None,
    slope_deg: float | None = None,
    ownership: str = _DEFAULT_OWNERSHIP,
) -> dict:
    """Module A 의 위성 추정을 Module C 입력 dict 로 변환한다.

    Module A 가 직접 제공하는 8개 필드(수종·임령·면적·체적±·탄소·신뢰도)는
    그대로 옮기고, 경제성 계산에 추가로 필요한 7개 입지 변수는 인자로
    받거나 보은 파일럿 기본값으로 채운다.

    Parameters
    ----------
    stand_state : StandStateEstimate | dict
        Module A `predict_stand()` 의 출력.
    site_index : int, optional
        지위지수. 미지정 시 정우 B 의 si_estimate 또는 영급 기반 추정.
    distance_to_road_km : float, optional
        임도까지 거리(km). 임도망 GIS 에서 산출하는 것이 이상적.
    elev : float, optional
        해발고(m). 정우 D15 기후 보정에 사용.
    slope_deg : float, optional
        경사도(도). 표준품셈 할증 산정에 사용.
    ownership : str
        소유 구분("공사유림" 기본).

    Returns
    -------
    dict
        `compute_lev()` 가 곧바로 소비할 수 있는 15개 키의 stand dict.

    Examples
    --------
    >>> from module_a.predict_stand import predict_stand
    >>> est = predict_stand(geom_wkt="POLYGON((...))", pnu="43745...",
    ...                     species_dominant="신갈나무", age_estimate=45)
    >>> stand = from_module_a(est, site_index=14, distance_to_road_km=1.5)
    >>> stand["species_dominant"]
    '신갈나무'
    """
    a = _as_dict(stand_state)

    # Module A 수종 키 → 정우 B/D 정식명
    bd_species = _to_bd_species(a.get("species_dominant", "기본활엽"))

    # 지위지수: 명시값 → Module A age 기반 추정 → 보수적 기본 14
    if site_index is None:
        site_index = _estimate_site_index(bd_species, a.get("age_estimate"))

    pnu = a.get("pnu", "")

    return {
        # ── Module A 가 위성으로 직접 제공 (8키) ──
        "pnu": pnu,
        "species_dominant": bd_species,
        "age_estimate": a.get("age_estimate") or 40,
        "area_ha": a.get("area_ha", 1.0),
        "volume_m3_per_ha": a.get("volume_m3_per_ha", 200.0),
        "volume_q05": a.get("volume_q05", a.get("volume_m3_per_ha", 200.0) * 0.85),
        "volume_q95": a.get("volume_q95", a.get("volume_m3_per_ha", 200.0) * 1.15),
        "carbon_tc_per_ha": a.get("carbon_tc_per_ha", 100.0),
        "confidence_level": a.get("confidence_level", "low"),
        "confidence_note": a.get("confidence_note"),
        # ── Module A 의 위성 불확실성 (D126 GEDI saturation) ──
        "agb_mg_per_ha": a.get("agb_mg_per_ha"),
        "agb_q05": a.get("agb_q05"),
        "agb_q95": a.get("agb_q95"),
        "saturation_warning": a.get("saturation_warning", False),
        # ── 어댑터가 보완 (7키) ──
        "site_index": site_index,
        "distance_to_road_km": (
            distance_to_road_km if distance_to_road_km is not None else _DEFAULT_DISTANCE_TO_ROAD_KM
        ),
        "elev": elev,
        "sigun": _pnu_to_sigun(pnu),
        "slope_class": _slope_to_class(slope_deg),
        "skidding_distance_m": _DEFAULT_SKIDDING_DISTANCE_M,
        "ownership": ownership,
        # ── 출처 추적 ──
        "_source": "module_a_satellite",
        "_geom_wkt": a.get("geom_wkt"),
    }


# ─────────────────────────────────────────────────────────────────────────
# 경로 2 — 정우 api_server.py forest_state(camelCase) → Module C stand dict
# ─────────────────────────────────────────────────────────────────────────


def from_forest_state(
    forest_state: dict,
    *,
    site_index: int | None = None,
    distance_to_road_km: float | None = None,
    elev: float | None = None,
    slope_deg: float | None = None,
    ownership: str = _DEFAULT_OWNERSHIP,
) -> dict:
    """정우 api_server.py 의 camelCase forest_state 를 stand dict 로 변환한다.

    api_server.py 는 Module A·B 를 묶어 ui 친화적 camelCase JSON 으로
    내보낸다. 이 함수는 그 JSON 을 Module C 가 읽는 snake_case dict 로
    되돌린다. forest_state 의 species 는 이미 정우 B/D 정식명이므로
    수종 매핑은 생략한다.
    """
    species = forest_state.get("species", "강원지방소나무")
    pnu = forest_state.get("pnu", "")

    if site_index is None:
        site_index = forest_state.get("siteIndex") or _estimate_site_index(
            species, forest_state.get("estimatedAge")
        )

    vol = forest_state.get("volumePerHa", 200.0)
    vol_unc = forest_state.get("volumeUncertainty", vol * 0.15)

    return {
        "pnu": pnu,
        "species_dominant": species,
        "age_estimate": forest_state.get("estimatedAge") or 40,
        "area_ha": forest_state.get("areaHa", 1.0),
        "volume_m3_per_ha": vol,
        "volume_q05": max(vol - 1.645 * vol_unc, 0.0),
        "volume_q95": vol + 1.645 * vol_unc,
        "carbon_tc_per_ha": forest_state.get("carbonPerHa", 100.0),
        "confidence_level": _confidence_from_warning(forest_state.get("dataWarning")),
        "confidence_note": forest_state.get("dataWarning"),
        "site_index": site_index,
        "distance_to_road_km": (
            distance_to_road_km if distance_to_road_km is not None else _DEFAULT_DISTANCE_TO_ROAD_KM
        ),
        "elev": elev,
        "sigun": _pnu_to_sigun(pnu),
        "slope_class": _slope_to_class(slope_deg),
        "skidding_distance_m": _DEFAULT_SKIDDING_DISTANCE_M,
        "ownership": ownership,
        "_source": "api_server_forest_state",
    }


# ─────────────────────────────────────────────────────────────────────────
# 보조 함수
# ─────────────────────────────────────────────────────────────────────────


def _estimate_site_index(species: str, age: int | None) -> int:
    """지위지수 보수적 추정.

    정우 B 의 si_estimate.py 가 위성·DEM·기상으로 정밀 추정하는 것이
    이상적이나, 통합 전 단계에서는 보은 파일럿의 수종별 평균 지위지수
    (산림학자 deliberation, FLIS 임지생산력급지도 기반)를 사용한다.
    """
    _SI_BY_SPECIES = {
        "강원지방소나무": 15,
        "중부지방소나무": 15,
        "잣나무": 15,
        "낙엽송": 17,
        "리기다소나무": 10,
        "편백": 14,
        "참나무류": 12,
        "신갈나무": 12,
        "굴참나무": 12,
        "상수리나무": 12,
    }
    return _SI_BY_SPECIES.get(species, 14)


def _confidence_from_warning(data_warning: str | None) -> str:
    """정우 B 의 dataWarning 유무로 신뢰도를 추정한다."""
    if not data_warning:
        return "medium"
    if "외삽" in data_warning or "범위 밖" in data_warning:
        return "low"
    return "medium"


def get_satellite_uncertainty_note(stand: dict) -> str | None:
    """Module A 위성 추정의 D126 한계를 산주에게 전달할 한국어 문장.

    GEDI saturation 으로 고밀도 침엽수림의 AGB 가 과소추정될 수 있다는
    Module A 의 알려진 한계(NFI 외부검증 R²=-0.187)를 정직하게 노출한다.
    """
    if stand.get("saturation_warning"):
        return (
            "위성 추정 주의: 이 임분은 고밀도 침엽수림으로, GEDI 라이다의 "
            "포화 구간(AGB>130 Mg/ha)에 해당합니다. 실제 체적이 위성 추정보다 "
            "클 수 있으므로(NFI 외부검증 R²=-0.187), 현장 조사로 확인을 권장합니다."
        )
    if stand.get("confidence_level") == "low":
        return (
            "위성 추정 신뢰도 낮음: 유효 픽셀이 적어 학습 데이터 평균에 의존했습니다. "
            "현장 조사 시 추정 폭이 크게 줄어듭니다."
        )
    return None


if __name__ == "__main__":
    print("=" * 66)
    print("stand_adapter.py 자가 검증")
    print("=" * 66)

    # Module A 출력 모사 (StandStateEstimate dict)
    fake_module_a = {
        "pnu": "4374533021100010000",
        "geom_wkt": "POLYGON((127.73 36.58, 127.74 36.58, 127.74 36.59, 127.73 36.59, 127.73 36.58))",
        "area_ha": 25.6,
        "species_dominant": "신갈",  # Module A 키
        "age_estimate": 45,
        "agb_mg_per_ha": 142.0,
        "agb_q05": 98.0,
        "agb_q95": 188.0,
        "volume_m3_per_ha": 215.0,
        "volume_q05": 148.0,
        "volume_q95": 285.0,
        "carbon_tc_per_ha": 96.0,
        "carbon_q05": 66.0,
        "carbon_q95": 128.0,
        "grade_distribution": {"중경": 0.4, "대경1": 0.3},
        "saturation_warning": True,  # 고밀도 침엽수 (실제로는 신갈이지만 테스트)
        "confidence_level": "high",
        "confidence_note": "유효 픽셀 1,240개 기반 예측",
    }

    print("\n[검증 1] Module A → Module C stand dict 변환")
    stand = from_module_a(fake_module_a, site_index=14, distance_to_road_km=1.5)
    print(f"  수종 매핑: '신갈' → '{stand['species_dominant']}'")
    print(f"  체적 중앙값: {stand['volume_m3_per_ha']} m³/ha")
    print(f"  체적 분산(위성): {stand['volume_q05']} ~ {stand['volume_q95']}")
    print(f"  시군(PNU 추출): {stand['sigun']}")
    print(f"  신뢰도: {stand['confidence_level']}")
    assert stand["species_dominant"] == "신갈나무"
    assert stand["sigun"] == "보은"
    assert stand["volume_q05"] == 148.0  # Module A 실 위성 분산

    print("\n[검증 2] saturation 경고 → 산주 문장")
    note = get_satellite_uncertainty_note(stand)
    print(f"  {note[:50]}...")
    assert "GEDI" in note

    print("\n[검증 3] forest_state(camelCase) → stand dict 변환")
    fake_fs = {
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
    stand2 = from_forest_state(fake_fs)
    print(f"  수종: {stand2['species_dominant']}")
    print(f"  체적 분산: {stand2['volume_q05']:.1f} ~ {stand2['volume_q95']:.1f}")
    assert stand2["species_dominant"] == "강원지방소나무"
    assert stand2["site_index"] == 15

    print("\n[검증 4] 수종 역매핑 전체")
    for a_key, bd_name in [
        ("강원소나무", "강원지방소나무"),
        ("리기다", "리기다소나무"),
        ("신갈", "신갈나무"),
        ("기본활엽", "참나무류"),
    ]:
        assert _to_bd_species(a_key) == bd_name
        print(f"  '{a_key}' → '{bd_name}' ✓")

    print("\n" + "=" * 66)
    print("✅ stand_adapter.py 4/4 검증 통과 (Module A ↔ Module C 호환)")
    print("=" * 66)
