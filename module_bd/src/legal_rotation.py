"""
legal_rotation.py
별표 3 PDF (수종별 기준벌기령) → JSON 룰베이스.

데이터:
- 출처: 산림자원의 조성 및 관리에 관한 법률 시행규칙 별표 3 <개정 2023.6.27>
- 파일: module_bd/data/raw/law_extracts/byeolpyo3_기준벌기령_283217.pdf

산출물:
- module_bd/data/processed/rotation_age.json
- 함수: rotation_age(species, ownership="사유림")

용도:
- 모듈 C (희도) Faustmann NPV 에서 *법적 최소 벌채 연령* 검증
- 예: 잣나무 사유림 50년, 낙엽송 30년

수종 매핑:
- 별표 3 의 '참나무류' = 임분수확표의 상수리/굴참/신갈나무
  (자작나무·백합나무는 잠정 수종이라 별도 매핑)
- 별표 3 의 '소나무' = 임분수확표의 강원지방소나무, 중부지방소나무
- 별표 3 의 '포플러류' = 임분수확표의 이태리포플러
"""

import json
import pdfplumber
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = ROOT / "module_bd" / "data" / "raw" / "law_extracts" / "byeolpyo3_기준벌기령_283217.pdf"
OUT_DIR = ROOT / "module_bd" / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 임분수확표 수종 → 별표 3 카테고리 매핑
# (희도/수범이 임분수확표 수종을 그대로 넘겨도 법령 매칭 가능)
SPECIES_TO_LEGAL = {
    # 별표 3 직접 매칭
    "잣나무":          "잣나무",
    "리기다소나무":    "리기다소나무",
    "낙엽송":          "낙엽송",
    "삼나무":          "삼나무",
    "편백":            "편백",
    
    # '소나무' 카테고리
    "강원지방소나무":  "소나무",
    "중부지방소나무":  "소나무",
    "해송":            "소나무",  # 잠정 — 별표 3 에 명시 안 됨, 소나무 카테고리로 간주
    
    # '참나무류'
    "상수리나무":      "참나무류",
    "굴참나무":        "참나무류",
    "신갈나무":        "참나무류",
    
    # '포플러류'
    "이태리포플러":    "포플러류",
    
    # 별표 3 에 명시 안 됨 (잠정) → 기타 활엽수로 간주
    "자작나무":        "기타 활엽수",
    "백합나무":        "기타 활엽수",
}


def parse_rotation_table() -> dict:
    """
    별표 3 PDF p.1 의 기준벌기령 표 텍스트 파싱.
    
    Returns:
        dict: {
            "수종 (별표3)": {
                "국유림": int,
                "공사유림": int,
                "기업경영림": int,
            }
        }
    """
    with pdfplumber.open(PDF_PATH) as pdf:
        text = pdf.pages[0].extract_text() or ""
    
    # 일반기준벌기령 섹션만 추출
    # "가. 일반기준벌기령" 부터 "나. 특수용도기준벌기령" 직전까지
    start = text.find("가. 일반기준벌기령")
    end = text.find("나. 특수용도기준벌기령")
    if start == -1 or end == -1:
        raise ValueError("일반기준벌기령 섹션 못 찾음")
    
    section = text[start:end]
    
    # 수종별 정규식 — "수종명 X년 Y년(Z년)" 형식
    # 예: "잣나무 60년 50년(40년)"
    # 예: "소나무 60년 40년(30년)"
    # 예: "포플러류 3년 3년"  ← 괄호 없는 케이스
    
    pattern = re.compile(
        r"(\S+(?:\s\S+)?)\s+"            # 수종명 (한두 단어)
        r"\(?(\d+)년\)?\s+"               # 국유림 년수 (괄호 있을 수도)
        r"\(?(\d+)년\)?"                  # 공사유림 년수
        r"(?:\s*\((\d+)년\))?"            # 기업경영림 년수 (괄호, 있을 수도 없을 수도)
    )
    
    # 알려진 수종 (False positive 방지)
    KNOWN_SPECIES = {
        "소나무", "(춘양목보호림단지)", "잣나무", "리기다소나무",
        "낙엽송", "삼나무", "편백", "기타 침엽수",
        "참나무류", "포플러류", "기타 활엽수",
    }
    
    result = {}
    for line in section.split("\n"):
        line = line.strip()
        if not line:
            continue
        m = pattern.match(line)
        if not m:
            continue
        name = m.group(1).strip()
        if name not in KNOWN_SPECIES:
            continue
        gukyu = int(m.group(2))           # 국유림
        sayu = int(m.group(3))            # 공사유림
        gieop = int(m.group(4)) if m.group(4) else sayu   # 기업경영림 (괄호 없으면 사유림과 동일)
        
        result[name] = {
            "국유림": gukyu,
            "공사유림": sayu,
            "기업경영림": gieop,
        }
    
    return result


def rotation_age(species: str, ownership: str = "공사유림") -> dict:
    """
    임분수확표 수종명 + 소유 형태 → 법적 최소 벌채 연령.
    
    Args:
        species: 수종명 (임분수확표 기준, 예: "강원지방소나무")
        ownership: "국유림" | "공사유림" (기본) | "기업경영림"
    
    Returns:
        dict: {
            "rotation_age": int | None,
            "legal_category": str,           # 별표 3 카테고리 (예: "소나무")
            "ownership": str,
            "source": str,
            "note": str | None,
        }
    """
    json_path = OUT_DIR / "rotation_age.json"
    if not json_path.exists():
        raise FileNotFoundError(
            f"룰베이스 JSON 없음: {json_path}\n"
            f"먼저 'python module_bd/src/legal_rotation.py' 실행 필요"
        )
    
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    
    legal_cat = SPECIES_TO_LEGAL.get(species)
    if legal_cat is None:
        return {
            "rotation_age": None,
            "legal_category": None,
            "ownership": ownership,
            "source": "별표 3",
            "note": f"'{species}' 매핑 없음. 사용 가능: {sorted(SPECIES_TO_LEGAL.keys())}",
        }
    
    if legal_cat not in data["rotation_age_years"]:
        return {
            "rotation_age": None,
            "legal_category": legal_cat,
            "ownership": ownership,
            "source": "별표 3",
            "note": f"'{legal_cat}' 별표 3 에 없음",
        }
    
    age = data["rotation_age_years"][legal_cat].get(ownership)
    note = None
    if species in {"자작나무", "백합나무"}:
        note = f"'{species}' 잠정 수종, '기타 활엽수' 기준 적용"
    elif species == "해송":
        note = "해송은 별표 3 명시 안 됨, '소나무' 카테고리로 간주 (잠정)"
    
    return {
        "rotation_age": age,
        "legal_category": legal_cat,
        "ownership": ownership,
        "source": "산림자원의 조성 및 관리에 관한 법률 시행규칙 별표 3 <개정 2023.6.27>",
        "note": note,
    }


def build_json() -> dict:
    """PDF 파싱 결과를 JSON 으로 저장."""
    parsed = parse_rotation_table()
    
    data = {
        "source": {
            "law": "산림자원의 조성 및 관리에 관한 법률 시행규칙",
            "annex": "별표 3",
            "revision": "2023-06-27",
            "pdf_file": str(PDF_PATH.relative_to(ROOT)),
        },
        "rotation_age_years": parsed,
        "species_mapping": SPECIES_TO_LEGAL,
    }
    
    out_json = OUT_DIR / "rotation_age.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 {out_json.relative_to(ROOT)}")
    return data


if __name__ == "__main__":
    print("=" * 60)
    print("📖 별표 3 → rotation_age.json 빌드")
    print("=" * 60)
    
    data = build_json()
    
    print()
    print("📋 추출된 기준벌기령:")
    for sp, ages in data["rotation_age_years"].items():
        print(f"   {sp:>14}: 국유림 {ages['국유림']}년 / "
              f"공사유림 {ages['공사유림']}년 / 기업경영림 {ages['기업경영림']}년")
    
    print()
    print("=" * 60)
    print("🌲 rotation_age() 함수 테스트")
    print("=" * 60)
    
    test_cases = [
        ("강원지방소나무", "공사유림", "충북 보은 주력"),
        ("강원지방소나무", "국유림", "국유림 60년"),
        ("강원지방소나무", "기업경영림", "기업경영림 30년"),
        ("잣나무", "공사유림", "잣나무 사유림"),
        ("낙엽송", "공사유림", "낙엽송 30년"),
        ("리기다소나무", "공사유림", "리기다 25년"),
        ("신갈나무", "공사유림", "참나무류 매핑"),
        ("자작나무", "공사유림", "잠정 → 기타 활엽수"),
        ("이태리포플러", "공사유림", "포플러류 3년"),
        ("해송", "공사유림", "잠정 소나무"),
        ("없는수종", "공사유림", "에러 케이스"),
    ]
    
    for species, ownership, desc in test_cases:
        result = rotation_age(species, ownership)
        age = result["rotation_age"]
        cat = result["legal_category"]
        age_str = f"{age}년" if age is not None else "None"
        print(f"\n   📌 {desc}")
        print(f"      {species} ({ownership}) → {age_str} (카테고리: {cat})")
        if result["note"]:
            print(f"      💬 {result['note']}")
    
    print()
    print("=" * 60)
    print("✅ rotation_age() 테스트 완료")
    print("=" * 60)