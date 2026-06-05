"""
weibull_fit.py — 등급분포 Weibull fit (D14 본 구현, 가이드 §5.5).

목적:
  · NFI 7차 충북 DBH 분포 → 영급 × 임상 그룹별 Weibull fit
  · shape (c), scale 모수 추정 (loc=6 고정, 최소 측정 DBH)
  · KS 검정 적합도 검증
  · grade_distribution() 함수 — 임분 DBH 등급별 본수 예측

가이드 §5.5:
  · "수종·영급별 등급분포 회귀"
  · 우리: 영급 × 임상 (23 그룹) + 영급 fallback (7 그룹)

진단 결과 (weibull_probe.py):
  · 전체 왜도 +1.112 → Weibull 교과서적 적합
  · 영급 × 임상 23 그룹 (≥100 그루)
  · 역-J 분포 (작은 나무 多, 큰 나무 少)

출력:
  · module_bd/data/processed/weibull_params.json
"""
import csv
import json
import math
from pathlib import Path
from collections import defaultdict

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
NFI_DIR = ROOT / "module_bd" / "data" / "raw" / "nfi"
PROCESSED_DIR = ROOT / "module_bd" / "data" / "processed"
STAND_CSV = NFI_DIR / "nfi7_chungbuk_stand.csv"
TREE_CSV = NFI_DIR / "nfi7_chungbuk_tree.csv"
OUT_PATH = PROCESSED_DIR / "weibull_params.json"

DBH_MIN = 6.0  # 최소 측정 DBH (NFI 기본조사원 기준)
MIN_TREES_GROUP = 100  # 그룹 fit 최소 그루 수
MIN_TREES_AGE = 300    # 영급 fallback 최소

# DBH 등급 (원목 등급 구분, cm)
DBH_GRADES = [
    ('소경재', 6, 18),    # 6-18cm
    ('중경재', 18, 30),   # 18-30cm
    ('대경재', 30, 999),  # 30cm+
]


def safe_float(v):
    if v is None or v == '':
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load_csv_rows(path):
    if not path.exists():
        return []
    with open(path, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def age_class_num(age_class_str):
    if not age_class_str or '영급' not in str(age_class_str):
        return None
    try:
        return int(str(age_class_str).replace('영급', '').strip())
    except ValueError:
        return None


def fit_weibull(dbh_values):
    """Weibull min fit (loc=6 고정). 반환: (shape, scale, ks_stat, ks_pvalue, n)."""
    arr = np.array([d for d in dbh_values if d is not None and d >= DBH_MIN])
    if len(arr) < MIN_TREES_GROUP:
        return None

    # loc 고정 fit (floc=DBH_MIN)
    try:
        shape, loc, scale = stats.weibull_min.fit(arr, floc=DBH_MIN)
    except Exception:
        return None

    # KS 검정
    ks_stat, ks_pvalue = stats.kstest(
        arr, 'weibull_min', args=(shape, loc, scale)
    )

    return {
        'shape': float(shape),
        'scale': float(scale),
        'loc': float(loc),
        'ks_stat': float(ks_stat),
        'ks_pvalue': float(ks_pvalue),
        'n': int(len(arr)),
        'mean_dbh': float(arr.mean()),
    }


def grade_proportions(shape, scale, loc=DBH_MIN):
    """Weibull 모수 → DBH 등급별 비율 (소경/중경/대경)."""
    props = {}
    for name, lo, hi in DBH_GRADES:
        # CDF(hi) - CDF(lo)
        cdf_hi = stats.weibull_min.cdf(hi, shape, loc, scale) if hi < 999 else 1.0
        cdf_lo = stats.weibull_min.cdf(lo, shape, loc, scale)
        props[name] = float(cdf_hi - cdf_lo)
    return props


def main():
    print("=" * 75)
    print("등급분포 Weibull fit (D14 본 구현, 가이드 §5.5)")
    print("=" * 75)

    stands = load_csv_rows(STAND_CSV)
    trees = load_csv_rows(TREE_CSV)
    print(f"\n충북: {len(stands)} 표본점, {len(trees)} 그루")

    # 표본점 → (영급, 임상)
    plot_meta = {}
    for s in stands:
        plot_id = s['표본점번호']
        ac = age_class_num(s.get('영급'))
        imsang = s.get('임상')
        plot_meta[plot_id] = (ac, imsang)

    # 그룹별 DBH 수집
    group_dbh = defaultdict(list)
    age_dbh = defaultdict(list)
    for t in trees:
        plot_id = t.get('표본점번호')
        dbh = safe_float(t.get('DBH_cm'))
        if dbh is None or plot_id not in plot_meta:
            continue
        ac, imsang = plot_meta[plot_id]
        if ac is None or imsang is None:
            continue
        group_dbh[(ac, imsang)].append(dbh)
        age_dbh[ac].append(dbh)

    # 1. 영급 × 임상 그룹 fit
    print(f"\n{'=' * 75}")
    print("영급 × 임상 그룹별 Weibull fit:")
    print(f"{'=' * 75}")
    print(f"  {'영급':<6} {'임상':<12} {'n':<7} {'shape':<8} {'scale':<8} "
          f"{'KS-p':<8} {'적합':<5}")
    print('-' * 65)

    group_params = {}
    fit_ok = 0
    for (ac, imsang), dbhs in sorted(group_dbh.items()):
        result = fit_weibull(dbhs)
        if result is None:
            continue
        adequate = "✓" if result['ks_pvalue'] > 0.05 else "△"
        if result['ks_pvalue'] > 0.05:
            fit_ok += 1
        key = f"{ac}_{imsang}"
        group_params[key] = result
        # grade 비율 추가
        result['grade_props'] = grade_proportions(result['shape'], result['scale'])
        print(f"  {ac}영급{'':<3} {imsang:<12} {result['n']:<7} "
              f"{result['shape']:<8.3f} {result['scale']:<8.2f} "
              f"{result['ks_pvalue']:<8.3f} {adequate}")

    print(f"\n  fit 성공 그룹: {len(group_params)}, KS 적합 (p>0.05): {fit_ok}")

    # 2. 영급 fallback fit
    print(f"\n{'=' * 75}")
    print("영급별 fallback Weibull fit (임상 무관):")
    print(f"{'=' * 75}")
    print(f"  {'영급':<6} {'n':<7} {'shape':<8} {'scale':<8} {'KS-p':<8} {'적합':<5}")
    print('-' * 50)

    age_params = {}
    for ac, dbhs in sorted(age_dbh.items()):
        if len(dbhs) < MIN_TREES_AGE:
            continue
        result = fit_weibull(dbhs)
        if result is None:
            continue
        adequate = "✓" if result['ks_pvalue'] > 0.05 else "△"
        result['grade_props'] = grade_proportions(result['shape'], result['scale'])
        age_params[str(ac)] = result
        print(f"  {ac}영급{'':<3} {result['n']:<7} {result['shape']:<8.3f} "
              f"{result['scale']:<8.2f} {result['ks_pvalue']:<8.3f} {adequate}")

    # 3. 등급 비율 예시 (대표 그룹)
    print(f"\n{'=' * 75}")
    print("등급별 비율 예시 (영급별, 임상 무관):")
    print(f"{'=' * 75}")
    print(f"  {'영급':<6} {'소경재':<10} {'중경재':<10} {'대경재':<10}")
    print(f"  {'':6} {'6-18cm':<10} {'18-30cm':<10} {'30cm+':<10}")
    print('-' * 50)
    for ac in sorted(age_params.keys(), key=int):
        props = age_params[ac]['grade_props']
        print(f"  {ac}영급{'':<3} {props['소경재']*100:<10.1f} "
              f"{props['중경재']*100:<10.1f} {props['대경재']*100:<10.1f}")

    # 4. 저장
    print(f"\n{'=' * 75}")
    print("저장:")
    print(f"{'=' * 75}")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    save_dict = {
        'metadata': {
            'method': 'scipy.stats.weibull_min (loc 고정 6cm)',
            'data': 'NFI 7차 충북 46722 그루',
            'dbh_grades': {name: [lo, hi] for name, lo, hi in DBH_GRADES},
            'n_groups_imsang': len(group_params),
            'n_groups_age': len(age_params),
        },
        'group_imsang': group_params,    # 영급_임상 → 모수
        'age_fallback': age_params,       # 영급 → 모수
    }
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(save_dict, f, ensure_ascii=False, indent=2)
    print(f"  ✓ {OUT_PATH.relative_to(ROOT)} ({OUT_PATH.stat().st_size // 1024} KB)")

    # 5. 의미 해석
    print(f"\n{'=' * 75}")
    print("의미 해석:")
    print(f"{'=' * 75}")
    print(f"  영급 × 임상: {len(group_params)} 그룹 fit")
    print(f"  영급 fallback: {len(age_params)} 그룹 fit")
    ks_rate = fit_ok / len(group_params) * 100 if group_params else 0
    print(f"  KS 적합률 (p>0.05): {ks_rate:.0f}%")
    if ks_rate >= 60:
        print(f"  → Weibull 분포 대부분 그룹에 적합. 등급분포 valid ✓")
    elif ks_rate >= 30:
        print(f"  → 일부 그룹 적합. 큰 표본은 KS 검정 엄격 (정상)")
    else:
        print(f"  → KS 엄격 (대표본). shape/scale 자체는 의미 있음")
    print(f"\n  주: KS 검정은 대표본(n>1000)에서 작은 편차도 기각하는 경향.")
    print(f"      shape·scale 모수는 등급 비율 산출에 직접 사용 가능.")

    print(f"\n다음: grade_distribution() 함수 → growth_predict 통합 (등급별 본수 예측)")


if __name__ == "__main__":
    main()