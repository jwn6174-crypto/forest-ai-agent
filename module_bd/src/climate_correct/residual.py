"""
residual.py — NFI 표본점별 잔차 (V_actual - V_table) 산출.

D13 결정 1+4+7 통합:
  · si_estimate.py 알고리즘 → 표본점별 (수종, SI, 임령)
  · v_actual.py 알고리즘 → 표본점별 V_actual (m³/ha)
  · growth_predict._lookup_stand() → V_table (m³/ha)
  · 잔차 = V_actual - V_table

잔차 의미 (가이드 §2.3):
  · 잔차 > 0 → 우리 임분이 *임분수확표(2014) 시점보다 잘 자람*
    (기후·관리 변화 → climate_correct 가 학습할 신호)
  · 잔차 ≈ 0 → 임분수확표가 *현재 상태 정확*
  · 잔차 < 0 → 우리 임분이 *임분수확표 시점보다 못 자람*
    (가뭄·병충해·관리 부실 등 부정 요인)

기대 결과 (가이드 §2.3 가설):
  · 잔차 평균이 *양수* → 한국 산림이 *임분수확표보다 잘 자라는 추세*
  · 분산이 *기후 변수와 회귀 가능한 크기* → climate_correct 의미 있음

알고리즘:
  1. si_estimate, v_actual 의 알고리즘 재사용
  2. growth_predict._load_stand_table() + _lookup_stand() 호출
  3. 표본점별 (V_actual, V_table) → residual 산출
  4. 통계 + 영급·임상·수종별 잔차 분포

실행: python module_bd/src/climate_correct/residual.py
"""
import sys
from pathlib import Path
from collections import defaultdict, Counter
import csv

ROOT = Path(__file__).resolve().parents[3]
NFI_DIR = ROOT / "module_bd" / "data" / "raw" / "nfi"
YIELD_DIR = ROOT / "module_bd" / "data" / "interim"
STAND_CSV = NFI_DIR / "nfi7_chungbuk_stand.csv"
TREE_CSV = NFI_DIR / "nfi7_chungbuk_tree.csv"

# growth_predict 의 lookup 함수 사용
sys.path.insert(0, str(ROOT / "module_bd" / "src"))
from growth_predict import _load_stand_table, _lookup_stand

# 수종 매핑 (D13 결정 7)
NFI_TO_YIELD = {
    "소나무": "중부지방소나무",
    "잣나무": "잣나무",
    "리기다소나무": "리기다소나무",
    "일본잎갈나무": "낙엽송",
    "신갈나무": "신갈나무",
    "굴참나무": "굴참나무",
    "상수리나무": "상수리나무",
    "졸참나무": "신갈나무",  # 참나무 그룹 통합
    "갈참나무": "신갈나무",
    "떡갈나무": "신갈나무",
}

# 조사원 면적 (6차 §2.3.1)
BASIC_PLOT_AREA_HA = 0.04
LARGE_PLOT_AREA_HA = 0.08
LARGE_DBH_THRESHOLD = 30.0


def safe_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load_csv(path):
    if not path.exists():
        return []
    with open(path, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def age_class_to_age(age_class_str):
    """영급 코드 → 임령 중앙값."""
    if not age_class_str or '영급' not in age_class_str:
        return None
    try:
        n = int(age_class_str.replace('영급', '').strip())
        return 10 * n - 5
    except ValueError:
        return None


def get_dominant_species(trees):
    """우점수종 → 임분수확표 매핑명."""
    species_counts = Counter(t.get('수종명') for t in trees)
    if not species_counts:
        return None
    nfi_name = species_counts.most_common(1)[0][0]
    return NFI_TO_YIELD.get(nfi_name)


def get_avg_height(trees):
    """유효 수고 평균 (m)."""
    heights = [safe_float(t.get('수고_m')) for t in trees]
    valid = [h for h in heights if h is not None]
    return sum(valid) / len(valid) if valid else None


def estimate_si_from_yield(yield_df, species, age, measured_height):
    """yield_df 전체에서 SI 추정."""
    species_df = yield_df[yield_df["수종"] == species]
    if species_df.empty:
        return None

    available_sis = sorted(species_df["지위지수"].unique())
    si_heights = {}
    for si in available_sis:
        si_rows = species_df[species_df["지위지수"] == si]
        closest = si_rows.iloc[(si_rows["임령(년)"] - age).abs().argmin()]
        si_heights[si] = closest["우세목수고(m)"]

    best_si = min(si_heights.keys(),
                  key=lambda s: abs(si_heights[s] - measured_height))
    return float(best_si)


def compute_v_actual(plot_trees):
    """표본점 V_actual (m³/ha)."""
    v_basic = 0.0
    v_large = 0.0
    for tree in plot_trees:
        dbh = safe_float(tree.get('DBH_cm'))
        v = safe_float(tree.get('추정간재적'))
        if dbh is None or v is None:
            continue
        if dbh < LARGE_DBH_THRESHOLD:
            v_basic += v
        else:
            v_large += v
    return v_basic / BASIC_PLOT_AREA_HA + v_large / LARGE_PLOT_AREA_HA


def main():
    print("=" * 70)
    print("NFI 보은 표본점 잔차 (V_actual - V_table) 산출 (단계 4)")
    print("=" * 70)

    print("\n자료 로딩...")
    stands = load_csv(STAND_CSV)
    trees = load_csv(TREE_CSV)
    yield_df = _load_stand_table()
    print(f"  임분수확표: {len(yield_df)}행, 수종 {yield_df['수종'].nunique()}종")

    boeun_stands = [s for s in stands if s.get('시군구') == '보은군']
    boeun_ids = {s['표본점번호'] for s in boeun_stands}
    boeun_trees = [t for t in trees if t.get('표본점번호') in boeun_ids]
    print(f"  보은 표본점: {len(boeun_stands)}, 나무: {len(boeun_trees)}")

    # 표본점별 그룹
    trees_by_plot = defaultdict(list)
    for tree in boeun_trees:
        trees_by_plot[tree.get('표본점번호')].append(tree)

    # 표본점별 (V_actual, V_table, residual) 산출
    results = []
    for stand in boeun_stands:
        plot_id = stand['표본점번호']
        plot_trees = trees_by_plot.get(plot_id, [])
        if not plot_trees:
            continue

        age_class = stand.get('영급')
        age = age_class_to_age(age_class)
        species = get_dominant_species(plot_trees)
        avg_h = get_avg_height(plot_trees)

        # 자격 검증
        if age is None or species is None or avg_h is None:
            continue

        # SI 추정
        si = estimate_si_from_yield(yield_df, species, age, avg_h)
        if si is None:
            continue

        # V_actual
        v_actual = compute_v_actual(plot_trees)

        # V_table (growth_predict._lookup_stand 호출)
        stand_data = _lookup_stand(yield_df, species, int(si), age)
        if stand_data is None:
            continue

        v_table = stand_data.get('volume_m3_per_ha')
        if v_table is None:
            continue

        residual = v_actual - v_table

        results.append({
            'plot_id': plot_id,
            'age_class': age_class,
            'age': age,
            'imsang': stand.get('임상'),
            'species': species,
            'si': si,
            'v_actual': v_actual,
            'v_table': v_table,
            'residual': residual,
        })

    # 결과 표 (처음 30개)
    print(f"\n{'표본점':<12} {'영급':<5} {'수종':<13} {'SI':<4} {'V_actual':<9} {'V_table':<9} {'잔차':<8}")
    print('-' * 70)
    for r in results[:30]:
        print(f"{r['plot_id']:<12} {r['age_class']:<5} {r['species'][:11]:<13} "
              f"{r['si']:<4.0f} {r['v_actual']:<9.1f} {r['v_table']:<9.1f} "
              f"{r['residual']:+.1f}")
    if len(results) > 30:
        print(f"  ... (외 {len(results)-30}개)")

    # 통계
    print(f"\n{'=' * 70}")
    print("잔차 통계:")
    print(f"{'=' * 70}")
    print(f"  처리된 표본점: {len(results)}")

    residuals = [r['residual'] for r in results]
    if residuals:
        avg = sum(residuals) / len(residuals)
        rmean = avg
        rsd = (sum((r - rmean)**2 for r in residuals) / len(residuals)) ** 0.5
        residuals_sorted = sorted(residuals)
        median = residuals_sorted[len(residuals_sorted) // 2]

        print(f"\n  잔차 통계 (m³/ha):")
        print(f"    평균: {avg:+.1f}  (가이드 §2.3: 양수면 *시점 이후 생장 가속*)")
        print(f"    중앙값: {median:+.1f}")
        print(f"    표준편차: {rsd:.1f}")
        print(f"    범위: {min(residuals):+.1f} ~ {max(residuals):+.1f}")

        # 양수/음수 비율
        pos = sum(1 for r in residuals if r > 0)
        neg = sum(1 for r in residuals if r < 0)
        print(f"\n  잔차 부호:")
        print(f"    양수 (V_actual > V_table): {pos}/{len(residuals)} ({pos/len(residuals)*100:.0f}%)")
        print(f"    음수 (V_actual < V_table): {neg}/{len(residuals)} ({neg/len(residuals)*100:.0f}%)")

    # 분포
    print(f"\n  잔차 분포 (m³/ha):")
    bins = [(-200, -100), (-100, -50), (-50, 0), (0, 50),
            (50, 100), (100, 200), (200, 500)]
    for lo, hi in bins:
        n = sum(1 for r in residuals if lo <= r < hi)
        bar = '█' * (n // 2) if n >= 2 else '·' * n
        print(f"    {lo:>+4}~{hi:<+4}: {n:>3} {bar}")

    # 영급별 잔차
    print(f"\n  영급별 잔차 평균 (m³/ha):")
    age_r = defaultdict(list)
    for r in results:
        age_r[r['age_class']].append(r['residual'])
    for ag in sorted(age_r.keys()):
        rs = age_r[ag]
        print(f"    {ag}: 평균 {sum(rs)/len(rs):+.1f}, 범위 {min(rs):+.0f}~{max(rs):+.0f}, n={len(rs)}")

    # 임상별 잔차
    print(f"\n  임상별 잔차 평균 (m³/ha):")
    im_r = defaultdict(list)
    for r in results:
        im_r[r['imsang']].append(r['residual'])
    for im in sorted(im_r.keys()):
        rs = im_r[im]
        print(f"    {im}: 평균 {sum(rs)/len(rs):+.1f}, 범위 {min(rs):+.0f}~{max(rs):+.0f}, n={len(rs)}")

    # 수종별 잔차
    print(f"\n  수종별 잔차 평균 (m³/ha):")
    sp_r = defaultdict(list)
    for r in results:
        sp_r[r['species']].append(r['residual'])
    for sp in sorted(sp_r.keys()):
        rs = sp_r[sp]
        print(f"    {sp:<15}: 평균 {sum(rs)/len(rs):+.1f}, n={len(rs)}")

    print(f"\n{'=' * 70}")
    print("의미 해석:")
    print(f"{'=' * 70}")
    if residuals:
        if avg > 30:
            print(f"  → 평균 +{avg:.0f} m³/ha: 보은 임분이 *임분수확표 시점보다 잘 자람*.")
            print(f"     가이드 §2.3 가설 지지. climate_correct 학습 신호 강함.")
        elif avg > 0:
            print(f"  → 평균 +{avg:.0f} m³/ha: 약한 양수. 보정 의미는 있으나 미미.")
        else:
            print(f"  → 평균 {avg:.0f} m³/ha: 음수. 보은 임분 *생장 더딘 추세*.")
            print(f"     원인: 가뭄·병해 영향 가능. 추가 진단 필요.")

        if rsd > 50:
            print(f"  → 표준편차 {rsd:.0f}: 충분한 변동성. 기후 회귀 가능.")
        else:
            print(f"  → 표준편차 {rsd:.0f}: 변동성 작음. 회귀 R² 낮을 가능성.")

    print(f"\n  다음 단계 3: 표본점-산악기상 매칭 + 기후 변수 계산")


if __name__ == "__main__":
    main()