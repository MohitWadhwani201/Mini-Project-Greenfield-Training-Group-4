from datetime import date
from typing import Optional

from . import validators as v


class PerformanceReview:
    """rating: 1-5 integer scale; performance_score: 0-100."""

    def __init__(self, employee_id: int, rating: int, performance_score: float,
                 review_date: Optional[date] = None, comments: str = "",
                 review_id: Optional[int] = None):
        self._review_id = review_id
        self._employee_id = employee_id
        self.rating = rating
        self.performance_score = performance_score
        self.review_date = review_date or date.today()
        self.comments = comments or ""

    @property
    def review_id(self): return self._review_id
    @property
    def employee_id(self): return self._employee_id

    @property
    def rating(self): return self._rating
    @rating.setter
    def rating(self, val): self._rating = int(v.in_range(val, 1, 5, "rating"))

    @property
    def performance_score(self): return self._score
    @performance_score.setter
    def performance_score(self, val): self._score = v.in_range(val, 0, 100, "performance_score")

    @property
    def review_date(self): return self._review_date
    @review_date.setter
    def review_date(self, val): self._review_date = v.not_future(val, "review_date")

    def to_dict(self):
        return {"review_id": self._review_id, "employee_id": self._employee_id,
                "rating": self._rating, "performance_score": self._score,
                "review_date": self._review_date, "comments": self.comments}
