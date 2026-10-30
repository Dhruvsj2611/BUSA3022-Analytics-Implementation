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
