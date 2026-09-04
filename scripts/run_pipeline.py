import sys
import os
import logging
from datetime import datetime

# Setup path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config.settings import (
    PATH_DATA_AKTIVITAS, PATH_DATA_UPAH, PATH_DATA_TPAK,
    LOG_FORMAT, LOG_LEVEL
)
from config.database import load_dataframe_to_sql
from src.etl.etl_activity import process_all_activities
from src.etl.etl_wage import process_all_wage_files
from src.etl.etl_tpak import process_tpak

# Setup logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def run_etl_pipeline():
    """Menjalankan full ETL pipeline secara berurutan"""
    
    logger.info("="*70)
    logger.info(f"MEMULAI ETL PIPELINE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*70)
    
    success_count = 0
    total_stages = 3
    
    # ============ 1. ETL TPAK ============
    try:
        logger.info("\n[1/3] Processing TPAK Data...")
        df_tpak = process_tpak(PATH_DATA_TPAK)
        if df_tpak is not None:
            if load_dataframe_to_sql(df_tpak, "fact_tpak_economics"):
                success_count += 1
    except Exception as e:
        logger.error(f"✗ TPAK ETL failed: {e}")
    
    # ============ 2. ETL UPAH ============
    try:
        logger.info("\n[2/3] Processing Wage Data...")
        df_wage = process_all_wage_files(PATH_DATA_UPAH)
        if df_wage is not None:
            if load_dataframe_to_sql(df_wage, "fact_wage_hourly"):
                success_count += 1
    except Exception as e:
        logger.error(f"✗ Wage ETL failed: {e}")
    
    # ============ 3. ETL AKTIVITAS ============
    try:
        logger.info("\n[3/3] Processing Labor Activity Data...")
        df_activity = process_all_activities(PATH_DATA_AKTIVITAS)
        if df_activity is not None:
            if load_dataframe_to_sql(df_activity, "fact_labor_activity"):
                success_count += 1
    except Exception as e:
        logger.error(f"✗ Activity ETL failed: {e}")
    
    # ============ SUMMARY ============
    logger.info("\n" + "="*70)
    logger.info(f"✓ ETL Pipeline Completed: {success_count}/{total_stages} stages successful")
    logger.info("="*70 + "\n")
    
    return success_count == total_stages


if __name__ == "__main__":
    success = run_etl_pipeline()
    sys.exit(0 if success else 1)