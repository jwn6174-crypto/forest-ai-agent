"""
yield_parse.py
임분수확표 PDF 의 표를 camelot 으로 추출하고 후처리하여
2차원 lookup table (흉고직경 × 수고 → 재적) 로 변환한다.

[발견]
- 페이지 14, 16, 20 등의 수간재적표는 camelot이 셀 단위로 분리 못 함
- 각 셀에 \n으로 구분된 다수 값이 들어있음
- 후처리로 분리해서 진짜 표로 재구성 가능
"""

import camelot
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = ROOT / "module_bd" / "data" / "raw" / "yield_table_2014.pdf"
OUT_DIR = ROOT / "module_bd" / "data" / "interim"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_volume_table(page: str) -> pd.DataFrame:
    """
    수간재적표 한 페이지 → 2D DataFrame (흉고직경 × 수고 → 재적).
    
    camelot이 셀에 \n으로 뭉친 값을 분리해서 진짜 표로 재구성.
    
    Args:
        page: PDF 페이지 번호 (예: "14")
    
    Returns:
        pd.DataFrame: index=흉고직경, columns=수고, values=재적(m³)
    """
    tables = camelot.read_pdf(str(PDF_PATH), pages=page, flavor="lattice")
    
    if tables.n == 0:
        raise ValueError(f"페이지 {page}: 표 못 찾음")
    
    df_raw = tables[0].df
    
    # 셀 위치 패턴 분석:
    #   df_raw.iloc[0, 0] = "흉고\n직경\n수고"      (헤더 + 수고 단어)
    #   df_raw.iloc[0, 1] = "6\n8\n10\n...\n28"   (수고 값들)
    #   df_raw.iloc[1, 0] = "5\n6\n7\n...\n35"    (흉고직경 값들)
    #   df_raw.iloc[1, 1] = "0.0081\n0.0097\n..." (재적, 모두 한 셀에)
    
    # 수고 (column 헤더) 추출
    heights_raw = df_raw.iloc[0, 1].strip().split("\n")
    heights = [int(h.strip()) for h in heights_raw if h.strip().isdigit()]
    
    # 흉고직경 (row 헤더) 추출
    dbh_raw = df_raw.iloc[1, 0].strip().split("\n")
    dbhs = [int(d.strip()) for d in dbh_raw if d.strip().isdigit()]
    
    # 재적 값들 (큰 한 덩어리)
    volumes_raw = df_raw.iloc[1, 1].strip().split("\n")
    volumes = []
    for v in volumes_raw:
        v = v.strip()
        if not v:
            continue
        try:
            volumes.append(float(v))
        except ValueError:
            volumes.append(np.nan)  # 공백 셀 처리
    
    n_dbh = len(dbhs)
    n_height = len(heights)
    expected = n_dbh * n_height
    
    print(f"   흉고직경 {n_dbh}개: {dbhs[:5]}...{dbhs[-3:]}")
    print(f"   수고 {n_height}개: {heights}")
    print(f"   재적 값 {len(volumes)}개 (예상: {expected})")
    
    if len(volumes) != expected:
        print(f"   ⚠️  값 개수 불일치! 부족분은 NaN으로 채움")
        # 부족하면 NaN으로 채우고, 넘치면 자르기
        if len(volumes) < expected:
            volumes.extend([np.nan] * (expected - len(volumes)))
        else:
            volumes = volumes[:expected]
    
    # 재구성: 컬럼 우선 (수고 기준) 또는 행 우선 (흉고직경 기준)?
    # PDF는 보통 흉고직경 행마다 → 수고 열 순회. 즉 행 우선 (C order).
    matrix = np.array(volumes).reshape(n_dbh, n_height)
    
    df = pd.DataFrame(matrix, index=dbhs, columns=heights)
    df.index.name = "흉고직경(cm)"
    df.columns.name = "수고(m)"
    
    return df


def parse_multiple_pages(pages: list[str]) -> dict[str, pd.DataFrame]:
    """여러 페이지 일괄 처리."""
    results = {}
    for page in pages:
        print(f"\n📄 페이지 {page} 처리 중...")
        try:
            df = parse_volume_table(page)
            results[page] = df
            print(f"   ✅ {df.shape[0]}행 × {df.shape[1]}열 표 완성")
        except Exception as e:
            print(f"   ❌ 실패: {type(e).__name__}: {e}")
    return results


# 페이지 → 수종 매핑 (PDF 목차에서 직접 추출)
SPECIES_PAGE_MAP = {
    # (수종명, 수피여부): 시작 페이지
    ("강원지방소나무", "수피포함"): 8,
    ("강원지방소나무", "수피제외"): 12,
    ("중부지방소나무", "수피포함"): 16,
    ("중부지방소나무", "수피제외"): 20,
    ("해송",          "수피포함"): 24,
    ("리기다소나무",  "수피포함"): 26,
    ("리기다소나무",  "수피제외"): 30,
    ("잣나무",        "수피포함"): 34,
    ("잣나무",        "수피제외"): 38,
    ("낙엽송",        "수피포함"): 42,
    ("낙엽송",        "수피제외"): 46,
    ("삼나무",        "수피포함"): 50,
    ("편백",          "수피포함"): 52,
    ("편백",          "수피제외"): 56,
    ("상수리나무",    "수피포함"): 60,
    ("상수리나무",    "수피제외"): 64,
    ("굴참나무",      "수피포함"): 68,
    ("굴참나무",      "수피제외"): 72,
    ("신갈나무",      "수피포함"): 76,
    ("신갈나무",      "수피제외"): 80,
    ("자작나무",      "수피포함"): 84,
    ("자작나무",      "수피제외"): 86,
    ("백합나무",      "수피포함"): 88,
    ("백합나무",      "수피제외"): 92,
    ("이태리포플러",  "수피포함"): 96,
}


def extract_all_species():
    """모든 수종의 수간재적표 일괄 추출."""
    print("=" * 60)
    print(f"🌲 14개 수종 × 25개 표 일괄 추출 시작")
    print("=" * 60)
    
    results = {}
    failures = []
    
    for (species, bark), start_page in SPECIES_PAGE_MAP.items():
        key = f"{species}_{bark}"
        print(f"\n📄 {key} — 페이지 {start_page} 시도")
        
        try:
            df = parse_volume_table(str(start_page))
            results[key] = df
            print(f"   ✅ {df.shape[0]} × {df.shape[1]} 추출 완료")
        except Exception as e:
            print(f"   ❌ 실패: {type(e).__name__}: {e}")
            failures.append(key)
    
    print()
    print("=" * 60)
    print(f"📊 최종 결과")
    print("=" * 60)
    print(f"   성공: {len(results)} / {len(SPECIES_PAGE_MAP)}")
    print(f"   실패: {failures}")
    
    return results


if __name__ == "__main__":
    print(f"📄 PDF: {PDF_PATH.name}")
    
    results = extract_all_species()
    
    # 각 수종별로 CSV + parquet 저장
    print()
    print("💾 저장 중...")
    for key, df in results.items():
        out_csv = OUT_DIR / f"yield_{key}.csv"
        df.to_csv(out_csv, encoding="utf-8-sig")
    
    # 통합 parquet (모든 수종 한 파일)
    all_data = []
    for key, df in results.items():
        species, bark = key.rsplit("_", 1)
        df_long = df.reset_index().melt(
            id_vars="흉고직경(cm)",
            var_name="수고(m)",
            value_name="재적(m³)"
        )
        df_long["수종"] = species
        df_long["수피여부"] = bark
        all_data.append(df_long)
    
    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        combined = combined[["수종", "수피여부", "흉고직경(cm)", "수고(m)", "재적(m³)"]]
        
        out_parquet = OUT_DIR / "yield_table_all.parquet"
        combined.to_parquet(out_parquet)
        print(f"💾 통합 parquet: {out_parquet.relative_to(ROOT)}")
        print(f"   총 {len(combined):,} 행")
        print(f"   수종 수: {combined['수종'].nunique()}")