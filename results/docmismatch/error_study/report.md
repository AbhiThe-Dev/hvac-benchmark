# Where the errors come from, and what a new measurement would have to do (exploratory; ERRORS_NOTES.md hashed before any analysis)

The registered 100 visits x 6 rooms, the demo's mixed setting. A check is DISCRIMINATING for a pair of causes when its Jeffreys divergence is at least 0.25; each wrong room goes into one bucket (protocol).

## Gates

- G1 base equals the stored accuracy, W0: **PASS** (74.83%)
- G1 base equals the stored accuracy, W1: **PASS** (54.67%)
- G2 wrong rooms by segment at W0 = the earlier decomposition (75 / 51 / 10 / 15): **PASS** (75 / 51 / 10 / 15)
- G3 buckets exhaustive and exclusive: **PASS**

## Part 1, W0: every wrong room, by bucket

| segment | wrong rooms | gap | not taken | misled | mixed | box-identity |
|---|---|---|---|---|---|---|
| own fault, no shared cause | 75 | 0 (0%) | 1 (1%) | 18 (24%) | 43 (57%) | 13 (17%) |
| own fault, faulty handler | 51 | 0 (0%) | 0 (0%) | 33 (65%) | 10 (20%) | 8 (16%) |
| own fault, healthy handler | 10 | 0 (0%) | 0 (0%) | 1 (10%) | 7 (70%) | 2 (20%) |
| shared | 15 | 0 (0%) | 0 (0%) | 1 (7%) | 14 (93%) | 0 (0%) |
| **all** | **151** | **0** (0%) | **1** (1%) | **53** (35%) | **74** (49%) | **23** (15%) |

Ceiling if every error of one bucket were turned right (accuracy points added; base 74.8%): gap +0.0; not taken +0.2; misled +8.8; mixed +12.3; box-identity +3.8

## Part 1, W1: every wrong room, by bucket

| segment | wrong rooms | gap | not taken | misled | mixed | box-identity |
|---|---|---|---|---|---|---|
| own fault, no shared cause | 156 | 0 (0%) | 0 (0%) | 43 (28%) | 84 (54%) | 29 (19%) |
| own fault, faulty handler | 51 | 0 (0%) | 0 (0%) | 32 (63%) | 9 (18%) | 10 (20%) |
| own fault, healthy handler | 22 | 0 (0%) | 0 (0%) | 8 (36%) | 11 (50%) | 3 (14%) |
| shared | 43 | 0 (0%) | 0 (0%) | 8 (19%) | 33 (77%) | 2 (5%) |
| **all** | **272** | **0** (0%) | **0** (0%) | **91** (33%) | **137** (50%) | **44** (16%) |

Ceiling if every error of one bucket were turned right (accuracy points added; base 54.7%): gap +0.0; not taken +0.0; misled +15.2; mixed +22.8; box-identity +7.3

## Part 1: symptom clusters of the ordinary errors (own fault, no shared cause), W0

A room's signature is the set of checks that came back abnormal / yes. Top signatures by number of errors:

| signature (abnormal checks) | rooms with it | wrong | error rate | most common truth to guess confusions | buckets |
|---|---|---|---|---|---|
| confirm_acts | 8 | 5 | 62% | wrong to wrong (3); unlisted to wrong (2) | box-identity 5 |
| flow_hood, override_diffuser | 8 | 5 | 62% | capacity_design to controller_config (3); flow_sensor to controller_config (1); controller_comms to controller_config (1) | mixed 4, misled 1 |
| bas_airflow, bas_damper, confirm_acts | 6 | 4 | 67% | controller_config to capacity_design (3); no_power to capacity_design (1) | misled 3, mixed 1 |
| bas_airflow | 6 | 4 | 67% | no_power to actuator_fail (3); damper_mech to actuator_fail (1) | mixed 3, misled 1 |
| bas_airflow, confirm_acts, duct_trace | 3 | 3 | 100% | signal_fault to controller_config (1); damper_mech to capacity_design (1); controller_config to capacity_design (1) | mixed 3 |
| confirm_acts, duct_trace | 3 | 3 | 100% | capacity_design to other (2); wrong to other (1) | misled 2, box-identity 1 |
| bas_airflow, bas_damper | 11 | 2 | 18% | damper_mech to actuator_fail (1); capacity_design to actuator_fail (1) | misled 2 |
| bas_reheat | 15 | 2 | 13% | wrong to reheat_fail (1); unlisted to reheat_fail (1) | box-identity 2 |
| confirm_acts, duct_trace, flow_hood | 4 | 2 | 50% | capacity_design to duct_diffuser (1); flow_sensor to controller_config (1) | mixed 1, not taken 1 |
| override_diffuser | 3 | 2 | 67% | controller_config to wrong (1); unlisted to wrong (1) | box-identity 2 |

The five most common signatures hold 21 of the 75 ordinary errors (28%); 50 different signatures in all.

## Part 1: the most confused ordinary pairs, and the best check the catalogue has for each (W0)

| pair | errors | best discriminating check (J, hit rates on the two causes, indicative minutes) | where the errors sit |
|---|---|---|---|
| capacity_design / controller_config | 9 | design_load (J 3.04; 0.75 vs 0.04; 6 min) | misled 5, mixed 4 |
| actuator_fail / no_power | 5 | power_24vac (J 5.27; 0.03 vs 0.92; 10 min) | mixed 4, misled 1 |
| controller_config / flow_sensor | 5 | flow_vs_gauge (J 4.95; 0.04 vs 0.92; 14 min) | misled 2, mixed 2, not taken 1 |
| controller_comms / signal_fault | 4 | controller_leds (J 1.70; 0.75 vs 0.15; 9 min) | mixed 4 |
| controller_comms / no_power | 4 | power_24vac (J 2.76; 0.20 vs 0.92; 10 min) | mixed 4 |
| capacity_design / other | 3 | design_load (J 3.04; 0.75 vs 0.04; 6 min) | misled 3 |
| capacity_design / flow_sensor | 3 | flow_vs_gauge (J 4.95; 0.04 vs 0.92; 14 min) | mixed 2, misled 1 |
| actuator_fail / damper_mech | 2 | manual_damper_test (J 4.69; 0.05 vs 0.92; 14 min) | misled 2 |

## Part 2, W0: one hypothetical check specific to the cause on the left of each pair (fires 0.80 on it, 0.08 on everything else), 3 min, control system

| arm | accuracy | gain vs base (95% CI) | added minutes / visit | wrong-and-confident change |
|---|---|---|---|---|
| pair 1: capacity_design/controller_config (check specific to controller_config) | 75.2% | +0.3 (-1.5, +2.2) | -10 | +0.2 |
| pair 2: actuator_fail/no_power (check specific to no_power) | 75.3% | +0.5 (-0.3, +1.3) | -0 | +0.2 |
| pair 3: controller_config/flow_sensor (check specific to flow_sensor) | 72.3% | -2.5 (-4.3, -0.7) | -2 | +0.2 |
| pair 4: controller_comms/signal_fault (check specific to controller_comms) | 75.5% | +0.7 (-0.3, +1.7) | -2 | +0.0 |
| pair 5: controller_comms/no_power (check specific to no_power) | 75.3% | +0.5 (-0.3, +1.3) | -0 | +0.2 |
| all five together | 73.2% | -1.7 (-4.8, +1.5) | -14 | -0.2 |

## Part 2, W1: one hypothetical check specific to the cause on the left of each pair (fires 0.80 on it, 0.08 on everything else), 3 min, control system

| arm | accuracy | gain vs base (95% CI) | added minutes / visit | wrong-and-confident change |
|---|---|---|---|---|
| pair 1: capacity_design/controller_config (check specific to controller_config) | 55.2% | +0.5 (-1.7, +2.7) | -11 | +1.3 |
| pair 2: actuator_fail/no_power (check specific to no_power) | 54.8% | +0.2 (-0.7, +1.2) | +0 | +0.5 |
| pair 3: controller_config/flow_sensor (check specific to flow_sensor) | 53.8% | -0.8 (-2.8, +1.2) | -5 | +1.8 |
| pair 4: controller_comms/signal_fault (check specific to controller_comms) | 54.2% | -0.5 (-1.7, +0.7) | -4 | +0.2 |
| pair 5: controller_comms/no_power (check specific to no_power) | 54.8% | +0.2 (-0.7, +1.2) | +0 | +0.5 |
| all five together | 55.2% | +0.5 (-2.3, +3.3) | -13 | +1.7 |

## Part 2, W0: one hypothetical check specific to the cause on the left of each pair (fires 0.80 on it, 0.08 on everything else), 10 min, at the box

| arm | accuracy | gain vs base (95% CI) | added minutes / visit | wrong-and-confident change |
|---|---|---|---|---|
| pair 1: capacity_design/controller_config (check specific to controller_config) | 76.5% | +1.7 (-0.2, +3.5) | -4 | +0.0 |
| pair 2: actuator_fail/no_power (check specific to no_power) | 75.3% | +0.5 (-0.3, +1.3) | -0 | +0.2 |
| pair 3: controller_config/flow_sensor (check specific to flow_sensor) | 75.2% | +0.3 (-0.5, +1.3) | -3 | +0.2 |
| pair 4: controller_comms/signal_fault (check specific to controller_comms) | 75.8% | +1.0 (+0.2, +2.0) | -0 | +0.0 |
| pair 5: controller_comms/no_power (check specific to no_power) | 75.3% | +0.5 (-0.3, +1.3) | -0 | +0.2 |
| all five together | 77.0% | +2.2 (-0.7, +5.2) | -5 | -0.2 |

## Part 2, W1: one hypothetical check specific to the cause on the left of each pair (fires 0.80 on it, 0.08 on everything else), 10 min, at the box

| arm | accuracy | gain vs base (95% CI) | added minutes / visit | wrong-and-confident change |
|---|---|---|---|---|
| pair 1: capacity_design/controller_config (check specific to controller_config) | 55.8% | +1.2 (-0.8, +3.3) | -5 | +1.2 |
| pair 2: actuator_fail/no_power (check specific to no_power) | 54.8% | +0.2 (-0.7, +1.2) | -0 | +0.5 |
| pair 3: controller_config/flow_sensor (check specific to flow_sensor) | 54.3% | -0.3 (-1.7, +1.0) | -1 | +0.8 |
| pair 4: controller_comms/signal_fault (check specific to controller_comms) | 54.5% | -0.2 (-1.2, +1.0) | -0 | +0.2 |
| pair 5: controller_comms/no_power (check specific to no_power) | 54.8% | +0.2 (-0.7, +1.2) | -0 | +0.5 |
| all five together | 56.3% | +1.7 (-0.8, +4.3) | -3 | +1.5 |

## Predictions (written before any analysis)

- E1 (ordinary errors that are not box-identity: 'not taken' the largest bucket and at least 40%, 'gap' at most 20%): **FAILED** (not taken 2%, gap 0%, misled 29%, mixed 69%)
- E2 (gap errors at most 25% of all wrong rooms): **HELD** (0%)
- E3 (the five most common signatures hold at most 50% of the ordinary errors): **HELD** (28%)
- E4 (one hypothetical check for the most-confused pair raises W0 accuracy by at most 1.5 points; 3-minute version): **HELD** (+0.3)
- E5 (all five together raise W0 accuracy by 2 to 6 points and stay below 85%; 3-minute version): **FAILED** (-1.7, 73.2%)
- E6 (the ceiling for fixing every gap error is at most 4 points): **HELD** (+0.0)
- E7 (folded rooms mostly 'not taken', at least 60%): **FAILED** (0%)
