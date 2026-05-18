"""
test_cost_function.py — cost_function() 단위 테스트.

  [검증] DECISIONS D6 기록값 / 회계적으로 당연한 항등식.
  [회귀] 현재 코드의 항목별 출력 기준선.

D6 검증 기준: 강원소나무 1ha 개벌, 280m³, 도로 15km, 중경사,
              묘목 강원지방소나무 → 총 19,774,003원
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cost_function import cost_function


def _base(**kw):
    """D6 기준 시나리오. kw로 일부만 덮어쓸 수 있음."""
    args = dict(volume_m3=280, area_ha=1.0, distance_to_road_km=15,
                action="clearcut", skidding_distance_m=800,
                slope_class="중", species="강원지방소나무")
    args.update(kw)
    return cost_function(**args)


# ──────────────────────────────────────────────
# [검증] DECISIONS D6 기록값
# ──────────────────────────────────────────────

def test_d6_reference_total():
    """D6 기록: 기준 시나리오 총비용 19,774,003원."""
    r = _base()
    assert r["total"] == 19_774_003, f"총비용 {r['total']}"


# ──────────────────────────────────────────────
# [검증] 회계 항등식 — 어떤 코드든 지켜야 함
# ──────────────────────────────────────────────

def test_subtotal_equals_breakdown_sum():
    """subtotal = breakdown 항목들의 합."""
    r = _base()
    assert r["subtotal"] == sum(r["breakdown"].values())


def test_total_equals_subtotal_plus_admin():
    """total = subtotal + 간접비."""
    r = _base()
    assert r["total"] == r["subtotal"] + r["admin_overhead_amount"]


def test_all_costs_positive():
    """모든 비용 항목은 양수."""
    r = _base()
    for name, cost in r["breakdown"].items():
        assert cost > 0, f"{name} = {cost}"
    assert r["total"] > 0


# ──────────────────────────────────────────────
# [검증] action별 구조 — 가이드/D3 설계
# ──────────────────────────────────────────────

def test_thinning_has_no_regen():
    """간벌은 재조림 없음 → regen 항목 부재."""
    r = _base(action="thinning", volume_m3=140)
    assert "regen" not in r["breakdown"]
    assert set(r["breakdown"].keys()) == {"harvest", "skidding",
                                          "transport", "loading"}


def test_clearcut_has_regen():
    """개벌은 재조림 포함 → regen 항목 존재."""
    r = _base()
    assert "regen" in r["breakdown"]


# ──────────────────────────────────────────────
# [검증] 단조성 — 거리·경사 늘면 비용 증가
# ──────────────────────────────────────────────

def test_farther_road_costs_more():
    """도로가 멀수록 운반비 → 총비용 증가 (또는 동일)."""
    near = _base(distance_to_road_km=5)["total"]
    far = _base(distance_to_road_km=300)["total"]
    assert far > near, f"가까움 {near} vs 멀리 {far}"


def test_steeper_slope_costs_more():
    """경사가 급할수록 할증 → 총비용 증가."""
    gentle = _base(slope_class="완")["total"]
    steep = _base(slope_class="급")["total"]
    assert steep > gentle, f"완경사 {gentle} vs 급경사 {steep}"


# ──────────────────────────────────────────────
# [검증] 수종별 묘목 단가 (D6) — 비싼 묘목이 regen 더 비쌈
# ──────────────────────────────────────────────

def test_species_affects_regen():
    """백합나무(1219원/본) regen > 리기다소나무(388원/본) regen."""
    cheap = _base(species="리기다소나무")["breakdown"]["regen"]
    pricey = _base(species="백합나무")["breakdown"]["regen"]
    assert pricey > cheap, f"리기다 {cheap} vs 백합 {pricey}"


def test_invalid_action_raises():
    """잘못된 action은 ValueError."""
    import pytest
    with pytest.raises(ValueError):
        _base(action="burning")


# ──────────────────────────────────────────────
# [회귀] 현재 항목별 출력 기준선 — D6 시나리오
# ──────────────────────────────────────────────

def test_regression_breakdown():
    """기준 시나리오 항목별 비용 — 현재 기준선."""
    r = _base()
    b = r["breakdown"]
    assert b["harvest"] == 2_860_908
    assert b["skidding"] == 2_734_200
    assert b["transport"] == 4_088_000
    assert b["loading"] == 1_624_000
    assert b["regen"] == 5_887_677