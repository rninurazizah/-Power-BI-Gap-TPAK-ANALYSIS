import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import text
import logging
from config.database import get_engine
from scipy.stats import gaussian_kde

logger = logging.getLogger(__name__)

sns.set_style("whitegrid")
plt.rcParams['font.size'] = 11


class Analysis:
    """Analisis Sederhana: Profiling + Visualisasi"""
    
    def __init__(self):
        try:
            self.engine = get_engine()
            self.df = None
            logger.info("✓ Analysis initialized")
        except Exception as e:
            logger.error(f"✗ Failed to initialize: {e}")
            raise
    
    def load_data(self):
        """Load data dari database"""
        query = """
        SELECT 
            f.year_key,
            p.province_name,
            MAX(CASE WHEN f.gender_key = 2 THEN f.tpak_rate_pct END) AS tpak_p,
            MAX(CASE WHEN f.gender_key = 1 THEN f.tpak_rate_pct END) AS tpak_l,
            w.wage_ratio_nasional,
            act.pct_beban_rt_p,
            act.pct_bekerja_p,
            act.pct_sekolah_p
        FROM fact_tpak_economics f
        JOIN dim_province p ON f.province_key = p.province_key
        LEFT JOIN (
            SELECT year, MAX(CASE WHEN gender_key = 2 THEN hourly_wage_idr END) / 
                    MAX(CASE WHEN gender_key = 1 THEN hourly_wage_idr END) AS wage_ratio_nasional
            FROM fact_wage_hourly GROUP BY year
        ) w ON f.year_key = w.year
        LEFT JOIN (
            SELECT a.year_key,
                SUM(CASE WHEN a.activity_key = 3 THEN a.total_penduduk ELSE 0 END) * 100.0 / SUM(a.total_penduduk) AS pct_beban_rt_p,
                SUM(CASE WHEN a.activity_key = 1 THEN a.total_penduduk ELSE 0 END) * 100.0 / SUM(a.total_penduduk) AS pct_bekerja_p,
                SUM(CASE WHEN a.activity_key = 5 THEN a.total_penduduk ELSE 0 END) * 100.0 / SUM(a.total_penduduk) AS pct_sekolah_p
            FROM fact_labor_activity a WHERE a.gender_key = 2 GROUP BY a.year_key
        ) act ON f.year_key = act.year_key
        GROUP BY f.year_key, p.province_key, p.province_name, w.wage_ratio_nasional, 
                act.pct_beban_rt_p, act.pct_bekerja_p, act.pct_sekolah_p
        """
        
        try:
            with self.engine.connect() as conn:
                self.df = pd.read_sql(text(query), conn)
            logger.info(f"✓ Data loaded: {len(self.df)} rows")
            return self.df
        except Exception as e:
            logger.error(f"✗ Error loading data: {e}")
            return None
    
    # ========== DATA PROFILING ==========
    
    def profile_data(self):
        """Cek duplikasi, missing values, dan statistik data"""
        if self.df is None:
            self.load_data()
        
        print("\n" + "="*80)
        print("📊 DATA PROFILING".center(80))
        print("="*80)
        
        # Duplikasi
        dup_count = self.df.duplicated().sum()
        print(f"\n🔍 Duplicates: {dup_count} rows")
        
        # Missing Values
        print(f"\n🚨 Missing Values:")
        missing = self.df.isnull().sum()
        for col in self.df.columns:
            if missing[col] > 0:
                pct = (missing[col] / len(self.df)) * 100
                print(f"  {col:<25}: {missing[col]:>3} ({pct:>5.2f}%)")
        
        if missing.sum() == 0:
            print("  ✓ No missing values")
        
        # Numeric Features
        print(f"\n🔢 Numeric Features:")
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            data = self.df[col].dropna()
            print(f"  {col:<25}: mean={data.mean():.2f}, std={data.std():.2f}, "
                  f"min={data.min():.2f}, max={data.max():.2f}")
        
        # Categorical Features
        print(f"\n🏷️  Categorical Features:")
        cat_cols = self.df.select_dtypes(include=['object']).columns
        for col in cat_cols:
            print(f"  {col:<25}: {self.df[col].nunique()} unique values")
        
        print("\n" + "="*80 + "\n")
    
    # ========== VISUALISASI ==========
    
    def plot_tpak_skewness(self, save_path=None):
        """Skewness TPAK Perempuan & Laki-laki"""
        if self.df is None:
            self.load_data()
        
        logger.info("📊 Creating TPAK Skewness plots...")
        
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        for idx, (col, color, title) in enumerate([
            ('tpak_p', '#FF6B9D', 'TPAK Perempuan 👩'),
            ('tpak_l', '#4A90E2', 'TPAK Laki-laki 👨')
        ]):
            data = self.df[col].dropna()
            ax = axes[idx]
            
            # Histogram + KDE
            ax.hist(data, bins=25, alpha=0.7, color=color, edgecolor='black', density=True)
            kde = gaussian_kde(data)
            x = np.linspace(data.min(), data.max(), 100)
            ax.plot(x, kde(x), 'r-', linewidth=2.5, label='KDE')
            
            # Mean & Median
            ax.axvline(data.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {data.mean():.2f}')
            ax.axvline(data.median(), color='green', linestyle='--', linewidth=2, label=f'Median: {data.median():.2f}')
            
            skew = data.skew()
            ax.set_title(f'{title}\nSkewness: {skew:.4f}', fontsize=12, fontweight='bold')
            ax.set_xlabel('TPAK Rate (%)', fontsize=10)
            ax.set_ylabel('Density', fontsize=10)
            ax.legend(fontsize=9)
            ax.grid(True, alpha=0.3)
            
            print(f"\n{title}: Mean={data.mean():.2f}, Median={data.median():.2f}, "
                  f"Skewness={skew:.4f}")
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"✓ Saved: {save_path}")
        plt.show()
        return fig
    
    def plot_household_boxplot(self, save_path=None):
        """Boxplot Beban RT Perempuan & Laki-laki"""
        if self.df is None:
            self.load_data()
        
        logger.info("📦 Creating Household Burden Boxplot...")
        
        fig, ax = plt.subplots(figsize=(12, 7))
        
        data_beban_p = self.df['pct_beban_rt_p'].dropna()
        
        bp = ax.boxplot(
            [data_beban_p],
            labels=['Beban RT Perempuan (%)'],
            patch_artist=True,
            notch=True,
            showmeans=True,
            meanprops=dict(marker='D', markerfacecolor='red', markersize=8)
        )
        
        for patch in bp['boxes']:
            patch.set_facecolor('#FF6B9D')
            patch.set_alpha(0.7)
        
        for median in bp['medians']:
            median.set(color='darkblue', linewidth=2)
        
        ax.set_title('📦 Beban Rumah Tangga Perempuan (Boxplot)', fontsize=13, fontweight='bold')
        ax.set_ylabel('Percentage (%)', fontsize=11)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Outliers info
        q1 = data_beban_p.quantile(0.25)
        q3 = data_beban_p.quantile(0.75)
        iqr = q3 - q1
        outliers = data_beban_p[(data_beban_p < q1 - 1.5*iqr) | (data_beban_p > q3 + 1.5*iqr)]
        
        print(f"\n📦 Beban RT Perempuan:")
        print(f"  Mean: {data_beban_p.mean():.2f}%, Median: {data_beban_p.median():.2f}%")
        print(f"  Outliers: {len(outliers)} ({len(outliers)/len(data_beban_p)*100:.1f}%)")
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"✓ Saved: {save_path}")
        plt.show()
        return fig
    
    def plot_correlation_heatmap(self, save_path=None):
        """Heatmap Korelasi dengan TPAK Gap"""
        if self.df is None:
            self.load_data()
        
        logger.info("🔥 Creating Correlation Heatmap...")
        
        # Tambahkan tpak_gap ke kolom yang akan dianalisis
        numeric_cols = ['tpak_p', 'tpak_l', 'tpak_gap', 'wage_ratio_nasional', 
                       'pct_beban_rt_p', 'pct_bekerja_p', 'pct_sekolah_p']
        numeric_cols = [col for col in numeric_cols if col in self.df.columns]
        
        # Hitung tpak_gap jika belum ada
        if 'tpak_gap' not in self.df.columns:
            self.df['tpak_gap'] = self.df['tpak_l'] - self.df['tpak_p']
        
        corr = self.df[numeric_cols].corr()
        
        fig, ax = plt.subplots(figsize=(12, 10))
        sns.heatmap(corr, annot=True, fmt='.3f', cmap='coolwarm', center=0, 
                   square=True, linewidths=2, cbar_kws={"shrink": 0.8}, 
                   vmin=-1, vmax=1, ax=ax, annot_kws={"size": 10})
        
        ax.set_title('🔥 Correlation Heatmap (dengan TPAK Gap)', fontsize=13, fontweight='bold', pad=20)
        plt.xticks(rotation=45, ha='right', fontsize=10)
        plt.yticks(rotation=0, fontsize=10)
        plt.tight_layout()
        
        # Print strong correlations
        print(f"\n🔗 Strong Correlations (|r| > 0.5):")
        found = False
        for i in range(len(corr.columns)):
            for j in range(i+1, len(corr.columns)):
                if abs(corr.iloc[i, j]) > 0.5:
                    found = True
                    print(f"  {corr.columns[i]:<20} ↔ {corr.columns[j]:<20}: {corr.iloc[i, j]:>8.4f}")
        if not found:
            print("  None found")
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"✓ Saved: {save_path}")
        plt.show()
        return fig, corr
    def generate_report(self, output_dir='notebooks'):
        """Generate semua laporan & visualisasi"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info("\n" + "="*80)
        logger.info("ANALYSIS REPORT".center(80))
        logger.info("="*80)
        
        # Load data
        self.load_data()
        if self.df is None:
            return False
        
        # Profiling
        self.profile_data()
        
        # Visualisasi
        self.plot_tpak_skewness(f'{output_dir}/01_tpak_skewness.png')
        self.plot_household_boxplot(f'{output_dir}/02_household_boxplot.png')
        self.plot_correlation_heatmap(f'{output_dir}/03_correlation_heatmap.png')
        
        logger.info("\n" + "="*80)
        logger.info("✓ REPORT GENERATED".center(80))
        logger.info("="*80 + "\n")
        return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    Analysis().generate_report()