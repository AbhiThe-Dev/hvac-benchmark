# photo_guide: photo-annotated, step-by-step help for ONE check

A technician (or a beginner) picks the check they are doing, photographs the equipment, and gets 3-7 plain-language steps drawn on their own photo, one step at a time, ending with "what normal looks like / what not normal looks like" and a Normal / Not normal answer (the same two words the main tool's reading checks use).

**Status: prototype, standalone.** Nothing in `pilot/` or `doc_mismatch/` imports this, and this imports nothing from them at run time. The check list is a snapshot (`checks.json`, built by `scripts/snapshot_checks.py` from the main catalogue). **Not validated:** whether the model puts marks on the right parts, and whether the steps are correct and safe in the field. See "What is and isn't tested".

## Run it
```bash
cp photo_guide/.env.example photo_guide/.env     # then put ANTHROPIC_API_KEY in it (git-ignored)
.venv/bin/python photo_guide/server.py           # http://localhost:8745; from a phone on the same Wi-Fi use this Mac's address
.venv/bin/python photo_guide/server.py --fake    # canned answers, no key: checks the screens only (port 8746)
cd photo_guide && ../.venv/bin/python -m guide.cli --check power_24vac photo.jpg --out out/try1
```
Model: `GUIDE_MODEL` (default `claude-haiku-4-5-20251001`). Every run is saved to `out/runs/<id>/` (photo, annotated images, `guidance.json`) and the in-app "mark is on the wrong thing" / "confusing" / answer buttons append to `out/feedback.jsonl`. All local and git-ignored. Photos are re-encoded without EXIF/GPS before being sent to the API.

## How it works
- `guide/prompt.py`: system prompt (beginner wording, safety rules) + per-check user text. Only the check's one-line text, family, and reading quantity/unit/normal band are sent. No cause names, rates or reasoning (same rule as `pilot/vision_extract.py`; a test enforces it).
- `guide/schema.py`: the forced `record_guidance` tool and its strict validation. Marks are points/boxes on a 0-1000 grid over the photo, clamped, so they never depend on the resize.
- `guide/render.py`: Pillow draws numbered marks + short labels; one overview image and one image per step (that step bold, the rest of the photo dimmed).
- Safety: the hazard text per check (electric / moving / hot / height) is fixed in `prompt.py` and shown before the photo and again before step 1; the model can only add a **stop** (then no steps are shown).
- Beginner flow: a check that needs something not in the photo (a control-system command, a tool) becomes an unmarked step and a "you need" item; a photo that doesn't show the part gets a "retake" hint instead of guesses.

## What is and isn't tested
- `.venv/bin/pytest photo_guide/tests`: schema, renderer, prompt leakage, model-call retry, API, upload rejection, all with a fake model. These do **not** show the real model's output is good.
- `eval/run_eval.py` scores real model output on photos you label (`eval/labels.json`, format in the file's docstring): verdict as expected, marks on a labelled part, step length, jargon candidates. Reading the annotated images is still required: a mark inside a labelled part is not proof it is the right part for that step.
- Not done: any field trial, any expert review of the steps. Do not hand to a real technician before an HVAC expert has read a sample of outputs.

## First live results (2026-10-16): 11 Wikimedia Commons photos, 14 cases, hand-labelled
Photos: `eval/photos/` (attribution in `ATTRIBUTION.md`); labels: `eval/labels.json`; outputs and annotated images: `eval/results/<model>/`. Small, clean stock photos; **no VAV box photo was available**, so the main equipment is untested. Labels were written before the runs; three "BAD" cases are disputed (below) and were NOT re-labelled afterwards.

| | Haiku 4.5 | Sonnet 5.5 |
|---|---|---|
| verdict as expected (help / retake / stop) | 6/14 | 11/14 |
| photos given steps | 0 of 8 expected | 4 of 8 expected |
| marks on a labelled part (loose: any labelled part counts) | n/a (no marks) | 17/19 |

- **Haiku 4.5 is not usable for this.** After the coordinate fix it asked for a retake on every photo; before it, it invented parts and put marks in the wrong place. It also gave a beginner 24 V meter steps for a 230 V actuator.
- **Sonnet 5.5** localised well (marks viewed by hand on 05, 06, 07, 08: on the thermostat screen and setpoint digits, the fan-drive box, the round switch, the outside-air hood and damper flaps), refused the 230 V actuator ("Do not measure this unit"), and stopped on both exposed-wiring photos. It still gives steps for only half the photos where I expected steps.
- **Disputed misses:** 01 (an actuator lying loose on a table, asked for a damper-linkage check), 03 (a furnace board, asked for a VAV controller check), 04 (a thermostat's back plate) were all "retake". The model is arguably right on each; my expectations were generous.
- **Sonnet 5.5 rejects forced tool use** (`tool` and `any`); `llm.py` falls back to `auto` and retries once if no tool call comes back.
- **Bugs the eval found and fixed:** the model marks in image PIXELS, not a 0-1000 grid, so the prompt now states the photo size and the code converts; `null` text fields rejected whole answers; overview labels collided (overview now numbers only).
- **Still open:** steps run past the 20-word limit (about half of Sonnet's steps); stray punctuation in unused fields; each call takes roughly 10-20 s; one run per model, so no estimate of run-to-run variation.

## Joining the main model later
`checks.json` rows carry the same `name`/`words` as `CheckV1`, and the final Normal/Not normal tap maps to the check's `reading` word. The hook would be `pilot/engine_adapter.selectable_checks` plus the `in_progress` stage in `pilot/static/index.html`; none of that is touched yet.
