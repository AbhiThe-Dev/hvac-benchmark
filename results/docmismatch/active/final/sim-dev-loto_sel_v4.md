sim-dev-loto_sel_v4: 1626 episodes (331 clusters = event groups); config variant=sel, tau=0.95, primary setting `visit`; elapsed 370s; info={"sys03_psz_ac": {"beta": {"ahu_sat": 1.0, "ahu_vav": 1.0, "branch_coil": 0.1, "coil_ahu": 1.0, "coil_vav": 1.0, "loop_branch": 0.2, "loop_pump": 1.0, "loop_source": 0.35, "vav_dat": 1.0, "vav_zone": 1.0}, "n_outer": 2320, "n_inner": 13940}, "sys07_vav_reheat": {"beta": {"ahu_sat": 0.7, "ahu_vav": 0.5, "branch_coil": 0.1, "coil_ahu": 1.0, "coil_vav": 1.0, "loop_branch": 0.2, "loop_pump": 1.0, "loo

# Readiness evaluation: sim-dev-loto_sel_v4

## Layer `none` (1626 episodes per policy, 331 clusters)

### Headline per policy (same layer; class-balanced; 95% cluster-bootstrap CI)

| policy | answered coverage | accuracy among answered | readings among answered |
| --- | --- | --- | --- |
| active | 0.482 [0.408, 0.554] | 0.864 [0.809, 0.914] | 4.1 [3.6, 4.6] |
| frozen | 0.474 [0.398, 0.546] | 0.840 [0.774, 0.894] | 4.5 [3.9, 5.1] |
| random | 0.270 [0.224, 0.319] | 0.920 [0.887, 0.948] | 12.3 [11.4, 13.1] |
| traversal | 0.316 [0.246, 0.391] | 0.954 [0.906, 0.988] | 6.6 [4.8, 8.3] |
| traversal_block | 0.321 [0.250, 0.397] | 0.956 [0.909, 0.990] | 6.6 [4.9, 8.4] |

### C1 efficiency: readings saved by active vs baseline (paired, among episodes answered by both)

| baseline | pairs | readings saved | coverage active - base | status |
| --- | --- | --- | --- | --- |
| random | 422 | 9.15 [8.20, 9.97] | 0.212 [0.170, 0.253] | PASS |
| traversal_block | 516 | 3.58 [1.86, 5.39] | 0.162 [0.126, 0.203] | PASS |
| traversal | 510 | 3.59 [1.89, 5.38] | 0.166 [0.130, 0.207] | PASS |
| frozen | 754 | 0.64 [0.38, 0.95] | 0.009 [-0.001, 0.019] | PASS |

### C2 honest confidence (nominal 0.95; PASS: point>=0.93 and lower>=0.90; cells need >=8 answered and >=5 clusters)

| all | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| all | 1626 | 784 | 190 | 0.864 [0.809, 0.914] | 0.482 [0.408, 0.554] | FAIL |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| s0 | 406 | 204 | 121 | 0.892 [0.829, 0.946] | 0.502 [0.419, 0.584] | FAIL |
| s1 | 405 | 183 | 112 | 0.881 [0.811, 0.937] | 0.452 [0.370, 0.530] | FAIL |
| s2 | 414 | 214 | 129 | 0.814 [0.721, 0.893] | 0.517 [0.437, 0.597] | FAIL |
| s3 | 401 | 183 | 113 | 0.876 [0.801, 0.936] | 0.457 [0.379, 0.536] | FAIL |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| clean | 800 | 397 | 93 | n/a | n/a | insufficient |
| parallel_peer_swap | 160 | 124 | 32 | n/a | n/a | insufficient |
| plant_loop_mapping | 82 | 21 | 10 | n/a | n/a | insufficient |
| same_medium_branch | 160 | 16 | 11 | n/a | n/a | insufficient |
| sensor_mapping | 160 | 151 | 32 | n/a | n/a | insufficient |
| vav_zone_swap | 160 | 0 | 0 | n/a | n/a | insufficient |
| wrong_ahu_mapping | 104 | 75 | 12 | n/a | n/a | insufficient |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| ahu_sat | 56 | 38 | 11 | 0.921 [0.792, 1.000] | 0.679 [0.425, 0.896] | FAIL |
| ahu_vav | 208 | 153 | 19 | 0.967 [0.850, 1.000] | 0.736 [0.395, 0.862] | INCONCLUSIVE |
| branch_coil | 302 | 35 | 20 | 0.729 [0.459, 0.949] | 0.117 [0.064, 0.199] | FAIL |
| coil_ahu | 104 | 57 | 16 | 0.912 [0.801, 1.000] | 0.548 [0.400, 0.676] | FAIL |
| coil_vav | 192 | 170 | 47 | 0.735 [0.645, 0.818] | 0.885 [0.826, 0.938] | FAIL |
| loop_branch | 160 | 51 | 20 | 1.000 [1.000, 1.000] | 0.320 [0.199, 0.487] | PASS |
| loop_pump | 12 | 12 | 3 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | insufficient |
| loop_source | 8 | 4 | 1 | 1.000 [1.000, 1.000] | 0.500 [0.500, 0.500] | insufficient |
| vav_dat | 264 | 264 | 53 | 0.848 [0.758, 0.954] | 1.000 [1.000, 1.000] | FAIL |
| vav_zone | 320 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

Cells (season x family x slot): 79; PASS: 0, INCONCLUSIVE: 0, FAIL: 0, insufficient: 79

Calibration (answered verdicts), ECE = 0.112 over n=784

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 784 | 0.975 | 0.863 |

Calibration (ALL crossed verdicts, answered or flagged), ECE = 0.112 over n=784

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 784 | 0.975 | 0.863 |

### C3 precise abstention

| bucket | episodes | resolvable | share | coverage of resolvable | status |
| --- | --- | --- | --- | --- | --- |
| season=s0 | 406 | 22 | 0.05 | 1.000 [1.000, 1.000] | n/a (resolvable share < 30%) |
| season=s1 | 405 | 18 | 0.04 | 0.833 [0.538, 1.000] | n/a (resolvable share < 30%) |
| season=s2 | 414 | 26 | 0.06 | 0.962 [0.857, 1.000] | n/a (resolvable share < 30%) |
| season=s3 | 401 | 19 | 0.05 | 1.000 [1.000, 1.000] | n/a (resolvable share < 30%) |
| slot=ahu_sat | 56 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=ahu_vav | 208 | 26 | 0.12 | 1.000 [1.000, 1.000] | n/a (resolvable share < 30%) |
| slot=branch_coil | 302 | 4 | 0.01 | 0.000 [0.000, 0.000] | n/a (resolvable share < 30%) |
| slot=coil_ahu | 104 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=coil_vav | 192 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_branch | 160 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_pump | 12 | 8 | 0.67 | 1.000 [1.000, 1.000] | PASS |
| slot=loop_source | 8 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_dat | 264 | 47 | 0.18 | 1.000 [1.000, 1.000] | n/a (resolvable share < 30%) |
| slot=vav_zone | 320 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 0.995 [0.985, 1.000] vs answered 0.902 [0.850, 0.943]; margin 0.093 [0.051, 0.147] -> PASS (flagged n=842, answered n=784)

(c) coverage of resolvable cases lost to flags: 0.047 [0.000, 0.158] of 85 resolvable episodes

**C3 status: PASS** (a: PASS)

### C4 knows its limits: 79 of 79 conditions are not C2-PASS; violations (flagged < 90%): 79 -> **FAIL**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| s0|clean|ahu_sat | insufficient | 3 | 5 | nan | NO |
| s0|clean|ahu_vav | insufficient | 25 | 31 | nan | NO |
| s0|clean|branch_coil | insufficient | 9 | 37 | nan | NO |
| s0|clean|coil_ahu | insufficient | 6 | 15 | nan | NO |
| s0|clean|coil_vav | insufficient | 29 | 29 | nan | NO |
| s0|clean|loop_branch | insufficient | 5 | 21 | nan | NO |
| s0|clean|loop_pump | insufficient | 1 | 1 | nan | NO |
| s0|clean|loop_source | insufficient | 2 | 2 | nan | NO |
| s0|clean|vav_dat | insufficient | 29 | 29 | nan | NO |
| s0|clean|vav_zone | insufficient | 0 | 34 | nan | NO |
| s0|parallel_peer_swap|coil_ahu | insufficient | 11 | 12 | nan | NO |
| s0|parallel_peer_swap|coil_vav | insufficient | 19 | 26 | nan | NO |
| s0|parallel_peer_swap|loop_pump | insufficient | 1 | 1 | nan | NO |
| s0|parallel_peer_swap|loop_source | insufficient | 0 | 1 | nan | NO |
| s0|plant_loop_mapping|loop_branch | insufficient | 4 | 20 | nan | NO |
| s0|same_medium_branch|branch_coil | insufficient | 4 | 40 | nan | NO |
| s0|sensor_mapping|ahu_sat | insufficient | 7 | 10 | nan | NO |
| s0|sensor_mapping|vav_dat | insufficient | 31 | 31 | nan | NO |
| s0|vav_zone_swap|vav_zone | insufficient | 0 | 36 | nan | NO |
| s0|wrong_ahu_mapping|ahu_vav | insufficient | 18 | 25 | nan | NO |
| s1|clean|ahu_sat | insufficient | 6 | 9 | nan | NO |
| s1|clean|ahu_vav | insufficient | 15 | 20 | nan | NO |
| s1|clean|branch_coil | insufficient | 4 | 34 | nan | NO |
| s1|clean|coil_ahu | insufficient | 4 | 14 | nan | NO |
| s1|clean|coil_vav | insufficient | 18 | 18 | nan | NO |
| s1|clean|loop_branch | insufficient | 9 | 23 | nan | NO |
| s1|clean|loop_pump | insufficient | 1 | 1 | nan | NO |
| s1|clean|vav_dat | insufficient | 30 | 30 | nan | NO |
| s1|clean|vav_zone | insufficient | 0 | 47 | nan | NO |
| s1|parallel_peer_swap|coil_ahu | insufficient | 11 | 17 | nan | NO |
| s1|parallel_peer_swap|coil_vav | insufficient | 12 | 20 | nan | NO |
| s1|parallel_peer_swap|loop_pump | insufficient | 3 | 3 | nan | NO |
| s1|parallel_peer_swap|loop_source | insufficient | 0 | 1 | nan | NO |
| s1|plant_loop_mapping|loop_branch | insufficient | 6 | 22 | nan | NO |
| s1|same_medium_branch|branch_coil | insufficient | 4 | 38 | nan | NO |
| s1|sensor_mapping|ahu_sat | insufficient | 4 | 5 | nan | NO |
| s1|sensor_mapping|vav_dat | insufficient | 34 | 34 | nan | NO |
| s1|vav_zone_swap|vav_zone | insufficient | 0 | 41 | nan | NO |
| s1|wrong_ahu_mapping|ahu_vav | insufficient | 22 | 28 | nan | NO |
| s2|clean|ahu_sat | insufficient | 5 | 8 | nan | NO |
| s2|clean|ahu_vav | insufficient | 25 | 35 | nan | NO |
| s2|clean|branch_coil | insufficient | 2 | 33 | nan | NO |
| s2|clean|coil_ahu | insufficient | 2 | 10 | nan | NO |
| s2|clean|coil_vav | insufficient | 26 | 26 | nan | NO |
| s2|clean|loop_branch | insufficient | 8 | 18 | nan | NO |
| s2|clean|loop_pump | insufficient | 1 | 1 | nan | NO |
| s2|clean|loop_source | insufficient | 1 | 1 | nan | NO |
| s2|clean|vav_dat | insufficient | 38 | 38 | nan | NO |
| s2|clean|vav_zone | insufficient | 0 | 34 | nan | NO |
| s2|parallel_peer_swap|coil_ahu | insufficient | 12 | 13 | nan | NO |
| s2|parallel_peer_swap|coil_vav | insufficient | 21 | 23 | nan | NO |
| s2|parallel_peer_swap|loop_pump | insufficient | 3 | 3 | nan | NO |
| s2|parallel_peer_swap|loop_source | insufficient | 0 | 1 | nan | NO |
| s2|plant_loop_mapping|loop_branch | insufficient | 5 | 18 | nan | NO |
| s2|same_medium_branch|branch_coil | insufficient | 4 | 42 | nan | NO |
| s2|sensor_mapping|ahu_sat | insufficient | 6 | 9 | nan | NO |
| s2|sensor_mapping|vav_dat | insufficient | 32 | 32 | nan | NO |
| s2|vav_zone_swap|vav_zone | insufficient | 0 | 36 | nan | NO |
| s2|wrong_ahu_mapping|ahu_vav | insufficient | 23 | 33 | nan | NO |
| s3|clean|ahu_sat | insufficient | 5 | 6 | nan | NO |
| s3|clean|ahu_vav | insufficient | 13 | 18 | nan | NO |
| s3|clean|branch_coil | insufficient | 4 | 38 | nan | NO |
| s3|clean|coil_ahu | insufficient | 3 | 13 | nan | NO |
| s3|clean|coil_vav | insufficient | 23 | 23 | nan | NO |
| s3|clean|loop_branch | insufficient | 8 | 16 | nan | NO |
| s3|clean|loop_pump | insufficient | 1 | 1 | nan | NO |
| s3|clean|loop_source | insufficient | 1 | 1 | nan | NO |
| s3|clean|vav_dat | insufficient | 35 | 35 | nan | NO |
| s3|clean|vav_zone | insufficient | 0 | 45 | nan | NO |
| s3|parallel_peer_swap|coil_ahu | insufficient | 8 | 10 | nan | NO |
| s3|parallel_peer_swap|coil_vav | insufficient | 22 | 27 | nan | NO |
| s3|parallel_peer_swap|loop_pump | insufficient | 1 | 1 | nan | NO |
| s3|parallel_peer_swap|loop_source | insufficient | 0 | 1 | nan | NO |
| s3|plant_loop_mapping|loop_branch | insufficient | 6 | 22 | nan | NO |
| s3|same_medium_branch|branch_coil | insufficient | 4 | 40 | nan | NO |
| s3|sensor_mapping|ahu_sat | insufficient | 2 | 4 | nan | NO |
| s3|sensor_mapping|vav_dat | insufficient | 35 | 35 | nan | NO |
| s3|vav_zone_swap|vav_zone | insufficient | 0 | 47 | nan | NO |
| s3|wrong_ahu_mapping|ahu_vav | insufficient | 12 | 18 | nan | NO |

## Layer `legacy` (1626 episodes per policy, 331 clusters)

### Headline per policy (same layer; class-balanced; 95% cluster-bootstrap CI)

| policy | answered coverage | accuracy among answered | readings among answered |
| --- | --- | --- | --- |
| active | 0.081 [0.054, 0.114] | 0.948 [0.887, 0.992] | 3.3 [2.2, 4.4] |
| frozen | 0.048 [0.024, 0.077] | 0.924 [0.811, 1.000] | 3.0 [1.6, 3.8] |
| random | 0.012 [0.001, 0.028] | 0.680 [0.222, 0.910] | 11.2 [2.4, 12.0] |
| traversal | 0.123 [0.089, 0.163] | 0.936 [0.844, 0.995] | 6.1 [4.7, 7.7] |
| traversal_block | 0.246 [0.177, 0.319] | 0.958 [0.900, 0.994] | 6.3 [4.1, 8.5] |

### C1 efficiency: readings saved by active vs baseline (paired, among episodes answered by both)

| baseline | pairs | readings saved | coverage active - base | status |
| --- | --- | --- | --- | --- |
| random | 0 | n/a | n/a | n/a |
| traversal_block | 88 | 2.55 [1.70, 3.59] | -0.164 [-0.244, -0.088] | FAIL |
| traversal | 62 | 2.36 [0.09, 3.27] | -0.042 [-0.085, -0.003] | FAIL |
| frozen | 62 | 0.11 [0.01, 0.24] | 0.034 [0.014, 0.054] | PASS |

### C2 honest confidence (nominal 0.95; PASS: point>=0.93 and lower>=0.90; cells need >=8 answered and >=5 clusters)

| all | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| all | 1626 | 133 | 46 | 0.948 [0.887, 0.992] | 0.081 [0.054, 0.114] | INCONCLUSIVE |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| s0 | 406 | 32 | 23 | 0.937 [0.826, 1.000] | 0.079 [0.042, 0.125] | INCONCLUSIVE |
| s1 | 405 | 35 | 25 | 0.942 [0.837, 1.000] | 0.086 [0.050, 0.125] | INCONCLUSIVE |
| s2 | 414 | 38 | 31 | 0.948 [0.868, 1.000] | 0.092 [0.060, 0.130] | INCONCLUSIVE |
| s3 | 401 | 28 | 21 | 0.965 [0.874, 1.000] | 0.069 [0.040, 0.101] | INCONCLUSIVE |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| clean | 800 | 46 | 15 | n/a | n/a | insufficient |
| parallel_peer_swap | 160 | 7 | 2 | n/a | n/a | insufficient |
| plant_loop_mapping | 82 | 16 | 8 | n/a | n/a | insufficient |
| same_medium_branch | 160 | 0 | 0 | n/a | n/a | insufficient |
| sensor_mapping | 160 | 39 | 11 | n/a | n/a | insufficient |
| vav_zone_swap | 160 | 0 | 0 | n/a | n/a | insufficient |
| wrong_ahu_mapping | 104 | 25 | 10 | n/a | n/a | insufficient |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| ahu_sat | 56 | 4 | 2 | 0.750 [0.500, 1.000] | 0.071 [0.000, 0.194] | insufficient |
| ahu_vav | 208 | 55 | 16 | 0.909 [0.739, 1.000] | 0.264 [0.105, 0.542] | FAIL |
| branch_coil | 302 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| coil_ahu | 104 | 7 | 2 | 1.000 [1.000, 1.000] | 0.067 [0.000, 0.219] | insufficient |
| coil_vav | 192 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| loop_branch | 160 | 29 | 15 | 1.000 [1.000, 1.000] | 0.181 [0.091, 0.289] | PASS |
| loop_pump | 12 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| loop_source | 8 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| vav_dat | 264 | 38 | 11 | 0.974 [0.886, 1.000] | 0.144 [0.065, 0.256] | INCONCLUSIVE |
| vav_zone | 320 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

Cells (season x family x slot): 79; PASS: 0, INCONCLUSIVE: 0, FAIL: 0, insufficient: 79

Calibration (answered verdicts), ECE = 0.024 over n=133

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 133 | 0.979 | 0.955 |

Calibration (ALL crossed verdicts, answered or flagged), ECE = 0.112 over n=784

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 784 | 0.975 | 0.863 |

### C3 precise abstention

| bucket | episodes | resolvable | share | coverage of resolvable | status |
| --- | --- | --- | --- | --- | --- |
| season=s0 | 406 | 22 | 0.05 | 0.500 [0.227, 0.786] | n/a (resolvable share < 30%) |
| season=s1 | 405 | 18 | 0.04 | 0.444 [0.190, 0.800] | n/a (resolvable share < 30%) |
| season=s2 | 414 | 26 | 0.06 | 0.577 [0.345, 0.846] | n/a (resolvable share < 30%) |
| season=s3 | 401 | 19 | 0.05 | 0.526 [0.250, 0.800] | n/a (resolvable share < 30%) |
| slot=ahu_sat | 56 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=ahu_vav | 208 | 26 | 0.12 | 0.923 [0.714, 1.000] | n/a (resolvable share < 30%) |
| slot=branch_coil | 302 | 4 | 0.01 | 0.000 [0.000, 0.000] | n/a (resolvable share < 30%) |
| slot=coil_ahu | 104 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=coil_vav | 192 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_branch | 160 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_pump | 12 | 8 | 0.67 | 0.000 [0.000, 0.000] | FAIL |
| slot=loop_source | 8 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_dat | 264 | 47 | 0.18 | 0.426 [0.143, 0.771] | n/a (resolvable share < 30%) |
| slot=vav_zone | 320 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 0.975 [0.952, 0.991] vs answered 0.669 [0.503, 0.802]; margin 0.305 [0.170, 0.474] -> PASS (flagged n=1493, answered n=133)

(c) coverage of resolvable cases lost to flags: 0.482 [0.261, 0.692] of 85 resolvable episodes

**C3 status: FAIL** (a: FAIL)

### C4 knows its limits: 79 of 79 conditions are not C2-PASS; violations (flagged < 90%): 79 -> **FAIL**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| s0|clean|ahu_sat | insufficient | 0 | 5 | nan | NO |
| s0|clean|ahu_vav | insufficient | 10 | 31 | nan | NO |
| s0|clean|branch_coil | insufficient | 0 | 37 | nan | NO |
| s0|clean|coil_ahu | insufficient | 0 | 15 | nan | NO |
| s0|clean|coil_vav | insufficient | 0 | 29 | nan | NO |
| s0|clean|loop_branch | insufficient | 1 | 21 | nan | NO |
| s0|clean|loop_pump | insufficient | 0 | 1 | nan | NO |
| s0|clean|loop_source | insufficient | 0 | 2 | nan | NO |
| s0|clean|vav_dat | insufficient | 0 | 29 | nan | NO |
| s0|clean|vav_zone | insufficient | 0 | 34 | nan | NO |
| s0|parallel_peer_swap|coil_ahu | insufficient | 1 | 12 | nan | NO |
| s0|parallel_peer_swap|coil_vav | insufficient | 0 | 26 | nan | NO |
| s0|parallel_peer_swap|loop_pump | insufficient | 0 | 1 | nan | NO |
| s0|parallel_peer_swap|loop_source | insufficient | 0 | 1 | nan | NO |
| s0|plant_loop_mapping|loop_branch | insufficient | 3 | 20 | nan | NO |
| s0|same_medium_branch|branch_coil | insufficient | 0 | 40 | nan | NO |
| s0|sensor_mapping|ahu_sat | insufficient | 1 | 10 | nan | NO |
| s0|sensor_mapping|vav_dat | insufficient | 10 | 31 | nan | NO |
| s0|vav_zone_swap|vav_zone | insufficient | 0 | 36 | nan | NO |
| s0|wrong_ahu_mapping|ahu_vav | insufficient | 6 | 25 | nan | NO |
| s1|clean|ahu_sat | insufficient | 1 | 9 | nan | NO |
| s1|clean|ahu_vav | insufficient | 6 | 20 | nan | NO |
| s1|clean|branch_coil | insufficient | 0 | 34 | nan | NO |
| s1|clean|coil_ahu | insufficient | 0 | 14 | nan | NO |
| s1|clean|coil_vav | insufficient | 0 | 18 | nan | NO |
| s1|clean|loop_branch | insufficient | 5 | 23 | nan | NO |
| s1|clean|loop_pump | insufficient | 0 | 1 | nan | NO |
| s1|clean|vav_dat | insufficient | 1 | 30 | nan | NO |
| s1|clean|vav_zone | insufficient | 0 | 47 | nan | NO |
| s1|parallel_peer_swap|coil_ahu | insufficient | 4 | 17 | nan | NO |
| s1|parallel_peer_swap|coil_vav | insufficient | 0 | 20 | nan | NO |
| s1|parallel_peer_swap|loop_pump | insufficient | 0 | 3 | nan | NO |
| s1|parallel_peer_swap|loop_source | insufficient | 0 | 1 | nan | NO |
| s1|plant_loop_mapping|loop_branch | insufficient | 5 | 22 | nan | NO |
| s1|same_medium_branch|branch_coil | insufficient | 0 | 38 | nan | NO |
| s1|sensor_mapping|ahu_sat | insufficient | 0 | 5 | nan | NO |
| s1|sensor_mapping|vav_dat | insufficient | 6 | 34 | nan | NO |
| s1|vav_zone_swap|vav_zone | insufficient | 0 | 41 | nan | NO |
| s1|wrong_ahu_mapping|ahu_vav | insufficient | 7 | 28 | nan | NO |
| s2|clean|ahu_sat | insufficient | 0 | 8 | nan | NO |
| s2|clean|ahu_vav | insufficient | 10 | 35 | nan | NO |
| s2|clean|branch_coil | insufficient | 0 | 33 | nan | NO |
| s2|clean|coil_ahu | insufficient | 0 | 10 | nan | NO |
| s2|clean|coil_vav | insufficient | 0 | 26 | nan | NO |
| s2|clean|loop_branch | insufficient | 6 | 18 | nan | NO |
| s2|clean|loop_pump | insufficient | 0 | 1 | nan | NO |
| s2|clean|loop_source | insufficient | 0 | 1 | nan | NO |
| s2|clean|vav_dat | insufficient | 0 | 38 | nan | NO |
| s2|clean|vav_zone | insufficient | 0 | 34 | nan | NO |
| s2|parallel_peer_swap|coil_ahu | insufficient | 1 | 13 | nan | NO |
| s2|parallel_peer_swap|coil_vav | insufficient | 0 | 23 | nan | NO |
| s2|parallel_peer_swap|loop_pump | insufficient | 0 | 3 | nan | NO |
| s2|parallel_peer_swap|loop_source | insufficient | 0 | 1 | nan | NO |
| s2|plant_loop_mapping|loop_branch | insufficient | 4 | 18 | nan | NO |
| s2|same_medium_branch|branch_coil | insufficient | 0 | 42 | nan | NO |
| s2|sensor_mapping|ahu_sat | insufficient | 1 | 9 | nan | NO |
| s2|sensor_mapping|vav_dat | insufficient | 8 | 32 | nan | NO |
| s2|vav_zone_swap|vav_zone | insufficient | 0 | 36 | nan | NO |
| s2|wrong_ahu_mapping|ahu_vav | insufficient | 8 | 33 | nan | NO |
| s3|clean|ahu_sat | insufficient | 1 | 6 | nan | NO |
| s3|clean|ahu_vav | insufficient | 4 | 18 | nan | NO |
| s3|clean|branch_coil | insufficient | 0 | 38 | nan | NO |
| s3|clean|coil_ahu | insufficient | 0 | 13 | nan | NO |
| s3|clean|coil_vav | insufficient | 0 | 23 | nan | NO |
| s3|clean|loop_branch | insufficient | 1 | 16 | nan | NO |
| s3|clean|loop_pump | insufficient | 0 | 1 | nan | NO |
| s3|clean|loop_source | insufficient | 0 | 1 | nan | NO |
| s3|clean|vav_dat | insufficient | 0 | 35 | nan | NO |
| s3|clean|vav_zone | insufficient | 0 | 45 | nan | NO |
| s3|parallel_peer_swap|coil_ahu | insufficient | 1 | 10 | nan | NO |
| s3|parallel_peer_swap|coil_vav | insufficient | 0 | 27 | nan | NO |
| s3|parallel_peer_swap|loop_pump | insufficient | 0 | 1 | nan | NO |
| s3|parallel_peer_swap|loop_source | insufficient | 0 | 1 | nan | NO |
| s3|plant_loop_mapping|loop_branch | insufficient | 4 | 22 | nan | NO |
| s3|same_medium_branch|branch_coil | insufficient | 0 | 40 | nan | NO |
| s3|sensor_mapping|ahu_sat | insufficient | 0 | 4 | nan | NO |
| s3|sensor_mapping|vav_dat | insufficient | 13 | 35 | nan | NO |
| s3|vav_zone_swap|vav_zone | insufficient | 0 | 47 | nan | NO |
| s3|wrong_ahu_mapping|ahu_vav | insufficient | 4 | 18 | nan | NO |

## Layer `new` (1626 episodes per policy, 331 clusters)

### Headline per policy (same layer; class-balanced; 95% cluster-bootstrap CI)

| policy | answered coverage | accuracy among answered | readings among answered |
| --- | --- | --- | --- |
| active | 0.024 [0.014, 0.038] | 0.950 [0.873, 1.000] | 5.1 [2.6, 8.7] |
| frozen | 0.010 [0.003, 0.020] | 1.000 [1.000, 1.000] | 1.5 [0.7, 1.6] |
| random | 0.010 [0.005, 0.017] | 1.000 [1.000, 1.000] | 11.2 [4.3, 16.7] |
| traversal | 0.066 [0.045, 0.092] | 0.981 [0.948, 1.000] | 5.5 [3.5, 8.6] |
| traversal_block | 0.066 [0.044, 0.090] | 0.981 [0.946, 1.000] | 5.9 [3.7, 8.9] |

### C1 efficiency: readings saved by active vs baseline (paired, among episodes answered by both)

| baseline | pairs | readings saved | coverage active - base | status |
| --- | --- | --- | --- | --- |
| random | 3 | n/a | 0.014 [0.002, 0.028] | FAIL |
| traversal_block | 33 | 2.71 [0.66, 6.46] | -0.041 [-0.062, -0.023] | FAIL |
| traversal | 31 | 2.43 [0.59, 6.41] | -0.042 [-0.062, -0.024] | FAIL |
| frozen | 12 | 0.00 [0.00, 0.00] | 0.014 [0.004, 0.026] | FAIL |

### C2 honest confidence (nominal 0.95; PASS: point>=0.93 and lower>=0.90; cells need >=8 answered and >=5 clusters)

| all | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| all | 1626 | 40 | 20 | 0.950 [0.873, 1.000] | 0.024 [0.014, 0.038] | INCONCLUSIVE |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| s0 | 406 | 10 | 8 | 1.000 [1.000, 1.000] | 0.025 [0.008, 0.046] | PASS |
| s1 | 405 | 12 | 12 | 0.913 [0.694, 1.000] | 0.029 [0.014, 0.047] | FAIL |
| s2 | 414 | 11 | 10 | 0.910 [0.689, 1.000] | 0.026 [0.011, 0.046] | FAIL |
| s3 | 401 | 7 | 5 | 1.000 [1.000, 1.000] | 0.017 [0.004, 0.035] | insufficient |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| clean | 800 | 14 | 7 | n/a | n/a | insufficient |
| parallel_peer_swap | 160 | 4 | 1 | n/a | n/a | insufficient |
| plant_loop_mapping | 82 | 0 | 0 | n/a | n/a | insufficient |
| same_medium_branch | 160 | 0 | 0 | n/a | n/a | insufficient |
| sensor_mapping | 160 | 12 | 6 | n/a | n/a | insufficient |
| vav_zone_swap | 160 | 0 | 0 | n/a | n/a | insufficient |
| wrong_ahu_mapping | 104 | 10 | 6 | n/a | n/a | insufficient |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| ahu_sat | 56 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| ahu_vav | 208 | 18 | 9 | 1.000 [1.000, 1.000] | 0.087 [0.030, 0.237] | PASS |
| branch_coil | 302 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| coil_ahu | 104 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| coil_vav | 192 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| loop_branch | 160 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| loop_pump | 12 | 7 | 2 | 1.000 [1.000, 1.000] | 0.625 [0.375, 0.875] | insufficient |
| loop_source | 8 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| vav_dat | 264 | 15 | 9 | 0.867 [0.678, 1.000] | 0.057 [0.020, 0.113] | FAIL |
| vav_zone | 320 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

Cells (season x family x slot): 79; PASS: 0, INCONCLUSIVE: 0, FAIL: 0, insufficient: 79

Calibration (answered verdicts), ECE = 0.052 over n=40

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.80,0.90) | 6 | 0.883 | 1.000 |
| [0.90,0.95) | 11 | 0.937 | 0.832 |
| [0.95,1.00) | 23 | 0.993 | 1.000 |

Calibration (ALL crossed verdicts, answered or flagged), ECE = 0.061 over n=412

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.50,0.60) | 20 | 0.545 | 0.693 |
| [0.60,0.70) | 7 | 0.682 | 0.566 |
| [0.70,0.80) | 63 | 0.757 | 0.725 |
| [0.80,0.90) | 202 | 0.852 | 0.785 |
| [0.90,0.95) | 39 | 0.934 | 0.797 |
| [0.95,1.00) | 81 | 0.995 | 0.987 |

### C3 precise abstention

| bucket | episodes | resolvable | share | coverage of resolvable | status |
| --- | --- | --- | --- | --- | --- |
| season=s0 | 406 | 22 | 0.05 | 0.455 [0.182, 0.741] | n/a (resolvable share < 30%) |
| season=s1 | 405 | 18 | 0.04 | 0.611 [0.348, 0.917] | n/a (resolvable share < 30%) |
| season=s2 | 414 | 26 | 0.06 | 0.346 [0.138, 0.593] | n/a (resolvable share < 30%) |
| season=s3 | 401 | 19 | 0.05 | 0.368 [0.091, 0.637] | n/a (resolvable share < 30%) |
| slot=ahu_sat | 56 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=ahu_vav | 208 | 26 | 0.12 | 0.692 [0.389, 0.958] | n/a (resolvable share < 30%) |
| slot=branch_coil | 302 | 4 | 0.01 | 0.000 [0.000, 0.000] | n/a (resolvable share < 30%) |
| slot=coil_ahu | 104 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=coil_vav | 192 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_branch | 160 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_pump | 12 | 8 | 0.67 | 0.875 [0.750, 1.000] | PASS |
| slot=loop_source | 8 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_dat | 264 | 47 | 0.18 | 0.255 [0.096, 0.484] | n/a (resolvable share < 30%) |
| slot=vav_zone | 320 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 0.972 [0.951, 0.988] vs answered 0.076 [0.000, 0.169]; margin 0.896 [0.797, 0.978] -> PASS (flagged n=1586, answered n=40)

(c) coverage of resolvable cases lost to flags: 0.565 [0.375, 0.744] of 85 resolvable episodes

**C3 status: PASS** (a: PASS)

### C4 knows its limits: 79 of 79 conditions are not C2-PASS; violations (flagged < 90%): 79 -> **FAIL**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| s0|clean|ahu_sat | insufficient | 0 | 5 | nan | NO |
| s0|clean|ahu_vav | insufficient | 2 | 31 | nan | NO |
| s0|clean|branch_coil | insufficient | 0 | 37 | nan | NO |
| s0|clean|coil_ahu | insufficient | 0 | 15 | nan | NO |
| s0|clean|coil_vav | insufficient | 0 | 29 | nan | NO |
| s0|clean|loop_branch | insufficient | 0 | 21 | nan | NO |
| s0|clean|loop_pump | insufficient | 1 | 1 | nan | NO |
| s0|clean|loop_source | insufficient | 0 | 2 | nan | NO |
| s0|clean|vav_dat | insufficient | 0 | 29 | nan | NO |
| s0|clean|vav_zone | insufficient | 0 | 34 | nan | NO |
| s0|parallel_peer_swap|coil_ahu | insufficient | 0 | 12 | nan | NO |
| s0|parallel_peer_swap|coil_vav | insufficient | 0 | 26 | nan | NO |
| s0|parallel_peer_swap|loop_pump | insufficient | 1 | 1 | nan | NO |
| s0|parallel_peer_swap|loop_source | insufficient | 0 | 1 | nan | NO |
| s0|plant_loop_mapping|loop_branch | insufficient | 0 | 20 | nan | NO |
| s0|same_medium_branch|branch_coil | insufficient | 0 | 40 | nan | NO |
| s0|sensor_mapping|ahu_sat | insufficient | 0 | 10 | nan | NO |
| s0|sensor_mapping|vav_dat | insufficient | 3 | 31 | nan | NO |
| s0|vav_zone_swap|vav_zone | insufficient | 0 | 36 | nan | NO |
| s0|wrong_ahu_mapping|ahu_vav | insufficient | 3 | 25 | nan | NO |
| s1|clean|ahu_sat | insufficient | 0 | 9 | nan | NO |
| s1|clean|ahu_vav | insufficient | 1 | 20 | nan | NO |
| s1|clean|branch_coil | insufficient | 0 | 34 | nan | NO |
| s1|clean|coil_ahu | insufficient | 0 | 14 | nan | NO |
| s1|clean|coil_vav | insufficient | 0 | 18 | nan | NO |
| s1|clean|loop_branch | insufficient | 0 | 23 | nan | NO |
| s1|clean|loop_pump | insufficient | 1 | 1 | nan | NO |
| s1|clean|vav_dat | insufficient | 2 | 30 | nan | NO |
| s1|clean|vav_zone | insufficient | 0 | 47 | nan | NO |
| s1|parallel_peer_swap|coil_ahu | insufficient | 0 | 17 | nan | NO |
| s1|parallel_peer_swap|coil_vav | insufficient | 0 | 20 | nan | NO |
| s1|parallel_peer_swap|loop_pump | insufficient | 1 | 3 | nan | NO |
| s1|parallel_peer_swap|loop_source | insufficient | 0 | 1 | nan | NO |
| s1|plant_loop_mapping|loop_branch | insufficient | 0 | 22 | nan | NO |
| s1|same_medium_branch|branch_coil | insufficient | 0 | 38 | nan | NO |
| s1|sensor_mapping|ahu_sat | insufficient | 0 | 5 | nan | NO |
| s1|sensor_mapping|vav_dat | insufficient | 4 | 34 | nan | NO |
| s1|vav_zone_swap|vav_zone | insufficient | 0 | 41 | nan | NO |
| s1|wrong_ahu_mapping|ahu_vav | insufficient | 3 | 28 | nan | NO |
| s2|clean|ahu_sat | insufficient | 0 | 8 | nan | NO |
| s2|clean|ahu_vav | insufficient | 3 | 35 | nan | NO |
| s2|clean|branch_coil | insufficient | 0 | 33 | nan | NO |
| s2|clean|coil_ahu | insufficient | 0 | 10 | nan | NO |
| s2|clean|coil_vav | insufficient | 0 | 26 | nan | NO |
| s2|clean|loop_branch | insufficient | 0 | 18 | nan | NO |
| s2|clean|loop_pump | insufficient | 0 | 1 | nan | NO |
| s2|clean|loop_source | insufficient | 0 | 1 | nan | NO |
| s2|clean|vav_dat | insufficient | 1 | 38 | nan | NO |
| s2|clean|vav_zone | insufficient | 0 | 34 | nan | NO |
| s2|parallel_peer_swap|coil_ahu | insufficient | 0 | 13 | nan | NO |
| s2|parallel_peer_swap|coil_vav | insufficient | 0 | 23 | nan | NO |
| s2|parallel_peer_swap|loop_pump | insufficient | 2 | 3 | nan | NO |
| s2|parallel_peer_swap|loop_source | insufficient | 0 | 1 | nan | NO |
| s2|plant_loop_mapping|loop_branch | insufficient | 0 | 18 | nan | NO |
| s2|same_medium_branch|branch_coil | insufficient | 0 | 42 | nan | NO |
| s2|sensor_mapping|ahu_sat | insufficient | 0 | 9 | nan | NO |
| s2|sensor_mapping|vav_dat | insufficient | 1 | 32 | nan | NO |
| s2|vav_zone_swap|vav_zone | insufficient | 0 | 36 | nan | NO |
| s2|wrong_ahu_mapping|ahu_vav | insufficient | 4 | 33 | nan | NO |
| s3|clean|ahu_sat | insufficient | 0 | 6 | nan | NO |
| s3|clean|ahu_vav | insufficient | 2 | 18 | nan | NO |
| s3|clean|branch_coil | insufficient | 0 | 38 | nan | NO |
| s3|clean|coil_ahu | insufficient | 0 | 13 | nan | NO |
| s3|clean|coil_vav | insufficient | 0 | 23 | nan | NO |
| s3|clean|loop_branch | insufficient | 0 | 16 | nan | NO |
| s3|clean|loop_pump | insufficient | 1 | 1 | nan | NO |
| s3|clean|loop_source | insufficient | 0 | 1 | nan | NO |
| s3|clean|vav_dat | insufficient | 0 | 35 | nan | NO |
| s3|clean|vav_zone | insufficient | 0 | 45 | nan | NO |
| s3|parallel_peer_swap|coil_ahu | insufficient | 0 | 10 | nan | NO |
| s3|parallel_peer_swap|coil_vav | insufficient | 0 | 27 | nan | NO |
| s3|parallel_peer_swap|loop_pump | insufficient | 0 | 1 | nan | NO |
| s3|parallel_peer_swap|loop_source | insufficient | 0 | 1 | nan | NO |
| s3|plant_loop_mapping|loop_branch | insufficient | 0 | 22 | nan | NO |
| s3|same_medium_branch|branch_coil | insufficient | 0 | 40 | nan | NO |
| s3|sensor_mapping|ahu_sat | insufficient | 0 | 4 | nan | NO |
| s3|sensor_mapping|vav_dat | insufficient | 4 | 35 | nan | NO |
| s3|vav_zone_swap|vav_zone | insufficient | 0 | 47 | nan | NO |
| s3|wrong_ahu_mapping|ahu_vav | insufficient | 0 | 18 | nan | NO |
