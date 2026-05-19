"use client";
import type { ForestState } from "@/lib/types";
import { TreePine, MapPin, AlertTriangle, Info } from "lucide-react";

const GRADE_COLORS: Record<string, string> = {
  teukYongJae: "bg-[#2a4830]",
  grade1:      "bg-[#3a6240]",
  grade2:      "bg-[#4a7a52]",
  grade3:      "bg-[#5e8e65]",
  wonJuJae:    "bg-[#7a9878]",
  wonRyoJae:   "bg-[#96a890]",
};
const GRADE_LABELS: Record<string, string> = {
  teukYongJae: "특용재",
  grade1: "1등급",
  grade2: "2등급",
  grade3: "3등급",
  wonJuJae: "원주재",
  wonRyoJae: "원료재",
};

// 수확표 데이터 품질 뱃지
function MethodBadge({ method }: { method?: string }) {
  if (!method) return null;
  const cfg =
    method === "exact"
      ? { label: "정밀값",  cls: "bg-[#1e3820]/80 text-[#6aab70] border-[#2d5230]" }
      : method.startsWith("interpolat")
      ? { label: "보간값",  cls: "bg-[#3a2e10]/80 text-[#887228] border-[#554a1a]" }
      : method.startsWith("extrapol")
      ? { label: "외삽값",  cls: "bg-red-950/60  text-red-400/80  border-red-800/40" }
      : { label: method,    cls: "bg-forest-900/70 text-forest-500 border-forest-700" };

  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded border font-medium ${cfg.cls}`}>
      {cfg.label}
    </span>
  );
}

function Skeleton() {
  return (
    <div className="space-y-3 animate-pulse">
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-5 bg-forest-800 rounded w-full" />
      ))}
      <div className="h-4 bg-forest-800 rounded w-3/4" />
    </div>
  );
}

export default function ForestStateCard({ state }: { state?: ForestState }) {
  if (!state) return (
    <div className="bg-black/45 backdrop-blur-md border border-white/10 shadow-xl rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <TreePine className="w-4 h-4 text-forest-500" />
        <span className="text-sm font-semibold text-forest-400">현재 임야 상태</span>
      </div>
      <Skeleton />
    </div>
  );

  const gradeEntries = Object.entries(state.gradeDistribution) as [
    keyof typeof GRADE_COLORS,
    number
  ][];

  return (
    <div className="bg-black/45 backdrop-blur-md border border-white/10 shadow-xl rounded-xl p-4 space-y-4 animate-slide-up">

      {/* 헤더 */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <TreePine className="w-4 h-4 text-forest-300" />
          <span className="text-sm font-semibold text-forest-100">현재 임야 상태</span>
          <MethodBadge method={state.dataMethod} />
        </div>
        <div className="flex items-center gap-1 text-xs text-forest-500">
          <MapPin className="w-3 h-3" />
          <span>{state.coordinates.lat.toFixed(2)}°N {state.coordinates.lng.toFixed(2)}°E</span>
        </div>
      </div>

      {/* 핵심 지표 — 3열 */}
      <div className="grid grid-cols-3 gap-2">
        <Stat label="수종"     value={state.species}            unit=""        accent colSpan />
        <Stat label="임령"     value={`${state.estimatedAge}`} unit="년" />
        <Stat label="지위지수" value={`SI ${state.siteIndex}`} unit="" />
        <Stat
          label="입목축적"
          value={`${state.volumePerHa}`}
          unit="m³/ha"
          sub={`±${state.volumeUncertainty}`}
        />
        <Stat label="수고"     value={`${state.heightNow ?? "—"}`} unit="m" />
        <Stat label="ha당 본수" value={state.nPerHaNow ? Math.round(state.nPerHaNow).toLocaleString() : "—"} unit="본" />
        <Stat label="탄소저장량" value={`${state.carbonPerHa}`} unit="tCO₂/ha" />
        <Stat label="면적"      value={`${state.areaHa}`}       unit="ha" />
        <Stat label="tMAI"     value={`${state.tmaiNow ?? "—"}`} unit="m³/ha/yr"
              tooltip="총평균재적생장량 — 임분 생산성 지표" />
      </div>

      {/* 등급별 재적 분포 바 */}
      <div>
        <p className="text-xs text-forest-500 mb-2">등급별 재적 분포</p>
        <div className="flex h-4 rounded overflow-hidden gap-0.5">
          {gradeEntries.map(([key, pct]) =>
            pct > 0 ? (
              <div
                key={key}
                className={`${GRADE_COLORS[key]} transition-all duration-500`}
                style={{ width: `${pct}%` }}
                title={`${GRADE_LABELS[key]}: ${pct}%`}
              />
            ) : null
          )}
        </div>
        <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2">
          {gradeEntries.map(([key, pct]) => (
            <span key={key} className="flex items-center gap-1 text-xs text-forest-400">
              <span className={`w-2 h-2 rounded-sm ${GRADE_COLORS[key]}`} />
              {GRADE_LABELS[key]} {pct}%
            </span>
          ))}
        </div>
      </div>

      {/* 경고 또는 안내 */}
      {state.dataWarning ? (
        <div className="flex items-start gap-1.5 p-2 rounded-lg bg-[#3a2e10]/60 border border-[#554a1a]/60">
          <AlertTriangle className="w-3.5 h-3.5 text-[#887228] mt-0.5 shrink-0" />
          <p className="text-xs text-[#a89040]">{state.dataWarning}</p>
        </div>
      ) : (
        <div className="flex items-start gap-1.5 p-2 rounded-lg bg-white/10 border border-white/10">
          <AlertTriangle className="w-3.5 h-3.5 text-forest-600 mt-0.5 shrink-0" />
          <p className="text-xs text-forest-400">
            위성 기반 추정값. 소면적 임지(&lt;1ha)는 ±값이 커질 수 있습니다.
          </p>
        </div>
      )}
    </div>
  );
}

function Stat({
  label, value, unit, sub, accent, colSpan, tooltip,
}: {
  label: string;
  value: string;
  unit: string;
  sub?: string;
  accent?: boolean;
  colSpan?: boolean;
  tooltip?: string;
}) {
  return (
    <div className={`bg-white/10 rounded-lg px-3 py-2 ${colSpan ? "col-span-1" : ""}`}>
      <div className="flex items-center gap-1 mb-0.5">
        <p className="text-xs text-forest-500">{label}</p>
        {tooltip && (
          <span title={tooltip} className="cursor-help">
            <Info className="w-2.5 h-2.5 text-forest-600" />
          </span>
        )}
      </div>
      <p className={`text-sm font-semibold ${accent ? "text-forest-200" : "text-forest-100"}`}>
        {value}
        {unit && <span className="text-xs font-normal text-forest-400 ml-1">{unit}</span>}
        {sub && <span className="text-xs text-forest-500 ml-1">{sub}</span>}
      </p>
    </div>
  );
}
