"""Causal experiment generation.

For this package's cohort, the design doc reverses `physics_pipeline`'s
original pipeline roles (section 2, "Causal training examples"):

    baseline model + its documented topology   ==  the BLUEPRINT
    one rewired model + its realized topology  ==  the ACTUAL system

STATUS: partially implemented, on purpose, after empirically confirming
what the current `physics_pipeline` object model (and its ten baseline
archetypes) actually supports. Read `KNOWN LIMITATIONS` below before
trusting the scope of what this module can generate.

## What was found before writing any of this

`reconcile_realized_topology` was the confirmed gap in the previous pass:
`physics_pipeline.rewire` mutates a model in place and `physics_pipeline
.extract.extract_topology` re-derives a graph, but nothing diffs a
post-rewire extraction against the pre-rewire one and reconciles node
identity across the two. Before writing that reconciliation logic, two load-
bearing assumptions were verified empirically (not assumed):

1. **OpenStudio object handles are stable across independent reloads of the
   same `.osm` file.** Confirmed directly: loading `baseline_sys07.osm`
   twice and comparing every `AirLoopHVAC`, `ThermalZone`, `PlantLoop`, and
   `Pump` handle between the two loads showed 100% agreement. This is also
   implicitly relied on by `physics_pipeline.pipeline`'s own
   `_resolve()`/`check_blueprint_physical_plausibility` (which resolves a
   node id captured from one load against a freshly-reloaded model of the
   same file) -- so this module's approach is consistent with, not
   additional risk beyond, what the existing pipeline already trusts.
2. **`.clone()` does NOT preserve identity by name or handle.** Confirmed
   directly: cloning a VAV:Reheat terminal within the same model produced a
   different handle *and* a renumbered name ("...Reheat 8" -> "...Reheat
   12", not "...Reheat 8_1"). Name-suffix stripping is therefore not a
   viable reconciliation strategy for a destroyed-and-recreated object;
   `reconcile_realized_topology` below uses a structural signature
   (brick_type + neighboring relation/type multiset) instead, deliberately
   excluding location (see that function's docstring for why), and refuses
   to guess when more than one candidate matches.

## KNOWN LIMITATIONS (read before generating a batch)

**Every zone-side rewire in the current `physics_pipeline` destroys real
equipment as a side effect, on every one of the 10 archetypes, because
every zone in every archetype already has its own terminal** (confirmed
empirically below, and independently stated by `rewire.py`'s own
`add_extra_service` docstring: "every zone in these test buildings is
already served"). Concretely:

- `remove_zone_service` / `remove_coil_service`: deletes the terminal/coil
  outright -- literally "equipment removed entirely."
- `reassign_terminal` / `add_extra_service`: clones a terminal to serve a
  *new* zone, but that zone's own pre-existing terminal has to be removed
  first (a zone can only have one), and the *donor* zone's clone-source
  terminal is destroyed as part of `_remove_branch_safely` too, in
  `reassign_terminal`'s case. Net effect: at least one terminal is
  destroyed with no reconciled counterpart anywhere in the realized graph
  -- an inventory change beyond the one intended connection edit, which is
  exactly what the design doc's "fixed-inventory connection task" excludes
  from v1.
- `set_ahu_direct_service`: same problem, plus the *replacement* object
  (a freshly-constructed pass-through terminal) has no documented
  counterpart to reconcile to either.

**The only fixed-inventory single connection change actually available is
`rewire.reassign_coil`** (move an existing coil's plant connection to a
different, already-existing pump) -- no object is created or destroyed,
so no clone-identity reconciliation is even needed for this specific
intervention family (confirmed: `reconcile_realized_topology` sees
identical node sets before/after a `reassign_coil` call). This is the ONLY
rewire_kind this module supports for now; see `OUT_OF_SCOPE_REWIRE_KINDS`
for the others and why each is rejected, explicitly, rather than silently
attempted.

**`reassign_coil` itself is only exercisable on ONE of the 10 archetypes.**
Surveyed all 10 (`scripts/generate_causal_batch.py`'s survey step, and see
this package's CHANGELOG.md for the raw output): a plant loop needs both a
pump AND coils on its demand side to be a `reassign_coil` source or target,
and `reassign_coil` needs at least *two* such loops with *different* pumps
in the same building. Only `sys07_vav_reheat` has two (a hot-water loop
with 11 heating coils, a chilled-water loop with 1 cooling coil); every
other archetype has zero or exactly one such loop. This is a real,
confirmed limitation of the current building set, not an oversight in this
module -- a batch generated here is necessarily single-building until
`physics_pipeline` gains either more archetypes with a second same- or
different-medium pump, or a terminal-side intervention that doesn't
destroy equipment (neither exists today).

Given this, this module does NOT attempt zone-side interventions at all.
Extending coverage requires either widening `physics_pipeline`'s building
set (out of scope: no source changes to either sibling package) or
designing a genuinely non-destructive terminal-side primitive, which does
not exist in `rewire.py` today.
"""

from __future__ import annotations

import itertools
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

from .contracts import (
    CorruptionKind,
    DiscrepancyEvent,
    InterventionTruth,
    OperatingContext,
    SimulatedObservables,
    ZoneObservableSeries,
)

PHYSICS_PIPELINE_SRC = Path(__file__).resolve().parents[3] / "physics_pipeline" / "src"

# Season-matched output window, matching physics_pipeline's own convention
# (`pipeline._coil_variable_and_window`): a heating coil barely runs at all
# outside heating season, which would make a genuinely dead coil
# indistinguishable from a normally-quiet one.
_HEATING_WINDOW = (1, 1, 1, 3)
_COOLING_WINDOW = (7, 1, 7, 3)


def import_physics_pipeline():
    """Import `physics_pipeline` via the same `sys.path` shim
    `physics_pipeline/pipeline.py` uses to import `hvac_benchmark` -- that
    package has no installable package metadata of its own (no
    `pyproject.toml` at `physics_pipeline/`), so this mirrors its own
    pattern rather than inventing a different one. Only ever called from
    this opt-in module (`pip install symptom-pipeline[physics]`); deployed
    prediction code (`features.py`, `models.py`, `calibration.py`,
    `benchmark_adapter.py`) must never import this module.
    """
    if str(PHYSICS_PIPELINE_SRC) not in sys.path:
        sys.path.insert(0, str(PHYSICS_PIPELINE_SRC))
    import physics_pipeline  # noqa: F401

    return physics_pipeline


class UnsupportedInterventionError(Exception):
    """Raised for any `rewire_kind` this module deliberately does not
    attempt. Carries the specific reason so a caller (or this module's own
    tests) can distinguish "genuinely out of v1 scope" from "just not
    implemented yet" -- see `OUT_OF_SCOPE_REWIRE_KINDS`.
    """

    def __init__(self, rewire_kind: str, reason: str):
        self.rewire_kind = rewire_kind
        self.reason = reason
        super().__init__(f"{rewire_kind!r} is not a supported v1 single intervention: {reason}")


class IntendedChangeMismatchError(Exception):
    """Raised when the realized topology's diff from the documented
    topology does not match what the intervention was supposed to produce.
    A hard failure, per the design doc: "Verify that the realized
    relationship differences match the intended intervention -- if they
    don't, that's a hard failure for this example, not a warning to log
    and continue past."
    """

    def __init__(self, expected: frozenset, actual: frozenset, warnings: list[str]):
        self.expected = expected
        self.actual = actual
        self.warnings = warnings
        super().__init__(
            f"realized topology diff {sorted(actual)} does not match the intended change "
            f"{sorted(expected)} (reconciliation warnings: {warnings})"
        )


def verify_intended_change(expected: frozenset, actual: frozenset, warnings: list[str]) -> None:
    """Step 5's hard-failure gate, pulled out as its own pure function so it
    can be unit-tested directly against a deliberately-wrong `expected`
    without needing to run OpenStudio at all (see
    `tests/test_intended_change_verification.py`, which does exactly that
    against the real discordant-pair output from an actual `reassign_coil`
    run). No-op if `actual == expected`; raises
    `IntendedChangeMismatchError` otherwise. Per the design doc: "if they
    don't [match], that's a hard failure for this example, not a warning to
    log and continue past."
    """
    if actual != expected:
        raise IntendedChangeMismatchError(expected, actual, warnings)


_EQUIPMENT_DESTROYED_REASON = (
    "destroys real equipment as a side effect on every one of the 10 archetypes (every zone is "
    "already served, confirmed empirically), which is an inventory change beyond the one intended "
    "connection edit -- out of v1's fixed-inventory scope. See this module's docstring."
)

OUT_OF_SCOPE_REWIRE_KINDS: dict[str, str] = {
    "remove_zone_service": "deletes the terminal outright -- literally 'equipment removed entirely', out of v1's fixed-inventory scope",
    "remove_coil_service": "deletes the coil outright -- literally 'equipment removed entirely', out of v1's fixed-inventory scope",
    "reassign_terminal": _EQUIPMENT_DESTROYED_REASON,
    "add_extra_service": _EQUIPMENT_DESTROYED_REASON,
    "set_ahu_direct_service": _EQUIPMENT_DESTROYED_REASON,
    "clone_terminal_for_zone": (
        "cloning alone is not a complete connection change, and every rewire.py primitive that "
        "actually relocates a cloned terminal (reassign_terminal, add_extra_service) destroys "
        "another zone's real terminal as a side effect on every archetype in this building set -- "
        "no terminal-side intervention currently satisfies v1's fixed-inventory constraint"
    ),
}

SUPPORTED_REWIRE_KINDS: frozenset[str] = frozenset({"reassign_coil"})


@dataclass(frozen=True)
class SingleInterventionSpec:
    """One supported v1 intervention: a single rewiring operation whose
    equipment identities and relationship change can be reconciled
    reliably. Cases that remove equipment entirely or introduce
    unresolvable identity changes are explicitly out of v1 scope (design
    doc, "Causal training examples") -- see `OUT_OF_SCOPE_REWIRE_KINDS`.

    `coil_id`/`target_pump_id` are OpenStudio handle strings (e.g.
    `"{uuid}"`, exactly as `physics_pipeline.extract` node ids are
    formatted); required when `rewire_kind == "reassign_coil"`. `zone_id`
    is kept for interface stability with zone-targeted kinds (all
    currently rejected via `OUT_OF_SCOPE_REWIRE_KINDS`) and is unused by
    the one supported kind.
    """

    building_id: str
    zone_id: str
    rewire_kind: str
    coil_id: str | None = None
    target_pump_id: str | None = None
    event_id: str | None = None


# --------------------------------------------------------------------------
# Topology identity reconciliation
# --------------------------------------------------------------------------


def _node_signature(graph, node: str) -> tuple:
    """A structural fingerprint for a node: its own brick_type plus the
    multiset of (relation, neighbor brick_type) pairs it participates in,
    in both directions. Used only for nodes that have NO identical-handle
    counterpart in the other graph (a destroyed-and-recreated object, e.g.
    a clone) -- nodes with a shared handle need no signature matching at
    all, since their identity is already certain.

    Deliberately excludes the node's own `location` attribute:
    `physics_pipeline.extract`'s convention is that a terminal's location
    is wherever it CURRENTLY sits ("the terminal physically sits with the
    zone it serves"), which is exactly what changes for equipment that
    physically relocated -- requiring it to match would make a genuinely
    relocated object unreconcilable by construction, the opposite of what
    this function exists to do. Ambiguity from dropping location (two
    same-typed candidates on both sides of the same diff) is caught
    separately, below, and reported rather than guessed.
    """
    brick_type = graph.nodes[node].get("brick_type")
    out_sig = tuple(sorted((d.get("relation"), graph.nodes[t].get("brick_type")) for _, t, d in graph.out_edges(node, data=True)))
    in_sig = tuple(sorted((d.get("relation"), graph.nodes[s].get("brick_type")) for s, _, d in graph.in_edges(node, data=True)))
    return (brick_type, out_sig, in_sig)


def reconcile_realized_topology(documented_nx_graph, realized_nx_graph) -> tuple[frozenset[tuple[str, str]], list[str]]:
    """Diffs two extracted topologies (as raw `networkx.MultiDiGraph`
    objects, exactly as `physics_pipeline.extract.extract_topology`
    returns them -- node ids are OpenStudio handle strings, edges carry a
    `relation` attribute) and reconciles node identity across the two.

    Two identity-resolution tiers, in order:

    1. **Identical handle** (the common case whenever nothing was cloned or
       destroyed -- confirmed to be ALL nodes for a `reassign_coil`
       intervention, since that primitive creates and destroys nothing).
    2. **Structural signature match** for any node left over after (1): if
       exactly one node on the other side shares the same (brick_type,
       neighbor relation/type multiset), they're reconciled as
       the same logical equipment (a destroyed-and-recreated clone).
       Ambiguous (2+ candidates) or absent matches are left unresolved and
       reported as warnings, never guessed.

    Returns `(discordant_pairs, warnings)`: `discordant_pairs` is the
    symmetric difference of `feeds` edges between the two graphs, expressed
    in DOCUMENTED node-id space (realized-only nodes that couldn't be
    reconciled keep their own realized id, since there is no documented id
    to translate them to). `warnings` explains every reconciliation
    decision, including "no counterpart found" cases -- read these before
    trusting a discordant-pairs result that includes an unreconciled node.
    """
    doc_nodes = set(documented_nx_graph.nodes())
    real_nodes = set(realized_nx_graph.nodes())

    identical = doc_nodes & real_nodes
    doc_only = doc_nodes - real_nodes
    real_only = real_nodes - doc_nodes

    warnings: list[str] = []
    # documented_id -> realized_id, seeded with the trivial identical-handle case
    doc_to_real: dict[str, str] = {n: n for n in identical}

    doc_sigs = {n: _node_signature(documented_nx_graph, n) for n in doc_only}
    real_sigs = {n: _node_signature(realized_nx_graph, n) for n in real_only}

    # Group by signature on BOTH sides before matching anything -- matching
    # greedily while iterating a Python `set` (unordered, hash-randomized
    # across runs) would let an accidental iteration order "win" an
    # otherwise-ambiguous match, which is exactly the silent-guess failure
    # mode this function exists to avoid. A match is only ever committed
    # when a signature is a mutual bijection: exactly one documented node
    # and exactly one realized node share it. Two documented nodes that are
    # structurally indistinguishable (e.g. two same-typed sibling terminals
    # with no other distinguishing signal) are correctly reported as
    # ambiguous for BOTH, never resolved by whichever happens to be
    # considered first.
    doc_groups: dict[tuple, list[str]] = {}
    for n, sig in doc_sigs.items():
        doc_groups.setdefault(sig, []).append(n)
    real_groups: dict[tuple, list[str]] = {}
    for n, sig in real_sigs.items():
        real_groups.setdefault(sig, []).append(n)

    matched_real: set[str] = set()
    for sig, doc_group in sorted(doc_groups.items(), key=lambda kv: sorted(kv[1])):
        real_group = real_groups.get(sig, [])
        if len(doc_group) == 1 and len(real_group) == 1:
            doc_node, real_node = doc_group[0], real_group[0]
            doc_to_real[doc_node] = real_node
            matched_real.add(real_node)
            warnings.append(
                f"reconciled destroyed-and-recreated node {doc_node!r} -> {real_node!r} "
                "by exact structural signature match (brick_type + neighbor relations)"
            )
        elif not real_group:
            for doc_node in sorted(doc_group):
                warnings.append(
                    f"documented node {doc_node!r} has no counterpart in the realized graph -- this "
                    "means equipment was removed entirely, which is out of v1's fixed-inventory scope "
                    "if it occurs for a nominally-supported intervention"
                )
        else:
            for doc_node in sorted(doc_group):
                warnings.append(
                    f"documented node {doc_node!r} has {len(real_group)} ambiguous structural matches "
                    f"in the realized graph {sorted(real_group)!r} (shared by {len(doc_group)} equally-"
                    "structured documented nodes) -- left unresolved, not guessed"
                )

    unresolved_real = real_only - matched_real
    for r in sorted(unresolved_real):
        warnings.append(f"realized node {r!r} has no documented counterpart -- treated as newly introduced equipment")

    def feeds_edges(graph) -> set[tuple[str, str]]:
        return {(s, t) for s, t, d in graph.edges(data=True) if d.get("relation") == "feeds"}

    # The documented graph's own edges are ALREADY in documented-id space --
    # they must never be relabeled through doc_to_real (a doc-id -> real-id
    # map would corrupt them into realized ids, comparing the wrong space
    # against itself). Only the realized graph's edges need translating,
    # via the INVERSE map (real-id -> doc-id), so both sides end up
    # expressed in the same (documented) id space before comparing.
    real_to_doc = {real_id: doc_id for doc_id, real_id in doc_to_real.items()}
    doc_feeds = feeds_edges(documented_nx_graph)
    real_feeds = {(real_to_doc.get(s, s), real_to_doc.get(t, t)) for s, t in feeds_edges(realized_nx_graph)}

    discordant = frozenset(doc_feeds.symmetric_difference(real_feeds))
    return discordant, warnings


# --------------------------------------------------------------------------
# Single-intervention causal experiment
# --------------------------------------------------------------------------


def _query_series(sql_path: Path, variable: str, key_upper: str) -> list[float]:
    con = sqlite3.connect(sql_path)
    cur = con.cursor()
    cur.execute(
        "SELECT rd.Value FROM ReportData rd "
        "JOIN ReportDataDictionary rdd ON rd.ReportDataDictionaryIndex = rdd.ReportDataDictionaryIndex "
        "JOIN Time t ON rd.TimeIndex = t.TimeIndex "
        "WHERE rdd.Name=? AND rdd.KeyValue=? AND t.EnvironmentPeriodIndex=("
        "  SELECT MAX(EnvironmentPeriodIndex) FROM EnvironmentPeriods)"
        "ORDER BY rd.TimeIndex",
        (variable, key_upper),
    )
    rows = [r[0] for r in cur.fetchall()]
    con.close()
    return rows


def _mean(series: list[float]) -> float | None:
    return sum(series) / len(series) if series else None


def run_single_intervention_experiment(
    spec: SingleInterventionSpec,
    out_dir: Path | None = None,
    baseline_cache: dict | None = None,
) -> tuple[InterventionTruth, SimulatedObservables, DiscrepancyEvent]:
    """The causal-experiment sequence from the design doc, implemented for
    the one supported intervention family (`rewire_kind="reassign_coil"`);
    see this module's docstring for why every other `rewire_kind` is
    rejected via `UnsupportedInterventionError` instead.

    1. Load a baseline building and extract its documented topology.
    2. Apply `reassign_coil` to a fresh copy of the model.
    3. Re-extract the realized topology.
    4. Reconcile identity (`reconcile_realized_topology`) and verify the
       realized diff is EXACTLY the intended (old_pump, coil) removal and
       (new_pump, coil) addition -- any other diff is a hard failure
       (`IntendedChangeMismatchError`), not a warning.
    5. Run baseline and changed models over a season-matched window
       (heating window for a heating coil, cooling window for a cooling
       coil, matching `physics_pipeline.pipeline._coil_variable_and_window`).
    6-7. Measure `Zone Mean Air Temperature` for EVERY zone in the
       documented graph, not just the coil's own zone -- remote/shared-
       system effects are part of the point, even though for a single
       zone-embedded reheat coil on this building's topology no material
       remote effect is actually expected (each zone has its own dedicated
       terminal; see the batch report for whether one was observed anyway).
    8. Label the discordant (pump, coil) pairs as one MISATTRIBUTED
       `DiscrepancyEvent` (the coil's true parent pump replaced by a wrong
       one) -- not "fabrication"/"removal" naming mechanically copied from
       `hvac_benchmark`, chosen because it is the accurate description of
       this specific edge change under the design doc's reversed roles.

    `baseline_cache`, if given, is a dict this function will read/write
    baseline `SimulationResult`s into, keyed by `(building_id, window)`, so
    a batch of several interventions on the same building only pays for one
    baseline EnergyPlus run -- mirrors `physics_pipeline.pipeline`'s own
    `baseline_cache` pattern. `out_dir` defaults to this package's
    `output/` directory.
    """
    if spec.rewire_kind in OUT_OF_SCOPE_REWIRE_KINDS:
        raise UnsupportedInterventionError(spec.rewire_kind, OUT_OF_SCOPE_REWIRE_KINDS[spec.rewire_kind])
    if spec.rewire_kind not in SUPPORTED_REWIRE_KINDS:
        raise UnsupportedInterventionError(spec.rewire_kind, "not a recognized rewire_kind for v1")
    if spec.coil_id is None or spec.target_pump_id is None:
        raise ValueError("reassign_coil requires both coil_id and target_pump_id")

    import_physics_pipeline()
    import openstudio
    from physics_pipeline import rewire as rewire_mod
    from physics_pipeline import simulate as sim_mod
    from physics_pipeline.buildings import ENERGYPLUS_BIN, ENERGYPLUS_IDD, WEATHER_FILE, get_building
    from physics_pipeline.extract import extract_topology

    building = get_building(spec.building_id)
    translator = openstudio.osversion.VersionTranslator()
    out_dir = out_dir or (Path(__file__).resolve().parents[2] / "output")
    out_dir.mkdir(parents=True, exist_ok=True)
    baseline_cache = baseline_cache if baseline_cache is not None else {}

    def load():
        return translator.loadModel(openstudio.path(str(building.osm_path))).get()

    # --- 1. baseline (documented) ---
    m_doc = load()
    _, _, doc_nx, doc_edges, _ = extract_topology(m_doc, building.building_id, "documented")

    original_pump_candidates = [s for s, t in doc_edges["feeds"] if t == spec.coil_id]
    if len(original_pump_candidates) != 1:
        raise ValueError(
            f"expected exactly one documented pump feeding coil {spec.coil_id!r}, found {original_pump_candidates!r}"
        )
    original_pump_id = original_pump_candidates[0]
    target_type = doc_nx.nodes[spec.coil_id].get("brick_type")

    # --- 2. apply ONE intervention to a fresh copy ---
    m_changed = load()
    coil_obj = m_changed.getModelObject(openstudio.toUUID(spec.coil_id))
    if not coil_obj.is_initialized():
        raise ValueError(f"coil {spec.coil_id!r} not found in {spec.building_id}")
    coil = coil_obj.get().to_CoilHeatingWater()
    if not coil.is_initialized():
        coil = coil_obj.get().to_CoilCoolingWater()
    if not coil.is_initialized():
        raise ValueError(f"{spec.coil_id!r} is not a hydronic coil (Coil:Heating:Water / Coil:Cooling:Water)")
    coil = coil.get()

    pump_obj = m_changed.getModelObject(openstudio.toUUID(spec.target_pump_id))
    if not pump_obj.is_initialized():
        raise ValueError(f"pump {spec.target_pump_id!r} not found in {spec.building_id}")
    pump = pump_obj.get().to_PumpVariableSpeed()
    if not pump.is_initialized():
        pump = pump_obj.get().to_PumpConstantSpeed()
    if not pump.is_initialized():
        raise ValueError(f"{spec.target_pump_id!r} is not a pump")
    pump = pump.get()

    if not rewire_mod.reassign_coil(m_changed, coil, pump):
        raise RuntimeError(f"reassign_coil failed for coil={spec.coil_id!r} -> pump={spec.target_pump_id!r}")

    # --- 3. re-extract realized topology ---
    _, _, real_nx, real_edges, _ = extract_topology(m_changed, building.building_id, "realized")

    # --- 4. reconcile + hard-verify the intended change ---
    discordant_pairs, warnings = reconcile_realized_topology(doc_nx, real_nx)
    expected = frozenset({(original_pump_id, spec.coil_id), (spec.target_pump_id, spec.coil_id)})
    verify_intended_change(expected, discordant_pairs, warnings)

    # --- 5. simulate baseline + changed under a matched, season-appropriate window ---
    window = _HEATING_WINDOW if target_type == "Heating_Coil" else _COOLING_WINDOW
    variable = "Heating Coil Heating Rate" if target_type == "Heating_Coil" else "Cooling Coil Total Cooling Rate"
    bm, bd, em, ed = window

    cache_key = (building.building_id, window)
    if cache_key not in baseline_cache:
        sim_mod.set_scoped_output(m_doc, bm, bd, em, ed)
        base_ws = sim_mod.forward_translate(m_doc)
        base_idf = out_dir / f"baseline_{building.building_id}_{bm}{bd}.idf"
        sim_mod.save_workspace_as_idf(base_ws, base_idf)
        baseline_cache[cache_key] = sim_mod.run_energyplus(
            base_idf, WEATHER_FILE, out_dir / f"baseline_run_{building.building_id}_{bm}{bd}",
            ENERGYPLUS_BIN, ENERGYPLUS_IDD,
        )
    base_result = baseline_cache[cache_key]

    event_tag = spec.event_id or f"{spec.building_id}_{spec.coil_id.strip('{}')}_{spec.target_pump_id.strip('{}')}"
    sim_mod.set_scoped_output(m_changed, bm, bd, em, ed)
    changed_ws = sim_mod.forward_translate(m_changed)
    changed_idf = out_dir / f"changed_{event_tag}.idf"
    sim_mod.save_workspace_as_idf(changed_ws, changed_idf)
    changed_result = sim_mod.run_energyplus(
        changed_idf, WEATHER_FILE, out_dir / f"changed_run_{event_tag}", ENERGYPLUS_BIN, ENERGYPLUS_IDD,
    )

    if not (base_result.success and changed_result.success):
        raise RuntimeError(
            f"simulation did not succeed for event {event_tag!r}: "
            f"baseline success={base_result.success} (severe={base_result.severe_error_count}), "
            f"changed success={changed_result.success} (severe={changed_result.severe_error_count})"
        )

    coil_name = coil.name().get()
    base_coil_series = _query_series(base_result.output_dir / "eplusout.sql", variable, coil_name.upper())
    changed_coil_series = _query_series(changed_result.output_dir / "eplusout.sql", variable, coil_name.upper())

    # --- 6-7. measure EVERY zone, not just the intervention's own zone ---
    zone_nodes = [n for n in doc_nx.nodes() if doc_nx.nodes[n].get("brick_type") == "HVAC_Zone"]
    per_node: list[ZoneObservableSeries] = []
    for zone_id in zone_nodes:
        zone_name = doc_nx.nodes[zone_id].get("name")
        if not zone_name:
            continue
        base_temp = _query_series(base_result.output_dir / "eplusout.sql", "Zone Mean Air Temperature", zone_name.upper())
        changed_temp = _query_series(changed_result.output_dir / "eplusout.sql", "Zone Mean Air Temperature", zone_name.upper())
        if not base_temp or not changed_temp:
            continue
        per_node.append(
            ZoneObservableSeries(
                node_id=zone_id,
                baseline_mean_temp_c=_mean(base_temp),
                changed_mean_temp_c=_mean(changed_temp),
                baseline_setpoint_c=None,
                changed_setpoint_c=None,
                baseline_supply_air_temp_c=None,
                changed_supply_air_temp_c=None,
                baseline_airflow_frac_of_design=None,
                changed_airflow_frac_of_design=None,
            )
        )

    demand_mode = OperatingContext.HEATING if target_type == "Heating_Coil" else OperatingContext.COOLING
    observables = SimulatedObservables(
        event_id=event_tag,
        per_node=tuple(per_node),
        demand_mode=demand_mode,
        outside_air_temp_unusual=False,
        quality_ok=True,
        quality_notes=(
            f"coil {variable} baseline_mean={_mean(base_coil_series)} changed_mean={_mean(changed_coil_series)}; "
            f"reconciliation warnings: {warnings}"
        ),
    )

    truth = InterventionTruth(
        event_id=event_tag,
        building_id=spec.building_id,
        changed_connection=(spec.target_pump_id, spec.coil_id, "feeds"),
        corruption_kind=CorruptionKind.MISATTRIBUTED,
        operational_fault=None,
        fault_magnitude=None,
        fault_onset_hour=None,
        baseline_run_id=str(base_result.output_dir),
        changed_run_id=str(changed_result.output_dir),
    )

    event = DiscrepancyEvent(
        event_id=event_tag,
        corruption_kind=CorruptionKind.MISATTRIBUTED,
        discordant_pairs=tuple(sorted(expected)),
        target_id=spec.coil_id,
    )

    return truth, observables, event


def discover_reassign_coil_specs(building_id: str) -> list[SingleInterventionSpec]:
    """Enumerates every `reassign_coil` intervention actually available on
    `building_id`: for each hydronic plant loop with both a pump and coils,
    every coil paired with every OTHER such loop's pump. Returns an empty
    list for a building with fewer than two qualifying loops (confirmed:
    9 of the 10 archetypes) -- callers should check for an empty result
    rather than assume every building has something to offer.
    """
    import_physics_pipeline()
    import openstudio
    from physics_pipeline.buildings import get_building

    building = get_building(building_id)
    translator = openstudio.osversion.VersionTranslator()
    model = translator.loadModel(openstudio.path(str(building.osm_path))).get()

    loops = []
    for plant in model.getPlantLoops():
        pumps = [c for c in plant.supplyComponents() if "Pump" in c.iddObjectType().valueName()]
        coils = [c for c in plant.demandComponents() if "Coil" in c.iddObjectType().valueName()]
        hydronic_coils = [c for c in coils if c.iddObjectType().valueName() in ("OS_Coil_Heating_Water", "OS_Coil_Cooling_Water")]
        if pumps and hydronic_coils:
            loops.append((str(pumps[0].handle()), hydronic_coils))

    specs: list[SingleInterventionSpec] = []
    for (pump_a, coils_a), (pump_b, _coils_b) in itertools.permutations(loops, 2):
        for coil in coils_a:
            specs.append(
                SingleInterventionSpec(
                    building_id=building_id,
                    zone_id="",
                    rewire_kind="reassign_coil",
                    coil_id=str(coil.handle()),
                    target_pump_id=pump_b,
                    event_id=f"{building_id}_{coil.handle()}_to_{pump_b}".translate(str.maketrans("", "", "{}")),
                )
            )
    return specs
