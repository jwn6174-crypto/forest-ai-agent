# Module C — diagnose/ (학습 기록)

> 정우 `module_bd/src/diagnose/` 패턴 모방.
> 데이터 진단·파싱 학습 기록 — module_c 의 src 모듈로 가기 전 시행착오·실험.

**작성일**: 2026-05-22

---

## 파일

### `parse_carbonregistry.py`
사용자가 conversation 으로 제공한 carbonregistry 658건 raw text 파싱.
- D114 학술 발견 (인증 320 vs 모델 220 = +45.4%) 의 근원 데이터.
- 출력: `module_c/data/raw/registered_offset/all_projects_2026_05.json` (충북·전북·강원 정선)
- 출력: `module_c/data/processed/validation_cases.json` (W6 검증 case 4개)

**사용**:
```bash
python module_c/diagnose/parse_carbonregistry.py
```

### `extract_pdf_docx.py`
사용자 제공 4 reference 파일의 텍스트 추출:
- `2024년 임산물생산조사 보고서.pdf` → NTFP 진짜 데이터 (D105)
- `2025년 산림소득분야 사업시행지침.pdf` → 산림보조사업 (D110)
- `OpenAPI활용가이드_산림청_산림자원통계 서비스_v1.2.docx` → data_go_kr_api.py
- `오픈API 활용자가이드_금융위원회_일반상품시세정보.docx` → KAU 호출 패턴

**사용**:
```bash
python module_c/diagnose/extract_pdf_docx.py
```

---

## 학습 메모

1. **PDF 추출 시 pdfplumber 사용** — pypdf 보다 표 추출 정확
2. **carbonregistry 658건 → 충북·전북·강원 정선** (학술 case study) — 정책학자 D109 4 조건 적용
3. **KAU vs 산림자원통계 API endpoint 차이** — 1160100 vs 1400000
4. **decoded 키 사용** — requests 자동 인코딩 (encoded 는 401)

---

## 정우 module_bd/src/diagnose/ 와 비교

| 정우 diagnose 13 파일 | Module C diagnose 2 파일 |
|---|---|
| KOFPI, KOSIS, 표준품셈, 별표3 PDF 진단 | carbonregistry, PDF/DOCX 추출 |
| 데이터 *진단* (어떻게 추출할까) | 데이터 *수집* (이미 알고 있는 출처에서) |

→ Module C 는 정우 데이터 호출로 충분 (8 진짜 데이터) — diagnose 적음.
