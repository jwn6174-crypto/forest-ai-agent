"use client";
import type { ModuleStatus } from "@/lib/types";
import { CheckCircle2, Loader2, Circle, AlertCircle } from "lucide-react";
import clsx from "clsx";

const MODULE_LABELS: Record<keyof ModuleStatus, string> = {
  A: "A: 위성 추정",
  B: "B: 성장 예측",
  C: "C: NPV 시나리오",
  D: "D: 시장 데이터",
  E: "E: AI 분석",
};

// 각 모듈이 완료됐을 때 전체 진행률 (%)
const MODULE_PROGRESS: Record<keyof ModuleStatus, number> = {
  A: 18,
  B: 38,
  C: 62,
  D: 82,
  E: 100,
};

// 모듈별 현재 작업 설명
const MODULE_DESC: Record<keyof ModuleStatus, string> = {
  A: "위성 영상에서 입목축적·탄소량 추정 중...",
  B: "임분수확표 기반 30년 성장 예측 중...",
  C: "Faustmann-Hartman NPV 시나리오 계산 중...",
  D: "KOFPI 목재가격 · KAU 탄소배출권 조회 중...",
  E: "AI 분석 결과 정리 중...",
};

function StatusIcon({ status }: { status: ModuleStatus[keyof ModuleStatus] }) {
  if (status === "loading")
    return <Loader2 className="w-3.5 h-3.5 animate-spin text-forest-300" />;
  if (status === "done")
    return <CheckCircle2 className="w-3.5 h-3.5 text-forest-300" />;
  if (status === "error")
    return <AlertCircle className="w-3.5 h-3.5 text-red-400" />;
  return <Circle className="w-3.5 h-3.5 text-forest-600" />;
}

function calcProgress(status: ModuleStatus): number {
  const keys = Object.keys(MODULE_LABELS) as (keyof ModuleStatus)[];
  let pct = 0;
  for (const k of keys) {
    if (status[k] === "done" || status[k] === "error") {
      pct = MODULE_PROGRESS[k];
    } else if (status[k] === "loading") {
      // 로딩 중인 모듈의 이전 단계까지만 채움 + 약간의 여유
      const prev = keys[keys.indexOf(k) - 1];
      const base = prev ? MODULE_PROGRESS[prev] : 0;
      const next = MODULE_PROGRESS[k];
      pct = base + Math.round((next - base) * 0.3);
      break;
    }
  }
  return pct;
}

function getActiveDesc(status: ModuleStatus): string {
  const keys = Object.keys(MODULE_LABELS) as (keyof ModuleStatus)[];
  for (const k of keys) {
    if (status[k] === "loading") return MODULE_DESC[k];
  }
  return "";
}

function isAnalyzing(status: ModuleStatus): boolean {
  return Object.values(status).some((v) => v === "loading");
}

function isDone(status: ModuleStatus): boolean {
  return status.E === "done";
}

export default function ModuleStatusBar({ status }: { status: ModuleStatus }) {
  const analyzing = isAnalyzing(status);
  const done = isDone(status);
  const progress = calcProgress(status);
  const desc = getActiveDesc(status);
  const allIdle = Object.values(status).every((v) => v === "idle");

  return (
    <div className="space-y-2">
      {/* 진행률 바 — 분석 중이거나 완료 시 표시 */}
      {!allIdle && (
        <div className="space-y-1">
          {/* 상단: 설명 텍스트 + 퍼센트 */}
          <div className="flex items-center justify-between">
            <p className="text-xs text-forest-400 truncate">
              {done
                ? "✅ 분석 완료"
                : analyzing
                ? desc
                : "분석 준비 중..."}
            </p>
            <span className="text-xs font-medium text-forest-300 tabular-nums ml-2 shrink-0">
              {progress}%
            </span>
          </div>

          {/* 진행률 바 */}
          <div className="h-1.5 w-full bg-forest-800 rounded-full overflow-hidden">
            <div
              className={clsx(
                "h-full rounded-full transition-all duration-700 ease-out",
                done
                  ? "bg-forest-400"
                  : "bg-gradient-to-r from-forest-500 to-forest-300"
              )}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* 모듈 칩 */}
      <div className="flex items-center gap-2 flex-wrap">
        {(Object.keys(MODULE_LABELS) as (keyof ModuleStatus)[]).map((key) => (
          <div
            key={key}
            className={clsx(
              "flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-all duration-300",
              status[key] === "done" &&
                "bg-forest-800 border-forest-500 text-forest-200",
              status[key] === "loading" &&
                "bg-forest-800 border-forest-400 text-forest-100 shadow-[0_0_8px_rgba(106,171,112,0.3)]",
              status[key] === "idle" &&
                "bg-forest-900 border-forest-700 text-forest-600",
              status[key] === "error" &&
                "bg-red-950/70 border-red-700 text-red-300"
            )}
          >
            <StatusIcon status={status[key]} />
            {MODULE_LABELS[key]}
          </div>
        ))}
      </div>
    </div>
  );
}
