import sys, hashlib, pickle
sys.path.insert(0,__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),'..','..','src'))
import numpy as np
from docmismatch import real_frp as R
from docmismatch.active.engine import Episode, run_episode, _Actions
from docmismatch.active.model import fit_slot_models, tf
from docmismatch.active.calibrate import calibrate_beta_seasons
from docmismatch.active.real_pool import REAL_SLOTS, load_or_build_real
from docmismatch.active.pools import hypotheses
def h32(s): return int(hashlib.sha1(s.encode()).hexdigest()[:8],16)
def real_episodes():
    pool=load_or_build_real(); rng=np.random.default_rng(11); out=[]
    for d,day in enumerate(pool.days):
        season=int(pool.season[pool.group==d][0]); ser=pool.day_series[d]
        for slot in REAL_SLOTS:
            pairs=[(a,b) for a in range(10) for b in range(10) if a!=b]
            wrong=[pairs[i] for i in rng.choice(len(pairs),20,replace=False)]
            eps=[Episode(pool,slot,b,a,b,True,f"real|{day}|{slot}|{a}>{b}|wrong",f"{day}|{slot}",{}) for a,b in wrong]
            for b in rng.choice(10,10,replace=False):
                eps.append(Episode(pool,slot,int(b),int(b),int(b),False,f"real|{day}|{slot}|{b}|right",f"{day}|{slot}",{}))
            for e in eps:
                if e.is_wrong:
                    a,b=e.doc,e.member
                    e.meta={"obs":R.observability(ser,R.Event(slot,min(a,b),max(a,b))),"family":R.FAMILY[slot]}
                else: e.meta={"obs":"n/a","family":"clean"}
                out.append((d,season,e))
    return pool,out
def setting_args(pool,setting,d,season):
    if setting=='lodo': return pool.group!=d, ('d',d), np.where(pool.group==d)[0]
    if setting=='loso': return pool.season!=season, ('s',season), np.where(pool.group==d)[0]
    return pool.season!=season, ('s',season), np.where(pool.season==season)[0]

import multiprocessing as mp, time
FITS={}
_G={}
def _one(j):
    pool,use_ctx,calib=_G['pool'],_G['ctx'],_G['calib']
    slot,key,mask=j
    mod=fit_slot_models([pool],slot,use_ctx,[mask])
    return (slot,use_ctx,key),(mod, calibrate_beta_seasons(pool,slot,use_ctx,mask) if (mod and calib) else 1.0)
def build_fits(pool, use_ctx='oat', calib=True):
    t=time.time(); _G.update(pool=pool,ctx=use_ctx,calib=calib)
    todo=[]; seen=set()
    for d in range(len(pool.days)):
        season=int(pool.season[pool.group==d][0])
        for slot in REAL_SLOTS:
            for j in ((slot,('d',d),pool.group!=d),(slot,('s',season),pool.season!=season)):
                k=(j[0],use_ctx,j[1])
                if k in seen: continue
                seen.add(k); todo.append(j)
    with mp.get_context('fork').Pool(10) as P: res=P.map(_one,todo)
    for k,v in res: FITS[k]=v
    print('fits',len(FITS),time.time()-t,flush=True)
def pmap(fn, items, n=10):
    with mp.get_context('fork').Pool(n) as P: return P.map(fn, items, chunksize=4)
