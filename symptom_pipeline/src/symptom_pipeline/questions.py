"""The fixed v1 questionnaire.

These are hypotheses about useful questions, not established diagnostic
rules -- they should be reviewed with an HVAC practitioner and each
question's incremental discriminative value should be measured on held-out
cases before being trusted. Nothing here implies that qualitative answers
always distinguish sensor bias, fouling, and connection errors.

`QUESTIONNAIRE_V1` is descriptive metadata for UI/documentation/versioning
purposes; the actual answer *shape* a report is validated against is
`contracts.StructuredAnswers`, so a question and its allowed choices cannot
drift apart silently -- `validate_questionnaire_coverage` below checks that.
"""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import (
    AirflowAnswer,
    Onset,
    OperatingContext,
    Persistence,
    ProblemDirection,
    SupplyAirFeel,
)

QUESTIONNAIRE_VERSION = "1.0.0"


@dataclass(frozen=True)
class Question:
    key: str
    text: str
    answer_choices: tuple[str, ...]
    discrimination_purpose: str


QUESTIONNAIRE_V1: tuple[Question, ...] = (
    Question(
        key="reported_locations",
        text="Where is the problem?",
        answer_choices=("<reviewed zone/equipment identity, one or more>",),
        discrimination_purpose="Establish the reported symptom location",
    ),
    Question(
        key="direction",
        text="What is wrong?",
        answer_choices=tuple(v.value for v in ProblemDirection),
        discrimination_purpose="Separate direction and operating context",
    ),
    Question(
        key="airflow",
        text="Is air coming from the outlet?",
        answer_choices=tuple(v.value for v in AirflowAnswer),
        discrimination_purpose="Distinguish service/flow problems from temperature-only problems",
    ),
    Question(
        key="supply_air_feel",
        text="What does the supplied air feel like?",
        answer_choices=tuple(v.value for v in SupplyAirFeel),
        discrimination_purpose="Separate delivery from conditioning problems",
    ),
    Question(
        key="persistence",
        text="When does it happen?",
        answer_choices=tuple(v.value for v in Persistence),
        discrimination_purpose="Distinguish persistent and schedule-dependent effects",
    ),
    Question(
        key="onset",
        text="How long has it happened?",
        answer_choices=tuple(v.value for v in Onset),
        discrimination_purpose="Represent onset without requiring exact timestamps",
    ),
    Question(
        key="other_spaces_affected",
        text="Are other spaces affected?",
        answer_choices=("<named spaces>", "none observed", "not checked"),
        discrimination_purpose="Support shared-system and multi-hop explanations",
    ),
    Question(
        key="operating_context",
        text="What was the operating context?",
        answer_choices=tuple(v.value for v in OperatingContext) + ("outside conditions unusual: yes/no/unknown",),
        discrimination_purpose="Condition interpretation on system demand",
    ),
)


def validate_questionnaire_coverage() -> None:
    """Every enum referenced by `QUESTIONNAIRE_V1`'s answer choices must be
    exactly the enum `contracts.StructuredAnswers` uses for that field, so
    the documentation table and the validated schema cannot silently drift
    apart. Raises `AssertionError` on mismatch; called by the test suite.
    """
    by_key = {q.key: q for q in QUESTIONNAIRE_V1}
    checks = {
        "direction": ProblemDirection,
        "airflow": AirflowAnswer,
        "supply_air_feel": SupplyAirFeel,
        "persistence": Persistence,
        "onset": Onset,
    }
    for key, enum_cls in checks.items():
        documented = set(by_key[key].answer_choices)
        actual = {v.value for v in enum_cls}
        assert documented == actual, f"{key}: questionnaire lists {documented}, contracts enum has {actual}"
