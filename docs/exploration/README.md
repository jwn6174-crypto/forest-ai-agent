# 탐색 자산 (Exploration)

이 폴더는 *책임 모듈 밖* 호기심으로 탐색한 진단 자산을 둔다.
정식 작업물 아니지만 — 해당 모듈 담당자가 시작할 때 *시간 절약*되는 정보를 담는다.

## 자산

### `gedi_boeun_count.py` — 보은 GEDI L4A footprint 개수 진단

**작성**: 2026-05-21, 정우 (모듈 B/D)
**대상 모듈**: A (위성, 민석 담당)
**목적**: 가이드 §3.4 의 "보은 GEDI footprint 5,000~15,000개" 추정 검증.

**핵심 발견** (시간 절약용):
1. **GAUL Level 2 한국 시군구 없음.** ADM2 가 "Administrative unit not available". 행정경계는 SHP 별도 다운로드 필요 (gisdeveloper.co.kr 등). 이 파일은 bbox 로 우회.
2. **GEE의 `LARSE/GEDI/GEDI04_A_002_INDEX` 는 *카탈로그*.** sub-asset(궤도)의 `table_id` 만 가짐. 진짜 footprint 는 `LARSE/GEDI/GEDI04_A_002/<table_id>` 따라가야 나옴.
3. **GEDI04_A_002 의 sub-asset 에 AGBD 값 *없음*.** Footprint 메타데이터·품질·지오로케이션만. AGBD 받으려면 `LARSE/GEDI/GEDI04_B_002` (1km 그리드) 별도 사용.
4. **보은 bbox 결과** (994 km², 보은 행정경계 584 km² 의 약 1.7배):
   - 전체 footprint: 321,460개 (119개 궤도 합)
   - 품질 통과 (l4_quality=1 AND degrade=0): 21,215개 (6.6%)
   - 행정경계 보정(× 0.59): ~12,464개 → **가이드 추정 5k~15k 의 상한 근처. 검증 통과**.
5. **품질 통과율 6.6%** — 미국·열대(30~50%)보다 낮음. 한국 산악 지형에서 degrade_flag 많이 떨어지는 듯.

**모듈 A 시작 시 다음 단계**:
- 정확한 보은 행정경계 SHP 받기 (gisdeveloper.co.kr → 시군구)
- bbox → 정식 행정경계 로 재계산
- L4B 1km 그리드 AGBD 도 같이 받아 학습 라벨 후보 둘 다 보유