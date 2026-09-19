"""Core data contracts for the symptom-informed ranking pipeline.

These types are the shared vocabulary between ingestion, the questionnaire,
report translation, feature extraction, model training, calibration, and the
benchmark adapter. Three artifacts are kept deliberately separate per the
design doc, and this module gives each its own type so they cannot be
accidentally conflated:

- `DocumentedGraph` / `EquipmentIdentity` / `DocumentedConnection`: the
  *claimed* topology, as a reviewer would read it off drawings or a table.
- `StructuredAnswers` / `SymptomReport`: what a person could plausibly
  report, never raw simulated observables and never fault identity.
- `DiscrepancyEvent` / `DiscrepancyLabel`: private ground truth, used only
  by training and evaluation code, never by ingestion or the model itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

SCHEMA_VERSION = "1.0.0"


# --------------------------------------------------------------------------
# Documented ("blueprint") topology
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class EquipmentIdentity:
    """A stable equipment/zone identity, reviewed and mapped from source
    drawings or tables into the documented graph.

    `source_ref` records where a human reviewer got this identity from (a
    drawing sheet, a table row, a Brick URI) for audit purposes only; it is
    never read by feature extraction or the model.
    """

    equipment_id: str
    brick_type: str
    display_name: str
    room_label: str | None = None
    source_ref: str | None = None


@dataclass(frozen=True)
class DocumentedConnection:
    """One documented relationship claim between two reviewed equipment
    identities. `relation` matches `hvac_benchmark`'s relation vocabulary
    ("feeds", "hasPart", "hasPoint") so documented connections can be
    compared against `hvac_benchmark` candidates without translation.
    """

    source_id: str
    target_id: str
    relation: str


@dataclass(frozen=True)
class DocumentedGraph:
    """The full documented topology as ingested from a Brick graph or an
    equipment/connection table, plus enough provenance to reproduce the
    ingestion later.

    `source_hash` is the sha256 of the raw ingested file(s), recorded
    because neither the benchmark root nor the physics_pipeline working
    tree can be relied on as a clean git checkout for reproducibility.
    """

    building_id: str
    equipment: tuple[EquipmentIdentity, ...]
    claimed_connections: tuple[DocumentedConnection, ...]
    ingestion_source: str
    source_hash: str
    schema_version: str = SCHEMA_VERSION

    def equipment_by_id(self) -> dict[str, EquipmentIdentity]:
        return {e.equipment_id: e for e in self.equipment}

    def claimed_pairs(self, relation: str = "feeds") -> frozenset[tuple[str, str]]:
        return frozenset(
            (c.source_id, c.target_id) for c in self.claimed_connections if c.relation == relation
        )


# --------------------------------------------------------------------------
# Structured questionnaire answers and symptom reports
# --------------------------------------------------------------------------


class ProblemDirection(str, Enum):
    TOO_HOT = "too_hot"
    TOO_COLD = "too_cold"
    ALTERNATING = "alternating"
    UNKNOWN = "unknown"


class AirflowAnswer(str, Enum):
    NORMAL = "normal"
    WEAK = "weak"
    ABSENT = "absent"
    UNKNOWN = "unknown"


class SupplyAirFeel(str, Enum):
    COOL = "cool"
    NEUTRAL = "neutral"
    WARM = "warm"
    UNKNOWN = "unknown"


class Persistence(str, Enum):
    CONSTANT_WHILE_OCCUPIED = "constant_while_occupied"
    INTERMITTENT = "intermittent"
    STARTUP_ONLY = "startup_only"
    UNKNOWN = "unknown"


class Onset(str, Enum):
    TODAY = "today"
    SEVERAL_DAYS = "several_days"
    LONGER = "longer"
    UNKNOWN = "unknown"


class OperatingContext(str, Enum):
    HEATING = "heating"
    COOLING = "cooling"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class StructuredAnswers:
    """One completed questionnaire response (see `questions.QUESTIONNAIRE_V1`
    for the fixed question set this answers). Every field has an explicit
    "unknown"/not-checked value; nothing here is required to be filled in --
    a missing-answer indicator is itself a feature, not an error.
    """

    reported_locations: tuple[str, ...]  # equipment_id values, reviewed
    direction: ProblemDirection
    airflow: AirflowAnswer
    supply_air_feel: SupplyAirFeel
    persistence: Persistence
    onset: Onset
    other_spaces_checked: bool  # False = "not checked"; distinct from "checked, none affected"
    other_spaces_affected: tuple[str, ...]  # equipment_id values; only meaningful if checked
    operating_context: OperatingContext
    outside_conditions_unusual: bool | None  # None = unknown
    questionnaire_version: str = "1.0.0"


@dataclass(frozen=True)
class SymptomReport:
    """A versioned symptom report referencing reviewed equipment IDs in a
    `DocumentedGraph`. This is the only symptom-derived input the model or
    the benchmark adapter ever sees; it never carries simulated observables,
    the actual (private) topology, or fault identity.

    `reporting_error_seed` is `None` for a clean-answer variant and an int
    for a degraded-report variant generated from the same physical event
    (see `report_translation.py`); both must land in the same dataset split.
    """

    report_id: str
    building_id: str
    answers: StructuredAnswers
    reporting_error_seed: int | None = None
    translation_version: str = "1.0.0"


# --------------------------------------------------------------------------
# Private ground truth (training/evaluation only)
# --------------------------------------------------------------------------


class CorruptionKind(str, Enum):
    MISSING = "missing"  # documented, not actually present
    FABRICATED = "fabricated"  # actually present, not documented
    MISATTRIBUTED = "misattributed"  # documented to the wrong endpoint


@dataclass(frozen=True)
class DiscrepancyEvent:
    """One physical connection discrepancy. A misattribution touches two
    discordant pairs (the true parent the blueprint dropped, and the wrong
    parent it added) but is one event -- both pair-level and event-level
    truth must be preserved, matching `hvac_benchmark.experiment.blueprint
    .CorruptionEvent`'s convention.
    """

    event_id: str
    corruption_kind: CorruptionKind
    discordant_pairs: tuple[tuple[str, str], ...]
    target_id: str


@dataclass(frozen=True)
class DiscrepancyLabel:
    """Ground truth for one candidate pair. Never exposed to ingestion,
    feature extraction, or the model -- training/evaluation code only.
    """

    source_id: str
    target_id: str
    relation: str
    is_discordant: bool
    event_id: str | None  # None if not discordant


# --------------------------------------------------------------------------
# Physical simulation records (private truth -- never fed to the model)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class InterventionTruth:
    """Artifact 1 of 3 in the physics-to-answer translation (design doc
    section 2, "Physics-to-answer translation"): the changed connection, any
    physical fault, its magnitude, and timing. Supplies labels and
    experimental conditions; must never directly determine a reported
    answer -- see `report_translation.py`.
    """

    event_id: str
    building_id: str
    changed_connection: tuple[str, str, str]  # (source_id, target_id, relation)
    corruption_kind: "CorruptionKind"
    operational_fault: str | None  # e.g. "thermostat_offset", "coil_fouling", or None
    fault_magnitude: float | None
    fault_onset_hour: float | None
    baseline_run_id: str
    changed_run_id: str


@dataclass(frozen=True)
class ZoneObservableSeries:
    """Simulated timeseries for one zone/equipment node, baseline vs.
    changed run. Kept as summary statistics (not raw hourly series) so this
    record stays small enough to persist per-event; the design doc's
    translation thresholds (section 2) are applied to exactly these fields.
    """

    node_id: str
    baseline_mean_temp_c: float
    changed_mean_temp_c: float
    baseline_setpoint_c: float | None
    changed_setpoint_c: float | None
    baseline_supply_air_temp_c: float | None
    changed_supply_air_temp_c: float | None
    baseline_airflow_frac_of_design: float | None
    changed_airflow_frac_of_design: float | None


@dataclass(frozen=True)
class SimulatedObservables:
    """Artifact 2 of 3: what the physics simulation actually produced,
    across every zone/equipment node examined for symptom effects (not just
    the intervention target -- remote-cause cases must be represented here
    too). Never exposed to the model; `report_translation.py` consumes this
    to produce `StructuredAnswers`, and evaluation code uses it to build
    one-hop/two-hop/longer-path strata.
    """

    event_id: str
    per_node: tuple[ZoneObservableSeries, ...]
    demand_mode: OperatingContext
    outside_air_temp_unusual: bool
    quality_ok: bool
    quality_notes: str = ""


# --------------------------------------------------------------------------
# Model output
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class CandidateDiscrepancyPrediction:
    """One ranked record: the model's calibrated estimate that
    `(source_id, target_id)` disagrees with the documented graph, given the
    report and the documented graph alone. Marginal, not a softmax
    distribution -- multiple candidates may each be independently likely to
    be wrong, and this is not a probability that the connection exists.
    """

    source_id: str
    target_id: str
    relation: str
    discrepancy_probability: float
    is_selected: bool = False


@dataclass(frozen=True)
class PredictionRecord:
    """Full output of one model invocation: every candidate's ranked
    probability, the selected suspect prefix, and enough version
    identifiers to reproduce the call bit-for-bit later.
    """

    report_id: str
    building_id: str
    predictions: tuple[CandidateDiscrepancyPrediction, ...]
    selected_pairs: tuple[tuple[str, str], ...]
    endpoint_node_union: frozenset[str]
    model_version: str
    calibration_version: str
    questionnaire_version: str
    graph_version: str
    supported: bool
    abstain_reason: str | None = None

    def suspect_set_size(self) -> int:
        return len(self.selected_pairs)

    def endpoint_expansion_size(self) -> int:
        return len(self.endpoint_node_union)
