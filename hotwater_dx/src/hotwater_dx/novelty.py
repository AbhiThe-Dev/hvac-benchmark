"""Causes the engine does not know about (idea 1 of the follow-up plan; Addendum 10). Simulation only.

Every earlier stress test used true causes that were inside the engine's list of 17. Real plants will have causes outside it (the manufacturer-document study found about seven
mixing-valve failure modes we lack; in a year of one cloud service about a quarter of incidents had a never-seen root-cause category). Two measurements:

* Leave-one-cause-out: for each of the 17 causes, delete it (and the pairs that contain it) from the engine's hypotheses and test on visits where it is the true cause. Nothing about
  the physics is invented, and it measures what the engine does when the truth is absent: say "other", abstain, or commit to a wrong cause.
* Two manufacturer-sourced mixing-valve causes added to the *test* world only (operation below the valve's minimum flow; an unregulated valve from a failed thermal element or
  reversed supplies), then the same engine with them added to its hypotheses.

A confident call is only *wrong* when it names a specific cause outside the truth's family (cause group); a confident "other" and an abstention are acceptable outcomes.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from . import causes as C
from . import checks as K
from . import stress as S
from .causes import CauseSpec
from .engine import ENGINE_CONFIG, OTHER, Likelihoods, _strkeys, fit, parts
from .matrix import THRESHOLDS, build_world
from .provenance import DISCLAIMER
from .sampling import substream
from .solve import has_complaint

NOVEL_CFG = {
    "WORLDS": 4,                               # matched replicate test worlds of 100 plants
    "MIN_CASES": 15,                           # a cause needs this many single-fault test visits to be held out
    "VARIANTS": {                              # name -> (engine options, 'other' spread multiplier); all but A_plain are the recommended S30_B with a different 'other'
        "A_plain": ({}, 1.5),
        "S30_B": ({}, 1.5),
        "S30_B_po20": ({"prior_other": 0.20}, 1.5),
        "S30_B_po30": ({"prior_other": 0.30}, 1.5),
        "S30_B_sd3": ({}, 3.0),
        "S30_B_po20_sd3": ({"prior_other": 0.20}, 3.0),
    },
    "NOVEL_MODES": {"tmv_below_min_flow": "valve minimum-flow ratio 1.3-3.0 x loop design flow, droop 25 F x severity (severity 0.4-1)",
                    "tmv_unregulated": "hot fraction stuck: element failed 0.45-0.80, supplies reversed 0.00-0.25 (severity 0.5-1)"},
    "BAR": {"exposure": 0.05, "other_share": 0.05, "top_k": 5, "concentration": 0.50, "tuning_cut": 0.30, "tuning_floor": 0.03, "top1_slack": 0.02, "wc_slack": 0.01,
            "conf_slack": 0.05, "novel_exposure": 0.10, "add_cost_top1": 0.02, "add_cost_wc": 0.01, "add_fix_top1": 0.60, "add_fix_wf": 0.03},
    "SEED": 20261901,
}
CFG = NOVEL_CFG


def frozen_hash() -> str:
    from . import adversary as AD
    blob = dict(cfg=_strkeys({k: v for k, v in NOVEL_CFG.items()}), adv=AD.frozen_hash())
    return hashlib.sha256(json.dumps(blob, sort_keys=True, default=str).encode()).hexdigest()


def base_config() -> dict:
    return dict(S.CONFIGS["B_robust"], q_eps=0.30)


def variant_config(name: str) -> tuple[dict, float]:
    opts, mult = CFG["VARIANTS"][name]
    if name == "A_plain":
        return dict(opts), mult
    return dict(base_config(), **opts), mult


# ------------------------------------------------------------------------------------------------ two manufacturer-sourced causes (test world, and later the engine)
def _flow_draw(rng, P, mode):
    return {"ratio": float(rng.uniform(1.3, 3.0))}


def _flow_apply(Q, mode, sev, d):
    Q.tmv_min_flow = d["ratio"] * Q.design_total
    Q.tmv_lowflow_droop = 25.0 * sev


def _unreg_draw(rng, P, mode):
    return {"f": float(rng.uniform(0.45, 0.80)) if mode == "element_failed" else float(rng.uniform(0.0, 0.25))}


def _unreg_apply(Q, mode, sev, d):
    Q.tmv_fixed_mix = d["f"]


NOVEL = (
    CauseSpec("tmv_below_min_flow", "B", "Mixing valve operating below its minimum flow (loop flow under the valve's control limit)", "manufacturer documents (Powers/Watts)", (), ("low_flow",), (0.4, 1.0),
              _flow_draw, _flow_apply, source="PLACEHOLDER"),
    CauseSpec("tmv_unregulated", "B", "Mixing valve not regulating: failed thermal element or hot and cold supplies reversed", "manufacturer documents (Bradley, Powers/Watts, Taco)", (), ("element_failed", "supplies_reversed"),
              (0.5, 1.0), _unreg_draw, _unreg_apply, source="PLACEHOLDER"),
)
NOVEL_IDS = tuple(c.id for c in NOVEL)


def group_of(cid: str) -> str:
    return C.BY_ID[cid].group if cid in C.BY_ID else next(c.group for c in NOVEL if c.id == cid)


def add_novel(w, seed: int, specs=NOVEL) -> None:
    """Add the novel causes to a built world exactly the way build_world adds its own (a symptomatic draw per plant, up to MAX_ATTEMPTS tries)."""
    for ki, spec in enumerate(specs):
        fps, draws, gated, attempts, passes = [], [], [], 0, 0
        for j, P in enumerate(w.plants):
            first, ok = None, False
            for a in range(THRESHOLDS["MAX_ATTEMPTS"]):
                d = spec.draw(substream(seed, 2, 50 + ki, j, a), P)
                Q = spec.apply(P, d)
                attempts += 1
                g = has_complaint(Q)
                passes += g
                first = first or (Q, d)
                if g:
                    fps.append(Q)
                    draws.append(d)
                    gated.append(True)
                    ok = True
                    break
            if not ok:
                fps.append(first[0])
                draws.append(first[1])
                gated.append(False)
        w.cause_plants[spec.id] = fps
        w.cause_draws[spec.id] = draws
        w.cause_gated[spec.id] = np.array(gated)
        w.cause_gate_rate[spec.id] = passes / max(attempts, 1)
        w.cause_ctx[spec.id] = [K.Ctx(Q) for Q in fps]


def novel_cases(w, ids, per: int, seed: int) -> list:
    rng = np.random.default_rng(seed)
    out = []
    for cid in ids:
        idx = np.where(w.cause_gated[cid])[0]
        for j in rng.choice(idx, size=min(per, len(idx)), replace=False):
            out.append(((cid,), w.cause_ctx[cid][int(j)], bool(w.plants[int(j)].thermal)))
    return out


# ------------------------------------------------------------------------------------------------ editing the engine's hypotheses
def _other_row(mean: np.ndarray, sd: np.ndarray, mult: float):
    return mean.mean(axis=0), np.sqrt((sd ** 2).mean(axis=0) + mean.var(axis=0)) * mult


def with_other(lk: Likelihoods, mult: float) -> Likelihoods:
    """Same hypotheses; the 'other' hypothesis recomputed with the given spread multiplier."""
    keep = [i for i, h in enumerate(lk.hyps) if h != OTHER]
    mo, so = _other_row(lk.mean[keep], lk.sd[keep], mult)
    return Likelihoods([lk.hyps[i] for i in keep] + [OTHER], lk.checks, np.vstack([lk.mean[keep], mo]), np.vstack([lk.sd[keep], so]), lk.thermal_only)


def drop_cause(lk: Likelihoods, cid: str, mult: float) -> Likelihoods:
    """The engine as it would be if `cid` (and every pair containing it) were not in its taxonomy; 'other' recomputed from what is left."""
    keep = [i for i, h in enumerate(lk.hyps) if h != OTHER and cid not in parts(h)]
    mo, so = _other_row(lk.mean[keep], lk.sd[keep], mult)
    return Likelihoods([lk.hyps[i] for i in keep] + [OTHER], lk.checks, np.vstack([lk.mean[keep], mo]), np.vstack([lk.sd[keep], so]), lk.thermal_only)


# ------------------------------------------------------------------------------------------------ outcomes when the truth is absent from the engine
def outcome_rates(results: list, truth_group: str) -> dict:
    n = len(results)
    conf = [r for r in results if r.reason == "confident"]
    wf = fo = co = 0
    for r in conf:
        if r.top == OTHER:
            co += 1
        elif truth_group in {group_of(c) for c in parts(r.top)}:
            fo += 1
        else:
            wf += 1
    return dict(n=n, wrong_family=wf / n if n else float("nan"), family_ok=fo / n if n else float("nan"), conf_other=co / n if n else float("nan"),
                abstain=1 - len(conf) / n if n else float("nan"), minutes=float(np.mean([r.minutes for r in results])) if n else float("nan"))


def _tax_metrics(results: list) -> dict:
    m = S.metrics(results)
    return {k: m[k] for k in ("n_single", "n_pair", "top1", "pair_hit", "wrong_conf", "confident", "checks", "minutes", "ece")}


def run_all(out: Path, quick: bool = False) -> dict:
    seed0 = CFG["SEED"]
    nw = 1 if quick else CFG["WORLDS"]
    out.mkdir(parents=True, exist_ok=True)
    wf = build_world(n_theta=S.N_FIT, seed=S.SEED_FIT)
    lk17 = fit(wf)
    add_novel(wf, seed0 + 1)
    lk19 = fit(wf)
    del wf
    spec = S.Spec("matched")
    cases_all, cases_c, cases_n = [], defaultdict(list), []
    for k in range(nw):
        w = S.build_test_world(spec, seed0 + 100 + k)
        cs = S.make_cases(w, seed0 + 200 + k)
        cases_all += cs
        for c in cs:
            if len(c[0]) == 1:
                cases_c[c[0][0]].append(c)
        add_novel(w, seed0 + 300 + k)
        cases_n += novel_cases(w, NOVEL_IDS, 30, seed0 + 400 + k)
        del w
    ev_seed = seed0 + 2000
    names = list(CFG["VARIANTS"])
    loco, tax = [], []
    lk_cache: dict = {}

    def lk_for(base: Likelihoods, tag: str, mult: float, cid: str | None = None):
        key = (tag, mult, cid)
        if key not in lk_cache:
            lk_cache[key] = drop_cause(base, cid, mult) if cid else with_other(base, mult)
        return lk_cache[key]

    for cid in sorted(cases_c, key=lambda c: C.IDS.index(c)):
        cs = cases_c[cid]
        if len(cs) < CFG["MIN_CASES"]:
            continue
        for v in names:
            cfg, mult = variant_config(v)
            res = S.evaluate(lk_for(lk17, "17", mult, cid), cs, spec, cfg, ev_seed)
            loco.append(dict(cause=cid, group=group_of(cid), variant=v, **outcome_rates(res, group_of(cid))))
    for v in names:
        cfg, mult = variant_config(v)
        tax.append(dict(engine="17 causes", variant=v, **_tax_metrics(S.evaluate(lk_for(lk17, "17", mult), cases_all, spec, cfg, ev_seed))))
    novel = []
    for v in names:
        cfg, mult = variant_config(v)
        for cid in NOVEL_IDS:
            cs = [c for c in cases_n if c[0][0] == cid]
            res = S.evaluate(lk_for(lk17, "17", mult), cs, spec, cfg, ev_seed)
            novel.append(dict(engine="17 causes", variant=v, cause=cid, top1=0.0, **outcome_rates(res, "B")))
    for v in ("A_plain", "S30_B"):
        cfg, mult = variant_config(v)
        lk = lk_for(lk19, "19", mult)
        tax.append(dict(engine="19 causes", variant=v, **_tax_metrics(S.evaluate(lk, cases_all, spec, cfg, ev_seed))))
        for cid in NOVEL_IDS:
            cs = [c for c in cases_n if c[0][0] == cid]
            res = S.evaluate(lk, cs, spec, cfg, ev_seed)
            novel.append(dict(engine="19 causes", variant=v, cause=cid, top1=float(np.mean([r.correct for r in res])), **outcome_rates(res, "B")))
    res = dict(quick=quick, hash=frozen_hash(), n_cases=len(cases_all), n_novel=len(cases_n), loco=loco, taxonomy=tax, novel=novel,
               n_loco_causes=len({r["cause"] for r in loco}))
    res["scorecard"] = scorecard(res)
    write(out, res)
    return res


# ------------------------------------------------------------------------------------------------ scorecard (rules frozen in PREREGISTRATION.md Addendum 10)
def _mean_loco(res: dict, v: str, key: str) -> float:
    return float(np.mean([r[key] for r in res["loco"] if r["variant"] == v]))


def _tax(res: dict, engine: str, v: str) -> dict:
    return next(r for r in res["taxonomy"] if r["engine"] == engine and r["variant"] == v)


def scorecard(res: dict) -> list[tuple[str, bool, str]]:
    B = CFG["BAR"]
    out = []
    base = "S30_B"
    wf0 = _mean_loco(res, base, "wrong_family")
    out.append(("N1", wf0 >= B["exposure"], f"exposure: with the true cause absent, the recommended engine (S30_B) is confident in a specific cause outside the truth's family in {wf0 * 100:.1f}% of visits on average over {res['n_loco_causes']} held-out causes (needs >= {B['exposure'] * 100:.0f}%)"))
    co0 = _mean_loco(res, base, "conf_other")
    out.append(("N2", co0 <= B["other_share"], f"'other' rarely gets said: confident 'other' in {co0 * 100:.1f}% of those visits (needs <= {B['other_share'] * 100:.0f}%); abstains in {_mean_loco(res, base, 'abstain') * 100:.0f}%, confident in the right family in {_mean_loco(res, base, 'family_ok') * 100:.1f}%"))
    per = defaultdict(float)
    for r in res["loco"]:
        if r["variant"] == base:
            per[r["cause"]] += r["wrong_family"] * r["n"]
    tot = sum(per.values())
    top = sorted(per, key=lambda c: -per[c])[:B["top_k"]]
    share = sum(per[c] for c in top) / tot if tot else float("nan")
    out.append(("N3", share >= B["concentration"], f"concentration: the {B['top_k']} worst-hit causes ({', '.join(top)}) hold {share * 100:.0f}% of the confident-wrong-family mass (needs >= {B['concentration'] * 100:.0f}%)"))
    tb = _tax(res, "17 causes", base)
    cands = []
    for v in CFG["VARIANTS"]:
        if v in ("A_plain", base):
            continue
        t = _tax(res, "17 causes", v)
        if t["top1"] >= tb["top1"] - B["top1_slack"] and t["wrong_conf"] <= tb["wrong_conf"] + B["wc_slack"] and t["confident"] >= tb["confident"] - B["conf_slack"]:
            cands.append(v)
    best = min(cands, key=lambda v: _mean_loco(res, v, "wrong_family")) if cands else base
    wfb = _mean_loco(res, best, "wrong_family")
    out.append(("N4", best != base and wfb <= (1 - B["tuning_cut"]) * wf0,
                f"tuning 'other' helps: best admissible setting {best} cuts the wrong-family rate from {wf0 * 100:.1f}% to {wfb * 100:.1f}% (needs <= {(1 - B['tuning_cut']) * 100:.0f}% of base); admissible: {', '.join(cands) or 'none'}"))
    out.append(("N5", wfb >= B["tuning_floor"], f"tuning is not enough: best admissible setting still leaves {wfb * 100:.1f}% (needs >= {B['tuning_floor'] * 100:.0f}%)"))
    nov = {r["cause"]: r for r in res["novel"] if r["engine"] == "17 causes" and r["variant"] == base}
    worst = max(nov.values(), key=lambda r: r["wrong_family"])
    out.append(("N6", worst["wrong_family"] >= B["novel_exposure"], "manufacturer-sourced causes the engine lacks: wrong-family confident rates " + ", ".join(f"{c} {r['wrong_family'] * 100:.1f}% (family-ok {r['family_ok'] * 100:.0f}%, abstain {r['abstain'] * 100:.0f}%)" for c, r in nov.items()) + f" (worst needs >= {B['novel_exposure'] * 100:.0f}%)"))
    t19 = _tax(res, "19 causes", base)
    out.append(("N7", t19["top1"] >= tb["top1"] - B["add_cost_top1"] and t19["wrong_conf"] <= tb["wrong_conf"] + B["add_cost_wc"],
                f"adding the two causes costs little on ordinary visits: top-1 {t19['top1']:.3f} vs {tb['top1']:.3f}, wrong-and-confident {t19['wrong_conf']:.3f} vs {tb['wrong_conf']:.3f}"))
    n19 = [r for r in res["novel"] if r["engine"] == "19 causes" and r["variant"] == base]
    okt = np.mean([r["top1"] for r in n19])
    okw = np.mean([r["wrong_family"] for r in n19])
    out.append(("N8", okt >= B["add_fix_top1"] and okw <= B["add_fix_wf"], f"adding them fixes the novel visits (mechanical, the simulator defines both the test and the engine's new rows): top-1 {okt:.2f} (needs >= {B['add_fix_top1']}), wrong-family {okw * 100:.1f}% (needs <= {B['add_fix_wf'] * 100:.0f}%)"))
    out.append(("RECOMMENDED", best != base and wfb <= (1 - B["tuning_cut"]) * wf0, f"frozen rule: 'other' setting {best}"))
    return out


def write(out: Path, res: dict) -> None:
    (out / "novelty.json").write_text(json.dumps(dict(disclaimer=DISCLAIMER, **res), indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else float(o)) + "\n")
    with open(out / "novelty_loco.csv", "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["# " + DISCLAIMER])
        cols = ["cause", "group", "variant", "n", "wrong_family", "family_ok", "conf_other", "abstain", "minutes"]
        wr.writerow(cols)
        for r in res["loco"]:
            wr.writerow([f"{r[c]:.4f}" if isinstance(r[c], float) else r[c] for c in cols])
    L = ["# Causes the engine does not know about (simulation only)", "", f"**{DISCLAIMER}**", "",
         "A confident call is *wrong* only when it names a specific cause outside the truth's family (cause group); a confident 'other' and an abstention are acceptable outcomes. "
         "Leave-one-cause-out deletes a cause (and the pairs containing it) from the engine and tests on visits where it is the truth; no physics is invented. The two manufacturer-sourced mixing-valve modes are simulator physics I wrote from the "
         "documents (effect sizes are placeholders), so results on them measure consistency, not agreement with buildings.", ""]
    if res.get("quick"):
        L += ["**QUICK SMOKE RUN: tiny sizes, numbers are not results.**", ""]
    L += [f"Frozen hash `{res['hash']}`. Visits: {res['n_cases']} ordinary, {res['n_novel']} with the two novel causes.", "", "## Scorecard (rules and predictions frozen before the run)", "", "| | holds | evidence |", "|---|---|---|"]
    L += [f"| {k} | {'yes' if ok else 'NO'} | {ev} |" for k, ok, ev in res["scorecard"]]
    L += ["", "## Leave-one-cause-out, mean over held-out causes", "", "| variant | confident in a wrong family | confident in the right family | confident 'other' | abstains | minutes |", "|---|---|---|---|---|---|"]
    for v in CFG["VARIANTS"]:
        L.append(f"| {v} | {_mean_loco(res, v, 'wrong_family') * 100:.1f}% | {_mean_loco(res, v, 'family_ok') * 100:.1f}% | {_mean_loco(res, v, 'conf_other') * 100:.1f}% | {_mean_loco(res, v, 'abstain') * 100:.0f}% | {_mean_loco(res, v, 'minutes'):.0f} |")
    L += ["", "## Leave-one-cause-out by cause (recommended engine S30_B; wrong-family / right-family / other / abstain)", "", "| cause | group | visits | wrong family | right family | other | abstain |", "|---|---|---|---|---|---|---|"]
    for r in sorted((r for r in res["loco"] if r["variant"] == "S30_B"), key=lambda r: -r["wrong_family"]):
        L.append(f"| {r['cause']} | {r['group']} | {r['n']} | {r['wrong_family'] * 100:.0f}% | {r['family_ok'] * 100:.0f}% | {r['conf_other'] * 100:.0f}% | {r['abstain'] * 100:.0f}% |")
    L += ["", "## Ordinary visits: what each 'other' setting costs (engine with all 17 causes) and what adding the two novel causes costs", "", "| engine | variant | top-1 | pair hit | wrong-and-confident | confident | minutes |", "|---|---|---|---|---|---|---|"]
    for r in res["taxonomy"]:
        L.append(f"| {r['engine']} | {r['variant']} | {r['top1']:.3f} | {r['pair_hit']:.2f} | {r['wrong_conf']:.3f} | {r['confident']:.2f} | {r['minutes']:.0f} |")
    L += ["", "## The two manufacturer-sourced causes", "", "| engine | variant | cause | top-1 | wrong family | right family | other | abstain |", "|---|---|---|---|---|---|---|---|"]
    for r in res["novel"]:
        L.append(f"| {r['engine']} | {r['variant']} | {r['cause']} | {r['top1']:.2f} | {r['wrong_family'] * 100:.0f}% | {r['family_ok'] * 100:.0f}% | {r['conf_other'] * 100:.0f}% | {r['abstain'] * 100:.0f}% |")
    L += ["", "Limits: groups are my consolidation of causes into families (plant, mixing valve, recirculation hydraulics, crossover and pressure, fixture, controls); a confident call inside the right family is counted acceptable, "
          "which flatters the engine when a family contains the wrong action; the novel causes' effect sizes are placeholders; the test world is the matched simulator."]
    (out / "NOVELTY_REPORT.md").write_text("\n".join(L) + "\n")
