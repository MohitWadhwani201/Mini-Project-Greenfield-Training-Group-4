
USE GreenFieldMiniProject_STG;

DELIMITER //

DROP PROCEDURE IF EXISTS Load_Dim_Date_From_Staging //
CREATE PROCEDURE Load_Dim_Date_From_Staging()
BEGIN
    INSERT IGNORE INTO GreenFieldMiniProject_OLAP.Dim_Date (date_id, full_date, year, month, quarter)
    SELECT date_key, full_date, calendar_year, month_number, calendar_quarter
    FROM GreenFieldMiniProject_STG.stg_dim_date
    WHERE date_key <> 99991231;
END //

DROP PROCEDURE IF EXISTS Load_OLTP_From_Staging //
CREATE PROCEDURE Load_OLTP_From_Staging()
BEGIN
    INSERT INTO GreenFieldMiniProject_OLTP.Departments (department_name)
    SELECT DISTINCT s.department
    FROM GreenFieldMiniProject_STG.stg_employees s
    WHERE NOT EXISTS (
        SELECT 1 FROM GreenFieldMiniProject_OLTP.Departments d WHERE d.department_name = s.department
    )
    ORDER BY s.department;

    INSERT INTO GreenFieldMiniProject_OLTP.Employees (
        employee_id, first_name, last_name, email, hire_date, department_id, job_role,
        monthly_income, date_of_birth, gender, marital_status, distance_from_home, education, is_active
    )
    SELECT s.employee_id, s.first_name, s.last_name, s.email, s.hire_date, d.department_id, s.job_title,
           s.monthly_income, s.date_of_birth, s.gender, s.marital_status, s.distance_from_home, s.education, s.is_active
    FROM GreenFieldMiniProject_STG.stg_employees s
    JOIN GreenFieldMiniProject_OLTP.Departments d ON d.department_name = s.department;

    INSERT INTO GreenFieldMiniProject_OLTP.Projects (project_id, project_name, start_date, end_date, budget, status)
    SELECT project_id, project_name, start_date, actual_end_date, budget, status
    FROM GreenFieldMiniProject_STG.stg_projects;

    INSERT INTO GreenFieldMiniProject_OLTP.Assignments (assignment_id, employee_id, project_id, role_on_project, assignment_date)
    SELECT assignment_id, employee_id, project_id, role_on_project, assigned_date
    FROM GreenFieldMiniProject_STG.stg_project_assignments;

    INSERT INTO GreenFieldMiniProject_OLTP.Reviews (
        review_id, employee_id, review_date, performance_rating, job_satisfaction, environment_satisfaction, work_life_balance
    )
    SELECT review_id, employee_id, review_date, performance_rating, job_satisfaction, environment_satisfaction, work_life_balance
    FROM GreenFieldMiniProject_STG.stg_performance_reviews;
END //

DROP PROCEDURE IF EXISTS Backfill_Dim_Employee_History //
CREATE PROCEDURE Backfill_Dim_Employee_History()
BEGIN
    INSERT INTO GreenFieldMiniProject_OLAP.Dim_Employee (
        employee_id, first_name, last_name, job_role, monthly_income, age, gender, start_date, end_date, is_current
    )
    WITH versions AS (
        SELECT h.*, MAX(h.version_no) OVER (PARTITION BY h.employee_id) AS last_version
        FROM GreenFieldMiniProject_STG.stg_employee_history h
    )
    SELECT
        v.employee_id, e.first_name, e.last_name, v.job_title, v.monthly_income,
        TIMESTAMPDIFF(YEAR, e.date_of_birth, v.start_date),      -- age at the start of this version
        e.gender, v.start_date,
        CASE WHEN v.version_no = v.last_version THEN NULL ELSE v.end_date END,
        CASE WHEN v.version_no = v.last_version THEN TRUE ELSE FALSE END
    FROM versions v
    JOIN GreenFieldMiniProject_STG.stg_employees e ON e.employee_id = v.employee_id
    ORDER BY v.employee_id, v.version_no;
END //

DELIMITER ;
