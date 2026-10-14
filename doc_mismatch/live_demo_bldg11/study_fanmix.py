"""A fan-off mixture and a lower end for the low-static mixture, exactly as frozen in FANMIX_NOTES.md (read that first; this file implements it and changes nothing in it).

  .venv/bin/python doc_mismatch/live_demo_bldg11/study_fanmix.py                       # the registered run; refuses to run if FANMIX_NOTES.md changed since it was frozen
  .venv/bin/python doc_mismatch/live_demo_bldg11/study_fanmix.py --smoke --out DIR     # plumbing check (4 visits per family): prints timing and gates only, never accuracy

Outputs (results/docmismatch/fanmix_study/): report.md, summary.json. The Mortar Brick files must be in data_cache/ (not part of the repository); nothing here is committed or deployed.
"""
import argparse
import hashlib
import importlib.util
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
import study_folding as F  # noqa: E402
import study_mix as MX  # noqa: E402
import study_second as SS  # noqa: E402
from docmismatch.troubleshoot.v1 import data as D  # noqa: E402
from docmismatch.troubleshoot.v1.engine import make_case_v1  # noqa: E402
from docmismatch.troubleshoot.v2.joint import JointModel, JointSettings  # noqa: E402

PROTOCOL, FROZEN = HERE / "FANMIX_NOTES.md", HERE / "FANMIX_NOTES.sha256"
OUT = HERE.parent.parent / "results" / "docmismatch" / "fanmix_study"
SERVER = HERE.parent / "live_demo" / "server.py"
MIX = MX.MIX
MIX2 = ((0.02, 0.2), (0.05, 0.2), (0.15, 0.2), (0.5, 0.2), (0.9, 0.2))
ARMS = {"TODAY": JointSettings(low_mix=MIX), "FAN": JointSettings(low_mix=MIX, fan_mix=MIX), "LOW2": JointSettings(low_mix=MIX2), "BOTH": JointSettings(low_mix=MIX2, fan_mix=MIX)}
WORLDS = {"W0": (0, 0.0), "W1": (1, 0.25)}
LS, FAN = ("low_static",), ("ahu_fan_off",)
REAL = ("bldg11", "bldg15", "bldg9")
STORED = {("bldg11", "W0"): (84.4, 188), ("bldg11", "W1"): (60.9, 205), ("bldg15", "W0"): (75.2, 239), ("bldg15", "W1"): (48.5, 245), ("bldg9", "W0"): (81.1, 207), ("bldg9", "W1"): (51.0, 237)}
N_A, N_B, N_S, CHUNK = 200, 100, 100, 20
SMALL = [f"Room-{i}" for i in range(24)]
A0, A1 = SMALL[:8], SMALL[8:16]
FAMILIES = [("A-LS", b) for b in REAL] + [("A-FAN", b) for b in REAL] + [("B", "bldg15"), ("B", "bldg11")] + [(s, "demo") for s in ("S1", "S2", "S3", "S4")]


def n_visits(fam, smoke):
    if smoke:
        return 4
    return N_A if fam.startswith("A-") else N_B


# ---------------------------------------------------------------------------------------------- the first demo's building (cached per process)
_SMALL = {}


def small():
    if not _SMALL:
        spec = importlib.util.spec_from_file_location("first_demo_server", SERVER)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        b = D.load_building_v1(mod.BUILDING)
        ctx = D.Context(instrument="yes", occupant="no", reheat="yes")             # as study_first_demo.py (FIRST_DEMO_DEVIATIONS.md D1)
        cases = {r: make_case_v1(b, r, mod.ITEMS, None, context=ctx, min_rate=mod.MIN_RATE) for r in SMALL}
        _SMALL.update(cases=cases, checks=cases[SMALL[0]].checks)
    return _SMALL["cases"], _SMALL["checks"]


def small_visit(fam, v, cases):
    ci = int(fam[1])
    rng = np.random.default_rng([S.SEED, 5151, ci, v])
    handlers = {"AHU-0": "ok", "AHU-1": "ok", "AHU-2": "ok"}
    items = []
    if ci == 1:                                                                    # the model's own world: each of the 8 rooms complains with probability 0.9, at least 3 do
        while True:
            m = rng.random(8) < 0.9
            if m.sum() >= 3:
                break
        items = [(r, FAN, "shared") for r, c in zip(A0, m) if c]
        handlers["AHU-0"] = "ahu_fan_off"
    elif ci in (2, 3):
        k = (2, 3, 4)[v % 3]
        cause = FAN if ci == 2 else LS
        sh = [A0[i] for i in rng.choice(8, k, replace=False)]
        loc = [A1[i] for i in rng.choice(8, 2, replace=False)]
        items = [(r, cause, "shared") for r in sh] + [(r, FD.own_cause(rng, cases[r]), "local") for r in loc]
        handlers["AHU-0"] = "ahu_fan_off" if ci == 2 else "low_static"
    else:
        rooms = [SMALL[i] for i in rng.choice(24, 6, replace=False)]
        items = [(r, FD.own_cause(rng, cases[r]), "local") for r in rooms]
    items = [items[int(i)] for i in rng.permutation(len(items))]
    return dict(v=50000 + ci * 1000 + v, kind="shared" if ci < 4 else "local", k=sum(1 for i in items if i[2] == "shared"), rooms=[i[0] for i in items], causes=[tuple(i[1]) for i in items],
                seg=[i[2] for i in items], ahu_state=handlers)


# ---------------------------------------------------------------------------------------------- the visits and cases of a family
_COV = {}


def real(name):
    f = MX.fam(name)
    if name not in _COV:
        _COV[name] = SS.covered_rooms(name, f)[0]
    return f, _COV[name]


def fan_visit(v, f, cov):
    vis = dict(SS.demo_visit(v, f, cov, True))
    vis["causes"] = [FAN if s == "shared" else tuple(c) for c, s in zip(vis["causes"], vis["seg"])]
    vis["ahu_state"] = {a: ("ahu_fan_off" if a == f.shared_ahu else "ok") for a in f.handlers}
    return vis


def b_visit(v, f):
    vis = dict(MX.draw_visit_g(v, f))
    vis["seg"] = ["shared" if tuple(c) == LS else "local" for c in vis["causes"]]
    return vis


def family_visits(fam, bld, vs):
    """-> (visits, cases by room, checks)"""
    if fam.startswith("S"):
        cases, checks = small()
        return [small_visit(fam, v, cases) for v in vs], cases, checks
    f, cov = real(bld)
    if fam == "A-LS":
        return [SS.demo_visit(v, f, cov, True) for v in vs], f.cases, f.checks
    if fam == "A-FAN":
        return [fan_visit(v, f, cov) for v in vs], f.cases, f.checks
    return [b_visit(v, f) for v in vs], f.cases, f.checks


# ---------------------------------------------------------------------------------------------- the runs
def run_chunk(args):
    fam, bld, wi, lo, hi = args
    visits, cases, checks = family_visits(fam, bld, range(lo, hi))
    a = list(WORLDS.values())[wi][1]
    out = []
    for visit in visits:
        cl = [cases[r] for r in visit["rooms"]]
        orc = MX.FamOracle(visit, cl, wi, a, checks)
        rec = {}
        for arm, js in ARMS.items():
            r = F.run_ticket_v(cl, orc, js, "base")
            rec[arm] = dict(guess=[tuple(g) for g in r["guess"]], conc=[bool(c) for c in r["concluded"]], own=[bool(x) for x in r["own_static"]], minutes=float(r["minutes"]))
        out.append((visit, rec))
    return args, out


def collect(results):
    """-> {(fam, bld, world): {arm: arrays}} with rooms in visit order"""
    by = {}
    for args, out in results:
        by.setdefault((args[0], args[1], args[2]), []).append((args[3], out))
    res = {}
    for key, chunks in by.items():
        pairs = [p for _, out in sorted(chunks, key=lambda c: c[0]) for p in out]
        d = {"visits": [p[0] for p in pairs]}
        truth = [tuple(c) for p in pairs for c in p[0]["causes"]]
        seg = np.array([s for p in pairs for s in p[0]["seg"]])
        d["truth"], d["seg"] = truth, seg
        d["visit"] = np.array([i for i, p in enumerate(pairs) for _ in p[0]["rooms"]])
        for arm in ARMS:
            g = [tuple(x) for p in pairs for x in p[1][arm]["guess"]]
            d[arm] = dict(guess=g, ok=np.array([x == t for x, t in zip(g, truth)]), conc=np.array([c for p in pairs for c in p[1][arm]["conc"]]),
                          own=np.array([c for p in pairs for c in p[1][arm]["own"]]), vmin=np.array([p[1][arm]["minutes"] for p in pairs]))
        res[key] = d
    return res


def stats(d, arm, mask=None):
    x = d[arm]
    m = np.ones(len(x["ok"]), bool) if mask is None else mask
    truth_fan = np.array([t == FAN for t in d["truth"]])
    guess_ls = np.array([g == LS for g in x["guess"]]); guess_fan = np.array([g == FAN for g in x["guess"]])
    hedged = x["conc"] & guess_ls & ~x["own"]
    sh, lo = d["seg"] == "shared", d["seg"] != "shared"
    return dict(acc=100 * x["ok"][m].mean(), shared=100 * x["ok"][m & sh].mean() if (m & sh).any() else float("nan"), local=100 * x["ok"][m & lo].mean() if (m & lo).any() else float("nan"),
                minutes=float(x["vmin"].mean()), wc=100 * ((~x["ok"]) & x["conc"])[m].mean(), wc_h=100 * ((~x["ok"]) & x["conc"] & ~hedged)[m].mean(), false_fan=100 * (guess_fan & ~truth_fan)[m].mean(),
                fan_as_ls=100 * guess_ls[m & truth_fan].mean() if (m & truth_fan).any() else float("nan"), fan_right=100 * guess_fan[m & truth_fan].mean() if (m & truth_fan).any() else float("nan"))


def boot(x, B=2000, seed=37):
    rng = np.random.default_rng(seed)
    n = len(x)
    return np.percentile([x[rng.integers(n, size=n)].mean() for _ in range(B)], [2.5, 97.5])


def paired(d, arm, base="TODAY", which="all"):
    """arm minus base: accuracy (pooled over the rooms in `which`, bootstrap over visits) and minutes per visit"""
    nv = len(d["visits"])
    mask = np.ones(len(d["seg"]), bool) if which == "all" else (d["seg"] == "shared") if which == "shared" else (d["seg"] != "shared")
    n = np.array([mask[d["visit"] == v].sum() for v in range(nv)], float)
    s_a = np.array([d[arm]["ok"][(d["visit"] == v) & mask].sum() for v in range(nv)], float)
    s_b = np.array([d[base]["ok"][(d["visit"] == v) & mask].sum() for v in range(nv)], float)
    rng = np.random.default_rng(41)
    pt = 100 * (s_a.sum() - s_b.sum()) / n.sum()
    bs = []
    for _ in range(2000):
        i = rng.integers(nv, size=nv)
        bs.append(100 * (s_a[i].sum() - s_b[i].sum()) / n[i].sum())
    dm = d[arm]["vmin"] - d[base]["vmin"]
    return pt, np.percentile(bs, [2.5, 97.5]), float(dm.mean()), boot(dm)


# ---------------------------------------------------------------------------------------------- gates
def gate_g2(n=10):
    one = JointSettings(low_mix=MIX, fan_mix=((0.9, 1.0),))
    bad, tot = 0, 0
    for fam, bld in (("A-LS", "bldg11"), ("A-FAN", "bldg11"), ("S2", "demo")):
        visits, cases, checks = family_visits(fam, bld, range(n))
        for visit in visits:
            cl = [cases[r] for r in visit["rooms"]]
            for wi, (wn, a) in enumerate(WORLDS.values()):
                orc = MX.FamOracle(visit, cl, wi, a, checks)
                x, y = F.run_ticket_v(cl, orc, ARMS["TODAY"], "base"), F.run_ticket_v(cl, orc, one, "base")
                tot += 1
                bad += not ([tuple(u) for u in x["guess"]] == [tuple(u) for u in y["guess"]] and [bool(u) for u in x["concluded"]] == [bool(u) for u in y["concluded"]] and x["minutes"] == y["minutes"])
    return bad == 0, f"a one-level fan mixture at 0.9 gives TODAY's guesses, conclusions and minutes on {tot} visit-world runs: {'identical' if not bad else f'{bad} DIFFER'}"


def gate_g3(smoke):
    msgs, ok = [], True
    for fam, bld in FAMILIES:
        vs = range(n_visits(fam, smoke))
        visits, cases, checks = family_visits(fam, bld, vs)
        good = True
        for vis in visits:
            rooms, causes, seg = vis["rooms"], [tuple(c) for c in vis["causes"]], vis.get("seg")
            st = vis["ahu_state"]
            if fam in ("A-LS", "A-FAN"):
                f, cov = real(bld)
                cause = LS if fam == "A-LS" else FAN
                sh = [r for r, c in zip(rooms, causes) if c == cause]
                oth = [(r, c) for r, c in zip(rooms, causes) if c != cause]
                other = vis["other"]
                good &= (len(set(rooms)) == 6 and len(sh) == 4 and all(cases[r].ahu == f.shared_ahu and r in cov for r in sh) and len(oth) == 2 and all(cases[r].ahu == other and r in cov for r, _ in oth)
                         and st[f.shared_ahu] == ("low_static" if fam == "A-LS" else "ahu_fan_off") and all(v == "ok" for a, v in st.items() if a != f.shared_ahu)
                         and sorted(c[0] for _, c in oth).count("actuator_fail") == 1 and sum(1 for _, c in oth if c[0] == "wrong") == 1)
            elif fam == "B":
                f, _ = real(bld)
                ls = [r for r, c in zip(rooms, causes) if c == LS]
                good &= len(rooms) == 6 and len(set(rooms)) == 6 and ((vis["kind"] == "shared" and vis["k"] in (3, 4, 5) and len(ls) == vis["k"] and all(cases[x].ahu == f.shared_ahu for x in ls)) or (vis["kind"] == "local" and not ls))
            elif fam == "S1":
                good &= len(rooms) >= 3 and all(r in A0 for r in rooms) and all(c == FAN for c in causes) and st["AHU-0"] == "ahu_fan_off" and len(set(rooms)) == len(rooms)
            elif fam in ("S2", "S3"):
                cause = FAN if fam == "S2" else LS
                sh = [r for r, c in zip(rooms, causes) if c == cause]
                loc = [r for r, c in zip(rooms, causes) if c != cause]
                good &= (len(sh) in (2, 3, 4) and all(r in A0 for r in sh) and len(loc) == 2 and all(r in A1 for r in loc) and len(set(rooms)) == len(rooms)
                         and st["AHU-0"] == ("ahu_fan_off" if fam == "S2" else "low_static") and st["AHU-1"] == "ok" and st["AHU-2"] == "ok")
            else:
                good &= len(rooms) == 6 and len(set(rooms)) == 6 and all(c not in (LS, FAN) for c in causes) and all(v == "ok" for v in st.values())
        ok &= good
        msgs.append(f"{fam} {bld}: {len(visits)} visits {'as stated' if good else 'NOT as stated'}")
    return ok, "; ".join(msgs)


def gate_g4():
    f, cov = real("bldg11")
    vis = fan_visit(3, f, cov)
    cl = [f.cases[r] for r in vis["rooms"]]
    qs = [(i, ck, cl[i].doc) for i in range(len(cl)) for ck in f.checks if ck.subject != "ahu" and ck.is_reading]
    o1, o2 = MX.FamOracle(vis, cl, 0, 0.0, f.checks), MX.FamOracle(vis, cl, 0, 0.0, f.checks)
    fwd = [o1.ask_room(*q) for q in qs]
    rev = [o2.ask_room(*q) for q in reversed(qs)][::-1]
    ahu = [o1.ask_ahu(f.shared_ahu, ck) for ck in f.checks if ck.subject == "ahu" and ck.is_reading]
    return fwd == rev and bool(ahu), f"{len(qs)} room questions of an A-FAN visit forward and backward: {'identical' if fwd == rev else 'DIFFERENT'}; {len(ahu)} air-handler questions answered in vocabulary"


def gate_g5():
    f, cov = real("bldg11")
    vis = fan_visit(0, f, cov)
    cl = [f.cases[r] for r in vis["rooms"]]
    out = {}
    for arm in ("TODAY", "FAN"):
        m = JointModel(cl, ARMS[arm])
        out[arm] = m.ahu_posterior_by_cause(m.initial())[f.shared_ahu]["ahu_fan_off"]
    n = f.sizes[f.shared_ahu]
    return out["TODAY"] < 1e-30 and out["FAN"] > 3e-3, f"fan-off prior at 4 complaints of {n} rooms (bldg11): TODAY {out['TODAY']:.2e}, FAN {out['FAN']:.2e}"


# ---------------------------------------------------------------------------------------------- the report
def fmt_diff(d, arm):
    g, gci, dm, dmci = paired(d, arm)
    return f"{g:+.1f} ({gci[0]:+.1f}, {gci[1]:+.1f}); {dm:+.0f} ({dmci[0]:+.0f}, {dmci[1]:+.0f})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    smoke = args.smoke
    if not smoke and hashlib.sha256(PROTOCOL.read_bytes()).hexdigest() != FROZEN.read_text().split()[0]:
        sys.exit("FANMIX_NOTES.md changed since it was frozen: refusing to run")
    out = Path(args.out) if args.out else OUT
    t0 = time.time()
    g2, g3, g4, g5 = gate_g2(2 if smoke else 10), gate_g3(smoke), gate_g4(), gate_g5()
    print(f"gates before the run ({time.time() - t0:.0f}s): G2 {g2[0]} | G3 {g3[0]} | G4 {g4[0]} | G5 {g5[0]}", flush=True)
    for g in (g2, g3, g4, g5):
        print("   ", g[1], flush=True)
    tasks = []
    for fam, bld in FAMILIES:
        n = n_visits(fam, smoke)
        for w, (wi, _) in WORLDS.items():
            for lo in range(0, n, CHUNK if not smoke else 4):
                tasks.append((fam, bld, w, lo, min(lo + (CHUNK if not smoke else 4), n)))
    tasks_w = [(f, b, WORLDS[w][0], lo, hi) for f, b, w, lo, hi in tasks]
    results = []
    with ProcessPoolExecutor(max_workers=9) as ex:
        for i, r in enumerate(ex.map(run_chunk, tasks_w)):
            results.append(r)
            if (i + 1) % 20 == 0 or i + 1 == len(tasks_w):
                print(f"  {i + 1}/{len(tasks_w)} chunks, {time.time() - t0:.0f}s", flush=True)
    if smoke:
        print("smoke run: plumbing only, accuracy deliberately not printed")
        return
    wname = {v[0]: k for k, v in WORLDS.items()}
    res = collect([((a[0], a[1], wname[a[2]], a[3], a[4]), o) for a, o in results])
    g1 = {}
    for b in REAL:
        for w in WORLDS:
            st = stats(res["A-LS", b, w], "TODAY")
            g1[b, w] = (f"{st['acc']:.1f}" == f"{STORED[b, w][0]:.1f}" and f"{st['minutes']:.0f}" == f"{STORED[b, w][1]:.0f}", st["acc"], st["minutes"])
    gates_ok = all(v[0] for v in g1.values()) and g2[0] and g3[0] and g4[0] and g5[0]

    def S_(fam, bld, w, arm, mask=None):
        return stats(res[fam, bld, w], arm, mask)

    def P_(fam, bld, w, arm, which="all"):
        return paired(res[fam, bld, w], arm, "TODAY", which)

    L = ["# A fan-off mixture and a lower end for the low-static mixture (exploratory; FANMIX_NOTES.md hashed before any run; demos, pilot and shipped defaults untouched)", "",
         "Simulated causes and answers (the visit families are mine); real Mortar layouts for A-LS, A-FAN and B, the first demo's synthetic 3 x 8 building for S1-S4. W0 = checks as the tool assumes, W1 = every rate 25% toward 0.5. "
         "Arms: TODAY = low-static mixture 5/15/50/90%; FAN = TODAY + fan-off mixture 5/15/50/90%; LOW2 = low-static mixture 2/5/15/50/90%; BOTH. Nothing committed or deployed.", "", "## Gates", "",
         *[f"- G1 TODAY on A-LS reproduces the stored mixed row, {b} {w}: **{'PASS' if v[0] else 'FAIL'}** ({v[1]:.1f}% / {v[2]:.0f} min; stored {STORED[b, w][0]}% / {STORED[b, w][1]})" for (b, w), v in g1.items()],
         f"- G2 {g2[1]}: **{'PASS' if g2[0] else 'FAIL'}**", f"- G3 composition: **{'PASS' if g3[0] else 'FAIL'}** ({g3[1]})", f"- G4 {g4[1]}: **{'PASS' if g4[0] else 'FAIL'}**", f"- G5 {g5[1]}: **{'PASS' if g5[0] else 'FAIL'}**", ""]
    if not gates_ok:
        L += ["**REGISTERED OUTCOME: NO RESULT (a gate failed).**", ""]
    names = {"A-LS": "A-LS: 4 low-static rooms on the larger handler + 2 own-fault rooms", "A-FAN": "A-FAN: 4 fan-off rooms on the larger handler + 2 own-fault rooms", "B": "B: registered composition (50 shared / 50 local visits)",
             "S1": "S1: fan off, the model's own world (each of 8 rooms complains at 90%)", "S2": "S2: fan off, 2-4 of 8 rooms complain + 2 own-fault rooms", "S3": "S3: low static, 2-4 of 8 rooms complain + 2 own-fault rooms", "S4": "S4: 6 own-fault rooms, no shared cause"}
    for fam in ("A-LS", "A-FAN", "B", "S1", "S2", "S3", "S4"):
        L += [f"## {names[fam]}", "", "| building | answers | arm | accuracy | shared-cause rooms | own-fault rooms | minutes / visit | wrong and confident | with the hedge | false fan-off | shared-cause rooms called fan off / low static | vs TODAY: accuracy (95% CI); minutes (95% CI) |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for fb, bld in [x for x in FAMILIES if x[0] == fam]:
            for w in WORLDS:
                for arm in ARMS:
                    s = S_(fam, bld, w, arm)
                    L.append(f"| {bld} | {w} | {arm} | {s['acc']:.1f}% | {s['shared']:.1f}% | {s['local']:.1f}% | {s['minutes']:.0f} | {s['wc']:.1f}% | {s['wc_h']:.1f}% | {s['false_fan']:.1f}% | "
                             + (f"{s['fan_right']:.0f}% / {s['fan_as_ls']:.0f}%" if fam in ("A-FAN", "S1", "S2") else "-") + " | " + ("" if arm == "TODAY" else fmt_diff(res[fam, bld, w], arm)) + " |")
        L.append("")
    # ---- predictions
    def shared_diff(fam, bld, w, arm="FAN"):
        return P_(fam, bld, w, arm, "shared")[0]

    P = []
    P.append(("P1 (A-FAN: under TODAY the 4 fan-off rooms are right at most 20% on each building)", all(S_("A-FAN", b, "W0", "TODAY")["shared"] <= 20 for b in REAL), ", ".join(f"{b} {S_('A-FAN', b, 'W0', 'TODAY')['shared']:.1f}%" for b in REAL)))
    P.append(("P2 (A-FAN: FAN raises the fan-off rooms by at least 25 points on each building)", all(shared_diff("A-FAN", b, "W0") >= 25 for b in REAL), ", ".join(f"{b} {shared_diff('A-FAN', b, 'W0'):+.1f} ({S_('A-FAN', b, 'W0', 'FAN')['shared']:.1f}%)" for b in REAL)))
    p3a, p3b = S_("S2", "demo", "W0", "TODAY")["shared"], shared_diff("S2", "demo", "W0")
    P.append(("P3 (S2: TODAY at most 20% on the fan-off rooms and FAN +25 or more)", p3a <= 20 and p3b >= 25, f"TODAY {p3a:.1f}%, FAN {p3b:+.1f} ({S_('S2', 'demo', 'W0', 'FAN')['shared']:.1f}%)"))
    s1d, s1m = P_("S1", "demo", "W0", "FAN"), S_("S1", "demo", "W0", "TODAY")["minutes"]
    P.append(("P4 (S1, the model's own world: FAN within 3 points and 5% of minutes of TODAY)", abs(s1d[0]) <= 3 and abs(s1d[2]) <= 0.05 * s1m, f"{s1d[0]:+.1f} points ({s1d[1][0]:+.1f}, {s1d[1][1]:+.1f}); {s1d[2]:+.1f} min on {s1m:.0f}"))
    harm_cells = [("A-LS", b) for b in REAL] + [("S3", "demo"), ("S4", "demo"), ("B", "bldg15"), ("B", "bldg11")]
    hf = []
    for fam, bld in harm_cells:
        d = P_(fam, bld, "W0", "FAN")
        wc = S_(fam, bld, "W0", "FAN")["wc"] - S_(fam, bld, "W0", "TODAY")["wc"]
        ff = S_(fam, bld, "W0", "FAN")["false_fan"]
        hf.append((fam, bld, abs(d[0]) <= 3 and wc <= 1 and ff <= 2, f"{fam} {bld}: {d[0]:+.1f} pts, wc {wc:+.1f}, false fan-off {ff:.1f}%"))
    P.append(("P5 (harm cells: FAN within 3 points, wrong-and-confident at most +1, false fan-off at most 2%)", all(h[2] for h in hf), "; ".join(h[3] for h in hf)))
    g6 = [shared_diff("A-FAN", b, "W1") for b in REAL] + [shared_diff("S2", "demo", "W1")]
    P.append(("P6 (W1: the fan-off gains of P2 and P3 are still at least 15 points)", all(x >= 15 for x in g6), ", ".join(f"{x:+.1f}" for x in g6)))
    p7 = P_("A-LS", "bldg15", "W0", "LOW2")
    P.append(("P7 (A-LS bldg15: LOW2 +3 or more with the CI above 0, shared rooms at least 85%)", p7[0] >= 3 and p7[1][0] > 0 and S_("A-LS", "bldg15", "W0", "LOW2")["shared"] >= 85,
              f"{p7[0]:+.1f} ({p7[1][0]:+.1f}, {p7[1][1]:+.1f}); shared {S_('A-LS', 'bldg15', 'W0', 'LOW2')['shared']:.1f}% (TODAY {S_('A-LS', 'bldg15', 'W0', 'TODAY')['shared']:.1f}%)"))
    p8 = {b: P_("A-LS", b, "W0", "LOW2")[0] for b in ("bldg11", "bldg9")}
    P.append(("P8 (A-LS bldg11, bldg9: LOW2 within 3 points of TODAY)", all(abs(v) <= 3 for v in p8.values()), ", ".join(f"{b} {v:+.1f}" for b, v in p8.items())))
    p9 = {f: P_(f, "demo", "W0", "LOW2")[0] for f in ("S1", "S2", "S3", "S4")}
    P.append(("P9 (S1-S4: LOW2 within 3 points of TODAY)", all(abs(v) <= 3 for v in p9.values()), ", ".join(f"{f} {v:+.1f}" for f, v in p9.items())))
    p10 = {b: (P_("B", b, "W0", "LOW2")[0], S_("B", b, "W0", "LOW2")["wc"] - S_("B", b, "W0", "TODAY")["wc"]) for b in ("bldg15", "bldg11")}
    P.append(("P10 (B: LOW2 within 3 points of TODAY and wrong-and-confident at most +1)", all(abs(v[0]) <= 3 and v[1] <= 1 for v in p10.values()), ", ".join(f"{b} {v[0]:+.1f} pts, wc {v[1]:+.1f}" for b, v in p10.items())))
    p11 = [(f"A-FAN {b}", S_("A-FAN", b, "W0", "BOTH")["acc"] - max(S_("A-FAN", b, "W0", "FAN")["acc"], S_("A-FAN", b, "W0", "LOW2")["acc"])) for b in REAL]
    p11.append(("A-LS bldg15", S_("A-LS", "bldg15", "W0", "BOTH")["acc"] - max(S_("A-LS", "bldg15", "W0", "FAN")["acc"], S_("A-LS", "bldg15", "W0", "LOW2")["acc"])))
    P.append(("P11 (BOTH not more than 2 points below the better single change in A-FAN and A-LS bldg15)", all(v >= -2 for _, v in p11), ", ".join(f"{n} {v:+.1f}" for n, v in p11)))
    L += ["## Predictions (written before any run)", ""] + [f"- {p}: **{'HELD' if ok else 'FAILED'}** ({d})" for p, ok, d in P] + [""]
    held = {p[0].split(" ")[0]: p[1] for p in P}
    fan_ok = all(held[k] for k in ("P2", "P3", "P4", "P5"))
    low_ok = all(held[k] for k in ("P7", "P8", "P9", "P10"))
    fan_lab = "WORTH ADOPTING" if fan_ok else "NO GAIN" if not (held["P2"] and held["P3"]) else "TRADES (a neutrality or harm check failed)"
    low_lab = "WORTH ADOPTING" if low_ok else "NO GAIN" if not held["P7"] else "TRADES (a neutrality or harm check failed)"
    L += ["## Decision rule applied", "", f"- FAN (fan-off mixture): **{fan_lab}**" if gates_ok else "- FAN: NO RESULT (a gate failed)", f"- LOW2 (lower end): **{low_lab}**" if gates_ok else "- LOW2: NO RESULT (a gate failed)", ""]
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text("\n".join(L))
    (out / "summary.json").write_text(json.dumps(dict(gates_ok=bool(gates_ok), fan=fan_lab, low2=low_lab, predictions={p[0].split(" ")[0]: bool(p[1]) for p in P}, protocol_sha256=hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()), indent=1))
    print("\n".join(L))


if __name__ == "__main__":
    main()
