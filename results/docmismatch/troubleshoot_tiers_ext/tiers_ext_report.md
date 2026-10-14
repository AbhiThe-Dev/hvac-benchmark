# What BAS access + a point map buy without documented attributes (Exploratory note E2)

Same synthetic building, draws and seed as Addendum 27. Adds one arm, **T3-noattr** = T1's items (equipment list, drawings' claims) plus `bas_access` and `point_map`, but **no** `attributes` (no reheat type, K-factor, design airflow, inlet size, static setpoint on file). Motivation: the named tiers are cumulative (T3 = T2 + access + map, so T3 always has attributes too), but a reported real-world documentation profile has T1 and T3 commonly available and T2 rarely so -- a combination no existing tier covers. Simulation only; every minute and probability a placeholder; nothing here is evidence about real buildings or technicians.

## Non-perturbation check

PASS: 30 episodes of T1, T2, T2+access and T3 reproduce study_tiers.run_cell exactly

## The primary cell (R0 / assumed / full): hardware / configuration-cause episodes (n = 438)

| arm | minutes | accuracy | right branch | wrong-and-confident | checks | questions asked |
|---|---|---|---|---|---|---|
| T1 | 91 | 71% | 72% | 0% | 8.6 | 2.9 |
| T2 | 85 | 77% | 79% | 0% | 8.6 | 2.3 |
| T2+access | 85 | 84% | 85% | 0% | 9.1 | 1.1 |
| T3-noattr | 55 | 79% | 81% | 1% | 9.3 | 1.2 |
| T3 | 48 | 82% | 84% | 0% | 9.2 | 0.6 |

## The comparisons this note is about, over the 12 cells

Labels are Addendum 21's frozen ones (IMPROVES / WORSE / TRADE / NEITHER at 5% minutes and 0.02 accuracy, paired 95% intervals); TRADE's bracket shows faster-but-less-accurate (F/L) or slower-but-more-accurate (S/M). SAFETY REG is the share of cells where wrong-and-confident is at least 0.02 higher with the interval clear of 0.

| comparison | IMPROVES | WORSE | TRADE (F/L, S/M) | NEITHER | SAFETY REG | primary cell: d minutes | d accuracy | d wrong-and-confident |
|---|---|---|---|---|---|---|---|---|
| T3-noattr vs T1 (what BAS access + a point map buy, with no attributes at all) | 100% | 0% | 0% (0%, 0%) | 0% | 33% | -36.0 (-39%) | +0.080 | +0.005 |
| T3-noattr vs T2 (access + map without attributes, vs. attributes alone) | 100% | 0% | 0% (0%, 0%) | 0% | 25% | -29.6 (-35%) | +0.023 | +0.005 |
| T3-noattr vs T2+access (adding the point map, when attributes were never there to begin with) | 92% | 0% | 8% (8%, 0%) | 0% | 0% | -29.6 (-35%) | -0.046 | +0.007 |
| T3 vs T3-noattr (what having attributes too, on top of access + map, still buys) | 58% | 0% | 0% (0%, 0%) | 42% | 0% | -7.2 (-13%) | +0.032 | -0.005 |

## Every cell: minutes / accuracy / wrong-and-confident (hardware / configuration-cause episodes)

| reliability / mix / coverage | T1 | T2 | T2+access | T3-noattr | T3 |
|---|---|---|---|---|---|
| R0 / assumed / full | 91 / 71% / 0% | 85 / 77% / 0% | 85 / 84% / 0% | 55 / 79% / 1% | 48 / 82% / 0% |
| R0 / assumed / half | 92 / 73% / 0% | 91 / 73% / 1% | 86 / 84% / 0% | 72 / 81% / 0% | 70 / 79% / 1% |
| R0 / shifted / full | 87 / 73% / 0% | 82 / 75% / 0% | 84 / 79% / 2% | 57 / 81% / 1% | 51 / 79% / 1% |
| R0 / shifted / half | 89 / 71% / 1% | 86 / 72% / 1% | 90 / 80% / 1% | 77 / 79% / 0% | 73 / 78% / 1% |
| R1 / assumed / full | 95 / 45% / 5% | 91 / 44% / 6% | 91 / 54% / 8% | 59 / 50% / 8% | 53 / 54% / 7% |
| R1 / assumed / half | 96 / 46% / 1% | 90 / 50% / 5% | 95 / 55% / 5% | 77 / 56% / 7% | 76 / 56% / 9% |
| R1 / shifted / full | 92 / 44% / 4% | 86 / 48% / 4% | 90 / 52% / 7% | 60 / 44% / 7% | 54 / 48% / 8% |
| R1 / shifted / half | 90 / 46% / 3% | 86 / 50% / 4% | 94 / 52% / 7% | 75 / 51% / 6% | 75 / 48% / 6% |
| R2 / assumed / full | 94 / 27% / 7% | 91 / 31% / 12% | 91 / 29% / 15% | 56 / 30% / 18% | 54 / 35% / 14% |
| R2 / assumed / half | 95 / 29% / 11% | 94 / 27% / 11% | 95 / 32% / 16% | 80 / 35% / 14% | 76 / 35% / 15% |
| R2 / shifted / full | 92 / 26% / 11% | 88 / 28% / 10% | 89 / 31% / 14% | 60 / 31% / 16% | 52 / 28% / 17% |
| R2 / shifted / half | 90 / 27% / 8% | 89 / 26% / 9% | 95 / 29% / 14% | 78 / 26% / 16% | 78 / 28% / 18% |

Run time 110 s.
