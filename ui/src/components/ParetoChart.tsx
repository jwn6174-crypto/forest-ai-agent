"use client";
import type { Scenario } from "@/lib/types";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LabelList,
} from "recharts";

const SCENARIO_COLORS: Record<string, string> = {
  immediate:  "#b85a28",
  five_year:  "#887228",
  ten_year:   "#4a7c52",
  koc:        "#3f6480",
  ntfp:       "#6b4e7a",
};

const CustomTooltip = ({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { payload: Scenario & { y: number } }[];
}) => {
  if (!active || !payload?.[0]) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-forest-800 border border-forest-600 rounded-lg p-3 text-xs shadow-xl">
      <p className="font-semibold text-forest-100">{d.name}</p>
      <p className="text-forest-400 mt-0.5">유동성: {(d.paretoX * 100).toFixed(0)}%</p>
      <p className="text-forest-400">NPV(중앙): {d.npv.p50.toLocaleString()}만원</p>
    </div>
  );
};

function Skeleton() {
  return <div className="h-52 bg-forest-800 rounded animate-pulse" />;
}

function ScenarioUnavailable() {
  return (
    <div className="h-52 flex flex-col items-center justify-center gap-2 text-forest-500">
      <div className="text-2xl opacity-40">⚠️</div>
      <p className="text-sm font-medium text-forest-400">경제성 분석 결과 없음</p>
      <p className="text-xs">분석 서버(Module C)에서 시나리오를 받지 못했습니다</p>
    </div>
  );
}

export default function ParetoChart({ scenarios }: { scenarios?: Scenario[] | null }) {
  const data = scenarios?.map((s) => ({
    ...s,
    x: s.paretoX,
    y: s.npv.p50,
  }));

  return (
    <div className="bg-black/45 backdrop-blur-md border border-white/10 shadow-xl rounded-xl p-4 h-full">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-semibold text-forest-100">파레토 프론트</p>
        <p className="text-xs text-forest-500">유동성 ↔ NPV 트레이드오프</p>
      </div>

      {scenarios === null ? (
        <ScenarioUnavailable />
      ) : !data ? (
        <Skeleton />
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <ScatterChart margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f3620" />
            <XAxis
              type="number"
              dataKey="x"
              domain={[0, 1]}
              tick={{ fontSize: 10, fill: "#6aab70" }}
              tickLine={false}
              axisLine={{ stroke: "#2d5230" }}
              tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
              label={{
                value: "즉시 현금화 가능성 →",
                position: "insideBottom",
                offset: -2,
                style: { fontSize: 10, fill: "#4a7c50" },
              }}
            />
            <YAxis
              type="number"
              dataKey="y"
              tick={{ fontSize: 10, fill: "#6aab70" }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => `${(v / 1000).toFixed(1)}천만`}
              label={{
                value: "30yr NPV (만원)",
                angle: -90,
                position: "insideLeft",
                offset: 10,
                style: { fontSize: 10, fill: "#4a7c50" },
              }}
            />
            <Tooltip content={<CustomTooltip />} />
            {data.map((s) => (
              <Scatter
                key={s.id}
                data={[s]}
                fill={SCENARIO_COLORS[s.id]}
                opacity={0.9}
                r={s.recommended ? 10 : 7}
              >
                <LabelList
                  dataKey="name"
                  position="top"
                  style={{ fontSize: 10, fill: SCENARIO_COLORS[s.id] }}
                />
              </Scatter>
            ))}
          </ScatterChart>
        </ResponsiveContainer>
      )}

      <p className="text-xs text-forest-600 mt-1">
        오른쪽 위 = 즉각적 현금화 + 높은 NPV가 이상적 · 원의 크기는 권장 여부
      </p>
    </div>
  );
}
