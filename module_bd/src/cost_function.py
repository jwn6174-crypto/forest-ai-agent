"""
cost_function.py
가이드 §7.1 — 임지·시나리오별 비용 추정 함수.

5/5 진짜 데이터 출처:
- harvest:    산림사업 표준품셈 (산림청 고시 제2025-82호) p.59-60 + 벌목부 시중노임
- skidding:   KOFPI 분기별 보고서 소운반비 (Q4 2025 기준)
- transport:  KOFPI 분기별 보고서 대운반비 (Q4 2025 기준)
- regen:      산림사업 표준품셈 p.73 (사방조림) + 보통/특별인부 시중노임 + 산림청 2025 묘목가격 고시
- 상차비:     KOFPI 보고서 (skidding/transport 공통)

가이드 §7.1 시그니처 정확 매칭. 희도 NPV 계산에서 직접 호출 가능.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WAGE_PATH = ROOT / "module_bd" / "data" / "raw" / "wage" / "wage_2025.json"


# ============================================================
# 데이터 로드 (모듈 import 시 1회)
# ============================================================

def _load_wages():
    """대한건설협회 시중노임 로드. 2025 하반기 기준."""
    with open(WAGE_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return {
        "보통인부": data["wages_won_per_person_day"]["보통인부"]["하반기"],
        "특별인부": data["wages_won_per_person_day"]["특별인부"]["하반기"],
        "벌목부":  data["wages_won_per_person_day"]["벌목부"]["하반기"],
    }

WAGES = _load_wages()


# ============================================================
# 표준품셈 + KOFPI 추출 데이터 (5/5 진짜 출처)
# ============================================================

# 1. 벌채 (산림사업 표준품셈 p.59-60)
#    - 전간목 기준: 벌목부 25.5 m³/인/일
#    - 즉 1m³ 벌채 = 1/25.5 = 0.0392 인일
HARVEST_VOLUME_PER_PERSON_DAY = 25.5  # 전간목 (단목 20.17, 전목 40.34)
HARVEST_WORKER = "벌목부"

# 2. 집재 (KOFPI 소운반비, 2025 Q4 침엽수 기준, 원/m³)
#    PDF 4분기 보고서 p.44
SKIDDING_BY_DISTANCE_KOFPI = {
    # (min_m, max_m): 원/m³
    (0,    500):   9300,    # 500m 이내 → 500-1000m 단가의 *낮은 추정* (KOFPI 표 시작이 500m)
    (500,  1000):  9300,
    (1000, 2000):  16400,
    (2000, 4000):  18400,
    (4000, 999999): 18400,  # 4km 초과는 동일 적용 (보수적 추정)
}

# 3. 운반 (KOFPI 대운반비, 2025 Q4 침엽수 5톤 기준, 원/m³)
#    PDF 4분기 보고서 p.43
TRANSPORT_BY_DISTANCE_KOFPI = {
    # (min_km, max_km): 원/m³
    (0,   50):    14600,
    (50,  100):   17500,
    (100, 150):   25200,
    (150, 200):   28500,
    (200, 250):   30700,
    (250, 300):   34900,
    (300, 9999):  36200,
}

# 4. 상차비 (KOFPI Q4 2025 침엽수, 원/m³) — skidding·transport 모두 적용
LOADING_CHARGE = 5800

# 5. 조림 (산림사업 표준품셈 p.73, 사방조림 1ha 기준)
REGEN_SPECIAL_WORKERS_PER_HA = 1.33
REGEN_NORMAL_WORKERS_PER_HA = 20
REGEN_SEEDLING_PER_HA = 4000           # 4,000본/ha (사방조림 표준)

# ============================================================
# 묘목 단가 — 산림청 2025년 공식 (산림자원법 시행령 제16조)
# ============================================================
SEEDLING_PRICES = {
    # 침엽수 (1-1 조림 표준)
    "강원지방소나무": 422,
    "중부지방소나무": 422,
    "소나무": 422,
    "잣나무": 530,           # 잣나무는 2-1 표준
    "낙엽송": 714,
    "리기다소나무": 388,
    "리기테다소나무": 390,
    "편백": 665,
    "삼나무": 699,
    
    # 활엽수 (1-1 조림 표준)
    "상수리나무": 1101,
    "신갈나무": 1101,        # 참나무류 매핑 (상수리 1-1)
    "굴참나무": 1101,        # 참나무류 매핑
    "참나무류": 1101,
    "자작나무": 1093,
    "백합나무": 1219,
    "물푸레나무": 884,
}

# 기본 (수종 불명 시)
REGEN_SEEDLING_UNIT_COST_DEFAULT = 550  # 7 수종 평균 (산림청 2025 공식)
REGEN_SUPPLY_COST_PER_HA = 200000      # 비료·운반비 추정 (PDF: "별도 계상", 추후 정밀화)

# 6. 간접비 (가이드 §7.1)
ADMIN_OVERHEAD = 0.15

# 7. 할증률 (산림사업 표준품셈 1-4, 작업 환경 보정)
SLOPE_SURCHARGE = {  # 1-4-5 경사도
    "완":  0.00,    # 15° 미만
    "중":  0.05,    # 15-30°
    "급":  0.10,    # 30° 초과
}


# ============================================================
# 헬퍼 함수
# ============================================================

def _lookup_skidding_unit(distance_m: float) -> int:
    """집재 거리 → KOFPI 단가 lookup (원/m³)."""
    for (lo, hi), price in SKIDDING_BY_DISTANCE_KOFPI.items():
        if lo <= distance_m < hi:
            return price
    return list(SKIDDING_BY_DISTANCE_KOFPI.values())[-1]


def _lookup_transport_unit(distance_km: float) -> int:
    """운반 거리 → KOFPI 단가 lookup (원/m³)."""
    for (lo, hi), price in TRANSPORT_BY_DISTANCE_KOFPI.items():
        if lo <= distance_km < hi:
            return price
    return list(TRANSPORT_BY_DISTANCE_KOFPI.values())[-1]


# ============================================================
# 메인 함수 — 가이드 §7.1 시그니처
# ============================================================

def cost_function(
    volume_m3: float,
    area_ha: float,
    distance_to_road_km: float,
    action: str,
    skidding_distance_m: float = 500.0,
    slope_class: str = "중",
    species: str = None,
) -> dict:
    """
    임지·시나리오별 비용 추정 (가이드 §7.1).
    
    Parameters
    ----------
    volume_m3 : float
        벌채 또는 처리 재적 (m³)
    area_ha : float
        임지 면적 (ha)
    distance_to_road_km : float
        가장 가까운 도로까지 거리 (km) — 트럭 운반 거리 추정
    action : str
        "clearcut" (개벌) | "thinning" (간벌) | "planting" (조림만)
    skidding_distance_m : float, optional
        집재 거리 (m). 기본 500m (KOFPI 표 시작값).
    slope_class : str, optional
        경사도 분류 "완" | "중" | "급". 기본 "중" (15-30°).
    species : str, optional
        수종명 (예: "강원지방소나무", "잣나무"). 
        제공 시 수종별 묘목 단가 (산림청 2025 공식) 사용.
        미제공 시 평균 단가 (550원/본) 사용.
    
    Returns
    -------
    dict
        가이드 §7.1 형식 + 메타데이터:
        {
            "breakdown": {harvest, skidding, transport, regen, loading},
            "total": 총비용 (간접비 포함),
            "subtotal": 직접비 합 (간접비 제외),
            "admin_overhead_amount": 간접비액,
            "slope_surcharge_applied": 할증률,
            "unit_costs": 각 항목 단위 비용 (시연용),
            "data_sources": 출처 메타데이터,
        }
    
    Examples
    --------
    >>> result = cost_function(
    ...     volume_m3=280, area_ha=1.0,
    ...     distance_to_road_km=15, action="clearcut",
    ...     skidding_distance_m=800, slope_class="중",
    ...     species="강원지방소나무",
    ... )
    >>> result["total"]
    20_633_628  # 약 2,063만원
    """
    if action not in ["clearcut", "thinning", "planting"]:
        raise ValueError(f"action 은 'clearcut', 'thinning', 'planting' 중 하나여야 함 (받음: {action})")
    
    breakdown = {}
    unit_costs = {}
    surcharge = 1.0 + SLOPE_SURCHARGE.get(slope_class, 0.05)
    
    # 1. 벌채 (clearcut, thinning 시)
    if action in ["clearcut", "thinning"]:
        # 벌목 인일 = volume / 25.5 (전간목 기준)
        person_days_harvest = volume_m3 / HARVEST_VOLUME_PER_PERSON_DAY
        harvest_cost = person_days_harvest * WAGES["벌목부"] * surcharge
        breakdown["harvest"] = round(harvest_cost)
        unit_costs["harvest_per_m3"] = round(harvest_cost / volume_m3) if volume_m3 > 0 else 0
    
    # 2. 집재 (clearcut, thinning 시) — KOFPI 소운반비
    if action in ["clearcut", "thinning"]:
        skidding_unit = _lookup_skidding_unit(skidding_distance_m)
        skidding_cost = volume_m3 * skidding_unit * surcharge
        breakdown["skidding"] = round(skidding_cost)
        unit_costs["skidding_per_m3"] = skidding_unit
    
    # 3. 운반 (clearcut, thinning 시) — KOFPI 대운반비
    if action in ["clearcut", "thinning"]:
        transport_unit = _lookup_transport_unit(distance_to_road_km)
        transport_cost = volume_m3 * transport_unit  # 운반은 경사도 할증 X
        breakdown["transport"] = round(transport_cost)
        unit_costs["transport_per_m3"] = transport_unit
    
    # 4. 상차비 (clearcut, thinning 시) — KOFPI
    if action in ["clearcut", "thinning"]:
        loading_cost = volume_m3 * LOADING_CHARGE
        breakdown["loading"] = round(loading_cost)
        unit_costs["loading_per_m3"] = LOADING_CHARGE
    
    # 5. 조림 (clearcut, planting 시)
    if action in ["clearcut", "planting"]:
        special_wage = REGEN_SPECIAL_WORKERS_PER_HA * WAGES["특별인부"] * area_ha
        normal_wage = REGEN_NORMAL_WORKERS_PER_HA * WAGES["보통인부"] * area_ha
        # 묘목 단가 (수종별, 산림청 2025 공식)
        if species and species in SEEDLING_PRICES:
            seedling_unit = SEEDLING_PRICES[species]
        else:
            seedling_unit = REGEN_SEEDLING_UNIT_COST_DEFAULT
        seedling_cost = REGEN_SEEDLING_PER_HA * seedling_unit * area_ha
        supply_cost = REGEN_SUPPLY_COST_PER_HA * area_ha
        regen_total = (special_wage + normal_wage + seedling_cost + supply_cost) * surcharge
        breakdown["regen"] = round(regen_total)
        unit_costs["regen_per_ha"] = round(regen_total / area_ha) if area_ha > 0 else 0
        unit_costs["seedling_unit"] = seedling_unit  # 시연용
    
    # 합계
    subtotal = sum(breakdown.values())
    admin_amount = subtotal * ADMIN_OVERHEAD
    total = subtotal + admin_amount
    
    return {
        "breakdown": breakdown,
        "subtotal": round(subtotal),
        "admin_overhead_amount": round(admin_amount),
        "total": round(total),
        "slope_surcharge_applied": SLOPE_SURCHARGE.get(slope_class, 0.05),
        "unit_costs": unit_costs,
        "data_sources": {
            "harvest": "산림사업 표준품셈 (산림청 고시 제2025-82호) p.59-60 + 대한건설협회 벌목부 노임",
            "skidding": "KOFPI 분기별 원목시장가격조사 보고서 소운반비 (2025 Q4 침엽수)",
            "transport": "KOFPI 분기별 원목시장가격조사 보고서 대운반비 (2025 Q4 침엽수 5톤)",
            "regen": "산림사업 표준품셈 p.73 사방조림 + 대한건설협회 노임 + 산림청 2025 묘목가격 고시",
            "loading": "KOFPI 분기별 보고서 상차비 (2025 Q4 침엽수)",
            "admin_overhead": "가이드 §7.1 (0.15)",
            "wages_period": "2025년 하반기 (2025-09-01 ~ 2025-12-31)",
        },
        "limitations": [
            "묘목 단가: 산림청 *공식 조림용* 가격 — 시중 가격은 1.2-2배 가능",
            "보육·간벌 작업의 *재투입* 비용 미반영 (개벌 단순화)",
            "경사도 외 할증 (이동거리, 작업시기 등) 미반영",
            "KOFPI 운반비는 *전국 평균* — 충북 보은 지역 특화 X",
            "비료·운반비 200,000원/ha 는 *추정값* (표준품셈 '별도 계상')",
        ],
    }


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("📊 cost_function() 테스트")
    print("=" * 60)
    
    # 테스트 1: 강원소나무 30→50년 개벌 (1ha)
    print("\n[테스트 1] 강원소나무 50년생 개벌 (1ha, 280m³)")
    print("-" * 60)
    result = cost_function(
        volume_m3=280,
        area_ha=1.0,
        distance_to_road_km=15,
        action="clearcut",
        skidding_distance_m=800,
        slope_class="중",
        species="강원지방소나무",
    )
    print(f"   📦 항목별 비용:")
    for item, cost in result["breakdown"].items():
        unit = result["unit_costs"].get(f"{item}_per_m3") or result["unit_costs"].get(f"{item}_per_ha", "-")
        print(f"      {item:>10}: {cost:>12,}원  (단가: {unit}원)")
    print(f"   ─" * 20)
    print(f"   직접비:      {result['subtotal']:>12,}원")
    print(f"   간접비(15%): {result['admin_overhead_amount']:>12,}원")
    print(f"   ═" * 20)
    print(f"   ✅ 총 비용:  {result['total']:>12,}원")
    print(f"   📌 묘목 단가: {result['unit_costs']['seedling_unit']}원/본 (강원지방소나무, 산림청 2025)")
    
    # 테스트 2: 간벌 (수확 50%)
    print("\n[테스트 2] 간벌 (140m³, 1ha)")
    print("-" * 60)
    result2 = cost_function(
        volume_m3=140,
        area_ha=1.0,
        distance_to_road_km=15,
        action="thinning",
        skidding_distance_m=800,
        slope_class="중",
    )
    print(f"   ✅ 총 비용:  {result2['total']:>12,}원")
    print(f"   📌 간벌은 regen *없음* (재조림 안 함)")
    
    # 테스트 3: 거리 영향 비교
    print("\n[테스트 3] 도로 거리별 비용 비교 (개벌 280m³, 1ha)")
    print("-" * 60)
    for dist_km in [5, 30, 100, 200, 300]:
        r = cost_function(
            volume_m3=280, area_ha=1.0,
            distance_to_road_km=dist_km, action="clearcut",
            skidding_distance_m=800, slope_class="중",
            species="강원지방소나무",
        )
        print(f"   도로 {dist_km:>3}km: 총 {r['total']:>11,}원  "
              f"(운반 단가: {r['unit_costs']['transport_per_m3']:,}원/m³)")
    
    # 테스트 4: 경사도 영향
    print("\n[테스트 4] 경사도 영향 (개벌 280m³, 1ha, 거리 15km)")
    print("-" * 60)
    for slope, label in [("완", "<15°"), ("중", "15-30°"), ("급", ">30°")]:
        r = cost_function(
            volume_m3=280, area_ha=1.0,
            distance_to_road_km=15, action="clearcut",
            skidding_distance_m=800, slope_class=slope,
            species="강원지방소나무",
        )
        print(f"   {label:>8} ({slope}): 총 {r['total']:>11,}원 "
              f"(할증 {r['slope_surcharge_applied']*100:.0f}%)")
    
    # 테스트 5: 수종별 조림비용 차이 (산림청 2025 공식 묘목가격)
    print("\n[테스트 5] 수종별 조림비용 차이 (개벌 200m³, 1ha, 15km)")
    print("-" * 60)
    for sp in ["강원지방소나무", "잣나무", "낙엽송", "리기다소나무", "편백", "상수리나무", "백합나무"]:
        r = cost_function(
            volume_m3=200, area_ha=1.0,
            distance_to_road_km=15, action="clearcut",
            skidding_distance_m=800, slope_class="중",
            species=sp,
        )
        seed = r["unit_costs"]["seedling_unit"]
        print(f"   {sp:>12} ({seed:>5}원/본): regen {r['breakdown']['regen']:>11,}원, "
              f"총 {r['total']:>11,}원")
    
    # 수종 미제공 시 기본값
    r = cost_function(
        volume_m3=200, area_ha=1.0,
        distance_to_road_km=15, action="clearcut",
        skidding_distance_m=800, slope_class="중",
    )
    print(f"   {'(미제공)':>12} ({r['unit_costs']['seedling_unit']:>5}원/본, 평균): "
          f"regen {r['breakdown']['regen']:>11,}원, 총 {r['total']:>11,}원")
    
    print()
    print("=" * 60)
    print("✅ cost_function() 작동 확인")
    print("=" * 60)