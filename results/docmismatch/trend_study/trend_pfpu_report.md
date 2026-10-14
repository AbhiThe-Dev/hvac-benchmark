# Trend-window versions of two BAS checks on the LBNL PFPU simulated fault set (exploratory; TREND_NOTES.md hashed before any trend-window value was computed)

SIMULATED data; the faulted box is S. A window = the trailing Operate-mode minutes, evaluated at every 15th Operate minute. `bas_airflow` window abnormal when at least 20% of its minutes are flagged (at least 60 minutes); `bas_reheat` window abnormal when at least 50% of its heat-called minutes are flagged (at least 15 such minutes, else no verdict = not flagged).

## Gate GA1: the snapshot rates recomputed here equal the stored ones (0.01)

- damper_stuck: recomputed 0.9998, stored 0.9998: **PASS**
- airflow_bias: recomputed 1.0000, stored 1.0000: **PASS**
- pi2_unstable: recomputed 0.2734, stored 0.2734: **PASS**
- reheat_valve: recomputed 0.0790, stored 0.0790: **PASS**

## Hit rates in the faulted box (mean over severities; range in brackets)

| fault | check | snapshot | 24 h window | 4 h window | catalogue today |
|---|---|---|---|---|---|
| damper_stuck | bas_airflow | 1.00 | **0.98** (0.98 to 0.98) | 0.92 (0.92 to 0.92) | 0.75 |
| airflow_bias | bas_airflow | 1.00 | **0.98** (0.98 to 0.98) | 0.92 (0.92 to 0.92) | 0.50 |
| pi2_unstable | bas_airflow | 0.27 | **0.84** (0.84 to 0.84) | 0.70 (0.70 to 0.70) | 0.50 |
| reheat_valve | bas_reheat | 0.08 | **0.19** (0.00 to 0.76) | 0.12 (0.00 to 0.61) | 0.75 |

Reheat valve, 24 h window: no verdict (fewer than 15 heat-called minutes in the window) in 73% of windows; post hoc sensitivity counting a valve that differs from its command when no heat is called: 0.59.

Per severity (24 h window, faulted box):

| fault | severity | snapshot | 24 h window |
|---|---|---|---|
| reheat_valve | leak 20% | 0.00 | 0.00 |
| reheat_valve | leak 50% | 0.00 | 0.00 |
| reheat_valve | leak 80% | 0.00 | 0.00 |
| reheat_valve | stuck 0% | 0.51 | 0.76 |
| reheat_valve | stuck 100% | 0.01 | 0.12 |
| reheat_valve | stuck 20% | 0.07 | 0.28 |
| reheat_valve | stuck 50% | 0.03 | 0.19 |
| reheat_valve | stuck 80% | 0.01 | 0.12 |
| airflow_bias | +200 cfm | 1.00 | 0.98 |
| airflow_bias | +400 cfm | 1.00 | 0.98 |
| airflow_bias | -200 cfm | 1.00 | 0.98 |
| airflow_bias | -400 cfm | 1.00 | 0.98 |
| damper_stuck | 0% | 1.00 | 0.98 |
| damper_stuck | 100% | 1.00 | 0.98 |
| damper_stuck | 20% | 1.00 | 0.98 |
| damper_stuck | 50% | 1.00 | 0.98 |
| damper_stuck | 80% | 1.00 | 0.98 |
| pi2_unstable | - | 0.27 | 0.84 |

False alarms of the 24 h window rules (fault-free run and the three healthy boxes of every faulted run): airflow 0.000, reheat 0.000 (a clean simulation: no information about real equipment).

## Predictions (written before any trend-window value was computed)

- T1 (unstable damper loop, 24 h window between 0.60 and 0.95): **HELD** (0.84)
- T2 (reheat valve stuck/leaking, 24 h window between 0.25 and 0.60): **FAILED** (0.19)
- T3 (damper stuck and airflow-sensor bias stay at 0.98 or above): **HELD** (0.983, 0.983)
- T4 (false alarms of the window rules at most 0.02): **HELD** (airflow 0.000, reheat 0.000)
- T5 (4 h window lower than 24 h for the unstable loop and the reheat valve): **HELD** (loop 0.70 vs 0.84; valve 0.12 vs 0.19)
