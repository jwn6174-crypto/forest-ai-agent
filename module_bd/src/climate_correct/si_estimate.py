"""
si_estimate.py — NFI 표본점별 SI(지위지수) 추정.

D13 결정 1 구현 (옵션 B):
  표본점별 평균 수고 + 영급 (→ 임령) → 임분수확표 우세목수고 역산 → SI 매칭

알고리즘:
  1. 표본점별 *유효 수고 평균* 계산 (tree.csv, 표준목 5-10본)
  2. 표본점별 *우점수종* 결정 (tree.csv 본수 최다)
  3. 영급 → 임령 (중앙값: N영급 → 10N-5년)
  4. (수종, 임령) 으로 yield_stand csv 필터
  5. 측정 수고와 가장 가까운 SI 매칭

데이터:
  · NFI 보은 stand.csv (102 표본점)
  · NFI 보은 tree.csv (4,505 그루)
  · yield_stand_*.csv (11 수종, module_bd/data/interim/)

출력:
  · 표본점별 SI 추정값 (콘솔)
  · 진단: 매칭 가능 표본점 수, SI 분포

실행: python module_bd/src/climate_correct/si_estimate.py
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv

ROOT = Path(__file__).resolve().parents[3]
NFI_DIR = ROOT / "module_bd" / "data" / "raw" / "nfi"
YIELD_DIR = ROOT / "module_bd" / "data" / "interim"
STAND_CSV = NFI_DIR / "nfi7_chungbuk_stand.csv"
TREE_CSV = NFI_DIR / "nfi7_chungbuk_tree.csv"

# 수종 매핑 (D13 결정 7)
NFI_TO_YIELD = {
    "소나무": "중부지방소나무",  # 충북 = 중부지방
    "잣나무": "잣나무",
    "리기다소나무": "리기다소나무",
    "일본잎갈나무": "낙엽송",
    "곰솔": None,  # 임분수확표 없음
    "신갈나무": "신갈나무",
    "굴참나무": "굴참나무",
    "상수리나무": "상수리나무",
    # 참나무 그룹 통합 (D13 결정 7)
    "졸참나무": "신갈나무",  # 신갈나무 표준 적용
    "갈참나무": "신갈나무",
    "떡갈나무": "신갈나무",
}


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


def age_class_to_age(age_class_str):
    """영급 코드 → 임령 중앙값. 예: '4영급' → 35."""
    if not age_class_str or '영급' not in age_class_str:
        return None
    try:
        n = int(age_class_str.replace('영급', '').strip())
        return 10 * n - 5  # N영급 = 10(N-1)+1 ~ 10N → 중앙값 10N-5
    except ValueError:
        return None


def get_dominant_species(trees):
    """표본점 내 본수 최다 수종 → 임분수확표 매핑명 반환."""
    species_counts = Counter(t.get('수종명') for t in trees)
    if not species_counts:
        return None
    nfi_name = species_counts.most_common(1)[0][0]
    return NFI_TO_YIELD.get(nfi_name)


def get_avg_height(trees):
    """표본점 내 *유효 수고* 평균 (m)."""
    heights = [safe_float(t.get('수고_m')) for t in trees]
    valid = [h for h in heights if h is not None]
    if not valid:
        return None
    return sum(valid) / len(valid)


def load_yield_stand(yield_species):
    """yield_stand_{species}.csv 로딩."""
    path = YIELD_DIR / f"yield_stand_{yield_species}.csv"
    if not path.exists():
        return None
    return load_csv(path)


def estimate_si(yield_species, age, measured_height):
    """
    (수종, 임령, 측정수고) → SI 추정.

    가장 가까운 SI 매칭:
      1. yield_stand csv 에서 (수종, 임령 가장 가까운 행) 필터
      2. 각 SI 별로 우세목수고 보고
      3. 측정수고와 가장 가까운 SI 반환
    """
    yield_data = load_yield_stand(yield_species)
    if not yield_data:
        return None, "yield_stand 없음"

    # 임령 가장 가까운 행 필터 (각 SI 별로 1행)
    rows_by_si = defaultdict(list)
    for row in yield_data:
        si = safe_float(row.get('지위지수'))
        ag = safe_float(row.get('임령(년)'))
        ht = safe_float(row.get('우세목수고(m)'))
        if si is None or ag is None or ht is None:
            continue
        rows_by_si[si].append({'age': ag, 'height': ht})

    if not rows_by_si:
        return None, "유효 데이터 없음"

    # 각 SI 별로 임령에 가장 가까운 행의 수고
    si_heights = {}
    for si, rows in rows_by_si.items():
        closest = min(rows, key=lambda r: abs(r['age'] - age))
        si_heights[si] = closest['height']

    # 측정 수고와 가장 가까운 SI
    best_si = min(si_heights.keys(),
                  key=lambda s: abs(si_heights[s] - measured_height))
    return best_si, f"매칭 (수고차 {abs(si_heights[best_si] - measured_height):.2f}m)"


def main():
    print("=" * 70)
    print("NFI 보은 표본점 SI(지위지수) 추정 (단계 1)")
    print("=" * 70)

    print("\nCSV 로딩...")
    stands = load_csv(STAND_CSV)
    trees = load_csv(TREE_CSV)

    # 보은만
    boeun_stands = [s for s in stands if s.get('시군구') == '보은군']
    boeun_ids = {s['표본점번호'] for s in boeun_stands}
    boeun_trees = [t for t in trees if t.get('표본점번호') in boeun_ids]

    print(f"  보은 표본점: {len(boeun_stands)}")
    print(f"  보은 나무: {len(boeun_trees)}")

    # 표본점별 진단
    print(f"\n{'표본점':<15} {'영급':<6} {'임령':<5} {'수종':<15} {'평균수고':<8} {'SI':<6} {'비고'}")
    print('-' * 70)

    results = []
    for stand in boeun_stands:
        plot_id = stand['표본점번호']
        age_class = stand.get('영급')
        age = age_class_to_age(age_class)

        # 해당 표본점 나무
        plot_trees = [t for t in boeun_trees if t.get('표본점번호') == plot_id]
        if not plot_trees:
            continue

        species = get_dominant_species(plot_trees)
        avg_h = get_avg_height(plot_trees)

        # SI 추정
        if age is None:
            si, note = None, "영급 결측"
        elif species is None:
            si, note = None, "수종 매핑 X"
        elif avg_h is None:
            si, note = None, "수고 측정 0"
        else:
            si, note = estimate_si(species, age, avg_h)

        results.append({
            'plot_id': plot_id,
            'age_class': age_class,
            'age': age,
            'species': species,
            'avg_h': avg_h,
            'si': si,
            'note': note,
        })

        # 처음 30개만 출력
        if len([r for r in results if r['si'] is not None]) <= 30:
            age_str = f"{age}" if age else "-"
            sp_str = species[:13] if species else "-"
            h_str = f"{avg_h:.1f}m" if avg_h else "-"
            si_str = f"{si:.0f}" if si else "-"
            print(f"{plot_id:<15} {age_class or '-':<6} {age_str:<5} {sp_str:<15} {h_str:<8} {si_str:<6} {note}")

    # 요약
    print(f"\n{'=' * 70}")
    print("요약:")
    print(f"{'=' * 70}")
    valid = [r for r in results if r['si'] is not None]
    print(f"  매칭 성공: {len(valid)}/{len(results)} 표본점 ({len(valid)/len(results)*100:.1f}%)")

    # 실패 원인
    fail_notes = Counter(r['note'] for r in results if r['si'] is None)
    if fail_notes:
        print(f"\n  매칭 실패 원인:")
        for note, n in fail_notes.most_common():
            print(f"    · {note}: {n}건")

    # SI 분포
    if valid:
        si_counts = Counter(r['si'] for r in valid)
        print(f"\n  SI 분포:")
        for si in sorted(si_counts.keys()):
            n = si_counts[si]
            bar = '█' * n
            print(f"    SI={si:.0f}: {n:>3} {bar}")

    # 수종별 SI 평균
    print(f"\n  수종별 SI 평균:")
    sp_si = defaultdict(list)
    for r in valid:
        sp_si[r['species']].append(r['si'])
    for sp in sorted(sp_si.keys()):
        sis = sp_si[sp]
        print(f"    {sp:<15}: SI {min(sis):.0f}~{max(sis):.0f}, "
              f"평균 {sum(sis)/len(sis):.1f}, n={len(sis)}")


if __name__ == "__main__":
    main()