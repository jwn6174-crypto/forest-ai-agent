"""
02_validation_d22.py — D22 학술 발견: carbonregistry 인증 vs Module C 모델 +45% 차이.

목적: 4 real 등록사업 (보은 2 + 진안 2) 의 인증 흡수량 vs Module C 모델 추정 비교.
출력: 비교표 + 시각화 데이터 (Plotly 호환 dict).

2026-06-05 정정(D131): Module B 탄소모델 갱신 후 모델 추정이 220.2 tCO₂/ha/30yr
(정우 _lookup_carbon_uptake 30~60년 평균 7.34 × 30)로 올라, 인증 320.2 대비 차이가
+45.4% 가 되었다. 초기 문서의 +103%(구 모델 157)는 구 모델값이라 정정.
"""

# %%
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from module_c.src.validation import validate_all_real_cases, summary_validation_report
from module_c.src.demo_parcels import REAL_REGISTERED_PARCELS

# %% [markdown]
# # D22 학술 발견 — 인증 vs 모델 +45% 차이
#
# **carbonregistry.forest.go.kr 658건 → 4 검증 case 정선** (정책학자 D17 4 조건):
# - 사업유형 = 벌기령 연장 산림경영 (한국 인증실적 99%)
# - 지역 = 충북 보은 / 전북 진안 + 인접
# - 참여유형 = 거래 (인증실적 공개)
# - 면적 1-200 ha (영세 사유림 대표)

# %%
print("=" * 80)
print("D22: carbonregistry 인증 vs Module C 모델 비교")
print("=" * 80)

print("\n[Real 등록사업 4개 메타]")
for pid, p in REAL_REGISTERED_PARCELS.items():
    print(f"\n  {pid}")
    print(f"    {p['lot_id']}")
    print(f"    면적: {p['area_ha']} ha")
    print(f"    인증: {p['registered_total_absorption_tco2']:,} tCO₂")
    print(f"    유형: {p['project_type']}")

# %%
print("\n" + "=" * 80)
print("Module C 비교 실행")
print("=" * 80)
results = validate_all_real_cases(verbose=True)

# %% [markdown]
# ## 종합 보고

# %%
print("\n" + "=" * 80)
summary = summary_validation_report(results)
print(f"검증 case 수: {summary['n_cases']}")
print(f"평균 차이: {summary['avg_difference_pct']}%")
print(f"학술 주장: {summary['academic_claim']}")

# %% [markdown]
# ## 시각화 데이터 (수범 module_e Plotly 용)

# %%
plot_data = {
    "x_labels": [r["parcel_id"][:30] for r in results],
    "certified_per_30yr": [r["certified_tco2_per_ha_per_30yr"] for r in results],
    "model_per_30yr": [r["model_30yr_total_tco2_per_ha"] for r in results],
    "difference_pct": [r["difference_pct"] for r in results],
    "korean": {
        "title": "D22: 인증 흡수량 vs Module C 모델 (4 real 등록사업)",
        "y_label": "30년 누적 흡수량 (tCO₂/ha)",
        "x_label": "검증 case",
        "legend_cert": "carbonregistry 인증",
        "legend_model": "Module C 모델 (자연 성장)",
    },
}

# 저장
out = Path(__file__).resolve().parents[1] / "data" / "processed" / "d22_plot_data.json"
out.write_text(json.dumps(plot_data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n시각화 데이터 저장: {out}")

# %% [markdown]
# ## 학술 해석 (논문 §6 Discussion)

# %%
print("\n" + "=" * 80)
print("D22 학술 해석")
print("=" * 80)
interpretation = """
4 검증 case 모두 인증사업(320.2 tCO₂/ha/30yr)이 Module C 모델(220.2)보다 +45% 큼. 두 가설:

가설 1 (인증사업의 회계 가정):
  carbonregistry 인증 = 320 tCO₂/ha/30yr → 10.67 tCO₂/ha/yr 에 해당,
  이는 국립산림과학원 (2003/2024) 의 30년 *피크* 흡수율(10.77 tCO₂/ha/yr)에 거의 일치.
  반면 모델은 30~60년 *평균* 7.34(피크 후 감소 반영) × 30 = 220.
  → 인증사업이 사실상 *피크값* 을 30년 내내 유지한다고 가정 = bookkeeping overestimation

가설 2 (경영 효과):
  벌기연장 산림경영 = 간벌·시비·하층관리로 *자연 성장 이상의* 흡수율 유지 가능
  → Module C (자연 성장 가정) 가 underestimation

두 가설 모두 검증 가능:
  - 가설 1: 국립산림과학원 임령별 실측 데이터 재해석으로 검증
  - 가설 2: 위성 (GEDI L4A, Sentinel-2) 시계열로 인증사업 임지 검증 (W6)

**학술 기여 (논문 Discussion 핵심)**:
  본 연구는 한국 산림탄소상쇄 인증실적이 국가 자연성장 모델보다 +45% 높다는
  체계적 격차를 정량화하고, 인증실적 baseline 가정의 검토 필요성을 제기한다.
  Module C 의 보수적 추정이 산주 의사결정에 *정직성* 더함 — 인증 흡수량을
  upper bound 로, Module C 를 lower bound 로 양쪽 표시 권장.
"""
print(interpretation)

print("=" * 80)
print("✅ D22 검증 완료")
print("=" * 80)
