"""
mt_weather_api.py
가이드 §2.3 — 산악기상정보 API 호출.

출처: 산림청_국립산림과학원_산악기상정보
- Base URL: http://apis.data.go.kr/1400377/mtweather/mountListSearch
- 인증: DATA_GO_KR_KEY (공공데이터포털 9 API 공통)
- 600+ 관측소, 시간 단위 (10m/2m 기온·습도·풍속·강수)

목적: growth_predict() 의 climate_scenario 진짜 보정 +
      충북 보은 인근 6 관측소 시계열 활용.
"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

API_KEY = os.getenv("DATA_GO_KR_KEY")
BASE_URL = "http://apis.data.go.kr/1400377/mtweather/mountListSearch"


# 충북 보은 인근 6 관측소 (가이드 §2.3 의 진짜 매핑)
BOEUN_STATIONS = {
    3033: {"name": "보은 가덕산", "lat": 36.52, "lon": 127.57, "alt": 324},
    3898: {"name": "보은 금단산", "lat": 36.61, "lon": 127.79, "alt": 627},
    3903: {"name": "보은 염동산", "lat": 36.49, "lon": 127.64, "alt": 282},
    3915: {"name": "보은 시루산", "lat": 36.55, "lon": 127.70, "alt": 362},
    3917: {"name": "보은 삼승산", "lat": 36.39, "lon": 127.75, "alt": 242},
    3918: {"name": "보은 노성산", "lat": 36.46, "lon": 127.63, "alt": 314},
}


def fetch_mt_weather(
    obsid: int = None,
    tm: str = None,
    local_area: str = "12",  # 충청북도
    page_no: int = 1,
    num_of_rows: int = 100,
) -> dict:
    """
    산악기상정보 API 호출.
    
    Args:
        obsid: 지점번호 (없으면 local_area 의 모든 관측소)
        tm: 관측시간 (예: "202412310900" — YYYYMMDDHHMM)
        local_area: 지역코드 (12 = 충청북도)
        page_no, num_of_rows: 페이지네이션
    
    Returns:
        dict: 응답 데이터 (resultCode, items, ...)
    """
    if not API_KEY:
        raise ValueError("DATA_GO_KR_KEY 가 .env 에 없음")
    
    params = {
        "serviceKey": API_KEY,
        "pageNo": page_no,
        "numOfRows": num_of_rows,
        "_type": "json",
        "localArea": local_area,
    }
    
    if obsid is not None:
        params["obsid"] = str(obsid)
    if tm is not None:
        params["tm"] = tm
    
    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    
    return response.json()


if __name__ == "__main__":
    from datetime import datetime, timedelta
    
    print("=" * 60)
    print("🌤  산악기상 과거 데이터 범위 진단")
    print("=" * 60)
    print("   관측소: 보은 가덕산 (3033)")
    print("   각 연도 동일 날짜(오늘 기준) 정오 데이터 확인")
    print("-" * 60)
    
    today = datetime.now()
    
    # 2021년 경계 정밀 확인 — 여러 달 + 2020년
    print("   [경계 확인] 2020-2022년 여러 시점")
    test_dates = [
        ("202201151200", "2022-01"),
        ("202205151200", "2022-05"),
        ("202109151200", "2021-09"),
        ("202105151200", "2021-05"),
        ("202101151200", "2021-01"),
        ("202009151200", "2020-09"),
        ("202005151200", "2020-05"),
        ("201906151200", "2019-06"),
    ]
    for tm, label in test_dates:
        try:
            result = fetch_mt_weather(obsid=3033, tm=tm, num_of_rows=1)
            items = result.get("response", {}).get("body", {}).get("items", "")
            if items and items != "":
                it = items.get("item", {})
                print(f"   {label}: ✅ 2m기온 {it.get('tm2m')}℃")
            else:
                print(f"   {label}: ❌ 없음")
        except Exception as e:
            print(f"   {label}: 에러 {e}")
    
    # 6 관측소 중 신설 관측소(3890번대) 확인 — 1년 전 데이터
    print("-" * 60)
    print("   보은 6 관측소 — 1년 전 데이터 유무 (관측소별 개통 시기 다름)")
    print("-" * 60)
    one_year = (today - timedelta(days=365)).strftime("%Y%m%d") + "1200"
    for obsid, info in BOEUN_STATIONS.items():
        try:
            result = fetch_mt_weather(obsid=obsid, tm=one_year, num_of_rows=1)
            items = result.get("response", {}).get("body", {}).get("items", "")
            if items and items != "":
                it = items.get("item", {})
                print(f"   [{obsid}] {info['name']:>10} (고도 {info['alt']}m): ✅ {it.get('tm2m')}℃")
            else:
                print(f"   [{obsid}] {info['name']:>10} (고도 {info['alt']}m): ❌ 없음")
        except Exception as e:
            print(f"   [{obsid}] {info['name']}: 에러 {e}")
    
    print()
    print("=" * 60)
    print("✅ 진단 완료 — 사용 가능 범위 확인")
    print("=" * 60)