"use client";
import type { Scenario } from "@/lib/types";
import {
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from "recharts";

const SCENARIO_COLORS: Record<string, string> = {
  immediate:  "#b85a28",   // 러스트 (즉시 수확)
  five_year:  "#887228",   // 올리브 골드
  ten_year:   "#4a7c52",   // 포레스트 그린
  koc:        "#3f6480",   // 슬레이트 블루 (탄소)
  ntfp:       "#6b4e7a",   // 더스티 모브 (비목재)
};

const CustomBar = (props: {
  x?: number; y?: number; width?: number; height?: number;
  p5?: number; p95?: number; scaleY?: number; zeroY?: number;
  fill?: string; recommended?: boolean;
}) => {
  const { x = 0, y = 0, width = 0, height = 0, fill = "#22c55e", recommended } = props;
  const cx = x + width / 2;
  const p5y = props.p5 !== undefined && props.scaleY !== undefined && props.zeroY !== undefined
    ? props.zeroY - props.p5 * props.scaleY
    : y + height;
  const p95y = props.p95 !== undefined && props.scaleY !== undefined && props.zeroY !== undefined
    ? props.zeroY - props.p95 * props.scaleY
    : y;

  return (
    <g>
      {recommended && (
        <rect x={x - 2} y={Math.min(y, p95y) - 4} width={width + 4}
          height={Math.abs(height) + Math.abs(y - p95y) + 8}
          fill={fill} fillOpacity={0.08} rx={4} />
      )}
      <rect x={x} y={y} width={width} height={height} fill={fill} fillOpacity={0.85} rx={3} />
      <line x1={cx} y1={p5y} x2={cx} y2={p95y} stroke={fill} strokeWidth={1.5} strokeDasharray="3,2" />
      <line x1={cx - 6} y1={p95y} x2={cx + 6} y2={p95y} stroke={fill} strokeWidth={1.5} />
      <line x1={cx - 6} y1={p5y} x2={cx + 6} y2={p5y} stroke={fill} strokeWidth={1.5} />
    </g>
  );
};

const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: {payload: Scenario & {p50: number}}[] }) => {
  if (!active || !payload?.[0]) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-forest-800 border border-forest-600 rounded-lg p-3 text-xs space-y-1 shadow-xl">
      <p className="font-semibold text-forest-100">{d.name}</p>
      <p className="text-forest-400">{d.description}</p>
      <div className="border-t border-forest-700 pt-1 mt-1 space-y-0.5">
        <p><span className="text-forest-400">중앙값:</span> <span className="text-forest-100 font-medium">{d.npv.p50.toLocaleString()}만원</span></p>
        <p><span className="text-forest-400">범위(5~95%):</span> <span className="text-forest-200">{d.npv.p5.toLocaleString()} ~ {d.npv.p95.toLocaleString()}만원</span></p>
        <p><span className="text-forest-400">손실 확률:</span> <span className="text-amber-400">{(d.npv.bankruptcyProb * 100).toFixed(0)}%</span></p>
        {d.kocEligible && <p className="text-blue-400">✓ KOC 등록 가능</p>}
      </div>
    </div>
  );
};

function Skeleton() {
  return (
    <div className="h-full flex items-end gap-4 px-8 pb-8 animate-pulse">
      {[60, 75, 90, 40, 70].map((h, i) => (
        <div key={i} className="flex-1 bg-forest-800 rounded-t" style={{ height: `${h}%` }} />
      ))}
    </div>
  );
}

function PendingModuleC() {
  return (
    <div className="h-52 flex flex-col items-center justify-center gap-2 text-forest-500">
      <div className="text-2xl opacity-40">⏳</div>
      <p className="text-sm font-medium text-forest-400">Module C 개발 중</p>
      <p className="text-xs">NPV 시나리오 분석 모듈 연동 대기</p>
    </div>
  );
}

export default function ScenarioNPVChart({ scenarios }: { scenarios?: Scenario[] | null }) {
  return (
    <div className="bg-black/45 backdrop-blur-md border border-white/10 shadow-xl rounded-xl p-4 h-full">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-semibold text-forest-100">30년 시나리오 NPV 비교</p>
        <p className="text-xs text-forest-500">단위: 만원 · 점선=불확실성 범위</p>
      </div>

      {scenarios === null ? (
        <PendingModuleC />
      ) : scenarios === undefined ? (
        <div className="h-52"><Skeleton /></div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <ComposedChart
            data={scenarios.map((s) => ({ ...s, p50: s.npv.p50 }))}
            margin={{ top: 10, right: 10, left: 10, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#1f3620" vertical={false} />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 11, fill: "#6aab70" }}
              tickLine={false}
              axisLine={{ stroke: "#2d5230" }}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "#6aab70" }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => `${v.toLocaleString()}`}
              width={60}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(45,82,48,0.3)" }} />
            <ReferenceLine y={0} stroke="#3d6b42" strokeDasharray="4 2" />
            <Bar dataKey="p50" shape={<CustomBar />} maxBarSize={60}>
              {scenarios.map((s) => (
                <Cell
                  key={s.id}
                  fill={SCENARIO_COLORS[s.id]}
                />
              ))}
            </Bar>
          </ComposedChart>
        </ResponsiveContainer>
      )}

      {scenarios && (
        <div className="flex flex-wrap gap-2 mt-2">
          {scenarios.map((s) => (
            <span
              key={s.id}
              className="flex items-center gap-1 text-xs"
              style={{ color: SCENARIO_COLORS[s.id] }}
            >
              <span
                className="w-2.5 h-2.5 rounded-sm inline-block"
                style={{ backgroundColor: SCENARIO_COLORS[s.id], opacity: 0.85 }}
              />
              {s.name}
              {s.recommended && <span className="text-forest-400 font-bold">✓</span>}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
