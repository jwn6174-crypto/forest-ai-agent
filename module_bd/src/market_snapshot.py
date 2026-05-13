"""
market_snapshot.py
가이드 §6.3 — market_snapshot(date_iso) 함수.

특정 날짜의 종합 시장 상태 반환:
- KOFPI 원목 시장가격 (6 등급, 소나무 기본 + 수종별 확장)
- KAU 탄소배출권 종가 (이미 fetch_kau_price() 있음, 추후 통합)
- KOC 추정값 (KAU × 0.7)
- WTA 산주 의지가격 (박2020, 17,039원)
- 할인율 (산주 평균 5%)

데이터:
- KOFPI: module_bd/data/interim/kofpi_history.parquet (2025 1-4분기)
- KAU: 추후 fetch_kau_price() 통합

희도의 NPV 계산이 *직접 호출* 가능한 인터페이스.
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

# kau_api 모듈 import 가능하게 — 같은 src/ 폴더
sys.path.insert(0, str(Path(__file__).parent))
from kau_api import fetch_kau_price, find_latest_data

ROOT = Path(__file__).resolve().parents[2]
KOFPI_PATH = ROOT / "module_bd" / "data" / "interim" / "kofpi_history.parquet"

# 가이드 §6.3 의 등급명 (PDF 의 "특용재급" → 가이드의 "특용재")
GRADE_NAME_MAP = {
    "특용재급": "특용재",
    "1등급": "1등급",
    "2등급": "2등급",
    "3등급": "3등급",
    "원주재급": "원주재",
    "원료재급": "원료재",
}

# 가이드 §6.3 6 등급 순서
GUIDE_GRADES = ["특용재", "1등급", "2등급", "3등급", "원주재", "원료재"]

# 기본 수종 (가이드 §6.3 timber_price 의 출처)
DEFAULT_SPECIES = "소나무"


def _load_kofpi() -> pd.DataFrame:
    """KOFPI 가격 데이터 로드 + 캐시."""
    if not KOFPI_PATH.exists():
        raise FileNotFoundError(
            f"KOFPI 데이터 없음: {KOFPI_PATH}\n"
            f"먼저 'python module_bd/src/kofpi_parse.py' 실행하세요."
        )
    return pd.read_parquet(KOFPI_PATH)


def _get_latest_month_before(df: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
    """주어진 (연도, 월) 이전의 *가장 최근* 월 데이터 반환."""
    # 연도·월을 정수로 비교
    target_ym = year * 100 + month
    df["ym"] = df["연도"] * 100 + df["월"]
    
    filtered = df[df["ym"] <= target_ym]
    if filtered.empty:
        # 데이터보다 *이전 날짜* 인 경우: 가장 오래된 월 사용 (경고 동반)
        earliest = df.sort_values("ym").iloc[0]
        print(f"⚠️  요청 날짜 {year}-{month:02d} 이 KOFPI 데이터 시작 이전. "
              f"가장 오래된 월 ({earliest['연도']}-{earliest['월']:02d}) 사용.")
        latest_ym = earliest["ym"]
    else:
        latest_ym = filtered["ym"].max()
    
    return df[df["ym"] == latest_ym].drop(columns="ym")


def _get_timber_price_for_species(df: pd.DataFrame, species: str) -> dict:
    """수종별 6 등급 가격 dict 반환 (가이드 §6.3 형식)."""
    sp_df = df[df["수종"] == species]
    
    price_dict = {}
    for guide_grade in GUIDE_GRADES:
        # PDF 등급명 (예: "특용재급") 으로 찾기
        pdf_grade = next(
            (pdf_g for pdf_g, gd_g in GRADE_NAME_MAP.items() if gd_g == guide_grade),
            guide_grade,
        )
        match = sp_df[sp_df["등급"] == pdf_grade]
        if match.empty:
            price_dict[guide_grade] = None  # 해당 등급 없음 (예: 편백 특용재)
        else:
            price_dict[guide_grade] = int(match.iloc[0]["가격_원_per_m3"])
    
    return price_dict

def _get_kau_snapshot(date_iso: str) -> dict:
    """
    KAU/KOC 시장 가격 가져오기.
    
    date_iso 의 *해당일* 부터 시도, 데이터 없으면 *최근 영업일* 자동 검색.
    KAU 거래량 가장 많은 vintage 의 종가 사용.
    """
    target_date = date_iso.replace("-", "")  # YYYY-MM-DD → YYYYMMDD
    
    # 해당일 시도
    items = fetch_kau_price(target_date)
    actual_date = target_date
    
    # 없으면 자동 검색 (2-14일 전)
    if not items:
        latest_date, items = find_latest_data(max_days_back=14)
        if items:
            actual_date = latest_date
    
    if not items:
        return {
            "kau_close": None,
            "koc_estimate": None,
            "kau_vintage": None,
            "actual_date": None,
            "warning": "KAU 데이터 없음 (API 또는 영업일 문제)",
        }
    
    # KAU 종목만 필터 (KCU·KOC·국제 제외)
    kau_items = [it for it in items if it["itmsNm"].startswith("KAU")]
    
    # 거래량 있는 KAU 우선 (가장 활발한 vintage)
    kau_with_trades = [
        it for it in kau_items 
        if int(it.get("trqu", 0) or 0) > 0
    ]
    
    if kau_with_trades:
        # 거래량 가장 많은 KAU
        best = max(kau_with_trades, key=lambda it: int(it.get("trqu", 0) or 0))
    elif kau_items:
        # 거래 없으면 첫 KAU (보통 KAU24/25)
        best = kau_items[0]
    else:
        return {
            "kau_close": None,
            "koc_estimate": None,
            "kau_vintage": None,
            "actual_date": actual_date,
            "warning": "KAU 종목 없음",
        }
    
    kau_close = float(best["clpr"]) if best.get("clpr") else None
    
    # KOC 가격 — 진짜 데이터 있으면 사용, 없으면 KAU × 0.7 추정
    koc_items = [it for it in items if it["itmsNm"].startswith("KOC")]
    koc_with_trades = [
        it for it in koc_items 
        if int(it.get("trqu", 0) or 0) > 0
    ]
    
    if koc_with_trades:
        koc_best = max(koc_with_trades, key=lambda it: int(it.get("trqu", 0) or 0))
        koc_close = float(koc_best["clpr"])
        koc_source = f"KOC 실거래 ({koc_best['itmsNm']})"
    elif kau_close:
        # 가이드 §6.3: KAU × 0.7 추정 (KOC 거래 없는 경우)
        koc_close = kau_close * 0.7
        koc_source = "KAU × 0.7 추정 (KOC 거래 없음)"
    else:
        koc_close = None
        koc_source = "데이터 없음"
    
    return {
        "kau_close": kau_close,
        "koc_estimate": koc_close,
        "kau_vintage": best["itmsNm"],
        "actual_date": actual_date,
        "koc_source": koc_source,
        "warning": None,
    }

def market_snapshot(date_iso: str) -> dict:
    """
    가이드 §6.3 — 특정 날짜의 종합 시장 상태.
    
    Parameters
    ----------
    date_iso : str
        ISO 8601 형식 날짜 ("YYYY-MM-DD"). 그 날짜 *이전의 가장 최근* 데이터 반환.
    
    Returns
    -------
    dict
        가이드 §6.3 형식:
        {
            "date": ISO 날짜,
            "timber_price": {6 등급 → 가격} (소나무 기본),
            "timber_price_by_species": {수종 → {6 등급 → 가격}} (확장),
            "timber_price_meta": 출처·갱신일·한계 정보,
            "kau_close": float | None (추후 fetch_kau_price() 통합),
            "koc_estimate": float | None,
            "vcm_floor_wta": 17039 (박2020 WTA),
            "discount_rate": 0.05 (산주 평균),
        }
    
    Examples
    --------
    >>> snap = market_snapshot("2026-05-13")
    >>> snap["timber_price"]["1등급"]
    199700
    >>> snap["timber_price_by_species"]["낙엽송"]["특용재"]
    160600
    """
    # 날짜 파싱
    try:
        dt = datetime.fromisoformat(date_iso)
    except ValueError:
        raise ValueError(f"날짜 형식 오류: {date_iso} (YYYY-MM-DD 형식 필요)")
    
    # KOFPI 데이터 로드
    kofpi = _load_kofpi()
    
    # 요청 날짜 이전의 가장 최근 월
    latest = _get_latest_month_before(kofpi, dt.year, dt.month)
    
    if latest.empty:
        raise ValueError(f"KOFPI 데이터에서 {date_iso} 이전 데이터 없음")
    
    # 사용한 월
    actual_year = int(latest["연도"].iloc[0])
    actual_month = int(latest["월"].iloc[0])
    actual_quarter = int(latest["분기"].iloc[0])
    
    # 기본 수종 (소나무) 가격
    timber_price_default = _get_timber_price_for_species(latest, DEFAULT_SPECIES)
    
    # 수종별 확장
    timber_price_by_species = {}
    for species in latest["수종"].unique():
        timber_price_by_species[species] = _get_timber_price_for_species(latest, species)
    
    # 메타데이터
    timber_price_meta = {
        "source": "KOFPI 분기별 원목시장가격조사 보고서",
        "url": "https://www.forest.go.kr (정보공개 → 통합자료실)",
        "actual_data_period": f"{actual_year}년 {actual_month}월 ({actual_quarter}분기)",
        "default_species": DEFAULT_SPECIES,
        "default_species_note": (
            "timber_price 는 소나무 기준. "
            "수종별 가격은 timber_price_by_species 참조."
        ),
        "grade_changes": (
            "Q3·Q4 부터 편백·삼나무 등급 구성 변경됨 "
            "(3등급 → 원료재급)."
        ),
        "legal_basis": "산림청 고시 제2025-22호 원목규격 고시",
        "unit": "원/m³",
        "unit_conversion": {
            "소나무류": "1m³=0.85톤",
            "낙엽송류": "1m³=0.77톤",
            "편백류": "1m³=0.73톤",
            "참나무류": "1m³=1톤",
        },
    }
    
    # KAU/KOC 시장 가격 ⭐ NEW
    kau_data = _get_kau_snapshot(date_iso)
    
    return {
        "date": date_iso,
        "timber_price": timber_price_default,
        "timber_price_by_species": timber_price_by_species,
        "timber_price_meta": timber_price_meta,
        "kau_close": kau_data["kau_close"],
        "koc_estimate": kau_data["koc_estimate"],
        "kau_meta": {
            "vintage": kau_data["kau_vintage"],
            "actual_date": kau_data["actual_date"],
            "koc_source": kau_data.get("koc_source"),
            "warning": kau_data.get("warning"),
        },
        "vcm_floor_wta": 17039,  # 박2020 산주 WTA 하한
        "discount_rate": 0.05,   # 산주 평균 4-6%
    }


if __name__ == "__main__":
    print("=" * 60)
    print("📊 market_snapshot() 테스트")
    print("=" * 60)
    
    # 테스트 1: 2026-05-13 (현재)
    print("\n[테스트 1] market_snapshot('2026-05-13')")
    snap = market_snapshot("2026-05-13")
    print(f"   날짜: {snap['date']}")
    print(f"   데이터 시점: {snap['timber_price_meta']['actual_data_period']}")
    print(f"   기본 수종: {snap['timber_price_meta']['default_species']}")
    print(f"   할인율: {snap['discount_rate']}")
    print(f"   WTA: {snap['vcm_floor_wta']:,}원")
    print(f"   KAU 종가: {snap['kau_close']:,.0f}원/tCO2 ({snap['kau_meta']['vintage']})" 
          if snap['kau_close'] else "   KAU: 데이터 없음")
    print(f"   KOC 추정: {snap['koc_estimate']:,.0f}원/tCO2 ({snap['kau_meta']['koc_source']})" 
          if snap['koc_estimate'] else "   KOC: 데이터 없음")
    print(f"\n   timber_price (소나무 기준):")
    for grade, price in snap["timber_price"].items():
        price_str = f"{price:>10,}원/m³" if price else "       N/A"
        print(f"      {grade:>6}: {price_str}")
    
    # 테스트 2: 수종별
    print("\n[테스트 2] timber_price_by_species (7 수종 × 6 등급)")
    print(f"   {'수종':>12} | {'특용재':>10} | {'1등급':>10} | {'2등급':>10} | "
          f"{'3등급':>10} | {'원주재':>10} | {'원료재':>10}")
    print("   " + "-" * 95)
    for species, prices in snap["timber_price_by_species"].items():
        row = f"   {species:>12} |"
        for grade in GUIDE_GRADES:
            v = prices.get(grade)
            row += f" {v:>10,} |" if v else f" {'N/A':>10} |"
        print(row.rstrip(" |"))
    
    # 테스트 3: 과거 날짜 (Q2 시점)
    print("\n[테스트 3] market_snapshot('2025-05-15') — 과거 Q2 시점")
    snap_q2 = market_snapshot("2025-05-15")
    print(f"   날짜: {snap_q2['date']}")
    print(f"   데이터 시점: {snap_q2['timber_price_meta']['actual_data_period']}")
    print(f"   소나무 1등급: {snap_q2['timber_price']['1등급']:,}원/m³")
    
    # 테스트 4: 잣나무 NPV 시연
    print("\n[테스트 4] 잣나무 NPV 계산 시연")
    snap = market_snapshot("2026-05-13")
    잣나무_1등급 = snap["timber_price_by_species"]["잣나무"]["1등급"]
    소나무_1등급 = snap["timber_price_by_species"]["소나무"]["1등급"]
    print(f"   잣나무 1등급: {잣나무_1등급:,}원/m³")
    print(f"   소나무 1등급: {소나무_1등급:,}원/m³")
    diff_pct = (잣나무_1등급 - 소나무_1등급) / 소나무_1등급 * 100
    print(f"   차이: {diff_pct:+.1f}% (수종별 가격 *진짜* 사용 가능)")
    
    print()
    print("=" * 60)
    print("✅ market_snapshot() 작동 확인")
    print("=" * 60)