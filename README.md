# 다목적 산림경영 AI Agent

> **충북 보은 파일럿** — 4인 학부생 공모전 작품 (200만원 상금)
> 산주가 자연어로 묻는 *산림 경영 의사결정* 을 AI 가 *데이터+방법론* 기반으로 답변

**기간:** 2026-05-12 ~ 진행 중
**현재 상태:** Day 7 완료 — 모듈 B/D 책임 13/13 완성 (climate_correct v8 R² 0.228 + 등급분포 Weibull + NEX-GDDP SSP 통합)
**자산:** 78+ commits · 17 DECISIONS · 5/5 진짜 PDF 데이터 · 단위 테스트 59개 · ASOS 5 시군 30년 평년 (55MB) · NFI 5/6/7차 시계열

---

## 🎯 프로젝트 개요

산주가 *"30년생 강원지방소나무 1.5ha, 지금 벌채할까 50년까지 키울까?"* 같은 질문을 자연어로 입력하면, AI 가:

1. *위성 영상* 으로 임분 상태 분석 (모듈 A)
2. *임분 성장* 예측 (모듈 B) — 탄소·등급분포·기후 보정(SSP) 포함 ⭐
3. *Faustmann NPV* 계산 (모듈 C)
4. *원목 시장가격·방법론* 으로 의사결정 보조 (모듈 D)
5. *자연어 + Streamlit UI* 로 답변 (모듈 E)

**파일럿 지역:** 충북 보은 (주력 수종: 강원지방소나무)

---

## 📦 모듈 구조

| 모듈 | 담당자 | 역할 | 상태 |
|---|---|---|---|
| **A** | 민석 | 위성 데이터 (Google Earth Engine), NFI 표본점 수집 | ⏳ 미시작 |
| **B** | 정우 | 임분 성장 예측 + 탄소 + 등급분포 + 기후 보정 | ✅ **13/13 완성** |
| **C** | 희도 | Faustmann NPV 계산 | 🔄 진행 중 |
| **D** | 정우 | 원목 시장가격 + 법령 + 비용 + RAG | ✅ **완성** |
| **E** | 하수범 | Streamlit + LLM 에이전트 | 🔄 진행 중 |

> 모듈 B/D 는 NFI 5/6/7차 실측 데이터를 직접 추출하여 climate_correct() 회귀
> 학습 + NEX-GDDP SSP 시나리오 통합 완료 (Day 7). 모듈 A 위성 GEE 작업은
> 별도 세션 진행 예정 (NFI 좌표는 추출 완료).

---

## 📂 모듈별 상세 문서

- [**모듈 B/D — 성장 예측 + 시장·정책**](module_bd/README.md) ⭐ (정우 작업)

---

## 🏆 Day 1-7 성취 (정우 작업 — 모듈 B/D)

### 함수 완성 (가이드 §8.2)
- ✅ `growth_predict()` — 11 수종 성장 + 탄소 + 등급분포 + 기후 보정 통합 ⭐ Day 7
- ✅ `grade_distribution()` — Weibull 등급별 본수 (소경/중경/대경) ⭐ Day 7
- ✅ `market_snapshot()` — 7 수종 × 6 등급 + KAU
- ✅ `cost_function()` — 5/5 진짜 PDF 데이터
- ✅ `rotation_age()` — 법정 기준벌기령 (별표 3)
- ✅ `lookup_volume()` — 개별 나무 재적
- ✅ `fetch_kau_price()` · `search_law()`
- ✅ `climate_correct` (v8) — NFI 5+6+7차 + SI 회귀, R² 0.228 ⭐ Day 7

### 단위 테스트 (가이드 §9.1)
- ✅ 59개 테스트 (`pytest module_bd/tests/`)
- ✅ growth_predict 8 · cost_function 11 · lookup_volume 8 · market_snapshot 8
  · rotation_age 10 · grade_distribution 14 ⭐ Day 7

### 학술 자산
- ✅ 임분수확표 (16,163 행 + 576 행), KOFPI 7수종, KAU + WTA, 표준품셈 + 노임
- ✅ 산림자원법 별표 3, 국립산림과학원 탄소흡수량, 산림청 묘목 단가
- ✅ 산림탄소상쇄 RAG (11 PDF, 281 청크), 임가경제 (충북 5년치)
- ✅ 산악기상 (보은 6 관측소), ASOS 5 시군 30년 평년 (54,790일)
- ✅ **NFI 5+6+7차 충북** — 시계열 3시점, 3,131 표본점, 137,436 그루 ⭐ Day 7
- ✅ **등급분포 Weibull** — 충북 46,722 그루, 23 그룹 fit (왜도 +1.112) ⭐ Day 7
- ✅ **climate_correct() v8** — R² 0.228, 2,194 행 패널 + SI ⭐ Day 7
- ✅ **NEX-GDDP-CMIP6 SSP** — 5모델 앙상블, 2021-2050, ssp245/585 ⭐ Day 7

### 학술 결정 (DECISIONS.md, 17 항목)
- D1-D10: KOFPI · 표준품셈 · schemas · carbon · seedling · RAG · 산악기상 · 임가경제
- D11-D13: NFI 7차 검증·추출 · climate_correct v5 (Day 6)
- **D14: 등급분포 Weibull fit (Day 7)**
- **D16: NFI 5차 통합 — 시계열 3시점 (Day 7)**
- **D17: SI 변수 + measure_year ablation (Day 7)**
- **D15: 기후 보정 통합 — NEX-GDDP SSP + 외삽 정직 감지 (Day 7)**

---

## 🌟 Day 7 핵심 진전

### 1. 등급분포 Weibull (D14)
NFI 충북 46,722 그루 DBH 분포 → Weibull fit (왜도 +1.112, 교과서적 적합).
영급 × 임상 23 그룹. 대경재 비율 영급 단조 증가. growth_predict() 통합:
강원소나무 30→60년 대경재 64→120본 (벌기 시점 결정 직접 지원).

### 2. climate_correct R² 0.204 → 0.228 (정직한 ablation)
| 버전 | 구성 | R² |
|---|---|---|
| v5 (Day 6) | 6+7차 | 0.204 ±0.074 |
| v7 | + NFI 5차 (시점 3) | 0.204 ±0.038 (안정성 2배) |
| **v8** | **+ SI** | **0.228 (best)** |
| v9 | + measure_year | 0.223 (효과 없음, 제거) |

- NFI 5차: 좌표/ID/코드 6/7차 동일 발견 → 변환 불필요
- 차수별 잔차 단조 증가 (-6.1 → +11.7) = 온난화/임분성숙 신호
- measure_year 효과 없음 = anomaly 가 시간 trend 흡수 (기후변수 정당성 입증)

### 3. 기후 보정 통합 + 외삽 정직 (D15)
- NEX-GDDP-CMIP6 GEE 직접 추출 (민석 의존 없이 우리가 직접)
- growth_predict(climate_scenario="SSP245", elev=350) 작동
- **외삽 정직 감지**: 미래 기온이 학습 범위 밖 → 트리 모델 외삽 →
  SSP245=SSP585 동일 보정. 이를 숨기지 않고 경고 자동 표시.
  "구조 완성 + 미래 외삽 한계 명시" = 학술적으로 가장 정직.

→ 상세: [DECISIONS.md](module_bd/DECISIONS.md)

---

## ⚡ 빠른 시작

```bash
# 1. 가상환경 + 패키지
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. .env 설정 (DATA_GO_KR_KEY, LAW_OC, VWORLD_KEY 등)

# 3. 데이터 재생성 (모듈 B/D)
python module_bd/src/yield_table_parse.py     # 임분수확표
python module_bd/src/cost_function.py          # 비용
python module_bd/src/growth_predict.py         # 성장+탄소+등급분포+기후보정
python module_bd/src/carbon_offset_chunk.py    # RAG 청크

# 4. climate_correct 학습 (Day 6-7)
python module_bd/src/asos_collect.py
python module_bd/src/asos_chungbuk_collect.py
python module_bd/src/diagnose/nfi5_extract.py                   # NFI 5차 추출 (D16)
python module_bd/src/climate_correct/climate_features_panel.py  # 시계열 패널 (70행)
python module_bd/src/climate_correct/fit_correct.py             # v8 회귀 → pkl
python module_bd/src/weibull_fit.py                             # 등급분포 (D14)
# NEX-GDDP 는 GEE JavaScript Code Editor 에서 추출 (D15)

# 5. 단위 테스트
pytest module_bd/tests/
```

---

## 👥 팀

- **정우** — 모듈 B (성장+탄소+등급분포+기후 보정), 모듈 D (시장·법령·비용·RAG)
- **민석** — 모듈 A (위성 GEE, NFI 표본점 수집)
- **희도** — 모듈 C (Faustmann NPV, NRF 과제 2022S1A5A8051754)
- **하수범** — 모듈 E (Streamlit + LLM 에이전트)

**과제 자금:** NRF 한국연구재단 일반공동연구 (CLIM Lab, 임철희 교수)

---

## 📚 학술 기반

- Faustmann (1849) — *Land Expectation Value*
- 산림자원의 조성 및 관리에 관한 법률 시행규칙 (2023 개정)
- 박2020 — 산주 WTA 의지가격 (17,039원/tCO2)
- KOFPI 분기별 원목시장가격조사 (산림청 고시 제2025-22호)
- 국립산림과학원 탄소흡수량 (2003 개발, 2013/2024 개정)
- 산림청 2025년 산림용 종자·묘목가격 (시행령 제16조)
- 산림탄소상쇄제도 운영지침 + 8 사업유형 방법론 (2025.1.2.)
- 산림청 국립산림과학원 산악기상정보 (보은 6 관측소)
- 국가산림자원조사 NFI 5/6/7차 (산림빅데이터팀, 2006-2020)
- 기상청 ASOS 일자료 (data.go.kr API, 5 시군 30년 1991-2020)
- **NASA NEX-GDDP-CMIP6 (GEE, SSP2-4.5/5-8.5, 2021-2050)** ⭐ Day 7
- Burton et al. (2024) ISIMIP3a/ATTRICI Factual/Counterfactual 프레임워크 (방법론 참고)

---

## 🔗 Repo

- GitHub: https://github.com/jwn6174-crypto/forest-ai-agent
- Module B/D 책임자: 정우 (jwn6174@gmail.com)