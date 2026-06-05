"""
grade_distribution.py — 등급분포 예측 (D14 완성, 가이드 §5.5 + §8.1).

weibull_fit.py 가 산출한 weibull_params.json 을 로드하여,
임분의 DBH 등급별 본수를 예측한다.

용도:
  · NPV 계산 (희도 모듈 C): 원목 등급별 매출
  · growth_predict() 통합: grade_distribution_trajectory (가이드 §8.1)

등급 (DBH 기준, cm):
  · 소경재: 6-18cm
  · 중경재: 18-30cm
  · 대경재: 30cm+

사용 예:
    from module_bd.src.grade_distribution import grade_distribution

    result = grade_distribution(
        age_class=5,            # 5영급 (41-50년)
        imsang='혼효림(M)',     # 임상 (None 가능 → 영급 fallback)
        n_total_per_ha=800,     # ha당 총 본수
    )
    # 반환:
    # {
    #   '소경재': 483, '중경재': 233, '대경재': 84,
    #   'proportions': {...}, 'params_used': {...}, 'fallback': False
    # }
"""
import json
from pathlib import Path

from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
PARAMS_PATH = ROOT / "module_bd" / "data" / "processed" / "weibull_params.json"

DBH_MIN = 6.0
DBH_GRADES = [
    ('소경재', 6, 18),
    ('중경재', 18, 30),
    ('대경재', 30, 999),
]

_params_cache = None


def _load_params():
    """weibull_params.json 로드 (캐시)."""
    global _params_cache
    if _params_cache is None:
        if not PARAMS_PATH.exists():
            raise FileNotFoundError(
                f"weibull_params.json 없음: {PARAMS_PATH}. "
                f"먼저 weibull_fit.py 실행 필요."
            )
        with open(PARAMS_PATH, encoding='utf-8') as f:
            _params_cache = json.load(f)
    return _params_cache


def _grade_proportions(shape, scale, loc=DBH_MIN):
    """Weibull 모수 → DBH 등급별 비율."""
    props = {}
    for name, lo, hi in DBH_GRADES:
        cdf_hi = stats.weibull_min.cdf(hi, shape, loc, scale) if hi < 999 else 1.0
        cdf_lo = stats.weibull_min.cdf(lo, shape, loc, scale)
        props[name] = float(cdf_hi - cdf_lo)
    return props


def grade_distribution(age_class, imsang=None, n_total_per_ha=None):
    """
    임분 DBH 등급별 본수 예측.

    Args:
        age_class: 영급 (1-10, int)
        imsang: 임상 ('침엽수림(D)'/'활엽수림(H)'/'혼효림(M)' 또는 None)
        n_total_per_ha: ha당 총 본수 (None 이면 비율만 반환)

    Returns:
        dict:
          소경재/중경재/대경재: 등급별 본수 (n_total 주어진 경우)
          proportions: 등급별 비율
          shape/scale: 사용된 Weibull 모수
          fallback: 영급 fallback 사용 여부
          group_key: 사용된 그룹 키
    """
    params = _load_params()
    group_imsang = params['group_imsang']
    age_fallback = params['age_fallback']

    # 1. 영급 × 임상 우선
    fallback = False
    group_key = None
    fit = None

    if imsang is not None:
        key = f"{age_class}_{imsang}"
        if key in group_imsang:
            fit = group_imsang[key]
            group_key = key

    # 2. 영급 fallback
    if fit is None:
        key = str(age_class)
        if key in age_fallback:
            fit = age_fallback[key]
            group_key = f"영급{age_class}(fallback)"
            fallback = True

    # 3. 그래도 없으면 — 가장 가까운 영급 fallback
    if fit is None:
        available_ages = sorted(int(k) for k in age_fallback.keys())
        if not available_ages:
            raise ValueError("weibull_params.json 에 영급 데이터 없음.")
        closest = min(available_ages, key=lambda a: abs(a - age_class))
        fit = age_fallback[str(closest)]
        group_key = f"영급{closest}(nearest fallback)"
        fallback = True

    # 4. 등급 비율
    shape = fit['shape']
    scale = fit['scale']
    props = _grade_proportions(shape, scale)

    result = {
        'proportions': props,
        'shape': shape,
        'scale': scale,
        'fallback': fallback,
        'group_key': group_key,
    }

    # 5. 본수 산출 (n_total 주어진 경우)
    if n_total_per_ha is not None:
        # 비율 정규화 (CDF 차이 합이 1 이 아닐 수 있음 — 6cm 미만 제외분)
        total_prop = sum(props.values())
        for name, _, _ in DBH_GRADES:
            normalized = props[name] / total_prop if total_prop > 0 else 0
            result[name] = int(round(n_total_per_ha * normalized))

    return result


def grade_distribution_trajectory(age_class_now, imsang, n_per_ha_trajectory,
                                   forecast_years):
    """
    growth_predict() trajectory 통합용 — 각 시점 등급분포.

    Args:
        age_class_now: 현재 영급
        imsang: 임상
        n_per_ha_trajectory: 각 시점 본수 리스트 (growth_predict 출력)
        forecast_years: 예측 연도 리스트 [0, 10, 20...]

    Returns:
        List[dict]: 각 시점 등급별 본수
    """
    trajectory = []
    for dt, n_per_ha in zip(forecast_years, n_per_ha_trajectory):
        # 영급 추정: 현재 영급 + 경과 연수 / 10
        future_age_class = age_class_now + int(dt // 10)
        future_age_class = min(future_age_class, 10)  # 최대 10영급
        dist = grade_distribution(future_age_class, imsang, n_per_ha)
        trajectory.append({
            'dt': dt,
            'age_class': future_age_class,
            '소경재': dist.get('소경재'),
            '중경재': dist.get('중경재'),
            '대경재': dist.get('대경재'),
            'fallback': dist['fallback'],
        })
    return trajectory


def main():
    """데모 — 영급별 등급분포 예시."""
    print("=" * 70)
    print("grade_distribution() 데모 (D14 완성)")
    print("=" * 70)

    # 예시 1: 영급 × 임상
    print("\n예시 1: 5영급 혼효림, ha당 800본")
    r = grade_distribution(5, '혼효림(M)', 800)
    print(f"  그룹: {r['group_key']} (fallback={r['fallback']})")
    print(f"  shape={r['shape']:.3f}, scale={r['scale']:.2f}")
    print(f"  소경재 {r['소경재']}본, 중경재 {r['중경재']}본, 대경재 {r['대경재']}본")

    # 예시 2: 영급 fallback
    print("\n예시 2: 4영급 (임상 미지정), ha당 1000본")
    r = grade_distribution(4, None, 1000)
    print(f"  그룹: {r['group_key']} (fallback={r['fallback']})")
    print(f"  소경재 {r['소경재']}본, 중경재 {r['중경재']}본, 대경재 {r['대경재']}본")

    # 예시 3: 영급별 비율 비교
    print("\n예시 3: 영급별 등급 비율 (임상 무관, %)")
    print(f"  {'영급':<6} {'소경재':<10} {'중경재':<10} {'대경재':<10}")
    print('-' * 45)
    for ac in range(2, 9):
        r = grade_distribution(ac, None, 1000)
        p = r['proportions']
        total = sum(p.values())
        print(f"  {ac}영급{'':<3} {p['소경재']/total*100:<10.1f} "
              f"{p['중경재']/total*100:<10.1f} {p['대경재']/total*100:<10.1f}")

    # 예시 4: trajectory
    print("\n예시 4: growth_predict trajectory 통합 (4영급 시작, 혼효림)")
    traj = grade_distribution_trajectory(
        age_class_now=4, imsang='혼효림(M)',
        n_per_ha_trajectory=[1200, 900, 700, 550],
        forecast_years=[0, 10, 20, 30],
    )
    for t in traj:
        print(f"  {t['dt']:>2}년후 ({t['age_class']}영급): "
              f"소경 {t['소경재']}, 중경 {t['중경재']}, 대경 {t['대경재']}")

    print("\n→ NPV 계산: 등급별 본수 × 등급별 재적 × 등급별 가격")


if __name__ == "__main__":
    main()