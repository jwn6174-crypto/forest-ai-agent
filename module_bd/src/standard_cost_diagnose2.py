"""
standard_cost_diagnose2.py
산림사업 표준품셈 PDF 의 가이드 §7.1 5개 변수 정확 위치 찾기.

진단 1 (standard_cost_diagnose.py) 결과:
- 벌채: p.30, 33, 56, 57, 71
- 집재: p.33 (할증), p.4 (목차)
- 트럭운반: p.156
- 조림: p.5, 10, 13 (제5장)
- 노임: p.23, 24, 27, 29
- 원목: p.25 (1-5 목재 원목 시가)

이 페이지들의 *진짜 내용* 자세히 확인.
"""

import pdfplumber
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = ROOT / "module_bd" / "data" / "raw" / "standard_cost" / "산림사업_표준품셈_2025-82호.pdf"


def show_page(pdf, page_num, max_lines=50):
    """페이지 텍스트 + 표 미리보기."""
    page = pdf.pages[page_num - 1]
    
    print(f"\n{'='*70}")
    print(f"📄 p.{page_num}")
    print('='*70)
    
    # 텍스트
    text = page.extract_text() or ""
    lines = text.split("\n")
    for i, line in enumerate(lines[:max_lines], 1):
        print(f"   {i:>3}: {line[:90]}")
    
    # 표
    tables = page.extract_tables()
    if tables:
        print(f"\n   📋 표 {len(tables)} 개 존재")
        for ti, table in enumerate(tables):
            print(f"\n   --- 표 {ti+1} ({len(table)} 행 × {len(table[0]) if table else 0} 열) ---")
            for row in table[:5]:  # 첫 5행만
                cells = [str(c)[:25] if c else "" for c in row]
                print(f"      | {' | '.join(cells)}")


def diagnose():
    print(f"📊 PDF 진단 Step 2: 가이드 §7.1 5개 변수 위치")
    
    with pdfplumber.open(PDF_PATH) as pdf:
        # 가이드 §7.1 5개 변수의 진짜 페이지 추정:
        # 1. harvest_unit_cost (벌채) → p.56-71 (벌채 단가표 추정)
        # 2. skidding_cost (집재) → 같은 영역
        # 3. transport_cost (트럭운반) → p.156, 162, 224
        # 4. regen_cost (조림) → 제5장 p.52~
        # 5. 노임 (1-2-5) → p.23-24
        
        target_pages = [
            # 노임 (1-2-5)
            23, 24,
            # 원목 시가 (1-5)
            25,
            # 벌채 관련
            56, 71,
            # 트럭운반
            156, 162,
            # 조림 (제5장)
            52, 53,
        ]
        
        for p in target_pages:
            if p <= len(pdf.pages):
                show_page(pdf, p, max_lines=40)
    
    print()
    print("=" * 70)
    print("✅ 진단 완료")
    print("=" * 70)


if __name__ == "__main__":
    diagnose()