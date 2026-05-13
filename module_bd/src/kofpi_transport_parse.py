"""
kofpi_transport_parse.py
KOFPI 분기별 원목시장가격조사 보고서 - 제4장 거리별 운반비 추출.

진단 완료:
- 모든 4 분기 PDF 가 p.41 (표지), p.43 (대운반비), p.44 (소운반비) 동일 구조
- 침엽수·활엽수 구분, 5톤/25톤 적재량 구분
- 4 분기 시계열 데이터 추출 가능

산출물:
- kofpi_transport.parquet/csv: 4분기 × 침엽수/활엽수 × 5톤/25톤 × 7 거리구간 (대운반)
- kofpi_skidding.parquet/csv: 4분기 × 침엽수/활엽수 × 3 거리구간 (소운반)
"""

import pdfplumber
import re
import gc
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KOFPI_DIR = ROOT / "module_bd" / "data" / "raw" / "kofpi_reports"
OUTPUT_DIR = ROOT / "module_bd" / "data" / "interim"

# 모든 KOFPI 4 분기 PDF 가 동일 구조 (진단 완료)
TRANSPORT_PAGE = 43  # 대운반비 (5톤·25톤 × 7 거리구간 × 침엽수/활엽수)
SKIDDING_PAGE = 44   # 소운반비 (3 거리구간 × 침엽수/활엽수)

# 거리 구간 (대운반비, 7 구간)
TRANSPORT_DISTANCES = [
    "50km 이내", "50-100km", "100-150km", "150-200km",
    "200-250km", "250-300km", "300km 이상"
]

# 소운반 거리 구간 (3 구간)
SKIDDING_DISTANCES = [
    "500-1,000m", "1,000-2,000m", "2,000-4,000m"
]


def safe_extract_text(page):
    try:
        return page.extract_text() or ""
    except Exception:
        return ""


def parse_transport_page(pdf_path, quarter):
    """대운반비 페이지 (p.43) — 침엽수·활엽수 × 5톤/25톤 × 7 거리 추출."""
    results = []
    
    with pdfplumber.open(pdf_path) as pdf:
        if TRANSPORT_PAGE > len(pdf.pages):
            return results
        
        page = pdf.pages[TRANSPORT_PAGE - 1]
        text = safe_extract_text(page)
        
        if not text:
            return results
        
        # 분기 라인 식별: "`25년 X분기" 또는 "`24년 X분기"
        lines = text.split("\n")
        
        current_species = None  # 침엽수 / 활엽수
        current_quarter_label = None  # `25년 1분기 등
        current_load = None     # 5톤 / 25톤
        
        for line in lines:
            # 수종 구분
            if "침엽수 대운반비" in line:
                current_species = "침엽수"
            elif "활엽수 대운반비" in line:
                current_species = "활엽수"
            
            # 분기 라인 (예: "`25년" 단독)
            year_match = re.search(r'`(\d{2})년', line)
            quarter_match = re.search(r'(\d)분기', line)
            
            if year_match and quarter_match:
                yr = year_match.group(1)
                qt = quarter_match.group(1)
                current_quarter_label = f"20{yr}Q{qt}"
            
            # 5톤 / 25톤
            if "5톤" in line and "25톤" not in line:
                current_load = "5톤"
            elif "25톤" in line:
                current_load = "25톤"
            
            # 운반비 행 ("운반비" + 7 개 숫자)
            if "운반비" in line and "물류비" not in line:
                # 숫자 추출 (콤마 포함)
                nums = re.findall(r'[\d,]+', line)
                nums = [int(n.replace(",", "")) for n in nums if "," in n or (n.isdigit() and len(n) >= 4)]
                
                if len(nums) >= 7 and current_species and current_quarter_label and current_load:
                    for dist, price in zip(TRANSPORT_DISTANCES, nums[:7]):
                        results.append({
                            "분기": current_quarter_label,
                            "수종_구분": current_species,
                            "적재량": current_load,
                            "거리구간": dist,
                            "운반비_원_per_m3": price,
                            "source_pdf": pdf_path.name,
                        })
            
            # 상차비 행 별도 (보통 "6,500" 또는 "5,800" 단독)
            # 상차비는 분기마다 1개 → 별도 처리
    
    gc.collect()
    return results


def parse_skidding_page(pdf_path, quarter):
    """소운반비 페이지 (p.44) — 침엽수·활엽수 × 3 거리 추출."""
    results = []
    
    with pdfplumber.open(pdf_path) as pdf:
        if SKIDDING_PAGE > len(pdf.pages):
            return results
        
        page = pdf.pages[SKIDDING_PAGE - 1]
        text = safe_extract_text(page)
        
        if not text:
            return results
        
        lines = text.split("\n")
        
        current_species = None
        current_quarter_label = None
        current_charge_load = None  # 상차비 값 임시 저장
        
        for line in lines:
            if "침엽수 소운반비" in line:
                current_species = "침엽수"
            elif "활엽수 소운반비" in line:
                current_species = "활엽수"
            
            year_match = re.search(r'`(\d{2})년', line)
            quarter_match = re.search(r'(\d)분기', line)
            
            if year_match and quarter_match:
                yr = year_match.group(1)
                qt = quarter_match.group(1)
                current_quarter_label = f"20{yr}Q{qt}"
            
            # 운반비 행
            if "운반비" in line and "물류비" not in line:
                nums = re.findall(r'[\d,]+', line)
                nums = [int(n.replace(",", "")) for n in nums if "," in n or (n.isdigit() and len(n) >= 4)]
                
                if len(nums) >= 3 and current_species and current_quarter_label:
                    for dist, price in zip(SKIDDING_DISTANCES, nums[:3]):
                        results.append({
                            "분기": current_quarter_label,
                            "수종_구분": current_species,
                            "거리구간": dist,
                            "소운반비_원_per_m3": price,
                            "source_pdf": pdf_path.name,
                        })
    
    gc.collect()
    return results


def main():
    print("=" * 60)
    print("📊 KOFPI 거리별 운반비 추출 (4분기 통합)")
    print("=" * 60)
    
    pdfs = sorted(KOFPI_DIR.glob("*.pdf"))
    
    all_transport = []
    all_skidding = []
    
    for pdf_path in pdfs:
        quarter_match = re.search(r'(\d+)분기', pdf_path.name)
        if not quarter_match:
            continue
        quarter = quarter_match.group(1)
        
        print(f"\n📄 {pdf_path.name}")
        
        # 대운반비 추출
        transport_data = parse_transport_page(pdf_path, quarter)
        all_transport.extend(transport_data)
        print(f"   대운반비: {len(transport_data)} 행")
        
        # 소운반비 추출
        skidding_data = parse_skidding_page(pdf_path, quarter)
        all_skidding.extend(skidding_data)
        print(f"   소운반비: {len(skidding_data)} 행")
        
        gc.collect()
    
    # DataFrame 변환
    df_transport = pd.DataFrame(all_transport)
    df_skidding = pd.DataFrame(all_skidding)
    
    print()
    print("=" * 60)
    print("📋 추출 결과 요약")
    print("=" * 60)
    
    if not df_transport.empty:
        # 중복 제거 (같은 분기·수종·적재량·거리 중복 가능성)
        df_transport = df_transport.drop_duplicates(
            subset=["분기", "수종_구분", "적재량", "거리구간"],
            keep="last"
        )
        print(f"\n✅ 대운반비: {len(df_transport)} 행")
        print(df_transport.head(10).to_string())
        
        # 저장
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        parquet_path = OUTPUT_DIR / "kofpi_transport.parquet"
        csv_path = OUTPUT_DIR / "kofpi_transport.csv"
        df_transport.to_parquet(parquet_path)
        df_transport.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"\n💾 저장: {parquet_path.relative_to(ROOT)}")
    
    if not df_skidding.empty:
        df_skidding = df_skidding.drop_duplicates(
            subset=["분기", "수종_구분", "거리구간"],
            keep="last"
        )
        print(f"\n✅ 소운반비: {len(df_skidding)} 행")
        print(df_skidding.head(10).to_string())
        
        parquet_path = OUTPUT_DIR / "kofpi_skidding.parquet"
        csv_path = OUTPUT_DIR / "kofpi_skidding.csv"
        df_skidding.to_parquet(parquet_path)
        df_skidding.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"💾 저장: {parquet_path.relative_to(ROOT)}")
    
    print()
    print("=" * 60)
    print("✅ 운반비 추출 완료")
    print("=" * 60)


if __name__ == "__main__":
    main()