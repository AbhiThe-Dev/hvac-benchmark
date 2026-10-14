# The tuned routine (min_rate = 0.02) against the language model, on Addendum 33's own 30 visits

`min_rate` = 0.02 here is the live default. This value (0.02) has only been checked on the primary cell, NOT confirmed across the other 17 cells the way 0.01 was (Addendum 35). Not a new experiment otherwise: it applies an already-fixed setting (chosen on evidence that never involved a language model) to the exact 30 visits Addendum 33 already ran the language model on, and reads the numbers off together. Simulation only; a language model is not a technician; the 30-visit sample is small (wide intervals).

## Minutes / accuracy / wrong-and-confident / checks (all visits, kind shares reweighted)

| policy | T2 | T3 |
|---|---|---|
| LLM technician | 76.2 min / 82% / 16.1% / 8.8 | 75.9 min / 79% / 5.0% / 16.3 |
| routine (min_rate=0.003, as it stands) | 92.0 min / 84% / 0.3% / 9.5 | 57.9 min / 87% / 0.3% / 11.3 |
| routine, tuned (min_rate=0.02) | 59.3 min / 79% / 0.0% / 6.9 | 48.2 min / 87% / 0.3% / 10.0 |
| joint tool | 101.5 min / 84% / 0.3% / 10.0 | 65.7 min / 90% / 0.3% / 11.9 |
| fast_parent (my rule) | 94.1 min / 62% / 38.2% / 9.7 | 79.6 min / 60% / 39.6% / 11.6 |

## Paired comparisons (all visits, kind shares reweighted)

| comparison | tier | d minutes | d accuracy | d wrong-and-confident | time / accuracy | label |
|---|---|---|---|---|---|---|
| A: LLM - tuned routine  [does tuning close the gap?] | T2 | +16.9 (+29%) | +0.032 | +0.161 | SLOWER / SAME | WORSE |
| A: LLM - tuned routine  [does tuning close the gap?] | T3 | +27.7 (+57%) | -0.082 | +0.048 | SLOWER / SAME | WORSE |
| B: tuned - original routine  [the tuning itself, on this sample] | T2 | -32.7 (-36%) | -0.052 | -0.003 | FASTER / LESS | TRADE |
| B: tuned - original routine  [the tuning itself, on this sample] | T3 | -9.7 (-17%) | +0.000 | +0.000 | FASTER / SAME | IMPROVES |
| C: LLM - original routine  [Addendum 33's comparison, replayed here] | T2 | -15.8 (-17%) | -0.020 | +0.158 | FASTER / SAME | IMPROVES |
| C: LLM - original routine  [Addendum 33's comparison, replayed here] | T3 | +18.0 (+31%) | -0.082 | +0.048 | SLOWER / SAME | WORSE |
| D: tuned - fast_parent | T2 | -34.7 (-37%) | +0.169 | -0.382 | FASTER / MORE | IMPROVES |
| D: tuned - fast_parent | T3 | -31.4 (-39%) | +0.268 | -0.393 | FASTER / MORE | IMPROVES |

## By kind: LLM minus the tuned routine

| kind | tier | d minutes | d accuracy | label |
|---|---|---|---|---|
| all | T2 | +16.9 (+29%) | +0.032 | WORSE |
| all | T3 | +27.7 (+57%) | -0.082 | WORSE |
| single | T2 | +6.5 (+15%) | +0.000 | NEITHER |
| single | T3 | -1.8 (-5%) | -0.100 | NEITHER |
| multi | T2 | +27.6 (+25%) | +0.150 | WORSE |
| multi | T3 | +11.2 (+11%) | +0.000 | NEITHER |
| shared | T2 | +37.1 (+123%) | -0.042 | NEITHER |
| shared | T3 | +157.8 (+923%) | -0.150 | WORSE |

## Reading

See the tables: read off, per tier, whether the tuned routine and the language model differ in speed (time column), accuracy and wrong-and-confident, and whether that difference is a real one (the label) or within noise (NEITHER). By kind: on shared-cause visits the routine's own shortcut, not this tuning, is what keeps it ahead of the language model (Addendum 33).
