# 정우 repo (forest-ai-agent) 완전 분석

> 2026-05-19 시점 `https://github.com/jwn6174-crypto/forest-ai-agent` 의 모든 디렉토리·파일·결정 인벤토리.

**작성일**: 2026-05-19 (Day 5)
**커밋 시점**: 마지막 push `2026-05-18T14:01:12Z` (commit count ~43)

---

## 디렉토리 구조

```
forest-ai-agent/
├── .gitignore
├── README.md                    (5.2 KB, 팀 전체 README)
├── test_keys.py                 (1.1 KB, API 키 sanity check)
├── test_vworld.py               (2.1 KB, VWorld 인증 테스트)
├── module_bd/
│   ├── README.md                (13 KB) — 모듈 B/D 인터페이스
│   ├── DECISIONS.md             (24 KB) — D1-D8 ADR 8개
│   ├── src/                     (14 파일 = 13 함수모듈 + diagnose/)
│   │   ├── carbon_offset_chunk.py    (7.9 KB)
│   │   ├── cost_function.py          (15.5 KB) ⭐ 비용 5/5
│   │   ├── growth_predict.py         (24.9 KB) ⭐ 성장 + 탄소
│   │   ├── kau_api.py                (4.6 KB)
│   │   ├── kofpi_parse.py            (10.7 KB)
│   │   ├── kofpi_transport_parse.py  (8.7 KB)
│   │   ├── legal_api.py              (6.0 KB)
│   │   ├── legal_rotation.py         (9.3 KB) ⭐ 별표3 룰베이스
│   │   ├── market_snapshot.py        (12.5 KB)
│   │   ├── mt_weather_api.py         (4.7 KB)
│   │   ├── mt_weather_collect.py     (6.2 KB)
│   │   ├── yield_parse.py            (11.6 KB)
│   │   ├── yield_parse_small.py      (5.2 KB)
│   │   ├── yield_table_parse.py      (7.1 KB)
│   │   └── diagnose/                 (학습 기록)
│   ├── tests/                   (5 파일, 45 tests 추정)
│   │   ├── __init__.py
│   │   ├── test_cost_function.py     (5.4 KB, 11 tests)
│   │   ├── test_growth_predict.py    (4.8 KB, 8 tests)
│   │   ├── test_lookup_volume.py     (4.0 KB, 8 tests)
│   │   ├── test_market_snapshot.py   (5.4 KB, 8 tests)
│   │   └── test_rotation_age.py      (5.1 KB, 10 tests)
│   └── data/
│       ├── raw/   (carbon/, carbon_offset/, kau_daily/, kofpi_reports/, law_extracts/,
│       │          seedling/, standard_cost/, wage/, yield_table_2014.pdf)
│       ├── interim/  (yield_table_full.parquet, yield_table_stand.parquet,
│       │              kofpi_*.parquet/csv, carbon_chunks.jsonl)
│       └── processed/  (rotation_age.json)
└── shared/
    ├── __init__.py
    └── schemas.py               (11.6 KB) ⭐ 5 Pydantic 모델
```

**미존재 (내가 만들 것 또는 PR 보낼 것)**:
- `module_a/` — 민석 전체 (빈 폴더로 PR 권장)
- `module_c/` — 내가 만들 핵심
- `module_e/` — 수범 (별도 작업)

---

## README.md 핵심 (정우 작성, 5.2 KB)

```
다목적 산림경영 AI Agent
충북 보은 파일럿 — 4인 학부생 공모전 (200만원 상금)

모듈 A 민석 ⏳ 미시작
모듈 B 나정우 ✅ 핵심 완성
모듈 C 희도 🔄 진행 중
모듈 D 나정우 ✅ 핵심 완성
모듈 E 하수범 🔄 진행 중

NRF 한국연구재단 일반공동연구 (CLIM Lab, 임철희 교수)
```

→ 정우는 이미 나(희도) 를 "모듈 C 진행 중" 으로 README 에 명시.
→ NRF 과제 (CLIM Lab, 임철희 교수) 연계 명시.

---

## module_bd/README.md 핵심 (13 KB)

함수 시그니처 7개 (가이드 §8.2 매칭):

```python
# 1. growth_predict
trajectory = growth_predict(
    species="강원지방소나무", site_index=14,
    age_now=30, forecast_years=[0, 10, 20, 30],
    climate_scenario="baseline",
)
# 반환 dict 키: dt, age, volume, dbh, height, n_per_ha,
#               tmai_m3_per_ha_yr, carbon_uptake_rate

# 2. market_snapshot
snap = market_snapshot(date_iso="2026-05-15")
# timber_price (소나무 6등급) + timber_price_by_species (7수종)
# kau_close, koc_estimate, vcm_floor_wta, discount_rate

# 3. cost_function (정우 D6 ⭐ species 추가됨)
result = cost_function(
    volume_m3=280, area_ha=1.0,
    distance_to_road_km=15, action="clearcut",
    skidding_distance_m=800, slope_class="중",
    species="강원지방소나무",
)
# breakdown: harvest, skidding, transport, loading, regen
# total, unit_costs, data_sources, limitations

# 4. rotation_age
rule = rotation_age("강원지방소나무", "사유림")  # → 40

# 5. lookup_volume (개별 나무)
result = lookup_volume(species="강원지방소나무",
                      bark="수피포함", dbh=20, height=15)
# volume (m³), quality, warning

# 6. fetch_kau_price
price = fetch_kau_price(date_iso="2025-12-31")

# 7. search_law
laws = search_law(query="기준벌기령")
```

---

## module_bd/DECISIONS.md (24 KB, 8 결정)

| ID | 결정 | 날짜 | 핵심 |
|---|---|---|---|
| D1 | KOFPI 수종별 확장 (옵션 B) | 5/13 | 가이드 1수종 → 7수종 |
| D2 | 표준품셈 → 비용 (옵션 Y) | 5/13 | 4-5 작업 + 3 할증, 75-85% 정확 |
| D3 | cost_function KOFPI 우선 + 표준품셈 보완 (5/5) | 5/13 | placeholder 함정 발견·정정 |
| D4 | shared/schemas.py 옵션 P2 | 5/13 | 가이드 100% + 확장 Optional |
| D5 | carbon_uptake_rate 통합 | 5/15 | 국립산림과학원 3,212 표본 |
| D6 | 묘목 단가 산림청 2025 (15수종) | 5/15 | regen -8.5% |
| D7 | 산림탄소상쇄 RAG (11 PDF, 281 청크) | 5/15 | 6 → 8 사업유형 |
| D8 | 산악기상 시계열 (6 관측소) | 5/16 | 진행 중, 1/6 완료 |

→ ADR 형식: 상황 → 대안 비교 표 → 선택 + 근거 → 한계 → 시연 가치.
→ 내가 D9 부터 동일 형식으로 작성.

---

## shared/schemas.py (11.6 KB, 5 모델)

```python
class GrowthForecast(BaseModel):           # growth_predict 반환
    species, site_index, age_now, climate_scenario
    forecast_years, volume_trajectory, dbh_trajectory,
    height_trajectory, n_per_ha_trajectory
    # Optional 확장
    grade_distribution_trajectory, carbon_uptake_rate,
    tmai_trajectory, method, warning
    # 헬퍼
    @classmethod from_trajectory_dicts(...)

class MarketSnapshot(BaseModel):           # market_snapshot 반환
    date, timber_price, kau_close, koc_estimate,
    vcm_floor_wta=17039, discount_rate=0.05
    # Optional 확장
    timber_price_by_species, timber_price_meta, kau_meta

class CostInput(BaseModel):                # cost_function 입력
    volume_m3, area_ha, distance_to_road_km, action,
    skidding_distance_m=500.0, slope_class="중"

class CostBreakdown(BaseModel):            # cost_function 출력
    breakdown, subtotal, admin_overhead_amount, total
    slope_surcharge_applied, unit_costs,
    data_sources, limitations

class RotationRule(BaseModel):             # rotation_age 컨텍스트
    species, ownership="사유림", legal_min_age
    legal_basis, species_category
```

**내가 추가할 모델 (Day 6-7 PR)**:
- `LEVResult` — compute_lev 의 시나리오 1개 출력
- `ComputeLEVRequest` — Module E 의 input schema
- `DraftPlanCard` — draft_plan 의 UI 카드 출력

---

## tests/ 구조 (45 tests 추정)

정우 패턴: **함수당 평균 9 tests**.
- 검증 테스트: 가이드·법령 보증값 (예: 강원지방소나무 사유림 = 40년)
- 회귀 테스트: 현재 출력 기준선 (예: 30년 SI=14 volume = 173.0 ± 0.1)

```python
# 예시 (test_rotation_age.py 추정)
def test_rotation_age_정우의_법령_기준값():
    assert rotation_age("강원지방소나무", "사유림") == 40  # 별표 3 보증
    assert rotation_age("잣나무", "사유림") == 60
    assert rotation_age("낙엽송", "사유림") == 30
    assert rotation_age("참나무류", "사유림") == 25
    assert rotation_age("포플러류", "사유림") == 3
```

→ 내 module_c/tests/ 도 **함수당 9 tests** 목표. 5 함수 × 9 = 45 tests.

---

## .gitignore (2.1 KB)

추정 내용: `__pycache__/`, `*.pyc`, `.venv/`, `.env`, `data/raw/*` (큰 PDF 제외 가능),
`data/interim/*.parquet`, `*.log`, `.DS_Store`, `.idea/`, `.vscode/`.

→ 내가 `data/raw/nfi_plots/*.parquet` 추가 필요할 수도 (큰 파일).

---

## 진척도 정량 (Day 4 마감 = 2026-05-15 기준)

| 지표 | 값 |
|---|---|
| 총 commits | ~43 |
| DECISIONS | 8 (D1-D7 마감, D8 진행) |
| 단위 테스트 | 45 (5 함수 × 9 평균) |
| 함수 시그니처 | 7 / 가이드 §8.2 7개 모두 ✅ |
| 진짜 데이터 | 5/5 (가이드 §7.1 placeholder 함정 모두 정정) |
| RAG 코퍼스 | 281 청크 / 11 PDF |
| Pydantic 모델 | 5 / 가이드 §8.1 4개 + 1 (CostInput/Breakdown 분리) |
| 가이드 §1.2 책임 안 | 9/11 (82%) |

→ 정우는 발표용 정량 수치만으로도 **공모전 1차 통과 수준**. 내가 module_c 까지 동급으로
만들면 학술 깊이 (Faustmann-Hartman 한국 변형) + 데이터 깊이 양쪽 모두 달성.

---

## 변경 이력
- 2026-05-19 Day 5 — 정우 repo 완전 인벤토리, 함수 시그니처·결정·테스트 분석
