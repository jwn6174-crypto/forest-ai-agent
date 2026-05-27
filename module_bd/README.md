# Module B / D — 성장 예측 · 시장 · 정책

다목적 산림경영 AI Agent 의 데이터·정책 백엔드.
산주에게 필요한 정보를 받아, *임분 성장 예측* + *시장 가격* + *법령 정보* + *비용 추정* + *탄소 흡수* + *정책 RAG* 을 자동으로 제공한다.

> **모듈 C (희도) 가 NPV 계산 시 호출하는 모든 데이터·함수의 집합지.**
> 모듈 E (수범) 의 LLM 에이전트가 자연어 응답 시 호출하는 핵심 모듈.

**최종 업데이트:** 2026-05-27 (Day 6 진행 중)

**Repo 상태:** 66 commits + 13 DECISIONS + 5/5 진짜 PDF 데이터 + RAG 281 청크 + 단위 테스트 45개

---

## 🎯 한 줄 요약

```python
# 희도가 모듈 C 에서 이렇게 import 해서 쓸 수 있다.
from module_bd.src.growth_predict import growth_predict, lookup_volume
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

### 1. `growth_predict()` — 임분 성장 + 탄소 흡수

```python
trajectory = growth_predict(
    species="강원지방소나무",
    site_index=14,
    age_now=30,
    forecast_years=[0, 10, 20, 30],
    climate_scenario="baseline",
)
# 반환: List[dict] — 각 시점 임분 상태
# 키: dt, age, volume, dbh, height, n_per_ha, tmai_m3_per_ha_yr,
#     carbon_uptake_rate (tCO2/ha/yr, 국립산림과학원 표준)
```

### 2. `market_snapshot()` — 시장 종합

```python
snap = market_snapshot(date_iso="2026-05-15")
# 반환: dict
#   timber_price: 소나무 6 등급 (가이드 기본)
#   timber_price_by_species: 7 수종 × 6 등급 (확장)
#   kau_close, koc_estimate, vcm_floor_wta, discount_rate
```

### 3. `cost_function()` — 5/5 진짜 데이터

```python
result = cost_function(
    volume_m3=280, area_ha=1.0,
    distance_to_road_km=15, action="clearcut",
    skidding_distance_m=800, slope_class="중",
    species="강원지방소나무",
)
# 반환: dict
#   breakdown: harvest, skidding, transport, loading, regen
#   total, subtotal, admin_overhead_amount
#   unit_costs, data_sources, limitations
```

### 4. `rotation_age()` — 법정 기준벌기령

```python
rule = rotation_age("강원지방소나무", ownership="공사유림")  # → 40 (년)
```

### 5. `lookup_volume()` — 개별 나무 재적

```python
result = lookup_volume(
    species="강원지방소나무",
    bark="수피포함", dbh=20, height=15,
)
# 반환: volume (m³), quality, warning
```

### 6. `fetch_kau_price()` — KAU 일별

```python
price_data = fetch_kau_price(date_iso="2025-12-31")
```

### 7. `search_law()` — 법령 검색

```python
laws = search_law(query="기준벌기령")
```

---

## ✅ 단위 테스트 (가이드 §9.1)

```bash
pytest module_bd/tests/
```

45개 테스트, 함수 5개 커버. 검증 테스트(가이드·법령 보증값, 물리 법칙)와
회귀 테스트(현재 출력 기준선)로 구분.

| 테스트 파일 | 개수 | 대상 |
|---|---|---|
| test_growth_predict.py | 8 | 가이드 §9.1 검증값, 단조성, 회귀 기준선 |
| test_cost_function.py | 11 | D6 기준 총비용, 회계 항등식, 단조성 |
| test_rotation_age.py | 10 | 별표3 법정값 (소나무·잣나무·낙엽송) |
| test_lookup_volume.py | 8 | 재적 양수·단조성, 그리드 스냅 |
| test_market_snapshot.py | 8 | KOFPI 7수종 등급순서, WTA·할인율 |

---

## 📁 디렉토리 구조

```
module_bd/
├── README.md          ← (이 파일, v10)
├── DECISIONS.md       ← 13 결정 학술 문서화
├── src/
│   ├── growth_predict.py        # B 모듈 핵심 + carbon
│   ├── yield_parse.py           # Ⅱ장 입목수간재적표 파싱
│   ├── yield_parse_small.py     # 작은 표 (해송/삼나무/이태리포플러) DRAFT
│   ├── yield_table_parse.py     # Ⅶ장 임분수확표 파싱
│   ├── market_snapshot.py       # 시장 종합 + 7 수종
│   ├── cost_function.py         # 5/5 진짜 데이터 비용
│   ├── kau_api.py               # KAU 일별 종가
│   ├── kofpi_parse.py           # KOFPI 분기별 가격
│   ├── kofpi_transport_parse.py # KOFPI 거리별 운반비
│   ├── legal_api.py             # 법제처 API
│   ├── legal_rotation.py        # 별표 3 룰베이스
│   ├── carbon_offset_chunk.py   # RAG 코퍼스 chunking
│   ├── mt_weather_api.py        # 산악기상 API (Day 4)
│   ├── mt_weather_collect.py    # 산악기상 수집 (429 대응, Day 4)
│   ├── mt_weather_process.py    # 산악기상 전처리 — 일/월/연 csv ⭐ Day 5
│   ├── forest_household_parse.py # 임가경제 파싱 ⭐ Day 4
│   ├── diagnose/                # 일회성 진단 스크립트
│   │   ├── frsas_probe.py       # 산림자원통계 API 진단 ⭐ Day 4
│   │   └── kosis_probe.py       # KOSIS 진단
│   └── standard_cost_diagnose{1-4}.py  # 표준품셈 진단 학습 기록
├── tests/             ← 단위 테스트 45개 ⭐ Day 4
└── data/
    ├── raw/
    │   ├── carbon/              # 국립산림과학원 탄소흡수량
    │   │   └── carbon_uptake_2003.json
    │   ├── carbon_offset/       # 산림청 산림탄소상쇄 PDF 21개
    │   ├── forest_household_economy/  # 임가경제조사 엑셀 ⭐ Day 4
    │   │   ├── 임업손익계산서_충청북도_2020-2024.xlsx
    │   │   └── 주요지표_월별지표_2020-2024.xlsx
    │   ├── kau_daily/           # KAU 일별 CSV
    │   ├── kofpi_reports/       # KOFPI 분기별 PDF (4 분기)
    │   ├── law_extracts/        # 법령 캐시
    │   ├── mt_weather/          # 산악기상 원본 (수집 완료, 6 관측소 jsonl) ⭐ Day 5
    │   ├── seedling/            # 산림청 묘목 단가 2025
    │   ├── standard_cost/       # 산림사업 표준품셈 PDF
    │   ├── wage/                # 대한건설협회 노임 2025
    │   └── yield_table_2014.pdf # 임분수확표 원본
    ├── interim/
    │   ├── yield_table_full.parquet     # Ⅱ장 통합 (16,163 행)
    │   ├── yield_table_stand.parquet    # Ⅶ장 통합 (576 행)
    │   ├── kofpi_history.parquet/csv    # 수종별 가격 시계열
    │   ├── kofpi_transport.parquet/csv  # 거리별 운반비
    │   ├── kofpi_skidding.parquet/csv   # 거리별 집재비
    │   └── carbon_chunks.jsonl          # RAG 281 청크
    └── processed/
        ├── rotation_age.json    # 별표 3 룰베이스
        └── forest_household_economy.json  # 임가경제 5년치 ⭐ Day 4
```

---

## 🎓 학술 자산

### 모듈 B (성장)
| 데이터 | 출처 | 비고 |
|---|---|---|
| 임분수확표 (Ⅶ장) | 산림청 임분수확표 2014 | 11 수종 × SI × 임령 |
| 입목수간재적표 (Ⅱ장) | 산림청 임분수확표 2014 | 16,163 행 |
| 탄소흡수량 (수종·임령별) | 국립산림과학원 (3,212 표본 × 40년) | |
| 산악기상 시계열 | 국립산림과학원 산악기상정보 | 보은 6 관측소, 수집·전처리 완료 ⭐ Day 5 |

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
| 집재 단가 | KOFPI 분기별 소운반비 | 9,300-18,400원/m³ |
| 운반 단가 | KOFPI 분기별 대운반비 | 14,600-36,200원/m³ |
| 상차비 | KOFPI 분기별 | 5,800원/m³ |
| 조림 노동 | 산림사업 표준품셈 p.73 | 1.33 특별 + 20 보통 인부 |
| 시중 노임 | 대한건설협회 통계 (통계법 제365004호) | 248,140원/인일 (벌목부) |
| 묘목 단가 | 산림청 2025 공식 (시행령 제16조) | 422원/본 (강원소나무) |

### 모듈 D (법령)
| 데이터 | 출처 | 비고 |
|---|---|---|
| 기준벌기령 | 산림자원법 별표 3 (개정 2023-06-27) | 룰베이스 JSON |
| 법령 검색 | 법제처 API | 실시간 |

### 모듈 D (정책 RAG)
| 데이터 | 출처 | 비고 |
|---|---|---|
| 산림탄소상쇄 11 PDF | 산림탄소등록부 (carbonregistry.forest.go.kr) | 281 청크 |
| 사업유형 8개 | 2025.1.2. 기준 방법론 | 신규조림·재조림, 산림경영, 식생복구, 목제품, 바이오매스, 수종갱신, 산불피해지, 산지전용 |

### 모듈 D (임가경제) ⭐ Day 4
| 데이터 | 출처 | 비고 |
|---|---|---|
| 임가경제조사 (충북 5년치) | 산림청 임가경제조사 (산림임업통계플랫폼) | 임업손익계산서·주요지표, 2020~2024 |

---

## 🏗 팀 인터페이스 (shared/schemas.py)

5 Pydantic 모델 — 가이드 §8.1 호환 + 우리 확장 (옵션 P2):

```python
from shared.schemas import (
    GrowthForecast,     # 성장 예측 결과 + carbon_uptake_rate
    MarketSnapshot,     # 시장 종합 + by_species 확장
    CostInput,          # 비용 함수 입력
    CostBreakdown,      # 비용 함수 출력 + 출처 메타
    RotationRule,       # 법정 벌기 + 법적 근거
)
```

---

## 📋 의사결정 기록 (DECISIONS.md)

학술 자산 — 시연·논문 Methods 섹션 활용:

| ID | 결정 | 날짜 |
|---|---|---|
| **D1** | KOFPI 데이터 — 수종별 확장 (옵션 B) | 2026-05-13 |
| **D2** | 표준품셈 → 비용 함수 — 옵션 Y | 2026-05-13 |
| **D3** | cost_function() — KOFPI 우선 + 표준품셈 보완 (5/5 진짜) | 2026-05-13 |
| **D4** | shared/schemas.py — 가이드 + 확장 (옵션 P2) | 2026-05-13 |
| **D5** | carbon_uptake_rate — 국립산림과학원 통합 | 2026-05-15 |
| **D6** | 묘목 단가 — 산림청 2025 공식 매핑 | 2026-05-15 |
| **D7** | 산림탄소상쇄 RAG 코퍼스 — 11 PDF 281 청크 | 2026-05-15 |
| **D8** | 산악기상 시계열 — 데이터 소스·수집 설계 (Day 3-5, 완료) | 2026-05-16 ~ 2026-05-22 |
| **D9** | 임가경제 데이터 — 임업 다각화 보조 수입 | 2026-05-19 |
| **D10** | 산악기상 시계열 전처리 — 임지 단위 일/월/연 통계 | 2026-05-24 |
| **D11** | NFI 7차 데이터 — 단위·구조·지침서 동등성 검증 | 2026-05-27 |
| **D12** | NFI 7차 추출본 csv 저장 + 보은 깊은 진단 | 2026-05-27 |
| **D13** | climate_correct() 회귀 설계 — 8개 결정 + 한계 정직 기록 | 2026-05-27 |

→ [DECISIONS.md](./DECISIONS.md) 전체 보기

---

## 🎯 가이드 §1.2 책임 안 (11 항목)

```
✅ 임분수확표 PDF 파싱 → DB 적재
✅ growth_predict() (11 수종)
✅ KOFPI 등급별 원목가격 스크래핑
✅ KAU 일별 종가 API 연동
✅ 표준품셈 → 비용 함수
✅ 법제처 별표 3 → 룰베이스
✅ 산림탄소상쇄 가이드라인 → RAG 코퍼스
✅ Pydantic 스키마 (shared/schemas.py)
✅ 탄소 흡수량 통합 (carbon_uptake_rate)
✅ 임가경제·임산물 (D9, 충북 5년치)
✅ 산악기상 시계열 (가이드 §2.3, D8+D10) — 6 관측소 수집·전처리 완료
⏳ 등급분포 Weibull (NFI 활용) — 모듈 A 협업 필요
```

→ **11/12 완성**. 등급분포 Weibull 및 climate_correct 회귀는 NFI(모듈 A) 대기.
핵심 책임 모두 완성.

---

## 🎯 가이드 §1.3 산출물 (Lead/팀에게 줄 것)

```
✅ Lead (Module C) — GrowthForecast, MarketSnapshot, CostFunction, RotationRule
✅ Person 4 (Module E) — chunked PDF (carbon_chunks.jsonl)
⚠️ Person 2 (Module A) — NFI 표본점 (모듈 A 협업 필요, 추후)
```

---

## 📌 다음 작업 (우선순위)

### 완료 ✅ (Day 1-4)
1. ✅ 모듈 B/D 7 함수 완성
2. ✅ shared/schemas.py 5 모델
3. ✅ 통합 데이터 자산 + 281 RAG 청크
4. ✅ 9 학술 결정 (DECISIONS.md)
5. ✅ 5/5 진짜 PDF 데이터 (가이드 §7.1 placeholder 함정 정정)
6. ✅ Faustmann + 탄소 통합 (carbon_uptake_rate)
7. ✅ 산림청 공식 묘목 단가 (15 수종 매핑)
8. ✅ 산림탄소상쇄 RAG 코퍼스 (11 PDF → 281 청크)
9. ✅ 단위 테스트 45개 (가이드 §9.1)
10. ✅ 임가경제 데이터 (충북 5년치, D9)

### Day 5+ 우선순위
1. **등급분포 Weibull** — NFI 실측 필요, 모듈 A 협업 시점에
2. **climate_correct() 회귀** — NFI 잔차 + 산악기상 시계열 결합
3. **모듈 A 위성 GEE 시작** — 큰 작업, 별도 세션 (민석 주도)
4. **발표용 Figure** (가이드 §9.2)

### 보완 (작은 추가)
- 충북 보은 지역 특화 운반비 (KOFPI 전국 평균 → 지역)
- 보육·간벌 재투입 비용 모델
- 표준품셈 26개 할증 추가 (작업시기·이동거리·집단화)
- 산림탄소상쇄 search 함수 (Person 4 책임, 우리는 데이터만)

---

## 🚀 사용 예시 — 김씨 산주 시나리오

```python
# 시나리오: 김씨 (충북 보은), 강원소나무 30년생, 1.5ha, 도로 12km
from module_bd.src.growth_predict import growth_predict
from module_bd.src.market_snapshot import market_snapshot
from module_bd.src.cost_function import cost_function
from module_bd.src.legal_rotation import rotation_age

# 1. 30년 → 50년 성장 예측
forecast = growth_predict(
    species="강원지방소나무", site_index=14,
    age_now=30, forecast_years=[0, 20],
)
# 30년 현재: V=173 m³/ha, C=10.77 tCO2/ha/yr (탄소 흡수 피크)
# 50년 후:   V=281 m³/ha, C=4.92 tCO2/ha/yr (감소)

# 2. 시장 가격
snap = market_snapshot("2026-05-15")
# 소나무 1등급: 199,700원/m³
# KAU: 17,200원/tCO2

# 3. 벌채 비용 (50년 시점)
cost = cost_function(
    volume_m3=281 * 1.5, area_ha=1.5,
    distance_to_road_km=12, action="clearcut",
    skidding_distance_m=800, slope_class="중",
    species="강원지방소나무",
)
# 총 약 3,200만원

# 4. 법정 벌기령 확인
rotation = rotation_age("강원지방소나무", ownership="공사유림")  # 40년
# → 30년 벌채는 *조건부 가능* (재해·병해충 등 예외 사유)

# 5. 희도 모듈 C 에서 Faustmann NPV 계산
# 수입 (원목 + 탄소 + 임업 다각화 보조 수입) - 비용 → LEV
# 시나리오 비교: 지금 벌채 vs 50년 → 추천
```

→ AI Agent 가 산주에게 *진짜 데이터 + 진짜 정책* 통합 답변.

---

## 🔧 환경 설정

```bash
# Python 3.11+
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
# 또는 source .venv/bin/activate  # Linux/macOS

pip install -r requirements.txt

# 의존성:
# - pandas, numpy, pyarrow
# - pdfplumber (PDF 파싱), openpyxl (엑셀 파싱)
# - pydantic (스키마)
# - requests (KAU·산악기상 API)
# - pytest (단위 테스트)
```

---

## 📞 연락

- GitHub: https://github.com/jwn6174-crypto/forest-ai-agent
- 정우 (Module B/D 담당): Kookmin University Forest Environmental Systems