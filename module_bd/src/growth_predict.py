"""
growth_predict.py
모듈 B 의 핵심 API. 임분수확표 lookup + 미래 성장 예측.

주요 함수:
- lookup_volume(species, bark, dbh, height) → 재적 m³
- growth_predict(...) → 미래 예측 (다음 단계)

데이터 출처:
- module_bd/data/interim/yield_table_full.parquet
- 16,163 재적 값 (98.5% 완성도)
- 22 큰 표 케이스 OK + 3 작은 표 DRAFT
"""

import pandas as pd
import numpy as np
from pathlib import Path
from functools import lru_cache

ROOT = Path(__file__).resolve().parents[2]
PARQUET_PATH = ROOT / "module_bd" / "data" / "interim" / "yield_table_full.parquet"

# 작은 표 수종 (DRAFT 데이터 — 사용 시 경고)
SMALL_TABLE_SPECIES = {"해송", "삼나무", "이태리포플러"}


@lru_cache(maxsize=1)
def _load_yield_table() -> pd.DataFrame:
    """
    임분수확표 parquet 로드 (lru_cache 로 한 번만 로드).
    """
    if not PARQUET_PATH.exists():
        raise FileNotFoundError(
            f"parquet 파일 없음: {PARQUET_PATH}\n"
            f"먼저 'python module_bd/src/yield_parse.py' 실행 필요"
        )
    df = pd.read_parquet(PARQUET_PATH)
    print(f"📊 임분수확표 로드: {len(df):,} 행, "
          f"수종 {df['수종'].nunique()}개, "
          f"OK {(df['품질']=='OK').sum():,} 행")
    return df


def lookup_volume(
    species: str,
    bark: str = "수피포함",
    dbh: float = None,
    height: float = None,
    use_draft: bool = False,
) -> dict:
    """
    임분수확표에서 재적 값 lookup.
    
    Args:
        species: 수종명 (예: "강원지방소나무", "잣나무", "낙엽송")
        bark: "수피포함" (기본) 또는 "수피제외"
        dbh: 흉고직경 (cm). 표에 없으면 가장 가까운 값 사용.
        height: 수고 (m). 표에 없으면 가장 가까운 값 사용.
        use_draft: True 면 DRAFT 데이터도 사용 (작은 표 수종)
    
    Returns:
        dict: {
            "volume": float (m³),
            "lookup_dbh": float (실제 사용한 DBH),
            "lookup_height": float (실제 사용한 수고),
            "quality": "OK" or "DRAFT",
            "warning": str or None,
        }
    
    Examples:
        >>> lookup_volume("강원지방소나무", "수피포함", 20, 18)
        {"volume": 0.2685, ...}
    """
    df = _load_yield_table()
    
    # 1. 수종 + 수피여부 필터
    mask = (df["수종"] == species) & (df["수피여부"] == bark)
    if use_draft:
        species_df = df[mask]
    else:
        species_df = df[mask & (df["품질"] == "OK")]
    
    if species_df.empty:
        # 작은 표 수종 안내
        if species in SMALL_TABLE_SPECIES:
            return {
                "volume": None,
                "lookup_dbh": None,
                "lookup_height": None,
                "quality": "DRAFT",
                "warning": f"{species}는 DRAFT 데이터만 있음. use_draft=True 로 사용 가능",
            }
        # 알 수 없는 수종
        available = sorted(df["수종"].unique())
        return {
            "volume": None,
            "lookup_dbh": None,
            "lookup_height": None,
            "quality": "ERROR",
            "warning": f"'{species}' 수종 없음. 사용 가능: {available}",
        }
    
    # 2. DBH 매칭 — 가장 가까운 값
    available_dbhs = sorted(species_df["흉고직경(cm)"].unique())
    closest_dbh = min(available_dbhs, key=lambda x: abs(x - dbh))
    
    # 3. 수고 매칭 — 가장 가까운 값
    height_df = species_df[species_df["흉고직경(cm)"] == closest_dbh]
    available_heights = sorted(height_df["수고(m)"].unique())
    closest_height = min(available_heights, key=lambda x: abs(x - height))
    
    # 4. 값 추출
    row = height_df[height_df["수고(m)"] == closest_height].iloc[0]
    volume = row["재적(m³)"]
    quality = row["품질"]
    
    # 5. 경고 생성
    warning = None
    if pd.isna(volume):
        warning = (
            f"빈 셀 (DBH {closest_dbh}cm × 수고 {closest_height}m): "
            f"물리적으로 불가능한 조합일 가능성"
        )
    elif abs(closest_dbh - dbh) > 1 or abs(closest_height - height) > 1:
        warning = (
            f"근접값 사용: 요청 ({dbh}cm, {height}m) → 사용 ({closest_dbh}cm, {closest_height}m)"
        )
    elif quality == "DRAFT":
        warning = f"DRAFT 데이터 (작은 표): 정렬 검증 미완료, 참고용"
    
    return {
        "volume": float(volume) if not pd.isna(volume) else None,
        "lookup_dbh": int(closest_dbh),
        "lookup_height": int(closest_height),
        "quality": quality,
        "warning": warning,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("🌲 lookup_volume() 테스트")
    print("=" * 60)
    
    test_cases = [
        # (수종, 수피, DBH, 수고, 설명)
        ("강원지방소나무", "수피포함", 20, 18, "정상 케이스"),
        ("강원지방소나무", "수피제외", 20, 18, "수피제외"),
        ("잣나무", "수피포함", 25, 20, "잣나무"),
        ("낙엽송", "수피포함", 30, 25, "낙엽송 큰 나무"),
        ("강원지방소나무", "수피포함", 35, 50, "큰 거목 (둘째 페이지)"),
        ("강원지방소나무", "수피포함", 23.5, 18.7, "근접값 (소수점)"),
        ("자작나무", "수피포함", 5, 50, "작은 DBH + 큰 수고 (빈 셀 예상)"),
        ("해송", "수피포함", 10, 8, "DRAFT 수종 (use_draft=False)"),
        ("해송", "수피포함", 10, 8, "DRAFT 수종 (use_draft=True)"),
        ("없는수종", "수피포함", 20, 18, "잘못된 수종"),
    ]
    
    for i, (sp, bk, d, h, desc) in enumerate(test_cases, 1):
        use_draft = "use_draft=True" in desc
        result = lookup_volume(sp, bk, d, h, use_draft=use_draft)
        print(f"\n[테스트 {i}] {desc}")
        print(f"  요청: {sp} ({bk}) DBH={d}cm 수고={h}m")
        if result["volume"] is not None:
            print(f"  ✅ 재적: {result['volume']:.4f} m³")
            print(f"     실제 lookup: DBH={result['lookup_dbh']}cm 수고={result['lookup_height']}m")
        else:
            print(f"  ⚠️  재적: None")
        print(f"  품질: {result['quality']}")
        if result["warning"]:
            print(f"  ⚠️  {result['warning']}")
    
    print()
    print("=" * 60)
    print("✅ lookup_volume() 테스트 완료")
    print("=" * 60)