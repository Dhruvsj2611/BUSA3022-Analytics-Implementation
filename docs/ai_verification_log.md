# BUSA3022 — AI Verification Log

## AI-assisted development

ChatGPT was used to assist with the initial Python pipeline,
validation logic, verification scripts and technical documentation.

All material used in the project must be reviewed and verified
before inclusion in the submission.

## Genuine AI-assisted coding issue

Task:
Compare saved S&P 500 closing prices with a fresh Yahoo Finance download.

Initial problem:
The comparison code attempted to merge the two datasets using
their date columns without first converting both columns
to a consistent data type.

Observed Python error:
ValueError: You are trying to merge on object and datetime64[ns]
columns for key 'date'.

How the problem was detected:
Google Colab displayed a traceback identifying incompatible
date-column types in the pandas merge operation.

Correction:
Both saved and freshly downloaded date columns were converted
using pd.to_datetime(), followed by date normalisation.

Verification:
The corrected comparison ran successfully.

Results:
- 124 records compared.
- 124 closing values matched within a 0.01 tolerance.
- Zero different values.
- Zero dates missing.

Important limitation:
The coding error occurred in the verification script,
not in the original data-ingestion pipeline.

## AI-generated code guardrails

Before accepting AI-assisted code:
1. Inspect the generated logic.
2. Confirm expected column names and data types.
3. Run controlled validation tests.
4. Investigate exceptions rather than suppressing them.
5. Compare outputs against source data.
6. Preserve logs of corrections and verification results.
7. Require human review before updating shared outputs.

## Leadership implications

A junior analyst receiving this pipeline should be supplied
with the README, architecture, data contract, tests,
quality logs and known limitations.

AI-generated suggestions should be treated as proposed
solutions requiring human verification, not authoritative
instructions.

## Evidence

- Notebook: notebooks/01_data_pipeline.ipynb
- Source verification: docs/source_verification.csv
- Failure tests: tests/test_pipeline.py
- Pipeline design: docs/pipeline_design.md
