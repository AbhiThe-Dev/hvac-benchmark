"""Does the tuned routine close the language model's speed edge from Addendum 33? Not a new experiment: it applies one already-fixed `min_rate` (chosen before this script existed, on
evidence that never involved the language model) to the exact 30 visits Addendum 33 already ran the language model on, and reads the numbers off together. No new tuning happens here, no
LLM is run, and nothing about either frozen result changes.
  .venv/bin/python doc_mismatch/scripts/80_minrate_vs_llm.py                    # the shipped default (0.02; NOT the 18-cell-confirmed 0.01 -- pass --min-rate 0.01 for that comparison)
  .venv/bin/python doc_mismatch/scripts/80_minrate_vs_llm.py --min-rate 0.01    # Addendum 35's confirmed value
"""
import argparse
import csv
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot.v2 import cli as V2CLI  # noqa: E402  (the live tool's own default, so this script can never drift from what actually ships)
from docmismatch.troubleshoot.v2 import policies as P  # noqa: E402
from docmismatch.troubleshoot.v2 import study_llm as L  # noqa: E402
from docmismatch.troubleshoot.v2 import study_minrate as MR  # noqa: E402
from docmismatch.troubleshoot.v2 import world2 as W  # noqa: E402

REPO = ROOT.parent
LLM_DIR = REPO / "results/docmismatch/troubleshoot_llm"
OUT = REPO / "results/docmismatch/troubleshoot_minrate"
LIVE_DEFAULT = V2CLI.LIVE_MIN_RATE_DEFAULT  # reads the live tool's own default; this script can never silently drift from what actually ships
CONFIRMED = MR.CHALLENGER  # 0.01, Addendum 35's 18-cell-confirmed value


def names_comps(tuned_label, mr):
    tuned = f"tool_ticket_memo2_mr{mr}"
    names = {"llm": "LLM technician", "tool_ticket_memo2": "routine (min_rate=0.003, as it stands)", tuned: f"routine, tuned (min_rate={mr:g}{tuned_label})", "tool_joint2": "joint tool",
             "fast_parent": "fast_parent (my rule)"}
    comps = {"A": ("llm", tuned, "LLM - tuned routine  [does tuning close the gap?]"), "B": (tuned, "tool_ticket_memo2", "tuned - original routine  [the tuning itself, on this sample]"),
             "C": ("llm", "tool_ticket_memo2", "LLM - original routine  [Addendum 33's comparison, replayed here]"), "D": (tuned, "fast_parent", "tuned - fast_parent")}
    return tuned, names, comps


def load_llm_records(path: Path) -> dict:
    recs = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            n = int(row["complaints"])
            recs[(row["visit"], row["tier"], row["policy"])] = dict(minutes=float(row["minutes"]), checks=float(row["checks"]), correct=int(row["correct"]), n=n,
                                                                     acc=int(row["correct"]) / n, wcr=int(row["wrong_confident"]) / n, conc=int(row["concluded"]) / n,
                                                                     first_ahu=bool(int(row["first_check_ahu"])))
    return recs


def add_tuned_routine(recs: dict, visits: list, wp, events: list, tuned: str, mr: float) -> None:
    for v in visits:
        ev = events[v["event"]]
        for t in L.TIERS:
            cbr = MR.cases_with(t, mr)
            cs = [cbr[r] for r in ev.rooms]
            ctxs = [W.context_dict(t, r) for r in ev.rooms]
            res = P.run_policy("tool_ticket_memo2", cs, L.TableOracle(ev, wp.rel_a), ctxs)
            recs[(v["id"], t, tuned)] = L.record(res, ev)


def pct(x):
    return f"{100 * x:+.0f}%"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-rate", type=float, default=LIVE_DEFAULT, help=f"defaults to the live tool's own current default ({LIVE_DEFAULT:g})")
    a = ap.parse_args(argv)
    mr = a.min_rate
    status = ("the live default" if mr == LIVE_DEFAULT else "") + (" and " if mr == LIVE_DEFAULT and mr == CONFIRMED else "") + ("Addendum 35's 18-cell-confirmed value" if mr == CONFIRMED else "")
    status = status or "neither the live default nor the 18-cell-confirmed value"
    caveat = "" if mr == CONFIRMED else f" This value ({mr:g}) has only been checked on the primary cell, NOT confirmed across the other 17 cells the way {CONFIRMED:g} was (Addendum 35)."

    vis = __import__("json").loads((LLM_DIR / "visits.json").read_text())
    visits, shares = vis["visits"], vis["shares"]
    _, wp, events = L.world()
    recs = load_llm_records(LLM_DIR / "llm_records.csv")
    tuned, names, comps = names_comps("", mr)
    add_tuned_routine(recs, visits, wp, events, tuned, mr)
    pols = ("llm", "tool_ticket_memo2", tuned, "tool_joint2", "fast_parent")
    arr = {(t, p): L.strat_arrays(recs, visits, t, p) for t in L.TIERS for p in pols}

    L_ = [f"# The tuned routine (min_rate = {mr:g}) against the language model, on Addendum 33's own 30 visits", "",
          f"`min_rate` = {mr:g} here is {status}.{caveat} Not a new experiment otherwise: it applies an already-fixed setting (chosen on evidence that never involved a language model) to "
          "the exact 30 visits Addendum 33 already ran the language model on, and reads the numbers off together. Simulation only; a language model is not a technician; the 30-visit sample "
          "is small (wide intervals).", "", "## Minutes / accuracy / wrong-and-confident / checks (all visits, kind shares reweighted)", "", "| policy | T2 | T3 |", "|---|---|---|"]
    for p in pols:
        row = []
        for t in L.TIERS:
            arr_ = arr[(t, p)]
            row.append(f"{L.wmean(arr_, shares, 'minutes'):.1f} min / {L.wmean(arr_, shares, 'acc'):.0%} / {L.wmean(arr_, shares, 'wcr'):.1%} / {L.wmean(arr_, shares, 'checks'):.1f}")
        L_.append(f"| {names[p]} | " + " | ".join(row) + " |")
    L_ += ["", "## Paired comparisons (all visits, kind shares reweighted)", "", "| comparison | tier | d minutes | d accuracy | d wrong-and-confident | time / accuracy | label |", "|---|---|---|---|---|---|---|"]
    for key, (a_, b_, label) in comps.items():
        for t in L.TIERS:
            c = L.compare(arr[(t, a_)], arr[(t, b_)], shares, L.KINDS, (hash((key, t, mr)) % 100000,))
            L_.append(f"| {key}: {label} | {t} | {c['d_min']:+.1f} ({pct(c['r_min'])}) | {c['d_acc']:+.3f} | {c['d_wc']:+.3f} | {c['time']} / {c['acc']} | {c['label']} |")
    L_ += ["", "## By kind: LLM minus the tuned routine", "", "| kind | tier | d minutes | d accuracy | label |", "|---|---|---|---|---|"]
    for sub, kinds in L.SUBS.items():
        for t in L.TIERS:
            c = L.compare(arr[(t, "llm")], arr[(t, tuned)], shares, kinds, (hash((sub, t, mr)) % 100000,))
            L_.append(f"| {sub} | {t} | {c['d_min']:+.1f} ({pct(c['r_min'])}) | {c['d_acc']:+.3f} | {c['label']} |")
    L_ += ["", "## Reading", "",
           "See the tables: read off, per tier, whether the tuned routine and the language model differ in speed (time column), accuracy and wrong-and-confident, and whether that difference "
           "is a real one (the label) or within noise (NEITHER). By kind: on shared-cause visits the routine's own shortcut, not this tuning, is what keeps it ahead of the language model "
           "(Addendum 33)."]
    out_name = "vs_llm_report.md" if mr == CONFIRMED else f"vs_llm_report_{mr:g}.md"
    (OUT / out_name).write_text("\n".join(L_) + "\n")
    print(f"wrote {OUT / out_name}")


if __name__ == "__main__":
    main()
