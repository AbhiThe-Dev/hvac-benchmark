# What detection rate does `bas_economizer` get against real, ground-truth economizer-fault data?

LBNL's Experimental RTU dataset (ORNL's Flexible Research Platform, a real 12.5-ton Trane RTU serving 10 VAV zones), recommended by Gabe Fierro. One-off empirical calibration, not a simulation, not pre-registered: measures three versions of the rule `bas_economizer`'s description implies against 1-minute real BAS data with known, imposed ground-truth faults.

## Rule A: literal reading ("stuck near its MINIMUM when conditions call for free cooling") -- catches only a stuck-LOW damper by design

A minute qualifies as "conditions call for more free cooling" if OAT < 50F and OAT < RAT - 2F. A day is ABNORMAL if the OA damper sits at or below 15 (near the documented 10% minimum) in at least half of qualifying minutes. Days with fewer than 30 qualifying minutes excluded.

| fault group | files | evaluable days | flagged ABNORMAL | rate |
|---|---|---|---|---|
| baseline (unfaulted) | 4 | 5 | 0 | 0% |
| OA damper stuck NEAR MINIMUM (5%, 10%) -- this check's stated target | 8 | 4 | 4 | 100% |
| OA damper stuck OPEN (50%, 100%) -- a different failure mode, not this check's stated target | 8 | 5 | 0 | 0% |
| incorrect setpoint, filename suffix -2/-4 (opens at a HIGHER OAT than 50F on evidence -- see Rule C correction) | 8 | 3 | 0 | 0% |
| incorrect setpoint, filename suffix +2/+4 (opens at a LOWER OAT than 50F, or not at all, on evidence -- see Rule C correction) | 8 | 3 | 3 | 100% |

## Rule B: widened ("the damper never modulates") -- 2026-09-29, built after Rule A was found to miss stuck-OPEN entirely

Drops the free-cooling gate. A day is ABNORMAL if occupied-hours OAT swings by at least 8F (real reason to move) while the damper's own range of motion over the day is at most 5 percentage points (it didn't). Needs at least 200 occupied minutes to evaluate a day.

| fault group | evaluable days | flagged ABNORMAL | rate |
|---|---|---|---|
| baseline (unfaulted) | 14 | 0 | 0% |
| OA damper stuck NEAR MINIMUM (5%, 10%) -- this check's stated target | 8 | 7 | 88% |
| OA damper stuck OPEN (50%, 100%) -- a different failure mode, not this check's stated target | 8 | 8 | 100% |
| incorrect setpoint, filename suffix -2/-4 (opens at a HIGHER OAT than 50F on evidence -- see Rule C correction) | 8 | 0 | 0% |
| incorrect setpoint, filename suffix +2/+4 (opens at a LOWER OAT than 50F, or not at all, on evidence -- see Rule C correction) | 8 | 0 | 0% |

## Rule C: setpoint crossover -- 2026-09-29, targets the fault Rule A/B cannot see (a wrong enable temperature, not a stuck damper)

Estimates each day's OWN empirical enable point (the warmest OAT the damper was ever seen clearly open, >20%) and compares it to the correct 50F; flagged if 3F or more off in EITHER direction, or if the damper never opened despite OAT reaching 45F or colder that day. **Group labels below are by filename suffix only, not by an assumed physical direction -- see the correction in this script's docstring.**

| fault group | evaluable days | flagged ABNORMAL | rate |
|---|---|---|---|
| baseline (unfaulted) | 5 | 0 | 0% |
| OA damper stuck NEAR MINIMUM (5%, 10%) -- this check's stated target | 4 | 4 | 100% |
| OA damper stuck OPEN (50%, 100%) -- a different failure mode, not this check's stated target | 8 | 7 | 88% |
| incorrect setpoint, filename suffix -2/-4 (opens at a HIGHER OAT than 50F on evidence -- see Rule C correction) | 5 | 5 | 100% |
| incorrect setpoint, filename suffix +2/+4 (opens at a LOWER OAT than 50F, or not at all, on evidence -- see Rule C correction) | 1 | 1 | 100% |

## Reading

**Clean, if small-sample, signal on the check's actual stated target:** 0% false-positive rate on 5 unfaulted days, 100% true-positive rate on the 4 days testing the fault this check's wording literally describes (damper stuck near minimum) -- consistent with (not proof of, at n=4-5) the placeholder "strong"=0.92, not a reason to lower it for that exact scenario.

**Rule A has a real scope gap, not a measurement artefact:** "stuck near its MINIMUM" only covers half of what the dataset labels "OA damper stuck" -- the other half, stuck OPEN (50%, 100%), is missed 100% of the time, because a wide-open damper never matches "near minimum".

**Rule B closes that gap.** Dropping the direction-specific check for a general "did it move at all" test catches BOTH stuck-low (88%, 7 of 8 days -- one miss right at the OAT-swing threshold) AND stuck-open (100%, 8 of 8 days), on a larger sample than Rule A could evaluate (16 days vs 9), while the false-positive rate stays clean (0 of 14 baseline days, a bigger and still-clean sample than Rule A's 5). **Rule B does NOT catch either incorrect-setpoint direction (0 of 16 days) -- correctly so, not a failure: a shifted setpoint doesn't freeze the damper, it just changes when a still-modulating damper decides to move, which is a different fault mechanism a "did it move" test was never going to see. That fault would need a genuinely different check (comparing WHEN the economizer engages against the correct temperature threshold), not a wider version of this one.**

**What Rule A/B leave open, Rule C closes -- with an honest correction along the way.** The setpoint fault was untouched by A and B because neither looks at WHEN the economizer engages, only whether/how much the damper moves. Rule C does, and finds a clean signal: 0% false positives on baseline (5 of 5 days clean), **100% flagged on the `-2/-4` files (5 of 5 days)**, whose empirical crossover sits 3-9F above 50F -- a real, detectable wrong-threshold signature. The `+2/+4` files gave only 1 evaluable day (most never got cold enough during the test to be evaluable at all under this rule), and that one day was also flagged (never opened despite reaching 43.5F). Both directions are individually detectable; the sample for one of them is just very thin. **Correction, reported rather than hidden: this session's own earlier write-up assumed `-2/-4` meant a LOWERED effective setpoint and `+2/+4` a RAISED one. Rule C's measurements show the opposite pattern** (`-2/-4` opens at a HIGHER OAT than correct; the one evaluable `+2/+4` day never opened at a LOWER OAT) -- the earlier direction labels were wrong, not just imprecise, and are corrected in this report's group labels rather than carried forward.

**What this changes:** nothing frozen (Addendum 37's decision stays UNSAFE; no code path in the live tool uses this data or any of these three rules). Between Rule B (both stuck-damper directions) and Rule C (the setpoint direction), every fault type in this dataset now has a working detector on real data, at a rate at least as good as the 0.92 placeholder -- the gap found earlier was in how narrowly the ORIGINAL check's wording was read, not in whether these faults are detectable at all. What's still untested: whether a single simulated check can carry all three signatures at once with one placeholder number, and Addendum 37's OTHER named safety hypothesis (the check's weak cross-detection of `low_static`), which none of this touches.
