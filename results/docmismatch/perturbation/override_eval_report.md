# Addendum 16, Part A: measured operating characteristics of a technician-style override test

126 EnergyPlus runs (7 train-role VAV buildings x July / January x test-order seeds 1-3 x 3 commands), each holding one 2-hour override test of every box (one per day); 126 runs passed the code-path checks (10-minute series length; for every `close` run the box flow is zero in exactly the two shifted hours and non-zero just before and after; run truth == pool `vav_zone` truth). Score = extra cooling (`full_cool`, `flow_only`) or extra warming (`close`) of a zone relative to its peers over the first D minutes versus the previous hour; zone-temperature noise `legacy` = 0.25 K, `harsh` = 0.5 K, 20 draws; 7 buildings counted equally; building-cluster bootstrap 95% CI (500). Simulation only.

## Top-1 identification: the highest-scoring zone is the zone the tested box serves (chance about 0.10-0.17)

| command | season | D = 30 min | D = 60 min | D = 120 min | AUROC at D = 60 |
|---|---|---|---|---|---|
| full_cool | july | 0.98 [0.97, 1.00] | 0.99 [0.98, 1.00] | 0.99 [0.98, 1.00] | 1.00 [0.99, 1.00] |
| full_cool | january | 1.00 [0.99, 1.00] | 1.00 [0.99, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] |
| close | july | 0.93 [0.87, 0.98] | 0.95 [0.90, 0.99] | 0.95 [0.91, 0.99] | 0.97 [0.94, 0.99] |
| close | january | 0.59 [0.35, 0.84] | 0.61 [0.37, 0.86] | 0.63 [0.40, 0.86] | 0.65 [0.43, 0.88] |
| flow_only | july | 0.80 [0.66, 0.93] | 0.80 [0.67, 0.93] | 0.81 [0.69, 0.94] | 0.92 [0.86, 0.97] |
| flow_only | january | 0.50 [0.28, 0.74] | 0.51 [0.28, 0.76] | 0.51 [0.27, 0.76] | 0.68 [0.49, 0.87] |

(`legacy` noise.) Noise robustness at D = 60 min:

| command | season | no noise | legacy (0.25 K) | harsh (0.5 K) |
|---|---|---|---|---|
| full_cool | july | 1.00 [1.00, 1.00] | 0.99 [0.98, 1.00] | 0.99 [0.97, 1.00] |
| full_cool | january | 1.00 [1.00, 1.00] | 1.00 [0.99, 1.00] | 0.99 [0.98, 1.00] |
| close | july | 0.95 [0.90, 0.99] | 0.95 [0.90, 0.99] | 0.94 [0.89, 0.98] |
| close | january | 0.62 [0.37, 0.87] | 0.61 [0.37, 0.86] | 0.60 [0.36, 0.84] |
| flow_only | july | 0.83 [0.73, 0.94] | 0.80 [0.67, 0.93] | 0.78 [0.64, 0.92] |
| flow_only | january | 0.55 [0.32, 0.79] | 0.51 [0.28, 0.76] | 0.50 [0.28, 0.73] |

Peers-only (primary) versus history-corrected (secondary) top-1 at D = 60 min:

| command | season | peers-only, legacy | history-corrected, legacy |
|---|---|---|---|
| full_cool | july | 0.99 [0.98, 1.00] | 1.00 [0.99, 1.00] |
| full_cool | january | 1.00 [0.99, 1.00] | 1.00 [0.99, 1.00] |
| close | july | 0.95 [0.90, 0.99] | 0.94 [0.89, 0.99] |
| close | january | 0.61 [0.37, 0.86] | 0.61 [0.37, 0.86] |
| flow_only | july | 0.80 [0.67, 0.93] | 0.80 [0.67, 0.93] |
| flow_only | january | 0.51 [0.28, 0.76] | 0.50 [0.28, 0.73] |

## Measured rates of the rule "the zone responds if its score >= theta" (D = 60 min, `legacy` noise)

Leave-one-building-out: theta = the smallest grid value with FPR <= 0.05 on the other 6 buildings; TPR / FPR measured on the held-out building (mean over buildings [95% CI]). The engine's ASSUMED rates are TPR 0.95, FPR 0.05.

| command | season | mean theta (K) | measured TPR | measured FPR | vs assumed 0.95 / 0.05 |
|---|---|---|---|---|---|
| full_cool | july | 0.64 | 0.99 [0.98, 1.00] | 0.03 [0.01, 0.05] | TPR at/above assumed; FPR at/below assumed |
| full_cool | january | 0.64 | 0.98 [0.96, 1.00] | 0.03 [0.01, 0.06] | TPR at/above assumed; FPR at/below assumed |
| close | july | 1.29 | 0.90 [0.85, 0.97] | 0.03 [0.01, 0.05] | TPR below assumed; FPR at/below assumed |
| close | january | 1.00 | 0.57 [0.33, 0.79] | 0.03 [0.01, 0.05] | TPR below assumed; FPR at/below assumed |
| flow_only | july | 0.68 | 0.75 [0.59, 0.91] | 0.03 [0.01, 0.05] | TPR below assumed; FPR at/below assumed |
| flow_only | january | 0.75 | 0.44 [0.24, 0.67] | 0.02 [0.01, 0.04] | TPR below assumed; FPR at/below assumed |

ROC points, all 7 buildings pooled (D = 60 min, `legacy`): TPR / FPR at each threshold

| command | season | theta = 0.25 K | theta = 0.5 K | theta = 0.75 K | theta = 1 K | theta = 1.5 K | theta = 2 K |
|---|---|---|---|---|---|---|---|
| full_cool | july | 0.99 / 0.13 | 0.99 / 0.05 | 0.98 / 0.02 | 0.98 / 0.01 | 0.90 / 0.00 | 0.81 / 0.00 |
| full_cool | january | 1.00 / 0.13 | 0.99 / 0.05 | 0.98 / 0.03 | 0.96 / 0.01 | 0.89 / 0.00 | 0.83 / 0.00 |
| close | july | 0.95 / 0.18 | 0.94 / 0.11 | 0.93 / 0.08 | 0.91 / 0.05 | 0.87 / 0.01 | 0.80 / 0.00 |
| close | january | 0.58 / 0.21 | 0.55 / 0.12 | 0.53 / 0.07 | 0.51 / 0.04 | 0.43 / 0.01 | 0.35 / 0.00 |
| flow_only | july | 0.79 / 0.13 | 0.74 / 0.05 | 0.70 / 0.02 | 0.68 / 0.01 | 0.58 / 0.00 | 0.42 / 0.00 |
| flow_only | january | 0.48 / 0.17 | 0.40 / 0.07 | 0.37 / 0.03 | 0.35 / 0.02 | 0.24 / 0.00 | 0.14 / 0.00 |

## Frozen readouts (Addendum 16, Part A)

- **full_cool**: A1 shortest D with top-1 >= 0.90 in both seasons (legacy) = 30 min; A4 same under harsh noise = 30 min; A2 assumed rates HELD
- **close**: A1 shortest D with top-1 >= 0.90 in both seasons (legacy) = not by 120 min; A4 same under harsh noise = not by 120 min; A2 assumed rates OPTIMISTIC
- **flow_only**: A1 shortest D with top-1 >= 0.90 in both seasons (legacy) = not by 120 min; A4 same under harsh noise = not by 120 min; A2 assumed rates OPTIMISTIC