# Per-building system identification: three-way comparison

Baseline arm, policy `active`, building-cluster bootstrap (300 resamples). `base`=unadapted, `hand`=Addendum 2 (trim=0.10, tau=30, hand-picked), `meta`=Addendum 3 (trim=0.10, tau=0.5, chosen by leave-one-building-out CV across 40 simulated buildings). `none`=plain rule, `new`=calibrated reliability layer (fit per variant on that variant's own inner records).

## layer = `none`

| suite | variant | n eps | answered | acc | cov | diff acc vs base | diff acc meta vs hand |
|---|---|---|---|---|---|---|---|
| T1_in_range | base | 577 | 280 | 0.765 [0.680, 0.848] | 0.486 [0.428, 0.536] |  |  |
| T1_in_range | hand | 577 | 280 | 0.829 [0.750, 0.898] | 0.486 [0.433, 0.538] | 0.063 [0.038, 0.097] |  |
| T1_in_range | meta | 577 | 279 | 0.824 [0.751, 0.891] | 0.484 [0.427, 0.537] | 0.059 [0.034, 0.091] | -0.004 [-0.021, 0.010] |
| T2_regime | base | 543 | 283 | 0.757 [0.687, 0.820] | 0.521 [0.476, 0.563] |  |  |
| T2_regime | hand | 543 | 281 | 0.801 [0.720, 0.864] | 0.518 [0.454, 0.572] | 0.044 [0.014, 0.075] |  |
| T2_regime | meta | 543 | 283 | 0.810 [0.734, 0.871] | 0.521 [0.455, 0.578] | 0.053 [0.021, 0.085] | 0.009 [0.002, 0.020] |
| T3_control | base | 581 | 280 | 0.721 [0.658, 0.773] | 0.482 [0.422, 0.548] |  |  |
| T3_control | hand | 581 | 276 | 0.802 [0.757, 0.848] | 0.475 [0.427, 0.527] | 0.080 [0.049, 0.111] |  |
| T3_control | meta | 581 | 277 | 0.798 [0.757, 0.840] | 0.477 [0.430, 0.531] | 0.077 [0.042, 0.109] | -0.003 [-0.013, 0.005] |
| T4_topology | base | 658 | 345 | 0.820 [0.776, 0.860] | 0.524 [0.501, 0.549] |  |  |
| T4_topology | hand | 658 | 340 | 0.877 [0.832, 0.919] | 0.517 [0.476, 0.566] | 0.057 [0.035, 0.080] |  |
| T4_topology | meta | 658 | 340 | 0.875 [0.830, 0.918] | 0.517 [0.475, 0.567] | 0.055 [0.031, 0.078] | -0.003 [-0.007, 0.000] |
| T5_climate | base | 541 | 276 | 0.744 [0.674, 0.808] | 0.510 [0.468, 0.545] |  |  |
| T5_climate | hand | 541 | 264 | 0.789 [0.737, 0.842] | 0.489 [0.440, 0.534] | 0.045 [0.003, 0.099] |  |
| T5_climate | meta | 541 | 264 | 0.792 [0.744, 0.842] | 0.489 [0.436, 0.537] | 0.049 [0.008, 0.101] | 0.003 [-0.006, 0.014] |
| T6_compound | base | 648 | 320 | 0.828 [0.777, 0.879] | 0.494 [0.462, 0.531] |  |  |
| T6_compound | hand | 648 | 310 | 0.898 [0.868, 0.927] | 0.478 [0.435, 0.516] | 0.070 [0.032, 0.111] |  |
| T6_compound | meta | 648 | 310 | 0.895 [0.862, 0.925] | 0.478 [0.429, 0.520] | 0.067 [0.030, 0.109] | -0.004 [-0.009, 0.000] |

## layer = `new`

| suite | variant | n eps | answered | acc | cov | diff acc vs base | diff acc meta vs hand |
|---|---|---|---|---|---|---|---|
| T1_in_range | base | 577 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] |  |  |
| T1_in_range | hand | 577 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | nan [nan, nan] |  |
| T1_in_range | meta | 577 | 28 | 1.000 [1.000, 1.000] | 0.048 [0.033, 0.070] | nan [nan, nan] | nan [nan, nan] |
| T2_regime | base | 543 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] |  |  |
| T2_regime | hand | 543 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | nan [nan, nan] |  |
| T2_regime | meta | 543 | 23 | 0.974 [0.925, 1.000] | 0.042 [0.031, 0.051] | nan [nan, nan] | nan [nan, nan] |
| T3_control | base | 581 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] |  |  |
| T3_control | hand | 581 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | nan [nan, nan] |  |
| T3_control | meta | 581 | 29 | 0.950 [0.919, 1.000] | 0.050 [0.028, 0.077] | nan [nan, nan] | nan [nan, nan] |
| T4_topology | base | 658 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] |  |  |
| T4_topology | hand | 658 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | nan [nan, nan] |  |
| T4_topology | meta | 658 | 62 | 0.935 [0.863, 0.990] | 0.094 [0.073, 0.115] | nan [nan, nan] | nan [nan, nan] |
| T5_climate | base | 541 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] |  |  |
| T5_climate | hand | 541 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | nan [nan, nan] |  |
| T5_climate | meta | 541 | 17 | 0.917 [0.782, 1.000] | 0.031 [0.018, 0.042] | nan [nan, nan] | nan [nan, nan] |
| T6_compound | base | 648 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] |  |  |
| T6_compound | hand | 648 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | nan [nan, nan] |  |
| T6_compound | meta | 648 | 49 | 0.961 [0.909, 1.000] | 0.076 [0.063, 0.087] | nan [nan, nan] | nan [nan, nan] |
