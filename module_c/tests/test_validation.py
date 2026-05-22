"""test_validation.py — D22 모델 vs carbonregistry 인증 비교."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from module_c.src.validation import (
    compute_model_30yr_uptake_tco2_per_ha,
    compare_with_certified,
    validate_all_real_cases,
    summary_validation_report,
)
from module_c.src.demo_parcels import REAL_REGISTERED_PARCELS


# [검증] real polygon 4개 모두 정의됨
def test_four_real_parcels_defined():
    assert len(REAL_REGISTERED_PARCELS) == 4


# [검증] 보은 산외면 오대리 — 학술 발견 reference
def test_boeun_oedari_validation():
    r = compare_with_certified("boeun_real_oedari_8197tco2", verbose=False)
    # 인증 320.2 tCO₂/ha/30yr
    assert 315 < r["certified_tco2_per_ha_per_30yr"] < 325


# [검증] D22 학술 발견 — +103% 차이
def test_model_vs_certified_103pct_difference():
    r = compare_with_certified("boeun_real_oedari_8197tco2", verbose=False)
    # 모델 ~157 vs 인증 ~320 = +103%
    assert 90 < r["difference_pct"] < 120


# [검증] interpretation 에 학술 해석 포함
def test_interpretation_has_baseline_note():
    r = compare_with_certified("boeun_real_oedari_8197tco2", verbose=False)
    assert "baseline" in r["interpretation"] or "보수" in r["interpretation"]


# [검증] 4 case 모두 +100% 근처 (인증사업의 동일 가정)
def test_all_four_cases_similar_difference():
    results = validate_all_real_cases(verbose=False)
    diffs = [r["difference_pct"] for r in results]
    # 모두 100-110% 사이 (단일 가정 사용)
    assert all(90 < d < 120 for d in diffs)


# [검증] summary 보고서
def test_summary_report_has_academic_claim():
    results = validate_all_real_cases(verbose=False)
    summary = summary_validation_report(results)
    assert "academic_claim" in summary
    assert summary["n_cases"] == 4


# [검증] 모델 30년 평균 uptake
def test_model_30yr_uptake_positive():
    stand = {"species_dominant": "강원지방소나무", "age_estimate": 40}
    r = compute_model_30yr_uptake_tco2_per_ha(stand)
    assert r["model_30yr_total_tco2_per_ha"] > 100


if __name__ == "__main__":
    funcs = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    passed = 0
    for f in funcs:
        try:
            f()
            print(f"  ✅ {f.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {f.__name__}: {e}")
    print(f"\n{passed}/{len(funcs)} passed")
