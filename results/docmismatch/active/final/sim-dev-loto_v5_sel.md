sim-dev-loto_v5_sel: 1626 episodes (331 clusters = event groups); config variant=sel, tau=0.95, primary setting `visit`; elapsed 789s; info={"sys03_psz_ac": {"beta": {"ahu_sat": 1.0, "ahu_vav": 1.0, "branch_coil": 0.1, "coil_ahu": 1.0, "coil_vav": 1.0, "loop_branch": 0.2, "loop_pump": 1.0, "loop_source": 0.35, "vav_dat": 1.0, "vav_zone": 1.0}, "n_outer": 2320, "n_inner": 13940}, "sys07_vav_reheat": {"beta": {"ahu_sat": 0.7, "ahu_vav": 0.5, "branch_coil": 0.1, "coil_ahu": 1.0, "coil_vav": 1.0, "loop_branch": 0.2, "loop_pump": 1.0, "loo

# Readiness evaluation: sim-dev-loto_v5_sel

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
| parallel_peer_swap | 316 | 243 | 67 | 0.794 [0.708, 0.863] | 0.769 [0.671, 0.854] | FAIL |
| plant_loop_mapping | 160 | 51 | 20 | 1.000 [1.000, 1.000] | 0.320 [0.199, 0.487] | PASS |
| same_medium_branch | 302 | 35 | 20 | 0.729 [0.459, 0.949] | 0.117 [0.064, 0.199] | FAIL |
| sensor_mapping | 320 | 302 | 64 | 0.858 [0.774, 0.952] | 0.944 [0.890, 0.984] | FAIL |
| vav_zone_swap | 320 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| wrong_ahu_mapping | 208 | 153 | 19 | 0.967 [0.850, 1.000] | 0.736 [0.395, 0.862] | INCONCLUSIVE |

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

Cells (season x family x slot): 40; PASS: 6, INCONCLUSIVE: 4, FAIL: 16, insufficient: 14

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

### C4 knows its limits: 34 of 40 conditions are not C2-PASS; violations (flagged < 90%): 29 -> **FAIL**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| s0|parallel_peer_swap|coil_ahu | FAIL | 17 | 27 | 0.34 | NO |
| s0|parallel_peer_swap|coil_vav | FAIL | 48 | 55 | 0.13 | NO |
| s0|parallel_peer_swap|loop_pump | insufficient | 2 | 2 | 0.00 | NO |
| s0|parallel_peer_swap|loop_source | insufficient | 2 | 3 | 0.50 | NO |
| s0|same_medium_branch|branch_coil | FAIL | 13 | 77 | 0.83 | NO |
| s0|sensor_mapping|ahu_sat | FAIL | 10 | 15 | 0.35 | NO |
| s0|sensor_mapping|vav_dat | FAIL | 60 | 60 | 0.00 | NO |
| s0|vav_zone_swap|vav_zone | insufficient | 0 | 70 | 1.00 | yes |
| s0|wrong_ahu_mapping|ahu_vav | INCONCLUSIVE | 43 | 56 | 0.24 | NO |
| s1|parallel_peer_swap|coil_vav | FAIL | 30 | 38 | 0.20 | NO |
| s1|parallel_peer_swap|loop_pump | insufficient | 4 | 4 | 0.00 | NO |
| s1|parallel_peer_swap|loop_source | insufficient | 0 | 1 | nan | NO |
| s1|same_medium_branch|branch_coil | FAIL | 8 | 72 | 0.89 | NO |
| s1|sensor_mapping|ahu_sat | FAIL | 10 | 14 | 0.27 | NO |
| s1|sensor_mapping|vav_dat | FAIL | 64 | 64 | 0.00 | NO |
| s1|vav_zone_swap|vav_zone | insufficient | 0 | 88 | 1.00 | yes |
| s1|wrong_ahu_mapping|ahu_vav | INCONCLUSIVE | 37 | 48 | 0.23 | NO |
| s2|parallel_peer_swap|coil_ahu | FAIL | 14 | 23 | 0.44 | NO |
| s2|parallel_peer_swap|coil_vav | FAIL | 47 | 49 | 0.04 | NO |
| s2|parallel_peer_swap|loop_pump | insufficient | 4 | 4 | 0.00 | NO |
| s2|parallel_peer_swap|loop_source | insufficient | 1 | 2 | 0.50 | NO |
| s2|same_medium_branch|branch_coil | insufficient | 6 | 75 | 0.92 | yes |
| s2|sensor_mapping|ahu_sat | FAIL | 11 | 17 | 0.35 | NO |
| s2|sensor_mapping|vav_dat | FAIL | 70 | 70 | 0.00 | NO |
| s2|vav_zone_swap|vav_zone | insufficient | 0 | 70 | 1.00 | yes |
| s2|wrong_ahu_mapping|ahu_vav | INCONCLUSIVE | 48 | 68 | 0.29 | NO |
| s3|parallel_peer_swap|coil_vav | FAIL | 45 | 50 | 0.09 | NO |
| s3|parallel_peer_swap|loop_pump | insufficient | 2 | 2 | 0.00 | NO |
| s3|parallel_peer_swap|loop_source | insufficient | 1 | 2 | 0.50 | NO |
| s3|same_medium_branch|branch_coil | FAIL | 8 | 78 | 0.90 | NO |
| s3|sensor_mapping|ahu_sat | insufficient | 7 | 10 | 0.33 | NO |
| s3|sensor_mapping|vav_dat | FAIL | 70 | 70 | 0.00 | NO |
| s3|vav_zone_swap|vav_zone | insufficient | 0 | 92 | 1.00 | yes |
| s3|wrong_ahu_mapping|ahu_vav | INCONCLUSIVE | 25 | 36 | 0.31 | NO |

## Layer `legacy` (1626 episodes per policy, 331 clusters)

### Headline per policy (same layer; class-balanced; 95% cluster-bootstrap CI)

| policy | answered coverage | accuracy among answered | readings among answered |
| --- | --- | --- | --- |
| active | 0.081 [0.054, 0.113] | 0.947 [0.887, 0.992] | 3.3 [2.2, 4.4] |
| frozen | 0.048 [0.024, 0.077] | 0.924 [0.811, 1.000] | 3.0 [1.6, 3.8] |
| random | 0.012 [0.001, 0.028] | 0.680 [0.222, 0.910] | 11.2 [2.4, 12.0] |
| traversal | 0.123 [0.089, 0.163] | 0.936 [0.844, 0.995] | 6.1 [4.7, 7.7] |
| traversal_block | 0.246 [0.177, 0.319] | 0.958 [0.900, 0.994] | 6.3 [4.1, 8.5] |

### C1 efficiency: readings saved by active vs baseline (paired, among episodes answered by both)

| baseline | pairs | readings saved | coverage active - base | status |
| --- | --- | --- | --- | --- |
| random | 0 | n/a | n/a | n/a |
| traversal_block | 88 | 2.55 [1.70, 3.59] | -0.165 [-0.245, -0.089] | FAIL |
| traversal | 62 | 2.36 [0.09, 3.27] | -0.042 [-0.086, -0.003] | FAIL |
| frozen | 62 | 0.11 [0.01, 0.24] | 0.033 [0.014, 0.053] | PASS |

### C2 honest confidence (nominal 0.95; PASS: point>=0.93 and lower>=0.90; cells need >=8 answered and >=5 clusters)

| all | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| all | 1626 | 132 | 46 | 0.947 [0.887, 0.992] | 0.081 [0.054, 0.113] | INCONCLUSIVE |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| s0 | 406 | 32 | 23 | 0.937 [0.826, 1.000] | 0.079 [0.042, 0.125] | INCONCLUSIVE |
| s1 | 405 | 34 | 25 | 0.941 [0.833, 1.000] | 0.083 [0.049, 0.122] | INCONCLUSIVE |
| s2 | 414 | 38 | 31 | 0.948 [0.868, 1.000] | 0.092 [0.060, 0.130] | INCONCLUSIVE |
| s3 | 401 | 28 | 21 | 0.965 [0.874, 1.000] | 0.069 [0.040, 0.101] | INCONCLUSIVE |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| parallel_peer_swap | 316 | 6 | 2 | 1.000 [1.000, 1.000] | 0.019 [0.000, 0.057] | insufficient |
| plant_loop_mapping | 160 | 29 | 15 | 1.000 [1.000, 1.000] | 0.181 [0.091, 0.289] | PASS |
| same_medium_branch | 302 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| sensor_mapping | 320 | 42 | 13 | 0.952 [0.856, 1.000] | 0.131 [0.067, 0.222] | INCONCLUSIVE |
| vav_zone_swap | 320 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| wrong_ahu_mapping | 208 | 55 | 16 | 0.909 [0.739, 1.000] | 0.264 [0.105, 0.542] | FAIL |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| ahu_sat | 56 | 4 | 2 | 0.750 [0.500, 1.000] | 0.071 [0.000, 0.194] | insufficient |
| ahu_vav | 208 | 55 | 16 | 0.909 [0.739, 1.000] | 0.264 [0.105, 0.542] | FAIL |
| branch_coil | 302 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| coil_ahu | 104 | 6 | 2 | 1.000 [1.000, 1.000] | 0.058 [0.000, 0.200] | insufficient |
| coil_vav | 192 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| loop_branch | 160 | 29 | 15 | 1.000 [1.000, 1.000] | 0.181 [0.091, 0.289] | PASS |
| loop_pump | 12 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| loop_source | 8 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| vav_dat | 264 | 38 | 11 | 0.974 [0.886, 1.000] | 0.144 [0.065, 0.256] | INCONCLUSIVE |
| vav_zone | 320 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

Cells (season x family x slot): 40; PASS: 5, INCONCLUSIVE: 2, FAIL: 2, insufficient: 31

Calibration (answered verdicts), ECE = 0.025 over n=132

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 132 | 0.979 | 0.954 |

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

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 0.975 [0.952, 0.991] vs answered 0.667 [0.499, 0.801]; margin 0.308 [0.172, 0.476] -> PASS (flagged n=1494, answered n=132)

(c) coverage of resolvable cases lost to flags: 0.482 [0.261, 0.692] of 85 resolvable episodes

**C3 status: FAIL** (a: FAIL)

### C4 knows its limits: 35 of 40 conditions are not C2-PASS; violations (flagged < 90%): 7 -> **FAIL**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| s0|parallel_peer_swap|coil_ahu | insufficient | 1 | 27 | 0.96 | yes |
| s0|parallel_peer_swap|coil_vav | insufficient | 0 | 55 | 1.00 | yes |
| s0|parallel_peer_swap|loop_pump | insufficient | 0 | 2 | 1.00 | yes |
| s0|parallel_peer_swap|loop_source | insufficient | 0 | 3 | 1.00 | yes |
| s0|plant_loop_mapping|loop_branch | insufficient | 4 | 41 | 0.90 | yes |
| s0|same_medium_branch|branch_coil | insufficient | 0 | 77 | 1.00 | yes |
| s0|sensor_mapping|ahu_sat | insufficient | 1 | 15 | 0.95 | yes |
| s0|vav_zone_swap|vav_zone | insufficient | 0 | 70 | 1.00 | yes |
| s0|wrong_ahu_mapping|ahu_vav | FAIL | 16 | 56 | 0.72 | NO |
| s1|parallel_peer_swap|coil_ahu | insufficient | 3 | 31 | 0.91 | yes |
| s1|parallel_peer_swap|coil_vav | insufficient | 0 | 38 | 1.00 | yes |
| s1|parallel_peer_swap|loop_pump | insufficient | 0 | 4 | 1.00 | yes |
| s1|parallel_peer_swap|loop_source | insufficient | 0 | 1 | nan | NO |
| s1|same_medium_branch|branch_coil | insufficient | 0 | 72 | 1.00 | yes |
| s1|sensor_mapping|ahu_sat | insufficient | 1 | 14 | 0.94 | yes |
| s1|sensor_mapping|vav_dat | insufficient | 7 | 64 | 0.90 | NO |
| s1|vav_zone_swap|vav_zone | insufficient | 0 | 88 | 1.00 | yes |
| s1|wrong_ahu_mapping|ahu_vav | INCONCLUSIVE | 13 | 48 | 0.72 | NO |
| s2|parallel_peer_swap|coil_ahu | insufficient | 1 | 23 | 0.96 | yes |
| s2|parallel_peer_swap|coil_vav | insufficient | 0 | 49 | 1.00 | yes |
| s2|parallel_peer_swap|loop_pump | insufficient | 0 | 4 | 1.00 | yes |
| s2|parallel_peer_swap|loop_source | insufficient | 0 | 2 | 1.00 | yes |
| s2|same_medium_branch|branch_coil | insufficient | 0 | 75 | 1.00 | yes |
| s2|sensor_mapping|ahu_sat | insufficient | 1 | 17 | 0.94 | yes |
| s2|vav_zone_swap|vav_zone | insufficient | 0 | 70 | 1.00 | yes |
| s2|wrong_ahu_mapping|ahu_vav | INCONCLUSIVE | 18 | 68 | 0.74 | NO |
| s3|parallel_peer_swap|coil_ahu | insufficient | 1 | 23 | 0.95 | yes |
| s3|parallel_peer_swap|coil_vav | insufficient | 0 | 50 | 1.00 | yes |
| s3|parallel_peer_swap|loop_pump | insufficient | 0 | 2 | 1.00 | yes |
| s3|parallel_peer_swap|loop_source | insufficient | 0 | 2 | 1.00 | yes |
| s3|plant_loop_mapping|loop_branch | insufficient | 5 | 38 | 0.88 | NO |
| s3|same_medium_branch|branch_coil | insufficient | 0 | 78 | 1.00 | yes |
| s3|sensor_mapping|ahu_sat | insufficient | 1 | 10 | 0.92 | yes |
| s3|vav_zone_swap|vav_zone | insufficient | 0 | 92 | 1.00 | yes |
| s3|wrong_ahu_mapping|ahu_vav | FAIL | 8 | 36 | 0.78 | NO |

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
| parallel_peer_swap | 316 | 7 | 2 | 1.000 [1.000, 1.000] | 0.022 [0.000, 0.059] | insufficient |
| plant_loop_mapping | 160 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| same_medium_branch | 302 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| sensor_mapping | 320 | 15 | 9 | 0.867 [0.673, 1.000] | 0.047 [0.016, 0.092] | FAIL |
| vav_zone_swap | 320 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| wrong_ahu_mapping | 208 | 18 | 9 | 1.000 [1.000, 1.000] | 0.087 [0.030, 0.237] | PASS |

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

Cells (season x family x slot): 40; PASS: 0, INCONCLUSIVE: 0, FAIL: 0, insufficient: 40

Calibration (answered verdicts), ECE = 0.049 over n=40

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.80,0.90) | 6 | 0.883 | 1.000 |
| [0.90,0.95) | 12 | 0.937 | 0.848 |
| [0.95,1.00) | 22 | 0.993 | 1.000 |

Calibration (ALL crossed verdicts, answered or flagged), ECE = 0.061 over n=412

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.50,0.60) | 20 | 0.545 | 0.693 |
| [0.60,0.70) | 7 | 0.684 | 0.566 |
| [0.70,0.80) | 63 | 0.756 | 0.725 |
| [0.80,0.90) | 202 | 0.852 | 0.785 |
| [0.90,0.95) | 40 | 0.936 | 0.802 |
| [0.95,1.00) | 80 | 0.995 | 0.987 |

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

### C4 knows its limits: 40 of 40 conditions are not C2-PASS; violations (flagged < 90%): 6 -> **FAIL**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| s0|parallel_peer_swap|coil_ahu | insufficient | 0 | 27 | 1.00 | yes |
| s0|parallel_peer_swap|coil_vav | insufficient | 0 | 55 | 1.00 | yes |
| s0|parallel_peer_swap|loop_pump | insufficient | 2 | 2 | 0.00 | NO |
| s0|parallel_peer_swap|loop_source | insufficient | 0 | 3 | 1.00 | yes |
| s0|plant_loop_mapping|loop_branch | insufficient | 0 | 41 | 1.00 | yes |
| s0|same_medium_branch|branch_coil | insufficient | 0 | 77 | 1.00 | yes |
| s0|sensor_mapping|ahu_sat | insufficient | 0 | 15 | 1.00 | yes |
| s0|sensor_mapping|vav_dat | insufficient | 3 | 60 | 0.95 | yes |
| s0|vav_zone_swap|vav_zone | insufficient | 0 | 70 | 1.00 | yes |
| s0|wrong_ahu_mapping|ahu_vav | insufficient | 5 | 56 | 0.91 | yes |
| s1|parallel_peer_swap|coil_ahu | insufficient | 0 | 31 | 1.00 | yes |
| s1|parallel_peer_swap|coil_vav | insufficient | 0 | 38 | 1.00 | yes |
| s1|parallel_peer_swap|loop_pump | insufficient | 2 | 4 | 0.33 | NO |
| s1|parallel_peer_swap|loop_source | insufficient | 0 | 1 | nan | NO |
| s1|plant_loop_mapping|loop_branch | insufficient | 0 | 45 | 1.00 | yes |
| s1|same_medium_branch|branch_coil | insufficient | 0 | 72 | 1.00 | yes |
| s1|sensor_mapping|ahu_sat | insufficient | 0 | 14 | 1.00 | yes |
| s1|sensor_mapping|vav_dat | insufficient | 6 | 64 | 0.91 | yes |
| s1|vav_zone_swap|vav_zone | insufficient | 0 | 88 | 1.00 | yes |
| s1|wrong_ahu_mapping|ahu_vav | insufficient | 4 | 48 | 0.92 | yes |
| s2|parallel_peer_swap|coil_ahu | insufficient | 0 | 23 | 1.00 | yes |
| s2|parallel_peer_swap|coil_vav | insufficient | 0 | 49 | 1.00 | yes |
| s2|parallel_peer_swap|loop_pump | insufficient | 2 | 4 | 0.67 | NO |
| s2|parallel_peer_swap|loop_source | insufficient | 0 | 2 | 1.00 | yes |
| s2|plant_loop_mapping|loop_branch | insufficient | 0 | 36 | 1.00 | yes |
| s2|same_medium_branch|branch_coil | insufficient | 0 | 75 | 1.00 | yes |
| s2|sensor_mapping|ahu_sat | insufficient | 0 | 17 | 1.00 | yes |
| s2|sensor_mapping|vav_dat | insufficient | 2 | 70 | 0.97 | yes |
| s2|vav_zone_swap|vav_zone | insufficient | 0 | 70 | 1.00 | yes |
| s2|wrong_ahu_mapping|ahu_vav | insufficient | 7 | 68 | 0.90 | NO |
| s3|parallel_peer_swap|coil_ahu | insufficient | 0 | 23 | 1.00 | yes |
| s3|parallel_peer_swap|coil_vav | insufficient | 0 | 50 | 1.00 | yes |
| s3|parallel_peer_swap|loop_pump | insufficient | 1 | 2 | 0.50 | NO |
| s3|parallel_peer_swap|loop_source | insufficient | 0 | 2 | 1.00 | yes |
| s3|plant_loop_mapping|loop_branch | insufficient | 0 | 38 | 1.00 | yes |
| s3|same_medium_branch|branch_coil | insufficient | 0 | 78 | 1.00 | yes |
| s3|sensor_mapping|ahu_sat | insufficient | 0 | 10 | 1.00 | yes |
| s3|sensor_mapping|vav_dat | insufficient | 4 | 70 | 0.94 | yes |
| s3|vav_zone_swap|vav_zone | insufficient | 0 | 92 | 1.00 | yes |
| s3|wrong_ahu_mapping|ahu_vav | insufficient | 2 | 36 | 0.94 | yes |
