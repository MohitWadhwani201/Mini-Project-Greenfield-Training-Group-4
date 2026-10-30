"""
Enterprise SaaS Data Visualizations (Linear / Datadog Aesthetic).
Implements transparent Plotly charts with muted palette and #374151 gridlines.
"""
from typing import List, Dict, Any, Optional
import pandas as pd
import plotly.graph_objects as go

# Minimalist SaaS Palette
FONT_FAMILY = "Inter, -apple-system, sans-serif"
COLOR_PRIMARY = "#3B82F6"       # Refined Blue
COLOR_EMERALD = "#10B981"       # Subtle Green
COLOR_AMBER = "#F59E0B"         # Subtle Amber
COLOR_ROSE = "#EF4444"          # Subtle Rose
COLOR_SLATE = "#6B7280"         # Muted Gray
COLOR_PURPLE = "#8B5CF6"        # Violet
COLOR_TEXT = "#F9FAFB"
COLOR_MUTED = "#9CA3AF"
COLOR_GRID = "#374151"          # Explicit gridline specification


def _apply_saas_layout(fig: go.Figure, title: str = "", height: int = 380) -> go.Figure:
    """Standardizes layout for a clean enterprise SaaS aesthetic."""
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(family=FONT_FAMILY, size=13, color=COLOR_TEXT),
            x=0.0,
            y=0.97,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        font=dict(family=FONT_FAMILY, color=COLOR_MUTED, size=11),
        margin=dict(l=35, r=25, t=40, b=35),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
            font=dict(family=FONT_FAMILY, size=11, color=COLOR_MUTED),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
        ),
        hoverlabel=dict(
            bgcolor="#111827",
            font_size=11,
            font_family=FONT_FAMILY,
            font_color=COLOR_TEXT,
            bordercolor="#374151",
        ),
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor=COLOR_GRID,
        gridwidth=1,
        zeroline=False,
        tickfont=dict(family=FONT_FAMILY, color=COLOR_MUTED, size=10),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=COLOR_GRID,
        gridwidth=1,
        zeroline=False,
        tickfont=dict(family=FONT_FAMILY, color=COLOR_MUTED, size=10),
    )
    return fig


# -----------------------------------------------------------------------------
# 1. YoY PERFORMANCE TRENDS
# -----------------------------------------------------------------------------
def create_yoy_performance_chart(data: List[Dict[str, Any]]) -> go.Figure:
    df = pd.DataFrame(data)
    fig = go.Figure()

    if df.empty:
        return _apply_saas_layout(fig, "No Performance History")

    fig.add_trace(
        go.Scatter(
            x=df["review_year"],
            y=df["avg_performance"],
            mode="lines+markers",
            name="Performance Rating",
            line=dict(color=COLOR_PRIMARY, width=2.5),
            marker=dict(size=7, color=COLOR_PRIMARY),
            hovertemplate="Year %{x}<br>Rating: <b>%{y:.2f}</b><extra></extra>",
        )
    )

    if "avg_job_satisfaction" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["review_year"],
                y=df["avg_job_satisfaction"],
                mode="lines",
                name="Job Satisfaction",
                line=dict(color=COLOR_EMERALD, width=1.5, dash="dash"),
                hovertemplate="Job Satisfaction: <b>%{y:.2f}</b><extra></extra>",
            )
        )

    if "avg_work_life_balance" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["review_year"],
                y=df["avg_work_life_balance"],
                mode="lines",
                name="Work-Life Balance",
                line=dict(color=COLOR_AMBER, width=1.5, dash="dot"),
                hovertemplate="Work-Life Balance: <b>%{y:.2f}</b><extra></extra>",
            )
        )

    if "yoy_change" in df.columns:
        fig.add_trace(
            go.Bar(
                x=df["review_year"],
                y=df["yoy_change"].fillna(0),
                name="YoY Delta",
                marker=dict(
                    color=df["yoy_change"].apply(
                        lambda v: "rgba(16, 185, 129, 0.4)" if v >= 0 else "rgba(239, 68, 68, 0.4)"
                    ),
                    line=dict(
                        color=df["yoy_change"].apply(lambda v: COLOR_EMERALD if v >= 0 else COLOR_ROSE),
                        width=1,
                    ),
                ),
                yaxis="y2",
                hovertemplate="YoY Change: <b>%{y:+.3f}</b><extra></extra>",
            )
        )
        fig.update_layout(
            yaxis2=dict(
                title=dict(text="", font=dict(color=COLOR_MUTED, size=10)),
                overlaying="y",
                side="right",
                showgrid=False,
                zeroline=True,
                zerolinecolor=COLOR_GRID,
                tickfont=dict(color=COLOR_MUTED, size=9),
            )
        )

    fig.update_yaxes(title="Score (1.0 - 4.0)", range=[1.5, 4.2])
    fig.update_xaxes(title="", dtick=1)
    return _apply_saas_layout(fig, "Performance Trajectory & YoY Change (SQL LAG)", height=360)


# -----------------------------------------------------------------------------
# 2. TOP PERFORMERS LEADERBOARD (DENSE_RANK)
# -----------------------------------------------------------------------------
def create_leaderboard_chart(data: List[Dict[str, Any]], top_n: int = 5) -> go.Figure:
    df = pd.DataFrame(data)
    fig = go.Figure()

    if df.empty:
        return _apply_saas_layout(fig, "No Leaderboard Records")

    df["full_name"] = df["first_name"] + " " + df["last_name"]
    df_sorted = df.sort_values(by=["dept_rank", "avg_rating"], ascending=[False, True])

    rank_colors = [
        COLOR_AMBER if r == 1 else "#94A3B8" if r == 2 else "#A16207" if r == 3 else COLOR_PRIMARY
        for r in df_sorted["dept_rank"]
    ]

    fig.add_trace(
        go.Bar(
            y=[f"Rank {r}: {name}" for r, name in zip(df_sorted["dept_rank"], df_sorted["full_name"])],
            x=df_sorted["avg_rating"],
            orientation="h",
            marker=dict(color=rank_colors, line=dict(color="#1F2937", width=1)),
            text=[f"{score:.2f} ({cnt} reviews)" for score, cnt in zip(df_sorted["avg_rating"], df_sorted["review_count"])],
            textposition="auto",
            textfont=dict(color=COLOR_TEXT, size=10),
            customdata=df_sorted[["department_name", "review_count", "dept_rank"]],
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Department: %{customdata[0]}<br>"
                "Avg Rating: <b>%{x:.2f}</b><br>"
                "Review Count: %{customdata[1]}<br>"
                "<extra></extra>"
            ),
        )
    )

    fig.update_xaxes(title="Average Rating", range=[2.0, 4.15])
    fig.update_yaxes(title="")
    return _apply_saas_layout(fig, "Leaderboard by Department (SQL DENSE_RANK)", height=max(320, len(df_sorted) * 32))


# -----------------------------------------------------------------------------
# 3. ATTRITION RISK & COMPENSATION
# -----------------------------------------------------------------------------
def create_attrition_chart(data: List[Dict[str, Any]], group_by: str = "Department") -> go.Figure:
    df = pd.DataFrame(data)
    fig = go.Figure()

    if df.empty:
        return _apply_saas_layout(fig, "No Attrition Records")

    df_sorted = df.sort_values(by="attrition_rate_pct", ascending=True)

    bar_colors = [
        COLOR_ROSE if rate >= 20.0 else COLOR_AMBER if rate >= 12.0 else COLOR_EMERALD
        for rate in df_sorted["attrition_rate_pct"]
    ]

    fig.add_trace(
        go.Bar(
            y=df_sorted["grp"],
            x=df_sorted["attrition_rate_pct"],
            orientation="h",
            marker=dict(color=bar_colors, line=dict(color="#1F2937", width=1)),
            text=[f"{rate:.1f}% ({att}/{hc})" for rate, att, hc in zip(df_sorted["attrition_rate_pct"], df_sorted["attrited"], df_sorted["headcount"])],
            textposition="auto",
            textfont=dict(color=COLOR_TEXT, size=10),
            customdata=df_sorted[["headcount", "attrited", "avg_monthly_income"]],
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Attrition Rate: <b>%{x:.2f}%</b><br>"
                "Attrited Count: %{customdata[1]} / %{customdata[0]}<br>"
                "Avg Monthly Income: ₹%{customdata[2]:,.2f}"
                "<extra></extra>"
            ),
        )
    )

    fig.add_vline(
        x=15.0,
        line_width=1,
        line_dash="dash",
        line_color=COLOR_ROSE,
        annotation_text="Threshold (15%)",
        annotation_position="top right",
        annotation_font=dict(color=COLOR_ROSE, size=9),
    )

    fig.update_xaxes(title="Attrition Rate (%)", range=[0, max(df_sorted["attrition_rate_pct"].max() * 1.25, 25)])
    fig.update_yaxes(title="")
    return _apply_saas_layout(fig, f"Attrition Rate by {group_by}", height=max(320, len(df_sorted) * 32))


def create_attrition_salary_scatter(data: List[Dict[str, Any]]) -> go.Figure:
    df = pd.DataFrame(data)
    fig = go.Figure()

    if df.empty:
        return _apply_saas_layout(fig, "No Compensation Records")

    fig.add_trace(
        go.Scatter(
            x=df["avg_monthly_income"],
            y=df["attrition_rate_pct"],
            mode="markers+text",
            text=df["grp"],
            textposition="top center",
            textfont=dict(size=9, color=COLOR_MUTED),
            marker=dict(
                size=df["headcount"].apply(lambda h: max(12, min(36, h // 18))),
                color=df["attrition_rate_pct"],
                colorscale=[[0, COLOR_EMERALD], [0.5, COLOR_AMBER], [1.0, COLOR_ROSE]],
                showscale=False,
                line=dict(color="#1F2937", width=1),
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Avg Income: ₹%{x:,.2f}<br>"
                "Attrition: %{y:.2f}%"
                "<extra></extra>"
            ),
        )
    )

    fig.update_xaxes(title="Average Monthly Income (₹)")
    fig.update_yaxes(title="Attrition Rate (%)")
    return _apply_saas_layout(fig, "Compensation vs Flight Risk Matrix", height=360)


# -----------------------------------------------------------------------------
# 4. PROJECT BOTTLENECKS MATRIX
# -----------------------------------------------------------------------------
def create_bottlenecks_matrix_chart(data: List[Dict[str, Any]]) -> go.Figure:
    df = pd.DataFrame(data)
    fig = go.Figure()

    if df.empty:
        return _apply_saas_layout(fig, "No Project Records")

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
            textfont=dict(size=10, color=COLOR_TEXT),
            marker=dict(
                size=df["employees_reviewed"].apply(lambda e: max(14, min(38, e * 1.1))),
                color=risk_colors,
                line=dict(color="#1F2937", width=1),
            ),
            customdata=df[["risk_rank", "status", "review_count", "employees_reviewed", "avg_performance"]],
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Risk Rank: %{customdata[0]}<br>"
                "Work-Life Balance: <b>%{x:.2f}</b><br>"
                "Job Satisfaction: <b>%{y:.2f}</b><br>"
                "Staff Evaluated: %{customdata[3]}<br>"
                "<extra></extra>"
            ),
        )
    )

    fig.add_vline(x=2.5, line_width=1, line_dash="dash", line_color=COLOR_GRID)
    fig.add_hline(y=2.5, line_width=1, line_dash="dash", line_color=COLOR_GRID)

    fig.update_xaxes(title="Work-Life Balance (1.0 - 4.0)", range=[1.2, 4.0])
    fig.update_yaxes(title="Job Satisfaction (1.0 - 4.0)", range=[1.2, 4.0])
    return _apply_saas_layout(fig, "Project Work-Life Balance vs Satisfaction", height=380)


# -----------------------------------------------------------------------------
# 5. SCD-2 TIME-TRAVEL TIMELINE
# -----------------------------------------------------------------------------
def create_scd2_timeline_chart(data: List[Dict[str, Any]]) -> go.Figure:
    df = pd.DataFrame(data)
    fig = go.Figure()

    if df.empty:
        return _apply_saas_layout(fig, "No Historical Versions")

    df_sorted = df.sort_values(by="start_date")
    today = pd.to_datetime("today").date()

    for _, row in df_sorted.iterrows():
        s_date = pd.to_datetime(row["start_date"])
        e_date = pd.to_datetime(row["end_date"]) if row.get("end_date") else pd.to_datetime(today)
        is_cur = bool(row.get("is_current", False))

        bar_color = COLOR_EMERALD if is_cur else "#374151"
        status_label = "Active (Current)" if is_cur else "Historical"
        income_delta = row.get("income_change", 0.0) or 0.0

        fig.add_trace(
            go.Bar(
                x=[(e_date - s_date).days or 30],
                y=[f"SK {row['employee_sk']}: {row['job_role']}"],
                base=[s_date],
                orientation="h",
                marker=dict(
                    color=bar_color,
                    line=dict(color=COLOR_PRIMARY if is_cur else "#4B5563", width=1),
                ),
                text=f"{status_label} | ₹{row['monthly_income']:,.0f}" + (f" ({income_delta:+,.0f})" if income_delta != 0 else ""),
                textposition="inside",
                textfont=dict(color=COLOR_TEXT, size=10),
                hovertemplate=(
                    f"<b>Version SK: {row['employee_sk']}</b><br>"
                    f"Role: {row['job_role']}<br>"
                    f"Monthly Income: ₹{row['monthly_income']:,.2f}<br>"
                    f"Start: {row['start_date']}<br>"
                    f"End: {row.get('end_date') or 'Ongoing'}<br>"
                    f"Status: {status_label}<br>"
                    f"Delta: ₹{income_delta:+,.2f}"
                    "<extra></extra>"
                ),
                showlegend=False,
            )
        )

    fig.update_xaxes(title="Validity Window", type="date")
    fig.update_yaxes(title="")
    return _apply_saas_layout(fig, "SCD Type 2 Version Lifecycle", height=max(220, len(df_sorted) * 55))
