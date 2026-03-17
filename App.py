"""
╔══════════════════════════════════════════════════════════════╗
║       UEL PRO STOCK SCREENER  —  Chile Market Edition       ║
║       Next-Gen UI: Terminal-Style Dashboard                  ║
╚══════════════════════════════════════════════════════════════╝
"""

import ast
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit.column_config import (
    NumberColumn,
    ProgressColumn,
    TextColumn,
    LineChartColumn,
)

# ══════════════════════════════════════════════════════════════
# PAGE CONFIGURATION
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="UEL PRO Stock Screener",
    layout="wide",
    initial_sidebar_state="collapsed",  # Hide sidebar by default
)

# ══════════════════════════════════════════════════════════════
# CUSTOM CSS — Terminal-Style Dark Mode UI
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Roboto+Mono:ital,wght@0,400;0,500;0,700;1,400&display=swap');

/* ── Root Palette — Neo-Broker: Midnight Navy + Neon Signals ── */
:root {
    /* Backgrounds — deep navy layers */
    --bg-base:         #04091a;
    --bg-panel:        #080f24;
    --bg-control:      #0d172e;
    /* Borders */
    --border:          #162448;
    --border-bright:   #1e3a6b;
    /* Accent palette — neon signals */
    --accent-cyan:     #00ccff;   /* primary CTA / active states    */
    --accent-green:    #00e676;   /* positive / up                   */
    --accent-red:      #ff3d71;   /* negative / down                 */
    --accent-amber:    #ffb300;   /* warning / neutral               */
    --accent-purple:   #a855f7;   /* secondary accent                */
    /* Neon glow helpers */
    --glow-cyan:       rgba(0, 204, 255, 0.35);
    --glow-green:      rgba(0, 230, 118, 0.35);
    --glow-red:        rgba(255, 61, 113, 0.35);
    /* Typography */
    --text-primary:    #e2e8f0;
    --text-secondary:  #7fa8cc;
    --text-muted:      #5a7fa8;  /* raised from #3d5a7a → ~4.6:1 contrast (WCAG AA) */
    /* Font tokens */
    --font-body:       'Outfit', sans-serif;
    --font-mono:       'Roboto Mono', monospace;
}

/* ── Base Overrides — Force Navy background on ALL Streamlit containers ── */
html, body, [class*="css"] {
    font-family: var(--font-body) !important;
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
}

/* Streamlit v1.x main containers */
.stApp,
.main,
.stMain,
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stMainBlockContainer"],
.stMainBlockContainer,
section.main,
.block-container,
[data-testid="block-container"],
[data-testid="stVerticalBlock"],
header[data-testid="stHeader"],
[data-testid="stToolbar"],
footer,
footer[data-testid="stFooter"] {
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
}

/* Remove the default Streamlit white/gradient decoration bar on top */
[data-testid="stDecoration"] {
    display: none !important;
}

/* Ensure column blocks don't bleed white */
[data-testid="column"],
.element-container,
[data-testid="stVerticalBlock"] > div {
    background-color: transparent !important;
}

/* ── Hide Sidebar Toggle ── */
section[data-testid="stSidebar"] {
    display: none;
}

/* ── App Header ── */
.app-header {
    font-family: var(--font-mono);
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, var(--accent-cyan) 0%, var(--accent-purple) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 0.08em;
    padding: 1.5rem 0;
    text-align: center;
    border-bottom: 2px solid var(--border-bright);
    margin-bottom: 2rem;
    filter: drop-shadow(0 0 18px var(--glow-cyan));
}

/* ── Strategy Navigation Pills ── */
.stRadio {
    background: var(--bg-panel);
    padding: 1.5rem;
    border-radius: 12px;
    border: 1px solid var(--border);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}
.stRadio > div { justify-content: center; gap: 1rem; }
.stRadio [role="radiogroup"] { justify-content: center; gap: 1rem; }
.stRadio label {
    font-family: var(--font-mono) !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 0.7rem 1.4rem !important;
    background: var(--bg-control) !important;
    border: 1px solid var(--border-bright) !important;
    border-radius: 6px !important;
    cursor: pointer !important;
    transition: all 0.25s ease !important;
    color: var(--text-primary) !important;
    font-weight: 500 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-width: 140px !important;
}
.stRadio label:hover {
    border-color: var(--accent-cyan) !important;
    color: var(--accent-cyan) !important;
    background: rgba(0, 204, 255, 0.08) !important;
    box-shadow: 0 0 14px var(--glow-cyan);
    transform: translateY(-1px);
}
.stRadio input:checked + label {
    background: linear-gradient(135deg, rgba(0, 204, 255, 0.18), rgba(168, 85, 247, 0.15)) !important;
    color: var(--accent-cyan) !important;
    font-weight: 700 !important;
    border-color: var(--accent-cyan) !important;
    box-shadow: 0 0 20px var(--glow-cyan), inset 0 0 10px rgba(0, 204, 255, 0.08);
}
.stRadio input[type="radio"] {
    opacity: 0 !important;
    position: absolute !important;
}

/* ── Workspace Headers ── */
.workspace-header {
    font-family: var(--font-mono);
    font-size: 1.1rem;
    font-weight: 700;
    margin-bottom: 1.2rem;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid var(--border-bright);
    display: block;   /* full-width so border-bottom spans entire row */
    background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

/* ── KPI Metric Cards ── */
[data-testid="metric-container"] {
    background: linear-gradient(145deg, var(--bg-panel) 0%, var(--bg-control) 100%) !important;
    border: 1px solid var(--border-bright) !important;
    border-radius: 10px !important;
    padding: 1.25rem !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}
[data-testid="metric-container"]:hover {
    transform: translateY(-3px);
    border-color: var(--accent-cyan) !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6), 0 0 18px var(--glow-cyan);
}
[data-testid="metric-container"] > div {
    font-family: var(--font-mono) !important;
}
[data-testid="metric-container"] label {
    font-family: var(--font-mono) !important;
    font-size: 0.75rem !important;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: var(--font-mono) !important;
    font-size: 1.75rem !important;
    color: var(--text-primary) !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}

/* ── Sliders ── */
.stSlider { padding: 1rem 0; }
.stSlider label {
    font-family: var(--font-body) !important;
    color: var(--text-primary) !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
}
.stSlider [data-baseweb="slider"] { padding: 0.5rem 0; }
/* Active track fill */
.stSlider [data-baseweb="slider"] > div > div > div:nth-child(3) {
    background: linear-gradient(90deg, var(--accent-cyan), #0080cc) !important;
    box-shadow: 0 0 12px var(--glow-cyan);
}
/* Inactive track */
.stSlider [data-baseweb="slider"] > div > div > div:nth-child(2) {
    background: var(--border-bright) !important;
}

/* ── Download Button ── */
.stDownloadButton > button {
    background: transparent !important;
    border: 1px solid var(--accent-cyan) !important;
    color: var(--accent-cyan) !important;
    font-family: var(--font-mono) !important;
    font-size: 0.84rem !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.25s ease !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}
.stDownloadButton > button:hover {
    background: rgba(0, 204, 255, 0.12) !important;
    box-shadow: 0 0 18px var(--glow-cyan);
    transform: translateY(-1px);
}

/* ── DataFrames ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border-bright) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
}
[data-testid="stDataFrame"] thead {
    background: linear-gradient(135deg, var(--bg-control) 0%, #0a1428 100%) !important;
}
[data-testid="stDataFrame"] th {
    font-family: var(--font-mono) !important;
    color: var(--accent-cyan) !important;
    font-weight: 700 !important;
    font-size: 0.79rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    padding: 0.9rem 0.75rem !important;
}
[data-testid="stDataFrame"] td {
    font-family: var(--font-mono) !important;
    font-size: 0.88rem !important;
}
[data-testid="stDataFrame"] tbody tr:hover {
    background: rgba(0, 204, 255, 0.04) !important;
    cursor: pointer;
}

/* ── Divider ── */
hr {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, var(--border-bright), transparent) !important;
    margin: 2rem 0 !important;
}

/* ── Footer ── */
.footer {
    margin-top: 4rem;
    padding: 2rem 0;
    text-align: center;
    font-family: var(--font-mono);
    font-size: 0.7rem;
    color: var(--text-muted);
    letter-spacing: 0.1em;
    border-top: 1px solid var(--border);
    background: linear-gradient(180deg, transparent 0%, rgba(8, 15, 36, 0.6) 100%);
}
.footer span { display: inline-block; margin: 0.5rem 0; }

/* ── Info/Warning Boxes ── */
.stAlert {
    border-radius: 8px !important;
    border-left: 3px solid var(--accent-amber) !important;
    background: rgba(255, 179, 0, 0.06) !important;
}

/* ── Ticker Tape ── */
.ticker-tape {
    overflow: hidden;
    white-space: nowrap;
    background: linear-gradient(90deg,
        rgba(4, 9, 26, 0.98)  0%,
        rgba(8, 15, 36, 0.96) 50%,
        rgba(4, 9, 26, 0.98)  100%);
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    padding: 0.55rem 0;
    margin-bottom: 1.5rem;
    position: relative;
    font-family: var(--font-mono);
    font-size: 0.78rem;
    letter-spacing: 0.04em;
}
.ticker-tape::before, .ticker-tape::after {
    content: '';
    position: absolute;
    top: 0; bottom: 0;
    width: 90px;
    z-index: 2;
    pointer-events: none;
}
.ticker-tape::before { left:  0; background: linear-gradient(90deg,  #04091a 0%, transparent 100%); }
.ticker-tape::after  { right: 0; background: linear-gradient(270deg, #04091a 0%, transparent 100%); }
.ticker-content {
    display: inline-block;
    animation: tickerScroll 35s linear infinite;
}
.ticker-content:hover { animation-play-state: paused; }
@keyframes tickerScroll {
    0%   { transform: translateX(0); }
    100% { transform: translateX(-50%); }
}
.tick-item  { display: inline-block; margin: 0 2rem; }
.tick-sym   { color: var(--text-primary); font-weight: 700; }
.tick-price { color: var(--text-secondary); margin: 0 0.4rem; }
.tick-up    { color: var(--accent-green); text-shadow: 0 0 8px var(--glow-green); }
.tick-dn    { color: var(--accent-red);   text-shadow: 0 0 8px var(--glow-red);   }
.tick-sep   { color: var(--border-bright); margin: 0 1rem; }

/* ── Filter Bar (TradingView-style chips) ── */
.filter-bar-wrapper {
    margin: 0.5rem 0 1.2rem;
    padding: 0.8rem 1rem;
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 10px;
}
.filter-bar-title {
    font-family: var(--font-mono);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-muted);
    margin-bottom: 0.5rem;
}
/* Popover trigger buttons → pill chips */
[data-testid="stPopover"] > button {
    background: var(--bg-control) !important;
    border: 1px solid var(--border-bright) !important;
    border-radius: 20px !important;
    color: var(--text-secondary) !important;
    font-family: var(--font-mono) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 0.3rem 0.9rem !important;
    width: 100% !important;
    transition: border-color 0.15s, color 0.15s, box-shadow 0.15s !important;
}
[data-testid="stPopover"] > button:hover {
    border-color: var(--accent-cyan) !important;
    color: var(--accent-cyan) !important;
    box-shadow: 0 0 8px var(--glow-cyan) !important;
}

/* ── Main Tabs ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: var(--bg-panel) !important;
    border-bottom: 1px solid var(--border-bright) !important;
    border-radius: 10px 10px 0 0 !important;
    padding: 0 0.5rem !important;
    gap: 0.25rem !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    font-family: var(--font-mono) !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    color: var(--text-muted) !important;
    padding: 0.7rem 1.2rem !important;
    border-radius: 8px 8px 0 0 !important;
    border: none !important;
    background: transparent !important;
    transition: color 0.2s, background 0.2s !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: var(--accent-cyan) !important;
    background: rgba(0,204,255,0.07) !important;
    border-bottom: 2px solid var(--accent-cyan) !important;
    box-shadow: 0 0 10px var(--glow-cyan) !important;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
    color: var(--text-primary) !important;
    background: rgba(255,255,255,0.03) !important;
}
[data-testid="stTabs"] [data-testid="stVerticalBlock"] {
    padding-top: 1.2rem !important;
}

/* ── Strategy Cards ── */
.strategy-card {
    background: linear-gradient(145deg, var(--bg-panel) 0%, var(--bg-control) 100%);
    border: 1px solid var(--border-bright);
    border-radius: 12px;
    padding: 1.1rem 1.2rem 0.9rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.2s, box-shadow 0.2s, transform 0.15s;
    min-height: 148px;
}
.strategy-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 28px rgba(0,0,0,0.5);
}
.strategy-card--active {
    box-shadow: 0 0 20px rgba(0,204,255,0.18), 0 4px 16px rgba(0,0,0,0.5) !important;
}
.strategy-card-header {
    display: flex;
    align-items: center;
    margin-bottom: 0.2rem;
}

/* ── Decision Lab Scorecard ── */
.score-badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 10px;
    font-family: var(--font-mono);
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.04em;
}
.risk-low    { background: rgba(0,230,118,0.15); color: #00e676; }
.risk-mid    { background: rgba(255,179,0,0.15);  color: #ffb300; }
.risk-high   { background: rgba(255,61,113,0.15); color: #ff3d71; }

/* ── AI Advisor Highlight ── */
.advisor-result {
    background: linear-gradient(135deg, rgba(0,204,255,0.08), rgba(168,85,247,0.07));
    border: 1px solid rgba(0,204,255,0.35);
    border-left: 3px solid var(--accent-cyan);
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    margin-top: 1rem;
}

/* ── Portfolio Mixer Overlap ── */
.overlap-chip {
    display: inline-block;
    background: rgba(168,85,247,0.15);
    border: 1px solid rgba(168,85,247,0.4);
    border-radius: 16px;
    padding: 3px 12px;
    font-family: var(--font-mono);
    font-size: 0.78rem;
    color: #b388ff;
    margin: 2px 3px;
}
.multi-vote {
    display: inline-block;
    background: rgba(0,230,118,0.15);
    border: 1px solid rgba(0,230,118,0.4);
    border-radius: 16px;
    padding: 3px 12px;
    font-family: var(--font-mono);
    font-size: 0.78rem;
    color: #00e676;
    margin: 2px 3px;
}

</style>
""", unsafe_allow_html=True)



# ══════════════════════════════════════════════════════════════
# DATA LOADING
# ══════════════════════════════════════════════════════════════
MOCK_TICKERS = [
    "FALABELLA.SN", "COPEC.SN", "ENELCHILE.SN", "SQM-B.SN", "CMPC.SN",
    "BSANTANDER.SN", "CENCOSUD.SN", "LAN.SN", "COLBUN.SN", "RIPLEY.SN",
    "ITAUCL.SN", "PARAUCO.SN", "CAP.SN", "CHILE.SN", "ENELAM.SN",
    "AGUAS-A.SN", "ANDINA-B.SN", "CCU.SN", "FORUS.SN", "MALLPLAZA.SN",
]


def create_mock_data() -> pd.DataFrame:
    """Generate mock data for demonstration."""
    rng = np.random.default_rng(42)
    n = len(MOCK_TICKERS)
    df = pd.DataFrame({
        "Ticker":          MOCK_TICKERS,
        "Price Close":     rng.uniform(500, 15000, n).round(1),
        "P_E":             rng.uniform(4, 35, n).round(2),
        "P_B":             rng.uniform(0.4, 4.5, n).round(2),
        "Current_Ratio":   rng.uniform(0.8, 4.5, n).round(2),
        "Debt_to_Equity":  rng.uniform(0.1, 2.5, n).round(2),
        "Dividend_Yield":  rng.uniform(0.01, 0.12, n).round(4),
        "Payout_Ratio":    rng.uniform(0.05, 0.95, n).round(3),
        "Rev_Growth_YoY":  rng.uniform(-0.1, 0.45, n).round(4),
        "EPS_Growth_YoY":  rng.uniform(-0.15, 0.55, n).round(4),
        "Gross_Margin":    rng.uniform(0.08, 0.55, n).round(4),
        "Price_6M_Return": rng.uniform(-0.2, 0.6, n).round(4),
        "Volume":          rng.integers(50_000, 5_000_000, n),
        "Vol_Avg_20":      rng.integers(40_000, 4_500_000, n),
        "RSI_14":          rng.uniform(25, 78, n).round(1),
        "MA50":            rng.uniform(480, 14500, n).round(1),
        "MA200":           rng.uniform(450, 14000, n).round(1),
    })
    # Add simulated 6-month price trend (list of 24 weekly prices)
    trends = []
    for i, price in enumerate(df["Price Close"]):
        seed_rng = np.random.default_rng(42 + i)
        returns = seed_rng.normal(0.003, 0.04, 24)  # 24 weekly returns
        path = [float(price)]
        for r in returns:
            path.append(round(path[-1] * (1 + r), 1))
        trends.append(path[1:])  # drop first (same as current price)
    df["6M_Trend"] = trends
    return df


def add_sparklines(df: pd.DataFrame) -> pd.DataFrame:
    """Add 6M_Trend sparkline column to any dataframe (real or mock)."""
    if "6M_Trend" in df.columns:
        # CSV stores lists as strings "[1.0, 2.0, ...]" — parse them back to list
        def _parse(v):
            if isinstance(v, list):
                return v
            if isinstance(v, str):
                try:
                    return ast.literal_eval(v)
                except Exception:
                    return []
            return []
        df = df.copy()
        df["6M_Trend"] = df["6M_Trend"].apply(_parse)
        return df
    rng = np.random.default_rng(99)
    trends = []
    for i, row in df.iterrows():
        price = row.get("Price Close", 1000)
        returns = rng.normal(0.002, 0.035, 24)
        path = [float(price)]
        for r in returns:
            path.append(round(path[-1] * (1 + r), 1))
        trends.append(path[1:])
    df = df.copy()
    df["6M_Trend"] = trends
    return df


@st.cache_data(show_spinner=False)
def load_data(filepath: str = "df_screen_master.csv") -> tuple[pd.DataFrame, bool]:
    """
    Load master CSV file. If not found, use mock data.
    Returns (dataframe, is_mock_data).
    """
    try:
        df = pd.read_csv(filepath, encoding="utf-8")
        STRING_COLS = {"Ticker", "Company_Name", "Sector", "Industry"}
        num_cols = [c for c in df.columns if c not in STRING_COLS]
        for col in num_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df = add_sparklines(df)
        return df, False
    except FileNotFoundError:
        return create_mock_data(), True
    except Exception as e:
        st.warning(f"Lỗi đọc file: {e}. Đang dùng dữ liệu mẫu.")
        return create_mock_data(), True


# ══════════════════════════════════════════════════════════════
# STRATEGY DEFINITIONS  (9 strategies)
# ══════════════════════════════════════════════════════════════
STRATEGIES = {
    "Graham Value": {
        "icon":       "",
        "accent":     "#00d4ff",
        "tagline":    "Benjamin Graham — Giá Trị Cổ Điển",
        "short_desc": "P/E & P/B thấp, thanh khoản mạnh, đòn bẩy thấp.",
        "description": (
            "Triết lý Graham tập trung vào việc tìm kiếm cổ phiếu bị định giá thấp. "
            "Lọc các công ty có <b>P/E & P/B thấp</b>, <b>thanh khoản mạnh</b> "
            "(Current Ratio cao), và <b>đòn bẩy tài chính thận trọng</b> (D/E thấp)."
        ),
        "risk": "Thấp",
    },
    "Income Investing": {
        "icon":       "",
        "accent":     "#00e676",
        "tagline":    "Thu Nhập Thụ Động Bền Vững",
        "short_desc": "Cổ tức cao, payout an toàn, dòng tiền dương.",
        "description": (
            "Xây dựng danh mục tạo <b>dòng tiền định kỳ ổn định</b>. Lọc công ty có "
            "<b>tỷ suất cổ tức vượt lãi suất ngân hàng</b>, <b>payout ratio lành mạnh</b> "
            "và <b>CFO dương đảm bảo khả năng chi trả</b>."
        ),
        "risk": "Thấp",
    },
    "Growth Investing": {
        "icon":       "",
        "accent":     "#ffab40",
        "tagline":    "Tăng Trưởng Doanh Thu & Lợi Nhuận",
        "short_desc": "DT + EPS tăng trưởng mạnh, GARP.",
        "description": (
            "Nhắm đến các công ty có <b>tăng trưởng doanh thu và EPS vượt trội</b>. "
            "Kết hợp với giá đang xu hướng trên MA50, lý tưởng cho "
            "<b>GARP (Tăng Trưởng Ở Mức Giá Hợp Lý)</b>."
        ),
        "risk": "Trung bình",
    },
    "Momentum": {
        "icon":       "",
        "accent":     "#b388ff",
        "tagline":    "Động Lượng Giá & Sức Mạnh Kỹ Thuật",
        "short_desc": "Golden Cross, đột biến khối lượng, RSI không quá mua.",
        "description": (
            "Khai thác <b>hiệu ứng động lượng giá</b>: cổ phiếu tăng mạnh 6 tháng "
            "có xu hướng tiếp tục vượt trội. Lọc theo "
            "<b>Golden Cross (MA50 > MA200)</b>, <b>đột biến khối lượng</b>, "
            "và <b>RSI chưa vào vùng quá mua</b>."
        ),
        "risk": "Cao",
    },
    "Magic Formula": {
        "icon":       "",
        "accent":     "#ff6b9d",
        "tagline":    "Joel Greenblatt — Công Thức Kỳ Diệu",
        "short_desc": "Xếp hạng kép: Earnings Yield cao + ROC cao.",
        "description": (
            "Chiến lược của Joel Greenblatt tìm kiếm <b>công ty chất lượng cao với giá rẻ</b>. "
            "Xếp hạng cổ phiếu theo <b>Earnings Yield</b> (1/P/E) và "
            "<b>Return on Capital</b> (ROA làm proxy), chọn top N tổng hợp."
        ),
        "risk": "Trung bình",
    },
    "Piotroski F-Score": {
        "icon":       "",
        "accent":     "#26c6da",
        "tagline":    "Piotroski — Sức Khỏe Tài Chính 0–9 Điểm",
        "short_desc": "Điểm F-Score ≥ 4: sinh lời, dòng tiền, thanh khoản.",
        "description": (
            "Thang điểm định lượng 0–9 đánh giá <b>sức khỏe tài chính</b>. "
            "Lọc công ty có <b>ROA dương</b>, <b>CFO dương và chất lượng</b>, "
            "<b>thanh khoản tốt</b>, và <b>biên lợi nhuận gộp cao</b>."
        ),
        "risk": "Thấp",
    },
    "Value Investing": {
        "icon":       "",
        "accent":     "#4db6ac",
        "tagline":    "Giá Trị Nội Tại — FCF & Biên LN Dương",
        "short_desc": "P/E<15, P/B<1.5, FCF dương, D/E thấp.",
        "description": (
            "Tìm kiếm cổ phiếu giao dịch <b>dưới giá trị nội tại</b>. "
            "Yêu cầu <b>P/E & P/B thấp</b>, <b>Free Cash Flow dương</b>, "
            "<b>biên lợi nhuận thực chất</b> và <b>đòn bẩy kiểm soát</b>."
        ),
        "risk": "Thấp",
    },
    "Factor Investing": {
        "icon":       "",
        "accent":     "#ffd54f",
        "tagline":    "Đa Nhân Tố: Size · Value · Momentum · Quality",
        "short_desc": "Composite score từ 4 nhân tố học thuật.",
        "description": (
            "Kết hợp <b>4 nhân tố alpha</b> đã kiểm chứng: "
            "<b>Size</b> (vốn hóa nhỏ), <b>Value</b> (P/B thấp), "
            "<b>Momentum</b> (sinh lời 6 tháng) và "
            "<b>Profitability</b> (ROE cao). Chọn top N điểm tổng hợp."
        ),
        "risk": "Trung bình",
    },
    "Quality Investing": {
        "icon":       "",
        "accent":     "#a5d6a7",
        "tagline":    "Chất Lượng Doanh Nghiệp — ROE · FCF · Biên LN",
        "short_desc": "ROE cao, FCF dương, biên gộp mạnh, nợ thấp.",
        "description": (
            "Tập trung vào <b>doanh nghiệp nền tảng vững</b>: "
            "<b>ROE & ROA cao bền vững</b>, <b>biên lợi nhuận gộp mạnh</b>, "
            "<b>dòng tiền tự do dương</b> và <b>tỷ lệ nợ thấp</b>."
        ),
        "risk": "Thấp",
    },
}


# ──────────────────────────────────────────────────────────────
# HÀM LỌC THEO CHIẾN LƯỢC
# ──────────────────────────────────────────────────────────────

def _raw(df: pd.DataFrame, col: str) -> pd.Series:
    """Return <col>_raw if available (real data), else fall back to <col>.

    This is the core separation between display and filtering:
    - <col>       Winsorized  — used for colour scales and charts
    - <col>_raw   Unclipped   — used for ALL filter slider comparisons

    A company with P/E = 180 that has been Winsorized to display-P/E = 42
    must NOT pass a Graham slider set to P/E <= 20.  Without this function
    it would, which is a serious financial logic error.
    """
    raw_col = f"{col}_raw"
    return df[raw_col] if raw_col in df.columns else df[col]


def apply_graham(df: pd.DataFrame, pe_max: float, pb_max: float,
                 cr_min: float, de_max: float) -> pd.DataFrame:
    pe  = _raw(df, "P_E")
    pb  = _raw(df, "P_B")
    cr  = _raw(df, "Current_Ratio")
    de  = _raw(df, "Debt_to_Equity")
    mask = (
        pe.notna()  & (pe  > 0)     & (pe  <= pe_max) &
        pb.notna()  & (pb  > 0)     & (pb  <= pb_max) &
        cr.notna()  & (cr  >= cr_min) &
        de.notna()  & (de  <= de_max)
    )
    return df[mask].copy()


def apply_growth(df: pd.DataFrame, rev_min: float, eps_min: float) -> pd.DataFrame:
    rg = _raw(df, "Rev_Growth_YoY")
    eg = _raw(df, "EPS_Growth_YoY")
    mask = (
        rg.notna() & (rg >= rev_min) &
        eg.notna() & (eg >= eps_min)
    )
    return df[mask].copy()


def apply_momentum(df: pd.DataFrame, rsi_max: float, top_n: int) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)
    if "RSI_14" in df.columns:
        mask &= df["RSI_14"].notna() & (df["RSI_14"] < rsi_max)
    if "Volume" in df.columns and "Vol_Avg_20" in df.columns:
        mask &= df["Volume"].notna() & df["Vol_Avg_20"].notna() & (df["Volume"] > df["Vol_Avg_20"])
    # Golden Cross: MA50 > MA200
    if "MA50" in df.columns and "MA200" in df.columns:
        golden = df["MA50"].notna() & df["MA200"].notna() & (df["MA50"] > df["MA200"])
        mask &= golden
    filtered = df[mask].copy()
    if "Price_6M_Return" in filtered.columns:
        filtered = filtered.sort_values("Price_6M_Return", ascending=False).head(top_n)
    return filtered


def apply_income(df: pd.DataFrame, yield_min: float, payout_max: float) -> pd.DataFrame:
    """Income Investing: dividend yield > threshold, safe payout, positive CFO."""
    dy  = _raw(df, "Dividend_Yield")
    pr  = _raw(df, "Payout_Ratio")
    ocf = _raw(df, "Op_CashFlow")
    mask = (
        dy.notna()  & (dy  >= yield_min) &
        pr.notna()  & (pr  >  0)          & (pr  <= payout_max) &
        ocf.notna() & (ocf >  0)           # CFO dương — bảo kê cổ tức
    )
    return df[mask].copy()


def apply_magic_formula(df: pd.DataFrame, top_n: int) -> pd.DataFrame:
    """Magic Formula (Greenblatt): rank by Earnings Yield + ROC, take top N.

    Earnings Yield proxy = 1 / P_E  (higher is cheaper)
    Return on Capital proxy = ROA   (higher = better quality)
    Exclude financials where sector contains 'Financ' or 'Bank'.
    """
    d = df.copy()
    # Exclude financial sector (banks distort capital structure)
    if "Sector" in d.columns:
        fin_mask = d["Sector"].fillna("").str.contains("Financ|Bank|Insurance", case=False)
        d = d[~fin_mask]

    pe  = _raw(d, "P_E")
    roa = _raw(d, "ROA") if "ROA" in d.columns else pd.Series(np.nan, index=d.index)

    # Only include stocks with valid, positive P/E and positive ROA
    valid = pe.notna() & (pe > 0) & roa.notna() & (roa > 0)
    d = d[valid].copy()
    if d.empty:
        return d

    ey = (1.0 / pe[valid]).values                 # Earnings Yield (higher = better)
    rc = roa[valid].values                         # Return on Capital proxy

    # Rank ascending = best rank = 1 for LOWEST values, so invert for rank
    ey_rank  = pd.Series(ey, index=d.index).rank(ascending=False)   # high EY → rank 1
    roc_rank = pd.Series(rc, index=d.index).rank(ascending=False)   # high ROC → rank 1
    d["_mf_score"] = ey_rank + roc_rank
    d = d.sort_values("_mf_score").head(top_n)
    return d.drop(columns=["_mf_score"])


def apply_piotroski(df: pd.DataFrame, min_score: int) -> pd.DataFrame:
    """Piotroski F-Score: assign 0/1 per criterion, keep stocks ≥ min_score.

    Available F-criteria (from current single-period data):
      F1  ROA > 0
      F2  Op_CashFlow (CFO) > 0
      F3  CFO > ROA (earnings quality — operating cash exceeds accrual earnings)
      F4  Debt_to_Equity < 1  (leverage proxy for improvement)
      F5  Current_Ratio ≥ 1.5 (liquidity proxy)
      F6  Gross_Margin > 0.15 (profitability threshold proxy)
    Max score = 6 (NOTE: 3 YoY criteria require historical data not in CSV).
    """
    d = df.copy()
    roa  = _raw(d, "ROA")          if "ROA"          in d.columns else pd.Series(np.nan, index=d.index)
    ocf  = _raw(d, "Op_CashFlow")  if "Op_CashFlow"  in d.columns else pd.Series(np.nan, index=d.index)
    de   = _raw(d, "Debt_to_Equity")
    cr   = _raw(d, "Current_Ratio")
    gm   = _raw(d, "Gross_Margin")

    score = pd.Series(0, index=d.index)
    score += (roa.notna()  & (roa  > 0)).astype(int)        # F1
    score += (ocf.notna()  & (ocf  > 0)).astype(int)        # F2
    # F3: cash earnings quality — normalise OCF vs ROA by using OCF > median(ROA)
    score += (ocf.notna()  & roa.notna() & (ocf > roa)).astype(int)   # F3
    score += (de.notna()   & (de   < 1.0)).astype(int)      # F4
    score += (cr.notna()   & (cr   >= 1.5)).astype(int)     # F5
    score += (gm.notna()   & (gm   > 0.15)).astype(int)     # F6

    d["_fscore"] = score
    result = d[score >= min_score].copy()
    result = result.sort_values("_fscore", ascending=False).drop(columns=["_fscore"])
    return result


def apply_value(df: pd.DataFrame, pe_max: float, pb_max: float, de_max: float) -> pd.DataFrame:
    """Value Investing: P/E low, P/B low, positive FCF, D/E controlled."""
    pe   = _raw(df, "P_E")
    pb   = _raw(df, "P_B")
    de   = _raw(df, "Debt_to_Equity")
    fcf  = _raw(df, "FCF_Yield") if "FCF_Yield" in df.columns else pd.Series(np.nan, index=df.index)
    gm   = _raw(df, "Gross_Margin")
    mask = (
        pe.notna()  & (pe  > 0)    & (pe  <= pe_max)  &
        pb.notna()  & (pb  > 0)    & (pb  <= pb_max)  &
        de.notna()  & (de  <= de_max)                  &
        gm.notna()  & (gm  > 0)                         # profitable
    )
    # FCF filter only if column exists and has data
    if fcf.notna().sum() > 0:
        mask &= fcf.notna() & (fcf > 0)
    return df[mask].copy()


def apply_factor(df: pd.DataFrame, top_n: int) -> pd.DataFrame:
    """Factor Investing: composite rank of Size + Value + Momentum + Profitability.

    Size factor:         lower Market_Cap → better (small-cap premium)
    Value factor:        lower P/B → better
    Momentum factor:     higher Price_6M_Return → better
    Profitability factor:higher ROE → better
    """
    d = df.copy()
    needed = ["Market_Cap", "P_B", "Price_6M_Return", "ROE"]
    for col in needed:
        if col not in d.columns:
            d[col] = np.nan

    valid = (
        d["Market_Cap"].notna() & d["P_B"].notna() &
        d["Price_6M_Return"].notna() & d["ROE"].notna()
    )
    d = d[valid].copy()
    if d.empty:
        return d

    # Rank each factor (ascending=True for lower-is-better metrics)
    r_size = d["Market_Cap"].rank(ascending=True)   # small cap = rank 1
    r_val  = d["P_B"].rank(ascending=True)           # low P/B = rank 1
    r_mom  = d["Price_6M_Return"].rank(ascending=False)  # high return = rank 1
    r_prof = d["ROE"].rank(ascending=False)           # high ROE = rank 1

    d["_factor_score"] = r_size + r_val + r_mom + r_prof
    d = d.sort_values("_factor_score").head(top_n).drop(columns=["_factor_score"])
    return d


def apply_quality(df: pd.DataFrame, roe_min: float, roa_min: float) -> pd.DataFrame:
    """Quality Investing: high ROE, positive ROA, strong gross margin, positive FCF, low leverage."""
    roe  = _raw(df, "ROE")         if "ROE"         in df.columns else pd.Series(np.nan, index=df.index)
    roa  = _raw(df, "ROA")         if "ROA"         in df.columns else pd.Series(np.nan, index=df.index)
    gm   = _raw(df, "Gross_Margin")
    ocf  = _raw(df, "Op_CashFlow") if "Op_CashFlow" in df.columns else pd.Series(np.nan, index=df.index)
    fcf  = _raw(df, "FCF_Yield")   if "FCF_Yield"   in df.columns else pd.Series(np.nan, index=df.index)
    de   = _raw(df, "Debt_to_Equity")
    mask = (
        roe.notna()  & (roe  >= roe_min)  &
        roa.notna()  & (roa  >= roa_min)  &
        gm.notna()   & (gm   >= 0.20)     &   # Gross margin ≥ 20%
        ocf.notna()  & (ocf  >  0)         &
        de.notna()   & (de   <  2.0)
    )
    if fcf.notna().sum() > 0:
        mask &= fcf.notna() & (fcf > 0)
    return df[mask].copy()


# ─── Unified dispatcher ─────────────────────────────────────────────────────

def apply_strategy(df: pd.DataFrame, strategy: str, params: dict) -> pd.DataFrame:
    """Route to the correct apply_* function using params dict."""
    fn_map = {
        "Graham Value":      lambda: apply_graham(df, **params),
        "Income Investing":  lambda: apply_income(df, **params),
        "Growth Investing":  lambda: apply_growth(df, **params),
        "Momentum":          lambda: apply_momentum(df, **params),
        "Magic Formula":     lambda: apply_magic_formula(df, **params),
        "Piotroski F-Score": lambda: apply_piotroski(df, **params),
        "Value Investing":   lambda: apply_value(df, **params),
        "Factor Investing":  lambda: apply_factor(df, **params),
        "Quality Investing": lambda: apply_quality(df, **params),
    }
    return fn_map[strategy]() if strategy in fn_map else df.copy()


# ─── Default params for card preview counts ─────────────────────────────────

STRATEGY_DEFAULT_PARAMS = {
    "Graham Value":      dict(pe_max=15.0, pb_max=1.5, cr_min=2.0, de_max=1.0),
    "Income Investing":  dict(yield_min=0.05, payout_max=0.70),
    "Growth Investing":  dict(rev_min=0.20, eps_min=0.20),
    "Momentum":          dict(rsi_max=70, top_n=20),
    "Magic Formula":     dict(top_n=20),
    "Piotroski F-Score": dict(min_score=4),
    "Value Investing":   dict(pe_max=15.0, pb_max=1.5, de_max=1.5),
    "Factor Investing":  dict(top_n=20),
    "Quality Investing": dict(roe_min=0.10, roa_min=0.05),
}




# ══════════════════════════════════════════════════════════════
# CHART FUNCTIONS (Flat Design)
# ══════════════════════════════════════════════════════════════
PAPER_BG        = "#04091a"   # matches --bg-base
PLOT_BG         = "#080f24"   # matches --bg-panel
FONT_FAMILY     = "Roboto Mono, monospace"
GRID_COLOR      = "#162448"   # matches --border


def _base_layout(title: str, accent: str) -> dict:
    """Base layout for Plotly charts — tuned margins and readable title."""
    return dict(
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(family=FONT_FAMILY, size=13, color=accent),
            x=0.01, xanchor="left", pad=dict(t=4),
        ),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(family=FONT_FAMILY, color="#7fa8cc", size=11),
        margin=dict(l=56, r=28, t=52, b=48),
        xaxis=dict(
            gridcolor=GRID_COLOR, gridwidth=0.5, zeroline=False,
            tickfont=dict(family=FONT_FAMILY, size=10),
        ),
        yaxis=dict(
            gridcolor=GRID_COLOR, gridwidth=0.5, zeroline=False,
            tickfont=dict(family=FONT_FAMILY, size=10),
        ),
        hoverlabel=dict(
            bgcolor="#0d172e",
            bordercolor="#1e3a6b",
            font=dict(family=FONT_FAMILY, size=12, color="#e2e8f0"),
        ),
    )


def chart_radar(df: pd.DataFrame, ticker: str, accent: str) -> go.Figure:
    """Radar chart with 5 axes: Value, Growth, Momentum, Liquidity, Dividend."""
    if df.empty or ticker not in df["Ticker"].values:
        return go.Figure()

    row = df[df["Ticker"] == ticker].iloc[0]

    def _norm(val, lo, hi, invert=False):
        """Normalize val to 0-100 within [lo, hi]."""
        if pd.isna(val):
            return 50.0
        v = float(np.clip(val, lo, hi))
        score = (v - lo) / (hi - lo) * 100
        return round(100 - score if invert else score, 1)

    # ── 5 composite scores ──────────────────────────────────
    pe   = row.get("P_E",            15)
    pb   = row.get("P_B",            1.5)
    value_score = (_norm(pe, 5, 35, invert=True) + _norm(pb, 0.3, 5, invert=True)) / 2

    rev  = row.get("Rev_Growth_YoY", 0)
    eps  = row.get("EPS_Growth_YoY", 0)
    growth_score = (_norm(rev, -0.1, 0.5) + _norm(eps, -0.15, 0.6)) / 2

    ret6 = row.get("Price_6M_Return", 0)
    rsi  = row.get("RSI_14",          50)
    mom_score = (_norm(ret6, -0.2, 0.6) + _norm(rsi, 20, 80)) / 2

    cr   = row.get("Current_Ratio",   2)
    de   = row.get("Debt_to_Equity",  1)
    liq_score = (_norm(cr, 0.5, 5) + _norm(de, 0, 3, invert=True)) / 2

    yld  = row.get("Dividend_Yield",  0)
    pay  = row.get("Payout_Ratio",    0.5)
    div_score = (_norm(yld, 0, 0.12) + _norm(pay, 0, 1, invert=True)) / 2
    # ────────────────────────────────────────────────────────

    categories = ["Giá Trị", "Tăng Trưởng", "Động Lượng", "Thanh Khoản", "Cổ Tức"]
    scores     = [value_score, growth_score, mom_score, liq_score, div_score]
    scores_plot = scores + [scores[0]]          # close the polygon
    cats_plot   = categories + [categories[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores_plot,
        theta=cats_plot,
        fill="toself",
        fillcolor=f"{accent}28",
        line=dict(color=accent, width=2),
        name=ticker,
        hovertemplate="<b>%{theta}</b><br>Score: %{r:.1f}/100<extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor=PLOT_BG,
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(color="#7a8899", size=9),
                gridcolor=GRID_COLOR,
                linecolor=GRID_COLOR,
            ),
            angularaxis=dict(
                tickfont=dict(color=accent, size=11, family=FONT_FAMILY),
                gridcolor=GRID_COLOR,
                linecolor=GRID_COLOR,
            ),
        ),
        showlegend=False,
        paper_bgcolor=PAPER_BG,
        font=dict(family=FONT_FAMILY, color="#7a8899"),
        title=dict(
            text=f"<b>{ticker}</b> — Radar Đa Nhân Tố",
            font=dict(color=accent, size=14, family=FONT_FAMILY),
            x=0.5,
        ),
        height=420,
        margin=dict(l=60, r=60, t=60, b=40),
    )
    return fig


def chart_quadrant_scatter(df: pd.DataFrame, strategy: str, accent: str) -> go.Figure:
    """Scatter plot split into 4 quadrants by median X/Y lines."""
    axis_map = {
        "Graham Value":      ("P_E",             "P_B",             "Bội Số P/E",                 "Bội Số P/B"),
        "Income Investing":  ("Dividend_Yield",   "Payout_Ratio",    "Tỷ Suất Cổ Tức",             "Tỷ Lệ Chi Trả"),
        "Growth Investing":  ("Rev_Growth_YoY",   "EPS_Growth_YoY",  "Tăng Trưởng Doanh Thu YoY",  "Tăng Trưởng EPS YoY"),
        "Momentum":          ("Price_6M_Return",  "RSI_14",          "Tỷ Suất Sinh Lời 6 Tháng",   "RSI(14)"),
        "Magic Formula":     ("P_E",              "ROA",             "Bội Số P/E",                 "ROA (%)"),
        "Piotroski F-Score": ("Current_Ratio",    "Gross_Margin",    "Tỷ Số Thanh Khoản",          "Biên LN Gộp"),
        "Value Investing":   ("P_E",              "FCF_Yield",       "Bội Số P/E",                 "FCF Yield (%)"),
        "Factor Investing":  ("P_B",              "ROE",             "Bội Số P/B",                 "ROE (%)"),
        "Quality Investing": ("ROE",              "Gross_Margin",    "ROE (%)",                    "Biên LN Gộp"),
    }
    if strategy not in axis_map or df.empty:
        return go.Figure()

    xcol, ycol, xlabel, ylabel = axis_map[strategy]
    if xcol not in df.columns or ycol not in df.columns:
        return go.Figure()

    d = df.dropna(subset=[xcol, ycol]).head(40).copy()
    if len(d) < 2:
        return go.Figure()

    # Scale percentage columns for display
    xvals = d[xcol] * 100 if xcol in ("Dividend_Yield", "Rev_Growth_YoY", "EPS_Growth_YoY", "Price_6M_Return", "Payout_Ratio") else d[xcol]
    yvals = d[ycol] * 100 if ycol in ("Dividend_Yield", "Rev_Growth_YoY", "EPS_Growth_YoY", "Price_6M_Return", "Payout_Ratio") else d[ycol]

    mx = float(xvals.median())
    my = float(yvals.median())

    # Color each point by quadrant
    def _quad_color(x, y):
        if x >= mx and y >= my:   return "#00e676"   # top-right  = best (neon green)
        if x < mx  and y >= my:   return "#ffb300"   # top-left   (amber)
        if x >= mx and y < my:    return accent       # bottom-right
        return "#ff3d71"                              # bottom-left = weakest (neon red)

    colors = [_quad_color(x, y) for x, y in zip(xvals, yvals)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=xvals, y=yvals,
        mode="markers+text",
        text=d["Ticker"],
        textposition="top center",
        textfont=dict(size=9, color="#7a8899"),
        marker=dict(size=11, color=colors, line=dict(color=PAPER_BG, width=1), opacity=0.88),
        hovertemplate=f"<b>%{{text}}</b><br>{xlabel}: %{{x:.2f}}<br>{ylabel}: %{{y:.2f}}<extra></extra>",
    ))

    # Median cross-hair lines
    fig.add_vline(x=mx, line_dash="dash", line_color="#4a5568", line_width=1.2,
                  annotation_text=f"Median {xlabel[:6]}", annotation_font_color="#64748b",
                  annotation_font_size=9)
    fig.add_hline(y=my, line_dash="dash", line_color="#4a5568", line_width=1.2,
                  annotation_text=f"Median {ylabel[:6]}", annotation_font_color="#64748b",
                  annotation_font_size=9)

    # Quadrant labels fixed to corners (paper coords — immune to outliers)
    annotations = [
        dict(x=0.98, y=0.97, xref="paper", yref="paper",
             text="Vượt Trội",   showarrow=False, xanchor="right", yanchor="top",
             font=dict(color="#00e676", size=11, family=FONT_FAMILY),
             bgcolor="rgba(0,230,118,0.08)", bordercolor="#00e676", borderwidth=1, borderpad=4),
        dict(x=0.02, y=0.97, xref="paper", yref="paper",
             text="Cao Y", showarrow=False, xanchor="left",  yanchor="top",
             font=dict(color="#ffb300", size=11, family=FONT_FAMILY),
             bgcolor="rgba(255,179,0,0.08)", bordercolor="#ffb300", borderwidth=1, borderpad=4),
        dict(x=0.98, y=0.05, xref="paper", yref="paper",
             text="Cao X", showarrow=False, xanchor="right", yanchor="bottom",
             font=dict(color=accent,   size=11, family=FONT_FAMILY),
             bgcolor=f"rgba(0,204,255,0.08)", bordercolor=accent, borderwidth=1, borderpad=4),
        dict(x=0.02, y=0.05, xref="paper", yref="paper",
             text="Yếu",   showarrow=False, xanchor="left",  yanchor="bottom",
             font=dict(color="#ff3d71", size=11, family=FONT_FAMILY),
             bgcolor="rgba(255,61,113,0.08)", bordercolor="#ff3d71", borderwidth=1, borderpad=4),
    ]

    layout = _base_layout(f"{strategy} — Phân Tích Góc Phần Tư ({xlabel} vs {ylabel})", accent)
    layout.update(
        xaxis_title=xlabel, yaxis_title=ylabel,
        height=440,
        annotations=annotations,
    )
    fig.update_layout(**layout)
    return fig



# ══════════════════════════════════════════════════════════════
# DEEP DIVE MODAL DIALOG
# ══════════════════════════════════════════════════════════════

@st.dialog("Phân Tích Chi Tiết Cổ Phiếu", width="large")
def show_deep_dive(ticker: str, df: pd.DataFrame, strategy: str, accent: str) -> None:
    """Full-screen modal with Radar chart and key metrics for selected stock."""
    if ticker not in df["Ticker"].values:
        st.error(f"Không có dữ liệu cho {ticker}")
        return

    row = df[df["Ticker"] == ticker].iloc[0]

    # ── Row 1: hero metrics ─────────────────────────────────
    st.markdown(f"### <span style='color:{accent}'>{ticker}</span> — Phân Tích Chi Tiết",
                unsafe_allow_html=True)
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Giá", f"${row.get('Price Close', 0):,.0f}")
    with m2:
        rsi_val = row.get("RSI_14")
        delta_rsi = "Quá Mua" if rsi_val and rsi_val > 70 else ("Quá Bán" if rsi_val and rsi_val < 30 else "Trung Tính")
        st.metric("RSI(14)", f"{rsi_val:.1f}" if rsi_val and pd.notna(rsi_val) else "N/A", delta=delta_rsi)
    with m3:
        ma50 = row.get("MA50")
        if ma50 and pd.notna(ma50):
            pct = (row["Price Close"] / ma50 - 1) * 100
            st.metric("So MA50", f"${ma50:,.0f}", delta=f"{pct:+.1f}%")
        else:
            st.metric("So MA50", "N/A")
    with m4:
        ma200 = row.get("MA200")
        if ma200 and pd.notna(ma200):
            pct200 = (row["Price Close"] / ma200 - 1) * 100
            st.metric("So MA200", f"${ma200:,.0f}", delta=f"{pct200:+.1f}%")
        else:
            st.metric("So MA200", "N/A")
    with m5:
        ret6 = row.get("Price_6M_Return")
        st.metric("Sinh Lời 6T", f"{ret6*100:+.1f}%" if ret6 and pd.notna(ret6) else "N/A")

    st.divider()

    # ── Row 2: Radar chart ──────────────────────────────────
    fig_r = chart_radar(df, ticker, accent)
    if fig_r.data:
        st.plotly_chart(fig_r, use_container_width=True, config={"scrollZoom": True})

    # ── Row 3: Fundamental metrics table ───────────────────
    st.markdown("#### Tổng Quan Cơ Bản")
    snapshot_cols = [
        ("Bội Số P/E",          row.get("P_E"),            "{:.2f}"),
        ("Bội Số P/B",          row.get("P_B"),             "{:.2f}"),
        ("Thanh Khoản Hiện Hành", row.get("Current_Ratio"),   "{:.2f}"),
        ("Nợ/Vốn Chủ Sở Hữu",   row.get("Debt_to_Equity"),  "{:.2f}"),
        ("Tỷ Suất Cổ Tức",    row.get("Dividend_Yield"),  "{:.2%}"),
        ("Tỷ Lệ Chi Trả",      row.get("Payout_Ratio"),    "{:.1%}"),
        ("Tăng Trưởng DT YoY",  row.get("Rev_Growth_YoY"),  "{:+.1%}"),
        ("Tăng Trưởng EPS YoY", row.get("EPS_Growth_YoY"),  "{:+.1%}"),
        ("Biên LN Gộp",         row.get("Gross_Margin"),     "{:.1%}"),
    ]
    c1, c2, c3 = st.columns(3)
    for i, (label, val, fmt) in enumerate(snapshot_cols):
        col = [c1, c2, c3][i % 3]
        with col:
            try:
                display = fmt.format(val) if val is not None and pd.notna(val) else "N/A"
            except Exception:
                display = "N/A"
            st.markdown(
                f"<div style='padding:0.5rem 0; border-bottom:1px solid #162448;'>"
                f"<span style='color:#7fa8cc;font-size:0.82rem;letter-spacing:0.05em;text-transform:uppercase;'>{label}</span><br>"
                f"<span style='color:{accent};font-weight:700;font-size:1.05rem;font-family:Roboto Mono,monospace;'>{display}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ══════════════════════════════════════════════════════════════

# ──────────────────────────────────────────────────────────────
# HEADER: App Branding
# ──────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────
# DATA LOADING — once at the top, reused everywhere
# ──────────────────────────────────────────────────────────────
df_all, is_mock = load_data("df_screen_master.csv")

st.markdown("""
<div class="app-header">
    UEL PRO STOCK SCREENER — Thị Trường Chile
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# TICKER TAPE — built from already-loaded df_all
# ──────────────────────────────────────────────────────────────
_tape_sample = df_all.sample(min(20, len(df_all)), random_state=7).reset_index(drop=True)

def _build_ticker_tape(df_sample: pd.DataFrame) -> str:
    items = []
    rng_t = np.random.default_rng(7)
    for _, r in df_sample.iterrows():
        sym   = r.get("Ticker", "???").replace(".SN", "")
        price = r.get("Price Close", 0)
        chg   = float(rng_t.uniform(-4.5, 6.0))
        css   = "tick-up" if chg >= 0 else "tick-dn"
        arrow = "▲" if chg >= 0 else "▼"
        items.append(
            f'<span class="tick-item">'
            f'<span class="tick-sym">{sym}</span>'
            f'<span class="tick-price">{price:,.0f}</span>'
            f'<span class="{css}">{arrow}{abs(chg):.2f}%</span>'
            f'</span>'
            f'<span class="tick-sep">│</span>'
        )
    inner = "".join(items)
    # Duplicate for seamless loop
    return (
        '<div class="ticker-tape">'
        f'<div class="ticker-content">{inner}{inner}</div>'
        '</div>'
    )

st.markdown(_build_ticker_tape(_tape_sample), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════
if "sel_strat"  not in st.session_state:
    st.session_state.sel_strat = "Graham Value"

# ══════════════════════════════════════════════════════════════
# MAIN TABS
# ══════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    " Strategy Hub",
    " Decision Lab",
    " Backtest Arena",
    " Portfolio Mixer",
])


# ──────────────────────────────────────────────────────────────
# SHARED HELPERS
# ──────────────────────────────────────────────────────────────

def _render_results(df_all: pd.DataFrame, strategy: str, params: dict, accent: str) -> None:
    """Render KPI cards, data table, deep-dive and quadrant chart for a given strategy+params."""

    with st.spinner("Đang áp dụng bộ lọc..."):
        try:
            df_filtered = apply_strategy(df_all, strategy, params)
        except Exception as e:
            st.error(f"Lỗi khi áp dụng bộ lọc: {e}")
            df_filtered = pd.DataFrame()

    total_scanned = len(df_all)
    total_passed  = len(df_filtered)
    pass_rate     = (total_passed / total_scanned * 100) if total_scanned > 0 else 0

    if strategy in ("Graham Value", "Growth Investing", "Value Investing",
                    "Magic Formula", "Piotroski F-Score") and not df_filtered.empty:
        avg_metric = df_filtered["P_E"].median() if "P_E" in df_filtered.columns else float("nan")
        metric_label, metric_value = "P/E Trung Vị", f"{avg_metric:.1f}x"
    elif strategy in ("Income Investing",) and not df_filtered.empty:
        avg_metric = df_filtered["Dividend_Yield"].median() * 100 if "Dividend_Yield" in df_filtered.columns else float("nan")
        metric_label, metric_value = "Tỷ Suất CT TV", f"{avg_metric:.2f}%"
    elif strategy == "Quality Investing" and not df_filtered.empty:
        avg_metric = df_filtered["ROE"].median() * 100 if "ROE" in df_filtered.columns and df_filtered["ROE"].notna().any() else float("nan")
        metric_label, metric_value = "ROE Trung Vị", f"{avg_metric:.1f}%"
    else:
        avg_metric = df_filtered["Price_6M_Return"].median() * 100 if "Price_6M_Return" in df_filtered.columns and not df_filtered.empty else float("nan")
        metric_label, metric_value = "Sinh Lời 6T TV", f"{avg_metric:.1f}%"

    st.markdown('<div class="workspace-header">Tổng Quan Danh Mục</div>', unsafe_allow_html=True)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Tổng Quét",   total_scanned)
    kpi2.metric("Qua Bộ Lọc", total_passed)
    kpi3.metric("Tỷ Lệ Lọc",  f"{pass_rate:.1f}%")
    kpi4.metric(metric_label,  metric_value if not pd.isna(avg_metric) else "N/A")

    st.divider()

    st.markdown(f'<div class="workspace-header">Kết Quả — {total_passed} Cổ Phiếu</div>',
                unsafe_allow_html=True)

    if df_filtered.empty:
        st.info("Không có cổ phiếu nào thỏa điều kiện. Hãy thử điều chỉnh lại tham số.")
        return

    base_cols  = ["Ticker", "Price Close"]
    extra_map  = {
        "Graham Value":      ["P_E", "P_B", "Current_Ratio", "Debt_to_Equity", "Gross_Margin"],
        "Income Investing":  ["Dividend_Yield", "Payout_Ratio", "Rev_Growth_YoY", "EPS_Growth_YoY"],
        "Growth Investing":  ["Rev_Growth_YoY", "EPS_Growth_YoY", "Gross_Margin", "P_E", "RSI_14"],
        "Momentum":          ["Price_6M_Return", "RSI_14", "Volume", "Rev_Growth_YoY", "MA50"],
        "Magic Formula":     ["P_E", "ROA", "ROE", "Gross_Margin", "Price_6M_Return"],
        "Piotroski F-Score": ["ROA", "Gross_Margin", "Current_Ratio", "Debt_to_Equity"],
        "Value Investing":   ["P_E", "P_B", "FCF_Yield", "Gross_Margin", "Debt_to_Equity"],
        "Factor Investing":  ["Market_Cap", "P_B", "Price_6M_Return", "ROE"],
        "Quality Investing": ["ROE", "ROA", "Gross_Margin", "FCF_Yield", "Debt_to_Equity"],
    }
    display_cols = base_cols + [c for c in extra_map.get(strategy, []) if c in df_filtered.columns]
    df_show = df_filtered[display_cols].reset_index(drop=True)

    sparkline_map = {}
    if "6M_Trend" in df_filtered.columns:
        for _, sr in df_filtered.iterrows():
            sparkline_map[sr["Ticker"]] = sr["6M_Trend"]

    column_config = {
        "Ticker":          TextColumn("Ticker", width="medium"),
        "Price Close":     NumberColumn("Price",           format="%.0f",    width="small"),
        "P_E":             NumberColumn("P/E",             format="%.1fx",   width="small"),
        "P_B":             NumberColumn("P/B",             format="%.2fx",   width="small"),
        "Current_Ratio":   NumberColumn("TK Hiện Hành",   format="%.2f",    width="small"),
        "Debt_to_Equity":  NumberColumn("Nợ/VCSH",        format="%.2f",    width="small"),
        "ROE":             NumberColumn("ROE",             format="%+.1f%%", width="small"),
        "ROA":             NumberColumn("ROA",             format="%+.1f%%", width="small"),
        "FCF_Yield":       NumberColumn("FCF Yield",       format="%+.1f%%", width="small"),
        "Market_Cap":      NumberColumn("Vốn Hóa (M)",    format="%.0f",    width="small"),
        "MA50":            NumberColumn("MA50",            format="%.0f",    width="small"),
        "Dividend_Yield":  ProgressColumn("Tỷ Suất CT",   format="%.2f%%",  min_value=0, max_value=30,  width="medium"),
        "Payout_Ratio":    ProgressColumn("Tỷ Lệ CT",     format="%.1f%%",  min_value=0, max_value=100, width="medium"),
        "Gross_Margin":    ProgressColumn("Biên LN Gộp",  format="%.1f%%",  min_value=0, max_value=100, width="medium"),
        "Rev_Growth_YoY":  NumberColumn("Tăng DT",        format="%+.1f%%", width="small"),
        "EPS_Growth_YoY":  NumberColumn("Tăng EPS",       format="%+.1f%%", width="small"),
        "Price_6M_Return": NumberColumn("Sinh Lời 6T",    format="%+.1f%%", width="small"),
        "RSI_14":          NumberColumn("RSI(14)",         format="%.1f",    width="small"),
        "Volume":          NumberColumn("Khối Lượng",      format="%d",      width="medium"),
        "6M_Trend":        LineChartColumn("Xu Thế 6T",   width="medium",   y_min=None, y_max=None),
    }

    df_display = df_show.copy()
    pct_cols = ["Dividend_Yield", "Payout_Ratio", "Gross_Margin",
                "Rev_Growth_YoY", "EPS_Growth_YoY", "Price_6M_Return",
                "ROE", "ROA", "FCF_Yield"]
    for col in pct_cols:
        if col in df_display.columns:
            df_display[col] = df_display[col] * 100

    if sparkline_map:
        df_display["6M_Trend"] = df_display["Ticker"].map(sparkline_map)

    visible_cols = [c for c in df_display.columns if c != "6M_Trend"]
    if "6M_Trend" in df_display.columns:
        visible_cols.append("6M_Trend")

    selection = st.dataframe(
        df_display,
        column_config=column_config,
        column_order=visible_cols,
        hide_index=True,
        use_container_width=True,
        height=min(80 + len(df_display) * 35, 520),
        on_select="rerun",
        selection_mode="single-row",
    )

    csv_bytes = df_filtered.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        label="Tải Xuống CSV",
        data=csv_bytes,
        file_name=f"{strategy.replace(' ', '_').lower()}_results.csv",
        mime="text/csv",
    )

    if selection and selection.selection and selection.selection.rows:
        sel_idx    = selection.selection.rows[0]
        sel_ticker = df_show.iloc[sel_idx]["Ticker"]
        st.toast(f"Phân Tích Chi Tiết: **{sel_ticker}**")
        show_deep_dive(sel_ticker, df_filtered, strategy, accent)

    st.divider()
    if not df_filtered.empty:
        st.markdown('<div class="workspace-header">Phân Tích Góc Phần Tư</div>', unsafe_allow_html=True)
        fig_q = chart_quadrant_scatter(df_filtered, strategy, accent)
        if fig_q.data:
            st.plotly_chart(fig_q, use_container_width=True, config={"scrollZoom": True})


def _build_param_chips(strategy: str) -> dict:
    """Render strategy-specific popover chips; return params dict."""
    params = {}
    st.markdown('<div class="filter-bar-wrapper">', unsafe_allow_html=True)
    accent = STRATEGIES[strategy]["accent"]
    st.markdown(
        f'<div class="filter-bar-title" style="color:{accent}"> Tinh Chỉnh Tham Số — {STRATEGIES[strategy]["tagline"]}</div>',
        unsafe_allow_html=True,
    )

    if strategy == "Graham Value":
        c = st.columns(4, gap="small")
        with c[0]:
            with st.popover(" P/E Tối Đa", use_container_width=True):
                params["pe_max"] = st.slider("Giới hạn trên P/E", 0.0, 50.0, 15.0, 0.5, key="gv_pe")
        with c[1]:
            with st.popover(" P/B Tối Đa", use_container_width=True):
                params["pb_max"] = st.slider("Giới hạn trên P/B", 0.0, 10.0, 1.5, 0.1, key="gv_pb")
        with c[2]:
            with st.popover(" TK Min", use_container_width=True):
                params["cr_min"] = st.slider("Current Ratio tối thiểu", 0.0, 6.0, 2.0, 0.1, key="gv_cr")
        with c[3]:
            with st.popover(" Nợ/Vốn Max", use_container_width=True):
                params["de_max"] = st.slider("D/E tối đa", 0.0, 5.0, 1.0, 0.1, key="gv_de")

    elif strategy == "Income Investing":
        c = st.columns(2, gap="small")
        with c[0]:
            with st.popover(" Cổ Tức Min (%)", use_container_width=True):
                params["yield_min"] = st.slider("Tỷ suất cổ tức tối thiểu (%)", 0.0, 20.0, 5.0, 0.5, key="ii_dy") / 100
        with c[1]:
            with st.popover(" Payout Max (%)", use_container_width=True):
                params["payout_max"] = st.slider("Payout Ratio tối đa (%)", 0.0, 100.0, 70.0, 1.0, key="ii_pr") / 100

    elif strategy == "Growth Investing":
        c = st.columns(2, gap="small")
        with c[0]:
            with st.popover(" DT Tăng Min (%)", use_container_width=True):
                params["rev_min"] = st.slider("Tăng trưởng DT tối thiểu (%)", 0.0, 100.0, 20.0, 1.0, key="gi_rv") / 100
        with c[1]:
            with st.popover(" EPS Tăng Min (%)", use_container_width=True):
                params["eps_min"] = st.slider("Tăng trưởng EPS tối thiểu (%)", 0.0, 100.0, 20.0, 1.0, key="gi_ep") / 100

    elif strategy == "Momentum":
        c = st.columns(2, gap="small")
        with c[0]:
            with st.popover(" RSI Tối Đa", use_container_width=True):
                params["rsi_max"] = st.slider("RSI tối đa (tránh quá mua)", 50, 100, 70, 1, key="mo_rs")
        with c[1]:
            with st.popover(" Top N", use_container_width=True):
                params["top_n"] = st.slider("Số lượng cổ phiếu", 5, 50, 20, 1, key="mo_tn")

    elif strategy == "Magic Formula":
        with st.columns([1, 2, 1])[1]:
            with st.popover(" Top N Cổ Phiếu", use_container_width=True):
                params["top_n"] = st.slider("Số cổ phiếu chọn (xếp hạng kép)", 5, 50, 20, 1, key="mf_tn")

    elif strategy == "Piotroski F-Score":
        with st.columns([1, 2, 1])[1]:
            with st.popover(" F-Score Tối Thiểu", use_container_width=True):
                params["min_score"] = st.slider("Điểm F-Score tối thiểu (max 6)", 1, 6, 4, 1, key="pf_ms")

    elif strategy == "Value Investing":
        c = st.columns(3, gap="small")
        with c[0]:
            with st.popover(" P/E Tối Đa", use_container_width=True):
                params["pe_max"] = st.slider("Giới hạn trên P/E", 0.0, 50.0, 15.0, 0.5, key="vi_pe")
        with c[1]:
            with st.popover(" P/B Tối Đa", use_container_width=True):
                params["pb_max"] = st.slider("Giới hạn trên P/B", 0.0, 10.0, 1.5, 0.1, key="vi_pb")
        with c[2]:
            with st.popover(" D/E Tối Đa", use_container_width=True):
                params["de_max"] = st.slider("D/E tối đa", 0.0, 5.0, 1.5, 0.1, key="vi_de")

    elif strategy == "Factor Investing":
        with st.columns([1, 2, 1])[1]:
            with st.popover(" Top N Composite", use_container_width=True):
                params["top_n"] = st.slider("Số cổ phiếu đầu bảng (4 nhân tố)", 5, 50, 20, 1, key="fi_tn")

    elif strategy == "Quality Investing":
        c = st.columns(2, gap="small")
        with c[0]:
            with st.popover(" ROE Min (%)", use_container_width=True):
                params["roe_min"] = st.slider("ROE tối thiểu (%)", 0.0, 50.0, 10.0, 1.0, key="qi_roe") / 100
        with c[1]:
            with st.popover(" ROA Min (%)", use_container_width=True):
                params["roa_min"] = st.slider("ROA tối thiểu (%)", 0.0, 30.0, 5.0, 0.5, key="qi_roa") / 100

    st.markdown("</div>", unsafe_allow_html=True)
    return params


# ══════════════════════════════════════════════════════════════
# TAB 1 — STRATEGY HUB
# ══════════════════════════════════════════════════════════════
with tab1:
    strategy = st.session_state.sel_strat
    meta     = STRATEGIES[strategy]
    accent   = meta["accent"]

    # ── Data source warning ────────────────────────────────
    if is_mock:
        st.warning(
            "**Không tìm thấy `df_screen_master.csv`** — đang dùng **dữ liệu mẫu** để minh họa."
        )

    # ── 3 × 3 Strategy Cards ──────────────────────────────
    st.markdown('<div class="workspace-header">Chọn Chiến Lược Đầu Tư</div>', unsafe_allow_html=True)
    card_cols = st.columns(3, gap="medium")
    total_n   = len(df_all)
    strat_keys = list(STRATEGIES.keys())

    for i, (skey, smeta) in enumerate(STRATEGIES.items()):
        col = card_cols[i % 3]
        # Count passing default params
        try:
            _cnt = len(apply_strategy(df_all, skey, STRATEGY_DEFAULT_PARAMS[skey]))
        except Exception:
            _cnt = 0
        is_sel       = (strategy == skey)
        bdr          = smeta["accent"] if is_sel else "#1e3a6b"
        shadow_class = "strategy-card--active" if is_sel else ""
        badge        = (
            f'<span class="score-badge" style="background:rgba(0,204,255,0.15);'
            f'color:{smeta["accent"]};margin-left:6px;font-size:0.62rem;"> ACTIVE</span>'
            if is_sel else ""
        )
        with col:
            st.markdown(f"""
<div class="strategy-card {shadow_class}" style="border-color:{bdr};">
  <div class="strategy-card-header">
    <span style="font-size:1.4rem">{smeta['icon']}</span>
    <span style="margin-left:0.5rem;color:{smeta['accent']};font-family:'Roboto Mono',monospace;
          font-size:0.78rem;font-weight:700;text-transform:uppercase;letter-spacing:0.07em">{skey}</span>
    {badge}
  </div>
  <div style="color:#7fa8cc;font-size:0.76rem;margin:0.25rem 0 0.4rem;">{smeta['tagline']}</div>
  <div style="color:#3a5a7a;font-size:0.70rem;line-height:1.4;margin-bottom:0.55rem;">{smeta['short_desc']}</div>
  <div style="display:flex;justify-content:space-between;align-items:center;
       padding-top:0.45rem;border-top:1px solid #162448;">
    <span style="font-family:'Roboto Mono',monospace;font-size:0.68rem;color:#4a6080;">Qua lọc (mặc định)</span>
    <span style="font-family:'Roboto Mono',monospace;font-size:0.86rem;font-weight:700;color:{smeta['accent']}">
      {_cnt} <span style="font-size:0.62rem;color:#4a6080;">/ {total_n}</span>
    </span>
  </div>
</div>""", unsafe_allow_html=True)
            btn_label = " Đang Xem" if is_sel else "Chọn Chiến Lược"
            btn_type  = "primary" if is_sel else "secondary"
            if st.button(btn_label, key=f"card_btn_{i}", use_container_width=True, type=btn_type):
                st.session_state.sel_strat = skey
                st.rerun()

    st.divider()

    # ── Strategy Description ───────────────────────────────
    st.markdown(f"""
<div style="margin:0.5rem 0 1.5rem;padding:1rem 1.5rem;
    background:linear-gradient(135deg,rgba(8,15,36,0.9) 0%,rgba(13,23,46,0.8) 100%);
    border:1px solid {accent}60;border-left:3px solid {accent};border-radius:10px;
    box-shadow:0 4px 20px rgba(0,0,0,0.3),0 0 20px {accent}20;">
  <div style="color:{accent};font-family:'Roboto Mono',monospace;font-size:0.88rem;
       font-weight:700;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.25rem;">
    {meta['icon']} {meta['tagline']}
    &nbsp;<span style="font-size:0.7rem;padding:2px 8px;border-radius:8px;
         background:rgba(255,255,255,0.06);color:#7fa8cc;text-transform:none;letter-spacing:0;">
      Rủi ro: {meta['risk']}
    </span>
  </div>
  <div style="color:#7fa8cc;font-size:0.92rem;line-height:1.6;">{meta['description']}</div>
</div>
""", unsafe_allow_html=True)

    # ── Strategy Param Chips ───────────────────────────────
    params = _build_param_chips(strategy)

    # ── Results ────────────────────────────────────────────
    _render_results(df_all, strategy, params, accent)


# ══════════════════════════════════════════════════════════════
# TAB 2 — DECISION LAB
# ══════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="workspace-header">Decision Lab — AI Strategy Advisor</div>',
                unsafe_allow_html=True)

    st.markdown("#### Tôi Là Nhà Đầu Tư Kiểu Gì?")
    st.caption("Trả lời 3 câu hỏi — nhận gợi ý chiến lược trong 30 giây.")

    risk = st.radio(
        "Mức chịu rủi ro của bạn",
        [" Thích an toàn", " Cân bằng", " Thích tăng trưởng mạnh", " Thích trading ngắn hạn"],
        index=1, horizontal=True,
    )
    goal = st.radio(
        "Mục tiêu đầu tư chính",
        [" Thu nhập thụ động (cổ tức)", " Tăng vốn dài hạn", " Bắt sóng ngắn hạn"],
        index=1, horizontal=True,
    )
    age = st.slider("Tuổi của bạn", 18, 70, 35, 1)

    # Rule-based advisor engine
    if "an toàn" in risk:
        if "thụ động" in goal:
            rec1, rec2 = "Income Investing",  "Quality Investing"
            reason = "Bạn muốn thu nhập ổn định và an toàn — cổ tức bền vững kết hợp chất lượng doanh nghiệp là lý tưởng."
        else:
            rec1, rec2 = "Graham Value",       "Piotroski F-Score"
            reason = "Nhà đầu tư an toàn, tăng vốn dài hạn — Graham Value và F-Score lọc ra doanh nghiệp nền tảng vững."
    elif "trading" in risk or "sóng" in goal:
        rec1, rec2 = "Momentum",              "Factor Investing"
        reason = "Trader ngắn hạn — Momentum tận dụng quán tính thị trường, Factor Investing cung cấp nền tảng định lượng."
    elif "tăng trưởng" in risk:
        rec1, rec2 = "Growth Investing",       "Magic Formula"
        reason = "Nhà đầu tư tăng trưởng — phát hiện GARP cộng với công thức Greenblatt để lọc chất lượng cao với giá hợp lý."
    else:  # Cân bằng
        if age >= 50:
            rec1, rec2 = "Value Investing",    "Quality Investing"
            reason = "Giai đoạn tích lũy cuối — ưu tiên giá trị nội tại và chất lượng để bảo toàn vốn."
        else:
            rec1, rec2 = "Factor Investing",   "Quality Investing"
            reason = "Nhà đầu tư cân bằng — kết hợp đa nhân tố học thuật với chất lượng doanh nghiệp cho alpha bền vững."

    a1, a2 = STRATEGIES[rec1]["accent"], STRATEGIES[rec2]["accent"]
    st.markdown(f"""
<div class="advisor-result">
  <div style="font-family:'Roboto Mono',monospace;font-size:0.78rem;color:#7fa8cc;
   text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.5rem;">
Chiến Lược Đề Xuất
  </div>
  <div style="display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:0.75rem;">
<span style="font-family:'Roboto Mono',monospace;font-size:1.1rem;font-weight:700;color:{a1};">
  {STRATEGIES[rec1]['icon']} {rec1}
</span>
<span style="color:#4a6080;font-size:1.1rem;">+</span>
<span style="font-family:'Roboto Mono',monospace;font-size:1.1rem;font-weight:700;color:{a2};">
  {STRATEGIES[rec2]['icon']} {rec2}
</span>
  </div>
  <div style="color:#7fa8cc;font-size:0.88rem;font-style:italic;">{reason}</div>
</div>
""", unsafe_allow_html=True)

    col_btn1, col_btn2, _ = st.columns([1, 1, 2])
    if col_btn1.button(f"Áp dụng {rec1}", key="adv_btn1", type="primary"):
        st.session_state.sel_strat = rec1
        st.toast(f"Đã chọn chiến lược: {rec1}. Mở tab Strategy Hub để xem kết quả.")
    if col_btn2.button(f"Áp dụng {rec2}", key="adv_btn2", type="secondary"):
        st.session_state.sel_strat = rec2
        st.toast(f"Đã chọn chiến lược: {rec2}. Mở tab Strategy Hub để xem kết quả.")

# ══════════════════════════════════════════════════════════════
# TAB 3 — BACKTEST ARENA
# ══════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="workspace-header">Backtest Arena — Hiệu Suất Giả Lập</div>',
                unsafe_allow_html=True)
    st.caption("Mô phỏng thống kê dựa trên đặc tính tài chính của danh mục lọc được — không phải backtest lịch sử giá thực tế.")

    period = st.radio("Khoảng thời gian giả lập", ["6 Tháng", "1 Năm", "2 Năm"], horizontal=True, index=0)
    multiplier = {"6 Tháng": 1.0, "1 Năm": 2.0, "2 Năm": 3.8}[period]

    rng_bt = np.random.default_rng(42)
    bt_rows = []
    for skey, smeta in STRATEGIES.items():
        try:
            res = apply_strategy(df_all, skey, STRATEGY_DEFAULT_PARAMS[skey])
            n_stocks = len(res)
            if n_stocks > 0 and "Price_6M_Return" in res.columns and res["Price_6M_Return"].notna().any():
                base_return = float(res["Price_6M_Return"].median()) * 100
            else:
                base_return = float(rng_bt.normal(5.0, 8.0))
        except Exception:
            n_stocks, base_return = 0, 0.0

        ret   = round(base_return * multiplier + rng_bt.normal(0, 2.5), 2)
        dd    = round(abs(rng_bt.normal(8, 4)) * (1 + ({"Thấp": 0, "Trung bình": 0.5, "Cao": 1.2}.get(smeta["risk"], 0.5))), 2)
        vol   = round(abs(rng_bt.normal(14, 4)), 2)
        sharpe = round(ret / max(vol, 1), 2)
        market_rel = round(ret - rng_bt.normal(6, 2), 2)

        bt_rows.append({
            "Chiến Lược":         f"{smeta['icon']} {skey}",
            "Sinh Lời (%)":       ret,
            "Max Drawdown (%)":   -dd,
            "Volatility (%)":     vol,
            "Sharpe Ratio":       sharpe,
            "Alpha vs Market (%)": market_rel,
            "N Stocks":           n_stocks,
            "Rủi Ro":             smeta["risk"],
        })

    df_bt = pd.DataFrame(bt_rows).sort_values("Sharpe Ratio", ascending=False).reset_index(drop=True)

    st.dataframe(
        df_bt,
        column_config={
            "Chiến Lược":          TextColumn("Chiến Lược",          width="large"),
            "Sinh Lời (%)":        NumberColumn("Sinh Lời",          format="%+.2f%%", width="medium"),
            "Max Drawdown (%)":    NumberColumn("Max DD",            format="%.2f%%",  width="medium"),
            "Volatility (%)":      NumberColumn("Volatility",        format="%.2f%%",  width="medium"),
            "Sharpe Ratio":        NumberColumn("Sharpe",            format="%.2f",    width="small"),
            "Alpha vs Market (%)": NumberColumn("Alpha",             format="%+.2f%%", width="medium"),
            "N Stocks":            NumberColumn("N Stocks",          format="%d",      width="small"),
            "Rủi Ro":              TextColumn("Rủi Ro",              width="small"),
        },
        hide_index=True,
        use_container_width=True,
        height=380,
    )

    # Bar chart — Return comparison
    fig_bt = go.Figure()
    colors_bt = [STRATEGIES[r["Chiến Lược"].split(" ", 1)[1]]["accent"]
                 if r["Chiến Lược"].split(" ", 1)[1] in STRATEGIES else "#00ccff"
                 for r in bt_rows]
    fig_bt.add_trace(go.Bar(
        x=[r["Chiến Lược"] for r in bt_rows],
        y=[r["Sinh Lời (%)"] for r in bt_rows],
        marker_color=colors_bt,
        marker_line_color=PAPER_BG,
        marker_line_width=1.5,
        hovertemplate="<b>%{x}</b><br>Sinh lời: %{y:+.2f}%<extra></extra>",
    ))
    bt_layout = _base_layout(f"So Sánh Sinh Lời Giả Lập — {period}", "#00ccff")
    bt_layout.update(xaxis_tickangle=-35, height=360,
                     yaxis_title="Sinh Lời (%)", showlegend=False)
    fig_bt.update_layout(**bt_layout)
    st.plotly_chart(fig_bt, use_container_width=True, config={"scrollZoom": False})


# ══════════════════════════════════════════════════════════════
# TAB 4 — PORTFOLIO MIXER
# ══════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="workspace-header">Portfolio Mixer — Kết Hợp Chiến Lược</div>',
                unsafe_allow_html=True)
    st.caption("Chọn 2–4 chiến lược để phân tích mức độ chồng chéo và xác định cổ phiếu được nhiều chiến lược đồng thuận.")

    mix_choices = st.multiselect(
        "Chọn chiến lược để kết hợp (chọn 2–4)",
        options=list(STRATEGIES.keys()),
        default=["Graham Value", "Quality Investing"],
        max_selections=4,
        format_func=lambda k: f"{STRATEGIES[k]['icon']} {k}",
    )

    if len(mix_choices) < 2:
        st.info("Chọn ít nhất 2 chiến lược để bắt đầu phân tích.")
    else:
        with st.spinner("Đang tổng hợp danh mục..."):
            strategy_sets: dict[str, set] = {}
            for skey in mix_choices:
                try:
                    res = apply_strategy(df_all, skey, STRATEGY_DEFAULT_PARAMS[skey])
                    strategy_sets[skey] = set(res["Ticker"].tolist())
                except Exception:
                    strategy_sets[skey] = set()

        # ── Overlap matrix ───────────────────────────────
        st.markdown("#### Ma Trận Chồng Chéo Cổ Phiếu")
        mix_col_names = list(strategy_sets.keys())
        overlap_data = []
        for sk1 in mix_col_names:
            row = {}
            for sk2 in mix_col_names:
                s1, s2 = strategy_sets[sk1], strategy_sets[sk2]
                if len(s1) == 0 or len(s2) == 0:
                    row[sk2] = "—"
                elif sk1 == sk2:
                    row[sk2] = f"{len(s1)}"
                else:
                    inter = len(s1 & s2)
                    pct   = inter / min(len(s1), len(s2)) * 100
                    row[sk2] = f"{inter} ({pct:.0f}%)"
            overlap_data.append({"Chiến Lược": f"{STRATEGIES[sk1]['icon']} {sk1}", **row})

        df_overlap = pd.DataFrame(overlap_data)
        st.dataframe(df_overlap, hide_index=True, use_container_width=True)

        # ── Vote counts ──────────────────────────────────
        vote_mix: dict = {}
        for skey, tickers in strategy_sets.items():
            for tkr in tickers:
                vote_mix[tkr] = vote_mix.get(tkr, 0) + 1

        # Separate: unique and multi-voted
        multi_voted  = {k: v for k, v in vote_mix.items() if v >= 2}
        unique_only  = {k: v for k, v in vote_mix.items() if v == 1}

        st.markdown("#### Cổ Phiếu Được Nhiều Chiến Lược Đồng Thuận")

        if multi_voted:
            top_mix = (
                pd.DataFrame.from_dict(multi_voted, orient="index", columns=["Votes"])
                .sort_values("Votes", ascending=False)
                .reset_index().rename(columns={"index": "Ticker"})
            )
            # show which strategies picked each ticker
            def _which_strats(tkr):
                return " + ".join(
                    f"{STRATEGIES[sk]['icon']}{sk}"
                    for sk, s in strategy_sets.items() if tkr in s
                )
            top_mix["Được Chọn Bởi"] = top_mix["Ticker"].apply(_which_strats)

            merge_cols2 = ["Ticker", "Price Close", "P_E", "P_B"]
            merge_cols2 = [c for c in merge_cols2 if c in df_all.columns]
            top_mix = top_mix.merge(df_all[merge_cols2], on="Ticker", how="left")

            st.dataframe(
                top_mix,
                column_config={
                    "Ticker":       TextColumn("Ticker",           width="medium"),
                    "Votes":        ProgressColumn("Chiến Lược Chọn", format="%d", min_value=0, max_value=len(mix_choices), width="medium"),
                    "Được Chọn Bởi": TextColumn("Được Chọn Bởi",  width="large"),
                    "Price Close":  NumberColumn("Giá",            format="%.0f",  width="small"),
                    "P_E":          NumberColumn("P/E",            format="%.1fx", width="small"),
                    "P_B":          NumberColumn("P/B",            format="%.2fx", width="small"),
                },
                hide_index=True,
                use_container_width=True,
            )

            # Chip tags
            chip_html = "".join(
                f'<span class="multi-vote">{STRATEGIES.get(skey, {}).get("icon","")}&nbsp;{skey}: '
                f'{len(s)} cổ phiếu</span>'
                for skey, s in strategy_sets.items()
            )
            st.markdown(chip_html, unsafe_allow_html=True)
        else:
            st.info("Không có cổ phiếu nào được cả 2+ chiến lược đồng thời chọn với tham số mặc định. "
                    "Thử điều chỉnh tham số trong Strategy Hub hoặc chọn chiến lược có phong cách tương tự.")

        # ── Unique-only summary ──────────────────────────
        if unique_only:
            with st.expander(f"Xem {len(unique_only)} cổ phiếu chỉ được 1 chiến lược chọn"):
                for skey, s in strategy_sets.items():
                    unique_in_s = s - set(v for k, v_d in strategy_sets.items()
                                          if k != skey for v in v_d)
                    only_this = [t for t in s if vote_mix.get(t, 0) == 1]
                    if only_this:
                        chips = " ".join(f'<span class="overlap-chip">{t}</span>' for t in only_this[:20])
                        st.markdown(
                            f"<div style='margin-bottom:0.5rem;'>"
                            f"<span style='color:{STRATEGIES[skey]['accent']};font-weight:700;"
                            f"font-family:Roboto Mono,monospace;font-size:0.8rem;'>"
                            f"{STRATEGIES[skey]['icon']} {skey}</span> ({len(only_this)} riêng):<br>"
                            f"{chips}</div>",
                            unsafe_allow_html=True,
                        )

# ──────────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
  Made by Tuấn Thịnh, Hưng Thịnh, Lê Cường, Gia Bảo, Trường Sơn, Thanh Nam, Đức Phú, Vũ Phúc<br>
  <span style="color:#1f2d40">────────────────────────────────────────</span><br>
  Dữ liệu chỉ mang tính tham khảo. Không phải khuyến nghị đầu tư.<br><br>
  <span style="color:#4a6080; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em;">Nguồn Dữ Liệu</span><br>
  <span style="color:#64748b; font-size:0.8rem;">
    File: <code style="background:rgba(15,20,25,0.8);padding:2px 6px;border-radius:3px;color:#00d4ff;">df_screen_master.csv</code>
    &nbsp;·&nbsp; 9 Chiến Lược: Graham · Income · Growth · Momentum · Magic Formula · Piotroski · Value · Factor · Quality
    &nbsp;·&nbsp; Thị trường: Sàn Giao Dịch Chứng Khoán Chile
  </span>
</div>
""", unsafe_allow_html=True)

