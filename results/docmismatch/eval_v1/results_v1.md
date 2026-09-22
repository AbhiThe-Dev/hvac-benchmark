# Documentation-mismatch benchmark v1 — findings

**Research question.** Does the existing pretrained encoder (`results/pretrain/encoder`) help detect documentation mismatches when the wrong documentation is itself physically plausible and the physical evidence is sufficient to tell the truth?

## Bottom line

**No measurable benefit.** On plausible-but-wrong documentation with sufficient evidence (97 hard events, leave-one-topology-out), pretrained and no-pretrain encoders are indistinguishable (Δ AUROC −0.014, 95% CI [−0.047, 0.000] fine-tuned; −0.009, [−0.030, +0.006] frozen), and the same holds on the specified train-A+B → test-C split (Δ −0.025 [−0.083, +0.013]; +0.013 [−0.043, +0.073]). What *does* matter is the physical evidence: evidence-only beats documentation-structure-only by +0.41 AUROC (CI [+0.31, +0.49]).

This is a negative result about *this* encoder on *this* synthetic benchmark, and it is a predictable one: the encoder sees only documented topology, and the hard cases are built so that the documented topology is equally plausible either way. It should not be read as "pretraining can never help documentation auditing" (see Limitations).

## What the five success criteria look like after this build

| Question | Answer |
|---|---|
| How many genuinely distinct physical errors were tested? | **120 hard events**, each a distinct physical event (one row per `physical_event_id`; unit-tested). Independent-ish units are fewer: 9–20 leakage groups per family (Wrong AHU 9, Same-medium branch 11, VAV-zone 12, Parallel peer 16, Plant loop 20, Sensor 20). Only 2 topologies contribute plant-loop cases, and 1 of the 20 parallel-peer rows is plant equipment (the rest are coil swaps). See the diversity table below. |
| Were the wrong connections still plausible? | By construction yes (all Phase 7 filters pass on all 120; unit-tested). Verified empirically: on the 93 degree-preserving hard cases every structure-only method — including the pretrained decoder used zero-shot — scores **exactly 0.50 AUROC**. The 27 single-edge *retarget* cases are not clean: they change loop/AHU degrees, and structure-only models reach 0.67–0.72 on them (all of them alike, including random-init encoders). They are reported as a separate slice. |
| Was there enough evidence to identify the correct connection? | 97/120 hard cases are labelled observable (Phase 8). The label is predictive: evidence-only models reach AUROC **0.90 on observable** and **0.49 (chance) on the 23 ambiguous/unobservable** hard cases. Observable ≠ learnable, though: VAV-zone swaps have 9 observable cases but every model sits at 0.48–0.58 on that family. |
| Did the test topology differ from training? | Yes. Held-out topologies are never seen in training (unit-tested), and leakage groups never straddle train/val. **Caveat:** A, B, C, D share one building envelope; A–C share Chicago weather (D is Golden CO). "Held-out topology" means held-out HVAC arrangement and equipment population, not a held-out building. |
| Did the pretrained encoder actually improve results? | No (above). Easy cases (n=30, plausibility-confounded, not scored in the main claim) are saturated: AUROC ≥0.97 for every model that has an encoder input, LOTO-pooled. |

## Things that surprised me / that you should know before using the numbers

1. **Any encoder input, pretrained or not, lifts the specified split.** Train A+B → test C: evidence-only AUROC 0.72 (clean FP rate 0.93), random-init frozen encoder 0.88 (0.05), pretrained frozen 0.89 (0.03), scratch fine-tuned 0.90 (0.00), pretrained fine-tuned 0.88 (0.00). The random-init control is what shows this is not a pretraining effect; without it, "+0.16 AUROC from adding the encoder" would have looked like a win. I did not diagnose the mechanism. Under leave-one-topology-out (more training topologies) the gap disappears (0.90 vs 0.89–0.90).
2. **Clean false-positive rates are not trustworthy operating points.** Threshold = smallest value with zero false positives on validation clean cases, which are only 6 documents. Held-out clean FP rates range 0.00–1.00 by topology and model (topology B, ten constant-volume single-zone AHUs, is 1.00 for every model with AUROC 0.59–0.66 — a strong distribution shift, not a subtle one). Prefer AUROC and the by-topology table.
3. **A benchmark artifact was found and isolated.** Clean documentation of a topology is a single fixed graph, and single-edge retargets change degrees, so structure-only detectors get above-chance scores on retargets without any plausibility knowledge (0.67–0.72 for every structure-only method that uses an encoder or the pretrained decoder, random-init encoders included). The `degree_preserving` flag and the "structure-controlled" slices exist for this; the headline "hard" numbers include the retargets, the controlled slice excludes them, and the conclusion is the same either way.
4. **The evidence features are physics checks I wrote** (mass balance, heat balance, duty-cycle agreement, sensor-vs-heat-balance prediction). AUROC 1.00 on sensor mapping and same-medium branch means those physical identities are exact in EnergyPlus, so there is no headroom for an encoder on those families. Whether a model given raw time series would discover them is untested.
5. **Family headroom is uneven.** Perfectly solved by evidence: sensor mapping, same-medium branch (1.00), parallel peer (0.92–0.96). Partly: plant loop (0.75–0.80), wrong AHU (0.64–0.73, dragged down by topology B). Not solved: VAV↔zone swaps (~chance) — hourly BAS-like trends barely identify which VAV serves which zone.

## Limitations

- Everything is synthetic (EnergyPlus + injected paperwork errors). `real_world_verified = false` on every row. No claim about real documentation errors.
- Small n: LOTO observable slice has 97 events / 85 groups; spec-C has 30 events. The CIs above are the honest resolution; effects larger than roughly +0.03 (LOTO) or +0.07 (spec C, frozen) are excluded, smaller ones are not.
- The pretrained encoder was trained on 46 real Brick buildings and has never seen this benchmark's graph vocabulary conventions (e.g. loop → branch-valve → coil). Its embeddings may be off-distribution on these graphs; frozen and fine-tuned variants bracket that but don't fix it.
- One fixed training recipe for all variants; hyperparameters were not tuned per variant. Scale-free-feature sensitivity (bottom) gives the same conclusion (pretrained − no-pretrain within ±0.03 AUROC on LOTO).
- Observability audit takes the best of four evidence channels and knows the true owner (oracle). It says "the evidence contains the answer", not "a model can extract it".
- Robustness variants (same event, other time windows) were not generated; each event has one 6-week window and one noise seed.

## Phase 1 — is there real documented-vs-verified ground truth?

**No public case-level dataset was found.** Search results (not full-text verified; ScienceDirect and UCL Discovery returned 403 to the search agent):

- UCL One Pool Street (Wang, Lilis, Katsigarakis, Mavrokapnidis, Korolija, Rovas, EC3 2024; related Energy & Buildings 325 (2024) 115035 and an Applied Energy paper on HVAC topology completeness). They reconstruct HVAC topology from incomplete IFC-BIM and compare it with design drawings; that is documentation vs. reconstructed documentation, not field-verified truth, and the data appears to be on request only. I did not confirm what the two Zenodo records contain.
- Commissioning / RCx case studies (DOE FEMP, PNNL, LBNL): narrative performance faults; no per-case as-built-vs-field connectivity found.
- BAS point verification / metadata inference (Fürst et al. large-scale AHU metadata inference; automated tagging work): labels are human-tagged points, so they measure inference accuracy, not documentation error against field truth.
- Torabi et al. (Building and Environment 2022, VAV AHU control human errors): taxonomy from literature + 11 practitioner interviews, no case data.
- Brick/Mortar/Haystack: models are documentation-derived; the Brick-tagged LBNL FDD set was checked against diagrams (docs vs docs).
- LBNL FDD and similar fault datasets are fault-detection labels and were **not** counted as documentation-error data.

Worth emailing: the One Pool Street authors (Meng Wang, Georgios Lilis, Dimitrios Rovas, Ivan Korolija) about whether any reported topology discrepancy was site-verified; Torabi/Gunay/O'Brien (Carleton); Mortar/Brick maintainers about audited models; LBNL commissioning researchers.

## Phase 2 — how 4 events became 16 rows, and why it cannot recur here

`symptom_pipeline/output/causal_batch_v1_summary.json`: 6 `reassign_coil` events on `sys07_vav_reheat` were attempted, 4 simulated cleanly (2 gave EnergyPlus severe errors), and each carried `n_report_variants: 4`, giving `n_dataset_records: 16`. All 4 events move a heating coil onto the same chilled-water pump (`corruption_kind: "misattributed"`), the split was a single degenerate bucket, and the summary itself says so. The 16 rows were 4 physical events × 4 report-wording variants.

This benchmark differs in three ways: (1) the building is never rewired — corruptions edit documentation only, so no simulation can fail because of a corruption and every family is available; (2) `physical_event_id` is unique per row (unit test `test_one_row_per_physical_event`), and wording/time-window variants are not generated; (3) `sys07` alone has 1 AHU and 1 loop per medium, so wrong-AHU, plant-loop and peer-equipment cases are impossible there. Two vendored multi-AHU fixtures (`multiple_airloops`, `multiple_loops_w_plenums`) were inspected and rejected because both AHUs serve the same 10 zones; two valid topologies were built instead (see README).


---
# Generated tables (from results/docmismatch/eval/*.json)

## Benchmark composition

| Topology | Hard | Easy | Clean | Total |
|---|---|---|---|---|
| A `sys07_vav_reheat` (1 AHU, 10 VAV, 1 HW + 1 CHW loop; vendored) | 19 | 7 | 8 | 34 |
| B `sys03_psz_ac` (10 single-zone AHUs, no plant; vendored) | 29 | 8 | 8 | 45 |
| C `vav_2ahu_2loops` (2 AHUs, 2 HW + 2 CHW loops; built) | 36 | 7 | 8 | 51 |
| D `vav_3ahu_2loops` (3 AHUs, 2 HW + 2 CHW loops, Golden CO climate; built) | 36 | 8 | 8 | 52 |
| **Total** | 120 | 30 | 32 | 182 |

## Diversity audit (Phase 12)

Every row is a distinct physical event (one row per event; no paraphrases, no re-windowed duplicates). 'Substitutions' counts distinct (topology, true owner -> documented owner) pairs; 'Components' counts distinct equipment nodes touched.

| Family | Rows | Base topologies | Distinct targets | Distinct components | Distinct replacement endpoints | Distinct substitutions | Leakage groups | Degree-preserving rows | Subtypes |
|---|---|---|---|---|---|---|---|---|---|
| Wrong AHU | 20 | 3 | 17 | 31 | 13 | 32 | 9 | 12 | retarget:8, swap:12 |
| VAV-zone swap | 20 | 4 | 32 | 64 | 32 | 40 | 12 | 20 | swap:20 |
| Plant loop | 20 | 2 | 21 | 27 | 6 | 21 | 20 | 1 | retarget:19, swap:1 |
| Sensor mapping | 20 | 4 | 40 | 80 | 40 | 40 | 20 | 20 | vav_dat:15, ahu_sat:5 |
| Same-medium branch | 20 | 3 | 31 | 62 | 31 | 40 | 11 | 20 | branch_coil:20 |
| Parallel peer swap | 20 | 4 | 35 | 67 | 32 | 40 | 16 | 20 | coil_ahu:9, coil_vav:10, loop_source:1 |

Candidate funnel (proposed -> passing every hard filter): Wrong AHU 75 -> 41; VAV-zone swap 180 -> 36; Plant loop 28 -> 22; Sensor mapping 229 -> 222; Same-medium branch 203 -> 52; Parallel peer swap 241 -> 76.

## Observability (Phase 8)

| Family | observable | ambiguous | unobservable |
|---|---|---|---|
| Wrong AHU | 20 | 0 | 0 |
| VAV-zone swap | 9 | 5 | 6 |
| Plant loop | 12 | 4 | 4 |
| Sensor mapping | 20 | 0 | 0 |
| Same-medium branch | 20 | 0 | 0 |
| Parallel peer swap | 16 | 1 | 3 |

## Headline: Specified split: train on A+B, test on held-out topology C

Mean ± sd over 5 training seeds. Threshold fixed on validation only (smallest threshold with 0 false positives on validation clean cases). 'bal.' = negatives re-weighted to 50% prevalence (chance AUPRC = 0.5).

**Hard mismatches with sufficient physical evidence (primary)** — 30 corrupted vs 8 clean

| Model | F1 (bal.) | AUROC | AUPRC (bal.) | Recall | Clean FP rate |
|---|---|---|---|---|---|
| Evidence only (no encoder) | 0.64 ±0.02 | 0.72 ±0.02 | 0.81 ±0.01 | 0.91 ±0.07 | 0.93 ±0.10 |
| Evidence + random-init encoder, frozen  [no pretrain] | 0.80 ±0.02 | 0.88 ±0.02 | 0.92 ±0.02 | 0.71 ±0.03 | 0.05 ±0.06 |
| Evidence + pretrained encoder, frozen  [pretrained] | 0.82 ±0.03 | 0.89 ±0.01 | 0.92 ±0.01 | 0.71 ±0.05 | 0.03 ±0.05 |
| Evidence + scratch encoder, fine-tuned  [no pretrain] | 0.84 ±0.01 | 0.90 ±0.01 | 0.94 ±0.01 | 0.73 ±0.01 | 0.00 |
| Evidence + pretrained encoder, fine-tuned  [pretrained] | 0.78 ±0.03 | 0.88 ±0.01 | 0.93 ±0.01 | 0.64 ±0.04 | 0.00 |
| Documentation structure only (no encoder, no evidence) | 0.00 | 0.50 | 0.50 | 0.00 | 0.00 |
| Pretrained decoder, zero-shot (masked edge) | 0.67 | 0.63 | 0.63 | 1.00 | 1.00 |
| Structure + random-init encoder, frozen | 0.00 | 0.57 ±0.07 | 0.58 ±0.06 | 0.00 | 0.00 |
| Structure + pretrained encoder, frozen | 0.27 ±0.33 | 0.61 ±0.02 | 0.61 ±0.02 | 0.40 ±0.49 | 0.40 ±0.49 |
| Structure + scratch encoder, fine-tuned | 0.00 | 0.63 | 0.63 | 0.00 | 0.00 |
| Structure + pretrained encoder, fine-tuned | 0.00 | 0.61 ±0.04 | 0.62 ±0.03 | 0.00 | 0.00 |

**All hard mismatches** — 36 corrupted vs 8 clean

| Model | F1 (bal.) | AUROC | AUPRC (bal.) | Recall | Clean FP rate |
|---|---|---|---|---|---|
| Evidence only (no encoder) | 0.63 ±0.02 | 0.68 ±0.02 | 0.77 ±0.01 | 0.89 ±0.07 | 0.93 ±0.10 |
| Evidence + random-init encoder, frozen  [no pretrain] | 0.75 ±0.02 | 0.82 ±0.02 | 0.88 ±0.01 | 0.63 ±0.04 | 0.05 ±0.06 |
| Evidence + pretrained encoder, frozen  [pretrained] | 0.75 ±0.03 | 0.82 ±0.01 | 0.88 ±0.01 | 0.62 ±0.04 | 0.03 ±0.05 |
| Evidence + scratch encoder, fine-tuned  [no pretrain] | 0.78 ±0.01 | 0.85 ±0.01 | 0.91 ±0.01 | 0.63 ±0.01 | 0.00 |
| Evidence + pretrained encoder, fine-tuned  [pretrained] | 0.72 ±0.03 | 0.83 ±0.01 | 0.89 ±0.01 | 0.56 ±0.03 | 0.00 |
| Documentation structure only (no encoder, no evidence) | 0.00 | 0.50 | 0.50 | 0.00 | 0.00 |
| Pretrained decoder, zero-shot (masked edge) | 0.67 | 0.67 | 0.67 | 1.00 | 1.00 |

**Easy mismatches (sanity check; plausibility-confounded)** — 7 corrupted vs 8 clean

| Model | F1 (bal.) | AUROC | AUPRC (bal.) | Recall | Clean FP rate |
|---|---|---|---|---|---|
| Evidence only (no encoder) | 0.68 ±0.02 | 0.91 ±0.02 | 0.93 ±0.02 | 1.00 | 0.93 ±0.10 |
| Evidence + random-init encoder, frozen  [no pretrain] | 0.95 ±0.03 | 0.97 ±0.04 | 0.98 ±0.02 | 0.94 ±0.07 | 0.05 ±0.06 |
| Evidence + pretrained encoder, frozen  [pretrained] | 0.99 ±0.02 | 1.00 | 1.00 | 1.00 | 0.03 ±0.05 |
| Evidence + scratch encoder, fine-tuned  [no pretrain] | 0.94 ±0.03 | 0.97 ±0.03 | 0.98 ±0.02 | 0.89 ±0.06 | 0.00 |
| Evidence + pretrained encoder, fine-tuned  [pretrained] | 0.97 ±0.04 | 1.00 | 1.00 | 0.94 ±0.07 | 0.00 |
| Documentation structure only (no encoder, no evidence) | 0.60 | 0.71 | 0.71 | 0.43 | 0.00 |
| Pretrained decoder, zero-shot (masked edge) | 0.67 | 0.93 | 0.93 | 1.00 | 1.00 |

## Headline: Specified split: same model, second held-out topology D

Mean ± sd over 5 training seeds. Threshold fixed on validation only (smallest threshold with 0 false positives on validation clean cases). 'bal.' = negatives re-weighted to 50% prevalence (chance AUPRC = 0.5).

**Hard mismatches with sufficient physical evidence (primary)** — 31 corrupted vs 8 clean

| Model | F1 (bal.) | AUROC | AUPRC (bal.) | Recall | Clean FP rate |
|---|---|---|---|---|---|
| Evidence only (no encoder) | 0.66 ±0.01 | 0.80 ±0.03 | 0.87 ±0.02 | 0.94 ±0.04 | 0.90 ±0.09 |
| Evidence + random-init encoder, frozen  [no pretrain] | 0.75 ±0.04 | 0.85 ±0.02 | 0.90 ±0.01 | 0.70 ±0.09 | 0.17 ±0.15 |
| Evidence + pretrained encoder, frozen  [pretrained] | 0.79 ±0.04 | 0.85 ±0.03 | 0.90 ±0.02 | 0.66 ±0.05 | 0.00 |
| Evidence + scratch encoder, fine-tuned  [no pretrain] | 0.77 ±0.04 | 0.86 ±0.01 | 0.90 ±0.01 | 0.66 ±0.03 | 0.05 ±0.06 |
| Evidence + pretrained encoder, fine-tuned  [pretrained] | 0.74 ±0.03 | 0.85 ±0.02 | 0.89 ±0.01 | 0.59 ±0.04 | 0.00 |
| Documentation structure only (no encoder, no evidence) | 0.00 | 0.50 | 0.50 | 0.00 | 0.00 |
| Pretrained decoder, zero-shot (masked edge) | 0.67 | 0.42 | 0.48 | 1.00 | 1.00 |
| Structure + random-init encoder, frozen | 0.00 | 0.47 ±0.01 | 0.51 ±0.02 | 0.00 | 0.00 |
| Structure + pretrained encoder, frozen | 0.27 ±0.33 | 0.46 ±0.02 | 0.50 ±0.01 | 0.40 ±0.49 | 0.40 ±0.49 |
| Structure + scratch encoder, fine-tuned | 0.00 | 0.47 ±0.01 | 0.53 | 0.00 | 0.00 |
| Structure + pretrained encoder, fine-tuned | 0.00 | 0.44 ±0.03 | 0.50 ±0.02 | 0.00 | 0.00 |

**All hard mismatches** — 36 corrupted vs 8 clean

| Model | F1 (bal.) | AUROC | AUPRC (bal.) | Recall | Clean FP rate |
|---|---|---|---|---|---|
| Evidence only (no encoder) | 0.65 ±0.02 | 0.74 ±0.03 | 0.83 ±0.02 | 0.91 ±0.03 | 0.90 ±0.09 |
| Evidence + random-init encoder, frozen  [no pretrain] | 0.70 ±0.04 | 0.79 ±0.02 | 0.86 ±0.01 | 0.63 ±0.09 | 0.17 ±0.15 |
| Evidence + pretrained encoder, frozen  [pretrained] | 0.72 ±0.03 | 0.78 ±0.03 | 0.86 ±0.02 | 0.57 ±0.04 | 0.00 |
| Evidence + scratch encoder, fine-tuned  [no pretrain] | 0.70 ±0.04 | 0.79 ±0.01 | 0.85 ±0.01 | 0.57 ±0.02 | 0.05 ±0.06 |
| Evidence + pretrained encoder, fine-tuned  [pretrained] | 0.67 ±0.03 | 0.78 ±0.02 | 0.85 ±0.01 | 0.51 ±0.03 | 0.00 |
| Documentation structure only (no encoder, no evidence) | 0.00 | 0.50 | 0.50 | 0.00 | 0.00 |
| Pretrained decoder, zero-shot (masked edge) | 0.67 | 0.46 | 0.53 | 1.00 | 1.00 |

**Easy mismatches (sanity check; plausibility-confounded)** — 8 corrupted vs 8 clean

| Model | F1 (bal.) | AUROC | AUPRC (bal.) | Recall | Clean FP rate |
|---|---|---|---|---|---|
| Evidence only (no encoder) | 0.69 ±0.02 | 1.00 | 1.00 | 1.00 | 0.90 ±0.09 |
| Evidence + random-init encoder, frozen  [no pretrain] | 0.91 ±0.08 | 0.99 ±0.02 | 0.99 ±0.02 | 0.97 ±0.05 | 0.17 ±0.15 |
| Evidence + pretrained encoder, frozen  [pretrained] | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 |
| Evidence + scratch encoder, fine-tuned  [no pretrain] | 0.93 ±0.06 | 0.99 ±0.01 | 0.99 ±0.01 | 0.93 ±0.10 | 0.05 ±0.06 |
| Evidence + pretrained encoder, fine-tuned  [pretrained] | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 |
| Documentation structure only (no encoder, no evidence) | 0.67 | 0.75 | 0.75 | 0.50 | 0.00 |
| Pretrained decoder, zero-shot (masked edge) | 0.67 | 0.75 | 0.80 | 1.00 | 1.00 |

## Headline: Leave-one-topology-out, pooled over the four held-out topologies (each case scored by a model that never saw its topology)

Mean ± sd over 5 training seeds. Threshold fixed on validation only (smallest threshold with 0 false positives on validation clean cases). 'bal.' = negatives re-weighted to 50% prevalence (chance AUPRC = 0.5).

**Hard mismatches with sufficient physical evidence (primary)** — 97 corrupted vs 32 clean

| Model | F1 (bal.) | AUROC | AUPRC (bal.) | Recall | Clean FP rate |
|---|---|---|---|---|---|
| Evidence only (no encoder) | 0.76 ±0.01 | 0.90 ±0.01 | 0.93 ±0.01 | 0.98 ±0.01 | 0.65 ±0.02 |
| Evidence + random-init encoder, frozen  [no pretrain] | 0.81 ±0.04 | 0.89 ±0.01 | 0.92 ±0.01 | 0.98 ±0.01 | 0.50 ±0.12 |
| Evidence + pretrained encoder, frozen  [pretrained] | 0.81 ±0.03 | 0.89 ±0.01 | 0.92 ±0.01 | 0.98 | 0.50 ±0.09 |
| Evidence + scratch encoder, fine-tuned  [no pretrain] | 0.85 | 0.90 ±0.01 | 0.93 | 0.92 ±0.02 | 0.33 ±0.03 |
| Evidence + pretrained encoder, fine-tuned  [pretrained] | 0.85 ±0.01 | 0.89 ±0.01 | 0.92 ±0.01 | 0.94 ±0.01 | 0.35 ±0.02 |
| Documentation structure only (no encoder, no evidence) | 0.07 ±0.08 | 0.50 | 0.50 | 0.06 ±0.07 | 0.10 ±0.12 |
| Pretrained decoder, zero-shot (masked edge) | 0.17 | 0.52 | 0.53 | 0.32 | 0.25 |
| Structure + random-init encoder, frozen | 0.00 | 0.53 ±0.01 | 0.54 ±0.01 | 0.00 | 0.00 |
| Structure + pretrained encoder, frozen | 0.01 ±0.01 | 0.53 ±0.01 | 0.53 | 0.00 ±0.01 | 0.00 |
| Structure + scratch encoder, fine-tuned | 0.00 | 0.53 | 0.54 | 0.00 | 0.00 |
| Structure + pretrained encoder, fine-tuned | 0.03 ±0.07 | 0.52 ±0.01 | 0.53 | 0.05 ±0.09 | 0.05 ±0.10 |

**All hard mismatches** — 120 corrupted vs 32 clean

| Model | F1 (bal.) | AUROC | AUPRC (bal.) | Recall | Clean FP rate |
|---|---|---|---|---|---|
| Evidence only (no encoder) | 0.73 ±0.01 | 0.82 ±0.01 | 0.87 ±0.01 | 0.91 | 0.65 ±0.02 |
| Evidence + random-init encoder, frozen  [no pretrain] | 0.76 ±0.03 | 0.82 ±0.01 | 0.87 ±0.01 | 0.89 ±0.02 | 0.50 ±0.12 |
| Evidence + pretrained encoder, frozen  [pretrained] | 0.77 ±0.02 | 0.82 ±0.01 | 0.88 ±0.01 | 0.91 ±0.01 | 0.50 ±0.09 |
| Evidence + scratch encoder, fine-tuned  [no pretrain] | 0.78 | 0.82 ±0.01 | 0.88 ±0.01 | 0.82 ±0.02 | 0.33 ±0.03 |
| Evidence + pretrained encoder, fine-tuned  [pretrained] | 0.78 ±0.01 | 0.81 ±0.02 | 0.87 ±0.01 | 0.84 ±0.01 | 0.35 ±0.02 |
| Documentation structure only (no encoder, no evidence) | 0.07 ±0.08 | 0.50 | 0.50 | 0.06 ±0.08 | 0.10 ±0.12 |
| Pretrained decoder, zero-shot (masked edge) | 0.17 | 0.54 | 0.55 | 0.30 | 0.25 |

**Easy mismatches (sanity check; plausibility-confounded)** — 30 corrupted vs 32 clean

| Model | F1 (bal.) | AUROC | AUPRC (bal.) | Recall | Clean FP rate |
|---|---|---|---|---|---|
| Evidence only (no encoder) | 0.77 ±0.01 | 0.98 ±0.01 | 0.99 | 1.00 | 0.65 ±0.02 |
| Evidence + random-init encoder, frozen  [no pretrain] | 0.82 ±0.04 | 0.98 | 0.99 | 1.00 | 0.50 ±0.12 |
| Evidence + pretrained encoder, frozen  [pretrained] | 0.82 ±0.03 | 0.97 ±0.01 | 0.99 | 1.00 | 0.50 ±0.09 |
| Evidence + scratch encoder, fine-tuned  [no pretrain] | 0.88 ±0.01 | 0.98 ±0.01 | 0.99 ±0.01 | 1.00 | 0.33 ±0.03 |
| Evidence + pretrained encoder, fine-tuned  [pretrained] | 0.87 ±0.01 | 0.98 ±0.01 | 0.99 ±0.01 | 1.00 | 0.35 ±0.02 |
| Documentation structure only (no encoder, no evidence) | 0.74 ±0.02 | 0.82 | 0.81 | 0.66 ±0.03 | 0.10 ±0.12 |
| Pretrained decoder, zero-shot (masked edge) | 0.49 | 0.85 | 0.87 | 0.50 | 0.25 |

## By corruption family (AUROC, leave-one-topology-out pooled)

| Model | Wrong AHU | VAV-zone swap | Plant loop | Sensor mapping | Same-medium branch | Parallel peer swap |
|---|---|---|---|---|---|---|
| Evidence only (no encoder) | 0.73 | 0.49 | 0.80 | 1.00 | 1.00 | 0.94 |
| Evidence + random-init encoder, frozen  [no pretrain] | 0.66 | 0.54 | 0.80 | 1.00 | 1.00 | 0.93 |
| Evidence + pretrained encoder, frozen  [pretrained] | 0.64 | 0.58 | 0.80 | 1.00 | 1.00 | 0.92 |
| Evidence + scratch encoder, fine-tuned  [no pretrain] | 0.71 | 0.50 | 0.75 | 1.00 | 1.00 | 0.96 |
| Evidence + pretrained encoder, fine-tuned  [pretrained] | 0.65 | 0.48 | 0.76 | 1.00 | 1.00 | 0.94 |
| Documentation structure only (no encoder, no evidence) | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 |
| Pretrained decoder, zero-shot (masked edge) | 0.50 | 0.50 | 0.72 | 0.50 | 0.50 | 0.50 |

Rows per family slice: Wrong AHU 20, VAV-zone swap 20, Plant loop 20, Sensor mapping 20, Same-medium branch 20, Parallel peer swap 20; clean negatives are the held-out topology's own (family slices share them).

## By held-out topology (hard AUROC / clean FP rate), leave-one-topology-out

| Model | A | B | C | D |
|---|---|---|---|---|
| Evidence only (no encoder) | 0.83 / 1.00 | 0.66 / 1.00 | 0.88 / 0.38 | 0.90 / 0.23 |
| Evidence + random-init encoder, frozen  [no pretrain] | 0.87 / 0.45 | 0.61 / 1.00 | 0.89 / 0.35 | 0.89 / 0.20 |
| Evidence + pretrained encoder, frozen  [pretrained] | 0.91 / 0.40 | 0.59 / 1.00 | 0.89 / 0.45 | 0.90 / 0.15 |
| Evidence + scratch encoder, fine-tuned  [no pretrain] | 0.86 / 0.00 | 0.65 / 1.00 | 0.86 / 0.28 | 0.89 / 0.03 |
| Evidence + pretrained encoder, fine-tuned  [pretrained] | 0.85 / 0.00 | 0.60 / 1.00 | 0.86 / 0.33 | 0.89 / 0.07 |

## Observable vs not-observable vs degree-controlled slices (AUROC, leave-one-topology-out pooled)

| Model | Observable (n=97) | Ambiguous + unobservable (n=23) | Degree-preserving (structure-controlled) (n=93) | Observable AND degree-preserving (n=78) | Retargets (degree shift; structure-confounded) (n=27) |
|---|---|---|---|---|---|
| Evidence only (no encoder) | 0.90 | 0.49 | 0.82 | 0.89 | 0.85 |
| Evidence + random-init encoder, frozen  [no pretrain] | 0.89 | 0.52 | 0.81 | 0.88 | 0.85 |
| Evidence + pretrained encoder, frozen  [pretrained] | 0.89 | 0.55 | 0.82 | 0.87 | 0.85 |
| Evidence + scratch encoder, fine-tuned  [no pretrain] | 0.90 | 0.48 | 0.82 | 0.89 | 0.82 |
| Evidence + pretrained encoder, fine-tuned  [pretrained] | 0.89 | 0.47 | 0.80 | 0.87 | 0.82 |
| Documentation structure only (no encoder, no evidence) | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 |
| Pretrained decoder, zero-shot (masked edge) | 0.52 | 0.63 | 0.50 | 0.50 | 0.67 |
| Structure + random-init encoder, frozen | 0.53 | 0.60 | 0.50 | 0.50 | 0.70 |
| Structure + pretrained encoder, frozen | 0.53 | 0.63 | 0.50 | 0.50 | 0.71 |
| Structure + scratch encoder, fine-tuned | 0.53 | 0.63 | 0.50 | 0.50 | 0.72 |
| Structure + pretrained encoder, fine-tuned | 0.52 | 0.63 | 0.50 | 0.50 | 0.68 |

## Does pretraining help? Paired group-bootstrap of Δ AUROC (pretrained − no-pretrain)

Resampling leakage groups (2000 draws); case scores averaged over 5 seeds. Positive Δ = pretrained better. CI excluding 0 = distinguishable from no effect.

| Comparison | Slice | View | AUROC (first) | AUROC (second) | Δ | 95% CI |
|---|---|---|---|---|---|---|
| Evidence + pretrained FT − evidence + scratch FT | hard_observable | LOTO pooled | 0.890 | 0.905 | -0.014 | [-0.047, +0.000] |
| Evidence + pretrained FT − evidence + scratch FT | hard_observable | train A+B → test C | 0.879 | 0.904 | -0.025 | [-0.083, +0.013] |
| Evidence + pretrained FT − evidence + scratch FT | hard | LOTO pooled | 0.816 | 0.831 | -0.016 | [-0.048, +0.009] |
| Evidence + pretrained FT − evidence + scratch FT | hard | train A+B → test C | 0.830 | 0.851 | -0.021 | [-0.068, +0.016] |
| Evidence + pretrained FT − evidence + scratch FT | hard_degree_preserving | LOTO pooled | 0.813 | 0.836 | -0.023 | [-0.060, +0.007] |
| Evidence + pretrained FT − evidence + scratch FT | hard_degree_preserving | train A+B → test C | 0.901 | 0.896 | +0.005 | [-0.027, +0.038] |
| Evidence + pretrained FT − evidence + scratch FT | hard_observable_dp | LOTO pooled | 0.877 | 0.893 | -0.016 | [-0.055, +0.000] |
| Evidence + pretrained FT − evidence + scratch FT | hard_observable_dp | train A+B → test C | 0.926 | 0.926 | +0.000 | [-0.028, +0.032] |
| Evidence + pretrained frozen − evidence + random frozen | hard_observable | LOTO pooled | 0.893 | 0.902 | -0.009 | [-0.030, +0.006] |
| Evidence + pretrained frozen − evidence + random frozen | hard_observable | train A+B → test C | 0.892 | 0.879 | +0.013 | [-0.043, +0.073] |
| Evidence + pretrained frozen − evidence + random frozen | hard | LOTO pooled | 0.825 | 0.833 | -0.008 | [-0.032, +0.013] |
| Evidence + pretrained frozen − evidence + random frozen | hard | train A+B → test C | 0.833 | 0.826 | +0.007 | [-0.057, +0.076] |
| Evidence + pretrained frozen − evidence + random frozen | hard_degree_preserving | LOTO pooled | 0.813 | 0.827 | -0.013 | [-0.039, +0.010] |
| Evidence + pretrained frozen − evidence + random frozen | hard_degree_preserving | train A+B → test C | 0.917 | 0.917 | +0.000 | [-0.025, +0.023] |
| Evidence + pretrained frozen − evidence + random frozen | hard_observable_dp | LOTO pooled | 0.875 | 0.888 | -0.013 | [-0.037, +0.000] |
| Evidence + pretrained frozen − evidence + random frozen | hard_observable_dp | train A+B → test C | 0.943 | 0.943 | +0.000 | [-0.024, +0.025] |
| Structure + pretrained FT − structure + scratch FT | hard_observable | LOTO pooled | 0.526 | 0.531 | -0.005 | [-0.019, +0.000] |
| Structure + pretrained FT − structure + scratch FT | hard_observable | train A+B → test C | 0.633 | 0.633 | +0.000 | [+0.000, +0.000] |
| Structure + pretrained FT − structure + scratch FT | hard | LOTO pooled | 0.546 | 0.550 | -0.004 | [-0.015, +0.000] |
| Structure + pretrained FT − structure + scratch FT | hard | train A+B → test C | 0.667 | 0.667 | +0.000 | [+0.000, +0.000] |
| Structure + pretrained FT − structure + scratch FT | hard_degree_preserving | LOTO pooled | 0.500 | 0.500 | +0.000 | [+0.000, +0.000] |
| Structure + pretrained FT − structure + scratch FT | hard_degree_preserving | train A+B → test C | 0.500 | 0.500 | +0.000 | [+0.000, +0.000] |
| Structure + pretrained FT − structure + scratch FT | hard_observable_dp | LOTO pooled | 0.500 | 0.500 | +0.000 | [+0.000, +0.000] |
| Structure + pretrained FT − structure + scratch FT | hard_observable_dp | train A+B → test C | 0.500 | 0.500 | +0.000 | [+0.000, +0.000] |
| Structure + pretrained frozen − structure + random frozen | hard_observable | LOTO pooled | 0.515 | 0.526 | -0.010 | [-0.032, +0.000] |
| Structure + pretrained frozen − structure + random frozen | hard_observable | train A+B → test C | 0.633 | 0.633 | +0.000 | [+0.000, +0.000] |
| Structure + pretrained frozen − structure + random frozen | hard | LOTO pooled | 0.537 | 0.546 | -0.008 | [-0.025, +0.000] |
| Structure + pretrained frozen − structure + random frozen | hard | train A+B → test C | 0.667 | 0.667 | +0.000 | [+0.000, +0.000] |
| Structure + pretrained frozen − structure + random frozen | hard_degree_preserving | LOTO pooled | 0.500 | 0.500 | +0.000 | [+0.000, +0.000] |
| Structure + pretrained frozen − structure + random frozen | hard_degree_preserving | train A+B → test C | 0.500 | 0.500 | +0.000 | [+0.000, +0.000] |
| Structure + pretrained frozen − structure + random frozen | hard_observable_dp | LOTO pooled | 0.500 | 0.500 | +0.000 | [+0.000, +0.000] |
| Structure + pretrained frozen − structure + random frozen | hard_observable_dp | train A+B → test C | 0.500 | 0.500 | +0.000 | [+0.000, +0.000] |
| Evidence + pretrained FT − evidence only | hard_observable | LOTO pooled | 0.890 | 0.907 | -0.017 | [-0.059, +0.008] |
| Evidence + pretrained FT − evidence only | hard_observable | train A+B → test C | 0.879 | 0.738 | +0.142 | [-0.053, +0.345] |
| Evidence + pretrained FT − evidence only | hard | LOTO pooled | 0.816 | 0.827 | -0.011 | [-0.055, +0.030] |
| Evidence + pretrained FT − evidence only | hard | train A+B → test C | 0.830 | 0.705 | +0.125 | [-0.092, +0.346] |
| Evidence + pretrained FT − evidence only | hard_degree_preserving | LOTO pooled | 0.813 | 0.820 | -0.007 | [-0.058, +0.043] |
| Evidence + pretrained FT − evidence only | hard_degree_preserving | train A+B → test C | 0.901 | 0.854 | +0.047 | [-0.125, +0.221] |
| Evidence + pretrained FT − evidence only | hard_observable_dp | LOTO pooled | 0.877 | 0.897 | -0.021 | [-0.071, +0.010] |
| Evidence + pretrained FT − evidence only | hard_observable_dp | train A+B → test C | 0.926 | 0.864 | +0.062 | [-0.113, +0.247] |
| Evidence + pretrained frozen − evidence only | hard_observable | LOTO pooled | 0.893 | 0.907 | -0.014 | [-0.069, +0.021] |
| Evidence + pretrained frozen − evidence only | hard_observable | train A+B → test C | 0.892 | 0.738 | +0.154 | [-0.044, +0.353] |
| Evidence + pretrained frozen − evidence only | hard | LOTO pooled | 0.825 | 0.827 | -0.002 | [-0.062, +0.056] |
| Evidence + pretrained frozen − evidence only | hard | train A+B → test C | 0.833 | 0.705 | +0.128 | [-0.085, +0.342] |
| Evidence + pretrained frozen − evidence only | hard_degree_preserving | LOTO pooled | 0.813 | 0.820 | -0.007 | [-0.075, +0.068] |
| Evidence + pretrained frozen − evidence only | hard_degree_preserving | train A+B → test C | 0.917 | 0.854 | +0.062 | [-0.095, +0.227] |
| Evidence + pretrained frozen − evidence only | hard_observable_dp | LOTO pooled | 0.875 | 0.897 | -0.022 | [-0.088, +0.016] |
| Evidence + pretrained frozen − evidence only | hard_observable_dp | train A+B → test C | 0.943 | 0.864 | +0.080 | [-0.075, +0.250] |
| Evidence only − structure only (does physical evidence matter?) | hard_observable | LOTO pooled | 0.907 | 0.500 | +0.407 | [+0.309, +0.485] |
| Evidence only − structure only (does physical evidence matter?) | hard_observable | train A+B → test C | 0.738 | 0.500 | +0.238 | [+0.062, +0.391] |
| Evidence only − structure only (does physical evidence matter?) | hard | LOTO pooled | 0.827 | 0.500 | +0.327 | [+0.226, +0.412] |
| Evidence only − structure only (does physical evidence matter?) | hard | train A+B → test C | 0.705 | 0.500 | +0.205 | [+0.024, +0.366] |
| Evidence only − structure only (does physical evidence matter?) | hard_degree_preserving | LOTO pooled | 0.820 | 0.500 | +0.320 | [+0.199, +0.424] |
| Evidence only − structure only (does physical evidence matter?) | hard_degree_preserving | train A+B → test C | 0.854 | 0.500 | +0.354 | [+0.192, +0.479] |
| Evidence only − structure only (does physical evidence matter?) | hard_observable_dp | LOTO pooled | 0.897 | 0.500 | +0.397 | [+0.279, +0.488] |
| Evidence only − structure only (does physical evidence matter?) | hard_observable_dp | train A+B → test C | 0.864 | 0.500 | +0.364 | [+0.204, +0.492] |

## Sensitivity: scale-free features (absolute log-error columns removed)

Same pipeline, same seeds; only the evidence feature set changes. AUROC / clean FP rate on observable hard cases.

| Model | LOTO pooled | spec C | spec D |
|---|---|---|---|
| Evidence only (no encoder) | 0.90 / 0.67 | 0.66 / 0.90 | 0.69 / 0.93 |
| Evidence + random-init encoder, frozen  [no pretrain] | 0.88 / 0.63 | 0.87 / 0.12 | 0.84 / 0.57 |
| Evidence + pretrained encoder, frozen  [pretrained] | 0.87 / 0.55 | 0.83 / 0.38 | 0.85 / 0.45 |
| Evidence + scratch encoder, fine-tuned  [no pretrain] | 0.88 / 0.38 | 0.89 / 0.05 | 0.84 / 0.42 |
| Evidence + pretrained encoder, fine-tuned  [pretrained] | 0.87 / 0.46 | 0.88 / 0.00 | 0.83 / 0.35 |
