# Stage 1 of the work-order study (Addendum 32): does the text carry evidence?

Real records (FMUCD, CC BY 4.0), a seeded sample of 600 unplanned HVAC orders (50 per university, 12 universities). The labels were made by two Claude models and adjudicated by me: **NOT expert-verified**, and the extractor is a Claude model too, so their errors are correlated. Nothing here says anything about the routine's speed; it only says whether the text carries evidence. Descriptions are terse single records; the corpus has no room or asset ID and no separate closing note.

## Gates

| gate | result | detail |
|---|---|---|
| G1 the stream was the published file | PASS | sha256 4464648252c4... |
| G2 frozen items unchanged since the sample was drawn | PASS | fingerprint 93e16d643670... |
| G3 sample file unchanged | PASS | hashes of the two sample files |
| G4 sample size | PASS | 600 orders, 12 universities |

## Labeller agreement before adjudication

| kind | both true | agree (of 600) | kappa | labeller 1 true | labeller 2 true |
|---|---|---|---|---|---|
| A reference | 409 | 581 | 0.92 | 416 | 421 |
| B history | 14 | 583 | 0.61 | 16 | 29 |
| C mismatch | 1 | 600 | 1.0 | 1 | 1 |
| D shared | 100 | 531 | 0.67 | 158 | 111 |

## What the text carries, and who finds it

Share of orders (equal weight over universities; volume-weighted; lowest and highest university) whose reference label is true, then the keyword search's and the language model's recall and precision against the reference (the model's precision counts only confirmed statements: reference true AND the quoted words appear in the description).

| kind | share (equal) | share (volume) | lowest-highest university | reference true (of 600) | keyword recall | keyword precision | model recall | model precision | model quotes not in the text |
|---|---|---|---|---|---|---|---|---|---|
| A reference | 69.5% | 76.7% | 0.0% - 98.0% | 417 | 37.9% | 100.0% | 99.0% | 97.2% | 0 |
| B history | 3.0% | 2.7% | 0.0% - 8.0% | 18 | 33.3% | 40.0% | 77.8% | 77.8% | 0 |
| C mismatch | 0.2% | 0.1% | 0.0% - 2.0% | 1 | 0.0% | n/a | 0.0% | n/a | 0 |
| D shared | 28.0% | 31.7% | 0.0% - 48.0% | 168 | 6.5% | 91.7% | 70.8% | 97.5% | 0 |

Orders with at least one of B, C, D (reference): 30.3% equal weight, 33.5% volume weight; of those the keyword search surfaces the statement in 2.8% of all orders (equal weight).

## The frozen stop rule

| figure | value | 95% interval | threshold |
|---|---|---|---|
| LLM-only share (a confirmed B, C or D statement the keyword search misses), equal weight | 19.3% | 16.5% - 22.3% | STOP below 10% |
| same, volume-weighted | 18.0% | | (not the rule; flagged if the verdict differs) |
| lowest - highest university | 0.0% - 44.0% | | |
| model precision over B, C, D (133 confirmed of 140 statements) | 95.0% | 91.3% - 98.5% | STOP below 70% |

**Frozen decision: PASS**.
No interval straddles a threshold.
Volume weights give the same verdict on the first criterion.

**Exploratory sensitivity (declared before any output was opened; not the frozen rule).** The adjudication read D generously (an order about an air handler counts as shared equipment, although it tells the technician nothing the routine does not know). LLM-only share, equal weight, counting only some kinds:

| kinds counted | LLM-only share |
|---|---|
| B and C (history, mismatch) | 1.3% |
| B only | 1.3% |
| C only | 0.0% |
| D only (shared) | 18.2% |
| B, C, D (the frozen figure) | 19.3% |
A pass would NOT be a go for the tool: it says nothing about whether history can be tied to the right equipment (the corpus has no room or asset ID), and Stage 2 needs a real building's export and an expert.

## By university (LLM-only share, orders of 50)

| university | eligible orders | LLM-only | any B/C/D |
|---|---|---|---|
| 1 | 13992 | 12.0% | 26.0% |
| 2 | 8536 | 0.0% | 0.0% |
| 3 | 6023 | 44.0% | 48.0% |
| 4 | 14137 | 26.0% | 36.0% |
| 5 | 61487 | 12.0% | 40.0% |
| 6 | 25774 | 10.0% | 36.0% |
| 7 | 1444 | 10.0% | 20.0% |
| 8 | 15403 | 12.0% | 18.0% |
| 9 | 9886 | 28.0% | 36.0% |
| 10 | 19676 | 28.0% | 28.0% |
| 11 | 24387 | 32.0% | 44.0% |
| 12 | 77061 | 18.0% | 32.0% |
