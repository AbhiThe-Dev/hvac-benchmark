# What each data tier buys (Addendum 27)

A synthetic building (8 rooms, 8 boxes, 2 air handlers); complaints whose true cause is drawn from the v1 cause tree; the tool given five amounts of data (the arms). 12 cells = 3 reliabilities x 2 cause mixes x 2 data coverages, 500 paired episodes x 5 arms each. Answers and causes are SIMULATED from the tool's own model family; every probability and every minute is a placeholder, so only orderings and ratios mean anything, and nothing here is evidence about real technicians. Hardware / configuration-cause episodes are the ones every arm can be compared on (T0 has no drawings to be wrong).

## Gates

| gate | result | detail |
|---|---|---|
| G1 code path | PASS | v0-equivalent tree = v0 on 12 episodes x 2 strategies; stored episodes = direct calls |
| G2 accounting | PASS | hand-summed minutes agree; 400 degraded-reliability episodes replay identically from their answers alone |
| G3 honesty | PASS | full/T0: 0.988 (n=80); full/T1: 0.978 (n=93); full/T2: 0.980 (n=101); full/T2+access: 0.995 (n=190); full/T3: 0.991 (n=214); half/T0: 0.986 (n=74); half/T1: 0.987 (n=79); half/T2: 0.952 (n=83); half/T2+access: 0.990 (n=206); half/T3: 0.985 (n=198) |
| G4 reproducibility | PASS | first 50 episodes of cell 0 reproduce |
| G5 completeness and pairing | PASS | ok |
| G6 availability | PASS | ok |

## The primary cell (R0 / assumed / full): hardware / configuration-cause episodes (n = 438)

| arm | minutes | accuracy | right branch | wrong-and-confident | checks | questions asked | entries typed | concluded | stopped (nothing worth its time) | hit the check limit |
|---|---|---|---|---|---|---|---|---|---|---|
| T0 | 88 | 72% | 75% | 0% | 8.3 | 3.0 | 12.2 | 18% | 68% | 13% |
| T1 | 91 | 71% | 72% | 0% | 8.6 | 2.9 | 12.5 | 21% | 60% | 19% |
| T2 | 85 | 77% | 79% | 0% | 8.6 | 2.3 | 11.9 | 23% | 50% | 27% |
| T2+access | 85 | 84% | 85% | 0% | 9.1 | 1.1 | 11.2 | 43% | 24% | 33% |
| T3 | 48 | 82% | 84% | 0% | 9.2 | 0.6 | 10.8 | 49% | 11% | 40% |

## Each step up, over the 12 cells (the richer arm minus the poorer, on the same episodes)

Labels are the frozen ones of Addendum 21 (IMPROVES / WORSE / TRADE / NEITHER at 5% minutes and 0.02 accuracy with paired 95% intervals). TRADE has two kinds, shown in brackets: the richer arm is faster but less accurate (F/L) or slower but more accurate (S/M). SAFETY REG is the share of cells where the wrong-and-confident rate is at least 0.02 higher with the interval clear of 0. The reading (adjacent steps only) is HELPS if IMPROVES >= 75% and WORSE + TRADE <= 10%, HURTS if WORSE + TRADE > 25%, otherwise MIXED.

| step | IMPROVES | WORSE | TRADE (F/L, S/M) | NEITHER | SAFETY REG | reading | primary cell: d minutes | d accuracy | d wrong-and-confident |
|---|---|---|---|---|---|---|---|---|---|
| T1 vs T0 (add the equipment list and the drawings' claims) | 0% | 42% | 0% (0%, 0%) | 58% | 8% | **HURTS** | +3.1 (+3%) | -0.009 | +0.002 |
| T2 vs T1 (add attributes and design values) | 33% | 0% | 0% (0%, 0%) | 67% | 17% | **MIXED** | -6.4 (-7%) | +0.057 | +0.000 |
| T2+access vs T2 (add control-system access, no point map) | 33% | 17% | 0% (0%, 0%) | 50% | 25% | **MIXED** | +0.0 (+0%) | +0.068 | -0.002 |
| T3 vs T2+access (add the point map) | 100% | 0% | 0% (0%, 0%) | 0% | 0% | **HELPS** | -36.8 (-43%) | -0.014 | +0.002 |
| T3 vs T2 (access and point map together) | 100% | 0% | 0% (0%, 0%) | 0% | 25% |  | -36.8 (-43%) | +0.055 | +0.000 |
| T3 vs T0 (everything against nothing) | 100% | 0% | 0% (0%, 0%) | 0% | 67% |  | -40.1 (-45%) | +0.103 | +0.002 |

## Every cell: minutes / accuracy / wrong-and-confident (hardware / configuration-cause episodes)

| reliability / mix / coverage | T0 | T1 | T2 | T2+access | T3 |
|---|---|---|---|---|---|
| R0 / assumed / full | 88 / 72% / 0% | 91 / 71% / 0% | 85 / 77% / 0% | 85 / 84% / 0% | 48 / 82% / 0% |
| R0 / assumed / half | 89 / 74% / 0% | 92 / 73% / 0% | 91 / 73% / 1% | 86 / 84% / 0% | 70 / 79% / 1% |
| R0 / shifted / full | 86 / 68% / 1% | 87 / 73% / 0% | 82 / 75% / 0% | 84 / 79% / 2% | 51 / 79% / 1% |
| R0 / shifted / half | 85 / 69% / 0% | 89 / 71% / 1% | 86 / 72% / 1% | 90 / 80% / 1% | 73 / 78% / 1% |
| R1 / assumed / full | 89 / 50% / 4% | 95 / 45% / 5% | 91 / 44% / 6% | 91 / 54% / 8% | 53 / 54% / 7% |
| R1 / assumed / half | 87 / 56% / 3% | 96 / 46% / 1% | 90 / 50% / 5% | 95 / 55% / 5% | 76 / 56% / 9% |
| R1 / shifted / full | 89 / 47% / 3% | 92 / 44% / 4% | 86 / 48% / 4% | 90 / 52% / 7% | 54 / 48% / 8% |
| R1 / shifted / half | 87 / 49% / 2% | 90 / 46% / 3% | 86 / 50% / 4% | 94 / 52% / 7% | 75 / 48% / 6% |
| R2 / assumed / full | 87 / 34% / 5% | 94 / 27% / 7% | 91 / 31% / 12% | 91 / 29% / 15% | 54 / 35% / 14% |
| R2 / assumed / half | 92 / 29% / 8% | 95 / 29% / 11% | 94 / 27% / 11% | 95 / 32% / 16% | 76 / 35% / 15% |
| R2 / shifted / full | 87 / 30% / 6% | 92 / 26% / 11% | 88 / 28% / 10% | 89 / 31% / 14% | 52 / 28% / 17% |
| R2 / shifted / half | 85 / 30% / 6% | 90 / 27% / 8% | 89 / 26% / 9% | 95 / 29% / 14% | 78 / 28% / 18% |

## Episodes where the drawings are wrong (T1 and up; T0 has no drawings): minutes / accuracy / wrong-and-confident

| reliability / mix / coverage | n | T1 | T2 | T2+access | T3 |
|---|---|---|---|---|---|
| R0 / assumed / full | 62 | 97 / 82% / 0% | 100 / 81% / 0% | 100 / 82% / 3% | 83 / 74% / 0% |
| R0 / assumed / half | 54 | 98 / 80% / 2% | 93 / 87% / 0% | 100 / 70% / 0% | 85 / 74% / 2% |
| R0 / shifted / full | 27 | 98 / 81% / 0% | 96 / 85% / 0% | 97 / 74% / 4% | 78 / 67% / 4% |
| R0 / shifted / half | 18 | 107 / 83% / 0% | 102 / 72% / 0% | 108 / 72% / 0% | 88 / 72% / 0% |
| R1 / assumed / full | 72 | 110 / 57% / 4% | 105 / 65% / 0% | 103 / 44% / 18% | 74 / 33% / 6% |
| R1 / assumed / half | 80 | 111 / 50% / 4% | 98 / 46% / 15% | 107 / 45% / 11% | 87 / 39% / 9% |
| R1 / shifted / full | 37 | 97 / 51% / 14% | 106 / 38% / 8% | 102 / 38% / 11% | 71 / 49% / 11% |
| R1 / shifted / half | 26 | 114 / 58% / 8% | 113 / 38% / 12% | 104 / 54% / 12% | 86 / 50% / 15% |
| R2 / assumed / full | 74 | 102 / 18% / 20% | 98 / 35% / 23% | 93 / 23% / 23% | 61 / 12% / 31% |
| R2 / assumed / half | 67 | 99 / 39% / 15% | 104 / 21% / 7% | 100 / 25% / 21% | 83 / 18% / 19% |
| R2 / shifted / full | 16 | 90 / 25% / 12% | 103 / 44% / 6% | 118 / 12% / 0% | 62 / 12% / 12% |
| R2 / shifted / half | 24 | 104 / 25% / 8% | 101 / 38% / 8% | 97 / 17% / 25% | 83 / 25% / 25% |

## Predictions (written before the run; each strict)

| prediction | holds | values |
|---|---|---|
| P1 | holds | (48.26255707762557, 63.79109589041096) |
| P2 | holds | (48.26255707762557, 76.56164383561644) |
| P3 | holds | (0.07018419607647379, 0.057077625570776336) |
| P4 | holds | (91.47488584474885, 88.38356164383562) |
| P5 | holds | {'T0': (0.051643192488262914, 0.00228310502283105), 'T1': (0.07276995305164319, 0.0045662100456621), 'T2': (0.11502347417840375, 0.0045662100456621), 'T2+access': (0.15492957746478872, 0.00228310502283105), 'T3': (0.13615023474178403, 0.0045662100456621)} |
| P6 | holds | (0.13158402469612193, 0.06820374300598109) |
| P7 | holds | (15.811659192825118, 36.80593607305936) |
| P8 | does not hold | {'T0': (0.6849894291754757, 0.7214611872146118), 'T1': (0.733615221987315, 0.7123287671232876), 'T2': (0.7526427061310782, 0.769406392694064), 'T2+access': (0.7906976744186046, 0.8378995433789954), 'T3': (0.7906976744186046, 0.8242009132420092)} |
| P9 | holds | (0.8225806451612904, 0.5) |

## Reliability, in words

- R0: checks as reliable as assumed
- R1: checks worse (25% of the way to a coin flip)
- R2: checks much worse (50% of the way to a coin flip)

Run time 29 s.
