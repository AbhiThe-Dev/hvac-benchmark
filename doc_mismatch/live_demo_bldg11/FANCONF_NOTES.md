# Three open items from the fan-off and lower-end studies (EXPLORATORY; written and hashed before any run; the demos, the pilot and the shipped defaults are not touched)

## Questions

1. **Fan-off confirm step.** The fan-off mixture (FANMIX_NOTES.md) closed the fan-off blind spot but called 4-6% of low-static rooms fan off. `bas_static`, `static_at_box` and `ahu_gauge` read the same 0.92 under fan off and low static; only `bas_ahu_fan` (0.92 vs 0.20) and `ahu_visit` (0.92 vs 0.10) separate them. Does requiring the fan-status read (`bas_ahu_fan`, a BAS look) before a room's leading cause is an upstream one (fan off or low static) remove most of the false fan-off calls and keep most of the fan-off gain, for little time? The reading, once taken, is carried to the later rooms of that handler exactly as the routine already carries any air-handler reading, so the cost is at most one BAS read per faulty-looking handler per visit.
2. **Lower-end gaps.** (a) The 2/5/15/50/90% low-static mixture (LOW2) also cut every other level's weight from 25% to 20%. Is its gain from the new 2% level or just from more weight on low levels? (b) LOW2 raised wrong-and-confident on fan-off visits in the FANMIX study (bldg15 8.1% to 16.5%, bldg9 13.2% to 17.5%) but that was seen in an unregistered column; register it.
3. **Hedge coverage.** The pilot hedge covers low-static conclusions only (a concluded low-static conclusion with no own box-level static reading of minutes > 0 is not confident). Extended to fan off: a concluded fan-off conclusion with no own box-level static reading is not confident either. How much of the wrong-and-confident share does that remove, and how many right conclusions does it hedge? Only matters once the fan-off mixture is used (without it fan-off conclusions are rare; fan-off rooms are called low static, which the existing hedge already covers).

## Arms (the routine is `tool_ticket_memo2` through the replica `study_folding.run_ticket_v(..., "base")`, T3-noattr, `min_rate` 0.02, each building's own check list)

- TODAY: `low_mix` 5/15/50/90% x 1/4 (the pilot and demo default). FAN: TODAY + `fan_mix` 5/15/50/90% x 1/4.
- **FANC**: FAN, plus the confirm step: after a room's own checks, if its leading cause is fan off or low static and `bas_ahu_fan` has not been answered for its handler in this visit (and is available), take it once, record it as the room's own check, carry it to later rooms on that handler like any air-handler reading, and let the room continue (the routine's loop) before concluding.
- **LOW2**: `low_mix` 2/5/15/50/90% x 1/5. **RW** (reweighting only): `low_mix` ((0.05, 0.4), (0.15, 0.2), (0.5, 0.2), (0.9, 0.2)): LOW2's weights with the 2% level's 20% moved onto the 5% level, so no new level, only more weight on the low end.

## Visit families (as FANMIX_NOTES.md: simulated, mine; W0 = checks as the tool assumes, W1 = every rate 25% toward 0.5)

A-LS (200 visits each; bldg11, bldg15, bldg9), A-FAN (200 each), B (100 each; bldg15, bldg11), S1-S4 on the first demo's 3 x 8 building (100 each). Same draws as the FANMIX study.

## Measures (per room unless stated)

Accuracy; shared-cause rooms; minutes per visit; wrong-and-confident raw; with the existing hedge (low static); with the hedge extended to fan off; share of right conclusions hedged; false fan-off rate (guess fan off, truth not); fan-off rooms right. Paired bootstrap over visits (2000).

## Gates (a failed gate = NO RESULT)

- G1: the shared arms reproduce the FANMIX study exactly (accuracy to one decimal, minutes to a whole number, W0): TODAY on A-LS (bldg11 84.4/188, bldg15 75.2/239, bldg9 81.1/207); FAN on A-LS (79.2/195, 71.2/227, 77.8/209) and on A-FAN (80.4/178, 72.7/214, 78.0/199); LOW2 on A-LS (84.3/186, 78.3/214, 82.8/197).
- G2: the confirm replica with the confirm step switched off equals `run_ticket_v` exactly (guesses, conclusions, minutes) on 40 visit-world runs.
- G3: composition as stated (FANMIX gate). G4: answers in vocabulary (asserted) and order-independent oracle.
- G5: in every visit the confirm step asks `bas_ahu_fan` at most once per handler, and never when it was already answered for that handler.

## Predictions (before any run; W0; points are percentage points per room)

Fan confirm (FANC)
- C1: A-LS on each building: FANC's false fan-off rate is at most 2% and its accuracy within 3 points of TODAY.
- C2: A-FAN on each building: FANC's accuracy on the fan-off rooms is at least 80% of FAN's.
- C3: B (bldg15, bldg11), S3, S4: FANC within 2 points of TODAY on accuracy and its wrong-and-confident at most 1 point above TODAY's.
- C4: S1 (the model's own world): FANC within 3 points of TODAY on accuracy.
- C5: minutes per visit under FANC within +5% of TODAY in A-LS (3) and B (2).
Lower end
- L1: RW captures at least half of LOW2's accuracy gain over TODAY on A-LS bldg15 (my guess is that most of it is reweighting).
- L2: A-FAN, bldg15 and bldg9: LOW2's wrong-and-confident (raw) is at least 3 points above TODAY's, and RW's rise is smaller than LOW2's on both.
Hedge
- H1: under FAN, over A-FAN (3), S1, S2, A-LS (3), B (2): the extended hedge cuts wrong-and-confident-with-hedge by at least half in every cell where the current hedge leaves at least 1%, and hedges at most 30% of right conclusions pooled over those cells.

## Decision rule (set now)

FANC is **worth adopting alongside the fan-off mixture** only if C1-C5 all hold. The hedge extension is **worth adding if the fan-off mixture is adopted** only if H1 holds. The lower-end items are reported against L1 and L2 and decide nothing alone. W1 is reported and does not decide.

## Limits stated in advance

The simulation reads a room's own checks from the room's own cause, so an own-fault room reads NORMAL static at its own box and a fan-status read at the handler is answered from the handler's state: the confirm step is as informative here as the catalogue says (0.92 against 0.20), which is a placeholder. The harsh convention of the soft-copy post hoc (every box on a faulty handler reads like the handler) would weaken any hedge that treats an own box reading as verification; it is not rerun here. Nothing is validated against real outcomes.
