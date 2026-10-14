# Addendum 44: do generated candidate causes the fixed model may have missed increase accuracy?

Simulation only; the world's four hidden causes are my construction (not sourced). Accuracy = `ok_len` (truth, or `other` on a hidden complaint). All numbers are percent / minutes per complaint.

## What the proposers wrote and what matched (rubric: id+label first, detail as fallback)

| proposer | candidate | matched hidden cause |
|---|---|---|
| p1 | Supply air temperature wrong | sat_off |
| p1 | Duct static sensor reads wrong | — (decoy) |
| p1 | Restriction in the box inlet run | fire_damper_closed |
| p1 | Blocked or missing return air path | return_blocked |
| p1 | Sensor mapped to the wrong zone or box | — (decoy) |
| p2 | Air handler supplying wrong air temperature | sat_off |
| p2 | Restriction in the branch duct ahead of the box | fire_damper_closed |
| p2 | Operator override left on a control point | — (decoy) |
| p2 | Fan-powered box local fan or backdraft damper failed | — (decoy) |
| p2 | Return or transfer air path blocked | return_blocked |
| p3 | AHU economizer / discharge air temperature fault | sat_off |
| p3 | Supply air temperature reset or chilled-water failure | — (decoy) |
| p3 | Reheat valve leaking by or overheating the room | — (decoy) |
| p3 | Wrong operating mode: heating sequence active or ahu in warm-up/changeover | — (decoy) |
| p3 | Return/exhaust or room pressure imbalance | return_blocked |
| p3 | Fire/smoke or isolation damper partly closed in the duct | fire_damper_closed |
| p3f | AHU economizer / discharge air temperature fault | sat_off |
| p3f | Supply air temperature reset or chilled-water failure | — (decoy) |
| p3f | Reheat valve leaking by or overheating the room | — (decoy) |
| p3f | Wrong operating mode: heating sequence active or ahu in warm-up/changeover | — (decoy) |
| p3f | Return/exhaust or room pressure imbalance | fire_damper_closed |
| p3f | Fire/smoke or isolation damper partly closed in the duct | — (decoy) |

## T2, m = 0.0 (0 hidden of 1500 complaints)

| arm | overall | in-model | hidden strict | hidden lenient | wrong&confident | minutes | gain vs A (95% CI) | in-model Δ | w&c Δ |
|---|---|---|---|---|---|---|---|---|---|
| A fixed |  71.9 |  71.9 |   nan |   nan |   0.1 | 50.7 | — | — | — |
| B_all:p1 |  68.3 |  68.3 |   nan |   nan |   0.0 | 53.8 | -3.6 (-5.5, -1.7) | -3.6 | -0.1 |
| B_match:p1 |  68.5 |  68.5 |   nan |   nan |   0.1 | 53.3 | -3.3 (-5.1, -1.5) | -3.3 | -0.1 |
| B_all:p2 |  66.0 |  66.0 |   nan |   nan |   0.3 | 53.5 | -5.9 (-7.9, -3.9) | -5.9 | +0.2 |
| B_match:p2 |  68.2 |  68.2 |   nan |   nan |   0.4 | 52.8 | -3.7 (-5.4, -1.8) | -3.7 | +0.3 |
| B_all:p3 |  69.1 |  69.1 |   nan |   nan |   0.1 | 53.5 | -2.8 (-4.6, -1.0) | -2.8 | -0.1 |
| B_match:p3 |  69.3 |  69.3 |   nan |   nan |   0.1 | 52.4 | -2.6 (-4.3, -0.9) | -2.6 | -0.1 |
| B_all:p3f |  69.1 |  69.1 |   nan |   nan |   0.1 | 53.5 | -2.8 (-4.6, -1.0) | -2.8 | -0.1 |
| B_match:p3f |  69.9 |  69.9 |   nan |   nan |   0.1 | 52.4 | -1.9 (-3.5, -0.4) | -1.9 | -0.1 |
| D |  71.3 |  71.3 |   nan |   nan |   0.1 | 50.8 | -0.5 (-1.3, +0.2) | -0.5 | +0.0 |
| C |  71.3 |  71.3 |   nan |   nan |   0.1 | 50.8 | -0.5 (-1.3, +0.2) | -0.5 | +0.0 |

## T2, m = 0.05 (70 hidden of 1500 complaints)

| arm | overall | in-model | hidden strict | hidden lenient | wrong&confident | minutes | gain vs A (95% CI) | in-model Δ | w&c Δ |
|---|---|---|---|---|---|---|---|---|---|
| A fixed |  70.3 |  72.6 |   0.0 |  24.3 |   0.2 | 51.6 | — | — | — |
| B_all:p1 |  66.2 |  67.8 |  28.6 |  32.9 |   0.0 | 54.3 | -4.1 (-5.9, -2.1) | -4.8 | -0.2 |
| B_match:p1 |  67.3 |  69.0 |  28.6 |  32.9 |   0.1 | 54.0 | -3.0 (-4.8, -1.2) | -3.6 | -0.1 |
| B_all:p2 |  64.7 |  65.8 |  37.1 |  41.4 |   0.2 | 54.5 | -5.7 (-7.6, -3.7) | -6.8 | +0.0 |
| B_match:p2 |  67.2 |  68.9 |  28.6 |  32.9 |   0.3 | 53.4 | -3.1 (-4.9, -1.3) | -3.7 | +0.1 |
| B_all:p3 |  67.1 |  68.8 |  28.6 |  32.9 |   0.1 | 54.3 | -3.2 (-5.1, -1.2) | -3.8 | -0.1 |
| B_match:p3 |  67.7 |  69.4 |  28.6 |  32.9 |   0.1 | 53.2 | -2.7 (-4.4, -0.9) | -3.2 | -0.1 |
| B_all:p3f |  66.6 |  68.8 |  17.1 |  21.4 |   0.1 | 54.4 | -3.7 (-5.5, -1.7) | -3.8 | -0.1 |
| B_match:p3f |  68.6 |  71.0 |  15.7 |  20.0 |   0.1 | 53.2 | -1.7 (-3.4, -0.1) | -1.6 | -0.1 |
| D |  71.7 |  73.0 |   0.0 |  45.7 |   0.1 | 52.0 | +1.4 (+0.1, +2.7) | +0.4 | -0.1 |
| C |  72.5 |  72.8 |  30.0 |  67.1 |   0.1 | 53.5 | +2.2 (+0.8, +3.6) | +0.2 | -0.1 |

## T2, m = 0.1 (151 hidden of 1500 complaints)

| arm | overall | in-model | hidden strict | hidden lenient | wrong&confident | minutes | gain vs A (95% CI) | in-model Δ | w&c Δ |
|---|---|---|---|---|---|---|---|---|---|
| A fixed |  70.7 |  73.5 |   0.0 |  46.4 |   0.2 | 52.8 | — | — | — |
| B_all:p1 |  64.9 |  67.7 |  34.4 |  40.4 |   0.0 | 54.3 | -5.8 (-7.8, -3.8) | -5.8 | -0.2 |
| B_match:p1 |  65.7 |  68.6 |  33.8 |  39.7 |   0.1 | 54.1 | -5.1 (-7.0, -3.2) | -4.9 | -0.1 |
| B_all:p2 |  63.9 |  65.7 |  44.4 |  48.3 |   0.3 | 54.0 | -6.8 (-8.9, -4.6) | -7.8 | +0.1 |
| B_match:p2 |  65.5 |  68.3 |  35.1 |  39.7 |   0.5 | 53.5 | -5.3 (-7.2, -3.4) | -5.1 | +0.3 |
| B_all:p3 |  65.4 |  68.3 |  33.1 |  39.1 |   0.1 | 55.0 | -5.3 (-7.3, -3.3) | -5.1 | -0.1 |
| B_match:p3 |  65.7 |  68.6 |  34.4 |  39.7 |   0.1 | 53.6 | -5.0 (-6.9, -3.1) | -4.8 | -0.1 |
| B_all:p3f |  64.3 |  68.3 |  21.9 |  27.8 |   0.1 | 55.2 | -6.5 (-8.4, -4.4) | -5.1 | -0.1 |
| B_match:p3f |  65.1 |  69.2 |  22.5 |  28.5 |   0.2 | 54.1 | -5.6 (-7.3, -3.8) | -4.2 | +0.0 |
| D |  70.3 |  72.6 |   0.0 |  49.7 |   0.2 | 53.0 | -0.4 (-1.9, +1.1) | -0.8 | +0.0 |
| C |  72.1 |  71.8 |  33.8 |  75.5 |   0.2 | 55.9 | +1.4 (-0.1, +3.1) | -1.7 | +0.0 |

## T2, m = 0.2 (306 hidden of 1500 complaints)

| arm | overall | in-model | hidden strict | hidden lenient | wrong&confident | minutes | gain vs A (95% CI) | in-model Δ | w&c Δ |
|---|---|---|---|---|---|---|---|---|---|
| A fixed |  63.3 |  70.8 |   0.0 |  34.0 |   0.3 | 53.4 | — | — | — |
| B_all:p1 |  59.5 |  66.1 |  29.4 |  33.7 |   0.1 | 56.0 | -3.8 (-6.1, -1.7) | -4.7 | -0.2 |
| B_match:p1 |  59.2 |  65.3 |  29.4 |  35.3 |   0.3 | 55.7 | -4.1 (-6.2, -2.1) | -5.4 | -0.1 |
| B_all:p2 |  59.6 |  64.2 |  38.2 |  41.8 |   0.3 | 56.0 | -3.7 (-6.0, -1.4) | -6.6 | -0.1 |
| B_match:p2 |  58.9 |  65.1 |  30.1 |  34.6 |   0.4 | 54.9 | -4.4 (-6.6, -2.5) | -5.7 | +0.1 |
| B_all:p3 |  60.0 |  67.3 |  27.8 |  31.7 |   0.3 | 56.7 | -3.3 (-5.5, -1.1) | -3.5 | -0.1 |
| B_match:p3 |  59.3 |  65.7 |  28.8 |  34.6 |   0.3 | 54.9 | -3.9 (-6.1, -2.0) | -5.1 | +0.0 |
| B_all:p3f |  58.9 |  67.3 |  22.2 |  26.1 |   0.3 | 57.0 | -4.4 (-6.7, -2.3) | -3.5 | -0.1 |
| B_match:p3f |  58.6 |  66.6 |  21.6 |  27.5 |   0.2 | 55.4 | -4.7 (-6.6, -2.9) | -4.2 | -0.1 |
| D |  58.4 |  66.2 |  21.9 |  27.8 |   0.2 | 54.3 | -4.9 (-6.7, -3.1) | -4.5 | -0.1 |
| C |  70.6 |  68.4 |  63.1 |  79.1 |   0.2 | 61.0 | +7.3 (+5.0, +9.6) | -2.3 | -0.1 |

## T3, m = 0.0 (0 hidden of 1500 complaints)

| arm | overall | in-model | hidden strict | hidden lenient | wrong&confident | minutes | gain vs A (95% CI) | in-model Δ | w&c Δ |
|---|---|---|---|---|---|---|---|---|---|
| A fixed |  78.7 |  78.7 |   nan |   nan |   0.5 | 37.6 | — | — | — |
| B_all:p1 |  70.7 |  70.7 |   nan |   nan |   0.5 | 40.3 | -7.9 (-10.7, -5.4) | -7.9 | +0.0 |
| B_match:p1 |  75.5 |  75.5 |   nan |   nan |   0.5 | 38.3 | -3.2 (-5.6, -0.9) | -3.2 | -0.1 |
| B_all:p2 |  71.5 |  71.5 |   nan |   nan |   0.9 | 40.6 | -7.1 (-9.7, -4.7) | -7.1 | +0.3 |
| B_match:p2 |  75.3 |  75.3 |   nan |   nan |   0.7 | 37.4 | -3.3 (-5.8, -1.1) | -3.3 | +0.1 |
| B_all:p3 |  73.7 |  73.7 |   nan |   nan |   0.3 | 42.0 | -5.0 (-7.5, -2.6) | -5.0 | -0.2 |
| B_match:p3 |  75.7 |  75.7 |   nan |   nan |   0.5 | 38.9 | -3.0 (-5.5, -0.7) | -3.0 | +0.0 |
| B_all:p3f |  73.7 |  73.7 |   nan |   nan |   0.3 | 42.0 | -5.0 (-7.5, -2.6) | -5.0 | -0.2 |
| B_match:p3f |  74.4 |  74.4 |   nan |   nan |   0.9 | 38.6 | -4.3 (-6.2, -2.5) | -4.3 | +0.3 |
| D |  77.9 |  77.9 |   nan |   nan |   0.6 | 37.9 | -0.7 (-1.7, +0.2) | -0.7 | +0.1 |
| C |  77.9 |  77.9 |   nan |   nan |   0.6 | 38.0 | -0.7 (-1.7, +0.2) | -0.7 | +0.1 |

## T3, m = 0.05 (71 hidden of 1500 complaints)

| arm | overall | in-model | hidden strict | hidden lenient | wrong&confident | minutes | gain vs A (95% CI) | in-model Δ | w&c Δ |
|---|---|---|---|---|---|---|---|---|---|
| A fixed |  76.7 |  78.9 |   0.0 |  33.8 |   0.5 | 38.5 | — | — | — |
| B_all:p1 |  70.3 |  71.4 |  33.8 |  49.3 |   0.5 | 40.5 | -6.4 (-9.0, -3.9) | -7.5 | -0.1 |
| B_match:p1 |  74.6 |  74.9 |  28.2 |  67.6 |   0.4 | 39.3 | -2.1 (-4.5, +0.2) | -3.9 | -0.1 |
| B_all:p2 |  70.0 |  71.0 |  33.8 |  49.3 |   0.4 | 40.4 | -6.7 (-9.1, -4.3) | -7.8 | -0.1 |
| B_match:p2 |  74.4 |  74.7 |  28.2 |  67.6 |   0.5 | 38.4 | -2.3 (-4.7, +0.0) | -4.1 | +0.0 |
| B_all:p3 |  67.1 |  69.3 |  21.1 |  22.5 |   0.5 | 42.6 | -9.6 (-12.1, -7.2) | -9.5 | -0.1 |
| B_match:p3 |  74.5 |  75.2 |  28.2 |  62.0 |   0.7 | 39.4 | -2.2 (-4.6, +0.2) | -3.7 | +0.1 |
| B_all:p3f |  67.3 |  69.3 |  25.4 |  26.8 |   0.5 | 42.6 | -9.4 (-11.9, -7.0) | -9.5 | -0.1 |
| B_match:p3f |  76.9 |  77.3 |  35.2 |  69.0 |   0.3 | 38.9 | +0.2 (-1.7, +2.1) | -1.5 | -0.3 |
| D |  76.0 |  78.3 |   2.8 |  29.6 |   0.6 | 39.0 | -0.7 (-1.7, +0.2) | -0.6 | +0.1 |
| C |  76.0 |  78.0 |  12.7 |  36.6 |   0.6 | 39.1 | -0.7 (-1.7, +0.2) | -0.9 | +0.1 |

## T3, m = 0.1 (144 hidden of 1500 complaints)

| arm | overall | in-model | hidden strict | hidden lenient | wrong&confident | minutes | gain vs A (95% CI) | in-model Δ | w&c Δ |
|---|---|---|---|---|---|---|---|---|---|
| A fixed |  75.1 |  79.1 |   0.0 |  37.5 |   0.3 | 39.9 | — | — | — |
| B_all:p1 |  69.4 |  71.3 |  40.3 |  51.4 |   0.3 | 41.1 | -5.7 (-8.5, -3.1) | -7.8 | +0.1 |
| B_match:p1 |  74.7 |  75.0 |  36.8 |  72.2 |   0.2 | 39.3 | -0.4 (-2.9, +2.0) | -4.1 | -0.1 |
| B_all:p2 |  67.5 |  69.5 |  36.1 |  48.6 |   0.5 | 41.1 | -7.6 (-10.3, -5.0) | -9.6 | +0.3 |
| B_match:p2 |  74.9 |  75.0 |  38.2 |  73.6 |   0.4 | 38.2 | -0.3 (-2.8, +2.2) | -4.1 | +0.1 |
| B_all:p3 |  68.3 |  72.0 |  28.5 |  33.3 |   0.2 | 43.5 | -6.9 (-9.4, -4.4) | -7.2 | -0.1 |
| B_match:p3 |  76.2 |  76.5 |  35.4 |  73.6 |   0.5 | 40.3 | +1.1 (-1.5, +3.5) | -2.7 | +0.2 |
| B_all:p3f |  68.1 |  72.0 |  27.1 |  31.9 |   0.2 | 43.5 | -7.0 (-9.6, -4.5) | -7.2 | -0.1 |
| B_match:p3f |  73.9 |  74.0 |  41.0 |  72.9 |   0.4 | 39.5 | -1.2 (-3.3, +0.9) | -5.1 | +0.1 |
| D |  75.5 |  77.6 |  18.8 |  56.2 |   0.2 | 40.0 | +0.4 (-1.4, +2.2) | -1.5 | -0.1 |
| C |  75.8 |  76.8 |  38.9 |  66.7 |   0.2 | 40.3 | +0.7 (-1.1, +2.5) | -2.4 | -0.1 |

## T3, m = 0.2 (290 hidden of 1500 complaints)

| arm | overall | in-model | hidden strict | hidden lenient | wrong&confident | minutes | gain vs A (95% CI) | in-model Δ | w&c Δ |
|---|---|---|---|---|---|---|---|---|---|
| A fixed |  71.6 |  78.8 |   0.0 |  41.7 |   0.4 | 40.9 | — | — | — |
| B_all:p1 |  66.9 |  71.4 |  37.2 |  48.3 |   0.3 | 41.5 | -4.7 (-7.4, -2.1) | -7.4 | -0.1 |
| B_match:p1 |  74.7 |  75.7 |  34.8 |  70.7 |   0.3 | 40.0 | +3.1 (+0.6, +5.6) | -3.1 | -0.1 |
| B_all:p2 |  66.5 |  69.8 |  39.0 |  52.4 |   0.5 | 41.5 | -5.1 (-7.7, -2.7) | -8.9 | +0.1 |
| B_match:p2 |  74.6 |  75.3 |  35.9 |  71.7 |   0.7 | 39.0 | +3.0 (+0.5, +5.5) | -3.5 | +0.3 |
| B_all:p3 |  62.3 |  69.8 |  27.2 |  31.0 |   0.3 | 44.4 | -9.3 (-11.9, -6.9) | -8.9 | -0.1 |
| B_match:p3 |  72.7 |  73.7 |  34.1 |  68.6 |   0.4 | 41.0 | +1.1 (-1.6, +3.6) | -5.0 | +0.0 |
| B_all:p3f |  62.3 |  69.8 |  26.9 |  30.7 |   0.3 | 44.4 | -9.3 (-12.1, -6.9) | -8.9 | -0.1 |
| B_match:p3f |  75.5 |  76.7 |  34.1 |  70.3 |   0.3 | 39.4 | +3.9 (+1.7, +6.1) | -2.1 | -0.1 |
| D |  67.3 |  73.0 |  39.0 |  43.8 |   0.5 | 44.2 | -4.3 (-7.0, -1.7) | -5.8 | +0.1 |
| C |  70.5 |  73.2 |  54.5 |  59.3 |   0.5 | 46.6 | -1.1 (-3.9, +1.6) | -5.5 | +0.1 |

## Frozen decision rule (m = 0.10): B_all vs A

| tier | proposer | gain CI>0 | in-model loss ≤2 | w&c rise ≤1 | all three |
|---|---|---|---|---|---|
| T2 | p1 | False (-5.8) | False (-5.8) | True (-0.2) | **False** |
| T2 | p2 | False (-6.8) | False (-7.8) | True (+0.1) | **False** |
| T2 | p3 | False (-5.3) | False (-5.1) | True (-0.1) | **False** |
| T2 | p3f | False (-6.5) | False (-5.1) | True (-0.1) | **False** |
| T3 | p1 | False (-5.7) | False (-7.8) | True (+0.1) | **False** |
| T3 | p2 | False (-7.6) | False (-9.6) | True (+0.3) | **False** |
| T3 | p3 | False (-6.9) | False (-7.2) | True (-0.1) | **False** |
| T3 | p3f | False (-7.0) | False (-7.2) | True (-0.1) | **False** |

**Verdict:** NO (0 of 6 proposer×tier cases pass all three conditions; p3f is a sensitivity row, not counted).