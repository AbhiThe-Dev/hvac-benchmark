# Intake readiness: mortar_bldg30

## Data coverage

- Period: 2017-01-15 to 2017-08-26 (223 calendar days), local standard time. Days with data: 84 in 2 separate chunk(s) (2.00 six-week windows' worth). Coverage below is judged over those days only.
- Points: 296 usable in the point list, 296 with trend data; 99 documented connections.
- No outdoor-temperature point: the operating context cannot be computed (a Weather equipment with an `oat` point is required).

## What each connection check can use

Channel = one kind of consistency test between two ends of a connection. Each channel cell = the fraction of the documented connections whose needed points are recorded, cover at least 50% of hours and vary beyond sensor noise. Status: FULL = all channels reach 80%; PARTIAL = some do; NOT TESTABLE = none do.

| connection | documented | channel 0 | channel 1 | channel 2 | status | what would unlock more |
|---|---|---|---|---|---|---|
| vav_zone: which room each VAV box serves | 99 | 96% | 97% | 96% | FULL | Zone `temp` low coverage on 2 unit(s) (needed by ch 0,1,2); VAV `flow` low coverage on 1 unit(s) (needed by ch 0,2); VAV `flow` not recorded on 1 unit(s) (needed by ch 0,2) |

Note on `vav_zone`: even with every point recorded, ordinary operation cannot tell which box serves which room (Addendum 11: no better than chance in simulation). That check needs deliberate changes to the room setpoints (Addendum 13) or a box override; trends from commissioning tests that contain such changes are the useful data.

## Documentation and truth

| connection | documented | verified right | verified wrong | unknown |
|---|---|---|---|---|
| vav_zone | 99 | 0 | 0 | 99 |

- No connection is marked verified: the data can be checked by the tool but not scored (we need verified-right and verified-wrong connections to measure accuracy).

## Does the data match the time the documentation was verified?

- as_built_date is missing: the date the connections were marked up / verified is unknown, so a later change to the building cannot be ruled out

## Data quality

- `VAV_1-1-1.t_dis`: only 55% of hours have a value; longest gap 906 h
- `VAV_1-1-2.flow`: only 80% of hours have a value; longest gap 402 h
- `VAV_1-1-2.t_dis`: longest gap 66 h
- `VAV_1-1-3.flow`: only 75% of hours have a value; longest gap 505 h
- `VAV_1-1-4.flow`: longest gap 234 h
- `VAV_1-1-4.t_dis`: only 80% of hours have a value; longest gap 402 h
- `VAV_1-1-5.t_dis`: only 80% of hours have a value; longest gap 402 h
- `VAV_1-1-6.t_dis`: only 80% of hours have a value; longest gap 402 h
- `VAV_1-2-1.flow`: longest gap 337 h
- `VAV_1-2-2.flow`: longest gap 234 h
- `VAV_1-2-3.flow`: longest gap 234 h
- `VAV_1-2-5.flow`: only 75% of hours have a value; longest gap 505 h
- `VAV_1-2-6.flow`: longest gap 66 h
- `VAV_1-2-6.t_dis`: only 75% of hours have a value; longest gap 505 h
- `VAV_1-2-7.flow`: longest gap 66 h
- `VAV_1-2-7.t_dis`: longest gap 234 h
- `VAV_1-2-8.flow`: only 75% of hours have a value; longest gap 505 h
- `VAV_1-3-1.flow`: only 66% of hours have a value; longest gap 673 h
- `VAV_1-3-1.t_dis`: longest gap 103 h
- `VAV_1-3-2.t_dis`: longest gap 337 h
- `VAV_1-3-3.flow`: longest gap 234 h
- `VAV_1-3-3.t_dis`: longest gap 103 h
- `VAV_1-3-6.t_dis`: longest gap 103 h
- `VAV_1-3-8.flow`: only 75% of hours have a value; longest gap 402 h
- `VAV_1-3-9.flow`: longest gap 337 h
- `VAV_1-4-2.flow`: only 80% of hours have a value; longest gap 234 h
- `VAV_1-4-3.t_dis`: only 66% of hours have a value; longest gap 673 h
- `VAV_1-4-4.flow`: only 61% of hours have a value; longest gap 775 h
- `VAV_1-4-6.flow`: only 75% of hours have a value; longest gap 505 h
- `VAV_1-4-8.flow`: only 66% of hours have a value; longest gap 673 h
- `VAV_1-4-8.t_dis`: only 78% of hours have a value; longest gap 439 h
- `VAV_1-5-10.t_dis`: longest gap 103 h
- `VAV_1-5-12.t_dis`: only 78% of hours have a value; longest gap 439 h
- `VAV_1-5-13.flow`: longest gap 103 h
- `VAV_1-5-16.flow`: longest gap 66 h
- `VAV_1-5-16.t_dis`: longest gap 169 h
- `VAV_1-5-4.flow`: longest gap 66 h
- `VAV_1-5-5.flow`: longest gap 271 h
- `VAV_1-5-7.flow`: longest gap 337 h
- `VAV_1-5-7.t_dis`: longest gap 103 h
- `VAV_1-5-8.flow`: only 66% of hours have a value; longest gap 673 h
- `VAV_1-5-8.t_dis`: longest gap 169 h
- `VAV_2-1-11.flow`: longest gap 103 h
- `VAV_2-1-11.t_dis`: only 80% of hours have a value; longest gap 402 h
- `VAV_2-1-12.flow`: only 50% of hours have a value; longest gap 1008 h
- `VAV_2-1-13.t_dis`: only 78% of hours have a value; longest gap 439 h
- `VAV_2-1-15.flow`: only 69% of hours have a value; longest gap 607 h
- `VAV_2-1-16.t_dis`: only 75% of hours have a value; longest gap 505 h
- `VAV_2-1-18.flow`: longest gap 234 h
- `VAV_2-1-19.t_dis`: only 78% of hours have a value; longest gap 439 h
- `VAV_2-1-20.t_dis`: longest gap 66 h
- `VAV_2-2-13.t_dis`: longest gap 337 h
- `VAV_2-2-20.t_dis`: longest gap 103 h
- `VAV_2-3-14.t_dis`: longest gap 66 h
- `VAV_2-3-16.flow`: longest gap 66 h
- `VAV_2-3-16.t_dis`: only 71% of hours have a value; longest gap 570 h
- `VAV_2-3-18.t_dis`: longest gap 234 h
- `VAV_2-3-19.t_dis`: longest gap 337 h
- `VAV_2-3-20.t_dis`: longest gap 271 h
- `VAV_2-3-21.t_dis`: longest gap 234 h
- `VAV_2-3-22.flow`: longest gap 103 h
- `VAV_2-3-22.t_dis`: only 61% of hours have a value; longest gap 775 h
- `VAV_2-4-17A.t_dis`: longest gap 66 h
- `VAV_2-4-19.flow`: longest gap 66 h
- `VAV_2-4-20.t_dis`: only 78% of hours have a value; longest gap 439 h
- `VAV_2-4-21.t_dis`: longest gap 271 h
- `VAV_2-5-17B.t_dis`: longest gap 169 h
- `VAV_2-5-19.t_dis`: longest gap 103 h
- `VAV_2-5-20.flow`: longest gap 66 h
- `VAV_2-5-24.flow`: only 78% of hours have a value; longest gap 439 h
- `VAV_2-B-1.t_dis`: only 75% of hours have a value; longest gap 505 h
- `Zone_1-1-1.temp`: only 71% of hours have a value; longest gap 570 h
- `Zone_1-1-3.temp`: only 71% of hours have a value; longest gap 570 h
- `Zone_1-1-4.temp`: only 50% of hours have a value; longest gap 1008 h
- `Zone_1-1-6.temp`: only 66% of hours have a value; longest gap 673 h
- `Zone_1-1-8.temp`: only 78% of hours have a value; longest gap 439 h
- `Zone_1-2-1.temp`: only 78% of hours have a value; longest gap 439 h
- `Zone_1-2-2.temp`: longest gap 66 h
- `Zone_1-2-4.temp`: longest gap 234 h
- `Zone_1-2-5.temp`: only 78% of hours have a value; longest gap 439 h
- `Zone_1-2-7.temp`: longest gap 103 h
- `Zone_1-3-1.temp`: only 75% of hours have a value; longest gap 505 h
- `Zone_1-3-2.temp`: only 80% of hours have a value; longest gap 402 h
- `Zone_1-3-4.temp`: longest gap 169 h
- `Zone_1-3-8.temp`: only 71% of hours have a value; longest gap 570 h
- `Zone_1-4-2.temp`: only 66% of hours have a value; longest gap 673 h
- `Zone_1-4-4.temp`: only 80% of hours have a value; longest gap 337 h
- `Zone_1-4-5.temp`: longest gap 66 h
- `Zone_1-4-8.temp`: longest gap 271 h
- `Zone_1-5-1.temp`: only 75% of hours have a value; longest gap 505 h
- `Zone_1-5-10.temp`: longest gap 180 h; 714 out-of-range values
- `Zone_1-5-11.temp`: only 75% of hours have a value; longest gap 505 h
- `Zone_1-5-12.temp`: longest gap 234 h
- `Zone_1-5-16.temp`: only 50% of hours have a value; longest gap 1008 h
- `Zone_1-5-2.temp`: longest gap 66 h
- `Zone_1-5-3.temp`: longest gap 234 h
- `Zone_2-1-12.temp`: longest gap 66 h
- `Zone_2-1-14.temp`: longest gap 103 h
- `Zone_2-1-17.temp`: only 75% of hours have a value; longest gap 505 h
- `Zone_2-1-19.temp`: longest gap 337 h
- `Zone_2-1-20.temp`: only 75% of hours have a value; longest gap 505 h
- `Zone_2-1-27.temp`: longest gap 271 h
- `Zone_2-2-16.temp`: longest gap 103 h
- `Zone_2-2-18.temp`: longest gap 271 h
- `Zone_2-2-20.temp`: only 80% of hours have a value; longest gap 402 h
- `Zone_2-2-21.temp`: longest gap 66 h
- `Zone_2-2-22.temp`: longest gap 169 h
- `Zone_2-3-17.temp`: longest gap 103 h
- `Zone_2-3-18.temp`: longest gap 66 h
- `Zone_2-3-19.temp`: longest gap 234 h
- `Zone_2-3-20.temp`: longest gap 234 h
- `Zone_2-3-21.temp`: only 75% of hours have a value; longest gap 505 h
- `Zone_2-3-22.temp`: only 75% of hours have a value; longest gap 505 h
- `Zone_2-4-16.temp`: only 66% of hours have a value; longest gap 673 h
- `Zone_2-4-18.temp`: longest gap 234 h
- `Zone_2-4-21.temp`: only 75% of hours have a value; longest gap 505 h
- `Zone_2-5-19.temp`: only 66% of hours have a value; longest gap 673 h
- `Zone_2-5-20.temp`: longest gap 66 h
- `Zone_2-5-22.temp`: only 75% of hours have a value; longest gap 505 h
- `Zone_2-5-24.temp`: longest gap 337 h
- `Zone_2-B-1.temp`: longest gap 169 h
