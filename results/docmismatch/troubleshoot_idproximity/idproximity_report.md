# Do identifiers carry location, and what would an id-neighbour list buy? (Addendum 24)

25 real Mortar buildings (Brick metadata only, cached; no download). Part A describes the identifiers of the layouts; Part B compares three candidate lists for the tool: MIN (the documented box, then the first K - 1 boxes of the equipment list), IDNEAR (the documented box, then the K - 1 boxes nearest to it in natural id order; still only the equipment list and the claims) and GROUPED (same air handler first; needs the box -> air handler claims too). The true cause is drawn over ALL boxes of the building; a wrong feeder that is not on a list counts as 'unlisted' for that policy (OFF-LIST). Worlds: LOCAL and ANYWHERE are Addendum 23's; the two ADJACENCY worlds are ASSUMED (a wrong feeder is likely a neighbour in id order) and favour IDNEAR BY CONSTRUCTION: they bound what id neighbours could buy if errors were that local, they do not show that errors are. 200 cells x 300 paired episodes x 3 policies. Minutes are placeholders. Nothing here is evidence about real technicians or real documentation errors.

## Gates

| gate | result | detail |
|---|---|---|
| G1 code path (id-near lists; min and grouped reproduce Addendum 23) | PASS | id-near lists of 25 rooms x 2 caps checked; 20 episodes x 4 runners identical; 100 cells reproduce Addendum 23 exactly |
| G2 accounting | PASS | 20 episodes x 5 policies |
| G3 coverage bookkeeping (and exact = simulated) | PASS | 200 cells recomputed; largest difference 0.0046 (tolerance 0.01) |
| G4 reproducibility | PASS | cell 0: first 50 episodes reproduced |
| G5 completeness and pairing | PASS | ok |
| G6 layout fidelity | PASS | 25 buildings |

## Part A: what the identifiers carry

**Name consistency**: 2025 of 2124 documented (box, zone) claims (95%) have the zone id inside the box id. If this is near 100%, the claims in these buildings are name-derived: the documented box and its room share a name by construction, so the claims say nothing about whether the drawings are right.

**Handler lift** (buildings with at least 2 documented handlers; K = 8): the share of a box's 7 id-nearest boxes that hang on its own air handler (id), the same for the first 7 boxes of the equipment order (first), the share a random list would give (random), and lift = id / random. Buildings with at most 8 boxes with a handler have full lists and lift 1 by construction.

| building | rooms | boxes | handlers | claims consistent | id | first | random | lift |
|---|---|---|---|---|---|---|---|---|
| bldg2 | 25 | 25 | 2 | 25/25 | 75% | 63% | 72% | 1.05 |
| bldg4 | 28 | 28 | 1 | 28/28 | - | - | - | - |
| bldg5 | 124 | 124 | 10 | 124/124 | 75% | 8% | 11% | 7.00 |
| bldg6 | 132 | 132 | 11 | 132/132 | 78% | 10% | 15% | 5.21 |
| bldg8 | 24 | 24 | 1 | 24/24 | - | - | - | - |
| bldg9 | 126 | 126 | 2 | 126/126 | 91% | 56% | 50% | 1.81 |
| bldg10 | 16 | 16 | 3 | 16/16 | 49% | 29% | 30% | 1.64 |
| bldg11 | 394 | 394 | 9 | 394/394 | 55% | 10% | 14% | 3.96 |
| bldg12 | 98 | 98 | 5 | 98/98 | 80% | 13% | 23% | 3.50 |
| bldg13 | 24 | 24 | 1 | 24/24 | - | - | - | - |
| bldg15 | 129 | 129 | 2 | 129/129 | 96% | 47% | 55% | 1.73 |
| bldg18 | 144 | 144 | 5 | 144/144 | 79% | 19% | 33% | 2.42 |
| bldg20 | 13 | 13 | 2 | 13/13 | 63% | 63% | 54% | 1.16 |
| bldg27 | 17 | 17 | 1 | 17/17 | - | - | - | - |
| bldg28 | 45 | 45 | 1 | 45/45 | - | - | - | - |
| bldg30 | 99 | 99 | 2 | 0/99 | 98% | 49% | 49% | 1.97 |
| bldg32 | 107 | 107 | 7 | 107/107 | 87% | 8% | 15% | 5.62 |
| bldg34 | 39 | 39 | 4 | 39/39 | 57% | 32% | 32% | 1.76 |
| bldg36 | 43 | 43 | 1 | 43/43 | - | - | - | - |
| bldg37 | 283 | 283 | 7 | 283/283 | 62% | 7% | 20% | 3.17 |
| bldg39 | 18 | 18 | 2 | 18/18 | 76% | 33% | 53% | 1.44 |
| bldg40 | 87 | 87 | 2 | 87/87 | 81% | 53% | 59% | 1.39 |
| bldg42 | 13 | 13 | 1 | 13/13 | - | - | - | - |
| bldg43 | 52 | 52 | 1 | 52/52 | - | - | - | - |
| bldg44 | 44 | 44 | 2 | 44/44 | 95% | 73% | 59% | 1.60 |

Over the 17 buildings with at least 2 handlers and more than 8 boxes with a handler: id beats first in 94% of them; mean id 76%, mean first 34%, mean random 38%, mean lift 2.73.

## Part B: coverage of wrong feeders by each list (exact; mean over the buildings)

Coverage = the share of the wrong-feeder weight (over all other boxes, in the world's weights) that lies on the list. Expected off-list share of visits = 0.135 x (1 - coverage).

| world | cap | coverage min / idnear / grouped | expected off-list share min / idnear / grouped | simulated off-list share min / idnear / grouped |
|---|---|---|---|---|
| errors local (same air handler) | K8 | 20% / 24% / 27% | 0.108 / 0.102 / 0.099 | 0.110 / 0.107 / 0.101 |
| errors local (same air handler) | K40 | 67% / 72% / 76% | 0.045 / 0.037 / 0.032 | 0.045 / 0.035 / 0.031 |
| errors anywhere | K8 | 20% / 20% / 20% | 0.108 / 0.108 / 0.108 | 0.103 / 0.105 / 0.103 |
| errors anywhere | K40 | 67% / 67% / 67% | 0.044 / 0.044 / 0.044 | 0.046 / 0.049 / 0.048 |
| ASSUMED adjacent-room errors (lambda 2) | K8 | 21% / 86% / 30% | 0.107 / 0.019 / 0.094 | 0.107 / 0.020 / 0.095 |
| ASSUMED adjacent-room errors (lambda 2) | K40 | 67% / 100% / 84% | 0.044 / 0.000 / 0.021 | 0.043 / 0.000 / 0.021 |
| ASSUMED nearby-room errors (lambda 8) | K8 | 20% / 47% / 25% | 0.109 / 0.071 / 0.101 | 0.108 / 0.067 / 0.099 |
| ASSUMED nearby-room errors (lambda 8) | K40 | 68% / 97% / 79% | 0.044 / 0.004 / 0.028 | 0.043 / 0.004 / 0.028 |

## The tool with each list: minutes / accuracy / actionable / wrong-and-confident / unresolved / off-list share (means over buildings)

| world | cap | min | idnear | grouped |
|---|---|---|---|---|
| errors local (same air handler) | K8 | 39 / 96% / 86% / 2% / 13% / 11% | 39 / 96% / 87% / 2% / 12% / 11% | 39 / 96% / 87% / 2% / 12% / 10% |
| errors local (same air handler) | K40 | 38 / 91% / 86% / 2% / 13% / 5% | 38 / 90% / 86% / 2% / 13% / 4% | 38 / 91% / 87% / 2% / 13% / 3% |
| errors anywhere | K8 | 38 / 96% / 87% / 2% / 12% / 10% | 38 / 96% / 86% / 2% / 12% / 10% | 38 / 96% / 87% / 2% / 12% / 10% |
| errors anywhere | K40 | 38 / 91% / 86% / 2% / 13% / 5% | 38 / 91% / 86% / 2% / 13% / 5% | 38 / 91% / 86% / 2% / 13% / 5% |
| ASSUMED adjacent-room errors (lambda 2) | K8 | 38 / 96% / 87% / 2% / 12% / 11% | 34 / 96% / 94% / 2% / 5% / 2% | 37 / 96% / 88% / 2% / 11% / 9% |
| ASSUMED adjacent-room errors (lambda 2) | K40 | 37 / 91% / 87% / 2% / 12% / 4% | 37 / 88% / 87% / 2% / 12% / 0% | 37 / 90% / 88% / 2% / 11% / 2% |
| ASSUMED nearby-room errors (lambda 8) | K8 | 38 / 96% / 86% / 2% / 12% / 11% | 37 / 96% / 90% / 2% / 9% / 7% | 38 / 96% / 87% / 2% / 12% / 10% |
| ASSUMED nearby-room errors (lambda 8) | K40 | 37 / 91% / 87% / 2% / 12% / 4% | 37 / 89% / 87% / 2% / 12% / 0% | 37 / 91% / 88% / 2% / 11% / 3% |

## What each list is worth against MIN (same episodes; Addendum 21's labels; deltas are treatment minus min, means over buildings)

| world | cap | list | IMPROVES | WORSE | TRADE | NEITHER | d minutes | d accuracy | d actionable | d off-list share |
|---|---|---|---|---|---|---|---|---|---|---|
| errors local (same air handler) | K8 | idnear | 0% | 0% | 0% | 100% | -0.3 | +0.000 | +0.004 | -0.004 |
| errors local (same air handler) | K8 | grouped | 4% | 0% | 0% | 96% | -0.4 | -0.000 | +0.008 | -0.009 |
| errors local (same air handler) | K40 | idnear | 0% | 12% | 0% | 88% | -0.0 | -0.007 | +0.001 | -0.010 |
| errors local (same air handler) | K40 | grouped | 4% | 12% | 0% | 84% | -0.4 | -0.002 | +0.009 | -0.015 |
| errors anywhere | K8 | idnear | 0% | 0% | 0% | 100% | +0.1 | -0.001 | -0.002 | +0.002 |
| errors anywhere | K8 | grouped | 0% | 0% | 0% | 100% | -0.0 | +0.000 | +0.000 | +0.000 |
| errors anywhere | K40 | idnear | 0% | 0% | 0% | 100% | +0.0 | +0.001 | -0.000 | +0.003 |
| errors anywhere | K40 | grouped | 4% | 4% | 0% | 92% | -0.1 | +0.000 | -0.001 | +0.002 |
| ASSUMED adjacent-room errors (lambda 2) | K8 | idnear | 100% | 0% | 0% | 0% | -3.5 | +0.001 | +0.069 | -0.087 |
| ASSUMED adjacent-room errors (lambda 2) | K8 | grouped | 0% | 0% | 0% | 100% | -0.5 | +0.001 | +0.011 | -0.012 |
| ASSUMED adjacent-room errors (lambda 2) | K40 | idnear | 0% | 52% | 0% | 48% | +0.0 | -0.033 | -0.001 | -0.043 |
| ASSUMED adjacent-room errors (lambda 2) | K40 | grouped | 4% | 28% | 0% | 68% | -0.4 | -0.006 | +0.010 | -0.023 |
| ASSUMED nearby-room errors (lambda 8) | K8 | idnear | 36% | 0% | 0% | 64% | -1.7 | +0.000 | +0.033 | -0.041 |
| ASSUMED nearby-room errors (lambda 8) | K8 | grouped | 4% | 0% | 0% | 96% | -0.3 | +0.001 | +0.007 | -0.009 |
| ASSUMED nearby-room errors (lambda 8) | K40 | idnear | 0% | 48% | 0% | 52% | +0.0 | -0.028 | +0.001 | -0.039 |
| ASSUMED nearby-room errors (lambda 8) | K40 | grouped | 4% | 8% | 0% | 88% | -0.2 | -0.004 | +0.007 | -0.015 |

## Per building, errors local (same air handler), K8: exact coverage of the wrong feeder

| building | boxes | handlers | min | idnear | grouped |
|---|---|---|---|---|---|
| bldg20 | 13 | 2 | 62% | 63% | 77% |
| bldg42 | 13 | 1 | 58% | 58% | 58% |
| bldg10 | 16 | 3 | 47% | 61% | 72% |
| bldg27 | 17 | 1 | 44% | 44% | 44% |
| bldg39 | 18 | 2 | 36% | 54% | 60% |
| bldg8 | 24 | 1 | 30% | 30% | 30% |
| bldg13 | 24 | 1 | 30% | 30% | 30% |
| bldg2 | 25 | 2 | 28% | 30% | 36% |
| bldg4 | 28 | 1 | 26% | 26% | 26% |
| bldg34 | 39 | 4 | 19% | 25% | 34% |
| bldg36 | 43 | 1 | 17% | 17% | 17% |
| bldg44 | 44 | 2 | 17% | 24% | 25% |
| bldg28 | 45 | 1 | 16% | 16% | 16% |
| bldg43 | 52 | 1 | 14% | 14% | 14% |
| bldg40 | 87 | 2 | 8% | 11% | 13% |
| bldg12 | 98 | 5 | 6% | 15% | 18% |
| bldg30 | 99 | 2 | 7% | 11% | 11% |
| bldg32 | 107 | 7 | 6% | 16% | 18% |
| bldg5 | 124 | 10 | 5% | 14% | 17% |
| bldg9 | 126 | 2 | 6% | 8% | 9% |
| bldg15 | 129 | 2 | 5% | 8% | 9% |
| bldg6 | 132 | 11 | 5% | 12% | 14% |
| bldg18 | 144 | 5 | 4% | 9% | 10% |
| bldg37 | 283 | 7 | 2% | 5% | 6% |
| bldg11 | 394 | 9 | 2% | 3% | 5% |

## Predictions written before the run

| | prediction | holds? | values |
|---|---|---|---|
| P1 | at least 90% of documented claims have the zone id inside the box id | **holds** | 0.953 |
| P2 | id-nearest boxes share the air handler more often than the first-K list in at least 70% of the buildings, mean lift at least 1.5 | **holds** | id beats first in 0.94 of 17 buildings; mean lift 2.73 |
| P3 | local world: coverage idnear > min at both caps and grouped >= idnear | **holds** | K8: 0.200 / 0.242 / 0.268; K40: 0.667 / 0.723 / 0.762 |
| P4 | local world: expected off-list shares of min and grouped differ by at most 0.015 at each cap | **holds** | K8: 0.108 vs 0.099; K40: 0.045 vs 0.032 |
| P5 | adjacent-room world (lambda 2), K8: expected off-list share of idnear at most 0.4 x that of min (by construction) | **holds** | 0.019 vs 0.107 |
| P6 | local, lambda 2 and lambda 8 worlds, both caps: actionable rate of idnear above min | **does not hold** | local/K8: 0.866 vs 0.863; local/K40: 0.862 vs 0.862; idlocal2/K8: 0.936 vs 0.867; idlocal2/K40: 0.868 vs 0.869; idlocal8/K8: 0.897 vs 0.864; idlocal8/K40: 0.873 vs 0.871 |

Wall clock 232 s. Cells are classified from point estimates and a paired bootstrap; some cells are misclassified by chance and no p-value is claimed. Limitations are in Addendum 24.