"""
03_kau_wta_breakeven.py — D23 학술 발견: KAU 시계열 + WTA 17,039원 돌파 임박.

목적: data.go.kr 1160100 의 KAU25 시계열로부터 박일희 2020 WTA hurdle 까지의
      거리를 *데이터로부터 직접 계산* 한다. (수치를 하드코딩하지 않는다 — D131)
출력: 시계열 데이터 + 시각화 (Plotly 호환).

2026-06-05 정정(D131): 검증 가능한 최신 데이터는 2026-03 의 15,550원이며 이는 WTA
17,039원에 8.7% 미달이다. 이전 버전의 '19,600원 / +126% / 역사적 첫 돌파' 서술은
원천 데이터에 없는 값이라 제거하고, 저점→최신 +79.4% 상승 및 '돌파 임박' 으로 정정.
"""

# %%
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# %% [markdown]
# # D23 학술 발견 — KAU vs WTA hurdle, 돌파 임박
#
# 모든 수치는 아래 시계열 데이터(data.go.kr)로부터 계산한다.

# %%
kau_path = Path(__file__).resolve().parents[1] / "data" / "raw" / "kau" / "kau_timeseries_2025_2026.json"
with open(kau_path, encoding="utf-8") as f:
    kau_data = json.load(f)

print("=" * 70)
print("D23: KAU 시계열 + WTA hurdle 거리 (데이터 기반)")
print("=" * 70)

# %%
wta = kau_data["_meta"]["wta_hurdle_won_per_tco2"]  # 17,039 박일희 2020
history = kau_data["history"]

print(f"\nWTA hurdle: {wta:,} 원/tCO₂ (박일희 2020 산주 의지가격)")
print(f"\n{'시점':<10s} {'vintage':<10s} {'종가':>10s} {'WTA 대비':>10s} {'margin':>12s}")
print("-" * 60)

for h in history:
    if h.get("clpr") is None:
        continue
    clpr = int(h["clpr"])
    ratio = clpr / wta
    margin = clpr - wta
    marker = "🚀 돌파" if margin > 0 else "  "
    print(f"{h['period']:<10s} {h['vintage']:<10s} {clpr:>10,d}원 {ratio:>9.2f}x {margin:>+12,d}원 {marker}")

# %%
# KAU25 시계열 추출 + 핵심 수치를 데이터에서 직접 계산
kau25_data = [(h["period"], int(h["clpr"])) for h in history if h["vintage"] == "KAU25"]
periods = [d[0] for d in kau25_data]
prices = [d[1] for d in kau25_data]

low_idx = min(range(len(prices)), key=lambda i: prices[i])
latest_idx = len(prices) - 1
low_price, low_period = prices[low_idx], periods[low_idx]
latest_price, latest_period = prices[latest_idx], periods[latest_idx]
change_pct = round((latest_price - low_price) / low_price * 100, 1)
margin_won = latest_price - wta
margin_pct = round(margin_won / wta * 100, 1)
crossed = latest_price > wta

# %% [markdown]
# ## 핵심 발견 (데이터 산출)

# %%
print("\n핵심 발견:")
print(f"  - 저점:  {low_period} {low_price:,}원 (WTA 의 {low_price/wta*100:.0f}%)")
print(f"  - 최신:  {latest_period} {latest_price:,}원 (WTA 의 {latest_price/wta*100:.0f}%)")
print(f"  - 변화율: 저점→최신 {change_pct:+.1f}% ({len(prices)}개 분기 시점)")
print(f"  - WTA 까지 거리: {margin_won:+,}원 ({margin_pct:+.1f}%)"
      + (" — 돌파!" if crossed else " — 아직 미돌파 (돌파 임박)"))

# %%
# 시각화 데이터 생성 (모든 서술 수치는 위 계산값 사용)
plot_data = {
    "x_periods": periods,
    "y_kau25_close": prices,
    "wta_hurdle": wta,
    "kau25_low": low_price,
    "kau25_latest": latest_price,
    "change_low_to_latest_pct": change_pct,
    "margin_to_wta_won": margin_won,
    "margin_to_wta_pct": margin_pct,
    "wta_crossed": crossed,
    "korean": {
        "title": (
            f"D23: KAU25 vs WTA hurdle {wta:,}원 — "
            + ("돌파" if crossed else f"돌파 임박 ({latest_period} 기준 {abs(margin_pct):.1f}% 미달)")
        ),
        "y_label": "KAU25 종가 (원/tCO₂)",
        "x_label": "시점",
        "wta_label": f"WTA hurdle {wta:,}원 (박일희 2020)",
        "approach_note": (
            f"{latest_period} KAU {latest_price:,}원 = WTA 의 {latest_price/wta*100:.1f}% "
            f"(margin {margin_won:+,}원). {low_period} 저점 {low_price:,}원 대비 "
            f"16개월 {change_pct:+.1f}% — "
            + ("돌파 달성." if crossed else "돌파 임박 국면이나 아직 미돌파.")
        ),
    },
    "interpretation": (
        "사유림 산주의 자발적 KOC 참여가 경제적으로 합리적이 되는 임계 도달 직전 국면. "
        f"최신 검증 가능 데이터({latest_period})의 KAU25 {latest_price:,}원은 WTA 의향가격"
        f"({wta:,}원)에 {abs(margin_pct):.1f}% 차이로 근접했으나 아직 넘어서지 않았다. "
        "KAU 가 WTA 를 돌파하면 Module C 시나리오 4(연장KOC) 의 carbon_revenue 가 "
        "양으로 활성화된다. 정책학자 D17 의 '노령림 정책 갈등' 의 경제적 해소가 "
        "임박했음을 데이터로 보여준다."
    ),
}

# 저장
out = Path(__file__).resolve().parents[1] / "data" / "processed" / "d23_plot_data.json"
out.write_text(json.dumps(plot_data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n시각화 데이터 저장: {out}")

# %% [markdown]
# ## 학술 해석 (논문 §5 Results 핵심)

# %%
print("\n" + "=" * 70)
print("D23 학술 해석 — 논문 §5 finding")
print("=" * 70)
interpretation = f"""
본 연구는 {low_period} ~ {latest_period} 16개월간 KAU25 종가의 {change_pct:+.1f}% 상승을 발견했다.
{latest_period} 기준 {latest_price:,}원은 박일희 (2020) 의 한국 산주 평균 WTA
{wta:,}원/tCO₂ 에 {abs(margin_pct):.1f}% 차이로 근접했으나 {'돌파했다' if crossed else '아직 돌파하지 않았다'}.

정책적 함의:
1. 사유림 산주의 *자발적 KOC 등록* 경제적 합리성의 임계 도달 직전
   - 현재: KAU {latest_price:,} < WTA {wta:,} → 아직 KOC 참여 비합리적
   - 임박: 추세 지속 시 단기 내 돌파 → 자발적 참여 합리성 확보 예상

2. 정책학자 D17 의 노령림 정책 갈등 해소가 임박한 시점
   - 영급 불균형 30년 이상 72% → 벌채 후 재조림 회전 vs KOC 연장 갈등
   - KAU > WTA 돌파 시점부터 산주가 KOC 연장 자발적 선택 가능

3. Module C 시나리오 4 (연장KOC) 의 경제적 유효성
   - WTA 미달(현재) → carbon_revenue=0 → 시나리오 4 비경제적
   - WTA 초과(돌파 후) → 시나리오 4 가 적극적 추천 가능

발표 시 Q&A 방어:
  Q: "왜 지금 산림탄소상쇄가 의미 있나?"
  A: "KAU 가 16개월 {change_pct:+.0f}% 급등해 산주 WTA 의향가격 {abs(margin_pct):.0f}% 거리까지
      근접했다. 돌파 임박 시점에 Faustmann-Hartman 으로 산주 참여 경제성을 정량화하는
      학술적·정책적 시의성."
"""
print(interpretation)

print("=" * 70)
print("✅ D23 시계열 분석 완료 — 발표 §5 finding (데이터 기반)")
print("=" * 70)
