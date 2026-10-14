# Two more "do not commit to one number" changes (EXPLORATORY; written and hashed before any run; the demos, the pilot and the shipped defaults are not touched)

## Question

The severity mixture (mixed) won by letting the data pick how many rooms a low-static handler starves, instead of fixing 50%. Two relatives, tested together because both cost no minutes:

1. **Fan-off mixture** (`JointSettings.fan_mix`, new, off by default): the model fixes 90% of the rooms of a fan-off handler as complaining. With 4 complaints on a 49-room handler the prior of fan off is 7e-42 (34 rooms: 7e-27; 86 rooms: 7e-79), so it can never be considered, the way low static could not (5e-11 shipped). On the first demo's 8-room handler, fan off with 2 of 8 rooms complaining was 0% right and called low static with 93% confidence. The change replaces `r_fan` by the same four levels as the low-static mixture: 5%, 15%, 50%, 90%, weight 1/4 each, sharing fan off's checks and cause.
2. **A lower end for the low-static mixture**: the lowest level is 5% and the bldg15 scenario complains 4 of 86 rooms (4.7%). Adding a 2% level (levels 2, 5, 15, 50, 90%, weight 1/5 each) raises the prior of low static there from 0.38% to 0.91% (4 of 8 rooms: 95.1% to 93.9%). Hypothesis (untested, mine): this is why bldg15's win was 75% against 81-84% on the other two buildings.

## Arms (the tool's setting; the routine is `tool_ticket_memo2` through the replica `study_folding.run_ticket_v(..., "base")`, T3-noattr, `min_rate` 0.02, each building's own check list)

- TODAY: `JointSettings(low_mix=MIX)`, MIX = 5/15/50/90% x 1/4 (the pilot and demo default).
- FAN: `JointSettings(low_mix=MIX, fan_mix=MIX)`.
- LOW2: `JointSettings(low_mix=MIX2)`, MIX2 = 2/5/15/50/90% x 1/5.
- BOTH: `JointSettings(low_mix=MIX2, fan_mix=MIX)`.
Levels and weights are fixed here, before any run, and are not tuned afterwards. Answers: W0 (checks as the tool assumes) and W1 (every rate 25% toward 0.5), the same oracle as the earlier studies.

## Visit families (all simulated; I wrote them, so a win says the change helps where the world varies as I drew it, not that real buildings do)

Real Mortar layouts (bldg11, bldg15, bldg9; recorded points only), 200 visits each, the restricted demo-shaped draw of `study_second.demo_visit`:
- **A-LS**: 4 rooms low static on the larger handler, 1 failed actuator and 1 wrong documented box on the other handler (identical to the earlier study).
- **A-FAN**: the same visits and rooms, but the 4 shared rooms have cause fan off and the larger handler's state is fan off (4 of 49, 4 of 86, 4 of 70 rooms complain).
- **B** (bldg15 and bldg11, 100 visits each): the registered composition `study_mix.draw_visit_g` (50 visits with 3-5 low-static rooms on the largest handler plus own-fault rooms anywhere, 50 with no shared cause).

The first demo's synthetic building (3 handlers x 8 rooms, Room-0..7 on AHU-0, Room-8..15 on AHU-1; the demo's configuration with `reheat=yes` as in `study_first_demo.py`), 100 visits per composition:
- **S1 fan off, the model's own world**: AHU-0 fan off, each of its 8 rooms complains with probability 0.9 (drawn per room; redrawn until at least 3 complain); only fan-off complaints.
- **S2 fan off, partial**: AHU-0 fan off, k = 2, 3 or 4 of its rooms complain (cycled by visit), plus 2 own-fault rooms on AHU-1.
- **S3 low static** (harm check): AHU-0 low static, k = 2, 3 or 4 rooms complain, plus 2 own-fault rooms on AHU-1.
- **S4 local only** (harm check): 6 distinct rooms anywhere, each with its own fault, no shared cause.
Own faults are drawn like the earlier studies (11 local causes equally likely, 10% documented box wrong, of which 10% unlisted).

## Measures (per room unless stated)

Accuracy (the guess equals the true cause); accuracy of the shared rooms and of the own-fault rooms separately; what the shared rooms of A-FAN, S1 and S2 were called when wrong (low static / other); minutes per visit; wrong-and-confident (wrong and concluded) and the same with the pilot's low-static hedge; **false fan-off rate** (rooms whose guess is fan off while the truth is not). Paired bootstrap over visits (2000), arm minus TODAY.

## Gates (a failed gate = NO RESULT)

- G1: TODAY on A-LS reproduces the stored mixed rows of `results/docmismatch/second_scenario/report.md` exactly (accuracy to one decimal, minutes to a whole number): bldg11 W0 84.4% / 188, W1 60.9% / 205; bldg15 W0 75.2% / 239, W1 48.5% / 245; bldg9 W0 81.1% / 207, W1 51.0% / 237.
- G2: `fan_mix=((0.9, 1.0),)` gives TODAY's guesses, conclusions and minutes exactly on 30 visits x 2 worlds drawn from the families.
- G3: every visit is composed as stated above (counts, handlers, causes, states).
- G4: every answer is in the check's vocabulary (asserted by the oracle) and the oracle's answers do not depend on the order of the questions (one A-FAN visit asked forward and backward).
- G5: the prior of fan off at 4 complaints of 49 rooms is below 1e-30 under TODAY and above 3e-3 under FAN (read from the model before any visit).

## Predictions (before any run; W0 unless stated; thresholds are per room, percentage points)

FAN (fan-off mixture)
- P1: A-FAN: under TODAY the 4 fan-off rooms are right at most 20% of the time on each of the three buildings (the blind spot).
- P2: A-FAN: FAN raises the fan-off rooms by at least 25 points on each of the three buildings.
- P3: S2: under TODAY the fan-off rooms are right at most 20% of the time and FAN raises them by at least 25 points.
- P4: S1 (the model's own world): FAN is within 3 points of TODAY on accuracy and within 5% on minutes.
- P5: harm checks (A-LS on three buildings, S3, S4, B on bldg15 and bldg11): in every one of those cells FAN is within 3 points of TODAY, its wrong-and-confident rate at most 1 point above TODAY's, and its false fan-off rate at most 2% of rooms.
- P6: at W1 the gains of P2 and P3 are still at least 15 points.

LOW2 (lower end)
- P7: A-LS, bldg15: LOW2 raises accuracy by at least 3 points (95% CI above 0), and the 4 shared rooms reach at least 85% (TODAY 78.8%).
- P8: A-LS, bldg11 and bldg9: LOW2 within 3 points of TODAY.
- P9: S1-S4: LOW2 within 3 points of TODAY in each composition.
- P10: B (bldg15, bldg11): LOW2 within 3 points of TODAY and its wrong-and-confident rate at most 1 point above TODAY's.

Combination
- P11: BOTH is not more than 2 points below the better single change in A-FAN (all three buildings) or in A-LS bldg15.

## Decision rule (set now)

FAN is **worth adopting** only if P2, P3, P4 and P5 all hold (gain where it should, neutral where the single number was right, no harm). LOW2 is **worth adopting** only if P7 holds and P8, P9 and P10 hold. If a target gain fails the label is NO GAIN; if a harm check fails it is TRADES (and says where). With eight or more cells compared, a single borderline cell is not an adoption argument; the CIs are reported. W1 is reported but does not decide.

## Limits stated in advance

The fan-off complaint counts (4 rooms of 49-86, 2-4 of 8) are my choice, as is the visit shape; if real fan-off failures hit nearly every room the single 90% is already right and FAN can only be neutral. Fan off and low static are told apart by the air handler's own readings, which in this simulation come from the catalogue's placeholder rates. Nothing is validated against real outcomes.
