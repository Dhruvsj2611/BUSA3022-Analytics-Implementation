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

Part 2 of the Really Big Bank market-intelligence proof of concept is implemented in [`part2_data_curation/`](part2_data_curation/README.md). It transforms the **validated** S&P 500 (`^GSPC`) and CBOE VIX (`VIXCLS`) observations from Part 1 without changing the source files. The aim is to support the business question: **How has market activity trended over the past 90 days, and is there anything we should be watching?**

### 2.1 Calculated Metrics and Business Relevance

The three metric requirements were defined in plain language before serving as acceptance criteria for AI-assisted transformation logic.

| Metric | Definition | Business relevance | Calculation rule |
|---|---|---|---|
| **20-session moving average (SMA20)** | Average the S&P 500 close for the current session and previous 19 trading sessions. Leave the first 19 observations blank. | Shows the underlying direction of market prices for trend benchmarking. | Mean of 20 closing prices (`min_periods=20`). |
| **Daily return (%)** | Express the change from the previous session's close as a percentage. Leave the first session blank. | Highlights the direction and magnitude of each market move. | `(close / previous_close − 1) × 100`. |
| **14-return annualised volatility (%)** | Measure the variation in the latest 14 daily returns and express it on an annualised basis. Leave results blank until 14 returns exist. | Indicates whether price movements are relatively stable or unsettled. | Sample SD of 14 decimal daily returns × `sqrt(252) × 100`. |

These metrics use **S&P 500 trading sessions, not calendar days**. The fixed windows and 252-session annualisation convention are modelling assumptions. Historical realised volatility is distinct from VIX, which reflects expected near-term volatility.

### 2.2 Data Alignment and Time Zone Handling

The S&P 500 defines the trading-session calendar. The script uses a **left join on the published US market-session date**, retaining every S&P 500 session and attaching VIX only if that date is present. Date-only provider values are session labels, not UTC instants. Actual timestamp values are converted to `America/New_York` before the session date is extracted; timestamps lacking a time zone are assumed to be New York local time. This avoids false date shifts when code runs in Australia and does not assume that both sources publish data on identical dates.

### 2.3 Data Quality Issue and Resolution

In the saved 29 October 2026 inputs, **28 October 2026** has an S&P 500 close but no same-day VIX observation. Rather than forward-filling an outdated volatility measure, the curated table keeps `vix_close` blank and sets `vix_gap_flag = True`. Four VIX-only dates are written to `part2_data_curation/real_outputs/vix_only_dates.csv` so they are not silently lost.

Validation also checks required columns, valid observation dates, positive numeric values and duplicate session dates. Invalid rows are quarantined with their rejection reasons; source/run outcomes appear in a structured, UTC-stamped `quality_log.csv`. A missing required column triggers a logged failure rather than an apparently valid output.

### 2.4 Working Proof of Concept

The saved outputs were generated using the actual **Part 1 validated CSV snapshot**, not new provider downloads.

| Evidence | Verified result |
|---|---:|
| S&P 500 sessions | 124 |
| Available VIX observations | 127 |
| Matching same-day observations | 123 |
| S&P 500 sessions missing VIX | 1 |
| VIX-only observation dates | 4 |
| Additional rows quarantined from the validated inputs | 0 |
| Automated Part 2 tests passed | 6 |

**Checked calculation (28 October 2026):** closing price 7,743.9800, preceding close 7,722.6001, daily return **+0.2768%**, SMA20 **7,734.3391**, and annualised 14-return volatility **10.8835%**. The tests also validate duplicate-row quarantine, VIX gaps, date conventions, VIX-only audit records and logged failures.

**Run from the group repository root:**

```bash
python -m pip install -r part2_data_curation/requirements.txt
python -m unittest discover -s part2_data_curation/tests -v
python part2_data_curation/curation.py \
  --sp500 data/validated/market_validated.csv \
  --vix data/validated/macro_validated.csv \
  --out part2_data_curation/real_outputs
```

Alternatively, run [`part2_data_curation/Part2_Data_Curation_Colab.ipynb`](part2_data_curation/Part2_Data_Curation_Colab.ipynb) in Google Colab. Files used for the proof of concept:

| File / folder | Purpose |
|---|---|
| [`part2_data_curation/curation.py`](part2_data_curation/curation.py) | Validation, data alignment and metric calculations |
| [`part2_data_curation/Part2_Data_Curation_Colab.ipynb`](part2_data_curation/Part2_Data_Curation_Colab.ipynb) | Executable notebook demonstration |
| [`part2_data_curation/tests/test_curation.py`](part2_data_curation/tests/test_curation.py) | Six automated tests |
| `part2_data_curation/real_outputs/` | Curated real-snapshot data, quality log, quarantine and unmatched-date audit |
| `part2_data_curation/sample_data/` and `part2_data_curation/demo_outputs/` | Separate synthetic failure-test examples and their outputs |
| [`part2_data_curation/requirements.txt`](part2_data_curation/requirements.txt) | Part 2-specific Python dependencies |

### 2.5 AI Agent Lens

The **plain-language definitions in Section 2.1** state what the calculation should mean, how many trading sessions it needs, and what should happen when data is insufficient. Those definitions act as requirements for AI-assisted transformation code, which must be reviewed rather than accepted merely because it executes. Checks include independently worked numeric examples and six passing automated tests.

The team should retain a common data dictionary with field names, units, session-date rules, formulas and warm-up behaviour. Changes to definitions or AI-assisted code require peer review and rerunning the checks before the curated file is used downstream. This is a limited proof of concept, not a production trading or banking decision engine.

# Really Big Bank — BUSA3022 Analytics Implementation Plan & Portfolio

## 3. Dashboard and Reporting Plan

This folder contains Part 3 of the Really Big Bank market-intelligence proof of concept. It turns the **curated** S&P 500 (`^GSPC`) and CBOE VIX (`VIXCLS`) dataset from Part 2 into a single dashboard view, without changing the Part 2 files. The dashboard answers the business question: **How has market activity trended over the past 90 days, and is there anything we should be watching?**

<img width="2440" height="1936" alt="dashboard_screenshot" src="https://github.com/user-attachments/assets/e176aef3-ba9c-4f9c-b76e-3981bb73e541" />

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
