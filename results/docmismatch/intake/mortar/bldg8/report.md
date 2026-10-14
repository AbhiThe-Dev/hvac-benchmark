# Intake readiness: mortar_bldg8

## Data coverage

- Period: 2015-07-15 to 2017-02-26 (592 calendar days), local standard time. Days with data: 84 in 2 separate chunk(s) (2.00 six-week windows' worth). Coverage below is judged over those days only.
- Points: 74 usable in the point list, 74 with trend data; 48 documented connections.
- Outdoor temperature: 4 to 36 C (5th-95th percentile 7 to 30 C). 

## What each connection check can use

Channel = one kind of consistency test between two ends of a connection. Each channel cell = the fraction of the documented connections whose needed points are recorded, cover at least 50% of hours and vary beyond sensor noise. Status: FULL = all channels reach 80%; PARTIAL = some do; NOT TESTABLE = none do.

| connection | documented | channel 0 | channel 1 | channel 2 | status | what would unlock more |
|---|---|---|---|---|---|---|
| ahu_vav: which air handler supplies each VAV box | 24 | 0% | 0% | 0% | NOT TESTABLE | VAV `t_in` not recorded on 24 unit(s) (needed by ch 0); AHU `flow` not recorded on 1 unit(s) (needed by ch 1,2) |
| vav_zone: which room each VAV box serves | 24 | 100% | 100% | 100% | FULL |  |

Note on `vav_zone`: even with every point recorded, ordinary operation cannot tell which box serves which room (Addendum 11: no better than chance in simulation). That check needs deliberate changes to the room setpoints (Addendum 13) or a box override; trends from commissioning tests that contain such changes are the useful data.

## Documentation and truth

| connection | documented | verified right | verified wrong | unknown |
|---|---|---|---|---|
| ahu_vav | 24 | 0 | 0 | 24 |
| vav_zone | 24 | 0 | 0 | 24 |

- No connection is marked verified: the data can be checked by the tool but not scored (we need verified-right and verified-wrong connections to measure accuracy).

## Does the data match the time the documentation was verified?

- as_built_date is missing: the date the connections were marked up / verified is unknown, so a later change to the building cannot be ruled out

## Data quality

- No point failed the coverage, range, sentinel or duplicate checks.
