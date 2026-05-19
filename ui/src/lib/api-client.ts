import type { ForestAnalysisResult, ChatMessage } from "./types";

export async function analyzeForest(
  pnu: string,
  riskPreference: string
): Promise<ForestAnalysisResult> {
  const res = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pnu, riskPreference }),
  });
  if (!res.ok) throw new Error("분석 API 오류");
  return res.json();
}

export async function* streamChat(
  messages: ChatMessage[],
  context: ForestAnalysisResult
): AsyncGenerator<string> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages: messages.map((m) => ({ role: m.role, content: m.content })),
      context,
    }),
  });
  if (!res.ok || !res.body) throw new Error("채팅 API 오류");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    yield decoder.decode(value, { stream: true });
  }
}
