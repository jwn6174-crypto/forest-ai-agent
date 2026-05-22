"""test_subsidies.py — D18 산림보조사업 단가."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from subsidies import lookup_subsidy, lookup_thinning_revenue, lookup_reforestation_subsidy


# [검증] 산림청 2025 reference
def test_thinning_1st_2_5M():
    r = lookup_subsidy("thinning_1st", area_ha=1.0, region="기타")
    assert r["amount_per_ha"] == 2_500_000


def test_reforestation_4_5M():
    r = lookup_subsidy("reforestation_seedling", area_ha=1.0, region="기타")
    assert r["amount_per_ha"] == 4_500_000


# [검증] 충북 +10% 보너스
def test_chungbuk_bonus_10pct():
    r = lookup_subsidy("thinning_1st", area_ha=1.0, region="충북")
    # 250만 × 1.10 = 275만
    assert r["total_amount"] == 2_750_000


# [검증] 면적 비례
def test_area_scaling():
    r = lookup_subsidy("thinning_1st", area_ha=2.0, region="기타")
    assert r["total_amount"] == 5_000_000


# [검증] 간벌 매출 — 임령 범위
def test_thinning_age_25_applicable():
    r = lookup_thinning_revenue(area_ha=1.0, age_now=25, region="충북")
    assert r["applicable"]


def test_thinning_age_10_not_applicable():
    r = lookup_thinning_revenue(area_ha=1.0, age_now=10, region="충북")
    assert not r["applicable"]


def test_thinning_age_60_not_applicable():
    r = lookup_thinning_revenue(area_ha=1.0, age_now=60, region="충북")
    assert not r["applicable"]


# [회귀] 재조림 보조 — 충북 보은 모달
def test_reforestation_boeun_2ha():
    r = lookup_reforestation_subsidy(area_ha=2.0, region="충북")
    # 450만 × 2 × 1.10 = 990만
    assert r["total_amount"] == 9_900_000


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
