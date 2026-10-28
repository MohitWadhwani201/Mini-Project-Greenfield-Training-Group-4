USE GreenFieldMiniProject_OLAP;

-- Run order: Populate_Dim_Date -> ETL_Load_Simple_Dimensions -> ETL_Dim_Employee_SCD2 -> ETL_Fact_PerformanceReviews
-- Run the whole ETL once per day (SCD2 closes versions at "yesterday" and opens new ones "today").

DELIMITER //

-- 0. Helper: Pre-populate Dim_Date for a Given Year Range
DROP PROCEDURE IF EXISTS Populate_Dim_Date //
CREATE PROCEDURE Populate_Dim_Date(IN start_year INT, IN end_year INT)
BEGIN
    DECLARE cur_date DATE;
    DECLARE stop_date DATE;

    SET cur_date = STR_TO_DATE(CONCAT(start_year, '-01-01'), '%Y-%m-%d');
    SET stop_date = STR_TO_DATE(CONCAT(end_year, '-12-31'), '%Y-%m-%d');

    WHILE cur_date <= stop_date DO
        INSERT IGNORE INTO GreenFieldMiniProject_OLAP.Dim_Date (date_id, full_date, year, month, quarter)
        VALUES (
            CAST(DATE_FORMAT(cur_date, '%Y%m%d') AS UNSIGNED),
            cur_date,
            YEAR(cur_date),
            MONTH(cur_date),
            QUARTER(cur_date)
        );
        SET cur_date = DATE_ADD(cur_date, INTERVAL 1 DAY);
    END WHILE;
END //

-- 1. ETL: Load Simple Dimensions (Departments & Projects) - SCD Type 1 (overwrite, no history)
DROP PROCEDURE IF EXISTS ETL_Load_Simple_Dimensions //
CREATE PROCEDURE ETL_Load_Simple_Dimensions()
BEGIN
    -- Refresh names/status that changed in OLTP
    UPDATE GreenFieldMiniProject_OLAP.Dim_Department dd
    JOIN GreenFieldMiniProject_OLTP.Departments d ON dd.department_id = d.department_id
    SET dd.department_name = d.department_name
    WHERE NOT (dd.department_name <=> d.department_name);

    UPDATE GreenFieldMiniProject_OLAP.Dim_Project dp
    JOIN GreenFieldMiniProject_OLTP.Projects p ON dp.project_id = p.project_id
    SET dp.project_name = p.project_name, dp.status = p.status
    WHERE NOT (dp.project_name <=> p.project_name) OR NOT (dp.status <=> p.status);

    -- Insert new departments from OLTP into OLAP
    INSERT INTO GreenFieldMiniProject_OLAP.Dim_Department (department_id, department_name)
    SELECT d.department_id, d.department_name
    FROM GreenFieldMiniProject_OLTP.Departments d
    WHERE NOT EXISTS (
        SELECT 1 FROM GreenFieldMiniProject_OLAP.Dim_Department dd WHERE dd.department_id = d.department_id
    );

    -- Insert new projects from OLTP into OLAP
    INSERT INTO GreenFieldMiniProject_OLAP.Dim_Project (project_id, project_name, status)
    SELECT p.project_id, p.project_name, p.status
    FROM GreenFieldMiniProject_OLTP.Projects p
    WHERE NOT EXISTS (
        SELECT 1 FROM GreenFieldMiniProject_OLAP.Dim_Project dp WHERE dp.project_id = p.project_id
    );
END //

-- 2. ETL: Load Dim_Employee (SCD Type 2 Implementation)
DROP PROCEDURE IF EXISTS ETL_Dim_Employee_SCD2 //
CREATE PROCEDURE ETL_Dim_Employee_SCD2()
BEGIN
    START TRANSACTION;

    -- STEP A: Close the current version if role or salary changed.
    -- "<=>" is a NULL-safe comparison, so NULL -> value changes are detected too.
    -- end_date = yesterday, so the new version (starting today) never overlaps it.
    UPDATE GreenFieldMiniProject_OLAP.Dim_Employee de
    JOIN GreenFieldMiniProject_OLTP.Employees e ON de.employee_id = e.employee_id
    SET
        de.end_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY),
        de.is_current = FALSE
    WHERE de.is_current = TRUE
      AND (NOT (de.job_role <=> e.job_role) OR NOT (de.monthly_income <=> e.monthly_income));

    -- STEP B: Insert a new current version for new hires and for employees closed in step A.
    -- An employee's very first version starts on hire_date (so old reviews can be matched);
    -- later versions start today.
    INSERT INTO GreenFieldMiniProject_OLAP.Dim_Employee (
        employee_id, first_name, last_name, job_role, monthly_income, age, gender, start_date, end_date, is_current
    )
    SELECT
        e.employee_id, e.first_name, e.last_name, e.job_role, e.monthly_income,
        TIMESTAMPDIFF(YEAR, e.date_of_birth, CURRENT_DATE()),
        e.gender,
        CASE
            WHEN EXISTS (SELECT 1 FROM GreenFieldMiniProject_OLAP.Dim_Employee x WHERE x.employee_id = e.employee_id)
                THEN CURRENT_DATE()
            ELSE e.hire_date
        END,
        NULL, TRUE
    FROM GreenFieldMiniProject_OLTP.Employees e
    LEFT JOIN GreenFieldMiniProject_OLAP.Dim_Employee de
        ON e.employee_id = de.employee_id AND de.is_current = TRUE
    WHERE de.employee_sk IS NULL;

    COMMIT;
END //

-- 3. ETL: Load Fact_PerformanceReviews (CTEs & Window Functions)
DROP PROCEDURE IF EXISTS ETL_Fact_PerformanceReviews //
CREATE PROCEDURE ETL_Fact_PerformanceReviews()
BEGIN
    INSERT INTO GreenFieldMiniProject_OLAP.Fact_PerformanceReviews (
        review_id, employee_sk, department_sk, project_sk, date_id,
        performance_rating, job_satisfaction, environment_satisfaction, work_life_balance
    )
    WITH ReviewWithProject AS (
        -- Attach the project the employee was most recently assigned to ON OR BEFORE the review date
        SELECT
            r.review_id, r.employee_id, r.review_date,
            r.performance_rating, r.job_satisfaction, r.environment_satisfaction, r.work_life_balance,
            e.department_id,
            a.project_id,
            ROW_NUMBER() OVER (
                PARTITION BY r.review_id
                ORDER BY a.assignment_date DESC, a.assignment_id DESC
            ) AS rn_project
        FROM GreenFieldMiniProject_OLTP.Reviews r
        JOIN GreenFieldMiniProject_OLTP.Employees e ON r.employee_id = e.employee_id
        LEFT JOIN GreenFieldMiniProject_OLTP.Assignments a
            ON a.employee_id = r.employee_id AND a.assignment_date <= r.review_date
    ),
    CleanedReviews AS (
        -- Deduplicate: keep the latest review when an employee has two reviews on the same date
        SELECT
            rp.*,
            ROW_NUMBER() OVER (
                PARTITION BY rp.employee_id, rp.review_date
                ORDER BY rp.review_id DESC
            ) AS rn_dup
        FROM ReviewWithProject rp
        WHERE rp.rn_project = 1
    )
    SELECT
        cr.review_id,
        de.employee_sk,
        COALESCE(dd.department_sk, -1) AS department_sk,
        COALESCE(dp.project_sk, -1) AS project_sk,
        CAST(DATE_FORMAT(cr.review_date, '%Y%m%d') AS UNSIGNED) AS date_id,
        cr.performance_rating,
        cr.job_satisfaction,
        cr.environment_satisfaction,
        cr.work_life_balance
    FROM CleanedReviews cr
    -- Point-in-time join: the employee version that was valid ON the review date
    JOIN GreenFieldMiniProject_OLAP.Dim_Employee de
        ON cr.employee_id = de.employee_id
       AND cr.review_date BETWEEN de.start_date AND COALESCE(de.end_date, '9999-12-31')
    LEFT JOIN GreenFieldMiniProject_OLAP.Dim_Department dd ON cr.department_id = dd.department_id
    LEFT JOIN GreenFieldMiniProject_OLAP.Dim_Project dp ON cr.project_id = dp.project_id
    WHERE cr.rn_dup = 1
      AND NOT EXISTS (   -- makes the load re-runnable: already loaded reviews are skipped
          SELECT 1 FROM GreenFieldMiniProject_OLAP.Fact_PerformanceReviews f WHERE f.review_id = cr.review_id
      );
END //

DELIMITER ;
