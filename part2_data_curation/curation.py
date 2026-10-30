"""BUSA3022 Part 2: reproducible S&P 500 / VIX data curation proof of concept.

Uses raw or Part 1 validated CSVs. Does not fetch live market data.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import json
import math
import re

import numpy as np
import pandas as pd

DATE_NAMES = ('session_date', 'market_session_date', 'date', 'observation_date', 'datetime', 'timestamp', 'time')
SP_NAMES = ('sp500_close', 'close', 'adj close', 'adj_close', '^gspc', 'gspc', 'price')
VIX_NAMES = ('vix', 'vixcls', 'vix_close', 'value', 'close', 'price')


def _normalized(s):
    return re.sub(r'[^a-z0-9]+', '_', str(s).strip().lower()).strip('_')


def _choose(df: pd.DataFrame, wanted: tuple[str, ...], *, kind: str):
    fields = {_normalized(c): c for c in df.columns}
    for possible in wanted:
        if _normalized(possible) in fields:
            return fields[_normalized(possible)]
    if kind == 'date' and len(df.columns) and str(df.columns[0]).lower().startswith('unnamed'):
        return df.columns[0]
    raise ValueError(f'Could not find {kind} column. Columns found: {list(df.columns)}. '
                     f'Expected one of: {list(wanted)}')


def _parse_market_date(value, date_field: str):
    """Date-only provider observations are session labels, never UTC instants.

    Timestamp columns, unlike Date columns, represent actual instants and are
    converted to America/New_York before deriving session date. A naive
    timestamp is assumed to be New York local time (documented assumption).
    """
    if pd.isna(value) or str(value).strip() == '':
        return pd.NaT
    field = _normalized(date_field)
    try:
        if field in ('timestamp', 'time', 'datetime'):
            instant = pd.Timestamp(value)
            if instant.tzinfo is None:
                instant = instant.tz_localize('America/New_York', ambiguous='raise', nonexistent='raise')
            else:
                instant = instant.tz_convert('America/New_York')
            return pd.Timestamp(instant.date())
        # Source's published date is a US market-session label, even when a
        # CSV writer serialized it with a midnight timestamp suffix.
        value_str = str(value).strip()
        match = re.match(r'^\d{4}-\d{2}-\d{2}', value_str)
        label = match.group(0) if match else value_str
        return pd.Timestamp(pd.to_datetime(label, errors='raise').date())
    except (ValueError, TypeError, OverflowError):
        return pd.NaT


def validate_csv(input_csv: str | Path, source: str):
    """Return (accepted, quarantined, log_rows); never silently drop bad rows."""
    source = source.upper()
    if source not in {'SP500', 'VIX'}:
        raise ValueError('source must be SP500 or VIX')
    df = pd.read_csv(input_csv, dtype=str, keep_default_na=False)
    if df.empty:
        raise ValueError(f'{source}: input file empty')
    try:
        date_field = _choose(df, DATE_NAMES, kind='date')
        value_field = _choose(df, SP_NAMES if source == 'SP500' else VIX_NAMES, kind='value')
    except ValueError as exc:
        # Schema error is fatal. File remains on disk; operational log still written by run_pipeline.
        raise ValueError(f'{source} SCHEMA_FAILURE: {exc}') from exc

    stage = pd.DataFrame({
        'source': source,
        'source_row': np.arange(2, len(df) + 2),
        'raw_date': df[date_field].astype(str),
        'raw_value': df[value_field].astype(str),
    })
    stage['market_session_date'] = stage['raw_date'].map(lambda x: _parse_market_date(x, str(date_field)))
    stage['value'] = pd.to_numeric(stage['raw_value'].replace('', np.nan), errors='coerce')
    reasons = [[] for _ in range(len(stage))]
    for i, (d, v) in enumerate(zip(stage['market_session_date'], stage['value'])):
        if pd.isna(d):
            reasons[i].append('invalid_or_missing_date')
        if pd.isna(v) or not np.isfinite(v) or v <= 0:
            reasons[i].append('missing_non_numeric_or_nonpositive_value')

    # Reject repeated dates, including if their value matches. First recorded row wins.
    dupe = stage['market_session_date'].notna() & stage['market_session_date'].duplicated(keep='first')
    for i in np.where(dupe)[0]:
        reasons[int(i)].append('duplicate_market_session_date')
    stage['rejection_reason'] = [';'.join(row) for row in reasons]
    quarantine = stage.loc[stage['rejection_reason'] != ''].copy()
    valid = stage.loc[stage['rejection_reason'] == '', ['market_session_date', 'value']].copy()
    valid = valid.sort_values('market_session_date').reset_index(drop=True)
    valid = valid.rename(columns={'value': 'sp500_close' if source == 'SP500' else 'vix_close'})
    events = [
        {'source': source, 'event': 'rows_received', 'affected_rows': len(stage), 'status': 'INFO'},
        {'source': source, 'event': 'rows_accepted', 'affected_rows': len(valid), 'status': 'PASS'},
        {'source': source, 'event': 'rows_quarantined', 'affected_rows': len(quarantine), 'status': 'WARN' if len(quarantine) else 'PASS'},
    ]
    for reason in ('invalid_or_missing_date', 'missing_non_numeric_or_nonpositive_value', 'duplicate_market_session_date'):
        count = int(stage['rejection_reason'].str.contains(reason, regex=False).sum())
        events.append({'source': source, 'event': reason, 'affected_rows': count, 'status': 'WARN' if count else 'PASS'})
    return valid, quarantine, events


def build_curated(sp500: pd.DataFrame, vix: pd.DataFrame) -> pd.DataFrame:
    """Join on US equity-market session dates; no backward/forward VIX filling."""
    out = sp500.merge(vix, on='market_session_date', how='left', validate='one_to_one').sort_values('market_session_date')
    out['sp500_daily_return_pct'] = out['sp500_close'].pct_change(fill_method=None) * 100
    out['sp500_sma20'] = out['sp500_close'].rolling(20, min_periods=20).mean()
    out['sp500_volatility14_annualized_pct'] = (out['sp500_daily_return_pct'] / 100).rolling(14, min_periods=14).std(ddof=1) * np.sqrt(252) * 100
    out['vix_gap_flag'] = out['vix_close'].isna()
    # Do not interpolate unavailable observations: avoids using unknown/future VIX data.
    assert (out.loc[out['vix_gap_flag'], 'vix_close'].isna()).all()
    return out.reset_index(drop=True)


def run_pipeline(sp500_path: str | Path, vix_path: str | Path, output_dir: str | Path):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    events, quarantines = [], []
    try:
        sp, spq, spe = validate_csv(sp500_path, 'SP500')
        events.extend(spe)
        quarantines.append(spq)
        vx, vxq, vxe = validate_csv(vix_path, 'VIX')
        events.extend(vxe)
        quarantines.append(vxq)
        curated = build_curated(sp, vx)
        gap_count = int(curated['vix_gap_flag'].sum())
        # VIX-only dates are valid FRED observations without an S&P 500 session.
        # Audit them explicitly instead of silently excluding them from the curated table.
        vix_only = vx.loc[~vx['market_session_date'].isin(sp['market_session_date'])].copy()
        vix_only.to_csv(out / 'vix_only_dates.csv', index=False, date_format='%Y-%m-%d')
        events.append({'source': 'JOIN', 'event': 'unmatched_vix_session_dates', 'affected_rows': gap_count, 'status': 'WARN' if gap_count else 'PASS'})
        events.append({'source': 'JOIN', 'event': 'vix_dates_without_sp500_session', 'affected_rows': len(vix_only), 'status': 'INFO'})
        events.append({'source': 'METRICS', 'event': 'sma20_warmup_or_missing', 'affected_rows': int(curated['sp500_sma20'].isna().sum()), 'status': 'INFO'})
        events.append({'source': 'METRICS', 'event': 'volatility14_warmup_or_missing', 'affected_rows': int(curated['sp500_volatility14_annualized_pct'].isna().sum()), 'status': 'INFO'})
        curated.to_csv(out / 'curated_sp500_vix.csv', index=False, date_format='%Y-%m-%d', float_format='%.8f')
        pd.concat(quarantines, ignore_index=True).to_csv(out / 'quarantined_records.csv', index=False, date_format='%Y-%m-%d')
        return curated
    except Exception as exc:
        events.append({'source': 'PIPELINE', 'event': 'pipeline_failure', 'affected_rows': 0, 'status': 'FAIL', 'details': str(exc)})
        raise
    finally:
        now = datetime.now(timezone.utc).isoformat()
        with (out / 'quality_log.csv').open('w', encoding='utf-8') as f:
            pd.DataFrame([{**{'run_id': run_id, 'logged_at_utc': now}, **e} for e in events],
                         columns=['run_id', 'logged_at_utc', 'source', 'event', 'affected_rows', 'status', 'details']).to_csv(f, index=False)


def main():
    p = argparse.ArgumentParser(description='BUSA3022 Part 2 market + VIX curation proof of concept')
    p.add_argument('--sp500', required=True, help='Path to S&P500 raw/validated CSV from Part 1')
    p.add_argument('--vix', required=True, help='Path to VIX raw/validated CSV from Part 1')
    p.add_argument('--out', default='demo_outputs', help='Output folder for curated data and audit logs')
    args = p.parse_args()
    curated = run_pipeline(args.sp500, args.vix, args.out)
    print(f'Produced {len(curated)} dated S&P 500 sessions. VIX missing on {int(curated.vix_gap_flag.sum())} sessions.')
    print(f'Output saved in {args.out}')
    print(curated.tail(3).to_string(index=False))


if __name__ == '__main__':
    main()
