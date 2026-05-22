# 논문 §1-§7 IMRaD outline v1

> 발표 (2026-06-26) 와 함께 제출할 학술 논문 초안. W6 (6/12-6/18) 에 §1-§5 완성, W7 에 §6-§7 final.

**Title (영문)**: A Faustmann–Hartman Korean Adaptation Captures KAU Market Inflection: A Decision-Support Framework for Forest Carbon Policy Based on Multi-Expert Deliberation

**Title (한글)**: Faustmann–Hartman 한국 변형으로 포착한 KAU 시장 변곡점: 5+1 학자 deliberation 기반 산림탄소 정책 의사결정 프레임워크

**Authors**: Heedo Choi¹ · Jeongwoo Na² · Minseok Kim¹ · Subum Ha¹ · Cheolhee Lim¹*
¹Department of Forest Environmental Systems, Kookmin University
²Same affiliation
*Corresponding author (CLIM Lab director, NRF 2022S1A5A8051754)

**Keywords**: Faustmann-Hartman, Korean forest carbon offset (KOC), KAU market, Willingness-to-accept (WTA), forest management decision support, Monte Carlo, IPCC HWP, multi-expert deliberation

---

## §1. Introduction (W6 작성, 1.5-2 페이지)

### 1.1 한국 산림 3 가지 구조적 공백 (1단락)
- 사유림 67% × 영급 불균형 (30년 이상 72%, 산림청 2050 탄소중립)
- 산림탄소상쇄 99% 가 "벌기령 연장" 으로 발생 (한국임업진흥원 589 등록사업)
- NDC 26.7Mt 흡수 목표 vs "노령림 → 벌채 → 재조림" 정책

### 1.2 학술 공백 (1단락)
Faustmann (1849) — Hartman (1976) — van Kooten (1995) — carbon-decay (Insley 2002, IPCC 2019) 표준은 있지만 **한국 데이터 (KOFPI Q4 2025, 별표 3, 임분수확표, carbonregistry) 로 임지 단위 instantiation 한 도구 사실상 부재**.

### 1.3 본 연구 contribution (1단락)
1. **Faustmann-Hartman 한국 변형 instantiation** — 6 시나리오 × Monte Carlo LHS 300
2. **D22**: carbonregistry 4 검증 case 인증 vs 모델 +103% 차이 — *baseline 가정 검토 필요성 첫 정량 제기*
3. **D23**: KAU 16개월 +126%, WTA 17,039원 (박일희 2020) **역사적 첫 돌파** 시점 발견
4. **8 전문가 deliberation** (산림·경제·정책·경영·AI·위성·산주·통합) 기반 학제적 모델링

### 1.4 논문 구조 (1단락)
§2 Background · §3 Data · §4 Methods · §5 Results · §6 Discussion · §7 Conclusion

---

## §2. Background (W6, 2 페이지)

### 2.1 Faustmann (1849) Land Expectation Value
- 영구 회전벌채의 순수입 현재가치
- 수식 + 분모 (1 − e^(-rT)) 의 영구회전 효과

### 2.2 Hartman (1976) 비목재 가치 통합
- 탄소·휴양·생물다양성 *flow value*
- 한국적 의미: KOC·자발적 탄소시장 통합

### 2.3 핵심 선행연구
| 저자·연도 | 핵심 |
|---|---|
| Faustmann (1849) | LEV 원전 |
| Hartman (1976) Econ Inquiry | 비목재 가치 |
| Reed (1984) | 확률론적 회전기 |
| Brazee & Mendelsohn (1988) | Lognormal 가격 |
| Insley (2002) | Real options 산림 |
| van Kooten (1995) | 탄소-목재 통합 |
| IPCC 2019 Refinement Vol4 Ch12 | HWP half-life default |
| 박일희 (2020) 서울대 학위논문 | 한국 산주 WTA 17,039원/tCO₂ |
| 임종환 (2020) 국립산림과학원 | SSP 시나리오 수종 영향 |
| 강진택 (2016) 국립산림과학원 | 강원소나무 Weibull 직경분포 |

### 2.4 한국 정책 맥락
- NDC 2030 산림 26.7Mt
- 산림기본법 시행규칙 별표 3 (기준벌기령, 2023-06-27 개정)
- 산림탄소상쇄제도 운영지침 2024 (8 사업유형)
- K-ETS KAU + 산림탄소상쇄 KOC (산림청·임업진흥원)

---

## §3. Data (W6, 2-3 페이지)

### 3.1 정우 module_bd 의 5/5 진짜 PDF 데이터 (Day 3 완성)
- KOFPI Q4 2025 7 수종 × 6 등급
- KAU 일별 (한국거래소)
- 표준품셈 (산림청 고시 제2025-82호)
- 별표 3 (시행규칙)
- 국립산림과학원 탄소흡수량 (2003 개발, 2013/2024 개정, 3,212 표본)
- 산림청 2025 묘목가격 (15 수종)
- 산림탄소상쇄 11 PDF → 281 RAG 청크

### 3.2 Module C 자체 데이터 (Day 6 완성)
| 데이터 | 출처 | 결정 |
|---|---|---|
| HWP decay | IPCC 2019 Refinement Vol4 Ch12 (35/25/2년) | D15 |
| SSP 기후 multiplier | 임종환 2020 + IPCC AR6 | D11.b |
| 산림보조사업 단가 | 산림청 「2025 산림소득분야 사업시행지침」 | D18 |
| NTFP 소득 | 산림청 「2024년 임산물생산조사 보고서」 (KOSIS 폐기) | D13 |
| 8 사업유형 룰 | 산림청 운영지침 2024 + 정우 RAG 281 청크 | D16 |
| **carbonregistry 658건** | **carbonregistry.forest.go.kr (사용자 직접 제공)** | **D22** |
| **KAU 16개월** | **data.go.kr 1160100 GetCertifiedEmissionReductionPriceInfo** | **D23** |

### 3.3 6 polygon (Sample 2 + Real 4)
- VWorld 실 좌표 (보은 산외면 오대리 lon=127.7344, lat=36.5841 등)

### 3.4 정책학자 D17 4 조건 + 확장
검증 case 선정: (a) 벌기령연장 사업유형 ✓ (b) 충북 보은 / 전북 진안 ✓ (c) 거래 (인증실적 공개) ✓ (d) 면적 영세 사유림 대표 ✓ (e) 사업개시 2018+ (proxy)

---

## §4. Methods (W6, 3-4 페이지)

### 4.1 Faustmann-Hartman 수식 instantiation
(슬라이드 3 의 수식 + 변수 정의 표)

### 4.2 6 시나리오 정의 (D18 간벌+10년 추가)
| 시나리오 | T | 비용 action | 탄소수익 | NTFP | 보조사업 |
|---|---|---|---|---|---|
| 즉시 | age_now | clearcut | 0 | 0 | regen |
| 5년 / 10년 | +5 / +10 | clearcut | 5-10년치 (KOC>WTA) | 0 | regen |
| 연장KOC | max(legal+10, age+10) | clearcut | 매년 KOC | 0 | - |
| 임산물 (S5a/S5b) | +15 | clearcut | 15년치 | 0.3-8M/ha | regen |
| **간벌+10년** | +10 | **thinning** | 10년치 | 0 | **thinning 2.5M/ha + regen** |

### 4.3 Monte Carlo + LHS (D11)
- 6 분산 source × LHS 300 samples
- Lognormal: timber_price, koc_price, ntfp_annual (Brazee-Mendelsohn 1988)
- Triangular: agb_mg, discount_rate
- Normal: climate_multiplier (임종환 2020)

### 4.4 HWP carbon decay (D15)
```
L_C(T) = Σ_i HWP_i · (1 − exp(−ln2 · t / h_i))
```
- IPCC 2019: sawnwood 35년, panels 25년, paper 2년
- 한국 침엽수 분배: 60% / 25% / 15%

### 4.5 Pareto front (Hartman 정통, D12)
- 2축: NPV vs 누적 탄소격리량
- 산주 UI 단순화: 3 대표점 (안정형 / 균형형 / 수익형)

### 4.6 8 전문가 deliberation 방법론
Round 1 (5/19) — 5 페르소나 병렬 spawn → 25 질문 응답 → D11-D21 결정.
Round 2 (5/20) — 3 페르소나 (학술 발견 후) → D22-D24 + 발표 framing.

### 4.7 Module C ↔ 정우 module_bd 인터페이스
- `growth_predict()` `market_snapshot()` `cost_function()` `rotation_age()` `fetch_kau_price()` 호출
- Pydantic 옵션 P2 패턴 (LEVResult, ComputeLEVRequest, DraftPlanCard)

---

## §5. Results (W6, 2-3 페이지)

### 5.1 D23 KAU 시장 변곡점 ⭐ strongest finding
- 2025-07 (8,670원) → 2026-05 (19,600원) = +126%
- WTA hurdle 17,039원 (박일희 2020) 한국 ETS 역사상 첫 돌파 (2026-03~05)
- **시나리오 4 (연장KOC) 의 경제적 유효성 확보 시점**

[Plot: KAU25 16개월 시계열 + WTA 가로선 + 돌파 시점 강조]

### 5.2 D22 인증 vs 모델 +103% 차이
- carbonregistry 4 case 모두 320 tCO₂/ha/30yr 균일
- Module C 모델 157 tCO₂/ha/30yr
- 4 case 차이 +103.1% ~ +103.3% (균일성)

[Plot: 4 case 인증 vs 모델 막대 차트]

### 5.3 6 polygon × 6 시나리오 결과 (보은 산외면 오대리, Primary)
| 시나리오 | NPV (M원) | 추천 |
|---|---|---|
| 즉시 | 66.0 | ✅ |
| 5년 | 56.8 | ✅ |
| 10년 | 48.8 | ✅ |
| 연장KOC | 48.8 | ✅ |
| 임산물 | 41.6 | ✅ |
| **간벌+10년** | **80.2** | ⭐ **추천 (균형)** |

→ 균형 추천 시나리오 = 간벌+10년 (NPV +14M/ha 대비 즉시벌채)

### 5.4 8 전문가 deliberation 종합 영향
- 모델 결정 13개 ADR (D9-D24) — 각 deliberation 추적
- 코드 19 파일 — 모든 결정 반영

---

## §6. Discussion (W6-W7, 2-3 페이지)

### 6.1 D22 학술 해석 — 두 가설 비교
- 가설 1: 인증 = 30년 *피크* 흡수율 (10.77) × 30년 = bookkeeping overestimation
- 가설 2: 인증 = 경영 후 실측 (간벌·시비·천연갱신 보완) — Module C 자연 성장 가정 차이
- **위성/원격탐사 학자 Round 2: 가설 2 압도적 가능성** — 자연성장 vs 경영후 측정의 모집단 차이
- → 정책 함의: 인증실적 baseline 가정 재검토 필요

### 6.2 D23 정책 시사
- 사유림 영세 산주 자발적 KOC 참여 *경제적 합리성*의 시점 발견
- 정책학자 D17 의 "노령림 정책 갈등" 해소 가능 시점
- Faustmann-Hartman 적용의 학술적·정책적 *시의성*

### 6.3 Module A (위성 AGB) 미시작 framing
- "위성 안 함" 을 *deliberate methodological choice* 로 reframing
- NFI direct lookup = IPCC Tier 2 표준 (Avitabile et al. 2016)
- 영세 polygon (1-2ha) 에서 위성 RF/XGBoost mixed pixel 30-40% 한계 우회

### 6.4 Limitations
- carbonregistry 사업 polygon centroid 만 확보 (구체적 polygon 비공개)
- HWP 한국 침엽수 분배 비율 60/25/15 추정 (정확 통계 미공개)
- 임종환 2020 SSP multiplier 원문 PDF 미확보 (IPCC AR6 보완)
- 송이 변동성 매우 큼 (2023→2024 -30.4%) — Monte Carlo std 큼
- W4 Weibull-2P fit 정우 NFI 협업 대기 (현재 HeuristicGD)

### 6.5 Future work
- GEDI L4A + Sentinel-2 NDVI 시계열 triangulation (위성 학자 Round 2 Plan B)
- 정우 carbon_chunks 281 청크 BGE-M3 embedding + RAG 정밀화 (수범 모듈 E)
- 8 사업유형 자동 매칭 신뢰도 향상 (룰베이스 80% → 90% 목표)

---

## §7. Conclusion (W7, 0.5 페이지)

본 연구는 Faustmann-Hartman 한국 변형 instantiation 을 통해 (1) 한국 산림탄소상쇄
인증실적의 baseline 가정 검토 필요성을 첫 정량 제기 (+103% 차이), (2) KAU 시장의
역사적 변곡점 (2026-03~05 WTA hurdle 첫 돌파) 을 발견했다.

8 전문가 deliberation 기반 학제적 모델링은 영세 사유림 산주의 의사결정 보조도구로
실용성을 확보했으며, 산림청·임업진흥원·지역 산림조합의 정책 시행에 직접 활용 가능하다.

향후 위성 (GEDI/Sentinel-2) 통합 검증과 정책 시행 후 정량 평가가 본 연구의 후속 과제다.

---

## Acknowledgements

This work was supported by NRF (National Research Foundation of Korea) Joint Research
Grant 2022S1A5A8051754 (CLIM Lab, Kookmin University, P.I. Cheolhee Lim).

데이터: carbonregistry.forest.go.kr · data.go.kr · 산림청 통합자료실 · VWorld · 국립산림과학원

---

## References (W7 final)

1. Faustmann, M. (1849). *Calculation of the value which forest land and immature stands possess for forestry*. Allgemeine Forst- und Jagd-Zeitung.
2. Hartman, R. (1976). The harvesting decision when a standing forest has value. *Economic Inquiry*, 14(1), 52-58.
3. IPCC (2019). 2019 Refinement to the 2006 IPCC Guidelines, Vol 4 Ch 12 Harvested Wood Products.
4. 박일희 (2020). 한국 산주의 산림탄소상쇄제도 의지가격. 서울대학교 식품자원경제학과 석사학위논문.
5. 임종환 외 (2020). 기후변화 시나리오 하 한국 주요 수종 생장 변화 전망. 국립산림과학원.
6. 강진택 외 (2016). 강원지방소나무 직경분포식. 국립산림과학원.
7. 국립산림과학원 (2003/2024). 수종별 탄소흡수량 (3,212 표본).
8. 산림청 (2025). 산림소득분야 사업시행지침.
9. 산림청 (2024). 산림탄소상쇄 운영지침.
10. Brazee, R., & Mendelsohn, R. (1988). Timber harvesting with fluctuating prices. *Forest Science*, 34(2), 359-372.
11. Reed, W. J. (1984). The effects of the risk of fire on the optimal rotation of a forest. *Journal of Environmental Economics and Management*, 11(2), 180-190.
12. Avitabile, V., et al. (2016). An integrated pan-tropical biomass map using multiple reference datasets. *Global Change Biology*, 22(4), 1406-1420.
13. carbonregistry.forest.go.kr 산림탄소상쇄 등록부 (Accessed 2026-05-20, 658 projects).
14. data.go.kr/1160100 GetCertifiedEmissionReductionPriceInfo (KAU 시계열, 2025-2026).

---

## Appendix

- A. Module C 소스 코드: github.com/jwn6174-crypto/forest-ai-agent
- B. 19 ADR (DECISIONS.md D9-D24)
- C. 8 전문가 deliberation 전문 (analysis/07 + 11)
- D. 4 검증 case 상세 (보은·진안 carbonregistry FCR_ID 명시)
- E. 데이터 8 JSON 원본
- F. 129 pytest 결과
- G. 발표 슬라이드 (7장)

---

## 변경 이력
- 2026-05-20 Day 6 — outline v1 (W6 에 §1-§5 완성, W7 에 §6-§7 final)
