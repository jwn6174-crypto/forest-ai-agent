"""
standard_cost_diagnose4.py
산림사업 표준품셈 — Step 4 정밀 추출 위치 확인.

Step 3 결과로 *진짜 단가 페이지* 정확 위치 파악:
- p.59: 벌목 단가 (단목 20.17 / 전간목 25.5 / 전목 40.34 m³/인일)
- p.18, 211: 일위대가 (통합 단가표 가능성)
- p.41, 48: 집재 트랙터 (skidding)
- p.71-73: 식재·조림 (regen)
- p.91: 풀베기·맹아제거 (보육)

이 Step 4:
- 각 핵심 페이지의 *완전 텍스트* 추출
- 표 *전체 행* 확인
- 단가 구조 *완전 이해*
"""

import pdfplumber
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = ROOT / "module_bd" / "data" / "raw" / "standard_cost" / "산림사업_표준품셈_2025-82호.pdf"


def show_full_page(pdf, page_num):
    """페이지 *전체 텍스트 + 표* 보기."""
    page = pdf.pages[page_num - 1]
    
    print(f"\n{'='*70}")
    print(f"📄 p.{page_num} — 완전 텍스트")
    print('='*70)
    
    text = page.extract_text() or ""
    print(text)
    
    tables = page.extract_tables()
    if tables:
        print(f"\n📋 표 {len(tables)} 개")
        for ti, table in enumerate(tables):
            print(f"\n--- 표 {ti+1} ---")
            for row in table:
                cells = [str(c)[:40].replace("\n", " ") if c else "" for c in row]
                print(f"   | {' | '.join(cells)}")


def diagnose():
    print(f"📊 PDF 진단 Step 4: 핵심 페이지 완전 추출")
    
    with pdfplumber.open(PDF_PATH) as pdf:
        # 가장 핵심 페이지들
        critical_pages = [
            18,      # 일위대가 (통합?)
            41,      # 집재 트랙터
            48,      # 집재 임내
            59,      # 벌목 단가 ⭐ 확실
            60,      # 벌목 단가 계속?
            71,      # 파종조림
            73,      # 나무심기
            91,      # 풀베기
            211,     # 일위대가 (제3장 어딘가)
            223,     # 간벌 + 벌목부
        ]
        
        for p in critical_pages:
            if p <= len(pdf.pages):
                show_full_page(pdf, p)
    
    print()
    print("=" * 70)
    print("✅ Step 4 진단 완료")
    print("=" * 70)


if __name__ == "__main__":
    diagnose()