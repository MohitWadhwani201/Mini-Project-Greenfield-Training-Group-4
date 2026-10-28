"""Read-only OLAP access. View names are the CONTRACT with Person 1 (sql/ folder)."""
from typing import Optional

from .base_manager import BaseManager


class AnalyticsManager(BaseManager):
    def get_top_performers(self, department: Optional[str] = None, top_n: int = 5) -> list[dict]:
        """From vw_top_performers_by_department (DENSE_RANK column: dept_rank)."""
        sql, params = "SELECT * FROM vw_top_performers_by_department WHERE dept_rank<=%s", [top_n]
        if department:
            sql += " AND department_name=%s"; params.append(department)
        return self._fetch_all(sql, params, olap=True)

    def get_yoy_performance(self) -> list[dict]:
        return self._fetch_all("SELECT * FROM vw_yoy_performance ORDER BY review_year", olap=True)

    def get_attrition_trends(self) -> list[dict]:
        return self._fetch_all("SELECT * FROM vw_attrition_trends ORDER BY year_num", olap=True)

    def get_project_bottlenecks(self) -> list[dict]:
        return self._fetch_all("SELECT * FROM vw_project_bottlenecks", olap=True)

    def get_employee_history(self, employee_id: int) -> list[dict]:
        """SCD-2 timeline for the Time-Travel inspector."""
        return self._fetch_all(
            "SELECT employee_sk, employee_id, department_name, job_title, salary, "
            "start_date, end_date, is_current FROM dim_employee "
            "WHERE employee_id=%s ORDER BY start_date", (employee_id,), olap=True)
