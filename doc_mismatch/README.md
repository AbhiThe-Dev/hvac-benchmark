# doc_mismatch — plausible documentation-error benchmark

Tests whether a model can tell that **documented** HVAC connectivity disagrees with the **physical** building when the wrong documentation is still believable. The building is always correct and never rewired; only the paperwork is corrupted. Read `../results/docmismatch/results.md` for findings and all tables.

## Pipeline

| Stage | Script | Env | Output (`../results/docmismatch/`) |
|---|---|---|---|
| 1. build / extract / simulate 4 base topologies (full year, hourly, EnergyPlus 25.2) | `scripts/01_simulate.py` | `physics_pipeline/.venv` (has `openstudio`) | `base/<topology>/{graph.json,evidence.npz,run.json}` |
| 2. propose → validate → observability-label → diversity-select cases | `scripts/02_build.py` | root `.venv` | `cases.jsonl`, `diversity_audit.json` |
| 3. features, encoder embeddings, 5 folds × 10 variants × 5 seeds | `scripts/03_evaluate.py` | root `.venv` (torch) | `eval/raw.pkl` |
| 4. metrics + paired group bootstrap | `scripts/04_aggregate.py` | root `.venv` | `eval/metrics.json`, `eval/comparisons.json` |
| 5. report | `scripts/05_report.py` | root `.venv` | `results.md` (prepends `findings.md`) |
| v2. relabel observability with masked channels | `scripts/06_relabel_observability.py` | root `.venv` | `cases.jsonl` (old label kept as `observable_v1`; v1 files in `eval_v1/`) |
| v2. clean calibration documents for the threshold | `scripts/07_make_calibration.py` | root `.venv` | `cases_calibration.jsonl` (96 docs, never trained on) |
| real. score real ORNL FRP data | `scripts/08_real_frp.py`, `scripts/09_real_analysis.py` | root `.venv` | `real_frp/real_results.json` |

```bash
cd doc_mismatch
../physics_pipeline/.venv/bin/python scripts/01_simulate.py     # ~1 min
../.venv/bin/python scripts/02_build.py && ../.venv/bin/python scripts/03_evaluate.py
../.venv/bin/python scripts/04_aggregate.py && ../.venv/bin/python scripts/05_report.py
DOCMISMATCH_FEATURES=scalefree ../.venv/bin/python scripts/03_evaluate.py   # sensitivity run (needs eval_scalefree/prepared.pkl copied from eval/)
../.venv/bin/python -m pytest tests -q                                       # 12 invariants
```

## v2 switches (for ablations / the correction ladder)

`DM_CLIP` (variance floor + input clipping), `DM_SUPPORT` (regime-support mask), `DM_MASKCH` (uninformative channels -> missing), `DM_EVAL_DIR`, `DM_NBOOT`; all default to on. `eval_s0..s3/` hold the staged runs (S0 reproduces v1).

## Real data

`src/docmismatch/real_frp.py` scores the ORNL FRP RTU-VAV field data in `data_cache/timeseries/rtu_exp/` (LBNL FDD Data Sets RTU, CC BY 4.0, see `data_cache/timeseries/LICENSES.md`; MORTAR time series is blocked pending written confirmation). No per-box airflow exists there, so evidence is coupling-based, NaN-aware and unit-free.

## Base topologies (all simulate with 0 severe errors)

| | Topology | Source |
|---|---|---|
| A | `sys07_vav_reheat`: 1 AHU, 10 VAV-reheat, 1 HW + 1 CHW loop | vendored NREL/OpenStudio-resources, unmodified |
| B | `sys03_psz_ac`: 10 single-zone AHUs, no plant | vendored, unmodified |
| C | `vav_2ahu_2loops`: 2 AHUs (by floor), 2 HW + 2 CHW loops | built by `build_models.py` on the sys07 envelope |
| D | `vav_3ahu_2loops`: 3 AHUs (N/S, E/W, core), 2 HW + 2 CHW loops, Golden CO weather | built |

Built models mirror `baseline_sys07`'s AHU sizing (an early draft sized on ventilation only and was ~40× undersized — caught by checking zone temperatures, fixed) and give each AHU a distinct SAT setpoint (12.2 / 13.3 / 12.8 °C), otherwise identical AHUs would make every SAT-sensor swap unobservable by construction.

## Design decisions worth knowing

- **Slots, not free-form edges.** Each connection type (`ahu_vav`, `vav_zone`, `loop_branch`, `branch_coil`, `loop_pump`, `loop_source`, `coil_ahu`, `coil_vav`, `ahu_sat`, `vav_dat`) has fixed owner/member classes, direction and cardinality (`data.SLOTS`, `rules.MAX_PER_OWNER_CLASS`).
- **Six hard families** map to slots: wrong AHU → `ahu_vav`; VAV-zone swap → `vav_zone`; plant loop → `loop_branch`; sensor mapping → `ahu_sat`/`vav_dat`; same-medium branch → `branch_coil`; parallel peer swap → `loop_pump`/`loop_source`/`coil_ahu`/`coil_vav`. A single-edge retarget is used when the source owner keeps ≥1 member; otherwise a pair swap.
- **Hard filters** (`corruptions.py`, `rules.py`): replacement differs, same class/medium/relation/direction, cardinality, no duplicate edge, no orphan, graph valid, capacity plausible (AHU/loop peak load), size compatible (peak flow/rate ≤1.5×, floor area ≤1.5×, sensor mean within 4 K).
- **Observability** (`observability.py`): per changed edge, true-owner vs documented-owner consistency error over 6 disjoint blocks on 4 channels; `observable` needs ≥5/6 block wins and mean relative gap ≥0.2.
- **Evidence** (`evidence.py`): noisy BAS-like series (T ±0.25 K, flow ±2%, rates ±3%, sensor offsets); per-connection errors = level match, dynamics, conservation; set-level flow/heat closure for AHUs and loops. Clean and corrupted docs share identical evidence for the same (topology, window, seed).
- **Detector** (`classify.py`): per-documented-edge MLP; case score = max edge logit. Variants differ only in input (evidence, structure, random/pretrained encoder, frozen/fine-tuned). Threshold set on validation only.
- **Splits**: leakage groups (union-find over shared corrupted components within topology+family); fold = held-out topology; validation = held-out groups + clean windows 6–7 of training topologies.
- **Deviations from the brief**: `actual_connection`/`documented_connection` are lists (swaps change two edges); 4 topologies rather than 3; the parallel-peer family is mostly coil swaps because only C and D have two same-medium loops with size-compatible plant equipment; clean cases are 4 topologies × 8 six-week windows.

## Not done

- Real-data test is one building / 14 days / untrained rule (see findings). Not done: a trained detector on real data, per-topology threshold calibration, the `Field RTU/` sites, MORTAR time series (license unresolved).
- Robustness variants (same event, other windows / noise seeds) and MORTAR-derived topologies.

## Sequential active verification (v3)
See `active_findings.md`. Pools/likelihood/engine in `src/docmismatch/active/`; run `scripts/12_active_sim.py`,
`scripts/14_active_real.py` (env `DM_CTXMODE=full|oat`), `scripts/16_context_likelihood_test.py`, then `DM_TAG=oat scripts/15_active_report.py`.
