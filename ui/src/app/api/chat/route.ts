import { GoogleGenerativeAI } from "@google/generative-ai";
import type { ForestAnalysisResult } from "@/lib/types";

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY ?? "");

function buildSystemPrompt(ctx: ForestAnalysisResult): string {
  const s = ctx.state;
  const best = ctx.scenarios?.find((sc) => sc.recommended);
  const bestName = best?.name ?? ctx.recommendation ?? "—";
  const bestNpv = best?.npv.p50 ?? 0;

  const scenarioLines = (ctx.scenarios ?? [])
    .map(
      (sc) =>
        `  (${sc.name}): 중앙값 ${sc.npv.p50.toLocaleString()}만원 (범위: ${sc.npv.p5.toLocaleString()}~${sc.npv.p95.toLocaleString()}만원)${sc.recommended ? " ✓권장" : ""}`
    )
    .join("\n");

  return `당신은 한국 산림경영 의사결정 지원 AI입니다. 아래 분석 결과를 기반으로 산주의 질문에 한국어로 친절하고 정확하게 답변하세요.

[임야 분석 결과]
PNU: ${s.pnu}
수종: ${s.species} | 추정 임령: ${s.estimatedAge}년 | 면적: ${s.areaHa}ha | 임종: ${s.forestType}
입목축적: ${s.volumePerHa} m³/ha (±${s.volumeUncertainty}) | 탄소저장량: ${s.carbonPerHa} tC/ha
등급 분포: 특용재 ${s.gradeDistribution.teukYongJae}% / 1등급 ${s.gradeDistribution.grade1}% / 2등급 ${s.gradeDistribution.grade2}% / 3등급 ${s.gradeDistribution.grade3}% / 원주재 ${s.gradeDistribution.wonJuJae}% / 원료재 ${s.gradeDistribution.wonRyoJae}%

[시나리오 30년 NPV]
${scenarioLines}

[권장 시나리오]: ${bestName} — 예상 NPV 약 ${bestNpv.toLocaleString()}만원

[KAU 현재가]: ${ctx.market.kauPrice.toLocaleString()}원/tCO₂ | [KOC 추정가]: ${ctx.market.kocEstimate.toLocaleString()}원/tCO₂
[할인율]: ${ctx.market.discountRate}% | [가격 기준일]: ${ctx.market.priceDate}

[탄소상쇄 등록 가능 유형]: ${ctx.offsetEligibility.matchedTypes.join(", ")}

[답변 지침]
- 항상 한국어로만 답변
- 수치 비교 시 구체적 금액 언급 (예: "약 9,200만원")
- 불확실성은 반드시 언급 ("이 수치는 가격 변동성을 반영한 추정값입니다")
- 산주가 이해하기 쉬운 일상 언어 사용
- 정확한 수익 보장 표현 금지 — 시나리오 비교임을 명시
- 전문 용어 사용 시 괄호 안에 쉬운 설명 추가`;
}

export async function POST(request: Request) {
  const { messages, context } = (await request.json()) as {
    messages: { role: "user" | "assistant"; content: string }[];
    context: ForestAnalysisResult;
  };

  if (!process.env.GEMINI_API_KEY) {
    return new Response("GEMINI_API_KEY가 설정되지 않았습니다.", { status: 503 });
  }

  // 마지막 메시지 (현재 질문)
  const lastMsg = messages[messages.length - 1];
  // 이전 대화 히스토리 (Gemini: role은 "user" | "model")
  const history = messages.slice(0, -1).map((m) => ({
    role: m.role === "assistant" ? "model" : "user",
    parts: [{ text: m.content }],
  }));

  const model = genAI.getGenerativeModel({
    model: "gemini-2.0-flash",
    systemInstruction: buildSystemPrompt(context),
  });

  const chat = model.startChat({ history });
  const result = await chat.sendMessageStream(lastMsg.content);

  const readable = new ReadableStream({
    async start(controller) {
      try {
        for await (const chunk of result.stream) {
          const text = chunk.text();
          if (text) {
            controller.enqueue(new TextEncoder().encode(text));
          }
        }
      } finally {
        controller.close();
      }
    },
  });

  return new Response(readable, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "no-cache",
      "X-Accel-Buffering": "no",
    },
  });
}
