"""Structural sensor audit across the full real building corpus (PREREGISTRATION_DR.md Addendum 5b): for every
VAV box in every real building hvac_benchmark has ingested (44 anonymized MORTAR buildings + the ORNL `rtu_exp`
testbed -- offline from data_cache/, never the network, never any timeseries or label), does its OWN Brick
documentation already list an airflow point (the instrument `vav_zone` channels 0/2 need)?

Unlike scripts/34, this needs no real DEV/SEALED split at all: it is a pure documentation-completeness question,
answerable for every real building hvac_benchmark has a graph for, including the 44 that have no timeseries.
  .venv/bin/python doc_mismatch/scripts/36_real_corpus_sensor_audit.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.active import brick_bridge as B  # noqa: E402
from docmismatch.active import measurement as M  # noqa: E402
from docmismatch.dr.pools import DR_DIR  # noqa: E402

OUT = DR_DIR / "measurement"
SLOT, CHANNEL = "vav_zone", 0   # channel 0's owner-side requirement is "flow"; channel 2 needs the same instrument


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    topos, ontology = B.load_real_topologies()

    per_building = {}
    totals = {True: 0, False: 0, None: 0}
    for bid, tg in sorted(topos.items()):
        vavs = B.class_nodes(tg, ontology, "VAV")
        if not vavs:
            per_building[bid] = dict(n_vav=0, present=0, absent=0, undetermined=0)
            continue
        counts = {True: 0, False: 0, None: 0}
        for v in vavs:
            met = B.structural_requirement_met(tg, ontology, v, None, SLOT, CHANNEL)
            counts[met] += 1
            totals[met] += 1
        per_building[bid] = dict(n_vav=len(vavs), present=counts[True], absent=counts[False], undetermined=counts[None])

    n_bldg_with_vav = sum(1 for v in per_building.values() if v["n_vav"] > 0)
    n_bldg_any_present = sum(1 for v in per_building.values() if v["present"] > 0)
    md = ["# Real building corpus: does the documentation already have the sensor `vav_zone` channels 0/2 need? (Addendum 5b)", "",
          f"{len(topos)} real buildings (44 anonymized MORTAR + ORNL `rtu_exp`), offline from `data_cache/`, never the network. "
          f"{n_bldg_with_vav} have at least one VAV-class node. Per VAV box: does a `hasPoint` edge lead to a point whose Brick "
          "class is-a `Flow_Sensor` (present), confidently does not (absent), or is undetermined (a point exists under a Brick "
          "class the reference ontology cannot place -- never guessed)?", "",
          f"**Corpus-wide: {totals[True]} present / {totals[False]} absent / {totals[None]} undetermined VAV boxes "
          f"({n_bldg_any_present}/{n_bldg_with_vav} buildings have at least one VAV box with the airflow point already documented).**",
          "", "| building | n VAV | present | absent | undetermined |", "|---|---|---|---|---|"]
    for bid, c in per_building.items():
        if c["n_vav"] == 0:
            continue
        md.append(f"| {bid} | {c['n_vav']} | {c['present']} | {c['absent']} | {c['undetermined']} |")
    md += ["", f"({sum(1 for v in per_building.values() if v['n_vav'] == 0)} buildings have no VAV-class node at all -- "
           "`vav_zone` recommendations never apply to them.)"]

    # a worked example: the actual recommendation text for one building's first VAV box, where the point is absent
    example = None
    for bid, tg in topos.items():
        vavs = B.class_nodes(tg, ontology, "VAV")
        for v in vavs:
            if B.structural_requirement_met(tg, ontology, v, None, SLOT, CHANNEL) is False:
                example = (bid, v, M.describe_requirement(SLOT, CHANNEL, tg=tg, ontology=ontology, owner_node=v))
                break
        if example:
            break
    if example:
        md += ["", "## Worked example", "", f"Building `{example[0]}`, VAV node `{example[1]}`:", "", f"> {example[2]}"]

    (OUT / "real_corpus_sensor_audit.json").write_text(json.dumps(per_building, indent=2))
    (OUT / "real_corpus_sensor_audit.md").write_text("\n".join(md))
    print("\n".join(md))


main()
