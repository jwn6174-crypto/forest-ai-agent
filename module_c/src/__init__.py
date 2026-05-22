"""Module C — Faustmann-Hartman LEV (희도 담당).

다목적 산림경영 AI Agent (충북 보은 파일럿) 의 의사결정 코어.
정우 module_bd 의 7 함수 + 자체 모듈 12 = 19 src 파일.

8 전문가 deliberation 기반 학술 발견 2개:
- D22: carbonregistry 인증 vs Module C 모델 +103% 차이
- D23: KAU 16개월 +126%, WTA 17,039원 역사적 첫 돌파 (2026-03~05)

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
from .compute_lev import compute_lev, compute_lev_with_plan
from .demo_parcels import (
    DEMO_PARCELS, get_demo_parcel,
    list_demo_parcels, list_sample_parcels, list_real_parcels,
    SAMPLE_PARCELS, REAL_REGISTERED_PARCELS,
)

# ============================================================
# 시나리오·등급분포·LEV 본체
# ============================================================
from .scenarios import (
    scenario_T, scenario_feasibility, VALID_SCENARIOS, rotation_age,
)
from .grade_distribution import (
    estimate_grade_distribution,
    GradeDistributionStrategy, HeuristicGD, WeibullGD,
    GRADE_BOUNDS_CM,
)
from .lev_core import compute_lev_single

# ============================================================
# Monte Carlo + 분산 source
# ============================================================
from .monte_carlo import run_monte_carlo
from .lhs_sampling import (
    lhs_samples, transform_uniform_to_distribution, generate_lhs_samples_6d,
)
from .climate_multiplier import (
    get_climate_multiplier, apply_multiplier_to_trajectory,
)
from .hwp_decay import (
    compute_hwp_remaining_fraction, compute_hwp_decay,
    compute_hwp_npv_contribution,
)

# ============================================================
# 시장·경제 변수
# ============================================================
from .kau_breakeven import (
    compute_kau_breakeven, format_kau_breakeven_message,
)
from .subsidies import (
    lookup_subsidy, lookup_thinning_revenue, lookup_reforestation_subsidy,
)
from .ntfp_income import lookup_ntfp, compute_ntfp_npv

# ============================================================
# 의사결정 + 추천 + UI
# ============================================================
from .recommend import (
    recommend_scenario, get_recommendation_reasons, get_next_actions,
    generate_kakao_message,
)
from .pareto import (
    compute_pareto_front, format_pareto_for_plotly, select_three_representative,
)
from .uncertainty import (
    classify_uncertainty, generate_uncertainty_note, get_uncertainty_summary,
)
from .offset_eligibility import (
    find_eligible_project_types, search_rag_citations,
)
from .draft_plan import create_draft_plan

# ============================================================
# 검증 (D22)
# ============================================================
from .validation import (
    compute_model_30yr_uptake_tco2_per_ha,
    compare_with_certified, validate_all_real_cases,
    summary_validation_report,
)

# ============================================================
# 외부 API (사용자 본인 명의 키)
# ============================================================
from .data_go_kr_api import (
    fetch_forest_statistics,
    fetch_kau_price, fetch_kau_latest_close, fetch_oil_price,
    vworld_pnu_to_geometry, vworld_address_to_coord,
)

# ============================================================
# Public API export (`from module_c.src import *`)
# ============================================================
__all__ = [
    # 진입점
    "compute_lev", "compute_lev_with_plan",
    "DEMO_PARCELS", "get_demo_parcel",
    "list_demo_parcels", "list_sample_parcels", "list_real_parcels",
    # 시나리오·LEV
    "scenario_T", "scenario_feasibility", "VALID_SCENARIOS", "rotation_age",
    "estimate_grade_distribution", "GradeDistributionStrategy",
    "HeuristicGD", "WeibullGD",
    "compute_lev_single",
    # Monte Carlo
    "run_monte_carlo", "lhs_samples",
    "get_climate_multiplier", "apply_multiplier_to_trajectory",
    "compute_hwp_decay", "compute_hwp_npv_contribution",
    # 시장·경제
    "compute_kau_breakeven", "format_kau_breakeven_message",
    "lookup_subsidy", "lookup_thinning_revenue", "lookup_reforestation_subsidy",
    "lookup_ntfp", "compute_ntfp_npv",
    # 추천·UI
    "recommend_scenario", "get_recommendation_reasons",
    "get_next_actions", "generate_kakao_message",
    "compute_pareto_front", "select_three_representative",
    "classify_uncertainty", "get_uncertainty_summary",
    "find_eligible_project_types", "search_rag_citations",
    "create_draft_plan",
    # 검증
    "compare_with_certified", "validate_all_real_cases",
    "summary_validation_report",
    # API
    "fetch_forest_statistics", "fetch_kau_price", "fetch_kau_latest_close",
    "vworld_pnu_to_geometry", "vworld_address_to_coord",
]


__version__ = "1.0.0-day6"
__author__ = "Heedo Choi <zxsa0716@kookmin.ac.kr>"
__decisions__ = "D9-D24 (ADR 13개)"
__tests__ = 129  # pytest 1.81s
