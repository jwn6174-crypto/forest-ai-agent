"""
test_keys.py
.env 파일에서 API 키가 잘 읽히는지 확인하는 스크립트
"""

import os
from dotenv import load_dotenv

# .env 파일 읽어들이기
load_dotenv()

# 환경변수에서 키 가져오기
data_go_kr_key = os.getenv("DATA_GO_KR_KEY")
law_oc = os.getenv("LAW_OC")
vworld_key = os.getenv("VWORLD_KEY")
gee_account = os.getenv("GEE_ACCOUNT")

# 결과 출력 (보안: 키 일부만 표시)
def mask(key, head=4, tail=4):
    """키를 앞 4글자 + ... + 뒤 4글자만 보여줌"""
    if not key:
        return "❌ 못 읽음"
    if len(key) <= head + tail:
        return key  # OC처럼 짧은 건 그대로
    return f"{key[:head]}...{key[-tail:]} (총 {len(key)}자)"

print("===== API 키 로드 테스트 =====")
print(f"DATA_GO_KR_KEY: {mask(data_go_kr_key)}")
print(f"LAW_OC:         {mask(law_oc)}")
print(f"VWORLD_KEY:     {mask(vworld_key)}")
print(f"GEE_ACCOUNT:    {gee_account}")
print()

if all([data_go_kr_key, law_oc, vworld_key, gee_account]):
    print("✅ 모든 키가 정상 로드됨!")
else:
    print("⚠️  일부 키가 비어 있음. .env 파일 확인 필요.")