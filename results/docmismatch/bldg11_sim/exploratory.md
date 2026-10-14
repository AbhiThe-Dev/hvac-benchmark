# Exploratory breakdown of the registered run (post-hoc; not registered, scores nothing)

Source: `complaints.csv` of the registered run. Strict scoring is the registered one: a complaint is right only if the leading cause equals the true first-order cause.

## W0

| policy | concluded | concluded and wrong | of which: local fault on a room of the faulty handler, named low static | false shared call, local visits | false shared call, shared visits (AHU06 rooms) | (AHU05 rooms) |
|---|---|---|---|---|---|---|
| tool_shipped | 72 of 600 | 3 (4% of concluded) | 0 | 0/300 | 0/57 | 0/44 |
| tool_adjusted | 245 of 600 | 45 (18% of concluded) | 43 | 1/300 | 52/57 | 0/44 |
| fast_parent | 600 of 600 | 279 (46% of concluded) | 45 | 8/300 | 45/57 | 0/44 |

## W1

| policy | concluded | concluded and wrong | of which: local fault on a room of the faulty handler, named low static | false shared call, local visits | false shared call, shared visits (AHU06 rooms) | (AHU05 rooms) |
|---|---|---|---|---|---|---|
| tool_shipped | 49 of 600 | 14 (29% of concluded) | 0 | 0/300 | 0/57 | 0/44 |
| tool_adjusted | 215 of 600 | 63 (29% of concluded) | 42 | 15/300 | 51/57 | 3/44 |
| fast_parent | 600 of 600 | 405 (68% of concluded) | 44 | 44/300 | 44/57 | 7/44 |

## What the folded calls are

In a shared visit, a complaint whose own cause is local but whose room hangs on the faulty handler is scored wrong if the tool names low static. Physically such a room is starved *and* has its own fault, so 'wrong' there means 'missed the second fault', not 'named a cause that is not present'. The registered metric (one first-order cause per complaint, listed as a limitation in the protocol) does not credit it.

Alternative scoring, NOT registered, shown only to size the effect: count a low-static call on a local-cause room of the faulty handler in a shared visit as correct.

| policy | world | registered accuracy | accuracy with those calls counted correct | registered wrong-and-confident | with those calls removed |
|---|---|---|---|---|---|
| tool_adjusted | W0 | 74.7% | 83.3% | 7.5% | 0.3% |
| tool_adjusted | W1 | 55.3% | 63.8% | 10.5% | 3.5% |

Reading: the confident errors of `tool_adjusted` are almost all this one pattern. Without it the safety bar would be met at W0 and W1; with it, it is not, and the registered verdict (UNSAFE) stands because the bar was fixed before the run.
