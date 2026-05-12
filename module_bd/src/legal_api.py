"""
legal_api.py
법제처 OpenAPI로 산림자원법 시행규칙 + 별표 3 (수종별 기준벌기령) 가져오기

[수행 단계]
1. 법령 검색 → MST 번호 획득
2. 법령 본문 XML 다운로드
3. 별표 3 PDF 링크 추출
4. PDF 다운로드 (별표 원본 보존)
"""

import os
import xml.etree.ElementTree as ET
import requests
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

OC = os.getenv("LAW_OC")

LAW_SEARCH_URL = "https://www.law.go.kr/DRF/lawSearch.do"
LAW_SERVICE_URL = "https://www.law.go.kr/DRF/lawService.do"

DATA_DIR = ROOT / "module_bd" / "data" / "raw" / "law_extracts"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def search_law(keyword: str):
    params = {"OC": OC, "target": "law", "type": "XML", "query": keyword, "display": "10"}
    response = requests.get(LAW_SEARCH_URL, params=params, timeout=10)
    if response.status_code != 200:
        return []
    root = ET.fromstring(response.content)
    return [
        {
            "법령일련번호": law.findtext("법령일련번호"),
            "법령명한글": law.findtext("법령명한글"),
            "시행일자": law.findtext("시행일자"),
        }
        for law in root.findall(".//law")
    ]


def fetch_law_full(mst: str):
    params = {"OC": OC, "target": "law", "type": "XML", "MST": mst}
    response = requests.get(LAW_SERVICE_URL, params=params, timeout=15)
    return response.content if response.status_code == 200 else None


def extract_byeolpyo_info(xml_content: bytes):
    """
    XML에서 모든 별표 정보 추출 (제목, 번호, PDF 링크).
    """
    root = ET.fromstring(xml_content)
    byeolpyos = []
    
    for unit in root.findall(".//별표단위"):
        info = {
            "번호": unit.findtext("별표번호", ""),
            "가지번호": unit.findtext("별표가지번호", ""),
            "구분": unit.findtext("별표구분", ""),
            "제목": (unit.findtext("별표제목") or "").strip(),
            "PDF링크": unit.findtext("별표서식PDF파일링크", ""),
            "HWP링크": unit.findtext("별표서식파일링크", ""),
            "내용": (unit.findtext("별표내용") or "").strip()[:300],
        }
        byeolpyos.append(info)
    
    return byeolpyos


def download_byeolpyo_pdf(pdf_link: str, save_name: str):
    """
    법제처가 제공하는 별표 PDF 다운로드.
    링크는 보통 상대 경로라 절대 경로로 변환 필요할 수 있음.
    """
    # 상대 경로면 https://www.law.go.kr 붙임
    if pdf_link.startswith("/"):
        url = "https://www.law.go.kr" + pdf_link
    elif not pdf_link.startswith("http"):
        url = "https://www.law.go.kr/" + pdf_link
    else:
        url = pdf_link
    
    response = requests.get(url, timeout=15)
    if response.status_code != 200:
        print(f"   ❌ PDF 다운로드 실패: HTTP {response.status_code}")
        return None
    
    pdf_path = DATA_DIR / save_name
    pdf_path.write_bytes(response.content)
    return pdf_path


if __name__ == "__main__":
    print("🌐 법제처 OpenAPI 호출 중...")
    print(f"   OC: {OC}")
    print()
    
    # Step 1: 법령 검색
    laws = search_law("산림자원의 조성 및 관리에 관한 법률 시행규칙")
    if not laws:
        print("❌ 검색 실패")
        exit(1)
    
    target = sorted(laws, key=lambda x: x["시행일자"] or "0", reverse=True)[0]
    print(f"✅ 대상: {target['법령명한글']}")
    print(f"   시행일자: {target['시행일자']}, MST: {target['법령일련번호']}")
    
    # Step 2: 법령 본문 다운로드
    print()
    print("📥 법령 본문 다운로드...")
    xml_content = fetch_law_full(target["법령일련번호"])
    if not xml_content:
        print("❌ 다운로드 실패")
        exit(1)
    
    xml_path = DATA_DIR / f"forest_law_{target['법령일련번호']}.xml"
    xml_path.write_bytes(xml_content)
    print(f"💾 XML 저장: {xml_path.name} ({len(xml_content):,} bytes)")
    
    # Step 3: 별표 목록 정리
    print()
    print("📑 별표 목록 추출 중...")
    byeolpyos = extract_byeolpyo_info(xml_content)
    print(f"   총 {len(byeolpyos)}개 별표 발견:")
    print()
    
    # 별표 3 찾기 — 제목에 "기준벌기령" 포함되어야 진짜 별표 3
    target_byeolpyo = None
    for bp in byeolpyos:
        is_target = (bp["번호"] == "0003" and "기준벌기령" in bp["제목"])
        marker = "⭐" if is_target else "  "
        print(f"   {marker} 별표 {bp['번호']:>4} : {bp['제목'][:60]}")
        if is_target:
            target_byeolpyo = bp
    
    # Step 4: 별표 3 PDF 다운로드
    if target_byeolpyo:
        print()
        print(f"🎯 별표 3 발견!")
        print(f"   제목: {target_byeolpyo['제목']}")
        
        if target_byeolpyo["PDF링크"]:
            print(f"   PDF 링크: {target_byeolpyo['PDF링크']}")
            print()
            print("📥 별표 3 PDF 다운로드 시도...")
            
            pdf_path = download_byeolpyo_pdf(
                target_byeolpyo["PDF링크"],
                f"byeolpyo3_기준벌기령_{target['법령일련번호']}.pdf"
            )
            
            if pdf_path:
                print(f"✅ 별표 3 PDF 저장: {pdf_path.name}")
                print(f"   크기: {pdf_path.stat().st_size:,} bytes")
                print(f"   경로: {pdf_path.relative_to(ROOT)}")
                print()
                print("💡 다음 단계: PDF 열어서 수종별 기준벌기령 표 확인")
                print("   추후: camelot으로 자동 표 추출 가능")
        else:
            print("   ⚠️ PDF 링크 없음. <별표내용> 텍스트만 사용 가능.")
            print()
            print(f"📋 별표 3 내용 (첫 300자):")
            print(target_byeolpyo["내용"])
    else:
        print()
        print("⚠️ 별표 3을 못 찾음.")