# The v1 tool against fast stand-in technicians (Addendum 28)

The complaints, data tiers and simulated answers of Addendum 27; the tool's episodes are Addendum 27's, reproduced. 12 cells, 500 paired episodes each. Three stand-ins, ALL MY CONSTRUCTIONS and none a real technician: `habit_A` (v0's fast stand-in: it can answer only in v0's four lumps), `fast_list` (cheapest-first checklist of single-cause checks; the first abnormal reading concludes) and `fast_confirm` (a finding must be confirmed). They are charged the tool's own minutes, get the world's facts for free, ask nothing, and always conclude, so their wrong-and-confident rate is their whole error rate. Everything is simulated from the tool's own model family with placeholder numbers; nothing here is evidence about real technicians.

## Gates

| gate | result | detail |
|---|---|---|
| G1 code path | PASS | habit_A = v0's simulate_habit on 20 episodes; the tool's episodes equal Addendum 27's raw file in all 12 cells |
| G2 accounting | PASS | hand-summed minutes agree; 1200 degraded-reliability stand-in episodes replay identically from their answers alone |
| G3 availability | PASS | ok |
| G4 reproducibility | PASS | first 50 episodes of cell 0 reproduce |
| G5 completeness and pairing | PASS | ok |

## Primary cell (R0 / assumed / full), hardware / configuration-cause episodes (n = 438), EXACT cause

| arm | policy | minutes | accuracy | wrong-and-confident | checks | entries typed | minutes per correct | unresolved |
|---|---|---|---|---|---|---|---|---|
| T0 | tool | 88 | 72% | 0% | 8.3 | 12.2 | 123 | 82% |
| T0 | fast_list | 66 | 47% | 53% | 6.2 | 7.2 | 141 | 0% (always concludes) |
| T0 | fast_confirm | 82 | 41% | 59% | 7.5 | 8.5 | 198 | 0% (always concludes) |
| T1 | tool | 91 | 71% | 0% | 8.6 | 12.5 | 128 | 79% |
| T1 | fast_list | 79 | 44% | 56% | 7.7 | 8.7 | 178 | 0% (always concludes) |
| T1 | fast_confirm | 101 | 38% | 62% | 9.7 | 10.7 | 266 | 0% (always concludes) |
| T2 | tool | 85 | 77% | 0% | 8.6 | 11.9 | 111 | 77% |
| T2 | fast_list | 79 | 46% | 54% | 8.1 | 9.1 | 172 | 0% (always concludes) |
| T2 | fast_confirm | 105 | 40% | 60% | 10.5 | 11.5 | 262 | 0% (always concludes) |
| T2+access | tool | 85 | 84% | 0% | 9.1 | 11.2 | 102 | 57% |
| T2+access | fast_list | 91 | 43% | 57% | 8.9 | 9.9 | 209 | 0% (always concludes) |
| T2+access | fast_confirm | 135 | 45% | 55% | 12.7 | 13.7 | 298 | 0% (always concludes) |
| T3 | tool | 48 | 82% | 0% | 9.2 | 10.8 | 59 | 51% |
| T3 | fast_list | 56 | 45% | 55% | 8.3 | 9.3 | 125 | 0% (always concludes) |
| T3 | fast_confirm | 95 | 42% | 58% | 12.6 | 13.6 | 224 | 0% (always concludes) |

## Same cell, hardware episodes, v0's LEVEL (four lumps): the level `habit_A` can answer at

The last column is the accuracy of always guessing 'the box acts, the cause is elsewhere', the base rate any lump-level accuracy must be read against.

| arm | tool | habit_A | fast_list | fast_confirm | constant guess |
|---|---|---|---|---|---|
| T0 | 88 min / 98% / 0% | 13 min / 72% / 28% | 66 min / 83% / 17% | 82 min / 84% / 16% | 82% |
| T1 | 91 min / 97% / 0% | 27 min / 72% / 28% | 79 min / 66% / 34% | 101 min / 63% / 37% | 82% |
| T2 | 85 min / 97% / 0% | 27 min / 72% / 28% | 79 min / 69% / 31% | 105 min / 66% / 34% | 82% |
| T2+access | 85 min / 97% / 0% | 27 min / 72% / 28% | 91 min / 71% / 29% | 135 min / 69% / 31% | 82% |
| T3 | 48 min / 97% / 0% | 27 min / 72% / 28% | 56 min / 74% / 26% | 95 min / 71% / 29% | 82% |

## Same cell, episodes where the drawings are wrong (n = 62; T1 and up): minutes / accuracy exact / accuracy at v0's level

| arm | tool | habit_A | fast_list | fast_confirm |
|---|---|---|---|---|
| T1 | 97 / 82% / 82% | 43 / n/a / 63% | 116 / 56% / 56% | 132 / 61% / 61% |
| T2 | 100 / 81% / 81% | 43 / n/a / 63% | 119 / 47% / 47% | 132 / 55% / 55% |
| T2+access | 100 / 82% / 82% | 43 / n/a / 63% | 152 / 39% / 39% | 198 / 58% / 58% |
| T3 | 83 / 74% / 74% | 43 / n/a / 63% | 110 / 37% / 37% | 150 / 60% / 60% |

## The tool against each stand-in, over the 12 cells (tool minus stand-in on the same episodes)

Labels are Addendum 21's (IMPROVES / WORSE / TRADE / NEITHER at 5% minutes and 0.02 accuracy, paired 95% intervals); TRADE in brackets: the tool faster but less accurate (F/L) or slower but more accurate (S/M); SAFETY REG = share of cells where the tool's wrong-and-confident rate is at least 0.02 higher with the interval clear of 0 (GAIN: lower). No verdict rule. The last column is the break-even cost of a wrong diagnosis on the primary cell's means (the extra minutes it must cost before the tool's extra time pays, or the cost below which a faster, less accurate tool is ahead).

| arm | stand-in | subset | level | IMPROVES | WORSE | TRADE (F/L, S/M) | NEITHER | SAFETY REG / GAIN | primary: d minutes | d accuracy | d wrong-and-confident | break-even wrong-diagnosis cost |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T0 | fast_list | hardware | exact | 0% | 0% | 100% (0%, 100%) | 0% | 0% / 100% | +23 (+35%) | +0.256 | -0.532 | 89 min (tool wins above) |
| T1 | fast_list | hardware | exact | 0% | 0% | 100% (0%, 100%) | 0% | 0% / 100% | +12 (+16%) | +0.269 | -0.553 | 46 min (tool wins above) |
| T2 | fast_list | hardware | exact | 8% | 0% | 92% (0%, 92%) | 0% | 0% / 100% | +6 (+8%) | +0.313 | -0.539 | 21 min (tool wins above) |
| T2+access | fast_list | hardware | exact | 25% | 0% | 75% (0%, 75%) | 0% | 0% / 100% | -5 (-6%) | +0.404 | -0.564 | tool ahead on both |
| T3 | fast_list | hardware | exact | 33% | 0% | 67% (0%, 67%) | 0% | 0% / 100% | -7 (-13%) | +0.379 | -0.550 | tool ahead on both |
| T0 | fast_confirm | hardware | exact | 25% | 0% | 75% (0%, 75%) | 0% | 0% / 100% | +6 (+8%) | +0.308 | -0.584 | 21 min (tool wins above) |
| T1 | fast_confirm | hardware | exact | 33% | 0% | 67% (0%, 67%) | 0% | 0% / 100% | -10 (-9%) | +0.333 | -0.616 | tool ahead on both |
| T2 | fast_confirm | hardware | exact | 33% | 0% | 67% (0%, 67%) | 0% | 0% / 100% | -20 (-19%) | +0.368 | -0.594 | tool ahead on both |
| T2+access | fast_confirm | hardware | exact | 83% | 0% | 17% (0%, 17%) | 0% | 0% / 100% | -50 (-37%) | +0.386 | -0.546 | tool ahead on both |
| T3 | fast_confirm | hardware | exact | 75% | 8% | 17% (0%, 17%) | 0% | 0% / 100% | -47 (-49%) | +0.400 | -0.571 | tool ahead on both |
| T0 | habit_A | hardware | v0 | 0% | 0% | 100% (0%, 100%) | 0% | 0% / 100% | +75 (+580%) | +0.253 | -0.276 | 297 min (tool wins above) |
| T1 | habit_A | hardware | v0 | 0% | 0% | 100% (0%, 100%) | 0% | 0% / 100% | +65 (+241%) | +0.251 | -0.276 | 258 min (tool wins above) |
| T2 | habit_A | hardware | v0 | 0% | 0% | 100% (0%, 100%) | 0% | 0% / 100% | +58 (+217%) | +0.242 | -0.276 | 241 min (tool wins above) |
| T2+access | habit_A | hardware | v0 | 0% | 0% | 100% (0%, 100%) | 0% | 0% / 100% | +58 (+217%) | +0.244 | -0.276 | 239 min (tool wins above) |
| T3 | habit_A | hardware | v0 | 0% | 0% | 100% (0%, 100%) | 0% | 0% / 100% | +21 (+80%) | +0.247 | -0.276 | 87 min (tool wins above) |
| T0 | fast_list | hardware | v0 | 0% | 0% | 100% (0%, 100%) | 0% | 0% / 100% | +23 (+35%) | +0.148 | -0.171 | 153 min (tool wins above) |
| T1 | fast_list | hardware | v0 | 0% | 0% | 100% (0%, 100%) | 0% | 0% / 100% | +12 (+16%) | +0.311 | -0.336 | 40 min (tool wins above) |
| T2 | fast_list | hardware | v0 | 8% | 0% | 92% (0%, 92%) | 0% | 0% / 100% | +6 (+8%) | +0.274 | -0.308 | 23 min (tool wins above) |
| T2+access | fast_list | hardware | v0 | 25% | 0% | 75% (0%, 75%) | 0% | 0% / 100% | -5 (-6%) | +0.263 | -0.295 | tool ahead on both |
| T3 | fast_list | hardware | v0 | 33% | 0% | 67% (0%, 67%) | 0% | 0% / 100% | -7 (-13%) | +0.231 | -0.260 | tool ahead on both |
| T0 | fast_confirm | hardware | v0 | 25% | 0% | 75% (0%, 75%) | 0% | 0% / 100% | +6 (+8%) | +0.139 | -0.162 | 46 min (tool wins above) |
| T1 | fast_confirm | hardware | v0 | 33% | 0% | 67% (0%, 67%) | 0% | 0% / 100% | -10 (-9%) | +0.340 | -0.365 | tool ahead on both |
| T2 | fast_confirm | hardware | v0 | 33% | 0% | 67% (0%, 67%) | 0% | 0% / 100% | -20 (-19%) | +0.311 | -0.345 | tool ahead on both |
| T2+access | fast_confirm | hardware | v0 | 83% | 0% | 17% (0%, 17%) | 0% | 0% / 100% | -50 (-37%) | +0.279 | -0.311 | tool ahead on both |
| T3 | fast_confirm | hardware | v0 | 75% | 0% | 25% (0%, 25%) | 0% | 0% / 100% | -47 (-49%) | +0.265 | -0.295 | tool ahead on both |
| T1 | fast_list | drawings wrong | exact | 33% | 8% | 58% (0%, 58%) | 0% | 0% / 100% | -18 (-16%) | +0.258 | -0.435 | tool ahead on both |
| T2 | fast_list | drawings wrong | exact | 33% | 0% | 67% (0%, 67%) | 0% | 0% / 100% | -20 (-16%) | +0.339 | -0.532 | tool ahead on both |
| T2+access | fast_list | drawings wrong | exact | 25% | 8% | 58% (0%, 58%) | 8% | 0% / 100% | -52 (-34%) | +0.435 | -0.581 | tool ahead on both |
| T3 | fast_list | drawings wrong | exact | 25% | 8% | 58% (0%, 58%) | 8% | 0% / 100% | -26 (-24%) | +0.371 | -0.629 | tool ahead on both |
| T1 | fast_confirm | drawings wrong | exact | 50% | 17% | 17% (0%, 17%) | 17% | 0% / 100% | -35 (-26%) | +0.210 | -0.387 | tool ahead on both |
| T2 | fast_confirm | drawings wrong | exact | 50% | 8% | 25% (0%, 25%) | 17% | 0% / 100% | -32 (-24%) | +0.258 | -0.452 | tool ahead on both |
| T2+access | fast_confirm | drawings wrong | exact | 83% | 0% | 0% (0%, 0%) | 17% | 0% / 100% | -98 (-49%) | +0.242 | -0.387 | tool ahead on both |
| T3 | fast_confirm | drawings wrong | exact | 75% | 0% | 0% (0%, 0%) | 25% | 0% / 100% | -67 (-44%) | +0.145 | -0.403 | tool ahead on both |
| T1 | habit_A | drawings wrong | v0 | 0% | 75% | 25% (0%, 25%) | 0% | 0% / 100% | +55 (+128%) | +0.194 | -0.371 | 283 min (tool wins above) |
| T2 | habit_A | drawings wrong | v0 | 0% | 67% | 33% (0%, 33%) | 0% | 0% / 100% | +57 (+134%) | +0.177 | -0.371 | 323 min (tool wins above) |
| T2+access | habit_A | drawings wrong | v0 | 0% | 83% | 17% (0%, 17%) | 0% | 0% / 100% | +57 (+134%) | +0.194 | -0.339 | 296 min (tool wins above) |
| T3 | habit_A | drawings wrong | v0 | 0% | 100% | 0% (0%, 0%) | 0% | 0% / 100% | +41 (+96%) | +0.113 | -0.371 | 361 min (tool wins above) |
| T1 | fast_list | drawings wrong | v0 | 33% | 8% | 58% (0%, 58%) | 0% | 0% / 100% | -18 (-16%) | +0.258 | -0.435 | tool ahead on both |
| T2 | fast_list | drawings wrong | v0 | 33% | 0% | 67% (0%, 67%) | 0% | 0% / 100% | -20 (-16%) | +0.339 | -0.532 | tool ahead on both |
| T2+access | fast_list | drawings wrong | v0 | 25% | 8% | 58% (0%, 58%) | 8% | 0% / 100% | -52 (-34%) | +0.435 | -0.581 | tool ahead on both |
| T3 | fast_list | drawings wrong | v0 | 25% | 8% | 58% (0%, 58%) | 8% | 0% / 100% | -26 (-24%) | +0.371 | -0.629 | tool ahead on both |
| T1 | fast_confirm | drawings wrong | v0 | 50% | 17% | 17% (0%, 17%) | 17% | 0% / 100% | -35 (-26%) | +0.210 | -0.387 | tool ahead on both |
| T2 | fast_confirm | drawings wrong | v0 | 50% | 8% | 25% (0%, 25%) | 17% | 0% / 100% | -32 (-24%) | +0.258 | -0.452 | tool ahead on both |
| T2+access | fast_confirm | drawings wrong | v0 | 83% | 0% | 0% (0%, 0%) | 17% | 0% / 100% | -98 (-49%) | +0.242 | -0.387 | tool ahead on both |
| T3 | fast_confirm | drawings wrong | v0 | 75% | 0% | 0% (0%, 0%) | 25% | 0% / 100% | -67 (-44%) | +0.145 | -0.403 | tool ahead on both |

## Every cell, hardware episodes, exact level: tool | fast_list | fast_confirm as minutes / accuracy / wrong-and-confident

| reliability / mix / coverage | arm | tool | fast_list | fast_confirm |
|---|---|---|---|---|
| R0 / assumed / full | T0 | 88 / 72% / 0% | 66 / 47% / 53% | 82 / 41% / 59% |
| R0 / assumed / full | T1 | 91 / 71% / 0% | 79 / 44% / 56% | 101 / 38% / 62% |
| R0 / assumed / full | T2 | 85 / 77% / 0% | 79 / 46% / 54% | 105 / 40% / 60% |
| R0 / assumed / full | T2+access | 85 / 84% / 0% | 91 / 43% / 57% | 135 / 45% / 55% |
| R0 / assumed / full | T3 | 48 / 82% / 0% | 56 / 45% / 55% | 95 / 42% / 58% |
| R0 / assumed / half | T0 | 89 / 74% / 0% | 65 / 47% / 53% | 86 / 41% / 59% |
| R0 / assumed / half | T1 | 92 / 73% / 0% | 79 / 45% / 55% | 106 / 38% / 62% |
| R0 / assumed / half | T2 | 91 / 73% / 1% | 78 / 48% / 52% | 104 / 36% / 64% |
| R0 / assumed / half | T2+access | 86 / 84% / 0% | 94 / 48% / 52% | 135 / 49% / 51% |
| R0 / assumed / half | T3 | 70 / 79% / 1% | 77 / 47% / 53% | 115 / 48% / 52% |
| R0 / shifted / full | T0 | 86 / 68% / 1% | 67 / 50% / 50% | 87 / 49% / 51% |
| R0 / shifted / full | T1 | 87 / 73% / 0% | 77 / 48% / 52% | 105 / 46% / 54% |
| R0 / shifted / full | T2 | 82 / 75% / 0% | 77 / 51% / 49% | 102 / 46% / 54% |
| R0 / shifted / full | T2+access | 84 / 79% / 2% | 83 / 52% / 48% | 133 / 46% / 54% |
| R0 / shifted / full | T3 | 51 / 79% / 1% | 53 / 52% / 48% | 90 / 49% / 51% |
| R0 / shifted / half | T0 | 85 / 69% / 0% | 70 / 49% / 51% | 88 / 54% / 46% |
| R0 / shifted / half | T1 | 89 / 71% / 1% | 83 / 45% / 55% | 104 / 49% / 51% |
| R0 / shifted / half | T2 | 86 / 72% / 1% | 79 / 50% / 50% | 103 / 50% / 50% |
| R0 / shifted / half | T2+access | 90 / 80% / 1% | 83 / 52% / 48% | 132 / 46% / 54% |
| R0 / shifted / half | T3 | 73 / 78% / 1% | 71 / 50% / 50% | 113 / 47% / 53% |
| R1 / assumed / full | T0 | 89 / 50% / 4% | 42 / 24% / 76% | 73 / 25% / 75% |
| R1 / assumed / full | T1 | 95 / 45% / 5% | 44 / 22% / 78% | 83 / 22% / 78% |
| R1 / assumed / full | T2 | 91 / 44% / 6% | 39 / 25% / 75% | 77 / 25% / 75% |
| R1 / assumed / full | T2+access | 91 / 54% / 8% | 43 / 23% / 77% | 112 / 29% / 71% |
| R1 / assumed / full | T3 | 53 / 54% / 7% | 21 / 25% / 75% | 72 / 31% / 69% |
| R1 / assumed / half | T0 | 87 / 56% / 3% | 40 / 25% / 75% | 72 / 26% / 74% |
| R1 / assumed / half | T1 | 96 / 46% / 1% | 43 / 25% / 75% | 81 / 24% / 76% |
| R1 / assumed / half | T2 | 90 / 50% / 5% | 42 / 24% / 76% | 78 / 27% / 73% |
| R1 / assumed / half | T2+access | 95 / 55% / 5% | 46 / 23% / 77% | 103 / 28% / 72% |
| R1 / assumed / half | T3 | 76 / 56% / 9% | 34 / 25% / 75% | 87 / 26% / 74% |
| R1 / shifted / full | T0 | 89 / 47% / 3% | 40 / 24% / 76% | 73 / 32% / 68% |
| R1 / shifted / full | T1 | 92 / 44% / 4% | 41 / 23% / 77% | 80 / 28% / 72% |
| R1 / shifted / full | T2 | 86 / 48% / 4% | 37 / 23% / 77% | 75 / 28% / 72% |
| R1 / shifted / full | T2+access | 90 / 52% / 7% | 38 / 25% / 75% | 106 / 30% / 70% |
| R1 / shifted / full | T3 | 54 / 48% / 8% | 17 / 29% / 71% | 72 / 31% / 69% |
| R1 / shifted / half | T0 | 87 / 49% / 2% | 42 / 26% / 74% | 70 / 31% / 69% |
| R1 / shifted / half | T1 | 90 / 46% / 3% | 45 / 25% / 75% | 75 / 27% / 73% |
| R1 / shifted / half | T2 | 86 / 50% / 4% | 41 / 27% / 73% | 72 / 26% / 74% |
| R1 / shifted / half | T2+access | 94 / 52% / 7% | 44 / 30% / 70% | 97 / 34% / 66% |
| R1 / shifted / half | T3 | 75 / 48% / 6% | 34 / 31% / 69% | 79 / 35% / 65% |
| R2 / assumed / full | T0 | 87 / 34% / 5% | 28 / 16% / 84% | 59 / 20% / 80% |
| R2 / assumed / full | T1 | 94 / 27% / 7% | 28 / 16% / 84% | 63 / 19% / 81% |
| R2 / assumed / full | T2 | 91 / 31% / 12% | 26 / 13% / 87% | 52 / 19% / 81% |
| R2 / assumed / full | T2+access | 91 / 29% / 15% | 29 / 14% / 86% | 88 / 21% / 79% |
| R2 / assumed / full | T3 | 54 / 35% / 14% | 11 / 14% / 86% | 53 / 23% / 77% |
| R2 / assumed / half | T0 | 92 / 29% / 8% | 28 / 14% / 86% | 57 / 17% / 83% |
| R2 / assumed / half | T1 | 95 / 29% / 11% | 29 / 14% / 86% | 60 / 15% / 85% |
| R2 / assumed / half | T2 | 94 / 27% / 11% | 28 / 13% / 87% | 57 / 15% / 85% |
| R2 / assumed / half | T2+access | 95 / 32% / 16% | 30 / 12% / 88% | 88 / 17% / 83% |
| R2 / assumed / half | T3 | 76 / 35% / 15% | 22 / 13% / 87% | 70 / 17% / 83% |
| R2 / shifted / full | T0 | 87 / 30% / 6% | 29 / 15% / 85% | 56 / 20% / 80% |
| R2 / shifted / full | T1 | 92 / 26% / 11% | 29 / 15% / 85% | 59 / 18% / 82% |
| R2 / shifted / full | T2 | 88 / 28% / 10% | 27 / 16% / 84% | 53 / 18% / 82% |
| R2 / shifted / full | T2+access | 89 / 31% / 14% | 27 / 21% / 79% | 83 / 17% / 83% |
| R2 / shifted / full | T3 | 52 / 28% / 17% | 11 / 21% / 79% | 45 / 24% / 76% |
| R2 / shifted / half | T0 | 85 / 30% / 6% | 27 / 14% / 86% | 55 / 17% / 83% |
| R2 / shifted / half | T1 | 90 / 27% / 8% | 27 / 14% / 86% | 58 / 16% / 84% |
| R2 / shifted / half | T2 | 89 / 26% / 9% | 26 / 14% / 86% | 56 / 14% / 86% |
| R2 / shifted / half | T2+access | 95 / 29% / 14% | 29 / 14% / 86% | 76 / 17% / 83% |
| R2 / shifted / half | T3 | 78 / 28% / 18% | 22 / 17% / 83% | 61 / 20% / 80% |

## Predictions (written before the run; each strict)

| prediction | holds | values |
|---|---|---|
| P1 | does not hold | {'T0': (65.70547945205479, 88.38356164383562), 'T1': (79.03424657534246, 91.47488584474885), 'T2': (78.64155251141553, 85.05479452054794), 'T2+access': (90.51826484018265, 85.06849315068493)} |
| P2 | holds | {'T0': (0.7214611872146118, 0.4657534246575342), 'T1': (0.7123287671232876, 0.4429223744292237), 'T2': (0.769406392694064, 0.45662100456621), 'T2+access': (0.8378995433789954, 0.4337899543378995), 'T3': (0.8242009132420092, 0.4452054794520548)} |
| P3 | holds | {'T0': (0.00228310502283105, 0.5342465753424658), 'T1': (0.0045662100456621, 0.5570776255707762), 'T2': (0.0045662100456621, 0.54337899543379), 'T2+access': (0.00228310502283105, 0.5662100456621004), 'T3': (0.0045662100456621, 0.5547945205479452)} |
| P4 | does not hold | {'T0': (81.91095890410959, 65.70547945205479, 0.4132420091324201, 0.4657534246575342), 'T1': (100.9771689497717, 79.03424657534246, 0.3789954337899543, 0.4429223744292237), 'T2': (105.34703196347031, 78.64155251141553, 0.4018264840182648, 0.45662100456621), 'T2+access': (134.79223744292239, 90.51826484018265, 0.4520547945205479, 0.4337899543378995), 'T3': (94.96118721461187, 55.64840182648402, 0.4246575342465753, 0.4452054794520548)} |
| P5 | holds | {'T0': (0.7214611872146118, 0.4132420091324201), 'T1': (0.7123287671232876, 0.3789954337899543), 'T2': (0.769406392694064, 0.4018264840182648), 'T2+access': (0.8378995433789954, 0.4520547945205479), 'T3': (0.8242009132420092, 0.4246575342465753)} |
| P6 | holds | {'T1': (0.9748858447488584, 0.723744292237443), 'T2': (0.9657534246575342, 0.723744292237443), 'T2+access': (0.9680365296803652, 0.723744292237443), 'T3': (0.9703196347031964, 0.723744292237443)} |
| P7 | holds | {'T0': (0.18544600938967137, 0.2557077625570776), 'T1': (0.11502347417840375, 0.2694063926940639), 'T2': (0.176056338028169, 0.31278538812785395), 'T2+access': (0.15727699530516434, 0.4041095890410959), 'T3': (0.20892018779342722, 0.3789954337899544)} |
| P8 | holds | (0.8672766062197423, 1.3451475033878872) |
| P9 | holds | {'T1': (0.8225806451612904, 0.5645161290322581), 'T2': (0.8064516129032258, 0.46774193548387094), 'T2+access': (0.8225806451612904, 0.3870967741935484), 'T3': (0.7419354838709677, 0.3709677419354839)} |

Run time 32 s.
