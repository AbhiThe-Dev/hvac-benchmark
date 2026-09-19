"""Translate simulated observables into reported answers -- and, separately,
into degraded (technician-error) report variants of the same physical event.

Three artifacts stay separate per the design doc:

1. `contracts.InterventionTruth` -- fault identity, supplies labels only.
2. `contracts.SimulatedObservables` -- what the simulation produced.
3. `contracts.StructuredAnswers` -- what a person could plausibly report.

Rule functions here read only (2) to produce the clean-answer variant of
(3); `contracts.InterventionTruth` (1) must never be read by any function in
this module -- that is the one invariant a unit test in this package
enforces (`tests/test_report_translation.py`), because it is the exact
failure mode the design doc calls out ("fault identity must not directly
determine answers").

`TranslationThresholds` are translation assumptions, not validated human
perception -- they must be reviewed by an HVAC practitioner and are
versioned so a later revision doesn't silently change historical datasets'
meaning. Baseline temperatures and exact injected magnitudes are
deliberately not exposed anywhere past this module.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np

from .contracts import (
    AirflowAnswer,
    Onset,
    OperatingContext,
    Persistence,
    ProblemDirection,
    SimulatedObservables,
    StructuredAnswers,
    SupplyAirFeel,
    ZoneObservableSeries,
)

TRANSLATION_VERSION = "1.0.0"


@dataclass(frozen=True)
class TranslationThresholds:
    """Practitioner-reviewed thresholds. Placeholder values below are
    illustrative starting points only (roughly: 2 degC is a noticeably
    uncomfortable zone deviation, 30% airflow loss is "weak", persistence
    needs three consecutive affected hours) -- treat every field as a TODO
    for HVAC-practitioner review before this translation is used to justify
    any deployment claim.
    """

    version: str = TRANSLATION_VERSION
    discomfort_temp_delta_c: float = 2.0
    weak_airflow_frac: float = 0.7
    absent_airflow_frac: float = 0.15
    warm_supply_delta_c: float = 1.5
    cool_supply_delta_c: float = -1.5
    multi_zone_affected_temp_delta_c: float = 1.0
    outside_air_temp_unusual_delta_c: float = 8.0


DEFAULT_THRESHOLDS = TranslationThresholds()


def _direction(node: ZoneObservableSeries, thresholds: TranslationThresholds) -> ProblemDirection:
    delta = node.changed_mean_temp_c - node.baseline_mean_temp_c
    if abs(delta) < thresholds.discomfort_temp_delta_c:
        return ProblemDirection.UNKNOWN
    return ProblemDirection.TOO_HOT if delta > 0 else ProblemDirection.TOO_COLD


def _airflow(node: ZoneObservableSeries, thresholds: TranslationThresholds) -> AirflowAnswer:
    if node.changed_airflow_frac_of_design is None:
        return AirflowAnswer.UNKNOWN
    frac = node.changed_airflow_frac_of_design
    if frac <= thresholds.absent_airflow_frac:
        return AirflowAnswer.ABSENT
    if frac <= thresholds.weak_airflow_frac:
        return AirflowAnswer.WEAK
    return AirflowAnswer.NORMAL


def _supply_air_feel(node: ZoneObservableSeries, thresholds: TranslationThresholds) -> SupplyAirFeel:
    if node.changed_supply_air_temp_c is None or node.baseline_supply_air_temp_c is None:
        return SupplyAirFeel.UNKNOWN
    delta = node.changed_supply_air_temp_c - node.baseline_supply_air_temp_c
    if delta >= thresholds.warm_supply_delta_c:
        return SupplyAirFeel.WARM
    if delta <= thresholds.cool_supply_delta_c:
        return SupplyAirFeel.COOL
    return SupplyAirFeel.NEUTRAL


def affected_nodes(
    observables: SimulatedObservables, primary_node_id: str, thresholds: TranslationThresholds = DEFAULT_THRESHOLDS
) -> tuple[str, ...]:
    """Nodes other than `primary_node_id` whose simulated temperature moved
    enough to count as an observed multi-zone effect. This is how remote
    "other spaces affected" answers are grounded in demonstrated physical
    effects rather than an assumed hop-count label.
    """
    out = []
    for node in observables.per_node:
        if node.node_id == primary_node_id:
            continue
        delta = abs(node.changed_mean_temp_c - node.baseline_mean_temp_c)
        if delta >= thresholds.multi_zone_affected_temp_delta_c:
            out.append(node.node_id)
    return tuple(sorted(out))


def translate_clean(
    observables: SimulatedObservables,
    primary_node_id: str,
    other_spaces_checked: bool = True,
    thresholds: TranslationThresholds = DEFAULT_THRESHOLDS,
) -> StructuredAnswers:
    """The clean-answer variant: a technically-idealized but still
    qualitative report, derived only from `observables` -- never from fault
    identity or magnitude.
    """
    primary = next((n for n in observables.per_node if n.node_id == primary_node_id), None)
    if primary is None:
        raise ValueError(f"{primary_node_id!r} not present in observables.per_node")

    other_affected = affected_nodes(observables, primary_node_id, thresholds) if other_spaces_checked else ()

    return StructuredAnswers(
        reported_locations=(primary_node_id,),
        direction=_direction(primary, thresholds),
        airflow=_airflow(primary, thresholds),
        supply_air_feel=_supply_air_feel(primary, thresholds),
        persistence=Persistence.CONSTANT_WHILE_OCCUPIED,
        onset=Onset.SEVERAL_DAYS,
        other_spaces_checked=other_spaces_checked,
        other_spaces_affected=other_affected,
        operating_context=observables.demand_mode,
        outside_conditions_unusual=observables.outside_air_temp_unusual,
        questionnaire_version="1.0.0",
    )


# --------------------------------------------------------------------------
# Degraded (technician-error) report variants
# --------------------------------------------------------------------------


def _rng(event_id: str, seed: int) -> np.random.RandomState:
    payload = f"{event_id}|{seed}".encode()
    return np.random.RandomState(int(hashlib.sha256(payload).hexdigest()[:8], 16))


def degrade_report(
    clean: StructuredAnswers,
    event_id: str,
    error_seed: int,
    error_level: float,
) -> StructuredAnswers:
    """Apply a seeded, reproducible reporting-error transform to a clean
    report: at `error_level` in [0, 1], each answer field independently has
    that probability of being (a) omitted (set to its unknown value) or (b)
    mistaken (flipped to a plausible wrong category, e.g. a real
    temperature-sensor-bias/fouling confusion, not an arbitrary category).

    `error_level` is a swept experimental parameter, not a claimed
    technician-error rate -- report sensitivity across several levels
    rather than treating any one as realistic (design doc section 2).
    """
    rng = _rng(event_id, error_seed)

    def maybe_omit_or_flip(value, unknown_value, wrong_values):
        roll = rng.random()
        if roll < error_level / 2:
            return unknown_value
        if roll < error_level:
            return wrong_values[rng.randint(0, len(wrong_values))] if wrong_values else value
        return value

    direction = maybe_omit_or_flip(
        clean.direction,
        ProblemDirection.UNKNOWN,
        [v for v in ProblemDirection if v not in (clean.direction, ProblemDirection.UNKNOWN)],
    )
    airflow = maybe_omit_or_flip(
        clean.airflow, AirflowAnswer.UNKNOWN, [AirflowAnswer.NORMAL, AirflowAnswer.WEAK]
    )
    supply_air_feel = maybe_omit_or_flip(
        clean.supply_air_feel,
        SupplyAirFeel.UNKNOWN,
        [v for v in SupplyAirFeel if v not in (clean.supply_air_feel, SupplyAirFeel.UNKNOWN)],
    )
    onset = maybe_omit_or_flip(
        clean.onset, Onset.UNKNOWN, [v for v in Onset if v not in (clean.onset, Onset.UNKNOWN)]
    )
    other_spaces_checked = clean.other_spaces_checked and rng.random() >= error_level
    other_spaces_affected = clean.other_spaces_affected
    if other_spaces_checked and other_spaces_affected and rng.random() < error_level:
        # A plausible reporting error: naming the wrong nearby zone, not an
        # arbitrary building-wide guess -- drop one truly-affected zone
        # rather than inventing an unaffected one, since this module never
        # sees the private actual graph to know what "nearby but wrong"
        # would be.
        other_spaces_affected = tuple(other_spaces_affected[:-1])

    return StructuredAnswers(
        reported_locations=clean.reported_locations,
        direction=direction,
        airflow=airflow,
        supply_air_feel=supply_air_feel,
        persistence=clean.persistence,
        onset=onset,
        other_spaces_checked=other_spaces_checked,
        other_spaces_affected=other_spaces_affected,
        operating_context=clean.operating_context,
        outside_conditions_unusual=clean.outside_conditions_unusual,
        questionnaire_version=clean.questionnaire_version,
    )


DEGRADED_ERROR_LEVELS: tuple[float, ...] = (0.0, 0.15, 0.30, 0.50)
