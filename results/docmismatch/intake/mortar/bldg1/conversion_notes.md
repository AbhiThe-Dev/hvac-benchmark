# Mortar bldg1 -> intake export

- Brick: 2 AHU, 8 VAV, 8 zones; 8 ahu_vav and 8 vav_zone documented connections.
- Exported points: 27 of 27 mapped (flow x8, oat x1, sat x2, t_dis x8, temp x8).
- Windows (42 days each, chosen by coverage only): 2017-01-15 (coverage 100%), 2016-07-15 (coverage 93%)
- Assumptions: US customary units (degF, cfm), range-checked; UTC clock; one-minute data averaged to 15 minutes; zone temperature taken from the sensor attached to the zone or to the VAV that feeds it.

## Notes

- 8 VAV(s) had several candidate flow points (Supply_Air_Flow_Sensor, Air_Flow_Sensor); the first class was used (most specific)
- outdoor temperature taken from AHU01 `bldg1.AHU.AHU01.Outside Air Temp`
