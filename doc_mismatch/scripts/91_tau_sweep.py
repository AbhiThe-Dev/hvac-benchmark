"""Addendum 41 (PREREGISTRATION_DR.md): does lowering the conclusion threshold `tau` cut checks without costing accuracy or safety?

All 18 cells of Addendum 30 x T3-noattr and T3 x tool_joint (the CLI's path; primary) and tool_ticket_memo2 (the routine of Addenda 34-36) x tau in {0.95, 0.90, 0.85, 0.80, 0.75}, with
`min_rate` fixed at the live 0.02; plus the two real calls of Addenda 38-40 at each tau (descriptive). Simulation only; nothing here changes the tool's defaults.

  .venv/bin/python doc_mismatch/scripts/91_tau_sweep.py                 # full run (about 2-3 minutes on 8 workers)
  .venv/bin/python doc_mismatch/scripts/91_tau_sweep.py --from-pickle   # regenerate the report from the stored raw results
  .venv/bin/python doc_mismatch/scripts/91_tau_sweep.py --smoke         # two cells, 40 events: plumbing only

Outputs: results/docmismatch/troubleshoot_tau/ (report.md, summary.json, cells.csv, raw.pkl).
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import importlib.util
import json
import pickle
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from docmismatch.troubleshoot.v2 import study_joint as J  # noqa: E402
from docmismatch.troubleshoot.v2 import study_tau as T  # noqa: E402

_s = importlib.util.spec_from_file_location("p90", ROOT / "scripts" / "90_field_pace.py")
P90 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(P90)
FCC, FC = P90.FCC, P90.FC
M, D = FCC.M, FCC.D

OUT = ROOT.parent / "results" / "docmismatch" / "troubleshoot_tau"

# Reference values from the exploratory probe, registered in Addendum 41 (gate G5): steps, central minutes (2 dp), right on every complaint (whole percent).
REF = {"cold_morning": {0.95: (6, "4.95", "99%"), 0.90: (6, "4.95", "99%"), 0.85: (5, "3.98", "100%"), 0.80: (4, "3.23", "100%"), 0.75: (3, "2.25", "100%")},
       "ep160": {0.95: (7, "5.25", "99%"), 0.90: (7, "5.25", "99%"), 0.85: (7, "5.25", "99%"), 0.80: (5, "3.75", "99%"), 0.75: (5, "3.75", "99%")}}


def make_cases_tau(base: dict, comp: dict, k: int, tmp: Path, tau: float) -> list:
    """Addendum 39/40's `make_cases`, with `tau` as given and `min_rate` the frozen live 0.02."""
    b = FC.build_building(base, k, tmp)
    tier = frozenset(base["tier_items"])
    settings = dataclasses.replace(M.Settings().with_drawings("mostly_right"), tau=tau)
    sym = comp["symptoms"]
    out = []
    for c in base["complaints"]:
        ctx = D.Context()
        for key, v in {**base["context"], "reheat": c["reheat"]}.items():
            ctx = ctx.declare(key, v)
        out.append(FCC.make_case_v1(b, c["room"], tier, settings, airflow=sym.get("airflow"), feel=sym.get("feel"), context=ctx, min_rate=T.MIN_RATE))
    return out


def real_calls(n_draws: int = 1000) -> dict:
    pace = json.loads(P90.PACE_FILE.read_text())
    central = pace["scenarios"]["CENTRAL"]
    rows, ref_ok, ref_detail = {}, True, []
    with tempfile.TemporaryDirectory() as td:
        for name in FCC.COMPETE_FILES:
            comp = json.loads((FCC.CASES_DIR / name).read_text())
            base = json.loads((FCC.CASES_DIR / comp["base_case"]).read_text())
            cid = base["id"]
            c = P90.with_truth(comp, pace["worlds"]["sampling_truth_primary"][cid])
            tech = float(pace["technician_minutes_to_diagnosis"][cid])
            rows[cid] = []
            for tau in T.TAU_GRID:
                cases = make_cases_tau(base, c, 6, Path(td), tau)
                ws = [FCC.one_world(cases, base, c, "model", d) for d in range(n_draws)]
                steps = float(np.median([w["steps"] for w in ws]))
                tmin = float(np.median([P90.price(w["checks"], central) for w in ws]))
                r = dict(tau=tau, steps=steps, time=tmin, ratio=tmin / tech, right=float(np.mean([w["all_correct"] for w in ws])), wc=float(np.mean([w["any_wc"] for w in ws])),
                         concluded=float(np.mean([w["all_concluded"] for w in ws])))
                rows[cid].append(r)
                want = REF[cid][tau]
                got = (int(steps), f"{tmin:.2f}", f"{r['right']:.0%}")
                ok = got == want
                ref_ok &= ok
                if not ok:
                    ref_detail.append(f"{cid} tau {tau}: got {got}, probe {want}")
    return dict(rows=rows, ref_ok=ref_ok, ref_detail=ref_detail)


def real_prediction(real: dict) -> tuple[bool, str]:
    at80 = {cid: next(r for r in rs if r["tau"] == 0.80) for cid, rs in real["rows"].items()}
    ok = all(r["ratio"] < 1.0 and r["right"] >= 0.98 for r in at80.values())
    return ok, "tau 0.80: " + ", ".join(f"{cid} ratio {r['ratio']:.2f}, right {r['right']:.0%}" for cid, r in at80.items())


def write_cells_csv(analyses: list[dict], path: Path) -> None:
    with open(path, "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["cell", "shared", "map", "rel", "tier", "policy", "tau", "subset", "n", "minutes", "checks", "accuracy", "wrong_confident", "concluded", "label_vs_0.95", "safety_vs_0.95", "r_min_vs_0.95", "d_acc_vs_0.95"])
        for a in analyses:
            c = a["cell"]
            for (tier, pol, tau, sub), s in sorted(a["sum"].items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2], kv[0][3])):
                if s["n"] == 0:
                    continue
                cmp_ = a["cmp"].get((tier, pol, tau, sub))
                wr.writerow([a["idx"], c.shared, c.map, c.rel, tier, pol, tau, sub, s["n"], f"{s['minutes']:.3f}", f"{s['checks']:.3f}", f"{s['accuracy']:.4f}", f"{s['wrong_confident']:.4f}",
                             f"{s['concluded']:.4f}", cmp_["label"] if cmp_ else "", cmp_["safety"] if cmp_ else "", f"{cmp_['r_min']:.4f}" if cmp_ else "", f"{cmp_['d_acc']:.4f}" if cmp_ else ""])


def finish(results: list[dict], n: int, workers: int | None, extra_gates: list, real: dict | None, from_pickle: bool) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    analyses = [T.analyze_cell(r) for r in results]
    gates = [("G1", *T.gate_g1(results)), *extra_gates]
    preds = T.predictions(analyses)
    if real is not None:
        preds["P7"] = real_prediction(real)
    all_ok = all(ok for _, ok, _ in gates)
    text = T.report(analyses, gates, preds, real, n)
    if not all_ok:
        text = "# NO RESULT: a gate failed (see Gates below); nothing here is a finding.\n\n" + text
    (OUT / "report.md").write_text(text + "\n")
    labels = T.all_labels(analyses)
    oc, tau_star = T.outcome(labels)
    (OUT / "summary.json").write_text(json.dumps(dict(
        outcome=oc if all_ok else "NO RESULT", tau_star=tau_star, gates={g: dict(passed=bool(ok), detail=d) for g, ok, d in gates},
        labels={f"{t}|{p}|{tau}": l for (t, p, tau), l in sorted(labels.items(), key=lambda kv: str(kv[0]))}, predictions={k: dict(held=bool(v[0]), detail=v[1]) for k, v in sorted(preds.items())},
        real_calls=(real["rows"] if real else None)), indent=1, sort_keys=True))
    write_cells_csv(analyses, OUT / "cells.csv")
    if not from_pickle:
        (OUT / "raw.pkl").write_bytes(pickle.dumps(results))
    print(text)
    return 0 if all_ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--from-pickle", action="store_true")
    ap.add_argument("--workers", type=int, default=None)
    a = ap.parse_args()
    cells = list(enumerate(J.all_cells()))
    if a.smoke:
        res = T.compute_cells(cells[:2], n=40, workers=1)
        for r in res:
            an = T.analyze_cell(r, B=50)
            k = (T.PRIMARY_TIER, T.PRIMARY_POLICY, 0.80, "all")
            print(r["idx"], r["cell"], {x: (round(v, 3) if isinstance(v, float) else v) for x, v in an["cmp"][k].items() if x in ("r_min", "d_acc", "d_wc", "label", "safety")})
        print("smoke ok (plumbing only; no gates, no labels)")
        return 0
    if a.from_pickle:
        results = pickle.loads((OUT / "raw.pkl").read_bytes())
        prev = json.loads((OUT / "summary.json").read_text())
        gates = [(g, v["passed"], v["detail"]) for g, v in prev["gates"].items() if g != "G1"]
        real = dict(rows={cid: rs for cid, rs in prev["real_calls"].items()}, ref_ok=True, ref_detail=[]) if prev.get("real_calls") else None
        return finish(results, results[0]["n"], None, gates, real, True)
    results = T.compute_cells(cells, workers=a.workers)
    real = real_calls()
    g2, g3, g4 = T.gate_g2(), T.gate_g3(), T.gate_g4()
    again = T.compute_cells([cells[0], cells[8], cells[17]], workers=1)
    g6 = T.gate_g6([results[0], results[8], results[17]], again)
    gates = [("G2", *g2), ("G3", *g3), ("G4", *g4), ("G5", real["ref_ok"], "the real-call rows reproduce the probe table registered in Addendum 41" + ("" if real["ref_ok"] else "; DIFFERENCES: " + "; ".join(real["ref_detail"]))),
             ("G6", *g6)]
    rc = finish(results, J.N_EPISODES, a.workers, gates, real, False)
    print("hashes: study_tau", FC.sha256(Path(T.__file__))[:12], "| runner", FC.sha256(Path(__file__))[:12])
    return rc


if __name__ == "__main__":
    sys.exit(main())
