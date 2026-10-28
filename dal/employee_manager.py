from datetime import date
from typing import Optional

from exceptions import EntityNotFoundError
from models import Employee
from .base_manager import BaseManager

_COLS = ("employee_id, first_name, last_name, email, department_id, "
         "job_title, salary, hire_date, is_active")


class EmployeeManager(BaseManager):
    """CRUD on OLTP employees + transactional SCD-2 sync into the warehouse."""

    def create_employee(self, emp: Employee) -> int:
        """Insert employee, return new employee_id. Raises DuplicateEntityError on dup email."""
        return self._db.execute_query(
            "INSERT INTO employees (first_name, last_name, email, department_id, "
            "job_title, salary, hire_date, is_active) VALUES (%s,%s,%s,%s,%s,%s,%s,1)",
            (emp.first_name, emp.last_name, emp.email, emp.department_id,
             emp.job_title, emp.salary, emp.hire_date), self.oltp)

    def get_employee(self, employee_id: int) -> Employee:
        row = self._fetch_one(f"SELECT {_COLS} FROM employees WHERE employee_id=%s",
                              (employee_id,))
        if not row:
            raise EntityNotFoundError("Employee", employee_id)
        return Employee.from_row(row)

    def list_employees(self, department_id: Optional[int] = None,
                       active_only: bool = True, limit: int = 100,
                       offset: int = 0) -> list[dict]:
        sql, params = f"SELECT {_COLS} FROM employees WHERE 1=1", []
        if department_id:
            sql += " AND department_id=%s"; params.append(department_id)
        if active_only:
            sql += " AND is_active=1"
        sql += " ORDER BY employee_id LIMIT %s OFFSET %s"
        params += [limit, offset]
        return self._fetch_all(sql, params)

    def update_employee_department(self, employee_id: int, new_department_id: int,
                                   new_job_title: Optional[str] = None) -> None:
        """OLTP update + SCD-2 sync in ONE transaction (both commit or both roll back).

        The stored procedure is called with a database-qualified name on the OLTP
        connection so a single transaction covers both writes.
        """
        self.get_employee(employee_id)  # raises EntityNotFoundError
        with self._db.transaction(self.oltp) as cur:
            if new_job_title:
                cur.execute("UPDATE employees SET department_id=%s, job_title=%s "
                            "WHERE employee_id=%s",
                            (new_department_id, new_job_title, employee_id))
            else:
                cur.execute("UPDATE employees SET department_id=%s WHERE employee_id=%s",
                            (new_department_id, employee_id))
            cur.execute(f"CALL {self.olap}.sp_run_scd2_employee_sync()")
            while cur.nextset():   # drain SP result sets
                pass

    def update_salary(self, employee_id: int, new_salary: float) -> None:
        emp = self.get_employee(employee_id)
        emp.salary = new_salary  # validation
        with self._db.transaction(self.oltp) as cur:
            cur.execute("UPDATE employees SET salary=%s WHERE employee_id=%s",
                        (emp.salary, employee_id))
            cur.execute(f"CALL {self.olap}.sp_run_scd2_employee_sync()")
            while cur.nextset():
                pass

    def terminate_employee(self, employee_id: int, end_date: Optional[date] = None) -> None:
        self.get_employee(employee_id)
        with self._db.transaction(self.oltp) as cur:
            cur.execute("UPDATE employees SET is_active=0 WHERE employee_id=%s",
                        (employee_id,))
            cur.execute(f"CALL {self.olap}.sp_run_scd2_employee_sync()")
            while cur.nextset():
                pass
