import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from curation import build_curated, run_pipeline, validate_csv, _parse_market_date


class CurationTests(unittest.TestCase):
    def test_metric_formulas_manually(self):
        days = pd.bdate_range('2026-01-05', periods=25)
        close = np.array([100.0 * (1.01 ** i) for i in range(25)])
        sp = pd.DataFrame({'market_session_date': days, 'sp500_close': close})
        vx = pd.DataFrame({'market_session_date': days, 'vix_close': np.full(25, 20.0)})
        out = build_curated(sp, vx)
        self.assertTrue(np.isnan(out.iloc[18].sp500_sma20))
        self.assertAlmostEqual(out.iloc[19].sp500_sma20, sum(close[:20]) / 20, places=10)
        self.assertAlmostEqual(out.iloc[1].sp500_daily_return_pct, 1.0, places=10)
        self.assertAlmostEqual(out.iloc[14].sp500_volatility14_annualized_pct, 0.0, places=10)
        self.assertTrue(np.isnan(out.iloc[13].sp500_volatility14_annualized_pct))

    def test_missing_vix_remains_missing(self):
        days = pd.bdate_range('2026-01-05', periods=4)
        sp = pd.DataFrame({'market_session_date': days, 'sp500_close': [1, 2, 3, 4]})
        vx = pd.DataFrame({'market_session_date': days.delete(2), 'vix_close': [10, 11, 13]})
        out = build_curated(sp, vx)
        self.assertTrue(out.iloc[2].vix_gap_flag)
        self.assertTrue(np.isnan(out.iloc[2].vix_close))

    def test_duplicates_and_invalids_quarantined(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'sp.csv'
            pd.DataFrame({'Date': ['2026-10-01', '2026-10-01', 'bad', '2026-10-02'],
                          'Close': ['100', '101', '55', '']}).to_csv(path, index=False)
            accepted, q, events = validate_csv(path, 'SP500')
            self.assertEqual(len(accepted), 1)
            self.assertEqual(len(q), 3)
            self.assertIn('duplicate_market_session_date', q.iloc[0].rejection_reason)
            self.assertIn('invalid_or_missing_date', q.iloc[1].rejection_reason)

    def test_date_labels_not_shifted_by_timezone(self):
        self.assertEqual(_parse_market_date('2026-10-28T00:00:00Z', 'Date'), pd.Timestamp('2026-10-28'))
        self.assertEqual(_parse_market_date('2026-10-29T01:00:00Z', 'timestamp'), pd.Timestamp('2026-10-28'))

    def test_vix_only_dates_logged_and_saved(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            sp = directory / 'market.csv'
            vx = directory / 'vix.csv'
            pd.DataFrame({'date': ['2026-10-27', '2026-10-28'],
                          'close': [100, 101]}).to_csv(sp, index=False)
            pd.DataFrame({'date': ['2026-10-26', '2026-10-27'],
                          'vix': [18.0, 19.0]}).to_csv(vx, index=False)
            output = directory / 'result'
            run_pipeline(sp, vx, output)
            extra = pd.read_csv(output / 'vix_only_dates.csv')
            self.assertEqual(extra['market_session_date'].tolist(), ['2026-10-26'])
            log = pd.read_csv(output / 'quality_log.csv')
            row = log.loc[log['event'] == 'vix_dates_without_sp500_session'].iloc[0]
            self.assertEqual(int(row['affected_rows']), 1)

    def test_failure_writes_log(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            bad = directory/'bad.csv'
            pd.DataFrame({'Other': ['2026-10-28'], 'wrong': ['10']}).to_csv(bad,index=False)
            vix = directory/'vix.csv'
            pd.DataFrame({'DATE':['2026-10-28'],'VIXCLS':[20]}).to_csv(vix,index=False)
            with self.assertRaises(ValueError):
                run_pipeline(bad,vix,directory/'output')
            log = pd.read_csv(directory/'output'/'quality_log.csv')
            self.assertIn('pipeline_failure', set(log.event))
            self.assertEqual(log.iloc[-1].status,'FAIL')


if __name__ == '__main__':
    unittest.main()
