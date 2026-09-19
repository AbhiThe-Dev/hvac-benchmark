"""Run one (topology, relation, experiment, policy, noise, seed) trial to a
fixed test budget, recording precision/recall/F1/calibration/test-count from
step zero, without ever consulting ground truth to decide when to stop.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config import BenchmarkConfig
from ..data.ontology import BrickOntology
from ..graph.networkx_build import TopologyGraph
from .bayes import expected_information_gain as indep_eig
from .bayes import update as bayes_update
from .candidates import Candidate, candidate_coverage, generate_candidates
from .noise import noise_draw, observe
from .policies import FrozenInitialPolicy, SelectionPolicy, make_policy, make_tiebreak
from .policy_view import PolicyView, build_policy_view
from .priors import sparse_priors, uniform_priors
from .structured import StructuredBelief

STRUCTURABLE_TARGET_ANCESTORS = ("Terminal_Unit", "Location")


@dataclass(frozen=True)
class TrajectoryPoint:
    test_number: int
    precision: float
    recall: float
    f1: float
    brier: float


@dataclass
class TrialResult:
    building_id: str
    relation: str
    experiment: str
    policy: str
    prior_kind: str
    noise_level: float
    lam: float | None
    seed: int
    n_candidates: int
    n_missed_true_edges: int
    budget: int
    n_tests_performed: int
    trajectory: list[TrajectoryPoint]
    true_parent_count_violations: int = 0


def _target_is_structurable(view: PolicyView, target_opaque: str, ontology: BrickOntology) -> bool:
    t_type = view.nodes[target_opaque].brick_type
    if t_type is None:
        return False
    ancestors = ontology.ancestors(t_type)
    return any(a in ancestors for a in STRUCTURABLE_TARGET_ANCESTORS)


def run_trial(
    tg: TopologyGraph,
    relation: str,
    ontology: BrickOntology,
    experiment: str,  # "independent" | "structured"
    policy_name: str,
    noise_level: float,
    seed: int,
    config: BenchmarkConfig,
    prior_kind: str = "sparse",
    lam: float | None = None,
) -> TrialResult:
    candidates = generate_candidates(tg, relation, ontology)
    true_edges = tg.edges_by_relation[relation]
    coverage = candidate_coverage(candidates, true_edges)

    view = build_policy_view(tg, candidates, seed=seed)
    n = len(view.candidates)

    priors_by_pair = (
        sparse_priors(candidates) if prior_kind == "sparse" else uniform_priors(candidates)
    )
    # candidates list and view.candidates are index-aligned via policy_view's
    # cand_order permutation; recover the (source,target) pair each opaque
    # candidate refers to so we can look up its prior and ground-truth label.
    real_pairs = [None] * n
    for i, oc in enumerate(view.candidates):
        real_pairs[i] = (view.opaque_to_real[oc.source], view.opaque_to_real[oc.target])
    priors = [priors_by_pair[pair] for pair in real_pairs]
    true_labels = {i: (real_pairs[i] in true_edges) for i in range(n)}

    lam = config.default_lambda if lam is None else lam
    is_structured = experiment == "structured" and relation == "feeds"

    groups: dict[str, list[int]] = {}
    if is_structured:
        for i, oc in enumerate(view.candidates):
            if _target_is_structurable(view, oc.target, ontology):
                groups.setdefault(oc.target, []).append(i)
    grouped_indices = {i for members in groups.values() for i in members}
    group_of: dict[int, str] = {i: t for t, members in groups.items() for i in members}
    group_local_pos: dict[int, int] = {
        i: pos for members in groups.values() for pos, i in enumerate(members)
    }
    structured_beliefs: dict[str, StructuredBelief] = {
        t: StructuredBelief(tuple(priors[i] for i in members), lam=lam, enumeration_cap=config.structured_enumeration_cap)
        for t, members in groups.items()
    }

    independent_posterior = {i: priors[i] for i in range(n) if i not in grouped_indices}

    def current_posterior(i: int) -> float:
        if i in grouped_indices:
            belief = structured_beliefs[group_of[i]]
            return float(belief.marginals()[group_local_pos[i]])
        return independent_posterior[i]

    def eig_of(i: int) -> float:
        if i in grouped_indices:
            belief = structured_beliefs[group_of[i]]
            return belief.expected_information_gain(group_local_pos[i], fp_rate=noise_level, fn_rate=noise_level)
        return indep_eig(independent_posterior[i], fp_rate=noise_level, fn_rate=noise_level)

    def apply_observation(i: int, obs: bool) -> None:
        if i in grouped_indices:
            t = group_of[i]
            pos = group_local_pos[i]
            structured_beliefs[t] = structured_beliefs[t].with_observation(pos, obs, noise_level, noise_level)
        else:
            independent_posterior[i] = bayes_update(independent_posterior[i], obs, noise_level, noise_level)

    max_repeats = config.max_repeats_noiseless if noise_level == 0.0 else config.max_repeats_noisy
    budget = n * max_repeats
    repeats_done = [0] * n
    retired = [False] * n

    def is_retired(i: int) -> bool:
        p = current_posterior(i)
        return p >= config.retirement_confidence or p <= (1 - config.retirement_confidence)

    tiebreak = make_tiebreak(n, seed)
    policy: SelectionPolicy = make_policy(policy_name)

    if policy.adaptive:
        fixed_order: list[int] | None = None
    elif isinstance(policy, FrozenInitialPolicy):
        fixed_order = policy.initial_ranking(view, ontology, tiebreak, eig_fn=eig_of)
    else:
        fixed_order = policy.initial_ranking(view, ontology, tiebreak)

    trajectory: list[TrajectoryPoint] = []

    def snapshot(test_number: int) -> None:
        posteriors = {i: current_posterior(i) for i in range(n)}
        # missed true edges: unreachable, fixed posterior 0.0 forever
        offset = n
        for j in range(coverage.n_missed):
            posteriors[offset + j] = 0.0
        labels = dict(true_labels)
        for j in range(coverage.n_missed):
            labels[offset + j] = True
        from ..evaluate.metrics import compute_metrics

        m = compute_metrics(posteriors, labels, threshold=config.reconstruction_threshold)
        trajectory.append(TrajectoryPoint(test_number, m.precision, m.recall, m.f1, m.brier))

    snapshot(0)

    n_tests_performed = 0
    if fixed_order is not None:
        cursor = 0
        cycle_guard = 0
        while n_tests_performed < budget and cycle_guard < budget * 2 + len(fixed_order) + 1:
            cycle_guard += 1
            idx = fixed_order[cursor % len(fixed_order)]
            cursor += 1
            if retired[idx] or repeats_done[idx] >= max_repeats:
                if all(retired[i] or repeats_done[i] >= max_repeats for i in range(n)):
                    break
                continue
            draw = noise_draw(tg.building_id, *real_pairs[idx], repeats_done[idx], seed)
            obs = observe(true_labels[idx], noise_level, noise_level, draw)
            apply_observation(idx, obs)
            repeats_done[idx] += 1
            n_tests_performed += 1
            if is_retired(idx):
                retired[idx] = True
            snapshot(n_tests_performed)
    else:
        while n_tests_performed < budget:
            unresolved = [i for i in range(n) if not retired[i] and repeats_done[i] < max_repeats]
            if not unresolved:
                break
            idx = policy.next_index(unresolved, eig_of, tiebreak)
            draw = noise_draw(tg.building_id, *real_pairs[idx], repeats_done[idx], seed)
            obs = observe(true_labels[idx], noise_level, noise_level, draw)
            apply_observation(idx, obs)
            repeats_done[idx] += 1
            n_tests_performed += 1
            if is_retired(idx):
                retired[idx] = True
            snapshot(n_tests_performed)

    true_parent_count_violations = 0
    for t, members in groups.items():
        n_true_parents = sum(1 for i in members if true_labels[i])
        if n_true_parents > 1:
            true_parent_count_violations += 1

    return TrialResult(
        building_id=tg.building_id,
        relation=relation,
        experiment=experiment,
        policy=policy_name,
        prior_kind=prior_kind,
        noise_level=noise_level,
        lam=lam if is_structured else None,
        seed=seed,
        n_candidates=n,
        n_missed_true_edges=coverage.n_missed,
        budget=budget,
        n_tests_performed=n_tests_performed,
        trajectory=trajectory,
        true_parent_count_violations=true_parent_count_violations,
    )
