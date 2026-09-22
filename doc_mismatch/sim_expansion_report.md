# Simulation expansion: 4 dev + 4 sealed buildings

Written after generation. No classifier, likelihood model or verifier was run on any of these buildings; sealed topologies were checked only for
EnergyPlus success, non-constant evidence, sizing sanity (zone temperatures, AHU/VAV flow balance) and graph structure.

## What was generated
* **Spec first.** `results/docmismatch/active/sim_spec.json` (SHA-256 in `sim_manifest.json`, `spec_sha256`, written before any simulation) holds every
  parameter, drawn from fixed-seed random draws over the ranges in `src/docmismatch/sim_spec.py` (dev seed 20260921, sealed seed 20260922). A draw had to meet
  written coverage requirements (e.g. an n_ahu=4 building, near-twin and separated SAT pairs); the dev draw met them on attempt 1 (second deterministic seed; attempt 0 failed) and the sealed draw on attempt 3 (attempts 0-2 failed). Attempts are rejected by spec-level rules only (`seeds.dev_attempts`, `seeds.sealed_attempts` in the spec); no simulation was involved in choosing between them.
  `scripts/18_make_sim_spec.py` refuses to overwrite an existing spec; `19_generate_sim.py` asserts the hash before simulating.
* **Builder.** `src/docmismatch/build_ext.py` (new). Unlike C/D it also builds the *envelope* (a floors x nx x ny grid of rectangular zones, so 6-16 VAVs are possible;
  the baseline_sys07 envelope has only 10 zones of very unequal size). HVAC is the same design as C/D (per-AHU coils, per-VAV hydronic reheat, per-loop pump + boiler/chiller)
  with the same non-ventilation-only AHU sizing settings (the earlier ~40x undersizing bug); design days now come from each climate's own DDY. `physical.py` got a
  4-line backward-compatible hook (`EXT_BUILDERS`, kind `"ext"`); registration is explicit (`build_ext.register_from_spec`).
* **Outputs.** `results/docmismatch/base/<tid>/{graph.json, evidence.npz, run.json, in.idf, eplusout.err}` for dev_E..H, seal_S1..S4 (full year, hourly, 8760 h, same graph slot structure and
  signal names as C/D). All 8 passed on the first attempt, 0 severe / 0 fatal EnergyPlus errors (28-47 warnings, the same benign kinds as C/D: OA-controller air-distribution defaults, min-flow input notes).

| id | role | climate | AHUs | VAVs (floors x nx x ny) | HW / CHW loops | SAT setpoints (C) [pattern] | occupancy start-end, night, weekend | wall time |
|---|---|---|---|---|---|---|---|---|
| dev_E | dev | Sterling VA (TMY3) | 1 | 6 (1x2x3) | 1 / 1 | 13.96 [single] | 7.5-17.3, 0.09, 0.06 | 8 s |
| dev_F | dev | Sacramento (CZ2010) | 2 | 6 (1x2x3) | 2 / 2 | 12.84, 13.06 [near-twin, 0.22 K] | 7.7-17.6, 0.06, 0.09 | 11 s |
| dev_G | dev | San Francisco (TMY3) | 3 | 6 (1x2x3) | 2 / 2 | 13.75, 13.89, 12.27 [1 twin pair] | 8.3-18.0, 0.10, 0.16 | 12 s |
| dev_H | dev | Golden CO (TMY3) | 2 | 12 (2x2x3) | 1 / 2 | 12.47, 12.20 [near-twin, 0.27 K] | 8.3-17.7, 0.04, 0.00 | 17 s |
| seal_S1 | sealed | Chicago AMY 2013 | 4 | 16 (1x4x4) | 3 / 1 | 13.14, 15.10, 11.77, 12.77 [separated] | 8.9-17.8, 0.19, 0.54 | 27 s |
| seal_S2 | sealed | Blue Canyon CA | 3 | 12 (1x3x4) | 3 / 1 | 13.88, 12.02, 15.37 [separated] | 6.6-21.8, 0.28, 0.39 | 20 s |
| seal_S3 | sealed | Arcata CA | 3 | 12 (2x2x3) | 1 / 1 | 13.36, 13.54, 13.47 [all near-twin] | 6.2-21.7, 0.12, 0.35 | 15 s |
| seal_S4 | sealed | Tampa FL | 1 | 15 (1x3x5) | 1 / 1 | 12.03 [single] | 8.4-20.3, 0.14, 0.53 | 15 s |

Runtime: one topology = 8-27 s wall (EnergyPlus 4-12 s, the rest OpenStudio build + graph extraction); all eight = 125 s. Dev pools (8 x `load_or_build_sim`) took about 1 s each.
The full per-topology spec (geometry, loads, setpoints, min-flow fraction, sizing factors, fan pressure, economizer flags, loop temperatures/deltas, grouping mode) is in `sim_spec.json`.

## What varies
Number of AHUs (1-4), VAVs (6-16; also VAVs per AHU, via random group sizes >= 2, block or column-stripe grouping), number of HW/CHW loops (1-3) and which AHU sits on which loop, loop design temperature and delta-T,
AHU SAT setpoints (near-twin within 0.3 K vs separated by >= 1 K), fan pressure, economizer on/off per AHU, VAV minimum-flow fraction (with per-box jitter), global sizing factors, zone dimensions and floor height, window-to-wall ratio,
infiltration, lights / equipment / people density with a per-zone lognormal scale, per-zone occupancy schedule shifts (+-1 h), weekday/night/weekend schedule levels, thermostat setpoints with setback, building orientation, and **climate**.

**Sealed extends beyond dev** (ranges in the spec; `SEALED_EXTENSIONS`): climates absent from dev (hot-humid Tampa, cool-marine Arcata, mountain Blue Canyon, and a different weather year of Chicago; dev uses Sterling, Sacramento, San Francisco, Golden),
up to 4 AHUs and 16 VAVs (dev max 3 / 12; the realised sealed draw has 4 AHUs and two buildings with > 12 VAVs), up to 3 loops per medium (dev max 2), wider load / window / infiltration / setpoint ranges, near-24/7 and heavy-weekend occupancy, wider zone sizes and SAT range.

## Climate coverage (honest)
Only vendored weather is used (nothing downloaded): 5 TMY3 files in the EnergyPlus install, 6 California CZ2010 files and 3 Chicago files (TMY3, AMY 2012, AMY 2013) in OpenStudio-resources.
Used: Sterling, Sacramento, San Francisco, Golden (dev); Chicago AMY 2013, Blue Canyon, Arcata, Tampa (sealed). Existing A-D use Chicago TMY3 (x3) and Golden TMY3.
Available but not drawn: Palm Springs (sealed pool) and Chicago AMY 2012 (dev pool); Los Angeles and Oakland were never in a pool; no extreme-cold or tropical hot-dry-humid weather beyond Tampa; no multi-year weather for one building. The year is one weather year per building.
Sealed climates are new *locations*, not different years of a dev location, except Chicago AMY 2013, which is a different year of a location A-C already use (TMY3).

## Failures, retries, warnings
No topology failed or was replaced; each was generated once (`generation.<tid>.attempts = 1` in the manifest). Development notes (before the spec was written, on a throwaway spec not in the manifest):
`Space.fromFloorPrint` needs a clockwise footprint, `matchSurfaces` needs a `SpaceVector`, a CZ2010 DDY contains monthly design days that fail the IDD range check when the file is loaded whole (fixed by parsing only annual design days as text),
and 10-minute-timestep schedule times had to be snapped (a first version gave 24-minute schedule breakpoints). Two Sacramento-EPW lines "no design condition fields" are harmless.
Generation checks recorded per topology in the manifest: component counts equal spec, per-AHU VAV counts equal spec group sizes, same 11 slots as C/D, no constant flow/temperature series (0 of 91-253 series constant), zone temperatures
within the setback band +-2 K in >= 98.7% of zone-hours (worst: seal_S1, 1.3%), AHU peak flow / sum of its VAV peaks 0.91-1.0 (a 40x undersizing would show here).

## Cases and pools
* `results/docmismatch/cases_dev_extra.jsonl` (179 cases: 117 hard, 30 easy, 32 clean) and `cases_sealed_sim.jsonl` (182: 120 hard, 30 easy, 32 clean), produced by `scripts/20_make_sim_cases.py` through the unchanged `build.build_cases` (topology tuple / letters patched at call time; original `cases.jsonl`, `cases_calibration.jsonl` untouched). Letters E-H and S1-S4; `observable` (masked-channel physics audit) and `degree_preserving` included; same keys as `cases.jsonl` except the legacy `observable_v1`. Sealed case file SHA-256 is in the manifest.
* Hard-case observability: dev true 92 / ambiguous 12 / false 13; sealed true 95 / ambiguous 14 / false 11. `vav_zone_swap` is again the least observable family (dev 8 of 20, sealed 14 of 20 observable). Hard per family: 20 each (dev `plant_loop_mapping` 17: not enough distinct candidates). One-AHU buildings (dev_E, seal_S4) contribute no `wrong_ahu_mapping` cases.
* Dev pools: `pool_dev_{E,F,G,H}_r{0,1}.pkl` built. Sealed pools are NOT built; `active/sim_data.load_sealed_sim(tid, rep, reason)` builds/loads on demand and appends `timestamp, script, tid#rep, reason` to `results/docmismatch/active/sealed_access.log` (the ledger the real sealed loader also uses); `DEV_TOPOLOGIES` / `SEALED_TOPOLOGIES` come from the manifest.

## How far from the real ORNL building, and what this can and cannot support
* Same modelling family as A-D: EnergyPlus hourly, VAV with hydronic reheat, constant scheduled SAT per AHU, no SAT reset, no duct/zone leakage faults, no sensor drift. The real building has **electric** reheat per box, 5-minute data, a different control sequence, real sensor noise and gaps; the simulated evidence is noise-added later by `evidence.make_evidence` exactly as for A-D, which is a stylised BAS-noise model.
* All 8 buildings share one envelope construction set (ASHRAE 189.1 CZ 4-5, from baseline_sys07) regardless of climate, one HVAC design family, and one equipment library (EIR chiller, variable-speed pump, boiler); zones inside a building are equal-size tiles, plus a 0.1-0.5 lognormal load scale. This is more diverse than 4 buildings, not a sample of real buildings.
* Dev set is small in VAV count (three of four have only 6 boxes; dev_G has 2 VAVs per AHU), so "wrong-owner" hypotheses per AHU slot are few there. The near-twin condition is realised in dev_F, dev_G (one pair), dev_H, and (sealed) seal_S3; separated in dev_G, seal_S1, seal_S2.
* Supports: development and leave-one-topology-out fitting on 7 dev buildings (A-D + E-H), checking whether behaviour depends on near-twin equipment, size, climate and schedule; one single-shot sealed simulation test on 4 blind buildings with broader conditions.
* Cannot support: any claim about real-building transfer (electric reheat, 5-min data, BAS sensor faults), about real technician reading costs, about faults other than documentation errors, or statistical power beyond 4 sealed buildings (case clusters within a building are not independent). The sealed cases were generated with the same generator family as dev, so dev/sealed shift is in parameters and climate, not in modelling approach.
* The sealed set was inspected only at generation level (spec parameters, EnergyPlus/sizing/structure checks, physics-only observability counts). Anyone changing the builder now would invalidate that blindness; note `build_ext.py` is not hashed in the manifest (only the spec and `sim_spec.py`).
