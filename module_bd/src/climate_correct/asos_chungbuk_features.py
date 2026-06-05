"""
asos_chungbuk_features.py — 충북 5 ASOS 시군별 평년·anomaly 비교.

목적:
  · 5 관측소 1991-2020 평년 + 2016-2020 평균 + anomaly
  · 공간 변동 (시군간 평년 차이) 진단
  · 시간 변동 (anomaly 패턴) 진단

→ 변동 충분하면 NFI 충북 매칭 회귀 진행
→ 부족하면 다른 길
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ASOS_DIR = ROOT / "module_bd" / "data" / "raw" / "asos"

GDD_BASE_TEMP = 5.0
NORMAL_YEARS = list(range(1991, 2021))
NFI_YEARS = list(range(2016, 2021))

STATIONS = [
    (131, '청주', 36.64, 127.45),
    (127, '충주', 36.97, 127.95),
    (221, '제천', 37.16, 128.19),
    (226, '보은', 36.49, 127.74),
    (135, '추풍령', 36.22, 127.99),
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
    yrs = [r for r in records if r['year'] == year]
    if len(yrs) < 300:
        return None
    temps = [r['avg_ta'] for r in yrs if r['avg_ta'] is not None]
    return {
        'avg_temp': sum(temps)/len(temps) if temps else None,
        'sum_rn': sum(r['sum_rn'] for r in yrs),
        'max_vpd': max([r['vpd'] for r in yrs if r['vpd'] is not None], default=None),
        'gdd_cum': sum(max(0, r['avg_ta'] - GDD_BASE_TEMP) for r in yrs if r['avg_ta'] is not None),
    }


def main():
    print("=" * 80)
    print("충북 5 ASOS 시군별 평년·anomaly 비교")
    print("=" * 80)

    print(f"\n{'관측소':<10} {'위도':<7} {'경도':<8} | {'1991-20 평년':<30} | {'2016-20 anomaly':<25}")
    print(f"{'':<10} {'':<7} {'':<8} | {'기온':<8} {'강수':<8} {'GDD':<8} | {'temp':<7} {'gdd':<7} {'vpd':<7}")
    print('-' * 100)

    results = []
    for stn_id, name, lat, lon in STATIONS:
        recs = load_asos(stn_id)
        if not recs:
            print(f"{name}: 자료 없음")
            continue

        annual_normal = [annual_stats(recs, y) for y in NORMAL_YEARS]
        annual_nfi = [annual_stats(recs, y) for y in NFI_YEARS]

        def avg(stats_list, key):
            valid = [s[key] for s in stats_list if s and s[key] is not None]
            return sum(valid) / len(valid) if valid else None

        normal_temp = avg(annual_normal, 'avg_temp')
        normal_rain = avg(annual_normal, 'sum_rn')
        normal_gdd = avg(annual_normal, 'gdd_cum')
        normal_max_vpd = avg(annual_normal, 'max_vpd')

        nfi_temp = avg(annual_nfi, 'avg_temp')
        nfi_rain = avg(annual_nfi, 'sum_rn')
        nfi_gdd = avg(annual_nfi, 'gdd_cum')
        nfi_max_vpd = avg(annual_nfi, 'max_vpd')

        temp_anom = nfi_temp - normal_temp
        prcp_anom = nfi_rain - normal_rain
        gdd_anom = nfi_gdd - normal_gdd
        vpd_anom = nfi_max_vpd - normal_max_vpd

        results.append({
            'name': name, 'stn_id': stn_id, 'lat': lat, 'lon': lon,
            'normal_temp': normal_temp, 'normal_rain': normal_rain,
            'normal_gdd': normal_gdd, 'normal_vpd': normal_max_vpd,
            'temp_anom': temp_anom, 'prcp_anom': prcp_anom,
            'gdd_anom': gdd_anom, 'vpd_anom': vpd_anom,
        })

        print(f"{name:<10} {lat:<7.2f} {lon:<8.2f} | "
              f"{normal_temp:<8.2f} {normal_rain:<8.0f} {normal_gdd:<8.0f} | "
              f"{temp_anom:<+7.3f} {gdd_anom:<+7.0f} {vpd_anom:<+7.3f}")

    # 변동 분석
    if results:
        print(f"\n{'=' * 80}")
        print("공간 변동 (시군간 평년 차이):")
        print(f"{'=' * 80}")
        temps = [r['normal_temp'] for r in results]
        rains = [r['normal_rain'] for r in results]
        gdds = [r['normal_gdd'] for r in results]
        print(f"  연평균 기온: {min(temps):.2f} ~ {max(temps):.2f} (차이 {max(temps)-min(temps):.2f}°C)")
        print(f"  연 강수량: {min(rains):.0f} ~ {max(rains):.0f} (차이 {max(rains)-min(rains):.0f} mm)")
        print(f"  연 GDD: {min(gdds):.0f} ~ {max(gdds):.0f} (차이 {max(gdds)-min(gdds):.0f})")

        print(f"\n{'=' * 80}")
        print("시간 변동 (시군별 anomaly):")
        print(f"{'=' * 80}")
        anoms = [r['temp_anom'] for r in results]
        print(f"  temp_anomaly_30y: {min(anoms):+.3f} ~ {max(anoms):+.3f}")
        print(f"     평균 {sum(anoms)/len(anoms):+.3f}, 표준편차 {(sum((a-sum(anoms)/len(anoms))**2 for a in anoms)/len(anoms))**0.5:.3f}")

        # 의미 분석
        print(f"\n{'=' * 80}")
        print("의미 분석:")
        print(f"{'=' * 80}")
        spatial_range = max(temps) - min(temps)
        anom_std = (sum((a-sum(anoms)/len(anoms))**2 for a in anoms)/len(anoms))**0.5
        if spatial_range > 1.5:
            print(f"  ✓ 공간 변동 {spatial_range:.2f}°C → 회귀 input 충분")
        else:
            print(f"  ⚠ 공간 변동 {spatial_range:.2f}°C → 작음")
        if anom_std > 0.1:
            print(f"  ✓ anomaly std {anom_std:.3f} → 시군별 다름")
        else:
            print(f"  ⚠ anomaly std {anom_std:.3f} → 시군별 비슷")


if __name__ == "__main__":
    main()