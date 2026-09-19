import math

from hvac_benchmark.config import DEFAULT_CONFIG
from hvac_benchmark.experiment.blueprint import symptom_flagged_nodes

from symptom_pipeline.contracts import PredictionRecord
from symptom_pipeline.evaluation import (
    brier_score,
    event_coverage_at_k,
    mean_reciprocal_rank,
    mean_tests_to_attainment,
    pair_recall_at_k,
    reciprocal_rank,
    run_paired_comparison,
)

from ._fixtures import forced_removal_blueprint, make_tg


def test_pair_recall_at_k():
    ranked = [("A", "B"), ("C", "D"), ("E", "F")]
    true = frozenset({("A", "B"), ("E", "F")})
    assert pair_recall_at_k(ranked, true, k=1) == 0.5
    assert pair_recall_at_k(ranked, true, k=3) == 1.0


def test_pair_recall_at_k_nan_with_no_true_pairs():
    assert math.isnan(pair_recall_at_k([("A", "B")], frozenset(), k=1))


def test_event_coverage_at_k():
    events = {"e1": frozenset({("A", "B")}), "e2": frozenset({("C", "D"), ("E", "F")})}
    ranked = [("A", "B"), ("C", "D"), ("E", "F")]
    assert event_coverage_at_k(events, ranked, k=1) == 0.5  # only e1 fully covered
    assert event_coverage_at_k(events, ranked, k=3) == 1.0


def test_reciprocal_rank_and_mrr():
    assert reciprocal_rank([("A", "B"), ("C", "D")], frozenset({("C", "D")})) == 0.5
    assert reciprocal_rank([("A", "B")], frozenset({("X", "Y")})) == 0.0
    mrr = mean_reciprocal_rank(
        [
            ([("A", "B"), ("C", "D")], frozenset({("A", "B")})),
            ([("A", "B"), ("C", "D")], frozenset({("C", "D")})),
        ]
    )
    assert mrr == (1.0 + 0.5) / 2


def test_brier_score_perfect_and_worst():
    assert brier_score([1.0, 0.0], [1, 0]) == 0.0
    assert brier_score([0.0, 1.0], [1, 0]) == 1.0


def test_mean_tests_to_attainment_reports_non_attainment_without_dropping():
    class Row:
        def __init__(self, v):
            self.n_tests_to_full_flag_sustained = v

    rows = [Row(3), Row(None), Row(5)]
    stats = mean_tests_to_attainment(rows)
    assert stats["n_total"] == 3
    assert stats["n_attained"] == 2
    assert stats["mean_among_attained"] == 4.0
    assert math.isclose(stats["non_attainment_rate"], 1 / 3)


def test_run_paired_comparison_covers_all_symptom_sources(ontology):
    tg = make_tg()
    bp = forced_removal_blueprint(tg)
    flagged = symptom_flagged_nodes(tg, bp)
    prediction = PredictionRecord(
        report_id="r1",
        building_id=tg.building_id,
        predictions=(),
        selected_pairs=(),
        endpoint_node_union=frozenset(flagged),
        model_version="test",
        calibration_version="test",
        questionnaire_version="1.0.0",
        graph_version="test",
        supported=True,
    )
    rows = run_paired_comparison(
        tg,
        ontology,
        bp,
        DEFAULT_CONFIG,
        policies=("active", "blueprint_literal"),
        noise_levels=(0.0,),
        seeds=(0,),
        prediction=prediction,
    )
    sources_seen = {r.symptom_source for r in rows}
    assert sources_seen == {"none", "oracle", "learned"}
    # 2 policies x 3 symptom sources x 1 noise x 1 seed
    assert len(rows) == 6
