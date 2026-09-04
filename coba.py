
from src.dataloader import get_analytics_data, get_forecast_data
import matplotlib.pyplot as plt
import numpy as np

# Menampilkan total missing values tiap kolom

df = get_analytics_data()
print(df.isnull().sum())
# Cek tahun pada baris yang memiliki nilai NaN di pct_beban_rt_p
missing_year = df[df['pct_beban_rt_p'].isnull()]['year_key'].unique()
print("Tahun penyebab missing values:", missing_year)
# Filter hanya tahun-tahun yang memiliki data lengkap
df_clean = df.dropna(subset=['pct_beban_rt_p']).copy()

# Cek hasil: missing values akan menjadi 0 di seluruh kolom
print(df_clean.isnull().sum())
print("Tahun yang digunakan:", sorted(df_clean['year_key'].unique()))




# 1. Pastikan data sudah bersih dari NaN (menggunakan tahun lengkap)
df_clean = df.dropna(
    subset=['tpak_p', 'wage_ratio_nasional', 'pct_beban_rt_p']
).copy()

# 2. Pilih variabel yang ingin dianalisis korelasinya
features = [
    'tpak_p',
    'tpak_l',
    'tpak_gap',
    'wage_ratio_nasional',
    'pct_beban_rt_p',
    'pct_bekerja_p',
    'pct_sekolah_p',
]

# Ganti label agar nama variabel di grafik lebih formal dan terbaca
labels = [
    'TPAK Perempuan',
    'TPAK Laki-laki',
    'TPAK Gap (L-P)',
    'Rasio Upah (P/L)',
    '% Beban RT (P)',
    '% Bekerja (P)',
    '% Sekolah (P)',
]

# 3. Hitung matriks korelasi Pearson
corr_matrix = df_clean[features].corr()

# 4. Buat mask untuk menutupi bagian segitiga atas
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))

# 5. Plotting

plt.figure(figsize=(9, 7))
sns.heatmap(
    corr_matrix,
    annot=True,
    fmt='.2f',
    cmap='coolwarm',
    vmin=-1,
    vmax=1,
    center=0,
    square=True,
    xticklabels=labels,
    yticklabels=labels,
)


plt.title('Matriks Korelasi Indikator Gender & Ketenagakerjaan', fontsize=12, pad=15)
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)
plt.tight_layout()
plt.show()


import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# 1. Ringkasan Statistik Deskriptif Numerik
tpak_vars = ['tpak_l', 'tpak_p', 'tpak_gap', 'pct_beban_rt_p']
print(df_clean[tpak_vars].describe().T[['mean', 'std', 'min', '50%', 'max']])

# 2. Visualisasi Distribusi & Deteksi Outlier (Histogram + Boxplot)
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Distribusi TPAK Perempuan
sns.histplot(
    df_clean['tpak_p'],
    kde=True,
    ax=axes[0, 0],
    color='purple',
    bins=15,
)
axes[0, 0].set_title('Distribusi Frekuensi TPAK Perempuan')
axes[0, 0].set_xlabel('TPAK Perempuan (%)')

# Distribusi TPAK Laki-laki
sns.histplot(
    df_clean['tpak_l'],
    kde=True,
    ax=axes[0, 1],
    color='teal',
    bins=15,
)
axes[0, 1].set_title('Distribusi Frekuensi TPAK Laki-laki')
axes[0, 1].set_xlabel('TPAK Laki-laki (%)')

# Boxplot Perbandingan Sebaran TPAK L vs P
df_melt = df_clean.melt(
    value_vars=['tpak_l', 'tpak_p'],
    var_name='Gender',
    value_name='TPAK_Rate',
)
df_melt['Gender'] = df_melt['Gender'].map(
    {'tpak_l': 'Laki-laki', 'tpak_p': 'Perempuan'}
)
sns.boxplot(
    data=df_melt,
    x='Gender',
    y='TPAK_Rate',
    hue='Gender',
    palette=['teal', 'purple'],
    ax=axes[1, 0],
    legend=False,
)
axes[1, 0].set_title('Sebaran & Outlier: TPAK Laki-laki vs Perempuan')
axes[1, 0].set_ylabel('TPAK (%)')

# Boxplot Sebaran Kesenjangan Gender (TPAK Gap)
sns.boxplot(
    x=df_clean['tpak_gap'],
    ax=axes[1, 1],
    color='salmon',
)
axes[1, 1].set_title('Sebaran Kesenjangan Partisipasi (TPAK Gap L - P)')
axes[1, 1].set_xlabel('Selisih TPAK (% Poin)')

plt.tight_layout()
plt.show()


