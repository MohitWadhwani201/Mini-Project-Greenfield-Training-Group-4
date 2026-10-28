"""Read-only analytics. Queries run directly on the star schema (CTEs + window functions),
so no extra views are required from the SQL side."""
from typing import Optional

from exceptions import ValidationError
from .base_manager import BaseManager


class AnalyticsManager(BaseManager):

    def get_top_performers(self, department: Optional[str] = None, top_n: int = 5,
                           year: Optional[int] = None) -> list[dict]:
        """Top employees per department by average performance_rating (DENSE_RANK)."""
        where, params = "WHERE dd.department_sk <> -1", []
        if year:
            where += " AND dt.year=%s"; params.append(year)
        outer, oparams = "WHERE dept_rank <= %s", [top_n]
        if department:
            outer += " AND department_name=%s"; oparams.append(department)
        sql = f"""
            WITH emp_scores AS (
                SELECT de.employee_id, de.first_name, de.last_name, dd.department_name,
                       ROUND(AVG(f.performance_rating), 2) AS avg_rating,
                       COUNT(*) AS review_count
                FROM Fact_PerformanceReviews f
                JOIN Dim_Employee   de ON f.employee_sk   = de.employee_sk
                JOIN Dim_Department dd ON f.department_sk = dd.department_sk
                JOIN Dim_Date       dt ON f.date_id       = dt.date_id
                {where}
                GROUP BY de.employee_id, de.first_name, de.last_name, dd.department_name
            ), ranked AS (
                SELECT *, DENSE_RANK() OVER (PARTITION BY department_name
                                             ORDER BY avg_rating DESC) AS dept_rank
                FROM emp_scores
            )
            SELECT * FROM ranked {outer} ORDER BY department_name, dept_rank, employee_id"""
        return self._fetch_all(sql, params + oparams, olap=True)

    def get_yoy_performance(self) -> list[dict]:
        """Yearly averages plus year-over-year change via LAG()."""
        return self._fetch_all("""
            WITH yearly AS (
                SELECT dt.year AS review_year,
                       COUNT(*) AS review_count,
                       ROUND(AVG(f.performance_rating), 3)       AS avg_performance,
                       ROUND(AVG(f.job_satisfaction), 3)         AS avg_job_satisfaction,
                       ROUND(AVG(f.environment_satisfaction), 3) AS avg_environment_satisfaction,
                       ROUND(AVG(f.work_life_balance), 3)        AS avg_work_life_balance
                FROM Fact_PerformanceReviews f
                JOIN Dim_Date dt ON f.date_id = dt.date_id
                GROUP BY dt.year
            )
            SELECT *, ROUND(avg_performance - LAG(avg_performance) OVER (ORDER BY review_year), 3)
                      AS yoy_change
            FROM yearly ORDER BY review_year""", olap=True)

    def get_attrition_summary(self, group_by: str = "department") -> list[dict]:
        """Attrition from OLTP is_active (a snapshot: the schema has no termination date,
        so a time trend is not possible)."""
        cols = {"department": "COALESCE(d.department_name, 'Unassigned')",
                "job_role": "e.job_role"}
        if group_by not in cols:
            raise ValidationError(f"group_by must be one of {list(cols)}")
        g = cols[group_by]
        return self._fetch_all(f"""
            SELECT {g} AS grp, COUNT(*) AS headcount,
                   SUM(e.is_active = 0) AS attrited,
                   ROUND(100 * SUM(e.is_active = 0) / COUNT(*), 2) AS attrition_rate_pct,
                   ROUND(AVG(e.monthly_income), 2) AS avg_monthly_income
            FROM Employees e LEFT JOIN Departments d ON e.department_id = d.department_id
            GROUP BY {g} ORDER BY attrition_rate_pct DESC""")

    def get_project_bottlenecks(self) -> list[dict]:
        """Projects ranked by worst average work-life balance (rank 1 = highest risk)."""
        return self._fetch_all("""
            WITH proj AS (
                SELECT dp.project_id, dp.project_name, dp.status,
                       COUNT(*) AS review_count,
                       COUNT(DISTINCT de.employee_id) AS employees_reviewed,
                       ROUND(AVG(f.performance_rating), 2) AS avg_performance,
                       ROUND(AVG(f.job_satisfaction), 2)   AS avg_job_satisfaction,
                       ROUND(AVG(f.work_life_balance), 2)  AS avg_work_life_balance
                FROM Fact_PerformanceReviews f
                JOIN Dim_Project  dp ON f.project_sk  = dp.project_sk
                JOIN Dim_Employee de ON f.employee_sk = de.employee_sk
                WHERE dp.project_sk <> -1
                GROUP BY dp.project_id, dp.project_name, dp.status
            )
            SELECT *, DENSE_RANK() OVER (ORDER BY avg_work_life_balance ASC,
                                                  avg_job_satisfaction ASC) AS risk_rank
            FROM proj ORDER BY risk_rank""", olap=True)

    def get_employee_history(self, employee_id: int) -> list[dict]:
        """SCD-2 timeline for the Time-Travel inspector, with income change via LAG()."""
        return self._fetch_all("""
            SELECT employee_sk, employee_id, first_name, last_name, job_role, monthly_income,
                   age, gender, start_date, end_date, is_current,
                   monthly_income - LAG(monthly_income) OVER (
                       PARTITION BY employee_id ORDER BY start_date) AS income_change
            FROM Dim_Employee WHERE employee_id=%s ORDER BY start_date""",
            (employee_id,), olap=True)