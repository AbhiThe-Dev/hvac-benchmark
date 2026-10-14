# The tool with only the minimum data it needs (Addendum 23)

Layouts: 25 real Mortar buildings (Brick metadata only); errors and the technician's answers are SIMULATED from the tool's own model family. 100 cells = 2 worlds x 2 candidate caps x 25 buildings, 300 paired episodes x 6 policies each. Level MIN = the equipment list and the drawings' claims only: no area for any box, so the candidate list is the documented box then the other boxes in identifier order, capped at K, all equally likely. Level GROUPED = Addendum 20's setting (same air handler first, weights 1 and 0.25). The TRUE cause is drawn over ALL boxes of the building; a wrong feeder that is not on the tool's list counts as 'unlisted' for that policy (the OFF-LIST share). In the LOCAL world a wrong feeder is likely on the same air handler; in the ANYWHERE world it is equally likely to be any box. `habit_A` and `habit_B` are ASSUMED stand-ins for trial and error, not real technicians. Minutes are placeholders: only orderings and ratios mean anything. Nothing here is evidence about real technicians or real drawings.

## Gates

| gate | result | detail |
|---|---|---|
| G1 code path (no grouping information: levels identical) | PASS | 30 episodes x 3 policies identical across levels; 30 episodes x 4 runners identical |
| G2 accounting | PASS | 20 episodes x 5 policies |
| G3 coverage bookkeeping | PASS | 100 cells recomputed |
| G4 reproducibility | PASS | cell 0: first 50 episodes reproduced |
| G5 completeness and pairing | PASS | ok |
| G6 layout fidelity | PASS | 25 buildings |

## Means over buildings: minutes / accuracy / actionable / wrong-and-confident / unresolved / off-list share

Accuracy counts a correct 'unlisted' as right; ACTIONABLE = right and the answer names a cause (not 'unlisted'), i.e. the technician knows what to do.

| world | cap | policy | min (equipment list + claims only) | grouped (Addendum 20's setting) |
|---|---|---|---|---|
| errors local | K8 | entropy | 39 / 96% / 86% / 2% / 13% / 11% | 39 / 96% / 87% / 2% / 12% / 10% |
| errors local | K8 | habit_A | 24 / 80% / 75% / 20% / 0% / 11% | 24 / 81% / 76% / 19% / 0% / 10% |
| errors local | K8 | habit_B | 54 / 91% / 81% / 9% / 0% / 11% | 53 / 92% / 82% / 8% / 0% / 10% |
| errors local | K40 | entropy | 38 / 91% / 86% / 2% / 13% / 5% | 38 / 91% / 87% / 2% / 13% / 3% |
| errors local | K40 | habit_A | 32 / 76% / 76% / 24% / 0% / 5% | 31 / 77% / 77% / 23% / 0% / 3% |
| errors local | K40 | habit_B | 102 / 89% / 86% / 11% / 0% / 5% | 95 / 89% / 87% / 11% / 0% / 3% |
| errors anywhere | K8 | entropy | 38 / 96% / 87% / 2% / 12% / 10% | 38 / 96% / 87% / 2% / 12% / 10% |
| errors anywhere | K8 | habit_A | 24 / 81% / 76% / 19% / 0% / 10% | 24 / 81% / 76% / 19% / 0% / 10% |
| errors anywhere | K8 | habit_B | 52 / 92% / 82% / 8% / 0% / 10% | 53 / 92% / 82% / 8% / 0% / 10% |
| errors anywhere | K40 | entropy | 38 / 91% / 86% / 2% / 13% / 5% | 38 / 91% / 86% / 2% / 13% / 5% |
| errors anywhere | K40 | habit_A | 32 / 77% / 76% / 23% / 0% / 5% | 32 / 77% / 77% / 23% / 0% / 5% |
| errors anywhere | K40 | habit_B | 102 / 89% / 86% / 11% / 0% / 5% | 103 / 89% / 86% / 11% / 0% / 5% |

## What grouping is worth to the tool (grouped against min, same episodes)

Labels are Addendum 21's (5% minutes, 0.02 accuracy, paired intervals); IMPROVES means grouping is better. Deltas are grouped minus min, mean over buildings.

| world | cap | IMPROVES | WORSE | TRADE | NEITHER | d minutes | d accuracy | d actionable | d off-list share |
|---|---|---|---|---|---|---|---|---|---|
| errors local | K8 | 4% | 0% | 0% | 96% | -0.4 | -0.000 | +0.008 | -0.009 |
| errors local | K40 | 4% | 12% | 0% | 84% | -0.4 | -0.002 | +0.009 | -0.015 |
| errors anywhere | K8 | 0% | 0% | 0% | 100% | -0.0 | +0.000 | +0.000 | +0.000 |
| errors anywhere | K40 | 4% | 4% | 0% | 92% | -0.1 | +0.000 | -0.001 | +0.002 |

## The tool against the two habits, within a level (share of buildings; context, no verdict)

Addendum 19's label against BOTH habits (WINS / LOSES), then against each habit: WINS / LOSES / BUYS ACCURACY (Addendum 20's secondary label).

| world | cap | level | vs both: WINS / LOSES | vs habit_A: WINS / LOSES / BUYS ACC | vs habit_B: WINS / LOSES / BUYS ACC |
|---|---|---|---|---|---|
| errors local | K8 | min | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| errors local | K8 | grouped | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| errors local | K40 | min | 0% / 0% | 0% / 0% / 88% | 84% / 0% / 0% |
| errors local | K40 | grouped | 0% / 0% | 0% / 0% / 88% | 88% / 0% / 0% |
| errors anywhere | K8 | min | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| errors anywhere | K8 | grouped | 0% / 0% | 0% / 0% / 100% | 100% / 0% / 0% |
| errors anywhere | K40 | min | 0% / 0% | 0% / 0% / 72% | 76% / 0% / 0% |
| errors anywhere | K40 | grouped | 0% / 0% | 0% / 0% / 76% | 76% / 0% / 0% |

## Per building, errors anywhere, K40 (level min): how coverage falls with building size

| building | rooms | boxes | off-list share | entropy minutes / accuracy / actionable | habit_A minutes / accuracy | habit_B minutes / accuracy |
|---|---|---|---|---|---|---|
| bldg20 | 13 | 13 | 0% | 34 / 91% / 91% | 26 / 81% | 56 / 92% |
| bldg42 | 13 | 13 | 0% | 34 / 94% / 93% | 24 / 80% | 51 / 93% |
| bldg10 | 16 | 16 | 0% | 39 / 90% / 88% | 26 / 81% | 58 / 91% |
| bldg27 | 17 | 17 | 0% | 37 / 93% / 92% | 25 / 83% | 61 / 93% |
| bldg39 | 18 | 18 | 0% | 30 / 93% / 92% | 28 / 84% | 49 / 93% |
| bldg8 | 24 | 24 | 0% | 36 / 88% / 88% | 25 / 81% | 72 / 91% |
| bldg13 | 24 | 24 | 0% | 40 / 87% / 86% | 30 / 76% | 74 / 90% |
| bldg2 | 25 | 25 | 0% | 39 / 87% / 87% | 31 / 74% | 72 / 92% |
| bldg4 | 28 | 28 | 0% | 39 / 88% / 86% | 31 / 80% | 74 / 92% |
| bldg34 | 39 | 39 | 0% | 43 / 86% / 85% | 37 / 72% | 113 / 89% |
| bldg36 | 43 | 43 | 2% | 39 / 87% / 85% | 35 / 75% | 114 / 83% |
| bldg44 | 44 | 44 | 3% | 37 / 89% / 86% | 31 / 78% | 98 / 92% |
| bldg28 | 45 | 45 | 1% | 42 / 85% / 82% | 31 / 75% | 114 / 87% |
| bldg43 | 52 | 52 | 2% | 39 / 90% / 88% | 35 / 76% | 110 / 91% |
| bldg40 | 87 | 87 | 7% | 37 / 92% / 86% | 40 / 76% | 121 / 89% |
| bldg12 | 98 | 98 | 10% | 39 / 93% / 84% | 38 / 73% | 124 / 86% |
| bldg30 | 99 | 99 | 6% | 36 / 90% / 85% | 31 / 74% | 129 / 87% |
| bldg32 | 107 | 107 | 11% | 45 / 93% / 82% | 41 / 75% | 166 / 86% |
| bldg5 | 124 | 124 | 10% | 38 / 91% / 84% | 31 / 77% | 132 / 87% |
| bldg9 | 126 | 126 | 12% | 39 / 92% / 83% | 39 / 73% | 129 / 83% |
| bldg15 | 129 | 129 | 8% | 34 / 93% / 87% | 32 / 79% | 111 / 89% |
| bldg6 | 132 | 132 | 12% | 43 / 93% / 82% | 34 / 74% | 137 / 87% |
| bldg18 | 144 | 144 | 12% | 44 / 91% / 80% | 35 / 69% | 144 / 85% |
| bldg37 | 283 | 283 | 9% | 37 / 95% / 87% | 29 / 77% | 108 / 89% |
| bldg11 | 394 | 394 | 11% | 36 / 96% / 86% | 36 / 72% | 141 / 87% |

## Predictions written before the run

| | prediction | holds? | values |
|---|---|---|---|
| P1 | local world: entropy@min has a higher off-list share and more minutes than entropy@grouped, at each cap | **holds** | K8: off-list 0.110 vs 0.101, minutes 38.9 vs 38.5; K40: off-list 0.045 vs 0.031, minutes 38.2 vs 37.8 |
| P2 | anywhere world: entropy@min is within 10% of entropy@grouped in minutes and within 0.02 in off-list share, at each cap | **holds** | K8: minutes 38.1 vs 38.1, off-list 0.103 vs 0.103; K40: minutes 38.2 vs 38.1, off-list 0.046 vs 0.048 |
| P3 | anywhere world: the off-list share of entropy@min is at least 0.08 at K8 and lower at K40 | **holds** | K8: 0.103; K40: 0.046 |
| P4 | entropy@min has higher accuracy than habit_A@min in all four groups | **holds** | local/K8: 0.959 vs 0.803; local/K40: 0.909 vs 0.765; anywhere/K8: 0.961 vs 0.810; anywhere/K40: 0.907 vs 0.766 |
| P5 | entropy@min takes fewer minutes than habit_B@min in all four groups | **holds** | local/K8: 38.9 vs 53.9; local/K40: 38.2 vs 101.7; anywhere/K8: 38.1 vs 52.4; anywhere/K40: 38.2 vs 102.2 |

Wall clock 98 s. Cells are classified from point estimates and a paired bootstrap; some cells are misclassified by chance and no p-value is claimed. Limitations are in Addendum 23.