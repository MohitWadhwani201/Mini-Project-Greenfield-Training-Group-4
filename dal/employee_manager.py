from typing import Optional

from exceptions import EntityNotFoundError, WarehouseSyncError, DatabaseOperationError
from models import Employee
from .base_manager import BaseManager

_COLS = ("employee_id, first_name, last_name, email, hire_date, department_id, job_role, "
         "monthly_income, date_of_birth, gender, marital_status, distance_from_home, "
         "education, is_active")
SCD2_PROC = "ETL_Dim_Employee_SCD2"


class EmployeeManager(BaseManager):
    """CRUD on OLTP Employees + SCD-2 sync into Dim_Employee.

    Atomicity note: ETL_Dim_Employee_SCD2 runs its own START TRANSACTION/COMMIT in
    another database, so it cannot share a transaction with the OLTP write. Flow:
      1. OLTP write in a managed transaction (commit / rollback)
      2. CALL ETL_Dim_Employee_SCD2 on its own connection
    If step 2 fails the OLTP change stays saved and WarehouseSyncError is raised;
    the procedure is idempotent, so the next ETL run catches up.
    """

    # ---- internal ------------------------------------------------------
    def _sync_dim_employee(self) -> None:
        try:
            self._db.call_procedure(SCD2_PROC, (), self.olap)
        except DatabaseOperationError as exc:
            raise WarehouseSyncError(
                f"Change saved in OLTP but warehouse sync failed: {exc}") from exc

    # ---- create / read -------------------------------------------------
    def create_employee(self, emp: Employee, sync_warehouse: bool = True) -> int:
        """Insert employee, return employee_id. DuplicateEntityError on duplicate email."""
        new_id = self._db.execute_query(
            "INSERT INTO Employees (first_name, last_name, email, hire_date, department_id, "
            "job_role, monthly_income, date_of_birth, gender, marital_status, "
            "distance_from_home, education, is_active) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1)",
            (emp.first_name, emp.last_name, emp.email, emp.hire_date, emp.department_id,
             emp.job_role, emp.monthly_income, emp.date_of_birth, emp.gender,
             emp.marital_status, emp.distance_from_home, emp.education), self.oltp)
        if sync_warehouse:
            self._sync_dim_employee()   # opens the employee's first SCD-2 version
        return new_id

    def get_employee(self, employee_id: int) -> Employee:
        row = self._fetch_one(f"SELECT {_COLS} FROM Employees WHERE employee_id=%s",
                              (employee_id,))
        if not row:
            raise EntityNotFoundError("Employee", employee_id)
        return Employee.from_row(row)

    def list_employees(self, department_id: Optional[int] = None, active_only: bool = True,
                       limit: int = 100, offset: int = 0) -> list[dict]:
        sql = ("SELECT e.employee_id, e.first_name, e.last_name, e.email, e.hire_date, "
               "e.department_id, d.department_name, e.job_role, e.monthly_income, e.is_active "
               "FROM Employees e LEFT JOIN Departments d ON e.department_id=d.department_id "
               "WHERE 1=1")
        params: list = []
        if department_id:
            sql += " AND e.department_id=%s"; params.append(department_id)
        if active_only:
            sql += " AND e.is_active=1"
        sql += " ORDER BY e.employee_id LIMIT %s OFFSET %s"
        params += [limit, offset]
        return self._fetch_all(sql, params)

    # ---- updates (trigger SCD-2) --------------------------------------
    def update_employee_position(self, employee_id: int,
                                 department_id: Optional[int] = None,
                                 job_role: Optional[str] = None,
                                 monthly_income: Optional[float] = None) -> None:
        """Change department / role / income, then sync SCD-2.

        Dim_Employee versions on job_role and monthly_income ONLY, so a pure
        department change updates OLTP but opens no new Dim_Employee version.
        """
        emp = self.get_employee(employee_id)       # EntityNotFoundError if missing
        if department_id is not None: emp.department_id = department_id   # validates
        if job_role is not None: emp.job_role = job_role
        if monthly_income is not None: emp.monthly_income = monthly_income
        with self._db.transaction(self.oltp) as cur:
            cur.execute("UPDATE Employees SET department_id=%s, job_role=%s, "
                        "monthly_income=%s WHERE employee_id=%s",
                        (emp.department_id, emp.job_role, emp.monthly_income, employee_id))
        self._sync_dim_employee()

    def update_employee_department(self, employee_id: int, new_department_id: int,
                                   new_job_role: Optional[str] = None) -> None:
        self.update_employee_position(employee_id, department_id=new_department_id,
                                      job_role=new_job_role)

    def update_salary(self, employee_id: int, new_monthly_income: float) -> None:
        self.update_employee_position(employee_id, monthly_income=new_monthly_income)

    def terminate_employee(self, employee_id: int) -> None:
        """Soft delete (is_active=0). Dim_Employee does not track is_active: no sync."""
        self.get_employee(employee_id)
        with self._db.transaction(self.oltp) as cur:
            cur.execute("UPDATE Employees SET is_active=0 WHERE employee_id=%s", (employee_id,))

    # ---- lookups -------------------------------------------------------
    def list_departments(self) -> list[dict]:
        return self._fetch_all("SELECT department_id, department_name FROM Departments "
                               "ORDER BY department_name")

    def create_department(self, name: str) -> int:
        from models import Department
        dept = Department(name)
        return self._db.execute_query(
            "INSERT INTO Departments (department_name) VALUES (%s)",
            (dept.department_name,), self.oltp)