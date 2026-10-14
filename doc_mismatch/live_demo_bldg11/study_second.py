"""Mixed against shipped on a second scenario of similar complexity (EXPLORATORY; SECOND_NOTES.md was written and hashed before any run; no new demo or UI).

  .venv/bin/python doc_mismatch/live_demo_bldg11/study_second.py        -> results/docmismatch/second_scenario/report.md

Needs the Mortar Brick files in data_cache/ (not part of the repository; nothing here is committed or deployed).
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_building as BB  # noqa: E402
import simulate as S  # noqa: E402
import study_folding as F  # noqa: E402
import study_mix as MX  # noqa: E402
from docmismatch.troubleshoot.v2.joint import JointSettings  # noqa: E402

OUT = HERE.parent.parent / "results" / "docmismatch" / "second_scenario"
MX.FAMS["bldg15"] = dict(ahus=None, salt=(15,), voff=15000, arms=("default", "mix"))
MX.FAMS["bldg9"] = dict(ahus=None, salt=(9,), voff=9000, arms=("default", "mix"))
JS = {"shipped": JointSettings(), "mixed": JointSettings(low_mix=MX.MIX)}
WORLDS = {"W0": (0, 0.0), "W1": (1, 0.25)}
LS = ("low_static",)
REF = {("W0", "shipped"): (23.8, 332), ("W0", "mixed"): (84.2, 190), ("W1", "shipped"): (11.2, 303), ("W1", "mixed"): (60.2, 200)}      # demo_composition.py, bldg11, 200 visits
N_A, N_B = 200, 100


def covered_rooms(name, f):
    raw = json.loads(BB.ensure_building(name, f.spec["ahus"]).read_text())
    pts, claims = raw["control_system"]["points"], raw["claims"]["vav_zone"]
    return {room for room, box in claims.items() if {"airflow", "damper", "reheat"} <= set(pts.get(box, {})) and "temperature" in pts.get(room, {})}, raw


def demo_visit(v, f, covered, restrict):
    rng = np.random.default_rng([S.SEED, 777, *f.spec["salt"], v])
    big = f.shared_ahu
    other = sorted((a for a in f.handlers if a != big), key=lambda a: (-f.sizes[a], a))[0]
    pool_big = sorted(r for r in f.cases if f.cases[r].ahu == big and (not restrict or r in covered))
    pool_oth = sorted(r for r in f.cases if f.cases[r].ahu == other and (not restrict or r in covered))
    sh = [pool_big[i] for i in rng.choice(len(pool_big), 4, replace=False)]
    act, wrong = [pool_oth[i] for i in rng.choice(len(pool_oth), 2, replace=False)]
    alts = f.cases[wrong].candidates[1:]
    items = [(r, LS, "shared") for r in sh] + [(act, ("actuator_fail",), "local"), (wrong, ("wrong", alts[int(rng.integers(len(alts)))]), "local")]
    items = [items[int(i)] for i in rng.permutation(len(items))]
    return dict(v=v + f.spec["voff"], kind="shared", k=4, rooms=[i[0] for i in items], causes=[i[1] for i in items], seg=[i[2] for i in items],
                ahu_state={a: ("low_static" if a == big else "ok") for a in f.handlers}, other=other)


def run(f, visits, js, wi, a):
    ok, conc, ls, own, seg, vix, vmin = [], [], [], [], [], [], []
    for i, visit in enumerate(visits):
        cl = [f.cases[r] for r in visit["rooms"]]
        orc = MX.FamOracle(visit, cl, wi, a, f.checks)
        r = F.run_ticket_v(cl, orc, js, "base")
        truth = [tuple(c) for c in visit["causes"]]
        ok += [tuple(g) == t for g, t in zip(r["guess"], truth)]; conc += r["concluded"]
        ls += [tuple(g) == LS for g in r["guess"]]; own += r["own_static"]; vix += [i] * len(cl); vmin.append(r["minutes"])
        if "seg" in visit:
            seg += visit["seg"]
        else:
            for room, t in zip(visit["rooms"], truth):
                seg.append("shared" if t == LS else "local on the faulty handler" if (visit["kind"] == "shared" and f.cases[room].ahu == f.shared_ahu) else "local elsewhere")
    return dict(ok=np.array(ok), conc=np.array(conc), ls=np.array(ls), own=np.array(own), seg=np.array(seg), visit=np.array(vix), vmin=np.array(vmin))


def boot(d, B=2000, seed=29):
    rng = np.random.default_rng(seed); n = len(d)
    return np.percentile([d[rng.integers(n, size=n)].mean() for _ in range(B)], [2.5, 97.5])


def stats(d, n_rooms=6):
    hedged = d["conc"] & d["ls"] & ~d["own"]
    wrong = ~d["ok"]
    allsix = np.array([d["ok"][d["visit"] == v].all() for v in range(len(d["vmin"]))])
    return dict(acc=100 * d["ok"].mean(), shared=100 * d["ok"][d["seg"] == "shared"].mean() if (d["seg"] == "shared").any() else float("nan"),
                local=100 * d["ok"][d["seg"] == "local"].mean() if (d["seg"] == "local").any() else float("nan"),
                faulty=100 * d["ok"][d["seg"] == "local on the faulty handler"].mean() if (d["seg"] == "local on the faulty handler").any() else float("nan"),
                allsix=100 * allsix.mean(), minutes=float(d["vmin"].mean()), wc=100 * (wrong & d["conc"]).mean(), wc_h=100 * (wrong & d["conc"] & ~hedged).mean(),
                hedged=int(hedged.sum()), hedged_right=int((hedged & d["ok"]).sum()), conc=100 * d["conc"].mean())


def paired(a, b):
    """b minus a, per visit"""
    va = np.array([a["ok"][a["visit"] == v].mean() for v in range(len(a["vmin"]))]); vb = np.array([b["ok"][b["visit"] == v].mean() for v in range(len(b["vmin"]))])
    g = 100 * (vb - va); dm = b["vmin"] - a["vmin"]
    return g.mean(), boot(g), dm.mean(), boot(dm)


def main():
    fams = {n: MX.fam(n) for n in ("bldg11", "bldg15", "bldg9")}
    cov = {n: covered_rooms(n, fams[n])[0] for n in fams}
    L = ["# Mixed against shipped on a second scenario of similar complexity (exploratory; SECOND_NOTES.md hashed before any run; no new demo or UI)", "",
         "Real Mortar layouts, recorded points only; simulated causes and answers; nothing committed or deployed. W0 = checks as the tool assumes, W1 = every rate 25% toward 0.5.", "",
         "| building | handlers (boxes) | boxes with airflow, damper, reheat and a zone temperature |", "|---|---|---|"]
    for n, f in fams.items():
        L.append(f"| {n} | " + ", ".join(f"{a} ({f.sizes[a]})" for a in f.handlers) + f" | " + ", ".join(f"{a} {sum(1 for r in cov[n] if f.cases[r].ahu == a)}" for a in f.handlers) + " |")
    # ---- gate G1: bldg11, unrestricted draw, reproduces demo_composition.py
    f11 = fams["bldg11"]
    vis_g = [demo_visit(v, f11, cov["bldg11"], False) for v in range(N_A)]
    g1 = {}
    for w, (wi, a) in WORLDS.items():
        for s in JS:
            d = run(f11, vis_g, JS[s], wi, a); st = stats(d)
            g1[w, s] = (f"{st['acc']:.1f}" == f"{REF[w, s][0]:.1f}" and f"{st['minutes']:.0f}" == f"{REF[w, s][1]:.0f}", st["acc"], st["minutes"])      # as printed by the earlier run (SECOND_DEVIATIONS.md D1)
    # ---- scenario A
    resA, vis_chk = {}, True
    for n, f in fams.items():
        visits = [demo_visit(v, f, cov[n], True) for v in range(N_A)]
        for vv in visits:                                                       # G2
            rooms = vv["rooms"]
            ok2 = len(set(rooms)) == 6 and sum(1 for r, s in zip(rooms, vv["seg"]) if s == "shared" and f.cases[r].ahu == f.shared_ahu and r in cov[n]) == 4 \
                and all(r in cov[n] and f.cases[r].ahu == vv["other"] for r, s in zip(rooms, vv["seg"]) if s == "local")
            vis_chk &= bool(ok2)
        for w, (wi, a) in WORLDS.items():
            runs = {s: run(f, visits, JS[s], wi, a) for s in JS}
            resA[n, w] = dict(runs=runs, st={s: stats(runs[s]) for s in JS}, diff=paired(runs["shipped"], runs["mixed"]))
    # ---- scenario B
    resB = {}
    for n in ("bldg15", "bldg9"):
        f = fams[n]
        visits = [MX.draw_visit_g(v, f) for v in range(N_B)]
        for w, (wi, a) in WORLDS.items():
            runs = {s: run(f, visits, JS[s], wi, a) for s in JS}
            resB[n, w] = dict(st={s: stats(runs[s]) for s in JS}, diff=paired(runs["shipped"], runs["mixed"]))
    gates = all(v[0] for v in g1.values()) and vis_chk
    L += ["", "## Gates", "", *[f"- G1 bldg11, unrestricted draw, reproduces the earlier demo-shaped run, {w} {s}: **{'PASS' if v[0] else 'FAIL'}** ({v[1]:.1f}% / {v[2]:.0f} min; earlier {REF[w, s][0]}% / {REF[w, s][1]})" for (w, s), v in g1.items()],
          f"- G2 every Scenario A visit: six distinct rooms, four low-static rooms on the larger handler, one actuator failure and one wrong box on the other, all with the required points: **{'PASS' if vis_chk else 'FAIL'}**", "- G3 every answer in the check's vocabulary: asserted by the oracle", ""]
    if not gates:
        L += ["**REGISTERED OUTCOME: NO RESULT (a gate failed).**", ""]
    L += ["## Scenario A: demo-shaped visits (200 per building; per room unless stated)", "",
          "| building | answers | setting | accuracy | the 4 shared rooms | the 2 own-fault rooms | all six right | minutes / visit | wrong and confident | with the hedge | mixed minus shipped: accuracy (95% CI), minutes (95% CI) |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for n in fams:
        for w in WORLDS:
            r = resA[n, w]; g, gci, dm, dmci = r["diff"]
            for s in JS:
                st = r["st"][s]
                L.append(f"| {n}{' (restricted draw)' if n == 'bldg11' else ''} | {w} | {s} | {st['acc']:.1f}% | {st['shared']:.1f}% | {st['local']:.1f}% | {st['allsix']:.0f}% | {st['minutes']:.0f} | {st['wc']:.1f}% | {st['wc_h']:.1f}% | " + (f"{g:+.1f} ({gci[0]:+.1f}, {gci[1]:+.1f}); {dm:+.0f} ({dmci[0]:+.0f}, {dmci[1]:+.0f})" if s == "mixed" else "") + " |")
    L += ["", "## Scenario B: the registered composition (100 visits per building; per room)", "",
          "| building | answers | setting | accuracy | shared rooms | own fault on the faulty handler | wrong and confident | with the hedge | rooms called confident | hedged conclusions (right) | minutes / visit | mixed minus shipped: accuracy (95% CI), minutes |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for n in ("bldg15", "bldg9"):
        for w in WORLDS:
            r = resB[n, w]; g, gci, dm, dmci = r["diff"]
            for s in JS:
                st = r["st"][s]
                L.append(f"| {n} | {w} | {s} | {st['acc']:.1f}% | {st['shared']:.1f}% | {st['faulty']:.1f}% | {st['wc']:.1f}% | {st['wc_h']:.1f}% | {st['conc']:.0f}% | {st['hedged']} ({st['hedged_right']}) | {st['minutes']:.0f} | " + (f"{g:+.1f} ({gci[0]:+.1f}, {gci[1]:+.1f}); {dm:+.0f}" if s == "mixed" else "") + " |")
    A15, A9, A11 = resA["bldg15", "W0"], resA["bldg9", "W0"], resA["bldg11", "W0"]
    B15, B9 = resB["bldg15", "W0"], resB["bldg9", "W0"]
    P = [("P1 (bldg15 A, W0: mixed beats shipped by at least 20 points per room and uses at least 20% fewer minutes)", A15["diff"][0] >= 20 and A15["diff"][2] <= -0.2 * A15["st"]["shipped"]["minutes"], f"{A15['diff'][0]:+.1f} points, {A15['diff'][2]:+.0f} min on {A15['st']['shipped']['minutes']:.0f}"),
         ("P2 (bldg15 A, W0: shared rooms at least 85% under mixed, at most 10% under shipped)", A15["st"]["mixed"]["shared"] >= 85 and A15["st"]["shipped"]["shared"] <= 10, f"mixed {A15['st']['mixed']['shared']:.1f}%, shipped {A15['st']['shipped']['shared']:.1f}%"),
         ("P3 (bldg15 A, W0: the two own-fault rooms within 5 points across the settings)", abs(A15["st"]["mixed"]["local"] - A15["st"]["shipped"]["local"]) <= 5, f"mixed {A15['st']['mixed']['local']:.1f}%, shipped {A15['st']['shipped']['local']:.1f}%"),
         ("P4 (bldg15 A, W0: all six right in at least 25% of visits under mixed, at most 5% under shipped)", A15["st"]["mixed"]["allsix"] >= 25 and A15["st"]["shipped"]["allsix"] <= 5, f"mixed {A15['st']['mixed']['allsix']:.0f}%, shipped {A15['st']['shipped']['allsix']:.0f}%"),
         ("P5 (bldg15 B, W0: mixed beats shipped by at least 10 points, wrong-and-confident at least 3 points higher, at most 1.5% with the hedge)", B15["diff"][0] >= 10 and B15["st"]["mixed"]["wc"] - B15["st"]["shipped"]["wc"] >= 3 and B15["st"]["mixed"]["wc_h"] <= 1.5,
          f"{B15['diff'][0]:+.1f} points; wrong-and-confident {B15['st']['shipped']['wc']:.1f}% to {B15['st']['mixed']['wc']:.1f}%; hedged {B15['st']['mixed']['wc_h']:.1f}%"),
         ("P6 (bldg9 agrees in sign with bldg15 on P1 and P5)", A9["diff"][0] > 0 and A9["diff"][2] < 0 and B9["diff"][0] > 0 and B9["st"]["mixed"]["wc"] > B9["st"]["shipped"]["wc"], f"A {A9['diff'][0]:+.1f} points; B {B9['diff'][0]:+.1f} points, wrong-and-confident {B9['st']['shipped']['wc']:.1f}% to {B9['st']['mixed']['wc']:.1f}%"),
         ("P7 (bldg11 restricted draw within 5 points of the unrestricted 84.2% mixed and 23.8% shipped, W0)", abs(A11["st"]["mixed"]["acc"] - 84.2) <= 5 and abs(A11["st"]["shipped"]["acc"] - 23.8) <= 5, f"mixed {A11['st']['mixed']['acc']:.1f}%, shipped {A11['st']['shipped']['acc']:.1f}%")]
    L += ["", "## Predictions (written before any run)", ""] + [f"- {p}: **{'HELD' if ok else 'FAILED'}** ({d})" for p, ok, d in P] + [""]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.md").write_text("\n".join(L))
    (OUT / "summary.json").write_text(json.dumps(dict(gates=gates, protocol_sha256=hashlib.sha256((HERE / "SECOND_NOTES.md").read_bytes()).hexdigest()), indent=1))
    print("\n".join(L))


if __name__ == "__main__":
    main()
