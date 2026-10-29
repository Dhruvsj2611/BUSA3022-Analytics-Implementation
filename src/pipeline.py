"""BUSA3022 Part 1: demonstrator ingestion, preservation and validation.
Live fetch requires internet and installs specified in requirements.txt.
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import csv
import io
import json
import uuid
import pandas as pd
import requests

MARKET_REQUIRED = ['date','open','high','low','close']
MACRO_REQUIRED = ['date','vix']

def quality_log(root, source, issue, count=0, detail='', run_id='manual'):
    path=Path(root)/'logs'/'data_quality_log.csv'; path.parent.mkdir(parents=True,exist_ok=True)
    record={'event_utc':datetime.now(timezone.utc).isoformat(),'run_id':run_id,'source':source,'issue':issue,'affected_rows':int(count),'detail':str(detail)}
    with path.open('a',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(record));
        if f.tell()==0:w.writeheader()
        w.writerow(record)
    return record

def validate(df, kind, root, run_id='manual'):
    """Validate only. No dates are merged and no records silently deleted.
    A validated subset is exported; quarantined rows preserved separately.
    """
    required= MARKET_REQUIRED if kind=='market' else MACRO_REQUIRED
    df=df.copy()
    missing=[c for c in required if c not in df.columns]
    if missing:
        quality_log(root,kind,'SCHEMA_MISMATCH',len(df),'missing columns: '+','.join(missing),run_id)
        raise ValueError('Missing required columns: '+str(missing))
    errors=pd.Series('',index=df.index,dtype='object')
    dt=pd.to_datetime(df['date'],errors='coerce')
    errors=errors.mask(dt.isna(),errors+'INVALID_DATE;')
    for col in required[1:]:
        nums=pd.to_numeric(df[col],errors='coerce')
        errors=errors.mask(nums.isna(),errors+'MISSING_OR_NONNUMERIC_'+col.upper()+';')
        if col in ['open','high','low','close']:
            errors=errors.mask(nums.le(0)&nums.notna(),errors+'NONPOSITIVE_'+col.upper()+';')
    duplicate=dt.notna() & dt.duplicated(keep=False)
    errors=errors.mask(duplicate,errors+'DUPLICATE_DATE;')
    good=df.loc[errors.eq('')].copy()
    bad=df.loc[errors.ne('')].copy()
    if len(bad):
        bad['validation_issue']=errors[errors.ne('')].values
        qpath=Path(root)/'data'/'quarantine'/f'{kind}_{run_id}.csv';qpath.parent.mkdir(parents=True,exist_ok=True)
        bad.to_csv(qpath,index=False)
        for issue in ['INVALID_DATE','DUPLICATE_DATE','MISSING_OR_NONNUMERIC','NONPOSITIVE']:
            n=int(errors.str.contains(issue,regex=False).sum())
            if n:quality_log(root,kind,issue,n,'See '+str(qpath.relative_to(root)),run_id)
    good['date']=pd.to_datetime(good['date']).dt.strftime('%Y-%m-%d')
    out=Path(root)/'data'/'validated'/f'{kind}_validated.csv';out.parent.mkdir(parents=True,exist_ok=True)
    good.to_csv(out,index=False)
    quality_log(root,kind,'VALIDATION_COMPLETE',len(bad),f'{len(good)} accepted, {len(bad)} quarantined',run_id)
    return good,bad

def save_raw(df,kind,root,run_id):
    path=Path(root)/'data'/'raw'/kind/f'{kind}_{run_id}.csv'
    path.parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(path,index=False)
    return path

def get_market(days=180):
    import yfinance as yf
    start=(datetime.now(timezone.utc)-timedelta(days=days)).date()
    end=(datetime.now(timezone.utc)+timedelta(days=1)).date()
    df=yf.download('^GSPC',start=str(start),end=str(end),auto_adjust=False,progress=False,threads=False)
    if df.empty:raise RuntimeError('Yahoo Finance returned no market rows')
    if isinstance(df.columns,pd.MultiIndex):df.columns=df.columns.get_level_values(0)
    df=df.reset_index()
    df.columns=[str(c).lower().replace(' ','_') for c in df.columns]
    if 'date' not in df.columns:raise ValueError('Unexpected Yahoo date schema')
    return df

def get_macro(days=180):
    url='https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS'
    r=requests.get(url,timeout=25);r.raise_for_status()
    df=pd.read_csv(io.StringIO(r.text))
    df.columns=[str(c).lower() for c in df.columns]
    if 'observation_date' in df.columns:df=df.rename(columns={'observation_date':'date'})
    if 'vixcls' in df.columns:df=df.rename(columns={'vixcls':'vix'})
    if 'date' not in df.columns:raise ValueError('Unexpected FRED date schema')
    start=pd.Timestamp.now(tz='UTC').tz_localize(None)-pd.Timedelta(days=days)
    return df.loc[pd.to_datetime(df['date'],errors='coerce')>=start.normalize()].copy()

def run_live(root='.',days=180):
    root=Path(root);run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:6]
    result={}
    for kind,fetch in [('market',get_market),('macro',get_macro)]:
        try:
            df=fetch(days)
            raw=save_raw(df,kind,root,run_id)
            quality_log(root,kind,'RAW_CAPTURED',len(df),str(raw.relative_to(root)),run_id)
            good,bad=validate(df,kind,root,run_id)
            result[kind]={'raw_rows':len(df),'accepted':len(good),'quarantined':len(bad)}
        except Exception as exc:
            quality_log(root,kind,'PIPELINE_FAILURE',0,f'{type(exc).__name__}: {exc}',run_id)
            result[kind]={'error':f'{type(exc).__name__}: {exc}'}
    return result

if __name__=='__main__':
    print(json.dumps(run_live(Path(__file__).resolve().parents[1]),indent=2))
