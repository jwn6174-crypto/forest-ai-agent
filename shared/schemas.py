"""
shared/schemas.py
모듈 B/D ↔ C (Lead) ↔ E (UI/LLM) 사이 *데이터 인터페이스* Pydantic 모델.

가이드 §8.1 명세를 *기본* 으로 하되, 우리 진짜 자산 (수종별 가격, 출처 메타) 을
Optional 필드로 *후방 호환성* 유지하며 확장.

희도가 모듈 C 에서:
    from shared.schemas import MarketSnapshot
    snap_dict = market_snapshot("2026-05-13")
    snap = MarketSnapshot(**snap_dict)   # 검증 + 타입 안전

    # IDE 자동완성:
    snap.timber_price["1등급"]               # 가이드 기본
    snap.timber_price_by_species["잣나무"]   # 우리 확장 (선택)
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional, Any


# ============================================================
# 1. GrowthForecast (growth_predict 반환)
# ============================================================


class GrowthForecast(BaseModel):
    """
    임분 성장 예측 결과 (가이드 §8.1 매칭).

    growth_predict() 가 List[dict] 반환 → 이 모델로 *각 시점* 또는 *전체* 매핑.

    호환성: 가이드 명세는 *trajectory* 가 List[float] 단위.
            우리는 *시점별 dict* 반환 → 변환 헬퍼 제공 (`from_trajectory_dicts`).
    """

    species: str = Field(..., description="수종명 (예: '강원지방소나무')")
    site_index: int = Field(..., description="지위지수")
    age_now: int = Field(..., description="현재 임령 (년)")
    climate_scenario: Literal["baseline", "SSP126", "SSP245", "SSP585"] = "baseline"

    # 가이드 §8.1 명세 (List 형식)
    forecast_years: List[int] = Field(..., description="예측 시점 (년) [0, 5, 10, ...]")
    volume_trajectory: List[float] = Field(..., description="m³/ha 시계열")
    dbh_trajectory: List[float] = Field(..., description="평균 흉고직경 (cm) 시계열")
    height_trajectory: List[float] = Field(..., description="평균 수고 (m) 시계열")
    n_per_ha_trajectory: List[float] = Field(..., description="ha 당 본수 시계열")

    # 가이드 §8.1 확장 (NPV 등급분포·탄소)
    grade_distribution_trajectory: Optional[List[Dict[str, float]]] = Field(
        None, description="시점별 등급분포 (추후 Weibull fit 후 추가)"
    )
    carbon_uptake_rate: Optional[List[float]] = Field(
        None, description="tCO2/ha/yr 시계열 (추후 산림탄소 모델 통합)"
    )

    # 우리 확장 (현재 구현)
    tmai_trajectory: Optional[List[float]] = Field(
        None, description="총평균재적생장량 (m³/ha/yr)"
    )
    method: str = Field("exact", description="lookup|interpolated|exact")
    warning: Optional[str] = None

    @classmethod
    def from_trajectory_dicts(
        cls,
        trajectory: List[Dict[str, Any]],
        species: str,
        site_index: int,
        age_now: int,
        climate_scenario: str = "baseline",
    ) -> "GrowthForecast":
        """growth_predict() 의 List[dict] 출력을 GrowthForecast 로 변환."""
        return cls(
            species=species,
            site_index=site_index,
            age_now=age_now,
            climate_scenario=climate_scenario,
            forecast_years=[d["age"] - age_now for d in trajectory],
            volume_trajectory=[d.get("volume", 0.0) for d in trajectory],
            dbh_trajectory=[d.get("dbh", 0.0) for d in trajectory],
            height_trajectory=[d.get("height", 0.0) for d in trajectory],
            n_per_ha_trajectory=[d.get("n_per_ha", 0.0) for d in trajectory],
            tmai_trajectory=[d.get("tmai_m3_per_ha_yr", 0.0) for d in trajectory],
            method=trajectory[0].get("method", "exact") if trajectory else "exact",
            warning=trajectory[0].get("warning") if trajectory else None,
        )


# ============================================================
# 2. MarketSnapshot (market_snapshot 반환)
# ============================================================


class MarketSnapshot(BaseModel):
    """
    종합 시장 스냅샷 (가이드 §6.3 + §8.1 매칭 + 우리 자산 확장).

    가이드 기본: timber_price (소나무 6 등급) + KAU/KOC + WTA + discount_rate
    우리 확장:   timber_price_by_species (7 수종), 출처 메타, KAU 상세
    """

    date: str = Field(..., description="ISO 8601 날짜 (예: '2026-05-13')")

    # 가이드 §8.1 기본 필드
    timber_price: Dict[str, Optional[int]] = Field(
        ...,
        description="6 등급 가격 (소나무 기본). 예: {'1등급': 199700, '2등급': 173400}",
    )
    kau_close: Optional[float] = Field(None, description="KAU 종가 원/tCO2")
    koc_estimate: Optional[float] = Field(None, description="KOC 추정/실거래 원/tCO2")
    vcm_floor_wta: float = Field(17039, description="박2020 산주 WTA 하한 원/tCO2")
    discount_rate: float = Field(0.05, description="할인율 (산주 평균)")

    # 우리 확장 — 수종별 가격
    timber_price_by_species: Optional[Dict[str, Dict[str, Optional[int]]]] = Field(
        None, description="7 수종 × 6 등급. 예: {'잣나무': {'1등급': 154700, ...}}"
    )

    # 우리 확장 — 출처 메타
    timber_price_meta: Optional[Dict[str, Any]] = Field(
        None, description="가격 데이터 출처·기간·법적 근거·단위 환산"
    )
    kau_meta: Optional[Dict[str, Any]] = Field(
        None, description="KAU vintage·실제 거래일·KOC 출처"
    )


# ============================================================
# 3. CostBreakdown + CostInput (cost_function 입출력)
# ============================================================


class CostInput(BaseModel):
    """
    cost_function() 의 *입력* 파라미터 (가이드 §8.1 의 CostFunction).

    가이드 §8.1 의 CostFunction 은 *함수 입력 변수* 모델로 해석.
    우리는 *입력* 과 *출력 (breakdown)* 을 분리.
    """

    volume_m3: float = Field(..., description="벌채 또는 처리 재적 (m³)")
    area_ha: float = Field(..., description="임지 면적 (ha)")
    distance_to_road_km: float = Field(..., description="도로까지 거리 (km)")
    action: Literal["clearcut", "thinning", "planting"] = Field(
        ..., description="작업 종류"
    )
    skidding_distance_m: float = Field(500.0, description="집재 거리 (m)")
    slope_class: Literal["완", "중", "급"] = Field("중", description="경사도 분류")


class CostBreakdown(BaseModel):
    """
    cost_function() 의 *출력* — 비용 분해 + 메타.
    """

    breakdown: Dict[str, int] = Field(..., description="항목별 비용 (원)")
    subtotal: int = Field(..., description="직접비 합 (원)")
    admin_overhead_amount: int = Field(..., description="간접비 (원)")
    total: int = Field(..., description="총 비용 (원, 간접비 포함)")

    # 시연용 메타
    slope_surcharge_applied: float = Field(..., description="적용 할증률")
    unit_costs: Dict[str, int] = Field(..., description="항목별 단위 비용")
    data_sources: Dict[str, str] = Field(..., description="각 항목 출처")
    limitations: List[str] = Field(default_factory=list, description="알려진 한계")


# ============================================================
# 4. RotationRule (rotation_age 반환)
# ============================================================


class RotationRule(BaseModel):
    """
    법정 기준벌기령 (가이드 §8.1 매칭).

    rotation_age() 는 int 반환 → 이 모델로 *컨텍스트* 포함 매핑.
    """

    species: str = Field(..., description="수종명")
    ownership: Literal["사유림", "국유림", "공유림"] = Field(
        "사유림", description="소유 구분"
    )
    legal_min_age: int = Field(..., description="법정 기준벌기령 (년)")

    # 우리 확장
    legal_basis: str = Field(
        "산림자원의 조성 및 관리에 관한 법률 시행규칙 별표 3 (개정 2023-06-27)",
        description="법적 근거",
    )
    species_category: Optional[str] = Field(
        None, description="법령 분류 (예: '강원지방소나무' → '소나무류')"
    )


# ============================================================
# 메모: 가이드 §8.1 매칭 vs 우리 확장
# ============================================================
"""
| 모델 | 가이드 §8.1 매칭 | 우리 확장 |
|---|---|---|
| GrowthForecast | volume/dbh/height/n_per_ha trajectory | tmai_trajectory, method, warning |
| MarketSnapshot | timber_price, kau/koc, wta, discount_rate | by_species, meta (출처) |
| CostInput/Breakdown | CostFunction (입력 변수) | Breakdown + 출처 + 한계 명시 |
| RotationRule | species, ownership, legal_min_age | legal_basis, species_category |

원칙:
- 가이드 §8.1 명세 100% 호환 (모든 필드 *required* 또는 *동일 default*)
- 우리 자산은 *Optional* 또는 *default 빈값* — 후방 호환성
- 정직히 *가이드 + 우리 추가* 차이 *주석* 표시
"""


if __name__ == "__main__":
    print("=" * 60)
    print("📋 shared/schemas.py 자가 검증")
    print("=" * 60)

    # 검증 1: 빈 모델 생성 가능?
    print("\n[검증 1] 가이드 §8.1 기본 필드만으로 생성")
    snap = MarketSnapshot(
        date="2026-05-13",
        timber_price={"1등급": 199700, "2등급": 173400},
        kau_close=17200.0,
        koc_estimate=12040.0,
    )
    print(f"   ✅ MarketSnapshot 가이드 기본: date={snap.date}, KAU={snap.kau_close}")

    # 검증 2: 우리 확장 필드 포함
    print("\n[검증 2] 우리 확장 필드 포함 생성")
    snap2 = MarketSnapshot(
        date="2026-05-13",
        timber_price={"1등급": 199700},
        kau_close=17200.0,
        koc_estimate=12040.0,
        timber_price_by_species={"잣나무": {"1등급": 154700}},
        timber_price_meta={"source": "KOFPI Q4 2025"},
    )
    print(
        f"   ✅ MarketSnapshot 확장: 잣나무 1등급={snap2.timber_price_by_species['잣나무']['1등급']}"
    )

    # 검증 3: RotationRule
    print("\n[검증 3] RotationRule")
    rule = RotationRule(
        species="강원지방소나무",
        ownership="사유림",
        legal_min_age=40,
        species_category="소나무류",
    )
    print(f"   ✅ {rule.species} {rule.ownership}: 기준벌기령 {rule.legal_min_age}년")

    # 검증 4: CostInput + CostBreakdown
    print("\n[검증 4] CostInput")
    inp = CostInput(
        volume_m3=280,
        area_ha=1.0,
        distance_to_road_km=15,
        action="clearcut",
    )
    print(
        f"   ✅ CostInput: {inp.action}, {inp.volume_m3}m³, {inp.distance_to_road_km}km"
    )

    # 검증 5: GrowthForecast
    print("\n[검증 5] GrowthForecast from trajectory")
    fake_traj = [
        {
            "age": 30,
            "volume": 173.0,
            "dbh": 16.9,
            "height": 12.0,
            "n_per_ha": 1261,
            "tmai_m3_per_ha_yr": 5.77,
            "method": "exact",
        },
        {
            "age": 50,
            "volume": 281.0,
            "dbh": 22.0,
            "height": 17.5,
            "n_per_ha": 950,
            "tmai_m3_per_ha_yr": 5.62,
            "method": "exact",
        },
    ]
    fc = GrowthForecast.from_trajectory_dicts(
        trajectory=fake_traj,
        species="강원지방소나무",
        site_index=14,
        age_now=30,
    )
    print(f"   ✅ GrowthForecast: {fc.species} SI={fc.site_index}")
    print(f"      forecast_years: {fc.forecast_years}")
    print(f"      volume_trajectory: {fc.volume_trajectory}")

    print()
    print("=" * 60)
    print("✅ 모든 스키마 작동 확인")
    print("=" * 60)

# ============================================================
# Module C 추가 (희도 D101) — 2026-05-20 Day 6
# Manual 01 §4.1 호환 + 옵션 P2 확장 (정우 D4 동일 패턴)
# 정우 D9 (임가경제) 와 ADR 번호 충돌 회피 위해 D101부터 시작
# ============================================================


class LEVResult(BaseModel):
    """
    Faustmann–Hartman LEV 계산 결과 (단일 시나리오 1건). 희도 D101.

    compute_lev() 가 Dict[scenario_name, LEVResult] 반환:
        results = compute_lev(stand, ["즉시","10년","연장KOC"])
        # results["즉시"].npv_per_ha, results["10년"].lev_per_ha 등
    """

    # ----- Manual 01 §4.1 필수 필드 -----
    scenario: str = Field(
        ...,
        description="시나리오 명: '즉시', '5년', '10년', '연장KOC', '임산물', '간벌+10년' (D110)",
    )
    T_optimal: int = Field(..., ge=0, le=200, description="벌기령 (년)")
    npv_per_ha: float = Field(..., description="순현재가치 중앙값 (원/ha)")
    npv_q05: float = Field(..., description="NPV 5% 분위수 (원/ha)")
    npv_q95: float = Field(..., description="NPV 95% 분위수 (원/ha)")
    lev_per_ha: float = Field(..., description="임지기대치 LEV (원/ha)")
    timber_revenue: float = Field(..., description="원목 수입 중앙값 (원)")
    carbon_revenue: float = Field(..., description="탄소 수입 중앙값 (원)")
    ntfp_revenue: float = Field(0.0, description="임산물 수입 (시나리오 5만 비영)")
    total_cost: float = Field(..., description="총 비용 (원)")
    carbon_stock_T: float = Field(..., description="T시점 탄소 저장량 (tCO₂/ha)")
    grade_distribution_T: Dict[str, float] = Field(
        ...,
        description="T시점 등급별 재적 비율 (특용재/1·2·3등급/원주재/원료재)",
    )
    feasibility: bool = Field(..., description="법정 기준벌기령 충족 여부")
    feasibility_note: Optional[str] = Field(
        None, description="feasibility=False 시 사유"
    )

    # ----- 우리 확장 (Optional, 옵션 P2) -----
    monte_carlo_n: Optional[int] = Field(1000, description="LHS samples")
    discount_rate: Optional[float] = Field(
        0.05, description="할인율 (민감도 0.04-0.07)"
    )
    timber_breakdown_by_grade: Optional[Dict[str, float]] = None
    carbon_uptake_trajectory: Optional[List[float]] = None
    cost_breakdown: Optional[Dict[str, float]] = None
    data_sources: Optional[Dict[str, str]] = None
    limitations: Optional[List[str]] = Field(default_factory=list)

    # ----- D101.1 추가 (deliberation 결과) -----
    uncertainty_tier: Optional[Literal["high", "med", "low"]] = Field(
        "med",
        description="q05-q95 폭에 따른 자동 tier (AI D106)",
    )
    uncertainty_note: Optional[str] = None
    kau_breakeven: Optional[float] = Field(
        None,
        description="KAU 임계가 (원/tCO₂). D115 학술 발견 — WTA 17,039원 첫 돌파 2026-03~05.",
    )
    kau_breakeven_note: Optional[str] = None
    climate_multiplier_applied: Optional[float] = Field(
        None,
        description="MC 적용 climate growth multiplier (산림학자 D103.b)",
    )


class ComputeLEVRequest(BaseModel):
    """수범 module_e 의 LLM agent 가 compute_lev tool 호출 시 입력. 희도 D101."""

    stand_state: Dict[str, Any]
    scenarios: List[
        Literal["즉시", "5년", "10년", "연장KOC", "임산물", "간벌+10년"]
    ] = Field(
        ...,
        description="최대 6 시나리오 (D110 간벌+10년 포함)",
    )
    discount_rate: float = Field(0.05, ge=0.01, le=0.20)
    n_monte_carlo: int = Field(1000, ge=100, le=10000)
    climate_scenario: Literal["baseline", "SSP126", "SSP245", "SSP585"] = "baseline"


class DraftPlanCard(BaseModel):
    """의사결정 카드 — 산주 + 정책 부록 이중 표현. 희도 D101 + Round 2 산주."""

    recommended_scenario: str
    npv_median: float
    npv_q05: float
    npv_q95: float
    age_now: int
    legal_min_age: int
    npv_uplift_label: str
    reasons: List[str]
    offset_citations: Optional[List[Dict[str, Any]]] = None
    next_actions: List[str]
    user_preference: Literal["위험회피", "균형", "수익극대화"] = "균형"
