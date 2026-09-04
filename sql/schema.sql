-- =============================================================================
-- Database & Schema Definition: Star Schema Gender Labor Market & TPAK Analysis
-- Database Name: gender_analyst
-- =============================================================================

CREATE DATABASE IF NOT EXISTS gender_analyst;
USE gender_analyst;

-- -----------------------------------------------------------------------------
-- 1. TABEL DIMENSI (DIMENSION TABLES)
-- -----------------------------------------------------------------------------

-- Dimensi Provinsi
CREATE TABLE IF NOT EXISTS dim_province (
    province_key INT PRIMARY KEY,
    province_name VARCHAR(100) NOT NULL,
    region_group VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimensi Gender / Jenis Kelamin
CREATE TABLE IF NOT EXISTS dim_gender (
    gender_key INT PRIMARY KEY,
    gender_code VARCHAR(10) NOT NULL,
    gender_name VARCHAR(50) NOT NULL
);

-- Dimensi Jenis Aktivitas Utama Penduduk
CREATE TABLE IF NOT EXISTS dim_activity (
    activity_key INT PRIMARY KEY,
    kegiatan_nama VARCHAR(100) NOT NULL,
    kategori_aktivitas VARCHAR(50) NOT NULL
);

-- -----------------------------------------------------------------------------
-- 2. TABEL FAKTA HISTORIS (HISTORICAL FACT TABLES)
-- -----------------------------------------------------------------------------

-- Fakta Indikator Makro & TPAK per Provinsi
CREATE TABLE IF NOT EXISTS fact_tpak_economics (
    fact_id INT AUTO_INCREMENT PRIMARY KEY,
    year_key INT NOT NULL,
    province_key INT NOT NULL,
    gender_key INT NOT NULL,
    tpak_rate_pct DECIMAL(5, 2) NOT NULL,
    tpt_rate_pct DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (province_key) REFERENCES dim_province(province_key),
    FOREIGN KEY (gender_key) REFERENCES dim_gender(gender_key)
);

-- Fakta Rata-Rata Upah per Jam Nasional (Gender Disaggregated)
CREATE TABLE IF NOT EXISTS fact_wage_hourly (
    wage_fact_id INT AUTO_INCREMENT PRIMARY KEY,
    year INT NOT NULL,
    gender_key INT NOT NULL,
    hourly_wage_idr DECIMAL(12, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (gender_key) REFERENCES dim_gender(gender_key)
);

-- Fakta Distribusi Aktivitas Angkatan Kerja (Agregat Nasional)
CREATE TABLE IF NOT EXISTS fact_labor_activity (
    activity_fact_id INT AUTO_INCREMENT PRIMARY KEY,
    year_key INT NOT NULL,
    gender_key INT NOT NULL,
    gender_code VARCHAR(10),
    activity_key INT NOT NULL,
    kegiatan_nama VARCHAR(100),
    total_penduduk BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (gender_key) REFERENCES dim_gender(gender_key),
    FOREIGN KEY (activity_key) REFERENCES dim_activity(activity_key)
);

-- -----------------------------------------------------------------------------
-- 3. TABEL ANALITIK, PREDIKSI, & FORECASTING (ANALYTICS & BI READY)
-- -----------------------------------------------------------------------------

-- Fakta Hasil Evaluasi Model Regresi OLS & Nilai Residual (Aktual vs Prediksi)
CREATE TABLE IF NOT EXISTS fact_tpak_prediction (
    pred_id INT AUTO_INCREMENT PRIMARY KEY,
    year_key INT NOT NULL,
    province_key INT NOT NULL,
    tpak_p DECIMAL(5, 2) NOT NULL,
    tpak_p_pred DECIMAL(5, 2) NOT NULL,
    residual DECIMAL(5, 2) NOT NULL,
    pct_beban_rt_p DECIMAL(5, 2),
    pct_sekolah_p DECIMAL(5, 2),
    wage_ratio_nasional DECIMAL(6, 4),
    tpak_l DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (province_key) REFERENCES dim_province(province_key)
);

-- Metadata Metrik dan Koefisien Model Regresi
CREATE TABLE IF NOT EXISTS dim_model_metrics (
    metric_id INT AUTO_INCREMENT PRIMARY KEY,
    feature_name VARCHAR(100) NOT NULL,
    coefficient_value DECIMAL(10, 4) NOT NULL,
    r2_percentage VARCHAR(20),
    mae DECIMAL(10, 4),
    rmse DECIMAL(10, 4),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Fakta Proyeksi & Skenario Kebijakan Masa Depan (Forecasting)
CREATE TABLE IF NOT EXISTS fact_tpak_forecast (
    forecast_id INT AUTO_INCREMENT PRIMARY KEY,
    year_key INT NOT NULL,
    province_key INT NOT NULL,
    province_name VARCHAR(100) NOT NULL,
    scenario_type VARCHAR(100) NOT NULL,
    pct_beban_rt_p_proj DECIMAL(5, 2),
    wage_ratio_proj DECIMAL(6, 4),
    tpak_p_forecast DECIMAL(5, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (province_key) REFERENCES dim_province(province_key)
);

-- -----------------------------------------------------------------------------
-- 4. VIEW ANALITIK UNTUK POWER BI (SEMANTIC LAYER)
-- -----------------------------------------------------------------------------

-- View Gabungan Data Historis & Proyeksi untuk Visualisasi Line Chart Power BI
CREATE OR REPLACE VIEW view_tpak_bi_dashboard AS
SELECT 
    p.province_key,
    p.province_name,
    p.region_group,
    f.year_key,
    f.tpak_p AS nilai_tpak,
    f.tpak_p_pred AS nilai_prediksi_model,
    f.residual AS error_residual,
    'Historis' AS status_data,
    'Aktual Lapangan' AS skenario
FROM fact_tpak_prediction f
JOIN dim_province p ON f.province_key = p.province_key

UNION ALL

SELECT 
    f.province_key,
    f.province_name,
    p.region_group,
    f.year_key,
    f.tpak_p_forecast AS nilai_tpak,
    NULL AS nilai_prediksi_model,
    NULL AS error_residual,
    'Proyeksi' AS status_data,
    f.scenario_type AS skenario
FROM fact_tpak_forecast f
JOIN dim_province p ON f.province_key = p.province_key;

-- ============================================================
-- VIEWS
-- ============================================================

-- View 1: Complete Analytics Data
CREATE OR REPLACE VIEW view_tpak_complete_analytics AS
SELECT 
    f.year_key,
    p.province_key,
    p.province_name,
    p.region_group,
    MAX(CASE WHEN f.gender_key = 2 THEN f.tpak_rate_pct END) AS tpak_p,
    MAX(CASE WHEN f.gender_key = 1 THEN f.tpak_rate_pct END) AS tpak_l,
    MAX(CASE WHEN f.gender_key = 1 THEN f.tpak_rate_pct END) - 
    MAX(CASE WHEN f.gender_key = 2 THEN f.tpak_rate_pct END) AS tpak_gap,
    w.wage_ratio_nasional,
    act.pct_beban_rt_p,
    act.pct_bekerja_p,
    act.pct_sekolah_p
FROM fact_tpak_economics f
JOIN dim_province p ON f.province_key = p.province_key
LEFT JOIN (
    SELECT 
        year,
        ROUND(
            MAX(CASE WHEN gender_key = 2 THEN hourly_wage_idr END) / 
            NULLIF(MAX(CASE WHEN gender_key = 1 THEN hourly_wage_idr END), 0),
            4
        ) AS wage_ratio_nasional
    FROM fact_wage_hourly
    GROUP BY year
) w ON f.year_key = w.year
LEFT JOIN (
    SELECT 
        a.year_key,
        ROUND(SUM(CASE WHEN a.activity_key = 3 THEN a.total_penduduk ELSE 0 END) * 100.0 / 
        NULLIF(SUM(a.total_penduduk), 0), 2) AS pct_beban_rt_p,
        ROUND(SUM(CASE WHEN a.activity_key = 1 THEN a.total_penduduk ELSE 0 END) * 100.0 / 
        NULLIF(SUM(a.total_penduduk), 0), 2) AS pct_bekerja_p,
        ROUND(SUM(CASE WHEN a.activity_key = 5 THEN a.total_penduduk ELSE 0 END) * 100.0 / 
        NULLIF(SUM(a.total_penduduk), 0), 2) AS pct_sekolah_p
    FROM fact_labor_activity a
    WHERE a.gender_key = 2
    GROUP BY a.year_key
) act ON f.year_key = act.year_key
GROUP BY f.year_key, p.province_key, p.province_name, p.region_group, w.wage_ratio_nasional, 
         act.pct_beban_rt_p, act.pct_bekerja_p, act.pct_sekolah_p;

-- View 2: TPAK Gender Gap Summary
CREATE OR REPLACE VIEW view_tpak_gender_gap AS
SELECT 
    f.year_key,
    p.province_name,
    MAX(CASE WHEN f.gender_key = 1 THEN f.tpak_rate_pct END) AS tpak_male,
    MAX(CASE WHEN f.gender_key = 2 THEN f.tpak_rate_pct END) AS tpak_female,
    MAX(CASE WHEN f.gender_key = 1 THEN f.tpak_rate_pct END) - 
    MAX(CASE WHEN f.gender_key = 2 THEN f.tpak_rate_pct END) AS gap
FROM fact_tpak_economics f
JOIN dim_province p ON f.province_key = p.province_key
GROUP BY f.year_key, p.province_name
ORDER BY f.year_key, gap DESC;

-- View 3: Wage Ratio Analysis
CREATE OR REPLACE VIEW view_wage_ratio_trend AS
SELECT 
    year,
    MAX(CASE WHEN gender_key = 1 THEN hourly_wage_idr END) AS wage_male,
    MAX(CASE WHEN gender_key = 2 THEN hourly_wage_idr END) AS wage_female,
    ROUND(
        MAX(CASE WHEN gender_key = 2 THEN hourly_wage_idr END) / 
        NULLIF(MAX(CASE WHEN gender_key = 1 THEN hourly_wage_idr END), 0),
        4
    ) AS wage_ratio
FROM fact_wage_hourly
GROUP BY year
ORDER BY year;

-- View 4: Activity Distribution by Gender
CREATE OR REPLACE VIEW view_activity_distribution AS
SELECT 
    a.year_key,
    g.gender_name,
    act.activity_name,
    SUM(a.total_penduduk) AS total_penduduk,
    ROUND(SUM(a.total_penduduk) * 100.0 / 
    (SELECT SUM(total_penduduk) FROM fact_labor_activity WHERE year_key = a.year_key AND gender_key = a.gender_key), 2) AS percentage
FROM fact_labor_activity a
JOIN dim_gender g ON a.gender_key = g.gender_key
JOIN dim_activity act ON a.activity_key = act.activity_key
GROUP BY a.year_key, a.gender_key, a.activity_key
ORDER BY a.year_key, a.gender_key, a.activity_key;

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_tpak_year_gender ON fact_tpak_economics(year_key, gender_key);
CREATE INDEX idx_tpak_province_year ON fact_tpak_economics(province_key, year_key);
CREATE INDEX idx_wage_year_gender ON fact_wage_hourly(year, gender_key);
CREATE INDEX idx_activity_year_gender ON fact_labor_activity(year_key, gender_key);

-- ============================================================
-- END OF SCHEMA
-- ============================================================