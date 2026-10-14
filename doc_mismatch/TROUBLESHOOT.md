# Technician-guided troubleshooting: working model v0

A question-and-answer helper for a call-out. The technician says where the problem is; the tool suggests **one check at a time** ("command box 2-05 to full cooling and check the diffuser"), the technician answers yes / no / unsure / skip, and the tool updates its belief until one cause is clear. **It uses no trend data.** It is built to be shown to technicians and to have its numbers replaced by theirs, not to be believed.

**Working model v1** (a wider cause tree and check catalogue, explicit data tiers, declared context, numeric readings, a discrepancy log) is in [TROUBLESHOOT_V1.md](TROUBLESHOOT_V1.md). It sits beside v0 and does not change it; nothing below is affected.

## Run it

```bash
.venv/bin/python doc_mismatch/scripts/61_troubleshoot.py                 # interactive, made-up example building
.venv/bin/python doc_mismatch/scripts/61_troubleshoot.py --demo          # a simulated technician answers: an illustration, not a result
.venv/bin/python doc_mismatch/scripts/61_troubleshoot.py --building my.json --member Room-204 --airflow no --strategy split_half
.venv/bin/python -m pytest doc_mismatch/tests/test_troubleshoot.py
```

## What it needs from a building

An equipment list (id, type, optionally area and tag) and the drawings' claims, in one JSON file ([example](examples/troubleshoot_example/building.json)). The claims may be wrong or out of date: they are what is being checked. Candidates for "who really feeds it" are the equipment of the right type, same area first (nearness prior). Nothing else.

## What the technician types

The location of the complaint (1), optionally whether air is coming out of the diffuser (1), then one answer per check, plus one entry for each extra piece of equipment they add. The session counts them (`Session.entries`). A six-check session is about 7 entries.

## Causes and checks it knows about

| Question | Causes | Checks |
|---|---|---|
| Room -> box (`vav_zone`) | documented box is wrong (which one), something unlisted, box feeds it but does not act (actuator / damper), box feeds it and acts (cause is elsewhere: outside v0) | box override and watch the room, box override and watch the diffuser, duct trace, confirm the box moves |
| Box -> air handler (`ahu_vav`) | documented handler is wrong (which one), something unlisted, documented handler is right | drop the handler's fan speed and watch the box, duct trace |

## What is assumed (all editable in `Settings`)

| Number | Value | Source |
|---|---|---|
| P(documented feeder is wrong) | 0.15, of which 10% is unlisted equipment | placeholder |
| P(documented box feeds it but does not act) | 0.15 (x3 if no air at the diffuser, /3 if there is) | placeholder |
| Nearness prior | a candidate outside the documented box's area counts 0.25 of one inside | placeholder |
| Hit / false-alarm rates: `override_room` | 0.98 / 0.03 | **measured in simulation** (PREREGISTRATION_DR.md Addendum 16, 30+ minute window) |
| Hit / false-alarm rates: everything else | 0.90-0.98 / 0.02-0.10 | placeholder (`duct_trace` from `active/physical.py`, itself assumed) |
| Minutes per check (access + do + wait) | e.g. override_room 6 + 2 + 30, override_diffuser 6 + 2 + 3, duct_trace 10 + 15 | placeholder |
| Stop when one cause reaches | 0.95 | placeholder |

Change any of them with `Settings(...)` or `settings.with_check("vav_zone", "duct_trace", access_min=3)`. The interviews are meant to replace them.

**Drawings rating (experimental, off by default).** `python -m docmismatch.troubleshoot --drawings mostly_right|mixed|poor` (or `settings.with_drawings(level)`) sets only the prior that the documented box is wrong: 5%, 15% (the default, `mixed`) or 30%. The levels are placeholders. In simulation (PREREGISTRATION_DR.md Addendum 21) `mostly_right` saved about 7-9% of the minutes at almost no cost in accuracy, even when the drawings were somewhat worse than rated, while `poor` made the tool 24-45% slower (about 0.8 more checks) in every world for a small gain in accuracy and fewer confidently wrong answers. The frozen decision was NOT WORTH OFFERING AS BUILT; the default stays `mixed`. Whether technicians can rate drawings at all is untested. A follow-up (Addendum 22) tested a one-way switch (only `mostly_right`, 5%): it saved 7-9% of the minutes with at most 1.2 points more confident wrong answers when the tool's checks are as reliable as assumed (even if left on in every building), but when checks are worse than assumed it added 1-4 points of confident wrong answers; the frozen decision was CONDITIONAL ON RELIABLE CHECKS. A 10% level made no difference at all. Nothing restricts `--drawings` to the one-way form yet.

## How a check is chosen

`entropy` (default): the check with the most expected information about the cause per minute, given the current belief and the technician's location (a check at the place they already are has no access time). `split_half`: the check whose answer is closest to a coin flip, per minute; it trusts the prior less, which literature on weak priors suggests is safer (see research_notes). `random` is a reference. No check is offered twice; "unsure" spends the time and learns nothing; "skip" spends nothing and is not offered again.

## What it does not do

- Cover causes beyond the ones above: setpoints, sensors, capacity and every other equipment fault are one lump ("cause is elsewhere").
- Use trends, alarms or FDD output. (The trend-based evidence engine in `active/` and `evidence.py` is a separate, optional layer for buildings that have data.)
- Run checks in parallel while waiting (the 30-minute room response could be spent on other checks), or price disruption to occupants.
- Repeat a noisy check, or accept a numeric reading (yes / no observations only).
- Use the full 8-question symptom form of `symptom_pipeline`: only the airflow question is wired in.

## With only the minimum data

The tool needs only an equipment list and the drawings' claim for the complaining room. In simulation (PREREGISTRATION_DR.md Addendum 23) that minimum, with no air-handler grouping, behaved almost exactly like the grouped setting: about 38 minutes, 91-96% accuracy and 2% confident wrong answers, with the same accuracy edge over a fast guesser and the same speed edge over a slow careful one (both stand-ins are my constructions, not real technicians). What it cannot do is find a wrong feeder that is not on the candidate list it was given: in buildings with more than about 85 boxes, 6-12% of visits ended with "none of these boxes" when the list was an arbitrary 40. Narrowing the search (by area, or by tracing the duct) is what recovers those; a trace-and-read-the-tag check is not built yet.

## Weighting candidates by id distance (optional)

`python -m docmismatch.troubleshoot --nearness id [--id-decay 4]` (or `Settings(nearness="id", id_decay=4.0)`) builds the candidate list from the documented box and the boxes nearest to it in natural id order (digit runs compare as numbers) and weights each by exp(-distance / decay), instead of ranking by shared air handler. It needs only the equipment list and the claims. The decay is a placeholder. In simulation (PREREGISTRATION_DR.md Addendum 25) it made a long candidate list useful and did no harm when wrong feeders were nowhere near the documented box, but how much it helps depends entirely on whether real documentation errors sit near the documented box in id order, which is unknown: if wrong feeders were adjacent rooms it added 3-7 points of visits ending with a named cause; if they were merely on the same air handler, about half a point. In 24 of the 25 campus layouts checked the ids embed the room number; conventions elsewhere will differ. The default is unchanged (`nearness="area"`).

## Validation status

Unit tests only (`tests/test_troubleshoot.py`, checked against deliberately broken versions), plus a simulated-technician demo. **Nothing has been tried with a real technician, and no claim is made that it saves time.** `sim.simulate_habit` is an ASSUMED stand-in for trial and error, not observed behaviour. A comparison of the tool with that stand-in, across a grid of priors, costs and wrong assumptions, needs to be pre-registered before it is run.
