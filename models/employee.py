from datetime import date
from typing import Optional

from . import validators as v


class Employee:
    """Employee entity (encapsulated; validated in setters)."""

    def __init__(self, first_name: str, last_name: str, email: str,
                 department_id: int, job_title: str, salary: float,
                 hire_date: date, employee_id: Optional[int] = None,
                 is_active: bool = True):
        self._employee_id = employee_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.department_id = department_id
        self.job_title = job_title
        self.salary = salary
        self.hire_date = hire_date
        self._is_active = bool(is_active)

    # read-only
    @property
    def employee_id(self): return self._employee_id
    @property
    def is_active(self): return self._is_active
    @property
    def full_name(self): return f"{self._first_name} {self._last_name}"

    @property
    def first_name(self): return self._first_name
    @first_name.setter
    def first_name(self, val): self._first_name = v.non_empty(val, "first_name")

    @property
    def last_name(self): return self._last_name
    @last_name.setter
    def last_name(self, val): self._last_name = v.non_empty(val, "last_name")

    @property
    def email(self): return self._email
    @email.setter
    def email(self, val): self._email = v.valid_email(val)

    @property
    def department_id(self): return self._department_id
    @department_id.setter
    def department_id(self, val):
        if not isinstance(val, int) or val <= 0:
            raise v.ValidationError("department_id must be a positive integer")
        self._department_id = val

    @property
    def job_title(self): return self._job_title
    @job_title.setter
    def job_title(self, val): self._job_title = v.non_empty(val, "job_title")

    @property
    def salary(self): return self._salary
    @salary.setter
    def salary(self, val): self._salary = v.valid_salary(val)

    @property
    def hire_date(self): return self._hire_date
    @hire_date.setter
    def hire_date(self, val): self._hire_date = v.not_future(val, "hire_date")

    def deactivate(self) -> None:
        self._is_active = False

    def to_dict(self) -> dict:
        return {"employee_id": self._employee_id, "first_name": self._first_name,
                "last_name": self._last_name, "email": self._email,
                "department_id": self._department_id, "job_title": self._job_title,
                "salary": self._salary, "hire_date": self._hire_date,
                "is_active": self._is_active}

    @classmethod
    def from_row(cls, row: dict) -> "Employee":
        return cls(row["first_name"], row["last_name"], row["email"],
                   row["department_id"], row["job_title"], row["salary"],
                   row["hire_date"], row.get("employee_id"), row.get("is_active", True))

    def __repr__(self):
        return f"Employee(id={self._employee_id}, {self.full_name}, dept={self._department_id})"
