# A confirm step by a visit to the air handler (exploratory; FANCONF2_NOTES.md hashed before any run; demos, pilot and shipped defaults untouched)

Simulated causes and answers (the visit families are mine); real Mortar layouts for A-LS, A-FAN and B, the first demo's synthetic 3 x 8 building for S1-S4. W0 = checks as the tool assumes, W1 = every rate 25% toward 0.5. TODAY = low-static mixture 5/15/50/90%; FAN = TODAY + fan-off mixture; FANV = FAN + one visit to the air handler (`ahu_visit`: 19 minutes in the catalogue; abnormal 0.92 under fan off, 0.10 under low static) before an upstream conclusion; FANO = FANV only when the other of fan off / low static still has at least 5%. 'asks/visit' = confirm visits per visit. Nothing committed or deployed.

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
- G2 the confirm replica with the step switched off equals run_ticket_v on 160 visit-world-setting runs: identical: **PASS**
- G3 composition: **PASS** (A-LS bldg11: 200 visits as stated; A-LS bldg15: 200 visits as stated; A-LS bldg9: 200 visits as stated; A-FAN bldg11: 200 visits as stated; A-FAN bldg15: 200 visits as stated; A-FAN bldg9: 200 visits as stated; B bldg15: 100 visits as stated; B bldg11: 100 visits as stated; S1 demo: 100 visits as stated; S2 demo: 100 visits as stated; S3 demo: 100 visits as stated; S4 demo: 100 visits as stated)
- G4 126 room questions of an A-FAN visit forward and backward: identical; 3 air-handler questions answered in vocabulary: **PASS**
- G5 `ahu_visit` in every check list; FANV asked it in every required family (A-LS bldg11 42, A-LS bldg15 17, A-LS bldg9 37, A-FAN bldg11 16, A-FAN bldg15 15, A-FAN bldg9 8, S3 demo 77 confirm visits in W0); at most once per handler per visit; never after it was answered: **PASS**

## A-LS: 4 low-static rooms on the larger handler + 2 own-fault rooms

| building | answers | arm | accuracy | shared-cause rooms | minutes / visit | asks / visit | wrong and confident | with the hedge | false fan-off | fan-off rooms called fan off | vs TODAY: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bldg11 | W0 | TODAY | 84.4% | 91.8% | 188 | 0.00 | 0.1% | 0.1% | 0.0% | - |  |
| bldg11 | W0 | FAN | 79.2% | 84.0% | 195 | 0.00 | 0.1% | 0.1% | 5.2% | - | -5.2 (-7.7, -2.8); +7 (+5, +10) |
| bldg11 | W0 | FANV | 79.1% | 83.8% | 195 | 0.21 | 0.1% | 0.1% | 5.3% | - | -5.3 (-7.9, -2.9); +7 (+5, +10) |
| bldg11 | W0 | FANO | 79.1% | 83.8% | 195 | 0.18 | 0.1% | 0.1% | 5.3% | - | -5.3 (-7.9, -2.9); +7 (+5, +10) |
| bldg11 | W1 | TODAY | 60.9% | 74.8% | 205 | 0.00 | 2.0% | 2.0% | 0.0% | - |  |
| bldg11 | W1 | FAN | 50.0% | 58.2% | 212 | 0.00 | 1.9% | 1.9% | 10.8% | - | -10.9 (-14.0, -7.8); +7 (+3, +11) |
| bldg11 | W1 | FANV | 49.2% | 57.1% | 212 | 0.15 | 2.0% | 2.0% | 11.5% | - | -11.7 (-14.9, -8.4); +7 (+3, +10) |
| bldg11 | W1 | FANO | 49.2% | 57.1% | 212 | 0.14 | 2.0% | 2.0% | 11.5% | - | -11.7 (-14.9, -8.4); +7 (+3, +10) |
| bldg15 | W0 | TODAY | 75.2% | 78.8% | 239 | 0.00 | 0.1% | 0.1% | 0.0% | - |  |
| bldg15 | W0 | FAN | 71.2% | 72.8% | 227 | 0.00 | 0.0% | 0.0% | 6.2% | - | -4.0 (-6.8, -1.3); -12 (-16, -8) |
| bldg15 | W0 | FANV | 71.2% | 72.8% | 227 | 0.09 | 0.0% | 0.0% | 6.2% | - | -4.0 (-6.8, -1.3); -12 (-16, -8) |
| bldg15 | W0 | FANO | 71.2% | 72.8% | 227 | 0.07 | 0.0% | 0.0% | 6.2% | - | -4.0 (-6.8, -1.3); -12 (-16, -9) |
| bldg15 | W1 | TODAY | 48.5% | 56.6% | 245 | 0.00 | 2.2% | 2.2% | 0.0% | - |  |
| bldg15 | W1 | FAN | 42.4% | 47.5% | 239 | 0.00 | 2.0% | 2.0% | 8.3% | - | -6.1 (-9.2, -3.0); -6 (-11, -1) |
| bldg15 | W1 | FANV | 42.2% | 47.1% | 239 | 0.07 | 2.0% | 2.0% | 8.7% | - | -6.3 (-9.5, -3.2); -6 (-11, -2) |
| bldg15 | W1 | FANO | 42.2% | 47.1% | 239 | 0.06 | 2.0% | 2.0% | 8.7% | - | -6.3 (-9.5, -3.2); -6 (-11, -2) |
| bldg9 | W0 | TODAY | 81.1% | 85.8% | 207 | 0.00 | 0.3% | 0.3% | 0.0% | - |  |
| bldg9 | W0 | FAN | 77.8% | 80.9% | 209 | 0.00 | 0.2% | 0.2% | 4.4% | - | -3.2 (-5.8, -1.0); +2 (-1, +5) |
| bldg9 | W0 | FANV | 77.5% | 80.4% | 209 | 0.18 | 0.2% | 0.2% | 4.6% | - | -3.6 (-6.2, -1.2); +3 (-1, +6) |
| bldg9 | W0 | FANO | 77.5% | 80.4% | 209 | 0.14 | 0.2% | 0.2% | 4.6% | - | -3.6 (-6.2, -1.2); +3 (-1, +6) |
| bldg9 | W1 | TODAY | 51.0% | 59.1% | 237 | 0.00 | 2.3% | 2.3% | 0.0% | - |  |
| bldg9 | W1 | FAN | 45.3% | 50.6% | 239 | 0.00 | 2.3% | 2.3% | 6.2% | - | -5.7 (-8.3, -3.3); +2 (-2, +5) |
| bldg9 | W1 | FANV | 44.9% | 50.0% | 239 | 0.16 | 2.2% | 2.2% | 6.8% | - | -6.1 (-8.8, -3.5); +1 (-2, +4) |
| bldg9 | W1 | FANO | 44.8% | 49.8% | 239 | 0.10 | 2.3% | 2.3% | 6.8% | - | -6.2 (-8.9, -3.7); +2 (-2, +5) |

## A-FAN: 4 fan-off rooms on the larger handler + 2 own-fault rooms

| building | answers | arm | accuracy | shared-cause rooms | minutes / visit | asks / visit | wrong and confident | with the hedge | false fan-off | fan-off rooms called fan off | vs TODAY: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bldg11 | W0 | TODAY | 23.2% | 0.0% | 174 | 0.00 | 58.8% | 13.4% | 0.0% | 0% |  |
| bldg11 | W0 | FAN | 80.4% | 85.8% | 178 | 0.00 | 3.3% | 0.8% | 0.0% | 86% | +57.2 (+54.1, +60.0); +4 (+1, +5) |
| bldg11 | W0 | FANV | 81.5% | 87.4% | 178 | 0.08 | 3.4% | 0.9% | 0.0% | 87% | +58.2 (+55.1, +61.1); +3 (+1, +5) |
| bldg11 | W0 | FANO | 81.5% | 87.4% | 178 | 0.07 | 3.4% | 0.9% | 0.0% | 87% | +58.2 (+55.1, +61.1); +4 (+1, +5) |
| bldg11 | W1 | TODAY | 11.1% | 0.0% | 194 | 0.00 | 48.6% | 12.7% | 0.0% | 0% |  |
| bldg11 | W1 | FAN | 53.2% | 63.0% | 194 | 0.00 | 6.2% | 2.3% | 0.0% | 63% | +42.1 (+37.8, +45.8); +1 (-2, +4) |
| bldg11 | W1 | FANV | 54.4% | 64.9% | 194 | 0.10 | 6.5% | 2.8% | 0.0% | 65% | +43.3 (+38.9, +47.2); +0 (-3, +3) |
| bldg11 | W1 | FANO | 54.4% | 64.9% | 194 | 0.09 | 6.5% | 2.8% | 0.0% | 65% | +43.3 (+38.9, +47.2); +0 (-3, +3) |
| bldg15 | W0 | TODAY | 22.8% | 0.0% | 227 | 0.00 | 8.1% | 0.1% | 0.0% | 0% |  |
| bldg15 | W0 | FAN | 72.7% | 74.9% | 214 | 0.00 | 1.6% | 1.6% | 0.0% | 75% | +49.9 (+46.2, +53.2); -12 (-14, -10) |
| bldg15 | W0 | FANV | 73.8% | 76.5% | 214 | 0.07 | 1.6% | 1.6% | 0.0% | 76% | +51.0 (+47.2, +54.5); -13 (-15, -11) |
| bldg15 | W0 | FANO | 73.8% | 76.5% | 214 | 0.07 | 1.6% | 1.6% | 0.0% | 76% | +51.0 (+47.2, +54.5); -13 (-15, -11) |
| bldg15 | W1 | TODAY | 10.8% | 0.0% | 237 | 0.00 | 10.3% | 1.8% | 0.0% | 0% |  |
| bldg15 | W1 | FAN | 43.9% | 49.8% | 230 | 0.00 | 3.3% | 3.2% | 0.0% | 50% | +33.2 (+29.2, +37.0); -7 (-11, -4) |
| bldg15 | W1 | FANV | 44.8% | 51.1% | 230 | 0.06 | 3.3% | 3.2% | 0.0% | 51% | +34.1 (+30.0, +38.0); -8 (-12, -4) |
| bldg15 | W1 | FANO | 44.8% | 51.1% | 230 | 0.06 | 3.3% | 3.2% | 0.0% | 51% | +34.1 (+30.0, +38.0); -8 (-12, -4) |
| bldg9 | W0 | TODAY | 23.9% | 0.0% | 190 | 0.00 | 13.2% | 7.2% | 0.0% | 0% |  |
| bldg9 | W0 | FAN | 78.0% | 81.1% | 199 | 0.00 | 4.2% | 1.3% | 0.0% | 81% | +54.1 (+50.7, +57.2); +10 (+8, +12) |
| bldg9 | W0 | FANV | 78.3% | 81.6% | 199 | 0.04 | 4.2% | 1.3% | 0.0% | 82% | +54.4 (+51.0, +57.6); +10 (+8, +12) |
| bldg9 | W0 | FANO | 78.3% | 81.6% | 199 | 0.02 | 4.2% | 1.3% | 0.0% | 82% | +54.4 (+51.0, +57.6); +10 (+8, +12) |
| bldg9 | W1 | TODAY | 11.6% | 0.0% | 224 | 0.00 | 15.6% | 8.4% | 0.0% | 0% |  |
| bldg9 | W1 | FAN | 46.8% | 52.8% | 225 | 0.00 | 7.1% | 3.4% | 0.0% | 53% | +35.2 (+31.0, +39.3); +1 (-2, +4) |
| bldg9 | W1 | FANV | 48.0% | 54.6% | 225 | 0.08 | 7.2% | 3.4% | 0.0% | 55% | +36.4 (+32.2, +40.6); +1 (-3, +4) |
| bldg9 | W1 | FANO | 48.0% | 54.6% | 225 | 0.07 | 7.2% | 3.5% | 0.0% | 55% | +36.4 (+32.2, +40.6); +1 (-2, +4) |

## B: registered composition (50 shared / 50 local visits)

| building | answers | arm | accuracy | shared-cause rooms | minutes / visit | asks / visit | wrong and confident | with the hedge | false fan-off | fan-off rooms called fan off | vs TODAY: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bldg15 | W0 | TODAY | 70.5% | 85.9% | 205 | 0.00 | 4.0% | 0.2% | 0.0% | - |  |
| bldg15 | W0 | FAN | 67.2% | 76.9% | 205 | 0.00 | 5.2% | 0.2% | 4.0% | - | -3.3 (-6.5, -0.8); -0 (-2, +2) |
| bldg15 | W0 | FANV | 66.8% | 75.9% | 204 | 0.06 | 5.0% | 0.0% | 4.7% | - | -3.7 (-7.2, -0.8); -1 (-3, +1) |
| bldg15 | W0 | FANO | 66.8% | 75.9% | 204 | 0.06 | 5.0% | 0.0% | 4.7% | - | -3.7 (-7.2, -0.8); -1 (-3, +1) |
| bldg15 | W1 | TODAY | 55.0% | 74.4% | 213 | 0.00 | 4.8% | 2.0% | 0.0% | - |  |
| bldg15 | W1 | FAN | 48.5% | 54.8% | 214 | 0.00 | 4.8% | 2.3% | 8.2% | - | -6.5 (-10.3, -2.8); +1 (-4, +6) |
| bldg15 | W1 | FANV | 47.5% | 51.8% | 214 | 0.08 | 4.8% | 2.3% | 9.2% | - | -7.5 (-11.7, -3.5); +1 (-4, +6) |
| bldg15 | W1 | FANO | 47.5% | 51.8% | 214 | 0.07 | 4.8% | 2.3% | 9.2% | - | -7.5 (-11.7, -3.5); +1 (-4, +6) |
| bldg11 | W0 | TODAY | 74.8% | 92.5% | 194 | 0.00 | 6.8% | 0.2% | 0.0% | - |  |
| bldg11 | W0 | FAN | 71.5% | 84.4% | 188 | 0.00 | 5.0% | 0.2% | 4.8% | - | -3.3 (-7.0, +0.2); -5 (-12, +0) |
| bldg11 | W0 | FANV | 71.3% | 84.4% | 188 | 0.14 | 5.2% | 0.3% | 5.0% | - | -3.5 (-7.2, -0.2); -5 (-13, +0) |
| bldg11 | W0 | FANO | 71.3% | 84.4% | 188 | 0.14 | 5.2% | 0.3% | 5.0% | - | -3.5 (-7.2, -0.2); -5 (-13, +0) |
| bldg11 | W1 | TODAY | 54.7% | 78.4% | 205 | 0.00 | 8.3% | 1.5% | 0.0% | - |  |
| bldg11 | W1 | FAN | 50.5% | 65.8% | 200 | 0.00 | 4.5% | 1.2% | 6.5% | - | -4.2 (-7.8, -1.0); -5 (-10, +1) |
| bldg11 | W1 | FANV | 50.2% | 65.3% | 199 | 0.10 | 4.8% | 1.2% | 6.7% | - | -4.5 (-8.3, -1.2); -5 (-11, +0) |
| bldg11 | W1 | FANO | 50.2% | 65.3% | 199 | 0.09 | 4.8% | 1.2% | 6.7% | - | -4.5 (-8.3, -1.2); -6 (-12, -0) |

## S1: fan off, the model's own world (each of 8 rooms complains at 90%)

| building | answers | arm | accuracy | shared-cause rooms | minutes / visit | asks / visit | wrong and confident | with the hedge | false fan-off | fan-off rooms called fan off | vs TODAY: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| demo | W0 | TODAY | 90.2% | 90.2% | 3 | 0.00 | 0.0% | 0.0% | 0.0% | 90% |  |
| demo | W0 | FAN | 87.3% | 87.3% | 19 | 0.00 | 8.9% | 0.0% | 0.0% | 87% | -2.9 (-6.6, +0.0); +16 (+15, +17) |
| demo | W0 | FANV | 87.3% | 87.3% | 21 | 0.10 | 1.1% | 0.0% | 0.0% | 87% | -2.9 (-6.6, +0.0); +18 (+17, +19) |
| demo | W0 | FANO | 87.3% | 87.3% | 19 | 0.00 | 8.9% | 0.0% | 0.0% | 87% | -2.9 (-6.6, +0.0); +16 (+15, +17) |
| demo | W1 | TODAY | 75.7% | 75.7% | 3 | 0.00 | 0.0% | 0.0% | 0.0% | 76% |  |
| demo | W1 | FAN | 59.3% | 59.3% | 17 | 0.00 | 24.3% | 0.0% | 0.0% | 59% | -16.5 (-24.2, -9.4); +13 (+12, +15) |
| demo | W1 | FANV | 59.3% | 59.3% | 21 | 0.24 | 5.3% | 0.0% | 0.0% | 59% | -16.5 (-24.2, -9.4); +18 (+17, +19) |
| demo | W1 | FANO | 59.3% | 59.3% | 17 | 0.00 | 24.3% | 0.0% | 0.0% | 59% | -16.5 (-24.2, -9.4); +13 (+12, +15) |

## S2: fan off, 2-4 of 8 rooms complain + 2 own-fault rooms

| building | answers | arm | accuracy | shared-cause rooms | minutes / visit | asks / visit | wrong and confident | with the hedge | false fan-off | fan-off rooms called fan off | vs TODAY: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| demo | W0 | TODAY | 29.9% | 0.0% | 113 | 0.00 | 56.7% | 6.8% | 0.0% | 0% |  |
| demo | W0 | FAN | 82.8% | 88.6% | 125 | 0.00 | 1.8% | 0.2% | 0.0% | 89% | +52.9 (+48.6, +56.7); +13 (+10, +15) |
| demo | W0 | FANV | 83.0% | 89.0% | 126 | 0.06 | 0.8% | 0.2% | 0.0% | 89% | +53.1 (+48.9, +56.8); +14 (+11, +16) |
| demo | W0 | FANO | 83.0% | 89.0% | 125 | 0.01 | 1.8% | 0.2% | 0.0% | 89% | +53.1 (+48.9, +56.8); +13 (+10, +15) |
| demo | W1 | TODAY | 19.2% | 0.0% | 119 | 0.00 | 51.9% | 7.6% | 0.0% | 0% |  |
| demo | W1 | FAN | 57.5% | 64.5% | 125 | 0.00 | 7.0% | 1.2% | 0.0% | 65% | +38.3 (+32.2, +43.6); +6 (+2, +10) |
| demo | W1 | FANV | 57.7% | 64.9% | 129 | 0.20 | 4.2% | 1.8% | 0.0% | 65% | +38.5 (+32.4, +43.8); +10 (+5, +14) |
| demo | W1 | FANO | 57.7% | 64.9% | 125 | 0.02 | 7.0% | 1.2% | 0.0% | 65% | +38.5 (+32.4, +43.8); +6 (+2, +10) |

## S3: low static, 2-4 of 8 rooms + 2 own-fault rooms

| building | answers | arm | accuracy | shared-cause rooms | minutes / visit | asks / visit | wrong and confident | with the hedge | false fan-off | fan-off rooms called fan off | vs TODAY: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| demo | W0 | TODAY | 90.0% | 97.3% | 110 | 0.00 | 0.2% | 0.2% | 0.0% | - |  |
| demo | W0 | FAN | 88.4% | 94.6% | 114 | 0.00 | 0.6% | 0.6% | 0.8% | - | -1.6 (-3.2, -0.4); +4 (+2, +6) |
| demo | W0 | FANV | 88.4% | 94.6% | 129 | 0.77 | 0.6% | 0.6% | 0.8% | - | -1.6 (-3.2, -0.4); +18 (+16, +20) |
| demo | W0 | FANO | 88.4% | 94.6% | 114 | 0.00 | 0.6% | 0.6% | 0.8% | - | -1.6 (-3.2, -0.4); +4 (+2, +6) |
| demo | W1 | TODAY | 73.3% | 95.7% | 120 | 0.00 | 3.2% | 2.4% | 0.0% | - |  |
| demo | W1 | FAN | 67.9% | 86.3% | 126 | 0.00 | 2.0% | 2.0% | 5.8% | - | -5.4 (-9.1, -1.7); +6 (+2, +9) |
| demo | W1 | FANV | 67.9% | 86.3% | 141 | 0.68 | 3.0% | 2.6% | 5.8% | - | -5.4 (-9.1, -1.7); +20 (+15, +25) |
| demo | W1 | FANO | 67.9% | 86.3% | 126 | 0.01 | 2.0% | 2.0% | 5.8% | - | -5.4 (-9.1, -1.7); +6 (+2, +9) |

## S4: 6 own-fault rooms, no shared cause

| building | answers | arm | accuracy | shared-cause rooms | minutes / visit | asks / visit | wrong and confident | with the hedge | false fan-off | fan-off rooms called fan off | vs TODAY: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| demo | W0 | TODAY | 75.2% | nan% | 289 | 0.00 | 2.3% | 0.3% | 0.0% | - |  |
| demo | W0 | FAN | 74.8% | nan% | 289 | 0.00 | 0.2% | 0.2% | 0.0% | - | -0.3 (-1.0, +0.3); +0 (-2, +2) |
| demo | W0 | FANV | 75.2% | nan% | 291 | 0.05 | 1.2% | 0.2% | 0.0% | - | +0.0 (-0.8, +1.0); +2 (-1, +6) |
| demo | W0 | FANO | 74.8% | nan% | 289 | 0.00 | 0.2% | 0.2% | 0.0% | - | -0.3 (-1.0, +0.3); +0 (-2, +2) |
| demo | W1 | TODAY | 41.5% | nan% | 277 | 0.00 | 12.5% | 4.5% | 0.0% | - |  |
| demo | W1 | FAN | 40.7% | nan% | 278 | 0.00 | 5.3% | 4.0% | 0.5% | - | -0.8 (-1.8, +0.0); +1 (-2, +6) |
| demo | W1 | FANV | 40.8% | nan% | 283 | 0.22 | 9.0% | 4.2% | 0.5% | - | -0.7 (-1.7, +0.3); +6 (+2, +11) |
| demo | W1 | FANO | 40.7% | nan% | 278 | 0.01 | 5.8% | 4.0% | 0.5% | - | -0.8 (-1.8, +0.0); +1 (-2, +6) |

## Predictions for FANV (written before any run)

- V1 (A-LS: false fan-off at most 2% and accuracy within 3 points of TODAY): **FAILED** (bldg11 false 5.3%, -5.3, bldg15 false 6.2%, -4.0, bldg9 false 4.6%, -3.6)
- V2 (A-FAN: fan-off rooms at least FAN's minus 2): **HELD** (bldg11 87.4% vs FAN 85.8%, bldg15 76.5% vs FAN 74.9%, bldg9 81.6% vs FAN 81.1%)
- V3 (B, S3, S4: within 2 points of TODAY, wrong-and-confident at most +1): **FAILED** (B bldg15 -3.7, wc +1.0, B bldg11 -3.5, wc -1.7, S3 demo -1.6, wc +0.4, S4 demo +0.0, wc -1.2)
- V4 (S1: within 3 points of TODAY): **HELD** (-2.9 (-6.6, +0.0); minutes +18 on 3)
- V5 (minutes within +10% of TODAY in A-LS and B): **HELD** (A-LS bldg11 +7 (+4%), A-LS bldg15 -12 (-5%), A-LS bldg9 +3 (+1%), B bldg15 -1 (-0%), B bldg11 -5 (-3%))

## The same predictions for FANO (V1-V5), and V6

- V1: **FAILED** (bldg11 false 5.3%, -5.3, bldg15 false 6.2%, -4.0, bldg9 false 4.6%, -3.6)
- V2: **HELD** (bldg11 87.4% vs FAN 85.8%, bldg15 76.5% vs FAN 74.9%, bldg9 81.6% vs FAN 81.1%)
- V3: **FAILED** (B bldg15 -3.7, wc +1.0, B bldg11 -3.5, wc -1.7, S3 demo -1.6, wc +0.4, S4 demo -0.3, wc -2.2)
- V4: **HELD** (-2.9 (-6.6, +0.0); minutes +16 on 3)
- V5: **HELD** (A-LS bldg11 +7 (+4%), A-LS bldg15 -12 (-5%), A-LS bldg9 +3 (+1%), B bldg15 -1 (-0%), B bldg11 -5 (-3%))
- V6: **FAILED** (false fan-off FAN 5.3%, FANV 5.4%, FANO 5.4% (FANO removes nan% as many as FANV); extra minutes over FAN: FANV +0, FANO +0 (97% of FANV's))

## Decision rule applied

- FANV: **NOT WORTH IT AS TESTED (V1, V3 failed)**
- FANO: **NOT WORTH IT AS TESTED (V1, V3, V6 failed)**
