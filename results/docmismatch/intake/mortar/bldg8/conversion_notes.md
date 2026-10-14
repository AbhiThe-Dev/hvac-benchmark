# Mortar bldg8 -> intake export

- Brick: 1 AHU, 24 VAV, 24 zones; 24 ahu_vav and 24 vav_zone documented connections.
- Exported points: 74 of 74 mapped (flow x24, oat x1, sat x1, t_dis x24, temp x24).
- Windows (42 days each, chosen by coverage only): 2017-01-15 (coverage 100%), 2015-07-15 (coverage 100%)
- Assumptions: US customary units (degF, cfm), range-checked; UTC clock; one-minute data averaged to 15 minutes; zone temperature taken from the sensor attached to the zone or to the VAV that feeds it.

## Notes

- outdoor temperature taken from AHU01 `bldg8.AHU.AHU01.Outside Air Temp`
