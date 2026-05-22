"""
run_all.py — Module C 전체 결과 재현 (정우 module_bd 패턴 모방).

1 명령으로 다음 모두 재현:
1. 6 polygon × 6 시나리오 LEV 계산
2. D22 검증 (4 real polygon vs carbonregistry)
3. D23 KAU 시계열 분석 + WTA 돌파 시각화
4. 민감도 분석 (5 차원)
5. 발표·논문 시각화 데이터 (Plotly JSON)

사용:
    python module_c/scripts/run_all.py [--output OUT_DIR] [--samples 300]

출력:
    OUT_DIR/results.json — 모든 polygon 결과
    OUT_DIR/d22_validation.json — D22 학술 발견
    OUT_DIR/d23_kau_timeseries.json — D23
    OUT_DIR/sensitivity.json — 민감도
    OUT_DIR/plotly_data.json — 시각화
"""

import json
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from module_c.src import (
    compute_lev_with_plan, get_demo_parcel, list_demo_parcels,
    list_sample_parcels, list_real_parcels,
)
from module_c.src.validation import validate_all_real_cases, summary_validation_report
from module_c.src.sensitivity import full_sensitivity_report
from module_c.src.pareto import format_pareto_for_plotly


def run_all_polygons(n_samples: int = 300, output_dir: Path = None) -> dict:
    """6 polygon × 6 시나리오 + Pareto + DraftPlanCard 통합."""
    output_dir = output_dir or (ROOT / "module_c" / "data" / "processed" / "run_all")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Module C — run_all.py 시작")
    print("=" * 70)
    print(f"  시작 시각: {datetime.now().isoformat()}")
    print(f"  MC samples: {n_samples}")
    print(f"  출력: {output_dir}")
    print()

    all_results = {}

    # 1. 모든 polygon × 시나리오
    print("[1/5] 6 polygon × 6 시나리오 계산")
    for parcel_id in list_demo_parcels():
        try:
            stand = get_demo_parcel(parcel_id)
            package = compute_lev_with_plan(stand, n_samples=n_samples)
            all_results[parcel_id] = {
                "parcel_meta": stand,
                "results": package["results"],
                "pareto": package["pareto"],
                "three_representative": package["three_representative"],
                "draft_plan": package["draft_plan"],
            }
            best = package["draft_plan"]["recommended_scenario"]
            print(f"  ✅ {parcel_id:<45s} 추천: {best}")
        except Exception as e:
            print(f"  ❌ {parcel_id}: {e}")
            all_results[parcel_id] = {"error": str(e)}

    # 결과 저장
    out_path = output_dir / "all_polygons_results.json"
    # numpy float 등 직렬화 안 되는 객체 제거
    out_path.write_text(json.dumps(
        all_results, ensure_ascii=False, indent=2, default=str,
    ), encoding="utf-8")
    print(f"  💾 {out_path}")

    # 2. D22 검증 (4 real polygon)
    print("\n[2/5] D22 검증 — 4 real polygon vs carbonregistry")
    validation = validate_all_real_cases(verbose=False)
    summary = summary_validation_report(validation)
    (output_dir / "d22_validation.json").write_text(
        json.dumps({"summary": summary, "cases": validation},
                    ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"  📊 평균 차이: {summary['avg_difference_pct']}%")
    print(f"  📝 학술 주장: {summary['academic_claim'][:60]}...")

    # 3. D23 KAU 시계열 (이미 저장됨)
    print("\n[3/5] D23 KAU 시계열")
    kau_path = ROOT / "module_c" / "data" / "raw" / "kau" / "kau_timeseries_2025_2026.json"
    if kau_path.exists():
        kau_data = json.loads(kau_path.read_text(encoding="utf-8"))
        (output_dir / "d23_kau_timeseries.json").write_text(
            json.dumps(kau_data, ensure_ascii=False, indent=2), encoding="utf-8",
        )
        kau25_history = [h for h in kau_data["history"] if h.get("vintage") == "KAU25"]
        peaks = [(h["period"], int(h["clpr"])) for h in kau25_history if h.get("clpr")]
        if peaks:
            min_p = min(peaks, key=lambda x: x[1])
            max_p = max(peaks, key=lambda x: x[1])
            print(f"  📈 KAU25 저점: {min_p[0]} {min_p[1]:,}원")
            print(f"  📈 KAU25 고점: {max_p[0]} {max_p[1]:,}원")
            change = (max_p[1] - min_p[1]) / min_p[1] * 100
            print(f"  📈 변화율: +{change:.1f}%")

    # 4. 민감도 (Primary 검증 case 1개)
    print("\n[4/5] 민감도 분석 (보은 산외면 오대리)")
    stand = get_demo_parcel("boeun_real_oedari_8197tco2")
    sens = full_sensitivity_report(stand, scenario="연장KOC")
    (output_dir / "sensitivity.json").write_text(
        json.dumps(sens, ensure_ascii=False, indent=2, default=str), encoding="utf-8",
    )
    print(f"  📐 5 차원 민감도 — SI/할인율/SSP/KAU/HWP")

    # 5. Plotly 시각화 데이터
    print("\n[5/5] Plotly 시각화 데이터")
    plotly_data = {
        "pareto_per_polygon": {},
        "d22_comparison": (output_dir.parent / "d22_plot_data.json").exists() and
            json.loads((output_dir.parent / "d22_plot_data.json").read_text(encoding="utf-8")),
        "d23_kau_breakthrough": (output_dir.parent / "d23_plot_data.json").exists() and
            json.loads((output_dir.parent / "d23_plot_data.json").read_text(encoding="utf-8")),
    }
    for pid, data in all_results.items():
        if data.get("pareto"):
            plotly_data["pareto_per_polygon"][pid] = format_pareto_for_plotly(data["pareto"])

    (output_dir / "plotly_data.json").write_text(
        json.dumps(plotly_data, ensure_ascii=False, indent=2, default=str), encoding="utf-8",
    )

    # 종합 보고
    print("\n" + "=" * 70)
    print("✅ run_all 완료")
    print("=" * 70)
    print(f"  완료 시각: {datetime.now().isoformat()}")
    print(f"  6 polygon × 6 시나리오 + D22·D23 + 민감도 + Plotly")
    print(f"  출력 디렉토리: {output_dir}")
    print(f"  파일 개수: {len(list(output_dir.glob('*.json')))}")

    return all_results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Module C 전체 결과 재현")
    parser.add_argument("--output", type=Path, default=None, help="출력 디렉토리")
    parser.add_argument("--samples", type=int, default=300, help="LHS MC samples")
    parser.add_argument("--fast", action="store_true", help="--samples 50 (빠른 검증)")
    args = parser.parse_args()

    n = 50 if args.fast else args.samples
    run_all_polygons(n_samples=n, output_dir=args.output)
