import glob
import os
import re
import pandas as pd


def process_all_wage_files(folder_path):
  search_pattern = os.path.join(folder_path, "*Upah*.csv")
  file_list = [f for f in glob.glob(search_pattern) if os.path.isfile(f)]

  if not file_list:
    print(f"Tidak ada file CSV Upah di: {folder_path}")
    return None

  print(
      f"Ditemukan {len(file_list)} file CSV Upah. Memulai proses"
      " penggabungan..."
  )
  combined_wages = []

  for file_path in file_list:
    try:
      # Ambil 4 digit tahun dari nama file
      match_year = re.search(r"(\d{4})", os.path.basename(file_path))
      year_val = int(match_year.group(1)) if match_year else None

      # Baca CSV tanpa header
      df = pd.read_csv(file_path, header=None, encoding="utf-8-sig")

      # Filter baris yang memuat teks Laki atau Perempuan
      df_clean = df[
          df[0]
          .astype(str)
          .str.contains("Laki|Perempuan", case=False, na=False)
      ].copy()
      df_clean.columns = ["gender_raw", "hourly_wage_idr"]

      # Standardisasi kode gender dan konversi tipe data angka
      df_clean["gender_code"] = df_clean["gender_raw"].apply(
          lambda x: "L" if "Laki" in str(x) else "P"
      )
      df_clean["hourly_wage_idr"] = (
          pd.to_numeric(
              df_clean["hourly_wage_idr"]
              .astype(str)
              .str.replace(",", "")
              .str.strip(),
              errors="coerce",
          )
          .fillna(0)
          .astype("int64")
      )
      df_clean["year"] = year_val

      combined_wages.append(
          df_clean[["year", "gender_code", "hourly_wage_idr"]]
      )
      print(f"  - Sukses memproses: {os.path.basename(file_path)} (Tahun {year_val})")

    except Exception as e:
      print(f"  - Gagal membaca {os.path.basename(file_path)}: {e}")

  if not combined_wages:
    return None

  df_all_wages = (
      pd.concat(combined_wages, ignore_index=True)
      .sort_values(by=["year", "gender_code"])
      .reset_index(drop=True)
  )

  print(
      f"\nTotal data upah berhasil digabung: {len(df_all_wages)} baris dari"
      f" {df_all_wages['year'].nunique()} tahun."
  )
  return df_all_wages