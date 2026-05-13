"""
yield_parse.py
임분수확표 PDF 의 표를 camelot 으로 추출하고 후처리하여
2차원 lookup table (흉고직경 × 수고 → 재적) 로 변환한다.

[2026-05-13 진행 상황]
- ✅ parse_volume_table: 첫 페이지 추출 (수고 6-28m, 22/25 케이스 완벽)
- ✅ parse_volume_table_second: 둘째 페이지 추출 (수고 30-52m)
- ⏳ 두 페이지 결합 후 모든 수종 처리

[발견]
- PDF page = 책 page + 6
- 각 수종 표가 2 PDF 페이지로 분할:
  - 첫 페이지: 흉고직경 헤더 + 수고 6-28m (셀 뭉침 패턴)
  - 둘째 페이지: 수고 30-52m (셀 개별 분리 패턴 — 훨씬 쉬움)
- 첫 페이지 셀 split 패턴 3가지:
  A. \n만 (p.14)
  B. \n + 공백 (p.22)
  C. 전각공백 U+3000 (p.30 작은 표)
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
    수간재적표 첫 페이지 → 2D DataFrame (흉고직경 × 수고 → 재적).
    수고 6-28m 범위. 셀 뭉침 패턴 3가지 처리.
    """
    tables = camelot.read_pdf(str(PDF_PATH), pages=page, flavor="lattice")
    
    if tables.n == 0:
        raise ValueError(f"페이지 {page}: 표 못 찾음")
    
    df_raw = tables[0].df
    
    # 수고 (column 헤더) — row 0, col 1
    heights_raw = df_raw.iloc[0, 1].strip().split("\n")
    heights = [int(h.strip()) for h in heights_raw if h.strip().isdigit()]
    
    # 흉고직경 (row 헤더) — row 1, col 0
    dbh_raw = df_raw.iloc[1, 0].strip().split("\n")
    dbhs = [int(d.strip()) for d in dbh_raw if d.strip().isdigit()]
    
    # 재적 값 수집 — 세 가지 패턴 처리
    volumes = []
    for r in range(1, df_raw.shape[0]):
        for c in range(1, df_raw.shape[1]):
            cell = df_raw.iloc[r, c]
            if not isinstance(cell, str):
                continue
            for line in cell.split("\n"):
                stripped = line.strip()
                if stripped == "" or stripped == "\u3000":
                    volumes.append(np.nan)
                    continue
                for token in line.split():
                    if token == "\u3000":
                        volumes.append(np.nan)
                    else:
                        try:
                            volumes.append(float(token))
                        except ValueError:
                            pass
    
    n_dbh = len(dbhs)
    n_height = len(heights)
    expected = n_dbh * n_height
    
    print(f"   흉고직경 {n_dbh}개: {dbhs[:5]}...{dbhs[-3:]}")
    print(f"   수고 {n_height}개: {heights}")
    print(f"   재적 값 {len(volumes)}개 (예상: {expected})")
    
    if len(volumes) != expected:
        print(f"   ⚠️  값 개수 불일치! 부족: {expected - len(volumes)}개")
        if len(volumes) < expected:
            volumes.extend([np.nan] * (expected - len(volumes)))
        else:
            print(f"   ⚠️  값이 {len(volumes) - expected}개 넘침. 앞 {expected}개만 사용")
            volumes = volumes[:expected]
    
    matrix = np.array(volumes).reshape(n_dbh, n_height)
    df = pd.DataFrame(matrix, index=dbhs, columns=heights)
    df.index.name = "흉고직경(cm)"
    df.columns.name = "수고(m)"
    
    return df


def parse_volume_table_second(page: str, expected_dbhs: list = None) -> pd.DataFrame:
    """
    수간재적표 둘째 페이지 (수고 30-52m) 파싱.
    
    첫 페이지와 다른 점:
    - 흉고직경 헤더가 *없음* (첫 페이지의 흉고직경을 그대로 사용)
    - 셀이 *개별로 분리* (셀 뭉침 없음)
    - 표 모양: (32, 12) — 행 0=수고헤더, 행 1-31=재적값
    
    Args:
        page: PDF 페이지 (예: "15")
        expected_dbhs: 흉고직경 리스트 (첫 페이지에서 가져온 값).
                       None이면 [5, 6, ..., 35] 기본.
    
    Returns:
        DataFrame: index=흉고직경, columns=수고 (30-52m), values=재적(m³)
    """
    # lattice 시도
    tables = camelot.read_pdf(str(PDF_PATH), pages=str(page), flavor="lattice")
    
    if tables.n == 0:
        # stream fallback
        print(f"   ⚠️  lattice 실패, stream 시도...")
        tables = camelot.read_pdf(str(PDF_PATH), pages=str(page), flavor="stream")
        if tables.n == 0:
            raise ValueError(f"페이지 {page}: lattice/stream 둘 다 실패")
    
    # 가장 큰 표를 선택 (둘째 페이지에 표가 여러 개 인식될 수 있음)
    df_raw = max((t.df for t in tables), key=lambda d: d.size)
    
    print(f"   선택된 표 shape: {df_raw.shape}, 표 개수: {tables.n}")
    
    # 행 0 = 수고 헤더
    heights = []
    for c in range(df_raw.shape[1]):
        cell = df_raw.iloc[0, c]
        if not isinstance(cell, str):
            continue
        cell = cell.strip()
        try:
            heights.append(int(cell))
        except ValueError:
            pass
    
    if not heights:
        raise ValueError(f"페이지 {page}: 수고 헤더 못 찾음. row 0 = {df_raw.iloc[0].tolist()}")
    
    # 행 1+ = 재적 값 (행마다 흉고직경 하나)
    n_dbh_rows = df_raw.shape[0] - 1
    
    if expected_dbhs is None:
        dbhs = list(range(5, 5 + n_dbh_rows))
    else:
        dbhs = expected_dbhs[:n_dbh_rows]
    
    # 매트릭스 채우기
    matrix = np.full((n_dbh_rows, len(heights)), np.nan)
    for r in range(n_dbh_rows):
        for c in range(min(len(heights), df_raw.shape[1])):
            cell = df_raw.iloc[r + 1, c]
            if not isinstance(cell, str):
                continue
            cell = cell.strip()
            try:
                matrix[r, c] = float(cell)
            except ValueError:
                pass
    
    df = pd.DataFrame(matrix, index=dbhs, columns=heights)
    df.index.name = "흉고직경(cm)"
    df.columns.name = "수고(m)"
    
    n_values = (~np.isnan(matrix)).sum()
    expected = n_dbh_rows * len(heights)
    print(f"   둘째 페이지: 흉고직경 {n_dbh_rows}개, 수고 {len(heights)}개 ({heights[0]}-{heights[-1]}m)")
    print(f"   재적 값 {n_values}개 (예상: {expected})")
    
    return df

# PDF 페이지 매핑 (책 page + 6)
SPECIES_PDF_PAGES = {
    ("강원지방소나무", "수피포함"): (14, 15),
    ("강원지방소나무", "수피제외"): (18, 19),
    ("중부지방소나무", "수피포함"): (22, 23),
    ("중부지방소나무", "수피제외"): (26, 27),
    ("해송",          "수피포함"): (30, 31),
    ("리기다소나무",  "수피포함"): (32, 33),
    ("리기다소나무",  "수피제외"): (36, 37),
    ("잣나무",        "수피포함"): (40, 41),
    ("잣나무",        "수피제외"): (44, 45),
    ("낙엽송",        "수피포함"): (48, 49),
    ("낙엽송",        "수피제외"): (52, 53),
    ("삼나무",        "수피포함"): (56, 57),
    ("편백",          "수피포함"): (58, 59),
    ("편백",          "수피제외"): (62, 63),
    ("상수리나무",    "수피포함"): (66, 67),
    ("상수리나무",    "수피제외"): (70, 71),
    ("굴참나무",      "수피포함"): (74, 75),
    ("굴참나무",      "수피제외"): (78, 79),
    ("신갈나무",      "수피포함"): (82, 83),
    ("신갈나무",      "수피제외"): (86, 87),
    ("자작나무",      "수피포함"): (90, 91),
    ("자작나무",      "수피제외"): (92, 93),
    ("백합나무",      "수피포함"): (94, 95),
    ("백합나무",      "수피제외"): (98, 99),
    ("이태리포플러",  "수피포함"): (102, 103),
}


if __name__ == "__main__":
    print(f"📄 PDF: {PDF_PATH.name}")
    print(f"🎯 강원지방소나무 두 페이지 결합 테스트")
    print()
    
    # 첫 페이지 추출
    print("=" * 60)
    print("📄 첫 페이지 (PDF p.14, 수고 6-28m)")
    print("=" * 60)
    df1 = parse_volume_table("14")
    print(f"   shape: {df1.shape}")
    
    # 둘째 페이지 추출
    print()
    print("=" * 60)
    print("📄 둘째 페이지 (PDF p.15, 수고 30-52m)")
    print("=" * 60)
    df2 = parse_volume_table_second("15", expected_dbhs=list(df1.index))
    print(f"   shape: {df2.shape}")
    
    # 결합
    print()
    print("=" * 60)
    print("🔗 두 페이지 결합")
    print("=" * 60)
    combined = pd.concat([df1, df2], axis=1)
    print(f"   결합 shape: {combined.shape}")
    print(f"   수고 범위: {min(combined.columns)}m ~ {max(combined.columns)}m")
    print(f"   흉고직경 범위: {min(combined.index)}cm ~ {max(combined.index)}cm")
    
    # 미리보기 (처음 5행, 양 끝 컬럼)
    print()
    print("처음 5행 × (앞 6열, 뒤 3열):")
    preview = pd.concat([combined.iloc[:5, :6], combined.iloc[:5, -3:]], axis=1)
    print(preview.to_string())
    
    # 통계
    n_total = combined.size
    n_values = combined.notna().sum().sum()
    print(f"\n📈 값 {n_values}개 / 총 {n_total}개")
    print(f"   재적 범위: {combined.min().min():.4f} ~ {combined.max().max():.4f} m³")
    
    # 저장
    out_csv = OUT_DIR / "yield_강원지방소나무_수피포함_full.csv"
    combined.to_csv(out_csv, encoding="utf-8-sig")
    print(f"\n💾 {out_csv.relative_to(ROOT)}")