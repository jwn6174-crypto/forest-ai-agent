"""
cell_debug.py
camelot이 페이지 22 같은 문제 페이지에서 셀을 어떻게 나누는지 직접 본다.
"""

import camelot
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = ROOT / "module_bd" / "data" / "raw" / "yield_table_2014.pdf"

# 작은 표 케이스 (수종 작아서 부분 손실)
PAGES = [
    (30, "해송 수피포함 (123/216)"),
    (56, "삼나무 수피포함 (134/216)"),
    (102, "이태리포플러 수피포함 (156/216)"),
]

for page, label in PAGES:
    print(f"\n{'#' * 70}")
    print(f"# 페이지 {page} — {label}")
    print(f"{'#' * 70}")
    
    tables = camelot.read_pdf(str(PDF_PATH), pages=str(page), flavor="lattice")
    
    if tables.n == 0:
        print(f"  ❌ 표 없음")
        continue
    
    df = tables[0].df
    print(f"  표 모양: {df.shape}")
    print(f"  정확도: {tables[0].accuracy:.1f}%")
    print()
    
    # 각 셀 내용 출력
    for r in range(df.shape[0]):
        for c in range(df.shape[1]):
            cell = df.iloc[r, c]
            if not isinstance(cell, str):
                continue
            preview = cell.strip()[:100].replace("\n", " ⏎ ")
            n_lines = cell.count("\n") + 1 if cell.strip() else 0
            print(f"  [{r},{c}] ({n_lines}줄, {len(cell)}자): {preview}")