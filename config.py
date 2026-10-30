
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()  # reads DB credentials from the .env file
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent
RAW_IBM_CSV = BASE_DIR / "data" / "raw" / "WA_Fn-UseC_-HR-Employee-Attrition.csv"
OUTPUT_DIR = BASE_DIR / "data" / "synthesized"
STAGING_SCHEMA_SQL = BASE_DIR / "sql" / "staging_schema.sql"

TARGET_ROWS = 100000                  
SCD2_CHANGE_FRACTION = 0.25          
RANDOM_SEED = 42                     
REFERENCE_DATE = str(date.today())    
FAKER_LOCALE = "en_IN"                

CHUNK_SIZE = 5000                     
CREATE_SCHEMA = True                  

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
        staging_db=os.getenv("STAGING_DB_NAME", os.getenv("DB_NAME", "GreenFieldMiniProject_STG")),
        oltp_db=os.getenv("OLTP_DB_NAME", "GreenFieldMiniProject_OLTP"),
        olap_db=os.getenv("OLAP_DB_NAME", "GreenFieldMiniProject_OLAP"),
        pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
    )

# Load typed settings
db_settings = load_settings()

# Module 2 pipeline & database settings
STAGING_DB = db_settings.staging_db
OLTP_DB = db_settings.oltp_db
OLAP_DB = db_settings.olap_db
RUN_WAREHOUSE_ETL = os.getenv("RUN_WAREHOUSE_ETL", "true").lower() == "true"

# Schema creation scripts in dependency order
SCHEMA_SCRIPTS = [
    BASE_DIR / "sql" / "staging_schema.sql",
    BASE_DIR / "sql" / "Schema_Definition" / "OLTP_Schema_DDL.sql",
    BASE_DIR / "sql" / "Schema_Definition" / "OLAP_Schema_DDL.sql",
    BASE_DIR / "sql" / "staging_to_warehouse.sql",
    BASE_DIR / "sql" / "Schema_Definition" / "ETL_Stored_Procedures.sql",
]

# Backward compatibility dict for Module 2 scripts expecting `DB_CONFIG`
DB_CONFIG = {
    "host": db_settings.host,
    "port": db_settings.port,
    "user": db_settings.user,
    "password": db_settings.password,
    "database": db_settings.staging_db,
}

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
