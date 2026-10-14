# Selective verification of rooms on a faulty handler ("folding" fix): protocol (EXPLORATORY; written and hashed before any variant was run)

## Question

In the demo's routine a room whose handler has been found low-static inherits that finding at zero minutes and concludes "low static" without checking anything at its own box. A room with its OWN fault on that handler is
then named as the shared cause ("folding": on the registered 100 bldg11 visits, 57 rooms on the faulty handler scored 3.5%, 52 of them called low static). Verifying every such room costs about 14 minutes each and mostly
lands on rooms that were already right. **Can a selective verification recover most of the accuracy for a fraction of the time?**

## Visits, worlds, setting (the same as the registered runs)

The same 100 visits (`simulate.draw_visit`, v = 0..99; 50 shared visits with 3 to 5 shared rooms on AHU06 plus local rooms, 50 all-local visits; 6 complaints each), the same noisy oracle (a pure function of seed, visit, world,
who, check, target), worlds W0 (checks as the tool assumes) and W1 (every rate 25% toward 0.5; the tool still assumes W0), the demo's default setting: the mixed-severity joint model (`low_mix`), `min_rate` 0.02, T3-noattr.

## Variants (fixed now)

All variants are the routine `tool_ticket_memo2` with one change: **after a room's session ends with low static as its leading cause, and the room has taken no box-level static reading of its own,** a verification step is added
and the session then continues under its normal rules (`min_rate`, `tau`, the 12-check cap). Variants that verify also stop copying one room's box-level static reading into the other rooms of the handler (that copy, "group informing", would
otherwise count as the verification).

| variant | the verification step |
|---|---|
| base | none (the routine as the demo runs it) |
| V1 verify all, box static | every such room takes the inlet-static reading at its own box (`static_at_box`, 14 minutes with the standard fallback) |
| V2 verify all, best per minute | every such room takes the one check with the best expected gain per minute (`Session.shortlist()['next']`, which ignores `min_rate`), cheap checks first |
| V3 verify two, box static | as V1, but at most two rooms per faulty handler per visit, in arrival order |
| V4 verify two, best per minute | as V2, at most two rooms per faulty handler per visit |

## Measures (fixed now)

Per room: right or wrong (leading cause equals the true cause), concluded, minutes. Reported overall and by segment: shared-cause rooms; own-fault rooms on the faulty handler; own-fault rooms on the healthy handler
in shared visits; own-fault rooms in visits with no shared cause. Per visit: minutes, checks. **Minutes added by segment**, paired against base (same room, same visit): how much of a variant's added time lands on rooms that base already had right.
Wrong-and-confident share (wrong and concluded). Paired bootstrap over visits (2000 resamples) for differences against base.

## Gates (a failed gate = NO RESULT)

- G1: the replica of the routine with no verification equals `run_policy("tool_ticket_memo2")` exactly (guesses, conclusions, minutes) on all 100 visits in both worlds.
- G2: the base accuracy equals the mixture study's stored `bldg11|W0|mix` and `bldg11|W1|mix` accuracies (0.2 points).
- G3: every answer is in the check's vocabulary; every forced check was available (a variant that cannot take its check skips it and counts the skip).

## Decision rule (fixed now)

A variant is **WORTH IT** at W0 when all four hold: overall accuracy gain at least 3 points with a paired 95% interval excluding 0; added minutes at most 15% of base; added minutes buy at least 0.3 accuracy points per minute (the generic
"take more checks" rate measured earlier was 0.2); wrong-and-confident not higher than base by more than 1 point. **TRADE** if the accuracy gain holds but the time or rate bar fails. **NEITHER** otherwise.
The W1 results are reported next to it and are not part of the verdict.

## Convention of the simulation that flatters verification (stated, not corrected)

The oracle answers a room-level check from that room's OWN first-order cause (the world's rule: a room is affected by the upstream fault or has its own fault, not both). So a room with its own fault on a low-static
handler reads "normal" at its box. In a real building such a room would also read low static (the whole handler is low), and the box reading would confirm "low static" without separating the two. The measured gain is therefore an upper bound on what
box-level verification can do.

## Predictions (made before the first variant ran)

- P1: V1 raises W0 accuracy by 4 to 8 points, raises the 57-room own-fault-on-faulty-handler segment from about 4% to at least 50%, and adds 25 to 45 minutes per visit.
- P2: at least 60% of V1's added minutes land on rooms that base already had right.
- P3: V2 gains less accuracy than V1 and its gain per added minute is below 0.3 (cheap checks cannot separate low static from the look-alikes).
- P4: V3 gets between 30% and 70% of V1's accuracy gain for between 30% and 70% of its added minutes (a budget is linear, not selective).
- P5: no variant is WORTH IT.
- P6: no variant lifts W0 overall accuracy above 85%.
- P7: at W1 every variant's gain is smaller than at W0.
