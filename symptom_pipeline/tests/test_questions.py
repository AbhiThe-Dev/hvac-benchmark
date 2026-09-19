from symptom_pipeline.questions import QUESTIONNAIRE_V1, validate_questionnaire_coverage


def test_questionnaire_has_all_eight_questions():
    assert len(QUESTIONNAIRE_V1) == 8
    assert {q.key for q in QUESTIONNAIRE_V1} == {
        "reported_locations",
        "direction",
        "airflow",
        "supply_air_feel",
        "persistence",
        "onset",
        "other_spaces_affected",
        "operating_context",
    }


def test_questionnaire_choices_match_contracts_enums():
    validate_questionnaire_coverage()
