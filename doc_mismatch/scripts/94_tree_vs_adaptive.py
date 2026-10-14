"""Addendum 43 (PREREGISTRATION_DR.md): a strong branching expert decision tree against the adaptive tool, and whether the tool's advantage survives stress. Simulation only.

The same visits, answers, minutes, check limit and scoring for: the adaptive tool (and its routine), six branching trees (E in two forms, two blind authors' L1, L2, two informed authors' I1, I2), a flat checklist and the
no-check guess; Addendum 30's 18 cells as the base world and 26 stress worlds (cause frequencies, control-system and field noise, check reliability, model mismatch, wrongly set tool
assumptions, one combined bad day); three data tiers.

  .venv/bin/python doc_mismatch/scripts/94_tree_vs_adaptive.py                 # full run
  .venv/bin/python doc_mismatch/scripts/94_tree_vs_adaptive.py --from-pickle   # regenerate the report from the stored raw results
  .venv/bin/python doc_mismatch/scripts/94_tree_vs_adaptive.py --smoke         # 2 base + 2 stress worlds, 40 visits: plumbing only (writes nowhere)

Outputs: results/docmismatch/troubleshoot_tree/ (report.md, summary.json, cells.csv, stress.csv, FROZEN.sha256, raw.pkl).
"""

from __future__ import annotations

import argparse
import csv
import json
import pickle
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402

from docmismatch.troubleshoot.v2 import study_tree as ST  # noqa: E402
from docmismatch.troubleshoot.v2 import study_tree_report as RP  # noqa: E402

OUT = ROOT.parent / "results" / "docmismatch" / "troubleshoot_tree"
FROZEN = [ROOT / "src/docmismatch/troubleshoot/v2/tree.py", ROOT / "src/docmismatch/troubleshoot/v2/study_tree.py", ROOT / "src/docmismatch/troubleshoot/v2/study_tree_report.py",
          ROOT / "scripts/94_tree_vs_adaptive.py", ROOT / "tests/test_troubleshoot_tree.py", ROOT / "expert_trees/tree_L1.json", ROOT / "expert_trees/tree_L2.json",
          ROOT / "expert_trees/tree_I1.json", ROOT / "expert_trees/tree_I2.json", ROOT / "expert_trees/BRIEF.md", ROOT / "expert_trees/BRIEF_INFORMED.md"]


def _analyze(r):
    return ST.analyze_world(r)


def analyze_all(results: list[dict], workers: int = 9) -> list[dict]:
    if workers <= 1 or len(results) == 1:
        return [_analyze(r) for r in results]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_analyze, results, chunksize=1))


def write_csv(path: Path, analyses: list[dict]) -> None:
    with open(path, "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["world_idx", "world", "group", "tier", "arm", "subset", "n", "mean_minutes", "median_minutes", "checks", "accuracy", "declared_and_wrong", "declared", "abstain"])
        for a in analyses:
            for (tier, arm, sub), s in sorted(a["sum"].items(), key=lambda kv: tuple(str(x) for x in kv[0])):
                if s["n"]:
                    wr.writerow([a["idx"], a["world"].name, a["world"].group, tier, arm, sub, s["n"], f"{s['minutes']:.3f}", f"{s['median_minutes']:.1f}", f"{s['checks']:.3f}", f"{s['accuracy']:.4f}",
                                 f"{s['wrong_confident']:.4f}", f"{s['concluded']:.4f}", f"{s['abstain']:.4f}"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--from-pickle", action="store_true")
    ap.add_argument("--tree-dir", type=Path, default=ST.TREE_DIR)
    ap.add_argument("--workers", type=int, default=9)
    ap.add_argument("--n", type=int, default=ST.N_EPISODES, help="visits per world (registered: 1000)")
    ap.add_argument("--no-informed", action="store_true", help="leave the informed-author trees out (not ready)")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    from docmismatch.troubleshoot.v2 import tree as TRM
    trees = dict(tree_E=TRM.tree_E(False), tree_Ed=TRM.tree_E(True), tree_L1=TRM.load_tree(a.tree_dir / "tree_L1.json"), tree_L2=TRM.load_tree(a.tree_dir / "tree_L2.json"))
    for k in ST.INFORMED_TREES:                       # an informed tree that has not been written yet is simply not in the run (its absence is stated in the report)
        if not a.no_informed and (a.tree_dir / f"{k}.json").exists():
            trees[k] = TRM.load_tree(a.tree_dir / f"{k}.json")
    arms = tuple(x for x in ST.ARMS if x in trees or x not in ST.TREES)
    OUT_DIR = a.out
    base_all, stress_all = ST.base_worlds(), ST.stress_worlds()
    fidx = next(i for i, w in base_all if w.name == "assumed/M0/R0")
    if a.smoke:
        base, stress, n, a.workers = [base_all[6], base_all[7]], [stress_all[0], stress_all[21]], 40, 1
    else:
        base, stress, n = base_all, stress_all, a.n
    pre = [("G1 neutral world", *ST.gate_neutral_world()), ("G2 answer table", *ST.gate_oracle()), ("G3 trees", *ST.gate_trees(trees)), ("G4 fair accounting", *ST.gate_fair_accounting(trees))]
    for g, ok, d in pre:
        print(f"{g}: {'PASS' if ok else 'FAIL'}: {d}", flush=True)
    if not all(g[1] for g in pre):
        print("A gate failed before any run: NO RESULT")
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if a.from_pickle:
        rbase, rstress = pickle.loads((OUT_DIR / "raw.pkl").read_bytes())
    else:
        if not a.smoke:
            (OUT_DIR / "FROZEN.sha256").write_text("".join(f"{ST.sha(p)}  {p.relative_to(ROOT)}\n" for p in FROZEN if p.exists()))
        rbase = ST.compute(base, trees, n, workers=a.workers, frontier_idx=fidx, arms=arms)
        rstress = ST.compute(stress, trees, n, workers=a.workers, arms=arms)
        if not a.smoke:
            (OUT_DIR / "raw.pkl").write_bytes(pickle.dumps((rbase, rstress)))
    post = []
    if not a.smoke:
        post.append(("G5 tool unchanged", *ST.gate_tool_unchanged(rbase)))
        post.append(("G6 events", *ST.gate_events(rbase)))
    if not a.from_pickle:
        chk = [base[0], stress[0]] if a.smoke else [base_all[6], stress_all[4], stress_all[21]]
        again = ST.compute(chk, trees, min(n, 150), workers=1, frontier_idx=fidx if not a.smoke else None, arms=arms)
        first = [r for r in (rbase + rstress) if r["idx"] in {i for i, _ in chk}]
        first_small = ST.compute(chk, trees, min(n, 150), workers=min(3, a.workers), frontier_idx=fidx if not a.smoke else None, arms=arms)
        post.append(("G7 reproducibility", *ST.gate_repro(again, first_small)))
        assert first
    for g, ok, d in post:
        print(f"{g}: {'PASS' if ok else 'FAIL'}: {d}", flush=True)
    gates = pre + post
    ok_all = all(g[1] for g in gates)
    an_base = analyze_all(rbase, a.workers)
    an_stress = analyze_all(rstress, a.workers)
    verd = ST.verdicts(an_base, an_stress)
    preds = ST.predictions(an_base, an_stress, verd)
    files = {"report": "report.md", "summary": "summary.json", "base worlds by tier, arm, visit kind": "cells.csv", "stress worlds": "stress.csv", "hashes of code, tests and trees before the run": "FROZEN.sha256",
             "raw per-visit arrays": "raw.pkl", "the trees": "doc_mismatch/expert_trees/ (L1, L2 as returned, with the authors' notes; E is generated by tree.tree_E)"}
    text = RP.report(an_base, an_stress, rbase, rstress, gates, preds, verd, trees, n, files)
    if not ok_all:
        text = "# NO RESULT: a gate failed (see Gates below); nothing here is a finding.\n\n" + text
    if a.smoke:
        print(text[:6000])
        print("... (smoke run: nothing written)")
        return 0
    (OUT_DIR / "report.md").write_text(text + "\n")
    write_csv(OUT_DIR / "cells.csv", an_base)
    write_csv(OUT_DIR / "stress.csv", an_stress)
    summary = dict(gates={g: dict(passed=bool(o), detail=d) for g, o, d in gates}, predictions={k: dict(held=bool(v[0]), detail=v[1]) for k, v in sorted(preds.items())},
                   verdicts={k: (list(v) if isinstance(v, tuple) else v) for k, v in verd.items()},
                   headline={f"{tier}|{arm}": ST.pooled_row(ST.pool(rbase, tier, arm)) for tier in ST.TIERS for arm in arms})
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=1, default=float))
    print(f"wrote {OUT_DIR}")
    print(json.dumps({k: (list(v) if isinstance(v, tuple) else v) for k, v in verd.items()}, indent=1, default=str))
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
