"""Generate a small, verified batch of causal training examples using
`simulation.run_single_intervention_experiment`, and wire the results into
`datasets.py`'s `DatasetRecord`/`group_split`/leakage-check path.

Usage (from `symptom_pipeline/`, with the `physics` extra installed):

    uv run python scripts/generate_causal_batch.py

Requires the `physics_pipeline` sibling checkout with its vendored
EnergyPlus binary, and the root project's `data_cache/` (for the cached
Brick ontology `hvac_benchmark.experiment.candidates` needs).

## What this batch can and cannot demonstrate

Per `simulation.py`'s documented "KNOWN LIMITATIONS": `reassign_coil` is
the only fixed-inventory single intervention this pipeline supports, and
it is only exercisable on ONE of the 10 archetypes (`sys07_vav_reheat` --
the only building with two hydronic plant loops on different pumps).
**Every event in this batch is therefore on the same building lineage.**
`group_split` is still run (to prove the plumbing works and the leakage
checks pass), but with a single lineage it necessarily produces one
degenerate bucket, not a genuine train/val/test partition -- this is
reported explicitly in the output summary, not hidden. A real held-out
split needs either more archetypes with a qualifying second pump
(`physics_pipeline` has none today) or a second, independently-lineaged
intervention family.

`main(return_records=True)` is reused by `scripts/run_plumbing_check.py`
to get the in-memory `DatasetRecord`s (and the `tg`/`candidates`/
`ontology` they were built from) without re-deriving them -- CLI usage
(`main()` with no arguments) is unchanged and still only writes the JSON
summary.
"""

from __future__ import annotations

import json
from pathlib import Path

from hvac_benchmark.data.cache import FileCache
from hvac_benchmark.data.ontology import BrickOntology
from hvac_benchmark.experiment.candidates import generate_feeds_candidates
from hvac_benchmark.graph.networkx_build import TopologyGraph

from symptom_pipeline.contracts import DiscrepancyLabel, StructuredAnswers, SymptomReport
from symptom_pipeline.datasets import DatasetRecord, assert_no_lineage_leakage, assert_no_split_leakage, group_split
from symptom_pipeline.report_translation import DEGRADED_ERROR_LEVELS, degrade_report, translate_clean
from symptom_pipeline.simulation import discover_reassign_coil_specs, run_single_intervention_experiment

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parents[1] / "output"
BUILDING_ID = "sys07_vav_reheat"
N_EVENTS = 6  # kept small deliberately: each event costs 1-2 real EnergyPlus runs


def _load_ontology() -> BrickOntology:
    cache = FileCache(REPO_ROOT / "data_cache")
    return BrickOntology.load(cache)


def _documented_topology_graph():
    """Independent of `run_single_intervention_experiment`'s own internal
    extraction (which is scoped to one event at a time): loads the SAME
    baseline building once here, purely to get a `TopologyGraph` for
    `generate_feeds_candidates`, so this batch can label the FULL candidate
    universe per event (not just the two discordant pairs) the way a real
    training example needs.
    """
    from symptom_pipeline.simulation import import_physics_pipeline

    import_physics_pipeline()
    import openstudio
    from physics_pipeline.buildings import get_building
    from physics_pipeline.extract import extract_topology, to_hvac_benchmark_graph

    building = get_building(BUILDING_ID)
    translator = openstudio.osversion.VersionTranslator()
    model = translator.loadModel(openstudio.path(str(building.osm_path))).get()
    bid, ct, nx_graph, edges_by_relation, _ = extract_topology(model, BUILDING_ID, "documented")
    return to_hvac_benchmark_graph(bid, ct, nx_graph, edges_by_relation)


def main(return_records: bool = False):
    """Runs the batch. By default (CLI usage) returns nothing and only
    writes the JSON summary, matching the original behavior. Pass
    `return_records=True` (used by `scripts/run_plumbing_check.py`) to get
    back a dict with the in-memory `DatasetRecord`s plus the `tg`/
    `candidates`/`ontology` objects they were built from, instead of
    discarding them once the summary is written.
    """
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ontology = _load_ontology()
    tg: TopologyGraph = _documented_topology_graph()
    candidates = generate_feeds_candidates(tg, ontology)
    print(f"documented candidate universe size for {BUILDING_ID}: {len(candidates)}")

    specs = discover_reassign_coil_specs(BUILDING_ID)
    print(f"discovered {len(specs)} real reassign_coil interventions on {BUILDING_ID}")
    if not specs:
        raise SystemExit(f"no reassign_coil interventions available on {BUILDING_ID} -- nothing to generate")

    chosen = specs[:N_EVENTS]
    print(f"running {len(chosen)} of them:")
    for s in chosen:
        print(f"  coil={s.coil_id} -> pump={s.target_pump_id}")

    baseline_cache: dict = {}
    records: list[DatasetRecord] = []
    event_summaries: list[dict] = []
    failures: list[dict] = []

    for spec in chosen:
        try:
            truth, observables, event = run_single_intervention_experiment(
                spec, out_dir=OUT_DIR / "runs", baseline_cache=baseline_cache
            )
        except Exception as exc:  # noqa: BLE001 -- deliberately recorded, not swallowed
            failures.append({"spec": spec.event_id, "error": f"{type(exc).__name__}: {exc}"})
            print(f"FAILED {spec.event_id}: {type(exc).__name__}: {exc}")
            continue

        # Report the zone with the largest measured deviation -- an
        # empirical choice of "where the symptom actually shows up",
        # not an architectural guess, since coils have no direct graph
        # edge to a zone in the extracted topology.
        primary = max(observables.per_node, key=lambda z: abs(z.changed_mean_temp_c - z.baseline_mean_temp_c))
        deviation = primary.changed_mean_temp_c - primary.baseline_mean_temp_c

        labels = tuple(
            DiscrepancyLabel(
                source_id=c.source,
                target_id=c.target,
                relation=c.relation,
                is_discordant=(c.source, c.target) in event.discordant_pairs,
                event_id=event.event_id if (c.source, c.target) in event.discordant_pairs else None,
            )
            for c in candidates
        )
        n_positive = sum(l.is_discordant for l in labels)

        clean_answers = translate_clean(observables, primary_node_id=primary.node_id)
        reports = [SymptomReport(f"{event.event_id}_clean", BUILDING_ID, clean_answers, reporting_error_seed=None)]
        for level in DEGRADED_ERROR_LEVELS[1:]:
            seed = hash((event.event_id, level)) & 0xFFFF
            degraded = degrade_report(clean_answers, event_id=event.event_id, error_seed=seed, error_level=level)
            reports.append(SymptomReport(f"{event.event_id}_err{level}", BUILDING_ID, degraded, reporting_error_seed=seed))

        for report in reports:
            records.append(
                DatasetRecord(
                    event=event,
                    report=report,
                    labels=labels,
                    building_lineage_id=BUILDING_ID,
                    split="unassigned",
                )
            )

        event_summaries.append(
            {
                "event_id": event.event_id,
                "coil_id": spec.coil_id,
                "target_pump_id": spec.target_pump_id,
                "corruption_kind": event.corruption_kind.value,
                "discordant_pairs": sorted(event.discordant_pairs),
                "candidate_universe_size": len(candidates),
                "n_positive_labels": n_positive,
                "primary_zone": primary.node_id,
                "primary_zone_deviation_c": round(deviation, 3),
                "n_report_variants": len(reports),
            }
        )
        print(f"OK {event.event_id}: primary_zone={primary.node_id} deviation={deviation:+.2f}C n_positive={n_positive}")

    # --- split assignment (see module docstring: necessarily degenerate here) ---
    lineage_ids = [r.building_lineage_id for r in records]
    assignment = group_split(lineage_ids, seed=0)
    records = [DatasetRecord(r.event, r.report, r.labels, r.building_lineage_id, assignment[r.building_lineage_id]) for r in records]

    assert_no_split_leakage(records)
    assert_no_lineage_leakage(records)

    split_counts: dict[str, int] = {}
    for r in records:
        split_counts[r.split] = split_counts.get(r.split, 0) + 1

    summary = {
        "building_id": BUILDING_ID,
        "n_events_attempted": len(chosen),
        "n_events_succeeded": len(event_summaries),
        "n_events_failed": len(failures),
        "failures": failures,
        "n_dataset_records": len(records),
        "split_counts": split_counts,
        "split_note": (
            "single building lineage (sys07_vav_reheat) -- group_split necessarily produced one "
            "degenerate bucket; this is NOT a genuine held-out partition, see this script's docstring"
        ),
        "events": event_summaries,
    }
    summary_path = OUT_DIR / "causal_batch_v1_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str))
    print(f"\nwrote summary to {summary_path}")
    print(json.dumps(summary, indent=2, default=str))

    if return_records:
        return {"records": records, "tg": tg, "candidates": candidates, "ontology": ontology, "summary": summary}
    return None


if __name__ == "__main__":
    main()
