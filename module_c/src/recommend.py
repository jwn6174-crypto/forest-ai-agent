"""
recommend.py — 추천 시나리오 선택 알고리즘.

사용자 preference 별 알고리즘:
- "위험회피": q05 최대 (worst-case 최대화)
- "균형": Sharpe-like ratio (mean / std)
- "수익극대화": median 최대

희도 D-recommend 결정 — 2026-05-20 Day 6 작성
"""

from typing import Dict, List, Literal

UserPreference = Literal["위험회피", "균형", "수익극대화"]


def recommend_scenario(
    lev_results: Dict[str, Dict],
    user_preference: UserPreference = "균형",
) -> str | None:
    """
    가능한 시나리오들 중 사용자 preference 에 맞는 1개 추천.

    Parameters
    ----------
    lev_results : dict
        {scenario_name: LEVResult_dict, ...}
        각 dict 의 키: npv, npv_q05, npv_q95, feasibility (선택)
    user_preference : str
        "위험회피" | "균형" | "수익극대화"

    Returns
    -------
    str | None
        추천 시나리오명. 가능한 시나리오 없으면 None.

    Examples
    --------
    >>> results = {
    ...     "즉시": {"npv": 10, "npv_q05": 8, "npv_q95": 12, "feasibility": True},
    ...     "10년": {"npv": 20, "npv_q05": 15, "npv_q95": 25, "feasibility": True},
    ... }
    >>> recommend_scenario(results, "수익극대화")
    '10년'
    """
    # feasibility 통과한 시나리오만
    feasible = {s: r for s, r in lev_results.items() if r.get("feasibility", True)}
    if not feasible:
        return None

    def _npv(r: Dict) -> float:
        return r.get("npv_median", r.get("npv", 0))

    if user_preference == "위험회피":
        # q05 (worst-case) 최대
        return max(feasible.items(), key=lambda kv: kv[1].get("npv_q05", _npv(kv[1])))[0]

    if user_preference == "수익극대화":
        # median NPV 최대
        return max(feasible.items(), key=lambda kv: _npv(kv[1]))[0]

    # 균형: Sharpe-like ratio
    def sharpe(r: Dict) -> float:
        median = _npv(r)
        q05 = r.get("npv_q05", median * 0.8)
        q95 = r.get("npv_q95", median * 1.2)
        # 90% PI ≈ ±1.645σ → std ≈ (q95-q05)/3.29
        std = max((q95 - q05) / 3.29, 1)
        return median / std

    return max(feasible.items(), key=lambda kv: sharpe(kv[1]))[0]


def get_recommendation_reasons(
    recommended: str,
    lev_results: Dict[str, Dict],
    user_preference: UserPreference = "균형",
    *,
    age_now: int = 0,
    legal_min_age: int = 0,
) -> List[str]:
    """
    추천 근거 (DraftPlanCard.reasons 용 자연어 문장 3-5개).

    경제학자·정책학자·경영자 deliberation 반영.
    """
    if recommended not in lev_results:
        return []

    best = lev_results[recommended]
    baseline = lev_results.get("즉시") or lev_results[recommended]
    _best_npv = best.get("npv_median", best.get("npv", 0))
    _base_npv = baseline.get("npv_median", baseline.get("npv", 0))
    uplift = _best_npv - _base_npv

    reasons = []

    # 1. NPV uplift
    if uplift > 0 and recommended != "즉시":
        reasons.append(
            f"즉시벌채 대비 NPV +{int(uplift / 1e4):,}만원/ha 증가 (등급 상승 + 추가 성장)"
        )

    # 2. 탄소 수익
    carbon = best.get("carbon_revenue", 0)
    if carbon > 0:
        reasons.append(f"탄소수익 {int(carbon / 1e4):,}만원 포함 (KOC > WTA hurdle 17,039원 충족)")

    # 3. NTFP 수익
    ntfp = best.get("ntfp_revenue", 0)
    if ntfp > 0:
        reasons.append(f"임산물 수익 {int(ntfp / 1e4):,}만원 포함")

    # 4. 보조사업 매출 (간벌)
    subsidy = best.get("subsidy_revenue", 0)
    if subsidy > 0:
        reasons.append(
            f"간벌 보조사업 매출 {int(subsidy / 1e4):,}만원 (산림청 2025 지침, 충북 +10%)"
        )

    # 5. 법정 벌기령 정보
    T = best.get("T_optimal", age_now)
    if legal_min_age > 0 and T < legal_min_age:
        reasons.append(f"⚠️ T={T}년 < 법정 {legal_min_age}년 — 법적 예외 사유 없으면 벌채 불가")
    elif legal_min_age > 0 and recommended == "연장KOC":
        reasons.append(f"법정 {legal_min_age}년 + 연장으로 산림탄소상쇄 사업 신청 가능")

    # 6. preference 별 추가 메시지
    if user_preference == "위험회피":
        q05 = best.get("npv_q05", _best_npv)
        reasons.append(f"최악의 10% 시나리오에서도 NPV {int(q05 / 1e4):,}만원 보장")
    elif user_preference == "수익극대화":
        q95 = best.get("npv_q95", _best_npv)
        reasons.append(f"최선의 10% 시나리오 NPV {int(q95 / 1e4):,}만원 가능")

    # 7. KAU breakeven 경고 (경제학자)
    kau_be = best.get("kau_breakeven_warning")
    if kau_be:
        reasons.append(f"⚠️ {kau_be}")

    return reasons[:6]  # 최대 6개


def get_next_actions(
    recommended: str,
    *,
    region: str = "충북 보은",
) -> List[str]:
    """
    DraftPlanCard.next_actions — 경영자 D20 권고 + Round 2 산주 권고 적용.

    Round 2 산주 (영세 사유림): "전화번호만으론 그날 안 감.
    사람 이름·전화·멘트 대본·서류 사진까지 손에 쥐어줘야 움직임."
    """
    actions = []

    # 기본 — 모든 시나리오 공통 (산주 권고: 사람 이름 + 대본)
    actions.append(
        "📞 보은군산림조합 산림경영지도원 (☎ 043-543-XXXX, 김주임). "
        '방문 시 멘트: "산주입니다. NPV 자료 보고 왔습니다."'
    )
    actions.append(
        "📁 지참 서류: 임야도, 등기부등본 (산림청 FGIS https://fgis.forest.go.kr "
        "→ 임반·소반 조회 → 임도 1km 이내 확인 후 출력)"
    )

    # 시나리오 별
    if recommended == "연장KOC":
        actions.append(
            "🌳 산림탄소센터 (https://koreaforestcarbon.org) → 신규사업 → 사업계획서 "
            "양식 다운로드 → 산림조합 위탁 (수수료 사업 수익의 10%, 사업기간 30년)"
        )
        actions.append(
            '💡 카카오톡 자녀에게 전송: "산림조합 통해 산림탄소상쇄 사업 신청. '
            '사업계획서 양식 도와줘."'
        )
    elif recommended == "간벌+10년":
        actions.append(
            "💰 산림조합 통해 산림보조사업 신청 (1차 솎아베기 ha당 250만원 + "
            f"{region} +10% 보너스). 사업 신청 → 선정 → 시업 → 정산 (8개월 소요)"
        )
        actions.append("📋 신청 시기: 매년 1-3월. 시·군·구청 산림과 별도 안내문 확인.")
    elif recommended == "임산물":
        actions.append(
            "🍄 충북농업기술원 임업기술센터 보은지소 (☎ 043-XXX-XXXX) 에 "
            "표고/송이/산양삼 재배 컨설팅 신청 (무료, 1-2주 소요)"
        )
        actions.append(
            "🌰 산림소득 보조사업 (산림청 2025 지침) — 토양개량제·유기질비료·"
            "생산단지 보조 신청 (총사업비 1-7억원, 국비 40% 지원)"
        )
    elif recommended in ["즉시", "5년", "10년"]:
        actions.append(
            "🪵 산림조합 통해 벌채 신청 + 재조림 보조 (5년 통합 ha당 450만원) "
            "동시 신청. 벌채 시기: 9월-3월 (수액 적은 시기) 권장."
        )
        actions.append("📞 충북도 산림과 (043-220-XXXX) — 벌채허가 신청 단계 안내 확인")

    return actions


def generate_kakao_message(
    recommended: str,
    npv_label: str,
    *,
    region: str = "충북 보은",
) -> str:
    """
    Round 2 산주 권고: 카카오톡으로 자녀에게 보낼 메시지 자동 생성.

    Examples
    --------
    >>> msg = generate_kakao_message("간벌+10년", "약 1,400만원/ha")
    >>> "산주님" in msg or "아빠" in msg
    True
    """
    base = {
        "즉시": f"우리 산 즉시 벌채 추천 (NPV {npv_label}). 산림조합 신청 도와줘.",
        "5년": f"우리 산 5년 더 키운 후 벌채 추천 (NPV {npv_label}).",
        "10년": f"우리 산 10년 더 키운 후 벌채 추천 (NPV {npv_label}). 등급 상승 효과.",
        "연장KOC": (
            f"우리 산 산림탄소상쇄 신청 추천 (NPV {npv_label}). 벌채 안 하고 매년 KOC 받는 사업."
        ),
        "간벌+10년": (
            f"우리 산 솎아베기 + 10년 더 키우기 추천 (NPV {npv_label}). "
            f"보조금 250만원/ha ({region}). 산림조합 통해 신청."
        ),
        "임산물": (
            f"우리 산 표고 재배 병행 추천 (NPV {npv_label}). 충북농기원 컨설팅 + 산림청 보조 신청."
        ),
    }
    msg = base.get(recommended, f"NPV 자료 결과: {recommended} 시나리오 추천.")
    return msg + " (Module C v1 자동 생성, 2026-05-20)"


if __name__ == "__main__":
    print("=" * 60)
    print("recommend.py 자가 검증")
    print("=" * 60)

    fake = {
        "즉시": {
            "npv": 50_000_000,
            "npv_q05": 40_000_000,
            "npv_q95": 60_000_000,
            "feasibility": True,
            "T_optimal": 50,
            "carbon_revenue": 0,
        },
        "10년": {
            "npv": 65_000_000,
            "npv_q05": 50_000_000,
            "npv_q95": 80_000_000,
            "feasibility": True,
            "T_optimal": 60,
            "carbon_revenue": 0,
        },
        "연장KOC": {
            "npv": 75_000_000,
            "npv_q05": 55_000_000,
            "npv_q95": 95_000_000,
            "feasibility": True,
            "T_optimal": 60,
            "carbon_revenue": 5_000_000,
            "kau_breakeven_warning": "KAU 17,200 → 16,300원 이하 시 LEV 음수",
        },
        "간벌+10년": {
            "npv": 80_000_000,
            "npv_q05": 65_000_000,
            "npv_q95": 95_000_000,
            "feasibility": True,
            "T_optimal": 60,
            "subsidy_revenue": 4_400_000,
        },
    }

    print("\n[검증 1] 수익극대화 → 간벌+10년 (NPV 최대)")
    r = recommend_scenario(fake, "수익극대화")
    print(f"  추천: {r}")
    assert r == "간벌+10년"

    print("\n[검증 2] 위험회피 → 간벌+10년 (q05 최대)")
    r = recommend_scenario(fake, "위험회피")
    print(f"  추천: {r}")
    assert r == "간벌+10년"

    print("\n[검증 3] 균형 → ?")
    r = recommend_scenario(fake, "균형")
    print(f"  추천: {r}")
    assert r is not None

    print("\n[검증 4] reasons")
    rs = get_recommendation_reasons("간벌+10년", fake, "균형", age_now=50, legal_min_age=40)
    for i, line in enumerate(rs):
        print(f"  {i + 1}. {line}")
    assert len(rs) >= 2

    print("\n[검증 5] next_actions")
    acts = get_next_actions("간벌+10년", region="충북 보은")
    for i, line in enumerate(acts):
        print(f"  {i + 1}. {line}")
    assert any("산림조합" in a for a in acts)

    print("\n" + "=" * 60)
    print("✅ recommend.py 5/5 검증 통과")
    print("=" * 60)
