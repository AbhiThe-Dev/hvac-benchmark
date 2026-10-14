# Two suggested reliability improvements on the LBNL PFPU simulated fault set (exploratory; LEAK_SHORT_NOTES.md hashed before any value of the new rules was computed)

SIMULATED data (best case; hit rates are at most plausible upper bounds, false-alarm rates plausible lower bounds); faulted box S; the box is fan-powered, the tool targets single-duct boxes.

## Gates

- G1 the existing reheat rule's snapshot rate on stuck+leak equals the stored 0.0790: **PASS** (0.0790)
- G2 the airflow snapshot rate on the unstable loop equals the stored 0.2734: **PASS** (0.2734)

## Test 1: discharge temperature above supply temperature (more than 3 degF, no heat called, box fan off), for a leaking reheat valve

| fault | severity | existing rule, snapshot | existing rule, 24 h | discharge-temperature rule, snapshot | discharge-temperature rule, 24 h | either rule, 24 h | share of Operate minutes the leak rule can judge |
|---|---|---|---|---|---|---|---|
| reheat_valve | leak 20% | 0.00 | 0.00 | 0.15 | 0.29 | 0.29 | 88% |
| reheat_valve | leak 50% | 0.00 | 0.00 | 0.15 | 0.30 | 0.30 | 89% |
| reheat_valve | leak 80% | 0.00 | 0.00 | 0.15 | 0.30 | 0.30 | 90% |
| reheat_valve | stuck 0% | 0.51 | 0.76 | 0.00 | 0.00 | 0.76 | 48% |
| reheat_valve | stuck 100% | 0.01 | 0.12 | 0.15 | 0.30 | 0.32 | 90% |
| reheat_valve | stuck 20% | 0.07 | 0.28 | 0.13 | 0.25 | 0.36 | 85% |
| reheat_valve | stuck 50% | 0.03 | 0.19 | 0.15 | 0.30 | 0.34 | 88% |
| reheat_valve | stuck 80% | 0.01 | 0.12 | 0.15 | 0.30 | 0.32 | 89% |

| family | existing rule 24 h | discharge-temperature rule 24 h | either rule 24 h | catalogue today |
|---|---|---|---|---|
| leak (3 severities) | 0.00 | 0.30 | 0.30 | 0.75 |
| stuck (5 severities) | 0.30 | 0.23 | 0.42 | 0.75 |
| **stuck + leak (8)** | **0.19** | 0.26 | **0.37** | 0.75 |

False alarms of the discharge-temperature rule (fault-free run and the three healthy boxes of every faulted run): snapshot 0.052, 24 h window 0.102.

## Test 2: a five-minute average of the airflow miss near maximum airflow

| fault | snapshot, all minutes | snapshot at the near-maximum minutes | five-minute mean at the near-maximum minutes | five-minute mean, all minutes | 24 h window (earlier) |
|---|---|---|---|---|---|
| damper_stuck | 1.00 | 1.00 | **1.00** | 1.00 | 0.98 |
| airflow_bias | 1.00 | 1.00 | **1.00** | 1.00 | 0.98 |
| pi2_unstable | 0.27 | 0.27 | **0.14** | 0.14 | 0.84 |

False alarms of the five-minute mean at the near-maximum minutes (fault-free run and healthy boxes): 0.000; of the snapshot at the same minutes: 0.000.

## Verdicts (rule fixed beforehand)

- Test 1, discharge-temperature rule on stuck+leak, either rule against the existing rule alone: **NOT SHARPER** (0.19 to 0.37; false alarms 0.102)
- Test 2, five-minute mean on the unstable loop against the snapshot at the same minutes: **NOT SHARPER** (0.27 to 0.14; false alarms 0.000)

## Predictions (written before any value of the new rules was computed)

- L1 (leaks flagged at 0.60 or more on average, snapshot): **FAILED** (0.15)
- L2 (valves stuck at 100%, 80%, 50% flagged at 0.80 or more each; stuck at 0% at 0.05 or less): **FAILED** (0% 0.00, 100% 0.15, 20% 0.13, 50% 0.15, 80% 0.15)
- L3 (discharge-temperature rule false alarms at most 0.05, snapshot): **FAILED** (0.052)
- L4 ('either rule', 24 h, stuck+leak at 0.60 or more): **FAILED** (0.37)
- S1 (five-minute mean flags the unstable loop between 0.15 and 0.60 near maximum): **FAILED** (0.14)
- S2 (damper stuck and sensor bias stay at 0.95 or more under the five-minute mean): **HELD** (1.00, 1.00)
- S3 (five-minute mean false alarms at most 0.02): **HELD** (0.000)
