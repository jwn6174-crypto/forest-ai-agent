"""
weibull_probe.py — NFI 7차 충북 DBH 분포 진단 (D14 1단계).

목적:
  · 영급 × 임상 그룹별 DBH 분포 모양 확인
  · Weibull fit 가능성 검증 (그룹당 그루 수, 분포 형태)
  · D12 발견 (핵심 5 그룹) 재확인 + 충북 전체 확장

D12 발견 (보은 핵심 5 그룹):
  · 4영급 × 활엽수림 16, 4영급 × 혼효림 15
  · 5영급 × 혼효림 13, 5영급 × 활엽수림 11, 5영급 × 침엽수림 10

D14 결정 (D12 발견 4 잠정 추천):
  · 형질급 무관, DBH 분포 자체 fit (옵션 B)
"""
import csv
import math
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(__file__).resolve().parents[3]
NFI_DIR = ROOT / "module_bd" / "data" / "raw" / "nfi"
STAND_CSV = NFI_DIR / "nfi7_chungbuk_stand.csv"
TREE_CSV = NFI_DIR / "nfi7_chungbuk_tree.csv"


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
    """영급 코드 → 숫자 (4영급 → 4)."""
    if not age_class_str or '영급' not in str(age_class_str):
        return None
    try:
        return int(str(age_class_str).replace('영급', '').strip())
    except ValueError:
        return None


def histogram(values, bin_width=4, max_val=60):
    """DBH 히스토그램 (텍스트)."""
    bins = defaultdict(int)
    for v in values:
        if v is None:
            continue
        b = int(v // bin_width) * bin_width
        b = min(b, max_val)
        bins[b] += 1
    return bins


def main():
    print("=" * 75)
    print("NFI 7차 충북 DBH 분포 진단 (D14 1단계)")
    print("=" * 75)

    stands = load_csv_rows(STAND_CSV)
    trees = load_csv_rows(TREE_CSV)
    print(f"\n충북: {len(stands)} 표본점, {len(trees)} 그루")

    # 표본점 → (영급, 임상) 매핑
    plot_meta = {}
    for s in stands:
        plot_id = s['표본점번호']
        ac = age_class_num(s.get('영급'))
        imsang = s.get('임상')
        plot_meta[plot_id] = (ac, imsang)

    # 나무 → 그룹별 DBH 수집
    group_dbh = defaultdict(list)       # (영급, 임상) → [DBH...]
    age_only_dbh = defaultdict(list)    # 영급 → [DBH...]
    imsang_only_dbh = defaultdict(list) # 임상 → [DBH...]
    all_dbh = []

    for t in trees:
        plot_id = t.get('표본점번호')
        dbh = safe_float(t.get('DBH_cm'))
        if dbh is None or plot_id not in plot_meta:
            continue
        ac, imsang = plot_meta[plot_id]
        if ac is None or imsang is None:
            continue
        group_dbh[(ac, imsang)].append(dbh)
        age_only_dbh[ac].append(dbh)
        imsang_only_dbh[imsang].append(dbh)
        all_dbh.append(dbh)

    # 전체 DBH 통계
    print(f"\n{'=' * 75}")
    print("전체 DBH 통계:")
    print(f"{'=' * 75}")
    print(f"  유효: {len(all_dbh)} 그루")
    print(f"  범위: {min(all_dbh):.1f} ~ {max(all_dbh):.1f} cm")
    print(f"  평균: {sum(all_dbh)/len(all_dbh):.1f} cm")

    # 전체 히스토그램
    print(f"\n  전체 DBH 히스토그램 (4cm 구간):")
    hist = histogram(all_dbh)
    max_count = max(hist.values())
    for b in sorted(hist.keys()):
        bar = '█' * int(hist[b] / max_count * 40)
        print(f"    {b:>2}-{b+4:>2}cm: {hist[b]:>5} {bar}")

    # 그룹별 (영급 × 임상) 통계
    print(f"\n{'=' * 75}")
    print("영급 × 임상 그룹별 (≥100 그루, Weibull fit 가능):")
    print(f"{'=' * 75}")
    print(f"  {'영급':<6} {'임상':<12} {'그루':<7} {'평균DBH':<9} {'범위':<14}")
    print('-' * 60)

    fittable_groups = []
    for (ac, imsang), dbhs in sorted(group_dbh.items()):
        if len(dbhs) >= 100:
            fittable_groups.append((ac, imsang, len(dbhs)))
            print(f"  {ac}영급{'':<3} {imsang:<12} {len(dbhs):<7} "
                  f"{sum(dbhs)/len(dbhs):<9.1f} {min(dbhs):.0f}-{max(dbhs):.0f}cm")

    print(f"\n  → Weibull fit 가능 그룹 (≥100 그루): {len(fittable_groups)}")

    # 영급만 그룹 (임상 무관)
    print(f"\n{'=' * 75}")
    print("영급별 (임상 무관, ≥500 그루):")
    print(f"{'=' * 75}")
    print(f"  {'영급':<6} {'그루':<7} {'평균DBH':<9} {'범위':<14}")
    print('-' * 50)
    for ac, dbhs in sorted(age_only_dbh.items()):
        if len(dbhs) >= 500:
            print(f"  {ac}영급{'':<3} {len(dbhs):<7} {sum(dbhs)/len(dbhs):<9.1f} "
                  f"{min(dbhs):.0f}-{max(dbhs):.0f}cm")

    # 임상별
    print(f"\n{'=' * 75}")
    print("임상별 (영급 무관):")
    print(f"{'=' * 75}")
    for imsang, dbhs in sorted(imsang_only_dbh.items()):
        print(f"  {imsang:<12}: {len(dbhs):>6} 그루, 평균 {sum(dbhs)/len(dbhs):.1f} cm")

    # Weibull 적합성 사전 판단 (왜도)
    print(f"\n{'=' * 75}")
    print("Weibull 적합성 사전 판단 (왜도 — 오른쪽 꼬리 분포 기대):")
    print(f"{'=' * 75}")
    mean = sum(all_dbh) / len(all_dbh)
    std = (sum((x - mean)**2 for x in all_dbh) / len(all_dbh)) ** 0.5
    skew = sum((x - mean)**3 for x in all_dbh) / (len(all_dbh) * std**3)
    print(f"  전체 왜도: {skew:+.3f}")
    if skew > 0.3:
        print(f"  → 오른쪽 꼬리 분포 (양의 왜도). Weibull 적합 ✓")
    elif skew > -0.3:
        print(f"  → 대칭에 가까움. Weibull 또는 정규분포 모두 가능")
    else:
        print(f"  → 왼쪽 꼬리. Weibull 부적합 가능")

    print(f"\n다음: weibull_fit.py — scipy.stats.weibull_min 그룹별 fit")


if __name__ == "__main__":
    main()