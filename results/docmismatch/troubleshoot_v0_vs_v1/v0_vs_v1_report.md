# The v1 tool against the tool as it was before (v0), on the same complaints (Addendum 29)

Addendum 27's episodes and simulated answers, 12 cells x 500 episodes. `v0` is the v0-equivalent tree of v1 (the old tool: two lumps and the four v0 checks, tau 0.95, 12 checks, no bits-per-minute stop) with the data of T1; `v1` is Addendum 27's tool at T1, T2, T2+access and T3. v0 can answer only in its four lumps, so accuracy is at v0's level (the leading cause at the end, whether or not concluded); v1's exact-cause accuracy is shown for context. Everything is simulated from the tool's own model family with placeholder numbers; nothing here is evidence about real technicians.

## Gates

| gate | result | detail |
|---|---|---|
| G1 code path | PASS | v0 policy = v0's simulate on 12 episodes; the v1 arms equal Addendum 27's raw file in all 12 cells |
| G2 accounting | PASS | hand-summed minutes agree; 80 degraded-reliability v0 episodes replay identically from their answers alone |
| G3 reproducibility | PASS | first 50 episodes of cell 0 reproduce |
| G4 completeness | PASS | ok |

## Primary cell (R0 / assumed / full), hardware / configuration-cause episodes (n = 438), accuracy at v0's level

| policy | minutes | checks | entries typed | reach 0.95 | accuracy (v0 level) | wrong-and-confident | v1 exact accuracy |
|---|---|---|---|---|---|---|---|
| v0 (before) | 49 | 4.3 | 5.3 | 82% | 80% | 3% | n/a |
| v1 at T1 | 91 | 8.6 | 12.5 | 21% | 97% | 0% | 71% |
| v1 at T2 | 85 | 8.6 | 11.9 | 23% | 97% | 0% | 77% |
| v1 at T2+access | 85 | 9.1 | 11.2 | 43% | 97% | 0% | 84% |
| v1 at T3 | 48 | 9.2 | 10.8 | 49% | 97% | 0% | 82% |
| constant guess 'the box acts, cause elsewhere' | | | | | 82% | | |

## Primary cell (R0 / assumed / full), episodes where the drawings are wrong (n = 62), accuracy at v0's level

| policy | minutes | checks | entries typed | reach 0.95 | accuracy (v0 level) | wrong-and-confident | v1 exact accuracy |
|---|---|---|---|---|---|---|---|
| v0 (before) | 82 | 7.2 | 8.2 | 84% | 81% | 13% | n/a |
| v1 at T1 | 97 | 9.0 | 11.3 | 71% | 82% | 0% | 82% |
| v1 at T2 | 100 | 9.4 | 11.8 | 71% | 81% | 0% | 81% |
| v1 at T2+access | 100 | 9.4 | 11.4 | 76% | 82% | 3% | 82% |
| v1 at T3 | 83 | 11.1 | 12.2 | 50% | 74% | 0% | 74% |
| constant guess 'the box acts, cause elsewhere' | | | | | 0% | | |

## v1 minus v0 over the 12 cells (same episodes, v0's level)

Labels are Addendum 21's (IMPROVES / WORSE / TRADE / NEITHER at 5% minutes and 0.02 accuracy, paired 95% intervals); TRADE in brackets: v1 faster but less accurate (F/L) or slower but more accurate (S/M); SAFETY REG = share of cells where v1's wrong-and-confident rate is at least 0.02 higher (GAIN: lower). Last column: break-even cost of a wrong diagnosis on the primary cell.

| v1 arm | subset | IMPROVES | WORSE | TRADE (F/L, S/M) | NEITHER | SAFETY REG / GAIN | primary: d minutes | d checks | d accuracy | d wrong-and-confident | break-even |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 | hardware | 0% | 17% | 83% (0%, 83%) | 0% | 0% / 100% | +42 (+86%) | +4.4 | +0.176 | -0.025 | 240 min (v1 wins above) |
| T2 | hardware | 0% | 0% | 100% (0%, 100%) | 0% | 0% / 92% | +36 (+73%) | +4.4 | +0.167 | -0.025 | 215 min (v1 wins above) |
| T2+access | hardware | 0% | 0% | 100% (0%, 100%) | 0% | 0% / 100% | +36 (+73%) | +4.9 | +0.169 | -0.025 | 212 min (v1 wins above) |
| T3 | hardware | 50% | 0% | 50% (0%, 50%) | 0% | 0% / 100% | -1 (-2%) | +4.9 | +0.171 | -0.025 | v1 ahead on both |
| T1 | drawings wrong | 0% | 58% | 0% (0%, 0%) | 42% | 0% / 75% | +15 (+19%) | +1.8 | +0.016 | -0.129 | 952 min (v1 wins above) |
| T2 | drawings wrong | 8% | 58% | 0% (0%, 0%) | 33% | 0% / 58% | +18 (+22%) | +2.2 | +0.000 | -0.129 | v0 ahead on both |
| T2+access | drawings wrong | 0% | 58% | 0% (0%, 0%) | 42% | 0% / 33% | +18 (+22%) | +2.2 | +0.016 | -0.097 | 1108 min (v1 wins above) |
| T3 | drawings wrong | 25% | 17% | 8% (8%, 0%) | 50% | 0% / 58% | +1 (+2%) | +3.9 | -0.065 | -0.129 | v0 ahead on both |

## Every cell, hardware episodes: minutes / checks / accuracy at v0's level, v0 | v1 at T1 | v1 at T3

| reliability / mix / coverage | v0 | v1 at T1 | v1 at T3 |
|---|---|---|---|
| R0 / assumed / full | 49 / 4.3 / 80% | 91 / 8.6 / 97% | 48 / 9.2 / 97% |
| R0 / assumed / half | 51 / 4.3 / 80% | 92 / 8.7 / 97% | 70 / 9.3 / 98% |
| R0 / shifted / full | 60 / 5.0 / 75% | 87 / 8.5 / 97% | 51 / 9.7 / 96% |
| R0 / shifted / half | 60 / 5.0 / 74% | 89 / 8.7 / 96% | 73 / 9.5 / 96% |
| R1 / assumed / full | 55 / 4.6 / 74% | 95 / 9.0 / 85% | 53 / 10.1 / 88% |
| R1 / assumed / half | 57 / 4.8 / 75% | 96 / 9.2 / 85% | 76 / 9.6 / 89% |
| R1 / shifted / full | 61 / 5.0 / 71% | 92 / 9.0 / 82% | 54 / 10.2 / 84% |
| R1 / shifted / half | 60 / 5.0 / 71% | 90 / 8.9 / 84% | 75 / 10.1 / 84% |
| R2 / assumed / full | 58 / 4.8 / 59% | 94 / 9.0 / 72% | 54 / 10.2 / 78% |
| R2 / assumed / half | 57 / 4.7 / 65% | 95 / 9.0 / 71% | 76 / 9.9 / 73% |
| R2 / shifted / full | 62 / 5.1 / 62% | 92 / 8.9 / 67% | 52 / 9.9 / 76% |
| R2 / shifted / half | 65 / 5.4 / 55% | 90 / 8.8 / 71% | 78 / 9.9 / 69% |

## Predictions (written before the run; each strict)

| prediction | holds | values |
|---|---|---|
| P1 | does not hold | {'T1': (91.47488584474885, 49.23744292237443), 'T2': (85.05479452054794, 49.23744292237443), 'T2+access': (85.06849315068493, 49.23744292237443), 'T3': (48.26255707762557, 49.23744292237443)} |
| P2 | holds | (8.616438356164384, 4.262557077625571) |
| P3 | holds | (0.9748858447488584, 0.7990867579908676) |
| P4 | holds | (0.02511415525114155, 0.0) |
| P5 | holds | (0.8225806451612904, 0.8064516129032258) |
| P6 | holds | (12, 12) |
| P7 | holds | (0.12910798122065725, 0.17579908675799083) |

Run time 28 s.
