from hvac_benchmark.experiment.candidates import Candidate

from symptom_pipeline.contracts import (
    AirflowAnswer,
    Onset,
    OperatingContext,
    Persistence,
    ProblemDirection,
    StructuredAnswers,
    SupplyAirFeel,
)
from symptom_pipeline.features import NUMERIC_FEATURE_FIELDS, UNREACHABLE_DISTANCE, bfs_distances, extract_candidate_features

from ._fixtures import make_tg


def _answers(reported_locations=("Zone_0",)) -> StructuredAnswers:
    return StructuredAnswers(
        reported_locations=reported_locations,
        direction=ProblemDirection.TOO_HOT,
        airflow=AirflowAnswer.WEAK,
        supply_air_feel=SupplyAirFeel.WARM,
        persistence=Persistence.CONSTANT_WHILE_OCCUPIED,
        onset=Onset.SEVERAL_DAYS,
        other_spaces_checked=True,
        other_spaces_affected=(),
        operating_context=OperatingContext.COOLING,
        outside_conditions_unusual=False,
    )


def test_bfs_distances_from_reported_location():
    tg = make_tg()
    distances = bfs_distances(tg, ("Zone_0",))
    assert distances["Zone_0"] == 0
    assert distances["VAV_0"] == 1
    assert distances["AHU"] == 2
    # VAV_1/Zone_1 are reachable via the shared AHU, not excluded.
    assert distances["VAV_1"] == 3
    assert distances["Zone_1"] == 4


def test_bfs_distances_unreachable_when_no_reported_location_present():
    tg = make_tg()
    distances = bfs_distances(tg, ())
    assert all(d == UNREACHABLE_DISTANCE for d in distances.values())


def test_extract_candidate_features_scores_every_candidate_including_unreachable():
    tg = make_tg()
    candidates = [
        Candidate("AHU", "VAV_0", "feeds", "r"),
        Candidate("AHU", "VAV_1", "feeds", "r"),
        Candidate("VAV_0", "Zone_0", "feeds", "r"),
        Candidate("VAV_1", "Zone_1", "feeds", "r"),
    ]
    claimed = frozenset({("AHU", "VAV_0"), ("VAV_0", "Zone_0"), ("AHU", "VAV_1"), ("VAV_1", "Zone_1")})
    features = extract_candidate_features(tg, candidates, claimed, _answers(("Zone_0",)))

    assert len(features) == len(candidates)
    by_pair = {(f.source_id, f.target_id): f for f in features}

    close = by_pair[("VAV_0", "Zone_0")]
    assert close.min_endpoint_distance_from_report == 0
    assert close.reachable_from_report is True
    assert close.is_claimed is True

    far = by_pair[("VAV_1", "Zone_1")]
    assert far.reachable_from_report is True  # connected via the shared AHU, just farther
    assert far.min_endpoint_distance_from_report > close.min_endpoint_distance_from_report

    # A candidate whose endpoints share no path to any reported location at
    # all must still be scored, never excluded.
    disconnected_candidates = extract_candidate_features(tg, candidates, claimed, _answers(()))
    assert all(f.reachable_from_report is False for f in disconnected_candidates)
    assert len(disconnected_candidates) == len(candidates)


def test_answer_features_reflect_structured_answers():
    tg = make_tg()
    candidates = [Candidate("AHU", "VAV_0", "feeds", "r")]
    features = extract_candidate_features(tg, candidates, frozenset(), _answers())
    f = features[0]
    assert f.direction_too_hot is True
    assert f.direction_too_cold is False
    assert f.airflow_weak is True
    assert f.supply_air_warm is True


def _make_tg_with_terminal_coils():
    """`make_tg()` plus the coil shape found in the real sys07 extraction: one
    AHU-owned coil (`hasPart` -> AHU) and terminal reheat coils whose ONLY
    documented relation is `pump -feeds-> coil` (no edge to their VAV/zone).
    """
    tg = make_tg()
    for node, kind in (("Pump_A", "Pump"), ("Pump_B", "Pump"), ("AHU_Coil", "Heating_Coil"),
                       ("Reheat_1", "Heating_Coil"), ("Reheat_2", "Heating_Coil")):
        tg.nx_graph.add_node(node, brick_type=kind, brick_types=[kind], location=None)
    tg.nx_graph.add_edge("AHU_Coil", "AHU", relation="hasPart")
    tg.edges_by_relation["hasPart"].add(("AHU_Coil", "AHU"))
    for coil in ("AHU_Coil", "Reheat_1", "Reheat_2"):
        tg.nx_graph.add_edge("Pump_A", coil, relation="feeds")
        tg.edges_by_relation["feeds"].add(("Pump_A", coil))
    return tg


def test_indistinguishable_terminal_coils_report_their_tie_group_size():
    tg = _make_tg_with_terminal_coils()
    candidates = [Candidate(p, c, "feeds", "r") for p in ("Pump_A", "Pump_B") for c in ("AHU_Coil", "Reheat_1", "Reheat_2")]
    claimed = frozenset(p for p in tg.edges_by_relation["feeds"] if p[0].startswith("Pump"))
    by_pair = {(f.source_id, f.target_id): f for f in extract_candidate_features(tg, candidates, claimed, _answers(("Zone_0",)))}

    # Regression: before this feature, every structural field was identical
    # for the two terminal coils under the same pump, so nothing told the
    # model it was guessing among siblings.
    a, b = by_pair[("Pump_A", "Reheat_1")], by_pair[("Pump_A", "Reheat_2")]
    assert (a.source_distance_from_report, a.target_distance_from_report, a.is_claimed) == (
        b.source_distance_from_report, b.target_distance_from_report, b.is_claimed)
    assert a.n_indistinguishable_siblings == b.n_indistinguishable_siblings == 1

    # The AHU-owned coil is reachable via hasPart, so it is structurally unique.
    assert by_pair[("Pump_A", "AHU_Coil")].n_indistinguishable_siblings == 0
    # Same coils under the unclaimed pump differ on `is_claimed`, so they form their own group.
    assert by_pair[("Pump_B", "Reheat_1")].n_indistinguishable_siblings == 1
    assert by_pair[("Pump_B", "AHU_Coil")].n_indistinguishable_siblings == 0


def test_sibling_count_is_numeric_and_ids_stay_excluded():
    tg = _make_tg_with_terminal_coils()
    candidates = [Candidate("Pump_A", "Reheat_1", "feeds", "r"), Candidate("Pump_A", "Reheat_2", "feeds", "r")]
    claimed = frozenset({("Pump_A", "Reheat_1"), ("Pump_A", "Reheat_2")})
    f = extract_candidate_features(tg, candidates, claimed, _answers())
    assert [x.n_indistinguishable_siblings for x in f] == [1, 1]
    assert "n_indistinguishable_siblings" in NUMERIC_FEATURE_FIELDS
    assert "source_id" not in NUMERIC_FEATURE_FIELDS and "target_id" not in NUMERIC_FEATURE_FIELDS
