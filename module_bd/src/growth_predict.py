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


def growth_predict(
    species: str,
    site_index: int,
    age_now: int,
    target_age: int,
) -> dict:
    """
    임분 성장 예측 (Ⅶ장 임분수확표 기반).
    
    Args:
        species: 수종명 (예: "강원지방소나무")
        site_index: 지위지수 (예: 14)
        age_now: 현재 임령 (년)
        target_age: 목표 임령 (년)
    
    Returns:
        dict: {
            "current": {...},  # 현재 임분 상태
            "future":  {...},  # 미래 임분 상태
            "growth":  {...},  # 변화량
            "warning": str or None,
        }
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
    
    # 현재 + 미래 lookup
    current = _lookup_stand(df, species, site_index, age_now)
    future = _lookup_stand(df, species, site_index, target_age)
    
    if current is None or future is None:
        return {
            "current": None, "future": None, "growth": None,
            "warning": f"lookup 실패",
        }
    
    # 범위 밖 처리
    if current.get("out_of_range") or future.get("out_of_range"):
        result = current if current.get("out_of_range") else future
        return {
            "current": None, "future": None, "growth": None,
            "warning": f"임령 범위 밖. 사용 가능: {result['valid_range']}년",
        }
    
    # 변화량 계산
    growth = {
        "years": target_age - age_now,
        "dbh_increase_cm": future["dbh_cm"] - current["dbh_cm"],
        "height_increase_m": future["height_m"] - current["height_m"],
        "volume_increase_m3_per_ha": future["volume_m3_per_ha"] - current["volume_m3_per_ha"],
        "volume_ratio": future["volume_m3_per_ha"] / current["volume_m3_per_ha"]
                        if current["volume_m3_per_ha"] > 0 else None,
        "n_mortality": current["n_per_ha"] - future["n_per_ha"],  # 자연 고사
    }
    
    return {
        "current": current,
        "future": future,
        "growth": growth,
        "warning": " | ".join(warnings) if warnings else None,
    }


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🌲 growth_predict() 테스트 — Ⅶ장 임분수확표 기반")
    print("=" * 60)
    
    test_cases = [
        # (수종, SI, 현재 임령, 목표 임령, 설명)
        ("강원지방소나무", 14, 30, 50, "벌채 적정기 예측 (30→50년)"),
        ("강원지방소나무", 14, 25, 35, "10년 후 예측 (보간 없음)"),
        ("강원지방소나무", 14, 32, 47, "보간 필요 (32→47년, 표에 없는 임령)"),
        ("잣나무",        14, 30, 60, "잣나무 SI=14, 30→60년"),
        ("낙엽송",        14, 20, 40, "낙엽송 20→40년 (벌채기)"),
        ("백합나무",      14, 10, 30, "백합나무 빠른 성장"),
        ("해송",          14, 20, 40, "Ⅶ장에 없는 수종 (에러)"),
        ("강원지방소나무", 14, 30, 25, "역방향 (오류)"),
        ("강원지방소나무", 14, 90, 100, "범위 밖 (10-80년만)"),
    ]
    
    for sp, si, age0, age1, desc in test_cases:
        result = growth_predict(sp, si, age0, age1)
        print(f"\n📌 {desc}")
        print(f"   요청: {sp} SI={si}, {age0}→{age1}년")
        
        if result["current"] is None:
            print(f"   ⚠️  {result['warning']}")
            continue
        
        c, f, g = result["current"], result["future"], result["growth"]
        print(f"   현재 ({age0}년): DBH={c['dbh_cm']:.1f}cm, 수고={c['height_m']:.1f}m, "
              f"본수={c['n_per_ha']:.0f}/ha, 재적={c['volume_m3_per_ha']:.1f}m³/ha")
        print(f"   미래 ({age1}년): DBH={f['dbh_cm']:.1f}cm, 수고={f['height_m']:.1f}m, "
              f"본수={f['n_per_ha']:.0f}/ha, 재적={f['volume_m3_per_ha']:.1f}m³/ha")
        print(f"   변화 ({g['years']}년): DBH +{g['dbh_increase_cm']:.1f}cm, "
              f"수고 +{g['height_increase_m']:.1f}m, "
              f"재적 +{g['volume_increase_m3_per_ha']:.1f}m³/ha ({g['volume_ratio']:.2f}배), "
              f"고사 {g['n_mortality']:.0f}/ha")
        if result["warning"]:
            print(f"   💬 {result['warning']}")
    
    print()
    print("=" * 60)
    print("✅ growth_predict() 테스트 완료")
    print("=" * 60)