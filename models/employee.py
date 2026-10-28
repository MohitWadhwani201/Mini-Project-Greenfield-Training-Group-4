from datetime import date
from typing import Optional

from . import validators as v


class Employee:
    """Maps to OLTP Employees. department_id may be None (FK is ON DELETE SET NULL)."""

    def __init__(self, first_name: str, last_name: str, email: str, hire_date: date,
                 department_id: Optional[int], job_role: str, monthly_income: float,
                 date_of_birth: Optional[date] = None, gender: Optional[str] = None,
                 marital_status: Optional[str] = None,
                 distance_from_home: Optional[int] = None,
                 education: Optional[int] = None,
                 employee_id: Optional[int] = None, is_active: bool = True):
        self._employee_id = employee_id
        self._is_active = bool(is_active)
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.hire_date = hire_date
        self.date_of_birth = date_of_birth
        self.department_id = department_id
        self.job_role = job_role
        self.monthly_income = monthly_income
        self.gender = gender
        self.marital_status = marital_status
        self.distance_from_home = distance_from_home
        self.education = education

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
    def hire_date(self): return self._hire_date
    @hire_date.setter
    def hire_date(self, val): self._hire_date = v.not_future(val, "hire_date")

    @property
    def date_of_birth(self): return self._dob
    @date_of_birth.setter
    def date_of_birth(self, val):
        val = v.valid_dob(val)
        if val is not None and val >= self._hire_date:
            raise v.ValidationError("date_of_birth must be before hire_date")
        self._dob = val

    @property
    def department_id(self): return self._department_id
    @department_id.setter
    def department_id(self, val):
        if val is not None and (not isinstance(val, int) or val <= 0):
            raise v.ValidationError("department_id must be a positive integer or None")
        self._department_id = val

    @property
    def job_role(self): return self._job_role
    @job_role.setter
    def job_role(self, val): self._job_role = v.non_empty(val, "job_role")

    @property
    def monthly_income(self): return self._income
    @monthly_income.setter
    def monthly_income(self, val): self._income = v.valid_income(val)

    @property
    def gender(self): return self._gender
    @gender.setter
    def gender(self, val): self._gender = v.optional_text(val, "gender")

    @property
    def marital_status(self): return self._marital
    @marital_status.setter
    def marital_status(self, val): self._marital = v.optional_text(val, "marital_status")

    @property
    def distance_from_home(self): return self._distance
    @distance_from_home.setter
    def distance_from_home(self, val):
        self._distance = None if val is None else int(v.in_range(val, 0, 1000, "distance_from_home"))

    @property
    def education(self): return self._education
    @education.setter
    def education(self, val):
        self._education = None if val is None else int(v.in_range(val, 1, 5, "education"))

    def to_dict(self) -> dict:
        return {"employee_id": self._employee_id, "first_name": self._first_name,
                "last_name": self._last_name, "email": self._email,
                "hire_date": self._hire_date, "department_id": self._department_id,
                "job_role": self._job_role, "monthly_income": self._income,
                "date_of_birth": self._dob, "gender": self._gender,
                "marital_status": self._marital, "distance_from_home": self._distance,
                "education": self._education, "is_active": self._is_active}

    @classmethod
    def from_row(cls, row: dict) -> "Employee":
        return cls(row["first_name"], row["last_name"], row["email"], row["hire_date"],
                   row.get("department_id"), row["job_role"], row["monthly_income"],
                   row.get("date_of_birth"), row.get("gender"), row.get("marital_status"),
                   row.get("distance_from_home"), row.get("education"),
                   row.get("employee_id"), bool(row.get("is_active", True)))

    def __repr__(self):
        return f"Employee(id={self._employee_id}, {self.full_name}, role={self._job_role})"