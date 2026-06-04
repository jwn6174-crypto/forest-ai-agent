"""
Module A — 위성 AGB Nowcasting
predict_stand.py : 팀원 import용 핵심 함수

사용법:
    from module_a.predict_stand import predict_stand, StandStateEstimate

    result = predict_stand(
        geom_wkt="POLYGON((127.72 36.49, ...))",
        pnu="4374010100100010000",
        species_dominant="신갈",
        age_estimate=45,
    )
"""

import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask as rio_mask
import geopandas as gpd
from shapely.geometry import mapping
from shapely.wkt import loads as wkt_loads
from datetime import datetime
from typing import Optional, Dict, Literal
from pydantic import BaseModel, Field
from quantile_forest import RandomForestQuantileRegressor
from sklearn.model_selection import train_test_split
from sklearn.neighbors import NearestNeighbors
import scipy.stats as stats
import os

# ── 경로 설정 (환경에 맞게 수정) ─────────────────────────────
_BASE = os.path.dirname(os.path.abspath(__file__))
RASTER_PATH = os.path.join(_BASE, "data", "boeun_satellite_features_10m.tif")
TRAIN_PATH  = os.path.join(_BASE, "data", "boeun_gedi_training_clean.csv")

# ── 피처 정의 ─────────────────────────────────────────────────
FEATURES_NO_DEM = [
    'B2','B4','B5','B6','B7','B8','B8A','B11','B12',
    'NDVI','NDRE','NBR','NDMI','EVI',
    'VV_mean','VH_mean','VV_std','VV_VH_ratio',
    'HH_db','HV_db','HH_HV_db'
]
DEM_FEATURES = ['elev', 'slope', 'northness', 'eastness']
FEATURES_ALL = FEATURES_NO_DEM + DEM_FEATURES

# ── 산림과학원 바이오매스 변환 계수 ──────────────────────────
SPECIES_PARAMS: Dict[str, Dict] = {
    "잣나무":    {"D": 0.41, "BEF": 1.35, "R": 0.28, "CF": 0.49},
    "낙엽송":    {"D": 0.45, "BEF": 1.34, "R": 0.29, "CF": 0.51},
    "강원소나무": {"D": 0.42, "BEF": 1.74, "R": 0.26, "CF": 0.51},
    "중부소나무": {"D": 0.47, "BEF": 1.74, "R": 0.26, "CF": 0.51},
    "리기다":    {"D": 0.50, "BEF": 1.33, "R": 0.36, "CF": 0.51},
    "신갈":      {"D": 0.66, "BEF": 1.45, "R": 0.43, "CF": 0.47},
    "굴참":      {"D": 0.72, "BEF": 1.45, "R": 0.43, "CF": 0.47},
    "상수리":    {"D": 0.72, "BEF": 1.45, "R": 0.43, "CF": 0.47},
    "편백":      {"D": 0.41, "BEF": 1.35, "R": 0.25, "CF": 0.51},
    "자작":      {"D": 0.61, "BEF": 1.40, "R": 0.31, "CF": 0.47},
    "백합":      {"D": 0.42, "BEF": 1.40, "R": 0.34, "CF": 0.47},
    "기본침엽":  {"D": 0.44, "BEF": 1.50, "R": 0.28, "CF": 0.51},
    "기본활엽":  {"D": 0.60, "BEF": 1.43, "R": 0.38, "CF": 0.47},
}

# ── GEDI 학습 메타 ────────────────────────────────────────────
GEDI_QUALITY_FILTERS = {
    "l4_quality_flag": 1,
    "degrade_flag": 0,
    "sensitivity_min": 0.9,
    "agbd_max": 500,
    "agbd_min": 0,
    "elev_min": 0,
    "se_ratio_max": 0.5,
}
N_GEDI_FOOTPRINTS_TOTAL = 11026   # 보은군 최종 학습 데이터
N_S2_SCENES_DEFAULT     = 23      # 2023년 여름 중위값 장면 수


# ─────────────────────────────────────────────────────────────
# Pydantic 출력 스키마
# ─────────────────────────────────────────────────────────────
class StandStateEstimate(BaseModel):
    """Module A 최종 출력 (가이드 §8.1 호환)"""
    pnu:               str                       # 필지번호 19자리
    geom_wkt:          str                       # 폴리곤 WKT (EPSG:4326)
    area_ha:           float = Field(..., gt=0)  # 면적 (ha)
    estimated_at:      datetime                  # 추정 시각 (UTC)

    species_dominant:  str                       # 우점수종
    species_secondary: Optional[str]  = None     # 부수종
    age_estimate:      Optional[int]  = Field(None, ge=0, le=200)  # 임령 (년)
    age_class:         Optional[str]  = None     # 영급 (예: 5영급)

    agb_mg_per_ha:     float                     # AGB 중앙값 (Mg/ha)
    agb_q05:           float                     # AGB 5% 분위
    agb_q95:           float                     # AGB 95% 분위
    volume_m3_per_ha:  float                     # 입목축적 중앙값 (m³/ha)
    volume_q05:        float
    volume_q95:        float
    carbon_tc_per_ha:  float                     # 탄소량 중앙값 (tC/ha)
    carbon_q05:        float
    carbon_q95:        float

    grade_distribution: Dict[str, float]         # DBH 등급 분포 (Weibull)

    n_gedi_footprints:  int                      # 사용된 GEDI footprint 수
    n_s2_scenes:        int                      # 사용된 S2 장면 수
    saturation_warning: bool = False             # AGB>130 + 침엽수 경고
    confidence_level:   Literal["high","medium","low"]
    confidence_note:    Optional[str] = None


# ─────────────────────────────────────────────────────────────
# 내부 변환 함수
# ─────────────────────────────────────────────────────────────
def _agb_to_volume(agb: float, sp: str) -> float:
    """AGB(Mg/ha) → 입목축적(m³/ha)  V = AGB / (D × BEF)"""
    p = SPECIES_PARAMS.get(sp, SPECIES_PARAMS["기본활엽"])
    return agb / (p["D"] * p["BEF"])


def _agb_to_carbon(agb: float, sp: str) -> float:
    """AGB(Mg/ha) → 탄소량(tC/ha)  C = AGB × (1+R) × CF"""
    p = SPECIES_PARAMS.get(sp, SPECIES_PARAMS["기본활엽"])
    return agb * (1 + p["R"]) * p["CF"]


def _age_class(age: Optional[int]) -> Optional[str]:
    """임령(년) → 영급 문자열"""
    if age is None:
        return None
    return f"{(age // 10) + 1}영급"


def _grade_distribution(agb: float) -> Dict[str, float]:
    """
    Weibull DBH 분포 기반 등급 비율 추정
    AGB → 평균 DBH 경험식 → Weibull(shape=2.5) 적분
    """
    mean_dbh = 7.5 * (agb / 50) ** 0.4
    shape, scale = 2.5, mean_dbh / 0.89
    breaks = [0, 6, 12, 18, 24, 30, 42, 999]
    labels = ["치수","소경","중경","대경1","대경2","대경3","초대경"]
    probs = {}
    for i, lab in enumerate(labels):
        lo = stats.weibull_min.cdf(breaks[i],   shape, scale=scale)
        hi = stats.weibull_min.cdf(breaks[i+1], shape, scale=scale)
        probs[lab] = round(hi - lo, 4)
    total = sum(probs.values()) or 1.0
    return {k: round(v / total, 4) for k, v in probs.items()}


# ─────────────────────────────────────────────────────────────
# 모델 초기화 (import 시 1회 실행)
# ─────────────────────────────────────────────────────────────
print("[Module A] 초기화 중...")

_df_train = pd.read_csv(TRAIN_PATH, encoding="utf-8-sig")
_df_train = _df_train[_df_train["NDVI"] >= 0.3].copy()
_df_train["sample_weight"] = 1.0 / (_df_train["agbd_se"] + 1.0)

_trn, _ = train_test_split(_df_train, test_size=0.15, random_state=42)

_qrf = RandomForestQuantileRegressor(
    n_estimators=1000,
    max_features=0.5,
    min_samples_leaf=5,
    min_samples_split=5,
    n_jobs=-1,
    random_state=42,
)
_qrf.fit(_trn[FEATURES_ALL], _trn["agbd"],
         sample_weight=_trn["sample_weight"])

_nn_dem = NearestNeighbors(n_neighbors=5, n_jobs=-1)
_nn_dem.fit(_df_train[FEATURES_NO_DEM].values)

print("[Module A] ✅ 초기화 완료 "
      f"(학습 데이터 {len(_df_train):,}개, "
      f"GEDI R²≈0.47, RMSE≈59.8 Mg/ha)")


# ─────────────────────────────────────────────────────────────
# 핵심 공개 함수
# ─────────────────────────────────────────────────────────────
def predict_stand(
    geom_wkt:          str,
    pnu:               str,
    species_dominant:  str,
    species_secondary: Optional[str] = None,
    age_estimate:      Optional[int] = None,
    n_gedi_footprints: int = N_GEDI_FOOTPRINTS_TOTAL,
    n_s2_scenes:       int = N_S2_SCENES_DEFAULT,
) -> StandStateEstimate:
    """
    임분 폴리곤 WKT + 수종 정보 → StandStateEstimate

    Parameters
    ----------
    geom_wkt          : 임분 폴리곤 WKT (EPSG:4326)
    pnu               : 필지번호 19자리
    species_dominant  : 우점수종 키 (SPECIES_PARAMS 참조)
    species_secondary : 부수종 키 (선택)
    age_estimate      : 임령 년수 (선택, 영급 자동 계산)
    n_gedi_footprints : 사용된 GEDI footprint 수
    n_s2_scenes       : 사용된 Sentinel-2 장면 수

    Returns
    -------
    StandStateEstimate
        agb/volume/carbon 각각 중앙값 + 90% 예측구간 포함

    Notes
    -----
    - GEDI saturation 경고: AGB > 130 Mg/ha + 침엽수 → saturation_warning=True
    - NFI 외부검증 R²=-0.187 (고AGB 침엽수림 과소추정 한계, GEDI saturation 기인)
    - 유효 픽셀 없는 폴리곤: 학습 데이터 평균으로 fallback (confidence='low')
    """

    # 1. 면적 계산 (WGS84 → EPSG:5179 투영 후)
    geom    = wkt_loads(geom_wkt)
    area_ha = (gpd.GeoSeries([geom], crs="EPSG:4326")
               .to_crs("EPSG:5179").area.values[0] / 10000)
    area_ha = max(area_ha, 0.0001)

    # 2. raster에서 위성 피처 추출
    try:
        with rasterio.open(RASTER_PATH) as src:
            out_image, _ = rio_mask(
                src, [mapping(geom)], crop=True, nodata=np.nan
            )
        pixels   = out_image.reshape(out_image.shape[0], -1).T  # (N, 25)
        df_pix   = pd.DataFrame(pixels, columns=FEATURES_ALL)
        valid    = (
            ~df_pix[FEATURES_NO_DEM].isnull().any(axis=1) &
            (df_pix["NDVI"] >= 0.3)
        )
        df_valid = df_pix[valid].copy()
    except Exception:
        df_valid = pd.DataFrame()

    n_pixels = len(df_valid)

    # 3. AGB 예측
    if n_pixels == 0:
        # fallback: 학습 데이터 전체 평균
        confidence = "low"
        note       = "폴리곤 내 유효 픽셀 없음 → 학습 데이터 평균 사용"
        feat_mean  = _df_train[FEATURES_ALL].mean().values.reshape(1, -1)
        preds      = _qrf.predict(
            pd.DataFrame(feat_mean, columns=FEATURES_ALL),
            quantiles=[0.05, 0.50, 0.95],
        )
        agb_q05, agb_med, agb_q95 = float(preds[0, 0]), float(preds[0, 1]), float(preds[0, 2])

    else:
        # DEM KNN 보간 (raster에서 DEM NaN → 학습 데이터 근방 값으로 대체)
        dists, idxs = _nn_dem.kneighbors(df_valid[FEATURES_NO_DEM].values)
        for j, dem_col in enumerate(DEM_FEATURES):
            dem_vals      = _df_train[dem_col].values
            df_valid[dem_col] = [
                np.average(dem_vals[idx], weights=1.0 / (dist + 1e-6))
                for idx, dist in zip(idxs, dists)
            ]

        # QRF 픽셀별 예측 → 중앙값 집계
        preds   = _qrf.predict(df_valid[FEATURES_ALL], quantiles=[0.05, 0.50, 0.95])
        agb_q05 = float(np.percentile(preds[:, 0], 50))
        agb_med = float(np.percentile(preds[:, 1], 50))
        agb_q95 = float(np.percentile(preds[:, 2], 50))

        pi_width = agb_q95 - agb_q05
        if n_pixels >= 50 and pi_width < 100:
            confidence = "high"
            note       = f"유효 픽셀 {n_pixels:,}개 기반 예측"
        elif n_pixels >= 10:
            confidence = "medium"
            note       = f"유효 픽셀 {n_pixels:,}개 (중간 신뢰도)"
        else:
            confidence = "low"
            note       = f"유효 픽셀 {n_pixels:,}개 (소수 픽셀)"

    # 4. 수종 키 확인
    sp_key = (species_dominant
              if species_dominant in SPECIES_PARAMS
              else "기본활엽")

    # 5. AGB → 입목축적 / 탄소량 변환
    vol_med  = _agb_to_volume(agb_med,  sp_key)
    vol_q05  = _agb_to_volume(agb_q05,  sp_key)
    vol_q95  = _agb_to_volume(agb_q95,  sp_key)
    carb_med = _agb_to_carbon(agb_med,  sp_key)
    carb_q05 = _agb_to_carbon(agb_q05,  sp_key)
    carb_q95 = _agb_to_carbon(agb_q95,  sp_key)

    # 6. Saturation 경고 (GEDI 포화 구간)
    _conifers  = ["잣나무","낙엽송","강원소나무","중부소나무","리기다","기본침엽"]
    sat_warn   = (agb_med > 130) and (species_dominant in _conifers)

    return StandStateEstimate(
        pnu               = pnu,
        geom_wkt          = geom_wkt,
        area_ha           = round(area_ha, 4),
        estimated_at      = datetime.utcnow(),
        species_dominant  = species_dominant,
        species_secondary = species_secondary,
        age_estimate      = age_estimate,
        age_class         = _age_class(age_estimate),
        agb_mg_per_ha     = round(agb_med,  2),
        agb_q05           = round(agb_q05,  2),
        agb_q95           = round(agb_q95,  2),
        volume_m3_per_ha  = round(vol_med,  2),
        volume_q05        = round(vol_q05,  2),
        volume_q95        = round(vol_q95,  2),
        carbon_tc_per_ha  = round(carb_med, 2),
        carbon_q05        = round(carb_q05, 2),
        carbon_q95        = round(carb_q95, 2),
        grade_distribution = _grade_distribution(agb_med),
        n_gedi_footprints  = n_gedi_footprints,
        n_s2_scenes        = n_s2_scenes,
        saturation_warning = sat_warn,
        confidence_level   = confidence,
        confidence_note    = note,
    )
