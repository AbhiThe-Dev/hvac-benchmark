# Mixed against shipped on the first demo's setup (exploratory; FIRST_DEMO_NOTES.md hashed before any run; the first demo's files are only read)

Synthetic building, 3 handlers x 8 boxes, Room-0 and Room-1 on AHU-0, the demo's own configuration (imported from its server), simulated noisy answers. Before any check the shipped model puts 9.1% on low static at AHU-0 and mixed 11.0%.

## Gates

- G1 the replica equals `run_policy('tool_ticket_memo2')` exactly (40 visits per arm and world): **PASS**
- G2 the cases are the demo's (Room-0 and Room-1 on AHU-0, `min_rate` 0.02, 30 checks): **PASS**
- G3 answers in the check's vocabulary: asserted by the oracle

## W0

| composition | setting | accuracy per room | Room-1 (the second room) | both rooms right | minutes / visit | wrong and confident | with the hedge | rooms called confident | mixed minus shipped: accuracy (95% CI), minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| C1 shared low static | shipped | 95.5% | 96.0% | 95% | 26 | 0.0% | 0.0% | 92% |  |
| C1 shared low static | mixed | 95.5% | 96.0% | 95% | 26 | 0.0% | 0.0% | 92% | +0.0 (+0.0, +0.0); +0.0 (+0.0, +0.0) |
| C2 shared fan off | shipped | 0.0% | 0.0% | 0% | 25 | 93.0% | 46.5% | 93% |  |
| C2 shared fan off | mixed | 0.0% | 0.0% | 0% | 25 | 93.0% | 46.5% | 93% | +0.0 (+0.0, +0.0); +0.0 (+0.0, +0.0) |
| C3 independent faults | shipped | 76.5% | 80.0% | 61% | 100 | 1.0% | 1.0% | 20% |  |
| C3 independent faults | mixed | 76.5% | 80.0% | 61% | 100 | 1.0% | 1.0% | 20% | +0.0 (+0.0, +0.0); +0.0 (+0.0, +0.0) |
| C4 one shared, one own fault | shipped | 49.5% | 7.0% | 0% | 29 | 45.5% | 0.0% | 90% |  |
| C4 one shared, one own fault | mixed | 49.5% | 7.0% | 0% | 29 | 45.5% | 0.0% | 90% | +0.0 (+0.0, +0.0); +0.0 (+0.0, +0.0) |
| all four pooled | shipped | 55.4% | 45.8% | 39% | 45 | 34.9% | 11.9% | 74% |  |
| all four pooled | mixed | 55.4% | 45.8% | 39% | 45 | 34.9% | 11.9% | 74% | +0.0 (+0.0, +0.0); +0.0 (+0.0, +0.0) |

## W1

| composition | setting | accuracy per room | Room-1 (the second room) | both rooms right | minutes / visit | wrong and confident | with the hedge | rooms called confident | mixed minus shipped: accuracy (95% CI), minutes (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| C1 shared low static | shipped | 80.5% | 86.0% | 75% | 44 | 1.5% | 1.5% | 76% |  |
| C1 shared low static | mixed | 80.5% | 86.0% | 75% | 44 | 1.5% | 1.5% | 76% | +0.0 (+0.0, +0.0); +0.0 (+0.0, +0.0) |
| C2 shared fan off | shipped | 0.0% | 0.0% | 0% | 41 | 77.0% | 40.5% | 77% |  |
| C2 shared fan off | mixed | 0.0% | 0.0% | 0% | 41 | 77.0% | 40.5% | 77% | +0.0 (+0.0, +0.0); +0.0 (+0.0, +0.0) |
| C3 independent faults | shipped | 43.5% | 48.0% | 19% | 103 | 4.0% | 3.5% | 16% |  |
| C3 independent faults | mixed | 43.5% | 48.0% | 19% | 103 | 4.0% | 3.5% | 16% | +0.0 (+0.0, +0.0); +0.0 (+0.0, +0.0) |
| C4 one shared, one own fault | shipped | 44.0% | 10.0% | 0% | 40 | 40.0% | 1.0% | 76% |  |
| C4 one shared, one own fault | mixed | 44.0% | 10.0% | 0% | 40 | 40.0% | 1.0% | 76% | +0.0 (+0.0, +0.0); +0.0 (+0.0, +0.0) |
| all four pooled | shipped | 42.0% | 36.0% | 24% | 57 | 30.6% | 11.6% | 61% |  |
| all four pooled | mixed | 42.0% | 36.0% | 24% | 57 | 30.6% | 11.6% | 61% | +0.0 (+0.0, +0.0); +0.0 (+0.0, +0.0) |

## Predictions (written before any run)

- F1 (W0 pooled: mixed minus shipped per-room accuracy within +-3 points): **HELD** (+0.0)
- F2 (W0 pooled minutes within +-5%): **HELD** (+0.0 min on 45)
- F3 (W0 pooled wrong-and-confident under mixed at most 1 point above shipped): **HELD** (34.9% to 34.9%)
- F4 (W0: in no composition is mixed worse than shipped by more than 5 points): **HELD** (C1 +0.0, C2 +0.0, C3 +0.0, C4 +0.0)
- F5 (W0, C4: the own-fault room right less than 50% of the time under both settings): **HELD** (shipped 7.0%, mixed 7.0%)
