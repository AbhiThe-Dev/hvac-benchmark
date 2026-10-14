"""Tenant answers as soft evidence (idea 8 of the robustness brief). Simulation only.

The engine's tenant questions (Q1 which floors, Q2 peak-only, Q3 warm cold taps) are numeric stand-ins that cost nothing and are asked first; removing Q1 alone cost 0.06 top-1 and doubled
confident errors (Addendum 4). Their reliability (a 15% off-by-one on Q1, small Gaussian noise on Q2 and Q3) is a guess, and a Gaussian likelihood treats a contradicting answer as
nearly decisive. Here the tenant's answer is, with a dialled probability, unrelated to the plant; the question is what to do about it:

    A_plain / B_robust   trust the answers as fitted (B also widens every likelihood)
    NoQ_A / NoQ_B        never ask the tenants
    S15/S30/S50_A        soft evidence: a tenant answer's likelihood is (1-eps) x the hypothesis density + eps x the broad 'other' density, so a contradicting answer can reorder but not eliminate
    S30_B                soft evidence with B's settings

Physical readings keep their full authority. Everything is inside the simulator; the real form of tenant error (systematic over-reporting, partial answers, yes/no phrasing) is not modelled.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from . import adversary as AD
from . import stress as S
from .engine import ENGINE_CHECKS, Engine, _strkeys, fit
from .matrix import build_world
from .provenance import DISCLAIMER

TEN_CONFIG = {
    "SETS": {"M": {"worlds": 4, "plants": 100}, "F": {"worlds": 4, "plants": 200}},     # matched replicates; the held-out broad family of Addendum 6
    "LEVELS": {"M": (0.0, 0.15, 0.30, 0.50, 0.70), "F": (0.0, 0.30, 0.60)},            # chance that a tenant answer is unrelated to the plant, on top of the built-in noise
    "EPS": (0.15, 0.30, 0.50),
    "BAR": {"ask_gain": 0.08, "trust_break": 2.0, "trust_break_min": 0.05, "soft_cut": 0.70, "soft_top1_slack": 0.01, "soft_cost": 0.03, "soft_wc_slack": 0.01,
            "b_robust_slack": 0.03, "wc_slack": 0.01, "top1_gain": 0.03, "conf_gain": 0.05, "matched_top1_drop": 0.05},
    "SEED": 20261701,
}
CFG = TEN_CONFIG
Q_IDS = frozenset({"Q1", "Q2", "Q3"})
NOQ = frozenset(ENGINE_CHECKS) - Q_IDS
VARIANTS = ("A_plain", "B_robust", "NoQ_A", "NoQ_B", "S15_A", "S30_A", "S50_A", "S30_B")
CANDIDATES = ("S15_A", "S30_A", "S50_A", "S30_B", "NoQ_B")


def variant_config(name: str) -> dict:
    B = dict(S.CONFIGS["B_robust"])
    return {"A_plain": {}, "B_robust": B, "NoQ_A": dict(allowed=NOQ), "NoQ_B": dict(B, allowed=NOQ), "S15_A": dict(q_eps=0.15), "S30_A": dict(q_eps=0.30),
            "S50_A": dict(q_eps=0.50), "S30_B": dict(B, q_eps=0.30)}[name]


def frozen_hash() -> str:
    blob = dict(ten=_strkeys(TEN_CONFIG), variants={v: {k: (sorted(x) if isinstance(x, frozenset) else str(x)) for k, x in variant_config(v).items()} for v in VARIANTS}, adv=AD.frozen_hash())
    return hashlib.sha256(json.dumps(blob, sort_keys=True, default=str).encode()).hexdigest()


def run_all(out: Path, quick: bool = False) -> dict:
    seed0 = CFG["SEED"]
    sets = {k: dict(v) for k, v in CFG["SETS"].items()}
    levels = {k: tuple(v) for k, v in CFG["LEVELS"].items()}
    boot = 500
    if quick:
        sets = {"M": dict(worlds=1, plants=40), "F": dict(worlds=1, plants=40)}
        levels = {"M": (0.0, 0.5), "F": (0.0, 0.5)}
        boot = 30
    out.mkdir(parents=True, exist_ok=True)
    lk = fit(build_world(n_theta=S.N_FIT, seed=S.SEED_FIT))
    cases = {"M": [], "F": []}
    spec = S.Spec("matched")
    for k in range(sets["M"]["worlds"]):
        w = S.build_test_world(spec, seed0 + 100 + k) if not quick else build_world(n_theta=sets["M"]["plants"], seed=seed0 + 100 + k)
        cases["M"] += AD.spec_cases(w, k, spec, seed0 + 200 + k)
        del w
    for k in range(sets["F"]["worlds"]):
        w = AD.family_world(AD.ADV_CONFIG["EXT_FACTOR"], seed0 + 300 + k, n=sets["F"]["plants"])
        cases["F"] += AD.family_cases(w, k, seed0 + 400 + k)
        del w
    rows, results = [], {}
    for sname, cs in cases.items():
        for p in levels[sname]:
            for v in VARIANTS:
                res = AD.evaluate_family(lk, cs, dict(variant_config(v), p_tenant=p), seed0 + 2000 + int(p * 100), lk)
                m = AD._ms(res)
                results[(sname, p, v)] = res
                rows.append(dict(set=sname, p_tenant=p, variant=v, **m))
    cell = {(r["set"], r["p_tenant"], r["variant"]): r for r in rows}
    diffs = []
    for sname, cs in cases.items():
        pid = AD.plant_ids(cs)
        one = np.ones(len(cs))
        for p in levels[sname]:
            for x in VARIANTS:
                for y in ("A_plain", "B_robust"):
                    if x == y:
                        continue
                    ax, ay = AD.arr(results[(sname, p, x)]), AD.arr(results[(sname, p, y)])
                    diffs.append(dict(set=sname, p_tenant=p, x=x, y=y,
                                      wrong_conf=AD.boot_ci(pid, [(ax["wc"], one, 1.0), (ay["wc"], one, -1.0)], boot, seed0 + 51),
                                      top1=AD.boot_ci(pid, [(ax["correct"], ax["single"], 1.0), (ay["correct"], ay["single"], -1.0)], boot, seed0 + 52),
                                      confident=AD.boot_ci(pid, [(ax["conf"], one, 1.0), (ay["conf"], one, -1.0)], boot, seed0 + 53)))
    first = {}
    for v in ("A_plain", "S15_A", "S30_A", "S50_A"):
        first[v] = {("thermal" if th else "fixed_orifice"): Engine(lk, th, **variant_config(v)).next_check()[0] for th in (False, True)}
    res = dict(quick=quick, hash=frozen_hash(), n={k: len(v) for k, v in cases.items()}, levels=levels, rows=rows, diffs=diffs, first=first)
    res["cell"] = {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in cell.items()}
    res["scorecard"] = scorecard(rows, levels)
    write(out, res)
    return res


# ------------------------------------------------------------------------------------------------ scorecard (rules frozen in PREREGISTRATION.md Addendum 8)
def _c(rows, s, p, v):
    return next(r for r in rows if r["set"] == s and abs(r["p_tenant"] - p) < 1e-9 and r["variant"] == v)


def _mean(rows, s, lv, v, key):
    return float(np.mean([_c(rows, s, p, v)[key] for p in lv]))


def scorecard(rows: list[dict], levels: dict) -> list[tuple[str, bool, str]]:
    B = CFG["BAR"]
    LM, LF = levels["M"], levels["F"]
    p0, pm, ph = LM[0], LM[min(3, len(LM) - 1)], LM[-1]       # 0, 0.50, 0.70 in the full run
    out = []
    a0, n0 = _c(rows, "M", p0, "A_plain"), _c(rows, "M", p0, "NoQ_A")
    out.append(("T1", a0["top1"] >= n0["top1"] + B["ask_gain"], f"tenants fully reliable (matched, p=0): trusting A top-1 {a0['top1']:.3f} vs never asking {n0['top1']:.3f} (needs +{B['ask_gain']})"))
    am = _c(rows, "M", pm, "A_plain")
    out.append(("T2", am["wrong_conf"] >= max(B["trust_break"] * a0["wrong_conf"], B["trust_break_min"]), f"trusting breaks (matched, p={pm}): A wrong-conf {am['wrong_conf']:.3f} vs {a0['wrong_conf']:.3f} at p=0 (needs >= {B['trust_break']}x and >= {B['trust_break_min']})"))
    flips = [p for p in LM if _c(rows, "M", p, "NoQ_A")["top1"] >= _c(rows, "M", p, "A_plain")["top1"]]
    out.append(("T3", bool(flips), "a break-even exists: never asking beats trusting on top-1 from p = " + (f"{min(flips):g}" if flips else "none up to " + f"{ph:g}") +
                " (A vs NoQ_A top-1: " + ", ".join(f"p={p:g}: {_c(rows, 'M', p, 'A_plain')['top1']:.3f}/{_c(rows, 'M', p, 'NoQ_A')['top1']:.3f}" for p in LM) + ")"))
    sm = _c(rows, "M", pm, "S30_A")
    out.append(("T4", sm["wrong_conf"] <= B["soft_cut"] * am["wrong_conf"] and sm["top1"] >= am["top1"] - B["soft_top1_slack"],
                f"soft evidence protects (matched, p={pm}): S30_A wrong-conf {sm['wrong_conf']:.3f} vs A {am['wrong_conf']:.3f} (needs <= {B['soft_cut']}x), top-1 {sm['top1']:.3f} vs {am['top1']:.3f} (not lower by more than {B['soft_top1_slack']})"))
    s0 = _c(rows, "M", p0, "S30_A")
    out.append(("T5", s0["top1"] >= a0["top1"] - B["soft_cost"] and s0["wrong_conf"] <= a0["wrong_conf"] + B["soft_wc_slack"],
                f"soft evidence is cheap when tenants are fine (matched, p=0): S30_A top-1 {s0['top1']:.3f} vs A {a0['top1']:.3f} (not lower by more than {B['soft_cost']}); wrong-conf {s0['wrong_conf']:.3f} vs {a0['wrong_conf']:.3f}"))
    ver = {}
    for x in CANDIDATES:
        i = _mean(rows, "F", LF, x, "wrong_conf") <= _mean(rows, "F", LF, "B_robust", "wrong_conf") + B["wc_slack"]
        ii = _mean(rows, "F", LF, x, "top1") >= _mean(rows, "F", LF, "B_robust", "top1") + B["top1_gain"] or _mean(rows, "F", LF, x, "confident") >= _mean(rows, "F", LF, "B_robust", "confident") + B["conf_gain"]
        iii = _c(rows, "M", p0, x)["top1"] >= a0["top1"] - B["matched_top1_drop"]
        iv = _c(rows, "M", ph, x)["wrong_conf"] <= _c(rows, "M", ph, "B_robust")["wrong_conf"] + B["wc_slack"]
        ver[x] = (bool(i and ii and iii and iv),
                  f"(i) mean wrong-conf {_mean(rows, 'F', LF, x, 'wrong_conf'):.3f} vs B {_mean(rows, 'F', LF, 'B_robust', 'wrong_conf'):.3f}: {i}; (ii) mean top-1 {_mean(rows, 'F', LF, x, 'top1'):.3f} vs {_mean(rows, 'F', LF, 'B_robust', 'top1'):.3f}, "
                  f"confident {_mean(rows, 'F', LF, x, 'confident'):.2f} vs {_mean(rows, 'F', LF, 'B_robust', 'confident'):.2f}: {ii}; (iii) matched p=0 top-1 {_c(rows, 'M', p0, x)['top1']:.3f} vs A {a0['top1']:.3f}: {iii}; "
                  f"(iv) p={ph:g} wrong-conf {_c(rows, 'M', ph, x)['wrong_conf']:.3f} vs B {_c(rows, 'M', ph, 'B_robust')['wrong_conf']:.3f}: {iv}")
    passing = [x for x, (ok, _) in ver.items() if ok]
    rec = min(passing, key=lambda x: _mean(rows, "F", LF, x, "wrong_conf")) if passing else "B_robust"
    out.append(("T6", bool(passing), "improvement over B_robust across tenant reliabilities under the frozen rule (i)-(iv): " + (", ".join(passing) if passing else "none passes") + " | " + " || ".join(f"{x}: {t}" for x, (_, t) in ver.items())))
    b0, bm = _c(rows, "M", p0, "B_robust"), _c(rows, "M", pm, "B_robust")
    out.append(("T7", bm["wrong_conf"] <= b0["wrong_conf"] + B["b_robust_slack"], f"B_robust is already robust to tenants (matched): wrong-conf {bm['wrong_conf']:.3f} at p={pm} vs {b0['wrong_conf']:.3f} at p=0 (needs within +{B['b_robust_slack']})"))
    out.append(("RECOMMENDED", rec != "B_robust", f"frozen decision rule recommends {rec}"))
    return out


def write(out: Path, res: dict) -> None:
    (out / "tenants.json").write_text(json.dumps(dict(disclaimer=DISCLAIMER, **res), indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else float(o)) + "\n")
    with open(out / "tenants_variants.csv", "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["# " + DISCLAIMER])
        cols = ["set", "p_tenant", "variant", "n_single", "n_pair", "top1", "top3_marginal", "pair_hit", "wrong_conf", "confident", "acc_when_confident", "checks", "minutes", "ece"]
        wr.writerow(cols)
        for r in res["rows"]:
            wr.writerow([f"{r[c]:.4f}" if isinstance(r[c], float) else r[c] for c in cols])
    L = ["# Tenant answers as soft evidence (simulation only)", "", f"**{DISCLAIMER}**", "",
         "Tenant answers (Q1-Q3) are numeric stand-ins; here each answer is, with probability p, unrelated to the plant. Soft evidence: likelihood = (1-eps) x hypothesis density + eps x the broad 'other' density; physical readings keep full authority. "
         "The real form of tenant error (systematic over-reporting, partial answers, yes/no phrasing) is not modelled.", ""]
    if res.get("quick"):
        L += ["**QUICK SMOKE RUN: tiny sizes, numbers are not results.**", ""]
    L += [f"Frozen hash `{res['hash']}`. Visits: matched replicates {res['n']['M']}, held-out broad family {res['n']['F']}.", "", "## Scorecard (rules and predictions frozen before the run)", "", "| | holds | evidence |", "|---|---|---|"]
    L += [f"| {k} | {'yes' if ok else 'NO'} | {ev} |" for k, ok, ev in res["scorecard"]]
    for sname, title in (("M", "Matched replicate worlds"), ("F", "Held-out broad family")):
        L += ["", f"## {title}: top-1 / wrong-and-confident / confident / minutes, by tenant unreliability p", "", "| variant | " + " | ".join(f"p={p:g}" for p in res["levels"][sname]) + " |", "|---|" + "---|" * len(res["levels"][sname])]
        for v in VARIANTS:
            cells = []
            for p in res["levels"][sname]:
                r = next(r for r in res["rows"] if r["set"] == sname and abs(r["p_tenant"] - p) < 1e-9 and r["variant"] == v)
                cells.append(f"{r['top1']:.3f} / {r['wrong_conf']:.3f} / {r['confident']:.2f} / {r['minutes']:.0f}")
            L.append(f"| {v} | " + " | ".join(cells) + " |")
    L += ["", "## Paired differences against `B_robust` (95% interval, whole plants resampled): d top-1 / d wrong-conf", "", "| set | p | variant | d top-1 | d wrong-conf |", "|---|---|---|---|---|"]
    f_ = lambda t: f"{t[0]:+.3f} [{t[1]:+.3f}, {t[2]:+.3f}]"  # noqa: E731
    for d in res["diffs"]:
        if d["y"] == "B_robust" and d["x"] in CANDIDATES + ("NoQ_A", "A_plain"):
            L.append(f"| {d['set']} | {d['p_tenant']:g} | {d['x']} | {f_(d['top1'])} | {f_(d['wrong_conf'])} |")
    L += ["", "## First check asked before any reading", "", "```", json.dumps(res["first"], indent=1), "```", "",
          "Limits: tenant error is modelled as a plant-independent answer with probability p (a stand-in for a tenant who misunderstands, guesses or answers for another unit); "
          "a consistent bias (every tenant over-reports) is not tested and soft evidence would not protect against it; Q2 and Q3 are numeric proxies for yes/no answers."]
    (out / "TENANTS_REPORT.md").write_text("\n".join(L) + "\n")
