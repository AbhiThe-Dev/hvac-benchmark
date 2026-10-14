# Mixed against shipped on a second scenario of similar complexity (exploratory; SECOND_NOTES.md hashed before any run; no new demo or UI)

Real Mortar layouts, recorded points only; simulated causes and answers; nothing committed or deployed. W0 = checks as the tool assumes, W1 = every rate 25% toward 0.5.

| building | handlers (boxes) | boxes with airflow, damper, reheat and a zone temperature |
|---|---|---|
| bldg11 | AHU05 (34), AHU06 (49) | AHU05 30, AHU06 41 |
| bldg15 | AHU01 (43), AHU02 (86) | AHU01 3, AHU02 58 |
| bldg9 | AHU01 (56), AHU02 (70) | AHU01 28, AHU02 33 |

## Gates

- G1 bldg11, unrestricted draw, reproduces the earlier demo-shaped run, W0 shipped: **PASS** (23.8% / 332 min; earlier 23.8% / 332)
- G1 bldg11, unrestricted draw, reproduces the earlier demo-shaped run, W0 mixed: **PASS** (84.2% / 190 min; earlier 84.2% / 190)
- G1 bldg11, unrestricted draw, reproduces the earlier demo-shaped run, W1 shipped: **PASS** (11.2% / 303 min; earlier 11.2% / 303)
- G1 bldg11, unrestricted draw, reproduces the earlier demo-shaped run, W1 mixed: **PASS** (60.2% / 200 min; earlier 60.2% / 200)
- G2 every Scenario A visit: six distinct rooms, four low-static rooms on the larger handler, one actuator failure and one wrong box on the other, all with the required points: **PASS**
- G3 every answer in the check's vocabulary: asserted by the oracle

## Scenario A: demo-shaped visits (200 per building; per room unless stated)

| building | answers | setting | accuracy | the 4 shared rooms | the 2 own-fault rooms | all six right | minutes / visit | wrong and confident | with the hedge | mixed minus shipped: accuracy (95% CI), minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|
| bldg11 (restricted draw) | W0 | shipped | 23.7% | 0.0% | 71.0% | 0% | 322 | 0.2% | 0.2% |  |
| bldg11 (restricted draw) | W0 | mixed | 84.4% | 91.8% | 69.8% | 42% | 188 | 0.1% | 0.1% | +60.8 (+58.2, +62.9); -134 (-142, -127) |
| bldg11 (restricted draw) | W1 | shipped | 11.8% | 0.0% | 35.2% | 0% | 302 | 2.8% | 2.8% |  |
| bldg11 (restricted draw) | W1 | mixed | 60.9% | 74.8% | 33.2% | 7% | 205 | 2.0% | 2.0% | +49.2 (+45.7, +52.7); -97 (-106, -87) |
| bldg15 | W0 | shipped | 22.8% | 0.0% | 68.2% | 0% | 323 | 0.1% | 0.1% |  |
| bldg15 | W0 | mixed | 75.2% | 78.8% | 68.2% | 22% | 239 | 0.1% | 0.1% | +52.5 (+49.7, +55.2); -85 (-92, -77) |
| bldg15 | W1 | shipped | 10.8% | 0.0% | 32.2% | 0% | 294 | 2.4% | 2.4% |  |
| bldg15 | W1 | mixed | 48.5% | 56.6% | 32.2% | 3% | 245 | 2.2% | 2.2% | +37.8 (+33.8, +41.7); -49 (-57, -42) |
| bldg9 | W0 | shipped | 23.9% | 0.0% | 71.8% | 0% | 321 | 0.3% | 0.3% |  |
| bldg9 | W0 | mixed | 81.1% | 85.8% | 71.8% | 35% | 207 | 0.3% | 0.3% | +57.2 (+54.5, +59.7); -114 (-121, -106) |
| bldg9 | W1 | shipped | 11.6% | 0.0% | 34.8% | 0% | 300 | 2.6% | 2.6% |  |
| bldg9 | W1 | mixed | 51.0% | 59.1% | 34.8% | 4% | 237 | 2.3% | 2.3% | +39.4 (+35.8, +43.2); -63 (-72, -55) |

## Scenario B: the registered composition (100 visits per building; per room)

| building | answers | setting | accuracy | shared rooms | own fault on the faulty handler | wrong and confident | with the hedge | rooms called confident | hedged conclusions (right) | minutes / visit | mixed minus shipped: accuracy (95% CI), minutes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bldg15 | W0 | shipped | 47.5% | 0.0% | 76.2% | 0.5% | 0.5% | 10% | 0 (0) | 284 |  |
| bldg15 | W0 | mixed | 70.5% | 85.9% | 23.8% | 4.0% | 0.2% | 31% | 102 (79) | 205 | +23.0 (+17.7, +28.7); -78 |
| bldg15 | W1 | shipped | 33.7% | 0.0% | 54.0% | 2.7% | 2.7% | 9% | 0 (0) | 268 |  |
| bldg15 | W1 | mixed | 55.0% | 74.4% | 28.6% | 4.8% | 2.0% | 27% | 92 (75) | 213 | +21.3 (+15.5, +27.7); -55 |
| bldg9 | W0 | shipped | 50.0% | 0.0% | 66.7% | 0.2% | 0.2% | 11% | 0 (0) | 307 |  |
| bldg9 | W0 | mixed | 72.8% | 80.9% | 23.5% | 3.3% | 0.0% | 31% | 99 (79) | 216 | +22.8 (+16.8, +29.2); -91 |
| bldg9 | W1 | shipped | 34.2% | 0.0% | 49.0% | 3.2% | 3.2% | 11% | 0 (0) | 318 |  |
| bldg9 | W1 | mixed | 55.5% | 70.9% | 25.5% | 5.0% | 2.5% | 26% | 79 (64) | 243 | +21.3 (+15.7, +27.3); -76 |

## Predictions (written before any run)

- P1 (bldg15 A, W0: mixed beats shipped by at least 20 points per room and uses at least 20% fewer minutes): **HELD** (+52.5 points, -85 min on 323)
- P2 (bldg15 A, W0: shared rooms at least 85% under mixed, at most 10% under shipped): **FAILED** (mixed 78.8%, shipped 0.0%)
- P3 (bldg15 A, W0: the two own-fault rooms within 5 points across the settings): **HELD** (mixed 68.2%, shipped 68.2%)
- P4 (bldg15 A, W0: all six right in at least 25% of visits under mixed, at most 5% under shipped): **FAILED** (mixed 22%, shipped 0%)
- P5 (bldg15 B, W0: mixed beats shipped by at least 10 points, wrong-and-confident at least 3 points higher, at most 1.5% with the hedge): **HELD** (+23.0 points; wrong-and-confident 0.5% to 4.0%; hedged 0.2%)
- P6 (bldg9 agrees in sign with bldg15 on P1 and P5): **HELD** (A +57.2 points; B +22.8 points, wrong-and-confident 0.2% to 3.3%)
- P7 (bldg11 restricted draw within 5 points of the unrestricted 84.2% mixed and 23.8% shipped, W0): **HELD** (mixed 84.4%, shipped 23.7%)
