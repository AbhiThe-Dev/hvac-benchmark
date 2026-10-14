# bldg11 scenario: 100-visit simulation (SIM_PROTOCOL.md)

Layout and point map real (Mortar bldg11, AHU06 and AHU05); visits, causes and answers simulated by me. **W0 is home-field for the tool** (answers drawn from the catalogue's own rates), so a good W0 number is weak evidence; **W1** moves every response probability 25% toward 0.5. The stand-ins are my constructions. Minutes are placeholders. 95% intervals are a bootstrap over visits. Nothing here validates the tool or the `r_low = 0.10` setting.

100 visits x 6 complaints = 600 complaints per row. Run 2026-10-11, 3 s.

## Gates

| gate | result | detail |
|---|---|---|
| G1 harness = demo | PASS | shipped: same trace, 219.0 min (demo 219.0, want 219.0); adjusted: same trace, 119.0 min (demo 119.0, want 119.0) |
| G2a oracle order-independent | PASS | 126 questions asked forward and backward gave identical answers |
| G3 composition | PASS | 100 visits: six distinct rooms each; shared visits k in 3..5 all on AHU06; local visits none |
| G4 completeness | PASS | 1200 of 1200 (visit, world, policy) runs, minutes finite: True |
| G5 answers in vocabulary | PASS | asserted on every draw |
| G2b run twice identical | PASS | visits 0, 1, 2, 50, 51: every world and policy |

## World W0 (the tool's own rates)

| policy | accuracy | wrong-and-confident | not concluded | false shared-cause call | minutes / visit | checks / visit |
|---|---|---|---|---|---|---|
| tool_shipped | 50.7% (45-56) | 0.5% (0-1) | 88.0% (85-90) | 0.0% (0-0) | 291 (280-302) | 49 (48-50) |
| tool_adjusted | 74.7% (71-78) | 7.5% (5-10) | 59.2% (52-66) | 13.2% (9-18) | 180 (157-205) | 32 (28-36) |
| tool_r0.25 (exploratory) | 67.7% (63-72) | 6.0% (4-8) | 63.8% (57-70) | 9.7% (6-14) | 219 (197-241) | 37 (34-41) |
| tool_r0.05 (exploratory) | 76.0% (73-79) | 6.0% (4-8) | 59.7% (54-66) | 12.2% (8-17) | 187 (166-209) | 34 (31-37) |
| fast_ticket | 32.2% (28-37) | 67.8% (63-72) | n/a (always concludes) | 0.0% (0-0) | 503 (464-541) | 57 (53-60) |
| fast_parent | 53.5% (48-58) | 46.5% (42-52) | n/a (always concludes) | 13.2% (8-18) | 261 (222-304) | 31 (26-36) |

Accuracy by segment (W0):

| policy | shared-cause complaints | local, in shared visits | local, in local visits | documentation-wrong | shared-cause complaints called low static |
|---|---|---|---|---|---|
| tool_shipped | 0.0% (0-0) | 78.2% (68-87) | 75.0% (70-80) | 61.4% (47-75) | 0.0% (0-0) |
| tool_adjusted | 94.5% (88-100) | 35.6% (25-46) | 74.7% (70-80) | 47.7% (33-62) | 94.5% (88-100) |
| tool_r0.25 | 67.8% (56-80) | 46.5% (35-58) | 74.7% (70-80) | 50.0% (35-64) | 67.8% (56-80) |
| tool_r0.05 | 96.0% (90-100) | 38.6% (29-49) | 75.3% (70-80) | 50.0% (35-65) | 96.0% (90-100) |
| fast_ticket | 0.0% (0-0) | 42.6% (32-53) | 50.0% (45-54) | 34.1% (20-48) | 0.0% (0-0) |
| fast_parent | 77.9% (66-89) | 22.8% (14-32) | 47.7% (42-52) | 25.0% (13-38) | 77.9% (66-89) |

## World W1 (checks less reliable than the tool assumes)

| policy | accuracy | wrong-and-confident | not concluded | false shared-cause call | minutes / visit | checks / visit |
|---|---|---|---|---|---|---|
| tool_shipped | 32.8% (28-38) | 2.3% (1-4) | 91.8% (90-94) | 0.0% (0-0) | 286 (275-297) | 48 (47-49) |
| tool_adjusted | 55.3% (50-60) | 10.5% (7-14) | 64.2% (57-71) | 17.2% (12-24) | 187 (161-212) | 33 (29-37) |
| tool_r0.25 (exploratory) | 50.2% (45-55) | 8.3% (6-11) | 68.8% (62-76) | 11.5% (7-16) | 217 (194-239) | 37 (34-40) |
| tool_r0.05 (exploratory) | 55.3% (50-60) | 7.8% (6-10) | 66.3% (60-72) | 14.0% (10-19) | 201 (179-224) | 35 (32-39) |
| fast_ticket | 20.2% (16-24) | 79.8% (76-84) | n/a (always concludes) | 0.0% (0-0) | 224 (203-246) | 31 (29-33) |
| fast_parent | 32.5% (27-38) | 67.5% (62-73) | n/a (always concludes) | 23.7% (17-31) | 133 (109-158) | 17 (14-20) |

Accuracy by segment (W1):

| policy | shared-cause complaints | local, in shared visits | local, in local visits | documentation-wrong | shared-cause complaints called low static |
|---|---|---|---|---|---|
| tool_shipped | 0.0% (0-0) | 48.5% (38-59) | 49.3% (43-55) | 20.5% (9-33) | 0.0% (0-0) |
| tool_adjusted | 84.4% (75-93) | 25.7% (17-35) | 46.0% (40-52) | 15.9% (5-27) | 84.4% (75-93) |
| tool_r0.25 | 61.8% (49-75) | 33.7% (24-44) | 48.0% (42-53) | 15.9% (5-27) | 61.8% (49-75) |
| tool_r0.05 | 80.9% (69-91) | 28.7% (20-38) | 47.3% (41-53) | 15.9% (5-27) | 80.9% (69-91) |
| fast_ticket | 0.0% (0-0) | 26.7% (19-35) | 31.3% (25-37) | 6.8% (0-15) | 0.0% (0-0) |
| fast_parent | 61.8% (48-77) | 9.9% (4-17) | 20.7% (16-26) | 4.5% (0-12) | 61.8% (48-77) |

## Paired differences (same visits, same answers; a minus b)

| world | a - b | accuracy (points) | minutes / visit |
|---|---|---|---|
| W0 | adj-ship | +24.0 (+18 to +30) | -111 (-135 to -86) |
| W0 | adj-fast_ticket | +42.5 (+37 to +48) | -323 (-378 to -270) |
| W0 | adj-fast_parent | +21.2 (+16 to +26) | -81 (-109 to -56) |
| W0 | ship-fast_ticket | +18.5 (+14 to +23) | -212 (-248 to -176) |
| W1 | adj-ship | +22.5 (+16 to +29) | -99 (-125 to -74) |
| W1 | adj-fast_ticket | +35.2 (+29 to +41) | -37 (-71 to -2) |
| W1 | adj-fast_parent | +22.8 (+18 to +28) | +54 (+32 to +76) |
| W1 | ship-fast_ticket | +12.7 (+9 to +16) | +62 (+39 to +84) |

## Predictions (registered before the run)

| # | prediction | result | detail |
|---|---|---|---|
| P1 | W0: adjusted exceeds shipped by >= 15 points overall, interval lower bound above 0 | HOLDS | difference 24.0 points (18.2 to 29.5) |
| P2 | W0 shared-cause complaints: shipped < 30% and adjusted > 80% | HOLDS | shipped 0%, adjusted 94% |
| P3 | W0: adjusted false shared-cause call rate <= 3% | DOES NOT HOLD | 13.2% (8.6 to 18.1) |
| P4 | SAFETY BAR: adjusted wrong-and-confident <= 5% at W0 and <= 10% at W1 | DOES NOT HOLD | W0 7.5% (5.0 to 10.0), W1 10.5% (7.3 to 13.8) |
| P5 | adjusted accuracy at W1 is at least 3 points below W0 | HOLDS | W0 74.7%, W1 55.3% |
| P6 | W0: adjusted mean visit minutes below fast_ticket's | HOLDS | adjusted 180, fast_ticket 503 |
| P7 | W0: adjusted overall accuracy between 65% and 90% | HOLDS | 74.7% |

Safety bar (P4): **UNSAFE** for `tool_adjusted`.
