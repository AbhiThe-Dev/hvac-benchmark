# Does the routine's stopping rule, on its own, explain the LLM's T2 speed edge? (Addendum 34)

A parameter sweep of the routine's own engine (`tau`, `min_rate`) on Addendum 30's primary cell, tier T2, 1000 events (identical answers to identical questions, `TableOracle`); no LLM is run here. Simulation only, from the tool's own model family with placeholder numbers.

## Gates

| gate | result | detail |
|---|---|---|
| G1 events | PASS | first 50 of 1000 events match Addendum 30's stored primary-cell kinds |
| G2 baseline reproduces Addendum 31 | PASS | baseline (tau=0.95, min_rate=0.003): 109.0 min / 80% against Addendum 31's 112 min / 80% |
| G3 answer table | PASS | the answer table is deterministic and independent of question order |
| G4 direction sanity | PASS | tau=0.99 against baseline: +1.8 min (should not be faster) |
| G5 reproducibility | PASS | the sweep reproduces exactly on a second run with the same seed |

## Primary sweep: `tau` (min_rate fixed at 0.003), T2, all visits

| tau | minutes / accuracy / wrong-and-confident / checks | d minutes (vs tau=0.95) | d accuracy | d wrong-and-confident | time / accuracy | label |
|---|---|---|---|---|---|---|
| 0.99 | 110.7 min / 80% / 0.2% / 11.3 | +1.8 (+2%) [+1, +2] | +0.000 [+0.00, +0.00] | -0.011 | SAME / SAME | NEITHER |
| 0.95 (baseline) | 109.0 min / 80% / 1.3% / 11.0 | +0.0 (+0%) [+0, +0] | +0.000 [+0.00, +0.00] | +0.000 | SAME / SAME | NEITHER |
| 0.90 | 101.6 min / 80% / 2.6% / 10.4 | -7.4 (-7%) [-8, -7] | -0.001 [-0.00, +0.00] | +0.013 | FASTER / SAME | IMPROVES |
| 0.85 | 95.8 min / 79% / 5.1% / 9.8 | -13.1 (-12%) [-15, -12] | -0.011 [-0.02, -0.00] | +0.038 | FASTER / SAME | IMPROVES |
| 0.80 | 91.5 min / 78% / 7.6% / 9.5 | -17.5 (-16%) [-19, -16] | -0.015 [-0.02, -0.01] | +0.062 | FASTER / SAME | IMPROVES |
| 0.75 | 87.0 min / 78% / 9.8% / 9.1 | -22.0 (-20%) [-24, -20] | -0.019 [-0.03, -0.01] | +0.085 | FASTER / SAME | IMPROVES |
| 0.70 | 80.4 min / 77% / 11.8% / 8.5 | -28.6 (-26%) [-31, -26] | -0.024 [-0.03, -0.01] | +0.104 | FASTER / LESS | TRADE |
| 0.60 | 73.4 min / 77% / 16.4% / 7.8 | -35.6 (-33%) [-38, -33] | -0.033 [-0.05, -0.02] | +0.151 | FASTER / LESS | TRADE |
| 0.50 | 66.8 min / 74% / 22.6% / 7.1 | -42.2 (-39%) [-45, -39] | -0.055 [-0.07, -0.04] | +0.213 | FASTER / LESS | TRADE |

## Secondary, exploratory sweep: `min_rate` (tau fixed at 0.95), T2, all visits

| min_rate | minutes / accuracy / wrong-and-confident / checks | d minutes (vs min_rate=0.003) | d accuracy | d wrong-and-confident | time / accuracy | label |
|---|---|---|---|---|---|---|
| 0.003 (baseline) | 109.0 min / 80% / 1.3% / 11.0 | +0.0 (+0%) [+0, +0] | +0.000 [+0.00, +0.00] | +0.000 | SAME / SAME | NEITHER |
| 0.01 | 76.1 min / 78% / 0.3% / 8.4 | -32.9 (-30%) [-35, -31] | -0.016 [-0.03, -0.01] | -0.010 | FASTER / SAME | IMPROVES |
| 0.02 | 62.4 min / 76% / 0.2% / 7.1 | -46.6 (-43%) [-49, -44] | -0.043 [-0.06, -0.03] | -0.011 | FASTER / LESS | TRADE |
| 0.05 | 7.1 min / 38% / 0.0% / 0.8 | -101.9 (-93%) [-106, -97] | -0.423 [-0.45, -0.39] | -0.013 | FASTER / LESS | TRADE |
| 0.1 | 0.0 min / 32% / 0.0% / 0.0 | -109.0 (-100%) [-113, -104] | -0.476 [-0.51, -0.45] | -0.013 | FASTER / LESS | TRADE |

## Exploratory, not registered: matching the language model's own wrong-and-confident rate
The language model's wrong-and-confident rate at T2 was about 16% of complaints (Addendum 33). The closest `tau` in this grid is **0.60** (wrong-and-confident 16.4%), where minutes are -33% against the baseline stopping rule (-35.6 minutes). This is not the frozen decision (which respects the safety tolerance); it asks what a stopping rule with the LLM's own error profile would cost or buy.

## Predictions (written before the run; each strict)

| prediction | holds | values |
|---|---|---|
| P1 | holds | minutes by tau (0.99->0.50): [110.7, 109.0, 101.6, 95.8, 91.5, 87.0, 80.4, 73.4, 66.8] |
| P2 | holds | accuracy by tau (0.99->0.50): [0.799, 0.799, 0.798, 0.788, 0.783, 0.779, 0.774, 0.765, 0.744] |
| P3 | holds | tau=0.90: -7% minutes, accuracy SAME |
| P4 | does not hold | best tau's minutes: -39%, accuracy LESS, d_wc +0.213 |
| P5 | holds | tau=0.99: +1.8 min |

## Frozen decision: THE STOPPING RULE PARTLY EXPLAINS IT

Run time 66 s.
