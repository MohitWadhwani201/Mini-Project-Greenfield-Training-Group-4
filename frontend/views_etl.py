"""
Data Warehouse Operations & ETL Console.
Provides warehouse orchestration, quality assurance health monitoring,
and architecture transparency for Phases 1-3 pipelines.
"""
from datetime import date
import streamlit as st

from frontend.dal_client import DALClient
from frontend.styles import get_kpi_card_html
from exceptions import DatabaseOperationError


def render_etl_module(dal: DALClient):
    st.markdown("## ⚙️ Data Warehouse Orchestration & ETL Health Console")
    st.caption("Inspect and manage the data pipeline moving records from staging and OLTP into the OLAP Star Schema.")

    tab_ops, tab_quality, tab_arch = st.tabs(
        [
            "⚡ Trigger Warehouse ETL",
            "🛡️ Data Quality & Integrity Checks",
            "🏛️ Star Schema Architecture",
        ]
    )

    with tab_ops:
        st.markdown("### ⚡ Execute Full Warehouse ETL Pipeline")
        st.caption(
            "Executes stored procedures in documented dependency order: `Populate_Dim_Date` ➔ `ETL_Load_Simple_Dimensions` ➔ `ETL_Dim_Employee_SCD2` ➔ `ETL_Fact_PerformanceReviews`."
        )

        col_p1, col_p2 = st.columns([1, 2])
        with col_p1:
            st.markdown(
                """
                <div style="background: #1E293B; border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 18px;">
                    <div style="font-size: 13px; font-weight: 700; color: #38BDF8; margin-bottom: 8px;">ETL EXECUTION ORDER</div>
                    <ol style="font-size: 12px; color: #94A3B8; padding-left: 18px; line-height: 1.8; margin: 0;">
                        <li><code>Populate_Dim_Date</code> (2015 to Target)</li>
                        <li><code>ETL_Load_Simple_Dimensions</code> (Type 1 overwrite)</li>
                        <li><code>ETL_Dim_Employee_SCD2</code> (Type 2 history)</li>
                        <li><code>ETL_Fact_PerformanceReviews</code> (Fact loading)</li>
                    </ol>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_p2:
            st.markdown("##### Pipeline Configuration")
            start_yr = st.number_input("Start Year for Date Dimension", min_value=2000, max_value=2030, value=2015)
            end_yr = st.number_input("End Year for Date Dimension", min_value=2020, max_value=2040, value=date.today().year + 2)

            run_etl_btn = st.button("🚀 Trigger Full Warehouse Synchronization", type="primary")

            if run_etl_btn:
                with st.spinner("Executing warehouse ETL procedures..."):
                    try:
                        dal.run_full_etl(start_year=start_yr, end_year=end_yr)
                        st.success("🎉 **Warehouse Synchronization completed successfully!** All dimensions and facts refreshed.")
                    except DatabaseOperationError as doe:
                        st.error(f"❌ ETL Execution Failed: {doe}")
                    except Exception as e:
                        st.error(f"❌ Unexpected Error during ETL: {e}")

    
    with tab_quality:
        st.markdown("### 🛡️ Warehouse Quality & Dimension Integrity Checks")
        st.caption("Runs automated SQL consistency validations on `Dim_Employee` and Star Schema integrity.")

        col_q1, col_q2 = st.columns([1, 3])
        with col_q1:
            check_now = st.button("🔍 Run Quality Audit Now", type="secondary")

        checks = dal.run_quality_checks()

        overlaps = checks.get("overlapping_versions", 0)
        multi_curr = checks.get("employees_without_exactly_one_current", 0)
        inverted = checks.get("inverted_date_ranges", 0)
        all_passed = (overlaps == 0) and (multi_curr == 0) and (inverted == 0)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            theme = "emerald" if overlaps == 0 else "rose"
            st.markdown(
                get_kpi_card_html("Overlapping Versions", str(overlaps), "Must be 0", theme),
                unsafe_allow_html=True,
            )
        with col2:
            theme = "emerald" if multi_curr == 0 else "rose"
            st.markdown(
                get_kpi_card_html("Multi/Zero Current", str(multi_curr), "Must be 0", theme),
                unsafe_allow_html=True,
            )
        with col3:
            theme = "emerald" if inverted == 0 else "rose"
            st.markdown(
                get_kpi_card_html("Inverted Date Ranges", str(inverted), "start_date > end_date", theme),
                unsafe_allow_html=True,
            )
        with col4:
            health_score = "100% HEALTHY" if all_passed else "ATTENTION NEEDED"
            health_theme = "emerald" if all_passed else "rose"
            st.markdown(
                get_kpi_card_html("Warehouse Health", health_score, "Dimension SCD-2 status", health_theme),
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        if all_passed:
            st.markdown(
                """
                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 8px; padding: 14px 18px; color: #34D399; font-size: 14px;">
                    ✅ <b>All SCD-2 Quality Audits Passed:</b> Every employee has exactly one active version, no date ranges overlap, and historical continuity is 100% preserved.
                </div>
                """,
                unsafe_allow_html=True,
            )


    with tab_arch:
        st.markdown("### 🏛️ Star Schema & SCD Type 2 Architecture Reference")
        st.markdown(
            """
            ```
            ┌────────────────────────────────┐
            │   GreenFieldMiniProject_OLTP   │
            │ ────────────────────────────── │
            │ • Employees                    │
            │ • Departments                  │
            │ • Projects                     │
            │ • Assignments                  │
            │ • Reviews                      │
            └────────────────┬───────────────┘
                             │
                             ▼  (ETL Procedures / Python DAL)
            ┌────────────────────────────────────────────────────────┐
            │               GreenFieldMiniProject_OLAP               │
            │ ────────────────────────────────────────────────────── │
            │                                                        │
            │   Dim_Department (SCD-1)      Dim_Project (SCD-1)      │
            │         │                             │                │
            │         └──────────────┐ ┌────────────┘                │
            │                        ▼ ▼                             │
            │          Fact_PerformanceReviews (Periodic Snapshot)   │
            │                        ▲ ▲                             │
            │         ┌──────────────┘ └────────────┐                │
            │         │                             │                │
            │   Dim_Date (Static)         Dim_Employee (SCD-2)       │
            │   • date_id (YYYYMMDD)      • employee_sk (Surrogate)  │
            │                             • start_date & end_date    │
            │                             • is_current flag          │
            └────────────────────────────────────────────────────────┘
            ```
            """
        )
        st.markdown(
            """
            **SCD Type 2 Specification:**
            - **Tracked Columns:** `job_role` and `monthly_income`.
            - **Close Condition:** When changes occur in OLTP, the active record (`is_current = TRUE`) in `Dim_Employee` has its `end_date` set to `CURRENT_DATE() - 1` and `is_current = FALSE`.
            - **Open Condition:** A new row is inserted with `start_date = CURRENT_DATE()`, `end_date = NULL`, and `is_current = TRUE`.
            - **Fact Preservation:** All reviews logged prior to the update retain foreign keys pointing to the historical `employee_sk`, guaranteeing audit accuracy.
            """
        )

