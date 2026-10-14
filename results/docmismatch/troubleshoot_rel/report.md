# More reliable answers: accuracy and the threshold (Addendum 42)

Simulation only: the nine R0 cells of Addendum 30 (1000 events each, the same events as Addendum 41), answers from a world sharpened by `b` (0 = as the tool assumes; 0.5 = half the way to certainty; 1.0 = every check deterministic, a ceiling not a forecast), `min_rate` 0.02. The tool keeps its own response model throughout. Labels are Addendum 21's, with Addendum 41's bars scaled to nine cells. Nothing here is evidence about real technicians and nothing changes the tool's defaults.

## Gates

- **G1: PASS.** first 50 events of every cell match Addendum 30's stored kinds
- **G2: PASS.** b = 0 reproduces Addendum 41's R0 cells exactly for 9 cells x 20 variants
- **G3: PASS.** the answer table is deterministic and independent of question order; the sharpened oracle at b = 0 answers exactly as TableOracle
- **G4: PASS.** sharpening is the identity at 0, stays in [0, 1], moves toward 0 or 1 and never across 0.5, is binary at 1.0, and gives bas_ahu_fan's 0.92 hit rate 0.96 at b = 0.5
- **G5: PASS.** 3 cells reproduce exactly on a second run (one worker against many) with the same seed

## Reliability effect at tau 0.95 (tool_joint, T3-noattr; cell means; paired against b = 0 on the same events)

| b | minutes | checks | accuracy | wrong-and-confident | concluded | accuracy change (cells labelled IMPROVES, of 9) | minutes change |
|---|---|---|---|---|---|---|---|
| 0.0 | 63.1 | 11.20 | 79% | 0.0083 | 31% | - | - |
| 0.5 | 60.6 | 10.78 | 87% | 0.0056 | 36% | +7.5 pts (9) | -4% |
| 1.0 | 58.6 | 10.41 | 93% | 0.0039 | 43% | +13.8 pts (9) | -7% |

Accuracy by visit kind (cell means):

| b | single | multi (no shared cause) | shared cause |
|---|---|---|---|
| 0.0 | 76% | 79% | 88% |
| 0.5 | 85% | 88% | 89% |
| 1.0 | 93% | 96% | 90% |

### tool_joint, T3-noattr, b = 0.0: lowering tau

| tau | label | IMPROVES | NEITHER | TRADE | WORSE | safety regressions (of 9) | minutes | accuracy | wrong-and-confident |
|---|---|---|---|---|---|---|---|---|---|
| 0.95 (baseline) | - | - | - | - | - | - | 63.1 | 79% | 0.0083 |
| 0.9 | **NO EFFECT** | 0 | 9 | 0 | 0 | 0 | 62.4 (-1%) | 79% (-0.1 pts) | 0.0192 |
| 0.85 | **UNSAFE** | 9 | 0 | 0 | 0 | 9 | 57.6 (-9%) | 78% (-1.3 pts) | 0.0617 |
| 0.8 | **UNSAFE** | 6 | 0 | 3 | 0 | 9 | 55.9 (-11%) | 77% (-1.8 pts) | 0.0835 |
| 0.75 | **UNSAFE** | 0 | 0 | 9 | 0 | 9 | 53.2 (-16%) | 76% (-3.3 pts) | 0.1100 |

### tool_joint, T3-noattr, b = 0.5: lowering tau

| tau | label | IMPROVES | NEITHER | TRADE | WORSE | safety regressions (of 9) | minutes | accuracy | wrong-and-confident |
|---|---|---|---|---|---|---|---|---|---|
| 0.95 (baseline) | - | - | - | - | - | - | 60.6 | 87% | 0.0056 |
| 0.9 | **NO EFFECT** | 0 | 9 | 0 | 0 | 0 | 59.7 (-1%) | 87% (-0.1 pts) | 0.0110 |
| 0.85 | **UNSAFE** | 9 | 0 | 0 | 0 | 8 | 55.9 (-8%) | 86% (-0.8 pts) | 0.0325 |
| 0.8 | **UNSAFE** | 9 | 0 | 0 | 0 | 8 | 54.6 (-10%) | 86% (-1.0 pts) | 0.0431 |
| 0.75 | **UNSAFE** | 4 | 0 | 5 | 0 | 9 | 52.5 (-13%) | 84% (-2.2 pts) | 0.0598 |

### tool_joint, T3-noattr, b = 1.0: lowering tau

| tau | label | IMPROVES | NEITHER | TRADE | WORSE | safety regressions (of 9) | minutes | accuracy | wrong-and-confident |
|---|---|---|---|---|---|---|---|---|---|
| 0.95 (baseline) | - | - | - | - | - | - | 58.6 | 93% | 0.0039 |
| 0.9 | **NO EFFECT** | 1 | 8 | 0 | 0 | 0 | 57.3 (-2%) | 93% (+0.2 pts) | 0.0047 |
| 0.85 | **TRADES** | 7 | 2 | 0 | 0 | 0 | 54.5 (-7%) | 93% (+0.2 pts) | 0.0049 |
| 0.8 | **PASSES** | 9 | 0 | 0 | 0 | 0 | 53.5 (-9%) | 93% (+0.2 pts) | 0.0052 |
| 0.75 | **PASSES** | 9 | 0 | 0 | 0 | 0 | 52.0 (-11%) | 93% (-0.3 pts) | 0.0103 |

### tool_ticket_memo2, T3-noattr, b = 0.0: lowering tau

| tau | label | IMPROVES | NEITHER | TRADE | WORSE | safety regressions (of 9) | minutes | accuracy | wrong-and-confident |
|---|---|---|---|---|---|---|---|---|---|
| 0.95 (baseline) | - | - | - | - | - | - | 60.8 | 78% | 0.0124 |
| 0.9 | **NO EFFECT** | 0 | 9 | 0 | 0 | 0 | 60.7 (-0%) | 78% (+0.0 pts) | 0.0208 |
| 0.85 | **UNSAFE** | 9 | 0 | 0 | 0 | 9 | 56.4 (-7%) | 77% (-1.1 pts) | 0.0608 |
| 0.8 | **UNSAFE** | 6 | 0 | 3 | 0 | 9 | 54.6 (-10%) | 77% (-1.6 pts) | 0.0847 |
| 0.75 | **UNSAFE** | 1 | 0 | 8 | 0 | 9 | 52.2 (-14%) | 75% (-2.9 pts) | 0.1108 |

### tool_ticket_memo2, T3-noattr, b = 0.5: lowering tau

| tau | label | IMPROVES | NEITHER | TRADE | WORSE | safety regressions (of 9) | minutes | accuracy | wrong-and-confident |
|---|---|---|---|---|---|---|---|---|---|
| 0.95 (baseline) | - | - | - | - | - | - | 58.4 | 86% | 0.0089 |
| 0.9 | **NO EFFECT** | 0 | 9 | 0 | 0 | 0 | 58.3 (-0%) | 86% (+0.0 pts) | 0.0130 |
| 0.85 | **UNSAFE** | 9 | 0 | 0 | 0 | 8 | 54.8 (-6%) | 85% (-0.6 pts) | 0.0333 |
| 0.8 | **UNSAFE** | 9 | 0 | 0 | 0 | 8 | 53.4 (-9%) | 85% (-0.9 pts) | 0.0451 |
| 0.75 | **UNSAFE** | 3 | 0 | 6 | 0 | 9 | 51.4 (-12%) | 84% (-2.1 pts) | 0.0616 |

### tool_ticket_memo2, T3-noattr, b = 1.0: lowering tau

| tau | label | IMPROVES | NEITHER | TRADE | WORSE | safety regressions (of 9) | minutes | accuracy | wrong-and-confident |
|---|---|---|---|---|---|---|---|---|---|
| 0.95 (baseline) | - | - | - | - | - | - | 55.9 | 92% | 0.0062 |
| 0.9 | **NO EFFECT** | 0 | 9 | 0 | 0 | 0 | 55.8 (-0%) | 92% (+0.0 pts) | 0.0065 |
| 0.85 | **TRADES** | 5 | 4 | 0 | 0 | 0 | 53.1 (-5%) | 92% (+0.0 pts) | 0.0065 |
| 0.8 | **PASSES** | 9 | 0 | 0 | 0 | 0 | 52.1 (-7%) | 92% (+0.0 pts) | 0.0065 |
| 0.75 | **PASSES** | 9 | 0 | 0 | 0 | 0 | 50.8 (-9%) | 92% (-0.5 pts) | 0.0118 |

### tool_joint, T3, b = 0.0: lowering tau

| tau | label | IMPROVES | NEITHER | TRADE | WORSE | safety regressions (of 9) | minutes | accuracy | wrong-and-confident |
|---|---|---|---|---|---|---|---|---|---|
| 0.95 (baseline) | - | - | - | - | - | - | 59.2 | 81% | 0.0084 |
| 0.9 | **NO EFFECT** | 0 | 9 | 0 | 0 | 1 | 58.6 (-1%) | 81% (-0.1 pts) | 0.0233 |
| 0.85 | **UNSAFE** | 8 | 0 | 1 | 0 | 9 | 53.5 (-10%) | 79% (-1.5 pts) | 0.0666 |
| 0.8 | **UNSAFE** | 5 | 0 | 4 | 0 | 9 | 52.3 (-12%) | 79% (-1.9 pts) | 0.0825 |
| 0.75 | **UNSAFE** | 0 | 0 | 9 | 0 | 9 | 49.8 (-16%) | 77% (-3.3 pts) | 0.1079 |

### tool_joint, T3, b = 0.5: lowering tau

| tau | label | IMPROVES | NEITHER | TRADE | WORSE | safety regressions (of 9) | minutes | accuracy | wrong-and-confident |
|---|---|---|---|---|---|---|---|---|---|
| 0.95 (baseline) | - | - | - | - | - | - | 56.1 | 89% | 0.0054 |
| 0.9 | **NO EFFECT** | 0 | 9 | 0 | 0 | 0 | 55.4 (-1%) | 89% (-0.1 pts) | 0.0116 |
| 0.85 | **UNSAFE** | 9 | 0 | 0 | 0 | 8 | 51.3 (-9%) | 88% (-0.8 pts) | 0.0323 |
| 0.8 | **UNSAFE** | 9 | 0 | 0 | 0 | 8 | 50.4 (-10%) | 88% (-1.0 pts) | 0.0405 |
| 0.75 | **UNSAFE** | 4 | 0 | 5 | 0 | 9 | 48.4 (-14%) | 86% (-2.2 pts) | 0.0577 |

### tool_joint, T3, b = 1.0: lowering tau

| tau | label | IMPROVES | NEITHER | TRADE | WORSE | safety regressions (of 9) | minutes | accuracy | wrong-and-confident |
|---|---|---|---|---|---|---|---|---|---|
| 0.95 (baseline) | - | - | - | - | - | - | 52.9 | 95% | 0.0039 |
| 0.9 | **NO EFFECT** | 1 | 8 | 0 | 0 | 0 | 51.7 (-2%) | 95% (+0.2 pts) | 0.0046 |
| 0.85 | **PASSES** | 9 | 0 | 0 | 0 | 0 | 48.5 (-8%) | 95% (+0.2 pts) | 0.0048 |
| 0.8 | **PASSES** | 9 | 0 | 0 | 0 | 0 | 47.9 (-9%) | 95% (+0.2 pts) | 0.0050 |
| 0.75 | **PASSES** | 9 | 0 | 0 | 0 | 0 | 46.4 (-12%) | 95% (-0.3 pts) | 0.0101 |

### tool_ticket_memo2, T3, b = 0.0: lowering tau

| tau | label | IMPROVES | NEITHER | TRADE | WORSE | safety regressions (of 9) | minutes | accuracy | wrong-and-confident |
|---|---|---|---|---|---|---|---|---|---|
| 0.95 (baseline) | - | - | - | - | - | - | 54.9 | 80% | 0.0123 |
| 0.9 | **NO EFFECT** | 0 | 9 | 0 | 0 | 0 | 54.8 (-0%) | 80% (+0.0 pts) | 0.0241 |
| 0.85 | **UNSAFE** | 8 | 0 | 1 | 0 | 9 | 50.0 (-9%) | 78% (-1.3 pts) | 0.0651 |
| 0.8 | **UNSAFE** | 6 | 0 | 3 | 0 | 9 | 48.9 (-11%) | 78% (-1.7 pts) | 0.0827 |
| 0.75 | **UNSAFE** | 1 | 0 | 8 | 0 | 9 | 46.5 (-15%) | 77% (-3.0 pts) | 0.1076 |

### tool_ticket_memo2, T3, b = 0.5: lowering tau

| tau | label | IMPROVES | NEITHER | TRADE | WORSE | safety regressions (of 9) | minutes | accuracy | wrong-and-confident |
|---|---|---|---|---|---|---|---|---|---|
| 0.95 (baseline) | - | - | - | - | - | - | 51.9 | 88% | 0.0087 |
| 0.9 | **NO EFFECT** | 0 | 9 | 0 | 0 | 0 | 51.8 (-0%) | 88% (+0.0 pts) | 0.0138 |
| 0.85 | **UNSAFE** | 9 | 0 | 0 | 0 | 7 | 47.8 (-8%) | 87% (-0.7 pts) | 0.0330 |
| 0.8 | **UNSAFE** | 9 | 0 | 0 | 0 | 8 | 46.9 (-10%) | 87% (-0.9 pts) | 0.0420 |
| 0.75 | **UNSAFE** | 4 | 0 | 5 | 0 | 9 | 44.9 (-13%) | 85% (-2.1 pts) | 0.0595 |

### tool_ticket_memo2, T3, b = 1.0: lowering tau

| tau | label | IMPROVES | NEITHER | TRADE | WORSE | safety regressions (of 9) | minutes | accuracy | wrong-and-confident |
|---|---|---|---|---|---|---|---|---|---|
| 0.95 (baseline) | - | - | - | - | - | - | 48.5 | 95% | 0.0062 |
| 0.9 | **NO EFFECT** | 0 | 9 | 0 | 0 | 0 | 48.4 (-0%) | 95% (+0.0 pts) | 0.0064 |
| 0.85 | **PASSES** | 9 | 0 | 0 | 0 | 0 | 45.1 (-7%) | 95% (+0.0 pts) | 0.0064 |
| 0.8 | **PASSES** | 9 | 0 | 0 | 0 | 0 | 44.6 (-8%) | 95% (+0.0 pts) | 0.0064 |
| 0.75 | **PASSES** | 9 | 0 | 0 | 0 | 1 | 43.0 (-11%) | 94% (-0.4 pts) | 0.0122 |

Lowest passing tau (tool_joint, T3-noattr): b = 0.0: none, b = 0.5: none, b = 1.0: 0.75.

## Registered predictions

| | held | detail |
|---|---|---|
| P1 | yes | accuracy 0.792 at b=0, 0.867 at 0.5, 0.930 at 1.0 (rise +0.138) |
| P2 | yes | accuracy at b=1.0 is 0.930 |
| P3 | yes | 0.792 < 0.867 < 0.930 |
| P4 | yes | wrong-and-confident 0.0083 at b=0, 0.0039 at b=1.0 |
| P5 | NO | minutes 63.1 at b=0, 58.6 at b=1.0 (-7%) |
| P6 | yes | b=1.0, tau 0.85: safety regressions in 0 of 9 cells (TRADES) |
| P7 | yes | b=0.5, tau 0.85: safety regressions in 8 of 9 cells (UNSAFE) |
| P8 | yes | accuracy gain at b=1.0: single +0.165, shared +0.021 |

## What is left wrong at b = 0.0 (tool_joint, T3-noattr, tau 0.95; all 9 cells pooled)

| true cause | complaints | exactly right | concluded and wrong | most common wrong answers |
|---|---|---|---|---|
| low_static | 5332 | 92% | 1% | capacity_design (184), controller_config (84), ahu_fan_off (75) |
| ahu_fan_off | 4235 | 88% | 3% | low_static (291), capacity_design (140), controller_config (22) |
| zone_sensor_setpoint | 2236 | 94% | 1% | low_static (37), other (28), capacity_design (25) |
| controller_config | 1419 | 64% | 2% | capacity_design (207), other (103), duct_diffuser (52) |
| flow_sensor | 1285 | 87% | 2% | controller_config (54), low_static (27), other (22) |
| duct_diffuser | 1058 | 77% | 1% | other (62), controller_config (61), capacity_design (43) |
| wrong box | 922 | 77% | 2% | reheat_fail (30), zone_sensor_setpoint (28), controller_config (27) |
| capacity_design | 816 | 59% | 2% | other (121), controller_config (94), flow_sensor (32) |
| other | 704 | 61% | 2% | controller_config (73), capacity_design (54), duct_diffuser (38) |
| reheat_fail | 650 | 83% | 1% | other (49), zone_sensor_setpoint (26), low_static (10) |
| damper_mech | 585 | 85% | 1% | actuator_fail (37), capacity_design (23), low_static (6) |
| actuator_fail | 571 | 80% | 1% | damper_mech (29), signal_fault (17), capacity_design (15) |
| controller_comms | 304 | 72% | 1% | no_power (27), actuator_fail (25), signal_fault (15) |
| no_power | 253 | 83% | 1% | actuator_fail (17), capacity_design (8), controller_comms (7) |
| signal_fault | 189 | 74% | 3% | controller_comms (17), actuator_fail (12), capacity_design (5) |
| unlisted | 104 | 29% | 2% | wrong box (53), reheat_fail (7), other (6) |

## What is left wrong at b = 1.0 (tool_joint, T3-noattr, tau 0.95; all 9 cells pooled)

| true cause | complaints | exactly right | concluded and wrong | most common wrong answers |
|---|---|---|---|---|
| low_static | 5332 | 90% | 0% | capacity_design (286), ahu_fan_off (217), controller_config (4) |
| ahu_fan_off | 4235 | 92% | 2% | capacity_design (194), low_static (151), controller_config (3) |
| zone_sensor_setpoint | 2236 | 98% | 1% | low_static (33), ahu_fan_off (3) |
| controller_config | 1419 | 83% | 1% | capacity_design (113), other (89), low_static (30) |
| flow_sensor | 1285 | 98% | 1% | low_static (26), ahu_fan_off (3) |
| duct_diffuser | 1058 | 98% | 1% | low_static (17), ahu_fan_off (3) |
| wrong box | 922 | 97% | 1% | low_static (21), ahu_fan_off (3), zone_sensor_setpoint (1) |
| capacity_design | 816 | 72% | 1% | other (173), controller_config (38), low_static (17) |
| other | 704 | 98% | 1% | low_static (11), ahu_fan_off (2) |
| reheat_fail | 650 | 98% | 1% | low_static (10), ahu_fan_off (1) |
| damper_mech | 585 | 99% | 1% | low_static (6) |
| actuator_fail | 571 | 98% | 1% | low_static (9) |
| controller_comms | 304 | 99% | 1% | low_static (4) |
| no_power | 253 | 98% | 1% | low_static (4) |
| signal_fault | 189 | 97% | 3% | low_static (5) |
| unlisted | 104 | 47% | 1% | wrong box (53), ahu_fan_off (1), low_static (1) |
