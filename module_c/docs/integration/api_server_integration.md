# api_server.py 통합 가이드 — Module C 연결 (정우·수범 전달용)

> 이 문서는 정우 `api_server.py` 의 `scenarios = None` 자리를 Module C 의 실제
> 계산 결과로 교체하는 정확한 방법을 담는다. 변경은 두 군데(import 블록과
> Module C 섹션)뿐이며, 기존 Module A·B·D 코드는 손대지 않는다.
>
> **작성**: 희도 · 2026-05-31 · Module A 도착 후 통합

---

## 통합 전체 그림

사용자가 PNU 를 입력하면, 분석 결과는 다음 경로로 흐른다.

```
ui (Next.js)  POST /api/analyze
   │
   ▼
api_server.py  POST /analyze
   │
   ├─ Module A  predict_stand()      → forest_state (위성 임분 상태)
   ├─ Module B  growth_predict()     → growth_forecast (성장 예측)
   ├─ Module D  market_snapshot()    → market_data (시장 가격)
   │
   ├─ stand_adapter.from_forest_state(forest_state)   ← ① 변환
   │     → stand dict (15키 완성)
   │
   ├─ compute_lev_with_plan(stand)                    ← ② Module C 계산
   │     → results · pareto · draft_plan
   │
   └─ ui_adapter.to_ui_scenarios(package)             ← ③ ui 형식 변환
         → scenarios[] · recommendation · offsetEligibility
   │
   ▼
ui  ScenarioTable · NPVChart · ParetoChart · ChatPanel
```

핵심은 Module C 가 api_server 안에서 *직접* 무거운 위성 모델을 부르지 않는다는
점이다. Module A 가 이미 만들어 둔 `forest_state` 만 받아 경제성을 계산하므로,
quantile-forest·rasterio 같은 의존성과 무관하게 가볍게 동작한다.

---

## 변경 1 — import 블록 (파일 상단)

기존 import 아래에 다음 세 줄을 추가한다.

```python
from module_c.src.compute_lev import compute_lev_with_plan
from module_c.src import stand_adapter, ui_adapter
```

> Module C 는 numpy·scipy·pydantic 만 필요하다. 이미 api_server 환경에
> 설치되어 있으므로 추가 설치는 없다.

---

## 변경 2 — Module C 섹션 (기존 `scenarios = None` 교체)

기존 코드:

```python
    # ── Module C: 시나리오 NPV — 미구현 ──────────────────────────────────────
    scenarios     = None   # Module C 미구현
    recommendation = None  # Module C 미구현
```

교체 코드:

```python
    # ── Module C: 시나리오 NPV — 통합 완료 (희도 D127) ───────────────────────
    try:
        # forest_state(camelCase) → Module C stand dict(snake_case, 15키)
        stand = stand_adapter.from_forest_state(forest_state)

        # 6 시나리오 × Monte Carlo(LHS) → NPV·Pareto·추천 카드
        package = compute_lev_with_plan(
            stand,
            n_samples=300,            # LHS 300 = 단순 MC 1000 동등 정확도
            user_preference="균형",   # ui riskPreference 와 연동 가능
        )

        # Module C 결과 → ui Scenario[] 형식
        age_now = forest_state.get("estimatedAge") or stand["age_estimate"]
        scenarios      = ui_adapter.to_ui_scenarios(package, age_now=age_now)
        recommendation = ui_adapter.to_ui_recommendation(package)

        # 8 사업유형 매칭 → offsetEligibility 보강(Module A 의 baselineCarbon 결합)
        offset_from_c = ui_adapter.to_ui_offset_eligibility(package)
        offset_from_c["baselineCarbon"] = (
            forest_state.get("carbonPerHa", 0) * forest_state.get("areaHa", 1)
        )
        offset_eligibility = offset_from_c  # Module C 의 정밀 매칭으로 교체

    except Exception as e:
        # Module C 오류 시에도 A·B·D 결과는 보존(graceful degradation)
        print(f"[Module C] 오류 — scenarios 생략: {e}")
        scenarios      = None
        recommendation = None
```

---

## riskPreference 연동 (선택)

ui 의 `analyzeForest(pnu, riskPreference)` 가 보내는 위험 선호를 Module C 의
추천 알고리즘에 직접 연결할 수 있다.

```python
    # request body 에서 riskPreference 추출
    _PREF_MAP = {"safe": "위험회피", "balanced": "균형", "profit": "수익극대화"}
    user_pref = _PREF_MAP.get(body.get("riskPreference"), "균형")

    package = compute_lev_with_plan(stand, n_samples=300, user_preference=user_pref)
```

이렇게 하면 산주가 ui 에서 "안정형/균형/수익형" 을 고를 때마다 추천 시나리오가
바뀐다(위험회피=q05 최대, 균형=Sharpe-like, 수익극대화=중앙값 최대).

---

## Module A 직접 연결 (api_server 가 위성 실측을 쓸 때)

현재 api_server 는 `mock_module_a(pnu)` 로 지역 프로파일을 쓴다. 민석의
실제 위성 추정으로 바꾸려면 다음만 교체한다.

```python
# 기존:
#   p = mock_module_a(pnu)

# Module A 실측:
try:
    from module_a.predict_stand import predict_stand
    est = predict_stand(
        geom_wkt=geom_wkt,           # VWorld 로 PNU → polygon 조회
        pnu=pnu,
        species_dominant=species,    # 임상도에서
        age_estimate=age_now,
    )
    stand = stand_adapter.from_module_a(est)   # ← forest_state 대신 직접
except (ImportError, FileNotFoundError):
    # 위성 모델·raster 없으면 기존 mock 으로 fallback
    p = mock_module_a(pnu)
    stand = stand_adapter.from_forest_state(forest_state)
```

> Module A 는 raster·QRF 모델(541MB·148MB)을 로컬 생성해야 하며, 없으면
> `confidence='low'` 로 학습 데이터 평균을 쓴다(민석 설계). stand_adapter 는
> 두 경우 모두 동일하게 처리한다.

---

## 검증 방법

1. **Module C 단독**: `python -m module_c.src.compute_lev` → 6 시나리오 출력
2. **stand_adapter**: `python module_c/src/stand_adapter.py` → 4/4 통과
3. **ui_adapter**: `python module_c/src/ui_adapter.py` → 5/5 통과
4. **api_server**: `python api_server.py` 실행 후
   `curl -X POST localhost:8001/analyze -d '{"pnu":"4374533021100010000"}'`
   → `scenarios` 가 null 이 아닌 배열로 반환되는지 확인

---

## 수범에게 — ui 변경 요청 (단 한 줄)

Module C 는 6번째 시나리오 "간벌+10년" 을 `"thinning"` id 로 내보낸다. ui
`src/lib/types.ts` 의 `Scenario.id` union 에 이 값을 추가하면 자동 표시된다.

```typescript
// 기존
id: "immediate" | "five_year" | "ten_year" | "koc" | "ntfp";

// 추가
id: "immediate" | "five_year" | "ten_year" | "koc" | "ntfp" | "thinning";
```

그 외 `Scenario` 의 모든 필드(npv.p5/p50/p95, bankruptcyProb, timberRevenue,
carbonRevenue, harvestCost, regenCost, ntfpRevenue, kocEligible, paretoX,
recommended)는 ui_adapter 가 정확히 채워서 보내므로 ui 컴포넌트는 변경 없이
동작한다.
