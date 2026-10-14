"""Which assumed inputs change what the engine does and how well it does it? (simulation only)

Two families of perturbation around the matched baseline (engine fitted on a matched world; cases from the same world, as in the stress test):

* WORLD parameters: for each of the 25 sampled plant parameters, restrict it to its lower or upper half-range (all other draws unchanged, so cases are nearly paired with the baseline).
  The engine is *not* refitted: this is "the building stock differs from what the likelihoods assumed in this parameter".
* ENGINE-side inputs: the case-mix prior, the engine's belief about how long checks take, which instruments the technician has, one check removed, and the engine's own settings
  (confidence bar, minimum-value rate, likelihood spread).

An effect "matters" only if it exceeds both the pre-registered threshold and twice the noise floor measured from replicate runs. The output is a ranked list of what to ask people about,
and a list of what does not need asking. It says nothing about real buildings.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from . import checks as K
from . import stress as S
from .engine import ENGINE_CHECKS, Engine, fit
from .matrix import build_world
from .params import PARAMS
from .provenance import DISCLAIMER

SENS_CONFIG = {
    "NULL_REPS": 5,                       # replicate case samples / evaluation seeds, for the noise floor
    "MATTER": {"top1": 0.04, "wrong_conf": 0.02, "minutes_rel": 0.15},
    "MIX_DRAWS": 5, "MIX_ALPHA": 1.0,     # Dirichlet(1) case mixes over the single causes
    "TIME_DRAWS": 5, "TIME_SIGMA": 0.7,   # lognormal multipliers on the engine's believed check minutes
    "TAU": [0.8, 0.9, 0.95, 0.99], "MIN_RATE": [0.005, 0.02, 0.05, 0.1], "VAR_INFLATE": [1.0, 1.5, 2.0, 3.0],
    "TIERS": {
        "T0_questions_eyes": ["Q1", "Q2", "Q3", "K16", "K10"],
        "T1_plus_thermometer": ["K01", "K02", "K03", "K05", "K06", "K07", "K11"],
        "T2_plus_gauges_clamp": ["K08", "K09", "K13", "K14", "K15"],
        "T3_plus_valve_and_isolation_tests": ["K12", "K17", "K18"],
        "T4_plus_72h_logger": ["K19"],
    },
    "SEED": 20261301,
}


def config_hash() -> str:
    return hashlib.sha256(json.dumps(SENS_CONFIG, sort_keys=True).encode()).hexdigest()


def tiers() -> list[tuple[str, frozenset]]:
    out, acc = [], set()
    for name, ids in SENS_CONFIG["TIERS"].items():
        acc |= set(ids)
        out.append((name, frozenset(acc)))
    return out


def _m(res):
    m = S.metrics(res)
    return {k: m[k] for k in ("top1", "wrong_conf", "confident", "checks", "minutes", "pair_hit")}


def _delta(a: dict, b: dict) -> dict:
    return {"d_top1": a["top1"] - b["top1"], "d_wrong_conf": a["wrong_conf"] - b["wrong_conf"], "d_minutes_rel": (a["minutes"] - b["minutes"]) / max(b["minutes"], 1e-9)}


def _score(d: dict, floor: dict) -> float:
    T = SENS_CONFIG["MATTER"]
    return max(abs(d["d_top1"]) / max(T["top1"], 2 * floor["top1"]), abs(d["d_wrong_conf"]) / max(T["wrong_conf"], 2 * floor["wrong_conf"]),
               abs(d["d_minutes_rel"]) / max(T["minutes_rel"], 2 * floor["minutes_rel"]))


def _mix_cases(cases: list, w: np.ndarray, rng: np.random.Generator, n: int = 500) -> list:
    singles = [c for c in cases if len(c[0]) == 1]
    pairs = [c for c in cases if len(c[0]) == 2]
    causes = sorted({c[0][0] for c in singles})
    wt = np.array([w[causes.index(c[0][0])] / sum(1 for x in singles if x[0] == c[0]) for c in singles])
    idx = rng.choice(len(singles), size=n, replace=True, p=wt / wt.sum())
    return [singles[i] for i in idx] + pairs


def run_all(out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    seed = SENS_CONFIG["SEED"]
    lk = fit(build_world(n_theta=S.N_FIT, seed=S.SEED_FIT))
    spec0 = S.Spec("matched")
    w0 = S.build_test_world(spec0, S.SEED_TEST + 0)
    cases0 = S.make_cases(w0, S.SEED_TEST + 1000)
    ev_seed = S.SEED_TEST + 2000
    base = _m(S.evaluate(lk, cases0, spec0, {}, ev_seed))
    rows: list[dict] = []

    def add(group, name, m, d=None, extra=None):
        rows.append(dict(group=group, name=name, **m, **(d or {}), **(extra or {})))

    add("baseline", "matched A_plain", base)
    # ---- noise floor: replicate case samples and evaluation seeds on the same world
    reps = []
    for r in range(SENS_CONFIG["NULL_REPS"]):
        cr = S.make_cases(w0, S.SEED_TEST + 5000 + r)
        reps.append(_m(S.evaluate(lk, cr, spec0, {}, S.SEED_TEST + 6000 + r)))
        add("null", f"replicate {r}", reps[-1], _delta(reps[-1], base))
    floor = {"top1": float(np.std([x["top1"] for x in reps], ddof=1)), "wrong_conf": float(np.std([x["wrong_conf"] for x in reps], ddof=1)),
             "minutes_rel": float(np.std([x["minutes"] for x in reps], ddof=1) / base["minutes"])}
    # ---- world parameters, lower and upper half
    for p in PARAMS:
        mid = 0.5 * (p.low + p.high)
        halves = {"low": (p.low, p.low) if p.kind == "binary" else (p.low, mid), "high": (p.high, p.high) if p.kind == "binary" else (mid, p.high)}
        for tag, rng_ in halves.items():
            w = build_world(n_theta=S.N_TEST, seed=S.SEED_TEST + 0, overrides={p.name: rng_})
            cs = S.make_cases(w, S.SEED_TEST + 1000)
            m = _m(S.evaluate(lk, cs, spec0, {}, ev_seed))
            d = _delta(m, base)
            add("world_param", f"{p.name} {tag}", m, d, dict(param=p.name, half=tag, prov=p.prov, score=_score(d, floor), n_cases=len(cs)))
    # ---- engine-side: case-mix prior (uniform assumed vs oracle vs wrong)
    rng = np.random.default_rng(seed)
    causes = sorted({c[0][0] for c in cases0 if len(c[0]) == 1})
    mixes = [rng.dirichlet([SENS_CONFIG["MIX_ALPHA"]] * len(causes)) for _ in range(SENS_CONFIG["MIX_DRAWS"])]
    for i, mix in enumerate(mixes):
        cs = _mix_cases(cases0, mix, np.random.default_rng(seed + 10 + i))
        uni = _m(S.evaluate(lk, cs, spec0, {}, ev_seed))
        ora = _m(S.evaluate(lk, cs, spec0, dict(prior_vec=dict(zip(causes, mix))), ev_seed))
        wrong = _m(S.evaluate(lk, cs, spec0, dict(prior_vec=dict(zip(causes, mixes[(i + 1) % len(mixes)]))), ev_seed))
        add("prior_mix", f"mix {i} uniform engine", uni, None, dict(mix_max=float(mix.max())))
        add("prior_mix", f"mix {i} oracle prior", ora, _delta(ora, uni))
        add("prior_mix", f"mix {i} wrong prior", wrong, _delta(wrong, uni))
    # ---- engine-side: belief about check minutes
    for i in range(SENS_CONFIG["TIME_DRAWS"]):
        mult = np.random.default_rng(seed + 100 + i).lognormal(0.0, SENS_CONFIG["TIME_SIGMA"], size=len(K.CHECKS))
        belief = {c.id: c.do_min * float(x) for c, x in zip(K.CHECKS, mult)}
        m = _m(S.evaluate(lk, cases0, spec0, dict(assumed_minutes=belief), ev_seed))
        add("time_belief", f"draw {i}", m, _delta(m, base))
    # ---- toolkit tiers and leave-one-check-out
    for name, allowed in tiers():
        add("tier", name, _m(S.evaluate(lk, cases0, spec0, dict(allowed=allowed), ev_seed)), None, dict(n_checks_allowed=len(allowed)))
    for cid in ENGINE_CHECKS:
        m = _m(S.evaluate(lk, cases0, spec0, dict(allowed=frozenset(ENGINE_CHECKS) - {cid}), ev_seed))
        add("leave_one_out", cid, m, _delta(m, base))
    # ---- engine settings, on matched cases and on the composite-mismatch cases
    comp = S.composite(1.0)
    wc = S.build_test_world(comp, S.SEED_TEST + 6)
    cases_c = S.make_cases(wc, S.SEED_TEST + 1006)
    for tau in SENS_CONFIG["TAU"]:
        for mr in SENS_CONFIG["MIN_RATE"]:
            for nm, spec, cs in (("matched", spec0, cases0), ("composite", comp, cases_c)):
                m = _m(S.evaluate(lk, cs, spec, dict(tau=tau, min_rate=mr), ev_seed))
                add("settings", f"tau={tau} min_rate={mr} [{nm}]", m, None, dict(tau=tau, min_rate=mr, world=nm))
    for vi in SENS_CONFIG["VAR_INFLATE"]:
        for nm, spec, cs in (("matched", spec0, cases0), ("composite", comp, cases_c)):
            m = _m(S.evaluate(lk, cs, spec, dict(var_inflate=vi), ev_seed))
            add("var_inflate", f"var_inflate={vi} [{nm}]", m, None, dict(var_inflate=vi, world=nm))
    # ---- first recommended check from the prior, per configuration
    first = {}
    for nm, kw in (("default", {}), ("oracle_prior_mix0", dict(prior_vec=dict(zip(causes, mixes[0])))), ("tau0.99", dict(tau=0.99)), ("B_robust", S.CONFIGS["B_robust"])):
        first[nm] = {("thermal" if th else "fixed_orifice"): Engine(lk, th, **kw).next_check()[0] for th in (False, True)}
    tm = []
    for i in range(SENS_CONFIG["TIME_DRAWS"]):
        mult = np.random.default_rng(seed + 100 + i).lognormal(0.0, SENS_CONFIG["TIME_SIGMA"], size=len(K.CHECKS))
        tm.append(Engine(lk, False, assumed_minutes={c.id: c.do_min * float(x) for c, x in zip(K.CHECKS, mult)}).next_check()[0])
    first["time_belief_draws"] = tm
    return dict(rows=rows, base=base, floor=floor, first=first, causes=causes)


def write(out: Path, res: dict) -> list:
    rows, base, floor = res["rows"], res["base"], res["floor"]
    T = SENS_CONFIG["MATTER"]
    sc = scorecard(res)
    with open(out / "engine_sensitivity.csv", "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["# " + DISCLAIMER])
        cols = sorted({k for r in rows for k in r})
        wr.writerow(cols)
        for r in rows:
            wr.writerow([("" if r.get(c) is None else (f"{r[c]:.4f}" if isinstance(r[c], float) else r[c])) for c in cols])
    (out / "engine_sensitivity.json").write_text(json.dumps(dict(disclaimer=DISCLAIMER, config_hash=config_hash(), base=base, floor=floor, first=res["first"], rows=rows), indent=1, default=float) + "\n")
    L = ["# Engine sensitivity analysis (simulation only)", "", f"**{DISCLAIMER}**", "",
         f"Baseline (matched world, engine A): top-1 {base['top1']:.3f}, wrong-and-confident {base['wrong_conf']:.3f}, {base['checks']:.1f} checks, {base['minutes']:.0f} min. "
         f"Noise floor (sd over {SENS_CONFIG['NULL_REPS']} replicate case samples): top-1 {floor['top1']:.3f}, wrong-and-confident {floor['wrong_conf']:.3f}, minutes {floor['minutes_rel'] * 100:.1f}%. "
         f"An effect matters if it exceeds the larger of the pre-registered threshold (top-1 {T['top1']}, wrong-and-confident {T['wrong_conf']}, minutes {T['minutes_rel'] * 100:.0f}%) and twice the noise floor.", "",
         "## Scorecard (predictions frozen before the run)", "", "| | holds | evidence |", "|---|---|---|"]
    L += [f"| {k} | {'yes' if ok else 'NO'} | {ev} |" for k, ok, ev in sc]
    wp = [r for r in rows if r["group"] == "world_param"]
    byp: dict[str, dict] = {}
    for r in wp:
        e = byp.setdefault(r["param"], dict(param=r["param"], prov=r["prov"], score=-1.0, worst=None))
        if r["score"] > e["score"]:
            e["score"], e["worst"] = r["score"], r
    ranked = sorted(byp.values(), key=lambda e: -e["score"])
    L += ["", "## 1. Plant parameters, ranked by how much the engine's results move when the parameter leaves the range it was fitted on", "",
          "Score = largest effect over the lower and upper half-range, as a multiple of the 'matters' bar (>= 1 matters).", "",
          "| rank | parameter | provenance | worst half | d top-1 | d wrong-conf | d minutes | score | matters |", "|---|---|---|---|---|---|---|---|---|"]
    for i, e in enumerate(ranked, 1):
        r = e["worst"]
        L.append(f"| {i} | {e['param']} | {e['prov']} | {r['half']} | {r['d_top1']:+.3f} | {r['d_wrong_conf']:+.3f} | {r['d_minutes_rel'] * 100:+.0f}% | {e['score']:.2f} | {'YES' if e['score'] >= 1 else 'no'} |")
    L += ["", "## 2. Case-mix prior", "", "| mix | engine | top-1 | wrong-conf | minutes | d top-1 vs uniform engine |", "|---|---|---|---|---|---|"]
    for r in rows:
        if r["group"] == "prior_mix":
            L.append(f"| {r['name']} | | {r['top1']:.3f} | {r['wrong_conf']:.3f} | {r['minutes']:.0f} | {r.get('d_top1', 0.0):+.3f} |")
    L += ["", "## 3. Engine's belief about check minutes (lognormal sigma %.1f, %d draws)" % (SENS_CONFIG["TIME_SIGMA"], SENS_CONFIG["TIME_DRAWS"]), "", "| draw | top-1 | wrong-conf | minutes | d top-1 | d minutes |", "|---|---|---|---|---|---|"]
    for r in rows:
        if r["group"] == "time_belief":
            L.append(f"| {r['name']} | {r['top1']:.3f} | {r['wrong_conf']:.3f} | {r['minutes']:.0f} | {r['d_top1']:+.3f} | {r['d_minutes_rel'] * 100:+.0f}% |")
    L += ["", "## 4. What instruments the technician has (cumulative tiers)", "", "| tier | checks allowed | top-1 | wrong-conf | confident | checks used | minutes |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        if r["group"] == "tier":
            L.append(f"| {r['name']} | {r['n_checks_allowed']} | {r['top1']:.3f} | {r['wrong_conf']:.3f} | {r['confident']:.2f} | {r['checks']:.1f} | {r['minutes']:.0f} |")
    loo = sorted((r for r in rows if r["group"] == "leave_one_out"), key=lambda r: r["d_top1"])
    L += ["", "## 5. Removing one check (all others available)", "", "| check removed | top-1 | d top-1 | wrong-conf | d minutes |", "|---|---|---|---|---|"]
    for r in loo[:12]:
        L.append(f"| {r['name']} ({K.BY_ID[r['name']].name[:45]}) | {r['top1']:.3f} | {r['d_top1']:+.3f} | {r['wrong_conf']:.3f} | {r['d_minutes_rel'] * 100:+.0f}% |")
    L.append(f"\n(Showing the 12 most costly removals of {len(loo)}; the largest single loss is {loo[0]['d_top1']:+.3f} top-1.)")
    L += ["", "## 6. The engine's own settings", "", "| setting | world | top-1 | wrong-conf | confident | minutes |", "|---|---|---|---|---|---|"]
    for r in rows:
        if r["group"] in ("settings", "var_inflate"):
            L.append(f"| {r['name'].split(' [')[0]} | {r['world']} | {r['top1']:.3f} | {r['wrong_conf']:.3f} | {r['confident']:.2f} | {r['minutes']:.0f} |")
    L += ["", "## 7. First check recommended before any reading", "", "```", json.dumps(res["first"], indent=1), "```"]
    (out / "ENGINE_SENSITIVITY_REPORT.md").write_text("\n".join(L) + "\n")
    return sc


def scorecard(res: dict) -> list[tuple[str, bool, str]]:
    rows, base, floor = res["rows"], res["base"], res["floor"]
    out = []
    wp = [r for r in rows if r["group"] == "world_param"]
    best: dict[str, float] = {}
    for r in wp:
        best[r["param"]] = max(best.get(r["param"], 0.0), r["score"])
    rank = sorted(best, key=lambda k: -best[k])
    out.append(("S1", "duty" in rank[:3], f"top 3 parameters: {', '.join(rank[:3])}; duty ranks {rank.index('duty') + 1}"))
    n_matter = sum(1 for v in best.values() if v >= 1.0)
    n_quiet = sum(1 for v in best.values() if v < 0.5)
    out.append(("S2", n_matter <= 8 and n_quiet >= 12, f"{n_matter} of {len(best)} parameters matter (<= 8); {n_quiet} have score < 0.5 (>= 12)"))
    t = [r for r in rows if r["group"] == "tier"]
    t1 = [r["top1"] for r in t]
    steps = [b - a for a, b in zip(t1, t1[1:])]
    out.append(("S4", all(s >= -0.02 for s in steps) and t1[0] < 0.45 and int(np.argmax(steps)) == 0, "tier top-1 " + ", ".join(f"{x:.2f}" for x in t1) + f" (non-decreasing within 0.02; T0 < 0.45; largest step is T0->T1: steps {', '.join(f'{s:+.2f}' for s in steps)})"))
    pm = [r for r in rows if r["group"] == "prior_mix"]
    ora = [r["d_top1"] for r in pm if "oracle" in r["name"]]
    wro = [r["d_top1"] for r in pm if "wrong" in r["name"]]
    out.append(("S5", np.mean(ora) >= 0.05 and np.mean(wro) > -0.05, f"oracle prior d top-1 {np.mean(ora):+.3f} (>= +0.05); wrong prior {np.mean(wro):+.3f} (> -0.05)"))
    tb = [r for r in rows if r["group"] == "time_belief"]
    out.append(("S6", abs(np.mean([r["d_minutes_rel"] for r in tb])) < 0.15 and abs(np.mean([r["d_top1"] for r in tb])) < 0.03,
                f"time belief: mean d minutes {np.mean([r['d_minutes_rel'] for r in tb]) * 100:+.1f}% (< 15%), mean d top-1 {np.mean([r['d_top1'] for r in tb]):+.3f} (< 0.03)"))
    loo = sorted((r for r in rows if r["group"] == "leave_one_out"), key=lambda r: r["d_top1"])
    out.append(("S7", loo[0]["d_top1"] >= -0.05 and loo[0]["name"] in ("K05", "K06", "K10", "K16", "K17"), f"largest single-check loss {loo[0]['name']} {loo[0]['d_top1']:+.3f} (>= -0.05; one of K05/K06/K10/K16/K17)"))
    st = [r for r in rows if r["group"] == "settings" and r["world"] == "matched"]
    ok = [r for r in st if r["wrong_conf"] <= 0.03 and r["confident"] >= 0.5]
    out.append(("S8", bool(ok), f"matched settings with wrong-conf <= 0.03 and confident >= 0.5: {', '.join('tau=%s min_rate=%s' % (r['tau'], r['min_rate']) for r in ok) or 'none'}"))
    return out


# ------------------------------------------------------------------------------------------------ exploratory follow-up (Addendum 5, written after seeing the Addendum 4 result)
PHYS = {"t_amb": (40, 90), "t_cold": (35, 80), "p_cold": (20, 150), "p_hot_deficit": (0.0, 12.0), "t_set_heater": (130, 160), "deadband": (1.0, 10.0), "heater_cap": (100_000, 1_200_000),
        "storage_gal": (50, 1000), "peak_frac": (0.2, 1.0), "t_set_tmv": (110, 140), "tmv_margin_min": (8.0, 35.0), "tmv_sag_gain": (0.0, 1.0), "tmv_tol": (0.5, 10.0),
        "len_scale": (0.4, 2.5), "u_ins": (0.04, 0.40), "ua_mult": (1.0, 3.0), "dT_design": (3.0, 15.0), "balance_err": (0.0, 1.0), "pump_oversize": (0.7, 2.5),
        "duty": (0.05, 1.0), "t_off_max_h": (0.2, 4.0), "deadleg_ft": (2.0, 25.0), "far_share": (0.05, 0.95)}


def out_of_range(out: Path, floor: dict, base: dict) -> list[dict]:
    """Each continuous parameter pushed beyond its fitted range by up to half a range on each side (clipped to physical bounds); the engine is not refitted."""
    lk = fit(build_world(n_theta=S.N_FIT, seed=S.SEED_FIT))
    spec0 = S.Spec("matched")
    ev_seed = S.SEED_TEST + 2000
    rows = []
    for p in PARAMS:
        if p.kind == "binary":
            continue
        span = p.high - p.low
        plo, phi = PHYS[p.name]
        for tag, rng_ in (("below", (max(plo, p.low - 0.5 * span), p.low)), ("above", (p.high, min(phi, p.high + 0.5 * span)))):
            if rng_[1] - rng_[0] < 1e-9 * max(abs(span), 1.0):
                continue
            w = build_world(n_theta=S.N_TEST, seed=S.SEED_TEST + 0, overrides={p.name: rng_})
            cs = S.make_cases(w, S.SEED_TEST + 1000)
            m = _m(S.evaluate(lk, cs, spec0, {}, ev_seed))
            d = _delta(m, base)
            rows.append(dict(param=p.name, side=tag, lo=rng_[0], hi=rng_[1], prov=p.prov, n_cases=len(cs), **m, **d, score=_score(d, floor)))
    rows.sort(key=lambda r: -r["score"])
    with open(out / "engine_sensitivity_out_of_range.csv", "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["# EXPLORATORY (written after the Addendum 4 result). " + DISCLAIMER])
        cols = ["param", "side", "lo", "hi", "prov", "n_cases", "top1", "wrong_conf", "confident", "checks", "minutes", "d_top1", "d_wrong_conf", "d_minutes_rel", "score"]
        wr.writerow(cols)
        for r in rows:
            wr.writerow([f"{r[c]:.4f}" if isinstance(r[c], float) else r[c] for c in cols])
    L = ["# Exploratory: parameters pushed beyond the range the engine was fitted on", "", f"**{DISCLAIMER}**", "",
         "Written after the Addendum 4 result, so it is NOT pre-registered. Each continuous parameter is moved up to half a range beyond its fitted range (clipped to physical bounds), one at a time, engine not refitted. "
         "Same bar and noise floor as Addendum 4 (score >= 1 matters).", "",
         "| rank | parameter | prov | side | range tried | top-1 | d top-1 | wrong-conf | d wrong-conf | d minutes | score |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        L.append(f"| {i} | {r['param']} | {r['prov']} | {r['side']} | {r['lo']:.3g} - {r['hi']:.3g} | {r['top1']:.3f} | {r['d_top1']:+.3f} | {r['wrong_conf']:.3f} | {r['d_wrong_conf']:+.3f} | {r['d_minutes_rel'] * 100:+.0f}% | {r['score']:.2f}{' **' if r['score'] >= 1 else ''} |")
    (out / "ENGINE_SENSITIVITY_OUT_OF_RANGE.md").write_text("\n".join(L) + "\n")
    return rows
