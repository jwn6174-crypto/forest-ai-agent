"use client";
import { useState, useCallback } from "react";
import type { ForestAnalysisResult, ModuleStatus, PartialResult } from "@/lib/types";
import { analyzeForest } from "@/lib/api-client";

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

const IDLE: ModuleStatus = { A: "idle", B: "idle", C: "idle", D: "idle", E: "idle" };

export function useForestAnalysis() {
  const [moduleStatus, setModuleStatus] = useState<ModuleStatus>(IDLE);
  const [partial, setPartial] = useState<PartialResult | null>(null);
  const [fullResult, setFullResult] = useState<ForestAnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isChatReady, setIsChatReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyze = useCallback(async (pnu: string, risk: string) => {
    setIsAnalyzing(true);
    setIsChatReady(false);
    setError(null);
    setPartial(null);
    setFullResult(null);
    setModuleStatus({ A: "loading", B: "idle", C: "idle", D: "idle", E: "idle" });

    try {
      // API는 즉시 전체 데이터 반환 — UI가 단계적으로 노출
      const data = await analyzeForest(pnu, risk);

      // Module A 완료 (2.4초): 현재 상태 노출
      await sleep(2400);
      setModuleStatus({ A: "done", B: "loading", C: "idle", D: "idle", E: "idle" });
      setPartial({ pnu, state: data.state });

      // Module B 완료 (1.6초): 성장 예측 노출
      await sleep(1600);
      // Module C는 미구현 — "idle" 유지, scenarios=null 노출
      setModuleStatus({ A: "done", B: "done", C: "idle", D: "loading", E: "idle" });
      setPartial((p) => ({ ...p!, growth: data.growth, scenarios: data.scenarios ?? null }));

      // Module D 완료 (0.6초): 시장 데이터 노출
      await sleep(600);
      setModuleStatus({ A: "done", B: "done", C: "idle", D: "done", E: "loading" });
      setPartial((p) => ({
        ...p!,
        market: data.market,
        recommendation: data.recommendation,
        offsetEligibility: data.offsetEligibility,
      }));

      // 전체 결과 set + LLM Agent 준비
      setFullResult(data);

      await sleep(400);
      setModuleStatus({ A: "done", B: "done", C: "idle", D: "done", E: "done" });
      setIsChatReady(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "분석 중 오류가 발생했습니다");
      setModuleStatus((prev) => {
        const key = Object.entries(prev).find(([, v]) => v === "loading")?.[0] as
          | keyof ModuleStatus
          | undefined;
        if (!key) return prev;
        return { ...prev, [key]: "error" };
      });
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  const reset = useCallback(() => {
    setModuleStatus(IDLE);
    setPartial(null);
    setFullResult(null);
    setIsAnalyzing(false);
    setIsChatReady(false);
    setError(null);
  }, []);

  return {
    moduleStatus,
    partial,
    fullResult,
    isAnalyzing,
    isChatReady,
    error,
    analyze,
    reset,
  };
}
