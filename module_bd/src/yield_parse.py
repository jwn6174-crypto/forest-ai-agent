"""
yield_parse.py
임분수확표 PDF 의 표를 camelot 으로 추출하고 후처리하여
2차원 lookup table (흉고직경 × 수고 → 재적) 로 변환한다.

[2026-05-12 진행 상황]
- ✅ parse_volume_table: 한 페이지 추출 + 셀에 뭉친 \n 분리 (검증: p.14)
- 🔄 parse_two_page_table: 2페이지 결합 (첫 페이지만 작동, 둘째 페이지 실패)
- ❌ 둘째 페이지(15, 19, ...) 는 셀 구조가 달라서 camelot이 인식 못 함
- ⏳ 다음 단계: 둘째 페이지 전용 파서 작성

[발견]
- PDF page = 책 page + 6
- 각 수종 표가 2 PDF 페이지로 분할:
  - 첫 페이지: 흉고직경 헤더 + 수고 6-28m
  - 둘째 페이지: 수고 30-52m만 (흉고직경 헤더 없음) ← 다른 파서 필요
- camelot이 셀 구분선 못 보고 외곽만 인식 → 후처리로 \n 분리
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
    
    camelot이 셀에 \n으로 뭉친 값을 분리.
    BUG FIX 2026-05-12: 페이지마다 camelot이 셀을 다르게 나눔.
    이제 *모든 데이터 셀* 을 순회하여 재적 값 수집.
    """
    tables = camelot.read_pdf(str(PDF_PATH), pages=page, flavor="lattice")
    
    if tables.n == 0:
        raise ValueError(f"페이지 {page}: 표 못 찾음")
    
    df_raw = tables[0].df
    
    # 수고 (column 헤더) — 보통 row 0, col 1
    heights_raw = df_raw.iloc[0, 1].strip().split("\n")
    heights = [int(h.strip()) for h in heights_raw if h.strip().isdigit()]
    
    # 흉고직경 (row 헤더) — 보통 row 1, col 0
    dbh_raw = df_raw.iloc[1, 0].strip().split("\n")
    dbhs = [int(d.strip()) for d in dbh_raw if d.strip().isdigit()]
    
    # 재적 값 수집 — 세 가지 패턴 처리
    # 패턴 A (예: p.14): 셀에 \n으로 값마다 분리 (372줄)
    # 패턴 B (예: p.22): 셀에 \n으로 행 구분 + 공백으로 행 안 값 구분 (31줄)
    # 패턴 C (작은 표, 예: p.30): 빈 셀 자리에 　(전각공백, U+3000) 표시
    volumes = []
    for r in range(1, df_raw.shape[0]):
        for c in range(1, df_raw.shape[1]):
            cell = df_raw.iloc[r, c]
            if not isinstance(cell, str):
                continue
            for line in cell.split("\n"):
                # 전각공백 (　) → NaN 으로 보존하면서 split
                stripped = line.strip()
                if stripped == "" or stripped == "\u3000":
                    # 줄 전체가 빈 줄 또는 전각공백 → NaN 하나 추가
                    volumes.append(np.nan)
                    continue
                for token in line.split():  # 공백 분리
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
            # 넘치는 경우: 첫 expected 개만 (또는 끝에서 자를 수도)
            print(f"   ⚠️  값이 {len(volumes) - expected}개 넘침. 앞 {expected}개만 사용")
            volumes = volumes[:expected]
    
    matrix = np.array(volumes).reshape(n_dbh, n_height)
    df = pd.DataFrame(matrix, index=dbhs, columns=heights)
    df.index.name = "흉고직경(cm)"
    df.columns.name = "수고(m)"
    
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
    print(f"🎯 첫 페이지만 추출 (둘째 페이지 30-52m은 내일)")
    print()
    
    results = {}
    failures = []
    
    for (species, bark), (p1, _) in SPECIES_PDF_PAGES.items():
        key = f"{species}_{bark}"
        print(f"\n🌲 {key} — PDF page {p1}")
        try:
            df = parse_volume_table(str(p1))
            results[key] = df
            print(f"   ✅ {df.shape}")
        except Exception as e:
            print(f"   ❌ {type(e).__name__}: {e}")
            failures.append(key)
    
    print()
    print("=" * 60)
    print(f"📊 첫 페이지 추출: {len(results)} 성공 / {len(failures)} 실패")
    print(f"   실패: {failures}")
    print("=" * 60)
    
    # 💾 각 수종별 CSV 저장
    print()
    print("💾 수종별 CSV 저장 중...")
    for key, df in results.items():
        out_csv = OUT_DIR / f"yield_{key}.csv"
        df.to_csv(out_csv, encoding="utf-8-sig")
    print(f"   ✅ {len(results)}개 CSV 저장 완료")
    
    # 💾 통합 long-format parquet
    print()
    print("💾 통합 long-format parquet 생성 중...")
    
    # 작은 표 3개 (NaN 위치 어긋남) 식별
    SMALL_TABLE_PARTIAL = {"해송_수피포함", "삼나무_수피포함", "이태리포플러_수피포함"}
    
    all_data = []
    for key, df in results.items():
        species, bark = key.rsplit("_", 1)
        # wide → long
        df_long = df.reset_index().melt(
            id_vars="흉고직경(cm)",
            var_name="수고(m)",
            value_name="재적(m³)"
        )
        df_long["수종"] = species
        df_long["수피여부"] = bark
        df_long["품질"] = "DRAFT" if key in SMALL_TABLE_PARTIAL else "OK"
        all_data.append(df_long)
    
    combined = pd.concat(all_data, ignore_index=True)
    combined = combined[["수종", "수피여부", "흉고직경(cm)", "수고(m)", "재적(m³)", "품질"]]
    
    out_parquet = OUT_DIR / "yield_table_partial.parquet"
    combined.to_parquet(out_parquet)
    
    # 통계
    n_total = len(combined)
    n_ok_rows = (combined["품질"] == "OK").sum()
    n_draft_rows = (combined["품질"] == "DRAFT").sum()
    n_values = combined["재적(m³)"].notna().sum()
    n_nan = combined["재적(m³)"].isna().sum()
    
    print(f"   ✅ {out_parquet.relative_to(ROOT)}")
    print(f"   총 {n_total:,} 행 ({n_ok_rows:,} OK + {n_draft_rows:,} DRAFT)")
    print(f"   재적 값: {n_values:,} 개 (NaN {n_nan:,} 개)")
    print(f"   수종: {combined['수종'].nunique()} 개")
    
    print()
    print("=" * 60)
    print("✅ Day 1 완료")
    print("=" * 60)
    print()
    print("💡 다음 단계 (Day 2):")
    print("   1. 작은 표 3개 (해송/삼나무/이태리포플러) 행별 정렬 수정")
    print("   2. 둘째 페이지 (수고 30-52m) 전용 파서")
    print("   3. growth_predict() 함수")
    print("   4. VWorld 재시도")