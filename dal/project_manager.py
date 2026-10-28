from typing import Optional

from exceptions import DuplicateEntityError, EntityNotFoundError
from models import Assignment, PerformanceReview, Project
from .base_manager import BaseManager


class ProjectManager(BaseManager):
    """Projects, assignments and reviews (OLTP side)."""

    def create_project(self, project: Project) -> int:
        return self._db.execute_query(
            "INSERT INTO Projects (project_name, start_date, end_date, budget, status) "
            "VALUES (%s,%s,%s,%s,%s)",
            (project.project_name, project.start_date, project.end_date,
             project.budget, project.status), self.oltp)

    def get_project(self, project_id: int) -> Project:
        row = self._fetch_one("SELECT * FROM Projects WHERE project_id=%s", (project_id,))
        if not row:
            raise EntityNotFoundError("Project", project_id)
        return Project.from_row(row)

    def list_projects(self, status: Optional[str] = None) -> list[dict]:
        if status:
            return self._fetch_all("SELECT * FROM Projects WHERE status=%s ORDER BY project_id",
                                   (status,))
        return self._fetch_all("SELECT * FROM Projects ORDER BY project_id")

    def assign_employee(self, a: Assignment) -> int:
        """Assign an employee to a project (rejects missing entities and duplicates)."""
        if not self._fetch_one("SELECT 1 AS x FROM Employees WHERE employee_id=%s",
                               (a.employee_id,)):
            raise EntityNotFoundError("Employee", a.employee_id)
        self.get_project(a.project_id)
        if self._fetch_one("SELECT 1 AS x FROM Assignments WHERE employee_id=%s AND project_id=%s",
                           (a.employee_id, a.project_id)):
            raise DuplicateEntityError(
                f"Employee {a.employee_id} is already assigned to project {a.project_id}")
        return self._db.execute_query(
            "INSERT INTO Assignments (employee_id, project_id, role_on_project, assignment_date) "
            "VALUES (%s,%s,%s,%s)",
            (a.employee_id, a.project_id, a.role_on_project, a.assignment_date), self.oltp)

    def list_assignments(self, project_id: Optional[int] = None,
                         employee_id: Optional[int] = None) -> list[dict]:
        sql = ("SELECT a.assignment_id, a.employee_id, CONCAT(e.first_name,' ',e.last_name) "
               "AS employee_name, a.project_id, p.project_name, a.role_on_project, "
               "a.assignment_date FROM Assignments a "
               "JOIN Employees e ON a.employee_id=e.employee_id "
               "JOIN Projects p ON a.project_id=p.project_id WHERE 1=1")
        params: list = []
        if project_id:
            sql += " AND a.project_id=%s"; params.append(project_id)
        if employee_id:
            sql += " AND a.employee_id=%s"; params.append(employee_id)
        return self._fetch_all(sql + " ORDER BY a.assignment_date DESC", params)

    def submit_review(self, r: PerformanceReview) -> int:
        """Insert review into OLTP. Run ETLManager.run_full_etl() to load it into the fact."""
        if not self._fetch_one("SELECT 1 AS x FROM Employees WHERE employee_id=%s",
                               (r.employee_id,)):
            raise EntityNotFoundError("Employee", r.employee_id)
        return self._db.execute_query(
            "INSERT INTO Reviews (employee_id, review_date, performance_rating, job_satisfaction, "
            "environment_satisfaction, work_life_balance) VALUES (%s,%s,%s,%s,%s,%s)",
            (r.employee_id, r.review_date, r.performance_rating, r.job_satisfaction,
             r.environment_satisfaction, r.work_life_balance), self.oltp)