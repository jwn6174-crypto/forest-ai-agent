# Timeline — D5 → W7 (2026-05-19 → 2026-06-26)

> 정우 Day 4 마감 = 우리 Day 4 (실제 캘린더 2026-05-15).
> 내가 시작하는 Day 5 = 2026-05-19. 발표 2026-06-26 = D-38.

**작성일**: 2026-05-19

---

## 주차별 매트릭스

| 주차 | 날짜 | 정우 (B/D) | 민석 (A) | 희도(나) (C+Lead) | 수범 (E) |
|---|---|---|---|---|---|
| W2-rem | 5/19-5/21 | 산악기상 6관측소 | 0 commit | 워크스페이스 + LEVResult schema PR | RAG embedding 준비 |
| W3 | 5/22-5/28 | 임가경제·임산물 | 0 → 시작? | compute_lev v1 결정론 + tests | mock backend e2e |
| W4 | 5/29-6/4 | 등급분포 Weibull (A 협업) | (Strategy B로 우회) | 5 시나리오 + Monte Carlo + Pareto | 5 tool function 흐름 |
| W5 | 6/5-6/11 | 데이터 freeze | mock 흡수 | stand_state_mock + draft_plan + 보은 real e2e | UI 폴리시 |
| W6 | 6/12-6/18 | 시연 데이터 | (fallback) | 진안 case + 검증 figure + 논문 초안 | 데모 영상 1차 |
| W7 | 6/19-6/26 | 발표 자료 | (fallback) | 발표 슬라이드 + 논문 final + 리허설 | 라이브 시연 안정성 |

---

## Day 5 (오늘, 2026-05-19) — 워크스페이스 셋업

### 완료
- [x] 기반채팅 5 HTML + claude_chat.md 전체 파악
- [x] 정우 repo (forest-ai-agent) 구조·README·module_bd/DECISIONS 완전 파악
- [x] 정우 shared/schemas.py 5개 모델 시그니처 확인
- [x] 정우 cost_function.py / growth_predict.py / legal_rotation.py / market_snapshot.py 헤더 확인
- [x] E:\forest_ai 폴더 트리 생성
- [x] README.md / STATUS.md 작성
- [x] _workspace/analysis/01_manual_corrections.md (11 정정)
- [x] _workspace/analysis/02_minseok_handle.md (3단 fallback)
- [x] _workspace/analysis/03_timeline.md (이 문서)

### Day 5 잔여
- [ ] module_c/README.md (정우 README 모방)
- [ ] module_c/DECISIONS.md D9 초고 — LEVResult schema 추가 결정
- [ ] shared/schemas_proposed.py — LEVResult + ComputeLEVRequest + DraftPlanCard

---

## Day 6-7 (5/20-5/21) — 정우에게 PR 보내기

### 작업
1. `shared/schemas_proposed.py` 검증 (자가 테스트 5개)
2. 정우 repo fork → branch `feat/lev-result-schema` 생성
3. `shared/schemas.py` 끝에 LEVResult/ComputeLEVRequest/DraftPlanCard append
4. `shared/test_schemas.py` 신규 작성 (5 검증 + 5 회귀 테스트)
5. PR 본문: "옵션 P2 패턴 — 가이드 §4.1 호환 100% + 우리 확장 Optional"
6. 정우 review approve 대기 → main merge 후 module_c/DECISIONS.md D9 confirm

### 부수 작업
- module_a 폴더 (`.gitkeep + README.md` 만) PR — fallback chain 의 ImportError 깔끔화
- module_c 폴더 초기 commit (README + DECISIONS + 빈 src/data/tests)

---

## W3 (5/22-5/28) — compute_lev v1 결정론

### 산출물
- `module_c/src/scenarios.py` — 5 시나리오 T 계산 + feasibility
- `module_c/src/compute_lev.py` — 결정론 (Monte Carlo 없음) 진입점
- `module_c/src/stand_state_mock.py` — Strategy A demo polygon 3개
- `module_c/tests/test_scenarios.py` — 10 테스트
- `module_c/tests/test_compute_lev.py` — 10 테스트 (단일 시나리오)
- `notebooks/01_lev_derivation.ipynb` — 손계산 검증

### 마일스톤 — W3 끝
- [ ] `compute_lev(stand=DEMO_PARCELS["boeun_pine_50y_2ha"], scenarios=["즉시","10년"])` 동작
- [ ] tests 20 green
- [ ] 정우의 7 함수 모두 호출 성공

---

## W4 (5/29-6/4) — Monte Carlo + Pareto

### 산출물
- `module_c/src/monte_carlo.py` — 1000 iteration, 6 분산 source
- `module_c/src/pareto.py` — NPV-탄소 Pareto front + matplotlib
- `module_c/src/recommend.py` — 위험회피/균형/수익극대화
- `module_c/tests/test_monte_carlo.py` — 안정성 테스트 (반복 5회, std < 5%)
- `notebooks/02_mc_stability.ipynb` — MC 수렴 시각화

### 6 분산 source
1. 위성 AGB — Triangular(q05, mid, q95) → 정우 module_a 없으면 mock ±20%
2. 등급별 목재가 — Normal(price, 10%·price), KOFPI 시계열 표준편차
3. KOC 가격 — Normal(KAU×0.7, 15%)
4. 임산물 연수입 — Normal(2M원, 20%)
5. 할인율 — Triangular(0.04, 0.05, 0.06) 박2020 산주 할인율
6. 임분수확표 잔차 — Normal(0, σ_NFI)

### 마일스톤 — W4 끝
- [ ] 5 시나리오 × 1000 iteration < 30초 단일 polygon
- [ ] Pareto plot PNG 자동 출력
- [ ] tests 30 green (정우 패턴 — Day 4 평균 9 tests/function)

---

## W5 (6/5-6/11) — Real e2e + draft_plan

### 산출물
- `module_c/src/draft_plan.py` — 의사결정 카드 dict 생성 + offset_citations
- `module_c/src/stand_state_mock.py` — Strategy B (NFI lookup) 통합
- `module_c/data/raw/nfi_plots/` — NFI 5·6·7차 보은 표본점 다운로드
- 수범 module_e 와 mock 5-tool 흐름 연결

### 마일스톤 — W5 끝 ★★★
- [ ] 보은군 1 polygon (보은 50년 소나무 2ha) end-to-end:
  polygon → stand_state → compute_lev → draft_plan → UI 표시
- [ ] mock 이 아닌 real (NFI lookup) 한 번 동작 확인
- [ ] 수범의 LLM agent 가 `compute_lev` tool call 성공

---

## W6 (6/12-6/18) — 검증 case + 논문 초안

### 산출물
- 진안군 산림탄소상쇄 등록사업 1건 (한국임업진흥원 carbonregistry 공개) 선정
- 모델 추정 흡수량 vs 인증 흡수량 비교 figure
- `_workspace/manuscript/draft_v1.md` — IMRaD 구조 논문 초안
- 발표 슬라이드 v1 (15-20 슬라이드)

### 마일스톤 — W6 끝
- [ ] 진안 case study figure 1개
- [ ] 논문 §1-§5 (Introduction, Background, Methods, Results, Discussion) 초안
- [ ] 슬라이드 v1 팀 4명 review

---

## W7 (6/19-6/26) — 제출 + 발표

### 산출물
- 발표 슬라이드 final
- 논문 final
- 라이브 시연 리허설 3회
- GitHub repo 정리 (README 최종, 모든 모듈 함수 시그니처 일치 확인)
- 백업 시나리오 (오프라인 데모 영상)

### 마일스톤 — 2026-06-26
- 제출
- 발표
- 200만원 상금?

---

## 위험 등록부

| # | 위험 | 확률 | 영향 | 대응 |
|---|---|---|---|---|
| R1 | 민석 끝까지 미시작 | 70% | 중 | Strategy B+A fallback 으로 학술 가치 유지, 논문 Discussion 에 기여로 변환 |
| R2 | 정우 PR review 지연 | 30% | 중 | local 작업 진행, merge 전에는 `from shared.schemas import LEVResult` 부분만 mock |
| R3 | 수범 module_e 늦어짐 | 50% | 중 | W3 mock e2e 마일스톤 강제, W5 까지 안 되면 Streamlit 직접 작성 (1.5일) |
| R4 | NFI 표본점 매칭 안 됨 | 40% | 낮 | Strategy A demo 3개로 시연, NFI 실패는 limitations 명시 |
| R5 | Monte Carlo 수렴 안 됨 | 20% | 중 | iteration 5000+ 시도, antithetic variates, control variates |
| R6 | 진안 검증 case 데이터 부재 | 30% | 낮 | 다른 등록사업 (강원·전북 다수) 로 대체, 학술 가치는 동일 |

---

## 변경 이력
- 2026-05-19 Day 5 — 초기 timeline 작성
