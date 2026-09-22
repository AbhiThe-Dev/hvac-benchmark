from hv import *
import sys
I=dict(info_mode='info',online_info=True)
SP=dict(shared_pair=True)
cfgs={
 **{f'capsel{c}':dict(ctx='oat',policies=['active'],fitkw=dict(shared_pair=True,**I),runkw=dict(shared_pair=True,online_info=True,pair_cap=c,sel_pooled=True)) for c in (2,3)},

 'selpool':dict(ctx='oat',policies=['active','random'],fitkw=dict(shared_pair=True,**I),runkw=dict(shared_pair=True,online_info=True,sel_pooled=True)),
 'selpool_nosp':dict(ctx='oat',policies=['active'],fitkw=dict(**I),runkw=dict(online_info=True,sel_pooled=True)),

 **{f'cap{c}':dict(ctx='oat',policies=['active'],fitkw=dict(shared_pair=True,**I),runkw=dict(shared_pair=True,online_info=True,pair_cap=c)) for c in (1,2,3,4,6)},

 'sp':dict(ctx='oat',policies=['active','random'],fitkw=dict(shared_pair=True),runkw=dict(shared_pair=True)),
 'info_sp':dict(ctx='oat',policies=['active','random'],fitkw=dict(shared_pair=True,**I),runkw=dict(shared_pair=True,online_info=True)),
 'info_sp_clip':dict(ctx='oat',policies=['active','random'],fitkw=dict(shared_pair=True,clip_ctx=True,**I),runkw=dict(shared_pair=True,online_info=True)),

 'tM6':dict(ctx='oat',policies=['active'],fitkw=I,runkw=dict(online_info=True,tauM_min=0.6)),
 'tM12':dict(ctx='oat',policies=['active'],fitkw=I,runkw=dict(online_info=True,tauM_min=1.2)),

 'baselines':dict(ctx='oat',policies=['active','random','random_info','random_oracle'],fitkw=I,runkw=dict(online_info=True)),

 'tau2':dict(ctx='oat',policies=['active','random'],fitkw=I,runkw=dict(online_info=True,tau_scale=2.0)),
 'tau3':dict(ctx='oat',policies=['active','random'],fitkw=I,runkw=dict(online_info=True,tau_scale=3.0)),
 'taumin5':dict(ctx='oat',policies=['active','random'],fitkw=I,runkw=dict(online_info=True,tau_min=0.5)),
 'taumin8':dict(ctx='oat',policies=['active','random'],fitkw=I,runkw=dict(online_info=True,tau_min=0.8)),

 'info_calact':dict(ctx='oat',policies=['active','random'],fitkw=I,runkw=dict(online_info=True),calib_policy='active'),
 'info_b02':dict(ctx='oat',policies=['active','random'],fitkw=I,runkw=dict(online_info=True),calib=False,beta=0.2),
 'info_b1':dict(ctx='oat',policies=['active','random'],fitkw=I,runkw=dict(online_info=True),calib=False,beta=1.0),

 'base':dict(ctx='oat',policies=['active','random','frozen']),
 'info':dict(ctx='oat',policies=['active','random','frozen'],fitkw=dict(info_mode='info',online_info=True),runkw=dict(online_info=True)),
 'info_noonline':dict(ctx='oat',policies=['active','random'],fitkw=dict(info_mode='info')),
}
for name in sys.argv[1:]:
    t=time.time(); R=run_real(cfgs[name]); print("##",name,round(time.time()-t)); summ(R,name)
    for setting in ('loso','hist_loso'):
        for pol in sorted({r['policy'] for r in R}):
            rows=[r for r in R if r['setting']==setting and r['policy']==pol]
            print('   ',setting,pol,'finite frac %.2f'%np.mean([r['fin'].mean() for r in rows]),'distinct owners %.1f'%np.mean([len(set(r['j'])) for r in rows]),'doc share of reads %.2f'%np.mean([np.mean(r['j']==0) for r in rows]))
