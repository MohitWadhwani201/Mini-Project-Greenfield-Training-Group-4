"""
Analytics Dashboard Module (Interacting with OLAP Star Schema).
Implements executive dashboards querying star schema dimensions and fact tables:
1. Year-Over-Year (YoY) Performance Trends (SQL LAG() window function)
2. Top Performers Leaderboard (SQL DENSE_RANK() window function)
3. Attrition Risk & Project Bottlenecks (Stress and compensation matrix)
4. SCD-2 Historical Time-Travel Inspector (Audit timeline and salary evolution)
"""
from typing import Optional
import streamlit as st
import pandas as pd

from frontend.dal_client import DALClient
from frontend.charts import (
    create_yoy_performance_chart,
    create_leaderboard_chart,
    create_attrition_chart,
    create_attrition_salary_scatter,
    create_bottlenecks_matrix_chart,
    create_scd2_timeline_chart,
)
from frontend.styles import get_kpi_card_html


def render_analytics_module(dal: DALClient):
    st.markdown("## 📊 Executive Analytics & Data Warehouse Insights (OLAP)")
    st.caption("Deep historical intelligence synthesized across dimensions and facts in the star schema using advanced SQL window functions.")

    tab_yoy, tab_leader, tab_risk, tab_scd2_view = st.tabs(
        [
            "📈 YoY Performance Trends",
            "🏆 Top Performers Leaderboard",
            "⚠️ Attrition Risk & Bottlenecks",
            "🕰️ SCD-2 Time-Travel Inspector",
        ]
    )

    with tab_yoy:
        st.markdown("### 📈 Year-Over-Year Performance Trajectory")
        st.caption("Aggregates annual reviews and calculates year-over-year momentum using the SQL `LAG()` window function.")

        yoy_data = dal.get_yoy_performance()
        if not yoy_data:
            st.info("No historical performance review records found in OLAP.")
        else:
            df_yoy = pd.DataFrame(yoy_data)
            latest = df_yoy.iloc[-1]
            prev = df_yoy.iloc[-2] if len(df_yoy) > 1 else latest

            yoy_delta = latest.get("yoy_change")
            delta_str = f"{yoy_delta:+.3f} vs prev year" if yoy_delta is not None else "Baseline Year"

            # Executive KPI Row
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(
                    get_kpi_card_html("Latest Performance", f"{latest['avg_performance']:.2f} ★", delta_str, "sky"),
                    unsafe_allow_html=True,
                )
            with col2:
                st.markdown(
                    get_kpi_card_html("Total Evaluations", f"{df_yoy['review_count'].sum():,}", "Across all years", "purple"),
                    unsafe_allow_html=True,
                )
            with col3:
                sat_val = latest.get("avg_job_satisfaction", 0.0)
                st.markdown(
                    get_kpi_card_html("Job Satisfaction", f"{sat_val:.2f} / 4.0", "Latest cohort score", "emerald"),
                    unsafe_allow_html=True,
                )
            with col4:
                wlb_val = latest.get("avg_work_life_balance", 0.0)
                st.markdown(
                    get_kpi_card_html("Work-Life Balance", f"{wlb_val:.2f} / 4.0", "Company-wide metric", "amber"),
                    unsafe_allow_html=True,
                )

            st.markdown("<br>", unsafe_allow_html=True)

            # Interactive Plotly Chart
            fig_yoy = create_yoy_performance_chart(yoy_data)
            st.plotly_chart(fig_yoy, use_container_width=True)

            # Detailed Yearly Table
            st.markdown("##### 📋 Historical Fact Performance Ledger")
            df_display = df_yoy.copy()
            df_display["review_count"] = df_display["review_count"].apply(lambda v: f"{v:,}")
            df_display["yoy_change"] = df_display["yoy_change"].apply(
                lambda v: f"{v:+.3f}" if pd.notnull(v) and v != 0 else "—"
            )
            st.dataframe(df_display, use_container_width=True, hide_index=True)

    
    with tab_leader:
        st.markdown("### 🏆 Top Performers Leaderboard (SQL DENSE_RANK)")
        st.caption("Ranks employees by average review rating partitioned by department using SQL `DENSE_RANK() OVER (PARTITION BY department_name ORDER BY avg_rating DESC)`.")

        # Leaderboard Filters
        col_f1, col_f2, col_f3 = st.columns([1.5, 1, 1])
        departments = dal.list_departments()
        dept_names = ["All Departments"] + [d["department_name"] for d in departments]

        with col_f1:
            sel_dept = st.selectbox("Filter Department", dept_names)
            filter_dept = None if sel_dept == "All Departments" else sel_dept
        with col_f2:
            sel_top_n = st.slider("Top N Ranks", min_value=1, max_value=10, value=5)
        with col_f3:
            sel_year = st.selectbox("Evaluation Year", ["All Years", 2025, 2024, 2023, 2022, 2021])
            filter_year = None if sel_year == "All Years" else int(sel_year)

        ranked_data = dal.get_top_performers(department=filter_dept, top_n=sel_top_n, year=filter_year)

        if not ranked_data:
            st.warning("No performers found matching the specified filter criteria.")
        else:
            # Highlight Top 3 Podium
            df_ranked = pd.DataFrame(ranked_data)
            top3 = df_ranked[df_ranked["dept_rank"] <= 3].head(3)

            if len(top3) > 0:
                st.markdown("##### 🥇 Top Performers Podium")
                podium_cols = st.columns(min(3, len(top3)))
                medals = ["🥇 1st Place", "🥈 2nd Place", "🥉 3rd Place"]
                themes = ["amber", "sky", "emerald"]

                for i, (_, row) in enumerate(top3.iterrows()):
                    with podium_cols[i]:
                        name = f"{row['first_name']} {row['last_name']}"
                        sub = f"{row['department_name']} &bull; {row['review_count']} reviews"
                        st.markdown(
                            get_kpi_card_html(medals[i], f"{row['avg_rating']:.2f} ★", f"{name}<br>{sub}", themes[i]),
                            unsafe_allow_html=True,
                        )

            st.markdown("<br>", unsafe_allow_html=True)
            # Plotly Leaderboard Chart
            fig_leader = create_leaderboard_chart(ranked_data, top_n=sel_top_n)
            st.plotly_chart(fig_leader, use_container_width=True)

            # Leaderboard Table
            st.markdown("##### 🏅 Full Ranked Leaderboard Table")
            display_cols = ["dept_rank", "first_name", "last_name", "department_name", "avg_rating", "review_count"]
            df_table = df_ranked[display_cols].rename(
                columns={
                    "dept_rank": "Rank #",
                    "first_name": "First Name",
                    "last_name": "Last Name",
                    "department_name": "Department",
                    "avg_rating": "Avg Rating",
                    "review_count": "Evaluations Evaluated",
                }
            )
            st.dataframe(df_table, use_container_width=True, hide_index=True)

    
    with tab_risk:
        st.markdown("### ⚠️ Attrition Risk & Project Bottlenecks")
        st.caption("Surfaces flight-risk roles, compensation gaps, and projects experiencing critical work-life balance stress.")

        col_dim, _ = st.columns([1, 2])
        with col_dim:
            group_by = st.radio("Aggregate Attrition By:", ["department", "job_role"], horizontal=True)

        attrition_data = dal.get_attrition_summary(group_by=group_by)
        project_bottlenecks = dal.get_project_bottlenecks()

        # Attrition Section
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            fig_att = create_attrition_chart(attrition_data, group_by=group_by.title())
            st.plotly_chart(fig_att, use_container_width=True)
        with col_c2:
            fig_scatter = create_attrition_salary_scatter(attrition_data)
            st.plotly_chart(fig_scatter, use_container_width=True)

        st.markdown("---")
        st.markdown("### 🚨 Project Stress & Bottleneck Risk Matrix")
        st.caption("Projects prioritized by lowest work-life balance score (`risk_rank = 1` indicates highest risk of burnout / delivery delay).")

        fig_proj = create_bottlenecks_matrix_chart(project_bottlenecks)
        st.plotly_chart(fig_proj, use_container_width=True)

        # Bottlenecks Table
        st.markdown("##### 📌 Ranked Project Health Register")
        if project_bottlenecks:
            df_proj_bn = pd.DataFrame(project_bottlenecks)
            df_proj_bn["risk_rank"] = df_proj_bn["risk_rank"].apply(
                lambda r: f"🚨 CRITICAL (Rank #{r})" if r == 1 else f"⚠️ ATTENTION (Rank #{r})" if r == 2 else f"✅ STABLE (Rank #{r})"
            )
            df_proj_bn["avg_work_life_balance"] = df_proj_bn["avg_work_life_balance"].apply(lambda v: f"{v:.2f} / 4.0")
            df_proj_bn["avg_job_satisfaction"] = df_proj_bn["avg_job_satisfaction"].apply(lambda v: f"{v:.2f} / 4.0")
            df_proj_bn["avg_performance"] = df_proj_bn["avg_performance"].apply(lambda v: f"{v:.2f} / 4.0")
            st.dataframe(df_proj_bn, use_container_width=True, hide_index=True)

    
    with tab_scd2_view:
        st.markdown("### 🕰️ Slowly Changing Dimension (SCD-2) Time-Travel Inspector")
        st.caption("Audit how employee roles, compensation, and career trajectories evolved over time without losing historical fidelity.")

        employees = dal.list_employees(active_only=False, limit=200)
        if not employees:
            st.warning("No employees available to inspect.")
        else:
            emp_choices = {
                f"#{e['employee_id']} - {e['first_name']} {e['last_name']} ({e['job_role']})": e["employee_id"]
                for e in employees
            }
            inspect_emp = st.selectbox("Select Employee for Historical Time-Travel Audit", list(emp_choices.keys()))
            emp_id_to_inspect = emp_choices[inspect_emp]

            emp_hist = dal.get_employee_history(emp_id_to_inspect)

            if not emp_hist:
                st.info("No dimension records found for this employee.")
            else:
                # Render Timeline Chart
                fig_timeline = create_scd2_timeline_chart(emp_hist)
                st.plotly_chart(fig_timeline, use_container_width=True)

                # Version Details Table
                st.markdown("##### 📑 Star Schema `Dim_Employee` Version Audit Trail")
                df_hist_full = pd.DataFrame(emp_hist)
                df_hist_full["is_current"] = df_hist_full["is_current"].apply(
                    lambda v: "🟢 ACTIVE (Current Version)" if v == 1 or v is True else "🔴 INACTIVE (Historical)"
                )
                df_hist_full["monthly_income"] = df_hist_full["monthly_income"].apply(lambda v: f"₹{v:,.2f}")
                df_hist_full["income_change"] = df_hist_full["income_change"].apply(
                    lambda v: f"₹{v:+,.2f}" if v and v != 0 else "—"
                )
                df_hist_full["end_date"] = df_hist_full["end_date"].fillna("Ongoing / Active")

                cols = [
                    "employee_sk",
                    "employee_id",
                    "job_role",
                    "monthly_income",
                    "income_change",
                    "start_date",
                    "end_date",
                    "is_current",
                ]
                st.dataframe(df_hist_full[cols], use_container_width=True, hide_index=True)

