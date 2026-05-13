"""
yield_parse_small.py
작은 표 3개 (해송 p.30, 삼나무 p.56, 이태리포플러 p.102) 정렬 수정.
camelot 대신 pdfplumber 로 텍스트 직접 추출 → 행별 파싱.

작은 표 특징:
- 흉고직경 4-30cm (27 rows)
- 수고 6-20m (DBH 8개)
- 각 행마다 값 개수 다름 (왼쪽 삼각형 비어있음)
- camelot이 빈 셀 정렬 어렵게 만듦
"""

import pdfplumber
import pandas as pd
import numpy as np
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = ROOT / "module_bd" / "data" / "raw" / "yield_table_2014.pdf"
OUT_DIR = ROOT / "module_bd" / "data" / "interim"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 작은 표 페이지 매핑
SMALL_TABLES = {
    "해송_수피포함": 30,
    "삼나무_수피포함": 56,
    "이태리포플러_수피포함": 102,
}

# 작은 표 공통 구조
DBHS = list(range(6, 21, 2))         # 흉고직경 6, 8, 10, ..., 20 (8개)
HEIGHTS = list(range(4, 31))         # 수고 4, 5, 6, ..., 30 (27개)


def parse_small_table(page_num: int) -> pd.DataFrame:
    """
    pdfplumber 로 페이지 텍스트 추출 → 행별 파싱.
    
    각 행 형식: "수고 재적1 재적2 재적3 ..."
    예: "4 0.0065 0.0112 0.0191"  ← 수고 4m, DBH 6/8/10에만 값
    """
    with pdfplumber.open(PDF_PATH) as pdf:
        page = pdf.pages[page_num - 1]
        text = page.extract_text() or ""
    
    # 27 × 8 빈 DataFrame
    df = pd.DataFrame(
        index=HEIGHTS,
        columns=DBHS,
        dtype=float,
    )
    df.index.name = "수고(m)"
    df.columns.name = "흉고직경(cm)"
    
    # 줄별로 처리
    n_filled = 0
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        
        # 줄 시작이 숫자 (수고) 인지 확인
        tokens = line.split()
        if not tokens or not tokens[0].isdigit():
            continue
        
        height = int(tokens[0])
        if height not in HEIGHTS:
            continue  # 다른 페이지 노이즈 무시
        
        # 나머지 토큰 = 재적 값들
        values = []
        for tok in tokens[1:]:
            try:
                values.append(float(tok))
            except ValueError:
                pass
        
        if not values:
            continue
        
        # DBH 6cm 부터 *왼쪽 정렬* 로 채우기
        # (작은 수고일수록 적은 DBH만 값 있음 — 좌상단부터 채우는 게 PDF 패턴)
        for i, v in enumerate(values):
            if i < len(DBHS):
                df.at[height, DBHS[i]] = v
                n_filled += 1
    
    return df, n_filled


if __name__ == "__main__":
    print(f"📄 PDF: {PDF_PATH.name}")
    print(f"🎯 작은 표 3개 pdfplumber로 재추출")
    print()
    
    for key, page in SMALL_TABLES.items():
        print(f"\n🌲 {key} (PDF p.{page})")
        df, n_filled = parse_small_table(page)
        
        # transpose: 수고 행 × 흉고직경 열 → 원본 형식 (흉고직경 행 × 수고 열)
        df_t = df.T
        df_t.index.name = "흉고직경(cm)"
        df_t.columns.name = "수고(m)"
        
        n_total = df.size  # 27 × 8 = 216
        n_nan = df.isna().sum().sum()
        n_values = n_total - n_nan
        
        print(f"   채운 값: {n_filled}개")
        print(f"   매트릭스: {df.shape}")
        print(f"   값 {n_values}개 / NaN {n_nan}개 (총 {n_total})")
        
        # 처음 8행 미리보기
        print(f"\n   처음 8행 미리보기:")
        print(df_t.iloc[:8].to_string())
        
        # 저장
        out_csv = OUT_DIR / f"yield_{key}.csv"
        df_t.to_csv(out_csv, encoding="utf-8-sig")
        print(f"   💾 {out_csv.relative_to(ROOT)}")
    
    print()
    print("=" * 60)
    print("✅ 작은 표 3개 재추출 완료")
    print("   다음: 통합 parquet 재생성으로 yield_table_partial.parquet 갱신")