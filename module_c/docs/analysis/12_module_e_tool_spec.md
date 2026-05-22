# 5 Tool Function Spec — 수범 module_e LLM Agent 호출용

> Manual 01 §07 통합 모듈 명세 — Person 4 (수범) 의 Claude Sonnet 4.6 function calling.
> 사용자 (희도) 가 거절한 "수범 TypeScript 합의" 와 별개로, **API 명세 자체는 학술 기여로 작성**.
> 수범이 W5 통합 시점에 본 명세를 참조하여 5 tool 등록.

**작성일**: 2026-05-20 Day 6
**근거**: Manual 01 §07 + Round 2 통합자 5분 7슬라이드 + 정우 api_server.py 패턴

---

## 0. LLM Agent 의 5 tool 목록

| # | Tool name | Module C 함수 | 용도 |
|---|---|---|---|
| 1 | `get_stand_state` | `demo_parcels.get_demo_parcel` + 향후 `module_a.predict_stand` | polygon → StandStateEstimate |
| 2 | `growth_forecast` | `module_bd.growth_predict` (정우) | T년 후 임분 상태 |
| 3 | `compute_lev` | `module_c.compute_lev_with_plan` | ⭐ 6 시나리오 NPV + Pareto + DraftPlanCard |
| 4 | `match_offset_methodology` | `module_c.find_eligible_project_types` + `search_rag_citations` | 8 사업유형 매칭 |
| 5 | `draft_management_plan` | `module_c.create_draft_plan` | 산림경영계획 초안 |

---

## 1. `get_stand_state`

### Description (LLM prompt 용)
```
임야 polygon (PNU 또는 좌표) 을 받아 현재 상태 (수종·임령·면적·체적 등) 를 반환.
민석 module_a (위성 AGB) 미시작 시 NFI direct lookup 또는 demo polygon fallback.
```

### Schema
```json
{
  "name": "get_stand_state",
  "description": "임야의 현재 상태 추정 (StandStateEstimate)",
  "input_schema": {
    "type": "object",
    "properties": {
      "pnu": {"type": "string", "description": "19자리 PNU 코드"},
      "geom_wkt": {"type": "string", "description": "POLYGON WKT (PNU 대신)"},
      "mode": {"type": "string", "enum": ["auto", "demo", "nfi", "imsangdo"], "default": "auto"}
    }
  }
}
```

### 호출 예
```python
result = get_stand_state(pnu="4374025931200110000", mode="auto")
# 또는 lot_id 기반
result = get_stand_state(geom_wkt="POLYGON((127.73 36.58, ...))")
```

### 반환
```json
{
  "pnu": "...",
  "species_dominant": "강원지방소나무",
  "age_estimate": 40,
  "site_index": 14,
  "area_ha": 25.6,
  "volume_m3_per_ha": 240,
  "carbon_tc_per_ha": 110,
  "distance_to_road_km": 1.5,
  "confidence_level": "registered",
  "_label": "보은 산외면 오대리 실 등록사업"
}
```

---

## 2. `growth_forecast`

### Description
```
수종·임령·SI 받아 T년 후 임분 상태 예측 (정우 growth_predict 호출).
SSP 기후 시나리오 옵션 (희도 climate_multiplier 적용).
```

### Schema
```json
{
  "name": "growth_forecast",
  "description": "수종·임령·SI → T년 후 임분 trajectory",
  "input_schema": {
    "type": "object",
    "properties": {
      "species": {"type": "string", "enum": ["강원지방소나무", "잣나무", "낙엽송", ...]},
      "site_index": {"type": "integer", "minimum": 8, "maximum": 22},
      "age_now": {"type": "integer", "minimum": 0, "maximum": 200},
      "forecast_years": {"type": "array", "items": {"type": "integer"}, "default": [0, 10, 20, 30]},
      "climate_scenario": {"type": "string", "enum": ["baseline", "SSP126", "SSP245", "SSP585"], "default": "baseline"}
    },
    "required": ["species", "site_index", "age_now"]
  }
}
```

### 반환
List[dict] — 각 시점 임분 (volume, dbh, height, carbon_uptake_rate 등)

---

## 3. `compute_lev` ⭐ 핵심 tool

### Description
```
임야 상태 + 6 시나리오 → Faustmann-Hartman NPV + LEV + Pareto + 추천 카드.
LLM agent 가 산주에게 자연어로 답할 핵심 정보.
```

### Schema
```json
{
  "name": "compute_lev",
  "description": "6 시나리오 NPV·LEV + Pareto + DraftPlanCard",
  "input_schema": {
    "type": "object",
    "properties": {
      "stand_state": {"type": "object", "description": "get_stand_state 결과"},
      "scenarios": {
        "type": "array",
        "items": {"type": "string", "enum": ["즉시","5년","10년","연장KOC","임산물","간벌+10년"]},
        "default": ["즉시","5년","10년","연장KOC","임산물","간벌+10년"]
      },
      "user_preference": {"type": "string", "enum": ["위험회피","균형","수익극대화"], "default": "균형"},
      "discount_rate": {"type": "number", "default": 0.05},
      "climate_scenario": {"type": "string", "default": "baseline"},
      "n_samples": {"type": "integer", "default": 300, "description": "LHS Monte Carlo samples"}
    },
    "required": ["stand_state"]
  }
}
```

### 반환
```json
{
  "results": {
    "즉시": {"npv_median": ..., "npv_q05": ..., "npv_q95": ..., "feasibility": true, ...},
    "간벌+10년": {...},
    ...
  },
  "pareto": {
    "pareto_optimal": ["간벌+10년", "연장KOC"],
    "dominated": ["즉시", ...]
  },
  "three_representative": [
    {"_label": "안정형", "scenario": "연장KOC", ...},
    {"_label": "균형형", "scenario": "간벌+10년", ...},
    {"_label": "수익형", "scenario": "10년", ...}
  ],
  "draft_plan": {
    "recommended_scenario": "간벌+10년",
    "natural_summary": "우리 산 → 솎아베기 + 10년 더 키우기. 잘되면 ...",
    "kakao_message": "우리 산 솎아베기 + 10년 더 키우기 추천 ...",
    "npv_단순표시": "약 879백만원",
    "npv_uplift_label": "+3,000만원/ha",
    "reasons": [...],
    "next_actions": [...],
    "offset_citations": [...],
    "uncertainty_tier": "med",
    "kau_breakeven_warning": ...
  }
}
```

### LLM 자연어 답변 패턴
```
LLM input:  "보은 산외면 오대리 25.6ha 강원소나무 40년 어떻게 해야해요?"
Tool call:  get_stand_state → compute_lev
LLM output: "보은 산외면 오대리 임지는 솎아베기 후 10년 더 키우는 게 추천 시나리오입니다.
            잘되면 약 11억원, 보통 8.8억원, 못되면 7.2억원 정도 예상됩니다.
            산림조합에서 250만원/ha 보조금 받을 수 있고, 충북 +10% 보너스도 있어요.
            카카오톡으로 자녀에게 메시지 보낼까요?"
```

---

## 4. `match_offset_methodology`

### Description
```
임야 상태 → 산림탄소상쇄 8 사업유형 중 적용 가능한 것 자동 매칭.
룰베이스 80% + 정우 RAG (carbon_chunks 281 청크) 20% hybrid.
```

### Schema
```json
{
  "name": "match_offset_methodology",
  "description": "임야 → 적용 가능 8 사업유형",
  "input_schema": {
    "type": "object",
    "properties": {
      "stand_state": {"type": "object"},
      "owner_intent": {"type": "string", "enum": ["wood_products", "biomass", "land_use_avoidance"]},
      "fire_history_within_5yr": {"type": "boolean", "default": false},
      "target_species": {"type": "string", "description": "수종갱신 시 목표 수종"}
    },
    "required": ["stand_state"]
  }
}
```

### 반환
```json
[
  {
    "code": "FM-Rotation",
    "korean": "벌기령 연장 산림경영",
    "eligible": true,
    "reason": "임령 40년 ≥ 법정 40년 — 적격. 한국 인증실적 99% 이 사업유형. KAU/WTA margin 2,561원 (D23 시점)",
    "verification": "rule_based",
    "rag_excerpts": [...]
  },
  ...
]
```

---

## 5. `draft_management_plan`

### Description
```
LEV 결과 + 사업유형 매칭 → 산림경영계획 초안 (산림조합 인가 신청 양식).
산림기본법상 산주가 작성해야 할 양식의 자동 fill.
```

### Schema
```json
{
  "name": "draft_management_plan",
  "description": "산림경영계획 초안 dict",
  "input_schema": {
    "type": "object",
    "properties": {
      "stand_state": {"type": "object"},
      "lev_results": {"type": "object", "description": "compute_lev 결과"},
      "user_preference": {"type": "string", "default": "균형"},
      "region": {"type": "string", "default": "충북 보은"}
    },
    "required": ["stand_state", "lev_results"]
  }
}
```

### 반환
DraftPlanCard (Tier 1·2·3) 분리 출력.

---

## LLM Prompt 권고 (수범 module_e 작성 시)

### System prompt 핵심
```
당신은 한국 산림경영 AI Agent (Module C v1.0.0). 영세 사유림 산주의 NPV 의사결정 보조.

원칙:
1. 산주 (60대, 농업 부업) 대상 자연어 — 학술 용어 최소화
2. 점추정 + 분포 이중 표현 (높은 불확실성 시 분포만)
3. 다음 행동 (산림조합·산림청 FGIS·산림탄소센터) 항상 제공
4. KAU breakeven 경고 정직 (D23 발견)
5. 카카오톡 메시지 자동 생성 (자녀 → 산주)

Tool 사용 순서:
1. get_stand_state — 임야 polygon 입력 시
2. compute_lev — 시나리오 비교 요청 시 (가장 자주)
3. match_offset_methodology — 산림탄소상쇄 관심 시
4. draft_management_plan — 신청 양식 요청 시
```

### 산주 질문 예제 → LLM 호출 패턴

**Q: "우리 산 어떻게 해요?"** (40대 자녀 카톡 입력)
```
1. get_stand_state(pnu=...) or 주소 입력 요청
2. compute_lev(stand_state, ...)
3. 자연어 답변: draft_plan.natural_summary + reasons[0-2] + next_actions[0-1]
4. 추가 정보 원하면 → match_offset_methodology + draft_management_plan
```

---

## 통합 시점 (W5)

수범이 본 명세 기반 module_e 작성 시:
1. `api_server.py` 의 `/compute_lev` endpoint 호출 (정우 5/19 신규)
2. 위 5 tool 등록 (Claude function calling)
3. system prompt 위 원칙 적용
4. Streamlit UI 에 DraftPlanCard Tier 1·2·3 카드 표시

---

## 변경 이력
- 2026-05-20 Day 6 — 5 tool 명세 작성 (Manual 01 §07 + 정우 api_server.py + Round 2 통합자 권고)
