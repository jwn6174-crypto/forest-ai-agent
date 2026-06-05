"""
lhs_sampling.py — Latin Hypercube Sampling (LHS) for Monte Carlo.

AI 엔지니어 deliberation 권고 (D11):
- 1000 단순 MC 의 std 3-7% → LHS 300 samples 로 std 1-2% 동등 정확도
- scipy.stats.qmc.LatinHypercube 사용
- 6 분산 source: AGB, 목재가, KOC, NTFP, 할인율, 기후 multiplier

희도 D11 결정 — 2026-05-20 Day 6 작성
"""

import math
from typing import Dict, List, Tuple

try:
    import numpy as np
    from scipy.stats import lognorm, norm, qmc, triang

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


def lhs_samples(
    n_samples: int,
    n_dim: int,
    seed: int = 42,
) -> "np.ndarray":
    """
    LHS 의 uniform [0,1) sample 행렬.

    Returns shape = (n_samples, n_dim).
    """
    if not HAS_SCIPY:
        raise ImportError("scipy 필요 — `pip install scipy`")
    sampler = qmc.LatinHypercube(d=n_dim, seed=seed)
    return sampler.random(n=n_samples)


def transform_uniform_to_distribution(
    u: float,
    dist_type: str,
    params: Dict[str, float],
) -> float:
    """
    Uniform [0,1) → 지정 분포로 inverse CDF 변환.

    Parameters
    ----------
    u : float in [0, 1)
        LHS uniform sample
    dist_type : str
        "lognormal" | "normal" | "triangular"
    params : dict
        분포별 파라미터
        - lognormal: {mean (의 mean), std} or {mu, sigma}
        - normal: {mean, std}
        - triangular: {min, mode, max}

    Returns
    -------
    float
    """
    if dist_type == "lognormal":
        if "mu" in params and "sigma" in params:
            mu, sigma = params["mu"], params["sigma"]
        else:
            # mean/std → mu/sigma 변환
            m, s = params["mean"], params["std"]
            if m <= 0:
                return 0.0
            sigma = math.sqrt(math.log(1 + (s / m) ** 2))
            mu = math.log(m) - sigma**2 / 2
        return lognorm.ppf(u, s=sigma, scale=math.exp(mu))

    if dist_type == "normal":
        return norm.ppf(u, loc=params["mean"], scale=params["std"])

    if dist_type == "triangular":
        lo, mode, hi = params["min"], params["mode"], params["max"]
        c = (mode - lo) / (hi - lo)
        return triang.ppf(u, c=c, loc=lo, scale=hi - lo)

    raise ValueError(f"Unknown dist_type: {dist_type}")


def generate_lhs_samples_6d(
    n_samples: int,
    distributions: Dict[str, Tuple[str, Dict[str, float]]],
    seed: int = 42,
) -> List[Dict[str, float]]:
    """
    6 분산 source × n_samples LHS 생성.

    Parameters
    ----------
    n_samples : int
        LHS samples (권장 200-500)
    distributions : dict
        {source_name: (dist_type, params), ...}
        예: {"timber_price_grade1": ("lognormal", {"mean": 199700, "std": 19970}), ...}
    seed : int

    Returns
    -------
    list[dict]
        각 sample 의 source_name → value dict

    Examples
    --------
    >>> dists = {
    ...     "agb": ("triangular", {"min": 80, "mode": 100, "max": 120}),
    ...     "timber_price": ("lognormal", {"mean": 200_000, "std": 20_000}),
    ...     "discount_rate": ("triangular", {"min": 0.04, "mode": 0.05, "max": 0.06}),
    ... }
    >>> samples = generate_lhs_samples_6d(300, dists, seed=42)
    >>> len(samples)
    300
    """
    if not HAS_SCIPY:
        raise ImportError("scipy 필요")

    sources = list(distributions.keys())
    n_dim = len(sources)
    uniform_matrix = lhs_samples(n_samples, n_dim, seed)

    results = []
    for i in range(n_samples):
        sample = {}
        for j, source_name in enumerate(sources):
            dist_type, params = distributions[source_name]
            u = uniform_matrix[i, j]
            sample[source_name] = float(transform_uniform_to_distribution(u, dist_type, params))
        results.append(sample)

    return results


if __name__ == "__main__":
    print("=" * 60)
    print("lhs_sampling.py 자가 검증")
    print("=" * 60)

    if not HAS_SCIPY:
        print("⚠️  scipy 미설치 — `pip install scipy` 후 재실행")
        print("코드 자체는 임포트 시점에만 에러 — 런타임 동작 확인 skip")
    else:
        # 검증 1: LHS 행렬 shape
        print("\n[검증 1] LHS shape")
        m = lhs_samples(300, 6, seed=42)
        print(f"  shape: {m.shape}, range: [{m.min():.4f}, {m.max():.4f}]")
        assert m.shape == (300, 6)
        assert 0 <= m.min() and m.max() < 1

        # 검증 2: Lognormal 변환 (양수)
        print("\n[검증 2] Lognormal — 모두 양수")
        vals = [
            transform_uniform_to_distribution(u, "lognormal", {"mean": 200_000, "std": 20_000})
            for u in [0.05, 0.5, 0.95]
        ]
        print(f"  q05, median, q95: {[int(v) for v in vals]}")
        assert all(v > 0 for v in vals)
        assert vals[0] < vals[2]

        # 검증 3: 6D LHS
        print("\n[검증 3] 6D LHS 300 samples")
        dists = {
            "agb_mg": ("triangular", {"min": 80, "mode": 100, "max": 120}),
            "timber_price": ("lognormal", {"mean": 199_700, "std": 19_970}),
            "koc_price": ("lognormal", {"mean": 12_040, "std": 1806}),
            "ntfp_annual": ("lognormal", {"mean": 5_500_000, "std": 1_500_000}),
            "discount_rate": ("triangular", {"min": 0.04, "mode": 0.05, "max": 0.06}),
            "climate_mult": ("normal", {"mean": 1.0, "std": 0.10}),
        }
        samples = generate_lhs_samples_6d(300, dists, seed=42)
        print(f"  생성: {len(samples)} samples")
        print(f"  첫 sample 키: {list(samples[0].keys())}")
        print(f"  agb_mg 평균: {sum(s['agb_mg'] for s in samples) / len(samples):.1f}")
        print(f"  timber_price 평균: {sum(s['timber_price'] for s in samples) / len(samples):,.0f}")
        print(
            f"  discount_rate 평균: {sum(s['discount_rate'] for s in samples) / len(samples):.4f}"
        )
        assert len(samples) == 300

    print("\n" + "=" * 60)
    print("✅ lhs_sampling.py 검증 통과")
    print("=" * 60)
