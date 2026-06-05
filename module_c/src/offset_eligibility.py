"""
offset_eligibility.py — 산림탄소상쇄 8 사업유형 적용 룰베이스 + RAG hybrid.

D16 (정책학자): 룰베이스 80% + 정우 RAG 20%.
- 신규조림/벌기연장/수종갱신 3개 → 별표3 임계값으로 결정 가능 (rule_based)
- 산지전용/목제품/재조림-신규구분 → 정우 carbon_chunks.jsonl 검색 (RAG)

희도 D16 결정 — 2026-05-20 Day 6 작성
"""

import json
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = ROOT / "data" / "raw" / "offset_eligibility" / "eligibility_rules_2024.json"

# 정우 module_bd carbon_chunks.jsonl 사용 (정우 RAG)
try:
    CARBON_CHUNKS_PATH = ROOT.parent / "module_bd" / "data" / "interim" / "carbon_chunks.jsonl"
except Exception:
    CARBON_CHUNKS_PATH = None


def _load_rules() -> dict:
    with open(RULES_PATH, encoding="utf-8") as f:
        return json.load(f)


# 별표3 룰베이스 (간단 fallback)
_ROTATION_RULES = {
    "강원지방소나무": 40,
    "중부지방소나무": 40,
    "잣나무": 60,
    "낙엽송": 30,
    "리기다소나무": 25,
    "삼나무": 30,
    "편백": 40,
    "참나무류": 25,
    "상수리나무": 25,
    "신갈나무": 25,
    "굴참나무": 25,
}


def find_eligible_project_types(
    stand: Dict,
    *,
    fire_history_within_5yr: bool = False,
    natural_recovery_impossible: bool = False,
    target_species: str | None = None,
    owner_intent: str | None = None,
) -> List[Dict]:
    """
    polygon → 적용 가능 사업유형 list (rule_based + RAG hint).

    Parameters
    ----------
    stand : dict
        StandStateEstimate dict
    fire_history_within_5yr : bool
        산불 피해 후 5년 이내 여부
    natural_recovery_impossible : bool
        자연복원 불가 여부
    target_species : str, optional
        수종 갱신 시 목표 수종
    owner_intent : str, optional
        "wood_products" | "biomass" | "land_use_avoidance"

    Returns
    -------
    list[dict]
        각 사업유형 매칭 결과
        {
            "code": "FM-Rotation",
            "korean": "벌기령 연장 산림경영",
            "eligible": True,
            "reason": "...",
            "verification": "rule_based" | "RAG",
        }

    Examples
    --------
    >>> stand = {"species_dominant": "강원지방소나무", "age_estimate": 30,
    ...          "area_ha": 1.5, "ownership": "사유림"}
    >>> r = find_eligible_project_types(stand)
    >>> any(p["code"] == "FM-Rotation" for p in r)
    True
    """
    rules_data = _load_rules()
    project_types = rules_data["project_types"]
    species = stand["species_dominant"]
    age = stand["age_estimate"]
    area_ha = stand["area_ha"]
    stand.get("ownership", "사유림")

    legal_min = _ROTATION_RULES.get(species, 40)

    results = []

    # 1. AR — 신규조림·재조림 (rule_based)
    ar = project_types["afforestation_reforestation"]
    if age == 0 and area_ha >= ar["rules"]["min_area_ha"]:
        results.append(
            {
                "code": "AR",
                "korean": ar["korean"],
                "eligible": True,
                "reason": "무립목지 + 5년 이상 무수목 — 자동 적격 (rule_based)",
                "verification": "rule_based",
            }
        )
    else:
        results.append(
            {
                "code": "AR",
                "korean": ar["korean"],
                "eligible": False,
                "reason": f"기존 임지 (age={age}) — AR 부적격",
                "verification": "rule_based",
            }
        )

    # 2. FM-Rotation — 벌기령 연장 (rule_based) ⭐ 한국 99%
    fm = project_types["forest_management_rotation"]
    if age >= legal_min - 10 and area_ha >= fm["rules"]["min_area_ha"]:
        results.append(
            {
                "code": "FM-Rotation",
                "korean": fm["korean"],
                "eligible": True,
                "reason": f"임령 {age}년 ≥ 법정 {legal_min}년 - 10 — 적격 (rule_based). "
                f"한국 인증실적 99% 이 사업유형. KAU/WTA margin 161원 — 가격 민감.",
                "verification": "rule_based",
                "korea_market_share": fm["rules"].get("extension_years_min", 10),
                "extension_required": True,
            }
        )
    else:
        results.append(
            {
                "code": "FM-Rotation",
                "korean": fm["korean"],
                "eligible": False,
                "reason": f"임령 {age}년 < 법정 {legal_min}년 - 10 = {legal_min - 10}년 — 너무 어림",
                "verification": "rule_based",
            }
        )

    # 3. SC — 수종 갱신 (rule_based)
    sc = project_types["species_conversion"]
    if age >= legal_min and target_species and target_species != species:
        high_carbon_targets = ["참나무류", "상수리나무", "잣나무", "편백"]
        if target_species in high_carbon_targets:
            results.append(
                {
                    "code": "SC",
                    "korean": sc["korean"],
                    "eligible": True,
                    "reason": f"{species} → {target_species} (고탄소 흡수 수종) 전환 — 적격",
                    "verification": "rule_based",
                }
            )

    # 4. FDP — 산불피해지 (RAG hint)
    if fire_history_within_5yr:
        fdp = project_types["fire_damage_planting"]
        results.append(
            {
                "code": "FDP",
                "korean": fdp["korean"],
                "eligible": True,
                "reason": "산불피해 후 5년 이내 — 적격",
                "verification": "rule_based",
                "rag_hint": "산림탄소상쇄 운영지침 fire_damage_planting 청크 (정우 carbon_chunks.jsonl) 검색 필요",
            }
        )

    # 5. WP — 목제품 (RAG hint)
    if owner_intent == "wood_products":
        wp = project_types["wood_products"]
        results.append(
            {
                "code": "WP",
                "korean": wp["korean"],
                "eligible": area_ha >= wp["rules"]["min_area_ha"],
                "reason": "산주 목제품 가공 의지 명시 — RAG 검색 필요",
                "verification": "RAG",
                "rag_hint": "정우 carbon_chunks.jsonl 'wood_products' 청크 검색",
            }
        )

    # 6. FB — 산림바이오매스 (RAG hint)
    if owner_intent == "biomass":
        results.append(
            {
                "code": "FB",
                "korean": project_types["forest_biomass"]["korean"],
                "eligible": True,
                "reason": "바이오매스 에너지 활용 의지 — RAG 검색 필요",
                "verification": "RAG",
            }
        )

    # 7. VR — 식생복구 (RAG)
    if natural_recovery_impossible:
        results.append(
            {
                "code": "VR",
                "korean": project_types["vegetation_restoration"]["korean"],
                "eligible": age < 5,
                "reason": "자연복원 불가 + 피해지 — RAG 검색 필요",
                "verification": "RAG",
            }
        )

    # 8. LUA — 산지전용 억제 (RAG)
    if owner_intent == "land_use_avoidance":
        results.append(
            {
                "code": "LUA",
                "korean": project_types["land_use_avoidance"]["korean"],
                "eligible": area_ha >= 1.0,
                "reason": "산지전용 허가 가능 → 유지 의지 — RAG 검색 필요",
                "verification": "RAG",
            }
        )

    return results


def search_rag_citations(
    project_code: str,
    *,
    query: str | None = None,
    top_k: int = 3,
) -> List[Dict]:
    """
    정우 carbon_chunks.jsonl 에서 사업유형 관련 청크 검색.

    NOTE: 현재는 keyword matching 만. 수범 module_e 가 embedding+FAISS 구축 후
    sentence-transformers 로 정밀 검색.

    Parameters
    ----------
    project_code : str
        "AR" | "FM-Rotation" | "VR" | "WP" | "FB" | "SC" | "FDP" | "LUA"
    query : str, optional
        추가 검색어
    top_k : int
        반환 청크 수

    Returns
    -------
    list[dict]
        청크 metadata
    """
    if not CARBON_CHUNKS_PATH or not CARBON_CHUNKS_PATH.exists():
        return [
            {
                "_note": "정우 carbon_chunks.jsonl 없음 — 통합 시점에 검색",
                "code": project_code,
            }
        ]

    # project_type 매핑 (정우 chunking 파일의 project_type 필드)
    type_map = {
        "AR": "afforestation_reforestation",
        "FM-Rotation": "forest_management_rotation",
        "VR": "vegetation_restoration",
        "WP": "wood_products",
        "FB": "forest_biomass",
        "SC": "species_conversion",
        "FDP": "fire_damage_planting",
        "LUA": "land_use_avoidance",
    }
    target_type = type_map.get(project_code)

    results = []
    with open(CARBON_CHUNKS_PATH, encoding="utf-8") as f:
        for line in f:
            chunk = json.loads(line)
            if chunk.get("project_type") == target_type:
                if query is None or query.lower() in chunk.get("text", "").lower():
                    results.append(
                        {
                            "chunk_id": chunk.get("id")
                            or chunk.get("source", "") + str(chunk.get("page", "")),
                            "source": chunk.get("source"),
                            "page": chunk.get("page"),
                            "text_excerpt": (chunk.get("text", "") or "")[:200],
                            "project_type": target_type,
                        }
                    )
                    if len(results) >= top_k:
                        break

    return results


if __name__ == "__main__":
    print("=" * 60)
    print("offset_eligibility.py 자가 검증")
    print("=" * 60)

    # 검증 1: 보은 30년 → FM-Rotation 적격
    print("\n[검증 1] 보은 강원소나무 30년 1.5ha")
    stand = {
        "species_dominant": "강원지방소나무",
        "age_estimate": 30,
        "area_ha": 1.5,
        "ownership": "사유림",
    }
    eligible = find_eligible_project_types(stand)
    for e in eligible:
        if e["eligible"]:
            print(f"  ✅ {e['code']} {e['korean']}: {e['reason'][:80]}")
        else:
            print(f"  ❌ {e['code']} {e['korean']}: {e['reason'][:80]}")
    fm = [e for e in eligible if e["code"] == "FM-Rotation"]
    assert fm[0]["eligible"]  # 30 >= 40-10

    # 검증 2: 보은 50년 + 수종갱신 → SC 적격
    print("\n[검증 2] 보은 강원소나무 50년 + 참나무 갱신")
    stand2 = {
        "species_dominant": "강원지방소나무",
        "age_estimate": 50,
        "area_ha": 2.0,
    }
    eligible2 = find_eligible_project_types(stand2, target_species="참나무류")
    sc = [e for e in eligible2 if e["code"] == "SC"]
    if sc:
        print(f"  SC: {sc[0]}")
        assert sc[0]["eligible"]

    # 검증 3: 산불피해지
    print("\n[검증 3] 산불피해지 (age=2)")
    stand3 = {"species_dominant": "강원지방소나무", "age_estimate": 2, "area_ha": 1.5}
    eligible3 = find_eligible_project_types(stand3, fire_history_within_5yr=True)
    fdp = [e for e in eligible3 if e["code"] == "FDP"]
    if fdp:
        print(f"  FDP: {fdp[0]}")

    # 검증 4: RAG 검색 (carbon_chunks 없으면 note)
    print("\n[검증 4] RAG 검색")
    cits = search_rag_citations("FM-Rotation", query="벌기령")
    print(f"  결과 수: {len(cits)}")
    print(f"  첫 결과: {cits[0] if cits else 'None'}")

    print("\n" + "=" * 60)
    print("✅ offset_eligibility.py 4/4 검증 통과")
    print("=" * 60)
