"""Does the routine still capture the shared-cause saving once a cause exists that mostly does NOT make several rooms complain together? (PREREGISTRATION_DR.md Addendum 37.) Simulation
only; adds `causes.ECON_FAULT` as a third upstream state, additively (every existing addendum's cells are untouched -- gate G1). ONE cell (Addendum 30's primary shared/map/reliability
levels), both tiers, not the full 18-cell sweep (a deliberate, registered scoping-down, not an oversight).
  .venv/bin/python doc_mismatch/scripts/82_troubleshoot_econ.py               # the pre-registered run
  .venv/bin/python doc_mismatch/scripts/82_troubleshoot_econ.py --smoke       # plumbing check on 60 events, a small G1 replay; gates still enforced, numbers meaningless
  .venv/bin/python doc_mismatch/scripts/82_troubleshoot_econ.py --from-pickle # regenerate the report from the stored raw results
A failed gate means NO RESULT.
"""
import argparse
import csv
import pickle
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot.v2 import study_econ as E  # noqa: E402

REPO = ROOT.parent
OUT = REPO / "results/docmismatch/troubleshoot_econ"
SUBSETS_SHOWN = ("all", "shared", "econ_shared")
SUB_TEXT = {"all": "all events", "shared": "shared-cause events (any upstream cause)", "econ_shared": "econ_fault-shared events (2+ complaints, same air handler, econ_fault)"}


def pct(x):
    return "n/a" if x is None or x != x else f"{100 * x:.1f}%"


def f1(x):
    return "n/a" if x is None or x != x else f"{x:.1f}"


def report(res: dict, an: dict, g: dict, preds: dict, dec: str, smoke: bool, wall: float) -> str:
    L = ["# Does the routine still capture it once the shared cause rarely makes several rooms complain together? (Addendum 37)", "",
         "Adds `causes.ECON_FAULT` (\"the economizer is not delivering the free cooling it should\") as a third upstream state, additively: every function this touches (`state_prior`, "
         "`ahu_row`, `bears_on_ahu`, the J-table, `draw_event`) is a no-op with no extra state requested (gate G1), so no other addendum's stored results are affected by this file "
         "existing. Simulation only, the model's own family, every number a placeholder; nothing here is evidence about real buildings or technicians. ONE cell (Addendum 30's primary "
         "shared/map/reliability levels), both tiers, not the full 18-cell sweep.", "", "## Gates", "", "| gate | result | detail |", "|---|---|---|"]
    for name, (ok, detail) in g.items():
        L.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {detail} |")
    if smoke:
        L += ["", "**SMOKE RUN: gates are enforced but the numbers below are meaningless (too few events).**"]
    if not all(ok for ok, _ in g.values()):
        return "\n".join(L + ["", "## NO RESULT (a gate failed)"])
    L += ["", f"## The cell (n={res['n']} events per tier): minutes / checks / share of complaints correct / wrong-and-confident", ""]
    for sub in SUBSETS_SHOWN:
        L += [f"**{SUB_TEXT[sub]}**", "", "| tier | policy | minutes | checks | accuracy | wrong-and-confident |", "|---|---|---|---|---|---|"]
        for tier in E.TIERS:
            for pol in E.POLICIES:
                s = an["summary"][(tier, pol, sub)]
                if s.get("n", 0) == 0:
                    L.append(f"| {tier} | {pol} | n/a (0 events) | | | |")
                else:
                    L.append(f"| {tier} | {pol} | {f1(s['minutes'])} | {s['checks']:.1f} | {pct(s['accuracy'])} | {pct(s['wrong_confident'])} |")
        L.append("")
    L += ["## Complaints whose true cause is `econ_fault`: share correctly named, and wrong-and-confident", "",
          "| tier | policy | econ complaints | correctly named | wrong-and-confident |", "|---|---|---|---|---|"]
    for tier in E.TIERS:
        for pol in E.POLICIES:
            s = an["summary"][(tier, pol, "all")]
            L.append(f"| {tier} | {pol} | {s.get('econ_n', 0)} | {pct(s.get('econ_accuracy'))} | {pct(s.get('econ_wrong_confident'))} |")
    L += ["", f"Reference (a separate, fresh 2-state world, no econ_fault): the routine's/joint's own wrong-and-confident rate on `low_static`-caused complaints, which P4 compares "
          f"`econ_fault`'s rate against -- {', '.join(f'{k[0]}/{k[1]} {pct(v)}' for k, v in an['ref_low_static'].items())}.",
          "", f"`econ_fault`-shared events in this cell: {an['econ_shared_n']} of {res['n']}.", "",
          "## Predictions (written before any code existed; each strict)", "", "| prediction | holds | detail |", "|---|---|---|"]
    for k, (ok, detail) in preds.items():
        L.append(f"| {k} | {'holds' if ok else 'does not hold' if ok is False else 'not enough data'} | {detail} |")
    L += ["", f"## Frozen decision: {dec}", "", f"Run time {wall:.0f} s."]
    return "\n".join(L)


def write_csv(path: Path, res: dict, an: dict) -> None:
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tier", "policy", "subset", "n", "minutes", "checks", "accuracy", "wrong_confident", "econ_n", "econ_accuracy", "econ_wrong_confident"])
        for tier in E.TIERS:
            for pol in E.POLICIES:
                for sub in list(E.SUBSETS) + ["econ_shared"]:
                    s = an["summary"][(tier, pol, sub)]
                    if s.get("n", 0) == 0:
                        continue
                    w.writerow([tier, pol, sub, s["n"], f"{s['minutes']:.4f}", f"{s['checks']:.4f}", f"{s['accuracy']:.4f}", f"{s['wrong_confident']:.4f}",
                               s.get("econ_n", 0), f"{s.get('econ_accuracy', float('nan')):.4f}", f"{s.get('econ_wrong_confident', float('nan')):.4f}"])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--from-pickle", action="store_true")
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    if a.from_pickle:
        res = pickle.loads((a.out / "econ_raw.pkl").read_bytes())
        ref = pickle.loads((a.out / "econ_ref.pkl").read_bytes())
    else:
        n = 60 if a.smoke else E.N_EPISODES
        res = E.run_cell_econ(n)
        ref = E.run_reference_low_static(n)
        (a.out / "econ_raw.pkl").write_bytes(pickle.dumps(res))
        (a.out / "econ_ref.pkl").write_bytes(pickle.dumps(ref))
    cases = E.make_cases_econ()
    g = E.gates(res, cases, g1_events=20 if a.smoke else 200)
    an = E.analyze(res, ref)
    preds = E.predictions(res, an, g)
    dec = E.decision(preds)
    text = report(res, an, g, preds, dec, smoke=a.smoke, wall=time.time() - t0)
    (a.out / "econ_report.md").write_text(text + "\n")
    (a.out / "econ_analysis.pkl").write_bytes(pickle.dumps(an))
    write_csv(a.out / "econ_cells.csv", res, an)
    print(f"wrote {a.out / 'econ_report.md'}; gates: " + ", ".join(f"{k.split()[0]} {'PASS' if ok else 'FAIL'}" for k, (ok, _) in g.items()) + f"; decision: {dec}")
    if not all(ok for ok, _ in g.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
