real-sealed: 3840 episodes (32 clusters = days); config variant=sel_slice, tau=0.95, primary setting `day`; elapsed 169s; info={"n_outer": 19200, "beta": {"vav_zone": 1.0, "vav_sat": 0.5, "vav_pwr": 0.5}}

# Readiness evaluation: real-sealed

## Layer `none` (3840 episodes per policy, 32 clusters)

### Headline per policy (same layer; class-balanced; 95% cluster-bootstrap CI)

| policy | answered coverage | accuracy among answered | readings among answered |
| --- | --- | --- | --- |
| active | 0.084 [0.051, 0.121] | 0.936 [0.883, 0.969] | 11.6 [9.9, 13.3] |
| frozen | 0.079 [0.045, 0.118] | 0.905 [0.829, 0.959] | 10.1 [8.4, 11.7] |
| random | 0.007 [0.003, 0.012] | 0.900 [0.733, 1.000] | 14.3 [12.2, 16.6] |
| traversal | 0.001 [0.000, 0.002] | 0.750 [0.750, 0.750] | 2.0 [0.0, 2.0] |
| traversal_block | 0.019 [0.008, 0.033] | 0.869 [0.625, 0.966] | 16.3 [12.3, 21.3] |

### C1 efficiency: readings saved by active vs baseline (paired, among episodes answered by both)

| baseline | pairs | readings saved | coverage active - base | status |
| --- | --- | --- | --- | --- |
| random | 12 | 6.12 [2.30, 10.50] | 0.077 [0.046, 0.112] | PASS |
| traversal_block | 40 | 10.88 [4.55, 16.25] | 0.065 [0.038, 0.097] | PASS |
| traversal | 1 | n/a | 0.083 [0.051, 0.121] | FAIL |
| frozen | 161 | -0.09 [-0.73, 0.53] | 0.005 [-0.008, 0.017] | FAIL |

### C2 honest confidence (nominal 0.95; PASS: point>=0.93 and lower>=0.90; cells need >=8 answered and >=5 clusters)

| all | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| all | 3840 | 231 | 24 | 0.936 [0.883, 0.969] | 0.084 [0.051, 0.121] | INCONCLUSIVE |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| fall | 960 | 33 | 5 | 0.987 [0.500, 1.000] | 0.055 [0.002, 0.129] | INCONCLUSIVE |
| spring | 960 | 104 | 7 | 0.986 [0.964, 1.000] | 0.144 [0.062, 0.236] | PASS |
| summer | 960 | 37 | 5 | 0.976 [0.970, 1.000] | 0.058 [0.007, 0.152] | PASS |
| winter | 960 | 57 | 7 | 0.779 [0.717, 0.847] | 0.078 [0.042, 0.113] | FAIL |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| VAV power point swap | 1280 | 71 | 16 | 0.994 [0.980, 1.000] | 0.091 [0.045, 0.146] | PASS |
| VAV supply-temp point swap | 1280 | 25 | 7 | 1.000 [1.000, 1.000] | 0.035 [0.010, 0.066] | PASS |
| VAV-zone swap | 1280 | 135 | 19 | 0.876 [0.778, 0.939] | 0.126 [0.073, 0.189] | FAIL |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| vav_pwr | 1280 | 71 | 16 | 0.994 [0.980, 1.000] | 0.091 [0.045, 0.146] | PASS |
| vav_sat | 1280 | 25 | 7 | 1.000 [1.000, 1.000] | 0.035 [0.010, 0.066] | PASS |
| vav_zone | 1280 | 135 | 19 | 0.876 [0.778, 0.939] | 0.126 [0.073, 0.189] | FAIL |

Cells (season x family x slot): 12; PASS: 1, INCONCLUSIVE: 0, FAIL: 1, insufficient: 10

Calibration (answered verdicts), ECE = 0.116 over n=231

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 231 | 0.968 | 0.852 |

Calibration (ALL crossed verdicts, answered or flagged), ECE = 0.116 over n=231

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 231 | 0.968 | 0.852 |

### C3 precise abstention

| bucket | episodes | resolvable | share | coverage of resolvable | status |
| --- | --- | --- | --- | --- | --- |
| season=fall | 960 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| season=spring | 960 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| season=summer | 960 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| season=winter | 960 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_pwr | 1280 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_sat | 1280 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_zone | 1280 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 1.000 [1.000, 1.000] vs answered 1.000 [1.000, 1.000]; margin 0.000 [0.000, 0.000] -> FAIL (flagged n=3609, answered n=231)

(c) coverage of resolvable cases lost to flags: n/a of 0 resolvable episodes

**C3 status: FAIL** (a: n/a)

### C4 knows its limits: 11 of 12 conditions are not C2-PASS; violations (flagged < 90%): 1 -> **FAIL**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| fall|VAV power point swap|vav_pwr | insufficient | 19 | 320 | 0.94 | yes |
| fall|VAV supply-temp point swap|vav_sat | insufficient | 8 | 320 | 0.97 | yes |
| fall|VAV-zone swap|vav_zone | insufficient | 6 | 320 | 0.98 | yes |
| spring|VAV power point swap|vav_pwr | insufficient | 20 | 320 | 0.94 | yes |
| spring|VAV supply-temp point swap|vav_sat | insufficient | 7 | 320 | 0.98 | yes |
| summer|VAV power point swap|vav_pwr | insufficient | 19 | 320 | 0.94 | yes |
| summer|VAV supply-temp point swap|vav_sat | insufficient | 9 | 320 | 0.97 | yes |
| summer|VAV-zone swap|vav_zone | insufficient | 9 | 320 | 0.97 | yes |
| winter|VAV power point swap|vav_pwr | insufficient | 13 | 320 | 0.96 | yes |
| winter|VAV supply-temp point swap|vav_sat | insufficient | 1 | 320 | 1.00 | yes |
| winter|VAV-zone swap|vav_zone | FAIL | 43 | 320 | 0.87 | NO |

## Layer `legacy` (3840 episodes per policy, 32 clusters)

### Headline per policy (same layer; class-balanced; 95% cluster-bootstrap CI)

| policy | answered coverage | accuracy among answered | readings among answered |
| --- | --- | --- | --- |
| active | 0.002 [0.000, 0.005] | 1.000 [1.000, 1.000] | 6.7 [5.5, 9.0] |
| frozen | 0.002 [0.000, 0.005] | 1.000 [1.000, 1.000] | 6.4 [5.1, 9.5] |
| random | 0.000 [0.000, 0.000] | n/a | 0.0 [0.0, 0.0] |
| traversal | 0.000 [0.000, 0.000] | n/a | 0.0 [0.0, 0.0] |
| traversal_block | 0.000 [0.000, 0.000] | n/a | 0.0 [0.0, 0.0] |

### C1 efficiency: readings saved by active vs baseline (paired, among episodes answered by both)

| baseline | pairs | readings saved | coverage active - base | status |
| --- | --- | --- | --- | --- |
| random | 0 | n/a | n/a | n/a |
| traversal_block | 0 | n/a | n/a | n/a |
| traversal | 0 | n/a | n/a | n/a |
| frozen | 11 | n/a | 0.000 [-0.001, 0.001] | FAIL |

### C2 honest confidence (nominal 0.95; PASS: point>=0.93 and lower>=0.90; cells need >=8 answered and >=5 clusters)

| all | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| all | 3840 | 14 | 5 | 1.000 [1.000, 1.000] | 0.002 [0.000, 0.005] | PASS |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| fall | 960 | 5 | 2 | 1.000 [1.000, 1.000] | 0.003 [0.000, 0.010] | insufficient |
| spring | 960 | 2 | 1 | 1.000 [1.000, 1.000] | 0.001 [0.000, 0.005] | insufficient |
| summer | 960 | 7 | 2 | 1.000 [1.000, 1.000] | 0.005 [0.000, 0.014] | insufficient |
| winter | 960 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| VAV power point swap | 1280 | 14 | 5 | 1.000 [1.000, 1.000] | 0.007 [0.001, 0.016] | PASS |
| VAV supply-temp point swap | 1280 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| VAV-zone swap | 1280 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| vav_pwr | 1280 | 14 | 5 | 1.000 [1.000, 1.000] | 0.007 [0.001, 0.016] | PASS |
| vav_sat | 1280 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| vav_zone | 1280 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

Cells (season x family x slot): 12; PASS: 0, INCONCLUSIVE: 0, FAIL: 0, insufficient: 12

Calibration (answered verdicts), ECE = 0.042 over n=14

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 14 | 0.958 | 1.000 |

Calibration (ALL crossed verdicts, answered or flagged), ECE = 0.116 over n=231

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 231 | 0.968 | 0.852 |

### C3 precise abstention

| bucket | episodes | resolvable | share | coverage of resolvable | status |
| --- | --- | --- | --- | --- | --- |
| season=fall | 960 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| season=spring | 960 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| season=summer | 960 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| season=winter | 960 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_pwr | 1280 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_sat | 1280 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_zone | 1280 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 1.000 [1.000, 1.000] vs answered 1.000 [1.000, 1.000]; margin 0.000 [0.000, 0.000] -> FAIL (flagged n=3826, answered n=14)

(c) coverage of resolvable cases lost to flags: n/a of 0 resolvable episodes

**C3 status: FAIL** (a: n/a)

### C4 knows its limits: 12 of 12 conditions are not C2-PASS; violations (flagged < 90%): 0 -> **PASS**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| fall|VAV power point swap|vav_pwr | insufficient | 5 | 320 | 0.98 | yes |
| fall|VAV supply-temp point swap|vav_sat | insufficient | 0 | 320 | 1.00 | yes |
| fall|VAV-zone swap|vav_zone | insufficient | 0 | 320 | 1.00 | yes |
| spring|VAV power point swap|vav_pwr | insufficient | 2 | 320 | 0.99 | yes |
| spring|VAV supply-temp point swap|vav_sat | insufficient | 0 | 320 | 1.00 | yes |
| spring|VAV-zone swap|vav_zone | insufficient | 0 | 320 | 1.00 | yes |
| summer|VAV power point swap|vav_pwr | insufficient | 7 | 320 | 0.98 | yes |
| summer|VAV supply-temp point swap|vav_sat | insufficient | 0 | 320 | 1.00 | yes |
| summer|VAV-zone swap|vav_zone | insufficient | 0 | 320 | 1.00 | yes |
| winter|VAV power point swap|vav_pwr | insufficient | 0 | 320 | 1.00 | yes |
| winter|VAV supply-temp point swap|vav_sat | insufficient | 0 | 320 | 1.00 | yes |
| winter|VAV-zone swap|vav_zone | insufficient | 0 | 320 | 1.00 | yes |

## Layer `new` (3840 episodes per policy, 32 clusters)

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
| all | 3840 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| fall | 960 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| spring | 960 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| summer | 960 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| winter | 960 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| VAV power point swap | 1280 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| VAV supply-temp point swap | 1280 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| VAV-zone swap | 1280 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| vav_pwr | 1280 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| vav_sat | 1280 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| vav_zone | 1280 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

Cells (season x family x slot): 12; PASS: 0, INCONCLUSIVE: 0, FAIL: 0, insufficient: 12

Calibration (answered verdicts), ECE = n/a over n=0

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |

Calibration (ALL crossed verdicts, answered or flagged), ECE = n/a over n=0

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |

### C3 precise abstention

| bucket | episodes | resolvable | share | coverage of resolvable | status |
| --- | --- | --- | --- | --- | --- |
| season=fall | 960 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| season=spring | 960 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| season=summer | 960 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| season=winter | 960 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_pwr | 1280 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_sat | 1280 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_zone | 1280 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 1.000 [1.000, 1.000] vs answered n/a; margin n/a -> FAIL (flagged n=3840, answered n=0)

(c) coverage of resolvable cases lost to flags: n/a of 0 resolvable episodes

**C3 status: FAIL** (a: n/a)

### C4 knows its limits: 12 of 12 conditions are not C2-PASS; violations (flagged < 90%): 0 -> **PASS**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| fall|VAV power point swap|vav_pwr | insufficient | 0 | 320 | 1.00 | yes |
| fall|VAV supply-temp point swap|vav_sat | insufficient | 0 | 320 | 1.00 | yes |
| fall|VAV-zone swap|vav_zone | insufficient | 0 | 320 | 1.00 | yes |
| spring|VAV power point swap|vav_pwr | insufficient | 0 | 320 | 1.00 | yes |
| spring|VAV supply-temp point swap|vav_sat | insufficient | 0 | 320 | 1.00 | yes |
| spring|VAV-zone swap|vav_zone | insufficient | 0 | 320 | 1.00 | yes |
| summer|VAV power point swap|vav_pwr | insufficient | 0 | 320 | 1.00 | yes |
| summer|VAV supply-temp point swap|vav_sat | insufficient | 0 | 320 | 1.00 | yes |
| summer|VAV-zone swap|vav_zone | insufficient | 0 | 320 | 1.00 | yes |
| winter|VAV power point swap|vav_pwr | insufficient | 0 | 320 | 1.00 | yes |
| winter|VAV supply-temp point swap|vav_sat | insufficient | 0 | 320 | 1.00 | yes |
| winter|VAV-zone swap|vav_zone | insufficient | 0 | 320 | 1.00 | yes |
