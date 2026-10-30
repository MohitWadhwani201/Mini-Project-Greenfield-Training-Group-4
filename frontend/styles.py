"""
Bespoke Enterprise SaaS Design System (Linear / Datadog / Vercel Aesthetic).
Provides custom CSS overrides, SVG icons, KPI card grids, and top navbar components.
"""

# Color Palette Tokens - Refined Enterprise Dark Neutral
COLOR_BG_ROOT = "#090D16"
COLOR_BG_SIDEBAR = "#0B0F19"
COLOR_SURFACE = "#111827"
COLOR_SURFACE_HOVER = "#1E293B"
COLOR_BORDER = "#1F2937"
COLOR_BORDER_HOVER = "#374151"
COLOR_PRIMARY = "#3B82F6"
COLOR_EMERALD = "#10B981"
COLOR_AMBER = "#F59E0B"
COLOR_ROSE = "#EF4444"
COLOR_TEXT_PRIMARY = "#F9FAFB"
COLOR_TEXT_SECONDARY = "#9CA3AF"
COLOR_TEXT_MUTED = "#6B7280"

# Minimal Inline SVG Icons (Lucide Specification)
SVG_DASHBOARD = """<svg class="nav-icon" viewBox="0 0 24 24"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>"""
SVG_OPERATIONS = """<svg class="nav-icon" viewBox="0 0 24 24"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>"""
SVG_ANALYTICS = """<svg class="nav-icon" viewBox="0 0 24 24"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>"""
SVG_WAREHOUSE = """<svg class="nav-icon" viewBox="0 0 24 24"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5V19A9 3 0 0 0 21 19V5"/><path d="M3 12A9 3 0 0 0 21 12"/></svg>"""

DARK_THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* Global Font & Reset */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    color: #F9FAFB;
    background-color: #090D16;
}

/* App Background */
.stApp {
    background-color: #090D16;
    color: #F9FAFB;
}

/* Hide Default Streamlit Header & Clutter */
header[data-testid="stHeader"], #MainMenu, footer {
    display: none !important;
}

/* Content Container Margin */
.block-container {
    padding-top: 1.25rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 1400px !important;
}

/* Custom Sidebar Styling */
section[data-testid="stSidebar"] {
    background-color: #0B0F19 !important;
    border-right: 1px solid #1F2937 !important;
}

section[data-testid="stSidebar"] > div:first-child {
    padding: 1.5rem 1rem !important;
}

/* Custom Navigation Menu */
.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 4px 1.25rem 4px;
    border-bottom: 1px solid #1F2937;
    margin-bottom: 1.25rem;
}

.brand-badge {
    width: 28px;
    height: 28px;
    border-radius: 6px;
    background: #1E293B;
    border: 1px solid #334155;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #3B82F6;
    font-size: 0.8125rem;
    font-weight: 700;
}

.brand-text-title {
    font-size: 0.875rem;
    font-weight: 600;
    color: #F9FAFB;
    letter-spacing: -0.01em;
    line-height: 1.2;
}

.brand-text-sub {
    font-size: 0.75rem;
    color: #6B7280;
    line-height: 1.2;
}

.nav-section-title {
    font-size: 0.6875rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #4B5563;
    padding: 0 8px;
    margin-bottom: 6px;
}

.nav-menu {
    display: flex;
    flex-direction: column;
    gap: 3px;
    margin-bottom: 1.5rem;
}

.nav-link {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    border-radius: 6px;
    color: #9CA3AF;
    text-decoration: none !important;
    font-size: 0.8125rem;
    font-weight: 500;
    transition: all 0.12s ease;
    border: 1px solid transparent;
}

.nav-link:hover {
    color: #F3F4F6;
    background: rgba(255, 255, 255, 0.04);
}

.nav-link.active {
    color: #FFFFFF;
    background: rgba(255, 255, 255, 0.07);
    border-color: rgba(255, 255, 255, 0.09);
    box-shadow: inset 2px 0 0 0 #3B82F6;
}

.nav-icon {
    width: 15px;
    height: 15px;
    stroke-width: 2;
    stroke: currentColor;
    fill: none;
    flex-shrink: 0;
}

/* Custom Top Navigation Bar (Flexbox) */
.top-navbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 1.125rem;
    border-bottom: 1px solid #1F2937;
    margin-bottom: 1.5rem;
}

.top-navbar-left {
    display: flex;
    flex-direction: column;
}

.brand-heading {
    font-size: 1.125rem;
    font-weight: 600;
    color: #F9FAFB;
    letter-spacing: -0.015em;
    margin: 0;
    line-height: 1.3;
}

.brand-subheading {
    font-size: 0.8125rem;
    color: #6B7280;
    margin: 2px 0 0 0;
    line-height: 1.2;
}

.badge-group {
    display: flex;
    align-items: center;
    gap: 8px;
}

.badge-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 10px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 500;
    color: #D1D5DB;
    background: #111827;
    border: 1px solid #1F2937;
    letter-spacing: 0.01em;
}

.status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    display: inline-block;
}

.dot-green { background-color: #10B981; }
.dot-amber { background-color: #F59E0B; }
.dot-blue { background-color: #3B82F6; }

/* Custom KPI Grid (CSS Grid 4 Columns) */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
}

@media (max-width: 1024px) {
    .kpi-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 640px) {
    .kpi-grid { grid-template-columns: 1fr; }
}

.kpi-card {
    background: #111827;
    border: 1px solid #1F2937;
    border-radius: 8px;
    padding: 1.125rem 1.25rem;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.2);
    transition: border-color 0.15s ease;
}

.kpi-card:hover {
    border-color: #374151;
}

.kpi-label {
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #9CA3AF;
    margin-bottom: 0.35rem;
}

.kpi-value {
    font-size: 1.75rem;
    font-weight: 600;
    color: #F9FAFB;
    font-variant-numeric: tabular-nums;
    line-height: 1.2;
    letter-spacing: -0.02em;
}

.kpi-footer {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    margin-top: 0.45rem;
    font-size: 0.75rem;
}

.trend-positive {
    color: #10B981;
    font-weight: 500;
    font-variant-numeric: tabular-nums;
}

.trend-negative {
    color: #EF4444;
    font-weight: 500;
    font-variant-numeric: tabular-nums;
}

.trend-neutral {
    color: #9CA3AF;
    font-weight: 500;
    font-variant-numeric: tabular-nums;
}

.kpi-meta-text {
    color: #6B7280;
}

/* Linear-style Surface Containers */
.surface-panel {
    background: #111827;
    border: 1px solid #1F2937;
    border-radius: 8px;
    padding: 1.25rem;
    margin-bottom: 1.25rem;
}

.surface-title {
    font-size: 0.875rem;
    font-weight: 600;
    color: #F3F4F6;
    letter-spacing: -0.01em;
    margin-bottom: 0.75rem;
}

/* Callout Box for SCD-2 Logic */
.callout-box {
    background: #111827;
    border: 1px solid #1F2937;
    border-left: 3px solid #3B82F6;
    border-radius: 6px;
    padding: 0.875rem 1rem;
    margin-bottom: 1.25rem;
}

.callout-title {
    font-size: 0.8125rem;
    font-weight: 600;
    color: #E5E7EB;
    margin-bottom: 0.25rem;
}

.callout-desc {
    font-size: 0.75rem;
    color: #9CA3AF;
    line-height: 1.5;
    margin: 0;
}

/* Form Inputs & Controls */
div[data-baseweb="input"],
div[data-baseweb="select"] > div,
div[data-baseweb="textarea"] {
    background-color: #111827 !important;
    border: 1px solid #1F2937 !important;
    border-radius: 6px !important;
    color: #F3F4F6 !important;
}

div[data-baseweb="input"]:focus-within,
div[data-baseweb="select"]:focus-within {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 1px #3B82F6 !important;
}

input, select, textarea {
    color: #F9FAFB !important;
    font-size: 0.875rem !important;
}

/* Primary Action Buttons */
.stButton > button {
    background: #2563EB !important;
    color: #FFFFFF !important;
    font-size: 0.8125rem !important;
    font-weight: 500 !important;
    border: 1px solid #3B82F6 !important;
    border-radius: 6px !important;
    padding: 6px 14px !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.2) !important;
}

.stButton > button:hover {
    background: #1D4ED8 !important;
    border-color: #60A5FA !important;
}

button[kind="secondary"] {
    background: #111827 !important;
    color: #D1D5DB !important;
    border: 1px solid #1F2937 !important;
    box-shadow: none !important;
}

button[kind="secondary"]:hover {
    background: #1E293B !important;
    border-color: #374151 !important;
}

/* Tab Bar - Underline Aesthetic */
.stTabs [data-baseweb="tab-list"] {
    background-color: transparent !important;
    border-bottom: 1px solid #1F2937 !important;
    padding: 0 !important;
    gap: 1.25rem !important;
}

.stTabs [data-baseweb="tab"] {
    height: 38px !important;
    background-color: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    color: #9CA3AF !important;
    font-size: 0.8125rem !important;
    font-weight: 500 !important;
    padding: 0 2px !important;
    transition: color 0.15s ease, border-color 0.15s ease !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: #E5E7EB !important;
}

.stTabs [aria-selected="true"] {
    color: #F9FAFB !important;
    border-bottom: 2px solid #3B82F6 !important;
    background: transparent !important;
}

/* Dataframe Styling */
div[data-testid="stDataFrame"] {
    border: 1px solid #1F2937 !important;
    border-radius: 6px !important;
    background-color: #111827 !important;
}

/* Scrollbars */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: #090D16;
}
::-webkit-scrollbar-thumb {
    background: #1F2937;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: #374151;
}
</style>
"""


def render_top_navbar(connected: bool = True, db_mode: str = "Live OLTP/OLAP") -> str:
    """Renders the custom top flexbox header."""
    status_dot = '<span class="status-dot dot-green"></span>' if connected else '<span class="status-dot dot-amber"></span>'
    status_text = db_mode if connected else "Sandbox Mode"
    return f"""
    <div class="top-navbar">
        <div class="top-navbar-left">
            <h1 class="brand-heading">HR Analytics Warehouse</h1>
            <p class="brand-subheading">Phase 4 & 5 Unified Platform</p>
        </div>
        <div class="badge-group">
            <span class="badge-pill">
                <span class="status-dot dot-blue"></span>
                SCD Type 2
            </span>
            <span class="badge-pill">
                {status_dot}
                {status_text}
            </span>
        </div>
    </div>
    """


def render_kpi_card(label: str, value: str, trend: str = "", meta: str = "", trend_type: str = "positive") -> str:
    """Renders a single tabular metric card for the 4-column CSS grid."""
    trend_html = ""
    if trend:
        cls = f"trend-{trend_type}"
        trend_html = f'<span class="{cls}">{trend}</span>'

    meta_html = f'<span class="kpi-meta-text">{meta}</span>' if meta else ""

    footer_html = ""
    if trend_html or meta_html:
        footer_html = f'<div class="kpi-footer">{trend_html}{meta_html}</div>'

    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {footer_html}
    </div>
    """


def render_kpi_grid(cards_html: list[str]) -> str:
    """Wraps cards in the CSS Grid."""
    return f"""
    <div class="kpi-grid">
        {"".join(cards_html)}
    </div>
    """


def render_scd2_callout() -> str:
    """Clean callout for SCD Type 2 logic."""
    return """
    <div class="callout-box">
        <div class="callout-title">SCD Type 2 Dimension Versioning</div>
        <p class="callout-desc">
            Modifications to <strong>Job Role</strong> or <strong>Monthly Income</strong> execute <code>ETL_Dim_Employee_SCD2</code>. 
            The prior active record is terminated (<code>is_current = FALSE</code>, <code>end_date = yesterday</code>), 
            and a new active record (<code>is_current = TRUE</code>, <code>start_date = today</code>) is inserted to preserve historical audit continuity.
        </p>
    </div>
    """
