"""Cheap check (exploratory, not pre-registered): if the active-testing loop stopped recommending more reads
once marginal information gain became negligible -- instead of always spending the full nmax=24 budget -- how
many of the 24 real-DEV `vav_zone` reads would actually have been skipped, and does skipping them change the
final belief at all? Uses the SAME zero-shot sim-fit model as every other Addendum-5/6 check; real DEV only,
never SEALED. Informs whether an EIG/cost-aware early-stopping rule (proposed after the honesty-ceiling result)
is worth building properly.
  .venv/bin/python doc_mismatch/scripts/38_early_stop_check.py
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.active.engine import run_episode  # noqa: E402
from docmismatch.active.readiness import SimKind, h32  # noqa: E402
from docmismatch.dr.pools import load_pool  # noqa: E402
from docmismatch.dr.sim2real_eval import real_vav_zone_episodes  # noqa: E402
from docmismatch.dr.verifier_eval import EXISTING, cases_for, make_cfg  # noqa: E402

N_EPS = 300
EPS = 1e-12


def entropy(p):
    p = np.clip(p, EPS, 1.0)
    return float(-(p * np.log2(p)).sum())


def main():
    cfg = make_cfg(("active",))
    cfg["sim_reps"] = [0]
    train = EXISTING
    train_pools = {t: {0: load_pool(t, 0, "legacy")} for t in train}
    sim_kind = SimKind(cfg, topos=train, pools=train_pools, cases=cases_for(train))
    tr_all = sim_kind.train(train)
    mod, beta = sim_kind.fit_slot(tr_all, "vav_zone", None)

    real_pool, real_eps = real_vav_zone_episodes()
    eps = real_eps[:N_EPS]

    nmax = 24
    gains = np.zeros((len(eps), nmax))   # realized entropy reduction at each read index (1-indexed reads, 0-indexed array)
    n_used = 0
    for e in eps:
        sl = np.where(e.pool.group == e.meta["day"])[0]
        seed = h32(e.ep_id) % 10_000
        r = run_episode(e, mod, sl, "active", tau=2.0, nmax=nmax, seed=seed, beta=beta, diag=True)
        if r is None:
            continue
        post_hist = r.diag["post"]  # (nmax+1, H)
        H = np.array([entropy(post_hist[t]) for t in range(len(post_hist))])
        g = -np.diff(H)  # entropy REDUCTION per read (positive = informative)
        gains[n_used, :len(g)] = g[:nmax]
        n_used += 1
    gains = gains[:n_used]

    mean_gain = gains.mean(0)
    cum = np.cumsum(mean_gain)
    total = cum[-1]
    print(f"n episodes={n_used}", flush=True)
    print(f"mean per-read entropy reduction (bits), reads 1..24:")
    for i in range(nmax):
        frac = cum[i] / total if total > 0 else 0.0
        print(f"  read {i + 1:2d}: gain={mean_gain[i]:.5f} bits, cumulative={cum[i]:.4f} ({frac:.1%} of total 24-read reduction)")

    # simulate an early-stop rule: stop once the trailing-3-read mean gain drops below a small bar,
    # relative to the FIRST read's gain (a natural, scale-free "diminishing returns" threshold)
    for bar_frac in (0.10, 0.05, 0.02):
        bar = bar_frac * mean_gain[0] if mean_gain[0] > 0 else 0.0
        stops = []
        for i in range(len(gains)):
            g = gains[i]
            n_stop = nmax
            for t in range(2, nmax):
                if g[t - 2:t + 1].mean() < bar:
                    n_stop = t + 1
                    break
            stops.append(n_stop)
        stops = np.array(stops)
        print(f"\nearly-stop bar = {bar_frac:.0%} of read-1 gain ({bar:.5f} bits): "
              f"mean reads used = {stops.mean():.1f} / {nmax} ({stops.mean() / nmax:.0%}), "
              f"median = {np.median(stops):.0f}, reads saved on average = {nmax - stops.mean():.1f}")


main()
