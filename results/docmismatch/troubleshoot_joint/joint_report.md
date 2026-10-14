# Investigating several complaints together (Addendum 30)

A synthetic well-documented building (3 air handlers x 8 boxes and rooms); visits with one or several complaints drawn from a generative model; 18 cells, 1000 events each, both tiers on the same events. Seven policies: the v1 tool ticket by ticket (`tool_ticket`; `tool_ticket_nb` with the neighbour-informed prior; `tool_ticket_memo` which also reuses air handler readings), the joint session (`tool_joint`, and `tool_joint_la2` with two-step look-ahead), and two stand-ins that are MY CONSTRUCTIONS (`fast_ticket`, `fast_parent`). Everything is simulated from the tool's own model family with placeholder numbers; nothing here is evidence about real technicians, buildings, or how often shared causes happen.

## Gates

| gate | result | detail |
|---|---|---|
| G1 exactness | PASS | 200 random groups: largest difference from brute-force enumeration 5.33e-15 |
| G2 code path | PASS | 50 single-complaint events: 0 differ from simulate_v1; scripted joint transcript costs 37 minutes (hand sum 37) |
| G3 replay | PASS | 540 replayed events: 0 differ |
| G4 reproducibility | PASS | cell 0: 0 policy/tier series differ in the first 30 events |
| G5 completeness and pairing | PASS | 18 cells, every policy at both tiers on identical events |
| G6 world sanity | PASS | shared-event share rises with f in every (map, rel) that has all three levels: rare 5%, assumed 15%, common 37% |

## What the visits look like in the primary cell (shared assumed / M0 / R0)

Mean complaints per visit 2.11; visits by kind: all 1000, shared 172, multi 255, single 573 (of 1000).


## Primary cell, tier T2: minutes per visit / share of complaints diagnosed correctly / wrong-and-confident / checks per visit

| policy | all events | shared-cause | several, no shared cause | one complaint |
|---|---|---|---|---|
| tool_ticket | 151 min / 78% / 0.6% / 16.3 | 296 min / 87% / 0.1% / 34.6 | 194 min / 78% / 0.8% / 20.1 | 89 min / 76% / 0.7% / 9.1 |
| tool_ticket_nb | 120 min / 80% / 1.3% / 12.3 | 131 min / 94% / 1.6% / 13.7 | 194 min / 77% / 0.9% / 20.0 | 84 min / 77% / 1.4% / 8.4 |
| tool_ticket_memo | 114 min / 78% / 1.0% / 11.3 | 97 min / 93% / 1.7% / 8.5 | 189 min / 75% / 2.2% / 19.3 | 85 min / 75% / 0.2% / 8.5 |
| tool_joint | 124 min / 80% / 0.8% / 11.8 | 128 min / 97% / 0.5% / 10.3 | 210 min / 77% / 0.7% / 20.0 | 85 min / 76% / 0.9% / 8.6 |
| tool_joint_la2 | 115 min / 79% / 0.6% / 12.1 | 115 min / 96% / 0.4% / 10.5 | 198 min / 78% / 0.5% / 20.6 | 79 min / 75% / 0.7% / 8.8 |
| fast_ticket | 190 min / 46% / 54.3% / 19.0 | 620 min / 19% / 81.1% / 60.0 | 161 min / 52% / 48.1% / 16.9 | 73 min / 51% / 49.0% / 7.6 |
| fast_parent | 104 min / 57% / 42.9% / 10.7 | 113 min / 80% / 19.9% / 11.0 | 164 min / 49% / 50.6% / 17.2 | 75 min / 54% / 46.4% / 7.8 |

## Primary cell, tier T3: minutes per visit / share of complaints diagnosed correctly / wrong-and-confident / checks per visit

| policy | all events | shared-cause | several, no shared cause | one complaint |
|---|---|---|---|---|
| tool_ticket | 93 min / 77% / 1.3% / 17.9 | 225 min / 86% / 2.0% / 36.7 | 109 min / 77% / 1.0% / 23.2 | 46 min / 75% / 1.2% / 9.9 |
| tool_ticket_nb | 68 min / 83% / 1.4% / 13.3 | 62 min / 95% / 2.7% / 13.2 | 113 min / 79% / 0.8% / 22.1 | 49 min / 81% / 1.2% / 9.4 |
| tool_ticket_memo | 64 min / 83% / 0.7% / 12.3 | 43 min / 95% / 2.4% / 7.9 | 113 min / 81% / 0.7% / 22.1 | 48 min / 81% / 0.2% / 9.3 |
| tool_joint | 71 min / 85% / 0.9% / 12.8 | 55 min / 96% / 2.8% / 8.7 | 131 min / 84% / 1.0% / 23.2 | 50 min / 81% / 0.3% / 9.4 |
| tool_joint_la2 | 71 min / 84% / 1.3% / 14.2 | 59 min / 97% / 1.7% / 12.0 | 129 min / 84% / 2.2% / 24.0 | 48 min / 79% / 0.7% / 10.5 |
| fast_ticket | 129 min / 44% / 55.9% / 18.1 | 372 min / 27% / 72.8% / 48.1 | 132 min / 50% / 49.9% / 19.9 | 55 min / 46% / 53.6% / 8.4 |
| fast_parent | 72 min / 54% / 46.4% / 11.1 | 52 min / 76% / 24.0% / 8.5 | 124 min / 50% / 49.7% / 19.2 | 54 min / 48% / 51.7% / 8.3 |

## Every comparison over the cells

Labels are Addendum 21's (IMPROVES / WORSE / TRADE / NEITHER at 5% minutes and 0.02 accuracy, paired 95% intervals) for the FIRST policy minus the second on the same events; TRADE in brackets: faster but less accurate (F/L) or slower but more accurate (S/M). SAFETY REG / GAIN = share of cells where the first policy's wrong-and-confident rate is at least 0.02 higher / lower with the interval clear of 0. The last columns are the primary cell's deltas and, for E and F, the break-even cost of a wrong diagnosis.

| comparison | tier | subset | cells | IMPROVES | WORSE | TRADE (F/L, S/M) | NEITHER | SAFETY REG / GAIN | primary: d minutes | d accuracy | d wrong-and-confident | break-even |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A: joint - ticket (what exists today) | T2 | all events | 18 | 83% | 0% | 0% (0%, 0%) | 17% | 0% / 0% | -27.0 (-18%) | +0.015 | +0.001 |  |
| A: joint - ticket (what exists today) | T3 | all events | 18 | 83% | 0% | 11% (0%, 11%) | 6% | 17% / 0% | -21.4 (-23%) | +0.072 | -0.004 |  |
| A: joint - ticket (what exists today) | T2 | shared-cause events (two or more complaints from one upstream fault) | 18 | 100% | 0% | 0% (0%, 0%) | 0% | 61% / 0% | -167.6 (-57%) | +0.093 | +0.004 |  |
| A: joint - ticket (what exists today) | T3 | shared-cause events (two or more complaints from one upstream fault) | 18 | 100% | 0% | 0% (0%, 0%) | 0% | 28% / 0% | -169.9 (-76%) | +0.099 | +0.008 |  |
| A: joint - ticket (what exists today) | T2 | several complaints, no shared cause | 18 | 6% | 78% | 11% (0%, 11%) | 6% | 0% / 0% | +16.2 (+8%) | -0.008 | -0.001 |  |
| A: joint - ticket (what exists today) | T3 | several complaints, no shared cause | 18 | 0% | 22% | 78% (0%, 78%) | 0% | 0% / 0% | +21.9 (+20%) | +0.074 | -0.000 |  |
| A: joint - ticket (what exists today) | T2 | one complaint | 18 | 44% | 0% | 0% (0%, 0%) | 56% | 0% / 6% | -4.0 (-5%) | +0.002 | +0.002 |  |
| A: joint - ticket (what exists today) | T3 | one complaint | 18 | 6% | 44% | 11% (0%, 11%) | 39% | 0% / 0% | +3.9 (+8%) | +0.063 | -0.009 |  |
| B: joint - ticket_memo (the routine that reuses readings)  [PRIMARY] | T2 | all events | 18 | 0% | 83% | 6% (0%, 6%) | 11% | 0% / 0% | +10.6 (+9%) | +0.018 | -0.002 |  |
| B: joint - ticket_memo (the routine that reuses readings)  [PRIMARY] | T3 | all events | 18 | 0% | 83% | 17% (0%, 17%) | 0% | 0% / 0% | +7.5 (+12%) | +0.014 | +0.003 |  |
| B: joint - ticket_memo (the routine that reuses readings)  [PRIMARY] | T2 | shared-cause events (two or more complaints from one upstream fault) | 18 | 11% | 56% | 11% (0%, 11%) | 22% | 11% / 0% | +31.3 (+32%) | +0.036 | -0.012 |  |
| B: joint - ticket_memo (the routine that reuses readings)  [PRIMARY] | T3 | shared-cause events (two or more complaints from one upstream fault) | 18 | 0% | 56% | 44% (0%, 44%) | 0% | 0% / 0% | +12.4 (+29%) | +0.013 | +0.004 |  |
| B: joint - ticket_memo (the routine that reuses readings)  [PRIMARY] | T2 | several complaints, no shared cause | 18 | 0% | 100% | 0% (0%, 0%) | 0% | 0% / 0% | +21.7 (+11%) | +0.016 | -0.015 |  |
| B: joint - ticket_memo (the routine that reuses readings)  [PRIMARY] | T3 | several complaints, no shared cause | 18 | 0% | 67% | 33% (0%, 33%) | 0% | 0% / 0% | +17.6 (+16%) | +0.033 | +0.004 |  |
| B: joint - ticket_memo (the routine that reuses readings)  [PRIMARY] | T2 | one complaint | 18 | 6% | 0% | 0% (0%, 0%) | 94% | 0% / 6% | -0.5 (-1%) | +0.014 | +0.007 |  |
| B: joint - ticket_memo (the routine that reuses readings)  [PRIMARY] | T3 | one complaint | 18 | 6% | 6% | 0% (0%, 0%) | 89% | 0% / 0% | +1.6 (+3%) | +0.005 | +0.002 |  |
| C: ticket_memo - ticket | T2 | all events | 18 | 100% | 0% | 0% (0%, 0%) | 0% | 0% / 0% | -37.7 (-25%) | -0.003 | +0.003 |  |
| C: ticket_memo - ticket | T3 | all events | 18 | 94% | 0% | 0% (0%, 0%) | 6% | 0% / 0% | -29.0 (-31%) | +0.058 | -0.006 |  |
| C: ticket_memo - ticket | T2 | shared-cause events (two or more complaints from one upstream fault) | 18 | 100% | 0% | 0% (0%, 0%) | 0% | 50% / 0% | -198.9 (-67%) | +0.057 | +0.016 |  |
| C: ticket_memo - ticket | T3 | shared-cause events (two or more complaints from one upstream fault) | 18 | 100% | 0% | 0% (0%, 0%) | 0% | 28% / 6% | -182.3 (-81%) | +0.086 | +0.004 |  |
| C: ticket_memo - ticket | T2 | several complaints, no shared cause | 18 | 11% | 0% | 0% (0%, 0%) | 89% | 6% / 0% | -5.5 (-3%) | -0.024 | +0.014 |  |
| C: ticket_memo - ticket | T3 | several complaints, no shared cause | 18 | 28% | 17% | 0% (0%, 0%) | 56% | 6% / 0% | +4.2 (+4%) | +0.040 | -0.004 |  |
| C: ticket_memo - ticket | T2 | one complaint | 18 | 28% | 0% | 0% (0%, 0%) | 72% | 0% / 6% | -3.6 (-4%) | -0.012 | -0.005 |  |
| C: ticket_memo - ticket | T3 | one complaint | 18 | 11% | 44% | 6% (0%, 6%) | 39% | 0% / 0% | +2.3 (+5%) | +0.058 | -0.010 |  |
| D: ticket_nb - ticket (the neighbour question alone) | T2 | all events | 18 | 100% | 0% | 0% (0%, 0%) | 0% | 0% / 0% | -31.1 (-21%) | +0.015 | +0.007 |  |
| D: ticket_nb - ticket (the neighbour question alone) | T3 | all events | 18 | 89% | 0% | 0% (0%, 0%) | 11% | 6% / 0% | -25.2 (-27%) | +0.055 | +0.001 |  |
| D: ticket_nb - ticket (the neighbour question alone) | T2 | shared-cause events (two or more complaints from one upstream fault) | 18 | 100% | 0% | 0% (0%, 0%) | 0% | 50% / 0% | -165.0 (-56%) | +0.069 | +0.014 |  |
| D: ticket_nb - ticket (the neighbour question alone) | T3 | shared-cause events (two or more complaints from one upstream fault) | 18 | 100% | 0% | 0% (0%, 0%) | 0% | 22% / 0% | -162.5 (-72%) | +0.085 | +0.007 |  |
| D: ticket_nb - ticket (the neighbour question alone) | T2 | several complaints, no shared cause | 18 | 22% | 0% | 0% (0%, 0%) | 78% | 6% / 0% | -0.7 (-0%) | -0.008 | +0.001 |  |
| D: ticket_nb - ticket (the neighbour question alone) | T3 | several complaints, no shared cause | 18 | 22% | 11% | 0% (0%, 0%) | 67% | 0% / 0% | +3.9 (+4%) | +0.023 | -0.002 |  |
| D: ticket_nb - ticket (the neighbour question alone) | T2 | one complaint | 18 | 61% | 0% | 0% (0%, 0%) | 39% | 0% / 6% | -4.4 (-5%) | +0.009 | +0.007 |  |
| D: ticket_nb - ticket (the neighbour question alone) | T3 | one complaint | 18 | 6% | 50% | 6% (0%, 6%) | 39% | 0% / 0% | +3.1 (+7%) | +0.061 | +0.000 |  |
| E: joint - fast_parent (an obvious human rule) | T2 | all events | 18 | 0% | 0% | 100% (0%, 100%) | 0% | 0% / 100% | +20.2 (+19%) | +0.227 | -0.421 | 89 min (joint wins above) |
| E: joint - fast_parent (an obvious human rule) | T3 | all events | 18 | 44% | 0% | 56% (0%, 56%) | 0% | 0% / 100% | -0.3 (-0%) | +0.310 | -0.455 | joint ahead on both |
| E: joint - fast_parent (an obvious human rule) | T2 | shared-cause events (two or more complaints from one upstream fault) | 18 | 22% | 6% | 72% (0%, 72%) | 0% | 0% / 100% | +15.4 (+14%) | +0.165 | -0.194 | 94 min (joint wins above) |
| E: joint - fast_parent (an obvious human rule) | T3 | shared-cause events (two or more complaints from one upstream fault) | 18 | 39% | 0% | 61% (0%, 61%) | 0% | 0% / 100% | +3.0 (+6%) | +0.200 | -0.212 | 15 min (joint wins above) |
| E: joint - fast_parent (an obvious human rule) | T2 | several complaints, no shared cause | 18 | 0% | 0% | 100% (0%, 100%) | 0% | 0% / 100% | +46.8 (+29%) | +0.275 | -0.498 | 170 min (joint wins above) |
| E: joint - fast_parent (an obvious human rule) | T3 | several complaints, no shared cause | 18 | 33% | 0% | 67% (0%, 67%) | 0% | 0% / 100% | +6.1 (+5%) | +0.342 | -0.487 | 18 min (joint wins above) |
| E: joint - fast_parent (an obvious human rule) | T2 | one complaint | 18 | 0% | 0% | 100% (0%, 100%) | 0% | 0% / 100% | +9.7 (+13%) | +0.225 | -0.455 | 43 min (joint wins above) |
| E: joint - fast_parent (an obvious human rule) | T3 | one complaint | 18 | 50% | 0% | 50% (0%, 50%) | 0% | 0% / 100% | -4.1 (-8%) | +0.328 | -0.513 | joint ahead on both |
| F: joint - fast_ticket (a checklist per complaint) | T2 | all events | 18 | 67% | 0% | 33% (0%, 33%) | 0% | 0% / 100% | -65.4 (-35%) | +0.341 | -0.535 | joint ahead on both |
| F: joint - fast_ticket (a checklist per complaint) | T3 | all events | 18 | 50% | 0% | 50% (0%, 50%) | 0% | 0% / 100% | -57.8 (-45%) | +0.405 | -0.550 | joint ahead on both |
| F: joint - fast_ticket (a checklist per complaint) | T2 | shared-cause events (two or more complaints from one upstream fault) | 18 | 100% | 0% | 0% (0%, 0%) | 0% | 0% / 100% | -492.1 (-79%) | +0.776 | -0.806 | joint ahead on both |
| F: joint - fast_ticket (a checklist per complaint) | T3 | shared-cause events (two or more complaints from one upstream fault) | 18 | 89% | 0% | 11% (0%, 11%) | 0% | 0% / 100% | -317.2 (-85%) | +0.687 | -0.700 | joint ahead on both |
| F: joint - fast_ticket (a checklist per complaint) | T2 | several complaints, no shared cause | 18 | 0% | 0% | 100% (0%, 100%) | 0% | 0% / 100% | +49.5 (+31%) | +0.250 | -0.474 | 198 min (joint wins above) |
| F: joint - fast_ticket (a checklist per complaint) | T3 | several complaints, no shared cause | 18 | 50% | 0% | 50% (0%, 50%) | 0% | 0% / 100% | -1.6 (-1%) | +0.343 | -0.489 | joint ahead on both |
| F: joint - fast_ticket (a checklist per complaint) | T2 | one complaint | 18 | 0% | 0% | 100% (0%, 100%) | 0% | 0% / 100% | +11.5 (+16%) | +0.251 | -0.482 | 46 min (joint wins above) |
| F: joint - fast_ticket (a checklist per complaint) | T3 | one complaint | 18 | 50% | 0% | 50% (0%, 50%) | 0% | 0% / 100% | -4.9 (-9%) | +0.347 | -0.532 | joint ahead on both |
| G: joint_la2 - joint (two-step look-ahead against one-step) | T2 | all events | 3 | 33% | 0% | 0% (0%, 0%) | 67% | 0% / 0% | -8.9 (-7%) | -0.004 | -0.002 |  |
| G: joint_la2 - joint (two-step look-ahead against one-step) | T3 | all events | 3 | 0% | 33% | 0% (0%, 0%) | 67% | 0% / 0% | -0.5 (-1%) | -0.009 | +0.003 |  |
| G: joint_la2 - joint (two-step look-ahead against one-step) | T2 | shared-cause events (two or more complaints from one upstream fault) | 3 | 33% | 0% | 0% (0%, 0%) | 67% | 0% / 0% | -12.7 (-10%) | -0.008 | -0.001 |  |
| G: joint_la2 - joint (two-step look-ahead against one-step) | T3 | shared-cause events (two or more complaints from one upstream fault) | 3 | 0% | 0% | 0% (0%, 0%) | 100% | 0% / 0% | +4.2 (+8%) | +0.008 | -0.011 |  |
| G: joint_la2 - joint (two-step look-ahead against one-step) | T2 | several complaints, no shared cause | 3 | 67% | 0% | 0% (0%, 0%) | 33% | 0% / 0% | -12.8 (-6%) | +0.007 | -0.002 |  |
| G: joint_la2 - joint (two-step look-ahead against one-step) | T3 | several complaints, no shared cause | 3 | 0% | 33% | 0% (0%, 0%) | 67% | 0% / 0% | -1.3 (-1%) | -0.003 | +0.011 |  |
| G: joint_la2 - joint (two-step look-ahead against one-step) | T2 | one complaint | 3 | 100% | 0% | 0% (0%, 0%) | 0% | 0% / 0% | -5.9 (-7%) | -0.007 | -0.002 |  |
| G: joint_la2 - joint (two-step look-ahead against one-step) | T3 | one complaint | 3 | 33% | 33% | 0% (0%, 0%) | 33% | 0% / 0% | -1.6 (-3%) | -0.017 | +0.003 |  |

## Every cell, all events: minutes / accuracy / wrong-and-confident for the tool policies and stand-ins (T2 | T3)

| cell | policy | T2 | T3 |
|---|---|---|---|
| shared rare / M0 / R0 | tool_ticket | 134 / 75% / 1.1% | 74 / 79% / 1.0% |
| shared rare / M0 / R0 | tool_ticket_nb | 119 / 79% / 0.8% | 68 / 82% / 1.2% |
| shared rare / M0 / R0 | tool_ticket_memo | 116 / 77% / 1.1% | 68 / 80% / 1.2% |
| shared rare / M0 / R0 | tool_joint | 121 / 77% / 1.1% | 77 / 83% / 0.8% |
| shared rare / M0 / R0 | tool_joint_la2 | 117 / 76% / 0.4% | 75 / 79% / 1.4% |
| shared rare / M0 / R0 | fast_ticket | 132 / 51% / 49.1% | 90 / 50% / 49.7% |
| shared rare / M0 / R0 | fast_parent | 103 / 54% / 45.8% | 79 / 52% / 47.9% |
| shared rare / M0 / R1 | tool_ticket | 146 / 47% / 4.8% | 82 / 54% / 7.4% |
| shared rare / M0 / R1 | tool_ticket_nb | 128 / 53% / 3.5% | 74 / 59% / 6.3% |
| shared rare / M0 / R1 | tool_ticket_memo | 125 / 52% / 5.2% | 71 / 57% / 8.1% |
| shared rare / M0 / R1 | tool_joint | 136 / 51% / 4.7% | 82 / 58% / 8.8% |
| shared rare / M0 / R1 | fast_ticket | 71 / 27% / 73.3% | 39 / 25% / 74.5% |
| shared rare / M0 / R1 | fast_parent | 57 / 30% / 69.8% | 31 / 25% / 74.6% |
| shared rare / M1 / R0 | tool_ticket | 132 / 74% / 0.6% | 72 / 78% / 0.5% |
| shared rare / M1 / R0 | tool_ticket_nb | 121 / 76% / 1.1% | 71 / 79% / 1.2% |
| shared rare / M1 / R0 | tool_ticket_memo | 120 / 76% / 1.1% | 70 / 79% / 1.1% |
| shared rare / M1 / R0 | tool_joint | 126 / 76% / 0.7% | 81 / 82% / 0.6% |
| shared rare / M1 / R0 | fast_ticket | 119 / 52% / 48.2% | 90 / 51% / 48.8% |
| shared rare / M1 / R0 | fast_parent | 105 / 53% / 47.0% | 81 / 51% / 49.1% |
| shared rare / M1 / R1 | tool_ticket | 143 / 48% / 4.8% | 80 / 53% / 6.9% |
| shared rare / M1 / R1 | tool_ticket_nb | 128 / 53% / 4.2% | 73 / 57% / 8.2% |
| shared rare / M1 / R1 | tool_ticket_memo | 126 / 53% / 4.9% | 72 / 58% / 7.3% |
| shared rare / M1 / R1 | tool_joint | 137 / 53% / 5.5% | 80 / 59% / 7.2% |
| shared rare / M1 / R1 | fast_ticket | 74 / 27% / 72.5% | 38 / 26% / 74.1% |
| shared rare / M1 / R1 | fast_parent | 55 / 27% / 72.5% | 32 / 24% / 75.8% |
| shared rare / M2 / R0 | tool_ticket | 133 / 77% / 0.8% | 75 / 74% / 0.3% |
| shared rare / M2 / R0 | tool_ticket_nb | 124 / 76% / 0.6% | 73 / 76% / 0.9% |
| shared rare / M2 / R0 | tool_ticket_memo | 121 / 78% / 0.9% | 72 / 77% / 0.9% |
| shared rare / M2 / R0 | tool_joint | 130 / 78% / 1.1% | 81 / 78% / 0.6% |
| shared rare / M2 / R0 | fast_ticket | 129 / 47% / 52.6% | 104 / 45% / 55.3% |
| shared rare / M2 / R0 | fast_parent | 113 / 50% / 49.7% | 89 / 47% / 53.0% |
| shared rare / M2 / R1 | tool_ticket | 141 / 48% / 4.4% | 81 / 48% / 6.2% |
| shared rare / M2 / R1 | tool_ticket_nb | 128 / 52% / 5.8% | 75 / 50% / 8.7% |
| shared rare / M2 / R1 | tool_ticket_memo | 124 / 50% / 5.2% | 75 / 50% / 8.2% |
| shared rare / M2 / R1 | tool_joint | 134 / 51% / 6.4% | 84 / 52% / 7.0% |
| shared rare / M2 / R1 | fast_ticket | 72 / 24% / 76.1% | 38 / 22% / 78.4% |
| shared rare / M2 / R1 | fast_parent | 62 / 24% / 76.5% | 35 / 22% / 78.0% |
| shared assumed / M0 / R0 | tool_ticket | 151 / 78% / 0.6% | 93 / 77% / 1.3% |
| shared assumed / M0 / R0 | tool_ticket_nb | 120 / 80% / 1.3% | 68 / 83% / 1.4% |
| shared assumed / M0 / R0 | tool_ticket_memo | 114 / 78% / 1.0% | 64 / 83% / 0.7% |
| shared assumed / M0 / R0 | tool_joint | 124 / 80% / 0.8% | 71 / 85% / 0.9% |
| shared assumed / M0 / R0 | tool_joint_la2 | 115 / 79% / 0.6% | 71 / 84% / 1.3% |
| shared assumed / M0 / R0 | fast_ticket | 190 / 46% / 54.3% | 129 / 44% / 55.9% |
| shared assumed / M0 / R0 | fast_parent | 104 / 57% / 42.9% | 72 / 54% / 46.4% |
| shared assumed / M0 / R1 | tool_ticket | 169 / 48% / 5.4% | 100 / 53% / 7.9% |
| shared assumed / M0 / R1 | tool_ticket_nb | 127 / 58% / 4.3% | 74 / 58% / 7.3% |
| shared assumed / M0 / R1 | tool_ticket_memo | 122 / 55% / 4.4% | 66 / 58% / 7.0% |
| shared assumed / M0 / R1 | tool_joint | 132 / 56% / 4.5% | 80 / 63% / 6.9% |
| shared assumed / M0 / R1 | fast_ticket | 93 / 23% / 77.2% | 44 / 22% / 78.0% |
| shared assumed / M0 / R1 | fast_parent | 59 / 30% / 70.3% | 31 / 29% / 71.3% |
| shared assumed / M1 / R0 | tool_ticket | 156 / 77% / 0.7% | 90 / 78% / 1.3% |
| shared assumed / M1 / R0 | tool_ticket_nb | 127 / 79% / 1.0% | 72 / 80% / 1.5% |
| shared assumed / M1 / R0 | tool_ticket_memo | 125 / 78% / 1.7% | 68 / 83% / 1.6% |
| shared assumed / M1 / R0 | tool_joint | 131 / 76% / 1.7% | 82 / 81% / 1.7% |
| shared assumed / M1 / R0 | fast_ticket | 175 / 49% / 51.1% | 119 / 48% / 52.0% |
| shared assumed / M1 / R0 | fast_parent | 103 / 55% / 44.8% | 82 / 53% / 46.8% |
| shared assumed / M1 / R1 | tool_ticket | 172 / 50% / 4.9% | 102 / 53% / 6.3% |
| shared assumed / M1 / R1 | tool_ticket_nb | 138 / 58% / 4.5% | 77 / 61% / 7.7% |
| shared assumed / M1 / R1 | tool_ticket_memo | 132 / 55% / 4.3% | 75 / 58% / 7.4% |
| shared assumed / M1 / R1 | tool_joint | 143 / 53% / 3.8% | 91 / 60% / 9.3% |
| shared assumed / M1 / R1 | fast_ticket | 99 / 24% / 75.8% | 49 / 24% / 76.1% |
| shared assumed / M1 / R1 | fast_parent | 62 / 32% / 67.6% | 34 / 29% / 70.8% |
| shared assumed / M2 / R0 | tool_ticket | 159 / 76% / 0.5% | 93 / 74% / 0.9% |
| shared assumed / M2 / R0 | tool_ticket_nb | 135 / 78% / 1.1% | 78 / 75% / 1.3% |
| shared assumed / M2 / R0 | tool_ticket_memo | 128 / 78% / 1.5% | 73 / 77% / 1.5% |
| shared assumed / M2 / R0 | tool_joint | 140 / 79% / 1.3% | 89 / 80% / 1.9% |
| shared assumed / M2 / R0 | fast_ticket | 187 / 44% / 55.9% | 130 / 48% / 52.5% |
| shared assumed / M2 / R0 | fast_parent | 112 / 51% / 49.1% | 93 / 49% / 50.6% |
| shared assumed / M2 / R1 | tool_ticket | 169 / 49% / 4.6% | 98 / 49% / 7.4% |
| shared assumed / M2 / R1 | tool_ticket_nb | 138 / 54% / 5.1% | 81 / 52% / 8.6% |
| shared assumed / M2 / R1 | tool_ticket_memo | 133 / 53% / 5.9% | 75 / 53% / 9.4% |
| shared assumed / M2 / R1 | tool_joint | 147 / 52% / 5.1% | 90 / 54% / 9.2% |
| shared assumed / M2 / R1 | fast_ticket | 96 / 21% / 78.9% | 47 / 21% / 78.7% |
| shared assumed / M2 / R1 | fast_parent | 65 / 30% / 70.0% | 35 / 25% / 74.9% |
| shared common / M0 / R0 | tool_ticket | 202 / 81% / 0.4% | 134 / 80% / 1.0% |
| shared common / M0 / R0 | tool_ticket_nb | 127 / 83% / 1.8% | 71 / 84% / 1.5% |
| shared common / M0 / R0 | tool_ticket_memo | 114 / 84% / 1.3% | 60 / 85% / 1.6% |
| shared common / M0 / R0 | tool_joint | 120 / 83% / 1.2% | 74 / 87% / 1.8% |
| shared common / M0 / R0 | tool_joint_la2 | 118 / 85% / 1.0% | 72 / 85% / 1.4% |
| shared common / M0 / R0 | fast_ticket | 312 / 42% / 57.8% | 184 / 45% / 55.3% |
| shared common / M0 / R0 | fast_parent | 101 / 63% / 37.3% | 74 / 57% / 42.6% |
| shared common / M0 / R1 | tool_ticket | 230 / 53% / 4.0% | 143 / 58% / 7.2% |
| shared common / M0 / R1 | tool_ticket_nb | 143 / 60% / 4.1% | 79 / 66% / 7.0% |
| shared common / M0 / R1 | tool_ticket_memo | 130 / 62% / 3.9% | 65 / 67% / 6.0% |
| shared common / M0 / R1 | tool_joint | 141 / 63% / 5.3% | 79 / 68% / 7.7% |
| shared common / M0 / R1 | fast_ticket | 155 / 20% / 79.8% | 70 / 24% / 75.5% |
| shared common / M0 / R1 | fast_parent | 60 / 39% / 61.2% | 34 / 39% / 61.1% |
| shared common / M1 / R0 | tool_ticket | 217 / 80% / 0.6% | 138 / 78% / 1.4% |
| shared common / M1 / R0 | tool_ticket_nb | 154 / 79% / 2.2% | 84 / 83% / 2.3% |
| shared common / M1 / R0 | tool_ticket_memo | 136 / 81% / 2.0% | 73 / 82% / 2.5% |
| shared common / M1 / R0 | tool_joint | 148 / 82% / 2.1% | 97 / 84% / 2.8% |
| shared common / M1 / R0 | fast_ticket | 317 / 39% / 60.9% | 186 / 43% / 57.1% |
| shared common / M1 / R0 | fast_parent | 114 / 61% / 39.4% | 89 / 58% / 42.4% |
| shared common / M1 / R1 | tool_ticket | 245 / 51% / 4.4% | 150 / 57% / 6.6% |
| shared common / M1 / R1 | tool_ticket_nb | 167 / 61% / 4.0% | 91 / 63% / 7.1% |
| shared common / M1 / R1 | tool_ticket_memo | 148 / 59% / 5.7% | 77 / 63% / 8.4% |
| shared common / M1 / R1 | tool_joint | 169 / 61% / 5.1% | 101 / 63% / 8.9% |
| shared common / M1 / R1 | fast_ticket | 161 / 21% / 79.4% | 76 / 25% / 75.4% |
| shared common / M1 / R1 | fast_parent | 71 / 38% / 61.7% | 38 / 39% / 61.0% |
| shared common / M2 / R0 | tool_ticket | 219 / 79% / 1.2% | 138 / 76% / 1.1% |
| shared common / M2 / R0 | tool_ticket_nb | 156 / 79% / 1.7% | 84 / 77% / 2.5% |
| shared common / M2 / R0 | tool_ticket_memo | 142 / 79% / 1.8% | 74 / 78% / 2.6% |
| shared common / M2 / R0 | tool_joint | 155 / 82% / 1.5% | 103 / 79% / 2.4% |
| shared common / M2 / R0 | fast_ticket | 323 / 40% / 60.4% | 199 / 41% / 59.1% |
| shared common / M2 / R0 | fast_parent | 130 / 59% / 40.8% | 96 / 57% / 43.1% |
| shared common / M2 / R1 | tool_ticket | 246 / 50% / 5.6% | 149 / 54% / 7.1% |
| shared common / M2 / R1 | tool_ticket_nb | 164 / 61% / 6.3% | 92 / 60% / 7.6% |
| shared common / M2 / R1 | tool_ticket_memo | 148 / 59% / 5.4% | 78 / 61% / 8.5% |
| shared common / M2 / R1 | tool_joint | 169 / 59% / 6.1% | 110 / 60% / 9.3% |
| shared common / M2 / R1 | fast_ticket | 164 / 17% / 82.8% | 69 / 22% / 77.8% |
| shared common / M2 / R1 | fast_parent | 72 / 37% / 63.4% | 41 / 33% / 67.3% |

## Predictions (written before the run; each strict)

| prediction | holds | values |
|---|---|---|
| P1 | holds | joint vs ticket, T2, shared: -57% minutes, accuracy MORE |
| P2 | holds | joint vs ticket_memo, T2, shared: +32% minutes |
| P3 | holds | ticket_nb vs ticket, T2, all: -21% minutes |
| P4 | does not hold | minutes joint saves against ticket on shared events: T2 167.6, T3 169.9 |
| P5 | does not hold | T2 wrong-and-confident: joint M0 0.008, joint M1 0.017, ticket_memo M1 0.017 |
| P6 | holds | T2 all: fast_parent 104 min 0.57, joint 124 min 0.80 |
| P7 | does not hold | look-ahead vs one-step |minutes| / |accuracy|: rare/T2: 3.6%, 0.018; rare/T3: 2.2%, 0.041; assumed/T2: 7.1%, 0.004; assumed/T3: 0.7%, 0.009; common/T2: 1.7%, 0.015; common/T3: 2.3%, 0.018 |
| P8 | holds | single events, joint vs ticket_nb: T2: 0.4%; T3: 1.6% |
| P9 | holds | rare shared, all events, advantage of joint over ticket_memo: T2: -4.1%; T3: -13.7% |

## Frozen decision: THE ROUTINE CAPTURES IT

Run time 352 s.
