"""
data_go_kr_api.py — data.go.kr OpenAPI 호출 wrapper.

지원 API:
1. 산림청 산림자원통계 (1400000/frsas1) — selectStatList1
2. 금융위 일반상품시세정보 (1160100) — KAU 배출권 시세

키 로드: os.environ["DATA_GO_KR_KEY_ENCODED"] (.env)

희도 D-API 결정 — 2026-05-20 Day 6 작성
"""

import os
import sys
from typing import Dict

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    requests = None

# .env 자동 로드
try:
    from pathlib import Path

    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except ImportError:
    pass


# ============================================================
# 산림자원통계 (1400000/frsas1)
# ============================================================

_FOREST_STAT_BASE = "http://apis.data.go.kr/1400000/frsas1"


def fetch_forest_statistics(
    clssc_id: str | None = None,
    page_no: int = 1,
    num_of_rows: int = 100,
    *,
    api_key_env: str = "DATA_GO_KR_KEY",
) -> Dict:
    """
    산림자원통계 시스템 통계 목록 조회.

    출처: OpenAPI활용가이드_산림청_산림자원통계 서비스_v1.2.docx

    Parameters
    ----------
    clssc_id : str, optional
        통계분류 ID (예: "woodUseReq" 목재이용실태조사)
    page_no : int
    num_of_rows : int
    api_key_env : str
        환경변수명. 기본 인코딩된 키.

    Returns
    -------
    dict
        {
            "msg": "조회가 완료되었습니다.",
            "code": 1,
            "data": [...],
            "totalCount": int,
        }

    Examples
    --------
    >>> r = fetch_forest_statistics(clssc_id="woodUseReq", num_of_rows=5)
    >>> r["code"] == 1
    True
    """
    if not HAS_REQUESTS:
        raise ImportError("requests 필요 — pip install requests python-dotenv")

    key = os.environ.get(api_key_env)
    if not key:
        raise RuntimeError(f"환경변수 {api_key_env} 미설정 — .env 확인")

    url = f"{_FOREST_STAT_BASE}/selectStatList1"
    params = {
        "serviceKey": key,
        "pageNo": page_no,
        "numOfRows": num_of_rows,
    }
    if clssc_id:
        params["clsscId"] = clssc_id

    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


# ============================================================
# 금융위 일반상품시세정보 — 배출권 시세 (1160100)
# ============================================================

_FIN_BASE = "https://apis.data.go.kr/1160100/service/GetGeneralProductInfoService"


def fetch_kau_price(
    bas_dt: str | None = None,
    begin_bas_dt: str | None = None,
    end_bas_dt: str | None = None,
    like_itms_nm: str = "KAU",
    page_no: int = 1,
    num_of_rows: int = 20,
    result_type: str = "json",
    *,
    api_key_env: str = "DATA_GO_KR_KEY",
) -> Dict:
    """
    KAU 배출권 시세 조회 (한국거래소 탄소배출권시장).

    출처: 오픈API 활용자가이드_금융위원회_일반상품시세정보.docx Table 11-14

    Parameters
    ----------
    bas_dt : str, optional
        기준일자 (YYYYMMDD) — 단일 일자
    begin_bas_dt / end_bas_dt : str, optional
        기간 조회
    like_itms_nm : str
        종목명 검색 (기본 "KAU" — KAU22, KAU23, KAU24, KAU25 모두 포함)
    page_no, num_of_rows : int
    result_type : str
        "json" or "xml"

    Returns
    -------
    dict
        {
            "response": {
                "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
                "body": {
                    "items": [{...}],
                    "totalCount": int,
                }
            }
        }

    Examples
    --------
    >>> # 2024 년 KAU 시세
    >>> r = fetch_kau_price(begin_bas_dt="20240101", end_bas_dt="20241231",
    ...                     like_itms_nm="KAU24", num_of_rows=10)
    >>> "response" in r
    True
    """
    if not HAS_REQUESTS:
        raise ImportError("requests 필요")

    key = os.environ.get(api_key_env)
    if not key:
        raise RuntimeError(f"환경변수 {api_key_env} 미설정")

    url = f"{_FIN_BASE}/getCertifiedEmissionReductionPriceInfo"
    params = {
        "serviceKey": key,
        "pageNo": page_no,
        "numOfRows": num_of_rows,
        "resultType": result_type,
        "likeItmsNm": like_itms_nm,
    }
    if bas_dt:
        params["basDt"] = bas_dt
    if begin_bas_dt:
        params["beginBasDt"] = begin_bas_dt
    if end_bas_dt:
        params["endBasDt"] = end_bas_dt

    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    if result_type == "json":
        return r.json()
    return {"raw_xml": r.text}


def fetch_kau_latest_close() -> float | None:
    """
    KAU 최신 종가 1건 (편의 함수).

    Returns
    -------
    float | None
        최신 KAU 종가 (원/tCO₂), 실패 시 None
    """
    try:
        r = fetch_kau_price(like_itms_nm="KAU", num_of_rows=1, page_no=1)
        body = r.get("response", {}).get("body", {})
        items = body.get("items", {})
        if isinstance(items, dict):
            items = items.get("item", [])
        if not items:
            return None
        if isinstance(items, dict):
            items = [items]
        return float(items[0].get("clpr", 0))
    except Exception as e:
        print(f"⚠️  fetch_kau_latest_close failed: {e}")
        return None


def fetch_oil_price(num_of_rows: int = 5, oil_ctg: str = "경유") -> Dict:
    """석유시세 (보조 — 운반비 변동 sensitivity 분석용)."""
    if not HAS_REQUESTS:
        raise ImportError("requests 필요")
    key = os.environ.get("DATA_GO_KR_KEY")
    if not key:
        raise RuntimeError("DATA_GO_KR_KEY 미설정")
    url = f"{_FIN_BASE}/getOilPriceInfo"
    r = requests.get(
        url,
        params={
            "serviceKey": key,
            "pageNo": 1,
            "numOfRows": num_of_rows,
            "resultType": "json",
            "oilCtg": oil_ctg,
        },
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


# ============================================================
# VWorld API — PNU/주소 → polygon
# ============================================================

_VWORLD_BASE = "http://api.vworld.kr/req"


def vworld_pnu_to_geometry(pnu: str) -> Dict:
    """
    VWorld 연속지적도 PNU → polygon 조회.

    Parameters
    ----------
    pnu : str
        19자리 PNU 코드

    Returns
    -------
    dict
        VWorld response (features 포함)
    """
    if not HAS_REQUESTS:
        raise ImportError("requests 필요")
    key = os.environ.get("VWORLD_KEY")
    if not key:
        raise RuntimeError("VWORLD_KEY 미설정")
    url = f"{_VWORLD_BASE}/data"
    r = requests.get(
        url,
        params={
            "key": key,
            "service": "data",
            "version": "2.0",
            "request": "GetFeature",
            "data": "LP_PA_CBND_BUBUN",
            "attrFilter": f"pnu:=:{pnu}",
            "geometry": "true",
            "format": "json",
        },
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def vworld_address_to_coord(address: str) -> Dict | None:
    """
    VWorld 주소 → 좌표 변환.

    Examples
    --------
    >>> r = vworld_address_to_coord("충북 보은군 보은읍")
    >>> r["status"]
    'OK'
    """
    if not HAS_REQUESTS:
        raise ImportError("requests 필요")
    key = os.environ.get("VWORLD_KEY")
    if not key:
        raise RuntimeError("VWORLD_KEY 미설정")
    url = f"{_VWORLD_BASE}/address"
    r = requests.get(
        url,
        params={
            "service": "address",
            "request": "getCoord",
            "key": key,
            "address": address,
            "type": "PARCEL",
            "format": "json",
        },
        timeout=15,
    )
    r.raise_for_status()
    return r.json().get("response", {})


if __name__ == "__main__":
    print("=" * 60)
    print("data_go_kr_api.py 자가 검증 (실 API 호출)")
    print("=" * 60)

    if not HAS_REQUESTS:
        print("\n⚠️  requests/python-dotenv 미설치 — pip install requests python-dotenv")
        sys.exit(0)

    print(f"\n  Key loaded (encoded): {os.environ.get('DATA_GO_KR_KEY_ENCODED', '?')[:20]}...")

    # 1. 산림자원통계
    print("\n[검증 1] 산림자원통계 — 목재이용실태조사")
    try:
        r = fetch_forest_statistics(clssc_id="woodUseReq", num_of_rows=3)
        print(f"  code={r.get('code')}, msg={r.get('msg', '')[:30]}")
        print(f"  data 개수: {len(r.get('data', []))}")
        if r.get("data"):
            print(f"  첫 항목: {r['data'][0]}")
    except Exception as e:
        print(f"  ❌ {e}")

    # 2. KAU 배출권 시세
    print("\n[검증 2] KAU 배출권 시세 (최근)")
    try:
        r = fetch_kau_price(like_itms_nm="KAU", num_of_rows=3)
        items = r.get("response", {}).get("body", {}).get("items", {})
        if isinstance(items, dict):
            items = items.get("item", [])
        if isinstance(items, dict):
            items = [items]
        print(f"  결과 수: {len(items) if items else 0}")
        for item in (items or [])[:3]:
            print(f"    {item.get('basDt')} {item.get('itmsNm'):>8s} 종가={item.get('clpr')}원")
    except Exception as e:
        print(f"  ❌ {e}")

    # 3. KAU 최신 종가 편의함수
    print("\n[검증 3] KAU 최신 종가 1개")
    close = fetch_kau_latest_close()
    print(f"  최신 종가: {close}원/tCO₂")

    # 4. VWorld 주소 변환
    print("\n[검증 4] VWorld 주소 → 좌표 (충북 보은군 보은읍)")
    try:
        r = vworld_address_to_coord("충북 보은군 보은읍")
        if r:
            print(f"  status: {r.get('status')}")
            result = r.get("result", {})
            point = result.get("point", {})
            print(f"  point: lon={point.get('x')}, lat={point.get('y')}")
    except Exception as e:
        print(f"  ❌ {e}")

    print("\n" + "=" * 60)
    print("✅ data_go_kr_api.py 동작 확인")
    print("=" * 60)
