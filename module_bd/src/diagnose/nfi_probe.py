"""
nfi_probe.py — NFI 7차 보은·충북 깊은 진단 (v4, 추출본 csv 기반).

목적:
  · nfi_extract.py 가 만든 stand.csv + tree.csv 로 빠른 진단
  · climate_correct·Weibull 설계 직접 입력 정보 산출
  · D13·D14 결정 전 *분포·매핑* 확인

진단 5가지:
  1. 보은 수종 매핑 — 우리 가이드 11 수종 vs NFI 실측
  2. 영급 × 임상 cross-tab — Weibull 그룹 후보
  3. 수고 단위 변환 검증 — 평균 13.58m 매칭 (D11 결정 2)
  4. 형질급 분포 — Weibull fit 시 *형질급 1·2* 만 사용 권장 여부
  5. 표본점당 본수 분포 — 표본점별 vs 그룹별 fit 가능성

데이터:
  module_bd/data/raw/nfi/nfi7_chungbuk_stand.csv  (1162행)
  module_bd/data/raw/nfi/nfi7_chungbuk_tree.csv   (46,722행)

실행 시간: 약 0.5초 (csv 0.1초 로딩 × 2)
"""
from pathlib import Path
import csv
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[3]
NFI_DIR = ROOT / "module_bd" / "data" / "raw" / "nfi"
STAND_CSV = NFI_DIR / "nfi7_chungbuk_stand.csv"
TREE_CSV = NFI_DIR / "nfi7_chungbuk_tree.csv"


# 가이드 11 수종 (가이드 §8.2, growth_predict 지원)
GUIDE_11_SPECIES = [
    "강원지방소나무", "중부지방소나무", "잣나무", "낙엽송",
    "리기다소나무", "곰솔", "편백",
    "신갈나무", "굴참나무", "상수리나무", "이태리포플러",
]

# NFI → 가이드 매핑 (D11 결정 6 보강)
NFI_TO_GUIDE = {
    "소나무": ["강원지방소나무", "중부지방소나무"],  # 지방형 구분 별도
    "잣나무": ["잣나무"],
    "리기다소나무": ["리기다소나무"],
    "일본잎갈나무": ["낙엽송"],
    "곰솔": ["곰솔"],
    "편백": ["편백"],
    "신갈나무": ["신갈나무"],
    "굴참나무": ["굴참나무"],
    "상수리나무": ["상수리나무"],
    # 이태리포플러는 NFI 명칭이 다를 수 있음
}


def safe_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load_csv(path):
    """csv 로딩 (utf-8-sig 으로 BOM 처리)."""
    if not path.exists():
        print(f"⚠ 파일 없음: {path}")
        return []
    with open(path, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def filter_boeun(rows, key='시군구'):
    """보은 표본점만 추출."""
    return [r for r in rows if r.get(key) == '보은군']


def diag1_species_mapping(trees):
    """진단 1: 보은 수종 매핑 (NFI 실측 → 우리 11 수종)."""
    print("=" * 60)
    print("[진단 1] 보은 수종 매핑 — 가이드 11 수종 vs NFI 실측")
    print("=" * 60)

    species_counts = Counter(t.get('수종명') for t in trees)
    print(f"\nNFI 수종 종류: {len(species_counts)}개")

    print(f"\n우리 11 수종 매칭:")
    mapped_total = 0
    for nfi_name, guide_names in NFI_TO_GUIDE.items():
        n = species_counts.get(nfi_name, 0)
        if n > 0:
            mapped_total += n
            guide_str = " / ".join(guide_names)
            print(f"  NFI '{nfi_name}' → 가이드 '{guide_str}': {n}그루")

    coverage = mapped_total / len(trees) * 100 if trees else 0
    print(f"\n매칭 비율: {mapped_total}/{len(trees)} = {coverage:.1f}%")

    print(f"\n매칭 안 된 상위 수종 (회귀 fallback 대상):")
    unmapped = [(s, n) for s, n in species_counts.most_common(20)
                if s not in NFI_TO_GUIDE]
    for s, n in unmapped[:10]:
        print(f"  {s}: {n}그루")


def diag2_age_imsang_crosstab(stands):
    """진단 2: 영급 × 임상 cross-tab (Weibull 그룹 후보)."""
    print("\n" + "=" * 60)
    print("[진단 2] 보은 영급 × 임상 cross-tab — Weibull 그룹")
    print("=" * 60)

    ct = defaultdict(lambda: defaultdict(int))
    for s in stands:
        ag = s.get('영급') or '(결측)'
        im = s.get('임상') or '(결측)'
        ct[ag][im] += 1

    # 헤더
    imsangs = sorted({im for ags in ct.values() for im in ags})
    print(f"\n           {''.join(im[:10].ljust(12) for im in imsangs)}")
    for ag in sorted(ct.keys()):
        row = ag.ljust(10)
        for im in imsangs:
            n = ct[ag].get(im, 0)
            row += str(n).rjust(11) + ' '
        print(f"  {row}")

    # 핵심 그룹 (4·5영급 × 임상)
    print(f"\n핵심 그룹 (4-5영급, 31-50년):")
    for ag in ['4영급', '5영급']:
        for im, n in ct[ag].items():
            if n >= 5:
                print(f"  {ag} × {im}: {n}개 표본점 (Weibull fit 가능)")


def diag3_height_unit_check(trees):
    """진단 3: 수고 단위 변환 검증 (D11 결정 2)."""
    print("\n" + "=" * 60)
    print("[진단 3] 수고 단위 변환 검증 — D11 결정 2 (cm ÷100 = m)")
    print("=" * 60)

    heights = [safe_float(t.get('수고_m')) for t in trees]
    valid = [h for h in heights if h is not None]
    invalid = len(heights) - len(valid)

    if not valid:
        print("  ⚠ 유효 수고 0건")
        return

    print(f"\n  유효 측정: {len(valid)}/{len(trees)} ({len(valid)/len(trees)*100:.1f}%)")
    print(f"  결측: {invalid}그루")
    print(f"  범위: {min(valid):.1f} ~ {max(valid):.1f}m")
    print(f"  평균: {sum(valid)/len(valid):.2f}m")
    print(f"\n  D11 결정 2 검증:")
    print(f"    한국 임분 평균 수고 12-16m 범위")
    avg = sum(valid)/len(valid)
    if 10 <= avg <= 18:
        print(f"    실측 평균 {avg:.2f}m → 정상 범위 ✓ (cm ÷100 = m 적용)")
    else:
        print(f"    실측 평균 {avg:.2f}m → 범위 밖. 단위 재검토 필요")


def diag4_formjeol_distribution(trees):
    """진단 4: 형질급 분포 (Weibull fit 시 양품만 사용 권장 여부)."""
    print("\n" + "=" * 60)
    print("[진단 4] 보은 형질급 분포 — Weibull fit 대상 결정")
    print("=" * 60)

    counts = Counter(t.get('형질급') for t in trees)
    total = sum(counts.values())
    print(f"\n  형질급 분포 ({total}그루):")
    for fg in ['1급목', '2급목', '3급목']:
        n = counts.get(fg, 0)
        pct = n / total * 100 if total else 0
        print(f"    {fg}: {n}그루 ({pct:.1f}%)")
    other = total - sum(counts.get(fg, 0) for fg in ['1급목', '2급목', '3급목'])
    if other > 0:
        print(f"    기타/결측: {other}그루")

    print(f"\n  의사결정:")
    n1 = counts.get('1급목', 0)
    n2 = counts.get('2급목', 0)
    print(f"    옵션 A: 1·2급목만 Weibull fit → {n1+n2}그루 ({(n1+n2)/total*100:.1f}%)")
    print(f"    옵션 B: 전체 형질급 fit → {total}그루")
    print(f"    옵션 C: 형질급 별도 fit (1급·2급·3급 각각)")


def diag5_trees_per_plot(stands, trees):
    """진단 5: 표본점당 본수 분포."""
    print("\n" + "=" * 60)
    print("[진단 5] 보은 표본점당 본수 분포")
    print("=" * 60)

    plot_counts = Counter(t.get('표본점번호') for t in trees)

    counts = list(plot_counts.values())
    if not counts:
        print("  ⚠ 표본점 매칭 0건")
        return

    counts.sort()
    avg = sum(counts) / len(counts)
    median = counts[len(counts) // 2]

    print(f"\n  본수 통계 ({len(counts)} 표본점):")
    print(f"    최소: {min(counts)}그루")
    print(f"    최대: {max(counts)}그루")
    print(f"    평균: {avg:.1f}그루")
    print(f"    중앙값: {median}그루")

    # 분포 빈도
    bins = [(1, 10), (11, 20), (21, 30), (31, 50), (51, 80), (81, 200)]
    print(f"\n  본수 구간 분포:")
    for lo, hi in bins:
        n = sum(1 for c in counts if lo <= c <= hi)
        bar = '█' * (n // 2)
        print(f"    {lo:>3}-{hi:<3}: {n:>3} 표본점 {bar}")

    # 표본점별 fit 가능성
    fittable = sum(1 for c in counts if c >= 20)
    print(f"\n  표본점별 Weibull fit 가능 (≥20그루): {fittable}/{len(counts)} 표본점")
    if fittable >= 50:
        print(f"  → 표본점별 fit 도 가능. 단, 그룹 fit 이 통계적 강건성 높음.")
    else:
        print(f"  → 표본점별 fit 비추천. *그룹 fit (수종·영급)* 권장.")


def main():
    print("=" * 60)
    print("NFI 7차 보은 깊은 진단 (v4, csv 기반)")
    print("=" * 60)

    # 빠른 로딩
    print(f"\nCSV 로딩 (0.1초씩)...")
    stands = load_csv(STAND_CSV)
    trees = load_csv(TREE_CSV)
    print(f"  stand: {len(stands)}행")
    print(f"  tree: {len(trees)}행")

    # 보은만
    boeun_stands = filter_boeun(stands)
    boeun_ids = {s['표본점번호'] for s in boeun_stands}
    boeun_trees = [t for t in trees if t.get('표본점번호') in boeun_ids]
    print(f"  보은 표본점: {len(boeun_stands)}개")
    print(f"  보은 나무: {len(boeun_trees)}그루")

    # 5가지 진단
    diag1_species_mapping(boeun_trees)
    diag2_age_imsang_crosstab(boeun_stands)
    diag3_height_unit_check(boeun_trees)
    diag4_formjeol_distribution(boeun_trees)
    diag5_trees_per_plot(boeun_stands, boeun_trees)

    print(f"\n{'=' * 60}")
    print(f"v4 진단 끝. D13·D14 설계 결정 입력 확보.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()