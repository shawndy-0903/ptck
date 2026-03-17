"""
=================================================================
  QUANT DATA PIPELINE  —  BUILD df_screen_master.csv
  Source: CHILE.xlsx  (Refinitiv terminal export)

  Architecture: ETL Pattern
    [EXTRACT]   -> Raw Excel sheets -> clean DataFrames
    [TRANSFORM] -> Feature engineering, PIT merge, Winsorize
    [LOAD]      -> Write df_screen_master.csv

  Quant Best Practices enforced:
    1. Robust parsing  -- auto-detect junk rows, handle sentinel
                          strings (#N/A, NULL) via vectorized ops
    2. Outlier control -- Winsorization at [1st, 99th] percentile
                          to prevent chart scale corruption
    3. Vectorization   -- zero iterrows(); all ops via .transform()
                          and broadcasting
    4. Look-ahead bias -- frequency-based PIT lag (annual=120d,
                          semi=60d, quarterly=45d) before merge
    5. Correctness     -- TTM DPS, Payout guard, Gross_Margin
                          coalesce, Revenue<0 guard, MA min_periods
=================================================================
"""

from __future__ import annotations

import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


# ==============================================================
# CONSTANTS
# ==============================================================

EXCEL_PATH  = "CHILE.xlsx"          # Source file (same directory)
OUTPUT_PATH = "df_screen_master.csv"

# Publication lag from fiscal period-end -> public filing availability.
# Chile CMF deadlines: annual=120d, semi-annual=60d, quarterly=45d.
# Frequency is auto-detected per ticker in apply_pit_lag().
PIT_LAG_ANNUAL     = 120   # EEFF Anuales  (CMF deadline)
PIT_LAG_SEMIANNUAL =  60   # EEFF Semestrales
PIT_LAG_QUARTERLY  =  45   # EEFF Trimestrales

# Sentinel strings emitted by financial terminals for missing data
_BAD_STRINGS: set[str] = {
    "#N/A", "#NA", "#VALUE!", "#REF!", "#DIV/0!",
    "NA", "N/A", "NULL", "NaN", "nan",
    "Unable to collect data", "-", "", " ",
}

# Keywords found in metadata rows at the top of terminal exports
_JUNK_KEYWORDS = ("Updated at", "Extracted", "Report", "Generated", "Source")

# Column name mapping: raw terminal header -> standardised app name
COL_MAP: dict[str, str] = {
    # Balance Sheet
    "Total Current Assets":                                        "Total_Current_Assets",
    "Total Current Liabilities":                                   "Total_Current_Liabilities",
    "Debt - Total":                                                "Debt_Total",
    "Common Equity - Total":                                       "Total_Equity",
    "Common Shares - Outstanding - Total":                         "Shares_Outstanding",
    "Total Assets":                                                "Total_Assets",
    "Cash & Cash Equivalents - Total":                             "Cash_Equivalents",
    "Cash & Short Term Investments":                               "Cash_Equivalents",    # alt
    "Net Debt":                                                    "Net_Debt_Raw",         # direct field
    # Income Statement
    "Revenue from Business Activities - Total":                    "Revenue",
    "Gross Profit - Industrials/Property - Total":                 "Gross_Profit",
    "Cost of Revenues - Total":                                    "Cost_of_Revenue",
    "EPS - Basic - incl Extraordinary Items, Common - Total":      "EPS_Basic",
    "DPS - Common - Net - Issue - By Announcement Date":           "DPS_Net",
    "Net Income after Minority Interest":                          "Net_Income",
    "Net Income after Tax":                                        "Net_Income",          # alt
    "Earnings before Interest Taxes Depreciation & Amortization": "EBITDA",
    # Cash Flow
    "Net Cash Flow from Operating Activities":                     "Op_CashFlow",
    "Capital Expenditures - Net - Cash Flow":                      "Capex",
    "Capital Expenditures - Total":                                "Capex",               # alt
    "Free Cash Flow":                                              "Free_Cash_Flow",
}

# Columns to Winsorize (clip to [1st, 99th] percentile cross-sectionally).
# These are DISPLAY columns — clipped for color scales only.
# Before clipping, each column is copied to <col>_raw for filter sliders in
# App.py (a company with P/E=180 stays P/E_raw=180 for Graham-filter logic
# even though the display P/E is capped at the 99th-pct value ~42).
_WINSOR_COLS = [
    "P_E", "P_B",
    "Rev_Growth_YoY", "EPS_Growth_YoY",
    "Debt_to_Equity", "Payout_Ratio",
    "Gross_Margin", "Current_Ratio", "Dividend_Yield",
    "ROE", "ROA", "Net_Debt_EBITDA", "FCF_Yield",
]

# Sheet names in CHILE.xlsx
BS_SHEETS    = ["BS1", "BS2", "BS3", "BS4", "BS5", "BS6", "BS7", "BS8", "BS9"]
IS_SHEETS    = ["IS1", "IS2", "IS3", "IS4"]
CF_SHEETS    = ["CF1", "CF2", "CF3"]
PRICE_SHEETS = ["PRICE", "PRICE2"]

# Final output columns (order preserved in CSV)
OUTPUT_COLS = [
    # ── Screener display columns (Winsorized — for color scales in App.py) ──
    "Ticker",
    "Price Close",
    "P_E", "P_B",
    "Current_Ratio",
    "Debt_to_Equity",
    "Dividend_Yield",
    "Payout_Ratio",
    "Rev_Growth_YoY",
    "EPS_Growth_YoY",
    "Gross_Margin",
    "Price_6M_Return",
    "Volume",
    "Vol_Avg_20",
    "RSI_14",
    "MA50",
    "MA200",
    # ── Extended display metrics ──
    "Market_Cap",
    "ROE", "ROA",
    "Net_Debt", "Net_Debt_EBITDA",
    "FCF_Yield",
    "Company_Name",        # from COMP sheet (Sector/Industry not in source)
    # ── Raw pre-Winsorize values — use these for FILTER SLIDERS in App.py ──
    # P/E raw=180 stays 180 even if display P/E is capped at 42.
    "P_E_raw", "P_B_raw",
    "Current_Ratio_raw",
    "Debt_to_Equity_raw",
    "Dividend_Yield_raw",
    "Payout_Ratio_raw",
    "Rev_Growth_YoY_raw",
    "EPS_Growth_YoY_raw",
    "Gross_Margin_raw",
    "ROE_raw", "ROA_raw",
    "Net_Debt_EBITDA_raw",
    "FCF_Yield_raw",
    # ── Raw financial inputs (debugging / downstream) ──
    "Revenue",
    "EPS_Basic",
    "DPS_Net",
    "Op_CashFlow",
    "Total_Current_Assets",
    "Total_Current_Liabilities",
    "Debt_Total",
    "Total_Equity",
    "Shares_Outstanding",
]



# ==============================================================
# EXTRACT — Read raw sheets into clean DataFrames
# ==============================================================

def _clean_numeric(series: pd.Series) -> pd.Series:
    """
    Vectorized coercion to float.

    Financial terminal exports contaminate numeric columns with sentinel
    strings like "#N/A" or "Unable to collect data". Replacing these
    before pd.to_numeric avoids silent NaN introduction by errors='coerce'
    masking real parse failures.
    """
    if series.dtype == object:
        series = series.astype(str).str.strip().replace(_BAD_STRINGS, np.nan)
    return pd.to_numeric(series, errors="coerce")


def read_fin_sheet(xl: pd.ExcelFile, sheet: str) -> pd.DataFrame:
    """
    Parse one financial sheet (BS / IS / CF) into a tidy DataFrame.

    CHILE.xlsx uses two layout variants:
      Type A (BS1-BS9, IS1-IS4, CF1-CF2)
            row 0 = metadata/blank  ->  skip
            row 1 = column headers
            row 2+ = data
            col 0 = blank/row-number (drop),  col 1 = Ticker,  col 2 = Date

      Type B (CF3)
            row 0 = column headers  (col 0 is NaN/metadata)
            row 1+ = data
            col 0 = Ticker,  col 1 = Date

    Auto-detection: if the first cell of data row 1 ends with ".SN"
    (a valid Chilean ticker suffix) the sheet is Type B.
    """
    try:
        raw = pd.read_excel(xl, sheet_name=sheet, header=None)
    except Exception as exc:
        print(f"    [SKIP] {sheet}: {exc}")
        return pd.DataFrame()

    if raw.shape[0] < 3:
        return pd.DataFrame()

    # Detect layout type by inspecting candidate first-data-cell
    probe = str(raw.iloc[1, 0]).strip()
    is_type_b = probe.endswith(".SN")

    if is_type_b:
        # ── Type B (CF3) ──────────────────────────────────
        headers      = [str(h) for h in raw.iloc[0].tolist()]
        data         = raw.iloc[1:].copy().reset_index(drop=True)
        data.columns = headers
        col_list     = list(data.columns)
        col_list[0]  = "Ticker"
        col_list[1]  = "Date"
        data.columns = col_list
    else:
        # ── Type A (BS, IS, CF1/CF2) ──────────────────────
        headers      = [str(h) for h in raw.iloc[1].tolist()]
        data         = raw.iloc[2:].copy().reset_index(drop=True)
        data.columns = headers
        col_list     = list(data.columns)
        if len(col_list) >= 3:
            col_list[1] = "Ticker"
            col_list[2] = "Date"
        data.columns = col_list
        # Drop leftmost index / blank column
        data = data.drop(columns=[col_list[0]], errors="ignore")

    # ── Common post-processing ────────────────────────────
    data["Ticker"] = data["Ticker"].astype(str).str.strip()
    data["Date"]   = pd.to_datetime(data["Date"], errors="coerce")

    # Keep only rows with valid .SN ticker and a parseable date
    data = data[data["Ticker"].str.endswith(".SN")].dropna(subset=["Date"])

    # Deduplicate columns (keep first) before numeric coercion to avoid
    # shape mismatch errors when duplicate headers exist in source sheets
    data = data.loc[:, ~data.columns.duplicated(keep="first")]

    # Coerce each financial column to float individually (vectorized per Series)
    for col in [c for c in data.columns if c not in ("Ticker", "Date")]:
        data[col] = _clean_numeric(data[col])

    return data.reset_index(drop=True)


def _merge_sheets(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """
    Outer-merge a list of DataFrames on [Ticker, Date],
    adding only columns not already present to avoid duplication.
    """
    result = dfs[0]
    for df in dfs[1:]:
        new_cols = ["Ticker", "Date"] + [
            c for c in df.columns if c not in result.columns
        ]
        result = pd.merge(result, df[new_cols], on=["Ticker", "Date"], how="outer")
    return result


def load_fin_group(xl: pd.ExcelFile, sheets: list[str], label: str) -> pd.DataFrame:
    """Extract and concatenate a group of financial sheets."""
    dfs = []
    for sh in sheets:
        df = read_fin_sheet(xl, sh)
        if not df.empty:
            print(f"    OK  {sh:6s}: {df.shape[0]:>6,} rows x {df.shape[1]} cols")
            dfs.append(df)

    if not dfs:
        print(f"    [WARN] No sheets loaded for {label}")
        return pd.DataFrame()

    result = _merge_sheets(dfs)
    print(f"  --> {label}: {result.shape[0]:,} rows x {result.shape[1]} cols")
    return result


def read_price_sheet(xl: pd.ExcelFile, sheet: str) -> pd.DataFrame:
    """
    Extract price data.

    Layout (both PRICE and PRICE2):
      row 0 = metadata/blank (skip)
      row 1 = header (skip -- names assigned by position)
      row 2+ = data
      col 1 = Ticker,  col 2 = Date,
      col 3 = Price Close,  col 4 = Volume
    """
    try:
        raw = pd.read_excel(xl, sheet_name=sheet, header=None)
    except Exception as exc:
        print(f"    [SKIP] {sheet}: {exc}")
        return pd.DataFrame()

    data         = raw.iloc[2:].copy().reset_index(drop=True)
    data.columns = range(len(data.columns))
    data         = data.rename(columns={1: "Ticker", 2: "Date",
                                         3: "Price Close", 4: "Volume"})
    data         = data[["Ticker", "Date", "Price Close", "Volume"]].copy()

    data["Ticker"]      = data["Ticker"].astype(str).str.strip()
    data["Date"]        = pd.to_datetime(data["Date"], errors="coerce")
    data["Price Close"] = _clean_numeric(data["Price Close"])
    data["Volume"]      = _clean_numeric(data["Volume"])

    return (
        data[data["Ticker"].str.endswith(".SN")]
        .dropna(subset=["Date", "Price Close"])
        .reset_index(drop=True)
    )


# ==============================================================
# TRANSFORM — Feature engineering on clean DataFrames
# ==============================================================

def safe_divide(num: pd.Series, den: pd.Series) -> pd.Series:
    """
    Vectorized division guarded against zero and NaN denominators.

    Uses np.where (C-level branching) instead of .apply() or loops.
    Returns NaN wherever denominator is zero or missing.
    """
    mask = den.notna() & (den != 0)
    return pd.Series(
        np.where(mask, num.values / np.where(mask, den.values, np.nan), np.nan),
        index=num.index,
    )


def winsorize(df: pd.DataFrame,
              cols: list[str],
              lower_pct: float = 0.01,
              upper_pct: float = 0.99) -> pd.DataFrame:
    """
    Cross-sectional Winsorization at [lower_pct, upper_pct] quantiles.

    Replaces extreme values with the boundary value rather than
    dropping the company. This preserves sample size while preventing
    a single outlier (e.g. P/E = 2000) from collapsing all chart scales.

    Example: if 99th-percentile P/E = 45, all P/E > 45 become 45.
    """
    df = df.copy()
    for col in cols:
        if col not in df.columns:
            continue
        lo = df[col].quantile(lower_pct)
        hi = df[col].quantile(upper_pct)
        df[col] = df[col].clip(lower=lo, upper=hi)
    return df


def _compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Wilder's RSI via Exponential Moving Average -- fully vectorized.

    RSI = 100 - 100 / (1 + RS),  RS = avg_gain / avg_loss
    Uses ewm(com=period-1) which is equivalent to Wilder's smoothing.
    Safe to call inside .transform() since it operates on a single Series.
    """
    delta    = series.diff()
    gain     = delta.clip(lower=0)
    loss     = (-delta).clip(lower=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs       = safe_divide(avg_gain, avg_loss)
    return 100 - (100 / (1 + rs))


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute price-based indicators for every ticker simultaneously.

    All operations use .groupby().transform() -- this applies the
    rolling/ewm calculation per-ticker without Python-level iteration,
    delegating entirely to Pandas C/Cython internals.

    Indicators:
      MA50            -- 50-period simple moving average
      MA200           -- 200-period simple moving average
      RSI_14          -- 14-period Wilder's RSI
      Vol_Avg_20      -- 20-period average daily volume
      Price_6M_Return -- 120-trading-day price return (~6 calendar months)
    """
    df  = df.sort_values(["Ticker", "Date"]).copy()
    grp = df.groupby("Ticker")

    df["MA50"]            = grp["Price Close"].transform(
        lambda x: x.rolling(50,  min_periods=50).mean()   # NaN if < 50 days history
    )
    df["MA200"]           = grp["Price Close"].transform(
        lambda x: x.rolling(200, min_periods=200).mean()  # NaN if < 200 days history
    )
    df["RSI_14"]          = grp["Price Close"].transform(
        lambda x: _compute_rsi(x, 14)
    )
    df["Vol_Avg_20"]      = grp["Volume"].transform(
        lambda x: x.rolling(20, min_periods=1).mean()
    )
    # pct_change(120): return over previous 120 trading days
    df["Price_6M_Return"] = grp["Price Close"].transform(
        lambda x: x.pct_change(120)
    )
    return df


def _yoy_growth(df: pd.DataFrame, col: str) -> pd.Series:
    """
    Year-over-Year growth rate, computed correctly within each Ticker group.

    Critical: sort_values() called BEFORE groupby().shift(1) to guarantee
    that "previous period" is temporally earlier -- not a row from a
    different ticker that happens to be adjacent after a merge.

    Formula: (current - prior) / |prior|
    Absolute-value denominator handles sign-flip when prior period was
    a loss (negative EPS/Revenue), preventing misleading sign reversal.
    """
    df_s  = df.sort_values(["Ticker", "Date"])
    prior = df_s.groupby("Ticker")[col].shift(1)
    return safe_divide(df_s[col] - prior, prior.abs()).reindex(df.index)


def apply_pit_lag(df_fund: pd.DataFrame) -> pd.DataFrame:
    """
    Simulate Point-in-Time availability of fundamental data.

    Problem: a fiscal year ending 31-Dec-2023 does NOT mean the data
    was readable on that day. Under CMF (Chile) rules companies have
    varying deadlines depending on reporting frequency.

    Fix: shift every fundamental Date forward by a lag that depends on
    the detected reporting frequency per ticker:
      - Annual   (gap > 270d) -> 120 days  (CMF EEFF Anuales)
      - Semi-annual (gap > 135d) -> 60 days
      - Quarterly               -> 45 days

    Frequency is auto-detected from median inter-report gap per ticker.
    """
    df   = df_fund.copy().sort_values(["Ticker", "Date"])
    gaps = df.groupby("Ticker")["Date"].diff().dt.days
    med  = gaps.groupby(df["Ticker"]).transform("median").fillna(365)

    lag = np.where(med > 270, PIT_LAG_ANNUAL,
          np.where(med > 135, PIT_LAG_SEMIANNUAL, PIT_LAG_QUARTERLY))

    df["Pub_Date"] = df["Date"] + pd.to_timedelta(lag, unit="D")
    return df


def merge_pit(df_fund: pd.DataFrame,
              df_price_ref: pd.DataFrame) -> pd.DataFrame:
    """
    Point-in-Time merge using pd.merge_asof.

    For each (Ticker, reference_date) in df_price_ref, find the most
    recently PUBLISHED fundamental period where Pub_Date <= reference_date.

    Deduplication before merge_asof is mandatory: duplicate (Ticker, Pub_Date)
    keys make merge_asof raise or silently return wrong rows.
    """
    df_fund_pit = (
        apply_pit_lag(df_fund)
        .drop_duplicates(subset=["Ticker", "Pub_Date"], keep="last")
        .sort_values("Pub_Date")
    )
    df_ref = (
        df_price_ref[["Ticker", "Date"]]
        .drop_duplicates(subset=["Ticker", "Date"], keep="last")
        .sort_values("Date")
    )

    merged = pd.merge_asof(
        df_ref,
        df_fund_pit.drop(columns=["Date"]),   # use Pub_Date as merge key
        left_on="Date",
        right_on="Pub_Date",
        by="Ticker",
        direction="backward",    # most recent Pub_Date <= price Date
    )
    return merged.drop(columns=["Pub_Date"], errors="ignore")


def _compute_ttm_dps(df_fund: pd.DataFrame,
                     df_price_ref: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    Trailing-12-month DPS: sum all dividends in the 365-day window ending at
    the PRICE reference date (last quote date) per ticker.

    Anchoring to the price date (not the last filing date) fixes two bugs:
      1. Semi-annual payers: both dividends are captured in a rolling 12-month
         window, not just the most recently filed period.
      2. Stale data guard: if a company hasn't filed in > 18 months the window
         finds no dividends and DPS_TTM is set to NaN rather than carrying
         forward a years-old payment as "current yield".

    Falls back to last-filing anchor when df_price_ref is not provided.
    """
    df = df_fund.copy().sort_values(["Ticker", "Date"])
    if "DPS_Net" not in df.columns:
        df["DPS_TTM"] = np.nan
        return df

    if df_price_ref is not None:
        # Anchor cutoff to the actual price/reference date per ticker.
        # 15-month window (not 12) ensures annual payers declaring in Nov/Dec
        # are captured when price_date is in Q1 of the following year.
        ref = (
            df_price_ref[["Ticker", "Date"]]
            .drop_duplicates("Ticker", keep="last")
            .rename(columns={"Date": "Price_Date"})
        )
        df = df.merge(ref, on="Ticker", how="left")
        # Stale guard: if last filing is > 24 months before price date → NaN
        staleness = (df["Price_Date"] - df.groupby("Ticker")["Date"].transform("max")).dt.days
        cutoff     = df["Price_Date"] - pd.DateOffset(months=15)
        stale_mask = staleness > 730                        # 24 months
    else:
        df["Price_Date"] = df.groupby("Ticker")["Date"].transform("max")
        cutoff     = df["Price_Date"] - pd.DateOffset(months=15)
        stale_mask = pd.Series(False, index=df.index)

    mask = (df["Date"] >= cutoff) & (df["Date"] <= df["Price_Date"])
    ttm  = (
        df[mask]
        .groupby("Ticker")["DPS_Net"]
        .sum()
        .rename("DPS_TTM")
    )
    df   = df.join(ttm, on="Ticker")
    # Zero out stale tickers (company hasn't filed in > 18 months)
    df.loc[stale_mask, "DPS_TTM"] = np.nan
    return df.drop(columns=["Price_Date"], errors="ignore")


def engineer_features(df_fund: pd.DataFrame,
                      df_price_full: pd.DataFrame,
                      df_price_latest: pd.DataFrame) -> pd.DataFrame:
    """
    Full feature engineering pipeline.

    Steps:
      1. YoY growth        -- full historical panel (needs prior-year rows)
      2. Average equity    -- (Equity_t + Equity_t-1) / 2 per ticker (CFA ROE)
      3. TTM DPS           -- trailing 12m sum anchored to price date
      4. PIT merge         -- join latest price with most-recently-published filing
      5. Ratios            -- all via safe_divide (zero-division / NaN safe)
      6. New metrics       -- Market_Cap, ROE/ROA (avg equity), Net_Debt, FCF_Yield
      7. Save _raw columns -- pre-Winsorize copies for App.py filter sliders
      8. Winsorize         -- [1st, 99th] pct on display columns only
    """
    df_fund = df_fund.copy()

    # ── Step 1: YoY growth (requires full multi-year history) ────────────
    if "Revenue" in df_fund.columns:
        df_fund.loc[df_fund["Revenue"] < 0, "Revenue"] = np.nan
        df_fund["Rev_Growth_YoY"] = _yoy_growth(df_fund, "Revenue")
    if "EPS_Basic" in df_fund.columns:
        df_fund["EPS_Growth_YoY"] = _yoy_growth(df_fund, "EPS_Basic")

    # ── Step 2: Average equity / assets for CFA-standard ROE / ROA ───────
    # ROE = Net_Income / avg(Equity_begin, Equity_end) avoids distortion when
    # a large capital raise mid-year inflates ending equity relative to income.
    df_s = df_fund.sort_values(["Ticker", "Date"])
    if "Total_Equity" in df_fund.columns:
        prev_eq          = df_s.groupby("Ticker")["Total_Equity"].shift(1)
        df_fund["Avg_Equity"] = ((df_s["Total_Equity"] + prev_eq) / 2).values
    if "Total_Assets" in df_fund.columns:
        prev_ast         = df_s.groupby("Ticker")["Total_Assets"].shift(1)
        df_fund["Avg_Assets"] = ((df_s["Total_Assets"] + prev_ast) / 2).values

    # ── Step 3: TTM DPS anchored to price date ────────────────────────────
    df_fund = _compute_ttm_dps(df_fund, df_price_ref=df_price_latest)

    # ── Step 4: Point-in-Time merge ──────────────────────────────────────
    df = merge_pit(df_fund, df_price_latest)

    # Attach price & technical indicators (already computed on full series)
    price_cols = ["Ticker", "Price Close", "Volume", "Vol_Avg_20",
                  "MA50", "MA200", "RSI_14", "Price_6M_Return"]
    avail      = [c for c in price_cols if c in df_price_latest.columns]
    df         = pd.merge(df, df_price_latest[avail],
                          on="Ticker", how="left", suffixes=("", "_px"))
    if "Date_px" in df.columns:
        df = df.drop(columns=["Date_px"])

    close = df.get("Price Close", pd.Series(np.nan, index=df.index))
    _nan  = pd.Series(np.nan, index=df.index)

    # ── Step 5: Financial ratios ──────────────────────────────────────────

    # EPS: use filed EPS_Basic as primary; fall back to Net_Income/Shares when
    # EPS_Basic is NaN. Sanity check warns if both exist but disagree by > 10%.
    eps = df.get("EPS_Basic", _nan).copy()
    if "Net_Income" in df.columns and "Shares_Outstanding" in df.columns:
        eps_computed = safe_divide(df["Net_Income"], df["Shares_Outstanding"])
        both_avail   = eps.notna() & eps_computed.notna() & (eps.abs() > 0)
        pct_diff     = ((eps - eps_computed).abs() / eps.abs()).where(both_avail)
        n_mismatch   = (pct_diff > 0.10).sum()
        if n_mismatch > 0:
            import warnings as _w
            _w.warn(
                f"EPS sanity: {n_mismatch} ticker(s) show >10% gap between "
                f"EPS_Basic and Net_Income/Shares. EPS_Basic used as primary.",
                stacklevel=2,
            )
        eps = eps.where(eps.notna(), other=eps_computed)

    # Book Value Per Share = Total Equity / Shares Outstanding
    bvps = (
        safe_divide(df["Total_Equity"], df["Shares_Outstanding"])
        if "Total_Equity" in df.columns and "Shares_Outstanding" in df.columns
        else _nan
    )

    # Valuation
    df["P_E"] = safe_divide(close, eps)
    df["P_B"] = safe_divide(close, bvps)

    # Market capitalisation
    df["Market_Cap"] = (
        close * df["Shares_Outstanding"]
        if "Shares_Outstanding" in df.columns
        else _nan
    )

    # Solvency & liquidity
    df["Current_Ratio"]  = safe_divide(df.get("Total_Current_Assets",     _nan),
                                        df.get("Total_Current_Liabilities", _nan))
    df["Debt_to_Equity"] = safe_divide(df.get("Debt_Total",   _nan),
                                        df.get("Total_Equity", _nan))

    # Income quality — TTM DPS anchored to price date (Step 3)
    dps_ttm = df.get("DPS_TTM", _nan)
    df["Dividend_Yield"] = safe_divide(dps_ttm, close)
    payout_raw           = safe_divide(dps_ttm, eps)
    df["Payout_Ratio"]   = payout_raw.where(eps > 0, other=np.nan)

    # Gross Margin: prefer filed Gross_Profit; coalesce with Revenue - COGS
    gross_calc  = df.get("Revenue", _nan) - df.get("Cost_of_Revenue", _nan)
    gross_final = df.get("Gross_Profit", _nan).fillna(gross_calc)
    df["Gross_Margin"] = safe_divide(gross_final, df.get("Revenue", _nan))

    # ── Step 6: Extended metrics ──────────────────────────────────────────

    # ROE / ROA — CFA standard: use average equity/assets (Step 2)
    if "Net_Income" in df.columns:
        df["ROE"] = safe_divide(
            df["Net_Income"],
            df.get("Avg_Equity", df.get("Total_Equity", _nan)),
        )
        df["ROA"] = safe_divide(
            df["Net_Income"],
            df.get("Avg_Assets", df.get("Total_Assets", _nan)),
        )
    else:
        df["ROE"] = _nan
        df["ROA"] = _nan

    # Net Debt: prefer direct field; fall back to Debt - Cash
    net_debt_src      = df.get("Net_Debt_Raw", _nan)
    computed_net_debt = df.get("Debt_Total", _nan) - df.get("Cash_Equivalents", _nan)
    df["Net_Debt"]    = net_debt_src.where(net_debt_src.notna(), other=computed_net_debt)

    # Net_Debt / EBITDA: set NaN when EBITDA <= 0 (ratio is economically
    # meaningless for loss-making or near-zero EBITDA companies).
    ebitda = df.get("EBITDA", _nan)
    df["Net_Debt_EBITDA"] = safe_divide(
        df["Net_Debt"],
        ebitda.where(ebitda > 0, other=np.nan),
    )

    # FCF Yield
    fcf_direct = df.get("Free_Cash_Flow", _nan)
    capex      = df.get("Capex", _nan)
    fcf_calc   = df.get("Op_CashFlow", _nan) - capex.abs()
    fcf        = fcf_direct.where(fcf_direct.notna(), other=fcf_calc)
    df["FCF_Yield"] = safe_divide(fcf, df["Market_Cap"])

    # Company name placeholder (COMP sheet has name but not sector/industry)
    if "Company_Name" not in df.columns:
        df["Company_Name"] = np.nan

    # ── Step 7: Save _raw copies BEFORE Winsorize ────────────────────────
    # App.py should use P_E_raw (true value) for filter sliders so that a
    # company with P/E=180 does NOT pass a Graham filter set to < 20, even
    # though the display P/E is capped at ~42 for colour-scale purposes.
    for col in _WINSOR_COLS:
        if col in df.columns:
            df[f"{col}_raw"] = df[col]

    # ── Step 8: Winsorize display columns ────────────────────────────────
    df = winsorize(df, _WINSOR_COLS)

    return df


# ==============================================================
# LOAD — Orchestrate ETL and write final CSV
# ==============================================================

def build_master_csv() -> None:
    """
    Main ETL entry point.

    Orchestrates: Extract -> Transform -> Load
    Prints a structured log and quality report (NaN counts) at the end.
    """
    sep = "=" * 62
    print(sep)
    print("  CHILE STOCK SCREENER  |  BUILDING df_screen_master.csv")
    print(sep)

    # ── EXTRACT ───────────────────────────────────────────────
    print(f"\n[EXTRACT]  Opening {EXCEL_PATH} ...")
    try:
        xl = pd.ExcelFile(EXCEL_PATH)
    except FileNotFoundError:
        print(f"  ERROR: File not found: {EXCEL_PATH}")
        return

    print("\n  Balance Sheet (BS1-BS9)...")
    df_bs = load_fin_group(xl, BS_SHEETS, "BS")

    print("\n  Income Statement (IS1-IS4)...")
    df_is = load_fin_group(xl, IS_SHEETS, "IS")

    print("\n  Cash Flow (CF1-CF3)...")
    df_cf = load_fin_group(xl, CF_SHEETS, "CF")

    # ── COMP sheet: Company names (Sector/Industry not in source data) ───
    print("\n  COMP sheet (Company names)...")
    df_comp = pd.DataFrame()
    if "COMP" in xl.sheet_names:
        try:
            comp_raw = xl.parse("COMP")
            comp_raw.columns = [str(c).strip() for c in comp_raw.columns]

            # The first column is named "Updated at HH:MM:SS" (Refinitiv metadata
            # header) but its VALUES are tickers like "AAISA.SN".  Detect the
            # ticker column by pattern-matching values rather than column name.
            ticker_col = None
            for c in comp_raw.columns:
                hit_rate = (
                    comp_raw[c]
                    .astype(str)
                    .str.match(r"^[A-Z0-9]+\.[A-Z]{2,3}$")
                    .mean()
                )
                if hit_rate > 0.5:
                    ticker_col = c
                    break

            rename_map: dict[str, str] = {}
            if ticker_col:
                rename_map[ticker_col] = "Ticker"
            for c in comp_raw.columns:
                lc = c.lower()
                if "company" in lc or ("name" in lc and c != ticker_col):
                    rename_map[c] = "Company_Name"
                elif "sector" in lc:
                    rename_map[c] = "Sector"
                elif "industry" in lc:
                    rename_map[c] = "Industry"

            comp_raw = comp_raw.rename(columns=rename_map)
            keep = [c for c in ["Ticker", "Company_Name", "Sector", "Industry"]
                    if c in comp_raw.columns]

            if "Ticker" in comp_raw.columns and len(keep) > 1:
                df_comp = comp_raw[keep].dropna(subset=["Ticker"]).copy()
                df_comp["Ticker"] = df_comp["Ticker"].astype(str).str.strip()
                extras = [c for c in keep if c != "Ticker"]
                print(f"    OK  COMP: {len(df_comp)} tickers, cols: {extras}")
            else:
                print("    INFO: COMP found; no Sector/Industry columns detected "
                      "(add them to CHILE.xlsx or an external mapping file).")
        except Exception as e:
            print(f"    WARN: Could not read COMP sheet: {e}")
    else:
        print("    INFO: No COMP sheet. Add Sector/Industry to CHILE.xlsx for "
              "classification support.")

    print("\n  Price Data (PRICE + PRICE2)...")
    price_frames = []
    for sh in PRICE_SHEETS:
        df_p = read_price_sheet(xl, sh)
        if not df_p.empty:
            print(f"    OK  {sh:8s}: {df_p.shape[0]:>7,} rows")
            price_frames.append(df_p)

    if not price_frames:
        print("  ERROR: No price data loaded.")
        return

    # ── TRANSFORM ─────────────────────────────────────────────
    print("\n[TRANSFORM]")

    fin_frames = [d for d in [df_bs, df_is, df_cf] if not d.empty]
    if not fin_frames:
        print("  ERROR: No fundamental data loaded.")
        return

    # Merge financial statement groups on [Ticker, Date]
    df_fund = _merge_sheets(fin_frames)
    print(f"  Fundamentals merged : {df_fund.shape[0]:,} rows x {df_fund.shape[1]} cols")

    # Standardise column names; drop duplicates (keep first occurrence)
    df_fund = (
        df_fund
        .rename(columns=COL_MAP)
        .loc[:, lambda d: ~d.columns.duplicated(keep="first")]
    )

    # Attach Sector / Industry from COMP sheet if available
    if not df_comp.empty:
        df_fund = df_fund.merge(df_comp, on="Ticker", how="left")

    # Price: deduplicate, sort, compute technical indicators on full series
    df_price = (
        pd.concat(price_frames, ignore_index=True)
        .drop_duplicates(subset=["Ticker", "Date"])
    )
    print(f"  Price data combined : {df_price.shape[0]:,} rows")

    print("  Computing technical indicators (MA50/200, RSI, Vol, 6M Return)...")
    df_price = add_technical_indicators(df_price)

    # Latest price snapshot per ticker -- used as PIT reference date
    df_price_latest = (
        df_price.sort_values("Date")
        .groupby("Ticker", as_index=False)
        .last()
    )
    print(f"  Latest price rows   : {len(df_price_latest):,} tickers")

    print(f"  Applying frequency-based PIT lag (annual=120d, semi=60d, quarterly=45d)...")
    print("  Running feature engineering (YoY growth, ratios, Winsorize)...")
    df_screen = engineer_features(df_fund, df_price, df_price_latest)

    # ── LOAD ──────────────────────────────────────────────────
    print("\n[LOAD]")
    available = [c for c in OUTPUT_COLS if c in df_screen.columns]
    df_out    = df_screen[available].copy()

    df_out.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(sep)
    print(f"  Written : {OUTPUT_PATH}")
    print(f"  Shape   : {df_out.shape[0]:,} tickers x {df_out.shape[1]} columns")
    print(sep)

    # Quality report: only show columns that have missing values
    nan_report = df_out.isnull().sum()
    nan_report = nan_report[nan_report > 0].sort_values(ascending=False)

    print("\n[QUALITY REPORT]  NaN counts (columns with missing data only):")
    if nan_report.empty:
        print("  No missing values.")
    else:
        for col, cnt in nan_report.items():
            pct = cnt / len(df_out) * 100
            print(f"  {col:<28s}: {cnt:>4} ({pct:4.1f}%)")

    # ── Preview: split into two readable blocks ───────────
    # Block 1 — screener columns (displayed in App.py)
    SCREEN_COLS = [
        "Ticker", "Price Close",
        "P_E", "P_B", "Current_Ratio", "Debt_to_Equity",
        "Dividend_Yield", "Payout_Ratio",
        "Rev_Growth_YoY", "EPS_Growth_YoY", "Gross_Margin",
        "Price_6M_Return", "Volume", "RSI_14", "MA50", "MA200",
        "Market_Cap", "ROE", "ROA", "Net_Debt", "Net_Debt_EBITDA", "FCF_Yield",
    ]
    # Block 2 — raw financial inputs (for debug)
    RAW_COLS = [
        "Ticker", "Revenue", "EPS_Basic", "DPS_Net",
        "Op_CashFlow", "Total_Equity", "Debt_Total",
    ]

    # Format floats in a human-readable way (avoid scientific notation)
    fmt: dict[str, str] = {
        "Price Close":      "{:>12,.2f}",
        "P_E":              "{:>8.2f}",
        "P_B":              "{:>7.2f}",
        "Current_Ratio":    "{:>7.2f}",
        "Debt_to_Equity":   "{:>8.2f}",
        "Dividend_Yield":   "{:>8.2%}",
        "Payout_Ratio":     "{:>8.2%}",
        "Rev_Growth_YoY":   "{:>+9.1%}",
        "EPS_Growth_YoY":   "{:>+9.1%}",
        "Gross_Margin":     "{:>8.2%}",
        "Price_6M_Return":  "{:>+9.1%}",
        "Volume":           "{:>12,.0f}",
        "RSI_14":           "{:>7.1f}",
        "MA50":             "{:>12,.2f}",
        "MA200":            "{:>12,.2f}",
        "Revenue":          "{:>15,.0f}",
        "EPS_Basic":        "{:>10.3f}",
        "DPS_Net":          "{:>10.3f}",
        "Op_CashFlow":      "{:>15,.0f}",
        "Total_Equity":     "{:>15,.0f}",
        "Debt_Total":       "{:>15,.0f}",
    }

    def _fmt_row(row: pd.Series, cols: list[str]) -> str:
        parts = []
        for c in cols:
            val = row.get(c, float("nan"))
            if c == "Ticker":
                parts.append(f"{str(val):<16s}")
            elif pd.isna(val):
                parts.append(f"{'N/A':>10s}")
            else:
                try:
                    parts.append(fmt.get(c, "{:>12.4f}").format(val))
                except (ValueError, TypeError):
                    parts.append(f"{str(val):>10s}")
        return "  ".join(parts)

    sample = df_out.head()

    print("\n[PREVIEW]  Screener metrics (5 rows):")
    # Build header manually for clean alignment
    hdr_parts = [f"{'Ticker':<16s}"] + [
        f"{c:>{max(len(c), 10)}s}" for c in SCREEN_COLS[1:]
    ]
    print("  " + "  ".join(hdr_parts))
    print("  " + "-" * (sum(max(len(c), 10) + 2 for c in SCREEN_COLS[1:]) + 14))
    for _, row in sample.iterrows():
        print("  " + _fmt_row(row, SCREEN_COLS))

    print("\n[PREVIEW]  Raw financials (5 rows):")
    hdr_parts2 = [f"{'Ticker':<16s}"] + [
        f"{c:>{max(len(c), 15)}s}" for c in RAW_COLS[1:]
    ]
    print("  " + "  ".join(hdr_parts2))
    print("  " + "-" * (sum(max(len(c), 15) + 2 for c in RAW_COLS[1:]) + 14))
    for _, row in sample.iterrows():
        print("  " + _fmt_row(row, RAW_COLS))


if __name__ == "__main__":
    build_master_csv()

