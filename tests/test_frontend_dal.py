"""
Unit & Integration validation for Frontend DAL client, charts, and SCD-2 simulation.
"""
from datetime import date
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from frontend.dal_client import DALClient
from frontend.charts import (
    create_yoy_performance_chart,
    create_leaderboard_chart,
    create_attrition_chart,
    create_bottlenecks_matrix_chart,
    create_scd2_timeline_chart,
)
from models import Employee, Project, Assignment, PerformanceReview


def test_frontend_flow():
    dal = DALClient.get_instance()
    print("Testing Departments...")
    depts = dal.list_departments()
    assert len(depts) > 0, "Departments should not be empty"

    print("Testing Employees...")
    emps = dal.list_employees()
    assert len(emps) > 0, "Employees should not be empty"

    print("Testing Analytics YoY...")
    yoy = dal.get_yoy_performance()
    assert len(yoy) > 0, "YoY should return rows"
    fig_yoy = create_yoy_performance_chart(yoy)
    assert fig_yoy is not None

    print("Testing Leaderboard DENSE_RANK...")
    leaders = dal.get_top_performers(top_n=5)
    assert len(leaders) > 0, "Leaderboard should return ranked employees"
    fig_lead = create_leaderboard_chart(leaders, top_n=5)
    assert fig_lead is not None

    print("Testing Attrition Summary...")
    att = dal.get_attrition_summary(group_by="department")
    assert len(att) > 0
    fig_att = create_attrition_chart(att, group_by="Department")
    assert fig_att is not None

    print("Testing Project Bottlenecks...")
    proj_bn = dal.get_project_bottlenecks()
    assert len(proj_bn) > 0
    fig_bn = create_bottlenecks_matrix_chart(proj_bn)
    assert fig_bn is not None

    print("Testing SCD-2 Time-Travel Timeline...")
    history_before = dal.get_employee_history(101)
    assert len(history_before) >= 1
    fig_time = create_scd2_timeline_chart(history_before)
    assert fig_time is not None

    print("Testing SCD-2 Update Execution...")
    emp_before = dal.get_employee(101)
    old_income = emp_before.monthly_income
    new_income = old_income + 2500.0
    dal.update_employee_position(
        employee_id=101,
        department_id=emp_before.department_id,
        job_role="Distinguished Enterprise Architect",
        monthly_income=new_income,
    )
    history_after = dal.get_employee_history(101)
    assert len(history_after) == len(history_before) + 1, "SCD-2 must create a new active version"

    # Verify version closure
    old_ver = [v for v in history_after if v["is_current"] == 0][-1]
    new_ver = [v for v in history_after if v["is_current"] == 1][0]
    assert old_ver["end_date"] is not None, "Previous version must have closed end_date"
    assert new_ver["is_current"] == 1, "New version must be marked is_current"
    assert new_ver["monthly_income"] == new_income, "New version must have new salary"
    print(f"SCD-2 Validated! Old Version closed on {old_ver['end_date']}, New Version active with income {new_ver['monthly_income']}")

    print("\nALL FRONTEND & DAL TESTS PASSED PERFECTLY!")


if __name__ == "__main__":
    test_frontend_flow()

