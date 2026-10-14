# 100-visit simulation of the bldg11 scenario (protocol, written 2026-10-11 BEFORE any simulated visit has run)

**Question.** On visits like the bldg11 demo scenario (six "too warm" complaints on two real air handlers, one of them with a possible shared low-static fault), how often is the tool's
diagnosis right, how often is it confidently wrong, and how long does it take, with noisy answers instead of the scripted ones? And does the "large-handler setting" (`r_low` 0.10) found while
building the demo hold up on visits it was not tuned on?

**What this is and is not.** A simulation: the layout and point map are real (Mortar bldg11 subset), everything else is drawn by me. Answers come from the catalogue's own response rates, so the
primary world is **home-field** for the tool (a good result is weak evidence, a bad one is strong); the degraded world is the stress. Nothing here is evidence about real technicians, real
faults, real response rates or real minutes (all placeholders). The stand-ins are my constructions. Not a validation.

**What has been seen before writing this (disclosure).** (1) The scripted demo visit under both model settings: shipped 2/6 right, 219 min; `r_low` 0.10 6/6, 119 min; a sweep of `r_low` on that one
visit (0.02-0.2 gives 6/6, 0.25 and above 2/6). So `r_low = 0.10` was chosen on a visit that the shared-cause visits below resemble: the "adjusted" arm is NOT independently validated by this
simulation on that axis; what is new is the local visits, the noise and the other causes. (2) Nothing of any simulated visit.

## The tool's inputs (identical to the demo, `visit.py`)
Tier T1 + control-system access + point map (no attributes); the real point map of AHU06 (49 boxes) and AHU05 (34 boxes) with no fan-status, controller-status or airflow-setpoint point
(`bas_ahu_fan` and `bas_controller` removed); candidates = the 7 nearest boxes by id (`nearness="id"`); drawings rated `mostly_right`; context declared (access yes, instrument yes, occupant no,
reheat yes); `min_rate` 0.02; `tau` 0.95. The tool arm is the ticket-by-ticket routine the demo runs (`run_ticket`, mode `memo2`, the prior from the joint model's marginals).

## The visits (frozen)
100 visits, seed 20261011, each with **six complaints on six distinct rooms**, in random arrival order. Rooms are drawn from ALL 83 rooms of the two air handlers (so boxes without a full point set
appear at their real share).
- **Shared visits (visits 0-49).** AHU06 is in `low_static`, AHU05 is fine. `k` rooms on AHU06 complain because of it (`k` = 3, 4, 5 cycling by visit number); their first-order cause is
  `low_static`. The other `6 - k` complaints are drawn uniformly from the remaining rooms of both air handlers and have a local cause.
- **Local visits (visits 50-99).** Both air handlers are fine. Six rooms drawn uniformly, each with a local cause. (The test that the tool does not invent a shared cause.)
- **A local cause.** With probability 0.10 the documented box is wrong: the true feeder is one of the documented box's 7 candidates (uniform), or with probability 0.10 of those it is not on
  the list (`unlisted`). Otherwise a leaf drawn **uniformly** over the 11 box-level causes `actuator_fail, damper_mech, no_power, signal_fault, controller_comms, controller_config,
  flow_sensor, zone_sensor_setpoint, duct_diffuser, capacity_design, reheat_fail` (uniform, not the tool's own prior shares: a deliberate mismatch). Not drawn: `other`, `ahu_fan_off`, `econ_fault`.
- **Answers.** Each answer is a draw from the catalogue's rate for that check under the true cause (air-handler checks: under the air handler's state), clipped to the rate floor, and is a pure
  function of (seed, visit, world, complaint room or air handler, check, target): the same question gets the same answer under every policy and in any order.
- **Two worlds.** W0: the catalogue's rates as the tool assumes them (home-field). W1: every response probability moved 25% toward 0.5 (`degrade_all`, a = 0.25): the tool is more confident than
  its checks deserve.

## Policies (the same 100 visits and answers for each; paired)
`tool_shipped` (`JointSettings()`, `r_low` 0.5); `tool_adjusted` (`r_low` 0.10); `fast_ticket` and `fast_parent`, the two stand-in technicians of Addendum 30 (assumed habits: cheapest check that
names one cause, first abnormal reading concludes; `fast_parent` reads an air handler first when two or more complaints sit on it). **Secondary, exploratory, no verdict:** `tool_r0.25` and
`tool_r0.05` (the tool with those `r_low` values) to show how the setting trades off.

## Metrics (per complaint unless stated; 95% intervals from a bootstrap over visits, 2000 resamples)
M1 **accuracy**: the leading cause equals the true cause exactly (a wrong box counts only if it names the true box). M2 **wrong-and-confident**: the policy concluded and was wrong (the stand-ins
always conclude). M3 **not concluded** (tool only). M4 **minutes** per visit (the tool's placeholder minutes, all policies charged by the tool's own accounting). M5 **false shared-cause call**:
a complaint whose true cause is not `low_static` that is diagnosed `low_static`. Reported overall and by segment: shared-cause complaints; local complaints in shared visits; local
complaints in local visits; documentation-wrong complaints. Paired differences with intervals.

## Predictions (written now; each is reported as holds / does not hold)
- **P1.** At W0, `tool_adjusted` accuracy exceeds `tool_shipped` by at least 15 points overall, with the interval's lower bound above 0.
- **P2.** At W0 on shared-cause complaints, `tool_shipped` accuracy is below 30% and `tool_adjusted` above 80%.
- **P3.** At W0, `tool_adjusted`'s false shared-cause call rate is at most 3% of non-`low_static` complaints.
- **P4 (the safety bar).** `tool_adjusted` wrong-and-confident is at most 5% at W0 and at most 10% at W1. A failure is reported as UNSAFE, whatever the speed.
- **P5.** `tool_adjusted` accuracy at W1 is lower than at W0 by at least 3 points.
- **P6.** At W0, `tool_adjusted` mean visit minutes are below `fast_ticket`'s. (No prediction about `fast_parent`: I do not know.)
- **P7.** At W0, `tool_adjusted` overall accuracy lies between 65% and 90%.

## Gates (a failed gate means NO RESULT)
G1 the harness reproduces the demo: with the demo's deterministic scripted answers, `run_ticket` mode `memo2` gives the same per-complaint guesses and total minutes as the demo for both settings
(119.0 and 219.0 minutes). G2 determinism: an answer is the same when asked twice and in a different order, and two runs give identical summaries. G3 composition: every visit has six distinct rooms,
shared visits have `k` in {3, 4, 5} low-static complaints all on AHU06 and local visits have none. G4 completeness: 100 visits x 2 worlds x all policies, finite minutes. G5 every answer drawn lies in
the check's own vocabulary.

## Limitations named up front
100 visits (600 complaints) resolve accuracy differences of roughly 8 points, not less; rare outcomes (confidently wrong at 1-2%) are barely resolvable. The visit mix (50/50 shared, `k` 3-5,
10% wrong documentation, uniform local causes) is mine and every headline number depends on it; I report segments so it can be re-weighted. Home-field answers at W0. `r_low = 0.10` was chosen on a
visit these resemble. One building, two air handlers, no fan-off or economizer visits, no causes outside the catalogue, no second fault on one complaint. Minutes are placeholders.

## What would follow
P4 fails: the setting is not safe to ship, regardless of accuracy. P1/P2 fail: the demo's result was an artefact of the one scripted visit. All hold: the setting is a candidate for the 18-cell
treatment of the earlier addenda (and for a real assumption about `r_low`), not a result.
