import logging

import pandas as pd

from .history_generator import SENTINEL

log = logging.getLogger(__name__)


class DataQualityValidator:

    def __init__(self, employees, history, projects, assignments, reviews, dim_date, min_rows=100000):
        self.emp = employees
        self.hist = history
        self.proj = projects
        self.asg = assignments
        self.rev = reviews
        self.dd = dim_date
        self.min_rows = min_rows

    def run(self):
        checks = [
            self._volume, self._unique_ids, self._one_current_per_active, self._no_current_for_leavers,
            self._contiguous_versions, self._start_before_end, self._first_version_is_hire,
            self._latest_version_matches_snapshot, self._allocation_cap, self._no_orphans,
            self._review_scores_valid,
            self._dim_date_ok,
        ]
        results = [c() for c in checks]
        for name, passed, detail in results:
            (log.info if passed else log.error)("%s  %s  %s", "PASS" if passed else "FAIL", name, detail)
        return results

    def _volume(self):
        # Checks that we generated at least the target number of employees.
        n = len(self.emp)
        return ("employee volume >= target", n >= self.min_rows, f"{n:,} employees")

    def _unique_ids(self):
        # Checks employee_id and history_id have no duplicates.
        ok = self.emp["employee_id"].is_unique and self.hist["history_id"].is_unique
        return ("employee_id / history_id unique", ok, "")

    def _one_current_per_active(self):
        # Every active employee must have exactly one is_current = 1 row.
        cur = self.hist[self.hist["is_current"] == 1].groupby("employee_id").size()
        active_ids = set(self.emp.loc[self.emp["is_active"] == 1, "employee_id"])
        bad = [e for e in active_ids if cur.get(e, 0) != 1]
        return ("exactly one is_current=1 per active employee", not bad, f"{len(bad)} violations")

    def _no_current_for_leavers(self):
        # Employees who left must have no is_current = 1 row.
        leavers = set(self.emp.loc[self.emp["is_active"] == 0, "employee_id"])
        bad = self.hist[(self.hist["employee_id"].isin(leavers)) & (self.hist["is_current"] == 1)]
        return ("no is_current=1 for terminated employees", bad.empty, f"{len(bad)} violations")

    def _contiguous_versions(self):
        # Each version must start the day after the previous one ends (no overlaps or gaps).
        h = self.hist.sort_values(["employee_id", "start_date"]).copy()
        h["start_dt"] = pd.to_datetime(h["start_date"])
        h["end_dt"] = pd.to_datetime(h["end_date"].where(h["end_date"] != SENTINEL))
        h["next_start"] = h.groupby("employee_id")["start_dt"].shift(-1)
        has_next = h["next_start"].notna()
        bad = h[has_next & ((h["end_dt"] + pd.Timedelta(days=1)) != h["next_start"])]
        return ("no overlaps / gaps between versions", bad.empty, f"{len(bad)} violations")

    def _start_before_end(self):
        # start_date must never be after end_date.
        closed = self.hist[self.hist["end_date"] != SENTINEL]
        bad = closed[closed["start_date"] > closed["end_date"]]
        return ("start_date <= end_date", bad.empty, f"{len(bad)} violations")

    def _first_version_is_hire(self):
        # The first version of every employee must start on their hire date.
        first = self.hist.sort_values(["employee_id", "start_date"]).groupby("employee_id").first()
        hire = self.emp.set_index("employee_id")["hire_date"].dt.strftime("%Y-%m-%d")
        bad = (first["start_date"] != hire.reindex(first.index)).sum()
        return ("first version starts on hire_date", bad == 0, f"{bad} violations")

    def _latest_version_matches_snapshot(self):
        # The newest version must equal the employee's current record.
        last = self.hist.sort_values(["employee_id", "start_date"]).groupby("employee_id").last()
        snap = self.emp.set_index("employee_id").reindex(last.index)
        cols = ["department", "job_role", "job_level", "monthly_income"]
        bad = int((last[cols].to_numpy() != snap[cols].to_numpy()).any(axis=1).sum())
        return ("latest version == current employee snapshot", bad == 0, f"{bad} violations")

    def _allocation_cap(self):
        # Total project allocation per employee must not exceed 100%.
        tot = self.asg.groupby("employee_id")["allocation_pct"].sum()
        bad = int((tot > 100).sum())
        return ("project allocation <= 100% per employee", bad == 0, f"{bad} violations")

    def _no_orphans(self):
        # Every foreign key must point to an existing employee or project.
        emp_ids = set(self.emp["employee_id"])
        bad = (
            (~self.hist["employee_id"].isin(emp_ids)).sum()
            + (~self.asg["employee_id"].isin(emp_ids)).sum()
            + (~self.rev["employee_id"].isin(emp_ids)).sum()
            + (~self.asg["project_id"].isin(set(self.proj["project_id"]))).sum()
        )
        return ("no orphan foreign keys", bad == 0, f"{int(bad)} violations")

    def _review_scores_valid(self):
        # Review ratings and satisfaction scores must stay on the 1-4 IBM scale.
        cols = ["performance_rating", "job_satisfaction", "environment_satisfaction", "work_life_balance"]
        bad = int(((self.rev[cols] < 1) | (self.rev[cols] > 4)).any(axis=1).sum())
        return ("review scores within 1-4", bad == 0, f"{bad} violations")

    def _dim_date_ok(self):
        # dim_date must have unique keys and no missing days.
        d = self.dd[self.dd["date_key"] != 99991231]
        full = pd.date_range(d["full_date"].min(), d["full_date"].max(), freq="D")
        ok = d["date_key"].is_unique and len(full) == len(d)
        return ("dim_date unique & contiguous", ok, f"{len(d):,} days")
