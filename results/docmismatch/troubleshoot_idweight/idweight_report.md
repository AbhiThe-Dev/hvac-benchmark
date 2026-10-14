# Weighting candidates by id distance (Addendum 25)

25 real Mortar buildings (Brick metadata only, cached; no download); 250 cells = 5 worlds x 2 caps x 25 buildings, 300 paired episodes x 6 policies. The tool's new option `nearness = 'id'` lists the documented box and the K - 1 boxes nearest to it in natural id order and weights each candidate exp(-distance / decay); IDNEAR is the same list with equal weights (so IDNEAR vs IDW isolates the weighting); MIN is the arbitrary first-K list; GROUPED needs the air-handler claims too. The true cause is drawn over ALL boxes; a wrong feeder off a policy's list counts as 'unlisted' (OFF-LIST). The three ASSUMED worlds put wrong feeders near the documented box in id order and favour the id levels BY CONSTRUCTION: they bound what id weighting could buy if errors were that local; they do not show that errors are. The tool's decay is a placeholder. Minutes are placeholders. Nothing here is evidence about real technicians or real documentation errors.

## Gates

| gate | result | detail |
|---|---|---|
| G1 code path (id-mode cases; min, idnear and grouped reproduce Addendum 24) | PASS | id-mode cases of 25 rooms x 2 caps x 3 decays checked; 20 episodes x 4 runners identical; 200 cells reproduce Addendum 24 exactly |
| G2 accounting | PASS | 20 episodes x 5 policies |
| G3 coverage bookkeeping and world ordering | PASS | 250 cells recomputed; mean rank distance of a wrong feeder idlocal2 2.5, idlocal4 3.9, idlocal8 6.3, anywhere 29.1 |
| G4 reproducibility | PASS | cell 0: first 50 episodes reproduced |
| G5 completeness and pairing | PASS | ok |
| G6 layout fidelity | PASS | 25 buildings |

## Decision (frozen rule; about keeping the option, never about shipping it): **WORTH KEEPING AS AN OPTION**

Kept if P1 (weighting fixes the long list), P3 (harmless when errors are anywhere) and P6 (safe) all hold; P2, P4 and P5 carry no verdict.

## The tool with each candidate list: minutes / accuracy / actionable / wrong-and-confident / unresolved / mean checks (means over buildings)

ACTIONABLE = right and names a cause (not 'unlisted'); accuracy counts a correct 'unlisted' as right.

| world | cap | min | idnear | idw2 | idw4 | idw8 | grouped |
|---|---|---|---|---|---|---|---|
| errors local (same air handler) | K8 | 39 / 96% / 86% / 2% / 13% / 3.7 | 39 / 96% / 87% / 2% / 12% / 3.7 | 40 / 96% / 87% / 2% / 12% / 3.7 | 40 / 96% / 87% / 2% / 12% / 3.7 | 39 / 96% / 87% / 2% / 12% / 3.7 | 39 / 96% / 87% / 2% / 12% / 3.7 |
| errors local (same air handler) | K40 | 38 / 91% / 86% / 2% / 13% / 3.8 | 38 / 90% / 86% / 2% / 13% / 3.8 | 38 / 91% / 87% / 2% / 13% / 3.7 | 38 / 91% / 87% / 2% / 13% / 3.7 | 38 / 91% / 87% / 2% / 13% / 3.7 | 38 / 91% / 87% / 2% / 13% / 3.7 |
| errors anywhere | K8 | 38 / 96% / 87% / 2% / 12% / 3.7 | 38 / 96% / 86% / 2% / 12% / 3.7 | 39 / 96% / 86% / 2% / 12% / 3.7 | 39 / 96% / 86% / 2% / 12% / 3.7 | 38 / 96% / 86% / 2% / 12% / 3.7 | 38 / 96% / 87% / 2% / 12% / 3.7 |
| errors anywhere | K40 | 38 / 91% / 86% / 2% / 13% / 3.8 | 38 / 91% / 86% / 2% / 13% / 3.8 | 38 / 91% / 86% / 2% / 13% / 3.7 | 38 / 91% / 86% / 2% / 13% / 3.7 | 38 / 91% / 86% / 2% / 13% / 3.7 | 38 / 91% / 86% / 2% / 13% / 3.8 |
| ASSUMED adjacent-room errors (lambda 2) | K8 | 38 / 96% / 87% / 2% / 12% / 3.6 | 34 / 96% / 94% / 2% / 5% / 3.4 | 34 / 97% / 94% / 2% / 5% / 3.3 | 34 / 97% / 94% / 2% / 5% / 3.3 | 33 / 97% / 94% / 2% / 5% / 3.3 | 37 / 96% / 88% / 2% / 11% / 3.6 |
| ASSUMED adjacent-room errors (lambda 2) | K40 | 37 / 91% / 87% / 2% / 12% / 3.7 | 37 / 88% / 87% / 2% / 12% / 3.7 | 34 / 95% / 94% / 2% / 5% / 3.4 | 33 / 95% / 94% / 2% / 5% / 3.4 | 33 / 95% / 94% / 2% / 5% / 3.4 | 37 / 90% / 88% / 2% / 11% / 3.7 |
| ASSUMED nearby-room errors (lambda 8) | K8 | 38 / 96% / 86% / 2% / 12% / 3.7 | 37 / 96% / 90% / 2% / 9% / 3.6 | 37 / 97% / 90% / 2% / 9% / 3.6 | 37 / 97% / 90% / 2% / 9% / 3.6 | 37 / 96% / 90% / 2% / 9% / 3.6 | 38 / 96% / 87% / 2% / 12% / 3.7 |
| ASSUMED nearby-room errors (lambda 8) | K40 | 37 / 91% / 87% / 2% / 12% / 3.7 | 37 / 89% / 87% / 2% / 12% / 3.7 | 36 / 91% / 90% / 2% / 9% / 3.5 | 35 / 92% / 90% / 2% / 9% / 3.5 | 35 / 92% / 90% / 2% / 9% / 3.5 | 37 / 91% / 88% / 2% / 11% / 3.6 |
| ASSUMED nearby-room errors (lambda 4) | K8 | 39 / 96% / 86% / 2% / 12% / 3.7 | 36 / 96% / 92% / 2% / 7% / 3.5 | 36 / 97% / 92% / 2% / 7% / 3.5 | 36 / 97% / 92% / 2% / 7% / 3.5 | 36 / 96% / 92% / 2% / 7% / 3.5 | 38 / 96% / 87% / 2% / 12% / 3.7 |
| ASSUMED nearby-room errors (lambda 4) | K40 | 38 / 91% / 87% / 2% / 13% / 3.8 | 38 / 88% / 87% / 2% / 13% / 3.8 | 36 / 93% / 92% / 2% / 8% / 3.5 | 35 / 93% / 92% / 2% / 8% / 3.5 | 35 / 93% / 92% / 2% / 8% / 3.5 | 38 / 90% / 87% / 2% / 12% / 3.7 |

## Each treatment against its baseline on the same episodes (Addendum 21's labels; deltas are treatment minus baseline, means over buildings)

| world | cap | treatment vs baseline | IMPROVES | WORSE | TRADE | NEITHER | d minutes | d accuracy | d actionable | d off-list share |
|---|---|---|---|---|---|---|---|---|---|---|
| errors local (same air handler) | K8 | idnear vs min | 0% | 0% | 0% | 100% | -0.3 | +0.000 | +0.004 | -0.004 |
| errors local (same air handler) | K8 | grouped vs min | 4% | 0% | 0% | 96% | -0.4 | -0.000 | +0.008 | -0.009 |
| errors local (same air handler) | K8 | idw2 vs idnear | 0% | 0% | 0% | 100% | +0.9 | +0.001 | -0.001 | +0.000 |
| errors local (same air handler) | K8 | idw4 vs idnear | 0% | 0% | 0% | 100% | +0.9 | +0.001 | -0.001 | +0.000 |
| errors local (same air handler) | K8 | idw8 vs idnear | 0% | 0% | 0% | 100% | -0.0 | -0.000 | -0.001 | +0.000 |
| errors local (same air handler) | K8 | idw4 vs min | 0% | 0% | 0% | 100% | +0.6 | +0.001 | +0.003 | -0.004 |
| errors local (same air handler) | K40 | idnear vs min | 0% | 12% | 0% | 88% | -0.0 | -0.007 | +0.001 | -0.010 |
| errors local (same air handler) | K40 | grouped vs min | 4% | 12% | 0% | 84% | -0.4 | -0.002 | +0.009 | -0.015 |
| errors local (same air handler) | K40 | idw2 vs idnear | 4% | 0% | 0% | 96% | -0.1 | +0.005 | +0.004 | +0.000 |
| errors local (same air handler) | K40 | idw4 vs idnear | 4% | 0% | 0% | 96% | -0.6 | +0.005 | +0.005 | +0.000 |
| errors local (same air handler) | K40 | idw8 vs idnear | 4% | 0% | 0% | 96% | -0.6 | +0.005 | +0.005 | +0.000 |
| errors local (same air handler) | K40 | idw4 vs min | 0% | 4% | 0% | 96% | -0.6 | -0.002 | +0.006 | -0.010 |
| errors anywhere | K8 | idnear vs min | 0% | 0% | 0% | 100% | +0.1 | -0.001 | -0.002 | +0.002 |
| errors anywhere | K8 | grouped vs min | 0% | 0% | 0% | 100% | -0.0 | +0.000 | +0.000 | +0.000 |
| errors anywhere | K8 | idw2 vs idnear | 0% | 4% | 0% | 96% | +0.9 | +0.002 | +0.001 | +0.000 |
| errors anywhere | K8 | idw4 vs idnear | 0% | 4% | 0% | 96% | +0.9 | +0.002 | +0.001 | +0.000 |
| errors anywhere | K8 | idw8 vs idnear | 0% | 0% | 0% | 100% | -0.0 | +0.001 | +0.001 | +0.000 |
| errors anywhere | K8 | idw4 vs min | 0% | 4% | 0% | 96% | +1.0 | +0.001 | -0.002 | +0.002 |
| errors anywhere | K40 | idnear vs min | 0% | 0% | 0% | 100% | +0.0 | +0.001 | -0.000 | +0.003 |
| errors anywhere | K40 | grouped vs min | 4% | 4% | 0% | 92% | -0.1 | +0.000 | -0.001 | +0.002 |
| errors anywhere | K40 | idw2 vs idnear | 0% | 0% | 0% | 100% | -0.1 | -0.002 | -0.002 | +0.000 |
| errors anywhere | K40 | idw4 vs idnear | 8% | 0% | 0% | 92% | -0.6 | +0.000 | +0.000 | +0.000 |
| errors anywhere | K40 | idw8 vs idnear | 8% | 0% | 0% | 92% | -0.6 | +0.000 | +0.000 | +0.000 |
| errors anywhere | K40 | idw4 vs min | 8% | 0% | 0% | 92% | -0.5 | +0.001 | -0.000 | +0.003 |
| ASSUMED adjacent-room errors (lambda 2) | K8 | idnear vs min | 100% | 0% | 0% | 0% | -3.5 | +0.001 | +0.069 | -0.087 |
| ASSUMED adjacent-room errors (lambda 2) | K8 | grouped vs min | 0% | 0% | 0% | 100% | -0.5 | +0.001 | +0.011 | -0.012 |
| ASSUMED adjacent-room errors (lambda 2) | K8 | idw2 vs idnear | 4% | 0% | 0% | 96% | -0.6 | +0.004 | +0.003 | +0.000 |
| ASSUMED adjacent-room errors (lambda 2) | K8 | idw4 vs idnear | 4% | 0% | 0% | 96% | -0.6 | +0.004 | +0.003 | +0.000 |
| ASSUMED adjacent-room errors (lambda 2) | K8 | idw8 vs idnear | 16% | 0% | 0% | 84% | -0.9 | +0.002 | +0.002 | +0.000 |
| ASSUMED adjacent-room errors (lambda 2) | K8 | idw4 vs min | 100% | 0% | 0% | 0% | -4.1 | +0.005 | +0.072 | -0.087 |
| ASSUMED adjacent-room errors (lambda 2) | K40 | idnear vs min | 0% | 52% | 0% | 48% | +0.0 | -0.033 | -0.001 | -0.043 |
| ASSUMED adjacent-room errors (lambda 2) | K40 | grouped vs min | 4% | 28% | 0% | 68% | -0.4 | -0.006 | +0.010 | -0.023 |
| ASSUMED adjacent-room errors (lambda 2) | K40 | idw2 vs idnear | 92% | 0% | 0% | 8% | -3.9 | +0.069 | +0.069 | +0.000 |
| ASSUMED adjacent-room errors (lambda 2) | K40 | idw4 vs idnear | 100% | 0% | 0% | 0% | -4.1 | +0.069 | +0.069 | +0.000 |
| ASSUMED adjacent-room errors (lambda 2) | K40 | idw8 vs idnear | 100% | 0% | 0% | 0% | -4.0 | +0.069 | +0.069 | +0.000 |
| ASSUMED adjacent-room errors (lambda 2) | K40 | idw4 vs min | 100% | 0% | 0% | 0% | -4.0 | +0.037 | +0.069 | -0.043 |
| ASSUMED nearby-room errors (lambda 8) | K8 | idnear vs min | 36% | 0% | 0% | 64% | -1.7 | +0.000 | +0.033 | -0.041 |
| ASSUMED nearby-room errors (lambda 8) | K8 | grouped vs min | 4% | 0% | 0% | 96% | -0.3 | +0.001 | +0.007 | -0.009 |
| ASSUMED nearby-room errors (lambda 8) | K8 | idw2 vs idnear | 0% | 0% | 0% | 100% | +0.6 | +0.002 | +0.001 | +0.000 |
| ASSUMED nearby-room errors (lambda 8) | K8 | idw4 vs idnear | 0% | 0% | 0% | 100% | +0.6 | +0.002 | +0.001 | +0.000 |
| ASSUMED nearby-room errors (lambda 8) | K8 | idw8 vs idnear | 0% | 0% | 0% | 100% | -0.1 | +0.000 | +0.000 | +0.000 |
| ASSUMED nearby-room errors (lambda 8) | K8 | idw4 vs min | 16% | 0% | 0% | 84% | -1.1 | +0.002 | +0.034 | -0.041 |
| ASSUMED nearby-room errors (lambda 8) | K40 | idnear vs min | 0% | 48% | 0% | 52% | +0.0 | -0.028 | +0.001 | -0.039 |
| ASSUMED nearby-room errors (lambda 8) | K40 | grouped vs min | 4% | 8% | 0% | 88% | -0.2 | -0.004 | +0.007 | -0.015 |
| ASSUMED nearby-room errors (lambda 8) | K40 | idw2 vs idnear | 68% | 0% | 0% | 32% | -1.5 | +0.029 | +0.029 | +0.000 |
| ASSUMED nearby-room errors (lambda 8) | K40 | idw4 vs idnear | 68% | 0% | 0% | 32% | -1.7 | +0.029 | +0.029 | +0.000 |
| ASSUMED nearby-room errors (lambda 8) | K40 | idw8 vs idnear | 68% | 0% | 0% | 32% | -1.7 | +0.029 | +0.029 | +0.000 |
| ASSUMED nearby-room errors (lambda 8) | K40 | idw4 vs min | 24% | 16% | 4% | 56% | -1.7 | +0.001 | +0.031 | -0.039 |
| ASSUMED nearby-room errors (lambda 4) | K8 | idnear vs min | 64% | 0% | 0% | 36% | -2.5 | +0.002 | +0.052 | -0.062 |
| ASSUMED nearby-room errors (lambda 4) | K8 | grouped vs min | 0% | 0% | 0% | 100% | -0.2 | -0.000 | +0.007 | -0.008 |
| ASSUMED nearby-room errors (lambda 4) | K8 | idw2 vs idnear | 0% | 0% | 0% | 100% | +0.3 | +0.001 | +0.000 | +0.000 |
| ASSUMED nearby-room errors (lambda 4) | K8 | idw4 vs idnear | 0% | 0% | 0% | 100% | +0.2 | +0.001 | +0.000 | +0.000 |
| ASSUMED nearby-room errors (lambda 4) | K8 | idw8 vs idnear | 0% | 0% | 0% | 100% | -0.3 | -0.000 | -0.000 | +0.000 |
| ASSUMED nearby-room errors (lambda 4) | K8 | idw4 vs min | 52% | 0% | 0% | 48% | -2.3 | +0.003 | +0.052 | -0.062 |
| ASSUMED nearby-room errors (lambda 4) | K40 | idnear vs min | 0% | 40% | 0% | 60% | +0.0 | -0.031 | +0.000 | -0.040 |
| ASSUMED nearby-room errors (lambda 4) | K40 | grouped vs min | 4% | 20% | 0% | 76% | -0.3 | -0.007 | +0.007 | -0.018 |
| ASSUMED nearby-room errors (lambda 4) | K40 | idw2 vs idnear | 88% | 0% | 0% | 12% | -2.6 | +0.052 | +0.052 | +0.000 |
| ASSUMED nearby-room errors (lambda 4) | K40 | idw4 vs idnear | 88% | 0% | 0% | 12% | -2.8 | +0.052 | +0.052 | +0.000 |
| ASSUMED nearby-room errors (lambda 4) | K40 | idw8 vs idnear | 88% | 0% | 0% | 12% | -2.8 | +0.052 | +0.052 | +0.000 |
| ASSUMED nearby-room errors (lambda 4) | K40 | idw4 vs min | 88% | 0% | 0% | 12% | -2.8 | +0.022 | +0.053 | -0.040 |

## Predictions written before the run

| | prediction | holds? | values |
|---|---|---|---|
| P1 | at K40 in each adjacency world, idw4's actionable rate is above idnear's | **holds** | idlocal2: 0.937 vs 0.868; idlocal4: 0.919 vs 0.867; idlocal8: 0.902 vs 0.873 |
| P2 | at K40 in lambda 2 and 4, idw4's actionable rate is at least 0.04 above min's | **holds** | idlocal2: 0.937 vs 0.869; idlocal4: 0.919 vs 0.866 |
| P3 | anywhere world, both caps: idw4 within 0.01 of min in actionable and at most 0.01 above in wrong-and-confident | **holds** | K8: actionable 0.865 vs 0.867, wrong-and-confident 0.022 vs 0.022; K40: actionable 0.861 vs 0.862, wrong-and-confident 0.024 vs 0.021 |
| P4 | local world, both caps: idw4's actionable rate is at least idnear's minus 0.005 | **holds** | K8: 0.865 vs 0.866; K40: 0.867 vs 0.862 |
| P5 | at K40 in each adjacency world, idw2 and idw8 also beat idnear in actionable | **holds** | idlocal2: idw2 0.937, idw8 0.937, idnear 0.868; idlocal4: idw2 0.918, idw8 0.919, idnear 0.867; idlocal8: idw2 0.901, idw8 0.902, idnear 0.873 |
| P6 | in all 10 (world, cap) groups idw4's wrong-and-confident rate is at most 0.01 above idnear's | **holds** | largest excess +0.0025 at ('anywhere', 'K40') |

Wall clock 624 s. Cells are classified from point estimates and a paired bootstrap; some cells are misclassified by chance and no p-value is claimed. Limitations are in Addendum 25.