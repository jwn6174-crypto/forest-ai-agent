# Module C ↔ Module B/D 연계 — 어떻게 정우 함수를 호출하는가

> 정우 module_bd 의 7 함수 + 5 Pydantic 모델 을 Module C 가 어떻게 사용하는지
> *코드 레벨 인터페이스 명세*.

**작성일**: 2026-05-19 (Day 5)
**근거**: 정우 module_bd/README.md + DECISIONS.md + 실제 코드 읽기

---

## 1. Import 경로 (정확)

```python
# module_c/src/compute_lev.py 의 첫 줄들
from module_bd.src.growth_predict import growth_predict, lookup_volume
from module_bd.src.market_snapshot import market_snapshot
from module_bd.src.cost_function import cost_function
from module_bd.src.legal_rotation import rotation_age
from module_bd.src.kau_api import fetch_kau_price
from shared.schemas import (
    GrowthForecast, MarketSnapshot, CostInput, CostBreakdown, RotationRule,
    LEVResult, ComputeLEVRequest, DraftPlanCard,  # D9 PR merge 후
)

# 내 모듈
from module_c.src.scenarios import scenario_T, scenario_feasibility
from module_c.src.stand_state_mock import get_stand_state
from module_c.src.monte_carlo import simulate_npv
```

---

## 2. compute_lev() 내부 호출 흐름

```
compute_lev(stand, scenarios, market=None, discount_rate=0.05, n_mc=1000)
    │
    ├─ market = market_snapshot(date.today())  ─────────→ 정우 D
    │   ↳ MarketSnapshot {timber_price, timber_price_by_species,
    │                     kau_close, koc_estimate, vcm_floor_wta}
    │
    ├─ rotation = rotation_age(species, "사유림")  ────→ 정우 D
    │   ↳ legal_min_age int
    │
    ├─ for sc in scenarios:
    │   │
    │   ├─ T = scenario_T(sc, species, age_now)        → 내 scenarios.py
    │   │
    │   ├─ feasible, note = scenario_feasibility(...)  → 내 scenarios.py
    │   │
    │   ├─ # Monte Carlo 1000회
    │   ├─ for i in range(n_mc):
    │   │   │
    │   │   ├─ gf = growth_predict(species, SI, age_now,  ─→ 정우 B
    │   │   │       forecast_years=list(range(0, T-age_now+1)))
    │   │   │   ↳ List[dict] {age, volume, dbh, height, n_per_ha,
    │   │   │                 tmai, carbon_uptake_rate}
    │   │   │
    │   │   ├─ # AGB triangular sampling
    │   │   ├─ # 등급별 가격 normal sampling (10% std)
    │   │   ├─ # KOC normal sampling (15% std)
    │   │   │
    │   │   ├─ cost = cost_function(  ───────────────────→ 정우 D
    │   │   │     volume_m3=gf[-1]["volume"] * area_ha,
    │   │   │     area_ha=area_ha,
    │   │   │     distance_to_road_km=stand["distance_to_road_km"],
    │   │   │     action="clearcut",
    │   │   │     skidding_distance_m=800,
    │   │   │     slope_class="중",
    │   │   │     species=species,  ← 정우 D6 추가됨
    │   │   │   )
    │   │   │   ↳ CostBreakdown {breakdown, total, unit_costs,
    │   │   │                    data_sources, limitations}
    │   │   │
    │   │   └─ npv = timber_rev + carbon_rev + ntfp - cost - regen
    │   │
    │   ├─ npvs = np.array([... 1000 ...])
    │   ├─ lev = median(npvs) / (1 - e^(-r·T))
    │   │
    │   └─ LEVResult(scenario=sc, T_optimal=T, npv_per_ha=median(npvs),
    │                npv_q05, npv_q95, lev_per_ha=lev, ...)
    │
    └─ return Dict[str, LEVResult]
```

---

## 3. 각 정우 함수가 반환하는 값 — 내가 어떻게 쓰는가

### `growth_predict()` → List[dict]

```python
gf = growth_predict("강원지방소나무", site_index=14, age_now=30,
                    forecast_years=[0, 5, 10, 15, 20], climate_scenario="baseline")
# gf = [
#   {age: 30, volume: 173.0, dbh: 16.9, height: 12.0, n_per_ha: 1261,
#    tmai_m3_per_ha_yr: 5.77, carbon_uptake_rate: 10.77, method: "exact"},
#   {age: 35, ...},
#   ...
#   {age: 50, volume: 281.0, dbh: 22.0, ..., carbon_uptake_rate: 4.92}
# ]
```

**내가 쓰는 값**:
- `gf[-1]["volume"]` × area_ha = T시점 총 재적 → 원목 수입 base
- `gf[t]["carbon_uptake_rate"]` for t in range(T-age_now) = ΔC(t) for 탄소 적분
- 등급분포는 미제공 → 정우 W4 Weibull fit 후 또는 내 휴리스틱 (DBH 평균 → 등급분포 룩업 테이블)

### `market_snapshot()` → dict

```python
snap = market_snapshot("2026-05-15")
# {
#   "date": "2026-05-15",
#   "timber_price": {"특용재": 367000, "1등급": 199700, "2등급": 173400,
#                    "3등급": 161000, "원주재": 155600, "원료재": 76400},
#   "timber_price_by_species": {
#       "강원지방소나무": {"1등급": 199700, ...},
#       "잣나무": {"1등급": 154700, ...},
#       "낙엽송": {"1등급": ...},
#       ... 7 수종
#   },
#   "kau_close": 17200.0,
#   "koc_estimate": 12040.0,  # KAU × 0.7
#   "vcm_floor_wta": 17039.0,
#   "discount_rate": 0.05,
#   "timber_price_meta": {...},
#   "kau_meta": {...},
# }
```

**내가 쓰는 값**:
- `snap["timber_price_by_species"][species][grade]` = p_g
- `snap["koc_estimate"]` = p_C, sampling around it
- `snap["vcm_floor_wta"]` = 17039 → WTA hurdle (KOC > WTA 시만 KOC 수입 카운트)
- `snap["discount_rate"]` = r default, MC 에서 Triangular(0.04, 0.05, 0.06) sampling

### `cost_function()` → CostBreakdown dict

```python
result = cost_function(volume_m3=420, area_ha=1.5, distance_to_road_km=12,
                       action="clearcut", skidding_distance_m=800,
                       slope_class="중", species="강원지방소나무")
# {
#   "breakdown": {"harvest": 4_087_000, "skidding": 5_852_000,
#                 "transport": 6_132_000, "loading": 2_436_000,
#                 "regen": 5_888_000, "admin": 3_637_000},
#   "subtotal": 24_395_000,
#   "admin_overhead_amount": 3_637_000,
#   "total": 28_032_000,
#   "slope_surcharge_applied": 1.20,
#   "unit_costs": {...},
#   "data_sources": {"harvest": "표준품셈 p.59-60 + 대한건설협회",
#                    "skidding": "KOFPI Q4 2025 p.44",
#                    "transport": "KOFPI Q4 2025 p.43",
#                    "regen": "산림청 2025 시행령 16조"},
#   "limitations": ["보육·간벌 재투입 미반영", "충북 보은 지역 특화 X"],
# }
```

**내가 쓰는 값**:
- `result["total"]` = Cost(T)
- `result["data_sources"]` → LEVResult.data_sources 에 merge
- `result["limitations"]` → LEVResult.limitations 에 extend

### `rotation_age()` → int

```python
legal_min = rotation_age("강원지방소나무", "사유림")  # → 40
```

**내가 쓰는 값**: `scenario_feasibility()` 내부에서 T ≥ legal_min 비교.

---

## 4. 데이터 흐름 다이어그램

```
┌─ User (Streamlit, 수범 module_e) ────────────────────────────┐
│  polygon: PNU or WKT                                         │
└────────────────────────┬─────────────────────────────────────┘
                         ↓
┌─ Module E LLM Agent (수범) ────────────────────────────────┐
│  tool: compute_lev(stand_state=..., scenarios=[...])         │
└────────────────────────┬─────────────────────────────────────┘
                         ↓
┌─ get_stand_state() ─ Module A fallback (희도 stand_state_mock)
│  try: module_a.predict_stand()    ← 민석 (미시작)             │
│  fallback: NFI direct lookup       ← data.go.kr 15122903     │
│  fallback: 임상도 (수종·영급)       ← data.go.kr 3045619      │
│  fallback: demo polygon 3개         ← hand-craft + growth_predict
└────────────────────────┬─────────────────────────────────────┘
                         ↓
                  StandStateEstimate
                         ↓
┌─ compute_lev() ─ Module C (희도) ────────────────────────────┐
│  for sc in scenarios:                                         │
│    1. scenario_T(sc, species, age_now)        ← 내 scenarios.py
│    2. for i in range(1000):                                   │
│       - growth_predict(...)        ← 정우 B (tmai + carbon)   │
│       - market_snapshot(...)       ← 정우 D (KOFPI + KAU)     │
│       - cost_function(...)         ← 정우 D (표준품셈 + KOFPI)│
│    3. LEVResult(...)                                          │
└────────────────────────┬─────────────────────────────────────┘
                         ↓
                  Dict[str, LEVResult]
                         ↓
┌─ draft_management_plan() ─ Module C ─────────────────────────┐
│  recommend_scenario(lev_results, user_preference)             │
│  + RAG search: 수범 carbon_chunks.jsonl 281 청크              │
└────────────────────────┬─────────────────────────────────────┘
                         ↓
                    DraftPlanCard
                         ↓
        UI 표시: 시나리오 5개 NPV bar + Pareto plot
                + 추천 카드 + 산림조합 next_actions
```

---

## 5. 통합 충돌 가능 지점 (미리 대비)

| # | 충돌 가능 | 대비 |
|---|---|---|
| 1 | `growth_predict` 가 `grade_distribution_trajectory` 미제공 | 내가 임시 휴리스틱 dict 작성, 정우 W4 fit 후 swap |
| 2 | `cost_function` 의 `species` 파라미터 미인식 (D6 적용 전 버전) | `try/except TypeError` 후 species 빼고 재호출 |
| 3 | `market_snapshot` 의 `koc_estimate` None | `snap.get("koc_estimate") or snap["kau_close"] * 0.7` |
| 4 | 정우의 `module_bd` 미설치 / Python path 안 잡힘 | `sys.path.insert(0, parent of forest-ai-agent)` |
| 5 | `from shared.schemas import LEVResult` D9 merge 전 | `try import → fallback import from shared/schemas_proposed.py` |
| 6 | `carbon_uptake_rate` 가 60년 초과 시 None | 60년 값으로 외삽 + warning |

---

## 6. 통합 테스트 (W3-W4 작성 예정)

```python
# module_c/tests/test_integration.py
def test_compute_lev_real_정우함수():
    """정우 함수 7개 모두 호출되어 NPV 계산 성공."""
    stand = get_stand_state(pnu="4374025931200110000", mode="demo")
    results = compute_lev(stand, scenarios=["즉시", "10년"])
    assert "즉시" in results
    assert results["즉시"].npv_per_ha != 0
    assert "KOFPI" in results["즉시"].data_sources.get("timber_price", "")

def test_compute_lev_law_constraint():
    """30년 강원지방소나무 즉시벌채는 법정 40년 미만 → feasibility=False."""
    stand = get_stand_state(pnu="boeun_pine_30y_1.5ha", mode="demo")
    results = compute_lev(stand, scenarios=["즉시"])
    assert results["즉시"].feasibility == False
    assert "법정 40년" in results["즉시"].feasibility_note
```

---

## 변경 이력
- 2026-05-19 Day 5 — 정우 함수 7개 ↔ 내 compute_lev 인터페이스 명세 작성
