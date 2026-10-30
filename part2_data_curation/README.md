# Really Big Bank — BUSA3022 Analytics Implementation Plan & Portfolio

## 2. Data Curation Plan

This folder contains Part 2 of the Really Big Bank market-intelligence proof of concept. It transforms the **validated** S&P 500 (`^GSPC`) and CBOE VIX (`VIXCLS`) observations from Part 1 without changing the source files. The aim is to support the business question: **How has market activity trended over the past 90 days, and is there anything we should be watching?**

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

In the saved 29 October 2026 inputs, **28 October 2026** has an S&P 500 close but no same-day VIX observation. Rather than forward-filling an outdated volatility measure, the curated table keeps `vix_close` blank and sets `vix_gap_flag = True`. Four VIX-only dates are written to `real_outputs/vix_only_dates.csv` so they are not silently lost.

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

Alternatively, run `Part2_Data_Curation_Colab.ipynb` in Google Colab. Files used for the proof of concept:

| File / folder | Purpose |
|---|---|
| `curation.py` | Validation, data alignment and metric calculations |
| `Part2_Data_Curation_Colab.ipynb` | Executable notebook demonstration |
| `tests/test_curation.py` | Six automated tests |
| `real_outputs/` | Curated real-snapshot data, quality log, quarantine and unmatched-date audit |
| `sample_data/` and `demo_outputs/` | Separate synthetic failure-test examples and their outputs |
| `requirements.txt` | Part 2-specific Python dependencies |

### 2.5 AI Agent Lens

The **plain-language definitions in Section 2.1** state what the calculation should mean, how many trading sessions it needs, and what should happen when data is insufficient. Those definitions act as requirements for AI-assisted transformation code, which must be reviewed rather than accepted merely because it executes. Checks include independently worked numeric examples and six passing automated tests.

The team should retain a common data dictionary with field names, units, session-date rules, formulas and warm-up behaviour. Changes to definitions or AI-assisted code require peer review and rerunning the checks before the curated file is used downstream. This is a limited proof of concept, not a production trading or banking decision engine.
