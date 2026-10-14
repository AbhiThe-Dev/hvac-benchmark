# The troubleshooting tool on real documented layouts (Addendum 20)

Layouts: 25 real Mortar buildings (Brick metadata only); errors and the technician's answers are SIMULATED from the tool's own model family. 150 cells = 3 worlds x 2 candidate regimes x 25 buildings, 500 paired episodes x 5 policies each. The tool always runs on its ASSUMED default settings; every policy is charged the TRUE minutes. `habit_A` and `habit_B` are ASSUMED stand-ins for trial and error. Minutes are placeholders: only orderings and ratios mean anything. The Brick graphs carry no location, so 'same air handler' stands in for 'nearby' and identifier order stands in for adjacency. Nothing here is evidence about real technicians or real documentation errors.

## Gates

| gate | result | detail |
|---|---|---|
| G1 code path | PASS | 30 episodes x 4 runners identical |
| G2 accounting | PASS | 20 episodes x 5 policies |
| G3 honesty (accuracy among concluded >= 0.92, W_default, each regime) | PASS | R_narrow: 0.977, R_wide: 0.976 |
| G4 reproducibility | PASS | cell 0: first 50 episodes reproduced |
| G5 completeness and pairing | PASS | ok |
| G6 layout fidelity | PASS | 25 buildings |

## The map, per (world, regime) and tool policy (against BOTH habits; Addendum 19's rule)

| world | regime | policy | WINS | LOSES | NEITHER | reading |
|---|---|---|---|---|---|---|
| W_default | R_narrow | entropy | 0% | 0% | 100% | DOES NOT HELP |
| W_default | R_narrow | split_half | 0% | 0% | 100% | DOES NOT HELP |
| W_default | R_narrow | random | 0% | 100% | 0% | DOES NOT HELP |
| W_default | R_wide | entropy | 0% | 0% | 100% | DOES NOT HELP |
| W_default | R_wide | split_half | 0% | 0% | 100% | DOES NOT HELP |
| W_default | R_wide | random | 0% | 100% | 0% | DOES NOT HELP |
| W_documented | R_narrow | entropy | 0% | 0% | 100% | DOES NOT HELP |
| W_documented | R_narrow | split_half | 0% | 0% | 100% | DOES NOT HELP |
| W_documented | R_narrow | random | 0% | 92% | 8% | DOES NOT HELP |
| W_documented | R_wide | entropy | 0% | 0% | 100% | DOES NOT HELP |
| W_documented | R_wide | split_half | 0% | 0% | 100% | DOES NOT HELP |
| W_documented | R_wide | random | 0% | 100% | 0% | DOES NOT HELP |
| W_stress | R_narrow | entropy | 0% | 0% | 100% | DOES NOT HELP |
| W_stress | R_narrow | split_half | 0% | 0% | 100% | DOES NOT HELP |
| W_stress | R_narrow | random | 0% | 0% | 100% | DOES NOT HELP |
| W_stress | R_wide | entropy | 0% | 0% | 100% | DOES NOT HELP |
| W_stress | R_wide | split_half | 0% | 0% | 100% | DOES NOT HELP |
| W_stress | R_wide | random | 0% | 100% | 0% | DOES NOT HELP |

All cells pooled:

| policy | WINS | LOSES | reading |
|---|---|---|---|
| entropy | 0% | 0% | **DOES NOT HELP** |
| split_half | 0% | 0% | **DOES NOT HELP** |
| random | 0% | 82% | **DOES NOT HELP** |

## Against each habit separately, with the secondary BUYS ACCURACY label (fraction of buildings)

| world | regime | policy | vs habit_A: WINS / LOSES / BUYS ACCURACY | vs habit_B: WINS / LOSES / BUYS ACCURACY |
|---|---|---|---|---|
| W_default | R_narrow | entropy | 0% / 0% / 100% | 100% / 0% / 0% |
| W_default | R_narrow | split_half | 0% / 0% / 100% | 0% / 0% / 0% |
| W_default | R_wide | entropy | 0% / 0% / 80% | 72% / 0% / 0% |
| W_default | R_wide | split_half | 0% / 0% / 100% | 24% / 0% / 0% |
| W_documented | R_narrow | entropy | 0% / 0% / 100% | 100% / 0% / 0% |
| W_documented | R_narrow | split_half | 0% / 0% / 100% | 4% / 0% / 0% |
| W_documented | R_wide | entropy | 0% / 0% / 52% | 100% / 0% / 0% |
| W_documented | R_wide | split_half | 0% / 0% / 100% | 76% / 0% / 0% |
| W_stress | R_narrow | entropy | 0% / 0% / 100% | 28% / 0% / 0% |
| W_stress | R_narrow | split_half | 0% / 0% / 100% | 0% / 0% / 64% |
| W_stress | R_wide | entropy | 0% / 0% / 100% | 100% / 0% / 0% |
| W_stress | R_wide | split_half | 0% / 0% / 88% | 80% / 0% / 0% |

## Means over buildings: minutes / accuracy / wrong-and-confident / unresolved / entries

| world | regime | entropy | split_half | random | habit_A | habit_B |
|---|---|---|---|---|---|---|
| W_default | R_narrow | 34 / 96% / 2% / 4% / 4.3 | 44 / 95% / 3% / 4% / 4.8 | 196 / 90% / 1% / 32% / 9.3 | 22 / 83% / 17% / 0% / 3.7 | 44 / 93% / 7% / 0% / 3.5 |
| W_default | R_wide | 37 / 89% / 2% / 11% / 4.6 | 49 / 87% / 3% / 31% / 5.6 | 269 / 75% / 0% / 82% / 12.0 | 31 / 78% / 22% / 0% / 4.4 | 83 / 90% / 10% / 0% / 5.1 |
| W_documented | R_narrow | 27 / 98% / 1% / 2% / 3.8 | 37 / 97% / 3% / 2% / 4.2 | 189 / 92% / 1% / 30% / 9.1 | 20 / 86% / 14% / 0% / 3.4 | 36 / 93% / 7% / 0% / 3.3 |
| W_documented | R_wide | 28 / 96% / 1% / 5% / 3.9 | 40 / 94% / 2% / 24% / 4.8 | 263 / 84% / 0% / 79% / 11.9 | 25 / 84% / 16% / 0% / 3.9 | 56 / 92% / 8% / 0% / 4.1 |
| W_stress | R_narrow | 61 / 78% / 12% / 18% / 6.3 | 74 / 72% / 18% / 17% / 7.2 | 227 / 70% / 6% / 52% / 10.7 | 24 / 57% / 43% / 0% / 3.7 | 65 / 63% / 37% / 0% / 4.1 |
| W_stress | R_wide | 66 / 69% / 10% / 30% / 6.7 | 77 / 61% / 13% / 54% / 8.2 | 277 / 47% / 2% / 89% / 12.4 | 28 / 51% / 49% / 0% / 4.1 | 94 / 55% / 45% / 0% / 5.3 |

## Per building, W_default: rooms, boxes, handlers; mean candidates; minutes / accuracy of entropy, habit_A, habit_B; label (vs both)

| building | rooms | boxes | handlers | regime | K | entropy | habit_A | habit_B | label |
|---|---|---|---|---|---|---|---|---|---|
| bldg2 | 25 | 25 | 2 | R_narrow | 8.0 | 31 / 98% | 21 / 83% | 44 / 91% | NEITHER |
| bldg2 | 25 | 25 | 2 | R_wide | 25.0 | 35 / 90% | 32 / 78% | 74 / 93% | NEITHER |
| bldg4 | 28 | 28 | 1 | R_narrow | 8.0 | 33 / 95% | 21 / 83% | 46 / 93% | NEITHER |
| bldg4 | 28 | 28 | 1 | R_wide | 28.0 | 37 / 88% | 33 / 74% | 73 / 91% | NEITHER |
| bldg5 | 124 | 124 | 10 | R_narrow | 8.0 | 36 / 97% | 23 / 83% | 44 / 94% | NEITHER |
| bldg5 | 124 | 124 | 10 | R_wide | 40.0 | 38 / 90% | 30 / 78% | 72 / 92% | NEITHER |
| bldg6 | 132 | 132 | 11 | R_narrow | 8.0 | 33 / 95% | 23 / 82% | 43 / 93% | NEITHER |
| bldg6 | 132 | 132 | 11 | R_wide | 40.0 | 37 / 88% | 34 / 77% | 96 / 89% | NEITHER |
| bldg8 | 24 | 24 | 1 | R_narrow | 8.0 | 35 / 96% | 22 / 83% | 44 / 92% | NEITHER |
| bldg8 | 24 | 24 | 1 | R_wide | 24.0 | 39 / 89% | 28 / 79% | 79 / 90% | NEITHER |
| bldg9 | 126 | 126 | 2 | R_narrow | 8.0 | 33 / 95% | 21 / 87% | 44 / 93% | NEITHER |
| bldg9 | 126 | 126 | 2 | R_wide | 40.0 | 37 / 88% | 29 / 74% | 105 / 88% | NEITHER |
| bldg10 | 16 | 16 | 3 | R_narrow | 8.0 | 32 / 97% | 24 / 80% | 40 / 94% | NEITHER |
| bldg10 | 16 | 16 | 3 | R_wide | 16.0 | 34 / 94% | 25 / 83% | 56 / 91% | NEITHER |
| bldg11 | 394 | 394 | 9 | R_narrow | 8.0 | 34 / 96% | 22 / 82% | 45 / 93% | NEITHER |
| bldg11 | 394 | 394 | 9 | R_wide | 40.0 | 40 / 87% | 30 / 79% | 95 / 90% | NEITHER |
| bldg12 | 98 | 98 | 5 | R_narrow | 8.0 | 30 / 96% | 22 / 83% | 42 / 95% | NEITHER |
| bldg12 | 98 | 98 | 5 | R_wide | 40.0 | 37 / 90% | 33 / 75% | 91 / 91% | NEITHER |
| bldg13 | 24 | 24 | 1 | R_narrow | 8.0 | 36 / 95% | 24 / 83% | 44 / 92% | NEITHER |
| bldg13 | 24 | 24 | 1 | R_wide | 24.0 | 35 / 91% | 29 / 80% | 74 / 91% | NEITHER |
| bldg15 | 129 | 129 | 2 | R_narrow | 8.0 | 33 / 95% | 22 / 85% | 45 / 94% | NEITHER |
| bldg15 | 129 | 129 | 2 | R_wide | 40.0 | 37 / 90% | 33 / 80% | 98 / 87% | NEITHER |
| bldg18 | 144 | 144 | 5 | R_narrow | 8.0 | 33 / 97% | 22 / 83% | 42 / 92% | NEITHER |
| bldg18 | 144 | 144 | 5 | R_wide | 40.0 | 38 / 86% | 32 / 78% | 86 / 89% | NEITHER |
| bldg20 | 13 | 13 | 2 | R_narrow | 8.0 | 33 / 96% | 24 / 81% | 44 / 93% | NEITHER |
| bldg20 | 13 | 13 | 2 | R_wide | 13.0 | 33 / 94% | 27 / 81% | 50 / 92% | NEITHER |
| bldg27 | 17 | 17 | 1 | R_narrow | 8.0 | 35 / 96% | 21 / 83% | 44 / 91% | NEITHER |
| bldg27 | 17 | 17 | 1 | R_wide | 17.0 | 36 / 89% | 28 / 77% | 66 / 90% | NEITHER |
| bldg28 | 45 | 45 | 1 | R_narrow | 8.0 | 34 / 95% | 24 / 81% | 47 / 91% | NEITHER |
| bldg28 | 45 | 45 | 1 | R_wide | 40.0 | 38 / 89% | 35 / 77% | 111 / 89% | NEITHER |
| bldg30 | 99 | 99 | 2 | R_narrow | 8.0 | 36 / 97% | 22 / 83% | 45 / 92% | NEITHER |
| bldg30 | 99 | 99 | 2 | R_wide | 40.0 | 35 / 90% | 31 / 80% | 89 / 91% | NEITHER |
| bldg32 | 107 | 107 | 7 | R_narrow | 8.0 | 33 / 97% | 22 / 82% | 44 / 94% | NEITHER |
| bldg32 | 107 | 107 | 7 | R_wide | 40.0 | 40 / 87% | 32 / 76% | 89 / 90% | NEITHER |
| bldg34 | 39 | 39 | 4 | R_narrow | 8.0 | 34 / 97% | 23 / 83% | 45 / 91% | NEITHER |
| bldg34 | 39 | 39 | 4 | R_wide | 39.0 | 32 / 91% | 32 / 81% | 74 / 92% | NEITHER |
| bldg36 | 43 | 43 | 1 | R_narrow | 8.0 | 33 / 98% | 23 / 82% | 45 / 93% | NEITHER |
| bldg36 | 43 | 43 | 1 | R_wide | 40.0 | 37 / 89% | 33 / 78% | 99 / 88% | NEITHER |
| bldg37 | 283 | 283 | 7 | R_narrow | 8.0 | 36 / 94% | 22 / 84% | 47 / 94% | NEITHER |
| bldg37 | 283 | 283 | 7 | R_wide | 40.0 | 36 / 89% | 31 / 78% | 94 / 90% | NEITHER |
| bldg39 | 18 | 18 | 2 | R_narrow | 8.0 | 32 / 96% | 21 / 85% | 43 / 94% | NEITHER |
| bldg39 | 18 | 18 | 2 | R_wide | 18.0 | 36 / 92% | 26 / 80% | 55 / 94% | NEITHER |
| bldg40 | 87 | 87 | 2 | R_narrow | 8.0 | 33 / 97% | 22 / 83% | 41 / 94% | NEITHER |
| bldg40 | 87 | 87 | 2 | R_wide | 40.0 | 34 / 90% | 32 / 81% | 88 / 87% | NEITHER |
| bldg42 | 13 | 13 | 1 | R_narrow | 8.0 | 33 / 97% | 22 / 82% | 46 / 94% | NEITHER |
| bldg42 | 13 | 13 | 1 | R_wide | 13.0 | 37 / 93% | 28 / 79% | 61 / 92% | NEITHER |
| bldg43 | 52 | 52 | 1 | R_narrow | 8.0 | 34 / 97% | 22 / 83% | 45 / 93% | NEITHER |
| bldg43 | 52 | 52 | 1 | R_wide | 40.0 | 40 / 87% | 35 / 74% | 108 / 87% | NEITHER |
| bldg44 | 44 | 44 | 2 | R_narrow | 8.0 | 36 / 96% | 23 / 81% | 44 / 92% | NEITHER |
| bldg44 | 44 | 44 | 2 | R_wide | 40.0 | 36 / 87% | 32 / 76% | 94 / 90% | NEITHER |

## Candidates and minutes (mean over cells; entropy, minutes)

| regime | mean candidates | cells | entropy | habit_A | habit_B |
|---|---|---|---|---|---|
| R_narrow | 0-8 | 75 | 41 | 22 | 48 |
| R_wide | 8-20 | 15 | 41 | 25 | 60 |
| R_wide | 20-41 | 60 | 44 | 29 | 82 |

## Predictions written before the run

| | prediction | holds? | values |
|---|---|---|---|
| P1 | entropy WINS in 0% of buildings in each of W_default and W_stress x both regimes | **holds** | ('W_default', 'R_narrow'): 0.000; ('W_default', 'R_wide'): 0.000; ('W_stress', 'R_narrow'): 0.000; ('W_stress', 'R_wide'): 0.000 |
| P2 | vs habit_B alone, entropy's WINS fraction is higher in W_documented than in W_default and W_stress | **holds** | W_default: 0.860; W_documented: 1.000; W_stress: 0.640 |
| P3 | vs habit_B alone, entropy's WINS fraction is higher in R_wide than in R_narrow | **holds** | R_narrow: 0.760; R_wide: 0.907 |
| P4 | entropy's wrong-and-confident rate is higher in W_stress than in W_default, in both regimes | **holds** | R_narrow: (0.119, 0.022); R_wide: (0.098, 0.021) |
| P5 | entropy's accuracy exceeds habit_A's in each of the six groups | **holds** | ('W_default', 'R_narrow'): (0.963, 0.827); ('W_default', 'R_wide'): (0.895, 0.781); ('W_documented', 'R_narrow'): (0.978, 0.858); ('W_documented', 'R_wide'): (0.956, 0.843); ('W_stress', 'R_narrow'): (0.775, 0.574); ('W_stress', 'R_wide'): (0.69, 0.515) |

Wall clock 1085 s. Cells are classified from point estimates and a paired bootstrap on minutes; some cells are misclassified by chance and no p-value is claimed. Limitations are in Addendum 20.