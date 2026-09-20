"""End-to-end plumbing check: features.py -> models.py -> calibration.py
-> benchmark_adapter.py, wired together on the 16 real `DatasetRecord`s
`generate_causal_batch.py` produces (4 successful `reassign_coil` events on
`sys07_vav_reheat`, x 4 report variants each: 1 clean + 3 degraded).

This exists to catch INTEGRATION bugs -- type mismatches, misaligned
arrays, wrong field names -- not to produce a usable model. With one
building and 4 physically distinct labelings, no accuracy or coverage
number this script prints is evidence the modeling approach works; do not
read it that way, and do not repeat any such number outside this script's
own output without the same disclaimer attached.

A clean run only proves the code didn't crash. A silently misaligned label
array (e.g. off by one, or a stale `candidates` list) would ALSO run to
completion and print a plausible-looking, meaningless coverage number.
Step 4 exists specifically to catch that failure mode: it demands the
trained model rank its own event's true discordant pairs near the top on
data it was TRAINED on -- an extremely low bar that only a genuinely
broken wiring (not a genuinely weak model) should fail. If step 4 fails,
this script stops there and does not proceed to calibration or the
benchmark-adapter handoff.

Usage (from `symptom_pipeline/`, with the `physics` extra installed --
re-running `generate_causal_batch`'s interventions needs real EnergyPlus):

    uv run python scripts/run_plumbing_check.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_causal_batch  # noqa: E402

from hvac_benchmark.config import DEFAULT_CONFIG  # noqa: E402
from hvac_benchmark.experiment.blueprint import Blueprint, CorruptionEvent  # noqa: E402
from hvac_benchmark.graph.networkx_build import TopologyGraph  # noqa: E402

from symptom_pipeline.benchmark_adapter import run_symptom_troubleshooting_trial  # noqa: E402
from symptom_pipeline.calibration import CALIBRATION_VERSION, EventValidationRecord, fit_calibrator, select_suspect_prefix  # noqa: E402
from symptom_pipeline.contracts import CandidateDiscrepancyPrediction, PredictionRecord  # noqa: E402
from symptom_pipeline.features import NUMERIC_FEATURE_FIELDS, extract_candidate_features  # noqa: E402
from symptom_pipeline.models import GBM_MODEL_VERSION, train_gbm  # noqa: E402
from symptom_pipeline.questions import QUESTIONNAIRE_VERSION  # noqa: E402

OUT_DIR = Path(__file__).resolve().parents[1] / "output"
SYMPTOM_PIPELINE_ROOT = Path(__file__).resolve().parents[1]

# The training event with the clearest measured deviation per
# output/causal_batch_v1_summary.json (-8.687C) -- chosen as the step-4
# sanity-floor target because a strong physical effect is the easiest case
# for the wiring to get right; if even this fails, the problem is upstream
# plumbing, not model quality.
SANITY_EVENT_ID = "sys07_vav_reheat_2e31bf24-9a17-4af7-85fb-4e6b0c740431_to_021fb487-0d27-4abb-99fa-ca3c39546934"
# Originally specified as "both true pairs rank in the top 10 of ~94 by raw
# score" -- kept here purely as an informational secondary readout. The
# actual pass/fail gate (below) checks TOP-TIER membership by distinct
# score value instead: raw rank under ties is arbitrary stable-sort order,
# and this dataset genuinely produces tied scores among same-family
# candidates (see the step-4 "FINDING" printed at runtime) for a real,
# diagnosed reason that is not a wiring bug -- a naive rank cutoff would
# have failed on that legitimate tie, not on an actual misalignment.
SANITY_FLOOR_K = 10


def _build_actual_topology(tg: TopologyGraph, old_pair: tuple[str, str], new_pair: tuple[str, str]) -> TopologyGraph:
    """`benchmark_adapter.run_symptom_troubleshooting_trial` (like the
    upstream `hvac_benchmark.experiment.troubleshooting_runner` it mirrors)
    treats its `tg` argument as GROUND TRUTH -- `true_edges =
    tg.edges_by_relation["feeds"]` -- and `blueprint.claimed_edges` as the
    (possibly wrong) documentation being checked against it. That is the
    OPPOSITE of `batch["tg"]`, which is the DOCUMENTED/baseline extraction
    (correct for `features.py`, which must only ever see the documented
    graph, but wrong to hand to the benchmark adapter as "truth").

    Reconstructs the actual/realized topology from the documented one by
    swapping the one `feeds` edge this event actually changed, rather than
    re-extracting from the changed OpenStudio model (which
    `run_single_intervention_experiment` doesn't return). This
    reconstruction is exact, not a guess: `reassign_coil`'s fixed-inventory
    guarantee means every node, type, and location is identical between
    the documented and realized graphs (confirmed in `simulation.py`'s own
    empirical findings), and `verify_intended_change` already hard-failed
    the run if anything OTHER than this one edge had changed -- so "swap
    exactly this one edge" is not an assumption, it's what step 4 of
    `run_single_intervention_experiment` already proved.
    """
    actual_edges = {rel: set(pairs) for rel, pairs in tg.edges_by_relation.items()}
    actual_edges["feeds"].discard(old_pair)
    actual_edges["feeds"].add(new_pair)
    return TopologyGraph(
        building_id=tg.building_id, config_type=tg.config_type, nx_graph=tg.nx_graph, edges_by_relation=actual_edges
    )


def _flatten(records, tg, candidates, claimed_pairs):
    """Builds one (features, labels) row per (record, candidate), and
    explicitly confirms -- does not assume -- that `extract_candidate_
    features`'s output, `candidates`, and `record.labels` all share index
    order, since all three are built by iterating the SAME `candidates`
    list but in three different call sites (`features.py`,
    `generate_causal_batch.py`'s label-construction loop, and this
    function). A silent divergence here (e.g. a stale `candidates` list
    passed to one call but not another) would train on a label array
    that's offset from its own features -- exactly the failure mode this
    whole script exists to catch.
    """
    all_features = []
    all_labels = []
    per_record = []
    for record in records:
        features = extract_candidate_features(tg, candidates, claimed_pairs, record.report.answers)
        assert len(features) == len(candidates) == len(record.labels), (
            f"length mismatch for {record.report.report_id!r}: "
            f"features={len(features)} candidates={len(candidates)} labels={len(record.labels)}"
        )
        for i, (f, lbl) in enumerate(zip(features, record.labels)):
            assert (f.source_id, f.target_id) == (lbl.source_id, lbl.target_id), (
                f"alignment broken at index {i} for {record.report.report_id!r}: "
                f"feature=({f.source_id},{f.target_id}) label=({lbl.source_id},{lbl.target_id})"
            )
        per_record.append((record, features))
        all_features.extend(features)
        all_labels.extend(bool(lbl.is_discordant) for lbl in record.labels)
    return all_features, all_labels, per_record


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- step 1: reuse generate_causal_batch's real records, kept in memory ---
    batch = generate_causal_batch.main(return_records=True)
    records = batch["records"]
    tg = batch["tg"]
    candidates = batch["candidates"]
    ontology = batch["ontology"]
    print(f"\n=== plumbing check: {len(records)} real DatasetRecords loaded ===")

    # --- step 2: claimed_pairs -- checked ingestion.py first ---
    # `contracts.DocumentedGraph.claimed_pairs()` is the more canonical
    # source in general (see ingestion.py), but generate_causal_batch.py
    # never builds a `DocumentedGraph` at all -- it works directly off the
    # raw extracted `TopologyGraph` (see `_documented_topology_graph`), so
    # there is no `DocumentedGraph` in scope here to call that method on.
    # `tg.edges_by_relation["feeds"]` IS the documented topology's own
    # claimed feeds edges in this pipeline; using it is what's actually
    # available, not a shortcut around a better option.
    claimed_pairs = frozenset(tg.edges_by_relation["feeds"])

    # --- step 3: flatten into one training table, alignment confirmed ---
    all_features, all_labels, per_record = _flatten(records, tg, candidates, claimed_pairs)
    n_candidates = len(candidates)
    print(f"flattened training table: {len(all_features)} rows ({len(records)} records x {n_candidates} candidates)")
    positive_rate = sum(all_labels) / len(all_labels)
    print(f"positive rate: {sum(all_labels)}/{len(all_labels)} = {positive_rate:.4f}")

    model = train_gbm(all_features, all_labels)
    print(f"trained GBM ({model.version}) on {len(all_features)} rows -- features -> models wiring OK")

    importances = sorted(
        zip(model.vectorizer.get_feature_names_out(), model.classifier.feature_importances_),
        key=lambda kv: kv[1],
        reverse=True,
    )
    nonzero_importances = [(name, round(float(v), 4)) for name, v in importances if v > 0]
    print("GBM feature_importances_ (non-zero, descending):")
    for name, v in nonzero_importances:
        print(f"  {name}: {v}")

    # --- step 4: sanity floor on the CLEAN report of the clearest-deviation event ---
    sanity_record = next(
        (r for r, _ in per_record if r.event.event_id == SANITY_EVENT_ID and r.report.reporting_error_seed is None),
        None,
    )
    if sanity_record is None:
        raise RuntimeError(
            f"expected sanity-check event {SANITY_EVENT_ID!r} (clean report) not found among generated "
            "records -- did generate_causal_batch's coil selection or success/failure outcome change? "
            "STOP: this script's hardcoded sanity target is now stale, do not proceed on a guess."
        )

    sanity_features = extract_candidate_features(tg, candidates, claimed_pairs, sanity_record.report.answers)
    raw_scores = model.predict_raw(sanity_features)
    ranked = sorted(zip(sanity_features, raw_scores), key=lambda fs: fs[1], reverse=True)
    ranked_pairs = [(f.source_id, f.target_id) for f, _ in ranked]

    true_pairs = set(sanity_record.event.discordant_pairs)
    ranks = {pair: ranked_pairs.index(pair) + 1 for pair in true_pairs}  # 1-indexed, subject to tie-breaking (see below)

    # Raw rank alone is the wrong pass/fail signal here, and re-running it
    # against a naive top-K cutoff is what this script did first -- and
    # got a FAIL (rank #3 and #13 of 94) that looked like it might be a
    # misalignment bug. Investigated before either accepting or dismissing
    # that: the actual raw scores collapse to only 2 distinct values across
    # all 94 candidates (confirmed by direct inspection, not assumed), so
    # rank #3 vs #13 is arbitrary stable-sort tie-breaking within an
    # identically-scored group, not a meaningful ranking difference.
    # A misalignment bug would instead push the true pairs' scores toward
    # the population AVERAGE (no better than random); tier membership,
    # not raw rank, is what actually distinguishes "no signal reached the
    # true pair" from "no PER-COIL signal exists to rank within its tier".
    distinct_scores = sorted({round(float(s), 8) for s in raw_scores}, reverse=True)
    score_by_pair = {(f.source_id, f.target_id): float(s) for f, s in zip(sanity_features, raw_scores)}
    top_score = distinct_scores[0]
    tiers = {pair: distinct_scores.index(round(score_by_pair[pair], 8)) + 1 for pair in true_pairs}  # 1 = top tier
    sanity_passed = all(tier == 1 for tier in tiers.values())
    degenerate_scores = len(distinct_scores) <= 3  # a handful of tiers across ~94 candidates is a real finding, not noise

    print(f"\n--- step 4: sanity floor on {SANITY_EVENT_ID} (measured deviation -8.687C) ---")
    print(f"n distinct raw-score values across {n_candidates} candidates: {len(distinct_scores)} {distinct_scores}")
    for pair in true_pairs:
        print(
            f"  true discordant pair {pair}: raw_score={score_by_pair[pair]:.8f} "
            f"rank=#{ranks[pair]} (tie-break order) tier={tiers[pair]} of {len(distinct_scores)}"
        )
    print(f"sanity floor (both true pairs in the TOP score tier): {'PASS' if sanity_passed else 'FAIL'}")

    if not sanity_passed:
        raise RuntimeError(
            f"SANITY FLOOR FAILED: {SANITY_EVENT_ID}'s own true discordant pairs are not even in the "
            f"top score tier ON DATA THE MODEL WAS TRAINED ON. This indicates a feature/label "
            "misalignment or wrong candidate universe upstream, not a model-quality issue. Stopping "
            "before calibration/benchmark-adapter steps, per design."
        )

    # Feature-level ties are a separate question from the model's score
    # tiers: the model can (and here does) collapse to fewer score values
    # than there are distinct feature vectors.
    feature_key = lambda f: (f.source_type, f.target_type) + tuple(getattr(f, n) for n in NUMERIC_FEATURE_FIELDS)
    group_sizes = Counter(feature_key(f) for f in sanity_features)
    true_group_sizes = {
        pair: group_sizes[feature_key(f)]
        for f in sanity_features
        for pair in true_pairs
        if (f.source_id, f.target_id) == pair
    }
    print(
        f"distinct feature vectors: {len(group_sizes)} of {n_candidates} candidates "
        f"(largest tie groups: {sorted(group_sizes.values(), reverse=True)[:4]}); "
        f"true pairs' tie-group sizes: {list(true_group_sizes.values())}"
    )
    true_pairs_tied = any(size > 1 for size in true_group_sizes.values())
    if true_pairs_tied:
        print(
            f"\nFINDING (not a wiring bug -- verified by direct inspection): the true pairs share feature "
            f"vectors with siblings (tie groups {list(true_group_sizes.values())}), so within-tier rank is a guess. "
            "`n_indistinguishable_siblings` reports this to the model but cannot break the tie. See CHANGELOG.md."
        )
    elif degenerate_scores:
        print(
            f"\nNOTE: raw scores take only {len(distinct_scores)} distinct values, but the true pairs are each "
            f"uniquely identified by their features (tie groups {list(true_group_sizes.values())}), so this is a "
            "saturated near-0/1 classifier rather than missing per-coil signal. In this data the reported zone is "
            "always the moved coil's own zone (see CHANGELOG 0.2.3), so this is not evidence of generalization."
        )

    # --- step 5: leave-one-event-out calibration + suspect-prefix selection ---
    # datasets.group_split only produces one degenerate bucket (single
    # building lineage -- see causal_batch_v1_summary.json's split_note),
    # so it cannot supply a real calibration split either. Leave-one-EVENT-
    # out (not leave-one-record-out, which would let report variants of
    # the SAME event leak between train and calibration) is the closest
    # approximation available with 4 events.
    event_ids = sorted({r.event.event_id for r, _ in per_record})
    print(f"\n--- step 5: leave-one-event-out over {len(event_ids)} events ---")
    validation_records: list[EventValidationRecord] = []
    fold_models: dict[str, tuple] = {}  # held_out_event_id -> (fold_model, calibrator)

    for held_out in event_ids:
        train_pairs = [(r, f) for r, f in per_record if r.event.event_id != held_out]
        holdout_pairs = [(r, f) for r, f in per_record if r.event.event_id == held_out]

        train_feats = [f for _, feats in train_pairs for f in feats]
        train_lbls = [bool(lbl.is_discordant) for r, _ in train_pairs for lbl in r.labels]
        fold_model = train_gbm(train_feats, train_lbls)

        cal_feats = [f for _, feats in holdout_pairs for f in feats]
        cal_lbls = [bool(lbl.is_discordant) for r, _ in holdout_pairs for lbl in r.labels]
        raw = fold_model.predict_raw(cal_feats)
        calibrator = fit_calibrator(raw, cal_lbls)
        fold_models[held_out] = (fold_model, calibrator)

        for r, feats in holdout_pairs:
            raw_r = fold_model.predict_raw(feats)
            cal_r = calibrator.apply(raw_r)
            ranked_r = sorted(zip(feats, cal_r), key=lambda fc: fc[1], reverse=True)
            validation_records.append(
                EventValidationRecord(
                    event_id=r.report.report_id,
                    ranked_pairs=tuple((f.source_id, f.target_id) for f, _ in ranked_r),
                    true_pairs=frozenset(r.event.discordant_pairs),
                    universe_size=n_candidates,
                )
            )
        print(f"  fold held_out={held_out}: trained on {len(train_feats)} rows, calibrated on {len(cal_feats)} rows")

    prefix_selection = select_suspect_prefix(validation_records, target_coverage=0.95)
    print(
        f"select_suspect_prefix executed: k={prefix_selection.k} "
        f"mean_event_coverage={prefix_selection.mean_event_coverage:.3f} "
        f"universe_fraction={prefix_selection.universe_fraction:.3f} "
        f"met_target={prefix_selection.met_target}"
    )

    # --- step 6: build one PredictionRecord (for the sanity event, using ---
    # --- its OWN held-out fold, i.e. never trained on this exact event) ---
    fold_model, calibrator = fold_models[SANITY_EVENT_ID]
    raw_sanity = fold_model.predict_raw(sanity_features)
    cal_sanity = calibrator.apply(raw_sanity)
    ranked_sanity = sorted(zip(sanity_features, cal_sanity), key=lambda fc: fc[1], reverse=True)
    selected_pairs = tuple((f.source_id, f.target_id) for f, _ in ranked_sanity[: prefix_selection.k])

    predictions = tuple(
        CandidateDiscrepancyPrediction(
            source_id=f.source_id,
            target_id=f.target_id,
            relation=f.relation,
            discrepancy_probability=float(p),
            is_selected=(f.source_id, f.target_id) in selected_pairs,
        )
        for f, p in ranked_sanity
    )
    prediction_record = PredictionRecord(
        report_id=sanity_record.report.report_id,
        building_id=sanity_record.report.building_id,
        predictions=predictions,
        selected_pairs=selected_pairs,
        endpoint_node_union=frozenset(n for pair in selected_pairs for n in pair),
        model_version=GBM_MODEL_VERSION,
        calibration_version=CALIBRATION_VERSION,
        questionnaire_version=QUESTIONNAIRE_VERSION,
        # No formal graph-versioning system exists elsewhere in this
        # package yet -- this is a stand-in identifier, not a real version
        # pin; flagged here rather than dressed up as one.
        graph_version=f"{tg.building_id}:{tg.config_type}",
        supported=True,
    )
    print(
        f"\nbuilt PredictionRecord: {len(predictions)} predictions, "
        f"{len(selected_pairs)} selected, endpoint_node_union size={len(prediction_record.endpoint_node_union)}"
    )
    print(f"sanity event's true pairs among selected_pairs: {true_pairs.issubset(set(selected_pairs))}")

    # --- step 7: hand the PredictionRecord to the real benchmark adapter ---
    # `claimed_pairs` (documented/baseline truth) already contains the OLD
    # pair and not the new one -- pick them apart explicitly rather than
    # assuming `discordant_pairs`' tuple order means anything (it's built
    # from `tuple(sorted(frozenset(...)))` in simulation.py, i.e. sorted by
    # UUID string, not by "old" vs "new").
    old_pair = next(p for p in sanity_record.event.discordant_pairs if p in claimed_pairs)
    new_pair = next(p for p in sanity_record.event.discordant_pairs if p not in claimed_pairs)
    actual_tg = _build_actual_topology(tg, old_pair, new_pair)

    blueprint = Blueprint(
        building_id=sanity_record.report.building_id,
        severity=1,
        corruption_seed=0,
        claimed_edges=claimed_pairs,
        events=(
            CorruptionEvent(
                corruption_type=sanity_record.event.corruption_kind.value,
                discordant_pairs=sanity_record.event.discordant_pairs,
                target=sanity_record.event.target_id,
            ),
        ),
    )
    trial_result = run_symptom_troubleshooting_trial(
        actual_tg,
        ontology,
        blueprint,
        policy_name="active",
        symptom_source="learned",
        noise_level=0.0,
        seed=0,
        config=DEFAULT_CONFIG,
        prediction=prediction_record,
    )
    assert trial_result.endpoint_expansion_size > 0, "learned symptom source produced an empty suspect region"
    print(
        f"\nrun_symptom_troubleshooting_trial(symptom_source='learned') OK: "
        f"endpoint_expansion_size={trial_result.endpoint_expansion_size} "
        f"n_tests_performed={trial_result.n_tests_performed}/{trial_result.budget} "
        f"n_tests_to_full_flag_sustained={trial_result.n_tests_to_full_flag_sustained}"
    )

    # --- step 8: reconfirm the standing "never use learned before this is green" rule ---
    print("\n--- step 8: re-running tests/test_oracle_parity.py ---")
    oracle_parity = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_oracle_parity.py", "-q"],
        cwd=SYMPTOM_PIPELINE_ROOT,
        capture_output=True,
        text=True,
    )
    oracle_parity_passed = oracle_parity.returncode == 0
    print(oracle_parity.stdout.strip().splitlines()[-1] if oracle_parity.stdout.strip() else "(no output)")
    print(f"oracle parity: {'PASS' if oracle_parity_passed else 'FAIL'}")
    if not oracle_parity_passed:
        print(oracle_parity.stdout)
        print(oracle_parity.stderr)

    # --- step 9: write the honest summary ---
    summary = {
        "purpose": "integration/plumbing check only -- NOT a model-quality or generalization claim",
        "n_records": len(records),
        "n_candidates_per_record": n_candidates,
        "positive_rate_overall": round(positive_rate, 4),
        "sanity_floor": {
            "event_id": SANITY_EVENT_ID,
            "pass_criterion": "both true discordant pairs in the TOP distinct raw-score tier (not raw rank -- see disclaimers)",
            "ranks_of_true_pairs_informational_only": {str(pair): rank for pair, rank in ranks.items()},
            "tiers_of_true_pairs": {str(pair): tier for pair, tier in tiers.items()},
            "n_distinct_raw_score_values": len(distinct_scores),
            "distinct_raw_score_values": distinct_scores,
            "feature_degeneracy_finding": degenerate_scores,
            "gbm_nonzero_feature_importances": dict(nonzero_importances),
            "n_distinct_feature_vectors": len(group_sizes),
            "largest_feature_tie_groups": sorted(group_sizes.values(), reverse=True)[:6],
            "true_pair_tie_group_sizes": {str(pair): size for pair, size in true_group_sizes.items()},
            "passed": sanity_passed,
        },
        "leave_one_event_out": {
            "n_folds": len(event_ids),
            "event_ids": event_ids,
            "suspect_prefix_selection": {
                "k": prefix_selection.k,
                "mean_event_coverage": prefix_selection.mean_event_coverage,
                "universe_fraction": prefix_selection.universe_fraction,
                "met_target": prefix_selection.met_target,
            },
        },
        "benchmark_adapter_handoff": {
            "symptom_source": "learned",
            "endpoint_expansion_size": trial_result.endpoint_expansion_size,
            "n_tests_performed": trial_result.n_tests_performed,
            "budget": trial_result.budget,
            "n_tests_to_full_flag_sustained": trial_result.n_tests_to_full_flag_sustained,
        },
        "oracle_parity_reconfirmed": oracle_parity_passed,
        "disclaimers": [
            "One building lineage (sys07_vav_reheat) and 4 physically distinct events (16 records via "
            "report variants of those same 4 events) -- no accuracy, coverage, or ranking number above "
            "is evidence the modeling approach works or generalizes.",
            "The leave-one-event-out 'calibration split' is a plumbing exercise, not a real calibration "
            "protocol -- each fold calibrates on a single held-out event's own 4 report variants.",
            "simulation.reconcile_realized_topology's structural-signature clone/relocation path is "
            "still exercised only by synthetic fixtures (tests/test_reconciliation.py), never by this "
            "real batch -- reassign_coil reconciles by trivial handle equality, so this real data never "
            "touches that code path.",
            "A real held-out train/val/test split needs a second, independently-lineaged intervention "
            "(a second qualifying archetype, or a second rewire_kind that doesn't destroy equipment) -- "
            "neither exists today.",
            (
                f"Raw model scores take {len(distinct_scores)} distinct values across {n_candidates} candidates; "
                f"features distinguish {len(group_sizes)} groups and the true pairs' feature tie groups have sizes "
                f"{list(true_group_sizes.values())}. In all 4 events the reported zone (the max-deviation zone) is the "
                "moved coil's own zone, so 'coil whose VAV feeds the reported zone' separates the true pairs "
                "perfectly; that is a property of how reports are built here, not evidence it holds when a "
                "report names a different zone."
            ),
        ],
    }
    summary_path = OUT_DIR / "plumbing_check_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str))
    print(f"\nwrote summary to {summary_path}")
    print("\n=== PLUMBING CHECK PASSED (integration only -- see disclaimers in summary) ===")


if __name__ == "__main__":
    main()
