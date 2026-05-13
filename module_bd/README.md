# Module B / D — 성장 예측 · 시장 · 정책

다목적 산림경영 AI Agent 의 데이터·정책 백엔드.
산주의 임야 정보를 받아, *임분 성장 예측* + *시장 가격* + *법령 정보* 를 자동으로 제공한다.

> **모듈 C (희도) 가 NPV 계산할 때 호출하는 모든 데이터·함수의 집합지.**
> 모듈 E (수범) 의 LLM 에이전트가 자연어 답변할 때도 이 모듈을 거친다.

**최종 업데이트:** 2026-05-13 (Day 2)

---

## 🎯 한 줄 요약

```python
# 희도가 모듈 C 에서 이렇게 import 해서 쓸 수 있다.
from module_bd.src.growth_predict import growth_predict, lookup_volume
from module_bd.src.kau_api import fetch_kau_price
from module_bd.src.legal_api import search_law, fetch_law_full
```

오늘 (Day 2) 기준 위 4개 함수가 *production-ready*.

---

## 📊 진척도

### Module B — 임분 성장 예측 (핵심 함수 완성 ✅)

| 함수 / 산출물 | 상태 | 데이터 출처 | 행/값 |
|---|---|---|---|
| `lookup_volume()` — 개별 나무 재적 | ✅ 완성 | 입목수간재적표 (Ⅱ장) | 16,163 값 |
| `growth_predict()` — 임분 성장 예측 | ✅ 완성 | 임분수확표 (Ⅶ장) | 576 행 |
| `yield_table_full.parquet` | ✅ | Ⅱ장 통합 | 14 수종 |
| `yield_table_stand.parquet` | ✅ | Ⅶ장 통합 | 11 수종 |
| 산악기상 시계열 + 보정 | ⏳ | 산악기상 API | 미시작 |
| 지위지수 추정기 | ⏳ | NFI 매칭 | 미시작 |

### Module D — 시장·정책 (일부 완성)

| 함수 | 상태 | 데이터 출처 |
|---|---|---|
| `fetch_kau_price()` | ✅ | data.go.kr 금융위 |
| `search_law()` + `fetch_law_full()` | ✅ | 법제처 OpenAPI |
| `get_parcel_polygon()` (VWorld) | ⏳ | VWorld 2D — 인증 외부 문제 |
| KOFPI 원목가격 | ⏳ | KOFPI 웹 스크래핑 |
| 별표 3 → 기준벌기령 룰베이스 | ⏳ | 별표 3 PDF (다운로드 완료) |
| 표준품셈 → 비용 함수 | ⏳ | 표준품셈 PDF |
| 산림탄소상쇄 RAG 코퍼스 | ⏳ | 가이드라인 PDF 6종 |

---

## 🌲 두 가지 yield 표 — 헷갈리지 마세요

PDF `2014 임목재적·바이오매스 및 임분수확표` 안에 *두 종류의 표* 가 있습니다. **둘 다 필요**하지만 *완전히 다른 의미*.

### Ⅱ장 입목수간재적표 (p.13-103)

**개별 나무 한 그루의 부피** 변환표.

- 입력: 수종, DBH (흉고직경 cm), 수고 (m)
- 출력: 재적 (m³) — *나무 한 그루*
- 용도: 산주가 *내 산에 DBH 22cm × 수고 18m 인 나무가 있다* → *부피는?*

이 데이터로 `lookup_volume()` 함수 작동.

### Ⅶ장 임분수확표 (p.191-215) ⭐ 모듈 B의 진짜 핵심

**임분 (1 ha) 의 시간에 따른 성장** 표.

- 입력: 수종, 지위지수 (SI), 임령 (년)
- 출력: ha 당 본수, 평균 DBH, 평균 수고, 재적 (m³/ha), 연평균 생장량
- 용도: 산주가 *25년생 강원지방소나무 SI=14 임분을 50년까지 키우면?* → *재적 173 → 281 m³/ha (1.63배)*

이 데이터로 `growth_predict()` 함수 작동. **모듈 C 의 Faustmann NPV 계산의 핵심 입력.**

---

## 🚀 함수 API 문서

### `lookup_volume(species, bark, dbh, height, use_draft=False)`

개별 나무의 재적 lookup (Ⅱ장 입목수간재적표).

```python
from module_bd.src.growth_predict import lookup_volume

result = lookup_volume("강원지방소나무", "수피포함", dbh=22, height=18)
# {
#   "volume": 0.3265,         # m³ (한 그루)
#   "lookup_dbh": 22,         # 실제 사용한 DBH (가장 가까운 값)
#   "lookup_height": 18,
#   "quality": "OK",
#   "warning": None,
# }
```

**파라미터:**
- `species`: 수종명 — 14 개 가능 (강원지방소나무, 잣나무, 낙엽송, 해송 등)
- `bark`: `"수피포함"` (기본) 또는 `"수피제외"`
- `dbh`: 흉고직경 (cm). 표에 없으면 가장 가까운 값 사용.
- `height`: 수고 (m). 표에 없으면 가장 가까운 값 사용.
- `use_draft`: `True` 면 작은 표 (해송/삼나무/이태리포플러) DRAFT 데이터 사용

**경고 조건:**
- 빈 셀 매칭 (예: DBH 5cm × 수고 50m — 물리적으로 불가능)
- 근접값 사용 (요청과 1cm/1m 초과 차이)
- DRAFT 데이터 (작은 표)

### `growth_predict(species, site_index, age_now, target_age)`

임분 성장 예측 (Ⅶ장 임분수확표).

```python
from module_bd.src.growth_predict import growth_predict

result = growth_predict("강원지방소나무", site_index=14, age_now=30, target_age=50)
# {
#   "current": {
#     "age": 30, "dbh_cm": 16.9, "height_m": 12.0, "dominant_height_m": 14.0,
#     "n_per_ha": 1261, "volume_m3_per_ha": 173.0, "tmai_m3_per_ha_yr": 5.77,
#     "method": "exact",
#   },
#   "future": {
#     "age": 50, "dbh_cm": 26.7, "height_m": 15.6, ...
#     "volume_m3_per_ha": 281.8, ...
#   },
#   "growth": {
#     "years": 20,
#     "dbh_increase_cm": 9.8,
#     "height_increase_m": 3.6,
#     "volume_increase_m3_per_ha": 108.8,
#     "volume_ratio": 1.63,
#     "n_mortality": 486,     # 자연 고사 그루 수
#   },
#   "warning": None,
# }
```

**파라미터:**
- `species`: 11 개 (강원/중부지방소나무, 잣나무, 낙엽송, 리기다소나무, 편백, 상수리/굴참/신갈나무, 자작/백합나무)
- `site_index`: 지위지수 — 수종마다 가능 값 다름 (보통 3~5 단계)
- `age_now`: 현재 임령 (년)
- `target_age`: 목표 임령 (년)

**보간:**  
표에 없는 임령은 *양 옆 값으로 선형 보간*. 예: 임령 32년 → 30년·35년 사이 보간.

**경고 조건:**
- `age_now > target_age` (역방향 예측 불가)
- 임령 범위 밖 (예: 90년 — 표는 보통 10~80년만)
- 자작나무·백합나무 *(잠정)* 데이터
- 해송·삼나무·이태리포플러는 Ⅶ장에 없음 → `lookup_volume()` 대안 안내

### `fetch_kau_price(start_date, end_date)`

KAU/KCU 탄소가격 일별 시세 (data.go.kr 금융위).

```python
from module_bd.src.kau_api import fetch_kau_price

df = fetch_kau_price("20260501", "20260513")
# DataFrame: 거래일, 종목명, 종가, 시가, 고가, 저가, 거래량 등
```

### `search_law(query)` + `fetch_law_full(law_id)`

법령 검색 + 본문 다운로드 (법제처 OpenAPI).

```python
from module_bd.src.legal_api import search_law, fetch_law_full

results = search_law("산림자원의 조성")
# [{"법령ID": "...", "법령명": "...", ...}, ...]

xml_path = fetch_law_full(law_id="265430")
# 법령 XML 본문 + 별표 PDF 다운로드
```

---

## 📁 데이터 자산

### 통합 데이터 (희도/수범이 직접 사용)

| 파일 | 내용 | 크기 | 사용처 |
|---|---|---|---|
| `data/interim/yield_table_full.parquet` | Ⅱ장 통합, long format | 16,414 행 | `lookup_volume()` |
| `data/interim/yield_table_stand.parquet` | Ⅶ장 통합, long format | 576 행 | `growth_predict()` |

**`yield_table_full.parquet` 컬럼:**  
`수종`, `수피여부`, `흉고직경(cm)`, `수고(m)`, `재적(m³)`, `품질` (`"OK"` or `"DRAFT"`)

**`yield_table_stand.parquet` 컬럼:**  
`수종`, `지위지수`, `임령(년)`, `평균DBH(cm)`, `단면적(m²/ha)`, `평균수고(m)`, `우세목수고(m)`, `본수(본/ha)`, `재적(m³/ha)`, `정기평균생장량(m³/ha)`, `정기평균생장률(%)`, `연평균생장량(m³/ha/yr)`

### 원본 데이터

| 위치 | 내용 |
|---|---|
| `data/raw/yield_table_2014.pdf` | 임분수확표 원본 (3.2 MB) |
| `data/raw/kau_daily/*.csv` | KAU 일별 시세 |
| `data/raw/law_extracts/*.xml`, `*.pdf` | 법령 + 별표 |

---

## 🗺️ PDF 페이지 매핑

### Ⅱ장 입목수간재적표 (각 수종 2 페이지)
PDF page = 책 page + 6

| # | 수종 | 수피포함 | 수피제외 |
|---|---|---|---|
| 1 | 강원지방소나무 | 14-15 | 18-19 |
| 2 | 중부지방소나무 | 22-23 | 26-27 |
| 3 | 해송 (DRAFT) | 30-31 | — |
| 4 | 리기다소나무 | 32-33 | 36-37 |
| 5 | 잣나무 | 40-41 | 44-45 |
| 6 | 낙엽송 | 48-49 | 52-53 |
| 7 | 삼나무 (DRAFT) | 56-57 | — |
| 8 | 편백 | 58-59 | 62-63 |
| 9 | 상수리나무 | 66-67 | 70-71 |
| 10 | 굴참나무 | 74-75 | 78-79 |
| 11 | 신갈나무 | 82-83 | 86-87 |
| 12 | 자작나무 | 90-91 | 92-93 |
| 13 | 백합나무 | 94-95 | 98-99 |
| 14 | 이태리포플러 (DRAFT) | 102-103 | — |

### Ⅶ장 임분수확표 (수종별 2~3 페이지)

| # | 수종 | 페이지 | SI 단계 |
|---|---|---|---|
| 1 | 강원지방소나무 | 192-193 | 12/14/16/18 |
| 2 | 중부지방소나무 | 194-195 | 10/12/14/16 |
| 3 | 리기다소나무 | 196-198 | 10/12/14/16/18 |
| 4 | 잣나무 | 199-200 | 3 단계 |
| 5 | 낙엽송 | 201-203 | 5 단계 |
| 6 | 편백 | 204-205 | 3 단계 |
| 7 | 상수리나무 | 206-207 | 3 단계 |
| 8 | 굴참나무 | 208-209 | 4 단계 |
| 9 | 신갈나무 | 210-211 | 3 단계 |
| 10 | 자작나무 *(잠정)* | 212-213 | 4 단계 |
| 11 | 백합나무 *(잠정)* | 214-215 | 5 단계 (임령 5-40만) |

> 해송·삼나무·이태리포플러는 **Ⅶ장에 없음**. `growth_predict()` 가 명시적 경고 반환.

---

## ⚠️ 알려진 한계

### 1. Ⅱ장 작은 표 3개 — DRAFT 라벨

해송·삼나무·이태리포플러는 *흉고직경 4-30cm × 수고 4-30m* 의 작은 표.  
pdfplumber 텍스트 추출 시 페이지 경계 모호로 일부 값 정렬 어긋남.

**검증 사례:** 해송 DBH 6cm × 수고 22m = 0.3652 m³ (물리적으로 불가능 — 페이지 31 큰 DBH 값이 페이지 30 에 섞임).

**영향:** 충북 보은 (파일럿) 주력 수종 = 강원지방소나무·잣나무·낙엽송. 작은 표 수종은 *시연 영향 작음*. `품질 == "OK"` 필터로 우회.

### 2. Ⅶ장 미수록 수종

해송·삼나무·이태리포플러는 Ⅶ장 임분수확표 *없음*. 시간 예측 불가.  
→ `growth_predict()` 가 자동 안내. `lookup_volume()` 으로 개별 나무는 가능.

### 3. 자작나무·백합나무 *(잠정)*

PDF 원문 자체에 *(잠정)* 표시.  
→ `growth_predict()` 가 자동 경고 반환.

### 4. VWorld PNU → polygon

VWorld API 키 인증 시스템 외부 문제로 보류. 다른 키 발급 또는 다드림 임상도 SHP 직접 다운로드 검토.

---

## 🛠️ 환경 설정 + 재현 방법

### 가상환경

```powershell
# venv 활성화 (PowerShell)
.\.venv\Scripts\Activate.ps1
```

### 데이터 재생성 (처음부터)

```powershell
# 1. KAU 시세
python module_bd/src/kau_api.py

# 2. 법제처 별표
python module_bd/src/legal_api.py

# 3. Ⅱ장 입목수간재적표 (16,163 값)
python module_bd/src/yield_parse.py

# 4. Ⅶ장 임분수확표 (576 행) ⭐ 모듈 B 핵심
python module_bd/src/yield_table_parse.py

# 5. 함수 테스트
python module_bd/src/growth_predict.py
```

### 진단 도구 (필요시)

```powershell
python module_bd/src/pdf_structure.py    # PDF 장 헤더 + 키워드 검색
python module_bd/src/cell_debug.py       # 특정 페이지 셀 구조 확인
python module_bd/src/page_debug.py       # 페이지 매핑 검증
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

## 📁 디렉토리 구조
module_bd/
├── README.md              ← 이 문서
├── data/
│   ├── raw/               — API/PDF 원본
│   │   ├── yield_table_2014.pdf
│   │   ├── kau_daily/
│   │   └── law_extracts/
│   ├── interim/           — 정형화된 중간 결과
│   │   ├── yield_table_full.parquet    ← Ⅱ장 통합
│   │   ├── yield_table_stand.parquet   ← Ⅶ장 통합
│   │   └── yield_*.csv                 ← 수종별 CSV
│   └── processed/         — 모델 입력용 (예정)
├── src/
│   ├── kau_api.py              ← Module D: KAU 시세
│   ├── legal_api.py            ← Module D: 법제처 별표
│   ├── yield_parse.py          ← Ⅱ장 추출
│   ├── yield_parse_small.py    ← Ⅱ장 작은 표 (DRAFT)
│   ├── yield_table_parse.py    ← Ⅶ장 추출 ⭐
│   ├── growth_predict.py       ← lookup_volume + growth_predict ⭐
│   ├── pdf_structure.py        ← 진단 도구
│   ├── cell_debug.py           ← 진단 도구
│   └── page_debug.py           ← 진단 도구
├── notebooks/             — 탐색·분석용 Jupyter (예정)
├── scrapers/              — Scrapy 프로젝트 (예정)
└── tests/                 — 단위 테스트 (예정)

---

## 📚 학습 메모

### data.go.kr OpenAPI
- 마스터키 1개로 *활용신청 완료된 API* 모두 호출 가능
- URL 파라미터 이름은 `serviceKey`
- KAU 데이터는 *영업일 1일 + 오후 1시* 이후 업데이트. 주말·공휴일 영향 큼
- 정확한 엔드포인트는 `apis.data.go.kr/.../getXXXX` 상세 페이지에서 *상세기능 목록* 확인 필수
- KAU25(2025년 vintage)만 활발히 거래되고 KOC(산림 오프셋)는 거래량 0인 경우 다수

### 법제처 OpenAPI
- URL 파라미터 이름은 `OC` (정우 OC: `nacave`)
- 응답은 *XML 형식*
- 별표는 *PDF/HWP 파일링크* 로만 제공 (텍스트로는 안 풀어줌)
- 별표 번호가 *법령 본문 별표* 와 *서식 별표* 에 *독립적으로 매겨져 중복* 발생 → 제목 키워드 필터 필요
- 별표 3 PDF는 `flSeq=161301293` (2026-02-01 시행 기준)

### camelot + PDF
- 격자 선이 있는 표라도 camelot이 *셀 구분선을 못 보는* 경우 흔함
- `flavor="lattice"` 가 안 되면 `"stream"` 시도
- **PDF 안에서 표마다 셀 인식 방식이 다름:**
  - Ⅱ장 첫 페이지 (수고 6-28m): lattice + 셀 안 뭉침 후처리 (3 가지 패턴)
  - Ⅱ장 둘째 페이지 (수고 30-52m): lattice 실패 → stream
  - Ⅶ장: lattice + 개별 셀 분리 (후처리 거의 불필요)
- 임시 PDF 파일 정리 시 Windows에서 *PermissionError* 발생 가능 (백신 충돌, 무시 가능)
- **책 페이지 번호 ≠ PDF 페이지 번호** — 항상 `pdfplumber`로 텍스트 직접 확인 권장

### PDF 셀 split 패턴 3가지 (Ⅱ장 첫 페이지)
- **패턴 A** (p.14 등): 셀 안에 `\n` 으로 값마다 분리 (372 줄)
- **패턴 B** (p.22 등): 셀 안에 `\n` 으로 행 구분 + 공백으로 행 안 값 구분
- **패턴 C** (작은 표 p.30 등): 빈 셀 자리에 `\u3000` (전각공백) 표시

### 환경 운영
- VS Code에서 New File 만들 때 *대상 폴더를 먼저 클릭*해서 선택. 아니면 엉뚱한 위치에 생성됨
- PowerShell 첫 venv 활성화 시 `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` 필요
- `.env`를 *절대 채팅·스크린샷·commit에 노출 금지*. 노출 시 즉시 재발급
- `git rm --cached <file>`은 *디스크는 안 지우고 staging에서만 제외* — 데이터 파일 제외할 때 유용
- PowerShell 스크롤백 한계 ~3000 줄. 큰 출력은 `python script.py > output.txt` 로 파일 저장
- Python stdout 인코딩 UTF-8 강제: `$env:PYTHONIOENCODING="utf-8"` (한글 출력 깨짐 방지)

---

## 🔄 변경 이력

### Day 2 (2026-05-13)
- ⭐ **Ⅶ장 임분수확표 발견** (p.191-215) — Day 1 의 Ⅱ장 추출만으로는 모듈 B 가이드 요구 사항 미충족
- ⭐ `growth_predict()` 함수 완성 — 576 행 임분수확표 위에서 작동
- ⭐ `lookup_volume()` 함수 완성 — 16,163 값 입목수간재적표 위에서 작동
- Ⅱ장 둘째 페이지 (수고 30-52m) 추출 완성 — stream flavor 필요
- 자작나무 NaN 8개 = 실제 빈 셀로 검증 (작은 DBH × 큰 수고 = 물리적 불가능)
- 작은 표 3개 (해송·삼나무·이태리포플러) DRAFT 라벨 + 영향 평가

### Day 1 (2026-05-12)
- data.go.kr, 법제처, VWorld API 키 발급
- `kau_api.py`, `legal_api.py` 완성
- 임분수확표 PDF 다운로드 + 구조 분석
- Ⅱ장 입목수간재적표 22/25 케이스 추출
- PDF 페이지 매핑 발견 (책 page + 6)
- camelot 셀 패턴 3가지 발견

---

## 🚧 다음 작업 (우선순위)

1. **별표 3 → 기준벌기령 룰베이스** (모듈 D, 30-60분)
2. **shared/schemas.py — 팀 인터페이스 합의** (Pydantic 모델, 30분)
3. **KOFPI 원목가격 스크래핑** (모듈 D, 1-2시간)
4. **산악기상 시계열** (모듈 B 보정, 2-3시간)
5. **표준품셈 → 비용 함수** (모듈 D, 1-2시간)
6. **산림탄소상쇄 RAG 코퍼스** (모듈 D + E, 2-3시간)
7. **모듈 A 위성 GEE** (모듈 A, 1주+)
8. **GitHub 원격 repo + 팀 공유** (인프라, 30분)
9. **VWorld 재시도** (외부 시스템 의존, 추후)