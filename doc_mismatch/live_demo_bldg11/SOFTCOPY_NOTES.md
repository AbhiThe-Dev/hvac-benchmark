# A softer copy between rooms (EXPLORATORY; written and hashed before any run; the demos, the pilot and the shipped defaults are not touched)

## Question

Today's routine (`tool_ticket_memo2`) shares what it learns about an air handler between rooms by COPYING it into each later room as if that room had been measured, at zero minutes: every air-handler reading already taken is entered in the room's log with its answer, and once any room's own box read abnormal static, every later room on that handler gets "static at its own box: abnormal". Those copies are certain (the answer is the room's own, as far as the model can tell), so a room that has a fault of its own but sits on a faulty handler is pushed to "low static" by a likelihood ratio of about 23 and can rarely argue back. In the error study 38 of 43 folded errors involved such a copy; folded rooms were 34% of all errors. The question: does replacing the certain copy by the joint model's own soft belief (the room is probably affected, with the chance of an own fault kept in proportion to how many rooms the handler's fault is starving) help folded rooms without costing time or accuracy elsewhere?

## The two soft arms (HARD = today's routine, `study_folding.run_ticket_v(..., "base")`, unchanged)

All arms use T3-noattr, `min_rate` 0.02, the severity mixture 5/15/50/90% x 1/4 (today's default), each building's own check list, no fan-off mixture (it was not adopted).

- **SOFT**: the joint model keeps a running state of everything answered in the visit (every air-handler reading, and every room check, as `JointModel.apply` does: the handler's states are re-weighted, the room's causes are re-weighted). When a room's turn comes its starting belief is the joint marginal for that room given everything so far, instead of the plain starting belief plus copies. No answer is copied into a room's log as a measurement: an air-handler check already answered is entered as "unsure" (no likelihood, but it is not asked again), and static at the room's own box stays available as a check the room can choose. A room counts as informed (may conclude without a check of its own) once a real reading that bears on its handler has been taken by anyone (any air-handler check, or static at any box: `bears_on_ahu`), as in the joint model's group-informing rule. Inside a room the session is v1's, unchanged (an air-handler check the room itself asks is applied to its own causes directly).
- **JOINT**: SOFT, and the room's belief throughout its own session is the joint marginal, so even an air-handler check asked by the room itself enters through the handler (with the own-fault chance kept) and not directly on the room's causes.

## Visit families (simulated; the world is mine; same generators as FANMIX_NOTES.md unless stated; W0 = checks as the tool assumes, W1 = every rate 25% toward 0.5)

Real layouts bldg11, bldg15, bldg9: **A-LS** (200 visits each; 4 low-static rooms on the larger handler + 2 own-fault rooms on the other; no folding), **B** (100 visits each; the registered composition: half the visits have 3-5 low-static rooms on the largest handler plus own-fault rooms anywhere, so some own-fault rooms sit on the faulty handler = the folding case; half have no shared cause), **A-FAN** (200 visits each; 4 fan-off rooms; harm check: today's setting cannot see fan off, so nothing should change).
The first demo's synthetic building, 100 visits each: **S1** fan off hitting each of 8 rooms at 90%; **S2** fan off with 2-4 of 8 complaining + 2 own-fault rooms on AHU-1; **S3** low static, 2-4 of 8 + 2 own-fault rooms on AHU-1; **S4** 6 own-fault rooms, no shared cause; **S5 (new, folding on a small handler)**: AHU-0 low static, k = 2 or 3 (cycled by visit) low-static rooms plus exactly 2 own-fault rooms, all four or five on AHU-0 (drawn like the other own faults).

## Measures (per room unless stated)

Accuracy; shared-cause rooms; own-fault rooms elsewhere; **folded rooms** (an own-fault room on a handler whose state is faulty); minutes per visit; wrong-and-confident (wrong and concluded) with and without the pilot's low-static hedge (a concluded low-static conclusion with no own box-level static reading of minutes > 0); share of folded rooms called low static. Paired bootstrap over visits (2000), arm minus HARD.

## Gates (a failed gate = NO RESULT)

- G1: HARD on A-LS reproduces the stored mixed rows (accuracy to one decimal, minutes to a whole number) as in FANMIX_NOTES.md G1.
- G2: SOFT equals HARD exactly (guesses, conclusions, minutes) on single-complaint visits (the first room of 40 visits drawn from A-LS, B and S3, both worlds): with no earlier room there is nothing to copy.
- G3: every visit is composed as stated (as FANMIX_NOTES.md G3; S5 as above).
- G4: answers in the check's vocabulary (asserted) and the oracle does not depend on the order of questions.
- G5: for every room that asked no air-handler check itself, in 30 visits per arm and world, SOFT's own session belief equals the joint model's marginal for that room to 1e-9 (the claim behind "the soft copy is the joint belief").

## Predictions (before any run; W0; points are percentage points per room)

- Q1 (folded rooms, B): SOFT raises the accuracy of folded rooms by at least 15 points pooled over the three buildings and at least 10 on each.
- Q2 (folded rooms, S5): SOFT raises them by at least 15 points.
- Q3 (no accuracy harm): overall accuracy under SOFT is not more than 2 points below HARD in any of B (3), A-LS (3), S3, S4, S5.
- Q4 (time): minutes per visit under SOFT within +10% of HARD in each of B (3) and A-LS (3).
- Q5 (confident errors): wrong-and-confident (raw) under SOFT at most 1 point above HARD in every cell of Q3, and at least 2 points below it in B on bldg11 (HARD 6.8% earlier).
- Q6 (fan-off families A-FAN x3, S1, S2): SOFT within 3 points of HARD.
- Q7 (A-LS): the 4 shared rooms within 3 points of HARD on each building.
- Q8: JOINT within 2 points of SOFT on overall accuracy in B on each building.

## Decision rule (set now)

SOFT is **worth adopting** only if Q1, Q2, Q3, Q4 and Q5 all hold. If Q1 and Q2 hold but Q4 fails: **TRADES ACCURACY FOR TIME** (with the numbers). If Q1 or Q2 fails: **NO GAIN**. If Q1 and Q2 hold and Q3 or Q5 fails: **TRADES (a harm check failed)**. W1 is reported and does not decide. JOINT is judged by the same rule.

## Limits stated in advance

The simulation answers a room's own check from the room's own first-order cause, so an own-fault room on a low-static handler reads NORMAL static at its own box; in a real building it would probably read low static too (the handler starves its box whatever the room's own fault is). Verification by an own reading is therefore flattered here, and so is any gain that comes from rooms taking one: the folded-room gains are upper bounds. The replica is not a change to the shipped tool: nothing here is built into the demos or the pilot. Nothing is validated against real outcomes.
