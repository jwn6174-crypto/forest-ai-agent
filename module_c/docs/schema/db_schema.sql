-- ============================================================
-- db_schema.sql — PostgreSQL + PostGIS 7 스키마 (Manual 01 §06)
-- ============================================================
-- 통합 단계 (W5+) 시 PostgreSQL 인스턴스에 적용.
-- 현재는 reference 만 (사용자: "통합은 나중").
--
-- 출처: master_design.html §A + Manual 01 §06
-- 작성일: 2026-05-20 (Day 6 reference)
-- ============================================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_raster;
-- CREATE EXTENSION IF NOT EXISTS vector;  -- pgvector (RAG embedding)


-- ============================================================
-- Schema 1: spatial — 행정·연속지적·임상도 polygon
-- 주 작성자: 희도 (Lead)
-- 갱신: 연 1회
-- ============================================================
CREATE SCHEMA IF NOT EXISTS spatial;

-- 연속지적 (VWorld 동기)
CREATE TABLE IF NOT EXISTS spatial.parcel_continuous (
    pnu          VARCHAR(19) PRIMARY KEY,
    geom         GEOMETRY(POLYGON, 5179) NOT NULL,
    sgg_cd       VARCHAR(5),           -- 시군구
    sigungu      TEXT,
    bjdong_cd    VARCHAR(10),
    bjdong_nm    TEXT,
    jibun        TEXT,
    area_m2      DOUBLE PRECISION,
    sync_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_parcel_geom ON spatial.parcel_continuous USING GIST (geom);
CREATE INDEX IF NOT EXISTS ix_parcel_sgg  ON spatial.parcel_continuous (sgg_cd);

-- 임상도 1:5,000 (정우 module_bd 영역)
CREATE TABLE IF NOT EXISTS spatial.forest_type_5k (
    fid          BIGSERIAL PRIMARY KEY,
    geom         GEOMETRY(MULTIPOLYGON, 5179),
    forest_type  TEXT,                  -- 임종 (산림/임야 외)
    cover_type   TEXT,                  -- 임상 (침/활/혼/죽림)
    species      TEXT,
    age_class    TEXT,                  -- I-VI (영급)
    dbh_class    TEXT,                  -- 1-6 (경급)
    crown_density TEXT,                 -- 소밀도 (소/중/밀)
    src_year     INT,
    src_sgg_cd   VARCHAR(5)
);
CREATE INDEX IF NOT EXISTS ix_fmap_geom ON spatial.forest_type_5k USING GIST (geom);

-- 행정경계
CREATE TABLE IF NOT EXISTS spatial.admin_sgg (
    sgg_cd VARCHAR(5) PRIMARY KEY,
    name   TEXT,
    geom   GEOMETRY(MULTIPOLYGON, 5179)
);


-- ============================================================
-- Schema 2: inventory — 임야 polygon 상태 추정 (Module A)
-- 주 작성자: 민석 (Person 2) — 현재 미시작, Module C 가 mock
-- ============================================================
CREATE SCHEMA IF NOT EXISTS inventory;

CREATE TABLE IF NOT EXISTS inventory.stand_estimate (
    pnu          VARCHAR(19) PRIMARY KEY,
    geom         GEOMETRY(POLYGON, 5179),
    estimated_at TIMESTAMPTZ NOT NULL,
    payload      JSONB NOT NULL,        -- StandStateEstimate dict
    model_ver    TEXT
);
CREATE INDEX IF NOT EXISTS ix_stand_geom ON inventory.stand_estimate USING GIST (geom);

-- 사용자 입력 polygon (UI 임시)
CREATE TABLE IF NOT EXISTS inventory.user_polygon (
    id         BIGSERIAL PRIMARY KEY,
    session_id TEXT,
    geom       GEOMETRY(POLYGON, 5179),
    created_at TIMESTAMPTZ DEFAULT now()
);


-- ============================================================
-- Schema 3: economics — Module C 출력 (희도 영역)
-- ============================================================
CREATE SCHEMA IF NOT EXISTS economics;

-- 6 시나리오 LEV 결과
CREATE TABLE IF NOT EXISTS economics.lev_result (
    id            BIGSERIAL PRIMARY KEY,
    pnu           VARCHAR(19) REFERENCES spatial.parcel_continuous(pnu),
    computed_at   TIMESTAMPTZ NOT NULL,
    discount_rate NUMERIC(4,3),
    climate_scenario TEXT,
    n_samples     INT,
    payload       JSONB NOT NULL,       -- Dict[scenario, LEVResult]
    recommendation TEXT,
    draft_plan    JSONB                 -- DraftPlanCard
);
CREATE INDEX IF NOT EXISTS ix_lev_pnu ON economics.lev_result (pnu, computed_at DESC);

-- D22 검증 case (carbonregistry 비교 결과)
CREATE TABLE IF NOT EXISTS economics.validation_case (
    id                   BIGSERIAL PRIMARY KEY,
    carbonregistry_id    TEXT UNIQUE,
    lot_id               TEXT,
    sigungu              TEXT,
    project_type         TEXT,
    transaction_type     TEXT,
    certified_total_tco2 NUMERIC,
    estimated_area_ha    NUMERIC,
    model_30yr_tco2_per_ha NUMERIC,
    difference_pct       NUMERIC,
    interpretation       TEXT,
    created_at           TIMESTAMPTZ DEFAULT now()
);


-- ============================================================
-- Schema 4: market — 정우 D 모듈 영역
-- ============================================================
CREATE SCHEMA IF NOT EXISTS market;

CREATE TABLE IF NOT EXISTS market.timber_price (
    ym         VARCHAR(8),               -- YYYYMM01
    grade      TEXT,                     -- 특용재/1·2·3등급/원주재/원료재
    species    TEXT DEFAULT '소나무',
    price      INT,                      -- 원/m³
    source     TEXT DEFAULT 'KOFPI',
    scraped_at TIMESTAMPTZ,
    PRIMARY KEY (ym, grade, species)
);

CREATE TABLE IF NOT EXISTS market.kau_daily (
    date    DATE,
    vintage TEXT,                        -- KAU24/25/26
    clpr    NUMERIC(10,2),               -- 종가
    high    NUMERIC(10,2),
    low     NUMERIC(10,2),
    trqu    BIGINT,                      -- 거래량
    PRIMARY KEY (date, vintage)
);
COMMENT ON TABLE market.kau_daily IS 'D23 발견: KAU25 16개월 +79.4%(8,670→15,550, 2025-07~2026-03), WTA 17,039원에 8.7% 미달 — 돌파 임박';


-- ============================================================
-- Schema 5: weather — 산악기상 (정우 D8)
-- ============================================================
CREATE SCHEMA IF NOT EXISTS weather;

CREATE TABLE IF NOT EXISTS weather.mt_station (
    station_id TEXT PRIMARY KEY,
    name       TEXT,
    geom       GEOMETRY(POINT, 5179),
    elev       NUMERIC
);

CREATE TABLE IF NOT EXISTS weather.mt_obs (
    station_id TEXT REFERENCES weather.mt_station,
    ts         TIMESTAMPTZ,
    temp       NUMERIC(5,2),
    prcp       NUMERIC(6,2),
    vpd        NUMERIC(6,3),
    wind       NUMERIC(5,2),
    PRIMARY KEY (station_id, ts)
);


-- ============================================================
-- Schema 6: carbon — 산림탄소상쇄 사업 + RAG
-- ============================================================
CREATE SCHEMA IF NOT EXISTS carbon;

-- 등록사업 (carbonregistry 658건 + 사용자 확장)
CREATE TABLE IF NOT EXISTS carbon.offset_project (
    project_id     TEXT PRIMARY KEY,    -- FCR_43_BOEUN_001 등
    name           TEXT,
    project_type   TEXT,                 -- forest_management_rotation 등
    sub_type       TEXT,                 -- rotation_extension 등
    transaction_type TEXT,                -- 거래/비거래
    sigungu        TEXT,
    town           TEXT,
    ri             TEXT,
    lot_id         TEXT,
    geom_centroid  GEOMETRY(POINT, 4326),
    area_ha        NUMERIC,
    total_absorption_tco2 NUMERIC,
    avg_uptake_tco2_per_ha_per_yr NUMERIC,
    registered_at  DATE,
    raw_json       JSONB,
    source         TEXT DEFAULT 'carbonregistry.forest.go.kr'
);
CREATE INDEX IF NOT EXISTS ix_offset_sigungu ON carbon.offset_project (sigungu);
CREATE INDEX IF NOT EXISTS ix_offset_type ON carbon.offset_project (project_type);
CREATE INDEX IF NOT EXISTS ix_offset_geom ON carbon.offset_project USING GIST (geom_centroid);

-- 8 사업유형 룰베이스 (D16)
CREATE TABLE IF NOT EXISTS carbon.eligibility_rules (
    code           TEXT PRIMARY KEY,    -- AR, FM-Rotation, ...
    korean         TEXT,
    rules_json     JSONB,
    verification   TEXT                 -- rule_based / RAG
);

-- RAG 코퍼스 (정우 carbon_chunks.jsonl 적재)
CREATE TABLE IF NOT EXISTS carbon.chunk_index (
    chunk_id     UUID PRIMARY KEY,
    source       TEXT,                   -- PDF 파일명
    page         INT,
    project_type TEXT,
    text         TEXT
    -- , embedding VECTOR(1024)          -- pgvector 활용 시
);
CREATE INDEX IF NOT EXISTS ix_chunk_project ON carbon.chunk_index (project_type);


-- ============================================================
-- Schema 7: legal — 법령 룰베이스
-- ============================================================
CREATE SCHEMA IF NOT EXISTS legal;

-- 별표 3 기준벌기령 (정우 D legal_rotation.py)
CREATE TABLE IF NOT EXISTS legal.rotation_rule (
    species     TEXT,
    ownership   TEXT,                    -- 사유림/국유림/공유림
    min_age     INT,
    law_article TEXT,
    fetched_at  TIMESTAMPTZ,
    PRIMARY KEY (species, ownership)
);

INSERT INTO legal.rotation_rule (species, ownership, min_age, law_article) VALUES
    ('강원지방소나무', '사유림', 40, '산림자원법 시행규칙 별표 3'),
    ('중부지방소나무', '사유림', 40, '산림자원법 시행규칙 별표 3'),
    ('잣나무',        '사유림', 60, '산림자원법 시행규칙 별표 3'),
    ('낙엽송',        '사유림', 30, '산림자원법 시행규칙 별표 3'),
    ('리기다소나무',  '사유림', 25, '산림자원법 시행규칙 별표 3'),
    ('편백',          '사유림', 40, '산림자원법 시행규칙 별표 3'),
    ('참나무류',      '사유림', 25, '산림자원법 시행규칙 별표 3'),
    ('포플러류',      '사유림',  3, '산림자원법 시행규칙 별표 3')
ON CONFLICT DO NOTHING;


-- ============================================================
-- Views — 자주 쓰는 join
-- ============================================================

-- D22 검증 case (보은·진안 인근, 벌기연장, 거래)
CREATE OR REPLACE VIEW economics.v_validation_targets AS
SELECT
    op.project_id,
    op.lot_id,
    op.sigungu,
    op.area_ha,
    op.total_absorption_tco2,
    op.avg_uptake_tco2_per_ha_per_yr,
    op.geom_centroid
FROM carbon.offset_project op
WHERE op.sub_type = 'rotation_extension'
  AND op.transaction_type = '거래'
  AND op.sigungu IN ('보은군', '진안군', '영동군', '괴산군', '제천시')
ORDER BY op.area_ha DESC;


-- ============================================================
-- 적재 순서 (W5+ 통합 시점)
-- ============================================================
-- 1. python module_c/scripts/load_carbonregistry.py — carbon.offset_project
-- 2. python module_c/scripts/load_kau.py — market.kau_daily
-- 3. python module_c/scripts/load_kofpi.py — market.timber_price (정우 정우)
-- 4. python module_c/scripts/load_eligibility.py — carbon.eligibility_rules
-- 5. python module_c/scripts/run_all.py → economics.lev_result · validation_case
