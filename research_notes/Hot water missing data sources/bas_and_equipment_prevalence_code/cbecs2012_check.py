import pandas as pd, numpy as np
df=pd.read_csv('cbecs12/puf2012.csv',low_memory=False)
for c in ['WTHTEQ','EMCS','SQFTC','PBA']: df[c]=pd.to_numeric(df[c],errors='coerce')
w=df.FINALWT
print('weighted bldgs (k)',w.sum()/1e3)
print(df.WTHTEQ.value_counts(dropna=False).to_dict(), df.EMCS.value_counts(dropna=False).to_dict())
wh=df.WTHTEQ.notna()
print('with water heating k', w[wh].sum()/1e3)
for v,l in [(1,'central'),(2,'distributed'),(3,'both')]:
    print(l, round(w[df.WTHTEQ==v].sum()/w[wh].sum()*100,1))
cen=df.WTHTEQ.isin([1,3]); ok=df.EMCS.notna()
print('EMCS yes all', round(w[(df.EMCS==1)].sum()/w[ok].sum()*100,1),
 ' floor', round((w*df.SQFT)[(df.EMCS==1)].sum()/(w*df.SQFT)[ok].sum()*100,1))
print('EMCS among central/both wh', round(w[cen&(df.EMCS==1)].sum()/w[cen&ok].sum()*100,1))
print('central/both AND EMCS, of wh', round(w[cen&(df.EMCS==1)].sum()/w[wh&ok].sum()*100,1))
g=df.assign(sz=pd.cut(df.SQFT,[0,5000,50000,1e12],labels=['<=5k','5-50k','>50k']))
for s in ['<=5k','5-50k','>50k']:
    m=(g.sz==s)
    print(s,'EMCS of wh', round(w[m&wh&(df.EMCS==1)].sum()/w[m&wh&ok].sum()*100,1),'central&EMCS of wh', round(w[m&cen&(df.EMCS==1)].sum()/w[m&wh&ok].sum()*100,1))
