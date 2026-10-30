# BUSA3022 — Member 2 Data Curation Handover

## 1. Project overview

This project develops a market-intelligence analytics system for the
fictional Really Big Bank.

Member 1 has developed a Python data-ingestion and validation
proof of concept.

Member 2 is responsible for data curation, date alignment,
metric calculations and associated validation.

## 2. Confirmed data sources

Market:
- Provider: Yahoo Finance
- Index: S&P 500
- Ticker: ^GSPC
- Frequency: Daily market observations

Macro:
- Provider: FRED
- Series: VIXCLS
- Description: CBOE Volatility Index
- Frequency: Daily observations

## 3. Files to use

Validated market dataset:
data/validated/market_validated.csv

Validated macro dataset:
data/validated/macro_validated.csv

Original data:
data/raw/market/
data/raw/macro/

Data-quality log:
logs/data_quality_log.csv

Source-verification evidence:
docs/source_verification.csv

Pipeline architecture:
diagrams/pipeline_architecture.png

## 4. Data structure

Market columns:
date, adj_close, close, high, low, open, volume

Macro columns:
date, vix

Dates use the YYYY-MM-DD format.

Market prices represent index points.
VIX values represent the volatility-index level.

## 5. Verified proof-of-concept results

Execution date: 29 October 2026

Market:
- 124 records retrieved and accepted
- Observation dates: 4 May–28 October 2026

Macro:
- 127 records retrieved and accepted
- Observation dates: 4 May–27 October 2026

The initial live validation quarantined zero records.

Repeat-download consistency verification:
- S&P 500: 124/124 closing values matched
- VIX: 127/127 values matched

## 6. Important requirements for Member 2

1. Preserve the original raw datasets.
2. Use the validated files as inputs.
3. Explicitly align the market and macro observation dates.
4. Do not assume missing dates are errors without checking calendars.
5. Do not invent values for market holidays or unavailable observations.
6. Define all calculated metrics in plain language before coding.
7. Implement two or three calculated metrics.
8. Document every transformation and data-quality decision.
9. Preserve the data dictionary and agreed column names.
10. Produce datasets that Member 3 can use for the dashboard.

## 7. Recommended metric direction

Potential metrics include:
- Daily percentage return
- Rolling average of S&P 500 closing prices
- Rolling or percentage change indicators

The final two or three metrics should be agreed with Member 3
and clearly justified against the business question.

## 8. Important limitations

The pipeline currently runs manually in Google Colab.

Automated daily scheduling is proposed but has not yet been deployed.

The S&P 500 dataset ends on 28 October 2026.
The VIX dataset ends on 27 October 2026.

The one-day difference should be investigated during date alignment.

The demonstrated failure tests used deliberately created sample errors,
not actual defects identified in the live datasets.

## 9. Member 2 deliverables

Member 2 should create:
- Data-curation methodology
- Metric definitions
- Cleaned and aligned dataset
- Two or three calculated metrics
- Data-quality issue and documented handling
- Working metric proof of concept
- Supporting evidence for the report and GitHub portfolio
- Handover documentation for Member 3


## 10. Completed Part 2 contribution (30 October 2026 repository package)

Part 2 now lives at `part2_data_curation/` and can be reproduced from the validated input snapshots listed above. The implementation produces:

- `real_outputs/curated_sp500_vix.csv`: 124 dated S&P 500 records and three metrics, joined by US market session to VIX.
- `real_outputs/vix_only_dates.csv`: four valid FRED VIX dates without an S&P 500 session, preserved separately.
- `real_outputs/quarantined_records.csv` and `quality_log.csv`: rejected rows and recorded quality outcomes. The saved group inputs produced zero new quarantined rows.
- `tests/test_curation.py`: six automated tests including hand-checkable metric logic, timestamp/date policy, missing values and schema failures.

The 28 October 2026 market session has no matching VIX record in the saved 29 October source snapshot. This is flagged, not forward-filled. **These counts must be rechecked after any upstream refresh.**

Member 3 should use `part2_data_curation/real_outputs/curated_sp500_vix.csv` and review `part2_data_curation/README.md` for metric definitions and data contracts.
