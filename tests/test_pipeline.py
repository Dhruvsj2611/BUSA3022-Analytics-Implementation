import sys, tempfile
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from pipeline import validate,save_raw

def run():
    with tempfile.TemporaryDirectory() as d:
        root=Path(d)
        data=pd.DataFrame({'date':['2026-10-20','2026-10-21','2026-10-21','bad-date'],
                           'open':[100,101,101,102],'high':[102,103,103,104],
                           'low':[99,100,100,101],'close':[101,102,None,103]})
        raw=save_raw(data,'market',root,'test')
        good,bad=validate(data,'market',root,'test')
        assert raw.exists() and len(good)==1 and len(bad)==3
        assert (root/'logs/data_quality_log.csv').exists()
        try:validate(data.drop(columns=['close']),'market',root,'schema')
        except ValueError:pass
        else:raise AssertionError('schema failure undetected')
        assert len(pd.read_csv(root/'logs/data_quality_log.csv'))>=4
        assert len(pd.read_csv(raw))==4
        print('PASS: raw preserved; missing value, duplicate dates, bad date and schema change detected; logs created')
if __name__=='__main__':run()
