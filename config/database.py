from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import logging
from config.settings import DATABASE_URL

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Singleton connection manager untuk database MySQL"""
    _instance = None
    _engine = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_engine(cls):
        """Dapatkan SQLAlchemy engine (singleton)"""
        if cls._engine is None:
            try:
                cls._engine = create_engine(
                    DATABASE_URL,
                    poolclass=QueuePool,
                    pool_size=5,
                    max_overflow=10,
                    pool_recycle=3600,
                    echo=False
                )
                logger.info("✓ Database connection established")
            except Exception as e:
                logger.error(f"✗ Failed to create engine: {e}")
                raise
        return cls._engine
    
    @staticmethod
    def load_to_sql(df, table_name, if_exists="replace", index=False):
        """Load DataFrame ke database dengan error handling"""
        try:
            engine = DatabaseConnection.get_engine()
            with engine.begin() as conn:
                df.to_sql(
                    name=table_name,
                    con=conn,
                    if_exists=if_exists,
                    index=index,
                )
            logger.info(f"✓ Data loaded to '{table_name}' ({len(df)} rows)")
            return True
        except Exception as e:
            logger.error(f"✗ Error loading data to {table_name}: {e}")
            return False
    
    @staticmethod
    def execute_query(query_sql):
        """Execute raw SQL query"""
        try:
            engine = DatabaseConnection.get_engine()
            with engine.connect() as conn:
                result = conn.execute(text(query_sql))
                conn.commit()
            logger.info("✓ Query executed successfully")
            return result
        except Exception as e:
            logger.error(f"✗ Error executing query: {e}")
            raise


# Shortcut functions
def get_engine():
    return DatabaseConnection.get_engine()


def load_dataframe_to_sql(df, table_name, if_exists="replace"):
    return DatabaseConnection.load_to_sql(df, table_name, if_exists)