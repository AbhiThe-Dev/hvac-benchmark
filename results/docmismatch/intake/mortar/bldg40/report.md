# Intake readiness: mortar_bldg40

## Data coverage

- Period: 2013-01-15 to 2015-08-26 (953 calendar days), local standard time. Days with data: 84 in 2 separate chunk(s) (2.00 six-week windows' worth). Coverage below is judged over those days only.
- Points: 150 usable in the point list, 150 with trend data; 174 documented connections.
- Outdoor temperature: 0 to 40 C (5th-95th percentile 5 to 34 C). 

## What each connection check can use

Channel = one kind of consistency test between two ends of a connection. Each channel cell = the fraction of the documented connections whose needed points are recorded, cover at least 50% of hours and vary beyond sensor noise. Status: FULL = all channels reach 80%; PARTIAL = some do; NOT TESTABLE = none do.

| connection | documented | channel 0 | channel 1 | channel 2 | status | what would unlock more |
|---|---|---|---|---|---|---|
| ahu_vav: which air handler supplies each VAV box | 87 | 0% | 0% | 0% | NOT TESTABLE | VAV `t_in` not recorded on 87 unit(s) (needed by ch 0); VAV `flow` not recorded on 18 unit(s) (needed by ch 1,2); AHU `flow` not recorded on 2 unit(s) (needed by ch 1,2) |
| vav_zone: which room each VAV box serves | 87 | 70% | 0% | 0% | NOT TESTABLE | VAV `t_dis` not recorded on 87 unit(s) (needed by ch 1,2); VAV `flow` not recorded on 18 unit(s) (needed by ch 0,2); Zone `temp` not recorded on 9 unit(s) (needed by ch 0,1,2) |

Note on `vav_zone`: even with every point recorded, ordinary operation cannot tell which box serves which room (Addendum 11: no better than chance in simulation). That check needs deliberate changes to the room setpoints (Addendum 13) or a box override; trends from commissioning tests that contain such changes are the useful data.

## Documentation and truth

| connection | documented | verified right | verified wrong | unknown |
|---|---|---|---|---|
| ahu_vav | 87 | 0 | 0 | 87 |
| vav_zone | 87 | 0 | 0 | 87 |

- No connection is marked verified: the data can be checked by the tool but not scored (we need verified-right and verified-wrong connections to measure accuracy).

## Does the data match the time the documentation was verified?

- as_built_date is missing: the date the connections were marked up / verified is unknown, so a later change to the building cannot be ruled out

## Data quality

- `RM2061A.temp`: only 30% of hours have a value
- `RM2061B.temp`: only 33% of hours have a value
- `RM2061C.temp`: only 40% of hours have a value
- `RM2061D.temp`: only 38% of hours have a value
- `RM2061E.temp`: only 39% of hours have a value
- `RM2063_2_MIX.temp`: only 29% of hours have a value; longest gap 1008 h
- `RM2065_2.temp`: only 37% of hours have a value
