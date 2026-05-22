"""
fixtures.py — pytest 공통 fixture (정우 _base() 패턴 모방).

D6 reference 패턴 동일 — 검증 기준값 + 회귀 baseline 분리.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


# D-fixture-1: 보은 50년 강원지방소나무 — 벌기령 도달, "표준 시나리오"
BASE_BOEUN_50Y = {
    "pnu": "4374025931200220000",
    "species_dominant": "강원지방소나무",
    "site_index": 15,
    "age_estimate": 50,
    "area_ha": 2.0,
    "distance_to_road_km": 1.5,
    "skidding_distance_m": 500,
    "slope_class": "중",
    "volume_m3_per_ha": 281.0,
    "volume_q05": 225.0,
    "volume_q95": 337.0,
    "carbon_tc_per_ha": 132.1,
    "confidence_level": "low",
}


# D-fixture-2: 보은 30년 (벌기령 미달)
BASE_BOEUN_30Y = {
    "pnu": "4374025931200110000",
    "species_dominant": "강원지방소나무",
    "site_index": 15,
    "age_estimate": 30,
    "area_ha": 1.5,
    "distance_to_road_km": 6.0,
    "skidding_distance_m": 800,
    "slope_class": "중",
    "volume_m3_per_ha": 173.0,
    "volume_q05": 138.0,
    "volume_q95": 208.0,
    "carbon_tc_per_ha": 81.3,
    "confidence_level": "low",
}


# D-fixture-3: 진안 낙엽송 25년
BASE_JINAN_25Y = {
    "pnu": "4574025931200330000",
    "species_dominant": "낙엽송",
    "site_index": 17,
    "age_estimate": 25,
    "area_ha": 5.0,
    "distance_to_road_km": 2.0,
    "volume_m3_per_ha": 195.0,
    "carbon_tc_per_ha": 90.0,
    "confidence_level": "low",
}


def base_stand(override=None) -> dict:
    """기본 stand_state dict (override 가능)."""
    stand = BASE_BOEUN_50Y.copy()
    if override:
        stand.update(override)
    return stand
