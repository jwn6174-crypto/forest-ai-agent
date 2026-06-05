"""Module C — Faustmann-Hartman LEV (희도 담당).

다목적 산림경영 AI Agent (충북 보은 파일럿) 의 의사결정 코어.
정우 module_bd 의 7 함수 + 자체 모듈 12 = 19 src 파일.

8 전문가 deliberation 기반 학술 발견 2개:
- D22: carbonregistry 인증(320) vs Module C 모델(220) +45% 차이
- D23: KAU 16개월 +79.4%(8,670→15,550), WTA 17,039원에 8.7% 미달 — 돌파 임박

Public API:
    >>> from module_c.src import compute_lev, compute_lev_with_plan, get_demo_parcel
    >>> stand = get_demo_parcel("boeun_real_oedari_8197tco2")
    >>> package = compute_lev_with_plan(stand, user_preference="균형")
    >>> package["draft_plan"]["natural_summary"]
    '우리 산 → ...'
"""

# ============================================================
# 진입점 (사용자가 가장 자주 사용)
# ============================================================
from .climate_multiplier import (
    apply_multiplier_to_trajectory,
    get_climate_multiplier,
)
from .compute_lev import compute_lev, compute_lev_with_plan

# ============================================================
# 외부 API (사용자 본인 명의 키)
# ============================================================
from .data_go_kr_api import (
    fetch_forest_statistics,
    fetch_kau_latest_close,
    fetch_kau_price,
    fetch_oil_price,
    vworld_address_to_coord,
    vworld_pnu_to_geometry,
)
from .demo_parcels import (
    DEMO_PARCELS,
    REAL_REGISTERED_PARCELS,
    SAMPLE_PARCELS,
    get_demo_parcel,
    list_demo_parcels,
    list_real_parcels,
    list_sample_parcels,
)
from .draft_plan import create_draft_plan
from .grade_distribution import (
    GRADE_BOUNDS_CM,
    GradeDistributionStrategy,
    HeuristicGD,
    WeibullGD,
    estimate_grade_distribution,
)
from .hwp_decay import (
    compute_hwp_decay,
    compute_hwp_npv_contribution,
    compute_hwp_remaining_fraction,
)

# ============================================================
# 시장·경제 변수
# ============================================================
from .kau_breakeven import (
    compute_kau_breakeven,
    format_kau_breakeven_message,
)
from .lev_core import compute_lev_single
from .lhs_sampling import (
    generate_lhs_samples_6d,
    lhs_samples,
    transform_uniform_to_distribution,
)

# ============================================================
# Monte Carlo + 분산 source
# ============================================================
from .monte_carlo import run_monte_carlo
from .ntfp_income import compute_ntfp_npv, lookup_ntfp
from .offset_eligibility import (
    find_eligible_project_types,
    search_rag_citations,
)
from .pareto import (
    compute_pareto_front,
    format_pareto_for_plotly,
    select_three_representative,
)

# ============================================================
# 의사결정 + 추천 + UI
# ============================================================
from .recommend import (
    generate_kakao_message,
    get_next_actions,
    get_recommendation_reasons,
    recommend_scenario,
)

# ============================================================
# 시나리오·등급분포·LEV 본체
# ============================================================
from .scenarios import (
    VALID_SCENARIOS,
    rotation_age,
    scenario_feasibility,
    scenario_T,
)
from .stand_adapter import from_forest_state, from_module_a
from .subsidies import (
    lookup_reforestation_subsidy,
    lookup_subsidy,
    lookup_thinning_revenue,
)
from .ui_adapter import (
    to_ui_offset_eligibility,
    to_ui_recommendation,
    to_ui_scenarios,
)
from .uncertainty import (
    classify_uncertainty,
    generate_uncertainty_note,
    get_uncertainty_summary,
)

# ============================================================
# 검증 (D22)
# ============================================================
from .validation import (
    compare_with_certified,
    compute_model_30yr_uptake_tco2_per_ha,
    summary_validation_report,
    validate_all_real_cases,
)

# ============================================================
# Public API export (`from module_c.src import *`)
# ============================================================
__all__ = [
    "DEMO_PARCELS",
    "VALID_SCENARIOS",
    "GradeDistributionStrategy",
    "HeuristicGD",
    "WeibullGD",
    "apply_multiplier_to_trajectory",
    "classify_uncertainty",
    # 검증
    "compare_with_certified",
    "compute_hwp_decay",
    "compute_hwp_npv_contribution",
    # 시장·경제
    "compute_kau_breakeven",
    # 진입점
    "compute_lev",
    "compute_lev_single",
    "compute_lev_with_plan",
    "compute_ntfp_npv",
    "compute_pareto_front",
    "create_draft_plan",
    "estimate_grade_distribution",
    # API
    "fetch_forest_statistics",
    "fetch_kau_latest_close",
    "fetch_kau_price",
    "find_eligible_project_types",
    "format_kau_breakeven_message",
    # 통합 어댑터 (D127) — Module A·ui 연결
    "from_forest_state",
    "from_module_a",
    "generate_kakao_message",
    "get_climate_multiplier",
    "get_demo_parcel",
    "get_next_actions",
    "get_recommendation_reasons",
    "get_uncertainty_summary",
    "lhs_samples",
    "list_demo_parcels",
    "list_real_parcels",
    "list_sample_parcels",
    "lookup_ntfp",
    "lookup_reforestation_subsidy",
    "lookup_subsidy",
    "lookup_thinning_revenue",
    # 추천·UI
    "recommend_scenario",
    "rotation_age",
    # Monte Carlo
    "run_monte_carlo",
    # 시나리오·LEV
    "scenario_T",
    "scenario_feasibility",
    "search_rag_citations",
    "select_three_representative",
    "summary_validation_report",
    "to_ui_offset_eligibility",
    "to_ui_recommendation",
    "to_ui_scenarios",
    "validate_all_real_cases",
    "vworld_address_to_coord",
    "vworld_pnu_to_geometry",
]


__version__ = "1.1.0-integrated"
__author__ = "Heedo Choi <zxsa0716@kookmin.ac.kr>"
__decisions__ = "D101-D132 (ADR 32개 — D128-D132 감사·UI 성능)"
__tests__ = 160  # 19 test 파일 (통합 e2e + stand/ui adapter 포함), +shared 15 = 175
