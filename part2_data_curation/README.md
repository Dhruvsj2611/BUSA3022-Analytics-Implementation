# Really Big Bank — BUSA3022 Analytics Implementation Plan & Portfolio

## 2. Data Curation Plan

# Part 2: Data Curation Plan

This section documents the transformation of validated S&P 500 (^GSPC) and CBOE VIX (VIXCLS) observations from Part 1 into a curated dataset for Really Big Bank's 90-day market-monitoring dashboard.

The implementation uses Python and pandas to align both sources, calculate three market indicators, validate results, and retain data-quality evidence. Original datasets are preserved separately to maintain traceability.

## 1. Calculated Metrics

Three metrics were defined in plain language before AI-assisted transformation code was developed.

### 1.1 20-Session Simple Moving Average (SMA20)

The average S&P 500 closing price over the current and previous 19 trading sessions.

**Formula:**

`SMA20(t) = [P(t) + P(t-1) + ... + P(t-19)] / 20`

**Business purpose:** Smooths short-term price fluctuations to identify underlying market trends.

**Missing-value rule:** The first 19 observations remain blank because 20 closing prices are required.

### 1.2 Daily Percentage Return

The percentage change in the S&P 500 closing price compared with the previous trading session.

**Formula:**

`R(t) = [P(t) / P(t-1) - 1] × 100`

**Business purpose:** Measures daily market performance and supports future comparisons with bank performance.

**Missing-value rule:** The first observation remains blank because no previous closing price is available.

### 1.3 14-Return Annualised Volatility

The sample standard deviation of the latest 14 daily returns expressed as decimals, annualised using 252 assumed trading sessions.

**Formula:**

`Vol14(t) = sample_SD[r(t-13), ..., r(t)] × sqrt(252) × 100`

The implementation uses sample standard deviation (`ddof=1`).

**Business purpose:** Measures observed market variability and supports comparison with VIX, which represents expected near-term volatility.

**Missing-value rule:** The first 14 observations remain blank because 14 daily returns are required.

## 2. Date Alignment and Integration

The S&P 500 trading calendar defines the common reporting axis. A same-day left join preserves all market-index observations and matches VIX observations using their US market-session dates.

### Verified Reconciliation

| Alignment outcome | Records |
|---|---:|
| S&P 500 source observations | 124 |
| VIX source observations | 127 |
| Matching dates | 123 |
| S&P 500 dates without VIX | 1 |
| VIX-only dates | 4 |
| Final curated market observations | 124 |

The unmatched VIX value remains blank and flagged. The four VIX-only observations are retained in a separate audit file and are not added to the curated S&P 500 dataset.

Both sources use US market observation dates under the `America/New_York` convention. Date-only values are treated as market-session labels, not UTC timestamps. Future timestamped inputs would require daylight-saving-aware conversion.

The current retrospective implementation does not establish exact source-publication times.

## 3. Data Quality and Missing Values

During the group's initial extraction on 29 October 2026, S&P 500 observations extended to 28 October 2026, whereas retrieved VIX observations extended to 27 October 2026.

The unmatched VIX observation remains missing rather than being filled with zero or an older value.

The implementation distinguishes:

- **Calculation warm-up periods:** Expected blank values caused by insufficient historical observations.
- **Source-data quality issues:** Invalid values, duplicate dates, missing required fields, or unmatched source observations requiring investigation.

Quality outcomes are retained through structured logs, quarantined-record outputs, and VIX-only-date audit records.

## 4. Proof of Concept and Verification

The Python implementation processes the validated Part 1 datasets and produces 124 curated market observations.

### Verified Calculation Example

**Reporting date:** 28 October 2026

| Metric | Result |
|---|---:|
| S&P 500 closing price | 7,743.9800 |
| Daily percentage return | +0.2768% |
| SMA20 | 7,734.3391 |
| 14-return annualised volatility | 10.8835% |
| VIX observation | Missing |

The calculations were checked against source closing prices.

### Automated Verification

Six automated tests passed, covering:

1. Date handling and alignment.
2. Invalid-record quarantine.
3. Failure and quality logging.
4. Metric calculation accuracy.
5. Missing VIX treatment.
6. Preservation of VIX-only audit records.

These tests provide evidence that the implemented transformation behaves as intended under the tested conditions.

## 5. Repository Files

All files are located in the `part2_data_curation/` directory.

| File | Purpose |
|---|---|
| `curation.py` | Working Python transformation script |
| `Part2_Data_Curation_Colab.ipynb` | Google Colab implementation |
| `tests/test_curation.py` | Six automated tests |
| `real_outputs/curated_sp500_vix.csv` | Final curated dataset |
| `real_outputs/quality_log.csv` | Structured data-quality log |
| `real_outputs/quarantined_records.csv` | Rejected-record audit |
| `real_outputs/vix_only_dates.csv` | Four unmatched VIX dates |

These files support reproducibility and technical review.

## 6. AI Agent Lens and Leadership

Metric requirements were defined before AI-assisted coding, including required inputs, calculation windows, units, business purposes, and missing-value rules.

AI-generated transformation logic was reviewed through numerical spot checks and six automated tests rather than accepted solely because it executed successfully.

For future maintenance, the team should maintain consistent field names, metric definitions, date conventions, and missing-data rules in a shared data dictionary.

All code modifications, including AI-assisted revisions, should undergo human review and automated testing before being used in dashboard reporting.
