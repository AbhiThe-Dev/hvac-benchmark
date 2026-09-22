real-dev-nested_v5_sel: 3600 episodes (30 clusters = days); config variant=sel, tau=0.95, primary setting `day`; elapsed 292s; info={"0": {"beta": {"vav_zone": 0.35, "vav_sat": 0.5, "vav_pwr": 0.5}, "n_outer": 7200, "n_inner": 10800}, "1": {"beta": {"vav_zone": 1.0, "vav_sat": 0.35, "vav_pwr": 0.5}, "n_outer": 3600, "n_inner": 14400}, "2": {"beta": {"vav_zone": 1.0, "vav_sat": 0.5, "vav_pwr": 0.5}, "n_outer": 3600, "n_inner": 14400}, "3": {"beta": {"vav_zone": 1.0, "vav_sat": 0.1, "vav_pwr": 0.2}, "n_outer": 3600, "n_inner": 1

# Readiness evaluation: real-dev-nested_v5_sel

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
| VAV power point swap | 1200 | 204 | 21 | 0.946 [0.884, 0.992] | 0.166 [0.106, 0.226] | INCONCLUSIVE |
| VAV supply-temp point swap | 1200 | 166 | 12 | 0.972 [0.935, 1.000] | 0.120 [0.068, 0.177] | PASS |
| VAV-zone swap | 1200 | 120 | 14 | 0.835 [0.748, 0.926] | 0.124 [0.066, 0.186] | FAIL |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| vav_pwr | 1200 | 204 | 21 | 0.946 [0.884, 0.992] | 0.166 [0.106, 0.226] | INCONCLUSIVE |
| vav_sat | 1200 | 166 | 12 | 0.972 [0.935, 1.000] | 0.120 [0.068, 0.177] | PASS |
| vav_zone | 1200 | 120 | 14 | 0.835 [0.748, 0.926] | 0.124 [0.066, 0.186] | FAIL |

Cells (season x family x slot): 12; PASS: 2, INCONCLUSIVE: 1, FAIL: 2, insufficient: 7

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
| season=winter | 720 | 1 | 0.00 | 0.000 [0.000, 0.000] | n/a (resolvable share < 30%) |
| slot=vav_pwr | 1200 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_sat | 1200 | 1 | 0.00 | 0.000 [0.000, 0.000] | n/a (resolvable share < 30%) |
| slot=vav_zone | 1200 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 1.000 [0.999, 1.000] vs answered 1.000 [1.000, 1.000]; margin -0.000 [-0.001, 0.000] -> FAIL (flagged n=3110, answered n=490)

(c) coverage of resolvable cases lost to flags: 1.000 [1.000, 1.000] of 1 resolvable episodes

**C3 status: FAIL** (a: n/a)

### C4 knows its limits: 10 of 12 conditions are not C2-PASS; violations (flagged < 90%): 3 -> **FAIL**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| fall|VAV-zone swap|vav_zone | insufficient | 15 | 480 | 0.95 | yes |
| spring|VAV power point swap|vav_pwr | insufficient | 4 | 240 | 0.99 | yes |
| spring|VAV supply-temp point swap|vav_sat | insufficient | 0 | 240 | 1.00 | yes |
| spring|VAV-zone swap|vav_zone | INCONCLUSIVE | 46 | 240 | 0.76 | NO |
| summer|VAV power point swap|vav_pwr | insufficient | 3 | 240 | 0.97 | yes |
| summer|VAV supply-temp point swap|vav_sat | insufficient | 1 | 240 | 0.99 | yes |
| summer|VAV-zone swap|vav_zone | insufficient | 0 | 240 | 1.00 | yes |
| winter|VAV power point swap|vav_pwr | FAIL | 35 | 240 | 0.78 | NO |
| winter|VAV supply-temp point swap|vav_sat | insufficient | 5 | 240 | 0.97 | yes |
| winter|VAV-zone swap|vav_zone | FAIL | 59 | 240 | 0.72 | NO |

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
| VAV power point swap | 1200 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| VAV supply-temp point swap | 1200 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| VAV-zone swap | 1200 | 20 | 6 | 1.000 [1.000, 1.000] | 0.011 [0.002, 0.024] | PASS |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| vav_pwr | 1200 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| vav_sat | 1200 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| vav_zone | 1200 | 20 | 6 | 1.000 [1.000, 1.000] | 0.011 [0.002, 0.024] | PASS |

Cells (season x family x slot): 12; PASS: 1, INCONCLUSIVE: 0, FAIL: 0, insufficient: 11

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
| season=winter | 720 | 1 | 0.00 | 0.000 [0.000, 0.000] | n/a (resolvable share < 30%) |
| slot=vav_pwr | 1200 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_sat | 1200 | 1 | 0.00 | 0.000 [0.000, 0.000] | n/a (resolvable share < 30%) |
| slot=vav_zone | 1200 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 1.000 [0.999, 1.000] vs answered 1.000 [1.000, 1.000]; margin -0.000 [-0.001, 0.000] -> FAIL (flagged n=3580, answered n=20)

(c) coverage of resolvable cases lost to flags: 1.000 [1.000, 1.000] of 1 resolvable episodes

**C3 status: FAIL** (a: n/a)

### C4 knows its limits: 11 of 12 conditions are not C2-PASS; violations (flagged < 90%): 0 -> **PASS**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| fall|VAV power point swap|vav_pwr | insufficient | 0 | 480 | 1.00 | yes |
| fall|VAV supply-temp point swap|vav_sat | insufficient | 0 | 480 | 1.00 | yes |
| fall|VAV-zone swap|vav_zone | insufficient | 0 | 480 | 1.00 | yes |
| spring|VAV power point swap|vav_pwr | insufficient | 0 | 240 | 1.00 | yes |
| spring|VAV supply-temp point swap|vav_sat | insufficient | 0 | 240 | 1.00 | yes |
| summer|VAV power point swap|vav_pwr | insufficient | 0 | 240 | 1.00 | yes |
| summer|VAV supply-temp point swap|vav_sat | insufficient | 0 | 240 | 1.00 | yes |
| summer|VAV-zone swap|vav_zone | insufficient | 0 | 240 | 1.00 | yes |
| winter|VAV power point swap|vav_pwr | insufficient | 0 | 240 | 1.00 | yes |
| winter|VAV supply-temp point swap|vav_sat | insufficient | 0 | 240 | 1.00 | yes |
| winter|VAV-zone swap|vav_zone | insufficient | 0 | 240 | 1.00 | yes |

## Layer `new` (3600 episodes per policy, 30 clusters)

### Headline per policy (same layer; class-balanced; 95% cluster-bootstrap CI)

| policy | answered coverage | accuracy among answered | readings among answered |
| --- | --- | --- | --- |
| active | 0.002 [0.000, 0.006] | 0.818 [0.818, 0.818] | 6.5 [0.0, 6.5] |
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
| all | 3600 | 5 | 1 | 0.818 [0.818, 0.818] | 0.002 [0.000, 0.006] | insufficient |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| fall | 1440 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| spring | 720 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| summer | 720 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| winter | 720 | 5 | 1 | 0.818 [0.818, 0.818] | 0.010 [0.000, 0.037] | insufficient |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| VAV power point swap | 1200 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| VAV supply-temp point swap | 1200 | 5 | 1 | 0.818 [0.818, 0.818] | 0.006 [0.000, 0.018] | insufficient |
| VAV-zone swap | 1200 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| vav_pwr | 1200 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| vav_sat | 1200 | 5 | 1 | 0.818 [0.818, 0.818] | 0.006 [0.000, 0.018] | insufficient |
| vav_zone | 1200 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

Cells (season x family x slot): 12; PASS: 0, INCONCLUSIVE: 0, FAIL: 0, insufficient: 12

Calibration (answered verdicts), ECE = 0.483 over n=5

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 5 | 0.983 | 0.500 |

Calibration (ALL crossed verdicts, answered or flagged), ECE = 0.116 over n=149

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.70,0.80) | 13 | 0.763 | 0.800 |
| [0.80,0.90) | 79 | 0.848 | 0.843 |
| [0.90,0.95) | 6 | 0.912 | 1.000 |
| [0.95,1.00) | 51 | 0.979 | 0.667 |

### C3 precise abstention

| bucket | episodes | resolvable | share | coverage of resolvable | status |
| --- | --- | --- | --- | --- | --- |
| season=fall | 1440 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| season=spring | 720 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| season=summer | 720 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| season=winter | 720 | 1 | 0.00 | 0.000 [0.000, 0.000] | n/a (resolvable share < 30%) |
| slot=vav_pwr | 1200 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_sat | 1200 | 1 | 0.00 | 0.000 [0.000, 0.000] | n/a (resolvable share < 30%) |
| slot=vav_zone | 1200 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 1.000 [0.999, 1.000] vs answered 1.000 [1.000, 1.000]; margin -0.000 [-0.001, -0.000] -> FAIL (flagged n=3595, answered n=5)

(c) coverage of resolvable cases lost to flags: 1.000 [1.000, 1.000] of 1 resolvable episodes

**C3 status: FAIL** (a: n/a)

### C4 knows its limits: 12 of 12 conditions are not C2-PASS; violations (flagged < 90%): 0 -> **PASS**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| fall|VAV power point swap|vav_pwr | insufficient | 0 | 480 | 1.00 | yes |
| fall|VAV supply-temp point swap|vav_sat | insufficient | 0 | 480 | 1.00 | yes |
| fall|VAV-zone swap|vav_zone | insufficient | 0 | 480 | 1.00 | yes |
| spring|VAV power point swap|vav_pwr | insufficient | 0 | 240 | 1.00 | yes |
| spring|VAV supply-temp point swap|vav_sat | insufficient | 0 | 240 | 1.00 | yes |
| spring|VAV-zone swap|vav_zone | insufficient | 0 | 240 | 1.00 | yes |
| summer|VAV power point swap|vav_pwr | insufficient | 0 | 240 | 1.00 | yes |
| summer|VAV supply-temp point swap|vav_sat | insufficient | 0 | 240 | 1.00 | yes |
| summer|VAV-zone swap|vav_zone | insufficient | 0 | 240 | 1.00 | yes |
| winter|VAV power point swap|vav_pwr | insufficient | 0 | 240 | 1.00 | yes |
| winter|VAV supply-temp point swap|vav_sat | insufficient | 5 | 240 | 0.97 | yes |
| winter|VAV-zone swap|vav_zone | insufficient | 0 | 240 | 1.00 | yes |
