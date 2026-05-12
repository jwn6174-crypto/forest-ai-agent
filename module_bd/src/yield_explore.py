"""
yield_explore.py
임분수확표 PDF의 구조를 탐색하는 도구.
본격 파싱(camelot) 전에 PDF의 페이지 수, 어떤 수종이 있는지,
표 구조가 어떻게 생겼는지 눈으로 확인.
"""

import pdfplumber
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = ROOT / "module_bd" / "data" / "raw" / "yield_table_2014.pdf"


def explore_pdf():
    """PDF 기본 정보 + 처음 몇 페이지 텍스트 확인."""
    
    print(f"📄 PDF 분석: {PDF_PATH.name}")
    print(f"   크기: {PDF_PATH.stat().st_size:,} bytes")
    print()
    
    with pdfplumber.open(PDF_PATH) as pdf:
        n_pages = len(pdf.pages)
        print(f"📊 총 페이지 수: {n_pages}")
        print()
        
        # 처음 5페이지 텍스트 미리보기
        print("=" * 60)
        print("📖 처음 5페이지 미리보기")
        print("=" * 60)
        
        for i in range(min(5, n_pages)):
            page = pdf.pages[i]
            text = page.extract_text() or ""
            print(f"\n--- 페이지 {i + 1} ---")
            print(text[:500])
            print(f"   (전체 길이: {len(text)}자)")
        
        # 수종 키워드 등장 페이지 찾기
        print()
        print("=" * 60)
        print("🔎 수종 키워드 등장 페이지 찾기")
        print("=" * 60)
        
        keywords = ["소나무", "잣나무", "낙엽송", "편백", "리기다", "참나무", "신갈"]
        
        for kw in keywords:
            found_pages = []
            for i in range(n_pages):
                page = pdf.pages[i]
                text = page.extract_text() or ""
                if kw in text:
                    found_pages.append(i + 1)
                    if len(found_pages) >= 3:
                        break
            
            if found_pages:
                print(f"   {kw}: 페이지 {found_pages[:3]}{'...' if len(found_pages) >= 3 else ''}")
            else:
                print(f"   {kw}: 못 찾음")
        
        # 마지막 페이지 미리보기
        print()
        print("=" * 60)
        print(f"📖 마지막 페이지 (#{n_pages}) 미리보기")
        print("=" * 60)
        last_page = pdf.pages[-1]
        text = last_page.extract_text() or ""
        print(text[:500])


def find_yield_table_pages():
    """
    임분수확표 본격 데이터가 있는 페이지 추정.
    '임령', '본수', '재적' 같은 표 헤더가 있는 페이지 찾기.
    """
    print()
    print("=" * 60)
    print("🎯 임분수확표 본격 데이터 페이지 추정")
    print("=" * 60)
    
    table_keywords = ["임령", "본수", "재적", "DBH", "흉고직경"]
    
    with pdfplumber.open(PDF_PATH) as pdf:
        table_pages = []
        for i in range(len(pdf.pages)):
            page = pdf.pages[i]
            text = page.extract_text() or ""
            
            hits = sum(1 for kw in table_keywords if kw in text)
            if hits >= 2:
                table_pages.append((i + 1, hits))
        
        print(f"   표로 추정되는 페이지: {len(table_pages)}개")
        if table_pages:
            print(f"   첫 표 페이지: #{table_pages[0][0]}")
            print(f"   마지막 표 페이지: #{table_pages[-1][0]}")
            print()
            print(f"   처음 10개 표 페이지: {[p[0] for p in table_pages[:10]]}")


if __name__ == "__main__":
    if not PDF_PATH.exists():
        print(f"❌ PDF 없음: {PDF_PATH}")
        exit(1)
    
    explore_pdf()
    find_yield_table_pages()
    
    print()
    print("💡 다음 단계: 표 페이지 범위 확인 후 camelot으로 본격 파싱")