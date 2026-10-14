# A strong branching expert tree against the adaptive tool (Addendum 43)

Simulation only. The base world is Addendum 30's 18 cells (300 visits each); the stress worlds are 26 single-factor or combined departures from its primary cell, one event stream each. Every arm works the same visits, is answered from the same answer table, is charged the tool's own minutes by an independent-checked accountant, is held to the same 12 checks per complaint and is scored the same way. **The world is the tool's own model family with placeholder rates (home field for the tool); no real technician is involved.** Trees: E is mine (written from the guides before any run); L1 and L2 were written blind by two independent expert authors who saw the check list and its minutes and nothing about the tool or any result; I1 and I2 by two more, who were also given the tool's whole response table and the service-history base rates (so the tool and the tree know the same things).

## Gates

- **G1 neutral world: PASS.** the neutral world is exactly the existing generator and table; every mix is a proper distribution
- **G2 answer table: PASS.** answers are order-independent, equal TableOracle's in the neutral world, and a stuck sensor is a property of the visit
- **G3 trees: PASS.** 1800 random-answer visits over 5 trees x 3 tiers ran to the end; most checks on one complaint 12 (limit 12)
- **G4 fair accounting: PASS.** 2520 (arm, visit) pairs: every reported minute total equals the independent accountant's
- **G5 tool unchanged: PASS.** 72 (cell, tier, policy) arrays equal Addendum 41's stored tau-0.95 arrays exactly (over the visits run)
- **G6 events: PASS.** first 50 events of every cell match Addendum 30's stored kinds
- **G7 reproducibility: PASS.** 3 worlds reproduce exactly on a second run (one worker against many)

## The trees

| tree | nodes (as a tree) | preamble | depth | leaves | leaf kinds | distinct checks used |
|---|---|---|---|---|---|---|
| tree E (mine, confirming) | 607 | 5 | 13 | 380 | conclude:sure 92, conclude:unsure 84, escalate 164, find_feeder 40 | 26 |
| tree E (decisive form) | 487 | 5 | 12 | 300 | conclude:sure 96, escalate 164, find_feeder 40 | 26 |
| tree L1 (blind author, controls-first) | 66 | 5 | 13 | 34 | conclude:sure 27, conclude:unsure 4, escalate 2, find_feeder 1 | 27 |
| tree L2 (blind author, hands-on) | 59 | 5 | 12 | 30 | conclude:sure 20, conclude:unsure 6, escalate 3, find_feeder 1 | 25 |
| tree I2 (informed author, hands-on) | 69 | 0 | 10 | 36 | conclude:sure 13, conclude:unsure 17, escalate 4, find_feeder 2 | 21 |

## Verdicts (computed by the registered rules)

1. **Is the tree already close?** At T3-noattr, the tool has a MATERIAL advantage over a tree (at least 15% fewer minutes at no accuracy cost, or at least 5 points more accuracy at no time cost, or at least 3 points fewer declared-wrong at no time or accuracy cost; intervals excluding 0) in this many of the 18 base cells: over tree E (mine) **8: MIXED**; over EVERY blind tree (E, E-decisive, L1, L2) 0: ALREADY CLOSE; over EVERY informed tree (authors who were given the tool's whole response table and the base rates) **0: ALREADY CLOSE**; over all trees run 0: ALREADY CLOSE.
2. **Does the advantage survive stress?** Over 26 stress worlds, the tool is materially better than E in **14** (E materially better in 0): **ERODES**; better than every informed tree in **2** (some informed tree materially better in 0): **DOES NOT SURVIVE**; better than every blind tree in 0 (0): DOES NOT SURVIVE.
3. **Value, with the cost of a mistake or of an unfinished diagnosis as the unknown** (a declared-wrong complaint costs 60 to 240 minutes, an undeclared one 0 to 60; counts of cells: the tool AHEAD / the answer DEPENDS ON THE COSTS / the tool BEHIND):
   - against tree E (mine, confirming): base cells 4 / 14 / 0; stress worlds 2 / 24 / 0
   - against tree I2 (informed author, hands-on): base cells 0 / 18 / 0; stress worlds 0 / 26 / 0
4. **Registered combination:** against E, PARTIAL; against the informed trees, NOT MATERIAL.

## Registered predictions

| | held | detail |
|---|---|---|
| P1 | NO | minutes: E 63.5 against the tool's 63.7 (-0%) |
| P2 | yes | accuracy: tool 0.689, E 0.431 |
| P3 | NO | declared: E 0.551, tool 0.287 |
| P4 | yes | declared and wrong: E 0.2115, tool 0.0210 |
| P5 | NO | flat checklist 0.395 / 63 min -> E 0.431 / 63 -> tool 0.689 / 64 |
| P6 | NO | blind-tree accuracies: tree_E 0.431, tree_Ed 0.431, tree_L1 0.444, tree_L2 0.427 |
| P7 | yes | Verdict 1 against E: 8 of 18 cells with a material tool advantage (MIXED) |
| P8 | yes | tool's accuracy lead over E: primary cell +0.307, sigma-1.0 jitter worlds +0.241 |
| P9 | yes | economizer world declared-and-wrong: tool 0.0110, E 0.1295 |
| P10 | yes | value verdict against E at the registered cost box: DEPENDS ON THE COSTS in 14 of 18 cells |
| P11 | NO | the tool at min_rate 0.08, primary cell: 7.9 min / 0.517 against E's 61.8 / 0.530 |
| P12 | yes | knowledge helps a tree: best informed tree (tree_I2) 0.506, E 0.431 |
| P13 | yes | adaptivity beyond knowledge: tool 0.689, best informed tree 0.506 |
| P14 | NO | declared and wrong: best informed tree 0.1058, E 0.2115 |

## Base world, T3-noattr (control system + point map, no design data): all arms (18 cells pooled, 5400 visits)

| arm | mean min | median min | checks | accuracy (best guess, declared or not) | declared and right | declared and WRONG | not declared |
|---|---|---|---|---|---|---|---|
| adaptive tool (live) | 63.7 | 53 | 11.4 | 69% | 39% | 3.0% | 58% |
| adaptive routine | 61.1 | 52 | 11.1 | 68% | 47% | 3.6% | 50% |
| tree E (mine, confirming) | 63.5 | 47 | 10.9 | 43% | 41% | 22.8% | 37% |
| tree E (decisive form) | 58.6 | 43 | 10.5 | 43% | 44% | 33.4% | 22% |
| tree L1 (blind author, controls-first) | 40.2 | 35 | 9.0 | 44% | 44% | 31.1% | 25% |
| tree L2 (blind author, hands-on) | 60.3 | 46 | 9.5 | 43% | 47% | 21.1% | 32% |
| tree I2 (informed author, hands-on) | 47.9 | 35 | 8.4 | 51% | 28% | 10.0% | 62% |
| flat checklist (fast_parent) | 62.6 | 27 | 9.9 | 40% | 50% | 50.2% | 0% |
| no checks (prior guess) | 0.0 | 0 | 0.0 | 29% | 0% | 0.0% | 100% |

## Base world, T3 (control system + design data): all arms (18 cells pooled, 5400 visits)

| arm | mean min | median min | checks | accuracy (best guess, declared or not) | declared and right | declared and WRONG | not declared |
|---|---|---|---|---|---|---|---|
| adaptive tool (live) | 59.8 | 50 | 12.1 | 69% | 40% | 3.3% | 57% |
| adaptive routine | 55.3 | 49 | 11.5 | 68% | 47% | 3.8% | 49% |
| tree E (mine, confirming) | 61.9 | 45 | 11.2 | 45% | 41% | 22.8% | 36% |
| tree E (decisive form) | 57.2 | 42 | 10.8 | 45% | 45% | 34.6% | 20% |
| tree L1 (blind author, controls-first) | 39.3 | 33 | 9.2 | 45% | 45% | 31.8% | 23% |
| tree L2 (blind author, hands-on) | 57.1 | 44 | 9.7 | 44% | 47% | 21.1% | 32% |
| tree I2 (informed author, hands-on) | 45.6 | 33 | 8.5 | 51% | 28% | 10.0% | 62% |
| flat checklist (fast_parent) | 59.2 | 23 | 9.8 | 41% | 51% | 49.1% | 0% |
| no checks (prior guess) | 0.0 | 0 | 0.0 | 29% | 0% | 0.0% | 100% |

## Base world, T2 (no control-system access): all arms (18 cells pooled, 5400 visits)

| arm | mean min | median min | checks | accuracy (best guess, declared or not) | declared and right | declared and WRONG | not declared |
|---|---|---|---|---|---|---|---|
| adaptive tool (live) | 67.2 | 57 | 7.5 | 63% | 6% | 0.7% | 94% |
| adaptive routine | 68.8 | 59 | 7.8 | 63% | 16% | 1.6% | 83% |
| tree E (mine, confirming) | 89.9 | 72 | 9.3 | 45% | 46% | 28.4% | 26% |
| tree E (decisive form) | 89.9 | 72 | 9.3 | 45% | 50% | 36.3% | 14% |
| tree L1 (blind author, controls-first) | 61.3 | 44 | 6.2 | 45% | 35% | 17.6% | 48% |
| tree L2 (blind author, hands-on) | 72.3 | 55 | 7.2 | 48% | 52% | 20.7% | 27% |
| tree I2 (informed author, hands-on) | 86.4 | 67 | 7.4 | 52% | 29% | 8.9% | 62% |
| flat checklist (fast_parent) | 87.0 | 50 | 9.2 | 44% | 54% | 45.6% | 0% |
| no checks (prior guess) | 0.0 | 0 | 0.0 | 29% | 0% | 0.0% | 100% |

## Visit kinds (T3-noattr (control system + point map, no design data), 18 cells pooled)

| arm | single-complaint: min / accuracy / declared-wrong | several, unrelated causes | shared cause on one air handler |
|---|---|---|---|
| adaptive tool (live) | 46 / 65% / 1.6% | 107 / 63% / 2.4% | 56 / 86% / 4.0% |
| adaptive routine | 46 / 65% / 1.6% | 103 / 61% / 2.8% | 49 / 85% / 5.0% |
| tree E (mine, confirming) | 35 / 42% / 20.0% | 79 / 41% / 20.3% | 123 / 50% / 25.4% |
| tree E (decisive form) | 32 / 42% / 34.2% | 71 / 41% / 34.4% | 118 / 50% / 32.5% |
| tree L1 (blind author, controls-first) | 27 / 40% / 33.0% | 60 / 39% / 35.9% | 50 / 65% / 27.7% |
| tree L2 (blind author, hands-on) | 38 / 38% / 18.8% | 84 / 36% / 20.8% | 92 / 66% / 22.3% |
| tree I2 (informed author, hands-on) | 32 / 49% / 10.7% | 72 / 46% / 12.9% | 59 / 61% / 8.2% |
| flat checklist (fast_parent) | 45 / 35% / 65.3% | 94 / 33% / 67.4% | 71 / 63% / 34.5% |

## Tool against tree E, cell by cell (T3-noattr (control system + point map, no design data))

| world | tool min | E min | tool acc | E acc | tool vs E | material? (tool / E) | tool vs best-accuracy tree | value vs E at the registered costs |
|---|---|---|---|---|---|---|---|---|
| rare/M0/R0 | 63 | 55 | 79% | 47% | TRADE (+15% min, +31.8 pts) | - / - | tree_I2: TRADE (+35%, +18.8 pts) | DEPENDS ON THE COSTS |
| rare/M0/R1 | 63 | 47 | 52% | 33% | TRADE (+35% min, +18.9 pts) | - / - | tree_I2: TRADE (+59%, +17.7 pts) | DEPENDS ON THE COSTS |
| rare/M1/R0 | 60 | 54 | 77% | 51% | TRADE (+10% min, +26.5 pts) | - / - | tree_I2: TRADE (+29%, +16.8 pts) | DEPENDS ON THE COSTS |
| rare/M1/R1 | 64 | 46 | 54% | 35% | TRADE (+38% min, +18.9 pts) | - / - | tree_I2: TRADE (+61%, +16.2 pts) | DEPENDS ON THE COSTS |
| rare/M2/R0 | 68 | 56 | 72% | 48% | TRADE (+22% min, +24.4 pts) | - / - | tree_I2: TRADE (+28%, +13.9 pts) | DEPENDS ON THE COSTS |
| rare/M2/R1 | 68 | 52 | 50% | 29% | TRADE (+32% min, +21.0 pts) | - / - | tree_I2: TRADE (+56%, +17.9 pts) | DEPENDS ON THE COSTS |
| assumed/M0/R0 | 58 | 62 | 84% | 53% | IMPROVES (-6% min, +30.7 pts) | tool / - | tree_I2: TRADE (+23%, +15.8 pts) | DEPENDS ON THE COSTS |
| assumed/M0/R1 | 61 | 52 | 60% | 34% | TRADE (+17% min, +26.2 pts) | - / - | tree_I2: TRADE (+56%, +20.6 pts) | DEPENDS ON THE COSTS |
| assumed/M1/R0 | 60 | 63 | 81% | 53% | IMPROVES (-3% min, +28.8 pts) | tool / - | tree_I2: TRADE (+27%, +16.5 pts) | DEPENDS ON THE COSTS |
| assumed/M1/R1 | 64 | 54 | 62% | 36% | TRADE (+18% min, +26.1 pts) | - / - | tree_I2: TRADE (+47%, +23.0 pts) | DEPENDS ON THE COSTS |
| assumed/M2/R0 | 72 | 68 | 78% | 54% | IMPROVES (+6% min, +23.3 pts) | - / - | tree_I2: TRADE (+25%, +18.3 pts) | DEPENDS ON THE COSTS |
| assumed/M2/R1 | 66 | 60 | 54% | 30% | IMPROVES (+9% min, +23.5 pts) | - / - | tree_I2: TRADE (+41%, +20.1 pts) | DEPENDS ON THE COSTS |
| common/M0/R0 | 55 | 76 | 85% | 57% | IMPROVES (-28% min, +28.0 pts) | tool / - | tree_I2: TRADE (+14%, +16.5 pts) | TOOL AHEAD |
| common/M0/R1 | 61 | 75 | 69% | 40% | IMPROVES (-18% min, +28.4 pts) | tool / - | tree_I2: TRADE (+22%, +22.9 pts) | TOOL AHEAD |
| common/M1/R0 | 65 | 83 | 79% | 53% | IMPROVES (-22% min, +25.7 pts) | tool / - | tree_I2: TRADE (+22%, +17.5 pts) | DEPENDS ON THE COSTS |
| common/M1/R1 | 62 | 72 | 59% | 37% | IMPROVES (-15% min, +22.1 pts) | tool / - | tree_I2: TRADE (+31%, +15.7 pts) | TOOL AHEAD |
| common/M2/R0 | 68 | 86 | 82% | 52% | IMPROVES (-20% min, +30.0 pts) | tool / - | tree_I2: TRADE (+28%, +18.9 pts) | DEPENDS ON THE COSTS |
| common/M2/R1 | 69 | 84 | 65% | 35% | IMPROVES (-18% min, +29.2 pts) | tool / - | tree_I2: TRADE (+17%, +21.9 pts) | TOOL AHEAD |

## By fault type (T3-noattr, 18 cells pooled; per complaint)

Per true cause: how often each arm's best guess is exactly right, how often it declares a diagnosis, how often it declares a WRONG one; and, on single-complaint visits, the median minutes.

| true cause | complaints | tool_joint: right / declared / declared-wrong / median min | tree_E: right / declared / declared-wrong / median min | tree_L1: right / declared / declared-wrong / median min | tree_L2: right / declared / declared-wrong / median min | fast_parent: right / declared / declared-wrong / median min |
|---|---|---|---|---|---|---|
| low_static | 3203 | 92% / 57% / 1.4% / 50 | 47% / 75% / 27.8% / 6 | 68% / 68% / 28.9% / 6 | 66% / 86% / 26.6% / 18 | 59% / 100% / 40.7% / 30 |
| ahu_fan_off | 2506 | 85% / 79% / 4.9% / nan | 60% / 83% / 23.1% / nan | 69% / 94% / 24.8% / nan | 75% / 92% / 17.0% / nan | 82% / 100% / 17.6% / nan |
| zone_sensor_setpoint | 1310 | 86% / 58% / 2.4% / 15 | 85% / 80% / 3.7% / 15 | 70% / 88% / 17.9% / 6 | 74% / 74% / 6.6% / 17 | 62% / 100% / 38.1% / 6 |
| controller_config | 870 | 53% / 7% / 4.0% / 47 | 27% / 34% / 26.6% / 46 | 33% / 73% / 39.7% / 45 | 39% / 50% / 29.8% / 49 | 0% / 100% / 100.0% / 32 |
| flow_sensor | 770 | 77% / 20% / 2.9% / 35 | 33% / 52% / 20.5% / 22 | 45% / 78% / 33.6% / 33 | 35% / 51% / 18.6% / 46 | 48% / 100% / 52.5% / 50 |
| duct_diffuser | 614 | 64% / 23% / 2.1% / 57 | 39% / 57% / 17.8% / 35 | 38% / 69% / 32.6% / 33 | 35% / 55% / 19.7% / 49 | 31% / 100% / 69.1% / 68 |
| wrong | 595 | 41% / 35% / 4.2% / 79 | 23% / 54% / 31.1% / 50 | 0% / 42% / 41.8% / 39 | 1% / 22% / 21.3% / 44 | 19% / 100% / 81.0% / 42 |
| capacity_design | 483 | 47% / 3% / 2.9% / 48 | 0% / 29% / 28.8% / 40 | 12% / 50% / 50.3% / 41 | 0% / 30% / 30.4% / 46 | 0% / 100% / 100.0% / 32 |
| other | 464 | 39% / 5% / 5.4% / 77 | 44% / 28% / 28.0% / 36 | 0% / 39% / 38.6% / 39 | 0% / 23% / 22.8% / 44 | 12% / 100% / 87.7% / 52 |
| reheat_fail | 412 | 70% / 9% / 4.1% / 32 | 59% / 50% / 9.0% / 22 | 50% / 74% / 24.3% / 10 | 43% / 48% / 18.9% / 43 | 67% / 100% / 32.8% / 6 |
| damper_mech | 342 | 70% / 4% / 2.0% / 33 | 34% / 59% / 25.1% / 32 | 51% / 88% / 36.8% / 35 | 43% / 62% / 19.3% / 46 | 42% / 100% / 57.9% / 42 |
| actuator_fail | 316 | 63% / 2% / 1.9% / 43 | 45% / 32% / 32.3% / 40 | 35% / 84% / 58.2% / 41 | 24% / 53% / 29.1% / 46 | 0% / 100% / 100.0% / 32 |
| controller_comms | 198 | 62% / 12% / 1.5% / 30 | 13% / 27% / 14.1% / 44 | 84% / 94% / 10.6% / 4 | 83% / 68% / 7.6% / 13 | 88% / 100% / 12.1% / 4 |
| no_power | 162 | 73% / 1% / 1.2% / 31 | 14% / 44% / 30.9% / 33 | 36% / 90% / 53.1% / 21 | 33% / 60% / 27.2% / 25 | 33% / 100% / 67.3% / 8 |
| signal_fault | 116 | 59% / 3% / 2.6% / 38 | 19% / 43% / 24.1% / 34 | 36% / 85% / 49.1% / 27 | 27% / 62% / 35.3% / 41 | 31% / 100% / 69.0% / 19 |
| unlisted | 66 | 20% / 3% / 3.0% / 83 | 23% / 47% / 47.0% / 54 | 5% / 47% / 47.0% / 39 | 5% / 24% / 24.2% / 44 | 0% / 100% / 100.0% / 32 |

## Stress worlds (T3-noattr)

| world | tool: min / acc / declared-wrong / declared | E: same | best other tree: acc | tool vs E | material (tool / E) | tool better than ALL trees? | value vs E |
|---|---|---|---|---|---|---|---|
| freq: controls-heavy | 57 / 80% / 1.1% / 28% | 66 / 43% / 10.5% / 46% | tree_I2 62% | IMPROVES (-13% min, +36.4 pts) | tool / - | no | DEPENDS ON THE COSTS |
| freq: mechanical-heavy | 57 / 79% / 0.2% / 21% | 62 / 50% / 14.9% / 50% | tree_I2 61% | IMPROVES (-7% min, +29.4 pts) | tool / - | no | DEPENDS ON THE COSTS |
| freq: zone-side-heavy | 54 / 82% / 0.1% / 32% | 53 / 58% / 5.3% / 57% | tree_I2 70% | IMPROVES (+2% min, +23.9 pts) | tool / - | no | DEPENDS ON THE COSTS |
| freq: flat (every cause equally likely) | 58 / 77% / 0.7% / 21% | 61 / 40% / 14.9% / 47% | tree_L1 58% | IMPROVES (-4% min, +36.7 pts) | tool / - | no | DEPENDS ON THE COSTS |
| freq: rare causes heavy | 69 / 76% / 0.4% / 23% | 63 / 49% / 14.7% / 43% | tree_I2 69% | TRADE (+10% min, +26.9 pts) | - / - | no | DEPENDS ON THE COSTS |
| freq: drawings poor (30% of boxes wrong) | 71 / 76% / 0.8% / 31% | 68 / 47% / 18.1% / 55% | tree_I2 57% | IMPROVES (+5% min, +29.3 pts) | tool / - | no | DEPENDS ON THE COSTS |
| noise: control-system reads 0.3 | 62 / 72% / 0.9% / 25% | 58 / 38% / 16.8% / 49% | tree_I2 45% | IMPROVES (+7% min, +34.7 pts) | - / - | no | DEPENDS ON THE COSTS |
| noise: control-system reads 0.6 | 62 / 63% / 2.5% / 21% | 58 / 25% / 22.6% / 43% | tree_I2 30% | IMPROVES (+7% min, +38.3 pts) | - / - | no | DEPENDS ON THE COSTS |
| noise: field measurements 0.3 | 62 / 59% / 2.8% / 29% | 53 / 45% / 25.3% / 60% | tree_I2 49% | TRADE (+16% min, +14.1 pts) | - / - | no | DEPENDS ON THE COSTS |
| noise: AHU static sensor stuck in 25% of visits | 59 / 79% / 0.5% / 32% | 75 / 48% / 12.8% / 51% | tree_I2 57% | IMPROVES (-21% min, +30.5 pts) | tool / - | no | TOOL AHEAD |
| reliability: every check 0.5 toward a coin flip | 56 / 40% / 10.7% / 25% | 48 / 25% / 44.5% / 63% | tree_I2 26% | TRADE (+17% min, +15.1 pts) | - / - | no | DEPENDS ON THE COSTS |
| reliability: false alarms x3 | 58 / 69% / 1.7% / 26% | 53 / 39% / 27.1% / 60% | tree_I2 50% | IMPROVES (+10% min, +29.8 pts) | - / - | no | DEPENDS ON THE COSTS |
| reliability: hits 40% weaker | 84 / 49% / 0.6% / 17% | 89 / 28% / 13.0% / 31% | tree_L1 36% | IMPROVES (-6% min, +21.3 pts) | tool / - | no | TOOL AHEAD |
| reliability: checks sharper than assumed (0.5) | 57 / 90% / 0.5% / 34% | 56 / 62% / 4.3% / 53% | tree_I2 80% | IMPROVES (+1% min, +27.7 pts) | tool / - | no | DEPENDS ON THE COSTS |
| reliability: every check deterministic (ceiling) | 50 / 94% / 0.1% / 47% | 44 / 76% / 0.6% / 66% | tree_I2 91% | TRADE (+14% min, +18.3 pts) | - / - | no | DEPENDS ON THE COSTS |
| mismatch: response table jittered, sigma 0.5 (A) | 57 / 77% / 1.0% / 29% | 58 / 49% / 14.2% / 55% | tree_I2 62% | IMPROVES (-2% min, +27.7 pts) | tool / - | no | DEPENDS ON THE COSTS |
| mismatch: response table jittered, sigma 0.5 (B) | 60 / 81% / 0.6% / 34% | 60 / 57% / 13.1% / 54% | tree_I2 63% | IMPROVES (+0% min, +24.0 pts) | tool / - | no | DEPENDS ON THE COSTS |
| mismatch: response table jittered, sigma 1.0 (A) | 55 / 70% / 0.9% / 27% | 52 / 46% / 18.0% / 56% | tree_I2 59% | IMPROVES (+7% min, +24.6 pts) | - / - | no | DEPENDS ON THE COSTS |
| mismatch: response table jittered, sigma 1.0 (B) | 61 / 83% / 0.1% / 29% | 60 / 59% / 10.9% / 47% | tree_Ed 59% | IMPROVES (+1% min, +23.5 pts) | tool / - | no | DEPENDS ON THE COSTS |
| mismatch: 10% of signatures lost or invented (A) | 62 / 71% / 1.7% / 32% | 55 / 45% / 15.3% / 54% | tree_I2 50% | TRADE (+13% min, +25.3 pts) | - / - | no | DEPENDS ON THE COSTS |
| mismatch: 10% of signatures lost or invented (B) | 62 / 73% / 0.7% / 30% | 53 / 45% / 15.4% / 52% | tree_I2 55% | TRADE (+16% min, +28.1 pts) | - / - | no | DEPENDS ON THE COSTS |
| mismatch: an economizer fault neither system knows | 60 / 71% / 1.1% / 30% | 71 / 47% / 13.0% / 52% | tree_I2 57% | IMPROVES (-14% min, +24.1 pts) | tool / - | no | DEPENDS ON THE COSTS |
| tool setting: believes upstream faults are 10x commoner | 60 / 79% / 0.0% / 28% | 60 / 52% / 15.0% / 57% | tree_I2 62% | IMPROVES (+1% min, +27.5 pts) | tool / - | no | DEPENDS ON THE COSTS |
| tool setting: believes upstream faults are 10x rarer | 56 / 79% / 1.3% / 32% | 62 / 51% / 13.9% / 54% | tree_I2 61% | IMPROVES (-9% min, +27.7 pts) | tool / - | no | DEPENDS ON THE COSTS |
| tool setting: drawings rated poor (world: 5% wrong) | 64 / 79% / 0.5% / 36% | 60 / 51% / 14.3% / 54% | tree_I2 64% | IMPROVES (+7% min, +27.8 pts) | - / - | no | DEPENDS ON THE COSTS |
| combined: a bad day | 60 / 52% / 3.8% / 27% | 50 / 33% / 30.8% / 58% | tree_I2 38% | TRADE (+20% min, +18.5 pts) | - / - | no | DEPENDS ON THE COSTS |

By group (T3-noattr; material advantage counted by the registered bars):

| group | worlds | tool materially better than E | E materially better than the tool | tool better than every tree |
|---|---|---|---|---|
| frequency | 6 | 5 | 0 | 0 |
| noise | 4 | 1 | 0 | 0 |
| reliability | 5 | 2 | 0 | 0 |
| mismatch | 7 | 4 | 0 | 0 |
| tool | 3 | 2 | 0 | 0 |
| combined | 1 | 0 | 0 | 0 |

## Stress worlds at T3 (control system + design data): tool against E (counts of the 26 worlds)

Tool materially better than E: 17; E materially better than the tool: 0; tool better than every tree: 0; and over the 18 base cells: 10 / 0 / 0.

## Stress worlds at T2 (no control-system access): tool against E (counts of the 26 worlds)

Tool materially better than E: 26; E materially better than the tool: 0; tool better than every tree: 3; and over the 18 base cells: 16 / 0 / 5.

## The tool's own speed-accuracy frontier against the trees (T3-noattr, Addendum 30's primary cell)

| arm | mean min | accuracy | declared-wrong | declared |
|---|---|---|---|---|
| tool@mr0.08 | 7.9 | 52% | 0.0% | 1% |
| tool@mr0.04 | 20.7 | 65% | 0.1% | 4% |
| tree L1 (blind author, controls-first) | 42.2 | 58% | 19.5% | 72% |
| tree I2 (informed author, hands-on) | 47.3 | 68% | 3.1% | 47% |
| tree E (decisive form) | 57.4 | 53% | 21.0% | 71% |
| tool@tau0.90 | 57.8 | 84% | 1.2% | 43% |
| adaptive tool (live) | 58.3 | 84% | 0.4% | 31% |
| tree E (mine, confirming) | 61.8 | 53% | 15.3% | 58% |
| tree L2 (blind author, hands-on) | 62.3 | 56% | 13.4% | 63% |
| tool@mr0.01 | 70.4 | 86% | 0.5% | 41% |
| flat checklist (fast_parent) | 81.1 | 50% | 50.4% | 100% |
| tool@mr0.003 | 86.9 | 86% | 0.5% | 55% |

## What the tool's lead is worth (T3-noattr (control system + point map, no design data), base world)

Mean minutes-equivalent the tool saves per visit against the tree (negative = the tree is cheaper), averaged over the cells; rows: the cost of a declared-wrong complaint; columns: the cost of a complaint left undeclared (minutes).

| declared-wrong cost \ undeclared cost | 0 | 15 | 30 | 60 |
|---|---|---|---|---|
| 0 | -0.2 | -7.5 | -14.8 | -29.4 |
| 30 | +13.4 | +6.2 | -1.1 | -15.7 |
| 60 | +27.1 | +19.8 | +12.5 | -2.0 |
| 120 | +54.4 | +47.1 | +39.9 | +25.3 |
| 240 | +109.1 | +101.8 | +94.5 | +79.9 |
| 480 | +218.4 | +211.1 | +203.8 | +189.2 |

Break-even cost of a declared-wrong complaint (minutes; the tool is cheaper above it only if the tree declares more wrong ones than the tool): undeclared 0: 6, undeclared 15: 24, undeclared 30: 42, undeclared 60: 79

Minutes per visit the tool saves against tree E in the base world: **-0.2** (mean 63.7 against 63.5); per complaint -0.1. Illustration only, at assumed loaded technician costs (replace with your own): $60/h: $-0 per visit, $-225 per 1000 visits; $100/h: $-0 per visit, $-375 per 1000 visits; $150/h: $-1 per visit, $-563 per 1000 visits. A negative number means the tool is SLOWER than the tree in minutes; the case for the tool then rests on declared-wrong and undeclared complaints (value table above).

## Files

- report: `report.md`
- summary: `summary.json`
- base worlds by tier, arm, visit kind: `cells.csv`
- stress worlds: `stress.csv`
- hashes of code, tests and trees before the run: `FROZEN.sha256`
- raw per-visit arrays: `raw.pkl`
- the trees: `doc_mismatch/expert_trees/ (L1, L2 as returned, with the authors' notes; E is generated by tree.tree_E)`
