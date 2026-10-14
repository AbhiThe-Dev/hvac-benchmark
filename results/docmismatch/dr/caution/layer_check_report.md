# Does the reliability layer remove the overconfidence? (Addendum 14, Part B)

Frozen nested path over the 8 `EXISTING` train-role topologies (leave-one-topology-out), legacy telemetry, one visit window, `active` policy, tau 0.95, frozen `sel_slice` fit + run options and layer configuration. `none` = plain 0.95 rule; `new` = calibrated reliability layer (primary); `legacy` = `abstain.py` (descriptive). Accuracy and coverage are class-balanced over is_wrong / is_right episodes; a verdict is right when CONFIRMED on a right document or REFUTED on a wrong one; 'retained' = answered-and-correct episodes / the plain rule's. CI = cluster bootstrap (1000, seed 0). Simulation only, small samples.

Consistency check (Deviation 1): `none` equals Part A's corrected `base` exactly on all 127 wrong-documentation episodes and on the 48 of 118 right-documentation episodes drawn identically by both harnesses (the rest are different draws of matched-correct negatives).

## All slots pooled

| layer | n eps | answered | coverage | acc \| answered [95% CI] | wrong & confident | false alarms (right docs) | missed faults (wrong docs) | retained vs plain |
|---|---|---|---|---|---|---|---|---|
| none | 585 | 268/585 | 0.46 | 0.869 [0.82, 0.92] | 5.6% | 2.8% (288) | 8.4% (297) |  |
| new | 585 | 8/585 | 0.01 | 0.917 [0.62, 1.00] | 0.2% | 0.0% (288) | 0.3% (297) | 0.03 |
| legacy | 585 | 39/585 | 0.07 | 1.000 [1.00, 1.00] | 0.0% | 0.0% (288) | 0.0% (297) | 0.17 |

## branch_coil  (105 episodes, 49 clusters)

| layer | n eps | answered | coverage | acc \| answered [95% CI] | wrong & confident | false alarms (right docs) | missed faults (wrong docs) | retained vs plain |
|---|---|---|---|---|---|---|---|---|
| none | 105 | 32/105 | 0.32 | 0.909 [0.65, 1.00] | 1.9% | 2.0% (49) | 1.8% (56) |  |
| new | 105 | 0/105 | 0.00 | nan n/a | 0.0% | 0.0% (49) | 0.0% (56) | 0.00 |
| legacy | 105 | 4/105 | 0.04 | 1.000 [1.00, 1.00] | 0.0% | 0.0% (49) | 0.0% (56) | 0.13 |

`new` abstentions: insufficient evidence: no verdict within the reading budget x73; near-twin / candidates not separated x21; slot not reliable in leave-unit-out runs x9; reliability score below the honest-confidence cut x2

## coil_ahu  (44 episodes, 23 clusters)

| layer | n eps | answered | coverage | acc \| answered [95% CI] | wrong & confident | false alarms (right docs) | missed faults (wrong docs) | retained vs plain |
|---|---|---|---|---|---|---|---|---|
| none | 44 | 16/44 | 0.36 | 0.833 [0.50, 1.00] | 4.5% | 4.5% (22) | 4.5% (22) |  |
| new | 44 | 2/44 | 0.05 | 0.500 [0.00, 1.00] | 2.3% | 0.0% (22) | 4.5% (22) | 0.07 |
| legacy | 44 | 3/44 | 0.07 | 1.000 [1.00, 1.00] | 0.0% | 0.0% (22) | 0.0% (22) | 0.21 |

`new` abstentions: insufficient evidence: no verdict within the reading budget x28; no honest confidence level demonstrated by out-of-unit runs x12; near-twin / candidates not separated x2

## ahu_vav  (56 episodes, 38 clusters)

| layer | n eps | answered | coverage | acc \| answered [95% CI] | wrong & confident | false alarms (right docs) | missed faults (wrong docs) | retained vs plain |
|---|---|---|---|---|---|---|---|---|
| none | 56 | 34/56 | 0.61 | 1.000 [1.00, 1.00] | 0.0% | 0.0% (28) | 0.0% (28) |  |
| new | 56 | 0/56 | 0.00 | nan n/a | 0.0% | 0.0% (28) | 0.0% (28) | 0.00 |
| legacy | 56 | 10/56 | 0.18 | 1.000 [1.00, 1.00] | 0.0% | 0.0% (28) | 0.0% (28) | 0.29 |

`new` abstentions: insufficient evidence: no verdict within the reading budget x22; no honest confidence level demonstrated by out-of-unit runs x20; near-twin / candidates not separated x14

## loop_branch  (control)  (40 episodes, 31 clusters)

| layer | n eps | answered | coverage | acc \| answered [95% CI] | wrong & confident | false alarms (right docs) | missed faults (wrong docs) | retained vs plain |
|---|---|---|---|---|---|---|---|---|
| none | 40 | 14/40 | 0.35 | 1.000 [1.00, 1.00] | 0.0% | 0.0% (19) | 0.0% (21) |  |
| new | 40 | 2/40 | 0.05 | 1.000 [1.00, 1.00] | 0.0% | 0.0% (19) | 0.0% (21) | 0.14 |
| legacy | 40 | 0/40 | 0.00 | nan n/a | 0.0% | 0.0% (19) | 0.0% (21) | 0.00 |

`new` abstentions: insufficient evidence: no verdict within the reading budget x26; no honest confidence level demonstrated by out-of-unit runs x10; slot not reliable in leave-unit-out runs x2

## Other slots (descriptive only; not part of the frozen verdict)

| slot | n eps | none: answered / acc | new: answered / acc / wrong&confident | legacy: answered / acc |
|---|---|---|---|---|
| ahu_sat | 32 | 15/32 / 0.94 | 0/32 / nan / 0% | 0/32 / nan |
| coil_vav | 80 | 58/80 / 0.72 | 0/80 / nan / 0% | 0/80 / nan |
| loop_pump | 4 | 4/4 / 1.00 | 0/4 / nan / 0% | 0/4 / nan |
| vav_dat | 96 | 95/96 / 0.85 | 4/96 / 1.00 / 0% | 22/96 / 1.00 |
| vav_zone | 128 | 0/128 / nan | 0/128 / nan / 0% | 0/128 / nan |

## Frozen reading rules (Addendum 14, Part B)

| slot | verdict (layer `new`) |
|---|---|
| branch_coil | NO PROBLEM TO FIX |
| coil_ahu | ABSTAINS -- too few answers to judge (honest but empty) |
| ahu_vav | NO PROBLEM TO FIX |

**Overall: the overconfidence was mostly an artefact of the defect.**

Control `loop_branch`: no regression (`new` answers 2/40, accuracy among answered 1.00).