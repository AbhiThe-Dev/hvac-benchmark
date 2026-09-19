"""Central configuration and shared constants for the benchmark.

All numeric knobs called out in the research plan live here so the
pipeline, tests, and report generation read a single source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BenchmarkConfig:
    # Paired seeds shared across topologies/policies/noise levels so that
    # "seed i" draws the same random stream everywhere it is used.
    n_seeds: int = 30
    base_seed: int = 20240601

    # Direct relationship query noise levels (false-positive / false-negative
    # rates), applied symmetrically per the plan.
    noise_levels: tuple[float, ...] = (0.0, 0.05, 0.15)

    # Retirement rule: an edge is resolved (removed from further testing) once
    # its posterior probability of existing crosses this confidence band.
    retirement_confidence: float = 0.99

    # Repeats permitted per candidate under noise; noiseless runs always use 1.
    max_repeats_noiseless: int = 1
    max_repeats_noisy: int = 10

    # Reconstruction threshold: an edge is asserted present if P(exists) > this.
    reconstruction_threshold: float = 0.5

    # Precision/recall targets. Primary is checked first; secondary is
    # reported when reached but never substituted for the primary claim.
    primary_precision: float = 0.90
    primary_recall: float = 0.90
    secondary_precision: float = 0.95
    secondary_recall: float = 0.95

    # Structured-belief cardinality coupling exp(-lambda * (k-1)^2).
    default_lambda: float = 1.0
    lambda_sensitivity: tuple[float, ...] = (0.0, 0.5, 1.0, 2.0)

    # Cap on exact enumeration size (2^m) for structured joint entropy; real
    # Brick candidate-parent sets for a single terminal/zone are small, so
    # this is essentially never hit but guards against pathological inputs.
    structured_enumeration_cap: int = 20

    # Number of seeded synthetic AHU-VAV-zone graphs (supplementary only).
    n_synthetic_graphs: int = 10

    # Feasibility cap on a single (topology, relation)'s candidate universe.
    # Trial cost is O(n^2) in universe size (the active policy scores every
    # candidate per step, metrics rescan every candidate per step, and the
    # budget is n tests), which is fine for every LBNL universe (max 3219)
    # but not for some MORTAR buildings (up to ~821k hasPoint candidates).
    # Above the cap the relation is marked unavailable with the reason
    # recorded -- reported, not silently dropped. 3300 is deliberately just
    # above the largest LBNL universe so no pre-existing LBNL relation changes.
    max_candidate_universe: int = 3300

    relations: tuple[str, ...] = ("feeds", "hasPoint", "hasPart")
    primary_relation: str = "feeds"

    results_dir: str = "results"
    cache_dir: str = "data_cache"

    # --- Troubleshooting-against-a-blueprint mode (separate from discovery
    # mode above; see experiment/blueprint.py, experiment/troubleshooting_runner.py) ---

    # Corruption severity = number of corruption *events* (misattribution
    # counts as one event even though it touches two candidate pairs).
    troubleshooting_severities: tuple[int, ...] = (1, 2, 3)
    # Independently-seeded corrupted-blueprint variants per (topology,
    # severity), and tie-break/noise replicate seeds per variant. Kept well
    # below the 30-seed discovery grid deliberately, to bound total runtime
    # the same way ABLATION_TOPOLOGIES bounds the ablation grid -- this is a
    # small case study, not a statistically powered sweep.
    troubleshooting_n_variants: int = 3
    troubleshooting_n_seeds_per_variant: int = 3
    troubleshooting_base_seed: int = 87200001

    # Rare-deviation prior: near-certain on blueprint-claimed edges, sparse
    # floor (matches priors.PRIOR_FLOOR) elsewhere in the candidate universe.
    blueprint_confidence: float = 0.97
    blueprint_absent_prior: float = 0.02

    # Blend factor pulling a symptom-flagged-region candidate's prior toward
    # 0.5 (uncertainty) in the symptom-triggered sub-experiment; 0 = no
    # effect, 1 = fully reset to uninformed.
    symptom_prior_relax: float = 0.5


DEFAULT_CONFIG = BenchmarkConfig()


@dataclass(frozen=True)
class PolicyName:
    ACTIVE: str = "active"
    RANDOM: str = "random"
    TRAVERSAL: str = "traversal"
    RULE_BASED: str = "rule_based"
    FROZEN_INITIAL: str = "frozen_initial"


POLICIES = (
    PolicyName.ACTIVE,
    PolicyName.RANDOM,
    PolicyName.TRAVERSAL,
    PolicyName.RULE_BASED,
    PolicyName.FROZEN_INITIAL,
)
