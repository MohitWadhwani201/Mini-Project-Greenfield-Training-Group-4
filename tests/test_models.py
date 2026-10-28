from datetime import date, timedelta
import pytest
from exceptions import ValidationError
from models import Employee, Project, Assignment, PerformanceReview


def make_emp(**kw):
    d = dict(first_name="Ana", last_name="Roy", email="Ana@Corp.com",
             hire_date=date(2020, 1, 1), department_id=1, job_role="Analyst",
             monthly_income=5000, date_of_birth=date(1995, 5, 5))
    d.update(kw)
    return Employee(**d)


def test_valid_employee_normalizes_email():
    assert make_emp().email == "ana@corp.com"

def test_department_may_be_none():
    assert make_emp(department_id=None).department_id is None

@pytest.mark.parametrize("kw", [
    {"email": "bad"}, {"monthly_income": 10}, {"first_name": " "}, {"job_role": ""},
    {"hire_date": date.today() + timedelta(days=1)}, {"department_id": 0},
    {"date_of_birth": date(2020, 6, 1)}, {"education": 9}, {"distance_from_home": -1}])
def test_invalid_employee(kw):
    with pytest.raises(ValidationError):
        make_emp(**kw)

def test_project_rules():
    with pytest.raises(ValidationError):
        Project("X", date(2024, 5, 1), date(2024, 1, 1))
    with pytest.raises(ValidationError):
        Project("X", date(2024, 1, 1), status="Bogus")
    with pytest.raises(ValidationError):
        Project("X", date(2024, 1, 1), budget=-5)
    assert Project("X", date(2024, 1, 1)).status == "Active"

def test_assignment_defaults():
    a = Assignment(1, 2, "Lead")
    assert a.assignment_date == date.today() and a.role_on_project == "Lead"

@pytest.mark.parametrize("field", ["performance_rating", "job_satisfaction",
                                   "environment_satisfaction", "work_life_balance"])
@pytest.mark.parametrize("bad", [0, 5])
def test_review_bounds(field, bad):
    args = dict(employee_id=1, performance_rating=3, job_satisfaction=3,
                environment_satisfaction=3, work_life_balance=3)
    args[field] = bad
    with pytest.raises(ValidationError):
        PerformanceReview(**args)