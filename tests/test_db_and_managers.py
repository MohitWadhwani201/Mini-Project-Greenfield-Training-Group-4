import threading
from datetime import date
from unittest.mock import MagicMock
import pytest
from core.db_manager import DatabaseConnection
from dal import EmployeeManager, ProjectManager, ETLManager, AnalyticsManager
from exceptions import (EntityNotFoundError, WarehouseSyncError, DatabaseOperationError,
                        DuplicateEntityError, ValidationError)
from models import Assignment


@pytest.fixture(autouse=True)
def fresh():
    DatabaseConnection.reset_instance()
    yield
    DatabaseConnection.reset_instance()


def _db():
    db = MagicMock(); db.oltp_name, db.olap_name = "oltp", "olap"
    return db

EMP_ROW = dict(employee_id=1, first_name="A", last_name="B", email="a@b.com",
               hire_date=date(2020, 1, 1), department_id=1, job_role="Analyst",
               monthly_income=5000, date_of_birth=date(1990, 1, 1), gender="F",
               marital_status="Single", distance_from_home=5, education=3, is_active=1)


def test_singleton_is_thread_safe():
    seen = []
    ts = [threading.Thread(target=lambda: seen.append(id(DatabaseConnection()))) for _ in range(20)]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert len(set(seen)) == 1


def test_call_procedure_rejects_bad_name():
    with pytest.raises(DatabaseOperationError):
        DatabaseConnection().call_procedure("x; DROP TABLE Employees")


def test_get_missing_employee_raises():
    db = _db(); db.fetch_one.return_value = None
    with pytest.raises(EntityNotFoundError):
        EmployeeManager(db).get_employee(99)


def test_update_writes_oltp_then_syncs_scd2():
    db = _db(); db.fetch_one.return_value = EMP_ROW
    cur = MagicMock(); db.transaction.return_value.__enter__.return_value = cur
    EmployeeManager(db).update_employee_department(1, 2, "Senior Analyst")
    assert cur.execute.call_args.args[0].startswith("UPDATE Employees")
    assert cur.execute.call_args.args[1][:2] == (2, "Senior Analyst")
    db.call_procedure.assert_called_once_with("ETL_Dim_Employee_SCD2", (), "olap")


def test_sync_failure_raises_warehouse_error():
    db = _db(); db.fetch_one.return_value = EMP_ROW
    db.call_procedure.side_effect = DatabaseOperationError("boom")
    with pytest.raises(WarehouseSyncError):
        EmployeeManager(db).update_salary(1, 6000)


def test_invalid_salary_never_touches_db():
    db = _db(); db.fetch_one.return_value = EMP_ROW
    with pytest.raises(ValidationError):
        EmployeeManager(db).update_salary(1, 1)
    db.transaction.assert_not_called(); db.call_procedure.assert_not_called()


def test_duplicate_assignment_rejected():
    db = _db()
    db.fetch_one.side_effect = [{"x": 1}, {"project_id": 2, "project_name": "P",
        "start_date": date(2024, 1, 1), "end_date": None, "budget": None, "status": "Active"},
        {"x": 1}]
    with pytest.raises(DuplicateEntityError):
        ProjectManager(db).assign_employee(Assignment(1, 2))


def test_etl_runs_in_documented_order():
    db = _db(); ETLManager(db).run_full_etl(2015, 2028)
    names = [c.args[0] for c in db.call_procedure.call_args_list]
    assert names == ["Populate_Dim_Date", "ETL_Load_Simple_Dimensions",
                     "ETL_Dim_Employee_SCD2", "ETL_Fact_PerformanceReviews"]


def test_attrition_group_by_whitelist():
    with pytest.raises(ValidationError):
        AnalyticsManager(_db()).get_attrition_summary("1; DROP")