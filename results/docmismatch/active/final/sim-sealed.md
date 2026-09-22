sim-sealed: 778 episodes (204 clusters = event groups); config variant=sel_slice, tau=0.95, primary setting `visit`; elapsed 371s; info={"n_outer": 7780, "beta": {"ahu_sat": 1.0, "ahu_vav": 1.0, "branch_coil": 0.35, "coil_ahu": 1.0, "coil_vav": 1.0, "loop_branch": 0.2, "loop_pump": 1.0, "loop_source": 0.35, "vav_dat": 1.0, "vav_zone": 0.1}}

# Readiness evaluation: sim-sealed

## Layer `none` (778 episodes per policy, 204 clusters)

### Headline per policy (same layer; class-balanced; 95% cluster-bootstrap CI)

| policy | answered coverage | accuracy among answered | readings among answered |
| --- | --- | --- | --- |
| active | 0.518 [0.444, 0.595] | 0.713 [0.611, 0.797] | 5.7 [5.2, 6.2] |
| frozen | 0.519 [0.443, 0.597] | 0.714 [0.616, 0.801] | 6.7 [6.1, 7.4] |
| random | 0.114 [0.082, 0.150] | 0.931 [0.858, 0.986] | 13.0 [11.4, 14.6] |
| traversal | 0.179 [0.130, 0.236] | 0.935 [0.843, 1.000] | 6.7 [5.6, 7.9] |
| traversal_block | 0.183 [0.134, 0.238] | 0.937 [0.844, 1.000] | 7.5 [6.2, 9.0] |

### C1 efficiency: readings saved by active vs baseline (paired, among episodes answered by both)

| baseline | pairs | readings saved | coverage active - base | status |
| --- | --- | --- | --- | --- |
| random | 87 | 8.49 [7.01, 10.01] | 0.404 [0.337, 0.474] | PASS |
| traversal_block | 143 | 3.07 [1.82, 4.60] | 0.335 [0.273, 0.401] | PASS |
| traversal | 140 | 2.23 [1.27, 3.28] | 0.339 [0.276, 0.408] | PASS |
| frozen | 391 | 0.93 [0.37, 1.53] | -0.001 [-0.020, 0.015] | FAIL |

### C2 honest confidence (nominal 0.95; PASS: point>=0.93 and lower>=0.90; cells need >=8 answered and >=5 clusters)

| all | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| all | 778 | 403 | 124 | 0.713 [0.611, 0.797] | 0.518 [0.444, 0.595] | FAIL |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| s0 | 178 | 95 | 72 | 0.737 [0.619, 0.850] | 0.537 [0.450, 0.622] | FAIL |
| s1 | 196 | 102 | 74 | 0.713 [0.586, 0.827] | 0.521 [0.425, 0.621] | FAIL |
| s2 | 218 | 123 | 81 | 0.690 [0.570, 0.795] | 0.561 [0.470, 0.650] | FAIL |
| s3 | 186 | 83 | 65 | 0.712 [0.577, 0.829] | 0.447 [0.355, 0.540] | FAIL |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| parallel_peer_swap | 158 | 133 | 33 | 0.619 [0.525, 0.734] | 0.841 [0.758, 0.916] | FAIL |
| plant_loop_mapping | 60 | 8 | 7 | 1.000 [1.000, 1.000] | 0.138 [0.044, 0.243] | PASS |
| same_medium_branch | 160 | 32 | 17 | 0.781 [0.569, 0.952] | 0.200 [0.115, 0.299] | FAIL |
| sensor_mapping | 160 | 150 | 36 | 0.713 [0.621, 0.814] | 0.938 [0.860, 0.993] | FAIL |
| vav_zone_swap | 160 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| wrong_ahu_mapping | 80 | 80 | 31 | 0.800 [0.688, 0.906] | 1.000 [1.000, 1.000] | FAIL |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| ahu_sat | 16 | 7 | 3 | 0.571 [0.571, 0.571] | 0.438 [0.438, 0.438] | insufficient |
| ahu_vav | 80 | 80 | 31 | 0.800 [0.688, 0.906] | 1.000 [1.000, 1.000] | FAIL |
| branch_coil | 160 | 32 | 17 | 0.781 [0.569, 0.952] | 0.200 [0.115, 0.299] | FAIL |
| coil_ahu | 16 | 5 | 4 | 0.800 [0.500, 1.000] | 0.312 [0.250, 0.375] | insufficient |
| coil_vav | 136 | 122 | 27 | 0.598 [0.508, 0.708] | 0.897 [0.825, 0.952] | FAIL |
| loop_branch | 60 | 8 | 7 | 1.000 [1.000, 1.000] | 0.138 [0.044, 0.243] | PASS |
| loop_source | 6 | 6 | 2 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | insufficient |
| vav_dat | 144 | 143 | 33 | 0.720 [0.625, 0.827] | 0.993 [0.977, 1.000] | FAIL |
| vav_zone | 160 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

Cells (season x family x slot): 36; PASS: 0, INCONCLUSIVE: 0, FAIL: 14, insufficient: 22

Calibration (answered verdicts), ECE = 0.256 over n=403

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 403 | 0.969 | 0.712 |

Calibration (ALL crossed verdicts, answered or flagged), ECE = 0.256 over n=403

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 403 | 0.969 | 0.712 |

### C3 precise abstention

| bucket | episodes | resolvable | share | coverage of resolvable | status |
| --- | --- | --- | --- | --- | --- |
| season=s0 | 178 | 11 | 0.06 | 1.000 [1.000, 1.000] | n/a (resolvable share < 30%) |
| season=s1 | 196 | 14 | 0.07 | 1.000 [1.000, 1.000] | n/a (resolvable share < 30%) |
| season=s2 | 218 | 12 | 0.06 | 1.000 [1.000, 1.000] | n/a (resolvable share < 30%) |
| season=s3 | 186 | 11 | 0.06 | 1.000 [1.000, 1.000] | n/a (resolvable share < 30%) |
| slot=ahu_sat | 16 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=ahu_vav | 80 | 42 | 0.53 | 1.000 [1.000, 1.000] | PASS |
| slot=branch_coil | 160 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=coil_ahu | 16 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=coil_vav | 136 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_branch | 60 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_source | 6 | 6 | 1.00 | 1.000 [1.000, 1.000] | PASS |
| slot=vav_dat | 144 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_zone | 160 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 1.000 [1.000, 1.000] vs answered 0.881 [0.820, 0.934]; margin 0.119 [0.066, 0.180] -> PASS (flagged n=375, answered n=403)

(c) coverage of resolvable cases lost to flags: 0.000 [0.000, 0.000] of 48 resolvable episodes

**C3 status: PASS** (a: PASS)

### C4 knows its limits: 36 of 36 conditions are not C2-PASS; violations (flagged < 90%): 30 -> **FAIL**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| s0|parallel_peer_swap|coil_ahu | insufficient | 3 | 3 | 0.00 | NO |
| s0|parallel_peer_swap|coil_vav | FAIL | 29 | 33 | 0.12 | NO |
| s0|parallel_peer_swap|loop_source | insufficient | 2 | 2 | 0.00 | NO |
| s0|plant_loop_mapping|loop_branch | insufficient | 0 | 13 | 1.00 | yes |
| s0|same_medium_branch|branch_coil | FAIL | 8 | 36 | 0.78 | NO |
| s0|sensor_mapping|ahu_sat | insufficient | 2 | 4 | 0.50 | NO |
| s0|sensor_mapping|vav_dat | FAIL | 35 | 35 | 0.00 | NO |
| s0|vav_zone_swap|vav_zone | insufficient | 0 | 36 | 1.00 | yes |
| s0|wrong_ahu_mapping|ahu_vav | FAIL | 16 | 16 | 0.00 | NO |
| s1|parallel_peer_swap|coil_ahu | insufficient | 1 | 4 | 0.75 | NO |
| s1|parallel_peer_swap|coil_vav | FAIL | 31 | 35 | 0.11 | NO |
| s1|parallel_peer_swap|loop_source | insufficient | 1 | 1 | 0.00 | NO |
| s1|plant_loop_mapping|loop_branch | insufficient | 2 | 17 | 0.88 | NO |
| s1|same_medium_branch|branch_coil | FAIL | 10 | 39 | 0.74 | NO |
| s1|sensor_mapping|ahu_sat | insufficient | 1 | 2 | 0.50 | NO |
| s1|sensor_mapping|vav_dat | FAIL | 32 | 32 | 0.00 | NO |
| s1|vav_zone_swap|vav_zone | insufficient | 0 | 42 | 1.00 | yes |
| s1|wrong_ahu_mapping|ahu_vav | FAIL | 24 | 24 | 0.00 | NO |
| s2|parallel_peer_swap|coil_ahu | insufficient | 1 | 4 | 0.75 | NO |
| s2|parallel_peer_swap|coil_vav | FAIL | 41 | 43 | 0.05 | NO |
| s2|parallel_peer_swap|loop_source | insufficient | 2 | 2 | 0.00 | NO |
| s2|plant_loop_mapping|loop_branch | insufficient | 4 | 14 | 0.71 | NO |
| s2|same_medium_branch|branch_coil | insufficient | 7 | 46 | 0.85 | NO |
| s2|sensor_mapping|ahu_sat | insufficient | 2 | 4 | 0.50 | NO |
| s2|sensor_mapping|vav_dat | FAIL | 47 | 48 | 0.02 | NO |
| s2|vav_zone_swap|vav_zone | insufficient | 0 | 38 | 1.00 | yes |
| s2|wrong_ahu_mapping|ahu_vav | FAIL | 19 | 19 | 0.00 | NO |
| s3|parallel_peer_swap|coil_ahu | insufficient | 0 | 5 | 1.00 | yes |
| s3|parallel_peer_swap|coil_vav | FAIL | 21 | 25 | 0.16 | NO |
| s3|parallel_peer_swap|loop_source | insufficient | 1 | 1 | 0.00 | NO |
| s3|plant_loop_mapping|loop_branch | insufficient | 2 | 16 | 0.88 | NO |
| s3|same_medium_branch|branch_coil | insufficient | 7 | 39 | 0.82 | NO |
| s3|sensor_mapping|ahu_sat | insufficient | 2 | 6 | 0.67 | NO |
| s3|sensor_mapping|vav_dat | FAIL | 29 | 29 | 0.00 | NO |
| s3|vav_zone_swap|vav_zone | insufficient | 0 | 44 | 1.00 | yes |
| s3|wrong_ahu_mapping|ahu_vav | FAIL | 21 | 21 | 0.00 | NO |

## Layer `legacy` (778 episodes per policy, 204 clusters)

### Headline per policy (same layer; class-balanced; 95% cluster-bootstrap CI)

| policy | answered coverage | accuracy among answered | readings among answered |
| --- | --- | --- | --- |
| active | 0.161 [0.118, 0.212] | 0.868 [0.772, 0.943] | 6.2 [5.3, 7.7] |
| frozen | 0.031 [0.013, 0.056] | 1.000 [1.000, 1.000] | 1.1 [0.7, 1.6] |
| random | 0.072 [0.048, 0.099] | 0.927 [0.832, 1.000] | 11.5 [9.6, 13.5] |
| traversal | 0.168 [0.119, 0.222] | 0.931 [0.830, 1.000] | 6.4 [5.3, 7.7] |
| traversal_block | 0.172 [0.123, 0.225] | 0.932 [0.834, 1.000] | 7.2 [5.8, 8.7] |

### C1 efficiency: readings saved by active vs baseline (paired, among episodes answered by both)

| baseline | pairs | readings saved | coverage active - base | status |
| --- | --- | --- | --- | --- |
| random | 34 | 6.91 [4.56, 9.47] | 0.089 [0.052, 0.131] | PASS |
| traversal_block | 58 | 0.86 [-0.24, 1.92] | -0.011 [-0.065, 0.042] | FAIL |
| traversal | 59 | 1.92 [0.67, 3.10] | -0.007 [-0.062, 0.044] | FAIL |
| frozen | 25 | n/a | 0.130 [0.092, 0.175] | FAIL |

### C2 honest confidence (nominal 0.95; PASS: point>=0.93 and lower>=0.90; cells need >=8 answered and >=5 clusters)

| all | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| all | 778 | 126 | 56 | 0.868 [0.772, 0.943] | 0.161 [0.118, 0.212] | FAIL |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| s0 | 178 | 28 | 24 | 0.897 [0.771, 1.000] | 0.152 [0.098, 0.213] | FAIL |
| s1 | 196 | 35 | 30 | 0.873 [0.740, 0.973] | 0.177 [0.118, 0.245] | FAIL |
| s2 | 218 | 32 | 27 | 0.883 [0.745, 0.974] | 0.144 [0.087, 0.204] | FAIL |
| s3 | 186 | 31 | 28 | 0.812 [0.653, 0.940] | 0.166 [0.109, 0.236] | FAIL |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| parallel_peer_swap | 158 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| plant_loop_mapping | 60 | 7 | 6 | 1.000 [1.000, 1.000] | 0.125 [0.036, 0.234] | insufficient |
| same_medium_branch | 160 | 10 | 8 | 0.900 [0.661, 1.000] | 0.062 [0.027, 0.107] | FAIL |
| sensor_mapping | 160 | 29 | 11 | 1.000 [1.000, 1.000] | 0.181 [0.100, 0.279] | PASS |
| vav_zone_swap | 160 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| wrong_ahu_mapping | 80 | 80 | 31 | 0.800 [0.688, 0.906] | 1.000 [1.000, 1.000] | FAIL |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| ahu_sat | 16 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| ahu_vav | 80 | 80 | 31 | 0.800 [0.688, 0.906] | 1.000 [1.000, 1.000] | FAIL |
| branch_coil | 160 | 10 | 8 | 0.900 [0.661, 1.000] | 0.062 [0.027, 0.107] | FAIL |
| coil_ahu | 16 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| coil_vav | 136 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| loop_branch | 60 | 7 | 6 | 1.000 [1.000, 1.000] | 0.125 [0.036, 0.234] | insufficient |
| loop_source | 6 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| vav_dat | 144 | 29 | 11 | 1.000 [1.000, 1.000] | 0.201 [0.113, 0.301] | PASS |
| vav_zone | 160 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

Cells (season x family x slot): 36; PASS: 2, INCONCLUSIVE: 0, FAIL: 4, insufficient: 30

Calibration (answered verdicts), ECE = 0.082 over n=126

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 126 | 0.967 | 0.885 |

Calibration (ALL crossed verdicts, answered or flagged), ECE = 0.256 over n=403

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 403 | 0.969 | 0.712 |

### C3 precise abstention

| bucket | episodes | resolvable | share | coverage of resolvable | status |
| --- | --- | --- | --- | --- | --- |
| season=s0 | 178 | 11 | 0.06 | 0.818 [0.538, 1.000] | n/a (resolvable share < 30%) |
| season=s1 | 196 | 14 | 0.07 | 0.929 [0.750, 1.000] | n/a (resolvable share < 30%) |
| season=s2 | 218 | 12 | 0.06 | 0.833 [0.500, 1.000] | n/a (resolvable share < 30%) |
| season=s3 | 186 | 11 | 0.06 | 0.909 [0.667, 1.000] | n/a (resolvable share < 30%) |
| slot=ahu_sat | 16 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=ahu_vav | 80 | 42 | 0.53 | 1.000 [1.000, 1.000] | PASS |
| slot=branch_coil | 160 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=coil_ahu | 16 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=coil_vav | 136 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_branch | 60 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_source | 6 | 6 | 1.00 | 0.000 [0.000, 0.000] | FAIL |
| slot=vav_dat | 144 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_zone | 160 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 0.991 [0.974, 1.000] vs answered 0.666 [0.520, 0.802]; margin 0.325 [0.185, 0.469] -> PASS (flagged n=652, answered n=126)

(c) coverage of resolvable cases lost to flags: 0.125 [0.000, 0.333] of 48 resolvable episodes

**C3 status: FAIL** (a: FAIL)

### C4 knows its limits: 34 of 36 conditions are not C2-PASS; violations (flagged < 90%): 9 -> **FAIL**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| s0|parallel_peer_swap|coil_ahu | insufficient | 0 | 3 | 1.00 | yes |
| s0|parallel_peer_swap|coil_vav | insufficient | 0 | 33 | 1.00 | yes |
| s0|parallel_peer_swap|loop_source | insufficient | 0 | 2 | 1.00 | yes |
| s0|plant_loop_mapping|loop_branch | insufficient | 0 | 13 | 1.00 | yes |
| s0|same_medium_branch|branch_coil | insufficient | 1 | 36 | 0.97 | yes |
| s0|sensor_mapping|ahu_sat | insufficient | 0 | 4 | 1.00 | yes |
| s0|vav_zone_swap|vav_zone | insufficient | 0 | 36 | 1.00 | yes |
| s0|wrong_ahu_mapping|ahu_vav | FAIL | 16 | 16 | 0.00 | NO |
| s1|parallel_peer_swap|coil_ahu | insufficient | 0 | 4 | 1.00 | yes |
| s1|parallel_peer_swap|coil_vav | insufficient | 0 | 35 | 1.00 | yes |
| s1|parallel_peer_swap|loop_source | insufficient | 0 | 1 | 1.00 | yes |
| s1|plant_loop_mapping|loop_branch | insufficient | 2 | 17 | 0.88 | NO |
| s1|same_medium_branch|branch_coil | insufficient | 6 | 39 | 0.85 | NO |
| s1|sensor_mapping|ahu_sat | insufficient | 0 | 2 | 1.00 | yes |
| s1|sensor_mapping|vav_dat | insufficient | 3 | 32 | 0.91 | yes |
| s1|vav_zone_swap|vav_zone | insufficient | 0 | 42 | 1.00 | yes |
| s1|wrong_ahu_mapping|ahu_vav | FAIL | 24 | 24 | 0.00 | NO |
| s2|parallel_peer_swap|coil_ahu | insufficient | 0 | 4 | 1.00 | yes |
| s2|parallel_peer_swap|coil_vav | insufficient | 0 | 43 | 1.00 | yes |
| s2|parallel_peer_swap|loop_source | insufficient | 0 | 2 | 1.00 | yes |
| s2|plant_loop_mapping|loop_branch | insufficient | 3 | 14 | 0.79 | NO |
| s2|same_medium_branch|branch_coil | insufficient | 1 | 46 | 0.98 | yes |
| s2|sensor_mapping|ahu_sat | insufficient | 0 | 4 | 1.00 | yes |
| s2|vav_zone_swap|vav_zone | insufficient | 0 | 38 | 1.00 | yes |
| s2|wrong_ahu_mapping|ahu_vav | FAIL | 19 | 19 | 0.00 | NO |
| s3|parallel_peer_swap|coil_ahu | insufficient | 0 | 5 | 1.00 | yes |
| s3|parallel_peer_swap|coil_vav | insufficient | 0 | 25 | 1.00 | yes |
| s3|parallel_peer_swap|loop_source | insufficient | 0 | 1 | 1.00 | yes |
| s3|plant_loop_mapping|loop_branch | insufficient | 2 | 16 | 0.88 | NO |
| s3|same_medium_branch|branch_coil | insufficient | 2 | 39 | 0.95 | yes |
| s3|sensor_mapping|ahu_sat | insufficient | 0 | 6 | 1.00 | yes |
| s3|sensor_mapping|vav_dat | insufficient | 6 | 29 | 0.79 | NO |
| s3|vav_zone_swap|vav_zone | insufficient | 0 | 44 | 1.00 | yes |
| s3|wrong_ahu_mapping|ahu_vav | FAIL | 21 | 21 | 0.00 | NO |

## Layer `new` (778 episodes per policy, 204 clusters)

### Headline per policy (same layer; class-balanced; 95% cluster-bootstrap CI)

| policy | answered coverage | accuracy among answered | readings among answered |
| --- | --- | --- | --- |
| active | 0.034 [0.016, 0.055] | 1.000 [1.000, 1.000] | 3.6 [0.8, 4.0] |
| frozen | 0.079 [0.051, 0.113] | 0.905 [0.808, 0.981] | 3.1 [2.8, 3.4] |
| random | 0.000 [0.000, 0.000] | n/a | 0.0 [0.0, 0.0] |
| traversal | 0.100 [0.065, 0.137] | 0.934 [0.790, 1.000] | 6.7 [5.4, 8.3] |
| traversal_block | 0.101 [0.067, 0.139] | 0.934 [0.793, 1.000] | 6.0 [4.7, 7.7] |

### C1 efficiency: readings saved by active vs baseline (paired, among episodes answered by both)

| baseline | pairs | readings saved | coverage active - base | status |
| --- | --- | --- | --- | --- |
| random | 0 | n/a | n/a | n/a |
| traversal_block | 26 | 1.88 [1.20, 3.02] | -0.067 [-0.098, -0.039] | FAIL |
| traversal | 25 | 2.02 [1.33, 2.86] | -0.066 [-0.097, -0.038] | FAIL |
| frozen | 8 | n/a | -0.045 [-0.081, -0.014] | FAIL |

### C2 honest confidence (nominal 0.95; PASS: point>=0.93 and lower>=0.90; cells need >=8 answered and >=5 clusters)

| all | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| all | 778 | 27 | 14 | 1.000 [1.000, 1.000] | 0.034 [0.016, 0.055] | PASS |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| s0 | 178 | 8 | 8 | 1.000 [1.000, 1.000] | 0.042 [0.016, 0.074] | PASS |
| s1 | 196 | 8 | 8 | 1.000 [1.000, 1.000] | 0.045 [0.017, 0.078] | PASS |
| s2 | 218 | 6 | 6 | 1.000 [1.000, 1.000] | 0.026 [0.008, 0.050] | insufficient |
| s3 | 186 | 5 | 5 | 1.000 [1.000, 1.000] | 0.026 [0.006, 0.052] | insufficient |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| parallel_peer_swap | 158 | 5 | 2 | 1.000 [1.000, 1.000] | 0.031 [0.000, 0.095] | insufficient |
| plant_loop_mapping | 60 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| same_medium_branch | 160 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| sensor_mapping | 160 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| vav_zone_swap | 160 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| wrong_ahu_mapping | 80 | 22 | 12 | 1.000 [1.000, 1.000] | 0.275 [0.167, 0.375] | PASS |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| ahu_sat | 16 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| ahu_vav | 80 | 22 | 12 | 1.000 [1.000, 1.000] | 0.275 [0.167, 0.375] | PASS |
| branch_coil | 160 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| coil_ahu | 16 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| coil_vav | 136 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| loop_branch | 60 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| loop_source | 6 | 5 | 2 | 1.000 [1.000, 1.000] | 0.750 [0.750, 0.750] | insufficient |
| vav_dat | 144 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| vav_zone | 160 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

Cells (season x family x slot): 36; PASS: 0, INCONCLUSIVE: 0, FAIL: 0, insufficient: 36

Calibration (answered verdicts), ECE = 0.118 over n=27

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.80,0.90) | 4 | 0.818 | 1.000 |
| [0.95,1.00) | 23 | 0.962 | 1.000 |

Calibration (ALL crossed verdicts, answered or flagged), ECE = 0.124 over n=403

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.50,0.60) | 22 | 0.541 | 0.312 |
| [0.60,0.70) | 4 | 0.669 | 0.753 |
| [0.80,0.90) | 124 | 0.816 | 0.714 |
| [0.95,1.00) | 226 | 0.964 | 0.822 |

### C3 precise abstention

| bucket | episodes | resolvable | share | coverage of resolvable | status |
| --- | --- | --- | --- | --- | --- |
| season=s0 | 178 | 11 | 0.06 | 0.727 [0.429, 1.000] | n/a (resolvable share < 30%) |
| season=s1 | 196 | 14 | 0.07 | 0.571 [0.294, 0.875] | n/a (resolvable share < 30%) |
| season=s2 | 218 | 12 | 0.06 | 0.500 [0.182, 0.889] | n/a (resolvable share < 30%) |
| season=s3 | 186 | 11 | 0.06 | 0.455 [0.154, 0.889] | n/a (resolvable share < 30%) |
| slot=ahu_sat | 16 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=ahu_vav | 80 | 42 | 0.53 | 0.524 [0.296, 0.800] | PASS |
| slot=branch_coil | 160 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=coil_ahu | 16 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=coil_vav | 136 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_branch | 60 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_source | 6 | 6 | 1.00 | 0.833 [0.500, 1.000] | PASS |
| slot=vav_dat | 144 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_zone | 160 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 0.971 [0.946, 0.991] vs answered 0.000 [0.000, 0.000]; margin 0.971 [0.946, 0.991] -> PASS (flagged n=751, answered n=27)

(c) coverage of resolvable cases lost to flags: 0.438 [0.185, 0.661] of 48 resolvable episodes

**C3 status: PASS** (a: PASS)

### C4 knows its limits: 36 of 36 conditions are not C2-PASS; violations (flagged < 90%): 8 -> **FAIL**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| s0|parallel_peer_swap|coil_ahu | insufficient | 0 | 3 | 1.00 | yes |
| s0|parallel_peer_swap|coil_vav | insufficient | 0 | 33 | 1.00 | yes |
| s0|parallel_peer_swap|loop_source | insufficient | 1 | 2 | 0.50 | NO |
| s0|plant_loop_mapping|loop_branch | insufficient | 0 | 13 | 1.00 | yes |
| s0|same_medium_branch|branch_coil | insufficient | 0 | 36 | 1.00 | yes |
| s0|sensor_mapping|ahu_sat | insufficient | 0 | 4 | 1.00 | yes |
| s0|sensor_mapping|vav_dat | insufficient | 0 | 35 | 1.00 | yes |
| s0|vav_zone_swap|vav_zone | insufficient | 0 | 36 | 1.00 | yes |
| s0|wrong_ahu_mapping|ahu_vav | insufficient | 7 | 16 | 0.56 | NO |
| s1|parallel_peer_swap|coil_ahu | insufficient | 0 | 4 | 1.00 | yes |
| s1|parallel_peer_swap|coil_vav | insufficient | 0 | 35 | 1.00 | yes |
| s1|parallel_peer_swap|loop_source | insufficient | 1 | 1 | 0.00 | NO |
| s1|plant_loop_mapping|loop_branch | insufficient | 0 | 17 | 1.00 | yes |
| s1|same_medium_branch|branch_coil | insufficient | 0 | 39 | 1.00 | yes |
| s1|sensor_mapping|ahu_sat | insufficient | 0 | 2 | 1.00 | yes |
| s1|sensor_mapping|vav_dat | insufficient | 0 | 32 | 1.00 | yes |
| s1|vav_zone_swap|vav_zone | insufficient | 0 | 42 | 1.00 | yes |
| s1|wrong_ahu_mapping|ahu_vav | insufficient | 7 | 24 | 0.71 | NO |
| s2|parallel_peer_swap|coil_ahu | insufficient | 0 | 4 | 1.00 | yes |
| s2|parallel_peer_swap|coil_vav | insufficient | 0 | 43 | 1.00 | yes |
| s2|parallel_peer_swap|loop_source | insufficient | 2 | 2 | 0.00 | NO |
| s2|plant_loop_mapping|loop_branch | insufficient | 0 | 14 | 1.00 | yes |
| s2|same_medium_branch|branch_coil | insufficient | 0 | 46 | 1.00 | yes |
| s2|sensor_mapping|ahu_sat | insufficient | 0 | 4 | 1.00 | yes |
| s2|sensor_mapping|vav_dat | insufficient | 0 | 48 | 1.00 | yes |
| s2|vav_zone_swap|vav_zone | insufficient | 0 | 38 | 1.00 | yes |
| s2|wrong_ahu_mapping|ahu_vav | insufficient | 4 | 19 | 0.79 | NO |
| s3|parallel_peer_swap|coil_ahu | insufficient | 0 | 5 | 1.00 | yes |
| s3|parallel_peer_swap|coil_vav | insufficient | 0 | 25 | 1.00 | yes |
| s3|parallel_peer_swap|loop_source | insufficient | 1 | 1 | 0.00 | NO |
| s3|plant_loop_mapping|loop_branch | insufficient | 0 | 16 | 1.00 | yes |
| s3|same_medium_branch|branch_coil | insufficient | 0 | 39 | 1.00 | yes |
| s3|sensor_mapping|ahu_sat | insufficient | 0 | 6 | 1.00 | yes |
| s3|sensor_mapping|vav_dat | insufficient | 0 | 29 | 1.00 | yes |
| s3|vav_zone_swap|vav_zone | insufficient | 0 | 44 | 1.00 | yes |
| s3|wrong_ahu_mapping|ahu_vav | insufficient | 4 | 21 | 0.81 | NO |
