# Pre-registration: domain-randomized simulation study

Written 2026-09-21, BEFORE any domain-randomized (DR) building was simulated and before any model was fitted on DR data.
May not be edited after the frozen test evaluation runs; changes go in a dated "Deviations" section at the end.

## 0. Motivation and hard exclusions
The earlier sealed evaluation (`active_readiness_final_report.md`) showed accuracy falling on unseen buildings/seasons (sim 0.87 dev -> 0.71 sealed; real winter 0.78) and a confidence layer that refused nearly everything.
Hypothesis under test: the simulation training distribution is too narrow (one HVAC design family, constant SAT, hourly noise at fixed levels, no telemetry defects), so likelihoods and confidence do not transfer.

* The burned sealed sets (real SEALED days: OA_damper_stuck, SA_temp_bias; sim seal_S1..S4) are NOT used for anything here: no training, tuning, thresholds, calibration, model selection, and no domain-randomization choice.
  The only reuse: some vendored weather FILES that seal_S1..S4 also happen to use are placed in this study's held-out TEST climates (a file-availability coincidence, not a result-driven choice).
* Real data used: DEV days only (30 days: 14 baseline + 16 Inc_Eco). Real data informs the sensor/telemetry layer (estimated statistics) and operating-range tables; it never enters a test set here, and this study does not touch real SEALED.
* All simulated cases are synthetic; every case record carries `real_world_verified: false` and `synthetic: true`.

## 1. What is randomized (physical layer, OpenStudio/EnergyPlus; the building is always correct, only the documentation is corrupted)
Weather (12 vendored EPWs, split TRAIN/TEST climates + EPW transforms: dry-bulb offset, solar scale, hemisphere flip = 182-day rotation of data columns); occupancy start/end/night/weekend fractions; lights/equipment/people densities and per-zone lognormal scale; setpoints and deadband width (1.5-5 K); SAT strategy (constant / outdoor-air reset; HELD OUT: warmest-zone reset) with reset range; static-pressure reset (emulated through fan-power curve coefficients: fixed vs reset; this changes fan power only); economizer type (none / fixed dry-bulb / fixed enthalpy; HELD OUT: differential dry-bulb, differential enthalpy) and high limit; minimum outdoor-air fraction schedule; boiler efficiency, chiller COP, fan efficiency; heating/cooling sizing factors; VAV minimum flow fraction; infiltration; reheat type (hydronic / electric; HELD OUT: mixed within one building); topology (n_ahu, n_vav, group mode, loops per medium; HELD OUT: n_ahu = 4, n_vav 14-18, 3 loops).
Not randomized (stated limits): hourly reporting (controller dynamics faster than an hour are invisible; "controller dynamics" = deadband, min-flow, setback and sizing only); one construction set (ASHRAE 189.1 CZ 4-5) for all buildings; hydronic/electric VAV family only (no PSZ/DX in DR); no physical equipment faults other than the economizer/min-OA regime.

## 2. Telemetry layer (applied to the hourly truth when evidence is made)
Noise, per-sensor offsets, drift (linear + random walk), quantisation, random dropouts (historian last-value fill), stale runs, timestamp jitter/inter-channel lag. Levels: `legacy` (exactly the previous hard-coded noise), `estimated` (statistics estimated from real DEV days, with per-building random effects), `wide` (estimated x random inflation, 2-3x defect rates). Parameters not identifiable from the data (e.g. long-term drift, VAV flow-sensor noise) are flagged `assumed`.
Distractor faults (telemetry level, unrelated to the documentation error): stuck sensor, bias step, spike outliers, flow-sensor gain error, on components chosen at random; episodes whose candidate owners/members are hit are labelled `distractor_overlap` and reported separately.

## 3. Training arms (identical downstream settings; each trains on the same NUMBER of buildings, 8, matching the current baseline; two noise seeds each)
| arm | physical buildings | telemetry |
|---|---|---|
| `baseline` | existing A-D + dev E-H (8) | legacy |
| `noise_only` | the same 8 buildings | wide |
| `regime` | 8 NEW buildings: operating-regime randomization, DEV-size hydronic topologies (n_ahu<=3, n_vav 6-12) | legacy |
| `full` | 8 NEW buildings: regime + topology (electric reheat, mixed group modes, n_vav<=14) + distractors | wide (+ distractors) |
| `full_x3` (scale check, secondary) | 24 new buildings, full DR | wide (+ distractors) |
Training buildings never appear in any test suite. The training-building seeds and the test-building seeds are different fixed seeds recorded in the frozen spec.

## 4. Test suites (blind, frozen spec; 8 buildings each; never used for design)
| suite | what is shifted vs the TRAIN sets |
|---|---|
| T1 `in_range` | new buildings from the DEV-spec ranges (baseline-like: constant SAT, hydronic, small) - checks DR does not hurt baseline-like buildings |
| T2 `regime` | new buildings with regimes inside the DR training ranges (SAT reset, economizer, wide loads/setpoints), small hydronic topologies |
| T3 `control` | held-out control regime: warmest-zone SAT reset and differential economizers |
| T4 `topology` | held-out topology: n_ahu 4, 14-18 VAVs, 3 loops, mixed reheat |
| T5 `climate` | held-out climates (TEST set) with transforms beyond the training ranges |
| T6 `compound` | T3 + T4 + T5 shifts together |
Seasons: fits are run either with all seasons (`seen season`) or with one season removed from training (`unseen season`, 4 folds); the test rows of the removed season give `unseen season` (T1..T5: unseen season; T3..T6: compound = unseen building/regime AND unseen season). `unseen days`: within the TRAINING buildings, fit on windows {0,2,4,6} and test on {1,3,5,7} (adjacent 6-week windows, same building).
Test telemetry: both `legacy` and `estimated` versions of every test building (same physics, same cases); `estimated` is primary.

## 5. Cases (documentation errors), diversity rules
Hard families: wrong compatible AHU, VAV-zone swap, wrong same-medium plant loop, BAS point swap, same-medium branch/coil swap, parallel-peer swap (existing `corruptions.propose_hard`, exhaustive proposals, then structural + physical plausibility filter). Easy (physically implausible) errors are generated separately and never mixed into hard metrics.
Per building at most 2 hard cases per family, chosen greedily for distinct physical targets and distinct substitution pairs; no paraphrases, no repeated windows for a hard event; clean cases use distinct windows and are labelled as such. Observability labelled by the existing masked-channel audit under `legacy` noise: `true` / `ambiguous` / `false`. Rows, unique physical simulations, base topologies, distinct physical targets and distinct actual->documented substitution pairs are reported per family and per suite.

## 6. Downstream systems and primary metrics
Two systems, run with identical settings across arms:
* S-V (sequential verifier): frozen configuration from `active/frozen/config.json` (variant sel_slice, ctx=oat, tau 0.95, nmax 24), likelihood + tempering fitted only on the arm's training buildings; policies active and random; setting `visit` (6 day-slices of one 6-week window). No parameter is tuned on any test suite.
* S-C (case-level detector, `classify.py`): variants `evidence_only`, `ev+scratch_finetuned`, `ev+pretrained_frozen`, `ev+pretrained_finetuned` (encoder = `results/pretrain/encoder`), trained on the arm's cases, 3 seeds.
Primary metrics: S-V: class-balanced accuracy of the plain stopping rule among answered episodes AND its answered coverage; S-C: AUROC hard(observable=true)-vs-clean. Secondary: S-V calibration (stated 0.95 vs realised; reliability layer fitted on the arm's inner leave-one-building-out records, coverage and realised accuracy of answered), forced accuracy at budget, S-C AUROC per family and TPR at 5% FPR.
Generalization gap = metric(unseen-days within training buildings) - metric(shifted suite).
Uncertainty: cluster bootstrap over BUILDINGS (primary, 2000 resamples), event-group bootstrap secondary. Paired arm differences on identical episodes.

## 7. Decision rules (fixed in advance)
* "DR reduces the drop": for at least one shifted suite (T3, T4, T5, T6) the paired difference (full - baseline) or (regime - baseline) in primary accuracy has a building-cluster 95% CI excluding 0 in the favourable direction AND T1 (in-range) does not degrade by more than 0.03 (point). Reported per suite; no pooling across suites to rescue a failure.
* "Noise-only helps": same rule, noise_only - baseline.
* "Pretrained encoder helps under DR": for each arm, paired (ev+pretrained_* minus evidence_only) and (ev+pretrained_* minus ev+scratch_finetuned) AUROC difference with CI excluding 0.
* "Confidence transfers": on shifted suites, realised accuracy of answered episodes >= 0.93 (point) with lower bound >= 0.90 at nominal 0.95, per arm; otherwise reported as not transferring.
* Nothing in this study can make the system "real-building ready": simulation-only gains are reported as simulation gains.

## 8. Execution order (what may be looked at when)
1. Generate training and test specs (fixed seeds), hash them into `results/docmismatch/dr/spec_manifest.json`. 2. Generation-level checks only (EnergyPlus success, component counts, non-constant series, thermal sanity, sizing sanity) - no model is run on any test building before step 4. 3. Freeze code (SHA-256 manifest) and config. 4. One evaluation run on the test suites. 5. Anything that goes wrong is fixed only for a labelled second run, with both reported.
Allowed development use of TRAIN buildings (not test): pipeline debugging and leave-one-training-building-out sanity checks.

## Deviations
Dated 2026-09-21, made while building the generator and BEFORE the DR spec was frozen or any DR building simulated for use (only throwaway trial buildings, not model-evaluated):
1. The "hemisphere flip" (182-day rotation of the EPW data columns) was DROPPED from the weather randomization: EnergyPlus computes the sun position from the calendar date, so rotated radiation would be physically inconsistent with sun angles. Weather randomization = climate choice (12 vendored files, train/test split) + dry-bulb/dew-point offset + solar scale.
2. The held-out SAT strategies are `warmest` (zone-demand) AND `tod_reset` (time-of-day, SAT warmer outside occupied hours). Reason (generation-level check on a trial building, no model): EnergyPlus `warmest` sat at its maximum almost always (SAT sd ~0), so on its own it was a level shift, not a new dynamic. `tod_reset` was added so the held-out control regime contains a genuinely time-varying SAT sequence.
3. First generation attempt (before any model was fitted or evaluated): building ids of `full` and `full_x3` collided (both `dr_full_NN`) so 5 simulations failed; ids fixed (`dr_ful_`, `dr_fx3_`), spec re-frozen (sha in `results/docmismatch/dr/spec_manifest.json`) and regenerated. In the same attempt 6 of 80 non-colliding buildings failed generation-level PHYSICS checks (2 thermal-sanity, 4 constant-flow-series). Rule added for the regenerated set: a rejected draw is replaced by the next deterministic re-draw (`draw_building(..., attempt=k)`, up to 6 attempts), every rejection and its reason is logged in `generation_log.json`; checks look at simulated physics only, never at a model. Consequence to state in the report: the DR distributions are conditioned on producing a well-sized, non-degenerate building.

## Addendum (dated 2026-09-21, written BEFORE running, after the main test-suite runs were already in progress)
A new analysis, additive to sections 6-7, not a change to any existing rule: **zero-shot sim-to-real transfer**. For each training arm, fit the `vav_zone` slot likelihood
(variant/ctx/tau from the frozen config) using ONLY that arm's simulated training buildings — no real row, of any kind, enters the fit. Score the resulting model,
unmodified, against the real building's `vav_zone` episodes from the pre-registered set (`active.real_data.real_episodes`, seed 2026, real DEV pool only — real SEALED
is not touched, same rule as everywhere else in this study). Policies active and random; decision layers "none" (plain rule) and "new" (reliability layer fit on that
arm's OWN sim leave-one-building-out inner records — also zero real rows). Cluster unit = calendar day (matching the original PREREGISTRATION.md's real-data rule),
not building (there is only one real building).
Scope: `vav_zone` only. The real building's other two documented-point checks (`vav_sat`, `vav_pwr`) have no existing counterpart slot on the simulation side; testing
them would require inventing a cross-domain feature correspondence, which was deliberately not done (a stated user decision) to avoid an unjustified equivalence claim.
This complements, and is weaker evidence than, the already-planned `28_dr_real_dev.py` real-log-density check: that script asks whether adding an arm's sim data to a
REAL-fitted model changes real log-density; this addendum asks whether a PURELY sim-fitted model is usable on real data at all, end to end (accuracy/coverage/calibration,
not just log-density). Neither can establish real-building readiness on its own (section 0).

## Addendum 2 (dated 2026-09-21, written BEFORE running against any test suite): per-building system identification
Targets the T3/T6 (unfamiliar-regime, compound-shift) failure directly, orthogonal to domain randomization: a fixed additive per-building,
per-(slot, channel) MEAN CORRECTION, estimated at test time from that building's own evidence, with NO ground-truth labels and no access to
the episode's own tested member.

**Estimator.** For a test building's pool, slot `s`, channel `k`, and a likelihood already fit on the training arm (`mu_M(ctx)` = the fitted
match-class mean): for every OTHER member `m' != m` (the member under test), take that member's PHYSICALLY TRUE owner (`sp.truth[m']`) across
ALL of the building's available slices (not just the site-visit window used for verification -- the wider "BAS history" a real historian would
have), compute the residual `tf(E[:,k,truth[m'],m']) - mu_M(ctx)`, trim the top/bottom 10% (robust to the few OTHER members in the same slot
that happen to carry their own injected error), and shrink the trimmed mean toward 0 by `n/(n+30)` (`n` = residual count; the pseudo-count 30
is a judgment call, not fit on any test result). The SAME bias is added to both `mu_M` and `mu_X` (the only estimable choice without labels --
assumes a building-level level shift affects the measurement, not the class separation; stated explicitly as an assumption, not verified).
Falls back to zero correction (unadapted) below `min_n=20` residuals.

**Honesty of the estimator, addressed in advance:** using `sp.truth` rather than "whatever the current documentation says for member m'" is a
simplification (deployment would only have current documentation, not physical truth) but does not leak the tested episode: the tested
member is always excluded, and the ~1-4 OTHER members per slot that carry an unrelated injected error in a DIFFERENT episode are a small
minority the trimmed statistic is designed to be robust to, affecting all episodes symmetrically rather than favouring the one under test.

**Evaluation (frozen before running):** `baseline` arm only (isolates the effect of adaptation from the effect of DR training), rep 0 only,
policy `active` only, layer `none` (plain rule) only, `estimated` test telemetry, all six T1-T6 suites -- a fast, cheap first check, not the
full arm x policy x layer matrix. Same episodes, same seeds, scored twice (with and without the bias): paired building-cluster bootstrap of
the accuracy/coverage/forced-accuracy difference. If this shows a real, CI-clearing gain on T3/T6 without hurting T1, it is worth extending to
the DR arms and the full matrix; if not, reported as a negative result and not pursued further.

## Addendum 3 (dated 2026-09-22, written BEFORE fitting against any test suite): meta-learned low-dimensional shrinkage
Replaces Addendum 2's hand-picked shrinkage constants (trim=0.10, prior_n=30) with values CHOSEN FROM DATA by cross-validation across
many simulated buildings, keeping the exact same functional form (`bias = trimmed_mean(residuals) * n/(n+tau)`) so the change is isolable
to "is the shrinkage strength right," not a different mechanism. Deliberately kept to 2 parameters (tau, trim) -- "low-dimensional" -- given
the small number of available buildings; a higher-capacity learned function was rejected as an overfitting risk (raised and agreed with the
user before this addendum was written).

**Meta-training pool.** All 40 buildings with `role: train` across the DR spec (`regime` 8 + `full` 8 + `full_x3` 24) -- never a T1-T6 test
building, and never re-derived after seeing any test-suite result. Each building is read under its OWN spec telemetry level (legacy/wide, as
drawn), which is itself diverse and not chosen for this purpose. The reference population model is the ONE already fitted on the `baseline`
arm's existing (A-D + dev E-H) training buildings (Addendum 2's model) -- unchanged, so any difference is attributable to the shrinkage
constants alone, exactly as Addendum 2 isolated the bias-correction mechanism from DR training.

**Meta-training examples.** For each of the 40 buildings, each slot, each of 4 slice-subsample fractions (0.15, 0.35, 0.6, 1.0 of that
building's 48 slices, seeded per building+fraction, ALL members used, no member excluded -- exclusion only matters when scoring a SPECIFIC
tested member, not here): the RAW trimmed-mean residual against the reference model at that fraction (`bias_restricted`, `n`, standard
error) vs. the same computed on ALL 48 slices (`bias_full`, treated as that building's low-noise target). Grid over trim in
{0.0, 0.05, 0.10, 0.20} x tau in {5,10,20,30,50,80,120,200,350,600}; the (trim, tau) minimising LEAVE-ONE-BUILDING-OUT cross-validated
mean squared error of `trim_shrunk(bias_restricted; trim, tau) - bias_full` across all 40 buildings x 4 fractions is adopted. No downstream
verifier accuracy is used to pick (trim, tau) -- only recovery of the low-noise target -- so the fitting objective does not depend on any
policy, layer, or test suite.

**Evaluation (frozen before running):** identical scope to Addendum 2 -- `baseline` arm, rep 0, policy `active`, both `none` and `new`
layers, `estimated` test telemetry, all six T1-T6 suites -- with a third variant added: `meta` (Addendum 2's bias estimator, same exclusion
rule, but with the learned (trim*, tau*) instead of the hand-picked (0.10, 30)). Reported against BOTH the unadapted baseline and Addendum
2's hand-shrinkage result on the SAME episodes/seeds. If `meta` does not measurably beat the hand-picked shrinkage, that is reported as a
negative (or null) result, not pursued further at higher complexity (Option 3 was explicitly deferred as the next step, not skipped to).

### Deviation to Addendum 3 (dated 2026-09-22, made BEFORE any test-suite data was touched)
The originally specified tau grid (5..600) had its cross-validated MSE still strictly decreasing at its smallest value (tau=5) for
every trim, i.e. the chosen point sat on the boundary of the search range -- a standard sign the true optimum lies outside it. The grid
was extended downward (0, 0.5, 1, 2, 3 added below 5) and the SAME leave-one-building-out procedure re-run on the SAME 40-building
meta-training pool. No test suite, policy, or downstream accuracy was involved in this change.

## Addendum 4 (dated 2026-09-22, written BEFORE touching real data with this mechanism): does the system-ID fix hold on real data?
Extends the zero-shot sim-to-real check (Addendum 1) and the system-ID check (Addenda 2-3) into one: a `vav_zone` likelihood fit ONLY on
simulated buildings (zero real rows, same as Addendum 1, same F->C context fix), scored against the real building's `vav_zone` episodes
(real DEV pool only, seed 2026 -- real SEALED stays untouched, same rule as everywhere in this study), under three variants: unadapted,
Addendum 2's hand-picked shrinkage, Addendum 3's meta-learned shrinkage (trim=0.10, tau=0.5, fit entirely on simulated buildings, never
refit here). The per-building bias for the REAL target building is estimated by the SAME `sysid.estimate_bias` mechanism, applied to the
real pool exactly as to a simulated one (the Pool/SlotPool structures are shared code, so this needs no special-casing) -- i.e., the exact
same adaptation procedure, unmodified, pointed at real evidence instead of simulated evidence. The reliability ("new") layer for each
variant is fit ONLY on the sim leave-one-training-building-out inner records (never on real data, so real data never enters calibration,
only scoring) and then applied, unmodified, to the real outer episodes. Cluster unit = calendar day (32 real DEV days), matching the
original PREREGISTRATION.md's real-data rule.
This is the direct test of whether today's simulation-side finding (meta-shrinkage restoring non-zero honest coverage) is a simulation
artifact or something that also holds when the sensors, physics and noise are real. No number from this run may be used to retune the
meta-fit, the shrinkage constants, or the reliability layer -- it is scored once and reported as-is, good or bad.

## Addendum 5 (dated 2026-09-21, written BEFORE running either mechanism below against real data): recommend the specific missing
## active measurement, instead of silently trusting or silently dropping an untrustworthy channel

**Motivation.** Addenda 1/4 found real `vav_zone` channels 0/2 carry no real signal (they need per-box airflow, which the ORNL
building's BAS does not log). The product's actual job (per project discussion, not re-litigated here) is to walk a technician
through which tests to run, not merely to score whatever happens to already be logged. So a channel a likelihood was never able to
validate on real data should not silently mislead the belief update -- and where the reason is "this building's BAS lacks the needed
instrument," the system should say exactly what a technician could go measure instead. This addendum covers two DIFFERENT, complementary
mechanisms for deciding "does this channel need an instrument this building doesn't have," both implemented in
`active/measurement.py` / `active/brick_bridge.py` / `active/engine.py` (`exclude_k` parameter, default empty = original behaviour,
bit-identical trajectories -- verified by test) before either was run against real data:

**(a) Statistical (`real_channel_validity`, ORNL DEV only, never SEALED).** For every channel of a slot, score every (slice, member,
candidate-owner) reading in a pool under that channel's sim-fitted likelihood; a reading is "correct" if the sign of its log-likelihood
ratio favours the truth. Validated = the channel's class-balanced accuracy's day-cluster bootstrap lower bound (q=0.10, min_clusters=6,
B=1000, chance=0.5) clears chance; refuses (not validated) with too little evidence, exactly like `ReliabilityLayer`. These thresholds
(q, min_clusters, min_gt=0.5, min_rows=30) are fixed in the code before this addendum's scripts are run.
Scope (frozen before running): all three real slots (`vav_zone`, `vav_sat`, `vav_pwr`) x their channels (9 total), zero-shot sim-fit
population model (Addendum 1's F->C context fix), scored against the full real DEV pool (32 days). `vav_zone` channels 0/2 are expected
to fail this check (a reproduction of Addendum 1/4's already-reported finding, not a new claim); channel 1 and the other two slots have
never been checked before and are genuinely new information from this run.

**(b) Structural (`brick_bridge.py`, the full real building corpus, no timeseries or labels needed at all).** hvac_benchmark already
parses every real building's OWN Brick documentation (`hasPoint` edges typed by Brick sensor class) for its pretrained-encoder corpus
(44 anonymized MORTAR buildings + the ORNL `rtu_exp` testbed -- `config_type == "experimental"`, offline from `data_cache/`, never the
network). This is a DIFFERENT, building-specific, always-available signal for the same question: does THIS building's documentation
already list the sensor a channel needs, regardless of whether we have any timeseries to check it against. `equipment_has_signal`
returns True / False / None (undetermined -- a point exists under a Brick class the reference ontology cannot place, e.g. the real
`rtu_exp` file's non-canonical `Electrical_Power_Sensor`; never guessed, per `ontology.py`'s own "no invented equivalences" rule) rather
than ever forcing a guess. Scope (frozen before running): every VAV-class node's `flow` requirement (`vav_zone` channels 0/2, the only
ones with a catalogued non-BAS-only requirement on the owner side) across the full real corpus -- reported as counts of
present/absent/undetermined per building, not tuned against anything.

**What this does NOT establish, stated explicitly (unchanged from the original conceptual discussion this addendum follows from):**
neither mechanism proves a technician-run measurement campaign would reproduce the statistics simulation assumes -- no real
campaign-collected replacement data exists anywhere in this project. (a) only says today's real BAS data can't validate the channel;
(b) only says today's real documentation doesn't list the instrument. The value of actually collecting the recommended measurement is
evaluated ONLY as a simulation ceiling (accuracy/coverage with vs. without the channel, in simulation, on the T1-T6 baseline arm), never
claimed as a validated real-world result. No number from any run in this addendum may retune `measurement.py`, `brick_bridge.py`, or
`engine.py`'s `exclude_k` mechanism -- they are scored once each and reported as-is.

### Deviation to Addendum 5 (dated 2026-09-21, made after seeing that `acc`/`cov` were uninformative, before seeing any `forced` number)
The first run of scripts/35's ablation crossed the `tau=0.95` confidence band on ZERO episodes in every variant, every layer, both real
DEV and every simulated T1-T6 suite (`vav_zone` alone, isolated from the other slot types that carry the rest of the reading budget in a
full verification, essentially never resolves within `nmax=24` readings by itself -- consistent with, not contradictory to, the
already-reported finding that vav_zone alone contributes ~0% to the honest-coverage win seen earlier this session). With zero crossed
episodes, `acc`/`cov` are uninformative for an exclude-vs-include comparison. `stat_forced_bal` (`dr/analysis.py`'s existing "forced"
statistic: is the model's implied verdict, whatever it is after the budget runs out, on the correct side of 0.5) was added to the
report to get a comparison at all -- this does not require crossing the confidence band, so it can still show whether excluding a
misleading channel shifts the belief in the right direction more often. No other change was made; the same cached raw records
(`real_ablation.pkl`, `sim_ceiling.pkl`) were re-scored, not re-run.

## Addendum 6 (dated 2026-09-21, written after exploratory diagnosis, BEFORE the formal run reported by scripts/37):
## is vav_zone's zero real-DEV honest coverage fixable by any standard lever, or is it a genuine evidence ceiling?

**Why.** Addendum 5 fixed a real but narrow accuracy problem (excluding a structurally-invalid channel); it left the honesty
problem (the calibrated layer answers ZERO real DEV `vav_zone` episodes, plain rule or otherwise) completely untouched. Before
concluding that is unfixable, three standard sequential-testing/calibration levers are tested directly against real DEV data
(never SEALED), each with a clear, falsifiable prediction:

1. **Confidence tempering (`beta`).** The deployed beta=0.1 was chosen by cross-validation ACROSS SIMULATED buildings
   (`calibrate.py`'s existing `calibrate_beta`), never validated against real data. `calibrate_beta_fixed_model` (new, in
   `calibrate.py`) holds the zero-shot sim-fit likelihood fixed and searches for the beta that minimises log-loss on real DEV
   data, nested leave-one-SEASON-out (never SEALED), over an extended grid (0.1 to 12.0). An initial single-draw exploratory
   run gave an unstable, noisy signal (beta preferred anywhere from 0.7 to 2.0 depending on the random seed used to pick which
   alternative owner is tested) -- the SAME "underpowered grid search, don't trust it" pattern as the original Addendum 3 tau-
   grid deviation. `repeats=8` pools 8 independent draws' log-loss (matching that fix) before choosing.
2. **Reading budget.** `nmax=24` may simply be too tight for `vav_zone`'s H=10 candidate space (all 10 real VAV boxes share
   the same Brick class/size, so `hypotheses()` returns all 10 for every episode -- no plausibility filter currently narrows
   it). Checked by running the SAME episodes with an unlimited budget (every reading in that visit day, random order to
   avoid EIG selection bias) and asking whether the posterior ever concentrates given everything available.
3. **Evidence window.** A single visit is one calendar day (6 four-hour blocks); pooling evidence across ALL 32 real DEV days
   for the SAME documented pair (far more than any realistic monitoring campaign) tests whether the ceiling is a per-day
   sample-size limit (fixable by a longer monitoring window, a legitimate and deployable recommendation) or persists
   regardless of how much data is pooled.

**Evaluation (frozen before running scripts/37):** all three checks on the SAME zero-shot sim-fit `vav_zone` model used
throughout Addenda 1/4/5 (no likelihood refit); real DEV only; report the raw numbers (max posterior deviation from 0.5,
fraction crossing 0.95 / 0.80) as-is, whichever way they land. No number from this addendum may retune anything -- if a lever
looks like it helps, that becomes a NEW addendum's basis for a full pre-registered evaluation, not something silently
adopted here.

## Addendum 7 (dated 2026-09-22, written BEFORE running scripts/39): stop wasting tests, not stop being honest

**Reframing (discussed with the user before writing this).** The system's actual job is minimizing technician TESTS, not
maximizing confidence -- those were conflated. Today's `vav_zone` result shows the current loop keeps recommending reads
all the way to `nmax=24` even when the trajectory has been flat (or actively adversarial, per Addendum 5a's channel-2
finding) since read ~5-8: 24 real site-tests were "spent" to learn what read 8 already knew. The fix is NOT to lower the
confidence bar (that would answer more by being less honest) -- it is to recognize, DURING testing, when continuing is not
converging and stop recommending more of it, exactly as a clinical trial's interim futility analysis stops a trial early
when continuing has no realistic chance of reaching significance (conditional-power stopping), as distinct from stopping
early for efficacy (already the existing tau-threshold rule).

**Mechanism (`engine.run_episode`, `futility_window`/`futility_margin`, both default 0/off = original bit-identical
trajectories, verified by `tests/test_engine_futility.py`).** At each step, once at least `2*futility_window` readings
have been taken, fit a linear trend of the DECISION entropy H(p)=-(p log2 p + (1-p) log2(1-p)) of P(doc) over the trailing
`futility_window` readings, linearly extrapolate it to the remaining budget, and stop (marking the result `futile=True`,
distinct from `stopped`=confidence reached and from plain budget exhaustion) if the projected final entropy would still
sit above H(tau) + `futility_margin`. This changes WHEN to keep testing; it does not touch WHICH reading EIG selects next,
and it never raises confidence in an answer -- a case that would have been FLAGGED at nmax is still FLAGGED (now sooner),
never upgraded to a verdict it would not otherwise have reached.

**Graceful output (`active/measurement.py`, `explain_result`).** Replaces a bare FLAGGED with an always-something status:
a confident verdict (unchanged), or the current best-guess probability, an explicit reason ("futile: this evidence type
was not converging" vs. "exhausted the reading budget"), and, for futile/exhausted cases, the missing-measurement
recommendation from Addendum 5 where applicable.

**Evaluation (frozen before running scripts/39): `futility_window=4, futility_margin=0.05`** -- the exact values already
used, before touching real data, in `tests/test_engine_futility.py`'s unit tests (chosen to validate the mechanism
qualitatively, not tuned against any reported result here). Applied on top of Addendum 5's best-validated variant
(`exclude_struct`: channels 0+2 dropped), real DEV `vav_zone` episodes, same seeds as the existing `real_ablation.pkl`
baseline. Primary reported metric: **mean/median technician reads per episode** (the actual quantity this whole addendum
is trying to shrink) with vs. without futility stopping, paired building(day)-cluster bootstrap. Secondary: forced
accuracy with vs. without, to confirm early stopping does not cost accuracy it would otherwise have earned. No number
from this run may retune `futility_window`/`futility_margin` -- reported once, as-is.

## Addendum 8 (dated 2026-09-22, written BEFORE running scripts/40): a continuous trust weight instead of a binary gate

**Motivation (discussed with the user before writing this).** Tying the recent work back to the Bayesian core: EIG-based
selection already seeks the most "decisive" available test, but only according to the FITTED model's own (possibly
sim-only-validated) beliefs. Addendum 5's `exclude_k` fixed this crudely -- a channel is either fully trusted or dropped
entirely. But Addendum 5a's own numbers show a spectrum: real `vav_zone` channel 1 point balanced accuracy 0.533
(weak-but-real), channel 0 0.516 (barely above chance), channel 2 0.307 (confidently BELOW chance). `exclude_struct`
drops both 0 and 2, discarding channel 0's small-but-real signal along with channel 2's actively-wrong one.

**Mechanism (`active/trust.py`).** `TrustWeightedModel` wraps a `ChannelModel` (same drop-in `__getattr__`-delegation
pattern as `dr.sysid.BiasAdaptedModel`) and inflates its class sds by `1/sqrt(weight)` -- the same power-likelihood
tempering `engine.py`'s global `beta` already performs, made channel-specific. `weight=1` is a passthrough (bit-
identical, verified by test); `weight -> 0` drives a channel toward zero contribution to BOTH the posterior update and
its own EIG, with no special-casing anywhere in `engine.py` (both read `sd_M`/`sd_X` purely via `model.params(ctx)`).
`trust_weight()` maps `real_channel_validity`'s POINT balanced-accuracy estimate (not the conservative lower bound,
which already plays the go/no-go role for the `validated` gate) linearly: chance (0.5) -> 0, perfect -> 1, clipped at 0
for below-chance channels (inverting evidence is a different, unattempted mechanism). `apply_trust_weights` drops any
channel below `MIN_WEIGHT=0.02` entirely rather than inflate its sd to numerical uselessness.

**Evaluation (frozen before running scripts/40):** three variants, ALL with Addendum 7's futility stopping on
(`futility_window=4, futility_margin=0.05`, the realistic deployed configuration) -- `no_adaptation` (all channels full
trust), `exclude_struct` (Addendum 5's binary best), `trust_weighted` (this addendum, weights from real DEV
`real_channel_validity`, computed once and applied identically to inner and outer records, matching every prior
addendum's "fit exactly as deployed" rule). Real DEV `vav_zone` episodes; inner leave-one-training-building-out records
(simulated) use the SAME per-variant model, including the same real-data-derived weights, even though the inner
calibration data is simulated -- consistent with, not a new exception to, how Addendum 5 applied `exclude_struct`
identically to inner and outer. Primary: forced accuracy, `trust_weighted` vs `exclude_struct`, paired cluster bootstrap.
Secondary: mean technician reads (should not regress from Addendum 7's number). No number from this run may retune
`trust_weight`'s formula or `MIN_WEIGHT` -- reported once, as-is, whichever way it lands.

### Deviation to Addenda 7/8 (dated 2026-09-22, a bug fix, not a retune of the frozen `futility_window`/`futility_margin`
### values -- made after building `measurement.diagnose_connection` and running it on a genuine simulated example)
Running the newly-integrated end-to-end path on a real, moderately-separated simulated `vav_zone` case (not a reported
result -- a worked-example walkthrough) surfaced a real bug in `is_futile()`: it extrapolated the BARE POINT ESTIMATE of
a short (`futility_window`=4-read) trend over the full remaining budget. A short window's slope is itself noisy, and the
example showed a genuinely, consistently converging trajectory (moving the correct direction on every read) killed at
the earliest possible check anyway, because the point-estimate extrapolation had no sense of its own uncertainty.
Fixed to a proper conditional-power form: extrapolate the OPTIMISTIC end of the trend (point estimate minus 1.645
standard errors of the fitted slope, ~90% one-sided), only declaring futility if even that optimistic projection would
not reach tau within the remaining budget; requires `futility_window >= 3` to estimate the slope's own uncertainty at
all (below that, refuses to judge rather than guess, same rule as `ReliabilityLayer`'s `min_clusters` gate). This changes
the MECHANISM's correctness, not the frozen `futility_window=4, futility_margin=0.05` values themselves, which are
unchanged. Because real DEV `vav_zone` data showed no consistent trend at all under EITHER version (confirmed
independently by Addendum 6's unlimited-budget and 32-day-pooling checks, neither of which depends on this mechanism),
Addenda 7 and 8's real-data conclusions are not expected to change -- but scripts 39 and 40 are re-run against the fixed
mechanism and the numbers reported again below, rather than left standing on a mechanism now known to have a bug.
