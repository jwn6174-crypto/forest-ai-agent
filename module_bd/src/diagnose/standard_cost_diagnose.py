"""
standard_cost_diagnose.py
산림사업 표준품셈 PDF 구조 진단.

목적: 가이드 §7.1 의 cost_function() 에 필요한 진짜 값 추출 위치 파악.
- 노임 (1-2-5)
- 운반 (1-2-7)
- 경사도·이동거리 할증 (1-4-5, 1-4-6)
- 목재 원목 시가 (1-5)
- 제2장 작업별 단가 (벌채·집재·운반·조림)
"""

import pdfplumber
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = ROOT / "module_bd" / "data" / "raw" / "standard_cost" / "산림사업_표준품셈_2025-82호.pdf"


def diagnose():
    print("=" * 60)
    print(f"📊 PDF 진단: {PDF_PATH.name}")
    print("=" * 60)
    
    if not PDF_PATH.exists():
        print(f"❌ 파일 없음: {PDF_PATH}")
        return
    
    print(f"✅ 파일 크기: {PDF_PATH.stat().st_size:,} bytes")
    
    with pdfplumber.open(PDF_PATH) as pdf:
        print(f"   총 페이지: {len(pdf.pages)}")
        
        # 1. 핵심 키워드별 페이지 찾기
        print()
        print("=" * 60)
        print("🔍 핵심 키워드 검색 (가이드 §7.1 의 5개 변수)")
        print("=" * 60)
        
        keywords = [
            "벌채",           # harvest_unit_cost
            "집재",           # skidding
            "트럭운반", "트럭 운반",  # transport
            "조림",           # regen
            "노임",           # 노임 단가
            "원목",           # 목재 원목 시가
            "표준품 일위대가",  # 일위대가표 (단가 종합)
            "경사도",         # 할증
            "이동거리",       # 할증
        ]
        
        for kw in keywords:
            pages_with_kw = []
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                if kw in text:
                    pages_with_kw.append(i + 1)
                    if len(pages_with_kw) >= 5:  # 5개까지만
                        pages_with_kw.append("...")
                        break
            if pages_with_kw:
                pages_str = ", ".join(str(p) for p in pages_with_kw[:5])
                print(f"   '{kw}': p.{pages_str}")
            else:
                print(f"   '{kw}': 발견 안 됨")
        
        # 2. 페이지별 표 개수 + 첫 페이지 표 샘플
        print()
        print("=" * 60)
        print("📋 표 개수 분포 (페이지별)")
        print("=" * 60)
        
        table_counts = {}
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            if tables:
                table_counts[i + 1] = len(tables)
        
        print(f"   표 있는 페이지: {len(table_counts)} 개")
        print(f"   총 표 개수: {sum(table_counts.values())}")
        
        # 표가 많은 페이지 top 10
        top_pages = sorted(table_counts.items(), key=lambda x: -x[1])[:10]
        print(f"   표 많은 페이지 top 10:")
        for page_num, count in top_pages:
            print(f"      p.{page_num}: {count} 개")
        
        # 3. 샘플 페이지 — "벌채" 단가가 처음 나오는 페이지 확인
        print()
        print("=" * 60)
        print("📄 '벌채' 단가 첫 페이지 텍스트 샘플 (60줄)")
        print("=" * 60)
        
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if "벌채" in text and ("원" in text or "단가" in text or "노임" in text):
                print(f"\n📄 p.{i + 1} (벌채 + 가격 키워드):")
                lines = text.split("\n")
                for j, line in enumerate(lines[:30], 1):
                    print(f"   {j:>3}: {line[:80]}")
                break
        
        # 4. 목차 페이지 (보통 1-5 페이지)
        print()
        print("=" * 60)
        print("📚 PDF 첫 5 페이지 미리보기 (목차 영역)")
        print("=" * 60)
        
        for i in range(min(5, len(pdf.pages))):
            page = pdf.pages[i]
            text = page.extract_text() or ""
            print(f"\n--- p.{i + 1} ---")
            print(text[:500])
    
    print()
    print("=" * 60)
    print("✅ 진단 완료")
    print("=" * 60)


if __name__ == "__main__":
    diagnose()