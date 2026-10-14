# Signal value and substitutes (Addendum 18)

Model-free; nothing fitted. Simulation only (`legacy` evidence, the Addendum 11 seeds). Every building counts equally. CIs are building-cluster bootstrap 95% (500 resamples); with six buildings they are wide, and verdicts use point estimates.

## Gates and checks

- **G1 code path (Part A):** 96 cached Addendum-11 values (ch0 / ch1 / ch2 / all3 per building and slot) reproduced to 1e-9: **PASS**
- **G1 code path (Part B):** V0 at offset 0 reproduces the cached `rank1_window['ch0']` (accuracy and unit count) for all 6 buildings: **PASS**
- **G2 null control** (true owners shuffled among boxes, 200 permutations, offset 0; pooled mean accuracy vs chance; tolerance 0.05):

| variant | shuffled accuracy | chance | verdict |
|---|---|---|---|
| V0 inlet_trend | 0.381 | 0.378 | PASS |
| V1 dis_reheat_off_oracle | 0.434 | 0.433 | PASS |
| V2 dis_flow_top50 | 0.385 | 0.378 | PASS |
| V3 dis_flow_top25 | 0.380 | 0.378 | PASS |
| V4 dis_all | 0.388 | 0.378 | PASS |
| S1 spot_1 | 0.376 | 0.378 | PASS |
| S3 spot_3 | 0.381 | 0.378 | PASS |
| S6 spot_6 | 0.384 | 0.378 | PASS |
| S24 day_logger | 0.382 | 0.378 | PASS |

- **C1 flow rules read no temperature:** by construction (unit test `test_hour_selection_reads_only_flow_or_reheat`).
- **C2 oracle identity** (largest |t_dis - t_in|, noise-free, over reheat-off hours) and **C4 season labels** (winter windows colder than summer windows by `ENV|oat`):

| building | handlers | boxes | reheat series | max abs(t_dis - t_in), reheat off (K) | winter colder than summer | window-mean outdoor temp, windows 0-7 |
|---|---|---|---|---|---|---|
| sys03_psz_ac | 10 | 10 | no | n/a | True | -5 2 11 18 23 22 14 6 |
| vav_2ahu_2loops | 2 | 10 | yes | 0.5129 | True | -5 2 11 18 23 22 14 6 |
| vav_3ahu_2loops | 3 | 10 | yes | 0.4998 | True | 0 1 9 15 21 22 12 4 |
| dev_F | 2 | 6 | yes | 0.3263 | True | 8 12 14 20 23 23 20 11 |
| dev_G | 3 | 6 | yes | 0.2960 | True | 10 12 14 15 16 17 16 13 |
| dev_H | 2 | 12 | yes | 0.4547 | True | 0 1 9 15 21 22 12 4 |

- **C3 selection shares** (mean share of hours selected / share of (box, slice) readings valid, by season group):

| building | rule | g0 | g1 | g2 | g3 | all |
|---|---|---|---|---|---|---|
| sys03_psz_ac | V2 dis_flow_top50 | 0.49 / 1.00 | 0.50 / 1.00 | 0.49 / 1.00 | 0.50 / 0.99 | 0.50 / 1.00 |
| sys03_psz_ac | V3 dis_flow_top25 | 0.25 / 0.53 | 0.25 / 0.61 | 0.25 / 0.60 | 0.24 / 0.55 | 0.25 / 0.57 |
| sys03_psz_ac | V4 dis_all | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |
| vav_2ahu_2loops | V1 dis_reheat_off_oracle | 0.08 / 0.16 | 0.26 / 0.54 | 0.32 / 0.68 | 0.16 / 0.29 | 0.20 / 0.42 |
| vav_2ahu_2loops | V2 dis_flow_top50 | 0.51 / 1.00 | 0.50 / 1.00 | 0.49 / 0.98 | 0.51 / 1.00 | 0.50 / 1.00 |
| vav_2ahu_2loops | V3 dis_flow_top25 | 0.27 / 0.71 | 0.26 / 0.61 | 0.23 / 0.49 | 0.27 / 0.62 | 0.26 / 0.61 |
| vav_2ahu_2loops | V4 dis_all | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |
| vav_3ahu_2loops | V1 dis_reheat_off_oracle | 0.14 / 0.32 | 0.29 / 0.62 | 0.36 / 0.80 | 0.16 / 0.30 | 0.24 / 0.51 |
| vav_3ahu_2loops | V2 dis_flow_top50 | 0.51 / 1.00 | 0.51 / 1.00 | 0.48 / 0.99 | 0.48 / 0.99 | 0.50 / 1.00 |
| vav_3ahu_2loops | V3 dis_flow_top25 | 0.27 / 0.66 | 0.25 / 0.60 | 0.23 / 0.54 | 0.23 / 0.47 | 0.24 / 0.57 |
| vav_3ahu_2loops | V4 dis_all | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |
| dev_F | V1 dis_reheat_off_oracle | 0.46 / 0.88 | 0.73 / 1.00 | 0.92 / 1.00 | 0.67 / 0.92 | 0.70 / 0.95 |
| dev_F | V2 dis_flow_top50 | 0.51 / 0.99 | 0.50 / 0.99 | 0.50 / 0.99 | 0.52 / 1.00 | 0.51 / 0.99 |
| dev_F | V3 dis_flow_top25 | 0.25 / 0.61 | 0.24 / 0.57 | 0.24 / 0.64 | 0.25 / 0.60 | 0.24 / 0.60 |
| dev_F | V4 dis_all | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |
| dev_G | V1 dis_reheat_off_oracle | 0.68 / 1.00 | 0.83 / 1.00 | 0.93 / 1.00 | 0.84 / 1.00 | 0.82 / 1.00 |
| dev_G | V2 dis_flow_top50 | 0.48 / 0.97 | 0.49 / 0.99 | 0.48 / 0.99 | 0.48 / 0.96 | 0.48 / 0.98 |
| dev_G | V3 dis_flow_top25 | 0.23 / 0.60 | 0.22 / 0.61 | 0.23 / 0.65 | 0.23 / 0.67 | 0.23 / 0.63 |
| dev_G | V4 dis_all | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |
| dev_H | V1 dis_reheat_off_oracle | 0.24 / 0.56 | 0.52 / 0.92 | 0.66 / 1.00 | 0.31 / 0.76 | 0.43 / 0.81 |
| dev_H | V2 dis_flow_top50 | 0.51 / 1.00 | 0.50 / 0.99 | 0.48 / 0.97 | 0.48 / 0.99 | 0.49 / 0.99 |
| dev_H | V3 dis_flow_top25 | 0.26 / 0.61 | 0.26 / 0.59 | 0.23 / 0.58 | 0.21 / 0.42 | 0.24 / 0.55 |
| dev_H | V4 dis_all | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |

## Part A -- which single missing signal costs the most

CEILING = best building-mean window rank-1 over the non-empty channel subsets (equal-weight standardised average, Addendum 11's statistic); VALUE = CEILING(all channels) - CEILING(channels that do not read the signal). CRITICAL = VALUE >= 0.15 or no channel remains; MINOR = VALUE < 0.05. A model-free UPPER BOUND on what the channels can do, not what the engine does. The census column is descriptive only.

### ahu_vav  (6 buildings; ceiling with every signal present 0.969)

Building-mean rank-1 by channel subset: ch0 0.969, ch1 0.618, ch2 0.400, ch0+1 0.814, ch0+2 0.952, ch1+2 0.650, all3 0.824

| missing signal | channels left | CEILING left | VALUE lost [95% CI] | label | recorded in the Mortar census |
|---|---|---|---|---|---|
| member `t_in` | ch1+2 | 0.650 | 0.319 [0.119, 0.499] | **CRITICAL** | recorded in 0 buildings (0 at >= 80%); documented in 0 |
| handler/owner `sat` | ch1+2 | 0.650 | 0.319 [0.119, 0.499] | **CRITICAL** | recorded in 30 buildings (22 at >= 80%); documented in 38 |
| member `flow` | ch0 | 0.969 | 0.000 [0.000, 0.000] | **MINOR** | recorded in 12 buildings (4 at >= 80%); documented in 16 |
| handler/owner `flow` | ch0 | 0.969 | 0.000 [0.000, 0.000] | **MINOR** | recorded in 3 buildings (1 at >= 80%); documented in 3 |

### loop_branch  (5 buildings; ceiling with every signal present 0.819)

Building-mean rank-1 by channel subset: ch0 0.694, ch1 0.711, ch2 0.806, ch0+1 0.705, ch0+2 0.767, ch1+2 0.777, all3 0.819

| missing signal | channels left | CEILING left | VALUE lost [95% CI] | label | recorded in the Mortar census |
|---|---|---|---|---|---|
| member `flow` | ch0 | 0.694 | 0.125 [0.038, 0.254] | **MODERATE** | no such node in any Mortar graph |
| handler/owner `flow` | ch0 | 0.694 | 0.125 [0.038, 0.254] | **MODERATE** | no such node in any Mortar graph |
| member `t_in` | ch1+2 | 0.806 | 0.013 [0.000, 0.068] | **MINOR** | no such node in any Mortar graph |
| handler/owner `t_sup` | ch1+2 | 0.806 | 0.013 [0.000, 0.068] | **MINOR** | no such node in any Mortar graph |

### branch_coil  (7 buildings; ceiling with every signal present 0.933)

Building-mean rank-1 by channel subset: ch0 0.925, ch1 0.835, ch2 0.770, ch0+1 0.922, ch0+2 0.915, ch1+2 0.882, all3 0.933

| missing signal | channels left | CEILING left | VALUE lost [95% CI] | label | recorded in the Mortar census |
|---|---|---|---|---|---|
| handler/owner `flow` | none | n/a | no channel left | **CRITICAL** | no such node in any Mortar graph |
| member `rate` | none | n/a | no channel left | **CRITICAL** | recorded in 0 buildings (0 at >= 80%); documented in 0 |
| handler/owner `t_in` | ch1+2 | 0.882 | 0.050 [0.026, 0.076] | **MODERATE** | no such node in any Mortar graph |
| handler/owner `t_out` | ch1+2 | 0.882 | 0.050 [0.026, 0.076] | **MODERATE** | no such node in any Mortar graph |

### coil_ahu  (6 buildings; ceiling with every signal present 0.850)

Building-mean rank-1 by channel subset: ch0 0.849, ch1 0.787, ch2 0.559, ch0+1 0.850, ch0+2 0.739, ch1+2 0.698, all3 0.817

| missing signal | channels left | CEILING left | VALUE lost [95% CI] | label | recorded in the Mortar census |
|---|---|---|---|---|---|
| handler/owner `flow` | none | n/a | no channel left | **CRITICAL** | recorded in 3 buildings (1 at >= 80%); documented in 3 |
| handler/owner `sat` | none | n/a | no channel left | **CRITICAL** | recorded in 30 buildings (22 at >= 80%); documented in 38 |
| handler/owner `mat` | none | n/a | no channel left | **CRITICAL** | recorded in 0 buildings (0 at >= 80%); documented in 30 |
| member `rate_s|rate` | none | n/a | no channel left | **CRITICAL** | recorded in 0 buildings (0 at >= 80%); documented in 0 |

## Part B -- can a recorded signal or a technician's reading replace `ahu_vav`'s box inlet temperature?

Window-aggregated rank-1 of the ch0 form (mean |box inlet reading + offset - candidate handler supply temperature|), pooled over buildings (V1: the five with a reheat series). Season groups: g0 = windows 0-1 (winter), g1 = 2-3, g2 = 4-5 (summer), g3 = 6-7; verdicts use g0 and g2. WORKS = rank-1 >= 0.80 and within 0.10 of V0 at the same offset and season.

### Verdicts

| variant | buildings | verdict | tolerated offset s* (K) | works at each offset (0 / 0.25 / 0.5 / 1 / 2) | baseline-limited seasons (same offsets) |
|---|---|---|---|---|---|
| V1 dis_reheat_off_oracle | 5 | **FRAGILE** | 0.0 | yes / no / no / no / no | - / g0,g2 / g0,g2 / g0,g2 / g0,g2 |
| V2 dis_flow_top50 | 6 | **FAILS** | none | no / no / no / no / no | - / - / g0,g2 / g0,g2 / g0,g2 |
| V3 dis_flow_top25 | 6 | **FAILS** | none | no / no / no / no / no | - / - / g0,g2 / g0,g2 / g0,g2 |
| V4 dis_all | 6 | **FAILS** | none | no / no / no / no / no | - / - / g0,g2 / g0,g2 / g0,g2 |
| S1 spot_1 | 6 | **FAILS** | none | no / no / no / no / no | - / - / g0,g2 / g0,g2 / g0,g2 |
| S3 spot_3 | 6 | **FAILS** | none | no / no / no / no / no | - / - / g0,g2 / g0,g2 / g0,g2 |
| S6 spot_6 | 6 | **FAILS** | none | no / no / no / no / no | - / - / g0,g2 / g0,g2 / g0,g2 |
| S24 day_logger | 6 | **FRAGILE** | 0.0 | yes / no / no / no / no | - / - / g0,g2 / g0,g2 / g0,g2 |

Smallest number of readings per box whose spot variant WORKS at each offset (among 1, 3, 6 and the 24-hour logger):

| offset (K) | 0.0 | 0.25 | 0.5 | 1.0 | 2.0 |
|---|---|---|---|---|---|
| smallest m | 24 | none | none | none | none |

### Rank-1 at offset 0 (pooled mean [CI]), all groups

| variant | g0 | g1 | g2 | g3 | all | chance (all) |
|---|---|---|---|---|---|---|
| V0 inlet_trend | 0.972 [0.944, 1.000] | 0.986 [0.958, 1.000] | 0.944 [0.833, 1.000] | 0.972 [0.944, 1.000] | 0.969 [0.920, 1.000] | 0.378 |
| V1 dis_reheat_off_oracle | 0.939 [0.873, 1.000] | 1.000 [1.000, 1.000] | 0.958 [0.925, 0.992] | 0.900 [0.817, 0.983] | 0.950 [0.900, 0.987] | 0.433 |
| V2 dis_flow_top50 | 0.624 [0.510, 0.778] | 0.743 [0.583, 0.896] | 0.728 [0.558, 0.896] | 0.631 [0.494, 0.778] | 0.681 [0.543, 0.824] | 0.378 |
| V3 dis_flow_top25 | 0.674 [0.550, 0.816] | 0.804 [0.732, 0.889] | 0.854 [0.775, 0.937] | 0.632 [0.521, 0.760] | 0.741 [0.657, 0.839] | 0.378 |
| V4 dis_all | 0.636 [0.467, 0.827] | 0.699 [0.516, 0.900] | 0.747 [0.560, 0.917] | 0.650 [0.494, 0.833] | 0.683 [0.524, 0.865] | 0.378 |
| S1 spot_1 | 0.680 [0.578, 0.822] | 0.662 [0.547, 0.816] | 0.684 [0.577, 0.815] | 0.657 [0.546, 0.806] | 0.671 [0.566, 0.817] | 0.378 |
| S3 spot_3 | 0.752 [0.640, 0.859] | 0.790 [0.697, 0.883] | 0.788 [0.669, 0.894] | 0.736 [0.634, 0.861] | 0.766 [0.661, 0.869] | 0.378 |
| S6 spot_6 | 0.805 [0.684, 0.908] | 0.855 [0.767, 0.933] | 0.814 [0.704, 0.923] | 0.800 [0.695, 0.904] | 0.819 [0.714, 0.918] | 0.378 |
| S24 day_logger | 0.889 [0.802, 0.959] | 0.929 [0.865, 0.979] | 0.896 [0.808, 0.962] | 0.852 [0.730, 0.958] | 0.892 [0.808, 0.961] | 0.378 |

### Rank-1 by offset, winter (windows 0-1) (pooled mean)

| variant | 0.0 K | 0.25 K | 0.5 K | 1.0 K | 2.0 K |
|---|---|---|---|---|---|
| V0 inlet_trend | 0.972 | 0.819 | 0.686 | 0.591 | 0.494 |
| V1 dis_reheat_off_oracle | 0.939 | 0.772 | 0.670 | 0.579 | 0.500 |
| V2 dis_flow_top50 | 0.624 | 0.615 | 0.603 | 0.519 | 0.471 |
| V3 dis_flow_top25 | 0.674 | 0.671 | 0.605 | 0.546 | 0.495 |
| V4 dis_all | 0.636 | 0.625 | 0.572 | 0.528 | 0.470 |
| S1 spot_1 | 0.680 | 0.639 | 0.580 | 0.505 | 0.457 |
| S3 spot_3 | 0.752 | 0.723 | 0.637 | 0.564 | 0.469 |
| S6 spot_6 | 0.805 | 0.742 | 0.667 | 0.589 | 0.486 |
| S24 day_logger | 0.889 | 0.789 | 0.682 | 0.585 | 0.484 |

### Rank-1 by offset, summer (windows 4-5) (pooled mean)

| variant | 0.0 K | 0.25 K | 0.5 K | 1.0 K | 2.0 K |
|---|---|---|---|---|---|
| V0 inlet_trend | 0.944 | 0.818 | 0.703 | 0.618 | 0.508 |
| V1 dis_reheat_off_oracle | 0.958 | 0.786 | 0.678 | 0.578 | 0.530 |
| V2 dis_flow_top50 | 0.728 | 0.689 | 0.659 | 0.549 | 0.491 |
| V3 dis_flow_top25 | 0.854 | 0.753 | 0.665 | 0.583 | 0.483 |
| V4 dis_all | 0.747 | 0.680 | 0.627 | 0.564 | 0.492 |
| S1 spot_1 | 0.684 | 0.652 | 0.585 | 0.504 | 0.457 |
| S3 spot_3 | 0.788 | 0.728 | 0.648 | 0.563 | 0.456 |
| S6 spot_6 | 0.814 | 0.752 | 0.672 | 0.579 | 0.489 |
| S24 day_logger | 0.896 | 0.801 | 0.697 | 0.606 | 0.502 |

### Per building (all windows), offset 0 and 0.5 K

| building | variant | 0 K | 0.5 K | units scored at 0 K | units skipped at 0 K |
|---|---|---|---|---|---|
| sys03_psz_ac | V0 | 1.000 | 0.941 | 80 | 0 |
| sys03_psz_ac | V2 | 1.000 | 0.935 | 80 | 0 |
| sys03_psz_ac | V3 | 0.987 | 0.890 | 79 | 1 |
| sys03_psz_ac | V4 | 1.000 | 0.932 | 80 | 0 |
| sys03_psz_ac | S1 | 0.504 | 0.392 | 80 | 0 |
| sys03_psz_ac | S3 | 0.771 | 0.653 | 80 | 0 |
| sys03_psz_ac | S6 | 0.862 | 0.728 | 80 | 0 |
| sys03_psz_ac | S24 | 0.926 | 0.823 | 80 | 0 |
| vav_2ahu_2loops | V0 | 1.000 | 0.829 | 80 | 0 |
| vav_2ahu_2loops | V1 | 1.000 | 0.837 | 61 | 19 |
| vav_2ahu_2loops | V2 | 0.512 | 0.519 | 80 | 0 |
| vav_2ahu_2loops | V3 | 0.650 | 0.593 | 80 | 0 |
| vav_2ahu_2loops | V4 | 0.500 | 0.500 | 80 | 0 |
| vav_2ahu_2loops | S1 | 0.971 | 0.843 | 80 | 0 |
| vav_2ahu_2loops | S3 | 0.999 | 0.862 | 80 | 0 |
| vav_2ahu_2loops | S6 | 1.000 | 0.847 | 80 | 0 |
| vav_2ahu_2loops | S24 | 1.000 | 0.869 | 80 | 0 |
| vav_3ahu_2loops | V0 | 1.000 | 0.660 | 80 | 0 |
| vav_3ahu_2loops | V1 | 1.000 | 0.700 | 64 | 16 |
| vav_3ahu_2loops | V2 | 0.450 | 0.446 | 80 | 0 |
| vav_3ahu_2loops | V3 | 0.658 | 0.503 | 79 | 1 |
| vav_3ahu_2loops | V4 | 0.400 | 0.401 | 80 | 0 |
| vav_3ahu_2loops | S1 | 0.719 | 0.625 | 80 | 0 |
| vav_3ahu_2loops | S3 | 0.863 | 0.598 | 80 | 0 |
| vav_3ahu_2loops | S6 | 0.954 | 0.604 | 80 | 0 |
| vav_3ahu_2loops | S24 | 1.000 | 0.664 | 80 | 0 |
| dev_F | V0 | 0.958 | 0.497 | 48 | 0 |
| dev_F | V1 | 0.938 | 0.626 | 48 | 0 |
| dev_F | V2 | 0.729 | 0.609 | 48 | 0 |
| dev_F | V3 | 0.729 | 0.624 | 48 | 0 |
| dev_F | V4 | 0.708 | 0.615 | 48 | 0 |
| dev_F | S1 | 0.580 | 0.518 | 48 | 0 |
| dev_F | S3 | 0.616 | 0.535 | 48 | 0 |
| dev_F | S6 | 0.678 | 0.559 | 48 | 0 |
| dev_F | S24 | 0.761 | 0.529 | 48 | 0 |
| dev_G | V0 | 0.854 | 0.697 | 48 | 0 |
| dev_G | V1 | 0.875 | 0.646 | 48 | 0 |
| dev_G | V2 | 0.729 | 0.698 | 48 | 0 |
| dev_G | V3 | 0.792 | 0.683 | 48 | 0 |
| dev_G | V4 | 0.896 | 0.608 | 48 | 0 |
| dev_G | S1 | 0.669 | 0.611 | 48 | 0 |
| dev_G | S3 | 0.689 | 0.634 | 48 | 0 |
| dev_G | S6 | 0.714 | 0.674 | 48 | 0 |
| dev_G | S24 | 0.767 | 0.599 | 48 | 0 |
| dev_H | V0 | 1.000 | 0.565 | 96 | 0 |
| dev_H | V1 | 0.936 | 0.558 | 94 | 2 |
| dev_H | V2 | 0.667 | 0.577 | 96 | 0 |
| dev_H | V3 | 0.632 | 0.475 | 95 | 1 |
| dev_H | V4 | 0.594 | 0.553 | 96 | 0 |
| dev_H | S1 | 0.581 | 0.543 | 96 | 0 |
| dev_H | S3 | 0.660 | 0.600 | 96 | 0 |
| dev_H | S6 | 0.703 | 0.616 | 96 | 0 |
| dev_H | S24 | 0.896 | 0.621 | 96 | 0 |

Chance is the mean of 1/|candidates| over the scored units; ties count 1/#tied. `sys03_psz_ac` is ten one-box packaged units (no reheat series, so no V1). The simulator's ducts are adiabatic and instantaneous (the true pair's noise-free ch0 error is zero), so V0 is optimistic and V1 is close to it by construction.