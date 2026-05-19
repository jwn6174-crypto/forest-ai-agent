// Module A 출력: 현재 임야 상태
export interface ForestState {
  pnu: string;
  species: string;
  estimatedAge: number;
  volumePerHa: number;
  volumeUncertainty: number;
  carbonPerHa: number;
  agbPerHa: number;
  areaHa: number;
  gradeDistribution: GradeDistribution;
  forestType: "침엽수" | "활엽수" | "혼효림";
  siteIndex: number;
  coordinates: { lat: number; lng: number };
  // Module B 현재 시점 추가 필드
  tmaiNow?: number;       // 총평균재적생장량 (m³/ha/yr)
  heightNow?: number;     // 현재 수고 (m)
  nPerHaNow?: number;     // 현재 ha당 본수
  dataMethod?: string;    // 수확표 lookup 방법
  dataWarning?: string | null;
}

export interface GradeDistribution {
  teukYongJae: number; // 특용재 (%)
  grade1: number;
  grade2: number;
  grade3: number;
  wonJuJae: number; // 원주재 (%)
  wonRyoJae: number; // 원료재 (%)
}

// Module B 출력: 성장 예측
export interface GrowthForecast {
  years: number[];
  volumePerHa: number[];
  carbonPerHa: number[];
  carbonSequestration: number[]; // tCO2/ha/yr
  gradeDistributionByYear: GradeDistribution[];
  climateScenario: "SSP1-2.6" | "SSP2-4.5" | "SSP5-8.5";
  // Module B 전달 필드
  dbhTrajectory: number[];          // 평균 흉고직경 (cm)
  heightTrajectory: number[];       // 평균 수고 (m)
  nPerHaTrajectory: number[];       // ha당 본수
  tmaiTrajectory: number[];         // 총평균재적생장량 (m³/ha/yr)
  dataMethod?: string;              // "exact" | "interpolated" | ...
  dataWarning?: string | null;
}

// Module C 출력: 시나리오별 LEV/NPV
export interface Scenario {
  id: "immediate" | "five_year" | "ten_year" | "koc" | "ntfp";
  name: string;
  description: string;
  harvestYear: number | null;
  npv: {
    p5: number;   // 만원
    p50: number;
    p95: number;
    bankruptcyProb: number; // NPV<0 확률
  };
  timberRevenue: number; // 만원
  carbonRevenue: number;
  harvestCost: number;
  regenCost: number;
  ntfpRevenue: number;
  kocEligible: boolean;
  kocMethodology?: string;
  paretoX: number; // 유동성 점수 (0=장기, 1=즉시)
  recommended: boolean;
}

// Module D 출력: 시장 데이터
export interface MarketData {
  kauPrice: number;      // 원/tCO₂
  kocEstimate: number;
  timberPrices: {
    teukYongJae: number;
    grade1: number;
    grade2: number;
    grade3: number;
    wonJuJae: number;
    wonRyoJae: number;
  };
  discountRate: number;  // %
  priceDate: string;
  vcmFloorWta?: number;  // 산주 WTA 하한 (원/tCO₂, 박2020)
}

export interface OffsetEligibility {
  eligible: boolean;
  matchedTypes: string[];
  baselineCarbon: number;
  additionalityCheck: boolean;
  nextSteps: string[];
}

export interface ModuleStatus {
  A: "idle" | "loading" | "done" | "error";
  B: "idle" | "loading" | "done" | "error";
  C: "idle" | "loading" | "done" | "error";
  D: "idle" | "loading" | "done" | "error";
  E: "idle" | "loading" | "done" | "error";
}

// 전체 분석 결과
export interface ForestAnalysisResult {
  pnu: string;
  analyzedAt: string;
  state: ForestState;
  growth: GrowthForecast;
  scenarios: Scenario[];
  market: MarketData;
  recommendation: string; // 권장 시나리오 ID
  offsetEligibility: OffsetEligibility;
}

// 부분 결과 (단계적 노출용)
export interface PartialResult {
  pnu: string;
  state?: ForestState;
  growth?: GrowthForecast;
  scenarios?: Scenario[] | null;  // null = Module C 미구현
  market?: MarketData;
  recommendation?: string | null;
  offsetEligibility?: OffsetEligibility;
}

// 채팅
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}
