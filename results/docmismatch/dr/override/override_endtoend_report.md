# Addendum 16, Part B: technician-style override tests wired into the engine (`vav_zone`)

112 `vav_zone` episodes (7 train-role buildings, 56 wrong / 56 right documentation), each under every (season, test-order seed) run = 6 rows per episode; stage 1 = frozen passive engine (Addendum 15); stage 2 = up to 4 sequential single-box override tests (D = 60 min, `legacy` 0.25 K noise), the next box chosen by `physical_eig`, belief updated with the engine's Bernoulli rule. MEASURED rates = Laplace-smoothed TPR / FPR on the 6 training buildings' tests at the theta chosen there (FPR <= 0.05); ASSUMED = `ACTUATE_OBSERVE`'s 0.95 / 0.05. Resolved = verdict rows / all rows; accuracy among resolved is class-balanced; false alarm = REFUTED on a right document; missed fault = CONFIRMED on a wrong document. CI = building-cluster bootstrap (500). Simulation only.

Passive stage: 112 episodes, resolved passively 0, mean passive reads 8.3.

Training-measured rates used (mean over the 7 held-out fits): full_cool july: theta 0.64 K, TPR 0.986, FPR 0.031; full_cool january: theta 0.64 K, TPR 0.986, FPR 0.035; close july: theta 1.29 K, TPR 0.884, FPR 0.026; close january: theta 1.00 K, TPR 0.511, FPR 0.042

## P0 passive only (futility on)

| subset | rows | resolved [CI] | acc \| resolved [CI] | wrong & confident | false alarms | missed faults | tests / row | forced minutes / row | minutes / correct verdict |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 112 | 0.00 [0.00, 0.00] | nan n/a | 0.0% | 0.0% | 0.0% | 0.00 | 0 | - |
| july | 112 | 0.00 [0.00, 0.00] | nan n/a | 0.0% | 0.0% | 0.0% | 0.00 | 0 | - |
| january | 112 | 0.00 [0.00, 0.00] | nan n/a | 0.0% | 0.0% | 0.0% | 0.00 | 0 | - |

Frozen rule: pooled **FAILS**; july FAILS, january FAILS  (descriptive, not scored)

## T_cool: passive, then override tests, `full_cool`, MEASURED rates

| subset | rows | resolved [CI] | acc \| resolved [CI] | wrong & confident | false alarms | missed faults | tests / row | forced minutes / row | minutes / correct verdict |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 672 | 1.00 [0.99, 1.00] | 0.946 [0.87, 0.99] | 5.4% | 8.3% | 2.4% | 1.23 | 74 | 78 |
| july | 336 | 0.99 [0.98, 1.00] | 0.946 [0.88, 0.99] | 5.4% | 8.9% | 1.8% | 1.19 | 72 | 76 |
| january | 336 | 1.00 [0.99, 1.00] | 0.946 [0.87, 0.99] | 5.4% | 7.7% | 3.0% | 1.26 | 76 | 80 |

Frozen rule: pooled **PASSES**; july PASSES, january PASSES

## T_cool_assumed: same, engine's ASSUMED rates 0.95 / 0.05

| subset | rows | resolved [CI] | acc \| resolved [CI] | wrong & confident | false alarms | missed faults | tests / row | forced minutes / row | minutes / correct verdict |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 672 | 0.99 [0.98, 1.00] | 0.947 [0.86, 1.00] | 5.2% | 9.8% | 0.6% | 1.54 | 93 | 98 |
| july | 336 | 0.99 [0.98, 1.00] | 0.958 [0.90, 1.00] | 4.2% | 8.3% | 0.0% | 1.56 | 94 | 98 |
| january | 336 | 0.99 [0.99, 1.00] | 0.937 [0.83, 0.99] | 6.2% | 11.3% | 1.2% | 1.52 | 91 | 98 |

Frozen rule: pooled **PASSES**; july PASSES, january FAILS  (descriptive, not scored)

## T_close: passive, then override tests, `close`, MEASURED rates

| subset | rows | resolved [CI] | acc \| resolved [CI] | wrong & confident | false alarms | missed faults | tests / row | forced minutes / row | minutes / correct verdict |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 672 | 0.67 [0.55, 0.76] | 0.940 [0.86, 0.98] | 4.5% | 7.7% | 1.2% | 2.58 | 155 | 247 |
| july | 336 | 0.95 [0.87, 0.99] | 0.903 [0.82, 0.96] | 8.9% | 15.5% | 2.4% | 1.81 | 109 | 127 |
| january | 336 | 0.40 [0.20, 0.54] | 1.000 [1.00, 1.00] | 0.0% | 0.0% | 0.0% | 3.35 | 201 | 505 |

Frozen rule: pooled **HONEST BUT PARTIAL**; july FAILS, january HONEST BUT PARTIAL

## T_close_assumed: same, engine's ASSUMED rates 0.95 / 0.05

| subset | rows | resolved [CI] | acc \| resolved [CI] | wrong & confident | false alarms | missed faults | tests / row | forced minutes / row | minutes / correct verdict |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 672 | 0.98 [0.97, 0.99] | 0.824 [0.69, 0.93] | 16.8% | 33.6% | 0.0% | 1.51 | 91 | 112 |
| july | 336 | 0.98 [0.96, 0.99] | 0.851 [0.72, 0.94] | 14.3% | 28.6% | 0.0% | 1.54 | 92 | 110 |
| january | 336 | 0.98 [0.96, 0.99] | 0.797 [0.62, 0.93] | 19.3% | 38.7% | 0.0% | 1.48 | 89 | 114 |

Frozen rule: pooled **RESOLVES BUT IS DISHONEST**; july RESOLVES BUT IS DISHONEST, january RESOLVES BUT IS DISHONEST  (descriptive, not scored)

## Frozen reading rules (Addendum 16, Part B)

| policy | pooled | july | january |
|---|---|---|---|
| T_cool: passive, then override tests, `full_cool`, MEASURED rates | PASSES | PASSES | PASSES |
| T_close: passive, then override tests, `close`, MEASURED rates | HONEST BUT PARTIAL | FAILS | HONEST BUT PARTIAL |

**Overall: the technician-style override WORKS (in simulation).**