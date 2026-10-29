# Really Big Bank — BUSA3022 Part 1 Pipeline

This package is a **proof-of-concept starter**, not a production deployment. It is based on the revised Analytics Lead Case Study.

## Local setup
```bash
python -m pip install -r requirements.txt
python tests/test_pipeline.py
python src/pipeline.py
```
Requires an internet connection for the final command. Or open `notebooks/01_data_pipeline.ipynb` in Google Colab after uploading or cloning the full repository; set working directory to repository root.

## Outputs
Raw timestamped market/macro snapshots in `data/raw/`, last validated CSVs in `data/validated/`, rejected rows in `data/quarantine/`, and structured issue entries in `logs/`. Never silently delete or fill invalid rows.

## Status
- Local synthetic validation and schema tests: **passed**.
- Live Yahoo/FRED downloads: **not yet executed/verified** (requires internet-enabled runtime).
- GitHub Actions schedule: **design only**, not configured or verified.
- Academic report and actual production evidence: **not completed**.

See `docs/pipeline_design.md` and `docs/handover_member2.md`. Document actual AI mistakes and corrections if any occur; do not fabricate an AI error.
