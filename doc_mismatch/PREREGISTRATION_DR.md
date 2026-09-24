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

## Addendum 9 (dated 2026-09-22, written BEFORE running the comparison below): a set-level conservation channel for `loop_branch`

**Motivation (discussed with the user before writing this).** A cheap, unregistered measurement this session (~94
`run_episode` calls across the 5 slots never previously checked) found `loop_branch` resolves within the 24-read budget
only 8/20 (40%) of the time on is_wrong simulated episodes -- weaker than previously assumed, and weaker than
`ahu_vav`/`coil_vav`/`vav_dat` (1-18 reads, established earlier). Separately, `evidence.closure_residual` -- a genuine
mass/energy-conservation check (does an owner's own measured flow/heat match the sum of everything currently documented
under it) -- already exists in this codebase but is wired only into the older static classifier (`features.py`) and
`observability.py`, never into the sequential engine (`active/engine.py`) that does the live diagnosis. This addendum
wires a derived form of it in, scoped to `loop_branch` only (not `ahu_vav`, which already resolves well and is left
untouched to keep this comparison clean).

**Mechanism (`evidence.closure_channel`, new function).** A 4th evidence channel (k=3), computed only for
`slot == "loop_branch"`: for candidate owner `o` and tested member `m`, let `others` = every OTHER member `base.slot_edges`
says truly belongs to `o` (ground truth, excluding `m` itself), and return `closure_residual(ev, o, others + [m], sl,
slot="loop_branch")` -- the same relative flow/heat-balance mismatch `test_benchmark_invariants.py` already asserts is
`< 0.05` for a owner's true, complete member set. If `o` truly supplies `m`, appending `m` to `o`'s true other members
reproduces `o`'s true complete set, so the residual should stay small (matching that existing invariant); if `o` does
NOT truly supply `m`, forcing `m` into `o`'s accounted-for total should inflate the mismatch. This is a non-negative
"error, lower = more consistent" value, so it drops into the SAME `tf()`-log-transform + per-class ridge-regression
`ChannelModel` fitting machinery as channels 0-2, unchanged (`model.fit_slot_models`'s `range(3)` -> `range(4)`; every
other slot's channel 3 stays all-NaN and is correctly never fit, `fit_channel` already returns `None` below
`MIN_TRAIN` rows). `engine.py` needs NO changes at all -- `_Actions`/`posterior`/`eig_all` already size every array off
`len(models)`, not a hardcoded channel count. Masked NaN (same `NEEDS`-driven `informative()` gate as channels 0-2) when
the owner's own flow is non-informative.

**Explicitly named simplifying assumption.** `others` is read from `base.slot_edges` -- SIMULATION GROUND TRUTH, not the
(possibly wrong) documentation -- because the active-testing pool architecture has no live "current full documented
graph" concept to draw on for members other than the one under test. This is legitimate ONLY under this benchmark's
existing single-error-per-episode construction (every member other than the one being tested is, by construction,
correctly documented, so ground truth and documentation agree for `others`); it does not leak the truth of `m` itself
(explicitly excluded from `others`). A real deployment would need this built from the DOCUMENTED graph instead --
exactly the graph a technician's blueprint already is -- not ground truth, which does not exist outside simulation. This
cheap check does not validate the mechanism's robustness to more than one simultaneous documentation error.

**Evaluation (frozen before running): same is_wrong `loop_branch` episode generation as the unregistered measurement
above (same topologies -- `vav_2ahu_2loops`, `dev_F`, `dev_G` -- same seeds/windows), `policy="active"`, `tau=0.95`,
`nmax=24`, run twice: once with channel 3 excluded (reproducing the 40% baseline) and once included. Primary metric:
fraction resolved within budget, with vs. without. Secondary: median/mean reads among resolved cases. No number from
this run may retune anything about `closure_channel` -- reported once, as-is, whichever way it lands.

**Result (2026-09-22, run once, as pre-registered above): negative.** Via `sim_kind.fit_slot` on all 8 `EXISTING`
training topologies (channel 3 fit successfully, `beta=0.2`), then the exact same 15 is_wrong `loop_branch` episodes
across `vav_2ahu_2loops`/`dev_F`/`dev_G` run twice with `exclude_k=frozenset({3})` vs `frozenset()`: **7/15 (47%)
resolved before, 6/15 (40%) after -- no improvement, a small regression.** One episode
(`dev_F|loop_branch|HWL-1>Branch-9|wrong`) flipped from a confident, correct REFUTED verdict (p=0.050) to unresolved
(p=0.170): the new channel actively pulled belief in the wrong direction on that case, not just added neutral noise.
Sample is small (15 episodes, one flip) so this is not strong evidence the mechanism is actively harmful, but it is
zero evidence it helps, on the exact slot it was built for. Per this addendum's own frozen evaluation, `closure_channel`
is NOT adopted into any default-on configuration. Left in the codebase (default OFF -- `fit_slot_models` only fits
channel 3 when real data supports it, and nothing selects `loop_branch` channel 3 unless a caller passes `models`
that include it) as a validated-negative result, same disposition as Addendum 8's trust weighting.

## Addendum 10 (dated 2026-09-23, written BEFORE running): does futility stopping generalize past the one real building it was validated on?

**Motivation (discussed with the user before writing this).** Addendum 7 validated futility stopping (`futility_window=4,
futility_margin=0.05`, on top of Addendum 5's `exclude_struct`) exactly once, against the single real DEV building
(ORNL `rtu_exp`, `vav_zone`, n=1200 rows from one building). Every other exercise of `diagnose_connection` this
project has done (the walkthrough demo, this session's slot-resolution-speed checks) also only ever touched that one
real building or hand-picked simulated examples from the 8 `EXISTING` training topologies. This codebase already has
a SEPARATE, larger, pre-registered generalization check -- the DR study's held-out T1-T6 suites (section 4 above,
`spec_ids()`) -- and it is ALREADY used for exactly this kind of question (`measurement_eval.run_sim_ceiling`, the
"simulation-only ceiling" behind Addendum 5/6's numbers). Futility has simply never been run through it: `_sim_rec`
(the per-episode runner `run_sim_ceiling` calls) has no `futility_window`/`futility_margin` parameters at all today --
only `_real_rec` does. This addendum closes that specific, checkable gap: does the ALREADY-VALIDATED, ALREADY-FROZEN
futility mechanism still save technician reads (without costing accuracy) on buildings/regimes it has never been run
against, or was Addendum 7's result an artifact of the one building it was checked on?

**Mechanism (`dr/measurement_eval.py`).** `_sim_rec` gains `futility_window=0, futility_margin=0.0` parameters
(default = original bit-identical behaviour, mirroring `_real_rec`'s existing signature exactly), threaded straight
into its `run_episode` call, with `n_read`/`futile` added to its returned record (again mirroring `_real_rec`). A new
`run_futility_sim_ceiling(cfg, ids_by_suite, suites, variants=FUTILITY_VARIANTS)` mirrors the existing
`run_sim_ceiling` (same T1-T6 suite iteration, same `telemetry="estimated"` convention already used for the Addendum
5/6 ceiling) but runs the already-defined `FUTILITY_VARIANTS` (`no_futility` vs `futility`, both on top of
`exclude_k={0,2}`) instead of the channel-exclusion `VARIANTS`. No new mechanism, no new parameters, no retuning --
purely pointing an already-frozen mechanism at an already-built, already-used, previously-unused-for-this test
population. Same explicit caveat as every other T1-T6 sim-ceiling check in this project: this is simulation only,
never evidence the real-world transfer holds, only whether the mechanism's LOGIC generalizes across simulated
regime/topology/climate shifts it has never been exercised against.

**Evaluation (frozen before running): T1-T6 suites, `vav_zone`, `exclude_k={0,2}` (Addendum 5's best variant) held
fixed in both arms, `futility_window=4, futility_margin=0.05` (Addendum 7's exact frozen values, not retuned) vs
`futility_window=0`. Primary metric: mean/median `n_read` per episode, with vs without, per suite. Secondary: forced
accuracy, with vs without, to confirm early stopping does not cost accuracy it would otherwise have earned. No number
from this run may retune `futility_window`/`futility_margin` or the exclusion choice -- reported once, as-is,
whichever way it lands, per suite.

**Result (2026-09-23, run once, as pre-registered above, `scripts/42_futility_sim_generalization.py`): positive, and
uniform.** Across all six T1-T6 suites (128 `vav_zone` episodes each, `estimated` telemetry): every single suite shows
**mean/median `n_read` = 24.0/24 without futility vs 8.0/8 with it -- a full 16-read (67%) saving**, and
`frac futile = 100%` in every suite. Forced accuracy moves by at most +-0.08 per suite (T1 +0.078, T2 -0.039,
T3 -0.023, T4 -0.008, T5 +0.008, T6 -0.008) -- small, roughly zero-centered, no suite shows a concerning drop.
**This generalizes Addendum 7's real-DEV finding (futility saves reads without costing accuracy) to five kinds of
held-out simulated shift (regime, control, topology, climate, compound) it had never been run against.**

The exact-8-reads/100%-futile uniformity was checked, not just reported: pulling a raw trajectory (channel 1 only,
after Addendum 5's exclusion) shows belief barely moves at all over the full 24-read budget (0.500 -> 0.492) even
though most individual reads DO register as informative (13/24) -- the remaining channel's class separation is too
weak in this population to move the decision variable, so the entropy trend is flat from the earliest possible check
(`n=2*futility_window=8`) in essentially every episode. Futility is not trading away real, slow-but-genuine
convergence here (the failure mode Addendum 7's bug fix specifically guarded against) -- it is correctly and quickly
recognizing that this evidence line was never going to resolve at all under `estimated` telemetry, a further,
independent confirmation (on top of this session's earlier structural/statistical findings) that `vav_zone`'s
post-exclusion evidence is weak. Low forced accuracy in BOTH arms (0.46-0.70) is consistent with this: futility is not
costing much because there was little decision-relevant accuracy on the table for either variant to earn. Simulation
only, `estimated` telemetry -- not a real-world re-validation of Addendum 7, a generalization check of the mechanism's
logic, per this addendum's own caveat.

## Addendum 11 (dated 2026-09-23, written BEFORE running scripts/43): can the current channels distinguish the candidates even in principle?

**Motivation (discussed with the user before writing this).** `vav_zone` never resolves: 0/18 in-budget on sim (Addendum 6's
neighbours), and Addendum 10 showed that with channels 0/2 excluded the belief barely moves over the full budget (0.500 ->
0.492 in a raw trajectory). Two different explanations predict two different remedies, and nothing measured so far
separates them: (a) the signal is structurally absent from passive operation (candidates' signatures are collinear / zones
follow the weather), so only deliberate perturbation or new instrumentation can help; (b) the signal exists but telemetry
noise or missing airflow signals hide it, so better data, longer windows or the airflow proxy could help. This addendum
measures the fork directly, before any effort is spent on a remedy.

**Mechanism (`dr/diagnosability.py`, `scripts/43_structural_diagnosability.py`): a MODEL-FREE diagnosability ladder --
nothing is fitted, so it is independent of the sim-to-real calibration problem.** For each (slot, channel) the raw
pair-consistency values `tf(e)` of `evidence.pair_errors` (masking OFF so raw separation is visible) are computed on three
evidence levels for the same physical building and slices: `truth` (noise-free `window_truth`), `legacy` (the original
hard-coded noise, identical to the cached legacy pools), and `estimated` (the DR study's real-DEV-estimated telemetry). Per
level and channel: (1) AUROC of "true-owner pairs have lower error than alternative-owner pairs" (0.5 = chance) and d';
(2) rank-1 identification -- aggregate a window's 6 day-slices (and, separately, all 48 slices), take the candidate with the
lowest per-channel-standardised error, ties broken by expected value, compared to chance = mean(1/|candidates|); for the
channel subsets `ch0`, `ch1`, `ch2`, `all3`. For `vav_zone`, a real column: the same metrics on the cached real ORNL DEV pool
(`pool_real`, DEV days only; day-level aggregation), giving the sim-vs-real gap per channel. Buildings: the 8 `EXISTING`
training topologies (train-role; each counts equally; building-cluster bootstrap CIs, 500 resamples). Slots: `vav_zone`
(focus) plus `loop_branch`, `branch_coil`, `coil_ahu` (the other measured-weak slots) and `ahu_vav` (the strong contrast).
Not used: any SEALED data, any T1-T6 test-suite building (the analysis may steer design decisions).

**Frozen reading rules (descriptive thresholds written before running, not tuned; the raw numbers are the result):**
STRUCTURALLY WEAK = AUROC(truth) < 0.60 (noise-free, complete data still cannot separate true from alternative pairs);
TELEMETRY-LIMITED = AUROC(truth) >= 0.75 and AUROC(estimated) < AUROC(truth) - 0.15; INSTRUMENTATION-LIMITED (`vav_zone`
only) = rank-1(truth, all3) - rank-1(truth, ch1 alone) >= 0.15, where ch1 is the only `vav_zone` channel computable on the
ORNL building (Addendum 5b). Reading: STRUCTURALLY WEAK for the channels that remain -> pursue perturbation / a different
statistic, not calibration; TELEMETRY- or INSTRUMENTATION-LIMITED -> data quality, longer windows, or an airflow proxy.

**Limitations named up front.** This measures diagnosability *by these channels' statistics*: an upper bound on what they can
do, NOT a proof that no passive statistic could do better (formal structural diagnosability would need the full physical
model). Hourly reporting means `truth` is still hourly -- sub-hourly dynamics that a real interval-data campaign might
expose are invisible here. The real column is one building. Simulation-only conclusions are not real-world claims.

**Clarification (same day, written before scripts/43 was run):** the INSTRUMENTATION-LIMITED rule uses the *window-aggregated*
rank-1 (one 6-day-slice visit, the technician-visit scale) as its primary measure; the fully pooled 48-slice rank-1 is
reported alongside as a robustness read, not as a second chance to trigger the rule.

**Result (2026-09-23, run once as pre-registered, `scripts/43_structural_diagnosability.py`, ~9 s):**
*Frozen rules.* `vav_zone` (8 buildings): **STRUCTURALLY WEAK on every channel and every evidence level** -- AUROC on noise-free `truth`
0.600 / 0.523 / 0.437 (ch0/ch1/ch2; ch0 a hair under the 0.60 line), and essentially unchanged on `legacy` (0.553/0.522/0.453) and
`estimated` (0.582/0.522/0.435). Window-aggregated rank-1 with all three channels on noise-free, complete data is **0.143 vs chance 0.123**
(`legacy` 0.109, `estimated` 0.125). It is **not telemetry-limited** (truth ~ estimated) and **not instrumentation-limited** (all3 0.143 vs
ch1 alone 0.176, gap -0.033: even complete airflow signals add nothing). The only TELEMETRY-LIMITED flag is `ahu_vav` ch0 (1.000 -> 0.823),
a channel whose true-pair error is exactly zero without noise (its `d'` at `truth` is meaningless, ~3e4; AUROC is the reliable column);
STRUCTURALLY WEAK also for `loop_branch` ch1 (0.513) and `ahu_vav` ch1/ch2 -- channels inside slots that remain diagnosable through another
channel. `branch_coil` and `coil_ahu` trigger no rule.
*Per-slot diagnosability (window rank-1, all3, truth / legacy / estimated; chance):* `branch_coil` 0.962 / 0.933 / 0.937 (0.142);
`ahu_vav` 0.960 / 0.824 / 0.768 (0.378); `loop_branch` 0.859 / 0.819 / 0.817 (0.500); `coil_ahu` 0.815 / 0.817 / 0.804 (0.378);
`vav_zone` 0.143 / 0.109 / 0.125 (0.123). **Reading:** the sim `vav_zone` channels cannot identify a zone's box even with perfect,
fully instrumented sensors, so neither better telemetry nor recovering airflow can fix it -- the remedy has to be a different statistic
or deliberate perturbation. The other four slots ARE diagnosable in principle.

*Exploratory observations -- NOT pre-registered, made while checking the result for artifacts; each needs its own pre-registered follow-up
before anything is adopted:*
(a) **Diagnosable but unresolved.** `branch_coil`/`loop_branch`/`coil_ahu` reach 0.94/0.82/0.80 top-1 accuracy from one visit yet the engine
resolves only 55%/40%/80% of is_wrong episodes at 0.95 confidence (this session's unregistered slot-speed measurement), with calibrated
tempering `beta` = 0.35 / 0.20 / 1.00 (`vav_zone` 0.10; `ahu_vav` 1.00). The bars differ (top-1 vs a 95%-confident verdict), but the gap
points to calibration/tempering, masking of flat channels, or budget -- not physics -- as the lever for those slots. Untested.
(b) **Real ORNL `vav_zone` ch2.** On the cached real DEV pool the true pair's mean tf(e) is clearly LOWER than alternatives' on ch2
(-0.39 vs -0.12, AUROC 0.724, n=371 true-pair readings), the physically expected direction (a box's electric-reheat activity vs its
room's temperature), while the simulation-fitted ch2 has essentially no separation (M -0.21 vs X -0.22). Addendum 5 excluded ch2 as
"confidently worse than chance" under that sim-fitted likelihood. Caveats: one building; ch2 is finite only when reheat is active, so only
10 of 140 (day, room) units and the 10 pooled members support its rank-1 of 1.000; per-candidate slice supports differ under pooling.
Real ch0 (AUROC 0.513) shows nothing; real ch1 is weak-but-real (0.552).
*Not concluded:* that no passive statistic could identify sim `vav_zone` (the ladder bounds these channels only), or that real ch2 is
reliable beyond this one building.

## Addendum 12 (dated 2026-09-23, written BEFORE running scripts/44): is the engine too cautious where the data are diagnosable?

**Motivation (discussed with the user before writing this).** Addendum 11 found `branch_coil`, `loop_branch`, `coil_ahu` and `ahu_vav`
identifiable in principle from a single visit (model-free top-1 0.96 / 0.86 / 0.82 / 0.96, chance 0.14 / 0.50 / 0.38 / 0.38), while the engine
resolves only 55% / 40% / 80% (this session's unregistered slot-speed measurement; `ahu_vav` resolves quickly) of is_wrong episodes at 0.95
confidence, with calibrated likelihood tempering `beta` = 0.35 / 0.20 / 1.00 / 1.00. Three levers could explain the gap: (i) the tempering `beta`
(calibrated to keep stated confidence honest, but possibly over-conservative under leave-one-building-out transfer), (ii) masking of "flat" channels
(the ladder ran with masking OFF; 6 of 12 unresolved `loop_branch` episodes stalled at exactly the 0.5 prior, i.e. no informative reading at all),
(iii) the 24-read budget. Nothing so far separates them. This addendum measures each lever's effect on BOTH resolution and honesty.

**Design (`scripts/44_caution_check.py`).** Slots `branch_coil`, `loop_branch`, `coil_ahu` (the diagnosable-but-unresolved ones) plus `ahu_vav` as a control.
Leave-one-topology-out over the 8 `EXISTING` train-role topologies: for each held-out topology the likelihood (and, for calibrated variants, `beta`) is
fitted on the OTHER seven only, exactly as the nested "inner" records do; all episodes of the held-out topology for the slot (is_wrong and matched-correct)
are run with `policy="active"`, `tau=0.95`, one visit window chosen as everywhere else (`h32(ep_id)%8`), seed `h32(ep_id)%10000`, legacy telemetry, no
futility, no channel exclusion. Variants (frozen): `base` = calibrated beta, masked pools, nmax 24 (today's behaviour); `beta1` = beta 1.0 (no tempering),
masked, 24; `beta1_unmasked` = beta 1.0 with pools built with channel masking OFF (models refitted on those pools), 24; `budget72` = calibrated beta,
masked, nmax 72. Nothing is tuned: the grid is frozen (calibrated / 1.0 only). Metrics per slot and variant: resolved fraction; accuracy among resolved
verdicts, class-balanced over is_wrong / is_right episodes (compare with the stated 0.95); wrong-and-confident rate over all episodes; mean reads among
resolved; per-episode flips vs `base`. Not used: SEALED data, T1-T6 suites.

**Frozen reading rules (descriptive thresholds written before running).** A lever is WORTH PURSUING for a slot if it raises the resolved fraction by
>= 0.10 absolute over `base` while accuracy among resolved stays >= 0.90 (0.95 minus a small-sample slack); it is worth pursuing overall if that holds in
at least two of the three diagnosable slots. If the resolved fraction rises but accuracy among resolved falls below 0.90, the tempering was doing its honest
job (the engine is not merely over-cautious) and the lever is REJECTED for that slot. A lever that changes neither is INERT.

**Limitations named up front.** Small samples (tens of episodes per slot, 3-7 topologies), one simulated HVAC family, simulation only, top-1 identification
(Addendum 11) and a 95%-confident verdict are different bars, so a gap between them is expected to be partly real caution and is not itself evidence of a bug.

**Result (2026-09-23, run once as pre-registered, `scripts/44_caution_check.py`, ~1 min): no lever is worth pursuing (0 of 3 diagnosable slots); the
hypothesis that the engine is merely over-cautious is REJECTED.** Held-out episodes (plain 0.95 rule, leave-one-topology-out; resolved / accuracy among
resolved (class-balanced) / wrong-and-confident over all episodes):
`branch_coil` (105 eps, 7 topologies): base 65% / 0.717 / 18.1%; `beta1` 97% / 0.715 / 28.6%; `beta1_unmasked` 75% / 0.760 / 17.1%; `budget72` 71% / 0.729 / 19.0%.
`loop_branch` (40 eps, 5 topologies; calibrated beta 0.10-0.20): base 38% / **1.000** / **0.0%**; `beta1` and `beta1_unmasked` 100% / 0.589 / 40.0%; `budget72` identical to base.
`coil_ahu` (44 eps; calibrated beta is already 1.00 everywhere, so no tempering to relax): base 61% / 0.671 / 15.9%; every variant inert (`beta1_unmasked` 55% / 0.719).
`ahu_vav` (56 eps; beta ~1.0): 100% resolved in ~2.3 reads, 0.804, 19.6%; every variant inert.
Frozen verdicts: `beta1` and `beta1_unmasked` REJECTED for `branch_coil` and `loop_branch` (accuracy among resolved < 0.90), INERT for `coil_ahu`/`ahu_vav`;
`budget72` INERT everywhere. **Reading:** the calibrated tempering is doing exactly its honest job -- on `loop_branch` it is the reason all 15 confident verdicts are
right; removing it resolves every episode but is wrong-and-confident 40% of the time. The masking hypothesis from Addendum 11 was wrong too: `loop_branch` is identical
with masking off, and the episodes that "stalled at 0.5" were slowed by the tempered likelihood, not lacking informative reads. The budget is not the limit.
**Unexpected, and worse than the earlier framing suggested:** out-of-building, the plain rule is OVERCONFIDENT on the "easy" slots -- accuracy among resolved verdicts
is 0.72 (`branch_coil`), 0.67 (`coil_ahu`), 0.80 (`ahu_vav`) against the stated 0.95. By episode type (base): `branch_coil` right 0.606 when the doc is wrong / 0.829 when
right; `coil_ahu` 0.941 when wrong but only **0.400 when the documentation is right** (it wrongly declares a correct blueprint wrong 60% of the time, n=10 resolved);
`ahu_vav` 0.786 / 0.821; `loop_branch` 1.000 / 1.000. The reliability layer (abstention) exists to handle exactly this and was NOT part of this plain-rule check.
Limitations: 40-105 episodes per slot, 5-7 topologies of one simulated family, small per-class cells, simulation only.

## Addendum 13 (dated 2026-09-23, written BEFORE running the evaluation of scripts/45-46): does deliberate perturbation identify the serving box where passive data cannot?

**Motivation (discussed with the user before writing this).** Addendum 11: passive `vav_zone` channels sit at chance even noise-free and fully instrumented
(rank-1 0.143 vs chance 0.123). Under closed-loop control the zone temperature is regulated, so the link is carried by the manipulated variable (box flow /
reheat) and buried under weather and schedule common mode -- the classic closed-loop identifiability limit, which is broken by exciting the control
REFERENCE, not by better sensors. The test: give every zone its own pseudo-random setpoint pattern and see whose box follows which zone. This is the
"active fault diagnosis / optimal input design" (#2) idea; it replaces the physical test `ACTUATE_OBSERVE`'s invented rates with a measured effect size.

**Mechanism (`interventions.py`, run in `physics_pipeline/.venv`; `dr/perturbation.py`, numpy only).** For a base topology the model is rebuilt unchanged except that each
zone gets a private thermostat whose COOLING and HEATING setpoints both follow `base +- 1.5 K` (base 24 / 20 C) under an independent +-1 code per zone with 2-hour
blocks (a BAS setpoint schedule; no hardware). EnergyPlus (25.2, hourly) runs 2 undithered days followed by a 12-day campaign (288 h) in July (cooling) and,
separately, January (heating). The input signal is the LOGGED zone setpoint `sp_cool` (what a BAS would record). For each zone `m` and candidate box `o` the score is
`S(m,o) = max(|corr(u_m, flow_o)|, |corr(u_m, t_dis_o)|)` over the first `L` campaign hours (sign-agnostic: raising the cooling setpoint lowers flow, raising the
heating setpoint raises discharge temperature); the predicted box is `argmax_o S`, ties counted as expected value. No fitting, no likelihood model.

**Disclosure of the design-shaping feasibility check (made BEFORE this addendum; it is NOT part of the evaluation).** One noise-free campaign of `sys07_vav_reheat`,
July, code seed 0, matched 10/10 zones once the logged setpoint (not the commanded code, which the simulator applied shifted by one hour) was used as the input and the
sign was taken as negative-correlation; a moving-average detrend hurt (4/10) and was dropped. Those observations fixed three design choices above (logged input,
sign-agnostic |corr|, no detrending, both setpoints shifted so both seasons respond). Seed 0 and that building/season/noise-free result are EXCLUDED from evaluation.

**Evaluation (frozen before running):** buildings `sys07_vav_reheat`, `vav_2ahu_2loops`, `vav_3ahu_2loops`, `dev_E`, `dev_F`, `dev_G`, `dev_H` (train-role; each counts equally; every
one has 10-ish zones and one VAV per zone -- chance = 1/n_vav); seasons July and January; code seeds 1, 2, 3; campaign lengths `L` in {24, 48, 96, 168, 288} h. Response
noise applied to the logged box signals: `none`; `legacy` (flow x N(1,0.02), temperature + N(0,0.25) -- the project's original telemetry noise); `harsh` (flow x N(1,0.10),
temperature + N(0,1.0)); 20 independent noise draws per campaign. Primary metric: rank-1 zone-to-box accuracy, mean over draws and seeds, building-cluster bootstrap 95% CI (500).
Passive comparator: for the same building/season, an UNDITHERED run (all zones held at constant setpoints, same window) scored with the existing passive `vav_zone`
channels through the Addendum 11 rank-1 (`all3` and `ch1`) over the same `L`. Never used: SEALED data, T1-T6 suites.

**Frozen reading rules:** perturbation BREAKS THE PASSIVE LIMIT if, under `legacy` noise, mean rank-1 >= 0.90 at L = 96 h in BOTH seasons while the passive comparator stays <= 0.30. If it
reaches 0.90 only at L > 96 the verdict is WORKS BUT NEEDS THE LONG CAMPAIGN (report the shortest L that reaches 0.90). If one season fails it is SEASON-LIMITED. If it does not reach
0.90 at L = 288 in either season it does NOT solve the problem. `harsh` noise is reported as robustness, not a pass/fail criterion.

**Limitations named up front.** (1) It identifies which box's actuator follows which zone's thermostat -- the control link -- which in this simulator coincides with the air-path link `vav_zone` encodes; a
real building whose thermostat wiring differs from its air path would need the complementary box-override test (`ACTUATE_OBSERVE` on the zone temperature). (2) The simulator runs no faults,
hourly reporting, one HVAC family, no occupants overriding setpoints, no real actuator saturation or BAS scan delays, and a campaign of 24 h to 12 days of continuous setpoint modulation (a comfort
cost the sim does not price). (3) No real building data with deliberate setpoint patterns exists in this repository, so nothing here validates a real deployment. (4) A campaign occupies the
building for hours to days but no technician labour after setup: its cost is not comparable to a sensor read and is NOT priced here.

**Result (2026-09-23, run once as pre-registered; campaigns generated by `scripts/45` -- 56 EnergyPlus runs, all clean, ~2 min -- evaluated by `scripts/46`):
frozen verdict = WORKS BUT NEEDS THE LONG CAMPAIGN; the passive limit IS broken.** Zone-to-box rank-1 accuracy under `legacy` noise, mean over 7 topologies x 3 code seeds x
20 noise draws [building-cluster 95% CI] (chance ~0.10):
*July (cooling):* 24 h 0.60 [0.59, 0.61]; 48 h 0.83 [0.81, 0.87]; 96 h **0.97** [0.95, 0.99]; 168 h 1.00; 288 h 1.00. *January (heating):* 24 h 0.78 [0.66, 0.89]; 48 h 0.96 [0.93, 0.99]; 96 h **0.89**
[0.85, 0.93]; 168 h 0.95 [0.92, 0.98]; 288 h 0.98 [0.96, 0.99]. The passive `vav_zone` channels on the undithered run of the same buildings and windows stay at chance in both seasons at every
length (all3 0.06-0.17, ch1 0.04-0.13; Addendum 11's finding, now reproduced on the campaign window). Frozen rule: July at 96 h passes (0.973 >= 0.90, passive 0.090 <= 0.30); January at 96 h is
0.891, a hair under 0.90 -- so the criterion "both seasons at 96 h" is NOT met, and the pre-registered verdict is WORKS BUT NEEDS THE LONG CAMPAIGN: shortest L at 0.90 = 96 h (July) and 48 h (January,
which then dips to 0.89 at 96 h before staying >= 0.95 from 168 h). The non-monotone January dip is a 3-code-seed artefact of which random sequence happened to open the campaign, not a physical effect.
Response-signal noise is irrelevant: `none`, `legacy` and `harsh` noise agree to within ~0.02 at every length (July 96 h: 0.97 / 0.97 / 0.98), so the limit is statistical power from the number of
independent setpoint blocks and the cross-correlation of the random codes, NOT sensor quality -- which is consistent with Addendum 11 (telemetry was never the bottleneck) and means an orthogonal/
optimised code design could plausibly shorten the campaign (untested; this addendum evaluated only iid random codes). Per building (July 24/96/288 h): all seven reach 1.00 by 288 h; the hardest
January case is `dev_H` (12 boxes: 0.64 / 0.79 / 0.97).
*What this does and does not establish:* in simulation, exciting the control reference resolves in ~4-7 days what passive channels cannot resolve at all, for all zones in parallel, with no dependence on
airflow instrumentation or telemetry quality (the response uses whichever of flow / discharge temperature the building logs). It identifies the thermostat->box control link (see Limitations (1)); it
does not validate a real deployment; the simulator omits setpoint overrides, actuator saturation, BAS scan delays and occupant comfort cost.
