# Does the routine still capture it once the shared cause rarely makes several rooms complain together? (Addendum 37)

Adds `causes.ECON_FAULT` ("the economizer is not delivering the free cooling it should") as a third upstream state, additively: every function this touches (`state_prior`, `ahu_row`, `bears_on_ahu`, the J-table, `draw_event`) is a no-op with no extra state requested (gate G1), so no other addendum's stored results are affected by this file existing. Simulation only, the model's own family, every number a placeholder; nothing here is evidence about real buildings or technicians. ONE cell (Addendum 30's primary shared/map/reliability levels), both tiers, not the full 18-cell sweep.

## Gates

| gate | result | detail |
|---|---|---|
| G1 the extension is additive | PASS | tool_joint/tool_ticket_memo vs Addendum 30's stored results: events differ in cells []; 14400 re-run Addendum 30 episodes: 0 differ |
| G2 probabilities are consistent | PASS | a prior with econ_fault enrolled sums to 1 and gives it positive mass: True; the f-split sums to f: True |
| G3 replay | PASS | 0 of 40 replays differ |
| G4 reproducibility | PASS | 0 policy/tier series differ in the first 30 events |
| G5 completeness | PASS | 1000 events, 4 policy/tier series |

## The cell (n=1000 events per tier): minutes / checks / share of complaints correct / wrong-and-confident

**all events**

| tier | policy | minutes | checks | accuracy | wrong-and-confident |
|---|---|---|---|---|---|
| T2 | tool_ticket_memo2 | 119.6 | 11.9 | 77.4% | 1.7% |
| T2 | tool_joint2 | 129.5 | 12.1 | 79.2% | 1.2% |
| T3 | tool_ticket_memo2 | 66.0 | 13.1 | 79.7% | 2.7% |
| T3 | tool_joint2 | 77.4 | 14.2 | 81.5% | 2.2% |

**shared-cause events (any upstream cause)**

| tier | policy | minutes | checks | accuracy | wrong-and-confident |
|---|---|---|---|---|---|
| T2 | tool_ticket_memo2 | 128.5 | 11.2 | 89.4% | 2.5% |
| T2 | tool_joint2 | 148.7 | 12.0 | 93.4% | 1.8% |
| T3 | tool_ticket_memo2 | 57.6 | 11.0 | 90.5% | 4.8% |
| T3 | tool_joint2 | 95.3 | 15.0 | 95.0% | 3.3% |

**econ_fault-shared events (2+ complaints, same air handler, econ_fault)**

| tier | policy | minutes | checks | accuracy | wrong-and-confident |
|---|---|---|---|---|---|
| T2 | tool_ticket_memo2 | 206.4 | 20.6 | 81.9% | 6.4% |
| T2 | tool_joint2 | 208.9 | 19.8 | 90.4% | 0.0% |
| T3 | tool_ticket_memo2 | 98.4 | 20.6 | 76.9% | 6.4% |
| T3 | tool_joint2 | 160.2 | 27.4 | 98.8% | 2.1% |

## Complaints whose true cause is `econ_fault`: share correctly named, and wrong-and-confident

| tier | policy | econ complaints | correctly named | wrong-and-confident |
|---|---|---|---|---|
| T2 | tool_ticket_memo2 | 51 | 78.4% | 5.9% |
| T2 | tool_joint2 | 51 | 88.2% | 0.0% |
| T3 | tool_ticket_memo2 | 51 | 74.5% | 5.9% |
| T3 | tool_joint2 | 51 | 90.2% | 0.0% |

Reference (a separate, fresh 2-state world, no econ_fault): the routine's/joint's own wrong-and-confident rate on `low_static`-caused complaints, which P4 compares `econ_fault`'s rate against -- T2/tool_ticket_memo2 1.6%, T2/tool_joint2 1.4%, T3/tool_ticket_memo2 1.4%, T3/tool_joint2 1.2%.

`econ_fault`-shared events in this cell: 16 of 1000.

## Predictions (written before any code existed; each strict)

| prediction | holds | detail |
|---|---|---|
| P1 additive (gate) | holds | tool_joint/tool_ticket_memo vs Addendum 30's stored results: events differ in cells []; 14400 re-run Addendum 30 episodes: 0 differ |
| P2 diagnosable at T2 (>=70% correct on econ-caused complaints) | holds | econ_accuracy=0.78 on 51 complaints |
| P2 diagnosable at T3 (>=70% correct on econ-caused complaints) | holds | econ_accuracy=0.75 on 51 complaints |
| P3 the routine at T2 (<=130% of joint2's minutes on econ-shared visits) | holds | routine/joint2 minutes = 0.99 (206 / 209 min, n=16) |
| P3 the routine at T3 (<=130% of joint2's minutes on econ-shared visits) | holds | routine/joint2 minutes = 0.61 (98 / 160 min, n=16) |
| P4 safety at T2 (econ wrong-and-confident <= low_static's + 2 points) | does not hold | econ=0.059, low_static reference=0.016 |
| P4 safety at T3 (econ wrong-and-confident <= low_static's + 2 points) | does not hold | econ=0.059, low_static reference=0.014 |

## Frozen decision: UNSAFE

Run time 1287 s.
