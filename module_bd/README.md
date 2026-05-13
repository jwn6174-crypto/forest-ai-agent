# Module B / D — 성장 예측 · 시장 · 정책

다목적 산림경영 AI Agent 의 데이터·정책 백엔드.
산주의 필요 정보를 받아, *임분 성장 예측* + *시장 가격* + *법령 정보* 를 자동으로 제공한다.

> **모듈 C (희도) 가 NPV 계산 시 호출하는 모든 데이터·함수의 집합지.**
> 모듈 E (수범) 의 LLM 에이전트가 자연어 답변할 때도 이 모듈에 의존함.

**최종 업데이트:** 2026-05-13 (Day 2 후반)

---

## 🎯 한 줄 요약

```python
# 희도가 모듈 C 에서 이렇게 import 해서 쓸 수 있다.
from module_bd.src.growth_predict import growth_predict, lookup_volume
from module_bd.src.kau_api import fetch_kau_price
from module_bd.src.legal_api import search_law, fetch_law_full
from module_bd.src.legal_rotation import rotation_age
from module_bd.src.market_snapshot import market_snapshot
```

오늘 (Day 2) 기준 6 개 함수가 *production-ready*.

---

## 📋 의사결정 기록

주요 설계 선택의 *근거* 와 *대안 비교* 는 [**DECISIONS.md**](DECISIONS.md) 참조.

현재 기록된 결정:
- **D1**: KOFPI 데이터 수종별 확장 (옵션 B)
- **D2**: 표준품셈 → 비용 함수 (옵션 Y, 진짜 PDF 추출 + 간단 모델)

---

## 📌 진행률

### Module B — 임분 성장 예측 (핵심 함수 완성 ✓)

| 함수 / 산출물 | 상태 | 데이터 출처 | 행 수 |
|---|---|---|---|
| `lookup_volume()` — 개별 수목 재적 | ✅ 완성 | 임목재적표 (Ⅱ장) | 16,163 개 |
| `growth_predict()` — 임분 성장 예측 (가이드 §8.2) | ✅ 완성 | 임분수확표 (Ⅶ장) | 576 행 |
| `yield_table_full.parquet` | ✅ | Ⅱ장 통합 | 14 수종 |
| `yield_table_stand.parquet` | ✅ | Ⅶ장 통합 | 11 수종 |
| 산악기상 시계열 + 보정 | ⏳ | 산악기상 API | 미시작 |
| 지위지수 추정기 | ⏳ | NFI 매칭 | 미시작 |

### Module D — 시장·정책 (핵심 완성)

| 함수 | 상태 | 데이터 출처 |
|---|---|---|
| `fetch_kau_price()` | ✅ | data.go.kr 금융위 |
| `search_law()` + `fetch_law_full()` | ✅ | 법제처 OpenAPI |
| `rotation_age()` — 별표 3 룰베이스 | ✅ NEW | 산림자원법 별표 3 |
| `market_snapshot()` — 가이드 §6.3 핵심 | ✅ NEW | KOFPI PDF 390 행 |
| `get_parcel_polygon()` (VWorld) | ⏳ | VWorld 2D — 인증 키 문제 |
| 표준품셈 → 비용 함수 | ⏳ | 표준품셈 PDF |
| 산림탄소상쇄 RAG 코퍼스 | ⏳ | 가이드라인 PDF 6종 |

---

## 🌲 두 가지 yield 표 — 헷갈리지 말 것

PDF `2014 임목재적·바이오매스 및 임분수확표` 안에 *두 종류의 표* 가 있습니다. **둘 다 필요**하지만 *완전히 다른 표*.

### Ⅱ장 임목재적표 (p.13-103)
**개별 수목 한 그루의 부피** 변환표.
- 입력: 수종, DBH (흉고직경 cm), 수고 (m)
- 출력: 재적 (m³) — *수목 한 그루*
- 용도: 산주가 *내 숲에 DBH 22cm × 수고 18m 인 수목이 있다* → *부피는?*

→ `lookup_volume()` 함수 작동.

### Ⅶ장 임분수확표 (p.191-215) ⭐ 모듈 B의 진짜 핵심
**임분 (1 ha) 의 시간에 따른 성장** 표.
- 입력: 수종, 지위지수 (SI), 임령 (년)
- 출력: ha 당 본수, 평균 DBH, 평균 수고, 재적 (m³/ha), 연평균 생장량
- 용도: 산주가 *25년생 강원지방소나무 SI=14 임분을 50년까지 키우면?* → *재적 173 → 281 m³/ha (1.63배)*

→ `growth_predict()` 함수 작동. **모듈 C 의 Faustmann NPV 계산의 핵심 입력.**

---

## 🛠 함수 API 문서

### `lookup_volume(species, bark, dbh, height, use_draft=False)`

개별 수목 재적 lookup (Ⅱ장 임목재적표).

```python
from module_bd.src.growth_predict import lookup_volume

result = lookup_volume("강원지방소나무", "수피포함", dbh=22, height=18)
# {"volume": 0.3265, "lookup_dbh": 22, "lookup_height": 18, "quality": "OK", "warning": None}
```

### `growth_predict(species, site_index, age_now, forecast_years, climate_scenario)`

임분 성장 예측 — **가이드 §8.2 시그니처 정확 매칭**.

```python
from module_bd.src.growth_predict import growth_predict

trajectory = growth_predict(
    species="강원지방소나무",
    site_index=14,
    age_now=30,
    forecast_years=[0, 5, 10, 15, 20],
    climate_scenario="baseline",
)
# List[dict] — 시간별 trajectory
# [{"dt": ..., "age": 30, "volume": 173.0, "dbh": 16.9, "height": 12.0, 
#   "n_per_ha": 1261, "tmai_m3_per_ha_yr": 5.77, "climate_scenario": "baseline", 
#   "method": "exact", "warning": None}, ...]
```

**파라미터:**
- `species`: 11 가지 (강원/중부지방소나무, 잣나무, 낙엽송, 리기다소나무, 신갈, 상수리/굴참나무, 편백, 자작/백합나무)
- `site_index`: 지위지수 — 수종마다 가능 값 (보통 3~5 단계)
- `age_now`: 현재 임령 (년)
- `forecast_years`: List[int] — 예측 시점 (예: `[0, 5, 10, 15]`)
- `climate_scenario`: `"baseline"` (기본) | `"SSP126"` | `"SSP245"` | `"SSP585"` (현재 baseline 외엔 warning)

### `market_snapshot(date_iso)` ⭐ NEW (Day 2 후반)

**가이드 §6.3 — 특정 날짜의 종합 시장 상태.**

```python
from module_bd.src.market_snapshot import market_snapshot

snap = market_snapshot("2026-05-13")
# {
#   "date": "2026-05-13",
#   "timber_price": {                      # 소나무 기본 (가이드 §6.3 시그니처)
#     "특용재": 360000, "1등급": 199700, "2등급": 173400,
#     "3등급": 158300, "원주재": 148700, "원료재": 75300,
#   },
#   "timber_price_by_species": {           # 7 수종 확장 (옵션 B)
#     "소나무":   {"특용재": 360000, "1등급": 199700, ...},
#     "낙엽송":   {"특용재": 160700, "1등급": 150500, ...},
#     "잣나무":   {"특용재": 169900, "1등급": 154700, ...},
#     "리기다소나무": {"특용재": None, "1등급": 105400, ...},
#     "참나무류": {"특용재": None, "1등급": 114800, ...},
#     "편백":     {"특용재": None, "1등급": 161700, "2등급": 142000, "3등급": None, ...},
#     "삼나무":   {"특용재": None, "1등급": 135000, "2등급": 130000, "3등급": None, ...},
#   },
#   "timber_price_meta": {                 # 정직한 출처·한계 정보
#     "source": "KOFPI 분기별 원목시장가격조사 보고서",
#     "url": "https://www.forest.go.kr (정보공개 → 통합자료실)",
#     "actual_data_period": "2025년 12월 (4분기)",
#     "default_species": "소나무",
#     "grade_changes": "Q3·Q4 부터 편백·삼나무 등급 구성 변경 (3등급 → 원료재급)",
#     "legal_basis": "산림청 고시 제2025-22호 원목규격 고시",
#     "unit": "원/m³",
#     "unit_conversion": {"소나무류": "1m³=0.85톤", "낙엽송류": "0.77톤", ...},
#   },
#   "kau_close": None,         # 추후 fetch_kau_price() 통합
#   "koc_estimate": None,
#   "vcm_floor_wta": 17039,    # 박2020 산주 WTA 하한
#   "discount_rate": 0.05,
# }
```

**핵심 동작:**
- `date_iso` 이전의 *가장 최근 월* KOFPI 데이터 lookup
- 미래 날짜 → 가장 최근 가격 반환 (Faustmann real-price-constant 가정)
- 과거 날짜 (예: `"2025-05-15"`) → Q2 시점 데이터 정확 lookup

### `rotation_age(species, ownership)` ⭐ NEW (Day 2 후반)

산림자원법 시행규칙 별표 3 기준벌기령 룰베이스.

```python
from module_bd.src.legal_rotation import rotation_age

rotation_age("강원지방소나무", "사유림")  # → 40
rotation_age("잣나무", "국유림")          # → 50
rotation_age("낙엽송", "사유림")          # → 30
rotation_age("신갈나무", "사유림")        # → 25 (참나무류 매핑)
```

**소스:** 산림자원의 조성 및 관리에 관한 법률 시행규칙 별표 3 (개정 2023-06-27)
**산출물:** `data/processed/rotation_age.json` (8 카테고리 × 2 소유 = 16 룰)

### `fetch_kau_price(start_date, end_date)`

KAU/KCU 탄소가격 일별 시세 (data.go.kr 금융위).

```python
from module_bd.src.kau_api import fetch_kau_price
df = fetch_kau_price("20260501", "20260513")
```

### `search_law(query)` + `fetch_law_full(law_id)`

법령 검색 + 본문 다운로드 (법제처 OpenAPI).

---

## 📦 데이터 산출

### 통합 데이터 (희도/수범이 직접 사용)

| 파일 | 내용 | 크기 | 사용처 |
|---|---|---|---|
| `data/interim/yield_table_full.parquet` | Ⅱ장 통합, long format | 16,414 행 | `lookup_volume()` |
| `data/interim/yield_table_stand.parquet` | Ⅶ장 통합, long format | 576 행 | `growth_predict()` |
| `data/interim/kofpi_history.parquet` ⭐ NEW | KOFPI 4분기 통합 | 390 행 | `market_snapshot()` |
| `data/processed/rotation_age.json` ⭐ NEW | 별표 3 룰베이스 | 16 룰 | `rotation_age()` |

**`kofpi_history.parquet` 컬럼:**
`연도`, `분기`, `월`, `수종`, `등급`, `가격_원_per_m3`, `source_pdf`

### 원본 데이터

| 위치 | 내용 |
|---|---|
| `data/raw/yield_table_2014.pdf` | 임분수확표 원본 (3.2 MB) |
| `data/raw/kau_daily/*.csv` | KAU 일별 시세 |
| `data/raw/law_extracts/*.xml`, `*.pdf` | 법령 + 별표 |
| `data/raw/kofpi_reports/2025년_{1,2,3,4}분기_*.pdf` ⭐ NEW | KOFPI 분기별 보고서 4 종 |

---

## 📊 KOFPI 데이터 — 진짜 자산 (Day 2 후반)

### 추출 결과 요약
4 분기 × 12 개월 시계열
7 수종 × 6 등급 (편백·삼나무 분기별 형식 변화)
총 390 행
가격 범위: 64,900 ~ 365,900 원/m³

### 수종별 등급 구성

| 수종 | 등급 수 | 등급 | 비고 |
|---|---|---|---|
| 소나무 | 6 | 특용재, 1·2·3, 원주재, 원료재 | 모든 분기 동일 |
| 낙엽송 | 6 | 위와 동일 | 모든 분기 동일 |
| 잣나무 | 6 | 위와 동일 | 모든 분기 동일 |
| 리기다소나무 | 5 | 1·2·3, 원주재, 원료재 | 특용재 없음 |
| 참나무류 | 4 | 1·2·3, 원료재 | 원주재 없음 |
| 편백 | 3 | Q1/Q2: 1·2·3 / Q3/Q4: 1·2, 원료재 | Q3 부터 형식 변경 |
| 삼나무 | 2 또는 3 | Q1/Q2: 2·3 / Q3/Q4: 1·2, 원료재 | Q3 부터 형식 변경 |

### 수종별 가격 차이 (1등급, 2025 Q4 기준)
소나무:        199,700원/m³  (기준)
편백:          161,700원/m³  (-19.0%)
잣나무:        154,700원/m³  (-22.5%)
낙엽송:        150,500원/m³  (-24.6%)
삼나무:        135,000원/m³  (-32.4%)
참나무류:      114,800원/m³  (-42.5%)
리기다소나무:  105,400원/m³  (-47.2%)

→ **수종별 가격 차이 *22-47%*. NPV 계산에 *결정적 영향*. 가이드 §6.3 의 `timber_price` 만으로는 *불충분*. `timber_price_by_species` *필수*.**

### 단위 환산 (KOFPI 보고서 표준)
- 소나무류 (소나무, 잣나무, 리기다소나무): 1m³=0.85톤
- 낙엽송류: 1m³=0.77톤
- 편백류 (편백, 삼나무): 1m³=0.73톤
- 참나무류: 1m³=1톤

---

## ⚠️ 알려진 한계

### 1. Ⅱ장 작은 표 3개는 DRAFT 라벨
이태리·일나무·이태리포플러는 *흉고직경 4-30cm × 수고 4-30m* 의 작은 표.
*품질 == "OK"* 필터로 회피 가능. (영향 적음)

### 2. Ⅶ장 일부 수종 미수록
이태리·일나무·이태리포플러는 임분수확표 *없음*. 시간 예측 불가.
→ `growth_predict()` 가 자동 안내. `lookup_volume()` 으로 개별 수목 가능.

### 3. 자작·백합나무 *(잠정)*
PDF 원문에 *(잠정)* 표시. → `growth_predict()` 가 자동 경고 반환.

### 4. KOFPI 데이터 — 단일 수종 시계열 깊이 ⭐ NEW
- 시계열: *4 분기 (12개월) 만*. 2014-2024 깊은 시계열은 *원본 PDF 추가 다운로드 필요*.
- 다만 *NPV 계산에는 단일 시점 가격으로 충분* (Faustmann real-price-constant 가정).

### 5. 미래 가격 *예측 안 함* ⭐ NEW
- 가이드 §6.3 의 `market_snapshot(date)` 는 *과거 lookup*. *예측 안 함*.
- Faustmann (1849) 학술 표준: *real prices constant + 할인율로 시간가치 흡수*.
- 시계열은 *Figure 2 시연 + 변동성 정량화* 용도.

### 6. fps.kofpi.or.kr 사이트 죽음 ⭐ NEW
- 검색 결과로 발견했지만 *DNS 해결 실패* (Non-existent domain).
- 가이드의 KOFPI URL (`statistics_04.do`) 도 *소나무 1수종만 공개*.
- → **진짜 출처는 `forest.go.kr` 통합자료실의 분기별 PDF 보고서**.

### 7. VWorld PNU → polygon
VWorld API 키 인증 시스템 트럭 문제로 보류. 다른 키 발급 또는 오프라인 임상도 SHP 직접 다운로드 검토.

---

## 🚀 환경 설정 + 실행 방법

### 가상환경
```powershell
.\.venv\Scripts\Activate.ps1
```

### 데이터 재생성 (처음부터)
```powershell
# Module B
python module_bd/src/yield_parse.py          # Ⅱ장 (16,163 개)
python module_bd/src/yield_table_parse.py    # Ⅶ장 (576 행)
python module_bd/src/growth_predict.py       # 함수 테스트

# Module D
python module_bd/src/kau_api.py              # KAU 시세
python module_bd/src/legal_api.py            # 법제처 별표
python module_bd/src/legal_rotation.py       # 별표 3 룰 ⭐ NEW
python module_bd/src/kofpi_parse.py          # KOFPI 4분기 PDF ⭐ NEW
python module_bd/src/market_snapshot.py      # 종합 시장 스냅샷 ⭐ NEW
```

---

## 🔑 필요한 환경 변수 (`.env`)

| 변수 | 출처 | 형식 |
|---|---|---|
| `DATA_GO_KR_KEY` | data.go.kr 마스터키 | 64자 영숫자 |
| `LAW_OC` | 법제처 OpenAPI ID | 영문 ID (예: `nacave`) |
| `VWORLD_KEY` | VWorld 인증키 | UUID 형식 |
| `GEE_ACCOUNT` | Google Earth Engine 계정 | 이메일 |

---

## 📦 디렉토리 구조
module_bd/
├── README.md
├── data/
│   ├── raw/
│   │   ├── yield_table_2014.pdf
│   │   ├── kau_daily/
│   │   ├── law_extracts/
│   │   └── kofpi_reports/        ← NEW (Day 2 후반)
│   │       └── 2025년_{1,2,3,4}분기_원목시장가격조사_보고서.pdf
│   ├── interim/
│   │   ├── yield_table_full.parquet
│   │   ├── yield_table_stand.parquet
│   │   └── kofpi_history.parquet  ← NEW
│   └── processed/
│       └── rotation_age.json      ← NEW
├── src/
│   ├── kau_api.py
│   ├── legal_api.py
│   ├── legal_rotation.py          ← NEW
│   ├── yield_parse.py
│   ├── yield_table_parse.py
│   ├── growth_predict.py
│   ├── kofpi_parse.py             ← NEW
│   ├── kofpi_diagnose.py          ← NEW (학습 기록)
│   ├── kofpi_diagnose_text.py     ← NEW (학습 기록)
│   ├── fps_diagnose.py            ← NEW (실패 기록)
│   └── market_snapshot.py         ← NEW
├── notebooks/
├── scrapers/
└── tests/

---

## 💡 학습 메모

### KOFPI 데이터 추출의 진짜 통찰 ⭐ NEW (Day 2 후반)
1. **가이드의 KOFPI URL (`statistics_04.do`) 은 소나무 1수종만 공개**. 7 수종 데이터는 *분기별 PDF 보고서*에 있음.
2. **fps.kofpi.or.kr 사이트 죽음** (DNS 해결 실패). 검색 결과는 살아있는 듯 보이지만 *2026-05 시점 사이트 없음*.
3. **분기별 등급 구성 변화**: Q3 부터 편백·삼나무 *3등급 → 원료재급* 으로 형식 변경. 시장 조사 방식 변화 반영.
4. **수종별 가격 22-47% 차이**: 가이드는 수종 차원 안 요구하지만 *현실에서는 필수*.
5. **미래 가격 예측 안 함**: Faustmann 학술 표준 + 가이드의 `market_snapshot(date)` 도 *과거 lookup*. 시계열은 *시연 + 변동성 맥락*.

### PDF 파싱 — KOFPI 보고서 패턴
- *수종명이 그 수종 등급들의 *중간 행 자리* 에 위치* (PDF 셀 세로 가운데 정렬 결과)
- *수종 영역 결정 알고리즘* (보정값 ±2/±3) 보다 **명시적 매핑** (분기별 등급 리스트) 이 *훨씬 정확*
- substring 함정: "리기다소나무" 안에 "소나무" 포함 → `if sp in line` 으로 잘못 매칭

### data.go.kr OpenAPI
- 마스터키 1개로 *신청 완료된 API* 모두 호출 가능
- URL 파라미터는 `serviceKey`
- KAU 데이터는 *영업일 1일 + 오후 1일* 이후 업데이트. 주말·공휴일 영향 큼

### 법제처 OpenAPI
- URL 파라미터는 `OC` (정우 OC: `nacave`)
- 응답은 *XML 형식*
- 별표는 *PDF/HWP 파일링크* 로만 제공 (텍스트로 직접 안 옴)
- 별표 3 PDF: `flSeq=161301293` (2026-02-01 시행 기준)

### camelot + PDF
- 격자 줄이 있는 PDF: `flavor="lattice"` 우선
- 격자 없으면 `flavor="stream"` 시도
- KOFPI PDF: pdfplumber 텍스트 추출 + 정규식 패턴이 *훨씬 정확*

---

## 🔄 변경 이력

### Day 2 후반 (2026-05-13 오후)
- ⭐ **rotation_age()** — 산림자원법 별표 3 룰베이스 (8 카테고리 × 2 소유 = 16 룰)
- ⭐ **KOFPI 4분기 PDF 추출** — 2025년 1-4분기 보고서 → 390 행 시계열
- ⭐ **market_snapshot(date)** — 가이드 §6.3 시그니처 정확 매칭 + 수종별 확장
- ⭐ **fps.kofpi.or.kr 진단** — 사이트 죽음 확인 + 진짜 출처 발견
- ⭐ **growth_predict() 리팩토링** — 가이드 §8.2 시그니처 (`forecast_years`, `climate_scenario`)

### Day 2 전반 (2026-05-13 오전)
- ✅ **Ⅶ장 임분수확표 발견** (p.191-215) — 모듈 B 핵심
- ✅ `growth_predict()` 첫 버전 완성
- ✅ Ⅱ장 두번째 페이지 (수고 30-52m) 추출 — stream flavor

### Day 1 (2026-05-12)
- ✅ data.go.kr, 법제처, VWorld API 키 발급
- ✅ `kau_api.py`, `legal_api.py` 완성
- ✅ 임분수확표 PDF 다운로드 + 구조 분석
- ✅ Ⅱ장 임목재적표 22/25 케이스 추출

---

## 📌 다음 작업 (우선순위)

1. **GitHub 원격 repo + 팀 공유** (오프셔, 15-30분) ⭐ 팀 핸드오프 핵심
2. **shared/schemas.py — 팀 인터페이스 합의** (Pydantic 모델, 30분)
3. **fetch_kau_price() 를 market_snapshot() 에 통합** (15분) — KAU/KOC 빈 칸 채우기
4. **표준품셈 → 비용 함수** (모듈 D, 1-2시간)
5. **산림탄소상쇄 RAG 코퍼스** (모듈 D + E, 2-3시간)
6. **산악기상 시계열** (모듈 B 보정, 2-3시간)
7. **모듈 A 위성 GEE** (1주+)
8. **VWorld 재시도** (외부 시스템 의존, 추후)