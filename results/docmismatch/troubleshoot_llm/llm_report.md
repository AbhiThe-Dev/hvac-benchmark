# A language model as the experienced technician (Addendum 33): a pilot

10 visits of each kind (30 visits) from Addendum 30's primary cell, each worked at T2 and T3 by the routine, the joint tool, my rule-based stand-in and a language model (Claude `sonnet`, one fresh session per visit and tier) working through a terminal. Identical answers to identical questions; the tool's own accountant charges the minutes. Simulation only, from the tool's own model family with placeholder numbers; a language model is not an experienced technician and nothing here is evidence about real technicians. About 10 visits per kind: wide intervals.

## Gates

| gate | result | detail |
|---|---|---|
| G1 answers | PASS | the answer table is deterministic and independent of question order on 12 sessions' questions |
| G2 accounting | PASS | 120 replays of fast_parent and the routine through the terminal: 0 differ in minutes or checks |
| G3 audit | PASS | 60 sessions audited; no breach |
| G4 completeness | PASS | 60 sessions; 0 ended without `finish` (scored as abandoned: []); 0 took no action |
| G5 partners | PASS | 0 of 60 re-run partner results differ from the stored ones |
| G6 sample | PASS | seed 33, 10 per kind, sample reproduced |

## Tier T2: minutes per visit / share of complaints diagnosed exactly right / wrong-and-confident / checks per visit (kind shares re-weighted to the cell's)

| policy | all visits (natural mix) | one complaint | several complaints, no shared cause | shared-cause visits |
|---|---|---|---|---|
| llm | 76 min / 82% / 16% / 8.8 | 51 min / 80% / 20% / 6.1 | 138 min / 80% / 15% / 16.0 | 67 min / 92% / 4% / 7.3 |
| tool_ticket_memo2 | 92 min / 84% / 0% / 9.5 | 67 min / 80% / 0% / 7.0 | 180 min / 85% / 0% / 18.8 | 42 min / 96% / 2% / 3.8 |
| tool_joint2 | 101 min / 84% / 0% / 10.0 | 67 min / 80% / 0% / 7.0 | 196 min / 85% / 0% / 19.1 | 74 min / 96% / 2% / 6.5 |
| fast_parent | 94 min / 62% / 38% / 9.7 | 69 min / 60% / 40% / 7.1 | 170 min / 50% / 50% / 17.8 | 62 min / 87% / 13% / 6.2 |

## Tier T3: minutes per visit / share of complaints diagnosed exactly right / wrong-and-confident / checks per visit (kind shares re-weighted to the cell's)

| policy | all visits (natural mix) | one complaint | several complaints, no shared cause | shared-cause visits |
|---|---|---|---|---|
| llm | 76 min / 79% / 5% / 16.3 | 33 min / 80% / 0% / 8.6 | 109 min / 75% / 10% / 22.0 | 175 min / 82% / 15% / 34.8 |
| tool_ticket_memo2 | 58 min / 87% / 0% / 11.3 | 42 min / 90% / 0% / 8.3 | 118 min / 75% / 0% / 22.6 | 18 min / 97% / 2% / 4.0 |
| tool_joint2 | 66 min / 90% / 0% / 11.9 | 42 min / 90% / 0% / 8.3 | 135 min / 85% / 0% / 24.1 | 39 min / 98% / 2% / 5.6 |
| fast_parent | 80 min / 60% / 40% / 11.6 | 72 min / 60% / 40% / 10.1 | 130 min / 40% / 60% / 19.3 | 27 min / 94% / 6% / 4.8 |

## Comparisons on the same visits (paired, bootstrap 95% intervals, Addendum 21 labels)

| comparison | tier | subset | d minutes | d accuracy | d wrong-and-confident | time / accuracy | label | break-even cost of a wrong diagnosis |
|---|---|---|---|---|---|---|---|---|
| P: LLM - routine (`tool_ticket_memo2`)  [PRIMARY] | T2 | all visits (natural mix) | -15.8 (-17%) [-28, -2] | -0.020 [-0.20, +0.15] | +0.158 | FASTER / SAME | IMPROVES | 802 min (first wins below) |
| P: LLM - routine (`tool_ticket_memo2`)  [PRIMARY] | T3 | all visits (natural mix) | +18.0 (+31%) [+7, +28] | -0.082 [-0.28, +0.11] | +0.048 | SLOWER / SAME | WORSE | second ahead on both |
| P: LLM - routine (`tool_ticket_memo2`)  [PRIMARY] | T2 | one complaint | -16.3 (-24%) [-32, +1] | +0.000 [-0.30, +0.30] | +0.200 | SAME / SAME | NEITHER | first ahead on both |
| P: LLM - routine (`tool_ticket_memo2`)  [PRIMARY] | T3 | one complaint | -9.2 (-22%) [-18, -1] | -0.100 [-0.40, +0.20] | +0.000 | FASTER / SAME | IMPROVES | 92 min (first wins below) |
| P: LLM - routine (`tool_ticket_memo2`)  [PRIMARY] | T2 | several complaints, no shared cause | -41.0 (-23%) [-60, -22] | -0.050 [-0.20, +0.10] | +0.150 | FASTER / SAME | IMPROVES | 820 min (first wins below) |
| P: LLM - routine (`tool_ticket_memo2`)  [PRIMARY] | T3 | several complaints, no shared cause | -9.4 (-8%) [-28, +8] | +0.000 [-0.20, +0.20] | +0.100 | SAME / SAME | NEITHER | first ahead on both |
| P: LLM - routine (`tool_ticket_memo2`)  [PRIMARY] | T2 | shared-cause visits | +25.7 (+62%) [-12, +71] | -0.042 [-0.10, +0.00] | +0.025 | SAME / SAME | NEITHER | second ahead on both |
| P: LLM - routine (`tool_ticket_memo2`)  [PRIMARY] | T3 | shared-cause visits | +157.1 (+883%) [+110, +205] | -0.150 [-0.27, -0.03] | +0.133 | SLOWER / LESS | WORSE | second ahead on both |
| Q: LLM - joint tool (`tool_joint2`) | T2 | all visits (natural mix) | -25.2 (-25%) [-39, -12] | -0.020 [-0.19, +0.15] | +0.158 | FASTER / SAME | IMPROVES | 1280 min (first wins below) |
| Q: LLM - joint tool (`tool_joint2`) | T3 | all visits (natural mix) | +10.2 (+16%) [+0, +21] | -0.111 [-0.32, +0.09] | +0.048 | SLOWER / SAME | WORSE | second ahead on both |
| Q: LLM - joint tool (`tool_joint2`) | T2 | one complaint | -16.3 (-24%) [-31, +2] | +0.000 [-0.30, +0.30] | +0.200 | SAME / SAME | NEITHER | first ahead on both |
| Q: LLM - joint tool (`tool_joint2`) | T3 | one complaint | -9.2 (-22%) [-18, -2] | -0.100 [-0.40, +0.20] | +0.000 | FASTER / SAME | IMPROVES | 92 min (first wins below) |
| Q: LLM - joint tool (`tool_joint2`) | T2 | several complaints, no shared cause | -57.2 (-29%) [-78, -37] | -0.050 [-0.20, +0.10] | +0.150 | FASTER / SAME | IMPROVES | 1144 min (first wins below) |
| Q: LLM - joint tool (`tool_joint2`) | T3 | several complaints, no shared cause | -26.0 (-19%) [-41, -13] | -0.100 [-0.30, +0.10] | +0.100 | FASTER / SAME | IMPROVES | 260 min (first wins below) |
| Q: LLM - joint tool (`tool_joint2`) | T2 | shared-cause visits | -6.4 (-9%) [-55, +35] | -0.042 [-0.10, +0.00] | +0.025 | SAME / SAME | NEITHER | 154 min (first wins below) |
| Q: LLM - joint tool (`tool_joint2`) | T3 | shared-cause visits | +135.8 (+347%) [+88, +187] | -0.167 [-0.30, -0.07] | +0.133 | SLOWER / LESS | WORSE | second ahead on both |
| R: LLM - fast_parent (my rule) | T2 | all visits (natural mix) | -17.8 (-19%) [-41, +4] | +0.201 [+0.06, +0.37] | -0.221 | SAME / MORE | IMPROVES | first ahead on both |
| R: LLM - fast_parent (my rule) | T3 | all visits (natural mix) | -3.8 (-5%) [-34, +24] | +0.185 [-0.03, +0.41] | -0.345 | SAME / SAME | NEITHER | first ahead on both |
| R: LLM - fast_parent (my rule) | T2 | one complaint | -18.1 (-26%) [-54, +14] | +0.200 [+0.00, +0.50] | -0.200 | SAME / SAME | NEITHER | first ahead on both |
| R: LLM - fast_parent (my rule) | T3 | one complaint | -38.8 (-54%) [-94, +6] | +0.200 [-0.20, +0.60] | -0.400 | SAME / SAME | NEITHER | first ahead on both |
| R: LLM - fast_parent (my rule) | T2 | several complaints, no shared cause | -31.7 (-19%) [-58, -7] | +0.300 [+0.10, +0.50] | -0.350 | FASTER / MORE | IMPROVES | first ahead on both |
| R: LLM - fast_parent (my rule) | T3 | several complaints, no shared cause | -21.6 (-17%) [-55, +8] | +0.350 [+0.05, +0.65] | -0.500 | SAME / MORE | IMPROVES | first ahead on both |
| R: LLM - fast_parent (my rule) | T2 | shared-cause visits | +5.1 (+8%) [-24, +35] | +0.050 [+0.00, +0.15] | -0.092 | SAME / SAME | NEITHER | 102 min (first wins above) |
| R: LLM - fast_parent (my rule) | T3 | shared-cause visits | +148.2 (+555%) [+96, +200] | -0.125 [-0.27, +0.00] | +0.092 | SLOWER / SAME | WORSE | second ahead on both |
| S: routine - fast_parent (Addendum 31's comparison on this sample) | T2 | all visits (natural mix) | -2.0 (-2%) [-23, +16] | +0.221 [+0.09, +0.39] | -0.379 | SAME / MORE | IMPROVES | first ahead on both |
| S: routine - fast_parent (Addendum 31's comparison on this sample) | T3 | all visits (natural mix) | -21.7 (-27%) [-51, +3] | +0.268 [+0.09, +0.46] | -0.393 | SAME / MORE | IMPROVES | first ahead on both |
| S: routine - fast_parent (Addendum 31's comparison on this sample) | T2 | one complaint | -1.8 (-3%) [-34, +28] | +0.200 [+0.00, +0.50] | -0.400 | SAME / SAME | NEITHER | first ahead on both |
| S: routine - fast_parent (Addendum 31's comparison on this sample) | T3 | one complaint | -29.6 (-41%) [-73, +8] | +0.300 [+0.00, +0.60] | -0.400 | SAME / SAME | NEITHER | first ahead on both |
| S: routine - fast_parent (Addendum 31's comparison on this sample) | T2 | several complaints, no shared cause | +9.3 (+5%) [-18, +40] | +0.350 [+0.15, +0.55] | -0.500 | SAME / MORE | IMPROVES | 27 min (first wins above) |
| S: routine - fast_parent (Addendum 31's comparison on this sample) | T3 | several complaints, no shared cause | -12.2 (-9%) [-51, +33] | +0.350 [+0.05, +0.60] | -0.600 | SAME / MORE | IMPROVES | first ahead on both |
| S: routine - fast_parent (Addendum 31's comparison on this sample) | T2 | shared-cause visits | -20.6 (-33%) [-61, +2] | +0.092 [+0.00, +0.26] | -0.117 | SAME / SAME | NEITHER | first ahead on both |
| S: routine - fast_parent (Addendum 31's comparison on this sample) | T3 | shared-cause visits | -8.9 (-33%) [-26, +2] | +0.025 [+0.00, +0.07] | -0.042 | SAME / SAME | NEITHER | first ahead on both |

## What the language model did

Sessions abandoned (stopped without `finish`): 0.

| tier | checks per visit | first check at the air handler (all / shared) | 'confident' share of conclusions | most used checks |
|---|---|---|---|---|
| T2 | 9.8 | 33% / 90% | 91% | override_diffuser 53, design_load 31, thermostat 26, flow_hood 25, confirm_acts 23, static_at_box 23 |
| T3 | 21.8 | 43% / 100% | 81% | bas_airflow 77, bas_damper 69, bas_controller 63, override_diffuser 62, bas_zone 55, max_airflow 41 |

## Predictions (written before the run; each strict)

| prediction | holds | values |
|---|---|---|
| P1 | holds | T3, LLM - routine: +18.0 min (+31%) |
| P2 | does not hold | T2, LLM - routine: -17% |
| P3 | holds | accuracy LLM - routine: T2 -0.020, T3 -0.082 |
| P4 | holds | wrong-and-confident LLM - routine: T2 +0.158, T3 +0.048 |
| P5 | holds | shared visits, minutes LLM - routine: T2 +25.7, T3 +157.1 |
| P6 | holds | accuracy LLM - fast_parent: T2 +0.201, T3 +0.185 |
| P7 | does not hold | T2, LLM - fast_parent: -17.8 min |
| P8 | holds | first check at the air handler, shared visits: T2 90%, T3 100% |

## Frozen decision: T2: THE LLM TECHNICIAN IS FASTER (accuracy SAME); T3: THE ROUTINE IS FASTER (accuracy SAME)
