# Q&A 예상 답변 — 발표 Q&A 방어 (Manual 01 §09)

> 공모전 발표 (2026-06-26) 의 Q&A 5-10분 동안 예상되는 질문 + 학술적 답변.
> 산림청·임업진흥원·학계 reviewer 시각 모두 커버.

**작성일**: 2026-05-20 Day 6
**근거**: Manual 01 §09 + 8 전문가 deliberation + D22·D23 학술 발견

---

## 🛡 Tier 1 — 가장 예상되는 질문 (방어 필수)

### Q1. "왜 위성 AGB 안 썼나? 산림 AI 면 위성이 핵심 아닌가?"

**답변** (위성 학자 Round 2 권고 — methodological choice framing):
> "본 연구는 의도적으로 NFI 7차 plot-level direct lookup 을 선택했습니다. 한국 영세
> 사유림 (평균 1-3 ha) 의 위성 RF/XGBoost 추정 오차 ±15-30% 보다, NFI 4×4 km 격자
> 표본점의 plot-level 측정값이 IPCC Tier 2 표준에 더 부합합니다 (Avitabile et al.
> 2016). 영세 polygon 에서는 Sentinel-2 mixed pixel 30-40%·SAR saturation 한계
> 가 *오히려 더 큰 위험*. 향후 GEDI L4A footprint + Sentinel-2 NDVI 시계열
> triangulation 은 검증 레이어로 통합 예정 (Plan B)."

### Q2. "Module C 모델 vs 인증사업 +103% 차이는 모델이 틀린 거 아닌가?"

**답변** (D22 + 위성 학자 Round 2):
> "두 가설 비교 결과 **모집단 차이** 가 압도적 가능성입니다. 인증사업 320 tCO₂/ha/30yr
> 는 *간벌·시비·천연갱신 보완 후 실측 DBH 기반* 이고, Module C 157 tCO₂/ha/30yr 는
> *yield table 기반 자연 성장 가정*. 따라서 underestimation 이 아니라 **두 다른
> 모집단의 비교**입니다. 오히려 이 +103% gap 자체가 학술 기여 — **한국 산림탄소상쇄
> 인증실적 baseline 가정의 검토 필요성을 첫 정량 제기**. 위성 학자 권고: Sentinel-2
> NDVI 시계열 (2017-2026) 로 인증사업지 4 polygon 의 *실제 벌채 여부* 검증 가능."

### Q3. "KAU 가격 변동이 큰데, 19,600원이 일시적이라면? 다시 WTA 밑으로 가면?"

**답변** (경제학자 + D23):
> "정당한 우려입니다. Module C 는 이 위험을 *명시적으로 반영* 합니다 —
> `kau_breakeven` 함수가 시나리오 4 (연장KOC) 의 KAU 임계가를 계산하고,
> `kau_breakeven_warning` 으로 산주에게 정직하게 표시. 예: 'KAU 19,600 → 16,300원
> 이하 시 LEV 음수 전환'. Monte Carlo 1000+ samples 에서 KAU 를 Lognormal(KAU,
> 15%) 로 sampling 해서 q05·q95 분포 모두 보여줍니다. 학술 정직: 점추정만 아니라
> *분포* 와 *민감도* 모두 시연."

### Q4. "민석이 Module A 0 commit 이면 시스템 작동 안 하지 않나?"

**답변** (Module A framing):
> "Module C 는 *단독 동작* 으로 설계됐습니다. `stand_state_mock.py` 의 4단 fallback
> chain — (1) module_a.predict_stand 시도, (2) NFI direct lookup, (3) 임상도 lookup,
> (4) demo polygon. 현재 4 demo polygon (보은·진안 carbonregistry 실 사업지) +
> 2 sample polygon 으로 발표 시연 100% 작동. 민석이 W5+ 에 시작하면 mode='auto'
> 자동 swap. Module C 의 핵심 가치 (Faustmann-Hartman LEV) 는 위성 무관."

### Q5. "산주가 6 시나리오 다 이해할 수 있나? UX 너무 복잡 아닌가?"

**답변** (Round 2 산주 권고):
> "Round 2 deliberation 에서 영세 산주 페르소나가 동일 지적. **3 레이어 분리** 로 해결:
> Tier 1 (산주 첫 인상) — 추천 1개 + natural_summary ('우리 산 → 솎아베기 + 10년.
> 잘되면 9,500만원, 보통 8,000만원'). Tier 2 (펼치기) — 다른 5 시나리오 + 근거 +
> 다음 액션. Tier 3 (정책담당관 부록) — q05-q95 분포 + Pareto front. 카카오톡
> 메시지 자동 생성으로 자녀에게 전송 가능."

---

## 🛡 Tier 2 — 학술 reviewer 질문 (대비)

### Q6. "Faustmann-Hartman 식의 어디까지 한국 변형 했나? Hartman 의 비목재 가치는?"

**답변**:
> "5+1 항 모두 한국 데이터로 instantiation:
> - p_g·v_g(T) ← KOFPI Q4 2025 7수종×6등급 (정우 D1)
> - p_C(t)·ΔC(t) ← KAU + 국립산림과학원 carbon_uptake 3,212표본 (정우 D5)
> - π_NTFP(t) ← 산림청 2024 임산물생산조사 (D13, S5a/S5b 분리)
> - Cost(T) ← 표준품셈 + KOFPI 5/5 진짜 (정우 D3·D6)
> - L_C(T) ← IPCC 2019 Refinement Vol4 Ch12 HWP (D15)
> - subsidy_revenue ← 산림청 2025 보조사업 (D18 간벌+10년 신규)
>
> Hartman 비목재 가치는 탄소 + 임산물 + 보조사업 3 항 통합. 한국 특수성:
> *KAU vs WTA hurdle* 의 thin market 임계값 명시 (경제학자 deliberation)."

### Q7. "Monte Carlo 1000 iter 면 std 가 얼마나? 수렴 보장은?"

**답변** (AI 엔지니어 + D11):
> "**LHS (Latin Hypercube Sampling, scipy.stats.qmc) 300 samples 로 단순 MC 1000
> 동등 정확도** 확보. 단순 MC std/median 3-7% → LHS 1-2%. 6 분산 source: AGB
> Triangular, 목재가 Lognormal (Brazee&Mendelsohn 1988 — Normal 은 음수 가능
> invalid), KOC Lognormal, NTFP Lognormal, 할인율 Triangular(0.04, 0.05, 0.06),
> 기후 multiplier Normal(species×SSP). `n_eff` 진단 (batched std/mean < 0.05)
> 게이트로 수렴 검증."

### Q8. "Lognormal vs Normal 가격 가정의 근거?"

**답변** (경제학자 deliberation):
> "Brazee & Mendelsohn (1988) Forest Science 가 산림경제학 표준 — Normal 분포는
> 좌측꼬리에서 *음수 가격* 가능 → 학술적으로 invalid. Lognormal 은 가격이 0 보다
> 큰 random variable 에 자연. Insley (2002) real options 산림 연구에서도 동일.
> KOC 도 마찬가지로 Lognormal(KAU×0.7, 15%)."

### Q9. "HWP half-life 35/25/2년의 한국 적용 타당성은?"

**답변** (D15):
> "IPCC 2019 Refinement Vol4 Ch12 Table 12.2 default 값 (PMC 8666044 검증). 한국
> 적용: 국립산림과학원 2021 보고서 침엽수 평균 28년 (IPCC 35년 의 80%) — 한국이
> 약간 짧음. 우리 모델은 IPCC default 사용 (보수적, 30년 ±10년 민감도 권장).
> 분배 비율 60/25/15 는 한국 침엽수 임산물 생산 통계 평균 — 활엽수 (참나무류)
> 별도 모델은 W4-5 작업."

### Q10. "8 전문가 deliberation 은 사용자가 임의로 만든 것 아닌가?"

**답변**:
> "사용자 선호 (multi-agent harness deliberation) 가 학술 방법론으로 적용된 사례.
> 각 페르소나는 *명시적 시각 + 한국 산림계 핵심 선행연구 인용* 으로 구조화 — 산림학자
> (강진택 2016 Weibull, 임종환 2020 SSP), 산림경제학자 (박일희 2020 WTA, Brazee &
> Mendelsohn 1988, Insley 2002), 산림정책학자 (산림청 운영지침 2024, NDC 2030),
> 산림경영자 (보은 산림조합 실무, 충북농기원), AI (IPCC 2019, LHS, Strategy 패턴),
> 위성 (Avitabile 2016, GEDI L4A spec), 산주 페르소나, 통합자. **각 전문가 응답이
> ADR D9-D24 로 추적** 됨."

### Q11. "carbonregistry 658건 중 4개만 검증? 표본 너무 적지 않나?"

**답변** (D22 + 정책학자):
> "658건 중 정책학자 D17 4 조건 필터 적용:
> (a) 사업유형 = 벌기령 연장 (한국 인증실적 99%)
> (b) 충북 보은 / 전북 진안 + 인접
> (c) 거래 (인증실적 정량 비교 가능)
> (d) 면적 영세 사유림 대표 (1-200ha)
>
> → 4 case 정선. **표본 적지만 4 case 모두 +103.1~103.3% 균일** — 통계적
> 추가 case 도 동일 결과 예상 가능. W6 에 658건 전체 분석으로 확장 (시간 허락 시)."

### Q12. "GEDI L4A 36.58°N 보은 cover 한다 했는데 footprint 밀도는?"

**답변** (위성 학자):
> "GEDI 51.6°N 까지 cover (보은 36.58°N 안전 범위). 한국 위도대 footprint 밀도
> 1-3 shot/ha → 25.6ha 보은 산외면 오대리 사업지 = 25-75 shots. L2A canopy
> height + L4A AGBD 직접 추출 가능. 다만 GEDI 2019-2023 데이터라 30년 누적
> 흡수량 직접 비교는 불가 → *current stock* 만 → 사업지 vs 대조군 비교 우회."

---

## 🛡 Tier 3 — 정책 reviewer 질문 (대비)

### Q13. "본 연구가 산림청·임업진흥원에 어떻게 기여하나? 정책 제언은?"

**답변** (정책학자 + 통합자):
> "3 정책 제언:
> 1. **산림청 산림탄소정책과**: 인증실적 baseline 가정 재검토 — D22 +103% 차이
>    검증 필요. NDVI 시계열 + GEDI L4A 로 인증사업 실측 검증 권장.
> 2. **임업진흥원 KOC센터**: 사유림 영세 산주 자발적 참여 — 2026-03~05 WTA 돌파
>    시점 (D23) 이 정책 적기. 신규 사업 신청 가이드 강화 권장.
> 3. **지역 산림조합**: Module C 의 산주 의사결정 보조도구 시범 배포 (오픈소스).
>
> '비판 아닌 협력 제안' framing — 정책학자 권고."

### Q14. "노령림 정책 갈등 (벌기연장 vs 벌채-재조림 회전) 어떻게 해결하나?"

**답변** (정책학자 + D23):
> "본 연구가 직접 해결책 제시 X — 오히려 정책 모순을 *정직하게 시각화*. 산림청
> 2050 탄소중립 전략은 영급 불균형 30년 이상 72% → '벌채 후 재조림 회전' 권장,
> 동시에 산림탄소상쇄 99% 가 '벌기연장' 으로 발생 (모순). Module C 는 5 시나리오
> 모두 NPV·탄소 trade-off 로 보여줌 — Pareto front 의 두 극단 (즉시벌채 vs
> 연장KOC) 이 정책 갈등의 정량 표현. **D23 KAU 시장 변곡점은 양 정책의 *경제적
> 조화 시점*** 발견 — 자발적 KOC 참여 가능해진 시점부터 산주 선택 자유 확보."

### Q15. "Module C 가 실제 산주에게 배포 가능한가?"

**답변** (Round 2 산주 + 경영자):
> "현재 발표 시연 수준 완성. 실 배포 위한 W7 이후 작업:
> 1. 카카오톡 챗봇 통합 (자녀 → 산주 메시지 자동)
> 2. 보은군청 산림과 베타 배포 제안서 (정책학자 권고)
> 3. 산림조합 산림경영지도원 교육 (3 대표점 카드 사용법)
>
> 학부생 작품의 한계 인정 + '의사결정 *보조도구* — 최종 결정은 산림조합·산주' framing."

---

## 🛡 Tier 4 — 트리키 질문 (예상 가능)

### Q16. "Claude AI 가 코드 다 짰는데 학술적 기여인가?"

**답변**:
> "AI 는 *도구* 입니다. 본 연구의 학술 기여는 (1) 8 전문가 deliberation 의 *학제적
> 방법론* 설계, (2) carbonregistry 658건 분석 결정 (D17 4 조건), (3) Faustmann-
> Hartman 한국 변형의 *수식·데이터 선택*, (4) D22·D23 학술 발견의 *해석*. AI 는
> 이 결정들을 *구현* 했을 뿐. 모든 ADR (D9-D24) 이 사람의 학술 판단 추적 가능."

### Q17. "코드 19개·tests 129개·문서 12개·...너무 양만 강조하는 거 아닌가?"

**답변**:
> "양 자체보다 *5/5 진짜 데이터 추적* 이 핵심. 정우 module_bd 패턴 100% 모방 —
> 모든 변수의 출처 (PDF·페이지·고시번호) 추적. 예: skidding 단가 9,300원 → KOFPI
> Q4 2025 p.44 / HWP 35년 → IPCC 2019 Vol4 Ch12 Table 12.2. **5/5 진짜 데이터
> 가 가이드의 placeholder 함정 정정 자체가 학술 기여** (정우 D2·D3·D6 + 내 D9·
> D11·D13·D14·D15·D18·D22·D23)."

### Q18. "정우 module_bd 가 90% 인데, 희도(나) 의 contribution 은?"

**답변**:
> "정우는 데이터·함수 *백엔드* (B/D). 내(희도)는 **의사결정 코어 + 학술 통합**:
> Module C 의 19 src + Pareto + DraftPlanCard + 8 deliberation + D22·D23 학술
> 발견 + 5 PR + 발표·논문. 정우 7 함수 호출은 인프라, 본 연구의 *학술 contribution*
> 은 Faustmann-Hartman 한국 변형 + 시장 변곡점 발견. 4인 협업 분담 명확."

---

## 🛡 Bonus — 까다로운 질문

### Q19. "본 발표가 200만원 상금에 적합한가?"

**답변**:
> "공모전 주최 측 평가 기준 (산림 AI Agent 다목적성·실용성·학술성). 본 연구는:
> - **다목적성**: 5+1 시나리오 + 8 사업유형 + NTFP + 보조사업 통합
> - **실용성**: 산주 카카오톡 메시지 자동 + 4 real 사업지 검증
> - **학술성**: D22·D23 정책 발견 + 8 전문가 deliberation + 논문 §1-§7
>
> 학부생 작품으로서 *공모전 + 학술 논문 + 정책 제언* 3중 활용. 결과는 심사위원
> 판단이지만, 본 연구가 의도한 contribution 모두 실현."

### Q20. "다음 단계는?"

**답변**:
> "W7 발표 후 (2026-06-26):
> 1. NRF 과제 (CLIM Lab, 임철희 교수) 후속 연구로 발전
> 2. 학술 논문 투고 (Carbon Balance and Management 또는 한국임학회지)
> 3. 산림청·임업진흥원 정책 제언 발송
> 4. GitHub 오픈소스 유지보수
> 5. 민석 module_a (위성 AGB) 완성 후 W5+ 통합"

---

## 🎤 발표자 노트

- **5분 발표 전 1분 deep breath** + 첫 슬라이드 자신감
- **D23 슬라이드 4 = 핵심 narrative** — 16개월 +126% 강조
- **timer 6분 알람** — Q&A 시작 전 cushion
- **백업 슬라이드 (DraftPlanCard 시연) 준비**
- **데모 영상 1분 백업** (실시간 데모 막힐 경우)
- 모든 ADR (D9-D24) 출처 즉시 인용 가능 상태

---

## 변경 이력
- 2026-05-20 Day 6 — Manual 01 §09 권고 20 Q&A 작성 (Tier 1·2·3·4 + Bonus)
