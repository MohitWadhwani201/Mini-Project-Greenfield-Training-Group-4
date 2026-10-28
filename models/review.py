from datetime import date
from typing import Optional

from . import validators as v


class PerformanceReview:
    """Maps to OLTP Reviews. All four scores use the 1-4 scale (see validators)."""

    def __init__(self, employee_id: int, performance_rating: int,
                 job_satisfaction: int, environment_satisfaction: int,
                 work_life_balance: int, review_date: Optional[date] = None,
                 review_id: Optional[int] = None):
        self._review_id = review_id
        self._employee_id = employee_id
        self.performance_rating = performance_rating
        self.job_satisfaction = job_satisfaction
        self.environment_satisfaction = environment_satisfaction
        self.work_life_balance = work_life_balance
        self.review_date = review_date or date.today()

    @property
    def review_id(self): return self._review_id
    @property
    def employee_id(self): return self._employee_id

    @property
    def performance_rating(self): return self._perf
    @performance_rating.setter
    def performance_rating(self, val): self._perf = v.rating(val, "performance_rating")

    @property
    def job_satisfaction(self): return self._js
    @job_satisfaction.setter
    def job_satisfaction(self, val): self._js = v.rating(val, "job_satisfaction")

    @property
    def environment_satisfaction(self): return self._es
    @environment_satisfaction.setter
    def environment_satisfaction(self, val): self._es = v.rating(val, "environment_satisfaction")

    @property
    def work_life_balance(self): return self._wlb
    @work_life_balance.setter
    def work_life_balance(self, val): self._wlb = v.rating(val, "work_life_balance")

    @property
    def review_date(self): return self._review_date
    @review_date.setter
    def review_date(self, val): self._review_date = v.not_future(val, "review_date")

    def to_dict(self):
        return {"review_id": self._review_id, "employee_id": self._employee_id,
                "review_date": self._review_date, "performance_rating": self._perf,
                "job_satisfaction": self._js, "environment_satisfaction": self._es,
                "work_life_balance": self._wlb}