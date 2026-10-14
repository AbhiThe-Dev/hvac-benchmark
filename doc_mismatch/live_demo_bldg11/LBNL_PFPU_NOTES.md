# Hit and false-alarm rates of two control-system checks against the LBNL PFPU simulated fault set (EXPLORATORY; written and hashed before any data value was read)

Data: LBNL FDD Data Sets, parallel fan-powered VAV units (PFPU), Figshare article 22344280 (CC BY 4.0), 31 one-year files at 1-minute steps. SIMULATED (HVACSIM+): one air handler, four boxes (E, I, S, W),
the fault always in the west box. Read before the data: the documentation (`LBNL_FDD_Data_Sets_FPU.pdf`). Nothing else was looked at.

## Why this is only a bound

A simulation has clean sensors, tight control loops and no technician. A hit rate measured here is at best a PLAUSIBLE UPPER BOUND on what the same reading shows in a real building (real faults could be
harsher than the simulated ones, so even that is not guaranteed); a false-alarm rate here is a PLAUSIBLE LOWER BOUND. So only one direction of finding is informative:
a measured hit rate BELOW the catalogue's, or a measured false-alarm rate AT OR ABOVE the catalogue's, says the catalogue is optimistic even against the best case.

## The two checks, as the catalogue words them, made numeric (fixed now)

- `bas_airflow` ("does the measured airflow miss the setpoint by more than about 10%?"): abnormal when |VAV_PM_CFM - VAV_PM_CFM_SP| > 10% of VAV_PM_CFM_SP. Catalogue rates: damper_mech and actuator_fail "good" (0.75), flow_sensor and controller_config "partial" (0.50), all other causes `bg` 0.05.
- `bas_reheat` ("is heat called for but the valve not responding?"): abnormal when RH_VLV_DM > 0.10 and |RH_VLV - RH_VLV_DM| > 0.10. Catalogue rate: reheat_fail "good" (0.75), `bg` 0.05.

The catalogue's other checks are not measured here (no command point for the damper; hunting and zone checks would need definitions I would have to invent).

## Mapping simulated faults to catalogue causes (fixed now; severities equally weighted within a fault type)

| catalogue cause | simulated fault (west box) | catalogue rate |
|---|---|---|
| damper_mech, actuator_fail (damper does not follow) | VAV damper stuck at 0, 20, 50, 80, 100% | 0.75 |
| flow_sensor | VAV airflow sensor bias -400, -200, +200, +400 cfm (the logged value is the biased one) | 0.50 |
| controller_config | room VAV damper control (PI2) unstable | 0.50 |
| reheat_fail (valve) | reheat valve stuck at 0, 20, 50, 80, 100% and leaking 20, 50, 80% | 0.75 |

Not in the primary comparison, reported descriptively: coil fouling (water- and air-side), room-temperature sensor bias, unstable room-temperature control (PI1), box fan restricted flow.

## Sampling (fixed now)

Samples in the air handler's Operate mode (SYS_CTL = 1) only. A hit rate = the share of those one-minute samples at which the check reads abnormal in the west box of the faulted run. A false-alarm rate = the same share in
(a) the fault-free run, all four boxes, and (b) the three healthy boxes (E, I, S) of the faulted runs. Sensitivity: dropping the first 30 minutes after each start-up. Stratum (reported, not primary): the third of Operate samples
with the highest airflow setpoint (the "hot afternoon" a complaint is about). One-minute samples are treated as the single reading a technician takes.

## Decision rule (fixed now)

Hit rate: measured below catalogue - 0.15 -> catalogue OPTIMISTIC (informative); within 0.15 -> CONSISTENT; above catalogue + 0.15 -> NO INFORMATION (a clean simulation can exceed real life).
False alarm: measured above 2 x catalogue `bg` -> OPTIMISTIC (informative); between half and twice -> REASONABLE (informative: even a clean simulation produces it); below half -> NO INFORMATION.

## Predictions (before any value was read)

- P1: damper stuck, `bas_airflow`: mean hit rate within 0.15 of 0.75 (CONSISTENT).
- P2: airflow sensor bias, `bas_airflow`: mean hit rate at most 0.25 (the box's controller tracks the biased reading), far below the catalogue's 0.50 -> OPTIMISTIC.
- P3: unstable PI2, `bas_airflow`: hit rate between 0.30 and 0.80.
- P4: reheat valve stuck or leaking, `bas_reheat`: mean hit rate below 0.60 (the check can only fire while heat is being called for, which is a minority of occupied minutes) -> OPTIMISTIC.
- P5: `bas_airflow` false alarms in the fault-free run: at most 5%.
