# Small helpers shared by the synthesizer modules.
import re

LEVEL_PREFIX = {1: "Junior", 2: "", 3: "Senior", 4: "Lead", 5: "Principal"}
NO_PREFIX_ROLES = {"Manager", "Research Director", "Manufacturing Director"}  # titles that already imply seniority


def to_snake(name):
    # Converts 'MonthlyIncome' to 'monthly_income'.
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def make_job_title(role, level):
    # Builds a job title like 'Senior Sales Executive' from role and level.
    if role in NO_PREFIX_ROLES:
        return role
    return f"{LEVEL_PREFIX.get(int(level), '')} {role}".strip()


def job_titles(roles, levels):
    # Same as make_job_title but for whole pandas columns at once.
    prefix = levels.map(LEVEL_PREFIX).fillna("")
    titles = (prefix + " " + roles).str.strip()
    return titles.where(~roles.isin(NO_PREFIX_ROLES), roles)
