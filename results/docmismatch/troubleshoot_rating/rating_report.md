# Telling the tool how far to trust the drawings (Addendum 21)

Layouts: 25 real Mortar buildings (Brick metadata only); errors and the technician's answers are SIMULATED from the tool's own model family. 250 cells = 5 worlds x 2 candidate regimes x 25 buildings, 500 paired episodes x 5 policies each. The technician's rating sets the tool's prior that the documented box is wrong (mostly_right 5%, mixed 15% = the default, poor 30%; ASSUMED levels). A world is the TRUE share of wrong drawings; everything else in the world is as the tool assumes. Minutes are placeholders: only orderings and ratios mean anything. A prior that is true helps mechanically in a world built from the tool's own model, so the informative numbers are the SIZE of the gain, the cost when the rating is wrong and the break-even rating accuracy. Nothing here is evidence about real technicians, real drawings, or whether technicians can rate drawings.

## Gates

| gate | result | detail |
|---|---|---|
| G1 default-off and code path | PASS | 30 episodes identical; 30 episodes x 4 runners identical |
| G2 accounting | PASS | 20 episodes x 5 policies |
| G3 honesty (accuracy among concluded >= 0.92, matched rating, each primary world and regime) | PASS | p05/R_narrow: 0.986, p05/R_wide: 0.986, p15/R_narrow: 0.979, p15/R_wide: 0.978, p30/R_narrow: 0.990, p30/R_wide: 0.989 |
| G4 reproducibility | PASS | cell 0: first 50 episodes reproduced |
| G5 completeness, pairing and habit independence | PASS | ok; 20 episodes x 2 habits x 3 ratings identical |
| G6 layout fidelity | PASS | 25 buildings |

## Means over buildings: minutes / accuracy / wrong-and-confident / mean checks (the TOOL under each rating, then the habits)

| world | regime | entropy@mostly_right | entropy@mixed | entropy@poor | habit_A | habit_B |
|---|---|---|---|---|---|---|
| 5% wrong | R_narrow | 24 / 98% / 1% / 2.6 | 27 / 98% / 1% / 2.8 | 39 / 99% / 1% / 3.6 | 20 / 85% / 15% / 2.4 | 36 / 93% / 7% / 2.3 |
| 5% wrong | R_wide | 26 / 96% / 1% / 2.7 | 28 / 96% / 1% / 2.9 | 41 / 96% / 1% / 3.7 | 26 / 83% / 17% / 3.0 | 56 / 92% / 8% / 3.1 |
| 10% wrong | R_narrow | 28 / 97% / 2% / 2.9 | 31 / 97% / 2% / 3.1 | 42 / 98% / 1% / 3.8 | 21 / 84% / 16% / 2.5 | 41 / 93% / 7% / 2.4 |
| 10% wrong | R_wide | 30 / 93% / 2% / 3.1 | 33 / 93% / 1% / 3.3 | 45 / 93% / 1% / 4.1 | 27 / 82% / 18% / 3.1 | 70 / 91% / 9% / 3.6 |
| 15% wrong | R_narrow | 31 / 96% / 3% / 3.2 | 34 / 96% / 2% / 3.4 | 46 / 98% / 1% / 4.1 | 23 / 82% / 18% / 2.7 | 45 / 92% / 8% / 2.5 |
| 15% wrong | R_wide | 34 / 89% / 3% / 3.4 | 37 / 89% / 2% / 3.7 | 49 / 90% / 1% / 4.5 | 31 / 78% / 22% / 3.4 | 84 / 90% / 10% / 4.1 |
| 22% wrong | R_narrow | 36 / 94% / 4% / 3.6 | 39 / 95% / 3% / 3.8 | 50 / 97% / 1% / 4.5 | 24 / 80% / 20% / 2.8 | 52 / 93% / 7% / 2.7 |
| 22% wrong | R_wide | 40 / 84% / 4% / 4.0 | 44 / 85% / 3% / 4.2 | 56 / 85% / 1% / 5.1 | 34 / 74% / 26% / 3.8 | 108 / 89% / 11% / 5.0 |
| 30% wrong | R_narrow | 42 / 92% / 5% / 4.0 | 45 / 94% / 4% / 4.2 | 55 / 96% / 1% / 5.0 | 26 / 78% / 22% / 3.0 | 59 / 92% / 8% / 3.0 |
| 30% wrong | R_wide | 48 / 79% / 5% / 4.6 | 51 / 79% / 4% / 4.9 | 63 / 80% / 1% / 5.7 | 40 / 70% / 30% / 4.3 | 135 / 87% / 13% / 6.0 |

## The scenarios: a rating against the default rating (`mixed`) on the same episodes

Label shares are over the 25 buildings of a regime or the 50 cells pooled. IMPROVES / WORSE / TRADE / NEITHER are the frozen labels (5% minutes, 0.02 accuracy, paired 95% intervals); SAFETY = cells whose wrong-and-confident rate is at least 0.02 higher (REG) or lower (GAIN) with the paired interval clear of 0; COST = WORSE, TRADE or a safety regression. Deltas are the mean over buildings of the paired mean difference (rating minus default).

| scenario | world / rating | regime | IMPROVES | WORSE | TRADE | NEITHER | safety REG / GAIN | COST | d minutes | d accuracy | d wrong-and-confident | d checks | reading |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 matched-low | 5% wrong / mostly_right | R_narrow | 100% | 0% | 0% | 0% | 0% / 0% | 0% | -2.3 (-9%) | -0.002 | +0.002 | -0.16 |  |
| S1 matched-low | 5% wrong / mostly_right | R_wide | 100% | 0% | 0% | 0% | 0% / 0% | 0% | -2.4 (-9%) | -0.000 | +0.002 | -0.17 |  |
| S1 matched-low | 5% wrong / mostly_right | pooled | 100% | 0% | 0% | 0% | 0% / 0% | 0% | -2.4 (-9%) | -0.001 | +0.002 | -0.17 | **HELPS BROADLY** |
| S2 matched-high | 30% wrong / poor | R_narrow | 0% | 36% | 64% | 0% | 0% / 92% | 100% | +10.9 (+24%) | +0.023 | -0.026 | +0.73 |  |
| S2 matched-high | 30% wrong / poor | R_wide | 0% | 76% | 24% | 0% | 0% / 80% | 100% | +12.0 (+24%) | +0.010 | -0.028 | +0.82 |  |
| S2 matched-high | 30% wrong / poor | pooled | 0% | 56% | 44% | 0% | 0% / 86% | 100% | +11.5 (+24%) | +0.016 | -0.027 | +0.78 | **DOES NOT HELP** |
| S3 over-sure by 1 | 15% wrong / mostly_right | R_narrow | 100% | 0% | 0% | 0% | 0% / 0% | 0% | -2.6 (-8%) | -0.005 | +0.006 | -0.19 |  |
| S3 over-sure by 1 | 15% wrong / mostly_right | R_wide | 100% | 0% | 0% | 0% | 0% / 0% | 0% | -2.8 (-8%) | -0.002 | +0.006 | -0.21 |  |
| S3 over-sure by 1 | 15% wrong / mostly_right | pooled | 100% | 0% | 0% | 0% | 0% / 0% | 0% | -2.7 (-8%) | -0.003 | +0.006 | -0.20 | **HARMLESS** |
| S4 over-sure by 2 | 30% wrong / mostly_right | R_narrow | 80% | 0% | 12% | 8% | 12% / 0% | 16% | -2.9 (-7%) | -0.012 | +0.013 | -0.23 |  |
| S4 over-sure by 2 | 30% wrong / mostly_right | R_wide | 96% | 0% | 0% | 4% | 8% / 0% | 8% | -3.7 (-7%) | -0.003 | +0.013 | -0.28 |  |
| S4 over-sure by 2 | 30% wrong / mostly_right | pooled | 88% | 0% | 6% | 6% | 10% / 0% | 12% | -3.3 (-7%) | -0.008 | +0.013 | -0.26 | **COSTS SOMETHING** |
| S5 too cautious by 1 | 15% wrong / poor | R_narrow | 0% | 84% | 16% | 0% | 0% / 28% | 100% | +11.7 (+34%) | +0.012 | -0.014 | +0.78 |  |
| S5 too cautious by 1 | 15% wrong / poor | R_wide | 0% | 100% | 0% | 0% | 0% / 16% | 100% | +12.1 (+33%) | +0.004 | -0.013 | +0.82 |  |
| S5 too cautious by 1 | 15% wrong / poor | pooled | 0% | 92% | 8% | 0% | 0% / 22% | 100% | +11.9 (+34%) | +0.008 | -0.014 | +0.80 | **HARMFUL** |
| S6 too cautious by 2 | 5% wrong / poor | R_narrow | 0% | 100% | 0% | 0% | 0% / 0% | 100% | +12.3 (+46%) | +0.005 | -0.005 | +0.81 |  |
| S6 too cautious by 2 | 5% wrong / poor | R_wide | 0% | 100% | 0% | 0% | 0% / 0% | 100% | +12.4 (+44%) | +0.002 | -0.006 | +0.84 |  |
| S6 too cautious by 2 | 5% wrong / poor | pooled | 0% | 100% | 0% | 0% | 0% / 0% | 100% | +12.3 (+45%) | +0.003 | -0.005 | +0.83 | **HARMFUL** |

(In the world with 15% wrong drawings the matched rating IS the default, so it is a control; every difference there is exactly zero.)

### Secondary: worlds between the rating levels (reported only; no verdict)

| world | rating | regime | IMPROVES | WORSE | TRADE | NEITHER | safety REG | d minutes | d accuracy | d wrong-and-confident |
|---|---|---|---|---|---|---|---|---|---|---|
| 10% wrong | mostly_right | R_narrow | 100% | 0% | 0% | 0% | 0% | -2.6 | -0.003 | +0.005 |
| 10% wrong | mostly_right | R_wide | 100% | 0% | 0% | 0% | 0% | -2.8 | -0.001 | +0.005 |
| 10% wrong | poor | R_narrow | 0% | 96% | 4% | 0% | 0% | +11.3 | +0.008 | -0.009 |
| 10% wrong | poor | R_wide | 0% | 100% | 0% | 0% | 0% | +12.1 | +0.002 | -0.009 |
| 22% wrong | mostly_right | R_narrow | 100% | 0% | 0% | 0% | 4% | -3.1 | -0.010 | +0.011 |
| 22% wrong | mostly_right | R_wide | 92% | 0% | 0% | 8% | 4% | -3.2 | -0.003 | +0.009 |
| 22% wrong | poor | R_narrow | 0% | 76% | 24% | 0% | 0% | +10.9 | +0.016 | -0.018 |
| 22% wrong | poor | R_wide | 0% | 96% | 4% | 0% | 0% | +12.2 | +0.006 | -0.020 |

## Break-even rating accuracy

The technician rates correctly with probability q and otherwise picks either other level with equal probability; the three primary worlds (5%, 15%, 30% wrong) are equally weighted (placeholder). Expected change against always using the default prior; favourable = minutes not above, accuracy not below, wrong-and-confident not above the default's.

| regime | q | d minutes | d accuracy | d wrong-and-confident | favourable |
|---|---|---|---|---|---|
| R_narrow | 0.33 | +3.00 | +0.0023 | -0.0026 | no |
| R_narrow | 0.50 | +2.96 | +0.0035 | -0.0040 | no |
| R_narrow | 0.60 | +2.94 | +0.0042 | -0.0048 | no |
| R_narrow | 0.70 | +2.92 | +0.0049 | -0.0056 | no |
| R_narrow | 0.80 | +2.89 | +0.0057 | -0.0064 | no |
| R_narrow | 0.90 | +2.87 | +0.0064 | -0.0072 | no |
| R_narrow | 1.00 | +2.85 | +0.0071 | -0.0080 | no |
| R_wide | 0.33 | +3.06 | +0.0013 | -0.0029 | no |
| R_wide | 0.50 | +3.09 | +0.0018 | -0.0043 | no |
| R_wide | 0.60 | +3.12 | +0.0021 | -0.0052 | no |
| R_wide | 0.70 | +3.14 | +0.0024 | -0.0061 | no |
| R_wide | 0.80 | +3.16 | +0.0027 | -0.0070 | no |
| R_wide | 0.90 | +3.18 | +0.0030 | -0.0079 | no |
| R_wide | 1.00 | +3.20 | +0.0033 | -0.0088 | no |

| regime | metric | smallest favourable q | largest favourable q | favourable at q = 1 |
|---|---|---|---|---|
| R_narrow | minutes | none | none | no |
| R_narrow | accuracy | 0.33 | 1.00 | yes |
| R_narrow | wrong-and-confident | 0.33 | 1.00 | yes |
| R_narrow | ALL THREE (joint) | none | none | no |
| R_wide | minutes | none | none | no |
| R_wide | accuracy | 0.33 | 1.00 | yes |
| R_wide | wrong-and-confident | 0.33 | 1.00 | yes |
| R_wide | ALL THREE (joint) | none | none | no |

## Decision (frozen rule; about OFFERING the setting, never about shipping it): **NOT WORTH OFFERING AS BUILT**

S1 reads HELPS BROADLY, S2 reads DOES NOT HELP; joint q* = R_narrow: none, R_wide: none against the bar of 0.75. The default stays `mixed` either way.

## Context (no verdict): the tool under each rating against the two habits, in the primary worlds

Addendum 19's label against BOTH habits (WINS / LOSES share of buildings), then against each habit: WINS / LOSES / BUYS ACCURACY (Addendum 20's secondary label).

| world | regime | rating | vs both: WINS / LOSES | vs habit_A: WINS / LOSES / BUYS ACC | vs habit_B: WINS / LOSES / BUYS ACC |
|---|---|---|---|---|---|
| 5% wrong | R_narrow | mostly_right (matched) | 0% / 0% | 0% / 0% / 96% | 100% / 0% / 0% |
| 5% wrong | R_narrow | mixed | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| 5% wrong | R_narrow | poor | 0% / 0% | 0% / 0% / 100% | 0% / 0% / 8% |
| 5% wrong | R_wide | mostly_right (matched) | 4% / 0% | 4% / 0% / 12% | 100% / 0% / 0% |
| 5% wrong | R_wide | mixed | 0% / 0% | 0% / 0% / 60% | 100% / 0% / 0% |
| 5% wrong | R_wide | poor | 0% / 0% | 0% / 0% / 100% | 84% / 0% / 0% |
| 15% wrong | R_narrow | mostly_right | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| 15% wrong | R_narrow | mixed (matched) | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| 15% wrong | R_narrow | poor | 0% / 0% | 0% / 0% / 100% | 0% / 0% / 0% |
| 15% wrong | R_wide | mostly_right | 0% / 0% | 0% / 0% / 48% | 72% / 0% / 0% |
| 15% wrong | R_wide | mixed (matched) | 0% / 0% | 0% / 0% / 80% | 76% / 0% / 0% |
| 15% wrong | R_wide | poor | 0% / 0% | 0% / 0% / 100% | 80% / 0% / 0% |
| 30% wrong | R_narrow | mostly_right | 0% / 0% | 0% / 0% / 100% | 88% / 0% / 0% |
| 30% wrong | R_narrow | mixed | 0% / 0% | 0% / 0% / 100% | 92% / 0% / 0% |
| 30% wrong | R_narrow | poor (matched) | 0% / 0% | 0% / 0% / 100% | 20% / 0% / 0% |
| 30% wrong | R_wide | mostly_right | 0% / 0% | 0% / 0% / 84% | 0% / 0% / 0% |
| 30% wrong | R_wide | mixed | 0% / 0% | 0% / 0% / 100% | 4% / 0% / 0% |
| 30% wrong | R_wide | poor (matched) | 0% / 0% | 0% / 0% / 100% | 8% / 0% / 0% |

## Predictions written before the run

| | prediction | holds? | values (per regime) |
|---|---|---|---|
| P1 | S1: minutes lower than the default in both regimes and accuracy not more than 0.01 lower | **holds** | R_narrow: -2.316, -0.002; R_wide: -2.444, -0.000 |
| P2 | S2: wrong-and-confident lower in both regimes and accuracy not lower | **holds** | R_narrow: -0.026, 0.023; R_wide: -0.028, 0.010 |
| P3 | S4: wrong-and-confident at least 0.02 higher in both regimes | **does not hold** | R_narrow: 0.013; R_wide: 0.013 |
| P4 | S6: minutes higher in both regimes | **holds** | R_narrow: 12.295; R_wide: 12.363 |
| P5 | at q = 0.70 the expected change is favourable on all three metrics in both regimes | **does not hold** | R_narrow: 2.916, 0.005, -0.006; R_wide: 3.137, 0.002, -0.006 |

Wall clock 529 s. Cells are classified from point estimates and a paired bootstrap; some cells are misclassified by chance and no p-value is claimed. Limitations are in Addendum 21.