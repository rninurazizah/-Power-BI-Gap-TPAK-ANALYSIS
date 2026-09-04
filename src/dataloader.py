import pandas as pd
from sqlalchemy import text
from config.database import get_engine
import logging

logger = logging.getLogger(__name__)


def get_analytics_data():
    """Mengambil data analitik prediksi yang sudah bersih dan ter-join."""
    try:
        query = "SELECT * FROM view_tpak_complete_analytics"
        with get_engine().connect() as conn:
            df = pd.read_sql(text(query), conn)
        logger.info(f"✓ Analytics data loaded: {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"✗ Error loading analytics data: {e}")
        return None


def get_forecast_data():
    """Mengambil data hasil proyeksi masa depan."""
    try:
        query = "SELECT * FROM fact_tpak_forecast"
        with get_engine().connect() as conn:
            df = pd.read_sql(text(query), conn)
        logger.info(f"✓ Forecast data loaded: {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"✗ Error loading forecast data: {e}")
        return None


def get_model_metrics():
    """Mengambil evaluasi model (R2, MAE, RMSE, Koefisien)."""
    try:
        query = "SELECT * FROM dim_model_metrics"
        with get_engine().connect() as conn:
            df = pd.read_sql(text(query), conn)
        logger.info(f"✓ Model metrics loaded: {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"✗ Error loading model metrics: {e}")
        return None


def get_tpak_by_province(year=None):
    """Mengambil TPAK per provinsi"""
    try:
        if year:
            query = f"""
            SELECT 
                p.province_name,
                p.region_group,
                MAX(CASE WHEN f.gender_key = 1 THEN f.tpak_rate_pct END) AS tpak_male,
                MAX(CASE WHEN f.gender_key = 2 THEN f.tpak_rate_pct END) AS tpak_female,
                MAX(CASE WHEN f.gender_key = 1 THEN f.tpak_rate_pct END) - 
                MAX(CASE WHEN f.gender_key = 2 THEN f.tpak_rate_pct END) AS gap
            FROM fact_tpak_economics f
            JOIN dim_province p ON f.province_key = p.province_key
            WHERE f.year_key = {year}
            GROUP BY p.province_name, p.region_group
            ORDER BY gap DESC
            """
        else:
            query = """
            SELECT 
                p.province_name,
                p.region_group,
                f.year_key,
                MAX(CASE WHEN f.gender_key = 1 THEN f.tpak_rate_pct END) AS tpak_male,
                MAX(CASE WHEN f.gender_key = 2 THEN f.tpak_rate_pct END) AS tpak_female,
                MAX(CASE WHEN f.gender_key = 1 THEN f.tpak_rate_pct END) - 
                MAX(CASE WHEN f.gender_key = 2 THEN f.tpak_rate_pct END) AS gap
            FROM fact_tpak_economics f
            JOIN dim_province p ON f.province_key = p.province_key
            GROUP BY p.province_name, p.region_group, f.year_key
            ORDER BY f.year_key, gap DESC
            """
        
        with get_engine().connect() as conn:
            df = pd.read_sql(text(query), conn)
        logger.info(f"✓ TPAK by province loaded: {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"✗ Error loading TPAK by province: {e}")
        return None


def get_wage_comparison(year=None):
    """Mengambil perbandingan upah"""
    try:
        if year:
            query = f"""
            SELECT 
                g.gender_name,
                w.hourly_wage_idr
            FROM fact_wage_hourly w
            JOIN dim_gender g ON w.gender_key = g.gender_key
            WHERE w.year = {year}
            ORDER BY g.gender_name
            """
        else:
            query = """
            SELECT 
                w.year,
                g.gender_name,
                w.hourly_wage_idr
            FROM fact_wage_hourly w
            JOIN dim_gender g ON w.gender_key = g.gender_key
            ORDER BY w.year, g.gender_name
            """
        
        with get_engine().connect() as conn:
            df = pd.read_sql(text(query), conn)
        logger.info(f"✓ Wage comparison loaded: {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"✗ Error loading wage comparison: {e}")
        return None


def get_activity_distribution(year=None, gender_name=None):
    """Mengambil distribusi kegiatan utama"""
    try:
        query = """
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
        WHERE 1=1
        """
        
        if year:
            query += f" AND a.year_key = {year}"
        if gender_name:
            query += f" AND g.gender_name = '{gender_name}'"
        
        query += " GROUP BY a.year_key, a.gender_key, a.activity_key ORDER BY a.year_key, a.gender_key, percentage DESC"
        
        with get_engine().connect() as conn:
            df = pd.read_sql(text(query), conn)
        logger.info(f"✓ Activity distribution loaded: {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"✗ Error loading activity distribution: {e}")
        return None