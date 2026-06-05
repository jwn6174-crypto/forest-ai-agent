"""
climate_features_panel.py — 시기별 + 시군별 ASOS anomaly 패널.

목적:
  · NFI 5차 (2006-2010) + 6차 (2011-2014) + 7차 (2016-2020) 측정 연도별 ASOS anomaly
  · 5 시군 ASOS × 14 년 = 최대 70 행 패널 데이터
  · 평년: 1991-2020 (30년)

알고리즘:
  1. 시군별 30년 평년 (temp, prcp, gdd, vpd_max) — 한 번 계산
  2. 각 측정 연도의 시군별 값 (temp, prcp, gdd, vpd_max) — 14 년 × 5 시군
  3. anomaly = (측정 연도) - 평년

출력:
  · data/processed/asos_anomaly_panel.csv
  · 컬럼: stn_id, sigun, year, temp_anom, prcp_anom, gdd_anom, vpd_anom

검증:
  · 시간 변동: 5차(2008) → 7차(2018) 같은 시군의 temp_anom 차이 (10년 span)
  · 공간 변동: 같은 해 시군별 temp_anom 차이
"""
import json
import math
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ASOS_DIR = ROOT / "module_bd" / "data" / "raw" / "asos"
OUT_DIR = ROOT / "module_bd" / "data" / "processed"
OUT_PATH = OUT_DIR / "asos_anomaly_panel.csv"

GDD_BASE_TEMP = 5.0
NORMAL_YEARS = list(range(1991, 2021))  # 1991-2020 평년 (30년)

# NFI 측정 연도 (5차 2006-2010 + 6차 2011-2014 + 7차 2016-2020)
NFI_MEASURE_YEARS = [2006, 2007, 2008, 2009, 2010,
                     2011, 2012, 2013, 2014,
                     2016, 2017, 2018, 2019, 2020]

# 차수별 측정 연도 (검증 출력용)
NFI5_YEARS = range(2006, 2011)   # 2006-2010
NFI6_YEARS = range(2011, 2015)   # 2011-2014
NFI7_YEARS = range(2016, 2021)   # 2016-2020

# 5 ASOS 시군
STATIONS = [
    (131, '청주'),
    (127, '충주'),
    (221, '제천'),
    (226, '보은'),
    (135, '추풍령'),
]


def safe_float(v):
    if v is None or v == '':
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def saturation_vapor_pressure(temp_c):
    if temp_c is None:
        return None
    return 0.6108 * math.exp(17.27 * temp_c / (temp_c + 237.3))


def calc_vpd(avg_ta, avg_td):
    es = saturation_vapor_pressure(avg_ta)
    ea = saturation_vapor_pressure(avg_td)
    if es is None or ea is None:
        return None
    return max(0, es - ea)


def load_asos(stn_id):
    path = ASOS_DIR / f"asos_{stn_id}_1991_2020.jsonl"
    if not path.exists():
        return []
    records = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            tm = item.get('tm')
            if not tm:
                continue
            year = int(tm[:4])
            avg_ta = safe_float(item.get('avgTa'))
            avg_td = safe_float(item.get('avgTd'))
            sum_rn = safe_float(item.get('sumRn')) or 0.0
            records.append({
                'year': year,
                'avg_ta': avg_ta,
                'sum_rn': sum_rn,
                'vpd': calc_vpd(avg_ta, avg_td),
            })
    return records


def annual_stats(records, year):
    """한 해의 통계 (avg_temp, sum_rn, max_vpd, gdd_cum)."""
    yrs = [r for r in records if r['year'] == year]
    if len(yrs) < 300:
        return None
    temps = [r['avg_ta'] for r in yrs if r['avg_ta'] is not None]
    return {
        'avg_temp': sum(temps) / len(temps) if temps else None,
        'sum_rn': sum(r['sum_rn'] for r in yrs),
        'max_vpd': max([r['vpd'] for r in yrs if r['vpd'] is not None], default=None),
        'gdd_cum': sum(max(0, r['avg_ta'] - GDD_BASE_TEMP)
                       for r in yrs if r['avg_ta'] is not None),
    }


def compute_normal(records):
    """1991-2020 평년 (4 변수)."""
    annual = [annual_stats(records, y) for y in NORMAL_YEARS]
    valid = [a for a in annual if a]

    def avg(key):
        vals = [a[key] for a in valid if a[key] is not None]
        return sum(vals) / len(vals) if vals else None

    return {
        'avg_temp': avg('avg_temp'),
        'sum_rn': avg('sum_rn'),
        'max_vpd': avg('max_vpd'),
        'gdd_cum': avg('gdd_cum'),
    }


def main():
    print("=" * 80)
    print("시기별 + 시군별 ASOS anomaly 패널 산출 (5+6+7차 시계열)")
    print("=" * 80)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. 시군별 평년 계산
    print("\n[1/3] 시군별 1991-2020 평년 산출...")
    print(f"{'시군':<8} {'기온':<7} {'강수':<8} {'GDD':<7} {'최대VPD':<8}")
    print('-' * 50)

    station_data = {}  # stn_id → (records, normal)
    for stn_id, name in STATIONS:
        records = load_asos(stn_id)
        if not records:
            print(f"  ⚠ {name}: 자료 없음")
            continue
        normal = compute_normal(records)
        station_data[stn_id] = {'name': name, 'records': records, 'normal': normal}
        print(f"{name:<8} {normal['avg_temp']:<7.2f} {normal['sum_rn']:<8.0f} "
              f"{normal['gdd_cum']:<7.0f} {normal['max_vpd']:<8.3f}")

    # 2. 측정 연도별 anomaly 산출
    print(f"\n[2/3] 측정 연도별 anomaly 산출 (최대 14년 × 5 시군 = 70 행)...")
    panel = []
    skipped = []
    for stn_id, data in station_data.items():
        for year in NFI_MEASURE_YEARS:
            stats = annual_stats(data['records'], year)
            if not stats:
                skipped.append((data['name'], year))
                continue
            row = {
                'stn_id': stn_id,
                'sigun': data['name'],
                'year': year,
                'temp_anom': stats['avg_temp'] - data['normal']['avg_temp'],
                'prcp_anom': stats['sum_rn'] - data['normal']['sum_rn'],
                'gdd_anom': stats['gdd_cum'] - data['normal']['gdd_cum'],
                'vpd_anom': stats['max_vpd'] - data['normal']['max_vpd'],
            }
            panel.append(row)
    print(f"  패널 행: {len(panel)}")
    if skipped:
        print(f"  결측 (300일 미만 skip): {len(skipped)} — {skipped}")

    # 3. CSV 저장
    print(f"\n[3/3] CSV 저장...")
    with open(OUT_PATH, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['stn_id', 'sigun', 'year',
                                               'temp_anom', 'prcp_anom',
                                               'gdd_anom', 'vpd_anom'])
        writer.writeheader()
        writer.writerows(panel)
    print(f"  ✓ {OUT_PATH.relative_to(ROOT)}")

    # 검증 — 시기별 anomaly 표
    print(f"\n{'=' * 90}")
    print("검증 — 시기별 + 시군별 temp_anomaly:")
    print(f"{'=' * 90}")
    print(f"{'시군':<8} ", end='')
    for y in NFI_MEASURE_YEARS:
        print(f"{y:>6}", end='')
    print()
    print('-' * 92)

    for stn_id, data in station_data.items():
        print(f"{data['name']:<8} ", end='')
        for y in NFI_MEASURE_YEARS:
            row = next((p for p in panel if p['stn_id'] == stn_id and p['year'] == y), None)
            if row:
                print(f"{row['temp_anom']:>+6.2f}", end='')
            else:
                print(f"{'?':>6}", end='')
        print()

    # 시간 변동 — 5차 vs 6차 vs 7차 (10년 span)
    print(f"\n{'=' * 80}")
    print("시간 변동 (5차 2008 vs 6차 2012.5 vs 7차 2018, 10년 span):")
    print(f"{'=' * 80}")
    for stn_id, data in station_data.items():
        nfi5 = [p['temp_anom'] for p in panel
                if p['stn_id'] == stn_id and p['year'] in NFI5_YEARS]
        nfi6 = [p['temp_anom'] for p in panel
                if p['stn_id'] == stn_id and p['year'] in NFI6_YEARS]
        nfi7 = [p['temp_anom'] for p in panel
                if p['stn_id'] == stn_id and p['year'] in NFI7_YEARS]
        parts = [f"  {data['name']}:"]
        if nfi5:
            parts.append(f"5차 {sum(nfi5)/len(nfi5):+.3f}C")
        if nfi6:
            parts.append(f"6차 {sum(nfi6)/len(nfi6):+.3f}C")
        if nfi7:
            parts.append(f"7차 {sum(nfi7)/len(nfi7):+.3f}C")
        if nfi5 and nfi7:
            parts.append(f"(5->7 차이 {sum(nfi7)/len(nfi7)-sum(nfi5)/len(nfi5):+.3f}C)")
        print(", ".join(parts))

    # 전체 변동 통계
    print(f"\n{'=' * 80}")
    print("전체 패널 변동 통계:")
    print(f"{'=' * 80}")
    temps = [p['temp_anom'] for p in panel]
    if temps:
        mean_t = sum(temps) / len(temps)
        std_t = (sum((t - mean_t)**2 for t in temps) / len(temps)) ** 0.5
        print(f"  temp_anom 범위: {min(temps):+.3f} ~ {max(temps):+.3f}")
        print(f"  표준편차: {std_t:.3f}")
        print(f"  → 시계열 회귀의 input 변동 (5차 추가로 10년 span 확대).")


if __name__ == "__main__":
    main()