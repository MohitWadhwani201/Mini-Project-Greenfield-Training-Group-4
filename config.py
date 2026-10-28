# Central settings for Module 2 - edit values here instead of using command-line options.
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # reads DB credentials from the .env file

BASE_DIR = Path(__file__).resolve().parent
RAW_IBM_CSV = BASE_DIR / "data" / "raw" / "WA_Fn-UseC_-HR-Employee-Attrition.csv"
OUTPUT_DIR = BASE_DIR / "data" / "synthesized"
STAGING_SCHEMA_SQL = BASE_DIR / "sql" / "staging_schema.sql"

# Synthesis settings
TARGET_ROWS = 100000                  # number of employees to generate
SCD2_CHANGE_FRACTION = 0.25           # share of employees that get history changes
RANDOM_SEED = 42                      # same seed gives the same data every run
REFERENCE_DATE = str(date.today())    # "today" used for hire/termination dates
FAKER_LOCALE = "en_IN"                # Indian names and cities

# Loader settings
CHUNK_SIZE = 5000                     # rows inserted per batch
CREATE_SCHEMA = True                  # True = drop and recreate stg_ tables, False = only empty them

# Database connection (values come from .env)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "greenfield_staging"),
}

# Logical name -> staging table name (change here when Person 1's schema is final)
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
