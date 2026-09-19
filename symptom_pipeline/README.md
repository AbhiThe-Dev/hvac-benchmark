# symptom_pipeline

Symptom-informed ranking of HVAC topology discrepancies: given a known
symptom report and a documented topology, rank plausible connection
discrepancies (missing, fabricated, or misattributed connections) and
supply an initial suspect region to `hvac_benchmark`'s existing Bayesian
troubleshooting machinery.

A **separate sibling package** to `hvac_benchmark` (`../src/hvac_benchmark`)
and `physics_pipeline` (`../physics_pipeline`). Neither is modified by
anything here. This package imports `hvac_benchmark`'s policies, priors,
Bayesian update functions, and observation simulator unchanged, and
(optionally, only for future data-generation work) imports
`physics_pipeline`'s extraction/rewiring/fault primitives via the same
`sys.path` shim `physics_pipeline/pipeline.py` uses to import
`hvac_benchmark` -- neither package has been changed to accommodate this
one.

## Status (this version)

This is a research prototype, not a validated diagnostic tool, and makes no
claim of real technician effectiveness. See `CHANGELOG.md` for what changed
and the concrete gaps found while building this. Summary by module:

| Module | Status |
|---|---|
| `contracts.py` | Implemented: the shared vocabulary for every other module. |
| `questions.py` | Implemented: the fixed v1 questionnaire (8 questions), validated against `contracts.StructuredAnswers`. |
| `ingestion.py` | Implemented: Brick TTL and equipment/connection-table ingestion into `DocumentedGraph` + `hvac_benchmark.graph.networkx_build.TopologyGraph`, with source-hash provenance and structural validation. |
| `report_translation.py` | Implemented: observable-to-answer rules and reporting-error variant generation. Thresholds are placeholders pending HVAC-practitioner review -- see the module docstring. |
| `features.py` | Implemented: whole-graph candidate-edge feature extraction (no hop cutoff), never reading the actual graph or fault identity. |
| `models.py` | Implemented: GBM (recommended v1) and logistic-baseline training harnesses over `features.py` output. No trained artifact ships with this package -- there is no labeled data yet (see `simulation.py`). |
| `calibration.py` | Implemented: isotonic calibration and suspect-prefix selection (95% mean event coverage target, frozen before test evaluation). |
| `benchmark_adapter.py` | Implemented: sibling troubleshooting runner with `none`/`oracle`/`learned` symptom sources. **Oracle-parity is a required, tested acceptance check** -- see below. `symptom_source="learned"` has now been exercised once end-to-end (`scripts/run_plumbing_check.py`, see `output/plumbing_check_summary.json`) -- an integration round-trip, not a model-quality result. |
| `evaluation.py` | Implemented: ranking/report metrics (recall@k, event coverage@k, MRR, Brier, reliability) and paired downstream comparison across symptom sources and policies. |
| `simulation.py` | **Implemented for one intervention family**: `reconcile_realized_topology` (identity reconciliation across independent extractions, verified against real OpenStudio output) and `run_single_intervention_experiment` for `rewire_kind="reassign_coil"`, the only fixed-inventory single connection change confirmed available in the current `physics_pipeline` object model + building set. Every other `rewire_kind` is explicitly rejected (`UnsupportedInterventionError`), not silently attempted -- see "Causal data generation" below and the module's own docstring for exactly why. |
| `datasets.py` | Implemented and now exercised against real generated records (`scripts/generate_causal_batch.py`) -- grouped-split and no-leakage invariants hold, though see the split-degeneracy caveat below. |

## Oracle-parity guarantee

`benchmark_adapter.run_symptom_troubleshooting_trial` reimplements
`hvac_benchmark.experiment.troubleshooting_runner.run_troubleshooting_trial`
side by side (not via monkey-patching) because that runner has no external
symptom-source hook. `tests/test_oracle_parity.py` asserts, across every
reference policy, three noise levels, and three seeds, that:

- `symptom_source="none"` matches `symptom_mode=False` bit-for-bit, and
- `symptom_source="oracle"` matches `symptom_mode=True` bit-for-bit.

Only `symptom_source="learned"` is new behavior. **Do not use `"learned"`
for any real experiment before this test passes on your checkout.**

## Causal data generation

`simulation.run_single_intervention_experiment` generates one causal
training example: load a baseline building (the "blueprint"), apply
`rewire.reassign_coil` to a fresh copy (the "actual system"), reconcile
topology identity between the two extractions, hard-verify the realized
diff matches the intended change, simulate both under a matched window,
and measure the effect across every zone.

**Why only `reassign_coil`:** every other `physics_pipeline.rewire`
primitive destroys a real piece of equipment as a side effect on every one
of the 10 archetypes (confirmed empirically -- every zone in every
archetype already has its own terminal), which is an inventory change
beyond the one intended connection edit and out of v1's fixed-inventory
scope. `reassign_coil` moves an existing coil's plant connection between
two already-existing pumps -- nothing is created or destroyed, so identity
reconciliation is (for this specific intervention) trivial by handle
equality; the harder destroyed-and-recreated-clone case is implemented and
tested, but only against synthetic graphs (`tests/test_reconciliation.py`),
since no available `physics_pipeline` intervention exercises it for real.

**Why only `sys07_vav_reheat`:** a survey of all 10 archetypes (run while
building this) found only one building with two hydronic plant loops on
different pumps -- the structural precondition `reassign_coil` needs.
Every other archetype has zero or exactly one qualifying loop. A batch
generated today is therefore necessarily single-building; `group_split`
still runs correctly on it, but produces one degenerate bucket, not a
genuine held-out partition -- reported explicitly in
`output/causal_batch_v1_summary.json`, not hidden.

**Required acceptance checks, run and inspected, not just asserted** (see
`tests/test_simulation_physics.py`, `tests/test_intended_change_verification.py`):
the step-5 verification fires correctly on a deliberately wrong case
(`test_intended_change_verification.py`, using the real discordant-pair
output below), and the reversal sanity check -- re-running the same case
with the intervention NOT applied -- shows the effect disappearing:

```
--- reversal sanity check (Thermal Zone 7 mean air temp, degC) ---
baseline (documented, no intervention):        23.079
changed (reassign_coil applied):                18.468  (deviation -4.611)
reversal (independent reload, NOT applied):     23.079  (deviation +0.000)
```

**Generate a batch:**

```bash
uv sync --extra physics       # installs openstudio==3.11.0
uv run pytest -m physics      # required acceptance checks, real EnergyPlus runs (~15-30s)
uv run python scripts/generate_causal_batch.py
```

The last real run of that script (6 candidate coil reassignments
attempted): **4 succeeded** with large, clearly measurable zone-temperature
effects (-1.9C to -8.7C), **2 failed with genuine EnergyPlus severe errors**
(one direction -- moving the central chilled-water coil onto the hot-water
pump -- and one specific heating coil) and were excluded with their failure
recorded, not silently dropped, per the design doc's "retain failure
records and denominators." See `output/causal_batch_v1_summary.json` for
the full per-event breakdown.

## Setup

```bash
cd symptom_pipeline
uv sync
uv run pytest
```

`hvac-benchmark` is pulled in as an editable path dependency on `..` (the
repo root), pinned to the exact source-hash-verifiable version recorded in
`CHANGELOG.md` -- not just floor-bounded -- because oracle parity depends
on its exact internal behavior. Re-run `tests/test_oracle_parity.py`
whenever that pin moves.

OpenStudio and `physics_pipeline` are **not** dependencies of this package
by default -- `pip install symptom-pipeline[physics]` installs
`openstudio==3.11.0` (pinned to match `physics_pipeline/.venv`'s own
version, since that package has no packaging metadata of its own to pin
against) for the data-generation tests and scripts only. Deployed
prediction (`features.py`/`models.py`/`calibration.py`/
`benchmark_adapter.py`) never imports `simulation.py` and never needs it.

## Scope (v1)

- Structured blueprint input: Brick graphs or equipment/connection tables,
  with reviewed manual mapping from drawings.
- Topology discrepancies whose physical consequences explain the reported
  symptom: missing, fabricated, or misattributed connections.
- One model invocation before testing; existing `hvac_benchmark` policies
  perform all subsequent test selection and Bayesian updates unchanged.
- The existing `hvac_benchmark` oracle (`symptom_flagged_nodes`) remains a
  comparison source, not a training target.
- Causal data generation: single connection changes only, and only via
  `reassign_coil` (see "Causal data generation" above) -- terminal-side
  interventions remain out of scope because every one currently destroys
  real equipment as a side effect.

Out of scope for v1: a trained/shipped model (no labeled data at meaningful
scale yet), multi-intervention or equipment-removal cases, operational-fault
confounder generation, a second building lineage for a genuine held-out
split, and any claim about real technician reporting behavior.
