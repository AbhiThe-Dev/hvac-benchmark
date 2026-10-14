# Intake readiness: synthetic_example

## Data coverage

- Period: 2021-01-04 to 2021-01-06 (2 calendar days), local standard time. Days with data: 2 in 1 separate chunk(s) (0.05 six-week windows' worth). Coverage below is judged over those days only.
- Points: 41 usable in the point list, 41 with trend data; 18 documented connections.
- Outdoor temperature: 8 to 12 C (5th-95th percentile 8 to 12 C). The engine was built on simulated buildings over a full year of weather; a narrow range limits what it can say.
- NOTE: 2 days with data is less than one six-week window (42 days). That is enough to read the connections, but not to learn how a building behaves across weather.

## What each connection check can use

Channel = one kind of consistency test between two ends of a connection. Each channel cell = the fraction of the documented connections whose needed points are recorded, cover at least 50% of hours and vary beyond sensor noise. Status: FULL = all channels reach 80%; PARTIAL = some do; NOT TESTABLE = none do.

| connection | documented | channel 0 | channel 1 | channel 2 | status | what would unlock more |
|---|---|---|---|---|---|---|
| ahu_sat: which air handler each supply-air-temperature sensor is on | 1 | 100% | 100% | 100% | FULL |  |
| ahu_vav: which air handler supplies each VAV box | 3 | 100% | 100% | 100% | FULL |  |
| branch_coil: which branch feeds each coil | 2 | 100% | 100% | 100% | FULL |  |
| coil_ahu: which air handler each coil belongs to | 2 | 100% | 100% | 100% | FULL |  |
| coil_vav: which VAV box each reheat coil belongs to | 1 | 100% | 100% | 100% | FULL |  |
| loop_branch: which water loop feeds each coil branch | 2 | 100% | 100% | 100% | FULL |  |
| loop_pump: which loop each pump belongs to | 1 | 100% | 100% | 100% | FULL |  |
| loop_source: which loop each boiler / chiller belongs to | 1 | 100% | 100% | 100% | FULL |  |
| vav_dat: which VAV box each discharge-air-temperature sensor is on | 2 | 100% | 100% | 100% | FULL |  |
| vav_zone: which room each VAV box serves | 3 | 100% | 100% | 100% | FULL |  |

Note on `vav_zone`: even with every point recorded, ordinary operation cannot tell which box serves which room (Addendum 11: no better than chance in simulation). That check needs deliberate changes to the room setpoints (Addendum 13) or a box override; trends from commissioning tests that contain such changes are the useful data.

## Documentation and truth

| connection | documented | verified right | verified wrong | unknown |
|---|---|---|---|---|
| ahu_sat | 1 | 1 | 0 | 0 |
| ahu_vav | 3 | 3 | 0 | 0 |
| branch_coil | 2 | 1 | 0 | 1 |
| coil_ahu | 2 | 2 | 0 | 0 |
| coil_vav | 1 | 1 | 0 | 0 |
| loop_branch | 2 | 1 | 1 | 0 |
| loop_pump | 1 | 1 | 0 | 0 |
| loop_source | 1 | 1 | 0 | 0 |
| vav_dat | 2 | 2 | 0 | 0 |
| vav_zone | 3 | 3 | 0 | 0 |

## Does the data match the time the documentation was verified?

- No conflict found between the trend period and the listed dates.

## Data quality

- No point failed the coverage, range, sentinel or duplicate checks.
