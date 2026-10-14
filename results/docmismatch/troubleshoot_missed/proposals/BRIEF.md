# Task: find the causes this troubleshooting model is missing

A diagnostic tool helps an HVAC technician who has been called to ONE complaint: "the room is not getting the right airflow or temperature". The room is served by a VAV
(variable-air-volume) box, fed by a central air handler. The tool keeps a fixed list of possible causes and a fixed menu of checks, and updates its belief about which
cause is responsible after each check the technician reports.

Your job: act as an experienced commissioning / controls technician and list causes of this complaint that the tool's list does NOT cover (or lumps so badly that it
would send the technician down the wrong path). For each, say how the tool's EXISTING checks would read if that were the true cause, and give ONE dedicated check that
would confirm it.

Rules: work from your own knowledge only. Do not read any files in the repository, do not search the web, do not look for the answer anywhere. You are writing the
proposal, not running anything. Give at most 6 candidates; give fewer if you are not confident in more. Quality over quantity: a wrong or redundant candidate has a cost.

## The tool's current causes (id: label — detail)

- actuator_fail: Actuator failed or out of torque — gear stripped, motor burned out, or a fail-safe driving the damper the wrong way
- damper_mech: Damper or linkage stuck or slipping — blade stuck (corrosion, debris, ice), linkage disconnected or slipping, travel limited by a stop or a misaligned coupling, poor seals
- no_power: Actuator has no 24 VAC — blown fuse, tripped breaker or failed transformer
- signal_fault: Control signal broken, shorted, inverted or the wrong range — no command reaches the actuator, or it acts the wrong way (0-10 V against 2-10 V)
- controller_comms: VAV controller offline or faulted — offline, rebooting, in a fault state or alarming, so commands do not get through
- controller_config: Controller set up wrongly — K-factor not the nameplate's, maximum airflow setpoint off the design value, minimum setpoint wrong, occupied and unoccupied swapped, poor loop tuning (hunting)
- flow_sensor: Flow sensor reads wrong — clogged ports, kinked, loose or swapped (high/low) tubes, transducer offset or drift
- zone_sensor_setpoint: Zone sensor, setpoint or schedule — sensor out of calibration, setpoint or occupancy schedule or mode wrong, an occupant override
- ahu_fan_off: Air handler fan off or tripped — supply fan stopped, VFD tripped
- low_static: Duct pressure too low upstream — static setpoint too low, degraded fan or belt, dirty filters, an upstream leak or blockage, many boxes calling for maximum
- reheat_fail: Reheat not working — valve stuck or leaking, coil fouled, electric element or connections damaged, no hot water
- duct_diffuser: Duct or diffuser problem between the box and the room — leaks or bypass, crushed or disconnected flex duct, diffuser or balancing damper blocked or closed
- capacity_design: Box or room capacity problem — box undersized for the room's current use, design airflow not enough, many boxes at maximum together
- other: Something else — the residual: nothing above explains it
- wrong / unlisted: the documented box (per the drawings) is not the one serving the room / the room is fed by equipment not on the equipment list

Also considered upstream causes (air handler level): ahu_fan_off, low_static (above).

## The tool's current checks (name [where]: what it asks) — every check answers 'abnormal' or 'normal' (v0-style checks answer yes/no)

- override_room [target]: Command the box to full cooling and watch whether the temperature in the room responds
- override_diffuser [target]: Command the box to full cooling and check whether airflow at the room's diffuser rises
- duct_trace [target]: Trace the duct from the room's diffuser back to its box: is it the target?
- confirm_acts [target]: Command the box and confirm its damper actually moves
- bas_ahu_fan [bas]: In the control system, read the supply fan status, speed and alarms of the air handler: is the fan off, tripped or in alarm?
- bas_static [bas]: In the control system, read the duct static pressure of the air handler against its setpoint: is it low?
- bas_controller [bas]: In the control system, read the controller status and alarms of the box: is it offline, in a fault state or alarming?
- bas_airflow [bas]: In the control system, read the airflow setpoint and measured airflow of the box: does the measurement miss the setpoint by more than about 10%?
- bas_damper [bas]: In the control system, read the damper position of the box against its command: is it pinned at 100% while airflow is low, or not following its command?
- bas_zone [bas]: In the control system, read the temperature, setpoint, occupancy schedule and mode of the room: is the setpoint, schedule or mode wrong for this room?
- bas_reheat [bas]: In the control system, read the reheat command and valve or stage position of the box: is heat called for but the valve or stage not responding?
- bas_hunting [bas]: In the control system, watch the damper and airflow of the box for about 5 minutes: do they keep swinging up and down?
- power_24vac [box]: At the box, measure the voltage at the actuator terminals: is it missing or outside 22 to 26 VAC?
- control_signal [box]: With the box commanded open, measure the control signal at its actuator input: is it missing (under about 2 V on a 0-10 V actuator)?
- manual_damper_test [box]: At the box, disconnect the actuator and turn the damper shaft by hand: is the damper stuck or binding?
- damper_linkage [box]: At the box, inspect the damper linkage, seals and stops: is the linkage loose or slipping, or the damper not reaching fully open or fully closed?
- controller_leds [box]: At the box, look at the controller status lights and event log: is it dead, showing a fault, or off the network?
- sensing_ports [box]: At the box, inspect the flow-sensing ports and tubing: are ports clogged, or tubes kinked, loose or swapped (high and low)?
- flow_vs_gauge [box]: At the box, compare the controller's pressure reading with a gauge on its flow taps: do they disagree by more than about 10%?
- k_factor [box]: Compare the K-factor programmed in the controller of the box with the value on its nameplate or submittal: do they differ?
- max_airflow [box]: Compare the maximum airflow setpoint in the controller of the box with its design airflow: is it different?
- static_at_box [box]: At the box, measure the static pressure at the inlet: is it below the minimum for its size (about 0.25 to 0.5 in. w.c.)?
- reheat_coil [box]: At the box, inspect the reheat coil and valve (or electric element and connections): is the valve stuck or leaking, the coil fouled, or a connection damaged?
- ahu_visit [ahu]: Go to the air handler: is the supply fan stopped, tripped or in fault?
- ahu_gauge [ahu]: At the air handler, read the duct static pressure gauge against its setpoint: is it low?
- flow_hood [room]: Measure airflow at the diffuser in the room with a flow hood: is it well off what the box should be delivering right now?
- diffuser_duct [room]: Look at the diffuser in the room and the duct behind it: is the diffuser blocked or closed, or the duct crushed, disconnected or leaking?
- thermostat [room]: In the room, compare the thermostat or zone sensor with a reference thermometer and check its setpoint and mode: is it off, or the setpoint or mode wrong?
- ask_occupant [room]: Ask the occupant: does it happen only at certain times, has anyone changed the thermostat, is a diffuser blocked? Do the answers point to one of those?
- design_load [room]: Compare the current use of the room (people, equipment, area) with the design airflow of the box: is the room now asking for more than the box can deliver?

## What to return

Write ONE JSON file (path given below) with this shape, and nothing else in it:
{"proposer": "<your label>",
 "candidates": [
  {"id": "snake_case_id",
   "label": "short name",
   "detail": "one or two sentences: what is physically wrong",
   "share": 0.0-0.3,   // your guess of the fraction of ALL such complaints this cause would be responsible for
   "profile": {"<existing check name>": "strong|good|partial|weak", ...},   // ONLY existing checks that would read ABNORMAL (or yes) because of this cause; leave out checks that would read normal
   "check": {"name": "snake_case_name", "text": "what the technician does and what counts as abnormal",
             "place": "box|room|ahu|bas", "do_min": <minutes to do it, 2-20>, "hit": "strong|good|partial|weak"}   // ONE new dedicated check
  }, ...]}
Level meaning: strong = reads abnormal about 92% of the time under that cause, good = 75%, partial = 50%, weak = 20%. Every check also false-alarms ~4% of the time under other causes.
Then reply with a one-line confirmation of the file path.
