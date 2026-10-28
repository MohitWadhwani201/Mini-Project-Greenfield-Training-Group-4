from datetime import date
from typing import Optional

from . import validators as v

VALID_STATUSES = ("Active", "Planned", "Completed", "On Hold")


class Project:
    """Maps to OLTP Projects."""

    def __init__(self, project_name: str, start_date: date,
                 end_date: Optional[date] = None, budget: Optional[float] = None,
                 status: str = "Active", project_id: Optional[int] = None):
        self._project_id = project_id
        self.project_name = project_name
        self.set_dates(start_date, end_date)
        self.budget = budget
        self.status = status

    @property
    def project_id(self): return self._project_id
    @property
    def project_name(self): return self._name
    @project_name.setter
    def project_name(self, val): self._name = v.non_empty(val, "project_name")
    @property
    def start_date(self): return self._start_date
    @property
    def end_date(self): return self._end_date

    def set_dates(self, start: date, end: Optional[date]) -> None:
        if not isinstance(start, date):
            raise v.ValidationError("start_date must be a date")
        v.date_order(start, end)
        self._start_date, self._end_date = start, end

    @property
    def budget(self): return self._budget
    @budget.setter
    def budget(self, val):
        self._budget = None if val is None else v.in_range(val, 0, 9_999_999_999, "budget")

    @property
    def status(self): return self._status
    @status.setter
    def status(self, val):
        if val not in VALID_STATUSES:
            raise v.ValidationError(f"status must be one of {VALID_STATUSES}")
        self._status = val

    def to_dict(self):
        return {"project_id": self._project_id, "project_name": self._name,
                "start_date": self._start_date, "end_date": self._end_date,
                "budget": self._budget, "status": self._status}

    @classmethod
    def from_row(cls, row: dict):
        b = row.get("budget")
        return cls(row["project_name"], row["start_date"], row.get("end_date"),
                   None if b is None else float(b), row.get("status") or "Active",
                   row.get("project_id"))