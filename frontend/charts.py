"""
Executive Dark Theme Plotly Visualizations for Enterprise HR Analytics.
Implements:
1. YoY Performance Trends (LAG change)
2. Top Performers Leaderboard (DENSE_RANK)
3. Attrition Risk & Compensation Distribution
4. Project Bottlenecks & Flight Risk Matrix
5. SCD-2 Historical Version Timeline
"""
from typing import List, Dict, Any, Optional
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Plotly Dark Theme Preset
THEME_FONT = "Plus Jakarta Sans, -apple-system, sans-serif"
COLOR_PRIMARY = "#38BDF8"       # Sky Blue
COLOR_SECONDARY = "#818CF8"     # Soft Indigo
COLOR_EMERALD = "#10B981"       # Mint / Success
COLOR_AMBER = "#F59E0B"         # Amber / Warning
COLOR_ROSE = "#F43F5E"          # Rose / Danger
COLOR_PURPLE = "#A855F7"        # Violet
COLOR_TEXT = "#F8FAFC"
COLOR_MUTED = "#94A3B8"
COLOR_GRID = "rgba(255, 255, 255, 0.07)"


def _apply_dark_layout(fig: go.Figure, title: str = "", height: int = 400) -> go.Figure:
    """Standardize layout for dark cyber enterprise aesthetic."""
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(family=THEME_FONT, size=15, color=COLOR_TEXT),
            x=0.01,
            y=0.96,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        font=dict(family=THEME_FONT, color=COLOR_MUTED, size=12),
        margin=dict(l=40, r=30, t=50, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(family=THEME_FONT, size=11, color=COLOR_MUTED),
            bgcolor="rgba(15, 23, 42, 0.6)",
            bordercolor="rgba(255,255,255,0.08)",
            borderwidth=1,
        ),
        hoverlabel=dict(
            bgcolor="#1E293B",
            font_size=12,
            font_family=THEME_FONT,
            font_color=COLOR_TEXT,
            bordercolor=COLOR_PRIMARY,
        ),
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor=COLOR_GRID,
        zeroline=False,
        tickfont=dict(family=THEME_FONT, color=COLOR_MUTED, size=11),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=COLOR_GRID,
        zeroline=False,
        tickfont=dict(family=THEME_FONT, color=COLOR_MUTED, size=11),
    )
    return fig


# -----------------------------------------------------------------------------
# 1. YoY PERFORMANCE TRENDS
# -----------------------------------------------------------------------------
def create_yoy_performance_chart(data: List[Dict[str, Any]]) -> go.Figure:
    """
    Renders YoY Performance Trend with LAG() delta markers and auxiliary satisfaction scores.
    """
    df = pd.DataFrame(data)
    fig = go.Figure()

    if df.empty:
        return _apply_dark_layout(fig, "No Performance History Found")

    # Primary Line: Avg Performance Rating
    fig.add_trace(
        go.Scatter(
            x=df["review_year"],
            y=df["avg_performance"],
            mode="lines+markers",
            name="Avg Performance",
            line=dict(color=COLOR_PRIMARY, width=3.5),
            marker=dict(size=9, color=COLOR_PRIMARY, line=dict(color="#0A0E17", width=2)),
            hovertemplate="<b>Year %{x}</b><br>Avg Rating: %{y:.2f}<extra></extra>",
        )
    )

    # Secondary Trace: Job Satisfaction
    if "avg_job_satisfaction" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["review_year"],
                y=df["avg_job_satisfaction"],
                mode="lines+markers",
                name="Job Satisfaction",
                line=dict(color=COLOR_EMERALD, width=2, dash="dash"),
                marker=dict(size=7, color=COLOR_EMERALD),
                hovertemplate="Job Satisfaction: %{y:.2f}<extra></extra>",
            )
        )

    # Tertiary Trace: Work-Life Balance
    if "avg_work_life_balance" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["review_year"],
                y=df["avg_work_life_balance"],
                mode="lines+markers",
                name="Work-Life Balance",
                line=dict(color=COLOR_AMBER, width=2, dash="dot"),
                marker=dict(size=7, color=COLOR_AMBER),
                hovertemplate="Work-Life Balance: %{y:.2f}<extra></extra>",
            )
        )

    # YoY Change Bars on secondary y-axis if present
    if "yoy_change" in df.columns:
        fig.add_trace(
            go.Bar(
                x=df["review_year"],
                y=df["yoy_change"].fillna(0),
                name="YoY Delta (LAG)",
                marker=dict(
                    color=df["yoy_change"].apply(
                        lambda v: "rgba(16, 185, 129, 0.45)" if v >= 0 else "rgba(244, 63, 94, 0.45)"
                    ),
                    line=dict(
                        color=df["yoy_change"].apply(lambda v: COLOR_EMERALD if v >= 0 else COLOR_ROSE),
                        width=1,
                    ),
                ),
                yaxis="y2",
                hovertemplate="YoY Change: %{y:+.3f}<extra></extra>",
            )
        )
        fig.update_layout(
            yaxis2=dict(
                title=dict(text="YoY Delta", font=dict(color=COLOR_MUTED, size=11)),
                overlaying="y",
                side="right",
                showgrid=False,
                zeroline=True,
                zerolinecolor=COLOR_GRID,
                tickfont=dict(color=COLOR_MUTED, size=10),
            )
        )

    fig.update_yaxes(title="Score (Scale 1.0 - 4.0)", range=[1.5, 4.2])
    fig.update_xaxes(title="Review Year", dtick=1)
    return _apply_dark_layout(fig, "Year-Over-Year Performance & Satisfaction Trajectory", height=430)


# -----------------------------------------------------------------------------
# 2. TOP PERFORMERS LEADERBOARD (DENSE_RANK)
# -----------------------------------------------------------------------------
def create_leaderboard_chart(data: List[Dict[str, Any]], top_n: int = 5) -> go.Figure:
    """
    Ranked horizontal bar chart for top performers grouped by department.
    """
    df = pd.DataFrame(data)
    fig = go.Figure()

    if df.empty:
        return _apply_dark_layout(fig, "No Leaderboard Data Available")

    df["full_name"] = df["first_name"] + " " + df["last_name"]
    # Sort for bottom-up horizontal bar display
    df_sorted = df.sort_values(by=["dept_rank", "avg_rating"], ascending=[False, True])

    # Rank badge mapping
    rank_colors = []
    for r in df_sorted["dept_rank"]:
        if r == 1:
            rank_colors.append("#F59E0B")  # Gold
        elif r == 2:
            rank_colors.append("#94A3B8")  # Silver
        elif r == 3:
            rank_colors.append("#B45309")  # Bronze
        else:
            rank_colors.append(COLOR_PRIMARY)

    fig.add_trace(
        go.Bar(
            y=[f"#{r} {name}" for r, name in zip(df_sorted["dept_rank"], df_sorted["full_name"])],
            x=df_sorted["avg_rating"],
            orientation="h",
            marker=dict(
                color=rank_colors,
                line=dict(color="rgba(255,255,255,0.15)", width=1),
            ),
            text=[f"<b>{score:.2f}</b> ★ ({cnt} reviews)" for score, cnt in zip(df_sorted["avg_rating"], df_sorted["review_count"])],
            textposition="auto",
            textfont=dict(color=COLOR_TEXT, size=11),
            customdata=df_sorted[["department_name", "review_count", "dept_rank"]],
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Department: %{customdata[0]}<br>"
                "Avg Rating: %{x:.2f} / 4.0<br>"
                "Reviews Evaluated: %{customdata[1]}<br>"
                "Department Rank: <b>#%{customdata[2]}</b>"
                "<extra></extra>"
            ),
        )
    )

    fig.update_xaxes(title="Average Performance Rating", range=[2.0, 4.15])
    fig.update_yaxes(title="")
    return _apply_dark_layout(fig, f"Top Performers Leaderboard (SQL DENSE_RANK)", height=max(380, len(df_sorted) * 35))


# -----------------------------------------------------------------------------
# 3. ATTRITION RISK & COMPENSATION
# -----------------------------------------------------------------------------
def create_attrition_chart(data: List[Dict[str, Any]], group_by: str = "Department") -> go.Figure:
    """
    Renders Attrition Rate (%) comparison with flight-risk threshold.
    """
    df = pd.DataFrame(data)
    fig = go.Figure()

    if df.empty:
        return _apply_dark_layout(fig, "No Attrition Data Available")

    df_sorted = df.sort_values(by="attrition_rate_pct", ascending=True)

    # Color scale by risk level
    bar_colors = [
        COLOR_ROSE if rate >= 20.0 else COLOR_AMBER if rate >= 12.0 else COLOR_EMERALD
        for rate in df_sorted["attrition_rate_pct"]
    ]

    fig.add_trace(
        go.Bar(
            y=df_sorted["grp"],
            x=df_sorted["attrition_rate_pct"],
            orientation="h",
            marker=dict(color=bar_colors, line=dict(color="rgba(255,255,255,0.15)", width=1)),
            text=[f"<b>{rate:.1f}%</b> ({att}/{hc})" for rate, att, hc in zip(df_sorted["attrition_rate_pct"], df_sorted["attrited"], df_sorted["headcount"])],
            textposition="auto",
            textfont=dict(color=COLOR_TEXT, size=11),
            customdata=df_sorted[["headcount", "attrited", "avg_monthly_income"]],
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Attrition Rate: <b>%{x:.2f}%</b><br>"
                "Attrited Count: %{customdata[1]} of %{customdata[0]}<br>"
                "Avg Monthly Income: ₹%{customdata[2]:,.2f}"
                "<extra></extra>"
            ),
        )
    )

    # Benchmark reference line (15% benchmark)
    fig.add_vline(
        x=15.0,
        line_width=1.5,
        line_dash="dash",
        line_color=COLOR_ROSE,
        annotation_text="Critical Threshold (15%)",
        annotation_position="top right",
        annotation_font=dict(color=COLOR_ROSE, size=10),
    )

    fig.update_xaxes(title="Attrition Rate (%)", range=[0, max(df_sorted["attrition_rate_pct"].max() * 1.25, 25)])
    fig.update_yaxes(title="")
    return _apply_dark_layout(fig, f"Flight Risk & Attrition Rate by {group_by}", height=max(360, len(df_sorted) * 34))


def create_attrition_salary_scatter(data: List[Dict[str, Any]]) -> go.Figure:
    """
    Scatter plot: Monthly Income vs Attrition Rate to uncover flight-risk compensation traps.
    """
    df = pd.DataFrame(data)
    fig = go.Figure()

    if df.empty:
        return _apply_dark_layout(fig, "No Compensation Data")

    fig.add_trace(
        go.Scatter(
            x=df["avg_monthly_income"],
            y=df["attrition_rate_pct"],
            mode="markers+text",
            text=df["grp"],
            textposition="top center",
            textfont=dict(size=10, color=COLOR_TEXT),
            marker=dict(
                size=df["headcount"].apply(lambda h: max(14, min(40, h // 15))),
                color=df["attrition_rate_pct"],
                colorscale=[[0, COLOR_EMERALD], [0.5, COLOR_AMBER], [1.0, COLOR_ROSE]],
                showscale=False,
                line=dict(color="#F8FAFC", width=1.5),
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Avg Monthly Income: ₹%{x:,.2f}<br>"
                "Attrition Rate: %{y:.2f}%<br>"
                "<extra></extra>"
            ),
        )
    )

    fig.update_xaxes(title="Average Monthly Income (₹)", showgrid=True)
    fig.update_yaxes(title="Attrition Rate (%)", showgrid=True)
    return _apply_dark_layout(fig, "Compensation vs Flight Risk Matrix (Bubble Size = Headcount)", height=400)


# -----------------------------------------------------------------------------
# 4. PROJECT BOTTLENECKS MATRIX
# -----------------------------------------------------------------------------
def create_bottlenecks_matrix_chart(data: List[Dict[str, Any]]) -> go.Figure:
    """
    Quadrant plot of Work-Life Balance vs Job Satisfaction per Project.
    Rank 1 identifies the highest bottleneck/burnout risk.
    """
    df = pd.DataFrame(data)
    fig = go.Figure()

    if df.empty:
        return _apply_dark_layout(fig, "No Project Risk Data")

    # Risk color mapping
    risk_colors = [
        COLOR_ROSE if rank == 1 else COLOR_AMBER if rank == 2 else COLOR_PRIMARY if rank == 3 else COLOR_EMERALD
        for rank in df["risk_rank"]
    ]

    fig.add_trace(
        go.Scatter(
            x=df["avg_work_life_balance"],
            y=df["avg_job_satisfaction"],
            mode="markers+text",
            text=df["project_name"],
            textposition="top center",
            textfont=dict(size=11, color=COLOR_TEXT),
            marker=dict(
                size=df["employees_reviewed"].apply(lambda e: max(16, min(45, e * 1.2))),
                color=risk_colors,
                line=dict(color="#FFFFFF", width=1.5),
            ),
            customdata=df[["risk_rank", "status", "review_count", "employees_reviewed", "avg_performance"]],
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Risk Rank: <b>#%{customdata[0]}</b><br>"
                "Project Status: %{customdata[1]}<br>"
                "Work-Life Balance: <b>%{x:.2f} / 4.0</b><br>"
                "Job Satisfaction: <b>%{y:.2f} / 4.0</b><br>"
                "Team Evaluated: %{customdata[3]} members (%{customdata[2]} reviews)<br>"
                "Avg Performance: %{customdata[4]:.2f}"
                "<extra></extra>"
            ),
        )
    )

    # Reference crosshairs at 2.5 benchmark
    fig.add_vline(x=2.5, line_width=1, line_dash="dash", line_color="rgba(255,255,255,0.2)")
    fig.add_hline(y=2.5, line_width=1, line_dash="dash", line_color="rgba(255,255,255,0.2)")

    fig.update_xaxes(title="Average Work-Life Balance Score", range=[1.2, 4.0])
    fig.update_yaxes(title="Average Job Satisfaction Score", range=[1.2, 4.0])
    return _apply_dark_layout(fig, "Project Stress & Burnout Bottlenecks (Bubble Size = Staff Count)", height=420)


# -----------------------------------------------------------------------------
# 5. SCD-2 TIME-TRAVEL TIMELINE
# -----------------------------------------------------------------------------
def create_scd2_timeline_chart(data: List[Dict[str, Any]]) -> go.Figure:
    """
    Gantt / Timeline chart visualizing the SCD Type 2 dimension versioning lifecycle.
    """
    df = pd.DataFrame(data)
    fig = go.Figure()

    if df.empty:
        return _apply_dark_layout(fig, "No Version History Available")

    df_sorted = df.sort_values(by="start_date")
    today = pd.to_datetime("today").date()

    for idx, row in df_sorted.iterrows():
        s_date = pd.to_datetime(row["start_date"])
        e_date = pd.to_datetime(row["end_date"]) if row.get("end_date") else pd.to_datetime(today)
        is_cur = bool(row.get("is_current", False))

        bar_color = COLOR_EMERALD if is_cur else "#475569"
        status_label = "ACTIVE (CURRENT)" if is_cur else "INACTIVE (HISTORICAL)"
        income_delta = row.get("income_change", 0.0) or 0.0

        fig.add_trace(
            go.Bar(
                x=[(e_date - s_date).days or 30],
                y=[f"Ver #{row['employee_sk']}: {row['job_role']}"],
                base=[s_date],
                orientation="h",
                marker=dict(
                    color=bar_color,
                    line=dict(color=COLOR_PRIMARY if is_cur else "rgba(255,255,255,0.2)", width=1.5),
                ),
                text=f"{status_label} &bull; ₹{row['monthly_income']:,.0f}/mo" + (f" ({income_delta:+,.0f} delta)" if income_delta != 0 else ""),
                textposition="inside",
                textfont=dict(color=COLOR_TEXT, size=11),
                hovertemplate=(
                    f"<b>Version SK: {row['employee_sk']}</b><br>"
                    f"Job Role: {row['job_role']}<br>"
                    f"Monthly Income: ₹{row['monthly_income']:,.2f}<br>"
                    f"Start Date: {row['start_date']}<br>"
                    f"End Date: {row.get('end_date') or 'Ongoing (Active)'}<br>"
                    f"Status: <b>{status_label}</b><br>"
                    f"Salary Delta (LAG): <b>₹{income_delta:+,.2f}</b>"
                    "<extra></extra>"
                ),
                name=f"SK #{row['employee_sk']}",
                showlegend=False,
            )
        )

    fig.update_xaxes(title="Validity Timeline", type="date")
    fig.update_yaxes(title="")
    return _apply_dark_layout(fig, "SCD Type 2 Dimension Lifespan (Audit & Time-Travel)", height=max(260, len(df_sorted) * 60))

