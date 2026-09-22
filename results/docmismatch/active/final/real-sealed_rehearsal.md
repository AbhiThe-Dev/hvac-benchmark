real-sealed_rehearsal: 720 episodes (6 clusters = days); config variant=sel_slice, tau=0.95, primary setting `day`; elapsed 54s; info={"n_outer": 3600, "beta": {"vav_zone": 1.0, "vav_sat": 0.7, "vav_pwr": 0.7}}

# Readiness evaluation: real-sealed_rehearsal

## Layer `none` (720 episodes per policy, 6 clusters)

### Headline per policy (same layer; class-balanced; 95% cluster-bootstrap CI)

| policy | answered coverage | accuracy among answered | readings among answered |
| --- | --- | --- | --- |
| active | 0.046 [0.037, 0.056] | 1.000 [1.000, 1.000] | 7.8 [6.6, 9.0] |
| frozen | 0.048 [0.040, 0.056] | 1.000 [1.000, 1.000] | 6.7 [5.0, 8.5] |
| random | 0.003 [0.000, 0.008] | 1.000 [1.000, 1.000] | 11.5 [0.0, 11.5] |
| traversal | 0.000 [0.000, 0.000] | n/a | 0.0 [0.0, 0.0] |
| traversal_block | 0.028 [0.017, 0.044] | 1.000 [1.000, 1.000] | 17.4 [6.8, 18.0] |

### C1 efficiency: readings saved by active vs baseline (paired, among episodes answered by both)

| baseline | pairs | readings saved | coverage active - base | status |
| --- | --- | --- | --- | --- |
| random | 0 | n/a | n/a | n/a |
| traversal_block | 6 | n/a | 0.019 [-0.006, 0.037] | FAIL |
| traversal | 0 | n/a | n/a | n/a |
| frozen | 25 | -1.18 [-2.27, -0.59] | -0.002 [-0.008, 0.003] | FAIL |

### C2 honest confidence (nominal 0.95; PASS: point>=0.93 and lower>=0.90; cells need >=8 answered and >=5 clusters)

| all | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| all | 720 | 32 | 6 | 1.000 [1.000, 1.000] | 0.046 [0.037, 0.056] | PASS |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| spring | 720 | 32 | 6 | 1.000 [1.000, 1.000] | 0.046 [0.037, 0.056] | PASS |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| VAV power point swap | 240 | 16 | 5 | 1.000 [1.000, 1.000] | 0.044 [0.025, 0.061] | PASS |
| VAV supply-temp point swap | 240 | 1 | 1 | 1.000 [1.000, 1.000] | 0.003 [0.000, 0.008] | insufficient |
| VAV-zone swap | 240 | 15 | 6 | 1.000 [1.000, 1.000] | 0.092 [0.067, 0.117] | PASS |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| vav_pwr | 240 | 16 | 5 | 1.000 [1.000, 1.000] | 0.044 [0.025, 0.061] | PASS |
| vav_sat | 240 | 1 | 1 | 1.000 [1.000, 1.000] | 0.003 [0.000, 0.008] | insufficient |
| vav_zone | 240 | 15 | 6 | 1.000 [1.000, 1.000] | 0.092 [0.067, 0.117] | PASS |

Cells (season x family x slot): 3; PASS: 2, INCONCLUSIVE: 0, FAIL: 0, insufficient: 1

Calibration (answered verdicts), ECE = 0.036 over n=32

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 32 | 0.964 | 1.000 |

Calibration (ALL crossed verdicts, answered or flagged), ECE = 0.036 over n=32

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 32 | 0.964 | 1.000 |

### C3 precise abstention

| bucket | episodes | resolvable | share | coverage of resolvable | status |
| --- | --- | --- | --- | --- | --- |
| season=spring | 720 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_pwr | 240 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_sat | 240 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_zone | 240 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 1.000 [1.000, 1.000] vs answered 1.000 [1.000, 1.000]; margin 0.000 [0.000, 0.000] -> FAIL (flagged n=688, answered n=32)

(c) coverage of resolvable cases lost to flags: n/a of 0 resolvable episodes

**C3 status: FAIL** (a: n/a)

### C4 knows its limits: 1 of 3 conditions are not C2-PASS; violations (flagged < 90%): 0 -> **PASS**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| spring|VAV supply-temp point swap|vav_sat | insufficient | 1 | 240 | 1.00 | yes |

## Layer `legacy` (720 episodes per policy, 6 clusters)

### Headline per policy (same layer; class-balanced; 95% cluster-bootstrap CI)

| policy | answered coverage | accuracy among answered | readings among answered |
| --- | --- | --- | --- |
| active | 0.001 [0.000, 0.003] | 1.000 [1.000, 1.000] | 4.5 [0.0, 4.5] |
| frozen | 0.003 [0.001, 0.005] | 1.000 [1.000, 1.000] | 6.0 [4.0, 10.0] |
| random | 0.000 [0.000, 0.000] | n/a | 0.0 [0.0, 0.0] |
| traversal | 0.000 [0.000, 0.000] | n/a | 0.0 [0.0, 0.0] |
| traversal_block | 0.000 [0.000, 0.000] | n/a | 0.0 [0.0, 0.0] |

### C1 efficiency: readings saved by active vs baseline (paired, among episodes answered by both)

| baseline | pairs | readings saved | coverage active - base | status |
| --- | --- | --- | --- | --- |
| random | 0 | n/a | n/a | n/a |
| traversal_block | 0 | n/a | n/a | n/a |
| traversal | 0 | n/a | n/a | n/a |
| frozen | 1 | n/a | -0.002 [-0.004, 0.000] | FAIL |

### C2 honest confidence (nominal 0.95; PASS: point>=0.93 and lower>=0.90; cells need >=8 answered and >=5 clusters)

| all | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| all | 720 | 1 | 1 | 1.000 [1.000, 1.000] | 0.001 [0.000, 0.003] | insufficient |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| spring | 720 | 1 | 1 | 1.000 [1.000, 1.000] | 0.001 [0.000, 0.003] | insufficient |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| VAV power point swap | 240 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| VAV supply-temp point swap | 240 | 1 | 1 | 1.000 [1.000, 1.000] | 0.003 [0.000, 0.008] | insufficient |
| VAV-zone swap | 240 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| vav_pwr | 240 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| vav_sat | 240 | 1 | 1 | 1.000 [1.000, 1.000] | 0.003 [0.000, 0.008] | insufficient |
| vav_zone | 240 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

Cells (season x family x slot): 3; PASS: 0, INCONCLUSIVE: 0, FAIL: 0, insufficient: 3

Calibration (answered verdicts), ECE = 0.046 over n=1

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 1 | 0.954 | 1.000 |

Calibration (ALL crossed verdicts, answered or flagged), ECE = 0.036 over n=32

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |
| [0.95,1.00) | 32 | 0.964 | 1.000 |

### C3 precise abstention

| bucket | episodes | resolvable | share | coverage of resolvable | status |
| --- | --- | --- | --- | --- | --- |
| season=spring | 720 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_pwr | 240 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_sat | 240 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_zone | 240 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 1.000 [1.000, 1.000] vs answered 1.000 [1.000, 1.000]; margin 0.000 [0.000, 0.000] -> FAIL (flagged n=719, answered n=1)

(c) coverage of resolvable cases lost to flags: n/a of 0 resolvable episodes

**C3 status: FAIL** (a: n/a)

### C4 knows its limits: 3 of 3 conditions are not C2-PASS; violations (flagged < 90%): 0 -> **PASS**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| spring|VAV power point swap|vav_pwr | insufficient | 0 | 240 | 1.00 | yes |
| spring|VAV supply-temp point swap|vav_sat | insufficient | 1 | 240 | 1.00 | yes |
| spring|VAV-zone swap|vav_zone | insufficient | 0 | 240 | 1.00 | yes |

## Layer `new` (720 episodes per policy, 6 clusters)

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
| all | 720 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

| season | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| spring | 720 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

| family | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| VAV power point swap | 240 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| VAV supply-temp point swap | 240 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| VAV-zone swap | 240 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

| slot | episodes | answered | clusters | accuracy among answered | coverage | status |
| --- | --- | --- | --- | --- | --- | --- |
| vav_pwr | 240 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| vav_sat | 240 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |
| vav_zone | 240 | 0 | 0 | n/a | 0.000 [0.000, 0.000] | insufficient |

Cells (season x family x slot): 3; PASS: 0, INCONCLUSIVE: 0, FAIL: 0, insufficient: 3

Calibration (answered verdicts), ECE = n/a over n=0

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |

Calibration (ALL crossed verdicts, answered or flagged), ECE = n/a over n=0

| conf bin | n | mean conf | realised accuracy |
| --- | --- | --- | --- |

### C3 precise abstention

| bucket | episodes | resolvable | share | coverage of resolvable | status |
| --- | --- | --- | --- | --- | --- |
| season=spring | 720 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_pwr | 240 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_sat | 240 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |
| slot=vav_zone | 240 | 0 | 0.00 | n/a | n/a (resolvable share < 30%) |

(b) flags carry information: share unresolvable-or-would-be-wrong: flagged 1.000 [1.000, 1.000] vs answered n/a; margin n/a -> FAIL (flagged n=720, answered n=0)

(c) coverage of resolvable cases lost to flags: n/a of 0 resolvable episodes

**C3 status: FAIL** (a: n/a)

### C4 knows its limits: 3 of 3 conditions are not C2-PASS; violations (flagged < 90%): 0 -> **PASS**

| condition (season|family|slot) | C2 | answered | episodes | flag rate | ok |
| --- | --- | --- | --- | --- | --- |
| spring|VAV power point swap|vav_pwr | insufficient | 0 | 240 | 1.00 | yes |
| spring|VAV supply-temp point swap|vav_sat | insufficient | 0 | 240 | 1.00 | yes |
| spring|VAV-zone swap|vav_zone | insufficient | 0 | 240 | 1.00 | yes |
