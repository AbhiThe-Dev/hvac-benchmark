# Intake readiness: mortar_bldg15

## Data coverage

- Period: 2017-01-15 to 2017-08-26 (223 calendar days), local standard time. Days with data: 84 in 2 separate chunk(s) (2.00 six-week windows' worth). Coverage below is judged over those days only.
- Points: 204 usable in the point list, 204 with trend data; 258 documented connections.
- Outdoor temperature: -6 to 38 C (5th-95th percentile 6 to 32 C). 

## What each connection check can use

Channel = one kind of consistency test between two ends of a connection. Each channel cell = the fraction of the documented connections whose needed points are recorded, cover at least 50% of hours and vary beyond sensor noise. Status: FULL = all channels reach 80%; PARTIAL = some do; NOT TESTABLE = none do.

| connection | documented | channel 0 | channel 1 | channel 2 | status | what would unlock more |
|---|---|---|---|---|---|---|
| ahu_vav: which air handler supplies each VAV box | 129 | 0% | 0% | 0% | NOT TESTABLE | VAV `t_in` not recorded on 129 unit(s) (needed by ch 0); VAV `flow` not recorded on 43 unit(s) (needed by ch 1,2); AHU `flow` not recorded on 2 unit(s) (needed by ch 1,2) |
| vav_zone: which room each VAV box serves | 129 | 66% | 21% | 21% | NOT TESTABLE | VAV `t_dis` not recorded on 102 unit(s) (needed by ch 1,2); VAV `flow` not recorded on 43 unit(s) (needed by ch 0,2); Zone `temp` not recorded on 41 unit(s) (needed by ch 0,1,2) |

Note on `vav_zone`: even with every point recorded, ordinary operation cannot tell which box serves which room (Addendum 11: no better than chance in simulation). That check needs deliberate changes to the room setpoints (Addendum 13) or a box override; trends from commissioning tests that contain such changes are the useful data.

## Documentation and truth

| connection | documented | verified right | verified wrong | unknown |
|---|---|---|---|---|
| ahu_vav | 129 | 0 | 0 | 129 |
| vav_zone | 129 | 0 | 0 | 129 |

- No connection is marked verified: the data can be checked by the tool but not scored (we need verified-right and verified-wrong connections to measure accuracy).

## Does the data match the time the documentation was verified?

- as_built_date is missing: the date the connections were marked up / verified is unknown, so a later change to the building cannot be ruled out

## Data quality

- `RM1120.temp`: only 78% of hours have a value; longest gap 441 h
- `VAVRM1128N.flow`: only 50% of hours have a value; longest gap 1008 h
- `RM1128N.temp`: only 50% of hours have a value; longest gap 1008 h
