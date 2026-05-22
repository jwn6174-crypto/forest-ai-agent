# Module C 단독 완성 빌드 플랜 — 정우 repo 합치기 (통합·민석 제외)

> **사용자 정정 (2026-05-19)**: "나는 module_c 만 완성하면 됨. 민석 module_a 완성 후 통합은 나중.
> 지금은 정우 BD 완성 깃허브에 module_c 를 완벽하게 합쳐야만 함."
>
> 이 문서는 그 정정을 반영한 **module_c 단독 작업의 완전한 명세**.
> 길이 ~900 lines, 7 섹션. 이 문서 하나로 W5 끝 (6/11) 까지 작업 자체 충족.

**작성일**: 2026-05-19 (Day 5 저녁)
**근거**: 정우 module_bd 14 src 파일 + DECISIONS 8개 + api_server.py 276줄 + 5 전문가 deliberation
**완료 기준 (W5 끝, 6/11)**: 정우 repo `main` 에 module_c 가 merge 되어 `pytest module_c/tests/` 70+ green, demo polygon 4개 결정론 + Monte Carlo + Pareto + DraftPlanCard 모두 동작.

---

## 1. 책임 경계 — Module C 의 정확한 영역

### 1.1 IN — module_c 가 책임지는 것 (오직 이것만)

| 영역 | 책임 |
|---|---|
| **LEV 수식 instantiation** | Faustmann (1849) + Hartman (1976) 한국 변형 식 코드화 |
| **5+1 시나리오 분기** | 즉시 / 5년 / 10년 / 연장KOC / 임산물(S5a 표고·S5b 송이) / **간벌+10년** |
| **Monte Carlo + LHS** | 1000 sample × 6 분산 source (Lognormal 가격, Triangular AGB·할인율 등) |
| **HWP carbon decay** | `L_C(T) = Σ HWP·(1-exp(-ln2·t/h))`, h=30년 기본 ±10년 민감도 |
| **Pareto front** | NPV vs 누적 탄소격리 (Hartman 정통, 단일축) + Risk 보조 |
| **추천 알고리즘** | 위험회피(q05 max) / 균형(Sharpe-like) / 수익극대화(median max) |
| **DraftPlanCard 생성** | 산주 UI (점추정) + 정책 UI (분포) 이중 표현 |
| **8 사업유형 룰베이스** | 정우 RAG 281 청크 추출 → 룰베이스 80% + 키워드 검색 20% |
| **KAU breakeven 계산** | 시나리오 4 연장KOC 의 임계가 + 정직성 명시 |
| **불확실성 tier 자동 판정** | q05-q95 폭 비율 → {high/med/low}, LLM prompt fragment 자동 |
| **module_c 만의 데이터 5개** | HWP, NTFP, 기후 multiplier, 산림보조사업, 8사업유형 룰 |
| **shared/schemas.py 추가** | LEVResult, ComputeLEVRequest, DraftPlanCard (옵션 P2 패턴) |

### 1.2 OUT — module_c 가 책임지지 않는 것 (다른 모듈 또는 통합 단계)

| 영역 | 누가 | 언제 |
|---|---|---|
| 위성 AGB / NFI lookup / 임상도 lookup | 민석 module_a | 민석 시작 후 |
| 위성-NFI fallback chain | 민석 또는 통합 단계 | W5+ 통합 시점 |
| api_server.py `/analyze` endpoint 의 scenarios 자리 교체 | 통합 단계 (PR 5) | W5 끝 |
| Next.js UI 의 Plotly 컴포넌트 | 수범 module_e | 진행 중 |
| LLM agent function calling 5 tool | 수범 module_e | W4-5 |
| RAG embedding (BGE-M3, FAISS) | 수범 module_e | W4 |
| `mock_module_a` 의 PNU → polygon 변환 | 정우 (api_server.py 에 이미 있음) | 완료 |
| 임분수확표 PDF 파싱·yield_table | 정우 module_bd | 완료 |
| KOFPI 가격·KAU API·표준품셈 | 정우 module_bd | 완료 |
| 별표 3 룰베이스 + 법제처 API | 정우 module_bd | 완료 |
| 산림탄소상쇄 11 PDF chunking | 정우 module_bd | 완료 |

→ **나는 위 IN 12개만 한다**. OUT 은 호출만 하거나 무시.

### 1.3 통합·민석 의존을 피하는 방법

module_c 는 W5 끝까지 *민석 없이* + *수범 UI 없이* 단독 동작 가능해야 한다. 방법:

1. **입력**: `compute_lev(stand_state: dict, ...)` 의 `stand_state` 는 **dict** 로 받음 (정우 `forest_state` JSON 호환).
   민석이 채우든 정우 `mock_module_a` 가 채우든 무관 — module_c 는 dict 의 키만 본다.
2. **시연용 demo 4 polygon**: `module_c/data/processed/demo_parcels.json` 에 사전 계산된 dict 4개 보관 (정우 `growth_predict()` 출력 + hand-craft 좌표).
3. **테스트**: pytest 가 demo dict 만 사용 — 외부 의존 0.
4. **출력**: `Dict[str, LEVResult]` + `DraftPlanCard` 만 반환. 수범 UI 가 어떻게 표시하든 무관.

---

## 2. 정우 module_bd 와의 인터페이스 — 정확 매트릭스

### 2.1 import 경로 (확정, 7 함수)

```python
# module_c/src/compute_lev.py 의 첫 import 블록
from module_bd.src.growth_predict import growth_predict, lookup_volume
from module_bd.src.market_snapshot import market_snapshot
from module_bd.src.cost_function import cost_function
from module_bd.src.legal_rotation import rotation_age
from module_bd.src.kau_api import fetch_kau_price
from module_bd.src.legal_api import search_law

from shared.schemas import (
    GrowthForecast,    # 정우 D4
    MarketSnapshot,    # 정우 D4
    CostInput, CostBreakdown,  # 정우 D4
    RotationRule,      # 정우 D4
    LEVResult,         # 내 D9 (PR 1)
    ComputeLEVRequest, # 내 D9 (PR 1)
    DraftPlanCard,     # 내 D9 (PR 1)
)
```

### 2.2 정우 함수 호출 정확한 패턴

#### growth_predict() — 가장 자주 호출

```python
# 입력
trajectory = growth_predict(
    species="강원지방소나무",          # 필수, 별표 3 정식명
    site_index=14,                      # 필수, int 8-22
    age_now=30,                         # 필수, int
    forecast_years=[0, 5, 10, 15, 20],  # list[int], age_now 부터 상대 년
    climate_scenario="baseline",        # "baseline" | "SSP126" | "SSP245" | "SSP585"
)

# 출력 — List[dict] (각 시점)
[
    {
        "age": 30, "volume": 173.0, "dbh": 16.9, "height": 12.0,
        "n_per_ha": 1261, "tmai_m3_per_ha_yr": 5.77,
        "carbon_uptake_rate": 10.77,     # ← Hartman 식의 ΔC(t) ⭐
        "method": "exact",
        "warning": None,
    },
    {"age": 35, ...},
    ...
    {"age": 50, "volume": 281.0, ..., "carbon_uptake_rate": 4.92},
]
```

**내가 사용하는 키**:
- `trajectory[-1]["volume"]` × area_ha = T시점 총 재적 → 원목 수입 base
- `trajectory[t]["carbon_uptake_rate"]` for t in trajectory = ΔC(t) → 탄소 적분
- `trajectory[t]["dbh"]` → 정우 `estimate_grade_dist(dbh)` 에 입력 → 등급분포

**알려진 한계**:
- `grade_distribution_trajectory` 없음 → 정우 `estimate_grade_dist(dbh)` 우회 (api_server.py 안에 있음, 내가 wrap)
- 60+년 외삽 시 `method="extrapolated_above"` + warning → 내가 limitations 에 자동 추가
- `climate_scenario != "baseline"` 시 실제 보정 미작동 (정우 D8 진행 중) → 내가 SSP multiplier 별도 적용

#### market_snapshot() — 한 번 호출

```python
snap = market_snapshot(date_iso="2026-05-19")

# 출력 dict
{
    "date": "2026-05-19",
    "timber_price": {                    # 소나무 기본 6 등급
        "특용재": 367000, "1등급": 199700,
        "2등급": 173400, "3등급": 161000,
        "원주재": 155600, "원료재": 76400,
    },
    "timber_price_by_species": {         # 7 수종 × 6 등급 ⭐ 정우 D1
        "강원지방소나무": {...},
        "잣나무": {...},
        "낙엽송": {...},
        "리기다소나무": {...},
        "편백": {...},
        "참나무류": {...},
        "백합나무": {...},
    },
    "kau_close": 17200.0,                # KRX 일별
    "koc_estimate": 12040.0,             # KAU × 0.7
    "vcm_floor_wta": 17039.0,            # 박2020 ⭐ KAU 와 161원 차이
    "discount_rate": 0.05,               # 산주 평균
    "timber_price_meta": {"source": "KOFPI Q4 2025", ...},
    "kau_meta": {...},
}
```

**내가 사용하는 키**:
- `snap["timber_price_by_species"][species][grade]` = p_g (Lognormal sampling base)
- `snap["koc_estimate"]` = p_C (Lognormal sampling base)
- `snap["vcm_floor_wta"]` = 17039 → WTA hurdle 검증
- `snap["discount_rate"]` = r default

#### cost_function() — 시나리오마다 호출

```python
# 입력 (정우 D6 species 추가됨)
result = cost_function(
    volume_m3=420.0,                  # T시점 총 재적
    area_ha=1.5,
    distance_to_road_km=12.0,         # 산주 입력
    action="clearcut",                # "clearcut" | "thinning" | "planting"
    skidding_distance_m=800.0,        # 기본 500
    slope_class="중",                 # "완" | "중" | "급"
    species="강원지방소나무",         # 수종별 묘목 단가 (정우 D6)
)

# 출력 dict
{
    "breakdown": {
        "harvest": 1_200_000,
        "skidding": 1_100_000,
        "transport": 1_500_000,
        "loading": 300_000,
        "regen": 700_000,
    },
    "subtotal": 4_800_000,
    "admin_overhead_amount": 720_000,
    "total": 5_520_000,
    "slope_surcharge_applied": 1.20,
    "unit_costs": {...},
    "data_sources": {                  # 정우 5/5 자동 출력 ⭐
        "harvest": "산림사업 표준품셈 (산림청 고시 제2025-82호) p.59-60 + ...",
        "skidding": "KOFPI 분기별 원목시장가격조사 보고서 소운반비 (2025 Q4 침엽수)",
        ...
    },
    "limitations": [
        "묘목 단가: 산림청 *공식 조림용* 가격 — ...",
        "보육·간벌 재투입 비용 미반영",
        ...
    ],
}
```

**내가 사용하는 키**:
- `result["total"]` = Cost(T) 항 (할인 적용 전)
- `result["data_sources"]` → `LEVResult.data_sources` 에 merge
- `result["limitations"]` → `LEVResult.limitations` 에 extend

**action 분기**:
- `즉시 / 5년 / 10년` → `action="clearcut"` (벌채+조림)
- `연장KOC` → `action="clearcut"` (T년 후 벌채)
- `임산물` → `action="clearcut"` (T년 후), + 매년 NTFP 매출 별도
- `간벌+10년` → `action="thinning"` (간벌, 30-40% 본수 제거), + 10년 후 별도 처리

#### rotation_age() — 1회 호출 (시나리오 feasibility 검증)

```python
legal_min = rotation_age(species="강원지방소나무", ownership="사유림")
# → 40 (int, 년)
```

#### fetch_kau_price() — 보조 (시계열 sensitivity 분석 시)

```python
hist = fetch_kau_price(date_iso="2025-12-31")
# 일별 종가 dict
```

#### search_law() — RAG 보조 (8 사업유형 매칭 시)

```python
# 정우 RAG 와 별개로 법령 직접 검색
laws = search_law(query="기준벌기령")
# 법령 조항 메타 list
```

### 2.3 정우 `estimate_grade_dist` (api_server.py 내부 함수) — 직접 사용 패턴

정우는 `api_server.py` 안에 `estimate_grade_dist(dbh_cm) -> dict` 휴리스틱을 작성. 7 DBH 구간 × 6 등급 비율 룩업.

```python
# module_c/src/grade_distribution.py 에서 정우 함수 import
# 정우 api_server.py 가 module 이 아니라 script 라 *함수만 복사*하거나 sys.path 추가

# 방안 A: 정우에게 api_server.py 의 estimate_grade_dist 함수를
#         module_bd/src/grade_dist.py 로 분리하는 PR 제안 (작은 PR, 친절)
# 방안 B: 내가 같은 휴리스틱을 module_c/src/grade_distribution.py 에 복사
#         (정우 D{n} reference 로 둔다)

# 권장: 방안 A — 정우와 합의 후 PR (라인 수 ~30, 5분 작업)
```

이걸 `HeuristicGD` 로 wrap (AI 엔지니어 Strategy 패턴):

```python
# module_c/src/grade_distribution.py
from abc import ABC, abstractmethod
from typing import Dict

class GradeDistributionStrategy(ABC):
    """등급분포 추정 전략 — 정우 W4 Weibull fit 으로 swap 가능."""
    @abstractmethod
    def estimate(self, dbh_cm: float, species: str = None) -> Dict[str, float]:
        ...

class HeuristicGD(GradeDistributionStrategy):
    """정우 api_server.estimate_grade_dist 의 7 DBH 구간 휴리스틱."""
    def estimate(self, dbh_cm, species=None):
        from module_bd.src.grade_dist import estimate_grade_dist  # 방안 A
        return estimate_grade_dist(dbh_cm)

class WeibullGD(GradeDistributionStrategy):
    """Bailey & Dell (1973) Weibull-2P fit. 정우 W4 NFI 협업 후."""
    def estimate(self, dbh_cm, species=None):
        # NFI 의존 → W5 이후
        raise NotImplementedError("W4 Weibull fit 대기")

# default: HeuristicGD (W4 이후 swap)
```

---

## 3. module_c 만의 데이터 — 5 종 구축

> **민석 영역 (NFI 직접 lookup, 임상도)** 은 제외. 정우 영역 (KOFPI/KAU/표준품셈/별표3/RAG) 도 제외.
> *오직 LEV 계산 자체에 필요한* 데이터만.

### 3.1 D-C-1: HWP (Harvested Wood Products) Carbon Decay 룰베이스 ⭐ P0

**용도**: Faustmann-Hartman 의 `L_C(T)` 항. 벌채 시 모든 탄소가 즉시 release 되는 것이 아니라, 제재목·합판·종이로 분해됨. h 년 half-life 의 지수감쇠.

**수식 (경제학자 D15 권고)**:
```
L_C(T) = Σ_i HWP_i · (1 − exp(−ln2 · t / h_i))
       = Σ_i HWP_i · (1 − 2^(−t/h_i))
```

- `HWP_i` = T시점 탄소 stock × 제품 분배 비율 (제재목 60%, 합판 25%, 종이/펄프 15% — 한국 침엽수 표준)
- `h_i` = 제품 half-life (제재목 30년, 합판 25년, 종이 2년)
- `t` = 벌채 후 경과 년 (LEV 영구 사이클이므로 무한 적분)

**출처**:
1. **IPCC 2019 Refinement to 2006 Guidelines** — `https://www.ipcc-nggip.iges.or.jp/public/2019rf/`
   - Vol 4 Ch12 HWP, Table 12.2 default half-lives
2. **국립산림과학원 2021 「목재제품의 탄소저장량 산정 방법」** PDF
   - 한국 침엽수 평균 28년 (IPCC 30년 ≈)
3. **김영환 외 (2021)** "한국 산림 탄소수지에서 HWP 의 역할" 한국임학회지

**저장**: `module_c/data/raw/hwp/hwp_decay_2021.json`

```json
{
  "_meta": {
    "source": "국립산림과학원 2021 + IPCC 2019 Refinement Tier 1",
    "law_basis": "「산림자원의 조성 및 관리에 관한 법률」 시행규칙 별표 9 (탄소저장량 산정)",
    "decision_id": "D15",
    "fetched_at": "2026-05-XX",
    "limitations": [
      "한국 침엽수 데이터 (활엽수 미반영)",
      "제품 분배 비율은 통계청 「임산물 생산조사」 2023 기준 — 가공율 변동"
    ]
  },
  "products": {
    "lumber": {
      "korean_name": "제재목",
      "half_life_years": 30,
      "default_share_for_conifer": 0.60,
      "uncertainty_years": 10,
      "source": "IPCC Tier 1 + 국립산림과학원 28년 (평균값 사용)"
    },
    "panel": {
      "korean_name": "합판/파티클보드",
      "half_life_years": 25,
      "default_share_for_conifer": 0.25,
      "uncertainty_years": 5,
      "source": "IPCC Tier 1"
    },
    "paper": {
      "korean_name": "종이/펄프",
      "half_life_years": 2,
      "default_share_for_conifer": 0.15,
      "uncertainty_years": 1,
      "source": "IPCC Tier 1 + 한국 펄프산업 평균"
    }
  }
}
```

**파싱 코드**: `module_c/src/hwp_decay.py` — `compute_hwp_decay(carbon_stock_at_T, T, decay_horizon=100)` 함수, 100년 적분.

**테스트**: `test_hwp_decay.py` 6 tests — IPCC reference, 합산 100%, 시간 단조감소 등.

### 3.2 D-C-2: 임산물 소득 룩업 테이블 ⭐ P0 (시나리오 S5)

**용도**: 시나리오 5 (임산물 병행) 의 `π_NTFP(t)` 항. 시나리오 분리: S5a 표고 (carbon 중립~+15%), S5b 송이 (carbon -15~-25%, 산림학자 권고).

**출처 (KOSIS 폐기, 경영자 D13 권고)**:
1. **산림청 「2023 임산물 생산조사」 연보** — `https://www.forest.go.kr/kfsweb/cmm/fms/FileDown.do` (PDF/HWP)
   - 표고/송이/산양삼/산나물/밤/호두 6 카테고리
2. **충북농업기술원 임업기술센터 보은지소** — 보은군청 산림과 통해 직접 확인
   - 보은 특화 ha당 실수익 (전국 평균 대비 ±20%)
3. **산림조합중앙회 임산물 유통정보** — `https://nfck.or.kr/board/forestPrice/list`
   - 월별 유통 단가 (시계열 변동성)

**저장**: `module_c/data/raw/ntfp/forest_byproduct_income_2023.json`

```json
{
  "_meta": {
    "source": "산림청 임산물 생산조사 2023 + 충북농기원 보은지소 + 산림조합",
    "decision_id": "D13",
    "fetched_at": "2026-05-XX",
    "regional_specificity": "충북 보은 1.0x, 전국 평균 0.95x (보수)"
  },
  "products": {
    "표고": {
      "production_method": "노지 원목재배 (참나무 1000본/ha)",
      "annual_income_won_per_ha": {"min": 3_000_000, "mean": 5_500_000, "max": 8_000_000},
      "peak_year_after_planting": 4,
      "yield_period_years": 7,
      "carbon_impact_on_pine": "+5~+15% (간벌재 활용)",
      "applicability": ["참나무", "낙엽송 (보조)"],
      "source": "산림청 임산물생산조사 2023 + 충북농기원 보은지소"
    },
    "송이": {
      "production_method": "천연 발생 (소나무림 균근)",
      "annual_income_won_per_ha": {"min": 500_000, "mean": 1_500_000, "max": 3_000_000},
      "peak_year_after_planting": 30,
      "yield_period_years": 50,
      "carbon_impact_on_pine": "-15~-25% (시비 제한, 하층식생 제거)",
      "applicability": ["강원지방소나무", "중부지방소나무"],
      "source": "산림청 + 산림학자 deliberation"
    },
    "산양삼": {
      "annual_income_won_per_ha": {"min": 500_000, "mean": 1_000_000, "max": 1_500_000},
      "peak_year_after_planting": 7,
      "...": "..."
    },
    "산나물": {
      "annual_income_won_per_ha": {"min": 300_000, "mean": 500_000, "max": 800_000},
      "...": "..."
    }
  }
}
```

**파싱 코드**: `module_c/src/ntfp_income.py` — `lookup_ntfp(product, species, region="보은") -> dict` 함수.

**테스트**: `test_ntfp_income.py` 5 tests.

### 3.3 D-C-3: SSP 기후 Multiplier ⭐ P1 (산림학자 권고)

**용도**: `growth_predict(climate_scenario="SSP245")` 가 정우 D8 진행 중이라 미작동. 내가 별도 multiplier 로 보정.

**출처**:
1. **임종환 (2020)** 국립산림과학원 「기후변화 시나리오 하 한국 주요 수종 생장 변화 전망」
   - 강원지방소나무 SSP2-4.5 → +5~-10%, SSP5-8.5 → -15~-25%
   - 낙엽송 → -15~-25%, -25~-40%
   - 잣나무 → 미변화~+5%, -5~-15%
   - 참나무류 → +10~+20%, +5~+15% (열적 유리)
2. **국립산림과학원 2024 「기후변화 적응 산림계획 가이드라인」**

**저장**: `module_c/data/raw/climate/climate_multipliers_2020.json`

```json
{
  "_meta": {
    "source": "임종환 (2020) 국립산림과학원",
    "decision_id": "D11.b",
    "scenarios": ["baseline", "SSP126", "SSP245", "SSP585"],
    "horizon_years": 30
  },
  "multipliers": {
    "강원지방소나무": {
      "baseline": {"mean": 1.00, "std": 0.05},
      "SSP126":    {"mean": 1.02, "std": 0.08},
      "SSP245":    {"mean": 0.97, "std": 0.10, "range": [0.90, 1.05]},
      "SSP585":    {"mean": 0.80, "std": 0.15, "range": [0.75, 0.85]}
    },
    "낙엽송": {
      "baseline": {"mean": 1.00, "std": 0.05},
      "SSP245":    {"mean": 0.80, "std": 0.10, "range": [0.75, 0.85]},
      "SSP585":    {"mean": 0.68, "std": 0.15, "range": [0.60, 0.75]}
    },
    "...": "..."
  }
}
```

**파싱 코드**: `module_c/src/climate_multiplier.py` — `apply_climate_multiplier(volume_trajectory, species, scenario) -> list` 함수, Monte Carlo 의 6번째 분산 source.

### 3.4 D-C-4: 산림 보조사업 단가 (간벌·갱신·풀베기) ⭐ P0 (D18 간벌 시나리오)

**용도**: 시나리오 6 "간벌+10년" 의 간벌 매출 (ha당 200-300만원 보조). 정우 cost_function 의 `action="thinning"` 은 비용만 계산 — 보조사업 매출은 별도.

**출처**:
1. **산림청 「2025 산림보조사업 지침」 PDF** — `forest.go.kr` 통합자료실
   - 간벌 ha당 2,500,000원 (1차 솎아베기)
   - 어린나무 가꾸기 ha당 1,800,000원
   - 풀베기 ha당 900,000원
   - 갱신 (재조림) ha당 4,500,000원 (1차 5년차까지)
2. **충북도 산림과 보조사업 안내** — 도 자체 추가 보조 (지역 차이)

**저장**: `module_c/data/raw/subsidies/forestry_subsidies_2025.json`

```json
{
  "_meta": {
    "source": "산림청 2025 산림보조사업 지침",
    "decision_id": "D18",
    "fetched_at": "2026-05-XX"
  },
  "subsidies_won_per_ha": {
    "thinning_1st": {"amount": 2_500_000, "korean": "1차 솎아베기", "frequency": "1회"},
    "thinning_2nd": {"amount": 2_000_000, "korean": "2차 솎아베기", "frequency": "1회"},
    "young_tree_care": {"amount": 1_800_000, "korean": "어린나무 가꾸기", "frequency": "1회"},
    "weeding": {"amount": 900_000, "korean": "풀베기", "frequency": "3회 (1·2·3년차)"},
    "reforestation": {"amount": 4_500_000, "korean": "재조림", "frequency": "5년차까지"}
  },
  "regional_bonus": {
    "충북": 0.10,
    "전북": 0.05,
    "기타": 0.0
  }
}
```

**파싱 코드**: `module_c/src/subsidies.py` — `lookup_subsidy(action, region="충북") -> int` 함수.

### 3.5 D-C-5: 8 사업유형 적용 룰베이스 ⭐ P1 (D16)

**용도**: `draft_management_plan` 의 `offset_citations` 필드. 사용자 polygon → 가능한 사업유형 자동 매칭.

**8 사업유형 (산림탄소상쇄제도 2025.1.2 기준)**:
1. 신규조림·재조림 (afforestation_reforestation)
2. 벌기령 연장 산림경영 (forest_management_rotation)
3. 식생복구 (vegetation_restoration)
4. 목제품 이용 (wood_products)
5. 산림 바이오매스 (forest_biomass)
6. 수종 갱신 (species_conversion)
7. 산불피해지 조림 (fire_damage_planting)
8. 산지전용 억제 (land_use_avoidance)

**출처 (정책학자 D16 하이브리드 권고)**:
- 80%: 산림청 「산림탄소상쇄 운영지침 2024」 PDF — 각 사업유형 *적용 조건* 직접 추출
- 20%: 정우 RAG 281 청크 검색 (모호한 경우 fallback)

**저장**: `module_c/data/raw/offset_eligibility/eligibility_rules_2024.json`

```json
{
  "_meta": {
    "source": "산림탄소상쇄 운영지침 2024 (산림청) + 정우 carbon_chunks.jsonl 추출",
    "decision_id": "D16",
    "version": "2025.1.2"
  },
  "project_types": {
    "afforestation_reforestation": {
      "korean": "신규조림·재조림",
      "rules": {
        "species_required": ["all"],
        "age_max": 0,
        "land_history": "1990년 이전 무립목지 또는 무수목 5년 이상",
        "area_min_ha": 0.5,
        "ownership_required": ["사유림", "공유림"]
      },
      "verification": "RAG"
    },
    "forest_management_rotation": {
      "korean": "벌기령 연장 산림경영",
      "rules": {
        "species_required": ["all"],
        "age_min": "법정 기준벌기령 -10",
        "extension_required_years": 10,
        "area_min_ha": 0.5
      },
      "verification": "rule_based"
    },
    "...": "..."
  }
}
```

**파싱 코드**: `module_c/src/offset_eligibility.py` — `find_eligible_types(state) -> List[dict]` 함수.

---

## 4. 코드 7 Tier 빌드 — 라인 수·파일·테스트 상세

> 각 tier 의 완료 = 정우에게 PR 보낼 수 있는 상태.

### Tier 1 — shared/schemas.py PR (Day 6-7, ~2 days)

| 파일 | 라인 수 | 책임 | tests |
|---|---|---|---|
| `shared/schemas.py` 갱신 | +180 (기존 357 → 537) | LEVResult / ComputeLEVRequest / DraftPlanCard 추가 (옵션 P2 패턴) | shared/test_schemas.py |
| `shared/test_schemas.py` 신규 | 200 | 5 검증 + 5 회귀 + 5 edge case = 15 tests | (자체) |

**PR 1 본문 초안** (정우에게 보낼 것):
```
feat(schemas): add LEVResult/ComputeLEVRequest/DraftPlanCard for Module C (D9)

옵션 P2 패턴 (D4 동일):
- Manual 01 §4.1 명세 100% 호환 (필수 필드)
- 우리 확장 Optional 필드 (uncertainty_tier, kau_breakeven 등)

DECISIONS.md D9 동시 PR.

테스트: shared/test_schemas.py 15 tests (가이드 매칭 5 + 회귀 5 + edge case 5)
```

**검증 기준**:
- 가이드 Manual 01 §4.1 필드만으로 `LEVResult(...)` 생성 가능 (5/5)
- 확장 필드 포함도 동일하게 생성 (5/5)
- `feasibility=False` 시 `feasibility_note` 자동 required validation
- `uncertainty_tier="high"` 시 `uncertainty_note` required

### Tier 2 — module_c/ 디렉토리 첫 commit (Day 8-11, ~4 days)

**Phase 2.1: scenarios + grade_dist + lev_core**

| 파일 | 라인 수 | 책임 | tests |
|---|---|---|---|
| `module_c/README.md` | 250 | 정우 README 모방 | - |
| `module_c/DECISIONS.md` | 400 | D9-D11 ADR | - |
| `module_c/BUILDPLAN.md` | 300 | 이 문서의 module_c 한정 요약 | - |
| `module_c/src/__init__.py` | 10 | public API | - |
| `module_c/src/scenarios.py` | 100 (완료) | 6 시나리오 T + feasibility | test_scenarios.py 12 |
| `module_c/src/grade_distribution.py` | 80 | Strategy 패턴, HeuristicGD wrap | test_grade_distribution.py 6 |
| `module_c/src/lev_core.py` | 200 | Faustmann-Hartman 단일 시나리오 결정론 (NPV·LEV 계산) | test_lev_core.py 10 |

**lev_core.py 함수 명세**:
```python
def compute_npv_deterministic(
    stand: dict,
    scenario: str,
    T: int,
    growth_trajectory: List[dict],   # 정우 growth_predict 결과
    market: dict,                     # 정우 market_snapshot 결과
    cost: dict,                       # 정우 cost_function 결과 (이미 호출됨)
    grade_dist_at_T: Dict[str, float],
    discount_rate: float = 0.05,
    hwp_decay: bool = True,
    climate_multiplier: float = 1.0,
) -> dict:
    """
    단일 시나리오의 NPV 결정론 계산 (Monte Carlo 없음).

    Returns:
        {
            "npv": float,
            "lev": float,
            "timber_revenue": float,
            "carbon_revenue": float,
            "ntfp_revenue": float,
            "total_cost": float,
            "hwp_release": float,
            "carbon_stock_T": float,
        }
    """
```

**Phase 2.2: compute_lev + demo_parcels + tests**

| 파일 | 라인 수 | 책임 | tests |
|---|---|---|---|
| `module_c/src/compute_lev.py` | 250 | 6 시나리오 dispatch → lev_core 호출 → Dict[str, LEVResult] | test_compute_lev.py 15 |
| `module_c/src/demo_parcels.py` | 150 | 4 demo polygon + 정우 함수로 사전 계산 | test_demo_parcels.py 6 |
| `module_c/data/processed/demo_parcels.json` | (생성) | 4 polygon 의 stand_state dict | - |
| `module_c/notebooks/01_lev_derivation.ipynb` | (notebook) | Faustmann 손계산 검증 | - |

**4 demo polygon** (D19 갱신, 산림학자 SI 정정):

```python
DEMO_PARCELS = {
    "boeun_pine_30y_1.5ha_outlying": {
        "pnu": "4374025931200110000",
        "species_dominant": "강원지방소나무",
        "site_index": 15,          # 산림학자 권고 14→15
        "age_estimate": 30,
        "area_ha": 1.5,
        "distance_to_road_km": 6.0,  # 경영자 권고 12→6
        "confidence_level": "low",
        "_label": "외곽 케이스 (보은 산간 일부)",
    },
    "boeun_rigida_35y_3ha_modal": {
        "pnu": "4374025931200660000",
        "species_dominant": "리기다소나무",
        "site_index": 10,
        "age_estimate": 35,
        "area_ha": 3.0,
        "distance_to_road_km": 0.8,
        "confidence_level": "low",
        "_label": "보은 사유림 모달 케이스 (경영자 권고)",
    },
    "boeun_pine_50y_2ha": {
        "pnu": "4374025931200220000",
        "species_dominant": "강원지방소나무",
        "site_index": 15,
        "age_estimate": 50,
        "area_ha": 2.0,
        "distance_to_road_km": 1.5,
        "confidence_level": "low",
        "_label": "벌기령 도달 (40년 기준)",
    },
    "jinan_larch_25y_5ha": {
        "pnu": "4574025931200330000",
        "species_dominant": "낙엽송",
        "site_index": 17,          # 산림학자 16-18
        "age_estimate": 25,
        "area_ha": 5.0,
        "distance_to_road_km": 2.0,
        "confidence_level": "low",
        "_label": "지역 확장 시연 (진안)",
    },
}
```

**PR 2 본문**:
```
feat(module_c): scenarios + LEV deterministic + 4 demo parcels (D10, D14, D18-19)

- 6 시나리오 (간벌+10년 추가, D18)
- HeuristicGD Strategy 패턴 (D14, 정우 estimate_grade_dist wrap)
- 단일 시나리오 NPV 결정론 (Monte Carlo 없음, v1)
- 4 demo polygon (보은 30/35/50, 진안 25, D19)

테스트: pytest module_c/tests/  → 49 green
의존: PR 1 (shared/schemas) merge 필요
```

### Tier 3 — Monte Carlo + LHS + HWP + 기후 (W3 5/22-5/28, ~6 days)

| 파일 | 라인 수 | 책임 | tests |
|---|---|---|---|
| `module_c/src/lhs_sampling.py` | 100 | scipy.stats.qmc.LatinHypercube wrap | test_lhs.py 5 |
| `module_c/src/monte_carlo.py` | 250 | 6 분산 source × N samples → NPV 분포 | test_monte_carlo.py 10 |
| `module_c/src/hwp_decay.py` | 150 | L_C(T) 지수감쇠, 100년 적분 | test_hwp_decay.py 6 |
| `module_c/src/climate_multiplier.py` | 100 | SSP × 수종 → growth multiplier | test_climate_multiplier.py 6 |
| `module_c/src/uncertainty.py` | 80 | q05-q95 폭 → tier {high/med/low} + LLM prompt | test_uncertainty.py 4 |
| `module_c/data/raw/hwp/hwp_decay_2021.json` | (data) | IPCC + 국립산림과학원 룰베이스 | - |
| `module_c/data/raw/climate/climate_multipliers_2020.json` | (data) | 임종환 2020 룰베이스 | - |
| `module_c/notebooks/02_mc_stability.ipynb` | (notebook) | LHS vs 단순 MC 수렴 비교 | - |

**Phase 3.1: MC 단순 (Day 11-13)**
Lognormal 가격 + Triangular AGB + Triangular 할인율 → 단순 MC, 수렴 std<5% 검증.

**Phase 3.2: LHS + HWP + 기후 (Day 14-17)**
LHS 6차원으로 변환 → 300 samples 로 동일 정확도. HWP decay 추가. 기후 multiplier 적용.

**PR 3 본문**:
```
feat(module_c): Monte Carlo + LHS + HWP decay + climate multiplier (D11, D15)

- Latin Hypercube Sampling (scipy.stats.qmc) — 300 samples 로 1000 단순 MC 동등 정확도
- Lognormal 목재가/KOC (D11 경제학자 권고)
- HWP carbon decay h=30년 단일 + ±10년 민감도 (D15)
- SSP 기후 multiplier (D11.b 산림학자 권고)
- uncertainty_tier 자동 판정 + LLM prompt fragment (AI D14)

테스트: pytest  → 80 green (누적)
검증: 5 시나리오 × demo 4개 = 20 cell, 수렴 std/median < 0.05 모두 통과
```

### Tier 4 — Recommend + 8 사업유형 + DraftPlanCard (W4 5/29-6/4, ~6 days)

| 파일 | 라인 수 | 책임 | tests |
|---|---|---|---|
| `module_c/src/pareto.py` | 150 | NPV-누적탄소 Pareto + Plotly | test_pareto.py 6 |
| `module_c/src/recommend.py` | 100 | Sharpe-like / q05 max / median max | test_recommend.py 8 |
| `module_c/src/kau_breakeven.py` | 80 | KAU 임계가 계산 | test_kau_breakeven.py 5 |
| `module_c/src/ntfp_income.py` | 100 | 표고/송이/산양삼/산나물 룩업 | test_ntfp.py 5 |
| `module_c/src/offset_eligibility.py` | 200 | 8 사업유형 룰베이스 + RAG hybrid | test_offset.py 10 |
| `module_c/src/subsidies.py` | 80 | 간벌·갱신·풀베기 보조사업 단가 | test_subsidies.py 5 |
| `module_c/src/draft_plan.py` | 250 | DraftPlanCard 이중 표현 (산주·정책) | test_draft_plan.py 10 |
| `module_c/data/raw/ntfp/forest_byproduct_income_2023.json` | (data) | 산림청 + 충북농기원 + 산림조합 | - |
| `module_c/data/raw/subsidies/forestry_subsidies_2025.json` | (data) | 산림청 2025 지침 | - |
| `module_c/data/raw/offset_eligibility/eligibility_rules_2024.json` | (data) | 8 사업유형 룰 + RAG 참조 | - |
| `module_c/notebooks/03_pareto_demo.ipynb` | (notebook) | 4 demo × Pareto plot | - |

**PR 4 본문**:
```
feat(module_c): Pareto + recommend + DraftPlanCard + NTFP + 8 offset types (D12-D17)

- Pareto front: NPV vs 누적 탄소격리 (Hartman 정통, D12 경제학자)
- 추천 알고리즘: 위험회피/균형/수익극대화 (Sharpe-like)
- KAU breakeven 자동 계산 + 정직 명시 (경제학자)
- DraftPlanCard 이중 표현: 산주 점추정 + 정책 분포 (D14 경제학자)
- NTFP 룩업: 표고/송이/산양삼/산나물 (D13 KOSIS 폐기, 산림청+충북농기원+산림조합)
- 8 사업유형 룰베이스 80% + 정우 RAG 20% hybrid (D16 정책학자)
- 간벌 보조사업 매출 통합 (D18)
- next_actions 구체화 — 전화·URL·서류명 (D20 경영자)

테스트: pytest  → 119 green (누적)
```

### Tier 5 — api_server.py 통합 PR (W5 6/5-6/11, ~3 days)

**유일하게 통합 작업** — 그러나 매우 작음 (정우 api_server.py 의 2줄 교체).

| 파일 | 변경 | 책임 |
|---|---|---|
| `api_server.py` 갱신 | ~30 lines | scenarios=None, recommendation=None 자리 교체 |
| `api_server.py` 신규 endpoint | ~50 lines | POST /compute_lev (BackgroundTasks) |

**PR 5 본문**:
```
feat(api_server): integrate module_c — replace scenarios=None (PR 5)

- /analyze endpoint 의 scenarios=None 교체 → module_c.compute_lev 호출
- /compute_lev 신규 endpoint (BackgroundTasks, 1000+ MC iter 용)
- forest_state ↔ StandStateEstimate 매핑 헬퍼

의존: PR 4 merge 필요
테스트: api 통합 테스트 6 추가
```

### Tier 6 — 검증 + 논문 + 슬라이드 (W6 6/12-6/18)

**module_c 코드 작업 끝**. W6 는 케이스 스터디 + 학술 산출.

| 파일 | 책임 |
|---|---|
| `module_c/notebooks/04_jinan_validation.ipynb` | 진안/보은 등록사업 1건 비교 figure |
| `_workspace/manuscript/draft_v1.md` | 논문 §1-§7 초안 (IMRaD) |
| `_workspace/slides/v1.md` (marp) | 발표 슬라이드 15-20장 |

### Tier 7 — Final (W7 6/19-6/26)

발표 리허설 + 최종 정비.

---

## 5. 정우 patterns 100% 모방 — 체크리스트

| # | 정우 패턴 | 내 module_c 적용 |
|---|---|---|
| 1 | README + DECISIONS + src/data/tests | ✅ 동일 구조 |
| 2 | ADR 형식 (상황→대안→근거→한계→시연가치) | ✅ D9-D21 모두 ADR |
| 3 | 함수당 평균 9 tests | 목표 70+ tests / 8 함수 = 평균 8.75 |
| 4 | `_base()` fixture 패턴 | 동일 — `module_c/tests/fixtures.py` |
| 5 | [검증] D{n} reference + [회귀] 출력 기준선 분리 | ✅ |
| 6 | pydantic v2 + Field(..., description=...) | ✅ |
| 7 | data_sources / limitations dict 자동 출력 | ✅ LEVResult 필수 |
| 8 | 5/5 진짜 데이터 — placeholder 발견 즉시 정정 | 메뉴얼 11정정 매핑 완료 |
| 9 | UTF-8 BOM 없는 encoding (Windows cp949 회피) | ✅ PYTHONIOENCODING=utf-8 |
| 10 | docstring Examples 섹션 | ✅ 모든 public 함수 |
| 11 | diagnose/ 폴더 — 학습 기록 보관 | `module_c/src/diagnose/` 동일 |
| 12 | type hint 모든 함수 | ✅ mypy clean |
| 13 | from_X / @classmethod 헬퍼 | LEVResult.from_lev_core_dict 등 |
| 14 | Optional[X] = None default | ✅ 옵션 P2 |
| 15 | Literal["A","B"] 명시 | ✅ scenario, ownership, slope_class, tier |

---

## 6. Day-by-Day 액션 (Day 6 → Day 31, W5 끝)

### W2 잔여 — Day 6-7 (5/20-5/21)

#### Day 6 (5/20, 화)
**오전 (3h)**
- [ ] data.go.kr 회원가입 + 4 fileData API 활용신청 (NFI 미신청 — 통합용이라 보류)
  - **임산물소득조사 (3044575)** ⭐ — D-C-2 데이터
  - 산림청 산림자원통계 OpenAPI (15080832) — 보조
  - 한국거래소 배출권 (15094805) — 보조 (정우 키로도 가능)
  - 임상도 (3045619) — 보류 (통합용)
- [ ] VWorld 인증키 발급 (즉시 승인)
- [ ] 산림청 「2023 임산물 생산조사」 PDF 다운로드 (kfri.go.kr → 통합자료실 → 통계자료)
- [ ] 산림청 「2025 산림보조사업 지침」 PDF 다운로드

**오후 (3h)**
- [ ] `shared/test_schemas.py` 15 tests 작성 — LEVResult/ComputeLEVRequest/DraftPlanCard
- [ ] 정우 `test_cost_function.py` 패턴 모방 (`_base()` fixture, [검증]·[회귀] 분리)
- [ ] PR 1 본문 작성

**저녁 (1h)**
- [ ] STATUS.md 갱신 — Day 6 완료 + Day 7 plan

#### Day 7 (5/21, 수)
**오전 (3h)**
- [ ] 정우 repo collaborator 추가 요청 또는 fork 결정
- [ ] PR 1 (shared/schemas.py + test_schemas.py) 발송
- [ ] PR 1 review 응답 + merge 대기

**오후 (3h)**
- [ ] `module_c/data/raw/hwp/hwp_decay_2021.json` 작성 (IPCC + 국립산림과학원)
- [ ] `module_c/src/hwp_decay.py` 함수 작성 (수식 + tests 시작)

**저녁 (1h)**
- [ ] 산림학자 deliberation 결과 적용 — demo polygon 4개 정의 (보은 30/35/50, 진안 25), SI 정정

---

### W3 — Day 8-14 (5/22-5/28) — module_c 결정론 v1 + 데이터 구축

#### Day 8 (목)
- [ ] PR 1 merge 확인. local `shared/schemas.py` 갱신.
- [ ] `module_c/src/grade_distribution.py` — Strategy 패턴 + HeuristicGD
- [ ] (정우에게) `module_bd/src/grade_dist.py` 분리 PR 제안 메시지

#### Day 9 (금)
- [ ] `module_c/src/lev_core.py` — Faustmann-Hartman 단일 시나리오 결정론
- [ ] `module_c/src/demo_parcels.py` — 4 demo polygon 정의
- [ ] 정우 `growth_predict()` 호출하여 `module_c/data/processed/demo_parcels.json` 생성

#### Day 10 (토) — 작업일
- [ ] `module_c/tests/fixtures.py` — `_base()`, `_base_50y_pine()` 등 fixture
- [ ] `module_c/tests/test_scenarios.py` 12 tests
- [ ] `module_c/tests/test_grade_distribution.py` 6 tests

#### Day 11 (일) — 작업일
- [ ] `module_c/src/compute_lev.py` v1 — 결정론 dispatch
- [ ] `module_c/tests/test_compute_lev.py` 15 tests
- [ ] `module_c/notebooks/01_lev_derivation.ipynb` — 손계산 검증

#### Day 12 (월)
- [ ] PR 2 (module_c 첫 commit + 결정론 v1) 발송
- [ ] `module_c/data/raw/ntfp/forest_byproduct_income_2023.json` 작성 시작
- [ ] 충북농업기술원 보은지소 연락 (이메일/전화) — 보은 특화 임산물 데이터 요청

#### Day 13 (화)
- [ ] PR 2 review 응답 + 수정
- [ ] `module_c/src/ntfp_income.py` 함수 작성
- [ ] `module_c/tests/test_ntfp.py` 5 tests

#### Day 14 (수)
- [ ] PR 2 merge 확인
- [ ] `module_c/src/lhs_sampling.py` — scipy.stats.qmc wrap
- [ ] `module_c/src/monte_carlo.py` 작성 시작

---

### W4 — Day 15-21 (5/29-6/4) — Monte Carlo + Pareto

#### Day 15 (목)
- [ ] `module_c/src/monte_carlo.py` 완성 — Lognormal 가격, Triangular AGB·할인율
- [ ] `module_c/tests/test_monte_carlo.py` 10 tests (수렴, antithetic 등)

#### Day 16 (금)
- [ ] `module_c/src/climate_multiplier.py` — SSP 보정
- [ ] `module_c/data/raw/climate/climate_multipliers_2020.json` (임종환 2020)
- [ ] `module_c/tests/test_climate.py` 6 tests

#### Day 17 (토)
- [ ] `module_c/src/uncertainty.py` — tier 자동 판정
- [ ] `module_c/tests/test_uncertainty.py` 4 tests
- [ ] `module_c/notebooks/02_mc_stability.ipynb` — 수렴 그래프

#### Day 18 (일)
- [ ] PR 3 (Monte Carlo + LHS + HWP + 기후) 발송
- [ ] `module_c/src/pareto.py` — Plotly Pareto front
- [ ] `module_c/src/kau_breakeven.py`

#### Day 19 (월)
- [ ] PR 3 review 응답
- [ ] `module_c/src/recommend.py` — Sharpe-like + user preference
- [ ] `module_c/tests/test_recommend.py` 8 tests

#### Day 20 (화)
- [ ] `module_c/src/subsidies.py` + `module_c/data/raw/subsidies/forestry_subsidies_2025.json`
- [ ] `module_c/src/offset_eligibility.py` — 8 사업유형 룰베이스 (룰베이스 부분)
- [ ] `module_c/data/raw/offset_eligibility/eligibility_rules_2024.json` 작성

#### Day 21 (수)
- [ ] 정우 `carbon_chunks.jsonl` 281 청크 검색 함수 작성 (RAG 보완 부분)
- [ ] `module_c/tests/test_offset.py` 10 tests

---

### W5 — Day 22-28 (6/5-6/11) — DraftPlanCard + api_server.py 통합

#### Day 22 (목)
- [ ] `module_c/src/draft_plan.py` — DraftPlanCard 생성 + 이중 표현
- [ ] `module_c/tests/test_draft_plan.py` 10 tests

#### Day 23 (금)
- [ ] `module_c/notebooks/03_pareto_demo.ipynb` — 4 demo × Pareto
- [ ] PR 4 (Pareto + recommend + DraftPlanCard + NTFP + 8 offset types) 발송

#### Day 24-25 (토-일)
- [ ] PR 4 review 응답 + 수정
- [ ] `module_c/data/raw/offset_eligibility/` 룰 정밀화 (정우 RAG 281 청크 활용)
- [ ] `module_c/notebooks/04_full_demo.ipynb` — 4 demo × 6 scenario × MC × Pareto end-to-end

#### Day 26 (월)
- [ ] PR 4 merge 확인
- [ ] api_server.py 의 scenarios=None 교체 PR 작성 시작

#### Day 27 (화)
- [ ] PR 5 (api_server.py 통합) 발송 — 단 30+50 줄, 작은 PR
- [ ] forest_state ↔ StandStateEstimate 매핑 헬퍼

#### Day 28 (수) — **W5 끝 = module_c 코드 완성 마일스톤** 🎯
- [ ] PR 5 merge 확인
- [ ] pytest module_c/tests/ 70+ green 최종 확인
- [ ] STATUS.md 갱신 — "module_c 코드 작업 완료"
- [ ] W6 (검증 + 논문) 준비

---

## 7. 위험 + 대응

| # | 위험 | 확률 | 영향 | 대응 |
|---|---|---|---|---|
| R1 | 정우 PR 1 review 5+ 일 지연 | 30% | 중 | local 작업 `from shared.schemas_proposed import` 임시, merge 후 swap |
| R2 | 정우가 `estimate_grade_dist` 분리 PR 거부 | 20% | 낮 | 함수 코드 module_c 에 복사 + 출처 주석 명시 |
| R3 | KOFPI Q4 2025 가격이 향후 분기 갱신되어 D6 reference 깨짐 | 50% | 낮 | tests 의 reference 값을 `tolerance=5%` 로 |
| R4 | 충북농기원 보은지소 연락 실패 → 보은 NTFP 데이터 없음 | 40% | 중 | 산림청 임산물생산조사 도 단위 + ±20% 추정 |
| R5 | 임종환 2020 SSP multiplier 데이터 미공개 | 30% | 중 | IPCC AR6 기본값 사용 + 한국 적용 한계 limitations 명시 |
| R6 | MC 수렴 안 됨 (std > 5%) | 30% | 중 | LHS 권장 (단순 MC 3-7%, LHS 1-2% std) |
| R7 | 정우 main 에 conflict 발생 (정우 1주 push 30+) | 50% | 낮 | 각 PR 작은 사이즈 유지 (200-500 lines), rebase 빠르게 |
| R8 | 6/26 마감 전 산림학자 W4 Weibull fit 못 끝남 | 70% | 낮 | HeuristicGD 그대로 유지 (Strategy 패턴 덕에 swap 무손실) |
| R9 | api_server.py 의 mock_module_a 와 내 demo PNU 불일치 | 30% | 중 | demo PNU 의 앞 2자리 = 정우 REGION_PROFILES 키와 맞춤 (보은 = "43") |
| R10 | shared/schemas.py 의 LEVResult 가 정우 W4 grade_distribution_trajectory 와 충돌 | 20% | 낮 | grade_distribution_T (LEVResult) 와 trajectory (GrowthForecast) 분리 |

---

## 8. 완료 조건 (W5 끝, 2026-06-11)

다음 모두 충족 시 module_c 코드 작업 완료:

- [ ] 정우 repo `main` 에 module_c/ 디렉토리 merge
- [ ] PR 1-5 모두 merge
- [ ] `pytest module_c/tests/` 70+ green
- [ ] 4 demo polygon × 6 scenario × MC 1000 = 24 cell 모두 동작
- [ ] `pytest shared/test_schemas.py` 15+ green
- [ ] `api_server.py` 의 `/analyze` endpoint 가 module_c 결과 반환
- [ ] `api_server.py` 의 `/compute_lev` endpoint 정상 동작
- [ ] DECISIONS.md D9-D21 ADR 13개 완성
- [ ] notebooks/01-04 모두 실행 가능
- [ ] `module_c/data/raw/` 5 종 데이터 모두 다운로드 완료
- [ ] 정우 patterns 100% 모방 체크리스트 15/15 통과

→ W6-7 은 케이스 스터디 + 논문 + 발표만. 코드 변경 0.

---

## 9. 즉시 (Day 5 종료 ~Day 6 오전)

지금 끊김 없이 할 것:

1. **이 문서 (10_module_c_focus.md) 확정** → 사용자 검토
2. `module_c/BUILDPLAN.md` 생성 (이 문서의 module_c 한정 축약, 정우 PR 동행용)
3. `STATUS.md` 갱신 — Day 5 완료 + Day 6-31 매트릭스
4. Day 6 오전 액션 4개 정리

---

## 변경 이력
- 2026-05-19 Day 5 (저녁) — 사용자 정정 ("module_c 만, 통합 나중") 반영하여 9 섹션 종합 빌드 플랜 작성
