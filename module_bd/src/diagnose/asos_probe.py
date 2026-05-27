"""
asos_probe.py — 기상청 ASOS 일자료 API 진단.

목적:
  · data.go.kr 의 ASOS 일자료 API 작동 확인
  · 보은 ASOS (관측소 226) 1주일치 데이터 시험 호출
  · 정상 작동 → asos_collect.py 본격 작성

API 정보:
  · 기상청_지상(종관, ASOS) 일자료 조회서비스
  · endpoint: https://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList
  · 인증키: data.go.kr 마스터키 (.env 의 DATA_GO_KR_KEY)
"""
import os
import sys
from pathlib import Path
import requests
import json

ROOT = Path(__file__).resolve().parents[3]


def load_env():
    """우리 프로젝트 .env 로드 (간이)."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return {}
    env = {}
    with open(env_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip()
    return env


def main():
    env = load_env()
    key = env.get('DATA_GO_KR_KEY')

    if not key:
        print("⚠ DATA_GO_KR_KEY 못 찾음")
        return

    print(f"✓ 인증키 로드: {key[:20]}...{key[-8:]}")

    # 시험 호출 — 보은 ASOS 2020년 1월 1주일
    url = "https://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList"
    params = {
        'serviceKey': key,
        'stnIds': '226',  # 보은
        'startDt': '20200101',
        'endDt': '20200107',  # 1주일
        'dataType': 'JSON',
        'pageNo': '1',
        'numOfRows': '10',
        'dataCd': 'ASOS',
        'dateCd': 'DAY',
    }

    print(f"\n호출 시작: 보은 ASOS (226), 2020-01-01 ~ 01-07")
    print(f"URL: {url}")
    print()

    try:
        r = requests.get(url, params=params, timeout=30)
        print(f"HTTP 상태: {r.status_code}")
        print(f"응답 길이: {len(r.text)} bytes")
        print()
    except Exception as e:
        print(f"⚠ 요청 실패: {e}")
        return

    # 응답 분석
    print("=" * 70)
    print("응답 본문 (처음 1000자):")
    print("=" * 70)
    print(r.text[:1000])
    print()

    # JSON 파싱 시도
    print("=" * 70)
    print("JSON 파싱:")
    print("=" * 70)
    try:
        data = r.json()
        print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
    except Exception as e:
        print(f"⚠ JSON 파싱 실패: {e}")
        print("→ 응답이 XML 형식일 수 있음 (활용 신청 안 됨 시 흔함)")


if __name__ == "__main__":
    main()