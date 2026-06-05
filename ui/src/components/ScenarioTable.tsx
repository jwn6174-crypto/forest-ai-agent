"use client";
import type { Scenario, MarketData } from "@/lib/types";
import { CheckCircle2, Star } from "lucide-react";
import clsx from "clsx";


function Skeleton() {
  return (
    <div className="space-y-2 animate-pulse">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="h-10 bg-forest-800 rounded-lg" />
      ))}
    </div>
  );
}

function ScenarioUnavailable() {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-8 text-forest-500">
      <div className="text-3xl opacity-40">⚠️</div>
      <p className="text-sm font-medium text-forest-400">경제성 분석 결과 없음</p>
      <p className="text-xs text-center leading-relaxed">
        분석 서버(Module C)에서 시나리오를 받지 못했습니다.<br />Python API 서버 상태를 확인해 주세요.
      </p>
    </div>
  );
}

export default function ScenarioTable({
  scenarios,
  market,
}: {
  scenarios?: Scenario[] | null;
  market?: MarketData;
}) {
  return (
    <div className="bg-black/45 backdrop-blur-md border border-white/10 shadow-xl rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-semibold text-forest-100">시나리오별 상세 비교</p>
        {market && (
          <p className="text-xs text-forest-500">
            KAU {market.kauPrice.toLocaleString()}원/tCO₂ · 할인율 {market.discountRate}% · {market.priceDate}
          </p>
        )}
      </div>

      {scenarios === null ? (
        <ScenarioUnavailable />
      ) : scenarios === undefined ? (
        <Skeleton />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-forest-500 border-b border-forest-700">
                <th className="text-left py-2 pr-4 font-medium">시나리오</th>
                <th className="text-right py-2 px-3 font-medium">NPV p50</th>
                <th className="text-right py-2 px-3 font-medium hidden sm:table-cell">범위 (p5~p95)</th>
                <th className="text-right py-2 px-3 font-medium hidden md:table-cell">목재수익</th>
                <th className="text-right py-2 px-3 font-medium hidden md:table-cell">탄소수익</th>
                <th className="text-center py-2 px-3 font-medium">KOC</th>
                <th className="text-center py-2 px-3 font-medium">손실위험</th>
              </tr>
            </thead>
            <tbody>
              {scenarios.map((s) => (
                <tr
                  key={s.id}
                  className={clsx(
                    "border-b border-forest-800 transition-colors hover:bg-forest-850",
                    s.recommended && "bg-forest-800/50"
                  )}
                >
                  <td className="py-2.5 pr-4">
                    <div className="flex items-center gap-2">
                      <div>
                        <p className={clsx(
                          "font-medium",
                          s.recommended ? "text-forest-100" : "text-forest-300"
                        )}>
                          {s.name}
                          {s.recommended && (
                            <Star className="inline w-3 h-3 text-[#887228] ml-1" />
                          )}
                        </p>
                        <p className="text-forest-600 text-xs">{s.description}</p>
                      </div>
                    </div>
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    <span className={clsx(
                      "font-semibold",
                      s.npv.p50 > 0 ? "text-forest-200" : "text-red-400"
                    )}>
                      {s.npv.p50.toLocaleString()}
                      <span className="text-forest-500 font-normal">만원</span>
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-right text-forest-500 hidden sm:table-cell">
                    {s.npv.p5.toLocaleString()} ~ {s.npv.p95.toLocaleString()}
                  </td>
                  <td className="py-2.5 px-3 text-right text-forest-400 hidden md:table-cell">
                    {s.timberRevenue > 0 ? `${s.timberRevenue.toLocaleString()}만` : "—"}
                  </td>
                  <td className="py-2.5 px-3 text-right text-[#5a8098] hidden md:table-cell">
                    {s.carbonRevenue > 0 ? `${s.carbonRevenue.toLocaleString()}만` : "—"}
                  </td>
                  <td className="py-2.5 px-3 text-center">
                    {s.kocEligible ? (
                      <CheckCircle2 className="w-4 h-4 text-[#5a8098] mx-auto" />
                    ) : (
                      <span className="text-forest-700">—</span>
                    )}
                  </td>
                  <td className="py-2.5 px-3 text-center">
                    <span className={clsx(
                      "px-2 py-0.5 rounded-full text-xs",
                      s.npv.bankruptcyProb < 0.05 && "bg-[#1e3820]/80 text-[#6aab70]",
                      s.npv.bankruptcyProb >= 0.05 && s.npv.bankruptcyProb < 0.15 && "bg-[#3a2e10]/80 text-[#887228]",
                      s.npv.bankruptcyProb >= 0.15 && "bg-red-950/60 text-red-400/80"
                    )}>
                      {(s.npv.bankruptcyProb * 100).toFixed(0)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
