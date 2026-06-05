# Module C — Faustmann–Hartman 경제성 분석

Module C 는 다목적 산림경영 AI Agent(충북 보은 파일럿)의 의사결정 코어다.
민석의 Module A 가 위성으로 추정한 임분 상태와 정우의 Module B·D 가 제공하는
성장 곡선·시장 가격을 받아, 산주가 던지는 단 하나의 질문에 답한다 — **"지금
이 숲을 어떻게 하는 것이 가장 이로운가."** 그 답을 1849년 Faustmann 의 임지
기대가치(LEV)와 1976년 Hartman 의 비목재 가치 이론을 한국 데이터로 풀어
계산하고, 여섯 가지 경영 시나리오의 순현재가치(NPV) 분포로 제시한다.

| 항목 | 내용 |
|---|---|
| 담당 | 희도 (zxsa0716@kookmin.ac.kr) |
| 버전 | v1.1.0-integrated — Module A·B·C·D 통합 완료 |
| 의사결정 기록 | ADR 27개 (D101–D127) |
| 검증 | 통합 e2e 포함 전체 테스트 통과, ruff clean |
| 과제 | 한국연구재단 일반공동연구 (CLIM Lab, 임철희 교수) |
| 발표 | 2026-06-26 |

---

## 학술 발견 다섯 건

Module C 는 네 모듈을 통합하는 과정에서 다섯 건의 학술적 발견을 정리했다.
그중 세 건(D114·D122·D126)은 하나의 일관된 가설로 수렴한다 — **한국 산림 탄소·
바이오매스 추정에는 방법마다 체계적 편향이 있다.**

| ID | 발견 | 의미 |
|---|---|---|
| **D114** | 산림탄소상쇄 인증실적(320 tCO₂/ha/30yr)이 자연 성장 모델(220)보다 **+45%** 높다 | 인증제도 baseline 가정 검토 필요성을 처음으로 정량화 |
| **D115** | KAU 배출권이 16개월간 **+79%** 올라(8,670→15,550원), 산주 의향가격(WTA 17,039원)에 **8.7% 차이로 근접 — 돌파 임박** | 자발적 탄소상쇄 참여가 경제적으로 합리적이 되는 임계 도달 직전 — 발표 핵심 |
| **D122** | 국가 수확표 등급분포가 NFI 실측보다 상위 등급을 **+123%** 과대평가 | 영세 사유림 NPV 가 가정보다 낮을 수 있음 |
| **D124** | 정우 기후 보정과 임종환 시뮬레이션의 생장 부호가 **정반대** | 모델 간 불일치를 정직하게 노출 |
| **D126** | 위성 GEDI 가 고밀도 침엽수림을 과소추정(NFI 외부검증 **R²=-0.187**) | 인증=과대, 수확표=과대, 위성=과소 → 3축 교차검증 근거 |

세 추정 방법의 편향이 서로 반대 방향이라는 점이 핵심이다. 보은 산외면 오대리
(25.6 ha, 인증 8,197 tCO₂)에서 인증을 상한으로, 자연 성장 모델을 하한으로,
위성 추정을 제3의 독립 측정으로 배치하면, +45% 차이의 원인이 인증의 회계
가정인지 실제 경영 효과인지를 판별할 수 있다.

---

## 한 줄 요약

```python
from module_c.src.compute_lev import compute_lev_with_plan
from module_c.src.demo_parcels import get_demo_parcel

stand = get_demo_parcel("boeun_pine_50y_2ha")
package = compute_lev_with_plan(stand, user_preference="균형")
# → {results, pareto, three_representative, draft_plan}
#    6 시나리오 × Monte Carlo 300 LHS samples × Pareto + DraftPlanCard
```

---

## 통합 파이프라인 — 위성에서 산주 화면까지

사용자가 필지번호(PNU)를 입력하면, 분석 결과는 네 모듈을 거쳐 ui 화면에 닿는다.
Module C 는 그 중심에서 위성 추정과 화면 사이를 잇되, 두 모듈을 직접 import 하지
않고 얇은 어댑터 두 개로만 결합한다(느슨한 결합).

```
사용자 PNU 입력  ──▶  api_server.py  POST /analyze
                          │
   Module A predict_stand()  ──▶  forest_state (위성 임분 상태)
   Module B growth_predict()      ──▶  성장 곡선 + 등급분포(Weibull) + 기후 보정
   Module D market_snapshot()     ──▶  KOFPI 목재가 · KAU 배출권가
                          │
   stand_adapter.from_forest_state()       ← ① 입력 변환 (15키 stand dict)
                          │
   compute_lev_with_plan()                 ← ② Module C 경제성 분석
       6 시나리오 × Monte Carlo(LHS) → NPV · Pareto · 추천 카드
                          │
   ui_adapter.to_ui_scenarios()            ← ③ 출력 변환 (ui Scenario[])
                          │
   ui  ScenarioTable · NPVChart · ParetoChart · ChatPanel
```

이 흐름 전체가 `test_integration_e2e.py` 로 검증된다. 통합 코드는
[`docs/integration/api_server_integration.md`](docs/integration/api_server_integration.md)
에 정확한 교체 코드로 정리해 두었다.

**어댑터 두 개**

| 어댑터 | 역할 |
|---|---|
| `src/stand_adapter.py` | Module A 위성 추정(StandStateEstimate)을 Module C 입력 dict 로 변환. 수종명을 정우 정식명으로 역매핑하고, 경제성에 필요한 입지 변수 7개를 보완한다. **위성의 실측 분산(volume_q05/q95)이 Monte Carlo 의 임의 ±20% 가정을 대체** — 불확실성이 "가정"에서 "측정"으로 격상된다. |
| `src/ui_adapter.py` | Module C 결과를 수범의 ui `Scenario[]` 로 변환. 한국어 식별자를 영어로, 원을 만원으로 바꾸고, Monte Carlo 분포에서 파산확률을, 사업유형 매칭에서 KOC 적격을 계산한다. |

---

## 디렉토리 구조

```
module_c/
├── README.md / DECISIONS.md / BUILDPLAN.md
├── src/                    (19 파일)
│   ├── scenarios.py            # 6 시나리오 + feasibility
│   ├── grade_distribution.py   # Strategy 패턴 (Heuristic + Weibull)
│   ├── hwp_decay.py            # IPCC 2019 35/25/2년 (D107)
│   ├── climate_multiplier.py   # SSP × 수종 (D103.b)
│   ├── subsidies.py            # 산림보조사업 (D110)
│   ├── ntfp_income.py          # 2024 임산물 보고서 (D105)
│   ├── uncertainty.py          # tier 자동 판정
│   ├── lhs_sampling.py         # Latin Hypercube
│   ├── lev_core.py             # ⭐ Faustmann-Hartman 본체
│   ├── monte_carlo.py          # 6 분산 source × LHS
│   ├── kau_breakeven.py        # KAU 임계가 (D115 핵심)
│   ├── recommend.py            # 위험회피/균형/수익극대화
│   ├── offset_eligibility.py   # 8 사업유형 룰+RAG hybrid (D108)
│   ├── pareto.py               # NPV-탄소 Pareto (D104)
│   ├── draft_plan.py           # DraftPlanCard 이중 표현
│   ├── demo_parcels.py         # 6 polygon (Sample 2 + Real 4)
│   ├── compute_lev.py          # ⭐ 진입점
│   ├── data_go_kr_api.py       # 산림자원통계 + KAU + VWorld
│   └── validation.py           # D114 모델 vs 인증 비교
├── tests/                  (19 파일 + fixtures, 160 tests)
├── scripts/
│   └── test_keys.py            # 6 API sanity check
├── data/
│   ├── raw/
│   │   ├── hwp/hwp_decay_2019.json
│   │   ├── climate/climate_multipliers_2020.json
│   │   ├── subsidies/forestry_subsidies_2025.json
│   │   ├── ntfp/forest_byproduct_income_2024.json
│   │   ├── offset_eligibility/eligibility_rules_2024.json
│   │   ├── registered_offset/all_projects_2026_05.json   # carbonregistry 658건
│   │   └── kau/kau_timeseries_2025_2026.json             # KAU 16개월
│   └── processed/
│       ├── validation_cases.json
│       ├── d22_plot_data.json
│       └── d23_plot_data.json
└── notebooks/
    ├── 01_lev_derivation.py        # Faustmann 손계산 검증
    ├── 02_validation_d22.py        # 인증 vs 모델 시각화
    └── 03_kau_wta_breakeven.py     # KAU 시계열 + WTA 돌파
```

---

## 정우 module_bd 의존 (7 함수)

```python
from module_bd.src.growth_predict import growth_predict, lookup_volume
from module_bd.src.market_snapshot import market_snapshot
from module_bd.src.cost_function import cost_function
from module_bd.src.legal_rotation import rotation_age
from module_bd.src.kau_api import fetch_kau_price
from shared.schemas import (
    GrowthForecast, MarketSnapshot, CostInput, CostBreakdown, RotationRule,
    LEVResult, ComputeLEVRequest, DraftPlanCard,  # ← module_c 추가 (PR 1)
)
```

---

## 6 시나리오 (D110 간벌+10년 추가)

| 시나리오 | T | 비용 action | 탄소수익 | NTFP | 보조사업 매출 |
|---|---|---|---|---|---|
| 즉시 | age_now | clearcut | 0 | 0 | 갱신 4.5M/ha |
| 5년 | +5 | clearcut | 5년치 (KOC>WTA) | 0 | 갱신 |
| 10년 | +10 | clearcut | 10년치 | 0 | 갱신 |
| 연장KOC | max(legal+10, age+10) | clearcut | 매년 KOC | 0 | - |
| 임산물 (S5a 표고/S5b 송이) | +15 | clearcut | 15년치 | 0.3-8M/ha | 갱신 |
| **간벌+10년** | +10 | **thinning** + 10년 후 잔존목 | 10년치 | 0 | **간벌 2.5M/ha + 갱신** |

---

## 8 전문가 deliberation

### Round 1 (5 페르소나, 5/19)
1. **산림학자** — Weibull-2P + SI ±2 + 송이/표고 분리 + SSP multiplier
2. **산림경제학자** — Lognormal 가격 + HWP 30년 + WTA 161원 발견 + 이중 표현
3. **산림정책학자** — 룰베이스+RAG hybrid + 노령림 모순 학술 기여
4. **경영자(실무)** — 간벌+10년 시나리오 + KOSIS 폐기 + 전화·URL 박기
5. **AI/ML 엔지니어** — LHS + Strategy 패턴 + uncertainty tier

### Round 2 (3 페르소나, 5/20)
6. **위성/원격탐사** — **+45% 는 모집단 차이** (자연성장 vs 경영후), **NDVI 시계열 = 발표 카드**, GEDI+S2 triangulation Plan B
7. **영세 산주** — 숫자 1개 큼지막 + 카카오톡 멘트 대본 + 펼치기 분리
8. **통합자** — **D115 우선 + "KAU 변곡점" 타이틀** + 5분 7슬라이드 구조

→ 자세한 내용: `_workspace/analysis/07_expert_sessions.md` (Round 1) + `11_expert_sessions_round2.md` (Round 2)

---

## 6 polygon (D116)

### Sample (산주 시연용, 2개)
- `boeun_pine_30y_1.5ha` — 강원소나무 30년, 1.5ha (벌기령 미달 시연)
- `boeun_pine_50y_2ha` — 강원소나무 50년, 2.0ha (벌기령 도달)

### Real 등록사업 (W6 검증 case, 4개)
- `boeun_real_oedari_8197tco2` — 보은 산외면 오대리 산39 외 2필지 ★★★
- `boeun_real_wonpyeongri_63658tco2` — 보은 산외면 원평리 11 외 11필지 (198ha)
- `jinan_real_waryongri_4671tco2` — 진안 용담면 와룡리 산48 외 1필지 ★★★ (영세 사유림 모달)
- `jinan_real_guryongri_18063tco2` — 진안 상전면 구룡리 산122 외 6필지

VWorld 실 좌표 확보: 보은 산외면 오대리 lon=127.7344, lat=36.5841

---

## 단위 테스트 — module_c 160 + shared 15 = 175 (module_bd 59 포함 전체 234)

```
shared/test_schemas.py             15  (가이드 §4.1 + 옵션 P2 확장)
module_c/tests/  (19 파일, 160 tests)
  test_stand_adapter.py            14  (Module A→C 어댑터, D127)
  test_scenarios.py                13
  test_ui_adapter.py               13  (C→ui 어댑터, D127)
  test_sensitivity.py              12  (5 차원 robustness)
  test_lev_core.py                 10  (Faustmann 본체 + 6 시나리오)
  test_compute_lev.py               8  (진입점 + 6 시나리오 dispatch)
  test_draft_plan.py                8  (이중 표현)
  test_grade_distribution.py        8  (Strategy 패턴)
  test_subsidies.py                 8  (산림청 2025 단가)
  test_climate_multiplier.py        7  (임종환 2020 reference)
  test_hwp_decay.py                 7  (IPCC 2019 reference)
  test_ntfp_income.py               7  (2024 보고서 reference)
  test_offset_eligibility.py        7  (8 사업유형)
  test_recommend.py                 7
  test_uncertainty.py               7  (tier 자동 판정)
  test_validation.py                7  (D114 +45% reference)
  test_kau_breakeven.py             6  (D115 margin)
  test_pareto.py                    6  (Hartman 정통)
  test_integration_e2e.py           5  (A·B·C·D·ui 전체 파이프라인)
─────────────────────────────────────
        module_c 160 + shared 15 = 175  (+ module_bd 59 = 전체 234)
```

**정우 패턴 100% 모방**: `_base()` fixture + [검증] D{n} reference + [회귀] 출력 기준선.

---

## DECISIONS ADR (D101-D132, 핵심 발췌)

| ID | 결정 | 근거 |
|---|---|---|
| D9 | LEVResult 스키마 (옵션 P2) | 정우 D4 호환 |
| D102 | stand_state fallback | 민석 미시작 우회 |
| D103 | MC 분포 (Lognormal+LHS) | 경제학자: 음수 방지. AI: LHS 300=MC 1000 |
| D104 | Pareto NPV-탄소 (Hartman) | 경제학자: Hartman 1976 정통 |
| D105 | NTFP 출처 (KOSIS 폐기) | 경영자: KOSIS 임가소득 미제공 |
| D106 | Strategy 등급분포 | 산림학자: Weibull-2P, AI: ABC |
| D107 | HWP IPCC 2019 (35/25/2년) | 경제학자: IPCC default |
| D108 | 8 사업유형 룰+RAG | 정책학자: 80/20 hybrid |
| D109 → D114 | 진안 검증 case | 정책학자 + carbonregistry |
| D110 | 간벌+10년 추가 | 경영자: 영세 사유림 7할 모달 |
| D111 → D116 | demo polygon 정정 | 산림학자 SI + 경영자 모달 |
| D112 | next_actions 구체화 | 경영자: 전화·URL·서류명 |
| D113 | api_server.py 통합 | AI: BackgroundTasks |
| **D114** | **carbonregistry 4 검증 case + 학술 발견 #1** | 사용자 658건 제공 → +45% 차이 (모델 220 vs 인증 320) |
| **D115** | **KAU 16개월 급등 + WTA 돌파 임박 + 학술 발견 #2** | 16개월 +79%(8,670→15,550), WTA 17,039원에 8.7% 미달 |
| D116 | 6 polygon (Sample 2 + Real 4) | VWorld 실 좌표 확보 |

→ 전체: [DECISIONS.md](./DECISIONS.md)

---

## 시연 시나리오 (보은 산외면 오대리 25.6ha, Primary 검증)

```python
from module_c.src.compute_lev import compute_lev_with_plan
from module_c.src.demo_parcels import get_demo_parcel

stand = get_demo_parcel("boeun_real_oedari_8197tco2")
package = compute_lev_with_plan(stand, user_preference="균형", n_samples=300)

# 결과:
# package["draft_plan"]["recommended_scenario"] = "간벌+10년"
# package["draft_plan"]["npv_단순표시"] = "약 ?백만원"
# package["pareto"]["pareto_optimal"] = ["간벌+10년", "연장KOC"]
# package["draft_plan"]["offset_citations"][0]["code"] = "FM-Rotation"
```

---

## 5 PR 시퀀스 (정우 repo, collaborator 권한 후)

| PR | 범위 | 라인 | 상태 |
|---|---|---|---|
| PR 1 | `shared/schemas.py` + 15 tests (D9) | +380 | ✅ Ready |
| PR 2 | `module_c/` 첫 commit (19 src + 8 data + 160 tests) | ~6,500 | ✅ Ready |
| PR 3 | (선택) GEDI+S2 triangulation Plan B (Round 2 위성 학자) | ~500 | ⏳ W4-5 선택 |
| PR 4 | `api_server.py` 통합 (`/compute_lev`) | ~80 | ⏳ W5 |

---

## 발표 (W7, D-37)

**Title**: "Faustmann-Hartman 한국 변형으로 포착한 KAU 시장 변곡점 — 5+1 학자 deliberation 기반 산림탄소 정책 의사결정 프레임워크"

**5분 7슬라이드 구조** (통합자 Round 2):
1. Title + 한 줄 메시지
2. Problem: WTA hurdle 미돌파 시대의 한국 임업
3. Method: Faustmann-Hartman 한국 변형 + 8 학자 deliberation
4. **Finding A: D115 KAU 변곡점** ⭐ 핵심 narrative
5. Finding B: D114 인증-모델 +45% gap
6. Validation: NFI direct lookup + 175 tests + Module A framing
7. Conclusion + 정책 제언

---

## 연락

- 희도 (Module C + Lead): zxsa0716@kookmin.ac.kr
- 정우 (Module B/D): https://github.com/jwn6174-crypto
- NRF 과제: CLIM Lab (임철희 교수)
