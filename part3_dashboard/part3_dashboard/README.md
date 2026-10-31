# Really Big Bank — BUSA3022 Analytics Implementation Plan & Portfolio

## 3. Dashboard and Reporting Plan

This folder contains Part 3 of the Really Big Bank market-intelligence proof of concept. It turns the **curated** S&P 500 (`^GSPC`) and CBOE VIX (`VIXCLS`) dataset from Part 2 into a single dashboard view, without changing the Part 2 files. The dashboard answers the business question: **How has market activity trended over the past 90 days, and is there anything we should be watching?**

![Working dashboard](outputs/dashboard_screenshot.png)

### 3.1 Audience and Design Approach

The audience is **financially literate but non-technical** managers. The dashboard is one page, read from top to bottom like a story:

| Order | Section | What it shows | Why it is there |
|---|---|---|---|
| 1 | **Headline signal** | Red/Amber/Green status, one plain-English sentence and key figures | A reader who stops here still gets the answer |
| 2 | **Trend** | S&P 500 close for the last 90 trading sessions with the Part 2 20-session moving average (SMA20) | Shows the market's direction; a close below the average is an early sign of weakening momentum |
| 3 | **Macro overlay** | S&P 500 and VIX on the same chart, each with its own scale | Shows whether shares and expected volatility are still moving in opposite directions |
| 4 | **Signal history** | VIX against the Red/Amber/Green bands | Shows how today's signal was reached and how often it has changed |

Candlesticks, trading volume, technical indicators and jargon were **deliberately left out** because they add detail without answering the question. Every colour is paired with a status word so the dashboard also works for colour-blind readers and in black-and-white print.

The wireframe (`wireframe.png`) is the design portfolio artifact; values in [brackets] are placeholders that the working dashboard fills in.

### 3.2 Trend and Macro Overlay

VIX normally moves **opposite** to shares: when the S&P 500 rises, VIX usually falls. The dashboard measures this with a **20-session correlation** between daily S&P 500 returns and daily VIX changes.

| Correlation | Meaning | Shown as |
|---|---|---|
| Close to −1 | Normal pattern: shares and VIX move in opposite directions | No shading |
| Above **−0.30** | Usual pattern has weakened (divergence) | Yellow shading on the overlay chart |

Missing VIX sessions are **not filled in**. They appear as gaps in the line, consistent with the Part 2 `vix_gap_flag` rule.

### 3.3 Red/Amber/Green Signal and Threshold Justification

The signal uses the **latest available VIX close**, because VIX is forward-looking and suits the question "is there anything we should be watching?".

| Status | Rule | Meaning | Justification |
|---|---|---|---|
| **Green** | VIX < 20 | Calm | VIX has averaged about 19.7 since 1990 (AIMA, 2016) |
| **Amber** | 20 ≤ VIX < 30 | Above normal — monitor daily | Expected volatility above its long-run average |
| **Red** | VIX ≥ 30 | Stress — escalate | Readings above 30 are widely read as investor anxiety (Hartford Funds, 2024) |
| **Grey** | Latest VIX more than 3 sessions old | Data issue — do not rely on the signal | Prevents an out-of-date reading showing a false Green |

All thresholds sit in **one configuration block** at the top of `part3_dashboard.py`, so they can be reviewed against the bank's risk appetite without touching chart code.

### 3.4 Working Proof of Concept

The saved outputs were generated from the actual **Part 2 curated snapshot** (`part2_data_curation/real_outputs/curated_sp500_vix.csv`), not new provider downloads.

| Evidence | Verified result |
|---|---:|
| Sessions shown | 90 (23 Jun – 28 Oct 2026) |
| Latest S&P 500 close (28 Oct 2026) | 7,743.98 |
| Change over 90 sessions | +5.1% |
| Latest SMA20 | 7,734.34 (close is above it) |
| Latest VIX (27 Oct 2026) | 17.52 |
| **Latest signal** | **Green** |
| 20-session S&P 500 / VIX correlation | −0.88 |
| Signal history | 89 Green, 1 Amber (29 Jul 2026, VIX 20.66), 0 Red |
| Divergence sessions shaded | 1 (28 Aug 2026, correlation −0.27) |
| Sessions missing VIX | 1 (28 Oct 2026, left blank) |
| Automated Part 3 tests passed | 12 |

The tests check Red/Amber/Green boundaries, stale and missing VIX, the 90-session window, schema failure, loading the real Part 2 file, one-day divergence shading and written outputs.

**Run from the group repository root:**

```bash
python -m pip install -r part3_dashboard/requirements.txt
python -m pytest -q part3_dashboard/tests
python part3_dashboard/part3_dashboard.py \
  --curated part2_data_curation/real_outputs/curated_sp500_vix.csv
```

To rebuild the inputs directly from Yahoo Finance and FRED instead (internet required), use `python part3_dashboard/part3_dashboard.py --fetch`.

Alternatively, run `Part3_Dashboard.ipynb` in Google Colab. Files used for the proof of concept:

| File / folder | Purpose |
|---|---|
| `part3_dashboard.py` | Signal rules, correlation, chart building and run log |
| `Part3_Dashboard.ipynb` | Executable notebook demonstration |
| `tests/test_part3_dashboard.py` | Twelve automated tests |
| `wireframe.png` / `wireframe.html` | Dashboard wireframe (portfolio artifact) |
| `outputs/dashboard.html` | Interactive dashboard (hover shows exact values) |
| `outputs/dashboard_screenshot.png` | Static image of the dashboard used in the report |
| `outputs/rag_signal_history.csv` | Signal status for every session shown |
| `outputs/dashboard_log.csv` | Structured, UTC-stamped run log |
| `requirements.txt` | Part 3-specific Python dependencies |

### 3.5 AI Agent Lens and Leadership

Claude (Anthropic, 2026) assisted with the dashboard code. AI-assisted code was accepted only after the **rendered dashboard was checked against the data**, not merely because it executed.

| # | Problem found | How it was caught | Correction |
|---|---|---|---|
| 1 | Red/Amber/Green bands on the VIX chart did not appear | Visual check of the rendered chart | Chart drawing order changed; bands drawn with explicit axis references |
| 2 | 28 Aug 2026 (correlation −0.27) should have been shaded yellow but was not | Comparing the chart with `rag_signal_history.csv` | A one-day band had zero width; bands now padded by half a day each side. Test added that fails on the old code and passes now |
| 3 | First drafts used jargon, unrounded axes and colour-only status | Review against the audience | Prompt revised: plain words, rounded numbers, one headline box, a status word beside every colour |

To help analysts present a clear message, the team should use a shared template: **state the question, give the answer first, use one chart per point and label anything unusual**. Before release, a non-technical colleague should be able to repeat the main message in one sentence. Changes to thresholds or AI-assisted code require peer review and rerunning the tests. This is a limited proof of concept, not a production trading or banking decision engine.
