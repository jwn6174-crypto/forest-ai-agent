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
  immediate: "#b85a28",
  five_year: "#887228",
  ten_year:  "#4a7c52",
  koc:       "#3f6480",
  ntfp:      "#6b4e7a",
  thinning:  "#2e6e5a",
};
const sc = (id: string) => SCENARIO_COLORS[id] ?? "#4a5568";

const SCENARIO_SHORT: Record<string, string> = {
  immediate: "즉시 벌채",
  five_year: "5년 후 벌채",
  ten_year:  "10년 후 벌채",
  koc:       "탄소상쇄(KOC)",
  ntfp:      "임산물 병행",
  thinning:  "간벌+10년",
};

// ─── 포인트 겹침 분리 ────────────────────────────────────────────────────────
type PPoint = Scenario & {
  x: number; y: number;
  labelDir: "above" | "below" | "left" | "right";
};

function prepareData(scenarios: Scenario[]): PPoint[] {
  // 1) 초기 데이터 생성
  const pts: PPoint[] = scenarios.map((s) => ({
    ...s,
    x: s.paretoX,
    y: s.npv.p50,
    labelDir: "above" as const,
  }));

  // 2) 겹치는 포인트 x축 분리 (threshold: 정규화 x 기준 4%)
  const X_THRESH = 0.04;
  const Y_THRESH = 0.05; // y 범위의 5%
  const yRange = Math.max(...pts.map((p) => p.y)) - Math.min(...pts.map((p) => p.y)) || 1;

  for (let i = 0; i < pts.length; i++) {
    for (let j = i + 1; j < pts.length; j++) {
      const dx = Math.abs(pts[i].x - pts[j].x);
      const dy = Math.abs(pts[i].y - pts[j].y);
      if (dx < X_THRESH && dy / yRange < Y_THRESH) {
        pts[i] = { ...pts[i], x: pts[i].x - 0.03 };
        pts[j] = { ...pts[j], x: pts[j].x + 0.03 };
      }
    }
  }

  // 3) 레이블 방향 결정
  const maxY = Math.max(...pts.map((p) => p.y));
  const maxX = Math.max(...pts.map((p) => p.x));

  return pts.map((p) => ({
    ...p,
    labelDir: (
      p.y === maxY    ? "below"  // 최고 NPV → 아래 (상단 여백 부족)
      : p.x >= maxX   ? "left"   // 우측 끝 → 왼쪽
      : "above"                  // 나머지 → 위
    ) as PPoint["labelDir"],
  }));
}

// ─── 커스텀 점 + 레이블 ───────────────────────────────────────────────────────
function CustomDot(props: { cx?: number; cy?: number; payload?: PPoint }) {
  const { cx, cy, payload } = props;
  if (cx == null || cy == null || !payload) return null;

  const color = sc(payload.id);
  const R = payload.recommended ? 8 : 5;
  const label = SCENARIO_SHORT[payload.id] ?? payload.name;
  const dir = payload.labelDir;

  // 레이블 위치 계산
  let lx = cx;
  let ly = cy;
  let anchor: "start" | "middle" | "end" = "middle";

  if (dir === "above")  { ly = cy - R - 5; }
  if (dir === "below")  { ly = cy + R + 13; }
  if (dir === "left")   { lx = cx - R - 5; ly = cy + 4; anchor = "end"; }
  if (dir === "right")  { lx = cx + R + 5; ly = cy + 4; anchor = "start"; }

  return (
    <g>
      {/* 권장 시나리오 링 */}
      {payload.recommended && (
        <circle cx={cx} cy={cy} r={R + 4}
          fill="none" stroke={color} strokeWidth={1.5} opacity={0.45} />
      )}
      {/* 점 */}
      <circle cx={cx} cy={cy} r={R} fill={color} opacity={0.9} />

      {/* 레이블 (1줄, 최대 8글자 → 필요 시 축약) */}
      <text
        x={lx} y={ly}
        textAnchor={anchor}
        fontSize={10}
        fill={color}
        fontWeight={payload.recommended ? 700 : 400}
        style={{ pointerEvents: "none", userSelect: "none" }}
      >
        {label}
      </text>
    </g>
  );
}

// ─── 툴팁 ────────────────────────────────────────────────────────────────────
const CustomTooltip = ({
  active, payload,
}: {
  active?: boolean;
  payload?: { payload: PPoint }[];
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

// ─── 메인 컴포넌트 ────────────────────────────────────────────────────────────
export default function ParetoChart({ scenarios }: { scenarios?: Scenario[] | null }) {
  const data = scenarios ? prepareData(scenarios) : null;

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
          <ScatterChart margin={{ top: 24, right: 52, left: 10, bottom: 18 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f3620" />
            <XAxis
              type="number" dataKey="x"
              domain={[0, 1.05]}
              tick={{ fontSize: 10, fill: "#6aab70" }}
              tickLine={false}
              axisLine={{ stroke: "#2d5230" }}
              tickFormatter={(v) => `${Math.round(v * 100)}%`}
              label={{
                value: "즉시 현금화 가능성 →",
                position: "insideBottom", offset: -4,
                style: { fontSize: 10, fill: "#4a7c50" },
              }}
            />
            <YAxis
              type="number" dataKey="y"
              tick={{ fontSize: 10, fill: "#6aab70" }}
              tickLine={false} axisLine={false}
              tickFormatter={(v) => `${(v / 1000).toFixed(1)}천만`}
              label={{
                value: "30yr NPV (만원)", angle: -90,
                position: "insideLeft", offset: 10,
                style: { fontSize: 10, fill: "#4a7c50" },
              }}
            />
            <Tooltip content={<CustomTooltip />} />
            {data.map((s) => (
              <Scatter
                key={s.id}
                data={[s]}
                fill={sc(s.id)}
                shape={(p: object) =>
                  <CustomDot {...(p as { cx?: number; cy?: number; payload?: PPoint })} />
                }
              />
            ))}
          </ScatterChart>
        </ResponsiveContainer>
      )}

      <p className="text-xs text-forest-600 mt-1">
        오른쪽 위 = 즉각 현금화 + 높은 NPV가 이상적 · 링 = 권장 시나리오
      </p>
    </div>
  );
}
