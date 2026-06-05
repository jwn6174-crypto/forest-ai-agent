"""
asos_chungbuk_probe.py — 충북 ASOS 관측소 진단.

목적:
  · ASOS 관측소 목록 추출 (충북 시군)
  · 가능한 시군별 평년 수집 준비

기상청 ASOS 관측소 ID (한국 표준):
  100s: 강원
  200s: 충북, 충남 (226 보은)
  
충북 후보 (추정):
  · 226 보은 (확정)
  · 131 청주
  · 127 충주
  · 221 추풍령
  · 281 제천
"""
import os
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[3]


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

# 충북 ASOS 후보 (한국 표준)
CANDIDATES = [
    (131, '청주'),
    (127, '충주'),
    (221, '추풍령'),
    (226, '보은'),  # 확인용
    (281, '제천'),
    (272, '영동'),
    (135, '추풍령'),  # 다른 번호
]


def probe(stn_id, name):
    """한 관측소 시험 호출 (1일치)."""
    url = "https://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList"
    params = {
        'serviceKey': API_KEY,
        'stnIds': str(stn_id),
        'startDt': '20200101',
        'endDt': '20200101',
        'dataType': 'JSON',
        'pageNo': '1',
        'numOfRows': '5',
        'dataCd': 'ASOS',
        'dateCd': 'DAY',
    }

    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            return f"HTTP {r.status_code}"
        data = r.json()
        result_code = data['response']['header']['resultCode']
        if result_code != '00':
            return f"API: {data['response']['header']['resultMsg']}"
        items = data['response']['body']['items']
        if not items or 'item' not in items:
            return "데이터 없음"
        item = items['item']
        if isinstance(item, list):
            item = item[0]
        actual_name = item.get('stnNm', '?')
        avg_ta = item.get('avgTa', '?')
        return f"{actual_name} (avgTa={avg_ta})"
    except Exception as e:
        return f"ERROR: {e}"


def main():
    if not API_KEY:
        print("⚠ DATA_GO_KR_KEY 없음")
        return

    print("=" * 60)
    print("충북 ASOS 관측소 진단")
    print("=" * 60)
    print()
    print(f"{'stnId':<7} {'예상':<8} {'결과':<50}")
    print('-' * 70)
    for stn_id, name in CANDIDATES:
        result = probe(stn_id, name)
        print(f"{stn_id:<7} {name:<8} {result}")


if __name__ == "__main__":
    main()