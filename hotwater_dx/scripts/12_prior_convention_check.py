import sys
sys.path.insert(0, "src")
import numpy as np
from hotwater_dx import stress as S, causes as C
from hotwater_dx.engine import fit
from hotwater_dx.matrix import build_world
from hotwater_dx.sensitivity import SENS_CONFIG, _mix_cases

seed = SENS_CONFIG["SEED"]
lk = fit(build_world(n_theta=S.N_FIT, seed=S.SEED_FIT))
spec0 = S.Spec("matched")
w0 = S.build_test_world(spec0, S.SEED_TEST + 0)
cases0 = S.make_cases(w0, S.SEED_TEST + 1000)
ev_seed = S.SEED_TEST + 2000
causes = sorted({c[0][0] for c in cases0 if len(c[0]) == 1})
absent = [c for c in C.IDS if c not in causes]
print("causes in test visits:", len(causes), "absent:", absent)
rng = np.random.default_rng(seed)
mixes = [rng.dirichlet([SENS_CONFIG["MIX_ALPHA"]] * len(causes)) for _ in range(SENS_CONFIG["MIX_DRAWS"])]
def top1(cs, **kw):
    return S.metrics(S.evaluate(lk, cs, spec0, kw, ev_seed))["top1"]
rows = []
for i, mix in enumerate(mixes):
    cs = _mix_cases(cases0, mix, np.random.default_rng(seed + 10 + i))
    uni = top1(cs)
    for name, pr in (("oracle", mix), ("wrong", mixes[(i + 1) % len(mixes)])):
        zero = dict(zip(causes, pr))                                   # Addendum 4 convention: absent causes get prior 0
        neutral = dict(zero); [neutral.setdefault(c, float(np.mean(pr))) for c in absent]   # absent causes keep a share
        rows.append((i, name, top1(cs, prior_vec=zero) - uni, top1(cs, prior_vec=neutral) - uni))
for name in ("oracle", "wrong"):
    r = [x for x in rows if x[1] == name]
    print(f"{name:7s} A4 convention (absent causes zeroed): mean d_top1 {np.mean([x[2] for x in r]):+.3f}   |   absent causes kept: {np.mean([x[3] for x in r]):+.3f}   per-mix kept: {[round(x[3],3) for x in r]}")
