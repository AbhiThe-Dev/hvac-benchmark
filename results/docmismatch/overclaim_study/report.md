# What if the tool is told the checks are more reliable than they are? (exploratory; OVERCLAIM_NOTES.md hashed before the run)

Same 100 visits, mixed setting. The WORLD answers with today's catalogue rates (W0) or 25% worse (W1); the TOOL believes today's rates, or rates sharper by 10% or 25%.

## Gate

- G1 honest tool equals the stored accuracy and minutes, W0: **PASS** (74.83%)
- G1 honest tool equals the stored accuracy and minutes, W1: **PASS** (54.67%)

## W0

| the tool believes | accuracy | accuracy vs honest (95% CI) | wrong and confident | rooms it concludes | precision of its conclusions | minutes / visit |
|---|---|---|---|---|---|---|
| honest (today's rates) | 74.8% | - | 6.8% | 43% | 84% | 194 |
| inflated 10% | 69.7% | -5.2 (-8.8, -1.7) | 18.5% | 74% | 75% | 148 |
| inflated 25% | 69.5% | -5.3 (-8.8, -2.3) | 19.5% | 80% | 75% | 148 |

## W1

| the tool believes | accuracy | accuracy vs honest (95% CI) | wrong and confident | rooms it concludes | precision of its conclusions | minutes / visit |
|---|---|---|---|---|---|---|
| honest (today's rates) | 54.7% | - | 8.3% | 36% | 77% | 205 |
| inflated 10% | 46.8% | -7.8 (-11.7, -4.0) | 40.0% | 80% | 50% | 128 |
| inflated 25% | 45.8% | -8.8 (-12.2, -5.7) | 42.0% | 82% | 49% | 126 |

## Predictions (written before the run)

- R1 (W0: the 25%-inflated tool loses at least 5 accuracy points): **HELD** (-5.3)
- R2 (W0: its wrong-and-confident rate at least doubles): **HELD** (19.5% vs 6.8%)
- R3 (the 10%-inflated tool loses less than the 25% one on both): **HELD** (10%: -5.2 / 18.5%; 25%: -5.3 / 19.5%)
- R4 (the 25%-inflated tool uses at least 10% fewer minutes): **HELD** (148 vs 194)
- R5 (precision of its conclusions below 80% in W0): **HELD** (75% (honest 84%))
- R6 (W1: the inflated tools are worse than the honest one on wrong-and-confident): **HELD** (honest (today's rates) 8.3%, inflated 10% 40.0%, inflated 25% 42.0%)
