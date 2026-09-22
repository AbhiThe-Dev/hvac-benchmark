"""Real DEV data, prediction-quality side only: does adding an arm's simulated pools improve the held-out REAL log-density of the vav_zone likelihood?
(held-out unit = a real season of the 30-day DEV pool; likelihood fitted on the other real seasons, +/- the arm's simulated pools; positive = sim helps.)
Same metric as scripts/21_data_decisions.py (previous sim pools: -0.011 nats/reading). Calibration on real is NOT assessed here (see report: real-only nested results are unchanged by DR).
"""
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.active import selection as SEL
from docmismatch.active.model import fit_slot_models, tf
from docmismatch.active.real_data import load_real_dev
from docmismatch.dr import verifier_eval as V
from docmismatch.dr.pools import DR_DIR, load_pool


def heldout_ll(models, pool, mask, slot):
    sp = pool.slots[slot]; idx = np.where(mask)[0]; tot = {}
    for k, m in models.items():
        mM, sM, mX, sX, _ = m.params(pool.ctx[idx])
        ll, n = 0.0, 0
        for mem in range(len(sp.members)):
            for o in range(len(sp.owners)):
                v = sp.E[idx, k, o, mem]; f = np.isfinite(v)
                if not f.any(): continue
                y = tf(v[f]); mu, sd, tau = (mM[f], sM[f], m.fit["M"].tau) if o == mem else (mX[f], sX[f], m.fit["X"].tau)
                var = sd ** 2 + tau ** 2
                ll += float((-0.5 * (np.log(2 * np.pi * var) + (y - mu) ** 2 / var)).sum()); n += int(f.sum())
        tot[k] = (ll, n)
    return tot


def main():
    p = load_real_dev(); Vv = SEL.get("sel"); slot = "vav_zone"; out = {}
    for arm, a in V.arms().items():
        sims = [load_pool(t, 0, a["tel"]) for t in a["train"]]
        sims = [s for s in sims if slot in s.slots]
        res = {}
        for ho in range(4):
            tr = p.season != ho
            A = fit_slot_models([p], slot, "oat", [tr], **Vv["fitkw"])
            B = fit_slot_models([p] + sims, slot, "oat", [tr] + [np.ones(s.n_slices, bool) for s in sims], **Vv["fitkw"])
            la, lb = heldout_ll(A, p, p.season == ho, slot), heldout_ll(B, p, p.season == ho, slot)
            res[ho] = {k: (la[k][0] / la[k][1], lb[k][0] / lb[k][1]) for k in la if k in lb}
        d = {k: [res[h][k][1] - res[h][k][0] for h in res if k in res[h]] for k in (0, 1, 2)}
        out[arm] = dict(per_season=res, mean_gain_by_channel={k: float(np.mean(v)) for k, v in d.items()}, mean_gain=float(np.mean([x for v in d.values() for x in v])), n_sim_pools=len(sims))
        print(arm, out[arm]["mean_gain_by_channel"], round(out[arm]["mean_gain"], 4), flush=True)
    (DR_DIR / "real_dev_logdensity.json").write_text(json.dumps(out, indent=1, default=float))


main()
