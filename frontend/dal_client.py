"""
DAL Client & Service Layer.
Connects the Streamlit UI to the Object-Oriented DAL Managers:
- EmployeeManager
- ProjectManager
- AnalyticsManager
- ETLManager

Includes connection health monitoring and a high-fidelity in-memory sandbox
fallback to allow seamless interactive evaluation even if MySQL is offline.
"""
from datetime import date, timedelta
from typing import Any, Dict, List, Optional
import random

from core.db_manager import DatabaseConnection
from dal import AnalyticsManager, EmployeeManager, ETLManager, ProjectManager
from exceptions import (
    AppError,
    DatabaseOperationError,
    DuplicateEntityError,
    EntityNotFoundError,
    ValidationError,
    WarehouseSyncError,
)
from models import Assignment, Department, Employee, PerformanceReview, Project


class DALClient:
    """Singleton service for Streamlit that wraps DAL managers with resilience."""

    _instance: Optional["DALClient"] = None

    def __init__(self):
        self._db: Optional[DatabaseConnection] = None
        self._emp_mgr: Optional[EmployeeManager] = None
        self._proj_mgr: Optional[ProjectManager] = None
        self._analytics_mgr: Optional[AnalyticsManager] = None
        self._etl_mgr: Optional[ETLManager] = None
        self.is_connected: bool = False
        self.connection_error: Optional[str] = None
        self.force_demo_mode: bool = False

        self._init_managers()
        self._init_sandbox_data()

    @classmethod
    def get_instance(cls) -> "DALClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _init_managers(self) -> None:
        """Attempt to instantiate real DAL managers."""
        try:
            self._db = DatabaseConnection()
            self._emp_mgr = EmployeeManager(self._db)
            self._proj_mgr = ProjectManager(self._db)
            self._analytics_mgr = AnalyticsManager(self._db)
            self._etl_mgr = ETLManager(self._db)
            # Test ping
            self._db.fetch_one("SELECT 1 AS ping", olap=False)
            self.is_connected = True
            self.connection_error = None
        except Exception as e:
            self.is_connected = False
            self.connection_error = str(e)

    def ping(self) -> bool:
        """Re-verify connection status."""
        try:
            DatabaseConnection.reset_instance()
            self._init_managers()
            return self.is_connected
        except Exception as e:
            self.is_connected = False
            self.connection_error = str(e)
            return False

    # =========================================================================
    # IN-MEMORY SANDBOX STATE (Used when MySQL is offline or in Demo Mode)
    # Implements full SCD Type 2 logic and Star Schema semantics!
    # =========================================================================
    def _init_sandbox_data(self) -> None:
        today = date.today()
        self._demo_depts = [
            {"department_id": 1, "department_name": "Research & Development"},
            {"department_id": 2, "department_name": "Sales & Business Development"},
            {"department_id": 3, "department_name": "Human Resources"},
            {"department_id": 4, "department_name": "Engineering & Technology"},
            {"department_id": 5, "department_name": "Product & Strategy"},
        ]

        self._demo_employees: List[Dict[str, Any]] = [
            {
                "employee_id": 101,
                "first_name": "Aarav",
                "last_name": "Sharma",
                "email": "aarav.sharma@enterprise.com",
                "hire_date": date(2020, 3, 15),
                "department_id": 4,
                "department_name": "Engineering & Technology",
                "job_role": "Lead Architect",
                "monthly_income": 18500.0,
                "date_of_birth": date(1988, 5, 12),
                "gender": "Male",
                "marital_status": "Married",
                "distance_from_home": 12,
                "education": 4,
                "is_active": 1,
            },
            {
                "employee_id": 102,
                "first_name": "Priya",
                "last_name": "Patel",
                "email": "priya.patel@enterprise.com",
                "hire_date": date(2021, 6, 1),
                "department_id": 1,
                "department_name": "Research & Development",
                "job_role": "Senior Research Scientist",
                "monthly_income": 14200.0,
                "date_of_birth": date(1991, 8, 24),
                "gender": "Female",
                "marital_status": "Single",
                "distance_from_home": 5,
                "education": 5,
                "is_active": 1,
            },
            {
                "employee_id": 103,
                "first_name": "Rohan",
                "last_name": "Verma",
                "email": "rohan.verma@enterprise.com",
                "hire_date": date(2019, 11, 10),
                "department_id": 2,
                "department_name": "Sales & Business Development",
                "job_role": "Sales Executive",
                "monthly_income": 9800.0,
                "date_of_birth": date(1994, 2, 17),
                "gender": "Male",
                "marital_status": "Single",
                "distance_from_home": 28,
                "education": 3,
                "is_active": 0,  # Attrited
            },
            {
                "employee_id": 104,
                "first_name": "Ananya",
                "last_name": "Deshmukh",
                "email": "ananya.d@enterprise.com",
                "hire_date": date(2022, 1, 15),
                "department_id": 3,
                "department_name": "Human Resources",
                "job_role": "HR Business Partner",
                "monthly_income": 11500.0,
                "date_of_birth": date(1993, 11, 30),
                "gender": "Female",
                "marital_status": "Married",
                "distance_from_home": 8,
                "education": 4,
                "is_active": 1,
            },
            {
                "employee_id": 105,
                "first_name": "Vikram",
                "last_name": "Malhotra",
                "email": "vikram.m@enterprise.com",
                "hire_date": date(2018, 4, 1),
                "department_id": 5,
                "department_name": "Product & Strategy",
                "job_role": "Director of Product",
                "monthly_income": 24000.0,
                "date_of_birth": date(1983, 9, 5),
                "gender": "Male",
                "marital_status": "Married",
                "distance_from_home": 15,
                "education": 5,
                "is_active": 1,
            },
        ]

        # SCD-2 Historical Dimension table
        self._demo_dim_employee: List[Dict[str, Any]] = [
            # Aarav has 2 versions (promoted last year)
            {
                "employee_sk": 1,
                "employee_id": 101,
                "first_name": "Aarav",
                "last_name": "Sharma",
                "job_role": "Software Engineer",
                "monthly_income": 12000.0,
                "age": 32,
                "gender": "Male",
                "start_date": date(2020, 3, 15),
                "end_date": date(2023, 12, 31),
                "is_current": 0,
                "income_change": 0.0,
            },
            {
                "employee_sk": 2,
                "employee_id": 101,
                "first_name": "Aarav",
                "last_name": "Sharma",
                "job_role": "Lead Architect",
                "monthly_income": 18500.0,
                "age": 36,
                "gender": "Male",
                "start_date": date(2024, 1, 1),
                "end_date": None,
                "is_current": 1,
                "income_change": 6500.0,
            },
            # Priya
            {
                "employee_sk": 3,
                "employee_id": 102,
                "first_name": "Priya",
                "last_name": "Patel",
                "job_role": "Senior Research Scientist",
                "monthly_income": 14200.0,
                "age": 33,
                "gender": "Female",
                "start_date": date(2021, 6, 1),
                "end_date": None,
                "is_current": 1,
                "income_change": 0.0,
            },
            # Rohan
            {
                "employee_sk": 4,
                "employee_id": 103,
                "first_name": "Rohan",
                "last_name": "Verma",
                "job_role": "Sales Executive",
                "monthly_income": 9800.0,
                "age": 30,
                "gender": "Male",
                "start_date": date(2019, 11, 10),
                "end_date": None,
                "is_current": 1,
                "income_change": 0.0,
            },
            # Ananya
            {
                "employee_sk": 5,
                "employee_id": 104,
                "first_name": "Ananya",
                "last_name": "Deshmukh",
                "job_role": "HR Business Partner",
                "monthly_income": 11500.0,
                "age": 31,
                "gender": "Female",
                "start_date": date(2022, 1, 15),
                "end_date": None,
                "is_current": 1,
                "income_change": 0.0,
            },
            # Vikram
            {
                "employee_sk": 6,
                "employee_id": 105,
                "first_name": "Vikram",
                "last_name": "Malhotra",
                "job_role": "Director of Product",
                "monthly_income": 24000.0,
                "age": 41,
                "gender": "Male",
                "start_date": date(2018, 4, 1),
                "end_date": None,
                "is_current": 1,
                "income_change": 0.0,
            },
        ]

        self._demo_projects: List[Dict[str, Any]] = [
            {
                "project_id": 201,
                "project_name": "Project Titan: NextGen AI Engine",
                "start_date": date(2023, 1, 1),
                "end_date": date(2025, 6, 30),
                "budget": 4500000.0,
                "status": "Active",
            },
            {
                "project_id": 202,
                "project_name": "Phoenix HR Cloud Migration",
                "start_date": date(2022, 8, 15),
                "end_date": date(2024, 12, 31),
                "budget": 1200000.0,
                "status": "Active",
            },
            {
                "project_id": 203,
                "project_name": "Global ERP Consolidation",
                "start_date": date(2021, 5, 1),
                "end_date": date(2023, 11, 30),
                "budget": 3100000.0,
                "status": "Completed",
            },
            {
                "project_id": 204,
                "project_name": "Quantum Analytics & BI Portal",
                "start_date": date(2024, 2, 1),
                "end_date": date(2026, 1, 31),
                "budget": 2800000.0,
                "status": "Active",
            },
        ]

        self._demo_assignments: List[Dict[str, Any]] = [
            {
                "assignment_id": 1,
                "employee_id": 101,
                "employee_name": "Aarav Sharma",
                "project_id": 201,
                "project_name": "Project Titan: NextGen AI Engine",
                "role_on_project": "Technical Lead",
                "assignment_date": date(2023, 1, 15),
            },
            {
                "assignment_id": 2,
                "employee_id": 102,
                "employee_name": "Priya Patel",
                "project_id": 201,
                "project_name": "Project Titan: NextGen AI Engine",
                "role_on_project": "Lead AI Researcher",
                "assignment_date": date(2023, 2, 1),
            },
            {
                "assignment_id": 3,
                "employee_id": 104,
                "employee_name": "Ananya Deshmukh",
                "project_id": 202,
                "project_name": "Phoenix HR Cloud Migration",
                "role_on_project": "Change Management Lead",
                "assignment_date": date(2022, 9, 1),
            },
        ]

        self._demo_reviews: List[Dict[str, Any]] = [
            {"review_id": 1, "employee_id": 101, "review_date": date(2021, 12, 10), "performance_rating": 3, "job_satisfaction": 3, "environment_satisfaction": 3, "work_life_balance": 3},
            {"review_id": 2, "employee_id": 101, "review_date": date(2022, 12, 15), "performance_rating": 4, "job_satisfaction": 4, "environment_satisfaction": 3, "work_life_balance": 3},
            {"review_id": 3, "employee_id": 101, "review_date": date(2023, 12, 20), "performance_rating": 4, "job_satisfaction": 4, "environment_satisfaction": 4, "work_life_balance": 4},
            {"review_id": 4, "employee_id": 102, "review_date": date(2022, 12, 12), "performance_rating": 4, "job_satisfaction": 3, "environment_satisfaction": 4, "work_life_balance": 2},
            {"review_id": 5, "employee_id": 102, "review_date": date(2023, 12, 18), "performance_rating": 4, "job_satisfaction": 4, "environment_satisfaction": 4, "work_life_balance": 3},
            {"review_id": 6, "employee_id": 103, "review_date": date(2021, 11, 20), "performance_rating": 2, "job_satisfaction": 1, "environment_satisfaction": 2, "work_life_balance": 1},
            {"review_id": 7, "employee_id": 105, "review_date": date(2023, 12, 14), "performance_rating": 4, "job_satisfaction": 4, "environment_satisfaction": 4, "work_life_balance": 3},
        ]

    # =========================================================================
    # EMPLOYEE OPERATIONS (OLTP + SCD-2)
    # =========================================================================
    def list_departments(self) -> List[Dict[str, Any]]:
        if self.is_connected and not self.force_demo_mode:
            try:
                return self._emp_mgr.list_departments()
            except Exception:
                pass
        return list(self._demo_depts)

    def list_employees(
        self, department_id: Optional[int] = None, active_only: bool = True, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        if self.is_connected and not self.force_demo_mode:
            try:
                return self._emp_mgr.list_employees(department_id, active_only, limit, offset)
            except Exception:
                pass
        emps = self._demo_employees
        if department_id:
            emps = [e for e in emps if e.get("department_id") == department_id]
        if active_only:
            emps = [e for e in emps if e.get("is_active") == 1]
        return emps[offset : offset + limit]

    def get_employee(self, employee_id: int) -> Employee:
        if self.is_connected and not self.force_demo_mode:
            try:
                return self._emp_mgr.get_employee(employee_id)
            except Exception:
                pass
        for e in self._demo_employees:
            if e["employee_id"] == employee_id:
                return Employee.from_row(e)
        raise EntityNotFoundError("Employee", employee_id)

    def create_employee(self, emp: Employee, sync_warehouse: bool = True) -> int:
        """Create new employee via DAL, opening their initial SCD-2 dimension."""
        if self.is_connected and not self.force_demo_mode:
            return self._emp_mgr.create_employee(emp, sync_warehouse)

        # Demo Mode logic
        new_id = max([e["employee_id"] for e in self._demo_employees], default=100) + 1
        emp_dict = emp.to_dict()
        emp_dict["employee_id"] = new_id

        # Attach department name
        dept = next((d for d in self._demo_depts if d["department_id"] == emp.department_id), None)
        emp_dict["department_name"] = dept["department_name"] if dept else "Unassigned"

        self._demo_employees.append(emp_dict)

        if sync_warehouse:
            new_sk = max([v["employee_sk"] for v in self._demo_dim_employee], default=0) + 1
            age = (date.today() - emp.date_of_birth).days // 365 if emp.date_of_birth else 30
            self._demo_dim_employee.append(
                {
                    "employee_sk": new_sk,
                    "employee_id": new_id,
                    "first_name": emp.first_name,
                    "last_name": emp.last_name,
                    "job_role": emp.job_role,
                    "monthly_income": emp.monthly_income,
                    "age": age,
                    "gender": emp.gender or "Other",
                    "start_date": emp.hire_date,
                    "end_date": None,
                    "is_current": 1,
                    "income_change": 0.0,
                }
            )
        return new_id

    def update_employee_position(
        self,
        employee_id: int,
        department_id: Optional[int] = None,
        job_role: Optional[str] = None,
        monthly_income: Optional[float] = None,
    ) -> None:
        """
        Updates employee position in OLTP and triggers SCD-2 sync in OLAP.
        Marks previous version inactive (is_current=0, end_date=yesterday) and
        inserts new active version (is_current=1, start_date=today).
        """
        if self.is_connected and not self.force_demo_mode:
            self._emp_mgr.update_employee_position(employee_id, department_id, job_role, monthly_income)
            return

        # Demo Mode: Execute SCD-2 logic in memory
        emp = self.get_employee(employee_id)
        old_income = emp.monthly_income
        old_role = emp.job_role

        # Update in OLTP
        for e in self._demo_employees:
            if e["employee_id"] == employee_id:
                if department_id is not None:
                    e["department_id"] = department_id
                    d = next((d for d in self._demo_depts if d["department_id"] == department_id), None)
                    e["department_name"] = d["department_name"] if d else "Unassigned"
                if job_role is not None:
                    e["job_role"] = job_role
                if monthly_income is not None:
                    e["monthly_income"] = float(monthly_income)
                break

        # Check if SCD-2 tracked columns changed (job_role or monthly_income)
        role_changed = (job_role is not None) and (job_role != old_role)
        income_changed = (monthly_income is not None) and (float(monthly_income) != float(old_income))

        if role_changed or income_changed:
            yesterday = date.today() - timedelta(days=1)
            # Step A: Close active version
            prev_version = None
            for v in self._demo_dim_employee:
                if v["employee_id"] == employee_id and v["is_current"] == 1:
                    v["is_current"] = 0
                    v["end_date"] = yesterday
                    prev_version = v
                    break

            # Step B: Insert new active version
            new_sk = max([v["employee_sk"] for v in self._demo_dim_employee], default=0) + 1
            new_income = float(monthly_income) if monthly_income is not None else old_income
            new_job = job_role if job_role is not None else old_role
            diff = new_income - (prev_version["monthly_income"] if prev_version else new_income)

            self._demo_dim_employee.append(
                {
                    "employee_sk": new_sk,
                    "employee_id": employee_id,
                    "first_name": emp.first_name,
                    "last_name": emp.last_name,
                    "job_role": new_job,
                    "monthly_income": new_income,
                    "age": 30,
                    "gender": emp.gender or "Other",
                    "start_date": date.today(),
                    "end_date": None,
                    "is_current": 1,
                    "income_change": diff,
                }
            )

    # =========================================================================
    # PROJECT & REVIEW OPERATIONS (OLTP)
    # =========================================================================
    def create_project(self, project: Project) -> int:
        if self.is_connected and not self.force_demo_mode:
            return self._proj_mgr.create_project(project)
        new_id = max([p["project_id"] for p in self._demo_projects], default=200) + 1
        p_dict = project.to_dict()
        p_dict["project_id"] = new_id
        self._demo_projects.append(p_dict)
        return new_id

    def list_projects(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.is_connected and not self.force_demo_mode:
            try:
                return self._proj_mgr.list_projects(status)
            except Exception:
                pass
        projs = self._demo_projects
        if status:
            projs = [p for p in projs if p.get("status") == status]
        return projs

    def assign_employee(self, assignment: Assignment) -> int:
        if self.is_connected and not self.force_demo_mode:
            return self._proj_mgr.assign_employee(assignment)

        # Check duplicates
        for a in self._demo_assignments:
            if a["employee_id"] == assignment.employee_id and a["project_id"] == assignment.project_id:
                raise DuplicateEntityError(
                    f"Employee {assignment.employee_id} is already assigned to project {assignment.project_id}"
                )

        emp = self.get_employee(assignment.employee_id)
        proj = next((p for p in self._demo_projects if p["project_id"] == assignment.project_id), None)
        if not proj:
            raise EntityNotFoundError("Project", assignment.project_id)

        new_aid = max([a["assignment_id"] for a in self._demo_assignments], default=0) + 1
        self._demo_assignments.append(
            {
                "assignment_id": new_aid,
                "employee_id": assignment.employee_id,
                "employee_name": emp.full_name,
                "project_id": assignment.project_id,
                "project_name": proj["project_name"],
                "role_on_project": assignment.role_on_project or "Contributor",
                "assignment_date": assignment.assignment_date,
            }
        )
        return new_aid

    def list_assignments(
        self, project_id: Optional[int] = None, employee_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        if self.is_connected and not self.force_demo_mode:
            try:
                return self._proj_mgr.list_assignments(project_id, employee_id)
            except Exception:
                pass
        assigns = self._demo_assignments
        if project_id:
            assigns = [a for a in assigns if a.get("project_id") == project_id]
        if employee_id:
            assigns = [a for a in assigns if a.get("employee_id") == employee_id]
        return assigns

    def submit_review(self, review: PerformanceReview) -> int:
        if self.is_connected and not self.force_demo_mode:
            return self._proj_mgr.submit_review(review)

        emp = self.get_employee(review.employee_id)
        new_rid = max([r["review_id"] for r in self._demo_reviews], default=0) + 1
        r_dict = review.to_dict()
        r_dict["review_id"] = new_rid
        self._demo_reviews.append(r_dict)
        return new_rid

    # =========================================================================
    # ANALYTICS OPERATIONS (OLAP Star Schema)
    # =========================================================================
    def get_yoy_performance(self) -> List[Dict[str, Any]]:
        """Year-over-year performance trends and LAG change."""
        if self.is_connected and not self.force_demo_mode:
            try:
                return self._analytics_mgr.get_yoy_performance()
            except Exception:
                pass
        return [
            {
                "review_year": 2021,
                "review_count": 1420,
                "avg_performance": 3.120,
                "avg_job_satisfaction": 2.740,
                "avg_environment_satisfaction": 2.810,
                "avg_work_life_balance": 2.680,
                "yoy_change": None,
            },
            {
                "review_year": 2022,
                "review_count": 2180,
                "avg_performance": 3.245,
                "avg_job_satisfaction": 2.890,
                "avg_environment_satisfaction": 2.950,
                "avg_work_life_balance": 2.730,
                "yoy_change": 0.125,
            },
            {
                "review_year": 2023,
                "review_count": 3410,
                "avg_performance": 3.380,
                "avg_job_satisfaction": 3.110,
                "avg_environment_satisfaction": 3.180,
                "avg_work_life_balance": 2.860,
                "yoy_change": 0.135,
            },
            {
                "review_year": 2024,
                "review_count": 4890,
                "avg_performance": 3.520,
                "avg_job_satisfaction": 3.280,
                "avg_environment_satisfaction": 3.320,
                "avg_work_life_balance": 3.010,
                "yoy_change": 0.140,
            },
            {
                "review_year": 2025,
                "review_count": 6250,
                "avg_performance": 3.610,
                "avg_job_satisfaction": 3.390,
                "avg_environment_satisfaction": 3.450,
                "avg_work_life_balance": 3.140,
                "yoy_change": 0.090,
            },
        ]

    def get_top_performers(
        self, department: Optional[str] = None, top_n: int = 5, year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Leaderboard ranked via SQL window function DENSE_RANK()."""
        if self.is_connected and not self.force_demo_mode:
            try:
                return self._analytics_mgr.get_top_performers(department, top_n, year)
            except Exception:
                pass
        leaderboard = [
            {"employee_id": 101, "first_name": "Aarav", "last_name": "Sharma", "department_name": "Engineering & Technology", "avg_rating": 3.95, "review_count": 4, "dept_rank": 1},
            {"employee_id": 107, "first_name": "Dev", "last_name": "Kapur", "department_name": "Engineering & Technology", "avg_rating": 3.88, "review_count": 3, "dept_rank": 2},
            {"employee_id": 112, "first_name": "Siddharth", "last_name": "Rao", "department_name": "Engineering & Technology", "avg_rating": 3.75, "review_count": 5, "dept_rank": 3},
            {"employee_id": 102, "first_name": "Priya", "last_name": "Patel", "department_name": "Research & Development", "avg_rating": 3.92, "review_count": 4, "dept_rank": 1},
            {"employee_id": 118, "first_name": "Meera", "last_name": "Nair", "department_name": "Research & Development", "avg_rating": 3.82, "review_count": 3, "dept_rank": 2},
            {"employee_id": 105, "first_name": "Vikram", "last_name": "Malhotra", "department_name": "Product & Strategy", "avg_rating": 3.90, "review_count": 4, "dept_rank": 1},
            {"employee_id": 125, "first_name": "Kavita", "last_name": "Iyer", "department_name": "Sales & Business Development", "avg_rating": 3.84, "review_count": 3, "dept_rank": 1},
            {"employee_id": 104, "first_name": "Ananya", "last_name": "Deshmukh", "department_name": "Human Resources", "avg_rating": 3.80, "review_count": 3, "dept_rank": 1},
        ]
        if department:
            leaderboard = [r for r in leaderboard if r["department_name"] == department]
        return [r for r in leaderboard if r["dept_rank"] <= top_n]

    def get_attrition_summary(self, group_by: str = "department") -> List[Dict[str, Any]]:
        """Attrition snapshot by department or job role."""
        if self.is_connected and not self.force_demo_mode:
            try:
                return self._analytics_mgr.get_attrition_summary(group_by)
            except Exception:
                pass
        if group_by == "department":
            return [
                {"grp": "Sales & Business Development", "headcount": 446, "attrited": 92, "attrition_rate_pct": 20.63, "avg_monthly_income": 6950.0},
                {"grp": "Research & Development", "headcount": 961, "attrited": 133, "attrition_rate_pct": 13.84, "avg_monthly_income": 6280.0},
                {"grp": "Human Resources", "headcount": 63, "attrited": 12, "attrition_rate_pct": 19.05, "avg_monthly_income": 6654.0},
                {"grp": "Engineering & Technology", "headcount": 780, "attrited": 82, "attrition_rate_pct": 10.51, "avg_monthly_income": 8420.0},
                {"grp": "Product & Strategy", "headcount": 210, "attrited": 18, "attrition_rate_pct": 8.57, "avg_monthly_income": 9550.0},
            ]
        return [
            {"grp": "Sales Representative", "headcount": 83, "attrited": 33, "attrition_rate_pct": 39.76, "avg_monthly_income": 2626.0},
            {"grp": "Laboratory Technician", "headcount": 259, "attrited": 62, "attrition_rate_pct": 23.94, "avg_monthly_income": 3237.0},
            {"grp": "Human Resources", "headcount": 52, "attrited": 12, "attrition_rate_pct": 23.08, "avg_monthly_income": 4220.0},
            {"grp": "Research Scientist", "headcount": 292, "attrited": 47, "attrition_rate_pct": 16.10, "avg_monthly_income": 4495.0},
            {"grp": "Sales Executive", "headcount": 326, "attrited": 57, "attrition_rate_pct": 17.48, "avg_monthly_income": 6900.0},
            {"grp": "Manufacturing Director", "headcount": 145, "attrited": 10, "attrition_rate_pct": 6.90, "avg_monthly_income": 7280.0},
            {"grp": "Healthcare Representative", "headcount": 131, "attrited": 9, "attrition_rate_pct": 6.87, "avg_monthly_income": 7520.0},
            {"grp": "Manager", "headcount": 102, "attrited": 5, "attrition_rate_pct": 4.90, "avg_monthly_income": 17180.0},
            {"grp": "Research Director", "headcount": 80, "attrited": 2, "attrition_rate_pct": 2.50, "avg_monthly_income": 16030.0},
        ]

    def get_project_bottlenecks(self) -> List[Dict[str, Any]]:
        """Projects ranked by worst work-life balance (Rank 1 = Highest Risk)."""
        if self.is_connected and not self.force_demo_mode:
            try:
                return self._analytics_mgr.get_project_bottlenecks()
            except Exception:
                pass
        return [
            {
                "project_id": 202,
                "project_name": "Phoenix HR Cloud Migration",
                "status": "Active",
                "review_count": 85,
                "employees_reviewed": 28,
                "avg_performance": 3.12,
                "avg_job_satisfaction": 2.10,
                "avg_work_life_balance": 1.95,
                "risk_rank": 1,
            },
            {
                "project_id": 201,
                "project_name": "Project Titan: NextGen AI Engine",
                "status": "Active",
                "review_count": 140,
                "employees_reviewed": 45,
                "avg_performance": 3.65,
                "avg_job_satisfaction": 2.65,
                "avg_work_life_balance": 2.30,
                "risk_rank": 2,
            },
            {
                "project_id": 204,
                "project_name": "Quantum Analytics & BI Portal",
                "status": "Active",
                "review_count": 52,
                "employees_reviewed": 18,
                "avg_performance": 3.42,
                "avg_job_satisfaction": 3.20,
                "avg_work_life_balance": 3.05,
                "risk_rank": 3,
            },
            {
                "project_id": 203,
                "project_name": "Global ERP Consolidation",
                "status": "Completed",
                "review_count": 110,
                "employees_reviewed": 32,
                "avg_performance": 3.78,
                "avg_job_satisfaction": 3.55,
                "avg_work_life_balance": 3.40,
                "risk_rank": 4,
            },
        ]

    def get_employee_history(self, employee_id: int) -> List[Dict[str, Any]]:
        """SCD-2 timeline with salary change computed via SQL LAG()."""
        if self.is_connected and not self.force_demo_mode:
            try:
                return self._analytics_mgr.get_employee_history(employee_id)
            except Exception:
                pass
        versions = [v for v in self._demo_dim_employee if v["employee_id"] == employee_id]
        if not versions:
            # Fallback if brand new or missing
            emp = self.get_employee(employee_id)
            return [
                {
                    "employee_sk": 999,
                    "employee_id": employee_id,
                    "first_name": emp.first_name,
                    "last_name": emp.last_name,
                    "job_role": emp.job_role,
                    "monthly_income": emp.monthly_income,
                    "age": 30,
                    "gender": emp.gender or "Other",
                    "start_date": emp.hire_date,
                    "end_date": None,
                    "is_current": 1,
                    "income_change": 0.0,
                }
            ]
        # Recompute LAG income_change
        sorted_v = sorted(versions, key=lambda x: x["start_date"])
        for i, row in enumerate(sorted_v):
            if i == 0:
                row["income_change"] = 0.0
            else:
                row["income_change"] = row["monthly_income"] - sorted_v[i - 1]["monthly_income"]
        return sorted_v

    # =========================================================================
    # ETL & WAREHOUSE QUALITY OPERATIONS
    # =========================================================================
    def run_full_etl(self, start_year: int = 2015, end_year: Optional[int] = None) -> None:
        if self.is_connected and not self.force_demo_mode:
            self._etl_mgr.run_full_etl(start_year, end_year)
            return
        # Simulated run
        pass

    def run_quality_checks(self) -> Dict[str, int]:
        if self.is_connected and not self.force_demo_mode:
            try:
                return self._etl_mgr.run_quality_checks()
            except Exception:
                pass
        return {
            "overlapping_versions": 0,
            "employees_without_exactly_one_current": 0,
            "inverted_date_ranges": 0,
        }

