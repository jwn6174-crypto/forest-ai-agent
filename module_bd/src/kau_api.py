"""
kau_api.py
data.go.kr 금융위 OpenAPI로 한국 탄소시장(KAU/KCU/KOC) 일별 시세 가져오기

[사용]
1. 단일 날짜 조회:    python kau_api.py
2. 다른 모듈에서:     from kau_api import fetch_kau_price, save_to_csv
"""

import os
import pandas as pd
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# 경로 설정: 이 파일 → src → module_bd → forest-ai-agent → .env
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

SERVICE_KEY = os.getenv("DATA_GO_KR_KEY")

# data.go.kr 금융위원회 일반상품시세정보 — 배출권시세 엔드포인트
URL = (
    "https://apis.data.go.kr/1160100/service/GetGeneralProductInfoService/"
    "getCertifiedEmissionReductionPriceInfo"
)

# 데이터 저장 경로
DATA_DIR = ROOT / "module_bd" / "data" / "raw" / "kau_daily"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def fetch_kau_price(date: str):
    """
    특정 날짜의 KAU/KCU/KOC 전체 시세 가져오기.
    
    Args:
        date: 'YYYYMMDD' 형식
    
    Returns:
        list of dict — 종목별 시가/종가/거래량
    """
    params = {
        "serviceKey": SERVICE_KEY,
        "numOfRows": "50",
        "pageNo": "1",
        "resultType": "json",
        "basDt": date,
    }
    
    response = requests.get(URL, params=params, timeout=10)
    
    if response.status_code != 200:
        return []
    
    try:
        items = response.json()["response"]["body"]["items"]["item"]
        if isinstance(items, dict):
            items = [items]
        return items
    except (KeyError, TypeError):
        return []


def find_latest_data(max_days_back: int = 14):
    """
    가장 최근의 데이터가 있는 날짜 자동 탐색.
    영업일 1일 + 오후 1시 후 업데이트 정책 반영.
    """
    for days_back in range(2, max_days_back + 1):
        date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")
        items = fetch_kau_price(date)
        if items:
            return date, items
    return None, []


def save_to_csv(items: list, date: str) -> Path:
    """
    KAU 일별 데이터를 CSV로 저장.
    파일명: kau_YYYYMMDD.csv
    """
    df = pd.DataFrame(items)
    
    # 핵심 컬럼만 추출하고 한국어로 정리
    keep = {
        "basDt": "기준일자",
        "itmsNm": "종목명",
        "mkp": "시가",
        "hipr": "고가",
        "lopr": "저가",
        "clpr": "종가",
        "trqu": "거래량",
        "trPrc": "거래대금",
    }
    
    df = df[[c for c in keep if c in df.columns]].rename(columns=keep)
    
    # 숫자형 변환
    for col in ["시가", "고가", "저가", "종가", "거래량", "거래대금"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    output_path = DATA_DIR / f"kau_{date}.csv"
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return output_path


def print_summary(items: list, date: str):
    """콘솔에 종목별 가격 요약 출력."""
    print(f"\n📊 {date} KAU/KCU/KOC 시세 요약")
    print("=" * 60)
    
    # 종목 카테고리 분류
    kau = [it for it in items if it["itmsNm"].startswith("KAU")]
    kcu = [it for it in items if it["itmsNm"].startswith("KCU")]
    koc = [it for it in items if it["itmsNm"].startswith("KOC")]
    intl = [it for it in items if it["itmsNm"].startswith("i-")]
    
    for label, group in [
        ("KAU (할당배출권)", kau),
        ("KCU (이월·차감)", kcu),
        ("KOC (오프셋 - 산림 포함!)", koc),
        ("i-KCU/i-KOC (국제)", intl),
    ]:
        if group:
            print(f"\n  {label}:")
            for it in group:
                volume = int(it.get("trqu", 0) or 0)
                trade_mark = "✅" if volume > 0 else "  "
                print(f"   {trade_mark} {it['itmsNm']:<14}  종가: {it['clpr']:>7}원  거래량: {volume:>7,}")
    
    print()


if __name__ == "__main__":
    print("🌐 한국 탄소시장 시세 조회 중...")
    print(f"   API: getCertifiedEmissionReductionPriceInfo")
    print(f"   저장 폴더: {DATA_DIR.relative_to(ROOT)}")
    
    date, items = find_latest_data()
    
    if not items:
        print("\n⚠️  최근 2주 데이터 없음. API 또는 정책 문제 의심.")
    else:
        print_summary(items, date)
        csv_path = save_to_csv(items, date)
        print(f"💾 저장 완료: {csv_path.relative_to(ROOT)}")
        print(f"   {len(items)}개 종목, {csv_path.stat().st_size:,} bytes")