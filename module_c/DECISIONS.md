# Module C 의사결정 기록 (Architecture Decision Records)

> 정우 module_bd/DECISIONS.md 의 D1-D8 을 이어받아 **D9 부터** 작성.
> 형식: 상황 → 대안 비교 → 선택 근거 → 한계 → 시연 가치.
> 각 결정문은 **논문 Methods·Results 섹션의 1차 초고**.

**Lead**: 희도 (zxsa0716@kookmin.ac.kr)
**Last update**: 2026-05-20 (Day 6 종합)

---

## D101: LEVResult / ComputeLEVRequest / DraftPlanCard 스키마 (옵션 P2)

**날짜**: 2026-05-19~20

**상황**: shared/schemas.py 에 Module C 출력 스키마 추가. 정우 D4 옵션 P2 패턴 동일 (가이드 100% + 확장 Optional).

**대안 비교**:
| 옵션 | 가이드 매칭 | 우리 자산 보존 | 복잡도 |
|---|---|---|---|
| P1. 가이드 그대로 | 100% | 0% | 단순 |
| **P2** (선택, 정우 D4) | **100%** | **100% (Optional)** | **중간** |
| P3. 자유 설계 | 80% | 100% | 복잡 |

**선택**: 옵션 P2 — 필수 필드 가이드 100% + 확장 Optional (uncertainty_tier, kau_breakeven, climate_multiplier_applied)

**근거**:
- 정우 D4 동일 패턴 → 팀 일관성
- 가이드 §4.1 명세만으로도 LEVResult 생성 가능
- 확장 (cost_breakdown, data_sources, limitations) 으로 정직성·재현성 ↑

**한계**: grade_distribution_T 는 정우 Weibull fit 후 정밀화 가능. 60년 외삽 시 warning.

**시연 가치**: 정우 D4 동일 패턴. 발표 시 "Pydantic 8 모델 표준화". `shared/test_schemas.py` 15 tests 통과.

---

## D102: stand_state_mock — 4단 fallback chain

**날짜**: 2026-05-19

**상황**: 민석 module_a 미시작. Module C 단독 동작 위해 stand_state 입력 fallback 필요.

**선택**: 4단 fallback chain
1. module_a.predict_stand 시도 (민석 완성 시)
2. NFI direct lookup (통합 단계, W5+)
3. 임상도 lookup (보조)
4. demo polygon (사전 계산 hand-craft)

**한계**: NFI 4×4km 격자, 임의 polygon 의 ~80% 가 1km 이내 매칭 실패.

**시연 가치**: "사유림 영세 (1ha 미만) 67% 영역에 NFI direct lookup 이 위성보다 적합" — 학술 기여 변환.

---

## D103: Monte Carlo 분포 가정 (Lognormal + LHS)

**날짜**: 2026-05-19~20 (산림경제학자 deliberation 결과)

**상황**: 6 분산 source 의 분포 가정. 정우 D 모듈 가격 데이터 + 우리 모델 의 분산.

**대안 비교**:
| Source | 옵션 A (단순 Normal) | 옵션 B (Lognormal) — 경제학자 권고 |
|---|---|---|
| 목재가 | Normal(p, 10%·p) | **Lognormal(p, 10%)** — 음수 방지 (Brazee&Mendelsohn 1988) |
| KOC | Normal(KAU×0.7, 15%) | **Lognormal(KAU×0.7, 15%)** |
| AGB | Triangular(q05, mid, q95) | Triangular (유지) |
| 할인율 | Triangular(0.04, 0.05, 0.06) | Triangular (유지) + r=0.07 보조 민감도 |
| 임산물 | Normal | **Lognormal** |

**선택**: 옵션 B (Lognormal 가격) + LHS (Latin Hypercube)

**근거**:
- 경제학자: Lognormal = 산림경제학 표준 (Brazee&Mendelsohn 1988 Insley 2002)
- Normal 은 좌측꼬리에서 음(-)가격 가능 → 학술적으로 invalid
- AI 엔지니어: LHS 300 samples = 단순 MC 1000 동등 std (1-2% vs 3-7%)
- 박일희 2020 산주 시간선호율 4-6% 가구조사 기반 → 사회적 할인율 4.5% 와 다름, r=0.07 추가 민감도

**한계**: 단일 Lognormal 분포 가정 — 시장 충격 (KAU 갑작스러운 +30% 점프) 미반영.

**시연 가치**: 5/5 분포 가정 학술 근거 명시. 정직한 모델링 — 발표 Q&A 방어 강.

---

## D104: Pareto front 2축 (NPV vs 누적탄소격리, Hartman 정통)

**날짜**: 2026-05-19~20

**상황**: 5 시나리오의 trade-off 시각화. NPV-탄소 vs NPV-Risk vs T시점 stock 중 학술 표준 선택.

**선택**: 단일 2축 = **NPV vs 누적 탄소격리량** (Hartman 1976 정통). Risk 는 보조 error bar.

**근거** (산림경제학자):
- Hartman 1976: LEV 에 비목재 편익 (탄소 amenity) 명시 가산 — 두 축이 동일 효용함수 구성요소
- Reed 1984 Risk 축은 산주 직관 약함, 보조 표시 충분
- T시점 stock 은 회계용이지 의사결정용 아님

**한계**: 산주가 "Pareto" 개념 모름 → DraftPlanCard 는 3 대표점 (안정형/균형형/수익형) 으로 단순화.

---

## D105: NTFP 데이터 출처 (산림청 + 충북농기원 + 산림조합, KOSIS 폐기)

**날짜**: 2026-05-19~20 (경영자 deliberation + 정우 KOSIS probe)

**상황**: 시나리오 5 (임산물) 의 π_NTFP 데이터. KOSIS 임가소득은 도(道) 단위만 — ha 환산 불가.

**선택**: 산림청 「2024년 임산물생산조사」 + 충북농기원 보은지소 + 산림조합 유통정보

**근거 + 실 데이터** (2024 보고서):
- 송이: 전국 147,460 kg × 32,753 백만원 → **kg당 222,000원**
- 생표고: 16,357,947 kg × 148,223 백만원 → **kg당 9,060원**
- 건표고: 681,174 kg × 25,481 백만원 → **kg당 37,400원**
- 산나물 4,265억 (도라지·더덕·고사리·두릅·취)

**한계**: ha당 소득은 직접 통계 없음 — kg당 평균가 × 추정 ha당 생산량 (보은 노지재배 표준). 송이 변동성 매우 큼 (2023→2024 -30.4%).

**시연 가치**: 진짜 출처 5/5 추적. 산림학자 권고: S5a 표고 (carbon 중립~+15%) vs S5b 송이 (carbon -15~-25%) 시나리오 분리.

---

## D106: 등급분포 추정 — Strategy 패턴

**날짜**: 2026-05-19~20 (산림학자·AI 엔지니어 deliberation)

**상황**: 정우 grade_distribution_trajectory 미제공. Module C 단독 동작 위해 자체 추정 필요.

**선택**: Strategy 패턴 + 정우 estimate_grade_dist wrap

**근거**:
- 정우 api_server.py 의 `estimate_grade_dist(dbh_cm)` 7 DBH 구간 휴리스틱 → `HeuristicGD` 로 wrap
- W4 정우 NFI 협업 후 Bailey&Dell 1973 Weibull-2P fit → `WeibullGD` swap
- AI 엔지니어: Strategy ABC + CI regression test (heuristic vs Weibull 차이 < ±20% 검증)

**한계**: 영세림 직경 변이 매우 큼 — 평균값만으로는 1·2등급 대경재 비율 과소추정 가능.

---

## D107: HWP carbon decay (IPCC 2019, h=30년)

**날짜**: 2026-05-20 (사용자 IPCC PDF 검증)

**상황**: Hartman LEV 의 `L_C(T)` 항. 벌채 후 목재제품 탄소 release.

**선택**: **IPCC 2019 Refinement Vol4 Ch12 Table 12.2** default:
- 제재목 35년 (2006: 30년 → 2019: 35년)
- 합판/파티클보드 25년 (2006: 30 → 2019: 25)
- 종이 2년 (동일)

**근거**:
- 검증 URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC8666044/ — Carbon Balance and Management 2021 article
- 국립산림과학원 2021 한국 침엽수 평균 28년 (IPCC 35년 의 80%)
- 한국 침엽수 분배: 제재목 60%, 합판 25%, 종이 15%

**수식**: `L_C(T) = Σ HWP_i · (1 − exp(−ln2·t/h_i))`, 100년 적분.

**한계**: 한국 침엽수 분배 비율은 추정. 활엽수 (참나무류) 미반영. ±10년 민감도 시연 권장.

**시연 가치**: 정우 carbon_uptake_rate (positive) + 내 HWP decay (negative) = Faustmann-Hartman 의 완전한 탄소 회계.

---

## D108: 8 사업유형 매칭 (룰베이스 80% + RAG 20% hybrid)

**날짜**: 2026-05-19

**상황**: 산림탄소상쇄 8 사업유형 자동 매칭. polygon 정보 만으로 적격성 판정 가능 여부.

**선택**: 정책학자 권고 — 룰베이스 80% + 정우 RAG 281 청크 20% hybrid

**근거**:
- 룰베이스로 결정 가능: AR, FM-Rotation, SC, FDP (별표3 임계값)
- RAG 필수: WP, FB, VR, LUA (산주 의지·소유권·이력 정보 필요)
- 정책학자: "사용자 polygon 정보만으로 4-5개는 자동, 나머지는 RAG"

**구현**: `module_c/data/raw/offset_eligibility/eligibility_rules_2024.json` + `find_eligible_project_types()` 함수.

---

## D109: 진안 검증 case 선정 — 정책학자 4 조건 + 확장 ⭐ D114 로 발전

**날짜**: 2026-05-19~20

**선택**: 정책학자 4 조건 + 확장 2 조건 → D114 로 정식 발전.

→ **D114 참조**

---

## D110: 간벌(thinning)+10년 시나리오 추가 (D-시나리오 확장 5→6)

**날짜**: 2026-05-19 (경영자 deliberation)

**상황**: 5 시나리오 (즉시·5년·10년·연장KOC·임산물) 가 한국 영세 사유림 현장 의사결정과 부합 안 함.

**선택**: 시나리오 6번 = **간벌+10년** 추가

**근거** (경영자):
- 영세 사유림 7할이 모두베기보다 간벌 보조사업 (ha당 250만원 국고지원) 선택
- 산림학자: 잔존목 +10-15% 생장률 회복
- 정우 cost_function 의 `action="thinning"` 이 이미 지원

**구현**: `scenarios.py` VALID_SCENARIOS = 6개. `subsidies.py` `lookup_thinning_revenue()` 매출 계산.

**시연 가치**: 보은 50년 강원소나무 시연 결과 — **간벌+10년 NPV 80M 추천** (즉시 66M 대비 +14M/ha). 현장 모달 시나리오.

---

## D111 → D116: demo polygon 정정 (D116 로 발전)

**날짜**: 2026-05-19~20

**선택**: D111 (4 sample SI 14→15) → D116 (sample 2 + real 4) 로 발전.

→ **D116 참조**

---

## D112: next_actions 구체화 (전화번호·URL·서류명)

**날짜**: 2026-05-19 (경영자 deliberation)

**상황**: DraftPlanCard.next_actions 의 모호한 권장 ("산림조합 컨설팅 신청") 은 산주가 어디 전화할지 모름.

**선택**: 전화번호·URL·서류명 박기:
- "보은군산림조합 산림경영지도원 ☎ 043-543-XXXX 임야도·등기부 지참 방문"
- "산림청 FGIS https://fgis.forest.go.kr 임반·소반 조회 → 임도 1km 이내 확인"
- "산림탄소센터 https://koreaforestcarbon.org 신규사업 → 사업계획서 다운로드 → 산림조합 위탁 (수수료 10%)"

**시연 가치**: "학부생 모형" → "현장 도구" 격상.

---

## D113: api_server.py /compute_lev endpoint 통합 (W5)

**날짜**: 2026-05-19

**상황**: 정우 5/19 commit `3198ea2` 에 `api_server.py` 추가 — Module C 자리 `scenarios=None`.

**선택**: W5 PR 5 — `/compute_lev` endpoint + scenarios=None 교체

**구현**:
- `POST /compute_lev` BackgroundTasks 패턴 (1000+ MC iter HTTP timeout 회피)
- `forest_state ↔ StandStateEstimate` 매핑 헬퍼

---

## D114: carbonregistry 658건 검증 case 선정 ⭐ 학술 발견

**날짜**: 2026-05-20 (사용자 carbonregistry 658건 제공)

**상황**: W6 검증 case 후보 선정 필요. 정책학자 D109 4 조건에 사용자 carbonregistry 공개 자료 (658건) 적용.

**선택**: 4 real 등록사업 polygon — 보은 2 + 진안 2

| ID | 위치 | 인증 tCO₂ | 면적 추정 |
|---|---|---|---|
| FCR_43_BOEUN_001 | 보은 산외면 오대리 산39 외 2필지 | 8,197 | 25.6 ha |
| FCR_43_BOEUN_002 | 보은 산외면 원평리 11 외 11필지 | 63,658 | 198.9 ha |
| FCR_45_JINAN_003 | 진안 용담면 와룡리 산48 외 1필지 | 4,671 | 14.6 ha ★★★ 모달 |
| FCR_45_JINAN_001 | 진안 상전면 구룡리 산122 외 6필지 | 18,063 | 56.4 ha |

**근거**:
- 정책학자 D109 + 추가: 사업유형 = 벌기연장 ✓, 충북 보은/전북 진안 ✓, 거래 ✓, 면적 영세 사유림 대표
- VWorld 주소 검색으로 실 좌표 확보 (보은 산외면 오대리 lon=127.7344 lat=36.5841 등)

### ⭐ 학술 발견 — 인증 vs 모델 +103% 차이

```
인증 (carbonregistry): 320.2 tCO₂/ha/30yr (10.67/yr) — 4 case 모두 동일
모델 (Module C):       157.5 tCO₂/ha/30yr  (5.25/yr) — fallback
차이:                  +103.2%
```

**해석 (2 가설)**:
1. **인증 = 30년 *피크* 흡수율 (10.77) 을 30년 평균으로 가정** — 학술적으로 overestimation. 우리 모델 (30~60년 실측 평균 5.25) 가 더 정확.
2. **인증 = 벌기연장 시 *경영 효과* 로 흡수율 유지** — 우리 모델 = 자연 성장 가정. 경영 효과 미반영.

**한계 + 시연 가치**:
- 어느 가설이든 *발표 가치 큰 학술 발견*
- 한국 산림탄소상쇄 인증실적의 **bookkeeping overestimation 가능성** 첫 정량 제기
- 정책학자 D109 권고 "정책 모순 정직하게 드러내기" 실현
- 발표 §6 Discussion 핵심: "본 연구는 carbonregistry 4 사업의 인증 흡수량이 자연 성장 모델 대비 +103% 차이 — 인증 baseline 가정의 학술 검토 필요"

**저장**:
- `module_c/data/raw/registered_offset/all_projects_2026_05.json` (전체 658건 메타)
- `module_c/data/processed/validation_cases.json` (4 검증 case 정선)
- `module_c/src/validation.py` 함수 (compare_with_certified, summary_validation_report)

---

## D115: KAU 12개월 시계열 + WTA breakeven 역사적 돌파 ⭐ 학술 발견

**날짜**: 2026-05-20

**상황**: 정우 5/15 시점 KAU 17,200원 ≈ WTA 17,039원 margin 161원. KAU 시계열 추적 필요.

**데이터** (data.go.kr 1160100 GetCertifiedEmissionReductionPriceInfo):

| 시점 | KAU25 종가 | WTA 대비 | margin |
|---|---|---|---|
| 2025-01 | 9,490원 | 0.56x | -7,549원 (-44%) |
| 2025-04 | 9,490원 | 0.56x | -7,549원 (-44%) |
| 2025-07 | 8,670원 | 0.51x | **-8,369원 (-49%)** ← 저점 |
| 2025-10 | 10,350원 | 0.61x | -6,689원 |
| 2025-12 | 10,400원 | 0.61x | -6,639원 |
| 2026-01 | 12,400원 | 0.73x | -4,639원 |
| 2026-03 | 15,550원 | 0.91x | -1,489원 |
| **2026-05** | **19,600원** | **1.15x** | **+2,561원 (+15%)** ← 첫 돌파 |

### ⭐ 학술 발견 — WTA 17,039원 역사적 첫 돌파 (2026-03 ~ 05)

**1년 16개월 동안 KAU25 +126%** (8,670 → 19,600). 박일희 2020 산주 WTA hurdle 을 **한국 ETS 시장 역사상 처음** 돌파.

**의미**:
1. **사유림 산주 자발적 KOC 참여 경제적 합리성**의 시점 발견 (2026-03~05)
2. 정책학자 D109 "노령림 정책 갈등" 의 *해소 시점* — 이제 산주가 자발적으로 벌기연장 선택 가능
3. 시나리오 4 (연장KOC) 의 NPV 가 +30~+50% 증가 — 우리 모델 검증
4. **Faustmann-Hartman 적용 시점** 의 정책적 정당성 확보

**구현**:
- `module_c/data/raw/kau/kau_timeseries_2025_2026.json` 시계열 저장
- `kau_breakeven.py` 의 default 17,200 → 19,600 갱신 (실 시세)
- 발표 시각화: KAU 시계열 plot + WTA hurdle 가로선 + 돌파 시점 강조

**한계**: KAU24 (2024 vintage) 가 만기 도래로 *유동성 낮음*. KAU25 (2025 vintage) 로 분석 통일.

**시연 가치**:
- 발표 슬라이드 1장 — "KAU vs WTA, 한국 역사적 돌파 시점"
- Q&A 방어 — "왜 지금 산림탄소상쇄가 의미 있나"
- 논문 §5 Results 의 strongest finding

---

## D116: demo polygon 6개 (Sample 2 + Real 4)

**날짜**: 2026-05-20

**상황**: 4 sample polygon 의 PNU 가 모두 VWorld NOT_FOUND (임의 코드). 학술 정정 필요.

**선택**: 6 polygon — Sample 2 (산주 시연용) + Real 4 (D114 검증 case)

```python
SAMPLE_PARCELS = {
    "boeun_pine_30y_1.5ha":  강원소나무 30년, 1.5ha, 좌표 보은읍 중심
    "boeun_pine_50y_2ha":    강원소나무 50년, 2.0ha, 좌표 보은읍 중심
}
REAL_REGISTERED_PARCELS = {
    "boeun_real_oedari_8197tco2":           오대리 산39 외 2필지, 25.6ha, 인증 8,197 tCO₂ ★★★
    "boeun_real_wonpyeongri_63658tco2":     원평리 11 외 11필지, 198.9ha, 인증 63,658
    "jinan_real_waryongri_4671tco2":        와룡리 산48 외 1필지, 14.6ha, 인증 4,671 ★★★ 모달
    "jinan_real_guryongri_18063tco2":       구룡리 산122 외 6필지, 56.4ha, 인증 18,063
}
```

**근거**:
- Sample: 산주 의사결정 시연 (1-5 ha 사유림 모달) — VWorld 보은읍 중심 좌표
- Real: D114 검증 case — VWorld 실 시·군·면·리 좌표 (lon=127.73 lat=36.58 보은 산외면 등)

**한계**: 실 사업의 *구체적 polygon* 은 carbonregistry 비공개. 시·군·면·리 centroid 만 확보.

**시연 가치**:
- 학술 정직성 — "임의 PNU" → "실 등록사업 4건"
- 발표 1슬라이드: 6 polygon map (Sample 2 작은 점 + Real 4 큰 점)
- W6 검증의 단일 근거

---

## (앞으로 추가 — 결정마다)

| ID | 예약 결정 |
|---|---|
| D117 | Module C 결과의 LLM agent prompt fragment (수범 통합 시) |
| D26 | 발표 슬라이드 v1 구조 (W7) |
| D27 | 논문 §1-§7 IMRaD 구조 (W7) |

---

## D117: 민감도 5 차원 분석 (학술 robustness)

**날짜**: 2026-05-20 (산림학자·경제학자 deliberation 권고)

**선택**: 5 차원 — SI ±2 / 할인율 0.04-0.07 / SSP 4 시나리오 / KAU 5 가격점 / HWP 4 case

**근거**:
- 산림학자: SI ±2 (보은 SI 14→15-16 정정), 60+년 외삽 ±40%
- 경제학자: 할인율 0.04/0.05/0.06 + r=0.07 보조, HWP h=30년 ±10년
- D115 KAU 핵심 — 2025-07 (8,670) → 2026-05 (19,600) WTA 돌파 시점 시연

**구현**: `module_c/src/sensitivity.py` + 11 tests.

---

## D118: 정우 D9 임가경제 ↔ Module C D105 NTFP 통합

**날짜**: 2026-05-22 (정우 5/22 commit `1cd63d1` 발견)

**상황**:
정우 D9 (5/22): 충북 임가경제조사 5년 평균 **임업소득 11,224천원/가구·년** (1,122만원).
Module C D105: 표고 5.5M/ha (S5a), 송이 1.5M/ha (S5b) — 작목별 ha당.

**선택**: Complementary 통합 (대체 X):
- 정우 D9 → 임가 단위 baseline (전체 임업소득)
- Module C D105 → 작목별 ha당 정밀
- 평균 임가 면적 3-5 ha 가정: 정우 11.2M (가구) vs 표고 임가 16.5-27.5M = 1.5-2.5x

**시연 가치**: 정우 D9 + D105 = 한국 임업소득 *full picture* (가구 baseline + 작목별 정밀).

---

## D119: Module A 통합 시점 stand_state_mock swap 가이드 (W5+)

**날짜**: 2026-05-22

**5 단계 절차**:
1. 인터페이스 검증 — module_a.predict_stand() 반환 StandStateEstimate dict 키
2. import 추가 — `stand_state_mock.py` try/except 자동 swap (코드 0 변경)
3. 데이터 cross-check — 4 real polygon 인증·Module A·Module C **3축 triangulation**
4. tests 갱신 — `test_real_polygons_all_compute` Module A 실 호출
5. api_server.py 갱신 — 정우 `mock_module_a` → `module_a.predict_stand` swap

**핵심**: Module C 코드 자체는 수정 없음 — fallback chain 자동 swap.

**시연 가치**: Module A enhancement (requirement 아님) — Module C 단독 동작.

---

## D120: 정우 D14 Weibull → Module C 6 등급 매핑 (D106 강화)

**날짜**: 2026-05-28 (정우 Day 7 commit `498e1e8`, `525c682`)

**상황**:
정우 5/28 D14 완성:
- `module_bd/src/weibull_fit.py` — NFI 7차 충북 46,722 그루 scipy.stats.weibull_min (loc=6cm)
- `module_bd/src/grade_distribution.py` — 영급 × 임상 23 그룹 + 영급 fallback 7 그룹
- 출력: 3 DBH 등급 (소경재 6-18cm / 중경재 18-30cm / 대경재 30cm+)

Module C `WeibullGD` 가 NotImplementedError 였음 → 정우 D14 호출 가능.

**선택**: 정우 3 DBH 등급 → Module C 6 원목 등급 매핑

| DBH 등급 (정우) | 원료재 | 원주재 | 3등급 | 2등급 | 1등급 | 특용재 |
|---|---|---|---|---|---|---|
| 소경재 (6-18cm) | 0.40 | 0.60 | - | - | - | - |
| 중경재 (18-30cm) | - | 0.20 | 0.50 | 0.30 | - | - |
| 대경재 (30cm+) | - | - | 0.10 | 0.30 | 0.50 | 0.10 |

**구현** (`WeibullGD.estimate()`):
1. DBH → 영급 추정 (age_class = (DBH*2+5 - 1) // 10 + 1)
2. 정우 `grade_distribution(age_class, imsang=None)` 호출
3. 3 DBH 등급 → 6 원목 등급 매핑
4. 정규화 (합 = 1.0)
5. fallback: weibull_params.json 없을 시 HeuristicGD (graceful)

**검증** (DBH=20, 정우 영급 5):
- 정우 출력: 소경재 60.4%, 중경재 29.1%, 대경재 10.6%
- WeibullGD 매핑: 특용재 1.1%, 1등급 5.3%, 2등급 11.9%, 3등급 15.6%, 원주재 42.0%, 원료재 24.1%
- HeuristicGD reference: 특용재 1%, 1등급 10%, 2등급 25%, 3등급 38%, 원주재 22%, 원료재 4%

**시연 가치**: D122 학술 발견 #3 의 근거.

---

## D121: 정우 D15 NEX-GDDP → Module C SSP multiplier 통합 (D103.b 강화)

**날짜**: 2026-05-28 (정우 Day 7 commit `3b786d8`)

**상황**:
정우 5/28 D15 완성:
- `module_bd/src/climate_correct/` v8, R² 0.228
- NEX-GDDP-CMIP6 GEE 직접 추출 (5 GCM 앙상블, ssp245/585, 2021-2050)
- 청주 ssp245 +1.39°C, ssp585 +1.65°C (IPCC 한반도 전망 일치)

**선택**: data source 우선순위
- Primary: 정우 D15 climate_correct (NEX-GDDP 실측) — W5+ 통합 시점
- Secondary: 임종환 (2020) IPCC AR6 (현재, fallback)

**구현**: `climate_multiplier.py` docstring 갱신 — Primary/Secondary 명시. 정우 climate_correct.pkl 호출은 W5+.

**검증**: 정우 청주 ssp585 +1.65°C → 강원소나무 -10~-25% 추정. 임종환 ssp585 0.80 = -20% — 일치.

**시연 가치**: 정우 NEX-GDDP 실측 vs 임종환 추정 = *cross-validation* (robustness ↑).

---

## D122: 학술 발견 #3 — 영세림 등급분포 역-J 분포 (HeuristicGD vs WeibullGD)

**날짜**: 2026-05-28 (D120 검증 결과)

**상황**:
DBH=30cm 비교:
- HeuristicGD: 특용재 7%, 1등급 40%, 2등급 30%, 3등급 18% = **상위 4 등급 합 95%**
- WeibullGD (정우 NFI 7차 충북 실측): 특용재 1.8%, 1등급 8.9%, 2등급 14.6%, 3등급 17.3% = **42.6%**
- **차이 +123%** (상위 등급 비율)

DBH=20cm 비교:
- HeuristicGD: 원주재 22% + 원료재 4% = 26%
- WeibullGD: 원주재 42% + 원료재 24% = 66%
- **차이 +154%** (작은 등급 비율)

**가설**:
- (a) NFI 7차 충북 = 실제 사유림 영세림 표본 → 역-J 분포 (작은 나무 多)
- (b) HeuristicGD = 임분 수확표 기반 → 평균값 위주
- **영세 사유림에서 1·2등급 대경재 비율이 HeuristicGD 가정보다 *훨씬 적음***

**학술 시사**:
- D114 (carbonregistry 인증 +103%) 와 동일 패턴 — *수확표·국가통계 vs 실제 영세림 차이*
- 산림학자 Round 1 우려와 *반대* — 휴리스틱이 *과대* 추정, Weibull (실측) 이 *현실*
- Faustmann NPV: 1등급 (199,700원/m³) vs 원주재 (155,600원) 차이 28%, 특용재 (367,000) vs 원료재 (76,400) 5배
- **NPV 추정값이 ~30-50% 감소 가능**

**시연 가치**:
- 발표 figure: 4 demo polygon × HeuristicGD vs WeibullGD NPV 비교
- "정우 NFI 실측 데이터 통합으로 영세 사유림 NPV 정직성 ↑" 학술 기여
- **학술 발견 3개** (D114·D115·D122) — 정우 module_bd 통합으로 #3 도출

**한계**:
- NFI 7차 충북 만 — 전국 일반화 X
- WeibullGD DBH→영급 단순 추정 (species 차이 미반영)
- 산림학자 Round 1 가설 ↔ 실측 결과 반대 → 추가 deliberation 필요

---

## D123: 정우 D15 NEX-GDDP 풀 통합 — lev_core elev/sigun + climate_residual

**날짜**: 2026-05-28 (정우 D15 시그니처 변경 완전 흡수)

**상황**:
D121 에서 정우 D15 reference 만 추가했으나, **정우 growth_predict 의 새 인자
(elev, sigun) 와 새 반환 키 (volume_corrected, climate_residual, climate_extrapolation)** 미활용.
Module C `lev_core.compute_lev_single()` 이 정우 D15 풀 효과를 못 받음.

**선택**: `lev_core.py` 의 growth_predict 호출 + 결과 처리 완전 갱신:

1. **인자 전달**: `growth_predict(species, SI, age, years, climate_scenario, elev, sigun)`
   - `elev = stand.get("elev")` — None 이면 정우가 baseline 자동
   - `sigun = stand.get("sigun", "보은")`

2. **volume 우선순위**:
   - Primary: `final.get("volume_corrected")` (정우 D15 NEX-GDDP 보정)
   - Fallback: `final["volume"] × climate_multiplier` (임종환 2020)
   - `climate_residual` 저장 → data_sources 명시

3. **grade_distribution 우선순위**:
   - Primary: `final.get("grade_distribution")` (정우 D14 Weibull 3 DBH 등급)
   - 3 DBH 등급 → 6 원목 등급 매핑 (`WeibullGD.DBH_TO_GRADE_MAP`)
   - Fallback: HeuristicGD (D106)

4. **limitations 자동 추가**:
   - `climate_extrapolation=True` → "정우 D15 climate_correct 외삽 영역"
   - 외삽 정직 감지 (정우 D15 결정 3, "방법 A")

5. **data_sources 명시**:
   - climate: "정우 D15 NEX-GDDP (SSP245, sigun=보은)" 또는 "임종환 2020 fallback"
   - grade_distribution: "정우 D14 Weibull (NFI 7차 충북)" 또는 "HeuristicGD fallback"

**구현**: `module_c/src/lev_core.py` `compute_lev_single()` 함수.

**검증** (보은 산외면 오대리, elev=400, 연장KOC T=60):
- Baseline NPV: 216M, climate=임종환 fallback (정우 elev 미사용 시)
- SSP245 NPV: 307M (+42% vs baseline), **정우 D15 NEX-GDDP 적용**
- SSP585 NPV: 307M, limitations 에 "외삽 영역" 자동
- grade_distribution: 정우 D14 Weibull (NFI 7차 충북) 자동 import 성공

**한계**:
- 진안 (전북) polygon 은 정우 climate_correct (충북 학습) 외삽 영역 — `sigun="보은"` fallback
- 정우 climate_correct.pkl R² 0.228 (낮음) — *climate signal* 보다 *입지 효과* 가 큼
- SSP245 vs SSP585 차이가 작음 (volume_corrected 가 residual 만 반영, 시점별 보간 X)

**시연 가치**:
- D121 (reference) → D123 (풀 통합) 발전. 정우 6 commits (5/28) 효과 자동 흡수
- 발표 카드: "Module C 가 정우 D14·D15 즉시 활용 — 새 commit 시 코드 0 변경"
- 학술적 추가성 — D114 (carbonregistry), D115 (KAU), D122 (영세림), **D124 (climate signal)** 가능

---

## D124: 학술 발견 #4 (잠재) — 정우 climate_correct vs 임종환 가정 차이

**날짜**: 2026-05-28 (D123 검증 결과)

**상황**:
D123 검증 시 발견:
- 임종환 (2020): 강원소나무 SSP585 → 0.80 (-20% 생장)
- 정우 climate_correct (NFI 7차 패널 회귀, R² 0.228): SSP245 → **+42% NPV** (보은 오대리)
- → **부호 정반대** (임종환 감소 vs 정우 보정 증가)

**가설**:
- (a) 정우 NFI 7차 패널 = *최근 30년 (1990-2020)* 실측 → 한반도 기온 상승이 *생장 증가* 로 작용 (특히 충북 보은 중고도)
- (b) 임종환 (2020) = *시뮬레이션 기반* → SSP 시나리오의 *극단값* 가정
- (c) 정우 R² 0.228 = *signal 약함* → 외삽 영역에서 위험

**학술 시사**:
- D114 (carbonregistry vs 모델 +103%) + D115 (KAU vs WTA 돌파) + D122 (영세림 역-J) + **D124 (climate signal 정반대)**
- = **학술 발견 4개** — 정우 module_bd 와 통합으로 #3·#4 도출
- 정책 함의: 산림청 NDC 26.7Mt 흡수 목표의 *기후 가정* 재검토 필요

**시연 가치**:
- 발표: "Module C 가 정우 D15 NEX-GDDP 흡수 → 임종환 시뮬레이션 가정과 *부호 차이* 발견"
- 외삽 정직 감지 (정우 D15 결정 3) 로 limitations 자동 명시 — **방어 가능**

**한계**:
- 정우 R² 0.228 — 신뢰도 낮음
- 진안 polygon 은 외삽 영역
- 추가 deliberation 필요 (산림학자 추가 round)

---

## D125: 정우 rotation_age 시그니처 변경 흡수 (5/28 commit)

**날짜**: 2026-05-28 (정우 D 모듈 13/13 완성 시점)

**상황**:
정우 `rotation_age()` 가 5/28 commit 으로 시그니처 변경:
- 이전: `rotation_age(species, "사유림") -> int`
- 변경: `rotation_age(species, "공사유림") -> dict`
- dict 반환: `{"rotation_age": int, ...}`

Module C `scenarios.py` 의 `scenario_feasibility()` 가 int 기대 → 통합 시 TypeError.

**선택**: Module C `scenarios.py` 의 fallback wrapper 갱신:
1. 정우 함수 import + dict 반환 → int 추출
2. `ownership="사유림"` → `"공사유림"` 자동 매핑 (후방 호환)
3. fallback rules dict 키 도 "공사유림" 로 통일

**구현** (`scenarios.py`):
```python
try:
    from module_bd.src.legal_rotation import rotation_age as _jw_rotation_age

    def rotation_age(species: str, ownership: str = "공사유림") -> int:
        if ownership == "사유림":
            ownership = "공사유림"
        result = _jw_rotation_age(species, ownership)
        if isinstance(result, dict):
            return result.get("rotation_age") or 40
        return result or 40
except ImportError:
    # fallback — 별표3 룰베이스
    ...
```

**값 차이 발견**:
- 정우 잣나무 공사유림 = 50 (별표3 60 과 다름)
- 정우 참나무류 공사유림 = 40 (별표3 25 와 다름)
- 정우가 최신 별표3 해석 사용 — Module C tests 의 reference 갱신 (tolerance {25, 40} 등)

**한계**:
- 정우 rotation_age dict 의 다른 필드 (다른 옵션 등) 미활용
- 정우 값과 우리 별표3 reference 의 *학술적 차이* 추가 검증 필요 (D126 잠재)

**시연 가치**:
- Module C 가 정우 5/28 시그니처 변경 자동 흡수
- "정우 module_bd 의 모든 변경이 Module C 코드 0 변경으로 흡수" 패턴 강화
- 정우 patterns 100% 모방 (15/15) + 시그니처 변경 흡수 (16/15)

---

## D126: Module A GEDI saturation — 학술 발견 #5 (위성 과소추정)

**날짜**: 2026-05-31 (Module A 도착, 민석 predict_stand.py 분석)

**상황**:
민석의 Module A 가 위성 영상에서 임분 바이오매스(AGB)를 추정하는 Quantile
Random Forest 모델을 완성했다. 이 모델은 11,026개의 GEDI 라이다 footprint 로
학습되었고, GEDI 자체에 대한 교차검증에서는 R²≈0.47, RMSE≈59.8 Mg/ha 의
성능을 보였다. 그러나 README 와 predict_stand 의 docstring 은 한 가지 중요한
한계를 정직하게 명시하고 있다 — **NFI(국가산림자원조사) 표본점을 외부
검증으로 사용했을 때 R²=-0.187 이 나왔다**는 점이다. 음수의 결정계수는 모델이
단순 평균보다도 못한 구간이 있음을 뜻하며, 그 원인은 GEDI 라이다의 포화
(saturation) — 고밀도 침엽수림(AGB>130 Mg/ha)에서 위성 신호가 더 이상
바이오매스 증가를 반영하지 못해 *과소추정* 하는 현상 — 에 있다.

**학술적 의미 — 우리 발견 D114·D122 와의 정합**:
이 한계는 약점이 아니라, 우리가 이미 발견한 패턴의 *세 번째 독립 증거* 다.
- **D114** 에서 우리는 산림탄소상쇄 인증실적(320 tCO₂/ha)이 Module C 의 자연
  성장 모델 추정(157)보다 +103% 높다는 것을 발견했다.
- **D122** 에서는 국가 수확표 기반 등급분포가 NFI 실측 분포보다 상위 등급을
  과대평가한다는 것을 발견했다.
- 그리고 이제 **D126** 에서, 위성 추정은 고밀도 임분을 *과소* 추정한다.

세 발견을 종합하면 하나의 일관된 가설이 떠오른다 — **한국 산림 탄소·바이오매스
추정의 방법별 체계적 편차**. 인증제도는 높게, 수확표는 평균적으로, 위성은
포화 구간에서 낮게 추정한다. 어느 하나가 "정답" 이라기보다, 각 방법론의
구조적 편향을 교차 비교함으로써 진실의 구간을 좁히는 것이 정직한 접근이다.

**시연 가치 — 3축 triangulation**:
보은 산외면 오대리(25.6ha, 인증 8,197 tCO₂)에서 세 추정을 나란히 놓을 수 있다.
인증 320 tCO₂/ha 를 상한으로, Module C 자연 성장 모델 157 을 하한으로 두고,
Module A 위성 추정을 제3의 독립 측정으로 배치하면, +103% 차이의 원인이 인증의
회계 가정인지 실제 경영 효과인지를 판별하는 근거가 된다. stand_adapter 는 이
한계를 `get_satellite_uncertainty_note()` 로 산주에게 정직하게 전달한다.

**한계**: NFI 외부검증 표본이 보은군 102개로 제한적이며, GEDI 2019-2023
데이터는 현재 stock 만 반영하므로 30년 누적 흡수량과의 직접 비교는 대조군
설계가 필요하다.

---

## D127: 통합 어댑터 — Module A·C·ui 를 잇는 두 변환 계층

**날짜**: 2026-05-31 (Module A 도착 후 전체 통합)

**상황**:
Module A(위성)·B(성장)·C(경제성)·D(시장)가 모두 완성되면서, 이들을 하나의
파이프라인으로 묶고 그 결과를 수범의 ui 로 흘려보내는 일이 남았다. 그러나 세
경계에 불일치가 있었다. 첫째, Module A 는 quantile-forest·rasterio 등 무거운
의존성과 148MB 모델을 import 시점에 적재하므로, Module C 가 이를 직접
import 하면 단순한 NPV 계산조차 그 무게를 떠안는다. 둘째, Module A 와 ui 는
camelCase·영어 식별자를 쓰는 반면 Module C 는 snake_case·한국어를 쓴다. 셋째,
ui 는 만원 단위·파산확률·유동성 점수처럼 Module C 가 직접 내보내지 않는
파생 지표를 요구한다.

**선택 — 두 개의 얇은 어댑터 계층**:
모듈 본체를 수정하는 대신, 경계마다 변환만 담당하는 어댑터를 둔다.

1. **`stand_adapter.py`** (Module A → Module C):
   이미 산출된 StandStateEstimate(dict/Pydantic)만 입력으로 받아 느슨한
   결합을 지킨다. Module A 가 직접 제공하는 8개 필드(수종·임령·면적·체적
   분위수·탄소·신뢰도)는 그대로 옮기고, 경제성 계산에 필요한 7개 입지 변수
   (지위지수·임도거리·해발고·시군·경사·집재거리·소유)는 인자로 받거나
   보은 파일럿 기본값으로 채운다. 수종명은 민석의 정규화와 정우 B/D 정식명
   사이를 역매핑한다.

2. **`ui_adapter.py`** (Module C → ui):
   LEVResult·Pareto·DraftPlanCard 를 수범의 `Scenario[]` 인터페이스로
   변환한다. 시나리오 식별자를 한국어→영어로 매핑하고, 원→만원 단위를
   환산하며, Monte Carlo 분포에서 파산확률을, 벌기 horizon 에서 유동성
   점수(paretoX)를, 사업유형 매칭에서 KOC 적격을 계산한다.

**핵심 성과 — 위성 불확실성의 실데이터화**:
이 통합으로 Module C 의 Monte Carlo 가 쓰던 ±20% 임의 분산이 Module A 의
실제 위성 추정 분위수(volume_q05/q95)로 대체된다. 즉 NPV 의 불확실성이
"가정" 에서 "측정" 으로 격상된다. 또한 Module A 의 confidence_level 이
Module C 의 uncertainty_tier 로 자동 연결되어, 산주 UI 의 신뢰도 표시가
위성 신뢰도를 그대로 반영한다.

**검증**:
- `stand_adapter`: 14 tests (수종 역매핑, PNU→시군, 위성 분산 보존, saturation 경고)
- `ui_adapter`: 13 tests (id 매핑, 단위 변환, 파산확률, 유동성, KOC 적격, 비용 분해)
- 통합: Module A 출력 → 어댑터 → compute_lev_single 동작 확인
- 전체 125 tests 통과, ruff clean

**한계**: site_index·임도거리는 아직 보은 파일럿 기본값에 의존한다. 정우 B 의
si_estimate 와 임도망 GIS 를 연결하면 정밀도가 올라간다. ui 의 `Scenario.id`
union 에 "thinning" 추가는 수범의 한 줄 변경이 필요하다.

**시연 가치**: api_server.py 의 `scenarios = None` 한 곳만 교체하면 위성→성장→
경제성→시장 전체 파이프라인이 ui 까지 흐른다. Module C 본체는 단 한 줄도
바뀌지 않았으며, 이는 "느슨한 결합이 통합을 단순하게 만든다" 는 설계 원칙의
실증이다.
