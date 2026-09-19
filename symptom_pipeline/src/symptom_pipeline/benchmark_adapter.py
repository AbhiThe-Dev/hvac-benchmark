"""Sibling troubleshooting runner.

Reproduces `hvac_benchmark.experiment.troubleshooting_runner
.run_troubleshooting_trial` step for step, but takes an external symptom
source instead of that runner's internal `symptom_flagged_nodes()` call --
the one hook the design doc's finding 4 confirms does not exist in
`hvac_benchmark`. This module exists *because* that hook is missing;
monkey-patching `troubleshooting_runner` was rejected in favor of a
narrowly-scoped, side-by-side reimplementation that imports every
inference/policy component unchanged (`hvac_benchmark.experiment.bayes`,
`.candidates`, `.noise`, `.policies`, `.policy_view`, `.priors`,
`.troubleshooting_policies`) and duplicates only the orchestration loop
itself.

Required acceptance check (`tests/test_oracle_parity.py`): for every
(policy, noise, seed) combination on the fixed fixture graph,
`symptom_source="none"` must match `run_troubleshooting_trial(...,
symptom_mode=False)` bit-for-bit, and `symptom_source="oracle"` must match
`run_troubleshooting_trial(..., symptom_mode=True)` bit-for-bit. Only
`symptom_source="learned"` introduces new behavior (a model-predicted
endpoint-node union in place of `symptom_flagged_nodes()`'s output). This
adapter must never be used for `learned`-source experiments before that
parity check passes.
"""

from __future__ import annotations

from dataclasses import dataclass

from hvac_benchmark.config import BenchmarkConfig
from hvac_benchmark.data.ontology import BrickOntology
from hvac_benchmark.experiment.bayes import expected_information_gain as indep_eig
from hvac_benchmark.experiment.bayes import update as bayes_update
from hvac_benchmark.experiment.blueprint import Blueprint, symptom_flagged_nodes
from hvac_benchmark.experiment.candidates import generate_feeds_candidates
from hvac_benchmark.experiment.noise import noise_draw, observe
from hvac_benchmark.experiment.policies import ActivePolicy, make_tiebreak
from hvac_benchmark.experiment.policy_view import build_policy_view
from hvac_benchmark.experiment.priors import apply_symptom_relaxation, blueprint_priors
from hvac_benchmark.experiment.troubleshooting_policies import (
    BlueprintLiteralPolicy,
    FullSweepPolicy,
    SymptomNaivePolicy,
)
from hvac_benchmark.graph.networkx_build import TopologyGraph

from .contracts import PredictionRecord

SYMPTOM_SOURCES: tuple[str, ...] = ("none", "oracle", "learned")


@dataclass(frozen=True)
class SymptomTroubleshootingTrajectoryPoint:
    test_number: int
    n_discordant_flagged: int
    n_false_positive_flags: int
    n_needless_retests: int


@dataclass
class SymptomTroubleshootingTrialResult:
    building_id: str
    corruption_seed: int
    requested_severity: int
    actual_severity: int
    corruption_types: tuple[str, ...]
    symptom_source: str
    policy: str
    noise_level: float
    seed: int
    n_candidates: int
    n_discordant_candidates: int
    budget: int
    n_tests_performed: int
    n_tests_to_full_flag_first: int | None
    n_tests_to_full_flag_sustained: int | None
    trajectory: list[SymptomTroubleshootingTrajectoryPoint]
    # Not present on hvac_benchmark's TroubleshootingTrialResult: how many
    # endpoint nodes the symptom source expanded the suspect region to.
    # Design doc: "Measure that expansion explicitly; it can dilute a good
    # edge ranking."
    endpoint_expansion_size: int


def _select_policy(name: str):
    return {
        "active": ActivePolicy(),
        "blueprint_literal": BlueprintLiteralPolicy(),
        "full_sweep": FullSweepPolicy(),
        "symptom_naive": SymptomNaivePolicy(),
    }[name]


def flagged_nodes_for_source(
    symptom_source: str,
    tg: TopologyGraph,
    blueprint: Blueprint,
    prediction: PredictionRecord | None,
) -> frozenset[str]:
    """The one substitution point this adapter exists for. `"none"` and
    `"oracle"` reproduce `troubleshooting_runner`'s two existing modes
    exactly; `"learned"` is new: the frozen endpoint-node union of a single
    upstream model prediction (design doc, "Bayesian handoff", steps 1-2),
    never a per-test model call.
    """
    if symptom_source == "none":
        return frozenset()
    if symptom_source == "oracle":
        return symptom_flagged_nodes(tg, blueprint)
    if symptom_source == "learned":
        if prediction is None:
            raise ValueError("symptom_source='learned' requires a PredictionRecord")
        return frozenset(prediction.endpoint_node_union)
    raise ValueError(f"unknown symptom_source {symptom_source!r}")


def run_symptom_troubleshooting_trial(
    tg: TopologyGraph,
    ontology: BrickOntology,
    blueprint: Blueprint,
    policy_name: str,
    symptom_source: str,
    noise_level: float,
    seed: int,
    config: BenchmarkConfig,
    prediction: PredictionRecord | None = None,
) -> SymptomTroubleshootingTrialResult:
    if symptom_source not in SYMPTOM_SOURCES:
        raise ValueError(f"unknown symptom_source {symptom_source!r}")

    candidates = generate_feeds_candidates(tg, ontology)
    view = build_policy_view(tg, candidates, seed=seed)
    n = len(view.candidates)

    real_pairs: list[tuple[str, str]] = [None] * n  # type: ignore[list-item]
    for i, oc in enumerate(view.candidates):
        real_pairs[i] = (view.opaque_to_real[oc.source], view.opaque_to_real[oc.target])

    priors_by_pair = blueprint_priors(
        candidates,
        blueprint.claimed_edges,
        blueprint_confidence=config.blueprint_confidence,
        absent_prior=config.blueprint_absent_prior,
    )

    # Matches troubleshooting_runner.py exactly: relaxation is applied iff
    # a symptom mechanism is active at all (there, `symptom_mode`; here,
    # any source other than "none"). "none" never calls
    # apply_symptom_relaxation, matching `symptom_mode=False`.
    apply_relaxation = symptom_source != "none"
    flagged_real_nodes = flagged_nodes_for_source(symptom_source, tg, blueprint, prediction)
    flagged_opaque_nodes = frozenset(
        view.real_to_opaque[node] for node in flagged_real_nodes if node in view.real_to_opaque
    )
    if apply_relaxation:
        priors_by_pair = apply_symptom_relaxation(
            priors_by_pair, flagged_real_nodes, relax=config.symptom_prior_relax
        )

    true_edges = tg.edges_by_relation["feeds"]
    discordant_pairs = blueprint.discordant_pairs

    posterior = [priors_by_pair[pair] for pair in real_pairs]
    is_blueprint_true = [pair in blueprint.claimed_edges for pair in real_pairs]
    is_discordant = [pair in discordant_pairs for pair in real_pairs]
    is_true = [pair in true_edges for pair in real_pairs]

    def eig_of(i: int) -> float:
        return indep_eig(posterior[i], fp_rate=noise_level, fn_rate=noise_level)

    def current_flag(i: int) -> bool:
        if is_blueprint_true[i]:
            return posterior[i] <= config.reconstruction_threshold
        return posterior[i] > config.reconstruction_threshold

    max_repeats = config.max_repeats_noiseless if noise_level == 0.0 else config.max_repeats_noisy
    budget = n * max_repeats
    repeats_done = [0] * n
    retired = [False] * n

    def is_retired(i: int) -> bool:
        p = posterior[i]
        return p >= config.retirement_confidence or p <= (1 - config.retirement_confidence)

    tiebreak = make_tiebreak(n, seed)
    policy = _select_policy(policy_name)

    if policy_name == "blueprint_literal":
        fixed_order: list[int] | None = []
    elif policy_name == "full_sweep":
        claimed_indices = {i for i in range(n) if is_blueprint_true[i]}
        fixed_order = policy.initial_ranking(view, ontology, tiebreak, blueprint_claimed_indices=claimed_indices)
    elif policy_name == "symptom_naive":
        assert symptom_source != "none", "symptom_naive is only defined with an active symptom source"
        fixed_order = policy.initial_ranking(view, ontology, tiebreak, flagged_opaque_nodes=flagged_opaque_nodes)
    elif policy_name == "active":
        fixed_order = None
    else:
        raise ValueError(f"unknown troubleshooting policy {policy_name!r}")

    trajectory: list[SymptomTroubleshootingTrajectoryPoint] = []
    ever_false_positive: set[int] = set()
    needless_count = 0

    def snapshot(test_number: int) -> None:
        n_flagged = sum(1 for i in range(n) if is_discordant[i] and current_flag(i))
        for i in range(n):
            if (not is_discordant[i]) and is_blueprint_true[i] and current_flag(i):
                ever_false_positive.add(i)
        trajectory.append(
            SymptomTroubleshootingTrajectoryPoint(
                test_number=test_number,
                n_discordant_flagged=n_flagged,
                n_false_positive_flags=len(ever_false_positive),
                n_needless_retests=needless_count,
            )
        )

    snapshot(0)

    n_tests_performed = 0

    def do_test(idx: int) -> None:
        nonlocal n_tests_performed, needless_count
        if (not is_discordant[idx]) and is_blueprint_true[idx]:
            needless_count += 1
        draw = noise_draw(tg.building_id, *real_pairs[idx], repeats_done[idx], seed)
        obs = observe(is_true[idx], noise_level, noise_level, draw)
        posterior[idx] = bayes_update(posterior[idx], obs, noise_level, noise_level)
        repeats_done[idx] += 1
        n_tests_performed += 1
        if is_retired(idx):
            retired[idx] = True

    if fixed_order is not None:
        cursor = 0
        cycle_guard = 0
        guard_len = max(len(fixed_order), 1)
        while fixed_order and n_tests_performed < budget and cycle_guard < budget * 2 + guard_len + 1:
            cycle_guard += 1
            idx = fixed_order[cursor % len(fixed_order)]
            cursor += 1
            if retired[idx] or repeats_done[idx] >= max_repeats:
                if all(retired[i] or repeats_done[i] >= max_repeats for i in fixed_order):
                    break
                continue
            do_test(idx)
            snapshot(n_tests_performed)
    else:
        while n_tests_performed < budget:
            unresolved = [i for i in range(n) if not retired[i] and repeats_done[i] < max_repeats]
            if not unresolved:
                break
            idx = policy.next_index(unresolved, eig_of, tiebreak)
            do_test(idx)
            snapshot(n_tests_performed)

    n_discordant_candidates = sum(is_discordant)

    first = None
    for pt in trajectory:
        if n_discordant_candidates > 0 and pt.n_discordant_flagged == n_discordant_candidates:
            first = pt.test_number
            break
    sustained = None
    if trajectory and n_discordant_candidates > 0 and trajectory[-1].n_discordant_flagged == n_discordant_candidates:
        sustained = trajectory[-1].test_number
        for pt in reversed(trajectory[:-1]):
            if pt.n_discordant_flagged == n_discordant_candidates:
                sustained = pt.test_number
            else:
                break

    return SymptomTroubleshootingTrialResult(
        building_id=tg.building_id,
        corruption_seed=blueprint.corruption_seed,
        requested_severity=blueprint.severity,
        actual_severity=len(blueprint.events),
        corruption_types=tuple(e.corruption_type for e in blueprint.events),
        symptom_source=symptom_source,
        policy=policy_name,
        noise_level=noise_level,
        seed=seed,
        n_candidates=n,
        n_discordant_candidates=n_discordant_candidates,
        budget=budget,
        n_tests_performed=n_tests_performed,
        n_tests_to_full_flag_first=first,
        n_tests_to_full_flag_sustained=sustained,
        trajectory=trajectory,
        endpoint_expansion_size=len(flagged_opaque_nodes),
    )
