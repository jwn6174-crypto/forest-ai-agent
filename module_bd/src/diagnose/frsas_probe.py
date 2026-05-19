"""
frsas_probe.py — 산림자원통계: 실제 수치 조회 경로 탐색 (2차).
selectStatList1 외 다른 엔드포인트 + 다른 파라미터 조합 시도.
"""
import os, json, requests
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / ".env")
KEY = os.getenv("DATA_GO_KR_KEY")
BASE = "http://apis.data.go.kr/1400000/frsas1"

# ── 진단 A: selectStatList1 응답에 통계별 totalCount 있나 재확인 ──
print("=" * 60)
print("[A] 임가경제조사 목록 — 각 통계의 totalCount 필드 확인")
print("=" * 60)
r = requests.get(f"{BASE}/selectStatList1",
                 params={"serviceKey": KEY, "pageNo": 1, "numOfRows": 3,
                         "clsscId": "mntHouseEcono"}, timeout=20)
data = r.json()
for row in data.get("data", []):
    print(f"   seq={row.get('statSeq')} {row.get('statNm')}")
    print(f"      전체 필드: {list(row.keys())}")

# ── 진단 B: 다른 엔드포인트 이름 추정 시도 ──
print("\n" + "=" * 60)
print("[B] selectStatList1 외 엔드포인트 시도")
print("=" * 60)
# selectStatList1 이 목록이면, 상세는 selectStat... 패턴일 것
endpoints = [
    "selectStatList",        # 1 없는 버전
    "selectStatData1",       # 데이터
    "selectStatDetail1",     # 상세
    "selectStatInfo1",
    "selectStat1",
    "getStatData1",
]
seq = "4132"  # 주요지표(월별지표)
for ep in endpoints:
    url = f"{BASE}/{ep}"
    p = {"serviceKey": KEY, "pageNo": 1, "numOfRows": 3,
         "clsscId": "mntHouseEcono", "statSeq": seq}
    try:
        resp = requests.get(url, params=p, timeout=15)
        body = resp.text[:200].replace("\n", " ")
        print(f"   /{ep}: HTTP {resp.status_code} — {body}")
    except Exception as e:
        print(f"   /{ep}: 에러 {e}")

# ── 진단 C: selectStatList1 에 statSeq 외 다른 파라미터명 ──
print("\n" + "=" * 60)
print("[C] selectStatList1 + 다양한 파라미터명")
print("=" * 60)
for pname in ["statSeq", "stat_seq", "seq", "statNo", "statId",
              "id", "dataSeq", "statClsscId"]:
    p = {"serviceKey": KEY, "pageNo": 1, "numOfRows": 3,
         "clsscId": "mntHouseEcono", pname: seq}
    try:
        d = requests.get(f"{BASE}/selectStatList1", params=p,
                         timeout=15).json()
        tc = d.get("totalCount")
        n = len(d.get("data", []))
        print(f"   {pname}={seq}: totalCount={tc}, 행수={n}")
    except Exception as e:
        print(f"   {pname}: 에러 {e}")

# ── 진단 D: 응답 raw 전체 (숨은 필드 확인) ──
print("\n" + "=" * 60)
print("[D] selectStatList1 raw 응답 (앞 800자)")
print("=" * 60)
r = requests.get(f"{BASE}/selectStatList1",
                 params={"serviceKey": KEY, "pageNo": 1, "numOfRows": 2,
                         "clsscId": "mntHouseEcono"}, timeout=20)
print(r.text[:800])