# Pre-registration: readiness evaluation of the sequential documentation verifier

Written 2026-09-21, BEFORE any modelling on the new data and before any sealed data was loaded. Nothing below may be edited after the
sealed evaluation has been run; deviations must be added as a dated "Deviations" section at the end, never by rewriting.

## 1. Data roles (fixed)
### Real (ORNL FRP research building, LBNL FDD Data Sets RTU, CC BY 4.0; one building, 10 VAV rooms)
| role | days | content | use |
|---|---|---|---|
| DEV | 30 | 14 baseline days (fall 8, spring 2, summer 2, winter 2) + 16 `Inc_Eco` fault-run days (4 per season) | all design, training, calibration, variant selection. Selection is done ONLY by nested leave-one-season-out inside DEV. |
| SEALED | 32 | 16 `OA_damper_stuck` + 16 `SA_temp_bias` days (4 per season per family) | one single-shot evaluation of ONE frozen configuration. Loader: `active/real_data.load_real_sealed(reason)`; every load is logged to `results/docmismatch/active/sealed_access.log`. |
Notes: the 14 baseline days were used in ~15 earlier variant comparisons: they can never again be a held-out set. The 48 fault days had never been loaded
by any prior analysis. DEV and SEALED days are distinct calendar days but interleave in the same weeks (weather autocorrelation between neighbouring days is
NOT removed); SEALED conditions (a stuck outdoor-air damper; a biased supply-air sensor) are operating regimes absent from DEV. The documentation errors
are synthetic swaps of point/zone documentation; truth = dataset naming; the sensor data is untouched. Independent units for inference = calendar days (cluster bootstrap by day).
This is still ONE building: nothing here can establish transfer to another building.

### Simulation
DEV topologies = A-D (existing) + any new development topologies; SEALED topologies = new topologies generated blind to modelling (different sizes / setpoints /
climate where available), never used for fitting, calibration or selection. Sim likelihoods are always fitted leave-one-topology-out within DEV; the sealed
topologies are scored once with the frozen configuration fitted on ALL DEV topologies.

## 2. What is frozen before the sealed run
Code (git-less: a SHA-256 manifest of `src/docmismatch/active/*.py` and the config JSON written to `results/docmismatch/active/frozen/`), likelihood model, selection policy,
reliability/abstention layer, all thresholds, tau, nmax=24, seeds and episode sets (`real_data.real_episodes`, seed 2026; sim: benchmark hard cases + matched correct edges).
The frozen configuration is fitted on all DEV data of the relevant kind and applied unchanged to SEALED data.

## 3. Definitions
* Episode: one documented connection (owner o of member m), a reading pool, budget 24 readings. Verdict states: CONFIRMED, REFUTED, or FLAGGED (with reason).
  "Answered" = CONFIRMED or REFUTED. Reported confidence for an answered verdict is the layer's calibrated probability that the verdict is right (a lower confidence
  bound, not the raw posterior). Nominal level 0.95.
* Class-balanced statistics (wrong-documentation and correct-documentation episodes weighted equally); 95% cluster-bootstrap CIs (clusters: real = day; sim = event group), >=1000 resamples.
* Resolvable case (for judging abstention only, never a system input): the frozen model given ALL informative readings in the pool reaches the correct verdict with calibrated confidence >= 0.95.

## 4. Success criteria (each reported separately on SEALED-real and SEALED-sim; no pooling to rescue a failure)
**C1 Efficiency.** Among episodes answered by BOTH active and random (each under the same frozen reliability layer), paired mean readings-to-answer(random) - readings-to-answer(active): 95% CI lower bound > 0,
AND active's answered coverage >= random's. Same against the fixed traversal order (informative-block-aware variant AND the naive one). PASS needs both on sealed-real and sealed-sim.
**C2 Honest confidence.** Among answered verdicts at nominal 0.95: realised accuracy point estimate >= 0.93 AND lower 95% CI bound >= 0.90 -> PASS; point >= 0.93 but lower bound < 0.90 -> INCONCLUSIVE
(the data cannot confirm it); otherwise FAIL. Evaluated overall and per season, per fault family, per slot with at least 8 answered verdicts / 5 clusters in the cell; cells with fewer are reported as "insufficient" and count against readiness
(not as passes). Calibration curve (reliability diagram at confidence bins 0.5-1.0) and ECE reported.
**C3 Precise abstention.** (a) No blanket refusal: for every (season) bucket and every (slot) bucket that contains resolvable cases making up >= 30% of the bucket, the answered coverage of resolvable cases in that bucket is >= 0.30. (b) Necessity: of the flagged
cases, the share that were unresolvable or would have been answered wrongly at 0.95 must exceed the same share among answered cases by a margin whose CI excludes 0 (flags carry information). (c) Cost: coverage of resolvable cases lost to flags reported plainly, overall and by bucket.
**C4 Knows its limits.** For every condition (season x fault family x slot) where C2 is FAIL/INCONCLUSIVE/insufficient, the system must FLAG rather than answer at least 90% of the time OR the condition is listed as not supported. Reported as a table.

## 5. Readiness verdict rule (the deliverable)
* READY: C1-C4 all PASS on sealed-real and sealed-sim.
* READY WITH NAMED CAVEATS: C2 and C4 PASS (honesty is the safety-critical property) on both, C1/C3 partially met, with each unmet item named; plus the pilot protocol in section 7.
* NOT READY: C2 or C4 not PASS on either sealed set. State exactly what is missing (data, model, or both).
Whatever the outcome, the report states the number of sealed episodes / days / answered verdicts behind every claim and says plainly when a claim rests on too little data to support it.

## 6. Rules of engagement
1. No variant, threshold or hyperparameter may be chosen on SEALED data. If the sealed run reveals a bug, fix it, note it under "Deviations", and re-report BOTH the pre-fix and post-fix sealed numbers; the sealed set is then declared burned.
2. Variant comparisons on DEV use nested leave-one-season-out (outer test season never used in inner selection or calibration). Report the number of variants tried.
3. Anything chosen after seeing held-out DEV numbers is flagged as a judgment call.
4. The sealed evaluation is run at most once per frozen configuration. After it, the final deployment model may be refitted on DEV+SEALED for a pilot; that refit is not evaluated and is labelled as such.

## 7. Pilot protocol requirement (part of readiness)
A deployment must run in shadow mode first: every verdict and its calibrated confidence logged next to a technician-confirmed truth for a subset, recalibrating per building, before any confident verdict is acted on.

## Deviations
(none yet)
