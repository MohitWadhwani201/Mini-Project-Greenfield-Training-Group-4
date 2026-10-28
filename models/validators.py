import re
from datetime import date
from typing import Optional

from exceptions import ValidationError

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
MIN_INCOME, MAX_INCOME = 500, 500_000          # monthly_income DECIMAL(10,2)
MIN_AGE, MAX_AGE = 16, 100
RATING_MIN, RATING_MAX = 1, 4                  # IBM dataset scale (1-4)


def non_empty(value, field: str) -> str:
    if value is None or not str(value).strip():
        raise ValidationError(f"{field} cannot be empty")
    return str(value).strip()


def optional_text(value, field: str) -> Optional[str]:
    return None if value is None or not str(value).strip() else str(value).strip()


def valid_email(value: str) -> str:
    value = non_empty(value, "email")
    if not EMAIL_RE.match(value):
        raise ValidationError(f"Invalid email address: {value}")
    return value.lower()


def valid_income(value) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValidationError("monthly_income must be a number")
    if not MIN_INCOME <= value <= MAX_INCOME:
        raise ValidationError(f"monthly_income must be between {MIN_INCOME} and {MAX_INCOME}")
    return value


def not_future(value: date, field: str) -> date:
    if not isinstance(value, date):
        raise ValidationError(f"{field} must be a date")
    if value > date.today():
        raise ValidationError(f"{field} cannot be in the future")
    return value


def valid_dob(value: Optional[date]) -> Optional[date]:
    if value is None:
        return None
    not_future(value, "date_of_birth")
    age = (date.today() - value).days / 365.25
    if not MIN_AGE <= age <= MAX_AGE:
        raise ValidationError(f"date_of_birth implies age outside {MIN_AGE}-{MAX_AGE}")
    return value


def in_range(value, low, high, field: str):
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field} must be a number")
    if not low <= value <= high:
        raise ValidationError(f"{field} must be between {low} and {high}")
    return value


def rating(value, field: str) -> int:
    return int(in_range(value, RATING_MIN, RATING_MAX, field))


def date_order(start: date, end: Optional[date], what: str = "end_date") -> None:
    if end is not None and end < start:
        raise ValidationError(f"{what} cannot be before start date")