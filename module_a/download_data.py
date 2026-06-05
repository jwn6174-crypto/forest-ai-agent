"""
download_data.py — Module A 대용량 위성 데이터 로컬 다운로드.

보은 전역 위성 합성 래스터 `boeun_satellite_features_10m.tif` 는 541MB 라
GitHub 에 올리지 않는다(저장소엔 6MB 학습 CSV 만 포함). 이 스크립트는
그 래스터를 로컬 `module_a/data/` 로 받아 `predict_stand()` 가 'live' 로
돌게 한다.

사용:
    python module_a/download_data.py

동작:
    1) 저장소에 이미 있는 학습 CSV 존재를 확인한다.
    2) 래스터가 이미 있으면 건너뛴다.
    3) 래스터 출처가 설정돼 있으면(아래 둘 중 하나) 내려받는다:
         · 환경변수 BOEUN_RASTER_URL = 직접 다운로드 URL, 또는
         · 환경변수 BOEUN_RASTER_GDRIVE_ID = 구글드라이브 파일 ID, 또는
         · 이 파일 상단의 _RASTER_GDRIVE_ID 상수(민석이 채움)
       설정이 없으면, 받는 방법 두 가지를 안내만 한다.

참고: 래스터가 없어도 predict_stand() 는 학습 데이터 평균값(confidence='low')
으로 폴백하고, api_server 는 Module A 를 mock 으로 처리하므로 시스템은 정상
기동한다. 이 스크립트는 'live' 위성 추론을 켜기 위한 편의 도구다.
"""

import os
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
RASTER_PATH = DATA_DIR / "boeun_satellite_features_10m.tif"
TRAIN_CSV = DATA_DIR / "boeun_gedi_training_clean.csv"

# ── 래스터 출처 (민석: 둘 중 하나만 채우면 끝) ─────────────────────────
# 구글드라이브에 541MB .tif 를 올렸다면 그 파일 ID 를 여기에:
_RASTER_GDRIVE_ID = ""          # 예: "1A2b3C..." (드라이브 공유링크의 id 부분)
# 또는 직접 다운로드 URL 이 있으면 환경변수 BOEUN_RASTER_URL 로 넘긴다.

# 541MB ± 여유. 받은 파일이 이보다 한참 작으면 실패(HTML 에러 등)로 간주.
_MIN_BYTES = 100 * 1024 * 1024  # 100MB


def _ok(path: Path) -> bool:
    return path.exists() and path.stat().st_size >= _MIN_BYTES


def _download_via_url(url: str) -> bool:
    import requests
    print(f"  ↓ URL 에서 다운로드: {url[:60]}…")
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        tmp = RASTER_PATH.with_suffix(".tif.part")
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                if chunk:
                    f.write(chunk)
        tmp.replace(RASTER_PATH)
    return _ok(RASTER_PATH)


def _download_via_gdrive(file_id: str) -> bool:
    try:
        import gdown
    except ImportError:
        print("  ⚠️  gdown 미설치 — `pip install gdown` 후 다시 실행하세요.")
        return False
    print(f"  ↓ 구글드라이브에서 다운로드 (id={file_id})")
    gdown.download(id=file_id, output=str(RASTER_PATH), quiet=False)
    return _ok(RASTER_PATH)


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 64)
    print("Module A 데이터 점검 / 다운로드")
    print("=" * 64)

    # 1) 학습 CSV (저장소 포함)
    print(f"  학습 CSV : {'있음' if TRAIN_CSV.exists() else '없음 ❌ (저장소에 있어야 정상)'}  {TRAIN_CSV.name}")

    # 2) 래스터 (대용량, 저장소 미포함)
    if _ok(RASTER_PATH):
        size_mb = RASTER_PATH.stat().st_size / 1e6
        print(f"  래스터   : 이미 있음 ({size_mb:.0f}MB) — 다운로드 생략. ✅ Module A live 가능")
        return 0

    url = os.environ.get("BOEUN_RASTER_URL", "").strip()
    gid = os.environ.get("BOEUN_RASTER_GDRIVE_ID", "").strip() or _RASTER_GDRIVE_ID.strip()

    ok = False
    try:
        if url:
            ok = _download_via_url(url)
        elif gid:
            ok = _download_via_gdrive(gid)
    except Exception as e:
        print(f"  ❌ 다운로드 실패: {e}")
        ok = False

    if ok:
        print(f"  래스터   : 다운로드 완료 ✅  {RASTER_PATH}")
        return 0

    # 출처 미설정 → 안내만
    print("  래스터   : 없음 — 출처가 설정되지 않았습니다.")
    print("")
    print("  받는 방법 (둘 중 하나):")
    print("   (A) 구글드라이브: 민석이 올린 .tif 파일 ID 를 환경변수로 지정 후 재실행")
    print("        Windows PowerShell:  $env:BOEUN_RASTER_GDRIVE_ID='파일ID'; python module_a/download_data.py")
    print("        (또는 이 파일 상단 _RASTER_GDRIVE_ID 에 직접 기입)")
    print("   (B) GEE export: module_a/README.md 의 'boeun_satellite_features_10m.tif' 절차로")
    print("        Google Earth Engine 에서 직접 export → module_a/data/ 에 저장")
    print("")
    print("  ※ 래스터가 없어도 predict_stand() 는 학습 평균값(confidence='low')으로")
    print("     동작하고, api_server 는 Module A 를 mock 으로 처리하므로 시스템은 정상 기동합니다.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
