# Sequential active evidence-gathering for documentation verification

Question per episode: *is documented owner o of member m correct?* A technician takes one reading at a time (one
channel of one candidate pair over one short trend slice, in a known operating context), the belief is updated exactly,
and the episode stops when P(documented owner correct) leaves (1-tau, tau) or 24 readings are used.
Full tables: `results/docmismatch/active/active_results_oat.md` (headline) and `..._ctxfull.md`; likelihood test:
`context_likelihood_test.md`. Code: `src/docmismatch/active/`, scripts 12, 14, 15, 16, tests `tests/test_active.py`.

## Reused vs built new
Reused unchanged from `hvac_benchmark.experiment`: `ActivePolicy` (argmax-EIG), `RandomPolicy`, `FrozenInitialPolicy`
(EIG frozen at step 0), `make_tiebreak` / `_seeded_tiebreak_sort` (shared tie-break priority), the "stop when p >= conf or
p <= 1-conf" rule, the methodology (all policies share one belief update, so only *selection* differs; frozen-vs-active
isolates adaptivity; accuracy-vs-tests trajectories). Reused from doc_mismatch: `evidence.pair_errors` / `real_frp.pair_errors`
as the reading definitions, the hard filters (class/medium) and the observability labels.
Built new: categorical belief over candidate owners with a continuous-outcome EIG on the decision variable
"documented owner correct"; the likelihood model (context regression, pair random effects, informativeness);
nested calibration; reading pools; cost tiers; new traversal / rule-based baselines. `bayes.py` (binary Bernoulli
observations) and `structured.py` (cardinality coupling) were NOT reusable as-is: readings here are continuous and the
question is over a categorical owner set.

## Results (hist = any of 48 day slices; OAT-only context model; hard-observable + matched correct edges; class-balanced; 95% cluster-bootstrap CIs)
tau=0.95, simulation, leave-one-topology-out likelihood:

| policy | episodes resolved within 24 readings | mean readings (unresolved counted as 24) | readings among resolved | error among resolved |
|---|---|---|---|---|
| active (EIG) | 0.75 [0.67, 0.83] | 9.4 [7.7, 11.1] | 4.7 | 0.07 |
| frozen initial | 0.73 | 9.6 | 4.5 | 0.06 |
| traversal heuristic | 0.51 | 15.3 | 7.3 | 0.02 |
| rule-based (static channel rank) | 0.51 | 15.1 | 6.5 | 0.00 |
| random | 0.37 | 19.7 | 12.4 | 0.07 |

Trade-off across tau (readings / realised error / resolved): tau=0.8 active 6.1/0.12/0.86, traversal 8.5/0.09/0.72,
rule-based 11.4/0.05/0.64, random 16.3/0.10/0.57. Active is not uniformly better on error: the fixed sweeps are slower but
more conservative. Verdict accuracy with NO stopping is ~0.8 for every policy after 24 readings (active 0.79, traversal 0.79,
rule-based 0.82, random 0.74): active reaches that ceiling in 1-2 readings, the others need many more; nobody exceeds it.
The ceiling is set by slots the evidence cannot resolve: `vav_zone` (never resolved), `ahu_sat`, `loop_branch`.

## Did temporal/operating context matter?
* Direct test (`context_likelihood_test.md`, held-out log-density per reading, context minus pooled): the context model
  first designed (quadratic in outdoor temp, load and swing features, context-dependent spread) is WORSE than one pooled
  distribution across buildings (-0.49 nats [-0.54, -0.43]) and on real held-out seasons (-0.03). An outdoor-temp-only mean
  shift is neutral across buildings (-0.005), helps within a building across seasons (+0.026 [+0.023, +0.029]) and on real
  held-out seasons (+0.023 [+0.019, +0.027]). The effect is real but small.
* End to end (paired, sim, OAT-only vs pooled): 0.9 fewer readings [0.2, 1.6] in hist; error among resolved 0.07 vs 0.09;
  accuracy at 8 readings +0.03 [+0.01, +0.06] in `visit`; log-loss differences straddle zero. With the full context model
  the same comparison is worse: error 0.15 vs 0.09, log-loss +0.19 [-0.12, +0.51].
* Real data, OAT-only vs pooled: mixed and mostly within noise, and clearly WORSE when the held-out season lies outside the
  training temperature range (`hist_loso`: error 0.43 vs 0.25, log-loss +0.33 [+0.11, +0.50]) - linear extrapolation in OAT fails
  exactly where the calibration experiments said the danger is.
Honest reading: context conditioning gives a modest, not dramatic, gain when the operating regime is covered by training
data, and hurts when it is not. Richer context than outdoor temperature did not transfer across buildings.
The OAT-only variant was chosen AFTER seeing held-out likelihoods of the evaluation topologies (three candidates), so the
"oat" rows carry mild selection bias; the "full" rows are the a-priori design and are reported alongside.

## Calibration problem found and how it was handled
First version stopped after 1-2 readings with 0.65-0.83 accuracy on some slots: pooled "wrong-owner" distributions do not
transfer between buildings (near-twin AHUs look like matches; a building with 10 alternatives dominated the pooled fit).
Mitigations, all from training buildings only: equal weight per building; a per-slot tempering factor beta chosen by nested
leave-one-building-out log-loss; a pair-level random effect so repeated readings of one pair are not independent. Residual
miscalibration remains (accuracy among resolved 0.93 vs nominal 0.95 in sim; 0.79 in real `loso`, 0.57 in `hist_loso`).

## Real data (ORNL RTU-VAV, LBNL CC BY 4.0; one building, 14 days; injected swaps; truth = dataset naming)
Not validated for practical use. Active is the best policy tested (tau=0.95, loso: 43% resolved, 6.0 readings among resolved,
accuracy among resolved 0.79 [0.68, 0.88] vs nominal 0.95), but forced-verdict accuracy after 24 readings is 0.72 - no better than
random ordering (0.72) - and in `hist_loso` confident verdicts are right only 57% of the time. Only `vav_pwr`/`vav_sat` swaps
resolve at all (few episodes; where they do, accuracy is 1.00); `vav_zone` is near chance, as in the earlier real-data work.
The fixed-order baselines are handicapped on real data (57% of 4-hour blocks are flat/NaN and a fixed sweep sits in one block),
so active-vs-baseline gaps on real data overstate the benefit. The sim result must not be read as a real-conditions result.

## Cost of readings (unresolved)
No credible cost numbers exist. Two qualitative tiers (BAS temperature/point trend = 1; needs a flow/power/energy trend = rho)
with rho swept. EIG-per-cost saves nothing at rho=1, 1.3 cost units [0.7, 2.1] (~5%) at rho=3 and 7.7 [4.3, 12.9] (~10%) at
rho=10 relative to plain EIG, with no change in readings. Tiering depends on which points a given building actually trends,
and ignores travel, access, lockout, and that one physical inspection can yield several readings. Treat as a mechanism demo.

## Other limitations
* Simulated evidence is one weather year, 4 topologies (2 vendored); slices are 24 h; the technician can choose the season
  in `hist` but not in `visit` (the more realistic mode; results are similar: 3.7 readings among resolved, error 0.09).
* Readings of different channels in one slice are treated as independent; prior P(doc correct)=0.5 matches the balanced test set.
* Not-observable positives: active resolves 45% of them at 0.84 accuracy (CI [0.47, 0.98]) - some confident wrong answers.
* Hypotheses are class/medium-compatible owners only; no capacity/size prior (peak-flow ratio was not the benchmark's criterion).
