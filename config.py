"""Central configuration. Values come from environment variables / .env."""
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

# Optional dotenv loading (Streamlit Cloud, for instance, uses its own secrets management)
try:
    from dotenv import load_dotenv
    load_dotenv()  # reads DB credentials from the .env file
except ImportError:
    pass

# ==========================================
# Paths & File Settings
# ==========================================
BASE_DIR = Path(__file__).resolve().parent
RAW_IBM_CSV = BASE_DIR / "data" / "raw" / "WA_Fn-UseC_-HR-Employee-Attrition.csv"
OUTPUT_DIR = BASE_DIR / "data" / "synthesized"
STAGING_SCHEMA_SQL = BASE_DIR / "sql" / "staging_schema.sql"

# ==========================================
# Synthesis Settings
# ==========================================
TARGET_ROWS = 100000                  # number of employees to generate
SCD2_CHANGE_FRACTION = 0.25           # share of employees that get history changes
RANDOM_SEED = 42                      # same seed gives the same data every run
REFERENCE_DATE = str(date.today())    # "today" used for hire/termination dates
FAKER_LOCALE = "en_IN"                # Indian names and cities

# ==========================================
# Loader Settings
# ==========================================
CHUNK_SIZE = 5000                     # rows inserted per batch
CREATE_SCHEMA = True                  # True = drop and recreate stg_ tables, False = only empty them

# ==========================================
# Database Configuration
# ==========================================
@dataclass(frozen=True)
class DBSettings:
    host: str
    port: int
    user: str
    password: str
    staging_db: str
    oltp_db: str
    olap_db: str
    pool_size: int

def load_settings() -> DBSettings:
    return DBSettings(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        staging_db=os.getenv("DB_NAME", "greenfield_staging"),
        oltp_db=os.getenv("OLTP_DB_NAME", "GreenFieldMiniProject_OLTP"),
        olap_db=os.getenv("OLAP_DB_NAME", "GreenFieldMiniProject_OLAP"),
        pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
    )

# Load typed settings
db_settings = load_settings()

# Backward compatibility dict for Module 2 scripts expecting `DB_CONFIG`
DB_CONFIG = {
    "host": db_settings.host,
    "port": db_settings.port,
    "user": db_settings.user,
    "password": db_settings.password,
    "database": db_settings.staging_db,
}

# ==========================================
# Table & Schema Mapping
# ==========================================
# Logical name -> staging table name
TABLE_MAP = {
    "dim_date": "stg_dim_date",
    "employees": "stg_employees",
    "history": "stg_employee_history",
    "projects": "stg_projects",
    "assignments": "stg_project_assignments",
    "reviews": "stg_performance_reviews",
}

# Logical name -> CSV file written by run_synthesis.py
CSV_FILES = {
    "dim_date": "dim_date.csv",
    "employees": "employees.csv",
    "history": "employee_history.csv",
    "projects": "projects.csv",
    "assignments": "project_assignments.csv",
    "reviews": "performance_reviews.csv",
}

# Optional column renames per table, e.g. {"employees": {"monthly_income": "salary"}}
COLUMN_RENAMES = {}