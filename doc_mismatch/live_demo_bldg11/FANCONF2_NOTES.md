# A confirm step by a visit to the air handler (EXPLORATORY; written and hashed before any run; the demos, the pilot and the shipped defaults are not touched)

## Why this study exists

FANCONF_NOTES.md registered a confirm step by the BAS fan status (`bas_ahu_fan`). It never fired: the three real Mortar layouts have no fan-status point, and on the first demo's building the routine already reads it. The fan-off mixture's false fan-off calls (4-6% of rooms on the real layouts, FANMIX study) happen where the only air-handler check that separates fan off from low static is `ahu_visit` (a walk to the air handler: catalogue 15 minutes to get there + 4 to look = 19 minutes when the technician is not already there; abnormal with probability 0.92 under fan off, 0.10 under low static, 0.04 otherwise). `bas_static`, `static_at_box` and `ahu_gauge` read the same under both. So: does a confirm by `ahu_visit` remove the false fan-off calls and keep the fan-off gain, and what does the walk cost?

## Arms (the routine is `tool_ticket_memo2` through the replica of `study_fanconfirm.run_ticket_confirm`, which equals `study_folding.run_ticket_v(..., "base")` with the step off; T3-noattr, `min_rate` 0.02, each building's own check list)

- TODAY: `low_mix` 5/15/50/90% x 1/4. FAN: TODAY + `fan_mix` 5/15/50/90% x 1/4.
- **FANV**: FAN, plus: after a room's own checks, if its leading cause is fan off or low static and `ahu_visit` has not been answered for its handler in this visit (and is available), take it once as the room's own check, carry it to later rooms on that handler through the routine's air-handler memo, and let the room continue (the routine's loop) before concluding.
- **FANO**: FANV, but only when the question is still open: the leading cause is fan off or low static AND the other of the two has probability at least 0.05 in the room's own posterior.

## Visit families, measures, worlds

As FANCONF_NOTES.md (A-LS x3, A-FAN x3, B bldg15 and bldg11, S1-S4; same draws; W0 and W1); the same measures. Paired bootstrap over visits (2000).

## Gates (a failed gate = NO RESULT)

- G1: TODAY and FAN reproduce the stored FANMIX numbers on A-LS and A-FAN, W0 (as FANCONF_NOTES.md G1).
- G2: the replica with the step switched off equals `run_ticket_v` exactly on 40 visit-world-setting runs.
- G3: composition as stated. G4: answers in vocabulary (asserted) and an order-independent oracle.
- G5 (not vacuous this time): `ahu_visit` is in the check list of every family; under FANV it is asked at least once in each of the six real-layout A-LS and A-FAN families and in S3; never more than once per handler per visit and never after it was answered for that handler.

## Predictions (before any run; W0; points are percentage points per room)

- V1: A-LS on each building: FANV's false fan-off rate at most 2% and its accuracy within 3 points of TODAY.
- V2: A-FAN on each building: FANV's accuracy on the fan-off rooms at least FAN's minus 2.
- V3: B (bldg15, bldg11), S3, S4: FANV within 2 points of TODAY on accuracy and wrong-and-confident at most 1 point above TODAY's.
- V4: S1 (the model's own world): FANV within 3 points of TODAY.
- V5: minutes per visit under FANV within +10% of TODAY in A-LS (3) and B (2). (The walk is 19 minutes against visits of 190-240; I expect this to be near the line and fail on at least one layout.)
- V6: FANO against FANV, A-LS pooled over the three buildings: FANO removes at least 70% as many false fan-off calls as FANV does (measured from FAN's rate), and its extra minutes over FAN are at most 70% of FANV's extra minutes over FAN.

## Decision rule (set now)

FANV is **worth adopting alongside the fan-off mixture** only if V1-V5 all hold. FANO is judged by V1-V5 and V6. If V1 and V2 hold but V5 fails: **TRADES TIME FOR SAFETY** (with the numbers). W1 is reported and does not decide.

## Limits stated in advance

The confirm reading is answered from the handler's state at the catalogue's placeholder rates (0.92 against 0.10); a real walk to an air handler may be answered less cleanly, and the 19 minutes is a catalogue number. The simulation reads a room's own checks from the room's own cause (an own-fault room reads normal static at its own box). Fan-off complaint counts and visit shapes are mine. Nothing is validated against real outcomes.
