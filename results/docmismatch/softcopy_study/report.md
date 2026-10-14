# A softer copy between rooms (exploratory; SOFTCOPY_NOTES.md hashed before any run; demos, pilot and shipped defaults untouched)

Simulated causes and answers (the visit families are mine); real Mortar layouts for A-LS, A-FAN and B, the first demo's synthetic 3 x 8 building for S1-S5. W0 = checks as the tool assumes, W1 = every rate 25% toward 0.5. HARD = today's routine (zero-minute certain copies); SOFT = the joint model's belief replaces the copies; JOINT = SOFT with the joint belief also inside a room's own session. Limit: an own-fault room on a low-static handler reads NORMAL static at its own box in this simulation (answers come from its own cause), so any gain that comes from a room taking its own reading is an upper bound. Nothing committed or deployed.

## Gates

- G1 HARD on A-LS reproduces the stored mixed row, bldg11 W0: **PASS** (84.4% / 188 min; stored 84.4% / 188)
- G1 HARD on A-LS reproduces the stored mixed row, bldg11 W1: **PASS** (60.9% / 205 min; stored 60.9% / 205)
- G1 HARD on A-LS reproduces the stored mixed row, bldg15 W0: **PASS** (75.2% / 239 min; stored 75.2% / 239)
- G1 HARD on A-LS reproduces the stored mixed row, bldg15 W1: **PASS** (48.5% / 245 min; stored 48.5% / 245)
- G1 HARD on A-LS reproduces the stored mixed row, bldg9 W0: **PASS** (81.1% / 207 min; stored 81.1% / 207)
- G1 HARD on A-LS reproduces the stored mixed row, bldg9 W1: **PASS** (51.0% / 237 min; stored 51.0% / 237)
- G2 SOFT equals HARD (guesses, conclusions, minutes) on 80 single-complaint visit-world runs: identical: **PASS**
- G3 composition: **PASS** (A-LS bldg11: 200 visits as stated; A-LS bldg15: 200 visits as stated; A-LS bldg9: 200 visits as stated; A-FAN bldg11: 200 visits as stated; A-FAN bldg15: 200 visits as stated; A-FAN bldg9: 200 visits as stated; B bldg15: 100 visits as stated; B bldg11: 100 visits as stated; S1 demo: 100 visits as stated; S2 demo: 100 visits as stated; S3 demo: 100 visits as stated; S4 demo: 100 visits as stated; B bldg9 as stated; S5 as stated)
- G4 126 room questions of an A-FAN visit forward and backward: identical; 3 air-handler questions answered in vocabulary: **PASS**
- G5 244 rooms that asked no air-handler check themselves: largest difference between the session's belief and the joint marginal 8.3e-16: **PASS**

## A-LS: 4 low-static rooms on the larger handler + 2 own-fault rooms on the other

| building | answers | arm | accuracy | shared-cause rooms | own-fault rooms elsewhere | folded rooms (own fault on the faulty handler) | folded called low static | minutes / visit | wrong and confident | with the hedge | rooms called confident | vs HARD: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bldg11 | W0 | HARD | 84.4% | 91.8% | 69.8% | - | - | 188 | 0.1% | 0.1% | 62% |  |
| bldg11 | W0 | SOFT | 86.1% | 94.1% | 70.0% | - | - | 226 | 0.1% | 0.1% | 57% | +1.7 (+0.5, +3.0); +38 (+33, +42) |
| bldg11 | W0 | JOINT | 85.7% | 93.5% | 70.0% | - | - | 227 | 0.1% | 0.1% | 56% | +1.2 (+0.0, +2.6); +39 (+34, +43) |
| bldg11 | W1 | HARD | 60.9% | 74.8% | 33.2% | - | - | 205 | 2.0% | 2.0% | 48% |  |
| bldg11 | W1 | SOFT | 57.8% | 70.0% | 33.5% | - | - | 248 | 2.3% | 2.3% | 41% | -3.1 (-4.6, -1.4); +43 (+38, +48) |
| bldg11 | W1 | JOINT | 57.2% | 69.0% | 33.5% | - | - | 249 | 2.4% | 2.4% | 39% | -3.8 (-5.4, -1.9); +44 (+38, +50) |
| bldg15 | W0 | HARD | 75.2% | 78.8% | 68.2% | - | - | 239 | 0.1% | 0.1% | 19% |  |
| bldg15 | W0 | SOFT | 76.7% | 80.9% | 68.2% | - | - | 252 | 0.1% | 0.1% | 40% | +1.4 (+0.2, +2.7); +13 (+10, +17) |
| bldg15 | W0 | JOINT | 76.2% | 80.2% | 68.2% | - | - | 253 | 0.1% | 0.1% | 39% | +1.0 (-0.2, +2.3); +14 (+10, +18) |
| bldg15 | W1 | HARD | 48.5% | 56.6% | 32.2% | - | - | 245 | 2.2% | 2.2% | 14% |  |
| bldg15 | W1 | SOFT | 46.9% | 54.2% | 32.2% | - | - | 261 | 2.3% | 2.3% | 25% | -1.6 (-3.2, -0.1); +16 (+12, +21) |
| bldg15 | W1 | JOINT | 46.6% | 53.8% | 32.2% | - | - | 262 | 2.3% | 2.3% | 24% | -1.9 (-3.6, -0.2); +17 (+13, +22) |
| bldg9 | W0 | HARD | 81.1% | 85.8% | 71.8% | - | - | 207 | 0.3% | 0.3% | 28% |  |
| bldg9 | W0 | SOFT | 80.8% | 85.4% | 71.8% | - | - | 241 | 0.3% | 0.3% | 49% | -0.2 (-1.3, +0.8); +34 (+31, +37) |
| bldg9 | W0 | JOINT | 80.5% | 84.9% | 71.8% | - | - | 242 | 0.3% | 0.3% | 48% | -0.6 (-1.8, +0.6); +35 (+32, +39) |
| bldg9 | W1 | HARD | 51.0% | 59.1% | 34.8% | - | - | 237 | 2.3% | 2.3% | 22% |  |
| bldg9 | W1 | SOFT | 47.2% | 53.6% | 34.5% | - | - | 270 | 2.7% | 2.7% | 30% | -3.8 (-5.4, -2.2); +32 (+27, +37) |
| bldg9 | W1 | JOINT | 46.7% | 52.8% | 34.5% | - | - | 271 | 2.7% | 2.7% | 28% | -4.3 (-6.1, -2.6); +33 (+28, +38) |

## B: registered composition (50 shared / 50 local visits; own-fault rooms can sit on the faulty handler)

| building | answers | arm | accuracy | shared-cause rooms | own-fault rooms elsewhere | folded rooms (own fault on the faulty handler) | folded called low static | minutes / visit | wrong and confident | with the hedge | rooms called confident | vs HARD: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bldg11 | W0 | HARD | 74.8% | 92.5% | 75.3% | 10.5% (n=57) | 86% | 194 | 6.8% | 0.2% | 43% |  |
| bldg11 | W0 | SOFT | 80.0% | 94.5% | 75.6% | 56.1% (n=57) | 28% | 232 | 1.8% | 1.7% | 40% | +5.2 (+3.0, +7.5); +39 (+29, +50) |
| bldg11 | W0 | JOINT | 80.2% | 94.5% | 75.6% | 57.9% (n=57) | 21% | 237 | 1.0% | 1.0% | 37% | +5.3 (+3.2, +7.7); +43 (+32, +55) |
| bldg11 | W1 | HARD | 54.7% | 78.4% | 48.3% | 10.5% (n=57) | 81% | 205 | 8.3% | 1.5% | 36% |  |
| bldg11 | W1 | SOFT | 55.0% | 72.9% | 48.5% | 31.6% (n=57) | 40% | 250 | 4.5% | 4.3% | 27% | +0.3 (-2.0, +2.7); +45 (+33, +58) |
| bldg11 | W1 | JOINT | 55.3% | 70.9% | 49.4% | 36.8% (n=57) | 32% | 254 | 3.8% | 3.8% | 26% | +0.7 (-2.0, +3.3); +49 (+36, +62) |
| bldg15 | W0 | HARD | 70.5% | 85.9% | 70.1% | 23.8% (n=63) | 62% | 205 | 4.0% | 0.2% | 31% |  |
| bldg15 | W0 | SOFT | 75.3% | 86.4% | 70.1% | 68.3% (n=63) | 6% | 243 | 0.3% | 0.3% | 34% | +4.8 (+2.8, +7.0); +38 (+28, +47) |
| bldg15 | W0 | JOINT | 75.5% | 86.4% | 70.1% | 69.8% (n=63) | 5% | 242 | 0.3% | 0.3% | 32% | +5.0 (+3.0, +7.2); +37 (+28, +47) |
| bldg15 | W1 | HARD | 55.0% | 74.4% | 48.5% | 28.6% (n=63) | 43% | 213 | 4.8% | 2.0% | 27% |  |
| bldg15 | W1 | SOFT | 53.8% | 65.8% | 49.1% | 41.3% (n=63) | 16% | 243 | 3.5% | 3.5% | 26% | -1.2 (-3.5, +1.0); +30 (+20, +40) |
| bldg15 | W1 | JOINT | 53.7% | 65.3% | 49.1% | 41.3% (n=63) | 14% | 245 | 3.2% | 3.2% | 25% | -1.3 (-3.7, +0.8); +31 (+22, +42) |
| bldg9 | W0 | HARD | 72.8% | 80.9% | 75.4% | 23.5% (n=51) | 67% | 216 | 3.3% | 0.0% | 31% |  |
| bldg9 | W0 | SOFT | 76.3% | 82.4% | 75.7% | 56.9% (n=51) | 14% | 259 | 0.3% | 0.3% | 35% | +3.5 (+1.5, +5.8); +43 (+30, +56) |
| bldg9 | W0 | JOINT | 76.5% | 82.4% | 75.7% | 58.8% (n=51) | 10% | 260 | 0.2% | 0.2% | 34% | +3.7 (+1.7, +6.0); +44 (+31, +57) |
| bldg9 | W1 | HARD | 55.5% | 70.9% | 51.1% | 25.5% (n=51) | 53% | 243 | 5.0% | 2.5% | 26% |  |
| bldg9 | W1 | SOFT | 54.8% | 65.3% | 51.1% | 39.2% (n=51) | 22% | 284 | 3.3% | 3.3% | 28% | -0.7 (-2.8, +1.5); +41 (+28, +55) |
| bldg9 | W1 | JOINT | 53.8% | 61.8% | 51.1% | 41.2% (n=51) | 18% | 285 | 3.2% | 3.2% | 27% | -1.7 (-4.0, +0.7); +43 (+29, +57) |

## S5: low static on AHU-0, 2-3 shared rooms + 2 own-fault rooms ALSO on AHU-0 (folding on a small handler)

| building | answers | arm | accuracy | shared-cause rooms | own-fault rooms elsewhere | folded rooms (own fault on the faulty handler) | folded called low static | minutes / visit | wrong and confident | with the hedge | rooms called confident | vs HARD: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| demo | W0 | HARD | 54.9% | 98.8% | nan% | 0.0% (n=200) | 98% | 6 | 41.1% | 0.0% | 92% |  |
| demo | W0 | SOFT | 56.4% | 98.8% | nan% | 3.5% (n=200) | 94% | 17 | 33.8% | 0.0% | 80% | +1.6 (+0.4, +2.9); +11 (+7, +16) |
| demo | W0 | JOINT | 56.2% | 98.4% | nan% | 3.5% (n=200) | 94% | 13 | 36.0% | 0.0% | 84% | +1.3 (+0.0, +3.1); +7 (+2, +13) |
| demo | W1 | HARD | 53.6% | 94.8% | nan% | 2.0% (n=200) | 94% | 15 | 34.9% | 0.4% | 78% |  |
| demo | W1 | SOFT | 53.8% | 94.0% | nan% | 3.5% (n=200) | 90% | 26 | 26.0% | 0.9% | 60% | +0.2 (-0.9, +1.5); +12 (+6, +19) |
| demo | W1 | JOINT | 54.0% | 94.4% | nan% | 3.5% (n=200) | 90% | 22 | 30.2% | 0.9% | 69% | +0.4 (-0.9, +2.0); +8 (+2, +14) |

## S3: low static, 2-4 of 8 rooms + 2 own-fault rooms on AHU-1

| building | answers | arm | accuracy | shared-cause rooms | own-fault rooms elsewhere | folded rooms (own fault on the faulty handler) | folded called low static | minutes / visit | wrong and confident | with the hedge | rooms called confident | vs HARD: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| demo | W0 | HARD | 90.0% | 97.3% | 79.0% | - | - | 110 | 0.2% | 0.2% | 65% |  |
| demo | W0 | SOFT | 90.4% | 98.0% | 79.0% | - | - | 118 | 0.2% | 0.2% | 55% | +0.4 (+0.0, +1.0); +7 (+5, +11) |
| demo | W0 | JOINT | 89.6% | 96.7% | 79.0% | - | - | 121 | 0.2% | 0.2% | 52% | -0.4 (-1.4, +0.6); +11 (+7, +16) |
| demo | W1 | HARD | 73.3% | 95.7% | 40.0% | - | - | 120 | 3.2% | 2.4% | 60% |  |
| demo | W1 | SOFT | 72.7% | 93.3% | 42.0% | - | - | 132 | 2.8% | 2.8% | 51% | -0.6 (-2.0, +0.6); +12 (+8, +16) |
| demo | W1 | JOINT | 72.7% | 93.3% | 42.0% | - | - | 134 | 2.8% | 2.8% | 48% | -0.6 (-2.0, +0.8); +14 (+9, +19) |

## S4: 6 own-fault rooms, no shared cause

| building | answers | arm | accuracy | shared-cause rooms | own-fault rooms elsewhere | folded rooms (own fault on the faulty handler) | folded called low static | minutes / visit | wrong and confident | with the hedge | rooms called confident | vs HARD: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| demo | W0 | HARD | 75.2% | nan% | 75.2% | - | - | 289 | 2.3% | 0.3% | 19% |  |
| demo | W0 | SOFT | 76.2% | nan% | 76.2% | - | - | 287 | 1.8% | 0.5% | 19% | +1.0 (+0.0, +2.2); -2 (-5, +3) |
| demo | W0 | JOINT | 76.3% | nan% | 76.3% | - | - | 287 | 1.3% | 0.3% | 18% | +1.2 (-0.2, +2.7); -1 (-6, +4) |
| demo | W1 | HARD | 41.5% | nan% | 41.5% | - | - | 277 | 12.5% | 4.5% | 22% |  |
| demo | W1 | SOFT | 43.5% | nan% | 43.5% | - | - | 286 | 9.0% | 5.0% | 18% | +2.0 (+0.7, +3.5); +10 (+3, +17) |
| demo | W1 | JOINT | 44.2% | nan% | 44.2% | - | - | 290 | 8.0% | 5.0% | 17% | +2.7 (+1.0, +4.5); +13 (+5, +22) |

## A-FAN: 4 fan-off rooms on the larger handler + 2 own-fault rooms on the other (harm check)

| building | answers | arm | accuracy | shared-cause rooms | own-fault rooms elsewhere | folded rooms (own fault on the faulty handler) | folded called low static | minutes / visit | wrong and confident | with the hedge | rooms called confident | vs HARD: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bldg11 | W0 | HARD | 23.2% | 0.0% | 69.8% | - | - | 174 | 58.8% | 13.4% | 64% |  |
| bldg11 | W0 | SOFT | 23.3% | 0.0% | 70.0% | - | - | 216 | 57.2% | 57.2% | 63% | +0.1 (+0.0, +0.2); +41 (+37, +45) |
| bldg11 | W0 | JOINT | 23.3% | 0.0% | 70.0% | - | - | 217 | 55.6% | 55.6% | 62% | +0.1 (+0.0, +0.2); +42 (+38, +46) |
| bldg11 | W1 | HARD | 11.1% | 0.0% | 33.2% | - | - | 194 | 48.6% | 12.7% | 51% |  |
| bldg11 | W1 | SOFT | 11.2% | 0.0% | 33.5% | - | - | 239 | 41.9% | 41.9% | 44% | +0.1 (+0.0, +0.2); +45 (+40, +51) |
| bldg11 | W1 | JOINT | 11.2% | 0.0% | 33.5% | - | - | 240 | 39.5% | 39.5% | 42% | +0.1 (+0.0, +0.2); +46 (+41, +52) |
| bldg15 | W0 | HARD | 22.8% | 0.0% | 68.2% | - | - | 227 | 8.1% | 0.1% | 14% |  |
| bldg15 | W0 | SOFT | 22.8% | 0.0% | 68.2% | - | - | 241 | 40.3% | 40.3% | 46% | +0.0 (+0.0, +0.0); +14 (+10, +17) |
| bldg15 | W0 | JOINT | 22.8% | 0.0% | 68.2% | - | - | 241 | 39.3% | 39.3% | 45% | +0.0 (+0.0, +0.0); +14 (+11, +18) |
| bldg15 | W1 | HARD | 10.8% | 0.0% | 32.2% | - | - | 237 | 10.3% | 1.8% | 12% |  |
| bldg15 | W1 | SOFT | 10.8% | 0.0% | 32.2% | - | - | 254 | 25.4% | 25.4% | 27% | +0.0 (+0.0, +0.0); +16 (+12, +20) |
| bldg15 | W1 | JOINT | 10.8% | 0.0% | 32.2% | - | - | 255 | 24.3% | 24.3% | 26% | +0.0 (+0.0, +0.0); +17 (+13, +22) |
| bldg9 | W0 | HARD | 23.9% | 0.0% | 71.8% | - | - | 190 | 13.2% | 7.2% | 20% |  |
| bldg9 | W0 | SOFT | 23.9% | 0.0% | 71.8% | - | - | 229 | 49.1% | 49.1% | 56% | +0.0 (+0.0, +0.0); +39 (+35, +42) |
| bldg9 | W0 | JOINT | 23.9% | 0.0% | 71.8% | - | - | 230 | 47.6% | 47.6% | 54% | +0.0 (+0.0, +0.0); +40 (+36, +44) |
| bldg9 | W1 | HARD | 11.6% | 0.0% | 34.8% | - | - | 224 | 15.6% | 8.4% | 19% |  |
| bldg9 | W1 | SOFT | 11.5% | 0.0% | 34.5% | - | - | 258 | 30.9% | 30.9% | 34% | -0.1 (-0.2, +0.0); +34 (+29, +38) |
| bldg9 | W1 | JOINT | 11.5% | 0.0% | 34.5% | - | - | 259 | 30.2% | 30.2% | 33% | -0.1 (-0.2, +0.0); +35 (+30, +40) |

## S1: fan off hitting each of 8 rooms at 90% (harm check)

| building | answers | arm | accuracy | shared-cause rooms | own-fault rooms elsewhere | folded rooms (own fault on the faulty handler) | folded called low static | minutes / visit | wrong and confident | with the hedge | rooms called confident | vs HARD: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| demo | W0 | HARD | 90.2% | 90.2% | nan% | - | - | 3 | 0.0% | 0.0% | 0% |  |
| demo | W0 | SOFT | 89.5% | 89.5% | nan% | - | - | 6 | 0.0% | 0.0% | 10% | -0.7 (-2.1, +0.0); +3 (+2, +4) |
| demo | W0 | JOINT | 89.4% | 89.4% | nan% | - | - | 6 | 0.0% | 0.0% | 12% | -0.8 (-2.6, +0.0); +3 (+2, +4) |
| demo | W1 | HARD | 75.7% | 75.7% | nan% | - | - | 3 | 0.0% | 0.0% | 0% |  |
| demo | W1 | SOFT | 73.6% | 73.6% | nan% | - | - | 6 | 0.0% | 0.0% | 8% | -2.1 (-4.8, +0.0); +3 (+2, +5) |
| demo | W1 | JOINT | 73.8% | 73.8% | nan% | - | - | 6 | 0.0% | 0.0% | 9% | -2.0 (-4.4, +0.0); +3 (+2, +5) |

## S2: fan off, 2-4 of 8 rooms complain + 2 own-fault rooms (harm check)

| building | answers | arm | accuracy | shared-cause rooms | own-fault rooms elsewhere | folded rooms (own fault on the faulty handler) | folded called low static | minutes / visit | wrong and confident | with the hedge | rooms called confident | vs HARD: accuracy (95% CI); minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| demo | W0 | HARD | 29.9% | 0.0% | 74.5% | - | - | 113 | 56.7% | 6.8% | 65% |  |
| demo | W0 | SOFT | 29.9% | 0.3% | 74.0% | - | - | 118 | 33.5% | 9.0% | 42% | +0.0 (-0.6, +0.6); +6 (+4, +8) |
| demo | W0 | JOINT | 34.5% | 8.0% | 74.0% | - | - | 125 | 26.5% | 8.4% | 35% | +4.6 (+3.1, +6.3); +12 (+10, +15) |
| demo | W1 | HARD | 19.2% | 0.0% | 48.0% | - | - | 119 | 51.9% | 7.6% | 57% |  |
| demo | W1 | SOFT | 19.8% | 1.0% | 48.0% | - | - | 126 | 35.7% | 11.0% | 41% | +0.6 (-0.2, +1.6); +7 (+4, +10) |
| demo | W1 | JOINT | 21.4% | 3.3% | 48.5% | - | - | 132 | 32.3% | 11.0% | 38% | +2.2 (+1.0, +3.6); +13 (+8, +18) |

## Predictions for SOFT (written before any run)

- Q1 (folded rooms, B: SOFT +15 pooled and +10 on each building): **HELD** (pooled +41.5 (+33.3, +49.4); bldg11 +45.6, bldg15 +44.4, bldg9 +33.3)
- Q2 (folded rooms, S5: +15): **FAILED** (S5 folded rooms +3.5 (+1.0, +6.5); HARD 0.0%, SOFT 3.5%)
- Q3 (no accuracy harm (not more than 2 below HARD in B, A-LS, S3, S4, S5)): **HELD** (B bldg11 +5.2, B bldg15 +4.8, B bldg9 +3.5, A-LS bldg11 +1.7, A-LS bldg15 +1.4, A-LS bldg9 -0.2, S3 demo +0.4, S4 demo +1.0, S5 demo +1.6)
- Q4 (minutes within +10% in B and A-LS): **FAILED** (B bldg11 +39 on 194 (+20%), B bldg15 +38 on 205 (+18%), B bldg9 +43 on 216 (+20%), A-LS bldg11 +38 on 188 (+20%), A-LS bldg15 +13 on 239 (+6%), A-LS bldg9 +34 on 207 (+16%))
- Q5 (wrong-and-confident at most +1 everywhere and at least 2 below in B bldg11): **HELD** (B bldg11 -5.0, B bldg15 -3.7, B bldg9 -3.0, A-LS bldg11 +0.0, A-LS bldg15 +0.0, A-LS bldg9 +0.0, S3 demo +0.0, S4 demo -0.5, S5 demo -7.3; B bldg11 HARD 6.8% -> 1.8%)
- Q6 (fan-off families within 3 points): **HELD** (A-FAN bldg11 +0.1, A-FAN bldg15 +0.0, A-FAN bldg9 +0.0, S1 demo -0.7, S2 demo +0.0)
- Q7 (A-LS shared rooms within 3 points): **HELD** (bldg11 +2.4, bldg15 +2.1, bldg9 -0.4)
- Q8 (JOINT within 2 points of SOFT in B): **HELD** (bldg11 +0.2, bldg15 +0.2, bldg9 +0.2)

## The same predictions for JOINT (Q1-Q7)

- Q1: **HELD** (pooled +43.3 (+34.9, +51.2); bldg11 +47.4, bldg15 +46.0, bldg9 +35.3)
- Q2: **FAILED** (S5 folded rooms +3.5 (+0.5, +7.5); HARD 0.0%, JOINT 3.5%)
- Q3: **HELD** (B bldg11 +5.3, B bldg15 +5.0, B bldg9 +3.7, A-LS bldg11 +1.2, A-LS bldg15 +1.0, A-LS bldg9 -0.6, S3 demo -0.4, S4 demo +1.2, S5 demo +1.3)
- Q4: **FAILED** (B bldg11 +43 on 194 (+22%), B bldg15 +37 on 205 (+18%), B bldg9 +44 on 216 (+20%), A-LS bldg11 +39 on 188 (+21%), A-LS bldg15 +14 on 239 (+6%), A-LS bldg9 +35 on 207 (+17%))
- Q5: **HELD** (B bldg11 -5.8, B bldg15 -3.7, B bldg9 -3.2, A-LS bldg11 +0.0, A-LS bldg15 +0.0, A-LS bldg9 +0.0, S3 demo +0.0, S4 demo -1.0, S5 demo -5.1; B bldg11 HARD 6.8% -> 1.0%)
- Q6: **FAILED** (A-FAN bldg11 +0.1, A-FAN bldg15 +0.0, A-FAN bldg9 +0.0, S1 demo -0.8, S2 demo +4.6)
- Q7: **HELD** (bldg11 +1.8, bldg15 +1.5, bldg9 -0.9)

## Decision rule applied

- SOFT: **NO GAIN**
- JOINT: **NO GAIN**
