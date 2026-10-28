# Builds SCD Type 2 history: one row per employee version (salary hike, promotion, department transfer).
import logging
from collections import Counter
from datetime import timedelta

import numpy as np
import pandas as pd

from .common import make_job_title

log = logging.getLogger(__name__)

SENTINEL = "9999-12-31"  # end_date of the current (open) version
HISTORY_COLUMNS = [
    "history_id", "employee_id", "version_no", "department", "job_role",
    "job_title", "job_level", "monthly_income", "start_date", "end_date",
    "is_current", "change_type",
]


class SCD2HistoryGenerator:
    # Walks backwards from each employee's current state so the newest version always matches it.
    CHANGE_WEIGHTS = {"SALARY_HIKE": 0.5, "PROMOTION": 0.3, "DEPT_TRANSFER": 0.2}
    MIN_DAYS_PER_CHANGE = 150 

    def __init__(self, employees, reference_date, change_fraction=0.25, seed=42):
        self.emp = employees.reset_index(drop=True)
        self.ref = pd.Timestamp(reference_date).normalize()
        self.change_fraction = change_fraction
        self.rng = np.random.default_rng(seed + 1)
        self.dept_roles = {d: sorted(g["job_role"].unique()) for d, g in self.emp.groupby("department")}
        self.stats = Counter()

    def generate(self):
        # Main method: returns the history table (every employee has at least one row).
        emp, rng = self.emp, self.rng
        last_day = emp["termination_date"].fillna(self.ref)
        tenure_days = (last_day - emp["hire_date"]).dt.days
        eligible = (tenure_days >= 360).to_numpy() 
        share = eligible.mean() if len(emp) else 0
        p = min(1.0, self.change_fraction / share) if share > 0 else 0.0
        chosen = (rng.random(len(emp)) < p) & eligible

        rows = []
        iterator = zip(
            emp["employee_id"], emp["department"], emp["job_role"], emp["job_level"],
            emp["monthly_income"], emp["hire_date"], last_day, emp["is_active"], chosen,
        )
        for eid, dept, role, level, income, hire, last, active, do_change in iterator:
            hire_d, last_d, active = hire.date(), last.date(), bool(active)
            current = {"department": dept, "job_role": role, "job_level": int(level), "monthly_income": int(income)}
            states, events, change_dates = [current], [], []

            if do_change:
                lo, hi = hire_d + timedelta(days=180), last_d - timedelta(days=30)
                span = (hi - lo).days
                k = min(int(rng.choice([1, 2, 3], p=[0.5, 0.35, 0.15])), span // self.MIN_DAYS_PER_CHANGE)
                slice_len = span / k
                change_dates = [
                    lo + timedelta(days=int(i * slice_len + slice_len * rng.uniform(0.2, 0.8)))
                    for i in range(k)
                ]
                cur = current
                for _ in range(k):  
                    prev, event = self._invert(cur)
                    states.append(prev)
                    events.append(event)
                    cur = prev
                states.reverse()  
                events.reverse()
                self.stats.update(events)

            k = len(change_dates)
            for i, st in enumerate(states):
                start = hire_d if i == 0 else change_dates[i - 1]
                if i < k:
                    end, is_cur = (change_dates[i] - timedelta(days=1)).isoformat(), 0
                elif active:
                    end, is_cur = SENTINEL, 1
                else:
                    end, is_cur = last_d.isoformat(), 0
                rows.append({
                    "employee_id": int(eid), "version_no": i + 1,
                    "department": st["department"], "job_role": st["job_role"],
                    "job_title": make_job_title(st["job_role"], st["job_level"]),
                    "job_level": st["job_level"], "monthly_income": st["monthly_income"],
                    "start_date": start.isoformat(), "end_date": end, "is_current": is_cur,
                    "change_type": "HIRE" if i == 0 else events[i - 1],
                })

        hist = pd.DataFrame(rows)
        hist.insert(0, "history_id", np.arange(1, len(hist) + 1))
        log.info(
            "History: %d version rows for %d employees (%d with changes); events: %s",
            len(hist), len(emp), int(chosen.sum()), dict(self.stats),
        )
        return hist[HISTORY_COLUMNS]

    def _invert(self, state):
        # Returns the state BEFORE a random change, plus the type of that change.
        rng = self.rng
        event = rng.choice(list(self.CHANGE_WEIGHTS), p=list(self.CHANGE_WEIGHTS.values()))
        prev = dict(state)
        others = [d for d in self.dept_roles if d != state["department"]]

        if event == "PROMOTION" and state["job_level"] >= 2:
            prev["job_level"] = state["job_level"] - 1
            prev["monthly_income"] = max(1000, round(state["monthly_income"] / rng.uniform(1.10, 1.25)))
        elif event == "DEPT_TRANSFER" and others:
            prev["department"] = str(rng.choice(others))
            prev["job_role"] = str(rng.choice(self.dept_roles[prev["department"]]))
        else:  
            event = "SALARY_HIKE"
            prev["monthly_income"] = max(1000, round(state["monthly_income"] / rng.uniform(1.03, 1.12)))
        return prev, str(event)
