"""
Data Entry Module (Interacting with OLTP Database).
Implements interactive forms for:
1. Onboarding new employees (Employee model + EmployeeManager.create_employee)
2. Updating department, job role, and salary (Triggers SCD Type 2 in OLAP Star Schema)
3. Creating new projects (Project model + ProjectManager.create_project)
4. Assigning employees to projects (Assignment model + ProjectManager.assign_employee)
5. Submitting performance reviews (PerformanceReview model + ProjectManager.submit_review)
"""
from datetime import date, timedelta
import streamlit as st
import pandas as pd

from frontend.dal_client import DALClient
from frontend.styles import render_scd2_callout
from exceptions import AppError, DuplicateEntityError, EntityNotFoundError, ValidationError, WarehouseSyncError
from models import Assignment, Employee, PerformanceReview, Project

JOB_ROLES = [
    "Research Scientist",
    "Senior Research Scientist",
    "Lead Architect",
    "Software Engineer",
    "Laboratory Technician",
    "Sales Executive",
    "Sales Representative",
    "HR Business Partner",
    "HR Specialist",
    "Director of Product",
    "Manufacturing Director",
    "Healthcare Representative",
    "Manager",
    "Research Director",
]

EDUCATION_LABELS = {
    1: "Level 1 - Below College / Secondary",
    2: "Level 2 - Associate Degree / College",
    3: "Level 3 - Bachelor's Degree",
    4: "Level 4 - Master's Degree",
    5: "Level 5 - Doctorate / PhD",
}


def render_data_entry_module(dal: DALClient):
    st.markdown("### Operational Data Entry (OLTP)")
    st.caption("Manage employee records, project allocations, and evaluations. Updating compensation triggers SCD Type 2 dimension versioning.")

    tab_onboard, tab_scd2, tab_project, tab_review = st.tabs(
        [
            "Employee Onboarding",
            "Position & Compensation (SCD-2)",
            "Project Management",
            "Performance Reviews",
        ]
    )

    
    with tab_onboard:
        st.markdown("#### Onboard New Employee")
        st.caption("Creates an operational record in OLTP and initializes version 1 in Dim_Employee.")

        departments = dal.list_departments()
        dept_options = {d["department_name"]: d["department_id"] for d in departments}

        with st.form("onboard_employee_form", clear_on_submit=False):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Personal Details**")
                first_name = st.text_input("First Name *", placeholder="e.g. Ramesh")
                last_name = st.text_input("Last Name *", placeholder="e.g. Gupta")
                email = st.text_input("Corporate Email *", placeholder="e.g. ramesh.gupta@enterprise.com")
                dob = st.date_input(
                    "Date of Birth *",
                    value=date(1995, 1, 1),
                    min_value=date(1950, 1, 1),
                    max_value=date.today() - timedelta(days=365 * 18),
                )
                gender = st.selectbox("Gender", ["Male", "Female", "Non-Binary", "Prefer not to say"])
                marital = st.selectbox("Marital Status", ["Single", "Married", "Divorced"])

            with col2:
                st.markdown("**Role & Compensation**")
                dept_name = st.selectbox("Department *", list(dept_options.keys()))
                job_role = st.selectbox("Job Role *", JOB_ROLES)
                salary = st.number_input(
                    "Monthly Income (₹) *",
                    min_value=500.0,
                    max_value=500000.0,
                    value=12500.0,
                    step=500.0,
                    help="Monthly gross income between ₹500 and ₹500,000",
                )
                hire_date = st.date_input("Hire Date *", value=date.today(), max_value=date.today())
                distance = st.slider("Commute Distance (KM)", min_value=0, max_value=100, value=8)
                education = st.selectbox("Education Level", [1, 2, 3, 4, 5], format_func=lambda x: EDUCATION_LABELS[x], index=2)

            sync_scd2 = st.checkbox(
                "Synchronize initial dimension version into Star Schema (ETL_Dim_Employee_SCD2)",
                value=True,
            )

            submit_onboard = st.form_submit_button("Complete Onboarding")

        if submit_onboard:
            try:
                emp = Employee(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    hire_date=hire_date,
                    department_id=dept_options[dept_name],
                    job_role=job_role,
                    monthly_income=salary,
                    date_of_birth=dob,
                    gender=gender,
                    marital_status=marital,
                    distance_from_home=distance,
                    education=education,
                )
                new_id = dal.create_employee(emp, sync_warehouse=sync_scd2)
                st.success(f"Employee #{new_id} ({first_name} {last_name}) successfully onboarded.")
                if sync_scd2:
                    st.info(f"SCD Type 2 Initialized: Active record created in Dim_Employee starting {hire_date}.")
            except ValidationError as ve:
                st.error(f"Validation Error: {ve}")
            except DuplicateEntityError as de:
                st.error(f"Duplicate Error: {de}")
            except WarehouseSyncError as we:
                st.warning(f"Saved in OLTP, warehouse sync deferred: {we}")
            except AppError as ae:
                st.error(f"Error: {ae}")

    
    with tab_scd2:
        st.markdown("#### Position Reassignment & Compensation (SCD-2)")
        st.markdown(render_scd2_callout(), unsafe_allow_html=True)

        employees = dal.list_employees(active_only=True, limit=200)
        if not employees:
            st.warning("No active employees found to update.")
        else:
            emp_lookup = {
                f"#{e['employee_id']} - {e['first_name']} {e['last_name']} ({e['job_role']})": e["employee_id"]
                for e in employees
            }
            selected_label = st.selectbox("Select Employee", list(emp_lookup.keys()))
            selected_emp_id = emp_lookup[selected_label]

            emp_obj = dal.get_employee(selected_emp_id)
            current_history = dal.get_employee_history(selected_emp_id)

            col_curr, col_update = st.columns([1, 1.2])

            with col_curr:
                st.markdown("**Current Dimension State**")
                st.markdown(
                    f"""
                    <div style="background: #111827; border: 1px solid #1F2937; border-radius: 6px; padding: 14px;">
                        <div style="font-size: 0.75rem; color: #6B7280;">Employee ID: <b style="color: #F3F4F6;">#{emp_obj.employee_id}</b></div>
                        <div style="font-size: 1rem; font-weight: 600; color: #F9FAFB; margin: 4px 0;">{emp_obj.full_name}</div>
                        <div style="font-size: 0.75rem; color: #6B7280; margin-top: 8px;">Job Role:</div>
                        <div style="font-size: 0.875rem; font-weight: 500; color: #D1D5DB;">{emp_obj.job_role}</div>
                        <div style="font-size: 0.75rem; color: #6B7280; margin-top: 8px;">Monthly Income:</div>
                        <div style="font-size: 1.125rem; font-weight: 600; color: #10B981; font-variant-numeric: tabular-nums;">₹{emp_obj.monthly_income:,.2f}</div>
                        <div style="font-size: 0.75rem; color: #6B7280; margin-top: 8px;">Hire Date:</div>
                        <div style="font-size: 0.8125rem; color: #9CA3AF;">{emp_obj.hire_date}</div>
                        <div style="font-size: 0.75rem; color: #6B7280; margin-top: 8px;">Total SCD-2 Versions:</div>
                        <div style="font-size: 0.8125rem; font-weight: 500; color: #3B82F6;">{len(current_history)} recorded</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col_update:
                st.markdown("**Submit Revised Details**")
                departments = dal.list_departments()
                dept_dict = {d["department_name"]: d["department_id"] for d in departments}

                curr_dept_idx = 0
                for idx, (name, d_id) in enumerate(dept_dict.items()):
                    if d_id == emp_obj.department_id:
                        curr_dept_idx = idx
                        break

                with st.form("scd2_update_form"):
                    new_dept_name = st.selectbox("Department", list(dept_dict.keys()), index=curr_dept_idx)
                    role_idx = JOB_ROLES.index(emp_obj.job_role) if emp_obj.job_role in JOB_ROLES else 0
                    new_job_role = st.selectbox("New Job Role (Tracked)", JOB_ROLES, index=role_idx)
                    new_salary = st.number_input(
                        "New Monthly Income (₹) (Tracked)",
                        min_value=500.0,
                        max_value=500000.0,
                        value=float(emp_obj.monthly_income),
                        step=500.0,
                    )
                    submit_update = st.form_submit_button("Execute SCD-2 Update")

                if submit_update:
                    try:
                        dal.update_employee_position(
                            employee_id=selected_emp_id,
                            department_id=dept_dict[new_dept_name],
                            job_role=new_job_role,
                            monthly_income=new_salary,
                        )
                        st.success(f"SCD Type 2 transaction executed for Employee #{selected_emp_id}.")
                        st.rerun()
                    except ValidationError as ve:
                        st.error(f"Validation Error: {ve}")
                    except WarehouseSyncError as we:
                        st.warning(f"Saved in OLTP, Star Schema sync deferred: {we}")
                    except AppError as ae:
                        st.error(f"Error: {ae}")

            st.markdown("---")
            st.markdown("#### Dim_Employee Version Ledger")
            fresh_history = dal.get_employee_history(selected_emp_id)
            if fresh_history:
                hist_df = pd.DataFrame(fresh_history)
                hist_display = hist_df.copy()
                hist_display["is_current"] = hist_display["is_current"].apply(
                    lambda x: "Active" if x == 1 or x is True else "Historical"
                )
                hist_display["monthly_income"] = hist_display["monthly_income"].apply(lambda v: f"₹{v:,.2f}")
                hist_display["income_change"] = hist_display["income_change"].apply(
                    lambda v: f"₹{v:+,.2f}" if v and v != 0 else "—"
                )
                hist_display["end_date"] = hist_display["end_date"].fillna("Ongoing")
                cols_to_show = [
                    "employee_sk",
                    "job_role",
                    "monthly_income",
                    "income_change",
                    "start_date",
                    "end_date",
                    "is_current",
                ]
                st.dataframe(hist_display[cols_to_show], use_container_width=True, hide_index=True)

    
    with tab_project:
        st.markdown("#### Projects and Allocation")
        col_p1, col_p2 = st.columns(2)

        with col_p1:
            st.markdown("**Register Project**")
            with st.form("create_project_form"):
                p_name = st.text_input("Project Name *", placeholder="e.g. Infrastructure Migration")
                p_start = st.date_input("Start Date *", value=date.today())
                p_end = st.date_input("Estimated End Date", value=date.today() + timedelta(days=180))
                p_budget = st.number_input("Budget (₹)", min_value=0.0, value=2500000.0, step=50000.0)
                p_status = st.selectbox("Status", ["Active", "Planned", "Completed", "On Hold"])
                submit_proj = st.form_submit_button("Create Project")

            if submit_proj:
                try:
                    new_proj = Project(
                        project_name=p_name,
                        start_date=p_start,
                        end_date=p_end,
                        budget=p_budget,
                        status=p_status,
                    )
                    new_pid = dal.create_project(new_proj)
                    st.success(f"Project #{new_pid} '{p_name}' successfully created.")
                except ValidationError as ve:
                    st.error(f"Validation Error: {ve}")
                except AppError as ae:
                    st.error(f"Error: {ae}")

        with col_p2:
            st.markdown("**Assign Team Member**")
            employees = dal.list_employees(active_only=True, limit=200)
            projects = dal.list_projects()

            if not employees or not projects:
                st.info("Requires at least one active employee and project.")
            else:
                emp_map = {f"#{e['employee_id']} {e['first_name']} {e['last_name']}": e["employee_id"] for e in employees}
                proj_map = {f"#{p['project_id']} {p['project_name']}": p["project_id"] for p in projects}

                with st.form("assign_employee_form"):
                    sel_emp = st.selectbox("Team Member", list(emp_map.keys()))
                    sel_proj = st.selectbox("Target Project", list(proj_map.keys()))
                    role_on_proj = st.text_input("Project Role", value="Core Contributor")
                    a_date = st.date_input("Assignment Date", value=date.today())
                    submit_assign = st.form_submit_button("Assign to Project")

                if submit_assign:
                    try:
                        assign = Assignment(
                            employee_id=emp_map[sel_emp],
                            project_id=proj_map[sel_proj],
                            role_on_project=role_on_proj,
                            assignment_date=a_date,
                        )
                        aid = dal.assign_employee(assign)
                        st.success(f"Assignment #{aid} registered.")
                    except DuplicateEntityError:
                        st.error("Employee is already assigned to this project.")
                    except AppError as ae:
                        st.error(f"Error: {ae}")

        st.markdown("---")
        st.markdown("#### Active Enterprise Projects")
        all_projects = dal.list_projects()
        if all_projects:
            df_proj = pd.DataFrame(all_projects)
            st.dataframe(df_proj, use_container_width=True, hide_index=True)

    
    with tab_review:
        st.markdown("#### Performance Evaluation Entry")
        st.caption("Logs assessment scores (1-4 scale) into OLTP. Periodic ETL sync loads these into Fact_PerformanceReviews.")

        employees = dal.list_employees(active_only=True, limit=200)
        if not employees:
            st.warning("No employees available to evaluate.")
        else:
            emp_map = {f"#{e['employee_id']} {e['first_name']} {e['last_name']} ({e['job_role']})": e["employee_id"] for e in employees}

            with st.form("submit_review_form"):
                col_r1, col_r2 = st.columns(2)

                with col_r1:
                    eval_emp = st.selectbox("Employee *", list(emp_map.keys()))
                    eval_date = st.date_input("Review Date *", value=date.today(), max_value=date.today())
                    perf_score = st.select_slider(
                        "Overall Performance Rating (1-4) *",
                        options=[1, 2, 3, 4],
                        value=3,
                        format_func=lambda x: {1: "1 - Low", 2: "2 - Good", 3: "3 - Excellent", 4: "4 - Outstanding"}[x],
                    )

                with col_r2:
                    job_sat = st.select_slider(
                        "Job Satisfaction (1-4) *",
                        options=[1, 2, 3, 4],
                        value=3,
                        format_func=lambda x: {1: "1 - Low", 2: "2 - Medium", 3: "3 - High", 4: "4 - Very High"}[x],
                    )
                    env_sat = st.select_slider(
                        "Environment Satisfaction (1-4) *",
                        options=[1, 2, 3, 4],
                        value=3,
                        format_func=lambda x: {1: "1 - Low", 2: "2 - Medium", 3: "3 - High", 4: "4 - Very High"}[x],
                    )
                    wlb = st.select_slider(
                        "Work-Life Balance (1-4) *",
                        options=[1, 2, 3, 4],
                        value=3,
                        format_func=lambda x: {1: "1 - Bad", 2: "2 - Good", 3: "3 - Better", 4: "4 - Best"}[x],
                    )

                submit_review_btn = st.form_submit_button("Record Evaluation")

            if submit_review_btn:
                try:
                    rev = PerformanceReview(
                        employee_id=emp_map[eval_emp],
                        performance_rating=perf_score,
                        job_satisfaction=job_sat,
                        environment_satisfaction=env_sat,
                        work_life_balance=wlb,
                        review_date=eval_date,
                    )
                    rid = dal.submit_review(rev)
                    st.success(f"Performance Review #{rid} saved into OLTP.")
                except ValidationError as ve:
                    st.error(f"Validation Error: {ve}")
                except AppError as ae:
                    st.error(f"Error: {ae}")
