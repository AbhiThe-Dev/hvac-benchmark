# Field data intake: what we need from a building, and what we do with it

We check whether a building's **documented connections** (which air handler feeds which VAV box, which box serves which room, which loop feeds which coil, ...)
match what the equipment actually does, using the building automation system's recorded data. This page says exactly what to send.
Everything is plain CSV. A small synthetic example is in [`examples/intake_example/`](examples/intake_example/) (its numbers are made up; it only shows the layout).

To see what a building's export can and cannot support before anything else is done:

```bash
.venv/bin/python doc_mismatch/scripts/54_intake_check.py EXPORT_DIR --report report.md
```

## The files

| File | Required | What it holds |
|---|---|---|
| `points.csv` | yes | one row per recorded point: which equipment it belongs to, what it measures, its unit |
| `trends.csv` | yes | the recorded history of those points over time |
| `connections.csv` | yes for checking | the documented connections, and (if known) what a field check found |
| `equipment.csv` | recommended | equipment that has no recorded points, and whether a coil heats or cools |
| `context.json` | recommended | time zone, the date the connections were marked up, and later changes to the building |

### `points.csv`

`point_id, equipment_id, equipment_type, signal, unit, logging`

- `point_id`: the name used as the column header in `trends.csv` (or the id in the long format). Must be unique.
- `equipment_id`: the piece of equipment the point belongs to, e.g. `VAV-12`. Use the same ids in `connections.csv`.
- `equipment_type`: one of `AHU, VAV, Zone, Coil, Branch, HWL, CHWL, Pump, Boiler, Chiller, Fan, SAT, DAT, Weather`. (`Branch` = the valve/branch that feeds one coil; `HWL`/`CHWL` = hot-/chilled-water loop; `SAT`/`DAT` = a stand-alone supply-/discharge-air-temperature sensor; `Weather` = the outdoor-air-temperature sensor.)
- `signal`: what it measures, from the list below. Points that are not on the list (damper position, valve position, ...) can be left out or included; they are ignored.
- `unit`: one of the accepted units below. An unknown unit is an error, never a guess.
- `logging`: `interval` (regular samples, the default) or `cov` (change-of-value logging: a value is recorded only when it changes; we hold the last value for up to 6 hours).

| Equipment | Signals we use | Unit kind |
|---|---|---|
| `AHU` (air handler) | `flow` supply airflow, `sat` supply-air temp, `mat` mixed-air temp, `htg` heating meter, `clg` cooling meter | airflow, temp, temp, power, power |
| `VAV` | `flow` airflow, `t_in` inlet air temp, `t_dis` discharge air temp, `reheat` reheat power (optional) | airflow, temp, temp, power |
| `Zone` | `temp` room temperature | temp |
| `Coil` | `rate` heat rate, `rate_s` sensible cooling rate (cooling coils, optional) | power |
| `Branch` | `flow`, `t_in`, `t_out` water flow and inlet/outlet water temp | water flow, temp, temp |
| `HWL`, `CHWL` | `flow`, `t_sup` supply temp, `t_ret` return temp | water flow, temp, temp |
| `Pump` | `flow`, `kw` power | water flow, power |
| `Boiler`, `Chiller` | `rate` heat / cooling rate, `t_out` outlet temp | power, temp |
| `Fan` | `kw` | power |
| `SAT`, `DAT` | `value` | temp |
| `Weather` | `oat` outdoor-air temperature | temp |

Accepted units (converted to °C, kg/s, W): temperature `C, degC, F, degF, K`; airflow `kg/s, kg/h, lb/min, lb/h, cfm, m3/s, m3/h, l/s`; water flow `kg/s, kg/h, gpm, l/s, l/min, m3/h, m3/s`;
power `W, kW, MW, BTU/h, MBH, kBTU/h, ton`. Volumetric flows are turned into mass flow with air 1.2 kg/m³ and water 998 kg/m³ (hot water is ~3% lighter: a disclosed approximation).

### `trends.csv`

Either **wide** (first column the timestamp, one column per `point_id`) or **long** (`timestamp, point_id, value`).

- Timestamps: ISO (`2021-01-04 06:15:00`, `2021-01-04T06:15:00-06:00`) or common US formats (`01/04/2021 06:15`, `1/4/2021 6:15 AM`). If there is no offset in the stamp, give the time zone in `context.json`.
- Sampling: **15 minutes or finer** is best; hourly works. Irregular is fine. Blanks are missing values. `-999`, `32767`, `inf`, and text like `offline` are treated as missing and counted.
- Length: **at least 3 months, covering more than one season**, is what lets us learn how a building behaves across weather; a few weeks or days still lets us read the connections. Separate chunks (for example two weeks in each season) are fine: coverage is judged only over the days that have data.
- We put everything on an hourly grid in **local standard time** (no daylight-saving jumps), starting at local midnight.

### `connections.csv`

`owner_id, member_id, slot, verified, true_owner, source`. One row per documented connection; `owner_id` is the "parent" end.

| `slot` | What the row says |
|---|---|
| `ahu_vav` | air handler `owner_id` supplies VAV box `member_id` |
| `vav_zone` | VAV box `owner_id` serves room/zone `member_id` |
| `loop_branch` | loop `owner_id` (HWL/CHWL) feeds branch `member_id` |
| `branch_coil` | branch `owner_id` feeds coil `member_id` |
| `loop_pump` | pump `member_id` belongs to loop `owner_id` |
| `loop_source` | boiler/chiller `member_id` belongs to loop `owner_id` |
| `coil_ahu` | coil `member_id` is part of air handler `owner_id` |
| `coil_vav` | reheat coil `member_id` is part of VAV box `owner_id` |
| `ahu_sat` | supply-air sensor `member_id` is on air handler `owner_id` |
| `vav_dat` | discharge-air sensor `member_id` is on VAV box `owner_id` |

- `verified`: `yes` (a field check or the as-built drawings confirm this documented connection), `no` (it is wrong), or `unknown` (default).
- `true_owner`: for `verified = no`, the owner that was found in the field, when known.
- `source`: where the documented connection came from: `design`, `as_built`, `bas`, or anything else.

**Verified rows are what make the data scorable.** Without any, we can check a building but not measure how often we are right. We need both `yes` and `no` rows.

### `equipment.csv` (optional)

`equipment_id, equipment_type, function, medium`. `function` = `heating` or `cooling` for a `Coil` (a heating coil is read differently from a cooling coil); `medium` = `hot_water` or `chilled_water` for branches, pumps, boilers, chillers and coils. Also lists equipment that has no recorded points but appears in `connections.csv`.

### `context.json` (optional, recommended)

```json
{"building_id": "school_12", "timezone": "America/Chicago", "as_built_date": "2020-11-15",
 "modifications": [{"date": "2022-03-01", "note": "AHU-2 cooling coil replaced"}]}
```

`as_built_date` is when the connections were marked up or verified; `modifications` are later changes to the equipment or its connections. **The trends should come from a period when the building still matched the verified connections**:
if a coil was re-piped after the markup, trends recorded afterwards show the modified building and would make a correct check look like an error. The report flags any conflict between these dates and the trend period.

## What each connection check needs

Each connection check has up to three "channels" (independent consistency tests). A channel can only run when every point it reads is recorded, covers at least half of the days' hours, and varies by more than sensor noise.
The report lists, per connection type, how many of a building's documented connections each channel can use, and which missing point would unlock more.

| `slot` | Checks | Points read on the owner side | Points read on the member side |
|---|---|---|---|
| `ahu_vav` | which air handler supplies each VAV box | air handler: `sat` (ch 0), `flow` (ch 1,2) | VAV box: `t_in` (ch 0), `flow` (ch 1,2) |
| `vav_zone` | which room each VAV box serves | VAV box: `flow` (ch 0,2), `t_dis` (ch 1,2) | room/zone: `temp` |
| `loop_branch` | which water loop feeds each coil branch | loop: `t_sup` (ch 0), `flow` (ch 1,2) | water branch: `t_in` (ch 0), `flow` (ch 1,2) |
| `branch_coil` | which branch feeds each coil | water branch: `flow`, `t_in` (ch 0), `t_out` (ch 0) | coil: `rate` |
| `loop_pump` | which loop each pump belongs to | loop: `flow` | pump: `flow` (ch 0,1), `kw` (ch 2) |
| `loop_source` | which loop each boiler / chiller belongs to | loop: `t_sup`, `flow` (ch 1,2), `t_ret` (ch 1,2) | boiler / chiller: `t_out` (ch 0), `rate` (ch 1,2) |
| `coil_ahu` | which air handler each coil belongs to | air handler: `flow`, `sat`, `mat` | coil: `rate` (cooling coils: `rate_s` if recorded, else `rate`) |
| `coil_vav` | which VAV box each reheat coil belongs to | VAV box: `flow`, `t_dis`, `t_in` | coil: `rate` |
| `ahu_sat` | which air handler each supply-air sensor is on | air handler: `flow`, `mat`, `htg`, `clg` | sensor: `value` |
| `vav_dat` | which VAV box each discharge-air sensor is on | VAV box: `t_in`, `flow` (and `reheat` if the box has reheat) | sensor: `value` |

Two things this table makes visible about real buildings: coil heat rates (`rate`) and air-handler heating/cooling meters (`htg`, `clg`) are often **not** recorded by a control system (they are computed in simulation), and box airflow (`flow`) is what most VAV checks lean on.
If a coil's water flow and inlet/outlet temperatures are recorded, its `rate` can be sent as the computed value (water flow in kg/s x 4.18 x |t_in - t_out| in K gives kW); we never derive one piece of equipment's series from another's or from the documentation.

**`vav_zone` needs more than data.** Even with every point recorded, ordinary operation cannot tell which box serves which room (in simulation, no better than chance, PREREGISTRATION_DR.md Addendum 11).
What works is deliberate changes to room setpoints (Addendum 13) or a box override; so **trends recorded during commissioning or functional tests that contain such changes are the most useful data for that connection.**

## What we do, and do not do

- Convert units, put every point on the common hourly grid, and report what is missing or doubtful. Nothing is silently repaired: unparseable timestamps, sentinels, out-of-range values, duplicate stamps, points with no trend, unit labels that look wrong (for example a room temperature of 72 labelled °C) are all listed.
- Build, for the documented connections, the same "reading pool" of day-long slices (six per six-week window; for chunked exports, days spread over the days that exist) that the simulated buildings use, so the existing engine runs unchanged (`docmismatch/field_pool.py`).
- **Not** fitted, tuned or scored here: the intake and readiness report never look at whether a documented connection is right, and no model is trained on the data by this step.
- Real-data evaluation is a separate, pre-registered step (held-out buildings, frozen rules); this page is only about getting data in cleanly.

## Checked on

- **A real building.** The ORNL RTU-VAV baseline days (10 rooms, 14 days in 14 chunks, 1-minute data in °F and W, `inf` values, fan-off blanks) load without changes: 34 points, 20 documented connections. The report reaches the same conclusion as the earlier statistical analysis of this building: with no box airflow and no box inlet temperature recorded, `ahu_vav` is untestable and `vav_zone` supports only its discharge-temperature channel (1 of 3).
- **A simulated building through a BAS-style export** (US units, 15-minute or hourly samples, US date format): the recovered series match the originals to 1e-7 and the evidence computed from them matches the engine's direct computation on more than 500 (owner, member, day) evaluations.
- **Six real Mortar buildings**, converted from their Brick graphs and Parquet timeseries by `scripts/56_mortar_to_intake.py` (`docmismatch/mortar_adapter.py`; two 42-day windows each, chosen by data coverage only; US units assumed and range-checked; UTC clock). What they support is in `results/docmismatch/intake/mortar_readiness.md`.
- A test perturbs every recorded signal of every connection type and confirms the "points read" table above is exactly what the evidence engine uses.
