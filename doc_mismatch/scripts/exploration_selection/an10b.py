from hv import *
from harness import _Actions
import hv
# analysis: which readings carry the evidence? held-out-season (hist_loso) models with info config
hv.CFG=dict(ctx='oat',policies=[],fitkw=dict(info_mode='info',online_info=True),runkw={})
pool,eps=real_episodes(); hv.POOL=pool
eps=[x for x in eps if (x[2].meta['obs']=='observable' or not x[2].is_wrong)]
hv.EPS=eps
todo=[];seen=set()
for d in range(len(pool.days)):
    season=int(pool.season[pool.group==d][0])
    for slot in REAL_SLOTS:
        j=(slot,('s',season),pool.season!=season)
        if (j[0],j[1]) in seen: continue
        seen.add((j[0],j[1])); todo.append(j)
with mp.get_context('fork').Pool(10) as P: hv.FIT2=dict(P.map(hv._fit,todo))
def work(item):
    d,season,e=item
    mask,key,sl=setting_args(hv.POOL,'hist_loso',d,season)
    mod,beta=hv.FIT2[(e.slot,key)]
    hy=hypotheses(hv.POOL.slots[e.slot],e.doc); acts=_Actions(e,mod,hy,sl,3.0)
    rng=np.random.default_rng(h32(e.ep_id)%1000)
    fin=np.isfinite(acts.y)
    out={}
    def acc(sel,n=24,per_owner_cap=None):
        idx=np.flatnonzero(sel); rng.shuffle(idx); idx=idx[:n]
        if len(idx)==0: return np.nan
        r=run_episode(e,mod,sl,'custom',tau=2.0,order=idx,beta=beta,nmax=len(idx),online_info=True)
        return r.traj[len(idx)] if len(r.traj)>len(idx) else r.traj[-1]
    doc=acts.j==0
    for name,sel in (('oracle_random',fin),('doc_only',fin&doc),('nondoc_only',fin&~doc)):
        out[name]=acc(sel)
    for nrr in (8,12,18,24,36):
        idx=[]
        byj={jj:list(np.flatnonzero(fin&(acts.j==jj))) for jj in range(len(hy))}
        for jj in byj: rng.shuffle(byj[jj])
        while len(idx)<nrr and any(byj.values()):
            for jj in byj:
                if byj[jj] and len(idx)<nrr: idx.append(byj[jj].pop())
        r=run_episode(e,mod,sl,'custom',tau=2.0,order=idx,beta=beta,nmax=len(idx),online_info=True)
        out['rr%d'%nrr]=r.traj[min(len(idx),len(r.traj)-1)]
    out['full_fin']=acc(fin,n=10**6)
    return dict(slot=e.slot,wrong=e.is_wrong,d=d,**out)
with mp.get_context('fork').Pool(10) as P: res=P.map(work,eps,chunksize=4)
for slot in (None,'vav_zone','vav_sat','vav_pwr'):
    rr=[r for r in res if slot is None or r['slot']==slot]
    w=[r['wrong'] for r in rr]
    print(slot, {k:round(bal([(r[k]>=.5)!=r['wrong'] for r in rr],w),2) for k in ('oracle_random','doc_only','nondoc_only','rr8','rr12','rr18','rr24','rr36','full_fin')})
    for cls in (True,False):
        r2=[r for r in rr if r['wrong']==cls]
        print('    wrong' if cls else '    right',{k:round(np.mean([(r[k]>=.5)!=r['wrong'] for r in r2]),2) for k in ('oracle_random','doc_only','nondoc_only','rr8','rr12','rr18','rr24','rr36','full_fin')})
