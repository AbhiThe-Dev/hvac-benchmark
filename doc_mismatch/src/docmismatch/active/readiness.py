"""Readiness pipeline: nested fitting, episode running, decision layers, frozen configuration, sealed-data guards.

One code path serves every evaluation (dev nested, rehearsal, sealed):

    run_fold(kind, train_units, test)      test = a held-out DEV unit, or a whole sealed pool
        1. likelihood + tempering beta fitted on `train_units` only                      (outer fit)
        2. verification episodes on the test set, all policies, never-stopped runs        (outer records)
        3. for every training unit h: likelihood refitted on train_units \\ {h}, episodes on h (inner records; beta borrowed from step 1,
           a parameter chosen from training units only)
        4. one decision layer per policy fitted on the inner records of that policy ONLY; applied to the outer records.
    Nothing in 3/4 sees the test set. `fold_plan` returns the (train, test) sets so tests can assert this.

Kinds: "real" (units = seasons of the 30-day DEV pool) and "sim" (units = topologies). Adding simulated topologies is a config change
(`sim_topologies()` reads results/docmismatch/active/sim_manifest.json when present).
Layers: "none" (plain stopping rule), "legacy" (abstain.py slot/season-level rule + nested target selection = the previous system),
"new" (reliability.py case-level layer).
"""
from __future__ import annotations

import datetime
import hashlib
import json
import multiprocessing as mp
import os
import pickle
import sys
from pathlib import Path

import numpy as np

from . import selection as SEL
from .abstain import (CONFIRMED as A_CONF, REFUTED as A_REF, AbstentionRule, nested_select)
from .calibrate import calibrate_beta, calibrate_beta_seasons
from .engine import Episode, run_episode
from .model import fit_slot_models
from .pools import SEASON_OF_WINDOW, load_or_build_sim
from .reliability import (CAP, FI, FLAGGED, CONFIRMED, REFUTED, ReliabilityLayer, Support, features_at, first_cross)

ROOT = Path(__file__).resolve().parents[3]                      # doc_mismatch/
RES = ROOT.parent / "results" / "docmismatch"
ACT = RES / "active"
FROZEN = ACT / "frozen"
LEDGER = ACT / "sealed_access.log"
CACHE = ACT / "readiness_cache"
SEASON_NAME = {0: "fall", 1: "spring", 2: "summer", 3: "winter"}
BASE_TOPOS = ["sys03_psz_ac", "sys07_vav_reheat", "vav_2ahu_2loops", "vav_3ahu_2loops"]
MAIN_POLICIES = ("active", "random", "traversal", "traversal_block", "frozen")

DEFAULT_CFG = dict(
    variant="sel_slice", ctx="oat", tau=0.95, nmax=24, seed=2026, policies=list(MAIN_POLICIES), calibrate_beta=True, sim_reps=[0, 1],
    sim_settings=["visit", "hist"], sim_primary="visit", real_episode_seed=2026, real_n_wrong=30, real_n_right=10,
    layer=dict(nominal=0.95, q=0.10, lb_floor=0.90, lam=3.0, min_clusters=6, slot_min_clusters=6, per_slot=True, features=None, use_slot_power=True),
    boot=2000, resolvable_conf=0.95,
)


def h32(s: str) -> int:
    return int(hashlib.sha1(s.encode()).hexdigest()[:8], 16)


# ---------------------------------------------------------------------------------------------- manifest / sealed guards
def sim_manifest() -> dict:
    """{dev: [topology ids], sealed: [ids]}. Reads results/docmismatch/active/sim_manifest.json when present (tolerant of its layout), else the 4 base topologies."""
    dev, sealed = list(BASE_TOPOS), []
    f = ACT / "sim_manifest.json"
    if not f.exists():
        return dict(dev=dev, sealed=sealed, source="default")
    m = json.loads(f.read_text())
    if isinstance(m, dict) and isinstance(m.get("dev_topologies"), list) and isinstance(m.get("sealed_topologies"), list):
        return dict(dev=list(dict.fromkeys(BASE_TOPOS + [t for t in m["dev_topologies"] if isinstance(t, str)])),
                    sealed=[t for t in m["sealed_topologies"] if isinstance(t, str)], source=str(f))
    d2, s2 = [], []

    def visit(x, role=None):
        if isinstance(x, dict):
            tid = x.get("topology_id") or x.get("id") or x.get("name")
            r = x.get("role") or x.get("split") or x.get("set") or role
            if tid and isinstance(tid, str) and r in ("dev", "sealed", "seal", "development"):
                (s2 if r in ("sealed", "seal") else d2).append(tid)
                return
            for k, v in x.items():
                if k in ("dev", "development", "dev_topologies") and isinstance(v, (list, dict)):
                    for it in (v if isinstance(v, list) else v.keys()):
                        (d2 if isinstance(it, str) else d2).append(it if isinstance(it, str) else (it.get("topology_id") or it.get("id")))
                elif k in ("sealed", "seal", "sealed_topologies") and isinstance(v, (list, dict)):
                    for it in (v if isinstance(v, list) else v.keys()):
                        s2.append(it if isinstance(it, str) else (it.get("topology_id") or it.get("id")))
                else:
                    visit(v, role)
        elif isinstance(x, list):
            for it in x:
                visit(it, role)
    visit(m)
    d2 = [t for t in dict.fromkeys(d2) if t]
    s2 = [t for t in dict.fromkeys(s2) if t]
    return dict(dev=list(dict.fromkeys(BASE_TOPOS + d2)), sealed=s2, source=str(f))


def sim_case_files(role: str) -> list[Path]:
    names = {"dev": ["cases.jsonl", "cases_dev_extra.jsonl"], "sealed": ["cases_sealed_sim.jsonl"]}[role]
    out = []
    for n in names:
        for d in (RES, ACT):
            if (d / n).exists():
                out.append(d / n)
                break
    return out


def code_manifest() -> dict:
    files = sorted((ROOT / "src" / "docmismatch" / "active").glob("*.py"))
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def frozen_check() -> dict:
    """Refuse to continue unless the frozen config and code hashes on disk match the current source tree. Returns the frozen config."""
    cf, mf = FROZEN / "config.json", FROZEN / "manifest.json"
    if not cf.exists() or not mf.exists():
        raise SystemExit("REFUSED: no frozen configuration (run scripts/20_final_eval.py --freeze first)")
    man = json.loads(mf.read_text())
    cur = code_manifest()
    bad = [k for k in sorted(set(cur) | set(man["code"])) if cur.get(k) != man["code"].get(k)]
    if bad:
        raise SystemExit(f"REFUSED: source differs from the frozen manifest: {bad}")
    if hashlib.sha256(cf.read_bytes()).hexdigest() != man["config_sha256"]:
        raise SystemExit("REFUSED: frozen config.json differs from the manifest")
    return json.loads(cf.read_text())


def log_sealed_access(reason: str):
    ACT.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, "a") as fh:
        fh.write(f"{datetime.datetime.now(datetime.timezone.utc).isoformat()}\t{Path(sys.argv[0]).name}\t{reason}\n")


def load_sim_sealed(reason: str, tids: list[str] | None = None):
    """Ledgered loader of the sealed simulated topologies (pools for every replicate) + their cases."""
    log_sealed_access("SIM " + reason)
    man = sim_manifest()
    tids = tids or man["sealed"]
    if not tids:
        raise SystemExit("no sealed simulated topologies in the manifest")
    pools = {t: {r: load_or_build_sim(t, r) for r in DEFAULT_CFG["sim_reps"]} for t in tids}
    cases = [json.loads(l) for f in sim_case_files("sealed") for l in open(f)]
    cases = [c for c in cases if c["topology_id"] in tids]
    return pools, cases


# ---------------------------------------------------------------------------------------------- kinds
class Kind:
    name = ""


class RealKind(Kind):
    name = "real"

    def __init__(self, cfg):
        from .real_data import load_real_dev, real_episodes
        self.cfg = cfg
        self.pool = load_real_dev()
        self._eps = {}
        self._real_episodes = real_episodes

    def units(self):
        return sorted(set(int(x) for x in self.pool.season))

    def label(self, u):
        return SEASON_NAME[u]

    def episodes(self, pool, unit=None):
        key = id(pool)
        if key not in self._eps:
            self._eps[key] = self._real_episodes(pool, n_wrong=self.cfg["real_n_wrong"], n_right=self.cfg["real_n_right"], seed=self.cfg["real_episode_seed"])
        eps = self._eps[key]
        if unit is None:
            return eps
        return [e for e in eps if e.meta["season"] == SEASON_NAME[unit]]

    def train(self, units):
        return dict(pool=self.pool, mask=np.isin(self.pool.season, list(units)))

    def support(self, tr):
        return Support.from_ctx(tr["pool"].ctx[tr["mask"]])

    def fit_slot(self, tr, slot, beta):
        m = fit_slot_models([tr["pool"]], slot, self.cfg["ctx"], [tr["mask"]], **SEL.get(self.cfg["variant"])["fitkw"])
        if not m:
            return None, 1.0
        if beta is not None:
            return m, beta
        if not self.cfg["calibrate_beta"]:
            return m, 1.0
        V = SEL.get(self.cfg["variant"])
        return m, calibrate_beta_seasons(tr["pool"], slot, self.cfg["ctx"], tr["mask"], fitkw=V["fitkw"], runkw=V["runkw"])

    def slots(self, tr):
        from .real_pool import REAL_SLOTS
        return list(REAL_SLOTS)

    def settings(self):
        return ["day"]

    def slice_idx(self, e, setting, rep):
        return np.where(e.pool.group == e.meta["day"])[0]

    def cluster(self, e):
        return f"d{e.meta['day']}"

    def meta(self, e, setting, rep):
        from .. import real_frp as _R
        return dict(season=e.meta["season"], family=_R.FAMILY[e.slot], obs=e.meta["obs"], scenario=e.meta.get("scenario", ""))

    def reps(self):
        return [0]

    def primary(self):
        return "day"


class SimKind(Kind):
    name = "sim"

    def __init__(self, cfg, topos=None, pools=None, cases=None):
        self.cfg = cfg
        self.man = sim_manifest()
        self.topos = topos or self.man["dev"]
        self._pools = pools
        self._cases = cases
        self._eps = {}

    def pools(self, t, rep):
        if self._pools is not None:
            return self._pools[t][rep]
        return load_or_build_sim(t, rep)

    def cases(self):
        if self._cases is None:
            self._cases = [json.loads(l) for f in sim_case_files("dev") for l in open(f)]
        return self._cases

    def units(self):
        return list(self.topos)

    def label(self, u):
        return str(u)

    def reps(self):
        return list(self.cfg["sim_reps"])

    def episodes(self, pool_unused, unit):
        """all hard-case + matched-correct episodes of topology `unit`, for every replicate: list of (rep, Episode)"""
        if unit not in self._eps:
            from .nested import build_sim_episodes
            out = []
            for rep in self.reps():
                pools = {t: self.pools(t, rep) for t in self.topos}
                cs = [c for c in self.cases() if c["topology_id"] in pools]
                out += [(rep, e) for e in build_sim_episodes(pools, cs) if e.meta["topo"] == unit]
            self._eps[unit] = out
        return self._eps[unit]

    def train(self, units):
        pools = [self.pools(t, r) for t in units for r in self.reps()]
        return dict(pools=pools, masks=[np.ones(p.n_slices, bool) for p in pools], units=list(units))

    def support(self, tr):
        return Support.from_ctx(np.vstack([p.ctx for p in tr["pools"]]))

    def fit_slot(self, tr, slot, beta):
        V = SEL.get(self.cfg["variant"])
        m = fit_slot_models(tr["pools"], slot, self.cfg["ctx"], tr["masks"], **V["fitkw"])
        if not m:
            return None, 1.0
        if beta is not None:
            return m, beta
        if not self.cfg["calibrate_beta"]:
            return m, 1.0
        return m, calibrate_beta(tr["pools"], slot, self.cfg["ctx"], tr["masks"], fitkw=V["fitkw"], runkw=V["runkw"])

    def slots(self, tr):
        return sorted({s for p in tr["pools"] for s in p.slots})

    def settings(self):
        return list(self.cfg["sim_settings"])

    def slice_idx(self, e, setting, rep):
        if setting == "hist":
            return np.arange(e.pool.n_slices)
        w = (h32(e.ep_id) + 3 * rep) % 8
        return np.where(e.pool.group == w)[0]

    def cluster(self, e):
        return e.group

    def meta(self, e, setting, rep):
        w = (h32(e.ep_id) + 3 * rep) % 8
        return dict(season=("s%d" % SEASON_OF_WINDOW[w]) if setting == "visit" else "all", family=e.meta.get("matched_to", e.meta["family"]), obs=e.meta["obs"], scenario="")

    def primary(self):
        return self.cfg["sim_primary"]


def make_kind(name, cfg, **kw):
    return RealKind(cfg) if name == "real" else SimKind(cfg, **kw)


# ---------------------------------------------------------------------------------------------- tasks
def fold_plan(units: list, outer=None) -> dict:
    """(train, test) sets of one fold: outer fit on `units`; inner runs (train = units \\ {h}, test = h) for every h in units."""
    units = list(units)
    inner = [dict(train=[u for u in units if u != h], test=h) for h in units]
    return dict(outer=dict(train=units, test=outer), inner=inner)


def _iter_eps(kind, test_pool, unit):
    """list of (rep, Episode)"""
    if kind.name == "real":
        return [(0, e) for e in kind.episodes(test_pool, unit)]
    return kind.episodes(None, unit)


def run_records(kind: Kind, cfg: dict, tr: dict, beta: dict | None, eps: list, policies, tag: dict, full=False) -> tuple[list[dict], dict]:
    """Run every (episode, setting, policy) never-stopped and reduce to records with decision-time features. Returns (records, betas used per slot)."""
    V = SEL.get(cfg["variant"])
    support = kind.support(tr)
    fits, betas = {}, {}
    recs = []
    for rep, e in eps:
        if e.slot not in fits:
            fits[e.slot] = kind.fit_slot(tr, e.slot, None if beta is None else beta.get(e.slot))
            betas[e.slot] = fits[e.slot][1]
        mod, b = fits[e.slot]
        if not mod:
            continue
        for setting in kind.settings():
            sl = kind.slice_idx(e, setting, rep)
            meta = kind.meta(e, setting, rep)
            start = len(recs)
            for pol in policies:
                seed = h32(e.ep_id) % 10_000 + rep
                r = run_episode(e, mod, sl, pol, tau=2.0, nmax=cfg["nmax"], seed=seed, beta=b, diag=True, **V["runkw"])
                if r is None:
                    continue
                crossed, n = first_cross(r.traj, cfg["tau"])
                f = features_at(r.diag, n, support)
                say = bool(r.traj[n] >= 0.5)
                rec = dict(policy=pol, setting=setting, rep=rep, ep=e.ep_id, slot=e.slot, wrong=bool(e.is_wrong), cluster=kind.cluster(e), crossed=crossed, n=n,
                           say_correct=say, p_stop=float(r.traj[n]), f=f.astype(np.float32), traj=r.traj.astype(np.float32), n_info=int(r.info_traj[min(n, len(r.info_traj) - 1)]),
                           group=kind.cluster(e), **meta, **tag)
                recs.append(rec)
            if full and setting == kind.primary():
                # full-evidence snapshot (for the analysis-only "resolvable" label): all informative readings in the pool, order-independent posterior
                from .pools import hypotheses
                nall = 3 * len(sl) * len(hypotheses(e.pool.slots[e.slot], e.doc))
                r = run_episode(e, mod, sl, "random", tau=2.0, nmax=nall, seed=1, beta=b, diag=True, **V["runkw"])
                if r is not None:
                    nn_ = min(r.n_read, len(r.diag["post"]) - 1)
                    p = float(r.diag["post"][nn_][0])
                    ff = features_at(r.diag, nn_, support)
                    for rc in recs[start:]:
                        rc["f_full"] = ff.astype(np.float32); rc["p_full"] = p
    return recs, betas


_G = {}


def _beta_task(a):
    kind, cfg = _G["kind"], _G["cfg"]
    tr = kind.train(a["train"])
    out = {}
    for s in kind.slots(tr):
        m, b = kind.fit_slot(tr, s, None)
        if m:
            out[s] = b
    return out


def _run_task(a):
    kind, cfg = _G["kind"], _G["cfg"]
    tr = kind.train(a["train"])
    if a["kind"] == "outer":
        test_pool = a.get("test_pool") if a.get("test_pool") is not None else getattr(kind, "pool", None)
        eps = _iter_eps(kind, test_pool, a["test"]) if a.get("eps") is None else a["eps"]
        recs, _ = run_records(kind, cfg, tr, a["beta"], eps, cfg["policies"], dict(unit=a["test"], role="outer"), full=True)
    else:
        eps = _iter_eps(kind, kind.pool if kind.name == "real" else None, a["test"])
        recs, _ = run_records(kind, cfg, tr, a["beta"], eps, cfg["policies"], dict(unit=a["test"], role="inner", outer=a.get("outer")))
    return recs


def _pmap(fn, jobs, procs):
    if procs > 1 and len(jobs) > 1:
        with mp.get_context("fork").Pool(min(procs, len(jobs))) as P:
            return P.map(fn, jobs, chunksize=1)
    return [fn(j) for j in jobs]


def _cache_key(kind, cfg, extra) -> str:
    src = "".join(hashlib.sha256((ROOT / "src" / "docmismatch" / "active" / f).read_bytes()).hexdigest()
                  for f in ("engine.py", "model.py", "selection.py", "pools.py", "real_data.py", "readiness.py", "calibrate.py", "nested.py"))
    core = {k: cfg[k] for k in ("variant", "ctx", "tau", "nmax", "policies", "calibrate_beta", "sim_reps", "sim_settings", "real_n_wrong", "real_n_right", "real_episode_seed")}
    return hashlib.sha1((src + kind.name + json.dumps(core, sort_keys=True) + json.dumps(extra, sort_keys=True, default=str)).encode()).hexdigest()[:16]


def run_fold_records(kind: Kind, cfg: dict, train_units: list, test_unit=None, test_pool=None, test_eps=None, procs: int = 1, use_cache=True):
    """Outer records on the test set and inner records on the training units (all policies). test_pool/test_eps: a sealed pool and its episodes."""
    _G["kind"], _G["cfg"] = kind, cfg
    key = _cache_key(kind, cfg, dict(train=[str(u) for u in train_units], test=str(test_unit), sealed=test_pool is not None and str(getattr(test_pool, "name", "")) + str(len(test_eps or []))))
    cf = CACHE / f"fold_{kind.name}_{key}.pkl"
    if use_cache and test_pool is None and cf.exists():
        return pickle.loads(cf.read_bytes())
    plan = fold_plan(train_units, test_unit)
    beta = _beta_task(dict(train=plan["outer"]["train"]))
    jobs = [dict(kind="outer", train=plan["outer"]["train"], test=test_unit, beta=beta, test_pool=test_pool, eps=test_eps)]
    jobs += [dict(kind="inner", train=p["train"], test=p["test"], beta=beta, outer=test_unit) for p in plan["inner"]]
    res = _pmap(_run_task, jobs, procs)
    out = dict(outer=res[0], inner=[r for x in res[1:] for r in x], beta=beta, plan=plan)
    if use_cache and test_pool is None:
        CACHE.mkdir(parents=True, exist_ok=True)
        cf.write_bytes(pickle.dumps(out))
    return out


# ---------------------------------------------------------------------------------------------- layers
def _mk_layer(cfg_layer: dict) -> ReliabilityLayer:
    from .reliability import FEATURES
    kw = dict(cfg_layer)
    kw["features"] = tuple(kw["features"]) if kw.get("features") else FEATURES
    return ReliabilityLayer(**kw)


def apply_layers(fold: dict, cfg: dict, layers=("none", "legacy", "new")) -> list[dict]:
    """Decision rows for every (outer record, layer). Each policy/setting has its own layer fitted on its own inner records."""
    rows = []
    inner, outer = fold["inner"], fold["outer"]
    for pol in cfg["policies"]:
        for setting in sorted({r["setting"] for r in outer}):
            io = [r for r in inner if r["policy"] == pol and r["setting"] == setting]
            oo = [r for r in outer if r["policy"] == pol and r["setting"] == setting]
            if not oo:
                continue
            lay = {}
            if "new" in layers:
                lay["new"] = _mk_layer(cfg["layer"]).fit_all(io)
            if "legacy" in layers:
                lay["legacy"] = _legacy_fit(io, cfg)
            for r in oo:
                for name in layers:
                    rows.append(_decide(name, lay.get(name), r, cfg))
    # resolvable labels (analysis only): full-evidence posterior correct AND the ACTIVE policy's layer would answer it with confidence
    return rows


def _legacy_fit(io, cfg):
    recs = [dict(policy="active", inner=r["unit"], traj=r["traj"], slot=r["slot"], wrong=r["wrong"], group=r["cluster"]) for r in io]
    if not recs:
        return None
    sel = nested_select(recs, "active", tau=cfg["tau"])
    return AbstentionRule(tau=cfg["tau"], by_sign=sel["by_sign"], target=sel["target"]).fit(recs)


def _decide(name, layer, r, cfg) -> dict:
    row = dict(layer=name, policy=r["policy"], setting=r["setting"], rep=r["rep"], ep=r["ep"], slot=r["slot"], wrong=r["wrong"], cluster=r["cluster"], season=r["season"],
               family=r["family"], obs=r["obs"], unit=r["unit"], crossed=r["crossed"], n=r["n"], say_correct=r["say_correct"], p_stop=r["p_stop"])
    if name == "none":
        st = (CONFIRMED if r["say_correct"] else REFUTED) if r["crossed"] else FLAGGED
        row.update(state=st, reason="ok" if r["crossed"] else "no verdict within budget", conf=max(r["p_stop"], 1 - r["p_stop"]) if r["crossed"] else np.nan, conf_cal=max(r["p_stop"], 1 - r["p_stop"]))
    elif name == "legacy":
        if layer is None:
            row.update(state=FLAGGED, reason="no training data", conf=np.nan, conf_cal=np.nan)
        else:
            d = layer.decide(r["slot"], r["traj"])
            ans = d.state in (A_CONF, A_REF)
            row.update(state=(CONFIRMED if d.say_correct else REFUTED) if ans else FLAGGED, reason=d.state + ": " + d.reason, conf=max(r["p_stop"], 1 - r["p_stop"]) if ans else np.nan,
                       conf_cal=max(r["p_stop"], 1 - r["p_stop"]))
    else:
        v = layer.decide(r)
        row.update(state=v.state, reason=v.reason, conf=v.conf, conf_cal=layer.calibrated(v.score) if np.isfinite(v.score) else np.nan)
        if "f_full" in r:
            crossed_full = r["p_full"] >= cfg["tau"] or r["p_full"] <= 1 - cfg["tau"]
            fr = dict(crossed=crossed_full, f=r["f_full"], slot=r["slot"], say_correct=r["p_full"] >= 0.5)
            vf = layer.decide(fr)
            row["full_answered"] = vf.state != FLAGGED
            row["full_correct"] = bool((r["p_full"] >= 0.5) == (not r["wrong"]))
    return row


# ---------------------------------------------------------------------------------------------- drivers
def run_nested(kind_name: str, cfg: dict, procs: int = 1, units=None, layers=("none", "legacy", "new"), **kw) -> tuple[list[dict], dict]:
    """Leave-one-unit-out over the DEV units of `kind_name`. Returns (decision rows, info)."""
    kind = make_kind(kind_name, cfg, **kw)
    us = kind.units()
    rows, info = [], {}
    for o in (units or us):
        fold = run_fold_records(kind, cfg, [u for u in us if u != o], test_unit=o, procs=procs)
        rows += apply_layers(fold, cfg, layers)
        info[str(o)] = dict(beta=fold["beta"], n_outer=len(fold["outer"]), n_inner=len(fold["inner"]))
    return rows, info


def run_sealed_real(cfg: dict, procs: int = 1, layers=("none", "legacy", "new"), rehearsal_unit=None):
    """Fit on ALL DEV seasons and score the SEALED real pool once (through the ledgered loader). rehearsal_unit: a DEV season treated as pseudo-sealed instead
    (fit without it; nothing sealed is loaded)."""
    kind = RealKind(cfg)
    if rehearsal_unit is not None:
        us = [u for u in kind.units() if u != rehearsal_unit]
        fold = run_fold_records(kind, cfg, us, test_unit=rehearsal_unit, procs=procs, use_cache=False)
    else:
        from .real_data import load_real_sealed
        sealed = load_real_sealed("20_final_eval real-sealed")
        eps = [(0, e) for e in kind.episodes(sealed)]
        fold = run_fold_records(kind, cfg, kind.units(), test_unit="SEALED", test_pool=sealed, test_eps=eps, procs=procs, use_cache=False)
    return apply_layers(fold, cfg, layers), dict(n_outer=len(fold["outer"]), beta=fold["beta"])


def run_sealed_sim(cfg: dict, procs: int = 1, layers=("none", "legacy", "new"), rehearsal_unit=None):
    man = sim_manifest()
    if rehearsal_unit is not None:
        kind = SimKind(cfg, topos=man["dev"])
        us = [u for u in kind.units() if u != rehearsal_unit]
        fold = run_fold_records(kind, cfg, us, test_unit=rehearsal_unit, procs=procs, use_cache=False)
        return apply_layers(fold, cfg, layers), dict(n_outer=len(fold["outer"]), beta=fold["beta"])
    pools, cases = load_sim_sealed("20_final_eval sim-sealed")
    # sealed pools are reachable ONLY here; dev pools stay in the training kind
    dev = SimKind(cfg, topos=man["dev"])
    allp = {t: {r: dev.pools(t, r) for r in cfg["sim_reps"]} for t in man["dev"]}
    allp.update(pools)
    sealed_kind = SimKind(cfg, topos=man["dev"] + list(pools), pools=allp, cases=cases + dev.cases())
    outer_eps = []
    for t in pools:
        outer_eps += sealed_kind.episodes(None, t)
    fold = run_fold_records(sealed_kind, cfg, man["dev"], test_unit="SEALED", test_pool=object(), test_eps=outer_eps, procs=procs, use_cache=False)
    return apply_layers(fold, cfg, layers), dict(n_outer=len(fold["outer"]), beta=fold["beta"])
