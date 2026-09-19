"""End-to-end orchestration: acquire data, build topologies, run every
experiment, and write everything under `results/`.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from .config import POLICIES, BenchmarkConfig
from .data.brick_examples import fetch_brick_examples
from .data.cache import FileCache
from .data.fetch import fetch_all_brick_models
from .data.mortar import fetch_all_mortar_graphs
from .data.ontology import BrickOntology
from .experiment.candidates import candidate_coverage, generate_candidates
from .experiment.runner import TrialResult, run_trial
from .graph.building_grouping import MORTAR_CORPUS_GROUPS, REAL_CORPUS_GROUPS, merge_all
from .graph.inventory import TopologyInventory, flag_duplicates, inventory_topology
from .graph.networkx_build import TopologyGraph, build_topology_graph
from .graph.synthetic import make_all_synthetic_graphs

logger = logging.getLogger(__name__)

RELATIONS = ("feeds", "hasPoint", "hasPart")

# Ablations are run on a representative subset of topologies to bound total
# runtime; documented explicitly in results.md rather than silently scoped.
ABLATION_TOPOLOGIES = ("rtu_exp", "sdahu")


@dataclass
class Bundle:
    tg: TopologyGraph
    category: str  # "real" | "synthetic"


@dataclass
class RelationAvailability:
    relation: str
    available: bool
    reason: str
    n_true_edges: int
    n_candidates: int
    n_missed: int


def compute_availability(
    tg: TopologyGraph, relation: str, ontology: BrickOntology, max_universe: int | None = None
) -> RelationAvailability:
    true_edges = tg.edges_by_relation[relation]
    if not true_edges:
        return RelationAvailability(relation, False, "no asserted edges for this relation", 0, 0, 0)
    candidates = generate_candidates(tg, relation, ontology)
    coverage = candidate_coverage(candidates, true_edges)
    if max_universe is not None and len(candidates) > max_universe:
        return RelationAvailability(
            relation,
            False,
            f"candidate universe ({len(candidates)}) exceeds feasibility cap ({max_universe}); "
            "trial cost is O(n^2) in universe size",
            len(true_edges),
            len(candidates),
            coverage.n_missed,
        )
    if coverage.n_covered == 0:
        return RelationAvailability(
            relation,
            False,
            "zero candidate coverage (entities likely missing rdf:type metadata needed for subclass-based "
            "candidate generation)",
            len(true_edges),
            len(candidates),
            coverage.n_missed,
        )
    return RelationAvailability(relation, True, "ok", len(true_edges), len(candidates), coverage.n_missed)


def load_topologies(
    cache: FileCache,
    ontology: BrickOntology,
    skip_download: bool = False,
    max_universe: int | None = None,
) -> tuple[
    list[Bundle], dict, dict
]:
    """Returns (bundles, provenance_report). provenance_report includes the
    file-to-building mapping, exclusions, and whether the Brick-example
    fallback was used."""
    fallback_used = False
    fallback_reason = None
    files_by_logical_name: dict[str, bytes] = {}

    if skip_download:
        for fn in os.listdir(cache.cache_dir):
            if fn.endswith(".ttl") and not fn.startswith("brick_ontology"):
                files_by_logical_name[fn] = cache.get_bytes(fn)
    else:
        try:
            models = fetch_all_brick_models(cache)
            for m in models:
                files_by_logical_name[m.logical_name] = m.data
        except Exception as exc:  # noqa: BLE001 - documented contingency path
            logger.warning("primary Figshare source unreachable (%s); falling back to Brick examples", exc)
            fallback_used = True
            fallback_reason = str(exc)

        try:
            mortar_models = fetch_all_mortar_graphs(cache)
            for m in mortar_models:
                files_by_logical_name[m.logical_name] = m.data
        except Exception as exc:  # noqa: BLE001 - MORTAR is a supplementary source; its
            # unavailability should not take down the LBNL-based run, but must not be
            # silently absorbed either.
            logger.warning("MORTAR source (Hugging Face) unreachable (%s); MORTAR buildings skipped", exc)

    all_real_groups = REAL_CORPUS_GROUPS + MORTAR_CORPUS_GROUPS
    merged, excluded_groups = merge_all(all_real_groups, files_by_logical_name, ontology)

    # A group can merge cleanly (every member file present, no grouping
    # ambiguity) and still be unusable: some anonymized MORTAR graphs may be
    # too sparse or structurally malformed to support any experiment. A
    # topology is usable if at least one of feeds/hasPoint/hasPart has both
    # real asserted edges and non-empty candidate coverage for them (the same
    # bar `compute_availability` already applies per relation downstream);
    # a topology meeting that bar for zero relations is excluded here,
    # explicitly, rather than silently carried into bundles as an
    # all-relations-unavailable no-op.
    usable_merged = []
    unusable_topologies = []
    for m in merged:
        tg = build_topology_graph(m.building_id, m.config_type, m.graph)
        relation_detail = {}
        any_usable = False
        for relation in RELATIONS:
            avail = compute_availability(tg, relation, ontology, max_universe)
            relation_detail[relation] = {
                "available": avail.available,
                "reason": avail.reason,
                "n_true_edges": avail.n_true_edges,
                "n_candidates": avail.n_candidates,
            }
            any_usable = any_usable or avail.available
        if any_usable:
            usable_merged.append(m)
        else:
            unusable_topologies.append(
                {
                    "building_id": m.building_id,
                    "members": list(m.member_logical_names),
                    "reason": "no relation (feeds/hasPoint/hasPart) has both true edges and "
                    "non-empty candidate coverage",
                    "relation_detail": relation_detail,
                }
            )
            logger.warning("excluding %s: no usable relation (%s)", m.building_id, relation_detail)
    merged = usable_merged

    bundles = [Bundle(tg=build_topology_graph(m.building_id, m.config_type, m.graph), category="real") for m in merged]
    parse_reports_by_building = {m.building_id: m.parse_reports for m in merged}
    usable_building_ids = {m.building_id for m in merged}

    if fallback_used:
        examples = fetch_brick_examples(cache, reason=fallback_reason or "primary source unreachable")
        # Fallback models are informational only; not wired into the real
        # corpus grouping since we have no verified building mapping for them.
        for logical_name, data, prov in examples:
            logger.info("fetched fallback example %s (%s)", logical_name, prov.source_revision)

    synthetic = [Bundle(tg=g, category="synthetic") for g in make_all_synthetic_graphs()]

    file_to_building = {
        g.building_id: {
            "member_files": list(g.member_logical_names),
            "config_type": g.config_type,
            "evidence": g.evidence,
            "status": g.status,
        }
        for g in all_real_groups
        if g.building_id in usable_building_ids
    }
    exclusions = [
        {"building_id": g.building_id, "status": g.status, "members": list(g.member_logical_names)}
        for g in excluded_groups
    ]

    provenance_report = {
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "file_to_building": file_to_building,
        "excluded_groups": exclusions,
        "unusable_topologies": unusable_topologies,
        "provenance_records": [asdict(p) for p in cache.all_provenance()],
    }

    return bundles + synthetic, provenance_report, parse_reports_by_building


def build_inventories(
    bundles: list[Bundle], merged_reports: dict[str, dict]
) -> list[TopologyInventory]:
    inventories = []
    for b in bundles:
        reports = merged_reports.get(b.tg.building_id, {})
        inventories.append(inventory_topology(b.tg, reports))
    return flag_duplicates(inventories)


def run_main_grid(
    bundles: list[Bundle],
    ontology: BrickOntology,
    config: BenchmarkConfig,
    availabilities: dict[tuple[str, str], RelationAvailability],
) -> list[TrialResult]:
    results: list[TrialResult] = []
    seeds = range(config.base_seed, config.base_seed + config.n_seeds)

    for b in bundles:
        tg = b.tg
        for relation in RELATIONS:
            avail = availabilities[(tg.building_id, relation)]
            if not avail.available:
                continue
            experiments = ["independent", "structured"] if relation == "feeds" else ["independent"]
            logger.info(
                "main grid: %s / %s (n_candidates=%d, %d trials so far)",
                tg.building_id, relation, avail.n_candidates, len(results),
            )
            for experiment in experiments:
                for policy in POLICIES:
                    for noise in config.noise_levels:
                        for seed in seeds:
                            results.append(
                                run_trial(
                                    tg,
                                    relation,
                                    ontology,
                                    experiment,
                                    policy,
                                    noise,
                                    seed,
                                    config,
                                    prior_kind="sparse",
                                    lam=config.default_lambda if experiment == "structured" else None,
                                )
                            )
    return results


def run_ablations(
    bundles: list[Bundle],
    ontology: BrickOntology,
    config: BenchmarkConfig,
    availabilities: dict[tuple[str, str], RelationAvailability],
) -> list[TrialResult]:
    """Uniform-prior ablation and lambda sensitivity, on a representative
    subset of feeds-eligible topologies (see ABLATION_TOPOLOGIES) to bound
    total runtime; both ablations use the active policy only, since they
    probe the inference/prior setup rather than policy comparison."""
    results: list[TrialResult] = []
    seeds = range(config.base_seed, config.base_seed + config.n_seeds)
    subset = [b for b in bundles if b.tg.building_id in ABLATION_TOPOLOGIES]

    for b in subset:
        tg = b.tg
        avail = availabilities.get((tg.building_id, "feeds"))
        if not avail or not avail.available:
            continue
        for noise in config.noise_levels:
            for seed in seeds:
                results.append(
                    run_trial(tg, "feeds", ontology, "independent", "active", noise, seed, config, prior_kind="uniform")
                )
        other_lams = [l for l in config.lambda_sensitivity if l != config.default_lambda]
        for lam in other_lams:
            for noise in config.noise_levels:
                for seed in seeds:
                    results.append(
                        run_trial(tg, "feeds", ontology, "structured", "active", noise, seed, config, lam=lam)
                    )
    return results


def trial_to_dict(r: TrialResult) -> dict:
    d = asdict(r)
    return d


def save_trajectories(results: list[TrialResult], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    groups: dict[str, list[TrialResult]] = {}
    for r in results:
        key = f"{r.building_id}__{r.relation}__{r.experiment}"
        groups.setdefault(key, []).append(r)
    for key, group in groups.items():
        path = out_dir / f"{key}.json"
        with open(path, "w") as f:
            json.dump([trial_to_dict(r) for r in group], f)


def run_pipeline(
    results_dir: str = "results",
    cache_dir: str = "data_cache",
    config: BenchmarkConfig | None = None,
    skip_download: bool = False,
    run_ablations_flag: bool = True,
    run_troubleshooting_flag: bool = True,
) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config = config or BenchmarkConfig()
    results_path = Path(results_dir)
    results_path.mkdir(parents=True, exist_ok=True)

    cache = FileCache(cache_dir)
    logger.info("loading Brick ontology")
    ontology = BrickOntology.load(cache)

    logger.info("acquiring Brick models")
    bundles, provenance_report, parse_reports_by_building = load_topologies(
        cache, ontology, skip_download=skip_download, max_universe=config.max_candidate_universe
    )
    logger.info("loaded %d topologies (%d real, %d synthetic)",
                len(bundles), sum(1 for b in bundles if b.category == "real"),
                sum(1 for b in bundles if b.category == "synthetic"))

    with open(results_path / "provenance.json", "w") as f:
        json.dump(provenance_report["provenance_records"], f, indent=2)
    with open(results_path / "file_to_building.json", "w") as f:
        json.dump(provenance_report["file_to_building"], f, indent=2)
    with open(results_path / "exclusions.json", "w") as f:
        json.dump(
            {"fallback_used": provenance_report["fallback_used"],
             "fallback_reason": provenance_report["fallback_reason"],
             "excluded_groups": provenance_report["excluded_groups"],
             "unusable_topologies": provenance_report["unusable_topologies"]},
            f, indent=2,
        )

    inventories = build_inventories(bundles, parse_reports_by_building)
    inv_by_id = {inv.building_id: inv for inv in inventories}

    logger.info("computing relation availability")
    availabilities: dict[tuple[str, str], RelationAvailability] = {}
    for b in bundles:
        dup_of = inv_by_id[b.tg.building_id].is_duplicate_of
        for relation in RELATIONS:
            if dup_of is not None:
                # A structural duplicate of an already-counted topology is
                # excluded from every relation's experiments, not just
                # feeds, so it is never run and never double-counted.
                availabilities[(b.tg.building_id, relation)] = RelationAvailability(
                    relation, False, f"structural duplicate of {dup_of} (excluded from all experiments)", 0, 0, 0
                )
            else:
                availabilities[(b.tg.building_id, relation)] = compute_availability(
                    b.tg, relation, ontology, config.max_candidate_universe
                )

    with open(results_path / "config.json", "w") as f:
        json.dump(asdict(config), f, indent=2)

    logger.info("running main grid")
    t0 = time.time()
    main_results = run_main_grid(bundles, ontology, config, availabilities)
    logger.info("main grid: %d trials in %.1fs", len(main_results), time.time() - t0)

    ablation_results: list[TrialResult] = []
    if run_ablations_flag:
        logger.info("running ablations")
        t0 = time.time()
        ablation_results = run_ablations(bundles, ontology, config, availabilities)
        logger.info("ablations: %d trials in %.1fs", len(ablation_results), time.time() - t0)

    save_trajectories(main_results, results_path / "trajectories")
    if ablation_results:
        save_trajectories(ablation_results, results_path / "trajectories_ablation")

    troubleshooting_results = []
    blueprints_by_building = {}
    if run_troubleshooting_flag:
        from .troubleshooting_pipeline import run_troubleshooting_grid, save_troubleshooting_trajectories

        logger.info("running troubleshooting-against-a-blueprint grid")
        t0 = time.time()
        troubleshooting_results, blueprints_by_building = run_troubleshooting_grid(
            bundles, ontology, config, availabilities
        )
        logger.info("troubleshooting grid: %d trials in %.1fs", len(troubleshooting_results), time.time() - t0)
        save_troubleshooting_trajectories(troubleshooting_results, results_path / "trajectories_troubleshooting")

    from .evaluate.report import generate_report

    generate_report(
        bundles=bundles,
        inventories=inventories,
        availabilities=availabilities,
        main_results=main_results,
        ablation_results=ablation_results,
        provenance_report=provenance_report,
        config=config,
        results_path=results_path,
        troubleshooting_results=troubleshooting_results,
        blueprints_by_building=blueprints_by_building,
    )
    logger.info("done. see %s/results.md", results_path)
