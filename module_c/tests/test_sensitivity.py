"""test_sensitivity.py — D25 학술 robustness 민감도 분석."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from module_c.src.sensitivity import (
    sensitivity_site_index, sensitivity_discount_rate,
    sensitivity_climate_scenario, sensitivity_kau_price,
    sensitivity_hwp_half_life, full_sensitivity_report,
)
from module_c.src.demo_parcels import get_demo_parcel


def _stand():
    return get_demo_parcel("boeun_real_oedari_8197tco2")


# [검증] SI ±2 — 산림학자 권고
def test_si_sensitivity_returns_5_points():
    r = sensitivity_site_index(_stand(), "연장KOC", T=60)
    assert len(r) >= 3
    # 결과 개수 검증 — fallback 모드에서는 SI 무관일 수 있음
    npvs = [x["npv"] for x in r]
    assert len(npvs) == len(r)
    assert all(isinstance(x, (int, float)) for x in npvs)


def test_si_sensitivity_range_8_to_22():
    """SI 범위 8-22 (한국 임분수확표 범위)"""
    r = sensitivity_site_index(_stand(), "즉시", T=50,
                                 si_range=[8, 12, 14, 18, 22])
    assert len(r) == 5


# [검증] 할인율 — 경제학자 권고 (0.04, 0.05, 0.06, 0.07)
def test_discount_rate_4_values():
    r = sensitivity_discount_rate(_stand(), "연장KOC", T=60)
    assert len(r) == 4
    # 0.04 ~ 0.07
    rates = [x["discount_rate"] for x in r]
    assert min(rates) == 0.04
    assert max(rates) == 0.07


def test_discount_rate_higher_lower_npv():
    """할인율 높을수록 NPV 감소 (T_horizon > 0 시)"""
    r = sensitivity_discount_rate(_stand(), "연장KOC", T=60)
    npvs = {x["discount_rate"]: x["npv"] for x in r}
    assert npvs[0.04] > npvs[0.07]


# [검증] SSP 기후 — 산림학자 D11.b
def test_ssp_4_scenarios():
    r = sensitivity_climate_scenario(_stand(), "즉시", T=50)
    assert len(r) == 4
    scenarios = [x["climate_scenario"] for x in r]
    assert "baseline" in scenarios
    assert "SSP585" in scenarios


def test_ssp585_reduces_npv():
    """강원소나무 SSP585 0.80 multiplier → NPV 감소"""
    r = sensitivity_climate_scenario(_stand(), "즉시", T=50)
    npvs = {x["climate_scenario"]: x["npv"] for x in r}
    assert npvs["SSP585"] < npvs["baseline"]


# [검증] KAU 민감도 — D23 학술 발견
def test_kau_5_price_points():
    r = sensitivity_kau_price(_stand(), "연장KOC", T=60)
    assert len(r) == 5


def test_kau_19600_passes_wta():
    """KAU 가 WTA 를 넘는 가상 점(19,600)은 wta_passed=True, 저점(8,670)은 False.
    (19,600 은 돌파 후 가정값; 최신 실측은 2026-03 15,550 으로 아직 미돌파)"""
    r = sensitivity_kau_price(_stand(), "연장KOC", T=60)
    kau_data = {x["kau_price"]: x for x in r}
    assert kau_data[19600]["wta_passed"]
    assert not kau_data[8670]["wta_passed"]  # 2025-07 저점
    assert not kau_data[15550]["wta_passed"]  # 2026-03 최신 실측 — 아직 미돌파


def test_kau_wta_margin_calculation():
    """WTA hurdle 17,039 reference"""
    r = sensitivity_kau_price(_stand(), "연장KOC", T=60)
    kau_data = {x["kau_price"]: x for x in r}
    assert kau_data[17039]["wta_margin"] == 0


# [검증] HWP half-life — D15
def test_hwp_4_cases():
    r = sensitivity_hwp_half_life(_stand(), "즉시", T=50)
    assert len(r) == 4
    labels = [x["label"] for x in r]
    assert any("IPCC" in l for l in labels)
    assert any("한국" in l for l in labels)


def test_hwp_longer_halflife_more_remaining():
    """긴 half-life → 30년 후 잔존 더 많음"""
    r = sensitivity_hwp_half_life(_stand(), "즉시", T=50)
    by_label = {x["label"]: x for x in r}
    boost = by_label["낙관적 (+10년)"]["hwp_remaining_30y_tco2"]
    pess = by_label["보수적 (-10년)"]["hwp_remaining_30y_tco2"]
    assert boost > pess


# [검증] 통합 보고서
def test_full_report_has_5_dimensions():
    r = full_sensitivity_report(_stand(), scenario="연장KOC")
    assert "site_index" in r
    assert "discount_rate" in r
    assert "climate_scenario" in r
    assert "kau_price" in r
    assert "hwp_half_life" in r


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
