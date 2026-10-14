"""Correlated check errors (EXPLORATORY; CORR_NOTES.md was written and hashed before any correlated run).

  .venv/bin/python doc_mismatch/live_demo_bldg11/study_correlation.py

A correlated world (control-system data at a box is invalid with probability pi: every control-system check at that box answers in one shared direction), three tools (independent / tempered / mixture),
the same 100 registered visits, the demo's mixed setting. The engine is not modified: a session subclass overrides the posterior.
Results: results/docmismatch/corr_study/.
"""
import contextlib
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import simulate as S  # noqa: E402
import study_folding as F  # noqa: E402
import visit as V  # noqa: E402
import world as Wd  # noqa: E402
from docmismatch.troubleshoot.v2.policies import PriorSession  # noqa: E402

OUT = HERE.parent.parent / "results" / "docmismatch" / "corr_study"
STORED = {"W0": (0.7483333333333333, 193.71), "W1": (0.5466666666666666, 204.81)}
WORLDS = {"W0": (0, 0.0), "W1": (1, 0.25)}
PIS = (0.0, 0.10, 0.25)
FAULTY_P = 0.90
RF = S.M.RATE_FLOOR


def grouped(ck) -> bool:
    return ck.place == "bas" and ck.subject in ("box", "zone")


class CorrOracle(S.NoisyOracle):
    def __init__(self, visit, cases, world, a, pi):
        super().__init__(visit, cases, world, a)
        self.pi = pi

    def invalid(self, i: int):
        r = np.random.default_rng([S.SEED, self.visit["v"], self.world, S._crc("invalid"), S._crc(self.cases[i].member)])
        inv = bool(r.random() < self.pi) if self.pi > 0 else False
        return inv, bool(r.random() < 0.5)

    def ask_room(self, i, ck, target):
        if self.pi > 0 and grouped(ck):
            inv, faulty = self.invalid(i)
            if inv:
                p = FAULTY_P if faulty else float(np.clip(self.tc[ck.name].bg, RF, 1.0 - RF))
                word = ck.words[0] if self._u("room", self.cases[i].member, f"{ck.name}|{target}|inv") < p else ck.words[1]
                assert word in ck.words
                return word
        return super().ask_room(i, ck, target)


class CorrSession(PriorSession):
    mode, p_t = "indep", 0.10

    def posterior(self):
        if self.mode == "indep":
            return super().posterior()
        causes, post = self._prior()
        grp = []
        for o in self.log:
            ck = self._check(o.check)
            if o.outcome not in ck.words:
                continue
            row = self._row(ck, o.target, causes)
            abn = o.outcome == ck.words[0]
            like = row if abn else 1.0 - row
            if grouped(ck):
                grp.append((like, abn, ck))
            else:
                post = post * like
        if grp:
            n = len(grp)
            L = np.prod([g[0] for g in grp], axis=0)
            if self.mode == "tempered":
                gl = L ** (1.0 / n)
            else:
                bg = [float(np.clip(g[2].bg, RF, 1.0 - RF)) for g in grp]
                healthy = np.prod([b if g[1] else 1.0 - b for b, g in zip(bg, grp)])
                faulty = np.prod([FAULTY_P if g[1] else 1.0 - FAULTY_P for g in grp])
                gl = (1.0 - self.p_t) * L + self.p_t * (0.5 * healthy + 0.5 * faulty)
            post = post * gl
        s = post.sum()
        return causes, (post / s if s > 0 else post)


@contextlib.contextmanager
def tool(mode, p_t=0.10):
    old = F.PriorSession
    F.PriorSession = lambda case, prior=None: _mk(case, prior, mode, p_t)
    try:
        yield
    finally:
        F.PriorSession = old


def _mk(case, prior, mode, p_t):
    s = CorrSession(case, prior)
    s.mode, s.p_t = mode, p_t
    return s


def run(cases, js, wi, a, pi, mode, p_t=0.10, n=100):
    ok, conc, inv, vis_ix, vmin = [], [], [], [], []
    for v in range(n):
        visit = S.draw_visit(v, cases)
        cl = [cases[r] for r in visit["rooms"]]
        orc = CorrOracle(visit, cl, wi, a, pi)
        with tool(mode, p_t):
            r = F.run_ticket_v(cl, orc, js, "base")
        truth = [tuple(c) for c in visit["causes"]]
        ok += [tuple(g) == t for g, t in zip(r["guess"], truth)]; conc += r["concluded"]
        inv += [orc.invalid(i)[0] for i in range(len(cl))]; vis_ix += [v] * len(cl); vmin.append(r["minutes"])
        if (mode, pi) == ("indep", 0.0):
            pass
    return dict(ok=np.array(ok), conc=np.array(conc), inv=np.array(inv), visit=np.array(vis_ix), vmin=np.array(vmin), guess=None)


def boot(d, B=2000, seed=17):
    rng = np.random.default_rng(seed); n = len(d)
    return np.percentile([d[rng.integers(n, size=n)].mean() for _ in range(B)], [2.5, 97.5])


def pv(d, mask_fn=None):
    return np.array([d["ok"][d["visit"] == v].mean() for v in range(100)])


def wcv(d):
    x = (~d["ok"]) & d["conc"]
    return np.array([x[d["visit"] == v].mean() for v in range(100)])


def main():
    S._init(); cases = S._CASES; js = V.joint_settings(Wd.load_scenario(), "mixed")
    ARMS = [("independent", "indep", 0.10), ("tempered", "tempered", 0.10), ("mixture (p_t 0.10)", "mixture", 0.10)]
    rec = {}
    for w, (wi, a) in WORLDS.items():
        for pi in PIS:
            for name, mode, pt in ARMS:
                rec[w, pi, name] = run(cases, js, wi, a, pi, mode, pt)
    # gates
    g1 = {w: abs(rec[w, 0.0, "independent"]["ok"].mean() - STORED[w][0]) <= 0.002 and abs(rec[w, 0.0, "independent"]["vmin"].mean() - STORED[w][1]) <= 0.05 for w in WORLDS}
    base_ref = rec["W0", 0.10, "independent"]
    g2 = run(cases, js, 0, 0.0, 0.10, "mixture", 1e-12)
    g2_ok = bool(np.array_equal(g2["ok"], base_ref["ok"]) and np.array_equal(g2["conc"], base_ref["conc"]) and np.allclose(g2["vmin"], base_ref["vmin"], atol=1e-9))
    g3_ok = True
    for v in range(20):
        visit = S.draw_visit(v, cases); cl = [cases[r] for r in visit["rooms"]]
        o1, o2 = CorrOracle(visit, cl, 0, 0.0, 0.25), CorrOracle(visit, cl, 0, 0.0, 0.25)
        cks = [c for c in V.CHECKS if grouped(c)]
        fw = [(i, c.name, o1.ask_room(i, c, cl[i].doc)) for i in range(len(cl)) for c in cks]
        bw = [(i, c.name, o2.ask_room(i, c, cl[i].doc)) for i in reversed(range(len(cl))) for c in reversed(cks)]
        g3_ok &= sorted(fw) == sorted(bw)
    gates = all(g1.values()) and g2_ok and g3_ok
    L = ["# Correlated check errors (exploratory; CORR_NOTES.md hashed before any correlated run)", "",
         "100 registered visits x 6 rooms, the demo's mixed setting. pi = probability that a box's control-system data is invalid (all control-system checks at that box then answer in one shared direction, whatever the cause). The correlated world is my construction; no data say how often it happens.", "",
         "## Gates", "", *[f"- G1 independent tool at pi = 0 equals the stored accuracy and minutes, {w}: **{'PASS' if g1[w] else 'FAIL'}** ({100*rec[w, 0.0, 'independent']['ok'].mean():.2f}%, {rec[w, 0.0, 'independent']['vmin'].mean():.1f} min)" for w in WORLDS],
         f"- G2 the mixture arm with p_t = 1e-12 equals the independent arm (guesses, conclusions, minutes) at pi = 0.10: **{'PASS' if g2_ok else 'FAIL'}**",
         f"- G3 the oracle is order-independent (20 visits, forward vs backward): **{'PASS' if g3_ok else 'FAIL'}**", ""]
    if not gates:
        L += ["**REGISTERED OUTCOME: NO RESULT (a gate failed).**", ""]
    res = {}
    for w in WORLDS:
        ref = rec[w, 0.0, "independent"]
        vref, wref = pv(ref), wcv(ref)
        L += [f"## {w}", "", "| data invalid (pi) | tool | accuracy | wrong and confident | rooms with invalid data: accuracy / wrong-and-confident | rooms with valid data: accuracy / wrong-and-confident | minutes / visit | wrong-and-confident vs independent tool at pi = 0, points (95% CI) | accuracy vs independent tool at the same pi, points (95% CI) | minutes vs independent tool at the same pi |", "|---|---|---|---|---|---|---|---|---|---|"]
        for pi in PIS:
            base_pi = rec[w, pi, "independent"]
            for name, _, _ in ARMS:
                d = rec[w, pi, name]
                wc = (~d["ok"]) & d["conc"]
                inv, val = d["inv"], ~d["inv"]
                ci_inv = (f"{100*d['ok'][inv].mean():.0f}% / {100*wc[inv].mean():.0f}%" if inv.any() else "-")
                dw = 100 * (wcv(d) - wref); cw = boot(dw)
                da = 100 * (pv(d) - pv(base_pi)); ca = boot(da)
                dm = d["vmin"].mean() - base_pi["vmin"].mean()
                res[w, pi, name] = dict(acc=100 * d["ok"].mean(), wc=100 * wc.mean(), dwc=float(dw.mean()), dwc_ci=cw.tolist(), dacc=float(da.mean()), dacc_ci=ca.tolist(), minutes=float(d["vmin"].mean()), dmin=float(dm))
                L.append(f"| {pi:.2f} | {name} | {100*d['ok'].mean():.1f}% | {100*wc.mean():.1f}% | {ci_inv} | {100*d['ok'][val].mean():.0f}% / {100*wc[val].mean():.0f}% | {d['vmin'].mean():.0f} | {dw.mean():+.1f} ({cw[0]:+.1f}, {cw[1]:+.1f}) | " + ("-" if name == "independent" else f"{da.mean():+.1f} ({ca[0]:+.1f}, {ca[1]:+.1f})") + " | " + ("-" if name == "independent" else f"{dm:+.0f}") + " |")
        L.append("")
    r0, r10, r25 = res["W0", 0.0, "independent"], res["W0", 0.10, "independent"], res["W0", 0.25, "independent"]
    harm = r10["dwc"] >= 1 and r10["dwc_ci"][0] > 0
    def repairs(name):
        r = res["W0", 0.10, name]; b = res["W0", 0.10, "independent"]
        return abs(r["wc"] - r0["wc"]) <= 1 and r["dacc"] >= -2 and r["dmin"] <= 0.10 * b["minutes"]
    L += ["## Verdicts at W0 (rule fixed beforehand)", "", f"- HARM of correlation (independent tool, pi 0 to 0.10, wrong-and-confident up by at least 1 point with the interval above 0): **{'YES' if harm else 'NO'}** ({r10['dwc']:+.1f} points, interval {r10['dwc_ci'][0]:+.1f} to {r10['dwc_ci'][1]:+.1f})",
          *[f"- {n} REPAIRS at pi = 0.10: **{'YES' if repairs(n) else 'NO'}** (wrong-and-confident {res['W0', 0.10, n]['wc']:.1f}% against {r0['wc']:.1f}% at pi = 0; accuracy {res['W0', 0.10, n]['dacc']:+.1f}; minutes {res['W0', 0.10, n]['dmin']:+.0f})" for n in ("tempered", "mixture (p_t 0.10)")], ""]
    P = [("C1 (independent tool, pi 0.10: wrong-and-confident at least 2 points above pi = 0)", r10["dwc"] >= 2, f"{r10['dwc']:+.1f}"),
         ("C2 (independent tool, pi 0.25: accuracy at least 3 points below pi = 0)", r0["acc"] - r25["acc"] >= 3, f"{r25['acc'] - r0['acc']:+.1f}"),
         ("C3 (mixture at pi 0.10 within 1 point of the pi = 0 wrong-and-confident level)", abs(res["W0", 0.10, "mixture (p_t 0.10)"]["wc"] - r0["wc"]) <= 1, f"{res['W0', 0.10, 'mixture (p_t 0.10)']['wc']:.1f}% vs {r0['wc']:.1f}%"),
         ("C4 (tempered lowers wrong-and-confident at pi 0.10, by less than the mixture)", res["W0", 0.10, "tempered"]["wc"] < r10["wc"] and res["W0", 0.10, "tempered"]["wc"] > res["W0", 0.10, "mixture (p_t 0.10)"]["wc"], f"tempered {res['W0', 0.10, 'tempered']['wc']:.1f}%, mixture {res['W0', 0.10, 'mixture (p_t 0.10)']['wc']:.1f}%, independent {r10['wc']:.1f}%"),
         ("C5 (at pi = 0 neither repair costs more than 2 accuracy points)", all(res["W0", 0.0, n]["dacc"] >= -2 for n in ("tempered", "mixture (p_t 0.10)")), ", ".join(f"{n.split(' ')[0]} {res['W0', 0.0, n]['dacc']:+.1f}" for n in ("tempered", "mixture (p_t 0.10)"))),
         ("C6 (mixture adds at least 5% minutes at pi 0.10)", res["W0", 0.10, "mixture (p_t 0.10)"]["dmin"] >= 0.05 * r10["minutes"], f"{res['W0', 0.10, 'mixture (p_t 0.10)']['dmin']:+.0f} min on {r10['minutes']:.0f}")]
    L += ["## Predictions (written before any correlated run)", ""] + [f"- {p}: **{'HELD' if ok else 'FAILED'}** ({d})" for p, ok, d in P] + [""]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.md").write_text("\n".join(L))
    (OUT / "summary.json").write_text(json.dumps(dict(gates=dict(g1={w: bool(x) for w, x in g1.items()}, g2=g2_ok, g3=g3_ok), results={f"{w}|{pi}|{n}": v for (w, pi, n), v in res.items()}, protocol_sha256=hashlib.sha256((HERE / "CORR_NOTES.md").read_bytes()).hexdigest()), indent=1))
    print("\n".join(L))


if __name__ == "__main__":
    main()
