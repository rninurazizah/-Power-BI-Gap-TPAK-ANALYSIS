import os
import sys
from config.database import load_dataframe_to_sql
from etl_activity import process_all_activities
from etl import process_tpak
from etl_wage import process_all_wage_files, process_all_wage_files


DB_CONFIG = {
    "user": "root",
    "password": "",
    "host": "localhost",
    "port": "3306",
    "database": "gender_analyst",
}

CONNECTION_STR = (
    f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
    f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)


def get_db_engine():
    try:
        engine = create_engine(CONNECTION_STR)
        return engine
    except Exception as e:
        print(f"[ERROR] Gagal membuat koneksi database: {e}")
        sys.exit(1)

        
# # Path Direktori
# CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# if CURRENT_DIR not in sys.path:
#   sys.path.append(CURRENT_DIR)

# DATA_DIR = r"D:\Documents\BI project\data_upah"

# if __name__ == "__main__":
#   # 1. Jalankan ETL Upah
#   print("--- Memulai ETL Upah Rata-Rata Per Jam ---")
#   df_wages = process_all_wage_files(DATA_DIR)
#   if df_wages is not None:
#     load_dataframe_to_sql(df_wages, table_name="fact_wage_hourly")
# if __name__ == "__main__":
#   # 1. Jalankan ETL Kegiatan Utama (Why Data)
#   print("--- Memulai ETL Kegiatan Utama ---")
#   df_activity = process_all_activities(DATA_DIR)
#   if df_activity is not None:
#     load_dataframe_to_sql(df_activity, table_name="stg_labor_activity")

  # 2. (Opsional) Uncomment jika ingin memperbarui data TPAK juga
  # print("\n--- Memulai ETL TPAK ---")
  # df_tpak = process_tpak(DATA_DIR)
  # if df_tpak is not None:
  #     load_dataframe_to_sql(df_tpak, table_name="stg_tpak_clean")