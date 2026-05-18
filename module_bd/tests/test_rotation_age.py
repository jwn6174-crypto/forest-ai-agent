"""
test_rotation_age.py — rotation_age() 단위 테스트.

  [검증] 산림자원법 시행규칙 별표 3 (개정 2023.6.27) 의 법정값.
         법이 정답이므로 회귀 테스트가 아니라 검증 테스트.

⚠️ 올바른 ownership 인자: "국유림" | "공사유림" | "기업경영림"
   "사유림" 은 정식 명칭 아님 → None 반환 (별표 3 명칭은 "공·사유림").
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from legal_rotation import rotation_age


# ──────────────────────────────────────────────
# [검증] 별표 3 법정 기준벌기령
# ──────────────────────────────────────────────

def test_sonamu_all_ownerships():
    """소나무: 국유림 60 / 공사유림 40 / 기업경영림 30."""
    assert rotation_age("강원지방소나무", "국유림")["rotation_age"] == 60
    assert rotation_age("강원지방소나무", "공사유림")["rotation_age"] == 40
    assert rotation_age("강원지방소나무", "기업경영림")["rotation_age"] == 30


def test_jatnamu_rotation():
    """잣나무 공사유림 50년."""
    assert rotation_age("잣나무", "공사유림")["rotation_age"] == 50


def test_nakyeopsong_rotation():
    """낙엽송 공사유림 30년."""
    assert rotation_age("낙엽송", "공사유림")["rotation_age"] == 30


def test_default_ownership_is_gongsayu():
    """ownership 생략 시 기본값 = 공사유림."""
    r = rotation_age("강원지방소나무")
    assert r["ownership"] == "공사유림"
    assert r["rotation_age"] == 40


# ──────────────────────────────────────────────
# [검증] 소유형태별 대소관계 — 국유림이 가장 길다
# ──────────────────────────────────────────────

def test_gukyu_longest():
    """같은 수종: 국유림 ≥ 공사유림 ≥ 기업경영림."""
    g = rotation_age("강원지방소나무", "국유림")["rotation_age"]
    s = rotation_age("강원지방소나무", "공사유림")["rotation_age"]
    e = rotation_age("강원지방소나무", "기업경영림")["rotation_age"]
    assert g >= s >= e, f"국유림 {g}, 공사유림 {s}, 기업 {e}"


# ──────────────────────────────────────────────
# [검증] 수종 매핑 — 임분수확표 명칭 → 별표 3 카테고리
# ──────────────────────────────────────────────

def test_species_mapping_to_legal_category():
    """임분수확표 수종 → 별표 3 카테고리 매핑."""
    assert rotation_age("강원지방소나무", "공사유림")["legal_category"] == "소나무"
    assert rotation_age("중부지방소나무", "공사유림")["legal_category"] == "소나무"
    assert rotation_age("상수리나무", "공사유림")["legal_category"] == "참나무류"
    assert rotation_age("굴참나무", "공사유림")["legal_category"] == "참나무류"
    assert rotation_age("신갈나무", "공사유림")["legal_category"] == "참나무류"


def test_provisional_species_have_note():
    """잠정 수종(자작·백합)은 '기타 활엽수' 적용 + note 표시."""
    r = rotation_age("자작나무", "공사유림")
    assert r["legal_category"] == "기타 활엽수"
    assert r["note"] is not None and "잠정" in r["note"]


# ──────────────────────────────────────────────
# [검증] 잘못된 입력 처리
# ──────────────────────────────────────────────

def test_unknown_species_returns_none_with_note():
    """매핑 없는 수종 → rotation_age None + 안내 note."""
    r = rotation_age("참나무류", "공사유림")  # '참나무류' 자체는 매핑 키 아님
    assert r["rotation_age"] is None
    assert r["legal_category"] is None
    assert r["note"] is not None


def test_wrong_ownership_name_returns_none():
    """'사유림'(비정식 명칭) → None. 정식은 '공사유림'.

    이 테스트는 의도된 동작을 고정한다 — 호출 측이
    정식 명칭을 쓰도록 강제하는 가드.
    """
    r = rotation_age("강원지방소나무", "사유림")
    assert r["rotation_age"] is None


def test_returns_dict_with_keys():
    """반환 구조 — dict, 필수 키 존재."""
    r = rotation_age("잣나무", "공사유림")
    for key in ["rotation_age", "legal_category", "ownership",
                "source", "note"]:
        assert key in r