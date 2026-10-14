"""The report of Addendum 43: tables from the raw arrays and the analyses of `study_tree`. Nothing here decides anything: every label and verdict is computed in `study_tree`."""

from __future__ import annotations

import numpy as np

from . import study_tree as ST
from .study_tree import ARMS, PRIMARY_TIER, ROUTINE, TIERS, TOOL, TREES, pct

ARM_NAME = {"tool_joint": "adaptive tool (live)", "tool_ticket_memo2": "adaptive routine", "tree_E": "tree E (mine, confirming)", "tree_Ed": "tree E (decisive form)", "tree_L1": "tree L1 (blind author, controls-first)",
            "tree_L2": "tree L2 (blind author, hands-on)",
            "tree_I1": "tree I1 (informed author, controls-first)", "tree_I2": "tree I2 (informed author, hands-on)", "fast_parent": "flat checklist (fast_parent)", "no_check": "no checks (prior guess)"}
TIER_NAME = {"T3-noattr": "T3-noattr (control system + point map, no design data)", "T3": "T3 (control system + design data)", "T2": "T2 (no control-system access)"}


def table_row(label: str, r: dict) -> str:
    return (f"| {label} | {r['mean_min']:.1f} | {r['median_min']:.0f} | {r['checks']:.1f} | {pct(r['accuracy'])} | {pct(r['right_declared'])} | {pct(r['wrong_declared'], 1)} | {pct(r['undeclared'])} |")


HEAD = "| arm | mean min | median min | checks | accuracy (best guess, declared or not) | declared and right | declared and WRONG | not declared |\n|---|---|---|---|---|---|---|---|"


def present(results: list[dict], tier: str = PRIMARY_TIER) -> tuple:
    return tuple(a for a in ARMS if (tier, a) in results[0]["arms"])


def headline(results: list[dict], tier: str, arms: tuple | None = None) -> list[str]:
    L = [HEAD]
    for a in (arms or present(results, tier)):
        L.append(table_row(ARM_NAME[a], ST.pooled_row(ST.pool(results, tier, a))))
    return L


def kind_table(results: list[dict], tier: str, arms: tuple) -> list[str]:
    L = ["| arm | single-complaint: min / accuracy / declared-wrong | several, unrelated causes | shared cause on one air handler |", "|---|---|---|---|"]
    for a in arms:
        p = ST.pool(results, tier, a)
        cells = []
        for k in ("single", "multi", "shared"):
            r = ST.pooled_row(p, p["kind"] == k)
            cells.append(f"{r['mean_min']:.0f} / {pct(r['accuracy'])} / {pct(r['wrong_declared'], 1)}")
        L.append(f"| {ARM_NAME[a]} | " + " | ".join(cells) + " |")
    return L


def per_cell(analyses: list[dict], tier: str) -> list[str]:
    L = ["| world | tool min | E min | tool acc | E acc | tool vs E | material? (tool / E) | tool vs best-accuracy tree | value vs E at the registered costs |", "|---|---|---|---|---|---|---|---|---|"]
    for a in analyses:
        s, c = a["sum"], a["cmp"]
        t, e = s[(tier, TOOL, "all")], s[(tier, "tree_E", "all")]
        ce, ec = c[(tier, TOOL, "tree_E", "all")], c[(tier, "tree_E", TOOL, "all")]
        best = max((x for x in TREES if (tier, x, "all") in s), key=lambda x: s[(tier, x, "all")]["accuracy"])
        cb = c[(tier, TOOL, best, "all")]
        L.append(f"| {a['world'].name} | {t['minutes']:.0f} | {e['minutes']:.0f} | {pct(t['accuracy'])} | {pct(e['accuracy'])} | {ce['label']} ({100 * ce['r_min']:+.0f}% min, {100 * ce['d_acc']:+.1f} pts) | "
                 f"{'tool' if ce['material'] else '-'} / {'tree' if ec['material'] else '-'} | {best}: {cb['label']} ({100 * cb['r_min']:+.0f}%, {100 * cb['d_acc']:+.1f} pts) | {a['val'][(tier, 'tree_E', 'all')]['state']} |")
    return L


def value_table(analyses: list[dict], tier: str, tree: str = "tree_E") -> list[str]:
    L = ["Mean minutes-equivalent the tool saves per visit against the tree (negative = the tree is cheaper), averaged over the cells; rows: the cost of a declared-wrong complaint; columns: the cost of a "
         "complaint left undeclared (minutes).", "", "| declared-wrong cost \\ undeclared cost | " + " | ".join(f"{u:g}" for u in ST.VALUE_GRID_U) + " |", "|---|" + "---|" * len(ST.VALUE_GRID_U)]
    for w in ST.VALUE_GRID_W:
        L.append(f"| {w:g} | " + " | ".join(f"{np.mean([a['val'][(tier, tree, 'all')]['grid'][(w, u)] for a in analyses]):+.1f}" for u in ST.VALUE_GRID_U) + " |")
    be = {u: float(np.nanmean([a["val"][(tier, tree, "all")]["break_even_wrong"][u] for a in analyses])) for u in ST.VALUE_GRID_U}
    L += ["", "Break-even cost of a declared-wrong complaint (minutes; the tool is cheaper above it only if the tree declares more wrong ones than the tool): " + ", ".join(f"undeclared {u:g}: {be[u]:.0f}" for u in ST.VALUE_GRID_U)]
    return L


def report(base: list[dict], stress: list[dict], rbase: list[dict], rstress: list[dict], gates: list, preds: dict, verd: dict, trees: dict, n: int, files: dict) -> str:
    t = PRIMARY_TIER
    L = ["# A strong branching expert tree against the adaptive tool (Addendum 43)", "",
         f"Simulation only. The base world is Addendum 30's 18 cells ({n} visits each); the stress worlds are {len(stress)} single-factor or combined departures from its primary cell, one event stream each. "
         "Every arm works the same visits, is answered from the same answer table, is charged the tool's own minutes by an independent-checked accountant, is held to the same 12 checks per complaint "
         "and is scored the same way. **The world is the tool's own model family with placeholder rates (home field for the tool); no real technician is involved.** Trees: E is mine (written from the "
         "guides before any run); L1 and L2 were written blind by two independent expert authors who saw the check list and its minutes and nothing about the tool or any result; I1 and I2 by two more, who were also given the tool's whole response table and the service-history base rates (so the tool and the tree know the same things).", "", "## Gates", ""]
    for g, ok, d in gates:
        L.append(f"- **{g}: {'PASS' if ok else 'FAIL'}.** {d}")
    L += ["", "## The trees", "", "| tree | nodes (as a tree) | preamble | depth | leaves | leaf kinds | distinct checks used |", "|---|---|---|---|---|---|---|"]
    for f in ST.tree_facts(trees):
        L.append(f"| {ARM_NAME[f['arm']]} | {f['nodes']} | {f['preamble']} | {f['depth']} | {f['leaves']} | " + ", ".join(f"{k} {v}" for k, v in sorted(f["leaf_ops"].items())) + f" | {f['checks_used']} |")
    L += ["", "## Verdicts (computed by the registered rules)", ""]
    vs = lambda k: verd[k]  # noqa: E731
    inf = "gap_informed" in verd
    inf_trees = tuple(x for x in ST.INFORMED_TREES if f"value_base_{x}" in verd)
    L += [f"1. **Is the tree already close?** At {t}, the tool has a MATERIAL advantage over a tree (at least 15% fewer minutes at no accuracy cost, or at least 5 points more accuracy at no time cost, "
          f"or at least 3 points fewer declared-wrong at no time or accuracy cost; intervals excluding 0) in this many of the {len(base)} base cells: over tree E (mine) **{vs('gap_E')[0]}: {vs('gap_E')[1]}**; "
          f"over EVERY blind tree (E, E-decisive, L1, L2) {vs('gap_blind')[0]}: {vs('gap_blind')[1]}"
          + (f"; over EVERY informed tree (authors who were given the tool's whole response table and the base rates) **{vs('gap_informed')[0]}: {vs('gap_informed')[1]}**" if inf else "; informed trees: not in this run")
          + f"; over all trees run {vs('gap_all_trees')[0]}: {vs('gap_all_trees')[1]}.",
          f"2. **Does the advantage survive stress?** Over {len(stress)} stress worlds, the tool is materially better than E in **{vs('stress_E')[0]}** (E materially better in {vs('stress_E')[1]}): **{vs('stress_E')[3]}**; "
          + (f"better than every informed tree in **{vs('stress_informed')[0]}** (some informed tree materially better in {vs('stress_informed')[1]}): **{vs('stress_informed')[3]}**; " if inf else "")
          + f"better than every blind tree in {vs('stress_blind')[0]} ({vs('stress_blind')[1]}): {vs('stress_blind')[3]}.",
          "3. **Value, with the cost of a mistake or of an unfinished diagnosis as the unknown** (a declared-wrong complaint costs 60 to 240 minutes, an undeclared one 0 to 60; counts of cells: the tool AHEAD / the answer "
          "DEPENDS ON THE COSTS / the tool BEHIND):"] + [
          f"   - against {ARM_NAME[tr]}: base cells {vs('value_base_' + tr)['TOOL AHEAD']} / {vs('value_base_' + tr)['DEPENDS ON THE COSTS']} / {vs('value_base_' + tr)['TOOL BEHIND']}; "
          f"stress worlds {vs('value_stress_' + tr)['TOOL AHEAD']} / {vs('value_stress_' + tr)['DEPENDS ON THE COSTS']} / {vs('value_stress_' + tr)['TOOL BEHIND']}" for tr in ("tree_E",) + inf_trees] + [
          f"4. **Registered combination:** against E, {verd['commercial']}" + (f"; against the informed trees, {verd['commercial_informed']}" if inf else "") + ".", ""]
    L += ["## Registered predictions", "", "| | held | detail |", "|---|---|---|"]
    for k in sorted(preds, key=lambda x: int(x[1:])):
        L.append(f"| {k} | {'yes' if preds[k][0] else 'NO'} | {preds[k][1]} |")
    for tier in TIERS:
        L += ["", f"## Base world, {TIER_NAME[tier]}: all arms (18 cells pooled, {18 * n} visits)", ""] + headline(rbase, tier)
    L += ["", f"## Visit kinds ({TIER_NAME[t]}, 18 cells pooled)", ""] + kind_table(rbase, t, tuple(a for a in (TOOL, ROUTINE) + TREES + ("fast_parent",) if a in present(rbase)))
    L += ["", f"## Tool against tree E, cell by cell ({TIER_NAME[t]})", ""] + per_cell(base, t)
    L += ["", "## By fault type (T3-noattr, 18 cells pooled; per complaint)", "",
          "Per true cause: how often each arm's best guess is exactly right, how often it declares a diagnosis, how often it declares a WRONG one; and, on single-complaint visits, the median minutes.", "",
          "| true cause | complaints | " + " | ".join(f"{a}: right / declared / declared-wrong / median min" for a in (TOOL, "tree_E", "tree_L1", "tree_L2", "fast_parent")) + " |", "|---|---|" + "---|" * 5]
    for r in ST.fault_rows(rbase, t, (TOOL, "tree_E", "tree_L1", "tree_L2", "fast_parent")):
        L.append(f"| {r['cause']} | {r['n']} | " + " | ".join(f"{pct(r['arms'][a]['right'])} / {pct(r['arms'][a]['declared'])} / {pct(r['arms'][a]['wrong_declared'], 1)} / {r['arms'][a]['single_median_min']:.0f}"
                                                              for a in (TOOL, "tree_E", "tree_L1", "tree_L2", "fast_parent")) + " |")
    L += ["", "## Stress worlds (T3-noattr)", "", "| world | tool: min / acc / declared-wrong / declared | E: same | best other tree: acc | tool vs E | material (tool / E) | tool better than ALL trees? | value vs E |",
          "|---|---|---|---|---|---|---|---|"]
    for a in stress:
        s, c = a["sum"], a["cmp"]
        ts, es = s[(t, TOOL, "all")], s[(t, "tree_E", "all")]
        ce, ec = c[(t, TOOL, "tree_E", "all")], c[(t, "tree_E", TOOL, "all")]
        bt = max((x for x in ("tree_Ed", "tree_L1", "tree_L2") + ST.INFORMED_TREES if (t, x, "all") in s), key=lambda x: s[(t, x, "all")]["accuracy"])
        L.append(f"| {a['world'].name} | {ts['minutes']:.0f} / {pct(ts['accuracy'])} / {pct(ts['wrong_confident'], 1)} / {pct(ts['concluded'])} | {es['minutes']:.0f} / {pct(es['accuracy'])} / {pct(es['wrong_confident'], 1)} / "
                 f"{pct(es['concluded'])} | {bt} {pct(s[(t, bt, 'all')]['accuracy'])} | {ce['label']} ({100 * ce['r_min']:+.0f}% min, {100 * ce['d_acc']:+.1f} pts) | {'tool' if ce['material'] else '-'} / "
                 f"{'tree' if ec['material'] else '-'} | {'yes' if ST.tool_beats_all_trees(a, t) else 'no'} | {a['val'][(t, 'tree_E', 'all')]['state']} |")
    L += ["", "By group (T3-noattr; material advantage counted by the registered bars):", "", "| group | worlds | tool materially better than E | E materially better than the tool | tool better than every tree |", "|---|---|---|---|---|"]
    for grp in ("frequency", "noise", "reliability", "mismatch", "tool", "combined"):
        ws = [a for a in stress if a["world"].group == grp]
        if ws:
            L.append(f"| {grp} | {len(ws)} | {sum(ST.tool_beats(a, t, 'tree_E') for a in ws)} | {sum(ST.tree_beats(a, t, 'tree_E') for a in ws)} | {sum(ST.tool_beats_all_trees(a, t) for a in ws)} |")
    for tier in (TIERS[1], TIERS[2]):
        L += ["", f"## Stress worlds at {TIER_NAME[tier]}: tool against E (counts of the {len(stress)} worlds)", "",
              f"Tool materially better than E: {sum(ST.tool_beats(a, tier, 'tree_E') for a in stress)}; E materially better than the tool: {sum(ST.tree_beats(a, tier, 'tree_E') for a in stress)}; "
              f"tool better than every tree: {sum(ST.tool_beats_all_trees(a, tier) for a in stress)}; and over the 18 base cells: {sum(ST.tool_beats(a, tier, 'tree_E') for a in base)} / "
              f"{sum(ST.tree_beats(a, tier, 'tree_E') for a in base)} / {sum(ST.tool_beats_all_trees(a, tier) for a in base)}."]
    prim = next(a for a in base if a["world"].name == "assumed/M0/R0")
    fr = [(k[1], v) for k, v in prim["sum"].items() if k[0] == t and k[2] == "all" and (k[1].startswith("tool@") or k[1] in (TOOL,) + TREES + ("fast_parent",))]
    L += ["", "## The tool's own speed-accuracy frontier against the trees (T3-noattr, Addendum 30's primary cell)", "",
          "| arm | mean min | accuracy | declared-wrong | declared |", "|---|---|---|---|---|"]
    for name, v in sorted(fr, key=lambda kv: kv[1]["minutes"]):
        L.append(f"| {ARM_NAME.get(name, name)} | {v['minutes']:.1f} | {pct(v['accuracy'])} | {pct(v['wrong_confident'], 1)} | {pct(v['concluded'])} |")
    L += ["", f"## What the tool's lead is worth ({TIER_NAME[t]}, base world)", ""] + value_table(base, t)
    r_t, r_e = ST.pooled_row(ST.pool(rbase, t, TOOL)), ST.pooled_row(ST.pool(rbase, t, "tree_E"))
    saved = r_e["mean_min"] - r_t["mean_min"]
    L += ["", f"Minutes per visit the tool saves against tree E in the base world: **{saved:+.1f}** (mean {r_t['mean_min']:.1f} against {r_e['mean_min']:.1f}); per complaint "
          f"{r_e['min_per_complaint'] - r_t['min_per_complaint']:+.1f}. Illustration only, at assumed loaded technician costs (replace with your own): " + "; ".join(
              f"${rate}/h: ${saved / 60 * rate:+.0f} per visit, ${1000 * saved / 60 * rate:+,.0f} per 1000 visits" for rate in (60, 100, 150)) + ". "
          "A negative number means the tool is SLOWER than the tree in minutes; the case for the tool then rests on declared-wrong and undeclared complaints (value table above)."]
    L += ["", "## Files", ""] + [f"- {k}: `{v}`" for k, v in files.items()]
    return "\n".join(L)
