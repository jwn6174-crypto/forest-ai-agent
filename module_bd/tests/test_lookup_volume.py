"""
test_lookup_volume.py — lookup_volume() 단위 테스트.

입목수간재적표(Ⅱ장, 산림청 2014) 기반 단목(단일 입목) 재적 lookup.

  [검증] 물리적으로 당연한 성질 (단조성, 양수, 자릿수).
  [회귀] 현재 코드의 lookup 출력 기준선.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from growth_predict import lookup_volume


# ──────────────────────────────────────────────
# [검증] 물리적 성질
# ──────────────────────────────────────────────

def test_volume_positive():
    """단목 재적은 양수."""
    r = lookup_volume(species="강원지방소나무", bark="수피포함",
                      dbh=20, height=15)
    assert r["volume"] > 0


def test_volume_increases_with_dbh():
    """DBH가 클수록 재적 증가 (수고 고정)."""
    small = lookup_volume(species="강원지방소나무", bark="수피포함",
                          dbh=20, height=15)["volume"]
    large = lookup_volume(species="강원지방소나무", bark="수피포함",
                          dbh=30, height=15)["volume"]
    assert large > small, f"dbh20 {small} vs dbh30 {large}"


def test_volume_increases_with_height():
    """수고가 클수록 재적 증가 (DBH 고정)."""
    short = lookup_volume(species="강원지방소나무", bark="수피포함",
                          dbh=30, height=14)["volume"]
    tall = lookup_volume(species="강원지방소나무", bark="수피포함",
                         dbh=30, height=22)["volume"]
    assert tall > short, f"h14 {short} vs h22 {tall}"


def test_volume_reasonable_magnitude():
    """단목 재적은 상식 범위 — 보통 0.01~5 m³."""
    r = lookup_volume(species="강원지방소나무", bark="수피포함",
                      dbh=20, height=15)
    assert 0.01 < r["volume"] < 5.0, f"재적 {r['volume']}"


# ──────────────────────────────────────────────
# [검증] 반환 구조
# ──────────────────────────────────────────────

def test_returns_dict_with_keys():
    """반환 — dict, 필수 키 존재."""
    r = lookup_volume(species="강원지방소나무", bark="수피포함",
                      dbh=20, height=15)
    for key in ["volume", "lookup_dbh", "lookup_height",
                "quality", "warning"]:
        assert key in r


def test_lookup_snaps_to_table_grid():
    """요청 수고가 재적표 격자에 맞춰 스냅됨 (15 → 14)."""
    r = lookup_volume(species="강원지방소나무", bark="수피포함",
                      dbh=20, height=15)
    # 격자에 스냅되므로 요청값과 다를 수 있음
    assert r["lookup_height"] <= 15
    assert r["lookup_dbh"] == 20


# ──────────────────────────────────────────────
# [회귀] 현재 lookup 출력 기준선
# ──────────────────────────────────────────────

def test_regression_kangwon_pine():
    """강원소나무 dbh20/h15 — 현재 기준선."""
    r = lookup_volume(species="강원지방소나무", bark="수피포함",
                      dbh=20, height=15)
    assert abs(r["volume"] - 0.1489) < 0.001
    assert r["lookup_dbh"] == 20
    assert r["lookup_height"] == 14
    assert r["quality"] == "OK"


def test_regression_jatnamu():
    """잣나무 dbh20/h14 — 현재 기준선."""
    r = lookup_volume(species="잣나무", bark="수피포함",
                      dbh=20, height=14)
    assert abs(r["volume"] - 0.1672) < 0.001