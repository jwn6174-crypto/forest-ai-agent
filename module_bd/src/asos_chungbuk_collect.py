"""
asos_chungbuk_collect.py — 충북 5 ASOS 관측소 1991-2020 일자료 수집.

목적:
  · 충북 + 추풍령 5 관측소 30년 평년 (시군별 공간 변동)
  · 보은 (226) 이미 수집됨 (asos_226_1991_2020.jsonl)
  · 추가 4개 수집 (131 청주, 127 충주, 221 제천, 135 추풍령)

관측소:
  · 131 청주 (북서, 평지, 36.64°N 127.45°E)
  · 127 충주 (북, 평지, 36.97°N 127.95°E)
  · 221 제천 (북동, 평지, 37.16°N 128.19°E)
  · 226 보은 (중남, 평지 36.49°N 127.74°E) ← 기존
  · 135 추풍령 (남, 산악 36.22°N 127.99°E, 경북 김천)

출력:
  · data/raw/asos/asos_<stnId>_1991_2020.jsonl × 4 새 파일
"""
import os
import json
import time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "module_bd" / "data" / "raw" / "asos"


def load_env():
    env_path = ROOT / ".env"
    env = {}
    if env_path.exists():
        with open(env_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip()
    return env


API_KEY = load_env().get('DATA_GO_KR_KEY')

# 충북 + 추풍령 5 관측소
STATIONS = [
    (131, '청주'),
    (127, '충주'),
    (221, '제천'),
    (135, '추풍령'),
    # 226 보은 이미 수집됨
]

START_YEAR = 1991
END_YEAR = 2020
URL = "https://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList"


def fetch_year(stn_id, year):
    params = {
        'serviceKey': API_KEY,
        'stnIds': str(stn_id),
        'startDt': f'{year}0101',
        'endDt': f'{year}1231',
        'dataType': 'JSON',
        'pageNo': '1',
        'numOfRows': '400',
        'dataCd': 'ASOS',
        'dateCd': 'DAY',
    }
    try:
        r = requests.get(URL, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        if data['response']['header']['resultCode'] != '00':
            return None, f"API: {data['response']['header']['resultMsg']}"
        items = data['response']['body']['items']['item']
        if isinstance(items, dict):
            items = [items]
        return items, None
    except Exception as e:
        return None, f"실패: {e}"


def main():
    if not API_KEY:
        print("⚠ DATA_GO_KR_KEY 없음")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"충북 4 ASOS + 추풍령 수집 (1991-2020, 30년)")
    print("=" * 70)

    total_records = 0
    for stn_id, name in STATIONS:
        out_path = OUT_DIR / f"asos_{stn_id}_1991_2020.jsonl"
        if out_path.exists():
            print(f"\n  {stn_id} {name}: 이미 존재 ({out_path.stat().st_size // 1024} KB). 건너뜀.")
            continue

        print(f"\n  {stn_id} {name}:")
        count = 0
        with open(out_path, 'w', encoding='utf-8') as f:
            for year in range(START_YEAR, END_YEAR + 1):
                items, err = fetch_year(stn_id, year)
                if items is None:
                    print(f"    {year}: 실패 ({err})")
                    continue
                for item in items:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
                count += len(items)
                # 진행 표시
                if year % 5 == 0:
                    print(f"    {year}: {len(items)}일 (누적 {count})")
                time.sleep(0.3)

        size_kb = out_path.stat().st_size // 1024
        print(f"  ✓ {out_path.name}: {count} 일, {size_kb} KB")
        total_records += count

    print(f"\n{'=' * 70}")
    print(f"수집 완료. 총 {total_records:,} 행 추가.")
    print(f"  파일: data/raw/asos/asos_<stnId>_1991_2020.jsonl × {len(STATIONS)}")


if __name__ == "__main__":
    main()