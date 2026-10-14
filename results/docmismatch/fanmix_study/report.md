# A fan-off mixture and a lower end for the low-static mixture (exploratory; FANMIX_NOTES.md hashed before any run; demos, pilot and shipped defaults untouched)

Simulated causes and answers (the visit families are mine); real Mortar layouts for A-LS, A-FAN and B, the first demo's synthetic 3 x 8 building for S1-S4. W0 = checks as the tool assumes, W1 = every rate 25% toward 0.5. Arms: TODAY = low-static mixture 5/15/50/90%; FAN = TODAY + fan-off mixture 5/15/50/90%; LOW2 = low-static mixture 2/5/15/50/90%; BOTH. Nothing committed or deployed.

## Gates

- G1 TODAY on A-LS reproduces the stored mixed row, bldg11 W0: **PASS** (84.4% / 188 min; stored 84.4% / 188)
- G1 TODAY on A-LS reproduces the stored mixed row, bldg11 W1: **PASS** (60.9% / 205 min; stored 60.9% / 205)
- G1 TODAY on A-LS reproduces the stored mixed row, bldg15 W0: **PASS** (75.2% / 239 min; stored 75.2% / 239)
- G1 TODAY on A-LS reproduces the stored mixed row, bldg15 W1: **PASS** (48.5% / 245 min; stored 48.5% / 245)
- G1 TODAY on A-LS reproduces the stored mixed row, bldg9 W0: **PASS** (81.1% / 207 min; stored 81.1% / 207)
- G1 TODAY on A-LS reproduces the stored mixed row, bldg9 W1: **PASS** (51.0% / 237 min; stored 51.0% / 237)
- G2 a one-level fan mixture at 0.9 gives TODAY's guesses, conclusions and minutes on 60 visit-world runs: identical: **PASS**
- G3 composition: **PASS** (A-LS bldg11: 200 visits as stated; A-LS bldg15: 200 visits as stated; A-LS bldg9: 200 visits as stated; A-FAN bldg11: 200 visits as stated; A-FAN bldg15: 200 visits as stated; A-FAN bldg9: 200 visits as stated; B bldg15: 100 visits as stated; B bldg11: 100 visits as stated; S1 demo: 100 visits as stated; S2 demo: 100 visits as stated; S3 demo: 100 visits as stated; S4 demo: 100 visits as stated)
- G4 126 room questions of an A-FAN visit forward and backward: identical; 3 air-handler questions answered in vocabulary: **PASS**
- G5 fan-off prior at 4 complaints of 49 rooms (bldg11): TODAY 7.25e-42, FAN 1.19e-02: **PASS**

## A-LS: 4 low-static rooms on the larger handler + 2 own-fault rooms

| building | answers | arm | accuracy | shared-cause rooms | own-fault rooms | minutes / visit | wrong and confident | with the hedge | false fan-off | shared-cause rooms called fan off / low static | vs TODAY: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bldg11 | W0 | TODAY | 84.4% | 91.8% | 69.8% | 188 | 0.1% | 0.1% | 0.0% | - |  |
| bldg11 | W0 | FAN | 79.2% | 84.0% | 69.8% | 195 | 0.1% | 0.1% | 5.2% | - | -5.2 (-7.7, -2.8); +7 (+5, +10) |
| bldg11 | W0 | LOW2 | 84.3% | 91.8% | 69.5% | 186 | 0.1% | 0.1% | 0.0% | - | -0.1 (-0.2, +0.0); -2 (-4, -1) |
| bldg11 | W0 | BOTH | 79.2% | 84.0% | 69.5% | 193 | 0.1% | 0.1% | 5.2% | - | -5.2 (-7.8, -2.8); +5 (+2, +8) |
| bldg11 | W1 | TODAY | 60.9% | 74.8% | 33.2% | 205 | 2.0% | 2.0% | 0.0% | - |  |
| bldg11 | W1 | FAN | 50.0% | 58.2% | 33.5% | 212 | 1.9% | 1.9% | 10.8% | - | -10.9 (-14.0, -7.8); +7 (+3, +11) |
| bldg11 | W1 | LOW2 | 61.0% | 74.9% | 33.2% | 202 | 2.0% | 2.0% | 0.0% | - | +0.1 (-0.2, +0.3); -3 (-5, -1) |
| bldg11 | W1 | BOTH | 50.2% | 58.8% | 33.2% | 209 | 1.8% | 1.8% | 10.8% | - | -10.7 (-13.9, -7.5); +4 (+1, +8) |
| bldg15 | W0 | TODAY | 75.2% | 78.8% | 68.2% | 239 | 0.1% | 0.1% | 0.0% | - |  |
| bldg15 | W0 | FAN | 71.2% | 72.8% | 68.2% | 227 | 0.0% | 0.0% | 6.2% | - | -4.0 (-6.8, -1.3); -12 (-16, -8) |
| bldg15 | W0 | LOW2 | 78.3% | 83.8% | 67.5% | 214 | 0.1% | 0.1% | 0.0% | - | +3.1 (+1.8, +4.6); -25 (-28, -21) |
| bldg15 | W0 | BOTH | 72.8% | 75.4% | 67.5% | 218 | 0.0% | 0.0% | 6.0% | - | -2.5 (-5.3, +0.2); -21 (-25, -17) |
| bldg15 | W1 | TODAY | 48.5% | 56.6% | 32.2% | 245 | 2.2% | 2.2% | 0.0% | - |  |
| bldg15 | W1 | FAN | 42.4% | 47.5% | 32.2% | 239 | 2.0% | 2.0% | 8.3% | - | -6.1 (-9.2, -3.0); -6 (-11, -1) |
| bldg15 | W1 | LOW2 | 53.6% | 64.2% | 32.2% | 223 | 2.0% | 2.0% | 0.0% | - | +5.1 (+3.2, +7.0); -22 (-27, -18) |
| bldg15 | W1 | BOTH | 46.8% | 54.0% | 32.2% | 227 | 1.8% | 1.8% | 8.8% | - | -1.8 (-5.2, +1.5); -19 (-24, -13) |
| bldg9 | W0 | TODAY | 81.1% | 85.8% | 71.8% | 207 | 0.3% | 0.3% | 0.0% | - |  |
| bldg9 | W0 | FAN | 77.8% | 80.9% | 71.8% | 209 | 0.2% | 0.2% | 4.4% | - | -3.2 (-5.8, -1.0); +2 (-1, +5) |
| bldg9 | W0 | LOW2 | 82.8% | 88.2% | 71.8% | 197 | 0.2% | 0.2% | 0.0% | - | +1.7 (+0.9, +2.5); -10 (-13, -8) |
| bldg9 | W0 | BOTH | 79.6% | 83.5% | 71.8% | 207 | 0.2% | 0.2% | 3.5% | - | -1.5 (-3.8, +0.5); +0 (-4, +4) |
| bldg9 | W1 | TODAY | 51.0% | 59.1% | 34.8% | 237 | 2.3% | 2.3% | 0.0% | - |  |
| bldg9 | W1 | FAN | 45.3% | 50.6% | 34.8% | 239 | 2.3% | 2.3% | 6.2% | - | -5.7 (-8.3, -3.3); +2 (-2, +5) |
| bldg9 | W1 | LOW2 | 53.6% | 63.0% | 34.8% | 227 | 2.2% | 2.2% | 0.0% | - | +2.6 (+1.5, +3.8); -11 (-14, -7) |
| bldg9 | W1 | BOTH | 48.7% | 55.6% | 34.8% | 234 | 2.2% | 2.2% | 5.5% | - | -2.3 (-4.8, -0.1); -3 (-7, +1) |

## A-FAN: 4 fan-off rooms on the larger handler + 2 own-fault rooms

| building | answers | arm | accuracy | shared-cause rooms | own-fault rooms | minutes / visit | wrong and confident | with the hedge | false fan-off | shared-cause rooms called fan off / low static | vs TODAY: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bldg11 | W0 | TODAY | 23.2% | 0.0% | 69.8% | 174 | 58.8% | 13.4% | 0.0% | 0% / 93% |  |
| bldg11 | W0 | FAN | 80.4% | 85.8% | 69.8% | 178 | 3.3% | 0.8% | 0.0% | 86% / 7% | +57.2 (+54.1, +60.0); +4 (+1, +5) |
| bldg11 | W0 | LOW2 | 23.2% | 0.0% | 69.5% | 172 | 58.6% | 13.2% | 0.0% | 0% / 93% | -0.1 (-0.2, +0.0); -2 (-4, -1) |
| bldg11 | W0 | BOTH | 80.3% | 85.8% | 69.5% | 176 | 3.3% | 0.8% | 0.0% | 86% / 7% | +57.1 (+54.0, +59.8); +1 (-1, +4) |
| bldg11 | W1 | TODAY | 11.1% | 0.0% | 33.2% | 194 | 48.6% | 12.7% | 0.0% | 0% / 77% |  |
| bldg11 | W1 | FAN | 53.2% | 63.0% | 33.5% | 194 | 6.2% | 2.3% | 0.0% | 63% / 15% | +42.1 (+37.8, +45.8); +1 (-2, +4) |
| bldg11 | W1 | LOW2 | 11.1% | 0.0% | 33.2% | 190 | 48.1% | 11.9% | 0.0% | 0% / 77% | +0.0 (-0.2, +0.2); -3 (-5, -2) |
| bldg11 | W1 | BOTH | 53.1% | 63.0% | 33.2% | 192 | 6.3% | 2.4% | 0.0% | 63% / 15% | +42.0 (+37.8, +45.8); -2 (-5, +1) |
| bldg15 | W0 | TODAY | 22.8% | 0.0% | 68.2% | 227 | 8.1% | 0.1% | 0.0% | 0% / 86% |  |
| bldg15 | W0 | FAN | 72.7% | 74.9% | 68.2% | 214 | 1.6% | 1.6% | 0.0% | 75% / 13% | +49.9 (+46.2, +53.2); -12 (-14, -10) |
| bldg15 | W0 | LOW2 | 22.5% | 0.0% | 67.5% | 198 | 16.5% | 8.2% | 0.0% | 0% / 88% | -0.2 (-0.6, +0.0); -29 (-31, -26) |
| bldg15 | W0 | BOTH | 72.2% | 74.6% | 67.5% | 207 | 7.0% | 1.8% | 0.0% | 75% / 15% | +49.5 (+45.8, +52.9); -20 (-23, -17) |
| bldg15 | W1 | TODAY | 10.8% | 0.0% | 32.2% | 237 | 10.3% | 1.8% | 0.0% | 0% / 61% |  |
| bldg15 | W1 | FAN | 43.9% | 49.8% | 32.2% | 230 | 3.3% | 3.2% | 0.0% | 50% / 15% | +33.2 (+29.2, +37.0); -7 (-11, -4) |
| bldg15 | W1 | LOW2 | 10.8% | 0.0% | 32.2% | 213 | 16.7% | 7.9% | 0.0% | 0% / 67% | +0.0 (-0.3, +0.3); -24 (-29, -20) |
| bldg15 | W1 | BOTH | 45.0% | 51.4% | 32.2% | 219 | 9.2% | 3.3% | 0.0% | 51% / 19% | +34.2 (+30.2, +38.2); -18 (-23, -14) |
| bldg9 | W0 | TODAY | 23.9% | 0.0% | 71.8% | 190 | 13.2% | 7.2% | 0.0% | 0% / 89% |  |
| bldg9 | W0 | FAN | 78.0% | 81.1% | 71.8% | 199 | 4.2% | 1.3% | 0.0% | 81% / 8% | +54.1 (+50.7, +57.2); +10 (+8, +12) |
| bldg9 | W0 | LOW2 | 23.9% | 0.0% | 71.8% | 185 | 17.5% | 14.3% | 0.0% | 0% / 90% | +0.0 (+0.0, +0.0); -5 (-6, -4) |
| bldg9 | W0 | BOTH | 75.5% | 77.4% | 71.8% | 200 | 3.7% | 1.1% | 0.0% | 77% / 13% | +51.6 (+48.2, +54.7); +10 (+8, +12) |
| bldg9 | W1 | TODAY | 11.6% | 0.0% | 34.8% | 224 | 15.6% | 8.4% | 0.0% | 0% / 62% |  |
| bldg9 | W1 | FAN | 46.8% | 52.8% | 34.8% | 225 | 7.1% | 3.4% | 0.0% | 53% / 12% | +35.2 (+31.0, +39.3); +1 (-2, +4) |
| bldg9 | W1 | LOW2 | 11.6% | 0.0% | 34.8% | 215 | 15.1% | 11.6% | 0.0% | 0% / 64% | +0.0 (+0.0, +0.0); -8 (-12, -6) |
| bldg9 | W1 | BOTH | 44.5% | 49.4% | 34.8% | 221 | 6.8% | 3.2% | 0.0% | 49% / 19% | +32.9 (+29.1, +36.8); -3 (-7, +1) |

## B: registered composition (50 shared / 50 local visits)

| building | answers | arm | accuracy | shared-cause rooms | own-fault rooms | minutes / visit | wrong and confident | with the hedge | false fan-off | shared-cause rooms called fan off / low static | vs TODAY: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bldg15 | W0 | TODAY | 70.5% | 85.9% | 62.8% | 205 | 4.0% | 0.2% | 0.0% | - |  |
| bldg15 | W0 | FAN | 67.2% | 76.9% | 62.3% | 205 | 5.2% | 0.2% | 4.0% | - | -3.3 (-6.5, -0.8); -0 (-2, +2) |
| bldg15 | W0 | LOW2 | 71.2% | 88.4% | 62.6% | 203 | 4.5% | 0.2% | 0.0% | - | +0.7 (-0.5, +2.5); -2 (-6, -0) |
| bldg15 | W0 | BOTH | 68.8% | 81.9% | 62.3% | 201 | 5.3% | 0.2% | 3.7% | - | -1.7 (-5.0, +1.3); -4 (-9, -0) |
| bldg15 | W1 | TODAY | 55.0% | 74.4% | 45.4% | 213 | 4.8% | 2.0% | 0.0% | - |  |
| bldg15 | W1 | FAN | 48.5% | 54.8% | 45.4% | 214 | 4.8% | 2.3% | 8.2% | - | -6.5 (-10.3, -2.8); +1 (-4, +6) |
| bldg15 | W1 | LOW2 | 55.0% | 73.9% | 45.6% | 212 | 4.8% | 2.3% | 0.0% | - | +0.0 (-1.0, +1.2); -1 (-3, +0) |
| bldg15 | W1 | BOTH | 49.5% | 57.3% | 45.6% | 214 | 4.3% | 2.2% | 7.8% | - | -5.5 (-9.3, -1.8); +0 (-5, +5) |
| bldg11 | W0 | TODAY | 74.8% | 92.5% | 66.1% | 194 | 6.8% | 0.2% | 0.0% | - |  |
| bldg11 | W0 | FAN | 71.5% | 84.4% | 65.1% | 188 | 5.0% | 0.2% | 4.8% | - | -3.3 (-7.0, +0.2); -5 (-12, +0) |
| bldg11 | W0 | LOW2 | 73.8% | 89.9% | 65.8% | 196 | 5.8% | 0.2% | 0.0% | - | -1.0 (-2.8, +0.0); +2 (-3, +8) |
| bldg11 | W0 | BOTH | 71.5% | 84.4% | 65.1% | 189 | 4.8% | 0.2% | 4.8% | - | -3.3 (-7.0, +0.2); -5 (-12, +1) |
| bldg11 | W1 | TODAY | 54.7% | 78.4% | 42.9% | 205 | 8.3% | 1.5% | 0.0% | - |  |
| bldg11 | W1 | FAN | 50.5% | 65.8% | 42.9% | 200 | 4.5% | 1.2% | 6.5% | - | -4.2 (-7.8, -1.0); -5 (-10, +1) |
| bldg11 | W1 | LOW2 | 54.3% | 77.9% | 42.6% | 206 | 7.8% | 1.5% | 0.0% | - | -0.3 (-1.0, +0.3); +1 (-0, +3) |
| bldg11 | W1 | BOTH | 50.5% | 65.8% | 42.9% | 201 | 4.5% | 1.2% | 6.3% | - | -4.2 (-7.8, -1.0); -4 (-10, +1) |

## S1: fan off, the model's own world (each of 8 rooms complains at 90%)

| building | answers | arm | accuracy | shared-cause rooms | own-fault rooms | minutes / visit | wrong and confident | with the hedge | false fan-off | shared-cause rooms called fan off / low static | vs TODAY: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| demo | W0 | TODAY | 90.2% | 90.2% | nan% | 3 | 0.0% | 0.0% | 0.0% | 90% / 10% |  |
| demo | W0 | FAN | 87.3% | 87.3% | nan% | 19 | 8.9% | 0.0% | 0.0% | 87% / 13% | -2.9 (-6.6, +0.0); +16 (+15, +17) |
| demo | W0 | LOW2 | 90.2% | 90.2% | nan% | 3 | 0.0% | 0.0% | 0.0% | 90% / 10% | +0.0 (+0.0, +0.0); +0 (+0, +0) |
| demo | W0 | BOTH | 87.3% | 87.3% | nan% | 19 | 0.0% | 0.0% | 0.0% | 87% / 13% | -2.9 (-6.6, +0.0); +16 (+15, +17) |
| demo | W1 | TODAY | 75.7% | 75.7% | nan% | 3 | 0.0% | 0.0% | 0.0% | 76% / 24% |  |
| demo | W1 | FAN | 59.3% | 59.3% | nan% | 17 | 24.3% | 0.0% | 0.0% | 59% / 41% | -16.5 (-24.2, -9.4); +13 (+12, +15) |
| demo | W1 | LOW2 | 75.7% | 75.7% | nan% | 3 | 0.0% | 0.0% | 0.0% | 76% / 24% | +0.0 (+0.0, +0.0); +0 (+0, +0) |
| demo | W1 | BOTH | 59.3% | 59.3% | nan% | 17 | 0.0% | 0.0% | 0.0% | 59% / 41% | -16.5 (-24.2, -9.4); +13 (+12, +15) |

## S2: fan off, 2-4 of 8 rooms complain + 2 own-fault rooms

| building | answers | arm | accuracy | shared-cause rooms | own-fault rooms | minutes / visit | wrong and confident | with the hedge | false fan-off | shared-cause rooms called fan off / low static | vs TODAY: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| demo | W0 | TODAY | 29.9% | 0.0% | 74.5% | 113 | 56.7% | 6.8% | 0.0% | 0% / 100% |  |
| demo | W0 | FAN | 82.8% | 88.6% | 74.0% | 125 | 1.8% | 0.2% | 0.0% | 89% / 11% | +52.9 (+48.6, +56.7); +13 (+10, +15) |
| demo | W0 | LOW2 | 29.9% | 0.0% | 74.5% | 112 | 56.3% | 6.4% | 0.0% | 0% / 99% | +0.0 (+0.0, +0.0); -0 (-1, +0) |
| demo | W0 | BOTH | 83.0% | 89.0% | 74.0% | 126 | 0.4% | 0.2% | 0.0% | 89% / 11% | +53.1 (+48.9, +56.8); +13 (+11, +15) |
| demo | W1 | TODAY | 19.2% | 0.0% | 48.0% | 119 | 51.9% | 7.6% | 0.0% | 0% / 93% |  |
| demo | W1 | FAN | 57.5% | 64.5% | 47.0% | 125 | 7.0% | 1.2% | 0.0% | 65% / 31% | +38.3 (+32.2, +43.6); +6 (+2, +10) |
| demo | W1 | LOW2 | 19.4% | 0.0% | 48.5% | 119 | 51.9% | 7.6% | 0.0% | 0% / 93% | +0.2 (+0.0, +0.6); -0 (-2, +1) |
| demo | W1 | BOTH | 57.7% | 64.9% | 47.0% | 127 | 2.6% | 1.4% | 0.0% | 65% / 31% | +38.5 (+32.4, +43.8); +8 (+4, +12) |

## S3: low static, 2-4 of 8 rooms complain + 2 own-fault rooms

| building | answers | arm | accuracy | shared-cause rooms | own-fault rooms | minutes / visit | wrong and confident | with the hedge | false fan-off | shared-cause rooms called fan off / low static | vs TODAY: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| demo | W0 | TODAY | 90.0% | 97.3% | 79.0% | 110 | 0.2% | 0.2% | 0.0% | - |  |
| demo | W0 | FAN | 88.4% | 94.6% | 79.0% | 114 | 0.6% | 0.6% | 0.8% | - | -1.6 (-3.2, -0.4); +4 (+2, +6) |
| demo | W0 | LOW2 | 89.2% | 96.0% | 79.0% | 110 | 0.2% | 0.2% | 0.0% | - | -0.8 (-1.9, +0.0); -0 (-1, +0) |
| demo | W0 | BOTH | 88.4% | 94.6% | 79.0% | 118 | 1.0% | 1.0% | 0.8% | - | -1.6 (-3.2, -0.4); +8 (+5, +10) |
| demo | W1 | TODAY | 73.3% | 95.7% | 40.0% | 120 | 3.2% | 2.4% | 0.0% | - |  |
| demo | W1 | FAN | 67.9% | 86.3% | 40.5% | 126 | 2.0% | 2.0% | 5.8% | - | -5.4 (-9.1, -1.7); +6 (+2, +9) |
| demo | W1 | LOW2 | 72.5% | 93.3% | 41.5% | 121 | 2.8% | 2.2% | 0.0% | - | -0.8 (-2.8, +0.8); +1 (-1, +2) |
| demo | W1 | BOTH | 67.3% | 85.6% | 40.0% | 128 | 7.0% | 7.0% | 6.0% | - | -6.0 (-9.7, -2.2); +8 (+4, +11) |

## S4: 6 own-fault rooms, no shared cause

| building | answers | arm | accuracy | shared-cause rooms | own-fault rooms | minutes / visit | wrong and confident | with the hedge | false fan-off | shared-cause rooms called fan off / low static | vs TODAY: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| demo | W0 | TODAY | 75.2% | nan% | 75.2% | 289 | 2.3% | 0.3% | 0.0% | - |  |
| demo | W0 | FAN | 74.8% | nan% | 74.8% | 289 | 0.2% | 0.2% | 0.0% | - | -0.3 (-1.0, +0.3); +0 (-2, +2) |
| demo | W0 | LOW2 | 75.0% | nan% | 75.0% | 287 | 2.3% | 0.3% | 0.0% | - | -0.2 (-0.8, +0.3); -2 (-3, -1) |
| demo | W0 | BOTH | 75.0% | nan% | 75.0% | 291 | 0.2% | 0.2% | 0.0% | - | -0.2 (-1.2, +0.8); +2 (-2, +7) |
| demo | W1 | TODAY | 41.5% | nan% | 41.5% | 277 | 12.5% | 4.5% | 0.0% | - |  |
| demo | W1 | FAN | 40.7% | nan% | 40.7% | 278 | 5.3% | 4.0% | 0.5% | - | -0.8 (-1.8, +0.0); +1 (-2, +6) |
| demo | W1 | LOW2 | 41.8% | nan% | 41.8% | 278 | 12.2% | 4.5% | 0.0% | - | +0.3 (+0.0, +0.8); +1 (-2, +6) |
| demo | W1 | BOTH | 41.7% | nan% | 41.7% | 288 | 5.0% | 4.7% | 0.5% | - | +0.2 (-1.5, +1.7); +11 (+3, +20) |

## Predictions (written before any run)

- P1 (A-FAN: under TODAY the 4 fan-off rooms are right at most 20% on each building): **HELD** (bldg11 0.0%, bldg15 0.0%, bldg9 0.0%)
- P2 (A-FAN: FAN raises the fan-off rooms by at least 25 points on each building): **HELD** (bldg11 +85.8 (85.8%), bldg15 +74.9 (74.9%), bldg9 +81.1 (81.1%))
- P3 (S2: TODAY at most 20% on the fan-off rooms and FAN +25 or more): **HELD** (TODAY 0.0%, FAN +88.6 (88.6%))
- P4 (S1, the model's own world: FAN within 3 points and 5% of minutes of TODAY): **FAILED** (-2.9 points (-6.6, +0.0); +16.2 min on 3)
- P5 (harm cells: FAN within 3 points, wrong-and-confident at most +1, false fan-off at most 2%): **FAILED** (A-LS bldg11: -5.2 pts, wc +0.0, false fan-off 5.2%; A-LS bldg15: -4.0 pts, wc -0.1, false fan-off 6.2%; A-LS bldg9: -3.2 pts, wc -0.1, false fan-off 4.4%; S3 demo: -1.6 pts, wc +0.4, false fan-off 0.8%; S4 demo: -0.3 pts, wc -2.2, false fan-off 0.0%; B bldg15: -3.3 pts, wc +1.2, false fan-off 4.0%; B bldg11: -3.3 pts, wc -1.8, false fan-off 4.8%)
- P6 (W1: the fan-off gains of P2 and P3 are still at least 15 points): **HELD** (+63.0, +49.8, +52.8, +64.5)
- P7 (A-LS bldg15: LOW2 +3 or more with the CI above 0, shared rooms at least 85%): **FAILED** (+3.1 (+1.8, +4.6); shared 83.8% (TODAY 78.8%))
- P8 (A-LS bldg11, bldg9: LOW2 within 3 points of TODAY): **HELD** (bldg11 -0.1, bldg9 +1.7)
- P9 (S1-S4: LOW2 within 3 points of TODAY): **HELD** (S1 +0.0, S2 +0.0, S3 -0.8, S4 -0.2)
- P10 (B: LOW2 within 3 points of TODAY and wrong-and-confident at most +1): **HELD** (bldg15 +0.7 pts, wc +0.5, bldg11 -1.0 pts, wc -1.0)
- P11 (BOTH not more than 2 points below the better single change in A-FAN and A-LS bldg15): **FAILED** (A-FAN bldg11 -0.1, A-FAN bldg15 -0.4, A-FAN bldg9 -2.5, A-LS bldg15 -5.6)

## Decision rule applied

- FAN (fan-off mixture): **TRADES (a neutrality or harm check failed)**
- LOW2 (lower end): **NO GAIN**
