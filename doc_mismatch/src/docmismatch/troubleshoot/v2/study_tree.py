"""Is a strong branching expert decision tree already as good as the adaptive tool, and does the tool's advantage survive realistic conditions? (PREREGISTRATION_DR.md Addendum 43.)

Simulation only; nothing here is evidence about real technicians or buildings, and the world is the tool's own model family (home field for the tool; named in the report).

The same visits, the same answer table (`study_llm.TableOracle`'s rule: an answer is a fixed function of (visit, complaint, check, target), whoever asks and in whatever order), the same check
minutes (the tool's own accountant), the same 12-checks-per-complaint limit and the same scoring are given to: the adaptive tool the CLI runs (`tool_joint`) and its routine
(`tool_ticket_memo2`); four branching expert trees (`tree_E`, my own, written from the guides, in a confirming and a decisive form; `tree_L1`, `tree_L2`, written blind by two independent
expert authors from the check list and the minutes alone, never shown the tool, its numbers or any result); a flat checklist (`fast_parent`); and the no-check guess. The base world is
Addendum 30's 18 cells; the stress worlds change the true cause frequencies, the noise of the control-system reads and of field measurements, the reliability of every check, and the
fit between the tool's model and the world (a jittered or structurally different response table, a cause neither system knows about, a stuck air-handler static sensor, and settings the tool
is given wrongly).
"""

from __future__ import annotations

import json
import os
import zlib
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from .. import model as M
from .. import study as S
from .. import study_rating as SG
from ..v1 import catalogue as K
from ..v1 import causes as C
from ..v1.engine import make_case_v1
from ..v1.study_fast_v1 import break_even
from . import policies as P
from . import study_econ as EC
from . import study_joint as J
from . import study_llm_ext as E
from . import study_rel as REL
from . import tree as TR
from . import world2 as W
from .joint import JointSession, JointSettings
from .study_llm import TableOracle

# ---------------------------------------------------------------------------------------------- frozen constants (Addendum 43)
SEED = 43
N_EPISODES = J.N_EPISODES
BOOT_B = J.BOOT_B
SUBSETS = J.SUBSETS
TIERS = (E.EXT_ARM, "T3", "T2")             # T3-noattr (primary: BAS + point map, no documented attributes), T3 (full data), T2 (no control-system access)
PRIMARY_TIER = E.EXT_ARM
TAU, MIN_RATE = 0.95, 0.02                  # the live tool: tau by default, min_rate = v2/cli.py's LIVE_MIN_RATE_DEFAULT at registration (2026-10-12), frozen here
TOOL, ROUTINE = "tool_joint", "tool_ticket_memo2"
BLIND_TREES = ("tree_E", "tree_Ed", "tree_L1", "tree_L2")      # written without the tool's response table: E by me from the guides, L1 and L2 by blind authors
INFORMED_TREES = ("tree_I1", "tree_I2")                        # Amendment 1: written by authors who were given the tool's whole response table and the service-history base rates
TREES = BLIND_TREES + INFORMED_TREES
REFS = ("fast_parent", "no_check")
ARMS = (TOOL, ROUTINE) + TREES + REFS
FRONTIER = (("tool@mr0.003", TAU, 0.003), ("tool@mr0.01", TAU, 0.01), ("tool@mr0.04", TAU, 0.04), ("tool@mr0.08", TAU, 0.08), ("tool@tau0.90", 0.90, MIN_RATE))
MAT_TIME, MAT_ACC, MAT_SAFE, MAT_ACC_FLOOR, MAT_TIME_CAP = 0.15, 0.05, 0.03, -0.02, 0.05      # the bars for a MATERIAL advantage (registered)
CLOSE_MAX, GAP_MIN = 5, 12                  # of 18 base cells at the primary tier: at most 5 = already close, at least 12 = a material gap
SURVIVE_FRAC, ERODE_FRAC = 2 / 3, 1 / 3     # of the stress worlds
# The value model (Verdict 3; registered, ASSUMPTIONS and not measurements): the minutes-equivalent cost of a visit = its minutes + C_WRONG x (complaints declared and wrong: a return trip, a
# wrong part) + C_UNDECL x (complaints not declared: the technician carries on alone). The registered box is the corners below; the tool is AHEAD if it is cheaper by more than VALUE_MARGIN of
# the tree's cost at every corner, BEHIND if dearer by more than that at every corner, and the answer DEPENDS ON THE COSTS otherwise. DEFAULT_COSTS is only for the single-number tables.
C_WRONG_BOX, C_UNDECL_BOX, VALUE_MARGIN, DEFAULT_COSTS = (60.0, 240.0), (0.0, 60.0), 0.05, (120.0, 30.0)
VALUE_GRID_W, VALUE_GRID_U = (0.0, 30.0, 60.0, 120.0, 240.0, 480.0), (0.0, 15.0, 30.0, 60.0)
TREE_DIR = Path(__file__).resolve().parents[4] / "expert_trees"
ECON = "econ_fault"
TYPE_IDS = tuple(C.BY_ID) + ("wrong", "unlisted", ECON)
TYPE_INDEX = {t: i for i, t in enumerate(TYPE_IDS)}
N_STRESS_BASE = 100                         # stress worlds use event streams [SEED_WORLD, 100 + k, 0, i], clear of Addendum 30's 0-17 and Addendum 37's 18-19

# ---------------------------------------------------------------------------------------------- cause mixes of the WORLD (the tool's prior never changes)
MIXES = {
    "none": {},
    "controls": dict(controller_config=4.0, controller_comms=4.0, signal_fault=4.0, flow_sensor=4.0),
    "mechanical": dict(actuator_fail=4.0, damper_mech=4.0, no_power=4.0),
    "zone_side": dict(zone_sensor_setpoint=4.0, reheat_fail=4.0, duct_diffuser=4.0, capacity_design=4.0),
    "tail": dict(other=8.0, unlisted=8.0, capacity_design=4.0),
    "flat": "flat",
}


def mix_prior(causes: list, p: np.ndarray, mix: str) -> np.ndarray:
    """The world's local-cause probabilities after the mix (renormalised); 'none' returns `p` unchanged."""
    spec = MIXES[mix]
    if not spec:
        return p
    q = np.array(p, float)
    if spec == "flat":
        leaf = [k for k, c in enumerate(causes) if c[0] not in ("wrong", "unlisted") and q[k] > 0]
        total = q[leaf].sum()
        q[leaf] = total / len(leaf)
        return q / q.sum()
    mult = np.array([spec.get(c[0], 1.0) for c in causes])
    q = q * mult
    return q / q.sum()


@dataclass(frozen=True)
class World:
    name: str
    group: str
    f: float = 0.03                    # per-air-handler probability of an upstream fault
    q_ahu: float = 0.0                 # P(a box's true air handler is not its documented one)
    p_wrong: float = 0.05              # P(the documented box of a room is wrong)
    rel_a: float = 0.0                 # every response probability moved this far toward 0.5 (Addendum 30's R1 = 0.25)
    mix: str = "none"
    bas_noise: float = 0.0             # the control-system reads only, moved this far toward 0.5
    field_noise: float = 0.0           # every other check (at the box, the air handler, the room, v0's act-and-watch), moved this far toward 0.5
    sharpen: float = 0.0               # every response probability moved this far toward certainty (Addendum 42's b)
    fa_mult: float = 1.0               # every false-alarm rate multiplied by this (capped at 0.5)
    hit_keep: float = 1.0              # every hit rate pulled toward its false-alarm rate: p -> bg + hit_keep (p - bg)
    jitter: float = 0.0                # logit-normal noise (sigma) on every response probability, fixed per (check, cause) for the whole world
    struct: float = 0.0                # P(a (check, cause) pair behaves unlike the tool's table: a strong signature is lost, an unseen cause fires 0.4)
    table_seed: int = 0
    static_stuck: float = 0.0          # P(an air handler's control-system static sensor is stuck at normal in a visit)
    econ: bool = False                 # a cause neither system knows about: an economizer fault (Addendum 37's world)
    tool_f: float | None = None        # the tool's own assumption of f (None = JointSettings' 0.03)
    tool_drawings: str = "mostly_right"

    def params(self) -> W.WorldParams:
        if self.econ:
            return W.WorldParams(self.f, self.q_ahu, self.p_wrong, self.rel_a, extra_states=(ECON,), extra_share={ECON: EC.ECON_F_SHARE}, extra_affect={ECON: EC.ECON_R_AFFECT})
        return W.WorldParams(self.f, self.q_ahu, self.p_wrong, self.rel_a)

    @property
    def neutral(self) -> bool:
        return all(getattr(self, k) == getattr(World("", ""), k) for k in ("mix", "bas_noise", "field_noise", "sharpen", "fa_mult", "hit_keep", "jitter", "struct", "static_stuck", "econ", "tool_f",
                                                                          "tool_drawings"))


def base_worlds() -> list[tuple[int, World]]:
    """Addendum 30's 18 cells as worlds, on the SAME event streams (stream index = the cell's index)."""
    out = []
    for idx, c in enumerate(J.all_cells()):
        q, pw = J.MAP_OF[c.map]
        out.append((idx, World(f"{c.shared}/{c.map}/{c.rel}", "base", f=J.F_OF[c.shared], q_ahu=q, p_wrong=pw, rel_a=J.REL_A[c.rel])))
    return out


def stress_worlds() -> list[tuple[int, World]]:
    """The registered stress worlds, one factor at a time from Addendum 30's primary cell (f = 0.03, M0, R0), plus one combined world. Each has its own event stream."""
    ws = [
        World("freq: controls-heavy", "frequency", mix="controls"),
        World("freq: mechanical-heavy", "frequency", mix="mechanical"),
        World("freq: zone-side-heavy", "frequency", mix="zone_side"),
        World("freq: flat (every cause equally likely)", "frequency", mix="flat"),
        World("freq: rare causes heavy", "frequency", mix="tail"),
        World("freq: drawings poor (30% of boxes wrong)", "frequency", p_wrong=0.30),
        World("noise: control-system reads 0.3", "noise", bas_noise=0.3),
        World("noise: control-system reads 0.6", "noise", bas_noise=0.6),
        World("noise: field measurements 0.3", "noise", field_noise=0.3),
        World("noise: AHU static sensor stuck in 25% of visits", "noise", static_stuck=0.25),
        World("reliability: every check 0.5 toward a coin flip", "reliability", rel_a=0.5),
        World("reliability: false alarms x3", "reliability", fa_mult=3.0),
        World("reliability: hits 40% weaker", "reliability", hit_keep=0.6),
        World("reliability: checks sharper than assumed (0.5)", "reliability", sharpen=0.5),
        World("reliability: every check deterministic (ceiling)", "reliability", sharpen=1.0),
        World("mismatch: response table jittered, sigma 0.5 (A)", "mismatch", jitter=0.5, table_seed=1),
        World("mismatch: response table jittered, sigma 0.5 (B)", "mismatch", jitter=0.5, table_seed=2),
        World("mismatch: response table jittered, sigma 1.0 (A)", "mismatch", jitter=1.0, table_seed=1),
        World("mismatch: response table jittered, sigma 1.0 (B)", "mismatch", jitter=1.0, table_seed=2),
        World("mismatch: 10% of signatures lost or invented (A)", "mismatch", struct=0.10, table_seed=1),
        World("mismatch: 10% of signatures lost or invented (B)", "mismatch", struct=0.10, table_seed=2),
        World("mismatch: an economizer fault neither system knows", "mismatch", f=0.09, econ=True),
        World("tool setting: believes upstream faults are 10x commoner", "tool", tool_f=0.30),
        World("tool setting: believes upstream faults are 10x rarer", "tool", tool_f=0.003),
        World("tool setting: drawings rated poor (world: 5% wrong)", "tool", tool_drawings="poor"),
        World("combined: a bad day", "combined", q_ahu=0.10, p_wrong=0.15, rel_a=0.25, mix="zone_side", bas_noise=0.3, jitter=0.5, table_seed=1),
    ]
    return [(N_STRESS_BASE + k, w) for k, w in enumerate(ws)]


# ---------------------------------------------------------------------------------------------- the world's events
def draw_event_mix(idx: int, i: int, w: World, cases: dict) -> W.Event:
    """`world2.draw_event`, with the world's cause mix applied to each room's local-cause probabilities (and, for an econ world, its extra upstream state). The draws are consumed in the
    same order, so with the neutral mix this returns exactly `world2.draw_event`'s event (gate G4)."""
    wp = w.params()
    extra, shares = ((C.ECON_FAULT,), EC.ECON_SHARES) if w.econ else ((), None)
    if w.mix == "none":
        return W.draw_event(idx, i, wp, cases, extra_causes=extra, shares=shares)
    rng = np.random.default_rng([W.SEED, idx, 0, i])
    states, upstream, r_affect = wp.states, wp.upstream, wp.r_affect()
    sp = wp.state_prior()
    ahus = [W.ahu_id(a) for a in range(W.N_AHU)]
    priors = {}
    for r in range(W.N_BOX):
        cs, pr = W.local_prior(cases[("T2", r)], wp.p_wrong, r, upstream=upstream, extra_causes=extra, shares=shares)
        priors[r] = (cs, mix_prior(cs, pr, w.mix))
    for _ in range(W.MAX_REDRAW):
        u = {a: states[int(rng.choice(len(sp), p=sp))] for a in ahus}
        true_ahu = {}
        for b in range(W.N_BOX):
            doc = ahus[b // W.PER_AHU]
            flip, alt = rng.random() < wp.q_ahu, int(rng.integers(W.N_AHU - 1))
            others = [a for a in ahus if a != doc]
            true_ahu[f"VAV-{b}"] = others[alt] if flip else doc
        rooms, causes, tas = [], [], []
        for r in range(W.N_BOX):
            has_local, ua = rng.random() < W.RHO, rng.random()
            cs, pr = priors[r]
            ci = int(rng.choice(len(cs), p=pr))
            local = cs[ci] if has_local else None
            tb = local[1] if local is not None and local[0] == "wrong" else f"VAV-{r}"
            ta = true_ahu[tb]
            state = u[ta]
            affected = state != "ok" and ua < r_affect[state]
            if has_local or affected:
                rooms.append(r)
                causes.append((state,) if affected else local)
                tas.append(ta)
        if rooms:
            order = rng.permutation(len(rooms))
            return W.Event(idx, i, u, true_ahu, [rooms[k] for k in order], [causes[k] for k in order], [tas[k] for k in order], upstream)
    raise RuntimeError("no event with a complaint after MAX_REDRAW draws")


# ---------------------------------------------------------------------------------------------- the world's answers
def _logit(p: float) -> float:
    p = min(max(p, 1e-4), 1 - 1e-4)
    return float(np.log(p / (1 - p)))


def _sig(x: float) -> float:
    return float(1.0 / (1.0 + np.exp(-x)))


def _u01(seed: int, key: str) -> float:
    return float(np.random.default_rng([SEED, seed, zlib.crc32(key.encode())]).random())


def _z(seed: int, key: str) -> float:
    return float(np.random.default_rng([SEED, seed, zlib.crc32(key.encode()), 7]).standard_normal())


def jitter_check(ck: K.CheckV1, sigma: float, struct: float, seed: int) -> K.CheckV1:
    """The check as the WORLD has it when its response table differs from the tool's: every entry gets logit-normal noise (`sigma`), and (reading checks) each (check, cause) pair is, with
    probability `struct`, structurally different: a signature the tool relies on is lost (hit rate 0.2) or an unseen cause fires (0.4). Deterministic in (seed, check, cause)."""
    if ck.is_reading:
        det = dict(ck.detects)
        if struct > 0:
            for cid in C.BY_ID:
                if _u01(seed, f"struct|{ck.name}|{cid}") < struct:
                    if cid in det and det[cid] > 0.5:
                        det[cid] = 0.2
                    elif cid not in det:
                        det[cid] = 0.4
        if sigma > 0:
            det = {k: _sig(_logit(v) + sigma * _z(seed, f"j|{ck.name}|{k}")) for k, v in det.items()}
            bg = _sig(_logit(ck.bg) + sigma * _z(seed, f"j|{ck.name}|bg"))
        else:
            bg = ck.bg
        return replace(ck, detects=det, bg=bg)
    if sigma > 0:
        v0 = replace(ck.v0, tpr=_sig(_logit(ck.v0.tpr) + sigma * _z(seed, f"j|{ck.name}|tpr")), fpr=_sig(_logit(ck.v0.fpr) + sigma * _z(seed, f"j|{ck.name}|fpr")))
        ov = {k: _sig(_logit(v) + sigma * _z(seed, f"j|{ck.name}|ov|{k}")) for k, v in ck.overrides.items()}
        return replace(ck, v0=v0, overrides=ov)
    return ck


def _map_probs(ck: K.CheckV1, f) -> K.CheckV1:
    if ck.is_reading:
        return replace(ck, detects={k: f(v) for k, v in ck.detects.items()}, bg=f(ck.bg))
    return replace(ck, v0=replace(ck.v0, tpr=f(ck.v0.tpr), fpr=f(ck.v0.fpr)), overrides={k: f(v) for k, v in ck.overrides.items()})


def fa_miss(ck: K.CheckV1, fa_mult: float, hit_keep: float) -> K.CheckV1:
    """False alarms multiplied (capped at 0.5) and hit rates pulled toward the (new) false-alarm rate. Reading checks and v0 checks alike (for v0 checks: fpr and tpr, and the overrides as hits)."""
    if ck.is_reading:
        bg = min(0.5, ck.bg * fa_mult)
        return replace(ck, bg=bg, detects={k: (v if v <= ck.bg else bg + hit_keep * (v - bg)) for k, v in ck.detects.items()})
    fpr = min(0.5, ck.v0.fpr * fa_mult)
    return replace(ck, v0=replace(ck.v0, fpr=fpr, tpr=fpr + hit_keep * (ck.v0.tpr - fpr)),
                   overrides={k: (v if v <= ck.v0.fpr else fpr + hit_keep * (v - fpr)) for k, v in ck.overrides.items()})


def world_checks(w: World) -> tuple:
    """The checks as the WORLD answers them: the catalogue, then (in this order) the jittered/structural table, false alarms and misses, noise on the control-system reads and on field
    measurements, sharpening, and last the global degradation toward a coin flip. With the neutral world this is exactly `catalogue.degrade_all(CATALOGUE, rel_a)`, the table
    `world2.Oracle` uses."""
    cks = K.CATALOGUE
    if w.jitter > 0 or w.struct > 0:
        cks = tuple(jitter_check(c, w.jitter, w.struct, w.table_seed) for c in cks)
    if w.fa_mult != 1.0 or w.hit_keep != 1.0:
        cks = tuple(fa_miss(c, w.fa_mult, w.hit_keep) for c in cks)
    if w.bas_noise > 0 or w.field_noise > 0:
        cks = tuple(K.degrade(c, w.bas_noise if c.family == "control system" else w.field_noise) for c in cks)
    if w.sharpen > 0:
        cks = REL.sharpen_all(cks, w.sharpen)
    return K.degrade_all(cks, w.rel_a)


class StressOracle(TableOracle):
    """`TableOracle`'s rule (an answer is a fixed function of the visit, the complaint, the check and the target) with the world's check table `tc` (built once per world) and, in a
    stuck-sensor world, an air handler whose control-system static read is stuck at 'normal' in a visit with the stated probability."""

    def __init__(self, event: W.Event, tc: dict, static_stuck: float = 0.0):
        self.event, self.rng, self.tc, self.static_stuck = event, np.random.default_rng(0), tc, static_stuck

    def ask_ahu(self, a: str, ck: K.CheckV1) -> str:
        if ck.name == "bas_static" and self.static_stuck > 0 and self._u(f"stuck|{a}") < self.static_stuck:
            return ck.words[1]
        return super().ask_ahu(a, ck)


def checks_table(w: World) -> dict:
    return {c.name: c for c in world_checks(w)}


# ---------------------------------------------------------------------------------------------- the tool's cases, and the arms
def cases_for(tier: str, tau: float, min_rate: float, drawings: str, bld) -> dict:
    s = replace(M.Settings().with_drawings(drawings), tau=tau)
    return {r: make_case_v1(bld, f"Room-{r}", W.TIER_ITEMS[tier], settings=s, context=W.tier_context(tier, r), member_name=f"Room {r}", min_rate=min_rate) for r in range(W.N_BOX)}


def load_trees(tree_dir: Path = TREE_DIR) -> dict:
    """{arm: tree dict}: Tree E in its two forms from `tree.tree_E`, and the four authors' trees (L1, L2 blind to the tool's numbers; I1, I2 informed of them) as frozen JSON files in `expert_trees/`."""
    return dict(tree_E=TR.tree_E(False), tree_Ed=TR.tree_E(True), tree_L1=TR.load_tree(Path(tree_dir) / "tree_L1.json"), tree_L2=TR.load_tree(Path(tree_dir) / "tree_L2.json"),
                tree_I1=TR.load_tree(Path(tree_dir) / "tree_I1.json"), tree_I2=TR.load_tree(Path(tree_dir) / "tree_I2.json"))


def no_check(cases: list, js: JointSettings) -> dict:
    """Zero checks: the guess the tool's prior alone gives for each complaint, declared for none."""
    st = JointSession(cases, js).status()
    return dict(minutes=0.0, n_checks=0, guess=[p["guess"] for p in st["complaints"]], concluded=[False] * len(cases), trace=[])


def run_arm(arm: str, trees: dict, cs: list, ctxs: list, oracle, js: JointSettings) -> dict:
    if arm in trees:
        return TR.run_tree(trees[arm], cs, oracle, ctxs)
    if arm == "no_check":
        return no_check(cs, js)
    return P.run_policy(arm, cs, oracle, ctxs, js)


def tcode(c: tuple) -> int:
    return TYPE_INDEX["wrong" if c[0] == "wrong" else c[0]]


def run_world(widx: int, w: World, n: int, trees: dict, frontier: bool = False, tiers: tuple = TIERS, arms: tuple = ARMS) -> dict:
    """`n` visits of one world, every arm at every tier on the same visits and the same answer table. Raw arrays only."""
    bld = W.make_building2()
    cases_all = W.make_cases(bld)
    events = [draw_event_mix(widx, i, w, cases_all) for i in range(n)]
    tc = checks_table(w)
    js = JointSettings(f=w.tool_f) if w.tool_f else JointSettings()
    out = dict(idx=widx, world=w, n=n, kind=np.array([e.kind for e in events]), n_compl=np.array([e.n for e in events]),
               truth_single=np.array([tcode(e.causes[0]) if e.n == 1 else -1 for e in events]), truth_flat=np.array([tcode(c) for e in events for c in e.causes], np.int16),
               tool_tag=(js.f, w.tool_drawings), arms={})
    variants = [(a, TAU, MIN_RATE, a) for a in arms] + ([(name, tau, mr, TOOL) for name, tau, mr in FRONTIER] if frontier else [])
    for tier in tiers:
        cb_cache = {}
        for name, tau, mr, base in variants:
            key = (tau, mr)
            if key not in cb_cache:
                cb_cache[key] = cases_for(tier, tau, mr, w.tool_drawings, bld)
            cb = cb_cache[key]
            mins, chk, ok, wc, cn, gflat, cflat, okflat = [], [], [], [], [], [], [], []
            for ev in events:
                cs = [cb[r] for r in ev.rooms]
                ctxs = [W.context_dict(tier, r) for r in ev.rooms]
                r = run_arm(base, trees, cs, ctxs, StressOracle(ev, tc, w.static_stuck), js)
                a, b, c = J.score(r, ev)
                mins.append(r["minutes"])
                chk.append(r["n_checks"])
                ok.append(a)
                wc.append(b)
                cn.append(c)
                gflat += [tcode(g) for g in r["guess"]]
                cflat += [bool(x) for x in r["concluded"]]
                okflat += [g == t for g, t in zip(r["guess"], ev.causes)]
            nn = out["n_compl"].astype(float)
            correct, wca, cna = np.array(ok, float), np.array(wc, float), np.array(cn, float)
            out["arms"][(tier, name)] = dict(minutes=np.array(mins, float), checks=np.array(chk, float), correct=correct, wc=wca / nn, concluded=cna, n=nn, acc=correct / nn, conc=cna / nn,
                                             guess_flat=np.array(gflat, np.int16), conc_flat=np.array(cflat, bool), ok_flat=np.array(okflat, bool))
    return out


def _run_args(args):
    return run_world(*args)


def compute(worlds: list[tuple[int, World]], trees: dict, n: int = N_EPISODES, workers: int | None = None, frontier_idx: int | None = None, tiers: tuple = TIERS, arms: tuple = ARMS) -> list[dict]:
    jobs = [(i, w, n, trees, i == frontier_idx, tiers, arms) for i, w in worlds]
    workers = workers if workers is not None else min(9, os.cpu_count() or 1)
    if workers <= 1 or len(jobs) == 1:
        return [_run_args(j) for j in jobs]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_run_args, jobs, chunksize=1))


# ---------------------------------------------------------------------------------------------- comparisons
def compare(a: dict, b: dict, idx: np.ndarray, boot: np.ndarray) -> dict:
    """`a` minus `b` on the same visits of `idx` (Addendum 21's labels: 5% minutes, 0.02 accuracy, 0.02 safety, paired 95% bootstrap intervals), plus the registered MATERIAL test of `a`
    being better than `b`: fewer minutes by MAT_TIME with accuracy no worse than MAT_ACC_FLOOR, or accuracy higher by MAT_ACC with minutes no more than MAT_TIME_CAP higher, or confident
    errors lower by MAT_SAFE with minutes no more than MAT_TIME_CAP higher and accuracy no worse than MAT_ACC_FLOOR; each with its interval excluding 0."""
    d_min, d_acc, d_wc = a["minutes"][idx] - b["minutes"][idx], a["acc"][idx] - b["acc"][idx], a["wc"][idx] - b["wc"][idx]
    ci_min, ci_acc, ci_wc = S.paired_ci(d_min, boot), S.paired_ci(d_acc, boot), S.paired_ci(d_wc, boot)
    base_min = float(b["minutes"][idx].mean())
    r_min = float(d_min.mean() / base_min) if base_min > 0 else float("nan")
    da, dw = float(d_acc.mean()), float(d_wc.mean())
    ts, as_ = SG.time_state(r_min, ci_min), SG.acc_state(da, ci_acc)
    kind, wstar = break_even(float(a["minutes"][idx].mean()), float(a["acc"][idx].mean()), base_min, float(b["acc"][idx].mean()))
    mat_time = r_min <= -MAT_TIME and ci_min[1] < 0 and da >= MAT_ACC_FLOOR
    mat_acc = da >= MAT_ACC and ci_acc[0] > 0 and r_min <= MAT_TIME_CAP
    mat_safe = dw <= -MAT_SAFE and ci_wc[1] < 0 and r_min <= MAT_TIME_CAP and da >= MAT_ACC_FLOOR
    return dict(d_min=float(d_min.mean()), r_min=r_min, d_acc=da, d_wc=dw, d_checks=float((a["checks"][idx] - b["checks"][idx]).mean()), ci_min=ci_min, ci_acc=ci_acc, ci_wc=ci_wc, time=ts, acc=as_,
                label=SG.label(ts, as_), safety=SG.safety_flag(dw, ci_wc), break_even=kind, wrong_cost=wstar, mat_time=bool(mat_time), mat_acc=bool(mat_acc), mat_safe=bool(mat_safe),
                material=bool(mat_time or mat_acc or mat_safe), minutes_a=float(a["minutes"][idx].mean()), minutes_b=base_min)


def summarize(v: dict, mask: np.ndarray) -> dict:
    s = J.summarize(v, mask)
    if s["n"]:
        s["median_minutes"] = float(np.median(v["minutes"][mask]))
        s["abstain"] = 1.0 - s["concluded"]
    return s


def visit_cost(v: dict, idx: np.ndarray, cw: float, cu: float) -> np.ndarray:
    """Per visit of `idx`: minutes + cw x (complaints declared and wrong) + cu x (complaints not declared)."""
    n = v["n"][idx]
    return v["minutes"][idx] + cw * v["wc"][idx] * n + cu * (n - v["concluded"][idx])


def value_compare(a: dict, b: dict, idx: np.ndarray, boot: np.ndarray) -> dict:
    """What arm `a` (the tool) saves per visit against arm `b`, in minutes-equivalent, at every point of the registered grid; the corners of the registered box with their paired intervals; and
    the break-even cost of a declared-wrong complaint at each undeclared-complaint cost (the C_WRONG at which the two cost the same)."""
    grid = {(cw, cu): float((visit_cost(b, idx, cw, cu) - visit_cost(a, idx, cw, cu)).mean()) for cw in VALUE_GRID_W for cu in VALUE_GRID_U}
    base = {(cw, cu): float(visit_cost(b, idx, cw, cu).mean()) for cw in VALUE_GRID_W for cu in VALUE_GRID_U}
    corners = {}
    for cw in C_WRONG_BOX:
        for cu in C_UNDECL_BOX:
            d = visit_cost(b, idx, cw, cu) - visit_cost(a, idx, cw, cu)
            ci = S.paired_ci(d, boot)
            m = float(visit_cost(b, idx, cw, cu).mean())
            corners[(cw, cu)] = dict(net=float(d.mean()), rel=float(d.mean() / m), ci=ci, ahead=bool(d.mean() / m > VALUE_MARGIN and ci[0] > 0), behind=bool(d.mean() / m < -VALUE_MARGIN and ci[1] < 0))
    n = a["n"][idx]
    d_wc, d_ab, d_min = float((a["wc"][idx] * n).mean() - (b["wc"][idx] * n).mean()), float(((n - a["concluded"][idx]) - (n - b["concluded"][idx])).mean()), float((a["minutes"][idx] - b["minutes"][idx]).mean())
    star = {}
    for cu in VALUE_GRID_U:
        den = -d_wc
        star[cu] = float((d_min + cu * d_ab) / den) if abs(den) > 1e-12 else float("nan")
    ahead, behind = all(c["ahead"] for c in corners.values()), all(c["behind"] for c in corners.values())
    return dict(grid=grid, base=base, corners=corners, break_even_wrong=star, state="TOOL AHEAD" if ahead else "TOOL BEHIND" if behind else "DEPENDS ON THE COSTS",
                net_default=grid[DEFAULT_COSTS[0], DEFAULT_COSTS[1]] if (DEFAULT_COSTS[0] in VALUE_GRID_W and DEFAULT_COSTS[1] in VALUE_GRID_U) else float("nan"))


def analyze_world(raw: dict, B: int = BOOT_B) -> dict:
    masks = J.subset_masks(raw)
    boot = {}
    for si, sub in enumerate(SUBSETS):
        idx = np.flatnonzero(masks[sub])
        boot[sub] = (idx, np.random.default_rng([SEED, raw["idx"], 99, si]).integers(0, len(idx), (B, len(idx))) if len(idx) else None)
    summ, cmp_ = {}, {}
    tiers = sorted({t for t, _ in raw["arms"]}, key=TIERS.index)
    for tier in tiers:
        names = [a for t, a in raw["arms"] if t == tier]
        for a in names:
            for sub in SUBSETS:
                summ[(tier, a, sub)] = summarize(raw["arms"][(tier, a)], masks[sub])
        for sub in SUBSETS:
            idx, bt = boot[sub]
            if bt is None:
                continue
            for other in [a for a in names if a != TOOL and a not in ("no_check",)]:
                cmp_[(tier, TOOL, other, sub)] = compare(raw["arms"][(tier, TOOL)], raw["arms"][(tier, other)], idx, bt)
                if other in TREES:
                    cmp_[(tier, other, TOOL, sub)] = compare(raw["arms"][(tier, other)], raw["arms"][(tier, TOOL)], idx, bt)
            if "tree_E" in names and ROUTINE in names:
                cmp_[(tier, "tree_E", ROUTINE, sub)] = compare(raw["arms"][(tier, "tree_E")], raw["arms"][(tier, ROUTINE)], idx, bt)
    val = {}
    for tier in tiers:
        for other in [a for a in TREES + (ROUTINE, "fast_parent") if (tier, a) in raw["arms"]]:
            for sub in ("all", "single"):
                idx, bt = boot[sub]
                if bt is not None:
                    val[(tier, other, sub)] = value_compare(raw["arms"][(tier, TOOL)], raw["arms"][(tier, other)], idx, bt)
    return dict(idx=raw["idx"], world=raw["world"], n=raw["n"], counts={s: int(masks[s].sum()) for s in SUBSETS}, sum=summ, cmp=cmp_, val=val, mean_complaints=float(raw["n_compl"].mean()))


# ---------------------------------------------------------------------------------------------- verdicts (registered)
def tool_beats(an: dict, tier: str, tree: str, sub: str = "all") -> bool:
    return an["cmp"][(tier, TOOL, tree, sub)]["material"]


def tree_beats(an: dict, tier: str, tree: str, sub: str = "all") -> bool:
    return an["cmp"][(tier, tree, TOOL, sub)]["material"]


def trees_run(an: dict, tier: str, sub: str = "all") -> tuple:
    return tuple(t for t in TREES if (tier, TOOL, t, sub) in an["cmp"])


def tool_beats_all_trees(an: dict, tier: str, sub: str = "all") -> bool:
    return all(tool_beats(an, tier, t, sub) for t in trees_run(an, tier, sub))


def any_tree_beats(an: dict, tier: str, sub: str = "all") -> bool:
    return any(tree_beats(an, tier, t, sub) for t in trees_run(an, tier, sub))


def count(analyses: list[dict], fn) -> int:
    return sum(1 for a in analyses if fn(a))


def gap_state(n_beats: int, n_total: int = 18) -> str:
    """Verdict 1 on one comparison: ALREADY CLOSE / MIXED / MATERIAL GAP, by the registered counts (scaled if fewer than 18 cells are run)."""
    lo, hi = CLOSE_MAX * n_total / 18, GAP_MIN * n_total / 18
    return "ALREADY CLOSE" if n_beats <= lo else "MATERIAL GAP" if n_beats >= hi else "MIXED"


def stress_state(n_tool: int, n_tree: int, n_total: int) -> str:
    """Verdict 2: SURVIVES (the tool materially better in at least two thirds of the stress worlds and no tree materially better in a third) / REVERSES (some tree materially better in a
    third or more) / ERODES (the rest, down to a third) / DOES NOT SURVIVE (the tool materially better in fewer than a third)."""
    if n_tree >= ERODE_FRAC * n_total:
        return "REVERSES"
    if n_tool >= SURVIVE_FRAC * n_total:
        return "SURVIVES"
    if n_tool >= ERODE_FRAC * n_total:
        return "ERODES"
    return "DOES NOT SURVIVE"


def verdicts(base: list[dict], stress: list[dict]) -> dict:
    t = PRIMARY_TIER
    out = {}
    have = [x for x in INFORMED_TREES if (t, x, "all") in base[0]["val"]]
    groups = dict(E=("tree_E",), blind=BLIND_TREES) | (dict(informed=tuple(have)) if have else {}) | dict(all_trees=BLIND_TREES + tuple(have))
    for label, names in groups.items():
        n = count(base, lambda a, names=names: all(tool_beats(a, t, x) for x in names))
        out[f"gap_{label}"] = (n, gap_state(n, len(base)))
        nT = count(stress, lambda a, names=names: all(tool_beats(a, t, x) for x in names))
        nR = count(stress, lambda a, names=names: any(tree_beats(a, t, x) for x in names))
        out[f"stress_{label}"] = (nT, nR, len(stress), stress_state(nT, nR, len(stress)))
    for tree in ("tree_E",) + tuple(have):
        sts = [a["val"][(t, tree, "all")]["state"] for a in base]
        out[f"value_base_{tree}"] = {k: sts.count(k) for k in ("TOOL AHEAD", "DEPENDS ON THE COSTS", "TOOL BEHIND")}
        sts = [a["val"][(t, tree, "all")]["state"] for a in stress]
        out[f"value_stress_{tree}"] = {k: sts.count(k) for k in ("TOOL AHEAD", "DEPENDS ON THE COSTS", "TOOL BEHIND")}
    out["value_base_E"], out["value_stress_E"] = out["value_base_tree_E"], out["value_stress_tree_E"]
    gE, sE = out["gap_E"][1], out["stress_E"][3]
    out["commercial"] = "MATERIAL AND ROBUST" if gE == "MATERIAL GAP" and sE == "SURVIVES" else "NOT MATERIAL" if gE == "ALREADY CLOSE" else "MATERIAL ONLY UNDER THE ASSUMED WORLD" \
        if gE == "MATERIAL GAP" else "PARTIAL"
    if have:
        gI, sI = out["gap_informed"][1], out["stress_informed"][3]
        out["commercial_informed"] = "MATERIAL AND ROBUST" if gI == "MATERIAL GAP" and sI == "SURVIVES" else "NOT MATERIAL" if gI == "ALREADY CLOSE" else "MATERIAL ONLY UNDER THE ASSUMED WORLD" \
            if gI == "MATERIAL GAP" else "PARTIAL"
    return out


# ---------------------------------------------------------------------------------------------- gates (checked before any table is read; a failure is NO RESULT)
def replay_minutes(steps: list, cases: list, ctxs: list) -> float:
    """An independent accountant: the minutes of a sequence of (complaint index or air handler id, check name, target) steps, from the catalogue's access / do / wait minutes, where the
    technician is, and the fallback minutes of data that is not on file. It shares no code with the tool's accountant except `data.availability` (the rule for what is missing)."""
    from ..v1 import data as D
    at, total = None, 0.0
    by_ahu = {c.ahu: i for i, c in reversed(list(enumerate(cases)))}
    for who, name, target in steps:
        i = by_ahu[who] if isinstance(who, str) else who
        c = cases[i]
        ck = next(x for x in c.checks if x.name == name)
        eq = {"box": c.doc if c.docs else None, "ahu": c.ahu, "zone": c.member if c.docs else None}[ck.subject]
        av = D.availability(ck, D.DataView(c.items, c.building, D.Context(**ctxs[i])), eq)
        place = {"target": target, "box": c.doc, "room": c.member or "room", "ahu": c.ahu or "ahu", "bas": "bas"}[ck.place]
        total += (0.0 if at == place else ck.access_min) + ck.do_min + ck.wait_min + av.extra_min
        at = place
    return total


def steps_of(arm: str, trace: list) -> list:
    """(who, check, target) of every check an arm actually did, from its trace."""
    if arm == TOOL:
        return [(who, name, target) for kind, who, name, target, _ in trace]
    return [(t[0], t[1], t[2]) for t in trace]


def gate_fair_accounting(trees: dict, n_events: int = 40) -> tuple[bool, str]:
    """The minutes an arm reports are what an independent accountant gets from the checks it did, for the tool, its routine and every tree, on events of several worlds at every tier:
    nobody gets a free or a doubled step."""
    bld = W.make_building2()
    cases_all = W.make_cases(bld)
    worlds = [base_worlds()[6][1], stress_worlds()[2][1], stress_worlds()[7][1]]
    bad, checked = [], 0
    for wi, w in enumerate(worlds):
        events = [draw_event_mix(900 + wi, i, w, cases_all) for i in range(n_events)]
        tc = checks_table(w)
        for tier in TIERS:
            cb = cases_for(tier, TAU, MIN_RATE, w.tool_drawings, bld)
            for ev in events:
                cs = [cb[r] for r in ev.rooms]
                ctxs = [W.context_dict(tier, r) for r in ev.rooms]
                for arm in (TOOL, ROUTINE) + tuple(x for x in TREES if x in trees):
                    r = run_arm(arm, trees, cs, ctxs, StressOracle(ev, tc, w.static_stuck), JointSettings())
                    got = replay_minutes(steps_of(arm, r["trace"]), cs, ctxs)
                    checked += 1
                    if abs(got - r["minutes"]) > 1e-9:
                        bad.append((w.name, tier, arm, round(got, 3), round(r["minutes"], 3)))
    return not bad, f"{checked} (arm, visit) pairs: every reported minute total equals the independent accountant's" + (f"; MISMATCHES: {bad[:3]}" if bad else "")


def gate_oracle(n_q: int = 120) -> tuple[bool, str]:
    """The answer table: order-independent; with the neutral world it answers exactly as Addendum 41's TableOracle; stuck sensors depend on the visit, not on who asks."""
    bld = W.make_building2()
    cases_all = W.make_cases(bld)
    w0 = base_worlds()[6][1]
    ev = draw_event_mix(6, 3, w0, cases_all)
    cb = cases_for(PRIMARY_TIER, TAU, MIN_RATE, w0.tool_drawings, bld)
    cs = [cb[r] for r in ev.rooms]
    qs = [(i, ck) for i, c in enumerate(cs) for ck in c.checks if ck.subject != "ahu"][:n_q]
    tc = checks_table(w0)
    a = [StressOracle(ev, tc).ask_room(i, ck, cs[i].doc) for i, ck in qs]
    b = [StressOracle(ev, tc).ask_room(i, ck, cs[i].doc) for i, ck in reversed(qs)][::-1]
    c = [TableOracle(ev, w0.rel_a).ask_room(i, ck, cs[i].doc) for i, ck in qs]
    ahu = [ck for ck in cs[0].checks if ck.subject == "ahu"]
    ws = replace(w0, static_stuck=0.5)
    s1 = [StressOracle(ev, checks_table(ws), 0.5).ask_ahu(cs[0].ahu, ck) for ck in ahu]
    s2 = [StressOracle(ev, checks_table(ws), 0.5).ask_ahu(cs[0].ahu, ck) for ck in reversed(ahu)][::-1]
    return a == b == c and s1 == s2, "answers are order-independent, equal TableOracle's in the neutral world, and a stuck sensor is a property of the visit"


def gate_neutral_world(n: int = 200) -> tuple[bool, str]:
    """`draw_event_mix` and `world_checks` are exactly the existing generator and table in the neutral world, including an economizer world's draw; mixes keep zeros at zero and sum to 1."""
    bld = W.make_building2()
    cases_all = W.make_cases(bld)
    ok, why = True, []
    for idx in (0, 6, 17):
        c = J.all_cells()[idx]
        q, pw = J.MAP_OF[c.map]
        w = World("n", "base", f=J.F_OF[c.shared], q_ahu=q, p_wrong=pw, rel_a=J.REL_A[c.rel])
        for i in range(n // 3):
            a, b = draw_event_mix(idx, i, w, cases_all), W.draw_event(idx, i, w.params(), cases_all)
            if (a.rooms, a.causes, a.u) != (b.rooms, b.causes, b.u):
                ok = False
                why.append(f"draw differs at cell {idx} event {i}")
                break
        tc = {k: v for k, v in checks_table(w).items()}
        ref = {x.name: x for x in K.degrade_all(K.CATALOGUE, w.rel_a)}
        if tc != ref:
            ok = False
            why.append(f"table differs at cell {idx}")
    we = World("e", "m", f=0.03, econ=True)
    for i in range(20):
        a = draw_event_mix(7, i, we, cases_all)
        b = W.draw_event(7, i, we.params(), cases_all, extra_causes=(C.ECON_FAULT,), shares=EC.ECON_SHARES)
        if (a.rooms, a.causes) != (b.rooms, b.causes):
            ok = False
            why.append("econ draw differs")
            break
    case = cases_all[("T2", 1)]
    cs, pr = W.local_prior(case, 0.05, 1)
    for m in MIXES:
        q = mix_prior(cs, pr, m)
        if abs(q.sum() - 1) > 1e-9 or any(q[k] > 0 for k, c in enumerate(cs) if pr[k] == 0):
            ok = False
            why.append(f"mix {m} breaks the prior")
    zs = mix_prior(cs, pr, "zone_side")
    if not zs[[k for k, c in enumerate(cs) if c[0] == "zone_sensor_setpoint"][0]] > pr[[k for k, c in enumerate(cs) if c[0] == "zone_sensor_setpoint"][0]]:
        ok = False
        why.append("zone_side mix does not raise zone_sensor_setpoint")
    return ok, "the neutral world is exactly the existing generator and table; every mix is a proper distribution" + (f"; PROBLEMS: {why[:3]}" if why else "")


def gate_trees(trees: dict) -> tuple[bool, str]:
    """Every tree validates, runs to the end on random answers at every tier without error, and never spends more than 12 checks on a complaint."""
    problems = {k: TR.validate(t) for k, t in trees.items()}
    if any(problems.values()):
        return False, f"invalid trees: { {k: v[:2] for k, v in problems.items() if v} }"

    class Rand:
        def __init__(self, seed):
            self.rng = np.random.default_rng(seed)

        def ask_room(self, i, ck, tgt):
            return ck.words[0] if self.rng.random() < 0.45 else ck.words[1]

        def ask_ahu(self, a, ck):
            return ck.words[0] if self.rng.random() < 0.45 else ck.words[1]

    bld = W.make_building2()
    runs, worst = 0, 0
    for tier in TIERS:
        cb = cases_for(tier, TAU, MIN_RATE, "mostly_right", bld)
        for name, t in trees.items():
            for seed in range(120):
                rng = np.random.default_rng([seed, 5])
                k = int(rng.integers(1, 5))
                rooms = [int(r) for r in rng.choice(np.arange(24), size=k, replace=False)]
                r = TR.run_tree(t, [cb[x] for x in rooms], Rand(seed), [W.context_dict(tier, x) for x in rooms])
                per = {}
                for tr in r["trace"]:
                    per[tr[0]] = per.get(tr[0], 0) + 1
                worst = max([worst] + list(per.values()))
                runs += 1
                if len(r["guess"]) != k or any(g is None for g in r["guess"]):
                    return False, f"{name} at {tier}: a complaint ended without a diagnosis"
    return worst <= TR.MAX_CHECKS_PER_COMPLAINT, f"{runs} random-answer visits over {len(trees)} trees x {len(TIERS)} tiers ran to the end; most checks on one complaint {worst} (limit {TR.MAX_CHECKS_PER_COMPLAINT})"


def gate_tool_unchanged(results: list[dict]) -> tuple[bool, str]:
    """The tool and its routine reproduce Addendum 41's stored arrays exactly in the 18 base cells at T3-noattr and T3 (so 'the adaptive tool' is the one every earlier result is about)."""
    import pickle
    raw41 = Path(__file__).resolve().parents[5] / "results" / "docmismatch" / "troubleshoot_tau" / "raw.pkl"
    if not raw41.exists():
        return False, f"Addendum 41's raw results are needed: {raw41}"
    stored = {r["idx"]: r for r in pickle.loads(raw41.read_bytes())}
    bad, n = [], 0
    for r in results:
        if r["idx"] not in stored:
            continue
        for tier in (E.EXT_ARM, "T3"):
            for pol in (TOOL, ROUTINE):
                a, s = r["arms"][(tier, pol)], stored[r["idx"]][(tier, pol, 0.95)]
                n += 1
                if not all(np.array_equal(a[k], s[k][: len(a[k])]) for k in ("minutes", "checks", "acc", "wc")):
                    bad.append((r["idx"], tier, pol))
    return not bad and n > 0, f"{n} (cell, tier, policy) arrays equal Addendum 41's stored tau-0.95 arrays exactly (over the visits run)" + (f"; MISMATCHES: {bad[:3]}" if bad else "")


def gate_events(results: list[dict]) -> tuple[bool, str]:
    from . import study_minrate as MR
    return MR.gate_g1(results, 50)


def gate_repro(a: list[dict], b: list[dict]) -> tuple[bool, str]:
    ok = all(np.array_equal(x["arms"][k][f], y["arms"][k][f]) for x, y in zip(a, b) for k in x["arms"] for f in ("minutes", "checks", "acc", "wc"))
    return ok, f"{len(a)} worlds reproduce exactly on a second run (one worker against many)"


# ---------------------------------------------------------------------------------------------- predictions (mine, registered before any tree was run; strict)
def cell_mean(analyses: list[dict], tier: str, arm: str, field: str, sub: str = "all") -> float:
    return float(np.mean([a["sum"][(tier, arm, sub)][field] for a in analyses if a["sum"][(tier, arm, sub)]["n"]]))


def predictions(base: list[dict], stress: list[dict], verd: dict) -> dict:
    t = PRIMARY_TIER
    m = lambda arm, f: cell_mean(base, t, arm, f)  # noqa: E731
    p = {}
    p["P1"] = (m("tree_E", "minutes") <= 0.90 * m(TOOL, "minutes"), f"minutes: E {m('tree_E', 'minutes'):.1f} against the tool's {m(TOOL, 'minutes'):.1f} ({100 * (m('tree_E', 'minutes') / m(TOOL, 'minutes') - 1):+.0f}%)")
    p["P2"] = (m(TOOL, "accuracy") - m("tree_E", "accuracy") >= 0.03, f"accuracy: tool {m(TOOL, 'accuracy'):.3f}, E {m('tree_E', 'accuracy'):.3f}")
    p["P3"] = (m("tree_E", "concluded") >= 2 * m(TOOL, "concluded"), f"declared: E {m('tree_E', 'concluded'):.3f}, tool {m(TOOL, 'concluded'):.3f}")
    p["P4"] = (m("tree_E", "wrong_confident") >= 2 * m(TOOL, "wrong_confident"), f"declared and wrong: E {m('tree_E', 'wrong_confident'):.4f}, tool {m(TOOL, 'wrong_confident'):.4f}")
    fp = m("fast_parent", "accuracy")
    p["P5"] = ((m("tree_E", "accuracy") - fp) >= 0.5 * (m(TOOL, "accuracy") - fp) and m("tree_E", "minutes") <= 0.8 * m("fast_parent", "minutes"),
               f"flat checklist {fp:.3f} / {m('fast_parent', 'minutes'):.0f} min -> E {m('tree_E', 'accuracy'):.3f} / {m('tree_E', 'minutes'):.0f} -> tool {m(TOOL, 'accuracy'):.3f} / {m(TOOL, 'minutes'):.0f}")
    accs = {tr: m(tr, "accuracy") for tr in BLIND_TREES}
    p["P6"] = (max(accs.values()) - min(accs.values()) >= 0.05, "blind-tree accuracies: " + ", ".join(f"{k} {v:.3f}" for k, v in accs.items()))
    p["P7"] = (verd["gap_E"][1] != "MATERIAL GAP", f"Verdict 1 against E: {verd['gap_E'][0]} of {len(base)} cells with a material tool advantage ({verd['gap_E'][1]})")
    lead = lambda an: an["sum"][(t, TOOL, "all")]["accuracy"] - an["sum"][(t, "tree_E", "all")]["accuracy"]  # noqa: E731
    prim = next(a for a in base if a["world"].name == "assumed/M0/R0")
    j10 = [a for a in stress if a["world"].jitter == 1.0]
    p["P8"] = (len(j10) == 2 and float(np.mean([lead(a) for a in j10])) < lead(prim), f"tool's accuracy lead over E: primary cell {lead(prim):+.3f}, sigma-1.0 jitter worlds {np.mean([lead(a) for a in j10]):+.3f}")
    ec = next(a for a in stress if a["world"].econ)
    p["P9"] = (ec["sum"][(t, TOOL, "all")]["wrong_confident"] < ec["sum"][(t, "tree_E", "all")]["wrong_confident"],
               f"economizer world declared-and-wrong: tool {ec['sum'][(t, TOOL, 'all')]['wrong_confident']:.4f}, E {ec['sum'][(t, 'tree_E', 'all')]['wrong_confident']:.4f}")
    dep = sum(1 for a in base if a["val"][(t, "tree_E", "all")]["state"] == "DEPENDS ON THE COSTS")
    p["P10"] = (dep >= 10, f"value verdict against E at the registered cost box: DEPENDS ON THE COSTS in {dep} of {len(base)} cells")
    fr = prim["sum"].get((t, "tool@mr0.08", "all"))
    p["P11"] = (fr is not None and fr["minutes"] <= 1.10 * prim["sum"][(t, "tree_E", "all")]["minutes"] and fr["accuracy"] > prim["sum"][(t, "tree_E", "all")]["accuracy"],
                "the tool at min_rate 0.08, primary cell: " + (f"{fr['minutes']:.1f} min / {fr['accuracy']:.3f} against E's {prim['sum'][(t, 'tree_E', 'all')]['minutes']:.1f} / {prim['sum'][(t, 'tree_E', 'all')]['accuracy']:.3f}" if fr else "not run"))
    have = [x for x in INFORMED_TREES if (t, x, "all") in base[0]["sum"]]
    if not have:
        return p
    best_inf = max(have, key=lambda x: m(x, "accuracy"))
    p["P12"] = (m(best_inf, "accuracy") - m("tree_E", "accuracy") >= 0.05, f"knowledge helps a tree: best informed tree ({best_inf}) {m(best_inf, 'accuracy'):.3f}, E {m('tree_E', 'accuracy'):.3f}")
    p["P13"] = (m(TOOL, "accuracy") - m(best_inf, "accuracy") >= 0.03, f"adaptivity beyond knowledge: tool {m(TOOL, 'accuracy'):.3f}, best informed tree {m(best_inf, 'accuracy'):.3f}")
    p["P14"] = (m(best_inf, "wrong_confident") <= 0.5 * m("tree_E", "wrong_confident"), f"declared and wrong: best informed tree {m(best_inf, 'wrong_confident'):.4f}, E {m('tree_E', 'wrong_confident'):.4f}")
    return p


# ---------------------------------------------------------------------------------------------- pooled views for the report
def pool(results: list[dict], tier: str, arm: str) -> dict:
    keys = ("minutes", "checks", "acc", "wc", "conc", "n", "correct", "concluded")
    out = {k: np.concatenate([r["arms"][(tier, arm)][k] for r in results]) for k in keys}
    out["guess_flat"] = np.concatenate([r["arms"][(tier, arm)]["guess_flat"] for r in results])
    out["conc_flat"] = np.concatenate([r["arms"][(tier, arm)]["conc_flat"] for r in results])
    out["ok_flat"] = np.concatenate([r["arms"][(tier, arm)]["ok_flat"] for r in results])
    out["truth_flat"] = np.concatenate([r["truth_flat"] for r in results])
    out["truth_single"] = np.concatenate([r["truth_single"] for r in results])
    out["kind"] = np.concatenate([r["kind"] for r in results])
    return out


def pooled_row(p: dict, mask: np.ndarray | None = None) -> dict:
    """Visit-level means as in every earlier addendum, plus the complaint-level split into declared-and-right, declared-and-wrong and not declared (they add to 1)."""
    m = np.ones(len(p["minutes"]), bool) if mask is None else mask
    flat_m = np.repeat(m, p["n"].astype(int))
    c, ok = p["conc_flat"][flat_m], p["ok_flat"][flat_m]
    return dict(visits=int(m.sum()), mean_min=float(p["minutes"][m].mean()), median_min=float(np.median(p["minutes"][m])), checks=float(p["checks"][m].mean()), accuracy=float(p["acc"][m].mean()),
                right_declared=float((c & ok).mean()), wrong_declared=float((c & ~ok).mean()), undeclared=float((~c).mean()), n_compl=float(p["n"][m].mean()),
                min_per_complaint=float(p["minutes"][m].sum() / p["n"][m].sum()))


def fault_rows(results: list[dict], tier: str, arms: tuple) -> list[dict]:
    pools = {a: pool(results, tier, a) for a in arms}
    truth = pools[arms[0]]["truth_flat"]
    rows = []
    for ti, name in enumerate(TYPE_IDS):
        sel = truth == ti
        if not sel.any():
            continue
        row = dict(cause=name, n=int(sel.sum()), arms={})
        for a, p in pools.items():
            c, ok = p["conc_flat"][sel], p["ok_flat"][sel]
            row["arms"][a] = dict(right=float(ok.mean()), declared=float(c.mean()), wrong_declared=float((c & ~ok).mean()))
            sm = p["truth_single"] == ti
            row["arms"][a]["single_n"] = int(sm.sum())
            row["arms"][a]["single_median_min"] = float(np.median(p["minutes"][sm])) if sm.any() else float("nan")
        rows.append(row)
    return sorted(rows, key=lambda r: -r["n"])


def pct(x: float, d: int = 0) -> str:
    return f"{100 * x:.{d}f}%"


def tree_facts(trees: dict) -> list[dict]:
    out = []
    for k, t in trees.items():
        lv = TR.leaves(t["root"])
        ops = {}
        for _, n in lv:
            ops[n["op"] + (":sure" if n.get("sure") else ":unsure" if n["op"] == "conclude" else "")] = ops.get(n["op"] + (":sure" if n.get("sure") else ":unsure" if n["op"] == "conclude" else ""), 0) + 1

        def depth(n):
            return 1 + max([depth(n[b]) for b in ("pos", "neg", "na") if b in n], default=0) if n.get("op") == "check" else 1

        used = set()

        def walk(n):
            if n.get("op") == "check":
                used.update(n["check"])
                for b in ("pos", "neg", "na"):
                    if b in n:
                        walk(n[b])
        walk(t["root"])
        if t.get("preamble"):
            walk(t["preamble"])
        out.append(dict(arm=k, name=t["name"], nodes=TR.count_nodes(t["root"]), preamble=TR.count_nodes(t["preamble"]) if t.get("preamble") else 0, depth=depth(t["root"]), leaves=len(lv),
                        leaf_ops=ops, checks_used=len(used)))
    return out


def sha(path: Path) -> str:
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
