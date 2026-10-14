# Zone temperature setpoints in the Mortar buildings: a descriptive look (exploratory)

Reads only the setpoint streams (no relationship with any box or zone measurement is computed). Samples outside 45-95 (degF assumed) are dropouts and treated as missing. Change event = a step larger than 0.05 between consecutive valid samples. INDIVIDUAL = at most 10% of the other zones change within +-15 min of the event; SHARED = at least 50% do (a schedule); MIXED = in between; '?' = fewer than half of the other zones were reporting. Whole record of each building, UTC clock.

## bldg1: 8 zone setpoint streams

- Labels: e.g. `bldg1.ZONE.AHU01.RM107A.Zone Air Temp Setpoint` and `bldg1.ZONE.AHU01.RM107B.Zone Air Temp Setpoint`.
- Record: median 1.5 years per stream, median sampling step 15 min; samples outside 45-95 (dropouts) removed: median 0.0% (max 0.0%); distinct values per stream: median 5 (min 4, max 5); share of samples at a stream's three most common values: median 82%; setpoint range 60.0 to 85.0.
- Change events: 5729 in total (716 per stream, 465 per stream-year). Shared with other zones: 4878 (85%); individual: 275 (5%); mixed: 576 (10%); unclassifiable: 0 (0%).
- Robustness, +-1 hour instead of +-15 min: individual 228 (4%), shared 4915 (86%).
- Hour of day (UTC) of the individual events: the three busiest hours hold 34% of them (uniform would be 12.5%).
- Individual events per zone over the whole record: median 20, quartiles 7-42, min 3, max 122; zones with none: 0 of 8; per zone-year: median 13.3.
- Size of individual changes (|step|): median 4.00, 90th percentile 6.00.

## bldg27: 17 zone setpoint streams

- Labels: e.g. `bldg27.ZONE.AC07.RM050.Zone Air Temp Setpoint` and `bldg27.ZONE.AC07.RM055N.Zone Air Temp Setpoint`.
- Record: median 3.3 years per stream, median sampling step 15 min; samples outside 45-95 (dropouts) removed: median 0.0% (max 0.0%); distinct values per stream: median 114 (min 101, max 124); share of samples at a stream's three most common values: median 94%; setpoint range 65.0 to 82.0.
- Change events: 52430 in total (3084 per stream, 932 per stream-year). Shared with other zones: 37836 (72%); individual: 5406 (10%); mixed: 9183 (18%); unclassifiable: 5 (0%).
- Robustness, +-1 hour instead of +-15 min: individual 2960 (6%), shared 39719 (76%).
- Hour of day (UTC) of the individual events: the three busiest hours hold 18% of them (uniform would be 12.5%).
- Individual events per zone over the whole record: median 289, quartiles 134-423, min 10, max 907; zones with none: 0 of 17; per zone-year: median 87.3.
- Size of individual changes (|step|): median 2.50, 90th percentile 4.00.

## bldg40: 66 zone setpoint streams

- Labels: e.g. `bldg40.ZONE.AHU01.RM1001.Zone Air Temp Setpoint` and `bldg40.ZONE.AHU01.RM1003_1.Zone Air Temp Setpoint`.
- Record: median 6.8 years per stream, median sampling step 15 min; samples outside 45-95 (dropouts) removed: median 0.0% (max 0.0%); distinct values per stream: median 3 (min 1, max 42); share of samples at a stream's three most common values: median 100%; setpoint range 55.0 to 90.0.
- Change events: 68245 in total (1034 per stream, 153 per stream-year). Shared with other zones: 0 (0%); individual: 40507 (59%); mixed: 27707 (41%); unclassifiable: 31 (0%).
- Robustness, +-1 hour instead of +-15 min: individual 38276 (56%), shared 0 (0%).
- Hour of day (UTC) of the individual events: the three busiest hours hold 15% of them (uniform would be 12.5%).
- Individual events per zone over the whole record: median 10, quartiles 1-130, min 0, max 20152; zones with none: 16 of 66; per zone-year: median 1.6.
- Size of individual changes (|step|): median 0.25, 90th percentile 3.00.

## bldg15: 92 zone setpoint streams

- Labels: e.g. `bldg15.ZONE.AHU01.RM1005_MIX.Zone Air Temp Setpoint` and `bldg15.ZONE.AHU01.RM1006_MIX.Zone Air Temp Setpoint`.
- Record: median 3.3 years per stream, median sampling step 15 min; samples outside 45-95 (dropouts) removed: median 0.0% (max 0.0%); distinct values per stream: median 6 (min 2, max 13); share of samples at a stream's three most common values: median 87%; setpoint range 55.0 to 90.0.
- Change events: 603055 in total (6555 per stream, 1958 per stream-year). Shared with other zones: 156531 (26%); individual: 70638 (12%); mixed: 375680 (62%); unclassifiable: 206 (0%).
- Robustness, +-1 hour instead of +-15 min: individual 40532 (7%), shared 203532 (34%).
- Hour of day (UTC) of the individual events: the three busiest hours hold 21% of them (uniform would be 12.5%).
- Individual events per zone over the whole record: median 287, quartiles 133-621, min 14, max 9351; zones with none: 0 of 92; per zone-year: median 85.9.
- Size of individual changes (|step|): median 6.00, 90th percentile 8.00.
