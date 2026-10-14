# bldg11 scenario demo (second demo, beside `../live_demo`)

A separate local demo. `../live_demo` (port 8743) is untouched; this one runs on **8744**.

```bash
.venv/bin/python doc_mismatch/live_demo_bldg11/server.py      # http://localhost:8744
```

It needs `data_cache/mortar__bldg11.ttl` (the Mortar Brick files are downloaded by the project's data step and are not in the repository). The building file is generated from it on first
use into `data_cache/demo_bldg11/` (git-ignored). **Do not commit that file or deploy this demo to the pilot host**: the Mortar licence rests on an email (`data_cache/timeseries/LICENSES.md`),
and the box and room identifiers look like real room numbers.

## What is real and what is scripted

| Piece | Source | Real? |
|---|---|---|
| 2 air handlers (AHU06: 49 boxes, AHU05: 34), every box and room under them, who feeds whom | Mortar bldg11 Brick model | real |
| Control-system points: airflow, damper command, reheat command (box), zone temperature, duct static (air handler) | the same Brick file, recorded points only | real |
| Which rooms complain, their causes, every answer to every check | `scenario.json`, `world.py` | **scripted** |

Points the Brick file does not have are not on the map: no fan status, no controller status, no airflow *setpoint*, no attributes (reheat type, design airflow, K-factor, static setpoint). So
`bas_ahu_fan` and `bas_controller` are left out of the check list, and the tool says "no expected value on file" for readings, as in the original demo (T3-noattr profile).
Coverage (from `build_building.py`): AHU06 45 of 49 boxes and AHU05 31 of 34 have airflow + damper command + reheat command + zone temperature.

Each ingredient of the script has a real precedent we read (`../FIELD_SOURCES.md`): a shared air-handler cause starving many boxes (NEBB hospital air handler; PNNL's more-than-25%-of-dampers-open rule),
reading the air handler first (the Trane "No Heat" call), a failed damper actuator (the same call), a box whose label does not match the BAS (the cold-morning call). No source combines them;
the combination is invented.

## The scenario

Six "too warm" complaints, arriving interleaved across the two air handlers (`scenario.json`):

| # | Room | Air handler | Scripted truth |
|---|---|---|---|
| 1 | RM2303 | AHU06 | low duct static |
| 2 | RM4511 | AHU05 | damper actuator failed |
| 3 | RM4311 | AHU06 | low duct static |
| 4 | RM5502 | AHU05 | documented box wrong; really fed by VAVRM5503 |
| 5 | RM5312 | AHU06 | low duct static |
| 6 | RM6302 | AHU06 | low duct static |

Why it should be hard for a technician (my reasoning, **not measured**): the ids look like room numbers with the floor as the first digit, so the four AHU06 complaints sit on floors 2, 4, 5
and 6 and look unrelated; one documented box reads normal; 83 boxes on two handlers. The only quantitative evidence about technician effort in this project is the assumed trial-and-error
stand-ins of Addendum 20, and the two real calls in which experts were quick. Asking a real engineer how long this visit would take them is the cheap check.

The scenario answer is the catalogue's own most likely reading under the scripted cause (`world.py`), so the tool is never fooled here. This walk-through shows how the tool reasons;
it measures nothing. Accuracy under noisy answers is measured separately: `SIM_PROTOCOL.md` (frozen before the run, hash in `SIM_PROTOCOL.sha256`), `simulate.py`, results in
`results/docmismatch/bldg11_sim/` (`report.md` as registered, `exploratory.md` post-hoc). Headline: the "large-handler setting" finds the shared cause (94% at the tool's own rates) but folds
local faults on the same handler into it, and **fails the registered safety bar** (confidently wrong 7.5% at W0, 10.5% at W1, against 5% and 10%).

## The finding the build turned up: the shipped joint model cannot see a shared fault on a large handler

The joint model (`troubleshoot/v2/joint.py`) assumes a room on a low-static handler complains with probability `r_low = 0.5` and counts every *silent* room on the handler as evidence against a
shared fault. In the original demo's building (8 rooms per handler, 2 complaining) that leaves 9% on low static before any check. Here, with 4 complaints among AHU06's 49 rooms, it leaves
about 5e-11 (prior printed as 0.0%), so the tool never reads the handler's static and every AHU06 room ends at a 61% "box or room capacity problem" best guess: wrong, 219 minutes, 2 of 6 match.

The model switch on the intro page runs the same engine with `r_low` cut to 0.10 ("Large-handler setting"): static is read once, the other AHU06 rooms inherit it at zero minutes, 6 of 6 match,
119 minutes. Sweep (all else equal): `r_low` 0.02 to 0.2 gives 6/6 (119 to 171 minutes); 0.25 and above, including the shipped 0.5, gives 2/6 (219 minutes). It is a tuning for this scenario,
not a validated setting, and 0.5 itself was never measured either.

## The general fix: a severity mixture (`JointSettings.low_mix`) and a short list

After the simulation, two changes that add no checking time were built (the folding fix adds time and is NOT built; the data-dependent levers need real outcomes):

- **`JointSettings(low_mix=...)`** (in `troubleshoot/v2/joint.py`, off by default, defaults byte-identical): instead of one fixed "half the rooms of a low-static handler complain", a mixture over
  5%, 15%, 50% and 90%, picked by the data. The demo offers it as "Mixed severity (general)"; the live CLI is unchanged (turning it on there is your decision, through a flag as for `min_rate`).
- **`Session.shortlist(k)`** (`troubleshoot/v1/engine.py`): "most likely A or B; to be more sure, do C (N min)" for a room the tool could not settle. It does not change the tool's single answer,
  so it is not an accuracy gain; it was 5.8 points of "right answer in the top two" on the 100 bldg11 visits (74.7% to 80.5%).

Protocol `MIX_PROTOCOL.md` (frozen before the run; hash in `MIX_PROTOCOL.sha256`), deviation `MIX_DEVIATIONS.md` D1, script `study_mix.py`, result `results/docmismatch/mix_study/report.md`.
**Registered outcome: NO RESULT** (a gate reference that Addendum 41 had already found wrong failed; the corrected gate passes; the numbers are reported under the logged deviation). 6 of 11 predictions held.

| set | mixture against the shipped model |
|---|---|
| bldg11, 100 visits | accuracy 50.7% to 74.8% (W0), 32.8% to 54.7% (W1); 97 fewer minutes per visit; equal to the hand-tuned 0.10 (74.7%) without tuning |
| bldg18 (67-room handler, no airflow points), 100 visits | 47.0% to 71.5% (W0), 30.0% to 48.0% (W1); 104 fewer minutes per visit |
| bldg8 (one handler, 24 rooms), 100 visits | no change (-0.7 points); the shipped model already finds the shared fault there because all six complaints sit on the one handler |
| 18 synthetic cells (8-room handlers), the routine | neutral: 0 of 18 cells harmed, minutes 60.4 to 60.0, accuracy -1.1 points (not significant) |
| 18 synthetic cells, the CLI's joint session | **about 6% more minutes** (10 of 18 cells WORSE on time; accuracy and safety unchanged): this is the one place it adds time |

Not fixed, and not helped by the mixture: **the folding** (a room with its own fault on a faulty handler is named as the shared cause). Wrong-and-confident stays at 6.8% (bldg11, W0), 5.0% (bldg18) and
18% (bldg8, where the shipped model has it too). The safety bar of `SIM_PROTOCOL.md` is still not met.

## What else could raise accuracy without time, and the ceiling (exploratory, 400 single complaints per cell, bldg11 point map; not registered)

The page offers two settings, "Shipped" and "Mixed severity (general)"; the hand-tuned `r_low` 0.10 ("adjusted") is still defined in `scenario.json` (`hidden`) because the registered scripts and tests use it.

| single complaint | accuracy as the tool runs (minutes) | ceiling if it did every check | checks 25% worse: as run / ceiling |
|---|---|---|---|
| today (no attributes, the tool's own priors) | 71.0% (47) | 82.2% | 42.0% / 55.0% |
| + documented design values | 70.0% (43) | 83.2% | 43.8% / 57.0% |
| + priors matching the building's real cause mix | 76.5% (46) | 84.8% | 45.5% / 58.8% |
| + both | 77.8% (45) | 86.2% | 47.0% / 61.5% |

So with this catalogue even unlimited time, documented values and perfect priors top out near 86%; 90% needs checks that separate look-alike causes or more reliable readings, which simulation cannot establish
(it would only assume the rates). The matched-priors row uses a world I made uniform over the 11 causes, so it is an upper bound for that mismatch: if the real mix resembles the tool's placeholder prior it gains nothing.

### What extra time buys (exploratory, 1500 single complaints per cell, same draw and noisy answers as above; not registered; script not kept in the repository)

| spend more time by | accuracy at tool rates (minutes) | accuracy, checks 25% worse (minutes) | confidently wrong, checks 25% worse |
|---|---|---|---|
| nothing (as the tool runs) | 73.6% (46) | 45.8% (46) | 3.7% |
| stopping later, `min_rate` 0.01 | 75.0% (54) | 47.9% (56) | 5.9% |
| after it stops, up to 2 more of its own short-list checks while below 95% | 77.3% (62) | 48.7% (63) | 7.7% |
| the same, up to 4 more | 79.5% (76) | 50.8% (79) | 8.6% |

About 0.2 points per extra minute at best, flattening toward the ceiling (82 to 86%). With the weaker checks the confidently-wrong share rises with every extra reading. Raising `tau` to 0.99 changes nothing
(the tool almost never reaches 0.95 on a wrong cause at tool rates). The folding fix is not in this table: it is for multi-complaint visits and was not measured (upper bound about 7 points, the folded share of errors).

### Better readings, first look (exploratory; `READINGS_NOTES.md` has the predictions, hashed before the run; `study_readings.py`, `sweep_reliability.py`; report in `results/docmismatch/readings_study/report.md`)

**Graded numeric readings** (`troubleshoot/v1/graded.py`, `make_case_v1(..., graded=True)`, off by default, default byte-identical, tests in `tests/test_v1_graded.py`): the technician's number is scored by how far off it is
instead of only normal/abnormal, using the catalogue's own rates (a Gaussian assumption of mine, not measured). **Result: no gain.** 1500 single complaints per cell, graded minus yes/no on identical draws:

| numbers drawn from | checks as assumed (W0) | checks 25% worse (W1) |
|---|---|---|
| the shape the model assumes (home field) | +1.7 points (95% CI +0.3 to +3.1), confidently wrong +0.1 | -0.3 (CI -1.9 to +1.4), confidently wrong +1.7 |
| varying severity, heavier tails | -0.9 (CI -2.3 to +0.5), confidently wrong +1.3 | +0.6 (CI -1.1 to +2.3), confidently wrong +2.9 |

Predictions: 5 of 6 held, but the one that mattered (a gain of 1 to 6 points at W0) held only at its lower edge, and the prediction that the confidently-wrong share would rise when checks are worse also held (it rose in 3 of 4 cells). Reason (my reading): the errors are among
look-alike causes that a check sees equally, and a reading's size separates "saw the cause" from "did not", not one look-alike from another; per-cause reading sizes are not something the catalogue has.

**What reliability is worth** (post hoc, `sweep_reliability.py`; the world's check rates move toward 0.5 or away from it, the tool's assumptions never change; 1500 single complaints):

| world's checks vs the tool's assumption | accuracy | minutes | confidently wrong |
|---|---|---|---|
| 25% worse | 46.6% | 46 | 3.8% |
| 10% worse | 62.1% | 47 | 1.2% |
| as assumed | 73.4% | 46 | 0.1% |
| 10% sharper (a strong check's 8% miss rate about halves, its 4% false alarm rate goes to about 0) | 84.6% | 45 | 0.0% |
| 25% sharper (strong checks error-free, weaker ones modestly better) | 88.9% | 44 | 0.0% |
| 50% sharper | 90.7% | 43 | 0.0% |

So reading reliability is the lever, and it saves time too; what the numbers cannot say is whether a typed number is more reliable than a judged one, or by how much. That needs the real number next to the real word
in the pilot's case records (the pilot adapter does not pass `reading=` / `expected=` through yet) and the verified outcome.

### Is the assumed false-alarm rate of the BAS readings about right? (exploratory; `FALSE_ALARM_NOTES.md` hashed before any value was read, `FALSE_ALARM_DEVIATIONS.md` D1, `measure_false_alarm.py`, report `results/docmismatch/false_alarm/report.md`)

Real Mortar trend data (bldg1, 8, 15, 30, 40), false-alarm side only (no labelled faults exist, so hit rates are untouched).

- **`bas_airflow` (catalogue 5%): NOT MEASURABLE.** The only recorded airflow "setpoint" (bldg30, 99 boxes) takes 1 to 8 values in a year: a configured limit, not a live setpoint. My first run printed 95% against it and called the assumption
  optimistic; that was an artifact, caught by a validity check and logged (D1). No downloaded building records a live airflow setpoint.
- **`bas_static` (catalogue 3%): bracketed, not called.** No building records the static setpoint either, so the reading was compared with proxies for it (running samples, 7 handlers, one instantaneous reading per 15 minutes, more than 20% off):

| proxy for the setpoint = median of the readings within | 2 h | 6 h | 24 h | 7 days | whole record |
|---|---|---|---|---|---|
| share of readings more than 20% off, median over handlers | 0.6% | 1.4% | 3.1% | 7.9% | 16.0% |

If the setpoint a technician compares with moves within a few hours, the false-alarm rate is under the catalogue's 3%; it reaches 3% only if the reference is a day old, and 16% against the whole-record level (which over-states whenever the setpoint is reset). The pre-registered rule
("called only if both proxies agree") gives NOT CALLED. Faults in the data only raise these figures. Predictions: F2 held; F1 and F3 (airflow) not testable.

### Hit rates of two BAS checks against the LBNL PFPU simulated fault set (exploratory; `LBNL_PFPU_NOTES.md` hashed before any value was read, `LBNL_PFPU_DEVIATIONS.md` D1, `measure_pfpu.py`, report `results/docmismatch/lbnl_pfpu/report.md`)

The data are SIMULATED (HVACSIM+; 1 air handler, 4 fan-powered boxes, one fault per one-year file at 1-minute steps; downloaded 2026-10-11 with your approval, 1.03 GB, MD5 verified, `data_cache/timeseries/lbnl_pfpu/provenance.json`).
A hit rate here is at best a plausible upper bound on a real one, a false-alarm rate a plausible lower bound; only "hit rate below the catalogue's" is informative. **The documentation says the fault is in the west box; the files say south**
(a damper stuck closed or open has a constant position in box S only); my first run measured the wrong box and printed 0.00 everywhere, caught and logged as D1.

| catalogue pair | simulated fault | catalogue | measured at a random Operate minute | verdict |
|---|---|---|---|---|
| `bas_airflow` on damper_mech / actuator_fail | damper stuck at 0, 20, 50, 80, 100% | 0.75 | 1.00 at every severity | no information (above) |
| `bas_airflow` on flow_sensor | airflow sensor bias of +-200 and +-400 cfm | 0.50 | 1.00 | no information (above) |
| `bas_airflow` on controller_config | unstable damper control loop | 0.50 | **0.27** | catalogue optimistic |
| `bas_reheat` on reheat_fail | reheat valve stuck or leaking | 0.75 | **0.08** (0.00 to 0.51); 0.65 to 1.00 while heat is called for, stuck valves only; leaking valves 0.00 | catalogue optimistic at a random minute |

False alarms in the simulation: 0.1% (`bas_airflow`) and 0.0% (`bas_reheat`): a clean simulation, no information about real equipment. Predictions: 2 of 5 held (P1 and P2 failed: the airflow check catches stuck dampers and biased sensors every time, and the simulated bias is in the logged value only; P3 missed by 0.03).
Descriptive: coil fouling, room-temperature bias and a restricted box fan are invisible to both checks (0.00). The pattern worth keeping: a reading's hit rate depends on WHEN it is taken (a reheat fault shows only while heat is called for; a hunting loop only part of the time),
which the catalogue's single number per cause does not express.

### Why six rooms score lower than the walk-through's 6 of 6 (exploratory; `demo_composition.py`, and the segment tables of `results/docmismatch/bldg11_sim/report.md`)

Accuracy of a visit is a weighted average of very different rooms. Registered 100-visit sim, the ADJUSTED setting (`r_low` 0.10; with the mixed setting the demo now opens on, the same 57 faulty-handler rooms score 10.5%, shared rooms 92.5%, overall 74.8%), checks as the tool assumes (600 rooms): the 199 shared-cause rooms 94.5%, the 300 independent local-fault rooms in visits with no shared cause 74.7%
(the same as one complaint alone: 73.6%), and the 101 local rooms in visits that also have a shared cause 35.6%: **57 of them sit on the faulty handler and score 3.5% (52 of 57 are called "low static", the folding problem)**, the 44 on the healthy handler 77.3%.
Visits shaped like the demo's script (4 shared rooms on AHU06, a failed actuator and a wrong documented box on the healthy AHU05; 200 visits per cell, noisy answers): per room 84.2% at W0 (shared 91.2%, local 70.2%), 60.2% at W1; every one of the six right in 40% of visits at W0 and 7% at W1.
The script avoids the folding case by putting its local rooms on the healthy handler, which is why it does better than the sim's average. In the earlier synthetic study, visits with many complaints are mostly shared-cause (the easy case), so its per-complaint accuracy rises with the number of complaints.

### Can the folding be fixed selectively? (exploratory; `FOLD_PROTOCOL.md` hashed before any variant ran, `study_folding.py`, report `results/docmismatch/fold_study/report.md`)

The same 100 visits, the demo's mixed setting, gates passed (the replica of the routine is exact; the base reproduces 74.83% / 193.7 min and 54.67% / 204.8 min). After a room's session ends with low static leading and no box-level static reading of its own, a verification step is added:

| variant (W0) | accuracy | own-fault rooms on the faulty handler | added minutes / visit | accuracy gain (95% CI) | points per added minute | added minutes on rooms base already had right | wrong-and-confident |
|---|---|---|---|---|---|---|---|
| base | 74.8% | 10.5% | - | - | - | - | 6.8% |
| V1 every room, box static (14 min) | 77.3% | 43.9% | +42 | +2.5 (+0.8, +4.2) | 0.06 | 60% | 2.3% |
| V2 every room, best check per minute | 77.0% | 40.4% | +35 | +2.2 (+0.5, +4.0) | 0.06 | 58% | 3.7% |
| V3 two rooms per handler, box static | 76.7% | 36.8% | +32 | +1.8 (+0.2, +3.5) | 0.06 | 57% | 3.5% |
| V4 two rooms per handler, best per minute | 76.5% | 35.1% | +30 | +1.7 (-0.0, +3.3) | 0.06 | 57% | 4.0% |

By the pre-set rule (gain of at least 3 points, at most 15% more time, at least 0.3 points per minute) every variant is NEITHER. A budget is linear, not selective (V3 keeps 73% of V1's gain for 75% of its minutes); no free signal separates the folded rooms.
Shared-cause rooms lose 2 points (92.5% to 90.5%: a noisy check flips some right ones). Folded rooms reach 44%, not 75%: the check shows "not low static", the room's own fault still has to be found among look-alikes.
**What it does buy is safety:** wrong-and-confident falls from 6.8% to 2.3% to 4.0% (intervals exclude zero, e.g. V1 -4.5, 95% CI -6.5 to -2.5; the interval was added after the table was seen); the registered bar was 5% at W0, which base fails and every variant meets. The rule did not weigh this, so the verdict stays NEITHER.
At W1 the gains are +1.2 to +1.3 points and confident errors fall by 3.0 to 4.0 points. Predictions: 4 of 7 held (P1, P2 and P4 failed). The oracle answers a room check from that room's own cause only, so a room with its own fault on a low-static handler reads "normal" at its box; in a building it would also read low. These gains are upper bounds.

### Does looking at a day's trend instead of one live value sharpen the checks? (exploratory; `TREND_NOTES.md` hashed before any trend-window value was computed, `trend_pfpu.py`, `study_trend.py`, reports in `results/docmismatch/trend_study/`)

Part A, on the LBNL PFPU SIMULATED fault set (a best case, so upper bounds; gate: the snapshot rates are re-derived exactly): hit rate of the same rule applied to the trailing 24 h or 4 h of Operate minutes in the faulted box.

| fault | check | snapshot | 24 h window | 4 h window | catalogue today |
|---|---|---|---|---|---|
| damper stuck (any position) | bas_airflow | 1.00 | 0.98 | 0.92 | 0.75 |
| airflow-sensor bias | bas_airflow | 1.00 | 0.98 | 0.92 | 0.50 |
| unstable damper loop | bas_airflow | 0.27 | **0.84** | 0.70 | 0.50 |
| reheat valve stuck or leaking | bas_reheat | 0.08 | **0.19** (stuck closed 0.76, leaks 0.00) | 0.12 | 0.75 |

A trend triples the catch rate of an unstable loop; it barely helps the reheat check, because 73% of one-day windows contain too few heat calls to judge (counting a valve that differs from its command with no call: 0.59, post hoc). Predictions: 4 of 5 held (reheat 24 h missed its 0.25 to 0.60 range).
Part B, those rates mapped into the catalogue (only the pairs the simulation can speak to; clipped to [0.05, 0.95]; trend look 4 min instead of 2) and run on the same 100 visits, tool and world agreeing: **+1.5 points at W0 (95% CI -0.8 to +4.0), 9 fewer minutes, wrong-and-confident 6.8% to 3.5%: NEITHER** by the pre-set rule
(at W1 -1.5, CI -4.0 to +1.0). 2-minute and 8-minute trend looks: +2.0 and +0.5. Four of four Part B predictions held.

CONTEXT, not measured by any data: every reading check 25% sharper (tool and world): 85.7% at W0 and 49 fewer minutes, but own-fault rooms on the faulty handler stay at 0% (folding), wrong-and-confident 9.5%.
POST HOC combination (added after seeing those rows): sharper checks together with the box-level verification of folding (V1): **92.2% at W0, 202 minutes (base 194), wrong-and-confident 2.3%**; 10% sharper does not get there (79.5%, verification changes nothing because the handler reading outweighs one box reading).
All of it assumes the sharper rates are TRUE: if the world is only 25% worse than the sharpened claims, accuracy is 55 to 58% and wrong-and-confident 28 to 33%. A sharper catalogue must be measured before the tool trusts it.

### Datasets looked for, for the causes the LBNL PFPU set does not cover (search only; nothing downloaded; 2026-10-11)

Almost every public labelled-fault set is fault injection: sensor bias, stuck dampers and valves, fouling, unstable control. None found covers loss of power, signal or communication, a disconnected diffuser, or an undersized box.

| lead | what it is | what it could give | status |
|---|---|---|---|
| ORNL "Datasets of faults in VAV terminal units" (Sci Data 2025; report ORNL/TM-2024/3704, OSTI 2479032) | EXPERIMENTAL, ORNL Flexible Research Platform; electric-reheat VAV boxes; damper stuck at 0, 20, 40, 60, 80, 100% (three sets, summer and winter 2023); airflow-sensor errors of +-20% and +-40% (made by shifting the airflow setpoint); 1-minute | real-hardware check of two pairs the simulation could only bound (damper stuck, airflow sensor) | download location not found (publisher page needs a login redirect); the listed points include airflow, damper opening and reheat energy but NO airflow setpoint, so the airflow-vs-setpoint rule cannot be applied as is |
| LBNL dual-duct AHU set (1.78 GB, SIMULATED, HVACSIM+) | 55 faulted cases, includes cold- and hot-deck SUPPLY AIR PRESSURE sensor bias (+-0.2, +-0.4 in.w.c.), which leaves the true duct static low while the logged value looks fine | nearest thing to a low-static fault; dual-duct boxes, not single-duct | not downloaded |
| Korean office AHU set (Figshare 25909813, 6.8 MB, REAL, hourly, 20 AHUs, Nov 2023 to May 2024) | semi-labelled by two experts: normal, supply fan fault (32,688 rows), pump, return- and supply-air sensor faults; 11 variables, no static pressure, no damper | only real labelled supply-fan faults found; coarse | not downloaded |
| ASHRAE RP-1312 (EXPERIMENTAL, Iowa Energy Resource Station; 17 faults incl. duct leakage, unstable control) | AHU-level experimental faults | duct leakage (a low-static mechanism) | access terms not found |
| FMUCD work orders (REAL, already on disk; 600 sampled HVAC orders) | free text with the technician's stated cause | the real mix of causes (priors), NOT check reliability; labels would be mine, unverified | usable now |
| NREL/OEDI "cyber-induced mechanical faults" | BACnet attack simulation | not device failure or power loss | not relevant |

For loss of power, signal and communication, a disconnected diffuser and an undersized box, no public labelled data was found: the pilot's verified outcomes, or fault injection on a testbed or simulator, are the remaining routes.

### Two reliability suggestions from a second agent, tested on the LBNL PFPU simulated set (exploratory; `LEAK_SHORT_NOTES.md` hashed before any value of the new rules was computed, `leak_short_pfpu.py`, report `results/docmismatch/leak_short/report.md`; both gates passed; predictions 2 of 7 held)

- **Discharge temperature above supply temperature for a leaking reheat valve** (more than 3 degF, no heat called, fan off): NOT SHARPER. Leaks 0.00 with the existing rule become 0.30 (24 h window), the pooled stuck+leak family 0.19 to 0.37 (catalogue 0.75), at a false-alarm rate of 0.10 (24 h; 0.05 snapshot).
  The hit rate is 0.15 at every severity (20% leak to valve stuck fully open), so it does not scale with the fault; by month it is flagged 39 to 45% of the time in January and February and 0% in July and August, and the fault-free run itself false-alarms 12 to 26% of winter minutes. Hot water is hot 88% of the time, so water temperature is not the reason.
  In this simulation a leak is not visible in the discharge temperature of a summer afternoon (real plants may differ; not tested).
- **A five-minute AVERAGE of the airflow miss near maximum airflow**: NOT SHARPER, and worse than a snapshot for an unstable loop (0.14 against 0.27), because an average washes out spikes. Post hoc: COUNTING out-of-band minutes among the last five gives 0.65 (at least 1), 0.37 (at least 2), 0.19 (at least 3) on the unstable loop, with 0.2% or less false alarms in this clean simulation; the 24 h window (0.84) is still the best rule measured. Stuck dampers and sensor bias stay at 1.00 under every version.

### Does the independence assumption hurt when check errors are correlated? (exploratory; `CORR_NOTES.md` hashed before any correlated run, `study_correlation.py`, report `results/docmismatch/corr_study/report.md`; gates passed; predictions 2 of 6 held)

My construction (no data say how often it happens): with probability pi the control-system data at a box is invalid, and then every control-system check at that box answers in one shared direction whatever the cause. Same 100 visits, mixed setting, W0:

| pi | tool | accuracy | wrong and confident | minutes |
|---|---|---|---|---|
| 0 | independent (today) | 74.8% | 6.8% | 194 |
| 0.10 | independent | 73.7% | 7.2% (+0.3, CI 0.0 to +0.8) | 194 |
| 0.25 | independent | 72.8% | 7.5% (+0.7, CI -0.2 to +1.5) | 197 |
| 0 / 0.10 / 0.25 | mixture ("data may be invalid", p_t 0.10) | 74.8 / 73.7 / 73.5% | 5.7 / 6.0 / 6.3% | 197 / 200 / 205 |
| 0 / 0.10 / 0.25 | tempered (group counts as one observation) | 72.2 / 71.8 / 72.0% | 6.5 / 6.8 / 7.3% | 208 / 209 / 210 |

HARM of correlation by the pre-set rule: NO. Why it is small: the tool takes about 2.5 control-system box reads per room (390 of 600 rooms take two or more), so there is plenty to multiply, but invalid data mostly produces contradictory evidence, not a confident wrong answer:
among rooms with two or more reads at pi = 0.25, invalid-data rooms are 61.9% right against 72.5% for valid ones (-10.6 points) and 2.9% wrong-and-confident against 0.3%. Confident errors concentrate elsewhere: the 117 rooms with NO box read of their own (the folding case) are 24.8% wrong-and-confident.
The mixture treatment is nearly free (no accuracy cost, +3 to +9 minutes) and trims confident errors by about 1 point even with no correlation (-1.2, CI -2.2 to -0.3); it does not reach the 5% bar. Tempering costs 2.7 accuracy points and 15 minutes at pi = 0 and is not worth it.
The test cannot rule out a worse real-world correlation (direction fixed 50/50 here); it found no large hidden problem.

### Where do the errors come from? (exploratory; `ERRORS_NOTES.md` hashed before any analysis, `study_errors.py`, report `results/docmismatch/error_study/report.md`; gates passed; predictions 4 of 7 held)

The 151 wrong rooms of the registered 100 visits (mixed setting, W0), each sorted by whether a check that separates the truth from the tool's answer (Jeffreys divergence at least 0.25 between the two causes' response rates) was missing, not taken, taken and misleading, or taken and mixed:

| segment | wrong | gap | not taken | misled | mixed | box-identity |
|---|---|---|---|---|---|---|
| own fault, no shared cause | 75 | 0 | 1 | 18 | 43 | 13 |
| own fault, faulty handler (folding) | 51 | 0 | 0 | 33 | 10 | 8 |
| own fault, healthy handler | 10 | 0 | 0 | 1 | 7 | 2 |
| shared | 15 | 0 | 0 | 1 | 14 | 0 |
| all | 151 | 0 | 1 | 53 | 74 | 23 |

**The catalogue is not short of discriminating checks and the tool is not failing to take them: 84% of the errors (127 of 151) are noisy answers** (misled or mixed), at the tool's own assumed rates. Fixing every misled error would add 8.8 points, every mixed one 12.3 (together a ceiling near 96%, if the discriminating checks never lied).
The symptom clusters are scattered (the five most common signatures hold 28% of the ordinary errors; 50 distinct signatures). Post hoc: in the folded rooms 38 of the 43 non-box-identity errors have a zero-minute COPY of another room's reading among the discriminating evidence (the routine's group-informing rule); in the ordinary errors 61 of 62 rest on the room's own measurements only.
Part 2: one hypothetical check specific to each of the five most confused pairs (fires 0.80 on its cause, 0.08 on everything else, 3 or 10 minutes) adds +0.3 to +0.7 points (3 min) or +0.3 to +1.7 (10 min); all five together -1.7 (3 min) to +2.2 (10 min), intervals include zero; one cheap check lowered accuracy by 2.5 points (flow sensor: the tool takes cheap checks eagerly and a 20% miss misleads).
A new check helps only if it is sharper than what already exists at the same cost. Caveat: that the catalogue separates a pair at 0.75 against 0.04 is itself an assumption; real gaps (pairs a technician cannot tell apart) are unknown and are a question for the technician sheet.

### What if the tool is TOLD the checks are more reliable than they really are? (exploratory; `OVERCLAIM_NOTES.md` hashed before the run, `study_overclaim.py`, report `results/docmismatch/overclaim_study/report.md`; gate passed; predictions 6 of 6 held)

The world answers with today's rates (W0) or 25% worse (W1); the tool believes today's rates (honest) or rates sharper by 10% or 25%. Same 100 visits, mixed setting:

| world | the tool believes | accuracy | wrong and confident | rooms it concludes | precision of its conclusions | minutes |
|---|---|---|---|---|---|---|
| W0 | honest | 74.8% | 6.8% | 43% | 84% | 194 |
| W0 | sharper by 10% | 69.7% (-5.2, CI -8.8 to -1.7) | 18.5% | 74% | 75% | 148 |
| W0 | sharper by 25% | 69.5% (-5.3) | 19.5% | 80% | 75% | 148 |
| W1 | honest | 54.7% | 8.3% | 36% | 77% | 205 |
| W1 | sharper by 10% | 46.8% (-7.8) | 40.0% | 80% | 50% | 128 |
| W1 | sharper by 25% | 45.8% (-8.8) | 42.0% | 82% | 49% | 126 |

Claiming reliability the checks do not have makes the tool stop sooner (24% fewer minutes), conclude far more rooms, and be right less often, both in how often its leading answer is correct and in how true its "95% sure" is (precision 75% in W0, about 50% in W1). Even a 10% overclaim does most of the damage.
The opposite error (real checks sharper than the tool believes) costs time, not correctness (the reliability sweep: a world 10% sharper than assumed gives 84.6% on single complaints at today's assumptions, with 45 against 46 minutes). The sharper-checks route to 90% therefore needs MEASURED rates in both directions.

### The pilot now runs on the severity mixture (2026-10-11)

`pilot/engine_adapter.py`: `JointSettings(..., low_mix=LOW_MIX)` is the default (5%, 15%, 50%, 90% of a low-static handler's rooms complaining, weight 1/4 each); `PILOT_JOINT_MODEL=shipped` runs the unmodified shipped model (documented in `pilot/.env.example`).
`catalogue_hash()` records the joint model (the shipped hash is unchanged, so earlier stored cases keep their meaning). Still different from this demo's Mixed setting: the pilot keeps `econ_fault` enrolled (the demo has it off), has no confidence cap or "own fault not ruled out" hedge, and keeps the rule that copies one room's reading into the other rooms of a handler (folding).
Tests: six new in `tests/test_pilot_engine_adapter.py` (default is the mixture and keeps the economizer cause; the switch gives exactly the old settings; a bad value fails loudly; the shipped fingerprint is unchanged; on a 49-room handler with 4 complaints low static is 4e-11 shipped and 0.021 mixed, and on an 8-room handler both are above 0.5; a visit builds on the default); all 187 pilot tests pass under both settings.

### The pilot now hedges low-static conclusions and caps their confidence (2026-10-11)

`pilot/engine_adapter.py` `hedge_for()`: when a room's leading cause is low duct static and its session holds no box-level static reading of its own (the zero-minute copy of another room's reading does not count; an "unsure" answer does not count), the technician sees "Explained by low static, own fault not ruled out" instead of "Diagnosed", confidence capped at 90% (`HEDGE_CAP`), a note, and the most informative check at that room (box or room, never the air handler).
The stored `tool_conclusion` event carries `hedged`, `raw_belief` (the model's number; `belief` is what was shown) and `hedge_rule_out`; the visit summary tags the room. Nothing else changes: no check is added or skipped, no leading answer, no minutes.
Measured with exactly this tool-side rule on the registered 100 bldg11 visits (mixed setting, simulated answers): wrong-and-confident 6.8% to 0.2% (8.3% to 1.5% with checks 25% worse); rooms called confident 43% to 15.5%; precision of the confident ones 84% to 99% (77% to 87%); accuracy unchanged (74.8% / 54.7%). The price: 166 conclusions hedged, 126 of them right (149 and 108 of them right at W1).
Limits: low static only (a fan-off conclusion can be inherited the same way; not measured, not hedged); in a real building a room with its own fault on a low-static handler would also read low static at its box, so the box reading does not prove the room has no fault of its own, which is why the note leads with "fix the air handler first and check whether this room is still off";
the rule that copies one room's reading into the others (the cause of folding) is unchanged; the measurement is simulated. Tests: `tests/test_pilot_hedge.py` (9; they fail when the hedge is switched off); all pilot tests pass.

### Mixed against shipped on a second scenario of similar complexity (exploratory; `SECOND_NOTES.md` hashed before any run, `SECOND_DEVIATIONS.md` D1 (a rounding-edge failure of my own gate, fixed; the first run's numbers are unchanged), `study_second.py`, report `results/docmismatch/second_scenario/report.md`; gates passed; predictions 5 of 7 held; no new demo or UI)

Real Mortar layouts, simulated causes and noisy answers. bldg15 (the requested second scenario): handlers of 86 and 43 boxes (only 3 of the 43 have the full point set, so the two own-fault rooms are drawn from a thin pool); bldg9 (replicate): 70 and 56 boxes; bldg11 (reference): 49 and 34. Gate: the harness reproduces the earlier bldg11 demo-shaped run exactly (84.2% / 190 min mixed, 23.8% / 332 shipped).
**Scenario A, demo-shaped visits** (4 low-static rooms on the larger handler; one failed actuator and one wrong box on the other; 200 visits; per room, checks as assumed): shipped to mixed 22.8% to 75.2% on bldg15 (+52.5 points, CI +49.7 to +55.2; 323 to 239 minutes), 23.9% to 81.1% on bldg9, 23.7% to 84.4% on bldg11 (restricted draw). With checks 25% worse: 10.8% to 48.5% (bldg15).
The win replicates but is smaller on bldg15 than on bldg11: the four shared rooms are 78.8% right (bldg11: 91.8%) and all six right in 22% of visits (bldg11: 42%). A hypothesis, not tested: 4 complaints among 86 rooms is 4.7%, just under the mixture's lowest level (5%).
**Scenario B, the registered composition** (own-fault rooms can sit on the faulty handler; 100 visits): mixed beats shipped by +23.0 (bldg15) and +22.8 (bldg9) points; the price is the folding trade seen on bldg11: own-fault rooms on the faulty handler fall from 76.2% to 23.8% (bldg15), wrong-and-confident rises from 0.5% to 4.0% (bldg9: 0.2% to 3.3%), and with the pilot's hedge it is 0.2% (0.0%).

### Mixed against shipped on the FIRST demo's setup (exploratory; `FIRST_DEMO_NOTES.md` hashed before any run, `FIRST_DEMO_DEVIATIONS.md` D1 (the demo's live "does this box have reheat?" question declared as yes), `study_first_demo.py`, report `results/docmismatch/first_demo/report.md`; gates passed; predictions 5 of 5 held; the first demo's files were only read and are unchanged)

The first demo: 3 handlers x 8 boxes, Room-0 and Room-1 both on AHU-0, no scripted answers, shipped joint model. Simulated noisy answers, 400 two-room visits in four compositions (100 each), configuration imported from the demo's own server. **Mixed and shipped make exactly the same decisions in every composition, at both answer qualities: accuracy, minutes and confident errors are identical** (before any check: 9.1% against 11.0% on low static at AHU-0; the final beliefs differ in the fourth decimal, no decision flips). On a handler of 8 rooms the choice does not matter.
What the same run shows about the first demo itself (both settings): shared low static, both rooms right 95% (26 min); independent faults 76.5% per room (61% both right, 100 min); one shared and one own fault: the own-fault room right 7% of the time (folding exists here too), wrong-and-confident 45.5%, **0.0% with the pilot's hedge**;
shared FAN OFF with only 2 of 8 rooms complaining: 0% right, called low static with confidence 93% of the time (46.5% with the hedge). The model assumes a fan-off handler makes about 90% of its rooms complain, so two complaints of eight read as low static: a stress case outside the model's own world, but a real blind spot, unchanged by the mixture; the hedge covers low static only.

### The first demo now has the same two settings (2026-10-11, at your request)

`../live_demo` (port 8743) was left untouched until now. Its intro screen now offers "Shipped settings" and "Mixed severity (general)", Mixed by default, passed to `/api/start` (`server.py`: `MIX`, `MODELS`, `Visit(model)`; `static/index.html`: the picker, the note and the "before any check" figure); nothing else about it changed. On its 8-room handlers the two settings make the same decisions (see the first-demo study above), and the page says so.
A server started before this change keeps the old code in memory and sends no setting list; the page then shows no picker instead of breaking. Restart it to get the picker. Tests: `tests/test_live_demo_first.py` (5).

### A fan-off mixture and a lower end for the low-static mixture (exploratory; `FANMIX_NOTES.md` hashed before any run, `study_fanmix.py`, report `results/docmismatch/fanmix_study/report.md`; all gates passed; predictions 7 of 11 held; demos, pilot and shipped defaults untouched)

Two "do not commit to one number" changes, off by default (`JointSettings.fan_mix`, new, tests in `tests/test_joint_fan_mix.py`; and a 2/5/15/50/90% low-static mixture used only in the study). Simulated causes and answers, my visit families; real Mortar layouts (bldg11, bldg15, bldg9) and the first demo's 3 x 8 building. Four arms: TODAY (the 5/15/50/90% low-static mixture), FAN (TODAY + a 5/15/50/90% fan-off mixture), LOW2, BOTH.
- **Fan off (FAN), registered label TRADES.** The blind spot is real and closes: with 4 fan-off rooms on a 49-room handler TODAY gets 0% of them right and is 59% wrong-and-confident (13% with the hedge, which covers low static only); FAN gets 86% right (bldg15 75%, bldg9 81%) and 3.3% wrong-and-confident, for +4 minutes. On the first demo's 8-room handler with 2-4 rooms complaining: 0% to 89%, wrong-and-confident 57% to 1.8%. At W1 the gain is still +50 to +65 points on those rooms. The price is paid elsewhere: low-static visits lose 3 to 5 points per room on the real layouts (shared rooms 91.8% to 84.0% on bldg11; 4-6% of rooms are called fan off falsely), the registered composition loses 3.3 points on both layouts, and in the model's own world (fan off hits 90% of 8 rooms, S1) FAN loses 2.9 points, takes 19 minutes instead of 3 and its wrong-and-confident rises from 0% to 8.9%. Likely cause (read from the catalogue, not traced): `bas_static`, `static_at_box` and `ahu_gauge` read the same 0.92 under fan off and low static, so only `bas_ahu_fan` (0.92 against 0.20) or `ahu_visit` (0.92 against 0.10) tell them apart, and the 0.20 means one abnormal fan reading under a low-static handler (20%) tips the tool toward fan off.
- **Post hoc, not registered:** whether FAN is worth it depends on how many upstream faults really are fan off. From the study's own numbers (shared rooms only): FAN gains 75-86 points on fan-off rooms and loses 4.9-7.8 on low-static rooms at W0, so it breaks even when 6-8% of upstream faults are fan off; at W1 (gain 50-63, loss 8.5-16.6) when 14-21% are. The model's own placeholder share is 29%, which gives +18 to +20 points per shared room at W0 and +7 to +10 at W1. Neither the share nor how many rooms complain under a real fan-off is measured; both are things the pilot or the technician can say.
- **Lower end (LOW2), registered label NO GAIN, by a narrow miss.** bldg15 W0: +3.1 points (CI +1.8, +4.6), 239 to 214 minutes (-25; CI -28, -21); the registered bar also asked the four shared rooms to reach 85% and they reached 83.8% (TODAY 78.8%). W1 +5.1 points, -22 minutes. bldg9 +1.7 (+0.9, +2.5), -10 minutes; bldg11 -0.1, -2 minutes. No harm seen in the registered cells (the first demo's building within 1 point; registered composition bldg15 +0.7 and bldg11 -1.0, both CIs include 0). My hypothesis that the 5% floor explains bldg15's lower score is partly right: the change closes about a third of the gap to bldg11 (75.2% to 78.3%, bldg11 84.4%); the rest has another cause.
- **BOTH** inherits FAN's harm (bldg15 low-static visits 72.8% against LOW2's 78.3%).
Predictions: P1, P2, P3, P6, P8, P9, P10 held; P4 failed on minutes (accuracy -2.9 was inside 3), P5 failed (harm cells), P7 failed on its shared-rooms clause (accuracy clause held), P11 failed. Limits: the fan-off complaint counts (4 of 49-86, 2-4 of 8) and the visit shapes are mine; the fan check's 0.20 under low static is a placeholder; FAN and BOTH show wrong-and-confident of 8.9% against 0.0% on S1 at the same accuracy, i.e. those rooms sit close to the 0.95 line, so that percentage is fragile.

### A softer copy between rooms (exploratory; `SOFTCOPY_NOTES.md` hashed before any run, `study_softcopy.py`, report `results/docmismatch/softcopy_study/report.md`; all gates passed; predictions 6 of 8 held; post hoc `posthoc_softcopy.py`, `results/docmismatch/softcopy_study/posthoc.md`; nothing built into the demos or the pilot)

Today's routine copies an air-handler reading (and a box's abnormal static) into every later room on that handler as a certain, zero-minute measurement, which is what folds a room's own fault into "low static". SOFT replaces the copy with the joint model's running belief (each later room starts from the joint marginal given everything answered so far; nothing is entered as a measurement; static at the room's own box stays available as a check); JOINT also keeps that belief inside a room's own session. Same simulated worlds as before (real layouts bldg11, bldg15, bldg9; the first demo's 3 x 8 building). G5 confirms the claim behind it: for rooms that asked no air-handler check themselves, the session's belief equals the joint marginal to 5.6e-16.
- **Registered label: NO GAIN** for SOFT and for JOINT (Q2, folding on a small handler, and Q4, minutes within +10%, failed). JOINT is within 0.2 points of SOFT everywhere (Q8).
- **What it did, in the simulation's usual convention (an own-fault room reads NORMAL static at its own box), W0:** on the registered composition B accuracy +5.2 (bldg11), +4.8 (bldg15), +3.5 (bldg9); folded rooms (an own-fault room on the faulty handler) +46 / +44 / +33 points; wrong-and-confident on bldg11 6.8% to 1.8% without the hedge (-3.7 bldg15, -3.0 bldg9). No harm in the demo-shaped visits (+1.7, +1.4, -0.2), the first demo's S3 and S4 (+0.4, +1.0), the fan-off families (within 0.7). **Not free:** +39, +38, +43 minutes per visit on B (+18 to +20%) and +38, +13, +34 on the demo-shaped visits (+6 to +20%). Compared with the earlier blunt verification of every folded room on the same 100 bldg11 visits (+2.5 points for +42 minutes) it buys about twice the accuracy for the same time, because the belief decides who needs a reading.
- **Small handler (S5, 2-3 shared + 2 own-fault rooms on one 8-room handler):** folded rooms 0.0% to 3.5%, wrong-and-confident 41% to 34%: with 4-5 of 8 rooms complaining the joint model believes the handler is clearly faulty and keeps an own fault at about 3% per room; it does not fold less.
- **W1 (checks 25% worse):** the accuracy gain on B disappears (+0.3, -1.2, -0.7) while the minutes cost stays (+30 to +45); only the folded-room and confident-error improvements remain.
- **Post hoc, the part that matters:** under SOFT 75-89% of folded rooms take a box-level static reading of their own (10-16% under HARD). The gain is that verification, chosen by belief instead of forced, and it works only because the simulation lets an own-fault room read NORMAL static at its box. Under a harsher convention (static at any box on a faulty handler reads like the handler, the tool still believes the catalogue's rate for local causes) the gain is +1.3 / +1.0 / +0.5 points overall (the CI includes 0 on bldg9 and touches it on bldg15), folded rooms +5 / +6 / -2 points (CIs include 0), for +23 to +28 minutes, and the pilot hedge protects less: hedged wrong-and-confident on bldg11 W0 1.0% under HARD, 6.2% under SOFT, because the own reading counts as verification. Which convention is closer to a real building is NOT known: a low-static handler may lower inlet static at most of its boxes while only the saturated rooms complain. That is a question for a technician or for pilot readings (record static at the boxes of complaining AND silent rooms on a handler found low).

### The three open items: a fan-status confirm step, the lower-end gaps, a hedge for fan off (exploratory; `FANCONF_NOTES.md` hashed before any run, `study_fanconfirm.py`, report `results/docmismatch/fanconfirm_study/report.md`; all gates passed; predictions 5 of 8 held, three of them trivially; nothing adopted)

- **Confirm step: never fired, so the registered label ("not worth it as tested", C1 and C3 failed) says nothing about the idea.** On the three real Mortar layouts the recorded point map has no fan-status point (their air-handler checks are `bas_static`, `ahu_visit`, `ahu_gauge`), so the registered `bas_ahu_fan` is unavailable. On the first demo's building it exists and the routine already reads it before an upstream conclusion in every such visit (0 confirm reads and 0 skips in 30 visits each of S1, S2 and S3), so FANC equals FAN everywhere. G5 passed vacuously (largest count 0). What it did show: the fan-off mixture's false calls (4-6% of rooms on the real layouts) happen where the only check that separates fan off from low static is the physical `ahu_visit`; on the demo building, where fan status is read, false fan-off is 0.0-0.8%. The version that could work on the real layouts, a confirm by `ahu_visit` (a walk to the air handler), was tested next (section below).
- **Lower-end gaps.** (a) RW (the 5/15/50/90% levels with weights 40/20/20/20, no new level) captures 89% of LOW2's bldg15 gain (+2.8 against +3.1 points; L1 held): the gain is more weight on the low end, not the 2% level. RW also saves more time on the demo-shaped visits (163 / 215 / 197 minutes against TODAY's 188 / 239 / 207; LOW2 186 / 214 / 197) and on the registered composition is +1.2 on bldg11 where LOW2 is -1.0, but its wrong-and-confident on B bldg15 is 5.5% against TODAY's 4.0% (LOW2 4.5%). (b) On fan-off visits both raise wrong-and-confident by the same amount (bldg15 +8.4 LOW2, +8.2 RW; bldg9 +4.3, +4.2; L2 held): the harm comes from weight on low levels in general. If any lower-end change is wanted, RW is one line of weights; neither was adopted.
- **Hedge extended to fan off: H1 failed.** Where wrong-and-confident remains under FAN (A-FAN bldg15 1.6%, bldg9 1.3%) the fan rule changes nothing (1.6% to 1.6%, 1.3% to 1.3%); across all 12 cells it removes 2 rooms, and it hedges 25 of 2264 right conclusions (1%). The remaining confident errors are not fan-off conclusions made without an own static reading. My registered "52% of right conclusions hedged" mixed in the existing low-static hedge, which already hedges most low-static conclusions (e.g. 517 of 739 right ones on bldg11 under TODAY); the failure of the cut criterion does not depend on that flaw.
Predictions that held (C2, C4, C5) held because FANC equals FAN. Unrun: a confirm by `ahu_visit`; extending the hedge is not worth it as tested.

### A confirm step by a visit to the air handler (exploratory; `FANCONF2_NOTES.md` hashed before any run, `study_fanconfirm2.py`, report `results/docmismatch/fanconfirm2_study/report.md`; all gates passed, G5 this time not vacuous; FANV predictions 3 of 5 held, FANO 3 of 6; nothing adopted)

FANV = the fan-off mixture plus one `ahu_visit` (19 minutes in the catalogue; abnormal 0.92 under fan off, 0.10 under low static) before an upstream conclusion; FANO = only when the other of fan off / low static still has 5%.
- **Registered label: NOT WORTH IT AS TESTED** (FANV V1, V3 failed; FANO V1, V3, V6 failed). It fired (A-LS: 42, 17, 37 confirm visits in 200; demo S3: 77 of 100) and costs no net minutes over the fan-off mixture (extra minutes +0 pooled), but false fan-off calls did not move: A-LS bldg11 5.2% to 5.3%, bldg15 6.2% to 6.2%, bldg9 4.4% to 4.6%; accuracy against TODAY stays -5.3 / -4.0 / -3.6. The fan-off rooms in A-FAN do slightly better (87.4%, 76.5%, 81.6% against FAN's 85.8, 74.9, 81.1; V2 held).
- **Why (diagnosed, not registered):** on the real layouts the routine already takes `ahu_visit` in nearly every visit where static reads abnormal (143 of 200 on bldg11), since it is the only check that separates the two causes. EVERY visit that ends with a false fan-off call (16, 21 and 14 of 200) is a visit where `ahu_visit` was taken and read abnormal: the catalogue's 10% false-alarm rate of the walk under low static, one noisy reading. A second look cannot remove it (nothing independent exists on these layouts: no fan-status point; the simulator also returns the same answer to the same question). The false fan-off calls are the false-alarm rate of the one separating check, not a missing check.
- **Post hoc sensitivity (not registered; the world's false-alarm rate of `ahu_visit` under low static changed, the tool still believing 0.10; A-LS, W0, 200 visits per building):** false fan-off calls and FAN's accuracy against TODAY: at 0.10: 5.2 / 6.2 / 4.4% and -5.2 / -4.0 / -3.2 points; at 0.05: 2.5 / 2.7 / 2.8% and -2.5 / -0.5 / -1.7; at 0.02: 0.9 / 0.6 / 1.2% and -0.9 / +1.6 / -0.1. So the price of the fan-off mixture on low-static visits scales with how often a walk to a low-static air handler reads "abnormal"; with a real rate of a few percent it is close to free. That rate is a placeholder (0.10) and unmeasured: a technician or pilot question (when the fan is running but duct static is low, how often does a walk to the unit look abnormal?).

## Other choices that differ from `../live_demo` (all in `visit.py`)

- Candidate boxes for a wrong documented box are the nearest by id (`nearness="id"`, shipped and studied in Addenda 24-26): with 49 boxes per handler "same air handler" is no shortlist.
- Drawings rated `mostly_right` (prior 0.05 that the documented box is wrong), the live CLI's own default; the original demo server leaves the prior at 0.15.
- Context declared up front: control-system access, flow hood/gauge yes, occupant no, reheat yes (the Brick file lists a reheat valve command on these boxes).
- `min_rate = 0.02`, the live shipped default.

## Corrections to what I said earlier in the session

- bldg11's air handlers **do** have a recorded static-pressure point (9 of 9 serving handlers). I first said they had none, from a table cut to the four most common point classes.
- A bldg11 box's own "Command" point is the **reheat valve** command; the damper command lives on a separate Damper sub-node. I first treated "Command" as the damper command.
- Box-level reheat command is recorded on 45 of AHU06's 49 boxes, so bldg11 is not a "no heating points" building.

## Files

`build_building.py` Brick to building file (subset, recorded points only) · `scenario.json` the script · `world.py` the scripted answers · `visit.py` the visit on the real engine ·
`server.py`, `static/index.html` the UI · test: `../tests/test_live_demo_bldg11.py`
