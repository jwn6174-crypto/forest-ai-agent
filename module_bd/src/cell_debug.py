"""
cell_debug.py
페이지 30 (해송) 의 [1,1] 셀 전체 내용 출력 → 진짜 패턴 파악
"""

import camelot
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = ROOT / "module_bd" / "data" / "raw" / "yield_table_2014.pdf"

tables = camelot.read_pdf(str(PDF_PATH), pages="30", flavor="lattice")
df = tables[0].df

print(f"표 모양: {df.shape}\n")

# [1,1] 셀 전체 내용 — 모든 줄 그대로
cell = df.iloc[1, 1]
print(f"[1,1] 셀 — 총 {len(cell)}자, {cell.count(chr(10)) + 1}줄")
print("=" * 60)
for i, line in enumerate(cell.split("\n"), 1):
    # 줄 번호 + 길이 + 내용 (전각공백 시각화)
    visualized = line.replace("\u3000", "[전각]").replace(" ", "·")
    print(f"  {i:>3}: ({len(line):>3}자) [{visualized}]")