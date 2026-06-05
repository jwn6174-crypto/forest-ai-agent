"use client";
import { useState } from "react";
import { FileText, Download, Printer, ChevronRight, TreePine, TrendingUp, Leaf, BarChart3 } from "lucide-react";
import type { PartialResult } from "@/lib/types";

// ── 보고서 HTML 생성 ──────────────────────────────────────────────────────────
function buildReportHTML(data: PartialResult, logoDataUrl: string): string {
  const s = data.state!;
  const m = data.market!;
  const scenarios = data.scenarios ?? [];
  const best = scenarios.find((sc) => sc.recommended);
  const elig = data.offsetEligibility;

  const scenarioRows = scenarios
    .map(
      (sc) => `
      <tr style="border-bottom:1px solid #d1e8d4">
        <td style="padding:8px 12px;font-weight:${sc.recommended ? "700" : "400"};color:${sc.recommended ? "#1a5c20" : "#333"}">
          ${sc.name}${sc.recommended ? " ★" : ""}
        </td>
        <td style="padding:8px 12px;text-align:right;font-weight:600">${sc.npv.p50.toLocaleString()}만원</td>
        <td style="padding:8px 12px;text-align:right;color:#666;font-size:12px">${sc.npv.p5.toLocaleString()} ~ ${sc.npv.p95.toLocaleString()}</td>
        <td style="padding:8px 12px;text-align:center;color:${sc.npv.bankruptcyProb < 0.05 ? "#1a7a1a" : sc.npv.bankruptcyProb < 0.15 ? "#a07020" : "#c03020"}">${(sc.npv.bankruptcyProb * 100).toFixed(0)}%</td>
        <td style="padding:8px 12px;text-align:center">${sc.kocEligible ? "✓" : "—"}</td>
      </tr>`
    )
    .join("");

  const gradeBar = Object.entries(s.gradeDistribution)
    .map(([k, v]) => {
      const colors: Record<string, string> = {
        teukYongJae: "#2a4830", grade1: "#3a6240", grade2: "#4a7a52",
        grade3: "#5e8e65", wonJuJae: "#7a9878", wonRyoJae: "#96a890",
      };
      const labels: Record<string, string> = {
        teukYongJae: "특용재", grade1: "1등급", grade2: "2등급",
        grade3: "3등급", wonJuJae: "원주재", wonRyoJae: "원료재",
      };
      return v > 0
        ? `<div style="display:inline-block;width:${v}%;height:16px;background:${colors[k]}" title="${labels[k]} ${v}%"></div>`
        : "";
    })
    .join("");

  return `<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8"/>
  <title>MOFOM AI 산림경영 분석 보고서 — ${s.pnu}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;700&display=swap');
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Noto Sans KR', sans-serif; color: #1a1a1a; background: #fff; font-size: 14px; line-height: 1.6; }
    .page { max-width: 800px; margin: 0 auto; padding: 40px 32px; }
    @media print { .page { padding: 20px 24px; } .no-print { display: none; } }

    /* 헤더 */
    .header { display: flex; align-items: center; justify-content: space-between; border-bottom: 3px solid #1a5c20; padding-bottom: 16px; margin-bottom: 28px; }
    .header-logo { font-size: 22px; font-weight: 700; color: #1a5c20; letter-spacing: -0.5px; }
    .header-sub { font-size: 11px; color: #666; text-align: right; }
    .header-badge { background: #e8f5e9; color: #1a5c20; font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 20px; border: 1px solid #a5d6a7; }

    /* 섹션 */
    .section { margin-bottom: 28px; }
    .section-title { font-size: 15px; font-weight: 700; color: #1a5c20; border-left: 4px solid #1a5c20; padding-left: 10px; margin-bottom: 14px; }

    /* 지표 그리드 */
    .metric-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 12px; }
    .metric-card { background: #f5fbf5; border: 1px solid #c8e6c9; border-radius: 8px; padding: 12px 14px; }
    .metric-label { font-size: 11px; color: #555; margin-bottom: 3px; }
    .metric-value { font-size: 18px; font-weight: 700; color: #1a3a1e; }
    .metric-unit { font-size: 11px; color: #777; margin-left: 3px; font-weight: 400; }

    /* 추천 박스 */
    .recommend-box { background: linear-gradient(135deg, #e8f5e9, #f1f8e9); border: 2px solid #66bb6a; border-radius: 10px; padding: 16px 20px; margin-bottom: 20px; }
    .recommend-title { font-size: 13px; color: #666; margin-bottom: 4px; }
    .recommend-value { font-size: 20px; font-weight: 700; color: #1a5c20; }
    .recommend-npv { font-size: 13px; color: #388e3c; margin-top: 2px; }

    /* 표 */
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    thead tr { background: #e8f5e9; }
    th { padding: 9px 12px; text-align: left; font-weight: 600; color: #1a5c20; font-size: 12px; }

    /* 시장 데이터 */
    .market-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
    .market-item { background: #f0f7f0; border-radius: 6px; padding: 10px 12px; }
    .market-label { font-size: 11px; color: #666; }
    .market-val { font-size: 15px; font-weight: 600; color: #1a3a1e; }

    /* 등급 바 */
    .grade-bar { border-radius: 4px; overflow: hidden; height: 16px; display: flex; margin-bottom: 8px; }

    /* KOC */
    .koc-box { background: #e3f2fd; border: 1px solid #90caf9; border-radius: 8px; padding: 12px 16px; }

    /* 푸터 */
    .footer { border-top: 1px solid #ddd; margin-top: 32px; padding-top: 12px; font-size: 11px; color: #999; display: flex; justify-content: space-between; }

    .print-btn { display: inline-flex; align-items: center; gap: 8px; background: #1a5c20; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-size: 14px; font-weight: 600; cursor: pointer; margin-bottom: 24px; }
    .print-btn:hover { background: #2e7d32; }
  </style>
</head>
<body>
<div class="page">

  <!-- 인쇄 버튼 (화면 전용) -->
  <div class="no-print" style="text-align:right;margin-bottom:16px">
    <button class="print-btn" onclick="window.print()">🖨️ PDF / 인쇄</button>
  </div>

  <!-- 헤더 -->
  <div class="header">
    <div style="display:flex;align-items:center;gap:10px">
      ${logoDataUrl
        ? `<img src="${logoDataUrl}" style="height:52px;width:auto;object-fit:contain" alt="MOFOM AI"/>`
        : `<span style="font-size:24px">🌲</span>`
      }
      <div>
        <div class="header-logo">MOFOM AI</div>
        <div style="font-size:12px;color:#555;margin-top:2px">다목적 산림경영 의사결정 분석 보고서</div>
      </div>
    </div>
    <div class="header-sub">
      <div class="header-badge">AI 분석 완료</div>
      <div style="margin-top:5px">PNU: ${s.pnu}</div>
      <div>분석일: ${m.priceDate}</div>
    </div>
  </div>

  <!-- 1. 임야 현황 -->
  <div class="section">
    <div class="section-title">1. 임야 현황 (Module A · B)</div>
    <div class="metric-grid">
      <div class="metric-card">
        <div class="metric-label">수종</div>
        <div class="metric-value" style="font-size:16px">${s.species}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">추정 임령</div>
        <div class="metric-value">${s.estimatedAge}<span class="metric-unit">년</span></div>
      </div>
      <div class="metric-card">
        <div class="metric-label">면적</div>
        <div class="metric-value">${s.areaHa}<span class="metric-unit">ha</span></div>
      </div>
      <div class="metric-card">
        <div class="metric-label">입목축적</div>
        <div class="metric-value">${s.volumePerHa}<span class="metric-unit">m³/ha</span></div>
      </div>
      <div class="metric-card">
        <div class="metric-label">탄소저장량</div>
        <div class="metric-value">${s.carbonPerHa}<span class="metric-unit">tCO₂/ha</span></div>
      </div>
      <div class="metric-card">
        <div class="metric-label">지위지수</div>
        <div class="metric-value">SI ${s.siteIndex}</div>
      </div>
    </div>
    <div style="font-size:12px;color:#666;margin-bottom:6px">등급별 재적 분포</div>
    <div class="grade-bar">${gradeBar}</div>
    <div style="font-size:11px;color:#888">
      특용재 ${s.gradeDistribution.teukYongJae}% / 1등급 ${s.gradeDistribution.grade1}% / 2등급 ${s.gradeDistribution.grade2}% / 3등급 ${s.gradeDistribution.grade3}% / 원주재 ${s.gradeDistribution.wonJuJae}% / 원료재 ${s.gradeDistribution.wonRyoJae}%
    </div>
  </div>

  <!-- 2. 권장 시나리오 -->
  ${best ? `
  <div class="section">
    <div class="section-title">2. 권장 시나리오 (Module C)</div>
    <div class="recommend-box">
      <div class="recommend-title">최적 시나리오</div>
      <div class="recommend-value">${best.name}</div>
      <div class="recommend-npv">30년 NPV 중앙값: ${best.npv.p50.toLocaleString()}만원 (범위: ${best.npv.p5.toLocaleString()} ~ ${best.npv.p95.toLocaleString()}만원)</div>
      <div style="font-size:12px;color:#555;margin-top:6px">${best.description}</div>
    </div>
  </div>` : ""}

  <!-- 3. 시나리오 비교 -->
  <div class="section">
    <div class="section-title">3. 전체 시나리오 NPV 비교 (Monte Carlo 2,000회)</div>
    <table>
      <thead>
        <tr>
          <th>시나리오</th>
          <th style="text-align:right">NPV p50</th>
          <th style="text-align:right">범위 (p5~p95)</th>
          <th style="text-align:center">손실확률</th>
          <th style="text-align:center">KOC</th>
        </tr>
      </thead>
      <tbody>${scenarioRows}</tbody>
    </table>
    <div style="font-size:11px;color:#999;margin-top:6px">할인율 ${m.discountRate}% · 가격 기준일 ${m.priceDate} · SSP1-2.6 기준</div>
  </div>

  <!-- 4. 시장 데이터 -->
  <div class="section">
    <div class="section-title">4. 탄소·목재 시장 데이터 (Module D)</div>
    <div class="market-grid">
      <div class="market-item">
        <div class="market-label">KAU 종가</div>
        <div class="market-val">${m.kauPrice.toLocaleString()}원/tCO₂</div>
      </div>
      <div class="market-item">
        <div class="market-label">KOC 추정가</div>
        <div class="market-val">${m.kocEstimate.toLocaleString()}원/tCO₂</div>
      </div>
      <div class="market-item">
        <div class="market-label">WTA 하한(박2020)</div>
        <div class="market-val">${(m.vcmFloorWta ?? 17039).toLocaleString()}원/tCO₂</div>
      </div>
    </div>
    <div style="margin-top:10px;font-size:12px;color:#555">
      목재 단가 — 특용재 ${(m.timberPrices.teukYongJae/1000).toFixed(0)}k / 1등급 ${(m.timberPrices.grade1/1000).toFixed(0)}k / 2등급 ${(m.timberPrices.grade2/1000).toFixed(0)}k / 3등급 ${(m.timberPrices.grade3/1000).toFixed(0)}k 원/m³ (KOFPI 2025 Q4)
    </div>
  </div>

  <!-- 5. 탄소상쇄 등록 가능성 -->
  ${elig ? `
  <div class="section">
    <div class="section-title">5. 산림탄소상쇄 등록 가능성</div>
    <div class="koc-box">
      <div style="font-weight:600;color:${elig.eligible ? "#1565c0" : "#555"};margin-bottom:6px">
        ${elig.eligible ? "✅ 등록 요건 충족" : "⚠️ 등록 요건 미충족"}
      </div>
      ${elig.matchedTypes.length > 0 ? `<div style="font-size:12px;color:#333;margin-bottom:4px">매칭 사업유형: ${elig.matchedTypes.join(", ")}</div>` : ""}
      <div style="font-size:12px;color:#555">
        다음 단계: ${elig.nextSteps.join(" → ")}
      </div>
    </div>
  </div>` : ""}

  <!-- 푸터 -->
  <div class="footer">
    <div>본 보고서는 시나리오 비교를 위한 추정값이며 정확한 수익을 보장하지 않습니다.</div>
    <div>MOFOM AI · ${m.priceDate}</div>
  </div>

</div>
</body>
</html>`;
}

// ── 사이드바 컴포넌트 ─────────────────────────────────────────────────────────
export default function ReportSidebar({ data }: { data: PartialResult | null }) {
  const [isGenerating, setIsGenerating] = useState(false);

  const ready = !!(data?.state && data?.market && data?.scenarios);

  const handleGenerate = async () => {
    if (!data || !ready) return;
    setIsGenerating(true);
    try {
      // 로고를 base64로 embed (새 탭 blob URL에서 /logo.png가 깨지지 않게)
      let logoDataUrl = "";
      try {
        const resp = await fetch("/logo.png");
        const imgBlob = await resp.blob();
        logoDataUrl = await new Promise<string>((resolve) => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(reader.result as string);
          reader.readAsDataURL(imgBlob);
        });
      } catch {
        // 실패 시 이모지 fallback
      }

      const html = buildReportHTML(data, logoDataUrl);
      const blob = new Blob([html], { type: "text/html;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const win = window.open(url, "_blank");
      if (win) win.focus();
    } finally {
      setTimeout(() => setIsGenerating(false), 800);
    }
  };

  const best = data?.scenarios?.find((s) => s.recommended);

  return (
    <div className="w-[168px] shrink-0 flex flex-col gap-3">

      {/* 보고서 생성 카드 */}
      <div className="bg-black/45 backdrop-blur-md border border-white/10 shadow-xl rounded-xl p-4 flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-forest-300 shrink-0" />
          <p className="text-sm font-semibold text-forest-100">보고서</p>
        </div>

        <button
          onClick={handleGenerate}
          disabled={!ready || isGenerating}
          className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg text-xs font-semibold transition-all duration-200
            bg-forest-700 border border-forest-500 text-forest-100
            hover:bg-forest-600 hover:border-forest-400 hover:shadow-[0_0_10px_rgba(106,171,112,0.25)]
            disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {isGenerating ? (
            <span className="animate-pulse">생성 중...</span>
          ) : (
            <>
              <Printer className="w-3.5 h-3.5" />
              PDF 보고서 생성
            </>
          )}
        </button>

        {ready && (
          <p className="text-[10px] text-forest-300 text-center leading-tight font-medium">
            새 탭에서 열린 후<br />Ctrl+P로 PDF 저장
          </p>
        )}
        {!ready && (
          <p className="text-[10px] text-forest-600 text-center leading-tight">
            분석 완료 후<br />활성화됩니다
          </p>
        )}
      </div>

      {/* 요약 지표 카드 */}
      {data?.state && (
        <div className="bg-black/45 backdrop-blur-md border border-white/10 shadow-xl rounded-xl p-4 flex flex-col gap-3 animate-slide-up">
          <div className="flex items-center gap-2">
            <TreePine className="w-4 h-4 text-forest-400 shrink-0" />
            <p className="text-xs font-semibold text-forest-300">임야 요약</p>
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-forest-500">수종</span>
              <span className="text-forest-200 font-medium text-right leading-tight max-w-[90px] truncate">{data.state.species}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-forest-500">임령</span>
              <span className="text-forest-200 font-medium">{data.state.estimatedAge}년</span>
            </div>
            <div className="flex justify-between">
              <span className="text-forest-500">면적</span>
              <span className="text-forest-200 font-medium">{data.state.areaHa}ha</span>
            </div>
            <div className="flex justify-between">
              <span className="text-forest-500">축적</span>
              <span className="text-forest-200 font-medium">{data.state.volumePerHa}m³</span>
            </div>
            <div className="flex justify-between">
              <span className="text-forest-500">탄소</span>
              <span className="text-forest-200 font-medium">{data.state.carbonPerHa}t</span>
            </div>
          </div>
        </div>
      )}

      {/* 권장 시나리오 카드 */}
      {best && (
        <div className="bg-black/45 backdrop-blur-md border border-forest-600/40 shadow-xl rounded-xl p-4 flex flex-col gap-2 animate-slide-up">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-forest-300 shrink-0" />
            <p className="text-xs font-semibold text-forest-300">권장</p>
          </div>
          <p className="text-xs font-bold text-forest-100">{best.name}</p>
          <p className="text-sm font-bold text-forest-200">
            {best.npv.p50.toLocaleString()}
            <span className="text-xs font-normal text-forest-500 ml-0.5">만원</span>
          </p>
          <div className="flex items-center gap-1">
            <ChevronRight className="w-3 h-3 text-forest-500" />
            <span className="text-[10px] text-forest-500">NPV 중앙값</span>
          </div>
        </div>
      )}

      {/* KOC 등록 가능 */}
      {data?.offsetEligibility?.eligible && (
        <div className="bg-[#0d1f2d]/70 backdrop-blur-md border border-[#3f6480]/40 shadow-xl rounded-xl p-4 flex flex-col gap-1.5 animate-slide-up">
          <div className="flex items-center gap-2">
            <Leaf className="w-4 h-4 text-[#5a8098] shrink-0" />
            <p className="text-xs font-semibold text-[#7aabcc]">탄소상쇄</p>
          </div>
          <p className="text-[10px] text-[#5a8098] leading-snug">KOC 등록<br/>요건 충족</p>
        </div>
      )}

      {/* 분석 통계 */}
      {data?.scenarios && (
        <div className="bg-black/45 backdrop-blur-md border border-white/10 shadow-xl rounded-xl p-4 flex flex-col gap-2 animate-slide-up">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-forest-400 shrink-0" />
            <p className="text-xs font-semibold text-forest-300">분석 통계</p>
          </div>
          <div className="space-y-1.5 text-[10px]">
            <div className="flex justify-between">
              <span className="text-forest-600">시나리오</span>
              <span className="text-forest-400">{data.scenarios.length}개</span>
            </div>
            <div className="flex justify-between">
              <span className="text-forest-600">MC 샘플</span>
              <span className="text-forest-400">2,000회</span>
            </div>
            <div className="flex justify-between">
              <span className="text-forest-600">모델</span>
              <span className="text-forest-400">F-H NPV</span>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
