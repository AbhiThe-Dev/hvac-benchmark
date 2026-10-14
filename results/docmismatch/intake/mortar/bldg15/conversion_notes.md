# Mortar bldg15 -> intake export

- Brick: 2 AHU, 129 VAV, 129 zones; 129 ahu_vav and 129 vav_zone documented connections.
- Exported points: 204 of 243 mapped (flow x86, oat x1, sat x2, t_dis x27, temp x88).
- Windows (42 days each, chosen by coverage only): 2017-01-15 (coverage 83%), 2017-07-15 (coverage 84%)
- Assumptions: US customary units (degF, cfm), range-checked; UTC clock; one-minute data averaged to 15 minutes; zone temperature taken from the sensor attached to the zone or to the VAV that feeds it.

## Dropped (not exported)

- VAVRM1005.flow (no values in the chosen windows)
- VAVRM1006.flow (no values in the chosen windows)
- VAVRM1106.flow (no values in the chosen windows)
- VAVRM1109.flow (no values in the chosen windows)
- VAVRM1116.flow (no values in the chosen windows)
- VAVRM1120.flow (no values in the chosen windows)
- VAVRM1130.flow (no values in the chosen windows)
- VAVRM1150.flow (no values in the chosen windows)
- VAVRM1200.flow (no values in the chosen windows)
- VAVRM1200A.flow (no values in the chosen windows)
- VAVRM1208.flow (no values in the chosen windows)
- VAVRM1208.t_dis (no values in the chosen windows)
- VAVRM1209.flow (no values in the chosen windows)
- VAVRM1211.flow (no values in the chosen windows)
- VAVRM1215.flow (no values in the chosen windows)
- VAVRM1219.flow (no values in the chosen windows)
- VAVRM1223.flow (no values in the chosen windows)
- RM1005_MIX.temp (no values in the chosen windows)
- RM1006_MIX.temp (no values in the chosen windows)
- RM1101B.temp (no values in the chosen windows)
- RM1101C.temp (no values in the chosen windows)
- RM1101N1.temp (no values in the chosen windows)
- RM1101N2.temp (no values in the chosen windows)
- RM1101S1.temp (no values in the chosen windows)
- RM1101S2.temp (no values in the chosen windows)
- RM1102.temp (no values in the chosen windows)
- RM1106_MIX.temp (no values in the chosen windows)
- RM1109_MIX.temp (no values in the chosen windows)
- RM1116_MIX.temp (no values in the chosen windows)
- RM1128S.temp (no values in the chosen windows)
- RM1130_MIX.temp (no values in the chosen windows)
- RM1200A_MIX.temp (no values in the chosen windows)
- RM1200_MIX.temp (no values in the chosen windows)
- RM1208_MIX.temp (no values in the chosen windows)
- RM1209_MIX.temp (no values in the chosen windows)
- RM1211_MIX.temp (no values in the chosen windows)
- RM1215_MIX.temp (no values in the chosen windows)
- RM1219_MIX.temp (no values in the chosen windows)
- RM1223_MIX.temp (no values in the chosen windows)

## Notes

- 102 VAV(s) had several candidate flow points (Supply_Air_Flow_Sensor, Air_Flow_Sensor); the first class was used (most specific)
- outdoor temperature taken from AHU01 `bldg15.AHU.AHU01.Outside Air Temp Virtual`
- window coverage was measured on 61 of 243 mapped streams (evenly spaced, sorted by id)
