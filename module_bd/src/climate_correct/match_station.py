"""
match_station.py — NFI 표본점 ↔ 산악기상 관측소 최근접 매칭.

D13 결정 3 구현 (수정판):
  · 좌표계 진단 완료: NFI = EPSG:5181, 컬럼 N=Y, E=X
  · 산악기상 6 관측소: 산림청 산악기상정보 기술문서 (표 9)
  · 매칭: Haversine 거리로 최근접 1개

산악기상 6 관측소 (보은, 충청북도):
  · obsid=3033, 보은 가덕산 (위도 36.52, 경도 127.57, 고도 324m)
  · obsid=3898, 보은 금단산 (위도 36.61, 경도 127.79, 고도 627m)
  · obsid=3903, 보은 염동산 (위도 36.49, 경도 127.64, 고도 282m)
  · obsid=3915, 보은 시루산 (위도 36.55, 경도 127.70, 고도 362m)
  · obsid=3917, 보은 삼승산 (위도 36.39, 경도 127.75, 고도 242m)
  · obsid=3918, 보은 노성산 (위도 36.46, 경도 127.63, 고도 314m)

알고리즘:
  1. NFI 좌표 (EPSG:5181) → WGS84 변환
  2. 표본점-관측소 Haversine 거리 계산 (6 관측소 × 102 표본점)
  3. 표본점별 최근접 관측소 선정
  4. 거리·해발고 차이 진단

출력:
  · 표본점별 (matched_obsid, distance_km, elev_diff_m)
  · 진단: 매칭 빈도, 평균/최대 거리, 해발고 차이 분포

실행: python module_bd/src/climate_correct/match_station.py
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import math
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[3]
NFI_DIR = ROOT / "module_bd" / "data" / "raw" / "nfi"
STAND_CSV = NFI_DIR / "nfi7_chungbuk_stand.csv"

# 6 산악기상 관측소 (산악기상정보 기술문서 v1.5, 표 9)
STATIONS = [
    {'obsid': 3033, 'name': '보은 가덕산', 'lat': 36.52, 'lon': 127.57, 'elev': 324},
    {'obsid': 3898, 'name': '보은 금단산', 'lat': 36.61, 'lon': 127.79, 'elev': 627},
    {'obsid': 3903, 'name': '보은 염동산', 'lat': 36.49, 'lon': 127.64, 'elev': 282},
    {'obsid': 3915, 'name': '보은 시루산', 'lat': 36.55, 'lon': 127.70, 'elev': 362},
    {'obsid': 3917, 'name': '보은 삼승산', 'lat': 36.39, 'lon': 127.75, 'elev': 242},
    {'obsid': 3918, 'name': '보은 노성산', 'lat': 36.46, 'lon': 127.63, 'elev': 314},
]

# NFI 좌표 변환: EPSG:5181 → WGS84
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
    """
    NFI 좌표 → WGS84.
    NFI csv 의 "좌표N" = Y, "좌표E" = X (always_xy=True 모드는 X, Y 순서 입력)
    """
    lon, lat = _transformer.transform(coord_e, coord_n)
    return lat, lon


def haversine_km(lat1, lon1, lat2, lon2):
    """두 점 사이 거리 (km). Haversine 공식."""
    R = 6371.0  # 지구 반경 km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def match_nearest(lat, lon, stations):
    """주어진 (lat, lon) 에 가장 가까운 station 반환 → (station_dict, distance_km)."""
    best = min(stations, key=lambda s: haversine_km(lat, lon, s['lat'], s['lon']))
    dist = haversine_km(lat, lon, best['lat'], best['lon'])
    return best, dist


def main():
    print("=" * 70)
    print("NFI 보은 표본점 ↔ 산악기상 6 관측소 최근접 매칭 (단계 3)")
    print("=" * 70)

    print("\nCSV 로딩...")
    stands = load_csv(STAND_CSV)
    boeun_stands = [s for s in stands if s.get('시군구') == '보은군']
    print(f"  보은 표본점: {len(boeun_stands)}")

    print(f"\n관측소 정보 (산악기상 docx 표 9):")
    for s in STATIONS:
        print(f"  {s['obsid']}: {s['name']:<12} ({s['lat']:.2f}, {s['lon']:.2f}, {s['elev']}m)")

    # 표본점별 매칭
    results = []
    for stand in boeun_stands:
        coord_n = safe_float(stand.get('좌표N'))
        coord_e = safe_float(stand.get('좌표E'))
        elev = safe_float(stand.get('해발고'))

        if coord_n is None or coord_e is None:
            continue

        lat, lon = nfi_to_wgs84(coord_n, coord_e)
        matched, dist_km = match_nearest(lat, lon, STATIONS)

        elev_diff = (elev - matched['elev']) if elev is not None else None

        results.append({
            'plot_id': stand['표본점번호'],
            'eupmyun': stand.get('읍면동'),
            'lat': lat,
            'lon': lon,
            'elev': elev,
            'matched_obsid': matched['obsid'],
            'matched_name': matched['name'],
            'distance_km': dist_km,
            'elev_diff_m': elev_diff,
        })

    # 결과 표 (처음 30개)
    print(f"\n표본점별 매칭 (처음 30개):")
    print(f"{'표본점':<12} {'읍면동':<8} {'위경도':<22} {'해발':<5} → "
          f"{'관측소':<12} {'거리':<7} {'해발차':<7}")
    print('-' * 90)
    for r in results[:30]:
        loc = f"({r['lat']:.3f}, {r['lon']:.3f})"
        elev_str = f"{r['elev']:.0f}m" if r['elev'] else "-"
        elev_diff_str = f"{r['elev_diff_m']:+.0f}m" if r['elev_diff_m'] is not None else "-"
        print(f"{r['plot_id']:<12} {r['eupmyun']:<8} {loc:<22} {elev_str:<5} → "
              f"{r['matched_name']:<12} {r['distance_km']:<7.2f} {elev_diff_str:<7}")
    if len(results) > 30:
        print(f"  ... (외 {len(results)-30}개)")

    # 매칭 빈도
    print(f"\n{'=' * 70}")
    print("진단:")
    print(f"{'=' * 70}")
    match_counts = Counter(r['matched_obsid'] for r in results)
    print(f"\n  관측소별 매칭 빈도:")
    for s in STATIONS:
        n = match_counts.get(s['obsid'], 0)
        bar = '█' * n
        print(f"    {s['obsid']} {s['name']:<12}: {n:>3} 표본점 {bar}")

    # 거리 통계
    dists = [r['distance_km'] for r in results]
    if dists:
        print(f"\n  거리 통계 (km):")
        print(f"    최소: {min(dists):.2f}")
        print(f"    최대: {max(dists):.2f}")
        print(f"    평균: {sum(dists)/len(dists):.2f}")
        print(f"    중앙값: {sorted(dists)[len(dists)//2]:.2f}")

    # 거리 분포
    print(f"\n  거리 분포:")
    bins = [(0, 2), (2, 4), (4, 6), (6, 8), (8, 10), (10, 15), (15, 30)]
    for lo, hi in bins:
        n = sum(1 for d in dists if lo <= d < hi)
        bar = '█' * (n // 3) if n >= 3 else '·' * n
        print(f"    {lo:>2}-{hi:<2}km: {n:>3} {bar}")

    # 해발고 차이
    elev_diffs = [r['elev_diff_m'] for r in results if r['elev_diff_m'] is not None]
    if elev_diffs:
        print(f"\n  해발고 차이 (표본점 - 관측소, m):")
        print(f"    최소: {min(elev_diffs):+.0f}")
        print(f"    최대: {max(elev_diffs):+.0f}")
        print(f"    평균: {sum(elev_diffs)/len(elev_diffs):+.0f}")
        # 분포
        bins_e = [(-500, -200), (-200, -100), (-100, 0), (0, 100), (100, 200), (200, 500)]
        print(f"\n  해발고 차이 분포:")
        for lo, hi in bins_e:
            n = sum(1 for e in elev_diffs if lo <= e < hi)
            bar = '█' * (n // 3) if n >= 3 else '·' * n
            print(f"    {lo:>+5}~{hi:<+5}: {n:>3} {bar}")

    print(f"\n{'=' * 70}")
    print("다음 단계 5: 기후 변수 (temp_anomaly, gdd_cum) 계산 + LightGBM fit")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()