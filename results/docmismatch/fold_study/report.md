# Selective verification of rooms on a faulty handler (exploratory; FOLD_PROTOCOL.md hashed before any variant ran)

100 visits x 6 rooms, the demo's default setting (mixed-severity joint model, `min_rate` 0.02, T3-noattr), noisy answers; W0 = checks as the tool assumes, W1 = every rate 25% toward 0.5.

## Gates

- G1 the replica of the routine equals `run_policy('tool_ticket_memo2')` on every visit in both worlds: **PASS**
- G2 base accuracy equals the stored mixture-study accuracy, W0: **PASS** (replica 74.83% / 193.7 min per visit, stored 74.83% / 193.7)
- G2 base accuracy equals the stored mixture-study accuracy, W1: **PASS** (replica 54.67% / 204.8 min per visit, stored 54.67% / 204.8)
- G3 every answer in the check's vocabulary (asserted); verification checks that could not be taken (skipped, counted): 0

## W0

| variant | accuracy (all rooms) | shared rooms | own fault, faulty handler | own fault, healthy handler | own fault, no shared cause | wrong and confident | minutes / visit | checks / visit | verification checks |
|---|---|---|---|---|---|---|---|---|---|
| base | 74.8% | 92.5% | 10.5% | 77.3% | 75.0% | 6.8% | 194 | 34.3 | 0 |
| V1 verify all, box static | 77.3% | 90.5% | 43.9% | 77.3% | 75.0% | 2.3% | 236 | 39.6 | 108 |
| V2 verify all, best per minute | 77.0% | 90.5% | 40.4% | 77.3% | 75.0% | 3.7% | 229 | 39.2 | 108 |
| V3 verify two, box static | 76.7% | 90.5% | 36.8% | 77.3% | 75.0% | 3.5% | 225 | 38.6 | 47 |
| V4 verify two, best per minute | 76.5% | 90.5% | 35.1% | 77.3% | 75.0% | 4.0% | 223 | 38.5 | 47 |

Against base, paired over visits (accuracy gain = percentage points of per-room accuracy; points per minute = that gain over the added minutes per visit):

| variant | accuracy gain (95% CI) | added minutes / visit (95% CI) | points per added minute | share of added minutes on rooms base already had right | on shared-cause rooms | wrong-and-confident change, points (95% CI; interval added after the table was seen) | verdict at W0 |
|---|---|---|---|---|---|---|---|
| V1 verify all, box static | +2.5 (+0.8, +4.2) | +42 (+32, +53) | 0.06 | 60% | 61% | -4.5 (-6.5, -2.5) | NEITHER |
| V2 verify all, best per minute | +2.2 (+0.5, +4.0) | +35 (+26, +46) | 0.06 | 58% | 62% | -3.2 (-5.3, -1.3) | NEITHER |
| V3 verify two, box static | +1.8 (+0.2, +3.5) | +32 (+23, +41) | 0.06 | 57% | 61% | -3.3 (-5.2, -1.7) | NEITHER |
| V4 verify two, best per minute | +1.7 (-0.0, +3.3) | +30 (+21, +39) | 0.06 | 57% | 62% | -2.8 (-4.7, -1.2) | NEITHER |

## W1

| variant | accuracy (all rooms) | shared rooms | own fault, faulty handler | own fault, healthy handler | own fault, no shared cause | wrong and confident | minutes / visit | checks / visit | verification checks |
|---|---|---|---|---|---|---|---|---|---|
| base | 54.7% | 78.4% | 10.5% | 50.0% | 48.0% | 8.3% | 205 | 35.4 | 0 |
| V1 verify all, box static | 56.0% | 76.9% | 24.6% | 52.3% | 48.7% | 4.3% | 248 | 40.9 | 107 |
| V2 verify all, best per minute | 55.8% | 77.4% | 21.1% | 52.3% | 48.7% | 5.3% | 237 | 40.2 | 107 |
| V3 verify two, box static | 56.0% | 76.9% | 24.6% | 52.3% | 48.7% | 4.8% | 240 | 40.1 | 58 |
| V4 verify two, best per minute | 56.0% | 77.4% | 22.8% | 52.3% | 48.7% | 5.0% | 235 | 39.7 | 58 |

Against base, paired over visits (accuracy gain = percentage points of per-room accuracy; points per minute = that gain over the added minutes per visit):

| variant | accuracy gain (95% CI) | added minutes / visit (95% CI) | points per added minute | share of added minutes on rooms base already had right | on shared-cause rooms | wrong-and-confident change, points (95% CI; interval added after the table was seen) | verdict at W0 |
|---|---|---|---|---|---|---|---|
| V1 verify all, box static | +1.3 (+0.2, +2.7) | +43 (+33, +55) | 0.03 | 57% | 57% | -4.0 (-5.8, -2.3) | (not part of the verdict) |
| V2 verify all, best per minute | +1.2 (+0.0, +2.5) | +32 (+23, +42) | 0.04 | 51% | 52% | -3.0 (-5.0, -1.2) | (not part of the verdict) |
| V3 verify two, box static | +1.3 (+0.2, +2.7) | +36 (+26, +46) | 0.04 | 57% | 55% | -3.5 (-5.3, -1.8) | (not part of the verdict) |
| V4 verify two, best per minute | +1.3 (+0.2, +2.7) | +30 (+21, +39) | 0.04 | 51% | 50% | -3.3 (-5.3, -1.7) | (not part of the verdict) |

## Predictions (written before the first variant ran)

- P1 (V1: +4 to +8 points, faulty-handler own-fault rooms to at least 50%, +25 to +45 minutes / visit): **FAILED** (gain +2.5, segment 43.9%, minutes +42)
- P2 (at least 60% of V1's added minutes land on rooms base already had right): **FAILED** (60%)
- P3 (V2 gains less than V1 and its points per added minute are below 0.3): **HELD** (V2 gain +2.2 vs V1 +2.5; points per minute 0.06)
- P4 (V3 gets 30-70% of V1's gain for 30-70% of its added minutes): **FAILED** (gain fraction 0.73, minutes fraction 0.75)
- P5 (no variant is WORTH IT): **HELD** (V1 NEITHER, V2 NEITHER, V3 NEITHER, V4 NEITHER)
- P6 (no variant lifts W0 overall accuracy above 85%): **HELD** (best 77.3%)
- P7 (at W1 every variant's gain is smaller than at W0): **HELD** (V1 +1.3 vs +2.5, V2 +1.2 vs +2.2, V3 +1.3 vs +1.8, V4 +1.3 vs +1.7)

Convention that flatters verification: the oracle answers a room-level check from the room's OWN first-order cause, so a room with its own fault on a low-static handler reads 'normal' at its box; in a real building it would also read low static. The gains above are upper bounds.
