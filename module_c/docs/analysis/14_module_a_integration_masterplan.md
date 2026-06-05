# Module A 도착 시 전체 통합 마스터플랜 (설계)

> **사용자 질문 (2026-05-31)**: "Module A 가 나오면 우리가 발견한 모든것들을 하나도
> 빠짐없이 전부 연계시키고 통합시키는거야? 설계만 해보자"
>
> **답**: 네. Module A 는 **단일 진입점** 으로 4 학술 발견 + ui 4 불일치 + 25 ADR 을 모두
> *강화·연결*. Module A 는 *대체* 가 아니라 *enhancement* (D119) — Module C 코드 변경 최소.

**작성일**: 2026-05-31 (설계만, 코드 X)
**전제**: Module C 25 ADR (D101-D125) 완성, 정우 module_bd 13/13 완성, Module A (민석) 미시작

---

## 0. 통합 철학 — 3 원칙

| # | 원칙 | 근거 |
|---|---|---|
| 1 | **Module A 는 enhancement, not requirement** | D119 — 현재 Module C 단독 작동, A 는 정밀도 강화 |
| 2 | **단일 통합 지점** = `api_server.py` 의 `forest_state` dict | A·B·C·D 모두 이 dict 를 거침 |
| 3 | **모든 학술 발견을 *강화* (대체 X)** | D114·D122 는 A 로 3축化, D115·D124 는 독립 유지 |

---

## 1. Module A 가 제공할 것 (인터페이스 확정)

정우 `api_server.py` 의 `mock_module_a(pnu)` 가 현재 *placeholder* 로 채우는 필드 →
민석 `module_a.predict_stand(pnu)` 가 *위성 실측* 으로 교체:

| forest_state 필드 | 현재 (mock) | Module A 완성 후 (위성) |
|---|---|---|
| `volumePerHa` | REGION_PROFILES 고정값 | GEDI L4A + Sentinel-2 + ALOS PALSAR 추정 |
| `volumeUncertainty` | `cur_vol × 0.15` (15% mock) | **위성 추정 표준오차 (R²~0.66, RMSE~40 Mg/ha)** |
| `agbPerHa` | `cur_vol × 0.45 × 1.2` (placeholder BEF) | **위성 직접 AGB (GEDI 라벨)** |
| `carbonPerHa` | `agb × 0.5 × 44/12` | 위성 AGB × CF |
| `gradeDistribution` | `estimate_grade_dist(dbh)` 휴리스틱 | 위성 + 임상도 stratification |
| `siteIndex` | REGION_PROFILES | 위성 + DEM + 기상 추정 |
| **(신규)** `saturation_warning` | 없음 | **고밀도 임분 위성 포화 여부** |
| **(신규)** `confidence_level` | 없음 | **high/medium/low (위성 신뢰도)** |

→ 핵심: Module A 는 **불확실성 (q05/q95) + 신뢰도 (confidence_level) + 포화경고** 를 *실데이터* 로 제공.
현재 Module C 의 demo polygon 은 이 값들을 ±20% mock 으로 채움.

---

## 2. 통합 의존성 그래프 (무엇이 무엇을 unblock)

```
[Module A 완성 (민석)]
   │ module_a/src/predict_stand.py
   ↓
┌──────────────────────────────────────────────────────┐
│ Phase 1: stand_state swap (D119)                      │
│   Module C fallback chain 1단 자동 활성화 (코드 0 변경)  │
│   6 demo polygon → 실 위성 polygon                     │
└────────────────────┬─────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────┐
│ Phase 2: api_server.py 통합 (D113)                    │
│   mock_module_a → module_a.predict_stand              │
│   scenarios=None → compute_lev_with_plan()            │
└────────────────────┬─────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────┐
│ Phase 3: ui_adapter (4 불일치 해결)                    │
│   LEVResult → ui Scenario[] JSON 변환                 │
└────────────────────┬─────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────┐
│ Phase 4: 학술 발견 4개 × Module A 연계                 │
│   D114 (3축), D122 (3원), D115·D124 (독립 유지)        │
└────────────────────┬─────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────┐
│ Phase 5: 불확실성 전파 + Monte Carlo 실 분산           │
│   confidence_level → uncertainty_tier (실데이터)       │
│   volume_q05/q95 → MC AGB triangular (실 위성)        │
└────────────────────┬─────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────┐
│ Phase 6: 발표·논문 통합 (학술 발견 4개 figure)         │
└──────────────────────────────────────────────────────┘
```

---

## 3. ⭐ 학술 발견 4개 × Module A 연계 매트릭스 (핵심 설계)

### D114 — carbonregistry 인증 +45% → **3축 triangulation 으로 강화**

| | 현재 (Module A 없음) | Module A 완성 후 |
|---|---|---|
| 축 1 | carbonregistry 인증: 320 tCO₂/ha/30yr | (동일) |
| 축 2 | Module C 모델 (자연 성장): 220 | (동일) |
| **축 3** | **없음** | **Module A 위성 AGB (보은 산외면 오대리 25.6ha 실측)** |
| 결론 | 차이 +45%, 가설 (a)/(b) 미결 | **위성이 가설 판별** |

**핵심 설계 — 위성이 +45% 의 원인 규명**:
- Module A 위성 AGB ≈ 인증 흡수량 기반 추정 → 가설 (b) *경영 효과* 입증 (간벌·시비 후 실측)
- Module A 위성 AGB ≈ Module C 모델 → 가설 (a) *인증 과대* (피크값×30 회계)
- 위성 학자 Round 2 핵심 카드 — GEDI L4A footprint (36.58°N 보은 cover, 25-75 shots) + Sentinel-2 NDVI 시계열 (벌채 여부 검증)
- → **발표 슬라이드 5 (Finding B) 를 "3축 triangulation" 으로 격상** = 학술 발견 #1 결정적 강화

### D122 — 영세림 등급분포 역-J → **3원 비교로 강화**

| | 현재 | Module A 완성 후 |
|---|---|---|
| 원 1 | HeuristicGD (수확표): DBH=30 상위등급 95% | (동일) |
| 원 2 | WeibullGD (정우 NFI 7차 충북): 42.6% | (동일) |
| **원 3** | **없음** | **Module A 위성 + 임상도 stratification gradeDistribution** |
| 결론 | 차이 +123% | 영세림 위성 한계 재확인 (위성 학자) |

**핵심 설계 — 영세림 위성 한계 검증**:
- 위성은 직접 DBH 분포 못 줌 (10m 해상도)
- Module A 의 grade_distribution (위성+임상도) 가 제3 추정
- 영세림 (1-2ha) mixed pixel 30-40% → **NFI Weibull (원 2) 이 여전히 best** 임을 입증
- → 위성 학자 발견 ("영세림은 NFI direct lookup 우위") 재확인. D102 정당화.

### D115 — KAU WTA 돌파 임박 → **Module A 독립 (변화 없음)**

- KAU·WTA 는 *시장 데이터* (정우 D 모듈) — Module A 위성과 완전 무관
- 발표 슬라이드 4 (Finding A, 핵심 narrative) 그대로 유지
- → 통합 무관, 안정

### D124 — climate signal 부호 정반대 → **Module A 독립 (정우 D15)**

- 정우 climate_correct (NEX-GDDP) 가 담당 — Module A 위성 무관
- 단, Module A 의 *현재 AGB* 가 과거 30년 기후 효과를 *이미 반영* → cross-check 가능 (보너스)
- → 통합 무관, D123 그대로

**요약**: 4 발견 중 **2개 (D114·D122) 가 Module A 로 강화**, 2개 (D115·D124) 독립 유지.

---

## 4. ui 4 불일치 → `ui_adapter.py` 설계

Phase 3 의 핵심. Module C `LEVResult` → ui `Scenario[]` 변환 모듈.

### 4.1 시나리오 id 매핑 (한글 ↔ 영문 + 간벌 처리)

```
Module C VALID_SCENARIOS    →    ui Scenario.id
─────────────────────────────────────────────
"즉시"                       →    "immediate"
"5년"                        →    "five_year"
"10년"                       →    "ten_year"
"연장KOC"                    →    "koc"
"임산물"                     →    "ntfp"
"간벌+10년"                  →    "thinning" ← ❗ ui types.ts 에 id 추가 필요 (수범)
```
→ **수범에게 명세**: ui `Scenario.id` union 에 `"thinning"` 추가 + ScenarioTable 에 행 1개.

### 4.2 필드·단위 변환표

| ui 필드 | Module C 출처 | 변환 로직 |
|---|---|---|
| `npv.p5/p50/p95` (만원) | `npv_q05/npv_per_ha/npv_q95` (원) | `÷ 10,000` + 키 매핑 |
| `npv.bankruptcyProb` | MC npvs 배열 | `(npv < 0 비율)` 계산 ← monte_carlo.py 에서 추가 산출 |
| `timberRevenue` (만원) | `timber_revenue` (원) | `÷ 10,000` |
| `carbonRevenue` (만원) | `carbon_revenue` | `÷ 10,000` |
| `harvestCost` | `cost_breakdown` (harvest+skidding+transport+loading) | 분해 합산 ÷ 10,000 |
| `regenCost` | `cost_breakdown.regen` | `÷ 10,000` |
| `ntfpRevenue` | `ntfp_revenue` | `÷ 10,000` |
| `kocEligible` (bool) | `offset_citations` 에 FM-Rotation 있으면 true | 추출 |
| `kocMethodology` | `offset_citations[].korean` | "벌기령 연장 산림경영" |
| `paretoX` (유동성 0~1) | `T_horizon` | `1 - T_horizon/30` (즉시=1, 30년=0) |
| `recommended` (bool) | DraftPlanCard `recommended_scenario` | id 비교 |
| `harvestYear` | `T_optimal - age_now` | 직접 |

### 4.3 chat route 연계 (라인 8·10·15)

- chat route 가 `ctx.scenarios.find(sc => sc.recommended)` 사용
- → ui_adapter 가 `recommended` bool 정확히 설정하면 자동 해결
- → LLM 챗봇이 NPV 시나리오 설명 가능 (Module C draft_plan.reasons 활용)

---

## 5. 불확실성 전파 — Module A 신뢰도 → Module C tier (실데이터화)

현재 (demo): `confidence_level="low"` 고정 → uncertainty_tier 계산
Module A 후:

```
Module A confidence_level   →   Module C uncertainty_tier (D-AI)
──────────────────────────────────────────────────────────────
"high" (위성 신뢰)           →   "low" tier (점추정 표시)
"medium"                     →   "med" tier
"low" (영세림/포화)          →   "high" tier (구간 + NFI fallback 안내)
saturation_warning=True      →   "high" tier 강제 + "위성 포화" note
```

- Module A 의 `volumeUncertainty` (실 표준오차) → MC 의 AGB triangular 분산 (현재 ±20% mock 대체)
- → uncertainty.py 의 tier 자동 판정이 *실데이터 기반* 으로 격상
- → 산주 UI 의 "신뢰도 낮음 + 다음 step" 메시지가 실제 위성 신뢰도 반영

---

## 6. Monte Carlo 실 분산 (D103 강화)

| MC 분산 source | 현재 | Module A 후 |
|---|---|---|
| AGB/volume | demo ±20% mock | **위성 q05/q95 (R²~0.66)** |
| 목재가 | KOFPI Lognormal | (동일) |
| KOC | KAU×0.7 Lognormal | (동일) |
| 할인율 | Triangular 0.04-0.06 | (동일) |
| 기후 | 정우 D15 NEX-GDDP | (동일) |

→ AGB 분산만 Module A 로 교체. 나머지 5 source 그대로. **MC 코드 변경 0** (stand dict 의 volume_q05/q95 자동 사용).

---

## 7. 검증 — 3축 triangulation 설계 (W6 검증의 결정판)

4 real polygon (보은 산외면 오대리·원평리, 진안 와룡리·구룡리) 에서:

```
                  보은 산외면 오대리 (25.6ha, 인증 8,197 tCO₂)
   ┌────────────────────────────────────────────────────┐
   │  축 1: carbonregistry 인증    320 tCO₂/ha/30yr      │
   │  축 2: Module C 모델 (자연)   220 tCO₂/ha/30yr      │
   │  축 3: Module A 위성 AGB      ??? (실측)            │
   └────────────────────────────────────────────────────┘
         → 축 3 위치가 +45% 차이의 원인 규명
```

- 위성 학자 Plan B (plan_b_satellite.py stub) 가 GEDI L4A + Sentinel-2 NDVI 시계열로 검증
- → 발표 figure: 4 polygon × 3축 비교 막대그래프

---

## 8. 통합 체크리스트 (Module A D-day)

### Phase 1: stand_state swap (예상 0.5일)
- [ ] 민석 `module_a/src/predict_stand(pnu, geom_wkt)` 인터페이스 검증 (StandStateEstimate dict 키)
- [ ] Module C `stand_state_mock.py` 의 try/except 자동 swap 확인 (코드 0 변경)
- [ ] 6 demo polygon → 실 위성 polygon 전환 테스트

### Phase 2: api_server.py 통합 (D113, 예상 1일)
- [ ] `mock_module_a(pnu)` → `module_a.predict_stand(pnu)` 교체
- [ ] `scenarios = None` → `compute_lev_with_plan()` 호출
- [ ] `forest_state → stand dict` 매핑 헬퍼 (species/age/volume/elev/sigun)

### Phase 3: ui_adapter (예상 1일)
- [ ] `module_c/src/ui_adapter.py` 작성 (§4 변환표)
- [ ] 수범에게 ui `Scenario.id` 에 `"thinning"` 추가 명세 전달
- [ ] bankruptcyProb (MC NPV<0 비율) monte_carlo.py 추가 산출
- [ ] paretoX (유동성 점수) pareto.py 추가

### Phase 4: 학술 발견 연계 (예상 2일)
- [ ] D114 3축 triangulation (위성 AGB vs 인증 vs 모델)
- [ ] D122 3원 비교 (수확표 vs NFI Weibull vs 위성 stratification)
- [ ] plan_b_satellite.py 실 호출 (GEDI + Sentinel-2, EarthData 인증)

### Phase 5: 불확실성 전파 (예상 0.5일)
- [ ] confidence_level → uncertainty_tier 매핑
- [ ] volume_q05/q95 → MC AGB 실 분산

### Phase 6: 발표·논문 (W7)
- [ ] 학술 발견 4개 figure (D114 3축 / D122 3원 / D115 KAU / D124 climate)
- [ ] 논문 §5 Results 갱신

→ **총 예상 5-6일** (Module A 완성 후). Module C 코드 변경은 ui_adapter + 2 함수 추가만.

---

## 9. 리스크 + 대응

| # | 리스크 | 확률 | 대응 |
|---|---|---|---|
| R1 | 민석 predict_stand 인터페이스 다름 | 40% | D119 의 키 명세 사전 전달 |
| R2 | 위성 AGB 가 인증·모델 둘 다와 큰 차이 | 30% | 3축 모두 표시 + 차이 원인 분석 (학술 가치) |
| R3 | GEDI 보은 footprint 부족 | 20% | Sentinel-2 NDVI 시계열로 대체 (벌채 검증만) |
| R4 | ui `thinning` id 추가 수범 지연 | 30% | 6번째 시나리오 임시 숨김 (5개만 표시) |
| R5 | 영세림 위성 신뢰 낮아 NPV 분산 폭증 | 50% | uncertainty_tier high + NFI fallback (이미 설계됨) |

---

## 10. 한 줄 결론

**Module A 는 `forest_state` 단일 dict 만 채우면, Module C 의 fallback chain (D119) +
ui_adapter (§4) 로 4 학술 발견 + ui 4 불일치 + 25 ADR 이 자동 연계.
D114·D122 는 위성으로 *3축化 강화*, D115·D124 는 독립 유지. Module C 코드 변경은
ui_adapter + 2 함수 추가만 — "거의 끝났다" 수준 유지.**

---

## 변경 이력
- 2026-05-31 — Module A 통합 마스터플랜 설계 (코드 X, 설계만). 사용자 "전부 연계" 비전 확인.
