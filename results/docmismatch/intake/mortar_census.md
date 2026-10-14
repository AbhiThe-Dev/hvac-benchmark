# Instrumentation census of the Mortar Brick models (metadata only)

45 graphs, 44 distinct buildings (`smc` lists the same streams as `bldg30`). RECORDED = the point links to a timeseries; DOCUMENTED = the graph lists it. A channel is SUPPORTED in a building when >= 80% of its documented pairs have every point the channel reads (same rule and channel-needs table as the readiness report). Nothing here reads a timeseries; whether a linked stream actually holds usable data is a separate question (readiness).

## What is modelled

- Buildings with AHUs: 42; with VAV boxes: 28; with zones: 29; with coils as nodes: 1 of 44.
- Water-side node classes present, by number of buildings: Valve_Command (39), Chiller (39), Pump_Command (5), Chilled_Water_Bypass_Valve (2), Boiler (1), Heating_Coil (1), Valve_Position_Sensor (1), Chilled_Water_System_Enable_Command (1). There is no water loop, branch, valve or pump node in any graph, so `loop_branch`, `branch_coil`, `loop_pump` and `loop_source` cannot be tested on this dataset at all.

## Which connection types could be tested

Buildings (of the ones that document the connection) supporting each channel; 'recorded' counts only points with a timeseries, 'if trended' counts every documented point.

| connection | buildings documenting it | documented pairs | ch0 | ch1 | ch2 | all 3 channels | at least one channel | at least one channel, if every documented point were trended |
|---|---|---|---|---|---|---|---|---|
| ahu_vav | 28 | 2143 | 0 | 0 | 0 | 0 | 0 | 0 |
| vav_zone | 28 | 2136 | 4 | 7 | 3 | 3 | 8 | 10 |
| coil_vav | 1 | 99 | 0 | 0 | 0 | 0 | 0 | 0 |
| coil_ahu | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Pair level (all buildings together): the share of documented pairs whose two ends have every point a channel reads (recorded / if trended).

| connection | pairs | ch0 | ch1 | ch2 |
|---|---|---|---|---|
| ahu_vav | 2143 | 0% / 0% | 5% / 5% | 5% / 5% |
| vav_zone | 2136 | 23% / 40% | 23% / 42% | 11% / 28% |
| coil_vav | 99 | 0% / 0% | 0% / 0% | 0% / 0% |
| coil_ahu | 0 | n/a / n/a | n/a / n/a | n/a / n/a |

## Which measurements exist

Per equipment kind and signal: buildings where at least one item has it recorded, and where at least 80% of the items do (documented-only in brackets).

| equipment | signal | at least one recorded | >= 80% recorded | at least one documented | >= 80% documented |
|---|---|---|---|---|---|
| AHU | flow | 3 | 1 | 3 | 1 |
| AHU | sat | 30 | 22 | 38 | 30 |
| AHU | mat | 0 | 0 | 30 | 15 |
| AHU | htg | 0 | 0 | 0 | 0 |
| AHU | clg | 0 | 0 | 0 | 0 |
| VAV | flow | 12 | 4 | 16 | 6 |
| VAV | t_dis | 12 | 7 | 16 | 8 |
| VAV | t_in | 0 | 0 | 0 | 0 |
| Zone | temp | 20 | 19 | 26 | 25 |
| Coil | rate | 0 | 0 | 0 | 0 |

## What real buildings record that our channels do not use

Point classes with a timeseries, by number of buildings, on AHUs, VAV boxes and zones (classes our channels already read are left out).

- **AHU**: Cooling_Command (31 buildings, 196 points), Outside_Air_Temperature_Sensor (29 buildings, 98 points), Supply_Air_Temperature_Setpoint (25 buildings, 88 points), Command (25 buildings, 104 points), Return_Air_Temperature_Sensor (23 buildings, 51 points), Supply_Air_Static_Pressure_Sensor (13 buildings, 41 points), Mode_Status (5 buildings, 10 points), Target_Zone_Air_Temperature_Setpoint (1 buildings, 4 points), CO2_Sensor (1 buildings, 3 points), Speed_Command (1 buildings, 2 points), Leaving_Chilled_Water_Temperature_Sensor (1 buildings, 14 points), Entering_Chilled_Water_Temperature_Sensor (1 buildings, 7 points)
- **VAV**: Target_Zone_Air_Temperature_Setpoint (15 buildings, 1080 points), Command (15 buildings, 809 points), Heating_Command (8 buildings, 323 points), Supply_Air_Temperature_Setpoint (1 buildings, 16 points), Occupancy_Sensor (1 buildings, 104 points), Temperature_Setpoint (1 buildings, 4 points), Valve_Command (1 buildings, 50 points), Air_Flow_Setpoint (1 buildings, 99 points)
- **Zone**: 

## Per building (recorded points; share of documented pairs each channel can use)

| building | AHU->VAV pairs | ahu_vav ch0 / ch1 / ch2 | VAV->zone pairs | vav_zone ch0 / ch1 / ch2 |
|---|---|---|---|---|
| bldg1 | 8 | 0% / 0% / 0% | 8 | 100% / 100% / 100% |
| bldg10 | 16 | 0% / 0% / 0% | 16 | 0% / 94% / 0% |
| bldg11 | 394 | 0% / 24% / 24% | 394 | 22% / 0% / 0% |
| bldg12 | 98 | 0% / 0% / 0% | 98 | 0% / 0% / 0% |
| bldg13 | 24 | 0% / 0% / 0% | 24 | 50% / 29% / 29% |
| bldg15 | 129 | 0% / 0% / 0% | 129 | 68% / 21% / 21% |
| bldg18 | 144 | 0% / 0% / 0% | 144 | 0% / 0% / 0% |
| bldg2 | 25 | 0% / 0% / 0% | 25 | 0% / 0% / 0% |
| bldg20 | 13 | 0% / 0% / 0% | 13 | 0% / 62% / 0% |
| bldg22 | 2 | 0% / 0% / 0% | 2 | 50% / 0% / 0% |
| bldg25 | 2 | 0% / 0% / 0% | 2 | 0% / 100% / 0% |
| bldg27 | 17 | 0% / 0% / 0% | 17 | 100% / 0% / 0% |
| bldg28 | 45 | 0% / 0% / 0% | 45 | 0% / 0% / 0% |
| bldg30 | 99 | 0% / 0% / 0% | 99 | 100% / 100% / 100% |
| bldg32 | 107 | 0% / 0% / 0% | 107 | 0% / 100% / 0% |
| bldg34 | 39 | 0% / 0% / 0% | 39 | 36% / 0% / 0% |
| bldg36 | 43 | 0% / 0% / 0% | 43 | 0% / 0% / 0% |
| bldg37 | 283 | 0% / 0% / 0% | 283 | 0% / 0% / 0% |
| bldg39 | 18 | 0% / 0% / 0% | 18 | 0% / 0% / 0% |
| bldg4 | 28 | 0% / 43% / 43% | 28 | 43% / 39% / 39% |
| bldg40 | 87 | 0% / 0% / 0% | 87 | 79% / 0% / 0% |
| bldg42 | 13 | 0% / 0% / 0% | 13 | 0% / 0% / 0% |
| bldg43 | 52 | 0% / 0% / 0% | 52 | 0% / 0% / 0% |
| bldg44 | 44 | 0% / 0% / 0% | 44 | 0% / 0% / 0% |
| bldg5 | 120 | 0% / 0% / 0% | 124 | 0% / 0% / 0% |
| bldg6 | 143 | 0% / 0% / 0% | 132 | 0% / 98% / 0% |
| bldg8 | 24 | 0% / 0% / 0% | 24 | 100% / 100% / 100% |
| bldg9 | 126 | 0% / 0% / 0% | 126 | 49% / 49% / 49% |