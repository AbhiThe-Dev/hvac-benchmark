# Pre-registration: physics-derived cause x check matrix for hot-water / recirculation complaints (hotwater_dx, Step 1)

Written 2026-10-07, BEFORE the first full-matrix run (`scripts/02_build_matrix.py` at `N_THETA = 200`). May not be edited after that run; changes go in a dated
"Deviations" section at the end. Everything here concerns **model output, not field evidence**.

## 0. Motivation and hard exclusions

The research notes (`research_notes/Hot water recirculation diagnostic inputs/`, `reports/Hot water missing data sources.md`) found structure and thresholds for hot-water
diagnosis in open sources, and no cause frequencies, no check likelihoods and no labelled faults. This step asks a narrower question that physics can answer: *within a small
model of a recirculating central hot-water plant, which checks separate which causes from a healthy plant, and for which (cause, check) cells does the answer depend on
numbers nobody has measured?* The second list is the input to sensitivity analysis and expert interviews (later steps).

Not in this step: cause priors, the diagnosing engine, interviews, partner work-order data, replay validation, heat-pump or indirect-tank plants, time-stepped dynamics.
This project imports nothing from the HVAC projects (`docmismatch`, `hvac_benchmark`, `symptom_pipeline`, `physics_pipeline`); a test enforces it.

## 1. The model (frozen by the code at the commit that holds this file)

One archetype (A1/D2): storage heater + master TMV in a "split-tie" layout (loop return and cold makeup mix into one stream that feeds both the heater and the TMV cold port; mass
and energy balance at every draw including zero), recirculation pump with a quadratic curve, supply and return mains, 4 direct-return risers with balancing valves (manual
fixed-orifice or thermal), optional crossover leakage at fixtures. Quasi-steady states only: idle recirculation, peak draw, pump-off stagnation (closed-form exponential
cool-down). A plant is *commissioned* before any fault is applied (valves set to design flow with a residual error; pump sized to the balanced head; heater raised if needed to respect
the TMV's minimum hot-supply margin), so "healthy" means balanced and commissioned. Faults never re-commission.

## 2. Parameters

`src/hotwater_dx/params.py`: 25 sampled parameters, each with a range, provenance tag (SOURCE / PHYSICS / ANALYST / PLACEHOLDER) and note. Source conflicts are parameters, not
constants: circulating floor `t_min_circ` in {120, 124} F, design loop dT in [5, 10] F. Sampling: Latin hypercube, `N_THETA = 200`, seed 20261007, independent sub-streams
keyed by (plant, cause, attempt) so results do not depend on loop order.

## 3. Causes (17) and the consolidation

`src/hotwater_dx/causes.py`. 25 taxonomy rows consolidate into 17 causes (row -> cause map in `CAUSES[*].taxonomy_rows`); rows 17, 20, 24, 25 are dropped with reasons (`DROPPED`).
Each cause is a pure change to a commissioned plant; severity 0 is the identity (tested). Severity and mode ranges are ANALYST.

## 4. Checks (23)

`src/hotwater_dx/checks.py`: 20 physical or read-out checks and 3 zero-cost questions. Each pre-registers **one primary feature** (second features are not scored). Time and safety class
are ANALYST estimates. K04 (TMV cold-isolation test) and K20 (history interview) are `physics_readable = False`: cells for causes declared relevant are NEEDS-ELICITATION by rule.
Pump amps and head (K08, K09) are read with the pump forced on (a technician hand-starts it), so a pump merely in its off-cycle reads normal.

## 5. Measurement-error model

`src/hotwater_dx/measurement.py` (all ANALYST unless cited). Temperature tools: clamp (contact loss kappa 0.02-0.12 of the pipe-to-ambient difference, per-visit bias sd 1.5 F, read noise 0.5 F),
probe (0.5 F), BAS (0.4 F), IR on bare copper (emissivity 0.05-0.30, reads toward ambient), logger (0.35 F). A difference of two readings with one clamp shares the contact loss and bias.
Pressure gauge sd 1 psi (0.25 psi for small drops), clamp meter 3%, stopwatch 2 s plus 3 s judgement of "hot", 0/1 read-outs misread with probability 0.05, tenant reports off by one riser with probability 0.15.
Spot readings are taken with the pump running with probability `duty`, else after an off-phase bounded by the aquastat restart (a healthy off-phase is at most a few tenths of an hour).

## 6. Sampling design and the complaint gate

For each plant: build the healthy plant, then for each cause draw (mode, severity, location) and apply it, re-drawing up to `MAX_ATTEMPTS = 6` times until the faulty plant produces the
symptom family: far-fixture time-to-hot > 30 s, or a fixture-delivered temperature more than 12 F under the TMV set point (idle) or the TMV outlet that far under at peak, or a riser-top spread
above 8 F with a riser more than 6 F under set point. Cells use symptomatic plants only if at least `GATE_MIN = 40` exist; otherwise the cause is flagged "weakly symptomatic" and cells use all plants.

## 7. Decision rules (frozen numerically; sha256 of `THRESHOLDS` below)

Per plant: effect = mean fault reading minus mean healthy reading at the same plant over `REPS = 24` noisy readings (`REPS_BINARY = 200` for 0/1 read-outs); `z = effect / sd`, where
`sd = max(sqrt(mean of the two within-plant variances), the check's resolution floor)`. This is the separation in *one* reading, with the as-designed value known (paired). A blind
column compares fault readings with the pooled 1st-99th percentile healthy band instead; it is reported, not used for classes.

- **DETERMINISTIC (seen)**: share of plants with `|z| >= 3.0` in the modal direction is >= 0.95 and direction consistency >= 0.95.
- **DETERMINISTIC (not seen)**: share with `|z| < 1.0` is >= 0.95.
- **PARAM-DEPENDENT**: anything else. The top parameters by Spearman rank correlation with z are recorded.
- **NEEDS-ELICITATION** by rule: the check is not physics-readable and the cause is declared relevant; or the cause is flagged `requires_dynamics` and the cell would be PARAM-DEPENDENT; or a PARAM cell whose
  top parameter (|rho| >= 0.5) is ANALYST or PLACEHOLDER (physics decides only conditional on a number we chose).
- **Pair confusion**: for each check and cause pair, `D = |median effect difference| / pooled sd` (sd combines measurement noise and the spread of effects over plants). A pair is separated by a check if `D >= 2.5`;
  pairs no check separates are "structurally ambiguous".
- **Tool fragility**: a DETERMINISTIC (seen) cell is flagged if it stops being DETERMINISTIC with an alternative tool (for example IR on bare copper).
- **Uncertainty ranking** (the interview list): source conflicts first, then NEEDS-ELICITATION, then PARAM-DEPENDENT (sign-unknown ones first), within tier by `1 - |2 p_sep - 1|` plus 0.1 for each of: ANALYST-dominated, tool-fragile.
- **Source cells**: eight cells have a claim from a READ source (`SOURCE_CELL_CLAIMS`). They never set a class; they set `agrees_with_source`. A disagreement is flagged CONFLICT and ranked first.
- **Two-fault interactions**: the 11 pairs seeded from the research notes are simulated at 100 plants x 10 key checks and described as masks / additive / compounds / looks-like-a / looks-like-b / mixed / invisible.

`THRESHOLDS` sha256: `9925322e8b3c7a95a0470c0a28008ee67bf96e19171fccd8acb3d0d5c133c840` (tested against the code; `frozen_thresholds.json` is written with every run).

## 8. Predictions, written before the full run

1. `fixture_branch_local` is DETERMINISTIC (not seen) on K01, K05, K07, K08 and K10, and DETERMINISTIC (seen) on K16.
2. `pump_failed` is DETERMINISTIC (seen) on K08 and K09; `pump_control_fault` is not DETERMINISTIC (seen) on K08 and is on K10.
3. `crossover` is DETERMINISTIC (seen) on K17 and K18 (AYALA16) and not DETERMINISTIC (seen) on K05 (AYALA16: temperature logging "indicative" only).
4. `balancing_valve_misset` is seen (DETERMINISTIC, or PARAM with p_sep >= 0.5) on K06 and not DETERMINISTIC (seen) on K05 (BED15: a fine principal return can hide a starved riser).
5. At least one cause pair is structurally ambiguous (no check separates it at D >= 2.5). Expected candidates: `heater_setpoint_low` vs `plant_sensor_offset`; `dip_tube_short_circuit` vs `heater_output_loss`.
6. At least one DETERMINISTIC (seen) cell is tool-fragile (degrades with IR on bare copper).
7. At least one seeded interaction is observed as `masks` or `looks_like_a/b` on some key check.
8. Weakly symptomatic causes (gate pass rate under 0.2): `pump_undersized`, `cold_pressure_problem`, `insulation_loss`.
9. At least 20% of cells are PARAM-DEPENDENT or NEEDS-ELICITATION (the model does not decide everything).

A prediction that fails is reported as failed. Predictions 3 and 4 are the only ones where a failure points at the model disagreeing with a source rather than at a modelling choice.

## 9. Gates (any failure means no result is reported)

(a) `scripts/01_validate_model.py` passes: no non-converged solve, enthalpy residual < 1e-3, healthy complaint rate < 2%, riser-top spread p95 <= 5 F. (b) The unit tests pass. (c) Re-running with the same
seed reproduces the matrix. (d) The threshold hash in the output equals the one above.

## 10. Execution order and honesty about what was already looked at

Tests -> `01_validate_model.py` -> one full run of `02_build_matrix.py` -> report. No threshold is changed after a matrix is seen. Class-count sensitivity to `Z_SEP` +-20% is reported as exploratory.

**Disclosed before freezing:** while building the pipeline I ran small smoke runs (24-60 plants, 1-17 causes) to find code defects. They led to these design changes, all before the thresholds were frozen:
the number of repeat readings went from 12 to 24 (null cells were not reliably null with 12), 0/1 read-outs use 200 repeats, pump amps and head are read with the pump forced on, the read-out misread rate is 0.05
(was 0.10) with resolution floor 0.1, the healthy off-phase is bounded by the aquastat restart, commissioned plants respect the TMV's minimum margin, and the heater and TMV ranges were widened. No cell result from a smoke run is used.

## Addendum 1 (2026-10-07, written BEFORE the full run): the return tie

The literal layout (all return flow through the heater cold inlet; TMV fed only by heater outlet and cold main) forces the TMV hot-port flow to equal the loop flow, so below a draw of about 0.3 times
the loop flow the outlet creeps toward the heater temperature, and a healthy plant would sit at heater temperature overnight. This model uses the "split tie" instead. The literal layout is not modelled and not
one of the causes. Powers' "creeps high overnight when the return is not properly plumbed" is therefore outside what this matrix can say.

## Result of the full run (2026-10-07; `scripts/02_build_matrix.py`, N_THETA = 200, seed 20261007, threshold sha256 as above; 33 s)

Gates: validation script PASS (0 non-converged solves, enthalpy residual 4e-16, healthy complaint rate 0.000, riser-top spread p95 3.4 F), 74 tests pass, threshold hash matches. 17 causes x 23 checks = 391 cells:
**26 DETERMINISTIC (seen), 252 DETERMINISTIC (not seen), 54 PARAM-DEPENDENT, 59 NEEDS-ELICITATION.** Moving `Z_SEP` by +-20% (exploratory): seen 34 / 26 / 23, PARAM 48 / 54 / 57; the not-seen count does not move.

Scorecard of section 8 (reported as run, failures included):

| # | Prediction | Result |
|---|---|---|
| 1 | `fixture_branch_local` not seen on K01/K05/K07/K08/K10, seen on K16 | **holds** |
| 2 | `pump_failed` seen on K08, K09; `pump_control_fault` not seen on K08, seen on K10 | **holds** |
| 3 | `crossover` seen on K17 and K18; not seen on K05 | **partly fails**: K17 seen (p_sep 1.00) and K05 not seen, but K18 is NEEDS-ELICITATION (p_sep 0.85, depends on `p_hot_deficit`, an analyst range) |
| 4 | `balancing_valve_misset` seen on K06, not seen on K05 | **partly fails**: K05 not seen (p_null 0.98) but K06 p_sep is only 0.23, NEEDS-ELICITATION, driven by `duty` (rho -0.85); flagged CONFLICT with BED15. K13 (flow from valve dP, pump forced on) sees it at 0.99 |
| 5 | at least one structurally ambiguous cause pair | **holds** (5 pairs: balancing vs isolation valve D 0.58; check valve vs insulation loss 0.69; setpoint-low vs dip tube 2.05; dip tube vs TMV set 2.21; output loss vs dip tube 2.21). The named candidate `heater_setpoint_low` vs `plant_sensor_offset` is separable (K11) |
| 6 | at least one tool-fragile seen cell | **holds** (7 cells: K01, K03, K05, K06 under IR) |
| 7 | a seeded interaction observed as masks / looks-like | **fails**: of 110 pair x check outcomes, 77 both-invisible, 23 additive, 5 mixed, 4 emergent, 1 compounds; none masks or looks-like |
| 8 | weakly symptomatic causes = pump_undersized, cold_pressure_problem, insulation_loss | **holds** (gate pass 0.00, 0.01, 0.04) |
| 9 | at least 20% of cells PARAM or NEEDS-ELIC | **holds** (28.9%) |

Source cells: model agrees with the cited source in 7 of 8 (the disagreement is prediction 4).

What the run says, in order of consequence:
1. **The pump duty cycle at the moment of the visit is the dominant unknown.** `duty` is the top parameter for 47 of the 113 uncertain cells (next: `t_set_tmv` 13, `valve_thermal` 12). A spot reading of any flow-dependent
   quantity lands in a pump off-phase with probability 1 - duty, which dilutes riser-level and return-level checks. This is a plausible real effect and also an artefact of an analyst range (0.25-1.0).
2. Checks that need flow are only as good as the pump state when they are taken. K08, K09 (pump forced on) and K13 (valve dP) are deterministic where the spot checks K05-K07 are not.
3. Only 26 of 391 cells are deterministic; the cause pairs balancing vs isolation valve and check valve vs insulation loss cannot be separated by any single check in the model.
4. Three causes (`pump_undersized`, `insulation_loss`, `cold_pressure_problem`) almost never produce the symptom here; their cells are computed on all plants.

## Addendum 2 (2026-10-07, written AFTER the full run, EXPLORATORY, not part of the frozen matrix): forcing the pump on

Because of finding 1 above I re-classified K05, K06 and K07 with the pump forced on (a technician hand-starts it), same plants, same thresholds. K06 then sees `balancing_valve_misset` and `isolation_valve_closed`
as DETERMINISTIC (seen), both previously NEEDS-ELICITATION, and `pump_control_fault` becomes invisible to K05-K07 (forcing the pump on hides a control fault, which K10 reads directly). Several other cells move between PARAM and
NEEDS-ELIC. This is a post-hoc exploration: it motivates adding forced-on variants of K05-K07 to the v1 check library with their own pre-registration; it does not alter the results above.

## Addendum 3 (2026-10-09, written BEFORE the engine/stress run): sequential engine and model-mismatch stress test

**Origin.** The matrix says which checks separate which causes. This addendum adds the engine that uses it (rank causes, pick the next check, update, stop) and asks how far its accuracy and, above all, its
*confident errors* survive when the world differs from the model that produced its likelihoods. Everything is simulation: it measures robustness to the kinds of model error listed below, not accuracy in buildings.

**Engine** (`engine.py`, constants in `ENGINE_CONFIG`). Hypotheses: the 17 single causes, the 11 seeded cause pairs (multi-fault support), and "other". Prior mass 0.80 / 0.15 / 0.05, uniform within each group.
Likelihoods: Gaussians per (hypothesis, check) fitted from a matched simulated world (200 plants, seed 20261101; 8 repeat readings per plant, 25 for 0/1 read-outs); "other" has the pooled mean and 1.5x the pooled spread.
Selection: expected information gain (bits, computed on an adaptive grid) per minute, where minutes = the check's time plus travel from the technician's current location (door->mechanical room 5, ->riser 8, ->fixture 8,
mechanical room->riser 4, ->fixture 6, riser->fixture 3; questions cost no travel; ANALYST). Stop when the leading hypothesis reaches 0.90, or the best remaining check gives under 0.02 bits/min, or 12 checks, or none are
left. Checks that need an unavailable valve type are excluded (K12 thermal only, K13 fixed-orifice only). K04 and K20 are not in the engine (no physics likelihood). The engine is told nothing else about the plant.

**Variants.** `A_plain` (above). `B_robust`: likelihood variance x2, "other" prior 0.10, stop at 0.95. `S_singles_only`: A without pair hypotheses. Baselines on the same cases and stop rule: `fixed_order` (a flowchart
order: Q1, Q2, Q3, K16, K05, K10, K08, K01, K03, K07, K06, K09, K11, K15, K14, K02, K13, K12, K17, K18, K19; ANALYST), `random_order`, and `all_checks` (every check, no early stop: the in-model ceiling).

**Test worlds** (100 plants each, fresh seeds 20261201+; cases: 30 symptomatic single-fault plants per cause (causes with fewer than 10 symptomatic plants are skipped), 9 per seeded pair): `matched` (same ranges, new seed);
`param_shift` (ua_mult 1.5-2.3, len_scale 1-2, duty 0.15-0.5, peak_frac 0.75-0.95, heater_cap 200-450 kBtu/h, balance_err 0.3-0.5, tmv_tol 3-7, t_amb 55-80); `mild_faults` (severity x0.5); `max_faults` (severity 1);
`latent_and_noise` (half the plants carry a hidden asymptomatic crossover of 0.02-0.04 gpm/sqrt(psi) on 1-2 risers, instrument error x2); `technician_error` (10% of checks cannot be done, costing 3 min; 10% of readings are wrong,
drawn from a random other hypothesis); `composite_1.00` (all of the above). The mismatch dial runs the composite from lambda 0 to 1 (0, 0.25, 0.5, 0.75; 1.0 is the composite world), A and B only.

**Metrics.** Single-fault top-1 (the leading hypothesis is the true cause); two-fault hit (the leading hypothesis names at least one true component) and exact; wrong-and-confident = stopped at the confidence bar with no true
component; abstain = stopped without reaching the bar; mean checks and minutes; expected calibration error of the leading posterior (10 bins, single-fault cases); accuracy when confident.

**Predictions (frozen):** E1 matched `A_plain`: top-1 >= 0.70 and wrong-and-confident <= 0.05. E2 matched `A_plain`: <= 8 checks and <= 60 minutes on average. E3 matched: engine minutes <= fixed-order minutes with top-1 within 0.02 of
fixed order or better. E4 composite lambda=1: `A_plain` wrong-and-confident > 0.10 (overconfidence under mismatch), `B_robust` <= 0.7 x that, with matched top-1 within 0.05 of `A_plain`. E5 matched pair cases: `A_plain`
pair-hit >= 0.70 and >= singles-only + 0.05. E6 along the dial `A_plain` top-1 is non-increasing within 0.03 per step and falls by at most 0.25 overall.
**Decision rule for the recommended variant:** B if its wrong-and-confident is <= A's in every test world and its matched top-1 is within 0.05 of A's; otherwise A. Differences under 0.03 are not interpreted (sampling error is about +-0.02 at these case counts).

**Not claimed.** No result here says anything about accuracy in real buildings; the unmodelled kinds of error (a different plant archetype, an unmodelled cause, real technician behaviour) are exactly the ones this test cannot see.
No engine or test setting changes after the run; changes go in Deviations.

Hash of the engine and stress configuration (`stress.frozen_hash()`): `00578d290af4bc03f8c72c8a1316210d3dd562bc70d76e6070d3da91121715d7`.

**Disclosed:** before freezing I fitted the engine on a 60-plant world and ran one simulated visit (a dead pump, diagnosed in 5 checks) and the unit tests, to confirm the code runs. No result from them is used.

## Result of Addendum 3 (2026-10-09; `scripts/03_engine_stress.py`, 160 s; hash as above; full tables in `output/ENGINE_STRESS_REPORT.md`, `engine_stress.csv`)

Simulation only. 501 single-fault and 99 two-fault cases in the matched world (436 / 99 in the composite world, where fewer causes had enough symptomatic plants).

| # | Prediction | Result |
|---|---|---|
| E1 | matched A: top-1 >= 0.70, wrong-and-confident <= 0.05 | **holds**: 0.76 and 0.027 |
| E2 | matched A: <= 8 checks, <= 60 min | **holds**: 6.3 checks, 41 min |
| E3 | engine minutes <= fixed-order minutes, top-1 not worse by more than 0.02 | **holds**: 41 min and 0.76 against 90 min and 0.59 (random order: 150 min, 0.65). The fixed order is my own plausible flowchart, not a tuned or published one |
| E4 | composite lambda=1: A wrong-and-confident > 0.10; B <= 0.7 x A; matched top-1 within 0.05 | **holds**: A 0.127, B 0.036; matched 0.72 vs 0.76 |
| E5 | pair cases: A hit >= 0.70 and >= singles-only + 0.05 | **fails**: A 0.93 vs singles-only 0.92. The pair hypotheses do not help the "name one true component" score, because a singles-only engine usually names one anyway. Their benefit shows elsewhere: exact two-fault identification 0.23 vs 0.00, and lower wrong-and-confident in every world (matched 0.027 vs 0.043; composite 0.127 vs 0.185) |
| E6 | along the dial top-1 non-increasing (within 0.03) and falls by at most 0.25 | **fails** on the size of the drop: 0.77, 0.72, 0.68, 0.59, 0.44 (monotone, but down 0.33). The all-checks ceiling falls to 0.36 in the same world, so most of the loss is in the information, not the policy |

Recommended variant by the frozen decision rule: **B_robust** (its wrong-and-confident is no higher than A's in every world and its matched top-1 is within 0.05 of A's).

Other facts from the run, not predicted:
1. **The engine is rarely confident.** At the 0.90 bar A is confident in 43% of matched visits (B: 26%); the rest stop for "no remaining check worth its time" and report a best guess. When A is confident it is right 94% of the time (B: 99%).
2. **Calibration degrades fast:** expected calibration error 0.05 matched, 0.29 in the composite world for A (0.18 for B).
3. **Worst single mismatches for A:** technician error (top-1 0.62, wrong-and-confident 0.088, two-fault hit 0.77) and shifted parameters (0.67, 0.076). Mild or maximal fault severity alone changes little (0.80 / 0.70).
4. **Information-based ordering beats the fixed-order and random baselines in every world**, on minutes (about 35-50 against 80-100 for the fixed order and about 150 for random order) and on top-1 (for example matched 0.76 against 0.59 and 0.65; composite 0.44 against 0.42 and 0.35, the narrowest gap). The all-checks ceiling is higher than A in most worlds (matched 0.78, param_shift 0.72).
5. **Under heavy mismatch an early stop beats using every check** (composite: A 0.44, all checks 0.36): more readings of mis-performed checks add noise.
6. The matched all-checks ceiling in the engine's own terms is 0.78, close to the 0.80 of the earlier naive-Bayes estimate.

Limits: the test worlds are generated by the same physics with different parameters; a different plant, an unmodelled cause, or real technician behaviour is exactly what it cannot see. The flowchart baseline and the travel minutes are my estimates.

## Addendum 4 (2026-10-09, written BEFORE the sensitivity run): which assumed inputs change what the engine does?

**Question.** Which of the inputs we had to assume (plant parameters, case mix, check times, instruments available, the engine's own settings) change the engine's accuracy, its confident errors or its minutes by more than noise,
so interview time goes only to those? Simulation only; nothing here measures a building.

**Design** (`sensitivity.py`; constants in `SENS_CONFIG`, hash below). Baseline = Addendum 3's matched world and engine A (fitted once, not refitted), same cases and seeds.
(1) *Noise floor*: 5 replicate case samples and evaluation seeds on the same world; the sd of top-1, wrong-and-confident and relative minutes. (2) *World parameters*: for each of the 25 sampled parameters, the world rebuilt with that parameter
restricted to its lower half-range and to its upper half-range (binary parameters pinned to each value), all else unchanged. (3) *Case-mix prior*: 5 Dirichlet(1) mixes over the 17 single causes; the engine with its uniform prior, with the true mix as prior
(oracle), and with another mix as prior (wrong). (4) *Check-time belief*: the engine's believed minutes per check multiplied by lognormal(0, 0.7), 5 draws; true minutes still charged. (5) *Toolkit tiers*, cumulative: T0 questions, eyes, stopwatch and
controls read-out (Q1-3, K16, K10); T1 + thermometer checks (K01, K02, K03, K05, K06, K07, K11); T2 + gauges and clamp meter (K08, K09, K13, K14, K15); T3 + valve wells and isolation tests (K12, K17, K18); T4 + 72 h logger (K19).
(6) *Leave-one-check-out* from all 21 checks. (7) *Engine settings*: confidence bar {0.8, 0.9, 0.95, 0.99} x minimum value rate {0.005, 0.02, 0.05, 0.1} bits/min, and likelihood variance inflation {1, 1.5, 2, 3}, on matched and composite-mismatch cases.
(8) The first check recommended before any reading, for each configuration (descriptive).

**"Matters"**: an effect matters if |d top-1| >= max(0.04, 2 sd) or |d wrong-and-confident| >= max(0.02, 2 sd) or |d minutes| >= max(15%, 2 sd), where sd is the replicate noise floor of that metric. A parameter's *score* is the largest of these
effects as a multiple of its bar over the two half-ranges (score >= 1 = matters). Nothing in the engine or the earlier results is changed by this analysis.

**Predictions (frozen):** S1 `duty` (the share of time the pump runs at arrival) ranks in the top 3 parameters by score (it dominated the matrix's uncertain cells). S2 at most 8 of the 25 parameters matter and at least 12 score below 0.5.
S4 top-1 is non-decreasing (within 0.02) from tier T0 to T4, T0 is below 0.45, and the largest step is T0 -> T1 (the first thermometer). S5 the oracle prior improves top-1 by at least 0.05 on average, and a wrong prior costs less than 0.05 relative to the uniform one.
S6 mis-believed check times change mean true minutes by under 15% and top-1 by under 0.03. S7 removing any single check costs at most 0.05 top-1, and the most costly removal is one of K05, K06, K10, K16, K17.
S8 on matched cases some (confidence bar, minimum rate) setting has wrong-and-confident <= 0.03 with confident >= 0.5. (There is no S3; the first-check listing is descriptive.)

**Not claimed.** Real priors, real check times, which parameters matter in buildings: all unknown. The ranking says where the *model's* answer is fragile to the *assumed* numbers.

Hash of the sensitivity configuration (`sensitivity.config_hash()`): `2c263ddf4dc8c16200754dcc414559d1c4ef7cfc7bd779edc07e97007f7939ea`.

## Result of Addendum 4 (2026-10-09; `scripts/04_engine_sensitivity.py`, about 9 min; config hash as above; `output/ENGINE_SENSITIVITY_REPORT.md`, `engine_sensitivity.csv`)

Baseline reproduces Addendum 3 exactly (top-1 0.764, wrong-and-confident 0.027, 41 min). Noise floor from 5 replicates: top-1 sd 0.014, wrong-and-confident 0.010, minutes 1.8%. Simulation only.

| # | Prediction | Result |
|---|---|---|
| S1 | `duty` ranks in the top 3 parameters | **fails**: top 3 are `tmv_margin_min`, `p_cold`, `u_ins`; `duty` ranks 5th (score 0.60) |
| S2 | at most 8 parameters matter, at least 12 score below 0.5 | **holds, trivially**: 0 of 25 matter; 18 score below 0.5. See the caveat below |
| S4 | tier top-1 non-decreasing, T0 < 0.45, largest step T0 -> T1 | **holds**: 0.41, 0.60, 0.74, 0.76, 0.76 (steps +0.19, +0.14, +0.02, +0.00) |
| S5 | oracle prior >= +0.05 top-1; wrong prior costs under 0.05 | **holds** as reported: oracle +0.095 (and about 11 fewer minutes), wrong prior -0.006 on average (individual mixes -0.054 to +0.068). **[Corrected 2026-10-10, see Deviations: the comparison zeroed the prior of causes absent from the test visits; kept, oracle is +0.052 and a wrong prior -0.044.]** |
| S6 | mis-believed check times change minutes < 15% and top-1 < 0.03 | **fails narrowly**: +12.5% minutes (passes), top-1 -0.036 (fails the 0.03 bar) |
| S7 | no single check costs more than 0.05; the costliest is one of K05/K06/K10/K16/K17 | **fails**: removing Q1 ("which floors are affected") costs -0.060 and doubles wrong-and-confident (0.062); next K11 -0.054, Q2 -0.050, K01 -0.048, K15 -0.048 |
| S8 | some (bar, rate) setting has wrong-and-confident <= 0.03 with confident >= 0.5 on matched cases | **fails**: the closest are (0.90, 0.005) at 0.042 / 0.53 and (0.95, 0.005) at 0.013 / 0.38. Confident errors and confident coverage trade off along a frontier |

**Caveat on S2 (a limit of my own design).** The pre-registered sweep restricts each parameter to a half of its *fitted* range, so the engine never meets a value it was not fitted on; "nothing matters" is therefore what the design could show, not evidence the engine is robust. The earlier stress test, which went outside the ranges
with several parameters at once, cost 0.09 to 0.32 top-1.

Other facts from the run: the first check recommended before any reading is Q2 ("worse at peak only?") in every configuration. A 72 h logger adds nothing in this model (0.764 with or without it), because the model has no time-of-day behaviour: do not read this as "loggers are useless". Moving the stopping rule's minimum value
rate to 0.05 bits/min or higher collapses accuracy (0.60) by stopping early; 0.005 gains about 1 point for 13 more minutes. Likelihood variance inflation trades accuracy for fewer confident errors (x2: top-1 0.72, wrong-and-confident 0.010).

## Addendum 5 (2026-10-09, written AFTER the Addendum 4 result, EXPLORATORY, not pre-registered): parameters beyond the fitted range

Because of the caveat above, each continuous parameter was pushed up to half a range *beyond* its fitted range on each side (clipped to physical bounds), one at a time, engine not refitted (`sensitivity.out_of_range`; `output/ENGINE_SENSITIVITY_OUT_OF_RANGE.md`). Same bar and noise floor.
**13 of 44 parameter-side combinations matter.** Largest effects (d top-1 / d wrong-and-confident): cold-side static pressure `p_cold` below 45 psi (-0.104 / +0.133); pump head at design flow below the balanced design (`pump_oversize` 0.7-1.0: -0.054 / +0.081); dead leg longer than 12 ft (`deadleg_ft` 12-16: -0.150 / +0.002);
TMV set point outside 120-130 F (`t_set_tmv` 115-120: -0.090 / +0.032; 130-135: -0.041 / +0.033); TMV minimum margin above 25 F (-0.061 / +0.039); piping 1.5x to 1.9x longer than nominal (-0.047 / +0.034); pump running less than 25% of the time (`duty` 0.05-0.25: -0.058 / +0.012);
design loop dT outside 5-10 F; high insulation loss; peak load above 85% of plant capacity. Part of this is mechanical: the engine reads *absolute* values (a return temperature, a time-to-hot), so a plant whose known set point or dead-leg length lies outside the fitted range shifts every reading. Those are facts a technician can read on arrival,
so conditioning the likelihoods on them (an intake step) is the obvious fix and is **not yet built or tested**.


## Addendum 6 (2026-10-09, written BEFORE the full run): the simulator as an adversary

**Question.** Idea 6 of the robustness brief: instead of hand-picked mismatch worlds, search a broad plausible family of plants and visits for where the engine is confidently wrong, then ask whether what the search finds lets us build a better engine than `B_robust` (the variant recommended in Addendum 3). Simulation only; the adversary can only find failures *inside this simulator's structure* (one plant archetype, steady state). It cannot find structural mismatch, so a good result here is not evidence about buildings.

**Design** (`adversary.py`; constants in `ADV_CONFIG`, hash below; `scripts/05_adversarial.py`, about 10 min).
(1) *Broad family.* Every continuous parameter is drawn from its fitted range extended by half its span on each side, clipped to the physical bounds of Addendum 5 (`PHYS`); the two binary parameters keep both values. Per visit: instrument error x U(1, 2), 0-10% of checks skipped, 0-10% of readings wrong, and 25% of plants carry a hidden asymptomatic crossover. No value exceeds the Addendum 3 composite world's. Visits are the Addendum 3 kind: up to 60 symptomatic plants per single cause, 9 per seeded pair, 200 plants per world.
(2) *Three disjoint sets of worlds.* Search: 8 worlds (the first 5 are peeled, the last 3 only validate the chosen box). Held-out confirmation: 6 fresh worlds, never used to select anything. Extrapolation probe: 2 worlds with every range extended a full span instead of half. Plus the five Addendum 3 worlds (matched, param_shift, latent_and_noise, technician_error, composite_1.00) at their original seeds and cases, as out-of-family checks; engine A and B must reproduce Addendum 3's numbers there.
(3) *Mining* (on engine A's confident-and-wrong rate, search set only). A per-feature failure-rate profile by quintile (25 plant parameters, the three per-visit knobs, the hidden-crossover flag) with a max-T permutation test (200 permutations; whole plants are permuted for plant features, so visits of one plant do not count as independent). PRIM peeling (Friedman and Fisher 1999: peel 5% per step from one tail of one feature, no pasting) on three feature sets: all features, plant parameters only, and `ARRIVAL` (facts a technician can read or estimate on arrival: ambient and cold-water temperature, static cold pressure, heater and TMV set points, deadband, heater capacity, storage volume, TMV minimum margin, relative pipe length, design dT, return floor, valve type, pump rating, dead-leg length; ANALYST list). The box is chosen on the validation worlds: highest validation density with support >= 0.10, then the simplest box (fewest restricted features) within 0.01 of that density.
(4) *Candidate fixes, all scored on identical visits and seeds* (wrong readings are drawn from the matched engine's likelihoods for every variant, so variants differ only in the engine). `A_plain`, `B_robust` as before (fitted on the Addendum 3 matched world). `R_A`, `R_B`: engines A and B with likelihoods **refitted on the broad family** (400 plants, instrument error x1.5, 25% hidden crossover; the adversary's family used as the training distribution). `G_guard`: engine A, switching to B's settings whenever the plant's arrival facts fall in the `ARRIVAL` box found on the search set (inactive unless that box's validation density is >= 1.5x the validation overall rate).
(5) *Metrics* as in Addendum 3 (single-fault top-1, wrong-and-confident, confident, checks, minutes, ECE), plus paired differences with 95% intervals from resampling whole plants (500 resamples).

**Predictions (frozen)**
- **P1** (the adversary finds a real failure region): the plant-parameter PRIM box has validation density >= 2.0x the validation overall rate at support >= 0.10, and on the held-out family density >= 1.5x the held-out overall rate with the 95% interval lower bound above that rate. *(I expect this to hold; the Addendum 5 effects were large.)*
- **P2** (agrees with Addendum 5): among the five plant parameters with the largest profile statistic, `p_cold` is present and at least three are among those Addendum 5 flagged (`p_cold`, `pump_oversize`, `deadleg_ft`, `t_set_tmv`, `tmv_margin_min`, `len_scale`, `duty`, `dT_design`, `u_ins`, `peak_frac`, `tmv_sag_gain`).
- **P3** (the broad family is harder than the matched world): on the held-out family engine A has top-1 <= 0.65 and wrong-and-confident >= 0.06 (matched: 0.764 / 0.027).
- **P4** (training on the adversary's family helps in-family): `R_A` has wrong-and-confident <= 0.70x `A_plain`'s on the held-out family with top-1 not lower by more than 0.01.
- **P5** (improvement over the incumbent): at least one of `R_A`, `R_B`, `G_guard` passes **all four** of: (i) held-out wrong-and-confident <= `B_robust`'s + 0.01; (ii) held-out top-1 >= `B_robust`'s + 0.03, or confident share >= `B_robust`'s + 0.05; (iii) matched-world top-1 >= `A_plain`'s - 0.05; (iv) wrong-and-confident <= `B_robust`'s + 0.01 in both the composite_1.00 and technician_error worlds. *(Genuinely uncertain; `B_robust` is already a strong, simple variant.)*
- **P6** (the arrival guard): `G_guard` recovers at least half of `B_robust`'s reduction in held-out wrong-and-confident relative to `A_plain`. *(I expect this to fail: several of the largest failure drivers, such as hidden crossover and instrument error, are not knowable on arrival.)*
- **P7** (no new weakness out of family): `R_B`'s wrong-and-confident <= `B_robust`'s + 0.01 in each of composite_1.00 and technician_error.
- **P8** (the refit's cost is small in the matched world): `R_A` matched top-1 >= `A_plain`'s - 0.05 and wrong-and-confident <= 0.05.
- **P9** (extrapolation): on the extrapolation family `R_A`'s wrong-and-confident <= `A_plain`'s.
**Decision rule for what to recommend:** the passing variant of P5 with the lowest held-out wrong-and-confident; if none passes, `B_robust` stays recommended and the finding is "no improvement". Sampling error on wrong-and-confident differences at these sizes is about +-0.01; the paired intervals are reported and a difference inside its interval is not claimed.

**Disclosed before freezing.** I ran the pipeline twice at tiny sizes (40-plant worlds, 1-2 per set, refit on 60 plants) to check that the code runs, and I saw its output. Two things came out of it. (a) PRIM boxes chosen by highest density on the peeling data restricted up to 14 features (the known habit of peeling noise), so I added the validation split and the simplest-box rule above before freezing. (b) The Addendum 3 worlds in that run are full-size, so **I already saw that `R_A`'s matched-world top-1 was about 0.69 against `A_plain`'s 0.76 and `R_B`'s about 0.61**: P8, and condition (iii) of P5 for `R_A`, are therefore not blind and I expect them to fail again (the full refit uses 400 plants, so the numbers will differ somewhat). The tiny-run P1 and P2 did not hold either but at that size they say nothing. No bar, prediction or case count was changed because of what I saw. Before the smoke run I also looked at the family itself on 100-plant worlds: with the half-span extension about 12% of healthy plants already complain and 1 of 800 solves did not converge; with the full span 45% complain, so the extrapolation family is well past plausible and is used only as a probe.

**Not claimed.** Nothing here measures a building. "Worst case" means worst within a family I defined; a different plant, an unmodelled cause or real technician behaviour is outside it. The guard's box can only use facts a technician could read on arrival; whether they are read correctly is untested.

Hash of the adversary configuration (`adversary.frozen_hash()`; includes the engine and stress hashes): `d37343f43a91ef358fa0038db0264d09409ef02c7c53224b99f65b70d9dceafe`.

## Result of Addendum 6 (2026-10-09; `scripts/05_adversarial.py`, 459 s; hash as above; `output/ADVERSARY_REPORT.md`, `adversary.json`, `adversary_variants.csv`)

Simulation only. 8,710 search visits, 6,534 held-out, 2,238 extrapolation. Engines A and B reproduce Addendum 3 exactly in its worlds (matched 0.764 / 0.027; composite 0.127 / 0.036). In the broad family 11-12% of healthy plants already complain (46% in the extrapolation family).

| # | Prediction | Result |
|---|---|---|
| P1 | the plant-parameter box is >= 2x denser than average on validation and >= 1.5x on held-out | **fails**: PRIM needed 14 features to reach 0.152 against a 0.135 baseline (1.1x); held-out 0.146 against 0.136 (the interval is above baseline, but only just). The confident errors are spread over the family, not concentrated in a box. I expected a box |
| P2 | top-5 plant parameters include `p_cold`, at least 3 flagged in Addendum 5 | **holds**: `p_cold` (t = 11.9; lowest quintile 0.228 against 0.11-0.13 elsewhere), `tmv_margin_min`, `len_scale`, `t_set_tmv`, `deadleg_ft`: all five flagged. Also significant: `tmv_sag_gain`, `ua_mult`, `pump_oversize`. Not individually detectable: `duty`, instrument error, skipped or misread checks, the hidden-crossover flag |
| P3 | the broad family is harder than matched | **holds**: engine A top-1 0.514, wrong-and-confident 0.136 (matched 0.764 / 0.027; five times the confident errors) |
| P4 | family-trained `R_A` cuts A's wrong-and-confident by >= 30% without losing top-1 | **holds**: 0.036 against 0.136, top-1 0.588 against 0.514 |
| P5 | some variant beats `B_robust` under the frozen rule (i)-(iv) | **fails**: `R_A` ties B on accuracy (0.588 vs 0.580) and fails (ii); it also misses (iv) by 0.001 in technician_error (0.048 vs 0.037 + 0.01). `R_B` is safer (0.011) but confident in only 12% of visits and loses 0.05 matched top-1 (0.669), failing (ii) and (iii). `G_guard` fails (i) |
| P6 | the arrival guard recovers >= half of B's reduction | **fails**: the guard never switched on (the arrival-only box was 1.2x baseline at 12% support, below the 1.5x bar) |
| P7 | `R_B` no worse than B in composite and technician_error | **holds**: 0.013 vs 0.036 and 0.018 vs 0.037 |
| P8 | `R_A`'s matched cost is small | **holds**: top-1 0.721 against 0.764, wrong-and-confident 0.015 (this one was not blind, see the disclosure) |
| P9 | `R_A` no worse than A on the extrapolation family | **holds**: 0.051 against 0.201 |

**Recommendation by the frozen rule: `B_robust` stays; no improvement.**

Held-out broad family (paired intervals resample whole plants):

| variant | top-1 | wrong-and-confident | confident | ECE | minutes |
|---|---|---|---|---|---|
| A_plain | 0.514 | 0.136 | 0.45 | 0.266 | 47 |
| B_robust | 0.580 | 0.029 | 0.23 | 0.142 | 54 |
| R_A | 0.588 | 0.036 | 0.24 | 0.075 | 50 |
| R_B | 0.572 | 0.011 | 0.12 | 0.054 | 52 |

`R_A` against `B_robust`: wrong-and-confident +0.007 [+0.002, +0.012], top-1 +0.008 [-0.005, +0.019], confident +0.016 [+0.006, +0.025]: a tie, with marginally more confident errors. `R_B` against B: wrong-and-confident -0.018 [-0.022, -0.013], top-1 -0.008 [-0.021, +0.005], confident -0.110 [-0.119, -0.101]: safer, at the price of being decisive half as often.

Other facts, not predicted: (1) `R_A` is better calibrated than `B_robust` in the broad family (ECE 0.075 against 0.142), the composite world (0.138 against 0.179) and the extrapolation family (0.172 against 0.249), and slightly worse matched (0.079 against 0.062); calibration was not in the frozen rule. (2) Plants that already complain when healthy are harder for every variant (A top-1 0.35 against 0.55) but are not what drives the gap between variants. (3) The cheap fix already in hand (B, widening every likelihood by the same amount) is as good as refitting on the family, so what the search found does not call for a new engine.

**What this does and does not say.** The useful output is the *headline number*: on a broad plausible family of plants the plain engine is right 51% of the time and confidently wrong 13.6% (B: 58% and 2.9%), a more honest bound than the matched world's 76% / 2.7%, and the drivers it ranks (cold-side static pressure above all; TMV set point and margin; pipe length; dead leg) agree with Addendum 5's one-at-a-time sweep. It did not find a pocket of knowable facts that is much worse than the rest, so an arrival-fact switch has nothing to switch on; whether conditioning the likelihoods on one or two such facts (`p_cold` is the one clear candidate) recovers anything is untested. Everything is inside this simulator: structural mismatch (another plant layout, time-of-day behaviour, causes outside the 17) is invisible to it.

## Addendum 7 (2026-10-09, written BEFORE the full run): condition the engine on facts read at the door

**Question.** Idea 7 of the robustness brief. Addendum 6 showed that widening the likelihoods (refit on the broad family, `R_A`) ties `B_robust` but does not beat it, and that the strongest drivers of confident errors are mostly facts a technician can read on arrival (cold-side static pressure above all; TMV set point and margin; pipe length; dead leg). Does making each (hypothesis, check) likelihood mean depend on those facts, instead of widening it, buy accuracy and fewer confident errors that survive noisy fact entry? Simulation only.

**Design** (`conditioning.py`; constants in `COND_CONFIG`, hash below; `scripts/06_conditioning.py`, expected about 20-25 min).
(1) *Readings collected once.* A family world (the Addendum 6 broad family, 600 plants, instrument error x1.5, 25% hidden crossover) gives, for each of the 28 hypotheses and 21 checks, readings tagged with their plant, drawn from exactly the streams `engine.fit` uses (a test confirms the unconditioned fit reproduces `engine.fit`).
(2) *A ladder fitted on the same readings.* `R`: no facts (the control). `C1`: cold-side static pressure. `C3`: the three arrival-knowable facts with the largest Addendum 6 profile statistic (`p_cold`, `tmv_margin_min`, `len_scale`). `C15`: the fifteen `ARRIVAL` facts of Addendum 6. `O`: oracle, all 25 design parameters (not obtainable in a building; the ceiling). Each (hypothesis, check) mean is a ridge regression (lambda 1) of the reading on the standardised facts and their squares, with the predicted mean clipped to the readings seen in fitting; the residual sd replaces the pooled sd (floored at the check's minimum). Facts are clipped to the range seen in fitting, so the model does not extrapolate; an unknown fact is imputed at its population mean. Relative readings (a temperature minus a set point) are the special case of a unit coefficient. Facts only shift the means of readings; they are never treated as evidence about the cause.
(3) *What the technician can read.* Gauge and controller values (static pressure, heater set point as displayed, TMV set point, deadband, dead-leg length, ambient and cold-water temperature, valve type) come from the **faulted** plant, so a cause that changes them is seen; nameplate and design facts (heater capacity, storage volume, TMV minimum margin, relative pipe length, design dT, return floor, pump rating) come from the design values. *Noisy entry* (`FACT_NOISE`, ANALYST): gauge, set point and temperature readings with small error; estimates (pipe length 20%, dead leg 25%, capacity and storage 10%, pump rating 15%) with larger; each fact unknown with a stated probability (up to 40%) and then imputed at the population mean; each known fact entered wrongly (a uniform draw over the family range) with probability 0.05. **The decision test uses noisy facts**; clean facts are the upper bound. Intake time is charged to every visit of a conditioned variant (`INTAKE_MIN`: C1 2 min, C3 4 min, C15 10 min; ANALYST).
(4) *Test sets* (fresh seeds, nothing selected on them): held-out broad family (6 worlds x 200 plants), extrapolation family (2 worlds, a full span beyond), and the five Addendum 3 worlds at their original seeds and cases. Wrong readings are drawn from the matched engine's likelihoods for every variant. Candidates (with noisy facts): `C3_A`, `C3_B`, `C15_A`, `C15_B` (engine settings A or B on the conditioned likelihoods), against `A_plain`, `B_robust`, and the controls `R_A`, `R_B` (same readings, no facts).

**Predictions (frozen)**
- **Q1** (the ceiling is worth having): on the held-out family the oracle `O_A` has top-1 at least 0.08 above `R_A`.
- **Q2** (arrival facts help, clean): `C15_A` has top-1 at least 0.03 above `R_A` and wrong-and-confident no more than 0.005 above `R_A`'s.
- **Q3** (how much of the ceiling is knowable): `C15_A`'s top-1 gain over `R_A` is at least half of `O_A`'s gain. *(coin flip: several top drivers, such as `tmv_sag_gain` and `ua_mult`, cannot be read at the door)*
- **Q4** (a short intake is enough): `C3_A`'s gain over `R_A` is at least half of `C15_A`'s. One-fact (`C1_A`) gain is reported, not scored.
- **Q5** (fact errors do not erase it): with noisy facts `C15_A` keeps at least half of its clean gain over `R_A`, with wrong-and-confident no more than 0.02 above `R_A`'s.
- **Q6** (improvement over the incumbent): at least one of `C3_A`, `C3_B`, `C15_A`, `C15_B` (noisy facts) passes **all five**: (i) held-out wrong-and-confident <= `B_robust`'s + 0.01; (ii) held-out top-1 >= `B_robust`'s + 0.03, or confident share >= `B_robust`'s + 0.05; (iii) matched-world top-1 >= `A_plain`'s - 0.05; (iv) wrong-and-confident <= `B_robust`'s + 0.01 in composite_1.00 and technician_error; (v) held-out minutes including intake <= 1.15 x `B_robust`'s. *(I put this below even odds: Addendum 6's guard found no knowable pocket that was much worse than the rest, so the failures look diffuse.)*
- **Q7** (extrapolation): on the extrapolation family `C15_A` (noisy facts) has wrong-and-confident no higher than `A_plain`'s.
- **Q8** (matched cost): `C15_A` (noisy facts) in the matched world has top-1 >= `A_plain`'s - 0.05 and wrong-and-confident <= 0.05.
**Decision rule:** the passing candidate of Q6 with the lowest held-out wrong-and-confident; if none passes, `B_robust` stays and the finding is "no improvement". Top-1 differences under about 0.02 are inside sampling error; the report gives paired intervals from resampling whole plants.

**Disclosed before freezing.** I ran the whole pipeline once at tiny sizes (40-plant worlds, an 80-plant fit) only to confirm that it runs; its output went to a file and **I did not read the scorecard or any number from it**. The unit tests confirm that the unconditioned fit reproduces `engine.fit` exactly, that the ridge recovers a planted dependence, that conditioning clips unseen values, and that gauges are read from the faulted plant. The choice of `C3` uses the Addendum 6 statistic (search set), not any held-out result. Addendum 6's `R_A` used 400 fit plants; the control here is refitted on the same 600-plant readings as the conditioned variants.

**Not claimed.** Nothing here measures a building. The facts' noise model, unknown-probabilities and intake minutes are my estimates, so the noisy-fact result tests *a* plausible amount of entry trouble, not the real one. Whether a technician records these facts correctly, and whether the real relationships between facts and readings look like the simulator's, are untested. The conditioned engine ignores what the facts say about the cause, which is conservative.

Hash of the conditioning configuration (`conditioning.frozen_hash()`; includes the Addendum 6 and engine hashes): `c83bbabac1b0652914531dcf67d57bfc181dcd066dd282b4e6205e66a24a4ccd`.

## Result of Addendum 7 (2026-10-09; `scripts/06_conditioning.py`, 1,098 s; hash as above; `output/CONDITIONING_REPORT.md`, `conditioning.json`, `conditioning_variants.csv`)

Simulation only. Fit on 600 family plants; 6,534-visit held-out family, 2,238 extrapolation visits, the five Addendum 3 worlds. Minutes include intake time.

| # | Prediction | Result |
|---|---|---|
| Q1 | oracle conditioning (all 25 design parameters) gains >= 0.08 top-1 over no conditioning | **fails**: 0.638 against 0.590, +0.047 [+0.034, +0.061]. My expectation was wrong: even knowing every plant parameter buys little with this regression form |
| Q2 | 15 arrival facts (clean) gain >= 0.03 top-1 and wrong-and-confident within +0.005 | **fails**: +0.022 [+0.008, +0.036], but wrong-and-confident 0.070 against 0.038 |
| Q3 | arrival facts capture >= half of the ceiling's gain | **fails narrowly**: 46% (+0.022 of +0.047) |
| Q4 | 3 facts capture >= half of the 15-fact gain | **fails narrowly**: 44% (+0.010 of +0.022). One fact, `p_cold`, alone gives +0.016, more than three facts do |
| Q5 | noisy, missing and wrong fact entries keep >= half the clean gain, wrong-and-confident within +0.02 | **fails badly**: top-1 0.548, which is 0.042 *below* the engine with no facts (0.590), and wrong-and-confident 0.106 |
| Q6 | some candidate beats `B_robust` under the frozen rule (i)-(v), noisy facts | **fails**: `C15_A` is confidently wrong 10.6% of the time (B: 3.2%); `C15_B` and `C3_B` match B's safety and top-1 but are decisive less often (0.19 and 0.16 against 0.23) and lose 0.04-0.09 matched top-1 (iii); `C3_A` is confidently wrong 5.5% |
| Q7 | extrapolation family: `C15_A` no worse than A | **holds**: 0.170 against 0.204 (clipping the facts to the fitted range prevents blow-up; still far worse than the unconditioned refit's 0.062) |
| Q8 | matched world: `C15_A` top-1 within 0.05 of A, wrong-and-confident <= 0.05 | **fails by 0.001**: 0.713 against 0.714 needed; wrong-and-confident 0.047 |

**Recommendation by the frozen rule: `B_robust` stays; no improvement.** 1 of 8 predictions holds.

Held-out broad family:

| variant | top-1 | wrong-and-confident | confident | ECE | minutes |
|---|---|---|---|---|---|
| A_plain | 0.507 | 0.142 | 0.45 | 0.274 | 47 |
| B_robust | 0.575 | 0.032 | 0.23 | 0.147 | 54 |
| R_A (no facts) | 0.590 | 0.038 | 0.26 | 0.077 | 52 |
| C1_A (clean) | 0.606 | 0.048 | 0.29 | 0.080 | 55 |
| C3_A (clean) | 0.600 | 0.048 | 0.30 | 0.089 | 56 |
| C15_A (clean) | 0.612 | 0.070 | 0.38 | 0.136 | 58 |
| O_A (oracle) | 0.638 | 0.072 | 0.43 | 0.130 | 46 |
| C3_A, noisy facts | 0.578 | 0.055 | 0.30 | 0.113 | 56 |
| C15_A, noisy facts | 0.548 | 0.106 | 0.39 | 0.210 | 58 |
| C3_B, noisy facts | 0.576 | 0.022 | 0.16 | 0.063 | 61 |
| C15_B, noisy facts | 0.573 | 0.030 | 0.19 | 0.100 | 63 |

What the ladder says (not predicted): (1) **conditioning sharpens the engine faster than it improves it**: every added fact raises the confident share and the confident-error rate more than top-1, and calibration gets worse (ECE 0.077 with no facts, 0.136 with 15, 0.130 for the oracle). (2) **Realistic fact entry cancels the gain and then some**: a wrong or imputed fact shifts every likelihood mean, and the sharpened engine does not notice. (3) **`p_cold` carries most of what there is** (regression weight 0.41, then `t_set_tmv` 0.21, `t_set_heater` 0.20; `tmv_margin_min` and `len_scale`, the other two of `C3`, 0.06 each). (4) **The family gap is not mostly about plant parameters**: A reaches 0.76 matched and 0.51 on the family, and even the oracle only reaches 0.64; what remains is per-visit trouble (instrument error, skipped and misread checks, hidden crossover) and the 11% of plants that already complain when healthy.

**Caveat on the ceiling.** The oracle uses a linear-plus-quadratic regression per hypothesis and check. If the real dependence of readings on parameters is strongly nonlinear (a threshold in time-to-hot, a regime switch in the TMV), a plant-specific physics prediction could do better than +0.047; this study cannot say. The bound that would settle it is a *physics oracle* (simulate every hypothesis on the case's own plant), which was not run.

## Addendum 8 (2026-10-09, written BEFORE the full run): tenant answers as soft evidence

**Question.** Idea 8 of the robustness brief. The three tenant questions (Q1 which floors, Q2 peak-only, Q3 warm cold taps) are free and asked first; Addendum 4 showed that removing Q1 alone costs 0.06 top-1 and doubles confident errors. Their reliability (Q1 off by one riser 15% of the time, Q2 and Q3 with small Gaussian noise) is a guess, and a Gaussian likelihood lets a single contradicting answer nearly eliminate the true cause. How bad does it get when tenants are less reliable than assumed, where is the point at which asking stops paying, and does treating tenant answers as soft evidence (they may reorder hypotheses but not eliminate them; physical readings keep full authority) fix it? Simulation only.

**Design** (`tenants.py`, engine options `q_eps` and `p_tenant`; constants in `TEN_CONFIG`, hash below; `scripts/07_tenants.py`, expected about 20 min).
(1) *Tenant unreliability dial.* With probability p each tenant answer (Q1-Q3, whenever asked) is unrelated to the plant: it is drawn from a randomly chosen hypothesis's likelihood (the matched engine's, the same source as technician misreads), on top of the built-in noise. Not modelled: systematic over-reporting, partial answers, yes/no phrasing.
(2) *Soft evidence.* With `q_eps` = eps, a tenant answer's likelihood under each hypothesis is (1 - eps) x its density + eps x the density of the broad "other" hypothesis (pooled mean, wide spread); the information-gain calculation uses the same mixture, so a doubted question is worth less. Physical checks are untouched.
(3) *Variants* (engines fitted once on the matched world as in Addendum 3): `A_plain` and `B_robust` (trust the answers as fitted); `NoQ_A`, `NoQ_B` (never ask the tenants); `S15_A`, `S30_A`, `S50_A` (soft evidence with eps 0.15, 0.30, 0.50, engine A settings); `S30_B` (eps 0.30 with B's settings).
(4) *Sets and levels.* Matched replicate worlds (4 x 100 plants, fresh seeds, original ranges): p in {0, 0.15, 0.30, 0.50, 0.70}. The Addendum 6 broad family (4 x 200 plants, fresh seeds, with its per-visit trouble): p in {0, 0.30, 0.60}. All variants run on identical visits and seeds at each p.

**Predictions (frozen)**
- **T1** (asking pays when tenants are reliable): matched, p = 0: `A_plain` top-1 is at least 0.08 above `NoQ_A`.
- **T2** (trusting breaks): matched, p = 0.50: `A_plain` wrong-and-confident is at least twice its p = 0 value and at least 0.05.
- **T3** (a break-even exists): on the matched set there is a p <= 0.70 at which `NoQ_A` top-1 is at least `A_plain`'s (reported: the lowest such p).
- **T4** (soft evidence protects): matched, p = 0.50: `S30_A` wrong-and-confident <= 0.7 x `A_plain`'s, with top-1 not lower by more than 0.01.
- **T5** (soft evidence is cheap when tenants are fine): matched, p = 0: `S30_A` top-1 not lower than `A_plain`'s by more than 0.03, wrong-and-confident not higher by more than 0.01.
- **T6** (improvement over the incumbent): at least one of `S15_A`, `S30_A`, `S50_A`, `S30_B`, `NoQ_B` passes **all four**: (i) over the broad-family levels (equal weights) mean wrong-and-confident <= `B_robust`'s + 0.01; (ii) mean top-1 >= `B_robust`'s + 0.03, or mean confident share >= `B_robust`'s + 0.05; (iii) matched p = 0 top-1 >= `A_plain`'s - 0.05; (iv) matched p = 0.70 wrong-and-confident <= `B_robust`'s + 0.01. *(Below even odds: B already widens every likelihood.)*
- **T7** (B is already robust to tenants): matched, `B_robust`'s wrong-and-confident at p = 0.50 is within +0.03 of its value at p = 0. *(Coin flip; I lean no, because variance inflation does not bound a Gaussian tail.)*
**Decision rule:** the passing candidate of T6 with the lowest mean broad-family wrong-and-confident; if none passes, `B_robust` stays and the finding is "no improvement". The report also gives, for the main contrasts, paired intervals from resampling whole plants.

**Disclosed before freezing.** I ran the whole pipeline once at tiny sizes (one 40-plant world per set, two levels) only to confirm that it runs; the output went to a file and **I did not read any number from it**. The engine gained two additive options (`q_eps`, `p_tenant`) whose defaults leave every earlier result unchanged; unit tests check that the defaults reproduce the old behaviour and that soft evidence bounds the effect of one wild tenant answer and changes only tenant checks.

**Not claimed.** Nothing here measures real tenants. The dial shows how the engine degrades if answers are unrelated to the plant with probability p; it says nothing about how often that is true, about answers that are *consistently* biased, or about yes/no phrasing. Q2 and Q3 are numeric stand-ins for yes/no questions.

Hash of the tenant configuration (`tenants.frozen_hash()`; includes the Addendum 6 hash): `4eda1c1271aacaebc25bae42444665d962e6604de6fcbb5bbc67915079e36e00`.

## Result of Addendum 8 (2026-10-09; `scripts/07_tenants.py`, 1,174 s; hash as above; `output/TENANTS_REPORT.md`, `tenants.json`, `tenants_variants.csv`)

Simulation only. Matched replicate worlds (2,400 visits) and the held-out broad family (about 4,300 visits), each variant on identical visits at each tenant-unreliability level p.

| # | Prediction | Result |
|---|---|---|
| T1 | with reliable tenants, trusting beats never asking by >= 0.08 top-1 | **fails**: 0.750 against 0.707, +0.043 [+0.024, +0.063]. Asking saves 20 minutes (40 against 60) but is worth less accuracy than I expected |
| T2 | at p = 0.50 trusting doubles confident errors (and >= 0.05) | **holds**: 0.147 against 0.034 |
| T3 | a break-even exists below p = 0.70 | **holds**: never asking ties trusting at p = 0.15 (0.700 against 0.702) and wins from p = 0.30 (0.699 against 0.641). Trusting only pays if about 85% or more of the answers carry information |
| T4 | soft evidence cuts confident errors to <= 0.7x at p = 0.50 without losing top-1 | **holds**: `S30_A` 0.054 against 0.147, top-1 0.729 against 0.576 (+0.153 [+0.133, +0.172]); it beats never asking (0.703) even with half the answers garbage |
| T5 | soft evidence is cheap when tenants are fine | **holds**: `S30_A` top-1 0.749 against 0.750, wrong-and-confident 0.038 against 0.034 (but +8 minutes: 48 against 40) |
| T6 | some candidate beats `B_robust` under the frozen rule | **holds**: `S30_B` passes (i)-(iv); `S15_A` and `S30_A` fail (i) (the A settings keep the broad family's confident errors at 0.12-0.14) and `NoQ_B` fails (ii) and (iii) |
| T7 | `B_robust` is already robust to tenant error | **fails**: its wrong-and-confident rises from 0.006 at p = 0 to 0.053 at p = 0.50 and 0.070 at p = 0.70 |

**Recommendation by the frozen rule: `S30_B`** (B's settings plus soft tenant evidence at eps 0.30). 5 of 7 predictions hold.

`S30_B` against `B_robust` (paired, 95% interval from whole plants):

| set | p | d top-1 | d wrong-and-confident |
|---|---|---|---|
| matched | 0 | -0.009 [-0.019, +0.001] | +0.000 [-0.002, +0.002] |
| matched | 0.15 | +0.032 [+0.019, +0.045] | -0.015 [-0.021, -0.010] |
| matched | 0.30 | +0.061 [+0.044, +0.077] | -0.032 [-0.039, -0.024] |
| matched | 0.50 | +0.098 [+0.081, +0.112] | -0.046 [-0.053, -0.037] |
| matched | 0.70 | +0.152 [+0.134, +0.169] | -0.062 [-0.072, -0.052] |
| broad family | 0 | +0.009 [-0.001, +0.019] | -0.007 [-0.011, -0.002] |
| broad family | 0.30 | +0.055 [+0.041, +0.068] | -0.025 [-0.031, -0.019] |
| broad family | 0.60 | +0.089 [+0.076, +0.103] | -0.041 [-0.048, -0.035] |

What it costs and what it does not fix: (1) with reliable tenants `S30_B` is a tie with B on accuracy and safety and spends **6-9 more minutes per visit** (matched 54 against 48; broad family 61 against 55), because a doubted question is worth less so the engine goes to physical checks sooner; the gain is insurance against unreliable tenants. (2) The first question asked is still Q2 in every variant. (3) The A settings with soft evidence still leave the broad family at 12-14% confident errors; soft evidence fixes tenant error, not the family's other trouble. (4) eps 0.15, 0.30 and 0.50 behave similarly (eps 0.50 loses about one point at p = 0); 0.30 is a reasonable default, not a tuned one.

**Caveat that matters.** The tenant error in this test is a plant-independent random answer, which is exactly the process the soft-evidence mixture assumes, so the result is partly favourable by construction. A consistent bias (every tenant over-reports, or "all floors" whenever there is any complaint) is the harder and more realistic case, and soft evidence would not protect against it; that test was not run. Q2 and Q3 are numeric stand-ins for yes/no answers.

## Addendum 9 (2026-10-09, written BEFORE any extraction): what manufacturers' own documents say, against the matrix

**Question.** Idea 4 of the robustness brief. Every number in the simulator is ours; the one independent source we can reach without field data is what manufacturers write in their own troubleshooting documents. Do they name the causes in our taxonomy and the checks in our catalogue? Where a document says a check reveals a cause, does the Addendum 1 matrix agree (presence and direction)? Which causes and checks do manufacturers use that we lack, and which of our causes do they barely mention? Documents, not simulation. Earlier research (`research_notes/Hot water recirculation diagnostic inputs/`) read in full only the Powers (Watts) TI430-420 table and the Caleffi 1164 guide; Taco, Grundfos, A. O. Smith, Lochinvar, Armstrong and others were unreadable or seen only as search summaries, so most of this is new reading.

**Design** (`oem.py`, `scripts/08_oem_compare.py`; constants in `OEM_CONFIG`, hash below).
(1) *Readers.* Four independent readers, each given the same brief (`data/reader_brief.md`; sha256 below), one document class each: **H** water heaters and boilers (A. O. Smith, Bradford White, Lochinvar, Rheem or Ruud commercial, PVI, indirect tanks and plate heat exchangers); **M** thermostatic mixing valves (Powers or Watts, Leonard, Symmons, Lawler, Armstrong, Taco, Caleffi, Honeywell or Resideo); **P** recirculation pumps, aquastats and controls, balancing valves, check valves (Taco, Grundfos, Bell and Gossett or Xylem, Armstrong, Caleffi, Watts, Wilo, Honeywell); **S** system-level hot-water recirculation and complaint guides, thermal expansion, PRVs and strainers from any of the above. Each targets 25-40 rows from at least 5 documents and 3 manufacturers.
(2) *Access and licensing rules.* WebSearch and WebFetch only; nothing downloaded or saved; no logins or paywalled documents; documents unreadable through those tools are listed and skipped, never guessed. Only paraphrase plus a locator and an anchor of at most 8 verbatim words is stored; no document text. The documents are copyrighted and their terms of use have not been reviewed by a lawyer; the claims file is an internal research artifact and is not to be redistributed.
(3) *Schema and mapping* as in `oem.SCHEMA`, `DOC_TYPES`, `PRODUCT_CLASSES`, `SYMPTOMS` and the reader brief: each row is one symptom-cause-check-observation statement, mapped to one of our 17 causes (`NEW:<slug>` or `OUT_OF_SCOPE` if none fits) and one of our 23 checks (`NEW:<slug>` or `NONE`), with a direction for the checked quantity. **Scored rows** are `DIRECT` (the document itself states the relation) and `READ_FULL` (the passage text itself was retrieved), not dropped by verification, duplicates counted once.
(4) *Verification.* A sample of 25% of scored rows (at least 25, at most 60; seeded draw, `OEM_CONFIG["VERIFY"]`) is re-read by an independent verifier (`data/verifier_brief.md`; sha256 below) who sees the paraphrase, locator and anchor but **not** the reader's ids or direction, decides `CONFIRMED`, `PARTLY`, `NOT_FOUND` or `UNREADABLE`, and independently maps the cause, check and direction (blind re-mapping). Rows found `NOT_FOUND` are dropped from the scored set.
(5) *Comparison.* For every scored row naming one of our 17 causes and a physical check, the matrix cell is looked up. "The matrix sees it" uses the rule already used for source claims: class DET_SEEN, or PARAM or NEEDS_ELIC with p_sep >= 0.5. Direction is compared only when the cell is seen, its median sign is not 0 and the row has a direction of +1 or -1. A *candidate correction* is a direction conflict, or two or more manufacturers saying a check reveals a cause the matrix calls DET_NOT_SEEN. **Nothing in the matrix or engine is changed by this study**; corrections need their own pre-registered addendum and rerun.

**Predictions (frozen; bars in `OEM_CONFIG["BAR"]`)**
- **O1** (coverage): at least 60% of scored rows map onto one of our 17 causes.
- **O2** (presence): of scored rows naming one of our causes and a physical check, the matrix sees the pair in at least 70%. *(I expect this to fail: manuals tell you to check things such as the power supply or the thermostat setting that our catalogue lacks or classes as not seen.)*
- **O3** (direction): at least 85% of comparable rows agree in direction.
- **O4** (taxonomy gaps): at least 2 new causes each supported by at least 2 manufacturers.
- **O5** (check gaps): at least 2 new checks each supported by at least 2 manufacturers.
- **O6** (thin coverage): at least 5 of our 17 causes have at most 1 scored row. *(I expect loop-level causes, crossover and insulation loss among them: manuals describe their own product.)*
- **O7** (extraction quality): at least 85% of verifiable sampled rows are `CONFIRMED`.
- **O8** (mapping is not arbitrary): the verifier's blind cause id equals the reader's for at least 80% of verified rows.
- **O9** (the comparison finds something): at least one candidate correction.
**Floor.** If fewer than 60 scored rows or fewer than 5 manufacturers result, O1-O6 and O9 are reported as descriptive only (no yes or no) and the study is called inconclusive on those points.

**Disclosed before freezing.** No extraction, probe or sample reading has been done for this study. The matrix cells used for comparison come from the Addendum 1 run; the two cells already backed by Powers and Caleffi text are not excluded (a reader may extract the same Powers table again, and duplicates within a document are counted once). Readers and verifiers are language-model agents that can err and may be wrong about what a document says; that is what the verification sample estimates. The frozen hash covers the schema, vocabulary, rules and bars; the briefs are hashed separately.

**Not claimed.** A mention in a manual says a cause exists and how a manufacturer suggests checking it, not how often it happens, and the documents are about the manufacturer's own product and mostly not about building-level loop causes. Agreement with manuals is not validation against buildings.

Hash of the OEM configuration (`oem.frozen_hash()`; includes the Addendum 1 thresholds hash): `7f6b2231e0ef94b6b8eb1bd3dcf88228f2231a97001e79f0b697473f3325d26d`. sha256 of `data/reader_brief.md`: `8d2f2167921c6418a83152a00c87c1d2608feeb416aafd39a45a75e082c3a1ec`. sha256 of `data/verifier_brief.md`: `180bcf7bdd76fc6d9554e350f20fd420fe4c7b9d12298e9d2f3c222825b21759`.

## Result of Addendum 9 (2026-10-09; `scripts/08_oem_compare.py`; hash as above; `output/OEM_REPORT.md`, `OEM_REPORT_no_proxy.md`, `oem_comparison.csv`; claims in `data/oem_claims.csv`, verification in `data/oem_verification.csv`)

Documents, not simulation. 177 rows extracted by four readers; **157 scored** (DIRECT and fully read) from **25 manufacturers**, 118 of them naming one of our 17 causes. A 39-row verification sample was re-read blind by two verifiers.

| # | Prediction | Result |
|---|---|---|
| O1 | at least 60% of scored rows map onto one of our 17 causes | **holds**: 75% (118 of 157); 71% without the proxy-read rows |
| O2 | the matrix sees at least 70% of (cause, check) pairs the documents name | **fails**: 39% (9 of 23). Nine of the 14 misses are one cluster, see below |
| O3 | direction agrees in at least 85% of comparable rows | **holds, with almost no power**: 6 of 6 (3 of 3 without proxy rows) |
| O4 | at least 2 new causes supported by 2+ manufacturers | **holds**: 5 (29 new cause slugs in all) |
| O5 | at least 2 new checks supported by 2+ manufacturers | **holds**: 6 (49 new check slugs in all; 3 without proxy rows) |
| O6 | at least 5 causes have 1 or fewer scored rows | **fails with the proxy rows (2 causes: `dip_tube_short_circuit`, `fixture_branch_local`), holds without them (6 causes)**: the result depends on the 33 rows I could not verify |
| O7 | at least 85% of verifiable sampled rows confirmed | **fails**: 24 of 31 (77%); 7 partly, **0 not found**, 8 unreadable |
| O8 | blind cause mapping agrees for at least 80% | **fails**: 71% on the frozen metric; 7 of the 9 disagreements are two spellings of the same new slug (for example `very_cold_inlet_water` against `cold_inlet_water_temp_low`); a post-hoc count that treats those as equal gives about 29 of 31 (94%), not part of the frozen result |
| O9 | at least one candidate correction | **holds**: one (below) |

5 of 9 predictions hold. **Verification by class**: heaters 10 of 11 confirmed, mixing valves 10 of 12, system guides 3 of 7 (4 partly: the weakest class, where the fetch tool summarised pages), pumps and valves **8 of 9 unreadable** (35 of 44 rows of that class came from PDFs read through the unauthorised proxy and could not be re-read), so that class is essentially unverified. No sampled row was fabricated.

What the documents say about the model (candidate changes; **nothing was applied**):
1. **The one candidate correction is a catalogue gap, not a physics error.** Nine rows from five manufacturers (Watts, Powers, Bradley, Symmons, Leonard) say the same thing about thermostatic mixing valves: if the hot supply is not far enough above the valve's set point, the valve cannot hold temperature, and the check is to measure hot supply against the set point. The matrix calls (`tmv_setpoint_wrong`, K01) not seen: in the simulator that cause moves the TMV set point toward the heater temperature, while K01 reads the heater outlet temperature alone. A hot-supply *margin* reading (heater outlet minus TMV set point) is what the manuals describe and what our catalogue lacks. Stated margins are 2, 5, 10, 15, 20 and 25 F depending on the valve family (our parameter range is 15 to 25 F); the lowest come from small or point-of-use valves, so this does not by itself argue for changing the range, but it does say the margin is valve-specific and should be read off the valve model.
2. **Our two TMV causes are coarse.** Manufacturers separate roughly seven TMV failure modes; the ones that matter for a recirculating plant are operation **below the valve's minimum flow**, **temperature creep or droop caused by the return and bridge arrangement**, a **failed thermal element**, a hot inlet that does not close off at no draw, and reversed supplies.
3. **Whole families are outside the model**: primary-side flow problems on indirect tanks (Amtrol, Triangle Tube), over-temperature (stacking, set point too high, grounded element), and thermal-expansion overpressure with relief-valve discharge.
4. **Most manufacturer checks are component tests we do not have** (element resistance, thermostat or ECO continuity, contactor voltage, power supply, indicator-LED codes, flow arrows, bypass-valve shut-off): of 118 mapped rows only 23 name one of our physical checks. The heater-side pairs the documents name are mostly consistent with the matrix (K01 and K11 with a faulty thermostat, K08 with a pump that runs but does not pump, K10 with controls faults, K13 with unbalanced branches).
5. **Coverage by cause**: heater output loss, sensor or thermostat faults, TMV fouling and balancing valves have 12 to 14 rows each; `dip_tube_short_circuit` and `fixture_branch_local` have 1; `heater_setpoint_low` has 2; `crossover` 4 rows from 2 manufacturers.

**Limits.** Heater and mixing-valve rows were read from third-party mirror copies of manuals (ManualsLib, ManualsDir; 82 scored rows), some with scrambled tables where cause and remedy are paired by order or wording; the system-guide reader got a language model's answer from the fetch tool rather than the page; copyright and terms of use have not been reviewed by a lawyer; a mention in a manual says a cause exists, not how often. This study cannot say how accuracy would change: any of these additions would be new causes or checks that the simulator would itself define, so a rerun measures consistency, not agreement with buildings.

## Addendum 10 (2026-10-10, written BEFORE the full run): what does the engine do when the true cause is not in its list?

**Question.** Every earlier stress test used true causes that were inside the engine's 17. Real plants will have causes outside it: the manufacturer-document study (Addendum 9) found about seven mixing-valve failure modes we lack, and the literature on deployed diagnostic systems reports never-seen root causes in roughly a quarter of incidents (one cloud-service year) and large accuracy loss when important nodes are missing (a medical network lost 0.11 AUC with 20% of important nodes removed). How often is the recommended engine (S30_B) confidently wrong when the truth is absent, does it ever say "other", can the "other" setting be tuned to help without hurting ordinary visits, and what does adding the best-evidenced missing causes cost and fix? Simulation only.

**Design** (`novelty.py`, `scripts/10_unmodelled.py`; constants in `NOVEL_CFG`, hash below; about 10 minutes).
(1) *Leave-one-cause-out (LOCO).* For each of the 17 causes with at least 15 single-fault test visits, the engine is built without that cause (and without every pair containing it; the "other" hypothesis is recomputed from what is left) and tested on visits where that cause is the truth. Test visits: 4 matched replicate worlds of 100 plants, fresh seeds. No physics is invented.
(2) *Outcomes.* A confident call is **wrong** only if it names a specific cause whose group (plant, mixing valve, recirculation hydraulics, crossover and pressure, fixture, controls) differs from the truth's; a confident call inside the truth's family is *acceptable* (the action is plausibly right); a confident "other" and an abstention are acceptable.
(3) *"Other" settings* (all on S30_B except the plain-A reference): prior mass on "other" 0.10 (S30_B), 0.20, 0.30; spread of "other" 1.5x (S30_B) or 3x; and 0.20 with 3x.
(4) *Two manufacturer-sourced causes written into the simulator* (new plant attributes, neutral by default; with the neutral defaults the full Addendum 3 stress table reproduces exactly): `tmv_below_min_flow` (the valve's minimum flow is 1.3 to 3.0 times the loop's design flow, so at idle the outlet sags by up to 25 F times severity, and not at peak) and `tmv_unregulated` (failed thermal element, hot fraction stuck at 0.45 to 0.80; or supplies reversed, 0.00 to 0.25). Effect sizes are placeholders. They are added to the test worlds only; then the engine is refitted with them added (19 causes) to measure what adding them costs on ordinary visits and fixes on theirs. That last fix is mechanical (the simulator defines both the test and the new rows) and is not evidence of agreement with buildings.
(5) *Selection of an "other" setting:* among the variants other than the plain-A reference and S30_B, those whose ordinary-visit top-1 is at most 0.02 below S30_B's, wrong-and-confident at most 0.01 above, and confident share at most 0.05 below are admissible; the admissible variant with the lowest mean wrong-family rate is chosen; it counts as an improvement only if it cuts S30_B's mean wrong-family rate by at least 30%.

**Predictions (frozen; bars in `NOVEL_CFG["BAR"]`)**
- **N1** (exposure): averaged over the held-out causes, S30_B is confidently wrong-family in at least 5% of visits.
- **N2** ("other" is rarely said): confident "other" in at most 5% of those visits.
- **N3** (concentration): the 5 worst-hit causes hold at least 50% of the wrong-family mass.
- **N4** (tuning helps): the selected admissible setting cuts the wrong-family rate by at least 30%.
- **N5** (tuning is not enough): the selected setting still leaves at least 3% wrong-family.
- **N6** (the sourced causes are a real exposure): for at least one of the two sourced causes, S30_B without them is confidently wrong-family in at least 10% of their visits. *(Unsure: both belong to the mixing-valve family, where the engine already has two causes, so many calls may be acceptable.)*
- **N7** (adding them is cheap): the 19-cause engine's ordinary-visit top-1 is at most 0.02 lower and its wrong-and-confident at most 0.01 higher than the 17-cause engine's.
- **N8** (adding them fixes their visits; mechanical): top-1 on the two causes' visits at least 0.60 and wrong-family at most 3%.
**Decision rule:** if the selected setting is an improvement (N4), it is recommended as the engine's "other" setting; the two sourced causes are recommended for the engine only if N7 holds; nothing is applied to the code defaults by this study.

**Disclosed before freezing.** I added three neutral-by-default attributes to the plant and three lines to the mixing-valve block; the Addendum 3 stress test rerun after the change reproduces `engine_stress.csv` exactly. I ran the pipeline once at tiny sizes only to confirm it runs; its output went to a file and I read no number from it. I have not looked at any leave-one-out result.

**Not claimed.** Nothing here says how often unmodelled causes occur in buildings (the literature figure is from a different domain) or how the engine behaves on any particular real cause. The groups are my consolidation. Placeholders define the sourced causes' effect sizes.

Hash of the novelty configuration (`novelty.frozen_hash()`; includes the Addendum 6 hash): `217e1bb9a147f86cb5e6c0684321001572a659bb88b93ab7863da7a621e884dc`.

## Addendum 11 (2026-10-10, written BEFORE the full run and before any language-model ranking exists): what is a weak prior over causes worth?

**Question.** Cause frequencies were the most valuable unknown input in Addendum 4 (an oracle prior: +0.095 top-1) while a random wrong prior cost 0.006 on average, an asymmetry that suggests a weak sourced prior could be cheap insurance. How right must a prior be before it pays, how much does shrinking it toward uniform protect, and do independent weak public sources agree enough to build one at all? Simulation plus a source-agreement check; the simulator cannot say how right a sourced prior would be.

**Design** (`priors.py`, `scripts/11_priors.py`; constants in `PRIOR_CFG`, hash below; about 20 minutes).
(1) *Value curve.* True case mixes over the causes are drawn from a Dirichlet (skewed, alpha 0.5; flatter, alpha 1.0), 6 mixes each. A prior's log-weights correlate with the true log-weights at **rho** in {-1, -0.5, 0, 0.25, 0.5, 0.75, 1} (-1 = reversed, 0 = unrelated, 1 = exact) and have the same spread; shrink weight 1.0 (as is) or 0.5 (half toward uniform, at rho in {-1, -0.5, 0, 0.5, 1}). Test visits: the four matched replicate worlds' single-fault visits resampled to the true mix (500 per mix) plus all two-fault visits. Engines A and S30_B (the recommended variant), each against the same engine with a uniform prior on identical visits and seeds.
(2) *Do weak sources agree?* Source **M**: the number of distinct manufacturers whose documents state each cause (Addendum 9 scored rows). Source **L**: five independent language-model rankings of the 17 causes from most to least frequent as the root cause of a persistent not-hot, lukewarm, slow or uneven complaint in commercial or multifamily plants with recirculation; each run sees the causes in a different shuffled order, may use no tools except one write, and may not read project files (prompts in `data/prior_sources/prompts.json`, sha256 below; the rankings are recall of what is written about the problem, not data, and are the weakest source). A prior is built only if **both** the Spearman correlation between M and the mean language-model rank is at least 0.30 **and** the mean pairwise Spearman among the five runs is at least 0.50; its weights are the standardised sum of M and the mean rank with a largest-to-smallest ratio of 4. Otherwise no sourced prior is built and uniform stays. (Component-reliability evidence in `research_notes/Hot water missing data sources/component_reliability.md` covers too few of the 17 causes to rank them and is not used.)
(3) *Shrinkage choice:* the shrink weight with the higher mean top-1 gain for S30_B over the plausible band rho in {-0.5, 0, 0.5} (skewed truth) is recommended if a prior is ever used.

**Predictions (frozen; bars in `PRIOR_CFG["BAR"]`)**
- **R1** (a random prior is harmless): at rho = 0 top-1 changes by at least -0.02 for both engines (skewed truth).
- **R2** (a moderately right prior pays): at rho = 0.5 S30_B gains at least +0.03.
- **R3** (an exact prior pays a lot): at rho = 1 S30_B gains at least +0.07.
- **R4** (the worst case is bounded): at rho = -1 S30_B's top-1 change is at least -0.10.
- **R5** (shrinking protects): shrinking by half at rho = -1 loses no more than 0.6 times the unshrunk loss, and at rho = 1 keeps at least half of the unshrunk gain (S30_B).
- **R6** (skew matters): the rho = 0.5 gain is larger under the skewed truth than the flatter one (S30_B).
- **R7** (it does not make the engine confidently wrong): at rho = -1 wrong-and-confident rises by at most 0.03 (S30_B).
- **R8** (a weak prior of unknown quality pays on average): over rho in {-0.5, 0, 0.5} the unshrunk prior's mean top-1 change is at least 0 (S30_B, skewed truth).
- **R9** (the sources agree enough): the agreement bars in (2) are met. *(Coin flip, leaning no: M reflects which documents I chose to read.)*

**Disclosed before freezing.** I ran the whole pipeline once at tiny sizes only to confirm it runs and read no number from it. I have not seen any language-model ranking. The sensitivity analysis' oracle and wrong-prior results are the only prior-related results I have seen.

**Not claimed.** A prior built here is an ordering of weak signals with no measured accuracy. Rho is the correlation of log-weights; a real prior also errs in scale, and the Dirichlet truths are my assumption about how skewed real frequencies are.

Hash of the prior configuration (`priors.frozen_hash()`; includes the Addendum 6 hash): `797d1748b65d67d25b35ddd42907ca94838d823321aba48ea84dada5e5eed0ff`. sha256 of `data/prior_sources/prompts.json`: `d4c852842cfa8ce5661e3d80f42cadcf8c8692bd7e2feed9d6922873ddce0d47`.

## Result of Addendum 10 (2026-10-10; `scripts/10_unmodelled.py`, 227 s; hash as above; `output/NOVELTY_REPORT.md`, `novelty_loco.csv`, `novelty.json`)

Simulation only. 15 causes held out in turn (136 visits each, 72 for insulation loss; pump under-sizing and cold-side pressure had too few symptomatic visits), 2,400-visit ordinary set, 240 visits of the two sourced causes.

| # | Prediction | Result |
|---|---|---|
| N1 | with the true cause absent, S30_B is confidently wrong-family in at least 5% of visits | **fails, in the engine's favour**: 0.6% (plain engine A: 9.9%). S30_B abstains in 78% of those visits |
| N2 | confident "other" in at most 5% | **holds**: 1.3% (it almost never says "other"; it abstains instead) |
| N3 | the 5 worst-hit causes hold at least 50% of the wrong-family mass | **holds trivially**: 100% of a total of 0.6% (4% for `tmv_starved_fouled`, 3% `dip_tube_short_circuit`, 1% for three others) |
| N4 | the selected "other" setting cuts the wrong-family rate by at least 30% | **holds technically**: `S30_B_po20_sd3` (0.20 on "other", 3x spread) 0.6% to 0.3%, an absolute change too small to matter |
| N5 | the selected setting still leaves at least 3% | **fails**: 0.3% (there is little left to remove) |
| N6 | at least one sourced cause is confidently wrong-family in 10% or more of its visits | **fails**: 0% for both (the engine without them abstains in 97% and 72% of their visits) |
| N7 | adding the two causes costs little on ordinary visits | **holds**: top-1 0.749 against 0.752, wrong-and-confident 0.008 against 0.006 |
| N8 | adding them fixes their visits (mechanical) | **holds, barely**: top-1 0.62 (0.86 and 0.39), wrong-family 0%; but the engine is still not confident in 78% and 75% of those visits |

5 of 8 predictions hold; three of them are the "problem is small" ones failing.

What the run says: (1) **the recommended engine protects itself against unmodelled causes by abstaining, not by saying "other"**: with the truth absent it commits to a wrong family in 0.6% of visits and abstains in 78%, against 9.9% and 50% for the plain engine A, which is the real safety margin of the soft-evidence, widened variant. (2) **The cost is time and no answer, not confident errors**: 67 minutes on average against 54 on ordinary visits. (3) **Causes with a distinctive signature are recognised as unknown** (crossover, check valves, fixture-level problems, mixing-valve set point: 88 to 100% abstention); causes with a close neighbour in the same group get absorbed into it (demand exceeds capacity 79%, pump control fault 66%, heater output loss 62% confident in the same family), which counts as acceptable here but may still be the wrong repair. (4) The two sourced mixing-valve modes are therefore not a confident-error risk; adding them makes the best guess right for 86% (below minimum flow) and 39% (unregulated) of their visits at no ordinary-visit cost, but the conservative engine stays unconfident, so they would mostly convert wrong abstentions into correct-but-hedged best guesses.

By the frozen rule the selected "other" setting is `S30_B_po20_sd3` and the sourced causes pass N7; **I would not change the engine for a 0.3 percentage-point effect**, and nothing was applied to the code defaults. Limits: groups are my consolidation; a confident call in the right family is counted acceptable; the sourced causes' effect sizes are placeholders; the test world is the matched simulator.

## Result of Addendum 11 (2026-10-10; `scripts/11_priors.py`, 1,662 s; hash as above; `output/PRIORS_REPORT.md`, `priors_curve.csv`, `priors.json`; language-model rankings in `data/prior_sources/L_1..5.json`)

Simulation plus a source check. 15 causes with test visits; 6 case mixes per skew; every prior compared with the same engine under a uniform prior on identical visits and seeds. **2 of 9 predictions hold.**

| # | Prediction | Result |
|---|---|---|
| R1 | a prior unrelated to the truth (rho = 0) costs at most 0.02 | **fails badly**: -0.264 (S30_B) and -0.286 (A), skewed truth; -0.086 and -0.134 with a flatter truth |
| R2 | a prior with rho = 0.5 gains at least +0.03 | **fails**: -0.122 (skewed truth); -0.016 (flatter truth) |
| R3 | the exact prior gains at least +0.07 | **holds**: +0.089 (S30_B); +0.075 for A |
| R4 | the maximally wrong prior costs at most 0.10 | **fails**: -0.469 |
| R5 | shrinking by half keeps at least half the gain and cuts the worst loss to 0.6x or less | **holds**: gain +0.077 against +0.089; loss -0.120 against -0.469 |
| R6 | skew makes a moderately right prior pay more | **fails, reversed**: a more skewed truth makes an imperfect prior more harmful (-0.122 against -0.016) |
| R7 | a maximally wrong prior raises confident errors by at most 0.03 | **fails**: +0.057 |
| R8 | over rho in {-0.5, 0, 0.5} an unshrunk prior pays on average | **fails**: -0.243 (S30_B, skewed truth) |
| R9 | the independent weak sources agree | **fails**: manufacturer emphasis against the mean language-model rank, Spearman -0.09 (needs 0.30); the five language-model runs agree with each other (0.92) |

The curve for S30_B (top-1 change against a uniform prior; skewed truth / flatter truth):

| rho | unshrunk | shrunk by half |
|---|---|---|
| -1 | -0.469 / -0.305 | -0.120 / -0.068 |
| -0.5 | -0.341 / -0.176 | -0.078 / -0.034 |
| 0 | -0.264 / -0.086 | -0.035 / +0.012 |
| 0.5 | -0.122 / -0.016 | -0.026 / +0.032 |
| 0.75 | -0.021 / +0.034 | not run |
| 1 | +0.089 / +0.066 | +0.077 / +0.054 |

**What this says.** (1) **A prior of unknown quality is not cheap insurance; it is expected to hurt.** An unshrunk prior pays only when it is almost exactly right (break-even rho about 0.75 with a flatter truth, about 1 with a skewed one). Shrinking by half moves break-even to about rho 0 (flatter truth) or about 0.9 (skewed truth). (2) **No sourced prior was built**: the language-model rankings are consistent with each other (they put balancing-valve mis-setting first, then a failed pump, crossover, a low heater set point and check valves, and dip-tube failure, cold-side pressure and sensor offset last) but that is one source's recall, and it does not agree with what manufacturers write about (the cause named by the most manufacturers, `plant_sensor_offset` with 12, is ranked 14th by the models). Uniform stays. (3) **If a prior is ever used**, it should come from real visits, with a shrink weight of at most 0.5, and only once an ordering with high agreement with the truth exists.

**Correction to Addendum 4 (recorded 2026-10-10).** This run exposed that Addendum 4's prior result (S5: oracle +0.095, wrong prior -0.006) was biased: its oracle and wrong priors gave zero weight to the two causes that never appeared among its test visits (pump under-sizing and cold-side pressure), which quietly removed two confusable competitors and made every non-uniform prior look better than it is. Replaying Addendum 4's exact setup (same worlds, mixes and seeds; `scripts/12_prior_convention_check.py`) with those causes kept gives **oracle +0.052 (was +0.095) and wrong prior -0.044 (was -0.006)**. The earlier statement that knowing cause frequencies is worth about +0.1 top-1 and that a wrong prior costs about nothing is retracted; the corrected values are about +0.05 and about -0.04 for engine A with Dirichlet(1) mixes, and the Addendum 11 curve above is the better guide. I had used the old figures to argue that a weak prior would be cheap insurance; that argument was wrong.

## Deviations

- 2026-10-09: after the Addendum 3 run I wrapped `np.log(prior)` in `np.errstate(divide="ignore")` in `Engine.__init__` to silence a benign log(0) warning for the zero pair prior of `S_singles_only`. The values are unchanged; no configuration, threshold or case was altered.
- 2026-10-09: the Addendum 4 run computed and saved all results, then crashed while formatting the report (a parameter with zero effect in both halves had no "worst" entry). I fixed the formatting bug and regenerated the report from the saved `engine_sensitivity.json`; no result was recomputed or altered.
- 2026-10-09: `engine.run_case` gained an optional `garbage_lk` argument (where wrong readings are drawn from; default is the engine's own likelihoods, so every earlier result is unchanged and Addendum 6 reproduces Addendum 3's A and B numbers exactly). Added before the Addendum 6 run; not a change to any frozen setting.
- 2026-10-09: `engine.Engine` gained an optional `q_eps` (soft evidence for tenant questions) and `engine.run_case` an optional `p_tenant`; defaults reproduce every earlier result. Added before the Addendum 8 run.
- 2026-10-09: before the Addendum 8 run I fixed `tenants.frozen_hash()`, which hashed a frozenset through `str()` and so changed with each Python launch; the sets are now sorted and the hash in Addendum 8 was replaced. No design element, prediction or bar changed, and no result existed yet.
- 2026-10-09 (Addendum 9, recorded after extraction and before any comparison or verification result was read): **the pump-and-valve reader broke the frozen access rule ("WebSearch and WebFetch only").** WebFetch returned unreadable bytes for most PDFs, so it fetched those URLs through a third-party text-extraction proxy (`r.jina.ai`). The documents are public and no project data was sent, but the service was not authorised. 35 of its rows come from PDFs read that way (33 of them scored); rows keep the original manufacturer URL. I will not use the proxy for verification, so those rows are expected to come back UNREADABLE from the verifiers. Handling: the main analysis uses the frozen rule unchanged, and a second analysis excludes those 33 rows (`output/OEM_REPORT_no_proxy.md`); both are reported. Other facts about how the documents were read: the heater and mixing-valve readers read third-party mirror copies of manufacturer manuals (ManualsLib, ManualsDir; 82 scored rows come from such copies), some of whose tables came out scrambled so that cause-to-remedy pairings rest on wording or order; the system-guide reader noted that WebFetch returns a small model's answer rather than raw page text, so its anchors are the fragments the tool returned. The fetch tool also cached 43 manufacturer PDFs (79 MB) in its own tool-results folder; nobody opened them.
- 2026-10-10 (Addendum 10): three plant attributes (`tmv_min_flow`, `tmv_lowflow_droop`, `tmv_fixed_mix`) and a few lines in `solve._plant_block` were added before the run; defaults are neutral and the Addendum 3 stress table reproduces exactly (verified by a rerun).
- 2026-10-10 (CORRECTION to Addendum 4): the prior comparison in S5 gave zero prior weight to the two causes absent from the test visits, biasing every non-uniform prior upward. With those causes kept (replay in `scripts/12_prior_convention_check.py`): oracle prior +0.052 (reported +0.095), wrong prior -0.044 (reported -0.006). S5's pass/fail on its frozen bars would not change for the oracle (>= +0.05) and the wrong-prior bar (> -0.05) is only just met; the interpretation 'a wrong prior costs about nothing' is retracted. Addendum 11 measures the curve properly. The frozen code and outputs of Addendum 4 are left as they were.
