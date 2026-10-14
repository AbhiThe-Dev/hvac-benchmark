# Task: design the decision tree you would actually follow on a VAV comfort call-out

You are a senior commercial HVAC service technician. Design the **branching decision tree (flowchart)** you would follow, from the moment you start, to find the root cause of a VAV-zone comfort complaint with as little wasted time as possible, and to avoid telling a customer the wrong cause. Use your own field experience: which checks you do first, what each result makes you do next, when you are confident enough to call the cause, and when you say "I can't pin it down, escalate". This is a *real expert's tree with branching*, not a flat checklist: later steps must depend on earlier results.

Do NOT use any tools, read any files, or search the web. Answer from your own knowledge and from this message only.

## The situation
- A building has several air handlers (AHUs). Each AHU feeds several VAV boxes; each VAV box serves one room. The drawings say which box serves which room and which AHU serves which box. The drawings are *mostly* right, but occasionally the documented box is not the one that actually serves the room (or the box's real AHU differs).
- A call-out has **one or more complaint rooms** ("the room is not getting the right airflow/temperature"), arriving together. You work them in the order given. You do not know whether a room is too hot or too cold, nor whether any air comes out of the diffuser (treat these as unknown).
- Every complaint has exactly ONE first-order root cause, chosen from the list below (or the drawings are wrong about which box serves the room: see `find_feeder`). Several complaints can share one cause when the cause is upstream (the air handler), or have separate local causes.
- You arrive with the equipment list and the drawings' claims. What else you have depends on the data tier your tree will be run under. **Your single tree will be run unchanged under three tiers**, so give ordered alternatives where a check may not be available:
  - **Tier A (full data):** control-system (BAS) access with a point map for every piece of equipment, plus nameplate/design data on file for every box and AHU.
  - **Tier B (BAS, no design data):** BAS access with a point map, but NO nameplate/design data on file (some checks cost extra minutes to look the data up, a few are impossible).
  - **Tier C (no BAS access):** no control-system access at all: physical checks only (some checks are impossible).
  - In every tier you carry a differential-pressure gauge/flow hood; no occupant is available to ask.
- Time: each check has a cost in minutes. **The "access" minutes are paid only if you are not already at that place** (places: at a laptop on the BAS; at the VAV box; in the air-handler room; in the room). Doing several checks at the same place saves the walking. A check that is impossible in a tier is "n/a" there.
- Checks are mostly right but not always: a reading can occasionally be wrong (a false alarm or a miss), more so for some checks than others. Use your judgment where a single reading would not convince you.
- Limits: at most 12 checks per complaint. A reading of the AHU is shared by every complaint on that AHU (it is only paid for once, and the same quantity read by another route counts: `bas_static` = `ahu_gauge`; `bas_ahu_fan` = `ahu_visit`).

## Root causes you can name (use these ids)
- `actuator_fail` (box_mechanical): Actuator failed or out of torque. gear stripped, motor burned out, or a fail-safe driving the damper the wrong way
- `damper_mech` (box_mechanical): Damper or linkage stuck or slipping. blade stuck (corrosion, debris, ice), linkage disconnected or slipping, travel limited by a stop or a misaligned coupling, poor seals
- `no_power` (power_and_signal): Actuator has no 24 VAC. blown fuse, tripped breaker or failed transformer
- `signal_fault` (power_and_signal): Control signal broken, shorted, inverted or the wrong range. no command reaches the actuator, or it acts the wrong way (0-10 V against 2-10 V)
- `controller_comms` (controls): VAV controller offline or faulted. offline, rebooting, in a fault state or alarming, so commands do not get through
- `controller_config` (controls): Controller set up wrongly. K-factor not the nameplate's, maximum airflow setpoint off the design value, minimum setpoint wrong, occupied and unoccupied swapped, poor loop tuning (hunting)
- `flow_sensor` (sensing): Flow sensor reads wrong. clogged ports, kinked, loose or swapped (high/low) tubes, transducer offset or drift [only boxes with pressure_independent]
- `zone_sensor_setpoint` (zone_inputs): Zone sensor, setpoint or schedule. sensor out of calibration, setpoint or occupancy schedule or mode wrong, an occupant override
- `ahu_fan_off` (upstream): Air handler fan off or tripped. supply fan stopped, VFD tripped
- `low_static` (upstream): Duct pressure too low upstream. static setpoint too low, degraded fan or belt, dirty filters, an upstream leak or blockage, many boxes calling for maximum
- `reheat_fail` (reheat): Reheat not working. valve stuck or leaking, coil fouled, electric element or connections damaged, no hot water [only boxes with reheat]
- `duct_diffuser` (distribution): Duct or diffuser problem between the box and the room. leaks or bypass, crushed or disconnected flex duct, diffuser or balancing damper blocked or closed
- `capacity_design` (capacity): Box or room capacity problem. box undersized for the room's current use, design airflow not enough, many boxes at maximum together
- `other` (other): Something else. the residual: nothing above explains it
- "documented box is wrong" (the drawings are wrong about which box serves the room): handled by the special leaf `find_feeder` (see below), not named as a cause.

## The checks you may use (use these ids exactly)
- `override_room` [v0 check; at the box you act on; applies to: the box/room itself] Command the documented box to full cooling and watch whether the temperature in the room responds
    - answer: YES = the room's temperature DOES respond (the box acts and feeds this room). NO = it does not respond.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 6, do 2, wait 30; full cost = 38 | 38 | 38  (access minutes are NOT paid again if you are already at that place)
- `override_diffuser` [v0 check; at the box you act on; applies to: the box/room itself] Command the documented box to full cooling and check whether airflow at the room's diffuser rises
    - answer: YES = airflow at the diffuser DOES rise. NO = it does not.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 6, do 2, wait 3; full cost = 11 | 11 | 11  (access minutes are NOT paid again if you are already at that place)
- `duct_trace` [v0 check; at the box you act on; applies to: the box/room itself] Trace the duct from the room's diffuser back to its box: is it the documented box?
    - answer: YES = the duct leads back to the DOCUMENTED box (the drawings are right). NO = it leads somewhere else.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 10, do 15, wait 0; full cost = 25 | 25 | 25  (access minutes are NOT paid again if you are already at that place)
- `confirm_acts` [v0 check; at the box you act on; applies to: the box/room itself] Command the documented box and confirm its damper actually moves
    - answer: YES = the damper DOES move when commanded. NO = it does not.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 6, do 3, wait 0; full cost = 9 | 9 | 9  (access minutes are NOT paid again if you are already at that place)
- `bas_ahu_fan` [control system; at a laptop on the control system; applies to: the AIR HANDLER (one reading speaks for every complaint on that AHU)] In the control system, read the supply fan status, speed and alarms of the air handler: is the fan off, tripped or in alarm?
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 0, do 2, wait 0; full cost = 2 | 2 | n/a  (access minutes are NOT paid again if you are already at that place)
- `bas_static` [control system; at a laptop on the control system; applies to: the AIR HANDLER (one reading speaks for every complaint on that AHU)] In the control system, read the duct static pressure of the air handler against its setpoint: is it low?
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 0, do 2, wait 0; full cost = 2 | 2 | n/a  (access minutes are NOT paid again if you are already at that place)
- `bas_controller` [control system; at a laptop on the control system; applies to: the box/room itself] In the control system, read the controller status and alarms of the documented box: is it offline, in a fault state or alarming?
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 0, do 2, wait 0; full cost = 2 | 2 | n/a  (access minutes are NOT paid again if you are already at that place)
- `bas_airflow` [control system; at a laptop on the control system; applies to: the box/room itself] In the control system, read the airflow setpoint and measured airflow of the documented box: does the measurement miss the setpoint by more than about 10%?
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 0, do 2, wait 0; full cost = 2 | 2 | n/a  (access minutes are NOT paid again if you are already at that place)
- `bas_damper` [control system; at a laptop on the control system; applies to: the box/room itself] In the control system, read the damper position of the documented box against its command: is it pinned at 100% while airflow is low, or not following its command?
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 0, do 2, wait 0; full cost = 2 | 2 | n/a  (access minutes are NOT paid again if you are already at that place)
- `bas_zone` [control system; at a laptop on the control system; applies to: the room/zone] In the control system, read the temperature, setpoint, occupancy schedule and mode of the room: is the setpoint, schedule or mode wrong for this room?
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 0, do 2, wait 0; full cost = 2 | 2 | n/a  (access minutes are NOT paid again if you are already at that place)
- `bas_reheat` [control system; at a laptop on the control system; applies to: the box/room itself] In the control system, read the reheat command and valve or stage position of the documented box: is heat called for but the valve or stage not responding? Only possible if the box has reheat.
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 0, do 2, wait 0; full cost = 2 | 2 | n/a  (access minutes are NOT paid again if you are already at that place)
- `bas_hunting` [control system; at a laptop on the control system; applies to: the box/room itself] In the control system, watch the damper and airflow of the documented box for about 5 minutes: do they keep swinging up and down?
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 0, do 2, wait 5; full cost = 7 | 7 | n/a  (access minutes are NOT paid again if you are already at that place)
- `power_24vac` [at the box; at the VAV box (above the ceiling); applies to: the box/room itself] At the documented box, measure the voltage at the actuator terminals: is it missing or outside 22 to 26 VAC?
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 6, do 4, wait 0; full cost = 10 | 10 | 10  (access minutes are NOT paid again if you are already at that place)
- `control_signal` [at the box; at the VAV box (above the ceiling); applies to: the box/room itself] With the documented box commanded open, measure the control signal at its actuator input: is it missing (under about 2 V on a 0-10 V actuator)?
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 6, do 4, wait 2; full cost = 12 | 12 | 12  (access minutes are NOT paid again if you are already at that place)
- `manual_damper_test` [at the box; at the VAV box (above the ceiling); applies to: the box/room itself] At the documented box, disconnect the actuator and turn the damper shaft by hand: is the damper stuck or binding?
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 6, do 8, wait 0; full cost = 14 | 14 | 14  (access minutes are NOT paid again if you are already at that place)
- `damper_linkage` [at the box; at the VAV box (above the ceiling); applies to: the box/room itself] At the documented box, inspect the damper linkage, seals and stops: is the linkage loose or slipping, or the damper not reaching fully open or fully closed?
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 6, do 10, wait 0; full cost = 16 | 16 | 16  (access minutes are NOT paid again if you are already at that place)
- `controller_leds` [at the box; at the VAV box (above the ceiling); applies to: the box/room itself] At the documented box, look at the controller status lights and event log: is it dead, showing a fault, or off the network?
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 6, do 3, wait 0; full cost = 9 | 9 | 9  (access minutes are NOT paid again if you are already at that place)
- `sensing_ports` [at the box; at the VAV box (above the ceiling); applies to: the box/room itself] At the documented box, inspect the flow-sensing ports and tubing: are ports clogged, or tubes kinked, loose or swapped (high and low)? Only possible if the box has pressure_independent.
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 6, do 10, wait 0; full cost = 16 | 16 | 16  (access minutes are NOT paid again if you are already at that place)
- `flow_vs_gauge` [at the box; at the VAV box (above the ceiling); applies to: the box/room itself] At the documented box, compare the controller's pressure reading with a gauge on its flow taps: do they disagree by more than about 10%? Only possible if the box has pressure_independent.
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 6, do 8, wait 0; full cost = 14 | 14 | n/a  (access minutes are NOT paid again if you are already at that place)
- `k_factor` [at the box; at the VAV box (above the ceiling); applies to: the box/room itself] Compare the K-factor programmed in the controller of the documented box with the value on its nameplate or submittal: do they differ? Only possible if the box has pressure_independent.
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 6, do 4, wait 0; full cost = 10 | 14 | n/a  (access minutes are NOT paid again if you are already at that place)
- `max_airflow` [at the box; at the VAV box (above the ceiling); applies to: the box/room itself] Compare the maximum airflow setpoint in the controller of the documented box with its design airflow: is it different?
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 0, do 4, wait 0; full cost = 4 | 12 | n/a  (access minutes are NOT paid again if you are already at that place)
- `static_at_box` [at the box; at the VAV box (above the ceiling); applies to: the box/room itself] At the documented box, measure the static pressure at the inlet: is it below the minimum for its size (about 0.25 to 0.5 in. w.c.)?
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 6, do 6, wait 0; full cost = 12 | 14 | 12  (access minutes are NOT paid again if you are already at that place)
- `reheat_coil` [at the box; at the VAV box (above the ceiling); applies to: the box/room itself] At the documented box, inspect the reheat coil and valve (or electric element and connections): is the valve stuck or leaking, the coil fouled, or a connection damaged? Only possible if the box has reheat.
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 6, do 10, wait 0; full cost = 16 | 16 | 16  (access minutes are NOT paid again if you are already at that place)
- `ahu_visit` [at the air handler; in the air-handler room; applies to: the AIR HANDLER (one reading speaks for every complaint on that AHU)] Go to the air handler: is the supply fan stopped, tripped or in fault?
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 15, do 4, wait 0; full cost = 19 | 19 | 19  (access minutes are NOT paid again if you are already at that place)
- `ahu_gauge` [at the air handler; in the air-handler room; applies to: the AIR HANDLER (one reading speaks for every complaint on that AHU)] At the air handler, read the duct static pressure gauge against its setpoint: is it low?
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 15, do 2, wait 0; full cost = 17 | 17 | 17  (access minutes are NOT paid again if you are already at that place)
- `flow_hood` [in the room; in the affected room; applies to: the room/zone] Measure airflow at the diffuser in the room with a flow hood: is it well off what the documented box should be delivering right now?
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 5, do 8, wait 0; full cost = 13 | 13 | 13  (access minutes are NOT paid again if you are already at that place)
- `diffuser_duct` [in the room; in the affected room; applies to: the room/zone] Look at the diffuser in the room and the duct behind it: is the diffuser blocked or closed, or the duct crushed, disconnected or leaking?
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 8, do 10, wait 0; full cost = 18 | 18 | 18  (access minutes are NOT paid again if you are already at that place)
- `thermostat` [in the room; in the affected room; applies to: the room/zone] In the room, compare the thermostat or zone sensor with a reference thermometer and check its setpoint and mode: is it off, or the setpoint or mode wrong?
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 5, do 6, wait 0; full cost = 11 | 11 | 11  (access minutes are NOT paid again if you are already at that place)
- `design_load` [in the room; in the affected room; applies to: the box/room itself] Compare the current use of the room (people, equipment, area) with the design airflow of the documented box: is the room now asking for more than the box can deliver?
    - answer: POSITIVE = the reading/inspection is ABNORMAL (the sign of a fault). NEGATIVE = normal.
    - minutes if you are not already there / total time per tier (A full data | B BAS but no nameplate/design data | C no BAS access): access 0, do 6, wait 0; full cost = 6 | n/a | 6  (access minutes are NOT paid again if you are already at that place)

## What your tree is judged on
Your tree will be run mechanically on many simulated call-outs and scored on: (1) is the named cause the true cause; (2) total minutes; (3) how often you declare "sure" and are wrong (costly: the customer replaces the wrong part); (4) how often you decline to conclude. You do not know the frequency of the causes: use your own experience of how common each is.

## Output format: strict JSON, nothing else inside the code block
A tree is `{"name": str, "preamble": node-or-null, "root": node}`.

- `root` is run once for each complaint, in order.
- `preamble` (optional) is run once, BEFORE the individual complaints, for each AHU that has TWO OR MORE complaints in the visit (the "shared parent first" habit). It may only use checks with `"target": "ahu"` and must end every path in `{"op": "done"}`. Its readings are remembered (free) when the individual complaints are worked. Use `null` if you would not do this.

Node types:
- `{"op": "check", "check": ["id1", "id2", ...], "target": "box" | "ahu", "pos": node, "neg": node, "na": node (optional), "why": "short reason"}`
  Do the FIRST available check in the list (list alternatives in preference order, e.g. `["bas_static", "ahu_gauge"]`). Follow `pos` if the answer is POSITIVE as defined for that check (for reading checks: abnormal; for `override_room`, `override_diffuser`, `duct_trace`, `confirm_acts`: the YES meanings given above; note these four are *healthy-looking* when YES), else `neg`. If none of the listed checks is possible in the current tier (or the box has no reheat etc.), follow `na`; if you give no `na`, `neg` is followed. `"target": "ahu"` is for AHU checks (shared across complaints on the AHU); `"target": "box"` for everything else (it refers to the documented box / the room).
- `{"op": "conclude", "cause": "<cause id>", "sure": true | false}`: `sure: true` = you would act on it (order the part / make the repair) and tell the customer; `sure: false` = "probably this, not confirmed". Leaf.
- `{"op": "find_feeder"}`: the documented box is wrong or something unlisted feeds the room; this standard procedure finds which other box serves the room (acting on each candidate box in turn and watching the room) and names it, or returns "not found". Use it when you believe the drawings are wrong. Leaf.
- `{"op": "escalate", "guess": "<cause id>"}`: you could not find the cause; you would hand off, but your best guess is `guess`. Leaf.
- `{"op": "done"}`: only to end a `preamble` path.
- Optional `"why"` on any node (one short line of reasoning; ignored by the machine).

Keep the tree under about 70 nodes. Every path must end in a leaf. Output the JSON in ONE fenced code block, then below it a short list (max 10 lines) of the judgement calls you made and anything you could not express in this format.

---
## Appendix (added by the study, not part of what the authors saw as the brief): how the two authors were asked, 2026-10-12

Each author was an `Explore`-type subagent (no memory index, no git status, no repository context) told: "Your only permitted tool action is ONE Read of this single file [the brief above]. Do not read, search, list or open anything else. ... Deliver exactly what the brief asks for." Each transcript shows exactly one tool use (that Read). Only the persona line differed:

- **L1 (controls-first):** "you are a senior BAS / controls-focused commercial service technician (15+ years). You start from the control-system front end, you trust points and status over a walk when they can answer the question, and you walk to the box or air handler only when the front end can't settle it or when a part must be condemned. You are efficient and you hate wasted trips, but you do not call a cause you have not supported."
- **L2 (hands-on mechanical):** "you are a senior hands-on mechanical service technician (20+ years) who came up on the tools. You trust your own meter, gauge and eyes over a front-end reading that could be a stale or wrong point, and you like to verify physically before you condemn a part or tell a customer a cause. You are not wasteful: you use the control system when it saves a trip, and you know shortcuts that experienced people take, but you want a confirmation before you call something."

The authors are language models writing as experienced technicians, not human experts. Their trees are frozen exactly as returned (`tree_L1.json`, `tree_L2.json`; the notes they appended are in `tree_L1.notes.txt`, `tree_L2.notes.txt`). The brief gave no detection rates, no prior frequencies and no mention of the adaptive tool.
