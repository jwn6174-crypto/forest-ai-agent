# Module C — Faustmann-Hartman LEV (희도 담당)

> **다목적 산림경영 AI Agent (충북 보은 파일럿)** 의 의사결정 코어.
> 정우 module_bd 의 7 함수 + 자체 모듈 12 = 19 src 파일.
> **8 전문가 deliberation** 기반 학술 발견 2개 (D114 +103%·D115 KAU 돌파).

**Lead**: 희도 (zxsa0716@kookmin.ac.kr)
**기간**: 2026-05-19 ~ 2026-06-26 (W2 후반 ~ W7)
**최종 마감**: 2026-06-26 (공모전 발표, 200만원 상금)
**NRF 과제**: 한국연구재단 일반공동연구 (CLIM Lab, 임철희 교수)

---

## 🏆 학술 발견 2개

### D114 — carbonregistry 인증 vs Module C 모델 +103.2% 차이
- 보은·진안 4 real 등록사업: 인증 320 tCO₂/ha/30yr vs 모델 157
- **한국 산림탄소상쇄 인증실적의 baseline 가정 검토 필요성 첫 정량 제기**
- 가설: (a) 회계 가정 (피크값을 평균으로) 또는 (b) 경영 후 측정 차이 — 위성 학자 (b) 압도적

### D115 — KAU 16개월 +126%, WTA 17,039원 역사적 첫 돌파 (2026-03~05) ⭐ 발표 핵심
- 2025-07 (8,670원, 저점) → 2026-05 (19,600원, +126%)
- **한국 ETS 시장 역사상 처음 WTA 돌파** — 사유림 산주 자발적 KOC 참여 *경제적 합리성* 시점 발견
- 정책학자 D109 의 "노령림 정책 갈등" 해소 가능 시점

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
├── tests/                  (16 파일 + fixtures, 129 tests)
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
6. **위성/원격탐사** — **+103% 는 모집단 차이** (자연성장 vs 경영후), **NDVI 시계열 = 발표 카드**, GEDI+S2 triangulation Plan B
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

## 단위 테스트 — 129 tests (정우 45 의 2.8배)

```
shared/test_schemas.py             15  (가이드 §4.1 + 옵션 P2 확장)
module_c/tests/
  test_scenarios.py                13
  test_hwp_decay.py                 7  (IPCC 2019 reference)
  test_climate_multiplier.py        7  (임종환 2020 reference)
  test_subsidies.py                 8  (산림청 2025 단가)
  test_kau_breakeven.py             6  (D115 161원/2561원)
  test_grade_distribution.py        7  (Strategy 패턴)
  test_uncertainty.py               7  (tier 자동 판정)
  test_ntfp_income.py               7  (2024 보고서 reference)
  test_lev_core.py                 10  (Faustmann 본체 + 6 시나리오)
  test_compute_lev.py               8  (진입점 + 6 시나리오 dispatch)
  test_pareto.py                    6  (Hartman 정통)
  test_recommend.py                 7
  test_offset_eligibility.py        7  (8 사업유형)
  test_draft_plan.py                7  (이중 표현)
  test_validation.py                7  (D114 +103% reference)
─────────────────────────────────────
                                   총 129 tests
```

**정우 패턴 100% 모방**: `_base()` fixture + [검증] D{n} reference + [회귀] 출력 기준선.

---

## DECISIONS ADR 13개 (D9-D116)

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
| **D114** | **carbonregistry 4 검증 case + 학술 발견 #1** | 사용자 658건 제공 → +103% 차이 |
| **D115** | **KAU 16개월 + WTA 돌파 + 학술 발견 #2** | 16개월 +126%, 2026-03~05 첫 돌파 |
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
| PR 2 | `module_c/` 첫 commit (19 src + 8 data + 129 tests) | ~6,500 | ✅ Ready |
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
5. Finding B: D114 인증-모델 +103% gap
6. Validation: NFI direct lookup + 129 tests + Module A framing
7. Conclusion + 정책 제언

---

## 연락

- 희도 (Module C + Lead): zxsa0716@kookmin.ac.kr
- 정우 (Module B/D): https://github.com/jwn6174-crypto
- NRF 과제: CLIM Lab (임철희 교수)
