# The live v2 tool against the real technician, in working time at his own pace (Addendum 40)

Two real calls, n = 2. Working time only (travel and waiting excluded for both, unless stated). The tool's checks are priced at the technician's observed pace from `field_cases/pace_table.json`; his time is his video minutes to diagnosis. He is correct by construction; the tool's unshown checks are answered by the catalogue's own model (home-field). The physical pace rests on two observations of one check family from one video.

**Gates.** G1 frozen files match: yes (the run refuses otherwise). G2: pricing hand-checked (BAS 0.75 per read, reheat_coil 1.625 at CENTRAL, waiting added unscaled); all 30 checks classified (8 BAS, 22 physical) with a do_min. G3 reproduction of Addendum 39's stored worlds under S2: cold_morning: PASS (0 of 1000 differ); ep160: PASS (0 of 1000 differ). G4 (byte-identical under two hash seeds) is checked outside this script. G5: no error; asked checks carrying a data-fallback surcharge (excluded from the price): cold_morning 616, ep160 0.

## Everything HVACR: office and cubicle area too cold in the morning, Trane VAV controls

Technician: 4.5 minutes to diagnosis. Tool at k = 6: median 6 steps (4 BAS reads and 2 physical or in-room checks), right on every complaint in 99% of worlds. Catalogue minutes (not comparable): 30.

**Primary (k = 6, primary truth).**

| pace | tool working time, median (IQR) | tool / technician | worlds where the tool is faster | label |
|---|---|---|---|---|
| FAST | 2.60 (2.60-2.60) | 0.58 | 98% | TOOL FASTER |
| CENTRAL | 4.95 (4.95-4.95) | 1.10 | 0% | TIE |
| SLOW | 8.30 (8.30-8.30) | 1.84 | 0% | TECHNICIAN FASTER |

Robustness: **SENSITIVE TO PACE**.

**Sensitivities at CENTRAL.**

| variant | tool median (IQR) | ratio | worlds where the tool is faster | label |
|---|---|---|---|---|
| S2: Addendum 39's sampling truth, k = 6 | 9.31 (8.56-9.96) | 2.07 | 0% | TECHNICIAN FASTER |
| S3: waiting added, k = 6 | 4.95 (4.95-4.95) | 1.10 | 0% | TIE |
| padding k = 2 | 4.95 (4.95-4.95) | 1.10 | 0% | TIE |
| padding k = 12 | 4.20 (4.20-4.20) | 0.93 | 89% | TIE |

## Nighthawk HVAC EP160: VAV electric heat not heating

Technician: 4.25 minutes to diagnosis. Tool at k = 6: median 7 steps (7 BAS reads and 0 physical or in-room checks), right on every complaint in 99% of worlds. Catalogue minutes (not comparable): 14.

**Primary (k = 6, primary truth).**

| pace | tool working time, median (IQR) | tool / technician | worlds where the tool is faster | label |
|---|---|---|---|---|
| FAST | 3.50 (3.50-3.50) | 0.82 | 82% | TIE |
| CENTRAL | 5.25 (5.25-5.25) | 1.24 | 0% | TIE |
| SLOW | 8.75 (8.75-8.75) | 2.06 | 0% | TECHNICIAN FASTER |

Robustness: **SENSITIVE TO PACE**.

**Sensitivities at CENTRAL.**

| variant | tool median (IQR) | ratio | worlds where the tool is faster | label |
|---|---|---|---|---|
| S1: plus his physical confirmation (3.25 min) when the tool asks for none | 8.50 (8.50-8.50) | 2.00 | 0% | TECHNICIAN FASTER |
| S2: Addendum 39's sampling truth, k = 6 | 5.25 (5.25-5.25) | 1.24 | 0% | TIE |
| S3: waiting added, k = 6 | 5.25 (5.25-5.25) | 1.24 | 0% | TIE |
| padding k = 2 | 5.25 (5.25-5.25) | 1.24 | 0% | TIE |
| padding k = 12 | 4.50 (4.50-4.50) | 1.06 | 0% | TIE |

## Registered predictions (evaluated by the runner)

| | claim | held | detail |
|---|---|---|---|
| P1 | EP160, CENTRAL: label is TIE | yes | label TIE, ratio 1.235 |
| P2 | cold-morning, CENTRAL, primary truth: TIE or TECHNICIAN FASTER | yes | label TIE, ratio 1.100 |
| P3 | no case is TOOL FASTER at CENTRAL | yes | - |
| P4 | EP160 SENSITIVE TO PACE (not TECHNICIAN FASTER at FAST, TECHNICIAN FASTER at SLOW) | yes | FAST TIE, SLOW TECHNICIAN FASTER, SENSITIVE TO PACE |
| P5 | S1 (EP160) CENTRAL ratio >= 1.25 | yes | ratio 2.000, median 8.50 min |
| P6 | share of worlds where the tool is faster is under 50% at CENTRAL, both cases | yes | cold-morning 0%, EP160 0% |
| P7 | tool right on every complaint in >= 90% of worlds, both cases | yes | cold-morning 99%, EP160 99% |
| P8 | S2 cold-morning, CENTRAL: TECHNICIAN FASTER | yes | label TECHNICIAN FASTER, ratio 2.069 |
