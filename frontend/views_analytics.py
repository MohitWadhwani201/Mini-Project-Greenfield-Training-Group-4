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
from frontend.styles import render_kpi_card, render_kpi_grid


def render_analytics_module(dal: DALClient):
    st.markdown("### Executive Analytics & Warehouse Intelligence (OLAP)")
    st.caption("Star Schema analytical queries powered by SQL window functions (LAG, DENSE_RANK) across dimensions and facts.")

    tab_yoy, tab_leader, tab_risk, tab_scd2_view = st.tabs(
        [
            "Year-over-Year Trends",
            "Department Leaderboards",
            "Attrition & Bottlenecks",
            "SCD-2 Time-Travel Inspector",
        ]
    )

    with tab_yoy:
        st.markdown("#### Performance Trajectory & Momentum (SQL LAG)")
        st.caption("Evaluates multi-year rating trends and delta metrics from Fact_PerformanceReviews.")

        yoy_data = dal.get_yoy_performance()
        if not yoy_data:
            st.info("No historical performance review records found in OLAP.")
        else:
            df_yoy = pd.DataFrame(yoy_data)
            latest = df_yoy.iloc[-1]
            prior = df_yoy.iloc[-2] if len(df_yoy) > 1 else latest

            yoy_delta = latest.get("yoy_change")
            trend_val = f"{yoy_delta:+.3f}" if yoy_delta is not None else "0.000"
            trend_type = "positive" if (yoy_delta or 0) >= 0 else "negative"

            # Dynamic deltas calculated from actual data records
            js_delta = latest.get("avg_job_satisfaction", 0.0) - prior.get("avg_job_satisfaction", 0.0)
            wlb_delta = latest.get("avg_work_life_balance", 0.0) - prior.get("avg_work_life_balance", 0.0)

            c1 = render_kpi_card("Current Avg Rating", f"{latest['avg_performance']:.2f}", trend_val, "vs prior year", trend_type)
            c2 = render_kpi_card("Historical Reviews", f"{int(df_yoy['review_count'].sum()):,}", "", "total records evaluated", "neutral")
            c3 = render_kpi_card("Job Satisfaction", f"{latest.get('avg_job_satisfaction', 0.0):.2f}", f"{js_delta:+.2f}", "vs prior year", "positive" if js_delta >= 0 else "negative")
            c4 = render_kpi_card("Work-Life Balance", f"{latest.get('avg_work_life_balance', 0.0):.2f}", f"{wlb_delta:+.2f}", "vs prior year", "positive" if wlb_delta >= 0 else "negative")
            st.markdown(render_kpi_grid([c1, c2, c3, c4]), unsafe_allow_html=True)

            fig_yoy = create_yoy_performance_chart(yoy_data)
            st.plotly_chart(fig_yoy, use_container_width=True)

            st.markdown("#### Historical Fact Aggregate Table")
            df_display = df_yoy.copy()
            df_display["review_count"] = df_display["review_count"].apply(lambda v: f"{int(v):,}" if pd.notnull(v) else "0")
            df_display["yoy_change"] = df_display["yoy_change"].apply(
                lambda v: f"{v:+.3f}" if pd.notnull(v) and v != 0 else "—"
            )
            st.dataframe(df_display, use_container_width=True, hide_index=True)

    
    with tab_leader:
        st.markdown("#### Top Performers (SQL DENSE_RANK)")
        st.caption("Ranks employees by average review rating partitioned by department using SQL window functions.")

        col_f1, col_f2, col_f3 = st.columns([1.5, 1, 1])
        departments = dal.list_departments()
        dept_names = ["All Departments"] + [d["department_name"] for d in departments]

        with col_f1:
            sel_dept = st.selectbox("Department Filter", dept_names)
            filter_dept = None if sel_dept == "All Departments" else sel_dept
        with col_f2:
            sel_top_n = st.slider("Top N Threshold", min_value=1, max_value=10, value=5)
        with col_f3:
            sel_year = st.selectbox("Evaluation Period", ["All Years", 2025, 2024, 2023, 2022, 2021])
            filter_year = None if sel_year == "All Years" else int(sel_year)

        ranked_data = dal.get_top_performers(department=filter_dept, top_n=sel_top_n, year=filter_year)

        # Truncate to match user's slider limit cleanly
        if ranked_data:
            ranked_data = ranked_data[:sel_top_n]

        if not ranked_data:
            st.warning("No records found matching the filter criteria.")
        else:
            df_ranked = pd.DataFrame(ranked_data)
            top3 = df_ranked.head(3)

            if len(top3) > 0:
                podium_cards = []
                for _, row in top3.iterrows():
                    r = row.get("dept_rank", 1)
                    name = f"{row['first_name']} {row['last_name']}"
                    card = render_kpi_card(
                        f"Rank {r}",
                        f"{float(row['avg_rating']):.2f}",
                        f"{int(row['review_count'])} reviews",
                        f"{name} ({row['department_name']})",
                        "neutral",
                    )
                    podium_cards.append(card)
                
                # Keep grid aligned with 4 cards
                while len(podium_cards) < 4:
                    podium_cards.append(render_kpi_card("Threshold", f"Top {sel_top_n}", "", "Active Filter", "neutral"))
                st.markdown(render_kpi_grid(podium_cards), unsafe_allow_html=True)

            fig_leader = create_leaderboard_chart(ranked_data, top_n=sel_top_n)
            st.plotly_chart(fig_leader, use_container_width=True)

            st.markdown("#### Ranked Performance Ledger")
            display_cols = ["dept_rank", "first_name", "last_name", "department_name", "avg_rating", "review_count"]
            available_cols = [c for c in display_cols if c in df_ranked.columns]
            df_table = df_ranked[available_cols].rename(
                columns={
                    "dept_rank": "Rank",
                    "first_name": "First Name",
                    "last_name": "Last Name",
                    "department_name": "Department",
                    "avg_rating": "Rating",
                    "review_count": "Evaluations",
                }
            )
            st.dataframe(df_table, use_container_width=True, hide_index=True)

    
    with tab_risk:
        st.markdown("#### Attrition Risk & Project Bottlenecks")
        st.caption("Surfaces flight-risk roles, compensation gaps, and projects experiencing critical work-life balance stress.")

        col_dim, _ = st.columns([1, 2])
        with col_dim:
            group_by = st.radio("Group Attrition By:", ["department", "job_role"], horizontal=True)

        attrition_data = dal.get_attrition_summary(group_by=group_by)
        project_bottlenecks = dal.get_project_bottlenecks()

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            fig_att = create_attrition_chart(attrition_data, group_by=group_by.title())
            st.plotly_chart(fig_att, use_container_width=True)
        with col_c2:
            fig_scatter = create_attrition_salary_scatter(attrition_data)
            st.plotly_chart(fig_scatter, use_container_width=True)

        st.markdown("---")
        st.markdown("#### Project Risk & Stress Matrix")
        st.caption("Projects prioritized by lowest work-life balance score (Rank 1 represents the highest risk).")

        fig_proj = create_bottlenecks_matrix_chart(project_bottlenecks)
        st.plotly_chart(fig_proj, use_container_width=True)

        if project_bottlenecks:
            st.markdown("#### Project Health Register")
            df_proj_bn = pd.DataFrame(project_bottlenecks)
            if "risk_rank" in df_proj_bn.columns:
                df_proj_bn["risk_rank"] = df_proj_bn["risk_rank"].apply(lambda r: f"Rank {r}")
            if "avg_work_life_balance" in df_proj_bn.columns:
                df_proj_bn["avg_work_life_balance"] = df_proj_bn["avg_work_life_balance"].apply(lambda v: f"{float(v):.2f}")
            if "avg_job_satisfaction" in df_proj_bn.columns:
                df_proj_bn["avg_job_satisfaction"] = df_proj_bn["avg_job_satisfaction"].apply(lambda v: f"{float(v):.2f}")
            if "avg_performance" in df_proj_bn.columns:
                df_proj_bn["avg_performance"] = df_proj_bn["avg_performance"].apply(lambda v: f"{float(v):.2f}")
            st.dataframe(df_proj_bn, use_container_width=True, hide_index=True)

    
    with tab_scd2_view:
        st.markdown("#### Slowly Changing Dimension (SCD-2) Inspector")
        st.caption("Audit individual career and compensation transitions preserved in Dim_Employee.")

        employees = dal.list_employees(active_only=False, limit=200)
        if not employees:
            st.warning("No employees available to inspect.")
        else:
            # Inline formatted string without line breaks
            emp_choices = {
                f"#{e['employee_id']} {e['first_name']} {e['last_name']} ({e['job_role']})": e["employee_id"]
                for e in employees
            }
            inspect_emp = st.selectbox("Select Employee for Historical Audit", list(emp_choices.keys()))
            emp_id_to_inspect = emp_choices[inspect_emp]

            emp_hist = dal.get_employee_history(emp_id_to_inspect)

            if not emp_hist:
                st.info("No dimension records found for this employee.")
            else:
                fig_timeline = create_scd2_timeline_chart(emp_hist)
                st.plotly_chart(fig_timeline, use_container_width=True)

                st.markdown("#### Star Schema Dim_Employee Audit Ledger")
                df_hist_full = pd.DataFrame(emp_hist)
                df_hist_full["is_current"] = df_hist_full["is_current"].apply(
                    lambda v: "Active" if v == 1 or v is True else "Historical"
                )
                df_hist_full["monthly_income"] = df_hist_full["monthly_income"].apply(
                    lambda v: f"₹{float(v):,.2f}" if pd.notnull(v) else "₹0.00"
                )
                df_hist_full["income_change"] = df_hist_full["income_change"].apply(
                    lambda v: f"₹{float(v):+,.2f}" if pd.notnull(v) and float(v) != 0 else "—"
                )
                df_hist_full["end_date"] = df_hist_full["end_date"].fillna("Ongoing")

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
                available_hist_cols = [c for c in cols if c in df_hist_full.columns]
                st.dataframe(df_hist_full[available_hist_cols], use_container_width=True, hide_index=True)