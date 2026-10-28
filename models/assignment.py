from datetime import date
from typing import Optional

from . import validators as v


class Assignment:
    """Maps to OLTP Assignments (employee <-> project junction)."""

    def __init__(self, employee_id: int, project_id: int,
                 role_on_project: Optional[str] = None,
                 assignment_date: Optional[date] = None,
                 assignment_id: Optional[int] = None):
        self._assignment_id = assignment_id
        self._employee_id = employee_id
        self._project_id = project_id
        self.role_on_project = role_on_project
        self._assignment_date = assignment_date or date.today()

    @property
    def assignment_id(self): return self._assignment_id
    @property
    def employee_id(self): return self._employee_id
    @property
    def project_id(self): return self._project_id
    @property
    def assignment_date(self): return self._assignment_date

    @property
    def role_on_project(self): return self._role
    @role_on_project.setter
    def role_on_project(self, val): self._role = v.optional_text(val, "role_on_project")

    def to_dict(self):
        return {"assignment_id": self._assignment_id, "employee_id": self._employee_id,
                "project_id": self._project_id, "role_on_project": self._role,
                "assignment_date": self._assignment_date}