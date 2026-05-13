"""
yield_table_parse.py
진짜 임분수확표 (Ⅶ. 임분수확표, PDF p.191-215) 파싱.

⭐ 이게 가이드가 요구하는 진짜 임분수확표:
- 11 수종 × SI 4단계 × 임령 ~15 단계
- 컬럼: 지위지수, 임령, 평균DBH, 우세목수고, 평균수고, 본수, 재적, MAI 등
- 모듈 B의 growth_predict(species, site_index, age_now, target_age) 의 데이터 소스

cf) yield_parse.py = 입목수간재적표 (Ⅱ장)
    - 컬럼: 흉고직경, 수고 → 재적
    - 모듈 B의 lookup_volume(species, dbh, height) 의 데이터 소스
"""

import camelot
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = ROOT / "module_bd" / "data" / "raw" / "yield_table_2014.pdf"
OUT_DIR = ROOT / "module_bd" / "data" / "interim"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# Ⅶ. 임분수확표 수종별 페이지 매핑 (검증 완료 2026-05-13)
YIELD_TABLE_PAGES = {
    "강원지방소나무":  [192, 193],
    "중부지방소나무":  [194, 195],
    "리기다소나무":   [196, 197, 198],
    "잣나무":         [199, 200],
    "낙엽송":         [201, 202, 203],
    "편백":          [204, 205],
    "상수리나무":     [206, 207],
    "굴참나무":      [208, 209],
    "신갈나무":      [210, 211],
    "자작나무":      [212, 213],  # (잠정)
    "백합나무":      [214, 215],  # (잠정)
}

# 컬럼 인덱스 → 의미 (p.192/193 분석 결과)
COLUMN_MAP = {
    0: "지위지수",
    1: "임령(년)",
    2: "평균DBH(cm)",
    3: "단면적(m²/ha)",
    4: "평균수고(m)",
    5: "우세목수고(m)",
    6: "본수(본/ha)",
    7: "재적(m³/ha)",
    8: "정기평균생장량(m³/ha)",
    9: "정기평균생장률(%)",
    10: "연평균생장량(m³/ha/yr)",
}


def parse_yield_page(page: int) -> pd.DataFrame:
    """
    임분수확표 한 페이지 추출.
    
    표 모양: 보통 (~30, 11) — 행 0=헤더, 행 1+=데이터
    셀 형식: 개별 분리 (모자병원 후처리 불필요)
    
    Returns:
        DataFrame: 한 페이지의 데이터 (header 제외)
    """
    tables = camelot.read_pdf(str(PDF_PATH), pages=str(page), flavor="lattice")
    
    if tables.n == 0:
        print(f"   ⚠️  lattice 실패, stream 시도")
        tables = camelot.read_pdf(str(PDF_PATH), pages=str(page), flavor="stream")
        if tables.n == 0:
            raise ValueError(f"페이지 {page}: 표 추출 불가")
    
    # 가장 큰 표 선택 (헤더 제외, 본문만)
    df_raw = max((t.df for t in tables), key=lambda d: d.size)
    
    # 행 0 = 헤더 (스킵). 행 1+ = 데이터
    data_rows = []
    for r in range(1, df_raw.shape[0]):
        row_values = []
        skip_row = False
        for c in range(min(11, df_raw.shape[1])):
            cell = df_raw.iloc[r, c]
            if not isinstance(cell, str):
                row_values.append(None)
                continue
            cell = cell.strip()
            if not cell:
                row_values.append(None)
                continue
            # 숫자 변환 (쉼표 제거: "6,815" → 6815)
            try:
                val = float(cell.replace(",", ""))
                row_values.append(val)
            except ValueError:
                # 숫자가 아니면 텍스트 그대로 (헤더 잔재 가능성)
                row_values.append(None)
                skip_row = True
                break
        
        if not skip_row and any(v is not None for v in row_values):
            data_rows.append(row_values)
    
    df = pd.DataFrame(data_rows, columns=[COLUMN_MAP[c] for c in range(11)])
    return df


def parse_species(species: str) -> pd.DataFrame:
    """수종 하나의 모든 페이지 결합."""
    pages = YIELD_TABLE_PAGES[species]
    print(f"🌲 {species} (PDF p.{pages})")
    
    all_data = []
    for page in pages:
        try:
            df = parse_yield_page(page)
            print(f"   p.{page}: {len(df)} 행")
            all_data.append(df)
        except Exception as e:
            print(f"   ❌ p.{page}: {type(e).__name__}: {e}")
    
    if not all_data:
        return pd.DataFrame()
    
    combined = pd.concat(all_data, ignore_index=True)
    combined["수종"] = species
    return combined


if __name__ == "__main__":
    print(f"📄 PDF: {PDF_PATH.name}")
    print(f"🎯 Ⅶ. 임분수확표 11 수종 일괄 처리")
    print()
    
    results = {}
    failures = []
    
    for species in YIELD_TABLE_PAGES:
        print(f"\n{'=' * 60}")
        try:
            df = parse_species(species)
            if df.empty:
                print(f"   ❌ {species}: 빈 데이터")
                failures.append(species)
                continue
            results[species] = df
            n_si = df["지위지수"].nunique()
            n_age = df["임령(년)"].nunique()
            n_rows = len(df)
            print(f"   ✅ {species}: {n_rows} 행, SI {n_si}단계, 임령 {n_age} 단계")
        except Exception as e:
            print(f"   ❌ {species}: {type(e).__name__}: {e}")
            failures.append(species)
    
    print()
    print("=" * 60)
    print(f"📊 처리 결과: {len(results)} 성공 / {len(failures)} 실패")
    if failures:
        print(f"   실패: {failures}")
    print("=" * 60)
    
    # 통합 DataFrame 생성
    if results:
        all_df = pd.concat(results.values(), ignore_index=True)
        all_df = all_df[
            ["수종", "지위지수", "임령(년)", "평균DBH(cm)", "단면적(m²/ha)",
             "평균수고(m)", "우세목수고(m)", "본수(본/ha)", "재적(m³/ha)",
             "정기평균생장량(m³/ha)", "정기평균생장률(%)", "연평균생장량(m³/ha/yr)"]
        ]
        
        # 통계
        print()
        print("📈 통합 데이터 통계")
        print(f"   총 {len(all_df):,} 행")
        print(f"   수종 {all_df['수종'].nunique()} 개")
        print(f"   재적 범위: {all_df['재적(m³/ha)'].min():.1f} ~ "
              f"{all_df['재적(m³/ha)'].max():.1f} m³/ha")
        
        # 수종별 요약
        print()
        print("수종별 요약:")
        summary = all_df.groupby("수종").agg(
            행수=("임령(년)", "count"),
            SI개수=("지위지수", "nunique"),
            임령_최소=("임령(년)", "min"),
            임령_최대=("임령(년)", "max"),
            재적_최대=("재적(m³/ha)", "max"),
        )
        print(summary.to_string())
        
        # 저장
        out_parquet = OUT_DIR / "yield_table_stand.parquet"
        all_df.to_parquet(out_parquet)
        print(f"\n💾 {out_parquet.relative_to(ROOT)}")
        
        # 수종별 CSV
        for species, df in results.items():
            out_csv = OUT_DIR / f"yield_stand_{species}.csv"
            df.to_csv(out_csv, encoding="utf-8-sig", index=False)
        print(f"💾 수종별 CSV {len(results)}개")
    
    print()
    print("=" * 60)
    print("✅ 진짜 임분수확표 일괄 처리 완료")
    print("=" * 60)