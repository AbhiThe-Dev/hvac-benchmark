# The one-way 'drawings are mostly right' switch (Addendum 22)

Layouts: 25 real Mortar buildings (Brick metadata only); errors and the technician's answers are SIMULATED from the tool's own model family. 600 cells = 4 stress conditions x 3 worlds x 2 candidate regimes x 25 buildings, 500 paired episodes x 5 policies each. The switch is OFF (the default prior: 15% of documented boxes wrong), ON (5%) or ON_MILD (10%, secondary). A world is the TRUE share of wrong drawings; a condition says how bad the actuators and the checks really are (X0 as assumed; X1 actuators fail 30% instead of 15%; X2 checks worse: every check except `override_room` has hit rate -0.15 and false-alarm rate +0.10; X3 both). The tool's own assumptions other than the prior never change. Minutes are placeholders: only orderings and ratios mean anything. This study is post-hoc in origin (it follows Addendum 21) and uses the same layouts and simulator, so it is a replication plus stress test, not independent evidence. Nothing here is evidence about real technicians, real drawings, or whether technicians can tell that drawings are mostly right.

## Gates

| gate | result | detail |
|---|---|---|
| G1 switch states and code path | PASS | 30 episodes identical; 30 episodes x 4 runners identical |
| G2 accounting | PASS | 20 episodes x 5 policies |
| G3 honesty (accuracy among concluded >= 0.92 in X0: off at 15% wrong, on at 5% wrong) | PASS | off/p15/R_narrow: 0.978, off/p15/R_wide: 0.977, on/p05/R_narrow: 0.986, on/p05/R_wide: 0.983 |
| G4 reproducibility | PASS | cell 0: first 50 episodes reproduced |
| G5 completeness, pairing and habit independence | PASS | ok; 20 episodes x 2 habits x 3 states identical |
| G6 layout fidelity | PASS | 25 buildings |

## Means over buildings: minutes / accuracy / wrong-and-confident / mean checks

| condition | world | regime | entropy@off | entropy@on | entropy@on_mild | habit_A | habit_B |
|---|---|---|---|---|---|---|---|
| X0 as assumed | 5% wrong | R_narrow | 27 / 98% / 1% / 2.8 | 25 / 98% / 1% / 2.6 | 27 / 98% / 1% / 2.8 | 20 / 85% / 15% / 2.4 | 36 / 93% / 7% / 2.3 |
| X0 as assumed | 5% wrong | R_wide | 28 / 95% / 1% / 2.9 | 25 / 95% / 2% / 2.7 | 28 / 95% / 1% / 2.9 | 25 / 84% / 16% / 2.9 | 54 / 92% / 8% / 3.0 |
| X0 as assumed | 15% wrong | R_narrow | 34 / 96% / 2% / 3.4 | 31 / 96% / 3% / 3.2 | 34 / 96% / 2% / 3.4 | 22 / 83% / 17% / 2.6 | 45 / 92% / 8% / 2.5 |
| X0 as assumed | 15% wrong | R_wide | 37 / 89% / 2% / 3.6 | 34 / 89% / 3% / 3.4 | 37 / 89% / 2% / 3.6 | 31 / 78% / 22% / 3.5 | 85 / 90% / 10% / 4.1 |
| X0 as assumed | 30% wrong | R_narrow | 45 / 93% / 3% / 4.3 | 42 / 92% / 4% / 4.0 | 45 / 93% / 3% / 4.3 | 27 / 79% / 21% / 3.1 | 59 / 92% / 8% / 3.0 |
| X0 as assumed | 30% wrong | R_wide | 51 / 79% / 3% / 4.9 | 48 / 79% / 5% / 4.6 | 51 / 79% / 3% / 4.9 | 39 / 69% / 31% / 4.2 | 135 / 87% / 13% / 6.0 |
| X1 actuators fail more | 5% wrong | R_narrow | 30 / 98% / 1% / 3.0 | 25 / 98% / 2% / 2.7 | 30 / 98% / 1% / 3.0 | 18 / 87% / 13% / 2.2 | 36 / 93% / 7% / 2.3 |
| X1 actuators fail more | 5% wrong | R_wide | 31 / 96% / 1% / 3.1 | 26 / 96% / 1% / 2.8 | 31 / 96% / 1% / 3.1 | 23 / 85% / 15% / 2.7 | 56 / 92% / 8% / 3.0 |
| X1 actuators fail more | 15% wrong | R_narrow | 37 / 96% / 2% / 3.6 | 32 / 96% / 3% / 3.2 | 37 / 96% / 2% / 3.6 | 22 / 84% / 16% / 2.5 | 46 / 92% / 8% / 2.6 |
| X1 actuators fail more | 15% wrong | R_wide | 40 / 89% / 2% / 3.9 | 35 / 89% / 3% / 3.6 | 40 / 89% / 2% / 3.9 | 30 / 80% / 20% / 3.2 | 89 / 90% / 10% / 4.3 |
| X1 actuators fail more | 30% wrong | R_narrow | 48 / 94% / 3% / 4.5 | 43 / 93% / 5% / 4.1 | 48 / 94% / 3% / 4.5 | 26 / 80% / 20% / 2.9 | 60 / 92% / 8% / 3.0 |
| X1 actuators fail more | 30% wrong | R_wide | 54 / 79% / 3% / 5.1 | 48 / 79% / 5% / 4.7 | 54 / 79% / 3% / 5.1 | 38 / 71% / 29% / 4.0 | 133 / 86% / 14% / 5.9 |
| X2 checks worse | 5% wrong | R_narrow | 41 / 88% / 7% / 3.6 | 35 / 89% / 8% / 3.2 | 41 / 88% / 7% / 3.6 | 21 / 62% / 38% / 2.5 | 52 / 66% / 34% / 2.8 |
| X2 checks worse | 5% wrong | R_wide | 41 / 87% / 6% / 3.7 | 36 / 88% / 7% / 3.2 | 41 / 87% / 6% / 3.7 | 24 / 61% / 39% / 2.7 | 65 / 65% / 35% / 3.3 |
| X2 checks worse | 15% wrong | R_narrow | 47 / 84% / 8% / 4.1 | 40 / 84% / 11% / 3.6 | 47 / 84% / 8% / 4.1 | 23 / 59% / 41% / 2.6 | 56 / 65% / 35% / 2.9 |
| X2 checks worse | 15% wrong | R_wide | 49 / 80% / 7% / 4.4 | 42 / 80% / 10% / 3.8 | 49 / 80% / 7% / 4.4 | 26 / 56% / 44% / 2.9 | 76 / 61% / 39% / 3.7 |
| X2 checks worse | 30% wrong | R_narrow | 57 / 78% / 11% / 5.0 | 49 / 76% / 15% / 4.4 | 57 / 78% / 11% / 5.0 | 25 / 53% / 47% / 2.8 | 66 / 62% / 38% / 3.2 |
| X2 checks worse | 30% wrong | R_wide | 60 / 70% / 10% / 5.3 | 52 / 69% / 14% / 4.6 | 60 / 70% / 10% / 5.3 | 28 / 48% / 52% / 3.1 | 92 / 54% / 46% / 4.2 |
| X3 both | 5% wrong | R_narrow | 45 / 88% / 7% / 3.9 | 37 / 89% / 7% / 3.3 | 45 / 88% / 7% / 3.9 | 20 / 66% / 34% / 2.3 | 52 / 67% / 33% / 2.8 |
| X3 both | 5% wrong | R_wide | 45 / 88% / 6% / 4.0 | 37 / 88% / 7% / 3.4 | 45 / 88% / 6% / 4.0 | 23 / 65% / 35% / 2.6 | 68 / 65% / 35% / 3.4 |
| X3 both | 15% wrong | R_narrow | 51 / 84% / 9% / 4.5 | 42 / 84% / 11% / 3.7 | 51 / 84% / 9% / 4.5 | 22 / 62% / 38% / 2.5 | 58 / 66% / 34% / 2.9 |
| X3 both | 15% wrong | R_wide | 53 / 80% / 8% / 4.7 | 43 / 81% / 10% / 3.9 | 53 / 81% / 7% / 4.7 | 24 / 60% / 40% / 2.7 | 77 / 61% / 39% / 3.7 |
| X3 both | 30% wrong | R_narrow | 60 / 78% / 12% / 5.2 | 49 / 76% / 16% / 4.3 | 60 / 78% / 12% / 5.2 | 24 / 57% / 43% / 2.7 | 65 / 62% / 38% / 3.2 |
| X3 both | 30% wrong | R_wide | 65 / 70% / 10% / 5.7 | 52 / 69% / 14% / 4.7 | 65 / 70% / 10% / 5.7 | 27 / 52% / 48% / 3.0 | 95 / 54% / 46% / 4.3 |

## The switch ON against OFF on the same episodes

Label shares are over the 25 buildings of a regime or the 50 cells pooled (Addendum 21's labels: 5% minutes, 0.02 accuracy, paired 95% intervals). SAFETY REG / GAIN = cells whose wrong-and-confident rate is at least 0.02 higher / lower with the paired interval clear of 0; COST = WORSE, TRADE or a safety regression. Deltas are the mean over buildings of the paired mean difference (on minus off). Reading: the map reading where the switch is right (5% wrong), the harm reading where it is wrongly on (15%, 30%).

| condition | world | regime | IMPROVES | WORSE | TRADE | NEITHER | safety REG / GAIN | COST | d minutes | d accuracy | d wrong-and-confident | d checks | reading |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| X0 as assumed | 5% wrong | R_narrow | 100% | 0% | 0% | 0% | 0% / 0% | 0% | -2.4 (-9%) | -0.002 | +0.003 | -0.17 |  |
| X0 as assumed | 5% wrong | R_wide | 100% | 0% | 0% | 0% | 0% / 0% | 0% | -2.5 (-9%) | -0.000 | +0.002 | -0.18 |  |
| X0 as assumed | 5% wrong | pooled | 100% | 0% | 0% | 0% | 0% / 0% | 0% | -2.5 (-9%) | -0.001 | +0.002 | -0.18 | **HELPS BROADLY** |
| X0 as assumed | 15% wrong | R_narrow | 100% | 0% | 0% | 0% | 0% / 0% | 0% | -2.6 (-8%) | -0.004 | +0.005 | -0.20 |  |
| X0 as assumed | 15% wrong | R_wide | 100% | 0% | 0% | 0% | 0% / 0% | 0% | -2.9 (-8%) | -0.002 | +0.006 | -0.21 |  |
| X0 as assumed | 15% wrong | pooled | 100% | 0% | 0% | 0% | 0% / 0% | 0% | -2.7 (-8%) | -0.003 | +0.006 | -0.20 | **HARMLESS** |
| X0 as assumed | 30% wrong | R_narrow | 88% | 0% | 0% | 12% | 0% / 0% | 0% | -2.9 (-6%) | -0.010 | +0.010 | -0.23 |  |
| X0 as assumed | 30% wrong | R_wide | 92% | 0% | 0% | 8% | 28% / 0% | 28% | -3.7 (-7%) | -0.004 | +0.015 | -0.28 |  |
| X0 as assumed | 30% wrong | pooled | 90% | 0% | 0% | 10% | 14% / 0% | 14% | -3.3 (-7%) | -0.007 | +0.012 | -0.26 | **COSTS SOMETHING** |
| X1 actuators fail more | 5% wrong | R_narrow | 100% | 0% | 0% | 0% | 0% / 0% | 0% | -4.8 (-16%) | -0.002 | +0.003 | -0.33 |  |
| X1 actuators fail more | 5% wrong | R_wide | 100% | 0% | 0% | 0% | 0% / 0% | 0% | -4.7 (-15%) | -0.001 | +0.003 | -0.33 |  |
| X1 actuators fail more | 5% wrong | pooled | 100% | 0% | 0% | 0% | 0% / 0% | 0% | -4.8 (-16%) | -0.001 | +0.003 | -0.33 | **HELPS BROADLY** |
| X1 actuators fail more | 15% wrong | R_narrow | 100% | 0% | 0% | 0% | 0% / 0% | 0% | -5.0 (-13%) | -0.006 | +0.007 | -0.36 |  |
| X1 actuators fail more | 15% wrong | R_wide | 100% | 0% | 0% | 0% | 0% / 0% | 0% | -5.0 (-12%) | -0.001 | +0.006 | -0.35 |  |
| X1 actuators fail more | 15% wrong | pooled | 100% | 0% | 0% | 0% | 0% / 0% | 0% | -5.0 (-13%) | -0.004 | +0.007 | -0.36 | **HARMLESS** |
| X1 actuators fail more | 30% wrong | R_narrow | 96% | 0% | 4% | 0% | 8% / 0% | 8% | -5.1 (-11%) | -0.011 | +0.012 | -0.38 |  |
| X1 actuators fail more | 30% wrong | R_wide | 100% | 0% | 0% | 0% | 8% / 0% | 8% | -5.9 (-11%) | -0.003 | +0.013 | -0.44 |  |
| X1 actuators fail more | 30% wrong | pooled | 98% | 0% | 2% | 0% | 8% / 0% | 8% | -5.5 (-11%) | -0.007 | +0.012 | -0.41 | **HARMLESS** |
| X2 checks worse | 5% wrong | R_narrow | 100% | 0% | 0% | 0% | 12% / 0% | 12% | -5.6 (-14%) | +0.008 | +0.010 | -0.43 |  |
| X2 checks worse | 5% wrong | R_wide | 100% | 0% | 0% | 0% | 12% / 0% | 12% | -5.5 (-13%) | +0.002 | +0.013 | -0.43 |  |
| X2 checks worse | 5% wrong | pooled | 100% | 0% | 0% | 0% | 12% / 0% | 12% | -5.5 (-14%) | +0.005 | +0.012 | -0.43 | **HELPS BROADLY** |
| X2 checks worse | 15% wrong | R_narrow | 100% | 0% | 0% | 0% | 60% / 0% | 60% | -6.7 (-14%) | -0.001 | +0.023 | -0.52 |  |
| X2 checks worse | 15% wrong | R_wide | 100% | 0% | 0% | 0% | 88% / 0% | 88% | -7.1 (-14%) | -0.002 | +0.026 | -0.56 |  |
| X2 checks worse | 15% wrong | pooled | 100% | 0% | 0% | 0% | 74% / 0% | 74% | -6.9 (-14%) | -0.002 | +0.025 | -0.54 | **HARMFUL** |
| X2 checks worse | 30% wrong | R_narrow | 68% | 0% | 32% | 0% | 100% / 0% | 100% | -8.2 (-14%) | -0.016 | +0.040 | -0.65 |  |
| X2 checks worse | 30% wrong | R_wide | 92% | 0% | 8% | 0% | 96% / 0% | 96% | -8.6 (-14%) | -0.006 | +0.043 | -0.68 |  |
| X2 checks worse | 30% wrong | pooled | 80% | 0% | 20% | 0% | 98% / 0% | 98% | -8.4 (-14%) | -0.011 | +0.042 | -0.67 | **HARMFUL** |
| X3 both | 5% wrong | R_narrow | 100% | 0% | 0% | 0% | 0% / 0% | 0% | -8.3 (-18%) | +0.012 | +0.006 | -0.63 |  |
| X3 both | 5% wrong | R_wide | 100% | 0% | 0% | 0% | 8% / 0% | 8% | -8.5 (-19%) | +0.002 | +0.011 | -0.65 |  |
| X3 both | 5% wrong | pooled | 100% | 0% | 0% | 0% | 4% / 0% | 4% | -8.4 (-19%) | +0.007 | +0.008 | -0.64 | **HELPS BROADLY** |
| X3 both | 15% wrong | R_narrow | 100% | 0% | 0% | 0% | 48% / 0% | 48% | -9.8 (-19%) | +0.001 | +0.019 | -0.75 |  |
| X3 both | 15% wrong | R_wide | 100% | 0% | 0% | 0% | 60% / 0% | 60% | -10.2 (-19%) | +0.002 | +0.023 | -0.79 |  |
| X3 both | 15% wrong | pooled | 100% | 0% | 0% | 0% | 54% / 0% | 54% | -10.0 (-19%) | +0.001 | +0.021 | -0.77 | **HARMFUL** |
| X3 both | 30% wrong | R_narrow | 88% | 0% | 12% | 0% | 100% / 0% | 100% | -11.5 (-19%) | -0.013 | +0.038 | -0.89 |  |
| X3 both | 30% wrong | R_wide | 100% | 0% | 0% | 0% | 100% / 0% | 100% | -12.6 (-20%) | -0.004 | +0.044 | -0.99 |  |
| X3 both | 30% wrong | pooled | 94% | 0% | 6% | 0% | 100% / 0% | 100% | -12.0 (-19%) | -0.009 | +0.041 | -0.94 | **HARMFUL** |

### Secondary: ON_MILD (10%) against OFF (reported only; no verdict)

| condition | world | regime | IMPROVES | WORSE | TRADE | NEITHER | safety REG | d minutes | d accuracy | d wrong-and-confident |
|---|---|---|---|---|---|---|---|---|---|---|
| X0 | 5% wrong | R_narrow | 0% | 0% | 0% | 100% | 0% | +0.0 | +0.000 | +0.000 |
| X0 | 5% wrong | R_wide | 0% | 0% | 0% | 100% | 0% | +0.0 | +0.000 | +0.000 |
| X0 | 15% wrong | R_narrow | 0% | 0% | 0% | 100% | 0% | +0.0 | +0.000 | +0.000 |
| X0 | 15% wrong | R_wide | 0% | 0% | 0% | 100% | 0% | +0.0 | +0.000 | -0.000 |
| X0 | 30% wrong | R_narrow | 0% | 0% | 0% | 100% | 0% | +0.0 | +0.000 | +0.000 |
| X0 | 30% wrong | R_wide | 0% | 0% | 0% | 100% | 0% | +0.0 | +0.000 | +0.000 |
| X1 | 5% wrong | R_narrow | 0% | 0% | 0% | 100% | 0% | +0.0 | +0.000 | +0.000 |
| X1 | 5% wrong | R_wide | 0% | 0% | 0% | 100% | 0% | +0.0 | +0.000 | +0.000 |
| X1 | 15% wrong | R_narrow | 0% | 0% | 0% | 100% | 0% | +0.0 | +0.000 | +0.000 |
| X1 | 15% wrong | R_wide | 0% | 0% | 0% | 100% | 0% | +0.0 | +0.000 | +0.000 |
| X1 | 30% wrong | R_narrow | 0% | 0% | 0% | 100% | 0% | +0.0 | +0.000 | +0.000 |
| X1 | 30% wrong | R_wide | 0% | 0% | 0% | 100% | 0% | +0.0 | +0.000 | +0.000 |
| X2 | 5% wrong | R_narrow | 0% | 0% | 0% | 100% | 0% | +0.0 | +0.000 | -0.000 |
| X2 | 5% wrong | R_wide | 0% | 0% | 0% | 100% | 0% | +0.0 | +0.001 | -0.000 |
| X2 | 15% wrong | R_narrow | 0% | 0% | 0% | 100% | 0% | +0.0 | +0.000 | -0.000 |
| X2 | 15% wrong | R_wide | 0% | 0% | 0% | 100% | 0% | +0.0 | +0.001 | -0.000 |
| X2 | 30% wrong | R_narrow | 0% | 0% | 0% | 100% | 0% | +0.0 | +0.000 | -0.000 |
| X2 | 30% wrong | R_wide | 0% | 0% | 0% | 100% | 0% | +0.1 | +0.001 | -0.001 |
| X3 | 5% wrong | R_narrow | 0% | 0% | 0% | 100% | 0% | +0.0 | +0.000 | +0.000 |
| X3 | 5% wrong | R_wide | 0% | 0% | 0% | 100% | 0% | +0.0 | +0.001 | -0.000 |
| X3 | 15% wrong | R_narrow | 0% | 0% | 0% | 100% | 0% | +0.0 | +0.000 | -0.000 |
| X3 | 15% wrong | R_wide | 0% | 0% | 0% | 100% | 0% | +0.1 | +0.002 | -0.001 |
| X3 | 30% wrong | R_narrow | 0% | 0% | 0% | 100% | 0% | +0.0 | +0.000 | -0.000 |
| X3 | 30% wrong | R_wide | 0% | 0% | 0% | 100% | 0% | +0.1 | +0.001 | -0.001 |

## How many wrong switch-ons can it take?

The technician flips the switch on with probability s when the drawings are 5% wrong and f when they are 15% or 30% wrong. Worlds are mixed as 'equal' (1/3, 1/3, 1/3) or 'tilted' toward well-documented buildings (0.6, 0.3, 0.1). Favourable = expected minutes not above 0, expected accuracy not more than 0.01 below and expected wrong-and-confident not more than 0.01 above the default's. f* = the largest f (grid step 0.01) at which the change is favourable at every f up to it.

| condition | regime | mix | f* at s = 0.5 | f* at s = 1.0 |
|---|---|---|---|---|
| X0 as assumed | R_narrow | equal | 1.00 | 1.00 |
| X0 as assumed | R_narrow | tilted | 1.00 | 1.00 |
| X0 as assumed | R_wide | equal | 1.00 | 1.00 |
| X0 as assumed | R_wide | tilted | 1.00 | 1.00 |
| X1 actuators fail more | R_narrow | equal | 1.00 | 1.00 |
| X1 actuators fail more | R_narrow | tilted | 1.00 | 1.00 |
| X1 actuators fail more | R_wide | equal | 1.00 | 1.00 |
| X1 actuators fail more | R_wide | tilted | 1.00 | 1.00 |
| X2 checks worse | R_narrow | equal | 0.39 | 0.31 |
| X2 checks worse | R_narrow | tilted | 0.64 | 0.36 |
| X2 checks worse | R_wide | equal | 0.33 | 0.24 |
| X2 checks worse | R_wide | tilted | 0.50 | 0.17 |
| X3 both | R_narrow | equal | 0.47 | 0.42 |
| X3 both | R_narrow | tilted | 0.86 | 0.67 |
| X3 both | R_wide | equal | 0.36 | 0.28 |
| X3 both | R_wide | tilted | 0.59 | 0.30 |

Expected change at s = 1.0, equal mix, for selected false-alarm rates f (minutes / accuracy / wrong-and-confident):

| condition | regime | f = 0 | f = 0.25 | f = 0.5 | f = 0.75 | f = 1.0 |
|---|---|---|---|---|---|---|
| X0 | R_narrow | -0.8 / -0.001 / +0.001 | -1.3 / -0.002 / +0.002 | -1.7 / -0.003 / +0.003 | -2.2 / -0.004 / +0.005 | -2.7 / -0.005 / +0.006 |
| X0 | R_wide | -0.8 / -0.000 / +0.001 | -1.4 / -0.001 / +0.002 | -1.9 / -0.001 / +0.004 | -2.5 / -0.002 / +0.006 | -3.0 / -0.002 / +0.008 |
| X1 | R_narrow | -1.6 / -0.001 / +0.001 | -2.4 / -0.002 / +0.002 | -3.3 / -0.003 / +0.004 | -4.1 / -0.005 / +0.006 | -5.0 / -0.006 / +0.007 |
| X1 | R_wide | -1.6 / -0.000 / +0.001 | -2.5 / -0.001 / +0.002 | -3.4 / -0.001 / +0.004 | -4.3 / -0.001 / +0.006 | -5.2 / -0.002 / +0.007 |
| X2 | R_narrow | -1.9 / +0.003 / +0.003 | -3.1 / +0.001 / +0.009 | -4.3 / -0.000 / +0.014 | -5.6 / -0.001 / +0.019 | -6.8 / -0.003 / +0.024 |
| X2 | R_wide | -1.8 / +0.001 / +0.004 | -3.1 / +0.000 / +0.010 | -4.5 / -0.001 / +0.016 | -5.8 / -0.001 / +0.022 | -7.1 / -0.002 / +0.027 |
| X3 | R_narrow | -2.8 / +0.004 / +0.002 | -4.5 / +0.003 / +0.007 | -6.3 / +0.002 / +0.011 | -8.1 / +0.001 / +0.016 | -9.8 / -0.000 / +0.021 |
| X3 | R_wide | -2.8 / +0.001 / +0.004 | -4.7 / +0.001 / +0.009 | -6.6 / +0.000 / +0.015 | -8.5 / +0.000 / +0.020 | -10.4 / -0.000 / +0.026 |

## Decision (frozen rule; about OFFERING the switch, never about shipping it): **CONDITIONAL ON RELIABLE CHECKS**

Q (the X0 5%-wrong group reads at least HELPS IN PART): yes (reads HELPS BROADLY). C per condition (no wrongly-on group reads HARMFUL and f* >= 0.50 at s = 1.0 for both mixes and both regimes): X0 holds, X1 holds, X2 fails, X3 fails. Wrongly-on readings: X0/15% wrong: HARMLESS, X0/30% wrong: COSTS SOMETHING, X1/15% wrong: HARMLESS, X1/30% wrong: HARMLESS, X2/15% wrong: HARMFUL, X2/30% wrong: HARMFUL, X3/15% wrong: HARMFUL, X3/30% wrong: HARMFUL. The default stays `off` either way.

## Context (no verdict): each state against the two habits

Addendum 19's label against BOTH habits (WINS / LOSES share of buildings), then against each habit: WINS / LOSES / BUYS ACCURACY.

| condition | world | regime | state | vs both: WINS / LOSES | vs habit_A: WINS / LOSES / BUYS ACC | vs habit_B: WINS / LOSES / BUYS ACC |
|---|---|---|---|---|---|---|
| X0 | 5% wrong | R_narrow | off | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X0 | 5% wrong | R_narrow | on | 0% / 0% | 0% / 0% / 96% | 100% / 0% / 0% |
| X0 | 5% wrong | R_narrow | on_mild | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X0 | 5% wrong | R_wide | off | 0% / 0% | 0% / 0% / 48% | 100% / 0% / 0% |
| X0 | 5% wrong | R_wide | on | 0% / 0% | 0% / 0% / 20% | 100% / 0% / 0% |
| X0 | 5% wrong | R_wide | on_mild | 0% / 0% | 0% / 0% / 48% | 100% / 0% / 0% |
| X0 | 15% wrong | R_narrow | off | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X0 | 15% wrong | R_narrow | on | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X0 | 15% wrong | R_narrow | on_mild | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X0 | 15% wrong | R_wide | off | 0% / 0% | 0% / 0% / 80% | 68% / 0% / 0% |
| X0 | 15% wrong | R_wide | on | 0% / 0% | 0% / 0% / 48% | 64% / 0% / 0% |
| X0 | 15% wrong | R_wide | on_mild | 0% / 0% | 0% / 0% / 80% | 68% / 0% / 0% |
| X0 | 30% wrong | R_narrow | off | 0% / 0% | 0% / 0% / 100% | 96% / 0% / 0% |
| X0 | 30% wrong | R_narrow | on | 0% / 0% | 0% / 0% / 100% | 96% / 0% / 0% |
| X0 | 30% wrong | R_narrow | on_mild | 0% / 0% | 0% / 0% / 100% | 96% / 0% / 0% |
| X0 | 30% wrong | R_wide | off | 0% / 0% | 0% / 0% / 100% | 4% / 0% / 0% |
| X0 | 30% wrong | R_wide | on | 0% / 0% | 0% / 0% / 88% | 4% / 0% / 0% |
| X0 | 30% wrong | R_wide | on_mild | 0% / 0% | 0% / 0% / 100% | 4% / 0% / 0% |
| X1 | 5% wrong | R_narrow | off | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X1 | 5% wrong | R_narrow | on | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X1 | 5% wrong | R_narrow | on_mild | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X1 | 5% wrong | R_wide | off | 0% / 0% | 0% / 0% / 96% | 100% / 0% / 0% |
| X1 | 5% wrong | R_wide | on | 0% / 0% | 0% / 0% / 56% | 100% / 0% / 0% |
| X1 | 5% wrong | R_wide | on_mild | 0% / 0% | 0% / 0% / 96% | 100% / 0% / 0% |
| X1 | 15% wrong | R_narrow | off | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X1 | 15% wrong | R_narrow | on | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X1 | 15% wrong | R_narrow | on_mild | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X1 | 15% wrong | R_wide | off | 0% / 0% | 0% / 0% / 100% | 68% / 0% / 0% |
| X1 | 15% wrong | R_wide | on | 0% / 0% | 0% / 0% / 84% | 68% / 0% / 0% |
| X1 | 15% wrong | R_wide | on_mild | 0% / 0% | 0% / 0% / 100% | 68% / 0% / 0% |
| X1 | 30% wrong | R_narrow | off | 0% / 0% | 0% / 0% / 100% | 88% / 0% / 0% |
| X1 | 30% wrong | R_narrow | on | 0% / 0% | 0% / 0% / 100% | 92% / 0% / 0% |
| X1 | 30% wrong | R_narrow | on_mild | 0% / 0% | 0% / 0% / 100% | 88% / 0% / 0% |
| X1 | 30% wrong | R_wide | off | 0% / 0% | 0% / 0% / 92% | 4% / 0% / 0% |
| X1 | 30% wrong | R_wide | on | 0% / 4% | 0% / 4% / 88% | 4% / 0% / 0% |
| X1 | 30% wrong | R_wide | on_mild | 0% / 0% | 0% / 0% / 92% | 4% / 0% / 0% |
| X2 | 5% wrong | R_narrow | off | 0% / 0% | 0% / 0% / 100% | 96% / 0% / 0% |
| X2 | 5% wrong | R_narrow | on | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X2 | 5% wrong | R_narrow | on_mild | 0% / 0% | 0% / 0% / 100% | 96% / 0% / 0% |
| X2 | 5% wrong | R_wide | off | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X2 | 5% wrong | R_wide | on | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X2 | 5% wrong | R_wide | on_mild | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X2 | 15% wrong | R_narrow | off | 0% / 0% | 0% / 0% / 100% | 92% / 0% / 0% |
| X2 | 15% wrong | R_narrow | on | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X2 | 15% wrong | R_narrow | on_mild | 0% / 0% | 0% / 0% / 100% | 92% / 0% / 0% |
| X2 | 15% wrong | R_wide | off | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X2 | 15% wrong | R_wide | on | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X2 | 15% wrong | R_wide | on_mild | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X2 | 30% wrong | R_narrow | off | 0% / 0% | 0% / 0% / 100% | 84% / 0% / 0% |
| X2 | 30% wrong | R_narrow | on | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X2 | 30% wrong | R_narrow | on_mild | 0% / 0% | 0% / 0% / 100% | 84% / 0% / 0% |
| X2 | 30% wrong | R_wide | off | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X2 | 30% wrong | R_wide | on | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X2 | 30% wrong | R_wide | on_mild | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X3 | 5% wrong | R_narrow | off | 0% / 0% | 0% / 0% / 100% | 68% / 0% / 0% |
| X3 | 5% wrong | R_narrow | on | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X3 | 5% wrong | R_narrow | on_mild | 0% / 0% | 0% / 0% / 100% | 68% / 0% / 0% |
| X3 | 5% wrong | R_wide | off | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X3 | 5% wrong | R_wide | on | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X3 | 5% wrong | R_wide | on_mild | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X3 | 15% wrong | R_narrow | off | 0% / 0% | 0% / 0% / 100% | 52% / 0% / 0% |
| X3 | 15% wrong | R_narrow | on | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X3 | 15% wrong | R_narrow | on_mild | 0% / 0% | 0% / 0% / 100% | 52% / 0% / 0% |
| X3 | 15% wrong | R_wide | off | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X3 | 15% wrong | R_wide | on | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X3 | 15% wrong | R_wide | on_mild | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X3 | 30% wrong | R_narrow | off | 0% / 0% | 0% / 0% / 100% | 36% / 0% / 0% |
| X3 | 30% wrong | R_narrow | on | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X3 | 30% wrong | R_narrow | on_mild | 0% / 0% | 0% / 0% / 100% | 36% / 0% / 0% |
| X3 | 30% wrong | R_wide | off | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X3 | 30% wrong | R_wide | on | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| X3 | 30% wrong | R_wide | on_mild | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |

## Replication: X0 here against Addendum 21 (same layouts and simulator, different seeds; means over buildings, minutes / accuracy / wrong-and-confident)

| world | regime | OFF now | 'mixed' in Add. 21 | ON now | 'mostly_right' in Add. 21 |
|---|---|---|---|---|---|
| 5% wrong | R_narrow | 27 / 98% / 1% | 27 / 98% / 1% | 25 / 98% / 1% | 24 / 98% / 1% |
| 5% wrong | R_wide | 28 / 95% / 1% | 28 / 96% / 1% | 25 / 95% / 2% | 26 / 96% / 1% |
| 15% wrong | R_narrow | 34 / 96% / 2% | 34 / 96% / 2% | 31 / 96% / 3% | 31 / 96% / 3% |
| 15% wrong | R_wide | 37 / 89% / 2% | 37 / 89% / 2% | 34 / 89% / 3% | 34 / 89% / 3% |
| 30% wrong | R_narrow | 45 / 93% / 3% | 45 / 94% / 4% | 42 / 92% / 4% | 42 / 92% / 5% |
| 30% wrong | R_wide | 51 / 79% / 3% | 51 / 79% / 4% | 48 / 79% / 5% | 48 / 79% / 5% |

## Predictions written before the run

| | prediction | holds? | values |
|---|---|---|---|
| P1 | X0, 5% wrong: `on` has lower minutes than `off` in both regimes and accuracy not more than 0.01 lower | **holds** | R_narrow: -2.44 min, -0.0018 acc; R_wide: -2.55 min, -0.0002 acc |
| P2 | 30% wrong: the wrong-and-confident increase from `on` is larger in X2 than in X0, in both regimes | **holds** | R_narrow: X2 +0.0401 vs X0 +0.0099; R_wide: X2 +0.0433 vs X0 +0.0150 |
| P3 | in every one of the 12 (condition, world) groups and both regimes `on` has lower mean minutes | **holds** | largest change in minutes: -2.44 at ('X0', 'R_narrow', 'p05') |
| P4 | `on_mild` is between `off` and `on` (smaller saving at 5% wrong, smaller wrong-and-confident increase at 30%) in every condition and regime | **holds** | violations: none |
| P5 | the frozen decision is CONDITIONAL ON RELIABLE CHECKS | **holds** | decision: CONDITIONAL ON RELIABLE CHECKS |

Wall clock 1446 s. Cells are classified from point estimates and a paired bootstrap; some cells are misclassified by chance and no p-value is claimed. Limitations are in Addendum 22.