# Intake readiness: ornl_rtu_baseline

## Data coverage

- Period: 2020-09-12 to 2022-03-10 (544 calendar days), local standard time. Days with data: 14 in 14 separate chunk(s) (0.33 six-week windows' worth). Coverage below is judged over those days only.
- Points: 34 usable in the point list, 34 with trend data; 20 documented connections.
- Outdoor temperature: -2 to 30 C (5th-95th percentile 4 to 27 C). 
- NOTE: 14 days with data is less than one six-week window (42 days). That is enough to read the connections, but not to learn how a building behaves across weather.

## What each connection check can use

Channel = one kind of consistency test between two ends of a connection. Each channel cell = the fraction of the documented connections whose needed points are recorded, cover at least 50% of hours and vary beyond sensor noise. Status: FULL = all channels reach 80%; PARTIAL = some do; NOT TESTABLE = none do.

| connection | documented | channel 0 | channel 1 | channel 2 | status | what would unlock more |
|---|---|---|---|---|---|---|
| ahu_vav: which air handler supplies each VAV box | 10 | 0% | 0% | 0% | NOT TESTABLE | VAV `t_in` not recorded on 10 unit(s) (needed by ch 0); VAV `flow` not recorded on 10 unit(s) (needed by ch 1,2) |
| vav_zone: which room each VAV box serves | 10 | 0% | 100% | 0% | PARTIAL | VAV `flow` not recorded on 10 unit(s) (needed by ch 0,2) |

Note on `vav_zone`: even with every point recorded, ordinary operation cannot tell which box serves which room (Addendum 11: no better than chance in simulation). That check needs deliberate changes to the room setpoints (Addendum 13) or a box override; trends from commissioning tests that contain such changes are the useful data.

## Documentation and truth

| connection | documented | verified right | verified wrong | unknown |
|---|---|---|---|---|
| ahu_vav | 10 | 0 | 0 | 10 |
| vav_zone | 10 | 0 | 0 | 10 |

- No connection is marked verified: the data can be checked by the tool but not scored (we need verified-right and verified-wrong connections to measure accuracy).

## Does the data match the time the documentation was verified?

- as_built_date is missing: the date the connections were marked up / verified is unknown, so a later change to the building cannot be ruled out

## Data quality

- No point failed the coverage, range, sentinel or duplicate checks.

## Notes from loading

- no time zone in context.json: clock times are assumed to be one consistent zone; if daylight saving was applied, summer hours may sit one hour off the true diurnal cycle
