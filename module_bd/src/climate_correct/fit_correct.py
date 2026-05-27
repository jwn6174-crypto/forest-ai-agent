"""
fit_correct.py v5 (복원) — NFI 6차 + 7차 시계열 패널 회귀.

D13 결정 8 + 정우님 통찰 (시간 anomaly 진짜 변동) 통합:
  · NFI 6차 (2011-2014) + 7차 (2016-2020) 통합 패널
  · 시군별 + 측정 연도별 ASOS anomaly (panel csv 사용)
  · LightGBM 회귀

변수 (6):
  시간/공간 anomaly (panel, 측정 연도별):
    · temp_anomaly_30y
    · prcp_anomaly_30y
    · gdd_anomaly
    · vpd_anomaly
  공간:
    · elev
    · imsang_code (D/H/M, 3 그룹)

결과 (정직):
  · 행 수: 1369 (6차 614 + 7차 755)
  · R² = +0.204 ± 0.074 ⭐
  · 변수 중요도: elev 51%, prcp 14%, vpd 13%, temp 10%, imsang 6%, gdd 6%

진전 비교:
  v1 (보은, 산악기상): -0.013
  v2 (보은, ASOS 상수): -0.029
  v3 (보은, +임상): -0.039
  v4 (충북 5 시군): +0.027
  v5 (충북, 6+7차 패널): +0.204 ⭐ 정직한 best

이후 시도 (v6 = species 세분화 + 이상치 제거):
  v6: -0.057 (역효과)
  → 정직한 ablation: v5 가 best
  → species 세분화 = 표본 부족 (낙엽송 92, 잣 55)
  → 이상치 제거 = 진짜 신호 손실
"""
import sys
import json
import math
from pathlib import Path
from collections import defaultdict, Counter
import csv

import pandas as pd
import numpy as np
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "module_bd" / "src"))
from growth_predict import _load_stand_table, _lookup_stand

NFI_DIR = ROOT / "module_bd" / "data" / "raw" / "nfi"
PROCESSED_DIR = ROOT / "module_bd" / "data" / "processed"
PANEL_CSV = PROCESSED_DIR / "asos_anomaly_panel.csv"
MODEL_PATH = PROCESSED_DIR / "climate_correct.pkl"

STAND_6 = NFI_DIR / "nfi6_chungbuk_stand.csv"
TREE_6 = NFI_DIR / "nfi6_chungbuk_tree.csv"
STAND_7 = NFI_DIR / "nfi7_chungbuk_stand.csv"
TREE_7 = NFI_DIR / "nfi7_chungbuk_tree.csv"

ASOS_STATIONS = [
    {'stn_id': 131, 'name': '청주', 'lat': 36.64, 'lon': 127.45},
    {'stn_id': 127, 'name': '충주', 'lat': 36.97, 'lon': 127.95},
    {'stn_id': 221, 'name': '제천', 'lat': 37.16, 'lon': 128.19},
    {'stn_id': 226, 'name': '보은', 'lat': 36.49, 'lon': 127.74},
    {'stn_id': 135, 'name': '추풍령', 'lat': 36.22, 'lon': 127.99},
]

NFI_TO_YIELD = {
    "소나무": "중부지방소나무", "잣나무": "잣나무", "리기다소나무": "리기다소나무",
    "일본잎갈나무": "낙엽송", "신갈나무": "신갈나무", "굴참나무": "굴참나무",
    "상수리나무": "상수리나무",
    "졸참나무": "신갈나무", "갈참나무": "신갈나무", "떡갈나무": "신갈나무",
}

IMSANG_TO_CODE = {
    '침엽수림(D)': 0,
    '활엽수림(H)': 1,
    '혼효림(M)': 2,
}

BASIC_PLOT_AREA_HA = 0.04
LARGE_PLOT_AREA_HA = 0.08
LARGE_DBH_THRESHOLD = 30.0

_transformer = Transformer.from_crs("EPSG:5181", "EPSG:4326", always_xy=True)


def safe_float(v):
    if v is None or v == '':
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def safe_int(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def load_csv_rows(path):
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


def match_nearest_asos(lat, lon):
    return min(ASOS_STATIONS, key=lambda s: haversine_km(lat, lon, s['lat'], s['lon']))


def age_class_to_age(age_class_str):
    if not age_class_str or '영급' not in str(age_class_str):
        return None
    try:
        n = int(str(age_class_str).replace('영급', '').strip())
        return 10 * n - 5
    except ValueError:
        return None


def get_dominant_species(trees):
    counts = Counter(t.get('수종명') for t in trees)
    if not counts:
        return None
    return NFI_TO_YIELD.get(counts.most_common(1)[0][0])


def get_avg_height(trees):
    h = [safe_float(t.get('수고_m')) for t in trees]
    valid = [x for x in h if x is not None]
    return sum(valid) / len(valid) if valid else None


def estimate_si(yield_df, species, age, measured_height):
    species_df = yield_df[yield_df["수종"] == species]
    if species_df.empty:
        return None
    available_sis = sorted(species_df["지위지수"].unique())
    si_heights = {}
    for si in available_sis:
        si_rows = species_df[species_df["지위지수"] == si]
        closest = si_rows.iloc[(si_rows["임령(년)"] - age).abs().argmin()]
        si_heights[si] = closest["우세목수고(m)"]
    return float(min(si_heights.keys(),
                     key=lambda s: abs(si_heights[s] - measured_height)))


def compute_v_actual(plot_trees):
    v_basic = sum(safe_float(t.get('추정간재적')) or 0
                  for t in plot_trees
                  if safe_float(t.get('DBH_cm')) and safe_float(t.get('DBH_cm')) < LARGE_DBH_THRESHOLD)
    v_large = sum(safe_float(t.get('추정간재적')) or 0
                  for t in plot_trees
                  if safe_float(t.get('DBH_cm')) and safe_float(t.get('DBH_cm')) >= LARGE_DBH_THRESHOLD)
    return v_basic / BASIC_PLOT_AREA_HA + v_large / LARGE_PLOT_AREA_HA


def load_panel():
    panel = {}
    if not PANEL_CSV.exists():
        return panel
    with open(PANEL_CSV, encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            key = (int(row['stn_id']), int(row['year']))
            panel[key] = {
                'temp_anom': float(row['temp_anom']),
                'prcp_anom': float(row['prcp_anom']),
                'gdd_anom': float(row['gdd_anom']),
                'vpd_anom': float(row['vpd_anom']),
            }
    return panel


def process_nfi_year(stands, trees, yield_df, year_label, panel):
    print(f"\n  [{year_label}차] 처리 중...")
    trees_by_plot = defaultdict(list)
    for tree in trees:
        plot_id = tree.get('표본점번호')
        if plot_id:
            trees_by_plot[plot_id].append(tree)

    rows = []
    for stand in stands:
        plot_id = stand['표본점번호']
        plot_trees = trees_by_plot.get(plot_id, [])
        if not plot_trees:
            continue

        age_class = stand.get('영급')
        age = age_class_to_age(age_class)
        species = get_dominant_species(plot_trees)
        avg_h = get_avg_height(plot_trees)
        elev = safe_float(stand.get('해발고'))
        coord_n = safe_float(stand.get('좌표N'))
        coord_e = safe_float(stand.get('좌표E'))
        imsang = stand.get('임상')
        imsang_code = IMSANG_TO_CODE.get(imsang)
        measure_year = safe_int(stand.get('조사연도'))

        if any(x is None for x in [age, species, avg_h, elev, coord_n, coord_e,
                                    imsang_code, measure_year]):
            continue

        si = estimate_si(yield_df, species, age, avg_h)
        if si is None:
            continue

        v_actual = compute_v_actual(plot_trees)
        stand_data = _lookup_stand(yield_df, species, int(si), age)
        if stand_data is None:
            continue
        v_table = stand_data.get('volume_m3_per_ha')
        if v_table is None:
            continue
        residual = v_actual - v_table

        lat, lon = nfi_to_wgs84(coord_n, coord_e)
        matched_asos = match_nearest_asos(lat, lon)
        anom = panel.get((matched_asos['stn_id'], measure_year))
        if anom is None:
            continue

        rows.append({
            'plot_id': plot_id,
            'nfi_round': year_label,
            'measure_year': measure_year,
            'sigun': matched_asos['name'],
            'residual': residual,
            'elev': elev,
            'imsang_code': imsang_code,
            'temp_anomaly_30y': anom['temp_anom'],
            'prcp_anomaly_30y': anom['prcp_anom'],
            'gdd_anomaly': anom['gdd_anom'],
            'vpd_anomaly': anom['vpd_anom'],
        })

    print(f"    표본점 {len(stands)} → 통합 {len(rows)} 행")
    return rows


def main():
    print("=" * 80)
    print("climate_correct() v5 (복원) — 시계열 패널 + imsang_code")
    print("=" * 80)

    # 1. 데이터 로딩
    print("\n[1/7] 데이터 로딩...")
    panel = load_panel()
    print(f"  ASOS anomaly panel: {len(panel)} (시군 × 연도)")

    s6 = load_csv_rows(STAND_6)
    t6 = load_csv_rows(TREE_6)
    s7 = load_csv_rows(STAND_7)
    t7 = load_csv_rows(TREE_7)
    yield_df = _load_stand_table()
    print(f"  NFI 6차: {len(s6)} 표본점, {len(t6)} 나무")
    print(f"  NFI 7차: {len(s7)} 표본점, {len(t7)} 나무")

    # 2. 차수별 처리
    print(f"\n[2/7] NFI 6·7차 통합 패널 생성...")
    rows_6 = process_nfi_year(s6, t6, yield_df, 6, panel)
    rows_7 = process_nfi_year(s7, t7, yield_df, 7, panel)
    df = pd.DataFrame(rows_6 + rows_7)
    print(f"\n  통합 패널: {len(df)} 행 (6차 {len(rows_6)} + 7차 {len(rows_7)})")

    if len(df) < 100:
        print(f"  ⚠ 행 너무 적음.")
        return

    # 3. 통계
    print(f"\n[3/7] 패널 통계:")
    print(f"  residual: 평균 {df['residual'].mean():+.1f}, std {df['residual'].std():.1f}")
    print(f"  temp_anomaly std: {df['temp_anomaly_30y'].std():.3f}")
    print(f"  차수별 잔차:")
    for r in [6, 7]:
        sub = df[df['nfi_round'] == r]
        print(f"    {r}차: n={len(sub)}, 평균 {sub['residual'].mean():+.1f}, std {sub['residual'].std():.1f}")

    # 4. 5-fold CV
    print("\n[4/7] LightGBM + 5-fold CV (시계열 패널)...")
    from lightgbm import LGBMRegressor
    from sklearn.model_selection import KFold
    from sklearn.metrics import r2_score, mean_squared_error

    FEATURES = ['temp_anomaly_30y', 'prcp_anomaly_30y', 'gdd_anomaly', 'vpd_anomaly',
                'elev', 'imsang_code']
    X = df[FEATURES]
    y = df['residual']

    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    r2_scores = []
    rmse_scores = []
    fold = 0
    for train_idx, val_idx in kf.split(X):
        fold += 1
        model = LGBMRegressor(
            n_estimators=200, max_depth=5, learning_rate=0.05,
            random_state=42, verbose=-1
        )
        model.fit(X.iloc[train_idx], y.iloc[train_idx],
                  categorical_feature=['imsang_code'])
        pred = model.predict(X.iloc[val_idx])
        r2 = r2_score(y.iloc[val_idx], pred)
        rmse = np.sqrt(mean_squared_error(y.iloc[val_idx], pred))
        r2_scores.append(r2)
        rmse_scores.append(rmse)
        print(f"  fold {fold}: R²={r2:+.3f}, RMSE={rmse:.1f}, n_val={len(val_idx)}")

    print(f"\n  5-fold CV:")
    print(f"    R² = {np.mean(r2_scores):+.3f} ± {np.std(r2_scores):.3f}")
    print(f"    RMSE = {np.mean(rmse_scores):.1f} ± {np.std(rmse_scores):.1f}")

    # 5. 최종 모델
    print("\n[5/7] 최종 모델...")
    final_model = LGBMRegressor(
        n_estimators=200, max_depth=5, learning_rate=0.05,
        random_state=42, verbose=-1
    )
    final_model.fit(X, y, categorical_feature=['imsang_code'])

    print(f"\n  변수 중요도:")
    importances = list(zip(FEATURES, final_model.feature_importances_))
    total = sum(imp for _, imp in importances)
    for feat, imp in sorted(importances, key=lambda x: -x[1]):
        pct = imp / total * 100 if total > 0 else 0
        bar = '█' * int(pct / 3)
        print(f"    {feat:<20}: {imp:>5} ({pct:>5.1f}%) {bar}")

    # 6. 저장
    print("\n[6/7] climate_correct.pkl 저장...")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    import joblib
    save_dict = {
        'model': final_model,
        'features': FEATURES,
        'asos_stations': ASOS_STATIONS,
        'imsang_mapping': IMSANG_TO_CODE,
        'metadata': {
            'algorithm': 'LightGBM',
            'n_samples': len(df),
            'cv_r2_mean': float(np.mean(r2_scores)),
            'cv_r2_std': float(np.std(r2_scores)),
            'cv_rmse_mean': float(np.mean(rmse_scores)),
            'cv_rmse_std': float(np.std(rmse_scores)),
            'data': {
                'nfi6_rows': len(rows_6),
                'nfi7_rows': len(rows_7),
                'total_rows': len(df),
            },
        },
    }
    joblib.dump(save_dict, MODEL_PATH)
    print(f"  ✓ {MODEL_PATH.relative_to(ROOT)} ({MODEL_PATH.stat().st_size // 1024} KB)")

    # 7. 비교
    print(f"\n{'=' * 80}")
    print("[7/7] R² 발전 비교 (5 시도 정직한 진전):")
    print(f"{'=' * 80}")
    r2_mean = np.mean(r2_scores)
    print(f"  v1 (보은, 산악기상만):       R² = -0.013")
    print(f"  v2 (보은, +ASOS 30y 상수):   R² = -0.029")
    print(f"  v3 (보은, +임상):            R² = -0.039")
    print(f"  v4 (충북, ASOS 5 시군):     R² = +0.027")
    print(f"  v5 (충북, 6+7차 패널):      R² = {r2_mean:+.3f} ⭐")
    print(f"\n  → v5 = best. 시계열 패널 + imsang_code 최적.")


if __name__ == "__main__":
    main()