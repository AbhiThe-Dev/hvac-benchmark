from hv import *
import hv, copy
pool,eps=real_episodes(); hv.POOL=pool
eps=[x for x in eps if (x[2].meta['obs']=='observable' or not x[2].is_wrong)]
hv.CFG=dict(ctx='oat',fitkw=dict(shared_pair=True,info_mode='info',online_info=True),runkw=dict(shared_pair=True,online_info=True),policies=[])
todo=[];seen=set()
for d in range(len(pool.days)):
    season=int(pool.season[pool.group==d][0])
    for slot in REAL_SLOTS:
        j=(slot,('s',season),pool.season!=season)
        if (j[0],j[1]) not in seen: seen.add((j[0],j[1])); todo.append(j)
with mp.get_context('fork').Pool(10) as P: hv.FIT2=dict(P.map(hv._fit,todo))
def work(item):
    d,season,e=item
    mask,key,sl=setting_args(hv.POOL,'hist_loso',d,season)
    mod,beta=hv.FIT2[(e.slot,key)]
    sp=hv.POOL.slots[e.slot]
    out=dict(slot=e.slot,wrong=e.is_wrong,season=season)
    for variant in ('base','shift_all','shift_X_oracle'):
        m2=copy.deepcopy(mod)
        if variant!='base':
            for k,m in m2.items():
                mM,sM,mX,sX,pi=m.params(hv.POOL.ctx[sl])
                # residuals of all finite readings in the pool (unlabeled: any pair) vs X mean
                if variant=='shift_all':
                    v=sp.E[sl,k]; y=tf(v); f=np.isfinite(y); res=(y-mX[:,None,None])[f].mean() if f.any() else 0.0
                else:
                    res=[]
                    for o in range(10):
                        for mm in range(10):
                            if o==mm: continue
                            v=tf(sp.E[sl,k,o,mm]); f=np.isfinite(v); res+=list((v-mX)[f])
                    res=np.mean(res) if res else 0.0
                for z in ('M','X'):
                    m.fit[z].bm=m.fit[z].bm.copy(); m.fit[z].bm[0]+=res
        for pol in ('active','random'):
            r=run_episode(e,m2,sl,pol,tau=2.0,seed=h32(e.ep_id)%10000,beta=beta,shared_pair=True,online_info=True)
            out[(variant,pol)]=r.traj
    return out
with mp.get_context('fork').Pool(10) as P: res=P.map(work,eps,chunksize=4)
for season in (0,None):
  rr=[r for r in res if season is None or r['season']==season]
  w=[r['wrong'] for r in rr]
  for variant in ('base','shift_all','shift_X_oracle'):
    for pol in ('active','random'):
        print('season',season,variant,pol,' '.join(f"{bal([(r[(variant,pol)][n]>=.5)!=r['wrong'] for r in rr],w):.2f}" for n in (1,2,4,8,12,24)))
