"""
subsidies.py — 산림보조사업 단가 lookup.

D18 (경영자 deliberation): 영세 사유림 7할이 간벌 보조사업 ha당 200-300만원 국고지원.
정우 cost_function 의 action="thinning" 은 *비용만* 계산 — 보조사업 매출은 별도.

데이터:
- 출처: 산림청 「2025 산림보조사업 지침」 + 충북도 자체 보조
- 솎아베기 2,500,000원/ha, 어린나무가꾸기 1,800,000원/ha, 풀베기 900,000원/ha 등

희도 D18 결정 — 2026-05-20 Day 6 작성
"""

import json
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[1]
SUBSIDY_PATH = ROOT / "data" / "raw" / "subsidies" / "forestry_subsidies_2025.json"


def _load_subsidies() -> dict:
    with open(SUBSIDY_PATH, encoding="utf-8") as f:
        return json.load(f)


SubsidyAction = Literal[
    "thinning_1st",
    "thinning_2nd",
    "young_tree_care",
    "weeding",
    "reforestation_seedling",
    "pruning",
]


def lookup_subsidy(
    action: SubsidyAction,
    area_ha: float = 1.0,
    region: str = "충북",
) -> dict:
    """
    보조사업 단가 lookup + 지역 보너스 적용.

    Parameters
    ----------
    action : str
        보조사업 종류 (thinning_1st, weeding, 등)
    area_ha : float
        면적 (ha)
    region : str
        "충북" | "전북" | "강원" | "기타"

    Returns
    -------
    dict
        {
            "amount_per_ha": int,           # 기본 단가
            "regional_bonus_rate": float,   # 지역 추가 보조율
            "total_amount": int,            # 면적 × (기본 + 보너스)
            "korean": str,
            "applicable_action": str,
            "source": str,
        }

    Examples
    --------
    >>> r = lookup_subsidy("thinning_1st", area_ha=2.0, region="충북")
    >>> r["total_amount"]
    5500000  # 2500000 × 2 × 1.10
    """
    data = _load_subsidies()
    subsidies = data["subsidies_won_per_ha"]
    regional = data["regional_bonus"]

    if action not in subsidies:
        raise ValueError(f"Unknown subsidy action: {action}. Valid: {list(subsidies.keys())}")

    base_amount = subsidies[action]["amount"]
    bonus_rate = regional.get(region, regional["기타"])["rate"]
    total = base_amount * area_ha * (1 + bonus_rate)

    return {
        "amount_per_ha": base_amount,
        "regional_bonus_rate": bonus_rate,
        "total_amount": round(total),
        "korean": subsidies[action]["korean"],
        "applicable_action": subsidies[action].get("applicable_action"),
        "source": subsidies[action].get("source", "산림청 2025 지침"),
        "_raw": subsidies[action],
    }


def lookup_thinning_revenue(
    area_ha: float,
    age_now: int,
    region: str = "충북",
) -> dict:
    """
    간벌 시나리오 (D18) 의 보조사업 매출 lookup.

    임령 별 1차 vs 2차 솎아베기 자동 선택:
    - 20-40년생: thinning_1st (2.5M/ha)
    - 30-50년생: thinning_2nd (2.0M/ha)
    - 둘 다 적용 가능 시 1차 우선

    Returns
    -------
    dict
        {amount: int, type: str, applicable: bool, ...}
    """
    if 20 <= age_now <= 40:
        return {**lookup_subsidy("thinning_1st", area_ha, region), "applicable": True}
    if 30 <= age_now <= 50:
        return {**lookup_subsidy("thinning_2nd", area_ha, region), "applicable": True}
    return {
        "amount_per_ha": 0,
        "total_amount": 0,
        "applicable": False,
        "korean": "간벌 부적격 임령",
        "note": f"age={age_now} 가 간벌 보조 적격 범위 (20-50) 밖",
    }


def lookup_reforestation_subsidy(area_ha: float, region: str = "충북") -> dict:
    """재조림 보조 (5년 통합)."""
    return lookup_subsidy("reforestation_seedling", area_ha, region)


if __name__ == "__main__":
    print("=" * 60)
    print("subsidies.py 자가 검증")
    print("=" * 60)

    # 검증 1: 솎아베기 1차 (충북 1.5ha)
    print("\n[검증 1] 솎아베기 1차 충북 1.5ha")
    r = lookup_subsidy("thinning_1st", area_ha=1.5, region="충북")
    print(f"  단가: {r['amount_per_ha']:,}원/ha")
    print(f"  보너스: {r['regional_bonus_rate'] * 100}%")
    print(f"  총: {r['total_amount']:,}원")
    expected = 2500000 * 1.5 * 1.10
    assert r["total_amount"] == round(expected)

    # 검증 2: 간벌 시나리오 매출 (보은 30년)
    print("\n[검증 2] 간벌 매출 (보은 강원소나무 30년 1.5ha)")
    r = lookup_thinning_revenue(area_ha=1.5, age_now=30, region="충북")
    print(
        f"  적용: {r['applicable']}, 단가: {r['amount_per_ha']:,}원/ha, 총: {r['total_amount']:,}원"
    )
    assert r["applicable"]
    assert r["total_amount"] == round(2500000 * 1.5 * 1.10)

    # 검증 3: 임령 범위 밖
    print("\n[검증 3] 임령 10년 (적격 범위 밖)")
    r = lookup_thinning_revenue(area_ha=1.0, age_now=10, region="충북")
    print(f"  적용: {r['applicable']}, note: {r.get('note')}")
    assert not r["applicable"]

    # 검증 4: 재조림
    print("\n[검증 4] 재조림 보조 (보은 2ha)")
    r = lookup_reforestation_subsidy(area_ha=2.0, region="충북")
    print(f"  총: {r['total_amount']:,}원")
    expected = 4500000 * 2.0 * 1.10
    assert r["total_amount"] == round(expected)

    print("\n" + "=" * 60)
    print("✅ subsidies.py 4/4 검증 통과")
    print("=" * 60)
