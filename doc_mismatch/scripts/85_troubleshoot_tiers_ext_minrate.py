"""Does the already-confirmed `min_rate` lever also make the T3-noattr documentation profile (Exploratory note E2) faster, and does it close the gap against the language model that
E2's extension found on ordinary (non-shared) complaints? Exploratory: a parameter sweep of an existing, already-tested knob, applied to an existing, already-tested item set -- no new
engine code, no new modeling risk. NOT a full 18-cell pre-registered confirmation like Addenda 34-36 gave the full-documentation tiers; a 5-cell spot-check stands in for that here.
  .venv/bin/python doc_mismatch/scripts/85_troubleshoot_tiers_ext_minrate.py
"""
import csv
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot.v2 import study_llm as L  # noqa: E402
from docmismatch.troubleshoot.v2 import study_llm_ext as E  # noqa: E402
from docmismatch.troubleshoot.v2 import study_minrate_ext as MX  # noqa: E402

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
    t0 = time.time()
    sweep = MX.primary_sweep()
    spot = MX.cell_spot_check()

    vis = json.loads((LLM_DIR / "visits.json").read_text())
    visits, shares = vis["visits"], vis["shares"]
    _, wp, events = L.world()
    recs = load_llm_records(LLM_DIR / "llm_records.csv")
    llm_cmp = MX.llm_comparison(visits, shares, events, wp, recs)

    L_ = ["# Does the `min_rate` lever help the T3-noattr documentation profile beat the language model? (Exploratory note E2, extended further)", "",
          "Asked directly by the user: does raising `min_rate` (already confirmed, Addenda 34-36, for the fully-documented tiers) also help T3-noattr, trading a small accuracy cost for "
          "a large speed gain? No new engine code: reuses `study_minrate.py`'s own sweep machinery, pointed at the T3-noattr item set. Simulation only; every number a placeholder; the "
          "language model's own numbers are Addendum 33's stored ones, unchanged (no new LLM call).", "",
          "## Primary cell sweep (1000 events; `min_rate` = 0.003 is the pre-tuning baseline, i.e. what Exploratory note E2's extension originally reported)", "",
          "| min_rate | minutes | accuracy | wrong-and-confident | checks | single min | multi min | shared min |", "|---|---|---|---|---|---|---|---|"]
    for row in sweep:
        L_.append(f"| {row['min_rate']:g} | {row['minutes']:.1f} | {row['acc']:.1%} | {row['wc']:.2%} | {row['checks']:.1f} | {row['single_minutes']:.1f} | {row['multi_minutes']:.1f} | "
                   f"{row['shared_minutes']:.1f} |")
    base = sweep[0]
    L_ += ["", f"Baseline (0.003): {base['minutes']:.1f} min / {base['acc']:.1%} accuracy. Reading: minutes fall smoothly and accuracy erodes gently out to about 0.02-0.022, then the "
           "trade-off worsens sharply from 0.025 to 0.03 (a cliff, not a gentle slope) -- the same shape Addendum 34 found for the fully-documented tiers, just at somewhat higher "
           f"`min_rate` values (T3-noattr's checks are individually more expensive here, so the bar has more room to rise before it starts cutting into checks that matter).", "",
          "## Spot-check across 5 of Addendum 30's 18 cells (a spread of shared frequency / map fault / reliability, not just the primary cell), baseline vs the candidate (0.02)", "",
          "| cell | min_rate=0.003 | min_rate=0.02 | d minutes | d accuracy | d wrong-and-confident |", "|---|---|---|---|---|---|"]
    for row in spot:
        b, c = row[0.003], row[MX.CANDIDATE]
        L_.append(f"| {row['cell']} | {b['minutes']:.1f} min / {b['acc']:.1%} / {b['wc']:.2%} | {c['minutes']:.1f} min / {c['acc']:.1%} / {c['wc']:.2%} | "
                   f"{c['minutes'] - b['minutes']:+.1f} ({pct((c['minutes'] - b['minutes']) / b['minutes'])}) | {c['acc'] - b['acc']:+.3f} | {c['wc'] - b['wc']:+.3f} |")
    L_ += ["", "Every one of the 5 cells: 24-31% fewer minutes, an accuracy cost of 0.4-2.6 points, and wrong-and-confident IMPROVES (never worsens) at every cell checked -- the "
           "direction and rough size hold up across very different shared-frequency, map-fault and reliability conditions, not just the one cell the fine sweep above used.", "",
          "## Against the language model, on Addendum 33's own 30 visits, at each candidate `min_rate` (all visits, kind shares reweighted)", "",
          "| min_rate | minutes | accuracy | wrong-and-confident | vs LLM@T2 | vs LLM@T3 |", "|---|---|---|---|---|---|"]
    for mr, d in llm_cmp.items():
        s = d["summary"]["all"]
        c2, c3 = d["vs_t2"]["all"], d["vs_t3"]["all"]
        L_.append(f"| {mr:g} | {s['minutes']:.1f} | {s['acc']:.1%} | {s['wcr']:.1%} | {c2['d_min']:+.1f} ({pct(c2['r_min'])}), {c2['label']} | {c3['d_min']:+.1f} ({pct(c3['r_min'])}), {c3['label']} |")
    L_ += ["", "## By kind, at the candidate (min_rate = 0.02): routine@T3-noattr minus LLM@T3 (the comparison E2's extension found losing on ordinary complaints)", "",
           "| kind | d minutes | d accuracy | label |", "|---|---|---|---|"]
    for sub, c in llm_cmp[MX.CANDIDATE]["vs_t3"].items():
        L_.append(f"| {sub} | {c['d_min']:+.1f} ({pct(c['r_min'])}) | {c['d_acc']:+.3f} | {c['label']} |")
    L_ += ["", "## Reading", "",
           f"**Recommendation: `min_rate` = {MX.CANDIDATE:g} for the T3-noattr profile specifically** (a separate decision from the live tool's shipped 0.015, which was tuned for the "
           "fully-documented tiers). At this value: the primary cell is about 25% faster for under 2 accuracy points, never worse on safety across the 5-cell spot-check, and -- the thing "
           "the user actually asked about -- the by-kind comparison against the language model flips from WORSE to NEITHER on single- and multi-complaint visits (no longer losing on "
           "ordinary complaints), while the aggregate becomes a clean, statistically real IMPROVES over both LLM pilots on speed, with accuracy still higher, not lower, than the language "
           "model's own. Going further (0.025) buys more speed for a larger but still moderate accuracy cost; 0.03 and beyond is a cliff, not a gentle trade, and is not recommended. "
           "**Caveat named up front: this is exploratory, not the full 18-cell pre-registered confirmation Addenda 34-36 gave the fully-documented tiers' `min_rate` values** -- the 5-cell "
           "spot-check is reassuring but is not that bar. If this value is to be shipped as a default for buildings matching this documentation profile, the same 18-cell confirmation "
           "done for 0.01/0.015 would be the honest next step, not assumed here."]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "tiers_ext_minrate_report.md").write_text("\n".join(L_) + "\n")
    print(f"wrote {OUT / 'tiers_ext_minrate_report.md'}; {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
