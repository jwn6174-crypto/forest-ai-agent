"""
mt_weather_collect.py
가이드 §2.3 — 산악기상 시계열 수집 (보은 6 관측소).

수집 범위: 2022-01-01 ~ 어제 (산악기상관측망 가용 전 기간)
시점: 하루 6개 (새벽 04/05/06 + 오후 14/15/16)
  → 일평균 = (새벽 최저 + 오후 최고) / 2  [기상학 표준 정의]
  → 새벽·오후 각 3개는 최저·최고 시각이 빗나가는 것 보완

출력: data/raw/mt_weather/obs_<obsid>.jsonl  (관측소별 원본)
  - 한 줄 = 한 시점 관측 (재실행 시 이미 받은 날 건너뜀)

이 스크립트는 *수집만* 한다. 일평균·연통계는 mt_weather_process.py.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

from mt_weather_api import fetch_mt_weather, BOEUN_STATIONS

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "module_bd" / "data" / "raw" / "mt_weather"

# 수집 설정
START_DATE = datetime(2022, 1, 1)
END_DATE = datetime.now() - timedelta(days=1)  # 어제까지
HOURS = ["04", "05", "06", "14", "15", "16"]   # 새벽 3 + 오후 3
SLEEP_SEC = 0.05   # TPS 30 제한 → 호출 간 최소 간격
SAVE_EVERY = 200   # N 시점마다 디스크 flush


def _load_done(jsonl_path: Path) -> set:
    """이미 받은 (날짜, 시각) 키 집합 — 재실행 시 건너뛰기용."""
    done = set()
    if not jsonl_path.exists():
        return done
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
                done.add(rec["tm_req"])
            except (json.JSONDecodeError, KeyError):
                continue
    return done


def _extract_item(result: dict) -> dict:
    """API 응답에서 item dict 추출. 없으면 None."""
    items = result.get("response", {}).get("body", {}).get("items", "")
    if not items or items == "":
        return None
    item = items.get("item", None)
    if item is None:
        return None
    if isinstance(item, list):
        return item[0] if item else None
    return item


class RateLimitHit(Exception):
    """일일 호출 한도(429) 도달 — 수집 중단 신호."""
    pass


def collect_station(obsid: int, info: dict):
    """관측소 1곳의 전체 기간 수집. 429 만나면 RateLimitHit 발생."""
    jsonl_path = OUT_DIR / f"obs_{obsid}.jsonl"
    done = _load_done(jsonl_path)
    print(f"\n[{obsid}] {info['name']} (고도 {info['alt']}m)")
    print(f"   이미 받은 시점: {len(done):,}개")

    buffer = []
    n_ok, n_empty = 0, 0
    day = START_DATE

    def _flush(f):
        for r in buffer:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        f.flush()
        buffer.clear()

    with open(jsonl_path, "a", encoding="utf-8") as f:
        while day <= END_DATE:
            ymd = day.strftime("%Y%m%d")
            for hh in HOURS:
                tm = ymd + hh + "00"
                if tm in done:
                    continue
                try:
                    result = fetch_mt_weather(obsid=obsid, tm=tm, num_of_rows=1)
                except Exception as e:
                    msg = str(e)
                    # 429 = 일일 한도. 기록하지 않고 즉시 중단.
                    if "429" in msg or "Too Many Requests" in msg:
                        _flush(f)
                        print(f"   ⏸  429 한도 도달 — {ymd} {hh}시에서 중단")
                        print(f"      이번 실행 수집: ok {n_ok:,} / 빈 {n_empty:,}")
                        raise RateLimitHit()
                    # 그 외 에러는 기록 후 계속 (일시적 네트워크 등)
                    buffer.append({"tm_req": tm, "obsid": obsid,
                                   "ok": False, "error": msg})
                    time.sleep(SLEEP_SEC)
                    continue

                item = _extract_item(result)
                rec = {"tm_req": tm, "obsid": obsid, "ok": item is not None}
                if item is not None:
                    rec["data"] = item
                    n_ok += 1
                else:
                    n_empty += 1
                buffer.append(rec)

                time.sleep(SLEEP_SEC)

                if len(buffer) >= SAVE_EVERY:
                    _flush(f)
                    print(f"   ... {ymd} 진행 중 (ok {n_ok:,} / 빈 {n_empty:,})")

            day += timedelta(days=1)

        _flush(f)

    print(f"   ✅ 완료: ok {n_ok:,} / 빈 {n_empty:,}")
    return n_ok, n_empty


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    total_days = (END_DATE - START_DATE).days + 1
    total_calls = total_days * len(BOEUN_STATIONS) * len(HOURS)
    est_min = total_calls * SLEEP_SEC / 60

    print("=" * 60)
    print("🌤  산악기상 시계열 수집 — 보은 6 관측소")
    print("=" * 60)
    print(f"   기간: {START_DATE:%Y-%m-%d} ~ {END_DATE:%Y-%m-%d} ({total_days:,}일)")
    print(f"   관측소: {len(BOEUN_STATIONS)}개")
    print(f"   시점: 하루 {len(HOURS)}개 ({'/'.join(HOURS)})")
    print(f"   예상 호출: {total_calls:,}회")
    print(f"   예상 시간: 약 {est_min:.0f}분")
    print(f"   저장: {OUT_DIR.relative_to(ROOT)}/obs_<obsid>.jsonl")
    print("   * 중단되어도 재실행하면 이어받음")
    print("=" * 60)

    grand_ok, grand_empty = 0, 0
    hit_limit = False
    for obsid, info in BOEUN_STATIONS.items():
        try:
            ok, empty = collect_station(obsid, info)
            grand_ok += ok
            grand_empty += empty
        except RateLimitHit:
            hit_limit = True
            break

    print()
    print("=" * 60)
    if hit_limit:
        print("⏸  오늘 한도 도달 — 수집 일시 중단")
        print(f"   이번 실행 수집: ok {grand_ok:,} / 빈 {grand_empty:,}")
        print("   → 자정(한도 리셋) 이후 같은 명령으로 재실행하면 이어받음")
    else:
        print("✅ 전체 수집 완료")
        print(f"   성공 {grand_ok:,} / 빈 응답 {grand_empty:,}")
        print("   다음: mt_weather_process.py 로 일평균·연통계 산출")
    print("=" * 60)


if __name__ == "__main__":
    main()