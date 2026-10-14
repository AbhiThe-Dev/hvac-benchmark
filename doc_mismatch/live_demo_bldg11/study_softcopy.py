"""A softer copy between rooms, exactly as frozen in SOFTCOPY_NOTES.md (read that first; this file implements it and changes nothing in it).

  .venv/bin/python doc_mismatch/live_demo_bldg11/study_softcopy.py                       # the registered run; refuses to run if SOFTCOPY_NOTES.md changed since it was frozen
  .venv/bin/python doc_mismatch/live_demo_bldg11/study_softcopy.py --smoke --out DIR     # plumbing check (4 visits per family): prints timing and gates only, never accuracy

Outputs (results/docmismatch/softcopy_study/): report.md, summary.json. The Mortar Brick files must be in data_cache/ (not part of the repository); nothing here is committed or deployed.
"""
import argparse
import hashlib
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import simulate as S  # noqa: E402
import study_first_demo as FD  # noqa: E402
import study_fanmix as FM  # noqa: E402
import study_folding as F  # noqa: E402
import study_mix as MX  # noqa: E402
from docmismatch.troubleshoot.v1.engine import Obs, Question  # noqa: E402
from docmismatch.troubleshoot.v2.joint import MAX_CHECKS_PER_COMPLAINT, JointModel, ahu_row, bears_on_ahu  # noqa: E402
from docmismatch.troubleshoot.v2.policies import PriorSession  # noqa: E402

PROTOCOL, FROZEN = HERE / "SOFTCOPY_NOTES.md", HERE / "SOFTCOPY_NOTES.sha256"
OUT = HERE.parent.parent / "results" / "docmismatch" / "softcopy_study"
JS = FM.ARMS["TODAY"]
ARMS = ("HARD", "SOFT", "JOINT")
WORLDS = FM.WORLDS
LS, FAN = FM.LS, FM.FAN
REAL = FM.REAL
A0 = FM.A0
FAMILIES = [("A-LS", b) for b in REAL] + [("A-FAN", b) for b in REAL] + [("B", b) for b in REAL] + [(s, "demo") for s in ("S1", "S2", "S3", "S4", "S5")]
N_A, N_B, N_S, CHUNK = 200, 100, 100, 20


def n_visits(fam, smoke):
    if smoke:
        return 4
    return N_A if fam.startswith("A-") else N_B


# ---------------------------------------------------------------------------------------------- the routine with a soft copy
class SoftSession(PriorSession):
    """A ticket session whose starting belief is given (the joint marginal given everything so far) and which counts as informed once a reading that bears on its handler has been taken by anyone.
    With `joint_marg` its belief throughout is the joint marginal of its room (the JOINT arm)."""

    def __init__(self, case, prior, informed_probe, joint_marg=None):
        super().__init__(case, prior)
        self._probe, self._jm = informed_probe, joint_marg

    def _informed(self) -> bool:
        return super()._informed() or self._probe()

    def posterior(self):
        if self._jm is None:
            return super().posterior()
        return self._given[0], self._jm()


def run_ticket_soft(cases, oracle, js, full, diag=None):
    model = JointModel(cases, js)
    state = model.initial()
    informed, memo, at = set(), {}, None
    guess, concluded, per_room_min, own_static, checks = [], [], [], [], 0

    def jmarg(i):
        g = model.group_stats(state, cases[i].ahu)
        return g.marg[g.idx.index(i)]

    for i, case in enumerate(cases):
        a = case.ahu
        sess = SoftSession(case, (model.causes[i], jmarg(i)), (lambda a=a: a in informed), (lambda i=i: jmarg(i)) if full else None)
        sess.at = at
        for (aa, name), word in memo.items():
            if aa == a:
                sess.log.append(Obs(name, case.doc, "unsure", 0.0))                  # already answered: not asked again, and not a measurement of this room
        asked_ahu, own = False, 0
        while own < MAX_CHECKS_PER_COMPLAINT:
            step = sess.next_step()
            if step is None:
                break
            if isinstance(step, Question):
                raise RuntimeError(f"the tool asked {step.key!r}")
            ck = step.check
            word = oracle.ask_ahu(a, ck) if ck.subject == "ahu" else oracle.ask_room(i, ck, step.target)
            assert word in ck.words                                                  # gate G4
            pos = word == ck.words[0]
            if ck.subject == "ahu":                                                  # what JointModel.apply does with the answer
                asked_ahu = True
                q = ahu_row(ck, model.upstream)
                state.ahu_ll[a] = state.ahu_ll[a] + np.log(q if pos else 1.0 - q)
                informed.add(a)
                memo[(a, ck.name)] = word
            else:
                r = model.row(i, ck, step.target)
                lk = state.lik[i] * (r if pos else 1.0 - r)
                state.lik[i] = lk / lk.max()
                if bears_on_ahu(ck, model.upstream):
                    informed.add(a)
            sess.report(word)
            own += 1
        if diag is not None and not full and not asked_ahu:
            diag.append(float(np.abs(sess.posterior()[1] - jmarg(i)).max()))
        st = sess.status()
        guess.append(st["ranked"][0][0])
        concluded.append(bool(st["concluded"]))
        per_room_min.append(float(sess.elapsed))
        own_static.append(any(o.check == "static_at_box" and o.minutes > 0 for o in sess.log))
        checks += own
        at = sess.at
    return dict(minutes=float(sum(per_room_min)), per_room_min=per_room_min, own_static=own_static, n_checks=checks, guess=guess, concluded=concluded)


# ---------------------------------------------------------------------------------------------- visits
def s5_visit(v, cases):
    rng = np.random.default_rng([S.SEED, 5151, 5, v])
    k = (2, 3)[v % 2]
    rooms = [A0[i] for i in rng.choice(8, k + 2, replace=False)]
    sh, loc = rooms[:k], rooms[k:]
    items = [(r, LS, "shared") for r in sh] + [(r, tuple(FD.own_cause(rng, cases[r])), "local") for r in loc]
    items = [items[int(i)] for i in rng.permutation(len(items))]
    return dict(v=55000 + v, kind="shared", k=k, rooms=[i[0] for i in items], causes=[tuple(i[1]) for i in items], seg=[i[2] for i in items],
                ahu_state={"AHU-0": "low_static", "AHU-1": "ok", "AHU-2": "ok"})


def fam_visits(fam, bld, vs):
    if fam == "S5":
        cases, checks = FM.small()
        return [s5_visit(v, cases) for v in vs], cases, checks
    return FM.family_visits(fam, bld, vs)


# ---------------------------------------------------------------------------------------------- the runs
def run_arm(arm, cl, orc):
    if arm == "HARD":
        return F.run_ticket_v(cl, orc, JS, "base")
    return run_ticket_soft(cl, orc, JS, arm == "JOINT")


def run_chunk(args):
    fam, bld, wi, lo, hi = args
    visits, cases, checks = fam_visits(fam, bld, range(lo, hi))
    a = list(WORLDS.values())[wi][1]
    out = []
    for visit in visits:
        cl = [cases[r] for r in visit["rooms"]]
        visit = dict(visit, faulty=[visit["ahu_state"][c.ahu] != "ok" for c in cl])
        orc = MX.FamOracle(visit, cl, wi, a, checks)
        rec = {}
        for arm in ARMS:
            r = run_arm(arm, cl, orc)
            rec[arm] = dict(guess=[tuple(g) for g in r["guess"]], conc=[bool(c) for c in r["concluded"]], own=[bool(x) for x in r["own_static"]], minutes=float(r["minutes"]))
        out.append((visit, rec))
    return args, out


def collect(results):
    by = {}
    for args, out in results:
        by.setdefault((args[0], args[1], args[2]), []).append((args[3], out))
    res = {}
    for key, chunks in by.items():
        pairs = [p for _, out in sorted(chunks, key=lambda c: c[0]) for p in out]
        d = {"visits": [p[0] for p in pairs]}
        d["truth"] = [tuple(c) for p in pairs for c in p[0]["causes"]]
        d["seg"] = np.array([s for p in pairs for s in p[0]["seg"]])
        d["faulty"] = np.array([f for p in pairs for f in p[0]["faulty"]])
        d["visit"] = np.array([i for i, p in enumerate(pairs) for _ in p[0]["rooms"]])
        for arm in ARMS:
            g = [tuple(x) for p in pairs for x in p[1][arm]["guess"]]
            d[arm] = dict(guess=g, ok=np.array([x == t for x, t in zip(g, d["truth"])]), conc=np.array([c for p in pairs for c in p[1][arm]["conc"]]),
                          own=np.array([c for p in pairs for c in p[1][arm]["own"]]), vmin=np.array([p[1][arm]["minutes"] for p in pairs]))
        res[key] = d
    return res


def masks(d):
    sh = d["seg"] == "shared"
    return dict(all=np.ones(len(sh), bool), shared=sh, elsewhere=(~sh) & (~d["faulty"]), folded=(~sh) & d["faulty"])


def stats(d, arm):
    x, m = d[arm], masks(d)
    guess_ls = np.array([g == LS for g in x["guess"]])
    hedged = x["conc"] & guess_ls & ~x["own"]
    acc = lambda k: 100 * x["ok"][m[k]].mean() if m[k].any() else float("nan")             # noqa: E731
    return dict(acc=acc("all"), shared=acc("shared"), elsewhere=acc("elsewhere"), folded=acc("folded"), n_folded=int(m["folded"].sum()), minutes=float(x["vmin"].mean()),
                wc=100 * ((~x["ok"]) & x["conc"]).mean(), wc_h=100 * ((~x["ok"]) & x["conc"] & ~hedged).mean(), conc=100 * x["conc"].mean(),
                folded_ls=100 * guess_ls[m["folded"]].mean() if m["folded"].any() else float("nan"))


def per_visit(d, arm, which):
    m = masks(d)[which]
    nv = len(d["visits"])
    n = np.array([m[d["visit"] == v].sum() for v in range(nv)], float)
    s = np.array([d[arm]["ok"][(d["visit"] == v) & m].sum() for v in range(nv)], float)
    return n, s


def boot_mean(x, B=2000, seed=43):
    rng = np.random.default_rng(seed)
    n = len(x)
    return np.percentile([x[rng.integers(n, size=n)].mean() for _ in range(B)], [2.5, 97.5])


def diff_ci(parts, arm, base, which):
    """arm minus base accuracy over the rooms in `which`, pooled over the (d,) in parts, bootstrap over visits"""
    n = np.concatenate([per_visit(d, arm, which)[0] for d in parts])
    sa = np.concatenate([per_visit(d, arm, which)[1] for d in parts])
    sb = np.concatenate([per_visit(d, base, which)[1] for d in parts])
    keep = n > 0
    n, sa, sb = n[keep], sa[keep], sb[keep]
    if n.sum() == 0:
        return float("nan"), (float("nan"), float("nan"))
    rng = np.random.default_rng(47)
    pt = 100 * (sa.sum() - sb.sum()) / n.sum()
    bs = []
    for _ in range(2000):
        i = rng.integers(len(n), size=len(n))
        bs.append(100 * (sa[i].sum() - sb[i].sum()) / n[i].sum())
    return pt, np.percentile(bs, [2.5, 97.5])


def minutes_diff(d, arm, base="HARD"):
    dm = d[arm]["vmin"] - d[base]["vmin"]
    return float(dm.mean()), boot_mean(dm)


# ---------------------------------------------------------------------------------------------- gates
def gate_g2(n=10):
    bad, tot = 0, 0
    for fam, bld in (("A-LS", "bldg11"), ("B", "bldg15"), ("S3", "demo"), ("S5", "demo")):
        visits, cases, checks = fam_visits(fam, bld, range(n))
        for visit in visits:
            cl = [cases[visit["rooms"][0]]]
            for wi, (wn, a) in enumerate(WORLDS.values()):
                orc = MX.FamOracle(visit, cl, wi, a, checks)
                x, y = F.run_ticket_v(cl, orc, JS, "base"), run_ticket_soft(cl, orc, JS, False)
                tot += 1
                bad += not ([tuple(u) for u in x["guess"]] == [tuple(u) for u in y["guess"]] and [bool(u) for u in x["concluded"]] == [bool(u) for u in y["concluded"]] and x["minutes"] == y["minutes"])
    return bad == 0, f"SOFT equals HARD (guesses, conclusions, minutes) on {tot} single-complaint visit-world runs: {'identical' if not bad else f'{bad} DIFFER'}"


def gate_g3(smoke):
    ok, msg = FM.gate_g3(smoke)                                                    # A-LS, A-FAN, B (bldg15, bldg11), S1-S4 as in FANMIX_NOTES.md
    extra, good = [], True
    f, _ = FM.real("bldg9")
    for vis in fam_visits("B", "bldg9", range(n_visits("B", smoke)))[0]:
        ls = [r for r, c in zip(vis["rooms"], vis["causes"]) if c == LS]
        cases = f.cases
        good &= len(vis["rooms"]) == 6 and len(set(vis["rooms"])) == 6 and ((vis["kind"] == "shared" and vis["k"] in (3, 4, 5) and len(ls) == vis["k"] and all(cases[x].ahu == f.shared_ahu for x in ls)) or (vis["kind"] == "local" and not ls))
    extra.append(f"B bldg9 {'as stated' if good else 'NOT as stated'}")
    g5 = True
    for vis in fam_visits("S5", "demo", range(n_visits("S5", smoke)))[0]:
        sh = [r for r, c in zip(vis["rooms"], vis["causes"]) if c == LS]
        loc = [r for r, c in zip(vis["rooms"], vis["causes"]) if c != LS]
        g5 &= len(sh) in (2, 3) and len(loc) == 2 and all(r in A0 for r in vis["rooms"]) and len(set(vis["rooms"])) == len(vis["rooms"]) and vis["ahu_state"] == {"AHU-0": "low_static", "AHU-1": "ok", "AHU-2": "ok"}
    extra.append(f"S5 {'as stated' if g5 else 'NOT as stated'}")
    return ok and good and g5, msg + "; " + "; ".join(extra)


def gate_g5(n=10):
    diffs = []
    for fam, bld in (("A-LS", "bldg11"), ("B", "bldg15"), ("S5", "demo")):
        visits, cases, checks = fam_visits(fam, bld, range(n))
        for visit in visits:
            cl = [cases[r] for r in visit["rooms"]]
            for wi, (wn, a) in enumerate(WORLDS.values()):
                orc = MX.FamOracle(visit, cl, wi, a, checks)
                run_ticket_soft(cl, orc, JS, False, diag=diffs)
    return bool(diffs) and max(diffs) < 1e-9, f"{len(diffs)} rooms that asked no air-handler check themselves: largest difference between the session's belief and the joint marginal {max(diffs):.1e}"


# ---------------------------------------------------------------------------------------------- the report
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    smoke = args.smoke
    if not smoke and hashlib.sha256(PROTOCOL.read_bytes()).hexdigest() != FROZEN.read_text().split()[0]:
        sys.exit("SOFTCOPY_NOTES.md changed since it was frozen: refusing to run")
    out = Path(args.out) if args.out else OUT
    t0 = time.time()
    g2, g3, g4, g5 = gate_g2(2 if smoke else 10), gate_g3(smoke), FM.gate_g4(), gate_g5(2 if smoke else 10)
    print(f"gates before the run ({time.time() - t0:.0f}s): G2 {g2[0]} | G3 {g3[0]} | G4 {g4[0]} | G5 {g5[0]}", flush=True)
    for g in (g2, g3, g4, g5):
        print("   ", g[1], flush=True)
    step = 4 if smoke else CHUNK
    tasks = []
    for fam, bld in FAMILIES:
        n = n_visits(fam, smoke)
        for w, (wi, _) in WORLDS.items():
            for lo in range(0, n, step):
                tasks.append((fam, bld, wi, lo, min(lo + step, n)))
    results = []
    with ProcessPoolExecutor(max_workers=9) as ex:
        for i, r in enumerate(ex.map(run_chunk, tasks)):
            results.append(r)
            if (i + 1) % 20 == 0 or i + 1 == len(tasks):
                print(f"  {i + 1}/{len(tasks)} chunks, {time.time() - t0:.0f}s", flush=True)
    if smoke:
        print("smoke run: plumbing only, accuracy deliberately not printed")
        return
    wname = {v[0]: k for k, v in WORLDS.items()}
    res = collect([((a[0], a[1], wname[a[2]], a[3], a[4]), o) for a, o in results])
    g1 = {}
    for b in REAL:
        for w in WORLDS:
            st = stats(res["A-LS", b, w], "HARD")
            g1[b, w] = (f"{st['acc']:.1f}" == f"{FM.STORED[b, w][0]:.1f}" and f"{st['minutes']:.0f}" == f"{FM.STORED[b, w][1]:.0f}", st["acc"], st["minutes"])
    gates_ok = all(v[0] for v in g1.values()) and g2[0] and g3[0] and g4[0] and g5[0]
    L = ["# A softer copy between rooms (exploratory; SOFTCOPY_NOTES.md hashed before any run; demos, pilot and shipped defaults untouched)", "",
         "Simulated causes and answers (the visit families are mine); real Mortar layouts for A-LS, A-FAN and B, the first demo's synthetic 3 x 8 building for S1-S5. W0 = checks as the tool assumes, W1 = every rate 25% toward 0.5. "
         "HARD = today's routine (zero-minute certain copies); SOFT = the joint model's belief replaces the copies; JOINT = SOFT with the joint belief also inside a room's own session. "
         "Limit: an own-fault room on a low-static handler reads NORMAL static at its own box in this simulation (answers come from its own cause), so any gain that comes from a room taking its own reading is an upper bound. Nothing committed or deployed.", "",
         "## Gates", "", *[f"- G1 HARD on A-LS reproduces the stored mixed row, {b} {w}: **{'PASS' if v[0] else 'FAIL'}** ({v[1]:.1f}% / {v[2]:.0f} min; stored {FM.STORED[b, w][0]}% / {FM.STORED[b, w][1]})" for (b, w), v in g1.items()],
         f"- G2 {g2[1]}: **{'PASS' if g2[0] else 'FAIL'}**", f"- G3 composition: **{'PASS' if g3[0] else 'FAIL'}** ({g3[1]})", f"- G4 {g4[1]}: **{'PASS' if g4[0] else 'FAIL'}**", f"- G5 {g5[1]}: **{'PASS' if g5[0] else 'FAIL'}**", ""]
    if not gates_ok:
        L += ["**REGISTERED OUTCOME: NO RESULT (a gate failed).**", ""]
    names = {"A-LS": "A-LS: 4 low-static rooms on the larger handler + 2 own-fault rooms on the other", "A-FAN": "A-FAN: 4 fan-off rooms on the larger handler + 2 own-fault rooms on the other (harm check)",
             "B": "B: registered composition (50 shared / 50 local visits; own-fault rooms can sit on the faulty handler)", "S1": "S1: fan off hitting each of 8 rooms at 90% (harm check)",
             "S2": "S2: fan off, 2-4 of 8 rooms complain + 2 own-fault rooms (harm check)", "S3": "S3: low static, 2-4 of 8 rooms + 2 own-fault rooms on AHU-1", "S4": "S4: 6 own-fault rooms, no shared cause",
             "S5": "S5: low static on AHU-0, 2-3 shared rooms + 2 own-fault rooms ALSO on AHU-0 (folding on a small handler)"}
    for fam in ("A-LS", "B", "S5", "S3", "S4", "A-FAN", "S1", "S2"):
        L += [f"## {names[fam]}", "", "| building | answers | arm | accuracy | shared-cause rooms | own-fault rooms elsewhere | folded rooms (own fault on the faulty handler) | folded called low static | minutes / visit | wrong and confident | with the hedge | rooms called confident | vs HARD: accuracy (95% CI); minutes (95% CI) |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for f_, bld in [x for x in FAMILIES if x[0] == fam]:
            for w in WORLDS:
                d = res[fam, bld, w]
                for arm in ARMS:
                    s = stats(d, arm)
                    fo = f"{s['folded']:.1f}% (n={s['n_folded']})" if s["n_folded"] else "-"
                    fl = f"{s['folded_ls']:.0f}%" if s["n_folded"] else "-"
                    if arm == "HARD":
                        dd = ""
                    else:
                        g, gci = diff_ci([d], arm, "HARD", "all")
                        dm, dmci = minutes_diff(d, arm)
                        dd = f"{g:+.1f} ({gci[0]:+.1f}, {gci[1]:+.1f}); {dm:+.0f} ({dmci[0]:+.0f}, {dmci[1]:+.0f})"
                    L.append(f"| {bld} | {w} | {arm} | {s['acc']:.1f}% | {s['shared']:.1f}% | {s['elsewhere']:.1f}% | {fo} | {fl} | {s['minutes']:.0f} | {s['wc']:.1f}% | {s['wc_h']:.1f}% | {s['conc']:.0f}% | {dd} |")
        L.append("")
    # ---- predictions
    R = lambda fam, b, w="W0": res[fam, b, w]                                          # noqa: E731

    def judge(arm):
        q = {}
        pooled, pci = diff_ci([R("B", b) for b in REAL], arm, "HARD", "folded")
        each = {b: diff_ci([R("B", b)], arm, "HARD", "folded")[0] for b in REAL}
        q["Q1"] = (pooled >= 15 and all(v >= 10 for v in each.values()), f"pooled {pooled:+.1f} ({pci[0]:+.1f}, {pci[1]:+.1f}); " + ", ".join(f"{b} {v:+.1f}" for b, v in each.items()))
        s5, s5ci = diff_ci([R("S5", "demo")], arm, "HARD", "folded")
        q["Q2"] = (s5 >= 15, f"S5 folded rooms {s5:+.1f} ({s5ci[0]:+.1f}, {s5ci[1]:+.1f}); HARD {stats(R('S5', 'demo'), 'HARD')['folded']:.1f}%, {arm} {stats(R('S5', 'demo'), arm)['folded']:.1f}%")
        cells = [("B", b) for b in REAL] + [("A-LS", b) for b in REAL] + [("S3", "demo"), ("S4", "demo"), ("S5", "demo")]
        accd = {(f_, b): diff_ci([R(f_, b)], arm, "HARD", "all")[0] for f_, b in cells}
        q["Q3"] = (all(v >= -2 for v in accd.values()), ", ".join(f"{f_} {b} {v:+.1f}" for (f_, b), v in accd.items()))
        tm = {(f_, b): (stats(R(f_, b), arm)["minutes"] - stats(R(f_, b), "HARD")["minutes"], stats(R(f_, b), "HARD")["minutes"]) for f_, b in cells[:6]}
        q["Q4"] = (all(dm <= 0.10 * base for dm, base in tm.values()), ", ".join(f"{f_} {b} {dm:+.0f} on {base:.0f} ({100 * dm / base:+.0f}%)" for (f_, b), (dm, base) in tm.items()))
        wcd = {(f_, b): stats(R(f_, b), arm)["wc"] - stats(R(f_, b), "HARD")["wc"] for f_, b in cells}
        q["Q5"] = (all(v <= 1 for v in wcd.values()) and wcd[("B", "bldg11")] <= -2, ", ".join(f"{f_} {b} {v:+.1f}" for (f_, b), v in wcd.items()) + f"; B bldg11 HARD {stats(R('B', 'bldg11'), 'HARD')['wc']:.1f}% -> {stats(R('B', 'bldg11'), arm)['wc']:.1f}%")
        fo = {(f_, b): diff_ci([R(f_, b)], arm, "HARD", "all")[0] for f_, b in [("A-FAN", x) for x in REAL] + [("S1", "demo"), ("S2", "demo")]}
        q["Q6"] = (all(abs(v) <= 3 for v in fo.values()), ", ".join(f"{f_} {b} {v:+.1f}" for (f_, b), v in fo.items()))
        sd = {b: diff_ci([R("A-LS", b)], arm, "HARD", "shared")[0] for b in REAL}
        q["Q7"] = (all(abs(v) <= 3 for v in sd.values()), ", ".join(f"{b} {v:+.1f}" for b, v in sd.items()))
        return q

    qs, qj = judge("SOFT"), judge("JOINT")
    q8 = {b: stats(R("B", b), "JOINT")["acc"] - stats(R("B", b), "SOFT")["acc"] for b in REAL}
    qs["Q8"] = (all(abs(v) <= 2 for v in q8.values()), ", ".join(f"{b} {v:+.1f}" for b, v in q8.items()))
    text = {"Q1": "folded rooms, B: SOFT +15 pooled and +10 on each building", "Q2": "folded rooms, S5: +15", "Q3": "no accuracy harm (not more than 2 below HARD in B, A-LS, S3, S4, S5)",
            "Q4": "minutes within +10% in B and A-LS", "Q5": "wrong-and-confident at most +1 everywhere and at least 2 below in B bldg11", "Q6": "fan-off families within 3 points",
            "Q7": "A-LS shared rooms within 3 points", "Q8": "JOINT within 2 points of SOFT in B"}
    L += ["## Predictions for SOFT (written before any run)", ""] + [f"- {k} ({text[k]}): **{'HELD' if qs[k][0] else 'FAILED'}** ({qs[k][1]})" for k in sorted(qs)] + [""]
    L += ["## The same predictions for JOINT (Q1-Q7)", ""] + [f"- {k}: **{'HELD' if qj[k][0] else 'FAILED'}** ({qj[k][1]})" for k in sorted(qj)] + [""]

    def label(q):
        if not gates_ok:
            return "NO RESULT (a gate failed)"
        if q["Q1"][0] and q["Q2"][0] and q["Q3"][0] and q["Q4"][0] and q["Q5"][0]:
            return "WORTH ADOPTING"
        if q["Q1"][0] and q["Q2"][0] and not q["Q4"][0] and q["Q3"][0] and q["Q5"][0]:
            return "TRADES ACCURACY FOR TIME"
        if q["Q1"][0] and q["Q2"][0]:
            return "TRADES (a harm check failed" + (", and time" if not q["Q4"][0] else "") + ")"
        return "NO GAIN"
    L += ["## Decision rule applied", "", f"- SOFT: **{label(qs)}**", f"- JOINT: **{label(qj)}**", ""]
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text("\n".join(L))
    (out / "summary.json").write_text(json.dumps(dict(gates_ok=bool(gates_ok), soft=label(qs), joint=label(qj), soft_q={k: bool(v[0]) for k, v in qs.items()}, joint_q={k: bool(v[0]) for k, v in qj.items()},
                                                  protocol_sha256=hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()), indent=1))
    print("\n".join(L))


if __name__ == "__main__":
    main()
