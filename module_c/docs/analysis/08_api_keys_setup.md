# API 키 발급 가이드 — 희도(zxsa0716@kookmin.ac.kr) 본인 명의

> 정우(jwn6174)가 이미 발급해서 쓰는 키들을 *희도 본인 명의로* 추가 발급.
> 이유: (1) 각 API 의 일일 한도 분리 사용 (2) 정우 휴학·졸업 후에도 동작 (3) PR 시 .env.example 에 author=heedo 명시 가능.

**작성일**: 2026-05-19 (Day 5)
**근거**: 정우 README "DATA_GO_KR_KEY, LAW_OC, VWORLD_KEY 등" + 정우 `.gitignore` `.env` 제외

---

## 0. 최종 .env 템플릿 (목표)

```bash
# E:\forest_ai\.env (절대 git 에 올리지 말 것 — .gitignore 처리)

# 정부 통합 OpenAPI (data.go.kr) — Tier 1
DATA_GO_KR_KEY=...your_decoded_key...
DATA_GO_KR_KEY_ENCODED=...your_encoded_key...

# 국토교통부 공간정보 (VWorld) — PNU/주소 → polygon
VWORLD_KEY=...your_vworld_key...

# 통계청 통계자료 (KOSIS) — 임가경제·임산물 시계열
KOSIS_KEY=...your_kosis_key...

# 법제처 국가법령정보 (LAW)
LAW_OC=...your_law_oc...

# NASA Earthdata (선택 — 모듈 A 협업 시)
EARTHDATA_USER=zxsa716
EARTHDATA_PASS=...

# Google Earth Engine (선택)
GEE_PROJECT=...

# 한국연구재단 NRF (참고만)
NRF_LAB=clim_lab
NRF_GRANT=2022S1A5A8051754
```

---

## 1. data.go.kr (공공데이터포털) — **P0 가장 중요**

### 1.1 회원가입
- URL: `https://www.data.go.kr/`
- 절차: 일반회원 → 이메일 인증 (zxsa0716@kookmin.ac.kr)
- 1분 내 완료

### 1.2 활용 신청할 API 목록 (6개 일괄)

| # | API 명 | URL | 용도 | 승인 |
|---|---|---|---|---|
| 1 | 국립산림과학원 산림자원조사 | data.go.kr/data/15080832 | NFI 통계 | 즉시 |
| 2 | 산림청 임상도 1:25,000 | data.go.kr/data/3045619 | 임상도 SHP | 즉시 (fileData) |
| 3 | NFI 임분조사 마이크로데이터 | data.go.kr/data/15122903 | NFI 4,500 표본점 | 즉시 (fileData) |
| 4 | 한국산림복지진흥원 임산물 소득조사 | data.go.kr/data/3044575 | NTFP 데이터 ⭐ | 즉시 (fileData) |
| 5 | 한국거래소 배출권 시세 | data.go.kr/data/15094805 | KAU 일별 | 1-2일 |
| 6 | 통계청 KOSIS 통계 | data.go.kr/data/15127763 | 임가경제 | 1-2일 |

### 1.3 신청 방법
1. 각 페이지 → "활용신청" 버튼
2. 사용 목적: "학부생 공모전 (NRF 한국연구재단 일반공동연구 CLIM Lab 산하) 충북 보은 산림 NPV 시뮬레이션"
3. 첨부: 없음
4. 승인 후 **마이페이지 → 인증키 발급**

### 1.4 키 형식
```bash
# 한 계정에 *원본 키 1개* + *URL 인코딩 키 1개* 둘 다 발급됨
DATA_GO_KR_KEY="6h7v8...본인 키 (decoded)..."
DATA_GO_KR_KEY_ENCODED="6h7v8...%2B...본인 키 (encoded)..."
# OpenAPI 호출 시: encoded 사용. fileData 다운로드: decoded.
```

### 1.5 정우 활용 예 참고
정우 `module_bd/src/kau_api.py`, `legal_api.py` 가 `os.environ["DATA_GO_KR_KEY"]` 호출.
내 코드도 동일 변수명 사용.

---

## 2. VWorld (국토교통부 공간정보) — **P0**

### 2.1 발급
- URL: `https://www.vworld.kr/v4po_main.do`
- 메뉴: 오픈API → 인증키 발급
- 회원가입 → 인증키 신청 → "사용 도메인" 입력 (개발 단계: `localhost` + `127.0.0.1`)
- **즉시 승인** (자동)

### 2.2 일일 한도
- 무료: **사실상 제한 없음** (수만건/일 가능)
- 제한 발생 시 도메인 추가 또는 키 추가 발급

### 2.3 키 형식
```bash
VWORLD_KEY="ABC...DEF12345"  # 단일 문자열
```

### 2.4 활용 예
```python
import requests, os
def pnu_to_polygon(pnu):
    url = "http://api.vworld.kr/req/data"
    params = {
        "key": os.environ["VWORLD_KEY"],
        "service": "data", "version": "2.0",
        "request": "GetFeature",
        "data": "LP_PA_CBND_BUBUN",  # 연속지적도
        "attrFilter": f"pnu:=:{pnu}",
        "geometry": "true", "geomFilter": "BOX(126,33,131,39)",
        "format": "json",
    }
    return requests.get(url, params=params).json()
```

### 2.5 정우 활용 확인
정우 `test_vworld.py` (2.1KB) 가 동일 패턴 사용 추정. 내 키로 같은 코드 동작 가능.

---

## 3. KOSIS (통계청) — **P1**

### 3.1 발급
- URL: `https://kosis.kr/openapi/index/index.jsp`
- 회원가입 → 마이페이지 → API 인증키 발급
- 즉시 발급

### 3.2 주의사항 (정우 5/18 KOSIS probe 결과)
**정우 발견**: KOSIS 임가경제조사 (DT_143F002) 는 **도(道) 단위만 제공**, ha 환산 안 됨.
→ 정우 diagnose 결론: "임가소득 미제공". **KOSIS 단독 사용 부족**.

### 3.3 대안 (경영자 D13 권고)
NTFP 200만원/ha/yr 가정의 데이터 출처:
- **산림청 「임산물 생산조사」 연보** — kfri.go.kr → 통합자료실 (HWP/PDF)
- **충북농업기술원 임업기술센터 보은지소** — 직접 연락 또는 보고서
- **산림조합중앙회 임산물 유통정보** — nfck.or.kr 게시판
- KOSIS는 *보조 시계열* 만 사용

### 3.4 키 형식
```bash
KOSIS_KEY="MA4yNDA1MTk..."  # base64-like
```

---

## 4. 법제처 (open.law.go.kr) — **P1**

### 4.1 발급
- URL: `https://open.law.go.kr/LSO/main.do`
- 회원가입 → 활용신청
- **1-2일 승인 대기**

### 4.2 활용 (정우 이미 사용 중)
정우 `module_bd/src/legal_api.py` 가 활용. 별표 3 (기준벌기령) 자동 갱신.
내가 새로 발급 가능, 또는 정우 키 재활용도 OK (백업).

### 4.3 키 형식
```bash
LAW_OC="zxsa0716"  # 정우는 jwn6174. OC = 본인 ID
```

---

## 5. (선택) NASA Earthdata — 모듈 A 협업 시 P2

- URL: `https://urs.earthdata.nasa.gov/`
- 가입 → ID 발급
- GEDI L4A, SMAP, MODIS 다운로드용
- 본인 메모리에 이미 등록됨: `EARTHDATA zxsa716` (Tanager 프로젝트)
- 그대로 재활용 가능

---

## 6. (선택) Google Earth Engine — 모듈 A 협업 시 P2

- URL: `https://code.earthengine.google.com/`
- Google 계정 + Cloud Project 등록 → 비상업 연구용 무료 신청
- 즉시-1일 승인
- 위성 데이터 (Sentinel-2/1, ALOS-2, GEDI L4A) 모두 GEE 에서 호출 가능

---

## 7. 키 보관 + 보안

### 7.1 .env 파일 위치
```
E:\forest_ai\.env                  ← 로컬 (gitignore)
E:\forest_ai\.env.example         ← 더미 (commit OK)
```

### 7.2 .env.example 템플릿 (정우 PR 시 추가)
```bash
# 본인 키로 채우세요
DATA_GO_KR_KEY=
DATA_GO_KR_KEY_ENCODED=
VWORLD_KEY=
KOSIS_KEY=
LAW_OC=
```

### 7.3 Python 로딩
```python
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
import os
key = os.environ["DATA_GO_KR_KEY"]
```

### 7.4 절대 하지 말 것
- `.env` 를 GitHub 에 commit (정우 .gitignore 가 막아주지만 한 번 사고면 키 revoke)
- 키를 코드에 하드코드
- 키를 Slack/Discord 평문 공유

---

## 8. Day 6 우선순위 (오늘 발급할 것)

**최우선 (Day 6 오전)**:
1. data.go.kr 회원가입 + 4개 fileData API 활용신청 (1번/3번/4번 즉시 승인)
2. VWorld 인증키 발급 (즉시)

**중간 (Day 6 오후 - 1-2일 대기)**:
3. data.go.kr OpenAPI 5번/6번 활용신청 (KAU·KOSIS)
4. KOSIS 별도 키 발급
5. 법제처 OC 발급

**선택 (W3 이후)**:
6. NASA Earthdata (재활용 가능)
7. Google Earth Engine

---

## 9. 첫 호출 sanity check 코드

`module_c/scripts/test_my_keys.py` (정우 `test_keys.py` 모방):

```python
"""희도 본인 키 발급 직후 sanity check."""
import os, requests
from dotenv import load_dotenv
load_dotenv()

def test_data_go_kr():
    """공공데이터포털 OpenAPI 호출 1개."""
    key = os.environ.get("DATA_GO_KR_KEY_ENCODED")
    assert key, "DATA_GO_KR_KEY_ENCODED 미설정"
    # 산림자원통계 호출 1건
    url = "http://apis.data.go.kr/1400000/service/forestKfdProductService"
    r = requests.get(url, params={"serviceKey": key, "pageNo": 1, "numOfRows": 1})
    print(f"data.go.kr: {r.status_code}, {r.text[:100]}")

def test_vworld():
    """VWorld PNU 1건 조회."""
    key = os.environ.get("VWORLD_KEY")
    assert key, "VWORLD_KEY 미설정"
    url = "http://api.vworld.kr/req/address"
    r = requests.get(url, params={
        "service": "address", "request": "getCoord",
        "key": key, "address": "충북 보은군 보은읍",
        "type": "PARCEL", "format": "json",
    })
    print(f"VWorld: {r.status_code}, {r.json().get('response', {}).get('status')}")

if __name__ == "__main__":
    test_data_go_kr()
    test_vworld()
```

---

## 변경 이력
- 2026-05-19 Day 5 — 4 P0/P1 + 3 선택 API 발급 가이드 작성
