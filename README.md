# 다목적 산림경영 AI Agent

> **충북 보은 파일럿** — 4인 학부생 공모전 작품 (200만원 상금)
> 산주가 자연어로 묻는 *산림 경영 의사결정* 을 AI 가 *데이터+방법론* 기반으로 답변

**기간:** 2026-05-12 ~ 진행 중
**현재 상태:** Day 4 마감 (42 commits, 8 DECISIONS, 5/5 진짜 PDF 데이터, 단위 테스트 45개)

---

## 🎯 프로젝트 개요

산주가 *"30년생 강원지방소나무 1.5ha, 지금 벌채할까 50년까지 키울까?"* 같은 질문을 자연어로 입력하면, AI 가:

1. *위성 영상* 으로 임분 상태 분석 (모듈 A)
2. *시간변화 성장* 예측 (모듈 B)
3. *Faustmann NPV* 계산 (모듈 C)
4. *원목 시장가격·방법론* 으로 의사결정 보조 (모듈 D)
5. *자연어 + Streamlit UI* 로 답변 (모듈 E)

**파일럿 지역:** 충북 보은 (주력 수종: 강원지방소나무)

---

## 📦 모듈 구조

| 모듈 | 담당자 | 역할 | 상태 |
|---|---|---|---|
| **A** | 민석 | 위성 데이터 (Google Earth Engine), NFI 표본점 수집 | ⏳ 미시작 |
| **B** | 정우 | 임분 성장 예측 + 탄소 흡수 | ✅ 핵심 완성 |
| **C** | 희도 | Faustmann NPV 계산 | 🔄 진행 중 |
| **D** | 정우 | 원목 시장가격 + 법령 + 비용 + RAG | ✅ 핵심 완성 |
| **E** | 하수범 | Streamlit + LLM 에이전트 | 🔄 진행 중 |

> 모듈 B/D 는 NFI 실측 데이터가 필요한 일부 작업(기후 보정 회귀, 등급분포 Weibull)에서
> 모듈 A(민석)와 협업한다. NFI 수집은 모듈 A 책임, 그 데이터를 받아 회귀·fit 하는 것은 모듈 B/D 책임.

---

## 📂 모듈별 상세 문서

- [**모듈 B/D — 성장 예측 + 시장·정책**](module_bd/README.md) ⭐ (정우 작업)

---

## 🏆 Day 1-4 성취 (정우 작업 — 모듈 B/D)

### 함수 완성 (가이드 §8.2)
- ✅ `growth_predict()` — 11 수종 임분 성장 + 탄소 흡수
- ✅ `market_snapshot()` — 7 수종 × 6 등급 + KAU
- ✅ `cost_function()` — 5/5 진짜 PDF 데이터
- ✅ `rotation_age()` — 법정 기준벌기령 (별표 3)
- ✅ `lookup_volume()` — 개별 나무 재적
- ✅ `fetch_kau_price()` — KAU 일별
- ✅ `search_law()` — 법령 검색

### 단위 테스트 (가이드 §9.1) ⭐ Day 4
- ✅ 45개 테스트, 함수 5개 커버 (`pytest module_bd/tests/`)
- ✅ growth_predict 8 · cost_function 11 · lookup_volume 8 · market_snapshot 8 · rotation_age 10
- ✅ 검증 테스트(가이드·법령 보증값) + 회귀 테스트(현재 출력 기준선) 구분

### 학술 자산 (5/5 진짜 데이터)
- ✅ 임분수확표 통합 (16,163 행 + 576 행)
- ✅ KOFPI 7 수종 가격 + 거리별 운반비
- ✅ KAU 일별 시계열 + WTA (박2020)
- ✅ 산림사업 표준품셈 + 대한건설협회 노임
- ✅ 산림자원법 별표 3 룰베이스
- ✅ 국립산림과학원 탄소흡수량 (3,212 표본)
- ✅ 산림청 2025 묘목 단가 (15 수종)
- ✅ 산림탄소상쇄 RAG (11 PDF, 281 청크)
- ✅ 산악기상 시계열 — 보은 6 관측소 수집·전처리 완료 (D8 + D10, Day 5)

### 학술 결정 (DECISIONS.md, 8 항목)
- D1-D4: KOFPI · 표준품셈 · cost_function · schemas (Day 2)
- D5-D7: carbon_uptake · seedling · RAG corpus (Day 3)
- D8: 산악기상 데이터 소스·수집 설계 (Day 3-5, 완료)
- D10: 산악기상 시계열 전처리 — 임지 단위 일/월/연 통계 (Day 5)

---

## ⚡ 빠른 시작

```bash
# 1. 가상환경 활성화
.\.venv\Scripts\Activate.ps1

# 2. 패키지 설치
pip install -r requirements.txt

# 3. .env 설정 (API 키)
# DATA_GO_KR_KEY, LAW_OC, VWORLD_KEY 등

# 4. 데이터 재생성 (모듈 B/D)
python module_bd/src/yield_table_parse.py     # 임분수확표
python module_bd/src/kofpi_parse.py            # 원목가격
python module_bd/src/cost_function.py          # 비용 계산
python module_bd/src/growth_predict.py         # 성장 예측 + 탄소
python module_bd/src/carbon_offset_chunk.py    # RAG 청크

# 5. 단위 테스트 실행
pytest module_bd/tests/

# 6. 산악기상 수집·전처리 (Day 3-5 완료)
python module_bd/src/mt_weather_collect.py
```

---

## 👥 팀

- **정우** — 모듈 B (성장 예측 + 탄소), 모듈 D (시장·법령·비용·RAG)
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

---

## 🔗 Repo

- GitHub: https://github.com/jwn6174-crypto/forest-ai-agent
- Module B/D 책임자: 정우 (jwn6174@gmail.com)