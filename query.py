import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text

# 1. Buat koneksi ke database MySQL
# Format: mysql+pymysql://<user>:<password>@<host>:<port>/<nama_database>
engine = create_engine("mysql+pymysql://root:@localhost:3306/gender_analyst")


# 2. Query SQL terstruktur
query = """
SELECT 
    f.year_key,
    p.province_name,
    p.region_group,
    -- TPAK Perempuan (gender_key = 2) dan Laki-laki (gender_key = 1)
    MAX(CASE WHEN f.gender_key = 2 THEN f.tpak_rate_pct END) AS tpak_p,
    MAX(CASE WHEN f.gender_key = 1 THEN f.tpak_rate_pct END) AS tpak_l,
    MAX(CASE WHEN f.gender_key = 1 THEN f.tpak_rate_pct END) - 
    MAX(CASE WHEN f.gender_key = 2 THEN f.tpak_rate_pct END) AS tpak_gap,
    -- Rasio Upah Makro Nasional (P / L)
    w.wage_ratio_nasional,
    -- Beban Domestik & Status Kerja Perempuan (%)
    act.pct_beban_rt_p,
    act.pct_bekerja_p,
    act.pct_sekolah_p
FROM fact_tpak_economics f
JOIN dim_province p ON f.province_key = p.province_key
-- Subquery Rasio Upah Nasional
LEFT JOIN (
    SELECT 
        year,
        MAX(CASE WHEN gender_key = 2 THEN hourly_wage_idr END) / 
        MAX(CASE WHEN gender_key = 1 THEN hourly_wage_idr END) AS wage_ratio_nasional
    FROM fact_wage_hourly
    GROUP BY year
) w ON f.year_key = w.year
-- Subquery Proporsi Kegiatan Utama Perempuan
LEFT JOIN (
    SELECT 
        a.year_key,
        SUM(CASE WHEN a.activity_key = 3 THEN a.total_penduduk ELSE 0 END) * 100.0 / SUM(a.total_penduduk) AS pct_beban_rt_p,
        SUM(CASE WHEN a.activity_key = 1 THEN a.total_penduduk ELSE 0 END) * 100.0 / SUM(a.total_penduduk) AS pct_bekerja_p,
        SUM(CASE WHEN a.activity_key = 5 THEN a.total_penduduk ELSE 0 END) * 100.0 / SUM(a.total_penduduk) AS pct_sekolah_p
    FROM fact_labor_activity a
    WHERE a.gender_key = 2
    GROUP BY a.year_key
) act ON f.year_key = act.year_key
GROUP BY f.year_key, p.province_name, p.region_group, w.wage_ratio_nasional, act.pct_beban_rt_p, act.pct_bekerja_p, act.pct_sekolah_p;
"""

with engine.connect() as connection:
    df = pd.read_sql(text(query), connection)

print("Data berhasil ditarik. Total baris:", len(df))
print(df.head())
