# PR 본문 — 정우에게 발송 (collaborator 권한 후)

---

## PR 1: shared/schemas.py 갱신 + tests (D9)

**제목**: `feat(schemas): add LEVResult/ComputeLEVRequest/DraftPlanCard for Module C (D9)`

**Branch**: `feat/lev-result-schema`

**본문**:

```markdown
## 요약

Module C (Faustmann-Hartman LEV) 가 사용할 3 Pydantic 모델 추가.

정우 D4 옵션 P2 패턴 동일:
- Manual 01 §4.1 명세 100% 호환 (필수 필드)
- 우리 확장 Optional (uncertainty_tier, kau_breakeven, climate_multiplier_applied)

## 추가된 스키마

```python
class LEVResult(BaseModel):
    # 가이드 §4.1 필수 — 14 필드
    scenario, T_optimal, npv_per_ha, npv_q05/q95,
    lev_per_ha, timber_revenue, carbon_revenue, ntfp_revenue,
    total_cost, carbon_stock_T, grade_distribution_T,
    feasibility, feasibility_note

    # 확장 Optional — 옵션 P2 (희도 D9, D11, D15, D22, D23)
    monte_carlo_n, discount_rate,
    cost_breakdown, data_sources, limitations,
    uncertainty_tier, uncertainty_note,        # AI D14
    kau_breakeven, kau_breakeven_note,         # 경제학자 + D23
    climate_multiplier_applied                  # 산림학자 D11.b

class ComputeLEVRequest(BaseModel):
    stand_state, scenarios (6 시나리오, D18 간벌+10년 포함),
    discount_rate, n_monte_carlo, climate_scenario

class DraftPlanCard(BaseModel):
    recommended_scenario, npv_median, npv_q05/q95,
    age_now, legal_min_age, npv_uplift_label,
    reasons, offset_citations, next_actions,
    user_preference
```

## 결정 (DECISIONS.md D9)

옵션 P2 채택 — 정우 D4 와 동일 패턴:
- 가이드 명세만으로 LEVResult 생성 가능 (검증 통과)
- 우리 풍부한 자산 (Monte Carlo, KAU breakeven 등) Optional 활용

## 테스트

`shared/test_schemas.py` 15 tests:
- [검증] Manual 01 §4.1 필수 필드만으로 생성 (5)
- [검증] 우리 확장 포함 생성 (5)
- [회귀] D9 fixture reference 값 (5)

```bash
$ python shared/test_schemas.py
15/15 passed ✅
```

## 변경 파일

- `shared/schemas.py`: +180 라인 (LEVResult, ComputeLEVRequest, DraftPlanCard)
- `shared/test_schemas.py`: 신규 200 라인

## 의존성

없음. PR 2 (module_c/) 가 본 PR merge 를 기다림.

## 후속 PR

- PR 2: `module_c/` 첫 commit (19 src + 8 data + 129 tests)
- PR 4: `api_server.py` `/compute_lev` endpoint (W5)
```

---

## PR 2: module_c/ 첫 commit (결정론 + Monte Carlo + Pareto + DraftPlanCard)

**제목**: `feat(module_c): Faustmann-Hartman LEV core + 8 expert deliberation + 2 academic findings`

**Branch**: `feat/module-c-initial`

**본문**:

```markdown
## 요약

Module C (Faustmann-Hartman LEV) 의 코어 — 19 src 파일 + 8 data JSON + 129 tests.

**학술 발견 2개**:
- **D22**: carbonregistry 인증 vs Module C 모델 +103% 차이 (4 case 모두) — 한국 인증실적 baseline 가정 검토 필요성 첫 정량 제기
- **D23**: KAU 16개월 +126% (8,670→19,600), WTA 17,039원 역사적 첫 돌파 (2026-03~05)

## 추가된 파일

### src/ (19 파일)
```
scenarios.py            6 시나리오 + feasibility (D18 간벌+10년 추가)
grade_distribution.py   Strategy 패턴 (HeuristicGD + WeibullGD swap)
hwp_decay.py            IPCC 2019 35/25/2년 (D15)
climate_multiplier.py   SSP × 수종 (D11.b)
subsidies.py            산림청 2025 보조사업 (D18)
ntfp_income.py          2024 임산물 보고서 (D13)
uncertainty.py          tier 자동 판정 (D14)
lhs_sampling.py         Latin Hypercube
lev_core.py             ⭐ Faustmann-Hartman 본체
monte_carlo.py          6 분산 source × LHS
kau_breakeven.py        KAU 임계가 (D23 핵심)
recommend.py            위험회피/균형/수익극대화
offset_eligibility.py   8 사업유형 룰+RAG hybrid (D16)
pareto.py               NPV-탄소 Pareto (D12, Hartman 정통)
draft_plan.py           DraftPlanCard 이중 표현
demo_parcels.py         6 polygon (Sample 2 + Real 4)
compute_lev.py          ⭐ 진입점
data_go_kr_api.py       산림자원통계 + KAU + VWorld (사용자 본인 키)
validation.py           D22 모델 vs 인증 비교
```

### data/ (8 JSON)
```
raw/hwp/hwp_decay_2019.json              IPCC 2019 검증 (PMC 8666044)
raw/climate/climate_multipliers_2020.json  임종환 2020 + IPCC AR6
raw/subsidies/forestry_subsidies_2025.json 산림청 2025 지침
raw/ntfp/forest_byproduct_income_2024.json 2024 임산물 보고서
raw/offset_eligibility/eligibility_rules_2024.json 8 사업유형
raw/registered_offset/all_projects_2026_05.json carbonregistry 658건
raw/kau/kau_timeseries_2025_2026.json     KAU 16개월
processed/validation_cases.json            W6 검증 case 정선
processed/d22_plot_data.json               시각화
processed/d23_plot_data.json               시각화
```

### tests/ (16 파일 + fixtures)
129 tests (정우 45 의 2.8배), 정우 `_base()` 패턴 모방.

### notebooks/ (3 파일)
- 01_lev_derivation.py: Faustmann 손계산 검증
- 02_validation_d22.py: 인증 vs 모델 시각화
- 03_kau_wta_breakeven.py: KAU 시계열 + WTA 돌파

## 8 전문가 deliberation

| 페르소나 | 핵심 기여 |
|---|---|
| 산림학자 | Weibull-2P + SI ±2 + 송이/표고 분리 + SSP multiplier |
| 산림경제학자 | Lognormal 가격 + HWP 30년 + WTA 발견 + 이중 표현 |
| 산림정책학자 | 룰베이스+RAG hybrid + 노령림 모순 학술 기여 |
| 경영자(실무) | 간벌+10년 시나리오 + KOSIS 폐기 + 전화·URL |
| AI 엔지니어 | LHS + Strategy 패턴 + uncertainty tier |
| 위성/원격탐사 | 모집단 차이 + NDVI 시계열 + GEDI+S2 Plan B |
| 영세 산주 | 숫자 1개 큼지막 + 카카오톡 멘트 |
| 통합자 | D23 우선 + "KAU 변곡점" 타이틀 |

## DECISIONS.md ADR 13개 (D9-D24)

자세한 내용: `module_c/DECISIONS.md`

## 정우 module_bd 의존

```python
from module_bd.src.growth_predict import growth_predict, lookup_volume
from module_bd.src.market_snapshot import market_snapshot
from module_bd.src.cost_function import cost_function
from module_bd.src.legal_rotation import rotation_age
from module_bd.src.kau_api import fetch_kau_price
from shared.schemas import LEVResult, ComputeLEVRequest, DraftPlanCard  # PR 1
```

## 테스트

```bash
$ pytest module_c/tests/ -v
129 passed in ~30s ✅
```

## 의존성

- PR 1 (shared/schemas.py LEVResult 추가) merge 필요

## 후속 PR

- PR 3 (선택): GEDI+S2 triangulation Plan B (위성 학자 권고)
- PR 4: `api_server.py` `/compute_lev` endpoint (W5)

## 발표 자료 준비

W7 마감 발표 슬라이드 (5분 7슬라이드):
**Title**: "Faustmann-Hartman 한국 변형으로 포착한 KAU 시장 변곡점"

자세한 빌드 플랜: `module_c/BUILDPLAN.md`
```

---

## PR 4: api_server.py 통합 (W5)

**제목**: `feat(api_server): integrate module_c — /compute_lev endpoint + replace scenarios=None`

**Branch**: `feat/api-compute-lev`

**본문**:

```markdown
## 요약

정우 5/19 commit `3198ea2` 의 `api_server.py` 의 Module C 자리 (`scenarios=None`) 를
실 `module_c.compute_lev()` 호출로 교체. 신규 `/compute_lev` async endpoint 추가.

## 변경

### `/analyze` endpoint (line 250 부근)
```python
# Before:
scenarios = None
recommendation = None

# After:
try:
    from module_c.src.compute_lev import compute_lev_with_plan
    package = compute_lev_with_plan(forest_state, n_samples=300)
    scenarios = {k: v for k, v in package["results"].items()}
    recommendation = package["draft_plan"]
except Exception as e:
    scenarios = {"error": str(e)}
    recommendation = None
```

### 신규 endpoint
```python
@app.post("/compute_lev")
async def compute_lev_endpoint(req: ComputeLEVRequest, bg: BackgroundTasks):
    # 1000+ MC iter HTTP timeout 회피용 BackgroundTasks 패턴
    ...
```

## 의존성

- PR 1 (shared/schemas) merge
- PR 2 (module_c/) merge

## 테스트

```bash
$ uvicorn api_server:app --reload --port 8001
$ curl -X POST http://localhost:8001/analyze -d '{"pnu":"4374025931200110000"}'
# → scenarios.즉시.npv_median 등 반환 (이전엔 null)
```
```

---

## 발송 전 사용자 액션

1. **정우에게 collaborator 권한 요청** (Slack/메신저 1줄)
2. **fork 결정 시**: PR 1, 2 를 fork → upstream 로 발송
3. **collaborator 받으면**: `git checkout -b feat/lev-result-schema` 후 직접 PR

## 본인 명의 commit 설정

```bash
git config user.email "zxsa0716@kookmin.ac.kr"
git config user.name "Heedo Choi"
```
