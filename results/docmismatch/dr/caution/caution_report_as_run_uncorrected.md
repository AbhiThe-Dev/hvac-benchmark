# Is the engine too cautious where the data are diagnosable? (Addendum 12)

Leave-one-topology-out over the 8 `EXISTING` topologies, legacy telemetry, one visit window, `active` policy, tau 0.95. `base` = calibrated beta, masked, 24 reads; `beta1` = no tempering; `beta1_unmasked` = no tempering + channel masking off; `budget72` = calibrated beta with 72 reads. 'acc | resolved' is class-balanced over is_wrong / is_right episodes (stated confidence is 0.95). Simulation only, small samples.

## branch_coil  (calibrated beta per held-out fit: mean 0.42, range 0.20-0.70)

| variant | n eps | resolved | acc \| resolved | wrong & confident | mean reads (resolved) | gained | lost | correct->wrong | wrong->correct |
|---|---|---|---|---|---|---|---|---|---|
| base | 105 | 68/105 (65%) | 0.717 | 18.1% | 6.5 |  |  |  |  |
| beta1 | 105 | 102/105 (97%) | 0.715 | 28.6% | 4.6 | 34 | 0 | 0 | 2 |
| beta1_unmasked | 105 | 79/105 (75%) | 0.760 | 17.1% | 6.0 | 24 | 13 | 3 | 3 |
| budget72 | 105 | 75/105 (71%) | 0.729 | 19.0% | 9.5 | 7 | 0 | 0 | 0 |

## loop_branch  (calibrated beta per held-out fit: mean 0.19, range 0.10-0.20)

| variant | n eps | resolved | acc \| resolved | wrong & confident | mean reads (resolved) | gained | lost | correct->wrong | wrong->correct |
|---|---|---|---|---|---|---|---|---|---|
| base | 40 | 15/40 (38%) | 1.000 | 0.0% | 5.3 |  |  |  |  |
| beta1 | 40 | 40/40 (100%) | 0.589 | 40.0% | 1.9 | 25 | 0 | 2 | 0 |
| beta1_unmasked | 40 | 40/40 (100%) | 0.589 | 40.0% | 1.9 | 25 | 0 | 2 | 0 |
| budget72 | 40 | 15/40 (38%) | 1.000 | 0.0% | 5.3 | 0 | 0 | 0 | 0 |

## coil_ahu  (calibrated beta per held-out fit: mean 1.00, range 1.00-1.00)

| variant | n eps | resolved | acc \| resolved | wrong & confident | mean reads (resolved) | gained | lost | correct->wrong | wrong->correct |
|---|---|---|---|---|---|---|---|---|---|
| base | 44 | 27/44 (61%) | 0.671 | 15.9% | 8.4 |  |  |  |  |
| beta1 | 44 | 27/44 (61%) | 0.671 | 15.9% | 8.4 | 0 | 0 | 0 | 0 |
| beta1_unmasked | 44 | 24/44 (55%) | 0.719 | 11.4% | 7.8 | 0 | 3 | 0 | 0 |
| budget72 | 44 | 27/44 (61%) | 0.671 | 15.9% | 8.4 | 0 | 0 | 0 | 0 |

## ahu_vav  (calibrated beta per held-out fit: mean 0.96, range 0.70-1.00)

| variant | n eps | resolved | acc \| resolved | wrong & confident | mean reads (resolved) | gained | lost | correct->wrong | wrong->correct |
|---|---|---|---|---|---|---|---|---|---|
| base | 56 | 56/56 (100%) | 0.804 | 19.6% | 2.3 |  |  |  |  |
| beta1 | 56 | 56/56 (100%) | 0.804 | 19.6% | 2.3 | 0 | 0 | 0 | 0 |
| beta1_unmasked | 56 | 56/56 (100%) | 0.804 | 19.6% | 2.3 | 0 | 0 | 0 | 0 |
| budget72 | 56 | 56/56 (100%) | 0.804 | 19.6% | 2.3 | 0 | 0 | 0 | 0 |

## Frozen reading rules (Addendum 12)

| slot | variant | verdict |
|---|---|---|
| branch_coil | beta1 | REJECTED (accuracy among resolved below 0.90) |
| branch_coil | beta1_unmasked | REJECTED (accuracy among resolved below 0.90) |
| branch_coil | budget72 | INERT |
| loop_branch | beta1 | REJECTED (accuracy among resolved below 0.90) |
| loop_branch | beta1_unmasked | REJECTED (accuracy among resolved below 0.90) |
| loop_branch | budget72 | INERT |
| coil_ahu | beta1 | INERT |
| coil_ahu | beta1_unmasked | INERT |
| coil_ahu | budget72 | INERT |
| ahu_vav | beta1 | INERT |
| ahu_vav | beta1_unmasked | INERT |
| ahu_vav | budget72 | INERT |

- `beta1`: worth pursuing in 0 of 3 diagnosable slots -> not worth pursuing overall

- `beta1_unmasked`: worth pursuing in 0 of 3 diagnosable slots -> not worth pursuing overall

- `budget72`: worth pursuing in 0 of 3 diagnosable slots -> not worth pursuing overall