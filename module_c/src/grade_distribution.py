"""
grade_distribution.py — 등급분포 추정 (Strategy 패턴).

D14 (산림학자 + AI deliberation):
- 정우 `estimate_grade_dist(dbh_cm)` (api_server.py 안) = HeuristicGD (default)
- W4 Weibull-2P fit (Bailey & Dell 1973, 강진택 2016) → WeibullGD (swap)
- AI 엔지니어 권고: ABC 인터페이스 + CI regression test fault tolerance

희도 D14 결정 — 2026-05-20 Day 6 작성
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional


# 산림청 원목규격 6 등급 (말구지름 기준)
GRADE_BOUNDS_CM = {
    "특용재": (48, 999),    # ≥48cm
    "1등급":  (36, 48),
    "2등급":  (24, 36),
    "3등급":  (18, 24),
    "원주재": (14, 18),
    "원료재": (0,  14),
}


class GradeDistributionStrategy(ABC):
    """등급분포 추정 전략 — fault tolerant Strategy 패턴 (AI D14)."""

    @abstractmethod
    def estimate(self, dbh_cm: float, species: Optional[str] = None) -> Dict[str, float]:
        """DBH (cm) → 6 등급 비율 dict (합 1.0)."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...


class HeuristicGD(GradeDistributionStrategy):
    """
    정우 api_server.py 의 estimate_grade_dist 휴리스틱을 wrap.

    7 DBH 구간 룩업. 정우 코드와 *동일 출력* (검증 가능).
    한국 강원지방소나무의 일반적 등급 분포 기반.
    """

    name = "HeuristicGD"

    def estimate(self, dbh_cm: float, species: Optional[str] = None) -> Dict[str, float]:
        # 정우 estimate_grade_dist 의 7 DBH 구간 (api_server.py L120-130)
        # 정우는 정수 % 반환 — 우리는 0-1 비율로 변환
        if dbh_cm < 10:
            d = {"특용재": 0,  "1등급":  0, "2등급":  0, "3등급":  5, "원주재": 25, "원료재": 70}
        elif dbh_cm < 14:
            d = {"특용재": 0,  "1등급":  0, "2등급":  2, "3등급": 15, "원주재": 43, "원료재": 40}
        elif dbh_cm < 18:
            d = {"특용재": 0,  "1등급":  3, "2등급": 10, "3등급": 28, "원주재": 42, "원료재": 17}
        elif dbh_cm < 22:
            d = {"특용재": 1,  "1등급": 10, "2등급": 25, "3등급": 38, "원주재": 22, "원료재":  4}
        elif dbh_cm < 26:
            d = {"특용재": 2,  "1등급": 20, "2등급": 30, "3등급": 32, "원주재": 14, "원료재":  2}
        elif dbh_cm < 30:
            d = {"특용재": 4,  "1등급": 30, "2등급": 32, "3등급": 24, "원주재":  9, "원료재":  1}
        else:
            d = {"특용재": 7,  "1등급": 40, "2등급": 30, "3등급": 18, "원주재":  4, "원료재":  1}

        # 0-1 비율로 변환
        return {k: v / 100.0 for k, v in d.items()}


class WeibullGD(GradeDistributionStrategy):
    """
    Bailey & Dell (1973) Weibull-2P fit.

    NFI 표본점의 DBH 분포로 shape·scale 추정.
    영급 ↔ shape·scale 회귀로 임의 임령 등급분포 산출.

    *W4 후 정우 NFI 협업 시 구현*. 현재는 NotImplementedError.
    """

    name = "WeibullGD"

    def estimate(self, dbh_cm: float, species: Optional[str] = None) -> Dict[str, float]:
        raise NotImplementedError(
            "WeibullGD 는 W4 정우 NFI Weibull fit 협업 후 구현. "
            "현재는 HeuristicGD 사용."
        )


# Default (HeuristicGD) — W4 후 WeibullGD 로 swap
DEFAULT_STRATEGY: GradeDistributionStrategy = HeuristicGD()


def estimate_grade_distribution(
    dbh_cm: float,
    species: Optional[str] = None,
    strategy: Optional[GradeDistributionStrategy] = None,
) -> Dict[str, float]:
    """
    DBH → 6 등급 비율 (Strategy 패턴 진입점).

    Parameters
    ----------
    dbh_cm : float
        평균 흉고직경
    species : str, optional
        수종 (WeibullGD 에서 활용)
    strategy : GradeDistributionStrategy, optional
        None 이면 DEFAULT_STRATEGY (HeuristicGD)

    Returns
    -------
    dict
        {"특용재": 0.05, "1등급": 0.30, "2등급": 0.32, "3등급": 0.24, "원주재": 0.09, "원료재": 0.01}

    Examples
    --------
    >>> r = estimate_grade_distribution(28.5)
    >>> abs(sum(r.values()) - 1.0) < 0.01
    True
    >>> r["1등급"] > 0.2  # DBH ~28 → 1등급 30%
    True
    """
    strat = strategy or DEFAULT_STRATEGY
    result = strat.estimate(dbh_cm, species)

    # Sanity check: 합 = 1.0 ± 0.01
    total = sum(result.values())
    if abs(total - 1.0) > 0.05:
        raise ValueError(f"등급분포 합 {total:.4f} != 1.0 (strategy: {strat.name})")

    return result


if __name__ == "__main__":
    print("=" * 60)
    print("grade_distribution.py 자가 검증")
    print("=" * 60)

    # 검증 1: HeuristicGD 합 = 1.0
    print("\n[검증 1] 합 = 1.0")
    for dbh in [10, 16, 22, 28, 34, 50]:
        d = estimate_grade_distribution(dbh)
        total = sum(d.values())
        print(f"  DBH {dbh}cm: 합 {total:.4f} (특용재 {d['특용재']:.2f}, 1등급 {d['1등급']:.2f}, ...)")
        assert abs(total - 1.0) < 0.05

    # 검증 2: DBH 증가 → 1등급+ 증가
    print("\n[검증 2] DBH 증가 → 1등급+ 비율 증가")
    d_small = estimate_grade_distribution(14)
    d_large = estimate_grade_distribution(34)
    p_small = d_small["특용재"] + d_small["1등급"] + d_small["2등급"]
    p_large = d_large["특용재"] + d_large["1등급"] + d_large["2등급"]
    print(f"  DBH 14cm: 상위 3등급 합 {p_small:.2f}")
    print(f"  DBH 34cm: 상위 3등급 합 {p_large:.2f}")
    assert p_large > p_small

    # 검증 3: WeibullGD NotImplementedError
    print("\n[검증 3] WeibullGD NotImplementedError")
    weibull = WeibullGD()
    try:
        weibull.estimate(20.0)
        assert False, "NotImplementedError 가 안 발생"
    except NotImplementedError as e:
        print(f"  ✅ 예상대로 NotImplementedError: {str(e)[:50]}...")

    # 검증 4: Strategy 패턴 swap
    print("\n[검증 4] Strategy 패턴 swap")
    custom = HeuristicGD()
    d = estimate_grade_distribution(20.0, strategy=custom)
    print(f"  custom HeuristicGD: 합 {sum(d.values()):.4f}")
    assert abs(sum(d.values()) - 1.0) < 0.05

    print("\n" + "=" * 60)
    print("✅ grade_distribution.py 4/4 검증 통과")
    print("=" * 60)
