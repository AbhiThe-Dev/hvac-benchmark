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
from symptom_pipeline.features import UNREACHABLE_DISTANCE, bfs_distances, extract_candidate_features

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
