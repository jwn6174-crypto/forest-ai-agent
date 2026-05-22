"""
ntfp_income.py — Non-Timber Forest Products 임산물 연수입 lookup.

시나리오 S5 (임산물 병행) 의 π_NTFP(t) 항.

D13 (경영자 권고): KOSIS 폐기 → 산림청 임산물생산조사 + 충북농기원 + 산림조합.
D 산림학자 권고: S5 → S5a 표고 (carbon 중립~+15%), S5b 송이 (carbon -15~-25%) 분리.

데이터:
- 출처: 산림청 「2023 임산물 생산조사」 (전국 평균 추정)
- 표고: 3-8M/ha (4년차 peak), 송이: 0.5-3M/ha (천연발생), 산양삼: 0.5-1.5M/ha (7년차)

희도 D13 결정 — 2026-05-20 Day 6 작성
"""

import json
import math
import random
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[1]
NTFP_PATH = ROOT / "data" / "raw" / "ntfp" / "forest_byproduct_income_2023.json"


def _load_ntfp() -> dict:
    with open(NTFP_PATH, encoding="utf-8") as f:
        return json.load(f)


NTFP_Product = Literal[
    "shiitake_oak_log",  # 표고 (S5a)
    "pine_mushroom",  # 송이 (S5b)
    "wild_ginseng_short",  # 산양삼 (S5c)
    "wild_vegetables",  # 산나물 (S5d)
    "chestnut",  # 밤 (S5e)
]


def lookup_ntfp(
    product: NTFP_Product = "shiitake_oak_log",
    species_host: str | None = None,
    region: str = "충북 보은",
) -> dict:
    """
    NTFP 평균 연소득 (원/ha/년) lookup.

    Parameters
    ----------
    product : str
        NTFP 종류 (shiitake_oak_log 등)
    species_host : str
        host 임지 수종 — 적용 가능성 검증
    region : str
        지역 (현재는 정보 표시만)

    Returns
    -------
    dict
        {
            "mean": float,
            "min": float, "max": float, "p25": float, "p75": float,
            "std": float,
            "peak_year": int,
            "yield_period_years": int,
            "carbon_impact_on_pine": str,
            "applicable_to_species": bool,
            ...
        }

    Examples
    --------
    >>> r = lookup_ntfp("shiitake_oak_log", species_host="참나무류")
    >>> r["mean"]
    5500000.0
    """
    data = _load_ntfp()
    products = data["products"]

    if product not in products:
        raise ValueError(f"Unknown NTFP product: {product}. Valid: {list(products.keys())}")

    p = products[product]
    income = p.get("annual_income_won_per_ha", {})

    applicable_hosts = p.get("applicable_species_host", ["all"])
    is_applicable = "all" in applicable_hosts or species_host in applicable_hosts

    return {
        "product": product,
        "korean_name": p["korean_name"],
        "mean": float(income.get("mean", 0)),
        "min": float(income.get("min", 0)),
        "max": float(income.get("max", 0)),
        "p25": float(income.get("p25", income.get("min", 0))),
        "p75": float(income.get("p75", income.get("max", 0))),
        "std": float(p.get("std_estimate", income.get("mean", 0) * 0.2)),
        "peak_year_after_inoculation": p.get(
            "peak_year_after_inoculation", p.get("peak_year_after_planting", 1)
        ),
        "yield_period_years": p.get("yield_period_years", 5),
        "carbon_impact_on_pine": p.get("carbon_impact_on_pine", "neutral"),
        "applicable_to_species": is_applicable,
        "applicable_hosts": applicable_hosts,
        "scenario_label": p.get("scenario_label", "S5"),
        "source": p.get("source_korea"),
        "region_note": "전국 평균 (보은 추가 보정 미적용)",
    }


def compute_ntfp_npv(
    product: NTFP_Product,
    duration_years: int,
    discount_rate: float = 0.05,
    species_host: str | None = None,
    rng: random.Random | None = None,
    sample: bool = False,
) -> dict:
    """
    NTFP 의 NPV 계산 (할인된 연소득 합).

    Parameters
    ----------
    product : str
        NTFP 종류
    duration_years : int
        병행 기간 (예: 시나리오 S5 의 age_now → T 까지)
    discount_rate : float
        할인율
    species_host : str
        host 수종
    rng : random.Random, optional
        MC sampling
    sample : bool
        MC 모드

    Returns
    -------
    dict
        {
            "npv": float,
            "annual_mean": float,
            "annual_sampled": float (if sample=True),
            "applicable": bool,
            ...
        }

    Examples
    --------
    >>> # 15년 표고 병행, r=5%
    >>> r = compute_ntfp_npv("shiitake_oak_log", 15, 0.05)
    >>> r["npv"] > 30_000_000
    True
    """
    info = lookup_ntfp(product, species_host=species_host)
    annual_mean = info["mean"]

    if sample and rng is not None:
        # Lognormal sampling (Y > 0 보장)
        sigma = math.log(1 + (info["std"] / annual_mean) ** 2) ** 0.5 if annual_mean > 0 else 0.3
        mu = math.log(annual_mean) - sigma**2 / 2 if annual_mean > 0 else 0
        annual = rng.lognormvariate(mu, sigma) if annual_mean > 0 else 0
    else:
        annual = annual_mean

    # 할인된 합산
    # peak year 전까지는 0, 그 후 period 까지
    peak = info["peak_year_after_inoculation"]
    yield_period = info["yield_period_years"]
    if isinstance(yield_period, str):
        yield_period = duration_years  # "indefinite"

    yield_start = min(peak, duration_years)
    yield_end = min(yield_start + yield_period, duration_years)

    npv = 0.0
    for t in range(yield_start, yield_end + 1):
        npv += annual * math.exp(-discount_rate * t)

    return {
        "npv": round(npv),
        "annual_mean": annual_mean,
        "annual_sampled": annual if sample else None,
        "duration_years": duration_years,
        "yield_start": yield_start,
        "yield_end": yield_end,
        "applicable": info["applicable_to_species"],
        "product": product,
        "carbon_impact_note": info["carbon_impact_on_pine"],
    }


if __name__ == "__main__":
    print("=" * 60)
    print("ntfp_income.py 자가 검증")
    print("=" * 60)

    # 검증 1: 표고 mean = 5.5M
    print("\n[검증 1] 표고 lookup")
    r = lookup_ntfp("shiitake_oak_log", species_host="참나무류")
    print(f"  mean: {r['mean']:,}원/ha/yr, peak: {r['peak_year_after_inoculation']}년차")
    assert r["mean"] == 5_500_000
    assert r["applicable_to_species"]

    # 검증 2: 송이 host 검증
    print("\n[검증 2] 송이 host = 강원지방소나무")
    r = lookup_ntfp("pine_mushroom", species_host="강원지방소나무")
    print(f"  carbon_impact: {r['carbon_impact_on_pine']}")
    assert r["applicable_to_species"]
    assert "-15" in r["carbon_impact_on_pine"]

    # 검증 3: 표고 15년 NPV
    print("\n[검증 3] 표고 15년 병행 NPV")
    r = compute_ntfp_npv("shiitake_oak_log", duration_years=15, discount_rate=0.05)
    print(f"  NPV: {r['npv']:,}원 (yield {r['yield_start']}~{r['yield_end']}년차)")
    assert r["npv"] > 10_000_000

    # 검증 4: 송이 30년 NPV (장기)
    print("\n[검증 4] 송이 30년 병행 NPV")
    r = compute_ntfp_npv("pine_mushroom", duration_years=30, discount_rate=0.05)
    print(f"  NPV: {r['npv']:,}원")
    assert r["npv"] > 0

    # 검증 5: MC sampling
    print("\n[검증 5] MC sampling 10회 (Lognormal)")
    rng = random.Random(42)
    samples = [
        compute_ntfp_npv("shiitake_oak_log", 15, 0.05, "참나무류", rng, sample=True)
        for _ in range(10)
    ]
    npvs = [s["npv"] for s in samples]
    print(f"  NPV 분포: min={min(npvs):,}, median={sorted(npvs)[5]:,}, max={max(npvs):,}")

    print("\n" + "=" * 60)
    print("✅ ntfp_income.py 5/5 검증 통과")
    print("=" * 60)
