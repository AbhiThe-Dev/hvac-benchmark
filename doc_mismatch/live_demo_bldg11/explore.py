"""EXPLORATORY, post-hoc breakdown of the registered 100-visit run (SIM_PROTOCOL.md). Nothing here is registered, scored or allowed to change a verdict in report.md; it only says where the
registered numbers come from. Reads results/docmismatch/bldg11_sim/complaints.csv, writes exploratory.md next to it.

  .venv/bin/python doc_mismatch/live_demo_bldg11/explore.py
"""

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "docmismatch" / "bldg11_sim"
BUILDING = ROOT / "data_cache" / "demo_bldg11" / "building_v2.json"
POLS = ("tool_shipped", "tool_adjusted", "fast_parent")


def main() -> None:
    claims = json.loads(BUILDING.read_text())["claims"]
    ahu_of_room = {z: claims["ahu_vav"][b] for z, b in claims["vav_zone"].items()}
    rows = list(csv.DictReader(open(OUT / "complaints.csv")))
    L = ["# Exploratory breakdown of the registered run (post-hoc; not registered, scores nothing)", "",
         "Source: `complaints.csv` of the registered run. Strict scoring is the registered one: a complaint is right only if the leading cause equals the true first-order cause.", ""]
    for world in ("W0", "W1"):
        L += [f"## {world}", "", "| policy | concluded | concluded and wrong | of which: local fault on a room of the faulty handler, named low static | false shared call, local visits | false shared call, shared visits (AHU06 rooms) | (AHU05 rooms) |", "|---|---|---|---|---|---|---|"]
        for pol in POLS:
            rs = [r for r in rows if r["world"] == world and r["policy"] == pol]
            conc = [r for r in rs if r["concluded"] == "1"]
            wc = [r for r in conc if r["correct"] == "0"]
            fold = [r for r in wc if r["kind"] == "shared" and r["truth"] != "low_static" and r["guess"] == "low_static" and ahu_of_room[r["room"]] == "AHU06"]

            def fsc(kind, ahu=None):
                nl = [r for r in rs if r["truth"] != "low_static" and r["kind"] == kind and (ahu is None or ahu_of_room[r["room"]] == ahu)]
                return f"{sum(r['guess'] == 'low_static' for r in nl)}/{len(nl)}"
            L.append(f"| {pol} | {len(conc)} of {len(rs)} | {len(wc)} ({100 * len(wc) / max(1, len(conc)):.0f}% of concluded) | {len(fold)} | {fsc('local')} | {fsc('shared', 'AHU06')} | {fsc('shared', 'AHU05')} |")
        L.append("")
    L += ["## What the folded calls are", "",
          "In a shared visit, a complaint whose own cause is local but whose room hangs on the faulty handler is scored wrong if the tool names low static. Physically such a room is starved *and* has its own "
          "fault, so 'wrong' there means 'missed the second fault', not 'named a cause that is not present'. The registered metric (one first-order cause per complaint, listed as a limitation in the protocol) "
          "does not credit it.", "",
          "Alternative scoring, NOT registered, shown only to size the effect: count a low-static call on a local-cause room of the faulty handler in a shared visit as correct.", "",
          "| policy | world | registered accuracy | accuracy with those calls counted correct | registered wrong-and-confident | with those calls removed |", "|---|---|---|---|---|---|"]
    for pol in ("tool_adjusted",):
        for world in ("W0", "W1"):
            rs = [r for r in rows if r["world"] == world and r["policy"] == pol]
            n = len(rs)
            fold_all = [r for r in rs if r["kind"] == "shared" and r["truth"] != "low_static" and r["guess"] == "low_static" and ahu_of_room[r["room"]] == "AHU06"]
            acc = sum(r["correct"] == "1" for r in rs) / n
            wc = sum(r["concluded"] == "1" and r["correct"] == "0" for r in rs) / n
            wc2 = sum(r["concluded"] == "1" and r["correct"] == "0" and r not in fold_all for r in rs) / n
            L.append(f"| {pol} | {world} | {100 * acc:.1f}% | {100 * (acc * n + len(fold_all)) / n:.1f}% | {100 * wc:.1f}% | {100 * wc2:.1f}% |")
    L += ["", "Reading: the confident errors of `tool_adjusted` are almost all this one pattern. Without it the safety bar would be met at W0 and W1; with it, it is not, and the registered verdict "
          "(UNSAFE) stands because the bar was fixed before the run."]
    (OUT / "exploratory.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
