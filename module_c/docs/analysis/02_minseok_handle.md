# 민석 미시작 — Module C 의 입력 처리 전략

> 민석이 Module A (위성 AGB) 를 아직 시작하지 않은 상태에서
> Module C 가 발표·논문까지 학술적으로 valid 하게 작동하기 위한 전략.

**작성일**: 2026-05-19 (Day 5)
**근거**: `기반채팅/05_module_c_work_standard.html` §05

---

## 문제 정의

Manual 01·02·03 의 가정:
> "Person 2 (민석) 가 polygon 입력을 받아 `StandStateEstimate` 를 만들어 Module C 에 준다."

현실 (2026-05-19):
> 정우 repo `module_a/` 폴더 자체 없음. 민석 0 commit. 6/26 발표까지 38일.

→ Module C 는 입력을 *자체적으로 만들 수 있어야* 한다.

---

## 3단 Fallback Chain

### Strategy A — Hand-crafted Demo Polygon (시연용)

3개 polygon 을 정우의 `growth_predict()` 결과로 채워서 사전 계산.

| ID | 지역 | 수종 | 임령 | 면적 | 도로 | volume | confidence |
|---|---|---|---|---|---|---|---|
| boeun_pine_30y_1.5ha | 충북 보은 | 강원지방소나무 | 30년 | 1.5 ha | 12 km | 173 m³/ha | low |
| boeun_pine_50y_2ha | 충북 보은 | 강원지방소나무 | 50년 | 2.0 ha | 1.5 km | 281 m³/ha | low |
| jinan_larch_25y_5ha | 전북 진안 | 낙엽송 | 25년 | 5.0 ha | 2.0 km | 195 m³/ha | low |

**보은 30년 시나리오 (정우 README 김씨 기반)** :
- 정우 `growth_predict("강원지방소나무", SI=14, age_now=30)` = volume 173 m³/ha
- AGB = 173 × 0.42 (목재밀도) × 1.74 (BEF) = 126.5 Mg/ha
- C = 126.5 × 1.26 (R 비) × 0.51 (CF) = 81.3 tC/ha
- volume_q05 / q95 = ±20% (mock 분산)

→ 모든 demo 의 수치는 *정우 함수가 생성*. mock 이지만 호환성 100%.

**학술적 정직성**: `confidence_level = "low"`, `confidence_note = "Mock demo polygon. 민석 모듈 A
미완성 시 hand-craft"` 명시.

---

### Strategy B — NFI 표본점 Direct Lookup (학술 valid)

NFI 5·6·7차 임분조사표 마이크로데이터 (data.go.kr/15122903) 를 직접 다운로드.

**원리**:
- NFI 는 4×4 km 격자 표본점. 충북 보은 면적 583 km² → 약 36 표본점.
- polygon 의 centroid 가 표본점 1 km 이내면 그 표본점의 측정값을 직접 사용.
- 4×4 km 격자라 1 km 이내일 확률은 *(π·1²) / (4²) ≈ 19.6%*. 보은 36 표본점 중 7-8개 polygon 이 매칭.
- 매칭 안 되면 → Strategy C (임상도) 로 fallback.

**구현**:
```python
def _nfi_lookup(pnu, geom_wkt, radius_km=1.0) -> Optional[dict]:
    nfi = pd.read_parquet("module_c/data/raw/nfi_plots/nfi_7th_boeun.parquet")
    center = wkt.loads(geom_wkt).centroid
    nfi["dist_km"] = nfi.apply(
        lambda r: Point(r["lon"], r["lat"]).distance(center) * 111.0, axis=1)
    near = nfi[nfi.dist_km < radius_km].sort_values("dist_km")
    if len(near) == 0: return None
    p = near.iloc[0]
    return {
        "species_dominant": p["species"],
        "age_estimate": int(p["age"]),
        "volume_m3_per_ha": float(p["volume_per_ha"]),
        "volume_q05": float(p["volume_per_ha"]) * 0.85,  # NFI 5% CI
        "volume_q95": float(p["volume_per_ha"]) * 1.15,
        "confidence_level": "medium" if p["dist_km"] < 0.5 else "low",
        "confidence_note": f"NFI 표본점 {p['plot_id']} (거리 {p['dist_km']:.2f}km) 직접 사용",
    }
```

**학술 가치**: 한국 사유림 67% 가 영세 (<1ha). 위성 AGB 의 10m 픽셀 mixing 으로
정확도가 급락하는 영역. **NFI direct lookup 이 오히려 위성보다 적합**한 시나리오를 만들 수 있음.

→ 논문 Discussion 에 "위성 AGB 미시작이어도 NFI direct lookup 으로 의사결정 가능,
영세 사유림에 더 적합한 접근일 수 있음" 학술 기여로 변환.

---

### Strategy C — 임상도 (수종, 영급) Lookup (최후)

데이터:
- 임상도 1:25,000 (data.go.kr 3045619, 전국 SHP, CC0)
- 임상도 1:5,000 (nsdi.go.kr, 시도별)
- 컬럼: 임상(침/활/혼/죽), 주요수종, 영급 (I-VI), 경급, 소밀도(A/B/C)

**원리**:
- polygon ∩ 임상도 → (수종, 영급) 추출 → NFI 평균값 lookup table 적용
- 영급 III (21-30년) → 강원지방소나무 평균 volume 160 m³/ha 등

**우선순위 낮음** : NFI lookup 실패 polygon 의 fallback. 정확도 medium-low.

---

## 진입점 — `get_stand_state()`

`module_a.src.predict_stand()` 와 **동일 시그니처**. 민석이 시작하면 그대로 swap.

```python
# module_c/src/stand_state_mock.py
def get_stand_state(pnu=None, geom_wkt=None, mode="auto") -> StandStateEstimate:
    """
    민석 module_a.predict_stand() 의 drop-in replacement.

    mode='auto':
        1. module_a.src.predict_stand 시도 (민석 완성 시)
        2. NFI 표본점 1km 이내 direct lookup
        3. 임상도 (수종, 영급) lookup
        4. demo polygon hand-craft
    mode='demo': demo 강제 (시연용)
    mode='nfi':  NFI 강제 (학술 검증용)
    """
    if mode == "demo":
        return _demo(pnu)
    if mode == "nfi":
        return _nfi_lookup(pnu, geom_wkt) or _raise("NFI lookup failed")

    # auto: fallback chain
    try:
        from module_a.src.predict_stand import predict_stand
        return predict_stand(pnu=pnu, geom_wkt=geom_wkt)
    except (ImportError, ModuleNotFoundError):
        pass
    if r := _nfi_lookup(pnu, geom_wkt): return r
    if r := _imsangdo_lookup(pnu, geom_wkt): return r
    return _demo(pnu)
```

---

## 발표 시연 시나리오

| 시나리오 | mode | polygon | 강조 |
|---|---|---|---|
| 1. 김씨 보은 30년 소나무 | demo | boeun_pine_30y_1.5ha | "법정 40년 < 30년 → 즉시벌채 불가" |
| 2. 박씨 보은 50년 소나무 | demo | boeun_pine_50y_2ha | "벌기령 도달, 5 시나리오 trade-off" |
| 3. 진안 산림조합 polygon | nfi 또는 demo | jinan_larch_25y_5ha | "지역 확장 + NFI direct lookup 시연" |

만약 W5 까지 민석이 시작하면 → mode="auto" 가 자동으로 위성 결과 사용.
민석이 끝까지 미시작 → mode="demo" + mode="nfi" 둘 다 시연하여 *fallback 자체가 학술 기여*.

---

## 민석 unblock 시 인계 책임

내가 만든 `stand_state_mock.py` 를 민석이 받으면:
1. `module_a/src/predict_stand.py` 작성 → 동일 시그니처 반환
2. `_nfi_lookup()` 코드 그대로 활용 가능 (NFI 라벨이 위성 학습셋의 ground truth)
3. `DEMO_PARCELS` 의 polygon 좌표로 *위성 검증* 가능 (volume q05/q95 와 RF 출력 비교)

→ 내 mock 이 민석 작업의 **테스트 벤치** 가 됨. 단순 placeholder 가 아니라 실 가치.

---

## 변경 이력
- 2026-05-19 Day 5 — 3단 fallback 전략 정리, demo polygon 3개 정의
