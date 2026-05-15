"""
[학습 메모 2026-05-12]
이 API는 (수종, 수고, 흉고직경) 모든 조합에 대해 데이터를 주지 않음.
샘플 (강원지방소나무, 6.0m, 5.0cm → 0.0080) 외 다양한 조합은 빈 응답.
→ 정확한 입력 표기 찾기 필요. 또는 모듈 B의 fallback 으로만 사용.
→ 주력은 임분수확표 PDF (camelot 파싱) 으로 가야 함.
"""

"""
growth_api.py
data.go.kr 산림청 국립산림과학원 산림생장정보 API
입목수간재적(stem volume) 조회

[용도]
모듈 B에서 특정 임야의 (수종, 수고, 흉고직경)을 입력하면
정확한 m³ 단위 수간재적을 반환받음.
임분수확표 PDF의 보완재 — *개별 정밀 조회*에 사용.

[모듈 B 통합]
- PDF 임분수확표 → 임분 평균 forecast
- 이 API → 특정 나무 정밀 조회 + PDF 검증
"""

import os
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

SERVICE_KEY = os.getenv("DATA_GO_KR_KEY")

# 요청주소 (페이지에서 확인한 정확한 URL)
URL = "http://apis.data.go.kr/1400377/forestGrowthInfoService/getWoodStemVolumInfoList"


def fetch_stem_volume(
    kind_of_tree: str,
    tree_height: float,
    breast_diameter: float,
):
    """
    수종·수고·흉고직경 입력 → 수간재적(m³) 반환.
    
    Args:
        kind_of_tree: 수종명 (예: "강원지방소나무", "잣나무", "낙엽송")
        tree_height: 수고 (m)
        breast_diameter: 흉고직경 (cm)
    
    Returns:
        dict {resultCode, resultMsg, resultvalue}
    """
    params = {
        "ServiceKey": SERVICE_KEY,
        "_type": "json",
        "KindOfTree": kind_of_tree,
        "TreeHeight": str(tree_height),
        "BreastHeightDiameter": str(breast_diameter),
    }
    
    response = requests.get(URL, params=params, timeout=10)
    
    if response.status_code != 200:
        print(f"❌ HTTP {response.status_code}: {response.text[:300]}")
        return None
    
    try:
        data = response.json()
        # 응답 구조 확인: 보통 response.body.items.item 형태
        body = data.get("response", {}).get("body", {})
        items = body.get("items", {})
        if isinstance(items, dict):
            item = items.get("item")
            if isinstance(item, list) and item:
                return item[0]
            elif isinstance(item, dict):
                return item
        return body  # fallback
    except Exception as e:
        print(f"⚠️ 파싱 오류: {e}")
        print(f"   원본 응답 (처음 500자): {response.text[:500]}")
        return None


def test_multiple_trees():
    """
    여러 수종·크기 조합으로 API 테스트.
    """
    test_cases = [
        ("강원지방소나무", 6.0, 5.0),
        ("강원지방소나무", 15.0, 20.0),
        ("강원지방소나무", 25.0, 35.0),
        ("잣나무", 10.0, 15.0),
        ("낙엽송", 20.0, 25.0),
        ("편백", 15.0, 20.0),
    ]
    
    results = []
    for tree, h, d in test_cases:
        print(f"\n🌳 {tree}  키 {h}m  직경 {d}cm")
        result = fetch_stem_volume(tree, h, d)
        if result:
            print(f"   결과코드: {result.get('resultCode', '?')}")
            print(f"   메시지:   {result.get('resultMsg', '?')}")
            volume = result.get("resultvalue", "?")
            print(f"   📊 수간재적: {volume} m³")
            results.append({
                "수종": tree,
                "수고(m)": h,
                "흉고직경(cm)": d,
                "수간재적(m³)": volume,
                "메시지": result.get("resultMsg"),
            })
        else:
            print(f"   ❌ 결과 없음")
    
    return results


if __name__ == "__main__":
    print("🌐 산림생장정보 API — 입목수간재적 조회")
    print(f"   엔드포인트: {URL}")
    print(f"   서비스키: ...{SERVICE_KEY[-4:] if SERVICE_KEY else 'None'}")
    print()
    
    results = test_multiple_trees()
    
    if results:
        print()
        print("=" * 60)
        print("📋 결과 요약")
        print("=" * 60)
        df = pd.DataFrame(results)
        print(df.to_string(index=False))
        
        # CSV로 저장
        out_path = ROOT / "module_bd" / "data" / "raw" / "growth_test.csv"
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print()
        print(f"💾 저장: {out_path.relative_to(ROOT)}")