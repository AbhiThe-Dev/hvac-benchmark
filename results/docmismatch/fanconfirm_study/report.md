# A fan-status confirm step, the lower-end gaps and a hedge for fan off (exploratory; FANCONF_NOTES.md hashed before any run; demos, pilot and shipped defaults untouched)

Simulated causes and answers (the visit families are mine); real Mortar layouts for A-LS, A-FAN and B, the first demo's synthetic 3 x 8 building for S1-S4. W0 = checks as the tool assumes, W1 = every rate 25% toward 0.5. TODAY = low-static mixture 5/15/50/90%; FAN = TODAY + fan-off mixture; FANC = FAN + one fan-status read before an upstream conclusion; LOW2 = 2/5/15/50/90%; RW = the 5/15/50/90% levels with weights 40/20/20/20 (LOW2's weights without the new level). 'hedge' = low-static hedge of the pilot; 'hedge+fan' = also a fan-off conclusion with no own box-level static reading counts as not confident. Nothing committed or deployed.

## Gates

- G1 TODAY on A-LS bldg11 W0 reproduces the FANMIX study: **PASS** (84.4% / 188 min; stored 84.4% / 188)
- G1 TODAY on A-LS bldg15 W0 reproduces the FANMIX study: **PASS** (75.2% / 239 min; stored 75.2% / 239)
- G1 TODAY on A-LS bldg9 W0 reproduces the FANMIX study: **PASS** (81.1% / 207 min; stored 81.1% / 207)
- G1 FAN on A-LS bldg11 W0 reproduces the FANMIX study: **PASS** (79.2% / 195 min; stored 79.2% / 195)
- G1 FAN on A-LS bldg15 W0 reproduces the FANMIX study: **PASS** (71.2% / 227 min; stored 71.2% / 227)
- G1 FAN on A-LS bldg9 W0 reproduces the FANMIX study: **PASS** (77.8% / 209 min; stored 77.8% / 209)
- G1 FAN on A-FAN bldg11 W0 reproduces the FANMIX study: **PASS** (80.4% / 178 min; stored 80.4% / 178)
- G1 FAN on A-FAN bldg15 W0 reproduces the FANMIX study: **PASS** (72.7% / 214 min; stored 72.7% / 214)
- G1 FAN on A-FAN bldg9 W0 reproduces the FANMIX study: **PASS** (78.0% / 199 min; stored 78.0% / 199)
- G1 LOW2 on A-LS bldg11 W0 reproduces the FANMIX study: **PASS** (84.3% / 186 min; stored 84.3% / 186)
- G1 LOW2 on A-LS bldg15 W0 reproduces the FANMIX study: **PASS** (78.3% / 214 min; stored 78.3% / 214)
- G1 LOW2 on A-LS bldg9 W0 reproduces the FANMIX study: **PASS** (82.8% / 197 min; stored 82.8% / 197)
- G2 the confirm replica with the step switched off equals run_ticket_v on 160 visit-world-setting runs: identical: **PASS**
- G3 composition: **PASS** (A-LS bldg11: 200 visits as stated; A-LS bldg15: 200 visits as stated; A-LS bldg9: 200 visits as stated; A-FAN bldg11: 200 visits as stated; A-FAN bldg15: 200 visits as stated; A-FAN bldg9: 200 visits as stated; B bldg15: 100 visits as stated; B bldg11: 100 visits as stated; S1 demo: 100 visits as stated; S2 demo: 100 visits as stated; S3 demo: 100 visits as stated; S4 demo: 100 visits as stated)
- G4 126 room questions of an A-FAN visit forward and backward: identical; 3 air-handler questions answered in vocabulary: **PASS**
- G5 the confirm step asked the fan status at most once per handler per visit and never after it was answered (largest count 0, violations 0): **PASS**

## A-LS: 4 low-static rooms on the larger handler + 2 own-fault rooms

| building | answers | arm | accuracy | shared-cause rooms | minutes / visit | wrong and confident | with the hedge | with hedge+fan | right conclusions hedged | false fan-off | fan-off rooms called fan off | vs TODAY: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bldg11 | W0 | TODAY | 84.4% | 91.8% | 188 | 0.1% | 0.1% | 0.1% | 517/739 | 0.0% | - |  |
| bldg11 | W0 | FAN | 79.2% | 84.0% | 195 | 0.1% | 0.1% | 0.1% | 405/581 | 5.2% | - | -5.2 (-7.7, -2.8); +7 (+5, +10) |
| bldg11 | W0 | FANC | 79.2% | 84.0% | 195 | 0.1% | 0.1% | 0.1% | 405/581 | 5.2% | - | -5.2 (-7.7, -2.8); +7 (+5, +10) |
| bldg11 | W0 | RW | 84.2% | 92.0% | 163 | 0.1% | 0.1% | 0.1% | 550/764 | 0.0% | - | -0.2 (-0.6, +0.2); -25 (-29, -21) |
| bldg11 | W0 | LOW2 | 84.3% | 91.8% | 186 | 0.1% | 0.1% | 0.1% | 517/737 | 0.0% | - | -0.1 (-0.2, +0.0); -2 (-4, -1) |
| bldg11 | W1 | TODAY | 60.9% | 74.8% | 205 | 2.0% | 2.0% | 2.0% | 397/558 | 0.0% | - |  |
| bldg11 | W1 | FAN | 50.0% | 58.2% | 212 | 1.9% | 1.9% | 1.9% | 227/321 | 10.8% | - | -10.9 (-14.0, -7.8); +7 (+3, +11) |
| bldg11 | W1 | FANC | 50.0% | 58.2% | 212 | 1.9% | 1.9% | 1.9% | 227/321 | 10.8% | - | -10.9 (-14.0, -7.8); +7 (+3, +11) |
| bldg11 | W1 | RW | 62.0% | 76.9% | 180 | 1.8% | 1.8% | 1.8% | 450/605 | 0.0% | - | +1.1 (+0.3, +1.9); -24 (-28, -21) |
| bldg11 | W1 | LOW2 | 61.0% | 74.9% | 202 | 2.0% | 2.0% | 2.0% | 399/551 | 0.0% | - | +0.1 (-0.2, +0.3); -3 (-5, -1) |
| bldg15 | W0 | TODAY | 75.2% | 78.8% | 239 | 0.1% | 0.1% | 0.1% | 163/231 | 0.0% | - |  |
| bldg15 | W0 | FAN | 71.2% | 72.8% | 227 | 0.0% | 0.0% | 0.0% | 2/195 | 6.2% | - | -4.0 (-6.8, -1.3); -12 (-16, -8) |
| bldg15 | W0 | FANC | 71.2% | 72.8% | 227 | 0.0% | 0.0% | 0.0% | 2/195 | 6.2% | - | -4.0 (-6.8, -1.3); -12 (-16, -8) |
| bldg15 | W0 | RW | 78.0% | 83.2% | 215 | 0.1% | 0.1% | 0.1% | 203/359 | 0.0% | - | +2.8 (+1.5, +4.2); -24 (-27, -20) |
| bldg15 | W0 | LOW2 | 78.3% | 83.8% | 214 | 0.1% | 0.1% | 0.1% | 204/358 | 0.0% | - | +3.1 (+1.8, +4.6); -25 (-28, -21) |
| bldg15 | W1 | TODAY | 48.5% | 56.6% | 245 | 2.2% | 2.2% | 2.2% | 121/140 | 0.0% | - |  |
| bldg15 | W1 | FAN | 42.4% | 47.5% | 239 | 2.0% | 2.0% | 2.0% | 2/100 | 8.3% | - | -6.1 (-9.2, -3.0); -6 (-11, -1) |
| bldg15 | W1 | FANC | 42.4% | 47.5% | 239 | 2.0% | 2.0% | 2.0% | 2/100 | 8.3% | - | -6.1 (-9.2, -3.0); -6 (-11, -1) |
| bldg15 | W1 | RW | 52.9% | 63.2% | 224 | 2.0% | 2.0% | 2.0% | 146/234 | 0.0% | - | +4.4 (+2.7, +6.3); -21 (-26, -17) |
| bldg15 | W1 | LOW2 | 53.6% | 64.2% | 223 | 2.0% | 2.0% | 2.0% | 147/231 | 0.0% | - | +5.1 (+3.2, +7.0); -22 (-27, -18) |
| bldg9 | W0 | TODAY | 81.1% | 85.8% | 207 | 0.3% | 0.3% | 0.3% | 176/332 | 0.0% | - |  |
| bldg9 | W0 | FAN | 77.8% | 80.9% | 209 | 0.2% | 0.2% | 0.2% | 440/648 | 4.4% | - | -3.2 (-5.8, -1.0); +2 (-1, +5) |
| bldg9 | W0 | FANC | 77.8% | 80.9% | 209 | 0.2% | 0.2% | 0.2% | 440/648 | 4.4% | - | -3.2 (-5.8, -1.0); +2 (-1, +5) |
| bldg9 | W0 | RW | 82.8% | 88.2% | 197 | 0.2% | 0.2% | 0.2% | 101/319 | 0.0% | - | +1.7 (+0.9, +2.5); -10 (-13, -8) |
| bldg9 | W0 | LOW2 | 82.8% | 88.2% | 197 | 0.2% | 0.2% | 0.2% | 103/324 | 0.0% | - | +1.7 (+0.9, +2.5); -10 (-13, -8) |
| bldg9 | W1 | TODAY | 51.0% | 59.1% | 237 | 2.3% | 2.3% | 2.3% | 129/238 | 0.0% | - |  |
| bldg9 | W1 | FAN | 45.3% | 50.6% | 239 | 2.3% | 2.3% | 2.3% | 238/352 | 6.2% | - | -5.7 (-8.3, -3.3); +2 (-2, +5) |
| bldg9 | W1 | FANC | 45.3% | 50.6% | 239 | 2.3% | 2.3% | 2.3% | 238/352 | 6.2% | - | -5.7 (-8.3, -3.3); +2 (-2, +5) |
| bldg9 | W1 | RW | 53.8% | 63.2% | 226 | 2.2% | 2.2% | 2.2% | 68/207 | 0.0% | - | +2.8 (+1.7, +4.0); -11 (-15, -8) |
| bldg9 | W1 | LOW2 | 53.6% | 63.0% | 227 | 2.2% | 2.2% | 2.2% | 70/213 | 0.0% | - | +2.6 (+1.5, +3.8); -11 (-14, -7) |

## A-FAN: 4 fan-off rooms on the larger handler + 2 own-fault rooms

| building | answers | arm | accuracy | shared-cause rooms | minutes / visit | wrong and confident | with the hedge | with hedge+fan | right conclusions hedged | false fan-off | fan-off rooms called fan off | vs TODAY: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bldg11 | W0 | TODAY | 23.2% | 0.0% | 174 | 58.8% | 13.4% | 13.4% | 0/69 | 0.0% | 0% |  |
| bldg11 | W0 | FAN | 80.4% | 85.8% | 178 | 3.3% | 0.8% | 0.8% | 0/69 | 0.0% | 86% | +57.2 (+54.1, +60.0); +4 (+1, +5) |
| bldg11 | W0 | FANC | 80.4% | 85.8% | 178 | 3.3% | 0.8% | 0.8% | 0/69 | 0.0% | 86% | +57.2 (+54.1, +60.0); +4 (+1, +5) |
| bldg11 | W0 | RW | 22.9% | 0.0% | 159 | 59.6% | 13.3% | 13.3% | 0/69 | 0.0% | 0% | -0.3 (-0.7, -0.1); -16 (-19, -13) |
| bldg11 | W0 | LOW2 | 23.2% | 0.0% | 172 | 58.6% | 13.2% | 13.2% | 0/69 | 0.0% | 0% | -0.1 (-0.2, +0.0); -2 (-4, -1) |
| bldg11 | W1 | TODAY | 11.1% | 0.0% | 194 | 48.6% | 12.7% | 12.7% | 0/28 | 0.0% | 0% |  |
| bldg11 | W1 | FAN | 53.2% | 63.0% | 194 | 6.2% | 2.3% | 2.3% | 0/28 | 0.0% | 63% | +42.1 (+37.8, +45.8); +1 (-2, +4) |
| bldg11 | W1 | FANC | 53.2% | 63.0% | 194 | 6.2% | 2.3% | 2.3% | 0/28 | 0.0% | 63% | +42.1 (+37.8, +45.8); +1 (-2, +4) |
| bldg11 | W1 | RW | 10.8% | 0.0% | 174 | 50.9% | 12.3% | 12.3% | 0/28 | 0.0% | 0% | -0.3 (-0.8, +0.1); -20 (-23, -17) |
| bldg11 | W1 | LOW2 | 11.1% | 0.0% | 190 | 48.1% | 11.9% | 11.9% | 0/28 | 0.0% | 0% | +0.0 (-0.2, +0.2); -3 (-5, -2) |
| bldg15 | W0 | TODAY | 22.8% | 0.0% | 227 | 8.1% | 0.1% | 0.1% | 0/66 | 0.0% | 0% |  |
| bldg15 | W0 | FAN | 72.7% | 74.9% | 214 | 1.6% | 1.6% | 1.6% | 0/66 | 0.0% | 75% | +49.9 (+46.2, +53.2); -12 (-14, -10) |
| bldg15 | W0 | FANC | 72.7% | 74.9% | 214 | 1.6% | 1.6% | 1.6% | 0/66 | 0.0% | 75% | +49.9 (+46.2, +53.2); -12 (-14, -10) |
| bldg15 | W0 | RW | 22.5% | 0.0% | 199 | 16.2% | 8.2% | 8.2% | 0/63 | 0.0% | 0% | -0.2 (-0.6, +0.0); -28 (-31, -25) |
| bldg15 | W0 | LOW2 | 22.5% | 0.0% | 198 | 16.5% | 8.2% | 8.2% | 0/63 | 0.0% | 0% | -0.2 (-0.6, +0.0); -29 (-31, -26) |
| bldg15 | W1 | TODAY | 10.8% | 0.0% | 237 | 10.3% | 1.8% | 1.8% | 0/17 | 0.0% | 0% |  |
| bldg15 | W1 | FAN | 43.9% | 49.8% | 230 | 3.3% | 3.2% | 3.2% | 0/17 | 0.0% | 50% | +33.2 (+29.2, +37.0); -7 (-11, -4) |
| bldg15 | W1 | FANC | 43.9% | 49.8% | 230 | 3.3% | 3.2% | 3.2% | 0/17 | 0.0% | 50% | +33.2 (+29.2, +37.0); -7 (-11, -4) |
| bldg15 | W1 | RW | 10.8% | 0.0% | 213 | 16.9% | 8.2% | 8.2% | 0/15 | 0.0% | 0% | +0.0 (-0.3, +0.3); -24 (-28, -20) |
| bldg15 | W1 | LOW2 | 10.8% | 0.0% | 213 | 16.7% | 7.9% | 7.9% | 0/15 | 0.0% | 0% | +0.0 (-0.3, +0.3); -24 (-29, -20) |
| bldg9 | W0 | TODAY | 23.9% | 0.0% | 190 | 13.2% | 7.2% | 7.2% | 0/79 | 0.0% | 0% |  |
| bldg9 | W0 | FAN | 78.0% | 81.1% | 199 | 4.2% | 1.3% | 1.3% | 0/79 | 0.0% | 81% | +54.1 (+50.7, +57.2); +10 (+8, +12) |
| bldg9 | W0 | FANC | 78.0% | 81.1% | 199 | 4.2% | 1.3% | 1.3% | 0/79 | 0.0% | 81% | +54.1 (+50.7, +57.2); +10 (+8, +12) |
| bldg9 | W0 | RW | 23.9% | 0.0% | 185 | 17.3% | 14.2% | 14.2% | 0/79 | 0.0% | 0% | +0.0 (+0.0, +0.0); -5 (-6, -4) |
| bldg9 | W0 | LOW2 | 23.9% | 0.0% | 185 | 17.5% | 14.3% | 14.3% | 0/79 | 0.0% | 0% | +0.0 (+0.0, +0.0); -5 (-6, -4) |
| bldg9 | W1 | TODAY | 11.6% | 0.0% | 224 | 15.6% | 8.4% | 8.4% | 0/36 | 0.0% | 0% |  |
| bldg9 | W1 | FAN | 46.8% | 52.8% | 225 | 7.1% | 3.4% | 3.4% | 0/34 | 0.0% | 53% | +35.2 (+31.0, +39.3); +1 (-2, +4) |
| bldg9 | W1 | FANC | 46.8% | 52.8% | 225 | 7.1% | 3.4% | 3.4% | 0/34 | 0.0% | 53% | +35.2 (+31.0, +39.3); +1 (-2, +4) |
| bldg9 | W1 | RW | 11.6% | 0.0% | 215 | 14.8% | 11.4% | 11.4% | 0/34 | 0.0% | 0% | +0.0 (+0.0, +0.0); -9 (-12, -6) |
| bldg9 | W1 | LOW2 | 11.6% | 0.0% | 215 | 15.1% | 11.6% | 11.6% | 0/34 | 0.0% | 0% | +0.0 (+0.0, +0.0); -8 (-12, -6) |

## B: registered composition (50 shared / 50 local visits)

| building | answers | arm | accuracy | shared-cause rooms | minutes / visit | wrong and confident | with the hedge | with hedge+fan | right conclusions hedged | false fan-off | fan-off rooms called fan off | vs TODAY: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bldg15 | W0 | TODAY | 70.5% | 85.9% | 205 | 4.0% | 0.2% | 0.2% | 79/163 | 0.0% | - |  |
| bldg15 | W0 | FAN | 67.2% | 76.9% | 205 | 5.2% | 0.2% | 0.2% | 84/166 | 4.0% | - | -3.3 (-6.5, -0.8); -0 (-2, +2) |
| bldg15 | W0 | FANC | 67.2% | 76.9% | 205 | 5.2% | 0.2% | 0.2% | 84/166 | 4.0% | - | -3.3 (-6.5, -0.8); -0 (-2, +2) |
| bldg15 | W0 | RW | 70.8% | 89.4% | 194 | 5.5% | 0.0% | 0.0% | 100/187 | 0.0% | - | +0.3 (-1.0, +2.2); -12 (-18, -6) |
| bldg15 | W0 | LOW2 | 71.2% | 88.4% | 203 | 4.5% | 0.2% | 0.2% | 91/179 | 0.0% | - | +0.7 (-0.5, +2.5); -2 (-6, -0) |
| bldg15 | W1 | TODAY | 55.0% | 74.4% | 213 | 4.8% | 2.0% | 2.0% | 75/132 | 0.0% | - |  |
| bldg15 | W1 | FAN | 48.5% | 54.8% | 214 | 4.8% | 2.3% | 2.3% | 56/112 | 8.2% | - | -6.5 (-10.3, -2.8); +1 (-4, +6) |
| bldg15 | W1 | FANC | 48.5% | 54.8% | 214 | 4.8% | 2.3% | 2.3% | 56/112 | 8.2% | - | -6.5 (-10.3, -2.8); +1 (-4, +6) |
| bldg15 | W1 | RW | 55.2% | 74.9% | 203 | 5.8% | 2.2% | 2.2% | 82/148 | 0.0% | - | +0.2 (-1.0, +1.3); -10 (-17, -5) |
| bldg15 | W1 | LOW2 | 55.0% | 73.9% | 212 | 4.8% | 2.3% | 2.3% | 75/138 | 0.0% | - | +0.0 (-1.0, +1.2); -1 (-3, +0) |
| bldg11 | W0 | TODAY | 74.8% | 92.5% | 194 | 6.8% | 0.2% | 0.2% | 126/218 | 0.0% | - |  |
| bldg11 | W0 | FAN | 71.5% | 84.4% | 188 | 5.0% | 0.2% | 0.2% | 86/149 | 4.8% | - | -3.3 (-7.0, +0.2); -5 (-12, +0) |
| bldg11 | W0 | FANC | 71.5% | 84.4% | 188 | 5.0% | 0.2% | 0.2% | 86/149 | 4.8% | - | -3.3 (-7.0, +0.2); -5 (-12, +0) |
| bldg11 | W0 | RW | 76.0% | 96.5% | 186 | 7.0% | 0.2% | 0.2% | 130/224 | 0.0% | - | +1.2 (+0.0, +3.2); -8 (-14, -3) |
| bldg11 | W0 | LOW2 | 73.8% | 89.9% | 196 | 5.8% | 0.2% | 0.2% | 93/184 | 0.0% | - | -1.0 (-2.8, +0.0); +2 (-3, +8) |
| bldg11 | W1 | TODAY | 54.7% | 78.4% | 205 | 8.3% | 1.5% | 1.5% | 108/166 | 0.0% | - |  |
| bldg11 | W1 | FAN | 50.5% | 65.8% | 200 | 4.5% | 1.2% | 1.2% | 46/78 | 6.5% | - | -4.2 (-7.8, -1.0); -5 (-10, +1) |
| bldg11 | W1 | FANC | 50.5% | 65.8% | 200 | 4.5% | 1.2% | 1.2% | 46/78 | 6.5% | - | -4.2 (-7.8, -1.0); -5 (-10, +1) |
| bldg11 | W1 | RW | 55.5% | 80.4% | 200 | 8.7% | 1.5% | 1.5% | 112/170 | 0.0% | - | +0.8 (+0.0, +1.7); -5 (-9, -1) |
| bldg11 | W1 | LOW2 | 54.3% | 77.9% | 206 | 7.8% | 1.5% | 1.5% | 85/145 | 0.0% | - | -0.3 (-1.0, +0.3); +1 (-0, +3) |

## S1: fan off, the model's own world (each of 8 rooms complains at 90%)

| building | answers | arm | accuracy | shared-cause rooms | minutes / visit | wrong and confident | with the hedge | with hedge+fan | right conclusions hedged | false fan-off | fan-off rooms called fan off | vs TODAY: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| demo | W0 | TODAY | 90.2% | 90.2% | 3 | 0.0% | 0.0% | 0.0% | 0/0 | 0.0% | 90% |  |
| demo | W0 | FAN | 87.3% | 87.3% | 19 | 8.9% | 0.0% | 0.0% | 0/0 | 0.0% | 87% | -2.9 (-6.6, +0.0); +16 (+15, +17) |
| demo | W0 | FANC | 87.3% | 87.3% | 19 | 8.9% | 0.0% | 0.0% | 0/0 | 0.0% | 87% | -2.9 (-6.6, +0.0); +16 (+15, +17) |
| demo | W0 | RW | 90.2% | 90.2% | 3 | 0.0% | 0.0% | 0.0% | 0/0 | 0.0% | 90% | +0.0 (+0.0, +0.0); +0 (+0, +0) |
| demo | W0 | LOW2 | 90.2% | 90.2% | 3 | 0.0% | 0.0% | 0.0% | 0/0 | 0.0% | 90% | +0.0 (+0.0, +0.0); +0 (+0, +0) |
| demo | W1 | TODAY | 75.7% | 75.7% | 3 | 0.0% | 0.0% | 0.0% | 0/0 | 0.0% | 76% |  |
| demo | W1 | FAN | 59.3% | 59.3% | 17 | 24.3% | 0.0% | 0.0% | 0/0 | 0.0% | 59% | -16.5 (-24.2, -9.4); +13 (+12, +15) |
| demo | W1 | FANC | 59.3% | 59.3% | 17 | 24.3% | 0.0% | 0.0% | 0/0 | 0.0% | 59% | -16.5 (-24.2, -9.4); +13 (+12, +15) |
| demo | W1 | RW | 75.7% | 75.7% | 3 | 0.0% | 0.0% | 0.0% | 0/0 | 0.0% | 76% | +0.0 (+0.0, +0.0); +0 (+0, +0) |
| demo | W1 | LOW2 | 75.7% | 75.7% | 3 | 0.0% | 0.0% | 0.0% | 0/0 | 0.0% | 76% | +0.0 (+0.0, +0.0); +0 (+0, +0) |

## S2: fan off, 2-4 of 8 rooms complain + 2 own-fault rooms

| building | answers | arm | accuracy | shared-cause rooms | minutes / visit | wrong and confident | with the hedge | with hedge+fan | right conclusions hedged | false fan-off | fan-off rooms called fan off | vs TODAY: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| demo | W0 | TODAY | 29.9% | 0.0% | 113 | 56.7% | 6.8% | 6.8% | 0/43 | 0.0% | 0% |  |
| demo | W0 | FAN | 82.8% | 88.6% | 125 | 1.8% | 0.2% | 0.2% | 25/68 | 0.0% | 89% | +52.9 (+48.6, +56.7); +13 (+10, +15) |
| demo | W0 | FANC | 82.8% | 88.6% | 125 | 1.8% | 0.2% | 0.2% | 25/68 | 0.0% | 89% | +52.9 (+48.6, +56.7); +13 (+10, +15) |
| demo | W0 | RW | 29.9% | 0.0% | 113 | 56.3% | 6.4% | 6.4% | 0/43 | 0.0% | 0% | +0.0 (+0.0, +0.0); +0 (+0, +0) |
| demo | W0 | LOW2 | 29.9% | 0.0% | 112 | 56.3% | 6.4% | 6.4% | 0/41 | 0.0% | 0% | +0.0 (+0.0, +0.0); -0 (-1, +0) |
| demo | W1 | TODAY | 19.2% | 0.0% | 119 | 51.9% | 7.6% | 7.6% | 0/27 | 0.0% | 0% |  |
| demo | W1 | FAN | 57.5% | 64.5% | 125 | 7.0% | 1.2% | 1.2% | 18/45 | 0.0% | 65% | +38.3 (+32.2, +43.6); +6 (+2, +10) |
| demo | W1 | FANC | 57.5% | 64.5% | 125 | 7.0% | 1.2% | 1.2% | 18/45 | 0.0% | 65% | +38.3 (+32.2, +43.6); +6 (+2, +10) |
| demo | W1 | RW | 19.2% | 0.0% | 119 | 51.9% | 7.6% | 7.6% | 0/27 | 0.0% | 0% | +0.0 (+0.0, +0.0); -0 (-1, +0) |
| demo | W1 | LOW2 | 19.4% | 0.0% | 119 | 51.9% | 7.6% | 7.6% | 0/26 | 0.0% | 0% | +0.2 (+0.0, +0.6); -0 (-2, +1) |

## S3: low static, 2-4 of 8 rooms + 2 own-fault rooms

| building | answers | arm | accuracy | shared-cause rooms | minutes / visit | wrong and confident | with the hedge | with hedge+fan | right conclusions hedged | false fan-off | fan-off rooms called fan off | vs TODAY: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| demo | W0 | TODAY | 90.0% | 97.3% | 110 | 0.2% | 0.2% | 0.2% | 252/322 | 0.0% | - |  |
| demo | W0 | FAN | 88.4% | 94.6% | 114 | 0.6% | 0.6% | 0.2% | 105/147 | 0.8% | - | -1.6 (-3.2, -0.4); +4 (+2, +6) |
| demo | W0 | FANC | 88.4% | 94.6% | 114 | 0.6% | 0.6% | 0.2% | 105/147 | 0.8% | - | -1.6 (-3.2, -0.4); +4 (+2, +6) |
| demo | W0 | RW | 90.0% | 97.3% | 110 | 0.2% | 0.2% | 0.2% | 252/319 | 0.0% | - | +0.0 (+0.0, +0.0); +0 (+0, +0) |
| demo | W0 | LOW2 | 89.2% | 96.0% | 110 | 0.2% | 0.2% | 0.2% | 252/316 | 0.0% | - | -0.8 (-1.9, +0.0); -0 (-1, +0) |
| demo | W1 | TODAY | 73.3% | 95.7% | 120 | 3.2% | 2.4% | 2.4% | 230/283 | 0.0% | - |  |
| demo | W1 | FAN | 67.9% | 86.3% | 126 | 2.0% | 2.0% | 1.8% | 94/120 | 5.8% | - | -5.4 (-9.1, -1.7); +6 (+2, +9) |
| demo | W1 | FANC | 67.9% | 86.3% | 126 | 2.0% | 2.0% | 1.8% | 94/120 | 5.8% | - | -5.4 (-9.1, -1.7); +6 (+2, +9) |
| demo | W1 | RW | 72.3% | 94.0% | 121 | 3.2% | 2.4% | 2.4% | 229/273 | 0.0% | - | -1.0 (-2.6, +0.0); +1 (+0, +2) |
| demo | W1 | LOW2 | 72.5% | 93.3% | 121 | 2.8% | 2.2% | 2.2% | 229/274 | 0.0% | - | -0.8 (-2.8, +0.8); +1 (-1, +2) |

## S4: 6 own-fault rooms, no shared cause

| building | answers | arm | accuracy | shared-cause rooms | minutes / visit | wrong and confident | with the hedge | with hedge+fan | right conclusions hedged | false fan-off | fan-off rooms called fan off | vs TODAY: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| demo | W0 | TODAY | 75.2% | nan% | 289 | 2.3% | 0.3% | 0.3% | 0/101 | 0.0% | - |  |
| demo | W0 | FAN | 74.8% | nan% | 289 | 0.2% | 0.2% | 0.2% | 0/96 | 0.0% | - | -0.3 (-1.0, +0.3); +0 (-2, +2) |
| demo | W0 | FANC | 74.8% | nan% | 289 | 0.2% | 0.2% | 0.2% | 0/96 | 0.0% | - | -0.3 (-1.0, +0.3); +0 (-2, +2) |
| demo | W0 | RW | 75.0% | nan% | 287 | 2.3% | 0.3% | 0.3% | 0/97 | 0.0% | - | -0.2 (-0.5, +0.0); -2 (-3, -1) |
| demo | W0 | LOW2 | 75.0% | nan% | 287 | 2.3% | 0.3% | 0.3% | 0/96 | 0.0% | - | -0.2 (-0.8, +0.3); -2 (-3, -1) |
| demo | W1 | TODAY | 41.5% | nan% | 277 | 12.5% | 4.5% | 4.5% | 0/57 | 0.0% | - |  |
| demo | W1 | FAN | 40.7% | nan% | 278 | 5.3% | 4.0% | 4.0% | 0/54 | 0.5% | - | -0.8 (-1.8, +0.0); +1 (-2, +6) |
| demo | W1 | FANC | 40.7% | nan% | 278 | 5.3% | 4.0% | 4.0% | 0/54 | 0.5% | - | -0.8 (-1.8, +0.0); +1 (-2, +6) |
| demo | W1 | RW | 41.8% | nan% | 279 | 12.2% | 4.5% | 4.5% | 0/55 | 0.0% | - | +0.3 (+0.0, +0.8); +2 (-1, +6) |
| demo | W1 | LOW2 | 41.8% | nan% | 278 | 12.2% | 4.5% | 4.5% | 0/55 | 0.0% | - | +0.3 (+0.0, +0.8); +1 (-2, +6) |

## Predictions (written before any run)

- C1 (A-LS: FANC false fan-off at most 2% and accuracy within 3 points of TODAY): **FAILED** (bldg11 false 5.2%, -5.2, bldg15 false 6.2%, -4.0, bldg9 false 4.4%, -3.2)
- C2 (A-FAN: FANC's fan-off rooms at least 80% of FAN's): **HELD** (bldg11 85.8% vs 85.8%, bldg15 74.9% vs 74.9%, bldg9 81.1% vs 81.1%)
- C3 (B, S3, S4: FANC within 2 points of TODAY, wrong-and-confident at most +1): **FAILED** (B bldg15 -3.3, wc +1.2, B bldg11 -3.3, wc -1.8, S3 demo -1.6, wc +0.4, S4 demo -0.3, wc -2.2)
- C4 (S1, the model's own world: FANC within 3 points of TODAY): **HELD** (-2.9 (-6.6, +0.0); minutes +16 on 3)
- C5 (minutes under FANC within +5% of TODAY in A-LS and B): **HELD** (A-LS bldg11 +7 (+4%), A-LS bldg15 -12 (-5%), A-LS bldg9 +2 (+1%), B bldg15 -0 (-0%), B bldg11 -5 (-3%))
- L1 (RW captures at least half of LOW2's bldg15 gain): **HELD** (RW +2.8, LOW2 +3.1 (89% captured))
- L2 (A-FAN: LOW2's wrong-and-confident at least 3 above TODAY's, RW's rise smaller): **HELD** (bldg15 LOW2 +8.4, RW +8.2, bldg9 LOW2 +4.3, RW +4.2)
- H1 (the extended hedge cuts the remaining wrong-and-confident by half where it is at least 1%, hedging at most 30% of right conclusions): **FAILED** (A-FAN bldg15 1.6% -> 1.6%; A-FAN bldg9 1.3% -> 1.3%; right conclusions hedged pooled 52%)

## Decision rule applied

- Fan-status confirm step: **NOT WORTH IT AS TESTED (C1, C3 failed)**
- Hedge extended to fan off: **NOT WORTH IT AS TESTED (H1 failed)**
- Lower-end gaps: reported against L1 and L2 above; they decide nothing alone.
