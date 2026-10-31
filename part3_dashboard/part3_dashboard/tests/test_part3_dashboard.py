"""Part 3 automated tests: RAG rule, missing-VIX handling and outputs.
Run from the repository root: python -m pytest -v part3_dashboard/tests
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import part3_dashboard as p3  # noqa: E402


# 1. Threshold boundaries behave exactly as documented
@pytest.mark.parametrize("vix,expected", [
    (12.0, "Green"), (19.99, "Green"), (20.0, "Amber"),
    (29.99, "Amber"), (30.0, "Red"), (55.0, "Red")])
def test_rag_thresholds(vix, expected):
    assert p3.rag_status(vix) == expected


# 2. Missing or stale VIX never produces a false "Green"
def test_missing_or_stale_vix_is_grey():
    assert p3.rag_status(None) == "Grey"
    assert p3.rag_status(np.nan) == "Grey"
    assert p3.rag_status(15.0, sessions_stale=p3.MAX_VIX_STALENESS + 1) == "Grey"
    assert p3.rag_status(15.0, sessions_stale=1) == "Green"


def _sample(n=120, vix_gap_last=True):
    dates = pd.bdate_range("2026-04-01", periods=n)
    close = np.linspace(7000, 7700, n)
    vix = np.full(n, 17.0)
    df = pd.DataFrame({"date": dates, "close": close, "vix": vix})
    if vix_gap_last:
        df.loc[n - 1, "vix"] = np.nan          # e.g. 28 Oct 2026 in Part 2
    df["sma20"] = df["close"].rolling(20, min_periods=20).mean()
    df["vix_gap_flag"] = df["vix"].isna()
    return df


# 3. Window = past 90 CALENDAR days; gap kept visible, not back-filled
def test_window_is_90_calendar_days_and_gap_not_filled():
    d = p3.prepare(_sample())
    span = (d["date"].iloc[-1] - d["date"].iloc[0]).days
    assert span < p3.WINDOW_DAYS                      # nothing older than 90 days shown
    assert (d["date"].iloc[0] - d["baseline_date"].iloc[0]).days >= 1
    assert pd.isna(d["vix"].iloc[-1])                 # raw gap preserved
    assert d["vix_last_available"].iloc[-1] == 17.0   # signal uses last reading
    assert d["vix_sessions_stale"].iloc[-1] == 1
    assert d["rag"].iloc[-1] == "Green"


# 3b. SMA20 still uses 20 TRADING SESSIONS from the full history (no warm-up gap)
def test_sma20_uses_trading_sessions_not_window():
    src = _sample()
    d = p3.prepare(src)
    first = d["date"].iloc[0]
    pos = src.index[src["date"] == first][0]
    assert d["sma20"].notna().all()
    assert d["sma20"].iloc[0] == pytest.approx(src["close"].iloc[pos - 19:pos + 1].mean())


# 3c. 90-day change is measured from the last close on/before the window start
def test_90_day_change_baseline():
    src = _sample()
    d = p3.prepare(src)
    h = p3.headline(d)
    base = src.loc[src["date"] <= src["date"].max() - pd.Timedelta(days=90), "close"].iloc[-1]
    assert h["chg_90"] == pytest.approx((src["close"].iloc[-1] / base - 1) * 100)


# 3d. Grey boundary: exactly 3 sessions old still coloured, 4 sessions old is Grey
def test_staleness_boundary():
    assert p3.rag_status(15.0, sessions_stale=p3.MAX_VIX_STALENESS) == "Green"
    assert p3.rag_status(25.0, sessions_stale=p3.MAX_VIX_STALENESS + 1) == "Grey"


# 3e. Divergence rule: shaded only when correlation is ABOVE -0.30
@pytest.mark.parametrize("corr,shaded", [(-0.31, False), (-0.30, False), (-0.29, True), (0.2, True)])
def test_divergence_threshold(corr, shaded):
    dates = pd.bdate_range("2026-08-03", periods=30)
    d = p3.prepare(pd.DataFrame({"date": dates, "close": np.linspace(7000, 7100, 30),
                                 "sma20": 7050.0, "vix": 16.0, "vix_gap_flag": False}))
    d["corr20"] = -0.8
    d.loc[10, "corr20"] = corr
    fig = p3.build_figure(d, p3.headline(d))
    bands = [x for x in fig.layout.shapes if x.fillcolor == "#fde68a"]
    assert (len(bands) == 1) == shaded


# 4. Curated file with different column names is accepted; missing column fails loudly
def test_column_aliases_and_schema_failure(tmp_path):
    df = _sample().rename(columns={"close": "sp500_close", "vix": "vix_close"})
    f = tmp_path / "curated.csv"
    df.to_csv(f, index=False)
    assert {"close", "vix"} <= set(p3.load_curated(f).columns)
    df.drop(columns=["vix_close"]).to_csv(f, index=False)
    with pytest.raises(KeyError):
        p3.load_curated(f)


# 5. End-to-end: dashboard, signal history and log are written
def test_outputs_written(tmp_path):
    src = tmp_path / "curated.csv"
    _sample().to_csv(src, index=False)
    h = p3.main(["--curated", str(src), "--out", str(tmp_path / "out")])
    for name in ("dashboard.html", "rag_signal_history.csv", "dashboard_log.csv"):
        assert (tmp_path / "out" / name).exists()
    assert h["rag"] in p3.RAG_COLOURS


def test_real_part2_file_loads_if_present():
    """The real Part 2 output uses `market_session_date`; it must load without edits."""
    from pathlib import Path
    real = Path(__file__).resolve().parents[2] / "part2_data_curation/real_outputs/curated_sp500_vix.csv"
    if not real.exists():
        import pytest; pytest.skip("Part 2 real output not in this checkout")
    df = p3.load_curated(real)
    assert len(df) == 124 and df["vix"].isna().sum() == 1


def test_single_weak_session_is_visibly_shaded():
    """A one-day divergence must produce a yellow band with non-zero width."""
    dates = pd.bdate_range("2026-08-03", periods=30)
    d = p3.prepare(pd.DataFrame({"date": dates, "close": np.linspace(7000, 7100, 30),
                                 "sma20": 7050.0, "vix": 16.0, "vix_gap_flag": False}))
    d["corr20"] = -0.8
    d.loc[15, "corr20"] = -0.27
    fig = p3.build_figure(d, p3.headline(d))
    bands = [s for s in fig.layout.shapes if s.fillcolor == "#fde68a"]
    assert len(bands) == 1
    assert pd.Timestamp(bands[0].x1) > pd.Timestamp(bands[0].x0)
