"""Estimate sensor/telemetry statistics from the DEV real files ONLY (ERTU_* baseline + Inc_Eco_*).
Sealed files (OA_damper*, SA_temp_bias*) are never opened: the file list is built from an allow-list of prefixes.
Writes results/docmismatch/dr/sensor_stats.json and sensor_stats.md.  numpy only.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import warnings

import numpy as np

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "docmismatch" / "dr"
RTU = ROOT / "data_cache" / "timeseries" / "rtu_exp"
FLT = ROOT / "data_cache" / "timeseries" / "rtu_faults"
ROOMS = ["102", "103", "104", "105", "106", "202", "203", "204", "205", "206"]
F2K = 5.0 / 9.0
SEASON_OF = {"Fall_2020": "fall", "Spring_2021": "spring", "Summer_2021": "summer", "Winter_2022": "winter"}
ORDER = ["fall", "spring", "summer", "winter"]
B = 300
FAN_ON_W = 100.0


def dev_files():
    fs = sorted(RTU.glob("ERTU_*.csv")) + sorted(FLT.glob("Inc_Eco_*.csv"))
    for f in fs:  # hard guard
        assert f.name.startswith(("ERTU_", "Inc_Eco_")), f
        assert not f.name.startswith(("OA_damper", "SA_temp_bias")), f
    return fs


def load_days():
    days, filestats = [], []
    for f in dev_files():
        rows = list(csv.reader(open(f)))
        hdr = rows[0][1:]
        t = np.array([r[0] for r in rows[1:]], dtype="datetime64[s]")
        X = np.array([[float(v) if v != "" else np.nan for v in r[1:]] for r in rows[1:]])
        season = SEASON_OF["_".join(f.stem.split("_")[-2:])]
        fam = "baseline" if f.name.startswith("ERTU") else "Inc_Eco"
        d = np.diff(t).astype(int)
        D = t.astype("datetime64[D]")
        ud = np.unique(D)
        filestats.append(dict(file=f.name, rows=len(t), n_days=len(ud), step_counts={str(k): int(v) for k, v in zip(*np.unique(d, return_counts=True))},
                              duplicates=int((d == 0).sum()), nonzero_seconds=int((t.astype("datetime64[s]").astype(int) % 60 != 0).sum()), gaps_days=[int((b - a) / np.timedelta64(1, "D")) for a, b in zip(ud[:-1], ud[1:])]))
        for u in ud:
            m = D == u
            if m.sum() != 1440:
                continue
            tm = t[m]
            assert (np.diff(tm).astype(int) == 60).all()
            days.append(dict(day=str(u), season=season, family=fam, file=f.name, t=tm, **{n: X[m, j] for j, n in enumerate(hdr)}))
    return days, filestats


# ---------------------------------------------------------------- channel groups
GROUPS = {  # group -> (cls, columns, kind)
    "room_temp": ("temp", [f"TERM_RM_TEMP_{r}" for r in ROOMS], "T"),
    "oat": ("temp", ["RTU_OA_TEMP"], "T"),
    "ra_temp": ("temp", ["RTU_RA_TEMP"], "T"),
    "vav_sat": ("value", [f"VAV_RM_SAT_{r}" for r in ROOMS], "T"),
    "rtu_sat": ("value", ["RTU_SA_TEMP"], "T"),
    "ma_temp": (None, ["RTU_MA_TEMP"], "T"),
    "vav_power": ("power", [f"VAV_RM_WATT_{r}" for r in ROOMS], "P150"),
    "rtu_power": ("power", ["RTU_SA_FAN_WATT", "RTU_COMP_WATT_1"], "P500"),
    "rtu_flow": ("flow", ["RTU_SA_FLOW"], "P500"),
}
LEVEL_THR = {"P150": 150.0, "P500": 500.0}


def d2_of(x):
    """second difference over triplets, plus level at centre"""
    d = x[2:] - 2 * x[1:-1] + x[:-2]
    return d, x[1:-1], np.abs(x[2:] - x[:-2])


def mad_sigma(v):
    """robust white sd from second-difference values (var(d2)=6 sigma^2).  Uses a 95%-trimmed RMS (truncated-normal corrected) rather than the
    MAD because the data are quantised: with sd < quantum the MAD is a degenerate multiple of the quantum."""
    if len(v) < 30:
        return np.nan
    a = np.abs(v)
    k = a <= np.percentile(a, 95)
    return float(np.sqrt(np.mean(a[k] ** 2) / 0.7588 / 6.0))


_TT = np.arange(60) - 29.5


def detrended_var(H):
    """within-hour variance about the best straight line (a linearly-interpolated hourly truth already carries the trend)"""
    b = (H * _TT).sum(1) / (_TT ** 2).sum()
    r = (H - H.mean(1, keepdims=True)) - b[:, None] * _TT
    return (r ** 2).sum(1) / 58.0


def per_day_features(d):
    """everything that bootstrap-over-days needs, per day"""
    out = {}
    fan_on = np.nan_to_num(d["RTU_SA_FAN_WATT"], nan=0.0) > FAN_ON_W
    for g, (cls, cols, kind) in GROUPS.items():
        d2s, lv_d2 = [], []
        sub_var, sub_lv = [], []
        low_d2 = []
        for c in cols:
            x = d[c].copy()
            if kind == "T":
                x = x * F2K  # K (absolute offset irrelevant for differences)
                d2, lv, rng2 = d2_of(x)
                ok = np.isfinite(d2)
                d2s.append(d2[ok])
                # sub-hour variability: within-hour deviation from hourly mean, hours with 60 finite samples
                H = x.reshape(24, 60)
                okh = np.isfinite(H).all(1)
                if okh.any():
                    sub_var.append(detrended_var(H[okh]))
            else:
                d2, lv, rng2 = d2_of(x)
                ok = np.isfinite(d2) & (lv > LEVEL_THR[kind]) & (rng2 < 0.05 * np.maximum(lv, 1e-9))
                d2s.append((d2[ok] / lv[ok]))
                H = x.reshape(24, 60)
                mu = H.mean(1)
                okh = np.isfinite(H).all(1) & (mu > LEVEL_THR[kind])
                if okh.any():
                    sub_var.append(detrended_var(H[okh]) / mu[okh] ** 2)
                # additive floor: standby (<30W VAV/ <5% max) samples, noise in raw units, scaled by file channel max later
                lowm = np.isfinite(d2) & (lv < (30.0 if kind == "P150" else 0.02 * 1e9)) & (rng2 < 5.0)
                if kind == "P150":
                    low_d2.append(np.c_[d2[lowm], np.full(lowm.sum(), np.nanmax(x))])
        out[g] = dict(d2=np.concatenate(d2s) if d2s else np.array([]), subvar=np.concatenate(sub_var) if sub_var else np.array([]),
                      low=np.concatenate(low_d2) if low_d2 else np.zeros((0, 2)))
    for cls, groups in (("temp", ["room_temp", "oat", "ra_temp"]), ("value", ["vav_sat", "rtu_sat"]), ("power", ["vav_power", "rtu_power"]), ("flow", ["rtu_flow"])):
        out["cls_" + cls] = np.concatenate([out[g]["d2"] for g in groups])
    return out, fan_on


def quant_info(days):
    """per group: quantum (native units) and fraction of samples on that grid, per season"""
    res = {}
    for g, (cls, cols, kind) in GROUPS.items():
        for s in ORDER:
            qs, fr = [], []
            for c in cols:
                v = np.concatenate([d[c][np.isfinite(d[c])] for d in days if d["season"] == s])
                dv = np.abs(np.diff(v))
                nz = dv[dv > 1e-6]
                if len(nz) < 20:
                    continue
                q = float(np.round(np.percentile(nz, 1.0), 4))
                r = v / q
                qs.append(q)
                fr.append(float((np.abs(r - np.round(r)) < 1e-3 * np.maximum(1, np.abs(r) * 1e-3)).mean()))
            res[(g, s)] = (float(np.median(qs)) if qs else np.nan, float(np.median(fr)) if fr else np.nan)
    return res


# ---------------------------------------------------------------- missing / stale
def runs(mask):
    d = np.diff(np.r_[0, mask.astype(int), 0])
    s, e = np.where(d == 1)[0], np.where(d == -1)[0]
    return s, e - s


def missing_stats(d):
    fan = d["RTU_SA_FAN_WATT"]
    fan_on = np.nan_to_num(fan, nan=0.0) > FAN_ON_W
    fan_group = ["RTU_SA_TEMP", "RTU_RA_TEMP", "RTU_SA_FLOW"] + [f"VAV_RM_SAT_{r}" for r in ROOMS]
    n_struct = n_rand = n_tot = 0
    rand_runs = []
    allnan_rows = np.zeros(1440, bool)
    for c, arr in d.items():
        if c in ("t", "day", "season", "family", "file"):
            continue
    cols = [c for c in d if c not in ("t", "day", "season", "family", "file")]
    M = np.array([np.isnan(d[c]) for c in cols])  # (ch, T)
    allnan_rows = M.all(0)
    for c in cols:
        m = np.isnan(d[c])
        n_tot += 1440
        if c in fan_group:
            struct = m & ~fan_on
            rand = m & fan_on
        else:
            struct = np.zeros(1440, bool)
            rand = m
        n_struct += int(struct.sum())
        n_rand += int(rand.sum())
        # runs of random dropouts counted per channel
        if rand.any():
            rand_runs += list(runs(rand)[1])
    return dict(n_tot=n_tot, n_struct=n_struct, n_rand=n_rand, rand_runs=rand_runs, allnan_rows=int(allnan_rows.sum()), fan_on_frac=float(fan_on.mean()))


STALE_CH = [f"TERM_RM_TEMP_{r}" for r in ROOMS] + [f"VAV_RM_SAT_{r}" for r in ROOMS] + ["RTU_OA_TEMP", "RTU_SA_TEMP", "RTU_RA_TEMP", "RTU_SA_FLOW"]
STALE_L = [5, 10, 30, 60]  # minutes


def stale_stats(d, rng):
    """fraction of valid samples that sit in an exact-repeat run of >=L identical values, versus a Bernoulli(repeat-prob) null."""
    out = {L: [0, 0, 0.0] for L in STALE_L}  # observed samples in runs, n valid, null expected
    lens = []
    for c in STALE_CH:
        x = d[c]
        ok = np.isfinite(x) & (np.nan_to_num(d["RTU_SA_FAN_WATT"], nan=0.0) > FAN_ON_W)  # fan-off periods carry structural flat/zero values
        if ok.sum() < 200:
            continue
        # split into contiguous finite segments
        rep = np.zeros(1440, bool)
        rep[1:] = (x[1:] == x[:-1]) & ok[1:] & ok[:-1]
        r = rep[1:][ok[1:] & ok[:-1]].mean()
        s, ln = runs(rep)  # ln = number of repeats; identical-value run length = ln+1
        lens += list(ln + 1)
        nnull = rng.random(1440) < r
        sn, lnn = runs(nnull)
        for L in STALE_L:
            out[L][0] += int(((ln + 1)[ln + 1 >= L]).sum())
            out[L][2] += float(((lnn + 1)[lnn + 1 >= L]).sum())
            out[L][1] += int(ok.sum())
    return out, lens


# ---------------------------------------------------------------- offsets (proxy)
def room_offsets(d, mode):
    T = np.array([d[f"TERM_RM_TEMP_{r}"] for r in ROOMS]) * F2K
    occ = d["OCCU_MOD"] > 0.5
    sel = np.isfinite(T).all(0) & (np.ones(1440, bool) if mode == "all" else ~occ)
    if sel.sum() < 120:
        return None
    med = np.median(T[:, sel], axis=0)
    return (T[:, sel] - med).mean(1)


def vav_offsets(d):
    S = np.array([d[f"VAV_RM_SAT_{r}"] for r in ROOMS]) * F2K
    W = np.array([d[f"VAV_RM_WATT_{r}"] for r in ROOMS])
    fan_on = np.nan_to_num(d["RTU_SA_FAN_WATT"], nan=0.0) > FAN_ON_W
    sel = fan_on & np.isfinite(S).all(0) & (W < 30).all(0)
    if sel.sum() < 60:
        return None, int(sel.sum())
    med = np.median(S[:, sel], axis=0)
    return (S[:, sel] - med).mean(1), int(sel.sum())


# ---------------------------------------------------------------- estimation of headline stats, given a set of days
def est_headlines(days, feats, idx, offs_room, offs_vav):
    """all headline scalar stats for the day index list idx (with repetition allowed)."""
    R = {}
    for cls, groups in (("temp", ["room_temp", "oat", "ra_temp"]), ("value", ["vav_sat", "rtu_sat"]), ("power", ["vav_power", "rtu_power"]), ("flow", ["rtu_flow"])):
        sg = np.array([mad_sigma(feats[i]["cls_" + cls]) for i in idx])
        sg = sg[np.isfinite(sg) & (sg > 0)]
        R[f"noise_{cls}"] = float(np.median(sg))  # median of per-day sigmas
        R[f"noise_{cls}_sdlog_between_days"] = float(np.std(np.log(sg), ddof=1))
        sv = np.concatenate([feats[i][g]["subvar"] for i in idx for g in groups])
        R[f"subhour_{cls}"] = float(np.sqrt(np.mean(sv))) if len(sv) else np.nan
    low = np.concatenate([feats[i]["vav_power"]["low"] for i in idx])
    R["power_abs_frac"] = float(1.4826 * np.median(np.abs(low[:, 0])) / np.sqrt(6) / np.median(low[:, 1])) if len(low) > 50 else np.nan
    # missingness
    ms = [missing_of[i] for i in idx]
    ntot = sum(m["n_tot"] for m in ms)
    R["struct_nan_frac"] = sum(m["n_struct"] for m in ms) / ntot
    R["rand_dropout_frac"] = sum(m["n_rand"] for m in ms) / ntot
    R["fan_on_frac"] = float(np.mean([m["fan_on_frac"] for m in ms]))
    for L in STALE_L:
        o = sum(stale_of[i][0][L][0] for i in idx)
        n = sum(stale_of[i][0][L][1] for i in idx)
        nu = sum(stale_of[i][0][L][2] for i in idx)
        R[f"stale_frac_ge{L}"] = o / n
        R[f"stale_excess_ge{L}"] = (o - nu) / n
    # offsets: sd across sensors of the mean (over selected days) offset
    ro = [offs_room[i] for i in idx if offs_room[i] is not None]
    R["room_offset_sd_K"] = float(np.std(np.mean(ro, 0), ddof=1)) if len(ro) else np.nan
    vo = [offs_vav[i] for i in idx if offs_vav[i] is not None]
    R["vav_sat_offset_sd_K"] = float(np.std(np.mean(vo, 0), ddof=1)) if len(vo) else np.nan
    return R


def boot(days, feats, idx0, rng, Bn=B):
    idx0 = np.array(idx0)
    base = est_headlines(days, feats, idx0, offs_room, offs_vav)
    reps = [est_headlines(days, feats, rng.choice(idx0, len(idx0)), offs_room, offs_vav) for _ in range(Bn)]
    out = {}
    for k, v in base.items():
        arr = np.array([r[k] for r in reps], float)
        arr = arr[np.isfinite(arr)]
        out[k] = dict(est=float(v), ci95=[float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))] if len(arr) > 10 else [None, None], n_days=int(len(idx0)))
    return out


# ---------------------------------------------------------------- operating variability
def _fill(d):
    d = dict(d)
    ix = np.arange(1440)
    for c in list(d):
        if c in ("t", "day", "season", "family", "file") or c in ("RTU_SA_TEMP", "RTU_SA_FLOW", "RTU_RA_TEMP") or c.startswith("VAV_RM_SAT"):
            continue
        x = d[c]
        m = np.isfinite(x)
        if not m.all() and m.any():
            d[c] = np.interp(ix, ix[m], x[m])
    return d


def op_table(days, idxs):
    days = [_fill(d) for d in days]
    rows = {}
    for s in ORDER:
        di = [days[i] for i in idxs if days[i]["season"] == s]
        oat = np.array([d["RTU_OA_TEMP"] * F2K - 273.15 * 0 for d in di])  # K delta only; convert to degC below
        oatC = (np.array([d["RTU_OA_TEMP"] for d in di]) - 32) * F2K
        occ = np.array([d["OCCU_MOD"] for d in di]) > 0.5
        hrs_occ = occ.sum(1) / 60
        st, en = [], []
        for o in occ:
            w = np.where(o)[0]
            st.append(w[0] / 60 if len(w) else np.nan)
            en.append((w[-1] + 1) / 60 if len(w) else np.nan)
        cs = np.array([d["TERM_RM_TEMP_CSPT"] for d in di])
        hs = np.array([d["TERM_RM_TEMP_HSPT"] for d in di])
        allocc = occ.any()
        def band(m):
            return ((cs[m] - hs[m]) * F2K)
        room = np.array([[d[f"TERM_RM_TEMP_{r}"] for r in ROOMS] for d in di])  # d,r,t
        roomC = (room - 32) * F2K
        sat = np.array([d["RTU_SA_TEMP"] for d in di])
        fan = np.array([np.nan_to_num(d["RTU_SA_FAN_WATT"]) for d in di]) > FAN_ON_W
        satocc = sat[occ & fan & np.isfinite(sat)]
        satC = (satocc - 32) * F2K
        dmp = np.array([d["RTU_OA_DMPR_DM"] for d in di])
        ratio = np.array([d["RTU_SA_FLOW"] for d in di])
        # per-day median SAT during occupied fan-on; correlation with day-mean OAT (reset proxy)
        dsat, doat = [], []
        for k, d in enumerate(di):
            m = occ[k] & fan[k] & np.isfinite(sat[k])
            if m.sum() > 60:
                dsat.append(np.median((sat[k][m] - 32) * F2K)); doat.append(oatC[k][occ[k]].mean())
        hourly_oat = oatC.reshape(len(di), 24, 60).mean(2)
        hourly_room = roomC.mean(1).reshape(len(di), 24, 60).mean(2)
        vw = np.array([[d[f"VAV_RM_WATT_{r}"] for r in ROOMS] for d in di]).sum(1).reshape(len(di), 24, 60).mean(2)
        rows[s] = dict(
            n_days=len(di),
            oat_C_min=[float(oatC.min(1).min()), float(oatC.min(1).max())], oat_C_max=[float(oatC.max(1).min()), float(oatC.max(1).max())],
            oat_C_daymean=[float(oatC.mean(1).min()), float(oatC.mean(1).max())], oat_diurnal_amp_C=float(np.mean(hourly_oat.max(1) - hourly_oat.min(1))),
            occ_hours=[float(np.nanmin(hrs_occ)), float(np.nanmedian(hrs_occ)), float(np.nanmax(hrs_occ))],
            occ_start_h=[float(np.nanmin(st)), float(np.nanmax(st))], occ_end_h=[float(np.nanmin(en)), float(np.nanmax(en))], occupied_frac_days=float(np.mean(occ.any(1))),
            cspt_occ_C=sorted(set(np.round((cs[occ] - 32) * F2K, 2).tolist())) if occ.any() else [], hspt_occ_C=sorted(set(np.round((hs[occ] - 32) * F2K, 2).tolist())) if occ.any() else [],
            cspt_unocc_C=sorted(set(np.round((cs[~occ] - 32) * F2K, 2).tolist())), hspt_unocc_C=sorted(set(np.round((hs[~occ] - 32) * F2K, 2).tolist())),
            band_width_occ_K=sorted(set(np.round(band(occ), 2).tolist())) if occ.any() else [], band_width_unocc_K=sorted(set(np.round(band(~occ), 2).tolist())),
            room_T_C=dict(mean=float(roomC.mean()), sd_over_time=float(roomC.mean(1).std()), p5=float(np.percentile(roomC, 5)), p95=float(np.percentile(roomC, 95)),
                          cross_room_sd_K=float(roomC.std(1).mean()), diurnal_amp_K=float(np.mean(hourly_room.max(1) - hourly_room.min(1)))),
            rtu_sat_occ_C=dict(p5=float(np.percentile(satC, 5)), p50=float(np.percentile(satC, 50)), p95=float(np.percentile(satC, 95))) if len(satC) else None,
            rtu_sat_daymedian_C=[float(min(dsat)), float(max(dsat))] if dsat else None,
            rtu_sat_reset_corr_with_oat=float(np.corrcoef(dsat, doat)[0, 1]) if len(dsat) > 3 else None,
            oa_damper_pct=dict(min=float(dmp.min()), max=float(dmp.max()), occ_mean=float(dmp[occ].mean()) if occ.any() else None, unocc_mean=float(dmp[~occ].mean()),
                               frac_occ_at_le10=float((dmp[occ] <= 10).mean()) if occ.any() else None, n_levels=int(len(np.unique(dmp)))),
            rtu_flow_cfm_occ=dict(p5=float(np.nanpercentile(ratio[occ], 5)), p95=float(np.nanpercentile(ratio[occ], 95))) if occ.any() else None,
            vav_reheat_total_W_hourly=dict(peak_hour=int(np.argmax(vw.mean(0))), peak=float(vw.mean(0).max()), min=float(vw.mean(0).min())),
        )
    return rows


def _e(x, kind, method, ci=None, n=None, **kw):
    return dict(est=x, ci95=ci, kind=kind, assumed=(kind in ("assumed", "proxy_assumed")), method=method, n=n, **kw)


def profile_inputs(S, days):
    """the compact contract read by docmismatch.dr.sensor_layer.  kind in {estimated, proxy, assumed, not_estimable}; assumed=True flags parameters that are not
    identified by this data (or only by a proxy that may be dominated by physical, not sensor, effects)."""
    H = S["headline_all"]
    def h(k, kind="estimated", method="", **kw):
        return _e(H[k]["est"], kind, method, H[k]["ci95"], H[k]["n_days"], **kw)
    q = S["quantisation"]
    Kq = 0.01 * F2K
    pw_max = float(np.median([np.nanmax(d[f"VAV_RM_WATT_{r}"]) for d in days for r in ROOMS]))
    fl_p95 = float(np.median([np.nanpercentile(d["RTU_SA_FLOW"], 95) for d in days]))
    vo = S["offsets_proxy"]["vav_sat_vs_median_unheated"]["between_season_changes"]
    ro = S["offsets_proxy"]["room_temp_vs_median_all_hours"]["between_season_changes"]
    v90 = [p["per_90d_if_random_walk_K"] for p in vo]
    r90 = [p["per_90d_if_random_walk_K"] for p in ro]
    P = {
      "noise_sd": {
        "temp": h("noise_temp", method="trimmed-RMS of 2nd differences of 1-min data (var d2 = 6 sigma^2), median of per-day sigmas; quantisation-limited (quantum 0.0056 K): true white noise may be smaller", unit="K", sdlog_between_days=H["noise_temp_sdlog_between_days"]["est"]),
        "value": h("noise_value", method="same, on VAV/RTU discharge-air sensors while fan on; includes real turbulence/cycling so an upper bound on sensor noise", unit="K", sdlog_between_days=H["noise_value_sdlog_between_days"]["est"]),
        "flow": h("noise_flow", method="same, relative to level, RTU_SA_FLOW only (no per-box flow exists) - transferred to VAV/loop flow by assumption", unit="relative", sdlog_between_days=H["noise_flow_sdlog_between_days"]["est"], transferred_to_other_flow_sensors=True),
        "power": h("noise_power", method="same, relative to level (>150 W VAV reheat, >500 W RTU) on quiet samples", unit="relative", sdlog_between_days=H["noise_power_sdlog_between_days"]["est"]),
      },
      "power_abs_frac": h("power_abs_frac", method="noise sd of VAV reheat at standby (<30 W) divided by channel max; quantum-limited (2.77 W quantum)"),
      "subhour_sd": {
        "temp": h("subhour_temp", "proxy", "sd of 1-min samples about the within-hour straight line; hours with 60 valid samples; RMS over hours and sensors", unit="K"),
        "value": h("subhour_value", "proxy", "same", unit="K"),
        "flow": h("subhour_flow", "proxy", "same, relative", unit="relative"),
        "power": h("subhour_power", "proxy", "same, relative", unit="relative"),
      },
      "quant": {
        "temp": _e(Kq, "estimated", "smallest non-zero step of 0.01 degF on Spring/Summer/Winter files (all samples on the grid); Fall file is unquantised/resampled", unit="K"),
        "value": _e(Kq, "estimated", "same (VAV/RTU discharge sensors)", unit="K"),
        "flow": _e(1.0 / fl_p95, "estimated", "1 cfm step / median p95 flow (Spring-Winter; Fall 0.5 cfm)", unit="fraction of series p95"),
        "power": _e(2.7702 / pw_max, "estimated", "2.77 W step / median per-channel VAV max power", unit="fraction of series max"),
      },
      "dropout": {
        "frac": h("rand_dropout_frac", method="random NaN samples (fan-on or non-fan channels) / all channel-samples on 1-min data; ~1 event per 6e4 samples", unit="fraction of 1-min samples"),
        "run_mean_min": _e(S["missingness"]["random_run_mean_min"], "estimated", "83 events, nearly all 1 min, one 55-min run", n=S["missingness"]["random_events"], unit="minutes"),
        "field_prior_frac": _e([0.002, 0.03], "assumed", "log-uniform prior for a field BAS/trend export; the lab logger has essentially no dropouts so the field rate is NOT identified by this data", unit="fraction of hourly samples", ci=None),
        "field_prior_run_mean_h": _e([1.0, 6.0], "assumed", "no hour-scale dropouts observed", unit="hours"),
      },
      "stale": {
        "frac": h("stale_frac_ge60", method="fraction of valid fan-on samples inside exact-repeat runs >= 60 identical values (none observed; max run 7 min)", unit="fraction"),
        "rule_of_three_upper_95": _e(3.0 / sum(m["n_tot"] for m in missing_of) * 22.0, "estimated", "rule-of-three upper bound on per-sample rate over the stale-checked channels", unit="fraction"),
        "field_prior_frac": _e([0.0, 0.02], "assumed", "frozen-sensor/flatline prior; none observed in lab data", unit="fraction of hourly samples"),
        "field_prior_run_mean_h": _e([4.0, 24.0], "assumed", "prior; not observed", unit="hours"),
      },
      "offset_sd_K": {
        "value": _e(H["vav_sat_offset_sd_K"]["est"], "proxy", "sd across 10 VAV SAT sensors of their mean deviation from the box median, unheated boxes (<30 W), fan on; includes real duct-location gradients so an upper-ish bound", H["vav_sat_offset_sd_K"]["ci95"], H["vav_sat_offset_sd_K"]["n_days"], unit="K"),
        "temp": _e(H["room_offset_sd_K"]["est"], "proxy", "sd across 10 rooms of mean deviation from the room median; DOMINATED by real zone differences (solar/orientation), so an UPPER bound on calibration spread", H["room_offset_sd_K"]["ci95"], H["room_offset_sd_K"]["n_days"], unit="K"),
      },
      "drift_K_per_90d": {
        "random_walk_sd": _e(float(np.median(v90)), "proxy_assumed", "rms change of per-sensor VAV-SAT offset between chronologically-adjacent season files (63-265 days apart), scaled by sqrt(gap/90); rough proxy, not drift", [float(min(v90)), float(max(v90))], 3, unit="K per 90 days"),
        "linear_sd": _e(float(np.median(v90)) * 0.5, "assumed", "assumed half of the random-walk proxy; long-term linear drift is not identifiable from 2-day windows", None, None, unit="K per 90 days"),
        "room_upper": _e(float(np.median(r90)), "proxy_assumed", "same construction on room temps (includes real load/season changes)", [float(min(r90)), float(max(r90))], 3, unit="K per 90 days"),
      },
      "timestamp": {
        "jitter_min": _e([0.0, 3.0], "assumed", "raw stamps are exact minutes (0 non-zero seconds) so sub-minute jitter is unobservable; range is a prior for a trend-log export", unit="minutes"),
        "lag_min": _e([0.0, 5.0], "assumed", "inter-channel lag not identifiable (channels share a logger clock)", unit="minutes"),
        "missing_minutes_within_days": _e(0.0, "estimated", "all 30 days have exactly 1440 consecutive 1-min stamps, no duplicates", n=30),
      },
      "not_estimable": ["long-term (months/years) sensor drift", "flow-sensor noise for individual VAV boxes and water loops (only RTU_SA_FLOW exists)", "hour-scale dropouts / stale runs in field BAS exports", "true calibration offsets separate from real spatial temperature gradients", "coil/water-side sensor noise (no water-side data)"],
    }
    return P


def main():
    rng = np.random.default_rng(20260921)
    days, filestats = load_days()
    print("days", len(days), {s: sum(d["season"] == s for d in days) for s in ORDER})
    global feats, missing_of, stale_of, offs_room, offs_vav
    feats = []
    for d in days:
        f, _ = per_day_features(d)
        feats.append(f)
    missing_of = [missing_stats(d) for d in days]
    stale_of = [stale_stats(d, np.random.default_rng(i)) for i, d in enumerate(days)]
    offs_room = [room_offsets(d, "all") for d in days]
    offs_vav = [vav_offsets(d)[0] for d in days]
    allidx = list(range(len(days)))
    idx_of = lambda seasons: [i for i in allidx if days[i]["season"] in seasons]  # noqa: E731

    S = {"meta": dict(files=[f["file"] for f in filestats], n_days=len(days), days_per_season={s: sum(d["season"] == s for d in days) for s in ORDER},
                      bootstrap=f"{B} resamples of whole days (30 dev days; days are the unit, so CIs treat days as exchangeable and ignore that they come from one building)",
                      sealed_guard="only ERTU_* and Inc_Eco_* files are opened (asserted by prefix); OA_damper*/SA_temp_bias* never touched",
                      units="temperature in K (deltas; degF*5/9), power/flow as relative noise (fraction of level) and additive floor as fraction of series max")}
    S["headline_all"] = boot(days, feats, allidx, rng)
    # by season (single-season, for the per-season table)
    S["headline_by_season"] = {s: boot(days, feats, idx_of([s]), rng, 100) for s in ORDER}
    # validation: two seasons vs the other two
    val = {}
    for name, A, Bs in (("fall+spring -> summer+winter", ["fall", "spring"], ["summer", "winter"]), ("summer+winter -> fall+spring", ["summer", "winter"], ["fall", "spring"])):
        ea, eb = boot(days, feats, idx_of(A), rng, 150), boot(days, feats, idx_of(Bs), rng, 150)
        v = {}
        for k in ea:
            a, b = ea[k], eb[k]
            if a["est"] is None or b["est"] is None or not np.isfinite(a["est"]) or not np.isfinite(b["est"]):
                continue
            lo, hi = a["ci95"]
            ov = (a["ci95"][0] is not None) and not (b["ci95"][1] < a["ci95"][0] or b["ci95"][0] > a["ci95"][1])
            v[k] = dict(fit_est=a["est"], fit_ci=a["ci95"], holdout_est=b["est"], holdout_ci=b["ci95"], ratio=(b["est"] / a["est"]) if a["est"] not in (0, None) else None, ci_overlap=bool(ov), holdout_in_fit_ci=bool(lo is not None and lo <= b["est"] <= hi))
        val[name] = v
    S["validation"] = val
    # per-group noise (diagnostic), per season
    grp = {}
    for g in GROUPS:
        grp[g] = {s: dict(sigma=mad_sigma(np.concatenate([feats[i][g]["d2"] for i in idx_of([s])])), n=int(sum(len(feats[i][g]["d2"]) for i in idx_of([s])))) for s in ORDER}
        grp[g]["all"] = dict(sigma=mad_sigma(np.concatenate([feats[i][g]["d2"] for i in allidx])), n=int(sum(len(feats[i][g]["d2"]) for i in allidx)))
        # cross-channel heterogeneity of noise (log-sd) within group
    S["noise_by_group_season"] = grp
    # per-channel noise heterogeneity (sd of log sigma across sensors, temp classes)
    het = {}
    for g in ("room_temp", "vav_sat"):
        sig = []
        for c in GROUPS[g][1]:
            v = np.concatenate([d2_of(d[c] * F2K)[0][np.isfinite(d2_of(d[c] * F2K)[0])] for d in days])
            sig.append(mad_sigma(v))
        het[g] = dict(per_sensor_sigma_K=[float(s) for s in sig], sd_log=float(np.std(np.log(np.maximum(sig, 1e-6)), ddof=1)))
    S["noise_heterogeneity"] = het
    # quantisation
    q = quant_info(days)
    S["quantisation"] = {g: {s: dict(quantum_native=q[(g, s)][0], frac_on_grid=q[(g, s)][1]) for s in ORDER} for g in GROUPS}
    # missingness details
    rr = [x for m in missing_of for x in m["rand_runs"]]
    S["missingness"] = dict(
        structural_definition="NaN in RTU_SA_TEMP/RTU_RA_TEMP/RTU_SA_FLOW/VAV_RM_SAT_* while RTU_SA_FAN_WATT<=100 W (fan off / setback)",
        random_definition="any other NaN (any channel while fan on, or any NaN in a channel that is never structurally NaN)",
        by_season={s: dict(struct_frac=sum(missing_of[i]["n_struct"] for i in idx_of([s])) / sum(missing_of[i]["n_tot"] for i in idx_of([s])),
                           random_frac=sum(missing_of[i]["n_rand"] for i in idx_of([s])) / sum(missing_of[i]["n_tot"] for i in idx_of([s])),
                           fan_on_frac=float(np.mean([missing_of[i]["fan_on_frac"] for i in idx_of([s])]))) for s in ORDER},
        random_events=len(rr), random_run_lengths_min=[int(x) for x in rr[:50]], random_run_mean_min=float(np.mean(rr)) if rr else None,
        rule_of_three_upper_95_frac=3.0 / sum(m["n_tot"] for m in missing_of), all_channel_nan_rows=int(sum(m["allnan_rows"] for m in missing_of)))
    # stale
    sl = [x for _, l in stale_of for x in l]
    S["stale"] = dict(method="fraction of valid samples inside runs of >=L exactly-identical consecutive values, on 22 continuous temp/flow channels, minus a Bernoulli(channel repeat prob) null simulated per day",
                      run_length_quantiles_min={q_: float(np.percentile(sl, q_)) for q_ in (50, 90, 99, 99.9)}, max_run_min=int(max(sl)),
                      by_season_ge30={s: dict(obs=sum(stale_of[i][0][30][0] for i in idx_of([s])) / sum(stale_of[i][0][30][1] for i in idx_of([s])),
                                              null=sum(stale_of[i][0][30][2] for i in idx_of([s])) / sum(stale_of[i][0][30][1] for i in idx_of([s]))) for s in ORDER})
    S["sampling"] = dict(files=filestats, missing_minute_fraction_within_days=0.0, note="timestamps are exact minute stamps; no jitter below 1 min is observable. Whole days are missing between recorded days (files are sparse samples of days).")
    # calibration offsets (proxy)
    off = {}
    for nm, fn in (("room_temp_vs_median_all_hours", lambda d: room_offsets(d, "all")), ("room_temp_vs_median_unoccupied", lambda d: room_offsets(d, "unocc")), ("vav_sat_vs_median_unheated", lambda d: vav_offsets(d)[0])):
        per_season, per_day = {}, {}
        for s in ORDER:
            o = [fn(days[i]) for i in idx_of([s])]
            o = [x for x in o if x is not None]
            per_season[s] = np.mean(o, 0) if o else None
            if o:
                per_day[s] = float(np.mean([np.std(x - per_season[s], ddof=0) for x in o]))
        seas = [s for s in ORDER if per_season[s] is not None]
        sd_by_season = {s: float(np.std(per_season[s], ddof=1)) for s in seas}
        pooled = np.mean([per_season[s] for s in seas], 0)
        # date gaps between seasons (chronological): fall2020 -> spring2021 -> summer2021 -> winter2022
        firstday = {s: min(days[i]["day"] for i in idx_of([s])) for s in ORDER}
        chron = sorted(seas, key=lambda s: firstday[s])
        pairs = []
        for a, b2 in zip(chron[:-1], chron[1:]):
            gap = (np.datetime64(firstday[b2]) - np.datetime64(firstday[a])).astype(int)
            dd = per_season[b2] - per_season[a]
            pairs.append(dict(a=a, b=b2, gap_days=int(gap), sd_offset_change_K=float(np.std(dd, ddof=1)), rms_offset_change_K=float(np.sqrt(np.mean(dd ** 2))), per_90d_if_random_walk_K=float(np.sqrt(np.mean(dd ** 2)) / np.sqrt(gap / 90.0))))
        # bootstrap CI over days of the persistent sd (already in headline); here also per-sensor table
        off[nm] = dict(per_sensor_pooled_K=[float(x) for x in pooled], persistent_sd_by_season_K=sd_by_season, day_to_day_sd_within_season_K=per_day, between_season_changes=pairs)
    S["offsets_proxy"] = off
    S["operating_variability"] = op_table(days, allidx)
    S["profile_inputs"] = profile_inputs(S, days)
    json.dump(S, open(OUT / "sensor_stats.json", "w"), indent=1, default=lambda o: None if (isinstance(o, float) and not np.isfinite(o)) else (o.item() if hasattr(o, "item") else str(o)))
    print("wrote json")


if __name__ == "__main__":
    main()
