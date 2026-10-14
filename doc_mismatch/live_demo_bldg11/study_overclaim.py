"""OVERCLAIM_NOTES.md (EXPLORATORY; hashed before the run): the tool is given sharper rates than the simulated world delivers.

  .venv/bin/python doc_mismatch/live_demo_bldg11/study_overclaim.py        -> results/docmismatch/overclaim_study/report.md
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import simulate as S  # noqa: E402
import study_folding as F  # noqa: E402
import study_trend as T  # noqa: E402
import visit as V  # noqa: E402
import world as Wd  # noqa: E402

OUT = HERE.parent.parent / "results" / "docmismatch" / "overclaim_study"
STORED = {"W0": (0.7483333333333333, 193.71), "W1": (0.5466666666666666, 204.81)}
WORLDS = {"W0": (0, 0.0), "W1": (1, 0.25)}
TOOLS = {"honest (today's rates)": 0.0, "inflated 10%": -0.10, "inflated 25%": -0.25}


def boot(d, B=2000, seed=23):
    rng = np.random.default_rng(seed); n = len(d)
    return np.percentile([d[rng.integers(n, size=n)].mean() for _ in range(B)], [2.5, 97.5])


def run(tool_a, wi, aw, js):
    checks_t = tuple(T.shift(c, tool_a) for c in V.CHECKS)           # what the tool believes
    cases = T.make_cases(checks_t)
    ok, conc, vis, vmin = [], [], [], []
    for v in range(100):
        visit = S.draw_visit(v, cases); cl = [cases[r] for r in visit["rooms"]]
        orc = T.ArmOracle(visit, cl, wi, aw, V.CHECKS)               # what the world delivers: today's catalogue, degraded in W1
        r = F.run_ticket_v(cl, orc, js, "base")
        truth = [tuple(c) for c in visit["causes"]]
        ok += [tuple(g) == t for g, t in zip(r["guess"], truth)]; conc += r["concluded"]; vis += [v] * len(cl); vmin.append(r["minutes"])
    return dict(ok=np.array(ok), conc=np.array(conc), visit=np.array(vis), vmin=np.array(vmin))


def main():
    S._init(); js = V.joint_settings(Wd.load_scenario(), "mixed")
    rec = {(w, n): run(a, wi, aw, js) for w, (wi, aw) in WORLDS.items() for n, a in TOOLS.items()}
    g1 = {w: abs(rec[w, "honest (today's rates)"]["ok"].mean() - STORED[w][0]) <= 0.002 and abs(rec[w, "honest (today's rates)"]["vmin"].mean() - STORED[w][1]) <= 0.05 for w in WORLDS}
    L = ["# What if the tool is told the checks are more reliable than they are? (exploratory; OVERCLAIM_NOTES.md hashed before the run)", "",
         "Same 100 visits, mixed setting. The WORLD answers with today's catalogue rates (W0) or 25% worse (W1); the TOOL believes today's rates, or rates sharper by 10% or 25%.", "", "## Gate", "",
         *[f"- G1 honest tool equals the stored accuracy and minutes, {w}: **{'PASS' if g1[w] else 'FAIL'}** ({100*rec[w, 'honest (today' + chr(39) + 's rates)']['ok'].mean():.2f}%)" for w in WORLDS], ""]
    if not all(g1.values()):
        L += ["**REGISTERED OUTCOME: NO RESULT (a gate failed).**", ""]
    res = {}
    for w in WORLDS:
        h = rec[w, "honest (today's rates)"]
        vh = np.array([h["ok"][h["visit"] == v].mean() for v in range(100)])
        L += [f"## {w}", "", "| the tool believes | accuracy | accuracy vs honest (95% CI) | wrong and confident | rooms it concludes | precision of its conclusions | minutes / visit |", "|---|---|---|---|---|---|---|"]
        for n in TOOLS:
            d = rec[w, n]
            wc = float(((~d["ok"]) & d["conc"]).mean()); conc = float(d["conc"].mean())
            prec = float(d["ok"][d["conc"]].mean()) if d["conc"].any() else float("nan")
            vo = np.array([d["ok"][d["visit"] == v].mean() for v in range(100)]); g = 100 * (vo - vh); ci = boot(g)
            res[w, n] = dict(acc=100 * d["ok"].mean(), dacc=float(g.mean()), wc=100 * wc, conc=100 * conc, prec=100 * prec, minutes=float(d["vmin"].mean()))
            L.append(f"| {n} | {100*d['ok'].mean():.1f}% | " + ("-" if n.startswith("honest") else f"{g.mean():+.1f} ({ci[0]:+.1f}, {ci[1]:+.1f})") + f" | {100*wc:.1f}% | {100*conc:.0f}% | {100*prec:.0f}% | {d['vmin'].mean():.0f} |")
        L.append("")
    H0, I10, I25 = (res["W0", n] for n in TOOLS)
    P = [("R1 (W0: the 25%-inflated tool loses at least 5 accuracy points)", I25["dacc"] <= -5, f"{I25['dacc']:+.1f}"),
         ("R2 (W0: its wrong-and-confident rate at least doubles)", I25["wc"] >= 2 * H0["wc"], f"{I25['wc']:.1f}% vs {H0['wc']:.1f}%"),
         ("R3 (the 10%-inflated tool loses less than the 25% one on both)", I10["dacc"] > I25["dacc"] and I10["wc"] < I25["wc"], f"10%: {I10['dacc']:+.1f} / {I10['wc']:.1f}%; 25%: {I25['dacc']:+.1f} / {I25['wc']:.1f}%"),
         ("R4 (the 25%-inflated tool uses at least 10% fewer minutes)", I25["minutes"] <= 0.9 * H0["minutes"], f"{I25['minutes']:.0f} vs {H0['minutes']:.0f}"),
         ("R5 (precision of its conclusions below 80% in W0)", I25["prec"] < 80, f"{I25['prec']:.0f}% (honest {H0['prec']:.0f}%)"),
         ("R6 (W1: the inflated tools are worse than the honest one on wrong-and-confident)", all(res["W1", n]["wc"] > res["W1", "honest (today's rates)"]["wc"] for n in ("inflated 10%", "inflated 25%")), ", ".join(f"{n} {res['W1', n]['wc']:.1f}%" for n in TOOLS))]
    L += ["## Predictions (written before the run)", ""] + [f"- {p}: **{'HELD' if ok else 'FAILED'}** ({d})" for p, ok, d in P] + [""]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.md").write_text("\n".join(L))
    (OUT / "summary.json").write_text(json.dumps(dict(g1={w: bool(x) for w, x in g1.items()}, results={f"{w}|{n}": v for (w, n), v in res.items()}, protocol_sha256=hashlib.sha256((HERE / "OVERCLAIM_NOTES.md").read_bytes()).hexdigest()), indent=1))
    print("\n".join(L))


if __name__ == "__main__":
    main()
