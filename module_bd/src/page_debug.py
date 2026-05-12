"""
page_debug.py
임시 진단: 강원지방소나무 시작 페이지를 진짜로 찾기.
페이지 6-15 각각의 텍스트 첫 300자 출력 → 어디서 표 시작하는지 눈으로 확인.
"""

import pdfplumber
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = ROOT / "module_bd" / "data" / "raw" / "yield_table_2014.pdf"

with pdfplumber.open(PDF_PATH) as pdf:
    for page_num in range(6, 16):  # PDF 페이지 6-15
        page = pdf.pages[page_num - 1]  # 0-indexed
        text = page.extract_text() or "(empty)"
        
        print(f"\n{'=' * 60}")
        print(f"📄 PDF 페이지 {page_num}")
        print(f"{'=' * 60}")
        print(text[:400])
        print(f"   (전체 길이: {len(text)}자)")