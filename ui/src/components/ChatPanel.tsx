"use client";
import { useState, useRef, useEffect, useCallback } from "react";
import type { ChatMessage, ForestAnalysisResult } from "@/lib/types";
import { Send, Bot, User, Loader2 } from "lucide-react";
import clsx from "clsx";
import { streamChat } from "@/lib/api-client";

const INITIAL_PROMPT =
  "이 임야의 분석 결과를 요약하고, 권장 시나리오와 그 이유를 쉽게 설명해주세요. 산주 입장에서 가장 중요한 점 3가지도 알려주세요.";

export default function ChatPanel({
  analysisResult,
  isReady,
}: {
  analysisResult?: ForestAnalysisResult;
  isReady: boolean;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const initialTriggered = useRef(false);

  const scrollToBottom = () => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!analysisResult || isStreaming) return;

      const userMsg: ChatMessage = {
        id: Date.now().toString(),
        role: "user",
        content: text,
        timestamp: new Date(),
      };

      const assistantId = (Date.now() + 1).toString();
      const assistantMsg: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsStreaming(true);
      setInput("");

      try {
        const history = [...messages, userMsg].map((m) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          timestamp: m.timestamp,
        }));

        let fullText = "";
        for await (const chunk of streamChat(history, analysisResult)) {
          fullText += chunk;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, content: fullText } : m
            )
          );
        }
      } catch {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: "죄송합니다. 오류가 발생했습니다. 다시 시도해주세요." }
              : m
          )
        );
      } finally {
        setIsStreaming(false);
      }
    },
    [analysisResult, isStreaming, messages]
  );

  // 분석 완료 시 자동으로 첫 메시지 전송
  useEffect(() => {
    if (isReady && analysisResult && !initialTriggered.current) {
      initialTriggered.current = true;
      sendMessage(INITIAL_PROMPT);
    }
  }, [isReady, analysisResult, sendMessage]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming || !isReady) return;
    sendMessage(input.trim());
  };

  return (
    <div className="bg-black/50 backdrop-blur-md border border-white/10 shadow-2xl rounded-2xl flex flex-col h-full">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-white/40">
        <Bot className="w-4 h-4 text-forest-300" />
        <span className="text-sm font-semibold text-forest-100">MOFOM.chat</span>
        {isStreaming && (
          <span className="flex items-center gap-1 text-xs text-forest-400 ml-auto">
            <Loader2 className="w-3 h-3 animate-spin" />
            답변 생성 중
          </span>
        )}
      </div>

      {/* 메시지 목록 */}
      <div className="flex-1 overflow-y-auto chat-scroll p-3 space-y-3 min-h-0">
        {messages.length === 0 && !isReady && (
          <div className="flex items-center justify-center h-full">
            <p className="text-sm text-forest-600 text-center px-4">
              임야를 분석하면 AI가 결과를 설명하고 질문에 답변합니다.
            </p>
          </div>
        )}

        {messages.length === 0 && isReady && (
          <div className="flex items-center justify-center h-full">
            <div className="flex gap-0.5">
              <span className="dot-1 w-2 h-2 rounded-full bg-forest-400 inline-block" />
              <span className="dot-2 w-2 h-2 rounded-full bg-forest-400 inline-block" />
              <span className="dot-3 w-2 h-2 rounded-full bg-forest-400 inline-block" />
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={clsx(
              "flex gap-2 animate-fade-in",
              msg.role === "user" && "flex-row-reverse"
            )}
          >
            <div className={clsx(
              "w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5",
              msg.role === "assistant" ? "bg-forest-700" : "bg-forest-600"
            )}>
              {msg.role === "assistant" ? (
                <Bot className="w-3.5 h-3.5 text-forest-200" />
              ) : (
                <User className="w-3.5 h-3.5 text-forest-200" />
              )}
            </div>
            <div className={clsx(
              "max-w-[85%] rounded-xl px-3 py-2 text-sm leading-relaxed",
              msg.role === "assistant"
                ? "bg-white/10 text-forest-100 rounded-tl-sm"
                : "bg-forest-600 text-white rounded-tr-sm"
            )}>
              {msg.content ? (
                <p className="whitespace-pre-wrap">
                  {msg.content}
                  {isStreaming &&
                    msg.id === messages[messages.length - 1]?.id &&
                    msg.role === "assistant" && (
                      <span className="typing-cursor" />
                    )}
                </p>
              ) : (
                <span className="typing-cursor text-forest-500" />
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* 빠른 질문 버튼 */}
      {isReady && messages.length > 0 && (
        <div className="px-3 pb-2 flex flex-wrap gap-1.5">
          {[
            "KOC 등록 절차를 알려주세요",
            "지금 당장 얼마를 받을 수 있나요?",
            "탄소가격이 올라가면 어떻게 되나요?",
          ].map((q) => (
            <button
              key={q}
              onClick={() => sendMessage(q)}
              disabled={isStreaming}
              className="text-xs px-2.5 py-1 rounded-full bg-forest-800 hover:bg-forest-700 text-forest-300 border border-forest-700 hover:border-forest-500 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* 입력창 */}
      <form
        onSubmit={handleSubmit}
        className="flex gap-2 p-3 border-t border-white/40"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={!isReady || isStreaming}
          placeholder={
            !isReady
              ? "임야 분석 후 질문 가능합니다"
              : "궁금한 점을 물어보세요..."
          }
          className={clsx(
            "flex-1 px-3 py-2 rounded-lg text-sm",
            "bg-forest-850 border border-forest-700 text-forest-100",
            "placeholder:text-forest-600 focus:outline-none focus:border-forest-500",
            "disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          )}
        />
        <button
          type="submit"
          disabled={!input.trim() || !isReady || isStreaming}
          className={clsx(
            "w-9 h-9 flex items-center justify-center rounded-lg",
            "bg-forest-500 hover:bg-forest-400 text-white",
            "disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          )}
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
