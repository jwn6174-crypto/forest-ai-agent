"""
kofpi_diagnose.py
KOFPI 원목가격 페이지 진단 — 스크래핑 가능성 판단.

URL: https://www.kofpi.or.kr/info/imupStory/statistics_04.do
"""

import requests
from bs4 import BeautifulSoup
import re

URL = "https://www.kofpi.or.kr/info/imupStory/statistics_04.do"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (research bot; Forest AI Agent contest project; "
                  "contact: nacave@kookmin.ac.kr)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


def diagnose():
    """Phase 1: 페이지 기본 구조 진단"""
    print("=" * 60)
    print(f"📡 KOFPI 페이지 진단")
    print(f"   URL: {URL}")
    print("=" * 60)
    
    try:
        r = requests.get(URL, headers=HEADERS, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"❌ 요청 실패: {type(e).__name__}: {e}")
        return
    
    print(f"\n✅ Status: {r.status_code}")
    print(f"   Content-Type: {r.headers.get('Content-Type', 'N/A')}")
    print(f"   응답 크기: {len(r.text):,} 자")
    
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.text, "lxml")
    
    # 표 분석
    print()
    print("=" * 60)
    print("🔍 표(table) 분석")
    print("=" * 60)
    tables = soup.find_all("table")
    print(f"   총 {len(tables)} 개 표")
    for i, t in enumerate(tables):
        cls = t.get("class", [])
        rows = t.find_all("tr")
        first_text = rows[0].get_text(strip=True)[:80] if rows else ""
        print(f"   표 {i}: class={cls}, 행수={len(rows)}, 첫 행: {first_text}")


def find_prices():
    """Phase 2: 가격 데이터 위치 분석"""
    r = requests.get(URL, headers=HEADERS, timeout=30)
    r.encoding = "utf-8"
    text = r.text
    
    print()
    print("=" * 60)
    print("💰 가격 18개 → 컨텍스트 분석")
    print("=" * 60)
    
    for match in re.finditer(r"(\d{1,3}(?:,\d{3})+)\s*원", text):
        start = max(0, match.start() - 200)
        end = min(len(text), match.end() + 100)
        ctx = text[start:end]
        ctx_clean = re.sub(r"<[^>]+>", " ", ctx)
        ctx_clean = re.sub(r"\s+", " ", ctx_clean).strip()
        print(f"\n💰 {match.group(1)}원")
        print(f"   ...{ctx_clean[-250:]}...")


def find_species_urls():
    """Phase 3: 다른 수종 페이지 URL 찾기"""
    print()
    print("=" * 60)
    print("🔍 수종별 페이지 URL 검색")
    print("=" * 60)
    
    r = requests.get(URL, headers=HEADERS, timeout=30)
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.text, "lxml")
    
    target_species = ["소나무", "낙엽송", "잣나무", "리기다", "참나무", "편백", "삼나무"]
    
    # 1. 페이지 내 링크 검색
    print("\n[1] 페이지 내 수종 관련 링크")
    found_any = False
    for a in soup.find_all("a"):
        href = a.get("href", "")
        text = a.get_text(strip=True)
        for sp in target_species:
            if sp in text or sp in href:
                print(f"   '{text[:40]}' → {href[:80]}")
                found_any = True
                break
    if not found_any:
        print("   (아무 링크도 없음)")
    
    # 2. JavaScript 안의 수종 관련 패턴
    print("\n[2] JavaScript 안의 수종 관련 패턴")
    found_js = False
    for script in soup.find_all("script"):
        content = script.string or ""
        if not content:
            continue
        for sp in target_species:
            if sp in content:
                idx = content.find(sp)
                ctx = content[max(0, idx-100):idx+150]
                ctx_compact = re.sub(r"\s+", " ", ctx).strip()
                print(f"   '{sp}' 발견: ...{ctx_compact}...")
                found_js = True
    if not found_js:
        print("   (JavaScript 안에 수종명 없음)")
    
    # 3. URL 패턴 추측
    print("\n[3] statistics_04 변형 URL 패턴 추측")
    candidates = [
        "statistics_04_01.do", "statistics_04_02.do", "statistics_04_2.do",
        "statistics_05.do", "statistics_06.do", "statistics_07.do",
    ]
    for path in candidates:
        test_url = f"https://www.kofpi.or.kr/info/imupStory/{path}"
        try:
            r = requests.head(test_url, headers=HEADERS, timeout=10, allow_redirects=False)
            status = r.status_code
            print(f"   {path}: HTTP {status}")
        except Exception as e:
            print(f"   {path}: ❌ {type(e).__name__}")
    
    # 4. 폼/POST 파라미터 검색
    print("\n[4] form/POST 파라미터 검색")
    forms = soup.find_all("form")
    for i, f in enumerate(forms):
        action = f.get("action", "")
        method = f.get("method", "get")
        inputs = f.find_all(["input", "select"])
        print(f"   form {i}: action='{action}', method={method}")
        for inp in inputs:
            name = inp.get("name", "?")
            type_ = inp.get("type", inp.name)
            value = inp.get("value", "")[:30] if inp.get("value") else ""
            print(f"      {type_} name='{name}' value='{value}'")
    
    # 5. iframe / 외부 리소스
    print("\n[5] iframe / 외부 데이터 소스")
    iframes = soup.find_all("iframe")
    if iframes:
        for f in iframes:
            print(f"   iframe src: {f.get('src', '?')}")
    else:
        print("   (iframe 없음)")


if __name__ == "__main__":
    diagnose()
    find_prices()
    find_species_urls()
    print()
    print("=" * 60)
    print("✅ 전체 진단 완료")
    print("=" * 60)