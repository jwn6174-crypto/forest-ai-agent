"""
v_actual.py — NFI 표본점별 실측 임목축적 V_actual (m³/ha) 산출.

D13 결정 4 구현:
  · 기본조사원 (DBH 6~30cm): 0.04ha 면적, V/0.04 × 본수
  · 대경목조사원 (DBH ≥30cm): 0.08ha 면적, V/0.08 × 본수

알고리즘:
  표본점 V_actual = sum(추정간재적[DBH<30]) / 0.04
                  + sum(추정간재적[DBH>=30]) / 0.08

지침서 근거 (6차 §2.3.1):
  · 기본조사원: 반경 11.3m, 면적 0.04ha
  · 대경목조사원: 반경 16.0m, 면적 0.08ha
  · 6cm <= DBH < 30cm 대상 기본조사원
  · DBH >= 30cm 만 대경목조사원

진단:
  · 표본점별 V_actual 통계 (m³/ha)
  · 대경목 비중 (대경목 V / 전체 V)
  · 임분수확표 V_table 과 비교 (sanity check)

실행: python module_bd/src/climate_correct/v_actual.py
"""
from pathlib import Path
from collections import defaultdict, Counter
import csv

ROOT = Path(__file__).resolve().parents[3]
NFI_DIR = ROOT / "module_bd" / "data" / "raw" / "nfi"
STAND_CSV = NFI_DIR / "nfi7_chungbuk_stand.csv"
TREE_CSV = NFI_DIR / "nfi7_chungbuk_tree.csv"

# 조사원 면적 (6차 §2.3.1)
BASIC_PLOT_AREA_HA = 0.04   # 기본조사원 (DBH 6~30cm)
LARGE_PLOT_AREA_HA = 0.08   # 대경목조사원 (DBH ≥30cm)

# 대경목 기준
LARGE_DBH_THRESHOLD = 30.0  # cm


def safe_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load_csv(path):
    if not path.exists():
        print(f"⚠ 파일 없음: {path}")
        return []
    with open(path, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def compute_v_actual(plot_trees):
    """
    표본점 내 나무들 → V_actual (m³/ha) 산출.

    Returns:
        dict with:
          v_actual_m3_ha (float),
          v_basic (소·중경 합 m³/ha),
          v_large (대경 합 m³/ha),
          n_basic (소·중경 본수),
          n_large (대경 본수)
    """
    v_basic_sum = 0.0  # 0.04ha 표본의 재적 합
    v_large_sum = 0.0  # 0.08ha 표본의 재적 합
    n_basic = 0
    n_large = 0

    for tree in plot_trees:
        dbh = safe_float(tree.get('DBH_cm'))
        v = safe_float(tree.get('추정간재적'))
        if dbh is None or v is None:
            continue

        if dbh < LARGE_DBH_THRESHOLD:
            v_basic_sum += v
            n_basic += 1
        else:
            v_large_sum += v
            n_large += 1

    # m³ → m³/ha 변환
    v_basic_per_ha = v_basic_sum / BASIC_PLOT_AREA_HA
    v_large_per_ha = v_large_sum / LARGE_PLOT_AREA_HA
    v_actual = v_basic_per_ha + v_large_per_ha

    return {
        'v_actual_m3_ha': v_actual,
        'v_basic_m3_ha': v_basic_per_ha,
        'v_large_m3_ha': v_large_per_ha,
        'n_basic': n_basic,
        'n_large': n_large,
        'large_share': v_large_per_ha / v_actual if v_actual > 0 else 0,
    }


def main():
    print("=" * 70)
    print("NFI 보은 표본점 V_actual 산출 (단계 2)")
    print("=" * 70)

    print("\nCSV 로딩...")
    stands = load_csv(STAND_CSV)
    trees = load_csv(TREE_CSV)

    boeun_stands = [s for s in stands if s.get('시군구') == '보은군']
    boeun_ids = {s['표본점번호'] for s in boeun_stands}
    boeun_trees = [t for t in trees if t.get('표본점번호') in boeun_ids]
    print(f"  보은 표본점: {len(boeun_stands)}")
    print(f"  보은 나무: {len(boeun_trees)}")

    # 표본점별 그룹
    trees_by_plot = defaultdict(list)
    for tree in boeun_trees:
        plot_id = tree.get('표본점번호')
        if plot_id:
            trees_by_plot[plot_id].append(tree)

    # 표본점별 V_actual 산출
    results = []
    for stand in boeun_stands:
        plot_id = stand['표본점번호']
        plot_trees = trees_by_plot.get(plot_id, [])
        if not plot_trees:
            continue

        result = compute_v_actual(plot_trees)
        result['plot_id'] = plot_id
        result['age_class'] = stand.get('영급')
        result['imsang'] = stand.get('임상')
        results.append(result)

    # 통계
    print(f"\n{'=' * 70}")
    print("산출 결과:")
    print(f"{'=' * 70}")
    print(f"  처리된 표본점: {len(results)}/{len(boeun_stands)}")

    v_actuals = [r['v_actual_m3_ha'] for r in results]
    v_actuals.sort()
    if v_actuals:
        avg = sum(v_actuals) / len(v_actuals)
        median = v_actuals[len(v_actuals) // 2]
        print(f"\n  V_actual 통계 (m³/ha):")
        print(f"    최소: {min(v_actuals):.1f}")
        print(f"    최대: {max(v_actuals):.1f}")
        print(f"    평균: {avg:.1f}")
        print(f"    중앙값: {median:.1f}")

        # 보고서 비교
        print(f"\n  비교 (2020 한국 산림자원 보고서):")
        print(f"    전국 평균: 165 m³/ha")
        print(f"    OECD 평균보다 높음 명시")
        if 100 <= avg <= 250:
            print(f"    → 보은 평균 {avg:.1f} 합리적 범위 ✓")
        else:
            print(f"    → 보은 평균 {avg:.1f} 검토 필요")

    # 대경목 비중
    large_shares = [r['large_share'] for r in results if r['v_actual_m3_ha'] > 0]
    if large_shares:
        avg_large_share = sum(large_shares) / len(large_shares) * 100
        print(f"\n  대경목 비중 (V_large / V_actual):")
        print(f"    평균: {avg_large_share:.1f}%")
        print(f"    (2020 보고서: 전국 대경목 90본/ha, 평균 임목축적 165m³/ha)")

    # 분포 빈도 (히스토그램)
    print(f"\n  V_actual 분포 (m³/ha):")
    bins = [(0, 50), (50, 100), (100, 150), (150, 200),
            (200, 300), (300, 500), (500, 1000)]
    for lo, hi in bins:
        n = sum(1 for v in v_actuals if lo <= v < hi)
        bar = '█' * (n // 2) if n >= 2 else '·' * n
        print(f"    {lo:>4}-{hi:<4}: {n:>3} {bar}")

    # 영급별 평균
    age_v = defaultdict(list)
    for r in results:
        age_v[r['age_class']].append(r['v_actual_m3_ha'])
    print(f"\n  영급별 V_actual 평균 (m³/ha):")
    for ag in sorted(age_v.keys(), key=lambda x: (x or 'zz')):
        if ag:
            vs = age_v[ag]
            print(f"    {ag}: 평균 {sum(vs)/len(vs):.1f}, 범위 {min(vs):.0f}~{max(vs):.0f}, n={len(vs)}")

    # 임상별 평균
    imsang_v = defaultdict(list)
    for r in results:
        imsang_v[r['imsang']].append(r['v_actual_m3_ha'])
    print(f"\n  임상별 V_actual 평균 (m³/ha):")
    for im in sorted(imsang_v.keys(), key=lambda x: (x or 'zz')):
        if im:
            vs = imsang_v[im]
            print(f"    {im}: 평균 {sum(vs)/len(vs):.1f}, 범위 {min(vs):.0f}~{max(vs):.0f}, n={len(vs)}")

    print(f"\n{'=' * 70}")
    print("다음 단계 3: 표본점-산악기상 매칭 (좌표 최근접) + 기후 변수 계산")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()