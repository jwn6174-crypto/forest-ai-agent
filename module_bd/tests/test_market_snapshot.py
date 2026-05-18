"""
test_market_snapshot.py — market_snapshot() 단위 테스트.

market_snapshot 은 일부가 실시간 API(KAU 종가)라 다른 함수와 다름.
  [검증] 안정적인 것만 — 반환 구조, KOFPI 7수종, 등급 순서, 상수.
  KAU 종가(kau_close)는 날마다 변하므로 '값'은 테스트하지 않음
  — 존재·타입·양수만 확인.

가이드 §9.1: test_kofpi_grade_order() — 등급별 가격 단조성 검증.

⚠️ 수종 명칭 주의: timber_price_by_species 는 KOFPI 기준 명칭
   ("소나무" 등) 사용. 임분수확표의 "강원지방소나무" 와 다름.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from market_snapshot import market_snapshot

# KOFPI 7수종 (timber_price_by_species 키)
KOFPI_SPECIES = {"낙엽송", "리기다소나무", "삼나무", "소나무",
                 "잣나무", "참나무류", "편백"}

# 원목 등급 — 가격 높은 순
GRADE_ORDER = ["1등급", "2등급", "3등급"]


# ──────────────────────────────────────────────
# [검증] 반환 구조
# ──────────────────────────────────────────────

def test_returns_dict_with_keys():
    """반환 — dict, 가이드 §8.1 필수 키 존재."""
    r = market_snapshot("2026-05-15")
    for key in ["date", "timber_price", "kau_close", "koc_estimate",
                "vcm_floor_wta", "discount_rate"]:
        assert key in r, f"키 누락: {key}"


def test_has_seven_kofpi_species():
    """timber_price_by_species — KOFPI 7수종 모두 존재."""
    r = market_snapshot("2026-05-15")
    bs = r["timber_price_by_species"]
    assert set(bs.keys()) == KOFPI_SPECIES, f"수종 불일치: {set(bs.keys())}"


# ──────────────────────────────────────────────
# [검증] 가이드 §9.1 — 등급별 가격 단조성
# ──────────────────────────────────────────────

def test_kofpi_grade_order():
    """1등급 > 2등급 > 3등급 — 가이드 §9.1 검증.

    등급이 낮을수록 가격이 싸야 함. 어기면 등급 컬럼 매핑 오류.
    """
    r = market_snapshot("2026-05-15")
    tp = r["timber_price"]
    prices = [tp[g] for g in GRADE_ORDER]
    assert prices == sorted(prices, reverse=True), \
        f"등급 순서 깨짐: {dict(zip(GRADE_ORDER, prices))}"


def test_grade_order_all_species():
    """7수종 각각 등급 순서 1>2>3 — 값이 있는 등급만 비교.

    특용재·원주재 등 거래가 드문 등급은 KOFPI 보고서에
    가격이 없어 None — 이는 정상(데이터 한계). None 은 제외하고,
    실제 가격이 있는 등급끼리 순서만 검증.
    """
    r = market_snapshot("2026-05-15")
    bs = r["timber_price_by_species"]
    for sp, grades in bs.items():
        # None 이 아닌 등급만 추림
        prices = [grades[g] for g in GRADE_ORDER
                  if g in grades and grades[g] is not None]
        assert prices == sorted(prices, reverse=True), \
            f"{sp} 등급 순서 깨짐: {prices}"
        # 1·2등급은 전 수종 필수 — 빠지면 데이터 문제
        assert grades.get("1등급") is not None, f"{sp} 1등급 없음"
        assert grades.get("2등급") is not None, f"{sp} 2등급 없음"


def test_prices_positive():
    """원목 가격은 양수 (None 인 등급은 거래 없음 — 제외)."""
    r = market_snapshot("2026-05-15")
    checked = 0
    for grade, price in r["timber_price"].items():
        if price is None:
            continue
        assert price > 0, f"{grade} = {price}"
        checked += 1
    assert checked > 0, "검증할 가격이 하나도 없음"


# ──────────────────────────────────────────────
# [검증] 상수 — 가이드 §8.1 / 박2020
# ──────────────────────────────────────────────

def test_vcm_floor_constant():
    """vcm_floor_wta = 17039 (박2020 WTA, 상수)."""
    r = market_snapshot("2026-05-15")
    assert r["vcm_floor_wta"] == 17039


def test_discount_rate_constant():
    """discount_rate = 0.05 (Faustmann 기본 할인율)."""
    r = market_snapshot("2026-05-15")
    assert r["discount_rate"] == 0.05


# ──────────────────────────────────────────────
# [검증] KAU — 값이 아니라 존재·타입만 (실시간 API)
# ──────────────────────────────────────────────

def test_kau_close_type():
    """kau_close — API 라 값은 변동. 존재 시 양수 숫자인지만 확인.

    API 가 막히면 None 일 수 있음 — 그 경우도 허용 (구조는 정상).
    """
    r = market_snapshot("2026-05-15")
    kau = r["kau_close"]
    assert kau is None or (isinstance(kau, (int, float)) and kau > 0)