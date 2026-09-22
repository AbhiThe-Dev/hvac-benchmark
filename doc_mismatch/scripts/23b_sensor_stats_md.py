"""Render results/docmismatch/dr/sensor_stats.md from sensor_stats.json (plain-language summary + tables)."""
import json
from pathlib import Path

R = Path(__file__).resolve().parents[2] / "results" / "docmismatch" / "dr"
S = json.load(open(R / "sensor_stats.json"))
P, H = S["profile_inputs"], S["headline_all"]


def ci(c, f="{:.3g}"):
    return "n/a" if not c or c[0] is None else f"[{f.format(c[0])}, {f.format(c[1])}]"


L = []
w = L.append
w("# Sensor / telemetry statistics from real DEV data\n")
w("Source: ORNL FRP RTU-VAV building (LBNL FDD RTU set), 1-minute, DEV files only: ERTU_{Fall_2020,Spring_2021,Summer_2021,Winter_2022} (14 days) + Inc_Eco_* (16 days) = 30 days "
  f"({S['meta']['days_per_season']}). Sealed OA_damper*/SA_temp_bias* files were never opened (prefix guard in `scripts/23_sensor_stats.py`). "
  "CIs are 95% percentile bootstrap over whole days (300 resamples); days are treated as exchangeable, which understates uncertainty for building-level effects (one building, 4 seasons).\n")
w("Inc_Eco files are economizer-setpoint-fault days; they are used here only because sensor statistics should not depend on that fault. Note the Fall file is a processed export (float artefacts, fan-off flow filled with 0 rather than NaN, RTU_MA_TEMP at 0.3 degF resolution), unlike Spring/Summer/Winter.\n")
w("## 1. Headline table (per signal class)\n")
w("| quantity | estimate | 95% CI | status |\n|---|---|---|---|")
rows = [("white noise sd, temperature (K)", "noise", "temp", "estimated, quantisation-limited (quantum 0.0056 K)"),
        ("white noise sd, BAS-point/discharge temp (K)", "noise", "value", "estimated but includes real cycling -> upper bound"),
        ("white noise, flow (relative)", "noise", "flow", "estimated on RTU_SA_FLOW only; transferred by assumption to VAV/loop flows"),
        ("white noise, power (relative)", "noise", "power", "estimated (VAV reheat, RTU)")]
for lab, a, b, st in rows:
    e = P["noise_sd"][b]
    w(f"| {lab} | {e['est']:.4g} | {ci(e['ci95'], '{:.4g}')} | {st} |")
e = P["power_abs_frac"]
w(f"| additive power floor (fraction of series max) | {e['est']:.3g} | {ci(e['ci95'])} | estimated, quantum-limited |")
for b, u in (("temp", "K"), ("value", "K"), ("flow", "rel"), ("power", "rel")):
    e = P["subhour_sd"][b]
    w(f"| sub-hour variability about the hourly line, {b} ({u}) | {e['est']:.3g} | {ci(e['ci95'])} | proxy (part turbulence/cycling, part sensor) |")
for b in ("temp", "value", "flow", "power"):
    e = P["quant"][b]
    w(f"| quantisation step, {b} | {e['est']:.3g} ({e['unit']}) | - | estimated |")
e = P["dropout"]["frac"]
w(f"| random dropout fraction (1-min samples) | {e['est']:.2e} | {ci(e['ci95'], '{:.2e}')} | estimated ~0: 83 events, mostly 1 min, one 55-min run |")
e = P["stale"]["frac"]
w(f"| stale (exact-repeat >=60 min) fraction | {e['est']:.2g} | {ci(e['ci95'])} | estimated 0: max exact-repeat run 7 min |")
e = P["offset_sd_K"]["value"]
w(f"| static offset sd, VAV SAT sensors vs box median (K) | {e['est']:.3f} | {ci(e['ci95'])} | PROXY (includes duct gradients) |")
e = P["offset_sd_K"]["temp"]
w(f"| static offset sd, room temps vs room median (K) | {e['est']:.3f} | {ci(e['ci95'])} | PROXY, upper bound (real zone differences) |")
e = P["drift_K_per_90d"]["random_walk_sd"]
w(f"| offset change per 90 d (random-walk scaling), VAV SAT | {e['est']:.3f} | range {ci(e['ci95'])} over 3 season pairs | PROXY + ASSUMED (not drift) |")
e = P["drift_K_per_90d"]["room_upper"]
w(f"| same, room temps | {e['est']:.3f} | range {ci(e['ci95'])} | PROXY, contaminated by real load change |")
w("| timestamp: missing minutes within a recorded day | 0 | 30/30 days complete | estimated |")
w("| timestamp jitter < 1 min, inter-channel lag | prior 0-3 min / 0-5 min | - | ASSUMED (unobservable) |")
w("")
w("Between-day spread of the noise level (sd of log per-day sigma; use as the per-building random-effect scale): "
  + ", ".join(f"{k} {P['noise_sd'][k]['sdlog_between_days']:.2f}" for k in P['noise_sd']) + ". Noise level differs strongly by season for discharge-air sensors "
  "(see section 3), i.e. the between-building/day spread is large and this is the dominant honest uncertainty.\n")
w("## 2. What is well estimated / proxy / not estimable\n")
w("Well estimated: quantisation steps; absence of random dropouts and stale runs in this logger (upper bound only); timestamp regularity; relative noise of RTU flow and power; "
  "air/room temperature white noise (as an upper limit, quantisation-limited).\n")
w("Proxies only: calibration offsets (room spread is mostly real zone differences; VAV SAT spread includes duct gradients), the 'drift' numbers (differences between files 2 months to 9 months apart, "
  "different years/loads; they bound how much offsets can change, they are not drift measurements), sub-hour variability.\n")
w("Not estimable from this data (flagged assumed=True in the JSON): " + "; ".join(P["not_estimable"]) + ". Field priors for hour-scale dropouts/stale runs and timestamp jitter/lag are assumptions and are labelled as such.\n")
w("## 3. Noise by group and season (K for temperature, relative for power/flow; second-difference method)\n")
w("| group | fall | spring | summer | winter |\n|---|---|---|---|---|")
for g, d in S["noise_by_group_season"].items():
    w(f"| {g} | " + " | ".join(f"{d[s]['sigma']:.4f}" for s in ["fall", "spring", "summer", "winter"]) + " |")
w("\n(ma_temp is coarsely quantised, 0.3 degF, so its value is not a white-noise estimate. Spring/Winter discharge-air sigma is 3-10x Summer/Fall: real supply-air cycling, so treat as an upper bound on sensor noise.)\n")
w("## 4. Validation: estimate on two seasons, check on the other two\n")
w("| quantity | fit (Fall+Spring) | hold (Summer+Winter) | ratio | CIs overlap | fit (Sum+Win) | hold (Fall+Spr) | CIs overlap |\n|---|---|---|---|---|---|---|---|")
V1, V2 = S["validation"]["fall+spring -> summer+winter"], S["validation"]["summer+winter -> fall+spring"]
ok = 0
tot = 0
for k in V1:
    if k in ("fan_on_frac", "struct_nan_frac") or k.startswith("stale_excess") or k.endswith("ge5") or k.endswith("ge10") or k.endswith("ge30"):
        continue
    a, b = V1[k], V2[k]
    tot += 2
    ok += int(a["ci_overlap"]) + int(b["ci_overlap"])
    rt = f"{a['ratio']:.2f}" if a["ratio"] is not None else "-"
    w(f"| {k} | {a['fit_est']:.3g} | {a['holdout_est']:.3g} | {rt} | {a['ci_overlap']} | {b['fit_est']:.3g} | {b['holdout_est']:.3g} | {b['ci_overlap']} |")
w(f"\nAgreement: {ok}/{tot} directional checks have overlapping CIs. Failures: temperature white noise (ratio ~1.3, both at the quantisation floor, tiny CIs, so 'overlap' fails on a difference of 0.005 K), "
  "sub-hour power variability (factor ~1.8), static offset sds (room 0.79 vs 0.44 K, VAV SAT 0.18 vs 0.14 K: offsets are season-dependent, consistent with being partly physical). "
  "struct-NaN fraction differs because the Fall file fills fan-off periods instead of leaving NaN (an export artefact, not a property of sensors). Noise levels of flow, power, discharge temperature, and dropout/stale rates transfer well.\n")
w("## 5. Sampling irregularity\n")
w("All 30 days have exactly 1440 consecutive 1-min stamps, zero duplicate stamps, zero non-zero seconds; maximum gap inside a day 60 s. Between recorded days the files skip 2-15 days "
  "(sparse sampling of days, not logger outages). Timestamp jitter below 1 min and channel lag are unobservable.\n")
w("## 6. Calibration-offset proxies (K)\n")
w("| comparison | persistent sd by season (fall/spring/summer/winter) | day-to-day sd within season |\n|---|---|---|")
for k, v in S["offsets_proxy"].items():
    w(f"| {k} | " + " / ".join(f"{v['persistent_sd_by_season_K'][s]:.2f}" for s in ["fall", "spring", "summer", "winter"]) + " | " + " / ".join(f"{v['day_to_day_sd_within_season_K'][s]:.2f}" for s in ["fall", "spring", "summer", "winter"]) + " |")
w("\nBetween-season change of per-sensor offset (rms, K; gap days; sqrt-scaled to 90 d):\n")
for k, v in S["offsets_proxy"].items():
    w(f"- {k}: " + "; ".join(f"{p['a']}->{p['b']} {p['rms_offset_change_K']:.2f} K over {p['gap_days']} d ({p['per_90d_if_random_walk_K']:.2f}/90d)" for p in v["between_season_changes"]))
w("")
w("## 7. Operating variability a simulator should cover (per season, dev days)\n")
O = S["operating_variability"]
w("| item | fall | spring | summer | winter |\n|---|---|---|---|---|")
def row(lab, f):
    w(f"| {lab} | " + " | ".join(f(O[s]) for s in ["fall", "spring", "summer", "winter"]) + " |")
rg = lambda a, u="": f"{a[0]:.1f} to {a[1]:.1f}{u}"  # noqa: E731
row("OAT daily min range (C)", lambda o: rg(o["oat_C_min"]))
row("OAT daily max range (C)", lambda o: rg(o["oat_C_max"]))
row("OAT diurnal amplitude (C)", lambda o: f"{o['oat_diurnal_amp_C']:.1f}")
row("occupied hours/day, start-end (h)", lambda o: f"{o['occ_hours'][1]:.0f}, {o['occ_start_h'][0]:.0f}-{o['occ_end_h'][0]:.0f}")
row("cool/heat setpoint occupied (C)", lambda o: f"{o['cspt_occ_C'][0]:.1f}/{o['hspt_occ_C'][0]:.1f} (band {o['band_width_occ_K'][0]:.1f} K)")
row("setpoints unoccupied (C)", lambda o: f"{o['cspt_unocc_C'][0]:.1f}/{o['hspt_unocc_C'][0]:.1f} (band {o['band_width_unocc_K'][0]:.1f} K)")
row("room temp mean, p5-p95 (C)", lambda o: f"{o['room_T_C']['mean']:.1f}, {o['room_T_C']['p5']:.1f}-{o['room_T_C']['p95']:.1f}")
row("cross-room sd (K) / diurnal amp (K)", lambda o: f"{o['room_T_C']['cross_room_sd_K']:.2f} / {o['room_T_C']['diurnal_amp_K']:.1f}")
row("RTU SAT occupied p5/p50/p95 (C)", lambda o: f"{o['rtu_sat_occ_C']['p5']:.1f}/{o['rtu_sat_occ_C']['p50']:.1f}/{o['rtu_sat_occ_C']['p95']:.1f}")
row("SAT daily-median range (C)", lambda o: rg(o["rtu_sat_daymedian_C"]))
row("SAT-vs-OAT correlation of daily medians (n<=12)", lambda o: "n/a" if o["rtu_sat_reset_corr_with_oat"] is None else f"{o['rtu_sat_reset_corr_with_oat']:.2f}")
row("OA damper occupied mean / frac<=10% / levels", lambda o: f"{o['oa_damper_pct']['occ_mean']:.0f}% / {o['oa_damper_pct']['frac_occ_at_le10']:.2f} / {o['oa_damper_pct']['n_levels']}")
row("RTU flow occupied p5-p95 (cfm)", lambda o: f"{o['rtu_flow_cfm_occ']['p5']:.0f}-{o['rtu_flow_cfm_occ']['p95']:.0f}")
row("total VAV reheat peak hour / peak (W)", lambda o: f"{o['vav_reheat_total_W_hourly']['peak_hour']} h / {o['vav_reheat_total_W_hourly']['peak']:.0f}")
w("\nReading: occupancy is a fixed 07:00-22:00 schedule every day (no weekday/weekend variation is observable in 30 sparse days); setpoints are fixed at 24.0/21.0 C occupied "
  "and 29.4/15.6 C unoccupied (no adaptive band); RTU SAT sits near 13 C with a daily-median spread of about 1-2 K (no material reset; the season correlations use only 6 days and are not evidence of reset); "
  "the OA damper sits at a 10% minimum in summer and modulates 0-100% in Fall/Spring/Winter (economizer). The RTU has no SAT-setpoint column, so setpoint level is inferred from the measurement.\n")
open(R / "sensor_stats.md", "w").write("\n".join(L))
print("wrote md", len(L))
