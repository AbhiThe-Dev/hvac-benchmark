"""Feature extraction over the whole documented graph, for every physically
compatible candidate connection.

Computed strictly from: endpoint types, blueprint-claimed status, path
distance from reported locations through documented `feeds`/`hasPart`
relationships, shared location, how many other candidates are structurally
indistinguishable from this one, and structured answers. Never uses the
actual (private) graph, injected fault metadata, corruption targets,
simulation handles, or building identifiers -- those would leak ground
truth into a feature the model could key on.

Distances are computed over the *whole* documented graph with no
immediate-neighbor or three-hop cutoff: a candidate whose endpoints are
unreachable from every reported location still gets scored, with an
explicit unreachable indicator, rather than being excluded. A missing
documented edge must not make its candidate impossible to rank.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields

import networkx as nx
from hvac_benchmark.experiment.candidates import Candidate
from hvac_benchmark.graph.networkx_build import TopologyGraph

from .contracts import (
    AirflowAnswer,
    Onset,
    OperatingContext,
    Persistence,
    ProblemDirection,
    StructuredAnswers,
    SupplyAirFeel,
)

UNREACHABLE_DISTANCE = -1
NON_NUMERIC_FIELDS = ("source_id", "target_id", "relation", "source_type", "target_type")


@dataclass(frozen=True)
class CandidateFeatures:
    source_id: str
    target_id: str
    relation: str
    source_type: str | None
    target_type: str | None

    is_claimed: bool
    source_distance_from_report: int
    target_distance_from_report: int
    min_endpoint_distance_from_report: int
    reachable_from_report: bool
    shares_location_with_report: bool
    n_other_spaces_named: int
    # How many OTHER candidates in the same universe are indistinguishable
    # from this one on every structural feature (same endpoint types,
    # relation, claimed status, distances, shared-location). 0 means this
    # candidate is uniquely identified by its structure; N means it is one
    # of N+1 interchangeable siblings and any rank among them is a guess.
    n_indistinguishable_siblings: int

    direction_too_hot: bool
    direction_too_cold: bool
    direction_alternating: bool
    direction_unknown: bool
    airflow_weak: bool
    airflow_absent: bool
    airflow_unknown: bool
    supply_air_warm: bool
    supply_air_cool: bool
    supply_air_unknown: bool
    persistence_intermittent: bool
    persistence_startup_only: bool
    onset_today: bool
    onset_unknown: bool
    other_spaces_checked: bool
    operating_heating: bool
    operating_cooling: bool


NUMERIC_FEATURE_FIELDS: tuple[str, ...] = tuple(
    f.name for f in fields(CandidateFeatures) if f.name not in NON_NUMERIC_FIELDS
)


def _undirected_relation_graph(tg: TopologyGraph, relations: tuple[str, ...] = ("feeds", "hasPart")) -> nx.Graph:
    g = nx.Graph()
    g.add_nodes_from(tg.nodes())
    for rel in relations:
        for s, t in tg.edges_by_relation.get(rel, ()):
            g.add_edge(s, t)
    return g


def bfs_distances(tg: TopologyGraph, sources: tuple[str, ...]) -> dict[str, int]:
    """Hop distance from any reported location to every documented node,
    over the undirected `feeds`/`hasPart` graph. `UNREACHABLE_DISTANCE` for
    nodes with no path from any reported location -- never excluded.
    """
    g = _undirected_relation_graph(tg)
    distances: dict[str, int] = {n: UNREACHABLE_DISTANCE for n in g.nodes()}
    frontier = [n for n in sources if n in g]
    for n in frontier:
        distances[n] = 0
    seen = set(frontier)
    depth = 0
    while frontier:
        depth += 1
        next_frontier = []
        for n in frontier:
            for neighbor in g.neighbors(n):
                if neighbor not in seen:
                    seen.add(neighbor)
                    distances[neighbor] = depth
                    next_frontier.append(neighbor)
        frontier = next_frontier
    return distances


def extract_candidate_features(
    tg: TopologyGraph,
    candidates: list[Candidate],
    claimed_pairs: frozenset[tuple[str, str]],
    answers: StructuredAnswers,
) -> list[CandidateFeatures]:
    distances = bfs_distances(tg, answers.reported_locations)
    report_locations = {tg.node_location(loc) for loc in answers.reported_locations if tg.node_location(loc)}

    def structural_signature(c: Candidate) -> tuple:
        d_source = distances.get(c.source, UNREACHABLE_DISTANCE)
        d_target = distances.get(c.target, UNREACHABLE_DISTANCE)
        shares_location = bool(report_locations) and (
            tg.node_location(c.source) in report_locations or tg.node_location(c.target) in report_locations
        )
        return (
            c.relation,
            tg.node_type(c.source),
            tg.node_type(c.target),
            (c.source, c.target) in claimed_pairs,
            d_source,
            d_target,
            shares_location,
        )

    # Deliberately built from the same structural inputs as the features
    # above and never from node ids, so it cannot leak identity: it only
    # reports how many other candidates share this one's feature values.
    signature_counts = Counter(structural_signature(c) for c in candidates)

    out: list[CandidateFeatures] = []
    for c in candidates:
        d_source = distances.get(c.source, UNREACHABLE_DISTANCE)
        d_target = distances.get(c.target, UNREACHABLE_DISTANCE)
        finite = [d for d in (d_source, d_target) if d >= 0]
        shares_location = bool(report_locations) and (
            tg.node_location(c.source) in report_locations or tg.node_location(c.target) in report_locations
        )

        out.append(
            CandidateFeatures(
                source_id=c.source,
                target_id=c.target,
                relation=c.relation,
                source_type=tg.node_type(c.source),
                target_type=tg.node_type(c.target),
                is_claimed=(c.source, c.target) in claimed_pairs,
                source_distance_from_report=d_source,
                target_distance_from_report=d_target,
                min_endpoint_distance_from_report=min(finite) if finite else UNREACHABLE_DISTANCE,
                reachable_from_report=bool(finite),
                shares_location_with_report=shares_location,
                n_other_spaces_named=len(answers.other_spaces_affected),
                n_indistinguishable_siblings=signature_counts[structural_signature(c)] - 1,
                direction_too_hot=answers.direction == ProblemDirection.TOO_HOT,
                direction_too_cold=answers.direction == ProblemDirection.TOO_COLD,
                direction_alternating=answers.direction == ProblemDirection.ALTERNATING,
                direction_unknown=answers.direction == ProblemDirection.UNKNOWN,
                airflow_weak=answers.airflow == AirflowAnswer.WEAK,
                airflow_absent=answers.airflow == AirflowAnswer.ABSENT,
                airflow_unknown=answers.airflow == AirflowAnswer.UNKNOWN,
                supply_air_warm=answers.supply_air_feel == SupplyAirFeel.WARM,
                supply_air_cool=answers.supply_air_feel == SupplyAirFeel.COOL,
                supply_air_unknown=answers.supply_air_feel == SupplyAirFeel.UNKNOWN,
                persistence_intermittent=answers.persistence == Persistence.INTERMITTENT,
                persistence_startup_only=answers.persistence == Persistence.STARTUP_ONLY,
                onset_today=answers.onset == Onset.TODAY,
                onset_unknown=answers.onset == Onset.UNKNOWN,
                other_spaces_checked=answers.other_spaces_checked,
                operating_heating=answers.operating_context == OperatingContext.HEATING,
                operating_cooling=answers.operating_context == OperatingContext.COOLING,
            )
        )
    return out
