# Mortar bldg30 -> intake export

- Brick: 0 AHU, 99 VAV, 99 zones; 0 ahu_vav and 99 vav_zone documented connections.
- Exported points: 296 of 297 mapped (flow x98, t_dis x99, temp x99).
- Windows (42 days each, chosen by coverage only): 2017-01-15 (coverage 99%), 2017-07-15 (coverage 86%)
- Assumptions: US customary units (degF, cfm), range-checked; UTC clock; one-minute data averaged to 15 minutes; zone temperature taken from the sensor attached to the zone or to the VAV that feeds it.

## Dropped (not exported)

- VAV_2-4-24.flow (90th percentile 1.97 outside 5-20000 cfm: unit implausible)

## Notes

- no AHU outdoor-air temperature point with data: no Weather series (a pool cannot be built without one)
- window coverage was measured on 75 of 297 mapped streams (evenly spaced, sorted by id)
