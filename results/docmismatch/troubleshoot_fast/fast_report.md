# The id-weighted tool against the fast and the slow stand-in technician (Addendum 26)

25 real Mortar buildings (Brick metadata only, cached; no download); 250 cells = 5 worlds x 2 caps x 25 buildings, 300 paired episodes x 6 policies. **HABIT_A ('the fast technician') and HABIT_B ('the slow, careful technician') are stand-ins I wrote, not real technicians**: they use no symptoms and no knowledge of the building beyond the ORDER of the candidate list, and stop at the first yes. To be fair they get the same candidates as the tool: on the id-near list ('idnear') they check the nearest boxes first; on the arbitrary list ('min') the first boxes of the equipment list. The tool with the id-weighted list is 'idw4' (weight decay 4, a placeholder). The tool stops after 12 checks and the habits run to exhaustion, which flatters the tool on minutes in visits that no list resolves. The three ASSUMED worlds put wrong feeders near the documented box in id order and favour id-ordered lists BY CONSTRUCTION, for the habits as much as for the tool. Minutes and hit rates are placeholders. Nothing here is evidence about real technicians.

## Gates

| gate | result | detail |
|---|---|---|
| G1 code path (tool reproduces Addendum 25, habits reproduce Addendum 23, habits ignore weights) | PASS | 250 cells reproduce Addendum 25 exactly; 100 cells reproduce Addendum 23 exactly; 20 episodes x 2 habits identical; 30 episodes x 4 runners identical |
| G2 accounting | PASS | 20 episodes x 5 policies |
| G3 coverage bookkeeping | PASS | 250 cells recomputed |
| G4 reproducibility | PASS | cell 0: first 50 episodes reproduced |
| G5 completeness and pairing | PASS | ok |
| G6 layout fidelity | PASS | 25 buildings |

## Means over buildings: minutes / accuracy / actionable / wrong-and-confident / unresolved / mean checks

ACTIONABLE = right and names a cause (not 'unlisted'); accuracy counts a correct 'unlisted' as right.

| world | cap | entropy@min | entropy@idw4 | habit_A@min | habit_A@idnear | habit_B@min | habit_B@idnear |
|---|---|---|---|---|---|---|---|
| errors local (same air handler) | K8 | 39 / 96% / 86% / 2% / 13% / 3.7 | 40 / 96% / 87% / 2% / 12% / 3.7 | 24 / 80% / 75% / 20% / 0% / 2.8 | 24 / 80% / 76% / 20% / 0% / 2.8 | 54 / 91% / 81% / 9% / 0% / 2.9 | 53 / 91% / 81% / 9% / 0% / 2.9 |
| errors local (same air handler) | K40 | 38 / 91% / 86% / 2% / 13% / 3.8 | 38 / 91% / 87% / 2% / 13% / 3.7 | 32 / 76% / 76% / 24% / 0% / 3.5 | 32 / 77% / 77% / 23% / 0% / 3.5 | 102 / 89% / 86% / 11% / 0% / 4.8 | 97 / 89% / 86% / 11% / 0% / 4.6 |
| errors anywhere | K8 | 38 / 96% / 87% / 2% / 12% / 3.7 | 39 / 96% / 86% / 2% / 12% / 3.7 | 24 / 81% / 76% / 19% / 0% / 2.8 | 24 / 81% / 76% / 19% / 0% / 2.8 | 52 / 92% / 82% / 8% / 0% / 2.8 | 53 / 92% / 82% / 8% / 0% / 2.8 |
| errors anywhere | K40 | 38 / 91% / 86% / 2% / 13% / 3.8 | 38 / 91% / 86% / 2% / 13% / 3.7 | 32 / 77% / 76% / 23% / 0% / 3.5 | 32 / 77% / 76% / 23% / 0% / 3.5 | 102 / 89% / 86% / 11% / 0% / 4.8 | 104 / 89% / 86% / 11% / 0% / 4.9 |
| ASSUMED adjacent-room errors (lambda 2) | K8 | 38 / 96% / 87% / 2% / 12% / 3.6 | 34 / 97% / 94% / 2% / 5% / 3.3 | 24 / 81% / 76% / 19% / 0% / 2.8 | 22 / 83% / 82% / 17% / 0% / 2.6 | 52 / 93% / 82% / 7% / 0% / 2.8 | 44 / 93% / 90% / 7% / 0% / 2.5 |
| ASSUMED adjacent-room errors (lambda 2) | K40 | 37 / 91% / 87% / 2% / 12% / 3.7 | 33 / 95% / 94% / 2% / 5% / 3.4 | 31 / 78% / 78% / 22% / 0% / 3.4 | 26 / 83% / 83% / 17% / 0% / 3.0 | 101 / 89% / 86% / 11% / 0% / 4.8 | 58 / 93% / 92% / 7% / 0% / 3.0 |
| ASSUMED nearby-room errors (lambda 8) | K8 | 38 / 96% / 86% / 2% / 12% / 3.7 | 37 / 97% / 90% / 2% / 9% / 3.6 | 24 / 81% / 76% / 19% / 0% / 2.8 | 23 / 82% / 78% / 18% / 0% / 2.7 | 53 / 92% / 81% / 8% / 0% / 2.8 | 49 / 92% / 85% / 8% / 0% / 2.7 |
| ASSUMED nearby-room errors (lambda 8) | K40 | 37 / 91% / 87% / 2% / 12% / 3.7 | 35 / 92% / 90% / 2% / 9% / 3.5 | 31 / 77% / 77% / 23% / 0% / 3.5 | 29 / 79% / 79% / 21% / 0% / 3.3 | 102 / 88% / 86% / 12% / 0% / 4.8 | 76 / 90% / 90% / 10% / 0% / 3.8 |
| ASSUMED nearby-room errors (lambda 4) | K8 | 39 / 96% / 86% / 2% / 12% / 3.7 | 36 / 97% / 92% / 2% / 7% / 3.5 | 24 / 80% / 76% / 20% / 0% / 2.8 | 23 / 82% / 80% / 18% / 0% / 2.7 | 53 / 91% / 81% / 9% / 0% / 2.9 | 48 / 92% / 87% / 8% / 0% / 2.7 |
| ASSUMED nearby-room errors (lambda 4) | K40 | 38 / 91% / 87% / 2% / 13% / 3.8 | 35 / 93% / 92% / 2% / 8% / 3.5 | 32 / 77% / 77% / 23% / 0% / 3.5 | 28 / 81% / 80% / 19% / 0% / 3.2 | 100 / 89% / 86% / 11% / 0% / 4.7 | 67 / 91% / 91% / 9% / 0% / 3.4 |

## The tool against each habit (share of buildings; Addendum 19's classification and Addendum 20's BUYS ACCURACY label)

WINS = the tool is at least 10% faster at no less than 0.02 lower accuracy; LOSES = at least 10% slower with no accuracy gain of 0.02; BUYS ACCURACY = at least 10% slower but at least 0.05 more accurate with the paired interval above 0. r = the tool's minutes relative to the habit's (mean over buildings; negative = the tool is faster).

| world | cap | comparison | WINS | LOSES | BUYS ACCURACY | NEITHER | r minutes | d accuracy |
|---|---|---|---|---|---|---|---|---|
| errors local (same air handler) | K8 | entropy@idw4 vs habit_A@idnear | 0% | 0% | 100% | 0% | +65% | +0.156 |
| errors local (same air handler) | K8 | entropy@idw4 vs habit_B@idnear | 100% | 0% | 0% | 0% | -26% | +0.046 |
| errors local (same air handler) | K8 | entropy@min vs habit_A@min | 0% | 0% | 100% | 0% | +61% | +0.156 |
| errors local (same air handler) | K8 | entropy@min vs habit_B@min | 100% | 0% | 0% | 0% | -28% | +0.045 |
| errors local (same air handler) | K8 | entropy@idw4 vs habit_A@min | 0% | 0% | 100% | 0% | +64% | +0.157 |
| errors local (same air handler) | K8 | entropy@idw4 vs habit_B@min | 100% | 0% | 0% | 0% | -27% | +0.046 |
| errors local (same air handler) | K40 | entropy@idw4 vs habit_A@idnear | 0% | 0% | 76% | 24% | +20% | +0.138 |
| errors local (same air handler) | K40 | entropy@idw4 vs habit_B@idnear | 84% | 0% | 0% | 16% | -58% | +0.017 |
| errors local (same air handler) | K40 | entropy@min vs habit_A@min | 0% | 0% | 88% | 12% | +22% | +0.144 |
| errors local (same air handler) | K40 | entropy@min vs habit_B@min | 84% | 0% | 0% | 16% | -59% | +0.022 |
| errors local (same air handler) | K40 | entropy@idw4 vs habit_A@min | 0% | 0% | 76% | 24% | +20% | +0.142 |
| errors local (same air handler) | K40 | entropy@idw4 vs habit_B@min | 84% | 0% | 0% | 16% | -60% | +0.020 |
| errors anywhere | K8 | entropy@idw4 vs habit_A@idnear | 0% | 0% | 100% | 0% | +63% | +0.152 |
| errors anywhere | K8 | entropy@idw4 vs habit_B@idnear | 100% | 0% | 0% | 0% | -26% | +0.039 |
| errors anywhere | K8 | entropy@min vs habit_A@min | 0% | 0% | 100% | 0% | +59% | +0.151 |
| errors anywhere | K8 | entropy@min vs habit_B@min | 100% | 0% | 0% | 0% | -27% | +0.037 |
| errors anywhere | K8 | entropy@idw4 vs habit_A@min | 0% | 0% | 100% | 0% | +63% | +0.152 |
| errors anywhere | K8 | entropy@idw4 vs habit_B@min | 100% | 0% | 0% | 0% | -25% | +0.038 |
| errors anywhere | K40 | entropy@idw4 vs habit_A@idnear | 0% | 0% | 68% | 32% | +19% | +0.143 |
| errors anywhere | K40 | entropy@idw4 vs habit_B@idnear | 80% | 0% | 0% | 20% | -60% | +0.017 |
| errors anywhere | K40 | entropy@min vs habit_A@min | 0% | 0% | 72% | 28% | +21% | +0.141 |
| errors anywhere | K40 | entropy@min vs habit_B@min | 76% | 0% | 0% | 24% | -58% | +0.017 |
| errors anywhere | K40 | entropy@idw4 vs habit_A@min | 0% | 0% | 64% | 36% | +20% | +0.143 |
| errors anywhere | K40 | entropy@idw4 vs habit_B@min | 84% | 0% | 0% | 16% | -59% | +0.019 |
| ASSUMED adjacent-room errors (lambda 2) | K8 | entropy@idw4 vs habit_A@idnear | 0% | 0% | 100% | 0% | +52% | +0.136 |
| ASSUMED adjacent-room errors (lambda 2) | K8 | entropy@idw4 vs habit_B@idnear | 100% | 0% | 0% | 0% | -23% | +0.033 |
| ASSUMED adjacent-room errors (lambda 2) | K8 | entropy@min vs habit_A@min | 0% | 0% | 100% | 0% | +56% | +0.152 |
| ASSUMED adjacent-room errors (lambda 2) | K8 | entropy@min vs habit_B@min | 100% | 0% | 0% | 0% | -27% | +0.034 |
| ASSUMED adjacent-room errors (lambda 2) | K8 | entropy@idw4 vs habit_A@min | 0% | 0% | 100% | 0% | +39% | +0.157 |
| ASSUMED adjacent-room errors (lambda 2) | K8 | entropy@idw4 vs habit_B@min | 100% | 0% | 0% | 0% | -35% | +0.039 |
| ASSUMED adjacent-room errors (lambda 2) | K40 | entropy@idw4 vs habit_A@idnear | 0% | 0% | 96% | 4% | +30% | +0.119 |
| ASSUMED adjacent-room errors (lambda 2) | K40 | entropy@idw4 vs habit_B@idnear | 100% | 0% | 0% | 0% | -41% | +0.021 |
| ASSUMED adjacent-room errors (lambda 2) | K40 | entropy@min vs habit_A@min | 0% | 0% | 80% | 20% | +22% | +0.132 |
| ASSUMED adjacent-room errors (lambda 2) | K40 | entropy@min vs habit_B@min | 84% | 0% | 0% | 16% | -60% | +0.020 |
| ASSUMED adjacent-room errors (lambda 2) | K40 | entropy@idw4 vs habit_A@min | 0% | 0% | 36% | 64% | +9% | +0.169 |
| ASSUMED adjacent-room errors (lambda 2) | K40 | entropy@idw4 vs habit_B@min | 100% | 0% | 0% | 0% | -64% | +0.057 |
| ASSUMED nearby-room errors (lambda 8) | K8 | entropy@idw4 vs habit_A@idnear | 0% | 0% | 100% | 0% | +60% | +0.150 |
| ASSUMED nearby-room errors (lambda 8) | K8 | entropy@idw4 vs habit_B@idnear | 100% | 0% | 0% | 0% | -25% | +0.047 |
| ASSUMED nearby-room errors (lambda 8) | K8 | entropy@min vs habit_A@min | 0% | 0% | 100% | 0% | +60% | +0.155 |
| ASSUMED nearby-room errors (lambda 8) | K8 | entropy@min vs habit_B@min | 100% | 0% | 0% | 0% | -27% | +0.047 |
| ASSUMED nearby-room errors (lambda 8) | K8 | entropy@idw4 vs habit_A@min | 0% | 0% | 100% | 0% | +55% | +0.157 |
| ASSUMED nearby-room errors (lambda 8) | K8 | entropy@idw4 vs habit_B@min | 100% | 0% | 0% | 0% | -29% | +0.049 |
| ASSUMED nearby-room errors (lambda 8) | K40 | entropy@idw4 vs habit_A@idnear | 0% | 0% | 88% | 12% | +22% | +0.124 |
| ASSUMED nearby-room errors (lambda 8) | K40 | entropy@idw4 vs habit_B@idnear | 96% | 0% | 0% | 4% | -52% | +0.011 |
| ASSUMED nearby-room errors (lambda 8) | K40 | entropy@min vs habit_A@min | 0% | 0% | 80% | 20% | +19% | +0.148 |
| ASSUMED nearby-room errors (lambda 8) | K40 | entropy@min vs habit_B@min | 92% | 0% | 0% | 8% | -60% | +0.030 |
| ASSUMED nearby-room errors (lambda 8) | K40 | entropy@idw4 vs habit_A@min | 0% | 0% | 64% | 36% | +14% | +0.149 |
| ASSUMED nearby-room errors (lambda 8) | K40 | entropy@idw4 vs habit_B@min | 100% | 0% | 0% | 0% | -62% | +0.031 |
| ASSUMED nearby-room errors (lambda 4) | K8 | entropy@idw4 vs habit_A@idnear | 0% | 0% | 100% | 0% | +59% | +0.146 |
| ASSUMED nearby-room errors (lambda 4) | K8 | entropy@idw4 vs habit_B@idnear | 100% | 0% | 0% | 0% | -24% | +0.047 |
| ASSUMED nearby-room errors (lambda 4) | K8 | entropy@min vs habit_A@min | 0% | 0% | 100% | 0% | +60% | +0.158 |
| ASSUMED nearby-room errors (lambda 4) | K8 | entropy@min vs habit_B@min | 100% | 0% | 0% | 0% | -27% | +0.049 |
| ASSUMED nearby-room errors (lambda 4) | K8 | entropy@idw4 vs habit_A@min | 0% | 0% | 100% | 0% | +51% | +0.160 |
| ASSUMED nearby-room errors (lambda 4) | K8 | entropy@idw4 vs habit_B@min | 100% | 0% | 0% | 0% | -32% | +0.051 |
| ASSUMED nearby-room errors (lambda 4) | K40 | entropy@idw4 vs habit_A@idnear | 0% | 0% | 92% | 8% | +26% | +0.124 |
| ASSUMED nearby-room errors (lambda 4) | K40 | entropy@idw4 vs habit_B@idnear | 92% | 0% | 0% | 8% | -46% | +0.016 |
| ASSUMED nearby-room errors (lambda 4) | K40 | entropy@min vs habit_A@min | 0% | 0% | 88% | 12% | +21% | +0.139 |
| ASSUMED nearby-room errors (lambda 4) | K40 | entropy@min vs habit_B@min | 72% | 0% | 0% | 28% | -58% | +0.023 |
| ASSUMED nearby-room errors (lambda 4) | K40 | entropy@idw4 vs habit_A@min | 0% | 0% | 44% | 56% | +12% | +0.161 |
| ASSUMED nearby-room errors (lambda 4) | K40 | entropy@idw4 vs habit_B@min | 100% | 0% | 0% | 0% | -61% | +0.044 |

## Against BOTH habits (Addendum 19's `combine`: WINS only if it wins against each, LOSES if it loses against either), share of buildings

| world | cap | same information | arbitrary list | tool with ids, technician without |
|---|---|---|---|---|
| errors local (same air handler) | K8 | 0% wins / 0% loses / 100% neither | 0% wins / 0% loses / 100% neither | 0% wins / 0% loses / 100% neither |
| errors local (same air handler) | K40 | 0% wins / 0% loses / 100% neither | 0% wins / 0% loses / 100% neither | 0% wins / 0% loses / 100% neither |
| errors anywhere | K8 | 0% wins / 0% loses / 100% neither | 0% wins / 0% loses / 100% neither | 0% wins / 0% loses / 100% neither |
| errors anywhere | K40 | 0% wins / 0% loses / 100% neither | 0% wins / 0% loses / 100% neither | 0% wins / 0% loses / 100% neither |
| ASSUMED adjacent-room errors (lambda 2) | K8 | 0% wins / 0% loses / 100% neither | 0% wins / 0% loses / 100% neither | 0% wins / 0% loses / 100% neither |
| ASSUMED adjacent-room errors (lambda 2) | K40 | 0% wins / 0% loses / 100% neither | 0% wins / 0% loses / 100% neither | 0% wins / 0% loses / 100% neither |
| ASSUMED nearby-room errors (lambda 8) | K8 | 0% wins / 0% loses / 100% neither | 0% wins / 0% loses / 100% neither | 0% wins / 0% loses / 100% neither |
| ASSUMED nearby-room errors (lambda 8) | K40 | 0% wins / 0% loses / 100% neither | 0% wins / 0% loses / 100% neither | 0% wins / 0% loses / 100% neither |
| ASSUMED nearby-room errors (lambda 4) | K8 | 0% wins / 0% loses / 100% neither | 0% wins / 0% loses / 100% neither | 0% wins / 0% loses / 100% neither |
| ASSUMED nearby-room errors (lambda 4) | K40 | 0% wins / 0% loses / 100% neither | 0% wins / 0% loses / 100% neither | 0% wins / 0% loses / 100% neither |

## What the habits gain from the id-near list (habit on idnear minus habit on min; means over buildings)

| world | cap | habit | d minutes | d accuracy | d actionable |
|---|---|---|---|---|---|
| errors local (same air handler) | K8 | habit_A | -0.1 | +0.001 | +0.002 |
| errors local (same air handler) | K8 | habit_B | -0.5 | -0.000 | +0.005 |
| errors local (same air handler) | K40 | habit_A | -0.0 | +0.004 | +0.004 |
| errors local (same air handler) | K40 | habit_B | -4.4 | +0.003 | +0.008 |
| errors anywhere | K8 | habit_A | -0.0 | -0.000 | -0.001 |
| errors anywhere | K8 | habit_B | +0.1 | -0.000 | -0.001 |
| errors anywhere | K40 | habit_A | +0.1 | +0.000 | +0.000 |
| errors anywhere | K40 | habit_B | +1.9 | +0.002 | -0.000 |
| ASSUMED adjacent-room errors (lambda 2) | K8 | habit_A | -2.1 | +0.021 | +0.058 |
| ASSUMED adjacent-room errors (lambda 2) | K8 | habit_B | -8.2 | +0.006 | +0.079 |
| ASSUMED adjacent-room errors (lambda 2) | K40 | habit_A | -5.1 | +0.050 | +0.051 |
| ASSUMED adjacent-room errors (lambda 2) | K40 | habit_B | -43.5 | +0.035 | +0.056 |
| ASSUMED nearby-room errors (lambda 8) | K8 | habit_A | -0.7 | +0.007 | +0.023 |
| ASSUMED nearby-room errors (lambda 8) | K8 | habit_B | -3.2 | +0.002 | +0.037 |
| ASSUMED nearby-room errors (lambda 8) | K40 | habit_A | -2.2 | +0.025 | +0.025 |
| ASSUMED nearby-room errors (lambda 8) | K40 | habit_B | -25.3 | +0.020 | +0.037 |
| ASSUMED nearby-room errors (lambda 4) | K8 | habit_A | -1.3 | +0.014 | +0.038 |
| ASSUMED nearby-room errors (lambda 4) | K8 | habit_B | -5.1 | +0.004 | +0.056 |
| ASSUMED nearby-room errors (lambda 4) | K40 | habit_A | -3.6 | +0.037 | +0.037 |
| ASSUMED nearby-room errors (lambda 4) | K40 | habit_B | -33.4 | +0.029 | +0.045 |

## Predictions written before the run

| | prediction | holds? | values |
|---|---|---|---|
| P1 | the fast stand-in (habit_A on the id-near list) is faster than the tool (idw4) in all 10 groups | **holds** | smallest margin +5.592 at anywhere/K40 (32.063 vs 37.654) |
| P2 | the tool is more accurate than habit_A@idnear in all 10 groups | **holds** | smallest margin +0.119 at idlocal2/K40 (0.947 vs 0.828) |
| P3 | the tool's wrong-and-confident rate is at least 0.05 below habit_A@idnear's in all 10 groups | **holds** | smallest margin +0.147 at idlocal2/K8 (0.022 vs 0.169) |
| P4 | the tool is faster than the slow stand-in (habit_B@idnear) in all 10 groups | **holds** | smallest margin +10.177 at idlocal2/K8 (33.518 vs 43.695) |
| P5 | in the lambda 2 world at both caps habit_A@idnear's actionable rate is at least 0.03 above habit_A@min's | **holds** | K8: 0.817 vs 0.759; K40: 0.827 vs 0.776 |

Wall clock 357 s. Cells are classified from point estimates and a paired bootstrap; some cells are misclassified by chance and no p-value is claimed. Limitations are in Addendum 26.