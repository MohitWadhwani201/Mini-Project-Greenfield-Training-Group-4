import threading
from unittest.mock import MagicMock
import pytest
from core.db_manager import DatabaseConnection
from dal import EmployeeManager
from exceptions import EntityNotFoundError


@pytest.fixture(autouse=True)
def fresh():
    DatabaseConnection.reset_instance()
    yield
    DatabaseConnection.reset_instance()


def test_singleton_is_thread_safe():
    seen = []
    ts = [threading.Thread(target=lambda: seen.append(id(DatabaseConnection()))) for _ in range(20)]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert len(set(seen)) == 1


def _mock_db():
    db = MagicMock(); db.oltp_name, db.olap_name = "oltp", "olap"
    return db


def test_get_missing_employee_raises():
    db = _mock_db(); db.fetch_one.return_value = None
    with pytest.raises(EntityNotFoundError):
        EmployeeManager(db).get_employee(99)


def test_department_update_runs_update_then_scd2_proc():
    db = _mock_db()
    db.fetch_one.return_value = dict(employee_id=1, first_name="A", last_name="B",
        email="a@b.com", department_id=1, job_title="X", salary=50000,
        hire_date=__import__("datetime").date(2020, 1, 1), is_active=1)
    cur = MagicMock(); cur.nextset.return_value = False
    db.transaction.return_value.__enter__.return_value = cur
    EmployeeManager(db).update_employee_department(1, 2)
    sqls = [c.args[0] for c in cur.execute.call_args_list]
    assert sqls[0].startswith("UPDATE employees") and "sp_run_scd2_employee_sync" in sqls[1]
