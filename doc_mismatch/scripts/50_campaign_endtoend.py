"""Addendum 15, Part B: does wiring the dither campaign into the engine make `vav_zone` verdicts better? (PREREGISTRATION_DR.md Addendum 15)
Stage 1 = the frozen passive engine (leave-one-topology-out, futility rule on, no channel exclusion); stage 2 = escalation to a 96 h / 168 h setpoint-dither campaign whose scores enter the
belief through a conditional-logit link fitted on TRAINING buildings only (`dr/campaign_eval.py`). Never touches SEALED data, T1-T6 suites or real data.
  .venv/bin/python doc_mismatch/scripts/50_campaign_endtoend.py
Needs the campaigns of scripts/48 (config a1.5_p0.0, seeds 4-6).
"""
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
from docmismatch.active.readiness import SimKind, h32  # noqa: E402
from docmismatch.data import load_base  # noqa: E402
from docmismatch.dr import campaign_eval as C  # noqa: E402
from docmismatch.dr import layer_eval as L  # noqa: E402
from docmismatch.dr import perturbation as P  # noqa: E402
from docmismatch.dr.pools import DR_DIR, build_pool  # noqa: E402
from docmismatch.dr.verifier_eval import EXISTING, cases_for, make_cfg  # noqa: E402

CAMP = ROOT.parent / "results" / "docmismatch" / "perturbation" / "campaigns15" / "a1.5_p0.0"
OUT = DR_DIR / "campaign"
TOPOS = ["sys07_vav_reheat", "vav_2ahu_2loops", "vav_3ahu_2loops", "dev_E", "dev_F", "dev_G", "dev_H"]      # train-role topologies with a VAV campaign
SEASONS = ["july", "january"]
SEEDS = (4, 5, 6)
SMOKE = os.environ.get("CAMPAIGN_SMOKE") == "1"    # plumbing test only: runs on Addendum 13's already-scored campaigns, writes nothing, prints only row counts
if SMOKE:
    CAMP, SEEDS = ROOT.parent / "results" / "docmismatch" / "perturbation" / "campaigns", (1, 2, 3)
LENGTHS = (96, 168)
PRE = 48
FUT = dict(futility_window=4, futility_margin=0.05)            # Addendum 7/10's frozen futility rule
SLOT = "vav_zone"
RS = (0.0, 0.1, 1.0, 10.0)


def build_pools() -> dict:
    old = EV.MASK_CHANNELS
    EV.MASK_CHANNELS = True
    try:
        return {t: {0: build_pool(t, 0, None)} for t in EXISTING}       # the pools scripts/44 and 47 use
    finally:
        EV.MASK_CHANNELS = old


def truth_and_ids(b):
    zones, vavs = sorted(b.ids("Zone")), sorted(b.ids("VAV"))
    own = {m: o for o, m in b.slot_edges[SLOT]}
    return zones, vavs, np.array([vavs.index(own[z]) for z in zones])


_CAMPS = {}


def campaign(tid, season, seed):
    k = (tid, season, seed)
    if k not in _CAMPS:
        b = load_base(tid, CAMP / season / f"seed{seed}")
        zones, vavs, truth = truth_and_ids(b)
        U, Y = P.campaign_arrays(b.ev, zones, vavs, PRE)
        _CAMPS[k] = dict(zones=zones, vavs=vavs, truth=truth, U=U, Y=Y)
    return _CAMPS[k]


def scores(camp, Lh, key):
    """S (zones, boxes) on the first Lh campaign hours with one `legacy`-noise draw seeded by `key`"""
    rng = np.random.default_rng([2, h32(key) % (2 ** 31)])
    Yn = P.add_noise({k: v[:, :Lh] for k, v in camp["Y"].items()}, "legacy", rng)
    return P.scores(camp["U"][:, :Lh], Yn)


def truth_check(pools):
    """code-path check: the campaign's zone-to-box truth equals the pool's vav_zone truth for every member of every topology"""
    bad = []
    for tid in TOPOS:
        sp = pools[tid][0].slots[SLOT]
        c = campaign(tid, "july", SEEDS[0])
        for mi, mem in enumerate(sp.members):
            if sp.owners[int(sp.truth[mi])] != c["vavs"][int(c["truth"][c["zones"].index(mem)])]:
                bad.append((tid, mem))
    return bad


def passive_stage(kind, cfg, h, eps, runkw):
    tr = kind.train([u for u in EXISTING if u != h])
    mod, beta = kind.fit_slot(tr, SLOT, None)
    out = {}
    if not mod:
        return out, beta
    for e in eps:
        r = run_episode(e, mod, kind.slice_idx(e, "visit", 0), "active", tau=cfg["tau"], nmax=cfg["nmax"], seed=h32(e.ep_id) % 10_000, beta=beta, diag=True, **FUT, **runkw)
        if r is None:
            continue
        post = r.diag["post"][-1].astype(float)
        out[e.ep_id] = dict(post=post / post.sum(), hyps=list(r.diag["hyps"]), n_read=int(r.n_read), futile=bool(r.futile), stopped=bool(r.stopped))
    return out, beta


def compute(t0):
    cfg = make_cfg(("active",))
    cfg["sim_reps"] = [0]
    runkw = SEL.get(cfg["variant"])["runkw"]
    pools = build_pools()
    bad = truth_check(pools)
    if bad:
        raise SystemExit(f"CODE-PATH CHECK FAILED: campaign truth differs from the pool's vav_zone truth for {bad[:5]}")
    print(f"code-path check passed (campaign truth == pool truth for every member of {len(TOPOS)} topologies) {time.time() - t0:.0f}s", flush=True)
    kind = SimKind(cfg, topos=EXISTING, pools=pools, cases=cases_for(EXISTING))
    rows = {"P0": [], **{f"P{i + 1}": [] for i in range(len(LENGTHS))}, **{f"C{Lh}": [] for Lh in LENGTHS}}
    info = dict(kappa={}, passive={}, beta={})
    for h in TOPOS:
        eps = [e for _, e in kind.episodes(None, h) if e.slot == SLOT]
        pas, beta = passive_stage(kind, cfg, h, eps, runkw)
        info["beta"][h] = beta
        info["passive"][h] = dict(n=len(pas), resolved=sum(v["stopped"] for v in pas.values()), futile=sum(v["futile"] for v in pas.values()), reads=float(np.mean([v["n_read"] for v in pas.values()])))
        train = [t for t in TOPOS if t != h]
        kappa = {}
        for Lh in LENGTHS:
            Ss, Ts = [], []
            for t in train:
                for season in SEASONS:
                    for s in SEEDS:
                        c = campaign(t, season, s)
                        Ss.append(scores(c, Lh, f"train|{t}|{season}|{s}|{Lh}"))
                        Ts.append(c["truth"])
            kappa[Lh] = C.fit_kappa(Ss, Ts)
        info["kappa"][h] = kappa
        for e in eps:
            if e.ep_id not in pas:
                continue
            v = pas[e.ep_id]
            sp = e.pool.slots[SLOT]
            hyps = v["hyps"]
            truth_j = hyps.index(e.truth_owner)
            rows["P0"].append(C.make_row(v["post"], truth_j, e.is_wrong, h, tau=cfg["tau"], ep=e.ep_id, reads=v["n_read"], hours=0.0, season="-"))
            passive_done = C.verdict(v["post"], cfg["tau"]) != "FLAGGED"
            for i, Lh in enumerate(LENGTHS):
                kap = kappa[Lh][0]
                for season in SEASONS:
                    for s in SEEDS:
                        c = campaign(h, season, s)
                        S = scores(c, Lh, f"{e.ep_id}|{season}|{s}|{Lh}")
                        s_row = S[c["zones"].index(sp.members[e.member])]
                        box_idx = [c["vavs"].index(sp.owners[o]) for o in hyps]
                        p1 = v["post"] if passive_done else C.combine(v["post"], box_idx, s_row, kap)
                        rows[f"P{i + 1}"].append(C.make_row(p1, truth_j, e.is_wrong, h, tau=cfg["tau"], ep=e.ep_id, reads=v["n_read"], hours=0.0 if passive_done else float(Lh), season=season, seed=s))
                        pc = C.combine(C.engine_prior(len(hyps)), box_idx, s_row, kap)
                        rows[f"C{Lh}"].append(C.make_row(pc, truth_j, e.is_wrong, h, tau=cfg["tau"], ep=e.ep_id, reads=0, hours=float(Lh), season=season, seed=s))
        if not SMOKE:
            print(f"  held-out {h:18s} episodes={len(pas):3d} passive resolved={info['passive'][h]['resolved']} futile={info['passive'][h]['futile']} "
                  f"kappa={ {k: v[0] for k, v in kappa.items()} } {time.time() - t0:.0f}s", flush=True)
    return dict(rows=rows, info=info)


def ci(rows, stat):
    lo, hi = C.cluster_boot(rows, stat)
    return "n/a" if not (np.isfinite(lo) and np.isfinite(hi)) else f"[{lo:.2f}, {hi:.2f}]"


def acc_stat(rows):
    return L.summarize(rows)["acc_answered"]


def line(name, rows):
    s = L.summarize(rows)
    n_ok = L.n_answered_correct(rows)
    res = C.resolved_fraction(rows)
    reads, hours = float(np.mean([r["reads"] for r in rows])), float(np.mean([r["hours"] for r in rows]))
    hpv = (sum(r["hours"] for r in rows) / n_ok) if n_ok else float("nan")
    return (f"| {name} | {len(rows)} | {res:.2f} {ci(rows, C.resolved_fraction)} | {s['acc_answered']:.3f} {ci(rows, acc_stat)} | {s['wrong_confident']:.1%} | "
            f"{s['false_alarm']:.1%} | {s['missed_fault']:.1%} | {C.localisation(rows):.2f} | {reads:.1f} | {hours:.0f} | {'-' if not np.isfinite(hpv) else f'{hpv:.0f}'} |")


HEAD = ["| policy / subset | rows | resolved [CI] | acc \\| resolved [CI] | wrong & confident | false alarms | missed faults | localised (wrong docs) | passive reads / row | campaign h / row | campaign h / correct verdict |",
        "|---|---|---|---|---|---|---|---|---|---|---|"]


def main():
    t0 = time.time()
    if SMOKE:
        res = compute(t0)
        print("SMOKE OK: rows per policy", {k: len(v) for k, v in res["rows"].items()}, f"{time.time() - t0:.0f}s")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / "campaign_endtoend.pkl"
    if f.exists():
        res = pickle.loads(f.read_bytes())
        print("loaded from cache", flush=True)
    else:
        res = compute(t0)
        f.write_bytes(pickle.dumps(res))
        print(f"done {time.time() - t0:.0f}s", flush=True)
    rows, info = res["rows"], res["info"]
    names = {"P0": "P0 passive only (futility on)", "P1": f"P1 passive, then {LENGTHS[0]} h campaign", "P2": f"P2 passive, then {LENGTHS[1]} h campaign",
             f"C{LENGTHS[0]}": f"C campaign only, {LENGTHS[0]} h (descriptive)", f"C{LENGTHS[1]}": f"C campaign only, {LENGTHS[1]} h (descriptive)"}

    md = ["# Addendum 15, Part B: wiring the dither campaign into the engine (`vav_zone`)", "",
          "112 `vav_zone` episodes (7 train-role topologies, 56 wrong / 56 right documentation), each scored under every (season, code seed 4-6) campaign realisation of its own building; "
          "stage 1 = frozen passive engine leave-one-topology-out with the futility rule; stage 2 = campaign escalation with a conditional-logit link fitted on the other 6 buildings' campaigns. "
          "Resolved = verdict rows / all rows; accuracy among resolved is class-balanced; false alarm = REFUTED on a right document; missed fault = CONFIRMED on a wrong document; "
          "localised = the most probable owner is the true one (wrong documents). CI = building-cluster bootstrap (500). Simulation only.", ""]
    n_p = sum(v["n"] for v in info["passive"].values())
    md += [f"Passive stage: {n_p} episodes; resolved passively {sum(v['resolved'] for v in info['passive'].values())}; stopped as futile {sum(v['futile'] for v in info['passive'].values())}; "
           f"mean passive reads {np.mean([v['reads'] for v in info['passive'].values()]):.1f}. Code-path check passed (campaign truth == pool truth).", ""]
    kap = {Lh: [info["kappa"][h][Lh] for h in TOPOS] for Lh in LENGTHS}
    md += ["Fitted link strength kappa (per held-out building; `*` = unbounded, the ML link is not finite): " + "; ".join(
        f"L={Lh} h: " + ", ".join(f"{k:.0f}{'*' if u else ''}" for k, u in kap[Lh]) for Lh in LENGTHS), ""]

    verdicts = {}
    for key, name in names.items():
        sub = rows[key]
        md += [f"## {name}", ""] + HEAD + [line("pooled", sub)]
        per = {}
        for season in SEASONS:
            ss = [r for r in sub if r["season"] in (season, "-")]
            md.append(line(season, ss))
            per[season] = C.policy_verdict(ss)
        pooled = C.policy_verdict(sub)
        md += ["", f"Frozen rule: pooled **{pooled}**; " + ", ".join(f"{s} {v}" for s, v in per.items()) + ("" if key.startswith("P") else "  (descriptive comparator, not scored)"), ""]
        if key in ("P1", "P2"):
            verdicts[key] = (pooled, per)

    md += ["## Total cost = passive reads + r x campaign hours, per correct resolved verdict", "", "r = one campaign hour in units of one passive read (not priced by us).", "",
           "| policy | " + " | ".join(f"r = {r:g}" for r in RS) + " |", "|---|" + "---|" * len(RS)]
    for key in ("P0", "P1", "P2"):
        sub = rows[key]
        n_ok = L.n_answered_correct(sub)
        cells = [(f"{(sum(x['reads'] for x in sub) + r * sum(x['hours'] for x in sub)) / n_ok:.1f}" if n_ok else "no verdicts") for r in RS]
        md.append(f"| {names[key]} | " + " | ".join(cells) + " |")

    md += ["", "## Frozen reading rules (Addendum 15, Part B)", "", "| policy | pooled | july | january |", "|---|---|---|---|"]
    for key, (pooled, per) in verdicts.items():
        md.append(f"| {names[key]} | {pooled} | {per['july']} | {per['january']} |")
    md += ["", f"**Overall: {C.overall(verdicts)}.**"]
    (OUT / "campaign_endtoend_report.md").write_text("\n".join(md))
    print("\n".join(md))


main()
