from datetime import date
from typing import Optional

from exceptions import DatabaseOperationError
from .base_manager import BaseManager


class ETLManager(BaseManager):
    """Runs the warehouse ETL procedures in the documented order and checks data quality."""

    def run_full_etl(self, start_year: int = 2015, end_year: Optional[int] = None) -> None:
        end_year = end_year or date.today().year + 2
        steps = [("Populate_Dim_Date", (start_year, end_year)),
                 ("ETL_Load_Simple_Dimensions", ()),
                 ("ETL_Dim_Employee_SCD2", ()),
                 ("ETL_Fact_PerformanceReviews", ())]
        for name, args in steps:
            try:
                self._db.call_procedure(name, args, self.olap)
            except DatabaseOperationError as exc:
                raise DatabaseOperationError(f"ETL step {name} failed: {exc}") from exc

    def run_quality_checks(self) -> dict:
        """Returns counts of violations; all zeros means healthy."""
        overlaps = self._fetch_one("""
            SELECT COUNT(*) AS n FROM Dim_Employee a JOIN Dim_Employee b
              ON a.employee_id = b.employee_id AND a.employee_sk < b.employee_sk
             AND a.start_date <= COALESCE(b.end_date, '9999-12-31')
             AND b.start_date <= COALESCE(a.end_date, '9999-12-31')""", olap=True)
        multi = self._fetch_one("""
            SELECT COUNT(*) AS n FROM (SELECT employee_id FROM Dim_Employee
              GROUP BY employee_id HAVING SUM(is_current) <> 1) t""", olap=True)
        inverted = self._fetch_one(
            "SELECT COUNT(*) AS n FROM Dim_Employee WHERE end_date < start_date", olap=True)
        return {"overlapping_versions": overlaps["n"],
                "employees_without_exactly_one_current": multi["n"],
                "inverted_date_ranges": inverted["n"]}