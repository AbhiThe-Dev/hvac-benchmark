# Mixed against shipped on a SECOND scenario of similar complexity (EXPLORATORY; written and hashed before any run; no new demo or UI)

## Question

On the bldg11 demo scenario the mixed setting beats the shipped one by a wide margin (84.2% against 23.8% per room on 200 demo-shaped visits with noisy answers). That scenario is close to the best case for the mixed setting: the shared rooms sit on a handler too big for the shipped model, and the two own-fault rooms sit on the healthy handler, where mixed has no folding risk. Does the win survive on another real layout and a differently drawn scenario, and what happens on the less favourable composition?

## Buildings (real Mortar layouts, recorded points only; the Brick files are not in the repository and nothing here is committed or deployed)

bldg15 (the requested second scenario): handlers of 86 boxes (58 with airflow, damper and reheat points) and 43 boxes (16 with them). bldg9 (replicate): 70 boxes (33) and 56 boxes (28). bldg11 (reference): the demo's two handlers, 49 (45) and 34 (31). Chosen from a survey of all 45 graphs as the layouts the existing builder can use with two large handlers and the full point set.

## Scenario A: demo-shaped visits (200 per building)

Six complaints, drawn like the demo script: 4 rooms on the LARGER handler with low static; on the other handler one failed actuator and one wrong documented box (the nearest-by-id alternatives, as the demo); all six boxes have airflow, damper and reheat points and the room has a temperature point (the demo's rule); arrival order shuffled. Noisy answers, W0 (checks as the tool assumes) and W1 (every rate 25% toward 0.5).

## Scenario B: the registered composition (100 visits per building)

`study_mix.draw_visit_g`: 50 shared visits (3 to 5 shared rooms on the largest handler plus random own-fault rooms anywhere) and 50 with no shared cause; the less favourable case for mixed (own-fault rooms can sit on the faulty handler).

## Arms and measures

Shipped (`JointSettings()`) and mixed (the severity mixture, 5/15/50/90% with weight 1/4), the demo's routine (`tool_ticket_memo2`), `min_rate` 0.02, T3-noattr, each building's own check list. Per room: right or wrong; per visit: all six right; minutes; wrong-and-confident (wrong and concluded); and wrong-and-confident WITH the pilot's hedge (a concluded low-static conclusion without a box-level static reading of the room's own is not confident). Paired bootstrap over visits (2000) for mixed minus shipped.

## Gates (a failed gate = NO RESULT)

G1: on bldg11 with the UNRESTRICTED room draw of `demo_composition.py` the new harness reproduces that run exactly: W0 shipped 23.8% / 332 min, mixed 84.2% / 190 min; W1 shipped 11.2% / 303, mixed 60.2% / 200 (per room, minutes per visit; 0.05). G2: every Scenario A visit has six distinct rooms, four on the larger handler (all low static), one actuator failure and one wrong box on the other handler, all with the required points. G3: every answer is in the check's vocabulary (asserted by the oracle).

## Predictions (before any run)

- P1: Scenario A, bldg15, W0: mixed beats shipped by at least 20 points per room and uses at least 20% fewer minutes.
- P2: Scenario A, bldg15, W0: the four shared rooms are at least 85% right under mixed and at most 10% under shipped.
- P3: Scenario A, bldg15, W0: the two own-fault rooms are within 5 points of each other under the two settings (no folding in this composition).
- P4: Scenario A, bldg15, W0: all six rooms right in at least 25% of visits under mixed and at most 5% under shipped.
- P5: Scenario B, bldg15, W0: mixed beats shipped by at least 10 points per room, and its wrong-and-confident share is at least 3 points higher than shipped's; with the hedge it is at most 1.5%.
- P6: the replicate (bldg9) agrees in sign with bldg15 on P1 and P5.
- P7: on the restricted draw bldg11 stays within 5 points of the unrestricted 84.2% (mixed) and 23.8% (shipped), W0.
