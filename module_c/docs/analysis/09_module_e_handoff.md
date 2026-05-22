# Module E (수범) ↔ Module C (희도) Handoff — api_server.py 통합 명세

> 정우가 2026-05-19 어제 commit `3198ea2` 로 `api_server.py` (Next.js 연동 FastAPI 브리지) 추가.
> 수범의 module_e 가 이 endpoint 를 호출. **내 compute_lev() 가 들어갈 자리가 이미 비어있음.**

**작성일**: 2026-05-19 (Day 5)
**근거**: 정우 `api_server.py` (276 lines) 직접 분석

---

## 0. 현재 상태 한 화면

```
┌─ 수범 module_e (Next.js, 데모 구축 중) ──────────────────┐
│  사용자가 PNU 입력 → POST /analyze                       │
└────────────────────────┬─────────────────────────────────┘
                         ↓
┌─ 정우 api_server.py (FastAPI, port 8001) ────────────────┐
│  ✅ Module A mock (10 시도 코드별 프로파일)              │
│  ✅ Module B growth_predict() (live)                     │
│  ✅ Module D market_snapshot() (live)                    │
│  ✅ estimate_grade_dist() (6 등급 휴리스틱)              │
│  ✅ Offset Eligibility (간단 룰)                         │
│  ❌ Module C scenarios = None  ← ★ 내가 채워야 할 곳     │
│  ❌ recommendation = None       ← ★ 내가 채워야 할 곳     │
└────────────────────────┬─────────────────────────────────┘
                         ↓
                    JSON 응답 → Next.js UI 표시
```

→ **내 작업**: 정우 `api_server.py` 에 두 줄 (`scenarios=None`, `recommendation=None`) 을 내 `compute_lev()` 호출로 교체하는 PR.

---

## 1. 정우 api_server.py 구조 (276 lines)

### 1.1 핵심 endpoint
- **POST /analyze** — 입력 `{"pnu": "4374025931200110000"}` → 통합 결과 JSON
- **GET /health** — 모듈 상태 dict

### 1.2 응답 schema (현재)

```json
{
  "pnu": "...",
  "analyzedAt": "2026-05-19T00:00:00Z",
  "state": {
    "pnu", "species", "estimatedAge", "volumePerHa", "volumeUncertainty",
    "carbonPerHa", "agbPerHa", "areaHa", "gradeDistribution",
    "forestType", "siteIndex", "coordinates"
  },
  "growth": {
    "years": [0, 5, 10, 20, 30],
    "volumePerHa": [...],
    "carbonPerHa": [...누적...],
    "carbonSequestration": [...연 흡수율 tCO2/ha/yr...],
    "gradeDistributionByYear": [...],
    "climateScenario": "SSP1-2.6"
  },
  "market": {
    "kauPrice", "kocEstimate", "timberPrices",
    "discountRate", "priceDate"
  },
  "scenarios": null,           // ★ 내가 채울 곳
  "recommendation": null,       // ★ 내가 채울 곳
  "offsetEligibility": {
    "eligible", "matchedTypes", "baselineCarbon",
    "additionalityCheck", "nextSteps"
  }
}
```

### 1.3 정우 mock_module_a (활용 가능!)
```python
REGION_PROFILES = {
    "11": 강원 (강원소나무 SI=12 age=45),
    "23": 인천 (잣나무 SI=14 age=38),
    "42": 강원 (낙엽송 SI=14 age=35),
    "43": 충북 (강원소나무 SI=10 age=50) ← 보은!
    "44": 충남 (잣나무 SI=12 age=42),
    "45": 전북 (리기다 SI=10 age=38),
    ...
}
```

→ 내 `stand_state_mock.py` 의 4단 fallback 중 **0단** 으로 정우 `mock_module_a` 호출 가능.

### 1.4 정우 estimate_grade_dist (Strategy 패턴의 default)
```python
def estimate_grade_dist(dbh_cm: float) -> dict:
    """0-7개 DBH 구간별 6 등급 비율 휴리스틱."""
    if dbh_cm < 10: return {teukYongJae:0, grade1:0, ...}
    if dbh_cm < 14: return {...}
    # ... 7 구간
```

→ AI 엔지니어 D14 Strategy 패턴의 `HeuristicGD` 가 정우 이 함수.
→ 내가 만들 `WeibullGD` 는 *추가 옵션*.

---

## 2. 내 compute_lev() endpoint 등록 PR 설계

### 2.1 추가할 endpoint

```python
# api_server.py 끝에 추가

from module_c.src.compute_lev import compute_lev
from module_c.src.draft_plan import draft_management_plan
from shared.schemas import ComputeLEVRequest, LEVResult, DraftPlanCard


@app.post("/compute_lev")
async def compute_lev_endpoint(req: ComputeLEVRequest) -> Dict[str, Any]:
    """5 시나리오 NPV + Pareto + 추천 카드 반환.

    AI 엔지니어 D21 권고: BackgroundTasks 또는 job_id 폴링 패턴 (1000 iter × 5
    scenario > 2초 시 HTTP timeout 위험).
    """
    try:
        results = compute_lev(
            stand=req.stand_state,
            scenarios=req.scenarios,
            discount_rate=req.discount_rate,
            n_mc=req.n_monte_carlo,
            climate_scenario=req.climate_scenario,
        )
        card = draft_management_plan(
            stand=req.stand_state,
            lev_results=results,
            user_preference="균형",
        )
        return {
            "scenarios": {k: v.model_dump() for k, v in results.items()},
            "recommendation": card.model_dump(),
            "computed_at": date.today().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Module C 오류: {e}")
```

### 2.2 /analyze 의 scenarios=None 교체

```python
# 정우 api_server.py 의 line 250 부근 (현재 None 반환):
#   scenarios = None
#   recommendation = None

# 내가 PR 로 교체:
try:
    from module_c.src.compute_lev import compute_lev
    from module_c.src.draft_plan import draft_management_plan

    scenarios_result = compute_lev(
        stand=forest_state,
        scenarios=["즉시", "5년", "10년", "연장KOC", "임산물", "간벌+10년"],
        discount_rate=discount_rate,
        n_mc=300,  # /analyze 는 빠른 응답 위해 300 (full /compute_lev 는 1000)
    )
    card = draft_management_plan(forest_state, scenarios_result)
    scenarios = {k: v.model_dump() for k, v in scenarios_result.items()}
    recommendation = card.model_dump()
except Exception as e:
    # Module C 오류 시 graceful degradation
    scenarios = {"error": str(e)}
    recommendation = None
```

### 2.3 BackgroundTasks 패턴 (full MC 시)

```python
from fastapi import BackgroundTasks
from uuid import uuid4

# 진행 중 job 저장소 (실 production 은 Redis)
JOBS: Dict[str, Dict[str, Any]] = {}


@app.post("/compute_lev_async")
async def compute_lev_async(req: ComputeLEVRequest, bg: BackgroundTasks):
    job_id = str(uuid4())
    JOBS[job_id] = {"status": "pending", "result": None}
    bg.add_task(_run_compute_lev, job_id, req)
    return {"job_id": job_id, "poll_url": f"/jobs/{job_id}"}


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(404)
    return JOBS[job_id]


def _run_compute_lev(job_id: str, req: ComputeLEVRequest):
    try:
        results = compute_lev(...)
        JOBS[job_id] = {"status": "complete", "result": results}
    except Exception as e:
        JOBS[job_id] = {"status": "error", "error": str(e)}
```

---

## 3. forest_state ↔ StandStateEstimate 매핑

정우 api_server.py 의 `forest_state` dict 키 (camelCase, JS-friendly) ↔ 내 `StandStateEstimate` (snake_case, Python-friendly):

| api_server `forest_state` | StandStateEstimate | 변환 |
|---|---|---|
| `pnu` | `pnu` | 동일 |
| `species` | `species_dominant` | rename |
| `estimatedAge` | `age_estimate` | rename |
| `volumePerHa` | `volume_m3_per_ha` | rename |
| `volumeUncertainty` | `volume_se` | rename |
| `carbonPerHa` | `carbon_tc_per_ha` | rename |
| `agbPerHa` | `agb_mg_per_ha` | rename |
| `areaHa` | `area_ha` | rename |
| `gradeDistribution` | `grade_distribution` | dict 키 변환 (teukYongJae → "특용재") |
| `forestType` | (없음) | 새 필드 |
| `siteIndex` | `site_index` | rename |
| `coordinates` | `geom_wkt` 또는 lat/lng | POINT WKT 변환 |

→ `shared/schemas.py` 에 변환 헬퍼:
```python
class StandStateEstimate(BaseModel):
    @classmethod
    def from_api_server_dict(cls, fs: dict) -> "StandStateEstimate":
        """api_server forest_state JSON → 내 schema."""
        return cls(
            pnu=fs["pnu"],
            species_dominant=fs["species"],
            age_estimate=fs["estimatedAge"],
            volume_m3_per_ha=fs["volumePerHa"],
            ...
        )
```

---

## 4. PR 계획 (정우에게)

### 4.1 PR 1: `shared/schemas.py` 갱신 — D9 + D9.1
- Day 6-7
- 내용: LEVResult, ComputeLEVRequest, DraftPlanCard 추가 + uncertainty_tier, kau_breakeven 필드
- 테스트: `shared/test_schemas.py` 5개

### 4.2 PR 2: `module_c/` 디렉토리 첫 commit
- Day 7-W3
- 내용: README, DECISIONS, scenarios.py + 6 시나리오 + tests
- 의존: PR 1 merge 후

### 4.3 PR 3: `api_server.py` 의 scenarios=None 교체
- W3-W4 (compute_lev 결정론 v1 완성 후)
- 내용: line 250 부근 try/except 로 compute_lev 호출
- 의존: PR 2 merge + Module C v1 동작

### 4.4 PR 4: `/compute_lev` async endpoint 추가
- W4-W5 (Monte Carlo + Pareto 완성 후)
- 내용: 위 §2.3 BackgroundTasks 패턴
- 의존: PR 3 + module_c MC 안정성

### 4.5 PR 5: `mock_module_a` 와 내 demo 통합
- W5
- 내용: 정우 `REGION_PROFILES` 에 보은 4개 demo polygon 추가
- 의존: 모든 이전 PR + NFI lookup 실작동

---

## 5. 수범과 합의해야 할 인터페이스

### 5.1 응답 필드 명세 (수범이 Next.js UI 에 표시할 것)

**scenarios 객체 (6 시나리오 × 시각별 정보)**:
```typescript
interface ScenarioResult {
  scenario: "즉시" | "5년" | "10년" | "연장KOC" | "임산물" | "간벌+10년";
  T_optimal: number;
  npv_median: number;
  npv_q05: number;
  npv_q95: number;
  lev_per_ha: number;
  timber_revenue: number;
  carbon_revenue: number;
  ntfp_revenue: number;
  total_cost: number;
  carbon_stock_T: number;
  grade_distribution_T: { 특용재: number; 1등급: number; ... };
  feasibility: boolean;
  feasibility_note?: string;
  uncertainty_tier: "high" | "med" | "low";    // AI D14
  kau_breakeven?: number;                       // 경제학자
  kau_breakeven_note?: string;
}
```

**recommendation 객체 (DraftPlanCard)**:
```typescript
interface Recommendation {
  recommended_scenario: string;
  npv_median: number;
  npv_q05: number;
  npv_q95: number;
  age_now: number;
  legal_min_age: number;
  npv_uplift_label: string;            // "+700만원/ha"
  reasons: string[];                    // 3-5 자연어 문장
  offset_citations?: Citation[];        // 정우 RAG 281 청크
  next_actions: string[];               // 경영자 D20 — 전화·URL·서류명
  user_preference: "위험회피" | "균형" | "수익극대화";

  // 경제학자 권고: 산주 UI 점추정 + 정책 부록 분리
  npv_단순표시: string;                  // "약 1,400만원"
  npv_worst_case_10pct: string;          // "최악의 10% 시 -300만원"
  uncertainty_tier: "high" | "med" | "low";
  uncertainty_note?: string;            // "LiDAR 측정 시 폭 절반"
  full_distribution?: object;           // 정책 부록용 (optional)
  kau_breakeven_warning?: string;       // "KAU 5% 하락 시 LEV 음수"
}
```

### 5.2 수범에게 보낼 메시지 초안

> 수범, 정우가 어제 api_server.py 만든 거 봤어. compute_lev/recommendation 자리가 비어 있더라.
> 내가 W3 끝까지 모듈 C v1 (결정론) 채워서 PR 보낼게. 그 동안 너 데모 UI 에서
> `scenarios = null` 일 때 "Module C 개발 중" placeholder 보여주면 좋겠어.
> W4 끝에는 MC + Pareto + uncertainty_tier 다 들어간 v2 로 전환할 예정.
> TypeScript interface 는 `09_module_e_handoff.md` §5.1, 5.2 에 명세. 더 필요한 필드 있으면 말해줘.

---

## 6. 동시 작업 가능 (수범 unblock)

수범이 *내 compute_lev 결과 없이도* 진행 가능한 것:

| 작업 | 의존 | 기간 |
|---|---|---|
| Next.js 페이지 라우팅 + PNU 입력 UI | 없음 | W3 |
| `/analyze` 응답 표시 (정우 4 모듈) | 정우만 | W3 |
| scenarios placeholder ("개발 중") | 없음 | W3 |
| 6 시나리오 카드 mock UI (내 D18 확정 후) | 내 schema PR | W3 끝 |
| Pareto plot (Plotly.js) | 내 MC PR | W4 끝 |
| DraftPlanCard recommendation 카드 | 내 PR3 | W4 끝 |
| LLM agent 자연어 답변 | 내 모든 PR | W5 |

---

## 7. 위험 + 대응

| # | 위험 | 대응 |
|---|---|---|
| 1 | 정우 api_server.py 가 수범 데모 진행 중에 자주 변경 | 정우와 `/compute_lev` endpoint API 계약 lock 합의 W2 끝 |
| 2 | forest_state dict ↔ StandStateEstimate 키 매핑 오류 | from_api_server_dict 헬퍼 + Pydantic validation 테스트 |
| 3 | 1000 iter MC 가 HTTP 30초 timeout 초과 | BackgroundTasks job_id 폴링 패턴 |
| 4 | 수범이 TypeScript interface 다른 이름으로 짜고 있음 | W2 끝 합의 회의 |
| 5 | 정우 `mock_module_a` 가 실제 polygon 좌표 부족 | 내 stand_state_mock.py 가 GeoJSON polygon 보완 |

---

## 변경 이력
- 2026-05-19 Day 5 — 정우 api_server.py 276 줄 분석, 5 PR 계획 + TypeScript interface 명세
