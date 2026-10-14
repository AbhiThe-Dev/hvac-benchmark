# Mortar bldg27 -> intake export

- Brick: 1 AHU, 17 VAV, 17 zones; 17 ahu_vav and 17 vav_zone documented connections.
- Exported points: 36 of 36 mapped (flow x17, oat x1, sat x1, temp x17).
- Windows (42 days each, chosen by coverage only): 2017-01-15 (coverage 100%), 2016-07-15 (coverage 96%)
- Assumptions: US customary units (degF, cfm), range-checked; UTC clock; one-minute data averaged to 15 minutes; zone temperature taken from the sensor attached to the zone or to the VAV that feeds it.

## Notes

- outdoor temperature taken from AC07 `bldg27.AHU.AC07.Outside Air Temp Virtual`
