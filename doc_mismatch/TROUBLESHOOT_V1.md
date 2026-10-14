# Technician-guided troubleshooting: working model v1

A question-and-answer helper for a call-out about a VAV zone that is "not getting the right airflow or temperature". The technician says where the problem is; the tool suggests **one check at a time**, the technician answers, and the tool updates its belief about the cause until one cause is clear or nothing left is worth its time. It sits beside v0 ([TROUBLESHOOT.md](TROUBLESHOOT.md)), which only asked "which box feeds this room?", and does not change it. It uses no trend data.

**Nothing here has been validated.** It has been exercised only in simulation and by unit tests. Every probability and every minute is a placeholder unless its source says otherwise, and no claim is made that it saves a technician any time. It is built to be shown to technicians and have its numbers replaced by theirs.

## Run it

```bash
.venv/bin/python doc_mismatch/scripts/70_troubleshoot_v1.py                                   # interactive, made-up example building (uses the richest tier its file supports)
.venv/bin/python doc_mismatch/scripts/70_troubleshoot_v1.py --demo --tier T3 --truth low_static # a simulated technician answers: an illustration, not a result
.venv/bin/python doc_mismatch/scripts/70_troubleshoot_v1.py --tier T0 --member Room-204 --room-name "Room 204"   # nothing but "it is a VAV zone"
.venv/bin/python doc_mismatch/scripts/70_troubleshoot_v1.py --tables                          # the tables below, generated from the code
.venv/bin/python -m pytest doc_mismatch/tests/test_troubleshoot_v1.py doc_mismatch/tests/test_troubleshoot_v1_session.py doc_mismatch/tests/test_troubleshoot_tiers.py
```

## Data tiers: what the tool can use

Tiers are explicit and selectable (`--tier`, or `make_case_v1(..., tier=...)`, which also takes an explicit set of data items). **No check may require data unless it truly cannot be offered without it**: a check that lacks a data item is offered at a stated fallback cost, and is unavailable only when the item cannot be made up for.

<!-- BEGIN:tiers -->
| Tier | Data items | What it means |
|---|---|---|
| T0 | none | nothing but the declared equipment type |
| T1 | claims, equipment_list | equipment list + the drawings' claims (v0's input) |
| T2 | attributes, claims, equipment_list | T1 + attributes and design values |
| T3 | attributes, bas_access, claims, equipment_list, point_map | T2 + control-system access and a point map |
| T4 | attributes, bas_access, claims, equipment_list, point_map, trends | T3 + trends (label only: no trend layer is built) |
<!-- END:tiers -->

- **T0** knows only that this is a VAV zone. There are no "the documented box is wrong" causes (there is no documentation to be wrong), and the checks are on "the box serving the room", whichever box the technician finds.
- **T1** is v0's input. It adds the documented box, candidates for a wrong claim, and which air handler serves the box.
- **T2** adds attributes and design values (reheat type, K-factor, design airflow, inlet size; the air handler's static setpoint). A reheat box is known without asking, numeric readings have an expected value on file, and one check that needs design values (`design_load`) becomes possible.
- **T3** adds control-system access and a point map: a control-system read costs about 2 minutes (and the recommendation names the point) instead of 10 or more.
- **T4** is a label. The trend layer is deliberately not built (the separate evidence engine in `active/` is the place for it).

**Fallback costs** (all placeholders): a control-system read is 2 minutes with a point map, 10 without, and unavailable without access; finding which air handler serves a box costs 4 more (control-system reads) or 10 more (a walk); reading a K-factor off the nameplate costs 4, looking up a design airflow 8, reading the inlet size off the box 2.

## What the technician is asked

The location of the complaint (1 entry), optionally two symptoms (is air coming out of the diffuser; too hot or too cold), then one answer per check. A few facts are asked **only when the best next check cannot be offered without them**, one tap each, counted as entries like symptoms:

| Question | Asked when the best check needs it | If the answer is no |
|---|---|---|
| Can you get into the building control system for this box and its air handler? | a control-system read is the best next check and the tier has no access | control-system reads are unavailable |
| Do you have a flow hood or a differential-pressure gauge with you? | a gauge or hood check is the best next check | those checks are unavailable |
| Is someone in the room who can answer a few questions? | asking the occupant is the best next check | that check is unavailable |
| Does this box have a reheat coil or an electric heater? | a reheat check is the best next check and the file does not say | the reheat cause and checks are removed |

A declared fact overrides the tier (someone who cannot get into the control system today is believed even at T3), and a declared reheat that contradicts the file is logged as a discrepancy. Facts can also be declared up front (`--context reheat=no,instrument=yes`). In the session API `next_step()` returns a check, a question or `None`; `recommend()` never asks anything.

## The causes

One first-order cause per call-out (as in v0). The structure follows the failure lists of the two guides (see Sources); the shares are placeholders, since neither guide gives frequencies. Each hardware cause belongs to one of v0's two "the documented box is right" lumps, so with the defaults the v1 prior adds up to v0's prior (tested): a refinement of v0's placeholders, not new numbers.

<!-- BEGIN:causes -->
| Branch | Cause | What it covers | Share of its lump (placeholder) | v0 lump | Where in the guides |
|---|---|---|---|---|---|
| documentation | Documented box is wrong (which one), or fed by something not on the list | the drawings' claim about which box serves the room | prior P(wrong) 0.15, of which 10% unlisted (v0's placeholders) | (v0's own causes) | v0 |
| box_mechanical | `actuator_fail`: Actuator failed or out of torque | gear stripped, motor burned out, or a fail-safe driving the damper the wrong way | 0.30 | doc_acts_fail | CH 3.1, CH 5.1, CH 13 Q2 |
| box_mechanical | `damper_mech`: Damper or linkage stuck or slipping | blade stuck (corrosion, debris, ice), linkage disconnected or slipping, travel limited by a stop or a misaligned coupling, poor seals | 0.30 | doc_acts_fail | CH 3.1, CH 4.1, PNNL damper, linkage |
| power_and_signal | `no_power`: Actuator has no 24 VAC | blown fuse, tripped breaker or failed transformer | 0.15 | doc_acts_fail | CH 3.1, CH 3.2 step 4 |
| power_and_signal | `signal_fault`: Control signal broken, shorted, inverted or the wrong range | no command reaches the actuator, or it acts the wrong way (0-10 V against 2-10 V) | 0.10 | doc_acts_fail | CH 3.1, CH 5.1, CH 13 Q2, PNNL controls |
| controls | `controller_comms`: VAV controller offline or faulted | offline, rebooting, in a fault state or alarming, so commands do not get through | 0.15 | doc_acts_fail | CH 3.1, CH 3.2 step 2 |
| controls | `controller_config`: Controller set up wrongly | K-factor not the nameplate's, maximum airflow setpoint off the design value, minimum setpoint wrong, occupied and unoccupied swapped, poor loop tuning (hunting) | 0.14 | doc_other | CH 4.1, CH 5.1, CH 6, CH 7, CH 9.2 |
| sensing | `flow_sensor`: Flow sensor reads wrong | clogged ports, kinked, loose or swapped (high/low) tubes, transducer offset or drift | 0.12 | doc_other | CH 4.1, CH 7.1, PNNL airflow sensor |
| zone_inputs | `zone_sensor_setpoint`: Zone sensor, setpoint or schedule | sensor out of calibration, setpoint or occupancy schedule or mode wrong, an occupant override | 0.22 | doc_other | PNNL zone sensor, PNNL performance monitoring, CH 9.2 |
| upstream | `ahu_fan_off`: Air handler fan off or tripped | supply fan stopped, VFD tripped | 0.05 | doc_other | CH 3.1, CH 3.2 step 1, CH 10 |
| upstream | `low_static`: Duct pressure too low upstream | static setpoint too low, degraded fan or belt, dirty filters, an upstream leak or blockage, many boxes calling for maximum | 0.12 | doc_other | CH 4.1, CH 8 |
| reheat | `reheat_fail`: Reheat not working | valve stuck or leaking, coil fouled, electric element or connections damaged, no hot water | 0.10 | doc_other | PNNL hydronic reheat, PNNL electric reheat |
| distribution | `duct_diffuser`: Duct or diffuser problem between the box and the room | leaks or bypass, crushed or disconnected flex duct, diffuser or balancing damper blocked or closed | 0.10 | doc_other | CH 5.1, PNNL duct connections |
| capacity | `capacity_design`: Box or room capacity problem | box undersized for the room's current use, design airflow not enough, many boxes at maximum together | 0.08 | doc_other | CH 4.1, CH 9 |
| other | `other`: Something else | the residual: nothing above explains it | 0.07 | doc_other |  |
<!-- END:causes -->

## The checks

Each check declares what it tests, a per-cause response model (the probability of a positive reading under each cause it sees, and a false-alarm rate for every other cause, including "the documented box is wrong"), its minutes (getting there + doing it + waiting; getting there is free when the technician is already at that place), the data it needs with a fallback cost, and where the procedure is described. **The response probabilities and the minutes are placeholders**; what is cited is the procedure and, where a guide gives one, the expected value of a reading. The four v0 checks are kept (their text, rates and minutes are v0's own objects); on a refined cause that behaves differently from its v0 lump (with the air handler off no box override can make the room respond) their rows are changed explicitly and marked as such.

<!-- BEGIN:catalogue -->
| Check | Family | Minutes (access + do + wait) | Needs (fallback when missing) | Causes it sees: P(positive), placeholder | Procedure in |
|---|---|---|---|---|---|
| `override_room` | v0 check | 6 + 2 + 30 = 38 | nothing | hit 0.98 / false alarm 0.03 (v0's rates); refined causes: flow_sensor 0.85, controller_config 0.60, other 0.60, capacity_design 0.50, low_static 0.35, duct_diffuser 0.15, ahu_fan_off 0.03 | v0 |
| `override_diffuser` | v0 check | 6 + 2 + 3 = 11 | nothing | hit 0.90 / false alarm 0.10 (v0's rates); refined causes: flow_sensor 0.85, capacity_design 0.75, controller_config 0.65, other 0.60, low_static 0.40, duct_diffuser 0.20, ahu_fan_off 0.10 | v0 |
| `duct_trace` | v0 check | 10 + 15 + 0 = 25 | nothing | hit 0.98 / false alarm 0.02 (v0's rates) | v0 |
| `confirm_acts` | v0 check | 6 + 3 + 0 = 9 | nothing | hit 0.95 / false alarm 0.05 (v0's rates) | v0, CH 3.2 step 3 |
| `bas_ahu_fan` | control system | 0 + 2 + 0 = 2 | bas_access (required); point_map (else +8); claims (else +4) | ahu_fan_off 0.92, low_static 0.20; every other cause 0.03 | CH 3.2 step 1, CH 10 |
| `bas_static` | control system | 0 + 2 + 0 = 2 | bas_access (required); point_map (else +8); claims (else +4) | ahu_fan_off 0.92, low_static 0.92; every other cause 0.03 | CH 4.2 step 4, CH 8 |
| `bas_controller` | control system | 0 + 2 + 0 = 2 | bas_access (required); point_map (else +8) | controller_comms 0.92, no_power 0.35, actuator_fail 0.20, signal_fault 0.15; every other cause 0.04 | CH 3.2 step 2 |
| `bas_airflow` | control system | 0 + 2 + 0 = 2 | bas_access (required); point_map (else +8) | ahu_fan_off 0.92, low_static 0.75, actuator_fail 0.75, damper_mech 0.75, no_power 0.75, signal_fault 0.75, controller_comms 0.50, flow_sensor 0.50, controller_config 0.50, capacity_design 0.50; every other cause 0.05 | CH 4.2 step 1, CH 10 |
| `bas_damper` | control system | 0 + 2 + 0 = 2 | bas_access (required); point_map (else +8) | damper_mech 0.75, actuator_fail 0.75, no_power 0.50, signal_fault 0.50, low_static 0.50, ahu_fan_off 0.50, capacity_design 0.50, controller_comms 0.20, flow_sensor 0.20, controller_config 0.20; every other cause 0.05 | CH 4.2 step 1, PNNL performance monitoring |
| `bas_zone` | control system | 0 + 2 + 0 = 2 | bas_access (required); point_map (else +8) | zone_sensor_setpoint 0.75; every other cause 0.05 | PNNL performance monitoring, CH 9.2 |
| `bas_reheat` | control system | 0 + 2 + 0 = 2 | bas_access (required); point_map (else +8); box has reheat (required) | reheat_fail 0.75, zone_sensor_setpoint 0.20; every other cause 0.05 | PNNL performance monitoring |
| `bas_hunting` | control system | 0 + 2 + 5 = 7 | bas_access (required); point_map (else +8) | controller_config 0.50, flow_sensor 0.50, damper_mech 0.20, low_static 0.20; every other cause 0.04 | CH 6 |
| `power_24vac` | at the box | 6 + 4 + 0 = 10 | nothing | no_power 0.92, controller_comms 0.20; every other cause 0.03 | CH 3.2 step 4 |
| `control_signal` | at the box | 6 + 4 + 2 = 12 | nothing | signal_fault 0.92, controller_comms 0.50, controller_config 0.20; every other cause 0.04 | CH 3.2 step 5 |
| `manual_damper_test` | at the box | 6 + 8 + 0 = 14 | nothing | damper_mech 0.92; every other cause 0.05 | CH 3.2 step 6 |
| `damper_linkage` | at the box | 6 + 10 + 0 = 16 | nothing | damper_mech 0.75, actuator_fail 0.20, controller_config 0.20; every other cause 0.04 | PNNL damper, PNNL damper linkage, CH 4.1 |
| `controller_leds` | at the box | 6 + 3 + 0 = 9 | nothing | controller_comms 0.75, no_power 0.35, signal_fault 0.15; every other cause 0.04 | CH 3.3 |
| `sensing_ports` | at the box | 6 + 10 + 0 = 16 | box is pressure-independent (required) | flow_sensor 0.75; every other cause 0.04 | CH 4.3, PNNL airflow sensor |
| `flow_vs_gauge` | at the box | 6 + 8 + 0 = 14 | bas_access (required); point_map (else +8); instrument (required); box is pressure-independent (required) | flow_sensor 0.92; every other cause 0.04 | CH 4.2 step 2 |
| `k_factor` | at the box | 6 + 4 + 0 = 10 | bas_access (required); point_map (else +4); attr:k_factor (else +4); box is pressure-independent (required) | controller_config 0.50; every other cause 0.03 | CH 4.2 step 5, CH 7.2 |
| `max_airflow` | at the box | 0 + 4 + 0 = 4 | bas_access (required); point_map (else +4); attr:design_airflow_cfm (else +8) | controller_config 0.50; every other cause 0.03 | CH 4.2 step 6, CH 13 Q7 |
| `static_at_box` | at the box | 6 + 6 + 0 = 12 | instrument (required); attr:inlet_diameter_in (else +2) | low_static 0.92, ahu_fan_off 0.92; every other cause 0.04 | CH 4.2 step 4, CH 8.3 |
| `reheat_coil` | at the box | 6 + 10 + 0 = 16 | box has reheat (required) | reheat_fail 0.75; every other cause 0.04 | PNNL hydronic reheat, PNNL electric reheat |
| `ahu_visit` | at the air handler | 15 + 4 + 0 = 19 | claims (else +10) | ahu_fan_off 0.92, low_static 0.10; every other cause 0.04 | CH 3.2 step 1, CH 8 |
| `ahu_gauge` | at the air handler | 15 + 2 + 0 = 17 | claims (else +10) | ahu_fan_off 0.92, low_static 0.92; every other cause 0.04 | CH 4.2 step 4, CH 8 |
| `flow_hood` | in the room | 5 + 8 + 0 = 13 | instrument (required) | ahu_fan_off 0.92, low_static 0.75, actuator_fail 0.75, damper_mech 0.75, no_power 0.75, signal_fault 0.75, flow_sensor 0.75, controller_config 0.75, duct_diffuser 0.75, controller_comms 0.50, capacity_design 0.50, other 0.20; every other cause 0.05 | CH 5.2 step 1 |
| `diffuser_duct` | in the room | 8 + 10 + 0 = 18 | nothing | duct_diffuser 0.85; every other cause 0.04 | CH 5.1, PNNL duct connections |
| `thermostat` | in the room | 5 + 6 + 0 = 11 | nothing | zone_sensor_setpoint 0.92; every other cause 0.05 | PNNL zone sensor |
| `ask_occupant` | in the room | 3 + 3 + 0 = 6 | occupant (required) | zone_sensor_setpoint 0.55, duct_diffuser 0.35, capacity_design 0.35, controller_config 0.20; every other cause 0.12 | PNNL performance monitoring |
| `design_load` | in the room | 0 + 6 + 0 = 6 | attr:design_airflow_cfm (required) | capacity_design 0.75; every other cause 0.04 | CH 4.1, CH 9 |
<!-- END:catalogue -->

## Observations

- The four v0 checks are answered **yes / no**, as in v0. The reading checks are phrased "is it wrong?" and answered **abnormal / normal** (yes / no work as synonyms). Both take **unsure** (the time is spent, nothing is learned) and **skip** (nothing is spent, nothing is learned, the check is not offered again).
- A reading check may be answered with a **number**. It is compared with an expected value and a tolerance and recorded as normal or abnormal; the expected value is the one the technician supplies, else the documented attribute (T2 and up), else the guide's:

<!-- BEGIN:readings -->
| Check | Quantity | Normal when | Source of the expected value |
|---|---|---|---|
| `bas_static` | duct static pressure (in. w.c.) | within 20% of the expected value (documented `static_setpoint_inwc`, else the technician's) | PLACEHOLDER tolerance; the setpoint is documented (T2) |
| `bas_airflow` | measured airflow (cfm) | within 10% of the expected value (the technician's) | cited (ControlsHub 13 Q5, which cites ASHRAE Guideline 36: within 10% above 20% of maximum; not checked against the Guideline); the expected value is the setpoint the technician reads |
| `power_24vac` | AC voltage at the actuator (V) | within 2 V of 24 | cited (ControlsHub 3.2 step 4: 22-26 VAC) |
| `control_signal` | DC control signal with an open command (V) | at least 2 V | cited (ControlsHub 3.2 step 5: above 2 V for an open command on a 0-10 V actuator) |
| `flow_vs_gauge` | controller differential pressure (in. w.c.) | within 10% of the expected value (the technician's) | PLACEHOLDER tolerance (ControlsHub 4.2 step 2 gives none); the expected value is the gauge's reading |
| `k_factor` | K-factor (no unit) | within 1% of the expected value (documented `k_factor`, else the technician's) | PLACEHOLDER tolerance (ControlsHub 7.2: a mismatch is corrected); the expected value is the documented or nameplate one |
| `max_airflow` | maximum airflow setpoint (cfm) | within 10% of the expected value (documented `design_airflow_cfm`, else the technician's) | PLACEHOLDER tolerance; ControlsHub 4.2 step 6 and 13 Q7: the maximum should equal the design value |
| `static_at_box` | inlet static pressure (in. w.c.) | at or above the minimum for the inlet size | cited (ControlsHub 8.3, minimum inlet static by box size) |
| `ahu_gauge` | duct static pressure (in. w.c.) | within 20% of the expected value (documented `static_setpoint_inwc`, else the technician's) | PLACEHOLDER tolerance; the setpoint is documented (T2) |
| `flow_hood` | airflow at the diffuser (cfm) | within 10% of the expected value (the technician's) | cited (ControlsHub 13 Q5, secondary); the expected value is the box's current setpoint or design airflow, supplied by the technician |
<!-- END:readings -->

- If the technician supplies an expected value that differs from the documented one (a nameplate K-factor that is not the file's), a discrepancy is logged.

## The session log

`Session.events` records discrepancies between the documentation and what was found, as structured events (`type`, minutes so far, checks so far, `data`): `documented_owner_wrong` (the tool concluded the room is fed by another box, or by something not on the list), `undocumented_equipment` (the technician added a box that is not on the equipment list: `add_equipment`) and `documented_attribute_mismatch` (a declared reheat or a nameplate value that contradicts the file). `Session.export()` returns the whole session as JSON-serialisable data, including an `assumptions` block (which numbers are placeholders, the stopping thresholds, `validated_on_real_call_outs: false`).

## The number that matters most: how reliable the checks are

Confidence figures assume each check reads as reliably as the catalogue says. That assumption is the one the earlier simulations were most sensitive to (v0: checks worse than assumed made the tool confidently wrong about three to four times as often, PREREGISTRATION_DR.md Addenda 19 and 22), and v1 answers each check independently given the cause, whereas real errors are correlated, so real confidence is likely to be lower than shown. The tool therefore prints this caveat with every result and carries it in the export; `catalogue.degrade_all(catalogue, a)` builds a world in which every check is worse than the tool believes, and the pre-registered tier study (Addendum 27) includes two levels of it as a stress condition. Replacing the placeholder rates with observed ones is what the technician interviews and shadow-mode logging are for.

## Worked examples (simulated technician; an illustration, not a result)

The simulated technician answers every check with its most likely result when the real cause is low duct pressure upstream. The same complaint at two tiers:

**T1** (v0's input; no control-system access):

<!-- BEGIN:example_t1 -->
```text
[demo] simulated technician; the real cause is Duct pressure too low upstream (each check answered with its most likely result)

Complaint: Room 204. Data available: tier T1.
The drawings say it is fed by 2-04. Could be fed by: 2-04, 2-05, 2-06, 2-01, 2-02, 2-03.

Next check (about 9 min): Command box 2-04 and confirm its damper actually moves
  about 82% likely to come back yes; expected to sharpen the picture by 0.40 bits for 9 minutes
  Result? [y]es / [n]o / [u]nsure / [s]kip / [+] add equipment / [q]uit > y
  belief now: Zone sensor, setpoint or schedule 18% | Controller set up wrongly 11% | Flow sensor reads wrong 10%

Next check (about 5 min): Command box 2-04 to full cooling and check whether airflow at Room 204's diffuser rises
  about 55% likely to come back yes; expected to sharpen the picture by 0.33 bits for 5 minutes
  Result? [y]es / [n]o / [u]nsure / [s]kip / [+] add equipment / [q]uit > n
  belief now: Duct or diffuser problem between the box and the room 15% | Duct pressure too low upstream 13% | fed by 2-05 12%

Do you have a flow hood or a differential-pressure gauge with you?  (needed before 'static_at_box', which is the most useful check right now)
  [y]es / [n]o / [s]kip (counts as no) > y

Next check (about 8 min): At box 2-04, measure the static pressure at the inlet: is it below the minimum for its size (about 0.25 to 0.5 in. w.c.)? [inlet static pressure: normal is at least 0.25 in. w.c.]
  about 23% likely to come back abnormal; expected to sharpen the picture by 0.50 bits for 8 minutes (includes 2 extra minutes because some data is not on file)
  Result? [a]bnormal / [n]ormal / a number / [u]nsure / [s]kip / [+] add equipment / [q]uit > y
  belief now: Duct pressure too low upstream 53% | Air handler fan off or tripped 33% | Duct or diffuser problem between the box and the room 3%

Can you get into the building control system for this box and its air handler?  (needed before 'bas_ahu_fan', which is the most useful check right now)
  [y]es / [n]o / [s]kip (counts as no) > n

Next check (about 19 min): Go to AHU-2: is the supply fan stopped, tripped or in fault?
  about 36% likely to come back abnormal; expected to sharpen the picture by 0.53 bits for 19 minutes
  Result? [a]bnormal / [n]ormal / a number / [u]nsure / [s]kip / [+] add equipment / [q]uit > n
  belief now: Duct pressure too low upstream 75% | Air handler fan off or tripped 4% | Duct or diffuser problem between the box and the room 4%

Next check (about 2 min): At AHU-2, read the duct static pressure gauge against its setpoint: is it low? [duct static pressure (in. w.c.); no expected value on file]
  about 74% likely to come back abnormal; expected to sharpen the picture by 0.46 bits for 2 minutes
  Result? [a]bnormal / [n]ormal / a number / [u]nsure / [s]kip / [+] add equipment / [q]uit > y
  belief now: Duct pressure too low upstream 94% | Air handler fan off or tripped 5% | Duct or diffuser problem between the box and the room 0%

No further check is worth its time.
  belief now: Duct pressure too low upstream 94% | Air handler fan off or tripped 5% | Duct or diffuser problem between the box and the room 0%

So far: 5 checks, about 43 minutes, 8 entries typed.
  Note: The confidence figures assume every check reads as reliably as the catalogue's rates say; those rates are placeholders (only override_room's come from a simulation). If the checks in your building are less reliable, the real confidence is lower (in v0's simulations, worse checks made the tool confidently wrong about three to four times as often; v1 has not been measured yet).
```
<!-- END:example_t1 -->

**T3** (attributes, control-system access and a point map): the first three checks are 2-minute control-system reads that name the point, and the expected duct pressure comes from the file. It also walks to the air handler at the end to re-check a fan status the control system had already shown, because the tool treats the two routes as independent evidence (see "What it does not do").

<!-- BEGIN:example_t3 -->
```text
[demo] simulated technician; the real cause is Duct pressure too low upstream (each check answered with its most likely result)

Complaint: Room 204. Data available: tier T3.
The drawings say it is fed by 2-04. Could be fed by: 2-04, 2-05, 2-06, 2-01, 2-02, 2-03.

Next check (about 2 min): In the control system, read the duct static pressure of AHU-2 against its setpoint: is it low? (control-system point: AHU2.DSP) [duct static pressure: normal is 0.96 to 1.44 in. w.c.]
  about 14% likely to come back abnormal; expected to sharpen the picture by 0.35 bits for 2 minutes
  Result? [a]bnormal / [n]ormal / a number / [u]nsure / [s]kip / [+] add equipment / [q]uit > y
  belief now: Duct pressure too low upstream 57% | Air handler fan off or tripped 24% | Zone sensor, setpoint or schedule 3%

Next check (about 2 min): In the control system, read the supply fan status, speed and alarms of AHU-2: is the fan off, tripped or in alarm? (control-system point: AHU2.SF_STS)
  about 34% likely to come back abnormal; expected to sharpen the picture by 0.38 bits for 2 minutes
  Result? [a]bnormal / [n]ormal / a number / [u]nsure / [s]kip / [+] add equipment / [q]uit > n
  belief now: Duct pressure too low upstream 69% | Zone sensor, setpoint or schedule 5% | Controller set up wrongly 3%

Next check (about 2 min): In the control system, read the airflow setpoint and measured airflow of box 2-04: does the measurement miss the setpoint by more than about 10%? (control-system point: AHU2.V204.CFM) [measured airflow (cfm); no expected value on file]
  about 62% likely to come back abnormal; expected to sharpen the picture by 0.22 bits for 2 minutes
  Result? [a]bnormal / [n]ormal / a number / [u]nsure / [s]kip / [+] add equipment / [q]uit > y
  belief now: Duct pressure too low upstream 83% | Air handler fan off or tripped 4% | Controller set up wrongly 3%

Do you have a flow hood or a differential-pressure gauge with you?  (needed before 'static_at_box', which is the most useful check right now)
  [y]es / [n]o / [s]kip (counts as no) > y

Next check (about 12 min): At box 2-04, measure the static pressure at the inlet: is it below the minimum for its size (about 0.25 to 0.5 in. w.c.)? [inlet static pressure: normal is at least 0.3 in. w.c.]
  about 81% likely to come back abnormal; expected to sharpen the picture by 0.33 bits for 12 minutes
  Result? [a]bnormal / [n]ormal / a number / [u]nsure / [s]kip / [+] add equipment / [q]uit > y
  belief now: Duct pressure too low upstream 95% | Air handler fan off or tripped 5% | Controller set up wrongly 0%

Next check (about 19 min): Go to AHU-2: is the supply fan stopped, tripped or in fault?
  about 14% likely to come back abnormal; expected to sharpen the picture by 0.12 bits for 19 minutes
  Result? [a]bnormal / [n]ormal / a number / [u]nsure / [s]kip / [+] add equipment / [q]uit > n
  belief now: Duct pressure too low upstream 99% | Air handler fan off or tripped 0% | Controller set up wrongly 0%

Likely cause: Duct pressure too low upstream: static setpoint too low, degraded fan or belt, dirty filters, an upstream leak or blockage, many boxes calling for maximum.

So far: 5 checks, about 37 minutes, 7 entries typed.
  Note: The confidence figures assume every check reads as reliably as the catalogue's rates say; those rates are placeholders (only override_room's come from a simulation). If the checks in your building are less reliable, the real confidence is lower (in v0's simulations, worse checks made the tool confidently wrong about three to four times as often; v1 has not been measured yet).
```
<!-- END:example_t3 -->

## What is a placeholder, what is measured, what is cited

| Item | Source |
|---|---|
| Prior masses (P(documented box wrong) 0.15 of which 10% unlisted; P(box does not act) 0.15) and the nearness weights | placeholders (v0's) |
| Leaf shares within each lump; the symptom multipliers (no air x3, "too cold" raises reheat failure x3, "too hot" raises capacity x2) | placeholders |
| Every response probability of every check, and every false-alarm rate | placeholders, except `override_room`'s hit and false-alarm rates (0.98 / 0.03), which v0 took from a simulation (PREREGISTRATION_DR.md Addendum 16) |
| Every minute, and every fallback cost | placeholders |
| Which checks exist, what each is looking for, in what order a technician would do them | cited: the PNNL and ControlsHub pages (section numbers in the tables) |
| Expected values and tolerances of readings | cited where a guide states them (22-26 VAC; above 2 V; minimum inlet static by box size; 10% airflow accuracy, which ControlsHub itself attributes to ASHRAE Guideline 36 and which was not checked against the Guideline); marked PLACEHOLDER where the guide gives none |
| Stopping: tau 0.95 (v0's), and at most 0.003 bits per minute of expected gain (new in v1) | placeholders |

## What it does not do

- One cause at a time. A wrong claim and a fault at the true box together are not modelled; after "the documented box is wrong, it is 2-05" the tool says to start a new diagnosis on 2-05 and does not chain it.
- Cover fan-powered, dual-duct or induction boxes as boxes of their own, or hunting beyond one live look; the box-to-air-handler question of v0 (`ahu_vav`) is not carried into v1 (the claim is used to find the air handler).
- Tell when two routes lead to the same fact through the same error. The control-system fan status and walking to the air handler count as independent evidence, which is right only if their errors really are independent, so the tool may recommend a walk to confirm what the control system just said. More generally each check is answered independently given the cause, whereas real errors are correlated.
- Use trends, alarms histories or FDD output; run checks in parallel while waiting (the 30-minute room response could be spent on other checks); price disruption to occupants; repeat a noisy check.
- Learn from a session: nothing is fitted.

## Sources

- PNNL, *Variable Air Volume (VAV) Systems: Operations & Maintenance Guide* (O&M Best Practices): https://www.pnnl.gov/projects/om-best-practices/variable-air-volume-systems (maintenance checklist and performance monitoring). Read on 2026-09-25.
- ControlsHub, *VAV Box Airflow Problems: Complete Troubleshooting Guide*: https://controlshub.tech/en/blog/66-vav-box-airflow-problems/ (sections 3-10 and 13; cited as "CH n.n" in the tables). A vendor blog: its numbers are its own and were not independently verified here. Read on 2026-09-25.

## Validation status and how it is tested

Unit tests only, plus a check against deliberately broken versions of the code, run with bytecode caching off and `__pycache__` removed (a same-size edit once left stale bytecode and a false failure). v0 is untouched: its demo output and three scripted transcripts, captured before any v1 code was written, are compared byte for byte, and the v0-equivalent tree of v1 reproduces v0's sessions and simulated episodes exactly. **The first study of what each data tier buys was pre-registered (PREREGISTRATION_DR.md Addendum 27) and run once, in simulation** (synthetic building, simulated technician, placeholder numbers): the point map is where the minutes are (T3 about 43% faster than control-system access without a map, at about the same accuracy); access alone bought accuracy, not minutes; attributes helped a little; **the number of checks did not fall with more data (about 8 to 9 per call-out at every tier)**; and when the checks are worse than the tool believes, accuracy falls to a quarter to a half and the richer tiers are confidently wrong more often. See the result paragraph of Addendum 27 for the numbers and caveats. Against invented fast stand-ins (a cheapest-first checklist, a checklist with confirmation, and v0's fast habit; Addendum 28, also simulation only) the tool was 26-40 points more accurate on the exact cause, slower with little data (+8% to +35% minutes against the plain checklist at T0-T2) and faster with the control system (-6% to -13% at T2+access and T3); the stand-ins are my constructions and cannot name several causes at all, so that accuracy gap partly reflects their design. Nothing has been tried with a real technician.
