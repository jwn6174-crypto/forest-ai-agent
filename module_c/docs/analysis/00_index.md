# Module C 분석 문서 — 전체 색인

이 디렉토리는 Module C(Faustmann–Hartman 경제성 분석)를 설계하고 구현하는
과정에서 내려진 모든 판단의 근거를 담는다. 코드가 "무엇을" 하는지는 `src/` 가
보여주고, "왜 그렇게" 하는지는 `DECISIONS.md` 의 27개 ADR 이 압축해 담는다.
이 색인이 가리키는 16편의 문서는 그 결정들이 어떤 조사·심의·검증을 거쳐
나왔는지를 풀어 쓴 연구 노트다.

작업은 2026년 5월 19일 Module C 의 첫 줄을 쓰면서 시작해, 5월 31일 Module A·B·C·D
네 모듈을 하나의 파이프라인으로 통합하기까지 이어졌다. 그 사이 여덟 분야의
전문가 심의를 두 차례 거쳤고, 다섯 건의 학술적 발견을 정리했으며, 정우의
module_bd 가 갱신될 때마다 그 변화를 흡수했다.

---

## 1. 출발점 — 무엇을, 왜 만드는가

| 문서 | 한 줄 요약 |
|---|---|
| [01_manual_corrections.md](01_manual_corrections.md) | 팀 가이드의 placeholder 값과 정우가 실제로 구현한 데이터 사이의 11개 차이를 정리하고, 이를 학술적 기여로 전환한 기록 |
| [02_minseok_handle.md](02_minseok_handle.md) | Module A 가 미완성이던 시기에 Module C 가 단독으로 동작하도록 설계한 fallback 전략 (현재는 통합 완료) |
| [03_timeline.md](03_timeline.md) | 5월 19일부터 발표(6월 26일)까지의 주차별 작업 매트릭스 |

## 2. 통합 설계 — 정우·수범과 어떻게 잇는가

| 문서 | 한 줄 요약 |
|---|---|
| [04_team_repo_audit.md](04_team_repo_audit.md) | 정우 forest-ai-agent 저장소의 전체 인벤토리 — 어떤 함수와 데이터가 이미 존재하는지 |
| [05_bd_integration.md](05_bd_integration.md) | Module C 가 정우의 module_bd 함수(growth_predict·market_snapshot·cost_function·rotation_age)를 호출하는 정확한 명세 |
| [06_module_c_build_plan.md](06_module_c_build_plan.md) | 데이터 8종·외부 API 5종·코드 6단계로 이루어진 종합 빌드 플랜 |
| [09_module_e_handoff.md](09_module_e_handoff.md) | 정우의 api_server.py 분석과 Module C 를 ui 로 잇는 endpoint 설계 |
| [12_module_e_tool_spec.md](12_module_e_tool_spec.md) | 수범의 LLM 에이전트가 호출할 도구 함수 명세 |

## 3. 전문가 심의 — 여덟 시선으로 검증한 판단

| 문서 | 한 줄 요약 |
|---|---|
| [07_expert_sessions.md](07_expert_sessions.md) | 1차 심의 — 산림학자·산림경제학자·정책학자·산림경영자·AI 엔지니어 다섯 시선의 합의 |
| [11_expert_sessions_round2.md](11_expert_sessions_round2.md) | 2차 심의 — 위성/원격탐사 학자·영세 산주·산림경제정책 통합자 세 시선의 추가 검증 |
| [10_module_c_focus.md](10_module_c_focus.md) | 위 심의를 종합한 Module C 단독 완성 빌드 플랜 (가장 방대한 단일 문서) |

## 4. 실무 — 데이터와 키

| 문서 | 한 줄 요약 |
|---|---|
| [08_api_keys_setup.md](08_api_keys_setup.md) | data.go.kr·VWorld·KOSIS·법제처 본인 명의 API 키 발급 절차 |
| [13_jeongwoo_patterns_checklist.md](13_jeongwoo_patterns_checklist.md) | 정우의 코딩·문서 패턴을 100% 따랐는지 점검한 15항목 체크리스트 |

## 5. Module A 통합 — 네 모듈을 하나로

| 문서 | 한 줄 요약 |
|---|---|
| [14_module_a_integration_masterplan.md](14_module_a_integration_masterplan.md) | Module A 도착 *전* 에 미리 세운 통합 마스터플랜 — 학술 발견을 위성으로 어떻게 강화할지 |
| [15_module_a_arrived_integration_audit.md](15_module_a_arrived_integration_audit.md) | Module A 도착 *후* 네 모듈을 총괄 감사한 기록 — 인터페이스 매트릭스와 학술 발견 #5 도출 |

통합 가이드는 분석 디렉토리가 아니라 [`../integration/api_server_integration.md`](../integration/api_server_integration.md)
에 따로 두었다. 정우와 수범이 자기 코드를 고칠 때 바로 참조할 수 있도록,
정확한 교체 코드와 검증 절차를 담았다.

---

## 핵심 통찰 다섯 가지

이 16편이 도달한 결론을 다섯 문장으로 압축하면 다음과 같다.

첫째, **정우의 module_bd 가 이미 만든 것을 호출만 하면 된다.** Module C 가
새로 데이터를 구축해야 했던 것은 임지 현재 상태(민석)와 임산물 수입(KOSIS
미제공)뿐이었고, 나머지 일곱 변수는 정우의 함수가 채워 준다.

둘째, **느슨한 결합이 통합을 단순하게 만든다.** Module A 가 무거운 위성 모델을
import 시점에 적재하더라도, Module C 는 그 출력 dict 만 받으므로 그 무게에서
자유롭다. 그 결과 통합은 어댑터 두 개와 api_server 한 곳의 교체로 끝났다.

셋째, **추정 방법마다 체계적 편향이 있다.** 산림탄소상쇄 인증실적은 높게(D114),
국가 수확표는 평균적으로(D122), 위성 GEDI 는 포화 구간에서 낮게(D126) 추정한다.
어느 하나를 정답으로 삼기보다 셋을 교차 비교하는 것이 정직하다.

넷째, **시장이 막 변곡점을 지났다.** KAU 배출권 가격이 2026년 3~5월 사이
산주의 의향가격(WTA 17,039원)을 한국 ETS 역사상 처음으로 넘어섰다(D115). 이
시점부터 사유림 산주의 자발적 탄소상쇄 참여가 경제적으로 합리적이 된다.

다섯째, **정직한 한계 명시가 곧 학술적 가치다.** 위성의 R²=-0.187, 기후 보정의
외삽 영역, 영세림의 직경 변이 — 이 한계들을 숨기지 않고 limitations 와
uncertainty_tier 로 드러내는 것이 이 시스템의 신뢰성을 떠받친다.

---

## 학술 발견 다섯 건 한눈에

| ID | 발견 | 추정 편향 |
|---|---|---|
| D114 | 산림탄소상쇄 인증실적이 자연 성장 모델보다 +103% 높다 | 인증 = 과대 |
| D115 | KAU 가 16개월 +126%, WTA 의향가격을 역사상 처음 돌파 | 시장 변곡점 |
| D122 | 국가 수확표 등급분포가 NFI 실측보다 상위 등급 과대 | 수확표 = 과대 |
| D124 | 정우 기후 보정과 임종환 시뮬레이션의 부호가 정반대 | 모델 간 불일치 |
| D126 | 위성 GEDI 가 고밀도 침엽수림을 과소추정(R²=-0.187) | 위성 = 과소 |

---

*최종 갱신: 2026-05-31, Module A·B·C·D 통합 완료 시점*
