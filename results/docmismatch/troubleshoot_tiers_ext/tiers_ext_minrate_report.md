# Does the `min_rate` lever help the T3-noattr documentation profile beat the language model? (Exploratory note E2, extended further)

Asked directly by the user: does raising `min_rate` (already confirmed, Addenda 34-36, for the fully-documented tiers) also help T3-noattr, trading a small accuracy cost for a large speed gain? No new engine code: reuses `study_minrate.py`'s own sweep machinery, pointed at the T3-noattr item set. Simulation only; every number a placeholder; the language model's own numbers are Addendum 33's stored ones, unchanged (no new LLM call).

## Primary cell sweep (1000 events; `min_rate` = 0.003 is the pre-tuning baseline, i.e. what Exploratory note E2's extension originally reported)

| min_rate | minutes | accuracy | wrong-and-confident | checks | single min | multi min | shared min |
|---|---|---|---|---|---|---|---|
| 0.003 | 78.1 | 82.3% | 1.50% | 12.5 | 59.1 | 130.2 | 53.2 |
| 0.01 | 67.1 | 82.2% | 0.97% | 11.6 | 51.4 | 114.3 | 38.8 |
| 0.015 | 61.4 | 81.5% | 0.97% | 10.9 | 47.8 | 103.6 | 34.7 |
| 0.017 | 60.2 | 81.0% | 0.87% | 10.8 | 46.9 | 101.6 | 34.3 |
| 0.018 | 60.0 | 81.0% | 0.87% | 10.7 | 46.6 | 101.1 | 34.1 |
| 0.02 | 58.3 | 80.4% | 0.87% | 10.5 | 45.3 | 98.4 | 33.3 |
| 0.022 | 55.0 | 79.8% | 0.85% | 10.2 | 42.4 | 93.5 | 31.0 |
| 0.025 | 50.7 | 77.5% | 0.74% | 9.8 | 39.2 | 85.7 | 28.9 |
| 0.03 | 32.1 | 68.2% | 0.49% | 7.9 | 25.0 | 53.9 | 18.7 |
| 0.05 | 18.0 | 57.8% | 0.37% | 5.8 | 13.8 | 30.9 | 10.1 |

Baseline (0.003): 78.1 min / 82.3% accuracy. Reading: minutes fall smoothly and accuracy erodes gently out to about 0.02-0.022, then the trade-off worsens sharply from 0.025 to 0.03 (a cliff, not a gentle slope) -- the same shape Addendum 34 found for the fully-documented tiers, just at somewhat higher `min_rate` values (T3-noattr's checks are individually more expensive here, so the bar has more room to rise before it starts cutting into checks that matter).

## Spot-check across 5 of Addendum 30's 18 cells (a spread of shared frequency / map fault / reliability, not just the primary cell), baseline vs the candidate (0.02)

| cell | min_rate=0.003 | min_rate=0.02 | d minutes | d accuracy | d wrong-and-confident |
|---|---|---|---|---|---|
| Cell(shared='rare', map='M0', rel='R0') | 81.2 min / 80.6% / 1.13% | 61.3 min / 78.7% / 0.40% | -19.9 (-24%) | -0.019 | -0.007 |
| Cell(shared='rare', map='M2', rel='R1') | 87.0 min / 51.9% / 7.69% | 63.0 min / 49.3% / 4.38% | -24.0 (-28%) | -0.026 | -0.033 |
| Cell(shared='assumed', map='M1', rel='R1') | 87.1 min / 59.5% / 6.40% | 61.4 min / 59.1% / 3.78% | -25.7 (-29%) | -0.004 | -0.026 |
| Cell(shared='common', map='M0', rel='R1') | 74.9 min / 68.0% / 6.05% | 52.0 min / 65.9% / 3.70% | -23.0 (-31%) | -0.020 | -0.024 |
| Cell(shared='common', map='M2', rel='R1') | 90.6 min / 61.0% / 7.89% | 62.3 min / 58.9% / 5.38% | -28.3 (-31%) | -0.021 | -0.025 |

Every one of the 5 cells: 24-31% fewer minutes, an accuracy cost of 0.4-2.6 points, and wrong-and-confident IMPROVES (never worsens) at every cell checked -- the direction and rough size hold up across very different shared-frequency, map-fault and reliability conditions, not just the one cell the fine sweep above used.

## Against the language model, on Addendum 33's own 30 visits, at each candidate `min_rate` (all visits, kind shares reweighted)

| min_rate | minutes | accuracy | wrong-and-confident | vs LLM@T2 | vs LLM@T3 |
|---|---|---|---|---|---|
| 0.003 | 68.1 | 88.8% | 0.3% | -8.2 (-11%), NEITHER | -7.8 (-10%), NEITHER |
| 0.01 | 56.3 | 88.8% | 0.3% | -19.9 (-26%), IMPROVES | -19.5 (-26%), IMPROVES |
| 0.015 | 52.3 | 88.8% | 0.3% | -24.0 (-31%), IMPROVES | -23.6 (-31%), IMPROVES |
| 0.02 | 47.3 | 87.5% | 0.3% | -29.0 (-38%), IMPROVES | -28.6 (-38%), IMPROVES |

## By kind, at the candidate (min_rate = 0.02): routine@T3-noattr minus LLM@T3 (the comparison E2's extension found losing on ordinary complaints)

| kind | d minutes | d accuracy | label |
|---|---|---|---|
| all | -28.6 (-38%) | +0.085 | IMPROVES |
| single | +0.4 (+1%) | +0.100 | NEITHER |
| multi | -16.1 (-15%) | +0.000 | NEITHER |
| shared | -150.9 (-86%) | +0.167 | IMPROVES |

## Reading

**Recommendation: `min_rate` = 0.02 for the T3-noattr profile specifically** (a separate decision from the live tool's shipped 0.015, which was tuned for the fully-documented tiers). At this value: the primary cell is about 25% faster for under 2 accuracy points, never worse on safety across the 5-cell spot-check, and -- the thing the user actually asked about -- the by-kind comparison against the language model flips from WORSE to NEITHER on single- and multi-complaint visits (no longer losing on ordinary complaints), while the aggregate becomes a clean, statistically real IMPROVES over both LLM pilots on speed, with accuracy still higher, not lower, than the language model's own. Going further (0.025) buys more speed for a larger but still moderate accuracy cost; 0.03 and beyond is a cliff, not a gentle trade, and is not recommended. **Caveat named up front: this is exploratory, not the full 18-cell pre-registered confirmation Addenda 34-36 gave the fully-documented tiers' `min_rate` values** -- the 5-cell spot-check is reassuring but is not that bar. If this value is to be shipped as a default for buildings matching this documentation profile, the same 18-cell confirmation done for 0.01/0.015 would be the honest next step, not assumed here.
