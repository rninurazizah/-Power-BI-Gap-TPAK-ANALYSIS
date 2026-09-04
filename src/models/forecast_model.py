import numpy as np
import pandas as pd
import logging
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sqlalchemy import text
from config.database import get_engine

logger = logging.getLogger(__name__)


def get_model_data():
    """Query data untuk training model"""
    query = """
    SELECT 
        f.year_key,
        p.province_key,
        p.province_name,
        p.region_group,
        MAX(CASE WHEN f.gender_key = 2 THEN f.tpak_rate_pct END) AS tpak_p,
        MAX(CASE WHEN f.gender_key = 1 THEN f.tpak_rate_pct END) AS tpak_l,
        w.wage_ratio_nasional,
        act.pct_beban_rt_p,
        act.pct_sekolah_p
    FROM fact_tpak_economics f
    JOIN dim_province p ON f.province_key = p.province_key
    LEFT JOIN (
        SELECT 
            year,
            MAX(CASE WHEN gender_key = 2 THEN hourly_wage_idr END) / 
            NULLIF(MAX(CASE WHEN gender_key = 1 THEN hourly_wage_idr END), 0) AS wage_ratio_nasional
        FROM fact_wage_hourly
        GROUP BY year
    ) w ON f.year_key = w.year
    LEFT JOIN (
        SELECT 
            a.year_key,
            SUM(CASE WHEN a.activity_key = 3 THEN a.total_penduduk ELSE 0 END) * 100.0 / NULLIF(SUM(a.total_penduduk), 0) AS pct_beban_rt_p,
            SUM(CASE WHEN a.activity_key = 5 THEN a.total_penduduk ELSE 0 END) * 100.0 / NULLIF(SUM(a.total_penduduk), 0) AS pct_sekolah_p
        FROM fact_labor_activity a
        WHERE a.gender_key = 2
        GROUP BY a.year_key
    ) act ON f.year_key = act.year_key
    GROUP BY f.year_key, p.province_key, p.province_name, p.region_group, w.wage_ratio_nasional, act.pct_beban_rt_p, act.pct_sekolah_p
    """
    
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)


def train_forecast_model(df_model):
    """Train model regresi linier"""
    logger.info("[1/3] Preparing data for model training...")
    
    df_clean = df_model.dropna(subset=[
        'tpak_p', 'pct_beban_rt_p', 'pct_sekolah_p', 
        'wage_ratio_nasional', 'tpak_l'
    ]).copy()
    
    features = ['pct_beban_rt_p', 'pct_sekolah_p', 'wage_ratio_nasional', 'tpak_l']
    X = df_clean[features]
    y = df_clean['tpak_p']
    
    logger.info("[2/3] Training Linear Regression Model...")
    model = LinearRegression()
    model.fit(X, y)
    
    # Hasil prediksi
    df_clean['tpak_p_pred'] = np.round(model.predict(X), 2)
    df_clean['residual'] = np.round(df_clean['tpak_p'] - df_clean['tpak_p_pred'], 2)
    
    return model, df_clean, features


def evaluate_model(y_true, y_pred):
    """Evaluasi performa model"""
    r2 = r2_score(y_true, y_pred) * 100
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    
    metrics = {
        'r2_score': round(r2, 2),
        'mae': round(mae, 3),
        'rmse': round(rmse, 3),
    }
    
    logger.info("\n--- Model Evaluation ---")
    logger.info(f"R² Score : {metrics['r2_score']}%")
    logger.info(f"MAE      : {metrics['mae']}")
    logger.info(f"RMSE     : {metrics['rmse']}\n")
    
    return metrics


def predict_tpak(model, X_new):
    """Prediksi TPAK untuk data baru"""
    return np.round(model.predict(X_new), 2)