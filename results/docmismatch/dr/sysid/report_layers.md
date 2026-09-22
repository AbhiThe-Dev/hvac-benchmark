# Per-building system identification: honest-confidence layer check (Addendum 2)

Baseline arm, policy `active`, building-cluster bootstrap (300 resamples). `none` = plain 0.95 stopping rule. `new` = calibrated reliability layer, fit separately per variant on that variant's own leave-one-training-building-out records (the held-out building is adapted too, matching real deployment).

Inner-fit diagnostics: base={'n_oof': 267, 'deff': 1.389234411988351, 'n_units': 8, 'n_all': 585, 'oof_tail': None, 'slot_tail': {np.str_('ahu_sat'): None, np.str_('ahu_vav'): {'lb': 0.9111645792376053, 'acc': np.float64(1.0), 'n': 33, 'clusters': 21}, np.str_('branch_coil'): None, np.str_('coil_ahu'): None, np.str_('coil_vav'): None, np.str_('loop_branch'): None, np.str_('vav_dat'): {'lb': 0.9111645792376053, 'acc': np.float64(1.0), 'n': 33, 'clusters': 21}}}
adapted={'n_oof': 269, 'deff': 1.334397727513547, 'n_units': 8, 'n_all': 585, 'oof_tail': None, 'slot_tail': {np.str_('ahu_sat'): None, np.str_('ahu_vav'): {'lb': 0.9143861542827891, 'acc': np.float64(1.0), 'n': 33, 'clusters': 21}, np.str_('branch_coil'): None, np.str_('coil_ahu'): None, np.str_('coil_vav'): None, np.str_('vav_dat'): {'lb': 0.9072983472220424, 'acc': np.float64(0.9615384615384616), 'n': 78, 'clusters': 44}}}

## layer = `none`

| suite | variant | n eps | answered | acc | cov | diff acc | diff cov |
|---|---|---|---|---|---|---|---|
| T1_in_range | base | 577 | 280 | 0.765 [0.680, 0.848] | 0.486 [0.428, 0.536] | | |
| T1_in_range | adapted | 577 | 280 | 0.829 [0.750, 0.898] | 0.486 [0.433, 0.538] | 0.063 [0.038, 0.097] | -0.000 [-0.025, 0.026] |
| T2_regime | base | 543 | 283 | 0.757 [0.687, 0.820] | 0.521 [0.476, 0.563] | | |
| T2_regime | adapted | 543 | 281 | 0.801 [0.720, 0.864] | 0.518 [0.454, 0.572] | 0.044 [0.014, 0.075] | -0.004 [-0.060, 0.039] |
| T3_control | base | 581 | 280 | 0.721 [0.658, 0.773] | 0.482 [0.422, 0.548] | | |
| T3_control | adapted | 581 | 276 | 0.802 [0.757, 0.848] | 0.475 [0.427, 0.527] | 0.080 [0.049, 0.111] | -0.006 [-0.037, 0.017] |
| T4_topology | base | 658 | 345 | 0.820 [0.776, 0.860] | 0.524 [0.501, 0.549] | | |
| T4_topology | adapted | 658 | 340 | 0.877 [0.832, 0.919] | 0.517 [0.476, 0.566] | 0.057 [0.035, 0.080] | -0.008 [-0.028, 0.017] |
| T5_climate | base | 541 | 276 | 0.744 [0.674, 0.808] | 0.510 [0.468, 0.545] | | |
| T5_climate | adapted | 541 | 264 | 0.789 [0.737, 0.842] | 0.489 [0.440, 0.534] | 0.045 [0.003, 0.099] | -0.021 [-0.054, 0.005] |
| T6_compound | base | 648 | 320 | 0.828 [0.777, 0.879] | 0.494 [0.462, 0.531] | | |
| T6_compound | adapted | 648 | 310 | 0.898 [0.868, 0.927] | 0.478 [0.435, 0.516] | 0.070 [0.032, 0.111] | -0.015 [-0.043, 0.012] |

## layer = `new`

| suite | variant | n eps | answered | acc | cov | diff acc | diff cov |
|---|---|---|---|---|---|---|---|
| T1_in_range | base | 577 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | | |
| T1_in_range | adapted | 577 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | nan [nan, nan] | 0.000 [0.000, 0.000] |
| T2_regime | base | 543 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | | |
| T2_regime | adapted | 543 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | nan [nan, nan] | 0.000 [0.000, 0.000] |
| T3_control | base | 581 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | | |
| T3_control | adapted | 581 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | nan [nan, nan] | 0.000 [0.000, 0.000] |
| T4_topology | base | 658 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | | |
| T4_topology | adapted | 658 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | nan [nan, nan] | 0.000 [0.000, 0.000] |
| T5_climate | base | 541 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | | |
| T5_climate | adapted | 541 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | nan [nan, nan] | 0.000 [0.000, 0.000] |
| T6_compound | base | 648 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | | |
| T6_compound | adapted | 648 | 0 | nan [nan, nan] | 0.000 [0.000, 0.000] | nan [nan, nan] | 0.000 [0.000, 0.000] |
