# import numpy as np
# import pandas as pd
# from sklearn.linear_model import LinearRegression
# from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
# from sqlalchemy import create_engine, text

# # 1. Konfigurasi Koneksi Database MySQL
# DB_USER = "root"
# DB_PASS = ""
# DB_HOST = "localhost"
# DB_PORT = "3306"
# DB_NAME = "gender_analyst"

# engine = create_engine(
#     f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# )

# # 2. Query Ekstraksi Data yang Sesuai Struktur Skema Database
# query_sql = """
# SELECT 
#     f.year_key,
#     p.province_key,
#     p.province_name,
#     p.region_group,
#     MAX(CASE WHEN f.gender_key = 2 THEN f.tpak_rate_pct END) AS tpak_p,
#     MAX(CASE WHEN f.gender_key = 1 THEN f.tpak_rate_pct END) AS tpak_l,
#     w.wage_ratio_nasional,
#     act.pct_beban_rt_p,
#     act.pct_sekolah_p
# FROM fact_tpak_economics f
# JOIN dim_province p ON f.province_key = p.province_key
# LEFT JOIN (
#     SELECT 
#         year,
#         MAX(CASE WHEN gender_key = 2 THEN hourly_wage_idr END) / 
#         NULLIF(MAX(CASE WHEN gender_key = 1 THEN hourly_wage_idr END), 0) AS wage_ratio_nasional
#     FROM fact_wage_hourly
#     GROUP BY year
# ) w ON f.year_key = w.year
# LEFT JOIN (
#     SELECT 
#         a.year_key,
#         SUM(CASE WHEN a.activity_key = 3 THEN a.total_penduduk ELSE 0 END) * 100.0 / NULLIF(SUM(a.total_penduduk), 0) AS pct_beban_rt_p,
#         SUM(CASE WHEN a.activity_key = 5 THEN a.total_penduduk ELSE 0 END) * 100.0 / NULLIF(SUM(a.total_penduduk), 0) AS pct_sekolah_p
#     FROM fact_labor_activity a
#     WHERE a.gender_key = 2
#     GROUP BY a.year_key
# ) act ON f.year_key = act.year_key
# GROUP BY 
#     f.year_key, 
#     p.province_key, 
#     p.province_name, 
#     p.region_group, 
#     w.wage_ratio_nasional, 
#     act.pct_beban_rt_p, 
#     act.pct_sekolah_p;
# """

# print("[1/4] Mengambil dataset dari MySQL...")
# with engine.connect() as conn:
#   df = pd.read_sql(text(query_sql), conn)

# # 3. Pembersihan Data & Persiapan Fitur
# df_model = df.dropna(
#     subset=[
#         "tpak_p",
#         "pct_beban_rt_p",
#         "pct_sekolah_p",
#         "wage_ratio_nasional",
#         "tpak_l",
#     ]
# ).copy()

# features = ["pct_beban_rt_p", "pct_sekolah_p", "wage_ratio_nasional", "tpak_l"]
# X = df_model[features]
# y = df_model["tpak_p"]

# # 4. Pelatihan Model Regresi Linier
# print("[2/4] Melatih Model Regresi Linier...")
# model = LinearRegression()
# model.fit(X, y)

# # Hasil prediksi dan nilai residual
# df_model["tpak_p_pred"] = np.round(model.predict(X), 2)
# df_model["residual"] = np.round(df_model["tpak_p"] - df_model["tpak_p_pred"], 2)

# # Evaluasi Metrik
# r2 = r2_score(y, df_model["tpak_p_pred"]) * 100
# mae = mean_absolute_error(y, df_model["tpak_p_pred"])
# rmse = np.sqrt(mean_squared_error(y, df_model["tpak_p_pred"]))

# print("\n--- Evaluasi Model ---")
# print(f"R² Score : {r2:.2f}%")
# print(f"MAE      : {mae:.3f}")
# print(f"RMSE     : {rmse:.3f}\n")

# # 5. Menyimpan Hasil Prediksi ke MySQL
# print("[3/4] Menyimpan tabel hasil prediksi ke MySQL...")
# output_cols = [
#     "year_key",
#     "province_key",
#     "tpak_p",
#     "tpak_p_pred",
#     "residual",
#     "pct_beban_rt_p",
#     "pct_sekolah_p",
#     "wage_ratio_nasional",
#     "tpak_l",
# ]

# df_model[output_cols].to_sql(
#     name="fact_tpak_prediction", con=engine, if_exists="replace", index=False)

# # 6. Menyimpan Parameter Koefisien Model ke Tabel Metadata
# df_coef = pd.DataFrame(
#     {
#         "feature_name": features + ["intercept"],
#         "coefficient_value": list(np.round(model.coef_, 4))
#         + [round(model.intercept_, 4)],
#         "r2_percentage": [f"{r2:.2f}%"] * (len(features) + 1),
#         "mae": [round(mae, 4)] * (len(features) + 1),
#         "rmse": [round(rmse, 4)] * (len(features) + 1),
#     }
# )

# df_coef.to_sql(
#     name="dim_model_metrics", con=engine, if_exists="replace", index=False
# )

# print(
#     "[4/4] Proses Selesai! Tabel 'fact_tpak_prediction' dan 'dim_model_metrics'"
#     " siap digunakan."
# )

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sqlalchemy import create_engine, text

# 1. Koneksi Database
engine = create_engine('mysql+pymysql://root:@localhost:3306/gender_analyst')

# 2. Ambil Data Historis Terakhir per Provinsi
query_last = """
SELECT 
    f.province_key,
    p.province_name,
    MAX(f.year_key) AS last_year,
    f.pct_beban_rt_p,
    f.pct_sekolah_p,
    f.wage_ratio_nasional,
    f.tpak_l,
    f.tpak_p AS last_actual_tpak_p
FROM fact_tpak_prediction f
JOIN dim_province p ON f.province_key = p.province_key
WHERE f.year_key = (SELECT MAX(year_key) FROM fact_tpak_prediction)
GROUP BY f.province_key, p.province_name, f.pct_beban_rt_p, f.pct_sekolah_p, f.wage_ratio_nasional, f.tpak_l, f.tpak_p;
"""

df_last = pd.read_sql(query_last, engine)

# 3. Ambil Koefisien Model dari Metadata
df_coef = pd.read_sql('SELECT * FROM dim_model_metrics', engine)
coef_dict = dict(zip(df_coef['feature_name'], df_coef['coefficient_value']))

# 4. Generate Skenario Masa Depan (Contoh: Proyeksi 3 Tahun ke Depan)
future_years = [2026, 2027, 2028]
forecast_records = []

for _, row in df_last.iterrows():
  curr_beban = row['pct_beban_rt_p']
  curr_sekolah = row['pct_sekolah_p']
  curr_wage = row['wage_ratio_nasional']
  curr_tpak_l = row['tpak_l']

  for step, yr in enumerate(future_years, start=1):
    # Asumsi tren moderat:
    # - Beban RT perempuan turun 0.5% per tahun
    # - Rasio upah perempuan naik 0.01 per tahun
    # - Partisipasi sekolah naik tipis 0.2% per tahun
    sim_beban = max(curr_beban - (0.5 * step), 0)
    sim_sekolah = curr_sekolah + (0.2 * step)
    sim_wage = curr_wage + (0.01 * step)
    sim_tpak_l = curr_tpak_l

    # Hitung Prediksi menggunakan formula OLS: y = beta_0 + sum(beta_i * X_i)
    pred_future = (
        coef_dict['intercept']
        + (coef_dict['pct_beban_rt_p'] * sim_beban)
        + (coef_dict['pct_sekolah_p'] * sim_sekolah)
        + (coef_dict['wage_ratio_nasional'] * sim_wage)
        + (coef_dict['tpak_l'] * sim_tpak_l)
    )

    forecast_records.append({
        'year_key': yr,
        'province_key': row['province_key'],
        'province_name': row['province_name'],
        'scenario_type': 'Targeted Policy (Moderat)',
        'pct_beban_rt_p_proj': round(sim_beban, 2),
        'wage_ratio_proj': round(sim_wage, 3),
        'tpak_p_forecast': round(pred_future, 2),
    })

df_forecast = pd.DataFrame(forecast_records)

# 5. Simpan Hasil Forecast ke MySQL
df_forecast.to_sql(
    name='fact_tpak_forecast', con=engine, if_exists='replace', index=False
)
print(
    f'[SUKSES] {len(df_forecast)} baris data proyeksi berhasil disimpan ke'
    " tabel 'fact_tpak_forecast'."
)