# Mortar bldg40 -> intake export

- Brick: 2 AHU, 87 VAV, 87 zones; 87 ahu_vav and 87 vav_zone documented connections.
- Exported points: 150 of 150 mapped (flow x69, oat x1, sat x2, temp x78).
- Windows (42 days each, chosen by coverage only): 2013-01-15 (coverage 95%), 2015-07-15 (coverage 95%)
- Assumptions: US customary units (degF, cfm), range-checked; UTC clock; one-minute data averaged to 15 minutes; zone temperature taken from the sensor attached to the zone or to the VAV that feeds it.

## Notes

- outdoor temperature taken from AHU01 `bldg40.AHU.AHU01.Outside Air Temp`
- window coverage was measured on 75 of 150 mapped streams (evenly spaced, sorted by id)
