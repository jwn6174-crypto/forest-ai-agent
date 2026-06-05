# 5 전문가 세션 — Deliberation 결과 + 종합 권고

> 사용자(희도) 핵심 선호: "여러 전문가 세션을 구축해서 계속해서 토론하고 완벽하게 제대로 된 방향".
> 이 문서는 5명 specialist agent 가 각자 시각에서 Module C 의 핵심 결정 25개 질문에 답한 결과 종합.

**세션 일자**: 2026-05-19 (Day 5)
**페르소나**: 산림학자 / 산림경제학자 / 산림정책학자 / 산림경영자(실무) / AI·ML 전문가
**대기 세션**: 위성/원격탐사 학자, 사유림 수요자, 산림경제·정책 통합자 (W3 진행)

---

## 0. 핵심 메시지 5개 (한 화면 종합)

| 페르소나 | 핵심 메시지 1줄 |
|---|---|
| 산림학자 | 옵션 B (Weibull) + SI 민감도 ±2 + 기후 multiplier 를 MC 에 결합 |
| 경제학자 | Hartman LEV 에 **Lognormal 가격** + HWP 30년 decay + KAU breakeven 명시, 산주 UI는 **점추정**·정책 UI는 분포로 분리 |
| 정책학자 | 정책 모순 (영급 불균형 vs 99% 벌기연장) 을 숨기지 말되, 비판 아닌 **보조도구** framing |
| 경영자 | 5 시나리오에 **간벌(thinning)** 추가, next_actions 에 **전화번호·URL·서류명** 박기 |
| AI 엔지니어 | **LHS · Strategy 패턴 · Pydantic 합의** 3개로 통합·재현성·불확실성 동시 해결 |

---

## 1. 산림학자 답변 요약 (5문)

| Q | 권고 | 영향 |
|---|---|---|
| D14 등급분포 | **Weibull-2P fit** (Bailey & Dell 1973, 강진택 2016) | 영세림의 직경 변이 보존, 1·2등급 단가 3-5배 차이 → LEV 결정적 |
| 60+년 외삽 | Chapman-Richards 점근선 30-50% + IPCC 2019 노령림 NEP anchor | 탄소순환림 시나리오에 ±40% 민감도 |
| 보은 SI=14 | SI **15-16** 권장, 산림입지정보시스템 FLIS 조회 + ±2 민감도 | demo 3 polygon 의 SI 재검토 |
| S5 임산물 | **S5a 표고 (carbon 중립~+15%)** vs **S5b 송이 (carbon -15~-25%)** 분리 | 시나리오 5 → 6개로 확장 |
| 기후 미보정 | Plan B: SSP2-4.5/5-8.5 climate_multiplier 를 MC 추가 변수 (Normal μ=1.0, σ=0.15) | LEV 정직성 + 정책 설득력 동시 |

### 주요 인용
- Bailey & Dell (1973) — Weibull DBH 분포
- 강진택 (2016) 국립산림과학원 — 강원소나무 직경분포식
- IPCC 2019 Refinement Tier 2 — 노령림 NEP
- 임종환 (2020) 국립산림과학원 — SSP 시나리오 한국 수종 영향

---

## 2. 산림경제학자 답변 요약 (5문)

| Q | 권고 | 영향 |
|---|---|---|
| D11 MC 분포 | **목재가 + KOC 는 Lognormal** (Normal 아님 — 음수 방지). 산주 사적 할인율 r=0.07 추가 민감도 | 내 schemas_proposed.py 수정 필요 |
| D12 Pareto | **NPV vs 누적 탄소격리량 (Hartman 정통)**. Risk 는 보조 error bar | 2축 plot 1개로 단순화 |
| D15 HWP decay | `L_C(T) = Σ HWP_i · (1 − exp(−ln2·t/h_i))`, h=30년 단일값 + ±10년 민감도 | LEV 식의 Hartman 항 정식화 |
| WTA-KAU breakeven | **margin = 161원 (0.9%)** = thin market 구조적 임계. 시나리오 4 (연장KOC) 에 결정적. KAU 5% 하락 시 LEV 음수 전환 가능 — **Module C 에 KAU breakeven point 명시 필수** |
| 분포 시각화 | **이중 표현**: 산주는 "중앙값 + 최악 10% 시 -X원" 점추정, 정책담당관은 q05-q95 분포 | DraftPlanCard 의 산주 표시와 정책 부록 분리 |

### 주요 인용
- Brazee & Mendelsohn (1988), Insley (2002) — Lognormal 가격
- Reed (1984) — 확률론적 회전기
- 박일희 (2020) — 한국 산주 시간선호율 4-6%
- IPCC 2019 — HWP 한국 default 35/25/2년 half-life
- Hanley & Spash — thin market
- Kahneman — 행동경제학 손실회피

---

## 3. 산림정책학자 답변 요약 (5문)

| Q | 권고 | 영향 |
|---|---|---|
| D17 진안 case | 4 조건 OK + 추가: (a) **사업개시 2018+** (방법론 v2.0), (b) **모니터링보고서 1+ 제출** (실측 검증), (c) **임령 30-50년** (보은 영급 분포) | W6 검증 figure 의 학술 valid |
| D16 8 사업유형 | **룰베이스 80% + RAG 20% 하이브리드**. 신규조림/벌기령연장/수종갱신 3개는 별표3 임계값으로 판정 가능. 산지전용억제/목제품/재조림-신규조림 구분은 RAG 필수 | 정우 281 청크 활용 + 내 룰베이스 작성 |
| 노령림 정책 갈등 | **벌기령 연장 시나리오 vs 벌채-재조림 회전 시나리오 나란히 비교** → "현 제도는 단기 흡수량 보상, 장기 영급 균형 미보상" 결론. **이게 학부생 작품의 차별화 지점** | DraftPlanCard 의 reasons 필드에 정책 모순 1줄 명시 |
| 공모전 이후 정책 함의 | 타깃 = 산림청 산림탄소정책과 + 임업진흥원 KOC센터 + 지역 산림조합. Framing = **"영세 사유림주 의사결정 보조도구 — KOC 진입장벽 완화 시범"** | W7 발표 슬라이드 closing |
| 위험: 비판조 어조 | **"기존 제도의 우수성 전제 + 사용자 접근성만 보완"** 명시 — 비판 아닌 협력 제안 | 발표 톤 매니저 |

---

## 4. 산림경영자(실무) 답변 요약 (5문) ⭐ 현장 시각

| Q | 권고 | 임팩트 |
|---|---|---|
| 5 시나리오 추가 | **간벌 (thinning) + 10년** 시나리오 추가 (영세 사유림 7할이 간벌 보조사업 ha당 200-300만원 국고지원). 즉시·5년·10년 중 1개 교체 | 시나리오 5 → 6개 확장, **D18 신규 결정** |
| 임산물 200만원 검증 | 보은 표고 노지재배 **300-800만원/ha** (참나무 1,000본, 4년차), 산양삼 50-150만원/ha (7년차), 산나물 30-80만원. **200만원 = 보수적, OK**. 출처: 산림청 「임산물 생산조사」, 충북농업기술원 임업기술센터 보은지소, 산림조합중앙회 임산물 유통정보 (KOSIS 아님) | **D13 NTFP 데이터 출처 정정** — KOSIS 폐기 |
| 운반 거리 | 보은 사유림 평균 **0.8-2.5km** (임도밀도 3.8m/ha). 12km 는 비현실 → **demo 30년 polygon 6km 로 낮추기**. 운반비: 보은→대전 **18,000-22,000원/m³**, 보은→청주 14,000-17,000원 | **D19 demo polygon 정정**, 정우 KOFPI 전국 평균보다 지역 단가 가능 |
| next_actions 구체화 | "산림조합 컨설팅" → **"보은군산림조합 산림경영지도원 ☎043-543-XXXX 임야도·등기부 지참 방문"**. "임지 도로 확인" → **"산림청 FGIS 임반·소반 조회"**. KOC → **"산림탄소센터 koreaforestcarbon.org 신규사업 → 사업계획서 다운로드 → 산림조합 위탁 (수수료 10%)"** | **D20 next_actions 구체화** |
| demo polygon 전형성 | 보은 사유림 산주 7할 = **2-4ha, 30-40년생 리기다·낙엽송 혼효림, 임도 1km 내**. 50년 1.5km OK, 30년 12km 외곽 케이스. **"보은 35년생 3ha 리기다·임도 0.8km" 모달 polygon 추가** | demo 3개 → 4개 확장 |

---

## 5. AI/ML 엔지니어 답변 요약 (5문) ⭐ 통합 시각

| Q | 권고 | 임팩트 |
|---|---|---|
| MC 수렴 | **LHS (Latin Hypercube Sampling)** — 6차원에서 동일 std 를 ~300 iter 로 달성. + `n_eff` 진단 게이트 (batched std/mean < 0.05) | scipy.stats.qmc 활용, 정우와 합의 |
| Pareto 시각화 | **3-5개 대표점 카드** ("안정형/균형형/수익형") + Plotly (Streamlit `st.plotly_chart`). Full front 는 expert mode 토글 | DraftPlanCard 에 3 대표 카드 patterns |
| 불확실성 전달 | q05-q95 폭 > median 50% 시 점추정 숨기고 **구간 + uncertainty_tier ∈ {high/med/low}**. high 일 때 "다음 step 1개 제시" ("LiDAR 측정 시 폭 절반 감소 예상") | LLM prompt 통합, LEVResult 에 uncertainty_tier 추가 |
| api_server.py 통합 | **`POST /compute_lev` endpoint 등록**. `BackgroundTasks` 또는 job_id 폴링 (1000 iter × 5 scenario > 2초 시 HTTP timeout 위험) | 정우 api_server.py 에 PR — D21 |
| Strategy 패턴 fault tolerance | `GradeDistributionStrategy` ABC, `HeuristicGD` + `WeibullGD` 둘 다 구현. CI 에 regression test (heuristic baseline NPV 저장, swap 시 ±20% 넘으면 빨간불, **양쪽 figure 모두 보존** — 발표 시 "Heuristic vs Weibull" 비교 plot 으로 강점 변환) | 정우 estimate_grade_dist 와 내 Weibull fit 둘 다 살림 |

---

## 6. 결정 갱신 매트릭스 — D11 ~ D21

전문가 답변을 반영하여 D11-D17 갱신 + D18-D21 신규.

| ID | 결정 | 이전 (Day 5 초안) | 갱신 (전문가 deliberation 후) |
|---|---|---|---|
| D11 | MC 분포 | 목재가/KOC Normal | **Lognormal**, 할인율 + r=0.07 보조 |
| D12 | Pareto 2축 | NPV-탄소 + NPV-Risk | **NPV-누적탄소격리 단일** (Hartman 정통), Risk 는 error bar |
| D13 | NTFP 데이터 | KOSIS API | **산림청 임산물생산조사 + 충북농업기술원 임업기술센터 + 산림조합 유통정보** (KOSIS 폐기) |
| D14 | 등급분포 | DBH 휴리스틱 → Weibull | **정우 `estimate_grade_dist` 즉시 활용 + Weibull-2P (Bailey-Dell, 강진택 2016) swap** Strategy 패턴 |
| D15 | HWP decay | (미정) | **h=30년 단일 + ±10년 민감도**, `L_C(T) = Σ HWP·(1-exp(-ln2·t/h))` |
| D16 | 8 사업유형 매칭 | RAG 우선 | **룰베이스 80% + 정우 RAG 20% 하이브리드**. 신규조림/벌기연장/수종갱신 룰베이스. 산지전용/목제품/재조림-신규구분 RAG |
| D17 | 진안 case | 사업유형+지역+면적+공개 | + **(a) 사업개시 2018+, (b) 모니터링 1+, (c) 임령 30-50년** |
| **D18** | **간벌(thinning) 시나리오** | (신규) | **시나리오 5 → 6 확장**: 즉시/5년/10년/연장KOC/임산물/**간벌+10년**. 영세 사유림 7할이 실제 선택 |
| **D19** | demo polygon 정정 + 추가 | (신규) | 보은 30년 dist 12→6km. **신규 polygon: 보은 35년 3ha 리기다·임도 0.8km** (모달 케이스). 총 4 demo |
| **D20** | next_actions 구체화 | (신규) | 전화번호/URL/서류명 박기. **"보은군산림조합 ☎043-543-XXXX", FGIS, koreaforestcarbon.org** |
| **D21** | api_server.py 통합 | (신규) | 정우 api_server.py 에 **`POST /compute_lev` endpoint** PR. ComputeLEVRequest Pydantic. BackgroundTasks. |

---

## 7. 코드·구조 변화 종합

### 7.1 shared/schemas.py 변경 (D9 → D9.1 갱신 PR)

```python
class LEVResult(BaseModel):
    # ... 기존 필드 ...

    # AI 엔지니어 권고: 불확실성 tier
    uncertainty_tier: Literal["high", "med", "low"] = "med"
    uncertainty_note: Optional[str] = None  # "LiDAR 측정 시 폭 절반" 등 다음 step

    # 경제학자 권고: KAU breakeven
    kau_breakeven: Optional[float] = None  # 이 시나리오의 KAU 임계가 (원/tCO₂)
    kau_breakeven_note: Optional[str] = None  # "KAU 15,550 → 16,300 이하 시 LEV 음수"


# 산림학자 권고: SSP 기후 multiplier
class ClimateSensitivity(BaseModel):
    scenario: Literal["baseline", "SSP126", "SSP245", "SSP585"]
    growth_multiplier: float  # Normal μ=1.0, σ=0.15
    species_specific: Dict[str, float]  # 강원소나무 +5~-10%, 낙엽송 -15~-25%
```

### 7.2 module_c 새 파일 (전문가 권고 반영)

| 파일 | 책임 | 출처 |
|---|---|---|
| `src/grade_distribution.py` | **정우 estimate_grade_dist import + Weibull-2P swap (Strategy 패턴)** | 산림학자 D14 + AI D14 |
| `src/hwp_decay.py` | **HWP 30년 half-life, L_C(T) 함수** | 경제학자 D15 |
| `src/climate_multiplier.py` | **SSP 시나리오 growth multiplier** | 산림학자 Plan B |
| `src/thinning_scenario.py` | **간벌(thinning) 시나리오 분리 — 잔존목 +10-15% growth** | 경영자 D18 |
| `src/lhs_sampling.py` | **Latin Hypercube Sampling (scipy.stats.qmc)** | AI D11 |
| `src/uncertainty_tier.py` | **q05-q95 폭에 따른 tier 자동 판정 + LLM prompt fragment** | AI D14 |
| `src/offset_eligibility.py` | **8 사업유형 룰베이스 + 정우 RAG hybrid** | 정책학자 D16 |

### 7.3 demo polygon 4개 (D19 갱신)

```python
DEMO_PARCELS = {
    "boeun_pine_30y_1.5ha_outlying": {  # 외곽 케이스
        "species": "강원지방소나무", "site_index": 15,  # ←15 (산림학자 권고)
        "age": 30, "area_ha": 1.5,
        "distance_to_road_km": 6.0,  # ←12→6 (경영자 권고)
    },
    "boeun_pine_50y_2ha": {  # 벌기령 도달
        "species": "강원지방소나무", "site_index": 15,
        "age": 50, "area_ha": 2.0, "distance_to_road_km": 1.5,
    },
    "boeun_rigida_35y_3ha_modal": {  # 신규 모달 케이스 ⭐
        "species": "리기다소나무", "site_index": 10,
        "age": 35, "area_ha": 3.0, "distance_to_road_km": 0.8,
    },
    "jinan_larch_25y_5ha": {  # 지역 확장
        "species": "낙엽송", "site_index": 17,  # ←16~18
        "age": 25, "area_ha": 5.0, "distance_to_road_km": 2.0,
    },
}
```

### 7.4 시나리오 6개 (D18 확장)

```python
VALID_SCENARIOS = ["즉시", "5년", "10년", "연장KOC", "임산물", "간벌+10년"]

def scenario_T(scenario, species, age_now, ownership="사유림"):
    # ... 기존 ...
    if scenario == "간벌+10년":
        # 30-40% 본수 제거 → 잔존목 10년 더 키움 (간벌 보조 200-300만/ha 수익)
        return age_now + 10
```

### 7.5 산주 UI vs 정책 UI 이중 표현 (경제학자 권고)

```python
class DraftPlanCard(BaseModel):
    # 산주용 (점추정)
    recommended_scenario: str
    npv_median_단순표시: int  # "약 1,400만원" 1개 숫자
    npv_worst_case_10pct: int  # "최악의 10% 시 -300만원"
    next_actions_구체: List[str]  # 전화번호·URL·서류명

    # 정책 부록용 (분포)
    full_distribution: Optional[Dict[str, Any]] = None  # fan chart, q05-q95, pareto

    # KAU breakeven (경제학자 핵심)
    kau_breakeven_warning: Optional[str] = None  # "KAU 5% 하락 시 LEV 음수"
```

---

## 8. 학술 기여 매핑 (5 전문가 → 논문 섹션)

| 논문 섹션 | 어떤 전문가 기여 |
|---|---|
| §1 Introduction | 정책학자: 영급 불균형 vs 99% 벌기연장 정책 모순 |
| §2 Background | 경제학자: Faustmann-Hartman 한국 변형의 학술 좌표, Lognormal 가격 |
| §3 Data | 경영자: KOSIS 미제공 → 산림청·충북농기원·산림조합 출처 |
| §4 Methods | 산림학자: Weibull-2P + SSP multiplier + 송이/표고 분리 |
| §5 Results | AI: LHS + Strategy + 불확실성 tier 시각화 |
| §6 Discussion | 정책학자: 비판 아닌 보조도구 framing, 산림청·임업진흥원 협력 제안 |
| §7 Limitations | 산림학자: SI=14→15-16 민감도, 60+년 외삽, 기후 미보정 |

---

## 9. 다음 deliberation 라운드 (W3 진행)

| 페르소나 | 핵심 질문 |
|---|---|
| **위성/원격탐사 학자** | 민석 module_a 미시작 → NFI direct lookup 의 위성 모델 비교 한계? 사유림 영세 영역에서 위성 vs NFI 정확도? |
| **사유림 수요자** | DraftPlanCard 의 UX — 영세 산주가 어떤 데이터를 어떤 순서로 보고 싶나? recommend 알고리즘 selection 기준 (위험회피/균형/수익극대화) 의 산주 인지 모델? |
| **산림경제·정책 통합자** | 5 전문가 답변 종합 + 학술 기여 priority ranking + 공모전 발표 5분 elevator pitch |

W3 (5/22-5/28) 에 3 추가 세션 진행 → `08_expert_sessions_round2.md`.

---

## 10. 즉시 실행 (Day 6-7)

전문가 권고 반영하여 다음 우선 실행:

1. **`shared/schemas_proposed.py` 갱신** — uncertainty_tier, kau_breakeven 필드 추가
2. **`module_c/src/scenarios.py` 갱신** — "간벌+10년" 시나리오 추가 (총 6개)
3. **`module_c/src/stand_state_mock.py`** — demo 4개 (보은 30/35/50, 진안 25), SI 15-16 으로 정정
4. **`module_c/DECISIONS.md`** — D11-D21 ADR 정식 작성
5. **`08_api_keys_setup.md`** — data.go.kr, VWorld, KOSIS 본인 키 발급
6. **`09_module_e_handoff.md`** — 정우 api_server.py 의 `compute_scenarios` endpoint PR 설계

---

## 변경 이력
- 2026-05-19 Day 5 — 5 specialist agent 답변 종합, D11-D21 결정 갱신
