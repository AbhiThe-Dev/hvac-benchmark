# Addendum 15, Part B: wiring the dither campaign into the engine (`vav_zone`)

112 `vav_zone` episodes (7 train-role topologies, 56 wrong / 56 right documentation), each scored under every (season, code seed 4-6) campaign realisation of its own building; stage 1 = frozen passive engine leave-one-topology-out with the futility rule; stage 2 = campaign escalation with a conditional-logit link fitted on the other 6 buildings' campaigns. Resolved = verdict rows / all rows; accuracy among resolved is class-balanced; false alarm = REFUTED on a right document; missed fault = CONFIRMED on a wrong document; localised = the most probable owner is the true one (wrong documents). CI = building-cluster bootstrap (500). Simulation only.

Passive stage: 112 episodes; resolved passively 0; stopped as futile 112; mean passive reads 8.3. Code-path check passed (campaign truth == pool truth).

Fitted link strength kappa (per held-out building; `*` = unbounded, the ML link is not finite): L=96 h: 30, 30, 30, 30, 30, 30, 30; L=168 h: 30, 30, 30, 30, 30, 30, 30

## P0 passive only (futility on)

| policy / subset | rows | resolved [CI] | acc \| resolved [CI] | wrong & confident | false alarms | missed faults | localised (wrong docs) | passive reads / row | campaign h / row | campaign h / correct verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| pooled | 112 | 0.00 [0.00, 0.00] | nan n/a | 0.0% | 0.0% | 0.0% | 0.00 | 8.3 | 0 | - |
| july | 112 | 0.00 [0.00, 0.00] | nan n/a | 0.0% | 0.0% | 0.0% | 0.00 | 8.3 | 0 | - |
| january | 112 | 0.00 [0.00, 0.00] | nan n/a | 0.0% | 0.0% | 0.0% | 0.00 | 8.3 | 0 | - |

Frozen rule: pooled **FAILS**; july FAILS, january FAILS

## P1 passive, then 96 h campaign

| policy / subset | rows | resolved [CI] | acc \| resolved [CI] | wrong & confident | false alarms | missed faults | localised (wrong docs) | passive reads / row | campaign h / row | campaign h / correct verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| pooled | 672 | 0.94 [0.92, 0.97] | 1.000 [1.00, 1.00] | 0.0% | 0.0% | 0.0% | 0.93 | 8.3 | 96 | 102 |
| july | 336 | 0.96 [0.94, 0.99] | 1.000 [1.00, 1.00] | 0.0% | 0.0% | 0.0% | 0.97 | 8.3 | 96 | 100 |
| january | 336 | 0.93 [0.88, 0.97] | 1.000 [1.00, 1.00] | 0.0% | 0.0% | 0.0% | 0.89 | 8.3 | 96 | 104 |

Frozen rule: pooled **PASSES**; july PASSES, january PASSES

## P2 passive, then 168 h campaign

| policy / subset | rows | resolved [CI] | acc \| resolved [CI] | wrong & confident | false alarms | missed faults | localised (wrong docs) | passive reads / row | campaign h / row | campaign h / correct verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| pooled | 672 | 0.95 [0.94, 0.97] | 1.000 [1.00, 1.00] | 0.0% | 0.0% | 0.0% | 0.98 | 8.3 | 168 | 176 |
| july | 336 | 0.99 [0.99, 1.00] | 1.000 [1.00, 1.00] | 0.0% | 0.0% | 0.0% | 1.00 | 8.3 | 168 | 169 |
| january | 336 | 0.91 [0.88, 0.94] | 1.000 [1.00, 1.00] | 0.0% | 0.0% | 0.0% | 0.95 | 8.3 | 168 | 184 |

Frozen rule: pooled **PASSES**; july PASSES, january PASSES

## C campaign only, 96 h (descriptive)

| policy / subset | rows | resolved [CI] | acc \| resolved [CI] | wrong & confident | false alarms | missed faults | localised (wrong docs) | passive reads / row | campaign h / row | campaign h / correct verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| pooled | 672 | 0.94 [0.92, 0.97] | 1.000 [1.00, 1.00] | 0.0% | 0.0% | 0.0% | 0.93 | 0.0 | 96 | 102 |
| july | 336 | 0.96 [0.94, 0.99] | 1.000 [1.00, 1.00] | 0.0% | 0.0% | 0.0% | 0.96 | 0.0 | 96 | 100 |
| january | 336 | 0.92 [0.86, 0.97] | 1.000 [1.00, 1.00] | 0.0% | 0.0% | 0.0% | 0.89 | 0.0 | 96 | 104 |

Frozen rule: pooled **PASSES**; july PASSES, january PASSES  (descriptive comparator, not scored)

## C campaign only, 168 h (descriptive)

| policy / subset | rows | resolved [CI] | acc \| resolved [CI] | wrong & confident | false alarms | missed faults | localised (wrong docs) | passive reads / row | campaign h / row | campaign h / correct verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| pooled | 672 | 0.95 [0.93, 0.97] | 1.000 [1.00, 1.00] | 0.0% | 0.0% | 0.0% | 0.97 | 0.0 | 168 | 177 |
| july | 336 | 0.99 [0.99, 1.00] | 1.000 [1.00, 1.00] | 0.0% | 0.0% | 0.0% | 1.00 | 0.0 | 168 | 169 |
| january | 336 | 0.90 [0.87, 0.95] | 1.000 [1.00, 1.00] | 0.0% | 0.0% | 0.0% | 0.95 | 0.0 | 168 | 186 |

Frozen rule: pooled **PASSES**; july PASSES, january PASSES  (descriptive comparator, not scored)

## Total cost = passive reads + r x campaign hours, per correct resolved verdict

r = one campaign hour in units of one passive read (not priced by us).

| policy | r = 0 | r = 0.1 | r = 1 | r = 10 |
|---|---|---|---|---|
| P0 passive only (futility on) | no verdicts | no verdicts | no verdicts | no verdicts |
| P1 passive, then 96 h campaign | 8.8 | 19.0 | 110.4 | 1024.8 |
| P2 passive, then 168 h campaign | 8.7 | 26.4 | 185.1 | 1772.7 |

## Frozen reading rules (Addendum 15, Part B)

| policy | pooled | july | january |
|---|---|---|---|
| P1 passive, then 96 h campaign | PASSES | PASSES | PASSES |
| P2 passive, then 168 h campaign | PASSES | PASSES | PASSES |

**Overall: wiring HELPS `vav_zone` (in simulation).**