sim-dev-loto_v5_sel_slice: 1626 episodes (331 clusters = event groups); config variant=sel_slice, tau=0.95, primary setting `visit`; elapsed 903s; info={"sys03_psz_ac": {"beta": {"ahu_sat": 1.0, "ahu_vav": 1.0, "branch_coil": 0.35, "coil_ahu": 1.0, "coil_vav": 1.0, "loop_branch": 0.2, "loop_pump": 1.0, "loop_source": 0.35, "vav_dat": 1.0, "vav_zone": 1.0}, "n_outer": 2320, "n_inner": 13940}, "sys07_vav_reheat": {"beta": {"ahu_sat": 1.0, "ahu_vav": 1.0, "branch_coil": 0.5, "coil_ahu": 1.0, "coil_vav": 1.0, "loop_branch": 0.2, "loop_pump": 1.0, "lo

# Readiness evaluation: sim-dev-loto_v5_sel_slice

## Layer `none` (1626 episodes per policy, 331 clusters)

### Headline per policy (same layer; class-balanced; 95% cluster-bootstrap CI)

| policy | answered coverage | accuracy among answered | readings among answered |
| --- | --- | --- | --- |
| active | 0.504 [0.433, 0.569] | 0.870 [0.812, 0.920] | 5.7 [4.9, 6.7] |
| frozen | 0.510 [0.436, 0.578] | 0.860 [0.802, 0.909] | 6.2 [5.3, 7.3] |
| random | 0.222 [0.179, 0.269] | 0.941 [0.908, 0.968] | 13.1 [12.1, 14.1] |
| traversal | 0.281 [0.222, 0.345] | 0.963 [0.927, 0.991] | 8.1 [7.0, 9.4] |
| traversal_block | 0.285 [0.225, 0.349] | 0.966 [0.931, 0.994] | 8.1 [7.0, 9.5] |

### C1 efficiency: readings saved by active vs baseline (paired, among episodes answered by both)

| baseline | pairs | readings saved | coverage active - base | status |
| --- | --- | --- | --- | --- |
| random | 350 | 9.23 [8.05, 10.20] | 0.282 [0.233, 0.330] | PASS |
| traversal_block | 460 | 3.87 [3.07, 4.87] | 0.219 [0.162, 0.276] | PASS |
| traversal | 453 | 3.93 [3.13, 4.97] | 0.223 [0.165, 0.282] | PASS |
| frozen | 790 | 0.58 [0.37, 0.85] | -0.006 [-0.025, 0.012] | FAIL |

### C2 honest confidence (nominal 0.95; PASS: point>=0.93 and lower>=0.90; cells need >=8 answered and >=5 clusters)

| all | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| all | 1626 | 818 | 197 | 0.870 [0.812, 0.920] | 0.504 [0.433, 0.569] | FAIL |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| s0 | 406 | 206 | 123 | 0.898 [0.841, 0.949] | 0.507 [0.415, 0.584] | FAIL |
| s1 | 405 | 192 | 114 | 0.887 [0.807, 0.949] | 0.475 [0.390, 0.557] | FAIL |
| s2 | 414 | 221 | 134 | 0.829 [0.734, 0.907] | 0.534 [0.450, 0.613] | FAIL |
| s3 | 401 | 199 | 121 | 0.871 [0.806, 0.930] | 0.498 [0.419, 0.579] | FAIL |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| parallel_peer_swap | 316 | 213 | 63 | 0.803 [0.720, 0.870] | 0.675 [0.575, 0.769] | FAIL |
| plant_loop_mapping | 160 | 51 | 20 | 1.000 [1.000, 1.000] | 0.320 [0.199, 0.487] | PASS |
| same_medium_branch | 302 | 119 | 31 | 0.869 [0.741, 0.955] | 0.405 [0.289, 0.519] | FAIL |
| sensor_mapping | 320 | 297 | 65 | 0.842 [0.745, 0.940] | 0.928 [0.866, 0.972] | FAIL |
| vav_zone_swap | 320 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| wrong_ahu_mapping | 208 | 138 | 18 | 0.986 [0.907, 1.000] | 0.663 [0.302, 0.814] | PASS |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| ahu_sat | 56 | 37 | 12 | 0.919 [0.795, 1.000] | 0.661 [0.431, 0.881] | FAIL |
| ahu_vav | 208 | 138 | 18 | 0.986 [0.907, 1.000] | 0.663 [0.302, 0.814] | PASS |
| branch_coil | 302 | 119 | 31 | 0.869 [0.741, 0.955] | 0.405 [0.289, 0.519] | FAIL |
| coil_ahu | 104 | 42 | 14 | 0.881 [0.731, 0.978] | 0.404 [0.248, 0.517] | FAIL |
| coil_vav | 192 | 155 | 45 | 0.761 [0.669, 0.843] | 0.807 [0.743, 0.883] | FAIL |
| loop_branch | 160 | 51 | 20 | 1.000 [1.000, 1.000] | 0.320 [0.199, 0.487] | PASS |
| loop_pump | 12 | 12 | 3 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | insufficient |
| loop_source | 8 | 4 | 1 | 1.000 [1.000, 1.000] | 0.500 [0.500, 0.500] | insufficient |
| vav_dat | 264 | 260 | 53 | 0.831 [0.731, 0.943] | 0.985 [0.966, 0.997] | FAIL |
| vav_zone | 320 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

Cells (season x family x slot): 40; PASS: 7, INCONCLUSIVE: 3, FAIL: 17, insufficient: 13

Calibration (answered verdicts), ECE = 0.106 over n=818

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 818 | 0.970 | 0.864 |

Calibration (ALL crossed verdicts, answered or flagged), ECE = 0.106 over n=818

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 818 | 0.970 | 0.864 |

### C3 precise abstention

| bucket | episodes | resolvable | share | coverage of resolvable | status |
| --- | --- | --- | --- | --- | --- |
| season=s0 | 406 | 31 | 0.08 | 0.903 [0.737, 1.000] | n/a (resolvable share < 30%) |
| season=s1 | 405 | 26 | 0.06 | 0.962 [0.864, 1.000] | n/a (resolvable share < 30%) |
| season=s2 | 414 | 33 | 0.08 | 0.970 [0.900, 1.000] | n/a (resolvable share < 30%) |
| season=s3 | 401 | 26 | 0.06 | 1.000 [1.000, 1.000] | n/a (resolvable share < 30%) |
| slot=ahu_sat | 56 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=ahu_vav | 208 | 22 | 0.11 | 1.000 [1.000, 1.000] | n/a (resolvable share < 30%) |
| slot=branch_coil | 302 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=coil_ahu | 104 | 5 | 0.05 | 0.000 [0.000, 0.000] | n/a (resolvable share < 30%) |
| slot=coil_vav | 192 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_branch | 160 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_pump | 12 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_source | 8 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_dat | 264 | 89 | 0.34 | 1.000 [1.000, 1.000] | PASS |
| slot=vav_zone | 320 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 0.994 [0.982, 1.000] vs answered 0.874 [0.818, 0.922]; margin 0.120 [0.071, 0.177] -> PASS (flagged n=808, answered n=818)

(c) coverage of resolvable cases lost to flags: 0.043 [0.000, 0.129] of 116 resolvable episodes

**C3 status: PASS** (a: PASS)

### C4 knows its limits: 33 of 40 conditions are not C2-PASS; violations (flagged < 90%): 29 -> **FAIL**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| s0|parallel_peer_swap|coil_ahu | FAIL | 13 | 27 | 0.49 | NO |
| s0|parallel_peer_swap|coil_vav | FAIL | 46 | 55 | 0.17 | NO |
| s0|parallel_peer_swap|loop_pump | insufficient | 2 | 2 | 0.00 | NO |
| s0|parallel_peer_swap|loop_source | insufficient | 2 | 3 | 0.50 | NO |
| s0|same_medium_branch|branch_coil | INCONCLUSIVE | 30 | 77 | 0.60 | NO |
| s0|sensor_mapping|ahu_sat | FAIL | 10 | 15 | 0.35 | NO |
| s0|sensor_mapping|vav_dat | FAIL | 58 | 60 | 0.03 | NO |
| s0|vav_zone_swap|vav_zone | insufficient | 0 | 70 | 1.00 | yes |
| s1|parallel_peer_swap|coil_ahu | FAIL | 11 | 31 | 0.66 | NO |
| s1|parallel_peer_swap|coil_vav | FAIL | 24 | 38 | 0.35 | NO |
| s1|parallel_peer_swap|loop_pump | insufficient | 4 | 4 | 0.00 | NO |
| s1|parallel_peer_swap|loop_source | insufficient | 0 | 1 | nan | NO |
| s1|same_medium_branch|branch_coil | FAIL | 31 | 72 | 0.56 | NO |
| s1|sensor_mapping|ahu_sat | FAIL | 9 | 14 | 0.32 | NO |
| s1|sensor_mapping|vav_dat | FAIL | 64 | 64 | 0.00 | NO |
| s1|vav_zone_swap|vav_zone | insufficient | 0 | 88 | 1.00 | yes |
| s1|wrong_ahu_mapping|ahu_vav | INCONCLUSIVE | 34 | 48 | 0.30 | NO |
| s2|parallel_peer_swap|coil_ahu | FAIL | 9 | 23 | 0.64 | NO |
| s2|parallel_peer_swap|coil_vav | FAIL | 43 | 49 | 0.13 | NO |
| s2|parallel_peer_swap|loop_pump | insufficient | 4 | 4 | 0.00 | NO |
| s2|parallel_peer_swap|loop_source | insufficient | 1 | 2 | 0.50 | NO |
| s2|same_medium_branch|branch_coil | FAIL | 24 | 75 | 0.67 | NO |
| s2|sensor_mapping|ahu_sat | FAIL | 13 | 17 | 0.24 | NO |
| s2|sensor_mapping|vav_dat | FAIL | 70 | 70 | 0.00 | NO |
| s2|vav_zone_swap|vav_zone | insufficient | 0 | 70 | 1.00 | yes |
| s3|parallel_peer_swap|coil_vav | FAIL | 42 | 50 | 0.15 | NO |
| s3|parallel_peer_swap|loop_pump | insufficient | 2 | 2 | 0.00 | NO |
| s3|parallel_peer_swap|loop_source | insufficient | 1 | 2 | 0.50 | NO |
| s3|same_medium_branch|branch_coil | FAIL | 34 | 78 | 0.56 | NO |
| s3|sensor_mapping|ahu_sat | insufficient | 5 | 10 | 0.50 | NO |
| s3|sensor_mapping|vav_dat | FAIL | 68 | 70 | 0.03 | NO |
| s3|vav_zone_swap|vav_zone | insufficient | 0 | 92 | 1.00 | yes |
| s3|wrong_ahu_mapping|ahu_vav | INCONCLUSIVE | 24 | 36 | 0.33 | NO |

## Layer `legacy` (1626 episodes per policy, 331 clusters)

### Headline per policy (same layer; class-balanced; 95% cluster-bootstrap CI)

| policy | answered coverage | accuracy among answered | readings among answered |
| --- | --- | --- | --- |
| active | 0.073 [0.044, 0.108] | 0.992 [0.971, 1.000] | 7.9 [3.4, 9.8] |
| frozen | 0.114 [0.066, 0.175] | 0.963 [0.907, 0.995] | 5.6 [4.2, 8.1] |
| random | 0.095 [0.071, 0.120] | 0.928 [0.880, 0.967] | 13.1 [11.8, 14.4] |
| traversal | 0.257 [0.201, 0.317] | 0.969 [0.934, 0.994] | 7.8 [6.7, 9.0] |
| traversal_block | 0.255 [0.197, 0.317] | 0.971 [0.938, 0.996] | 7.9 [6.9, 9.2] |

### C1 efficiency: readings saved by active vs baseline (paired, among episodes answered by both)

| baseline | pairs | readings saved | coverage active - base | status |
| --- | --- | --- | --- | --- |
| random | 50 | 9.09 [7.82, 10.24] | -0.021 [-0.056, 0.016] | FAIL |
| traversal_block | 77 | 4.14 [3.29, 5.13] | -0.181 [-0.252, -0.116] | FAIL |
| traversal | 72 | 5.91 [4.34, 7.50] | -0.183 [-0.257, -0.117] | FAIL |
| frozen | 74 | 0.35 [-0.01, 0.74] | -0.040 [-0.104, 0.015] | FAIL |

### C2 honest confidence (nominal 0.95; PASS: point>=0.93 and lower>=0.90; cells need >=8 answered and >=5 clusters)

| all | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| all | 1626 | 120 | 40 | 0.992 [0.971, 1.000] | 0.073 [0.044, 0.108] | PASS |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| s0 | 406 | 23 | 19 | 1.000 [1.000, 1.000] | 0.057 [0.032, 0.084] | PASS |
| s1 | 405 | 38 | 22 | 1.000 [1.000, 1.000] | 0.093 [0.047, 0.148] | PASS |
| s2 | 414 | 29 | 22 | 1.000 [1.000, 1.000] | 0.070 [0.037, 0.111] | PASS |
| s3 | 401 | 30 | 18 | 0.967 [0.875, 1.000] | 0.074 [0.036, 0.124] | INCONCLUSIVE |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| parallel_peer_swap | 316 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| plant_loop_mapping | 160 | 26 | 14 | 1.000 [1.000, 1.000] | 0.161 [0.079, 0.250] | PASS |
| same_medium_branch | 302 | 24 | 3 | 1.000 [1.000, 1.000] | 0.085 [0.000, 0.191] | insufficient |
| sensor_mapping | 320 | 49 | 15 | 1.000 [1.000, 1.000] | 0.153 [0.091, 0.229] | PASS |
| vav_zone_swap | 320 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| wrong_ahu_mapping | 208 | 21 | 8 | 0.952 [0.799, 1.000] | 0.101 [0.029, 0.256] | INCONCLUSIVE |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| ahu_sat | 56 | 2 | 1 | 1.000 [1.000, 1.000] | 0.036 [0.000, 0.125] | insufficient |
| ahu_vav | 208 | 21 | 8 | 0.952 [0.799, 1.000] | 0.101 [0.029, 0.256] | INCONCLUSIVE |
| branch_coil | 302 | 24 | 3 | 1.000 [1.000, 1.000] | 0.085 [0.000, 0.191] | insufficient |
| coil_ahu | 104 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| coil_vav | 192 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| loop_branch | 160 | 26 | 14 | 1.000 [1.000, 1.000] | 0.161 [0.079, 0.250] | PASS |
| loop_pump | 12 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| loop_source | 8 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| vav_dat | 264 | 47 | 14 | 1.000 [1.000, 1.000] | 0.178 [0.108, 0.274] | PASS |
| vav_zone | 320 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

Cells (season x family x slot): 40; PASS: 5, INCONCLUSIVE: 0, FAIL: 0, insufficient: 35

Calibration (answered verdicts), ECE = 0.023 over n=120

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 120 | 0.971 | 0.994 |

Calibration (ALL crossed verdicts, answered or flagged), ECE = 0.106 over n=818

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 818 | 0.970 | 0.864 |

### C3 precise abstention

| bucket | episodes | resolvable | share | coverage of resolvable | status |
| --- | --- | --- | --- | --- | --- |
| season=s0 | 406 | 31 | 0.08 | 0.387 [0.171, 0.611] | n/a (resolvable share < 30%) |
| season=s1 | 405 | 26 | 0.06 | 0.346 [0.150, 0.591] | n/a (resolvable share < 30%) |
| season=s2 | 414 | 33 | 0.08 | 0.333 [0.148, 0.567] | n/a (resolvable share < 30%) |
| season=s3 | 401 | 26 | 0.06 | 0.231 [0.083, 0.455] | n/a (resolvable share < 30%) |
| slot=ahu_sat | 56 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=ahu_vav | 208 | 22 | 0.11 | 0.273 [0.000, 0.636] | n/a (resolvable share < 30%) |
| slot=branch_coil | 302 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=coil_ahu | 104 | 5 | 0.05 | 0.000 [0.000, 0.000] | n/a (resolvable share < 30%) |
| slot=coil_vav | 192 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_branch | 160 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_pump | 12 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_source | 8 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_dat | 264 | 89 | 0.34 | 0.360 [0.169, 0.593] | PASS |
| slot=vav_zone | 320 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 0.953 [0.926, 0.976] vs answered 0.686 [0.490, 0.847]; margin 0.267 [0.106, 0.463] -> PASS (flagged n=1506, answered n=120)

(c) coverage of resolvable cases lost to flags: 0.672 [0.477, 0.831] of 116 resolvable episodes

**C3 status: PASS** (a: PASS)

### C4 knows its limits: 35 of 40 conditions are not C2-PASS; violations (flagged < 90%): 6 -> **FAIL**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| s0|parallel_peer_swap|coil_ahu | insufficient | 0 | 27 | 1.00 | yes |
| s0|parallel_peer_swap|coil_vav | insufficient | 0 | 55 | 1.00 | yes |
| s0|parallel_peer_swap|loop_pump | insufficient | 0 | 2 | 1.00 | yes |
| s0|parallel_peer_swap|loop_source | insufficient | 0 | 3 | 1.00 | yes |
| s0|plant_loop_mapping|loop_branch | insufficient | 4 | 41 | 0.90 | yes |
| s0|same_medium_branch|branch_coil | insufficient | 1 | 77 | 0.99 | yes |
| s0|sensor_mapping|ahu_sat | insufficient | 1 | 15 | 0.95 | yes |
| s0|vav_zone_swap|vav_zone | insufficient | 0 | 70 | 1.00 | yes |
| s0|wrong_ahu_mapping|ahu_vav | insufficient | 5 | 56 | 0.91 | yes |
| s1|parallel_peer_swap|coil_ahu | insufficient | 0 | 31 | 1.00 | yes |
| s1|parallel_peer_swap|coil_vav | insufficient | 0 | 38 | 1.00 | yes |
| s1|parallel_peer_swap|loop_pump | insufficient | 0 | 4 | 1.00 | yes |
| s1|parallel_peer_swap|loop_source | insufficient | 0 | 1 | nan | NO |
| s1|same_medium_branch|branch_coil | insufficient | 9 | 72 | 0.87 | NO |
| s1|sensor_mapping|ahu_sat | insufficient | 0 | 14 | 1.00 | yes |
| s1|vav_zone_swap|vav_zone | insufficient | 0 | 88 | 1.00 | yes |
| s1|wrong_ahu_mapping|ahu_vav | insufficient | 5 | 48 | 0.91 | yes |
| s2|parallel_peer_swap|coil_ahu | insufficient | 0 | 23 | 1.00 | yes |
| s2|parallel_peer_swap|coil_vav | insufficient | 0 | 49 | 1.00 | yes |
| s2|parallel_peer_swap|loop_pump | insufficient | 0 | 4 | 1.00 | yes |
| s2|parallel_peer_swap|loop_source | insufficient | 0 | 2 | 1.00 | yes |
| s2|plant_loop_mapping|loop_branch | insufficient | 7 | 36 | 0.81 | NO |
| s2|same_medium_branch|branch_coil | insufficient | 6 | 75 | 0.91 | yes |
| s2|sensor_mapping|ahu_sat | insufficient | 1 | 17 | 0.94 | yes |
| s2|vav_zone_swap|vav_zone | insufficient | 0 | 70 | 1.00 | yes |
| s2|wrong_ahu_mapping|ahu_vav | insufficient | 7 | 68 | 0.90 | NO |
| s3|parallel_peer_swap|coil_ahu | insufficient | 0 | 23 | 1.00 | yes |
| s3|parallel_peer_swap|coil_vav | insufficient | 0 | 50 | 1.00 | yes |
| s3|parallel_peer_swap|loop_pump | insufficient | 0 | 2 | 1.00 | yes |
| s3|parallel_peer_swap|loop_source | insufficient | 0 | 2 | 1.00 | yes |
| s3|plant_loop_mapping|loop_branch | insufficient | 4 | 38 | 0.91 | yes |
| s3|same_medium_branch|branch_coil | insufficient | 8 | 78 | 0.89 | NO |
| s3|sensor_mapping|ahu_sat | insufficient | 0 | 10 | 1.00 | yes |
| s3|vav_zone_swap|vav_zone | insufficient | 0 | 92 | 1.00 | yes |
| s3|wrong_ahu_mapping|ahu_vav | insufficient | 4 | 36 | 0.89 | NO |

## Layer `new` (1626 episodes per policy, 331 clusters)

### Headline per policy (same layer; class-balanced; 95% cluster-bootstrap CI)

| policy | answered coverage | accuracy among answered | readings among answered |
| --- | --- | --- | --- |
| active | 0.042 [0.024, 0.064] | 0.986 [0.957, 1.000] | 3.2 [2.7, 3.9] |
| frozen | 0.002 [0.000, 0.004] | 1.000 [1.000, 1.000] | 3.0 [0.0, 7.0] |
| random | 0.014 [0.006, 0.023] | 1.000 [1.000, 1.000] | 15.5 [13.4, 17.6] |
| traversal | 0.008 [0.001, 0.016] | 1.000 [1.000, 1.000] | 12.7 [1.6, 16.3] |
| traversal_block | 0.028 [0.013, 0.045] | 0.956 [0.852, 1.000] | 6.7 [4.5, 10.8] |

### C1 efficiency: readings saved by active vs baseline (paired, among episodes answered by both)

| baseline | pairs | readings saved | coverage active - base | status |
| --- | --- | --- | --- | --- |
| random | 12 | 9.25 [8.25, 10.06] | 0.028 [0.011, 0.049] | PASS |
| traversal_block | 0 | n/a | n/a | n/a |
| traversal | 0 | n/a | n/a | n/a |
| frozen | 0 | n/a | n/a | n/a |

### C2 honest confidence (nominal 0.95; PASS: point>=0.93 and lower>=0.90; cells need >=8 answered and >=5 clusters)

| all | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| all | 1626 | 69 | 22 | 0.986 [0.957, 1.000] | 0.042 [0.024, 0.064] | PASS |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| s0 | 406 | 19 | 13 | 1.000 [1.000, 1.000] | 0.047 [0.022, 0.076] | PASS |
| s1 | 405 | 17 | 12 | 1.000 [1.000, 1.000] | 0.042 [0.018, 0.072] | PASS |
| s2 | 414 | 18 | 14 | 1.000 [1.000, 1.000] | 0.044 [0.022, 0.069] | PASS |
| s3 | 401 | 15 | 12 | 0.935 [0.815, 1.000] | 0.037 [0.017, 0.063] | INCONCLUSIVE |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| parallel_peer_swap | 316 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| plant_loop_mapping | 160 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| same_medium_branch | 302 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| sensor_mapping | 320 | 57 | 17 | 0.982 [0.951, 1.000] | 0.178 [0.102, 0.259] | PASS |
| vav_zone_swap | 320 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| wrong_ahu_mapping | 208 | 12 | 5 | 1.000 [1.000, 1.000] | 0.058 [0.012, 0.182] | PASS |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| ahu_sat | 56 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| ahu_vav | 208 | 12 | 5 | 1.000 [1.000, 1.000] | 0.058 [0.012, 0.182] | PASS |
| branch_coil | 302 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| coil_ahu | 104 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| coil_vav | 192 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| loop_branch | 160 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| loop_pump | 12 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| loop_source | 8 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| vav_dat | 264 | 57 | 17 | 0.982 [0.952, 1.000] | 0.216 [0.127, 0.308] | PASS |
| vav_zone | 320 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

Cells (season x family x slot): 40; PASS: 3, INCONCLUSIVE: 0, FAIL: 1, insufficient: 36

Calibration (answered verdicts), ECE = 0.041 over n=69

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.90,0.95) | 46 | 0.934 | 0.978 |
| [0.95,1.00) | 23 | 0.966 | 1.000 |

Calibration (ALL crossed verdicts, answered or flagged), ECE = 0.077 over n=549

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.50,0.60) | 7 | 0.532 | 0.260 |
| [0.60,0.70) | 49 | 0.651 | 0.790 |
| [0.70,0.80) | 64 | 0.755 | 0.686 |
| [0.80,0.90) | 96 | 0.872 | 0.676 |
| [0.90,0.95) | 138 | 0.920 | 0.985 |
| [0.95,1.00) | 183 | 0.976 | 0.970 |

### C3 precise abstention

| bucket | episodes | resolvable | share | coverage of resolvable | status |
| --- | --- | --- | --- | --- | --- |
| season=s0 | 406 | 31 | 0.08 | 0.548 [0.345, 0.743] | n/a (resolvable share < 30%) |
| season=s1 | 405 | 26 | 0.06 | 0.462 [0.222, 0.714] | n/a (resolvable share < 30%) |
| season=s2 | 414 | 33 | 0.08 | 0.485 [0.293, 0.667] | n/a (resolvable share < 30%) |
| season=s3 | 401 | 26 | 0.06 | 0.423 [0.222, 0.636] | n/a (resolvable share < 30%) |
| slot=ahu_sat | 56 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=ahu_vav | 208 | 22 | 0.11 | 0.545 [0.157, 0.917] | n/a (resolvable share < 30%) |
| slot=branch_coil | 302 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=coil_ahu | 104 | 5 | 0.05 | 0.000 [0.000, 0.000] | n/a (resolvable share < 30%) |
| slot=coil_vav | 192 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_branch | 160 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_pump | 12 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_source | 8 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_dat | 264 | 89 | 0.34 | 0.494 [0.343, 0.651] | PASS |
| slot=vav_zone | 320 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 0.966 [0.948, 0.982] vs answered 0.191 [0.047, 0.391]; margin 0.775 [0.573, 0.924] -> PASS (flagged n=1557, answered n=69)

(c) coverage of resolvable cases lost to flags: 0.517 [0.378, 0.660] of 116 resolvable episodes

**C3 status: PASS** (a: PASS)

### C4 knows its limits: 37 of 40 conditions are not C2-PASS; violations (flagged < 90%): 2 -> **FAIL**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| s0|parallel_peer_swap|coil_ahu | insufficient | 0 | 27 | 1.00 | yes |
| s0|parallel_peer_swap|coil_vav | insufficient | 0 | 55 | 1.00 | yes |
| s0|parallel_peer_swap|loop_pump | insufficient | 0 | 2 | 1.00 | yes |
| s0|parallel_peer_swap|loop_source | insufficient | 0 | 3 | 1.00 | yes |
| s0|plant_loop_mapping|loop_branch | insufficient | 0 | 41 | 1.00 | yes |
| s0|same_medium_branch|branch_coil | insufficient | 0 | 77 | 1.00 | yes |
| s0|sensor_mapping|ahu_sat | insufficient | 0 | 15 | 1.00 | yes |
| s0|vav_zone_swap|vav_zone | insufficient | 0 | 70 | 1.00 | yes |
| s0|wrong_ahu_mapping|ahu_vav | insufficient | 3 | 56 | 0.94 | yes |
| s1|parallel_peer_swap|coil_ahu | insufficient | 0 | 31 | 1.00 | yes |
| s1|parallel_peer_swap|coil_vav | insufficient | 0 | 38 | 1.00 | yes |
| s1|parallel_peer_swap|loop_pump | insufficient | 0 | 4 | 1.00 | yes |
| s1|parallel_peer_swap|loop_source | insufficient | 0 | 1 | nan | NO |
| s1|plant_loop_mapping|loop_branch | insufficient | 0 | 45 | 1.00 | yes |
| s1|same_medium_branch|branch_coil | insufficient | 0 | 72 | 1.00 | yes |
| s1|sensor_mapping|ahu_sat | insufficient | 0 | 14 | 1.00 | yes |
| s1|vav_zone_swap|vav_zone | insufficient | 0 | 88 | 1.00 | yes |
| s1|wrong_ahu_mapping|ahu_vav | insufficient | 2 | 48 | 0.96 | yes |
| s2|parallel_peer_swap|coil_ahu | insufficient | 0 | 23 | 1.00 | yes |
| s2|parallel_peer_swap|coil_vav | insufficient | 0 | 49 | 1.00 | yes |
| s2|parallel_peer_swap|loop_pump | insufficient | 0 | 4 | 1.00 | yes |
| s2|parallel_peer_swap|loop_source | insufficient | 0 | 2 | 1.00 | yes |
| s2|plant_loop_mapping|loop_branch | insufficient | 0 | 36 | 1.00 | yes |
| s2|same_medium_branch|branch_coil | insufficient | 0 | 75 | 1.00 | yes |
| s2|sensor_mapping|ahu_sat | insufficient | 0 | 17 | 1.00 | yes |
| s2|vav_zone_swap|vav_zone | insufficient | 0 | 70 | 1.00 | yes |
| s2|wrong_ahu_mapping|ahu_vav | insufficient | 6 | 68 | 0.91 | yes |
| s3|parallel_peer_swap|coil_ahu | insufficient | 0 | 23 | 1.00 | yes |
| s3|parallel_peer_swap|coil_vav | insufficient | 0 | 50 | 1.00 | yes |
| s3|parallel_peer_swap|loop_pump | insufficient | 0 | 2 | 1.00 | yes |
| s3|parallel_peer_swap|loop_source | insufficient | 0 | 2 | 1.00 | yes |
| s3|plant_loop_mapping|loop_branch | insufficient | 0 | 38 | 1.00 | yes |
| s3|same_medium_branch|branch_coil | insufficient | 0 | 78 | 1.00 | yes |
| s3|sensor_mapping|ahu_sat | insufficient | 0 | 10 | 1.00 | yes |
| s3|sensor_mapping|vav_dat | FAIL | 14 | 70 | 0.80 | NO |
| s3|vav_zone_swap|vav_zone | insufficient | 0 | 92 | 1.00 | yes |
| s3|wrong_ahu_mapping|ahu_vav | insufficient | 1 | 36 | 0.97 | yes |
