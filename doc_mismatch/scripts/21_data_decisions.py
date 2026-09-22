"""Data decisions (dev only): (1) does adding simulated pools improve held-out REAL log-likelihood? (2) power analysis for verifying honest 95% confidence.
Held-out unit = a real SEASON; likelihood fitted on the other real seasons (+ optionally sim pools of the same slot). Metric: mean log-density of the
class-conditional Gaussian (mean, sd + pair effect) over held-out informative readings, real-only minus real+sim (positive = sim helps)."""
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.active import readiness as R, selection as SEL
from docmismatch.active.model import fit_slot_models, tf
from docmismatch.active.real_data import load_real_dev

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
    p = load_real_dev(); V = SEL.get("sel"); out = {}
    sim = [R.load_or_build_sim(t, r) for t in R.sim_manifest()["dev"] for r in (0,)]
    for slot in ("vav_zone",):
        sims = [s for s in sim if slot in s.slots]
        res = {}
        for ho in range(4):
            tr = p.season != ho
            a = fit_slot_models([p], slot, "oat", [tr], **V["fitkw"])
            b = fit_slot_models([p] + sims, slot, "oat", [tr] + [np.ones(s.n_slices, bool) for s in sims], **V["fitkw"])
            la, lb = heldout_ll(a, p, p.season == ho, slot), heldout_ll(b, p, p.season == ho, slot)
            res[ho] = {k: (la[k][0] / la[k][1], lb[k][0] / lb[k][1]) for k in la if k in lb}
        out[slot] = res
    # power analysis: episodes needed to show accuracy >= 0.93 with lower 95% bound >= 0.90 when true accuracy is 0.95, design effect d
    from math import sqrt
    def need(acc, d, lb=0.90, z=1.645):
        return int(np.ceil(d * z ** 2 * acc * (1 - acc) / (acc - lb) ** 2))
    out["power"] = {f"true_acc={a},deff={d}": need(a, d) for a in (0.95, 0.97) for d in (1, 4)}
    out["power_note"] = "answered verdicts needed (one-sided 95% normal bound, lower bound >= 0.90); independent clusters needed = answered / mean answered-per-cluster"
    (R.ACT / "final").mkdir(parents=True, exist_ok=True)
    (R.ACT / "final" / "data_decisions.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps(out, indent=1, default=float))
main()
