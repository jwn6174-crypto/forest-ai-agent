"""
scenarios.py — 5 시나리오 T 계산 + 법정 벌기령 feasibility.

5 시나리오:
- 즉시:    T = age_now
- 5년:     T = age_now + 5
- 10년:    T = age_now + 10
- 연장KOC: T = max(legal_min + 10, age_now + 10) — 산림탄소상쇄 산림경영 사업유형
- 임산물:  T = age_now + 15 — 표고/송이 등 비목재 임산물 병행

법정 벌기령 (산림자원법 시행규칙 별표 3, 2023-06-27 개정):
- 강원지방소나무 사유림: 40년
- 잣나무 사유림: 60년
- 낙엽송 사유림: 30년
- 참나무류 사유림: 25년
- 포플러류 사유림: 3년

희도 D10 결정 — stand_state_mock 3단 fallback chain 의 시나리오 분기.
"""

from typing import Literal, Tuple

# 정우 D 모듈 rotation_age 시그니처 변경 흡수 (5/28 commit):
# - 반환 dict (이전 int): {"rotation_age": int, ...}
# - ownership: "공사유림" (이전 "사유림"), "국유림", "기업경영림"
try:
    from module_bd.src.legal_rotation import rotation_age as _jw_rotation_age

    def rotation_age(species: str, ownership: str = "공사유림") -> int:
        """정우 dict 반환 → int 추출 wrapper (D125 호환층)."""
        # 정우 "사유림" → "공사유림" 자동 매핑
        if ownership == "사유림":
            ownership = "공사유림"
        result = _jw_rotation_age(species, ownership)
        if isinstance(result, dict):
            return result.get("rotation_age") or 40
        return result or 40
except ImportError:

    def rotation_age(species: str, ownership: str = "공사유림") -> int:
        """Fallback — 정우 module_bd 미배포 시 별표 3 룰베이스 직접 사용."""
        # "사유림" → "공사유림" 정우 표준 매핑
        if ownership == "사유림":
            ownership = "공사유림"
        _RULES = {
            "강원지방소나무": {"공사유림": 40, "국유림": 60},
            "중부지방소나무": {"공사유림": 40, "국유림": 60},
            "잣나무": {"공사유림": 60, "국유림": 60},
            "낙엽송": {"공사유림": 30, "국유림": 50},
            "리기다소나무": {"공사유림": 25, "국유림": 30},
            "삼나무": {"공사유림": 30, "국유림": 50},
            "편백": {"공사유림": 40, "국유림": 60},
            "참나무류": {"공사유림": 25, "국유림": 60},
            "상수리나무": {"공사유림": 25, "국유림": 60},
            "신갈나무": {"공사유림": 25, "국유림": 60},
            "굴참나무": {"공사유림": 25, "국유림": 60},
            "포플러류": {"공사유림": 3, "국유림": 3},
            "이태리포플러": {"공사유림": 3, "국유림": 3},
            "기타 활엽수": {"공사유림": 40, "국유림": 60},
            "자작나무": {"공사유림": 40, "국유림": 60},
            "백합나무": {"공사유림": 40, "국유림": 60},
        }
        return _RULES.get(species, {}).get(ownership, 40)


Scenario = Literal["즉시", "5년", "10년", "연장KOC", "임산물", "간벌+10년"]

VALID_SCENARIOS = ["즉시", "5년", "10년", "연장KOC", "임산물", "간벌+10년"]
# D18 (경영자 deliberation 2026-05-19): 영세 사유림 7할이 간벌 보조사업 ha당
# 200-300만원 국고지원 받음. 모두베기보다 간벌+10년 키우기가 현장 모달 선택.


def scenario_T(
    scenario: Scenario,
    species: str,
    age_now: int,
    ownership: str = "사유림",
) -> int:
    """시나리오별 벌기령 (년) 계산."""
    legal_min = rotation_age(species, ownership)

    if scenario == "즉시":
        return age_now
    if scenario == "5년":
        return age_now + 5
    if scenario == "10년":
        return age_now + 10
    if scenario == "연장KOC":
        return max(legal_min + 10, age_now + 10)
    if scenario == "임산물":
        return age_now + 15
    if scenario == "간벌+10년":
        # 30-40% 본수 제거 → 잔존목 10년 더 키움 (산림학자: 잔존목 +10-15% growth)
        # 간벌 시점에 보조사업 수익 200-300만원/ha 발생
        return age_now + 10

    raise ValueError(f"알 수 없는 시나리오: {scenario}. 유효: {VALID_SCENARIOS}")


def scenario_feasibility(
    scenario: Scenario,
    species: str,
    age_now: int,
    T: int,
    ownership: str = "사유림",
) -> Tuple[bool, str | None]:
    """법정 기준벌기령 충족 여부 + 사유.

    Returns:
        (feasible: bool, note: Optional[str])
    """
    legal_min = rotation_age(species, ownership)
    # scenario_T() 는 *절대 벌채임령* 을 돌려준다(즉시=age_now, 10년=age_now+10).
    # 따라서 벌채 시점 임령 = T 그 자체다. age_now+T 로 더하면 age_now 가 이중
    # 계산되어, 벌기령 미달 임지(예: 30년생 소나무 즉시, 법정 40년)가 잘못
    # feasible 로 판정된다(test_feasibility_벌기령_미달 회귀). T 를 그대로 쓴다.
    harvest_age = T  # = 벌채 시점의 임령 (scenario_T 가 이미 절대 임령)

    if harvest_age >= legal_min:
        return True, None

    note = (
        f"벌채 임령 {harvest_age}년 < 법정 기준벌기령 {legal_min}년 ({species}, {ownership}). "
        f"산림자원법 시행규칙 별표 3 (2023-06-27 개정). "
        f"법적 예외 사유(재해·병해충 등) 없으면 벌채 불가."
    )
    return False, note


if __name__ == "__main__":
    # 스모크 테스트
    print("=" * 60)
    print("scenarios.py 자가 검증")
    print("=" * 60)

    # 강원지방소나무 30년 (보은 시나리오)
    print("\n[김씨 보은 강원지방소나무 30년]")
    for sc in VALID_SCENARIOS:
        T = scenario_T(sc, "강원지방소나무", 30)
        feasible, note = scenario_feasibility(sc, "강원지방소나무", 30, T)
        mark = "✅" if feasible else "❌"
        print(f"  {sc:6s} T={T:3d} {mark} {note or ''}")

    # 강원지방소나무 50년 (벌기령 도달)
    print("\n[박씨 보은 강원지방소나무 50년]")
    for sc in VALID_SCENARIOS:
        T = scenario_T(sc, "강원지방소나무", 50)
        feasible, note = scenario_feasibility(sc, "강원지방소나무", 50, T)
        mark = "✅" if feasible else "❌"
        print(f"  {sc:6s} T={T:3d} {mark}")

    # 낙엽송 25년 (진안)
    print("\n[진안 낙엽송 25년]")
    for sc in VALID_SCENARIOS:
        T = scenario_T(sc, "낙엽송", 25)
        feasible, note = scenario_feasibility(sc, "낙엽송", 25, T)
        mark = "✅" if feasible else "❌"
        print(f"  {sc:6s} T={T:3d} {mark}")

    print("\n" + "=" * 60)
    print("✅ scenarios.py 동작 확인")
    print("=" * 60)
