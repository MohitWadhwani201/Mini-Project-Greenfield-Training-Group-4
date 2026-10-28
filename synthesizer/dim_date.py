# Generates the calendar table (Dim_Date) with one row per day.
import pandas as pd

OPEN_END_KEY = 99991231  


class DimDateGenerator:
   

    def __init__(self, start_year=2010, end_year=2035, fiscal_start_month=4):
        self.start_year = start_year
        self.end_year = end_year
        self.fiscal_start_month = fiscal_start_month 

    def generate(self):
        # Returns the full calendar DataFrame including the open-end row.
        d = pd.date_range(f"{self.start_year}-01-01", f"{self.end_year}-12-31", freq="D")
        s = pd.Series(d)
        fy_shift = (s.dt.month - self.fiscal_start_month) % 12
        fiscal_year = s.dt.year + (s.dt.month >= self.fiscal_start_month).astype(int)
        if self.fiscal_start_month == 1:
            fiscal_year = s.dt.year
        df = pd.DataFrame({
            "date_key": s.dt.strftime("%Y%m%d").astype(int),
            "full_date": s.dt.strftime("%Y-%m-%d"),
            "day_of_month": s.dt.day,
            "day_of_week": s.dt.dayofweek + 1,  # 1 = Monday
            "day_name": s.dt.day_name(),
            "week_of_year": s.dt.isocalendar().week.astype(int),
            "month_number": s.dt.month,
            "month_name": s.dt.month_name(),
            "calendar_quarter": s.dt.quarter,
            "calendar_year": s.dt.year,
            "is_weekend": (s.dt.dayofweek >= 5).astype(int),
            "is_month_end": s.dt.is_month_end.astype(int),
            "fiscal_year": fiscal_year,
            "fiscal_quarter": fy_shift // 3 + 1,
        })
        sentinel = {c: 0 for c in df.columns}
        sentinel.update({"date_key": OPEN_END_KEY, "full_date": "9999-12-31", "day_of_month": 31,
                         "day_of_week": 5, "day_name": "Friday", "week_of_year": 52,
                         "month_number": 12, "month_name": "December", "calendar_quarter": 4,
                         "calendar_year": 9999, "fiscal_year": 9999, "fiscal_quarter": 3})
        return pd.concat([df, pd.DataFrame([sentinel])], ignore_index=True)
