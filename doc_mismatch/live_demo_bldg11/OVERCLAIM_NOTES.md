# What if the tool is TOLD the checks are more reliable than they really are? (EXPLORATORY; written and hashed before the run)

## Question

Earlier runs always gave the tool and the simulated world the same rates (or let the world be worse than the tool's). Here the tool is given SHARPER rates than the world delivers. Does it still pick the right cause, and is what it claims still true?

## Design (fixed now)

The same 100 registered visits, the demo's mixed setting, `min_rate` 0.02, T3-noattr. The WORLD answers with today's catalogue rates (W0) or with every rate 25% toward 0.5 (W1). The TOOL assumes today's rates (honest) or rates moved away from 0.5 by 10% or 25% (the same `shift` as `study_trend.py`: inflated claims; strong checks nearly error-free). 3 tool arms x 2 worlds.
Measures per cell: accuracy; wrong-and-confident; the share of rooms the tool concludes; PRECISION of its conclusions (among rooms it concludes at 95% belief, the share that are right); minutes per visit. Paired bootstrap over visits against the honest tool in the same world.

## Gates

G1: the honest tool in W0 and W1 equals the stored 74.83% / 54.67% and 193.7 / 204.8 minutes.

## Predictions (before the run)

- R1: in W0 the 25%-inflated tool loses at least 5 accuracy points against the honest tool.
- R2: in W0 its wrong-and-confident rate is at least double the honest tool's (6.8%).
- R3: the 10%-inflated tool loses less than the 25%-inflated one, on accuracy and on wrong-and-confident.
- R4: the 25%-inflated tool uses at least 10% fewer minutes than the honest tool (it believes it can stop sooner).
- R5: the precision of its conclusions is below 80% in W0 (the honest tool's is about 84%).
- R6: in W1 the inflated tools are also worse than the honest one on wrong-and-confident.
