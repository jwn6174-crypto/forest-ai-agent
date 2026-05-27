"""
asos_collect.py — 보은 ASOS 일자료 1991-2020 수집.

목적:
  · 기상청 ASOS API (data.go.kr/15059093)
  · 보은 관측소 226 (보은읍, 평지)
  · 1991-01-01 ~ 2020-12-31 (30년 평년)
  · 일 단위: 평균/최저/최고 기온, 강수, 습도, 이슬점 등

사용 변수 (climate_correct 입력):
  · avgTa: 평균기온 → temp_anomaly_30y, gdd_cum
  · sumRn: 일 강수량 → prcp_anomaly_30y
  · avgRhm: 평균 상대습도 → VPD 계산
  · avgTd: 이슬점 온도 → VPD 계산

출력:
  · data/raw/asos/asos_226_1991_2020.jsonl (~11,000 행)

호출 패턴 (mt_weather_collect.py 재사용):
  · 한 호출 = 한 해 (numOfRows=400)
  · 30 호출 (1991, 1992, ..., 2020)
  · API 한도 여유 (10,000건/일 한도)

실행: python module_bd/src/asos_collect.py
"""
import os
import json
import time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "module_bd" / "data" / "raw" / "asos"
OUT_PATH = OUT_DIR / "asos_226_1991_2020.jsonl"

# .env 로드
def load_env():
    env_path = ROOT / ".env"
    env = {}
    if env_path.exists():
        with open(env_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip()
    return env

ENV = load_env()
API_KEY = ENV.get('DATA_GO_KR_KEY')

# 보은 ASOS
STN_ID = '226'
STN_NAME = '보은'
START_YEAR = 1991
END_YEAR = 2020

URL = "https://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList"


def fetch_year(year):
    """한 해 (365 또는 366일) 일자료 → list of dict."""
    params = {
        'serviceKey': API_KEY,
        'stnIds': STN_ID,
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
    except Exception as e:
        return None, f"요청 실패: {e}"

    try:
        result_code = data['response']['header']['resultCode']
        if result_code != '00':
            return None, f"API 에러: {data['response']['header']['resultMsg']}"

        items = data['response']['body']['items']['item']
        if isinstance(items, dict):  # 1개 행이면 dict 로 옴
            items = [items]
        return items, None
    except (KeyError, TypeError) as e:
        return None, f"파싱 에러: {e}"


def main():
    if not API_KEY:
        print("⚠ DATA_GO_KR_KEY 못 찾음")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"보은 ASOS (226) 일자료 수집 — {START_YEAR} ~ {END_YEAR} ({END_YEAR - START_YEAR + 1}년)")
    print("=" * 70)

    if OUT_PATH.exists():
        size_kb = OUT_PATH.stat().st_size / 1024
        print(f"\n⚠ 출력 파일 이미 존재: {OUT_PATH.name} ({size_kb:.0f} KB)")
        ans = input("덮어쓰기? (y/N): ")
        if ans.lower() != 'y':
            print("취소. 기존 파일 유지.")
            return

    total_count = 0
    fail_years = []

    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        for year in range(START_YEAR, END_YEAR + 1):
            print(f"  {year}: 호출 중...", end=" ", flush=True)
            items, err = fetch_year(year)

            if items is None:
                print(f"실패 ({err})")
                fail_years.append(year)
                # 1번 재시도
                time.sleep(2)
                items, err = fetch_year(year)
                if items is None:
                    print(f"    재시도 실패. 건너뜀.")
                    continue
                else:
                    print(f"    재시도 성공")

            # jsonl 로 저장
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

            total_count += len(items)
            print(f"{len(items)} 일")

            # 호출 간격
            time.sleep(0.3)

    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"\n{'=' * 70}")
    print(f"수집 완료:")
    print(f"  총 일수: {total_count}")
    print(f"  파일: {OUT_PATH.name} ({size_kb:.0f} KB)")
    if fail_years:
        print(f"  실패 연도: {fail_years}")
    print(f"{'=' * 70}")
    print(f"\n다음: asos_features.py — 평년 산출 + anomaly 계산")


if __name__ == "__main__":
    main()