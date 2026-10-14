"""Addendum 16, Part B: does a technician-style override test, with MEASURED rates, resolve `vav_zone` episodes honestly? (PREREGISTRATION_DR.md Addendum 16)
Stage 1 = the frozen passive engine (as Addendum 15); stage 2 = sequential single-box override tests on the engine's own Bernoulli machinery (`active/physical.py`, unchanged) whose
true/false-positive rates are measured on the 6 TRAINING buildings' simulated tests (scripts/52's cached scores). Never touches SEALED data, T1-T6 suites or real data.
  .venv/bin/python doc_mismatch/scripts/53_override_endtoend.py
Needs the runs of scripts/51 and the cached scores of scripts/52.
"""
import json
import os
import pickle
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import evidence as EV  # noqa: E402
from docmismatch.active import selection as SEL  # noqa: E402
from docmismatch.active.engine import run_episode  # noqa: E402
from docmismatch.active.physical import ACTUATE_OBSERVE, PhysicalTestType  # noqa: E402
from docmismatch.active.readiness import SimKind, h32  # noqa: E402
from docmismatch.data import load_base  # noqa: E402
from docmismatch.dr import campaign_eval as C  # noqa: E402
from docmismatch.dr import layer_eval as L  # noqa: E402
from docmismatch.dr import override_eval as O  # noqa: E402
from docmismatch.dr.pools import DR_DIR, build_pool  # noqa: E402
from docmismatch.dr.verifier_eval import EXISTING, cases_for, make_cfg  # noqa: E402

RUNS = ROOT.parent / "results" / "docmismatch" / "perturbation" / "overrides"
PART_A = ROOT.parent / "results" / "docmismatch" / "perturbation" / "override_eval.pkl"
OUT = DR_DIR / "override"
TOPOS = ["sys07_vav_reheat", "vav_2ahu_2loops", "vav_3ahu_2loops", "dev_E", "dev_F", "dev_G", "dev_H"]
SEASONS = ["july", "january"]
SEEDS = (1, 2, 3)
KINDS = ("full_cool", "close")
D_MIN = 60
NOISE = "legacy"
FUT = dict(futility_window=4, futility_margin=0.05)
SLOT = "vav_zone"
TAU = 0.95
MAX_TESTS = 4
SMOKE = os.environ.get("OVERRIDE_SMOKE") == "1"     # plumbing test only: one held-out building, writes nothing, prints only row counts


def build_pools() -> dict:
    old = EV.MASK_CHANNELS
    EV.MASK_CHANNELS = True
    try:
        return {t: {0: build_pool(t, 0, None)} for t in EXISTING}
    finally:
        EV.MASK_CHANNELS = old


_RUNS = {}


def run(kind, season, seed, tid):
    k = (kind, season, seed, tid)
    if k not in _RUNS:
        b = load_base(tid, RUNS / kind / season / f"seed{seed}")
        plan = {t["vav"]: t for t in json.loads((RUNS / kind / season / f"seed{seed}" / tid / "tests.json").read_text())["plan"]}
        zones = sorted(b.ids("Zone"))
        _RUNS[k] = dict(plan=plan, zones=zones, T=np.stack([b.ev[f"{z}|temp10"] for z in zones]))
    return _RUNS[k]


def passive_stage(kind, cfg, h, eps, runkw):
    tr = kind.train([u for u in EXISTING if u != h])
    mod, beta = kind.fit_slot(tr, SLOT, None)
    out = {}
    if not mod:
        return out
    for e in eps:
        r = run_episode(e, mod, kind.slice_idx(e, "visit", 0), "active", tau=cfg["tau"], nmax=cfg["nmax"], seed=h32(e.ep_id) % 10_000, beta=beta, diag=True, **FUT, **runkw)
        if r is None:
            continue
        post = r.diag["post"][-1].astype(float)
        out[e.ep_id] = dict(post=post / post.sum(), hyps=list(r.diag["hyps"]), n_read=int(r.n_read), futile=bool(r.futile))
    return out


def training_rates(scores, kind, season, h):
    """(theta, measured TPR, measured FPR) from the 6 training buildings' simulated tests (same command, season, D, noise)"""
    pos = np.concatenate([scores[(kind, season, t, D_MIN, NOISE)][0] for t in TOPOS if t != h])
    neg = np.concatenate([scores[(kind, season, t, D_MIN, NOISE)][1] for t in TOPOS if t != h])
    th = O.choose_theta(pos, neg)
    return (th, *O.measured_rates(pos, neg, th))


def compute(t0):
    cfg = make_cfg(("active",))
    cfg["sim_reps"] = [0]
    runkw = SEL.get(cfg["variant"])["runkw"]
    scores = pickle.loads(PART_A.read_bytes())["scores"]
    kind = SimKind(cfg, topos=EXISTING, pools=build_pools(), cases=cases_for(EXISTING))
    pol_names = [f"T_{k}{'' if r == 'measured' else '_assumed'}" for k in KINDS for r in ("measured", "assumed")]
    rows = {"P0": [], **{p: [] for p in pol_names}}
    info = dict(rates={}, passive={})
    for h in (TOPOS[:1] if SMOKE else TOPOS):
        eps = [e for _, e in kind.episodes(None, h) if e.slot == SLOT]
        pas = passive_stage(kind, cfg, h, eps, runkw)
        info["passive"][h] = dict(n=len(pas), resolved=sum(C.verdict(v["post"], TAU) != "FLAGGED" for v in pas.values()), reads=float(np.mean([v["n_read"] for v in pas.values()])))
        rates = {(k, s): training_rates(scores, k, s, h) for k in KINDS for s in SEASONS}
        info["rates"][h] = rates
        for e in eps:
            if e.ep_id not in pas:
                continue
            v = pas[e.ep_id]
            sp = e.pool.slots[SLOT]
            hyps, truth_j = v["hyps"], v["hyps"].index(e.truth_owner)
            zone = sp.members[e.member]
            boxes = [sp.owners[o] for o in hyps]
            rows["P0"].append(C.make_row(v["post"], truth_j, e.is_wrong, h, tau=TAU, ep=e.ep_id, tests=0, minutes=0.0, season="-"))
            for k in KINDS:
                for season in SEASONS:
                    theta, tpr, fpr = rates[(k, season)]
                    types = {"measured": PhysicalTestType(f"measured_{k}", tpr, fpr, ACTUATE_OBSERVE.cost, f"measured {k} override"), "assumed": ACTUATE_OBSERVE}
                    for s in SEEDS:
                        for rname, ttype in types.items():
                            def outcome(j, n_prev, k=k, season=season, s=s, theta=theta):
                                r = run(k, season, ((s - 1 + n_prev) % 3) + 1, h)
                                t = r["plan"][boxes[j]]
                                rng = np.random.default_rng([3, h32(e.ep_id) % (2 ** 31), s, n_prev, j, KINDS.index(k), SEASONS.index(season)])
                                sc = O.test_scores(r["T"], t["day"], t["start_hour"], D_MIN, k, O.NOISE_SD[NOISE], rng, season=season)
                                return bool(sc[r["zones"].index(zone)] >= theta)
                            post, log = O.run_physical_sequence(v["post"], outcome, ttype, tau=TAU, max_tests=MAX_TESTS)
                            name = f"T_{k}{'' if rname == 'measured' else '_assumed'}"
                            rows[name].append(C.make_row(post, truth_j, e.is_wrong, h, tau=TAU, ep=e.ep_id, tests=len(log), minutes=float(len(log) * D_MIN), season=season, seed=s))
        if not SMOKE:
            print(f"  held-out {h:18s} episodes={len(pas):3d} passive resolved={info['passive'][h]['resolved']} {time.time() - t0:.0f}s", flush=True)
    return dict(rows=rows, info=info)


def ci(rows, stat):
    lo, hi = C.cluster_boot(rows, stat)
    return "n/a" if not (np.isfinite(lo) and np.isfinite(hi)) else f"[{lo:.2f}, {hi:.2f}]"


def acc_stat(rows):
    return L.summarize(rows)["acc_answered"]


HEAD = ["| subset | rows | resolved [CI] | acc \\| resolved [CI] | wrong & confident | false alarms | missed faults | tests / row | forced minutes / row | minutes / correct verdict |", "|---|---|---|---|---|---|---|---|---|---|"]


def line(name, rows):
    s = L.summarize(rows)
    n_ok = L.n_answered_correct(rows)
    mins = sum(r["minutes"] for r in rows)
    return (f"| {name} | {len(rows)} | {C.resolved_fraction(rows):.2f} {ci(rows, C.resolved_fraction)} | {s['acc_answered']:.3f} {ci(rows, acc_stat)} | {s['wrong_confident']:.1%} | {s['false_alarm']:.1%} | "
            f"{s['missed_fault']:.1%} | {np.mean([r['tests'] for r in rows]):.2f} | {mins / len(rows):.0f} | {'-' if not n_ok else f'{mins / n_ok:.0f}'} |")


def main():
    t0 = time.time()
    if SMOKE:
        res = compute(t0)
        print("SMOKE OK: rows per policy", {k: len(v) for k, v in res["rows"].items()}, f"{time.time() - t0:.0f}s")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / "override_endtoend.pkl"
    if f.exists():
        res = pickle.loads(f.read_bytes())
        print("loaded from cache", flush=True)
    else:
        res = compute(t0)
        f.write_bytes(pickle.dumps(res))
        print(f"done {time.time() - t0:.0f}s", flush=True)
    rows, info = res["rows"], res["info"]
    label = {"P0": "P0 passive only (futility on)", "T_full_cool": "T_cool: passive, then override tests, `full_cool`, MEASURED rates", "T_full_cool_assumed": "T_cool_assumed: same, engine's ASSUMED rates 0.95 / 0.05",
             "T_close": "T_close: passive, then override tests, `close`, MEASURED rates", "T_close_assumed": "T_close_assumed: same, engine's ASSUMED rates 0.95 / 0.05"}

    md = ["# Addendum 16, Part B: technician-style override tests wired into the engine (`vav_zone`)", "",
          "112 `vav_zone` episodes (7 train-role buildings, 56 wrong / 56 right documentation), each under every (season, test-order seed) run = 6 rows per episode; stage 1 = frozen passive engine (Addendum 15); "
          f"stage 2 = up to {MAX_TESTS} sequential single-box override tests (D = {D_MIN} min, `legacy` 0.25 K noise), the next box chosen by `physical_eig`, belief updated with the engine's Bernoulli rule. "
          "MEASURED rates = Laplace-smoothed TPR / FPR on the 6 training buildings' tests at the theta chosen there (FPR <= 0.05); ASSUMED = `ACTUATE_OBSERVE`'s 0.95 / 0.05. Resolved = verdict rows / all rows; "
          "accuracy among resolved is class-balanced; false alarm = REFUTED on a right document; missed fault = CONFIRMED on a wrong document. CI = building-cluster bootstrap (500). Simulation only.", "",
          f"Passive stage: {sum(v['n'] for v in info['passive'].values())} episodes, resolved passively {sum(v['resolved'] for v in info['passive'].values())}, mean passive reads {np.mean([v['reads'] for v in info['passive'].values()]):.1f}.", ""]
    md += ["Training-measured rates used (mean over the 7 held-out fits): " + "; ".join(
        f"{k} {s}: theta {np.mean([info['rates'][h][(k, s)][0] for h in TOPOS]):.2f} K, TPR {np.mean([info['rates'][h][(k, s)][1] for h in TOPOS]):.3f}, FPR {np.mean([info['rates'][h][(k, s)][2] for h in TOPOS]):.3f}"
        for k in KINDS for s in SEASONS), ""]

    verdicts = {}
    for name, title in label.items():
        sub = rows[name]
        md += [f"## {title}", ""] + HEAD + [line("pooled", sub)]
        per = {}
        for season in SEASONS:
            ss = [r for r in sub if r["season"] in (season, "-")]
            md.append(line(season, ss))
            per[season] = C.policy_verdict(ss)
        pooled = C.policy_verdict(sub)
        scored = name in ("T_full_cool", "T_close")
        md += ["", f"Frozen rule: pooled **{pooled}**; " + ", ".join(f"{s} {v}" for s, v in per.items()) + ("" if scored else "  (descriptive, not scored)"), ""]
        if scored:
            verdicts[name] = (pooled, per)

    md += ["## Frozen reading rules (Addendum 16, Part B)", "", "| policy | pooled | july | january |", "|---|---|---|---|"]
    for name, (pooled, per) in verdicts.items():
        md.append(f"| {label[name]} | {pooled} | {per['july']} | {per['january']} |")
    ov = C.overall(verdicts).replace("wiring HELPS `vav_zone` (in simulation)", "the technician-style override WORKS (in simulation)").replace(
        "wiring HELPS IN ONE SEASON ONLY", "the technician-style override works in ONE SEASON ONLY").replace("wiring does NOT help", "the technician-style override does NOT work")
    md += ["", f"**Overall: {ov}.**"]
    (OUT / "override_endtoend_report.md").write_text("\n".join(md))
    print("\n".join(md))


main()
