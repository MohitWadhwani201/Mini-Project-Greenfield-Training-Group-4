from typing import Optional

from . import validators as v


class Department:
    def __init__(self, department_name: str, department_id: Optional[int] = None):
        self._department_id = department_id
        self.department_name = department_name

    @property
    def department_id(self): return self._department_id
    @property
    def department_name(self): return self._name
    @department_name.setter
    def department_name(self, val): self._name = v.non_empty(val, "department_name")

    def to_dict(self):
        return {"department_id": self._department_id, "department_name": self._name}

    @classmethod
    def from_row(cls, row: dict):
        return cls(row["department_name"], row.get("department_id"))
