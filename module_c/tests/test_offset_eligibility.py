"""test_offset_eligibility.py — D16 8 사업유형 룰베이스."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from offset_eligibility import find_eligible_project_types


def _boeun_30y():
    return {
        "species_dominant": "강원지방소나무",
        "age_estimate": 30, "area_ha": 1.5, "ownership": "사유림",
    }


# [검증] 30년 강원소나무 → FM-Rotation 적격 (≥ 법정 40-10)
def test_fm_rotation_30y_pine_eligible():
    eligible = find_eligible_project_types(_boeun_30y())
    fm = [e for e in eligible if e["code"] == "FM-Rotation"]
    assert fm[0]["eligible"]


# [검증] 0년 임지 + 무립목지 → AR 적격
def test_ar_zero_age_eligible():
    stand = {"species_dominant": "강원지방소나무", "age_estimate": 0,
             "area_ha": 1.5, "ownership": "사유림"}
    eligible = find_eligible_project_types(stand)
    ar = [e for e in eligible if e["code"] == "AR"]
    assert ar[0]["eligible"]


# [검증] 50년 임지 + 참나무 갱신 → SC 적격
def test_sc_with_target_species_oak():
    stand = {"species_dominant": "강원지방소나무", "age_estimate": 50,
             "area_ha": 2.0}
    eligible = find_eligible_project_types(stand, target_species="참나무류")
    sc = [e for e in eligible if e["code"] == "SC"]
    assert sc and sc[0]["eligible"]


# [검증] 산불피해 → FDP 적격
def test_fdp_fire_history_eligible():
    stand = {"species_dominant": "강원지방소나무", "age_estimate": 2, "area_ha": 1.5}
    eligible = find_eligible_project_types(stand, fire_history_within_5yr=True)
    fdp = [e for e in eligible if e["code"] == "FDP"]
    assert fdp and fdp[0]["eligible"]


# [검증] WP — owner_intent 명시 시만 (RAG)
def test_wp_only_with_intent():
    stand = {"species_dominant": "강원지방소나무", "age_estimate": 50, "area_ha": 2.0}
    no_intent = find_eligible_project_types(stand)
    with_intent = find_eligible_project_types(stand, owner_intent="wood_products")
    no_wp = [e for e in no_intent if e["code"] == "WP"]
    yes_wp = [e for e in with_intent if e["code"] == "WP"]
    assert not no_wp  # 없어야
    assert yes_wp  # 있어야


# [검증] 한국 시장 99% — FM-Rotation
def test_fm_rotation_has_korea_market_share_note():
    eligible = find_eligible_project_types(_boeun_30y())
    fm = [e for e in eligible if e["code"] == "FM-Rotation"][0]
    assert "99" in fm["reason"] or "korea_market_share" in fm


# [회귀] 룰베이스 vs RAG 분리
def test_rule_based_vs_rag_separation():
    eligible = find_eligible_project_types(_boeun_30y(), owner_intent="wood_products")
    verif_types = {e["verification"] for e in eligible if e["eligible"]}
    assert "rule_based" in verif_types


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
