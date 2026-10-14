# LBNL PFPU simulated fault set: hit and false-alarm rates of two checks (exploratory; LBNL_PFPU_NOTES.md hashed before any value was read)

SIMULATED data (HVACSIM+): a measured hit rate is at best a plausible upper bound on the real one, a false-alarm rate a plausible lower bound. One-minute Operate-mode samples; the faulted box is found from the data (the documentation says west; the files say south: LBNL_PFPU_DEVIATIONS.md D1).

## Hit rates (box S of the faulted run, the box the data show is faulted)

| catalogue cause | simulated fault | check | catalogue | measured (mean over severities) | after start-up | high-demand third | range over severities | verdict |
|---|---|---|---|---|---|---|---|---|
| damper_stuck | damper_stuck | bas_airflow | 0.75 | **1.00** | 1.00 | 1.00 | 1.00 to 1.00 | NO INFORMATION (above: a clean simulation can exceed real life) |
| flow_sensor | airflow_bias | bas_airflow | 0.50 | **1.00** | 1.00 | 1.00 | 1.00 to 1.00 | NO INFORMATION (above: a clean simulation can exceed real life) |
| controller_config | pi2_unstable | bas_airflow | 0.50 | **0.27** | 0.27 | 0.27 | 0.27 to 0.27 | OPTIMISTIC (informative) |
| reheat_fail (valve) | reheat_valve | bas_reheat | 0.75 | **0.08** | 0.08 | nan | 0.00 to 0.51 | OPTIMISTIC (informative) |

Post hoc sensitivity (added after the per-box table was seen, not part of the verdict): if `bas_reheat` also counts a valve that differs from its command when no heat is called for, the mean hit rate on reheat valve stuck or leaking is 0.56.

Per severity (box S, `rate`):

| fault | severity | bas_airflow | bas_reheat | reheat: share of Operate minutes with heat called for | reheat: rate while heat is called for |
|---|---|---|---|---|---|
| pi1_unstable | - | 0.07 | 0.07 | 12% | 0.58 |
| coil_fouling | Airside Minor | 0.00 | 0.00 | 9% | 0.00 |
| coil_fouling | Airside Moderate | 0.00 | 0.00 | 10% | 0.00 |
| coil_fouling | Airside Severe | 0.00 | 0.00 | 10% | 0.00 |
| coil_fouling | Waterside Minor | 0.00 | 0.00 | 9% | 0.00 |
| coil_fouling | Waterside Moderate | 0.00 | 0.00 | 9% | 0.00 |
| coil_fouling | Waterside Severe | 0.00 | 0.00 | 9% | 0.00 |
| reheat_valve | leak 20% | 0.00 | 0.00 | 3% | 0.00 |
| reheat_valve | leak 50% | 0.00 | 0.00 | 2% | 0.00 |
| reheat_valve | leak 80% | 0.00 | 0.00 | 2% | 0.00 |
| reheat_valve | stuck 0% | 0.00 | 0.51 | 51% | 1.00 |
| reheat_valve | stuck 100% | 0.00 | 0.01 | 2% | 0.72 |
| reheat_valve | stuck 20% | 0.00 | 0.07 | 8% | 0.85 |
| reheat_valve | stuck 50% | 0.00 | 0.03 | 3% | 0.85 |
| reheat_valve | stuck 80% | 0.00 | 0.01 | 2% | 0.65 |
| room_temp_bias | +2 C | 0.00 | 0.00 | 4% | 0.00 |
| room_temp_bias | +4 C | 0.00 | 0.00 | 2% | 0.00 |
| room_temp_bias | -2 C | 0.00 | 0.00 | 17% | 0.00 |
| room_temp_bias | -4 C | 0.00 | 0.00 | 35% | 0.00 |
| airflow_bias | +200 cfm | 1.00 | 0.00 | 3% | 0.00 |
| airflow_bias | +400 cfm | 1.00 | 0.00 | 3% | 0.00 |
| airflow_bias | -200 cfm | 1.00 | 0.00 | 31% | 0.00 |
| airflow_bias | -400 cfm | 1.00 | 0.00 | 66% | 0.00 |
| damper_stuck | 0% | 1.00 | 0.00 | 2% | 0.00 |
| damper_stuck | 100% | 1.00 | 0.00 | 95% | 0.00 |
| damper_stuck | 20% | 1.00 | 0.00 | 8% | 0.00 |
| damper_stuck | 50% | 1.00 | 0.00 | 53% | 0.00 |
| damper_stuck | 80% | 1.00 | 0.00 | 94% | 0.00 |
| pi2_unstable | - | 0.27 | 0.00 | 9% | 0.00 |
| fan_restricted | - | 0.00 | 0.00 | 12% | 0.00 |

## False-alarm rates

| check | catalogue bg | fault-free run, four boxes | the three healthy boxes in faulted runs, median over runs (range) | verdict (fault-free) |
|---|---|---|---|---|
| bas_airflow | 0.05 | 0.001 (0.001, 0.001, 0.001, 0.001) | 0.001 (0.001 to 0.001) | NO INFORMATION (below: a clean simulation is cleaner than real life) |
| bas_reheat | 0.05 | 0.000 (0.000, 0.000, 0.000, 0.000) | 0.000 (0.000 to 0.000) | NO INFORMATION (below: a clean simulation is cleaner than real life) |

## Predictions (written before any value was read)

- P1 (damper stuck, bas_airflow, within 0.15 of 0.75): FAILED (measured 1.00)
- P2 (airflow-sensor bias, bas_airflow at most 0.25): FAILED (measured 1.00)
- P3 (unstable PI2, bas_airflow between 0.30 and 0.80): FAILED (measured 0.27)
- P4 (reheat valve stuck or leaking, bas_reheat below 0.60): HELD (measured 0.08)
- P5 (bas_airflow false alarms in the fault-free run at most 5%): HELD (measured 0.001)

Not in the primary comparison (descriptive): coil fouling, room-temperature sensor bias, unstable PI1, restricted box fan; their rates are in `rates.csv`.
