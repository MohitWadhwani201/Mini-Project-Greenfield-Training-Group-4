
CREATE DATABASE IF NOT EXISTS GreenFieldMiniProject_STG;  -- server default collation, same as the Part 1 databases
USE GreenFieldMiniProject_STG;

DROP TABLE IF EXISTS stg_performance_reviews;
DROP TABLE IF EXISTS stg_project_assignments;
DROP TABLE IF EXISTS stg_projects;
DROP TABLE IF EXISTS stg_employee_history;
DROP TABLE IF EXISTS stg_employees;
DROP TABLE IF EXISTS stg_dim_date;

CREATE TABLE stg_dim_date (
    date_key         INT          NOT NULL PRIMARY KEY,   -- YYYYMMDD (99991231 = open-ended row, not copied to Dim_Date)
    full_date        DATE         NOT NULL,
    day_of_month     TINYINT      NOT NULL,
    day_of_week      TINYINT      NOT NULL,               -- 1 = Monday
    day_name         VARCHAR(10)  NOT NULL,
    week_of_year     TINYINT      NOT NULL,
    month_number     TINYINT      NOT NULL,
    month_name       VARCHAR(10)  NOT NULL,
    calendar_quarter TINYINT      NOT NULL,
    calendar_year    SMALLINT     NOT NULL,
    is_weekend       TINYINT(1)   NOT NULL,
    is_month_end     TINYINT(1)   NOT NULL,
    fiscal_year      SMALLINT     NOT NULL,               -- April-March
    fiscal_quarter   TINYINT      NOT NULL,
    UNIQUE KEY uq_full_date (full_date)
);

CREATE TABLE stg_employees (
    employee_id                INT          NOT NULL PRIMARY KEY,
    source                     VARCHAR(15)  NOT NULL,     -- IBM_ORIGINAL | SYNTHETIC
    first_name                 VARCHAR(50)  NOT NULL,
    last_name                  VARCHAR(50)  NOT NULL,
    full_name                  VARCHAR(101) NOT NULL,
    gender                     VARCHAR(10)  NOT NULL,
    email                      VARCHAR(120) NOT NULL,
    date_of_birth              DATE         NOT NULL,
    age                        TINYINT UNSIGNED NOT NULL,
    marital_status             VARCHAR(15)  NOT NULL,
    education                  TINYINT      NOT NULL,     -- 1..5 (IBM scale)
    education_field            VARCHAR(30)  NOT NULL,
    city                       VARCHAR(60)  NOT NULL,
    department                 VARCHAR(50)  NOT NULL,
    job_role                   VARCHAR(50)  NOT NULL,
    job_title                  VARCHAR(70)  NOT NULL,     -- becomes OLTP Employees.job_role (it changes on promotion)
    job_level                  TINYINT      NOT NULL,
    monthly_income             INT          NOT NULL,
    daily_rate                 INT          NOT NULL,
    hourly_rate                INT          NOT NULL,
    monthly_rate               INT          NOT NULL,
    percent_salary_hike        TINYINT      NOT NULL,
    performance_rating         TINYINT      NOT NULL,
    business_travel            VARCHAR(25)  NOT NULL,
    over_time                  VARCHAR(3)   NOT NULL,
    distance_from_home         SMALLINT     NOT NULL,
    num_companies_worked       TINYINT      NOT NULL,
    total_working_years        TINYINT      NOT NULL,
    training_times_last_year   TINYINT      NOT NULL,
    years_at_company           TINYINT      NOT NULL,
    years_in_current_role      TINYINT      NOT NULL,
    years_since_last_promotion TINYINT      NOT NULL,
    years_with_curr_manager    TINYINT      NOT NULL,
    stock_option_level         TINYINT      NOT NULL,
    job_involvement            TINYINT      NOT NULL,
    job_satisfaction           TINYINT      NOT NULL,
    environment_satisfaction   TINYINT      NOT NULL,
    relationship_satisfaction  TINYINT      NOT NULL,
    work_life_balance          TINYINT      NOT NULL,
    attrition                  VARCHAR(3)   NOT NULL,
    hire_date                  DATE         NOT NULL,
    termination_date           DATE         NULL,
    is_active                  TINYINT(1)   NOT NULL,
    KEY idx_emp_department (department),
    KEY idx_emp_active (is_active)
);

-- SCD Type 2 source rows: one row per employee VERSION (inclusive dates, open version end_date = '9999-12-31').
CREATE TABLE stg_employee_history (
    history_id     INT         NOT NULL PRIMARY KEY,
    employee_id    INT         NOT NULL,
    version_no     TINYINT     NOT NULL,
    department     VARCHAR(50) NOT NULL,
    job_role       VARCHAR(50) NOT NULL,
    job_title      VARCHAR(70) NOT NULL,
    job_level      TINYINT     NOT NULL,
    monthly_income INT         NOT NULL,
    start_date     DATE        NOT NULL,
    end_date       DATE        NOT NULL,
    is_current     TINYINT(1)  NOT NULL,
    change_type    VARCHAR(20) NOT NULL,                  -- HIRE | SALARY_HIKE | PROMOTION | DEPT_TRANSFER
    KEY idx_hist_emp_start (employee_id, start_date)
);

CREATE TABLE stg_projects (
    project_id        INT          NOT NULL PRIMARY KEY,
    project_code      VARCHAR(12)  NOT NULL,
    project_name      VARCHAR(80)  NOT NULL,
    owning_department VARCHAR(50)  NOT NULL,
    start_date        DATE         NOT NULL,
    planned_end_date  DATE         NOT NULL,
    actual_end_date   DATE         NULL,
    status            VARCHAR(15)  NOT NULL,
    budget            INT          NOT NULL
);

CREATE TABLE stg_project_assignments (
    assignment_id   INT         NOT NULL PRIMARY KEY,
    employee_id     INT         NOT NULL,
    project_id      INT         NOT NULL,
    role_on_project VARCHAR(30) NOT NULL,
    allocation_pct  TINYINT     NOT NULL,
    assigned_date   DATE        NOT NULL,
    KEY idx_asg_emp (employee_id),
    KEY idx_asg_proj (project_id)
);

CREATE TABLE stg_performance_reviews (
    review_id                INT      NOT NULL PRIMARY KEY,
    employee_id              INT      NOT NULL,
    review_date              DATE     NOT NULL,
    performance_rating       TINYINT  NOT NULL,           -- 1-4 (IBM scale)
    job_satisfaction         TINYINT  NOT NULL,
    environment_satisfaction TINYINT  NOT NULL,
    work_life_balance        TINYINT  NOT NULL,
    KEY idx_rev_emp_date (employee_id, review_date)
);
