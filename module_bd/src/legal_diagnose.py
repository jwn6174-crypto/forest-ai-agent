"""
legal_diagnose.py
법제처 XML의 실제 구조 확인용 임시 도구.
별표 관련 태그가 어떻게 들어있는지 본다.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
xml_path = ROOT / "module_bd" / "data" / "raw" / "law_extracts" / "forest_law_283217.xml"

content = xml_path.read_bytes()
root = ET.fromstring(content)

print(f"📄 XML 분석: {xml_path.name}")
print(f"   루트 태그: <{root.tag}>")
print(f"   직계 자식 태그: {[c.tag for c in root]}")
print()

# 모든 태그 이름 수집 (어떤 태그들이 있나)
all_tags = Counter()
def walk(elem, depth=0):
    all_tags[elem.tag] += 1
    for child in elem:
        walk(child, depth + 1)

walk(root)

print(f"📊 등장하는 태그 종류: {len(all_tags)}개")
print("   상위 20개:")
for tag, count in all_tags.most_common(20):
    print(f"   {count:>5}× <{tag}>")

print()
print("🔎 '별표' 키워드 포함 태그:")
for tag in all_tags:
    if "별표" in tag or "표" in tag:
        print(f"   <{tag}> — {all_tags[tag]}회")

print()
print("🔎 '기준벌기령' 키워드 등장 위치:")
def find_keyword(elem, path=""):
    text = (elem.text or "") + (elem.tail or "")
    if "기준벌기령" in text or "벌기령" in text:
        print(f"   {path}/<{elem.tag}> : {text.strip()[:80]}")
    for i, child in enumerate(elem):
        find_keyword(child, f"{path}/{elem.tag}")

find_keyword(root)

print()
print("💡 별표 부분 텍스트 (처음 1000자):")
def find_table_text(elem):
    text_parts = []
    for e in elem.iter():
        if e.text:
            text_parts.append(e.text)
    return " ".join(text_parts)

# '벌기령'이라는 단어 주변 텍스트 찾기
full_text = find_table_text(root)
idx = full_text.find("벌기령")
if idx >= 0:
    start = max(0, idx - 100)
    end = min(len(full_text), idx + 800)
    print(full_text[start:end])
else:
    print("   '벌기령' 키워드 못 찾음")