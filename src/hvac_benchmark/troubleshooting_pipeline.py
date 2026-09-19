"""Orchestration for the troubleshooting-against-a-blueprint evaluation
mode. Kept separate from `pipeline.py` so the existing discovery-mode
orchestration (`run_main_grid`, `run_ablations`) is never modified by this
addition; `pipeline.run_pipeline` calls into this module additively.
"""

from __future__ import annotations

import json
from pathlib import Path

from .config import BenchmarkConfig
from .data.ontology import BrickOntology
from .experiment.blueprint import Blueprint, generate_blueprint
from .experiment.troubleshooting_runner import (
    TROUBLESHOOTING_BLIND_POLICIES,
    TROUBLESHOOTING_SYMPTOM_POLICIES,
    TroubleshootingTrialResult,
    run_troubleshooting_trial,
)
from .parallel import ExecOptions, Unit, run_units
from .pipeline import Bundle, RelationAvailability


def _troubleshooting_unit(ontology: BrickOntology, tg, config: BenchmarkConfig):
    """All troubleshooting trials for one topology: returns (results, blueprints)."""
    results: list[TroubleshootingTrialResult] = []
    blueprints: list[Blueprint] = []
    for severity in config.troubleshooting_severities:
        for variant in range(config.troubleshooting_n_variants):
            corruption_seed = config.troubleshooting_base_seed + severity * 1000 + variant
            blueprint = generate_blueprint(tg, ontology, severity, corruption_seed)
            if len(blueprint.events) == 0:
                # Topology too small/under-connected to safely construct
                # even one corruption at this severity (e.g. no
                # alternate plausible parent for a misattribution);
                # skip rather than run a trial with zero corruption
                # sites, which would make the primary metric vacuous.
                continue
            blueprints.append(blueprint)

            for symptom_mode, policy_set in (
                (False, TROUBLESHOOTING_BLIND_POLICIES),
                (True, TROUBLESHOOTING_SYMPTOM_POLICIES),
            ):
                for policy in policy_set:
                    for noise in config.noise_levels:
                        for seed in range(
                            config.base_seed, config.base_seed + config.troubleshooting_n_seeds_per_variant
                        ):
                            results.append(
                                run_troubleshooting_trial(
                                    tg, ontology, blueprint, policy, symptom_mode, noise, seed, config
                                )
                            )
    return results, blueprints


def run_troubleshooting_grid(
    bundles: list[Bundle],
    ontology: BrickOntology,
    config: BenchmarkConfig,
    availabilities: dict[tuple[str, str], RelationAvailability],
    exec_opts: ExecOptions | None = None,
) -> tuple[list[TroubleshootingTrialResult], dict[str, list[Blueprint]]]:
    """Runs blind and symptom-triggered troubleshooting trials for every
    real `feeds`-eligible topology already used by the primary discovery
    benchmark. One set of corrupted-blueprint variants per
    (topology, severity) is generated once and reused across every policy
    and noise level -- the same paired-comparison principle the discovery
    grid uses (same seeds/same corruption across policies), so policies are
    compared against the identical corruption, never independently
    resampled ones. One unit per topology, so units can run in parallel and
    be checkpointed without changing any result.
    """
    real_feeds_bundles = [
        b
        for b in bundles
        if b.category == "real"
        and availabilities.get((b.tg.building_id, "feeds")) is not None
        and availabilities[(b.tg.building_id, "feeds")].available
    ]
    units = [
        Unit(
            f"troubleshooting__{b.tg.building_id}",
            _troubleshooting_unit,
            (b.tg, config),
            float(availabilities[(b.tg.building_id, "feeds")].n_candidates) ** 2,
        )
        for b in real_feeds_bundles
    ]
    unit_outputs = run_units(units, ontology, config, exec_opts, "troubleshooting grid")

    results: list[TroubleshootingTrialResult] = []
    blueprints_by_building: dict[str, list[Blueprint]] = {}
    for b, (unit_results, blueprints) in zip(real_feeds_bundles, unit_outputs):
        results.extend(unit_results)
        blueprints_by_building[b.tg.building_id] = blueprints
    return results, blueprints_by_building


def _trial_to_dict(r: TroubleshootingTrialResult) -> dict:
    from dataclasses import asdict

    return asdict(r)


def save_troubleshooting_trajectories(results: list[TroubleshootingTrialResult], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    groups: dict[str, list[TroubleshootingTrialResult]] = {}
    for r in results:
        key = f"{r.building_id}__severity{r.requested_severity}__{'symptom' if r.symptom_mode else 'blind'}"
        groups.setdefault(key, []).append(r)
    for key, group in groups.items():
        path = out_dir / f"{key}.json"
        with open(path, "w") as f:
            json.dump([_trial_to_dict(r) for r in group], f)
