# Mixed against shipped on the FIRST demo's setup (EXPLORATORY; written and hashed before any run; the first demo's files are read, never modified)

## The first demo (`../live_demo`, port 8743)

A synthetic building (`examples/troubleshoot_example/building_v2.json`: 3 air handlers x 8 boxes, 24 rooms); two complaints, Room-0 and Room-1, both on AHU-0; the technician answers every check (no scripted scenario); the shipped joint model (`JointSettings()`), the routine `tool_ticket_memo2`, T3-noattr, `min_rate` 0.02, no economizer cause.
Before any check (plumbing, read before this note): shipped puts 9.1% on low static at AHU-0, mixed 11.0%. On a handler this small the two settings start almost the same.

## Test (simulated answers, since the demo has no script)

The demo's own configuration is taken from `../live_demo/server.py` (`build_cases()`, imported read-only), so the setup is exactly the demo's. Two-room visits, Room-0 then Room-1, four compositions of 100 visits each (400 in all):

- C1 shared low static: both rooms low static (AHU-0 low static);
- C2 shared fan off: both rooms fan off (AHU-0 fan off);
- C3 independent: both rooms have their own faults (the registered draw: 11 local causes equally likely, 10% documented box wrong, of which 10% unlisted);
- C4 one shared, one own: Room-0 low static, Room-1 its own fault (AHU-0 low static): the folding composition.

Noisy answers, W0 (checks as the tool assumes) and W1 (every rate 25% toward 0.5); shipped (`JointSettings()`) and mixed (5/15/50/90% with weight 1/4). The demo's 30-check list. Measures: per-room accuracy, both rooms right, minutes per visit, wrong-and-confident (wrong and concluded), and with the pilot's hedge (a concluded low-static conclusion with no box-level static reading of the room's own is not confident). Paired bootstrap over visits (2000), mixed minus shipped.

## Gates (a failed gate = NO RESULT)

G1: the replica of the routine equals `run_policy("tool_ticket_memo2")` exactly (guesses, conclusions, minutes) on 40 visits per arm and world. G2: the cases built from the demo's `build_cases()` are Room-0 and Room-1 on AHU-0, `min_rate` 0.02, 30 checks. G3: answers in the check's vocabulary (asserted by the oracle).

## Predictions (before any run)

- F1: W0, all four compositions pooled: mixed minus shipped per-room accuracy within +-3 points.
- F2: W0, pooled minutes per visit within +-5%.
- F3: W0, pooled wrong-and-confident under mixed not more than 1 point above shipped's.
- F4: W0: in no single composition is mixed worse than shipped by more than 5 points per room.
- F5: W0, C4: the own-fault room (Room-1) is right less than 50% of the time under BOTH settings (the folding problem exists in the first demo too).
