# Trend-window versions of two BAS checks: how much sharper than a snapshot, and what that does to the visit (EXPLORATORY; written and hashed before any trend-window value was computed)

Already seen before this note (so not predicted): the SNAPSHOT hit rates on the LBNL PFPU simulated fault set (`results/docmismatch/lbnl_pfpu/report.md`): `bas_airflow` on damper stuck 1.00, airflow-sensor bias 1.00, unstable damper loop (PI2) 0.27;
`bas_reheat` on reheat valve stuck or leaking 0.08 (the faulted box is S; the documentation's "west" is wrong). The simulation is a best case: a hit rate measured here is at most a plausible upper bound on a real one.

## Part A: the same rules applied to a trend window (`trend_pfpu.py`)

Technician looks at the last day of the box's trend in the BAS instead of one live value. Per box, per minute the snapshot rules are unchanged: airflow flag = |flow - setpoint| > 10% of setpoint; reheat flag = command > 0.10 and |position - command| > 0.10.
A window rule judges the TRAILING window of Operate-mode minutes ending at an evaluation minute (every 15th Operate minute):

- `bas_airflow`, window abnormal when at least 20% of the window's Operate minutes are flagged (at least 60 Operate minutes in the window, else no verdict, counted as not flagged).
- `bas_reheat`, window abnormal when, among the window's Operate minutes with heat called for, at least 50% are flagged (at least 15 such minutes, else no verdict, counted as not flagged). Post hoc sensitivity, labelled so: also counting a valve that differs from its command when no heat is called.

Windows: 24 hours (primary) and 4 hours (secondary). Thresholds 20% and 50% were chosen now, from the wording ("a fifth of the day", "half of the heat calls"), not tuned on the faults. A hit rate = the share of evaluation minutes in the faulted box (S) at which the window is abnormal, averaged equally over severities within a fault family, as for the snapshot. False alarm = the same in the fault-free run (four boxes) and in the three healthy boxes of the faulted runs.

Gate GA1: the snapshot rates recomputed by this script equal the stored ones (`lbnl_pfpu/summary.json`) to 0.01. A failed gate = NO RESULT.

## Part B: what those rates do to the visit (`study_trend.py`)

The same 100 registered visits, the demo's mixed setting, `min_rate` 0.02, T3-noattr, worlds W0 (checks as the tool assumes) and W1 (every rate 25% toward 0.5). The tool and the world both use the modified catalogue below (the tool is "updated and knows"), compared against the unmodified catalogue on the same visits.

Mapping (fixed now). Measured 24-hour window rates replace the catalogue's `detects` only where the simulation has an analogue, clipped into [0.05, 0.95] (never more certain than the strongest catalogue level plus a margin); `bg` unchanged (0.05); everything else unchanged:

| check | cause(s) in the catalogue | takes the 24 h window rate of |
|---|---|---|
| `bas_airflow` | actuator_fail, damper_mech, no_power, signal_fault (a damper that does not follow its command) | damper stuck |
| `bas_airflow` | flow_sensor | airflow-sensor bias |
| `bas_airflow` | controller_config | unstable damper loop (PI2) |
| `bas_reheat` | reheat_fail | reheat valve stuck or leaking |

Time: a trend look costs 4 minutes instead of 2 (assumption: opening the trend view); sensitivity 2 and 8. Context rows, NOT measured by this data: every reading check sharpened by 10% and by 25% (rates move away from 0.5; tool and world), to show what a general sharpening would do.

Gates GB1: the unmodified-catalogue arm equals the stored mixture-study numbers (74.83% / 54.67%, 0.2 points). GB2: every answer in vocabulary.

## Decision rule (fixed now)

The trend catalogue is **WORTH IT** at W0 if the accuracy gain is at least 3 points with a paired 95% interval excluding 0, added minutes at most 10%, and wrong-and-confident not higher than base by more than 1 point; **TRADE** if the accuracy gain holds but another bar fails; **NEITHER** otherwise.

## Predictions (before any trend-window value was computed)

- T1: unstable damper loop, 24 h window: between 0.60 and 0.95 (snapshot 0.27).
- T2: reheat valve stuck or leaking, 24 h window: between 0.25 and 0.60 (well above the snapshot 0.08, below the catalogue's 0.75; leaking valves stay near 0).
- T3: damper stuck and airflow-sensor bias stay at 0.98 or above.
- T4: false-alarm rates of the window rules in the fault-free run: at most 0.02.
- T5: the 4 h window gives lower hit rates than the 24 h window for the unstable loop and for the reheat valve.
- B1: the trend catalogue raises W0 accuracy by 0.5 to 3 points (only a few cause pairs change).
- B2: sharpening every check by 25% takes W0 accuracy to between 82% and 90%, not to 90% (folding remains).
- B3: the 4-minute trend look changes minutes per visit by less than 5%.
- B4: wrong-and-confident does not rise by more than 1 point under the trend catalogue.
