# Really Big Bank — BUSA3022 Analytics Implementation Plan & Portfolio

## Project Overview

This repository supports the BUSA3022 Analytics Lead Case Study for the fictional Really Big Bank.

The project aims to develop a market-intelligence analytics system that helps management answer:

**How has market activity trended over the past 90 days, and is there anything we should be watching?**

The group project has four components:

1. **Data Pipeline:** Financial data ingestion, validation and quality logging.
2. **Data Curation:** Date alignment, financial metrics and transformation.
3. **Dashboard:** A 90-day market overview, macroeconomic comparison and Red/Amber/Green signal.
4. **Presentation and Integration:** Implementation rationale, working demonstrations, AI reflection and leadership considerations.

This is an academic proof of concept, not a production banking system.

## 1. Data Sources

| Dataset | Provider | Identifier | Frequency |
|---|---|---|---|
| S&P 500 Index | Yahoo Finance | `^GSPC` | Daily market observations |
| CBOE Volatility Index (VIX) | FRED | `VIXCLS` | Daily observations |

The S&P 500 represents broad US equity-market performance. VIX provides a forward-looking measure of expected market volatility, rather than historical realised volatility.

Approximately 180 calendar days of source data are requested to support the final 90-day dashboard and rolling calculations.

## 1.1 Pipeline Architecture

![Data Pipeline Architecture](diagrams/pipeline_architecture.png)

The implemented pipeline follows these stages:

1. Retrieve financial data using Python.
2. Preserve timestamped raw CSV snapshots.
3. Validate required columns and observation values.
4. Separate accepted records from problematic records.
5. Record data-quality events and validation outcomes.
6. Provide validated datasets for downstream processing.

Raw observations are kept separately from transformed data to support reproducibility and investigation.

## 1.2 Proof-of-Concept Results

**Execution date:** 29 October 2026.

| Dataset | Retrieved | Accepted | Quarantined |
|---|---:|---:|---:|
| S&P 500 | 124 | 124 | 0 |
| VIX | 127 | 127 | 0 |
| **Total** | **251** | **251** | **0** |

Observation coverage:

- S&P 500: 4 May 2026 to 28 October 2026.
- VIX: 4 May 2026 to 27 October 2026.

The latest VIX observation was one day behind the latest S&P 500 observation in this run. Source freshness must therefore be evaluated against publication timing rather than assuming both series update simultaneously.

### Source Verification

The saved data was compared with fresh downloads from the same providers.

- S&P 500: 124 of 124 closing values matched within the comparison tolerance.
- VIX: 127 of 127 observations matched.
- No comparison dates were missing.

These are repeat-download consistency checks, not independent cross-provider verification.

See `docs/source_verification.csv`.

## 1.3 Data Quality and Failure Handling

The pipeline checks:

- Required column availability.
- Valid observation dates.
- Numeric and positive market-price values.
- Missing required values.
- Duplicate observation dates.

Controlled synthetic tests demonstrated detection of missing values, duplicates, invalid dates and schema changes.

These deliberately introduced problems were test scenarios, not defects found in the live financial downloads.

The pipeline preserves raw data and creates structured quality logs rather than silently discarding invalid observations.

Relevant files:

- `tests/test_pipeline.py`
- `logs/data_quality_log.csv`
- `docs/pipeline_design.md`

## 1.4 How to Run the Proof of Concept

### Requirements

- Python 3
- Internet connection
- Packages listed in `requirements.txt`

### Local setup

From the repository's root folder, install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the validation tests:

```bash
python tests/test_pipeline.py
```

Run the pipeline:

```bash
python src/pipeline.py
```

Alternatively, open `notebooks/01_data_pipeline.ipynb` in Google Colab, install the dependencies, and execute the notebook cells using the repository root as the working directory.

The notebook contains the demonstrated live execution and supporting checks.

## 1.5 Project Files

| Path | Purpose |
|---|---|
| `src/pipeline.py` | Data retrieval and validation logic |
| `tests/test_pipeline.py` | Synthetic failure tests |
| `notebooks/01_data_pipeline.ipynb` | Executed notebook and verification evidence |
| `data/raw/` | Original timestamped source snapshots |
| `data/validated/` | Accepted datasets |
| `data/quarantine/` | Rejected records, when produced |
| `logs/data_quality_log.csv` | Structured execution and quality events |
| `diagrams/pipeline_architecture.png` | Pipeline architecture diagram |
| `docs/pipeline_design.md` | Design decisions and limitations |
| `docs/source_verification.csv` | Repeat-download comparison results |
| `docs/ai_verification_log.md` | AI-assisted coding issue and correction |
| `docs/handover_member2.md` | Downstream handover instructions |

## 1.6 Handover to Member 2

The data-curation team should begin with:

- `data/validated/market_validated.csv`
- `data/validated/macro_validated.csv`

Market fields:

`date`, `adj_close`, `close`, `high`, `low`, `open`, `volume`

Macro fields:

`date`, `vix`

Both series use US observation dates. Dates should be aligned explicitly, without arbitrarily shifting observations according to the Australian execution timezone.

Do not invent missing observations or assume every calendar date represents a trading day.

Member 2 has added a reproducible data-curation proof of concept (three calculated metrics, date alignment and an audit log). See [Part 2 technical documentation](part2_data_curation/README.md).

See `docs/handover_member2.md`.

## 1.7 AI Use and Verification

ChatGPT assisted with code development, testing guidance and documentation.

One genuine AI-assisted error occurred during source verification: an attempted pandas merge used incompatible date-column types (`object` and `datetime64[ns]`).

The error was detected through the Python traceback, corrected through consistent datetime conversion, and followed by successful comparison of all 124 S&P 500 closing values.

This error occurred in the verification script, not the underlying ingestion pipeline.

AI-generated code requires human review, controlled tests, source checks and documented corrections before it is accepted.

See `docs/ai_verification_log.md`.

## 1.8 Proposed Operations and Limitations

Daily GitHub Actions scheduling is proposed but has **not been deployed**.

The current working proof of concept was executed manually using Google Colab.

Further production requirements would include automated monitoring, retries, atomic writes, controlled releases, access management and clear responsibility for failed runs.

Validated CSV files currently represent latest-run snapshots, not a managed production data warehouse.

## 1.9 Group Collaboration

The four group members are responsible for:

- Member 1: Pipeline and source validation.
- Member 2: Data curation and calculated metrics.
- Member 3: Dashboard and reporting.
- Member 4: Presentation, integration and final consistency checks.

The technical components should retain consistent source identifiers, column definitions, observation-date conventions and documented assumptions.

Changes to shared data contracts should be discussed and recorded before downstream files are modified.

## Academic Note

This repository contains academic proof-of-concept work. Any generative-AI-produced text used in the assessed submission must be attributed in accordance with the revised assignment brief and the university's academic-integrity requirements.


## 2. Data Curation Plan

The Data Curation Plan transforms the validated S&P 500 (^GSPC) and CBOE VIX (VIXCLS) observations from Part 1 into consistent metrics for Really Big Bank's market-monitoring and future benchmarking objectives (Chicago Board Options Exchange [CBOE], n.d.; Yahoo Finance, n.d.). Original datasets remain unchanged, while a separate curated output supports the 90-day dashboard.

### 2.1 Calculated Metrics and Business Relevance

Three metrics were defined in plain language before AI-assisted transformation code was developed.

**1. 20-Session Simple Moving Average (SMA20):** The average S&P 500 closing price across the current and previous 19 trading sessions. It smooths short-term fluctuations and helps management identify underlying market trends.

SMA20(t) = [P(t) + P(t-1) + ... + P(t-19)] / 20

**2. Daily Percentage Return:** The percentage change in the S&P 500 closing price compared with the previous trading session. It measures daily market performance on a consistent scale, supporting future comparisons with bank performance.

R(t) = [P(t) / P(t-1) - 1] x 100

**3. 14-Return Annualised Volatility:** The sample standard deviation of the latest 14 daily decimal returns, annualised using the square root of 252 assumed trading sessions and converted to a percentage.

Vol14(t) = sample_SD[r(t-13), ..., r(t)] x sqrt(252) x 100

Here, \(P_t\) represents the S&P 500 closing price, while \(r_t\) represents its daily return expressed as a decimal. The volatility calculation uses the sample standard deviation (`ddof=1`) (pandas development team, n.d.-a).

This metric measures recent market variability. Comparing realised volatility with VIX, a forward-looking measure of expected market volatility, helps management identify differences between observed market movements and expectations (CBOE, n.d.).

### 2.2 Data Alignment and Time Zone Management

The S&P 500 trading calendar defines the common time axis. A same-day left join preserves all 124 S&P 500 observations while matching available VIX values by their US market-session dates.

The reconciliation identified **123 matching dates, one S&P 500 date without a corresponding VIX observation, and four VIX-only dates**. The unmatched VIX value remains blank and flagged, while VIX-only observations are retained separately for auditing rather than silently discarded.

Both sources use US market observation dates under the *America/New_York* convention. Date-only values are treated as session labels rather than UTC timestamps, preventing unintended date shifts. Any future timestamped inputs will require daylight-saving-aware conversion. The analysis assumes observation dates represent reporting sessions rather than verified publication times.

### 2.3 Data Quality and Missing-Value Treatment

A data-quality concern identified in Part 1 was the difference in source freshness: S&P 500 observations extended to 28 October 2026, while VIX observations ended on 27 October 2026. The unmatched VIX observation remains blank instead of being replaced with zero or an earlier value.

Expected calculation gaps are distinguished from genuine data-quality issues. SMA20 leaves its first 19 observations blank, daily return leaves its first observation blank, and 14-return volatility leaves its first 14 observations blank because the required historical observations are not yet available. These are expected calculation warm-up periods rather than data-quality failures.

In contrast, missing required source values, duplicate dates and invalid numeric values are identified through validation checks. Rejected records and their corresponding reasons are retained in the structured quality log, ensuring that data-quality issues remain traceable. This approach is consistent with explicit missing-value handling in pandas (pandas development team, n.d.-b).

### 2.4 Proof of Concept and Calculation Verification

The working Python proof of concept processes the validated datasets from Part 1, producing 124 curated market observations. Its calculations were independently checked against the source closing prices.

On 28 October 2026, the S&P 500 closing price was **7,743.9800**, with a daily return of **0.2768%**, SMA20 of **7,734.3391**, and 14-return annualised volatility of **10.8835%**.

Six automated tests passed, covering date handling, invalid-record quarantine, failure logging, metric calculations, missing VIX treatment and preservation of VIX-only audit dates.

The transformation script (`part2_data_curation/curation.py`), six automated tests (`part2_data_curation/tests/test_curation.py`), curated dataset (`part2_data_curation/real_outputs/curated_sp500_vix.csv`) and supporting audit files are available in the shared GitHub repository. These outputs provide reproducible calculation evidence and an analysis-ready dataset for the Part 3 dashboard and recorded presentation.

### 2.5 AI-Assisted Development and Data Modelling Standards

Before using AI to assist with transformation logic, the metric specifications defined each required input, look-back period, unit, business purpose and rule for incomplete calculation windows. These plain-language definitions in Section 2.1 provided criteria for reviewing AI-generated code rather than accepting it simply because it executed successfully. Numerical spot checks and six automated tests were used to verify calculation accuracy and date-alignment logic.

To maintain consistency, the team should document metric formulas, field names, date conventions and missing-data rules in a shared data dictionary. Analysts should follow these standards, review quality logs and rerun automated tests before approving changes. AI-assisted revisions must undergo the same verification process as manually developed code before dashboard use.

[README.md](https://github.com/user-attachments/files/34219383/README.md)
# Really Big Bank — BUSA3022 Analytics Implementation Plan & Portfolio

## 3. Dashboard and Reporting Plan

This folder contains Part 3 of the Really Big Bank market-intelligence proof of concept. It turns the **curated** S&P 500 (`^GSPC`) and CBOE VIX (`VIXCLS`) dataset from Part 2 into a single dashboard view, without changing the Part 2 files. The dashboard answers the business question: **How has market activity trended over the past 90 days, and is there anything we should be watching?**
<img width="2440" height="2016" alt="dashboard_screenshot" src="https://github.com/user-attachments/assets/ab8c519c-965e-4bc9-a636-a0189b543f13" />

### 3.1 Audience and Design Approach

The audience is **financially literate but non-technical** managers. The dashboard is one page, read from top to bottom like a story:

| Order | Section | What it shows | Why it is there |
|---|---|---|---|
| 1 | **Headline signal** | Red/Amber/Green status, one plain-English sentence and key figures | A reader who stops here still gets the answer |
| 2 | **Trend** | S&P 500 close for the **past 90 calendar days** with the Part 2 20-session moving average (SMA20) | Shows the market's direction; a close below the average is an early sign of weakening momentum |
| 3 | **Macro overlay** | S&P 500 (blue, left axis) and VIX (purple, right axis) on the same chart | Shows whether shares and expected volatility are still moving in opposite directions |
| 4 | **Signal history** | VIX against the Red/Amber/Green bands | Shows how today's signal was reached and how often it has changed |

**Window and session conventions.** The display window is the **past 90 calendar days** (the brief asks about "the past 90 days"), counted back from the latest S&P 500 session. The SMA20 and the correlation still count **trading sessions** and are calculated on the full history before the window is applied, so the first day shown already has complete 20-session values. The 90-day change is measured from the last close on or before the window start.

Candlesticks, trading volume, technical indicators and jargon were **deliberately left out** because they add detail without answering the question. Every colour is paired with a status word so the dashboard also works for colour-blind readers and in black-and-white print.

The wireframe (`wireframe.png`) is the design portfolio artifact; values in [brackets] are placeholders that the working dashboard fills in.

### 3.2 Trend and Macro Overlay

VIX normally moves **opposite** to shares: when the S&P 500 rises, VIX usually falls (Hartford Funds, 2026).

**Correlation warning rule.** For every session, the dashboard calculates the correlation between daily S&P 500 % returns and daily VIX % changes over the **last 20 trading sessions**. At least 15 sessions with both values are required, so a single missing VIX day does not blank the measure. A day is shaded yellow when the correlation is **above −0.30** (strictly greater). An absolute correlation below 0.30 is weaker than Cohen's (1988) "medium" benchmark, i.e. the usual opposite relationship has become weak.

| Correlation | Meaning | Shown as |
|---|---|---|
| −1 to −0.30 | Normal pattern: shares and VIX move in opposite directions | No shading |
| Above **−0.30** | Usual pattern has weakened (divergence) | Yellow shading on the overlay chart |

Because the two lines use different scales, the chart tells readers to compare the **directions** of the lines, not where they cross. Price axes are zoomed to the data range (not from zero); this is stated under the dashboard title.

Missing VIX sessions are **not filled in**. They appear as gaps in the line, consistent with the Part 2 `vix_gap_flag` rule.

### 3.3 Red/Amber/Green Signal and Threshold Justification

The signal uses the **latest available VIX close**, because VIX is forward-looking and suits the question "is there anything we should be watching?".

| Status | Rule | Meaning | Justification |
|---|---|---|---|
| **Green** | VIX < 20 | Calm | VIX averaged 18.93 in 2025 and about 18.10 so far in 2026 (MacroTrends, n.d.); below 20 "generally indicates investor contentment" (Hartford Funds, 2026) |
| **Amber** | 20 ≤ VIX < 30 | Above normal — monitor daily | Expected volatility above its long-run average |
| **Red** | VIX ≥ 30 | Stress — escalate | Above 30 "suggests anxiety" (Hartford Funds, 2026) |
| **Grey** | Latest VIX missing, or more than 3 sessions old (4+) | Data issue — do not rely on the signal | Prevents an out-of-date reading showing a false Green |

All thresholds sit in **one configuration block** at the top of `part3_dashboard.py`, so they can be reviewed against the bank's risk appetite without touching chart code.

### 3.4 Working Proof of Concept

The saved outputs were generated from the actual **Part 2 curated snapshot** (`part2_data_curation/real_outputs/curated_sp500_vix.csv`), not new provider downloads.

| Evidence | Verified result |
|---|---:|
| Display window | Past 90 calendar days: 31 Jul – 28 Oct 2026 (63 trading sessions) |
| Latest S&P 500 close (28 Oct 2026) | 7,743.98 |
| 90-day change (from 30 Jul 2026 close of 7,437.63) | +4.1% |
| 90-day high / low close | 7,818.93 (6 Oct) / 7,489.72 (31 Jul) |
| Latest SMA20 | 7,734.34 (close is above it) |
| VIX range in window | 14.21 (22 Sep) – 19.99 (16 Oct) |
| Latest VIX (27 Oct 2026) | 17.52 |
| **Latest signal** | **Green** |
| Signal history in window | 63 Green, 0 Amber, 0 Red, 0 Grey |
| Latest 20-session S&P 500 / VIX correlation | −0.88 |
| Correlation range in window | −0.96 to −0.27 |
| Divergence sessions shaded yellow | 1 (28 Aug 2026, correlation −0.27) |
| Sessions missing VIX | 1 (28 Oct 2026, left blank) |
| Automated Part 3 tests passed | 19 |

#### What the dashboard shows

- **S&P 500 trend:** up 4.1% over the past 90 days to 7,744. It peaked at 7,819 on 6 October, dipped to about 7,550 in mid-September, and now sits just above its 20-session average.
- **VIX movement:** calm throughout, between 14.2 and 20.0. VIX rose from around 15 in early October to 19.99 on 16 October (0.01 below Amber) and has since eased to 17.52.
- **Correlation / divergence:** shares and VIX mostly moved in opposite directions (−0.88 now). The relationship weakened briefly on 28 August (−0.27), the only yellow day.
- **What the signal means:** Green — markets expect normal-sized moves. The mid-October rise in VIX to just under 20 is the main thing worth watching.

Note: the 29 Jul 2026 Amber reading (VIX 20.66) falls just outside the 90-day window, so it is not shown.

The tests check the Green/Amber/Red boundaries (19.99, 20, 29.99, 30), Grey for missing or stale VIX (3 vs 4 sessions old), the 90-calendar-day window, SMA20 using trading sessions, the 90-day change baseline, the −0.30 shading boundary (−0.31, −0.30, −0.29), one-day shading width, schema failure, loading the real Part 2 file and written outputs. Full results: `outputs/test_results.txt`.

**Run from the group repository root:**

```bash
python -m pip install -r part3_dashboard/requirements.txt
python -m pytest -v part3_dashboard/tests
python part3_dashboard/part3_dashboard.py \
  --curated part2_data_curation/real_outputs/curated_sp500_vix.csv
```

To rebuild the inputs directly from Yahoo Finance and FRED instead (internet required), use `python part3_dashboard/part3_dashboard.py --fetch`.

Alternatively, run `Part3_Dashboard.ipynb` in Google Colab. Files used for the proof of concept:

| File / folder | Purpose |
|---|---|
| `part3_dashboard.py` | Signal rules, correlation, chart building and run log |
| `Part3_Dashboard.ipynb` | Executable notebook demonstration |
| `tests/test_part3_dashboard.py` | Nineteen automated tests |
| `outputs/test_results.txt` | Saved test run (evidence) |
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
| 4 | AI-built first version showed the last 90 **trading sessions** (about four months), not the past 90 **days** the brief asks for | Team peer review against the brief | Window changed to 90 calendar days (SMA20 and correlation still use trading sessions); tests added for the window, SMA20 and 90-day change |
| 5 | Chart 2 could be misread (crossing lines on two scales) and the −0.30 rule had no stated source | Team peer review | Colour-coded axis titles, "compare directions, not crossings" note, zoomed-axis note; rule justified with Cohen (1988) and boundary tests added |

To help analysts present a clear message, the team should use a shared template: **state the question, give the answer first, use one chart per point and label anything unusual**. Before release, a non-technical colleague should be able to repeat the main message in one sentence. Changes to thresholds or AI-assisted code require peer review and rerunning the tests. This is a limited proof of concept, not a production trading or banking decision engine.



