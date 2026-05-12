"""
test_vworld.py
VWorld API로 PNU → 임야 polygon GeoJSON 가져오기
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

VWORLD_KEY = os.getenv("VWORLD_KEY")

# 테스트할 임야 PNU (충북 보은군 회북면 부수리 산 15)
TEST_PNU = "4374040025100150000"

# VWorld 데이터 API — 연속지적도 (임야)
url = "https://api.vworld.kr/req/data"

params = {
    "service": "data",
    "request": "GetFeature",
    "data": "LP_PA_CBND_BUBUN",  # 연속지적도 (필지 단위)
    "key": VWORLD_KEY,
    "attrFilter": f"pnu:=:{TEST_PNU}",
    "geometry": "true",
    "format": "json",
    "size": "10",
    "page": "1",
}

print(f"🌐 VWorld API 호출 중...")
print(f"   PNU: {TEST_PNU}")
print()

response = requests.get(url, params=params)

print(f"📡 응답 코드: {response.status_code}")
print()

if response.status_code == 200:
    data = response.json()
    
    # 응답 구조 확인
    result_status = data.get("response", {}).get("status")
    print(f"📋 결과 상태: {result_status}")
    
    if result_status == "OK":
        features = data["response"]["result"]["featureCollection"]["features"]
        print(f"✅ {len(features)}개 필지 발견!")
        
        if features:
            feat = features[0]
            props = feat["properties"]
            geom = feat["geometry"]
            
            print()
            print("===== 첫 번째 필지 정보 =====")
            print(f"  주소: {props.get('addr', '?')}")
            print(f"  지번: {props.get('jibun', '?')}")
            print(f"  면적: {props.get('lndpcl_ar', '?')} m²")
            print(f"  좌표계: {geom.get('type', '?')}")
            
            # 좌표 점 개수
            if geom.get("type") == "Polygon":
                coords = geom["coordinates"][0]
                print(f"  polygon 꼭짓점 수: {len(coords)}개")
                print(f"  첫 좌표: {coords[0]}")
    else:
        print(f"⚠️  응답: {data.get('response', {}).get('error', data)}")
else:
    print(f"❌ HTTP 오류: {response.text[:500]}")