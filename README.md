# 다목적 산림경영 AI Agent

> **충북 보은 파일럿** — 4인 팀 공모전 작품 (200만원 상금)
> 산주가 자연어로 묻는 *임분 경영 의사결정* 을 AI 가 *데이터·법령·시장* 기반으로 답변.

**기간:** 2026-05-12 ~ 진행 중
**현재 상태:** Day 2 (모듈 B, D 핵심 함수 완성)

---

## 🎯 프로젝트 개요

산주가 *"30년생 강원지방소나무 임분, 지금 벌채할까 더 키울까?"* 같은 질문을 자연어로 입력하면, AI 가:

1. *위성 영상*으로 임분 상태 파악 (모듈 A)
2. *시간별 성장* 예측 (모듈 B)
3. *Faustmann NPV* 계산 (모듈 C)
4. *원목 시장가격·법령*으로 의사결정 보조 (모듈 D)
5. *자연어 + Streamlit UI* 로 답변 (모듈 E)

**파일럿 지역:** 충북 보은 (주력 수종: 강원지방소나무)

---

## 📂 모듈 구조

| 모듈 | 담당자 | 역할 | 상태 |
|---|---|---|---|
| **A** | 정우 + 민석 | 위성 데이터 (Google Earth Engine) | ⏳ 미시작 |
| **B** | 정우 + 민석 | 임분 성장 예측 | ✅ 핵심 완성 |
| **C** | 희도 | Faustmann NPV 계산 | ⏳ 진행 중 |
| **D** | 정우 + 민석 | 원목 시장가격 + 법령 | ✅ 핵심 완성 |
| **E** | 하수범 | Streamlit + LLM 에이전트 | ⏳ 진행 중 |

---

## 📖 모듈별 상세 문서

- [**모듈 B/D — 성장 예측 + 시장·정책**](module_bd/README.md) ⭐ (정우 작업)

---

## 🚀 빠른 시작

```bash
# 1. 가상환경 활성화
.\.venv\Scripts\Activate.ps1

# 2. 패키지 설치
pip install -r requirements.txt

# 3. .env 설정 (API 키)
# DATA_GO_KR_KEY, LAW_OC, VWORLD_KEY 등

# 4. 데이터 재생성 (모듈 B/D)
python module_bd/src/yield_table_parse.py     # 임분수확표
python module_bd/src/kofpi_parse.py           # 원목가격
python module_bd/src/market_snapshot.py       # 종합 시장 스냅샷
```

---

## 🤝 팀

- **정우** (정우나, Kookmin Univ.) — 모듈 A, B, D, 데이터 인프라
- **민석** — 모듈 A, B 협업
- **희도** — 모듈 C (Faustmann NPV, NRF 과제 2022S1A5A8051754)
- **하수범** — 모듈 E (Streamlit + LLM 에이전트)

**과제 자금:** NRF 한국연구재단 일반공동연구 (CLIM Lab, 임철희 교수)

---

## 📌 학술 기반

- Faustmann (1849) — *Land Expectation Value*
- 산림자원의 조성 및 관리에 관한 법률 시행규칙 (2023 개정)
- 박2020 — 산주 WTA 의지가격 (17,039원/tCO₂)
- KOFPI 분기별 원목시장가격조사 (산림청 고시 제2025-22호)