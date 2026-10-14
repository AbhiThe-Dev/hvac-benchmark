# Does the routine's check-value bar (min_rate) hold up across tiers and cells? (Addendum 35)

Addendum 30's 18 cells, 1000 events each, both tiers; the routine (`tool_ticket_memo2`) at its default check-value bar (`min_rate` = 0.003) against Addendum 34's lead (`min_rate` = 0.01); `tau` unchanged at 0.95 throughout; identical answers to identical questions (`TableOracle`). No LLM is run here. Simulation only, from the tool's own model family with placeholder numbers; nothing here is evidence about real technicians, buildings, or how often shared causes happen.

## Gates

| gate | result | detail |
|---|---|---|
| G1 regression | PASS | first 50 events of every cell match Addendum 30's stored kinds |
| G2 baseline reproduces Addendum 31 | PASS | T2: 109.0 min / 80% against Addendum 31's 112 / 80%; T3: 63.6 min / 83% against Addendum 31's 65 / 82% |
| G3 answer table | PASS | the answer table is deterministic and independent of question order |
| G4 reproduces Addendum 34 (P6) | PASS | primary cell T2: base 108.99 vs Addendum 34's 108.99; challenger 76.11 vs 76.11 |
| G5 reproducibility (first 3 cells re-run) | PASS | the sweep reproduces exactly on a second run with the same seed |

## Primary cell (shared assumed / M0 / R0), tier T2: minutes per visit / share diagnosed exactly right / wrong-and-confident / checks per visit

| min_rate | all events | shared-cause | several, no shared cause | one complaint |
|---|---|---|---|---|
| 0.003 (baseline) | 109 min / 80% / 1.3% / 11.0 | 81 min / 94% / 2.3% / 7.0 | 189 min / 76% / 0.9% / 19.7 | 82 min / 77% / 1.2% / 8.3 |
| 0.01 (challenger) | 76 min / 78% / 0.3% / 8.4 | 41 min / 92% / 1.0% / 4.3 | 138 min / 75% / 0.1% / 15.6 | 59 min / 76% / 0.2% / 6.5 |

## Primary cell (shared assumed / M0 / R0), tier T3: minutes per visit / share diagnosed exactly right / wrong-and-confident / checks per visit

| min_rate | all events | shared-cause | several, no shared cause | one complaint |
|---|---|---|---|---|
| 0.003 (baseline) | 64 min / 83% / 1.1% / 12.2 | 37 min / 96% / 3.0% / 7.1 | 114 min / 80% / 0.3% / 22.0 | 49 min / 81% / 0.9% / 9.4 |
| 0.01 (challenger) | 57 min / 83% / 0.8% / 11.5 | 30 min / 95% / 3.0% / 6.4 | 102 min / 79% / 0.3% / 20.6 | 45 min / 82% / 0.3% / 8.9 |

## Every cell, both tiers: challenger (min_rate=0.01) minus baseline (min_rate=0.003), `all` events

| cell | tier | d minutes | d accuracy | d wrong-and-confident | time / accuracy | label | safety |
|---|---|---|---|---|---|---|---|
| shared rare / M0 / R0 | T2 | -33.2 (-29%) | -0.012 | -0.005 | FASTER / SAME | IMPROVES | NONE |
| shared rare / M0 / R0 | T3 | -6.0 (-9%) | -0.002 | -0.001 | FASTER / SAME | IMPROVES | NONE |
| shared rare / M0 / R1 | T2 | -39.9 (-31%) | -0.010 | -0.027 | FASTER / SAME | IMPROVES | GAIN |
| shared rare / M0 / R1 | T3 | -8.2 (-11%) | -0.004 | -0.011 | FASTER / SAME | IMPROVES | NONE |
| shared rare / M1 / R0 | T2 | -32.6 (-28%) | -0.026 | -0.003 | FASTER / LESS | TRADE | NONE |
| shared rare / M1 / R0 | T3 | -6.5 (-9%) | -0.001 | -0.001 | FASTER / SAME | IMPROVES | NONE |
| shared rare / M1 / R1 | T2 | -37.2 (-31%) | -0.009 | -0.034 | FASTER / SAME | IMPROVES | GAIN |
| shared rare / M1 / R1 | T3 | -6.5 (-9%) | -0.003 | -0.011 | FASTER / SAME | IMPROVES | NONE |
| shared rare / M2 / R0 | T2 | -30.1 (-25%) | -0.018 | -0.008 | FASTER / SAME | IMPROVES | NONE |
| shared rare / M2 / R0 | T3 | -5.8 (-8%) | -0.003 | -0.000 | FASTER / SAME | IMPROVES | NONE |
| shared rare / M2 / R1 | T2 | -36.5 (-29%) | -0.014 | -0.029 | FASTER / SAME | IMPROVES | GAIN |
| shared rare / M2 / R1 | T3 | -7.2 (-10%) | -0.000 | -0.013 | FASTER / SAME | IMPROVES | NONE |
| shared assumed / M0 / R0 | T2 | -32.9 (-30%) | -0.016 | -0.010 | FASTER / SAME | IMPROVES | NONE |
| shared assumed / M0 / R0 | T3 | -6.8 (-11%) | +0.000 | -0.003 | FASTER / SAME | IMPROVES | NONE |
| shared assumed / M0 / R1 | T2 | -37.5 (-32%) | -0.021 | -0.026 | FASTER / LESS | TRADE | GAIN |
| shared assumed / M0 / R1 | T3 | -8.9 (-13%) | -0.005 | -0.005 | FASTER / SAME | IMPROVES | NONE |
| shared assumed / M1 / R0 | T2 | -36.2 (-30%) | -0.024 | -0.008 | FASTER / LESS | TRADE | NONE |
| shared assumed / M1 / R0 | T3 | -7.4 (-11%) | -0.003 | -0.002 | FASTER / SAME | IMPROVES | NONE |
| shared assumed / M1 / R1 | T2 | -44.5 (-34%) | -0.009 | -0.022 | FASTER / SAME | IMPROVES | GAIN |
| shared assumed / M1 / R1 | T3 | -8.7 (-12%) | +0.000 | -0.010 | FASTER / SAME | IMPROVES | NONE |
| shared assumed / M2 / R0 | T2 | -33.2 (-27%) | -0.024 | -0.009 | FASTER / LESS | TRADE | NONE |
| shared assumed / M2 / R0 | T3 | -7.2 (-10%) | -0.000 | -0.002 | FASTER / SAME | IMPROVES | NONE |
| shared assumed / M2 / R1 | T2 | -39.3 (-31%) | -0.009 | -0.028 | FASTER / SAME | IMPROVES | GAIN |
| shared assumed / M2 / R1 | T3 | -6.7 (-9%) | -0.003 | -0.007 | FASTER / SAME | IMPROVES | NONE |
| shared common / M0 / R0 | T2 | -37.2 (-34%) | -0.011 | -0.015 | FASTER / SAME | IMPROVES | NONE |
| shared common / M0 / R0 | T3 | -7.2 (-12%) | -0.005 | +0.000 | FASTER / SAME | IMPROVES | NONE |
| shared common / M0 / R1 | T2 | -45.0 (-39%) | -0.011 | -0.030 | FASTER / SAME | IMPROVES | GAIN |
| shared common / M0 / R1 | T3 | -9.2 (-14%) | -0.004 | -0.007 | FASTER / SAME | IMPROVES | NONE |
| shared common / M1 / R0 | T2 | -49.1 (-37%) | -0.027 | -0.012 | FASTER / LESS | TRADE | NONE |
| shared common / M1 / R0 | T3 | -10.2 (-14%) | -0.001 | -0.001 | FASTER / SAME | IMPROVES | NONE |
| shared common / M1 / R1 | T2 | -51.2 (-38%) | +0.001 | -0.034 | FASTER / SAME | IMPROVES | GAIN |
| shared common / M1 / R1 | T3 | -10.9 (-14%) | -0.004 | -0.012 | FASTER / SAME | IMPROVES | NONE |
| shared common / M2 / R0 | T2 | -45.3 (-34%) | -0.029 | -0.013 | FASTER / LESS | TRADE | NONE |
| shared common / M2 / R0 | T3 | -8.3 (-11%) | -0.002 | -0.002 | FASTER / SAME | IMPROVES | NONE |
| shared common / M2 / R1 | T2 | -51.0 (-37%) | -0.019 | -0.029 | FASTER / SAME | IMPROVES | GAIN |
| shared common / M2 / R1 | T3 | -11.9 (-15%) | -0.007 | -0.008 | FASTER / SAME | IMPROVES | NONE |

## Shares of the 18 cells (challenger vs baseline, `all` events)

| tier | IMPROVES | WORSE | TRADE | NEITHER | SAFETY REGRESSION | SAFETY GAIN |
|---|---|---|---|---|---|---|
| T2 | 67% | 0% | 33% | 0% | 0% | 50% |
| T3 | 100% | 0% | 0% | 0% | 0% | 0% |

## Predictions (written before the run; each strict)

| prediction | holds | values |
|---|---|---|
| P1 | does not hold | T2: IMPROVES in 12 of 18 cells |
| P2 | holds | T3: IMPROVES in 18 of 18 cells |
| P3 | holds | WORSE in 0 of 18 cells at T2, 0 at T3 |
| P4 | holds | safety regressions: 0 of 18 at T2, 0 at T3 |
| P5 | holds | safety regressions: 0 of 12 (M0 x 2 tiers), 0 of 24 (M1/M2 x 2 tiers) |
| P6 | holds | primary cell T2: base 108.99 vs Addendum 34's 108.99; challenger 76.11 vs 76.11 |

## Frozen decision: NOT CONFIRMED

Run time 19 s.
