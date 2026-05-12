"""
page_debug.py
임분수확표 PDF의 11개 문제 페이지 전후 텍스트 확인.
진짜 표가 어디 있는지 진단.
"""

import pdfplumber
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = ROOT / "module_bd" / "data" / "raw" / "yield_table_2014.pdf"

# 11개 문제 페이지 (재적 31/372 또는 작은 표 케이스)
PROBLEM_PAGES = {
    "중부지방소나무_수피포함": 22,
    "중부지방소나무_수피제외": 26,
    "해송_수피포함": 30,
    "낙엽송_수피포함": 48,
    "낙엽송_수피제외": 52,
    "삼나무_수피포함": 56,
    "굴참나무_수피포함": 74,
    "굴참나무_수피제외": 78,
    "백합나무_수피포함": 94,
    "백합나무_수피제외": 98,
    "이태리포플러_수피포함": 102,
}


with pdfplumber.open(PDF_PATH) as pdf:
    for label, page_num in PROBLEM_PAGES.items():
        print(f"\n{'#' * 70}")
        print(f"# {label} — 시도한 페이지 {page_num}")
        print(f"# 전후 페이지 {page_num - 2} ~ {page_num + 2} 확인")
        print(f"{'#' * 70}")
        
        for offset in range(-2, 3):
            p = page_num + offset
            if p < 1 or p > len(pdf.pages):
                continue
            
            page = pdf.pages[p - 1]
            text = page.extract_text() or ""
            
            # 처음 200자만 (페이지 시작 부분)
            preview = text[:200].replace("\n", " | ")
            mark = " ⭐" if offset == 0 else "  "
            print(f"{mark} PDF p.{p}: {preview}")