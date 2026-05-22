# Analysis Index — Day 5-6 산출 종합

> 2026-05-19~20 Day 5-6 작업의 모든 분석 문서 인덱스.

---

## 파일 목록 (12)

| # | 파일 | 용도 |
|---|---|---|
| 00 | [00_index.md](./00_index.md) | 이 파일 |
| 01 | [01_manual_corrections.md](./01_manual_corrections.md) | 메뉴얼 vs 정우 실제 11 정정 항목 |
| 02 | [02_minseok_handle.md](./02_minseok_handle.md) | 민석 미시작 3단 fallback 전략 |
| 03 | [03_timeline.md](./03_timeline.md) | D5 → W7 (6/26) 작업 매트릭스 |
| 04 | [04_team_repo_audit.md](./04_team_repo_audit.md) | 정우 forest-ai-agent 완전 인벤토리 |
| 05 | [05_bd_integration.md](./05_bd_integration.md) | Module C ↔ B/D 함수 호출 명세 |
| 06 | [06_module_c_build_plan.md](./06_module_c_build_plan.md) | 데이터 8 + API 5 + 코드 6 tier 종합 빌드 플랜 |
| 07 | [07_expert_sessions.md](./07_expert_sessions.md) | Round 1: 5 deliberation (산림학자/경제/정책/경영자/AI) |
| 08 | [08_api_keys_setup.md](./08_api_keys_setup.md) | data.go.kr/VWorld/KOSIS/법제처 키 발급 |
| 09 | [09_module_e_handoff.md](./09_module_e_handoff.md) | 정우 5/19 api_server.py + compute_lev endpoint PR |
| 10 | [10_module_c_focus.md](./10_module_c_focus.md) | 종합 빌드 플랜 (사용자 정정 반영) |
| **11** | [11_expert_sessions_round2.md](./11_expert_sessions_round2.md) | **Round 2: 위성·산주·통합자** + 학술 발견 2개 반영 |

---

## 핵심 통찰 (Day 6 최종)

### 🏆 학술 발견 2개
1. **D22 — carbonregistry 4 검증 case 인증 320 tCO₂/ha/30yr vs 모델 157 = +103% 차이**
   - 한국 산림탄소상쇄 인증실적 baseline 가정 검토 필요성 첫 정량 제기
   - 위성 학자: 자연성장 vs 경영후 측정의 *모집단 차이* (가설 b)
2. **D23 — KAU25 16개월 +126% (8,670→19,600), WTA 17,039원 한국 ETS 역사상 첫 돌파** (2026-03~05)
   - 사유림 산주 자발적 KOC 참여 *경제적 합리성*의 시점 발견
   - 발표 strongest finding

### 8 전문가 deliberation 종합
| Round 1 | Round 2 |
|---|---|
| 산림학자 (Weibull-2P) | 위성/원격탐사 (모집단 차이·NDVI 시계열) |
| 산림경제학자 (Lognormal·WTA) | 영세 산주 (숫자 1개 큼지막·카카오톡) |
| 산림정책학자 (정책 모순 기여) | 통합자 (**D23 우선·KAU 변곡점 타이틀**) |
| 경영자 (간벌+10년) | |
| AI 엔지니어 (LHS·Strategy) | |

### Module C 정량
- **129 tests pytest 통과** (정우 45 의 2.8배)
- **19 src + 8 data JSON + 16 test 파일 + 3 notebooks**
- **DECISIONS ADR 13개** (D9-D24)
- **6 polygon** (Sample 2 + Real 4)
- **6 API 키 통과** (decoded 형식, 사용자 본인 명의)

---

## 외부 산출 (workspace 밖)

- `E:\forest_ai\README.md` / `STATUS.md` / `.env` (gitignore)
- `E:\forest_ai\module_c\` (코드 + 데이터 + tests + notebooks)
- `E:\forest_ai\shared\schemas_proposed.py` + `test_schemas.py` (15 tests)
- `E:\forest_ai\_workspace\PR_bodies.md` (PR 1, 2, 4 본문)

---

## 변경 이력
- 2026-05-19 Day 5 — Round 1 5 deliberation + 10 분석 문서
- 2026-05-20 Day 6 — Round 2 3 deliberation + 학술 발견 D22·D23 + 11번 추가
