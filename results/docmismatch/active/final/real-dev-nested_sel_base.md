real-dev-nested_sel_base: 3600 episodes (30 clusters = days); config variant=sel, tau=0.95, primary setting `day`; elapsed 135s; info={"0": {"beta": {"vav_zone": 0.35, "vav_sat": 0.5, "vav_pwr": 0.5}, "n_outer": 7200, "n_inner": 10800}, "1": {"beta": {"vav_zone": 1.0, "vav_sat": 0.35, "vav_pwr": 0.5}, "n_outer": 3600, "n_inner": 14400}, "2": {"beta": {"vav_zone": 1.0, "vav_sat": 0.5, "vav_pwr": 0.5}, "n_outer": 3600, "n_inner": 14400}, "3": {"beta": {"vav_zone": 1.0, "vav_sat": 0.1, "vav_pwr": 0.2}, "n_outer": 3600, "n_inner": 1

# Readiness evaluation: real-dev-nested_sel_base

## Layer `none` (3600 episodes per policy, 30 clusters)

### Headline per policy (same layer; class-balanced; 95% cluster-bootstrap CI)

| policy | answered coverage | accuracy among answered | readings among answered |
| --- | --- | --- | --- |
| active | 0.137 [0.095, 0.178] | 0.920 [0.868, 0.965] | 7.2 [6.5, 8.1] |
| frozen | 0.132 [0.090, 0.174] | 0.933 [0.888, 0.974] | 7.7 [7.0, 8.4] |
| random | 0.018 [0.009, 0.028] | 0.876 [0.740, 1.000] | 16.3 [13.3, 18.1] |
| traversal | 0.000 [0.000, 0.000] | n/a | 0.0 [0.0, 0.0] |
| traversal_block | 0.045 [0.028, 0.065] | 0.905 [0.839, 0.988] | 10.2 [7.1, 12.8] |

### C1 efficiency: readings saved by active vs baseline (paired, among episodes answered by both)

| baseline | pairs | readings saved | coverage active - base | status |
| --- | --- | --- | --- | --- |
| random | 43 | 10.65 [5.67, 13.78] | 0.119 [0.082, 0.154] | PASS |
| traversal_block | 102 | 2.80 [0.64, 5.23] | 0.092 [0.061, 0.123] | PASS |
| traversal | 0 | n/a | n/a | n/a |
| frozen | 435 | 1.15 [0.68, 1.57] | 0.005 [-0.004, 0.015] | PASS |

### C2 honest confidence (nominal 0.95; PASS: point>=0.93 and lower>=0.90; cells need >=8 answered and >=5 clusters)

| all | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| all | 3600 | 490 | 24 | 0.920 [0.868, 0.965] | 0.137 [0.095, 0.178] | FAIL |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| fall | 1440 | 337 | 10 | 0.971 [0.941, 0.995] | 0.205 [0.134, 0.263] | PASS |
| spring | 720 | 50 | 6 | 0.957 [0.902, 1.000] | 0.085 [0.070, 0.104] | PASS |
| summer | 720 | 4 | 3 | 1.000 [1.000, 1.000] | 0.011 [0.000, 0.022] | insufficient |
| winter | 720 | 99 | 5 | 0.780 [0.699, 0.937] | 0.177 [0.075, 0.296] | FAIL |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| VAV power point swap | 900 | 157 | 16 | n/a | n/a | insufficient |
| VAV supply-temp point swap | 900 | 141 | 11 | n/a | n/a | insufficient |
| VAV-zone swap | 900 | 68 | 13 | n/a | n/a | insufficient |
| clean | 900 | 124 | 24 | n/a | n/a | insufficient |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| vav_pwr | 1200 | 204 | 21 | 0.946 [0.884, 0.992] | 0.166 [0.106, 0.226] | INCONCLUSIVE |
| vav_sat | 1200 | 166 | 12 | 0.972 [0.935, 1.000] | 0.120 [0.068, 0.177] | PASS |
| vav_zone | 1200 | 120 | 14 | 0.835 [0.748, 0.926] | 0.124 [0.066, 0.186] | FAIL |

Cells (season x family x slot): 24; PASS: 0, INCONCLUSIVE: 0, FAIL: 0, insufficient: 24

Calibration (answered verdicts), ECE = 0.049 over n=490

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 490 | 0.969 | 0.920 |

Calibration (ALL crossed verdicts, answered or flagged), ECE = 0.049 over n=490

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 490 | 0.969 | 0.920 |

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

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 1.000 [1.000, 1.000] vs answered 1.000 [1.000, 1.000]; margin 0.000 [0.000, 0.000] -> FAIL (flagged n=3110, answered n=490)

(c) coverage of resolvable cases lost to flags: n/a of 0 resolvable episodes

**C3 status: FAIL** (a: n/a)

### C4 knows its limits: 24 of 24 conditions are not C2-PASS; violations (flagged < 90%): 24 -> **FAIL**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| fall|VAV power point swap|vav_pwr | insufficient | 140 | 360 | nan | NO |
| fall|VAV supply-temp point swap|vav_sat | insufficient | 139 | 360 | nan | NO |
| fall|VAV-zone swap|vav_zone | insufficient | 5 | 360 | nan | NO |
| fall|clean|vav_pwr | insufficient | 22 | 120 | nan | NO |
| fall|clean|vav_sat | insufficient | 21 | 120 | nan | NO |
| fall|clean|vav_zone | insufficient | 10 | 120 | nan | NO |
| spring|VAV power point swap|vav_pwr | insufficient | 4 | 180 | nan | NO |
| spring|VAV supply-temp point swap|vav_sat | insufficient | 0 | 180 | nan | NO |
| spring|VAV-zone swap|vav_zone | insufficient | 25 | 180 | nan | NO |
| spring|clean|vav_pwr | insufficient | 0 | 60 | nan | NO |
| spring|clean|vav_sat | insufficient | 0 | 60 | nan | NO |
| spring|clean|vav_zone | insufficient | 21 | 60 | nan | NO |
| summer|VAV power point swap|vav_pwr | insufficient | 0 | 180 | nan | NO |
| summer|VAV supply-temp point swap|vav_sat | insufficient | 0 | 180 | nan | NO |
| summer|VAV-zone swap|vav_zone | insufficient | 0 | 180 | nan | NO |
| summer|clean|vav_pwr | insufficient | 3 | 60 | nan | NO |
| summer|clean|vav_sat | insufficient | 1 | 60 | nan | NO |
| summer|clean|vav_zone | insufficient | 0 | 60 | nan | NO |
| winter|VAV power point swap|vav_pwr | insufficient | 13 | 180 | nan | NO |
| winter|VAV supply-temp point swap|vav_sat | insufficient | 2 | 180 | nan | NO |
| winter|VAV-zone swap|vav_zone | insufficient | 38 | 180 | nan | NO |
| winter|clean|vav_pwr | insufficient | 22 | 60 | nan | NO |
| winter|clean|vav_sat | insufficient | 3 | 60 | nan | NO |
| winter|clean|vav_zone | insufficient | 21 | 60 | nan | NO |

## Layer `legacy` (3600 episodes per policy, 30 clusters)

### Headline per policy (same layer; class-balanced; 95% cluster-bootstrap CI)

| policy | answered coverage | accuracy among answered | readings among answered |
| --- | --- | --- | --- |
| active | 0.004 [0.001, 0.008] | 1.000 [1.000, 1.000] | 10.2 [9.1, 10.9] |
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
| all | 3600 | 20 | 6 | 1.000 [1.000, 1.000] | 0.004 [0.001, 0.008] | PASS |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| fall | 1440 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| spring | 720 | 20 | 6 | 1.000 [1.000, 1.000] | 0.019 [0.008, 0.034] | PASS |
| summer | 720 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| winter | 720 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| VAV power point swap | 900 | 0 | 0 | n/a | n/a | insufficient |
| VAV supply-temp point swap | 900 | 0 | 0 | n/a | n/a | insufficient |
| VAV-zone swap | 900 | 20 | 6 | n/a | n/a | insufficient |
| clean | 900 | 0 | 0 | n/a | n/a | insufficient |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| vav_pwr | 1200 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| vav_sat | 1200 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| vav_zone | 1200 | 20 | 6 | 1.000 [1.000, 1.000] | 0.011 [0.002, 0.024] | PASS |

Cells (season x family x slot): 24; PASS: 0, INCONCLUSIVE: 0, FAIL: 0, insufficient: 24

Calibration (answered verdicts), ECE = 0.028 over n=20

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 20 | 0.972 | 1.000 |

Calibration (ALL crossed verdicts, answered or flagged), ECE = 0.049 over n=490

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 490 | 0.969 | 0.920 |

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

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 1.000 [1.000, 1.000] vs answered 1.000 [1.000, 1.000]; margin 0.000 [0.000, 0.000] -> FAIL (flagged n=3580, answered n=20)

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
| spring|VAV-zone swap|vav_zone | insufficient | 20 | 180 | nan | NO |
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
