from typing import Optional

from exceptions import EntityNotFoundError, ValidationError
from models import Assignment, PerformanceReview, Project
from .base_manager import BaseManager


class ProjectManager(BaseManager):
    """Projects, assignments and performance reviews (OLTP side)."""

    def create_project(self, project: Project) -> int:
        return self._db.execute_query(
            "INSERT INTO projects (project_name, start_date, end_date, status) "
            "VALUES (%s,%s,%s,%s)",
            (project.project_name, project.start_date, project.end_date,
             project.status), self.oltp)

    def get_project(self, project_id: int) -> Project:
        row = self._fetch_one("SELECT * FROM projects WHERE project_id=%s", (project_id,))
        if not row:
            raise EntityNotFoundError("Project", project_id)
        return Project.from_row(row)

    def list_projects(self, status: Optional[str] = None) -> list[dict]:
        if status:
            return self._fetch_all("SELECT * FROM projects WHERE status=%s", (status,))
        return self._fetch_all("SELECT * FROM projects ORDER BY project_id")

    def assign_employee(self, a: Assignment) -> int:
        """Assign with allocation check: employee total allocation must stay <= 100%."""
        with self._db.transaction(self.oltp) as cur:
            cur.execute("SELECT COALESCE(SUM(allocation_pct),0) AS total "
                        "FROM project_assignments WHERE employee_id=%s FOR UPDATE",
                        (a.employee_id,))
            total = float(cur.fetchone()["total"])
            if total + a.allocation_pct > 100:
                raise ValidationError(
                    f"Employee {a.employee_id} would be allocated {total + a.allocation_pct}% (>100%)")
            cur.execute("INSERT INTO project_assignments (employee_id, project_id, "
                        "allocation_pct, role, assigned_date) VALUES (%s,%s,%s,%s,%s)",
                        (a.employee_id, a.project_id, a.allocation_pct, a.role,
                         a.assigned_date))
            return cur.lastrowid

    def list_assignments(self, project_id: Optional[int] = None,
                         employee_id: Optional[int] = None) -> list[dict]:
        sql, params = "SELECT * FROM project_assignments WHERE 1=1", []
        if project_id:
            sql += " AND project_id=%s"; params.append(project_id)
        if employee_id:
            sql += " AND employee_id=%s"; params.append(employee_id)
        return self._fetch_all(sql, params)

    def submit_review(self, r: PerformanceReview) -> int:
        return self._db.execute_query(
            "INSERT INTO performance_reviews (employee_id, review_date, rating, "
            "performance_score, comments) VALUES (%s,%s,%s,%s,%s)",
            (r.employee_id, r.review_date, r.rating, r.performance_score, r.comments),
            self.oltp)
