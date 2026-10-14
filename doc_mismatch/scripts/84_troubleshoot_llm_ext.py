"""Does "T3-noattr" (BAS access + a point map, no documented attributes; Exploratory note E2) hold up against the language model on Addendum 33's own 30 visits? Not a new experiment: it
applies one already-built item set (`v1/study_tiers_ext.py`, built on the user's own reported field finding) to the exact 30 visits Addendum 33 already ran the language model on, and reads
the numbers off together, the same way `scripts/80_minrate_vs_llm.py` did for the `min_rate` variants. No new language model call; Addendum 33's `llm_records.csv` is reused unchanged.
  .venv/bin/python doc_mismatch/scripts/84_troubleshoot_llm_ext.py
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot.v2 import study_llm as L  # noqa: E402
from docmismatch.troubleshoot.v2 import study_llm_ext as E  # noqa: E402

REPO = ROOT.parent
LLM_DIR = REPO / "results/docmismatch/troubleshoot_llm"
OUT = REPO / "results/docmismatch/troubleshoot_tiers_ext"


def load_llm_records(path: Path) -> dict:
    recs = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            n = int(row["complaints"])
            recs[(row["visit"], row["tier"], row["policy"])] = dict(minutes=float(row["minutes"]), checks=float(row["checks"]), correct=int(row["correct"]), n=n,
                                                                     acc=int(row["correct"]) / n, wcr=int(row["wrong_confident"]) / n, conc=int(row["concluded"]) / n,
                                                                     first_ahu=bool(int(row["first_check_ahu"])))
    return recs


def pct(x):
    return f"{100 * x:+.0f}%"


def main():
    vis = json.loads((LLM_DIR / "visits.json").read_text())
    visits, shares = vis["visits"], vis["shares"]
    _, wp, events = L.world()
    recs = load_llm_records(LLM_DIR / "llm_records.csv")
    cases = E.make_cases_ext()
    E.add_ext_routine(recs, visits, wp, events, cases)

    rows = [("llm", "T2"), ("llm", "T3"), (E.ROUTINE, "T2"), (E.ROUTINE, "T3"), (E.ROUTINE, E.EXT_ARM)]
    arr = {(p, t): L.strat_arrays(recs, visits, t, p) for p, t in rows}
    names = {("llm", "T2"): "LLM technician, T2", ("llm", "T3"): "LLM technician, T3", (E.ROUTINE, "T2"): "routine, T2 (attributes, no access)",
              (E.ROUTINE, "T3"): "routine, T3 (attributes + access + map)", (E.ROUTINE, E.EXT_ARM): "routine, T3-noattr (access + map, no attributes)"}

    L_ = ["# Does \"T3-noattr\" hold up against the language model? (Exploratory note E2, extended)", "",
          "`T3-noattr` = T1's items (equipment list, drawings' claims) plus `bas_access` and `point_map`, but no `attributes` -- the item set built in Exploratory note E2 from the user's "
          "reported field finding (BAS access and a point map common, documented attributes rare). This replays the routine (`tool_ticket_memo2`) at that item set on the exact 30 visits "
          "Addendum 33 already ran the language model on (same world, same `TableOracle` answers); the language model's own numbers are Addendum 33's stored ones, unchanged -- no new "
          "language model call. Simulation only; a language model is not a technician; the 30-visit sample is small (wide intervals); every minute and probability a placeholder.", "",
          "## Minutes / accuracy / wrong-and-confident / checks (all visits, kind shares reweighted)", "", "| policy | minutes | accuracy | wrong-and-confident | checks |", "|---|---|---|---|---|"]
    for p, t in rows:
        a = arr[(p, t)]
        L_.append(f"| {names[(p, t)]} | {L.wmean(a, shares, 'minutes'):.1f} | {L.wmean(a, shares, 'acc'):.0%} | {L.wmean(a, shares, 'wcr'):.1%} | {L.wmean(a, shares, 'checks'):.1f} |")

    comps = [(("llm", "T2"), (E.ROUTINE, E.EXT_ARM), "T3-noattr vs LLM@T2  [T3-noattr's speed win over the LLM's own faster pilot tier]"),
             (("llm", "T3"), (E.ROUTINE, E.EXT_ARM), "T3-noattr vs LLM@T3  [Addendum 33's actual comparison, but with attributes removed from the routine]"),
             ((E.ROUTINE, "T2"), (E.ROUTINE, E.EXT_ARM), "T3-noattr vs routine@T2  [what access + map alone buy over attributes alone, on this world/sample]"),
             ((E.ROUTINE, "T3"), (E.ROUTINE, E.EXT_ARM), "T3-noattr vs routine@T3  [what attributes still buy once access + map exist, on this world/sample]")]
    L_ += ["", "## Paired comparisons (routine@T3-noattr minus the other side; all visits, kind shares reweighted)", "",
           "| comparison | d minutes | d accuracy | d wrong-and-confident | time / accuracy | label |", "|---|---|---|---|---|---|"]
    for i, (b, a, label) in enumerate(comps):
        c = L.compare(arr[a], arr[b], shares, L.KINDS, (900 + i,))
        L_.append(f"| {label} | {c['d_min']:+.1f} ({pct(c['r_min'])}) | {c['d_acc']:+.3f} | {c['d_wc']:+.3f} | {c['time']} / {c['acc']} | {c['label']} |")

    L_ += ["", "## By kind: routine@T3-noattr minus LLM@T3", "", "| kind | d minutes | d accuracy | label |", "|---|---|---|---|"]
    for i, (sub, kinds) in enumerate(L.SUBS.items()):
        c = L.compare(arr[(E.ROUTINE, E.EXT_ARM)], arr[("llm", "T3")], shares, kinds, (950 + i,))
        L_.append(f"| {sub} | {c['d_min']:+.1f} ({pct(c['r_min'])}) | {c['d_acc']:+.3f} | {c['label']} |")

    L_ += ["", "## Reading", "",
           "T3-noattr sits between T2 and T3 by construction (T2's access, T3's map, neither's attributes). Read its row against both LLM pilots: beating LLM@T2 says the point map's speed "
           "carries even without attributes; the comparison against LLM@T3 is the one that matters most, since T3 is where the routine already won decisively in Addendum 33 -- this checks "
           "whether that margin survives losing attribute documentation. The by-kind table isolates whether any change is concentrated in shared-cause visits (the routine's own shortcut, "
           "unaffected by this item set) or elsewhere."]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "tiers_ext_vs_llm_report.md").write_text("\n".join(L_) + "\n")
    print(f"wrote {OUT / 'tiers_ext_vs_llm_report.md'}")


if __name__ == "__main__":
    main()
