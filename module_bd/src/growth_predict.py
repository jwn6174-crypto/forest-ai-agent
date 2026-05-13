"""
growth_predict.py
모듈 B 의 핵심 API. 임분수확표 기반 성장 예측.

주요 함수:
- lookup_volume(species, bark, dbh, height) → 개별 나무 재적 (Ⅱ장 입목수간재적표 사용)
- growth_predict(species, site_index, age_now, T) → 임분 전체 성장 예측 (Ⅶ장 임분수확표 사용)

데이터 출처:
- module_bd/data/interim/yield_table_full.parquet (Ⅱ장 입목수간재적표, 16,163 값)
- module_bd/data/interim/yield_table_stand.parquet (Ⅶ장 임분수확표, 576 행)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from functools import lru_cache

ROOT = Path(__file__).resolve().parents[2]
PARQUET_VOLUME = ROOT / "module_bd" / "data" / "interim" / "yield_table_full.parquet"
PARQUET_STAND = ROOT / "module_bd" / "data" / "interim" / "yield_table_stand.parquet"

# 작은 표 수종 (DRAFT, 입목수간재적표)
SMALL_TABLE_SPECIES = {"해송", "삼나무", "이태리포플러"}

# 임분수확표 없는 수종 (Ⅶ장에 없음, 잠정 데이터 또는 제외)
STAND_NO_DATA = {"해송", "삼나무", "이태리포플러"}
STAND_TENTATIVE = {"자작나무", "백합나무"}  # (잠정) 표시


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
    
    Args:
        species: 수종명 (예: "강원지방소나무")
        site_index: 지위지수 (예: 14)
        age_now: 현재 임령 (년)
        target_age: 목표 임령 (년)
    
    Returns:
        dict: {current, future, growth, warning}
    """
    df = _load_stand_table()
    warnings = []
    
    # 수종 검증
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
) -> list:
    """
    임분 성장 예측 — *여러 시점 trajectory* (가이드 공식 API).
    
    가이드 시그니처 (Module BD guide §8.2):
        growth_predict(
            species="잣나무", site_index=14, age_now=50,
            forecast_years=[0, 5, 10, 15, 20], climate_scenario="baseline"
        )
    
    Args:
        species: 수종명 (11 수종, 예: "강원지방소나무")
        site_index: 지위지수 (수종마다 가능 값 다름)
        age_now: 현재 임령 (년)
        forecast_years: 예측 시점 리스트 (현재로부터 dt년 후, 예: [0, 5, 10])
        climate_scenario: "baseline" (기본) | "SSP126" | "SSP245" | "SSP585"
                          현재 baseline 만 작동, 다른 시나리오는 경고 반환
    
    Returns:
        List[dict]: 각 시점의 임분 상태
            [{"dt": 0, "age": 50, "volume": 296.2, "dbh": 33.0, "height": 19.0,
              "n_per_ha": 489, "grade_distribution": None,
              "tmai_m3_per_ha_yr": 4.93, "method": "exact", "warning": None}, ...]
        
        또는 에러 시:
            [{"error": "...", "warning": "..."}]
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
    
    # 기후 시나리오 검증
    valid_scenarios = ["baseline", "SSP126", "SSP245", "SSP585"]
    if climate_scenario not in valid_scenarios:
        return [{
            "error": "invalid_climate_scenario",
            "warning": f"climate_scenario must be one of {valid_scenarios}",
        }]
    
    climate_warning = None
    if climate_scenario != "baseline":
        climate_warning = (
            f"기후 보정 layer (SSP 시나리오) 미구현. "
            f"baseline 값 반환 — Module B Week 3-4 작업 예정."
        )
    
    species_warning = None
    if species in STAND_TENTATIVE:
        species_warning = f"{species}는 (잠정) 데이터 — PDF 원문 표시"
    
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
        
        # 정상 케이스 — 가이드 trajectory 항목 형식
        warns = []
        if climate_warning:
            warns.append(climate_warning)
        if species_warning:
            warns.append(species_warning)
        
        trajectory.append({
            "dt": dt,
            "age": int(stand["age"]),
            "volume": stand["volume_m3_per_ha"],          # m³/ha
            "dbh": stand["dbh_cm"],                       # cm
            "height": stand["height_m"],                  # m
            "dominant_height": stand["dominant_height_m"], # m
            "n_per_ha": stand["n_per_ha"],
            "tmai_m3_per_ha_yr": stand["tmai_m3_per_ha_yr"],
            "grade_distribution": None,  # NFI Weibull 미구현 (Module A 협업 필요)
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
    print("=" * 60)
    print("🌲 growth_predict() — 가이드 공식 시그니처 테스트")
    print("=" * 60)
    
    # 테스트 1: 가이드 §8.2 예시
    print("\n📌 가이드 §8.2 예시: 잣나무 SI=14 age=50 forecast=[0,5,10,15,20]")
    trajectory = growth_predict(
        species="잣나무", site_index=14, age_now=50,
        forecast_years=[0, 5, 10, 15, 20],
        climate_scenario="baseline",
    )
    for t in trajectory:
        if "error" in t:
            print(f"   dt={t['dt']:>2}: ❌ {t['warning']}")
            continue
        print(f"   dt={t['dt']:>2}, 임령={t['age']:>2}년: "
              f"V={t['volume']:>6.1f} m³/ha, DBH={t['dbh']:>5.1f}cm, "
              f"H={t['height']:>4.1f}m, N={t['n_per_ha']:>4.0f}/ha")
    
    # 테스트 2: 강원지방소나무 (충북 보은 주력)
    print("\n📌 충북 보은 주력: 강원지방소나무 SI=14 age=30 forecast=[0,10,20,30]")
    trajectory = growth_predict(
        species="강원지방소나무", site_index=14, age_now=30,
        forecast_years=[0, 10, 20, 30],
    )
    for t in trajectory:
        if "error" in t:
            print(f"   dt={t['dt']:>2}: ❌ {t['warning']}")
            continue
        print(f"   dt={t['dt']:>2}, 임령={t['age']:>2}년: "
              f"V={t['volume']:>6.1f} m³/ha, DBH={t['dbh']:>5.1f}cm")
    
    # 테스트 3: 보간 (forecast_years 가 표에 없는 임령 만듦)
    print("\n📌 보간: 강원지방소나무 SI=14 age=27 forecast=[3, 8, 13]")
    print("   → 임령 30, 35, 40 (직접 lookup)")
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
    
    # 테스트 4: 기후 시나리오 (현재 미구현)
    print("\n📌 기후 시나리오 (미구현): 잣나무 SSP585")
    trajectory = growth_predict(
        species="잣나무", site_index=14, age_now=30,
        forecast_years=[0, 20],
        climate_scenario="SSP585",
    )
    for t in trajectory:
        if "error" in t:
            print(f"   dt={t['dt']:>2}: ❌ {t['warning']}")
            continue
        print(f"   dt={t['dt']:>2}, 임령={t['age']:>2}년: "
              f"V={t['volume']:>6.1f} m³/ha")
        if t['warning']:
            print(f"      💬 {t['warning']}")
    
    # 테스트 5: 범위 밖
    print("\n📌 범위 밖: 강원지방소나무 age=30 forecast=[60] (임령 90 → 범위 밖)")
    trajectory = growth_predict(
        species="강원지방소나무", site_index=14, age_now=30,
        forecast_years=[60],
    )
    for t in trajectory:
        if "error" in t:
            print(f"   dt={t['dt']:>2}: ⚠️  {t['warning']}")
    
    # 테스트 6: Ⅶ장에 없는 수종
    print("\n📌 Ⅶ장 없는 수종: 해송")
    trajectory = growth_predict(
        species="해송", site_index=14, age_now=20,
        forecast_years=[0, 10],
    )
    for t in trajectory:
        if "error" in t:
            print(f"   ⚠️  {t['warning']}")
    
    # 테스트 7: 잠정 수종
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
    print("=" * 60)
    print("🌲 growth_compare() — 두 시점 비교 (내부 사용)")
    print("=" * 60)
    result = growth_compare("강원지방소나무", site_index=14, age_now=30, target_age=50)
    if result["current"]:
        c, f, g = result["current"], result["future"], result["growth"]
        print(f"   현재 (30년): V={c['volume_m3_per_ha']:.1f}, N={c['n_per_ha']:.0f}/ha")
        print(f"   미래 (50년): V={f['volume_m3_per_ha']:.1f}, N={f['n_per_ha']:.0f}/ha")
        print(f"   변화: V +{g['volume_increase_m3_per_ha']:.1f} ({g['volume_ratio']:.2f}배), "
              f"고사 {g['n_mortality']:.0f}/ha")
    
    print()
    print("=" * 60)
    print("✅ 모든 테스트 완료")
    print("=" * 60)