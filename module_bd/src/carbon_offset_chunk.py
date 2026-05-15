"""
carbon_offset_chunk.py
가이드 §6.4 — 산림탄소상쇄 가이드라인 PDF chunking.

목적: 산림청 공식 PDF 11종을 chunk → JSONL → Person 4 (수범) 의 RAG 코퍼스.

출력: module_bd/data/interim/carbon_chunks.jsonl
형식: {text, source, page, project_type, type}

가이드 §6.4 정확 매칭. 한국어 인코딩 + memory 관리.
"""

import pdfplumber
import json
import re
import gc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_DIR = ROOT / "module_bd" / "data" / "raw" / "carbon_offset"
OUT_PATH = ROOT / "module_bd" / "data" / "interim" / "carbon_chunks.jsonl"


# ============================================================
# 사업유형 매핑 (가이드 §6.4 + 우리 확장)
# ============================================================

# 8 사업유형 PDF (2025.1.2. 기준 폴더)
PDF_TYPES_METHODOLOGY = {
    "01. 신규조림재조림 사업 방법론_Ver1.0.pdf":          "afforestation_reforestation",
    "02. 벌기령 연장을 통한 산림경영 사업 방법론_Ver2.0.pdf": "forest_management_rotation",
    "03. 식생복구 사업 방법론_Ver2.0.pdf":                "vegetation_restoration",
    "04. 목제품 이용 사업 방법론_Ver1.0.pdf":             "wood_products",
    "05. 산림바이오매스 에너지 이용 사업 방법론_Ver1.0.pdf": "bioenergy",
    "06. 수종 갱신을 통한 산림경영 사업 방법론_Ver1.0.pdf":  "species_renewal",
    "07. 산불피해지 조림사업의 방법론_Ver2.0.pdf":         "fire_damage_planting",
    "08. 산지전용 억제 사업 방법론_Ver1.0.pdf":           "land_use_change_prevention",
}

# 3 보조 PDF (carbon_offset 루트)
PDF_TYPES_SUPPORT = {
    "산림탄소상쇄제도 운영 지침(2024.8.22.).pdf":          "operation_guideline",
    "산림탄소상쇄사업_산림조사_가이드라인ver04.pdf":         "forest_survey_guide",
    "산림탄소흡수원사업 통합 가이드북.pdf":                  "comprehensive_guidebook",
}


# ============================================================
# chunk_pdf() 함수 (가이드 §6.4 그대로)
# ============================================================

def chunk_pdf(pdf_path: Path, project_type: str, max_chars: int = 800, overlap_sentences: int = 2):
    """
    가이드 §6.4 chunk_pdf() — 한국어 문장 종결 기준 chunking.
    
    Args:
        pdf_path: PDF 파일 경로
        project_type: 사업유형 분류 (afforestation, forest_management 등)
        max_chars: 청크 최대 글자 수 (기본 800)
        overlap_sentences: 청크 간 overlap 문장 수 (기본 2)
    
    Returns:
        List[dict]: {text, source, page, project_type, type}
    """
    chunks = []
    pdf_name = pdf_path.name
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            
            for page_no, page in enumerate(pdf.pages, 1):
                try:
                    txt = page.extract_text() or ""
                except Exception as e:
                    print(f"   ⚠️ p.{page_no} 추출 실패: {e}")
                    continue
                
                if not txt.strip():
                    continue
                
                # 공백 정리
                txt = re.sub(r"\s+", " ", txt).strip()
                
                # 한국어 문장 종결 (마침표, 느낌표, 물음표, 한국어 마침표)
                sents = re.split(r"(?<=[.!?。])\s+", txt)
                
                buf, n = [], 0
                for s in sents:
                    if n + len(s) > max_chars and buf:
                        chunks.append({
                            "text": " ".join(buf),
                            "source": pdf_name,
                            "page": page_no,
                            "project_type": project_type,
                            "type": "guideline",
                        })
                        # overlap 유지 (마지막 N 문장)
                        buf = buf[-overlap_sentences:]
                        n = sum(len(b) for b in buf)
                    
                    buf.append(s)
                    n += len(s)
                
                # 마지막 청크
                if buf:
                    chunks.append({
                        "text": " ".join(buf),
                        "source": pdf_name,
                        "page": page_no,
                        "project_type": project_type,
                        "type": "guideline",
                    })
                
                # 메모리 정리 (큰 PDF 대비)
                if page_no % 50 == 0:
                    gc.collect()
    
    except Exception as e:
        print(f"   ❌ {pdf_name} 처리 실패: {e}")
        return chunks
    
    return chunks


# ============================================================
# 메인
# ============================================================

def main():
    print("=" * 60)
    print("📄 산림탄소상쇄 가이드라인 PDF chunking")
    print("=" * 60)
    
    all_chunks = []
    
    # 1. 8 사업유형 방법론 (2025.1.2. 기준)
    method_dir = PDF_DIR / "사회공헌형 산림탄소상쇄 방법론(2025.1.2. 기준)"
    print(f"\n📂 사업유형 방법론 (2025.1.2. 기준)")
    print("-" * 60)
    
    for fname, ptype in PDF_TYPES_METHODOLOGY.items():
        pdf_path = method_dir / fname
        if not pdf_path.exists():
            print(f"   ⚠️ 파일 없음: {fname}")
            continue
        
        chunks = chunk_pdf(pdf_path, ptype)
        all_chunks.extend(chunks)
        print(f"   ✅ {ptype:>35} : {len(chunks):>4} 청크 ({fname[:30]}...)")
        gc.collect()
    
    # 2. 3 보조 PDF (carbon_offset 루트)
    print(f"\n📂 보조 PDF (운영 지침 + 산림조사 + 통합 가이드북)")
    print("-" * 60)
    
    for fname, ptype in PDF_TYPES_SUPPORT.items():
        pdf_path = PDF_DIR / fname
        if not pdf_path.exists():
            print(f"   ⚠️ 파일 없음: {fname}")
            continue
        
        chunks = chunk_pdf(pdf_path, ptype)
        all_chunks.extend(chunks)
        print(f"   ✅ {ptype:>35} : {len(chunks):>4} 청크")
        gc.collect()
    
    # JSONL 저장
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    
    # 통계
    print()
    print("=" * 60)
    print("📊 청크 통계")
    print("=" * 60)
    print(f"   총 청크: {len(all_chunks):,} 개")
    print(f"   저장: {OUT_PATH.relative_to(ROOT)}")
    print(f"   파일 크기: {OUT_PATH.stat().st_size / 1024:.1f} KB")
    
    # 사업유형별 분포
    print(f"\n   사업유형별 분포:")
    types = {}
    for c in all_chunks:
        types[c["project_type"]] = types.get(c["project_type"], 0) + 1
    for t, n in sorted(types.items(), key=lambda x: -x[1]):
        print(f"      {t:>40}: {n:>5} 청크")
    
    # 청크 길이 통계
    lengths = [len(c["text"]) for c in all_chunks]
    print(f"\n   청크 길이 (글자):")
    print(f"      평균: {sum(lengths)/len(lengths):.0f}")
    print(f"      최소: {min(lengths)}")
    print(f"      최대: {max(lengths)}")
    
    # 샘플 청크 (각 사업유형 첫 1개)
    print(f"\n   📝 샘플 청크 (각 사업유형 첫 1개):")
    seen = set()
    for c in all_chunks:
        if c["project_type"] in seen:
            continue
        seen.add(c["project_type"])
        print(f"\n   ── {c['project_type']} (p.{c['page']}) ──")
        print(f"   {c['text'][:150]}...")
    
    print()
    print("=" * 60)
    print("✅ chunk_pdf() 작동 확인 — Person 4 (수범) RAG 데이터 준비 완료")
    print("=" * 60)


if __name__ == "__main__":
    main()