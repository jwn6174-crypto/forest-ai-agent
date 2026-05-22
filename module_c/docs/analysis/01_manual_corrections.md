# 메뉴얼 정정 종합 — 11 항목

> 기반채팅의 4 메뉴얼 (Manual 01-04) + master_design 을 작성할 때
> 정우가 module_bd 를 실제로 만들면서 발견한 정정 항목들.
>
> 이 정정 자체를 **논문 Methods 의 학술 기여**로 변환한다.

**작성일**: 2026-05-19 (Day 5)
**근거**: `기반채팅/05_module_c_work_standard.html` §02 "우리 메뉴얼 정정 종합표 (11항목)"
**검증**: 정우 repo `module_bd/DECISIONS.md` D1-D8

---

## 영향 분류

| 카테고리 | 항목 수 | 영향 |
|---|---|---|
| 위치·명칭 정정 | 4 (#1-4) | 코드 import 경로, 법령 정식명 |
| placeholder → 진짜 데이터 | 4 (#5-8) | NPV 정확도 크게 개선 |
| 구조 정정 | 3 (#9-11) | RAG 코퍼스 범위, 임산물 출처, compute_lev import |

---

## 위치·명칭 정정 (4항)

### #1. schemas.py 위치
- **Manual 01 §7.2** : `forest_agent/schemas.py`
- **정우 실제** : `shared/schemas.py`
- **이유** : 모든 모듈이 공유하는 인터페이스 계약은 단일 모듈 하위가 아니라
  최상위 `shared/` 에 두는 게 직관적. 정우 D4 채택.
- **action** : 내 코드에서 `from shared.schemas import ...` 로 통일.

### #2. 수종 정식명
- **Manual 02/03 본문** : "강원소나무"
- **정우 실제** : "강원지방소나무"
- **이유** : 산림자원법 시행규칙 별표 3 / 임분수확표 / 국립산림과학원 모두
  *강원지방소나무*. "강원소나무"는 통칭. 법령 매칭과 데이터셋 join 시 정식명 필수.
- **action** : 내 코드/문서 모두 강원지방소나무. 같이 *중부지방소나무* 도 별도 카테고리.

### #3. ownership 한국어
- **Manual 03 §8.1 RotationRule** : `ownership="general"`
- **정우 실제** : `ownership="사유림"` (Literal["사유림","국유림","공유림"])
- **이유** : 별표 3 자체가 사유림/국유림/공유림 한국어 컬럼. JSON 룰베이스 키도 한국어.
- **action** : `LEVResult.feasibility` 검증 시 `rotation_age(species, "사유림")` 호출.

### #4. CostFunction 입출력 분리
- **Manual 03 §8.1** : `class CostFunction(BaseModel): ...` (단일 모델)
- **정우 실제** : `CostInput` (입력) + `CostBreakdown` (출력) 분리
- **이유** : 가이드의 CostFunction 명세는 *함수 입력 변수* 모델로 모호. 정우 D4 가
  명시적으로 입력과 출력을 분리해 IDE 자동완성과 검증을 동시에 제공.
- **action** : `compute_lev()` 내부에서 `cost_function(...)` 호출 결과를
  `CostBreakdown` 으로 받아 `LEVResult.cost_breakdown` 에 dict 형태로 저장.

---

## Placeholder → 진짜 데이터 (4항)

### #5. 집재 단가 (skidding)
- **메뉴얼** : `skidding_cost_per_m3_km = 3,500원` (선형 단가 모델)
- **정우 실제 (KOFPI Q4 2025 p.44)** :
  - 0-1km : 9,300원/m³
  - 1-2km : 16,400원/m³
  - 2-4km+ : 18,400원/m³
- **영향** : 비용 3-6배 증가. 가이드의 *선형* 모델은 KOFPI 의 *구간형* 표와 정합 안 됨.
- **action** : `compute_lev()` 에서 `cost_function(skidding_distance_m=...)` 호출하면
  자동 정정됨 (정우 D3 함수 호출). 따로 처리 불필요.

### #6. 운반 단가 (transport)
- **메뉴얼** : `transport_cost_per_m3_km = 1,200원` (선형)
- **정우 실제 (KOFPI Q4 2025 p.43)** :
  - 0-50km : 14,600원/m³
  - 50-100km : 17,500원/m³
  - 100-150km : 25,200원/m³
  - ... 300km+ : 36,200원/m³
- **영향** : 비용 12-30배 증가. 충북 보은 → 서울 시장 (~150km) 25,200원/m³.
- **action** : 동일 — `cost_function(distance_to_road_km=15)` 자동 호출.

### #7. 묘목 단가 (regen)
- **메뉴얼** : `regen 묘목 = 800원/본` (추정)
- **정우 실제 (산림청 2025 시행령 16조, 15수종)** :
  - 강원지방소나무 : 422원/본 (-47%)
  - 잣나무 : 530원/본 (-34%)
  - 낙엽송 : 714원/본 (-11%)
  - 백합나무 : 1,219원/본 (+52%)
  - 평균 : 약 550원/본
- **영향** : 수종별 ±50%. regen 항목이 총 비용의 ~30% 차지 → 총비용 -8.5%.
- **action** : `cost_function(species="강원지방소나무", ...)` 시그니처에 species 추가됨 (정우 D6).

### #8. 탄소 흡수율
- **메뉴얼** : "임의 가정" (수치 없음)
- **정우 실제 (국립산림과학원 2003 개발 / 2013·2024 개정, 3,212 표본 × 40년)** :
  - 강원지방소나무 30년 : 10.77 tCO₂/ha/yr (피크)
  - 50년 : 4.92 tCO₂/ha/yr (피크의 46%)
  - 60년+ : 외삽 (warning 명시)
- **영향** : Faustmann-Hartman 의 `∫ p_C(t) · ΔC(t) · e^(-rt) dt` 항이 학술적으로 valid 해짐.
- **action** : `growth_predict(...)` 결과 dict 의 `carbon_uptake_rate` 사용 (정우 D5).

---

## 구조 정정 (3항)

### #9. 산림탄소상쇄 PDF 범위
- **메뉴얼 (Manual 03 §6.4)** : 6 PDF (식생복구·산림경영·재조림·신규조림·BCDM·산지전용)
- **정우 실제 (D7, 2025.1.2 기준)** : 11 PDF · 8 사업유형 + 3 보조
  - 8 사업유형 : 신규조림·재조림 통합, 벌기령 연장 산림경영, 식생복구, 목제품 이용,
    산림바이오매스, 수종 갱신, 산불피해지 조림, 산지전용 억제
  - 3 보조 : 운영지침, 산림조사 가이드라인, 통합 가이드북
  - 출력 : `carbon_chunks.jsonl` 281 청크
- **이유** : 가이드 작성 시점 6 PDF 였으나 2025.1.2 기준 8 사업유형으로 개정.
  BCDM 은 각 방법론 PDF 내부로 통합됨.
- **action** : `draft_plan.py` 의 `offset_citations` 필드에 정우의 281 청크 metadata 사용.
  수범 module_e 가 embedding 후 RAG 검색.

### #10. 임산물 소득
- **메뉴얼 (Manual 03 §3.2)** : "임가경제·임산물 200만원/ha" 가정 (출처 없음)
- **정우 실제** : 아직 미작성 (Day 4+ 우선순위 #2 로 명시됨)
- **action** : 내가 module_c 의 시나리오 S5 (임산물 병행) 에서
  - **단기** : 200만원/ha mock 사용하되 *mock 명시* (limitations 필드)
  - **중기** : KOSIS 임산물소득조사 OpenAPI 직접 호출 (data.go.kr 3044575)
  - **출처** : 표고 ha당 소득 (1,109 임가 평균), 산양삼, 산나물 별 카테고리

### #11. compute_lev 의 정우 함수 import
- **메뉴얼 (Manual 01 §4.2)** : 가이드 함수를 mock 으로 import
  ```python
  from module_bd import growth_predict, market_snapshot, cost_function, rotation_age
  ```
- **정우 실제** : 정확한 경로는
  ```python
  from module_bd.src.growth_predict import growth_predict, lookup_volume
  from module_bd.src.market_snapshot import market_snapshot
  from module_bd.src.cost_function import cost_function
  from module_bd.src.legal_rotation import rotation_age
  from module_bd.src.kau_api import fetch_kau_price
  ```
- **action** : `compute_lev.py` 의 첫 줄에 정확한 import 7개 작성.
  순환 import 방지를 위해 `shared.schemas` 만 위에서 import.

---

## 정정의 학술적 의미

| 메뉴얼 vs 실제 차이 | 1줄 시연 문구 |
|---|---|
| skidding 3,500 → 9,300원 | "KOFPI 분기보고 직접 추출로 가이드 placeholder 3배 정정" |
| transport 1,200 → 14,600원 | "거리별 구간 단가 → 30km 운반비 30배 차이" |
| seedling 800 → 422원 (소나무) | "산림청 2025 공식 묘목가 적용으로 regen -21%" |
| 탄소율 임의 → 10.77 (소나무 30y) | "국립산림과학원 3,212 표본 통합으로 carbon revenue 실측" |
| 6 PDF → 8 사업유형 RAG | "2025.1.2 개정 반영 281 청크 RAG" |

→ 논문 §3 (Data) 또는 §4 (Methods) 에 "Manual placeholder vs Implemented" 표로 삽입.
→ Discussion 에 "정직한 데이터 정정이 학술 기여" 1단락.

---

## 변경 이력
- 2026-05-19 Day 5 — 11 항목 정리, 기반채팅 05 + 정우 DECISIONS.md 교차 검증
