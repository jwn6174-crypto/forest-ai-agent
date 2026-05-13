"""
fps_diagnose.py
임산물생생도매가격시스템 (fps.kofpi.or.kr) 진단.

이게 KOFPI 본진. 일별·수종별·등급별 가격 데이터 가능성.
"""

import requests
from bs4 import BeautifulSoup
import re

# 다양한 가격 페이지
URLS = {
    "원목_시장가격": "https://fps.kofpi.or.kr/fnt/price/wood/market/list.do",
    "원목_전체동향": "https://fps.kofpi.or.kr/fnt/price/wood/total/list.do",
    "목재제품": "https://fps.kofpi.or.kr/fnt/price/wood/01/stats.do",
    "임산물_지역별": "https://fps.kofpi.or.kr/fnt/price/forest/area/list.do",
    "메인": "https://fps.kofpi.or.kr/main.do",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (research bot; Forest AI Agent contest project; "
                  "contact: nacave@kookmin.ac.kr)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


def diagnose_page(name, url):
    """한 페이지 진단."""
    print()
    print("=" * 70)
    print(f"📡 {name}")
    print(f"   URL: {url}")
    print("=" * 70)
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        r.encoding = "utf-8"
    except Exception as e:
        print(f"   ❌ 요청 실패: {type(e).__name__}: {e}")
        return
    
    print(f"   Status: {r.status_code}, 응답 크기: {len(r.text):,} 자")
    
    soup = BeautifulSoup(r.text, "lxml")
    
    # 표 분석
    tables = soup.find_all("table")
    print(f"   표: {len(tables)} 개")
    for i, t in enumerate(tables[:5]):
        cls = t.get("class", [])
        rows = t.find_all("tr")
        first_text = rows[0].get_text(strip=True)[:80] if rows else ""
        print(f"      표 {i}: class={cls}, 행={len(rows)}, 첫 행: {first_text}")
    
    # 6 등급 + 7 수종 키워드
    grades = ["특용재", "1등급", "2등급", "3등급", "원주재", "원료재"]
    species = ["소나무", "낙엽송", "잣나무", "리기다", "참나무", "편백", "삼나무"]
    
    grade_counts = {g: r.text.count(g) for g in grades}
    species_counts = {s: r.text.count(s) for s in species}
    
    print(f"   등급 키워드:")
    for g, c in grade_counts.items():
        if c > 0:
            print(f"      {g}: {c} 회")
    
    print(f"   수종 키워드:")
    for s, c in species_counts.items():
        if c > 0:
            print(f"      {s}: {c} 회")
    
    # 가격 패턴
    prices = re.findall(r"(\d{1,3}(?:,\d{3})+)\s*원", r.text)
    print(f"   가격값 (xx,xxx원): {len(prices)} 개")
    if prices[:5]:
        print(f"      샘플: {', '.join(prices[:5])}")
    
    # 폼 / select (검색·필터)
    selects = soup.find_all("select")
    print(f"   드롭다운(select): {len(selects)} 개")
    for s in selects[:5]:
        name = s.get("name", "?")
        options = [o.get_text(strip=True) for o in s.find_all("option")][:8]
        print(f"      name='{name}': {options}")
    
    # 다운로드 링크
    download_links = []
    for a in soup.find_all("a"):
        href = a.get("href", "") or ""
        text = a.get_text(strip=True)
        if any(kw in (href + text).lower() for kw in ["download", "엑셀", ".xls", ".csv", "다운로드"]):
            download_links.append((text[:30], href[:80]))
    if download_links:
        print(f"   📥 다운로드 링크 {len(download_links)} 개:")
        for t, h in download_links[:5]:
            print(f"      '{t}' → {h}")


if __name__ == "__main__":
    for name, url in URLS.items():
        diagnose_page(name, url)
    
    print()
    print("=" * 70)
    print("✅ fps.kofpi.or.kr 전체 진단 완료")
    print("=" * 70)