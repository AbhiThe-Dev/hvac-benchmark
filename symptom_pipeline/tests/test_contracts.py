from symptom_pipeline.contracts import (
    AirflowAnswer,
    CandidateDiscrepancyPrediction,
    DocumentedConnection,
    DocumentedGraph,
    EquipmentIdentity,
    Onset,
    OperatingContext,
    Persistence,
    PredictionRecord,
    ProblemDirection,
    StructuredAnswers,
    SupplyAirFeel,
)


def _documented_graph() -> DocumentedGraph:
    equipment = (
        EquipmentIdentity("AHU_1", "AHU", "AHU 1"),
        EquipmentIdentity("VAV_1", "VAV", "VAV 1", room_label="R1"),
    )
    connections = (DocumentedConnection("AHU_1", "VAV_1", "feeds"),)
    return DocumentedGraph("bldg", equipment, connections, "equipment_table", "deadbeef")


def test_documented_graph_lookup_helpers():
    dg = _documented_graph()
    by_id = dg.equipment_by_id()
    assert by_id["AHU_1"].brick_type == "AHU"
    assert dg.claimed_pairs("feeds") == frozenset({("AHU_1", "VAV_1")})
    assert dg.claimed_pairs("hasPart") == frozenset()


def test_prediction_record_size_helpers():
    predictions = (
        CandidateDiscrepancyPrediction("A", "B", "feeds", 0.9, is_selected=True),
        CandidateDiscrepancyPrediction("C", "D", "feeds", 0.1, is_selected=False),
    )
    record = PredictionRecord(
        report_id="r1",
        building_id="bldg",
        predictions=predictions,
        selected_pairs=(("A", "B"),),
        endpoint_node_union=frozenset({"A", "B"}),
        model_version="v1",
        calibration_version="v1",
        questionnaire_version="1.0.0",
        graph_version="v1",
        supported=True,
    )
    assert record.suspect_set_size() == 1
    assert record.endpoint_expansion_size() == 2


def test_structured_answers_permit_unknown_everywhere():
    answers = StructuredAnswers(
        reported_locations=(),
        direction=ProblemDirection.UNKNOWN,
        airflow=AirflowAnswer.UNKNOWN,
        supply_air_feel=SupplyAirFeel.UNKNOWN,
        persistence=Persistence.UNKNOWN,
        onset=Onset.UNKNOWN,
        other_spaces_checked=False,
        other_spaces_affected=(),
        operating_context=OperatingContext.UNKNOWN,
        outside_conditions_unusual=None,
    )
    assert answers.outside_conditions_unusual is None
