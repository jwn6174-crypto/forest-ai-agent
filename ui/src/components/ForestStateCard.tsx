"use client";
import type { ForestState } from "@/lib/types";
import { TreePine, MapPin, AlertTriangle } from "lucide-react";

const GRADE_COLORS: Record<string, string> = {
  teukYongJae: "bg-emerald-600",
  grade1: "bg-emerald-500",
  grade2: "bg-green-500",
  grade3: "bg-green-400",
  wonJuJae: "bg-lime-500",
  wonRyoJae: "bg-lime-400",
};
const GRADE_LABELS: Record<string, string> = {
  teukYongJae: "특용재",
  grade1: "1등급",
  grade2: "2등급",
  grade3: "3등급",
  wonJuJae: "원주재",
  wonRyoJae: "원료재",
};

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
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <TreePine className="w-4 h-4 text-forest-300" />
          <span className="text-sm font-semibold text-forest-100">현재 임야 상태</span>
        </div>
        <div className="flex items-center gap-1 text-xs text-forest-500">
          <MapPin className="w-3 h-3" />
          <span>{state.coordinates.lat.toFixed(2)}°N {state.coordinates.lng.toFixed(2)}°E</span>
        </div>
      </div>

      {/* 핵심 지표 */}
      <div className="grid grid-cols-2 gap-3">
        <Stat label="수종" value={state.species} unit="" accent />
        <Stat label="추정 임령" value={`${state.estimatedAge}`} unit="년" />
        <Stat
          label="입목축적"
          value={`${state.volumePerHa}`}
          unit={`m³/ha`}
          sub={`±${state.volumeUncertainty}`}
        />
        <Stat label="탄소저장량" value={`${state.carbonPerHa}`} unit="tC/ha" />
        <Stat label="임야 면적" value={`${state.areaHa}`} unit="ha" />
        <Stat label="임종" value={state.forestType} unit="" />
      </div>

      {/* 등급별 재적 분포 */}
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

      {/* 불확실성 안내 */}
      <div className="flex items-start gap-1.5 p-2 rounded-lg bg-white/10 border border-white/10">
        <AlertTriangle className="w-3.5 h-3.5 text-amber-500 mt-0.5 shrink-0" />
        <p className="text-xs text-forest-400">
          위성 기반 추정값. 소면적 임지(&lt;1ha)는 ±값이 커질 수 있습니다.
        </p>
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  unit,
  sub,
  accent,
}: {
  label: string;
  value: string;
  unit: string;
  sub?: string;
  accent?: boolean;
}) {
  return (
    <div className="bg-white/10 rounded-lg px-3 py-2">
      <p className="text-xs text-forest-500 mb-0.5">{label}</p>
      <p className={`text-sm font-semibold ${accent ? "text-forest-200" : "text-forest-100"}`}>
        {value}
        {unit && <span className="text-xs font-normal text-forest-400 ml-1">{unit}</span>}
        {sub && <span className="text-xs text-forest-500 ml-1">{sub}</span>}
      </p>
    </div>
  );
}
