# Where do the errors come from, and what would a new measurement have to do? (EXPLORATORY; written and hashed before any analysis)

## Question

The 151 wrong rooms of the registered 100 visits (mixed setting, W0) are mostly "ordinary" own-fault rooms (75) and folded rooms (51). For each wrong room: was a check that could have told the truth from the tool's wrong answer missing from the catalogue, available but not taken, taken but misleading, or taken and mixed? And how much would one NEW check, specific to the most-confused pair, be worth?

## Part 1: sorting every error (W0 and W1; the same visits, the demo's mixed setting, `min_rate` 0.02, T3-noattr; no engine change)

Per wrong room: the true cause T, the tool's leading cause G, and the observations in the room's session (including the zero-minute copies from earlier tickets). For a pair of ordinary causes (neither is "documented box wrong" nor "unlisted") the DISCRIMINABILITY of a check c is the Jeffreys divergence between its two response rates, J_c = (pT - pG) ln( pT (1 - pG) / (pG (1 - pT)) ), rates clipped as the engine does, over the 28 checks of the demo's list. A check is DISCRIMINATING when J_c >= 0.25 (about "good" against "partial" or better). Each error goes into exactly one bucket:

1. **gap**: no check in the list is discriminating for (T, G);
2. **not taken**: at least one discriminating check exists, none was taken in this room;
3. **misled**: discriminating checks were taken, and every one of them answered in the direction that favours G over T (its answer likelihood ratio P(answer | T) / P(answer | G) below 1);
4. **mixed**: at least one taken discriminating check favoured T and the room was still wrong;
5. **box-identity**: T or G is "documented box wrong" or "unlisted" (not analysed with J; counted).

Counts are reported for all wrong rooms and by segment (own fault with no shared cause; own fault on the faulty handler = folding; own fault on the healthy handler; shared-cause rooms). **Symptom clusters**: a room's signature is the set of checks that came back abnormal / yes; the report ranks signatures by number of errors and shows which truths and guesses sit inside. **Ceilings**: accuracy if every error of one bucket were turned right (base accuracy + bucket count / 600).

## Part 2: what a new, specific check would be worth

For the five most-confused ordinary pairs (counted among own-fault rooms with no shared cause; pairs involving low static are excluded, since folding is its own problem), add ONE hypothetical check per pair to the catalogue: it fires (answers abnormal) with probability 0.80 when the cause is A, the cause that is the truth more often among that pair's errors, and with probability 0.08 for every other cause, including B; no data needed, 3 minutes ("cheap", place control system); sensitivity at 10 minutes (physical, 6 + 4). The simulated world uses the same rates (home field by design: this measures the value of the measurement, not whether such a check exists). Arms: base; each single new check; all five together. Same 100 visits, W0 and W1, paired bootstrap against base.

## Gates (a failed gate = NO RESULT)

G1: the base run equals the stored 74.83% / 54.67% and 193.7 / 204.8 minutes. G2: the number of wrong rooms by segment at W0 matches the earlier decomposition (75 / 51 / 10 / 15). G3: buckets are exhaustive and exclusive (they sum to the number of wrong rooms).

## Predictions (before any analysis)

- E1: among the ordinary errors (own fault, no shared cause) that are not box-identity, "not taken" is the largest bucket, at least 40%, and "gap" is at most 20%.
- E2: "gap" errors are at most 25% of all wrong rooms.
- E3: the five most common symptom signatures account for at most 50% of the ordinary errors.
- E4: one hypothetical specific check for the most-confused pair raises W0 accuracy by at most 1.5 points.
- E5: all five together raise W0 accuracy by 2 to 6 points and stay below 85%.
- E6: the ceiling for fixing every "gap" error is at most 4 points.
- E7: the folded rooms (own fault on the faulty handler) fall mostly in "not taken" (at least 60% of them).
