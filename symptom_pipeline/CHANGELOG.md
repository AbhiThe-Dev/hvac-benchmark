# Changelog

## 0.2.3 -- real fix: VAV reheat coil -> terminal `hasPart` edge in `physics_pipeline`

First change to `physics_pipeline` by this project. **Cause confirmed:**
`extract_topology` walked each AirLoop's demand side and emitted
`AHU -feeds-> terminal -feeds-> zone`, plus AHU-owned coils/fans as
`hasPart`, but never followed `AirTerminal:SingleDuct:VAV:Reheat` to its
`reheatCoil()`. The coil only appeared later, from the plant-loop walk, as
the target of `pump -feeds-> coil`. Not a missing Brick relation or type
mapping: `_brick_equipment_type` already handled it.

**Precedent, not invention:** AHU coils/fans -> AHU and (uncommitted,
pre-existing work) PTAC/PTHP coils -> unit are both `part -hasPart->
whole`. The new edge is `coil -hasPart-> VAV terminal`, same direction.
`physics_pipeline`'s existing uncommitted changes (`extract.py` PTAC/PTHP
walk and `add_zone_node` refactor; `buildings.py`, `faults.py`, `rewire.py`)
were read first: none touches reheat-coil extraction (`rewire.py` only
handles reheat coils on the corruption side), so this adds to `extract.py`
without overlapping. Those uncommitted changes remain uncommitted; this
edit is in the same working tree.

**Change:** 9 lines in `extract.py`, scoped to
`OS_AirTerminal_SingleDuct_VAV_Reheat` only.

**Regression checks (all 10 buildings, before/after diff of node, feeds and
hasPart counts, node types and candidate count):** the only differences are
`sys07_vav_reheat` and `sys05_vav_reheat_dx`, each +10 `hasPart` edges.
Node counts, `feeds` counts and candidate universes are all unchanged
(sys07: 94, as I had predicted it would probably change -- it did not,
because the coils were already nodes and `hasPart` is not a `feeds`
candidate tier). `physics_pipeline` has no pytest suite (`tests/` is
empty); its only check is `scripts/test_extract.py`, a smoke script, which
still reports 100% feeds-candidate coverage (sys07 32/32). Its
`results_physics/` was NOT regenerated and may show old `hasPart` counts for
sys05/sys07.

**Downstream re-verification:**
- `generate_causal_batch.py`: output summary byte-identical to before
  (universe 94, 4 succeeded / 2 failed, same deviations and pairs).
- `symptom_pipeline` `pytest -m "not slow"`: 191 passed; `-m physics`:
  3 passed. Root `hvac_benchmark` suite: 247 passed. No `hvac_benchmark`
  fixture or recorded result references `sys07`/`sys05` (its results are
  real LBNL buildings), so `uv run hvac-benchmark` was not re-run.
- `run_plumbing_check.py` (sanity event): feature tie groups for the true
  pairs went from 10 to 1 (each true pair is now uniquely identified);
  distinct feature vectors 19 -> 21. True pairs now rank #1 and #2 (was #3
  and #13) and are the only 2 candidates in the top score tier. Repeated
  with true leave-one-event-out models (never trained on the held-out
  event): in all 4 folds the true pairs are exactly the top tier of size 2.
  Leave-one-event-out `select_suspect_prefix`: k 14 -> 2 (universe fraction
  0.149 -> 0.021).
- GBM `feature_importances_`: `target_distance_from_report` 0.327,
  `min_endpoint_distance_from_report` 0.315, `target_type=Heating_Coil`
  0.139, `source_type=Pump` 0.107, `n_indistinguishable_siblings` 0.065,
  `shares_location_with_report` 0.047; everything else 0 (including
  `is_claimed`). So the new signal is used, mainly through distance.
- "Raw scores collapse to 2 levels" **persists** (0.99996 vs 1e-6), but its
  meaning changed: the top level is now exactly the 2 true pairs, i.e. a
  saturated near-0/1 classifier on separable data, not missing signal.
  No hyperparameters were touched.

**Why this is not evidence of generalization:** in all 4 events the
reported zone (chosen as the max-deviation zone) is exactly the zone served
by the moved coil's own VAV, so "coil whose VAV feeds the reported zone"
(coil at distance 2) separates the true pairs by construction. A report
naming a neighboring zone, or a symptom that appears elsewhere, is not
covered by this data. One building, 4 events, still.

**Scope note for future work (measured, not fixed):** the same
"terminal coil has no ownership edge" gap exists for exactly the VAV:Reheat
buildings, sys05 and sys07 (10 coils each, now fixed). `sys06`/`sys08`
(ParallelPIU with electric reheat) do not put their reheat coils into the
graph at all; `AirTerminal:ConstantVolume:Reheat` and `SeriesPIU:Reheat`
are mapped as terminals but their coils are not walked either. Not touched.
Coils still have no `location` attribute (only terminals and zones do).

## 0.2.2 -- coil feature-coverage gap: diagnosed, corrected, partially mitigated

Diagnosed on `sys07_vav_reheat_2e31bf24-...` (94 candidates) against the
real documented graph before changing anything. **The 0.2.1 explanation
was wrong in two ways:**

- Coils are *not* BFS-unreachable. Distances are 3-5, so
  `reachable_from_report` is true for every coil. What is true is that
  coils have no `location` (so `shares_location_with_report` is false).
- Feature vectors are *not* identical across all coils. The features
  separate the 94 candidates into 19 distinct vectors (tie groups of
  20, 12, 10, 10, 5, 5, 5, 4x5, 1x7). The pump/coil family is 24
  candidates: 4 groups.

**Actual structure (real extraction):** the documented graph has 32
`feeds` and only 3 `hasPart` edges. `hasPart` links only the AHU's own
coils/fan to `Air Loop HVAC 1` (direction part -> whole). The 10
terminal reheat coils (`Coil Heating Water 3..12`) have exactly one
relation each: `pump -feeds-> coil`. There is no coil -> VAV/zone/loop
edge, so they can only be reached from a zone *through the pump*
(zone -> VAV -> AHU -> AHU heating coil -> pump -> terminal coil = 5
hops, the same for all ten). That distance is real but carries no
per-coil information. Both true discordant pairs are of this kind, each
in a tie group of 10 (9 indistinguishable siblings).

**Direction (a), walking through the coil's owning AHU/loop, is not
available from the documented graph:** the owning relation for terminal
reheat coils does not exist in it (it is an extractor gap in
`physics_pipeline.extract`, which does not emit VAV -> reheat-coil
edges). Fixing it means changing the extraction, not `features.py`. Not
done here: it changes the documented graph every other component sees.

**Direction (b) implemented:** `CandidateFeatures.n_indistinguishable_siblings`
(also in `NUMERIC_FEATURE_FIELDS`) counts other candidates in the universe
with the same relation, endpoint types, claimed status, both distances and
shared-location flag. It uses no node ids, so the identity-leakage
exclusion of `source_id`/`target_id` is untouched. It tells the model when
it is guessing among siblings; it cannot break the tie.
`tests/test_features.py` gains a fixture reproducing the real coil shape
(AHU-owned coil via `hasPart` vs terminal coils with only a pump edge),
asserting identical structural fields for the terminal coils, sibling
count 1 for them and 0 for the AHU coil.

**Re-run of `scripts/run_plumbing_check.py`: no change in ranking.** Raw
scores are still 2 distinct values; true pairs still rank #3 and #13 (tier
1 of 2) on the sanity event. The tie was not resolved, so the true pairs
do not separate by rank. Note the 2-value collapse is also on the model
side (the GBM uses 2 score levels though the features give 19 groups), and
that was not investigated or tuned here. The script's finding text and
`plumbing_check_summary.json` now report feature-level tie groups
(19 vectors; true pairs in groups of 10) instead of the incorrect
"unreachable" claim. This says nothing about generalization: one building.
The route to a real fix is the extractor edge for terminal reheat coils.

## 0.2.1 -- end-to-end plumbing check (integration only, no model-quality claim)

`scripts/run_plumbing_check.py` wires `features.py -> models.py ->
calibration.py -> benchmark_adapter.py` together on the 16 real
`DatasetRecord`s from `scripts/generate_causal_batch.py` (previously
discarded after writing the summary; `generate_causal_batch.main` now
accepts `return_records=True` to keep them in memory). This exists to
catch integration bugs, not to claim the model works -- see the summary's
own `purpose` field and disclaimers.

**A real bug caught and fixed during this pass, not by this script's own
sanity check but by a careful re-read of `benchmark_adapter.py`:**
`run_symptom_troubleshooting_trial` treats its `tg` argument as GROUND
TRUTH (`true_edges = tg.edges_by_relation["feeds"]`) and `blueprint
.claimed_edges` as the (possibly wrong) documentation -- the opposite of
what `generate_causal_batch.py`'s `tg` is (the documented/baseline
extraction). Passing the documented `tg` directly would have made the
exercise degenerate: the discordant pair's "new" edge would never test as
true. Fixed by reconstructing the actual/realized topology from the
documented one (`_build_actual_topology`), swapping only the one `feeds`
edge the event actually changed -- exact, not a guess, because
`reassign_coil`'s fixed-inventory guarantee plus `verify_intended_change`'s
own hard-failure gate already proves nothing else changed.

**A second, more interesting non-bug found and correctly diagnosed rather
than assumed:** the script's first run of the step-4 sanity check (both
true discordant pairs should rank in the top 10 of ~94 candidates)
FAILED -- ranks #3 and #13. Investigated before treating this as either a
pass or a wiring failure: direct inspection showed the model's raw scores
collapse to only 2 distinct values across all 94 candidates. Root cause,
confirmed by inspection: coil and pump nodes carry no `location` attribute
and are BFS-unreachable from any reported zone in the current extraction
(no `feeds`/`hasPart` path connects a coil to a zone at all), so every
coil under the same pump produces an identical feature vector -- the model
correctly separates the pump/coil candidate family from everything else,
but has zero per-coil signal to rank within it. Rank #3 vs #13 was
arbitrary stable-sort order within an exactly-tied group, not evidence of
misalignment (a real misalignment bug would push the true pairs' scores
toward the population average, not into the single highest-scoring tier
with 20 other tied candidates). Fixed the sanity check itself to test tier
membership (by distinct score value) instead of raw rank, which is what
was actually diagnostic here; the naive rank cutoff would have blocked a
correctly-wired pipeline over a real, explainable modeling limitation.
**The feature-coverage gap in `features.py` was diagnosed further in 0.2.2
(below); the root-cause statement above ("BFS-unreachable", "identical
feature vector") turned out to be partly wrong -- see that entry.**

### Result (real, from `output/plumbing_check_summary.json`)

- Sanity floor: both true discordant pairs in the top score tier -- PASS
  (with the feature-degeneracy finding above attached, not hidden).
- Leave-one-event-out (4 folds, the closest approximation available with
  one degenerate-split lineage): `select_suspect_prefix` executed on real
  shapes, k=14 of 94 (universe_fraction=0.149) -- not read as a real
  coverage number per the disclaimers above.
- `benchmark_adapter.run_symptom_troubleshooting_trial(symptom_source
  ="learned")` executed successfully end to end for the first time:
  endpoint_expansion_size=12, 94/94 tests performed,
  n_tests_to_full_flag_sustained=16.
- `tests/test_oracle_parity.py` reconfirmed green (129 passed) before this
  counted as done, per the standing "never use `learned` before this
  passes" rule.

**Still true, unchanged by this pass:** one building lineage, four
physically distinct events; no accuracy or generalization claim;
`reconcile_realized_topology`'s clone/relocation path still only exercised
by synthetic fixtures.

## 0.2.0 -- node-identity reconciliation + first verified causal batch

Implements the topology-identity-reconciliation logic `simulation.py` was
previously stubbed on, and uses it to generate a small, verified batch of
causal training examples. This entry records what was actually run and
inspected, not just implemented -- see "Required acceptance checks" below.

**Working-tree note (repeated from the initial scaffold entry, still
true):** `physics_pipeline`'s working tree has substantial uncommitted
changes (`buildings.py`, `extract.py`, `faults.py`, `pipeline.py`,
`rewire.py`, confirmed via `git status` before this pass and unchanged by
it) that predate `symptom_pipeline`. This pass built against that current
uncommitted state, not the last commit -- noted for traceability, not
assumed safe to ignore.

### Empirically verified before writing any reconciliation logic

Two load-bearing assumptions, confirmed by direct OpenStudio scripts
(not assumed from reading source):

1. **Object handles are stable across independent reloads of the same
   `.osm` file.** Loading `baseline_sys07.osm` twice and comparing every
   `AirLoopHVAC`/`ThermalZone`/`PlantLoop`/`Pump` handle between the two
   loads showed 100% agreement. This is the reason a "documented"
   extraction (one load) and a "realized" extraction (a second, separately
   rewired load) can be diffed by node id at all.
2. **`.clone()` preserves neither handle nor name.** Cloning a VAV:Reheat
   terminal within the same model produced a different handle AND a
   renumbered name ("...Reheat 8" -> "...Reheat 12", not "...Reheat 8_1"),
   ruling out name-suffix stripping as a reconciliation strategy.

### Added

- `simulation.reconcile_realized_topology`: diffs two extracted topologies
  (raw `networkx.MultiDiGraph`s, exactly as `physics_pipeline.extract
  .extract_topology` returns them) via a two-tier identity resolution --
  identical handle first, then a structural signature (brick_type +
  neighboring relation/type multiset, deliberately excluding location,
  which changes for genuinely relocated equipment) for anything left over,
  refusing to guess on ambiguous (2+ candidate) matches. Caught and fixed a
  real correctness bug in its own first draft during testing: matching
  greedily while iterating a Python `set` (unordered, hash-randomized) let
  an accidental iteration order "win" an otherwise-genuinely-ambiguous
  match; fixed by grouping candidates by signature on both sides first and
  only committing a match when it is a mutual bijection (see
  `tests/test_reconciliation.py`, which reproduces the bug's exact shape).
- `simulation.run_single_intervention_experiment`: implemented for
  `rewire_kind="reassign_coil"` -- the only fixed-inventory single
  connection change confirmed available (see "Known limitations" below).
  Runs the full sequence: load baseline, apply the intervention to a fresh
  copy, re-extract, reconcile + hard-verify the intended change
  (`verify_intended_change`, raises `IntendedChangeMismatchError` on
  mismatch rather than logging and continuing), simulate baseline and
  changed under a season-matched window, measure `Zone Mean Air
  Temperature` across every zone in the building (not just the
  intervention's own zone), and label the discordant (pump, coil) pairs as
  one `MISATTRIBUTED` `DiscrepancyEvent`.
- `simulation.UnsupportedInterventionError`: every other `rewire_kind`
  (`remove_zone_service`, `remove_coil_service`, `reassign_terminal`,
  `add_extra_service`, `set_ahu_direct_service`, `clone_terminal_for_zone`)
  is rejected explicitly, with a specific documented reason each, checked
  BEFORE importing OpenStudio at all -- so this rejection path is testable
  without the `physics` extra installed (`tests/test_simulation_stubs.py`).
- `simulation.discover_reassign_coil_specs`: enumerates every real
  `reassign_coil` intervention actually available on a given building, by
  querying its plant loops for pump+coil pairs.
- `scripts/generate_causal_batch.py`: generates a batch end to end and
  wires it into `datasets.py`'s existing, unmodified `DatasetRecord`/
  `group_split`/`assert_no_split_leakage`/`assert_no_lineage_leakage` path.
- `[project.optional-dependencies].physics` now actually installs
  `openstudio==3.11.0` (previously an empty placeholder), pinned to match
  `physics_pipeline/.venv`'s own installed version.
- New tests: `tests/test_reconciliation.py` (pure Python, synthetic
  graphs -- identical-handle, relocated-clone, and genuinely-ambiguous
  cases), `tests/test_intended_change_verification.py` (pure Python,
  using the REAL discordant-pair output from an actual `reassign_coil` run
  as fixed test data -- proves the step-5 hard-failure gate fires on a
  deliberately wrong case), `tests/test_simulation_physics.py`
  (`@pytest.mark.physics`, real EnergyPlus runs -- full experiment
  correctness, per-zone effect measurement, and the reversal sanity
  check).

### Required acceptance checks -- run and inspected, not just asserted

**Step 5 fires on a wrong case:** `test_intended_change_verification.py`
constructs a deliberately wrong expected-change set against the REAL
discordant-pair output from an actual run (moving `Coil Heating Water 3`
from the hot-water pump to the chilled-water pump on `sys07_vav_reheat`)
and confirms `IntendedChangeMismatchError` fires -- for a missing pair, a
wrong-coil reference, and an unexpectedly-extra pair.

**Reversal sanity check**, `Thermal Zone 7` mean air temperature, degC:

```
baseline (documented, no intervention):        23.079
changed (reassign_coil applied):                18.468  (deviation -4.611)
reversal (independent reload, NOT applied):     23.079  (deviation +0.000)
```

The intervention's own coil delivered 40.2 kW average heating (peak 62.4
kW) at baseline and exactly 0.0 W at every hour once fed by chilled water
instead -- both simulations completed with `severe_errors=0`.

**Batch generation** (`scripts/generate_causal_batch.py`, 6 candidate
`reassign_coil` interventions attempted on `sys07_vav_reheat`): 4 succeeded
with clearly measurable effects (target-zone deviations -1.9C to -8.7C
across the 4), 2 failed with genuine EnergyPlus severe errors (moving the
central chilled-water coil onto the hot-water pump: 2267 severe errors;
one specific heating coil onto the chilled-water pump: 378) and were
excluded with their failure recorded in the batch summary's `failures`
list and `n_events_failed` count, not silently dropped. 16 `DatasetRecord`s
produced (4 events x 4 report variants: 1 clean + 3 degraded at the
existing `DEGRADED_ERROR_LEVELS`). `assert_no_split_leakage` and
`assert_no_lineage_leakage` both pass.

### Known limitations (confirmed, not assumed -- read before trusting scope)

- **Every zone-side `rewire.py` primitive destroys real equipment on every
  one of the 10 archetypes**, because every zone in every archetype
  already has its own terminal (confirmed empirically; also independently
  stated by `rewire.add_extra_service`'s own docstring). `reassign_terminal`
  and `add_extra_service` clone a terminal to relocate it but must remove
  the target zone's own pre-existing terminal first (a zone can only have
  one) with no reconciled counterpart for it anywhere in the realized
  graph; `set_ahu_direct_service` replaces a destroyed terminal with a
  freshly-constructed one with no documented counterpart either;
  `remove_zone_service`/`remove_coil_service` delete equipment outright.
  All are therefore out of v1's fixed-inventory scope and explicitly
  rejected, not silently attempted.
- **`reassign_coil` -- the one fixed-inventory intervention available --
  is only exercisable on ONE of the 10 archetypes.** Surveyed all 10:
  `sys08` has one hydronic loop (chilled-water only), `sys05`/`sys01` have
  one each (hot-water only), `sys06`/`sys02`/`sys03`/`sys04`/`sys09`/`sys10`
  have zero. Only `sys07_vav_reheat` has two (hot-water: 11 heating coils;
  chilled-water: 1 cooling coil). A batch generated today is necessarily
  single-building.
- **The clone/relocation branch of `reconcile_realized_topology` is
  validated only against synthetic graphs**, not real physics output --
  no available `physics_pipeline` intervention that satisfies v1's
  fixed-inventory constraint actually triggers it (`reassign_coil` creates
  and destroys nothing, so every node matches by identical handle). If a
  future terminal-side intervention is ever added, re-validate this branch
  against its real output before trusting it.
- **`reassign_coil` is not uniformly safe across all coils in `sys07`**:
  2 of 6 attempted candidates produced genuine EnergyPlus severe errors
  (see "Batch generation" above) rather than a clean functional-collapse
  result. This is EXCLUDED from training data (per design), not a bug in
  the rewire call itself -- consistent with `physics_pipeline`'s own
  documented finding that cross-medium coil reassignment "can produce a
  functioning EnergyPlus model that still shows severe errors."
- **The generated batch's `group_split` produces one degenerate bucket**
  (single building lineage) -- it is NOT a genuine held-out train/val/test
  partition. `datasets.py`'s split-leakage invariants are proven to hold
  on real records, but a meaningful split needs either more archetypes
  with a second qualifying pump (none exist today) or a second,
  independently-lineaged intervention family.
- **Full candidate-universe labeling reuses `hvac_benchmark`'s own
  `generate_feeds_candidates` + cached Brick ontology** (94 candidates for
  `sys07`), giving each event both its 2 positive (discordant) labels and
  92 negative labels -- this was not attempted in the 0.1.0 pass.

## 0.1.0 -- initial foundational scaffold

Implements the "real foundational scaffold + oracle-parity adapter" scope
agreed for this pass, out of the full symptom-informed-ranking design doc
(8-12 week estimate for a reviewed research prototype; this pass covers
roughly the first half of phases 1, 3, and 6, plus the type contracts and
metric/calibration machinery phases 4-5 will consume once real data exists).

### Added

- `contracts.py`: `DocumentedGraph`/`EquipmentIdentity`/`DocumentedConnection`
  (documented topology), `StructuredAnswers`/`SymptomReport` (questionnaire
  and symptom reports, every field permits "unknown"), `InterventionTruth`/
  `SimulatedObservables`/`ZoneObservableSeries` (private physical truth),
  `DiscrepancyEvent`/`DiscrepancyLabel` (ground truth), `PredictionRecord`/
  `CandidateDiscrepancyPrediction` (model output).
- `questions.py`: the fixed v1 questionnaire (8 questions), with a test
  enforcing that its documented answer choices never drift from
  `contracts.StructuredAnswers`'s enums.
- `ingestion.py`: load a `DocumentedGraph` (+ matching `TopologyGraph`) from
  Brick TTL or from reviewed equipment/connection tables; sha256 source-hash
  provenance (`hash_source_files`); structural validation
  (`validate_documented_graph`) for dangling connections, duplicate IDs,
  and unrecognized relations.
- `report_translation.py`: rule-based translation from
  `SimulatedObservables` to `StructuredAnswers` (`translate_clean`), plus
  seeded, reproducible reporting-error variant generation (`degrade_report`)
  across a swept `DEGRADED_ERROR_LEVELS` grid. Enforced by test never to
  read `InterventionTruth`.
- `features.py`: whole-documented-graph candidate-edge feature extraction
  (`extract_candidate_features`) -- endpoint types, claimed-edge status,
  BFS hop distance from reported locations over documented `feeds`/
  `hasPart` edges (no cutoff; unreachable candidates are scored, not
  excluded), shared location, and every structured-answer field. Never
  reads the actual graph, fault identity, or building identifiers.
- `models.py`: `train_gbm` (recommended v1 architecture) and
  `train_logistic_baseline`, both wrapping `sklearn` over `features.py`
  output via a `DictVectorizer` (categorical `source_type`/`target_type`
  one-hot encoded at fit time, frozen for inference).
- `calibration.py`: isotonic probability calibration (`fit_calibrator`) and
  suspect-prefix selection (`select_suspect_prefix`) targeting 95% mean
  event coverage on validation data -- a misattribution only counts as
  covered when *both* its discordant pairs are in the prefix
  (`event_covered_at_k`).
- `benchmark_adapter.py`: `run_symptom_troubleshooting_trial`, a sibling
  reimplementation of `hvac_benchmark.experiment.troubleshooting_runner
  .run_troubleshooting_trial` with an external `none`/`oracle`/`learned`
  symptom-source hook in place of that runner's internal
  `symptom_flagged_nodes()` call (which has no such hook). Also reports
  `endpoint_expansion_size` (not present on the upstream result type), per
  the design doc's instruction to measure suspect-region expansion
  explicitly.
- `evaluation.py`: `pair_recall_at_k`, `event_coverage_at_k`,
  `reciprocal_rank`/`mean_reciprocal_rank`, `brier_score`,
  `reliability_curve`, `run_paired_comparison` (crosses all three symptom
  sources with requested policies/noise/seeds), and
  `mean_tests_to_attainment` (reports non-attainment rate rather than
  silently dropping non-attaining trials from an average).
- `simulation.py` (stub, raises `NotImplementedError`): the real
  `SingleInterventionSpec` contract and the exact 8-step causal-experiment
  sequence the design doc specifies, wired to the concrete
  `physics_pipeline` functions each step would reuse.
- `datasets.py`: `DatasetRecord`, `group_split` (grouped by building
  lineage, not by individual event/report), `assert_no_split_leakage`, and
  `assert_no_lineage_leakage` -- implemented and tested against synthetic
  records; no real data to run them against yet.
- Full test suite (`tests/`) including a required oracle-parity acceptance
  check (`test_oracle_parity.py`) across every reference policy, three
  noise levels, and three seeds, on a hand-built fixture graph duplicated
  from `tests/test_troubleshooting_runner.py` at the benchmark repo root.

### Known gaps (confirmed by direct source inspection, not assumed)

- **`physics_pipeline` has no topology-identity-reconciliation function.**
  `rewire.py` mutates an OpenStudio model in place and returns `bool`;
  `extract.py`'s `extract_topology` re-derives a fresh graph but nothing
  diffs a post-rewire extraction against the pre-rewire graph and
  reconciles cloned/replaced node identities (e.g.
  `rewire.clone_terminal_for_zone`'s clone). This blocks
  `simulation.run_single_intervention_experiment` and is the reason
  `simulation.py` and `datasets.py` remain stubs/untested-against-real-data
  in this pass.
- **`physics_pipeline.pipeline._run_coil_fault` is confirmed dead code.**
  It calls `faults.add_coil_fouling_fault(ws, coil_name, coil_idd_type=...)`
  without the now-required `outside_coil_surface_area` positional argument
  and would raise `TypeError` if ever invoked; `physics_pipeline`'s own
  README documents this fault mechanism as "does not generalize" and never
  wires it in. `simulation.py`'s docstring tells future implementers to
  call `add_coil_fouling_fault` directly (with `estimate_coil_surface_area`
  against a prior sizing run's `eplusout.eio`), never to build on
  `_run_coil_fault`.
- **No standalone benchmark CHANGELOG exists** at the repo root; the
  coverage/validation claims this design references (10 system archetypes,
  86 attempted rewiring events: 83 clean, 2 functionally dead, 1 failed)
  live in `physics_pipeline/README.md`'s "Key findings" section, which this
  package's own README links to rather than restating as this package's
  own claim.
- **Pinned dependency versions, not floor-bounded.** `pyproject.toml` pins
  `hvac-benchmark==0.1.0` and every other dependency to the exact version
  present in this repo's `.venv` at the time this package was created,
  because neither the benchmark root (no git checkout) nor
  `physics_pipeline` (git checkout with uncommitted changes) can currently
  guarantee reproducibility any other way. Bump deliberately, re-running
  `tests/test_oracle_parity.py` on every bump.
