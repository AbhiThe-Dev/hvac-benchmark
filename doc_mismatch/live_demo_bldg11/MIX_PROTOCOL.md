# Severity-mixture model for shared faults: does it raise accuracy on any building without costing time? (protocol, written 2026-10-11 BEFORE any mixture result exists)

**The change under test (already in `troubleshoot/v2/joint.py`, off by default).** The shipped joint model assumes that a room on a low-static air handler complains with probability
`r_low = 0.5`, and counts every SILENT room of that handler as evidence against a shared fault. On a big handler with a few complaints that makes the shared fault effectively impossible (prior
about 5e-11 for 4 complaints among 49 rooms; about 0.2% for 4 among 24). `JointSettings(low_mix=...)` replaces the single `r_low` by a mixture over how many rooms the fault starves: four levels
`r` in (0.05, 0.15, 0.5, 0.9), weight 0.25 each (`MIX`), each a separate state sharing low static's checks and cause; the data pick the level. No number is tuned to a building. The levels 0.5
and 0.9 are the shipped `r_low` and `r_fan`; 0.05 and 0.15 were chosen after seeing that any single `r_low` from 0.02 to 0.2 fixed the bldg11 demo scenario.

**Why this and not the other levers.** Only changes that add no checking time are built: this one (it also removes the cost of checking every room of a big handler separately) and a short-list
presentation. The folding fix adds time, and the data-dependent levers (recalibration, new checks) need real outcomes; neither is built here, so **the safety problem of the folding remains and this
study is not expected to fix it**.

**What this is and is not.** Simulation. Layouts and point maps are real (Mortar); faults, answers and minutes are simulated and placeholders; worlds are drawn from the tool's own model family
(home-field). Nothing here is evidence about real buildings or technicians, and no default of the tool or the CLI is changed.

**What has been seen before writing this (disclosure).** The registered 100-visit bldg11 run (`SIM_PROTOCOL.md`, results in `results/docmismatch/bldg11_sim/`) and its exploratory breakdowns: shipped
50.7% / 32.8% accuracy (W0 / W1), `r_low` 0.10 74.7% / 55.3%, wrong-and-confident 7.5% / 10.5% (the folding), and a sweep of `r_low` on the one scripted visit. So the bldg11 arm (S2) is NOT
independent of what shaped the mixture; the independent evidence is S1 (small synthetic handlers, 18 cells) and S3 (two other real layouts). Nothing of S1 or S3 has been seen.

## Arms (every set: the same events/visits and the same answers for every arm; paired)
`default` = `JointSettings()`; `mix` = `JointSettings(low_mix=MIX)`; in S2 also `adjusted` = `JointSettings(r_low=0.10)` as a reference (it is the setting `mix` is meant to replace without tuning).
Everything else is the live tool exactly (T1 + control-system access + point map, no attributes; `min_rate` 0.02; `tau` 0.95; drawings `mostly_right`).

## S1: does it hurt where the shipped model was fine? (Addendum 30's 18 cells, synthetic building, 8 rooms per handler)
All 18 cells, 1000 events each (stream `[30, cell, 0, i]`, answers from `TableOracle`), tiers T3-noattr (primary) and T3, policies `tool_joint` (the CLI's session; primary) and
`tool_ticket_memo2` (the routine; secondary). Labels, tolerances and paired bootstrap are Addendum 21's as in `study_tau.py`. A cell is a **HARM cell** for a combination if its label is WORSE,
or its accuracy label is LESS, or its safety label is REGRESSION.

## S2: the registered bldg11 visits (100 visits, W0 and W1, `simulate.py`'s family and answers exactly)
Arms `default` (= `tool_shipped` of the registered run), `adjusted`, `mix`. Metrics and bootstrap as in `SIM_PROTOCOL.md` (accuracy, wrong-and-confident, not concluded, false shared-cause
call, minutes per visit; segments).

## S3: two other real layouts (100 visits each, W0 and W1, the same visit family)
`bldg18` (5 handlers of 3, 7, 28, 39 and 67 boxes; recorded points: static on every handler, zone temperature, setpoint and reheat command on the boxes, **no airflow or damper points**) and
`bldg8` (one handler, 24 boxes; static, airflow, damper and reheat points). Mortar bldg18 and bldg8 point maps are built by `build_building.py` exactly as bldg11's (recorded points only);
the check list of each building drops every check whose control-system point does not exist anywhere in that building (for bldg11 this reproduces the demo's list). The visit family is S2's
(six distinct rooms; shared visits 0-49 with `k` = 3, 4, 5 rooms of the LARGEST handler affected by low static and the rest local; local visits 50-99; local cause 10% wrong box of which 10% unlisted,
else uniform over the 11 box-level causes; answers drawn from the catalogue's rates, W1 = rates 25% toward 0.5). For `bldg8` (one handler) the local complaints of shared visits sit on the faulty handler.

## Metrics, per complaint; 95% intervals from a bootstrap over visits (2000 resamples) in S2/S3
Accuracy (exact leading cause), wrong-and-confident (concluded and wrong), not concluded, false shared-cause call, minutes per visit. Paired differences `mix - default` and `mix - adjusted`.

## Predictions (written now; each reported as holds / does not hold)
- **P1 (no harm, primary).** S1, `tool_joint` at T3-noattr: `mix` is a HARM cell in at most 1 of the 18 cells.
- **P2.** S1, same combination: `mix` is NEITHER in at least 12 of 18 cells (small handlers: little to gain).
- **P3.** S1, same combination: cell-mean accuracy within 1 point and cell-mean minutes within 5% of `default`.
- **P4.** S2 at W0: `mix` accuracy within 3 points of `adjusted` and at least 15 points above `default`.
- **P5.** S2 at W0: `mix` accuracy on shared-cause complaints is at least 80%.
- **P6.** S2 at W0: `mix` minutes per visit at most `default`'s and within 15% of `adjusted`'s.
- **P7.** S2: `mix` still FAILS the registered safety bar (wrong-and-confident above 5% at W0 or above 10% at W1), because the folding is not addressed.
- **P8.** S3 `bldg18` at W0: `mix` accuracy at least 5 points above `default`.
- **P9.** S3 `bldg8` at W0: `mix` accuracy at least 5 points above `default` (the shipped model already fails at 24 rooms).
- **P10.** In no S2/S3 building does `mix` lose more than 3 points of accuracy to `default`, at W0 or W1.
- **P11.** In no S2/S3 building does `mix` take more minutes per visit than `default`, at W0 or W1.

## Gates (a failed gate means NO RESULT)
G1 the default path is unchanged: `study_tau`'s gates reproduce Addendum 30's stored per-event results and Exploratory note E2's numbers, and this script's `default` arm reproduces the registered
bldg11 run's `tool_shipped` rows exactly (all visits, both worlds). G2 a one-level mixture `((0.5, 1.0),)` reproduces `default` exactly (guesses and minutes) on 30 bldg11 visits, and the mixture's
state prior and its by-cause posterior each sum to 1. G3 the generalised visit generator reproduces `simulate.draw_visit` exactly on bldg11's 100 visits; every S3 visit has six distinct rooms
and the stated composition. G4 oracle draws are order-independent. G5 completeness (every arm, every visit, both worlds, finite minutes). G6 the derived check list of bldg11 equals the demo's.

## Limitations named up front
Home-field answers; the visit mix is mine; the mixture grid and its equal weights are mine; 100 visits resolve accuracy differences of about 8 points; S3 has two buildings; bldg18 has no airflow
points, so its check list is thin (low accuracy there says something about sparse points, not about the mixture); the folding is untouched, so confident errors are expected to remain; minutes are
placeholders.

## What would follow
P1, P2 and P3 hold and S2/S3 gain: the mixture is a candidate to replace the fixed `r_low` in the CLI (the user's decision, through a flag as for `min_rate`), not a result. P1 fails: the mixture
harms small handlers and is not offered. P7 failing to hold would be the surprise: the safety bar would then be met without a folding fix.
