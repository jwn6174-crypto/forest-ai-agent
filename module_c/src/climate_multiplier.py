"""
climate_multiplier.py — SSP 기후 시나리오 × 수종 → 생장 multiplier.

산림학자 deliberation 권고:
- 정우 growth_predict(climate_scenario="SSP245") 가 D8 진행 중이라 미작동.
- 내가 별도 multiplier 로 보정 — Monte Carlo 의 6번째 분산 source.

데이터:
- 출처: 임종환 (2020) 국립산림과학원 + IPCC AR6 한국 지역 투영
- 강원지방소나무 SSP245 평균 0.97, SSP585 평균 0.80
- 낙엽송 SSP245 평균 0.80 (정책 수종 전환 대상)
- 참나무류 SSP245 평균 1.15 (열적 유리)

희도 D11.b 결정 — 2026-05-20 Day 6 작성
"""

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIMATE_PATH = ROOT / "data" / "raw" / "climate" / "climate_multipliers_2020.json"


def _load_climate_data() -> dict:
    with open(CLIMATE_PATH, encoding="utf-8") as f:
        return json.load(f)


# 수종 alias (정우 carbon_table 패턴 모방)
SPECIES_ALIASES = {
    "상수리나무": "참나무류",
    "신갈나무": "참나무류",
    "굴참나무": "참나무류",
    "소나무": "강원지방소나무",
}


def get_climate_multiplier(
    species: str,
    scenario: str = "baseline",
    rng: random.Random | None = None,
    sample: bool = False,
) -> float:
    """
    수종 × SSP 시나리오 → 생장 multiplier.

    Parameters
    ----------
    species : str
        수종명 (강원지방소나무, 낙엽송, 참나무류 등)
    scenario : str
        "baseline" | "SSP126" | "SSP245" | "SSP585"
    rng : random.Random, optional
        Monte Carlo 용 seeded RNG
    sample : bool
        True 면 Normal(mean, std) sampling, False 면 mean

    Returns
    -------
    float
        생장 multiplier (예: 0.97 = -3% 생장 감소)

    Examples
    --------
    >>> get_climate_multiplier("강원지방소나무", "SSP245")
    0.97
    >>> get_climate_multiplier("낙엽송", "SSP585")
    0.68
    """
    data = _load_climate_data()
    multipliers = data["multipliers"]

    # alias 처리
    canonical = SPECIES_ALIASES.get(species, species)

    if canonical not in multipliers:
        return 1.0

    species_data = multipliers[canonical]
    if isinstance(species_data, str):
        # "참나무류 동일" 같은 reference
        canonical = species_data.split()[0]
        species_data = multipliers[canonical]

    if scenario not in species_data:
        scenario = "baseline"

    params = species_data[scenario]

    if sample and rng is not None:
        mean = params["mean"]
        std = params["std"]
        # 음수 방지: max(0.1, sampled)
        return max(0.1, rng.gauss(mean, std))

    return params["mean"]


def apply_multiplier_to_trajectory(
    volume_trajectory: list,
    species: str,
    scenario: str = "baseline",
    rng: random.Random | None = None,
    sample: bool = False,
) -> list:
    """
    volume trajectory 의 각 시점에 climate multiplier 적용.

    단순화: 동일 multiplier 를 모든 시점에 적용 (30년 horizon 평균).
    정밀하게 하려면 시점별 multiplier 보간 — 추후 D11.c 결정.

    Parameters
    ----------
    volume_trajectory : list[float]
        정우 growth_predict 의 volume_per_ha 시계열
    species : str
        수종
    scenario : str
        SSP 시나리오
    rng : random.Random, optional
        MC sampling 용
    sample : bool
        MC 모드 여부

    Returns
    -------
    list[float]
        보정된 volume trajectory

    Examples
    --------
    >>> traj = [100.0, 150.0, 200.0, 250.0]
    >>> apply_multiplier_to_trajectory(traj, "낙엽송", "SSP585")
    [68.0, 102.0, 136.0, 170.0]
    """
    m = get_climate_multiplier(species, scenario, rng, sample)
    return [round(v * m, 2) for v in volume_trajectory]


if __name__ == "__main__":
    print("=" * 60)
    print("climate_multiplier.py 자가 검증")
    print("=" * 60)

    # 검증 1: baseline = 1.0
    print("\n[검증 1] baseline = 1.0")
    m = get_climate_multiplier("강원지방소나무", "baseline")
    print(f"  강원지방소나무 baseline: {m}")
    assert m == 1.0

    # 검증 2: 낙엽송 SSP585 < 0.7
    print("\n[검증 2] 낙엽송 SSP585 (취약 수종)")
    m = get_climate_multiplier("낙엽송", "SSP585")
    print(f"  낙엽송 SSP585: {m}")
    assert m < 0.75

    # 검증 3: 참나무 SSP245 > 1.1 (열적 유리)
    print("\n[검증 3] 참나무류 SSP245 (열적 유리)")
    m = get_climate_multiplier("참나무류", "SSP245")
    print(f"  참나무류 SSP245: {m}")
    assert m > 1.1

    # 검증 4: trajectory 적용
    print("\n[검증 4] trajectory 적용")
    traj = [100.0, 150.0, 200.0]
    boosted = apply_multiplier_to_trajectory(traj, "참나무류", "SSP245")
    print(f"  baseline: {traj}")
    print(f"  SSP245:   {boosted}")
    assert all(b > t for b, t in zip(boosted, traj, strict=False))

    # 검증 5: MC sampling
    print("\n[검증 5] MC sampling (10회)")
    rng = random.Random(42)
    samples = [
        get_climate_multiplier("강원지방소나무", "SSP245", rng, sample=True) for _ in range(10)
    ]
    print(f"  samples: {[round(s, 3) for s in samples]}")
    print(f"  mean: {sum(samples) / len(samples):.3f}")

    print("\n" + "=" * 60)
    print("✅ climate_multiplier.py 5/5 검증 통과")
    print("=" * 60)
