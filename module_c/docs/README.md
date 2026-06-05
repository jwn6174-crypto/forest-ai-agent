# Module C Docs — 학술 산출물 + 분석 + Deliberation 인덱스

> Module C (Faustmann-Hartman LEV) 의 모든 학술·분석·발표·논문 산출물.
> 정우 module_bd 패턴 확장 — module_bd 는 src/data/tests, module_c 는 + docs/.

**작성일**: 2026-05-22
**Module C 버전**: v1.0.0-day6

---

## 📂 디렉토리 구조

```
module_c/docs/
├── README.md                       (이 파일 — docs 인덱스)
├── PR_bodies.md                    PR 1·2·4 본문 (정우 review 용)
├── analysis/                       13 분석 문서 (Day 5-6)
├── manuscript/                     논문 §1-§7 IMRaD outline
├── slides/                         발표 슬라이드 + Q&A 20개
└── schema/                         DB schema SQL (W5+ 통합)
```

---

## 1. analysis/ — 13 분석 문서

| # | 파일 | 용도 |
|---|---|---|
| 00 | [00_index.md](analysis/00_index.md) | analysis 인덱스 |
| 01 | [01_manual_corrections.md](analysis/01_manual_corrections.md) | 메뉴얼 vs 정우 실제 11 정정 |
| 02 | [02_minseok_handle.md](analysis/02_minseok_handle.md) | 민석 모듈 A 미시작 fallback 전략 |
| 03 | [03_timeline.md](analysis/03_timeline.md) | D5 → W7 작업 매트릭스 |
| 04 | [04_team_repo_audit.md](analysis/04_team_repo_audit.md) | 정우 repo 완전 인벤토리 |
| 05 | [05_bd_integration.md](analysis/05_bd_integration.md) | Module C ↔ B/D 함수 호출 명세 |
| 06 | [06_module_c_build_plan.md](analysis/06_module_c_build_plan.md) | 데이터 8 + API 5 + 코드 6 tier |
| **07** | [07_expert_sessions.md](analysis/07_expert_sessions.md) | **Round 1: 5 전문가 deliberation** |
| 08 | [08_api_keys_setup.md](analysis/08_api_keys_setup.md) | 본인 명의 API 키 발급 |
| 09 | [09_module_e_handoff.md](analysis/09_module_e_handoff.md) | 정우 api_server.py 분석 |
| 10 | [10_module_c_focus.md](analysis/10_module_c_focus.md) | 종합 빌드 플랜 |
| **11** | [11_expert_sessions_round2.md](analysis/11_expert_sessions_round2.md) | **Round 2: 3 전문가 deliberation + 학술 발견** |
| 12 | [12_module_e_tool_spec.md](analysis/12_module_e_tool_spec.md) | 수범 LLM agent 5 tool 명세 |
| 13 | [13_jeongwoo_patterns_checklist.md](analysis/13_jeongwoo_patterns_checklist.md) | 정우 patterns 100% 모방 15/15 |

### 핵심 분석 통찰

- **메뉴얼 11 정정** (#01): 가이드 placeholder vs 정우 5/5 진짜 데이터
- **8 전문가 deliberation** (#07 + #11): 산림·경제·정책·경영·AI·위성·산주·통합자
- **종합 빌드 플랜** (#10): 19 src + 8 data + 160 tests(+shared 15=175) + 27 ADR(D101-D132)
- **정우 patterns 100%** (#13): 15/15 체크리스트 통과

---

## 2. manuscript/ — 논문

### `paper_outline_v1.md` (IMRaD §1-§7)

**Title (영문)**: A Faustmann–Hartman Korean Adaptation Captures KAU Market Inflection: A Decision-Support Framework for Forest Carbon Policy Based on Multi-Expert Deliberation

**Title (한글)**: Faustmann–Hartman 한국 변형으로 포착한 KAU 시장 변곡점: 5+1 학자 deliberation 기반 산림탄소 정책 의사결정 프레임워크

**구조**:
- §1 Introduction — 한국 산림 3 구조적 공백
- §2 Background — Faustmann + Hartman + 선행연구 13편
- §3 Data — 정우 5/5 + Module C 자체 데이터 8 종
- §4 Methods — 수식 + 6 시나리오 + LHS + HWP + 8 deliberation
- §5 Results — ⭐ **D115 KAU 변곡점** + D114 +45% gap
- §6 Discussion — 두 가설 비교 + Module A framing + Limitations
- §7 Conclusion + References 14편 + Appendix

**작성 일정**: W6 (6/12-18) §1-§5 완성, W7 (6/19-26) §6-§7 final.

---

## 3. slides/ — 발표 자료

### `v1_presentation.md` — 5분 7슬라이드 (Marp)
1. Title: "Faustmann-Hartman 한국 변형으로 포착한 KAU 시장 변곡점"
2. Problem: WTA hurdle 미돌파 시대의 한국 임업
3. Method: Faustmann-Hartman + 8 학자 deliberation
4. ⭐ **Finding A: D115 KAU 변곡점** (핵심 narrative)
5. Finding B: D114 인증-모델 +45% gap
6. Validation: NFI direct lookup + 175 tests
7. Conclusion + 정책 제언

### `QA_anticipated.md` — 20 Q&A 예상 답변 (Tier 1·2·3·4)
- Tier 1 (가장 예상): 위성 미사용, +45% 차이, KAU 변동, 민석 미시작, 6 시나리오 UX
- Tier 2 (학술 reviewer): Faustmann 식 적용, MC 수렴, Lognormal, HWP 한국 적용, 8 deliberation
- Tier 3 (정책 reviewer): 산림청 기여, 노령림 정책, 실 배포 가능성
- Tier 4 (트리키): AI 사용, 양 강조, 정우 vs 희도, 200만원 상금, 다음 단계
- Bonus: 5 추가

---

## 4. schema/ — DB schema (W5+ 통합 reference)

### `db_schema.sql`
PostgreSQL + PostGIS 7 schema (Manual 01 §06):
- spatial · inventory · economics · market · weather · carbon · legal

W5+ 통합 단계 시 적용. 현재는 reference 만.

---

## 5. PR_bodies.md — 정우 PR review 용

PR 1 (shared/schemas D101), PR 2 (module_c 첫 commit), PR 4 (api_server `/compute_lev` W5) 의 본문.

---

## 워크플로우

### 발표 (W7) 작성 시
1. `slides/v1_presentation.md` 7 슬라이드 finalize (Marp → PDF)
2. `slides/QA_anticipated.md` 20 Q&A 암기
3. 백업 영상 녹화 (5분 데모)

### 논문 (W6-W7) 작성 시
1. `manuscript/paper_outline_v1.md` outline → §1-§5 draft (W6)
2. References 14편 검증 + DOI 확인
3. §6-§7 final + Appendix (W7)

### PR review (W3 잔여) 시
1. `PR_bodies.md` 본문 → GitHub PR 생성
2. 정우 review 응답 + 수정 commit
3. merge 후 main 적용

---

## 인용

발표·논문 인용 시:
> Choi, H., et al. (2026). *A Faustmann–Hartman Korean Adaptation Captures KAU Market Inflection*. 충북 보은 산림경영 AI Agent 공모전. https://github.com/jwn6174-crypto/forest-ai-agent

---

## 변경 이력
- 2026-05-22 — _workspace 의 모든 학술·분석·발표·논문 산출물을 module_c/docs/ 로 통합 (정우 모듈 패턴 확장)
