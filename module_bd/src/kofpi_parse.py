"""
kofpi_parse.py
KOFPI 분기별 원목시장가격조사 보고서 PDF → DataFrame

데이터 출처:
- 한국임업진흥원 분기별 보고서
- 다운로드: forest.go.kr/kfsweb [정보공개] - [통합자료실]

수종별 등급 개수 (PDF 페이지 5):
- 소나무·낙엽송·잣나무: 6 등급 (특용재·1·2·3·원주재·원료재)
- 리기다소나무: 5 등급 (특용재 없음)
- 참나무류: 4 등급 (1·2·3·원료재)
- 편백: 3 등급 (1·2·3등급)
- 삼나무: 2 등급 (2·3등급)

산출물: module_bd/data/interim/kofpi_history.parquet
"""

import pdfplumber
import pandas as pd
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_DIR = ROOT / "module_bd" / "data" / "raw" / "kofpi_reports"
OUT_DIR = ROOT / "module_bd" / "data" / "interim"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 수종별 등급 구성 (PDF 진단으로 확정)
SPECIES_GRADES = {
    "소나무":      ["특용재급", "1등급", "2등급", "3등급", "원주재급", "원료재급"],
    "낙엽송":      ["특용재급", "1등급", "2등급", "3등급", "원주재급", "원료재급"],
    "잣나무":      ["특용재급", "1등급", "2등급", "3등급", "원주재급", "원료재급"],
    "리기다소나무": ["1등급", "2등급", "3등급", "원주재급", "원료재급"],
    "참나무류":     ["1등급", "2등급", "3등급", "원료재급"],
    "편백":        ["1등급", "2등급", "3등급"],
    "삼나무":      ["2등급", "3등급"],
}

# 수종 순서 (PDF 출현 순서)
SPECIES_ORDER = ["소나무", "낙엽송", "잣나무", "리기다소나무", "참나무류", "편백", "삼나무"]


def find_summary_page(pdf) -> int:
    """수종별 요약표 페이지 찾기."""
    for i, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        if "수종별 국산재 원목 시장가격 요약" in text:
            return i
    return -1


def parse_summary_text(text: str, year: int, quarter: int, pdf_name: str) -> list:
    """
    수종별 요약표 파싱 — *명시적 위치 매핑*.
    
    PDF 텍스트 진단으로 확인된 패턴: 각 수종 그룹 내 가격 행의 위치는
    PDF 형식이 동일하므로 *고정 순서*로 처리. 단, 분기별로 등급 구성이
    다른 수종 (편백·삼나무) 은 *해당 분기의 등급 리스트*를 사용.
    """
    rows = []
    
    quarter_months = {1: [1, 2, 3], 2: [4, 5, 6], 3: [7, 8, 9], 4: [10, 11, 12]}
    months = quarter_months[quarter]
    
    # 분기별 등급 구성 (PDF 진단 결과)
    if quarter in (1, 2):
        species_grades_for_quarter = {
            "소나무":      ["특용재급", "1등급", "2등급", "3등급", "원주재급", "원료재급"],
            "낙엽송":      ["특용재급", "1등급", "2등급", "3등급", "원주재급", "원료재급"],
            "잣나무":      ["특용재급", "1등급", "2등급", "3등급", "원주재급", "원료재급"],
            "리기다소나무": ["1등급", "2등급", "3등급", "원주재급", "원료재급"],
            "참나무류":     ["1등급", "2등급", "3등급", "원료재급"],
            "편백":        ["1등급", "2등급", "3등급"],
            "삼나무":      ["2등급", "3등급"],
        }
    else:  # Q3, Q4
        species_grades_for_quarter = {
            "소나무":      ["특용재급", "1등급", "2등급", "3등급", "원주재급", "원료재급"],
            "낙엽송":      ["특용재급", "1등급", "2등급", "3등급", "원주재급", "원료재급"],
            "잣나무":      ["특용재급", "1등급", "2등급", "3등급", "원주재급", "원료재급"],
            "리기다소나무": ["1등급", "2등급", "3등급", "원주재급", "원료재급"],
            "참나무류":     ["1등급", "2등급", "3등급", "원료재급"],
            "편백":        ["1등급", "2등급", "원료재급"],
            "삼나무":      ["1등급", "2등급", "원료재급"],
        }
    
    # 모든 가격 행 *순서대로* 추출
    m3_section = text.split("(단위: 원/톤)")[0]
    
    price_pattern = re.compile(
        r"(특용재급|1등급|2등급|3등급|원주재급|원료재급)\s+"
        r"([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)"
    )
    
    all_price_rows = []
    for m in price_pattern.finditer(m3_section):
        grade = m.group(1)
        prices = [int(m.group(k + 2).replace(",", "")) for k in range(4)]
        all_price_rows.append((grade, prices))
    
    print(f"   가격 행 {len(all_price_rows)} 개 발견")
    
    # 기대 행 수
    expected_grades_flat = []
    for sp in SPECIES_ORDER:
        expected_grades_flat.extend([(sp, g) for g in species_grades_for_quarter[sp]])
    
    print(f"   기대 행 수: {len(expected_grades_flat)} (수종별 등급 누적)")
    
    if len(all_price_rows) != len(expected_grades_flat):
        print(f"   ⚠️  행 수 불일치! 발견 {len(all_price_rows)} vs 기대 {len(expected_grades_flat)}")
    
    # 순서대로 매핑
    for i, (sp, expected_grade) in enumerate(expected_grades_flat):
        if i >= len(all_price_rows):
            print(f"   ⚠️  {sp} {expected_grade}: 가격 행 부족")
            break
        
        found_grade, prices = all_price_rows[i]
        if found_grade != expected_grade:
            print(f"   ⚠️  순서 mismatch: {sp} {expected_grade} 기대했는데 "
                  f"{found_grade} 발견 (행 #{i})")
            # 그래도 *기대 등급* 으로 저장 (PDF 의 등급명 우선)
            # 또는 found_grade 우선?
            # → found_grade 우선이 더 안전 (실제 PDF 데이터)
        
        # 월 3개 가격
        for k, month in enumerate(months):
            rows.append({
                "연도": year,
                "분기": quarter,
                "월": month,
                "수종": sp,
                "등급": found_grade,  # PDF 의 실제 등급명
                "가격_원_per_m3": prices[k],
                "source_pdf": pdf_name,
            })
    
    # 수종별 그룹 결과 요약
    seen_groups = {}
    for sp, _ in expected_grades_flat[: len(all_price_rows)]:
        seen_groups.setdefault(sp, 0)
        seen_groups[sp] += 1
    for sp, count in seen_groups.items():
        grades_in_pdf = [r[0] for i, r in enumerate(all_price_rows)
                         if expected_grades_flat[i][0] == sp]
        print(f"      {sp}: {count} 등급 [{', '.join(grades_in_pdf)}]")
    
    return rows

def parse_kofpi_pdf(pdf_path: Path) -> pd.DataFrame:
    """KOFPI 분기별 보고서 PDF 1개 파싱."""
    match = re.search(r"(\d{4})년_?(\d)분기", pdf_path.name)
    if not match:
        raise ValueError(f"파일명에서 연도·분기 못 찾음: {pdf_path.name}")
    
    year = int(match.group(1))
    quarter = int(match.group(2))
    print(f"\n📄 {pdf_path.name} → {year}년 {quarter}분기")
    
    with pdfplumber.open(pdf_path) as pdf:
        page_idx = find_summary_page(pdf)
        if page_idx == -1:
            raise ValueError(f"요약표 페이지 못 찾음: {pdf_path.name}")
        
        print(f"   요약표 위치: PDF p.{page_idx + 1}")
        text = pdf.pages[page_idx].extract_text()
    
    rows = parse_summary_text(text, year, quarter, pdf_path.name)
    df = pd.DataFrame(rows)
    
    if df.empty:
        print(f"   ❌ 데이터 추출 실패")
        return df
    
    # 기대 행 수: (6+6+6+5+4+3+2) 등급 × 3 월 = 32 × 3 = 96
    expected = sum(len(g) for g in SPECIES_GRADES.values()) * 3
    print(f"   ✅ {len(df)} 행 추출 (기대 {expected})")
    print(f"      수종: {df['수종'].nunique()}, 등급: {df['등급'].nunique()}, "
          f"월: {df['월'].nunique()}")
    
    return df


def parse_all_reports() -> pd.DataFrame:
    """kofpi_reports/ 폴더의 모든 PDF 일괄 처리."""
    print("=" * 60)
    print(f"📚 KOFPI 보고서 일괄 처리")
    print(f"   위치: {PDF_DIR.relative_to(ROOT)}")
    print("=" * 60)
    
    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"PDF 파일 없음: {PDF_DIR}")
    
    print(f"   {len(pdf_files)} 개 PDF 발견")
    
    all_dfs = []
    for pdf_path in pdf_files:
        try:
            df = parse_kofpi_pdf(pdf_path)
            if not df.empty:
                all_dfs.append(df)
        except Exception as e:
            print(f"   ❌ {pdf_path.name}: {type(e).__name__}: {e}")
    
    if not all_dfs:
        raise ValueError("추출된 데이터 없음")
    
    combined = pd.concat(all_dfs, ignore_index=True)
    combined = combined.sort_values(["연도", "분기", "월", "수종", "등급"]).reset_index(drop=True)
    
    return combined


if __name__ == "__main__":
    df = parse_all_reports()
    
    print()
    print("=" * 60)
    print("📊 통합 결과")
    print("=" * 60)
    print(f"   총 {len(df):,} 행")
    print(f"   기간: {df['연도'].min()}-{df['연도'].max()}")
    print(f"   분기: {sorted(df['분기'].unique())}")
    print(f"   월: {sorted(df['월'].unique())}")
    print(f"   수종 ({df['수종'].nunique()}): {sorted(df['수종'].unique())}")
    print(f"   등급 ({df['등급'].nunique()}): {sorted(df['등급'].unique())}")
    print(f"   가격 범위: {df['가격_원_per_m3'].min():,} ~ {df['가격_원_per_m3'].max():,} 원/m³")
    
    print()
    print("📋 벤치마크 검증 — 소나무 1등급 시계열 (예상 약 200,000원대):")
    sample = df[(df["수종"] == "소나무") & (df["등급"] == "1등급")].sort_values(["연도", "월"])
    for _, row in sample.iterrows():
        print(f"   {row['연도']}년 {row['월']:>2}월: {row['가격_원_per_m3']:>10,} 원/m³")
    
    print("📋 수종별 등급 개수 검증 (분기별 형식 변경 반영):")
    print("   참고: 편백·삼나무는 Q3·Q4 부터 형식 변경됨 (원료재급 추가)")
    
    # 분기별 등급 검증
    for quarter in sorted(df["분기"].unique()):
        q_df = df[df["분기"] == quarter]
        print(f"   {quarter}분기:")
        for sp in SPECIES_ORDER:
            sp_grades = q_df[q_df["수종"] == sp]["등급"].nunique()
            print(f"      {sp}: {sp_grades} 등급")
    
    # 저장
    out_path = OUT_DIR / "kofpi_history.parquet"
    df.to_parquet(out_path)
    print()
    print(f"💾 저장: {out_path.relative_to(ROOT)}")
    
    csv_path = OUT_DIR / "kofpi_history.csv"
    df.to_csv(csv_path, encoding="utf-8-sig", index=False)
    print(f"💾 저장: {csv_path.relative_to(ROOT)}")
    
    print()
    print("=" * 60)
    print("✅ KOFPI 보고서 추출 완료")
    print("=" * 60)