"""
kosis_probe.py — KOSIS 지표정보 조회 서비스에 임가경제 지표가 있는지 진단.
일회성 진단 스크립트.
"""
import os, requests
from pathlib import Path
from urllib.parse import quote
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / ".env")
KEY = os.getenv("DATA_GO_KR_KEY")
URL = "http://apis.data.go.kr/1240000/IndicatorService/IndListSearchRequest"

for kw in ["임가", "임업", "임가소득", "농가소득", "가계"]:
    params = {"serviceKey": KEY, "STAT_JIPYO_NM": kw, "format": "json"}
    try:
        r = requests.get(URL, params=params, timeout=20)
        print(f"\n[{kw}] HTTP {r.status_code}")
        # JSON 시도, 안 되면 raw
        try:
            data = r.json()
            body = data.get("response", {}).get("body", {})
            total = body.get("totalCount", "?")
            print(f"   totalCount: {total}")
            items = body.get("items", {})
            if items:
                il = items.get("item", []) if isinstance(items, dict) else items
                if not isinstance(il, list):
                    il = [il]
                for it in il[:5]:
                    print(f"   - {it.get('statJipyoNm')} ({it.get('unit')}, {it.get('areaTypeName')})")
        except Exception:
            print(f"   raw: {r.text[:300]}")
    except Exception as e:
        print(f"[{kw}] 에러: {e}")