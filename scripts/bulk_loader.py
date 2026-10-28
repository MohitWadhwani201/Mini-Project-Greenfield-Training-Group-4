#builds the databases and bulk-loads the synthesized CSV files into the staging tables in chunks.
import logging
import sys
import time
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError

import config
from scripts.sql_runner import run_sql_file

log = logging.getLogger("bulk_loader")

LOAD_ORDER = ["dim_date", "employees", "history", "projects", "assignments", "reviews"]


class LoadError(RuntimeError):
   
    pass


class BulkLoader:
  
    def __init__(self, db=None, chunk_size=5000, table_map=None, column_renames=None):
        self.db = db or config.DB_CONFIG
        self.chunk_size = chunk_size
        self.table_map = table_map or config.TABLE_MAP
        self.column_renames = config.COLUMN_RENAMES if column_renames is None else column_renames
        self._engine = None

    @property
    def engine(self):
        if self._engine is None:
            url = URL.create("mysql+pymysql", username=self.db["user"], password=self.db["password"],
                             host=self.db["host"], port=self.db["port"])
            self._engine = create_engine(url, pool_pre_ping=True)
        return self._engine

    def check_connection(self):
        # Fails early with a clear message if MySQL is unreachable or the login is wrong.
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            raise LoadError(f"Cannot connect to MySQL at {self.db['host']}:{self.db['port']} "
                            f"as {self.db['user']!r}: {exc}") from exc

    def create_schema(self):
        try:
            with self.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                for name in (config.STAGING_DB, config.OLTP_DB, config.OLAP_DB):
                    conn.exec_driver_sql(f"DROP DATABASE IF EXISTS `{name}`")
                for script in config.SCHEMA_SCRIPTS:
                    count = run_sql_file(conn, script)
                    log.info("Ran %-28s (%d statements)", Path(script).name, count)
        except (SQLAlchemyError, FileNotFoundError) as exc:
            raise LoadError(f"Schema creation failed: {exc}") from exc

    def truncate_all(self):
        s, t, a = config.STAGING_DB, config.OLTP_DB, config.OLAP_DB
        try:
            with self.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                conn.exec_driver_sql("SET FOREIGN_KEY_CHECKS = 0")
                for key in self.table_map.values():
                    conn.exec_driver_sql(f"TRUNCATE TABLE `{s}`.`{key}`")
                for table in ("Reviews", "Assignments", "Projects", "Employees", "Departments"):
                    conn.exec_driver_sql(f"TRUNCATE TABLE `{t}`.`{table}`")
                for table in ("Fact_PerformanceReviews", "Dim_Employee", "Dim_Date"):
                    conn.exec_driver_sql(f"TRUNCATE TABLE `{a}`.`{table}`")
                conn.exec_driver_sql(f"DELETE FROM `{a}`.`Dim_Department` WHERE department_sk > 0")
                conn.exec_driver_sql(f"DELETE FROM `{a}`.`Dim_Project` WHERE project_sk > 0")
                conn.exec_driver_sql("SET FOREIGN_KEY_CHECKS = 1")
        except SQLAlchemyError as exc:
            raise LoadError(f"Truncate failed (set CREATE_SCHEMA = True in config.py on the first run): {exc}") from exc

    def load_table(self, key, csv_path):
        table = self.table_map[key]
        renames = self.column_renames.get(key, {})
        total = 0
        start_time = time.time()
        try:
            for chunk in pd.read_csv(csv_path, chunksize=self.chunk_size):
                if renames:
                    chunk = chunk.rename(columns=renames)
                chunk.to_sql(table, con=self.engine, schema=config.STAGING_DB, if_exists="append", index=False)
                total += len(chunk)
        except (SQLAlchemyError, ValueError) as exc:
            raise LoadError(f"Loading {Path(csv_path).name} into {table} failed after {total:,} rows: {exc}") from exc
        log.info("Loaded %-26s %9s rows in %5.1fs", table, f"{total:,}", time.time() - start_time)
        return total

    def verify(self, expected):
        with self.engine.connect() as conn:
            for key, exp in expected.items():
                got = conn.execute(text(f"SELECT COUNT(*) FROM `{config.STAGING_DB}`.`{self.table_map[key]}`")).scalar()
                if got != exp:
                    raise LoadError(f"Row-count mismatch in {self.table_map[key]}: CSV={exp:,} DB={got:,}")
        log.info("Staging verification passed: all row counts match the CSVs")

    def run(self, data_dir, create_schema=True):
        data_dir = Path(data_dir)
        missing = [config.CSV_FILES[k] for k in LOAD_ORDER if not (data_dir / config.CSV_FILES[k]).exists()]
        if missing:
            raise LoadError(f"Missing CSVs in {data_dir}: {missing}. Run run_synthesis.py first.")
        self.check_connection()
        if create_schema:
            self.create_schema()
        else:
            self.truncate_all()
        counts = {k: self.load_table(k, data_dir / config.CSV_FILES[k]) for k in LOAD_ORDER}
        self.verify(counts)
        return counts


def main():
    # Runs staging load, then (if enabled) the OLTP / Dim_Employee / fact load, using the settings in config.py.
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-5s %(message)s", datefmt="%H:%M:%S")
    from scripts.warehouse_pipeline import WarehousePipeline  
    try:
        loader = BulkLoader(chunk_size=config.CHUNK_SIZE)
        counts = loader.run(config.OUTPUT_DIR, config.CREATE_SCHEMA)
        if config.RUN_WAREHOUSE_ETL:
            WarehousePipeline(loader.engine).run(counts)
    except LoadError as exc:
        log.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
