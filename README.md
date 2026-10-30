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

Part 2 builds on the validated S&P 500 and VIX datasets from Part 1 to support market trend analysis and future benchmarking.

### 2.1 Calculated Metrics and Business Relevance

Three metrics are used:

- **20-Session Moving Average:** The average S&P 500 closing price across the latest 20 trading sessions, used to identify underlying market trends.
- **Daily Return (%):** The percentage change in the S&P 500 closing price from the previous trading session, used to assess market direction and daily performance.
- **14-Return Annualised Volatility (%):** The variability of the latest 14 daily returns, annualised to assess changes in market risk.

### 2.2 Data Alignment and Time Zone Handling

S&P 500 and VIX observations are aligned using their US market-session dates. Source dates are standardised before joining, while UTC timestamps are retained for processing and audit logs. The S&P 500 trading calendar defines the final dataset.

### 2.3 Data Quality Issue and Resolution

The validated datasets contain 124 S&P 500 observations and 127 VIX observations, with 123 matching dates. The VIX observation for 28 October 2026 is unavailable. This missing value is flagged rather than silently replaced, while four VIX-only dates are retained in a separate audit file.

### 2.4 Working Proof of Concept

The Python implementation calculates the proposed metrics, aligns the source datasets, and records data-quality outcomes. Six automated tests passed, supporting the correctness of the implemented calculation and validation logic.

The implementation, notebook, tests, and saved outputs are available in [Part 2 Data Curation](part2_data_curation/README.md).

### 2.5 AI Agent Lens

Metric requirements are specified in plain language before AI-assisted transformation logic is developed. These definitions establish the calculation windows, expected outputs, and handling of insufficient observations, providing clear criteria for checking the generated code.

