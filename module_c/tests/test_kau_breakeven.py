"""test_kau_breakeven.py — D23 KAU 임계가 (경제학자 핵심)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kau_breakeven import compute_kau_breakeven, format_kau_breakeven_message


# [검증] WTA hurdle 17,039원 reference
def test_wta_hurdle_constant():
    r = compute_kau_breakeven(50_000_000, 17_200, 5_000_000)
    assert r["margin_to_wta"] == 161  # 17,200 - 17,039


def test_wta_hurdle_with_hypothetical_kau_19600():
    """margin 계산 검증 — KAU 가 WTA 를 돌파한 가상값(19,600) 입력 시 margin 부호.
    (19,600 은 실측이 아니라 돌파 후를 가정한 민감도용 값. 최신 실측은 15,550)"""
    r = compute_kau_breakeven(50_000_000, 19_600, 5_000_000)
    assert r["margin_to_wta"] == 2_561  # 19,600 - 17,039


# [검증] carbon_revenue=0 → KAU 무영향
def test_no_carbon_revenue():
    r = compute_kau_breakeven(50_000_000, 17_200, 0)
    assert r["kau_breakeven"] is None


# [검증] 작은 margin → warning
def test_thin_margin_warning():
    r = compute_kau_breakeven(1_000_000, 17_200, 5_000_000)
    # NPV 가 carbon_revenue 와 유사하면 breakeven 이 kau_used 근처
    assert r["kau_breakeven"] is not None


# [회귀] 큰 NPV → 음수 breakeven (LEV 항상 +)
def test_large_npv_negative_breakeven():
    """NPV 50M, carbon 5M — non-carbon 부분이 45M 이라 KAU 0이어도 LEV +"""
    r = compute_kau_breakeven(50_000_000, 17_200, 5_000_000)
    assert r["kau_breakeven"] is not None
    assert r["kau_breakeven"] < 0  # non-carbon 이 크면 breakeven 이 음수


# [검증] format 메시지
def test_format_message_no_carbon():
    r = compute_kau_breakeven(50_000_000, 17_200, 0)
    msg = format_kau_breakeven_message(r)
    assert "carbon" in msg.lower() or "탄소" in msg or "KAU 변동 무영향" in msg


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
