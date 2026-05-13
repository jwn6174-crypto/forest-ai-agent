"""
cell_debug.py
페이지의 셀 구조를 진단한다. 진짜 패턴을 보고 파서를 만들기 위한 도구.
"""

import camelot
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = ROOT / "module_bd" / "data" / "raw" / "yield_table_2014.pdf"

# 진단할 페이지 목록 — 필요에 따라 수정
PAGES = [
    (91, "자작나무 둘째 (수고 28-50m, 590/598 - NaN 8개)"),
]


for page, label in PAGES:
    print(f"\n{'#' * 70}")
    print(f"# 페이지 {page} — {label}")
    print(f"{'#' * 70}")
    
    tables = camelot.read_pdf(str(PDF_PATH), pages=str(page), flavor="lattice")
    
    if tables.n == 0:
        print(f"  ❌ lattice 로 표 못 찾음. stream 시도...")
        tables = camelot.read_pdf(str(PDF_PATH), pages=str(page), flavor="stream")
        if tables.n == 0:
            print(f"  ❌ stream 도 실패. 표 인식 불가.")
            continue
        else:
            print(f"  ⚠️  stream 으로 인식됨")
    
    df = tables[0].df
    print(f"  표 모양: {df.shape}")
    print(f"  정확도: {tables[0].accuracy:.1f}%")
    print()
    
    # 모든 셀의 내용 출력
    for r in range(df.shape[0]):
        for c in range(df.shape[1]):
            cell = df.iloc[r, c]
            if not isinstance(cell, str):
                continue
            n_lines = cell.count("\n") + 1 if cell.strip() else 0
            print(f"\n  [{r},{c}] — {n_lines}줄, {len(cell)}자")
            for i, line in enumerate(cell.split("\n"), 1):
                visualized = line.replace("\u3000", "[전각]").replace(" ", "·")
                if len(visualized) > 150:
                    visualized = visualized[:150] + "..."
                print(f"     {i:>3}: ({len(line):>3}자) [{visualized}]")