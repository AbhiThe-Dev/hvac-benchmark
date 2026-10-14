"""The severity-mixture study, exactly as frozen in MIX_PROTOCOL.md (read that first; this file implements it and changes nothing in it).

  .venv/bin/python doc_mismatch/live_demo_bldg11/study_mix.py                       # the registered run; refuses to run if MIX_PROTOCOL.md changed since it was frozen
  .venv/bin/python doc_mismatch/live_demo_bldg11/study_mix.py --smoke --out DIR     # plumbing check (2 cells, a few visits): prints gates only, never accuracy

Outputs (results/docmismatch/mix_study/): report.md, summary.json, complaints_s23.csv.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from docmismatch.troubleshoot import model as M  # noqa: E402
from docmismatch.troubleshoot.v1 import catalogue as K  # noqa: E402
from docmismatch.troubleshoot.v1 import data as D  # noqa: E402
from docmismatch.troubleshoot.v1.engine import make_case_v1  # noqa: E402
from docmismatch.troubleshoot.v2 import policies as P  # noqa: E402
from docmismatch.troubleshoot.v2 import study_joint as J  # noqa: E402
from docmismatch.troubleshoot.v2 import study_llm_ext as E  # noqa: E402
from docmismatch.troubleshoot.v2 import study_minrate as MR  # noqa: E402
from docmismatch.troubleshoot.v2 import study_tau as T  # noqa: E402
from docmismatch.troubleshoot.v2 import world2 as W  # noqa: E402
from docmismatch.troubleshoot.v2.joint import JointModel, JointSettings  # noqa: E402
from docmismatch.troubleshoot.v2.study_llm import TableOracle  # noqa: E402

import build_building as BB  # noqa: E402
import simulate as S  # noqa: E402  (the registered bldg11 family: visits, oracle, bootstrap and tables)
import visit as V  # noqa: E402

PROTOCOL, FROZEN = HERE / "MIX_PROTOCOL.md", HERE / "MIX_PROTOCOL.sha256"
OUT = ROOT.parent / "results" / "docmismatch" / "mix_study"
SEED_M = 20261012
MIX = ((0.05, 0.25), (0.15, 0.25), (0.5, 0.25), (0.9, 0.25))
S1_TIERS = (E.EXT_ARM, "T3")
S1_POLICIES = ("tool_joint", "tool_ticket_memo2")
S1_PRIMARY = (E.EXT_ARM, "tool_joint")
FAMS = {"bldg11": dict(ahus=BB.DEFAULT_AHUS, salt=(), voff=0, arms=("default", "adjusted", "mix")),
        "bldg18": dict(ahus=None, salt=(18,), voff=18000, arms=("default", "mix")),
        "bldg8": dict(ahus=None, salt=(8,), voff=8000, arms=("default", "mix"))}
ARM_JS = {"default": JointSettings(), "adjusted": JointSettings(r_low=0.10), "mix": JointSettings(low_mix=MIX), "onelevel": JointSettings(low_mix=((0.5, 1.0),))}


# ================================================================================================ S1: the 18 synthetic cells
def run_s1_variant(tier: str, policy: str, js: JointSettings, events: list, wp, bld) -> dict:
    """`study_tau.run_variant` with the joint settings as a parameter (tau 0.95 and the live min_rate throughout)."""
    cases_by_room = T.cases_with(tier, T.BASE_TAU, T.MIN_RATE, bld)
    mins, chk, ok, wc, cn = [], [], [], [], []
    for ev in events:
        cs = [cases_by_room[r] for r in ev.rooms]
        ctxs = [W.context_dict(tier, r) for r in ev.rooms]
        r = P.run_policy(policy, cs, TableOracle(ev, wp.rel_a), ctxs, js)
        a, b, c = J.score(r, ev)
        mins.append(r["minutes"])
        chk.append(r["n_checks"])
        ok.append(a)
        wc.append(b)
        cn.append(c)
    n = np.array([e.n for e in events], float)
    correct, wca, cna = np.array(ok, float), np.array(wc, float), np.array(cn, float)
    return dict(minutes=np.array(mins, float), checks=np.array(chk, float), correct=correct, wc=wca / n, concluded=cna, n=n, acc=correct / n, conc=cna / n)


def run_s1_cell(args) -> dict:
    idx, cell, n = args
    bld = W.make_building2()
    cases_all = W.make_cases(bld)
    wp = cell.params()
    events = [W.draw_event(idx, i, wp, cases_all) for i in range(n)]
    out = dict(idx=idx, cell=cell, n=n, kind=np.array([e.kind for e in events]))
    for tier in S1_TIERS:
        for pol in S1_POLICIES:
            for arm in ("default", "mix"):
                out[(tier, pol, arm)] = run_s1_variant(tier, pol, ARM_JS[arm], events, wp, bld)
    return out


def analyze_s1_cell(out: dict, B: int = 1000) -> dict:
    masks = J.subset_masks(out)
    cmp_, summ = {}, {}
    for si, sub in enumerate(J.SUBSETS):
        idx = np.flatnonzero(masks[sub])
        bt = np.random.default_rng([SEED_M, out["idx"], 99, si]).integers(0, len(idx), (B, len(idx))) if len(idx) else None
        for tier in S1_TIERS:
            for pol in S1_POLICIES:
                base, mix = out[(tier, pol, "default")], out[(tier, pol, "mix")]
                summ[(tier, pol, "default", sub)] = J.summarize(base, masks[sub])
                summ[(tier, pol, "mix", sub)] = J.summarize(mix, masks[sub])
                if bt is not None:
                    cmp_[(tier, pol, sub)] = MR.compare(mix, base, idx, bt)
    return dict(idx=out["idx"], cell=out["cell"], sum=summ, cmp=cmp_)


def is_harm(c: dict) -> bool:
    return c["label"] == "WORSE" or c["acc"] == "LESS" or c["safety"] == "REGRESSION"


def s1_counts(an: list, tier: str, pol: str) -> dict:
    cs = [a["cmp"][(tier, pol, "all")] for a in an]
    return dict(cells=len(cs), harm=sum(map(is_harm, cs)), improves=sum(c["label"] == "IMPROVES" for c in cs), neither=sum(c["label"] == "NEITHER" for c in cs),
                trade=sum(c["label"] == "TRADE" for c in cs), worse=sum(c["label"] == "WORSE" for c in cs), less=sum(c["acc"] == "LESS" for c in cs),
                safety=sum(c["safety"] == "REGRESSION" for c in cs), faster=sum(c["time"] == "FASTER" for c in cs), slower=sum(c["time"] == "SLOWER" for c in cs))


def s1_means(an: list, tier: str, pol: str, arm: str, sub: str = "all") -> dict:
    ss = [a["sum"][(tier, pol, arm, sub)] for a in an]
    return {k: float(np.mean([s[k] for s in ss])) for k in ("minutes", "accuracy", "wrong_confident", "concluded")}


# ================================================================================================ S2 / S3: real layouts
class Fam:
    """One real building's context for the visit family: its building file, the check list its real point map supports, one tool case per room, and the largest handler."""

    def __init__(self, name: str):
        spec = FAMS[name]
        self.name, self.spec = name, spec
        path = BB.ensure_building(name, spec["ahus"])
        raw = json.loads(path.read_text())
        self.checks = tuple(c for c in K.CATALOGUE if c.name not in BB.checks_absent_from_map(raw, K.CATALOGUE))
        bld = D.load_building_v1(path)
        ctx = D.Context(**S.CTX)
        self.cases = {r: make_case_v1(bld, r, V.ITEMS, V.SETTINGS, context=ctx, checks=self.checks, min_rate=V.MIN_RATE) for r in raw["claims"]["vav_zone"]}
        sizes = Counter(c.ahu for c in self.cases.values())
        self.handlers = sorted(sizes)
        self.shared_ahu = max(sizes, key=lambda a: (sizes[a], a))
        self.sizes = dict(sizes)


_FAMS: dict = {}


def fam(name: str) -> Fam:
    if name not in _FAMS:
        _FAMS[name] = Fam(name)
    return _FAMS[name]


def draw_visit_g(v: int, f: Fam) -> dict:
    """`simulate.draw_visit` generalised to any building (the faulty handler of shared visits is the LARGEST one); for bldg11 it reproduces the registered draw exactly (gate G3)."""
    salt, voff = f.spec["salt"], f.spec["voff"]
    rng = np.random.default_rng([S.SEED, *salt, v, 0])
    shared = v < S.N_SHARED
    rooms = sorted(f.cases)
    by_shared = [r for r in rooms if f.cases[r].ahu == f.shared_ahu]
    if shared:
        k = (3, 4, 5)[v % 3]
        sh = [by_shared[i] for i in rng.choice(len(by_shared), k, replace=False)]
        pool = [r for r in rooms if r not in sh]
        loc = [pool[i] for i in rng.choice(len(pool), S.N_COMPLAINTS - k, replace=False)]
    else:
        k, sh = 0, []
        loc = [rooms[i] for i in rng.choice(len(rooms), S.N_COMPLAINTS, replace=False)]
    items = [(r, ("low_static",)) for r in sh]
    for r in loc:
        if rng.random() < S.P_DOC_WRONG:
            alts = f.cases[r].candidates[1:]
            items.append((r, ("unlisted",) if rng.random() < S.P_UNLISTED else ("wrong", alts[int(rng.integers(len(alts)))])))
        else:
            items.append((r, (S.LOCAL_CAUSES[int(rng.integers(len(S.LOCAL_CAUSES)))],)))
    order = rng.permutation(len(items))
    items = [items[int(i)] for i in order]
    return dict(v=v + voff, kind="shared" if shared else "local", k=k, rooms=[r for r, _ in items], causes=[c for _, c in items],
                ahu_state={a: ("low_static" if (shared and a == f.shared_ahu) else "ok") for a in f.handlers})


class FamOracle(S.NoisyOracle):
    """`simulate.NoisyOracle` with the building's own check list (draws are the same pure function of seed, visit, world, who, check and target)."""

    def __init__(self, visit: dict, cases: list, world: int, a: float, checks: tuple):
        self.visit, self.cases, self.world = visit, cases, world
        self.tc = {c.name: c for c in K.degrade_all(checks, a)}


def run_fam_visit(args) -> dict:
    name, v, arms = args
    f = fam(name)
    visit = draw_visit_g(v, f)
    cl = [f.cases[r] for r in visit["rooms"]]
    out = {"visit": visit, "runs": {}}
    for wi, (wn, a) in enumerate(S.WORLDS.items()):
        orc = FamOracle(visit, cl, wi, a, f.checks)
        for arm in arms:
            r = P.run_policy("tool_ticket_memo2", cl, orc, [S.CTX] * len(cl), ARM_JS[arm])
            out["runs"][(wn, arm)] = dict(minutes=float(r["minutes"]), n_checks=int(r["n_checks"]), guess=[tuple(g) for g in r["guess"]], concluded=[bool(c) for c in r["concluded"]])
    return out


# ================================================================================================ gates
def gates_common(fam_results: dict, smoke: bool) -> dict:
    g = {}
    # G6 the derived check list of bldg11 is the demo's
    f11 = fam("bldg11")
    g["G6 bldg11 check list = demo's"] = ([c.name for c in f11.checks] == [c.name for c in V.CHECKS], f"{len(f11.checks)} checks, same names and order as the demo")
    # G3 generaliser == registered draw on bldg11; compositions
    same = all(draw_visit_g(v, f11) == S.draw_visit(v, S._CASES) for v in range(S.N_VISITS if not smoke else 12))
    msg = [f"bldg11: generalised draw {'identical to' if same else 'DIFFERENT FROM'} simulate.draw_visit"]
    ok = same
    for name, res in fam_results.items():
        f = fam(name)
        for r in res:
            vis = r["visit"]
            ls = [rm for rm, c in zip(vis["rooms"], vis["causes"]) if c == ("low_static",)]
            good = len(vis["rooms"]) == 6 and len(set(vis["rooms"])) == 6 and ((vis["kind"] == "shared" and vis["k"] in (3, 4, 5) and len(ls) == vis["k"] and all(f.cases[x].ahu == f.shared_ahu for x in ls))
                                                                              or (vis["kind"] == "local" and not ls))
            ok = ok and good
        msg.append(f"{name}: {len(res)} visits composed as stated (largest handler {f.shared_ahu}, {f.sizes[f.shared_ahu]} rooms)")
    g["G3 visit generator and composition"] = (ok, "; ".join(msg))
    # G4 oracle order independence
    f = fam("bldg18")
    vis = draw_visit_g(3, f)
    cl = [f.cases[r] for r in vis["rooms"]]
    qs = [(i, ck, cl[i].doc) for i in range(len(cl)) for ck in f.checks if ck.subject != "ahu" and ck.is_reading]
    o1, o2 = FamOracle(vis, cl, 0, 0.0, f.checks), FamOracle(vis, cl, 0, 0.0, f.checks)
    fwd = [o1.ask_room(*q) for q in qs]
    rev = [o2.ask_room(*q) for q in reversed(qs)][::-1]
    g["G4 oracle order-independent"] = (fwd == rev, f"{len(qs)} questions forward and backward")
    # G2 sums and the one-level mixture
    js = ARM_JS["mix"]
    sums = abs(js.state_prior.sum() - 1.0) < 1e-12 and abs(ARM_JS["default"].state_prior.sum() - 1.0) < 1e-12
    f11 = fam("bldg11")
    vis = draw_visit_g(0, f11)
    model = JointModel([f11.cases[r] for r in vis["rooms"]], js)
    bycause = all(abs(sum(d.values()) - 1.0) < 1e-9 for d in model.ahu_posterior_by_cause(model.initial()).values())
    g["G2a mixture sums"] = (sums and bycause, f"state prior sums to 1 (default and mixture); by-cause air-handler posterior sums to 1: {bycause}; states {js.states}")
    return g


def gate_g2b(n: int) -> tuple:
    f = fam("bldg11")
    bad = 0
    for v in range(n):
        vis = draw_visit_g(v, f)
        cl = [f.cases[r] for r in vis["rooms"]]
        for wi, (wn, a) in enumerate(S.WORLDS.items()):
            orc = FamOracle(vis, cl, wi, a, f.checks)
            r1 = P.run_policy("tool_ticket_memo2", cl, orc, [S.CTX] * 6, ARM_JS["default"])
            r2 = P.run_policy("tool_ticket_memo2", cl, orc, [S.CTX] * 6, ARM_JS["onelevel"])
            bad += not (r1["guess"] == r2["guess"] and r1["minutes"] == r2["minutes"] and r1["concluded"] == r2["concluded"])
    return bad == 0, f"a one-level mixture at r = 0.5 gives the default's guesses, conclusions and minutes on {n} bldg11 visits x 2 worlds: {'identical' if not bad else f'{bad} DIFFER'}"


def gate_e2_corrected() -> tuple:
    """MIX_DEVIATIONS.md D1: `study_tau.gate_g3` draws the wrong event stream. The corrected check (scripts/92_tau_g3_check.py): on E2's own stream (cell index 0, the primary cell's world
    parameters) the routine at tau 0.95, min_rate 0.02, T3-noattr reproduces E2's stored 58.3 min / 80.4% exactly, and the sweep's code path equals the old one."""
    cells = J.all_cells()
    pidx = next(i for i, c in enumerate(cells) if c.is_primary)
    wp, bld = cells[pidx].params(), W.make_building2()
    cases_all = W.make_cases(bld)
    events = [W.draw_event(0, i, wp, cases_all) for i in range(1000)]
    old = MR.run_variant_events(E.EXT_ARM, T.MIN_RATE, events, wp, bld)
    new = T.run_variant(E.EXT_ARM, T.BASE_TAU, T.MIN_RATE, "tool_ticket_memo2", events, wp, bld)
    same = all(np.array_equal(old[k], new[k]) for k in ("minutes", "checks", "acc", "wc"))
    m, a = float(new["minutes"].mean()), float(new["acc"].mean())
    ok = same and round(m, 1) == 58.3 and round(a, 3) == 0.804
    return ok, f"on E2's own stream: {m:.1f} min / {a:.1%} against E2's 58.3 / 80.4%; new code path identical to the old: {same}"


def gate_g1b(res11: list) -> tuple:
    """This script's `default` arm reproduces the registered run's tool_shipped rows exactly."""
    stored: dict = {}
    for r in csv.DictReader(open(S.OUT / "complaints.csv")):
        if r["policy"] == "tool_shipped":
            stored.setdefault((r["world"], int(r["visit"])), []).append((r["room"], r["truth"], r["guess"], int(r["concluded"])))
    bad = 0
    for res in res11:
        vis = res["visit"]
        for wn in S.WORLDS:
            run = res["runs"][(wn, "default")]
            mine = [(rm, ":".join(t), ":".join(g), int(c)) for rm, t, g, c in zip(vis["rooms"], vis["causes"], run["guess"], run["concluded"])]
            bad += mine != stored[(wn, vis["v"])]
    return bad == 0, f"{len(res11)} visits x 2 worlds: the default arm's rows {'are identical to' if not bad else f'DIFFER ({bad}) from'} the registered run's tool_shipped rows"


# ================================================================================================ analysis and report
def pct(x: dict) -> str:
    return f"{100 * x['p']:.1f}% ({100 * x['lo']:.0f}-{100 * x['hi']:.0f})"


def mins(x: dict) -> str:
    return f"{x['p']:.0f} ({x['lo']:.0f}-{x['hi']:.0f})"


def analyse_fams(res_by_fam: dict, idx: np.ndarray) -> tuple[dict, dict, dict, list]:
    St, Pd, rows_all = {}, {}, []
    for name, res in res_by_fam.items():
        Tb, rows = S.tabulate(res)
        for r in rows:
            r["building"] = name
        rows_all += rows
        St[name] = S.stats_for(Tb, idx)
        Pd[name] = {}
        for w in S.WORLDS:
            Pd[name][f"{w}:mix-default"] = S.paired(Tb, idx, w, "mix", "default")
            if "adjusted" in FAMS[name]["arms"]:
                Pd[name][f"{w}:mix-adjusted"] = S.paired(Tb, idx, w, "mix", "adjusted")
    return St, Pd, {}, rows_all


def evaluate(an: list, St: dict, Pd: dict) -> list:
    out = []
    c = s1_counts(an, *S1_PRIMARY)
    out.append(("P1", "S1 tool_joint, T3-noattr: mixture is a HARM cell in at most 1 of 18", c["harm"] <= 1, f"{c['harm']} harm cells (WORSE {c['worse']}, accuracy LESS {c['less']}, safety REGRESSION {c['safety']})"))
    out.append(("P2", "S1 same: NEITHER in at least 12 of 18", c["neither"] >= 12, f"NEITHER {c['neither']}, IMPROVES {c['improves']}, TRADE {c['trade']}, WORSE {c['worse']}"))
    d, m = s1_means(an, *S1_PRIMARY, "default"), s1_means(an, *S1_PRIMARY, "mix")
    out.append(("P3", "S1 same: cell-mean accuracy within 1 point and minutes within 5% of default", abs(m["accuracy"] - d["accuracy"]) <= 0.01 and abs(m["minutes"] / d["minutes"] - 1) <= 0.05,
                f"accuracy {100 * d['accuracy']:.1f}% -> {100 * m['accuracy']:.1f}%, minutes {d['minutes']:.1f} -> {m['minutes']:.1f} ({100 * (m['minutes'] / d['minutes'] - 1):+.1f}%)"))
    s11 = St["bldg11"]
    mx, ad, df = s11[("W0", "mix")], s11[("W0", "adjusted")], s11[("W0", "default")]
    out.append(("P4", "S2 W0: mix accuracy within 3 points of adjusted and at least 15 above default", abs(mx["acc"]["p"] - ad["acc"]["p"]) <= 0.03 and mx["acc"]["p"] - df["acc"]["p"] >= 0.15,
                f"mix {100 * mx['acc']['p']:.1f}%, adjusted {100 * ad['acc']['p']:.1f}%, default {100 * df['acc']['p']:.1f}%"))
    out.append(("P5", "S2 W0: mix accuracy on shared-cause complaints at least 80%", mx["acc_shared"]["p"] >= 0.80, f"{100 * mx['acc_shared']['p']:.1f}%"))
    out.append(("P6", "S2 W0: mix minutes at most default's and within 15% of adjusted's", mx["minutes"]["p"] <= df["minutes"]["p"] and abs(mx["minutes"]["p"] / ad["minutes"]["p"] - 1) <= 0.15,
                f"mix {mx['minutes']['p']:.0f}, default {df['minutes']['p']:.0f}, adjusted {ad['minutes']['p']:.0f}"))
    m1 = s11[("W1", "mix")]
    out.append(("P7", "S2: mix still fails the safety bar (wrong-and-confident above 5% at W0 or above 10% at W1)", mx["wc"]["p"] > 0.05 or m1["wc"]["p"] > 0.10,
                f"W0 {100 * mx['wc']['p']:.1f}%, W1 {100 * m1['wc']['p']:.1f}%"))
    b18 = Pd["bldg18"]["W0:mix-default"]["acc"]
    out.append(("P8", "S3 bldg18 W0: mix accuracy at least 5 points above default", b18["p"] >= 0.05, f"{100 * b18['p']:+.1f} points ({100 * b18['lo']:+.1f} to {100 * b18['hi']:+.1f})"))
    b8 = Pd["bldg8"]["W0:mix-default"]["acc"]
    out.append(("P9", "S3 bldg8 W0: mix accuracy at least 5 points above default", b8["p"] >= 0.05, f"{100 * b8['p']:+.1f} points ({100 * b8['lo']:+.1f} to {100 * b8['hi']:+.1f})"))
    worst = min((Pd[b][f"{w}:mix-default"]["acc"]["p"], b, w) for b in Pd for w in S.WORLDS)
    out.append(("P10", "no S2/S3 building loses more than 3 points of accuracy (either world)", worst[0] >= -0.03, f"smallest change {100 * worst[0]:+.1f} points ({worst[1]}, {worst[2]})"))
    slow = max((Pd[b][f"{w}:mix-default"]["minutes"]["p"], b, w) for b in Pd for w in S.WORLDS)
    out.append(("P11", "no S2/S3 building takes more minutes per visit (either world)", slow[0] <= 0.0, f"largest change {slow[0]:+.0f} min ({slow[1]}, {slow[2]})"))
    return out


def report(an: list, St: dict, Pd: dict, preds: list, gates: dict, meta: dict) -> str:
    L = ["# Severity-mixture study (MIX_PROTOCOL.md)", "",
         "Simulation; layouts and point maps real (Mortar), faults, answers and minutes simulated and placeholder; worlds from the tool's own model family. `default` = shipped joint model, `mix` = "
         f"`low_mix` {MIX}, `adjusted` = `r_low` 0.10 (S2 reference only). 95% intervals from a bootstrap over visits. Nothing here changes a default of the tool.", "",
         f"Run {meta['when']}, {meta['secs']:.0f} s.", "",
         "> **REGISTERED OUTCOME: NO RESULT.** Gate G1a-ii, as registered (`study_tau.gate_g3`), FAILED on a reference Addendum 41 had already found to be wrong (the wrong event stream). The numbers "
         "below are reported under the logged deviation `MIX_DEVIATIONS.md` D1, which replaces that gate with its corrected form (PASS below). No result had been seen when the deviation was decided. "
         "They are not the registered result.", "",
         "## Gates", "", "| gate | result | detail |", "|---|---|---|"]
    for g, (ok, d) in gates.items():
        L.append(f"| {g} | {'PASS' if ok else 'FAIL'} | {d} |")
    L += ["", "## S1: the 18 synthetic cells (8 rooms per handler), mixture minus default", "",
          "| tier | policy | IMPROVES | NEITHER | TRADE | WORSE | accuracy LESS | safety REGRESSION | faster / slower | harm cells | cell-mean min (default -> mix) | accuracy | wrong-and-confident |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for tier in S1_TIERS:
        for pol in S1_POLICIES:
            c = s1_counts(an, tier, pol)
            d, m = s1_means(an, tier, pol, "default"), s1_means(an, tier, pol, "mix")
            L.append(f"| {tier} | {pol} | {c['improves']} | {c['neither']} | {c['trade']} | {c['worse']} | {c['less']} | {c['safety']} | {c['faster']} / {c['slower']} | **{c['harm']}** | {d['minutes']:.1f} -> {m['minutes']:.1f} | "
                     f"{100 * d['accuracy']:.1f}% -> {100 * m['accuracy']:.1f}% | {100 * d['wrong_confident']:.2f}% -> {100 * m['wrong_confident']:.2f}% |")
    for name in St:
        arms = FAMS[name]["arms"]
        f = fam(name)
        L += ["", f"## {'S2' if name == 'bldg11' else 'S3'}: {name} (largest handler {f.shared_ahu}, {f.sizes[f.shared_ahu]} rooms; handlers {dict(sorted(f.sizes.items()))}; checks supported by its real point map: {len(f.checks)})", ""]
        for w in S.WORLDS:
            L += [f"### {w}", "", "| arm | accuracy | wrong-and-confident | not concluded | false shared-cause call | minutes / visit | shared-cause complaints | local, in shared visits | local, in local visits | documentation-wrong |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
            for arm in arms:
                s = St[name][(w, arm)]
                L.append(f"| {arm} | {pct(s['acc'])} | {pct(s['wc'])} | {pct(s['nc'])} | {pct(s['fsc'])} | {mins(s['minutes'])} | {pct(s['acc_shared'])} | {pct(s['acc_local_in_shared'])} | {pct(s['acc_local_in_local'])} | {pct(s['acc_docwrong'])} |")
            L.append("")
        L += ["| world | a - b | accuracy (points) | minutes / visit |", "|---|---|---|---|"]
        for k, v in Pd[name].items():
            w, pair = k.split(":")
            L.append(f"| {w} | {pair} | {100 * v['acc']['p']:+.1f} ({100 * v['acc']['lo']:+.0f} to {100 * v['acc']['hi']:+.0f}) | {v['minutes']['p']:+.0f} ({v['minutes']['lo']:+.0f} to {v['minutes']['hi']:+.0f}) |")
    L += ["", "## Predictions (registered before the run)", "", "| # | prediction | result | detail |", "|---|---|---|---|"]
    for pid, text, ok, det in preds:
        L.append(f"| {pid} | {text} | {'HOLDS' if ok else 'DOES NOT HOLD'} | {det} |")
    L.append("")
    return "\n".join(L)


# ================================================================================================ main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    have, want = hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(), FROZEN.read_text().split()[0]
    if have != want:
        raise SystemExit("MIX_PROTOCOL.md has changed since it was frozen (MIX_PROTOCOL.sha256): a change after the freeze is a logged deviation, not a silent edit")
    S._init()
    t0 = time.time()
    cells = list(enumerate(J.all_cells()))
    n_events, n_vis = (20, 6) if a.smoke else (J.N_EPISODES, S.N_VISITS)
    if a.smoke:
        cells = cells[:2]
    ids = list(range(3)) + list(range(50, 53)) if a.smoke else list(range(n_vis))
    with ProcessPoolExecutor(a.workers) as ex:
        s1 = list(ex.map(run_s1_cell, [(i, c, n_events) for i, c in cells], chunksize=1))
        jobs = [(name, v, FAMS[name]["arms"]) for name in FAMS for v in ids]
        res_flat = list(ex.map(run_fam_visit, jobs, chunksize=1))
    res_by_fam = {name: [r for (nm, _, _), r in zip(jobs, res_flat) if nm == name] for name in FAMS}
    gates = gates_common(res_by_fam, a.smoke)
    gates["G2b one-level mixture = default"] = gate_g2b(10 if a.smoke else 30)
    expect = sum(len(ids) * len(S.WORLDS) * len(FAMS[n]["arms"]) for n in FAMS)
    got = sum(len(r["runs"]) for res in res_by_fam.values() for r in res)
    fin = all(np.isfinite(run["minutes"]) for res in res_by_fam.values() for r in res for run in r["runs"].values())
    gates["G5 completeness"] = (got == expect and fin and len(s1) == len(cells), f"{got} of {expect} building runs, {len(s1)} of {len(cells)} S1 cells, minutes finite: {fin}")
    if a.smoke:
        print(f"SMOKE ({len(cells)} cells x {n_events} events, {len(ids)} visits per building, {time.time() - t0:.0f} s) -- gates only, no accuracy printed; G1 needs the full run")
        for g, (ok, d) in gates.items():
            print(f"  {g}: {'PASS' if ok else 'FAIL'} - {d}")
        return
    gates["G1a-i default path reproduces Addendum 30 (study_tau.gate_g2)"] = T.gate_g2()
    reg = T.gate_g3()
    gates["G1a-ii AS REGISTERED (study_tau.gate_g3): known wrong reference, see MIX_DEVIATIONS.md D1"] = reg
    gates["G1a-ii CORRECTED per D1 (E2 on its own stream)"] = gate_e2_corrected()
    gates["G1b default arm = registered tool_shipped rows"] = gate_g1b(res_by_fam["bldg11"])
    registered_fail = {k for k, (ok, _) in gates.items() if not ok}
    if registered_fail - {"G1a-ii AS REGISTERED (study_tau.gate_g3): known wrong reference, see MIX_DEVIATIONS.md D1"}:
        for g, (ok, d) in gates.items():
            print(f"  {g}: {'PASS' if ok else 'FAIL'} - {d}")
        raise SystemExit("a gate failed beyond the logged deviation: NO RESULT")
    an = [analyze_s1_cell(o) for o in s1]
    idx = S.boot_idx()
    St, Pd, _, rows = analyse_fams(res_by_fam, idx)
    preds = evaluate(an, St, Pd)
    a.out.mkdir(parents=True, exist_ok=True)
    with open(a.out / "complaints_s23.csv", "w", newline="") as fh:
        w_ = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w_.writeheader()
        w_.writerows(rows)
    meta = dict(when=time.strftime("%Y-%m-%d"), secs=time.time() - t0)
    (a.out / "summary.json").write_text(json.dumps(dict(meta=meta, protocol_sha256=have, predictions=[dict(id=p, text=t, holds=bool(ok), detail=d) for p, t, ok, d in preds],
                                                         s1={f"{t}|{p}": s1_counts(an, t, p) for t in S1_TIERS for p in S1_POLICIES},
                                                         s23={f"{n}|{k[0]}|{k[1]}": v for n, st in St.items() for k, v in st.items()}), indent=1, default=float))
    (a.out / "report.md").write_text(report(an, St, Pd, preds, gates, meta))
    print("wrote", a.out / "report.md")


if __name__ == "__main__":
    main()
