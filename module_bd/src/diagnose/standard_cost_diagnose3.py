"""
standard_cost_diagnose3.py
산림사업 표준품셈 — 가이드 §7.1 5개 변수 *진짜 페이지* 정밀 매핑.

Step 2 진단 결과:
- 노임 (1-2-5): p.24
- 운반 (1-2-7): p.24-25 (자재 운반)
- 조림 작업: p.52 (제3장), p.71 (파종조림)
- 트럭운반: p.156, 162 (건설공사용)

이 Step 3 진단:
- 벌채 작업 단가 (진짜 작업표) 찾기
- 집재 작업 단가 (가선집재·삭도집재 등) 찾기
- 조림 단가 (식재 작업 단가) 찾기
- 보육 (간벌) 단가 찾기
"""

import pdfplumber
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = ROOT / "module_bd" / "data" / "raw" / "standard_cost" / "산림사업_표준품셈_2025-82호.pdf"


def find_pages_with_keywords(pdf, keyword_pairs, max_pages=10):
    """
    여러 키워드 *조합* 으로 페이지 찾기.
    keyword_pairs: [("벌채", "기계"), ("집재", "가선"), ...]
    """
    results = {}
    
    for keywords in keyword_pairs:
        pages_found = []
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if all(kw in text for kw in keywords):
                pages_found.append(i + 1)
                if len(pages_found) >= max_pages:
                    pages_found.append("...")
                    break
        
        key = " + ".join(keywords)
        results[key] = pages_found
    
    return results


def show_page_brief(pdf, page_num, max_lines=20):
    """페이지 간단 미리보기."""
    page = pdf.pages[page_num - 1]
    text = page.extract_text() or ""
    print(f"\n{'='*70}")
    print(f"📄 p.{page_num}")
    print('='*70)
    
    lines = text.split("\n")
    for i, line in enumerate(lines[:max_lines], 1):
        print(f"   {i:>3}: {line[:85]}")


def diagnose():
    print(f"📊 PDF 진단 Step 3: 가이드 §7.1 5개 변수 정밀 매핑")
    
    with pdfplumber.open(PDF_PATH) as pdf:
        # 단계 1: 핵심 작업별 페이지 찾기
        print("\n" + "=" * 70)
        print("🔍 핵심 작업별 페이지 찾기 (키워드 조합)")
        print("=" * 70)
        
        keyword_pairs = [
            # 벌채 작업 (수확 벌채 = harvest)
            ("벌목", "기계톱"),
            ("수확벌채", "인력"),
            ("간벌", "벌목부"),
            ("벌채", "보통인부"),
            
            # 집재 (skidding)
            ("집재", "가선"),
            ("집재", "트랙터"),
            ("집재", "임내"),
            
            # 운반 (transport)
            ("운반", "원목"),
            ("덤프트럭", "원목"),
            
            # 조림 (regen)
            ("식재", "묘목"),
            ("나무심기", "보통인부"),
            ("조림", "ha당"),
            
            # 보육
            ("풀베기", "전면"),
            ("어린나무", "가꾸기"),
            
            # 일위대가 (또는 종합단가)
            ("일위대가",),
            ("표준품", "단가"),
        ]
        
        results = find_pages_with_keywords(pdf, keyword_pairs, max_pages=5)
        
        for key, pages in results.items():
            pages_str = ", ".join(str(p) for p in pages[:5])
            print(f"   '{key}': p.{pages_str if pages else '발견 안 됨'}")
        
        # 단계 2: 가장 유망한 페이지 자세히 보기
        print("\n" + "=" * 70)
        print("📄 유망 페이지 미리보기")
        print("=" * 70)
        
        # 자동 결정 — '벌목 + 기계톱' 첫 페이지
        priority_pages = []
        for key in ["벌목 + 기계톱", "집재 + 가선", "식재 + 묘목", "풀베기 + 전면"]:
            if results.get(key) and isinstance(results[key][0], int):
                priority_pages.append(results[key][0])
        
        # 중복 제거 + 정렬
        priority_pages = sorted(set(priority_pages))[:6]
        
        for p in priority_pages:
            if p <= len(pdf.pages):
                show_page_brief(pdf, p, max_lines=35)
    
    print()
    print("=" * 70)
    print("✅ Step 3 진단 완료")
    print("=" * 70)


if __name__ == "__main__":
    diagnose()