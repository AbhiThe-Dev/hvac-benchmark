sim-sealed_rehearsal: 240 episodes (52 clusters = event groups); config variant=sel_slice, tau=0.95, primary setting `visit`; elapsed 64s; info={"n_outer": 2400, "beta": {"ahu_sat": 1.0, "ahu_vav": 0.7, "branch_coil": 0.35, "coil_ahu": 1.0, "coil_vav": 1.0, "loop_branch": 0.2, "loop_pump": 1.0, "loop_source": 0.5, "vav_dat": 1.0, "vav_zone": 0.1}}

# Readiness evaluation: sim-sealed_rehearsal

## Layer `none` (240 episodes per policy, 52 clusters)

### Headline per policy (same layer; class-balanced; 95% cluster-bootstrap CI)

| policy | answered coverage | accuracy among answered | readings among answered |
| --- | --- | --- | --- |
| active | 0.454 [0.309, 0.589] | 0.945 [0.871, 1.000] | 7.4 [4.7, 9.9] |
| frozen | 0.450 [0.302, 0.590] | 0.935 [0.858, 0.992] | 7.8 [4.9, 10.5] |
| random | 0.225 [0.130, 0.354] | 1.000 [1.000, 1.000] | 13.5 [12.0, 14.8] |
| traversal | 0.238 [0.139, 0.375] | 1.000 [1.000, 1.000] | 10.4 [8.0, 13.9] |
| traversal_block | 0.242 [0.141, 0.377] | 1.000 [1.000, 1.000] | 10.0 [7.7, 13.2] |

### C1 efficiency: readings saved by active vs baseline (paired, among episodes answered by both)

| baseline | pairs | readings saved | coverage active - base | status |
| --- | --- | --- | --- | --- |
| random | 54 | 8.50 [6.50, 10.22] | 0.229 [0.104, 0.351] | PASS |
| traversal_block | 57 | 5.25 [3.17, 7.70] | 0.213 [0.085, 0.339] | PASS |
| traversal | 56 | 6.03 [3.99, 8.69] | 0.217 [0.089, 0.344] | PASS |
| frozen | 106 | 0.25 [-0.42, 0.79] | 0.004 [-0.008, 0.019] | FAIL |

### C2 honest confidence (nominal 0.95; PASS: point>=0.93 and lower>=0.90; cells need >=8 answered and >=5 clusters)

| all | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| all | 240 | 109 | 29 | 0.945 [0.871, 1.000] | 0.454 [0.309, 0.589] | INCONCLUSIVE |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| s0 | 61 | 27 | 19 | 1.000 [1.000, 1.000] | 0.442 [0.280, 0.626] | PASS |
| s1 | 63 | 25 | 15 | 0.958 [0.847, 1.000] | 0.392 [0.203, 0.579] | INCONCLUSIVE |
| s2 | 64 | 32 | 20 | 0.969 [0.902, 1.000] | 0.500 [0.339, 0.639] | PASS |
| s3 | 52 | 25 | 15 | 0.848 [0.654, 1.000] | 0.487 [0.278, 0.666] | FAIL |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| parallel_peer_swap | 48 | 31 | 11 | 0.871 [0.684, 1.000] | 0.646 [0.437, 0.814] | FAIL |
| plant_loop_mapping | 44 | 3 | 1 | 1.000 [1.000, 1.000] | 0.068 [0.000, 0.188] | insufficient |
| same_medium_branch | 56 | 28 | 4 | 1.000 [1.000, 1.000] | 0.500 [0.393, 0.593] | insufficient |
| sensor_mapping | 40 | 35 | 8 | 0.943 [0.806, 1.000] | 0.875 [0.459, 1.000] | INCONCLUSIVE |
| vav_zone_swap | 40 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| wrong_ahu_mapping | 12 | 12 | 5 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | PASS |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| ahu_sat | 8 | 4 | 2 | 1.000 [1.000, 1.000] | 0.500 [0.250, 0.750] | insufficient |
| ahu_vav | 12 | 12 | 5 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | PASS |
| branch_coil | 56 | 28 | 4 | 1.000 [1.000, 1.000] | 0.500 [0.393, 0.593] | insufficient |
| coil_ahu | 16 | 9 | 4 | 1.000 [1.000, 1.000] | 0.562 [0.250, 0.732] | insufficient |
| coil_vav | 24 | 18 | 6 | 0.778 [0.625, 1.000] | 0.750 [0.625, 1.000] | FAIL |
| loop_branch | 44 | 3 | 1 | 1.000 [1.000, 1.000] | 0.068 [0.000, 0.188] | insufficient |
| loop_source | 8 | 4 | 1 | 1.000 [1.000, 1.000] | 0.500 [0.500, 0.500] | insufficient |
| vav_dat | 32 | 31 | 6 | 0.935 [0.750, 1.000] | 0.969 [0.875, 1.000] | INCONCLUSIVE |
| vav_zone | 40 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

Cells (season x family x slot): 35; PASS: 1, INCONCLUSIVE: 0, FAIL: 1, insufficient: 33

Calibration (answered verdicts), ECE = 0.034 over n=109

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 109 | 0.964 | 0.930 |

Calibration (ALL crossed verdicts, answered or flagged), ECE = 0.034 over n=109

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 109 | 0.964 | 0.930 |

### C3 precise abstention

| bucket | episodes | resolvable | share | coverage of resolvable | status |
| --- | --- | --- | --- | --- | --- |
| season=s0 | 61 | 12 | 0.20 | 1.000 [1.000, 1.000] | n/a (resolvable share < 30%) |
| season=s1 | 63 | 6 | 0.10 | 1.000 [1.000, 1.000] | n/a (resolvable share < 30%) |
| season=s2 | 64 | 16 | 0.25 | 1.000 [1.000, 1.000] | n/a (resolvable share < 30%) |
| season=s3 | 52 | 8 | 0.15 | 1.000 [1.000, 1.000] | n/a (resolvable share < 30%) |
| slot=ahu_sat | 8 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=ahu_vav | 12 | 12 | 1.00 | 1.000 [1.000, 1.000] | PASS |
| slot=branch_coil | 56 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=coil_ahu | 16 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=coil_vav | 24 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_branch | 44 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_source | 8 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_dat | 32 | 30 | 0.94 | 1.000 [1.000, 1.000] | PASS |
| slot=vav_zone | 40 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 1.000 [1.000, 1.000] vs answered 0.624 [0.356, 0.837]; margin 0.376 [0.163, 0.644] -> PASS (flagged n=131, answered n=109)

(c) coverage of resolvable cases lost to flags: 0.000 [0.000, 0.000] of 42 resolvable episodes

**C3 status: PASS** (a: PASS)

### C4 knows its limits: 34 of 35 conditions are not C2-PASS; violations (flagged < 90%): 24 -> **FAIL**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| s0|parallel_peer_swap|coil_ahu | insufficient | 1 | 3 | 0.67 | NO |
| s0|parallel_peer_swap|coil_vav | insufficient | 7 | 10 | 0.30 | NO |
| s0|parallel_peer_swap|loop_source | insufficient | 2 | 3 | 0.33 | NO |
| s0|plant_loop_mapping|loop_branch | insufficient | 1 | 13 | 0.92 | yes |
| s0|same_medium_branch|branch_coil | insufficient | 3 | 9 | 0.67 | NO |
| s0|sensor_mapping|ahu_sat | insufficient | 1 | 2 | 0.50 | NO |
| s0|vav_zone_swap|vav_zone | insufficient | 0 | 8 | 1.00 | yes |
| s0|wrong_ahu_mapping|ahu_vav | insufficient | 3 | 3 | 0.00 | NO |
| s1|parallel_peer_swap|coil_ahu | insufficient | 5 | 7 | 0.29 | NO |
| s1|parallel_peer_swap|coil_vav | insufficient | 2 | 3 | 0.33 | NO |
| s1|parallel_peer_swap|loop_source | insufficient | 0 | 1 | 1.00 | yes |
| s1|plant_loop_mapping|loop_branch | insufficient | 1 | 14 | 0.93 | yes |
| s1|same_medium_branch|branch_coil | insufficient | 10 | 19 | 0.47 | NO |
| s1|sensor_mapping|ahu_sat | insufficient | 1 | 2 | 0.50 | NO |
| s1|sensor_mapping|vav_dat | insufficient | 4 | 4 | 0.00 | NO |
| s1|vav_zone_swap|vav_zone | insufficient | 0 | 11 | 1.00 | yes |
| s1|wrong_ahu_mapping|ahu_vav | insufficient | 2 | 2 | 0.00 | NO |
| s2|parallel_peer_swap|coil_ahu | insufficient | 0 | 2 | 1.00 | yes |
| s2|parallel_peer_swap|coil_vav | insufficient | 4 | 6 | 0.33 | NO |
| s2|parallel_peer_swap|loop_source | insufficient | 1 | 2 | 0.50 | NO |
| s2|plant_loop_mapping|loop_branch | insufficient | 1 | 11 | 0.91 | yes |
| s2|same_medium_branch|branch_coil | insufficient | 7 | 13 | 0.46 | NO |
| s2|sensor_mapping|ahu_sat | insufficient | 2 | 4 | 0.50 | NO |
| s2|sensor_mapping|vav_dat | FAIL | 11 | 11 | 0.00 | NO |
| s2|vav_zone_swap|vav_zone | insufficient | 0 | 9 | 1.00 | yes |
| s2|wrong_ahu_mapping|ahu_vav | insufficient | 6 | 6 | 0.00 | NO |
| s3|parallel_peer_swap|coil_ahu | insufficient | 3 | 4 | 0.25 | NO |
| s3|parallel_peer_swap|coil_vav | insufficient | 5 | 5 | 0.00 | NO |
| s3|parallel_peer_swap|loop_source | insufficient | 1 | 2 | 0.50 | NO |
| s3|plant_loop_mapping|loop_branch | insufficient | 0 | 6 | 1.00 | yes |
| s3|same_medium_branch|branch_coil | insufficient | 8 | 15 | 0.47 | NO |
| s3|sensor_mapping|vav_dat | insufficient | 7 | 7 | 0.00 | NO |
| s3|vav_zone_swap|vav_zone | insufficient | 0 | 12 | 1.00 | yes |
| s3|wrong_ahu_mapping|ahu_vav | insufficient | 1 | 1 | 0.00 | NO |

## Layer `legacy` (240 episodes per policy, 52 clusters)

### Headline per policy (same layer; class-balanced; 95% cluster-bootstrap CI)

| policy | answered coverage | accuracy among answered | readings among answered |
| --- | --- | --- | --- |
| active | 0.188 [0.054, 0.332] | 1.000 [1.000, 1.000] | 10.7 [1.3, 12.3] |
| frozen | 0.050 [0.010, 0.105] | 1.000 [1.000, 1.000] | 1.4 [1.0, 2.0] |
| random | 0.138 [0.069, 0.226] | 1.000 [1.000, 1.000] | 12.8 [10.6, 14.7] |
| traversal | 0.192 [0.098, 0.316] | 1.000 [1.000, 1.000] | 9.2 [6.6, 12.7] |
| traversal_block | 0.196 [0.102, 0.319] | 1.000 [1.000, 1.000] | 9.0 [6.6, 12.3] |

### C1 efficiency: readings saved by active vs baseline (paired, among episodes answered by both)

| baseline | pairs | readings saved | coverage active - base | status |
| --- | --- | --- | --- | --- |
| random | 16 | n/a | 0.050 [-0.120, 0.209] | FAIL |
| traversal_block | 17 | n/a | -0.008 [-0.219, 0.177] | FAIL |
| traversal | 16 | n/a | -0.004 [-0.214, 0.179] | FAIL |
| frozen | 11 | n/a | 0.138 [0.014, 0.270] | FAIL |

### C2 honest confidence (nominal 0.95; PASS: point>=0.93 and lower>=0.90; cells need >=8 answered and >=5 clusters)

| all | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| all | 240 | 45 | 10 | 1.000 [1.000, 1.000] | 0.188 [0.054, 0.332] | PASS |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| s0 | 61 | 8 | 7 | 1.000 [1.000, 1.000] | 0.129 [0.052, 0.222] | PASS |
| s1 | 63 | 13 | 5 | 1.000 [1.000, 1.000] | 0.203 [0.029, 0.393] | PASS |
| s2 | 64 | 14 | 9 | 1.000 [1.000, 1.000] | 0.219 [0.073, 0.381] | PASS |
| s3 | 52 | 10 | 4 | 1.000 [1.000, 1.000] | 0.196 [0.016, 0.387] | insufficient |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| parallel_peer_swap | 48 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| plant_loop_mapping | 44 | 3 | 1 | 1.000 [1.000, 1.000] | 0.068 [0.000, 0.188] | insufficient |
| same_medium_branch | 56 | 22 | 1 | 1.000 [1.000, 1.000] | 0.393 [0.393, 0.393] | insufficient |
| sensor_mapping | 40 | 14 | 5 | 1.000 [1.000, 1.000] | 0.350 [0.188, 0.500] | PASS |
| vav_zone_swap | 40 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| wrong_ahu_mapping | 12 | 6 | 3 | 1.000 [1.000, 1.000] | 0.500 [0.500, 0.500] | insufficient |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| ahu_sat | 8 | 2 | 1 | 1.000 [1.000, 1.000] | 0.250 [0.250, 0.250] | insufficient |
| ahu_vav | 12 | 6 | 3 | 1.000 [1.000, 1.000] | 0.500 [0.500, 0.500] | insufficient |
| branch_coil | 56 | 22 | 1 | 1.000 [1.000, 1.000] | 0.393 [0.393, 0.393] | insufficient |
| coil_ahu | 16 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| coil_vav | 24 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| loop_branch | 44 | 3 | 1 | 1.000 [1.000, 1.000] | 0.068 [0.000, 0.188] | insufficient |
| loop_source | 8 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| vav_dat | 32 | 12 | 4 | 1.000 [1.000, 1.000] | 0.375 [0.125, 0.500] | insufficient |
| vav_zone | 40 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

Cells (season x family x slot): 35; PASS: 0, INCONCLUSIVE: 0, FAIL: 0, insufficient: 35

Calibration (answered verdicts), ECE = 0.037 over n=45

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 45 | 0.963 | 1.000 |

Calibration (ALL crossed verdicts, answered or flagged), ECE = 0.034 over n=109

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 109 | 0.964 | 0.930 |

### C3 precise abstention

| bucket | episodes | resolvable | share | coverage of resolvable | status |
| --- | --- | --- | --- | --- | --- |
| season=s0 | 61 | 12 | 0.20 | 0.500 [0.143, 1.000] | n/a (resolvable share < 30%) |
| season=s1 | 63 | 6 | 0.10 | 0.500 [0.000, 1.000] | n/a (resolvable share < 30%) |
| season=s2 | 64 | 16 | 0.25 | 0.375 [0.120, 0.765] | n/a (resolvable share < 30%) |
| season=s3 | 52 | 8 | 0.15 | 0.375 [0.000, 1.000] | n/a (resolvable share < 30%) |
| slot=ahu_sat | 8 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=ahu_vav | 12 | 12 | 1.00 | 0.500 [0.000, 1.000] | PASS |
| slot=branch_coil | 56 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=coil_ahu | 16 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=coil_vav | 24 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_branch | 44 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_source | 8 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_dat | 32 | 30 | 0.94 | 0.400 [0.053, 1.000] | PASS |
| slot=vav_zone | 40 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 0.882 [0.744, 0.980] vs answered 0.600 [0.000, 0.852]; margin 0.282 [0.030, 0.873] -> PASS (flagged n=195, answered n=45)

(c) coverage of resolvable cases lost to flags: 0.571 [0.174, 0.857] of 42 resolvable episodes

**C3 status: PASS** (a: PASS)

### C4 knows its limits: 35 of 35 conditions are not C2-PASS; violations (flagged < 90%): 12 -> **FAIL**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| s0|parallel_peer_swap|coil_ahu | insufficient | 0 | 3 | 1.00 | yes |
| s0|parallel_peer_swap|coil_vav | insufficient | 0 | 10 | 1.00 | yes |
| s0|parallel_peer_swap|loop_source | insufficient | 0 | 3 | 1.00 | yes |
| s0|plant_loop_mapping|loop_branch | insufficient | 1 | 13 | 0.92 | yes |
| s0|same_medium_branch|branch_coil | insufficient | 0 | 9 | 1.00 | yes |
| s0|sensor_mapping|ahu_sat | insufficient | 1 | 2 | 0.50 | NO |
| s0|sensor_mapping|vav_dat | insufficient | 4 | 10 | 0.60 | NO |
| s0|vav_zone_swap|vav_zone | insufficient | 0 | 8 | 1.00 | yes |
| s0|wrong_ahu_mapping|ahu_vav | insufficient | 2 | 3 | 0.33 | NO |
| s1|parallel_peer_swap|coil_ahu | insufficient | 0 | 7 | 1.00 | yes |
| s1|parallel_peer_swap|coil_vav | insufficient | 0 | 3 | 1.00 | yes |
| s1|parallel_peer_swap|loop_source | insufficient | 0 | 1 | 1.00 | yes |
| s1|plant_loop_mapping|loop_branch | insufficient | 1 | 14 | 0.93 | yes |
| s1|same_medium_branch|branch_coil | insufficient | 9 | 19 | 0.53 | NO |
| s1|sensor_mapping|ahu_sat | insufficient | 0 | 2 | 1.00 | yes |
| s1|sensor_mapping|vav_dat | insufficient | 2 | 4 | 0.50 | NO |
| s1|vav_zone_swap|vav_zone | insufficient | 0 | 11 | 1.00 | yes |
| s1|wrong_ahu_mapping|ahu_vav | insufficient | 1 | 2 | 0.50 | NO |
| s2|parallel_peer_swap|coil_ahu | insufficient | 0 | 2 | 1.00 | yes |
| s2|parallel_peer_swap|coil_vav | insufficient | 0 | 6 | 1.00 | yes |
| s2|parallel_peer_swap|loop_source | insufficient | 0 | 2 | 1.00 | yes |
| s2|plant_loop_mapping|loop_branch | insufficient | 1 | 11 | 0.91 | yes |
| s2|same_medium_branch|branch_coil | insufficient | 6 | 13 | 0.54 | NO |
| s2|sensor_mapping|ahu_sat | insufficient | 1 | 4 | 0.75 | NO |
| s2|sensor_mapping|vav_dat | insufficient | 3 | 11 | 0.73 | NO |
| s2|vav_zone_swap|vav_zone | insufficient | 0 | 9 | 1.00 | yes |
| s2|wrong_ahu_mapping|ahu_vav | insufficient | 3 | 6 | 0.50 | NO |
| s3|parallel_peer_swap|coil_ahu | insufficient | 0 | 4 | 1.00 | yes |
| s3|parallel_peer_swap|coil_vav | insufficient | 0 | 5 | 1.00 | yes |
| s3|parallel_peer_swap|loop_source | insufficient | 0 | 2 | 1.00 | yes |
| s3|plant_loop_mapping|loop_branch | insufficient | 0 | 6 | 1.00 | yes |
| s3|same_medium_branch|branch_coil | insufficient | 7 | 15 | 0.53 | NO |
| s3|sensor_mapping|vav_dat | insufficient | 3 | 7 | 0.57 | NO |
| s3|vav_zone_swap|vav_zone | insufficient | 0 | 12 | 1.00 | yes |
| s3|wrong_ahu_mapping|ahu_vav | insufficient | 0 | 1 | 1.00 | yes |

## Layer `new` (240 episodes per policy, 52 clusters)

### Headline per policy (same layer; class-balanced; 95% cluster-bootstrap CI)

| policy | answered coverage | accuracy among answered | readings among answered |
| --- | --- | --- | --- |
| active | 0.146 [0.061, 0.257] | 1.000 [1.000, 1.000] | 3.8 [2.9, 5.1] |
| frozen | 0.000 [0.000, 0.000] | n/a | 0.0 [0.0, 0.0] |
| random | 0.071 [0.026, 0.141] | 1.000 [1.000, 1.000] | 14.3 [8.1, 15.2] |
| traversal | 0.000 [0.000, 0.000] | n/a | 0.0 [0.0, 0.0] |
| traversal_block | 0.000 [0.000, 0.000] | n/a | 0.0 [0.0, 0.0] |

### C1 efficiency: readings saved by active vs baseline (paired, among episodes answered by both)

| baseline | pairs | readings saved | coverage active - base | status |
| --- | --- | --- | --- | --- |
| random | 12 | 9.25 [8.42, 10.00] | 0.075 [-0.005, 0.172] | PASS |
| traversal_block | 0 | n/a | n/a | n/a |
| traversal | 0 | n/a | n/a | n/a |
| frozen | 0 | n/a | n/a | n/a |

### C2 honest confidence (nominal 0.95; PASS: point>=0.93 and lower>=0.90; cells need >=8 answered and >=5 clusters)

| all | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| all | 240 | 35 | 11 | 1.000 [1.000, 1.000] | 0.146 [0.061, 0.257] | PASS |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| s0 | 61 | 12 | 8 | 1.000 [1.000, 1.000] | 0.197 [0.075, 0.348] | PASS |
| s1 | 63 | 6 | 5 | 1.000 [1.000, 1.000] | 0.095 [0.024, 0.211] | insufficient |
| s2 | 64 | 11 | 8 | 1.000 [1.000, 1.000] | 0.172 [0.064, 0.296] | PASS |
| s3 | 52 | 6 | 5 | 1.000 [1.000, 1.000] | 0.116 [0.031, 0.240] | insufficient |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| parallel_peer_swap | 48 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| plant_loop_mapping | 44 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| same_medium_branch | 56 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| sensor_mapping | 40 | 23 | 6 | 1.000 [1.000, 1.000] | 0.575 [0.188, 0.761] | PASS |
| vav_zone_swap | 40 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| wrong_ahu_mapping | 12 | 12 | 5 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | PASS |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| ahu_sat | 8 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| ahu_vav | 12 | 12 | 5 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | PASS |
| branch_coil | 56 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| coil_ahu | 16 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| coil_vav | 24 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| loop_branch | 44 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| loop_source | 8 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| vav_dat | 32 | 23 | 6 | 1.000 [1.000, 1.000] | 0.719 [0.557, 0.875] | PASS |
| vav_zone | 40 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

Cells (season x family x slot): 35; PASS: 1, INCONCLUSIVE: 0, FAIL: 0, insufficient: 34

Calibration (answered verdicts), ECE = 0.058 over n=35

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.90,0.95) | 31 | 0.938 | 1.000 |
| [0.95,1.00) | 4 | 0.973 | 1.000 |

Calibration (ALL crossed verdicts, answered or flagged), ECE = 0.120 over n=105

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.60,0.70) | 5 | 0.652 | 1.000 |
| [0.70,0.80) | 18 | 0.716 | 0.860 |
| [0.80,0.90) | 8 | 0.882 | 0.435 |
| [0.90,0.95) | 65 | 0.936 | 1.000 |
| [0.95,1.00) | 9 | 0.979 | 1.000 |

### C3 precise abstention

| bucket | episodes | resolvable | share | coverage of resolvable | status |
| --- | --- | --- | --- | --- | --- |
| season=s0 | 61 | 12 | 0.20 | 1.000 [1.000, 1.000] | n/a (resolvable share < 30%) |
| season=s1 | 63 | 6 | 0.10 | 1.000 [1.000, 1.000] | n/a (resolvable share < 30%) |
| season=s2 | 64 | 16 | 0.25 | 0.688 [0.429, 0.917] | n/a (resolvable share < 30%) |
| season=s3 | 52 | 8 | 0.15 | 0.750 [0.500, 1.000] | n/a (resolvable share < 30%) |
| slot=ahu_sat | 8 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=ahu_vav | 12 | 12 | 1.00 | 1.000 [1.000, 1.000] | PASS |
| slot=branch_coil | 56 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=coil_ahu | 16 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=coil_vav | 24 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_branch | 44 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=loop_source | 8 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_dat | 32 | 30 | 0.94 | 0.767 [0.607, 0.913] | PASS |
| slot=vav_zone | 40 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 0.971 [0.928, 0.996] vs answered 0.000 [0.000, 0.000]; margin 0.971 [0.928, 0.996] -> PASS (flagged n=205, answered n=35)

(c) coverage of resolvable cases lost to flags: 0.167 [0.042, 0.275] of 42 resolvable episodes

**C3 status: PASS** (a: PASS)

### C4 knows its limits: 34 of 35 conditions are not C2-PASS; violations (flagged < 90%): 7 -> **FAIL**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| s0|parallel_peer_swap|coil_ahu | insufficient | 0 | 3 | 1.00 | yes |
| s0|parallel_peer_swap|coil_vav | insufficient | 0 | 10 | 1.00 | yes |
| s0|parallel_peer_swap|loop_source | insufficient | 0 | 3 | 1.00 | yes |
| s0|plant_loop_mapping|loop_branch | insufficient | 0 | 13 | 1.00 | yes |
| s0|same_medium_branch|branch_coil | insufficient | 0 | 9 | 1.00 | yes |
| s0|sensor_mapping|ahu_sat | insufficient | 0 | 2 | 1.00 | yes |
| s0|vav_zone_swap|vav_zone | insufficient | 0 | 8 | 1.00 | yes |
| s0|wrong_ahu_mapping|ahu_vav | insufficient | 3 | 3 | 0.00 | NO |
| s1|parallel_peer_swap|coil_ahu | insufficient | 0 | 7 | 1.00 | yes |
| s1|parallel_peer_swap|coil_vav | insufficient | 0 | 3 | 1.00 | yes |
| s1|parallel_peer_swap|loop_source | insufficient | 0 | 1 | 1.00 | yes |
| s1|plant_loop_mapping|loop_branch | insufficient | 0 | 14 | 1.00 | yes |
| s1|same_medium_branch|branch_coil | insufficient | 0 | 19 | 1.00 | yes |
| s1|sensor_mapping|ahu_sat | insufficient | 0 | 2 | 1.00 | yes |
| s1|sensor_mapping|vav_dat | insufficient | 4 | 4 | 0.00 | NO |
| s1|vav_zone_swap|vav_zone | insufficient | 0 | 11 | 1.00 | yes |
| s1|wrong_ahu_mapping|ahu_vav | insufficient | 2 | 2 | 0.00 | NO |
| s2|parallel_peer_swap|coil_ahu | insufficient | 0 | 2 | 1.00 | yes |
| s2|parallel_peer_swap|coil_vav | insufficient | 0 | 6 | 1.00 | yes |
| s2|parallel_peer_swap|loop_source | insufficient | 0 | 2 | 1.00 | yes |
| s2|plant_loop_mapping|loop_branch | insufficient | 0 | 11 | 1.00 | yes |
| s2|same_medium_branch|branch_coil | insufficient | 0 | 13 | 1.00 | yes |
| s2|sensor_mapping|ahu_sat | insufficient | 0 | 4 | 1.00 | yes |
| s2|sensor_mapping|vav_dat | insufficient | 5 | 11 | 0.55 | NO |
| s2|vav_zone_swap|vav_zone | insufficient | 0 | 9 | 1.00 | yes |
| s2|wrong_ahu_mapping|ahu_vav | insufficient | 6 | 6 | 0.00 | NO |
| s3|parallel_peer_swap|coil_ahu | insufficient | 0 | 4 | 1.00 | yes |
| s3|parallel_peer_swap|coil_vav | insufficient | 0 | 5 | 1.00 | yes |
| s3|parallel_peer_swap|loop_source | insufficient | 0 | 2 | 1.00 | yes |
| s3|plant_loop_mapping|loop_branch | insufficient | 0 | 6 | 1.00 | yes |
| s3|same_medium_branch|branch_coil | insufficient | 0 | 15 | 1.00 | yes |
| s3|sensor_mapping|vav_dat | insufficient | 5 | 7 | 0.29 | NO |
| s3|vav_zone_swap|vav_zone | insufficient | 0 | 12 | 1.00 | yes |
| s3|wrong_ahu_mapping|ahu_vav | insufficient | 1 | 1 | 0.00 | NO |
