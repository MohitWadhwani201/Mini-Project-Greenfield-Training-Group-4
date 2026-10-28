"""Reusable validation helpers. All raise ValidationError."""
import re
from datetime import date
from typing import Optional

from exceptions import ValidationError

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
MIN_SALARY, MAX_SALARY = 15_000, 1_000_000


def non_empty(value: str, field: str) -> str:
    if value is None or not str(value).strip():
        raise ValidationError(f"{field} cannot be empty")
    return str(value).strip()


def valid_email(value: str) -> str:
    value = non_empty(value, "email")
    if not EMAIL_RE.match(value):
        raise ValidationError(f"Invalid email address: {value}")
    return value.lower()


def valid_salary(value) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValidationError("salary must be a number")
    if not MIN_SALARY <= value <= MAX_SALARY:
        raise ValidationError(f"salary must be between {MIN_SALARY} and {MAX_SALARY}")
    return value


def not_future(value: date, field: str) -> date:
    if not isinstance(value, date):
        raise ValidationError(f"{field} must be a date")
    if value > date.today():
        raise ValidationError(f"{field} cannot be in the future")
    return value


def in_range(value, low, high, field: str):
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field} must be a number")
    if not low <= value <= high:
        raise ValidationError(f"{field} must be between {low} and {high}")
    return value


def date_order(start: date, end: Optional[date], what: str = "end_date") -> None:
    if end is not None and end < start:
        raise ValidationError(f"{what} cannot be before start date")
