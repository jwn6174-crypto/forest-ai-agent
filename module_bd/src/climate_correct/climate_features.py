"""
climate_features.py — 표본점별 기후 변수 산출 (단계 5a).

D13 결정 2 정직 구현:
  사용 가능: temp_anomaly (4년 평균), gdd_cum (생장한계 5°C 누적), 해발고
  미수집: prcp_anomaly_30y, vpd_max → D15+ 보강 예정

알고리즘:
  1. match_station.py 의 매칭 결과 → 표본점별 matched_obsid
  2. 6 obsid 의 jsonl 로딩 → 일평균 기온 시계열
  3. 관측소별 연평균 + GDD 누적 산출
  4. temp_anomaly = 관측소 평균 - 6 관측소 전체 평균
  5. 표본점별 (temp_anomaly, gdd_cum, 해발고) 출력

GDD (Growing Degree Days):
  · 기저온도 5°C (한국 임업 표준)
  · 일평균 - 5 (양수만, 음수는 0)
  · 매년 누적, 4년 평균

데이터:
  · module_bd/data/raw/mt_weather/obs_<obsid>.jsonl (6 관측소)
  · module_bd/data/raw/nfi/nfi7_chungbuk_stand.csv

실행: python module_bd/src/climate_correct/climate_features.py
"""
import json
from pathlib import Path
from collections import defaultdict
import csv
from datetime import datetime
import math
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[3]
NFI_DIR = ROOT / "module_bd" / "data" / "raw" / "nfi"
MT_DIR = ROOT / "module_bd" / "data" / "raw" / "mt_weather"
STAND_CSV = NFI_DIR / "nfi7_chungbuk_stand.csv"

# 6 관측소 (match_station.py 와 동일)
STATIONS = [
    {'obsid': 3033, 'name': '보은 가덕산', 'lat': 36.52, 'lon': 127.57, 'elev': 324},
    {'obsid': 3898, 'name': '보은 금단산', 'lat': 36.61, 'lon': 127.79, 'elev': 627},
    {'obsid': 3903, 'name': '보은 염동산', 'lat': 36.49, 'lon': 127.64, 'elev': 282},
    {'obsid': 3915, 'name': '보은 시루산', 'lat': 36.55, 'lon': 127.70, 'elev': 362},
    {'obsid': 3917, 'name': '보은 삼승산', 'lat': 36.39, 'lon': 127.75, 'elev': 242},
    {'obsid': 3918, 'name': '보은 노성산', 'lat': 36.46, 'lon': 127.63, 'elev': 314},
]

# GDD 기저온도 (한국 임업 표준)
GDD_BASE_TEMP = 5.0

# NFI 좌표 변환
_transformer = Transformer.from_crs("EPSG:5181", "EPSG:4326", always_xy=True)


def safe_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load_csv(path):
    if not path.exists():
        return []
    with open(path, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def nfi_to_wgs84(coord_n, coord_e):
    lon, lat = _transformer.transform(coord_e, coord_n)
    return lat, lon


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def match_nearest_obsid(lat, lon):
    """가장 가까운 관측소 obsid 반환."""
    best = min(STATIONS, key=lambda s: haversine_km(lat, lon, s['lat'], s['lon']))
    return best['obsid']


def load_station_temps(obsid):
    """
    관측소 jsonl → {date: [hourly temps]} 반환.

    각 줄 형식: {"data": {"tm": "2022-01-01 04:00", "tm2m": -11.9, ...}}
    """
    path = MT_DIR / f"obs_{obsid}.jsonl"
    if not path.exists():
        return {}

    daily = defaultdict(list)
    with open(path, encoding='utf-8') as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not rec.get('ok'):
                continue
            data = rec.get('data', {})
            tm = data.get('tm')
            tm2m = data.get('tm2m')
            if tm is None or tm2m is None:
                continue
            try:
                # "2022-01-01 04:00" → date "2022-01-01"
                date_str = tm.split(' ')[0]
                daily[date_str].append(float(tm2m))
            except (ValueError, IndexError):
                continue
    return daily


def daily_means(daily_temps):
    """{date: [hourly]} → {date: mean}."""
    return {d: sum(ts)/len(ts) for d, ts in daily_temps.items() if ts}


def annual_temp(daily_means_dict, year):
    """해당 연도 일평균 → 연평균. 결측 시 None."""
    year_str = f"{year}-"
    year_days = [v for d, v in daily_means_dict.items() if d.startswith(year_str)]
    if len(year_days) < 300:  # 300일 미만이면 결측 처리
        return None
    return sum(year_days) / len(year_days)


def annual_gdd(daily_means_dict, year, base_temp=GDD_BASE_TEMP):
    """해당 연도 GDD 누적."""
    year_str = f"{year}-"
    year_days = [v for d, v in daily_means_dict.items() if d.startswith(year_str)]
    if len(year_days) < 300:
        return None
    return sum(max(0, t - base_temp) for t in year_days)


def main():
    print("=" * 70)
    print("표본점별 기후 변수 산출 (단계 5a)")
    print("=" * 70)

    # 1. 관측소별 기온 시계열 로딩
    print("\n[1/4] 관측소별 기온 시계열 로딩...")
    station_temps = {}  # obsid → daily means dict
    for s in STATIONS:
        obsid = s['obsid']
        daily_raw = load_station_temps(obsid)
        daily_mean = daily_means(daily_raw)
        station_temps[obsid] = daily_mean
        print(f"  {obsid} {s['name']}: {len(daily_mean)} 일")

    # 2. 관측소별 연평균 + GDD (4년)
    print("\n[2/4] 관측소별 연평균·GDD 산출 (2022-2025)...")
    YEARS = [2022, 2023, 2024, 2025]
    station_stats = {}  # obsid → (avg_temp_4y, avg_gdd_4y)
    for s in STATIONS:
        obsid = s['obsid']
        temps = [annual_temp(station_temps[obsid], y) for y in YEARS]
        gdds = [annual_gdd(station_temps[obsid], y) for y in YEARS]
        valid_temps = [t for t in temps if t is not None]
        valid_gdds = [g for g in gdds if g is not None]
        if valid_temps and valid_gdds:
            avg_t = sum(valid_temps) / len(valid_temps)
            avg_g = sum(valid_gdds) / len(valid_gdds)
            station_stats[obsid] = (avg_t, avg_g)
            print(f"  {obsid} {s['name']:<12} ({s['elev']}m): "
                  f"4년 평균 {avg_t:.2f}°C, GDD {avg_g:.0f}, 유효 {len(valid_temps)}/4년")

    # 3. 6 관측소 전체 평균 (anomaly 기준)
    if station_stats:
        boeun_avg_temp = sum(t for t, _ in station_stats.values()) / len(station_stats)
        boeun_avg_gdd = sum(g for _, g in station_stats.values()) / len(station_stats)
        print(f"\n  보은 6 관측소 평균: {boeun_avg_temp:.2f}°C, GDD {boeun_avg_gdd:.0f}")

    # 4. 표본점별 매칭 + 기후 변수
    print("\n[3/4] NFI 표본점별 매칭...")
    stands = load_csv(STAND_CSV)
    boeun_stands = [s for s in stands if s.get('시군구') == '보은군']
    print(f"  보은 표본점: {len(boeun_stands)}")

    print("\n[4/4] 표본점별 기후 변수 산출...")
    results = []
    for stand in boeun_stands:
        coord_n = safe_float(stand.get('좌표N'))
        coord_e = safe_float(stand.get('좌표E'))
        elev = safe_float(stand.get('해발고'))
        if coord_n is None or coord_e is None:
            continue

        lat, lon = nfi_to_wgs84(coord_n, coord_e)
        matched_obsid = match_nearest_obsid(lat, lon)
        stats = station_stats.get(matched_obsid)
        if stats is None:
            continue
        temp, gdd = stats

        temp_anomaly = temp - boeun_avg_temp

        results.append({
            'plot_id': stand['표본점번호'],
            'eupmyun': stand.get('읍면동'),
            'elev': elev,
            'matched_obsid': matched_obsid,
            'temp_avg': temp,
            'temp_anomaly': temp_anomaly,
            'gdd_cum': gdd,
        })

    # 결과 (처음 30개)
    print(f"\n표본점별 기후 변수 (처음 30개):")
    print(f"{'표본점':<12} {'읍면동':<8} {'해발':<6} {'관측소':<6} {'4y평균':<8} {'anomaly':<9} {'GDD':<7}")
    print('-' * 70)
    for r in results[:30]:
        elev_str = f"{r['elev']:.0f}m" if r['elev'] else "-"
        print(f"{r['plot_id']:<12} {r['eupmyun']:<8} {elev_str:<6} {r['matched_obsid']:<6} "
              f"{r['temp_avg']:<8.2f} {r['temp_anomaly']:+8.2f} {r['gdd_cum']:<7.0f}")
    if len(results) > 30:
        print(f"  ... (외 {len(results)-30}개)")

    # 통계
    print(f"\n{'=' * 70}")
    print("기후 변수 통계 (전체 표본점):")
    print(f"{'=' * 70}")

    temps = [r['temp_avg'] for r in results]
    anomalies = [r['temp_anomaly'] for r in results]
    gdds = [r['gdd_cum'] for r in results]
    elevs = [r['elev'] for r in results if r['elev'] is not None]

    print(f"\n  처리된 표본점: {len(results)}")
    if temps:
        print(f"\n  기온 (°C):")
        print(f"    평균: {sum(temps)/len(temps):.2f}, 범위: {min(temps):.2f} ~ {max(temps):.2f}")
    if anomalies:
        print(f"\n  Temp anomaly (°C, 보은 6 관측소 평균 대비):")
        print(f"    평균: {sum(anomalies)/len(anomalies):+.3f}")
        print(f"    범위: {min(anomalies):+.2f} ~ {max(anomalies):+.2f}")
        print(f"    표준편차: {(sum((a-sum(anomalies)/len(anomalies))**2 for a in anomalies)/len(anomalies))**0.5:.3f}")
    if gdds:
        print(f"\n  GDD (5°C 기저, °C·day):")
        print(f"    평균: {sum(gdds)/len(gdds):.0f}")
        print(f"    범위: {min(gdds):.0f} ~ {max(gdds):.0f}")
    if elevs:
        print(f"\n  해발고 (m):")
        print(f"    평균: {sum(elevs)/len(elevs):.0f}, 범위: {min(elevs):.0f} ~ {max(elevs):.0f}")

    print(f"\n{'=' * 70}")
    print("다음 단계 5b (fit_correct.py): residual ~ 기후 + 해발고 LightGBM 회귀")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()