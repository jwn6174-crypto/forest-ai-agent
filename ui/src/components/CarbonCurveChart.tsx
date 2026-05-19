"use client";
import type { GrowthForecast } from "@/lib/types";
import {
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

function Skeleton() {
  return <div className="h-full bg-forest-800 rounded animate-pulse" />;
}

const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { name: string; value: number; color: string }[];
  label?: number;
}) => {
  if (!active || !payload?.length) return null;
  // 보조 데이터는 payload에 숨겨서 받아옴
  const extra = (payload[0] as { payload?: Record<string, number> }).payload;
  return (
    <div className="bg-forest-900/95 border border-white/10 rounded-lg p-3 text-xs shadow-xl">
      <p className="font-medium text-forest-200 mb-2">현재 + {label}년</p>
      {payload.map((p) => (
        <p key={p.name} className="flex justify-between gap-6" style={{ color: p.color }}>
          <span>{p.name}</span>
          <span className="font-medium">{typeof p.value === "number" ? p.value.toFixed(1) : p.value}</span>
        </p>
      ))}
      {extra && (
        <div className="mt-2 pt-2 border-t border-white/10 space-y-0.5 text-forest-500">
          {extra["흉고직경 (cm)"] !== undefined && (
            <p className="flex justify-between gap-6">
              <span>흉고직경</span>
              <span>{extra["흉고직경 (cm)"].toFixed(1)} cm</span>
            </p>
          )}
          {extra["ha당 본수"] !== undefined && (
            <p className="flex justify-between gap-6">
              <span>ha당 본수</span>
              <span>{Math.round(extra["ha당 본수"]).toLocaleString()} 본</span>
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default function CarbonCurveChart({ growth }: { growth?: GrowthForecast }) {
  const data = growth
    ? growth.years.map((y, i) => ({
        year: y,
        "입목축적 (m³/ha)":       growth.volumePerHa[i],
        "탄소흡수율 (tCO₂/ha/yr)": growth.carbonSequestration[i],
        "흉고직경 (cm)":           growth.dbhTrajectory?.[i] ?? 0,
        "ha당 본수":               growth.nPerHaTrajectory?.[i] ?? 0,
      }))
    : [];

  return (
    <div className="bg-black/45 backdrop-blur-md border border-white/10 shadow-xl rounded-xl p-4 h-full">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-semibold text-forest-100">재적 성장 &amp; 탄소 흡수</p>
        <p className="text-xs text-forest-500">{growth?.climateScenario ?? "SSP1-2.6"} · Module B</p>
      </div>

      {!growth ? (
        <div className="h-52"><Skeleton /></div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <ComposedChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="volGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#4a7c52" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#4a7c52" stopOpacity={0.02} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="#1f3620" vertical={false} />

            <XAxis
              dataKey="year"
              tick={{ fontSize: 11, fill: "#6aab70" }}
              tickLine={false}
              axisLine={{ stroke: "#2d5230" }}
              tickFormatter={(v) => `+${v}년`}
            />

            {/* 왼쪽: 입목축적 (m³/ha) */}
            <YAxis
              yAxisId="vol"
              tick={{ fontSize: 11, fill: "#6aab70" }}
              tickLine={false}
              axisLine={false}
              width={46}
              tickFormatter={(v) => `${v}`}
              label={{ value: "m³/ha", angle: -90, position: "insideLeft",
                       offset: 12, style: { fontSize: 9, fill: "#3d6b42" } }}
            />

            {/* 오른쪽: 탄소흡수율 (tCO₂/ha/yr) */}
            <YAxis
              yAxisId="co2"
              orientation="right"
              tick={{ fontSize: 11, fill: "#5a8098" }}
              tickLine={false}
              axisLine={false}
              width={38}
              tickFormatter={(v) => `${v}`}
              label={{ value: "tCO₂", angle: 90, position: "insideRight",
                       offset: 10, style: { fontSize: 9, fill: "#3f6480" } }}
            />

            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: 11, paddingTop: 4 }} />

            {/* 재적 성장 — 면적 차트 */}
            <Area
              yAxisId="vol"
              type="monotone"
              dataKey="입목축적 (m³/ha)"
              stroke="#4a7c52"
              strokeWidth={2}
              fill="url(#volGrad)"
              dot={{ r: 3, fill: "#4a7c52", strokeWidth: 0 }}
              activeDot={{ r: 5 }}
            />

            {/* 탄소흡수율 — 점선 라인 */}
            <Line
              yAxisId="co2"
              type="monotone"
              dataKey="탄소흡수율 (tCO₂/ha/yr)"
              stroke="#3f6480"
              strokeWidth={2}
              strokeDasharray="5 3"
              dot={false}
              activeDot={{ r: 4 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
