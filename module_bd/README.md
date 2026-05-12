# Module B/D — 시장·성장·정책

## 작업 진행 상황 (2026-05-12 기준)

### ✅ 완성된 함수

| 파일 | 함수 | 출처 | 결과물 |
|---|---|---|---|
| `src/kau_api.py` | `fetch_kau_price()` | data.go.kr 금융위 | `data/raw/kau_daily/*.csv` |
| `src/legal_api.py` | `search_law()`, `fetch_law_full()` | 법제처 OpenAPI | `data/raw/law_extracts/*.xml`, `*.pdf` |

### ⚠️ 작업 중 / 보류

| 파일 | 상태 | 비고 |
|---|---|---|
| `src/growth_api.py` | 빈 응답 다수 | 산림생장정보 API는 한정된 (수종, 키, 직경) 조합만 응답. 정확한 표기 찾기 또는 임분수확표 PDF로 대체 |
| `src/legal_diagnose.py` | 임시 도구 | XML 구조 파악용. 추후 삭제 가능 |

### ⏳ 예정

- [ ] 임분수확표 PDF 파싱 (camelot) → `data/interim/yield_table.parquet`
- [ ] KOFPI 원목가격 스크래퍼
- [ ] VWorld PNU → polygon 함수
- [ ] 별표 3 PDF → 수종별 기준벌기령 표 추출

## 환경 설정

```powershell
# 가상환경 활성화 (PowerShell)
.\.venv\Scripts\Activate.ps1

# 실행
python module_bd/src/kau_api.py
python module_bd/src/legal_api.py
```

## 필요한 환경 변수 (.env)

- `DATA_GO_KR_KEY` — data.go.kr 마스터키 (64자)
- `LAW_OC` — 법제처 OC (영문 ID)
- `VWORLD_KEY` — VWorld 인증키 (UUID 형식)
- `GEE_ACCOUNT` — Google Earth Engine 계정

## 디렉토리 설명

- `data/raw/` — API에서 받은 원본 (XML, PDF, CSV)
- `data/interim/` — 정형화된 중간 결과 (parquet)
- `data/processed/` — 모델 입력용 최종 데이터
- `notebooks/` — 탐색·분석용 Jupyter
- `src/` — 재사용 가능한 함수 모듈
- `scrapers/` — Scrapy 프로젝트
- `tests/` — 단위 테스트
- `figures/` — 발표·논문용 그림

## 학습 메모

### data.go.kr API
- 마스터키 1개로 *활용신청 완료된 API* 모두 호출 가능
- URL 파라미터 이름은 `serviceKey`
- KAU 데이터는 *영업일 1일 + 오후 1시* 이후 업데이트. 주말/공휴일 영향 큼
- 정확한 엔드포인트는 `apis.data.go.kr/.../getXXXX` 페이지에서 *상세기능* 확인 필수

### 법제처 API
- URL 파라미터 이름은 `OC` (정우 OC: `nacave`)
- 응답은 *XML 형식*
- 별표는 *PDF/HWP 파일링크* 로만 제공 (텍스트로는 안 풀어줌)
- 별표 번호가 *법령 본문 별표* 와 *서식 별표* 에 *독립적으로 매겨져 중복* 발생 → 제목 필터 필요