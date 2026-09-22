# Readiness, DEV results (nested), written BEFORE any sealed run

Everything below is DEV only: real = leave-one-SEASON-out over the 30 DEV days (each fold fully nested: likelihood, tempering beta, reliability layer all fitted without
the test season; the layer additionally on inner leave-one-season-out runs); sim = leave-one-TOPOLOGY-out over 8 DEV topologies (A-D + dev_E..H). Sealed data were never
loaded (`results/docmismatch/active/sealed_access.log` does not exist). Detail: `results/docmismatch/active/final/{real-dev-nested,sim-dev-loto}_v5_{sel,sel_slice}.{md,json}`.
Code/config frozen (`results/docmismatch/active/frozen/`); sealed command at the bottom.

## What was built
* `reliability.py`: case-level layer. Features at the stopping point (posterior margin, top-2 gap, informative readings, distinct owners/slices read, cross-reading and cross-slice
  agreement, residuals unlikely under both classes, operating-context distance to the fitted data, slot resolving power estimated leave-unit-out), ridge-logistic score,
  leave-inner-unit-out out-of-fold scores, isotonic calibration, conservative lower bound (cluster design-effect-inflated Beta, one-sided 90%), answer only in the largest top-score
  tail whose point accuracy >= 0.95 AND lower bound >= 0.90; per-slot tightening; otherwise FLAGGED with a reason. Uses `wrong` only as the training target of inner (training-unit) records.
* `engine.py`/`model.py`: exact joint-Gaussian belief with a **slice-member effect** (variant `sel_slice`): readings of one member in one slice by different candidates share a common offset.
  Motivated by a diagnostic (residual ICC by slice 0.3-0.8 on real supply-air/power channels; omega ~0.4-0.6 vs noise sd 0.6-0.9); reduces to `sel` when omega=0 (test, max diff 2e-9).
  New baseline policy `traversal_block` (informative-block-aware sweep). `readiness.py`/`evalkit.py`/`scripts/20_final_eval.py`: single nested code path, C1-C4, cluster bootstrap (1000+), sealed guards.
* Tests: 60 (+11 new in `tests/test_reliability.py`: layer answers easy / flags hard synthetic mixed set, all-hard -> flags, isotonic calibration, class-total handling, fold-plan no-leakage, layer independent of outer labels,
  frozen-hash refusal, slice model == baseline at omega=0, sealed real and sealed sim code paths end-to-end with DEV stand-ins).

## Headline numbers (class-balanced, 95% cluster-bootstrap CI). "none" = plain tau=0.95 stopping rule, "legacy" = previous slot/season abstention (target chosen by nested selection), "new" = case-level layer
### Real, nested LOSO, 3600 episodes / 30 days, active policy, likelihood `sel_slice` (chosen; `sel` in brackets)
| layer | answered coverage | accuracy among answered | C2 overall | C3 | C4 |
|---|---|---|---|---|---|
| none | 0.112 [0.074,0.151] (0.137) | 0.954 [0.911,0.990] (0.920 [0.868,0.965]) | PASS (FAIL) | FAIL | FAIL (1/12 cells violate) |
| legacy | 0.000 (0.004) | insufficient (1.000, tiny n) | insufficient | FAIL | PASS (trivially, nothing answered) |
| new | 0.000 (0.002) | insufficient | insufficient | FAIL | PASS (trivially) |
* Efficiency at the plain rule (all policies same rule): readings saved by active vs random 12.6 [4.8,16.1] (24 paired episodes; random almost never reaches a verdict), vs informative-block traversal 3.7 [1.6,6.4] (93 pairs), vs frozen 0.9 [0.3,1.5]; naive traversal reaches no verdict at all in a day pool.
  Active answered coverage 0.112 vs traversal_block 0.041, random 0.011. ECE of the raw posterior 0.012.
* The new layer answers NOTHING on real DEV: inner runs (likelihood trained on 2 seasons) have crossed-verdict accuracy ~0.83, and no top-score region with point accuracy >= 0.95 and lower bound >= 0.90 exists
  (ablation, 8 layer configurations: `final/layer_ablation_real_sel_slice.json`; the most permissive, nominal 0.93/LB 0.85, answers 0.3% with 100% accuracy). So on real data the honest system FLAGS everything: "cannot demonstrate 95% here".
  The plain rule is 95% accurate overall on real DEV, but per season/slot cells are too small (6-12 days) to show it, and C3 (no blanket refusal) fails for the layers.

### Sim, nested LOTO, 8 topologies, `visit` setting, active, `sel_slice` (`sel`)
| layer | answered coverage | accuracy among answered | C2 overall | C3 | C4 |
|---|---|---|---|---|---|
| none | 0.504 (0.482) | 0.870 [0.812,0.920] (0.864) | FAIL | PASS | FAIL (29/40 cells violate) |
| legacy | 0.073 (0.081) | 0.992 [0.971,1.000] (0.947) | PASS (INCONCLUSIVE) | PASS (FAIL) | FAIL (6/40) |
| new | 0.042 [0.024,0.064] (0.024) | 0.986 [0.957,1.000] (0.950 [0.873,1.000]) | PASS (INCONCLUSIVE) | PASS | FAIL (2/40: a 1-episode cell and s3/sensor_mapping/vav_dat, 14 of 70 answered, C2 FAIL) |
* New layer: per season PASS/PASS/PASS/INCONCLUSIVE (15-19 answered each); answers only `ahu_vav` and `vav_dat` (all other slots flagged); ECE 0.041 (answered, n=69); flags carry information (flagged unresolvable-or-wrong share 0.97 vs answered 0.19, margin 0.78 [0.57,0.92]).
* Efficiency, plain rule: active saves 9.2 [8.0,10.2] readings vs random, 3.9 [3.1,4.9] vs both traversals, 0.6 vs frozen (CI excludes 0 for `sel` but marginal fail for the `sel_slice` frozen row: 0.58 [0.37,0.85] counted FAIL only because active coverage < frozen's).
  BUT the plain-rule accuracy of active is 0.87 whereas the slower policies are 0.94-0.97: active's speed is bought with over-confidence; at MATCHED honest confidence (same layer) only 12 paired episodes with random and none with the traversals exist because the layer answers 4% (C1 not establishable, `n/a`/FAIL).
* Regression vs legacy: coverage of the new layer 0.042 vs legacy 0.073 (legacy also higher accuracy? 0.992 vs 0.986: equal within CI); the new layer has fewer C3/C4 failures (C4 2 vs 6 violating cells) at lower coverage. It is NOT a coverage win; it is better calibrated at the cell level.

## C1-C4 status (DEV, layer `new`)
C1: real: NOT established at matched confidence (nothing answered); at the plain rule active is more efficient (CIs exclude 0). Sim: not established at matched confidence (12 pairs vs random PASS, none vs traversals).
C2: sim overall PASS (0.986, LB 0.957) but only 2 of 10 slots answered; real: insufficient (nothing answered) - i.e. no honest-95% claim is possible on real DEV.
C3: sim PASS; real FAIL (blanket flagging: coverage of resolvable cases below 0.30 in every bucket).
C4: real PASS trivially (flags everything); sim FAIL (2 violating cells of 40).

## Variants tried on DEV (count) and negative results
* Likelihood: 2 (`sel`, `sel_slice`) x decision layers 3 (none, legacy, new) = 6 pipeline configurations, each run on real-nested and sim-LOTO.
* Reliability-layer configurations (real and sim): 8 (all features LB0.90 [default]; LB0.85; nominal 0.93/LB0.85; core feature subset; margin only; no per-slot tightening; q=0.2; stronger ridge). Trade-off: relaxing the standard buys coverage but loses C2/C4 (sim no-per-slot: coverage 0.175, acc 0.954, C4 16 violating cells).
* Data decision (script 21): adding simulated `vav_zone` pools to the real likelihood changes held-out real log-density by -0.011 nats/reading on average (12 season x channel cases, 6 up / 6 down, range -0.14..+0.09): no reliable gain, as expected (different modality). Simulation does NOT fix real transfer.
* Extra topologies (dev_E..H) help the sim side: with 8 instead of 4 DEV topologies the inner layer trains on 7 units instead of 3 and the new layer moves from answering nothing/marginal to answering 4%.
* Not tried (cost): online unit-level shift with joint marginalisation over all candidates beyond the slice effect; layer applied at every step (sequential stopping on the reliability score); richer features.
* Power analysis (script 21 `power`): to show accuracy >= 0.93 with one-sided 95% lower bound >= 0.90 when the true accuracy is 0.95 needs ~52 independent answered verdicts, ~206 with a design effect of 4 (days/events share correlated errors); at true accuracy 0.97: 17 / 65. One building with 30 DEV (32 sealed) days, ~5-50 answered per cell, cannot support per-cell claims; per-cell verification needs several hundred independent days or, better, several buildings.

## Judgment calls made AFTER seeing held-out DEV numbers (selection-biased)
1. Adopting `sel_slice`: motivated by the ICC diagnostic, chosen because held-out DEV accuracy among crossed rose 0.92 -> 0.95 (real) and 0.95 -> 0.99 at layer level (sim).
2. Layer standard: nominal 0.95 on the tail's point accuracy AND one-sided 90% lower bound >= 0.90 (originally LB >= 0.95, which answered nothing anywhere); scan fix (small samples do not stop the scan).
3. Family label of correct edges = the slot's / matched fault family so that C2/C4 cells contain both classes; flag rate defined as share flagged (no class balancing).
4. Primary reading pool: the day's 6 blocks (real; keeps days independent) and `visit` (sim); `hist`/season pools not used for criteria.
5. Sim frozen-policy C1 rows are decided by coverage; not tuned.

## Predictions for the SEALED run (written before it)
* Real-sealed (32 days from two fault regimes absent from DEV; likelihood fitted on all 30 DEV days): the new layer will again answer (almost) nothing or very little -> C2 insufficient, C3 FAIL, C4 PASS trivially, C1 not established at matched confidence. The plain rule may reach a verdict on ~5-10% of episodes with accuracy near 0.9-0.95 but I do not expect its cells to be demonstrable; regimes like a stuck damper / biased supply-air sensor are outside the fitted distribution, so I expect flagging or, for the plain rule, confident errors.
* Sim-sealed (4 new topologies, new climates): C2 overall likely PASS or INCONCLUSIVE (accuracy 0.95-0.99 among a few percent-to-10% answered); C3 probably PASS; C4 likely FAIL by one or a few small cells; C1 unlikely to be established at matched confidence because so few episodes are answered by more than one policy.
* Overall: NOT READY under section 5 (C2 and C4 both must PASS on both sets; real cannot show honest 95%). What is missing: DATA (more independent real days across seasons and, above all, other buildings, with realistic fault regimes), and a stronger likelihood; not more of the same synthetic data.
