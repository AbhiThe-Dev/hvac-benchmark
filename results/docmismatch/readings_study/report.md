# Graded readings, first look (exploratory; predictions in READINGS_NOTES.md)

Single complaints on the bldg11 point map, n = 1500 per cell, accuracy % (minutes per complaint) [confidently wrong %].

| world | numbers from | yes/no baseline | binary arm | graded arm | graded minus binary, accuracy points (95% CI) | minutes | numeric readings per visit | minutes with +0.5 min per reading |
|---|---|---|---|---|---|---|---|---|
| W0 | matched | 73.6% (46) [0.3] | 72.3% (47) [0.3] | 74.1% (45) [0.3] | +1.7 (+0.3, +3.1); confidently wrong +0.1 | -1.9 | 2.93 | 48 vs 46 |
| W0 | mismatched | 73.6% (46) [0.3] | 67.8% (47) [0.3] | 66.9% (44) [1.7] | -0.9 (-2.3, +0.5); confidently wrong +1.3 | -2.9 | 2.88 | 49 vs 46 |
| W1 | matched | 45.8% (46) [3.7] | 46.3% (46) [4.3] | 46.1% (44) [6.1] | -0.3 (-1.9, +1.4); confidently wrong +1.7 | -2.4 | 2.97 | 48 vs 45 |
| W1 | mismatched | 45.8% (46) [3.7] | 46.2% (46) [3.4] | 46.8% (44) [6.3] | +0.6 (-1.1, +2.3); confidently wrong +2.9 | -2.4 | 2.91 | 48 vs 45 |

## Predictions (written before the run)

- P0 sanity (binary arm vs yes/no baseline, W0 matched: accuracy within 2 points and minutes within 3): HELD (accuracy 72.3% vs 73.6%, minutes 46.6 vs 46.0)
- P1 (matched, W0: graded +1 to +6 points, minutes within 8%): HELD (gain +1.7, minutes -4.0%)
- P2 (matched, W1: graded still gains and confidently-wrong rises by at least 1 point): FAILED (gain -0.3, confidently wrong +1.7)
- P3 (mismatched W0 gain at most half of matched W0 gain): HELD (mismatched -0.9 vs matched +1.7)
- P4 (no W0 cell reaches 80%): HELD
- P5 (entry cost changes minutes by less than 3): HELD (1.5 min)
