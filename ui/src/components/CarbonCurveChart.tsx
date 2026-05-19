"use client";
import type { GrowthForecast } from "@/lib/types";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

function Skeleton() {
  return (
    <div className="h-full bg-forest-800 rounded animate-pulse" />
  );
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
  return (
    <div className="bg-forest-800 border border-forest-600 rounded-lg p-3 text-xs shadow-xl">
      <p className="font-medium text-forest-200 mb-1">현재 + {label}년</p>
      {payload.map((p) => (
        <p key={p.name} style={{ color: p.color }}>
          {p.name}: {p.value.toFixed(1)}
        </p>
      ))}
    </div>
  );
};

export default function CarbonCurveChart({ growth }: { growth?: GrowthForecast }) {
  const data = growth
    ? growth.years.map((y, i) => ({
        year: y,
        "탄소저장량 (tC/ha)": growth.carbonPerHa[i],
        "연간 흡수량 (tC/ha/yr)": growth.carbonSequestration[i],
      }))
    : [];

  return (
    <div className="bg-black/45 backdrop-blur-md border border-white/10 shadow-xl rounded-xl p-4 h-full">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-semibold text-forest-100">탄소 흡수 곡선</p>
        <p className="text-xs text-forest-500">{growth?.climateScenario ?? "SSP2-4.5"}</p>
      </div>

      {!growth ? (
        <div className="h-52"><Skeleton /></div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="carbonGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#4a7c52" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#4a7c52" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="seqGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3f6480" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#3f6480" stopOpacity={0} />
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
            <YAxis
              yAxisId="left"
              tick={{ fontSize: 11, fill: "#6aab70" }}
              tickLine={false}
              axisLine={false}
              width={50}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fontSize: 11, fill: "#5a8098" }}
              tickLine={false}
              axisLine={false}
              width={40}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: 11, color: "#6aab70", paddingTop: 4 }}
            />
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="탄소저장량 (tC/ha)"
              stroke="#4a7c52"
              strokeWidth={2}
              fill="url(#carbonGrad)"
              dot={{ r: 3, fill: "#4a7c52" }}
            />
            <Area
              yAxisId="right"
              type="monotone"
              dataKey="연간 흡수량 (tC/ha/yr)"
              stroke="#3f6480"
              strokeWidth={2}
              fill="url(#seqGrad)"
              strokeDasharray="5 3"
              dot={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
