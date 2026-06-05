"""
test_keys.py — 희도(zxsa0716) 본인 명의 API 키 sanity check.

정우 test_keys.py 패턴 모방. 실 API 호출하여 키 작동 확인.

사용:
    python module_c/scripts/test_keys.py

출력: 5 키 (DATA_GO_KR, VWORLD, KOSIS, LAW_OC, ENV 로드) 동작 여부.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# .env 로드
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    print("⚠️  python-dotenv 미설치 — pip install python-dotenv")
    sys.exit(1)


def mask(key: str, n: int = 8) -> str:
    """키를 일부만 표시 (보안)."""
    if not key:
        return "?? (미설정)"
    if len(key) <= n * 2:
        return key[:n] + "..."
    return f"{key[:n]}...{key[-4:]}"


def test_env_loaded():
    print("\n[1] .env 파일 로드 확인")
    keys = ["DATA_GO_KR_KEY", "DATA_GO_KR_KEY", "VWORLD_KEY", "KOSIS_KEY", "LAW_OC"]
    all_ok = True
    for k in keys:
        v = os.environ.get(k)
        status = "✅" if v else "❌"
        print(f"  {status} {k}: {mask(v)}")
        if not v:
            all_ok = False
    return all_ok


def test_data_go_kr():
    print("\n[2] data.go.kr — 산림자원통계 OpenAPI")
    try:
        import requests
        key = os.environ.get("DATA_GO_KR_KEY")
        url = "http://apis.data.go.kr/1400000/frsas1/selectStatList1"
        r = requests.get(url, params={
            "serviceKey": key, "pageNo": 1, "numOfRows": 3, "clsscId": "woodUseReq",
        }, timeout=15)
        if r.status_code == 200:
            data = r.json()
            print(f"  ✅ {r.status_code} {data.get('msg', '')[:30]} count={len(data.get('data', []))}")
            return True
        else:
            print(f"  ❌ {r.status_code} {r.text[:100]}")
            return False
    except Exception as e:
        print(f"  ❌ {e}")
        return False


def test_kau_price():
    print("\n[3] data.go.kr — KAU 배출권 시세 (금융위 1160100)")
    try:
        import requests
        key = os.environ.get("DATA_GO_KR_KEY")
        url = "https://apis.data.go.kr/1160100/service/GetGeneralProductInfoService/getCertifiedEmissionReductionPriceInfo"
        r = requests.get(url, params={
            "serviceKey": key, "pageNo": 1, "numOfRows": 1,
            "resultType": "json", "likeItmsNm": "KAU",
        }, timeout=15)
        if r.status_code == 200:
            body = r.json().get("response", {}).get("body", {})
            total = body.get("totalCount", 0)
            print(f"  ✅ {r.status_code} totalCount={total}")
            return True
        else:
            print(f"  ❌ {r.status_code} {r.text[:100]}")
            return False
    except Exception as e:
        print(f"  ❌ {e}")
        return False


def test_vworld():
    print("\n[4] VWorld — 주소 → 좌표")
    try:
        import requests
        key = os.environ.get("VWORLD_KEY")
        url = "http://api.vworld.kr/req/address"
        r = requests.get(url, params={
            "service": "address", "request": "getCoord",
            "key": key, "address": "충북 보은군 보은읍",
            "type": "PARCEL", "format": "json",
        }, timeout=15)
        if r.status_code == 200:
            data = r.json().get("response", {})
            status = data.get("status")
            print(f"  ✅ {r.status_code} status={status}")
            if status == "OK":
                pt = data.get("result", {}).get("point", {})
                print(f"     point: lon={pt.get('x')}, lat={pt.get('y')}")
            return status == "OK"
        else:
            print(f"  ❌ {r.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ {e}")
        return False


def test_law():
    print("\n[5] 법제처 OC — 법령 조회")
    try:
        import requests
        oc = os.environ.get("LAW_OC")
        # 별표3 (기준벌기령) 검색
        url = "http://www.law.go.kr/DRF/lawSearch.do"
        r = requests.get(url, params={
            "OC": oc, "target": "law", "type": "JSON",
            "query": "산림자원의 조성 및 관리에 관한 법률",
        }, timeout=15)
        if r.status_code == 200:
            print(f"  ✅ {r.status_code} {len(r.text)} bytes")
            return True
        else:
            print(f"  ❌ {r.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ {e}")
        return False


def test_kosis():
    print("\n[6] KOSIS — 통계자료 조회 (보조)")
    try:
        import requests
        key = os.environ.get("KOSIS_KEY")
        # KOSIS 통계 메타 조회 (가장 단순 호출)
        url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
        r = requests.get(url, params={
            "apiKey": key, "method": "getList",
            "orgId": "143", "tblId": "DT_143F002",  # 임가경제조사 (정우 5/18 probe)
            "format": "json", "objL1": "0",
            "prdSe": "Y", "newEstPrdCnt": "1",
        }, timeout=15)
        if r.status_code == 200:
            txt = r.text[:200]
            print(f"  ✅ {r.status_code} {txt[:100]}")
            return True
        else:
            print(f"  ❌ {r.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("희도 본인 명의 API 키 sanity check")
    print("=" * 60)

    results = {
        "env": test_env_loaded(),
        "data_go_kr": test_data_go_kr(),
        "kau": test_kau_price(),
        "vworld": test_vworld(),
        "law": test_law(),
        "kosis": test_kosis(),
    }

    print("\n" + "=" * 60)
    print("결과 종합")
    print("=" * 60)
    for k, v in results.items():
        print(f"  {'✅' if v else '❌'} {k}")

    passed = sum(1 for v in results.values() if v)
    print(f"\n{passed}/{len(results)} 통과")

    if passed < len(results):
        print("\n⚠️  실패한 항목은 키 미발급 또는 활용신청 승인 대기 중일 수 있음")
