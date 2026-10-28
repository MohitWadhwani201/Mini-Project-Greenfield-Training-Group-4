CREATE DATABASE IF NOT EXISTS GreenFieldMiniProject_OLAP;
USE GreenFieldMiniProject_OLAP;

-- 1. Dim_Department (surrogate key department_sk, business key department_id)
CREATE TABLE IF NOT EXISTS Dim_Department (
    department_sk INT AUTO_INCREMENT PRIMARY KEY,
    department_id INT NOT NULL,
    department_name VARCHAR(100),
    UNIQUE KEY uq_dim_department_id (department_id)
);

-- 2. Dim_Project (surrogate key project_sk, business key project_id)
CREATE TABLE IF NOT EXISTS Dim_Project (
    project_sk INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    project_name VARCHAR(100),
    status VARCHAR(50),
    UNIQUE KEY uq_dim_project_id (project_id)
);

-- 3. Dim_Date (smart key date_id = YYYYMMDD)
CREATE TABLE IF NOT EXISTS Dim_Date (
    date_id INT PRIMARY KEY,
    full_date DATE NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    quarter INT NOT NULL
);

-- 4. Employee Dimension Table
-- This table tracks an employee's history over time. Whenever an employee's details change, 
-- we create a new row instead of overwriting the old data.
-- The start and end dates show exactly when a specific version of their profile was active. 
-- The most recent, active version of an employee will have a blank end date and is marked as "current". 
-- The "age" column represents how old the employee was when that specific version of their profile started.
CREATE TABLE IF NOT EXISTS Dim_Employee (
    employee_sk INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    job_role VARCHAR(100),
    monthly_income DECIMAL(10,2),
    age INT,
    gender VARCHAR(20),
    start_date DATE NOT NULL,
    end_date DATE,
    is_current BOOLEAN DEFAULT TRUE,
    KEY idx_dim_emp_current (employee_id, is_current),
    KEY idx_dim_emp_validity (employee_id, start_date, end_date)
);

-- 5. Fact_PerformanceReviews
-- The review_id column stores the original review ID from the source database. 
-- It is marked as UNIQUE to ensure that if the data loading process runs more than once, 
-- it won't accidentally create duplicate review records in this table.
CREATE TABLE IF NOT EXISTS Fact_PerformanceReviews (
    review_sk INT AUTO_INCREMENT PRIMARY KEY,
    review_id INT NOT NULL,
    employee_sk INT NOT NULL,
    department_sk INT NOT NULL,
    project_sk INT NOT NULL,
    date_id INT NOT NULL,
    performance_rating INT,
    job_satisfaction INT,
    environment_satisfaction INT,
    work_life_balance INT,
    UNIQUE KEY uq_fact_review_id (review_id),
    FOREIGN KEY (employee_sk) REFERENCES Dim_Employee(employee_sk),
    FOREIGN KEY (department_sk) REFERENCES Dim_Department(department_sk),
    FOREIGN KEY (project_sk) REFERENCES Dim_Project(project_sk),
    FOREIGN KEY (date_id) REFERENCES Dim_Date(date_id)
);

-- Unknown members (key -1) so facts without a department / project are kept instead of dropped
INSERT INTO Dim_Department (department_sk, department_id, department_name)
VALUES (-1, 0, 'Unknown / Unassigned')
ON DUPLICATE KEY UPDATE department_name = 'Unknown / Unassigned';

INSERT INTO Dim_Project (project_sk, project_id, project_name, status)
VALUES (-1, 0, 'Unassigned / General HR', 'N/A')
ON DUPLICATE KEY UPDATE project_name = 'Unassigned / General HR';
