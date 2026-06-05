# Module C 완성 빌드 플랜 — 데이터·API·설계·코드 전부

> "내가 어떤 걸 완벽하게 데이터 구축하고, API 찾고, 어떤 설계로 어떤 코드를 만들어야 하나"
> 라는 질문에 대한 단일 답.

**작성일**: 2026-05-19 (Day 5)
**근거**: 정우 module_bd 인벤토리 + 메뉴얼 11정정 + 민석 fallback 전략 + 5 시나리오 정의

---

## 0. 우선 한 화면 — 무엇을 채워야 LEV 식이 닫히는가

Faustmann-Hartman 식:
```
NPV(T) = Σ_g [p_g · v_g(T)] · e^(-rT)
       + ∫_0^T p_C(t) · ΔC(t) · e^(-rt) dt
       + ∫_0^T π_NTFP(t) · e^(-rt) dt
       − Cost(T) · e^(-rT) − C_regen
LEV  = NPV(T) / (1 − e^(-rT))
```

| 항 | 변수 | 누가 제공? | 상태 |
|---|---|---|---|
| 등급별 가격 | p_g | 정우 D `market_snapshot()` | ✅ |
| T시점 등급별 재적 | v_g(T) = V(T) × dist_g(T) | 정우 B `growth_predict()` × **내 grade_dist 휴리스틱** | 🟡 부분 |
| 탄소가격 | p_C(t) | 정우 D `market_snapshot()["koc_estimate"]` | ✅ |
| 탄소 흡수 | ΔC(t) | 정우 B `growth_predict()["carbon_uptake_rate"]` | ✅ |
| **임산물 수입** | π_NTFP(t) | **내가 KOSIS API 로 가져와야** | ❌ |
| 비용 | Cost(T) | 정우 D `cost_function()` | ✅ |
| 재조림 | C_regen | 정우 D `cost_function(action="planting")` | ✅ |
| 할인율 | r | 정우 D `market_snapshot()["discount_rate"]=0.05` | ✅ |
| 법정 벌기 | T ≥ legal_min | 정우 D `rotation_age()` | ✅ |
| **임지 현재상태** | V0, AGB, age, species | **민석 미시작 → 내 fallback chain** | ❌ |

**결론**: 식의 9개 변수 중 7개는 정우가 제공. 내가 채워야 할 것은 단 **2개**:
1. **임지 현재상태** (StandStateEstimate) — 민석 미시작 우회
2. **임산물 수입** (π_NTFP) — KOSIS API 확보

그 외에 *내가 만들어야 할 코드 로직* 은 LEV 식 자체 계산 + Monte Carlo + Pareto + 의사결정 카드.

---

## 1. 데이터 인벤토리 — 내가 직접 구축할 것

### P0 — Critical (이거 없으면 Module C 학술 valid 안 됨)

#### D1.1 NFI 5·6·7차 보은 표본점 마이크로데이터 ⭐ 핵심
- **용도**: Strategy B fallback (민석 미시작 우회) + W6 진안 검증 case 보조
- **출처**: `data.go.kr/data/15122903/fileData.do` — 임분조사 마이크로데이터
- **방법**: data.go.kr 회원가입 (정우 이미 발급, `.env DATA_GO_KR_KEY` 있음) → file 다운로드
- **저장**: `module_c/data/raw/nfi_plots/nfi_7th_korea.csv` (전국 4,500 표본점)
- **파싱**: `scripts/fetch_nfi.py` 작성 → 보은 시도코드 (충북 43) 클립
- **출력**: `module_c/data/interim/nfi_plots_boeun.parquet`
- **필드**: plot_id, lon, lat, species, age, site_index, volume_per_ha, dbh_mean, height_mean, carbon_per_ha
- **예상 매칭률**: 보은 583 km² / NFI 4×4 km 격자 → ~36 표본점
- **마감**: W4 끝 (5/29 이후 NFI lookup 실작동 위해)

#### D1.2 보은군 행정경계 polygon
- **용도**: NFI 클리핑, polygon 입력 검증, 시연용 지도
- **출처**: `gisdeveloper.co.kr` 무료 도로명주소 DB 기반 SGG SHP
- **저장**: `module_c/data/raw/admin/sgg_boeun.geojson` (단일 polygon)
- **마감**: Day 7

#### D1.3 demo polygon 3개의 사전 계산값
- **용도**: Strategy A (시연용 hand-craft)
- **방법**: 정우 `growth_predict()` 호출해서 volume/dbh/height/carbon 채움
- **저장**: `module_c/data/interim/stand_estimates_mock.parquet` (3 행)
- **마감**: Day 6-7

---

### P1 — Important (학술 valid + 5 시나리오 완성도)

#### D1.4 임산물 소득 데이터 ⭐ 메뉴얼 정정 #10
- **용도**: 시나리오 S5 (임산물 병행) 의 π_NTFP — 정우 미작성
- **출처 A**: `data.go.kr/data/3044575/fileData.do` — 임산물소득조사 (1,109 임가)
- **출처 B**: `data.go.kr/data/15127763` — KOSIS 임가경제조사 OpenAPI
- **출처 C**: 산림청 「임산물 표준소득자료」 PDF (kfri.go.kr)
- **방법**: 출처 A 가장 간단 (file 다운로드, 회원가입만 필요)
- **저장**: `module_c/data/raw/ntfp/forest_byproduct_income_2024.csv`
- **파싱**: 표고/산양삼/산나물/밤/호두 5 카테고리 × ha당 연소득
- **출력**: `module_c/data/interim/ntfp_lookup.json` 
  ```json
  {"표고": {"mean_won_per_ha_yr": 2_400_000, "std": 480_000},
   "산양삼": {"mean": 6_800_000, "std": 1_700_000}, ...}
  ```
- **마감**: W3 (시나리오 S5 코드 작성 전)

#### D1.5 진안군 산림탄소상쇄 등록사업 1건 (검증 case)
- **용도**: W6 모델 추정 흡수량 vs 인증 흡수량 비교 figure
- **출처**: `carbonregistry.forest.go.kr` 등록사업 목록 (589 사업 공개)
- **선정 기준**: 
  - 사업유형 = 벌기령 연장 산림경영 (99% 차지)
  - 사업지 = 전북 진안 또는 충북 보은 인근
  - 인증 흡수량 공개
  - 면적 1-5 ha (우리 시연 polygon 규모)
- **저장**: `module_c/data/raw/registered_offset/{project_id}.json`
- **마감**: W6 (6/12)

---

### P2 — Nice to have

#### D1.6 임상도 1:25,000 SHP (Strategy C fallback)
- 출처: `data.go.kr/data/3045619/fileData.do`
- 면적 큰 SHP (전국 ~700 MB). 보은만 클리핑.
- 마감: W5 또는 skip (Strategy B NFI 만으로 발표 가능)

#### D1.7 HWP carbon decay 룰베이스
- 출처: 국립산림과학원 「목재제품의 탄소저장량 산정」 PDF
- 핵심: 제재목 30년 half-life, 합판 20년, 펄프 2년
- 마감: W4 (Faustmann-Hartman 의 Hartman 항 정확도 ↑)

#### D1.8 산림탄소상쇄 등록 가능성 룰베이스
- 출처: 정우 `carbon_chunks.jsonl` 281 청크 → 8 사업유형별 적용조건 추출
- 또는 산림청 「운영지침」 PDF 직접 파싱
- 마감: W4 (draft_plan 의 offset_citations 향상)

---

## 2. API 인벤토리 — 내가 연결해야 할 것

### A1. VWorld API (P0) — PNU/주소 → polygon

```python
# 사용 예
import requests
url = "http://api.vworld.kr/req/data"
params = {
    "key": os.environ["VWORLD_KEY"],
    "service": "data",
    "version": "2.0",
    "request": "getfeature",
    "data": "LP_PA_CBND_BUBUN",  # 연속지적도
    "attrfilter": f"pnu:=:{pnu}",
    "geometry": "true",
}
```
- **상태**: 정우 `test_vworld.py` 존재 → 키 발급됨 (`VWORLD_KEY` env)
- **무료**, 일일 한도 사실상 없음
- **내가 쓸 곳**: `module_c/src/stand_state_mock.py` 의 `_pnu_to_centroid()` + 시연 polygon 검증
- **마감**: Day 7

### A2. data.go.kr fileData (P0) — NFI 다운로드

- 정우가 이미 `DATA_GO_KR_KEY` 발급. 추가 신청 불필요.
- NFI 마이크로데이터는 OpenAPI 아니라 fileData 형식 → 일회 다운로드 + parquet 변환.
- **마감**: Day 7-W3

### A3. KOSIS OpenAPI (P1) — 임가경제·임산물

```python
# 사용 예
url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
params = {
    "apiKey": ..., "method": "getList",
    "orgId": "143", "tblId": "DT_143F002",  # 임가경제조사
    "format": "json", "objL1": "0",  # 전국
    "prdSe": "Y", "newEstPrdCnt": "5",
}
```
- 정우 이미 `KOSIS_KEY` 발급했을 가능성 (정우 README 에 "DATA_GO_KR_KEY, LAW_OC, VWORLD_KEY 등").
- 없으면 `data.go.kr/data/15127763` 활용신청 (1-2일).
- **마감**: W3 (NTFP 데이터 확보 위해)

### A4. (선택) 한국임업진흥원 산림탄소등록부 스크래핑

- 등록사업 589건 목록 공개되지만 OpenAPI 없음 → HTML 스크래핑.
- 페이지: `carbonregistry.forest.go.kr/offset/projects`
- W6 진안 검증 case 1건만 선정하면 되니 *수동 검색* 으로 충분.
- **마감**: W6

### A5. (정우 활용) module_bd 의 7 함수

이미 사용 가능:
- `growth_predict`, `market_snapshot`, `cost_function`, `rotation_age`, `lookup_volume`, `fetch_kau_price`, `search_law`

---

## 3. 코드 빌드 순서 — Tier 별

### Tier 1: Day 5-7 (5/19-5/21) — 스캐폴드 + Schema PR

| 파일 | 책임 | 상태 |
|---|---|---|
| `module_c/README.md` | 정우 모방 | ✅ |
| `module_c/DECISIONS.md` D9 | LEVResult schema | ✅ 초고 |
| `shared/schemas_proposed.py` | LEVResult + ComputeLEVRequest + DraftPlanCard | ✅ 검증 통과 |
| `module_c/src/scenarios.py` | 5 시나리오 T + feasibility | ✅ |
| `module_c/tests/test_scenarios.py` | 10 tests | ⏳ Day 6 |
| `module_c/tests/test_schemas.py` | 5 tests for LEVResult | ⏳ Day 6 |
| `module_c/src/stand_state_mock.py` Strategy A | demo polygon 3개 + 정우 growth_predict 호출 | ⏳ Day 7 |
| `scripts/fetch_admin_boundary.py` | 보은 polygon 다운로드 | ⏳ Day 7 |

**완료 기준**: scenarios + schema PR 정우 review-ready, demo 3개 polygon 의 volume/AGB/grade dict 가 정우 함수로 채워짐.

---

### Tier 2: W3 (5/22-5/28) — 결정론 compute_lev

| 파일 | 책임 |
|---|---|
| `module_c/src/grade_distribution.py` | DBH 평균 → 등급분포 휴리스틱 (정우 W4 fit 전 임시) |
| `module_c/src/compute_lev.py` v1 결정론 | 5 시나리오 NPV 계산 (MC 없음) |
| `module_c/tests/test_grade_distribution.py` | 6 tests |
| `module_c/tests/test_compute_lev.py` v1 | 10 tests (단일 시나리오) |
| `notebooks/01_lev_derivation.ipynb` | Faustmann-Hartman 손계산 검증 |
| `scripts/fetch_ntfp_kosis.py` | KOSIS 임산물 소득 다운로드 |
| `module_c/data/interim/ntfp_lookup.json` | 5 카테고리 × ha당 소득 |

**완료 기준**: `compute_lev(stand=DEMO_PARCELS["boeun_pine_50y_2ha"], scenarios=["즉시","10년"])` 동작.
NPV 단위 검증 (원/ha, 의미 있는 수치). tests 30 green.

#### 등급분포 휴리스틱 (W3 임시, W4 Weibull 로 swap)

산림청 「원목규격」 (KFS 1-2024) 등급 기준:
| 등급 | 최소 말구지름 |
|---|---|
| 특용재 | ≥48 cm |
| 1등급 | 36-47 cm |
| 2등급 | 24-35 cm |
| 3등급 | 18-23 cm |
| 원주재 | 14-17 cm |
| 원료재 | <14 cm |

DBH 평균 → 말구지름 = DBH × 0.7 (경험 근사) → 등급별 비율 추정.
정규분포 가정: `dist_g = P(말구지름 ∈ 등급 g 구간 | μ=DBH×0.7, σ=DBH×0.15)`.

---

### Tier 3: W4 (5/29-6/4) — Monte Carlo + Pareto + draft_plan

| 파일 | 책임 |
|---|---|
| `module_c/src/monte_carlo.py` | 1000 iter, 6 분산 source |
| `module_c/src/compute_lev.py` v2 MC 통합 | results.npv_q05/q95 채움 |
| `module_c/src/pareto.py` | NPV-탄소 2D scatter + frontier |
| `module_c/src/recommend.py` | 위험회피/균형/수익극대화 Sharpe-like |
| `module_c/src/draft_plan.py` | DraftPlanCard 생성 + offset_citations |
| `module_c/src/offset_eligibility.py` | 8 사업유형 자동 매칭 룰베이스 |
| `module_c/tests/test_monte_carlo.py` | 8 tests (수렴, std<5%) |
| `module_c/tests/test_pareto.py` | 6 tests |
| `module_c/tests/test_draft_plan.py` | 6 tests |
| `notebooks/02_mc_stability.ipynb` | MC 수렴 그래프 |

**완료 기준**: 5 시나리오 × 1000 MC < 30초/polygon. Pareto plot PNG 자동 출력.
정우 W4 Weibull fit 완료 시 grade_distribution swap. tests 50 green.

---

### Tier 4: W5 (6/5-6/11) — Real e2e + 통합

| 파일 | 책임 |
|---|---|
| `scripts/fetch_nfi.py` | NFI 마이크로데이터 다운로드 |
| `scripts/clip_nfi_to_boeun.py` | 보은 36 표본점 클립 |
| `module_c/data/interim/nfi_plots_boeun.parquet` | 36 표본점 정제 |
| `module_c/src/stand_state_mock.py` Strategy B | NFI direct lookup 실작동 |
| `module_c/src/stand_state_mock.py` Strategy C | 임상도 lookup (선택) |
| `module_c/tests/test_stand_state_mock.py` | 8 tests (3 mode × demo+nfi) |
| `notebooks/03_demo_scenarios.ipynb` | 3 polygon 시연 노트북 |

**마일스톤 W5 끝**: 보은 polygon 1개 real (NFI lookup) e2e 동작.
수범 module_e 의 LLM agent 에서 `compute_lev` tool call → DraftPlanCard 반환 → UI 표시.

---

### Tier 5: W6 (6/12-6/18) — 검증 case + 논문 초안

| 파일 | 책임 |
|---|---|
| `_workspace/scripts/find_jinan_case.py` | carbonregistry 스크래핑 |
| `module_c/data/raw/registered_offset/{id}.json` | 진안 등록사업 1건 |
| `module_c/src/validation.py` | 모델 vs 인증 흡수량 비교 |
| `notebooks/04_jinan_validation.ipynb` | 검증 figure 생성 |
| `_workspace/manuscript/draft_v1.md` | IMRaD 논문 초안 §1-§5 |
| `_workspace/slides/v1.pptx` 또는 marp.md | 발표 슬라이드 15-20장 |

---

### Tier 6: W7 (6/19-6/26) — 발표 + 제출

- 슬라이드 final, 논문 final, 리허설 3회
- repo 정리, README 갱신, 모든 함수 시그니처 일치 검증
- 백업 데모 영상

---

## 4. 결정 예약 (D11-D17)

D9, D10 은 이미 초고. 아래 7개 결정은 코드 작성 시점에 ADR 작성.

| ID | 결정 주제 | 옵션 | 예상 선택 | 마감 |
|---|---|---|---|---|
| D11 | MC 6 분산 source 분포 | Normal vs Triangular vs Beta | 변수별 다른 분포 (위 4.1) | W3 |
| D12 | Pareto front 2축 | NPV-탄소 vs NPV-Risk vs 누적격리 | NPV-탄소 + NPV-Risk 동시 | W4 |
| D13 | NTFP π_NTFP 가정 | mock 200만 vs KOSIS 실측 vs 임가경제 분위수 | KOSIS 실측 (W3 데이터 후) | W3 |
| D14 | 등급분포 추정 | 휴리스틱 vs Weibull vs NFI 통계 | 휴리스틱 W3 → Weibull W4 swap | W4 |
| D15 | HWP carbon decay | IPCC default vs 한국 데이터 | 한국 데이터 30년 half-life | W4 |
| D16 | 8 사업유형 적용 룰 | 정우 RAG 검색 vs 룰베이스 추출 | 룰베이스 (정우 RAG 보완) | W4 |
| D17 | 진안 검증 case 선정 | 사업유형 X 사업지 X 면적 기준 | 벌기연장 + 진안/보은 + 1-5ha | W6 |

---

## 5. Day-by-Day (5/19-5/28 즉시 10일)

### Day 5 (오늘, 5/19) ✅ 완료
- [x] 워크스페이스 셋업
- [x] 6 분석 문서 (00-05)
- [x] LEVResult schema 자가검증 통과
- [x] scenarios.py 자가검증 통과

### Day 6 (5/20)
- [ ] `module_c/tests/test_scenarios.py` 10 tests (정우 패턴: 검증 5 + 회귀 5)
- [ ] `module_c/tests/test_schemas.py` 5 tests for LEVResult
- [ ] `scripts/fetch_admin_boundary.py` — 보은 polygon 다운로드
- [ ] 정우 repo fork or collaborator 요청
- [ ] D9 PR 본문 작성

### Day 7 (5/21)
- [ ] `module_c/src/stand_state_mock.py` Strategy A 작성
  - DEMO_PARCELS 3개 dict
  - `_compute_demo_state(species, age, area)` — 정우 growth_predict 호출
  - `get_stand_state(pnu, geom_wkt, mode="auto")` 4단 try
- [ ] `module_c/tests/test_stand_state_mock.py` 6 tests
- [ ] D9 PR 보내기 (`shared/schemas.py` append + `shared/test_schemas.py`)
- [ ] module_a 빈 폴더 PR (`.gitkeep` + Manual 02 기반 README 초안)

### Day 8 (5/22) — W3 시작
- [ ] `module_c/src/grade_distribution.py` 휴리스틱 (D14 임시)
- [ ] `module_c/src/compute_lev.py` v1 결정론 — `_simulate_npv_once(...)` 만, MC 없음
- [ ] `module_c/tests/test_compute_lev.py` 단일 시나리오 5 tests

### Day 9 (5/23)
- [ ] `compute_lev.py` 5 시나리오 통합 + dict 반환
- [ ] `module_c/tests/test_compute_lev.py` 추가 5 tests
- [ ] notebooks/01_lev_derivation.ipynb — 손계산 검증

### Day 10 (5/24)
- [ ] `scripts/fetch_ntfp_kosis.py` — KOSIS 임산물 소득 다운로드
- [ ] `module_c/data/interim/ntfp_lookup.json` 5 카테고리
- [ ] D13 결정문 ADR

### Day 11-14 (5/25-5/28)
- [ ] `module_c/src/monte_carlo.py` 1000 iter
- [ ] `compute_lev.py` MC 통합 → npv_q05/q95
- [ ] `module_c/tests/test_monte_carlo.py` 8 tests
- [ ] D11 결정문 ADR

**W3 끝 마일스톤**: 5 시나리오 × MC 1000 동작, tests 30 green.

---

## 6. 위험 + 대응

| 위험 | 확률 | 대응 |
|---|---|---|
| 정우 D9 PR review 지연 | 30% | local 작업 진행, `from shared.schemas_proposed import` 임시 |
| KOSIS API 신청 시간 | 50% | data.go.kr 3044575 fileData 또는 정우 키 재활용 |
| NFI 마이크로데이터 큼 (700MB+) | 70% | 충북만 클립 (~50MB), `.gitignore` raw |
| 등급분포 Weibull fit 정우 W4 못 끝냄 | 50% | 휴리스틱 그대로 발표, limitations 명시 |
| Monte Carlo std > 5% | 30% | iter 5000 증가 또는 antithetic variates |
| 진안 검증 case 데이터 부족 | 40% | 강원/전북 다른 등록사업 1건으로 대체 |

---

## 7. 우선 결정 필요 (사용자에게)

지금 즉시 답변 필요:

1. **정우 repo 협업 방식** — (a) fork + PR 만? (b) collaborator 추가? 
   - 권장: collaborator 추가 (4명 팀이라 PR review 가벼움)

2. **정우 환경 변수 공유** — `.env` 의 `DATA_GO_KR_KEY`, `VWORLD_KEY`, `LAW_OC` 받기?
   - 받아야 NFI/VWorld API 호출 가능

3. **module_a 빈 폴더 PR 보낼지** — 민석 unblock 위한 자리만 만드는 것
   - 권장: 보내기 (fallback chain ImportError 가 깔끔, 민석 시작 시 자연스러운 시드)

4. **수범 module_e 진척 확인** — 정우 README 에 "진행 중" 만 적힘. mock backend 받을 준비됐는지?
   - 권장: 수범에게 W3 끝 (5/28) 까지 5 tool function 시그니처 합의

---

## 변경 이력
- 2026-05-19 Day 5 — 데이터 8개 + API 5개 + 코드 6 tier + 결정 7개 종합 빌드 플랜
