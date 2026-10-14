# The live v2 tool against the real technician (Addendum 39)

Two real calls, n = 2. Steps are catalogue-check units. The technician's accepted causes are his own findings, so he cannot lose on accuracy by construction. Tool answers for checks the video does not show are drawn from the catalogue's own response model (home-field). Minutes are reported, not scored.

## Everything HVACR: office and cubicle area too cold in the morning, Trane VAV controls

**Technician:** 4 steps (5 if each complaint's check is counted separately), 4.5 video minutes to diagnosis, correct by construction. Verified in the video: No: 'they'll probably call tomorrow and say they're too hot' (15:00).

| tool, answers from the world | steps median (IQR) | tool / technician | P(tool steps <= technician's) | P(right on every complaint) | P(wrong and confident) | P(concluded) | catalogue min (median) | verdict |
|---|---|---|---|---|---|---|---|---|
| model draws, k = 2 | 11 (10-12) | 2.75 | 2% | 72% | 2% | 9% | 63 | TECHNICIAN FEWER STEPS |
| model draws, k = 6 (primary) | 11 (11-12) | 2.75 | 0% | 73% | 0% | 7% | 69 | TECHNICIAN FEWER STEPS |
| model draws, k = 12 | 10 (10-11) | 2.50 | 0% | 73% | 0% | 7% | 65 | TECHNICIAN FEWER STEPS |
| normal (one run, k = 6) | 21 | 5.25 | - | no | no | - | 158 | - |
| unsure (one run, k = 6) | 7 | 1.75 | - | yes | no | - | 32 | - |

First check the tool picks (primary): {'bas_static': 1000}. Checks it asks most often: {'bas_airflow': 1000, 'bas_static': 1000, 'bas_zone': 1000, 'thermostat': 1000, 'bas_damper': 981, 'bas_controller': 830, 'bas_hunting': 740, 'confirm_acts': 688}. On average 3.0 of its checks are answered by the video and 8.5 by the drawn world. Right per complaint: ['100%', '73%'].

## Nighthawk HVAC EP160: VAV electric heat not heating

**Technician:** 4 steps (4 if each complaint's check is counted separately), 4.25 video minutes to diagnosis, correct by construction. Verified in the video: Yes for T212: current restored after the fuse and wires were fixed (5:00-5:15); T117 pulling about 10 A, normal for its element (6:00).

| tool, answers from the world | steps median (IQR) | tool / technician | P(tool steps <= technician's) | P(right on every complaint) | P(wrong and confident) | P(concluded) | catalogue min (median) | verdict |
|---|---|---|---|---|---|---|---|---|
| model draws, k = 2 | 7 (7-7) | 1.75 | 0% | 99% | 1% | 1% | 14 | TECHNICIAN FEWER STEPS |
| model draws, k = 6 (primary) | 7 (7-7) | 1.75 | 0% | 99% | 0% | 1% | 14 | TECHNICIAN FEWER STEPS |
| model draws, k = 12 | 6 (6-6) | 1.50 | 0% | 100% | 0% | 1% | 12 | TECHNICIAN FEWER STEPS |
| normal (one run, k = 6) | 7 | 1.75 | - | yes | no | - | 14 | - |
| unsure (one run, k = 6) | 12 | 3.00 | - | yes | no | - | 56 | - |

First check the tool picks (primary): {'bas_static': 1000}. Checks it asks most often: {'bas_airflow': 1000, 'bas_reheat': 1000, 'bas_static': 1000, 'bas_zone': 1000, 'reheat_coil': 176, 'bas_damper': 111, 'thermostat': 100, 'bas_hunting': 78}. On average 2.2 of its checks are answered by the video and 5.4 by the drawn world. Right per complaint: ['100%', '100%'].

