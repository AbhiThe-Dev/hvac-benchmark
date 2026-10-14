# Field-case replay of the live v2 tool (Addendum 38)

Simulation-grade placeholders throughout; two real videos; n = 2. The scripted technician answers only from what the video shows ('E') and says 'unsure' otherwise ('U'). Padding rooms (k) are invented. Nothing here validates or calibrates the tool.

## Everything HVACR: office and cubicle area too cold in the morning, Trane VAV controls

Technician's first check: `bas_zone`. Tier: T3-noattr (BAS access + point map, no documented attributes): nothing in the video shows a design value being consulted.

| k (non-complaining rooms) | checks recommended | answered from video | coverage | tool minutes (U minutes) | first check | = technician's? | stop |
|---|---|---|---|---|---|---|---|
| 2 | 8 | 4 | 50% | 34 (17) | `bas_static` | no | stalled (nothing left worth its time) |
| 6 (primary) | 7 | 3 | 43% | 32 (17) | `bas_static` | no | stalled (nothing left worth its time) |
| 12 | 6 | 3 | 50% | 30 (15) | `bas_zone` | yes | stalled (nothing left worth its time) |

### k = 2: complaints (probability mass on the accepted causes, before -> after)

| complaint | accepted | before | after | tool's leading cause | concluded | wrong and confident |
|---|---|---|---|---|---|---|
| Room-206 | zone_sensor_setpoint, controller_config | 13% | 98% | zone_sensor_setpoint 98% | yes | no |
| Room-232 | controller_config, zone_sensor_setpoint | 15% | 84% | zone_sensor_setpoint 81% | no | no |

| # | check | for | min | answer | basis |
|---|---|---|---|---|---|
| 1 | `bas_static` | RTU-2 | 2 | unsure (U) |  |
| 2 | `bas_airflow` | Room-232 | 2 | unsure (U) |  |
| 3 | `bas_ahu_fan` | RTU-2 | 2 | normal (E) | 10:15-10:45, 11:15 |
| 4 | `bas_zone` | Room-232 | 2 | abnormal (E) | 2:45-3:15 |
| 5 | `bas_damper` | Room-232 | 2 | unsure (U) |  |
| 6 | `bas_zone` | Room-206 | 2 | abnormal (E) | 0:00-0:30, 2:45-3:15, 5:45-6:30 |
| 7 | `thermostat` | Room-206 | 11 | abnormal (E) | 5:45-6:15 |
| 8 | `thermostat` | Room-232 | 11 | unsure (U) |  |

Technician's mapped checks the tool never recommended: none. Checks the tool recommended that the technician did not do: bas_airflow, bas_damper, bas_static, thermostat.

Air handler belief at the end (ok / fan off / low static): RTU-2: 98% / 0% / 2%

### k = 6: complaints (probability mass on the accepted causes, before -> after)

| complaint | accepted | before | after | tool's leading cause | concluded | wrong and confident |
|---|---|---|---|---|---|---|
| Room-206 | zone_sensor_setpoint, controller_config | 30% | 99% | zone_sensor_setpoint 99% | yes | no |
| Room-232 | controller_config, zone_sensor_setpoint | 34% | 85% | zone_sensor_setpoint 82% | no | no |

| # | check | for | min | answer | basis |
|---|---|---|---|---|---|
| 1 | `bas_static` | RTU-2 | 2 | unsure (U) |  |
| 2 | `bas_airflow` | Room-232 | 2 | unsure (U) |  |
| 3 | `bas_zone` | Room-232 | 2 | abnormal (E) | 2:45-3:15 |
| 4 | `bas_zone` | Room-206 | 2 | abnormal (E) | 0:00-0:30, 2:45-3:15, 5:45-6:30 |
| 5 | `bas_damper` | Room-232 | 2 | unsure (U) |  |
| 6 | `thermostat` | Room-206 | 11 | abnormal (E) | 5:45-6:15 |
| 7 | `thermostat` | Room-232 | 11 | unsure (U) |  |

Technician's mapped checks the tool never recommended: bas_ahu_fan. Checks the tool recommended that the technician did not do: bas_airflow, bas_damper, bas_static, thermostat.

Air handler belief at the end (ok / fan off / low static): RTU-2: 100% / 0% / 0%

### k = 12: complaints (probability mass on the accepted causes, before -> after)

| complaint | accepted | before | after | tool's leading cause | concluded | wrong and confident |
|---|---|---|---|---|---|---|
| Room-206 | zone_sensor_setpoint, controller_config | 33% | 99% | zone_sensor_setpoint 99% | yes | no |
| Room-232 | controller_config, zone_sensor_setpoint | 38% | 85% | zone_sensor_setpoint 82% | no | no |

| # | check | for | min | answer | basis |
|---|---|---|---|---|---|
| 1 | `bas_zone` | Room-232 | 2 | abnormal (E) | 2:45-3:15 |
| 2 | `bas_zone` | Room-206 | 2 | abnormal (E) | 0:00-0:30, 2:45-3:15, 5:45-6:30 |
| 3 | `bas_airflow` | Room-232 | 2 | unsure (U) |  |
| 4 | `bas_damper` | Room-232 | 2 | unsure (U) |  |
| 5 | `thermostat` | Room-206 | 11 | abnormal (E) | 5:45-6:15 |
| 6 | `thermostat` | Room-232 | 11 | unsure (U) |  |

Technician's mapped checks the tool never recommended: bas_ahu_fan. Checks the tool recommended that the technician did not do: bas_airflow, bas_damper, thermostat.

Air handler belief at the end (ok / fan off / low static): RTU-2: 100% / 0% / 0%

## Nighthawk HVAC EP160: VAV electric heat not heating

Technician's first check: `bas_reheat`. Tier: T3-noattr (BAS access + point map, no documented attributes).

| k (non-complaining rooms) | checks recommended | answered from video | coverage | tool minutes (U minutes) | first check | = technician's? | stop |
|---|---|---|---|---|---|---|---|
| 2 | 15 | 4 | 27% | 91 (55) | `bas_static` | no | stalled (nothing left worth its time) |
| 6 (primary) | 13 | 4 | 31% | 72 (36) | `bas_static` | no | stalled (nothing left worth its time) |
| 12 | 12 | 4 | 33% | 70 (34) | `bas_zone` | no | stalled (nothing left worth its time) |

### k = 2: complaints (probability mass on the accepted causes, before -> after)

| complaint | accepted | before | after | tool's leading cause | concluded | wrong and confident |
|---|---|---|---|---|---|---|
| Zone-T212 | reheat_fail | 4% | 94% | reheat_fail 94% | no | no |
| Zone-T117 | reheat_fail, other | 6% | 94% | reheat_fail 94% | no | no |

| # | check | for | min | answer | basis |
|---|---|---|---|---|---|
| 1 | `bas_static` | AHU-1 | 2 | unsure (U) |  |
| 2 | `bas_airflow` | Zone-T212 | 2 | unsure (U) |  |
| 3 | `bas_airflow` | Zone-T117 | 2 | unsure (U) |  |
| 4 | `bas_ahu_fan` | AHU-1 | 2 | unsure (U) |  |
| 5 | `bas_damper` | Zone-T212 | 2 | unsure (U) |  |
| 6 | `bas_damper` | Zone-T117 | 2 | unsure (U) |  |
| 7 | `bas_zone` | Zone-T212 | 2 | unsure (U) |  |
| 8 | `bas_zone` | Zone-T117 | 2 | unsure (U) |  |
| 9 | `ahu_gauge` | AHU-1 | 17 | unsure (U) |  |
| 10 | `bas_reheat` | Zone-T212 | 2 | abnormal (E) | 0:30-1:00 |
| 11 | `bas_reheat` | Zone-T117 | 2 | abnormal (E) | 1:00-1:30 |
| 12 | `thermostat` | Zone-T212 | 11 | unsure (U) |  |
| 13 | `thermostat` | Zone-T117 | 11 | unsure (U) |  |
| 14 | `reheat_coil` | Zone-T212 | 16 | abnormal (E) | 3:15-5:15 |
| 15 | `reheat_coil` | Zone-T117 | 16 | abnormal (E) | 5:15-6:15 |

Technician's mapped checks the tool never recommended: none. Checks the tool recommended that the technician did not do: ahu_gauge, bas_ahu_fan, bas_airflow, bas_damper, bas_static, bas_zone, thermostat.

Air handler belief at the end (ok / fan off / low static): AHU-1: 99% / 0% / 1%

### k = 6: complaints (probability mass on the accepted causes, before -> after)

| complaint | accepted | before | after | tool's leading cause | concluded | wrong and confident |
|---|---|---|---|---|---|---|
| Zone-T212 | reheat_fail | 8% | 94% | reheat_fail 94% | no | no |
| Zone-T117 | reheat_fail, other | 14% | 95% | reheat_fail 94% | no | no |

| # | check | for | min | answer | basis |
|---|---|---|---|---|---|
| 1 | `bas_static` | AHU-1 | 2 | unsure (U) |  |
| 2 | `bas_airflow` | Zone-T212 | 2 | unsure (U) |  |
| 3 | `bas_airflow` | Zone-T117 | 2 | unsure (U) |  |
| 4 | `bas_zone` | Zone-T212 | 2 | unsure (U) |  |
| 5 | `bas_zone` | Zone-T117 | 2 | unsure (U) |  |
| 6 | `bas_damper` | Zone-T212 | 2 | unsure (U) |  |
| 7 | `bas_damper` | Zone-T117 | 2 | unsure (U) |  |
| 8 | `bas_reheat` | Zone-T212 | 2 | abnormal (E) | 0:30-1:00 |
| 9 | `bas_reheat` | Zone-T117 | 2 | abnormal (E) | 1:00-1:30 |
| 10 | `thermostat` | Zone-T212 | 11 | unsure (U) |  |
| 11 | `thermostat` | Zone-T117 | 11 | unsure (U) |  |
| 12 | `reheat_coil` | Zone-T212 | 16 | abnormal (E) | 3:15-5:15 |
| 13 | `reheat_coil` | Zone-T117 | 16 | abnormal (E) | 5:15-6:15 |

Technician's mapped checks the tool never recommended: none. Checks the tool recommended that the technician did not do: bas_airflow, bas_damper, bas_static, bas_zone, thermostat.

Air handler belief at the end (ok / fan off / low static): AHU-1: 100% / 0% / 0%

### k = 12: complaints (probability mass on the accepted causes, before -> after)

| complaint | accepted | before | after | tool's leading cause | concluded | wrong and confident |
|---|---|---|---|---|---|---|
| Zone-T212 | reheat_fail | 9% | 94% | reheat_fail 94% | no | no |
| Zone-T117 | reheat_fail, other | 16% | 95% | reheat_fail 94% | no | no |

| # | check | for | min | answer | basis |
|---|---|---|---|---|---|
| 1 | `bas_zone` | Zone-T212 | 2 | unsure (U) |  |
| 2 | `bas_zone` | Zone-T117 | 2 | unsure (U) |  |
| 3 | `bas_airflow` | Zone-T212 | 2 | unsure (U) |  |
| 4 | `bas_airflow` | Zone-T117 | 2 | unsure (U) |  |
| 5 | `bas_damper` | Zone-T212 | 2 | unsure (U) |  |
| 6 | `bas_damper` | Zone-T117 | 2 | unsure (U) |  |
| 7 | `bas_reheat` | Zone-T212 | 2 | abnormal (E) | 0:30-1:00 |
| 8 | `bas_reheat` | Zone-T117 | 2 | abnormal (E) | 1:00-1:30 |
| 9 | `thermostat` | Zone-T212 | 11 | unsure (U) |  |
| 10 | `thermostat` | Zone-T117 | 11 | unsure (U) |  |
| 11 | `reheat_coil` | Zone-T212 | 16 | abnormal (E) | 3:15-5:15 |
| 12 | `reheat_coil` | Zone-T117 | 16 | abnormal (E) | 5:15-6:15 |

Technician's mapped checks the tool never recommended: none. Checks the tool recommended that the technician did not do: bas_airflow, bas_damper, bas_zone, thermostat.

Air handler belief at the end (ok / fan off / low static): AHU-1: 100% / 0% / 0%

