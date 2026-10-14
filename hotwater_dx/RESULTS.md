# Step 1 results (physics-model output, not field evidence)

Full detail: `PREREGISTRATION.md` (rules, predictions, scorecard) and `output/` (regenerate with `uv run python scripts/02_build_matrix.py`).

- 17 causes x 23 checks = 391 cells: **26 deterministic (seen), 252 deterministic (not seen), 54 parameter-dependent, 59 needs-elicitation.**
- 6 of 9 pre-registered predictions hold; 3 fail or partly fail (crossover x K18, balancing-valve x K06, and no seeded two-fault interaction showed masking).
- The single biggest unknown is **how often the recirculation pump is actually running when a technician arrives** (`duty` drives 47 of 113 uncertain cells). Flow-dependent checks should be done with the pump forced on (exploratory Addendum 2).
- Cause pairs no single check separates: balancing vs isolation valve; check valve vs insulation loss; heater set point low vs dip tube; dip tube vs TMV set; heater output loss vs dip tube.
- Three causes almost never produce the symptom in the model (pump under-sized, insulation loss, cold-side pressure), so their rows are less informative.
- Interview list: `output/uncertain_cells.csv` (120 rows, source conflicts first). Parameters that matter most for interviews: `duty`, `t_set_tmv`, `valve_thermal`.
- Limits: `output/model_limits.md`. The model's loop heat loss runs high against the field mean (median ~85 W/apartment vs 62.5), one plant archetype, steady state only, severity ranges are analyst estimates, and no cause priors exist.

## Engine and stress test (Addendum 3, simulation only)

- Engine = information-per-minute check selection (with travel time), 17 single causes + 11 seeded pairs + "other", stops at 0.90 posterior or when nothing is worth its time.
- Matched world: top-1 0.76, 6.3 checks, 41 min, wrong-and-confident 2.7%. Fixed-order flowchart: top-1 0.59, 10 checks, 90 min. In-model ceiling (all checks): 0.78.
- It is confident in only 43% of visits (right 94% of those); the rest it ends with a best guess.
- Under a composite mismatch (shifted parameters, milder faults, hidden crossover, 2x instrument error, 10% skipped and 10% wrong readings) top-1 falls to 0.44 and wrong-and-confident rises to 12.7%. The robust variant B holds it to 3.6% by being confident less often (16%).
- 4 of 6 pre-registered predictions hold; the two that fail (pair hypotheses' effect on "hit" score; size of the degradation) are in PREREGISTRATION.md.
- This says nothing about real buildings. Next: sensitivity analysis on the uncertain cells, then interviews.

## Sensitivity analysis (Addendum 4, simulation only; Addendum 5 exploratory)

- 3 of 7 pre-registered predictions hold (tool tiers, value of knowing cause frequencies, "nothing matters inside the fitted ranges", which is weak). 4 fail (duty is not the top parameter; check-time beliefs matter slightly; Q1 is the costliest check to lose; no setting gives both few confident errors and many confident calls).
- **Knowing how often each cause occurs is the most valuable single input** (CORRECTED 2026-10-10: the original +0.095 / -0.006 figures were biased by giving zero prior to causes absent from the test visits; correct values are about +0.05 for an oracle prior and about -0.04 for a wrong one, and the Addendum 11 curve shows a prior of unknown quality is expected to hurt). As originally written: an oracle case-mix prior gives +0.095 top-1 and about 11 fewer minutes; a wrong prior costs about nothing on average but up to -0.054.
- **Instruments:** questions and eyes only 0.41 top-1; plus thermometer checks 0.60; plus clamp meter and gauges 0.74; plus valve and isolation tests 0.76. The logger adds nothing in this model because it has no time-of-day behaviour.
- **The zero-cost questions are the most valuable checks** (removing "which floors are affected" costs 0.06 and doubles confident errors) - but the model treats tenant reports as 85% reliable, which is a guess.
- **Inside the fitted ranges no single parameter matters; beyond them 13 of 44 do** (exploratory): low cold-side pressure, an under-sized pump, long dead legs, TMV set points outside 120-130 F, long piping, rarely-running pumps. The engine reads absolute values, so facts the technician can read on arrival (set points, dead-leg length, pump rating, static pressure) should be collected and conditioned on.
- Default stopping settings (0.90 bar, 0.02 bits/min) sit near the knee of the trade-off; the frontier is in `output/ENGINE_SENSITIVITY_REPORT.md`.

## Adversarial search (Addendum 6, simulation only)

- Idea: treat the simulator as an adversary. Drew plants from a broad plausible family (every parameter extended half a range beyond its fitted range) with per-visit instrument error, skipped and misread checks, and hidden crossover; mined where the engine is confidently wrong; tested two fixes on fresh worlds.
- **Honest headline for the plain engine on that family: top-1 0.51 and confidently wrong 13.6% of visits (matched world 0.76 and 2.7%). `B_robust`: 0.58 and 2.9%.**
- Failures are spread across the family: no compact failure box (14 features for 1.1x the average rate). The strongest driver by far is low cold-side static pressure, then TMV margin and set point, pipe length, dead leg, pump head; all five top drivers were already flagged by the one-at-a-time sweep.
- **No improvement over `B_robust`.** Refitting the likelihoods on the family (R_A) ties B on accuracy and confident errors and is better calibrated (ECE 0.075 against 0.142); the safer R_B is confident half as often and loses 0.05 matched top-1. The arrival-fact guard never switched on (no knowable pocket was much worse). 6 of 9 pre-registered predictions hold (P2, P3, P4, P7, P8, P9); P1, P5 and P6 fail.
- Untested follow-up: condition the likelihoods on `p_cold` (and maybe TMV margin and set point). Everything is within this simulator; structural mismatch is invisible to it.

## Conditioning on facts read at the door (Addendum 7, simulation only)

- Idea: instead of widening likelihoods, make each reading's expected value depend on facts a technician can read on arrival (static pressure, set points, dead-leg length, etc.). A ladder: no facts, 1 fact, 3, 15, and an oracle that knows all 25 plant parameters.
- **No improvement over `B_robust`; 1 of 8 pre-registered predictions holds** (extrapolation). With clean facts, 15 facts add +0.022 top-1 (oracle: +0.047) but raise the confident-error rate (0.070 against 0.038 unconditioned). With realistic fact entry (noisy, missing, 5% wrong) the conditioned engine is *worse than using no facts* (top-1 0.548 against 0.590; confidently wrong 10.6%).
- **The oracle ceiling is small**: even knowing every plant parameter lifts the family top-1 from 0.59 to only 0.64 (matched world: 0.76). Most of the family's gap is per-visit trouble and plants that already complain when healthy, not parameter shifts. Caveat: linear-plus-quadratic regression; a physics-based oracle could show more and was not run.
- Cold-side static pressure carries most of what there is; one fact (`p_cold`) gives +0.016 top-1, more than three facts do.
- Together with Addendum 6: widening ties `B_robust`, conditioning does not beat it, and the guard found nothing to switch on. In simulation, `B_robust` is hard to improve on with the information the model has; the next gains are more likely to come from outside the simulator.

## Tenant answers as soft evidence (Addendum 8, simulation only)

- Tenant answers (Q1-Q3) were modelled as a guess of 15% off-by-one. Dialling the chance that an answer is unrelated to the plant from 0 to 70%: the engine that trusts them loses 0.24 top-1 and goes from 3% to 20% confident errors on matched worlds; never asking ties it at 15% and beats it from 30%. **Trusting tenant answers only pays if about 85% or more are informative.** Asking is still worth about 20 minutes per visit when tenants are reliable.
- **Soft evidence works**: letting a tenant answer be wrong with probability 0.3 (a mixture with the broad "other" hypothesis; physical readings unchanged) removes almost all of that loss (top-1 0.729 against 0.576 at p = 0.50, confident errors 0.054 against 0.147) and costs nothing in accuracy when tenants are reliable.
- **`B_robust` is not robust to tenant error** (confident errors 0.006 at p = 0, 0.053 at p = 0.50). By the frozen rule, **`S30_B` (B's settings plus soft tenant evidence) is now the recommended variant**: a tie with B for reliable tenants, +0.03 to +0.15 top-1 and 0.015 to 0.06 fewer confident errors as tenants degrade, at a cost of 6-9 more minutes per visit.
- 5 of 7 pre-registered predictions hold (T1 fails: asking is worth +0.043 top-1, not +0.08; T7 fails: B is not robust to tenants).
- The test's error form (random unrelated answers) matches the mixture by construction; consistent over-reporting was not tested and is the real next check. Real tenant reliability is unknown.

## What manufacturers' own documents say (Addendum 9, documents not simulation)

- 157 scored statements from 25 manufacturers (A. O. Smith, Bradford White, PVI, Lochinvar, Rheem, Triangle Tube, Amtrol, Powers/Watts, Bradley, Symmons, Leonard, Lawler, Caleffi, Taco, Grundfos, Armstrong, Bell & Gossett, Resideo, Kemper and others), read by four independent readers; a 39-row blind verification found **no fabricated statements** but 7 of 31 readable rows partly overstated, and the pump-and-valve class (35 of 44 rows came from PDFs read via an unauthorised proxy) is essentially unverified.
- **5 of 9 pre-registered predictions hold.** 75% of statements map onto our 17 causes. The matrix sees 39% of the (cause, check) pairs the documents name, but 9 of the 14 misses are one cluster: manufacturers' number one mixing-valve check is hot-supply *margin* (heater outlet minus valve set point); our catalogue reads heater outlet alone.
- **Taxonomy gaps worth considering** (none applied): finer TMV failure modes (operation below minimum flow, creep or droop from the return arrangement, failed thermal element, hot inlet not closing), indirect-tank primary-side problems, over-temperature and thermal-expansion complaints, and a long list of component-level electrical and control tests.
- **Nothing changes in the model or the engine from this**; each change would need its own pre-registered rerun, and a rerun measures internal consistency, not agreement with buildings. The practical value is a sourced list of what real manufacturers tell technicians to look at.
- Not done: reading the 43 PDFs the fetch tool cached (79 MB in its tool-results folder; not opened), a legal review of the documents' terms, and any independent read of the pump-class rows.

## Unmodelled causes and weak priors (Addenda 10 and 11, simulation)

- **Unmodelled causes are mostly an abstention and time problem, not a confident-error problem, for the recommended engine.** With the true cause removed from its list, S30_B commits to a wrong family in 0.6% of visits and abstains in 78% (plain engine A: 9.9% and 50%); the cost is about 67 minutes against 54. The two manufacturer-sourced mixing-valve modes are likewise not a confident-error risk (0%); adding them costs nothing on ordinary visits (top-1 0.749 against 0.752). 5 of 8 predictions held, three of them the "problem is small" ones failing. Nothing was changed in the engine.
- **A prior of unknown quality is expected to hurt.** An unrelated prior costs 0.09 to 0.26 top-1; a prior pays only when almost exactly right (break-even rho about 0.75 to 1; about 0 to 0.9 if shrunk by half). Independent weak sources do not agree (manufacturer emphasis against language-model recall: Spearman -0.09), so **no sourced prior was built; uniform stays.** 2 of 9 predictions held.
- **Correction:** Addendum 4's prior result was biased (see above); the value of knowing cause frequencies is about +0.05 top-1, not +0.095, and a wrong prior costs about 0.04, not nothing.
- Net: neither idea raised simulated accuracy; one closed off an idea (public-source priors) and one corrected an earlier number. The remaining levers need real data.
