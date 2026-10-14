# What the pilot records

One **case** is one complaint room in one visit. Everything about it is stored in `cases` (the context entered once, up
front) and `case_event` (an append-only log of what happened, in order). The technician can see all of it for any case
in the app ("View everything recorded for this case"); the in-app notice (`cases.NOTICE`) says the same in plain words.

The sequence this dataset exists for, and the part to protect most carefully:

> complaint → diagnostic checks → check results → time per check → confirmed root cause → successful repair

A case is `complete` in an export only if it has every link of that chain (see **Completeness**).

## The 16 fields

| # | Field | Stored in | Entered by | When |
|---|---|---|---|---|
| 1 | Initial complaint | `visits.feel`, `visits.airflow`; `cases.complaint_text`, `complaint_source` | technician | start of visit |
| 2 | Building and system context | `cases.building_type`, `system_kind`, `equipment_age_band`; AHU/VAV/room ids in the building file | technician (+ photo read) | start of visit |
| 3 | Initial readings | `cases.readings_json` (text with units), `alarms_text`; the BAS photo (kept on the server) | technician | start of visit |
| 4 | Possible causes considered | technician: `cases.own_hypotheses_json`. Tool: `suggestion_shown.ranked` (top 5 causes with probabilities, every step) | technician / automatic | before any tool output / at each reveal |
| 5 | Every check performed | `check_result`, `external_result` events (and `room_log` for the engine) | technician | per check |
| 6 | Order of checks | `case_event.seq` (and the step number in exports) | automatic | per event |
| 7 | Result of each check | `check_result.word` (+ `reading_text`, `note`); `external_result.result_text` | technician | per check |
| 8 | Time per check, incl. walking/setup | `check_started.server_ts` → `check_result.server_ts`; optional `minutes_correction` beside it | automatic (+ optional correction) | per check |
| 9 | What the technician would check next | `intent` event, recorded **before** the suggestion is revealed | technician | each step |
| 10 | Software's recommended next check | `suggestion_shown`: check, target, text, modeled minutes, `p_pos`, gain, why, ranked causes | automatic | each reveal |
| 11 | Followed or rejected, and why | `decision`: `follow` / `substitute` / `external` / `skip` + reason chip + note; `check_result.followed_suggestion` | technician | each step |
| 12 | Final confirmed root cause | `root_cause.cause_id` (+ `text` if "something else"), `in_taxonomy`, `agrees_with_tool` | technician | after the visit or later |
| 13 | How it was confirmed | `root_cause.how_confirmed`, and for "saw it"/"measured it" whether that was before the repair: `root_cause.confirmed_before_repair`. Graded by the **verification ladder** (below). | technician | with 12 |
| 14 | Repair performed | `repair`: action chips, text, `repaired_on` | technician | when done |
| 15 | Did the repair fix it | `outcome.fixed` (yes / partial / no / unknown) | technician | when known |
| 16 | Repeat within 7/30 days | `followup` events; `followup_due` holds the dates; `cases.prior_case_id` links a return visit to the earlier case | technician (or developer) | day 7 and day 30 after a fix |

Also stored per case: `participant_id` (role, years in HVAC, VAV experience; bands only), `data_version`, and
`catalogue_hash`, a fingerprint of the checks, minutes, `min_rate`, cause shares and the joint model (severity mixture by default, or `PILOT_JOINT_MODEL=shipped`) that produced the recommendations.
The recommendation is **stored when it is shown**, not recomputed later, because the engine replays against whatever
the catalogue is today.

## Events

`case_event` rows are never updated or deleted (SQLite triggers abort both). A correction is a new row.

| kind | payload |
|---|---|
| `intent` | `choice` (`check` / `other` / `unsure`), `check`, `target`, `text` |
| `suggestion_shown` | `check`, `target`, `text`, `minutes` (modeled), `p_pos`, `gain`, `why`, `ranked` [{cause, id, p}], `free_via_memo`, `intent_matches` |
| `decision` | `action`, `reason`, `note`, `suggested` {check, target}, and `check`/`target` or `external_text`; for `skip`, `room_log_id` |
| `check_started` | `check`, `target`, `external` |
| `check_result` | `check`, `target`, `text` (the wording shown, kept for the re-check screen), `word`, `reading_text`, `note`, `minutes_correction`, `modeled_minutes`, `followed_suggestion`, `room_log_id`, `started_event_id` |
| `external_result` | `external_text`, `result_text`, `note`, `minutes_correction`, `started_event_id` |
| `question_answer` | `key`, `answer`, `room_log_id` (a yes/no the tool needed before it could suggest a check) |
| `tool_conclusion` | `cause`, `id`, `text`, `belief`, `forced`, `modeled_minutes`, `checks` (once per case) |
| `root_cause` | `cause_id`, `text`, `in_taxonomy`, `how_confirmed`, `confirmed_before_repair` (true / false / null), `actual_box` (only when the drawings were wrong), `tool_cause_id`, `agrees_with_tool` |
| `repair` | `actions`, `text`, `repaired_on` |
| `outcome` | `fixed`, `note` |
| `post_repair_check` | `of_event_id` (the original `check_result`), `check`, `target`, `before_word`, `before_reading_text`, `result` (`now_ok` / `still_wrong` / `unsure`), `reading_text`, `note` |
| `followup` | `window_days`, `recurred`, `note`, `recorded_by` (`technician` / `developer`) |

If a field is recorded more than once (e.g. the root cause is revised), the **latest** event is the current answer and
earlier ones stay as history.

## How to read it honestly

- **The tool influences the sequence.** Once the suggestion is shown, a technician who follows it is partly following
  the tool. That is why `intent` is captured first: `suggested.intent_matches` and the step's `intent_matched_action`
  (both are columns in `checks.csv`) compare what they would have done unprompted with what the tool said and what they did. Without the intent step, "followed the
  suggestion" would be uninterpretable.
- **`modeled_minutes` are placeholders**, not measurements (`minutes_source = PLACEHOLDER` in the catalogue). Measured
  `seconds` are the first real calibration data for them.
- **Time starts when the technician taps "Doing this check"**, so walking and setup are in it only if they tap when they
  set off. `minutes_correction` exists for the times they did not. The raw timestamps are never overwritten.
- **`agrees_with_tool` is `null`** when the tool's conclusion was too coarse to name a part (`doc_acts_fail`,
  `doc_other`) or the technician could not determine the cause. It is only true/false when both named a cause.
- **`in_taxonomy = false`** means the real cause is outside the tool's cause list (e.g. refrigeration-side, which the
  tool does not model). Counting these measures the taxonomy's coverage.
- **n is tiny** (one participant at a time, about a week). Treat this as calibration and a check on question order,
  not validation of accuracy.
- **A complaint room that the tool concluded instantly** (e.g. from a fan reading carried over from the room before)
  has few or no checks of its own; that is the shared-cause saving, not missing data.

## Completeness

An export's `complete` is true only when all five hold (`completeness` shows which):

1. `complaint`: free text, or a hot/cold answer
2. `timed_check`: at least one check with a measured start-to-result time
3. `root_cause`: a confirmed cause that is not "couldn't determine"
4. `repair`: a repair was recorded
5. `confirmed_fixed`: the outcome is `yes` (a "partly" is not counted)

## The verification ladder

How far a case's root-cause label was actually checked. It is **computed from the events** (`pilot/ladder.py`, no stored
state), so it applies to every case, and the app, the record view and the export share one definition. It is four
independent pieces of evidence, not a strict order:

| Rung | Granted when |
|---|---|
| `suspected` | a cause is named (not "couldn't determine") |
| `physically_confirmed` | the fault was **seen or measured**, and the technician said that was **before the repair** |
| `repair_confirmed` | a real repair was made and the outcome is `yes` ("partly" does not count) |
| `stayed_fixed` | `repair_confirmed`, and a 7- or 30-day follow-up says it did not come back (and none says it did) |

`level` is the highest rung reached (0 = no cause named, 1 suspected, 2 physically confirmed before repair, 3 repair
confirmed, 4 stayed fixed). A case can be level 3 without ever being physically confirmed: suspected, replaced the
part, it worked. That is real evidence, but it is a different kind of evidence, so the rungs are kept separate.

**A rung is never granted on inference.** "Measured it" with no answer to "was that before you repaired anything?" is
**not** counted as before the repair (it is flagged `pre_repair_unknown`, and every case recorded before this field
existed reads that way). "The repair fixed it" is a repair result and is stored as after the repair. "Ruled out the
others" and "another tech told me" are not physical. These are the technician's own statements, not independently checked.

`caveats` say what weakens an otherwise-granted rung, so you can choose how strict to be:

| Caveat | Meaning |
|---|---|
| `pre_repair_unknown` / `physical_confirmation_after_repair` | measured or saw it, but not stated to be before the repair / stated to be only after |
| `multi_action_repair` | more than one real repair action; the fix cannot be pinned on one cause |
| `repair_did_not_fix` / `repair_partly_fixed` / `outcome_unknown` | a repair was made and the outcome was not a clear yes. `repair_did_not_fix` is evidence **against** the named cause. |
| `recheck_contradicts_fix` | recorded as fixed, but a test that found the fault still fails when repeated after the repair |
| `recurred_within_7_days` / `_30_days` | a follow-up says it came back; the fix did not hold |
| `cause_revised` | the technician changed which cause it was (history is kept; the latest counts) |
| `no_repair_made` / `fixed_without_repair` / `repair_text_only` | "what was done" recorded no actual repair / the complaint cleared with no repair recorded / the repair is only described in words |
| `fixed_without_named_cause` | recorded as fixed, but no cause was named |

## The one-tap re-check (before / after, on the same test)

After a repair, the close-out screen offers each test in the case that **found something** (an "abnormal" or "yes" result,
up to the three most recent) and asks one thing: *"It's fine now / Still wrong / Couldn't tell"*. An optional reading can be
typed with it. That is the before/after: the same test, before and after, with no typing needed.

- **Before** is the original result, already stored. **After** is a `post_repair_check` event linked to it.
- **It is never fed to the engine.** The engine refuses a repeat of a check it already has, and a re-check is not new
  diagnostic evidence about the cause. The reasoning and the visit replay are untouched.
- **A repair must be recorded first**: a "fine now" before any repair would mean nothing. Only a test that found something
  in *this* case can be re-checked.
- **The answers are neutral on purpose** ("fine now", not "no"), because for many checks "yes" means *fault found* and would
  read backwards after a repair.
- **Latest answer per test wins; earlier ones stay** as history (a first re-check "still wrong" and a later one "fine" are both kept).
- **It can only add a caveat.** "Still wrong" after "fixed: yes" gives `recheck_contradicts_fix` (a warning, not a verdict:
  the rung stays, because the outcome is still recorded). "Fine now" never grants a rung; it only changes the wording to "and
  the re-check agrees". Like "fixed: yes", it is the technician's own answer, just tied to a specific test.
- **Limits.** A case the tool concluded from a reading carried over from another room has no test of its own to repeat. A test
  that needs a trip back to the equipment costs a trip back. Zone temperature is a poor "after" (about an hour to settle);
  box-level airflow against setpoint or damper against command respond in minutes. Cases recorded before the wording was
  stored fall back to the check's code name on the re-check card.

**The ladder and `complete` answer different questions.** `complete` is whether the chain of records exists
(complaint, a timed check, a confirmed cause, a repair, a confirmed fix). The ladder is how far to trust the label. A
room the tool concluded instantly from a reading carried over from the room before has no timed check of its own, so it
can reach level 4 and still not be `complete`.

## System topology (`pilot/topology.py`, in the export as `topology`)

Almost all of it needs **nothing from the technician**: it is read from the confirmed building file and from events that
already exist. The one exception is a single optional question, asked only when they record that the drawings were wrong.

| Part | What it is | Where it comes from |
|---|---|---|
| `documented` | the drawings' claim for the room: AHU, box, room; the other boxes and rooms **seen** on that AHU; which BAS point types exist (AHU, box, zone temperature, reheat); how many of this visit's complaint rooms share the AHU | the building file (photo read, edited and confirmed on the confirm screen) |
| `reheat` | what the technician declared when asked, the system-type chip, and whether a reheat point exists. These can disagree, and that is left visible. | `question_answer`, `cases.system_kind`, the building file |
| `evidence` | what the checks that bear on "which box serves this room" said | `check_result` events |
| `verified` | were the drawings **wrong / right / suspected_wrong / unverified**, on what `basis`, which `actual_box`, and whether sources `conflict` | technician, duct trace, tool |

**How `evidence` is read.** `duct_trace` ("trace the duct from the diffuser: is it that box?") is a *direct* test of the
layout; a "no" means not that box. `override_room` and `override_diffuser` (command a box, watch the room) are *indirect*: a
"yes" is good evidence that box serves the room, but a "no" is **inconclusive**, because a dead actuator looks identical to
a wrong box. 'Couldn't tell' and skipped checks are not evidence.

**How `verified` is decided** (and what it refuses to do):
- The technician recording "the drawings were wrong" gives `wrong` (basis `technician`), with their `actual_box` if they named
  one (a box, `not_listed`, or `not_sure`). A duct trace that found another box fills it in if they did not.
- Otherwise a **duct trace** decides: "yes" on the drawings' box is `right`; "no" is `wrong`; "yes" on a different box is `wrong`.
- Otherwise, if the tool concluded the drawings were wrong, it is only `suspected_wrong` (basis `tool`). The tool's claim and
  the box it named are kept separately in `tool_claim`.
- **Never inferred from an unrelated cause.** Confirming a failed actuator does not make the drawings `right`. Commanding checks
  alone never set the status. If the technician and a duct trace disagree, `conflict` is true and the technician's statement wins.

**Limits you should know**
- **The counts are of what was photographed or confirmed on the confirm screen ("seen"), not a survey.** An air handler serving
  20 boxes shows however many were in the photo.
- **Not captured: duct branches and which boxes share one, upstream/downstream order along a trunk, the plant, where the
  static-pressure sensor sits.** The building file holds only AHU, box, room claims and BAS points, and technicians rarely know
  the rest. Capturing them would need real questions.
- **Most cases will be `unverified`.** Topology is only verified when the tool asks a topology-verifying test, or the technician
  finds the drawings were wrong. Expect `documented` and `reheat` to be filled for nearly every case and `verified` for few.
- **Re-identification.** Aliases are per visit and all names are masked, but a distinctive set of counts plus building type and
  dates can narrow down a building. Treat the topology block with the same care as the rest.

## How this is tested

`tests/test_pilot_e2e.py` runs a **simulated technician** against the real HTTP endpoints, in the order the frontend calls them, on a
controlled clock, and keeps its own log of everything it did. It then checks the stored record against that log: no event lost,
duplicated or reordered; start-to-result time equal to the time that passed (even when the device clock lies); what was shown is what was
stored; the ladder matches the evidence given; follow-ups fall +7/+30 days from the fix; the export matches (and masks exact building
names, emails and phones); a restored backup exports byte-for-byte what the live system does; a purge removes one participant and leaves
another's record unchanged; a restart mid-visit changes nothing; racing requests and double taps neither duplicate nor corrupt; and a
battery of malformed and out-of-order requests never returns a 500 or leaves a partial write. It also measures per-tap latency on a
20- and a 49-room visit (about 8 ms).

It found two real bugs, both fixed: `advance` could move on from a room that had not concluded (silently abandoning a complaint room;
now it needs a concluded room and the caller names the room it is leaving), and an out-of-range id in a URL raised instead of answering
"not found". What it does **not** cover: a real technician, the real vision and email services, the Docker image build, a deployment on
Fly, or the frontend's appearance (checked by hand in a browser, not by the tests).

## Handling

| | |
|---|---|
| Where it lives | `pilot.db` (SQLite, WAL) and `visits/` on the Fly volume at `/data`. Photos in `uploads/`. |
| Backup | `python -m pilot.scripts.backup` (see its docstring). Online-consistent, verified, restorable. **Nothing runs it automatically**; until you run it, the volume is the only copy. |
| Export | `python -m pilot.scripts.export_cases`, on your machine against a backup. Writes `cases.jsonl`, `cases.csv` (one row per case: completeness and ladder), `checks.csv` (one row per step). No HTTP export endpoint. |
| Follow-ups | the app asks the technician; `python -m pilot.scripts.followups list|record` is for chasing and for answers given outside the app |
| Next participant | `python -m pilot.scripts.followups new-participant` |
| Deletion / withdrawal | `python -m pilot.scripts.purge case <id>` or `participant <id>`. Dry run unless `--execute`. Removes a visit (or a participant's visits) from every table and from disk, then vacuums. Leaves an audit row with counts only. See below. |
| Anonymization | at export only. Equipment, room and BAS point names → per-visit aliases; emails and phone numbers masked; photos, raw vision output and file paths never exported. `--drop-free-text` removes every free-text field. |

### What is *not* protected (be aware before recruiting)

- **Free text is not made safe by pattern.** A name typed into a note survives an export without `--drop-free-text`.
- **Photos are stored unmodified on the server** (EXIF stripped, otherwise as taken) and can show building names.
- **Deleting here does not delete copies.** `purge` removes the live database and disk. It cannot reach backup
  tarballs you already made, exports you already wrote, or Fly volume snapshots (pass `--backups <folder>` to have it list
  the tarballs that still hold the data). If you promise withdrawal, decide what you will do about those copies first.
- **Any valid session can read any case by id.** Fine while one participant is active and the developer relays every
  login; not fine if several people share the deployment.
- **The append-only triggers stop the app and scripts from editing events, not someone with the database file.**
- **Deploying mid-visit breaks the open page** for that technician (the step payload changed shape). Deploy between visits.
- The technician's notice describes this app's recording. `outreach/ONE_PAGER.md` describes tickets and ride-alongs and
  does not mention per-check timing; per-check timing can read as performance monitoring, so say it up front.

## Withdrawal and deletion (`scripts/purge.py`)

```
python -m pilot.scripts.purge list
python -m pilot.scripts.purge participant 3                       # dry run: prints the plan, changes nothing
python -m pilot.scripts.purge participant 3 --orphan-intakes --reason withdrawal_request --execute --backups ~/pilot-backups
python -m pilot.scripts.purge case 12 --reason data_error --execute
```

- **A case is purged with its whole visit**, because the rooms of one visit share a building file, photos and vision
  output. A visit that holds cases of two different participants is refused rather than split.
- **Per visit it removes:** the cases, every `case_event`, follow-up dates, the engine's `room_log` and conclusions, the
  visit row, its intake rows (raw vision output), and its folder and photos on disk. `participant` also removes the
  participant record. Another case's "return visit for…" link to a purged case is cleared.
- **The append-only triggers** are dropped and restored inside one transaction. If anything fails the whole purge rolls
  back, triggers included, and files are only removed after the database commit.
- **It is real deletion:** the script checkpoints and truncates the write-ahead log and vacuums the file; a test plants
  text in one participant's data and proves it is gone from the raw database bytes while another participant's survives.
- **Unconfirmed intakes** (photos read, no visit started) cannot be tied to a participant. They are listed and kept;
  `--orphan-intakes` also deletes the ones made during that participant's time. Check they are theirs first.
- **`--reason` is a fixed list** (`withdrawal_request`, `data_error`, `test_data`, `other`), not free text, so the audit
  row (`purge_log`: when, scope, id, reason, counts) cannot be a place a name gets typed.
- Deletion is irreversible, and the script deliberately takes no backup first (that would make a new copy).


## The hedge on low-static conclusions

A room whose leading cause is low duct static and that has no box-level static reading of its own (the zero-minute copy of another room's reading does not count) is shown as "Explained by low static, own fault not ruled out" with its confidence capped at 90% (`HEDGE_CAP`), never as "Diagnosed". The `tool_conclusion` event then carries `hedged: true`, `raw_belief` (the model's own number; `belief` is what the technician saw) and `hedge_rule_out` (the check at the room or box, never at the air handler, that would sharpen the picture most per minute, or null). It changes no check and no leading answer: it is a safety measure, not an accuracy one (live_demo_bldg11/README.md).
