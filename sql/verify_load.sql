
SELECT 'STG employees' AS layer, COUNT(*) AS n FROM GreenFieldMiniProject_STG.stg_employees
UNION ALL SELECT 'OLTP Employees', COUNT(*) FROM GreenFieldMiniProject_OLTP.Employees
UNION ALL SELECT 'OLAP Dim_Employee (versions)', COUNT(*) FROM GreenFieldMiniProject_OLAP.Dim_Employee
UNION ALL SELECT 'OLAP Fact_PerformanceReviews', COUNT(*) FROM GreenFieldMiniProject_OLAP.Fact_PerformanceReviews;

SELECT employee_id FROM GreenFieldMiniProject_OLAP.Dim_Employee
GROUP BY employee_id HAVING SUM(is_current) <> 1;

SELECT a.employee_id, a.employee_sk, b.employee_sk AS next_sk
FROM GreenFieldMiniProject_OLAP.Dim_Employee a
JOIN GreenFieldMiniProject_OLAP.Dim_Employee b
  ON a.employee_id = b.employee_id AND b.start_date > a.start_date
 AND b.start_date <= COALESCE(a.end_date, '9999-12-31');   -- overlapping versions

SELECT employee_id, job_role, monthly_income, start_date, end_date, is_current
FROM GreenFieldMiniProject_OLAP.Dim_Employee
WHERE employee_id = (SELECT employee_id FROM GreenFieldMiniProject_OLAP.Dim_Employee
                     GROUP BY employee_id HAVING COUNT(*) = 3 ORDER BY employee_id LIMIT 1)
ORDER BY start_date;

SELECT r.review_date, de.job_role AS role_at_review, de.monthly_income AS salary_at_review, f.performance_rating
FROM GreenFieldMiniProject_OLAP.Fact_PerformanceReviews f
JOIN GreenFieldMiniProject_OLTP.Reviews r ON r.review_id = f.review_id
JOIN GreenFieldMiniProject_OLAP.Dim_Employee de ON de.employee_sk = f.employee_sk
WHERE de.employee_id = 3
ORDER BY r.review_date;

WITH avg_rating AS (
    SELECT dd.department_name, de.employee_id, de.first_name, de.last_name,
           ROUND(AVG(f.performance_rating), 2) AS avg_rating, COUNT(*) AS reviews
    FROM GreenFieldMiniProject_OLAP.Fact_PerformanceReviews f
    JOIN GreenFieldMiniProject_OLAP.Dim_Employee de ON de.employee_sk = f.employee_sk
    JOIN GreenFieldMiniProject_OLAP.Dim_Department dd ON dd.department_sk = f.department_sk
    GROUP BY dd.department_name, de.employee_id, de.first_name, de.last_name
    HAVING COUNT(*) >= 4
),
ranked AS (
    SELECT *, DENSE_RANK() OVER (PARTITION BY department_name ORDER BY avg_rating DESC) AS rnk
    FROM avg_rating
)
SELECT * FROM ranked WHERE rnk <= 3 ORDER BY department_name, rnk, employee_id LIMIT 30;

SELECT d.year, ROUND(AVG(f.performance_rating), 2) AS avg_rating, COUNT(*) AS reviews
FROM GreenFieldMiniProject_OLAP.Fact_PerformanceReviews f
JOIN GreenFieldMiniProject_OLAP.Dim_Date d ON d.date_id = f.date_id
GROUP BY d.year ORDER BY d.year;
