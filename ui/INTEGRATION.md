# UI ↔ 백엔드 통합 가이드 (수범 전달용)

이 문서는 Next.js `ui` 와 Python `api_server.py` 가 어떻게 맞물려 도는지, 무엇이
이미 준비되었고 무엇을 더 다듬으면 되는지를 정리한다. 2026-06-05 통합 점검에서
A·B·C·D 네 모듈을 잇는 백엔드 계약을 검증하고, UI 쪽에서 끊겨 있던 연결 몇 군데를
고쳤다. 그 결과 산주가 PNU 를 넣고 "분석 시작" 을 누르면, 위성 추정부터 Faustmann
경제성·추천까지가 하나의 응답으로 약 0.4초 만에 화면에 흐른다.

---

## 1. 두 서버를 띄우는 법

UI 는 자기 자신(Next.js)과 Python 분석 서버, 두 프로세스를 함께 띄워야 동작한다.

```bash
# 1) Python 분석 서버 (포트 8001) — A·B·C·D 통합 엔진
cd forest-ai-agent
python api_server.py            # 또는 uvicorn api_server:app --port 8001 --reload

# 2) Next.js UI (포트 3000)
cd ui
npm install                     # 최초 1회
npm run dev
```

필요한 환경변수:

| 위치 | 변수 | 용도 | 기본값 |
|---|---|---|---|
| `ui/.env.local` | `PYTHON_API_URL` | Next.js → Python 서버 주소 | `http://localhost:8001` |
| `ui` 실행 환경 | `ANTHROPIC_API_KEY` | 채팅(Module E LLM)용 | (필수) |
| Python 실행 환경 | `UI_MC_SAMPLES` | `/analyze` 의 Monte Carlo 샘플 수 | `300` |

> Python 서버는 부팅 시 약 10초 동안 캐시를 데운다(KAU 시세·임분수확표·Module C
> 파이프라인 워밍). 이 워밍 덕분에 **첫 사용자 요청부터 약 0.4초**로 응답한다. 워밍
> 로그(`[startup] 캐시 워밍 완료`)가 뜬 뒤 UI 를 사용하면 된다.

---

## 2. 데이터 흐름 한눈에

```
PNUInput (pnu, risk)
  └─ useForestAnalysis.analyze(pnu, risk)
       └─ api-client.analyzeForest()  →  POST /api/analyze   (Next.js route)
            └─ route.ts  →  POST http://localhost:8001/analyze  (Python)
                 └─ api_server.analyze()
                      A(mock) → B growth_predict → C compute_lev_with_plan → D market
                      → stand_adapter → ui_adapter → ForestAnalysisResult(JSON)
```

응답은 한 번에 전부 오지만, `useForestAnalysis` 가 A→B→C→D→E 순서로 **단계적으로
노출**해 분석이 진행되는 듯한 연출을 만든다. 실제 계산은 이미 끝나 있으므로 이
연출 타이밍(`sleep` 값)은 자유롭게 조정해도 된다.

---

## 3. 엔드포인트 계약

### `POST /analyze`

요청:

```json
{ "pnu": "4374033021100010001", "riskPreference": "balanced" }
```

- `riskPreference` 는 `"safe" | "balanced" | "profit"` 셋 중 하나. 백엔드가
  각각 위험회피·균형·수익극대화 선호로 Module C 추천에 반영한다. (그 외 값은
  안전하게 `balanced` 로 처리)

응답: `types.ts` 의 `ForestAnalysisResult` 와 1:1 대응한다.

```jsonc
{
  "pnu": "...",
  "analyzedAt": "2026-06-05T00:00:00Z",
  "state":   { /* ForestState — Module A·B */ },
  "growth":  { /* GrowthForecast — Module B */ },
  "market":  { /* MarketData — Module D */ },
  "scenarios": [ /* Scenario[6] — Module C, 아래 표 */ ],
  "recommendation": "thinning",          // 권장 시나리오 id
  "offsetEligibility": { /* OffsetEligibility */ }
}
```

`scenarios` 6개의 `id` 와 의미:

| id | 시나리오 | 의미 |
|---|---|---|
| `immediate` | 즉시 벌채 | 지금 수확 |
| `five_year` | 5년 후 | 5년 더 키우고 수확 |
| `ten_year` | 10년 후 | 10년 더 키우고 수확 |
| `koc` | 연장+탄소 | 벌기연장 + 산림탄소상쇄(KOC) |
| `ntfp` | 임산물 | 표고·산나물 등 비목재 수입 |
| `thinning` | 간벌+10년 | 간벌 보조 + 10년 연장 |

각 `Scenario` 의 금액 필드(`npv.p5/p50/p95`, `timberRevenue` 등)는 **만원 단위**다
(`ui_adapter` 가 원→만원 변환). `npv.bankruptcyProb` 는 NPV<0 확률, `paretoX` 는
유동성 점수(0=장기, 1=즉시)다.

### `GET /health`

```json
{ "status": "ok", "modules": { "A": "mock", "B": "...(live)", "C": "Faustmann-Hartman (live)", "D": "...(live)" } }
```

---

## 4. 이번 점검에서 고친 UI 연결 (이미 반영됨)

산주의 위험선호와 Module C 상태 표시가 끊겨 있어 바로잡았다.

1. **위험선호 전달 복구** — `api/analyze/route.ts` 가 `pnu` 만 백엔드로 넘기고
   `riskPreference` 를 누락하고 있었다. 이제 함께 전달한다.
2. **위험선호 값 정렬** — `PNUInput` 의 선택값이 `low/medium/high` 였는데 백엔드는
   `safe/balanced/profit` 를 기대해 항상 '균형'으로 처리됐다. UI 를 `safe/balanced/
   profit`(안정/균형/수익)로 맞췄다.
3. **Module C 상태 반영** — `useForestAnalysis` 가 C 를 영구 `idle`("미구현")로 두던
   것을, 시나리오 수신 시 `loading→done`(실패 시 `error`)으로 표시하도록 고쳤다.
4. **빈 상태 문구 정정** — `ScenarioTable·ParetoChart·ScenarioNPVChart` 의 "Module C
   개발 중" 자리표시자를, 이제는 백엔드 응답 실패 시에만 뜨므로 "경제성 분석 결과
   없음(서버 확인)" 으로 바꿨다. `ModuleStatusBar` 의 "C: LEV 계산 ·준비중" → "C:
   경제성 분석".

---

## 5. 수범이 이어서 다듬으면 좋은 것

- **채팅 프롬프트 라벨** — `api/chat/route.ts` 의 시스템 프롬프트가 "[5개 시나리오]"
  라고 적혀 있으나 실제는 6개다. 또 `ctx.scenarios` 가 null 일 때(백엔드 실패)
  `.find/.map` 가 터질 수 있으니 가드 한 줄을 권한다.
- **로딩 연출 타이밍** — 실제 계산이 0.4초면 끝나므로, A·B·C·D 단계 노출 `sleep`
  값을 줄이면 더 빠릿한 체감을 줄 수 있다(현재는 의도적 연출).
- **에러 UX** — Python 서버 미기동 시 route 가 503 을 주고 `analyze` 가 throw 한다.
  사용자 안내 토스트/배너를 붙이면 데모 안정성이 올라간다.
- **그래프 고도화** — `CarbonCurveChart·GradeDistributionChart` 는 `growth` 필드로,
  `ParetoChart·ScenarioNPVChart` 는 `scenarios` 로 이미 그려진다. 색·툴팁·단위
  표기를 발표용으로 다듬는 여지가 있다.

---

## 6. 빠른 점검 체크리스트

- [ ] `python api_server.py` 가 `[startup] 캐시 워밍 완료` 를 출력하는가
- [ ] `curl localhost:8001/health` 가 `C: "Faustmann-Hartman (live)"` 를 주는가
- [ ] UI 에서 데모 PNU 로 "분석 시작" → 6개 시나리오 표·NPV 차트·파레토가 뜨는가
- [ ] 위험선호를 바꿔도 정상 응답하는가(추천이 같을 수는 있으나 오류는 없어야)
- [ ] 채팅이 분석 결과를 인용해 답하는가(`ANTHROPIC_API_KEY` 필요)

*최종 갱신: 2026-06-05 — A·B·C·D·api_server·ui 통합 점검 및 계약 정렬 완료*
