"""Reading pool of a FIELD building (from `intake.FieldBuilding`), in exactly the layout `active.pools.build_sim_pool` gives simulated buildings, so the
engine, models and decision layers consume it unchanged.

Slices are 24-hour local-standard-time days, six per six-week window (days 0, 8, ... 40 of each window, as in simulation); `group` = the window (a "site visit"),
`season` = the simulation's season of the window nearest in the year, `ctx` = (outdoor-temperature mean, its daily swing, building load fraction).
Differences from simulation, all deliberate: the evidence is the recorded data itself (no injected noise); a channel is NaN (missing) when a point it reads is
not recorded or has fewer than `min_valid_hours` of 24 in the slice; short gaps (< the limit) are linearly filled; the building-wide common-mode signals of
`vav_zone` use the boxes / zones that have the point; the closure channel (channel 3) is left NaN. Nothing here uses the documentation except to decide WHICH
pairs (documented owners and members) to read; the truth arrays hold only what a field check verified (-1 = unknown).
"""

from __future__ import annotations

import warnings
from datetime import timedelta

import numpy as np

from .active.pools import CTX_NAMES, DAYS_PER_WINDOW_PICK, EVIDENCE_SLOTS, SEASON_OF_WINDOW, Pool, SlotPool  # noqa: F401
from .data import SLOTS
from .evidence import _z, pair_errors
from .intake import FieldBuilding
from .intake_report import CHANNEL_SIGNALS, WINDOW_H, resolve


class _Fill(dict):
    """dict that answers a missing series with NaNs, so `evidence.pair_errors` runs; the channels that read such a series are then overwritten with NaN."""

    def __init__(self, data, n):
        super().__init__(data)
        self._n = n

    def __missing__(self, key):
        return np.full(self._n, np.nan)


def _fill_short_gaps(x: np.ndarray) -> np.ndarray:
    good = np.isfinite(x)
    if good.all():
        return x
    return np.interp(np.arange(len(x)), np.flatnonzero(good), x[good])


def field_context(base, ev: dict) -> dict:
    """`evidence.make_context` over the boxes / zones that have the point (a missing box contributes nothing instead of failing the whole building)."""
    def fleet(kind, sig):
        arrs = [_z(ev[f"{i}|{sig}"]) for i in base.ids(kind) if f"{i}|{sig}" in ev]
        return np.mean(arrs, axis=0) if arrs else 0.0
    return {"Fm": fleet("VAV", "flow"), "Dm": fleet("VAV", "t_dis"), "Tm": fleet("Zone", "temp")}


def _channel_available(slot: str, k: int, o: str, m: str, ev: dict, equipment: dict) -> bool:
    eq = {"o": o, "m": m}
    return all(any(f"{eq[who]}|{s}" in ev for s in resolve(sig, equipment[eq[who]]["kind"], equipment[eq[who]].get("function", "")).split("|"))
               for who, sig in CHANNEL_SIGNALS[slot][k])


def _load_fraction(fb: FieldBuilding, base) -> np.ndarray:
    for kind in ("AHU", "VAV"):
        fl = [fb.ev[f"{i}|flow"] / (np.nanmax(np.abs(fb.ev[f"{i}|flow"])) + 1e-9) for i in base.ids(kind) if f"{i}|flow" in fb.ev and np.isfinite(fb.ev[f"{i}|flow"]).any()]
        if fl:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)      # hours nobody recorded are NaN in every series
                return np.nanmean(fl, axis=0)
    return np.full(fb.n_hours, 0.5)


def build_field_pool(fb: FieldBuilding, *, min_valid_hours: int = 20, kind: str = "sim", slice_days: str = "engine", mask_uninformative: bool | None = None,
                     require_oat: bool = True) -> Pool:
    """Pool of `fb`'s documented connections. `kind` only selects the grouping convention of `active.model` ('sim': one unit per building, right for training
    across many buildings; 'real': one building split by season); the data are the field data either way.

    Options added for the model-free real-data study (PREREGISTRATION_DR.md Addendum 17); the defaults reproduce the earlier behaviour exactly:
      slice_days="engine": the simulation's six day positions per six-week window (or the spread rule for chunked exports); "all": every day of each window that has data.
      mask_uninformative=None: the engine's default masking of flat channels; False: raw channel values (as in Addendum 11's diagnosability ladder).
      require_oat=False: no outdoor-temperature series needed (days are then judged on data presence only and the context's outdoor columns are 0 when there is none):
        for statistics that never read the context."""
    if slice_days not in ("engine", "all"):
        raise ValueError(f"slice_days must be 'engine' or 'all', not {slice_days!r}")
    base = fb.base()
    oat_key = next((k for k in fb.ev if k.endswith("|oat")), None)
    if oat_key is None and require_oat:
        raise ValueError("no outdoor-temperature series (a Weather equipment with an `oat` point is required)")
    oat = fb.ev[oat_key] if oat_key is not None else np.full(fb.n_hours, np.nan)
    load = _load_fraction(fb, base)
    n_windows = int(np.ceil(fb.n_hours / WINDOW_H))
    slices = []                                       # (window, start hour)
    for w in range(n_windows):
        usable_days = [d for d in range(WINDOW_H // 24) if (a := w * WINDOW_H + d * 24) + 24 <= fb.n_hours and fb.active_hours[a:a + 24].all()
                       and (not require_oat or np.isfinite(oat[a:a + 24]).sum() >= min_valid_hours)]
        if slice_days == "all":
            slices += [(w, w * WINDOW_H + d * 24) for d in usable_days]
            continue
        picks = [d for d in DAYS_PER_WINDOW_PICK if d in usable_days]            # the simulation's positions where the data allow ...
        rest = [d for d in usable_days if d not in picks]
        need = min(len(DAYS_PER_WINDOW_PICK), len(usable_days)) - len(picks)      # ... and, for chunked exports, other days spread evenly over the rest
        if need > 0 and rest and fb.n_chunks > 1:                                  # continuous data keep the simulation's exact positions
            picks += [rest[int(i)] for i in np.linspace(0, len(rest) - 1, need).round().astype(int)] if need < len(rest) else rest
        slices += [(w, w * WINDOW_H + d * 24) for d in sorted(set(picks))]
    if not slices:
        raise ValueError("no usable day-slice: need at least one day with outdoor temperature and the standard slice positions inside the data")
    ctx = np.zeros((len(slices), len(CTX_NAMES)))
    season, group = np.zeros(len(slices), int), np.zeros(len(slices), int)
    win_doy = {}
    for w, a in slices:
        win_doy.setdefault(w, []).append((fb.t0_local + timedelta(hours=a)).timetuple().tm_yday - 1)
    for i, (w, a) in enumerate(slices):
        seg = oat[a:a + 24]
        o = _fill_short_gaps(seg) if np.isfinite(seg).any() else np.zeros(24)                 # no outdoor series (require_oat=False): placeholder zeros
        ctx[i] = [float(o.mean()), float(o.max() - o.min()), float(np.nanmean(load[a:a + 24]))]
        season[i], group[i] = SEASON_OF_WINDOW[min(7, int(np.mean(win_doy[w])) // 42)], w      # season of the window's mean day of year (simulation: window index)
    pool = Pool(f"{fb.building_id}#field", kind, ctx, season, group)

    # per-slice cleaned series: keys with too few valid hours are dropped (their channels become NaN), short gaps are filled
    slice_ev = []
    for w, a in slices:
        d = {}
        for key, x in fb.ev.items():
            seg = x[a:a + 24]
            if np.isfinite(seg).sum() >= min_valid_hours:
                d[key] = _fill_short_gaps(seg)
        slice_ev.append(_Fill(d, 24))

    meta = {}
    for slot in EVIDENCE_SLOTS:
        claims = [c for c in fb.claims if c.slot == slot]
        if not claims or slot not in CHANNEL_SIGNALS:
            continue
        spec = SLOTS[slot]
        owners = base.ids(*spec["owner"])
        first = {}
        for c in claims:
            first.setdefault(c.member, c)
        members = sorted(first)
        oi = {o: i for i, o in enumerate(owners)}
        truth = np.full(len(members), -1)
        documented = np.array([oi[first[m].owner] for m in members])
        for j, m in enumerate(members):
            c = first[m]
            if c.verified == "yes":
                truth[j] = oi[c.owner]
            elif c.verified == "no" and c.true_owner in oi:
                truth[j] = oi[c.true_owner]
        E = np.full((len(slices), 4, len(owners), len(members)), np.nan)
        with np.errstate(all="ignore"):
            for i, ev in enumerate(slice_ev):
                c_ctx = field_context(base, ev) if slot == "vav_zone" else None
                for a_, o in enumerate(owners):
                    for b_, m in enumerate(members):
                        avail = [_channel_available(slot, k, o, m, ev, fb.equipment) for k in range(3)]
                        if not any(avail):
                            continue
                        e = pair_errors(base, ev, slot, o, m, slice(None), c_ctx, mask_uninformative=mask_uninformative)
                        for k in range(3):
                            if avail[k]:
                                E[i, k, a_, b_] = e[k]
        size = np.array([float(np.nanmax(np.abs(fb.ev[f"{o}|flow"]))) + 1e-9 if f"{o}|flow" in fb.ev and np.isfinite(fb.ev[f"{o}|flow"]).any() else 1.0 for o in owners])
        pool.slots[slot] = SlotPool(slot, owners, members, truth, E, [base.cls(o) for o in owners], size)
        meta[slot] = dict(documented=documented, verified=[first[m].verified for m in members], true_owner=[first[m].true_owner for m in members])
    pool.field_meta = meta
    pool.field_windows = [w for w, _ in slices]
    pool.field_slice_hours = [a for _, a in slices]          # start hour (grid hours) of each slice
    return pool
