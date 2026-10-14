# Trend-window checks in the visit (exploratory; TREND_NOTES.md hashed before any trend-window value was computed)

The same 100 visits (6 rooms each), the demo's mixed setting, `min_rate` 0.02, T3-noattr. Tool and world use the arm's catalogue; W0 = as it says, W1 = every rate 25% toward 0.5. The simulated data are a best case, so the trend rates are upper bounds.

## Rates used (mapped pairs only; clipped to [0.05, 0.95])

| catalogue cause(s) | check | catalogue | snapshot measured | 24 h window measured |
|---|---|---|---|---|
| actuator_fail, damper_mech, no_power, signal_fault | bas_airflow | 0.75 | 0.95 | 0.95 |
| flow_sensor | bas_airflow | 0.50 | 0.95 | 0.95 |
| controller_config | bas_airflow | 0.50 | 0.27 | 0.84 |
| reheat_fail | bas_reheat | 0.75 | 0.08 | 0.19 |

## Gates

- GB1 the unmodified catalogue equals the stored mixture-study accuracy, W0: **PASS** (74.83%)
- GB1 the unmodified catalogue equals the stored mixture-study accuracy, W1: **PASS** (54.67%)
- GB2 every answer in the check's vocabulary: asserted by the oracle

## W0

| arm | accuracy | shared | own fault, faulty handler | own fault, healthy handler | own fault, no shared cause | wrong and confident | minutes / visit | bas_airflow + bas_reheat looks / visit | accuracy gain vs base (95% CI) | added minutes (95% CI) | verdict at W0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| base | 74.8% | 92.5% | 10.5% | 77.3% | 75.0% | 6.8% | 194 | 6.97 | - | - | - |
| snapshot-measured | 74.8% | 92.0% | 14.0% | 77.3% | 74.7% | 5.7% | 174 | 4.82 | +0.0 (-2.2, +2.2) | -20 (-27, -12) | NEITHER |
| trend | 76.3% | 92.5% | 7.0% | 81.8% | 78.0% | 3.5% | 185 | 3.92 | +1.5 (-0.8, +4.0) | -9 (-17, -1) | NEITHER |
| trend_2min | 76.8% | 92.5% | 12.3% | 81.8% | 78.0% | 6.2% | 179 | 4.89 | +2.0 (-0.3, +4.3) | -15 (-22, -8) | NEITHER |
| trend_8min | 75.3% | 92.0% | 8.8% | 81.8% | 76.0% | 3.7% | 188 | 2.77 | +0.5 (-1.8, +2.8) | -5 (-14, +2) | NEITHER |
| sharp10 (context) | 79.5% | 98.0% | 1.8% | 79.5% | 82.0% | 9.7% | 161 | 5.17 | +4.7 (+1.5, +8.0) | -33 (-45, -22) | TRADE |
| sharp25 (context) | 85.7% | 100.0% | 0.0% | 88.6% | 92.0% | 9.5% | 144 | 4.91 | +10.8 (+7.2, +14.7) | -49 (-62, -38) | TRADE |

## W1

| arm | accuracy | shared | own fault, faulty handler | own fault, healthy handler | own fault, no shared cause | wrong and confident | minutes / visit | bas_airflow + bas_reheat looks / visit | accuracy gain vs base (95% CI) | added minutes (95% CI) | verdict at W0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| base | 54.7% | 78.4% | 10.5% | 50.0% | 48.0% | 8.3% | 205 | 6.89 | - | - | - |
| snapshot-measured | 53.0% | 78.4% | 7.0% | 50.0% | 45.3% | 9.5% | 182 | 4.80 | -1.7 (-4.0, +0.8) | -22 (-32, -13) | (not part of the verdict) |
| trend | 53.2% | 78.4% | 7.0% | 54.5% | 45.0% | 7.2% | 194 | 4.16 | -1.5 (-4.0, +1.0) | -11 (-19, -3) | (not part of the verdict) |
| trend_2min | 52.2% | 77.4% | 7.0% | 52.3% | 44.0% | 9.8% | 186 | 4.85 | -2.5 (-5.0, +0.2) | -18 (-27, -10) | (not part of the verdict) |
| trend_8min | 52.8% | 77.4% | 12.3% | 56.8% | 43.7% | 8.0% | 195 | 3.02 | -1.8 (-4.0, +0.5) | -9 (-20, -0) | (not part of the verdict) |
| sharp10 (context) | 53.7% | 88.4% | 1.8% | 47.7% | 41.3% | 33.0% | 129 | 4.57 | -1.0 (-4.8, +3.0) | -76 (-91, -62) | (not part of the verdict) |
| sharp25 (context) | 55.5% | 84.4% | 3.5% | 47.7% | 47.3% | 33.0% | 127 | 4.39 | +0.8 (-3.0, +4.7) | -77 (-93, -63) | (not part of the verdict) |

## Predictions (written before any trend-window value was computed)

- B1 (the trend catalogue raises W0 accuracy by 0.5 to 3 points): **HELD** (+1.5)
- B2 (every check 25% sharper: W0 accuracy between 82% and 90%, not 90%): **HELD** (85.7%)
- B3 (the 4-minute trend look changes minutes per visit by less than 5%): **HELD** (-9 min on 194)
- B4 (wrong-and-confident does not rise by more than 1 point under the trend catalogue): **HELD** (-3.3)

Sim conventions that flatter the checks: the oracle answers a room check from the room's own first-order cause; the window rates come from a clean simulation. The 'sharper' rows are not measured by any data.
