# Module C 빌드 플랜 (정우 PR 동행 문서)

> Module C 가 정우 module_bd 를 어떻게 호출하고, 자체 데이터를 어떻게 구축하며,
> 5 PR 순서로 정우 repo 에 합쳐지는지 설명. `_workspace/analysis/10_module_c_focus.md`
> 의 *공개 가능한 축약본*. 정우/수범/민석이 읽을 수 있는 톤.

**Lead**: 희도 (Module C + Lead)
**기간**: 2026-05-20 ~ 2026-06-11 (W2 후반 ~ W5 끝)
**최종 마감**: 2026-06-26 (공모전 발표)

---

## 1. Module C 책임 한 줄

```
StandStateEstimate (정우 module_a mock or 민석 위성) 입력
  → 6 시나리오 NPV/LEV (Monte Carlo 1000+ samples)
  → Pareto front (NPV vs 누적 탄소격리)
  → DraftPlanCard (산주 의사결정 카드)
```

---

## 2. 정우 module_bd 의존 (직접 import)

```python
from module_bd.src.growth_predict import growth_predict, lookup_volume
from module_bd.src.market_snapshot import market_snapshot
from module_bd.src.cost_function import cost_function
from module_bd.src.legal_rotation import rotation_age
from module_bd.src.kau_api import fetch_kau_price
from module_bd.src.legal_api import search_law
from shared.schemas import (
    GrowthForecast, MarketSnapshot, CostInput, CostBreakdown, RotationRule,
    LEVResult, ComputeLEVRequest, DraftPlanCard,  # ← module_c 가 추가 (D9 PR)
)
```

**정우 함수의 어떤 키를 사용하는지**: `_workspace/analysis/10_module_c_focus.md` §2.2 참조.

---

## 3. 5 PR 시퀀스

| PR | 범위 | 라인 수 | 날짜 | 의존 |
|---|---|---|---|---|
| **PR 1** | `shared/schemas.py` 에 LEVResult/ComputeLEVRequest/DraftPlanCard 추가 (D9) | +180 + tests 200 | 2026-05-21 | 없음 |
| **PR 2** | `module_c/` 첫 commit (scenarios + grade_dist + lev_core + 4 demo + tests) | ~990 | 2026-05-26 | PR 1 |
| **PR 3** | Monte Carlo + LHS + HWP decay + 기후 multiplier | ~680 | 2026-06-01 | PR 2 |
| **PR 4** | Pareto + recommend + DraftPlanCard + NTFP + 8 사업유형 | ~960 | 2026-06-05 | PR 3 |
| **PR 5** | `api_server.py` 의 scenarios=None 교체 + `/compute_lev` 엔드포인트 | ~80 | 2026-06-09 | PR 4 |

각 PR 은 정우 review 가능한 작은 사이즈 (200-1000 lines). 작은 단위로 자주.

---

## 4. 6 시나리오 정의

| 시나리오 | T | 비용 action | 탄소수익 | NTFP | 보조사업 매출 |
|---|---|---|---|---|---|
| 즉시 | age_now | clearcut | 0 | 0 | 갱신 4.5M/ha |
| 5년 | age_now+5 | clearcut (5년 후) | 5년치 (KOC>WTA 시) | 0 | 갱신 |
| 10년 | age_now+10 | clearcut (10년 후) | 10년치 | 0 | 갱신 |
| 연장KOC | max(legal+10, age+10) | clearcut (T년 후) | 매년 KOC | 0 | 없음 (벌채 안 함) |
| 임산물 (S5a 표고, S5b 송이 분리) | age_now+15 | clearcut + NTFP | 15년치 | 매년 0.3-8M/ha | 갱신 |
| **간벌+10년** | age_now+10 | **thinning (30-40%)** + 10년 후 잔존목 clearcut | 10년치 (잔존목) | 0 | **간벌 2.5M/ha + 갱신** |

**Why 간벌?** (D110) 영세 사유림 7할이 산림보조사업 (ha당 2.5M) 받고 잔존목 키우기. 정우 cost_function 의 `action="thinning"` 이 이미 지원.

---

## 5. Module C 만의 데이터 (data/raw/)

| 데이터 | 출처 | 용도 |
|---|---|---|
| HWP decay 룰 | IPCC 2019 + 국립산림과학원 2021 | L_C(T) 계산 |
| NTFP 소득 | 산림청 임산물생산조사 + 충북농기원 + 산림조합 (KOSIS 미제공) | 시나리오 S5 |
| 기후 multiplier | 임종환 (2020) 국립산림과학원 | SSP 보정 |
| 산림보조사업 단가 | 산림청 2025 지침 | 간벌·갱신 매출 |
| 8 사업유형 룰 | 산림청 운영지침 2024 + 정우 RAG hybrid | DraftPlanCard offset_citations |

---

## 6. 단위 테스트 (정우 패턴 모방)

- 함수당 평균 9 tests (정우 Day 4 기준)
- `_base()` fixture — 보은 50년 강원지방소나무 (벌기령 도달, 명확)
- [검증] D{n} reference + [회귀] 출력 기준선 분리
- 회계 항등식 자동 검증

**목표**: PR 4 merge 후 `pytest module_c/tests/` **70+ green**.

---

## 7. ADR 13개 (DECISIONS.md)

D9-D113 모두 ADR 형식 (상황 → 대안 비교 → 선택 + 근거 → 한계 → 시연 가치).

- D9 LEVResult 스키마 (옵션 P2)
- D102 stand_state mock fallback
- D103 MC 분포 (Lognormal 가격, Triangular AGB)
- D104 Pareto 2축 (NPV-누적탄소, Hartman 정통)
- D105 NTFP 데이터 출처 (산림청+충북농기원, KOSIS 폐기)
- D106 등급분포 Strategy (HeuristicGD → WeibullGD swap)
- D107 HWP decay h=30년 ±10
- D108 8 사업유형 룰베이스 80% + RAG 20%
- D109 진안 검증 case 선정
- D110 간벌+10년 시나리오 추가
- D111 demo polygon 4개 정정 + 추가
- D112 next_actions 구체화 (전화·URL·서류명)
- D113 api_server.py /compute_lev endpoint

---

## 8. 5 전문가 deliberation (D103-D113 근거)

산림학자 + 산림경제학자 + 산림정책학자 + 산림경영자(실무) + AI/ML 엔지니어
5명 전문가 세션 결과는 `_workspace/analysis/07_expert_sessions.md` 참조.

**핵심 통찰**:
- 경제학자: Lognormal 가격, Hartman 정통 Pareto, KAU breakeven 명시, 산주/정책 UI 분리
- 산림학자: Weibull-2P, SI ±2 민감도, 송이/표고 시나리오 분리, SSP multiplier
- 정책학자: 노령림 정책 모순 학술 기여, 룰베이스 80% + RAG 20% 하이브리드
- 경영자: 간벌 시나리오 추가, KOSIS 폐기, 전화·URL 박기, 모달 polygon
- AI: LHS, Strategy 패턴 fault tolerance, uncertainty tier 자동 판정

---

## 9. 정우 patterns 100% 모방 (체크리스트 15항)

자세한 매트릭스는 `_workspace/analysis/10_module_c_focus.md` §5 참조.

- ✅ README + DECISIONS + src/data/tests
- ✅ ADR 형식 결정문
- ✅ `_base()` fixture
- ✅ [검증]·[회귀] 분리
- ✅ 5/5 진짜 데이터 추적
- ✅ data_sources + limitations 자동 출력
- ✅ pydantic v2 + Literal[...]
- ✅ UTF-8 BOM 없는 encoding
- ✅ docstring Examples
- ✅ Optional default
- ✅ type hint
- ✅ diagnose/ 폴더 보존
- ✅ from_X 헬퍼
- ✅ 옵션 P2 (가이드 100% + 확장 Optional)
- ✅ 작은 PR (200-1000 lines)

---

## 10. 연락

- 희도 (Lead + Module C): zxsa0716@kookmin.ac.kr
- GitHub PR: jwn6174-crypto/forest-ai-agent
- NRF 과제: CLIM Lab (임철희 교수)
- 작업 워크스페이스 (개인): `E:\forest_ai\` (gitignore)
