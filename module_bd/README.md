# Module B / D — 성장 예측 · 시장 · 정책

다목적 산림경영 AI Agent 의 데이터·정책 백엔드.
산주에게 필요한 정보를 받아, *임분 성장 예측* + *시장 가격* + *법령 정보* + *비용 추정* + *탄소 흡수* + *정책 RAG* 을 자동으로 제공한다.

> **모듈 C (희도) 가 NPV 계산 시 호출하는 모든 데이터·함수의 집합지.**
> 모듈 E (수범) 의 LLM 에이전트가 자연어 응답 시 호출하는 핵심 모듈.

**최종 업데이트:** 2026-05-28 (Day 7 완료 — 모듈 B/D 책임 13/13 완성)

**Repo 상태:** 78+ commits + 17 DECISIONS + 5/5 진단 PDF 데이터 + RAG 281 청크 + 단위 테스트 59개 + ASOS 5 시군 30년 평년 (55MB) + NEX-GDDP SSP 시나리오

---

## 🎯 한 줄 요약

```python
# 희도가 모듈 C 에서 이렇게 import 해서 쓸 수 있다.
from module_bd.src.growth_predict import growth_predict, lookup_volume
from module_bd.src.grade_distribution import grade_distribution
from module_bd.src.market_snapshot import market_snapshot
from module_bd.src.cost_function import cost_function
from module_bd.src.legal_rotation import rotation_age
from module_bd.src.kau_api import fetch_kau_price
from module_bd.src.legal_api import search_law, fetch_law_full

# 팀 인터페이스 (Pydantic)
from shared.schemas import GrowthForecast, MarketSnapshot, CostInput, CostBreakdown, RotationRule
```

---

## 📦 함수 시그니처 (가이드 §8.2 매칭)

### 1. `growth_predict()` — 임분 성장 + 탄소 + 등급분포 + 기후 보정 ⭐ Day 7 통합 완성

```python
trajectory = growth_predict(
    species="강원지방소나무",
    site_index=14,
    age_now=30,
    forecast_years=[0, 10, 20, 30],
    climate_scenario="baseline",   # "baseline" | "SSP245" | "SSP585"
    elev=350,                      # 해발고 (m) — 기후 보정에 필요 (D15)
    sigun="보은",                  # 충북 시군 — NEX anomaly lookup (D15)
)
# 반환: List[dict] — 각 시점 임분 상태
# 키: dt, age, volume, dbh, height, n_per_ha, tmai_m3_per_ha_yr,
#     carbon_uptake_rate (tCO2/ha/yr, 국립산림과학원 표준),
#     grade_distribution (소경/중경/대경 본수, Weibull D14),
#     volume_corrected (기후 보정 V, D15), climate_residual,
#     climate_extrapolation (외삽 여부 플래그, D15)
```

성장(임분수확표) + 탄소(국립산림과학원) + 등급분포(Weibull D14) +
기후보정(climate_correct D13-D17 + NEX-GDDP D15) 통합. 가이드 §8.1
GrowthForecast 전 필드 충족.

### 2. `grade_distribution()` — 등급별 본수 (Weibull) ⭐ Day 7

```python
g = grade_distribution(age_class=4, imsang="활엽수림(H)", n_total_per_ha=600)
# 반환: dict — 소경재/중경재/대경재 (본수), proportions, shape, scale, fallback
# 영급 × 임상 23 그룹 우선, 영급 7 fallback, nearest fallback
```

### 3. `market_snapshot()` — 시장 종합

```python
snap = market_snapshot(date_iso="2026-05-15")
#   timber_price, timber_price_by_species (7 수종), kau_close, koc_estimate, ...
```

### 4. `cost_function()` — 5/5 진짜 데이터

```python
result = cost_function(
    volume_m3=280, area_ha=1.0, distance_to_road_km=15,
    action="clearcut", skidding_distance_m=800, slope_class="중",
    species="강원지방소나무",
)
#   breakdown, total, unit_costs, data_sources, limitations
```

### 5. `rotation_age()` — 법정 기준벌기령

```python
rule = rotation_age("강원지방소나무", ownership="공사유림")  # → 40 (년)
```

### 6. `lookup_volume()` — 개별 나무 재적

```python
result = lookup_volume(species="강원지방소나무", bark="수피포함", dbh=20, height=15)
```

### 7. `fetch_kau_price()` / `search_law()` — KAU 일별 / 법령 검색

### 8. `climate_correct` (v8) — 기후 보정 회귀 (Day 7 완성) ⭐

```python
import joblib, pandas as pd

# v8 모델 (NFI 5+6+7차 시계열 패널 + SI, R² 0.228)
saved = joblib.load("module_bd/data/processed/climate_correct.pkl")
model, features = saved['model'], saved['features']

input_data = pd.DataFrame([{
    'temp_anomaly_30y': 0.7, 'prcp_anomaly_30y': 60,
    'gdd_anomaly': 200, 'vpd_anomaly': 0.2,
    'elev': 350, 'imsang_code': 1, 'si': 14,   # si 추가 (D17)
}])
predicted_residual = model.predict(input_data)[0]  # m³/ha
# 보정 임목축적 = V_table + predicted_residual
```

> growth_predict() 가 SSP245/SSP585 시나리오 시 NEX-GDDP anomaly 를
> 이 모델에 넣어 자동 보정 (D15). 미래 기온이 학습 범위 밖이면 외삽
> 경고 자동 표시 (climate_extrapolation 플래그).

---

## ✅ 단위 테스트 (가이드 §9.1)

```bash
pytest module_bd/tests/
```

59개 테스트. 검증 테스트(가이드·법령 보증값, 물리 법칙)와
회귀 테스트(현재 출력 기준선)로 구분.

| 테스트 파일 | 개수 | 대상 |
|---|---|---|
| test_growth_predict.py | 8 | 가이드 §9.1 검증값, 단조성, 회귀 기준선 |
| test_cost_function.py | 11 | D6 기준 총비용, 회계 항등식, 단조성 |
| test_rotation_age.py | 10 | 별표3 법정값 (소나무·잣나무·낙엽송) |
| test_lookup_volume.py | 8 | 재적 양수·단조성, 그리드 스냅 |
| test_market_snapshot.py | 8 | KOFPI 7수종 등급순서, WTA·할인율 |
| test_grade_distribution.py | 14 | Weibull 등급분포 (검증 11 + 회귀 3) ⭐ Day 7 |

---

## 📁 디렉토리 구조 (Day 7 추가분 ⭐)

```
module_bd/
├── README.md          ← (이 파일, v13)
├── DECISIONS.md       ← 17 결정 학술 문서화 (D1-D17)
├── src/
│   ├── growth_predict.py        # B 핵심 + 탄소 + 등급분포 + 기후보정 통합 ⭐ Day 7
│   ├── grade_distribution.py    # 등급분포 Weibull 예측 (D14) ⭐ Day 7
│   ├── weibull_fit.py           # Weibull fit → json (D14) ⭐ Day 7
│   ├── market_snapshot.py · cost_function.py · kau_api.py
│   ├── kofpi_parse.py · kofpi_transport_parse.py
│   ├── legal_api.py · legal_rotation.py · carbon_offset_chunk.py
│   ├── yield_parse.py · yield_parse_small.py · yield_table_parse.py
│   ├── mt_weather_*.py · forest_household_parse.py
│   ├── asos_collect.py · asos_chungbuk_collect.py
│   ├── climate_correct/         # climate_correct 본 구현 폴더
│   │   ├── asos_features.py · asos_chungbuk_features.py
│   │   ├── climate_features_panel.py # 시기별 anomaly 패널 (5+6+7차, 70행) ⭐ Day 7
│   │   └── fit_correct.py       # LightGBM 회귀 (v8 best, R² 0.228) ⭐ Day 7
│   └── diagnose/                # 일회성 진단 스크립트
│       ├── weibull_probe.py     # DBH 분포 진단 (D14) ⭐ Day 7
│       ├── nfi5_coord_probe.py  # NFI 5차 좌표 체계 진단 (D16) ⭐ Day 7
│       ├── nfi5_extract.py      # NFI 5차 추출 (영문→한글, 수고 cm→m) ⭐ Day 7
│       ├── nfi6_extract.py · nfi_5_6_7_probe.py
│       └── (기타 진단)
└── data/
    ├── raw/
    │   ├── carbon/ · carbon_offset/ · forest_household_economy/
    │   ├── kau_daily/ · kofpi_reports/ · law_extracts/
    │   ├── mt_weather/ · asos/ (5 시군 1991-2020)
    │   ├── nfi/                 # NFI raw xlsx (gitignore, 5/6/7차)
    │   │   ├── nfi5_chungbuk_{stand,tree}.csv  # 5차 추출 (D16) ⭐ Day 7
    │   │   ├── nfi6_chungbuk_{stand,tree}.csv  # 6차 추출
    │   │   └── nfi7_chungbuk_{stand,tree}.csv  # 7차 추출
    │   ├── nex/                 # NEX-GDDP SSP anomaly (D15) ⭐ Day 7
    │   │   └── nex_gddp_chungbuk_anomaly.csv
    │   ├── seedling/ · standard_cost/ · wage/
    │   └── yield_table_2014.pdf
    ├── interim/
    │   ├── yield_table_full.parquet · yield_table_stand.parquet
    │   ├── kofpi_*.parquet/csv · carbon_chunks.jsonl
    └── processed/
        ├── rotation_age.json · forest_household_economy.json
        ├── mt_weather_{daily,monthly,annual}.csv
        ├── asos_anomaly_panel.csv        # 5+6+7차 시계열 패널 (70행) ⭐ Day 7
        ├── weibull_params.json           # 23 그룹 + 7 fallback 모수 (D14) ⭐ Day 7
        ├── nex_scenario_anomaly.csv       # NEX SSP anomaly (D15) ⭐ Day 7
        └── climate_correct.pkl           # v8 best 모델 (R² 0.228) ⭐ Day 7
```

---

## 🎓 학술 자산

### 모듈 B (성장)
| 데이터 | 출처 | 비고 |
|---|---|---|
| 임분수확표 (Ⅶ장) | 산림청 임분수확표 2014 | 11 수종 × SI × 임령 |
| 입목수간재적표 (Ⅱ장) | 산림청 임분수확표 2014 | 16,163 행 |
| 탄소흡수량 (수종·임령별) | 국립산림과학원 (3,212 표본 × 40년) | |
| 산악기상 시계열 | 국립산림과학원 산악기상정보 | 보은 6 관측소, 수집·전처리 완료 |
| ASOS 30년 평년 | 기상청 ASOS API (data.go.kr) | 5 시군 × 1991-2020, 54,790일 |
| **NFI 5+6+7차 충북** | **국가산림자원조사 (산림빅데이터팀, 2006-2020)** | **시계열 3시점, 3,131 표본점, 137,436 그루** ⭐ Day 7 |
| **등급분포 Weibull (D14)** | **NFI 충북 46,722 그루 DBH 분포 fit** | **23 그룹 (영급×임상), 왜도 +1.112** ⭐ Day 7 |
| **climate_correct() v8** | **NFI 5+6+7차 + ASOS 시계열 패널 + SI 회귀** | **R² 0.228, 2,194 행 패널, best 모델** ⭐ Day 7 |
| **NEX-GDDP-CMIP6 SSP** | **NASA/GDDP-CMIP6 (GEE 직접 추출)** | **5모델 앙상블, 2021-2050, ssp245/585** ⭐ Day 7 |

### 모듈 D (시장)
| 데이터 | 출처 | 비고 |
|---|---|---|
| 원목 가격 (7 수종 × 6 등급) | KOFPI 분기별 보고서 | 4 분기 시계열 |
| KAU 일별 종가 | 한국거래소 | API 연동 |
| WTA 산주 의지가격 | 박2020 (Park, 2020) | 17,039원/tCO2 |

### 모듈 D (비용)
| 데이터 | 출처 | 비고 |
|---|---|---|
| 벌채 노동 | 산림사업 표준품셈 p.59-60 | 벌목부 25.5 m³/인일 |
| 집재/운반/상차 | KOFPI 분기별 | 9,300-36,200원/m³ |
| 조림 노동 | 산림사업 표준품셈 p.73 | 1.33 특별 + 20 보통 인부 |
| 시중 노임 | 대한건설협회 통계 | 248,140원/인일 (벌목부) |
| 묘목 단가 | 산림청 2025 공식 (시행령 제16조) | 422원/본 (강원소나무) |

### 모듈 D (법령 · 정책 RAG · 임가경제)
| 데이터 | 출처 | 비고 |
|---|---|---|
| 기준벌기령 | 산림자원법 별표 3 (개정 2023-06-27) | 룰베이스 JSON |
| 법령 검색 | 법제처 API | 실시간 |
| 산림탄소상쇄 11 PDF | 산림탄소등록부 | 281 청크, 8 사업유형 |
| 임가경제조사 (충북 5년치) | 산림임업통계플랫폼 | 2020~2024 |

---

## 📋 의사결정 기록 (DECISIONS.md, 17 항목)

| ID | 결정 | 날짜 |
|---|---|---|
| D1-D4 | KOFPI · 표준품셈 · cost_function · schemas | 2026-05-13 |
| D5-D7 | carbon_uptake · seedling · RAG corpus | 2026-05-15 |
| D8 | 산악기상 시계열 수집 설계 | 2026-05-16~22 |
| D9 | 임가경제 데이터 | 2026-05-19 |
| D10 | 산악기상 전처리 (일/월/연) | 2026-05-24 |
| D11 | NFI 7차 단위·구조 검증 | 2026-05-27 |
| D12 | NFI 7차 추출 + 보은 진단 | 2026-05-27 |
| D13 | climate_correct 회귀 설계 (v5 R² 0.204) | 2026-05-27 |
| **D14** | **등급분포 Weibull fit (왜도 +1.112, 14 테스트)** | **2026-05-28** |
| **D16** | **NFI 5차 통합 — 시계열 3시점 (v7, std 절반)** | **2026-05-28** |
| **D17** | **SI 변수 추가 (v8 R² 0.228) + measure_year ablation** | **2026-05-28** |
| **D15** | **기후 보정 통합 — NEX-GDDP SSP + 외삽 정직 감지** | **2026-05-28** |

→ [DECISIONS.md](./DECISIONS.md) 전체 보기

---

## 🎯 가이드 §1.2 책임 안 (13 항목) — 13/13 완성 ⭐

```
✅ 임분수확표 PDF 파싱 → DB 적재
✅ growth_predict() (11 수종) + 탄소 + 등급분포 + 기후보정 통합
✅ KOFPI 등급별 원목가격 스크래핑
✅ KAU 일별 종가 API 연동
✅ 표준품셈 → 비용 함수
✅ 법제처 별표 3 → 룰베이스
✅ 산림탄소상쇄 가이드라인 → RAG 코퍼스
✅ Pydantic 스키마 (shared/schemas.py)
✅ 탄소 흡수량 통합 (carbon_uptake_rate)
✅ 임가경제·임산물 (D9, 충북 5년치)
✅ 산악기상 시계열 (가이드 §2.3, D8+D10)
✅ climate_correct() (v8, R² 0.228, NFI 5+6+7차 + SI) ⭐ Day 7
✅ 등급분포 Weibull (D14, NFI 충북 46,722 그루) ⭐ Day 7
```

→ **13/13 완성** ⭐ 모듈 B/D 핵심 책임 전부 완료.

추가 통합 (가이드 §8.1 GrowthForecast 충족):
- growth_predict() ↔ grade_distribution (등급분포 trajectory)
- growth_predict() ↔ climate_correct.pkl (SSP 시나리오 보정, NEX-GDDP)

---

## 🎯 가이드 §1.3 산출물

```
✅ Lead (Module C) — GrowthForecast, MarketSnapshot, CostFunction,
   RotationRule, climate_correct.pkl, grade_distribution
✅ Person 4 (Module E) — chunked PDF (carbon_chunks.jsonl)
⚠️ Person 2 (Module A) — NFI 표본점 (좌표 추출 완료, 위성 매칭은 협업)
```

---

## 🌟 Day 7 핵심 진전

### 1. 등급분포 Weibull (D14)
- NFI 충북 46,722 그루 DBH 분포, 왜도 +1.112 (Weibull 교과서적 적합)
- 영급 × 임상 23 그룹 fit. 대경재 비율 영급 단조 증가 (0.1% → 17.8%)
- growth_predict() 통합: 강원소나무 30→60년 대경재 64→120본

### 2. climate_correct R² 끌어올리기 (정직한 ablation)
| 버전 | 구성 | R² | 비고 |
|---|---|---|---|
| v5 | 6+7차 (시점 2) | 0.204 ±0.074 | Day 6 |
| v7 | 5+6+7차 (시점 3) | 0.204 ±0.038 | NFI 5차 통합, 안정성 2배 |
| **v8** | **+ SI** | **0.228** | **best** |
| v9 | + measure_year | 0.223 | 효과 없음 → 제거 |

- NFI 5차 통합 (D16): 좌표/ID/코드 6/7차 동일 발견 → 변환 불필요
- 차수별 잔차 단조 증가 (5차 -6.1 → 7차 +11.7) = 온난화/임분성숙 신호
- measure_year 효과 없음 → anomaly 가 시간 trend 이미 흡수 = 기후변수 정당성 입증

### 3. 기후 보정 통합 (D15)
- NEX-GDDP-CMIP6 GEE 직접 추출 (5모델, 2021-2050, ssp245/585)
- growth_predict(climate_scenario="SSP245", elev=350) 작동
- **외삽 정직 감지**: 미래 기온(+1.4~1.7) > 학습 범위(+1.16) → 외삽
  경고 자동 표시. "보정값 방향성 참고용, SSP 구분 제한적" 명시.

---

## 📌 다음 작업 (선택)

- 발표용 Figure (가이드 §9.2): 차수별 잔차 추세, Weibull 곡선, SSP 보정 비교
- 충북 보은 지역 특화 운반비 (KOFPI 전국 평균 → 지역)
- 보육·간벌 재투입 비용 모델
- 모듈 A 위성 GEE (민석 주도, 별도 세션)

---

## 🚀 사용 예시 — 김씨 산주 시나리오

```python
from module_bd.src.growth_predict import growth_predict
from module_bd.src.market_snapshot import market_snapshot
from module_bd.src.cost_function import cost_function
from module_bd.src.legal_rotation import rotation_age

# 1. 성장 예측 (기후 보정 포함)
forecast = growth_predict(
    species="강원지방소나무", site_index=14, age_now=30,
    forecast_years=[0, 20], climate_scenario="SSP245", elev=350,
)
# 30년: V=173 m³/ha, C=10.77 tCO2/ha/yr, 등급[소799 중398 대64]
# 50년: V=281 m³/ha, 기후보정 V_corrected (외삽 경고 동반)

# 2-4. 시장·비용·법령 (생략 — 위 함수 시그니처 참조)
# 5. 희도 모듈 C: Faustmann NPV (원목+탄소+다각화 - 비용)
```

---

## 🔧 환경 설정

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# pandas, numpy, pyarrow, pdfplumber, openpyxl, pydantic, requests, pytest,
# lightgbm, scikit-learn, joblib, scipy (climate_correct + Weibull),
# pyproj (NFI 좌표 EPSG:5181 → WGS84)
# NEX-GDDP 는 GEE JavaScript Code Editor 에서 추출 (Python 의존성 아님)
```

---

## 📞 연락

- GitHub: https://github.com/jwn6174-crypto/forest-ai-agent
- 정우 (Module B/D 담당): Kookmin University Forest Environmental Systems