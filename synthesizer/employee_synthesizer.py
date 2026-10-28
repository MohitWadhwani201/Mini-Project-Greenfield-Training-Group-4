# Scales the 1,470-row IBM HR dataset up to 100,000+ realistic employees.
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

from .common import job_titles, to_snake

log = logging.getLogger(__name__)

EMPLOYEE_COLUMNS = [
    "employee_id", "source", "first_name", "last_name", "full_name", "gender",
    "email", "date_of_birth", "age", "marital_status", "education",
    "education_field", "city", "department", "job_role", "job_title",
    "job_level", "monthly_income", "daily_rate", "hourly_rate", "monthly_rate",
    "percent_salary_hike", "performance_rating", "business_travel", "over_time",
    "distance_from_home", "num_companies_worked", "total_working_years",
    "training_times_last_year", "years_at_company", "years_in_current_role",
    "years_since_last_promotion", "years_with_curr_manager",
    "stock_option_level", "job_involvement", "job_satisfaction",
    "environment_satisfaction", "relationship_satisfaction", "work_life_balance",
    "attrition", "hire_date", "termination_date", "is_active",
]

REQUIRED_IBM_COLUMNS = [
    "age", "attrition", "business_travel", "daily_rate", "department",
    "distance_from_home", "education", "education_field",
    "environment_satisfaction", "gender", "hourly_rate", "job_involvement",
    "job_level", "job_role", "job_satisfaction", "marital_status",
    "monthly_income", "monthly_rate", "num_companies_worked", "over_time",
    "percent_salary_hike", "performance_rating", "relationship_satisfaction",
    "stock_option_level", "total_working_years", "training_times_last_year",
    "work_life_balance", "years_at_company", "years_in_current_role",
    "years_since_last_promotion", "years_with_curr_manager",
]
SATISFACTION_COLS = [
    "environment_satisfaction", "job_involvement", "job_satisfaction",
    "relationship_satisfaction", "work_life_balance",
]
CONSTANT_IBM_COLUMNS = ["employee_count", "employee_number", "over18", "standard_hours"]  # useless columns


class EmployeeSynthesizer:
    # Loads the IBM data and scales it with pandas, numpy and Faker.

    def __init__(self, base_csv, target_rows=100000, reference_date=None, seed=42, locale="en_IN"):
        self.base_csv = Path(base_csv)
        self.target_rows = target_rows
        self.reference_date = pd.Timestamp(reference_date).normalize()
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        Faker.seed(seed)
        self.fake = Faker(locale)

    def load_base(self):
        # Reads the IBM CSV, checks its columns and drops the useless ones.
        if not self.base_csv.exists():
            raise FileNotFoundError(
                f"IBM dataset not found at {self.base_csv}. Download "
                "'WA_Fn-UseC_-HR-Employee-Attrition.csv' from Kaggle and place it there."
            )
        df = pd.read_csv(self.base_csv, encoding="utf-8-sig")
        df.columns = [to_snake(c) for c in df.columns]
        missing = [c for c in REQUIRED_IBM_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Base CSV is missing expected IBM columns: {missing}")
        df = df.drop(columns=[c for c in CONSTANT_IBM_COLUMNS if c in df.columns])
        df = df.dropna(subset=REQUIRED_IBM_COLUMNS).drop_duplicates().reset_index(drop=True)
        log.info("Loaded %d base rows from %s", len(df), self.base_csv.name)
        return df

    def scale(self):
        # Main method: returns the full employee table with target_rows rows.
        base = self.load_base()
        n = self.target_rows
        if n <= len(base):
            df = base.sample(n=n, random_state=self.seed).copy()
            df["source"] = "IBM_ORIGINAL"
        else:
            donors = self.rng.integers(0, len(base), size=n - len(base))
            clones = self._jitter(base.iloc[donors].copy().reset_index(drop=True), base)
            original = base.copy()
            original["source"] = "IBM_ORIGINAL"
            clones["source"] = "SYNTHETIC"
            df = pd.concat([original, clones], ignore_index=True)

        df = df.iloc[self.rng.permutation(len(df))].reset_index(drop=True)
        df.insert(0, "employee_id", np.arange(1, len(df) + 1))
        df = self._enforce_consistency(df)
        df = self._add_identity(df)
        df = self._add_dates(df)
        df["job_title"] = job_titles(df["job_role"], df["job_level"])
        log.info("Scaled to %d employees", len(df))
        return df[EMPLOYEE_COLUMNS]

    def _jitter(self, c, base):
        # Slightly changes cloned rows so they are similar to, but not copies of, the originals.
        rng, m = self.rng, len(c)
        c["age"] = (c["age"] + rng.integers(-4, 5, m)).clip(18, 60)
        c["monthly_income"] = (
            (c["monthly_income"] * rng.lognormal(0, 0.10, m)).round().clip(1009, 19999).astype(int)
        )
        c["monthly_rate"] = (
            (c["monthly_rate"] * rng.lognormal(0, 0.05, m)).round().clip(2094, 26999).astype(int)
        )
        c["daily_rate"] = (c["daily_rate"] + rng.integers(-100, 101, m)).clip(100, 1500)
        c["hourly_rate"] = (c["hourly_rate"] + rng.integers(-8, 9, m)).clip(30, 100)
        c["distance_from_home"] = (c["distance_from_home"] + rng.integers(-2, 3, m)).clip(1, 29)
        c["total_working_years"] = (c["total_working_years"] + rng.integers(-2, 3, m)).clip(0, 40)
        c["years_at_company"] = (c["years_at_company"] + rng.integers(-1, 2, m)).clip(0, 40)
        c["percent_salary_hike"] = (c["percent_salary_hike"] + rng.integers(-1, 2, m)).clip(11, 25)
        c["training_times_last_year"] = (c["training_times_last_year"] + rng.integers(-1, 2, m)).clip(0, 6)
        c["num_companies_worked"] = (c["num_companies_worked"] + rng.integers(-1, 2, m)).clip(0, 9)
        for col in SATISFACTION_COLS: 
            mask = rng.random(m) < 0.15
            c.loc[mask, col] = rng.choice(base[col].to_numpy(), int(mask.sum()))
        return c

    @staticmethod
    def _enforce_consistency(df):
        # Keeps tenure columns logical (e.g. years at company never exceeds total working years).
        df["total_working_years"] = np.minimum(df["total_working_years"], (df["age"] - 18).clip(lower=0))
        df["years_at_company"] = np.minimum(df["years_at_company"], df["total_working_years"])
        for col in ("years_in_current_role", "years_since_last_promotion", "years_with_curr_manager"):
            df[col] = np.minimum(df[col], df["years_at_company"])
        int_cols = df.select_dtypes(include="number").columns
        df[int_cols] = df[int_cols].astype(int)
        return df

    def _pool(self, factory, size):
        # Builds a sorted list of unique fake values (sorted so results are reproducible).
        return np.array(sorted({factory() for _ in range(size)}))

    def _add_identity(self, df):
        # Adds Faker-generated names, email and city.
        rng, m = self.rng, len(df)
        male = self._pool(self.fake.first_name_male, 3000)
        female = self._pool(self.fake.first_name_female, 3000)
        last = self._pool(self.fake.last_name, 4000)
        cities = self._pool(self.fake.city, 150)

        is_male = df["gender"].eq("Male").to_numpy()
        df["first_name"] = np.where(is_male, rng.choice(male, m), rng.choice(female, m))
        df["last_name"] = rng.choice(last, m)
        df["full_name"] = df["first_name"] + " " + df["last_name"]
        clean_f = df["first_name"].str.lower().str.replace(r"[^a-z]", "", regex=True)
        clean_l = df["last_name"].str.lower().str.replace(r"[^a-z]", "", regex=True)
        df["email"] = clean_f + "." + clean_l + "." + df["employee_id"].astype(str) + "@greenfield-corp.com"
        df["city"] = rng.choice(cities, m)
        return df

    def _add_dates(self, df):
        # Creates hire, termination and birth dates that match years_at_company and attrition.
        rng, m, ref = self.rng, len(df), self.reference_date
        active = df["attrition"].eq("No")
        term = pd.Series(ref - pd.to_timedelta(rng.integers(30, 3 * 365, m), unit="D"), index=df.index)
        anchor = term.where(~active, ref)  # leavers count back from exit date, active from today
        tenure_days = df["years_at_company"].to_numpy() * 365 + rng.integers(0, 365, m)
        df["hire_date"] = (anchor - pd.to_timedelta(tenure_days, unit="D")).dt.normalize()
        df["termination_date"] = term.where(~active).dt.normalize()
        df["is_active"] = active.astype(int)
        dob_days = df["age"].to_numpy() * 365.25 + rng.integers(0, 365, m)
        df["date_of_birth"] = pd.Series(ref - pd.to_timedelta(dob_days, unit="D"), index=df.index).dt.normalize()
        return df
