# TEST HELPER ONLY: builds a small fake CSV with IBM's columns so tests run offline (not the real dataset).
import sys
from pathlib import Path

import numpy as np
import pandas as pd

COLUMNS = ["Age", "Attrition", "BusinessTravel", "DailyRate", "Department", "DistanceFromHome",
           "Education", "EducationField", "EmployeeCount", "EmployeeNumber", "EnvironmentSatisfaction",
           "Gender", "HourlyRate", "JobInvolvement", "JobLevel", "JobRole", "JobSatisfaction",
           "MaritalStatus", "MonthlyIncome", "MonthlyRate", "NumCompaniesWorked", "Over18", "OverTime",
           "PercentSalaryHike", "PerformanceRating", "RelationshipSatisfaction", "StandardHours",
           "StockOptionLevel", "TotalWorkingYears", "TrainingTimesLastYear", "WorkLifeBalance",
           "YearsAtCompany", "YearsInCurrentRole", "YearsSinceLastPromotion", "YearsWithCurrManager"]
ROLES = {"Research & Development": ["Research Scientist", "Laboratory Technician", "Manufacturing Director",
                                     "Healthcare Representative", "Research Director", "Manager"],
         "Sales": ["Sales Executive", "Sales Representative", "Manager"],
         "Human Resources": ["Human Resources", "Manager"]}


def make(path, n=1470, seed=7):
    # Writes a mock IBM-shaped CSV to the given path.
    r = np.random.default_rng(seed)
    dept = r.choice(list(ROLES), n, p=[0.65, 0.30, 0.05])
    role = [r.choice(ROLES[d]) for d in dept]
    level = r.choice([1, 2, 3, 4, 5], n, p=[0.37, 0.36, 0.15, 0.07, 0.05])
    age = np.clip(r.normal(37, 9, n), 18, 60).astype(int)
    twy = np.clip(age - 18 - r.integers(0, 12, n), 0, 40)
    yac = np.minimum(np.clip(r.gamma(2, 3, n).astype(int), 0, 40), twy)
    df = pd.DataFrame({
        "Age": age, "Attrition": r.choice(["Yes", "No"], n, p=[0.16, 0.84]),
        "BusinessTravel": r.choice(["Travel_Rarely", "Travel_Frequently", "Non-Travel"], n, p=[0.7, 0.19, 0.11]),
        "DailyRate": r.integers(102, 1499, n), "Department": dept, "DistanceFromHome": r.integers(1, 29, n),
        "Education": r.integers(1, 6, n),
        "EducationField": r.choice(["Life Sciences", "Medical", "Marketing", "Technical Degree", "Other"], n),
        "EmployeeCount": 1, "EmployeeNumber": np.arange(1, n + 1),
        "EnvironmentSatisfaction": r.integers(1, 5, n), "Gender": r.choice(["Male", "Female"], n, p=[0.6, 0.4]),
        "HourlyRate": r.integers(30, 100, n), "JobInvolvement": r.integers(1, 5, n), "JobLevel": level,
        "JobRole": role, "JobSatisfaction": r.integers(1, 5, n),
        "MaritalStatus": r.choice(["Single", "Married", "Divorced"], n),
        "MonthlyIncome": np.clip(np.array([2800, 5500, 9800, 15000, 19000])[level - 1] * r.lognormal(0, .2, n), 1009, 19999).astype(int),
        "MonthlyRate": r.integers(2094, 26999, n), "NumCompaniesWorked": r.integers(0, 9, n), "Over18": "Y",
        "OverTime": r.choice(["Yes", "No"], n, p=[0.28, 0.72]), "PercentSalaryHike": r.integers(11, 25, n),
        "PerformanceRating": r.choice([3, 4], n, p=[0.85, 0.15]), "RelationshipSatisfaction": r.integers(1, 5, n),
        "StandardHours": 80, "StockOptionLevel": r.integers(0, 4, n), "TotalWorkingYears": twy,
        "TrainingTimesLastYear": r.integers(0, 7, n), "WorkLifeBalance": r.integers(1, 5, n),
        "YearsAtCompany": yac, "YearsInCurrentRole": np.minimum(yac, r.integers(0, 10, n)),
        "YearsSinceLastPromotion": np.minimum(yac, r.integers(0, 8, n)),
        "YearsWithCurrManager": np.minimum(yac, r.integers(0, 10, n)),
    })[COLUMNS]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


if __name__ == "__main__":
    make(sys.argv[1] if len(sys.argv) > 1 else "data/raw/mock_ibm.csv")
