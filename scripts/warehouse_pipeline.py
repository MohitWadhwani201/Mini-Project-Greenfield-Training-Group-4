# Moves staged data into the OLTP and OLAP tables, runs ETL procedures and verifies the result.
import logging
import time

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

import config

log = logging.getLogger("warehouse_pipeline")


class WarehousePipeline:
    
    def __init__(self, engine):
        self.engine = engine
        self.s, self.t, self.a = config.STAGING_DB, config.OLTP_DB, config.OLAP_DB

    def _call(self, conn, procedure):
        # Calls one stored procedure and logs how long it took.
        start_time = time.time()
        conn.exec_driver_sql(f"CALL {procedure}()")
        log.info("CALL %-52s %5.1fs", procedure, time.time() - start_time)

    def _scalar(self, conn, sql):
        # Runs a query that returns one number.
        return conn.execute(text(sql)).scalar()

    def run(self, staging_counts):
        from scripts.bulk_loader import LoadError
        try:
            with self.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                self._call(conn, f"{self.s}.Load_Dim_Date_From_Staging")
                self._call(conn, f"{self.s}.Load_OLTP_From_Staging")
                self._call(conn, f"{self.s}.Backfill_Dim_Employee_History")
                self._call(conn, f"{self.a}.ETL_Load_Simple_Dimensions")
                versions_before = self._scalar(conn, f"SELECT COUNT(*) FROM {self.a}.Dim_Employee")
                self._call(conn, f"{self.a}.ETL_Dim_Employee_SCD2")
                self._call(conn, f"{self.a}.ETL_Fact_PerformanceReviews")
                results = self._checks(conn, staging_counts, versions_before)
        except SQLAlchemyError as exc:
            raise LoadError(f"Warehouse load failed: {exc}") from exc
        failed = [r for r in results if not r[1]]
        if failed:
            raise LoadError(f"{len(failed)} warehouse check(s) failed: {[r[0] for r in failed]}")
        log.info("Warehouse load complete - all %d checks passed", len(results))

    def _checks(self, conn, counts, versions_before):
        # Compares OLTP/OLAP against staging and checks SCD-2 integrity; returns (name, passed, detail) tuples.
        q = lambda sql: self._scalar(conn, sql)
        checks = [
            ("OLTP Employees == staging", q(f"SELECT COUNT(*) FROM {self.t}.Employees") == counts["employees"]),
            ("OLTP Projects == staging", q(f"SELECT COUNT(*) FROM {self.t}.Projects") == counts["projects"]),
            ("OLTP Assignments == staging", q(f"SELECT COUNT(*) FROM {self.t}.Assignments") == counts["assignments"]),
            ("OLTP Reviews == staging", q(f"SELECT COUNT(*) FROM {self.t}.Reviews") == counts["reviews"]),
            ("Dim_Employee versions == staging history",
             versions_before == counts["history"]),
            ("SCD2 ETL added no extra versions after backfill",
             q(f"SELECT COUNT(*) FROM {self.a}.Dim_Employee") == versions_before),
            ("exactly one is_current row per employee",
             q(f"SELECT COUNT(*) FROM (SELECT employee_id FROM {self.a}.Dim_Employee "
               f"GROUP BY employee_id HAVING SUM(is_current) <> 1) x") == 0),
            ("Fact rows == reviews", q(f"SELECT COUNT(*) FROM {self.a}.Fact_PerformanceReviews") == counts["reviews"]),
            ("every fact joins the employee version valid on its review date",
             q(f"SELECT COUNT(*) FROM {self.a}.Fact_PerformanceReviews f "
               f"JOIN {self.t}.Reviews r ON r.review_id = f.review_id "
               f"JOIN {self.a}.Dim_Employee de ON de.employee_sk = f.employee_sk "
               f"WHERE r.review_date NOT BETWEEN de.start_date AND COALESCE(de.end_date, '9999-12-31')") == 0),
        ]
        for name, passed in checks:
            (log.info if passed else log.error)("%s  %s", "PASS" if passed else "FAIL", name)
        return [(name, passed, "") for name, passed in checks]
