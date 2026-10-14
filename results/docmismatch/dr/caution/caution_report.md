# Is the engine too cautious where the data are diagnosable? (Addendum 12)

Leave-one-topology-out over the 8 `EXISTING` topologies, legacy telemetry, one visit window, `active` policy, tau 0.95. `base` = calibrated beta, masked, 24 reads; `beta1` = no tempering; `beta1_unmasked` = no tempering + channel masking off; `budget72` = calibrated beta with 72 reads. 'acc | resolved' is class-balanced over is_wrong / is_right episodes (stated confidence is 0.95). Simulation only, small samples.

## branch_coil  (calibrated beta per held-out fit: mean 0.42, range 0.20-0.70)

| variant | n eps | resolved | acc \| resolved | wrong & confident | mean reads (resolved) | gained | lost | correct->wrong | wrong->correct |
|---|---|---|---|---|---|---|---|---|---|
| base | 105 | 32/105 (30%) | 0.849 | 4.8% | 10.1 |  |  |  |  |
| beta1 | 105 | 92/105 (88%) | 0.685 | 27.6% | 6.2 | 60 | 0 | 0 | 0 |
| beta1_unmasked | 105 | 59/105 (56%) | 0.937 | 3.8% | 7.4 | 29 | 2 | 0 | 2 |
| budget72 | 105 | 41/105 (39%) | 0.889 | 4.8% | 19.4 | 9 | 0 | 0 | 0 |

## loop_branch  (calibrated beta per held-out fit: mean 0.19, range 0.10-0.20)

| variant | n eps | resolved | acc \| resolved | wrong & confident | mean reads (resolved) | gained | lost | correct->wrong | wrong->correct |
|---|---|---|---|---|---|---|---|---|---|
| base | 40 | 15/40 (38%) | 1.000 | 0.0% | 5.7 |  |  |  |  |
| beta1 | 40 | 40/40 (100%) | 0.639 | 35.0% | 2.0 | 25 | 0 | 3 | 0 |
| beta1_unmasked | 40 | 40/40 (100%) | 0.639 | 35.0% | 2.0 | 25 | 0 | 3 | 0 |
| budget72 | 40 | 15/40 (38%) | 1.000 | 0.0% | 5.7 | 0 | 0 | 0 | 0 |

## coil_ahu  (calibrated beta per held-out fit: mean 1.00, range 1.00-1.00)

| variant | n eps | resolved | acc \| resolved | wrong & confident | mean reads (resolved) | gained | lost | correct->wrong | wrong->correct |
|---|---|---|---|---|---|---|---|---|---|
| base | 44 | 15/44 (34%) | 0.792 | 4.5% | 8.6 |  |  |  |  |
| beta1 | 44 | 15/44 (34%) | 0.792 | 4.5% | 8.6 | 0 | 0 | 0 | 0 |
| beta1_unmasked | 44 | 19/44 (43%) | 0.664 | 9.1% | 9.7 | 4 | 0 | 0 | 0 |
| budget72 | 44 | 15/44 (34%) | 0.792 | 4.5% | 8.6 | 0 | 0 | 0 | 0 |

## ahu_vav  (calibrated beta per held-out fit: mean 0.96, range 0.70-1.00)

| variant | n eps | resolved | acc \| resolved | wrong & confident | mean reads (resolved) | gained | lost | correct->wrong | wrong->correct |
|---|---|---|---|---|---|---|---|---|---|
| base | 56 | 33/56 (59%) | 1.000 | 0.0% | 3.7 |  |  |  |  |
| beta1 | 56 | 33/56 (59%) | 1.000 | 0.0% | 3.2 | 0 | 0 | 0 | 0 |
| beta1_unmasked | 56 | 36/56 (64%) | 0.971 | 1.8% | 4.4 | 3 | 0 | 0 | 0 |
| budget72 | 56 | 33/56 (59%) | 1.000 | 0.0% | 3.7 | 0 | 0 | 0 | 0 |

## Frozen reading rules (Addendum 12)

| slot | variant | verdict |
|---|---|---|
| branch_coil | beta1 | REJECTED (accuracy among resolved below 0.90) |
| branch_coil | beta1_unmasked | WORTH PURSUING |
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

- `beta1_unmasked`: worth pursuing in 1 of 3 diagnosable slots -> not worth pursuing overall

- `budget72`: worth pursuing in 0 of 3 diagnosable slots -> not worth pursuing overall