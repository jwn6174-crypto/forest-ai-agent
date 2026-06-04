# Module A — 위성 AGB Nowcasting
> 다목적 산림경영 AI Agent · 2026 공모전

---

## 개요

Module A는 위성 원격탐사 데이터와 GEDI 라이다 기반 지상부 바이오매스(AGB) 라벨을 결합하여, 현지 조사 없이 임분의 현재 상태를 추정하는 모듈입니다.

```
위성 이미지 (Sentinel-2 / SAR / PALSAR / DEM)
        ↓
  Quantile Random Forest
        ↓
AGB (Mg/ha) · 입목축적 (m³/ha) · 탄소량 (tC/ha)
+ 90% 예측 구간 · DBH 등급 분포 · 포화 경고
```

---

## 데이터

| 데이터 | 출처 | 설명 |
|--------|------|------|
| GEDI L4A | NASA/LARSE | 지상부 바이오매스 라벨 (Mg/ha) |
| Sentinel-2 SR | ESA/Copernicus | 광학 반사율 9밴드 + 식생지수 5개 |
| Sentinel-1 GRD | ESA/Copernicus | SAR (VV/VH) |
| ALOS-2 PALSAR | JAXA | L밴드 SAR (HH/HV) |
| ALOS AW3D30 | JAXA | DEM (elev/slope/northness/eastness) |
| NFI 7차 | 산림청 | 외부 검증용 (보은군 102개 표본점) |
| 임상도 2024 | 산림청 | 수종·영급 정보 |

**학습 데이터**: `boeun_gedi_training_clean.csv`
- 행: 11,026개 GEDI footprint (보은군)
- 피처: 25개 위성 피처
- 라벨: agbd (Mg/ha), NDVI≥0.3 필터 적용

---

## 피처 목록 (25개)

```python
FEATURES = [
    # Sentinel-2 광학 (9밴드)
    'B2', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B11', 'B12',
    # 식생지수 (5개)
    'NDVI', 'NDRE', 'NBR', 'NDMI', 'EVI',
    # Sentinel-1 SAR (4개)
    'VV_mean', 'VH_mean', 'VV_std', 'VV_VH_ratio',
    # PALSAR L밴드 (3개)
    'HH_db', 'HV_db', 'HH_HV_db',
    # 지형 (4개)
    'elev', 'slope', 'northness', 'eastness'
]
```

> B3 제거: B2·B4와 상관계수 0.9+ (다중공산성)

---

## 모델 성능

| 모델 | R² | RMSE | 비고 |
|------|----|------|------|
| RF baseline | 0.413 | 65.7 Mg/ha | B3 포함 |
| **RF (최종)** | **0.479** | **59.3 Mg/ha** | B3 제거, NDVI≥0.3 |
| Quantile RF | 0.471 | 59.8 Mg/ha | 90%PI coverage=0.916 |
| XGBoost | 0.438 | 61.7 Mg/ha | — |

### NFI 외부 검증

- n=86 표본점, R²=-0.187, RMSE=145.9 m³/ha
- **한계**: GEDI saturation 문제로 AGB>200 Mg/ha 구간 과소추정
- 모델 적용 범위: AGB < 200 Mg/ha (보은군 산림 평균 103.8 Mg/ha)

### 보은군 AGB 공간 추정 결과 (2023)

- 산림면적: 69,208 ha (전체 면적의 58.2%)
- AGB 평균: 103.8 Mg/ha
- AGB 최대: 276.5 Mg/ha

---

## 모델 파라미터

```python
# Quantile Random Forest (최종 모델)
RandomForestQuantileRegressor(
    n_estimators=1000,
    max_features=0.5,
    min_samples_leaf=5,
    min_samples_split=5,
    n_jobs=-1,
    random_state=42
)

# 샘플 가중치 (GEDI 측정 불확실성 반영)
sample_weight = 1 / (agbd_se + 1)
```

---

## 출력 스키마

```python
class StandStateEstimate(BaseModel):
    pnu:               str           # 필지번호
    geom_wkt:          str           # 폴리곤 WKT (EPSG:4326)
    area_ha:           float         # 면적 (ha)
    estimated_at:      datetime      # 추정 시각
    species_dominant:  str           # 우점수종
    species_secondary: Optional[str] # 부수종
    age_estimate:      Optional[int] # 임령 (년)
    age_class:         Optional[str] # 영급 (예: 5영급)
    agb_mg_per_ha:     float         # AGB 중앙값 (Mg/ha)
    agb_q05:           float         # AGB 5% 분위
    agb_q95:           float         # AGB 95% 분위
    volume_m3_per_ha:  float         # 입목축적 (m³/ha)
    volume_q05:        float
    volume_q95:        float
    carbon_tc_per_ha:  float         # 탄소량 (tC/ha)
    carbon_q05:        float
    carbon_q95:        float
    grade_distribution: Dict[str, float]  # DBH 등급 분포
    n_gedi_footprints:  int          # 사용된 GEDI footprint 수
    n_s2_scenes:        int          # 사용된 S2 장면 수
    saturation_warning: bool         # AGB>130 + 침엽수 경고
    confidence_level:   str          # "high" / "medium" / "low"
    confidence_note:    Optional[str]
```

---

## 사용법

```python
from module_a import predict_stand

result = predict_stand(
    geom_wkt="POLYGON((127.72 36.49, 127.725 36.49, ...))",
    pnu="4374010100100010000",
    species_dominant="신갈",
    species_secondary="굴참",
    age_estimate=45,
    n_gedi_footprints=12,
    n_s2_scenes=8,
)

print(result.agb_mg_per_ha)    # AGB (Mg/ha)
print(result.volume_m3_per_ha) # 입목축적 (m³/ha)
print(result.carbon_tc_per_ha) # 탄소량 (tC/ha)
print(result.confidence_level) # "high" / "medium" / "low"
```

### 출력 예시

```json
{
  "pnu": "4374010100100010000",
  "area_ha": 24.84,
  "species_dominant": "신갈",
  "age_class": "5영급",
  "agb_mg_per_ha": 107.3,
  "agb_q05": 68.2,
  "agb_q95": 189.4,
  "volume_m3_per_ha": 124.8,
  "carbon_tc_per_ha": 72.1,
  "grade_distribution": {
    "치수": 0.12, "소경": 0.38, "중경": 0.31,
    "대경1": 0.14, "대경2": 0.04, "대경3": 0.01, "초대경": 0.0
  },
  "saturation_warning": false,
  "confidence_level": "high",
  "confidence_note": "유효 픽셀 2561개 기반 예측"
}
```

---

## 변환 계수 (산림과학원)

AGB → 입목축적: `V = AGB / (D × BEF)`  
AGB → 탄소량: `C = AGB × (1 + R) × CF`

| 수종 | D (밀도) | BEF | R (지하부) | CF (탄소분율) |
|------|---------|-----|-----------|-------------|
| 잣나무 | 0.41 | 1.35 | 0.28 | 0.49 |
| 낙엽송 | 0.45 | 1.34 | 0.29 | 0.51 |
| 신갈 | 0.66 | 1.45 | 0.43 | 0.47 |
| 굴참 | 0.72 | 1.45 | 0.43 | 0.47 |
| 기본침엽 | 0.44 | 1.50 | 0.28 | 0.51 |
| 기본활엽 | 0.60 | 1.43 | 0.38 | 0.47 |

---

## 파일 구조

```
데이터/
├── boeun_gedi_training_clean.csv   # 학습 데이터 (11,026개)
├── qrf_model.pkl                   # 학습된 QRF 모델
├── boeun_satellite_features_10m.tif # 위성 피처 raster (25밴드, 10m)
├── boeun_agb_10m.tif               # AGB 예측 raster (q05/q50/q95)
├── nfi_boeun_holdout.csv           # NFI 외부 검증 데이터
└── fig1_gedi_scatter.png           # Fig 1
    fig2_nfi_validation.png         # Fig 2
    fig3_agb_map.png                # Fig 3
```

---

## 한계 및 향후 과제

1. **GEDI Saturation**: AGB > 130 Mg/ha 구간에서 과소추정 발생 (RF 포화 문제)
2. **DEM 누락**: GEE export 시 DEM 밴드 미추출 → 학습 데이터 KNN 보간으로 대체
3. **NFI 외부검증**: R²=-0.187 (고AGB 침엽수림 과소추정이 주원인)
4. **향후**: GEE에서 DEM 별도 export 후 통합, 전국 스케일 확장

---

## 환경

```
Python 3.11 (conda: forest)
주요 패키지: earthengine-api, geopandas, rasterio,
             scikit-learn, quantile-forest, pydantic
GEE 프로젝트: constant-goods-461116-r4
```

---

*Module A — 위성 AGB Nowcasting | 2026 다목적 산림경영 AI Agent 공모전*
