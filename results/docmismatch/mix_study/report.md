# Severity-mixture study (MIX_PROTOCOL.md)

Simulation; layouts and point maps real (Mortar), faults, answers and minutes simulated and placeholder; worlds from the tool's own model family. `default` = shipped joint model, `mix` = `low_mix` ((0.05, 0.25), (0.15, 0.25), (0.5, 0.25), (0.9, 0.25)), `adjusted` = `r_low` 0.10 (S2 reference only). 95% intervals from a bootstrap over visits. Nothing here changes a default of the tool.

Run 2026-10-11, 224 s.

> **REGISTERED OUTCOME: NO RESULT.** Gate G1a-ii, as registered (`study_tau.gate_g3`), FAILED on a reference Addendum 41 had already found to be wrong (the wrong event stream). The numbers below are reported under the logged deviation `MIX_DEVIATIONS.md` D1, which replaces that gate with its corrected form (PASS below). No result had been seen when the deviation was decided. They are not the registered result.

## Gates

| gate | result | detail |
|---|---|---|
| G6 bldg11 check list = demo's | PASS | 28 checks, same names and order as the demo |
| G3 visit generator and composition | PASS | bldg11: generalised draw identical to simulate.draw_visit; bldg11: 100 visits composed as stated (largest handler AHU06, 49 rooms); bldg18: 100 visits composed as stated (largest handler AHU01, 67 rooms); bldg8: 100 visits composed as stated (largest handler AHU01, 24 rooms) |
| G4 oracle order-independent | PASS | 108 questions forward and backward |
| G2a mixture sums | PASS | state prior sums to 1 (default and mixture); by-cause air-handler posterior sums to 1: True; states ('ok', 'ahu_fan_off', 'low_static', 'low_static~1', 'low_static~2', 'low_static~3') |
| G2b one-level mixture = default | PASS | a one-level mixture at r = 0.5 gives the default's guesses, conclusions and minutes on 30 bldg11 visits x 2 worlds: identical |
| G5 completeness | PASS | 1400 of 1400 building runs, 18 of 18 S1 cells, minutes finite: True |
| G1a-i default path reproduces Addendum 30 (study_tau.gate_g2) | PASS | (a) tool_joint at T3, primary cell, first 200 events: identical to Addendum 30's stored per-event results; (b) routine at 0.95/0.003, T3, primary cell: 63.6 min / 83% against Addendum 31's 65 / 82% |
| G1a-ii AS REGISTERED (study_tau.gate_g3): known wrong reference, see MIX_DEVIATIONS.md D1 | FAIL | routine, 0.95/0.02, T3-noattr, primary cell: 56.6 min / 81.0% against E2's 58.3 / 80.4%; identical to study_minrate's own run: True |
| G1a-ii CORRECTED per D1 (E2 on its own stream) | PASS | on E2's own stream: 58.3 min / 80.4% against E2's 58.3 / 80.4%; new code path identical to the old: True |
| G1b default arm = registered tool_shipped rows | PASS | 100 visits x 2 worlds: the default arm's rows are identical to the registered run's tool_shipped rows |

## S1: the 18 synthetic cells (8 rooms per handler), mixture minus default

| tier | policy | IMPROVES | NEITHER | TRADE | WORSE | accuracy LESS | safety REGRESSION | faster / slower | harm cells | cell-mean min (default -> mix) | accuracy | wrong-and-confident |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T3-noattr | tool_joint | 0 | 8 | 0 | 10 | 0 | 0 | 0 / 10 | **10** | 62.7 -> 66.5 | 68.3% -> 67.8% | 2.20% -> 2.42% |
| T3-noattr | tool_ticket_memo2 | 0 | 18 | 0 | 0 | 0 | 0 | 0 / 0 | **0** | 60.4 -> 60.0 | 67.6% -> 66.5% | 2.77% -> 2.42% |
| T3 | tool_joint | 0 | 9 | 0 | 9 | 0 | 0 | 0 / 9 | **9** | 58.9 -> 62.4 | 69.3% -> 68.9% | 2.52% -> 2.69% |
| T3 | tool_ticket_memo2 | 0 | 18 | 0 | 0 | 0 | 0 | 0 / 0 | **0** | 54.7 -> 54.5 | 68.4% -> 67.6% | 3.00% -> 2.67% |

## S2: bldg11 (largest handler AHU06, 49 rooms; handlers {'AHU05': 34, 'AHU06': 49}; checks supported by its real point map: 28)

### W0

| arm | accuracy | wrong-and-confident | not concluded | false shared-cause call | minutes / visit | shared-cause complaints | local, in shared visits | local, in local visits | documentation-wrong |
|---|---|---|---|---|---|---|---|---|---|
| default | 50.7% (45-56) | 0.5% (0-1) | 88.0% (85-90) | 0.0% (0-0) | 291 (280-302) | 0.0% (0-0) | 78.2% (68-87) | 75.0% (70-80) | 61.4% (47-75) |
| adjusted | 74.7% (71-78) | 7.5% (5-10) | 59.2% (52-66) | 13.2% (9-18) | 180 (157-205) | 94.5% (88-100) | 35.6% (25-46) | 74.7% (70-80) | 47.7% (33-62) |
| mix | 74.8% (71-78) | 6.8% (5-9) | 56.8% (51-63) | 12.2% (8-17) | 194 (172-218) | 92.5% (85-99) | 39.6% (30-50) | 75.0% (70-80) | 52.3% (37-67) |

### W1

| arm | accuracy | wrong-and-confident | not concluded | false shared-cause call | minutes / visit | shared-cause complaints | local, in shared visits | local, in local visits | documentation-wrong |
|---|---|---|---|---|---|---|---|---|---|
| default | 32.8% (28-38) | 2.3% (1-4) | 91.8% (90-94) | 0.0% (0-0) | 286 (275-297) | 0.0% (0-0) | 48.5% (38-59) | 49.3% (43-55) | 20.5% (9-33) |
| adjusted | 55.3% (50-60) | 10.5% (7-14) | 64.2% (57-71) | 17.2% (12-24) | 187 (161-212) | 84.4% (75-93) | 25.7% (17-35) | 46.0% (40-52) | 15.9% (5-27) |
| mix | 54.7% (50-60) | 8.3% (6-11) | 64.0% (57-71) | 14.2% (10-20) | 205 (182-229) | 78.4% (67-89) | 27.7% (19-37) | 48.0% (42-54) | 15.9% (5-27) |

| world | a - b | accuracy (points) | minutes / visit |
|---|---|---|---|
| W0 | mix-default | +24.2 (+18 to +30) | -97 (-120 to -74) |
| W0 | mix-adjusted | +0.2 (-1 to +1) | +14 (+7 to +21) |
| W1 | mix-default | +21.8 (+16 to +28) | -81 (-105 to -59) |
| W1 | mix-adjusted | -0.7 (-3 to +1) | +18 (+9 to +27) |

## S3: bldg18 (largest handler AHU01, 67 rooms; handlers {'AHU01': 67, 'AHU02': 39, 'AHU03': 28, 'AHU04': 3, 'AHU05': 7}; checks supported by its real point map: 25)

### W0

| arm | accuracy | wrong-and-confident | not concluded | false shared-cause call | minutes / visit | shared-cause complaints | local, in shared visits | local, in local visits | documentation-wrong |
|---|---|---|---|---|---|---|---|---|---|
| default | 47.0% (41-53) | 1.0% (0-2) | 86.8% (84-90) | 0.0% (0-0) | 309 (297-321) | 0.0% (0-0) | 67.3% (58-76) | 71.3% (66-77) | 61.1% (44-78) |
| mix | 71.5% (67-76) | 5.0% (3-7) | 68.5% (62-74) | 8.7% (5-13) | 205 (183-227) | 85.9% (77-94) | 45.5% (35-57) | 70.7% (65-76) | 50.0% (32-68) |

### W1

| arm | accuracy | wrong-and-confident | not concluded | false shared-cause call | minutes / visit | shared-cause complaints | local, in shared visits | local, in local visits | documentation-wrong |
|---|---|---|---|---|---|---|---|---|---|
| default | 30.0% (26-34) | 5.2% (3-7) | 85.8% (83-88) | 0.5% (0-2) | 316 (305-327) | 0.0% (0-0) | 45.5% (36-55) | 44.7% (40-50) | 11.1% (0-24) |
| mix | 48.0% (43-53) | 7.8% (5-10) | 72.7% (67-78) | 8.2% (5-12) | 241 (218-264) | 61.3% (48-74) | 31.7% (22-43) | 44.7% (39-50) | 8.3% (0-21) |

| world | a - b | accuracy (points) | minutes / visit |
|---|---|---|---|
| W0 | mix-default | +24.5 (+18 to +31) | -104 (-129 to -79) |
| W1 | mix-default | +18.0 (+12 to +24) | -75 (-99 to -52) |

## S3: bldg8 (largest handler AHU01, 24 rooms; handlers {'AHU01': 24}; checks supported by its real point map: 28)

### W0

| arm | accuracy | wrong-and-confident | not concluded | false shared-cause call | minutes / visit | shared-cause complaints | local, in shared visits | local, in local visits | documentation-wrong |
|---|---|---|---|---|---|---|---|---|---|
| default | 69.3% (66-73) | 18.7% (14-23) | 41.2% (33-50) | 29.4% (21-38) | 141 (113-169) | 100.0% (100-100) | 1.0% (0-3) | 72.0% (66-78) | 36.8% (21-52) |
| mix | 68.7% (65-72) | 18.2% (14-22) | 42.2% (34-51) | 29.9% (22-39) | 142 (114-170) | 100.0% (100-100) | 1.0% (0-3) | 70.7% (64-77) | 36.8% (21-52) |

### W1

| arm | accuracy | wrong-and-confident | not concluded | false shared-cause call | minutes / visit | shared-cause complaints | local, in shared visits | local, in local visits | documentation-wrong |
|---|---|---|---|---|---|---|---|---|---|
| default | 50.7% (46-56) | 22.7% (18-28) | 43.5% (36-53) | 37.9% (29-47) | 136 (111-165) | 98.5% (96-100) | 2.0% (0-5) | 35.3% (29-41) | 10.5% (0-22) |
| mix | 49.3% (44-54) | 21.5% (16-27) | 45.7% (37-55) | 40.9% (32-50) | 133 (108-162) | 99.0% (97-100) | 2.0% (0-5) | 32.3% (27-38) | 10.5% (0-22) |

| world | a - b | accuracy (points) | minutes / visit |
|---|---|---|---|
| W0 | mix-default | -0.7 (-3 to +1) | +1 (-3 to +4) |
| W1 | mix-default | -1.3 (-3 to -0) | -4 (-8 to +1) |

## Predictions (registered before the run)

| # | prediction | result | detail |
|---|---|---|---|
| P1 | S1 tool_joint, T3-noattr: mixture is a HARM cell in at most 1 of 18 | DOES NOT HOLD | 10 harm cells (WORSE 10, accuracy LESS 0, safety REGRESSION 0) |
| P2 | S1 same: NEITHER in at least 12 of 18 | DOES NOT HOLD | NEITHER 8, IMPROVES 0, TRADE 0, WORSE 10 |
| P3 | S1 same: cell-mean accuracy within 1 point and minutes within 5% of default | DOES NOT HOLD | accuracy 68.3% -> 67.8%, minutes 62.7 -> 66.5 (+6.0%) |
| P4 | S2 W0: mix accuracy within 3 points of adjusted and at least 15 above default | HOLDS | mix 74.8%, adjusted 74.7%, default 50.7% |
| P5 | S2 W0: mix accuracy on shared-cause complaints at least 80% | HOLDS | 92.5% |
| P6 | S2 W0: mix minutes at most default's and within 15% of adjusted's | HOLDS | mix 194, default 291, adjusted 180 |
| P7 | S2: mix still fails the safety bar (wrong-and-confident above 5% at W0 or above 10% at W1) | HOLDS | W0 6.8%, W1 8.3% |
| P8 | S3 bldg18 W0: mix accuracy at least 5 points above default | HOLDS | +24.5 points (+18.0 to +30.8) |
| P9 | S3 bldg8 W0: mix accuracy at least 5 points above default | DOES NOT HOLD | -0.7 points (-2.5 to +0.5) |
| P10 | no S2/S3 building loses more than 3 points of accuracy (either world) | HOLDS | smallest change -1.3 points (bldg8, W1) |
| P11 | no S2/S3 building takes more minutes per visit (either world) | DOES NOT HOLD | largest change +1 min (bldg8, W0) |
