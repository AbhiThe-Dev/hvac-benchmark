# Addendum 15, Part A: robustness of the dither campaign

Fresh campaigns (code seeds 4-6), 7 train-role topologies counted equally, both seasons; rank-1 = fraction of zones whose most-responsive box is the true serving box (chance about 0.10); `legacy` noise = the project's original telemetry noise; building-cluster bootstrap 95% CI (500). A cell WORKS if the mean rank-1 is >= 0.90 in BOTH seasons at that campaign length. Simulation only.

## Amplitude x override dropout (signals flow + t_dis, `legacy` noise)

| half-swing | dropout | season | 24 h | 48 h | 96 h | 168 h | 288 h | shortest working L | swing-hours a x L |
|---|---|---|---|---|---|---|---|---|---|
| 0.5 K | 0% | july | 0.31 [0.23, 0.39] | 0.43 [0.35, 0.52] | 0.68 [0.61, 0.76] | 0.79 [0.76, 0.82] | 0.92 [0.89, 0.96] | not by 288 h | - |
| 0.5 K | 0% | january | 0.49 [0.35, 0.61] | 0.59 [0.49, 0.67] | 0.54 [0.44, 0.61] | 0.63 [0.59, 0.67] | 0.82 [0.77, 0.86] | | |
| 0.5 K | 25% | july | 0.30 [0.24, 0.36] | 0.40 [0.31, 0.50] | 0.66 [0.59, 0.74] | 0.73 [0.69, 0.76] | 0.89 [0.86, 0.92] | not by 288 h | - |
| 0.5 K | 25% | january | 0.48 [0.35, 0.60] | 0.57 [0.46, 0.66] | 0.49 [0.41, 0.56] | 0.62 [0.58, 0.67] | 0.75 [0.72, 0.78] | | |
| 1.0 K | 0% | july | 0.58 [0.51, 0.67] | 0.77 [0.73, 0.82] | 0.94 [0.92, 0.96] | 0.99 [0.97, 1.00] | 1.00 [1.00, 1.00] | 288 | 288 |
| 1.0 K | 0% | january | 0.72 [0.58, 0.84] | 0.83 [0.77, 0.89] | 0.83 [0.74, 0.91] | 0.87 [0.85, 0.89] | 0.98 [0.97, 0.99] | | |
| 1.0 K | 25% | july | 0.59 [0.53, 0.67] | 0.75 [0.71, 0.81] | 0.92 [0.88, 0.96] | 0.97 [0.95, 0.99] | 1.00 [1.00, 1.00] | 288 | 288 |
| 1.0 K | 25% | january | 0.71 [0.55, 0.85] | 0.83 [0.75, 0.89] | 0.79 [0.70, 0.89] | 0.83 [0.81, 0.87] | 0.96 [0.93, 0.98] | | |
| 1.5 K | 0% | july | 0.69 [0.63, 0.77] | 0.87 [0.82, 0.92] | 0.98 [0.97, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 96 | 144 |
| 1.5 K | 0% | january | 0.83 [0.72, 0.93] | 0.91 [0.87, 0.95] | 0.92 [0.88, 0.96] | 0.95 [0.93, 0.97] | 1.00 [0.99, 1.00] | | |
| 1.5 K | 25% | july | 0.77 [0.73, 0.83] | 0.81 [0.76, 0.87] | 0.97 [0.95, 0.99] | 0.99 [0.99, 1.00] | 1.00 [1.00, 1.00] | 96 | 144 |
| 1.5 K | 25% | january | 0.81 [0.67, 0.92] | 0.92 [0.87, 0.97] | 0.95 [0.90, 0.98] | 0.95 [0.93, 0.97] | 1.00 [0.99, 1.00] | | |

## Signals the building logs (half-swing 1.5 K, no dropout, `legacy` noise)

| signal set | season | 24 h | 48 h | 96 h | 168 h | 288 h | shortest working L |
|---|---|---|---|---|---|---|---|
| flow+t_dis | july | 0.69 [0.63, 0.77] | 0.87 [0.82, 0.92] | 0.98 [0.97, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 96 |
| flow+t_dis | january | 0.83 [0.72, 0.93] | 0.91 [0.87, 0.95] | 0.92 [0.88, 0.96] | 0.95 [0.93, 0.97] | 1.00 [0.99, 1.00] | |
| flow | july | 0.63 [0.52, 0.75] | 0.60 [0.55, 0.67] | 0.91 [0.85, 0.97] | 0.92 [0.90, 0.93] | 0.97 [0.96, 0.99] | not by 288 h |
| flow | january | 0.13 [0.11, 0.16] | 0.13 [0.11, 0.15] | 0.46 [0.30, 0.64] | 0.55 [0.39, 0.72] | 0.61 [0.46, 0.78] | |
| t_dis | july | 0.69 [0.65, 0.74] | 0.87 [0.82, 0.91] | 0.98 [0.96, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 96 |
| t_dis | january | 0.86 [0.77, 0.94] | 0.91 [0.87, 0.95] | 0.93 [0.90, 0.96] | 0.95 [0.94, 0.97] | 1.00 [0.99, 1.00] | |
| t_dis+reheat | july | 0.69 [0.65, 0.74] | 0.87 [0.82, 0.91] | 0.98 [0.96, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 96 |
| t_dis+reheat | january | 0.86 [0.78, 0.94] | 0.91 [0.88, 0.95] | 0.93 [0.90, 0.96] | 0.95 [0.94, 0.97] | 1.00 [0.99, 1.00] | |

## `harsh` noise (robustness; flow x N(1, 0.10), temperature + N(0, 1.0)), signals flow + t_dis, shortest working L

| half-swing | dropout | shortest working L (harsh) |
|---|---|---|
| 0.5 K | 0% | not by 288 h |
| 0.5 K | 25% | not by 288 h |
| 1.0 K | 0% | 288 |
| 1.0 K | 25% | 288 |
| 1.5 K | 0% | 96 |
| 1.5 K | 25% | 96 |

## Frozen readouts (Addendum 15)

- R1 smallest half-swing that works by L <= 168 h with no dropout: 1.5 K (works at L = 96 h)
- R2 half-swing 1.5 K with 25% overrides: works by L <= 168 h: yes; by L <= 288 h: yes (L = 96 h)
- R3 signal sets that work by L <= 168 h at 1.5 K / no dropout: flow+t_dis, t_dis, t_dis+reheat