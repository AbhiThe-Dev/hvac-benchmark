"""Mixed against shipped on the FIRST demo's setup (EXPLORATORY; FIRST_DEMO_NOTES.md was written and hashed before any run). The first demo's files are only read.

  .venv/bin/python doc_mismatch/live_demo_bldg11/study_first_demo.py        -> results/docmismatch/first_demo/report.md
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import simulate as S  # noqa: E402
import study_folding as F  # noqa: E402
import study_mix as MX  # noqa: E402
from docmismatch.troubleshoot.v1 import data as D  # noqa: E402
from docmismatch.troubleshoot.v1.engine import make_case_v1  # noqa: E402
from docmismatch.troubleshoot.v2.joint import JointSettings  # noqa: E402
from docmismatch.troubleshoot.v2.policies import run_policy  # noqa: E402

OUT = HERE.parent.parent / "results" / "docmismatch" / "first_demo"
SERVER = HERE.parent / "live_demo" / "server.py"
JS = {"shipped": JointSettings(), "mixed": JointSettings(low_mix=MX.MIX)}
WORLDS = {"W0": (0, 0.0), "W1": (1, 0.25)}
LS, FAN = ("low_static",), ("ahu_fan_off",)
COMPS = {"C1 shared low static": 1, "C2 shared fan off": 2, "C3 independent faults": 3, "C4 one shared, one own fault": 4}
N = 100


def demo_cases():
    spec = importlib.util.spec_from_file_location("first_demo_server", SERVER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)                     # no side effects: the server only starts under __main__
    b = D.load_building_v1(mod.BUILDING)
    ctx = D.Context(instrument="yes", occupant="no", reheat="yes")      # the demo's context plus the answer to its live question about reheat (FIRST_DEMO_DEVIATIONS.md D1)
    return [make_case_v1(b, r, mod.ITEMS, None, context=ctx, min_rate=mod.MIN_RATE) for r in mod.ROOM_IDS]


def own_cause(rng, case):
    if rng.random() < S.P_DOC_WRONG:
        alts = case.candidates[1:]
        return ("unlisted",) if rng.random() < S.P_UNLISTED else ("wrong", alts[int(rng.integers(len(alts)))])
    return (S.LOCAL_CAUSES[int(rng.integers(len(S.LOCAL_CAUSES)))],)


def make_visit(ci, v, cases):
    rng = np.random.default_rng([S.SEED, 4242, ci, v])
    rooms = [c.member for c in cases]
    state = "ok"
    if ci == 1:
        causes, state = [LS, LS], "low_static"
    elif ci == 2:
        causes, state = [FAN, FAN], "ahu_fan_off"
    elif ci == 3:
        causes = [own_cause(rng, cases[0]), own_cause(rng, cases[1])]
    else:
        causes, state = [LS, own_cause(rng, cases[1])], "low_static"
    return dict(v=30000 + ci * 1000 + v, kind="demo", k=0, rooms=rooms, causes=causes, ahu_state={"AHU-0": state, "AHU-1": "ok", "AHU-2": "ok"})


def run(cases, checks, visits, js, wi, a):
    ok, conc, ls, own, comp, vix, vmin, mins = [], [], [], [], [], [], [], []
    for i, (ci, visit) in enumerate(visits):
        orc = MX.FamOracle(visit, cases, wi, a, checks)
        r = F.run_ticket_v(cases, orc, js, "base")
        ok += [tuple(g) == tuple(t) for g, t in zip(r["guess"], visit["causes"])]; conc += r["concluded"]
        ls += [tuple(g) == LS for g in r["guess"]]; own += r["own_static"]; comp += [ci] * 2; vix += [i] * 2; vmin.append(r["minutes"])
    return dict(ok=np.array(ok), conc=np.array(conc), ls=np.array(ls), own=np.array(own), comp=np.array(comp), visit=np.array(vix), vmin=np.array(vmin), room=np.tile([0, 1], len(visits)))


def stats(d, mask=None):
    m = np.ones(len(d["ok"]), bool) if mask is None else mask
    vm = np.array([m[d["visit"] == v].any() for v in range(len(d["vmin"]))])
    hedged = d["conc"] & d["ls"] & ~d["own"]
    both = np.array([d["ok"][d["visit"] == v].all() for v in range(len(d["vmin"]))])
    return dict(acc=100 * d["ok"][m].mean(), room1=100 * d["ok"][m & (d["room"] == 1)].mean(), both=100 * both[vm].mean(), minutes=float(d["vmin"][vm].mean()),
                wc=100 * ((~d["ok"]) & d["conc"])[m].mean(), wc_h=100 * ((~d["ok"]) & d["conc"] & ~hedged)[m].mean(), conc=100 * d["conc"][m].mean(), hedged=int(hedged[m].sum()))


def boot(x, B=2000, seed=31):
    rng = np.random.default_rng(seed); n = len(x)
    return np.percentile([x[rng.integers(n, size=n)].mean() for _ in range(B)], [2.5, 97.5])


def pdiff(a, b, vmask):
    va = np.array([a["ok"][a["visit"] == v].mean() for v in range(len(a["vmin"]))])[vmask]; vb = np.array([b["ok"][b["visit"] == v].mean() for v in range(len(b["vmin"]))])[vmask]
    g = 100 * (vb - va); dm = (b["vmin"] - a["vmin"])[vmask]
    return g.mean(), boot(g), dm.mean(), boot(dm)


def main():
    S._init()
    cases = demo_cases(); checks = cases[0].checks
    g2 = [c.member for c in cases] == ["Room-0", "Room-1"] and all(c.ahu == "AHU-0" for c in cases) and all(c.min_rate == 0.02 for c in cases) and len(checks) == 30 and all(c.ctx.reheat == 'yes' and c.ctx.instrument == 'yes' and c.ctx.occupant == 'no' for c in cases)
    visits = [(ci, make_visit(ci, v, cases)) for ci in COMPS.values() for v in range(N)]
    g1 = True
    for w, (wi, a) in WORLDS.items():
        for s, js in JS.items():
            for ci, visit in visits[::10][:40]:
                orc = MX.FamOracle(visit, cases, wi, a, checks)
                x = F.run_ticket_v(cases, orc, js, "base"); y = run_policy("tool_ticket_memo2", cases, orc, [S.CTX] * 2, js)
                g1 &= [tuple(u) for u in x["guess"]] == [tuple(u) for u in y["guess"]] and [bool(u) for u in x["concluded"]] == [bool(u) for u in y["concluded"]] and abs(x["minutes"] - y["minutes"]) < 1e-9
    res = {}
    for w, (wi, a) in WORLDS.items():
        runs = {s: run(cases, checks, visits, js, wi, a) for s, js in JS.items()}
        res[w] = runs
    L = ["# Mixed against shipped on the first demo's setup (exploratory; FIRST_DEMO_NOTES.md hashed before any run; the first demo's files are only read)", "",
         "Synthetic building, 3 handlers x 8 boxes, Room-0 and Room-1 on AHU-0, the demo's own configuration (imported from its server), simulated noisy answers. Before any check the shipped model puts 9.1% on low static at AHU-0 and mixed 11.0%.", "",
         "## Gates", "", f"- G1 the replica equals `run_policy('tool_ticket_memo2')` exactly (40 visits per arm and world): **{'PASS' if g1 else 'FAIL'}**",
         f"- G2 the cases are the demo's (Room-0 and Room-1 on AHU-0, `min_rate` 0.02, 30 checks): **{'PASS' if g2 else 'FAIL'}**", "- G3 answers in the check's vocabulary: asserted by the oracle", ""]
    if not (g1 and g2):
        L += ["**REGISTERED OUTCOME: NO RESULT (a gate failed).**", ""]
    out = {}
    for w in WORLDS:
        L += [f"## {w}", "", "| composition | setting | accuracy per room | Room-1 (the second room) | both rooms right | minutes / visit | wrong and confident | with the hedge | rooms called confident | mixed minus shipped: accuracy (95% CI), minutes (95% CI) |", "|---|---|---|---|---|---|---|---|---|---|"]
        for name, ci in list(COMPS.items()) + [("all four pooled", None)]:
            mask = np.ones(len(res[w]["shipped"]["ok"]), bool) if ci is None else (res[w]["shipped"]["comp"] == ci)
            vmask = np.array([mask[res[w]["shipped"]["visit"] == v].any() for v in range(len(res[w]["shipped"]["vmin"]))])
            g, gci, dm, dmci = pdiff(res[w]["shipped"], res[w]["mixed"], vmask)
            for s in JS:
                st = stats(res[w][s], mask); out[w, name, s] = st
                L.append(f"| {name} | {s} | {st['acc']:.1f}% | {st['room1']:.1f}% | {st['both']:.0f}% | {st['minutes']:.0f} | {st['wc']:.1f}% | {st['wc_h']:.1f}% | {st['conc']:.0f}% | " + (f"{g:+.1f} ({gci[0]:+.1f}, {gci[1]:+.1f}); {dm:+.1f} ({dmci[0]:+.1f}, {dmci[1]:+.1f})" if s == "mixed" else "") + " |")
            out[w, name, "diff"] = (g, gci, dm, dmci)
        L.append("")
    pooled, c4 = "all four pooled", "C4 one shared, one own fault"
    P = [("F1 (W0 pooled: mixed minus shipped per-room accuracy within +-3 points)", abs(out["W0", pooled, "diff"][0]) <= 3, f"{out['W0', pooled, 'diff'][0]:+.1f}"),
         ("F2 (W0 pooled minutes within +-5%)", abs(out["W0", pooled, "diff"][2]) <= 0.05 * out["W0", pooled, "shipped"]["minutes"], f"{out['W0', pooled, 'diff'][2]:+.1f} min on {out['W0', pooled, 'shipped']['minutes']:.0f}"),
         ("F3 (W0 pooled wrong-and-confident under mixed at most 1 point above shipped)", out["W0", pooled, "mixed"]["wc"] - out["W0", pooled, "shipped"]["wc"] <= 1, f"{out['W0', pooled, 'shipped']['wc']:.1f}% to {out['W0', pooled, 'mixed']['wc']:.1f}%"),
         ("F4 (W0: in no composition is mixed worse than shipped by more than 5 points)", all(out["W0", n, "diff"][0] >= -5 for n in COMPS), ", ".join(f"{n.split(' ')[0]} {out['W0', n, 'diff'][0]:+.1f}" for n in COMPS)),
         ("F5 (W0, C4: the own-fault room right less than 50% of the time under both settings)", out["W0", c4, "shipped"]["room1"] < 50 and out["W0", c4, "mixed"]["room1"] < 50, f"shipped {out['W0', c4, 'shipped']['room1']:.1f}%, mixed {out['W0', c4, 'mixed']['room1']:.1f}%")]
    L += ["## Predictions (written before any run)", ""] + [f"- {p}: **{'HELD' if ok else 'FAILED'}** ({d})" for p, ok, d in P] + [""]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.md").write_text("\n".join(L))
    (OUT / "summary.json").write_text(json.dumps(dict(g1=bool(g1), g2=bool(g2), protocol_sha256=hashlib.sha256((HERE / "FIRST_DEMO_NOTES.md").read_bytes()).hexdigest()), indent=1))
    print("\n".join(L))


if __name__ == "__main__":
    main()
