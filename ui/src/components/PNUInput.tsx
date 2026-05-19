"use client";
import { useState } from "react";
import { Search, TreePine } from "lucide-react";
import clsx from "clsx";

const DEMO_CASES = [
  { label: "잣나무 50년 · 보은군", pnu: "4372025024100020000" },
  { label: "낙엽송 25년 · 보은군", pnu: "4372025024200040004" },
  { label: "혼효림 40년 · 진안군", pnu: "4371025024100080007" },
];

interface Props {
  onAnalyze: (pnu: string, risk: string) => void;
  isAnalyzing: boolean;
}

export default function PNUInput({ onAnalyze, isAnalyzing }: Props) {
  const [pnu, setPnu] = useState("");
  const [risk, setRisk] = useState("medium");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!pnu.trim() || isAnalyzing) return;
    onAnalyze(pnu.trim(), risk);
  };

  const handleDemo = (demoPnu: string) => {
    setPnu(demoPnu);
    onAnalyze(demoPnu, risk);
  };

  return (
    <div className="space-y-3">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="flex-1 relative">
          <input
            type="text"
            value={pnu}
            onChange={(e) => setPnu(e.target.value)}
            placeholder="PNU 코드 19자리 입력 (예: 4372025024100020000)"
            maxLength={19}
            className={clsx(
              "w-full px-4 py-2.5 rounded-lg text-sm font-mono",
              "bg-forest-850 border border-forest-600 text-forest-100",
              "placeholder:text-forest-600 focus:outline-none focus:border-forest-400",
              "transition-colors duration-200"
            )}
          />
        </div>
        <select
          value={risk}
          onChange={(e) => setRisk(e.target.value)}
          className="px-3 py-2.5 rounded-lg text-sm bg-forest-850 border border-forest-600 text-forest-100 focus:outline-none focus:border-forest-400 cursor-pointer"
        >
          <option value="low">보수적</option>
          <option value="medium">중간</option>
          <option value="high">공격적</option>
        </select>
        <button
          type="submit"
          disabled={!pnu.trim() || isAnalyzing}
          className={clsx(
            "flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold",
            "bg-forest-500 hover:bg-forest-400 text-white",
            "disabled:opacity-40 disabled:cursor-not-allowed",
            "transition-all duration-200"
          )}
        >
          {isAnalyzing ? (
            <>
              <span className="flex gap-0.5">
                <span className="dot-1 w-1.5 h-1.5 rounded-full bg-white inline-block" />
                <span className="dot-2 w-1.5 h-1.5 rounded-full bg-white inline-block" />
                <span className="dot-3 w-1.5 h-1.5 rounded-full bg-white inline-block" />
              </span>
              분석 중
            </>
          ) : (
            <>
              <Search className="w-4 h-4" />
              분석 시작
            </>
          )}
        </button>
      </form>

      <div className="flex items-center gap-2">
        <span className="text-xs text-forest-600">데모:</span>
        {DEMO_CASES.map((c) => (
          <button
            key={c.pnu}
            onClick={() => handleDemo(c.pnu)}
            disabled={isAnalyzing}
            className="flex items-center gap-1 px-2.5 py-1 rounded-md text-xs bg-forest-800 hover:bg-forest-700 text-forest-300 border border-forest-700 hover:border-forest-500 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <TreePine className="w-3 h-3" />
            {c.label}
          </button>
        ))}
      </div>
    </div>
  );
}
