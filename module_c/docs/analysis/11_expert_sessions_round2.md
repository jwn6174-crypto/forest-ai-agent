# 추가 전문가 deliberation Round 2 (3 세션)

> 2026-05-20 D22·D23 학술 발견 후 진행한 round 2 deliberation.
> 페르소나: 위성/원격탐사 학자, 영세 사유림 산주, 산림경제·정책 통합자.

**일자**: 2026-05-20 Day 6 저녁
**선행**: round 1 5 페르소나 (산림학자/경제학자/정책학자/경영자/AI) — `07_expert_sessions.md`

---

## 0. 핵심 메시지 3개 (round 2 종합)

| 페르소나 | 핵심 메시지 1줄 |
|---|---|
| 위성/원격탐사 학자 | **+103% 차이는 underestimation 이 아니라 자연성장 vs 경영후 측정의 모집단 차이**. GEDI+S2 triangulation Plan B |
| 영세 사유림 산주 | **숫자 하나 크게**, 나머지는 접어두고, 다음 행동은 *사람 이름·전화·대본*까지 손에 쥐어줘야 산주가 움직임 |
| 통합자 | "Faustmann-Hartman 한국 변형으로 포착한 **KAU 시장 변곡점**" — 발표 통합 타이틀 |

---

## 1. 위성/원격탐사 학자 답변

### 1.1 NFI direct lookup vs 위성 모델 — 영세림 적합성
영세 polygon (1-2ha) 에서 위성 RF/XGBoost 가 *더 위험*. Sentinel-2 10m 픽셀 기준 1ha = 100 픽셀이지만 가장자리 mixed pixel + 인접 spillover 30-40%. RF saturation (>150 Mg/ha 에서 NDVI/SAR 포화). **NFI lookup (임상도 + 영급/우점수종 stratified mean) = IPCC Tier 2 표준** — Avitabile et al. (2016) 도 소면적 plot-based stratification 우위 인정.

### 1.2 +103% 차이 — 위성 시각 해석
**가설 (b) 경영 후 측정** 압도적 가능성. 인증사업 320 tCO₂/ha/30yr 는 *간벌·시비·천연갱신 보완 후 실측 DBH 기반*, Module C 는 *yield table 기반 자연 성장*. Sentinel-2 NDVI 시계열로 검증: 인증사업지가 일반 임분 대비 NDVI peak +5-10%·빠른 회복 → **서로 다른 모집단 비교** (underestimation 아님).

### 1.3 보은 산외면 오대리 GEDI 검증
GEDI 51.6°N 까지 cover → 36.58°N 보은 궤도 내. 한국 위도 footprint 1-3/ha → **25.6ha 25-75 shots**. L2A/L4A footprint-level 직접 추출하면 carbonregistry 320 tCO₂/ha 비교 가능. 단 GEDI 2019-2023 데이터 → *current stock* 만, 30년 누적 미관측 → biomass 차이 (사업지 vs 대조군) 우회.

### 1.4 NDII/NDVI 시계열로 벌채 여부 검증
**매우 robust 가능**. Sentinel-2 (2017-) NDVI/NDII 월별 시계열에서 벌채 시 NDVI 0.8 → 0.2 급락 + 회복 6-10년. Hansen GFC·RADD alert 동일. **인증사업 4 polygon 의 2017-2026 NDVI 평탄/상승 → 벌채 없음 = 인증 유효성 입증** — *위성 모델 없이 시계열만으로*. **발표 가장 강력한 카드**.

### 1.5 위험 + Plan B
reviewer 공격 거의 확실 ("왜 위성 안 썼나"). **Plan B = NFI baseline + GEDI L4A footprint sliced + Sentinel-2 NDVI 시계열 triangulation**. 희도 1주 안에 GEDI Python (h5py + earthaccess) + S2 NDVI (GEE) 추가 가능. Framing: "Module C = 경영 의사결정용 보수적 추정, GEDI/S2 = 검증 레이어".

**핵심 메시지**: +103% 는 underestimation 이 아니라 모집단 차이. GEDI+S2 시계열 triangulation Plan B 로 reviewer 공격 차단.

---

## 2. 영세 사유림 산주 답변

### 2.1 "1,400만원 + 최악 -300만원 손실" — 인지
1,400만원 보면 "오, 좀 되네" 싶다가 -300만원 보면 헷갈림. **"잘되면 1,400만원, 못되면 본전 깎임 — 보통 800만원쯤" 자연어로 풀어주기**. 숫자 두 개 색깔 (빨강·파랑) + 큰 글자.

### 2.2 6 시나리오 한 화면 — 정보 과부하
**6개 너무 많음**. 산주는 "그래서 뭐 하라는 거요?" 가 제일 궁금. **추천 1개 위에 큼지막하게, 나머지는 "다른 방법도 있어요" 접어두기**. 발표용: 카드 1장 "권장: 10년 후 벌채 — 약 1,200만원". 비교는 자녀가 펼쳐서.

### 2.3 next_actions 구체화 (D20) 검증
전화번호만으론 그날 안 감. **카카오톡 + 사람 이름 + 멘트 대본**:
> "○○님, 보은조합 김주임 010-XXXX, '산주님 NPV 자료 보고 왔다'고 하시면 됩니다"

또는 자녀 핸드폰 "예약 신청" 버튼. 임야도·등기부 "이거랑 이거 챙기세요" 사진.

### 2.4 신뢰도 "낮음" — 인지
"낮음" 한 단어로는 "에이, 못 믿겠네" 하고 덮어버림. **이유 + 다음 행동 같이**:
> "현장 조사 안 해서 ±30% 차이 가능, 조합 가서 확인 권장"

### 2.5 정직성 vs 인지 — 레이어 분리
**앞면 큰 숫자 1개, 뒷면(펼치기) 범위·tier**. 학술 정직은 PDF, 산주 화면은 "잘되면/보통/못되면" 3줄.

**핵심 메시지**: 숫자 하나 크게, 나머지는 접어두고, 다음 행동은 사람 이름·전화·대본까지 손에 쥐어줘야 산주가 움직임.

---

## 3. 산림경제·정책 통합자 답변

### 3.1 학술 발견 priority — D23 > D22
**D23 (KAU+126%·WTA 돌파) 강한 주장**. D22 는 "누가 맞는가" 방어 부담 큼. D23 은 *시장 데이터 자체가 말하는 변곡점* — 산림청·임업진흥원 *immediate relevance* (지금 행동해야 할 정책 타이밍). Framing: "Faustmann LEV 가 16개월 전엔 임업 손해, 지금은 흑자 — 한국 산림경제 tipping point 를 모델로 포착".

### 3.2 5분 7슬라이드 발표 구조 ⭐ 채택
1. **Title** + 한 줄 메시지
2. **Problem**: WTA hurdle 미돌파 시대의 한국 임업
3. **Method**: Faustmann-Hartman 한국 변형 + 5+1 학자 deliberation
4. **Finding A**: D23 KAU 변곡점 시연 (live dashboard) ⭐ 핵심 narrative
5. **Finding B**: D22 인증-모델 +103% gap
6. **Validation**: NFI direct lookup + 129 tests + Module A 미시작 framing
7. **Conclusion** + 정책 제언

### 3.3 학부생 점수 잃기 쉬운 3차원
1. **데이터 진정성** (carbonregistry·KAU 출처 명시 + 재현가능성)
2. **정책 적합성** (모델 결과 → 산림기본계획·탄소중립 연계)
3. **시연 UX** (수범 module_e 5분 내 한 번 막히면 신뢰 붕괴 — 백업 영상 필수)

모델 완성도는 129 tests 로 이미 방어됨.

### 3.4 Module A 미시작 framing
**약점 인정 (10초)** + **학술 기여 강조**:
> "위성 기반 AGB 추정은 향후 과제 — 본 연구는 NFI 7차 plot-level 직접 lookup 으로
> 위성 추정 오차 (±15-30%) 우회. 한국 NFI 의 plot 정밀도 활용 = methodological conservative choice."

= deliberate methodological decision 으로 재framing.

### 3.5 통합 메시지 (발표 첫 슬라이드 title)
> **"Faustmann-Hartman 한국 변형으로 포착한 KAU 시장 변곡점**:
> 5+1 학자 deliberation 기반 산림탄소 정책 의사결정 프레임워크"

---

## 4. Round 2 의 코드·문서 반영

| 영역 | Round 2 권고 → 반영 |
|---|---|
| **GEDI+S2 triangulation Plan B** | W4-5 에 `module_c/scripts/gedi_l4a_validation.py` 추가 (선택, 위험 회피) |
| **NDVI 시계열 검증** | `notebooks/04_ndvi_timeseries.py` 추가 (선택, "발표 가장 강력한 카드") |
| **DraftPlanCard 단순화** | `draft_plan.py` 갱신 — 추천 1개 큼지막 + "다른 방법도 있어요" 접기 |
| **카카오톡 + 멘트 대본** | `recommend.py` next_actions 갱신 — 사람 이름·전화·대본 |
| **D23 우선 → 발표** | 슬라이드 4 핵심 narrative + Title "KAU 시장 변곡점" |
| **5분 7슬라이드 구조** | `_workspace/slides/v1.md` (W7) |
| **백업 영상** | W7 마지막 작업 — 데모 영상 녹화 |

---

## 5. 8 전문가 deliberation 종합 (round 1 + 2)

| # | 페르소나 | 핵심 기여 |
|---|---|---|
| 1 | 산림학자 | Weibull-2P + SI ±2 + 송이/표고 분리 + SSP multiplier |
| 2 | 산림경제학자 | Lognormal 가격 + HWP 30년 + WTA 161원 발견 + 이중 표현 |
| 3 | 산림정책학자 | 룰베이스+RAG hybrid + 노령림 모순 학술 기여 + 협력 framing |
| 4 | 경영자 (실무) | 간벌+10년 시나리오 + KOSIS 폐기 + 전화·URL 박기 + 모달 polygon |
| 5 | AI/ML 엔지니어 | LHS + Strategy 패턴 + uncertainty tier + api_server BackgroundTasks |
| 6 | **위성/원격탐사** | NDVI 시계열 = 발표 카드 + GEDI+S2 triangulation Plan B |
| 7 | **영세 산주** | 숫자 1개 큼지막 + 카카오톡 멘트 대본 + 펼치기 분리 |
| 8 | **통합자** | D23 우선 + "KAU 변곡점" 타이틀 + 5분 7슬라이드 구조 |

---

## 변경 이력
- 2026-05-20 Day 6 저녁 — Round 2 3 페르소나 deliberation 완료
