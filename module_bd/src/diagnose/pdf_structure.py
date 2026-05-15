"""
pdf_structure.py
PDF 페이지 191-215 (Ⅶ. 임분수확표) 안에서 수종별 시작 페이지 찾기.
"""

import pdfplumber
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = ROOT / "module_bd" / "data" / "raw" / "yield_table_2014.pdf"

# 임분수확표 수록 수종 (가이드 + 입목수간재적표 비교)
SPECIES = [
    "강원지방소나무", "중부지방소나무", "리기다소나무",
    "잣나무", "낙엽송", "삼나무", "편백",
    "상수리나무", "굴참나무", "신갈나무",
    "자작나무", "백합나무",
    # 입목수간재적표 있던 다른 수종 — 임분수확표 없을 수도
    "해송", "이태리포플러",
]


def scan_yield_section():
    """Ⅶ. 임분수확표 (p.191-215) 각 페이지의 첫 5줄 + 수종명 매칭."""
    
    print(f"📄 PDF: {PDF_PATH.name}")
    print(f"🎯 Ⅶ. 임분수확표 (p.191-215) 수종별 시작 페이지 찾기")
    print()
    
    species_pages = {}
    
    with pdfplumber.open(PDF_PATH) as pdf:
        for page_num in range(191, 216):  # 191 ~ 215
            page = pdf.pages[page_num - 1]
            text = page.extract_text() or ""
            
            top_lines = [l.strip() for l in text.split("\n")[:5] if l.strip()]
            
            print(f"--- PDF p.{page_num} ---")
            for line in top_lines:
                # 150자 제한
                line_short = line[:120]
                print(f"   {line_short}")
                
                # 수종 이름 매칭 (예: "1. 강원지방소나무")
                for sp in SPECIES:
                    if sp in line and len(line) < 50:  # 제목 줄만
                        if sp not in species_pages:
                            species_pages[sp] = page_num
            print()
    
    print("=" * 60)
    print("📋 수종별 시작 페이지 (Ⅶ. 임분수확표)")
    print("=" * 60)
    for sp, page in sorted(species_pages.items(), key=lambda x: x[1]):
        print(f"   {sp:>10} : PDF p.{page}")
    
    # 누락 수종
    missing = [sp for sp in SPECIES if sp not in species_pages]
    if missing:
        print()
        print(f"⚠️  매칭 안 된 수종: {missing}")


if __name__ == "__main__":
    scan_yield_section()