# Enterprise HR Analytics & Data Warehouse Platform

A robust, full-stack backend data engineering and analytics solution featuring a 3-tier database architecture (**Staging**, **3NF OLTP**, and **Star-Schema OLAP Data Warehouse** with **Slowly Changing Dimensions Type 2**), synthetic data generation at scale, automated ETL pipelines, and an object-oriented Python Data Access Layer (DAL).

---

## Architecture Overview

```
                                      ┌────────────────────────────────────────────────────────┐
                                      │                      DATA INGESTION                    │
                                      │              (Data Synthesis & Generation)             │
                                      └────────────────────────────────────────────────────────┘
                                                                  │
                                                                  ▼
 [Raw IBM HR CSV] ──► run_synthesis.py ──► [Synthesized CSVs in data/synthesized/]
                                                                  │
                                                                  ▼ (BulkLoader via SQLAlchemy)
                                              ┌───────────────────────────────────────┐
                                              │ GreenFieldMiniProject_STG (Staging)   │
                                              │ stg_dim_date, stg_employees,          │
                                              │ stg_employee_history, stg_projects,   │
                                              │ stg_project_assignments, stg_reviews  │
                                              └───────────────────────────────────────┘
                                                                  │
                                                                  ▼ (warehouse_pipeline.py)
                       ┌──────────────────────────────────────────┴──────────────────────────────────────────┐
                       │                                                                                     │
                       ▼                                                                                     ▼
        ┌─────────────────────────────┐                                                       ┌─────────────────────────────┐
        │        OLTP DATABASE        │                                                       │       OLAP DATA WAREHOUSE   │
        │  GreenFieldMiniProject_OLTP │                                                       │  GreenFieldMiniProject_OLAP │
        ├─────────────────────────────┤                                                       ├─────────────────────────────┤
        │ • Departments               │                                                       │ • Dim_Department            │
        │ • Employees                 │                                                       │ • Dim_Project               │
        │ • Projects                  │                                                       │ • Dim_Date                  │
        │ • Assignments               │                                                       │ • Dim_Employee (SCD Type 2) │
        │ • Reviews                   │                                                       │ • Fact_PerformanceReviews   │
        └─────────────────────────────┘                                                       └─────────────────────────────┘
                       ▲                                                                                     ▲
                       │                                                                                     │
                       │           ┌──────────────────────────────────────────────────────────┐              │
                       └───────────┤                 OBJECT-ORIENTED DAL & BUSINESS LAYER     ├──────────────┘
                                   │ • core.DatabaseConnection (Thread-safe MySQL Pools)      │
                                   │ • dal.EmployeeManager (OLTP CRUD + SCD-2 Sync)           │
                                   │ • dal.ProjectManager (Projects, Assignments, Reviews)    │
                                   │ • dal.ETLManager (OLAP Incremental ETL & Health Checks)  │
                                   │ • dal.AnalyticsManager (CTE & Window Function Analytics) │
                                   │ • models.* (Domain Models & Strict Validations)          │
                                   └──────────────────────────────────────────────────────────┘
```

---

## Key Modules

### 1. Database Architecture & Schemas (`sql/`)
- **Staging Database (`GreenFieldMiniProject_STG`)**: Intermediate schema holding raw CSV chunks before relational and dimensional modeling.
- **OLTP Database (`GreenFieldMiniProject_OLTP`)**: 3rd Normal Form (3NF) relational transactional schema with foreign key constraints, cascading rules, and unique email constraints.
- **OLAP Data Warehouse (`GreenFieldMiniProject_OLAP`)**: Kimball star schema with:
  - **`Dim_Employee`**: SCD Type 2 tracking historical changes in department, job role, and salary with `start_date`, `end_date`, and `is_current` flags.
  - **`Dim_Date`**: Smart-key calendar dimension (`YYYYMMDD`).
  - **`Dim_Department` & `Dim_Project`**: SCD Type 1 dimensions with unknown member (`-1`) records.
  - **`Fact_PerformanceReviews`**: Fact table linking reviews to point-in-time employee versions and dimensional attributes.
- **ETL Stored Procedures**: Fully idempotent SQL procedures for daily incremental loads and SCD-2 version maintenance.

### 2. Data Synthesis & Bulk Ingestion (`synthesizer/`, `scripts/`)
- Scales IBM HR Employee Attrition baseline data up to 100,000+ realistic employee profiles using Faker with Indian localization (`en_IN`).
- Simulates realistic employee career lifecycles: promotions, salary hikes, department transfers, project assignments, and performance reviews.
- Generates SCD-2 history with non-overlapping date intervals and strict business rules.
- High-performance chunked bulk loading (`5,000` rows/batch) with integrity and row-count verification.

### 3. Object-Oriented Data Access Layer (DAL) (`core/`, `dal/`, `models/`)
- **Thread-safe Singleton Connection Pool** (`core/db_manager.py`): Manages dedicated, isolated MySQL connection pools for both OLTP and OLAP databases with automatic rollback transaction context managers.
- **Dual-Database Write Synchronization** (`dal/employee_manager.py`): Atomically updates the OLTP record and triggers an asynchronous/independent SCD-2 sync into OLAP.
- **Advanced Star Schema Analytics** (`dal/analytics_manager.py`): Executes advanced SQL queries directly on the star schema utilizing Common Table Expressions (CTEs), `DENSE_RANK()`, and `LAG()` window functions for YoY metrics and attrition reports.
- **Domain Models & Validation** (`models/`): Self-validating domain entities (`Employee`, `Department`, `Project`, `Assignment`, `PerformanceReview`) that enforce business invariants before queries reach the database.

---

## Directory Structure

```text
Backend/
├── core/
│   ├── db_manager.py             # Thread-safe Singleton DatabaseConnection with pooling
│   └── __init__.py
├── dal/
│   ├── analytics_manager.py      # Star-schema analytics (CTEs, Window Functions, DENSE_RANK, LAG)
│   ├── base_manager.py           # Base DAL manager with query helpers
│   ├── employee_manager.py       # OLTP CRUD & SCD-2 OLAP sync
│   ├── etl_manager.py            # Warehouse ETL orchestration & data quality checks
│   ├── project_manager.py        # Project, assignment, and review management
│   └── __init__.py
├── data/
│   ├── raw/                      # Baseline raw IBM HR dataset
│   └── synthesized/              # Synthesized output CSVs and manifest (generated)
├── exceptions/
│   ├── custom_exceptions.py      # Typed business & database exceptions
│   └── __init__.py
├── models/
│   ├── assignment.py             # Project assignment entity
│   ├── department.py             # Department entity
│   ├── employee.py               # Employee entity
│   ├── project.py                # Project entity
│   ├── review.py                 # PerformanceReview entity
│   ├── validators.py             # Data validation logic
│   └── __init__.py
├── scripts/
│   ├── bulk_loader.py            # Chunked database loader & schema creator
│   ├── sql_runner.py             # SQL script runner with DELIMITER support
│   └── warehouse_pipeline.py     # Staging-to-Warehouse migration pipeline & sanity checks
├── sql/
│   ├── Schema_Definition/
│   │   ├── ETL_Stored_Procedures.sql # Daily incremental ETL stored procedures
│   │   ├── OLAP_Schema_DDL.sql       # Star-schema warehouse DDL
│   │   └── OLTP_Schema_DDL.sql       # 3NF transactional database DDL
│   ├── staging_schema.sql            # Staging tables DDL
│   ├── staging_to_warehouse.sql      # Staging-to-OLTP/OLAP migration procedures
│   └── verify_load.sql               # Verification and audit SQL queries
├── synthesizer/
│   ├── common.py                 # Synthesis distribution helpers
│   ├── dim_date.py               # Date dimension synthesis
│   ├── employee_synthesizer.py   # Employee dataset scaling
│   ├── history_generator.py      # SCD Type 2 history simulation
│   ├── related_data.py           # Projects, assignments, and reviews synthesis
│   ├── validators.py             # In-memory synthesis data quality checks
│   └── __init__.py
├── tests/
│   ├── test_db_and_managers.py   # Unit & mock tests for DAL managers and thread-safety
│   └── test_models.py            # Unit tests for domain models & validation rules
├── .env.example                  # Environment configuration template
├── config.py                     # Central application configuration
├── requirements.txt              # Project dependencies
└── run_synthesis.py              # Synthetic data generation entrypoint
```

---

## Setup & Installation

### 1. Prerequisites
- **Python**: 3.10 or higher
- **MySQL Server**: 8.0 or higher running locally (or accessible remotely)

### 2. Virtual Environment Setup
Clone the repository and initialize a Python virtual environment:

```bash
# Navigate to the backend directory
cd Backend

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On Linux/macOS or Git Bash:
source .venv/Scripts/activate  # or source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and set your MySQL credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```ini
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=YourPasswordHere
STAGING_DB_NAME=GreenFieldMiniProject_STG
OLTP_DB_NAME=GreenFieldMiniProject_OLTP
OLAP_DB_NAME=GreenFieldMiniProject_OLAP
DB_POOL_SIZE=5
```

---

## Execution Guide

Follow these steps to run the complete pipeline from data synthesis to testing:

### Step 1: Generate Synthetic Data
Run the synthesizer to process the baseline dataset and generate the scaled CSV files:

```bash
python run_synthesis.py
```
- **Inputs**: `data/raw/WA_Fn-UseC_-HR-Employee-Attrition.csv`
- **Outputs**: Generates `dim_date.csv`, `employees.csv`, `employee_history.csv`, `projects.csv`, `project_assignments.csv`, `performance_reviews.csv`, and `manifest.json` under `data/synthesized/`.

### Step 2: Build Databases & Run Warehouse Pipeline
Execute the bulk loader:

```bash
python -m scripts.bulk_loader
```
This automated script will:
1. Re-create all three databases (`GreenFieldMiniProject_STG`, `GreenFieldMiniProject_OLTP`, `GreenFieldMiniProject_OLAP`).
2. Run all DDL and Stored Procedure scripts across all schemas.
3. Ingest CSV files into the staging tables in batches of 5,000.
4. Execute `WarehousePipeline` to:
   - Migrate staging data to OLTP tables.
   - Populate `Dim_Date` and dimensions in OLAP.
   - Backfill historical SCD-2 employee records into `Dim_Employee`.
   - Run OLAP ETL stored procedures to build `Fact_PerformanceReviews`.
   - Run 9 automated data integrity checks.

### Step 3: Run Unit & Integration Tests
Execute the pytest suite:

```bash
python -m pytest -v
```

> **Tip**: If you prefer running `pytest -v` directly without `python -m`, create a `pytest.ini` file in the root with:
> ```ini
> [pytest]
> pythonpath = .
> ```

---

## Python API Usage Examples

### 1. Database Connection & Transactions
```python
from core.db_manager import DatabaseConnection

db = DatabaseConnection()

# Query with parameterized inputs
employees = db.fetch_all(
    "SELECT employee_id, first_name, last_name FROM Employees WHERE department_id = %s",
    (1,),
    database=db.oltp_name
)

# Atomic transaction block
with db.transaction() as cur:
    cur.execute("UPDATE Employees SET is_active = 0 WHERE employee_id = %s", (10,))
    # Automatically commits on exit or rolls back on exception
```

### 2. Employee Management with SCD-2 Warehouse Sync
```python
from datetime import date
from core.db_manager import DatabaseConnection
from dal import EmployeeManager
from models import Employee

db = DatabaseConnection()
emp_mgr = EmployeeManager(db)

# Create an employee in OLTP (triggers opening an SCD-2 version in OLAP)
new_emp = Employee(
    first_name="Priya",
    last_name="Sharma",
    email="priya.sharma@example.com",
    hire_date=date(2023, 6, 1),
    department_id=2,
    job_role="Data Engineer",
    monthly_income=85000.00,
    date_of_birth=date(1996, 4, 12),
    gender="Female",
    marital_status="Single",
    distance_from_home=8,
    education=4
)
emp_id = emp_mgr.create_employee(new_emp)

# Promote employee (updates OLTP and creates a new SCD-2 version in Dim_Employee)
emp_mgr.update_employee_department(
    employee_id=emp_id,
    new_department_id=2,
    new_job_role="Senior Data Engineer"
)
```

### 3. Star Schema Analytics
```python
from core.db_manager import DatabaseConnection
from dal import AnalyticsManager

db = DatabaseConnection()
analytics = AnalyticsManager(db)

# 1. Top performers per department using DENSE_RANK()
top_performers = analytics.get_top_performers(top_n=3, year=2024)

# 2. Year-over-Year performance change using LAG()
yoy_stats = analytics.get_yoy_performance()

# 3. Departmental attrition summary
attrition = analytics.get_attrition_summary(group_by="department")
```

### 4. Running Warehouse ETL & Health Checks
```python
from core.db_manager import DatabaseConnection
from dal import ETLManager

db = DatabaseConnection()
etl = ETLManager(db)

# Run full ETL for a date range
etl.run_full_etl(start_year=2020, end_year=2026)

# Verify SCD-2 health
health = etl.run_quality_checks()
print(health)
# Output: {'overlapping_versions': 0, 'employees_without_exactly_one_current': 0, 'inverted_date_ranges': 0}
```

---

## Data Integrity & Quality Verification

Sanity and audit queries are provided in [sql/verify_load.sql](sql/verify_load.sql). You can run them in MySQL Workbench or the MySQL CLI to verify:
1. **Row counts across layers**: Consistency between staging, OLTP, and OLAP fact/dimension counts.
2. **SCD-2 Validity**:
   - Every employee has exactly one active record (`is_current = 1`).
   - Zero overlapping date intervals for version histories.
3. **Point-in-Time Fact Joins**: Verifies that every performance review joins the exact employee version valid at the time of the review date.

