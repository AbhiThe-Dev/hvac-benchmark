# Readiness verdict: sequential documentation verifier (ML side)

Date 2026-09-21. Protocol: `PREREGISTRATION.md` (binding, unchanged since written; no Deviations). Frozen config + SHA-256 manifest: `results/docmismatch/active/frozen/`
(14 code files verified unchanged before the run). Sealed data was loaded exactly once per set (`results/docmismatch/active/sealed_access.log`); nothing was tuned on it.
Full reports: `results/docmismatch/active/final/{real-sealed,sim-sealed}.md`; dev work and predictions: `active_readiness_dev_report.md`. Tests: 62 pass.
Sealed sets: real = 32 unseen days (OA-damper-stuck + supply-air-sensor-bias fault runs, all seasons, one building), 3840 episodes; sim = 4 unseen buildings, 778 episodes.

## VERDICT: NOT READY (pre-registered rule: C2 not PASS on sealed-real, C4 not PASS on sealed-sim)

## Sealed results (class-balanced, 95% cluster-bootstrap CIs)
| criterion | sealed real | sealed sim |
|---|---|---|
| C1 efficiency, plain stopping rule (no reliability layer) | PASS vs random (6.1 readings saved [2.3, 10.5], only 12 paired episodes) and vs block-aware traversal (10.9 [4.6, 16.3], 40 pairs); no gain over the frozen-EIG policy | PASS vs random (8.5 [7.0, 10.0]), block-aware traversal (3.1 [1.8, 4.6]), naive traversal (2.2 [1.3, 3.3]) |
| C1 under the frozen reliability layer (pre-registered form) | n/a: the layer answers nothing | FAIL: the layer answers only 3.4% of active's episodes and fewer than the baselines'; no comparison against random possible |
| C2 honest confidence, plain rule | INCONCLUSIVE overall: 0.936 [0.883, 0.969], coverage 0.084; winter FAIL 0.779 [0.717, 0.847]; VAV-zone FAIL 0.876 [0.778, 0.939]; ECE 0.116 | FAIL: 0.713 [0.611, 0.797] at coverage 0.518, ECE 0.256 (dev estimate had been 0.87) |
| C2, frozen layer | insufficient: answers 0 of 3840 | PASS overall on 27 answers (accuracy 1.00), but all 36 conditions insufficient; coverage 0.034 |
| C3 precise abstention, frozen layer | FAIL (nothing answered; 0 resolvable cases even with all readings) | PASS, but 44% of resolvable cases [19%, 66%] were flagged |
| C4 knows its limits, frozen layer | PASS only trivially (flags everything) | FAIL: 8 of 36 conditions answered more than 10% of the time without C2 support |

## What the numbers say
1. The efficiency advantage is real and holds on unseen data, on both substrates: with the plain stopping rule, active needs fewer readings than random / fixed orders with CIs above zero.
   But it is bought with accuracy: sealed-sim plain-rule accuracy is 0.71 for active versus 0.93 for random and traversal. Speed at the stated 95% level is not free.
2. Confidence is NOT honest out of distribution. Winter real days (unseen operating regimes) are answered with 78% accuracy at nominal 95%; sealed-sim accuracy dropped from 0.87 (dev) to 0.71.
   The calibrated reliability layer fixes honesty by refusing (real: everything; sim: 96.6%). Honest and useful together was not achieved.
3. Real evidence with this model does not support 95% verdicts on this building: no sealed real episode was "resolvable" (all-readings frozen model, confidence >= 0.95).
4. vav_pwr and vav_sat swaps are answered accurately (0.99 / 1.00) on real data; vav_zone is not (0.88 and below; near chance in earlier work).

## What is missing
* REAL DATA (the binding gap): independent real days across seasons AND buildings. One building, 32 sealed days, 24 clusters with any answer cannot show 95% honesty per condition;
  the power analysis needs about 52 answered verdicts if independent, about 206 with realistic within-day clustering, per condition that matters, and all conditions were "insufficient" here.
  More simulation does not help: sim-derived likelihood terms changed held-out real log-density by -0.011 nats/reading (no effect), and the real evidence modality (5-minute electric-reheat power,
  supply-air lift, room temperature) has no faithful hourly-EnergyPlus analogue.
* MODEL: cross-building/regime calibration. The dev-to-sealed drop in sim (0.87 -> 0.71) and the winter failure show that the fitted likelihood does not transfer to unseen regimes; the conformal-style layer only converts that into refusals.
  A model that abstains rarely AND is honest needs more training regimes/buildings than exist, not a different threshold.

## Judgment calls (selection-biased, made after seeing held-out DEV results)
`sel_slice` variant adopted after an ICC diagnostic and the first nested result; the layer standard was relaxed from lower bound >= 0.95 to point >= 0.95 plus lower bound >= 0.90 (the original answered nothing);
family labels for correct edges, flag-rate definition, day pool (real) and `visit` (sim) as primary settings. None were chosen on sealed data. Sealed sets are now burned for further tuning.

## What this system is and is not ready for
Not ready to have anyone act on its confident verdicts on a real building. A shadow-mode pilot (PREREGISTRATION section 7: log every verdict and readings next to technician-confirmed truth, act on none)
is the only way to obtain the missing data and is reasonable, provided its outputs are treated as unvalidated. The DEV+SEALED days can be used to refit for that pilot; that refit is not evaluated.
