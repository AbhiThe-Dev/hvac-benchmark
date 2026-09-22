# Checkpoint: modelling agent (written on resume)

## Implemented (all under src/docmismatch/active/ unless noted; all new options default-off, 51 tests pass)
* engine.py: `run_episode(diag=True)` (posterior history + per-reading diagnostics), policy `traversal_block` (informative-block-aware sweep),
  `slice_effect=True` (exact joint-Gaussian belief with a slice-member effect shared by all candidates' readings of one member in one slice; equals the old belief when omega=0, max diff 2e-9).
* model.py: `estimate_slice_effect` (method of moments, different-candidate cross-products), ChannelModel.omega/rho_s; `fit_slot_models(slice_effect=)`.
* selection.py: variant `sel_slice` (= sel + slice effect).
* reliability.py: case-level reliability layer (features at stop, ridge-logistic score, leave-inner-unit-out OOF, isotonic, cluster-aware conservative LB, contiguous tail scan, per-slot tightening, flag reasons).
* readiness.py: nested fold runner (`run_fold_records`, `fold_plan`), real/sim kinds, layers none|legacy|new, frozen_check, ledgered sim-sealed loader, sealed runners + rehearsal.
* evalkit.py: C1-C4 metrics, cluster bootstrap, calibration/ECE, markdown.
* scripts/20_final_eval.py: entry point (--freeze, --data ..., --rehearsal).
## Variants tried (running count = 2 likelihood variants x 3 decision layers)
1. sel + layers none/legacy/new, real-dev-nested (full nested run, 135 s): plain rule acc 0.920 [0.868,0.965] cov 0.137; legacy cov 0.004 (acc 1.0); new layer answers nothing (inner runs trained on 2 seasons have crossed-accuracy ~0.83, no tail with LB>=0.95).
2. sel_slice, outer-only quick check: acc among crossed 0.958 vs 0.912 (sel), coverage 0.112 vs 0.137. Full nested run was interrupted.
Diagnostic (not a variant): slice-member residual ICC 0.3-0.8 on real sat/pwr channels, motivating sel_slice.
## Remaining, in order
1. rerun real-dev-nested for sel_slice; sim-dev-loto (with dev_E..H) for both; choose variant; consider layer strictness / nominal target honestly.
2. sim-helps-real logL check; power analysis. 3. tests/test_reliability.py. 4. --freeze, rehearsals. 5. active_readiness_dev_report.md with predictions.
## Judgment calls after seeing held-out DEV numbers
* Trying sel_slice was motivated by the ICC diagnostic and the first nested result (post hoc). Reading pool = the day's 6 blocks (chosen before, kept). Layer LB standard (one-sided 90%, design-effect-inflated Beta, nominal 0.95) set a priori.
## Sealed data
Never loaded. results/docmismatch/active/sealed_access.log does not exist.

## Status update (after resume)
* Now: four re-runs in background (real-dev-nested and sim-dev-loto with dev_E..H included, variants sel and sel_slice, tags v5_*), needed because cell-family labels were fixed (correct edges now carry the slot/matched family so C2/C4 cells contain both classes). Not blocked.
* Finished since resume: tests/test_reliability.py (9 pass; suite green), scripts/21_data_decisions.py (sim-helps-real logL test + power table -> final/data_decisions.json), scripts/22_layer_ablation.py, layer scan fix (small samples no longer break the scan) and lb_floor=0.90 (tail point acc >= 0.95 AND one-sided 90% LB >= 0.90; a judgment call made after seeing that LB>=0.95 answered nothing).
* Headline (pre-fix cells, so C4 numbers not trusted yet): real nested sel_slice, plain rule: acc 0.954 [0.911,0.990], coverage 0.112; sel: acc 0.920, cov 0.137. New layer answers ~nothing on real (inner runs trained on 2 seasons have crossed acc ~0.83). Sim LOTO (sel, 8 dev topologies): plain acc 0.864 cov 0.48; legacy cov 0.08 acc 0.95; new layer cov 0.024 acc 0.95.
* Variants on DEV so far: likelihood 2 (sel, sel_slice) x layer 3 (none, legacy, new) + 8 layer-config ablations pending on real (22_layer_ablation.py; all answer ~0 on real before the cell fix). Total tried = 2 + 8 layer configs (+ lb_floor change).
* Remaining (ETA): dev report + ablations (~1h after runs), freeze (minutes; must be re-run if any file in active/ changes), rehearsal real+sim (~15 min), final report.
* Sealed data: never loaded; sealed_access.log does not exist.

## Final state
Frozen (variant sel_slice, results/docmismatch/active/frozen/), rehearsals real+sim ran end to end, tests 71 pass, dev report written (active_readiness_dev_report.md). Sealed data never loaded.
