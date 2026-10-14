"""How right does a weak prior over causes have to be before it pays? (idea 2 of the follow-up plan; Addendum 11). Simulation plus a source-agreement check.

Cause frequencies were the most valuable unknown input in the sensitivity analysis (an oracle prior: +0.095 top-1; a random wrong prior: -0.006 on average). Before building a prior from weak public
evidence we measure the payoff curve: priors whose log-weights correlate with the truth at rho (from -1, maximally wrong, to +1, exact), with the same spread as the truth, optionally shrunk toward
uniform. Then we ask whether independent weak sources (what manufacturers write about each cause; independent language-model recall of practitioner knowledge) agree well enough to build one at all.
The agreement check measures consistency among sources, not truth; the simulator cannot tell us how right a sourced prior is.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from . import causes as C
from . import stress as S
from .engine import _strkeys, fit
from .matrix import build_world
from .provenance import DISCLAIMER
from .sensitivity import _mix_cases

PRIOR_CFG = {
    "ALPHAS": (0.5, 1.0),                      # Dirichlet skew of the true case mix over the causes (smaller = more skewed)
    "MIXES": 6,
    "RHOS": (-1.0, -0.5, 0.0, 0.25, 0.5, 0.75, 1.0),
    "SHRINK": (1.0, 0.5),                      # weight on the informed prior; the rest is uniform
    "SHRINK_RHOS": (-1.0, -0.5, 0.0, 0.5, 1.0),
    "BAND": (-0.5, 0.0, 0.5),                  # the plausible range of rho for a prior built from weak public evidence (ANALYST)
    "ENGINES": ("A_plain", "S30_B"),
    "WORLDS": 4, "N_SINGLE": 500,
    "SOURCES": {"min_overlap": 8, "min_m_l_spearman": 0.30, "min_l_internal": 0.50, "max_ratio": 4.0, "n_llm_runs": 5},
    "BAR": {"random_cost": 0.02, "rho05_gain": 0.03, "rho1_gain": 0.07, "wrong_floor": -0.10, "shrink_loss": 0.6, "shrink_gain": 0.5, "wc_rise": 0.03},
    "SEED": 20262001,
}
CFG = PRIOR_CFG


def frozen_hash() -> str:
    from . import adversary as AD
    return hashlib.sha256(json.dumps(dict(cfg=_strkeys(PRIOR_CFG), adv=AD.frozen_hash()), sort_keys=True, default=str).encode()).hexdigest()


def engine_config(name: str) -> dict:
    return {} if name == "A_plain" else dict(S.CONFIGS["B_robust"], q_eps=0.30)


# ------------------------------------------------------------------------------------------------ priors of controlled quality
def standardised(x: np.ndarray) -> np.ndarray:
    return (x - x.mean()) / x.std()


def orthogonal_noise(u: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    e = rng.standard_normal(len(u))
    e = e - (e @ u) / (u @ u) * u
    return standardised(e)


def make_prior(w: np.ndarray, rho: float, shrink: float, e: np.ndarray) -> np.ndarray:
    """Prior weights whose log-weights have correlation rho with the truth's and the same spread, shrunk toward uniform."""
    logw = np.log(w)
    sd = logw.std()
    u = standardised(logw)
    pu = rho * u + np.sqrt(max(1.0 - rho * rho, 0.0)) * e
    p = np.exp(sd * pu)
    p /= p.sum()
    return shrink * p + (1.0 - shrink) / len(p)


def spearman(a, b) -> float:
    def rank(x):
        x = np.asarray(x, float)
        order = np.argsort(x, kind="mergesort")
        r = np.empty(len(x))
        r[order] = np.arange(len(x))
        for v in np.unique(x):
            m = x == v
            r[m] = r[m].mean()
        return r
    ra, rb = rank(a), rank(b)
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def run_curve(quick: bool = False) -> dict:
    seed0 = CFG["SEED"]
    nw = 1 if quick else CFG["WORLDS"]
    nmix = 2 if quick else CFG["MIXES"]
    alphas = CFG["ALPHAS"]
    lk = fit(build_world(n_theta=S.N_FIT, seed=S.SEED_FIT))
    spec = S.Spec("matched")
    cases = []
    for k in range(nw):
        w = S.build_test_world(spec, seed0 + 100 + k)
        cases += S.make_cases(w, seed0 + 200 + k)
        del w
    singles = [c for c in cases if len(c[0]) == 1]
    present = sorted({c[0][0] for c in singles})            # alphabetical, the order sensitivity._mix_cases uses to align weights
    rows = []
    for ai, alpha in enumerate(alphas):
        for mi in range(nmix):
            rng = np.random.default_rng(np.random.SeedSequence([seed0, ai, mi]))
            w = rng.dirichlet([alpha] * len(present))
            w = np.maximum(w, 1e-4)
            w /= w.sum()
            e = orthogonal_noise(standardised(np.log(w)), np.random.default_rng(np.random.SeedSequence([seed0, 7, ai, mi])))
            cs = _mix_cases(cases, w, np.random.default_rng(np.random.SeedSequence([seed0, 8, ai, mi])), n=CFG["N_SINGLE"] if not quick else 150)
            ev_seed = seed0 + 5000 + 100 * ai + mi
            for eng in CFG["ENGINES"]:
                cfg = engine_config(eng)
                base = S.metrics(S.evaluate(lk, cs, spec, cfg, ev_seed))
                grid = [(rho, 1.0) for rho in CFG["RHOS"]] + [(rho, CFG["SHRINK"][1]) for rho in CFG["SHRINK_RHOS"]]
                if quick:
                    grid = [(-1.0, 1.0), (0.0, 1.0), (1.0, 1.0), (-1.0, 0.5)]
                for rho, sh in grid:
                    p = make_prior(w, rho, sh, e)
                    vec = {c: float(x) for c, x in zip(present, p)}
                    for c in C.IDS:
                        vec.setdefault(c, float(p.mean()))
                    m = S.metrics(S.evaluate(lk, cs, spec, dict(cfg, prior_vec=vec), ev_seed))
                    rows.append(dict(alpha=alpha, mix=mi, engine=eng, rho=rho, shrink=sh, d_top1=m["top1"] - base["top1"], d_wrong_conf=m["wrong_conf"] - base["wrong_conf"],
                                     d_minutes=m["minutes"] - base["minutes"], d_confident=m["confident"] - base["confident"], top1=m["top1"], base_top1=base["top1"], base_wrong_conf=base["wrong_conf"]))
    return dict(rows=rows, n_causes=len(present), n_cases=len(cases))


def cell(rows, alpha, eng, rho, sh, key="d_top1"):
    v = [r[key] for r in rows if r["alpha"] == alpha and r["engine"] == eng and abs(r["rho"] - rho) < 1e-9 and abs(r["shrink"] - sh) < 1e-9]
    return float(np.mean(v)) if v else float("nan")


# ------------------------------------------------------------------------------------------------ do independent weak sources agree?
def read_sources(root: Path) -> dict:
    """M: number of distinct manufacturers whose documents state each cause (Addendum 9; scored rows). L: independent language-model rankings (data/prior_sources/L_*.json)."""
    from . import oem as OE
    rows = OE.scored(OE.read_claims(root / "data" / "oem_claims.csv"))
    mf = defaultdict(set)
    for r in rows:
        if r["cause_id"] in OE.CAUSE_IDS:
            mf[r["cause_id"]].add(r["manufacturer"].strip().lower())
    M = np.array([len(mf[c]) for c in C.IDS], float)
    runs = []
    for p in sorted((root / "data" / "prior_sources").glob("L_*.json")):
        d = json.loads(p.read_text())
        rk = {x["cause_id"]: float(x["rank"]) for x in d}
        if set(rk) == set(C.IDS):
            runs.append(np.array([rk[c] for c in C.IDS]))
    return dict(M=M, L=runs)


def source_agreement(src: dict) -> dict:
    B = CFG["SOURCES"]
    L = src["L"]
    out = dict(n_runs=len(L), M=src["M"].tolist())
    if not L:
        return dict(out, status="pending", usable=False, reason="no language-model rankings yet")
    Lm = np.mean(L, axis=0)                                   # mean rank: 1 = most frequent
    internal = float(np.nanmean([spearman(L[i], L[j]) for i in range(len(L)) for j in range(i + 1, len(L))])) if len(L) > 1 else float("nan")
    ml = spearman(src["M"], -Lm)                              # M counts (higher = more) against L ranks (lower = more)
    usable = bool(len(C.IDS) >= B["min_overlap"] and ml >= B["min_m_l_spearman"] and internal >= B["min_l_internal"])
    out.update(L_mean_rank={c: float(x) for c, x in zip(C.IDS, Lm)}, L_internal=internal, M_vs_L=ml, usable=usable, status="done",
               reason=("both agreement bars met" if usable else f"M vs L Spearman {ml:.2f} (needs >= {B['min_m_l_spearman']}) and L internal {internal:.2f} (needs >= {B['min_l_internal']})"))
    if usable:
        z = standardised(standardised(src["M"]) + standardised(-Lm))
        wts = np.exp(z * np.log(B["max_ratio"]) / (z.max() - z.min()))
        out["weights"] = {c: float(x / wts.sum()) for c, x in zip(C.IDS, wts)}
    return out


# ------------------------------------------------------------------------------------------------ scorecard (rules frozen in PREREGISTRATION.md Addendum 11)
def scorecard(curve: dict, agree: dict) -> list[tuple[str, bool, str]]:
    B = CFG["BAR"]
    rows = curve["rows"]
    a = CFG["ALPHAS"][0]
    out = []
    r0 = {e: cell(rows, a, e, 0.0, 1.0) for e in CFG["ENGINES"]}
    out.append(("R1", all(v >= -B["random_cost"] for v in r0.values()), "an uninformative prior of the same spread (rho = 0) changes top-1 by " + ", ".join(f"{e} {v:+.3f}" for e, v in r0.items()) + f" (needs >= -{B['random_cost']}; skewed truth, alpha {a})"))
    g05 = cell(rows, a, "S30_B", 0.5, 1.0)
    out.append(("R2", g05 >= B["rho05_gain"], f"a prior with rho = 0.5 gains {g05:+.3f} top-1 for S30_B (needs >= +{B['rho05_gain']})"))
    g1 = cell(rows, a, "S30_B", 1.0, 1.0)
    out.append(("R3", g1 >= B["rho1_gain"], f"the exact prior (rho = 1) gains {g1:+.3f} for S30_B (needs >= +{B['rho1_gain']})"))
    gm = cell(rows, a, "S30_B", -1.0, 1.0)
    out.append(("R4", gm >= B["wrong_floor"], f"the maximally wrong prior (rho = -1) changes top-1 by {gm:+.3f} for S30_B (needs >= {B['wrong_floor']})"))
    sm, s1 = cell(rows, a, "S30_B", -1.0, 0.5), cell(rows, a, "S30_B", 1.0, 0.5)
    ok5 = (gm < 0 and sm >= B["shrink_loss"] * gm) and (g1 > 0 and s1 >= B["shrink_gain"] * g1)
    out.append(("R5", ok5, f"shrinking by half: loss at rho = -1 {sm:+.3f} vs {gm:+.3f} unshrunk (needs a loss no more than {B['shrink_loss']}x); gain at rho = 1 {s1:+.3f} vs {g1:+.3f} (keeps at least {B['shrink_gain']}x)"))
    g05b = cell(rows, CFG["ALPHAS"][1], "S30_B", 0.5, 1.0)
    out.append(("R6", g05 > g05b, f"skew matters: the rho = 0.5 gain is {g05:+.3f} with a skewed truth (alpha {a}) and {g05b:+.3f} with a flatter one (alpha {CFG['ALPHAS'][1]})"))
    wc = cell(rows, a, "S30_B", -1.0, 1.0, "d_wrong_conf")
    out.append(("R7", wc <= B["wc_rise"], f"a maximally wrong prior raises confident errors by {wc:+.3f} for S30_B (needs <= +{B['wc_rise']})"))
    band = np.mean([cell(rows, a, "S30_B", r, 1.0) for r in CFG["BAND"]])
    out.append(("R8", band >= 0.0, f"over the plausible band rho in {CFG['BAND']} an unshrunk prior pays on average: {band:+.3f} top-1 for S30_B"))
    if agree.get("status") == "done":
        out.append(("R9", agree["usable"], "independent weak sources agree enough to build a sourced prior: " + agree["reason"]))
    else:
        out.append(("R9", False, "source agreement not computed: " + agree.get("reason", "")))
    # decision on shrinkage: the value that does best over the plausible band
    sh = {s: np.mean([cell(rows, a, "S30_B", r, s) for r in CFG["BAND"]]) for s in CFG["SHRINK"]}
    best = max(sh, key=lambda s: sh[s])
    out.append(("RECOMMENDED", True, f"if a prior is used, shrink weight {best} (band mean top-1: " + ", ".join(f"{s}: {v:+.3f}" for s, v in sh.items()) + ")"))
    return out


def run_all(root: Path, out: Path, quick: bool = False) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    curve = run_curve(quick)
    agree = source_agreement(read_sources(root))
    res = dict(quick=quick, hash=frozen_hash(), curve=curve, agreement=agree)
    res["scorecard"] = scorecard(curve, agree)
    write(out, res)
    return res


def write(out: Path, res: dict) -> None:
    (out / "priors.json").write_text(json.dumps(dict(disclaimer=DISCLAIMER, **res), indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else float(o)) + "\n")
    rows = res["curve"]["rows"]
    with open(out / "priors_curve.csv", "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["# " + DISCLAIMER])
        cols = ["alpha", "mix", "engine", "rho", "shrink", "d_top1", "d_wrong_conf", "d_confident", "d_minutes", "top1", "base_top1", "base_wrong_conf"]
        wr.writerow(cols)
        for r in rows:
            wr.writerow([f"{r[c]:.4f}" if isinstance(r[c], float) else r[c] for c in cols])
    L = ["# What a weak prior over causes is worth (simulation) and whether weak sources agree", "", f"**{DISCLAIMER}**", "",
         "The prior's log-weights correlate with the true case mix at rho (-1 = reversed, 0 = unrelated, 1 = exact), with the same spread as the truth. The comparison is the same engine, same visits, same seeds with a uniform prior. "
         "The simulator cannot say how right a prior built from real sources is; the source-agreement check below measures only whether independent weak sources point the same way.", ""]
    if res.get("quick"):
        L += ["**QUICK SMOKE RUN: tiny sizes, numbers are not results.**", ""]
    L += [f"Frozen hash `{res['hash']}`. {res['curve']['n_cases']} visits per world set, {res['curve']['n_causes']} causes with test visits, {CFG['MIXES']} case mixes per skew.", "", "## Scorecard (rules and predictions frozen before the run)", "", "| | holds | evidence |", "|---|---|---|"]
    L += [f"| {k} | {'yes' if ok else 'NO'} | {ev} |" for k, ok, ev in res["scorecard"]]
    for alpha in CFG["ALPHAS"]:
        L += ["", f"## Change in top-1 against a uniform prior, truth skew alpha = {alpha} (mean over mixes; worst mix in brackets)", "", "| rho | " + " | ".join(f"{e} shrink {s}" for e in CFG["ENGINES"] for s in CFG["SHRINK"]) + " |", "|---|" + "---|" * (len(CFG["ENGINES"]) * len(CFG["SHRINK"]))]
        for rho in CFG["RHOS"]:
            cells = []
            for e in CFG["ENGINES"]:
                for s in CFG["SHRINK"]:
                    v = [r["d_top1"] for r in rows if r["alpha"] == alpha and r["engine"] == e and abs(r["rho"] - rho) < 1e-9 and abs(r["shrink"] - s) < 1e-9]
                    cells.append(f"{np.mean(v):+.3f} ({min(v):+.3f})" if v else "-")
            L.append(f"| {rho:g} | " + " | ".join(cells) + " |")
    ag = res["agreement"]
    L += ["", "## Do independent weak sources agree?", "", f"Status: {ag.get('status')}; usable: {ag.get('usable')}; {ag.get('reason', '')}", ""]
    if ag.get("status") == "done":
        L += [f"Language-model runs: {ag['n_runs']}; mean pairwise Spearman among runs {ag['L_internal']:.2f}; Spearman between manufacturer-document emphasis and mean language-model rank {ag['M_vs_L']:.2f}.", "",
              "| cause | manufacturers naming it | mean LLM rank (1 = most frequent) | sourced weight |", "|---|---|---|---|"]
        M = dict(zip(C.IDS, ag["M"]))
        for c in sorted(C.IDS, key=lambda c: ag["L_mean_rank"][c]):
            L.append(f"| {c} | {int(M[c])} | {ag['L_mean_rank'][c]:.1f} | {ag.get('weights', {}).get(c, float('nan')):.3f} |")
    L += ["", "Limits: rho is the correlation of log-weights; a real sourced prior also has errors of scale that this does not model; the language-model rankings are recall of what is written about hot-water problems, not data; manufacturer-document emphasis reflects "
          "which documents I chose to read; neither says how often a cause happens in buildings."]
    (out / "PRIORS_REPORT.md").write_text("\n".join(L) + "\n")
