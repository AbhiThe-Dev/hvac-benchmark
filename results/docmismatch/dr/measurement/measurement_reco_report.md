# Missing-measurement recommendation: does excluding it help? (Addendum 5)

real DEV vav_zone episodes (n=1200), building-cluster (day) bootstrap (300 resamples). `include`=all 3 channels, `exclude_stat`=channel 2 dropped (Addendum 5a), `exclude_struct`=channels 0+2 dropped (Addendum 5b).

## Real DEV

| variant | n eps | answered | acc | cov | forced acc | diff acc vs include | diff forced vs include |
|---|---|---|---|---|---|---|---|
| include (none) | 1200 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.528 [0.492, 0.562] |  |  |
| exclude_stat (none) | 1200 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.533 [0.505, 0.563] | nan [nan, nan] | 0.005 [-0.008, 0.018] |
| exclude_struct (none) | 1200 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.556 [0.526, 0.589] | nan [nan, nan] | 0.028 [0.006, 0.054] |

| variant | n eps | answered | acc | cov | forced acc | diff acc vs include | diff forced vs include |
|---|---|---|---|---|---|---|---|
| include (new) | 1200 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.528 [0.492, 0.562] |  |  |
| exclude_stat (new) | 1200 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.533 [0.505, 0.563] | nan [nan, nan] | 0.005 [-0.008, 0.018] |
| exclude_struct (new) | 1200 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.556 [0.526, 0.589] | nan [nan, nan] | 0.028 [0.006, 0.054] |

## Simulation-only ceiling (T1-T6, baseline arm, plain rule) -- upper bound, NOT a real-world claim

| suite | variant | n eps | answered | acc | cov | forced acc | diff acc vs include | diff forced vs include |
|---|---|---|---|---|---|---|---|---|
| T1_in_range | include | 128 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.594 [0.519, 0.676] |  |  |
| T1_in_range | exclude_stat | 128 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.578 [0.507, 0.664] | nan [nan, nan] | -0.016 [-0.039, 0.000] |
| T1_in_range | exclude_struct | 128 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.617 [0.531, 0.723] | nan [nan, nan] | 0.023 [-0.047, 0.086] |
| T2_regime | include | 128 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.539 [0.445, 0.641] |  |  |
| T2_regime | exclude_stat | 128 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.531 [0.445, 0.617] | nan [nan, nan] | -0.008 [-0.023, 0.000] |
| T2_regime | exclude_struct | 128 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.602 [0.484, 0.711] | nan [nan, nan] | 0.062 [-0.016, 0.141] |
| T3_control | include | 128 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.508 [0.453, 0.578] |  |  |
| T3_control | exclude_stat | 128 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.516 [0.461, 0.578] | nan [nan, nan] | 0.008 [0.000, 0.023] |
| T3_control | exclude_struct | 128 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.602 [0.531, 0.711] | nan [nan, nan] | 0.094 [0.016, 0.172] |
| T4_topology | include | 128 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.500 [0.477, 0.520] |  |  |
| T4_topology | exclude_stat | 128 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.484 [0.457, 0.508] | nan [nan, nan] | -0.016 [-0.039, 0.000] |
| T4_topology | exclude_struct | 128 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.602 [0.516, 0.684] | nan [nan, nan] | 0.102 [0.012, 0.188] |
| T5_climate | include | 128 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.516 [0.477, 0.570] |  |  |
| T5_climate | exclude_stat | 128 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.516 [0.477, 0.570] | nan [nan, nan] | 0.000 [0.000, 0.000] |
| T5_climate | exclude_struct | 128 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.461 [0.375, 0.547] | nan [nan, nan] | -0.055 [-0.133, 0.039] |
| T6_compound | include | 128 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.477 [0.438, 0.516] |  |  |
| T6_compound | exclude_stat | 128 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.469 [0.438, 0.508] | nan [nan, nan] | -0.008 [-0.023, 0.000] |
| T6_compound | exclude_struct | 128 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.578 [0.492, 0.664] | nan [nan, nan] | 0.102 [0.023, 0.172] |