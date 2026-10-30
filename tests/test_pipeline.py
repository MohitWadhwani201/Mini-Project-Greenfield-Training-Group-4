# Unit tests for the synthesis pipeline (uses a mock CSV, no database needed). Run with: pytest -q
import pytest

from synthesizer import (DataQualityValidator, DimDateGenerator, EmployeeSynthesizer,
                         RelatedDataSynthesizer, SCD2HistoryGenerator)
from tests.make_mock_ibm_csv import make

REF = "2026-10-28"


@pytest.fixture(scope="module")
def data(tmp_path_factory):
    # Builds a small 5,000-employee dataset once for all tests.
    csv = tmp_path_factory.mktemp("raw") / "ibm.csv"
    make(str(csv))
    emp = EmployeeSynthesizer(csv, 5000, REF, 1).scale()
    hist = SCD2HistoryGenerator(emp, REF, 0.25, 1).generate()
    rel = RelatedDataSynthesizer(emp, REF, 1)
    proj = rel.generate_projects()
    return emp, hist, proj, rel.generate_assignments(proj), rel.generate_reviews()


def test_scales_to_target(data):
    # Employee count equals the target and IDs are unique.
    assert len(data[0]) == 5000 and data[0]["employee_id"].is_unique


def test_change_fraction_close_to_25_percent(data):
    # About 25% of employees should have more than one history version.
    hist = data[1]
    assert 0.20 <= (hist.groupby("employee_id").size() > 1).mean() <= 0.30


def test_all_quality_checks_pass(data):
    # All data-quality checks must pass.
    emp, hist, proj, asg, rev = data
    results = DataQualityValidator(emp, hist, proj, asg, rev, DimDateGenerator().generate(), min_rows=5000).run()
    assert all(passed for _, passed, _ in results), [r for r in results if not r[1]]


def test_reproducible(tmp_path):
    # The same seed must produce identical data.
    csv = tmp_path / "ibm.csv"
    make(str(csv))
    a = EmployeeSynthesizer(csv, 2000, REF, 5).scale()
    b = EmployeeSynthesizer(csv, 2000, REF, 5).scale()
    assert a.equals(b)


def test_missing_input_gives_helpful_error(tmp_path):
    # A missing IBM file should give a clear error message.
    with pytest.raises(FileNotFoundError, match="Kaggle"):
        EmployeeSynthesizer(tmp_path / "nope.csv", 100, REF).scale()


def test_assignments_dates_are_valid(data):
    # Assignment dates must be on or after the project start and the hire date, and before the employee left.
    emp, _, proj, asg, _ = data
    a = asg.merge(proj[["project_id", "start_date"]], on="project_id").merge(
        emp[["employee_id", "hire_date", "termination_date"]], on="employee_id")
    assert (a["assigned_date"] >= a["start_date"]).all()
    assert (a["assigned_date"] >= a["hire_date"]).all()
    assert (a["assigned_date"] <= a["termination_date"].fillna(a["assigned_date"])).all()


def test_review_columns_match_part1_oltp(data):
    # Reviews must have exactly the Part 1 OLTP Reviews columns.
    assert list(data[4].columns) == ["review_id", "employee_id", "review_date", "performance_rating",
                                     "job_satisfaction", "environment_satisfaction", "work_life_balance"]


def test_sql_runner_handles_delimiters_and_comments():
    # DELIMITER blocks stay in one statement; trailing comments do not hide the semicolon.
    from scripts.sql_runner import split_sql
    text = ("USE db;  -- comment\nDELIMITER //\nCREATE PROCEDURE p()\nBEGIN\n  SELECT 1;\n  SELECT 2;\nEND //\n"
            "DELIMITER ;\nSELECT 3;")
    statements = split_sql(text)
    assert len(statements) == 3
    assert statements[0] == "USE db"
    assert "SELECT 1;" in statements[1] and "SELECT 2;" in statements[1]
