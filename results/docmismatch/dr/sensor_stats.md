# Sensor / telemetry statistics from real DEV data

Source: ORNL FRP RTU-VAV building (LBNL FDD RTU set), 1-minute, DEV files only: ERTU_{Fall_2020,Spring_2021,Summer_2021,Winter_2022} (14 days) + Inc_Eco_* (16 days) = 30 days ({'fall': 12, 'spring': 6, 'summer': 6, 'winter': 6}). Sealed OA_damper*/SA_temp_bias* files were never opened (prefix guard in `scripts/23_sensor_stats.py`). CIs are 95% percentile bootstrap over whole days (300 resamples); days are treated as exchangeable, which understates uncertainty for building-level effects (one building, 4 seasons).

Inc_Eco files are economizer-setpoint-fault days; they are used here only because sensor statistics should not depend on that fault. Note the Fall file is a processed export (float artefacts, fan-off flow filled with 0 rather than NaN, RTU_MA_TEMP at 0.3 degF resolution), unlike Spring/Summer/Winter.

## 1. Headline table (per signal class)

| quantity | estimate | 95% CI | status |
|---|---|---|---|
| white noise sd, temperature (K) | 0.01966 | [0.01726, 0.02102] | estimated, quantisation-limited (quantum 0.0056 K) |
| white noise sd, BAS-point/discharge temp (K) | 0.09079 | [0.07894, 0.1351] | estimated but includes real cycling -> upper bound |
| white noise, flow (relative) | 0.001133 | [0.001077, 0.001317] | estimated on RTU_SA_FLOW only; transferred by assumption to VAV/loop flows |
| white noise, power (relative) | 0.008117 | [0.006735, 0.009131] | estimated (VAV reheat, RTU) |
| additive power floor (fraction of series max) | 0.000948 | [0.000397, 0.00162] | estimated, quantum-limited |
| sub-hour variability about the hourly line, temp (K) | 0.327 | [0.209, 0.48] | proxy (part turbulence/cycling, part sensor) |
| sub-hour variability about the hourly line, value (K) | 1.35 | [1.14, 1.57] | proxy (part turbulence/cycling, part sensor) |
| sub-hour variability about the hourly line, flow (rel) | 0.0358 | [0.0327, 0.0388] | proxy (part turbulence/cycling, part sensor) |
| sub-hour variability about the hourly line, power (rel) | 0.581 | [0.475, 0.673] | proxy (part turbulence/cycling, part sensor) |
| quantisation step, temp | 0.00556 (K) | - | estimated |
| quantisation step, value | 0.00556 (K) | - | estimated |
| quantisation step, flow | 0.000301 (fraction of series p95) | - | estimated |
| quantisation step, power | 0.00253 (fraction of series max) | - | estimated |
| random dropout fraction (1-min samples) | 5.66e-05 | [0.00e+00, 1.30e-04] | estimated ~0: 83 events, mostly 1 min, one 55-min run |
| stale (exact-repeat >=60 min) fraction | 0 | [0, 0] | estimated 0: max exact-repeat run 7 min |
| static offset sd, VAV SAT sensors vs box median (K) | 0.164 | [0.152, 0.179] | PROXY (includes duct gradients) |
| static offset sd, room temps vs room median (K) | 0.614 | [0.509, 0.763] | PROXY, upper bound (real zone differences) |
| offset change per 90 d (random-walk scaling), VAV SAT | 0.089 | range [0.0468, 0.121] over 3 season pairs | PROXY + ASSUMED (not drift) |
| same, room temps | 0.384 | range [0.376, 0.534] | PROXY, contaminated by real load change |
| timestamp: missing minutes within a recorded day | 0 | 30/30 days complete | estimated |
| timestamp jitter < 1 min, inter-channel lag | prior 0-3 min / 0-5 min | - | ASSUMED (unobservable) |

Between-day spread of the noise level (sd of log per-day sigma; use as the per-building random-effect scale): temp 0.14, value 0.66, flow 0.32, power 0.41. Noise level differs strongly by season for discharge-air sensors (see section 3), i.e. the between-building/day spread is large and this is the dominant honest uncertainty.

## 2. What is well estimated / proxy / not estimable

Well estimated: quantisation steps; absence of random dropouts and stale runs in this logger (upper bound only); timestamp regularity; relative noise of RTU flow and power; air/room temperature white noise (as an upper limit, quantisation-limited).

Proxies only: calibration offsets (room spread is mostly real zone differences; VAV SAT spread includes duct gradients), the 'drift' numbers (differences between files 2 months to 9 months apart, different years/loads; they bound how much offsets can change, they are not drift measurements), sub-hour variability.

Not estimable from this data (flagged assumed=True in the JSON): long-term (months/years) sensor drift; flow-sensor noise for individual VAV boxes and water loops (only RTU_SA_FLOW exists); hour-scale dropouts / stale runs in field BAS exports; true calibration offsets separate from real spatial temperature gradients; coil/water-side sensor noise (no water-side data). Field priors for hour-scale dropouts/stale runs and timestamp jitter/lag are assumptions and are labelled as such.

## 3. Noise by group and season (K for temperature, relative for power/flow; second-difference method)

| group | fall | spring | summer | winter |
|---|---|---|---|---|
| room_temp | 0.0220 | 0.0181 | 0.0156 | 0.0158 |
| oat | 0.0364 | 0.0539 | 0.0601 | 0.0322 |
| ra_temp | 0.0098 | 0.0122 | 0.0098 | 0.0114 |
| vav_sat | 0.0761 | 0.3108 | 0.0683 | 0.1628 |
| rtu_sat | 0.1547 | 0.5988 | 0.1507 | 0.3646 |
| ma_temp | 0.0171 | 0.0293 | 0.0200 | 0.0247 |
| vav_power | 0.0157 | 0.0367 | 0.0206 | 0.0126 |
| rtu_power | 0.0023 | 0.0037 | 0.0033 | 0.0025 |
| rtu_flow | 0.0011 | 0.0023 | 0.0011 | 0.0015 |

(ma_temp is coarsely quantised, 0.3 degF, so its value is not a white-noise estimate. Spring/Winter discharge-air sigma is 3-10x Summer/Fall: real supply-air cycling, so treat as an upper bound on sensor noise.)

## 4. Validation: estimate on two seasons, check on the other two

| quantity | fit (Fall+Spring) | hold (Summer+Winter) | ratio | CIs overlap | fit (Sum+Win) | hold (Fall+Spr) | CIs overlap |
|---|---|---|---|---|---|---|---|
| noise_temp | 0.0212 | 0.0165 | 0.78 | False | 0.0165 | 0.0212 | False |
| noise_temp_sdlog_between_days | 0.0825 | 0.0314 | 0.38 | False | 0.0314 | 0.0825 | False |
| subhour_temp | 0.225 | 0.438 | 1.95 | True | 0.438 | 0.225 | True |
| noise_value | 0.0918 | 0.0842 | 0.92 | True | 0.0842 | 0.0918 | True |
| noise_value_sdlog_between_days | 0.754 | 0.505 | 0.67 | True | 0.505 | 0.754 | True |
| subhour_value | 1.43 | 1.18 | 0.82 | True | 1.18 | 1.43 | True |
| noise_power | 0.00812 | 0.00638 | 0.79 | True | 0.00638 | 0.00812 | True |
| noise_power_sdlog_between_days | 0.308 | 0.516 | 1.67 | False | 0.516 | 0.308 | True |
| subhour_power | 0.667 | 0.38 | 0.57 | False | 0.38 | 0.667 | False |
| noise_flow | 0.00117 | 0.00113 | 0.97 | True | 0.00113 | 0.00117 | True |
| noise_flow_sdlog_between_days | 0.375 | 0.233 | 0.62 | True | 0.233 | 0.375 | True |
| subhour_flow | 0.0341 | 0.0381 | 1.12 | True | 0.0381 | 0.0341 | True |
| power_abs_frac | 0.000662 | 0.00203 | 3.07 | True | 0.00203 | 0.000662 | True |
| rand_dropout_frac | 9.44e-05 | 0 | 0.00 | True | 0 | 9.44e-05 | True |
| stale_frac_ge60 | 0 | 0 | - | True | 0 | 0 | True |
| room_offset_sd_K | 0.791 | 0.443 | 0.56 | False | 0.443 | 0.791 | False |
| vav_sat_offset_sd_K | 0.181 | 0.136 | 0.75 | False | 0.136 | 0.181 | False |

Agreement: 23/34 directional checks have overlapping CIs. Failures: temperature white noise (ratio ~1.3, both at the quantisation floor, tiny CIs, so 'overlap' fails on a difference of 0.005 K), sub-hour power variability (factor ~1.8), static offset sds (room 0.79 vs 0.44 K, VAV SAT 0.18 vs 0.14 K: offsets are season-dependent, consistent with being partly physical). struct-NaN fraction differs because the Fall file fills fan-off periods instead of leaving NaN (an export artefact, not a property of sensors). Noise levels of flow, power, discharge temperature, and dropout/stale rates transfer well.

## 5. Sampling irregularity

All 30 days have exactly 1440 consecutive 1-min stamps, zero duplicate stamps, zero non-zero seconds; maximum gap inside a day 60 s. Between recorded days the files skip 2-15 days (sparse sampling of days, not logger outages). Timestamp jitter below 1 min and channel lag are unobservable.

## 6. Calibration-offset proxies (K)

| comparison | persistent sd by season (fall/spring/summer/winter) | day-to-day sd within season |
|---|---|---|
| room_temp_vs_median_all_hours | 1.05 / 0.41 / 0.29 / 0.73 | 0.27 / 0.12 / 0.13 / 0.24 |
| room_temp_vs_median_unoccupied | 1.05 / 0.81 / 0.49 / 0.97 | 0.31 / 0.17 / 0.15 / 0.31 |
| vav_sat_vs_median_unheated | 0.20 / 0.17 / 0.13 / 0.18 | 0.06 / 0.04 / 0.01 / 0.00 |

Between-season change of per-sensor offset (rms, K; gap days; sqrt-scaled to 90 d):

- room_temp_vs_median_all_hours: fall->spring 0.80 K over 202 d (0.53/90d); spring->summer 0.32 K over 63 d (0.38/90d); summer->winter 0.65 K over 265 d (0.38/90d)
- room_temp_vs_median_unoccupied: fall->spring 0.73 K over 202 d (0.49/90d); spring->summer 0.55 K over 63 d (0.66/90d); summer->winter 0.76 K over 265 d (0.45/90d)
- vav_sat_vs_median_unheated: fall->spring 0.13 K over 202 d (0.09/90d); spring->summer 0.10 K over 63 d (0.12/90d); summer->winter 0.08 K over 265 d (0.05/90d)

## 7. Operating variability a simulator should cover (per season, dev days)

| item | fall | spring | summer | winter |
|---|---|---|---|---|
| OAT daily min range (C) | 8.5 to 21.2 | -2.8 to 11.2 | 14.2 to 21.0 | -17.8 to 12.7 |
| OAT daily max range (C) | 20.2 to 31.8 | 10.6 to 26.2 | 28.7 to 34.1 | 12.6 to 25.2 |
| OAT diurnal amplitude (C) | 10.0 | 13.4 | 12.8 | 10.2 |
| occupied hours/day, start-end (h) | 15, 7-22 | 15, 7-22 | 15, 7-22 | 15, 7-22 |
| cool/heat setpoint occupied (C) | 24.0/21.0 (band 3.0 K) | 24.0/21.0 (band 3.0 K) | 24.0/21.0 (band 3.0 K) | 24.0/21.0 (band 3.0 K) |
| setpoints unoccupied (C) | 29.4/15.6 (band 13.9 K) | 29.4/15.6 (band 13.9 K) | 29.4/15.6 (band 13.9 K) | 29.4/15.6 (band 13.9 K) |
| room temp mean, p5-p95 (C) | 22.7, 20.5-25.7 | 21.8, 20.3-23.9 | 23.6, 21.2-26.1 | 21.4, 19.8-23.6 |
| cross-room sd (K) / diurnal amp (K) | 1.14 / 3.0 | 0.68 / 2.1 | 0.59 / 4.4 | 0.87 / 1.8 |
| RTU SAT occupied p5/p50/p95 (C) | 11.7/13.0/16.1 | 9.4/13.2/18.5 | 11.6/13.5/15.5 | 10.8/13.4/17.0 |
| SAT daily-median range (C) | 12.5 to 14.1 | 12.4 to 13.5 | 13.3 to 13.8 | 12.5 to 13.6 |
| SAT-vs-OAT correlation of daily medians (n<=12) | 0.70 | -0.52 | -0.19 | -0.94 |
| OA damper occupied mean / frac<=10% / levels | 13% / 0.96 / 100 | 24% / 0.75 / 459 | 10% / 1.00 / 2 | 33% / 0.63 / 380 |
| RTU flow occupied p5-p95 (cfm) | 3133-3392 | 3077-3405 | 3168-3806 | 3064-3242 |
| total VAV reheat peak hour / peak (W) | 21 h / 7162 | 7 h / 9431 | 21 h / 1434 | 21 h / 10724 |

Reading: occupancy is a fixed 07:00-22:00 schedule every day (no weekday/weekend variation is observable in 30 sparse days); setpoints are fixed at 24.0/21.0 C occupied and 29.4/15.6 C unoccupied (no adaptive band); RTU SAT sits near 13 C with a daily-median spread of about 1-2 K (no material reset; the season correlations use only 6 days and are not evidence of reset); the OA damper sits at a 10% minimum in summer and modulates 0-100% in Fall/Spring/Winter (economizer). The RTU has no SAT-setpoint column, so setpoint level is inferred from the measurement.
