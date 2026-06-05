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
} from "recharts";

const SCENARIO_COLORS: Record<string, string> = {
  immediate:  "#b85a28",
  five_year:  "#887228",
  ten_year:   "#4a7c52",
  koc:        "#3f6480",
  ntfp:       "#6b4e7a",
  thinning:   "#2e6e5a",
};
const sc = (id: string) => SCENARIO_COLORS[id] ?? "#4a5568";

// 2줄 짧은 이름 (차트 공간 절약)
const SCENARIO_SHORT: Record<string, [string, string]> = {
  immediate:  ["즉시", "벌채"],
  five_year:  ["5년 후", "벌채"],
  ten_year:   ["10년 후", "벌채"],
  koc:        ["탄소상쇄", "(KOC)"],
  ntfp:       ["임산물", "병행"],
  thinning:   ["간벌", "+10년"],
};

const CustomTooltip = ({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { payload: Scenario & { x: number; y: number } }[];
}) => {
  if (!active || !payload?.[0]) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-forest-800 border border-forest-600 rounded-lg p-3 text-xs shadow-xl">
      <p className="font-semibold text-forest-100">{d.name}</p>
      <p className="text-forest-400 mt-0.5">유동성: {(d.paretoX * 100).toFixed(0)}%</p>
      <p className="text-forest-400">NPV(중앙): {d.npv.p50.toLocaleString()}만원</p>
      {d.recommended && <p className="text-forest-300 font-medium mt-1">✓ 권장 시나리오</p>}
    </div>
  );
};

// CustomDot: 점 + 레이블 위치를 동적으로 결정
function CustomDot(props: {
  cx?: number;
  cy?: number;
  payload?: Scenario & { x: number; y: number };
  chartHeight?: number;
}) {
  const { cx, cy, payload } = props;
  if (cx == null || cy == null || !payload) return null;

  const id = payload.id;
  const color = sc(id);
  const recommended = payload.recommended;
  const r = recommended ? 10 : 7;
  const [line1, line2] = SCENARIO_SHORT[id] ?? [payload.name, ""];

  // 상단 여백(30px) 이내면 레이블을 아래쪽에, 아니면 위쪽에
  const labelAbove = cy > 35;
  const baseY = labelAbove ? cy - r - 4 : cy + r + 13;
  const lineH = 12;

  // 우측 끝 포인트는 레이블을 왼쪽으로 이동
  const isRightEdge = payload.paretoX > 0.88;
  const anchor = isRightEdge ? "end" : "middle";
  const dx = isRightEdge ? -r - 2 : 0;

  return (
    <g>
      {/* 점 */}
      <circle cx={cx} cy={cy} r={r} fill={color} opacity={0.9} />
      {recommended && (
        <circle
          cx={cx} cy={cy} r={r + 4}
          fill="none" stroke={color} strokeWidth={1.5} opacity={0.4}
        />
      )}
      {/* 라인1 */}
      <text
        x={cx + dx} y={labelAbove ? baseY : baseY}
        textAnchor={anchor} fontSize={10} fill={color}
        fontWeight={recommended ? 700 : 400}
        style={{ pointerEvents: "none" }}
      >
        {line1}
      </text>
      {/* 라인2 */}
      {line2 && (
        <text
          x={cx + dx} y={(labelAbove ? baseY : baseY) + lineH}
          textAnchor={anchor} fontSize={10} fill={color}
          fontWeight={recommended ? 700 : 400}
          style={{ pointerEvents: "none" }}
        >
          {line2}
        </text>
      )}
    </g>
  );
}

function Skeleton() {
  return <div className="h-52 bg-forest-800 rounded animate-pulse" />;
}

function PendingModuleC() {
  return (
    <div className="h-52 flex flex-col items-center justify-center gap-2 text-forest-500">
      <div className="text-2xl opacity-40">⏳</div>
      <p className="text-sm font-medium text-forest-400">시나리오 분석 오류</p>
      <p className="text-xs">파레토 분석 모듈 연동 대기</p>
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
        <PendingModuleC />
      ) : !data ? (
        <Skeleton />
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <ScatterChart margin={{ top: 28, right: 40, left: 10, bottom: 18 }}>
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
                offset: -4,
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
                fill={sc(s.id)}
                shape={(p: object) => <CustomDot {...(p as { cx?: number; cy?: number; payload?: Scenario & { x: number; y: number } })} />}
              />
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
