# Diagnose Scripts — 학습/진단 흔적

이 폴더는 *production 코드가 아닌* PDF·API 진단·학습 스크립트 모음.

**진짜 production 코드**: `module_bd/src/` 의 13 파일 (모듈 README v5 명시).

## 분류

### Day 1 (초기 학습)
- `growth_api.py`: 국립산림과학원 API 시도 (DRAFT, 나중에 PDF 파싱으로 전환)
- `yield_explore.py`: 임분수확표 PDF 구조 탐색
- `legal_diagnose.py`: 법제처 API 시도

### Day 2 (PDF 진단)
- `cell_debug.py`: PDF 표 cell 단위 디버그
- `pdf_structure.py`: PDF 일반 구조 분석
- `page_debug.py`: 페이지별 디버그
- `kofpi_diagnose.py`: KOFPI 표 추출 시도 1차
- `kofpi_diagnose_text.py`: KOFPI 텍스트 추출 시도
- `fps_diagnose.py`: 임분수확표 cell 탐색

### Day 2 후반 (표준품셈 진단 4 단계)
- `standard_cost_diagnose.py`:  PDF 구조 1차 진단
- `standard_cost_diagnose2.py`: 표 추출 2차
- `standard_cost_diagnose3.py`: 페이지 매핑 3차
- `standard_cost_diagnose4.py`: 최종 진단 → 옵션 Y 결정 근거

## 학술 가치

이 스크립트들은 *어떻게 진짜 PDF 데이터에 도달했는지* 의 학습 흔적.

- 가이드 §7.1 placeholder 함정 발견 과정
- KOFPI 표 추출 방법 학습 (Day 2)
- 표준품셈 PDF 구조 이해 (Day 2 후반)

→ DECISIONS.md 의 D2, D3 결정의 *배경 데이터* 역할.

## 사용 정책

production 코드에서 이 스크립트들 *import 하지 않음*. 학습용·참고용으로만 보관.