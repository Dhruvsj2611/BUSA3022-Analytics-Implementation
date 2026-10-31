"""
BUSA3022 - Part 3: Dashboard & Reporting proof of concept
Really Big Bank - Market Intelligence dashboard (S&P 500 + CBOE VIX)

Answers: "How has market activity trended over the past 90 days,
          and is there anything we should be watching?"

Input  : the Part 2 curated CSV (one row per S&P 500 session, with close,
         SMA20 and the same-day VIX where available + vix_gap_flag).
         If no curated file is supplied, the script can rebuild the same
         inputs from Yahoo Finance + FRED using the Part 2 metric rules
         (use --fetch; needs internet, e.g. Google Colab).
Output : outputs/dashboard.html        interactive dashboard (3 components)
         outputs/rag_signal_history.csv RAG status for every session shown
         outputs/dashboard_log.csv      UTC-stamped run log

Usage  : python part3_dashboard.py --curated ../part2_data_curation/outputs/<curated>.csv
         python part3_dashboard.py --fetch
"""
from __future__ import annotations

import argparse
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --------------------------------------------------------------------------
# 1. Business rules (kept in one place so they can be reviewed and changed)
# --------------------------------------------------------------------------
WINDOW_DAYS = 90              # dashboard look-back, in CALENDAR days (brief: "past 90 days")
SMA_WINDOW = 20               # must match Part 2 SMA20 definition
CORR_WINDOW = 20              # trading sessions used for the S&P/VIX correlation
CORR_MIN_PAIRS = 15           # min. sessions with both daily moves, so one missing VIX day
                              # (e.g. 28 Oct 2026) does not blank the measure
VIX_AMBER = 20.0              # >= 20: above recent average (18.93 in 2025, MacroTrends) -> Amber
VIX_RED = 30.0                # >= 30: widely read as investor anxiety (Hartford Funds 2024) -> Red
MAX_VIX_STALENESS = 3         # sessions; older than this -> Grey (data issue)
WEAK_INVERSE_CORR = -0.30     # corr above this = usual inverse link weak (|r| < 0.3 is
                              # conventionally "weak", Cohen 1988) -> yellow divergence shading

RAG_COLOURS = {"Green": "#1a9850", "Amber": "#f59e0b", "Red": "#d73027",
               "Grey": "#9ca3af"}
RAG_MEANING = {
    "Green": "Calm: expected volatility at or below its long-run average.",
    "Amber": "Watch: expected volatility above normal - monitor daily.",
    "Red": "Stress: expected volatility at crisis-type levels - escalate.",
    "Grey": "Data issue: VIX is out of date - do not rely on the signal.",
}

# Accepted column names in the Part 2 curated file (first match wins).
COLUMN_ALIASES = {
    "date": ["market_session_date", "date", "session_date", "Date", "trade_date"],
    "close": ["close", "sp500_close", "spx_close", "gspc_close", "Close"],
    "sma20": ["sma20", "sma_20", "sp500_sma20", "SMA20"],
    "vix": ["vix", "vix_close", "vixcls", "VIXCLS", "VIX"],
    "vix_gap_flag": ["vix_gap_flag"],
}

OUT_DIR = Path(__file__).resolve().parent / "outputs"
RUN_ID = uuid.uuid4().hex[:8]
_log: list[dict] = []


def log(event: str, rows: int | None = None, level: str = "INFO") -> None:
    _log.append({"utc_timestamp": datetime.now(timezone.utc).isoformat(),
                 "run_id": RUN_ID, "level": level, "event": event,
                 "rows": rows})
    print(f"[{level}] {event}" + (f" (rows={rows})" if rows is not None else ""))


# --------------------------------------------------------------------------
# 2. Load data
# --------------------------------------------------------------------------
def _pick(df: pd.DataFrame, key: str, required: bool = True) -> str | None:
    for c in COLUMN_ALIASES[key]:
        if c in df.columns:
            return c
    if required:
        raise KeyError(f"Curated file has no '{key}' column. Looked for "
                       f"{COLUMN_ALIASES[key]}; found {list(df.columns)}")
    return None


def load_curated(path: str | Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    cols = {k: _pick(raw, k, required=k in ("date", "close", "vix"))
            for k in COLUMN_ALIASES}
    df = pd.DataFrame({k: raw[c] for k, c in cols.items() if c})
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
    df = df.sort_values("date").reset_index(drop=True)
    if "sma20" not in df:
        log("SMA20 not in curated file - recalculated with Part 2 rule",
            level="WARN")
        df["sma20"] = df["close"].rolling(SMA_WINDOW, min_periods=SMA_WINDOW).mean()
    if "vix_gap_flag" not in df:
        df["vix_gap_flag"] = df["vix"].isna()
    log(f"Loaded curated file {Path(path).name}", len(df))
    return df


def fetch_live(days: int = 180) -> pd.DataFrame:
    """Rebuild the curated inputs from source (same rules as Part 2)."""
    import yfinance as yf  # pre-installed in Google Colab

    start = (pd.Timestamp.today() - pd.Timedelta(days=days)).date()
    spx = yf.download("^GSPC", start=str(start), progress=False, auto_adjust=False)
    if isinstance(spx.columns, pd.MultiIndex):
        spx.columns = spx.columns.get_level_values(0)
    spx = spx.reset_index()[["Date", "Close"]].rename(
        columns={"Date": "date", "Close": "close"})
    vix = pd.read_csv(
        f"https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS&cosd={start}",
        na_values=".")
    vix.columns = ["date", "vix"]
    for d in (spx, vix):
        d["date"] = pd.to_datetime(d["date"]).dt.tz_localize(None).dt.normalize()
    # S&P 500 calendar defines the time axis (left join, as in Part 2 s2.2)
    df = spx.merge(vix, on="date", how="left").sort_values("date")
    df["sma20"] = df["close"].rolling(SMA_WINDOW, min_periods=SMA_WINDOW).mean()
    df["vix_gap_flag"] = df["vix"].isna()
    log("Fetched live data from Yahoo Finance + FRED", len(df))
    return df.reset_index(drop=True)


# --------------------------------------------------------------------------
# 3. Dashboard calculations
# --------------------------------------------------------------------------
def rag_status(vix_value: float | None, sessions_stale: int = 0) -> str:
    """Red/Amber/Green rule. Grey when the VIX reading is missing or stale."""
    if vix_value is None or pd.isna(vix_value) or sessions_stale > MAX_VIX_STALENESS:
        return "Grey"
    if vix_value >= VIX_RED:
        return "Red"
    if vix_value >= VIX_AMBER:
        return "Amber"
    return "Green"


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    # Missing VIX is NOT back-filled into the data; for the signal we use the
    # latest *available* reading and record how many sessions old it is.
    d["vix_last_available"] = d["vix"].ffill()
    has_vix = d["vix"].notna()
    last_vix_pos = pd.Series(np.where(has_vix, np.arange(len(d)), np.nan)).ffill()
    d["vix_sessions_stale"] = (np.arange(len(d)) - last_vix_pos).fillna(999).astype(int)
    d["rag"] = [rag_status(v, s) for v, s in
                zip(d["vix_last_available"], d["vix_sessions_stale"])]
    # Rolling correlation of daily % moves (only sessions where both exist)
    d["spx_ret"] = d["close"].pct_change() * 100
    d["vix_chg"] = d["vix"].pct_change(fill_method=None) * 100
    d["corr20"] = d["spx_ret"].rolling(CORR_WINDOW, min_periods=CORR_MIN_PAIRS).corr(d["vix_chg"])
    # Display window = last 90 CALENDAR days. SMA20 and the correlation were
    # calculated above on the full trading-session history, so the first day
    # shown already has complete 20-session windows.
    end = d["date"].max()
    start = end - pd.Timedelta(days=WINDOW_DAYS)
    before = d[d["date"] <= start]
    # 90-day change is measured from the last close on/before the window start
    d["baseline_close"] = before["close"].iloc[-1] if len(before) else d.loc[d["date"] > start, "close"].iloc[0]
    d["baseline_date"] = before["date"].iloc[-1] if len(before) else d.loc[d["date"] > start, "date"].iloc[0]
    d = d[d["date"] > start].reset_index(drop=True)
    log(f"Prepared last {WINDOW_DAYS} calendar days "
        f"({d['date'].iloc[0]:%d %b %Y} to {end:%d %b %Y}, {len(d)} trading sessions)", len(d))
    if d["vix_gap_flag"].any():
        log(f"{int(d['vix_gap_flag'].sum())} session(s) without same-day VIX "
            "- shown as gaps, signal uses last available reading", level="WARN")
    return d


def headline(d: pd.DataFrame) -> dict:
    last = d.iloc[-1]
    vix_rows = d[d["vix"].notna()]
    vix_date = vix_rows["date"].iloc[-1] if len(vix_rows) else None
    return {
        "as_at": last["date"],
        "close": last["close"],
        "chg_90": (last["close"] / d["baseline_close"].iloc[0] - 1) * 100,
        "baseline_date": d["baseline_date"].iloc[0],
        "above_sma": bool(last["close"] >= last["sma20"]) if pd.notna(last["sma20"]) else None,
        "vix": last["vix_last_available"],
        "vix_date": vix_date,
        "corr": d["corr20"].dropna().iloc[-1] if d["corr20"].notna().any() else np.nan,
        "rag": last["rag"],
        "high": d["close"].max(), "low": d["close"].min(),
    }


def story_text(h: dict) -> str:
    """One plain-English sentence that answers the business question."""
    trend = "up" if h["chg_90"] >= 0 else "down"
    sma = ("above" if h["above_sma"] else "below") if h["above_sma"] is not None else "near"
    link = ("moving in opposite directions as usual" if pd.isna(h["corr"]) or h["corr"] <= WEAK_INVERSE_CORR
            else "not moving in their usual opposite directions - worth watching")
    return (f"The S&P 500 is {trend} {abs(h['chg_90']):.1f}% over the past 90 days and "
            f"sits {sma} its 20-session average. VIX is {h['vix']:.1f} "
            f"({h['rag']}); shares and volatility are {link}.")


# --------------------------------------------------------------------------
# 4. Build the dashboard
# --------------------------------------------------------------------------
def build_figure(d: pd.DataFrame, h: dict) -> go.Figure:
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.11,
        row_heights=[0.42, 0.33, 0.25],
        specs=[[{}], [{"secondary_y": True}], [{}]],
        subplot_titles=(
            "1  Trend - S&P 500 close vs its 20-session average",
            "2  Macro overlay - S&P 500 (blue, left axis) vs VIX 'fear gauge' (purple, right axis)",
            "3  Signal history - VIX against Red/Amber/Green thresholds"))

    hov = "%{x|%d %b %Y}<br>%{y:,.0f}<extra>%{fullData.name}</extra>"
    # Panel 1: price + rolling average
    fig.add_trace(go.Scatter(x=d["date"], y=d["close"], name="S&P 500 close",
                             line=dict(color="#1f3b73", width=2), hovertemplate=hov),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=d["date"], y=d["sma20"], name="20-session average",
                             line=dict(color="#f28e2b", width=2, dash="dash"),
                             hovertemplate=hov), row=1, col=1)

    # Panel 2: macro overlay (dual axis) + shaded divergence periods
    fig.add_trace(go.Scatter(x=d["date"], y=d["close"], name="S&P 500 (left)",
                             line=dict(color="#1f3b73", width=1.6),
                             showlegend=False, hovertemplate=hov),
                  row=2, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(x=d["date"], y=d["vix"], name="VIX (right)",
                             line=dict(color="#7b3294", width=1.6),
                             connectgaps=False,
                             hovertemplate="%{x|%d %b %Y}<br>VIX %{y:.1f}<extra></extra>"),
                  row=2, col=1, secondary_y=True)
    weak = d["corr20"] > WEAK_INVERSE_CORR
    for start, end in _runs(d["date"], weak):
        # pad half a day each side so a single-session run is still visible
        fig.add_vrect(x0=pd.Timestamp(start) - pd.Timedelta(hours=12),
                      x1=pd.Timestamp(end) + pd.Timedelta(hours=12),
                      fillcolor="#fde68a", opacity=0.45,
                      line_width=0, layer="below", row=2, col=1)
    if weak.any():
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
                                 marker=dict(size=12, color="#fde68a", symbol="square"),
                                 name="Yellow = 20-session correlation above −0.30 (usual opposite move weakened)"), row=2, col=1)


    # Panel 3: RAG bands + VIX
    top = max(40.0, float(np.nanmax(d["vix"])) + 3 if d["vix"].notna().any() else 40.0)
    fig.add_trace(go.Scatter(x=d["date"], y=d["vix"], name="VIX close",
                             line=dict(color="#111827", width=1.6), showlegend=False,
                             hovertemplate="%{x|%d %b %Y}<br>VIX %{y:.1f}<extra></extra>"),
                  row=3, col=1)
    # bands added after the trace (plotly skips shapes on empty subplots)
    for lo, hi, col in [(0, VIX_AMBER, "Green"), (VIX_AMBER, VIX_RED, "Amber"),
                        (VIX_RED, top, "Red")]:
        fig.add_hrect(y0=lo, y1=hi, fillcolor=RAG_COLOURS[col], opacity=0.15,
                      line_width=0, layer="below", row=3, col=1)
    fig.add_annotation(xref="x3 domain", yref="y4", x=0, y=1, xanchor="left", yanchor="bottom",
                       showarrow=False, text="Green < 20", font=dict(size=10, color="#4b5563"))
    for y, lab in [(VIX_AMBER, "Amber 20 to under 30"), (VIX_RED, "Red ≥ 30")]:
        fig.add_hline(y=y, line=dict(color="#6b7280", width=1, dash="dot"),
                      annotation_text=lab, annotation_position="top left",
                      annotation_font_size=10, row=3, col=1)

    # Header: RAG tile + KPIs + story
    rag = h["rag"]
    vix_note = (f"VIX {h['vix']:.1f} as at {h['vix_date']:%d %b}"
                if h["vix_date"] is not None else "VIX unavailable")
    fig.add_annotation(
        xref="paper", yref="paper", x=0, y=1.125, xanchor="left", yanchor="middle",
        showarrow=False, align="left", width=1040,
        text=(f"<b>Is there anything we should be watching?</b>  "
              f"<span style='color:{RAG_COLOURS[rag]}'><b>● {rag.upper()}</b></span>"
              f" - {RAG_MEANING[rag]}<br>"
              f"<span style='font-size:12px;color:#374151'>{story_text(h)}</span><br>"
              f"<span style='font-size:12px;color:#374151'>S&P 500 <b>{h['close']:,.0f}</b>"
              f" ({h['chg_90']:+.1f}% over 90 days)  |  {vix_note}  |  "
              f"20-session S&P/VIX correlation <b>{h['corr']:+.2f}</b> (normal: below −0.30)</span>"),
        font=dict(size=14), bgcolor="#f9fafb", bordercolor=RAG_COLOURS[rag],
        borderwidth=2, borderpad=8)

    fig.update_layout(
        title=dict(text=("Really Big Bank - Market Activity, past 90 days"
                         f"<br><sup>Data to {h['as_at']:%d %b %Y} | Sources: Yahoo "
                         "Finance (^GSPC), FRED (VIXCLS) | Gaps = no VIX published "
                         "for that session | Price axes are zoomed to the data range, not from zero</sup>"), x=0, y=0.985),
        template="simple_white", height=1000, margin=dict(t=160, l=70, r=70, b=70), width=1200,
        hovermode="x unified", font=dict(family="Arial", size=12),
        legend=dict(orientation="h", y=-0.075, x=0))
    fig.update_yaxes(title_text="S&P 500 index level", row=1, col=1, tickformat=",")
    fig.update_yaxes(title_text="S&P 500 (left)", title_font_color="#1f3b73", row=2, col=1,
                     secondary_y=False, tickformat=",")
    fig.update_yaxes(title_text="VIX (right)", title_font_color="#7b3294", row=2, col=1,
                     secondary_y=True, showgrid=False,
                     tickformat=".0f")
    fig.update_yaxes(title_text="VIX level", range=[0, top], row=3, col=1)
    fig.update_xaxes(title_text="US trading date", title_font_size=11, row=3, col=1)
    fig.update_xaxes(title_text="Two different scales: compare the directions of the lines, not where they cross",
                     title_font=dict(size=11, color="#4b5563"), row=2, col=1)
    # Dates under every chart (shared x-axes hide them on the upper panels by default)
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])], tickformat="%d %b",
                     showticklabels=True)
    return fig


def _runs(dates: pd.Series, mask: pd.Series):
    """Contiguous date ranges where mask is True."""
    out, start, prev = [], None, None
    for dt, m in zip(dates, mask.fillna(False)):
        if m and start is None:
            start = dt
        if not m and start is not None:
            out.append((start, prev)); start = None
        prev = dt
    if start is not None:
        out.append((start, prev))
    return out


# --------------------------------------------------------------------------
def main(argv=None) -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("--curated", help="Part 2 curated CSV")
    ap.add_argument("--fetch", action="store_true", help="rebuild inputs from source")
    ap.add_argument("--out", default=str(OUT_DIR))
    a = ap.parse_args(argv)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    df = fetch_live() if a.fetch or not a.curated else load_curated(a.curated)
    d = prepare(df)
    h = headline(d)
    fig = build_figure(d, h)
    fig.write_html(out / "dashboard.html", include_plotlyjs=True)
    html = (out / "dashboard.html").read_text(encoding="utf-8")
    (out / "dashboard.html").write_text(html.replace(
        "<head>", "<head><title>Really Big Bank - Market Activity, past 90 days</title>", 1),
        encoding="utf-8")
    d[["date", "close", "sma20", "vix", "vix_gap_flag", "vix_last_available",
       "vix_sessions_stale", "rag", "corr20"]].to_csv(
        out / "rag_signal_history.csv", index=False)
    log(f"Dashboard written; latest signal {h['rag']} "
        f"(VIX {h['vix']:.2f}, corr {h['corr']:+.2f})", len(d))
    pd.DataFrame(_log).to_csv(out / "dashboard_log.csv", index=False)
    print("\n" + story_text(h))
    return h


if __name__ == "__main__":
    main()
