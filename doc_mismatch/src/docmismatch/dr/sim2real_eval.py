"""Zero-shot sim-to-real transfer (see PREREGISTRATION_DR.md Addendum): fit the vav_zone likelihood on an arm's SIMULATED
training buildings only (zero real rows), score it against the real building's vav_zone episodes (real DEV pool, seed 2026).
Reuses active.readiness's inner-fold machinery (unmodified) for the sim leave-one-building-out reliability-layer fit,
and a small dedicated loop for the outer real episodes (real slicing/day-clustering isn't expressible by SimKind's window logic).
"""

from __future__ import annotations

import numpy as np

from ..active import readiness as RD
from ..active import selection as SEL
from ..active.engine import run_episode
from ..active.real_data import load_real_dev, real_episodes
from ..active.reliability import Support, features_at, first_cross
from ..active.readiness import SimKind, h32
from .verifier_eval import cases_for


def real_vav_zone_episodes():
    """Real DEV pool + its vav_zone episodes, with context converted from the real loader's native degF to the
    simulation's degC (the only unit fix here; a real bug caught by a dry run before the full launch: sim ctx
    oat ranges ~[-7,27] C, real ctx is degF ~[30,90], so an unconverted sim-fit model saw every real day as an
    impossible temperature and answered at chance. NOTE (caveat, not fixed): sim's 2nd context feature is the
    slice's diurnal OAT RANGE (max-min); real's is OAT STANDARD DEVIATION. Both are called "swing" under the
    shared CTX_NAMES scheme but are different statistics -- a pre-existing definitional mismatch in the project,
    harmless when each domain is only ever scored with its own fit, not harmless here. Left uncorrected (reported
    as a caveat) rather than silently redefined, since range vs sd is itself a judgment call."""
    import copy
    pool = load_real_dev()
    p2 = copy.copy(pool)
    ctx = pool.ctx.copy()
    ctx[:, 0] = (ctx[:, 0] - 32.0) * 5.0 / 9.0
    ctx[:, 1] = ctx[:, 1] * 5.0 / 9.0
    p2.ctx = ctx
    eps = [e for e in real_episodes(p2) if e.slot == "vav_zone"]
    return p2, eps


def _outer_rec(e, mod, beta, cfg, variant_runkw, pol, support):
    sl = np.where(e.pool.group == e.meta["day"])[0]
    seed = h32(e.ep_id) % 10_000
    r = run_episode(e, mod, sl, pol, tau=2.0, nmax=cfg["nmax"], seed=seed, beta=beta, diag=True, **variant_runkw)
    if r is None:
        return None
    crossed, n = first_cross(r.traj, cfg["tau"])
    f = features_at(r.diag, n, support)
    say = bool(r.traj[n] >= 0.5)
    return dict(policy=pol, setting="real_dev", rep=0, ep=f"realday{e.meta['day']:02d}|{e.ep_id}", slot=e.slot, wrong=bool(e.is_wrong),
                cluster=e.group, crossed=crossed, n=n, say_correct=say, p_stop=float(r.traj[n]), f=f.astype(np.float32),
                traj=r.traj.astype(np.float32), n_info=int(r.info_traj[min(n, len(r.info_traj) - 1)]), group=e.group,
                season=e.meta["season"], family=e.meta["family"], obs=e.meta["obs"], unit="real_dev")


def run_arm(train_buildings: list[str], tel: str, pools: dict, cfg: dict, real_pool, real_eps: list, procs: int = 1) -> dict:
    V = SEL.get(cfg["variant"])
    sim_kind = SimKind(cfg, topos=train_buildings, pools=pools, cases=cases_for(train_buildings))
    tr = sim_kind.train(train_buildings)
    mod, beta = sim_kind.fit_slot(tr, "vav_zone", None)
    if not mod:
        return dict(ok=False, reason="no vav_zone model for this arm")
    support = sim_kind.support(tr)
    outer = {pol: [_outer_rec(e, mod, beta, cfg, V["runkw"], pol, support) for e in real_eps] for pol in cfg["policies"]}
    outer = {pol: [r for r in rs if r is not None] for pol, rs in outer.items()}
    # inner: sim leave-one-training-building-out records (unmodified readiness.py machinery; zero real rows)
    RD._G["kind"], RD._G["cfg"] = sim_kind, cfg
    beta_map = {"vav_zone": beta}
    jobs = [dict(kind="inner", train=[u for u in train_buildings if u != h], test=h, beta=beta_map, outer="sim2real") for h in train_buildings]
    inner = [r for x in RD._pmap(RD._run_task, jobs, procs) for r in x if r["slot"] == "vav_zone"]
    rows = []
    for pol in cfg["policies"]:
        for r in outer[pol]:
            rows.append(RD._decide("none", None, r, cfg))
        io = [r for r in inner if r["policy"] == pol]
        lay = RD._mk_layer(cfg["layer"]).fit_all(io) if io else None
        for r in outer[pol]:
            rows.append(RD._decide("new", lay, r, cfg))
    return dict(ok=True, rows=rows, beta=beta, n_outer=len(real_eps), n_inner=len(inner))
