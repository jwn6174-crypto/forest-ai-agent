markdown# Module B/D — 시장·성장·정책

다목적 산림경영 AI Agent의 데이터·정책 백엔드.
산주의 임야 정보를 입력받아, 시장 가격·법령·임분 성장 데이터를 자동으로 수집·정형화한다.

## 최종 업데이트: 2026-05-12

---

## 📊 진행 상황

### ✅ Module D — 시장·정책 (60%)

| 함수 | 파일 | 출처 | 결과물 | 상태 |
|---|---|---|---|---|
| `fetch_kau_price()` | `src/kau_api.py` | data.go.kr 금융위 | `data/raw/kau_daily/*.csv` | ✅ 완성 |
| `search_law()` + `fetch_law_full()` | `src/legal_api.py` | 법제처 OpenAPI | `data/raw/law_extracts/*.xml`, `*.pdf` | ✅ 완성 |
| `fetch_stem_volume()` | `src/growth_api.py` | data.go.kr 산림과학원 | — | ⚠️ 빈 응답 다수, 학습 메모만 |
| (VWorld PNU → polygon) | — | VWorld 2D API | — | ⏳ 인증 시스템 지연 (내일 재시도) |
| (KOFPI 원목가격) | — | KOFPI 웹 스크래핑 | — | ⏳ Week 2 |
| (별표 3 → 기준벌기령 표) | — | camelot로 PDF 파싱 | — | ⏳ PDF 다운로드만 완료 |

### 🔄 Module B — 성장 예측 (40%)

| 작업 | 파일 | 상태 |
|---|---|---|
| 임분수확표 PDF 다운로드 (3.2MB) | `data/raw/yield_table_2014.pdf` | ✅ 완료 |
| PDF 구조 분석 (271p, 14수종) | `src/yield_explore.py` | ✅ 완료 |
| camelot 한 페이지 추출 검증 (p.14: 31×12) | `src/yield_parse.py` | ✅ 완료 |
| 페이지 매핑 발견 (책 page + 6) | — | ✅ 완료 |
| 2페이지 결합 로직 | `src/yield_parse.py` | 🔄 진행 중 |
| 14개 수종 일괄 추출 | — | ⏳ 결합 로직 후 |
| `growth_predict()` 함수 | — | ⏳ 수확표 정리 후 |

### 🗑️ 임시 / 폐기 예정

| 파일 | 설명 |
|---|---|
| `src/legal_diagnose.py` | XML 구조 파악용 일회성 도구. 추후 삭제 가능 |
| `src/page_debug.py` | PDF 페이지 매핑 검증용 일회성 도구. 추후 삭제 가능 |

---

## 🗺️ 임분수확표 PDF 파싱 — 상세

### 발견 (2026-05-12)

1. **책 페이지 ≠ PDF 페이지**: `PDF page = 책 page + 6`
   - 예: 책에서 "강원지방소나무 page 8" → 실제 PDF 페이지 14
2. **각 수종 표가 2 PDF 페이지로 분할됨**:
   - 첫 페이지: 흉고직경 5–35 cm, 수고 **6–28 m** (12 cols)
   - 둘째 페이지: 흉고직경 5–35 cm, 수고 **30–52 m** (12 cols, 수종마다 다를 수 있음)
3. **camelot 셀 통합 문제**:
   - camelot이 표 외곽만 인식하고 내부 셀 구분선은 못 봄
   - 각 셀에 `\n`으로 구분된 수십~수백 개 값이 뭉쳐 들어옴
   - `parse_volume_table()`에서 후처리로 분리 → 2D DataFrame 재구성

### 정확한 PDF 페이지 매핑 (책 page + 6)

| # | 수종 | 수피포함 (PDF p) | 수피제외 (PDF p) |
|---|---|---|---|
| 1 | 강원지방소나무 | 14–15 | 18–19 |
| 2 | 중부지방소나무 | 22–23 | 26–27 |
| 3 | 해송 | 30–31 | — |
| 4 | 리기다소나무 | 32–33 | 36–37 |
| 5 | 잣나무 | 40–41 | 44–45 |
| 6 | 낙엽송 | 48–49 | 52–53 |
| 7 | 삼나무 | 56–57 | — |
| 8 | 편백 | 58–59 | 62–63 |
| 9 | 상수리나무 | 66–67 | 70–71 |
| 10 | 굴참나무 | 74–75 | 78–79 |
| 11 | 신갈나무 | 82–83 | 86–87 |
| 12 | 자작나무 | 90–91 | 92–93 |
| 13 | 백합나무 | 94–95 | 98–99 |
| 14 | 이태리포플러 | 102–103 | — |

> ⚠️ 위 매핑은 강원지방소나무(p.14-15)에서만 검증됨.  
> 다른 수종은 결합 로직 완성 후 수종별로 재검증 필요.

### 이미 발견된 폐기 사유

- 초기 `yield_table_all.parquet` (7,972행)는 *잘못된 페이지 매핑*으로 생성됨 → 폐기됨
- 일부 페이지에서 *재적 값 31개만 추출* (예상: 372) → 91% 손실 → 폐기됨

---

## 🛠️ 환경 설정

```powershell
# 가상환경 활성화 (PowerShell)
.\.venv\Scripts\Activate.ps1

# 실행 예시
python module_bd/src/kau_api.py            # KAU 시세 → CSV
python module_bd/src/legal_api.py          # 법제처 별표 → PDF
python module_bd/src/yield_explore.py      # PDF 구조 탐색
python module_bd/src/yield_parse.py        # 임분수확표 추출
```

## 🔑 필요한 환경 변수 (`.env`)

| 변수 | 출처 | 형식 |
|---|---|---|
| `DATA_GO_KR_KEY` | data.go.kr 마스터키 | 64자 영숫자 |
| `LAW_OC` | 법제처 OpenAPI ID | 영문 ID (예: `nacave`) |
| `VWORLD_KEY` | VWorld 인증키 | UUID 형식 |
| `GEE_ACCOUNT` | Google Earth Engine 계정 | 이메일 |

## 📁 디렉토리 구조
module_bd/
├── data/
│   ├── raw/       — API에서 받은 원본 (XML, PDF, CSV)
│   ├── interim/   — 정형화된 중간 결과 (parquet)
│   └── processed/ — 모델 입력용 최종 데이터
├── notebooks/     — 탐색·분석용 Jupyter
├── src/           — 재사용 가능한 함수 모듈
├── scrapers/      — Scrapy 프로젝트 (예정)
├── tests/         — 단위 테스트 (예정)
└── figures/       — 발표·논문용 그림

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
- 임시 PDF 파일 정리 시 Windows에서 *PermissionError* 발생 가능 (백신 충돌, 무시 가능)
- **책 페이지 번호 ≠ PDF 페이지 번호** — 항상 `pdfplumber`로 텍스트 직접 확인 권장

### 환경 운영
- VS Code에서 New File 만들 때 *대상 폴더를 먼저 클릭*해서 선택. 아니면 엉뚱한 위치에 생성됨
- PowerShell 첫 venv 활성화 시 `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` 필요
- `.env`를 *절대 채팅·스크린샷·commit에 노출 금지*. 노출 시 즉시 재발급
- `git rm --cached <file>`은 *디스크는 안 지우고 staging에서만 제외* — 데이터 파일 제외할 때 유용