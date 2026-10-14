# The group-informing rule (Addendum 31)

Addendum 30's world, cells and events (18 cells, 1000 events each, both tiers); three new policies with the repaired conclusion rule (`tool_ticket_memo2`, `tool_joint2`, `tool_joint2_la2`) compared with Addendum 30's stored results (same events, different answer draws). Everything is simulated from the tool's own model family with placeholder numbers; the stand-in is my construction; nothing here is evidence about real technicians, buildings, or how often shared causes happen.

## Gates

| gate | result | detail |
|---|---|---|
| G1 regression | PASS | events differ in cells []; 1440 re-run Addendum 30 episodes: 0 differ |
| G2 the rule | PASS | one bearing check (static_at_box); 100 random groups: largest difference from brute force or from the rule-off beliefs 5.12e-14; informing semantics as registered |
| G3 replay | PASS | 360 replayed events: 0 differ |
| G4 reproducibility | PASS | cell 0: 0 policy/tier series differ in the first 30 events |
| G5 completeness and pairing | PASS | 18 cells, every new policy at both tiers on Addendum 30's events |
| G6 the tool's settings | PASS | the tool's settings are Addendum 30's in every cell |

## Primary cell (shared assumed / M0 / R0), tier T2: minutes per visit / share of complaints diagnosed correctly / wrong-and-confident / checks per visit

| policy | all events | shared-cause | several, no shared cause | one complaint |
|---|---|---|---|---|
| tool_ticket | 151 min / 78% / 0.6% / 16.3 | 296 min / 87% / 0.1% / 34.6 | 194 min / 78% / 0.8% / 20.1 | 89 min / 76% / 0.7% / 9.1 |
| tool_ticket_memo | 114 min / 78% / 1.0% / 11.3 | 97 min / 93% / 1.7% / 8.5 | 189 min / 75% / 2.2% / 19.3 | 85 min / 75% / 0.2% / 8.5 |
| tool_ticket_memo2 | 112 min / 80% / 0.7% / 11.2 | 82 min / 93% / 2.2% / 7.1 | 191 min / 77% / 0.8% / 19.8 | 85 min / 77% / 0.2% / 8.5 |
| tool_joint | 124 min / 80% / 0.8% / 11.8 | 128 min / 97% / 0.5% / 10.3 | 210 min / 77% / 0.7% / 20.0 | 85 min / 76% / 0.9% / 8.6 |
| tool_joint2 | 119 min / 80% / 0.8% / 11.3 | 97 min / 95% / 2.4% / 7.7 | 209 min / 78% / 0.8% / 19.7 | 85 min / 77% / 0.3% / 8.6 |
| tool_joint2_la2 | 112 min / 80% / 1.0% / 11.8 | 100 min / 96% / 2.1% / 9.0 | 192 min / 77% / 0.9% / 20.4 | 79 min / 76% / 0.7% / 8.9 |
| tool_joint3 | 118 min / 81% / 0.9% / 11.3 | 92 min / 96% / 2.1% / 7.7 | 211 min / 77% / 1.1% / 20.0 | 84 min / 79% / 0.5% / 8.5 |
| fast_parent | 104 min / 57% / 42.9% / 10.7 | 113 min / 80% / 19.9% / 11.0 | 164 min / 49% / 50.6% / 17.2 | 75 min / 54% / 46.4% / 7.8 |

## Primary cell (shared assumed / M0 / R0), tier T3: minutes per visit / share of complaints diagnosed correctly / wrong-and-confident / checks per visit

| policy | all events | shared-cause | several, no shared cause | one complaint |
|---|---|---|---|---|
| tool_ticket | 93 min / 77% / 1.3% / 17.9 | 225 min / 86% / 2.0% / 36.7 | 109 min / 77% / 1.0% / 23.2 | 46 min / 75% / 1.2% / 9.9 |
| tool_ticket_memo | 64 min / 83% / 0.7% / 12.3 | 43 min / 95% / 2.4% / 7.9 | 113 min / 81% / 0.7% / 22.1 | 48 min / 81% / 0.2% / 9.3 |
| tool_ticket_memo2 | 65 min / 82% / 1.1% / 12.3 | 41 min / 95% / 2.3% / 7.8 | 111 min / 80% / 1.8% / 21.6 | 51 min / 80% / 0.3% / 9.5 |
| tool_joint | 71 min / 85% / 0.9% / 12.8 | 55 min / 96% / 2.8% / 8.7 | 131 min / 84% / 1.0% / 23.2 | 50 min / 81% / 0.3% / 9.4 |
| tool_joint2 | 71 min / 84% / 1.2% / 13.0 | 53 min / 95% / 3.1% / 8.7 | 134 min / 83% / 1.6% / 23.8 | 49 min / 82% / 0.5% / 9.4 |
| tool_joint2_la2 | 72 min / 82% / 1.5% / 14.3 | 64 min / 97% / 2.2% / 12.1 | 131 min / 83% / 1.6% / 24.3 | 48 min / 76% / 1.2% / 10.5 |
| tool_joint3 | 72 min / 84% / 1.1% / 12.9 | 49 min / 96% / 2.5% / 8.2 | 138 min / 84% / 0.7% / 23.8 | 49 min / 80% / 0.9% / 9.4 |
| fast_parent | 72 min / 54% / 46.4% / 11.1 | 52 min / 76% / 24.0% / 8.5 | 124 min / 50% / 49.7% / 19.2 | 54 min / 48% / 51.7% / 8.3 |

## Every comparison over the cells

Labels are Addendum 21's for the FIRST policy minus the second on the same events (TRADE in brackets: faster but less accurate (F/L) or slower but more accurate (S/M)); SAFETY REG / GAIN = share of cells where the first policy's wrong-and-confident rate is at least 0.02 higher / lower with the interval clear of 0. The last columns are the primary cell's deltas and, for K, the break-even cost of a wrong diagnosis.

| comparison | tier | subset | cells | IMPROVES | WORSE | TRADE (F/L, S/M) | NEITHER | SAFETY REG / GAIN | primary: d minutes | d accuracy | d wrong-and-confident | break-even |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H: joint2 - ticket_memo2 (the machinery against the routine, both repaired)  [PRIMARY] | T2 | all events | 18 | 0% | 83% | 6% (0%, 6%) | 11% | 0% / 0% | +7.1 (+6%) | +0.005 | +0.001 |  |
| H: joint2 - ticket_memo2 (the machinery against the routine, both repaired)  [PRIMARY] | T3 | all events | 18 | 0% | 83% | 17% (0%, 17%) | 0% | 0% / 0% | +6.6 (+10%) | +0.018 | +0.002 |  |
| H: joint2 - ticket_memo2 (the machinery against the routine, both repaired)  [PRIMARY] | T2 | shared-cause events | 18 | 0% | 56% | 6% (0%, 6%) | 39% | 22% / 0% | +14.3 (+17%) | +0.022 | +0.002 |  |
| H: joint2 - ticket_memo2 (the machinery against the routine, both repaired)  [PRIMARY] | T3 | shared-cause events | 18 | 0% | 67% | 33% (0%, 33%) | 0% | 6% / 0% | +11.8 (+29%) | +0.004 | +0.008 |  |
| H: joint2 - ticket_memo2 (the machinery against the routine, both repaired)  [PRIMARY] | T2 | several complaints, no shared cause | 18 | 0% | 89% | 6% (0%, 6%) | 6% | 0% / 6% | +17.6 (+9%) | +0.011 | -0.001 |  |
| H: joint2 - ticket_memo2 (the machinery against the routine, both repaired)  [PRIMARY] | T3 | several complaints, no shared cause | 18 | 0% | 67% | 33% (0%, 33%) | 0% | 0% / 11% | +22.2 (+20%) | +0.027 | -0.002 |  |
| H: joint2 - ticket_memo2 (the machinery against the routine, both repaired)  [PRIMARY] | T2 | one complaint | 18 | 0% | 0% | 0% (0%, 0%) | 100% | 6% / 0% | +0.3 (+0%) | -0.002 | +0.002 |  |
| H: joint2 - ticket_memo2 (the machinery against the routine, both repaired)  [PRIMARY] | T3 | one complaint | 18 | 11% | 0% | 0% (0%, 0%) | 89% | 0% / 0% | -1.9 (-4%) | +0.017 | +0.002 |  |
| I: joint2 - joint (what the repair did for the joint tool) | T2 | all events | 18 | 17% | 0% | 0% (0%, 0%) | 83% | 0% / 0% | -5.3 (-4%) | +0.004 | +0.000 |  |
| I: joint2 - joint (what the repair did for the joint tool) | T3 | all events | 18 | 6% | 6% | 0% (0%, 0%) | 89% | 0% / 6% | -0.2 (-0%) | -0.003 | +0.003 |  |
| I: joint2 - joint (what the repair did for the joint tool) | T2 | shared-cause events | 18 | 39% | 0% | 0% (0%, 0%) | 61% | 11% / 6% | -31.5 (-25%) | -0.013 | +0.019 |  |
| I: joint2 - joint (what the repair did for the joint tool) | T3 | shared-cause events | 18 | 6% | 0% | 0% (0%, 0%) | 94% | 6% / 0% | -2.3 (-4%) | -0.007 | +0.003 |  |
| I: joint2 - joint (what the repair did for the joint tool) | T2 | several complaints, no shared cause | 18 | 6% | 0% | 0% (0%, 0%) | 94% | 0% / 6% | -1.7 (-1%) | +0.012 | +0.001 |  |
| I: joint2 - joint (what the repair did for the joint tool) | T3 | several complaints, no shared cause | 18 | 0% | 0% | 0% (0%, 0%) | 100% | 0% / 0% | +3.0 (+2%) | -0.014 | +0.006 |  |
| I: joint2 - joint (what the repair did for the joint tool) | T2 | one complaint | 18 | 0% | 6% | 0% (0%, 0%) | 94% | 6% / 0% | +0.9 (+1%) | +0.005 | -0.005 |  |
| I: joint2 - joint (what the repair did for the joint tool) | T3 | one complaint | 18 | 11% | 11% | 0% (0%, 0%) | 78% | 0% / 0% | -1.0 (-2%) | +0.003 | +0.002 |  |
| J: ticket_memo2 - ticket_memo (what it did for the routine) | T2 | all events | 18 | 39% | 0% | 0% (0%, 0%) | 61% | 0% / 0% | -1.8 (-2%) | +0.017 | -0.003 |  |
| J: ticket_memo2 - ticket_memo (what it did for the routine) | T3 | all events | 18 | 0% | 11% | 0% (0%, 0%) | 89% | 0% / 0% | +0.8 (+1%) | -0.007 | +0.004 |  |
| J: ticket_memo2 - ticket_memo (what it did for the routine) | T2 | shared-cause events | 18 | 72% | 0% | 0% (0%, 0%) | 28% | 6% / 6% | -14.4 (-15%) | +0.001 | +0.005 |  |
| J: ticket_memo2 - ticket_memo (what it did for the routine) | T3 | shared-cause events | 18 | 17% | 6% | 0% (0%, 0%) | 78% | 0% / 6% | -1.7 (-4%) | +0.003 | -0.001 |  |
| J: ticket_memo2 - ticket_memo (what it did for the routine) | T2 | several complaints, no shared cause | 18 | 0% | 0% | 0% (0%, 0%) | 100% | 0% / 0% | +2.3 (+1%) | +0.017 | -0.013 |  |
| J: ticket_memo2 - ticket_memo (what it did for the routine) | T3 | several complaints, no shared cause | 18 | 6% | 6% | 0% (0%, 0%) | 89% | 11% / 0% | -1.5 (-1%) | -0.008 | +0.012 |  |
| J: ticket_memo2 - ticket_memo (what it did for the routine) | T2 | one complaint | 18 | 0% | 6% | 0% (0%, 0%) | 94% | 0% / 0% | +0.2 (+0%) | +0.021 | +0.000 |  |
| J: ticket_memo2 - ticket_memo (what it did for the routine) | T3 | one complaint | 18 | 0% | 17% | 0% (0%, 0%) | 83% | 0% / 0% | +2.5 (+5%) | -0.009 | +0.002 |  |
| K: joint2 - fast_parent (an obvious human rule) | T2 | all events | 18 | 0% | 0% | 100% (0%, 100%) | 0% | 0% / 100% | +14.9 (+14%) | +0.231 | -0.421 | 64 min (joint2 wins above) |
| K: joint2 - fast_parent (an obvious human rule) | T3 | all events | 18 | 44% | 0% | 56% (0%, 56%) | 0% | 0% / 100% | -0.5 (-1%) | +0.307 | -0.452 | joint2 ahead on both |
| K: joint2 - fast_parent (an obvious human rule) | T2 | shared-cause events | 18 | 33% | 0% | 67% (0%, 67%) | 0% | 0% / 100% | -16.0 (-14%) | +0.152 | -0.175 | joint2 ahead on both |
| K: joint2 - fast_parent (an obvious human rule) | T3 | shared-cause events | 18 | 33% | 0% | 67% (0%, 67%) | 0% | 0% / 100% | +0.7 (+1%) | +0.193 | -0.209 | 3 min (joint2 wins above) |
| K: joint2 - fast_parent (an obvious human rule) | T2 | several complaints, no shared cause | 18 | 0% | 0% | 100% (0%, 100%) | 0% | 0% / 100% | +45.1 (+28%) | +0.287 | -0.498 | 157 min (joint2 wins above) |
| K: joint2 - fast_parent (an obvious human rule) | T3 | several complaints, no shared cause | 18 | 33% | 0% | 67% (0%, 67%) | 0% | 0% / 100% | +9.1 (+7%) | +0.327 | -0.481 | 28 min (joint2 wins above) |
| K: joint2 - fast_parent (an obvious human rule) | T2 | one complaint | 18 | 0% | 0% | 100% (0%, 100%) | 0% | 0% / 100% | +10.7 (+14%) | +0.230 | -0.461 | 46 min (joint2 wins above) |
| K: joint2 - fast_parent (an obvious human rule) | T3 | one complaint | 18 | 50% | 0% | 50% (0%, 50%) | 0% | 0% / 100% | -5.1 (-9%) | +0.332 | -0.511 | joint2 ahead on both |
| L: joint2 - ticket (what exists today) | T2 | all events | 18 | 89% | 0% | 0% (0%, 0%) | 11% | 6% / 0% | -32.3 (-21%) | +0.019 | +0.002 |  |
| L: joint2 - ticket (what exists today) | T3 | all events | 18 | 78% | 0% | 11% (0%, 11%) | 11% | 6% / 0% | -21.6 (-23%) | +0.069 | -0.001 |  |
| L: joint2 - ticket (what exists today) | T2 | shared-cause events | 18 | 100% | 0% | 0% (0%, 0%) | 0% | 78% / 0% | -199.1 (-67%) | +0.080 | +0.022 |  |
| L: joint2 - ticket (what exists today) | T3 | shared-cause events | 18 | 100% | 0% | 0% (0%, 0%) | 0% | 28% / 6% | -172.2 (-77%) | +0.092 | +0.011 |  |
| L: joint2 - ticket (what exists today) | T2 | several complaints, no shared cause | 18 | 6% | 67% | 11% (0%, 11%) | 17% | 0% / 0% | +14.4 (+7%) | +0.004 | +0.000 |  |
| L: joint2 - ticket (what exists today) | T3 | several complaints, no shared cause | 18 | 0% | 22% | 78% (0%, 78%) | 0% | 6% / 0% | +24.9 (+23%) | +0.059 | +0.006 |  |
| L: joint2 - ticket (what exists today) | T2 | one complaint | 18 | 50% | 0% | 0% (0%, 0%) | 50% | 0% / 6% | -3.1 (-3%) | +0.007 | -0.003 |  |
| L: joint2 - ticket (what exists today) | T3 | one complaint | 18 | 6% | 56% | 6% (0%, 6%) | 33% | 0% / 0% | +2.9 (+6%) | +0.066 | -0.007 |  |
| M: joint2_la2 - joint2 (two-step look-ahead against one-step) | T2 | all events | 3 | 67% | 0% | 0% (0%, 0%) | 33% | 0% / 0% | -7.3 (-6%) | -0.003 | +0.002 |  |
| M: joint2_la2 - joint2 (two-step look-ahead against one-step) | T3 | all events | 3 | 0% | 33% | 0% (0%, 0%) | 67% | 0% / 0% | +0.9 (+1%) | -0.026 | +0.002 |  |
| M: joint2_la2 - joint2 (two-step look-ahead against one-step) | T2 | shared-cause events | 3 | 0% | 0% | 0% (0%, 0%) | 100% | 0% / 0% | +3.3 (+3%) | +0.011 | -0.003 |  |
| M: joint2_la2 - joint2 (two-step look-ahead against one-step) | T3 | shared-cause events | 3 | 0% | 33% | 0% (0%, 0%) | 67% | 0% / 33% | +10.8 (+20%) | +0.013 | -0.009 |  |
| M: joint2_la2 - joint2 (two-step look-ahead against one-step) | T2 | several complaints, no shared cause | 3 | 100% | 0% | 0% (0%, 0%) | 0% | 0% / 0% | -16.3 (-8%) | -0.011 | +0.001 |  |
| M: joint2_la2 - joint2 (two-step look-ahead against one-step) | T3 | several complaints, no shared cause | 3 | 33% | 0% | 0% (0%, 0%) | 67% | 0% / 0% | -2.6 (-2%) | +0.002 | -0.001 |  |
| M: joint2_la2 - joint2 (two-step look-ahead against one-step) | T2 | one complaint | 3 | 100% | 0% | 0% (0%, 0%) | 0% | 0% / 0% | -6.4 (-7%) | -0.003 | +0.003 |  |
| M: joint2_la2 - joint2 (two-step look-ahead against one-step) | T3 | one complaint | 3 | 0% | 67% | 0% (0%, 0%) | 33% | 0% / 0% | -0.6 (-1%) | -0.051 | +0.007 |  |
| N: joint3 - ticket_memo2 (SECONDARY: repaired, air-handler rate threshold unscaled) | T2 | all events | 18 | 0% | 72% | 11% (0%, 11%) | 17% | 0% / 0% | +6.2 (+6%) | +0.014 | +0.002 |  |
| N: joint3 - ticket_memo2 (SECONDARY: repaired, air-handler rate threshold unscaled) | T3 | all events | 18 | 0% | 72% | 28% (0%, 28%) | 0% | 0% / 0% | +7.0 (+11%) | +0.013 | +0.000 |  |
| N: joint3 - ticket_memo2 (SECONDARY: repaired, air-handler rate threshold unscaled) | T2 | shared-cause events | 18 | 11% | 56% | 11% (0%, 11%) | 22% | 6% / 0% | +9.9 (+12%) | +0.026 | -0.001 |  |
| N: joint3 - ticket_memo2 (SECONDARY: repaired, air-handler rate threshold unscaled) | T3 | shared-cause events | 18 | 0% | 44% | 50% (0%, 50%) | 6% | 6% / 0% | +8.4 (+21%) | +0.012 | +0.002 |  |
| N: joint3 - ticket_memo2 (SECONDARY: repaired, air-handler rate threshold unscaled) | T2 | several complaints, no shared cause | 18 | 0% | 89% | 11% (0%, 11%) | 0% | 0% / 0% | +20.1 (+11%) | -0.006 | +0.003 |  |
| N: joint3 - ticket_memo2 (SECONDARY: repaired, air-handler rate threshold unscaled) | T3 | several complaints, no shared cause | 18 | 0% | 67% | 33% (0%, 33%) | 0% | 0% / 0% | +26.3 (+24%) | +0.038 | -0.012 |  |
| N: joint3 - ticket_memo2 (SECONDARY: repaired, air-handler rate threshold unscaled) | T2 | one complaint | 18 | 0% | 0% | 0% (0%, 0%) | 100% | 0% / 0% | -1.1 (-1%) | +0.019 | +0.003 |  |
| N: joint3 - ticket_memo2 (SECONDARY: repaired, air-handler rate threshold unscaled) | T3 | one complaint | 18 | 6% | 6% | 0% (0%, 0%) | 89% | 0% / 0% | -2.1 (-4%) | +0.002 | +0.005 |  |
| O: joint3 - joint2 (what unscaling the air-handler threshold did) | T2 | all events | 18 | 11% | 0% | 0% (0%, 0%) | 89% | 0% / 0% | -1.0 (-1%) | +0.009 | +0.001 |  |
| O: joint3 - joint2 (what unscaling the air-handler threshold did) | T3 | all events | 18 | 6% | 0% | 0% (0%, 0%) | 94% | 0% / 0% | +0.4 (+1%) | -0.005 | -0.001 |  |
| O: joint3 - joint2 (what unscaling the air-handler threshold did) | T2 | shared-cause events | 18 | 11% | 6% | 0% (0%, 0%) | 83% | 0% / 6% | -4.4 (-5%) | +0.005 | -0.003 |  |
| O: joint3 - joint2 (what unscaling the air-handler threshold did) | T3 | shared-cause events | 18 | 11% | 0% | 0% (0%, 0%) | 89% | 0% / 11% | -3.4 (-7%) | +0.008 | -0.006 |  |
| O: joint3 - joint2 (what unscaling the air-handler threshold did) | T2 | several complaints, no shared cause | 18 | 0% | 11% | 0% (0%, 0%) | 89% | 6% / 0% | +2.5 (+1%) | -0.017 | +0.003 |  |
| O: joint3 - joint2 (what unscaling the air-handler threshold did) | T3 | several complaints, no shared cause | 18 | 0% | 0% | 0% (0%, 0%) | 100% | 11% / 0% | +4.1 (+3%) | +0.011 | -0.010 |  |
| O: joint3 - joint2 (what unscaling the air-handler threshold did) | T2 | one complaint | 18 | 6% | 0% | 0% (0%, 0%) | 94% | 0% / 11% | -1.4 (-2%) | +0.021 | +0.002 |  |
| O: joint3 - joint2 (what unscaling the air-handler threshold did) | T3 | one complaint | 18 | 6% | 6% | 0% (0%, 0%) | 89% | 0% / 0% | -0.1 (-0%) | -0.016 | +0.003 |  |

## Every cell, all events: minutes / accuracy / wrong-and-confident (T2 | T3)

| cell | policy | T2 | T3 |
|---|---|---|---|
| shared rare / M0 / R0 | tool_ticket | 134 / 75% / 1.1% | 74 / 79% / 1.0% |
| shared rare / M0 / R0 | tool_ticket_memo | 116 / 77% / 1.1% | 68 / 80% / 1.2% |
| shared rare / M0 / R0 | tool_ticket_memo2 | 115 / 79% / 0.8% | 68 / 81% / 1.0% |
| shared rare / M0 / R0 | tool_joint | 121 / 77% / 1.1% | 77 / 83% / 0.8% |
| shared rare / M0 / R0 | tool_joint2 | 123 / 78% / 0.8% | 75 / 82% / 0.7% |
| shared rare / M0 / R0 | tool_joint2_la2 | 114 / 76% / 0.7% | 76 / 81% / 0.9% |
| shared rare / M0 / R0 | tool_joint3 | 122 / 78% / 1.7% | 75 / 83% / 0.8% |
| shared rare / M0 / R0 | fast_parent | 103 / 54% / 45.8% | 79 / 52% / 47.9% |
| shared rare / M0 / R1 | tool_ticket | 146 / 47% / 4.8% | 82 / 54% / 7.4% |
| shared rare / M0 / R1 | tool_ticket_memo | 125 / 52% / 5.2% | 71 / 57% / 8.1% |
| shared rare / M0 / R1 | tool_ticket_memo2 | 123 / 53% / 4.9% | 71 / 56% / 8.6% |
| shared rare / M0 / R1 | tool_joint | 136 / 51% / 4.7% | 82 / 58% / 8.8% |
| shared rare / M0 / R1 | tool_joint2 | 133 / 51% / 5.3% | 85 / 59% / 6.6% |
| shared rare / M0 / R1 | tool_joint3 | 129 / 55% / 4.0% | 82 / 60% / 7.6% |
| shared rare / M0 / R1 | fast_parent | 57 / 30% / 69.8% | 31 / 25% / 74.6% |
| shared rare / M1 / R0 | tool_ticket | 132 / 74% / 0.6% | 72 / 78% / 0.5% |
| shared rare / M1 / R0 | tool_ticket_memo | 120 / 76% / 1.1% | 70 / 79% / 1.1% |
| shared rare / M1 / R0 | tool_ticket_memo2 | 118 / 77% / 1.3% | 70 / 81% / 0.6% |
| shared rare / M1 / R0 | tool_joint | 126 / 76% / 0.7% | 81 / 82% / 0.6% |
| shared rare / M1 / R0 | tool_joint2 | 123 / 78% / 0.9% | 79 / 82% / 1.2% |
| shared rare / M1 / R0 | tool_joint3 | 126 / 76% / 1.1% | 80 / 82% / 0.8% |
| shared rare / M1 / R0 | fast_parent | 105 / 53% / 47.0% | 81 / 51% / 49.1% |
| shared rare / M1 / R1 | tool_ticket | 143 / 48% / 4.8% | 80 / 53% / 6.9% |
| shared rare / M1 / R1 | tool_ticket_memo | 126 / 53% / 4.9% | 72 / 58% / 7.3% |
| shared rare / M1 / R1 | tool_ticket_memo2 | 125 / 51% / 4.2% | 72 / 55% / 7.7% |
| shared rare / M1 / R1 | tool_joint | 137 / 53% / 5.5% | 80 / 59% / 7.2% |
| shared rare / M1 / R1 | tool_joint2 | 134 / 52% / 5.9% | 83 / 57% / 7.6% |
| shared rare / M1 / R1 | tool_joint3 | 131 / 53% / 4.3% | 82 / 57% / 7.0% |
| shared rare / M1 / R1 | fast_parent | 55 / 27% / 72.5% | 32 / 24% / 75.8% |
| shared rare / M2 / R0 | tool_ticket | 133 / 77% / 0.8% | 75 / 74% / 0.3% |
| shared rare / M2 / R0 | tool_ticket_memo | 121 / 78% / 0.9% | 72 / 77% / 0.9% |
| shared rare / M2 / R0 | tool_ticket_memo2 | 121 / 76% / 0.4% | 71 / 76% / 0.5% |
| shared rare / M2 / R0 | tool_joint | 130 / 78% / 1.1% | 81 / 78% / 0.6% |
| shared rare / M2 / R0 | tool_joint2 | 127 / 78% / 1.5% | 82 / 78% / 0.9% |
| shared rare / M2 / R0 | tool_joint3 | 128 / 77% / 1.1% | 83 / 77% / 1.3% |
| shared rare / M2 / R0 | fast_parent | 113 / 50% / 49.7% | 89 / 47% / 53.0% |
| shared rare / M2 / R1 | tool_ticket | 141 / 48% / 4.4% | 81 / 48% / 6.2% |
| shared rare / M2 / R1 | tool_ticket_memo | 124 / 50% / 5.2% | 75 / 50% / 8.2% |
| shared rare / M2 / R1 | tool_ticket_memo2 | 125 / 49% / 5.5% | 72 / 51% / 9.5% |
| shared rare / M2 / R1 | tool_joint | 134 / 51% / 6.4% | 84 / 52% / 7.0% |
| shared rare / M2 / R1 | tool_joint2 | 134 / 49% / 5.7% | 82 / 52% / 7.8% |
| shared rare / M2 / R1 | tool_joint3 | 133 / 53% / 5.6% | 85 / 51% / 8.8% |
| shared rare / M2 / R1 | fast_parent | 62 / 24% / 76.5% | 35 / 22% / 78.0% |
| shared assumed / M0 / R0 | tool_ticket | 151 / 78% / 0.6% | 93 / 77% / 1.3% |
| shared assumed / M0 / R0 | tool_ticket_memo | 114 / 78% / 1.0% | 64 / 83% / 0.7% |
| shared assumed / M0 / R0 | tool_ticket_memo2 | 112 / 80% / 0.7% | 65 / 82% / 1.1% |
| shared assumed / M0 / R0 | tool_joint | 124 / 80% / 0.8% | 71 / 85% / 0.9% |
| shared assumed / M0 / R0 | tool_joint2 | 119 / 80% / 0.8% | 71 / 84% / 1.2% |
| shared assumed / M0 / R0 | tool_joint2_la2 | 112 / 80% / 1.0% | 72 / 82% / 1.5% |
| shared assumed / M0 / R0 | tool_joint3 | 118 / 81% / 0.9% | 72 / 84% / 1.1% |
| shared assumed / M0 / R0 | fast_parent | 104 / 57% / 42.9% | 72 / 54% / 46.4% |
| shared assumed / M0 / R1 | tool_ticket | 169 / 48% / 5.4% | 100 / 53% / 7.9% |
| shared assumed / M0 / R1 | tool_ticket_memo | 122 / 55% / 4.4% | 66 / 58% / 7.0% |
| shared assumed / M0 / R1 | tool_ticket_memo2 | 116 / 56% / 5.0% | 69 / 61% / 7.7% |
| shared assumed / M0 / R1 | tool_joint | 132 / 56% / 4.5% | 80 / 63% / 6.9% |
| shared assumed / M0 / R1 | tool_joint2 | 124 / 58% / 4.8% | 79 / 60% / 6.7% |
| shared assumed / M0 / R1 | tool_joint3 | 129 / 55% / 4.6% | 77 / 57% / 8.5% |
| shared assumed / M0 / R1 | fast_parent | 59 / 30% / 70.3% | 31 / 29% / 71.3% |
| shared assumed / M1 / R0 | tool_ticket | 156 / 77% / 0.7% | 90 / 78% / 1.3% |
| shared assumed / M1 / R0 | tool_ticket_memo | 125 / 78% / 1.7% | 68 / 83% / 1.6% |
| shared assumed / M1 / R0 | tool_ticket_memo2 | 120 / 76% / 1.8% | 69 / 79% / 1.4% |
| shared assumed / M1 / R0 | tool_joint | 131 / 76% / 1.7% | 82 / 81% / 1.7% |
| shared assumed / M1 / R0 | tool_joint2 | 127 / 79% / 1.2% | 85 / 81% / 1.2% |
| shared assumed / M1 / R0 | tool_joint3 | 129 / 78% / 1.4% | 84 / 82% / 1.1% |
| shared assumed / M1 / R0 | fast_parent | 103 / 55% / 44.8% | 82 / 53% / 46.8% |
| shared assumed / M1 / R1 | tool_ticket | 172 / 50% / 4.9% | 102 / 53% / 6.3% |
| shared assumed / M1 / R1 | tool_ticket_memo | 132 / 55% / 4.3% | 75 / 58% / 7.4% |
| shared assumed / M1 / R1 | tool_ticket_memo2 | 131 / 54% / 4.4% | 72 / 58% / 9.0% |
| shared assumed / M1 / R1 | tool_joint | 143 / 53% / 3.8% | 91 / 60% / 9.3% |
| shared assumed / M1 / R1 | tool_joint2 | 140 / 56% / 3.8% | 90 / 59% / 8.5% |
| shared assumed / M1 / R1 | tool_joint3 | 137 / 56% / 5.2% | 88 / 61% / 8.2% |
| shared assumed / M1 / R1 | fast_parent | 62 / 32% / 67.6% | 34 / 29% / 70.8% |
| shared assumed / M2 / R0 | tool_ticket | 159 / 76% / 0.5% | 93 / 74% / 0.9% |
| shared assumed / M2 / R0 | tool_ticket_memo | 128 / 78% / 1.5% | 73 / 77% / 1.5% |
| shared assumed / M2 / R0 | tool_ticket_memo2 | 125 / 77% / 2.2% | 73 / 75% / 2.0% |
| shared assumed / M2 / R0 | tool_joint | 140 / 79% / 1.3% | 89 / 80% / 1.9% |
| shared assumed / M2 / R0 | tool_joint2 | 137 / 79% / 1.7% | 90 / 75% / 2.5% |
| shared assumed / M2 / R0 | tool_joint3 | 136 / 77% / 2.3% | 90 / 79% / 1.5% |
| shared assumed / M2 / R0 | fast_parent | 112 / 51% / 49.1% | 93 / 49% / 50.6% |
| shared assumed / M2 / R1 | tool_ticket | 169 / 49% / 4.6% | 98 / 49% / 7.4% |
| shared assumed / M2 / R1 | tool_ticket_memo | 133 / 53% / 5.9% | 75 / 53% / 9.4% |
| shared assumed / M2 / R1 | tool_ticket_memo2 | 127 / 52% / 6.0% | 76 / 53% / 8.0% |
| shared assumed / M2 / R1 | tool_joint | 147 / 52% / 5.1% | 90 / 54% / 9.2% |
| shared assumed / M2 / R1 | tool_joint2 | 141 / 54% / 4.8% | 90 / 53% / 9.5% |
| shared assumed / M2 / R1 | tool_joint3 | 141 / 54% / 5.1% | 91 / 52% / 8.2% |
| shared assumed / M2 / R1 | fast_parent | 65 / 30% / 70.0% | 35 / 25% / 74.9% |
| shared common / M0 / R0 | tool_ticket | 202 / 81% / 0.4% | 134 / 80% / 1.0% |
| shared common / M0 / R0 | tool_ticket_memo | 114 / 84% / 1.3% | 60 / 85% / 1.6% |
| shared common / M0 / R0 | tool_ticket_memo2 | 108 / 83% / 1.3% | 58 / 84% / 2.0% |
| shared common / M0 / R0 | tool_joint | 120 / 83% / 1.2% | 74 / 87% / 1.8% |
| shared common / M0 / R0 | tool_joint2 | 117 / 84% / 1.5% | 72 / 88% / 1.6% |
| shared common / M0 / R0 | tool_joint2_la2 | 112 / 85% / 1.1% | 72 / 85% / 2.2% |
| shared common / M0 / R0 | tool_joint3 | 118 / 83% / 1.3% | 73 / 86% / 1.4% |
| shared common / M0 / R0 | fast_parent | 101 / 63% / 37.3% | 74 / 57% / 42.6% |
| shared common / M0 / R1 | tool_ticket | 230 / 53% / 4.0% | 143 / 58% / 7.2% |
| shared common / M0 / R1 | tool_ticket_memo | 130 / 62% / 3.9% | 65 / 67% / 6.0% |
| shared common / M0 / R1 | tool_ticket_memo2 | 115 / 65% / 3.3% | 64 / 67% / 6.5% |
| shared common / M0 / R1 | tool_joint | 141 / 63% / 5.3% | 79 / 68% / 7.7% |
| shared common / M0 / R1 | tool_joint2 | 128 / 65% / 3.5% | 80 / 67% / 6.8% |
| shared common / M0 / R1 | tool_joint3 | 128 / 67% / 4.7% | 78 / 68% / 7.2% |
| shared common / M0 / R1 | fast_parent | 60 / 39% / 61.2% | 34 / 39% / 61.1% |
| shared common / M1 / R0 | tool_ticket | 217 / 80% / 0.6% | 138 / 78% / 1.4% |
| shared common / M1 / R0 | tool_ticket_memo | 136 / 81% / 2.0% | 73 / 82% / 2.5% |
| shared common / M1 / R0 | tool_ticket_memo2 | 128 / 78% / 2.1% | 71 / 82% / 2.9% |
| shared common / M1 / R0 | tool_joint | 148 / 82% / 2.1% | 97 / 84% / 2.8% |
| shared common / M1 / R0 | tool_joint2 | 143 / 80% / 2.5% | 97 / 84% / 2.2% |
| shared common / M1 / R0 | tool_joint3 | 145 / 82% / 2.5% | 98 / 84% / 2.1% |
| shared common / M1 / R0 | fast_parent | 114 / 61% / 39.4% | 89 / 58% / 42.4% |
| shared common / M1 / R1 | tool_ticket | 245 / 51% / 4.4% | 150 / 57% / 6.6% |
| shared common / M1 / R1 | tool_ticket_memo | 148 / 59% / 5.7% | 77 / 63% / 8.4% |
| shared common / M1 / R1 | tool_ticket_memo2 | 138 / 58% / 5.2% | 75 / 64% / 8.1% |
| shared common / M1 / R1 | tool_joint | 169 / 61% / 5.1% | 101 / 63% / 8.9% |
| shared common / M1 / R1 | tool_joint2 | 152 / 61% / 6.9% | 104 / 64% / 7.6% |
| shared common / M1 / R1 | tool_joint3 | 155 / 61% / 5.2% | 106 / 65% / 8.0% |
| shared common / M1 / R1 | fast_parent | 71 / 38% / 61.7% | 38 / 39% / 61.0% |
| shared common / M2 / R0 | tool_ticket | 219 / 79% / 1.2% | 138 / 76% / 1.1% |
| shared common / M2 / R0 | tool_ticket_memo | 142 / 79% / 1.8% | 74 / 78% / 2.6% |
| shared common / M2 / R0 | tool_ticket_memo2 | 133 / 79% / 1.7% | 74 / 76% / 2.6% |
| shared common / M2 / R0 | tool_joint | 155 / 82% / 1.5% | 103 / 79% / 2.4% |
| shared common / M2 / R0 | tool_joint2 | 148 / 80% / 2.0% | 101 / 82% / 2.3% |
| shared common / M2 / R0 | tool_joint3 | 147 / 80% / 2.0% | 102 / 80% / 3.2% |
| shared common / M2 / R0 | fast_parent | 130 / 59% / 40.8% | 96 / 57% / 43.1% |
| shared common / M2 / R1 | tool_ticket | 246 / 50% / 5.6% | 149 / 54% / 7.1% |
| shared common / M2 / R1 | tool_ticket_memo | 148 / 59% / 5.4% | 78 / 61% / 8.5% |
| shared common / M2 / R1 | tool_ticket_memo2 | 138 / 59% / 6.3% | 78 / 57% / 10.2% |
| shared common / M2 / R1 | tool_joint | 169 / 59% / 6.1% | 110 / 60% / 9.3% |
| shared common / M2 / R1 | tool_joint2 | 164 / 61% / 5.5% | 105 / 61% / 8.4% |
| shared common / M2 / R1 | tool_joint3 | 152 / 60% / 6.8% | 109 / 62% / 9.1% |
| shared common / M2 / R1 | fast_parent | 72 / 37% / 63.4% | 41 / 33% / 67.3% |

## Predictions (written before the run; each strict)

| prediction | holds | values |
|---|---|---|
| P1 | holds | joint2 vs joint, T2, shared: -25% minutes |
| P2 | holds | ticket_memo2 vs ticket_memo, T2, shared: -15% minutes |
| P3 | holds | joint2 vs joint, T3, shared: -4% minutes |
| P4 | holds | joint2 vs ticket_memo2, T2, shared: NEITHER (+17% minutes, accuracy SAME) |
| P5 | does not hold | joint2 vs ticket_memo2, T2, shared: +17% minutes |
| P6 | holds | wrong-and-confident, joint2 vs joint, all events: T2: 0.008 vs 0.008; T3: 0.012 vs 0.009 |
| P7 | holds | accuracy, joint2 vs joint, all events: T2: 0.802 vs 0.798; T3: 0.843 vs 0.845 |
| P8 | holds | T2 wrong-and-confident, joint2 minus ticket_memo2, all events: M1: -0.006; M2: -0.005 |
| P9 | holds | look-ahead vs one-step, shared events, three cells: T2: ['NEITHER', 'NEITHER', 'NEITHER']; T3: ['WORSE', 'NEITHER', 'NEITHER'] |
| P10 | holds | single events, joint2 vs joint: T2: 1.1%; T3: 2.1% |
| P11 | does not hold | joint3 vs joint2, T2, shared: -5% minutes |

## Frozen decision: THE ROUTINE STILL WINS

Run time 315 s.
