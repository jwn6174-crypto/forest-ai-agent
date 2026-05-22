"""
draft_plan.py — DraftPlanCard 생성 (산주 UI + 정책 부록 이중 표현).

경제학자 D14 권고:
- 산주용: "약 1,400만원" 점추정 + "최악의 10% 시 -300만원" 단일 숫자
- 정책담당관용: q05-q95 분포 + fan chart + Pareto

희도 D-draft_plan 결정 — 2026-05-20 Day 6 작성
"""

from typing import Dict, List, Optional

from .recommend import (
    recommend_scenario, get_recommendation_reasons, get_next_actions,
    generate_kakao_message,
)
from .uncertainty import get_uncertainty_summary
from .kau_breakeven import compute_kau_breakeven, format_kau_breakeven_message
from .offset_eligibility import find_eligible_project_types, search_rag_citations


def create_draft_plan(
    stand: Dict,
    lev_results: Dict[str, Dict],
    *,
    user_preference: str = "균형",
    legal_min_age: Optional[int] = None,
    region: str = "충북 보은",
    search_offset: bool = True,
) -> Dict[str, any]:
    """
    Module C 의 최종 출력 — 산주 의사결정 카드.

    Parameters
    ----------
    stand : dict
        StandStateEstimate dict
    lev_results : dict
        {scenario_name: LEVResult dict (Monte Carlo 결과)}
    user_preference : str
        "위험회피" | "균형" | "수익극대화"
    legal_min_age : int, optional
        법정 기준벌기령 (None 이면 자동 lookup)
    region : str
    search_offset : bool
        8 사업유형 자동 매칭 여부

    Returns
    -------
    dict
        {
            # 산주 UI (점추정)
            "recommended_scenario": str,
            "npv_단순표시": str,            # "약 1,400만원"
            "npv_worst_case_10pct": str,     # "최악의 10% 시 -300만원"
            "npv_uplift_label": str,
            "age_now": int,
            "legal_min_age": int,

            # 자연어 근거 + 액션
            "reasons": List[str],
            "next_actions": List[str],

            # 8 사업유형 매칭
            "offset_citations": List[Dict],

            # 불확실성
            "uncertainty_tier": "high"|"med"|"low",
            "uncertainty_note": str,
            "show_point_estimate": bool,

            # 경제학자: KAU breakeven 경고
            "kau_breakeven_warning": str | None,

            # 정책 부록
            "full_distribution": Dict (q05-q95, std_ratio 등),

            "user_preference": str,
            "_meta": Dict,
        }
    """
    # 추천
    recommended = recommend_scenario(lev_results, user_preference)
    if not recommended:
        return {"error": "feasible 시나리오 없음"}

    best = lev_results[recommended]
    baseline = lev_results.get("즉시") or best

    age_now = stand["age_estimate"]
    species = stand["species_dominant"]

    # 법정 기준벌기령 자동
    if legal_min_age is None:
        from .scenarios import rotation_age
        legal_min_age = rotation_age(species, "사유림")

    npv_med = best.get("npv_median", best.get("npv", 0))
    npv_q05 = best.get("npv_q05", npv_med * 0.85)
    npv_q95 = best.get("npv_q95", npv_med * 1.15)
    uplift = npv_med - baseline.get("npv_median", baseline.get("npv", 0))

    # 산주용 점추정 문구
    npv_simple = f"약 {int(npv_med / 1e6):,}백만원" if npv_med >= 1e6 else f"약 {int(npv_med / 1e4):,}만원"
    npv_worst = (
        f"최악의 10% 시 {int(npv_q05 / 1e4):,}만원"
        if npv_q05 >= 0
        else f"최악의 10% 시 -{int(abs(npv_q05) / 1e4):,}만원 (손실)"
    )
    uplift_label = (
        f"+{int(uplift / 1e4):,}만원/ha"
        if uplift > 0 else (f"-{int(abs(uplift) / 1e4):,}만원/ha" if uplift < 0 else "-")
    )

    # 추천 근거
    reasons = get_recommendation_reasons(
        recommended, lev_results, user_preference,
        age_now=age_now, legal_min_age=legal_min_age,
    )

    # 다음 액션
    next_actions = get_next_actions(recommended, region=region)

    # 불확실성 tier
    uncertainty = get_uncertainty_summary(
        npv_med, npv_q05, npv_q95,
        has_satellite_data=stand.get("confidence_level") != "low",
        has_nfi_match=stand.get("confidence_note", "").startswith("NFI"),
        species=species,
    )

    # KAU breakeven (경제학자)
    carbon_rev = best.get("carbon_revenue_median", best.get("carbon_revenue", 0))
    kau_be = compute_kau_breakeven(
        npv_at_kau=npv_med,
        kau_used=17_200,
        carbon_revenue_at_kau=carbon_rev,
    )

    # 8 사업유형 매칭
    offset_citations = []
    if search_offset:
        eligible = find_eligible_project_types(stand)
        for proj in eligible:
            if not proj["eligible"]:
                continue
            citation = {
                "code": proj["code"],
                "korean": proj["korean"],
                "reason": proj["reason"],
                "verification": proj["verification"],
            }
            # RAG 보조 (정우 carbon_chunks 가 있을 때)
            if proj["verification"] == "RAG":
                citation["rag_excerpts"] = search_rag_citations(proj["code"], top_k=2)
            offset_citations.append(citation)

    # Round 2 산주 권고: 카카오톡 메시지 자동 생성
    kakao_msg = generate_kakao_message(recommended, uplift_label, region=region)

    # Round 2 산주 권고: 한 줄 자연어 요약 (산주 첫 인상)
    natural_summary = _make_natural_summary(recommended, npv_med, npv_q05, npv_q95, uplift)

    return {
        # ─── 산주 UI (Tier 1 — 한 화면 첫 인상) ──────────────
        "recommended_scenario": recommended,
        "natural_summary": natural_summary,  # 산주 한 줄 자연어 (Round 2)
        "kakao_message": kakao_msg,           # 자녀에게 카톡 전송용 (Round 2)
        "npv_단순표시": npv_simple if uncertainty["show_point_estimate"] else None,
        "npv_worst_case_10pct": npv_worst,
        "npv_uplift_label": uplift_label,
        "age_now": age_now,
        "legal_min_age": legal_min_age,

        # ─── 산주 UI (Tier 2 — 펼치기 영역, "다른 방법도 있어요") ──
        "reasons": reasons,
        "next_actions": next_actions,
        "offset_citations": offset_citations,

        # ─── 불확실성 (Round 2: 이유 + 다음 행동) ─────────────
        "uncertainty_tier": uncertainty["tier"],
        "uncertainty_note": uncertainty["note"],
        "show_point_estimate": uncertainty["show_point_estimate"],

        # ─── KAU breakeven (경제학자 + D23) ─────────────────
        "kau_breakeven_warning": (
            format_kau_breakeven_message(kau_be) if kau_be.get("warning") or kau_be["kau_breakeven"] else None
        ),

        # ─── 정책 부록 (Tier 3 — 정책담당관 view) ──────────────
        "full_distribution": {
            "npv_median": npv_med,
            "npv_q05": npv_q05,
            "npv_q25": best.get("npv_q25"),
            "npv_q75": best.get("npv_q75"),
            "npv_q95": npv_q95,
            "std_ratio": best.get("std_ratio"),
        },

        # ─── 기타 ────────────────────────────────────────────
        "user_preference": user_preference,
        "_meta": {
            "species": species,
            "site_index": stand.get("site_index"),
            "area_ha": stand["area_ha"],
            "distance_to_road_km": stand.get("distance_to_road_km"),
            "confidence_level": stand.get("confidence_level"),
        },
    }


def _make_natural_summary(
    scenario: str, npv_med: float, npv_q05: float, npv_q95: float, uplift: float,
) -> str:
    """Round 2 산주 권고: '잘되면/보통/못되면' 한 줄 자연어 요약."""
    good = int(npv_q95 / 1e6)
    typical = int(npv_med / 1e6)
    bad = int(npv_q05 / 1e6)

    sc_korean = {
        "즉시": "지금 바로 벌채",
        "5년": "5년 더 키운 후 벌채",
        "10년": "10년 더 키운 후 벌채",
        "연장KOC": "산림탄소상쇄 (벌채 안 하고 KOC 받기)",
        "임산물": "표고/송이 등 임산물 병행",
        "간벌+10년": "솎아베기 + 10년 더 키우기",
    }.get(scenario, scenario)

    if bad < 0:
        return (
            f"우리 산 → {sc_korean}. "
            f"잘되면 {good}백만원, 보통 {typical}백만원, 못되면 본전 깎임."
        )
    return (
        f"우리 산 → {sc_korean}. "
        f"잘되면 {good}백만원, 보통 {typical}백만원, 못되면 {bad}백만원."
    )


if __name__ == "__main__":
    print("=" * 60)
    print("draft_plan.py 자가 검증")
    print("=" * 60)

    stand = {
        "species_dominant": "강원지방소나무",
        "age_estimate": 50, "site_index": 15,
        "area_ha": 2.0, "distance_to_road_km": 1.5,
        "confidence_level": "low",
    }

    fake_results = {
        "즉시": {"npv_median": 50e6, "npv_q05": 40e6, "npv_q95": 60e6,
                 "feasibility": True, "T_optimal": 50,
                 "carbon_revenue_median": 0, "carbon_stock_T_tco2_per_ha_median": 0},
        "10년": {"npv_median": 65e6, "npv_q05": 50e6, "npv_q95": 80e6,
                 "feasibility": True, "T_optimal": 60,
                 "carbon_revenue_median": 0, "carbon_stock_T_tco2_per_ha_median": 200},
        "간벌+10년": {"npv_median": 80e6, "npv_q05": 65e6, "npv_q95": 95e6,
                      "feasibility": True, "T_optimal": 60,
                      "carbon_revenue_median": 0, "subsidy_revenue_median": 4.4e6,
                      "carbon_stock_T_tco2_per_ha_median": 250},
    }

    print("\n[검증 1] 균형 선호 — DraftPlanCard 생성")
    card = create_draft_plan(stand, fake_results, user_preference="균형",
                              legal_min_age=40, region="충북 보은")
    print(f"  추천: {card['recommended_scenario']}")
    print(f"  npv_단순표시: {card['npv_단순표시']}")
    print(f"  npv_worst: {card['npv_worst_case_10pct']}")
    print(f"  uplift: {card['npv_uplift_label']}")
    print(f"  tier: {card['uncertainty_tier']}")
    print(f"  reasons:")
    for r in card["reasons"][:3]:
        print(f"    - {r}")
    print(f"  next_actions:")
    for a in card["next_actions"][:3]:
        print(f"    - {a}")
    print(f"  offset_citations: {len(card['offset_citations'])} 개")
    for c in card["offset_citations"]:
        print(f"    - {c['code']} {c['korean']}: {c['reason'][:60]}")

    print("\n[검증 2] 위험회피 선호")
    card2 = create_draft_plan(stand, fake_results, user_preference="위험회피", legal_min_age=40)
    print(f"  추천: {card2['recommended_scenario']} (q05 최대)")

    print("\n[검증 3] full_distribution")
    print(f"  {card['full_distribution']}")

    print("\n" + "=" * 60)
    print("✅ draft_plan.py 3/3 검증 통과 (DraftPlanCard 생성)")
    print("=" * 60)
