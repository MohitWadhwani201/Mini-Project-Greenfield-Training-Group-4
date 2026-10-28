"""
Main Streamlit Application Entry Point.
Enterprise HR Analytics & Data Warehouse System (Phases 4 & 5).
"""
import sys
from pathlib import Path

# Add project root to sys.path to guarantee clean module resolution
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd

from frontend.dal_client import DALClient
from frontend.styles import (
    DARK_THEME_CSS,
    get_header_html,
    get_kpi_card_html,
)
from frontend.views_data_entry import render_data_entry_module
from frontend.views_analytics import render_analytics_module
from frontend.views_etl import render_etl_module

# Configure page layout and browser metadata
st.set_page_config(
    page_title="Enterprise HR Analytics & Warehouse",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject Enterprise Cyber Dark CSS
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)


def main():
    # Initialize singleton DAL Client
    dal = DALClient.get_instance()

    # -------------------------------------------------------------------------
    # SIDEBAR: SYSTEM CONTROLS & NAVIGATION
    # -------------------------------------------------------------------------
    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 10px 0 16px 0; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 16px;">
                <div style="font-size: 11px; font-weight: 700; color: #38BDF8; letter-spacing: 1.5px; text-transform: uppercase;">PLATFORM CONSOLE</div>
                <div style="font-size: 19px; font-weight: 800; color: #F8FAFC; margin-top: 4px;">HR WAREHOUSE</div>
                <div style="font-size: 12px; color: #94A3B8;">Phase 4 & 5 UI & Dashboards</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("##### 🧭 Navigation")
        nav_choice = st.radio(
            "Select Module",
            [
                "📊 Executive Overview",
                "📝 HR Operations (OLTP Data Entry)",
                "📈 Executive Analytics (OLAP Star Schema)",
                "⚙️ Warehouse & ETL Console",
            ],
            label_visibility="collapsed",
        )

        st.markdown("---")
        st.markdown("##### 🔌 Database Connectivity")

        # Live vs Demo mode selector
        use_demo = st.toggle("Force Sandbox / Demo Mode", value=dal.force_demo_mode or not dal.is_connected)
        dal.force_demo_mode = use_demo

        col_st1, col_st2 = st.columns([2, 1])
        with col_st1:
            if dal.is_connected and not dal.force_demo_mode:
                st.markdown('<span class="status-pill pill-active">● Live MySQL (Connected)</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="status-pill pill-warning">⚠ Sandbox Demo Mode</span>', unsafe_allow_html=True)

        with col_st2:
            if st.button("🔄 Ping", help="Re-probe database connection"):
                dal.ping()
                st.rerun()

        if dal.connection_error and not dal.force_demo_mode:
            st.caption(f"Connection Note: {dal.connection_error[:100]}...")

        st.markdown("---")
        st.markdown(
            """
            <div style="font-size: 11px; color: #64748B; line-height: 1.6;">
                <b>Stack:</b> Streamlit &bull; Plotly &bull; MySQL OLTP/OLAP &bull; SCD Type 2 &bull; Python DAL<br>
                <b>Specification:</b> Greenfield Enterprise HR System
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -------------------------------------------------------------------------
    # MAIN VIEW HEADER
    # -------------------------------------------------------------------------
    db_mode = "Live MySQL OLTP/OLAP" if dal.is_connected and not dal.force_demo_mode else "Interactive Sandbox Mode"
    st.markdown(get_header_html(connected=(dal.is_connected and not dal.force_demo_mode), db_mode=db_mode), unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # MODULE ROUTING
    # -------------------------------------------------------------------------
    if nav_choice == "📊 Executive Overview":
        render_overview_module(dal)
    elif nav_choice == "📝 HR Operations (OLTP Data Entry)":
        render_data_entry_module(dal)
    elif nav_choice == "📈 Executive Analytics (OLAP Star Schema)":
        render_analytics_module(dal)
    elif nav_choice == "⚙️ Warehouse & ETL Console":
        render_etl_module(dal)


def render_overview_module(dal: DALClient):
    """Landing dashboard presenting key enterprise indicators."""
    st.markdown("## 📊 Executive Overview & Workforce Pulse")
    st.caption("Real-time operational summary bridging transactional OLTP headcount with analytical OLAP aggregations.")

    employees = dal.list_employees(active_only=False, limit=500)
    departments = dal.list_departments()
    projects = dal.list_projects()
    yoy_data = dal.get_yoy_performance()

    active_emp = [e for e in employees if e.get("is_active") == 1]
    attrited_emp = [e for e in employees if e.get("is_active") == 0]
    total_hc = len(employees)
    attrition_rate = (len(attrited_emp) / total_hc * 100) if total_hc > 0 else 0.0

    avg_sal = sum([e.get("monthly_income", 0.0) for e in active_emp]) / len(active_emp) if active_emp else 0.0
    latest_perf = yoy_data[-1]["avg_performance"] if yoy_data else 3.5

    # High Level Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            get_kpi_card_html("Active Workforce", f"{len(active_emp):,}", f"Out of {total_hc:,} Total Hired", "emerald"),
            unsafe_allow_html=True,
        )
    with col2:
        theme = "emerald" if attrition_rate < 15.0 else "rose"
        st.markdown(
            get_kpi_card_html("Attrition Rate", f"{attrition_rate:.1f}%", f"{len(attrited_emp)} Attrited Employees", theme),
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            get_kpi_card_html("Avg Monthly Income", f"₹{avg_sal:,.0f}", "Active cohort compensation", "sky"),
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            get_kpi_card_html("Performance Rating", f"{latest_perf:.2f} ★", "OLAP Star Schema Fact Avg", "purple"),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Summary Cards
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown("### 🏢 Department Distribution")
        dept_summary = dal.get_attrition_summary(group_by="department")
        if dept_summary:
            df_dept = pd.DataFrame(dept_summary)
            df_display = df_dept.rename(
                columns={
                    "grp": "Department",
                    "headcount": "Headcount",
                    "attrited": "Attrition",
                    "attrition_rate_pct": "Attrition %",
                    "avg_monthly_income": "Avg Monthly Salary (₹)",
                }
            )
            df_display["Avg Monthly Salary (₹)"] = df_display["Avg Monthly Salary (₹)"].apply(lambda v: f"₹{v:,.2f}")
            df_display["Attrition %"] = df_display["Attrition %"].apply(lambda v: f"{v:.1f}%")
            st.dataframe(df_display, use_container_width=True, hide_index=True)

    with col_right:
        st.markdown("### 🚀 Strategic Projects")
        if projects:
            df_p = pd.DataFrame(projects)
            st.dataframe(
                df_p[["project_name", "status", "budget"]].rename(
                    columns={"project_name": "Project", "status": "Status", "budget": "Budget (₹)"}
                ),
                use_container_width=True,
                hide_index=True,
            )

    st.markdown("---")
    st.markdown("### ⚡ Quick Navigation & Core Features")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown(
            """
            <div class="glass-panel">
                <div class="glass-panel-title">📝 Data Entry (OLTP)</div>
                <p style="font-size: 13px; color: #94A3B8; margin-top: 8px;">
                    Onboard new staff, register projects, assign roles, and log reviews with full model validation.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            """
            <div class="glass-panel">
                <div class="glass-panel-title">🔄 SCD Type 2 Engine</div>
                <p style="font-size: 13px; color: #94A3B8; margin-top: 8px;">
                    Promote staff or update salaries; watch the system close previous versions and open new ones live.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_c:
        st.markdown(
            """
            <div class="glass-panel">
                <div class="glass-panel-title">📈 Star Schema Analytics</div>
                <p style="font-size: 13px; color: #94A3B8; margin-top: 8px;">
                    Explore YoY trends via LAG, leaderboard podiums via DENSE_RANK, and flight-risk matrix.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()

