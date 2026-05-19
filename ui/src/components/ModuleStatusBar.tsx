"use client";
import type { ModuleStatus } from "@/lib/types";
import { CheckCircle2, Loader2, Circle, AlertCircle } from "lucide-react";
import clsx from "clsx";

const MODULE_LABELS: Record<keyof ModuleStatus, string> = {
  A: "A: 위성 추정",
  B: "B: 성장 예측",
  C: "C: LEV 계산 ·준비중",
  D: "D: 시장 데이터",
  E: "E: AI 분석",
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

export default function ModuleStatusBar({ status }: { status: ModuleStatus }) {
  return (
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
  );
}
