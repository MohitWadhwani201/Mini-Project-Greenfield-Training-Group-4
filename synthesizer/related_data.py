import logging

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

CODENAMES = ["Atlas", "Orion", "Nimbus", "Helios", "Vertex", "Zenith", "Aurora", "Titan",
             "Nova", "Pioneer", "Falcon", "Summit", "Horizon", "Catalyst", "Quantum", "Ember"]
DOMAINS = ["Platform", "Migration", "Analytics", "Portal", "Automation", "Onboarding",
           "Compliance", "Outreach", "Optimization", "Integration"]
PROJECT_ROLES = ["Developer", "Analyst", "Team Lead", "QA Specialist", "Coordinator", "Consultant"]


class RelatedDataSynthesizer:

    def __init__(self, employees, reference_date, seed=42, n_projects=150):
        self.emp = employees.reset_index(drop=True)
        self.ref = pd.Timestamp(reference_date).normalize()
        self.rng = np.random.default_rng(seed + 2)
        self.seed = seed
        self.n_projects = n_projects

    def generate_projects(self):
        rng, ref = self.rng, self.ref
        depts = sorted(self.emp["department"].unique())
        share = self.emp["department"].value_counts(normalize=True).reindex(depts)
        counts = np.maximum(10, np.round(self.n_projects * share)).astype(int)
        owners = np.repeat(depts, counts.to_numpy())
        n = len(owners)

        start = pd.Series(ref - pd.to_timedelta(rng.integers(60, 7 * 365, n), unit="D"))
        planned = start + pd.to_timedelta(rng.integers(120, 900, n), unit="D")
        done = (planned <= ref).to_numpy()
        actual = (planned + pd.to_timedelta(rng.integers(-30, 60, n), unit="D")).clip(upper=ref).where(done)
        status = np.where(done, "Completed", np.where(rng.random(n) < 0.1, "On Hold", "Active"))

        df = pd.DataFrame({
            "project_name": pd.Series(rng.choice(CODENAMES, n)) + " " + pd.Series(rng.choice(DOMAINS, n)),
            "owning_department": owners,
            "start_date": start.dt.normalize(),
            "planned_end_date": planned.dt.normalize(),
            "actual_end_date": actual.dt.normalize(),
            "status": status,
            "budget": np.round(rng.lognormal(12.5, 0.6, n), -3).astype(int),
        })
        df = df.sample(frac=1, random_state=self.seed).reset_index(drop=True)
        df.insert(0, "project_id", np.arange(1, n + 1))
        df.insert(1, "project_code", "PRJ-" + df["project_id"].astype(str).str.zfill(4))
        log.info("Projects: %d", len(df))
        return df

    def generate_assignments(self, projects):
        # Gives each employee 1-2 projects of their department; dates fall inside the 5-year review window.
        rng, ref, emp = self.rng, self.ref, self.emp
        floor = ref - pd.DateOffset(years=5)
        last_day = emp["termination_date"].fillna(ref)
        window_start = emp["hire_date"].where(emp["hire_date"] > floor, floor).to_numpy()
        span_days = (last_day - pd.Series(window_start, index=emp.index)).dt.days.clip(lower=1).to_numpy()

        parts = []
        for dept, g in emp.groupby("department"):
            idx = g.index.to_numpy()
            m = len(idx)
            dp = projects[projects["owning_department"] == dept].sort_values("start_date")
            starts, pids = dp["start_date"].to_numpy(), dp["project_id"].to_numpy()

            # first project early in the window, second one later
            d1 = window_start[idx] + (span_days[idx] * rng.beta(1, 4, m)).astype("int64").astype("timedelta64[D]")
            d2 = window_start[idx] + (span_days[idx] * (0.5 + 0.5 * rng.random(m))).astype("int64").astype("timedelta64[D]")
            first = self._pick_project(starts, pids, d1)
            second = self._pick_project(starts, pids, d2)
            has2 = (rng.random(m) < 0.5) & (second != -1) & (first != -1) & (second != first)
            alloc1 = np.where(has2, rng.choice([50, 60, 70], m), 100)
            ids = g["employee_id"].to_numpy()
            ok1 = first != -1
            parts.append(pd.DataFrame({"employee_id": ids[ok1], "project_id": first[ok1],
                                       "allocation_pct": alloc1[ok1], "assigned_date": d1[ok1]}))
            parts.append(pd.DataFrame({"employee_id": ids[has2], "project_id": second[has2],
                                       "allocation_pct": 100 - alloc1[has2], "assigned_date": d2[has2]}))
        a = pd.concat(parts, ignore_index=True)
        a["assigned_date"] = pd.to_datetime(a["assigned_date"]).dt.normalize()
        a["role_on_project"] = rng.choice(PROJECT_ROLES, len(a))
        a = a.sort_values(["employee_id", "assigned_date"]).reset_index(drop=True)
        a.insert(0, "assignment_id", np.arange(1, len(a) + 1))
        log.info("Assignments: %d", len(a))
        return a[["assignment_id", "employee_id", "project_id", "role_on_project",
                  "allocation_pct", "assigned_date"]]

    def _pick_project(self, starts, pids, dates):
        # For each date, picks a random project that had already started by then (-1 if none had).
        available = np.searchsorted(starts, dates, side="right")
        choice = np.minimum((self.rng.random(len(dates)) * available).astype(int), max(len(pids) - 1, 0))
        return np.where(available > 0, pids[choice], -1)

    def generate_reviews(self, years_back=5):
        # Creates yearly reviews (last 5 years) with the same columns as the OLTP Reviews table.
        rng, emp, ref_year = self.rng, self.emp, self.ref.year
        n = len(emp)
        active = emp["is_active"].to_numpy().astype(bool)
        hire_year = emp["hire_date"].dt.year.to_numpy()
        term_year = emp["termination_date"].dt.year.fillna(ref_year + 1).to_numpy().astype(int)

        first_year = np.maximum(hire_year + 1, ref_year - years_back)
        last_year = np.where(active, ref_year - 1, np.minimum(term_year - 1, ref_year - 1))
        counts = np.clip(last_year - first_year + 1, 0, None)

        total = int(counts.sum())
        emp_idx = np.repeat(np.arange(n), counts)
        offsets = np.arange(total) - np.repeat(np.cumsum(counts) - counts, counts)
        years = first_year[emp_idx] + offsets

        review_date = (pd.to_datetime(pd.Series(years).astype(str) + "-11-15")
                       + pd.to_timedelta(rng.integers(0, 31, total), unit="D"))
        rev = pd.DataFrame({
            "employee_id": emp["employee_id"].to_numpy()[emp_idx],
            "review_date": review_date,
        })
        # Scores use the IBM 1-4 scale, staying close to the employee's own values
        noise = rng.choice([-2, -1, 0, 1], total, p=[0.03, 0.17, 0.60, 0.20])
        rev["performance_rating"] = np.clip(emp["performance_rating"].to_numpy()[emp_idx] + noise, 1, 4)
        for col in ("job_satisfaction", "environment_satisfaction", "work_life_balance"):
            noise = rng.choice([-1, 0, 0, 1], total)
            rev[col] = np.clip(emp[col].to_numpy()[emp_idx] + noise, 1, 4)

        rev = rev.sort_values(["employee_id", "review_date"]).reset_index(drop=True)
        rev.insert(0, "review_id", np.arange(1, len(rev) + 1))
        log.info("Reviews: %d", len(rev))
        return rev[["review_id", "employee_id", "review_date", "performance_rating",
                    "job_satisfaction", "environment_satisfaction", "work_life_balance"]]
