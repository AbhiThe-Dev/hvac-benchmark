import sys; sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from harness import *
from harness import _Actions
import harness
POOL=None; EPS=None; CFG=None; FIT2={}
def _fit(j):
    slot,key,mask=j; c=CFG
    mod=fit_slot_models([POOL],slot,c['ctx'],[mask],**c.get('fitkw',{}))
    beta=calibrate_beta_seasons(POOL,slot,c['ctx'],mask,policy=c.get('calib_policy','random'),fitkw=c.get('fitkw',{}),runkw=c.get('runkw',{})) if (mod and c.get('calib',True)) else c.get('beta',1.0)
    return (slot,key),(mod,beta)
def _work(item):
    d,season,e=item; c=CFG; out=[]
    for setting in ('lodo','loso','hist_loso'):
        mask,key,sl=setting_args(POOL,setting,d,season)
        mod,beta=FIT2[(e.slot,key)]
        if not mod: continue
        for pol in c['policies']:
            r=run_episode(e,mod,sl,pol,tau=2.0,seed=h32(e.ep_id)%10000,beta=beta*c.get('beta_mult',1.0),**c.get('runkw',{}))
            if r is None: continue
            hy=hypotheses(POOL.slots[e.slot],e.doc); ac=_Actions(e,mod,hy,sl,3.0); o=np.array(r.order,int)
            out.append(dict(setting=setting,policy=pol,ep=e.ep_id,slot=e.slot,wrong=e.is_wrong,group=e.group,traj=r.traj,beta=beta,obs=e.meta['obs'],order=r.order,j=ac.j[o],k=ac.k[o],fin=np.isfinite(ac.y[o])))
    return out
def run_real(cfg, only_obs=True):
    global POOL,EPS,CFG,FIT2
    CFG=cfg
    POOL,eps=real_episodes()
    if only_obs: eps=[x for x in eps if (x[2].meta['obs']=='observable' or not x[2].is_wrong)]
    EPS=eps
    todo=[];seen=set()
    for d in range(len(POOL.days)):
        season=int(POOL.season[POOL.group==d][0])
        for slot in REAL_SLOTS:
            for j in ((slot,('d',d),POOL.group!=d),(slot,('s',season),POOL.season!=season)):
                if (j[0],j[1]) in seen: continue
                seen.add((j[0],j[1])); todo.append(j)
    ctx=mp.get_context('fork')
    with ctx.Pool(10) as P: res=P.map(_fit,todo)
    FIT2=dict(res)
    with ctx.Pool(10) as P: out=P.map(_work,EPS,chunksize=4)
    return [r for x in out for r in x]
def bal(v,w):
    v=np.asarray(v,float);w=np.asarray(w,bool); return np.mean([v[w].mean(),v[~w].mean()])
def summ(R,label='',ns=(1,2,4,8,24),tau=.95):
    for setting in ('lodo','loso','hist_loso'):
        for pol in sorted({r['policy'] for r in R}):
            rows=[r for r in R if r['setting']==setting and r['policy']==pol]
            w=[r['wrong'] for r in rows]
            acc=[bal([(r['traj'][n]>=.5)!=r['wrong'] for r in rows],w) for n in ns]
            # resolved
            res=[];okr=[];nn=[]
            for r in rows:
                t=r['traj']; hit=np.flatnonzero((t>=tau)|(t<=1-tau)); n=hit[0] if len(hit) else 24
                rs=len(hit)>0; res.append(rs); nn.append(n); okr.append((t[n]>=.5)!=r['wrong'])
            res=np.array(res); okr=np.array(okr); w=np.array(w)
            accres=bal(okr[res],w[res]) if res.any() and w[res].any() and (~w[res]).any() else float('nan')
            print(f"{label:14s}{setting:10s}{pol:10s} acc@{ns}: "+' '.join(f'{a:.2f}' for a in acc)+f" | resolved {bal(res,w):.2f} acc|res {accres:.2f} n_res {len(rows)}")
