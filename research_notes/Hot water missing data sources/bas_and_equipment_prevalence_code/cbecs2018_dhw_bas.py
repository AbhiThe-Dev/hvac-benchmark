"""CBECS 2018 public-use microdata: DHW equipment configuration x BAS (EMCS) prevalence.
Run: venv/bin/python -I code/cbecs2018_dhw_bas.py
Variance: jackknife, V = sum_r (theta_r - theta)^2, R=151 (CBECS 2018 User's Guide, jkcoefs=1).
Weights: FINALWT (buildings). Floorspace-weighted = FINALWT*SQFT.
"""
import pandas as pd, numpy as np
df = pd.read_csv('cbecs_data/cbecs2018_final_public.csv')
W = df['FINALWT'].values
R = np.column_stack([df[f'FINALWT{i}'].values for i in range(1,152)])
sq = df['SQFT'].values

PBA = {1:'Vacant',2:'Office',4:'Laboratory',5:'Nonrefrig warehouse',6:'Food sales',7:'Public order/safety',
 8:'Outpatient health',11:'Refrig warehouse',12:'Religious worship',13:'Public assembly',14:'Education',
 15:'Food service',16:'Inpatient health',17:'Nursing',18:'Lodging',23:'Strip mall',24:'Enclosed mall',
 25:'Retail (non-mall)',26:'Service',91:'Other'}
SZ = {2:'1k-5k',3:'5k-10k',4:'10k-25k',5:'25k-50k',6:'50k-100k',7:'100k-200k',8:'200k-500k',9:'500k-1M',10:'>1M'}

def est(num, den, fw=False):
    """share = sum(w*num)/sum(w*den); returns pct, rse%, unweighted n in den"""
    num=np.asarray(num,float); den=np.asarray(den,float); num=num*den  # numerator restricted to denominator
    s = sq if fw else 1.0
    th = (W*s*num).sum()/max((W*s*den).sum(),1e-9)
    thr = (R*(s*num)[:,None]).sum(0)/np.maximum((R*(s*den)[:,None]).sum(0),1e-9)
    se = np.sqrt(((thr-th)**2).sum())
    return 100*th, (100*se/(100*th) *100 if th>0 else np.nan), int(den.sum())

def total(mask, fw=False):
    mask=np.asarray(mask,float); s = sq if fw else 1.0
    t=(W*s*mask).sum(); tr=(R*(s*mask)[:,None]).sum(0)
    return t, np.sqrt(((tr-t)**2).sum())/t*100

allb = np.ones(len(df),bool)
wat = (df.WATR==1).values
cen = df.WTHTEQ.isin([1,3]).values        # centralized or both
poi = (df.WTHTEQ==2).values               # point-of-use only
both = (df.WTHTEQ==3).values
cenonly = (df.WTHTEQ==1).values
emcs = (df.EMCS==1).values
valid = df.EMCS.notna().values   # BAS share denominators restrict to valid EMCS responses
print('N sample', len(df), ' weighted bldgs', W.sum()/1e3, 'k')
print('missing counts: WATR', df.WATR.isna().sum(),' WTHTEQ among WATR=1:', df.loc[wat,'WTHTEQ'].isna().sum(), ' EMCS na:', df.EMCS.isna().sum(), ' EMCS na among central:', df.loc[cen,'EMCS'].isna().sum())
print(pd.crosstab(df.WATR, df.WTHTEQ.fillna(-1)))
print(pd.crosstab(df.WATR, df.EMCS.fillna(-1)))

def line(label, num, den):
    p,r,n = est(num,den); pf,rf,_ = est(num,den,True)
    return dict(label=label, bldg_pct=round(p,1), bldg_rse=round(r,1), floor_pct=round(pf,1), floor_rse=round(rf,1), n=n)

rows=[]
rows.append(line('Bldgs w/ any water heating (of all)', wat, allb))
rows.append(line('  Of water-heated: centralized only', cenonly, wat))
rows.append(line('  Of water-heated: point-of-use only', poi, wat))
rows.append(line('  Of water-heated: both', both, wat))
rows.append(line('  Of water-heated: centralized or both', cen, wat))
for f,n in [('ELWATR','electricity'),('NGWATR','natural gas'),('FKWATR','fuel oil'),('PRWATR','propane'),('STWATR','district steam'),('HWWATR','district hot water'),('SOWATR','solar thermal'),('WOWATR','wood'),('COWATR','coal'),('OTWATR','other')]:
    rows.append(line(f'  Of water-heated: fuel {n} ({f})', (df[f]==1).values, wat))
rows.append(line('  Of water-heated: booster heaters (BOOSTWT=1)', (df.BOOSTWT==1).values, wat))
rows.append(line('  Of water-heated: waste heat used (WHWT=1)', (df.WHWT==1).values, wat))
rows.append(line('  Of water-heated: has large hot-water space (HWTRM=1)', (df.HWTRM==1).values, wat))
rows.append(line('All bldgs: BAS/EMCS present', emcs, allb&valid))
rows.append(line('Water-heated bldgs: BAS present', emcs, wat&valid))
rows.append(line('Centralized/both bldgs: BAS present', emcs, cen&valid))
rows.append(line('Point-of-use-only bldgs: BAS present', emcs, poi&valid))
rows.append(line('Water-heated: centralized/both AND BAS', cen&emcs, wat&valid))
rows.append(line('Water-heated: centralized/both, NO BAS', cen&~emcs, wat&valid))
rows.append(line('Water-heated: BAS controls heating (EMCSHT=1) & central/both', cen&(df.EMCSHT==1).values, wat&valid))
rows.append(line('Water-heated: smart thermostat present (SMRTTHRM=1)', (df.SMRTTHRM==1).values, wat))
rows.append(line('Centralized/both bldgs: has dist. hot-water/steam/boiler heating? (BOILER_*)', (df[[c for c in df.columns if c.startswith('BOILER_') and not c.startswith('Z')]]==1).any(axis=1).values, cen))
out=pd.DataFrame(rows); pd.set_option('display.width',250,'display.max_colwidth',90)
print(out.to_string(index=False)); out.to_csv('cbecs2018_national.csv',index=False)

def by(var, mp, name):
    rr=[]
    for k,lab in mp.items():
        g = (df[var]==k).values
        if g.sum()==0: continue
        tw,_ = total(g&wat)
        a=dict(group=lab, n_sample=int(g.sum()), bldgs_k=round(total(g)[0]/1e3), waterheated_bldgs_k=round(tw/1e3))
        for lab2,num,den in [('pct_waterheated',wat,g),('pct_cen_or_both_of_wh',cen,g&wat),('pct_poi_only_of_wh',poi,g&wat),('pct_BAS_of_all',emcs,g&valid),('pct_BAS_of_wh',emcs,g&wat&valid),('pct_BAS_of_cen',emcs,g&cen&valid),('pct_cen_AND_BAS_of_wh',cen&emcs,g&wat&valid)]:
            p,r,n = est(num,den); a[lab2]=round(p,1) if n>=20 else np.nan; a[lab2+'_rse']=round(r) if n>=20 else np.nan; 
        rr.append(a)
    t=pd.DataFrame(rr); print('\n== by',name); print(t.to_string(index=False)); t.to_csv(f'cbecs2018_by_{name}.csv',index=False); return t
by('PBA',PBA,'activity'); by('SQFTC',SZ,'size')
# size grouping used for the product: small <=5k (rare BAS), 5-50k, >50k
df=df.copy(); df['SZ3']=pd.cut(df.SQFT,[0,5000,50000,1e12],labels=['<=5k','5k-50k','>50k']).astype(str)
by('SZ3',{'<=5k':'<=5k','5k-50k':'5k-50k','>50k':'>50k'},'size3')
# key product-relevant segments: lodging, health inpatient/nursing, education, office, food service
