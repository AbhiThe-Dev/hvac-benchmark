"""Adversarial search for the engine's failure regions (simulation only).

Idea #6 of the robustness brief: treat the simulator as an adversary, not as ground truth. Instead of the hand-picked mismatch worlds of the stress test, draw plants from a
*broad plausible family* (every continuous parameter extended half a range beyond the range the engine was fitted on, clipped to physical bounds), add per-visit operational
trouble (noisier instruments, skipped and misread checks, hidden crossover), and mine where the engine is confidently wrong ("scenario discovery": a permutation-tested
parameter profile plus PRIM boxes, Friedman and Fisher 1999). Then test two candidate fixes against held-out draws:

* R: the same engine with likelihoods refitted on the broad family (the adversary's family used as the training distribution), and
* G: a guard that switches to the robust variant when facts a technician can read on arrival fall inside the discovered failure box.

Everything is simulated, and the adversary can only find failures *inside this simulator's structure* (one plant archetype, steady state): it cannot find structural mismatch.
"""
from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import measurement as M
from . import stress as S
from .engine import PAIRS, Likelihoods, _strkeys, fit, parts, run_case
from .matrix import build_world
from .params import PARAMS
from .provenance import DISCLAIMER
from .sampling import substream
from .sensitivity import PHYS
from .solve import has_complaint
from . import causes as C
from . import checks as K

ADV_CONFIG = {
    "EXT_FACTOR": 0.5,                 # broad family: fitted range extended by this fraction of its span on each side (clipped to PHYS)
    "EXT2_FACTOR": 1.0,                # extrapolation probe: a full span on each side
    "N_PLANTS": 200,                   # plants per world
    "TRAIN_WORLDS": 8, "HELD_WORLDS": 6, "EXT2_WORLDS": 2,
    "PER_CAUSE": 60, "PER_PAIR": 9,    # cases per world: up to 60 symptomatic plants per single cause, 9 per seeded pair
    "OPS": {"noise": (1.0, 2.0), "p_skip": (0.0, 0.10), "p_garbage": (0.0, 0.10), "latent_p": 0.25},   # per-visit draws; no value exceeds the Addendum 3 composite world's
    "FIT": {"n_plants": 400, "noise": 1.5, "latent_p": 0.25},       # the family-trained likelihoods
    "PRIM": {"alpha": 0.05, "stop_support": 0.05, "select_support": 0.10, "boot": 500, "confirm_ratio": 1.5, "min_ratio": 2.0, "peel_frac": 2 / 3, "simplicity_tol": 0.01},
    "PERM": 200, "BINS": 5, "MIN_BIN": 30,
    # facts a technician can read or estimate on arrival (ANALYST): used for the guard
    "ARRIVAL": ("t_amb", "t_cold", "p_cold", "t_set_heater", "deadband", "heater_cap", "storage_gal", "t_set_tmv", "tmv_margin_min", "len_scale", "dT_design",
                "t_min_circ", "valve_thermal", "pump_oversize", "deadleg_ft"),
    # parameters whose one-at-a-time push beyond the fitted range mattered in Addendum 5 (exploratory)
    "ADD5": ("p_cold", "pump_oversize", "deadleg_ft", "t_set_tmv", "tmv_margin_min", "len_scale", "duty", "dT_design", "u_ins", "peak_frac", "tmv_sag_gain"),
    "BAR": {"family_top1_max": 0.65, "family_wc_min": 0.06, "refit_wc_cut": 0.30, "refit_top1_slack": 0.01, "wc_slack": 0.01, "top1_gain": 0.03, "conf_gain": 0.05,
            "matched_top1_drop": 0.05, "matched_wc_max": 0.05, "recover_frac": 0.5, "guard_min_ratio": 1.5},
    "VARIANTS": ("A_plain", "B_robust", "R_A", "R_B", "G_guard"),
    "SEED": 20261401,
}
OPS = ADV_CONFIG["OPS"]
PLANT_FEATS = tuple(p.name for p in PARAMS)
BINARY = frozenset(p.name for p in PARAMS if p.kind == "binary") | {"latent"}
OPS_FEATS = ("noise", "p_skip", "p_garbage", "latent")
ALL_FEATS = PLANT_FEATS + OPS_FEATS
CASE_LEVEL = ("noise", "p_skip", "p_garbage")


def frozen_hash() -> str:
    blob = dict(adv=_strkeys(ADV_CONFIG), phys=_strkeys(PHYS), engine_hash=__import__("hotwater_dx.engine", fromlist=["config_hash"]).config_hash(), stress=S.frozen_hash())
    return hashlib.sha256(json.dumps(blob, sort_keys=True, default=str).encode()).hexdigest()


# ------------------------------------------------------------------------------------------------ the broad family
def ext_overrides(factor: float) -> dict:
    ov = {}
    for p in PARAMS:
        if p.kind == "binary":
            continue
        span = p.high - p.low
        lo, hi = PHYS[p.name]
        ov[p.name] = (max(lo, p.low - factor * span), min(hi, p.high + factor * span))
    return ov


def family_world(factor: float, seed: int, n: int | None = None, latent_p: float | None = None):
    lp = OPS["latent_p"] if latent_p is None else latent_p
    return build_world(n_theta=n or ADV_CONFIG["N_PLANTS"], seed=seed, overrides=ext_overrides(factor), latent=S._latent(lp))


@dataclass
class FCase:
    truth: tuple
    ctx: object
    thermal: bool
    world: int
    plant: int
    theta: dict
    latent: bool
    healthy_complaint: bool
    noise: float
    p_skip: float
    p_garbage: float

    @property
    def key(self) -> tuple:
        return (self.world, self.plant)


def _plant_flags(w):
    return [has_complaint(P) for P in w.plants], [any(g > 0 for g in P.g_x) for P in w.plants]


def family_cases(w, wi: int, seed: int) -> list[FCase]:
    """Symptomatic single-fault and pair-fault visits with per-visit operational draws (noise, skipped and misread checks)."""
    rng = np.random.default_rng(seed)
    hc, lat = _plant_flags(w)
    out: list[FCase] = []

    def add(truth, ctx, j):
        r = np.random.default_rng(np.random.SeedSequence([seed, 5, len(out)]))
        out.append(FCase(truth, ctx, bool(w.plants[j].thermal), wi, j, w.design[j], lat[j], hc[j], float(r.uniform(*OPS["noise"])), float(r.uniform(*OPS["p_skip"])),
                         float(r.uniform(*OPS["p_garbage"]))))

    for cid in [c for c in w.cause_plants if int(w.cause_gated[c].sum()) >= 10]:
        idx = np.where(w.cause_gated[cid])[0]
        for j in rng.choice(idx, size=min(ADV_CONFIG["PER_CAUSE"], len(idx)), replace=False):
            add((cid,), w.cause_ctx[cid][int(j)], int(j))
    for pi, h in enumerate(PAIRS):
        a, b = (C.BY_ID[x] for x in parts(h))
        got, tries = 0, 0
        while got < ADV_CONFIG["PER_PAIR"] and tries < 40:
            j = int(rng.integers(len(w.plants)))
            tries += 1
            P = w.plants[j]
            da, db = a.draw(substream(w.seed, 9, pi, j, tries), P), b.draw(substream(w.seed, 9, pi, j, tries + 100), P)
            Q = b.apply(a.apply(P, da), db)
            if has_complaint(Q):
                add(tuple(parts(h)), K.Ctx(Q), j)
                got += 1
    return out


def make_cases_tracked(w, seed: int) -> list[tuple]:
    """Exactly stress.make_cases, but each case also carries the index of its plant (so arrival facts are known). Used for the Addendum 3 worlds."""
    rng = np.random.default_rng(seed)
    cases = []
    singles = [cid for cid in w.cause_plants if int(w.cause_gated[cid].sum()) >= 10]
    per = max(S.CASES_SINGLE // max(len(singles), 1), 1)
    for cid in singles:
        idx = np.where(w.cause_gated[cid])[0]
        for j in rng.choice(idx, size=min(per, len(idx)), replace=False):
            cases.append(((cid,), w.cause_ctx[cid][int(j)], bool(w.plants[int(j)].thermal), int(j)))
    per_pair = max(S.CASES_PAIR // len(PAIRS), 1)
    for pi, h in enumerate(PAIRS):
        a, b = (C.BY_ID[x] for x in parts(h))
        got, tries = 0, 0
        while got < per_pair and tries < 40:
            j = int(rng.integers(len(w.plants)))
            tries += 1
            P = w.plants[j]
            da, db = a.draw(substream(w.seed, 9, pi, j, tries), P), b.draw(substream(w.seed, 9, pi, j, tries + 100), P)
            Q = b.apply(a.apply(P, da), db)
            if has_complaint(Q):
                cases.append((tuple(parts(h)), K.Ctx(Q), bool(P.thermal), j))
                got += 1
    return cases


def spec_cases(w, wi_world: int, spec: S.Spec, seed: int) -> list[FCase]:
    hc, lat = _plant_flags(w)
    return [FCase(t, ctx, th, wi_world, j, w.design[j], lat[j], hc[j], spec.noise, spec.p_skip, spec.p_garbage) for t, ctx, th, j in make_cases_tracked(w, seed)]


def evaluate_family(lk: Likelihoods, cases: list[FCase], config: dict, seed: int, garbage_lk: Likelihoods | None = None) -> list:
    out = []
    try:
        for i, c in enumerate(cases):
            M.NOISE["scale"] = c.noise
            rng = np.random.default_rng(np.random.SeedSequence([seed, i]))
            out.append(run_case(lk, c.ctx, c.truth, rng, c.thermal, p_skip=c.p_skip, p_garbage=c.p_garbage, garbage_lk=garbage_lk, **config))
    finally:
        M.NOISE["scale"] = 1.0
    return out


# ------------------------------------------------------------------------------------------------ features, profile, PRIM
def feature_matrix(cases: list[FCase]) -> np.ndarray:
    X = np.zeros((len(cases), len(ALL_FEATS)))
    for i, c in enumerate(cases):
        for j, n in enumerate(PLANT_FEATS):
            X[i, j] = c.theta[n]
        X[i, len(PLANT_FEATS):] = (c.noise, c.p_skip, c.p_garbage, float(c.latent))
    return X


def plant_ids(cases: list[FCase]) -> np.ndarray:
    keys = {}
    return np.array([keys.setdefault(c.key, len(keys)) for c in cases])


def _bins(X: np.ndarray, names, nb: int) -> np.ndarray:
    B = np.zeros(X.shape, int)
    for j, n in enumerate(names):
        col = X[:, j]
        u = np.unique(col)
        if len(u) <= 2:
            B[:, j] = (col > u.min()).astype(int)
        else:
            B[:, j] = np.searchsorted(np.quantile(col, np.linspace(0, 1, nb + 1)[1:-1]), col, side="right")
    return B


def _spread(bins_f: np.ndarray, y: np.ndarray, nb: int, min_bin: int) -> float:
    cnt = np.bincount(bins_f, minlength=nb)
    s = np.bincount(bins_f, weights=y, minlength=nb)
    ok = cnt >= min_bin
    if ok.sum() < 2:
        return 0.0
    r = s[ok] / cnt[ok]
    return float(r.max() - r.min())


def profile(X: np.ndarray, y: np.ndarray, pid: np.ndarray, names=ALL_FEATS, nb: int | None = None, perms: int | None = None, seed: int = 0) -> list[dict]:
    """Per-feature failure-rate profile by quantile bin and a max-T permutation test (plant parameters are permuted across whole plants, per-visit knobs across visits)."""
    nb = nb or ADV_CONFIG["BINS"]
    perms = perms or ADV_CONFIG["PERM"]
    mb = ADV_CONFIG["MIN_BIN"]
    B = _bins(X, names, nb)
    F = len(names)
    obs = np.array([_spread(B[:, j], y, nb, mb) for j in range(F)])
    _, first = np.unique(pid, return_index=True)          # first case index of each plant (plant ids are 0..n-1)
    Bp = B[first]                                         # [plants, F]
    rng = np.random.default_rng(seed)
    null = np.zeros((perms, F))
    for b in range(perms):
        perm = rng.permutation(len(first))
        cperm = rng.permutation(len(y))
        for j, n in enumerate(names):
            bj = B[cperm, j] if n in CASE_LEVEL else Bp[perm[pid], j]
            null[b, j] = _spread(bj, y, nb, mb)
    mu, sd = null.mean(0), null.std(0) + 1e-12
    t_obs = (obs - mu) / sd
    thr = float(np.quantile(((null - mu) / sd).max(axis=1), 0.95))
    rows = []
    for j, n in enumerate(names):
        cnt = np.bincount(B[:, j], minlength=nb)
        rates = [float(np.bincount(B[:, j], weights=y, minlength=nb)[k] / cnt[k]) if cnt[k] >= mb else float("nan") for k in range(nb if len(np.unique(X[:, j])) > 2 else 2)]
        rows.append(dict(feature=n, spread=float(obs[j]), t=float(t_obs[j]), matters=bool(t_obs[j] > thr), rates=rates, thr=thr))
    rows.sort(key=lambda r: -r["t"])
    return rows


def prim(X: np.ndarray, y: np.ndarray, names, cols: list[int], alpha: float, stop_support: float) -> dict:
    """Patient rule induction (peeling only, no pasting). Returns the peeling trajectory (a list of nested boxes); `select_box` chooses one on held-aside data."""
    n = len(y)
    inbox = np.ones(n, bool)
    lo, hi = {}, {}
    traj = [dict(lo=dict(lo), hi=dict(hi), support=1.0, density=float(y.mean()))]
    done_bin = set()
    while inbox.sum() > stop_support * n:
        best = None
        for j in cols:
            col = X[:, j]
            if names[j] in BINARY:
                if j in done_bin:
                    continue
                for v in (0.0, 1.0):
                    keep = inbox & (col == v)
                    if keep.sum() < stop_support * n or keep.sum() == inbox.sum():
                        continue
                    cand = (float(y[keep].mean()), j, "bin", v, keep)
                    if best is None or cand[0] > best[0]:
                        best = cand
            else:
                xj = col[inbox]
                for side in ("lo", "hi"):
                    q = float(np.quantile(xj, alpha if side == "lo" else 1 - alpha))
                    keep = inbox & ((col >= q) if side == "lo" else (col <= q))
                    if keep.sum() < stop_support * n or keep.sum() == inbox.sum():
                        continue
                    cand = (float(y[keep].mean()), j, side, q, keep)
                    if best is None or cand[0] > best[0]:
                        best = cand
        if best is None:
            break
        _, j, kind, val, keep = best
        nm = names[j]
        if kind == "bin":
            lo[nm] = hi[nm] = val
            done_bin.add(j)
        elif kind == "lo":
            lo[nm] = max(lo.get(nm, -np.inf), val)
        else:
            hi[nm] = min(hi.get(nm, np.inf), val)
        inbox = keep
        traj.append(dict(lo=dict(lo), hi=dict(hi), support=float(inbox.mean()), density=float(y[inbox].mean())))
    return dict(trajectory=traj)


def select_box(traj: list, Xv: np.ndarray, yv: np.ndarray, names, select_support: float, tol: float = 0.01) -> dict:
    """Choose a box from a peeling trajectory using data the peeling never saw: highest validation density among boxes with validation support >= select_support,
    then the simplest (fewest restricted features) box within `tol` of that density. Guards against PRIM's habit of peeling noise once the real signal is used up."""
    scored = []
    for t in traj:
        m = in_box(Xv, names, t)
        sup = float(m.mean())
        if sup >= select_support and m.any():
            scored.append((float(yv[m].mean()), sup, t))
    if not scored:
        return dict(box=traj[0], val_support=1.0, val_density=float(yv.mean()), n_restricted=0)
    best = max(d for d, _, _ in scored)
    d, sup, t = min(((d, sup, t) for d, sup, t in scored if d >= best - tol), key=lambda x: (len(set(x[2]["lo"]) | set(x[2]["hi"])), -x[1]))
    return dict(box=t, val_support=sup, val_density=d, n_restricted=len(set(t["lo"]) | set(t["hi"])))


def in_box(X: np.ndarray, names, box: dict) -> np.ndarray:
    m = np.ones(len(X), bool)
    for nm, v in box["lo"].items():
        m &= X[:, names.index(nm)] >= v - 1e-12
    for nm, v in box["hi"].items():
        m &= X[:, names.index(nm)] <= v + 1e-12
    return m


def box_text(box: dict) -> str:
    keys = sorted(set(box["lo"]) | set(box["hi"]))
    parts_ = []
    for k in keys:
        a, b = box["lo"].get(k, -np.inf), box["hi"].get(k, np.inf)
        if k in BINARY and a == b:
            parts_.append(f"{k} = {a:g}")
        elif np.isinf(a):
            parts_.append(f"{k} <= {b:.3g}")
        elif np.isinf(b):
            parts_.append(f"{k} >= {a:.3g}")
        else:
            parts_.append(f"{a:.3g} <= {k} <= {b:.3g}")
    return "; ".join(parts_) or "(whole family)"


# ------------------------------------------------------------------------------------------------ cluster bootstrap on plants
def _per_plant(pid: np.ndarray, num: np.ndarray, den: np.ndarray):
    n = pid.max() + 1
    return np.bincount(pid, weights=num, minlength=n), np.bincount(pid, weights=den, minlength=n)


def boot_ci(pid: np.ndarray, pairs: list[tuple], B: int, seed: int = 0) -> tuple[float, float, float]:
    """pairs = [(num, den, sign), ...]: statistic = sum(sign * sum(w*num) / sum(w*den)) with plant resampling weights w. Returns (estimate, lo, hi)."""
    n = pid.max() + 1
    sums = [(*_per_plant(pid, num, den), s) for num, den, s in pairs]

    def stat(w):
        return sum(s * (w @ a) / max(w @ b, 1e-12) for a, b, s in sums)
    est = stat(np.ones(n))
    rng = np.random.default_rng(seed)
    bs = np.array([stat(rng.multinomial(n, np.full(n, 1.0 / n)).astype(float)) for _ in range(B)])
    return float(est), float(np.quantile(bs, 0.025)), float(np.quantile(bs, 0.975))


def arr(res: list) -> dict:
    single = np.array([len(r.truth) == 1 for r in res], float)
    return dict(wc=np.array([r.wrong_conf for r in res], float), correct=np.array([r.correct for r in res], float) * single, single=single,
                conf=np.array([r.reason == "confident" for r in res], float), minutes=np.array([r.minutes for r in res], float))


# ------------------------------------------------------------------------------------------------ the run
def _ms(res):
    m = S.metrics(res)
    return {k: m[k] for k in ("n_single", "n_pair", "top1", "top3_marginal", "pair_hit", "wrong_conf", "confident", "acc_when_confident", "checks", "minutes", "ece")}


def run_all(out: Path, quick: bool = False) -> dict:
    cfg = ADV_CONFIG
    seed0 = cfg["SEED"]
    if quick:
        n_pl, n_tr, n_he, n_e2, fit_n, perms, boot = 40, 2, 1, 1, 60, 20, 50
    else:
        n_pl, n_tr, n_he, n_e2, fit_n, perms, boot = cfg["N_PLANTS"], cfg["TRAIN_WORLDS"], cfg["HELD_WORLDS"], cfg["EXT2_WORLDS"], cfg["FIT"]["n_plants"], cfg["PERM"], cfg["PRIM"]["boot"]
    out.mkdir(parents=True, exist_ok=True)
    CONF = dict(S.CONFIGS)
    lk_m = fit(build_world(n_theta=S.N_FIT, seed=S.SEED_FIT))
    M.NOISE["scale"] = cfg["FIT"]["noise"]
    try:
        lk_r = fit(family_world(cfg["EXT_FACTOR"], seed0 + 1, n=fit_n, latent_p=cfg["FIT"]["latent_p"]))
    finally:
        M.NOISE["scale"] = 1.0
    engines = {"A_plain": (lk_m, CONF["A_plain"]), "B_robust": (lk_m, CONF["B_robust"]), "R_A": (lk_r, CONF["A_plain"]), "R_B": (lk_r, CONF["B_robust"])}

    def world_set(factor, base, count):
        cases, health = [], []
        for k in range(count):
            w = family_world(factor, seed0 + base + k, n=n_pl)
            cs = family_cases(w, k, seed0 + base + 500 + k)
            hc, _ = _plant_flags(w)
            health.append(dict(world=k, healthy_complaint=float(np.mean(hc)),
                               nonconverged=sum(1 for c in w.ctx_h for s in [c.idle_on, c.peak_on, c.peak_off, *c.idle_off] if s is not None and not s.converged),
                               min_gated=min(int(w.cause_gated[c].sum()) for c in w.cause_gated)))
            cases += cs
            del w
        return cases, health

    def run_variants(cases, names, seed, garbage_lk=lk_m):
        return {v: evaluate_family(engines[v][0], cases, engines[v][1], seed, garbage_lk) for v in names}

    # ---- search set: where does the plain engine fail?
    train, train_health = world_set(cfg["EXT_FACTOR"], 100, n_tr)
    tr = run_variants(train, ("A_plain", "B_robust"), seed0 + 2000)
    Xt, pid_t = feature_matrix(train), plant_ids(train)
    yA = arr(tr["A_plain"])["wc"]
    miss = 1.0 - arr(tr["A_plain"])["correct"]
    prof_wc = profile(Xt, yA, pid_t, perms=perms, seed=seed0 + 7)
    prof_top1 = profile(Xt, np.where(arr(tr["A_plain"])["single"] > 0, miss, 0.0), pid_t, perms=perms, seed=seed0 + 8)
    P = cfg["PRIM"]
    names = list(ALL_FEATS)
    idx_of = {n: i for i, n in enumerate(names)}
    sets = {"all": list(range(len(names))),
            "plant_only": [idx_of[n] for n in PLANT_FEATS],
            "arrival_only": [idx_of[n] for n in cfg["ARRIVAL"]]}
    n_peel = max(1, int(round(n_tr * P["peel_frac"])))                       # search worlds used to peel; the rest select the box (never the held-out family)
    pm = np.array([c.world < n_peel for c in train])
    val_rate = float(yA[~pm].mean())
    prims = {}
    for k, cols in sets.items():
        tr_ = prim(Xt[pm], yA[pm], names, cols, P["alpha"], P["stop_support"])
        prims[k] = select_box(tr_["trajectory"], Xt[~pm], yA[~pm], names, P["select_support"], P["simplicity_tol"])

    # ---- held-out family, extrapolation family
    held, held_health = world_set(cfg["EXT_FACTOR"], 200, n_he)
    ext2, ext2_health = world_set(cfg["EXT2_FACTOR"], 300, n_e2)
    Xh, pid_h = feature_matrix(held), plant_ids(held)
    Xe, pid_e = feature_matrix(ext2), plant_ids(ext2)
    guard_box = prims["arrival_only"]["box"]
    guard_active = prims["arrival_only"]["val_density"] >= cfg["BAR"]["guard_min_ratio"] * val_rate

    def with_guard(res, X):
        m = in_box(X, names, guard_box) if guard_active else np.zeros(len(X), bool)
        res = dict(res)
        res["G_guard"] = [rb if g else ra for ra, rb, g in zip(res["A_plain"], res["B_robust"], m)]
        return res, m

    hr, g_h = with_guard(run_variants(held, ("A_plain", "B_robust", "R_A", "R_B"), seed0 + 2100), Xh)
    er, g_e = with_guard(run_variants(ext2, ("A_plain", "B_robust", "R_A", "R_B"), seed0 + 2200), Xe)

    # ---- Addendum 3 worlds (out-of-family operational and parametric mismatch), same seeds and cases as the stress test
    h2, h2_res = {}, {}
    for wname in ("matched", "param_shift", "latent_and_noise", "technician_error", "composite_1.00"):
        wi = next(i for i, s in enumerate(S.WORLDS) if s.name == wname)
        spec = S.WORLDS[wi]
        w = S.build_test_world(spec, S.SEED_TEST + wi)
        cs = spec_cases(w, wi, spec, S.SEED_TEST + 1000 + wi)
        res, g = with_guard(run_variants(cs, ("A_plain", "B_robust", "R_A", "R_B"), S.SEED_TEST + 2000 + wi), feature_matrix(cs))
        h2[wname], h2_res[wname] = {v: _ms(r) for v, r in res.items()}, (cs, res)
        del w

    result = dict(quick=quick, hash=frozen_hash(), train_n=len(train), held_n=len(held), ext2_n=len(ext2),
                  health=dict(train=train_health, held=held_health, ext2=ext2_health),
                  base_train={v: _ms(r) for v, r in tr.items()}, profile_wc=prof_wc, profile_top1=prof_top1,
                  prims={k: dict(box=v["box"], text=box_text(v["box"]), restricted=sorted(set(v["box"]["lo"]) | set(v["box"]["hi"])), val_support=v["val_support"], val_density=v["val_density"])
                         for k, v in prims.items()},
                  train_rate=float(yA.mean()), val_rate=val_rate, n_peel_worlds=n_peel, guard_active=bool(guard_active), guard_text=box_text(guard_box))
    # held-out evaluation of each box (all variants) with plant-cluster bootstrap on the plain engine's density
    overall_h = float(arr(hr["A_plain"])["wc"].mean())
    boxes = {}
    for k, v in prims.items():
        m = in_box(Xh, names, v["box"])
        a = arr(hr["A_plain"])
        est, lo_, hi_ = boot_ci(pid_h, [(a["wc"] * m, m.astype(float), 1.0)], boot, seed0 + 11) if m.any() else (float("nan"),) * 3
        boxes[k] = dict(support=float(m.mean()), density={var: float(arr(hr[var])["wc"][m].mean()) if m.any() else float("nan") for var in hr},
                        ci=(lo_, hi_), overall=overall_h, val_density=v["val_density"], val_support=v["val_support"], n_in=int(m.sum()))
    result["boxes_held"] = boxes
    result["held"] = {v: _ms(r) for v, r in hr.items()}
    result["ext2"] = {v: _ms(r) for v, r in er.items()}
    result["h2"] = h2
    result["guard_share_held"] = float(g_h.mean())
    # strata on the held-out family
    hcf = np.array([c.healthy_complaint for c in held])
    result["strata_healthy_complaint"] = {str(flag): {v: _ms([r for r, c in zip(hr[v], held) if c.healthy_complaint == flag]) for v in hr} for flag in (False, True) if (hcf == flag).any()}
    # paired differences with plant-cluster bootstrap
    diffs = {}
    for x, y_ in (("A_plain", "B_robust"), ("R_A", "A_plain"), ("R_B", "B_robust"), ("R_A", "B_robust"), ("G_guard", "A_plain"), ("G_guard", "B_robust")):
        ax, ay = arr(hr[x]), arr(hr[y_])
        one = np.ones(len(held))
        diffs[f"{x} - {y_}"] = dict(wrong_conf=boot_ci(pid_h, [(ax["wc"], one, 1.0), (ay["wc"], one, -1.0)], boot, seed0 + 21),
                                    top1=boot_ci(pid_h, [(ax["correct"], ax["single"], 1.0), (ay["correct"], ay["single"], -1.0)], boot, seed0 + 22),
                                    confident=boot_ci(pid_h, [(ax["conf"], one, 1.0), (ay["conf"], one, -1.0)], boot, seed0 + 23))
    result["diffs_held"] = diffs
    result["scorecard"] = scorecard(result)
    write(out, result)
    return result


# ------------------------------------------------------------------------------------------------ scorecard (rules frozen in PREREGISTRATION.md Addendum 6)
def _passes(res: dict, x: str) -> tuple[bool, list[str]]:
    B = ADV_CONFIG["BAR"]
    h, h2 = res["held"], res["h2"]
    notes = []
    i = h[x]["wrong_conf"] <= h["B_robust"]["wrong_conf"] + B["wc_slack"]
    ii = h[x]["top1"] >= h["B_robust"]["top1"] + B["top1_gain"] or h[x]["confident"] >= h["B_robust"]["confident"] + B["conf_gain"]
    iii = h2["matched"][x]["top1"] >= h2["matched"]["A_plain"]["top1"] - B["matched_top1_drop"]
    iv = all(h2[w][x]["wrong_conf"] <= h2[w]["B_robust"]["wrong_conf"] + B["wc_slack"] for w in ("composite_1.00", "technician_error"))
    notes.append(f"(i) held-out wrong-conf {h[x]['wrong_conf']:.3f} <= B {h['B_robust']['wrong_conf']:.3f} + {B['wc_slack']}: {i}")
    notes.append(f"(ii) top-1 {h[x]['top1']:.3f} vs B {h['B_robust']['top1']:.3f} (+{B['top1_gain']}) or confident {h[x]['confident']:.2f} vs {h['B_robust']['confident']:.2f} (+{B['conf_gain']}): {ii}")
    notes.append(f"(iii) matched top-1 {h2['matched'][x]['top1']:.3f} >= A {h2['matched']['A_plain']['top1']:.3f} - {B['matched_top1_drop']}: {iii}")
    notes.append("(iv) composite and technician_error wrong-conf <= B + %.2f: %s (%s)" % (B["wc_slack"], iv, ", ".join(f"{w} {h2[w][x]['wrong_conf']:.3f} vs {h2[w]['B_robust']['wrong_conf']:.3f}" for w in ("composite_1.00", "technician_error"))))
    return bool(i and ii and iii and iv), notes


def scorecard(res: dict) -> list[tuple[str, bool, str]]:
    B, P = ADV_CONFIG["BAR"], ADV_CONFIG["PRIM"]
    h, h2, e2 = res["held"], res["h2"], res["ext2"]
    out = []
    pb = res["boxes_held"]["plant_only"]
    pr1 = res["prims"]["plant_only"]
    tr_ratio = pr1["val_density"] / max(res["val_rate"], 1e-9)
    ho_ratio = pb["density"]["A_plain"] / max(pb["overall"], 1e-9)
    ok1 = tr_ratio >= P["min_ratio"] and pr1["val_support"] >= P["select_support"] and ho_ratio >= P["confirm_ratio"] and pb["ci"][0] > pb["overall"]
    out.append(("P1", ok1, f"plant-parameter box ({len(pr1['restricted'])} features): validation density {pr1['val_density']:.3f} = {tr_ratio:.1f}x validation overall {res['val_rate']:.3f} (>= {P['min_ratio']}x) at support "
                           f"{pr1['val_support']:.2f} (>= {P['select_support']}); held-out density {pb['density']['A_plain']:.3f} = {ho_ratio:.1f}x overall {pb['overall']:.3f} "
                           f"(>= {P['confirm_ratio']}x), 95% CI lower {pb['ci'][0]:.3f} > overall"))
    pl = [r for r in res["profile_wc"] if r["feature"] in PLANT_FEATS]
    top5 = [r["feature"] for r in pl[:5]]
    n_add5 = sum(1 for f in top5 if f in ADV_CONFIG["ADD5"])
    out.append(("P2", "p_cold" in top5 and n_add5 >= 3, f"top 5 plant parameters by wrong-conf profile: {', '.join(top5)}; {n_add5} of 5 flagged in Addendum 5 (>= 3); p_cold in top 5: {'p_cold' in top5}"))
    out.append(("P3", h["A_plain"]["top1"] <= B["family_top1_max"] and h["A_plain"]["wrong_conf"] >= B["family_wc_min"],
                f"held-out family, engine A: top-1 {h['A_plain']['top1']:.3f} (<= {B['family_top1_max']}), wrong-conf {h['A_plain']['wrong_conf']:.3f} (>= {B['family_wc_min']}); matched was 0.764 / 0.027"))
    out.append(("P4", h["R_A"]["wrong_conf"] <= (1 - B["refit_wc_cut"]) * h["A_plain"]["wrong_conf"] and h["R_A"]["top1"] >= h["A_plain"]["top1"] - B["refit_top1_slack"],
                f"family-trained R_A vs A on held-out: wrong-conf {h['R_A']['wrong_conf']:.3f} vs {h['A_plain']['wrong_conf']:.3f} (needs <= {(1 - B['refit_wc_cut']):.2f}x); top-1 {h['R_A']['top1']:.3f} vs {h['A_plain']['top1']:.3f} (not lower by more than {B['refit_top1_slack']})"))
    verdicts = {x: _passes(res, x) for x in ("R_A", "R_B", "G_guard")}
    passing = [x for x, (ok, _) in verdicts.items() if ok]
    rec = min(passing, key=lambda x: h[x]["wrong_conf"]) if passing else "B_robust"
    out.append(("P5", bool(passing), "improvement over B_robust under the frozen rule (i)-(iv): " + (", ".join(passing) if passing else "none passes") + " | " +
                " || ".join(f"{x}: " + "; ".join(n) for x, (_, n) in verdicts.items())))
    a, b, g = h["A_plain"]["wrong_conf"], h["B_robust"]["wrong_conf"], h["G_guard"]["wrong_conf"]
    okg = res["guard_active"] and a > b and (a - g) >= B["recover_frac"] * (a - b)
    out.append(("P6", bool(okg), f"guard (active: {res['guard_active']}; in {res['guard_share_held'] * 100:.0f}% of held-out visits): wrong-conf A {a:.3f}, B {b:.3f}, G {g:.3f}; G recovers {(a - g) / max(a - b, 1e-9) * 100:.0f}% of B's reduction (needs >= {B['recover_frac'] * 100:.0f}%)"))
    ok7 = all(h2[w]["R_B"]["wrong_conf"] <= h2[w]["B_robust"]["wrong_conf"] + B["wc_slack"] for w in ("composite_1.00", "technician_error"))
    out.append(("P7", ok7, "R_B vs B wrong-conf in Addendum 3 worlds: " + ", ".join(f"{w} {h2[w]['R_B']['wrong_conf']:.3f} vs {h2[w]['B_robust']['wrong_conf']:.3f}" for w in ("composite_1.00", "technician_error")) + f" (R_B <= B + {B['wc_slack']})"))
    m = h2["matched"]
    out.append(("P8", m["R_A"]["top1"] >= m["A_plain"]["top1"] - B["matched_top1_drop"] and m["R_A"]["wrong_conf"] <= B["matched_wc_max"],
                f"matched world, R_A vs A: top-1 {m['R_A']['top1']:.3f} vs {m['A_plain']['top1']:.3f} (not lower by more than {B['matched_top1_drop']}); wrong-conf {m['R_A']['wrong_conf']:.3f} (<= {B['matched_wc_max']})"))
    out.append(("P9", e2["R_A"]["wrong_conf"] <= e2["A_plain"]["wrong_conf"], f"extrapolation family (a full span beyond): wrong-conf R_A {e2['R_A']['wrong_conf']:.3f} vs A {e2['A_plain']['wrong_conf']:.3f}"))
    out.append(("RECOMMENDED", rec != "B_robust", f"frozen decision rule recommends {rec}"))
    return out


# ------------------------------------------------------------------------------------------------ report
def write(out: Path, res: dict) -> None:
    (out / "adversary.json").write_text(json.dumps(dict(disclaimer=DISCLAIMER, **{k: v for k, v in res.items()}), indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else float(o)) + "\n")
    with open(out / "adversary_variants.csv", "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["# " + DISCLAIMER])
        cols = ["set", "variant", "n_single", "n_pair", "top1", "top3_marginal", "pair_hit", "wrong_conf", "confident", "acc_when_confident", "checks", "minutes", "ece"]
        wr.writerow(cols)
        for setname, d in [("held_family", res["held"]), ("ext2_family", res["ext2"])] + [(f"A3:{w}", d) for w, d in res["h2"].items()]:
            for v, m in d.items():
                wr.writerow([setname, v] + [f"{m[c]:.4f}" if isinstance(m[c], float) else m[c] for c in cols[2:]])
    L = ["# Adversarial search for failure regions (simulation only)", "", f"**{DISCLAIMER}**", "",
         "The adversary can only find failures *inside this simulator's structure* (one plant archetype, steady state). It cannot find structural mismatch, so every number here is a bound on a small, simulated family, not on buildings.", ""]
    if res.get("quick"):
        L += ["**QUICK SMOKE RUN: tiny sizes, numbers are not results.**", ""]
    L += [f"Frozen hash `{res['hash']}`. Cases: search {res['train_n']}, held-out {res['held_n']}, extrapolation {res['ext2_n']}.", "", "## Scorecard (rules and predictions frozen before the run)", "", "| | holds | evidence |", "|---|---|---|"]
    for k, ok, ev in res["scorecard"]:
        L.append(f"| {k} | {'yes' if ok else 'NO'} | {ev} |")
    hl = res["health"]
    L += ["", "## Family health", "", "| set | healthy plants already complaining | non-converged solves | fewest symptomatic plants for any cause |", "|---|---|---|---|"]
    for nm, hh in hl.items():
        L.append(f"| {nm} | {np.mean([x['healthy_complaint'] for x in hh]) * 100:.0f}% | {sum(x['nonconverged'] for x in hh)} | {min(x['min_gated'] for x in hh)} |")
    L += ["", "Plants that already complain when healthy are a structural trap (the complaint has a cause the engine does not model); results are split by that flag below.", "",
          "## Engine on the broad family vs the earlier worlds", "", "| set | variant | top-1 | pair hit | wrong-conf | confident | acc when confident | checks | minutes | ECE |", "|---|---|---|---|---|---|---|---|---|---|"]

    def row(setname, v, m):
        return f"| {setname} | {v} | {m['top1']:.3f} | {m['pair_hit']:.2f} | {m['wrong_conf']:.3f} | {m['confident']:.2f} | {m['acc_when_confident']:.2f} | {m['checks']:.1f} | {m['minutes']:.0f} | {m['ece']:.3f} |"
    for v in ADV_CONFIG["VARIANTS"]:
        L.append(row("held-out broad family", v, res["held"][v]))
    for v in ADV_CONFIG["VARIANTS"]:
        L.append(row("extrapolation (full span)", v, res["ext2"][v]))
    for w, d in res["h2"].items():
        for v in ADV_CONFIG["VARIANTS"]:
            L.append(row(f"Addendum 3: {w}", v, d[v]))
    L += ["", "Search-set (train) rates of the plain engine A and B: " + "; ".join(f"{v}: top-1 {m['top1']:.3f}, wrong-conf {m['wrong_conf']:.3f}" for v, m in res["base_train"].items()), "",
          "## Paired differences on the held-out family (95% interval from resampling whole plants)", "", "| comparison | d wrong-conf | d top-1 | d confident |", "|---|---|---|---|"]
    for k, d in res["diffs_held"].items():
        f = lambda t: f"{t[0]:+.3f} [{t[1]:+.3f}, {t[2]:+.3f}]"
        L.append(f"| {k} | {f(d['wrong_conf'])} | {f(d['top1'])} | {f(d['confident'])} |")
    L += ["", "## Held-out family split by whether the healthy plant already complains", "", "| healthy plant complains | variant | top-1 | wrong-conf | confident |", "|---|---|---|---|---|"]
    for flag, d in res["strata_healthy_complaint"].items():
        for v, m in d.items():
            L.append(f"| {flag} | {v} | {m['top1']:.3f} | {m['wrong_conf']:.3f} | {m['confident']:.2f} |")
    L += ["", "## Where the plain engine fails (search set; target = confident and wrong)", "", f"Overall rate {res['train_rate']:.3f} (peeling worlds: {res['n_peel_worlds']} of the search worlds; the rest validate the box; validation overall rate {res['val_rate']:.3f}). Failure rate by quantile bin (low to high), ranked by a max-T permutation test "
          f"(threshold t = {res['profile_wc'][0]['thr']:.1f}).", "", "| rank | feature | t | spread | rate by bin (low -> high) | matters |", "|---|---|---|---|---|---|"]
    for i, r in enumerate(res["profile_wc"], 1):
        L.append(f"| {i} | {r['feature']} | {r['t']:.1f} | {r['spread']:.3f} | {', '.join('-' if x != x else f'{x:.3f}' for x in r['rates'])} | {'YES' if r['matters'] else 'no'} |")
    L += ["", "## Failure boxes (PRIM peeling on the search set; evaluated on the held-out family)", "", "| feature set | box | validation support | validation density | held-out support | held-out density A | 95% CI (A) | B | R_A | R_B | G |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, bx in res["boxes_held"].items():
        d = bx["density"]
        L.append(f"| {k} | {res['prims'][k]['text']} | {bx['val_support']:.2f} | {bx['val_density']:.3f} | {bx['support']:.2f} | {d['A_plain']:.3f} | [{bx['ci'][0]:.3f}, {bx['ci'][1]:.3f}] | {d['B_robust']:.3f} | {d['R_A']:.3f} | {d['R_B']:.3f} | {d['G_guard']:.3f} |")
    L += ["", f"Guard (arrival-only box) active: {res['guard_active']}; rule: {res['guard_text']}.", "",
          "Limits: the family is analyst-chosen; the adversary searches only the simulator's own parameters and per-visit trouble; candidate fixes were tuned on nothing but the search set; "
          "R is trained on the family it is then tested on in-family, so the Addendum 3 worlds and the extrapolation family are the generalisation checks."]
    (out / "ADVERSARY_REPORT.md").write_text("\n".join(L) + "\n")
