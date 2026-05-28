"""
growth_predict.py
모듈 B 의 핵심 API. 임분수확표 기반 성장 예측.

주요 함수:
- lookup_volume(species, bark, dbh, height) → 개별 나무 재적 (Ⅱ장 입목수간재적표 사용)
- growth_predict(species, site_index, age_now, T) → 임분 전체 성장 예측 (Ⅶ장 임분수확표 사용)

데이터 출처:
- module_bd/data/interim/yield_table_full.parquet (Ⅱ장 입목수간재적표, 16,163 값)
- module_bd/data/interim/yield_table_stand.parquet (Ⅶ장 임분수확표, 576 행)
- module_bd/data/processed/climate_correct.pkl (D13/D16/D17 기후 보정 모델, v8)
- module_bd/data/processed/nex_scenario_anomaly.csv (D15 NEX-GDDP SSP anomaly)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from functools import lru_cache

import json
import csv

# D14 등급분포 (Weibull) 통합
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from grade_distribution import grade_distribution
    _HAS_GRADE = True
except ImportError:
    _HAS_GRADE = False

ROOT = Path(__file__).resolve().parents[2]
PARQUET_VOLUME = ROOT / "module_bd" / "data" / "interim" / "yield_table_full.parquet"
PARQUET_STAND = ROOT / "module_bd" / "data" / "interim" / "yield_table_stand.parquet"

CARBON_PATH = ROOT / "module_bd" / "data" / "raw" / "carbon" / "carbon_uptake_2003.json"

# D15 기후 보정 (climate_correct.pkl + NEX-GDDP SSP anomaly)
CLIMATE_MODEL_PATH = ROOT / "module_bd" / "data" / "processed" / "climate_correct.pkl"
NEX_ANOMALY_PATH = ROOT / "module_bd" / "data" / "processed" / "nex_scenario_anomaly.csv"
# 학습 데이터 (외삽 감지용 — climate_correct 가 학습한 anomaly 범위)
PANEL_ANOMALY_PATH = ROOT / "module_bd" / "data" / "processed" / "asos_anomaly_panel.csv"

# growth_predict 대문자 시나리오 → NEX 소문자
SCENARIO_TO_NEX = {
    "SSP245": "ssp245",
    "SSP585": "ssp585",
}

# 작은 표 수종 (DRAFT, 입목수간재적표)
SMALL_TABLE_SPECIES = {"해송", "삼나무", "이태리포플러"}

# 임분수확표 없는 수종 (Ⅶ장에 없음, 잠정 데이터 또는 제외)
STAND_NO_DATA = {"해송", "삼나무", "이태리포플러"}
STAND_TENTATIVE = {"자작나무", "백합나무"}  # (잠정) 표시

# 침엽수 수종 (임상 추정용 — D14/D15 공통)
CONIFERS = {"강원지방소나무", "중부지방소나무", "소나무", "잣나무",
            "낙엽송", "리기다소나무", "편백", "곰솔", "삼나무", "해송"}


# ============================================================
# Ⅱ장 입목수간재적표 — 개별 나무 재적 lookup
# ============================================================

@lru_cache(maxsize=1)
def _load_volume_table() -> pd.DataFrame:
    if not PARQUET_VOLUME.exists():
        raise FileNotFoundError(f"입목수간재적표 없음: {PARQUET_VOLUME}")
    df = pd.read_parquet(PARQUET_VOLUME)
    print(f"📊 입목수간재적표 로드: {len(df):,} 행 (Ⅱ장)")
    return df


def lookup_volume(
    species: str,
    bark: str = "수피포함",
    dbh: float = None,
    height: float = None,
    use_draft: bool = False,
) -> dict:
    """
    개별 나무의 재적 lookup (Ⅱ장 입목수간재적표).

    Args:
        species: 수종명
        bark: "수피포함" (기본) 또는 "수피제외"
        dbh: 흉고직경 (cm)
        height: 수고 (m)
        use_draft: True 면 DRAFT 데이터도 사용 (해송/삼나무/이태리포플러)

    Returns:
        dict: {volume, lookup_dbh, lookup_height, quality, warning}
    """
    df = _load_volume_table()

    mask = (df["수종"] == species) & (df["수피여부"] == bark)
    if not use_draft:
        mask &= (df["품질"] == "OK")
    species_df = df[mask]

    if species_df.empty:
        if species in SMALL_TABLE_SPECIES:
            return {
                "volume": None, "lookup_dbh": None, "lookup_height": None,
                "quality": "DRAFT",
                "warning": f"{species}는 DRAFT만 있음. use_draft=True 로 사용 가능",
            }
        return {
            "volume": None, "lookup_dbh": None, "lookup_height": None,
            "quality": "ERROR",
            "warning": f"'{species}' 수종 없음. 사용 가능: {sorted(df['수종'].unique())}",
        }

    # 가장 가까운 DBH, 수고 찾기
    available_dbhs = sorted(species_df["흉고직경(cm)"].unique())
    closest_dbh = min(available_dbhs, key=lambda x: abs(x - dbh))

    height_df = species_df[species_df["흉고직경(cm)"] == closest_dbh]
    available_heights = sorted(height_df["수고(m)"].unique())
    closest_height = min(available_heights, key=lambda x: abs(x - height))

    row = height_df[height_df["수고(m)"] == closest_height].iloc[0]
    volume = row["재적(m³)"]
    quality = row["품질"]

    warning = None
    if pd.isna(volume):
        warning = f"빈 셀 (DBH {closest_dbh}cm × 수고 {closest_height}m): 물리적으로 불가능한 조합"
    elif abs(closest_dbh - dbh) > 1 or abs(closest_height - height) > 1:
        warning = f"근접값 사용: 요청 ({dbh}, {height}) → 사용 ({closest_dbh}, {closest_height})"
    elif quality == "DRAFT":
        warning = "DRAFT 데이터 (작은 표, 정렬 미검증)"

    return {
        "volume": float(volume) if not pd.isna(volume) else None,
        "lookup_dbh": int(closest_dbh),
        "lookup_height": int(closest_height),
        "quality": quality,
        "warning": warning,
    }


# ============================================================
# Ⅶ장 임분수확표 — 임분 전체 성장 예측
# ============================================================

@lru_cache(maxsize=1)
def _load_stand_table() -> pd.DataFrame:
    if not PARQUET_STAND.exists():
        raise FileNotFoundError(f"임분수확표 없음: {PARQUET_STAND}")
    df = pd.read_parquet(PARQUET_STAND)
    print(f"📊 임분수확표 로드: {len(df):,} 행 (Ⅶ장, {df['수종'].nunique()} 수종)")
    return df

# ============================================================
# 산림 탄소흡수량 (국립산림과학원 표준)
# ============================================================

@lru_cache(maxsize=1)
def _load_carbon_table() -> dict:
    """국립산림과학원 표준 탄소흡수량 (tCO2/ha/yr) 로드."""
    if not CARBON_PATH.exists():
        print(f"⚠️  탄소흡수 데이터 없음: {CARBON_PATH}")
        return {}
    with open(CARBON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("uptake_tco2_per_ha_per_yr", {})


# 수종 별칭 매핑 (yield_table 의 수종명 → carbon 데이터의 수종명)
CARBON_SPECIES_ALIASES = {
    "강원지방소나무": "강원지방소나무",
    "중부지방소나무": "중부지방소나무",
    "소나무": "소나무",
    "잣나무": "잣나무",
    "낙엽송": "낙엽송",
    "리기다소나무": "리기다소나무",
    "편백": "편백",
    "신갈나무": "참나무",      # 참나무류로 매핑
    "굴참나무": "참나무",
    "상수리나무": "참나무",
    "자작나무": None,           # 데이터 없음
    "백합나무": None,           # 데이터 없음
}


def _lookup_carbon_uptake(species: str, age: int) -> dict:
    """
    수종·임령별 연간 탄소흡수량 lookup (tCO2/ha/yr).

    국립산림과학원 표준 데이터는 10년 단위 (10/20/30/40/50/60).
    중간 임령은 *선형 보간*.

    Returns:
        dict: {
            "carbon_uptake_rate": float | None,  # tCO2/ha/yr
            "method": str,                        # "exact" | "interpolated" | "extrapolated"
            "warning": str | None,
        }
    """
    carbon_table = _load_carbon_table()

    # 수종 매핑
    carbon_species = CARBON_SPECIES_ALIASES.get(species)
    if carbon_species is None:
        return {
            "carbon_uptake_rate": None,
            "method": "no_data",
            "warning": f"'{species}' 의 탄소흡수 데이터 없음 (국립산림과학원 표준)",
        }

    species_data = carbon_table.get(carbon_species, {})
    if not species_data:
        return {
            "carbon_uptake_rate": None,
            "method": "no_data",
            "warning": f"'{carbon_species}' 데이터 카본 테이블에 없음",
        }

    # _note 제외하고 임령만 추출
    age_data = {int(k): v for k, v in species_data.items() if k.isdigit()}

    if not age_data:
        return {
            "carbon_uptake_rate": None,
            "method": "no_data",
            "warning": f"'{carbon_species}' 의 임령별 데이터 없음",
        }

    available_ages = sorted(age_data.keys())

    # 정확 일치
    if age in age_data:
        return {
            "carbon_uptake_rate": age_data[age],
            "method": "exact",
            "warning": None,
        }

    # 범위 밖 (extrapolation)
    if age < available_ages[0]:
        return {
            "carbon_uptake_rate": age_data[available_ages[0]],
            "method": "extrapolated_below",
            "warning": f"임령 {age}년 < 가장 어린 데이터 {available_ages[0]}년. "
                       f"{available_ages[0]}년 값 사용 ({age_data[available_ages[0]]})",
        }
    if age > available_ages[-1]:
        return {
            "carbon_uptake_rate": age_data[available_ages[-1]],
            "method": "extrapolated_above",
            "warning": f"임령 {age}년 > 가장 늙은 데이터 {available_ages[-1]}년. "
                       f"{available_ages[-1]}년 값 사용 ({age_data[available_ages[-1]]})",
        }

    # 선형 보간
    lower_age = max(a for a in available_ages if a < age)
    upper_age = min(a for a in available_ages if a > age)
    w = (age - lower_age) / (upper_age - lower_age)
    rate = age_data[lower_age] + w * (age_data[upper_age] - age_data[lower_age])

    return {
        "carbon_uptake_rate": round(rate, 2),
        "method": f"interpolated_{lower_age}-{upper_age}",
        "warning": None,
    }


# ============================================================
# D15 기후 보정 (climate_correct.pkl + NEX-GDDP SSP anomaly)
# ============================================================

@lru_cache(maxsize=1)
def _load_climate_model():
    """climate_correct.pkl 로드 (LightGBM + features). 없으면 None."""
    if not CLIMATE_MODEL_PATH.exists():
        return None
    try:
        import joblib
        return joblib.load(CLIMATE_MODEL_PATH)
    except Exception:
        return None


@lru_cache(maxsize=1)
def _load_train_anomaly_ranges() -> dict:
    """
    학습 데이터(ASOS panel)의 anomaly 변수별 범위 → 외삽 감지용.
    Returns: {'temp_anomaly_30y': (min, max), ...} 또는 {} (파일 없음).

    NEX 미래 anomaly 가 이 범위 밖이면 = 외삽 (트리 모델 신뢰 낮음).
    학습에 쓴 바로 그 데이터를 진실의 원천으로 사용.
    """
    # panel 컬럼명 → climate_correct feature 명 매핑
    col_map = {
        'temp_anom': 'temp_anomaly_30y',
        'prcp_anom': 'prcp_anomaly_30y',
        'gdd_anom': 'gdd_anomaly',
        'vpd_anom': 'vpd_anomaly',
    }
    if not PANEL_ANOMALY_PATH.exists():
        return {}
    vals = {f: [] for f in col_map.values()}
    with open(PANEL_ANOMALY_PATH, encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            for col, feat in col_map.items():
                try:
                    vals[feat].append(float(row[col]))
                except (KeyError, TypeError, ValueError):
                    pass
    return {f: (min(v), max(v)) for f, v in vals.items() if v}


@lru_cache(maxsize=1)
def _load_nex_anomaly() -> dict:
    """
    NEX-GDDP SSP anomaly 로드 → {(sigun, scenario): {4 anomaly}}.
    CSV 컬럼: sigun, stn_id, scenario, temp, prcp, gdd, vpd
    """
    table = {}
    if not NEX_ANOMALY_PATH.exists():
        return table
    with open(NEX_ANOMALY_PATH, encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            key = (row['sigun'], row['scenario'])
            table[key] = {
                'temp_anomaly_30y': float(row['temp']),
                'prcp_anomaly_30y': float(row['prcp']),
                'gdd_anomaly': float(row['gdd']),
                'vpd_anomaly': float(row['vpd']),
            }
    return table


def _compute_climate_correction(species, site_index, elev, sigun, climate_scenario):
    """
    climate_correct.pkl 로 V_table 보정값(residual, m³/ha) 계산.

    Returns: (residual_float, warning_str_or_None)
      · baseline 또는 모델/데이터 없으면 (0.0, 경고 또는 None)
    """
    if climate_scenario == "baseline":
        return 0.0, None

    nex_scen = SCENARIO_TO_NEX.get(climate_scenario)
    if nex_scen is None:
        return 0.0, (f"'{climate_scenario}' NEX-GDDP 미제공 "
                     f"(ssp245/ssp585만 지원). 기후 보정 0.")

    model_dict = _load_climate_model()
    if model_dict is None:
        return 0.0, "climate_correct.pkl 없음. 기후 보정 0."

    nex = _load_nex_anomaly()
    anom = nex.get((sigun, nex_scen))
    if anom is None:
        return 0.0, (f"NEX anomaly 없음 ({sigun}, {nex_scen}). "
                     f"기후 보정 0.")

    if elev is None:
        return 0.0, "elev (해발고) 미입력 → 기후 보정 불가 (보정 0)."

    # 임상 코드 (climate_correct 학습 시 IMSANG_TO_CODE: D=0, H=1, M=2)
    imsang_code = 0 if species in CONIFERS else 1

    model = model_dict['model']
    features = model_dict['features']
    feat_values = {
        'temp_anomaly_30y': anom['temp_anomaly_30y'],
        'prcp_anomaly_30y': anom['prcp_anomaly_30y'],
        'gdd_anomaly': anom['gdd_anomaly'],
        'vpd_anomaly': anom['vpd_anomaly'],
        'elev': float(elev),
        'imsang_code': imsang_code,
        'si': float(site_index),
    }

    # --- 외삽 감지 (방법 A) ---
    # NEX 미래 anomaly 가 학습(ASOS) 범위 밖이면 = 외삽.
    # 트리 모델(LightGBM)은 외삽 구간에서 상수 출력 → 보정값 신뢰 낮음,
    # SSP 시나리오 구분 불가. 정직히 경고.
    ranges = _load_train_anomaly_ranges()
    extrapolated_vars = []
    for feat in ['temp_anomaly_30y', 'prcp_anomaly_30y', 'gdd_anomaly', 'vpd_anomaly']:
        if feat in ranges and feat in feat_values:
            lo, hi = ranges[feat]
            v = feat_values[feat]
            if v < lo or v > hi:
                short = feat.replace('_anomaly_30y', '').replace('_anomaly', '')
                extrapolated_vars.append(f"{short}({v:+.2f} vs 학습 {lo:+.2f}~{hi:+.2f})")

    try:
        missing = [f for f in features if f not in feat_values]
        if missing:
            return 0.0, f"climate_correct feature 미지원: {missing}. 보정 0."
        X = pd.DataFrame([[feat_values[f] for f in features]], columns=features)
        residual = float(model.predict(X)[0])
    except Exception as e:
        return 0.0, f"기후 보정 예측 실패: {e}. 보정 0."

    # 외삽 경고 (보정값은 제공하되 방향성 참고용임을 명시)
    if extrapolated_vars:
        warn = (f"[외삽 주의] 미래 anomaly 가 학습 범위 밖: "
                f"{', '.join(extrapolated_vars)}. "
                f"트리 모델 외삽 → 보정값({residual:+.1f})은 *방향성 참고용*, "
                f"정확한 크기 불확실. SSP 시나리오 간 구분 제한적.")
        return residual, warn

    return residual, None


def _lookup_stand(df: pd.DataFrame, species: str, site_index: int, age: int) -> dict:
    """
    임분수확표에서 (species, SI, age) 행 lookup. age 가 표에 없으면 보간.
    """
    species_df = df[df["수종"] == species]
    if species_df.empty:
        return None

    # SI 매칭 (가장 가까운 값)
    available_sis = sorted(species_df["지위지수"].unique())
    closest_si = min(available_sis, key=lambda x: abs(x - site_index))
    si_df = species_df[species_df["지위지수"] == closest_si].sort_values("임령(년)")

    if si_df.empty:
        return None

    # 임령 매칭 (정확 일치 우선, 없으면 양 옆 보간)
    available_ages = sorted(si_df["임령(년)"].unique())

    exact = si_df[si_df["임령(년)"] == age]
    if not exact.empty:
        row = exact.iloc[0]
        return {
            "site_index": float(closest_si),
            "age": float(age),
            "dbh_cm": float(row["평균DBH(cm)"]),
            "height_m": float(row["평균수고(m)"]),
            "dominant_height_m": float(row["우세목수고(m)"]),
            "n_per_ha": float(row["본수(본/ha)"]),
            "volume_m3_per_ha": float(row["재적(m³/ha)"]),
            "tmai_m3_per_ha_yr": float(row["연평균생장량(m³/ha/yr)"]) if pd.notna(row["연평균생장량(m³/ha/yr)"]) else None,
            "method": "exact",
        }

    # 양 옆 임령으로 선형 보간
    age_min = min(available_ages)
    age_max = max(available_ages)

    if age < age_min:
        return {"out_of_range": True, "valid_range": (age_min, age_max),
                "available_ages": available_ages}
    if age > age_max:
        return {"out_of_range": True, "valid_range": (age_min, age_max),
                "available_ages": available_ages}

    # 보간
    lower_age = max(a for a in available_ages if a < age)
    upper_age = min(a for a in available_ages if a > age)

    lower_row = si_df[si_df["임령(년)"] == lower_age].iloc[0]
    upper_row = si_df[si_df["임령(년)"] == upper_age].iloc[0]

    # 선형 보간 가중치
    w = (age - lower_age) / (upper_age - lower_age)

    def interp(col):
        a = lower_row[col]
        b = upper_row[col]
        if pd.isna(a) or pd.isna(b):
            return None
        return float(a + w * (b - a))

    return {
        "site_index": float(closest_si),
        "age": float(age),
        "dbh_cm": interp("평균DBH(cm)"),
        "height_m": interp("평균수고(m)"),
        "dominant_height_m": interp("우세목수고(m)"),
        "n_per_ha": interp("본수(본/ha)"),
        "volume_m3_per_ha": interp("재적(m³/ha)"),
        "tmai_m3_per_ha_yr": interp("연평균생장량(m³/ha/yr)"),
        "method": f"interpolated between age {lower_age} and {upper_age}",
    }


def growth_compare(
    species: str,
    site_index: int,
    age_now: int,
    target_age: int,
) -> dict:
    """
    임분 성장 *두 시점 비교* — 현재 vs 미래.

    내부 사용 또는 빠른 비교용. 가이드 공식 API 는 growth_predict() 사용.
    """
    df = _load_stand_table()
    warnings = []

    if species in STAND_NO_DATA:
        return {
            "current": None, "future": None, "growth": None,
            "warning": f"'{species}' 는 Ⅶ장 임분수확표에 없음 (해송/삼나무/이태리포플러). "
                       f"lookup_volume() 으로 개별 나무 재적은 조회 가능.",
        }

    available_species = sorted(df["수종"].unique())
    if species not in available_species:
        return {
            "current": None, "future": None, "growth": None,
            "warning": f"'{species}' 수종 없음. 사용 가능: {available_species}",
        }

    if species in STAND_TENTATIVE:
        warnings.append(f"{species}는 (잠정) 데이터 — PDF 원문 표시")

    if target_age < age_now:
        return {
            "current": None, "future": None, "growth": None,
            "warning": f"target_age({target_age}) < age_now({age_now}). 역방향 예측 불가",
        }

    current = _lookup_stand(df, species, site_index, age_now)
    future = _lookup_stand(df, species, site_index, target_age)

    if current is None or future is None:
        return {
            "current": None, "future": None, "growth": None,
            "warning": f"lookup 실패",
        }

    if current.get("out_of_range") or future.get("out_of_range"):
        result = current if current.get("out_of_range") else future
        return {
            "current": None, "future": None, "growth": None,
            "warning": f"임령 범위 밖. 사용 가능: {result['valid_range']}년",
        }

    growth = {
        "years": target_age - age_now,
        "dbh_increase_cm": future["dbh_cm"] - current["dbh_cm"],
        "height_increase_m": future["height_m"] - current["height_m"],
        "volume_increase_m3_per_ha": future["volume_m3_per_ha"] - current["volume_m3_per_ha"],
        "volume_ratio": future["volume_m3_per_ha"] / current["volume_m3_per_ha"]
                        if current["volume_m3_per_ha"] > 0 else None,
        "n_mortality": current["n_per_ha"] - future["n_per_ha"],
    }

    return {
        "current": current,
        "future": future,
        "growth": growth,
        "warning": " | ".join(warnings) if warnings else None,
    }


# ============================================================
# 가이드 공식 API — growth_predict()
# ============================================================

def growth_predict(
    species: str,
    site_index: int,
    age_now: int,
    forecast_years: list,
    climate_scenario: str = "baseline",
    elev: float = None,
    sigun: str = "보은",
) -> list:
    """
    임분 성장 예측 — *여러 시점 trajectory* (가이드 공식 API).

    가이드 시그니처 (Module BD guide §8.2) + D15 기후 보정:
        growth_predict(
            species="잣나무", site_index=14, age_now=50,
            forecast_years=[0, 5, 10, 15, 20],
            climate_scenario="SSP245", elev=350, sigun="보은"
        )

    Args:
        species: 수종명 (11 수종)
        site_index: 지위지수
        age_now: 현재 임령 (년)
        forecast_years: 예측 시점 리스트 (현재로부터 dt년 후)
        climate_scenario: "baseline" (기본) | "SSP245" | "SSP585"
                          baseline = 임분수확표 그대로
                          SSP245/585 = NEX-GDDP 기후 anomaly 로 보정 (D15)
        elev: 해발고 (m). 기후 보정에 필요 (SSP 시나리오 시).
              None 이면 보정 안 함 (baseline 동일) + 경고.
        sigun: 충북 시군 ('보은' 기본, 파일럿).
               청주/충주/제천/보은/추풍령 — NEX anomaly lookup 용.

    Returns:
        List[dict]: 각 시점의 임분 상태
            · volume: 임분수확표 baseline V (m³/ha)
            · volume_corrected: 기후 보정 V (baseline + residual)
            · climate_residual: 보정값 (m³/ha, baseline 이면 0)
            · grade_distribution, carbon_uptake_rate, ...
    """
    df = _load_stand_table()

    # 사전 검증
    if species in STAND_NO_DATA:
        return [{
            "error": "no_stand_data",
            "warning": f"'{species}' 는 Ⅶ장 임분수확표에 없음. "
                       f"lookup_volume() 으로 개별 나무는 가능.",
        }]

    available_species = sorted(df["수종"].unique())
    if species not in available_species:
        return [{
            "error": "unknown_species",
            "warning": f"'{species}' 수종 없음. 사용 가능: {available_species}",
        }]

    # 기후 시나리오 검증 (SSP126 은 NEX-GDDP 미제공)
    valid_scenarios = ["baseline", "SSP245", "SSP585"]
    if climate_scenario not in valid_scenarios:
        return [{
            "error": "invalid_climate_scenario",
            "warning": f"climate_scenario must be one of {valid_scenarios} "
                       f"(SSP126 은 NEX-GDDP GEE 미제공)",
        }]

    # 기후 보정값 (residual) — 한 임분에 대해 한 번 계산 (기후+입지만, 나이 무관)
    climate_residual, climate_warning = _compute_climate_correction(
        species, site_index, elev, sigun, climate_scenario)

    species_warning = None
    if species in STAND_TENTATIVE:
        species_warning = f"{species}는 (잠정) 데이터 — PDF 원문 표시"

    # 등급분포용 임상 코드 (수종 기반 침엽/활엽 추정)
    imsang_for_grade = "침엽수림(D)" if species in CONIFERS else "활엽수림(H)"

    # 각 시점 lookup
    trajectory = []
    for dt in forecast_years:
        future_age = age_now + dt

        if future_age < 0:
            trajectory.append({
                "dt": dt, "age": future_age,
                "error": "negative_age",
                "warning": f"미래 임령이 음수 (age_now={age_now}, dt={dt})",
            })
            continue

        stand = _lookup_stand(df, species, site_index, future_age)

        if stand is None:
            trajectory.append({
                "dt": dt, "age": future_age,
                "error": "lookup_failed",
                "warning": "임분수확표 lookup 실패",
            })
            continue

        if stand.get("out_of_range"):
            trajectory.append({
                "dt": dt, "age": future_age,
                "error": "out_of_range",
                "warning": f"임령 {future_age}년이 임분수확표 범위 밖. "
                           f"사용 가능: {stand['valid_range']}년",
                "valid_range": stand["valid_range"],
            })
            continue

        # 정상 케이스
        warns = []
        if climate_warning:
            warns.append(climate_warning)
        if species_warning:
            warns.append(species_warning)

        # 탄소흡수량 lookup
        carbon = _lookup_carbon_uptake(species, future_age)
        if carbon["warning"]:
            warns.append(carbon["warning"])

        # 등급분포 (D14 Weibull) — 임령 → 영급: (age-1)//10 + 1
        grade_dist = None
        if _HAS_GRADE and stand["n_per_ha"] is not None:
            _ac = min(max((int(stand["age"]) - 1) // 10 + 1, 1), 10)
            try:
                _g = grade_distribution(_ac, imsang_for_grade, int(stand["n_per_ha"]))
                grade_dist = {
                    "소경재": _g["소경재"],
                    "중경재": _g["중경재"],
                    "대경재": _g["대경재"],
                    "fallback": _g["fallback"],
                }
            except Exception:
                grade_dist = None

        # 기후 보정 V (D15) — baseline V + residual (나이 무관 동일 보정)
        v_base = stand["volume_m3_per_ha"]
        v_corrected = v_base + climate_residual if v_base is not None else None

        trajectory.append({
            "dt": dt,
            "age": int(stand["age"]),
            "volume": v_base,                              # m³/ha (임분수확표 baseline)
            "volume_corrected": v_corrected,               # m³/ha (기후 보정) ⭐ D15
            "climate_residual": round(climate_residual, 2),  # 보정값 (baseline=0) ⭐ D15
            "climate_extrapolation": bool(climate_warning and "[외삽 주의]" in climate_warning),  # 외삽 여부 ⭐
            "dbh": stand["dbh_cm"],                        # cm
            "height": stand["height_m"],                   # m
            "dominant_height": stand["dominant_height_m"],  # m
            "n_per_ha": stand["n_per_ha"],
            "tmai_m3_per_ha_yr": stand["tmai_m3_per_ha_yr"],
            "grade_distribution": grade_dist,              # D14 Weibull
            "carbon_uptake_rate": carbon["carbon_uptake_rate"],
            "carbon_method": carbon["method"],
            "climate_scenario": climate_scenario,
            "site_index_used": stand["site_index"],
            "method": stand["method"],
            "warning": " | ".join(warns) if warns else None,
        })

    return trajectory


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("🌲 growth_predict() — 가이드 공식 시그니처 + D15 기후 보정 테스트")
    print("=" * 70)

    # 테스트 1: 가이드 §8.2 예시 (baseline)
    print("\n📌 가이드 §8.2: 잣나무 SI=14 age=50 forecast=[0,5,10,15,20] baseline")
    trajectory = growth_predict(
        species="잣나무", site_index=14, age_now=50,
        forecast_years=[0, 5, 10, 15, 20],
        climate_scenario="baseline",
    )
    for t in trajectory:
        if "error" in t:
            print(f"   dt={t['dt']:>2}: ❌ {t['warning']}")
            continue
        carbon_str = f"C={t['carbon_uptake_rate']:>5.2f}" if t.get('carbon_uptake_rate') else "C=N/A "
        g = t.get('grade_distribution')
        grade_str = (f"등급[소{g['소경재']} 중{g['중경재']} 대{g['대경재']}]"
                     if g else "등급[N/A]")
        print(f"   dt={t['dt']:>2}, 임령={t['age']:>2}년: "
              f"V={t['volume']:>6.1f}, DBH={t['dbh']:>5.1f}cm, "
              f"N={t['n_per_ha']:>4.0f}/ha, {carbon_str}, {grade_str}")

    # 테스트 2: 강원지방소나무 (충북 보은 주력, baseline)
    print("\n📌 보은 주력: 강원지방소나무 SI=14 age=30 forecast=[0,10,20,30]")
    trajectory = growth_predict(
        species="강원지방소나무", site_index=14, age_now=30,
        forecast_years=[0, 10, 20, 30],
    )
    for t in trajectory:
        if "error" in t:
            print(f"   dt={t['dt']:>2}: ❌ {t['warning']}")
            continue
        carbon_str = f"C={t['carbon_uptake_rate']:>5.2f}" if t.get('carbon_uptake_rate') else "C=N/A "
        g = t.get('grade_distribution')
        grade_str = (f"등급[소{g['소경재']} 중{g['중경재']} 대{g['대경재']}]"
                     if g else "등급[N/A]")
        print(f"   dt={t['dt']:>2}, 임령={t['age']:>2}년: "
              f"V={t['volume']:>6.1f}, DBH={t['dbh']:>5.1f}cm, {carbon_str}, {grade_str}")

    # 테스트 3: 보간
    print("\n📌 보간: 강원지방소나무 SI=14 age=27 forecast=[3, 8, 13]")
    trajectory = growth_predict(
        species="강원지방소나무", site_index=14, age_now=27,
        forecast_years=[3, 8, 13],
    )
    for t in trajectory:
        if "error" in t:
            print(f"   dt={t['dt']:>2}: ❌ {t['warning']}")
            continue
        print(f"   dt={t['dt']:>2}, 임령={t['age']:>2}년: "
              f"V={t['volume']:>6.1f} m³/ha [{t['method']}]")

    # 테스트 4: D15 기후 보정 — SSP245 vs SSP585 (elev 제공) ⭐
    print("\n📌 D15 기후 보정: 강원지방소나무 SI=14 age=40 elev=350 보은")
    print("   baseline vs SSP245 vs SSP585 (대경재 벌기 시점 비교)")
    for scen in ["baseline", "SSP245", "SSP585"]:
        traj = growth_predict(
            species="강원지방소나무", site_index=14, age_now=40,
            forecast_years=[0, 20],
            climate_scenario=scen, elev=350, sigun="보은",
        )
        for t in traj:
            if "error" in t:
                continue
            vc = t.get('volume_corrected')
            vc_str = f"{vc:>6.1f}" if vc is not None else "N/A"
            ext = " [외삽]" if t.get('climate_extrapolation') else ""
            print(f"   {scen:<9} dt={t['dt']:>2} 임령={t['age']}년: "
                  f"V_base={t['volume']:>6.1f}, V_corrected={vc_str}, "
                  f"보정={t['climate_residual']:>+6.1f}{ext}")
        if traj and traj[0].get('warning'):
            print(f"      💬 {traj[0]['warning']}")

    # 테스트 5: SSP 인데 elev 없음 (정직한 경고)
    print("\n📌 elev 없이 SSP245 (보정 불가 경고)")
    traj = growth_predict(
        species="잣나무", site_index=14, age_now=40,
        forecast_years=[0], climate_scenario="SSP245",
    )
    for t in traj:
        if "error" not in t:
            print(f"   dt={t['dt']} 임령={t['age']}년: V={t['volume']:.1f}, "
                  f"보정={t['climate_residual']:+.1f}")
            if t['warning']:
                print(f"      💬 {t['warning']}")

    # 테스트 6: 범위 밖
    print("\n📌 범위 밖: 강원지방소나무 age=30 forecast=[60] (임령 90)")
    trajectory = growth_predict(
        species="강원지방소나무", site_index=14, age_now=30,
        forecast_years=[60],
    )
    for t in trajectory:
        if "error" in t:
            print(f"   dt={t['dt']:>2}: ⚠️  {t['warning']}")

    # 테스트 7: Ⅶ장 없는 수종
    print("\n📌 Ⅶ장 없는 수종: 해송")
    trajectory = growth_predict(
        species="해송", site_index=14, age_now=20, forecast_years=[0, 10],
    )
    for t in trajectory:
        if "error" in t:
            print(f"   ⚠️  {t['warning']}")

    # 테스트 8: 잠정 수종
    print("\n📌 잠정 수종: 백합나무 SI=14 age=10 forecast=[0,10,20,30]")
    trajectory = growth_predict(
        species="백합나무", site_index=14, age_now=10,
        forecast_years=[0, 10, 20, 30],
    )
    for t in trajectory:
        if "error" in t:
            print(f"   dt={t['dt']:>2}: ❌ {t['warning']}")
            continue
        print(f"   dt={t['dt']:>2}, 임령={t['age']:>2}년: V={t['volume']:>6.1f} m³/ha")
        if t['warning']:
            print(f"      💬 {t['warning']}")

    print()
    print("=" * 70)
    print("🌲 growth_compare() — 두 시점 비교 (내부 사용)")
    print("=" * 70)
    result = growth_compare("강원지방소나무", site_index=14, age_now=30, target_age=50)
    if result["current"]:
        c, f, g = result["current"], result["future"], result["growth"]
        print(f"   현재 (30년): V={c['volume_m3_per_ha']:.1f}, N={c['n_per_ha']:.0f}/ha")
        print(f"   미래 (50년): V={f['volume_m3_per_ha']:.1f}, N={f['n_per_ha']:.0f}/ha")
        print(f"   변화: V +{g['volume_increase_m3_per_ha']:.1f} ({g['volume_ratio']:.2f}배), "
              f"고사 {g['n_mortality']:.0f}/ha")

    print()
    print("=" * 70)
    print("✅ 모든 테스트 완료")
    print("=" * 70)