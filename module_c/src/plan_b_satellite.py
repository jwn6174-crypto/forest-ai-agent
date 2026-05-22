"""
plan_b_satellite.py — Plan B 위성 통합 (위성 학자 Round 2 권고).

D117.b 선택 결정 — 발표 reviewer "왜 위성 안 썼나" 공격 대응.

위성/원격탐사 학자 권고:
- GEDI L4A footprint (36.58°N 보은 cover) + Sentinel-2 NDVI 시계열
- triangulation: NFI baseline + GEDI footprint sliced + S2 NDVI 시계열

상태: stub 코드 (실제 호출은 W4-5 통합 시점에 GEE 인증 + earthaccess 인증 후).
"""

from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]


# ============================================================
# GEDI L4A — footprint-level AGBD (h5py + earthaccess)
# ============================================================


def gedi_l4a_footprint_search(
    lat: float,
    lon: float,
    radius_m: int = 500,
) -> List[Dict]:
    """
    GEDI L4A AGBD footprint 조회 (NASA Earthdata earthaccess).

    NASA Earthdata 인증 필요:
        ~/.netrc 에 NASA login 또는 earthaccess.login()

    Parameters
    ----------
    lat, lon : float — polygon centroid
    radius_m : int — 검색 반경 (m)

    Returns
    -------
    list[dict]
        각 footprint 의 lat/lon/AGBD (Mg/ha) ± SE

    한국 위도 36-39°N: 1-3 shots/ha 밀도 추정 (위성 학자 Round 2)

    Examples
    --------
    >>> # 보은 산외면 오대리 (FCR_43_BOEUN_001)
    >>> footprints = gedi_l4a_footprint_search(36.5841, 127.7344, radius_m=500)
    >>> len(footprints) > 0
    True
    """
    try:
        import earthaccess  # noqa: F401
    except ImportError:
        return [
            {
                "error": "earthaccess 미설치",
                "install": "pip install earthaccess",
                "note": "NASA Earthdata 인증 필요 (~/.netrc 또는 earthaccess.login())",
            }
        ]

    # NOTE: 실 호출은 W4-5 통합 시점. 현재 stub.
    return [
        {
            "_stub": True,
            "_note": "GEDI L4A footprint stub — 실 호출은 W4-5 (위성 학자 권고)",
            "lat": lat,
            "lon": lon,
            "radius_m": radius_m,
            "_estimated_footprint_count": int((radius_m / 100) ** 2 * 1.5),  # 1-3/ha 가정
        }
    ]


# ============================================================
# Sentinel-2 NDVI 시계열 (GEE)
# ============================================================


def sentinel2_ndvi_timeseries(
    lat: float,
    lon: float,
    start_date: str = "2017-01-01",
    end_date: str = "2026-05-31",
    radius_m: int = 100,
) -> Dict:
    """
    Sentinel-2 NDVI 월별 시계열 — *벌채 여부 검증* (위성 학자 핵심 카드).

    벌채 발생 시 NDVI 0.8 → 0.2 급락 + 6-10년 회복.
    인증사업 4 polygon 의 2017-2026 NDVI 추세가 *평탄/상승* 이면 *벌채 없음 = 인증 유효성 입증*.

    Parameters
    ----------
    lat, lon : float — polygon centroid
    start_date, end_date : str
    radius_m : int — buffer (m)

    Returns
    -------
    dict
        {
            "monthly_ndvi": List[float],
            "monthly_dates": List[str],
            "trend": "평탄" | "상승" | "급락" | "회복",
            "harvest_detected": bool,
            "harvest_dates": List[str],
            "_note": "발표 가장 강력한 카드 — 위성 모델 없이 시계열만으로 인증 검증",
        }
    """
    try:
        import ee  # noqa: F401
    except ImportError:
        return {
            "error": "earthengine-api 미설치",
            "install": "pip install earthengine-api",
            "note": "GEE 인증 필요: ee.Authenticate() + ee.Initialize(project='...')",
        }

    # NOTE: 실 호출은 W4-5 통합 시점. 현재 stub.
    return {
        "_stub": True,
        "_note": "S2 NDVI 시계열 stub — 발표 W7 데모용 사전 캐싱 권장 (위성 학자)",
        "lat": lat,
        "lon": lon,
        "buffer_m": radius_m,
        "_period": f"{start_date} ~ {end_date}",
        "_expected_for_certified_case": {
            "trend": "평탄/상승",
            "harvest_detected": False,
            "interpretation": "인증사업이 *벌채 안 함* 약속 이행 입증",
        },
    }


# ============================================================
# Triangulation — NFI + GEDI + S2 통합 검증
# ============================================================


def triangulate_validation_case(
    case_id: str,
    lat: float,
    lon: float,
    *,
    nfi_estimate_tco2_per_ha: float | None = None,
    model_estimate_tco2_per_ha: float | None = None,
    certified_tco2_per_ha: float | None = None,
) -> Dict:
    """
    위성 학자 Plan B — 4 source triangulation 검증.

    1. NFI direct lookup (Module C 기본)
    2. Module C model (Faustmann 자연 성장)
    3. GEDI L4A current AGB stock (실측)
    4. S2 NDVI 시계열 (벌채 여부)
    + carbonregistry 인증값 (정량 비교)

    Examples
    --------
    >>> r = triangulate_validation_case("FCR_43_BOEUN_001",
    ...     36.5841, 127.7344,
    ...     nfi_estimate_tco2_per_ha=200,
    ...     model_estimate_tco2_per_ha=157,
    ...     certified_tco2_per_ha=320)
    >>> r["consensus_estimate"] > 0
    True
    """
    gedi = gedi_l4a_footprint_search(lat, lon)
    s2 = sentinel2_ndvi_timeseries(lat, lon)

    sources = {}
    if nfi_estimate_tco2_per_ha:
        sources["nfi"] = nfi_estimate_tco2_per_ha
    if model_estimate_tco2_per_ha:
        sources["model"] = model_estimate_tco2_per_ha
    if certified_tco2_per_ha:
        sources["certified"] = certified_tco2_per_ha
    # GEDI 는 stub 이므로 일단 None
    sources["gedi"] = None  # W4-5 실 호출 후 채움

    valid_sources = {k: v for k, v in sources.items() if v}
    consensus = sum(valid_sources.values()) / len(valid_sources) if valid_sources else 0

    return {
        "case_id": case_id,
        "lat": lat,
        "lon": lon,
        "sources": sources,
        "consensus_estimate": consensus,
        "gedi_footprints": gedi,
        "s2_ndvi": s2,
        "_interpretation": (
            f"NFI vs 모델 vs 인증 = {valid_sources}. "
            f"평균 {consensus:.1f} tCO₂/ha/30yr. "
            "GEDI+S2 통합 후 모집단 차이 정량 검증 가능."
        ),
        "_status": "W4-5 통합 시점 실 호출 (현재 stub)",
    }


# ============================================================
# 4 검증 case 의 Plan B 좌표
# ============================================================

PLAN_B_VALIDATION_CASES = {
    "FCR_43_BOEUN_001": {
        "lat": 36.5841,
        "lon": 127.7344,
        "lot_id": "충청북도 보은군 산외면 오대리 산39 외 2필지",
        "certified_tco2": 8197,
        "area_ha": 25.6,
    },
    "FCR_43_BOEUN_002": {
        "lat": 36.5878,
        "lon": 127.7348,
        "lot_id": "충청북도 보은군 산외면 원평리 11 외 11필지",
        "certified_tco2": 63658,
        "area_ha": 198.9,
    },
    "FCR_45_JINAN_003": {
        "lat": 35.9799,
        "lon": 127.4676,
        "lot_id": "전라북도 진안군 용담면 와룡리 산48 외 1필지",
        "certified_tco2": 4671,
        "area_ha": 14.6,
    },
    "FCR_45_JINAN_001": {
        "lat": 35.8984,
        "lon": 127.5294,
        "lot_id": "전라북도 진안군 상전면 구룡리 산122 외 6필지",
        "certified_tco2": 18063,
        "area_ha": 56.4,
    },
}


def run_plan_b_all_cases() -> Dict:
    """4 검증 case 모두 Plan B 실행 (W4-5 stub)."""
    return {
        case_id: triangulate_validation_case(
            case_id,
            info["lat"],
            info["lon"],
            model_estimate_tco2_per_ha=157.5,
            certified_tco2_per_ha=info["certified_tco2"] / info["area_ha"],
        )
        for case_id, info in PLAN_B_VALIDATION_CASES.items()
    }


if __name__ == "__main__":
    print("=" * 70)
    print("plan_b_satellite.py — Plan B 위성 통합 (W4-5 stub)")
    print("=" * 70)
    print()
    print("위성 학자 Round 2 권고:")
    print("  - +103% 차이는 자연성장 vs 경영후 측정의 모집단 차이")
    print("  - GEDI L4A + Sentinel-2 NDVI 시계열 = 발표 가장 강력한 카드")
    print("  - NFI baseline + GEDI sliced + S2 NDVI triangulation Plan B")
    print()

    results = run_plan_b_all_cases()
    for case_id, r in results.items():
        print(f"[{case_id}]")
        print(f"  {r['_interpretation']}")
        print(f"  GEDI: {(r['gedi_footprints'][0].get('_stub', False) and 'stub') or 'real'}")
        print(f"  S2 NDVI: {(r['s2_ndvi'].get('_stub', False) and 'stub') or 'real'}")
        print()

    print("=" * 70)
    print("✅ Plan B stub — W4-5 통합 시 GEE/earthaccess 인증 후 실 호출")
    print("=" * 70)
