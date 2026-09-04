import os
from dotenv import load_dotenv

# Load environment variables dari .env
load_dotenv()

# ==================== DATABASE CONFIGURATION ====================
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "gender_analyst")

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# ==================== FILE PATHS ====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

PATH_DATA_AKTIVITAS = os.path.join(DATA_RAW_DIR, "data_aktivitas")
PATH_DATA_UPAH = os.path.join(DATA_RAW_DIR, "data_upah")
PATH_DATA_TPAK = os.path.join(DATA_RAW_DIR, "data_tpak")

# ==================== ETL SETTINGS ====================
ENCODING = "utf-8-sig"
CHUNK_SIZE = 10000

# ==================== MODEL SETTINGS ====================
MODEL_TEST_SIZE = 0.2
MODEL_RANDOM_STATE = 42

# ==================== LOGGING ====================
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"