"use client";
import type { GrowthForecast } from "@/lib/types";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

const GRADES = [
  { key: "teukYongJae", label: "특용재", color: "#2a4830" },  // 진한 숲 (고가)
  { key: "grade1",      label: "1등급",  color: "#3a6240" },
  { key: "grade2",      label: "2등급",  color: "#4a7a52" },
  { key: "grade3",      label: "3등급",  color: "#5e8e65" },
  { key: "wonJuJae",   label: "원주재", color: "#7a9878" },  // 세이지
  { key: "wonRyoJae",  label: "원료재", color: "#96a890" },  // 무채 세이지
] as const;

const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { name: string; value: number; fill: string }[];
  label?: string;
}) => {
  if (!active || !payload?.length) return null;
  const total = payload.reduce((s, p) => s + p.value, 0);
  return (
    <div className="bg-forest-800 border border-forest-600 rounded-lg p-3 text-xs shadow-xl">
      <p className="font-medium text-forest-200 mb-1.5">{label}</p>
      {payload.slice().reverse().map((p) => (
        <p key={p.name} className="flex justify-between gap-4" style={{ color: p.fill }}>
          <span>{p.name}</span>
          <span className="font-medium">{p.value}%</span>
        </p>
      ))}
      <p className="text-forest-400 border-t border-forest-700 mt-1 pt-1">합계 {total}%</p>
    </div>
  );
};

function Skeleton() {
  return <div className="h-52 bg-forest-800 rounded animate-pulse" />;
}

export default function GradeDistributionChart({ growth }: { growth?: GrowthForecast }) {
  const data = growth
    ? growth.years.map((y, i) => {
        const dist = growth.gradeDistributionByYear[i];
        return {
          year: `+${y}년`,
          특용재: dist.teukYongJae,
          "1등급": dist.grade1,
          "2등급": dist.grade2,
          "3등급": dist.grade3,
          원주재: dist.wonJuJae,
          원료재: dist.wonRyoJae,
        };
      })
    : [];

  return (
    <div className="bg-black/45 backdrop-blur-md border border-white/10 shadow-xl rounded-xl p-4 h-full">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-semibold text-forest-100">등급별 재적 분포 변화</p>
        <p className="text-xs text-forest-500">임령별 등급 비율 (%)</p>
      </div>

      {!growth ? (
        <Skeleton />
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f3620" vertical={false} />
            <XAxis
              dataKey="year"
              tick={{ fontSize: 11, fill: "#6aab70" }}
              tickLine={false}
              axisLine={{ stroke: "#2d5230" }}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "#6aab70" }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => `${v}%`}
              width={36}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(45,82,48,0.3)" }} />
            <Legend wrapperStyle={{ fontSize: 11, color: "#6aab70", paddingTop: 4 }} />
            {GRADES.map((g) => (
              <Bar
                key={g.key}
                dataKey={g.label}
                stackId="grade"
                fill={g.color}
                maxBarSize={48}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
