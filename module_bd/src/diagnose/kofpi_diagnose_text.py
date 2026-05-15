"""
kofpi_diagnose_text.py
KOFPI PDF 요약표의 *실제 텍스트 줄 순서* 확인.
"""

import pdfplumber
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = ROOT / "module_bd" / "data" / "raw" / "kofpi_reports" / "2025년_3분기_원목시장가격조사_보고서.pdf"


def diagnose():
    with pdfplumber.open(PDF_PATH) as pdf:
        # 페이지 4 (0-indexed) = PDF p.5
        text = pdf.pages[4].extract_text()
    
    print("=" * 60)
    print(f"📄 {PDF_PATH.name} — PDF p.5 텍스트")
    print("=" * 60)
    
    for i, line in enumerate(text.split("\n"), 1):
        print(f"{i:>3}: [{line}]")


if __name__ == "__main__":
    diagnose()