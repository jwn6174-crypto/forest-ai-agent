"""
test_growth_predict.py — growth_predict() 단위 테스트.

두 종류로 구분:
  [검증] 가이드/외부 출처가 보증한 값. 코드가 어기면 코드가 틀림.
  [회귀] 현재 코드의 출력을 기준선으로 고정. 의도치 않은 변경 감지용.

가이드 §9.1 (L366): 잣나무 SI=14, 30년 → 본수≈800, DBH≈22, 수고≈14, 재적≈150
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from growth_predict import growth_predict


# ──────────────────────────────────────────────
# [검증] 가이드 §9.1 보증값 — 잣나무 SI=14, 30년
# ──────────────────────────────────────────────

def test_jatnamu_guide_reference():
    """가이드 L366 검증값과 대조. '≈' 값이라 범위로 확인."""
    r = growth_predict("잣나무", 14, 30, [0])
    d = r[0]
    # 가이드: 본수 ≈800 → 700~950 허용
    assert 700 <= d["n_per_ha"] <= 950, f"본수 {d['n_per_ha']}"
    # 가이드: DBH ≈22cm → 18~25 허용
    assert 18 <= d["dbh"] <= 25, f"DBH {d['dbh']}"
    # 가이드: 수고 ≈14m → 10~16 허용
    assert 10 <= d["height"] <= 16, f"수고 {d['height']}"
    # 가이드: 재적 ≈150 → 130~175 허용. 한 자리 빗나가면 column offset
    assert 130 <= d["volume"] <= 175, f"재적 {d['volume']}"


def test_column_offset_guard():
    """재적이 한 자리 빗나가지 않았는지 (15도 1500도 아님)."""
    r = growth_predict("잣나무", 14, 30, [0])
    v = r[0]["volume"]
    assert 50 < v < 500, f"재적 {v} — column offset 의심"


# ──────────────────────────────────────────────
# [검증] 물리적으로 당연한 성질 (어떤 코드든 지켜야 함)
# ──────────────────────────────────────────────

def test_volume_monotonic_increasing():
    """나무는 자란다 — 시간이 갈수록 부피 증가."""
    r = growth_predict("강원지방소나무", 14, 30, [0, 10, 20])
    vols = [x["volume"] for x in r]
    assert vols == sorted(vols), f"부피가 단조증가 안 함: {vols}"


def test_dbh_monotonic_increasing():
    """DBH(흉고직경)도 시간이 갈수록 증가."""
    r = growth_predict("강원지방소나무", 14, 30, [0, 10, 20])
    dbhs = [x["dbh"] for x in r]
    assert dbhs == sorted(dbhs), f"DBH가 단조증가 안 함: {dbhs}"


def test_age_advances_with_forecast():
    """forecast_years 만큼 나이가 더해진다."""
    r = growth_predict("강원지방소나무", 14, 30, [0, 20])
    assert r[0]["age"] == 30
    assert r[1]["age"] == 50


def test_returns_list_with_all_keys():
    """반환 구조 — list of dict, 필수 키 존재."""
    r = growth_predict("강원지방소나무", 14, 30, [0])
    assert isinstance(r, list) and len(r) == 1
    for key in ["dt", "age", "volume", "dbh", "height",
                "n_per_ha", "carbon_uptake_rate", "method"]:
        assert key in r[0], f"키 누락: {key}"


# ──────────────────────────────────────────────
# [회귀] 현재 출력 기준선 고정 — 강원소나무 SI=14, 30→50년
#   주의: 가이드 보증값이 아니라 '현재 코드의 값'.
#   코드 수정으로 이 값이 바뀌면 의도된 변경인지 검토할 것.
# ──────────────────────────────────────────────

def test_regression_kangwon_pine():
    """강원소나무 SI=14 시계열 — 현재 기준선."""
    r = growth_predict("강원지방소나무", 14, 30, [0, 20])
    d0, d20 = r[0], r[1]
    assert abs(d0["volume"] - 173.0) < 1.0, f"30년 재적 {d0['volume']}"
    assert abs(d0["dbh"] - 16.9) < 0.5, f"30년 DBH {d0['dbh']}"
    assert abs(d20["volume"] - 281.8) < 1.0, f"50년 재적 {d20['volume']}"
    assert abs(d20["dbh"] - 26.7) < 0.5, f"50년 DBH {d20['dbh']}"


def test_regression_carbon_uptake():
    """탄소흡수율 — D5 결정에서 확인된 값 (30년 피크 후 감소)."""
    r = growth_predict("강원지방소나무", 14, 30, [0, 20])
    assert abs(r[0]["carbon_uptake_rate"] - 10.77) < 0.1, "30년 탄소"
    assert abs(r[1]["carbon_uptake_rate"] - 4.92) < 0.1, "50년 탄소"
    # 30년이 50년보다 흡수율 높음 (피크 후 감소)
    assert r[0]["carbon_uptake_rate"] > r[1]["carbon_uptake_rate"]