-- ============================================================
-- USEFUL QUERIES - Gender & Labor Economics Analysis
-- ============================================================

-- Query 1: TPAK Trend by Province
SELECT 
    year_key,
    province_name,
    tpak_p,
    tpak_l,
    tpak_gap
FROM view_tpak_gender_gap
WHERE province_name NOT IN ('INDONESIA', 'Indonesia')
ORDER BY year_key, province_name;

-- Query 2: Top 10 Provinces with Largest Gender Gap
SELECT 
    province_name,
    tpak_male,
    tpak_female,
    gap
FROM view_tpak_gender_gap
WHERE year_key = (SELECT MAX(year_key) FROM dim_year)
ORDER BY gap DESC
LIMIT 10;

-- Query 3: Wage Ratio National Trend
SELECT 
    year,
    wage_male,
    wage_female,
    wage_ratio
FROM view_wage_ratio_trend
ORDER BY year;

-- Query 4: Activity Distribution for Women
SELECT 
    year_key,
    activity_name,
    total_penduduk,
    percentage
FROM view_activity_distribution
WHERE gender_name = 'Perempuan'
ORDER BY year_key, percentage DESC;

-- Query 5: Correlation Data for Analysis
SELECT 
    f.year_key,
    p.province_name,
    p.region_group,
    MAX(CASE WHEN f.gender_key = 2 THEN f.tpak_rate_pct END) AS tpak_p,
    MAX(CASE WHEN f.gender_key = 1 THEN f.tpak_rate_pct END) AS tpak_l,
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
GROUP BY f.year_key, p.province_key, p.province_name, p.region_group
ORDER BY f.year_key, p.province_name;

-- Query 6: Year-over-Year TPAK Change
SELECT 
    COALESCE(curr.year_key, prev.year_key) AS year_key,
    COALESCE(curr.province_name, prev.province_name) AS province_name,
    ROUND(prev.tpak_p, 2) AS prev_year_tpak_p,
    ROUND(curr.tpak_p, 2) AS curr_year_tpak_p,
    ROUND(curr.tpak_p - prev.tpak_p, 2) AS yoy_change
FROM view_tpak_gender_gap curr
FULL OUTER JOIN view_tpak_gender_gap prev 
    ON curr.province_name = prev.province_name 
    AND curr.year_key = prev.year_key + 1
ORDER BY year_key DESC, yoy_change DESC;

-- Query 7: Data Completeness Check
SELECT 
    dy.year_value AS year,
    COUNT(DISTINCT f.province_key) AS tpak_records,
    COUNT(DISTINCT w.wage_key) AS wage_records,
    COUNT(DISTINCT a.activity_fact_key) AS activity_records
FROM dim_year dy
LEFT JOIN fact_tpak_economics f ON dy.year_key = f.year_key
LEFT JOIN fact_wage_hourly w ON dy.year_value = w.year
LEFT JOIN fact_labor_activity a ON dy.year_key = a.year_key
GROUP BY dy.year_value
ORDER BY dy.year_value;

-- Query 8: Missing Data Identification
SELECT 
    'TPAK' AS table_name,
    dy.year_value,
    COUNT(*) AS missing_records
FROM dim_year dy
LEFT JOIN fact_tpak_economics f ON dy.year_key = f.year_key
WHERE f.tpak_key IS NULL
GROUP BY dy.year_value

UNION ALL

SELECT 
    'Wage' AS table_name,
    w.year,
    COUNT(*) AS missing_records
FROM fact_wage_hourly w
WHERE w.hourly_wage_idr IS NULL
GROUP BY w.year;

-- ============================================================
-- END OF QUERIES
-- ============================================================