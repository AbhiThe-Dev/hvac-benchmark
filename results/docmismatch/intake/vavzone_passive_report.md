# Passive `vav_zone` identifiability on real Mortar buildings (Addendum 17)

Model-free rank-1 identification of which box serves which zone, from the passive channels of Addendum 11 (`evidence.pair_errors`, raw values, three channels), on the pre-registered analysis set of two 42-day windows per building. Truth = the documented Brick assignment (not field-verified). p = permutation test (10,000 random one-to-one re-assignments, seed 0). Simulation reference (Addendum 11): window rank-1 0.109-0.143 vs chance 0.123.

## Verdict: **BUILDING-DEPENDENT OR WEAK**

| gate | passed |
|---|---|
| G1 code path | yes |
| G2 analysis set >= 8 pairs | yes |
| G3 sensitivity (alpha 1.0 recovered) | yes |

G1 = score-matrix code reproduces `rank1_accuracy` (1e-12); G2 = >= 8 pairs in each primary building; G3 = injected coupling (alpha = 1.0) recovered with accuracy >= 0.80 in both primary buildings.

## Primary statistic (full record, all three channels)

| building | analysis set | audit / series exclusions | rank-1 | chance | permutation p | permutation null (mean / 95th pct) | top-3 | min detectable coupling |
|---|---|---|---|---|---|---|---|---|
| bldg8 | 24 pairs | 0 / 0 | 0.167 | 0.042 | 0.0134 | 0.041 / 0.125 | 0.250 | 0.5 |
| bldg30 | 95 pairs | 1 / 3 | 0.042 | 0.011 | 0.0123 | 0.011 / 0.032 | 0.126 | 0.5 |

## Sensitivity control (coupling injected into the real data; rank-1 / p)

| building | alpha 0.0 | alpha 0.1 | alpha 0.25 | alpha 0.5 | alpha 1.0 |
|---|---|---|---|---|---|
| bldg8 | 0.167 / 0.0134 | 0.125 / 0.0651 | 0.375 / 0.0001 | 0.500 / 0.0001 | 0.875 / 0.0001 |
| bldg30 | 0.042 / 0.0123 | 0.137 / 0.0001 | 0.484 / 0.0001 | 0.779 / 0.0001 | 0.884 / 0.0001 |

## bldg8 (primary): 24 pairs

| channels | rank-1 | permutation p (2,000) | top-3 |
|---|---|---|---|
| ch0 | 0.042 | 0.6572 | 0.208 |
| ch1 | 0.250 | 0.0005 | 0.375 |
| ch2 | 0.042 | 0.6622 | 0.167 |
| ch0+ch1 | 0.208 | 0.0010 | 0.292 |
| ch0+ch2 | 0.000 | 1.0000 | 0.083 |
| ch1+ch2 | 0.208 | 0.0025 | 0.458 |
| all3 | 0.167 | 0.0180 | 0.250 |

Per-channel AUROC (true pairs have lower error; 0.5 = chance; simulation truth 0.600 / 0.523 / 0.437) and d': ch0: 0.475 (d' -0.09; 2016 true / 46368 alternative readings); ch1: 0.542 (d' 0.20; 2016 true / 46368 alternative readings); ch2: 0.492 (d' 0.03; 2016 true / 46368 alternative readings)

Visit-scale (engine slice positions, window-aggregated, 16 slices in 2 window(s), 48 units): rank-1 0.062 vs chance 0.042.

Per window (all days of the window): window 0: rank-1 0.000 over 42 days (chance 0.042); window 1: rank-1 0.208 over 42 days (chance 0.042)

Accuracy against record length (first L days of each window, pooled): L=3: 0.125 (p 0.064, 6 days); L=7: 0.125 (p 0.071, 14 days); L=14: 0.167 (p 0.012, 28 days); L=28: 0.167 (p 0.018, 56 days); L=42: 0.167 (p 0.018, 84 days)


## bldg30 (primary): 95 pairs

Excluded: 1 by the label audit; 3 by series usability, e.g. VAV_1-1-4 (Zone_1-1-4|temp low coverage); VAV_1-5-16 (Zone_1-5-16|temp low coverage); VAV_2-1-12 (VAV_2-1-12|flow low coverage)

| channels | rank-1 | permutation p (2,000) | top-3 |
|---|---|---|---|
| ch0 | 0.000 | 1.0000 | 0.000 |
| ch1 | 0.116 | 0.0005 | 0.295 |
| ch2 | 0.000 | 1.0000 | 0.063 |
| ch0+ch1 | 0.042 | 0.0130 | 0.147 |
| ch0+ch2 | 0.011 | 0.6632 | 0.053 |
| ch1+ch2 | 0.063 | 0.0005 | 0.189 |
| all3 | 0.042 | 0.0110 | 0.126 |

Per-channel AUROC (true pairs have lower error; 0.5 = chance; simulation truth 0.600 / 0.523 / 0.437) and d': ch0: 0.462 (d' -0.13; 6956 true / 650950 alternative readings); ch1: 0.553 (d' 0.23; 6864 true / 646376 alternative readings); ch2: 0.530 (d' 0.10; 6560 true / 614561 alternative readings)

Visit-scale (engine slice positions, window-aggregated, 18 slices in 2 window(s), 179 units): rank-1 0.045 vs chance 0.011.

Per window (all days of the window): window 0: rank-1 0.042 over 42 days (chance 0.011); window 1: rank-1 0.012 over 42 days (chance 0.011)

Accuracy against record length (first L days of each window, pooled): L=3: 0.042 (p 0.016, 6 days); L=7: 0.032 (p 0.067, 14 days); L=14: 0.032 (p 0.064, 28 days); L=28: 0.042 (p 0.011, 56 days); L=42: 0.042 (p 0.011, 84 days)


## bldg1 (secondary, channel 0 only, descriptive): 8 pairs

| channels | rank-1 | permutation p (2,000) | top-3 |
|---|---|---|---|
| ch0 | 0.125 | 0.6522 | 0.125 |

Per-channel AUROC (true pairs have lower error; 0.5 = chance; simulation truth 0.600 / 0.523 / 0.437) and d': ch0: 0.449 (d' -0.14; 648 true / 4536 alternative readings)

Visit-scale (engine slice positions, window-aggregated, 18 slices in 4 window(s), 32 units): rank-1 0.188 vs chance 0.125.

Per window (all days of the window): window 0: rank-1 0.250 over 1 days (chance 0.125); window 1: rank-1 0.000 over 17 days (chance 0.125); window 2: rank-1 0.250 over 22 days (chance 0.125); window 3: rank-1 0.125 over 42 days (chance 0.125)

Accuracy against record length (first L days of each window, pooled): L=3: 0.125 (p 0.657, 10 days); L=7: 0.000 (p 1.000, 22 days); L=14: 0.125 (p 0.659, 43 days); L=28: 0.125 (p 0.638, 68 days); L=42: 0.125 (p 0.652, 82 days)


## bldg27 (secondary, channel 0 only, descriptive): 17 pairs

| channels | rank-1 | permutation p (2,000) | top-3 |
|---|---|---|---|
| ch0 | 0.235 | 0.0135 | 0.353 |

Per-channel AUROC (true pairs have lower error; 0.5 = chance; simulation truth 0.600 / 0.523 / 0.437) and d': ch0: 0.513 (d' 0.11; 1377 true / 22032 alternative readings)

Visit-scale (engine slice positions, window-aggregated, 18 slices in 3 window(s), 51 units): rank-1 0.078 vs chance 0.059.

Per window (all days of the window): window 0: rank-1 0.176 over 19 days (chance 0.059); window 1: rank-1 0.235 over 22 days (chance 0.059); window 2: rank-1 0.235 over 42 days (chance 0.059)

Accuracy against record length (first L days of each window, pooled): L=3: 0.176 (p 0.074, 9 days); L=7: 0.176 (p 0.075, 21 days); L=14: 0.235 (p 0.012, 42 days); L=28: 0.235 (p 0.015, 69 days); L=42: 0.235 (p 0.013, 83 days)
