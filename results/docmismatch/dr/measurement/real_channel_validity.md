# Real-channel-validity check (Addendum 5a)

Zero-shot sim-fitted likelihood (baseline arm's existing training buildings, zero real rows), scored against every real DEV reading (32 days, never SEALED). Day-cluster bootstrap (B=1000) lower-bound (q=0.10) class-balanced accuracy vs. chance (0.5); refuses (not validated) below min_clusters=6 or min_rows=30, exactly like `reliability.ReliabilityLayer`.

| slot | channel | validated | point bal-acc | lb bal-acc | n days | n rows | reason |
|---|---|---|---|---|---|---|---|
| vav_zone | 0 | True | 0.516 | 0.500 | 30 | 7646 | ok |
| vav_zone | 1 | True | 0.533 | 0.523 | 30 | 12442 | ok |
| vav_zone | 2 | False | 0.322 | 0.307 | 30 | 7646 | day-cluster lower-bound balanced accuracy 0.307 does not clear chance (0.5) |
| vav_sat | - | - | - | - | - | - | no sim model for this slot |
| vav_pwr | - | - | - | - | - | - | no sim model for this slot |