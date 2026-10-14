"""Write the matrix outputs. Every file carries the physics-model disclaimer."""
from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import numpy as np

from . import causes as C
from . import checks as K
from .matrix import THRESHOLDS, World, ambiguous_pairs, parameter_leverage, thresholds_hash, uncertainty_rows
from .provenance import DISCLAIMER

CODE = {"DET_SEEN": "S", "DET_NOT_SEEN": ".", "PARAM": "P", "NEEDS_ELIC": "E", "N/A": "-"}


def _clean(o):
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        f = float(o)
        return None if f != f else round(f, 4)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def write_all(out: Path, w: World, cells, pairs, interactions, extra: dict | None = None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    amb = ambiguous_pairs(pairs)
    unc = uncertainty_rows(cells, w, amb)
    lev = parameter_leverage(cells)
    n_gated = {cid: int(w.cause_gated[cid].sum()) for cid in w.cause_plants}
    weak = {cid: n_gated[cid] < THRESHOLDS["GATE_MIN"] for cid in n_gated}
    meta = dict(disclaimer=DISCLAIMER, thresholds=THRESHOLDS, thresholds_hash=thresholds_hash(), n_plants=len(w.plants), seed=w.seed,
                gate_pass_rate={k: round(v, 3) for k, v in w.cause_gate_rate.items()}, n_gated=n_gated, weakly_symptomatic=weak)
    (out / "frozen_thresholds.json").write_text(json.dumps(dict(thresholds=THRESHOLDS, sha256=thresholds_hash()), indent=1) + "\n")
    (out / "matrix.json").write_text(json.dumps(_clean(dict(meta=meta, cells=[asdict(c) for c in cells], ambiguous_pairs=amb, interactions=interactions,
                                                         parameter_leverage=lev, extra=extra or {})), indent=1) + "\n")
    with open(out / "matrix.csv", "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["# " + DISCLAIMER])
        wr.writerow(["cause", "check", "tool", "class", "reason", "n_plants", "gated", "p_sep", "p_null", "sign_consistency", "median_effect", "p_blind", "top_param", "provenance",
                     "source_claim", "agrees_with_source", "tool_fragile", "requires_dynamics"])
        for c in cells:
            wr.writerow([c.cause, c.check, c.tool, c.cls, c.reason, c.n, c.gated, f"{c.p_sep:.3f}", f"{c.p_null:.3f}", f"{c.sign_cons:.3f}", f"{c.median_effect:.3f}", f"{c.p_blind:.3f}",
                         (c.top_params[0][0] + f" ({c.top_params[0][1]})") if c.top_params else "", c.provenance, c.source_claim, c.agrees, c.tool_fragile, c.requires_dynamics])
    with open(out / "uncertain_cells.csv", "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["# " + DISCLAIMER])
        wr.writerow(["rank", "cause", "check", "class", "score", "p_sep", "sign_consistency", "top_param", "conflict_with_source", "reason"])
        for i, r in enumerate(unc, 1):
            wr.writerow([i, r["cause"], r["check"], r["cls"], r["score"], f"{r['p_sep']:.3f}", f"{r['sign_cons']:.3f}", r["top_param"], r["conflict"], r["reason"]])
    with open(out / "pairs_confusion.csv", "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["# " + DISCLAIMER + " Pairs below have NO check that separates them at D >= %.1f." % THRESHOLDS["D_STAR"]])
        wr.writerow(["cause_a", "cause_b", "best_check", "best_D"])
        for p in amb:
            wr.writerow([p["a"], p["b"], p["best_check"], f"{p['best_D']:.2f}"])
    with open(out / "pair_interactions.csv", "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["# " + DISCLAIMER])
        wr.writerow(["cause_a", "cause_b", "seeded_kind", "check", "effect_a", "effect_b", "effect_both", "sd", "observed", "note"])
        for r in interactions:
            wr.writerow([r["a"], r["b"], r["seeded_kind"], r["check"], f"{r['e_a']:.3f}", f"{r['e_b']:.3f}", f"{r['e_ab']:.3f}", f"{r['sd']:.3f}", r["observed"], r["note"]])
    with open(out / "parameter_leverage.csv", "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["# " + DISCLAIMER])
        wr.writerow(["parameter", "provenance", "uncertain_cells_driven", "sum_abs_rho"])
        for r in lev:
            wr.writerow([r["param"], r["prov"], r["cells"], f"{r['sum_abs_rho']:.2f}"])
    _write_md(out, w, cells, unc, amb, interactions, meta)
    return dict(meta=meta, n_unc=len(unc), counts=Counter(c.cls for c in cells))


def _write_md(out: Path, w, cells, unc, amb, inter, meta) -> None:
    by = {(c.cause, c.check): c for c in cells}
    lines = ["# Cause x check matrix (hot-water / recirculation, archetype A1/D2)", "", f"**{DISCLAIMER}**", "",
             f"{meta['n_plants']} plant draws per cause (Latin hypercube, seed {meta['seed']}); thresholds sha256 `{meta['thresholds_hash'][:16]}...` (frozen in PREREGISTRATION.md).", "",
             "Legend: `S` = DETERMINISTIC (separated from normal in >= 95% of plants, one reading), `.` = DETERMINISTIC-NOT-SEEN (indistinguishable from normal), `P` = PARAM-DEPENDENT "
             "(separation depends on plant parameters), `E` = NEEDS-ELICITATION (physics cannot decide), `-` = not applicable. Suffix `!` = disagrees with a cited source, `f` = degrades with a poorer tool, `~` = cause is weakly symptomatic in the model.", ""]
    ids = [c.id for c in K.CHECKS]
    lines.append("| cause \\ check | " + " | ".join(ids) + " | gate pass |")
    lines.append("|---|" + "---|" * (len(ids) + 1))
    for cid in w.cause_plants:
        row = []
        for k in ids:
            c = by[(cid, k)]
            row.append(CODE[c.cls] + ("!" if c.agrees is False else "") + ("f" if c.tool_fragile else ""))
        flag = "~" if meta["weakly_symptomatic"][cid] else ""
        lines.append(f"| {cid}{flag} | " + " | ".join(row) + f" | {meta['gate_pass_rate'][cid]:.2f} |")
    lines += ["", "## Checks", "", "| id | check | feature | location | est. min | safety | remote | physics-readable |", "|---|---|---|---|---|---|---|---|"]
    for c in K.CHECKS:
        lines.append(f"| {c.id} | {c.name} | {c.feature} ({c.unit}) | {c.location} | {c.do_min:g} x{c.n_points} | {c.safety} | {c.remote} | {c.physics_readable} |")
    lines += ["", "Minutes are ANALYST estimates (`minutes_source`), not data.", "", "## Counts", ""]
    cnt = Counter(c.cls for c in cells)
    lines += [f"- {k}: {v}" for k, v in sorted(cnt.items())]
    weak = [c for c, v in meta["weakly_symptomatic"].items() if v]
    lines += ["", "## Causes the model cannot make symptomatic", "",
              "These causes rarely or never produced a complaint (lukewarm / slow / uneven) in the model, so their cells use all plants, not only symptomatic ones: "
              + (", ".join(f"`{c}` (gate pass {meta['gate_pass_rate'][c]:.2f})" for c in weak) if weak else "none") + ".", "",
              "## Cause pairs no check separates", ""]
    lines += ([f"- `{p['a']}` vs `{p['b']}`: best check {p['best_check']}, D = {p['best_D']:.2f}" for p in amb] or ["- none"])
    conflicts = [c for c in cells if c.agrees is False]
    lines += ["", "## Disagreements with cited sources", ""]
    lines += ([f"- `{c.cause}` x {c.check}: model class {c.cls}; source says: {c.source_claim}" for c in conflicts] or ["- none"])
    agree = [c for c in cells if c.agrees]
    lines += ["", f"Cells where the model agrees with a cited source claim: {len(agree)} of {len(agree) + len(conflicts)}.", "", "## Interview list (top 25 of %d uncertain cells)" % len(unc), "",
              "Ranked by: source conflicts first, then NEEDS-ELICITATION, then PARAM-DEPENDENT (see `uncertain_cells.csv`).", "", "| # | cause | check | class | reason |", "|---|---|---|---|---|"]
    for i, r in enumerate(unc[:25], 1):
        lines.append(f"| {i} | {r['cause']} | {r['check']} | {r['cls']} | {r['reason'] or r['top_param']} |")
    (out / "MATRIX_REPORT.md").write_text("\n".join(lines) + "\n")
    (out / "matrix.md").write_text("\n".join(lines) + "\n")


MODEL_LIMITS = """# What the model cannot represent (v0)

{disclaimer}

- **Steady state only.** Three kinds of state (idle recirculation, peak draw, pump-off stagnation) plus closed-form cool-down. Pump cycling, TMV hunting, intermittent faults and time-of-day
  effects are not simulated; cells that depend on them are NEEDS-ELICITATION, not zero.
- **One plant archetype** (storage heater + master TMV, direct-return risers, split-tie return). Heat-pump water heaters (defrost, swing tanks), indirect tanks, solar preheat, heat trace and
  single-loop distribution are out of scope. Rows 17, 20, 24 and 25 of the cause taxonomy are dropped (see causes.DROPPED).
- **Severity and mode ranges are analyst estimates.** The research notes found no published severity or frequency distributions; a fault that looks deterministic here is deterministic
  *within the modelled range*. Cause priors are not modelled at all.
- **Loop heat loss runs high against the ETCC mean** (model median ~85 W per apartment against a measured mean of 62.5 W; 4 risers x ~8 apartments is itself an assumption). It is not tuned away.
- **Quadratic hydraulics.** Pipe friction is linearised at the design flow; head loss in balancing valves dominates the hydraulics, so absolute pipe-friction results are coarse.
- **Time and safety class of each check are analyst estimates**, not data. Travel time between locations is not modelled here (locations are recorded for the later engine).
- **Paired comparison.** The primary classification assumes the technician knows the as-designed value (a drawing, a commissioning report). The blind column `p_blind` compares against the pooled
  healthy spread instead. The documentation-mismatch work is a reminder that the as-designed value can itself be wrong.
- **Circularity.** A cause defined as a parameter change will look separable partly by construction. Measurement error, wide parameter ranges and the calibration anchors limit this; they do not remove it.
- **One feature per check** is pre-registered; second features (for example riser spread) are not scored.
- Two-fault interactions are simulated for the {n_pairs} pairs the notes mention; other pairs are untested.
"""


def write_model_limits(out: Path, n_pairs: int) -> None:
    (out / "model_limits.md").write_text(MODEL_LIMITS.format(disclaimer=DISCLAIMER, n_pairs=n_pairs))
