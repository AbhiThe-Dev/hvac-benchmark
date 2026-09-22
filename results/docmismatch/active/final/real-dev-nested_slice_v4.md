real-dev-nested_slice_v4: 3600 episodes (30 clusters = days); config variant=sel_slice, tau=0.95, primary setting `day`; elapsed 283s; info={"0": {"beta": {"vav_zone": 0.35, "vav_sat": 0.7, "vav_pwr": 0.7}, "n_outer": 7200, "n_inner": 10800}, "1": {"beta": {"vav_zone": 1.0, "vav_sat": 0.7, "vav_pwr": 0.7}, "n_outer": 3600, "n_inner": 14400}, "2": {"beta": {"vav_zone": 1.0, "vav_sat": 0.7, "vav_pwr": 0.7}, "n_outer": 3600, "n_inner": 14400}, "3": {"beta": {"vav_zone": 1.0, "vav_sat": 0.2, "vav_pwr": 0.2}, "n_outer": 3600, "n_inner": 14

# Readiness evaluation: real-dev-nested_slice_v4

## Layer `none` (3600 episodes per policy, 30 clusters)

### Headline per policy (same layer; class-balanced; 95% cluster-bootstrap CI)

| policy | answered coverage | accuracy among answered | readings among answered |
| --- | --- | --- | --- |
| active | 0.112 [0.074, 0.151] | 0.954 [0.911, 0.990] | 9.5 [8.7, 10.5] |
| frozen | 0.104 [0.070, 0.141] | 0.950 [0.906, 0.988] | 9.2 [8.3, 10.0] |
| random | 0.011 [0.005, 0.017] | 0.845 [0.633, 1.000] | 19.2 [17.2, 21.0] |
| traversal | 0.000 [0.000, 0.000] | n/a | 0.0 [0.0, 0.0] |
| traversal_block | 0.041 [0.029, 0.055] | 0.964 [0.917, 0.994] | 13.2 [11.8, 15.1] |

### C1 efficiency: readings saved by active vs baseline (paired, among episodes answered by both)

| baseline | pairs | readings saved | coverage active - base | status |
| --- | --- | --- | --- | --- |
| random | 24 | 12.58 [4.79, 16.14] | 0.101 [0.066, 0.137] | PASS |
| traversal_block | 93 | 3.65 [1.60, 6.35] | 0.071 [0.041, 0.101] | PASS |
| traversal | 0 | n/a | n/a | n/a |
| frozen | 369 | 0.92 [0.32, 1.49] | 0.007 [-0.001, 0.017] | PASS |

### C2 honest confidence (nominal 0.95; PASS: point>=0.93 and lower>=0.90; cells need >=8 answered and >=5 clusters)

| all | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| all | 3600 | 428 | 27 | 0.954 [0.911, 0.990] | 0.112 [0.074, 0.151] | PASS |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| fall | 1440 | 343 | 11 | 0.978 [0.951, 0.997] | 0.209 [0.141, 0.266] | PASS |
| spring | 720 | 32 | 6 | 1.000 [1.000, 1.000] | 0.046 [0.035, 0.057] | PASS |
| summer | 720 | 6 | 6 | 1.000 [1.000, 1.000] | 0.017 [0.017, 0.017] | insufficient |
| winter | 720 | 47 | 4 | 0.788 [0.657, 0.925] | 0.079 [0.003, 0.178] | insufficient |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| VAV power point swap | 900 | 176 | 17 | n/a | n/a | insufficient |
| VAV supply-temp point swap | 900 | 133 | 12 | n/a | n/a | insufficient |
| VAV-zone swap | 900 | 31 | 8 | n/a | n/a | insufficient |
| clean | 900 | 88 | 25 | n/a | n/a | insufficient |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| vav_pwr | 1200 | 224 | 23 | 0.975 [0.953, 0.995] | 0.178 [0.111, 0.255] | PASS |
| vav_sat | 1200 | 150 | 12 | 0.973 [0.928, 1.000] | 0.102 [0.055, 0.153] | PASS |
| vav_zone | 1200 | 54 | 12 | 0.850 [0.742, 0.984] | 0.056 [0.022, 0.101] | FAIL |

Cells (season x family x slot): 24; PASS: 0, INCONCLUSIVE: 0, FAIL: 0, insufficient: 24

Calibration (answered verdicts), ECE = 0.012 over n=428

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 428 | 0.964 | 0.952 |

Calibration (ALL crossed verdicts, answered or flagged), ECE = 0.012 over n=428

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 428 | 0.964 | 0.952 |

### C3 precise abstention

| bucket | episodes | resolvable | share | coverage of resolvable | status |
| --- | --- | --- | --- | --- | --- |
| season=fall | 1440 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| season=spring | 720 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| season=summer | 720 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| season=winter | 720 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_pwr | 1200 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_sat | 1200 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_zone | 1200 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 1.000 [1.000, 1.000] vs answered 1.000 [1.000, 1.000]; margin 0.000 [0.000, 0.000] -> FAIL (flagged n=3172, answered n=428)

(c) coverage of resolvable cases lost to flags: n/a of 0 resolvable episodes

**C3 status: FAIL** (a: n/a)

### C4 knows its limits: 24 of 24 conditions are not C2-PASS; violations (flagged < 90%): 24 -> **FAIL**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| fall|VAV power point swap|vav_pwr | insufficient | 158 | 360 | nan | NO |
| fall|VAV supply-temp point swap|vav_sat | insufficient | 130 | 360 | nan | NO |
| fall|VAV-zone swap|vav_zone | insufficient | 1 | 360 | nan | NO |
| fall|clean|vav_pwr | insufficient | 36 | 120 | nan | NO |
| fall|clean|vav_sat | insufficient | 14 | 120 | nan | NO |
| fall|clean|vav_zone | insufficient | 4 | 120 | nan | NO |
| spring|VAV power point swap|vav_pwr | insufficient | 16 | 180 | nan | NO |
| spring|VAV supply-temp point swap|vav_sat | insufficient | 1 | 180 | nan | NO |
| spring|VAV-zone swap|vav_zone | insufficient | 6 | 180 | nan | NO |
| spring|clean|vav_pwr | insufficient | 0 | 60 | nan | NO |
| spring|clean|vav_sat | insufficient | 0 | 60 | nan | NO |
| spring|clean|vav_zone | insufficient | 9 | 60 | nan | NO |
| summer|VAV power point swap|vav_pwr | insufficient | 0 | 180 | nan | NO |
| summer|VAV supply-temp point swap|vav_sat | insufficient | 0 | 180 | nan | NO |
| summer|VAV-zone swap|vav_zone | insufficient | 0 | 180 | nan | NO |
| summer|clean|vav_pwr | insufficient | 6 | 60 | nan | NO |
| summer|clean|vav_sat | insufficient | 0 | 60 | nan | NO |
| summer|clean|vav_zone | insufficient | 0 | 60 | nan | NO |
| winter|VAV power point swap|vav_pwr | insufficient | 2 | 180 | nan | NO |
| winter|VAV supply-temp point swap|vav_sat | insufficient | 2 | 180 | nan | NO |
| winter|VAV-zone swap|vav_zone | insufficient | 24 | 180 | nan | NO |
| winter|clean|vav_pwr | insufficient | 6 | 60 | nan | NO |
| winter|clean|vav_sat | insufficient | 3 | 60 | nan | NO |
| winter|clean|vav_zone | insufficient | 10 | 60 | nan | NO |

## Layer `legacy` (3600 episodes per policy, 30 clusters)

### Headline per policy (same layer; class-balanced; 95% cluster-bootstrap CI)

| policy | answered coverage | accuracy among answered | readings among answered |
| --- | --- | --- | --- |
| active | 0.000 [0.000, 0.001] | 1.000 [1.000, 1.000] | 4.5 [0.0, 4.5] |
| frozen | 0.001 [0.000, 0.001] | 1.000 [1.000, 1.000] | 7.0 [4.0, 10.0] |
| random | 0.000 [0.000, 0.000] | n/a | 0.0 [0.0, 0.0] |
| traversal | 0.000 [0.000, 0.000] | n/a | 0.0 [0.0, 0.0] |
| traversal_block | 0.001 [0.000, 0.002] | 1.000 [1.000, 1.000] | 5.7 [0.0, 5.7] |

### C1 efficiency: readings saved by active vs baseline (paired, among episodes answered by both)

| baseline | pairs | readings saved | coverage active - base | status |
| --- | --- | --- | --- | --- |
| random | 0 | n/a | n/a | n/a |
| traversal_block | 0 | n/a | n/a | n/a |
| traversal | 0 | n/a | n/a | n/a |
| frozen | 1 | n/a | -0.001 [-0.001, 0.000] | FAIL |

### C2 honest confidence (nominal 0.95; PASS: point>=0.93 and lower>=0.90; cells need >=8 answered and >=5 clusters)

| all | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| all | 3600 | 1 | 1 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.001] | insufficient |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| fall | 1440 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| spring | 720 | 1 | 1 | 1.000 [1.000, 1.000] | 0.001 [0.000, 0.003] | insufficient |
| summer | 720 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| winter | 720 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| VAV power point swap | 900 | 0 | 0 | n/a | n/a | insufficient |
| VAV supply-temp point swap | 900 | 1 | 1 | n/a | n/a | insufficient |
| VAV-zone swap | 900 | 0 | 0 | n/a | n/a | insufficient |
| clean | 900 | 0 | 0 | n/a | n/a | insufficient |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| vav_pwr | 1200 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| vav_sat | 1200 | 1 | 1 | 1.000 [1.000, 1.000] | 0.001 [0.000, 0.002] | insufficient |
| vav_zone | 1200 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

Cells (season x family x slot): 24; PASS: 0, INCONCLUSIVE: 0, FAIL: 0, insufficient: 24

Calibration (answered verdicts), ECE = 0.046 over n=1

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 1 | 0.954 | 1.000 |

Calibration (ALL crossed verdicts, answered or flagged), ECE = 0.012 over n=428

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 428 | 0.964 | 0.952 |

### C3 precise abstention

| bucket | episodes | resolvable | share | coverage of resolvable | status |
| --- | --- | --- | --- | --- | --- |
| season=fall | 1440 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| season=spring | 720 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| season=summer | 720 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| season=winter | 720 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_pwr | 1200 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_sat | 1200 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_zone | 1200 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 1.000 [1.000, 1.000] vs answered 1.000 [1.000, 1.000]; margin 0.000 [0.000, 0.000] -> FAIL (flagged n=3599, answered n=1)

(c) coverage of resolvable cases lost to flags: n/a of 0 resolvable episodes

**C3 status: FAIL** (a: n/a)

### C4 knows its limits: 24 of 24 conditions are not C2-PASS; violations (flagged < 90%): 24 -> **FAIL**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| fall|VAV power point swap|vav_pwr | insufficient | 0 | 360 | nan | NO |
| fall|VAV supply-temp point swap|vav_sat | insufficient | 0 | 360 | nan | NO |
| fall|VAV-zone swap|vav_zone | insufficient | 0 | 360 | nan | NO |
| fall|clean|vav_pwr | insufficient | 0 | 120 | nan | NO |
| fall|clean|vav_sat | insufficient | 0 | 120 | nan | NO |
| fall|clean|vav_zone | insufficient | 0 | 120 | nan | NO |
| spring|VAV power point swap|vav_pwr | insufficient | 0 | 180 | nan | NO |
| spring|VAV supply-temp point swap|vav_sat | insufficient | 1 | 180 | nan | NO |
| spring|VAV-zone swap|vav_zone | insufficient | 0 | 180 | nan | NO |
| spring|clean|vav_pwr | insufficient | 0 | 60 | nan | NO |
| spring|clean|vav_sat | insufficient | 0 | 60 | nan | NO |
| spring|clean|vav_zone | insufficient | 0 | 60 | nan | NO |
| summer|VAV power point swap|vav_pwr | insufficient | 0 | 180 | nan | NO |
| summer|VAV supply-temp point swap|vav_sat | insufficient | 0 | 180 | nan | NO |
| summer|VAV-zone swap|vav_zone | insufficient | 0 | 180 | nan | NO |
| summer|clean|vav_pwr | insufficient | 0 | 60 | nan | NO |
| summer|clean|vav_sat | insufficient | 0 | 60 | nan | NO |
| summer|clean|vav_zone | insufficient | 0 | 60 | nan | NO |
| winter|VAV power point swap|vav_pwr | insufficient | 0 | 180 | nan | NO |
| winter|VAV supply-temp point swap|vav_sat | insufficient | 0 | 180 | nan | NO |
| winter|VAV-zone swap|vav_zone | insufficient | 0 | 180 | nan | NO |
| winter|clean|vav_pwr | insufficient | 0 | 60 | nan | NO |
| winter|clean|vav_sat | insufficient | 0 | 60 | nan | NO |
| winter|clean|vav_zone | insufficient | 0 | 60 | nan | NO |

## Layer `new` (3600 episodes per policy, 30 clusters)

### Headline per policy (same layer; class-balanced; 95% cluster-bootstrap CI)

| policy | answered coverage | accuracy among answered | readings among answered |
| --- | --- | --- | --- |
| active | 0.000 [0.000, 0.000] | n/a | 0.0 [0.0, 0.0] |
| frozen | 0.000 [0.000, 0.000] | n/a | 0.0 [0.0, 0.0] |
| random | 0.000 [0.000, 0.000] | n/a | 0.0 [0.0, 0.0] |
| traversal | 0.000 [0.000, 0.000] | n/a | 0.0 [0.0, 0.0] |
| traversal_block | 0.000 [0.000, 0.000] | n/a | 0.0 [0.0, 0.0] |

### C1 efficiency: readings saved by active vs baseline (paired, among episodes answered by both)

| baseline | pairs | readings saved | coverage active - base | status |
| --- | --- | --- | --- | --- |
| random | 0 | n/a | n/a | n/a |
| traversal_block | 0 | n/a | n/a | n/a |
| traversal | 0 | n/a | n/a | n/a |
| frozen | 0 | n/a | n/a | n/a |

### C2 honest confidence (nominal 0.95; PASS: point>=0.93 and lower>=0.90; cells need >=8 answered and >=5 clusters)

| all | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| all | 3600 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| fall | 1440 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| spring | 720 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| summer | 720 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| winter | 720 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| VAV power point swap | 900 | 0 | 0 | n/a | n/a | insufficient |
| VAV supply-temp point swap | 900 | 0 | 0 | n/a | n/a | insufficient |
| VAV-zone swap | 900 | 0 | 0 | n/a | n/a | insufficient |
| clean | 900 | 0 | 0 | n/a | n/a | insufficient |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| vav_pwr | 1200 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| vav_sat | 1200 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| vav_zone | 1200 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

Cells (season x family x slot): 24; PASS: 0, INCONCLUSIVE: 0, FAIL: 0, insufficient: 24

Calibration (answered verdicts), ECE = n/a over n=0

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |

Calibration (ALL crossed verdicts, answered or flagged), ECE = n/a over n=0

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |

### C3 precise abstention

| bucket | episodes | resolvable | share | coverage of resolvable | status |
| --- | --- | --- | --- | --- | --- |
| season=fall | 1440 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| season=spring | 720 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| season=summer | 720 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| season=winter | 720 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_pwr | 1200 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_sat | 1200 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_zone | 1200 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 1.000 [1.000, 1.000] vs answered n/a; margin n/a -> FAIL (flagged n=3600, answered n=0)

(c) coverage of resolvable cases lost to flags: n/a of 0 resolvable episodes

**C3 status: FAIL** (a: n/a)

### C4 knows its limits: 24 of 24 conditions are not C2-PASS; violations (flagged < 90%): 24 -> **FAIL**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| fall|VAV power point swap|vav_pwr | insufficient | 0 | 360 | nan | NO |
| fall|VAV supply-temp point swap|vav_sat | insufficient | 0 | 360 | nan | NO |
| fall|VAV-zone swap|vav_zone | insufficient | 0 | 360 | nan | NO |
| fall|clean|vav_pwr | insufficient | 0 | 120 | nan | NO |
| fall|clean|vav_sat | insufficient | 0 | 120 | nan | NO |
| fall|clean|vav_zone | insufficient | 0 | 120 | nan | NO |
| spring|VAV power point swap|vav_pwr | insufficient | 0 | 180 | nan | NO |
| spring|VAV supply-temp point swap|vav_sat | insufficient | 0 | 180 | nan | NO |
| spring|VAV-zone swap|vav_zone | insufficient | 0 | 180 | nan | NO |
| spring|clean|vav_pwr | insufficient | 0 | 60 | nan | NO |
| spring|clean|vav_sat | insufficient | 0 | 60 | nan | NO |
| spring|clean|vav_zone | insufficient | 0 | 60 | nan | NO |
| summer|VAV power point swap|vav_pwr | insufficient | 0 | 180 | nan | NO |
| summer|VAV supply-temp point swap|vav_sat | insufficient | 0 | 180 | nan | NO |
| summer|VAV-zone swap|vav_zone | insufficient | 0 | 180 | nan | NO |
| summer|clean|vav_pwr | insufficient | 0 | 60 | nan | NO |
| summer|clean|vav_sat | insufficient | 0 | 60 | nan | NO |
| summer|clean|vav_zone | insufficient | 0 | 60 | nan | NO |
| winter|VAV power point swap|vav_pwr | insufficient | 0 | 180 | nan | NO |
| winter|VAV supply-temp point swap|vav_sat | insufficient | 0 | 180 | nan | NO |
| winter|VAV-zone swap|vav_zone | insufficient | 0 | 180 | nan | NO |
| winter|clean|vav_pwr | insufficient | 0 | 60 | nan | NO |
| winter|clean|vav_sat | insufficient | 0 | 60 | nan | NO |
| winter|clean|vav_zone | insufficient | 0 | 60 | nan | NO |
