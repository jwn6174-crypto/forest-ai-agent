"""
mt_weather_process.py — 산악기상 jsonl → 일/월/연 통계 csv.

가이드 §2.3 책임: "산악기상 시계열 수집·전처리"
설계 결정 (D10):
  · 기온: tm2m (2m 높이, 식생 영향)
  · 일평균: (min(04-06시) + max(14-16시)) / 2  — 기상학 정식
  · 강수: 제외 (rn 6시간만 측정, cprn 정체 불명)
  · 임지 평균: 가용한 관측소들 단순 평균 (그룹 A/B 동등)
    → 그룹 B (시루산·삼승산·노성산) 2024-07~11 결측에도
      연평균 영향 0.03°C 이하로 강건성 실증.

산출 (data/processed/):
  mt_weather_daily.csv    임지 일평균 (≈1,585행, 4년)
  mt_weather_monthly.csv  월별 통계 (53행)
  mt_weather_annual.csv   연별 통계 (5년, climate_correct 입력)
"""

import csv
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "module_bd" / "data" / "raw" / "mt_weather"
OUT = ROOT / "module_bd" / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

STATIONS = {
    3033: "가덕산",
    3898: "금단산",
    3903: "염동산",
    3915: "시루산",
    3917: "삼승산",
    3918: "노성산",
}


def read_station_jsonl(obsid: int) -> dict[str, list[tuple[int, float]]]:
    """한 관측소 jsonl → 날짜별 (시각, tm2m) 리스트."""
    path = RAW / f"obs_{obsid}.jsonl"
    by_date: dict[str, list[tuple[int, float]]] = defaultdict(list)
    with open(path, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            if not rec.get("ok"):
                continue
            data = rec.get("data") or {}
            tm2m = data.get("tm2m")
            tm = data.get("tm")
            if tm2m is None or tm is None:
                continue
            dt = datetime.strptime(tm, "%Y-%m-%d %H:%M")
            by_date[dt.strftime("%Y-%m-%d")].append((dt.hour, float(tm2m)))
    return dict(by_date)


def daily_mean(readings: list[tuple[int, float]]) -> dict | None:
    """한 날의 6 시점 → 일평균 (min+max)/2. 결측 정책: 한쪽 통째면 None."""
    morning = [t for h, t in readings if 4 <= h <= 6]
    afternoon = [t for h, t in readings if 14 <= h <= 16]
    if not morning or not afternoon:
        return None
    tmin = min(morning)
    tmax = max(afternoon)
    return {
        "tmin": round(tmin, 2),
        "tmax": round(tmax, 2),
        "tmean": round((tmin + tmax) / 2, 2),
        "n_morning": len(morning),
        "n_afternoon": len(afternoon),
        "n_total": len(morning) + len(afternoon),
    }


def daily_per_station(obsid: int) -> dict[str, dict]:
    """한 관측소의 모든 날 일평균."""
    raw = read_station_jsonl(obsid)
    return {date: daily_mean(readings) for date, readings in raw.items()}


def site_average(stations_daily: dict[int, dict[str, dict]]
                 ) -> dict[str, dict]:
    """6 관측소 일평균 → 임지(보은) 일평균."""
    by_date: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    for obsid, daily in stations_daily.items():
        for date, vals in daily.items():
            if vals is not None:
                by_date[date].append((obsid, vals))

    result: dict[str, dict] = {}
    for date, sv in by_date.items():
        n = len(sv)
        result[date] = {
            "tmean": round(sum(v["tmean"] for _, v in sv) / n, 2),
            "tmin": round(sum(v["tmin"] for _, v in sv) / n, 2),
            "tmax": round(sum(v["tmax"] for _, v in sv) / n, 2),
            "n_stations": n,
            "stations": ",".join(sorted(STATIONS[obsid] for obsid, _ in sv)),
        }
    return result


def monthly_aggregate(site_daily: dict[str, dict]) -> dict[str, dict]:
    """임지 일평균 → 월별 통계."""
    by_month: dict[str, list[dict]] = defaultdict(list)
    for date, vals in site_daily.items():
        by_month[date[:7]].append(vals)

    result = {}
    for month, days in by_month.items():
        n = len(days)
        result[month] = {
            "tmean": round(sum(d["tmean"] for d in days) / n, 2),
            "tmin": round(sum(d["tmin"] for d in days) / n, 2),
            "tmax": round(sum(d["tmax"] for d in days) / n, 2),
            "n_days": n,
            "avg_n_stations": round(
                sum(d["n_stations"] for d in days) / n, 2
            ),
        }
    return result


def annual_aggregate(site_daily: dict[str, dict]) -> dict[int, dict]:
    """임지 일평균 → 연 통계 (climate_correct 입력)."""
    by_year: dict[int, list[dict]] = defaultdict(list)
    for date, vals in site_daily.items():
        by_year[int(date[:4])].append(vals)

    result = {}
    for year, days in by_year.items():
        n = len(days)
        n_full = sum(1 for d in days if d["n_stations"] == 6)
        result[year] = {
            "tmean": round(sum(d["tmean"] for d in days) / n, 2),
            "tmin": round(sum(d["tmin"] for d in days) / n, 2),
            "tmax": round(sum(d["tmax"] for d in days) / n, 2),
            "n_days": n,
            "n_days_full": n_full,
            "n_days_partial": n - n_full,
        }
    return result


def save_daily(site_daily: dict[str, dict], path: Path):
    """일별 csv 저장 — date 기준 정렬."""
    cols = ["date", "tmean", "tmin", "tmax", "n_stations", "stations"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for date in sorted(site_daily.keys()):
            v = site_daily[date]
            w.writerow([date, v["tmean"], v["tmin"], v["tmax"],
                        v["n_stations"], v["stations"]])


def save_monthly(monthly: dict[str, dict], path: Path):
    """월별 csv 저장."""
    cols = ["month", "tmean", "tmin", "tmax", "n_days", "avg_n_stations"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for month in sorted(monthly.keys()):
            v = monthly[month]
            w.writerow([month, v["tmean"], v["tmin"], v["tmax"],
                        v["n_days"], v["avg_n_stations"]])


def save_annual(annual: dict[int, dict], path: Path):
    """연별 csv 저장 — climate_correct 입력."""
    cols = ["year", "tmean", "tmin", "tmax",
            "n_days", "n_days_full", "n_days_partial"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for year in sorted(annual.keys()):
            v = annual[year]
            w.writerow([year, v["tmean"], v["tmin"], v["tmax"],
                        v["n_days"], v["n_days_full"], v["n_days_partial"]])


def main():
    print("=" * 60)
    print("🌤  산악기상 전처리 — 보은 6 관측소 → 임지 통계 csv")
    print("=" * 60)

    # 1) 관측소별 일평균
    print("\n[1/4] 관측소별 일평균...")
    all_daily = {}
    for obsid, name in STATIONS.items():
        daily = daily_per_station(obsid)
        valid = sum(1 for v in daily.values() if v is not None)
        all_daily[obsid] = daily
        print(f"  [{obsid}] {name:6}: {valid:,}/{len(daily):,}일")

    # 2) 임지 일평균
    print("\n[2/4] 임지(6관측소 평균) 일평균...")
    site = site_average(all_daily)
    print(f"  {len(site):,}일 산출")

    # 3) 월·연 집계
    print("\n[3/4] 월·연 집계...")
    monthly = monthly_aggregate(site)
    annual = annual_aggregate(site)
    print(f"  월별: {len(monthly)}개월, 연별: {len(annual)}년")

    # 4) csv 저장
    print("\n[4/4] csv 저장...")
    daily_path = OUT / "mt_weather_daily.csv"
    monthly_path = OUT / "mt_weather_monthly.csv"
    annual_path = OUT / "mt_weather_annual.csv"
    save_daily(site, daily_path)
    save_monthly(monthly, monthly_path)
    save_annual(annual, annual_path)
    print(f"  💾 {daily_path.relative_to(ROOT)}")
    print(f"  💾 {monthly_path.relative_to(ROOT)}")
    print(f"  💾 {annual_path.relative_to(ROOT)}")

    # 요약 리포트
    print("\n" + "=" * 60)
    print("✅ 전처리 완료")
    print("=" * 60)
    print(f"\n[연 통계 — climate_correct 입력 후보]")
    print(f"  {'year':6} {'tmean':>7} {'tmin':>7} {'tmax':>7} "
          f"{'n_days':>7} {'full':>7} {'partial':>8}")
    for year in sorted(annual.keys()):
        a = annual[year]
        print(f"  {year:<6} {a['tmean']:>7} {a['tmin']:>7} "
              f"{a['tmax']:>7} {a['n_days']:>7} "
              f"{a['n_days_full']:>7} {a['n_days_partial']:>8}")

    full_years = [y for y, a in annual.items() if a["n_days"] >= 360]
    if full_years:
        avg = sum(annual[y]["tmean"] for y in full_years) / len(full_years)
        print(f"\n[참고] 완전한 해({full_years}) 평균 기온: {avg:.2f}°C")
        print(f"       청주 평년 12.5°C - 고도보정(0.6×3.59) ≈ 10.3°C")
        print(f"       min+max/2 편향으로 실측이 약 1°C 높게 나옴 (정상)")


if __name__ == "__main__":
    main()