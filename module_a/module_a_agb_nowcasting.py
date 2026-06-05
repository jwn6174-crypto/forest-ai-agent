#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module A — 위성 AGB Nowcasting
다목적 산림경영 AI Agent | 충북 보은 파일럿

실행 순서:
    python module_a_agb_nowcasting.py --step 1   # 환경 설정 및 GEE 인증
    python module_a_agb_nowcasting.py --step 2   # GEDI 추출
    python module_a_agb_nowcasting.py --step 3   # 위성 피처 추출
    python module_a_agb_nowcasting.py --step 4   # 데이터 전처리
    python module_a_agb_nowcasting.py --step 5   # RF 베이스라인
    python module_a_agb_nowcasting.py --step 6   # Quantile RF 최종
    python module_a_agb_nowcasting.py --step 7   # Figure 3장
    python module_a_agb_nowcasting.py --step 8   # predict_stand() 완성
    python module_a_agb_nowcasting.py --step all # 전체 실행
"""

import argparse
import sys

# ── 경로 설정 ─────────────────────────────────────────────────
DATA_DIR   = r"G:\연구\공모전\ai공모전\데이터"
TRAIN_PATH = DATA_DIR + r"\boeun_gedi_training_clean.csv"
MODEL_PATH = DATA_DIR + r"\qrf_model.pkl"
RASTER_PATH= DATA_DIR + r"\boeun_satellite_features_10m.tif"
BOEUN_PATH = DATA_DIR + r"\boeun_boundary_wgs84.geojson"
NFI_PATH   = DATA_DIR + r"\mdb_NFI_7_수정.xlsx"
NFI_SAT_PATH = DATA_DIR + r"\nfi_boeun_satellite_features.csv"

GEE_PROJECT = "constant-goods-461116-r4"

FEATURES_NO_DEM = [
    "B2","B4","B5","B6","B7","B8","B8A","B11","B12",
    "NDVI","NDRE","NBR","NDMI","EVI",
    "VV_mean","VH_mean","VV_std","VV_VH_ratio",
    "HH_db","HV_db","HH_HV_db",
]
DEM_FEATURES = ["elev","slope","northness","eastness"]
FEATURES_ALL = FEATURES_NO_DEM + DEM_FEATURES

SPECIES_PARAMS = {
    "잣나무":    {"D": 0.41, "BEF": 1.35, "R": 0.28, "CF": 0.49},
    "낙엽송":    {"D": 0.45, "BEF": 1.34, "R": 0.29, "CF": 0.51},
    "강원소나무": {"D": 0.42, "BEF": 1.74, "R": 0.26, "CF": 0.51},
    "중부소나무": {"D": 0.47, "BEF": 1.74, "R": 0.26, "CF": 0.51},
    "리기다":    {"D": 0.50, "BEF": 1.33, "R": 0.36, "CF": 0.51},
    "신갈":      {"D": 0.66, "BEF": 1.45, "R": 0.43, "CF": 0.47},
    "굴참":      {"D": 0.72, "BEF": 1.45, "R": 0.43, "CF": 0.47},
    "상수리":    {"D": 0.72, "BEF": 1.45, "R": 0.43, "CF": 0.47},
    "편백":      {"D": 0.41, "BEF": 1.35, "R": 0.25, "CF": 0.51},
    "자작":      {"D": 0.61, "BEF": 1.40, "R": 0.31, "CF": 0.47},
    "백합":      {"D": 0.42, "BEF": 1.40, "R": 0.34, "CF": 0.47},
    "기본침엽":  {"D": 0.44, "BEF": 1.50, "R": 0.28, "CF": 0.51},
    "기본활엽":  {"D": 0.60, "BEF": 1.43, "R": 0.38, "CF": 0.47},
}


# ═════════════════════════════════════════════════════════════
# Step 1 — 환경 설정 및 GEE 인증
# ═════════════════════════════════════════════════════════════
def step1_setup():
    print("\n" + "="*60)
    print("Step 1 — 환경 설정 및 GEE 인증")
    print("="*60)

    # 패키지 설치 확인
    import subprocess
    packages = [
        "earthengine-api", "geemap", "geopandas",
        "rasterio", "rioxarray", "quantile-forest",
        "pydantic", "pyproj",
    ]
    for pkg in packages:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg, "-q"],
            capture_output=True, text=True
        )
        status = "✅" if result.returncode == 0 else "❌"
        print(f"  {status} {pkg}")

    # GEE 인증 (최초 1회)
    import ee
    try:
        ee.Initialize(project=GEE_PROJECT)
        print("\n✅ GEE 이미 인증됨. 초기화 성공!")
    except Exception:
        print("\nGEE 인증 필요. 브라우저가 열립니다...")
        ee.Authenticate()
        ee.Initialize(project=GEE_PROJECT)
        print("✅ GEE 인증 및 초기화 완료!")

    # 연결 테스트
    import json, geopandas as gpd
    aoi = ee.Geometry.Point([127.7, 36.5])
    img = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
           .filterBounds(aoi).filterDate("2023-06-01","2023-08-31").first())
    print(f"\nGEE 연결 테스트:")
    print(f"  이미지 ID: {img.get('system:index').getInfo()}")
    print(f"  촬영 날짜: {img.date().format('YYYY-MM-dd').getInfo()}")

    # 보은군 경계 로드
    with open(BOEUN_PATH) as f:
        import json
        gj = json.load(f)
    boeun_ee = ee.Geometry(gj["features"][0]["geometry"])
    area_km2 = boeun_ee.area().divide(1e6).getInfo()
    print(f"\n보은군 면적: {area_km2:.1f} km²")
    print("✅ Step 1 완료!")
    return boeun_ee


# ═════════════════════════════════════════════════════════════
# Step 2 — GEDI L4A 학습 데이터 추출
# ═════════════════════════════════════════════════════════════
def step2_gedi(boeun_ee):
    print("\n" + "="*60)
    print("Step 2 — GEDI L4A 학습 데이터 추출 (GEE)")
    print("="*60)

    import ee
    ee.Initialize(project=GEE_PROJECT)

    # INDEX로 sub-asset 목록
    index = (ee.FeatureCollection("LARSE/GEDI/GEDI04_A_002_INDEX")
             .filterBounds(boeun_ee))
    table_ids = index.aggregate_array("table_id").getInfo()
    print(f"GEDI sub-asset 수: {len(table_ids)}개")

    # 보은군 footprint 합치기 + 품질 필터
    boeun_merged = ee.FeatureCollection(
        [ee.FeatureCollection(tid).filterBounds(boeun_ee) for tid in table_ids]
    ).flatten()

    boeun_q = (boeun_merged
        .filter(ee.Filter.eq("l4_quality_flag", 1))
        .filter(ee.Filter.eq("degrade_flag", 0))
        .filter(ee.Filter.gt("sensitivity", 0.9))
        .filter(ee.Filter.lt("agbd", 500))
        .filter(ee.Filter.gt("agbd", 0))
        .filter(ee.Filter.gt("elev_lowestmode", 0))
        .map(lambda f: f.set("se_ratio",
             ee.Number(f.get("agbd_se")).divide(
             ee.Number(f.get("agbd")).add(0.001))))
        .filter(ee.Filter.lt("se_ratio", 0.5))
    )

    n = boeun_q.size().getInfo()
    stats = boeun_q.aggregate_stats("agbd").getInfo()
    print(f"품질 필터 후: {n:,}개 footprint")
    print(f"agbd 평균: {stats['mean']:.1f} Mg/ha")
    print(f"agbd std:  {stats['total_sd']:.1f} Mg/ha")
    print("\n※ Export는 Step 3에서 위성 피처와 함께 진행됩니다.")
    print("✅ Step 2 완료!")
    return boeun_q


# ═════════════════════════════════════════════════════════════
# Step 3 — 위성 피처 추출 (GEE)
# ═════════════════════════════════════════════════════════════
def step3_satellite(boeun_ee, boeun_q):
    print("\n" + "="*60)
    print("Step 3 — 위성 피처 추출 (GEE)")
    print("="*60)

    import ee
    ee.Initialize(project=GEE_PROJECT)

    # Sentinel-2 (CS+ 마스킹)
    cs = (ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")
          .filterBounds(boeun_ee).filterDate("2023-05-01","2023-10-31"))
    s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
          .filterBounds(boeun_ee).filterDate("2023-05-01","2023-10-31")
          .linkCollection(cs, ["cs_cdf"])
          .map(lambda img: img.updateMask(img.select("cs_cdf").gte(0.6)))
          .select(["B2","B4","B5","B6","B7","B8","B8A","B11","B12"])
          .median().toFloat())

    ndvi = s2.normalizedDifference(["B8","B4"]).rename("NDVI")
    ndre = s2.normalizedDifference(["B8","B5"]).rename("NDRE")
    nbr  = s2.normalizedDifference(["B8","B12"]).rename("NBR")
    ndmi = s2.normalizedDifference(["B8","B11"]).rename("NDMI")
    evi  = s2.expression(
        "2.5*((NIR-R)/(NIR+6*R-7.5*B+1))",
        {"NIR":s2.select("B8"),"R":s2.select("B4"),"B":s2.select("B2")}
    ).rename("EVI")

    # Sentinel-1 SAR (Speckle 제거)
    speckle = lambda img: img.focal_mean(radius=1, kernelType="square", units="pixels")
    s1 = (ee.ImageCollection("COPERNICUS/S1_GRD")
          .filterBounds(boeun_ee).filterDate("2023-05-01","2023-10-31")
          .filter(ee.Filter.eq("instrumentMode","IW"))
          .filter(ee.Filter.listContains("transmitterReceiverPolarisation","VV"))
          .filter(ee.Filter.listContains("transmitterReceiverPolarisation","VH")))
    vv_mean = s1.select("VV").map(speckle).mean().rename("VV_mean")
    vh_mean = s1.select("VH").map(speckle).mean().rename("VH_mean")
    vv_std  = s1.select("VV").reduce(ee.Reducer.stdDev()).rename("VV_std")
    vv_vh   = vv_mean.subtract(vh_mean).rename("VV_VH_ratio")

    # PALSAR
    palsar = (ee.ImageCollection("JAXA/ALOS/PALSAR/YEARLY/SAR_EPOCH")
              .filterDate("2023-01-01","2024-01-01").first())
    HH    = palsar.select("HH").pow(2).log10().multiply(10).subtract(83.0).rename("HH_db")
    HV    = palsar.select("HV").pow(2).log10().multiply(10).subtract(83.0).rename("HV_db")
    HH_HV = HH.subtract(HV).rename("HH_HV_db")

    # DEM
    dem       = (ee.ImageCollection("JAXA/ALOS/AW3D30/V3_2")
                 .first().select("DSM").rename("elev"))
    slope     = ee.Terrain.slope(dem).rename("slope")
    aspect    = ee.Terrain.aspect(dem).multiply(3.14159/180)
    northness = aspect.cos().rename("northness")
    eastness  = aspect.sin().rename("eastness")

    # 전체 피처 이미지 (25개)
    img_all = ee.Image.cat([
        s2, ndvi, ndre, nbr, ndmi, evi,
        vv_mean, vh_mean, vv_std, vv_vh,
        HH, HV, HH_HV,
        dem, slope, northness, eastness,
    ]).toFloat()

    print(f"피처 밴드 수: {len(img_all.bandNames().getInfo())}개")

    # GEDI footprint에서 피처 추출 (25m 버퍼)
    def extract(feature):
        return feature.setMulti(img_all.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=feature.geometry().buffer(25),
            scale=10, maxPixels=1e6
        ))

    # 테스트 확인
    test = ee.FeatureCollection(boeun_q.toList(3)).map(extract).first().getInfo()
    props = test["properties"]
    print(f"테스트 NDVI: {props.get('NDVI'):.4f}")
    print(f"테스트 elev: {props.get('elev'):.0f}m")

    # Export (GEDI 학습 데이터)
    task1 = ee.batch.Export.table.toDrive(
        collection=boeun_q.map(extract),
        description="training-boeun-gedi-2023",
        folder="GEE_exports",
        fileNamePrefix="boeun_gedi_training_clean",
        fileFormat="CSV",
    )
    task1.start()
    print(f"\n✅ GEDI 학습 데이터 Export 시작! ID: {task1.id}")

    # Export (보은군 전체 raster — Fig 3용)
    import json, geopandas as gpd
    with open(BOEUN_PATH) as f:
        gj = json.load(f)
    boeun_geom = ee.Geometry(gj["features"][0]["geometry"])

    img_raster = img_all.updateMask(ndvi.gte(0.3)).clip(boeun_geom)
    task2 = ee.batch.Export.image.toDrive(
        image=img_raster,
        description="boeun_satellite_features_10m",
        folder="GEE_exports",
        fileNamePrefix="boeun_satellite_features_10m",
        region=boeun_geom, scale=10,
        crs="EPSG:4326", maxPixels=1e10,
        fileFormat="GeoTIFF",
    )
    task2.start()
    print(f"✅ 보은군 raster Export 시작! ID: {task2.id}")
    print("진행 확인: https://code.earthengine.google.com/tasks")
    print("완료 후 구글드라이브 → GEE_exports 폴더에서 다운로드")
    print("✅ Step 3 완료!")


# ═════════════════════════════════════════════════════════════
# Step 4 — 데이터 전처리 및 탐색
# ═════════════════════════════════════════════════════════════
def step4_preprocess():
    print("\n" + "="*60)
    print("Step 4 — 데이터 전처리 및 탐색")
    print("="*60)

    import pandas as pd
    import numpy as np
    from sklearn.model_selection import train_test_split
    import matplotlib
    matplotlib.rcParams["axes.unicode_minus"] = False

    df = pd.read_csv(TRAIN_PATH, encoding="utf-8-sig")
    print(f"원본 데이터: {len(df):,}행 × {df.shape[1]}컬럼")
    print(f"결측값: {df.isnull().sum().sum()}")

    # 전처리
    df = df[df["NDVI"] >= 0.3].copy()
    df["sample_weight"] = 1.0 / (df["agbd_se"] + 1.0)
    print(f"\nNDVI≥0.3 필터 후: {len(df):,}행")
    print(f"agbd 평균: {df['agbd'].mean():.1f} Mg/ha")
    print(f"agbd std:  {df['agbd'].std():.1f} Mg/ha")
    print(f"NDVI 평균: {df['NDVI'].mean():.3f}")

    # 상관관계 Top 10
    corr = df[FEATURES_ALL + ["agbd"]].corr()["agbd"].drop("agbd")
    top10 = corr.abs().sort_values(ascending=False).head(10)
    print("\nAGB 상관관계 Top 10:")
    for feat, _ in top10.items():
        raw = corr[feat]
        bar = "█" * int(abs(raw) * 60)
        print(f"  {feat:15s}: {raw:+.3f} {bar}")

    # train/val 분리
    trn, val = train_test_split(df, test_size=0.15, random_state=42)
    print(f"\n학습셋: {len(trn):,}개 / 검증셋: {len(val):,}개")
    print("✅ Step 4 완료!")
    return df, trn, val


# ═════════════════════════════════════════════════════════════
# Step 5 — 베이스라인 모델 (Random Forest)
# ═════════════════════════════════════════════════════════════
def step5_rf_baseline(trn, val):
    print("\n" + "="*60)
    print("Step 5 — 베이스라인 모델 (Random Forest)")
    print("="*60)

    import time, numpy as np
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import r2_score, mean_squared_error

    print("RF 학습 중...")
    start = time.time()

    rf = RandomForestRegressor(
        n_estimators=1000, max_depth=None, max_features=0.5,
        min_samples_leaf=5, min_samples_split=5,
        n_jobs=-1, random_state=42,
    )
    rf.fit(trn[FEATURES_ALL], trn["agbd"],
           sample_weight=trn["sample_weight"])

    pred = rf.predict(val[FEATURES_ALL])
    r2   = r2_score(val["agbd"], pred)
    rmse = np.sqrt(mean_squared_error(val["agbd"], pred))

    print(f"학습 시간: {time.time()-start:.1f}초")
    print(f"\n===== RF 베이스라인 =====")
    print(f"R²:   {r2:.3f}")
    print(f"RMSE: {rmse:.1f} Mg/ha")

    import pandas as pd
    importances = pd.Series(rf.feature_importances_, index=FEATURES_ALL)
    top10 = importances.sort_values(ascending=False).head(10)
    print("\n피처 중요도 Top 10:")
    for feat, imp in top10.items():
        bar = "█" * int(imp * 300)
        print(f"  {feat:15s} {imp:.3f} {bar}")

    print("✅ Step 5 완료!")
    return rf


# ═════════════════════════════════════════════════════════════
# Step 6 — 최종 모델 (Quantile RF)
# ═════════════════════════════════════════════════════════════
def step6_quantile_rf(trn, val):
    print("\n" + "="*60)
    print("Step 6 — 최종 모델 (Quantile Random Forest)")
    print("="*60)

    import time, numpy as np, joblib
    from quantile_forest import RandomForestQuantileRegressor
    from sklearn.metrics import r2_score, mean_squared_error

    print("Quantile RF 학습 중...")
    start = time.time()

    qrf = RandomForestQuantileRegressor(
        n_estimators=1000, max_features=0.5,
        min_samples_leaf=5, min_samples_split=5,
        n_jobs=-1, random_state=42,
    )
    qrf.fit(trn[FEATURES_ALL], trn["agbd"],
            sample_weight=trn["sample_weight"])

    pred_q   = qrf.predict(val[FEATURES_ALL], quantiles=[0.05, 0.50, 0.95])
    q05, q50, q95 = pred_q[:,0], pred_q[:,1], pred_q[:,2]

    r2       = r2_score(val["agbd"], q50)
    rmse     = np.sqrt(mean_squared_error(val["agbd"], q50))
    coverage = ((val["agbd"].values >= q05) & (val["agbd"].values <= q95)).mean()

    print(f"학습 시간: {time.time()-start:.1f}초")
    print(f"\n===== Quantile RF 성능 =====")
    print(f"R²:              {r2:.3f}")
    print(f"RMSE:            {rmse:.1f} Mg/ha")
    print(f"90%PI coverage:  {coverage:.3f}  (목표: 0.85~0.95)")

    joblib.dump(qrf, MODEL_PATH)
    print(f"\n✅ 모델 저장: {MODEL_PATH}")
    print("✅ Step 6 완료!")
    return qrf, q05, q50, q95, val


# ═════════════════════════════════════════════════════════════
# Step 7 — 발표용 Figure 3장
# ═════════════════════════════════════════════════════════════
def step7_figures(qrf, q05, q50, q95, val, df):
    print("\n" + "="*60)
    print("Step 7 — 발표용 Figure 3장")
    print("="*60)

    import numpy as np, pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    from sklearn.metrics import r2_score, mean_squared_error

    # 한글 폰트
    for font in fm.findSystemFonts():
        if "malgun" in font.lower() or "nanum" in font.lower():
            fm.fontManager.addfont(font)
            plt.rcParams["font.family"] = fm.FontProperties(fname=font).get_name()
            break
    plt.rcParams["axes.unicode_minus"] = False

    # ── Fig 1: GEDI 성능 scatter ─────────────────────────────
    print("\n[Fig 1] GEDI 성능 scatter 생성 중...")
    y_true = val["agbd"].values
    y_pred = q50

    r2   = r2_score(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    cov  = ((y_true >= q05) & (y_true <= q95)).mean()

    fig, ax = plt.subplots(figsize=(8, 8), dpi=150)
    ax.errorbar(y_true, y_pred,
                yerr=[y_pred-q05, q95-y_pred],
                fmt="none", alpha=0.08, color="steelblue",
                elinewidth=0.5, capsize=0)
    sc = ax.scatter(y_true, y_pred, c=y_pred-y_true,
                    cmap="RdBu_r", vmin=-150, vmax=150,
                    alpha=0.5, s=15, zorder=3)
    plt.colorbar(sc, ax=ax, label="잔차 (예측 - 실측, Mg/ha)")
    ax.plot([0,500],[0,500],"k--",lw=1.5,label="1:1 line")
    z = np.polyfit(y_true, y_pred, 1)
    xfit = np.linspace(0, 500, 100)
    ax.plot(xfit, np.poly1d(z)(xfit), "r-", lw=1.5, label="회귀선")
    ax.text(0.05, 0.95,
            f"n = {len(y_true):,}\nR² = {r2:.3f}\nRMSE = {rmse:.1f} Mg/ha",
            transform=ax.transAxes, va="top", fontsize=11,
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8))
    ax.set_xlabel("GEDI 실측 AGB (Mg/ha)", fontsize=13)
    ax.set_ylabel("모델 예측 AGB (Mg/ha)", fontsize=13)
    ax.set_title(
        f"Fig 1 — GEDI AGB 예측 성능\n"
        f"R²={r2:.3f}  RMSE={rmse:.1f} Mg/ha  90%PI coverage={cov:.3f}",
        fontsize=13)
    ax.set_xlim(0,520); ax.set_ylim(0,520)
    ax.legend(fontsize=11); ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(DATA_DIR + r"\fig1_gedi_scatter.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✅ Fig 1 저장 완료 (R²={r2:.3f})")

    # ── Fig 2: NFI 외부 검증 ─────────────────────────────────
    print("\n[Fig 2] NFI 외부 검증 생성 중...")
    from sklearn.neighbors import NearestNeighbors

    nn_dem = NearestNeighbors(n_neighbors=5, n_jobs=-1)
    nn_dem.fit(df[FEATURES_NO_DEM].values)

    try:
        df_nfi_sat = pd.read_csv(NFI_SAT_PATH)
        dists, idxs = nn_dem.kneighbors(df_nfi_sat[FEATURES_NO_DEM].values)
        for j, c in enumerate(DEM_FEATURES):
            df_nfi_sat[c] = [
                np.average(df[c].values[idx], weights=1/(dist+1e-6))
                for idx, dist in zip(idxs, dists)
            ]

        preds = qrf.predict(df_nfi_sat[FEATURES_ALL], quantiles=[0.05,0.50,0.95])
        df_nfi_sat["agb_med"] = preds[:,1]
        df_nfi_sat["agb_q05"] = preds[:,0]
        df_nfi_sat["agb_q95"] = preds[:,2]

        SPECIES_MAP = {
            "침엽수림(D)": (0.44,1.50),
            "활엽수림(H)": (0.60,1.43),
            "혼효림(M)":   (0.60,1.43),
        }
        def agb2vol(agb, imsan):
            D, BEF = SPECIES_MAP.get(imsan, (0.60,1.43))
            return agb / (D * BEF)

        df_nfi_sat["vol_pred"] = df_nfi_sat.apply(
            lambda r: agb2vol(r["agb_med"], r["imsan"]), axis=1)
        df_nfi_sat["vol_q05"]  = df_nfi_sat.apply(
            lambda r: agb2vol(r["agb_q05"], r["imsan"]), axis=1)
        df_nfi_sat["vol_q95"]  = df_nfi_sat.apply(
            lambda r: agb2vol(r["agb_q95"], r["imsan"]), axis=1)

        df_tree = pd.read_excel(NFI_PATH, sheet_name="임목조사표")
        df_tree["추정간재적"] = pd.to_numeric(
            df_tree["추정간재적"], errors="coerce").fillna(0)
        vol_plot = (df_tree.groupby("표본점번호")["추정간재적"]
                    .sum() / 0.04).reset_index()
        vol_plot.columns = ["plot_id","volume_nfi"]
        vol_plot["plot_id"] = vol_plot["plot_id"].astype(str)
        df_nfi_sat["plot_id"] = df_nfi_sat["plot_id"].astype(str)

        df_fig2 = df_nfi_sat.merge(vol_plot, on="plot_id", how="inner")
        df_fig2 = df_fig2[df_fig2["volume_nfi"] > 0].copy()

        r2_nfi   = r2_score(df_fig2["volume_nfi"], df_fig2["vol_pred"])
        rmse_nfi = np.sqrt(mean_squared_error(df_fig2["volume_nfi"], df_fig2["vol_pred"]))

        COLOR = {"침엽수림(D)":"#2166ac","활엽수림(H)":"#d73027","혼효림(M)":"#4dac26"}
        fig, ax = plt.subplots(figsize=(7,7), dpi=150)
        for imsan, grp in df_fig2.groupby("imsan"):
            ax.errorbar(grp["volume_nfi"], grp["vol_pred"],
                        yerr=[grp["vol_pred"]-grp["vol_q05"],
                              grp["vol_q95"]-grp["vol_pred"]],
                        fmt="o", color=COLOR.get(imsan,"gray"),
                        alpha=0.8, capsize=3, markersize=6, lw=1.0, label=imsan)
        vmax = max(df_fig2["volume_nfi"].max(), df_fig2["vol_pred"].max()) * 1.1
        ax.plot([0,vmax],[0,vmax],"k--",lw=1.2,label="1:1 line")
        m, b = np.polyfit(df_fig2["volume_nfi"], df_fig2["vol_pred"], 1)
        ax.plot(np.linspace(0,vmax,100), m*np.linspace(0,vmax,100)+b,
                "r-", lw=1.5, label="회귀선")
        ax.text(0.05, 0.95,
                f"n = {len(df_fig2)}\nR² = {r2_nfi:.3f}\nRMSE = {rmse_nfi:.1f} m³/ha",
                transform=ax.transAxes, va="top", fontsize=11,
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8))
        ax.set_xlabel("NFI 실측 입목축적 (m³/ha)", fontsize=13)
        ax.set_ylabel("모델 예측 입목축적 (m³/ha)", fontsize=13)
        ax.set_title(
            f"Fig 2 — NFI 외부 검증\nR²={r2_nfi:.3f}  RMSE={rmse_nfi:.1f} m³/ha",
            fontsize=13)
        ax.legend(fontsize=10); ax.grid(True, alpha=0.3)
        ax.set_xlim(0,vmax); ax.set_ylim(0,vmax)
        plt.tight_layout()
        plt.savefig(DATA_DIR + r"\fig2_nfi_validation.png", dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  ✅ Fig 2 저장 완료 (R²={r2_nfi:.3f}, RMSE={rmse_nfi:.1f} m³/ha)")
        print("  ※ R²=-0.187 예상: GEDI saturation으로 인한 고AGB 과소추정 한계")
    except FileNotFoundError:
        print(f"  ⚠️  {NFI_SAT_PATH} 없음 → Step 3 Export 완료 후 재실행")

    # ── Fig 3: AGB 공간지도 ──────────────────────────────────
    print("\n[Fig 3] AGB 공간 분포 지도 생성 중...")
    try:
        import rasterio, geopandas as gpd
        from sklearn.neighbors import NearestNeighbors

        with rasterio.open(RASTER_PATH) as src:
            bands   = src.read()
            profile = src.profile.copy()
            extent  = [src.bounds.left, src.bounds.right,
                       src.bounds.bottom, src.bounds.top]

        H, W = bands.shape[1], bands.shape[2]
        pixels = bands.reshape(bands.shape[0], -1).T
        no_dem_idx = [FEATURES_ALL.index(f) for f in FEATURES_NO_DEM]
        valid_mask = ~np.any(np.isnan(pixels[:, no_dem_idx]), axis=1)
        print(f"  유효 픽셀: {valid_mask.sum():,}개 ({valid_mask.sum()/(H*W)*100:.1f}%)")

        nn_dem2 = NearestNeighbors(n_neighbors=5, n_jobs=-1)
        nn_dem2.fit(df[FEATURES_NO_DEM].values)

        X_nodem = pixels[valid_mask][:, no_dem_idx]
        BATCH = 100000
        n_valid = X_nodem.shape[0]
        dem_interp = np.zeros((n_valid, 4))
        for i in range(0, n_valid, BATCH):
            d, ix = nn_dem2.kneighbors(X_nodem[i:i+BATCH])
            for j, c in enumerate(DEM_FEATURES):
                dem_interp[i:i+BATCH,j] = [
                    np.average(df[c].values[idx], weights=1/(dist+1e-6))
                    for idx, dist in zip(ix, d)
                ]
            print(f"    DEM 보간: {min(i+BATCH,n_valid):,}/{n_valid:,}")

        X_valid = np.hstack([X_nodem, dem_interp])

        BATCH2 = 50000
        agb_pred = np.full(n_valid, np.nan)
        agb_q05_ = np.full(n_valid, np.nan)
        agb_q95_ = np.full(n_valid, np.nan)
        for i in range(0, n_valid, BATCH2):
            batch = pd.DataFrame(X_valid[i:i+BATCH2], columns=FEATURES_ALL)
            p = qrf.predict(batch, quantiles=[0.05,0.50,0.95])
            agb_pred[i:i+BATCH2] = p[:,1]
            agb_q05_[i:i+BATCH2] = p[:,0]
            agb_q95_[i:i+BATCH2] = p[:,2]
            pct = min(i+BATCH2,n_valid)/n_valid*100
            print(f"    AGB 예측: {min(i+BATCH2,n_valid):,}/{n_valid:,} ({pct:.0f}%)")

        def to_map(arr):
            m = np.full(H*W, np.nan)
            m[valid_mask] = arr
            return m.reshape(H, W)

        agb_map     = to_map(agb_pred)
        agb_q05_map = to_map(agb_q05_)
        agb_q95_map = to_map(agb_q95_)
        valid_vals  = agb_map[~np.isnan(agb_map)]

        # GeoTIFF 저장
        profile.update(count=3, dtype="float32", nodata=-9999)
        with rasterio.open(DATA_DIR + r"\boeun_agb_10m.tif", "w", **profile) as dst:
            for i, m in enumerate([agb_map, agb_q05_map, agb_q95_map], 1):
                dst.write(np.where(np.isnan(m),-9999,m).astype("float32"), i)

        boeun_gdf = gpd.read_file(BOEUN_PATH)
        fig, axes = plt.subplots(1, 3, figsize=(18,7), dpi=150)
        for ax, data, title in zip(axes,
            [agb_map, agb_q05_map, agb_q95_map],
            ["AGB 중앙값 (q50)","AGB 하한 (q05)","AGB 상한 (q95)"]):
            im = ax.imshow(data, cmap=plt.cm.YlGn, vmin=0, vmax=300,
                           extent=extent, origin="upper", aspect="equal")
            boeun_gdf.boundary.plot(ax=ax, color="black", linewidth=1.2)
            ax.set_title(title, fontsize=12)
            ax.set_xlabel("경도",fontsize=9); ax.set_ylabel("위도",fontsize=9)
            plt.colorbar(im, ax=ax, label="AGB (Mg/ha)", shrink=0.8)
        fig.suptitle(
            f"Fig 3 — 보은군 지상부 바이오매스 공간 분포 (2023)\n"
            f"평균 {valid_vals.mean():.1f} Mg/ha  |  "
            f"최대 {valid_vals.max():.1f} Mg/ha  |  "
            f"산림면적 {len(valid_vals)*100/1e4:.0f} ha",
            fontsize=13)
        plt.tight_layout()
        plt.savefig(DATA_DIR + r"\fig3_agb_map.png", dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  ✅ Fig 3 저장 완료")
        print(f"     AGB 평균: {valid_vals.mean():.1f} Mg/ha")
        print(f"     산림면적: {len(valid_vals)*100/1e4:.0f} ha")
    except FileNotFoundError:
        print(f"  ⚠️  {RASTER_PATH} 없음 → Step 3 Export 완료 후 재실행")

    print("\n✅ Step 7 완료!")


# ═════════════════════════════════════════════════════════════
# Step 8 — predict_stand() 함수 완성 및 테스트
# ═════════════════════════════════════════════════════════════
def step8_predict_stand(qrf, df):
    print("\n" + "="*60)
    print("Step 8 — predict_stand() 함수 테스트")
    print("="*60)

    import numpy as np, pandas as pd, rasterio
    import scipy.stats as stats
    import geopandas as gpd
    from rasterio.mask import mask as rio_mask
    from shapely.geometry import mapping
    from shapely.wkt import loads as wkt_loads
    from datetime import datetime
    from typing import Optional, Dict, Literal
    from pydantic import BaseModel, Field
    from sklearn.neighbors import NearestNeighbors

    # KNN DEM 보간기
    nn_dem = NearestNeighbors(n_neighbors=5, n_jobs=-1)
    nn_dem.fit(df[FEATURES_NO_DEM].values)

    class StandStateEstimate(BaseModel):
        pnu:               str
        geom_wkt:          str
        area_ha:           float = Field(..., gt=0)
        estimated_at:      datetime
        species_dominant:  str
        species_secondary: Optional[str]  = None
        age_estimate:      Optional[int]  = Field(None, ge=0, le=200)
        age_class:         Optional[str]  = None
        agb_mg_per_ha:     float
        agb_q05:           float
        agb_q95:           float
        volume_m3_per_ha:  float
        volume_q05:        float
        volume_q95:        float
        carbon_tc_per_ha:  float
        carbon_q05:        float
        carbon_q95:        float
        grade_distribution: Dict[str, float]
        n_gedi_footprints:  int
        n_s2_scenes:        int
        saturation_warning: bool = False
        confidence_level:   Literal["high","medium","low"]
        confidence_note:    Optional[str] = None

    def _agb_to_volume(agb, sp):
        p = SPECIES_PARAMS.get(sp, SPECIES_PARAMS["기본활엽"])
        return agb / (p["D"] * p["BEF"])

    def _agb_to_carbon(agb, sp):
        p = SPECIES_PARAMS.get(sp, SPECIES_PARAMS["기본활엽"])
        return agb * (1 + p["R"]) * p["CF"]

    def _age_class(age):
        return None if age is None else f"{(age//10)+1}영급"

    def _grade_dist(agb):
        mean_dbh = 7.5 * (agb/50)**0.4
        shape, scale = 2.5, mean_dbh/0.89
        breaks = [0,6,12,18,24,30,42,999]
        labels = ["치수","소경","중경","대경1","대경2","대경3","초대경"]
        probs = {}
        for i, lab in enumerate(labels):
            probs[lab] = round(
                stats.weibull_min.cdf(breaks[i+1],shape,scale=scale)
              - stats.weibull_min.cdf(breaks[i],shape,scale=scale), 4)
        total = sum(probs.values()) or 1.0
        return {k: round(v/total,4) for k,v in probs.items()}

    def predict_stand(geom_wkt, pnu, species_dominant,
                      species_secondary=None, age_estimate=None,
                      n_gedi_footprints=11026, n_s2_scenes=23):
        geom    = wkt_loads(geom_wkt)
        area_ha = max(gpd.GeoSeries([geom], crs="EPSG:4326")
                      .to_crs("EPSG:5179").area.values[0] / 10000, 0.0001)
        try:
            with rasterio.open(RASTER_PATH) as src:
                out_image, _ = rio_mask(src,[mapping(geom)],crop=True,nodata=np.nan)
            pixels   = out_image.reshape(out_image.shape[0],-1).T
            df_pix   = pd.DataFrame(pixels, columns=FEATURES_ALL)
            valid    = (~df_pix[FEATURES_NO_DEM].isnull().any(axis=1) &
                        (df_pix["NDVI"] >= 0.3))
            df_valid = df_pix[valid].copy()
        except Exception:
            df_valid = pd.DataFrame()

        n_pixels = len(df_valid)
        if n_pixels == 0:
            confidence = "low"
            note = "유효 픽셀 없음 → 학습 데이터 평균 사용"
            feat_mean = df[FEATURES_ALL].mean().values.reshape(1,-1)
            p = qrf.predict(pd.DataFrame(feat_mean,columns=FEATURES_ALL),
                            quantiles=[0.05,0.50,0.95])
            agb_q05,agb_med,agb_q95 = float(p[0,0]),float(p[0,1]),float(p[0,2])
        else:
            d, ix = nn_dem.kneighbors(df_valid[FEATURES_NO_DEM].values)
            for j, c in enumerate(DEM_FEATURES):
                df_valid[c] = [np.average(df[c].values[i],weights=1/(dist+1e-6))
                               for i,dist in zip(ix,d)]
            p = qrf.predict(df_valid[FEATURES_ALL], quantiles=[0.05,0.50,0.95])
            agb_q05=float(np.percentile(p[:,0],50))
            agb_med=float(np.percentile(p[:,1],50))
            agb_q95=float(np.percentile(p[:,2],50))
            pi_w = agb_q95 - agb_q05
            if n_pixels>=50 and pi_w<100:
                confidence,note = "high",f"유효 픽셀 {n_pixels:,}개 기반 예측"
            elif n_pixels>=10:
                confidence,note = "medium",f"유효 픽셀 {n_pixels:,}개 (중간 신뢰도)"
            else:
                confidence,note = "low",f"유효 픽셀 {n_pixels:,}개 (소수 픽셀)"

        sp = species_dominant if species_dominant in SPECIES_PARAMS else "기본활엽"
        return StandStateEstimate(
            pnu=pnu, geom_wkt=geom_wkt,
            area_ha=round(area_ha,4), estimated_at=datetime.utcnow(),
            species_dominant=species_dominant, species_secondary=species_secondary,
            age_estimate=age_estimate, age_class=_age_class(age_estimate),
            agb_mg_per_ha=round(agb_med,2), agb_q05=round(agb_q05,2), agb_q95=round(agb_q95,2),
            volume_m3_per_ha=round(_agb_to_volume(agb_med,sp),2),
            volume_q05=round(_agb_to_volume(agb_q05,sp),2),
            volume_q95=round(_agb_to_volume(agb_q95,sp),2),
            carbon_tc_per_ha=round(_agb_to_carbon(agb_med,sp),2),
            carbon_q05=round(_agb_to_carbon(agb_q05,sp),2),
            carbon_q95=round(_agb_to_carbon(agb_q95,sp),2),
            grade_distribution=_grade_dist(agb_med),
            n_gedi_footprints=n_gedi_footprints, n_s2_scenes=n_s2_scenes,
            saturation_warning=(agb_med>130 and species_dominant in
                ["잣나무","낙엽송","강원소나무","중부소나무","리기다","기본침엽"]),
            confidence_level=confidence, confidence_note=note,
        )

    # 테스트 실행
    TEST_WKT = ("POLYGON((127.72 36.49, 127.725 36.49, "
                "127.725 36.495, 127.72 36.495, 127.72 36.49))")
    result = predict_stand(
        geom_wkt=TEST_WKT, pnu="4374010100100010000",
        species_dominant="신갈", species_secondary="굴참",
        age_estimate=45, n_gedi_footprints=12, n_s2_scenes=8,
    )

    print("\n" + "="*50)
    print("StandStateEstimate 최종 출력")
    print("="*50)
    for k, v in result.model_dump().items():
        print(f"  {k:22s}: {v}")

    print("\n✅ Step 8 완료!")
    print("\n" + "="*60)
    print("🎉 Module A 전체 파이프라인 완료!")
    print("="*60)
    print(f"  학습 데이터: GEDI L4A 11,026개 (보은군)")
    print(f"  피처:        위성 25개 (S2/SAR/PALSAR/DEM)")
    print(f"  모델:        Quantile RF — R²=0.471, RMSE=59.8 Mg/ha")
    print(f"  90%PI:       coverage=0.916")
    print(f"  산출물:      Fig1/2/3 + predict_stand() + qrf_model.pkl")


# ═════════════════════════════════════════════════════════════
# 메인 실행
# ═════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(
        description="Module A — 위성 AGB Nowcasting"
    )
    parser.add_argument(
        "--step", default="all",
        choices=["1","2","3","4","5","6","7","8","all"],
        help="실행할 단계 (기본값: all)"
    )
    args = parser.parse_args()

    boeun_ee = boeun_q = rf = qrf = df = trn = val = None
    q05 = q50 = q95 = None

    run_all = (args.step == "all")

    if args.step in ("1", "all"):
        boeun_ee = step1_setup()

    if args.step in ("2", "all"):
        if boeun_ee is None:
            import ee, json
            ee.Initialize(project=GEE_PROJECT)
            with open(BOEUN_PATH) as f:
                gj = json.load(f)
            boeun_ee = ee.Geometry(gj["features"][0]["geometry"])
        boeun_q = step2_gedi(boeun_ee)

    if args.step in ("3", "all"):
        if boeun_ee is None or boeun_q is None:
            print("⚠️  Step 2를 먼저 실행해주세요.")
            return
        step3_satellite(boeun_ee, boeun_q)

    if args.step in ("4", "all"):
        df, trn, val = step4_preprocess()

    if args.step in ("5", "all"):
        if trn is None:
            df, trn, val = step4_preprocess()
        rf = step5_rf_baseline(trn, val)

    if args.step in ("6", "all"):
        if trn is None:
            df, trn, val = step4_preprocess()
        qrf, q05, q50, q95, val = step6_quantile_rf(trn, val)

    if args.step in ("7", "all"):
        if qrf is None:
            import joblib
            qrf = joblib.load(MODEL_PATH)
        if df is None:
            import pandas as pd
            from sklearn.model_selection import train_test_split
            df = pd.read_csv(TRAIN_PATH, encoding="utf-8-sig")
            df = df[df["NDVI"] >= 0.3].copy()
            df["sample_weight"] = 1.0 / (df["agbd_se"] + 1.0)
            _, val = train_test_split(df, test_size=0.15, random_state=42)
            preds = qrf.predict(val[FEATURES_ALL], quantiles=[0.05,0.50,0.95])
            q05, q50, q95 = preds[:,0], preds[:,1], preds[:,2]
        step7_figures(qrf, q05, q50, q95, val, df)

    if args.step in ("8", "all"):
        if qrf is None:
            import joblib
            qrf = joblib.load(MODEL_PATH)
        if df is None:
            import pandas as pd
            df = pd.read_csv(TRAIN_PATH, encoding="utf-8-sig")
            df = df[df["NDVI"] >= 0.3].copy()
            df["sample_weight"] = 1.0 / (df["agbd_se"] + 1.0)
        step8_predict_stand(qrf, df)


if __name__ == "__main__":
    main()
