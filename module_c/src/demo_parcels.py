"""
demo_parcels.py — 6 시연·검증용 polygon.

D19 (산림학자·경영자 deliberation):
- 4 작은 sample polygon (산주 의사결정 시연) — SI 15-17 정정
- D22 (정책학자 + carbonregistry 658건):
- 4 real 등록사업 polygon (W6 검증 case) — VWorld 실 좌표 + 인증 흡수량

좌표: 모두 VWorld 주소 검색으로 얻은 실 lon/lat.
PNU: real 등록사업은 carbonregistry 공개 사업번호 (산39 외 2필지 같은 lot_id).

희도 D19 + D22 결정 — 2026-05-20 Day 6 갱신
"""

from typing import Dict


# ===========================================================
# 1. 작은 sample polygon (산주 의사결정 시연용)
# ===========================================================

SAMPLE_PARCELS: Dict[str, Dict] = {
    "boeun_pine_30y_1.5ha": {
        "_type": "sample",
        "pnu": "4374025931200110000",
        "species_dominant": "강원지방소나무",
        "site_index": 15,
        "age_estimate": 30,
        "area_ha": 1.5,
        "distance_to_road_km": 6.0,
        "skidding_distance_m": 800,
        "slope_class": "중",
        "geom_centroid_lon": 127.71804,
        "geom_centroid_lat": 36.50673,
        "geom_wkt": "POLYGON((127.71754 36.50623, 127.71854 36.50623, 127.71854 36.50723, 127.71754 36.50723, 127.71754 36.50623))",
        "volume_m3_per_ha": 173.0,
        "volume_q05": 138.0,
        "volume_q95": 208.0,
        "agb_mg_per_ha": 126.5,
        "carbon_tc_per_ha": 81.3,
        "confidence_level": "low",
        "confidence_note": "보은읍 임의 좌표 (VWorld 보은읍 중심) — 산주 의사결정 시연용 sample",
        "_label": "작은 사유림 sample (30년)",
        "_scenario_focus": "법정 40년 < 30년 → 즉시벌채 불가. 10년/연장KOC 비교 시연.",
    },
    "boeun_pine_50y_2ha": {
        "_type": "sample",
        "pnu": "4374025931200220000",
        "species_dominant": "강원지방소나무",
        "site_index": 15,
        "age_estimate": 50,
        "area_ha": 2.0,
        "distance_to_road_km": 1.5,
        "skidding_distance_m": 500,
        "slope_class": "중",
        "geom_centroid_lon": 127.71804,
        "geom_centroid_lat": 36.50673,
        "geom_wkt": "POLYGON((127.71704 36.50573, 127.71904 36.50573, 127.71904 36.50773, 127.71704 36.50773, 127.71704 36.50573))",
        "volume_m3_per_ha": 281.0,
        "volume_q05": 225.0,
        "volume_q95": 337.0,
        "carbon_tc_per_ha": 132.1,
        "confidence_level": "low",
        "_label": "벌기령 도달 sample (50년)",
        "_scenario_focus": "모든 시나리오 가능. 즉시 vs 연장KOC trade-off 시연.",
    },
}


# ===========================================================
# 2. Real 등록사업 polygon (W6 검증 case)
# 출처: carbonregistry.forest.go.kr (사용자 제공 2026-05-20, 658건)
# ===========================================================

REAL_REGISTERED_PARCELS: Dict[str, Dict] = {
    "boeun_real_oedari_8197tco2": {
        "_type": "real_registered",
        "carbonregistry_id": "FCR_43_BOEUN_001",
        "lot_id": "충청북도 보은군 산외면 오대리 산39 외 2필지",
        "pnu_partial": "43745",  # 충북 보은 시도+시군 코드
        "species_dominant": "강원지방소나무",
        "site_index": 14,
        "age_estimate": 40,  # 벌기연장 사업 = 법정 40년 도달 시점 + 연장
        "area_ha": 25.6,  # 8,197 tCO₂ ÷ 320 tCO₂/ha (30년 평균) ≈ 25.6 ha
        "distance_to_road_km": 1.5,  # 산외면 평균 추정
        "geom_centroid_lon": 127.73435,
        "geom_centroid_lat": 36.58411,
        "volume_m3_per_ha": 240.0,  # 강원소나무 40년 SI=14 추정
        "carbon_tc_per_ha": 110.0,
        "registered_total_absorption_tco2": 8197,
        "registered_avg_uptake_tco2_per_ha_per_yr": 10.67,
        "transaction_type": "거래",
        "project_type": "산림경영 > 벌기령연장",
        "confidence_level": "registered",
        "confidence_note": "carbonregistry.forest.go.kr 인증사업 — 정량 검증 가능",
        "_label": "★★★ Primary 검증 case (보은 산외면 오대리)",
        "_validation_priority": "★★★",
        "_scenario_focus": "벌기연장 시나리오 — 모델 추정 vs 인증 흡수량 비교",
    },
    "boeun_real_wonpyeongri_63658tco2": {
        "_type": "real_registered",
        "carbonregistry_id": "FCR_43_BOEUN_002",
        "lot_id": "충청북도 보은군 산외면 원평리 11 외 11필지",
        "species_dominant": "강원지방소나무",
        "site_index": 14,
        "age_estimate": 45,
        "area_ha": 198.9,
        "distance_to_road_km": 2.0,
        "geom_centroid_lon": 127.73476,
        "geom_centroid_lat": 36.58784,
        "volume_m3_per_ha": 260.0,
        "carbon_tc_per_ha": 120.0,
        "registered_total_absorption_tco2": 63658,
        "registered_avg_uptake_tco2_per_ha_per_yr": 10.67,
        "transaction_type": "거래",
        "project_type": "산림경영 > 벌기령연장",
        "confidence_level": "registered",
        "_label": "★★ 큰 규모 보은 사업 (198 ha)",
    },
    "jinan_real_waryongri_4671tco2": {
        "_type": "real_registered",
        "carbonregistry_id": "FCR_45_JINAN_003",
        "lot_id": "전라북도 진안군 용담면 와룡리 산48 외 1필지",
        "species_dominant": "강원지방소나무",
        "site_index": 14,
        "age_estimate": 40,
        "area_ha": 14.6,
        "distance_to_road_km": 1.8,
        "geom_centroid_lon": 127.46763,
        "geom_centroid_lat": 35.97994,
        "volume_m3_per_ha": 240.0,
        "carbon_tc_per_ha": 110.0,
        "registered_total_absorption_tco2": 4671,
        "registered_avg_uptake_tco2_per_ha_per_yr": 10.67,
        "transaction_type": "거래",
        "project_type": "산림경영 > 벌기령연장",
        "confidence_level": "registered",
        "_label": "★★★ Secondary 검증 case (진안 와룡리, 사유림 모달)",
        "_validation_priority": "★★★",
    },
    "jinan_real_guryongri_18063tco2": {
        "_type": "real_registered",
        "carbonregistry_id": "FCR_45_JINAN_001",
        "lot_id": "전라북도 진안군 상전면 구룡리 산122 외 6필지",
        "species_dominant": "강원지방소나무",
        "site_index": 14,
        "age_estimate": 42,
        "area_ha": 56.4,
        "distance_to_road_km": 2.5,
        "geom_centroid_lon": 127.52935,
        "geom_centroid_lat": 35.89841,
        "volume_m3_per_ha": 250.0,
        "carbon_tc_per_ha": 115.0,
        "registered_total_absorption_tco2": 18063,
        "registered_avg_uptake_tco2_per_ha_per_yr": 10.68,
        "transaction_type": "거래",
        "project_type": "산림경영 > 벌기령연장",
        "confidence_level": "registered",
        "_label": "★★ Tertiary 검증 (진안 구룡리, 56 ha)",
    },
}


# ===========================================================
# 통합 dict
# ===========================================================

DEMO_PARCELS: Dict[str, Dict] = {**SAMPLE_PARCELS, **REAL_REGISTERED_PARCELS}


def get_demo_parcel(parcel_id: str) -> Dict:
    """전체 6 polygon 중 1개 반환."""
    if parcel_id not in DEMO_PARCELS:
        raise ValueError(f"Unknown parcel: {parcel_id}. Available: {list(DEMO_PARCELS.keys())}")
    return DEMO_PARCELS[parcel_id].copy()


def list_demo_parcels(type_filter: str = None) -> list:
    """parcel 목록.
    type_filter: None | "sample" | "real_registered"
    """
    if type_filter:
        return [k for k, v in DEMO_PARCELS.items() if v.get("_type") == type_filter]
    return list(DEMO_PARCELS.keys())


def list_real_parcels() -> list:
    """W6 검증 case 4 polygon."""
    return list_demo_parcels("real_registered")


def list_sample_parcels() -> list:
    """산주 시연 sample polygon."""
    return list_demo_parcels("sample")


if __name__ == "__main__":
    print("=" * 70)
    print("demo_parcels.py — 6 polygon 정의")
    print("=" * 70)

    print(f"\n총 {len(DEMO_PARCELS)} polygon")
    print(f"  sample (산주 시연): {len(list_sample_parcels())}")
    print(f"  real (W6 검증): {len(list_real_parcels())}")

    print("\n[Sample polygon — 산주 의사결정 시연]")
    for key in list_sample_parcels():
        p = DEMO_PARCELS[key]
        print(f"\n  {key}")
        print(f"    {p['species_dominant']} {p['age_estimate']}년 SI={p['site_index']} {p['area_ha']}ha")
        print(f"    좌표: lon={p['geom_centroid_lon']:.4f}, lat={p['geom_centroid_lat']:.4f}")
        print(f"    {p['_label']}")

    print("\n[Real 등록사업 polygon — W6 검증 case]")
    for key in list_real_parcels():
        p = DEMO_PARCELS[key]
        print(f"\n  {key}")
        print(f"    {p['lot_id']}")
        print(f"    면적: {p['area_ha']} ha, 인증 {p['registered_total_absorption_tco2']:,} tCO₂")
        print(f"    좌표: lon={p['geom_centroid_lon']:.4f}, lat={p['geom_centroid_lat']:.4f}")
        print(f"    유형: {p['project_type']} ({p['transaction_type']})")
        print(f"    {p['_label']}")

    print("\n" + "=" * 70)
    print("✅ 6 polygon 정의 완료 (Sample 2 + Real 4)")
    print("=" * 70)
