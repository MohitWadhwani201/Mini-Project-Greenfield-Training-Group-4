"""
Main Streamlit Application Entry Point.
Enterprise SaaS HR Analytics & Data Warehouse Platform (Phases 4 & 5).
Styled with a bespoke Linear / Datadog / Vercel design system.
"""
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd

from frontend.dal_client import DALClient
from frontend.styles import (
    DARK_THEME_CSS,
    SVG_DASHBOARD,
    SVG_OPERATIONS,
    SVG_ANALYTICS,
    SVG_WAREHOUSE,
    render_top_navbar,
    render_kpi_card,
    render_kpi_grid,
)
from frontend.views_data_entry import render_data_entry_module
from frontend.views_analytics import render_analytics_module
from frontend.views_etl import render_etl_module

# Page configuration
st.set_page_config(
    page_title="HR Analytics Warehouse",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom Linear/Datadog-style CSS
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)


def main():
    dal = DALClient.get_instance()

    with st.sidebar:
        # Custom Brand Header
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="brand-badge">HR</div>
                <div>
                    <div class="brand-text-title">Enterprise Warehouse</div>
                    <div class="brand-text-sub">Phases 4 & 5</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Custom Navigation Menu Links
        nav_links_html = f"""
        <div class="nav-section-title">Navigation</div>
        <nav class="nav-menu">
            <a href="?nav=overview" target="_self" class="nav-link {'active' if nav_param == 'overview' else ''}">
                {SVG_DASHBOARD}
                <span>Executive Overview</span>
            </a>
            <a href="?nav=operations" target="_self" class="nav-link {'active' if nav_param == 'operations' else ''}">
                {SVG_OPERATIONS}
                <span>HR Operations (OLTP)</span>
            </a>
            <a href="?nav=analytics" target="_self" class="nav-link {'active' if nav_param == 'analytics' else ''}">
                {SVG_ANALYTICS}
                <span>Analytics & OLAP</span>
            </a>
            <a href="?nav=warehouse" target="_self" class="nav-link {'active' if nav_param == 'warehouse' else ''}">
                {SVG_WAREHOUSE}
                <span>Warehouse Console</span>
            </a>
        </nav>
        """
        st.markdown(nav_links_html, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="nav-section-title">Environment Controls</div>', unsafe_allow_html=True)

        # Environment sandbox toggle
        use_demo = st.toggle("Sandbox Data Mode", value=dal.force_demo_mode or not dal.is_connected)
        dal.force_demo_mode = use_demo

        col_st1, col_st2 = st.columns([2, 1])
        with col_st1:
            if dal.is_connected and not dal.force_demo_mode:
                st.markdown(
                    """
                    <span class="badge-pill">
                        <span class="status-dot dot-green"></span>
                        Live MySQL
                    </span>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    """
                    <span class="badge-pill">
                        <span class="status-dot dot-amber"></span>
                        Sandbox Mode
                    </span>
                    """,
                    unsafe_allow_html=True,
                )
        with col_st2:
            if st.button("Probe", help="Re-check database status"):
                dal.ping()
                st.rerun()

        if dal.connection_error and not dal.force_demo_mode:
            st.caption(f"Connection: {dal.connection_error[:70]}...")

        st.markdown("---")
        st.markdown(
            """
            <div style="font-size: 0.6875rem; color: #4B5563; line-height: 1.6; padding: 0 4px;">
                Stack: MySQL OLTP &bull; OLAP Star Schema &bull; SCD Type 2 &bull; Streamlit &bull; Plotly
            </div>
            """,
            unsafe_allow_html=True,
        )

    db_mode = "Live MySQL (Connected)" if dal.is_connected and not dal.force_demo_mode else "Sandbox Mode"
    st.markdown(
        render_top_navbar(connected=(dal.is_connected and not dal.force_demo_mode), db_mode=db_mode),
        unsafe_allow_html=True,
    )

    if nav_param == "overview":
        render_overview_module(dal)
    elif nav_param == "operations":
        render_data_entry_module(dal)
    elif nav_param == "analytics":
        render_analytics_module(dal)
    elif nav_param == "warehouse":
        render_etl_module(dal)


def render_overview_module(dal: DALClient):
    """Landing dashboard presenting key enterprise indicators using custom CSS Grid."""
    st.markdown("### Executive Overview & Workforce Pulse")
    st.caption("Operational metrics from OLTP synchronized with analytical aggregations from the OLAP Star Schema.")

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

    # -------------------------------------------------------------------------
    # 4-COLUMN CSS GRID (No st.metric, pure tabular-nums styling)
    # -------------------------------------------------------------------------
    card1 = render_kpi_card(
        label="Active Workforce",
        value=f"{len(active_emp):,}",
        trend="+3.2%",
        meta=f"of {total_hc:,} headcount",
        trend_type="positive",
    )
    card2 = render_kpi_card(
        label="Attrition Rate",
        value=f"{attrition_rate:.1f}%",
        trend="-1.4%",
        meta=f"{len(attrited_emp)} total departures",
        trend_type="positive" if attrition_rate < 15.0 else "negative",
    )
    card3 = render_kpi_card(
        label="Avg Monthly Compensation",
        value=f"₹{avg_sal:,.0f}",
        trend="+4.8%",
        meta="vs prior quarter",
        trend_type="positive",
    )
    card4 = render_kpi_card(
        label="Fact Rating Aggregate",
        value=f"{latest_perf:.2f}",
        trend="+0.09",
        meta="Scale 1.0 - 4.0",
        trend_type="positive",
    )

    st.markdown(render_kpi_grid([card1, card2, card3, card4]), unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # DISTRIBUTION TABLES
    # -------------------------------------------------------------------------
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown("#### Department Distribution")
        dept_summary = dal.get_attrition_summary(group_by="department")
        if dept_summary:
            df_dept = pd.DataFrame(dept_summary)
            df_display = df_dept.rename(
                columns={
                    "grp": "Department",
                    "headcount": "Headcount",
                    "attrited": "Attrition",
                    "attrition_rate_pct": "Attrition Rate",
                    "avg_monthly_income": "Avg Monthly Income",
                }
            )
            df_display["Avg Monthly Income"] = df_display["Avg Monthly Income"].apply(lambda v: f"₹{v:,.2f}")
            df_display["Attrition Rate"] = df_display["Attrition Rate"].apply(lambda v: f"{v:.1f}%")
            st.dataframe(df_display, use_container_width=True, hide_index=True)

    with col_right:
        st.markdown("#### Active Enterprise Projects")
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
    st.markdown("#### Platform Modules")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown(
            """
            <div class="surface-panel">
                <div class="surface-title">Data Entry (OLTP)</div>
                <div style="font-size: 0.8125rem; color: #9CA3AF; line-height: 1.5;">
                    Onboard personnel, register enterprise projects, assign staffing, and submit performance evaluations.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            """
            <div class="surface-panel">
                <div class="surface-title">SCD Type 2 Automation</div>
                <div style="font-size: 0.8125rem; color: #9CA3AF; line-height: 1.5;">
                    Update job roles or compensation to automatically close previous versions and create active records in Dim_Employee.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_c:
        st.markdown(
            """
            <div class="surface-panel">
                <div class="surface-title">Analytics & Warehouse (OLAP)</div>
                <div style="font-size: 0.8125rem; color: #9CA3AF; line-height: 1.5;">
                    Query YoY trends using LAG, inspect department leaderboards with DENSE_RANK, and evaluate flight-risk matrices.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
