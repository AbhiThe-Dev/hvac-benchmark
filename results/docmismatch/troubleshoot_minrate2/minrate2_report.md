# Does the live default (min_rate = 0.015) hold up across tiers and cells? (Addendum 36)

Addendum 30's 18 cells, 1000 events each, both tiers; the routine (`tool_ticket_memo2`) at its default check-value bar (`min_rate` = 0.003) against the live tool's current default (`min_rate` = 0.015, chosen by the user beyond Addendum 35's confirmed 0.01); `tau` unchanged at 0.95; identical answers to identical questions (`TableOracle`). No LLM is run here. Simulation only, from the tool's own model family with placeholder numbers.

## Gates

| gate | result | detail |
|---|---|---|
| G1 regression | PASS | first 50 events of every cell match Addendum 30's stored kinds |
| G2 baseline reproduces Addendum 31 | PASS | T2: 109.0 min / 80% against Addendum 31's 112 / 80%; T3: 63.6 min / 83% against Addendum 31's 65 / 82% |
| G3 answer table | PASS | the answer table is deterministic and independent of question order |
| G4 reproduces the 0.015 reference (P6) | PASS | primary cell: T2 67.88 min / 0.770 against the reference 67.9 / 0.770; T3 52.13 / 0.827 against 52.1 / 0.827 |
| G5 reproducibility (first 3 cells re-run) | PASS | the sweep reproduces exactly on a second run with the same seed |

## Primary cell (shared assumed / M0 / R0), tier T2: minutes per visit / share diagnosed exactly right / wrong-and-confident / checks per visit

| min_rate | all events | shared-cause | several, no shared cause | one complaint |
|---|---|---|---|---|
| 0.003 (baseline) | 109 min / 80% / 1.3% / 11.0 | 81 min / 94% / 2.3% / 7.0 | 189 min / 76% / 0.9% / 19.7 | 82 min / 77% / 1.2% / 8.3 |
| 0.015 (live default) | 68 min / 77% / 0.2% / 7.7 | 38 min / 92% / 1.0% / 3.9 | 121 min / 73% / 0.1% / 14.0 | 53 min / 74% / 0.0% / 5.9 |

## Primary cell (shared assumed / M0 / R0), tier T3: minutes per visit / share diagnosed exactly right / wrong-and-confident / checks per visit

| min_rate | all events | shared-cause | several, no shared cause | one complaint |
|---|---|---|---|---|
| 0.003 (baseline) | 64 min / 83% / 1.1% / 12.2 | 37 min / 96% / 3.0% / 7.1 | 114 min / 80% / 0.3% / 22.0 | 49 min / 81% / 0.9% / 9.4 |
| 0.015 (live default) | 52 min / 83% / 0.8% / 10.8 | 27 min / 95% / 3.0% / 5.8 | 93 min / 78% / 0.3% / 19.5 | 41 min / 81% / 0.3% / 8.5 |

## Every cell, both tiers: challenger (min_rate=0.015) minus baseline (min_rate=0.003), `all` events

| cell | tier | d minutes | d accuracy | d wrong-and-confident | time / accuracy | label | safety |
|---|---|---|---|---|---|---|---|
| shared rare / M0 / R0 | T2 | -41.9 (-36%) | -0.021 | -0.007 | FASTER / LESS | TRADE | NONE |
| shared rare / M0 / R0 | T3 | -11.0 (-16%) | -0.003 | -0.002 | FASTER / SAME | IMPROVES | NONE |
| shared rare / M0 / R1 | T2 | -52.2 (-41%) | -0.030 | -0.031 | FASTER / LESS | TRADE | GAIN |
| shared rare / M0 / R1 | T3 | -14.9 (-20%) | -0.011 | -0.020 | FASTER / SAME | IMPROVES | NONE |
| shared rare / M1 / R0 | T2 | -41.9 (-36%) | -0.037 | -0.005 | FASTER / LESS | TRADE | NONE |
| shared rare / M1 / R0 | T3 | -12.2 (-18%) | -0.008 | -0.002 | FASTER / SAME | IMPROVES | NONE |
| shared rare / M1 / R1 | T2 | -48.4 (-40%) | -0.019 | -0.039 | FASTER / SAME | IMPROVES | GAIN |
| shared rare / M1 / R1 | T3 | -12.8 (-18%) | -0.017 | -0.026 | FASTER / SAME | IMPROVES | GAIN |
| shared rare / M2 / R0 | T2 | -39.4 (-33%) | -0.037 | -0.008 | FASTER / LESS | TRADE | NONE |
| shared rare / M2 / R0 | T3 | -11.2 (-15%) | -0.011 | -0.001 | FASTER / SAME | IMPROVES | NONE |
| shared rare / M2 / R1 | T2 | -46.6 (-38%) | -0.034 | -0.033 | FASTER / LESS | TRADE | GAIN |
| shared rare / M2 / R1 | T3 | -14.1 (-19%) | -0.011 | -0.030 | FASTER / SAME | IMPROVES | GAIN |
| shared assumed / M0 / R0 | T2 | -41.1 (-38%) | -0.029 | -0.011 | FASTER / LESS | TRADE | NONE |
| shared assumed / M0 / R0 | T3 | -11.4 (-18%) | -0.005 | -0.003 | FASTER / SAME | IMPROVES | NONE |
| shared assumed / M0 / R1 | T2 | -48.0 (-41%) | -0.025 | -0.030 | FASTER / LESS | TRADE | GAIN |
| shared assumed / M0 / R1 | T3 | -14.5 (-21%) | -0.017 | -0.019 | FASTER / SAME | IMPROVES | NONE |
| shared assumed / M1 / R0 | T2 | -45.7 (-38%) | -0.033 | -0.009 | FASTER / LESS | TRADE | NONE |
| shared assumed / M1 / R0 | T3 | -12.3 (-18%) | -0.007 | -0.003 | FASTER / SAME | IMPROVES | NONE |
| shared assumed / M1 / R1 | T2 | -55.7 (-42%) | -0.025 | -0.028 | FASTER / LESS | TRADE | GAIN |
| shared assumed / M1 / R1 | T3 | -15.5 (-21%) | -0.005 | -0.017 | FASTER / SAME | IMPROVES | NONE |
| shared assumed / M2 / R0 | T2 | -42.5 (-34%) | -0.032 | -0.009 | FASTER / LESS | TRADE | NONE |
| shared assumed / M2 / R0 | T3 | -11.9 (-16%) | -0.006 | -0.002 | FASTER / SAME | IMPROVES | NONE |
| shared assumed / M2 / R1 | T2 | -50.4 (-39%) | -0.015 | -0.034 | FASTER / SAME | IMPROVES | GAIN |
| shared assumed / M2 / R1 | T3 | -13.7 (-19%) | -0.006 | -0.021 | FASTER / SAME | IMPROVES | GAIN |
| shared common / M0 / R0 | T2 | -44.3 (-41%) | -0.016 | -0.016 | FASTER / SAME | IMPROVES | NONE |
| shared common / M0 / R0 | T3 | -11.5 (-19%) | -0.011 | -0.001 | FASTER / SAME | IMPROVES | NONE |
| shared common / M0 / R1 | T2 | -54.0 (-47%) | -0.019 | -0.032 | FASTER / SAME | IMPROVES | GAIN |
| shared common / M0 / R1 | T3 | -14.6 (-23%) | -0.014 | -0.022 | FASTER / SAME | IMPROVES | GAIN |
| shared common / M1 / R0 | T2 | -58.3 (-44%) | -0.037 | -0.012 | FASTER / LESS | TRADE | NONE |
| shared common / M1 / R0 | T3 | -16.0 (-22%) | -0.005 | -0.002 | FASTER / SAME | IMPROVES | NONE |
| shared common / M1 / R1 | T2 | -61.6 (-46%) | -0.012 | -0.039 | FASTER / SAME | IMPROVES | GAIN |
| shared common / M1 / R1 | T3 | -18.1 (-24%) | -0.012 | -0.023 | FASTER / SAME | IMPROVES | GAIN |
| shared common / M2 / R0 | T2 | -54.0 (-40%) | -0.037 | -0.013 | FASTER / LESS | TRADE | NONE |
| shared common / M2 / R0 | T3 | -12.2 (-17%) | -0.004 | -0.004 | FASTER / SAME | IMPROVES | NONE |
| shared common / M2 / R1 | T2 | -61.1 (-45%) | -0.026 | -0.033 | FASTER / LESS | TRADE | GAIN |
| shared common / M2 / R1 | T3 | -17.6 (-23%) | -0.015 | -0.018 | FASTER / SAME | IMPROVES | NONE |

## Shares of the 18 cells (challenger vs baseline, `all` events)

| tier | IMPROVES | WORSE | TRADE | NEITHER | SAFETY REGRESSION | SAFETY GAIN |
|---|---|---|---|---|---|---|
| T2 | 28% | 0% | 72% | 0% | 0% | 50% |
| T3 | 100% | 0% | 0% | 0% | 0% | 28% |

## Predictions (written before the run; each strict)

| prediction | holds | values |
|---|---|---|
| P1 | does not hold | T2: IMPROVES in 5 of 18 cells |
| P2 | holds | T3: IMPROVES in 18 of 18 cells |
| P3 | holds | WORSE in 0 of 18 cells at T2, 0 at T3 |
| P4 | holds | safety regressions: 0 of 18 at T2, 0 at T3 |
| P5 | holds | safety regressions: 0 of 12 (M0 x 2 tiers), 0 of 24 (M1/M2 x 2 tiers) |
| P6 | holds | primary cell: T2 67.88 min / 0.770 against the reference 67.9 / 0.770; T3 52.13 / 0.827 against 52.1 / 0.827 |

## Frozen decision: NOT CONFIRMED

Run time 97 s.
