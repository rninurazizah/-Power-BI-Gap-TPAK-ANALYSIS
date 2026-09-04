import glob
import os
import re
import pandas as pd
from sqlalchemy import create_engine

# %% 1. Fungsi ETL Pengolahan File Kegiatan Utama


def process_all_activities(folder_path):
  file_list = sorted(glob.glob(os.path.join(folder_path, "*.csv")))
  file_list = [f for f in file_list if "tpak" not in os.path.basename(f).lower()]

  if not file_list:
    print(f"[PERINGATAN] Tidak ada file CSV yang ditemukan di: {folder_path}")
    return None

  print(
      f"Ditemukan {len(file_list)} file Kegiatan Utama. Memulai"
      " penggabungan..."
  )
  combined_list = []

  activity_id_map = {
      "Bekerja": 1,
      "Lainnya": 2,
      "Mengurus Rumah Tangga": 3,
      "Pengangguran": 4,
      "Sekolah": 5,
  }

  exclude_rows = [
      "I. Angkatan Kerja/Economically Active",
      "II. Bukan Angkatan Kerja/Not Economically Active",
      "Jumlah/Total",
  ]

  for file_path in file_list:
    filename = os.path.basename(file_path)
    try:
      # Ekstrak 4 digit tahun dari nama file
      match_year = re.search(r"(\d{4})", filename)
      year_val = int(match_year.group(1)) if match_year else None

      df = pd.read_csv(file_path, encoding="utf-8-sig")

      # 1. Hapus baris yang kolom 'Kegiatan Utama'-nya kosong (NaN/float)
      df = df.dropna(subset=["Kegiatan Utama"]).copy()

      # 2. Pastikan semua nilai di Kegiatan Utama adalah string murni
      df["Kegiatan Utama"] = df["Kegiatan Utama"].astype(str).str.strip()

      # 3. Filter baris header agregat
      df_filtered = df[~df["Kegiatan Utama"].isin(exclude_rows)].copy()

      # 4. Deteksi kolom gender secara dinamis
      gender_cols = [
          col
          for col in df_filtered.columns
          if "Laki-Laki" in str(col) and "Perempuan" not in str(col)
      ] + [
          col
          for col in df_filtered.columns
          if "Perempuan" in str(col) and "+" not in str(col)
      ]

      # 5. Unpivot (Melt)
      df_unpivoted = df_filtered.melt(
          id_vars=["Kegiatan Utama"],
          value_vars=gender_cols,
          var_name="gender_raw",
          value_name="total_penduduk",
      )

      # 6. Standardisasi Gender & Format Angka
      df_unpivoted["gender_raw"] = (
          df_unpivoted["gender_raw"].astype(str).str.strip()
      )
      df_unpivoted["gender_code"] = df_unpivoted["gender_raw"].apply(
          lambda x: "L" if "Laki-Laki" in x else "P"
      )
      df_unpivoted["gender_key"] = df_unpivoted["gender_code"].map(
          {"L": 1, "P": 2}
      )

      # Bersihkan titik pemisah ribuan dan ubah ke numerik
      df_unpivoted["total_penduduk"] = (
          pd.to_numeric(
              df_unpivoted["total_penduduk"]
              .astype(str)
              .str.replace(".", "", regex=False)
              .str.replace(",", "", regex=False)
              .str.strip(),
              errors="coerce",
          )
          .fillna(0)
          .astype("int64")
      )
      df_unpivoted["year_key"] = year_val

      # 7. Standardisasi Nama Kegiatan (Aman dari tipe float)
      def clean_kegiatan(x):
        x_str = str(x)
        if "Bekerja" in x_str:
          return "Bekerja"
        if "Pengangguran" in x_str:
          return "Pengangguran"
        if "Sekolah" in x_str:
          return "Sekolah"
        if "Mengurus Rumah" in x_str:
          return "Mengurus Rumah Tangga"
        return "Lainnya"

      df_unpivoted["kegiatan_nama"] = df_unpivoted["Kegiatan Utama"].apply(
          clean_kegiatan
      )
      df_unpivoted["activity_key"] = df_unpivoted["kegiatan_nama"].map(
          activity_id_map
      )

      # Pilih kolom rapi
      df_clean = df_unpivoted[[
          "year_key",
          "gender_key",
          "gender_code",
          "activity_key",
          "kegiatan_nama",
          "total_penduduk",
      ]]

      combined_list.append(df_clean)
      print(f"  [✓] Sukses memproses: {filename} (Tahun {year_val})")

    except Exception as e:
      print(f"  [✗] Gagal membaca {filename}: {e}")

  if not combined_list:
    return None

  # Gabungkan seluruh data dan urutkan
  df_all = (
      pd.concat(combined_list, ignore_index=True)
      .sort_values(by=["year_key", "gender_key", "activity_key"])
      .reset_index(drop=True)
  )

  print(
      f"\nTotal data berhasil disatukan: {len(df_all)} baris dari"
      f" {sorted(df_all['year_key'].unique())}"
  )
  return df_all


# %% 2. Eksekusi Pemrosesan & Timpa ke Database MySQL

folder_data = r"D:\Documents\BI project\data_aktivitas"
df_fact_activity = process_all_activities(folder_data)

if df_fact_activity is not None:
  engine = create_engine("mysql+pymysql://root:@localhost:3306/gender_analyst")

  with engine.begin() as conn:
    df_fact_activity.to_sql(
        name="fact_labor_activity",
        con=conn,
        if_exists="replace",
        index=False,
    )
  print(
      "\n[BERHASIL] Tabel fact_labor_activity di database gender_analyst telah"
      " diperbarui total!"
  )