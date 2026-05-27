"""
asos_features.py — 보은 ASOS 평년 + anomaly 산출 (가이드 §5.4 4 변수).

D13 결정 2 *완전 구현* (정우님 짚어준 시기 미스매치 해결):
  · 평년: 1991-2020 (30년) ← 가이드 §5.4 "30y" 명시
  · NFI 시기: 2016-2020 (5년)
  · anomaly = NFI 시기 평균 - 30년 평년

4 변수:
  · temp_anomaly_30y: 연평균 기온 anomaly (°C)
  · prcp_anomaly_30y: 연 강수량 anomaly (mm/year)
  · vpd_max: NFI 시기 평균 연 최대 VPD (kPa)
  · gdd_cum: NFI 시기 평균 누적 GDD (°C·day, 5°C 기저)

VPD 계산 (Tetens 공식):
  es(T) = 0.6108 × exp(17.27 × T / (T + 237.3))  [kPa]
  VPD = es(avgTa) - es(avgTd)
  (이슬점 사용, 가장 정확)

데이터:
  module_bd/data/raw/asos/asos_226_1991_2020.jsonl
"""
import json
import math
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[3]
ASOS_PATH = ROOT / "module_bd" / "data" / "raw" / "asos" / "asos_226_1991_2020.jsonl"

GDD_BASE_TEMP = 5.0
NORMAL_YEARS = list(range(1991, 2021))  # 1991-2020 (30년 평년)
NFI_YEARS = list(range(2016, 2021))     # 2016-2020 (NFI 시기)


def safe_float(v):
    """빈 문자열·None 안전 변환."""
    if v is None or v == '':
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def saturation_vapor_pressure(temp_c):
    """포화 수증기압 (kPa). Tetens 공식."""
    if temp_c is None:
        return None
    return 0.6108 * math.exp(17.27 * temp_c / (temp_c + 237.3))


def calc_vpd(avg_ta, avg_td):
    """VPD (kPa) = es(avgTa) - es(avgTd). 이슬점 사용."""
    es = saturation_vapor_pressure(avg_ta)
    ea = saturation_vapor_pressure(avg_td)
    if es is None or ea is None:
        return None
    return max(0, es - ea)


def load_asos():
    """ASOS jsonl 로딩 → list of dict (필수 변수만)."""
    if not ASOS_PATH.exists():
        print(f"⚠ 파일 없음: {ASOS_PATH}")
        return []

    records = []
    with open(ASOS_PATH, encoding='utf-8') as f:
        for line in f:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            tm = item.get('tm')  # "2020-01-01"
            if not tm:
                continue
            try:
                year = int(tm[:4])
                avg_ta = safe_float(item.get('avgTa'))
                avg_td = safe_float(item.get('avgTd'))
                sum_rn = safe_float(item.get('sumRn')) or 0.0  # 빈 값 = 0 (강수 없음)
                avg_rhm = safe_float(item.get('avgRhm'))
                records.append({
                    'date': tm,
                    'year': year,
                    'avg_ta': avg_ta,
                    'avg_td': avg_td,
                    'sum_rn': sum_rn,
                    'avg_rhm': avg_rhm,
                    'vpd': calc_vpd(avg_ta, avg_td),
                })
            except Exception:
                continue
    return records


def annual_stats(records, year):
    """한 해의 (avg_temp, sum_rn, avg_vpd, max_vpd, gdd_cum) 산출."""
    year_recs = [r for r in records if r['year'] == year]
    if len(year_recs) < 300:
        return None

    # 평균 기온 (연평균)
    temps = [r['avg_ta'] for r in year_recs if r['avg_ta'] is not None]
    avg_temp = sum(temps) / len(temps) if temps else None

    # 연 강수 (합)
    rains = [r['sum_rn'] for r in year_recs]
    sum_rn = sum(rains)

    # VPD (평균 + 최대)
    vpds = [r['vpd'] for r in year_recs if r['vpd'] is not None]
    avg_vpd = sum(vpds) / len(vpds) if vpds else None
    max_vpd = max(vpds) if vpds else None

    # GDD 누적
    gdd_days = [max(0, r['avg_ta'] - GDD_BASE_TEMP)
                for r in year_recs if r['avg_ta'] is not None]
    gdd_cum = sum(gdd_days)

    return {
        'year': year,
        'avg_temp': avg_temp,
        'sum_rn': sum_rn,
        'avg_vpd': avg_vpd,
        'max_vpd': max_vpd,
        'gdd_cum': gdd_cum,
        'n_days': len(year_recs),
    }


def main():
    print("=" * 70)
    print("보은 ASOS 1991-2020 평년 + 2016-2020 anomaly 산출")
    print("=" * 70)

    print("\nASOS 로딩...")
    records = load_asos()
    print(f"  총 일수: {len(records)}")

    # 연도별 통계
    print("\n연도별 통계 산출...")
    annual = {}
    for year in NORMAL_YEARS:
        stats = annual_stats(records, year)
        if stats:
            annual[year] = stats

    print(f"  유효 연도: {len(annual)}/{len(NORMAL_YEARS)}")

    # 1991-2020 평년 (30년)
    normal_temps = [annual[y]['avg_temp'] for y in NORMAL_YEARS if y in annual and annual[y]['avg_temp'] is not None]
    normal_rains = [annual[y]['sum_rn'] for y in NORMAL_YEARS if y in annual]
    normal_vpds = [annual[y]['avg_vpd'] for y in NORMAL_YEARS if y in annual and annual[y]['avg_vpd'] is not None]
    normal_max_vpds = [annual[y]['max_vpd'] for y in NORMAL_YEARS if y in annual and annual[y]['max_vpd'] is not None]
    normal_gdds = [annual[y]['gdd_cum'] for y in NORMAL_YEARS if y in annual]

    normal_temp = sum(normal_temps) / len(normal_temps)
    normal_rain = sum(normal_rains) / len(normal_rains)
    normal_vpd = sum(normal_vpds) / len(normal_vpds)
    normal_max_vpd = sum(normal_max_vpds) / len(normal_max_vpds)
    normal_gdd = sum(normal_gdds) / len(normal_gdds)

    # 2016-2020 평균 (NFI 시기)
    nfi_temps = [annual[y]['avg_temp'] for y in NFI_YEARS if y in annual and annual[y]['avg_temp'] is not None]
    nfi_rains = [annual[y]['sum_rn'] for y in NFI_YEARS if y in annual]
    nfi_max_vpds = [annual[y]['max_vpd'] for y in NFI_YEARS if y in annual and annual[y]['max_vpd'] is not None]
    nfi_gdds = [annual[y]['gdd_cum'] for y in NFI_YEARS if y in annual]

    nfi_temp = sum(nfi_temps) / len(nfi_temps)
    nfi_rain = sum(nfi_rains) / len(nfi_rains)
    nfi_max_vpd = sum(nfi_max_vpds) / len(nfi_max_vpds)
    nfi_gdd = sum(nfi_gdds) / len(nfi_gdds)

    # 출력
    print(f"\n{'=' * 70}")
    print("결과:")
    print(f"{'=' * 70}")

    print(f"\n1991-2020 평년 (30년):")
    print(f"  연평균 기온: {normal_temp:.2f} °C")
    print(f"  연 강수량: {normal_rain:.0f} mm/year")
    print(f"  연 평균 VPD: {normal_vpd:.3f} kPa")
    print(f"  연 최대 VPD: {normal_max_vpd:.3f} kPa")
    print(f"  연 GDD 누적: {normal_gdd:.0f} °C·day")

    print(f"\n2016-2020 평균 (NFI 시기, 5년):")
    print(f"  연평균 기온: {nfi_temp:.2f} °C")
    print(f"  연 강수량: {nfi_rain:.0f} mm/year")
    print(f"  연 최대 VPD: {nfi_max_vpd:.3f} kPa")
    print(f"  연 GDD 누적: {nfi_gdd:.0f} °C·day")

    print(f"\nAnomaly (NFI 시기 - 30년 평년):")
    print(f"  temp_anomaly_30y = {nfi_temp - normal_temp:+.3f} °C")
    print(f"  prcp_anomaly_30y = {nfi_rain - normal_rain:+.0f} mm/year")
    print(f"  vpd_anomaly: {nfi_max_vpd - normal_max_vpd:+.3f} kPa")
    print(f"  gdd_anomaly: {nfi_gdd - normal_gdd:+.0f} °C·day")

    # 연도별 보기
    print(f"\n{'=' * 70}")
    print("연도별 통계 (2016-2020):")
    print(f"{'=' * 70}")
    print(f"  {'연도':<6} {'평균기온':<10} {'강수':<10} {'GDD':<8} {'최대VPD':<10}")
    for year in NFI_YEARS:
        if year in annual:
            s = annual[year]
            print(f"  {year:<6} {s['avg_temp']:<10.2f} {s['sum_rn']:<10.0f} {s['gdd_cum']:<8.0f} {s['max_vpd']:<10.3f}")

    # 학술 의미
    print(f"\n{'=' * 70}")
    print("의미 해석:")
    print(f"{'=' * 70}")
    t_anom = nfi_temp - normal_temp
    if t_anom > 0.5:
        print(f"  → 2016-2020 이 1991-2020 평년보다 {t_anom:.2f}°C 더 더움.")
        print(f"     지구온난화 신호 명확. NFI 시기 = 비교적 따뜻한 5년.")
    elif t_anom > 0:
        print(f"  → 2016-2020 이 평년보다 약간 ({t_anom:.2f}°C) 더 더움.")
    else:
        print(f"  → 2016-2020 이 평년보다 약간 ({t_anom:.2f}°C) 덜 더움.")

    print(f"\n다음: fit_correct.py 갱신 (4 변수 추가) + 재실행 → R² 검증")


if __name__ == "__main__":
    main()