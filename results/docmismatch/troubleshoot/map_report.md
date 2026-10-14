# Sensitivity map: technician-guided tool vs trial-and-error stand-ins (Addendum 19)

Simulation only. 486 truth cells x 500 paired episodes x 5 policies; the tool always runs on its ASSUMED default settings, the simulated technician answers from the TRUE numbers and every policy is charged the TRUE minutes. `habit_A` and `habit_B` are ASSUMED stand-ins for trial and error, not observed behaviour. All minutes are placeholders: only orderings and ratios mean anything. Nothing here is evidence about real technicians.

## Gates

| gate | result | detail |
|---|---|---|
| G1 code path | PASS | 30 episodes x 4 runners identical |
| G2 accounting | PASS | 20 episodes x 5 policies |
| G3 honesty (accuracy among concluded >= 0.92, assumptions-correct cells) | PASS | K=3: 0.972, K=6: 0.988, K=10: 0.977 |
| G4 reproducibility | PASS | cell 78: first 50 episodes reproduced |
| G5 completeness and pairing | PASS | ok |

## The map, per tool policy (against BOTH habits: WINS only if it wins against each, LOSES if it loses against either)

| policy | WINS | LOSES | NEITHER | of which trade-off | reading |
|---|---|---|---|---|---|
| entropy | 0% | 5% | 95% | 5 cells | **DOES NOT HELP** |
| split_half | 0% | 13% | 87% | 5 cells | **DOES NOT HELP** |
| random | 0% | 31% | 69% | 0 cells | **DOES NOT HELP** |

Against each habit separately (WINS / LOSES fraction of cells):

| policy | vs habit_A | vs habit_B |
|---|---|---|
| entropy | 0% / 0% | 43% / 5% |
| split_half | 0% / 0% | 14% / 13% |
| random | 0% / 6% | 0% / 31% |

## Best case (the tool's assumptions exactly right) and robustness (at least one assumption wrong)

| policy | assumptions-correct cells (K = 3, 6, 10) | cells with a misspecified factor |
|---|---|---|
| entropy | NEITHER, NEITHER, NEITHER | WINS 0%, LOSES 5% |
| split_half | NEITHER, NEITHER, NEITHER | WINS 0%, LOSES 13% |
| random | NEITHER, NEITHER, LOSES | WINS 0%, LOSES 31% |

## Marginals: WINS / LOSES by level of each factor (strength: WINS >= 80%; weakness: LOSES >= 25%)

### entropy

| factor | level | WINS | LOSES | cells | |
|---|---|---|---|---|---|
| K | 3 | 0% | 6% | 162 |  |
| K | 6 | 0% | 4% | 162 |  |
| K | 10 | 0% | 5% | 162 |  |
| p_wrong | 0.05 | 0% | 0% | 162 |  |
| p_wrong | 0.15 | 0% | 3% | 162 |  |
| p_wrong | 0.3 | 0% | 11% | 162 |  |
| p_act | 0.05 | 0% | 5% | 162 |  |
| p_act | 0.15 | 0% | 4% | 162 |  |
| p_act | 0.3 | 0% | 6% | 162 |  |
| near | 0.05 | 0% | 4% | 162 |  |
| near | 0.25 | 0% | 5% | 162 |  |
| near | 1.0 | 0% | 6% | 162 |  |
| rates | assumed | 0% | 9% | 243 |  |
| rates | degraded | 0% | 0% | 243 |  |
| costs | assumed | 0% | 0% | 162 |  |
| costs | access_x3 | 0% | 0% | 162 |  |
| costs | trace_cheap | 0% | 14% | 162 |  |

### split_half

| factor | level | WINS | LOSES | cells | |
|---|---|---|---|---|---|
| K | 3 | 0% | 6% | 162 |  |
| K | 6 | 0% | 18% | 162 |  |
| K | 10 | 0% | 16% | 162 |  |
| p_wrong | 0.05 | 0% | 6% | 162 |  |
| p_wrong | 0.15 | 0% | 12% | 162 |  |
| p_wrong | 0.3 | 0% | 22% | 162 |  |
| p_act | 0.05 | 0% | 7% | 162 |  |
| p_act | 0.15 | 0% | 10% | 162 |  |
| p_act | 0.3 | 0% | 23% | 162 |  |
| near | 0.05 | 0% | 16% | 162 |  |
| near | 0.25 | 0% | 14% | 162 |  |
| near | 1.0 | 0% | 10% | 162 |  |
| rates | assumed | 0% | 26% | 243 | weakness |
| rates | degraded | 0% | 1% | 243 |  |
| costs | assumed | 0% | 4% | 162 |  |
| costs | access_x3 | 0% | 7% | 162 |  |
| costs | trace_cheap | 0% | 28% | 162 | weakness |

## `split_half` against `entropy` in the misspecified cells

| | cells |
|---|---|
| both WIN | 0 |
| only split_half WINS | 0 |
| only entropy WINS | 0 |
| neither WINS | 483 |
| entropy LOSES, split_half does not | 2 |
| split_half LOSES, entropy does not | 44 |

## Predictions written before the run

| | prediction | holds? | values |
|---|---|---|---|
| P1 | the advantage grows with K (WINS at K = 10 vs K = 3) | **does not hold** | 0.000 vs 0.000 |
| P2 | it shrinks as P(documented feeder wrong) falls (WINS at 0.30 vs 0.05) | **does not hold** | 0.000 vs 0.000 |
| P3 | entropy loses ground to split_half as the truth departs from the tool's prior (W_entropy - W_split_half at 3 departures vs 0) | **does not hold** | 0.000 vs 0.000 |
| P4 | expensive access widens the lead (WINS at access x 3 vs as assumed) | **does not hold** | 0.000 vs 0.000 |
| P5 | with degraded hit rates split_half wins at least as often as entropy (split_half vs entropy) | **holds** | 0.000 vs 0.000 |

## By true cause, the default cell (K = 6, everything as assumed)

| true cause | episodes | entropy: min / acc | split_half: min / acc | random: min / acc | habit_A: min / acc | habit_B: min / acc |
|---|---|---|---|---|---|---|
| doc_other | 352 | 20 / 99% | 21 / 99% | 142 / 99% | 17 / 89% | 31 / 91% |
| doc_acts_fail | 73 | 42 / 99% | 52 / 95% | 234 / 95% | 10 / 97% | 31 / 90% |
| wrong VAV-1 | 23 | 79 / 96% | 123 / 96% | 193 / 87% | 26 / 74% | 50 / 100% |
| wrong VAV-2 | 25 | 62 / 96% | 110 / 88% | 198 / 92% | 33 / 72% | 72 / 92% |
| wrong VAV-3 | 10 | 106 / 80% | 90 / 50% | 240 / 90% | 43 / 60% | 100 / 100% |
| wrong VAV-4 | 8 | 102 / 100% | 76 / 75% | 218 / 88% | 47 / 38% | 128 / 88% |
| wrong VAV-5 | 3 | 82 / 100% | 93 / 100% | 268 / 100% | 54 / 33% | 150 / 100% |
| unlisted | 6 | 153 / 83% | 185 / 100% | 255 / 50% | 62 / 67% | 146 / 83% |

## Input burden, honesty and secondary metrics (means over cells)

| policy | entries per session | unresolved | wrong-and-confident | accuracy | minutes | minutes per correct (median over cells) |
|---|---|---|---|---|---|---|
| entropy | 4.6 | 7% | 6% | 91% | 46 | 47 |
| split_half | 4.6 | 9% | 8% | 88% | 54 | 55 |
| random | 8.1 | 26% | 4% | 88% | 182 | 189 |
| habit_A | 3.4 | 0% | 28% | 72% | 27 | 34 |
| habit_B | 3.5 | 0% | 20% | 80% | 47 | 55 |

Wall clock 306 s. Cells are classified from point estimates and a paired bootstrap on minutes; with 486 cells x 2 policies some cells are misclassified by chance, and no p-value is claimed. Limitations are listed in Addendum 19 (independent answer noise, truths drawn from the tool's own model family, assumed habits, placeholder minutes, no parallel waiting, one connection type).