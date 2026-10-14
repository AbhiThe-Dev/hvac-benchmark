# Labeling instructions: hot-water work orders (FMUCD, real campus work orders)

You label short work-order texts. Use ONLY the text in the row (and the ComponentDescription / subsystem columns as context). Do not guess beyond the text. These are terse, often all-caps, with abbreviations (DHW = domestic hot water, DHWR = DHW return/recirculation, WH = water heater, HWS/HWR in a non-plumbing context = heating hot water, not domestic).

For EACH row output one JSON object with exactly these keys:

- "sid": the row id.
- "hw_complaint": "yes" if the order reports a problem with the availability, temperature, flow, or pressure of domestic hot water at fixtures or in a building/zone (no hot water, not hot, lukewarm, slow to heat, runs out, too hot, low hot-water pressure, hot/cold crossover). "no" otherwise (pure leak repair, fixture hardware, PM request, install, space heating, etc.).
- "symptom": one of: no_hot | lukewarm_slow_uneven | too_hot | low_flow_pressure | crossover_mixing | leak | equipment_alarm_fault | planned_or_install_request | other
- "scope": one of: building_wide | multi_unit_or_floor | single_unit_or_fixture | unspecified   (building_wide = whole building or "all" fixtures; multi = several rooms/units/a floor/a wing; single = one room, unit or fixture)
- "cause_stated": "yes" ONLY if the text itself names what is wrong beyond the symptom (e.g. failed pump, heater tripped, leaking tank, closed valve, power or gas outage, tempering valve stuck, element burned out), or says what was found. "no" if it states only the symptom or only a request to investigate/repair.
- "cause_class": if cause_stated is yes, one of: heater_plant | controls_setpoint | mixing_valve | recirc_pump | check_valve | balancing_valve | isolation_valve_closed | pipe_leak_or_break | scale_sediment | fixture_cartridge_or_valve | supply_outage | capacity_demand | other ; otherwise "none".
- "component_named": the component the text mentions (short, lower case) or "".
- "recurrence_stated": "yes" if the text says it is a repeat (again, still, recurring, previous WO), else "no".
- "action_named": one of: none | investigate | reset_or_adjust | repair | replace | flush_or_clean | other

Be conservative: when in doubt choose "no"/"unspecified"/"other". Output a JSON array only (no commentary) in the file you are told to write.
