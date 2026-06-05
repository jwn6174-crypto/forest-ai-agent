"""
gedi_boeun_count.py — 보은 GEDI L4A footprint 개수 확인 (bbox 추정).

진단 자산. 모듈 A(민석) 영역이지만 호기심·정보 공유용.

발견 기록:
  · GAUL 한국 시군구 없음 → 행정경계 SHP 필요 (현재는 bbox 대용)
  · LARSE/GEDI/GEDI04_A_002_INDEX = 카탈로그 (footprint 아님)
  · 진짜 footprint 는 INDEX 의 table_id 가 가리키는 sub-asset 안
  · 한 sub-asset = 한 궤도 = 수천 footprint
  · GEE의 GEDI04_A_002 는 AGBD 값 *없음* — footprint 메타데이터 전용.
    AGBD 받으려면 LARSE/GEDI/GEDI04_B_002 (1km 그리드) 사용 필요.
    이 진단은 footprint 'count' 확인이 목적이므로 L4A 로 충분.
"""
import ee

PROJECT = "jw2026"

ee.Initialize(project=PROJECT)

# 보은 bbox (행정경계보다 약간 큼, 약 994 km²)
BOEUN_BBOX = ee.Geometry.Rectangle([127.55, 36.40, 127.95, 36.65])


# ── [1] INDEX 에서 보은 위 sub-asset 119개 ──
print("=" * 60)
print("[1] INDEX 카탈로그 — 보은 bbox 안의 sub-asset")
print("=" * 60)
index = (
    ee.FeatureCollection("LARSE/GEDI/GEDI04_A_002_INDEX")
    .filterBounds(BOEUN_BBOX)
)
table_ids = index.aggregate_array("table_id").getInfo()
n_tables = len(table_ids)
print(f"sub-asset(table) 개수: {n_tables}")


# ── [2] 119개 sub-asset 합치기 — 총 footprint count ──
print("\n" + "=" * 60)
print(f"[2] {n_tables}개 sub-asset 합쳐 보은 bbox 안 footprint 총 수")
print("=" * 60)
print(f"  서버 호출 중... ({n_tables}개 collection 합산, 1~3분 소요)")

# 119개 FeatureCollection 을 모두 만들고 bbox 로 필터한 뒤 합침
collections = [
    ee.FeatureCollection(tid).filterBounds(BOEUN_BBOX)
    for tid in table_ids
]
merged = ee.FeatureCollection(collections).flatten()

# 전체 count
n_total = merged.size().getInfo()
print(f"\n  [전체] {n_total:,} footprint")

# 가이드 §5.5 품질 필터
merged_q = (
    merged
    .filter(ee.Filter.eq("l4_quality_flag", 1))
    .filter(ee.Filter.eq("degrade_flag", 0))
)
n_q = merged_q.size().getInfo()
print(f"  [품질] l4_quality=1 AND degrade=0: {n_q:,} "
      f"({n_q/max(n_total,1)*100:.1f}%)")

# + sensitivity > 0.9
merged_qs = merged_q.filter(ee.Filter.gt("sensitivity", 0.9))
n_qs = merged_qs.size().getInfo()
print(f"  [+sens] +sensitivity>0.9 (가이드 §5.5): {n_qs:,}")


# ── [3] 가이드 추정과 비교 ──
print("\n" + "=" * 60)
print("가이드 §3.4 (정식 행정경계 기준 추정):")
print("  전체 30,000~50,000 → 품질 필터 후 5,000~15,000")
print(f"\n실측 (bbox = 보은 약 1.7배 면적):")
print(f"  전체 {n_total:,} → 품질 후 {n_q:,} → +sens {n_qs:,}")
print("=" * 60)

# 행정경계 환산 (bbox 면적 / 보은 면적)
ratio = 584 / 994
print(f"\nbbox 보정 (× {ratio:.2f} = 보은/bbox 면적비):")
print(f"  전체 추정:    ~{int(n_total * ratio):,}")
print(f"  품질 후 추정: ~{int(n_q * ratio):,}")
print(f"  +sens 후:    ~{int(n_qs * ratio):,}")
print("\n주의: bbox 보정은 footprint 가 균등 분포한다는 가정.")
print("      정확한 행정경계 count 는 보은 SHP + 모듈 A 정식 작업.")