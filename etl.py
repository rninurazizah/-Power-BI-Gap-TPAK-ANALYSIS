import glob
import os
import re
import numpy as np
import pandas as pd


def process_tpak(folder_path):
  search_pattern = os.path.join(folder_path, "*tpak*.csv")
  file_list = [f for f in glob.glob(search_pattern) if os.path.isfile(f)]
  if not file_list:
    file_list = [
        f
        for f in glob.glob(os.path.join(folder_path, "*.csv"))
        if "Kegiatan" not in f
    ]

  combined_data = []
  for file_path in file_list:
    match_year = re.search(r"(\d{4})", os.path.basename(file_path))
    year_val = int(match_year.group(1)) if match_year else None

    df = pd.read_csv(
        file_path,
        skiprows=4,
        header=None,
        names=["region_name", "tpak_male", "tpak_female"],
        encoding="utf-8-sig",
    )
    df["region_name"] = df["region_name"].astype(str).str.strip()
    df["tpak_male"] = pd.to_numeric(
        df["tpak_male"].replace("-", np.nan), errors="coerce"
    )
    df["tpak_female"] = pd.to_numeric(
        df["tpak_female"].replace("-", np.nan), errors="coerce"
    )
    df["year"] = year_val
    df["admin_level"] = df["region_name"].apply(
        lambda x: (
            "National"
            if x == "INDONESIA"
            else ("Province" if x.isupper() else "City_Regency")
        )
    )
    combined_data.append(df)

  if not combined_data:
    return None

  df_all = pd.concat(combined_data, ignore_index=True)
  df_prov = df_all[
      (df_all["admin_level"] == "Province")
      & (df_all["region_name"] != "INDONESIA")
  ].copy()

  df_long = pd.melt(
      df_prov,
      id_vars=["region_name", "year"],
      value_vars=["tpak_male", "tpak_female"],
      var_name="gender_raw",
      value_name="tpak_rate_pct",
  )
  df_long["gender_code"] = df_long["gender_raw"].map(
      {"tpak_male": "L", "tpak_female": "P"}
  )
  df_long.drop(columns=["gender_raw"], inplace=True)
  return df_long.dropna(subset=["tpak_rate_pct"]).reset_index(drop=True)