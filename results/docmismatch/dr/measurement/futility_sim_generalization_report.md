# Does futility stopping generalize past real DEV? (Addendum 10, simulation-only T1-T6)

`vav_zone`, channels 0+2 excluded in both variants (Addendum 5's `exclude_struct`), same T1-T6 held-out DR suites as Addendum 5/6's sim ceiling. `no_futility` = full nmax=24 budget. `futility` = futility_window=4, futility_margin=0.05 (Addendum 7's exact frozen values, not retuned here). Simulation only -- see the addendum's explicit caveat.

## Technician reads per episode (the primary metric)

| suite | variant | n eps | mean n_read | median n_read | reads saved vs no_futility | frac futile |
|---|---|---|---|---|---|---|
| T1_in_range | no_futility | 128 | 24.0 | 24 | 0.0 | 0.0% |
| T1_in_range | futility | 128 | 8.0 | 8 | 16.0 | 100.0% |
| T2_regime | no_futility | 128 | 24.0 | 24 | 0.0 | 0.0% |
| T2_regime | futility | 128 | 8.0 | 8 | 16.0 | 100.0% |
| T3_control | no_futility | 128 | 24.0 | 24 | 0.0 | 0.0% |
| T3_control | futility | 128 | 8.0 | 8 | 16.0 | 100.0% |
| T4_topology | no_futility | 128 | 24.0 | 24 | 0.0 | 0.0% |
| T4_topology | futility | 128 | 8.0 | 8 | 16.0 | 100.0% |
| T5_climate | no_futility | 128 | 24.0 | 24 | 0.0 | 0.0% |
| T5_climate | futility | 128 | 8.0 | 8 | 16.0 | 100.0% |
| T6_compound | no_futility | 128 | 24.0 | 24 | 0.0 | 0.0% |
| T6_compound | futility | 128 | 8.0 | 8 | 16.0 | 100.0% |

## Forced accuracy per suite (point estimates, small per-suite N -- no cluster bootstrap; does stopping early cost anything?)

| suite | variant | n eps | forced acc | diff vs no_futility |
|---|---|---|---|---|
| T1_in_range | no_futility | 128 | 0.617 |  |
| T1_in_range | futility | 128 | 0.695 | +0.078 |
| T2_regime | no_futility | 128 | 0.602 |  |
| T2_regime | futility | 128 | 0.562 | -0.039 |
| T3_control | no_futility | 128 | 0.602 |  |
| T3_control | futility | 128 | 0.578 | -0.023 |
| T4_topology | no_futility | 128 | 0.602 |  |
| T4_topology | futility | 128 | 0.594 | -0.008 |
| T5_climate | no_futility | 128 | 0.461 |  |
| T5_climate | futility | 128 | 0.469 | +0.008 |
| T6_compound | no_futility | 128 | 0.578 |  |
| T6_compound | futility | 128 | 0.570 | -0.008 |