# Two suggested reliability improvements, tested on the LBNL PFPU simulated fault set (EXPLORATORY; written and hashed before any value of the new rules was computed)

Source of the suggestions: a second agent's reply to a reliability question (pasted by the user). Already seen before this note (so not predicted): the existing rules' snapshot and 24 h window rates (`results/docmismatch/lbnl_pfpu/`, `trend_study/`): airflow check on unstable loop 0.27 (snapshot), 0.70 (4 h), 0.84 (24 h); reheat command-vs-position rule on reheat valve stuck or leaking 0.08 (snapshot), 0.19 (24 h), leaks 0.00. The simulation is a best case, so hit rates are at most plausible upper bounds, false-alarm rates plausible lower bounds. Faulted box = the one found from the damper footprint (S).
Caveat: PFPU is a fan-powered box; the tool is for single-duct VAV boxes.

## Test 1: a discharge-temperature check for a leaking reheat valve

Rule (fixed now): on Operate-mode minutes with the reheat command at most 0.02 AND the box fan off (`VAV_FAN_CS` = 0) AND both temperatures finite, abnormal when the box discharge air temperature (`VAV_DAT`) exceeds the air handler supply air temperature (`SA_TEMP`) by more than 3 degF. (The fan-on exclusion is there because a parallel fan mixes warm plenum air without any reheat.)
Snapshot rate = share of eligible minutes flagged. 24 h window rate: at every 15th Operate minute, the trailing 1440 minutes are abnormal when at least 20% of their eligible minutes are flagged (at least 60 eligible minutes, else no verdict = not flagged), as in `trend_pfpu.py`.
Compared with the existing rule (heat called for and the valve not following; 24 h window: at least 50% of at least 15 heat-called minutes flagged) and with "either rule" at the same evaluation minutes. Families, equally weighted over severities: reheat valve LEAK (20, 50, 80%), reheat valve STUCK (0, 20, 50, 80, 100%), and the pooled stuck+leak mean (8) that the catalogue's 0.75 for reheat_fail is compared with. False alarms: fault-free run and the three healthy boxes of every faulted run.

## Test 2: a five-minute average near maximum airflow for the airflow check

Rule (fixed now): at every 15th Operate minute at which the box's airflow setpoint is in the top third of that file's Operate setpoints (the "near maximum" third) and the previous five minutes are all valid Operate minutes, abnormal when the mean of |flow - setpoint| / setpoint over the five minutes exceeds 10%. Compared, at the same minutes, with the one-minute snapshot rule (|flow - setpoint| > 10% of setpoint) and, from the earlier run, with the 24 h window. Also reported at all Operate minutes. Families: damper stuck, airflow-sensor bias, unstable damper loop (PI2). False alarms as above.

## Gates (a failed gate = NO RESULT)

G1: the existing reheat rule's snapshot family rate for stuck+leak recomputed here equals the stored 0.0790 (0.01). G2: the airflow snapshot rate on the unstable loop recomputed here equals the stored 0.2734 (0.01).

## Calling a rule sharper (fixed now)

A new rule is SHARPER if it raises the hit rate of the family it targets (Test 1: stuck+leak, 24 h window "either rule" against the existing rule alone; Test 2: unstable loop, five-minute mean against the snapshot at the same minutes) by at least 0.15 with a false-alarm rate of at most 0.05; otherwise NOT SHARPER.

## Predictions (before any value of the new rules was computed)

- L1: the discharge-temperature rule flags reheat valve leaks at 0.60 or more on average over the three severities (snapshot).
- L2: it flags valves stuck at 100%, 80% and 50% at 0.80 or more each, and valves stuck at 0% at 0.05 or less.
- L3: its false-alarm rate (fault-free and healthy boxes, snapshot) is at most 0.05.
- L4: "either rule" over the 24 h window reaches 0.60 or more on the pooled stuck+leak family (existing rule alone: 0.19).
- S1: the five-minute mean flags the unstable loop between 0.15 and 0.60 at near-maximum minutes (below the 24 h window's 0.84).
- S2: damper stuck and airflow-sensor bias stay at 0.95 or more under the five-minute mean.
- S3: the five-minute mean's false-alarm rate is at most 0.02.
