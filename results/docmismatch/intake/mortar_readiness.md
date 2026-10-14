# Mortar buildings: what their recorded points support (readiness only)

Each building is exported as two 42-day windows (chosen by data coverage only), US customary units assumed and range-checked, UTC clock, connections = the Brick model (not field-verified). Channel cells = share of the documented connections whose points are recorded, cover at least half the hours and vary beyond sensor noise. Per-building detail: `mortar/<bldg>/report.md`.

| building | AHU / VAV / zones | exported points | windows (start, coverage) | dropped | ahu_vav ch0/ch1/ch2 | vav_zone ch0/ch1/ch2 |
|---|---|---|---|---|---|---|
| bldg1 | 2 / 8 / 8 | 27 (flow x8, oat x1, sat x2, t_dis x8, temp x8) | 2017-01-15 (100%); 2016-07-15 (93%) | 0 | 0%/0%/0% (NOT TESTABLE) | 100%/0%/0% (PARTIAL) |
| bldg8 | 1 / 24 / 24 | 74 (flow x24, oat x1, sat x1, t_dis x24, temp x24) | 2017-01-15 (100%); 2015-07-15 (100%) | 0 | 0%/0%/0% (NOT TESTABLE) | 100%/100%/100% (FULL) |
| bldg27 | 1 / 17 / 17 | 36 (flow x17, oat x1, sat x1, temp x17) | 2017-01-15 (100%); 2016-07-15 (96%) | 0 | 0%/0%/0% (NOT TESTABLE) | 100%/0%/0% (PARTIAL) |
| bldg30 | 0 / 99 / 99 | 296 (flow x98, t_dis x99, temp x99) | 2017-01-15 (99%); 2017-07-15 (86%) | 1 | not documented | 96%/97%/96% (FULL) |
| bldg40 | 2 / 87 / 87 | 150 (flow x69, oat x1, sat x2, temp x78) | 2013-01-15 (95%); 2015-07-15 (95%) | 0 | 0%/0%/0% (NOT TESTABLE) | 70%/0%/0% (NOT TESTABLE) |
| bldg15 | 2 / 129 / 129 | 204 (flow x86, oat x1, sat x2, t_dis x27, temp x88) | 2017-01-15 (83%); 2017-07-15 (84%) | 39 | 0%/0%/0% (NOT TESTABLE) | 66%/21%/21% (NOT TESTABLE) |

**Erratum 2026-09-24:** `bldg30`'s 99 AHU -> VAV connections are missing from the table above because the converter did not recognise the alias class `AHU`; the correct `ahu_vav` entry for `bldg30` is 99 documented pairs, untestable (see Addendum 17 erratum).
