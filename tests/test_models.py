from datetime import date, timedelta
import pytest
from exceptions import ValidationError
from models import Employee, Project, Assignment, PerformanceReview


def make_emp(**kw):
    d = dict(first_name="Ana", last_name="Roy", email="Ana@Corp.com", department_id=1,
             job_title="Analyst", salary=50000, hire_date=date(2020, 1, 1))
    d.update(kw)
    return Employee(**d)


def test_valid_employee_normalizes_email():
    assert make_emp().email == "ana@corp.com"

@pytest.mark.parametrize("kw", [{"email": "bad"}, {"salary": 100}, {"first_name": " "},
    {"hire_date": date.today() + timedelta(days=1)}, {"department_id": 0}])
def test_invalid_employee(kw):
    with pytest.raises(ValidationError):
        make_emp(**kw)

def test_project_date_order_and_status():
    with pytest.raises(ValidationError):
        Project("X", date(2024, 5, 1), date(2024, 1, 1))
    with pytest.raises(ValidationError):
        Project("X", date(2024, 1, 1), status="Bogus")

@pytest.mark.parametrize("pct", [0, 101])
def test_assignment_allocation(pct):
    with pytest.raises(ValidationError):
        Assignment(1, 1, pct)

@pytest.mark.parametrize("rating,score", [(0, 50), (6, 50), (3, 101)])
def test_review_bounds(rating, score):
    with pytest.raises(ValidationError):
        PerformanceReview(1, rating, score)
