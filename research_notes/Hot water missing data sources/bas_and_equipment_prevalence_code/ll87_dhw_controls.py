"""NYC LL87 (2019-2024, Audit Template) : SHW (service hot water) system type + controls + BAS flag.
Source: https://data.cityofnewyork.us/d/au6c-jqvf  (xlsx, 10,702 rows, 1,986 cols). Unweighted, self-selected (NYC buildings >50k sf, LL87 filers).
Run: venv/bin/python -I code/ll87_dhw_controls.py"""
import pandas as pd, numpy as np
d=pd.read_pickle('ll87/sheet_in.pkl')
print('rows',len(d),'unique Audit Template ID',d['Audit Template ID'].nunique(),'unique BBL',d['Borough/Block/Lot (BBL)'].nunique())
print(d['Report Type'].value_counts().head())
# one row per audit template id already? keep latest submission per Audit Template ID
d['sub']=pd.to_datetime(d['Submission Date'],errors='coerce',utc=True)
d=d.sort_values('sub').drop_duplicates('Audit Template ID',keep='last')
print('after dedupe by ATID',len(d))
t1='Type: SHW Sys 1'
d['has_shw']=~d[t1].isin(['No SHW System'])&d[t1].notna()
print(d[t1].value_counts(dropna=False))
H=d[d.has_shw]
print('buildings w/ SHW sys1:',len(H))
def pct(s): return round(100*s.mean(),1)
ctl=['No Controls','Time Based Controls','Aquastat Based Controls','Demand Based Controls','EMS/BMS Controls','Other Controls']
# any SHW system (sys1..N) flagged EMS/BMS
sysn=[c for c in d.columns if c.startswith('EMS/BMS Controls : SHW Sys')]
anyems=d[sysn].fillna(0).max(axis=1)==1
d['any_shw_ems']=anyems
valid=d['EMS/BMS Controls : SHW Sys 1'].notna()
print('\nShare of audited bldgs (valid ctl response, has SHW) with SHW-EMS/BMS (any sys):', pct(d.loc[valid&d.has_shw,'any_shw_ems']), 'n=',(valid&d.has_shw).sum())
for c in ctl:
    col=f'{c} : SHW Sys 1'
    m=d.has_shw&d[col].notna()
    print(f'  {c:28s} {pct(d.loc[m,col]==1):5.1f}%  n={m.sum()}')
bas='Building automation system? (Y/N)'
m=d.has_shw&d[bas].notna()
print('\nBuilding BAS flag yes among SHW bldgs', pct(d.loc[m,bas]==1), 'n',m.sum())
print('Of BAS=Yes bldgs, share with SHW EMS/BMS ctl:', pct(d.loc[m&(d[bas]==1),'any_shw_ems']), 'n',(m&(d[bas]==1)).sum())
print('Of BAS=No bldgs, share with SHW EMS/BMS ctl:', pct(d.loc[m&(d[bas]==0),'any_shw_ems']), 'n',(m&(d[bas]==0)).sum())
# BAS heating-plant flag
hp='Building Automation System: Heating Plant 1'
mm=d.has_shw&d[hp].notna(); print('BAS on Heating Plant 1:', pct(d.loc[mm,hp]==1), 'n',mm.sum())
# by SHW type
print('\nBy SHW sys1 type: n, %EMS/BMS, %demand, %aquastat, %time')
g=d[d.has_shw&valid].groupby(t1)
print(pd.DataFrame({'n':g.size(),'ems_bms':g.apply(lambda x:pct(x['EMS/BMS Controls : SHW Sys 1']==1)),'demand':g.apply(lambda x:pct(x['Demand Based Controls : SHW Sys 1']==1)),'aquastat':g.apply(lambda x:pct(x['Aquastat Based Controls : SHW Sys 1']==1)),'bldg_BAS':g.apply(lambda x:pct(x[bas]==1))}).to_string())
# by primary use
u='Use Type: Space Function 1'
print(d[u].value_counts().head(8))
d['mf']=d[u].astype(str).str.contains('Multifamily|Residential|Dormitor',case=False)
for k,gp in d[d.has_shw&valid].groupby('mf'):
    print('\nMultifamily-like' if k else '\nNon-multifamily','n',len(gp),'| BAS',pct(gp[bas]==1),'| SHW EMS/BMS',pct(gp['any_shw_ems']),'| demand',pct(gp['Demand Based Controls : SHW Sys 1']==1),'| plant/boiler-fed (Type=Plant)',pct(gp[t1]=='Plant'), '| storage(direct/indirect)',pct(gp[t1].str.contains('Storage')),'| instantaneous',pct(gp[t1].str.contains('Instantaneous')),'| heat pump',pct(gp[t1]=='Heat Pump'))
# size
d['gfa']=pd.to_numeric(d['Gross Floor Area'],errors='coerce')
d['szb']=pd.cut(d.gfa,[0,100e3,250e3,1e9],labels=['<100k','100-250k','>250k'])
for k,gp in d[d.has_shw&valid].groupby('szb',observed=True):
    print(k,'n',len(gp),'| BAS',pct(gp[bas]==1),'| SHW EMS/BMS',pct(gp['any_shw_ems']))
# Year completed vintage
