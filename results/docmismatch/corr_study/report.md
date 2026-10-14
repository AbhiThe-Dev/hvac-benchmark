# Correlated check errors (exploratory; CORR_NOTES.md hashed before any correlated run)

100 registered visits x 6 rooms, the demo's mixed setting. pi = probability that a box's control-system data is invalid (all control-system checks at that box then answer in one shared direction, whatever the cause). The correlated world is my construction; no data say how often it happens.

## Gates

- G1 independent tool at pi = 0 equals the stored accuracy and minutes, W0: **PASS** (74.83%, 193.7 min)
- G1 independent tool at pi = 0 equals the stored accuracy and minutes, W1: **PASS** (54.67%, 204.8 min)
- G2 the mixture arm with p_t = 1e-12 equals the independent arm (guesses, conclusions, minutes) at pi = 0.10: **PASS**
- G3 the oracle is order-independent (20 visits, forward vs backward): **PASS**

## W0

| data invalid (pi) | tool | accuracy | wrong and confident | rooms with invalid data: accuracy / wrong-and-confident | rooms with valid data: accuracy / wrong-and-confident | minutes / visit | wrong-and-confident vs independent tool at pi = 0, points (95% CI) | accuracy vs independent tool at the same pi, points (95% CI) | minutes vs independent tool at the same pi |
|---|---|---|---|---|---|---|---|---|---|
| 0.00 | independent | 74.8% | 6.8% | - | 75% / 7% | 194 | +0.0 (+0.0, +0.0) | - | - |
| 0.00 | tempered | 72.2% | 6.5% | - | 72% / 6% | 208 | -0.3 (-1.0, +0.3) | -2.7 (-4.5, -1.0) | +15 |
| 0.00 | mixture (p_t 0.10) | 74.8% | 5.7% | - | 75% / 6% | 197 | -1.2 (-2.2, -0.3) | -0.0 (-0.5, +0.5) | +3 |
| 0.10 | independent | 73.7% | 7.2% | 67% / 8% | 75% / 7% | 194 | +0.3 (+0.0, +0.8) | - | - |
| 0.10 | tempered | 71.8% | 6.8% | 69% / 8% | 72% / 7% | 209 | +0.0 (-0.8, +0.8) | -1.8 (-3.7, -0.2) | +15 |
| 0.10 | mixture (p_t 0.10) | 73.7% | 6.0% | 67% / 8% | 75% / 6% | 200 | -0.8 (-1.8, +0.0) | -0.0 (-0.7, +0.7) | +6 |
| 0.25 | independent | 72.8% | 7.5% | 67% / 9% | 75% / 7% | 197 | +0.7 (-0.2, +1.5) | - | - |
| 0.25 | tempered | 72.0% | 7.3% | 71% / 8% | 72% / 7% | 210 | +0.5 (-0.5, +1.5) | -0.8 (-2.8, +1.0) | +13 |
| 0.25 | mixture (p_t 0.10) | 73.5% | 6.3% | 70% / 8% | 75% / 6% | 205 | -0.5 (-1.7, +0.5) | +0.7 (-0.2, +1.7) | +9 |

## W1

| data invalid (pi) | tool | accuracy | wrong and confident | rooms with invalid data: accuracy / wrong-and-confident | rooms with valid data: accuracy / wrong-and-confident | minutes / visit | wrong-and-confident vs independent tool at pi = 0, points (95% CI) | accuracy vs independent tool at the same pi, points (95% CI) | minutes vs independent tool at the same pi |
|---|---|---|---|---|---|---|---|---|---|
| 0.00 | independent | 54.7% | 8.3% | - | 55% / 8% | 205 | +0.0 (+0.0, +0.0) | - | - |
| 0.00 | tempered | 52.3% | 8.5% | - | 52% / 8% | 226 | +0.2 (-1.2, +1.5) | -2.3 (-4.7, -0.0) | +21 |
| 0.00 | mixture (p_t 0.10) | 54.5% | 8.0% | - | 55% / 8% | 209 | -0.3 (-1.3, +0.5) | -0.2 (-1.2, +0.7) | +4 |
| 0.10 | independent | 53.8% | 8.8% | 48% / 9% | 55% / 9% | 199 | +0.5 (-0.3, +1.7) | - | - |
| 0.10 | tempered | 52.2% | 8.3% | 49% / 6% | 53% / 9% | 224 | +0.0 (-1.2, +1.2) | -1.7 (-3.8, +0.5) | +26 |
| 0.10 | mixture (p_t 0.10) | 53.8% | 8.0% | 49% / 6% | 54% / 8% | 205 | -0.3 (-1.7, +0.8) | -0.0 (-1.3, +1.3) | +6 |
| 0.25 | independent | 52.7% | 9.2% | 45% / 11% | 55% / 9% | 201 | +0.8 (-0.2, +2.0) | - | - |
| 0.25 | tempered | 52.0% | 8.5% | 48% / 8% | 53% / 9% | 226 | +0.2 (-1.0, +1.5) | -0.7 (-2.8, +1.3) | +26 |
| 0.25 | mixture (p_t 0.10) | 53.2% | 8.5% | 47% / 9% | 55% / 8% | 210 | +0.2 (-1.0, +1.3) | +0.5 (-1.0, +2.0) | +9 |

## Verdicts at W0 (rule fixed beforehand)

- HARM of correlation (independent tool, pi 0 to 0.10, wrong-and-confident up by at least 1 point with the interval above 0): **NO** (+0.3 points, interval +0.0 to +0.8)
- tempered REPAIRS at pi = 0.10: **YES** (wrong-and-confident 6.8% against 6.8% at pi = 0; accuracy -1.8; minutes +15)
- mixture (p_t 0.10) REPAIRS at pi = 0.10: **YES** (wrong-and-confident 6.0% against 6.8% at pi = 0; accuracy -0.0; minutes +6)

## Predictions (written before any correlated run)

- C1 (independent tool, pi 0.10: wrong-and-confident at least 2 points above pi = 0): **FAILED** (+0.3)
- C2 (independent tool, pi 0.25: accuracy at least 3 points below pi = 0): **FAILED** (-2.0)
- C3 (mixture at pi 0.10 within 1 point of the pi = 0 wrong-and-confident level): **HELD** (6.0% vs 6.8%)
- C4 (tempered lowers wrong-and-confident at pi 0.10, by less than the mixture): **HELD** (tempered 6.8%, mixture 6.0%, independent 7.2%)
- C5 (at pi = 0 neither repair costs more than 2 accuracy points): **FAILED** (tempered -2.7, mixture -0.0)
- C6 (mixture adds at least 5% minutes at pi 0.10): **FAILED** (+6 min on 194)
