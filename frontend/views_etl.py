"""
Data Warehouse Operations & ETL Console.
Provides warehouse orchestration, quality assurance health monitoring,
and architecture transparency for Phases 1-3 pipelines.
"""
from datetime import date
import streamlit as st

from frontend.dal_client import DALClient
from frontend.styles import render_kpi_card, render_kpi_grid
from exceptions import DatabaseOperationError


def render_etl_module(dal: DALClient):
    st.markdown("### Warehouse Operations & Quality Assurance")
    st.caption("Orchestrate ETL stored procedures and validate Star Schema dimensional integrity.")

    tab_ops, tab_quality, tab_arch = st.tabs(
        [
            "Pipeline Synchronization",
            "Dimension Integrity Checks",
            "Star Schema Architecture",
        ]
    )

    with tab_ops:
        st.markdown("#### Execute Warehouse Pipeline")
        st.caption(
            "Runs stored procedures in documented dependency order: Populate_Dim_Date -> ETL_Load_Simple_Dimensions -> ETL_Dim_Employee_SCD2 -> ETL_Fact_PerformanceReviews."
        )

        col_p1, col_p2 = st.columns([1, 2])
        with col_p1:
            st.markdown(
                """
                <div style="background: #111827; border: 1px solid #1F2937; border-radius: 6px; padding: 14px;">
                    <div style="font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: #9CA3AF; margin-bottom: 6px;">Pipeline Sequence</div>
                    <ol style="font-size: 0.75rem; color: #D1D5DB; padding-left: 16px; line-height: 1.8; margin: 0;">
                        <li><code>Populate_Dim_Date</code></li>
                        <li><code>ETL_Load_Simple_Dimensions</code></li>
                        <li><code>ETL_Dim_Employee_SCD2</code></li>
                        <li><code>ETL_Fact_PerformanceReviews</code></li>
                    </ol>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_p2:
            st.markdown("**Configuration**")
            start_yr = st.number_input("Start Year for Date Dimension", min_value=2000, max_value=2030, value=2015)
            end_yr = st.number_input("End Year for Date Dimension", min_value=2020, max_value=2040, value=date.today().year + 2)

            run_etl_btn = st.button("Trigger Warehouse Synchronization")

            if run_etl_btn:
                with st.spinner("Executing warehouse ETL procedures..."):
                    try:
                        dal.run_full_etl(start_year=start_yr, end_year=end_yr)
                        st.success("Warehouse Synchronization completed successfully.")
                    except DatabaseOperationError as doe:
                        st.error(f"ETL Execution Failed: {doe}")
                    except Exception as e:
                        st.error(f"Unexpected Error during ETL: {e}")

    
    with tab_quality:
        st.markdown("#### Dimension Integrity & Consistency Checks")
        st.caption("Automated SQL validation verifying Dim_Employee SCD Type 2 state constraints.")

        checks = dal.run_quality_checks()

        overlaps = checks.get("overlapping_versions", 0)
        multi_curr = checks.get("employees_without_exactly_one_current", 0)
        inverted = checks.get("inverted_date_ranges", 0)
        all_passed = (overlaps == 0) and (multi_curr == 0) and (inverted == 0)

        c1 = render_kpi_card("Overlapping Versions", str(overlaps), "Pass" if overlaps == 0 else "Fail", "Must be 0", "positive" if overlaps == 0 else "negative")
        c2 = render_kpi_card("Current Flag Errors", str(multi_curr), "Pass" if multi_curr == 0 else "Fail", "Must be 0", "positive" if multi_curr == 0 else "negative")
        c3 = render_kpi_card("Inverted Date Ranges", str(inverted), "Pass" if inverted == 0 else "Fail", "start_date > end_date", "positive" if inverted == 0 else "negative")
        c4 = render_kpi_card("Integrity Status", "100%" if all_passed else "Action Required", "", "Dimensional health", "positive" if all_passed else "negative")

        st.markdown(render_kpi_grid([c1, c2, c3, c4]), unsafe_allow_html=True)

        if all_passed:
            st.markdown(
                """
                <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 6px; padding: 12px 16px; color: #34D399; font-size: 0.8125rem;">
                    All quality checks passed: Each employee maintains exactly one active dimension version, no historical validity windows overlap, and chronological order is preserved.
                </div>
                """,
                unsafe_allow_html=True,
            )


    with tab_arch:
        st.markdown("#### Dimensional Star Schema Architecture")
        st.markdown(
            """
            ```
            [ OLTP Layer: GreenFieldMiniProject_OLTP ]
            • Employees | Departments | Projects | Assignments | Reviews
                                |
                                v  (ETL Procedures / Python DAL)
            [ OLAP Star Schema: GreenFieldMiniProject_OLAP ]
            
            Dim_Department (SCD-1)           Dim_Project (SCD-1)
                   \                                /
                    v                              v
                  [ Fact_PerformanceReviews (Periodic Snapshot) ]
                    ^                              ^
                   /                                \
            Dim_Date (Static)                Dim_Employee (SCD-2)
            • date_id (YYYYMMDD)             • employee_sk (Surrogate Key)
                                             • start_date & end_date
                                             • is_current flag
            ```
            """
        )
        st.markdown(
            """
            **SCD Type 2 Implementation Summary:**
            - **Tracked Attributes**: `job_role` and `monthly_income`.
            - **Retiring Prior Version**: Sets `is_current = FALSE` and `end_date = CURRENT_DATE() - 1`.
            - **Generating New Version**: Inserts new record with `is_current = TRUE`, `start_date = CURRENT_DATE()`, and `end_date = NULL`.
            - **Audit Fidelity**: Historic performance reviews remain anchored to the surrogate key `employee_sk` active at the time of review.
            """
        )
