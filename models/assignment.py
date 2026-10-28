from datetime import date
from typing import Optional

from . import validators as v


class Assignment:
    """Employee-to-project assignment with allocation percentage (1-100)."""

    def __init__(self, employee_id: int, project_id: int, allocation_pct: float,
                 role: str = "Contributor", assigned_date: Optional[date] = None,
                 assignment_id: Optional[int] = None):
        self._assignment_id = assignment_id
        self._employee_id = employee_id
        self._project_id = project_id
        self.allocation_pct = allocation_pct
        self.role = role
        self._assigned_date = assigned_date or date.today()

    @property
    def assignment_id(self): return self._assignment_id
    @property
    def employee_id(self): return self._employee_id
    @property
    def project_id(self): return self._project_id
    @property
    def assigned_date(self): return self._assigned_date

    @property
    def allocation_pct(self): return self._alloc
    @allocation_pct.setter
    def allocation_pct(self, val): self._alloc = v.in_range(val, 1, 100, "allocation_pct")

    @property
    def role(self): return self._role
    @role.setter
    def role(self, val): self._role = v.non_empty(val, "role")

    def to_dict(self):
        return {"assignment_id": self._assignment_id, "employee_id": self._employee_id,
                "project_id": self._project_id, "allocation_pct": self._alloc,
                "role": self._role, "assigned_date": self._assigned_date}
