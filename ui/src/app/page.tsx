"use client";
import { Github, AlertCircle } from "lucide-react";
import PNUInput from "@/components/PNUInput";
import ModuleStatusBar from "@/components/ModuleStatusBar";
import ForestStateCard from "@/components/ForestStateCard";
import ScenarioNPVChart from "@/components/ScenarioNPVChart";
import CarbonCurveChart from "@/components/CarbonCurveChart";
import GradeDistributionChart from "@/components/GradeDistributionChart";
import ParetoChart from "@/components/ParetoChart";
import ScenarioTable from "@/components/ScenarioTable";
import ChatPanel from "@/components/ChatPanel";
import ReportSidebar from "@/components/ReportSidebar";
import { useForestAnalysis } from "@/hooks/useForestAnalysis";

export default function Home() {
  const {
    moduleStatus,
    partial,
    fullResult,
    isAnalyzing,
    isChatReady,
    error,
    analyze,
  } = useForestAnalysis();

  const hasData = !!partial;

  return (
    <div className="flex flex-col h-screen overflow-hidden">

      {/* ── 헤더 ── */}
      <header className="shrink-0 bg-black/50 backdrop-blur-md border-b border-white/10 shadow-lg">
        <div className="flex items-center gap-4 px-5 py-2">
          {/* 로고 */}
          <div className="shrink-0">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/logo.png" alt="MOFOM AI" className="h-20 w-auto" />
          </div>

          {/* PNU 입력 */}
          <div className="flex-1">
            <PNUInput onAnalyze={analyze} isAnalyzing={isAnalyzing} />
          </div>

          {/* GitHub */}
          <a
            href="https://github.com"
            className="shrink-0 text-forest-500 hover:text-forest-300 transition-colors"
            aria-label="GitHub"
          >
            <Github className="w-5 h-5" />
          </a>
        </div>

        {/* 모듈 상태 바 */}
        <div className="px-5 pb-2.5">
          <ModuleStatusBar status={moduleStatus} />
        </div>
      </header>

      {/* ── 에러 배너 ── */}
      {error && (
        <div className="shrink-0 flex items-center gap-2 px-5 py-2 bg-red-50/90 border-b border-red-200 text-red-700 text-sm">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {/* ── 메인 콘텐츠 ── */}
      {!hasData ? (
        /* 초기 화면 */
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-8 px-4">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/logo.png" alt="MOFOM AI" className="h-56 w-auto mx-auto drop-shadow-2xl" />

            <div className="bg-black/50 backdrop-blur-md rounded-3xl px-10 py-8 border border-white/10 shadow-2xl space-y-4">
              <h1 className="text-3xl font-bold text-forest-100">
                다목적 산림경영 의사결정 AI
              </h1>
              <p className="text-forest-400 text-sm max-w-lg mx-auto leading-relaxed">
                임야 PNU 코드를 입력하면 위성 데이터 · 임분수확표 · 탄소시장 가격을
                <br />
                Faustmann–Hartman 모델로 통합하여 5개 시나리오의 NPV를 분석합니다.
              </p>

              <div className="grid grid-cols-3 gap-4 max-w-md mx-auto pt-2">
                {[
                  { img: "/card-satellite.jpg", label: "위성 AGB 추정",  sub: "GEDI · Sentinel" },
                  { img: "/card-chart.jpg",     label: "30년 성장 예측", sub: "임분수확표" },
                  { img: "/card-ai.jpg",        label: "AI 자연어 설명", sub: "Claude Sonnet" },
                ].map((f) => (
                  <div
                    key={f.label}
                    className="bg-white/10 rounded-2xl overflow-hidden border border-white/15 text-center"
                  >
                    <img
                      src={f.img}
                      alt={f.label}
                      className="w-full h-24 object-cover"
                    />
                    <div className="px-3 py-2.5">
                      <p className="text-sm font-semibold text-forest-200">{f.label}</p>
                      <p className="text-xs text-forest-500 mt-0.5">{f.sub}</p>
                    </div>
                  </div>
                ))}
              </div>

              <p className="text-xs text-forest-500 pt-1">
                위 데모 버튼으로 샘플 임야를 즉시 분석해보세요
              </p>
            </div>
          </div>
        </main>
      ) : (
        /* ── 분석 결과 대시보드 ── */
        <main className="flex-1 overflow-hidden">
          <div className="h-full max-w-screen-2xl mx-auto flex gap-3 p-3">

            {/* 맨 왼쪽: 보고서 사이드바 */}
            <ReportSidebar data={partial} />

            {/* 중앙: 상태 카드 + 차트 + 표 */}
            <div className="flex-1 min-w-0 flex flex-col gap-3 overflow-y-auto">
              <ForestStateCard state={partial?.state} />

              {/* 차트 Row 1: NPV 바차트 + 탄소곡선 */}
              <div className="grid grid-cols-2 gap-3 shrink-0">
                <ScenarioNPVChart scenarios={partial?.scenarios} />
                <CarbonCurveChart growth={partial?.growth} />
              </div>

              {/* 차트 Row 2: 파레토(2/3) + 등급분포(1/3) */}
              <div className="grid grid-cols-3 gap-3 shrink-0">
                <div className="col-span-2">
                  <ParetoChart scenarios={partial?.scenarios} />
                </div>
                <GradeDistributionChart growth={partial?.growth} />
              </div>

              {/* 시나리오 표 */}
              <div className="shrink-0">
                <ScenarioTable scenarios={partial?.scenarios} market={partial?.market} />
              </div>

              {/* KOC 등록 가능성 + Module D 시장 상세 */}
              {partial?.offsetEligibility && (
                <div className="shrink-0 bg-black/45 backdrop-blur-md border border-white/10 shadow-xl rounded-xl p-4 animate-slide-up space-y-4">
                  <p className="text-sm font-semibold text-forest-100">
                    🌿 산림탄소상쇄 등록 가능성
                  </p>

                  <div className="grid grid-cols-2 gap-4 text-xs">
                    <div>
                      <p className="text-forest-500 mb-1.5">매칭 사업유형</p>
                      <div className="flex flex-wrap gap-1">
                        {partial.offsetEligibility.matchedTypes.length > 0
                          ? partial.offsetEligibility.matchedTypes.map((t) => (
                              <span key={t} className="px-2 py-0.5 bg-[#1a2e3a]/80 text-[#5a8098] border border-[#3f6480]/40 rounded-full">
                                {t}
                              </span>
                            ))
                          : <span className="text-forest-600">해당 없음</span>
                        }
                      </div>
                    </div>
                    <div>
                      <p className="text-forest-500 mb-1.5">다음 단계</p>
                      <ol className="space-y-1 text-forest-400 list-decimal list-inside">
                        {partial.offsetEligibility.nextSteps.map((step) => (
                          <li key={step}>{step}</li>
                        ))}
                      </ol>
                    </div>
                  </div>

                  {/* Module D: 탄소 시장 가격 상세 */}
                  {partial.market && (
                    <div className="border-t border-white/10 pt-3">
                      <p className="text-xs text-forest-500 mb-2">탄소 시장 가격 (Module D · {partial.market.priceDate})</p>
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <div className="bg-white/10 rounded-lg px-3 py-2">
                          <p className="text-forest-500 mb-0.5">KAU 종가</p>
                          <p className="font-semibold text-forest-100">
                            {partial.market.kauPrice.toLocaleString()}
                            <span className="text-forest-400 font-normal ml-1">원/tCO₂</span>
                          </p>
                        </div>
                        <div className="bg-white/10 rounded-lg px-3 py-2">
                          <p className="text-forest-500 mb-0.5">KOC 추정가</p>
                          <p className="font-semibold text-forest-100">
                            {partial.market.kocEstimate.toLocaleString()}
                            <span className="text-forest-400 font-normal ml-1">원/tCO₂</span>
                          </p>
                        </div>
                        <div className="bg-white/10 rounded-lg px-3 py-2">
                          <p className="text-forest-500 mb-0.5">WTA 하한</p>
                          <p className="font-semibold text-forest-100">
                            {(partial.market.vcmFloorWta ?? 17039).toLocaleString()}
                            <span className="text-forest-400 font-normal ml-1">원/tCO₂</span>
                          </p>
                          <p className="text-[10px] text-forest-600 mt-0.5">박2020 산주 기준</p>
                        </div>
                      </div>

                      {/* 수종별 목재 가격 */}
                      <div className="mt-3">
                        <p className="text-xs text-forest-500 mb-2">수종 목재 가격 (6등급)</p>
                        <div className="grid grid-cols-6 gap-1 text-[10px] text-center">
                          {(["teukYongJae","grade1","grade2","grade3","wonJuJae","wonRyoJae"] as const).map((g) => {
                            const labels: Record<string, string> = {
                              teukYongJae: "특용재", grade1: "1등급", grade2: "2등급",
                              grade3: "3등급", wonJuJae: "원주재", wonRyoJae: "원료재",
                            };
                            const v = partial.market!.timberPrices[g];
                            return (
                              <div key={g} className="bg-white/10 rounded px-1 py-1.5">
                                <p className="text-forest-500">{labels[g]}</p>
                                <p className="text-forest-200 font-medium mt-0.5">
                                  {v ? (v / 1000).toFixed(0) + "k" : "—"}
                                </p>
                              </div>
                            );
                          })}
                        </div>
                        <p className="text-[10px] text-forest-600 mt-1.5 text-right">
                          단위: 원/m³ · KOFPI 2025 Q4
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* 면책 문구 */}
              <p className="shrink-0 text-xs text-forest-300 pb-2 text-center font-medium">
                본 분석은 시나리오 비교를 위한 추정값이며 정확한 수익을 보장하지 않습니다.
                가격 가정: KAU {partial?.market?.kauPrice?.toLocaleString()}원/tCO₂ ·
                할인율 {partial?.market?.discountRate}% · SSP2-4.5 기준
              </p>
            </div>

            {/* 오른쪽: 채팅 메인 패널 */}
            <div className="w-[440px] xl:w-[500px] shrink-0 flex flex-col min-h-0">
              <ChatPanel
                analysisResult={fullResult ?? undefined}
                isReady={isChatReady}
              />
            </div>

          </div>
        </main>
      )}
    </div>
  );
}
