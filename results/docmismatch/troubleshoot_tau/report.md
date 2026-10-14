# NO RESULT: a gate failed (see Gates below); nothing here is a finding.

# Does lowering `tau` cut checks without costing accuracy or safety? (Addendum 41)

Simulation only: Addendum 30's 18 cells (1000 events each), answers from `TableOracle`, `min_rate` = 0.02 throughout, baseline `tau` = 0.95. Labels are Addendum 21's (5% minutes, 0.02 accuracy, 0.02 safety, paired 95% intervals) over the `all` subset; bars are Addendum 35's. Nothing here is evidence about real technicians and nothing changes the tool's defaults.

## Gates

- **G1: PASS.** first 50 events of every cell match Addendum 30's stored kinds
- **G2: PASS.** (a) tool_joint at T3, primary cell, first 200 events: identical to Addendum 30's stored per-event results; (b) routine at 0.95/0.003, T3, primary cell: 63.6 min / 83% against Addendum 31's 65 / 82%
- **G3: FAIL.** routine, 0.95/0.02, T3-noattr, primary cell: 56.6 min / 81.0% against E2's 58.3 / 80.4%; identical to study_minrate's own run: True
- **G4: PASS.** the answer table is deterministic and independent of question order
- **G5: PASS.** the real-call rows reproduce the probe table registered in Addendum 41
- **G6: PASS.** 3 cells reproduce exactly on a second run (one worker against many) with the same seed

## Overall outcome (tool_joint, T3-noattr): **NO LEVEL BELOW 0.95 PASSES**

### tool_joint, T3-noattr

| tau | label | IMPROVES | NEITHER | TRADE | WORSE | safety regressions | R1: IMPROVES / WORSE / safety (of 9) | cell-mean minutes | checks | accuracy | wrong-and-confident |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.95 (baseline) | - | - | - | - | - | - | - | 62.7 | 11.25 | 68% | 0.0220 |
| 0.9 | **UNSAFE** | 0 | 18 | 0 | 0 | 9 | 0 / 0 / 9 | 61.8 (-2%) | 11.03 | 68% (-0.1 pts) | 0.0541 |
| 0.85 | **UNSAFE** | 17 | 0 | 1 | 0 | 18 | 8 / 0 / 9 | 55.3 (-12%) | 10.22 | 67% (-1.4 pts) | 0.1322 |
| 0.8 | **UNSAFE** | 8 | 0 | 10 | 0 | 18 | 2 / 0 / 9 | 53.0 (-15%) | 9.82 | 66% (-2.1 pts) | 0.1759 |
| 0.75 | **UNSAFE** | 0 | 0 | 18 | 0 | 18 | 0 / 0 / 9 | 49.2 (-22%) | 9.11 | 65% (-3.7 pts) | 0.2173 |

### tool_ticket_memo2, T3-noattr

| tau | label | IMPROVES | NEITHER | TRADE | WORSE | safety regressions | R1: IMPROVES / WORSE / safety (of 9) | cell-mean minutes | checks | accuracy | wrong-and-confident |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.95 (baseline) | - | - | - | - | - | - | - | 60.4 | 10.93 | 68% | 0.0277 |
| 0.9 | **UNSAFE** | 0 | 18 | 0 | 0 | 9 | 0 / 0 / 9 | 60.3 (-0%) | 10.89 | 68% (+0.0 pts) | 0.0550 |
| 0.85 | **UNSAFE** | 17 | 0 | 1 | 0 | 18 | 8 / 0 / 9 | 54.5 (-10%) | 10.19 | 66% (-1.2 pts) | 0.1303 |
| 0.8 | **UNSAFE** | 9 | 0 | 9 | 0 | 18 | 3 / 0 / 9 | 51.8 (-14%) | 9.79 | 66% (-1.9 pts) | 0.1759 |
| 0.75 | **UNSAFE** | 1 | 0 | 17 | 0 | 18 | 0 / 0 / 9 | 48.2 (-20%) | 9.13 | 64% (-3.4 pts) | 0.2181 |

### tool_joint, T3

| tau | label | IMPROVES | NEITHER | TRADE | WORSE | safety regressions | R1: IMPROVES / WORSE / safety (of 9) | cell-mean minutes | checks | accuracy | wrong-and-confident |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.95 (baseline) | - | - | - | - | - | - | - | 58.9 | 11.93 | 69% | 0.0252 |
| 0.9 | **UNSAFE** | 1 | 17 | 0 | 0 | 10 | 1 / 0 / 9 | 58.0 (-2%) | 11.71 | 69% (-0.1 pts) | 0.0714 |
| 0.85 | **UNSAFE** | 15 | 0 | 3 | 0 | 18 | 7 / 0 / 9 | 51.3 (-13%) | 10.80 | 68% (-1.6 pts) | 0.1536 |
| 0.8 | **UNSAFE** | 8 | 0 | 10 | 0 | 18 | 3 / 0 / 9 | 49.6 (-16%) | 10.43 | 67% (-2.2 pts) | 0.1855 |
| 0.75 | **UNSAFE** | 0 | 0 | 18 | 0 | 18 | 0 / 0 / 9 | 46.0 (-22%) | 9.72 | 66% (-3.8 pts) | 0.2240 |

### tool_ticket_memo2, T3

| tau | label | IMPROVES | NEITHER | TRADE | WORSE | safety regressions | R1: IMPROVES / WORSE / safety (of 9) | cell-mean minutes | checks | accuracy | wrong-and-confident |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.95 (baseline) | - | - | - | - | - | - | - | 54.7 | 11.39 | 68% | 0.0300 |
| 0.9 | **UNSAFE** | 0 | 18 | 0 | 0 | 9 | 0 / 0 / 9 | 54.6 (-0%) | 11.35 | 68% (+0.0 pts) | 0.0716 |
| 0.85 | **UNSAFE** | 16 | 0 | 2 | 0 | 18 | 8 / 0 / 9 | 48.2 (-12%) | 10.51 | 67% (-1.4 pts) | 0.1496 |
| 0.8 | **UNSAFE** | 9 | 0 | 9 | 0 | 18 | 3 / 0 / 9 | 46.5 (-15%) | 10.18 | 66% (-2.0 pts) | 0.1838 |
| 0.75 | **UNSAFE** | 1 | 0 | 17 | 0 | 18 | 0 / 0 / 9 | 43.0 (-21%) | 9.51 | 65% (-3.6 pts) | 0.2225 |

## Registered predictions

| | held | detail |
|---|---|---|
| P1 | yes | tau 0.90: NEITHER in 18 of 18 cells |
| P2 | yes | tau 0.80: at least 5% faster in 18 of 18 cells |
| P3 | yes | tau 0.80 is UNSAFE |
| P4 | yes | tau 0.80 is UNSAFE, 0.75 is UNSAFE |
| P5 | yes | cell-mean wrong-and-confident 0.0220 at 0.95, 0.2173 at 0.75 (difference +0.1953) |
| P6 | NO | tau 0.80 safety regressions: 9 of 9 R1 cells, 9 of 9 R0 cells |
| P7 | yes | tau 0.80: cold_morning ratio 0.72, right 100%, ep160 ratio 0.88, right 99% |
| P8 | yes | routine, tau 0.80, T3-noattr: minutes lower in 18 of 18 cells |

## The two real calls (descriptive; the live CLI path, k = 6, the consistent worlds of Addendum 40; time at the CENTRAL pace)

| call | tau | steps | working time (min) | / technician | right on every complaint | wrong and confident | concluded |
|---|---|---|---|---|---|---|---|
| cold_morning | 0.95 | 6 | 4.95 | 1.10 | 99% | 0.0% | 89% |
| cold_morning | 0.9 | 6 | 4.95 | 1.10 | 99% | 0.0% | 92% |
| cold_morning | 0.85 | 5 | 3.98 | 0.88 | 100% | 0.0% | 100% |
| cold_morning | 0.8 | 4 | 3.23 | 0.72 | 100% | 0.2% | 100% |
| cold_morning | 0.75 | 3 | 2.25 | 0.50 | 100% | 0.2% | 100% |
| ep160 | 0.95 | 7 | 5.25 | 1.24 | 99% | 0.5% | 1% |
| ep160 | 0.9 | 7 | 5.25 | 1.24 | 99% | 0.5% | 1% |
| ep160 | 0.85 | 7 | 5.25 | 1.24 | 99% | 0.7% | 100% |
| ep160 | 0.8 | 5 | 3.75 | 0.88 | 99% | 0.7% | 100% |
| ep160 | 0.75 | 5 | 3.75 | 0.88 | 99% | 0.7% | 100% |
