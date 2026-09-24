# Does deliberate setpoint perturbation identify the serving box where passive data cannot? (Addendum 13)

7 train-role topologies (each counts equally), code seeds 1-3, 20 noise draws each; rank-1 = fraction of zones whose most-responsive box is the true serving box; chance = 1/n_vav (about 0.10). `legacy` noise = the project's original telemetry noise; `harsh` = flow x N(1,0.10), temperature + N(0,1.0). Passive = the existing `vav_zone` channels on the UNDITHERED run of the same building and window. Building-cluster bootstrap 95% CI (500). Simulation only.

## july

| campaign length | active, none noise | active, legacy noise | active, harsh noise | passive all3 | passive ch1 |
|---|---|---|---|---|---|
| 24 h | 0.61 [0.59, 0.62] | 0.60 [0.59, 0.61] | 0.58 [0.57, 0.60] | 0.10 [0.04, 0.15] | 0.08 [0.03, 0.13] |
| 48 h | 0.84 [0.80, 0.88] | 0.83 [0.81, 0.87] | 0.83 [0.80, 0.87] | 0.09 [0.04, 0.14] | 0.05 [0.01, 0.10] |
| 96 h | 0.97 [0.95, 0.99] | 0.97 [0.95, 0.99] | 0.98 [0.96, 0.99] | 0.09 [0.03, 0.15] | 0.04 [0.00, 0.09] |
| 168 h | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.12 [0.05, 0.20] | 0.05 [0.00, 0.12] |
| 288 h | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.11 [0.04, 0.20] | 0.09 [0.02, 0.14] |

Per building, active `legacy` noise: sys07_vav_reheat 0.59/0.93/1.00, vav_2ahu_2loops 0.59/0.93/1.00, vav_3ahu_2loops 0.63/0.97/1.00, dev_E 0.59/1.00/1.00, dev_F 0.61/1.00/1.00, dev_G 0.61/1.00/1.00, dev_H 0.58/0.97/1.00  (L = 24/96/288 h)

## january

| campaign length | active, none noise | active, legacy noise | active, harsh noise | passive all3 | passive ch1 |
|---|---|---|---|---|---|
| 24 h | 0.79 [0.69, 0.89] | 0.78 [0.66, 0.89] | 0.77 [0.64, 0.89] | 0.16 [0.06, 0.28] | 0.09 [0.02, 0.18] |
| 48 h | 0.96 [0.94, 0.99] | 0.96 [0.93, 0.99] | 0.95 [0.91, 0.98] | 0.06 [0.03, 0.12] | 0.05 [0.01, 0.10] |
| 96 h | 0.89 [0.86, 0.92] | 0.89 [0.85, 0.93] | 0.89 [0.85, 0.93] | 0.12 [0.06, 0.17] | 0.12 [0.05, 0.19] |
| 168 h | 0.95 [0.92, 0.98] | 0.95 [0.92, 0.98] | 0.95 [0.92, 0.98] | 0.17 [0.09, 0.24] | 0.11 [0.02, 0.23] |
| 288 h | 0.98 [0.96, 1.00] | 0.98 [0.96, 0.99] | 0.98 [0.96, 0.99] | 0.14 [0.06, 0.23] | 0.13 [0.05, 0.22] |

Per building, active `legacy` noise: sys07_vav_reheat 0.87/0.90/1.00, vav_2ahu_2loops 0.88/0.90/1.00, vav_3ahu_2loops 0.52/0.86/0.97, dev_E 1.00/0.96/0.98, dev_F 0.72/0.88/0.94, dev_G 0.82/0.94/1.00, dev_H 0.64/0.79/0.97  (L = 24/96/288 h)

## Frozen reading rules (Addendum 13)

- july: legacy-noise rank-1 at 96 h = 0.973 (needs >= 0.90); passive all3 at 96 h = 0.090 (needs <= 0.30); shortest L reaching 0.90 = 96
- january: legacy-noise rank-1 at 96 h = 0.891 (needs >= 0.90); passive all3 at 96 h = 0.119 (needs <= 0.30); shortest L reaching 0.90 = 48

**VERDICT: WORKS BUT NEEDS THE LONG CAMPAIGN** (0.90 reached in both seasons, but not both at 96 h).