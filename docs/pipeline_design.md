# Pipeline design decisions (v1)

- **Business question:** how has market activity trended over 90 days?
- **Market source:** Yahoo Finance, `^GSPC`, daily OHLC prices. Volume is optional and not relied on for the core design.
- **Macro source:** FRED, `VIXCLS`, daily VIX closing observation. VIX is forward-looking implied volatility, not realised index volatility.
- **Ingestion window:** 180 calendar days to support initial rolling calculations and the display window.
- **Schedule proposal:** GitHub Actions daily, after US market close with a publication lag; use manual Colab execution as a demonstrator. Scheduling has not yet been deployed.
- **Stages:** provider fetch → immutable timestamped raw CSV → schema and row checks → validated CSV + quarantined rows and CSV quality log → Member 2 transformations.
- **Quality rules:** required fields, parseable date, positive OHLC, numeric values, duplicate observation dates. Source availability, trading holidays and source-delay are assessed separately; do not manufacture missing trading-day observations.
- **Failure policy:** network/API failure is logged; never replace current data with invented or silently stale observations. Failed schema validation logs an error and prevents validated output for that source/run.
- **Current limitation:** validated files are latest-run snapshots; production implementation should use atomic writes, immutable raw storage, retry/backoff, secrets management, completeness/freshness checks and idempotent scheduled releases.
- **Time axis:** Yahoo index values refer to US market sessions. FRED VIX dates are observation dates, not Sydney dates. Member 2 explicitly joins US observation dates with an outer join and tracks gaps; do not shift dates based on execution timezone.
- **Data provenance:** source, series IDs, retrieval timestamps in raw filename and logs; use provenance manifests in production.
- **Downstream commitment:** file schema and units can only change via shared versioned contract.


## Proof-of-concept execution evidence — 29 October 2026

### Live ingestion results
- Yahoo Finance S&P 500 (^GSPC): 124 rows retrieved, 124 accepted, 0 quarantined.
- FRED VIX (VIXCLS): 127 rows retrieved, 127 accepted, 0 quarantined.
- Total: 251 accepted observations.
- Historical period: 4 May 2026 onwards.
- Latest S&P 500 observation: 28 October 2026.
- Latest VIX observation: 27 October 2026.

### Data-quality logging
The live execution generated four log events:
- Market raw capture.
- Market validation completion.
- Macro raw capture.
- Macro validation completion.

Logs contain UTC timestamps, a run identifier, source,
event type, affected row count and descriptive details.

### Controlled failure testing
Synthetic test records were used to confirm detection of:
- Missing values.
- Duplicate observation dates.
- Invalid dates.
- Schema changes.

The tests also confirmed raw-data preservation and log creation.
These deliberately introduced errors are not claimed to have
occurred in the downloaded financial datasets.

### Source-verification evidence
Saved data was compared with fresh downloads from the same providers.

- S&P 500: 124 of 124 closing values matched within 0.01.
- VIX: 127 of 127 observations matched within 0.0001.
- No comparison dates were missing.
- Evidence file: docs/source_verification.csv.

These are repeat-download consistency checks, not independent
verification against a second financial-data provider.

### Known limitations
- Automated scheduling is proposed but has not been deployed.
- Missing values in future source updates may require investigation.
- Source publication lag explains why data freshness must be
  assessed against the source's expected reporting schedule.
- Current validated datasets are latest-run CSV snapshots.
- A production system would require stronger access control,
  retry handling, monitoring, atomic writes and operational ownership.
