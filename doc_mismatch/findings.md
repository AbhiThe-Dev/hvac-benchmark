# Documentation-mismatch benchmark — findings (v2, corrected 2026-09-21)

> **v2 notice.** The v1 report's specified-split numbers, clean false-positive rates and topology-B result were affected by three pipeline defects. They are fixed here; v1 tables are kept in `results/docmismatch/eval_v1/` and the section "v2 corrections" (bottom) shows every stage. The two headline conclusions of v1 survive, and are slightly stronger. Two v1 explanations were wrong and are corrected below.

**Research question.** Does the existing pretrained encoder (`results/pretrain/encoder`) help detect documentation mismatches when the wrong documentation is itself physically plausible and the physical evidence is sufficient to tell the truth? And does physical evidence beat documentation structure on *real* data, not just simulation?

## Bottom line

1. **Pretraining: no measurable benefit, now with a tighter interval.** Leave-one-topology-out, 91 hard cases with sufficient evidence: pretrained − no-pretrain Δ AUROC **+0.004 [−0.006, +0.017]** fine-tuned and **+0.004 [−0.008, +0.020]** frozen (v1: −0.014 [−0.047, 0.000]). Specified split (n=20): −0.019 [−0.073, 0.000] / −0.006 [−0.035, 0.000]. No comparison excludes zero; larger effects than about +0.02 (LOTO) are excluded.
2. **Physical evidence beats documentation structure on simulated data: +0.438 AUROC [+0.324, +0.497]** LOTO (v1 +0.407). Structure-only is exactly 0.50 on every degree-preserving hard case.
3. **On real field data the advantage holds but is meaningfully weaker and narrower.** ORNL FRP RTU-VAV data (real, 14 days, 1-minute), an untrained coupling-based evidence rule reaches AUROC **0.70 [0.65, 0.76]** against 0.50 for structure-only (Δ +0.20 [+0.15, +0.26]); the *same rule* on the simulated benchmark gets 0.79 [0.71, 0.85]. It is strong for point-to-equipment mapping (0.83) and near chance for which-VAV-serves-which-room (0.58). See "Real-data test".

## What was corrected, and what it changed

| # | Defect in v1 | What was actually wrong | Fix | Effect |
|---|---|---|---|---|
| 1 | Specified-split "any encoder lifts AUROC 0.72 -> 0.88" | I had attributed it to the encoder path; then to extrapolation on the `loop_*` slots. The precise cause: the head was scored on feature *regimes* it never saw (e.g. `loop_branch` rows *with* an alternative owner when A+B training had none, and, in the other direction, rows *without* alternatives when training always had them). Evidence-only extrapolated arbitrarily there; heads with extra parameters happened to extrapolate differently. | Row-level **regime-support mask** on (slot, has-alternative-owner, has-alternative-member), min 10 training rows; unsupported rows dropped from training and scoring; cases whose corrupted edge is in an unsupported regime are excluded (29 of the 103 specified-split test cases on C and D, 21 of them among the 72 hard ones; the other folds exclude 0-2; reported per fold). | Specified split, all hard: evidence-only 0.68 -> 0.89; encoder variants 0.82-0.85 -> 0.91-0.97. The gap between evidence-only and encoder variants shrinks from about 0.15 to a difference no longer distinguishable (Δ +0.037 [−0.012, +0.126], n=20). LOTO pooled essentially unchanged (0.82 -> 0.85). **The v1 claim that an encoder "lifts" the specified split was an artifact and is retracted.** |
| 2 | Clean FP rate from "max over 6 validation clean documents" | A noise-driven threshold. | Threshold = 90th percentile of **24 held-out clean calibration documents per training topology** (never trained on). | Threshold is now stable, but **the clean FPR is still not controlled**: LOTO pooled 0.40-0.47 (v1 0.33-0.65), by topology A 0.00-0.03, C 0.30-0.38, D 0.35-0.68, **B 0.72-1.00**. A threshold calibrated on other topologies does not transfer across topologies. *Unresolved by this fix.* Per-topology calibration was then tested and also fails unless the calibration data spans seasons; see the follow-up section below. |
| 3 | Topology B: constant/uninformative channels scored as signal | B's constant-volume terminals have one flow value all year, `t_dis − t_in` = 0, zone pinned at 24.0 C. Noise-only correlations were scored as error ≈ 1 ("inconsistent"). | Channels whose inputs do not vary beyond noise (signal sd > ~1.7x noise sd) are **missing** (NaN, with a `missing` flag), not scored; the same rule masks them in the observability audit. Also corrected an over-strict first version of the rule (it wrongly masked AHU coil checks on constant-flow systems). | B held-out AUROC: encoder variants 0.60-0.62 -> **0.73-0.74**, evidence-only 0.71 -> 0.75. B is still the weakest topology, and **its clean FPR (0.72-1.00) is not explained away** — the "1.00 for every model" was partly this bug and partly the threshold, and the threshold part remains. |

Two smaller notes. (a) A defensive variance floor (0.1) and clipping of standardized inputs was added after the mask briefly produced logits of ~42; the ladder shows it changed **nothing** in the reported numbers on its own (S1 ~= S0). My earlier suggestion that the 1e-3 variance floor was the main cause of the specified-split anomaly was not supported. (b) A first "slot-level" support mask was insufficient and made held-out A worse (0.85 -> 0.74) before the regime-level mask fixed it; the ladder table at the bottom shows this. Observability labels were recomputed with masked channels: 8 of 120 changed (4 observable -> ambiguous, 2 observable -> unobservable, 2 ambiguous -> unobservable), none on B; the case *selection* was not changed.

## Follow-up: does per-topology calibration fix the clean false-positive rate? (2026-09-21)

**Short answer: no. Calibration must span time (seasons), not just topology.** Scripts `10_own_calibration.py`, `11_leave_window_out_calibration.py`; outputs in `results/docmismatch/eval_owncal/`. All five evidence models, LOTO, mean over 5 seeds, hard-observable positives, target FPR 10%.

| Threshold source | Clean FPR by held-out topology (A / B / C / D) | Mean FPR | Mean recall |
|---|---|---|---|
| Other topologies' 24 calibration docs each (v2 default) | 0.00-0.03 / 0.77-1.00 / 0.40-0.50 / 0.30-0.70 | 0.43-0.52 | 0.99-1.00 |
| **Own topology's** 24 calibration docs (windows 6-7, 12 noise draws each) | 0.67-0.83 / 0.43-0.80 / 0.43-0.63 / 0.33-0.53 | 0.53-0.67 | 0.91-0.98 |
| Own topology, **leave-one-window-out** over 8 clean windows | 0.12 / 0.12 / 0.12 / 0.12 | 0.12 | 0.85-0.87 (A 1.00, B **0.49-0.57**, C 0.89-0.96, D 0.95-0.99) |

(The first two rows are evaluated on the benchmark's clean windows 0-5 only, physically disjoint from the calibration windows 6-7.)

- **Why own-topology calibration fails:** clean max-edge scores vary more *between* evidence windows than between noise draws (evidence-only: between-window sd 0.30 / 2.04 / 0.73 / 1.01 on A / B / C / D vs noise sd 0.11 / 0.49 / 0.46 / 0.96). On B, clean scores range from -1.1 to +4.8 across windows, so two calibration windows cannot bound the rest. This, not cross-topology transfer, is the dominant reason the FPR is uncontrolled.
- **Leave-one-window-out:** the FPR of exactly 1/8 for every model is a property of the protocol (the highest of 8 exchangeable windows is always the one flagged), not a finding; the information is in the recall it costs. Averaged recall drops from ~0.99 to ~0.85, mostly on B (~0.5). So a controlled ~10% FPR is achievable for these detectors only with clean calibration data spanning the seasons of the deployment building, and on topology B it costs about half the detections.
- Caveat: 8 windows x 1 document per topology, one noise draw each; the estimate has wide sampling error. Pretrained vs no-pretrain shows no difference under any calibration protocol.

## Corrected key numbers (all in the tables below)

- LOTO pooled, hard with sufficient evidence (n=91 vs 32 clean): AUROC evidence-only 0.94, random/scratch encoders 0.93-0.94, pretrained 0.93-0.94; structure-only 0.50; pretrained decoder zero-shot 0.52.
- By family (LOTO AUROC, all evidence models): sensor mapping 0.99-1.00, same-medium branch 1.00, parallel peer 0.96-0.98, plant loop 0.73-0.81, wrong AHU 0.76-0.79, **VAV-zone swap 0.54-0.57 (chance)**.
- Observable vs not (evidence models): 0.93-0.94 vs 0.54-0.58 (n=91 vs 29): the observability audit keeps its predictive value.
- Degree-preserving hard cases (n=93): structure-only exactly 0.50; the retarget artifact from v1 remains flagged.

## Licensing (checked before any download)

- **LBNL / Figshare `22338265` (RTU): CC BY 4.0, verified** on the article record via the Figshare API (`license.name = "CC BY 4.0"`, v1, not embargoed). The *collection* record (`6486349`) carries no license field of its own; I relied on the article-level record for the archive actually used. Attribution: Chen & Granderson (2023), doi:10.6084/m9.figshare.22338265.v1. Only the article I downloaded was verified; I did not verify the other seven.
- **MORTAR time series: unresolved -> blocked, nothing downloaded.** The existing confirmation was about anonymized building data via the Hugging Face mirror (static Brick graphs). Time series is served via mortardata.org, requires a free account (which I cannot create), and I found no published license or terms; its site returned an expired TLS certificate when fetched. It needs its own written confirmation from the MORTAR maintainers covering time-series data. Details in `data_cache/timeseries/LICENSES.md`.

## What real data was pulled

From Figshare article 22338265 by ranged reads of the archive (not the full 307 MB): `ORNL_RTU/ERTU_{Fall_2020,Spring_2021,Summer_2021,Winter_2022}.csv` (the four fault-free experimental files, about 8.9 MB uncompressed, 3.4 MB with the PDF fetched by ranged reads), `LBNL_FDD_Data_Sets_RTU.pdf` (documentation), stored in `data_cache/timeseries/rtu_exp/` with SHA-256 and provenance. This is the ORNL Flexible Research Platform: one Trane 12.5-ton RTU serving 10 electric-reheat VAV boxes (rooms 102-106, 202-206), an unoccupied research facility with emulated loads. **Not** pulled: the 48 faulted ORNL files (not needed), and the same archive's `Field RTU/` (Site1/Site2) and `Simulated RTU/`. `Field RTU/` looks like real building data under the same license and may be worth adding; it was outside the stated scope.

## Real-data test

**What the real data can and cannot support.** No per-box airflow, no water side: the mass/heat-balance checks that carry the simulated result do not exist here. Evidence is *coupling*: reheat power, discharge-air temperature lift over the RTU supply temperature, and room temperature. Data are 1-minute, degF/W, in 14 non-contiguous days; ~37% of rows in three files have NaN supply/VAV temperatures overnight (fan off); one VAV's reheat stream is flat (room 103, mean 12 W). So everything is NaN-aware and pairwise-complete (5-minute means, at least 2 h of valid overlap), flat streams make a channel missing, and only unit-free statistics (correlations, duty cycles, ranks) are used. Real-data families (single building, 10 boxes): VAV-zone swap, VAV supply-temp point swap, VAV power point swap, room-temp point swap = 4 x 45 room-pair swaps = 180 events; each is scored on each of the 14 days against the same day's clean documentation.

**Design discipline.** Channel choices were made on the Fall days only (8 days); Spring/Summer/Winter (6 days) are the held-out check. Exploration showed a sign that flipped across seasons, so the zone channels are sign-agnostic; I stopped tuning there.

**Result** (untrained margin rule; two-way cluster bootstrap over events and days, 2000 draws):

- Overall: rule **0.702 [0.65, 0.76]** vs structure-only **0.500**, Δ **+0.202 [+0.15, +0.26]**.
- Held-out seasons: 0.790 [0.72, 0.87]; design (Fall): 0.636 [0.59, 0.68]. Do not read the held-out > design difference as generalization: 6 days, and the clean-document score varies from 0.23 to 0.67 across days.
- By family: point swaps (SAT, power) **0.83 [0.75-0.90]**; VAV-zone and room-temp swaps **0.58 [0.52-0.65]**, barely above chance.
- Observable events (day-level audit, 52 of 180): 0.836 [0.76, 0.91]; not observable: 0.648.
- Same untrained rule on the simulated benchmark: all hard 0.787 [0.71, 0.85], observable 0.883, VAV point swaps 1.00, VAV-zone 0.456.

**So: the finding holds on real data, but it is meaningfully weaker.** Real is 0.09 lower overall and the point-swap family drops from 1.00 to 0.83. Structure-only is 0.50 on both because every event is a degree-preserving swap (this is a property of the benchmark's construction, so it tells us nothing about real documentation errors). The VAV-zone family is at or near chance in both simulation and reality, which independently corroborates that hourly-to-minute BAS trends barely identify which box serves which room.

## Caveats for the real-data result (please read)

- **Not the same comparison as the +0.438.** That number is a *trained* head on simulated evidence; on real data no trained head was fit (one building, 14 days cannot support held-out-topology training, and the simulated head's channels are not the real ones). The like-for-like reference is the *same untrained rule* on both (real 0.70 vs sim 0.79 all-hard).
- **One building, 10 VAVs, 14 days.** Events share the same 10 rooms; effective independence is low. CIs account for event and day clustering but not for the fact that it is a single facility. Clean negatives are only 14 (one per day).
- **"Ground truth" = the dataset's own point names.** A lab facility with a published system diagram, but the mapping is not independently field-verified; a real naming error in the dataset would be invisible. The injected errors are still synthetic: this is real *behavior* with synthetic *documentation errors* (stage 2 of your progression), not real documentation errors.
- **Same-floor swaps are not harder** here (0.705 vs 0.699 cross-floor); plausibility for real rooms was defined only as same floor, which is a weak notion.
- The FRP is an unoccupied research building with emulated loads and a fault-free experimental schedule, so it is cleaner than typical field data; a messier building would likely be harder still.
- Only fault-free data was used; whether real *faults* interact with mapping detection is untested.

## Limitations carried over from v1

- Everything in the simulated benchmark is synthetic; `real_world_verified = false` on every row. The four simulated topologies share one envelope; A-C share Chicago weather (D Golden CO).
- Small n: LOTO observable slice 91 events / 102 groups (comparisons); spec-C 20 events.
- The pretrained encoder never saw this benchmark's graph conventions (loop -> branch-valve -> coil) and is topology-only, so a null result is expected when the hard cases equalize topological plausibility. It does not show that pretraining cannot help auditing in general.
- One training recipe for all variants; not tuned per variant. The evidence features are hand-written physics checks; a model on raw time series is untested.
- The observability audit takes the best of four channels and knows the true owner (oracle): it says the evidence contains the answer, not that a model can extract it.
- Robustness variants (same event, other windows) were not generated.

## Phase 1 — is there real documented-vs-verified ground truth?

**No public case-level dataset was found.** (Search results, not full-text verified; ScienceDirect and UCL Discovery returned 403 to the search agent.)

- UCL One Pool Street (Wang, Lilis, Katsigarakis, Mavrokapnidis, Korolija, Rovas, EC3 2024; related Energy & Buildings 325 (2024) 115035 and an Applied Energy paper): topology reconstructed from incomplete IFC-BIM compared with design drawings, i.e. documentation vs reconstructed documentation, data apparently on request.
- Commissioning/RCx case studies (DOE FEMP, PNNL, LBNL): narrative performance faults, no per-case as-built-vs-field connectivity found.
- BAS point verification / metadata inference (Fürst et al.; automated tagging): labels are human-tagged points, measuring inference accuracy, not documentation error against field truth.
- Torabi et al. (Building and Environment 2022): taxonomy + 11 interviews, no case data.
- Brick/Mortar/Haystack: documentation-derived models; the Brick-tagged LBNL set was checked against diagrams (docs vs docs).
- LBNL FDD and similar fault datasets are fault labels and were not counted.

Worth emailing: One Pool Street authors (Meng Wang, Georgios Lilis, Dimitrios Rovas, Ivan Korolija), Torabi/Gunay/O'Brien (Carleton), Mortar/Brick maintainers, LBNL commissioning researchers.

## Phase 2 — how 4 events became 16 rows

`symptom_pipeline/output/causal_batch_v1_summary.json`: 6 `reassign_coil` events on `sys07_vav_reheat`, 4 simulated cleanly, each with `n_report_variants: 4`, giving 16 records: 4 physical events x 4 wordings, all the same heating-coil-to-chilled-water-pump move, single degenerate split. Here, the building is never rewired, `physical_event_id` is unique per row (unit-tested), and wording/window variants are not generated. Two vendored multi-AHU fixtures were rejected because both AHUs serve the same 10 zones; two valid topologies were built instead (see README).
