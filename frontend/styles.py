"""
Executive Dark Theme & Design System for Enterprise HR Data Platform.
Provides typography, color tokens, and custom CSS injections.
"""

# Color Palette Tokens
PRIMARY_COLOR = "#38BDF8"       # Electric Cyan / Sky Blue
PRIMARY_HOVER = "#0284C7"       # Deep Sky
SECONDARY_COLOR = "#818CF8"     # Soft Indigo
ACCENT_EMERALD = "#10B981"      # Emerald Success / Active
ACCENT_AMBER = "#F59E0B"        # Amber Warning / Medium Risk
ACCENT_ROSE = "#F43F5E"         # Rose Danger / Inactive / Flight Risk
ACCENT_PURPLE = "#A855F7"       # Violet Accent
BG_DARK = "#0A0E17"             # Obsidian Base
BG_SURFACE = "#111827"          # Dark Slate Container
BG_SURFACE_ELEVATED = "#1E293B" # Elevated Dark Slate
TEXT_LIGHT = "#F8FAFC"          # Bright Off-White
TEXT_MUTED = "#94A3B8"          # Cool Slate Gray
BORDER_SUBTLE = "rgba(255, 255, 255, 0.08)"
BORDER_ACCENT = "rgba(56, 189, 248, 0.25)"


DARK_THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* Global Reset & Typography */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    color: #F8FAFC;
    background-color: #0A0E17;
}

/* App Background */
.stApp {
    background: radial-gradient(circle at 15% 15%, #0F172A 0%, #0A0E17 100%) fixed;
    color: #F8FAFC;
}

/* Sidebar Customization */
section[data-testid="stSidebar"] {
    background-color: #0F172A !important;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}

section[data-testid="stSidebar"] .stMarkdown h1, 
section[data-testid="stSidebar"] .stMarkdown h2, 
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #F8FAFC !important;
}

/* Streamlit Header Bar */
header[data-testid="stHeader"] {
    background: transparent !important;
}

/* Top App Banner */
.enterprise-header {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
    border: 1px solid rgba(56, 189, 248, 0.2);
    border-radius: 14px;
    padding: 24px 30px;
    margin-bottom: 24px;
    backdrop-filter: blur(12px);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
}

.enterprise-title {
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -0.5px;
    background: linear-gradient(135deg, #F8FAFC 0%, #38BDF8 60%, #818CF8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    padding: 0;
}

.enterprise-subtitle {
    color: #94A3B8;
    font-size: 14px;
    font-weight: 400;
    margin-top: 6px;
    margin-bottom: 0;
}

/* Metric / KPI Cards */
.kpi-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
}

.kpi-card {
    background: linear-gradient(145deg, #161F30 0%, #0F172A 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 20px;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.kpi-card:hover {
    transform: translateY(-2px);
    border-color: rgba(56, 189, 248, 0.35);
    box-shadow: 0 10px 25px -5px rgba(56, 189, 248, 0.15);
}

.kpi-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: #38BDF8;
}

.kpi-card.emerald::before { background: #10B981; }
.kpi-card.amber::before { background: #F59E0B; }
.kpi-card.rose::before { background: #F43F5E; }
.kpi-card.purple::before { background: #A855F7; }

.kpi-label {
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #94A3B8;
    margin-bottom: 8px;
}

.kpi-value {
    font-size: 30px;
    font-weight: 700;
    color: #F8FAFC;
    line-height: 1.1;
    font-family: 'JetBrains Mono', monospace;
}

.kpi-subtext {
    font-size: 12px;
    color: #64748B;
    margin-top: 6px;
}

/* Glass Surface Cards */
.glass-panel {
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 22px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
}

.glass-panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    padding-bottom: 12px;
    margin-bottom: 16px;
}

.glass-panel-title {
    font-size: 17px;
    font-weight: 700;
    color: #F8FAFC;
    letter-spacing: -0.2px;
    margin: 0;
}

/* SCD-2 Explanatory Box */
.scd2-banner {
    background: linear-gradient(135deg, rgba(30, 27, 75, 0.6) 0%, rgba(15, 23, 42, 0.85) 100%);
    border: 1px solid rgba(129, 140, 248, 0.3);
    border-left: 4px solid #818CF8;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 20px;
}

.scd2-banner-title {
    font-size: 14px;
    font-weight: 700;
    color: #C7D2FE;
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
}

.scd2-banner-desc {
    font-size: 13px;
    color: #94A3B8;
    line-height: 1.5;
    margin: 0;
}

/* Status Badges */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.3px;
}

.pill-active {
    background: rgba(16, 185, 129, 0.15);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.pill-inactive {
    background: rgba(244, 63, 94, 0.15);
    color: #FB7185;
    border: 1px solid rgba(244, 63, 94, 0.3);
}

.pill-info {
    background: rgba(56, 189, 248, 0.15);
    color: #38BDF8;
    border: 1px solid rgba(56, 189, 248, 0.3);
}

.pill-warning {
    background: rgba(245, 158, 11, 0.15);
    color: #FBBF24;
    border: 1px solid rgba(245, 158, 11, 0.3);
}

/* Form Inputs & Customization */
div[data-baseweb="input"], 
div[data-baseweb="select"] > div,
div[data-baseweb="textarea"] {
    background-color: #1E293B !important;
    border-color: rgba(255, 255, 255, 0.12) !important;
    color: #F8FAFC !important;
    border-radius: 8px !important;
}

div[data-baseweb="input"]:focus-within,
div[data-baseweb="select"]:focus-within {
    border-color: #38BDF8 !important;
    box-shadow: 0 0 0 1px #38BDF8 !important;
}

input, select, textarea {
    color: #F8FAFC !important;
}

/* Button Customization */
.stButton > button {
    background: linear-gradient(135deg, #0284C7 0%, #2563EB 100%) !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 22px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 14px 0 rgba(2, 132, 199, 0.35) !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #0369A1 0%, #1D4ED8 100%) !important;
    box-shadow: 0 6px 20px 0 rgba(2, 132, 199, 0.5) !important;
    transform: translateY(-1px) !important;
}

.stButton > button:active {
    transform: translateY(0px) !important;
}

/* Secondary Button override */
button[kind="secondary"] {
    background: #1E293B !important;
    color: #94A3B8 !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    box-shadow: none !important;
}

/* Tabs Styling */
.stTabs [data-baseweb="tab-list"] {
    background-color: #0F172A;
    border-radius: 10px;
    padding: 6px;
    gap: 8px;
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.stTabs [data-baseweb="tab"] {
    height: 42px;
    white-space: pre-wrap;
    background-color: transparent;
    border-radius: 8px;
    color: #94A3B8;
    font-weight: 600;
    font-size: 14px;
    border: none;
    padding: 0 18px;
    transition: all 0.2s ease;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(56, 189, 248, 0.15) 0%, rgba(99, 102, 241, 0.15) 100%) !important;
    color: #38BDF8 !important;
    border: 1px solid rgba(56, 189, 248, 0.35) !important;
}

/* Dataframe & Tables */
div[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.08);
}

/* Custom Scrollbars */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: #0A0E17;
}
::-webkit-scrollbar-thumb {
    background: #1E293B;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: #334155;
}
</style>
"""


def get_header_html(connected: bool = True, db_mode: str = "Live OLTP/OLAP") -> str:
    status_pill = (
        f'<span class="status-pill pill-active">● {db_mode}</span>'
        if connected
        else '<span class="status-pill pill-warning">⚠ Demo Mode (Sandbox)</span>'
    )
    return f"""
    <div class="enterprise-header">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
            <div>
                <h1 class="enterprise-title">⚡ ENTERPRISE HR ANALYTICS & WAREHOUSE</h1>
                <p class="enterprise-subtitle">
                    Phase 4 & 5 Unified Platform &bull; OLTP Transactions &bull; OLAP Star Schema &bull; SCD Type 2 Engine
                </p>
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <span class="status-pill pill-info">SCD Type 2 Enabled</span>
                {status_pill}
            </div>
        </div>
    </div>
    """


def get_kpi_card_html(label: str, value: str, subtext: str = "", theme: str = "sky") -> str:
    return f"""
    <div class="kpi-card {theme}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {f'<div class="kpi-subtext">{subtext}</div>' if subtext else ''}
    </div>
    """


def get_scd2_explanation_html() -> str:
    return """
    <div class="scd2-banner">
        <div class="scd2-banner-title">
            <span>🛡️ SCD TYPE 2 (SLOWLY CHANGING DIMENSIONS) AUTOMATION</span>
        </div>
        <p class="scd2-banner-desc">
            Whenever an employee's <strong>Job Role</strong> or <strong>Monthly Income</strong> is modified, 
            the DAL automatically executes <code>ETL_Dim_Employee_SCD2</code> in the Star Schema. 
            The previous active record is terminated (<code>is_current = FALSE</code>, <code>end_date = yesterday</code>), 
            and a new active version (<code>is_current = TRUE</code>, <code>start_date = today</code>) is inserted. 
            This guarantees 100% audit accuracy for historical performance queries.
        </p>
    </div>
    """

