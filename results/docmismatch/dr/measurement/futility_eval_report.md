# Does futility stopping save technician tests without costing accuracy? (Addendum 7)

real DEV vav_zone episodes (n=1200), channels 0+2 excluded in both variants (Addendum 5's `exclude_struct`). `no_futility` = full nmax=24 budget every time (the existing baseline). `futility` = futility_window=4, futility_margin=0.05 (frozen before this run). Building/day-cluster bootstrap (300 resamples).

## Technician reads per episode (the actual target of this addendum)

| variant | mean n_read | median n_read | reads saved vs no_futility | frac futile |
|---|---|---|---|---|
| no_futility | 24.0 | 24 | 0.0 | 0.0% |
| futility | 8.0 | 8 | 16.0 | 100.0% |

## Forced accuracy (does stopping early cost anything?)

| variant (layer) | n eps | answered | acc | cov | forced acc | diff forced vs no_futility |
|---|---|---|---|---|---|---|
| no_futility (none) | 1200 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.556 [0.526, 0.589] |  |
| futility (none) | 1200 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.543 [0.514, 0.572] | -0.013 [-0.030, 0.004] |
| no_futility (new) | 1200 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.556 [0.526, 0.589] |  |
| futility (new) | 1200 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | 0.543 [0.514, 0.572] | -0.013 [-0.030, 0.004] |