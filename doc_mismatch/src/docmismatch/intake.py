"""Field-data intake: turn a building's control-system export (point list + trend history + documented connections) into the
structures the evidence engine consumes. Standard library + numpy only. The file formats are specified in `doc_mismatch/INTAKE.md`.

  load_export(dir)  ->  FieldBuilding    (units converted to SI, one common hourly grid, per-point quality report)
  FieldBuilding.base()                   a `data.Base` of the DOCUMENTED connections + hourly series keyed "EQUIPMENT|signal"

Design rules:
  * Nothing is ever derived from the documentation: a series is a recorded point of one piece of equipment, exactly as logged.
    (In particular AHU-level heating / cooling meters are NOT summed from documented coils.)
  * Units are converted with fixed, disclosed constants (air 1.2 kg/m3, water 998 kg/m3); unknown units are an error, not a guess.
  * The hourly grid is LOCAL STANDARD TIME (no daylight-saving jumps) starting at local midnight, so 24-hour slices are calendar days.
  * Anything doubtful is reported (`FieldBuilding.notes`, `PointQA`), never silently repaired.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

from .data import SLOTS, Base

# ---------------------------------------------------------------------------------------------- vocabulary
EQUIPMENT_TYPES = ("AHU", "VAV", "Zone", "Coil", "Branch", "HWL", "CHWL", "Pump", "Boiler", "Chiller", "Fan", "SAT", "DAT", "Weather")
SIGNALS: dict[str, dict[str, str]] = {          # equipment type -> {signal name: physical dimension}
    "AHU": {"flow": "air_flow", "sat": "temp", "mat": "temp", "htg": "power", "clg": "power"},
    "VAV": {"flow": "air_flow", "t_in": "temp", "t_dis": "temp", "reheat": "power"},
    "Zone": {"temp": "temp"},
    "Coil": {"rate": "power", "rate_s": "power"},
    "Branch": {"flow": "water_flow", "t_in": "temp", "t_out": "temp"},
    "HWL": {"flow": "water_flow", "t_sup": "temp", "t_ret": "temp"},
    "CHWL": {"flow": "water_flow", "t_sup": "temp", "t_ret": "temp"},
    "Pump": {"flow": "water_flow", "kw": "power"},
    "Boiler": {"rate": "power", "t_out": "temp"},
    "Chiller": {"rate": "power", "t_out": "temp"},
    "Fan": {"kw": "power"},
    "SAT": {"value": "temp"},
    "DAT": {"value": "temp"},
    "Weather": {"oat": "temp"},
}
AIR_DENSITY = 1.2       # kg/m3, volumetric air flow -> mass flow
WATER_DENSITY = 998.0   # kg/m3 (hot water at ~80 C is ~3% lighter: a disclosed approximation)

# unit string (lower-case, spaces and degree signs removed) -> (factor, offset): SI = value * factor + offset. SI = degC, kg/s, W.
_M3_PER_CFM, _M3_PER_GAL = 0.000471947443, 0.003785411784
UNITS: dict[str, dict[str, tuple[float, float]]] = {
    "temp": {"c": (1.0, 0.0), "degc": (1.0, 0.0), "f": (5.0 / 9.0, -32.0 * 5.0 / 9.0), "degf": (5.0 / 9.0, -32.0 * 5.0 / 9.0), "k": (1.0, -273.15)},
    "air_flow": {"kg/s": (1.0, 0.0), "kg/h": (1 / 3600.0, 0.0), "lb/min": (0.45359237 / 60.0, 0.0), "lb/h": (0.45359237 / 3600.0, 0.0),
                 "cfm": (_M3_PER_CFM * AIR_DENSITY, 0.0), "m3/s": (AIR_DENSITY, 0.0), "m3/h": (AIR_DENSITY / 3600.0, 0.0), "l/s": (AIR_DENSITY / 1000.0, 0.0)},
    "water_flow": {"kg/s": (1.0, 0.0), "kg/h": (1 / 3600.0, 0.0), "gpm": (_M3_PER_GAL / 60.0 * WATER_DENSITY, 0.0), "l/s": (WATER_DENSITY / 1000.0, 0.0),
                   "l/min": (WATER_DENSITY / 60000.0, 0.0), "m3/h": (WATER_DENSITY / 3600.0, 0.0), "m3/s": (WATER_DENSITY, 0.0)},
    "power": {"w": (1.0, 0.0), "kw": (1000.0, 0.0), "mw": (1e6, 0.0), "btu/h": (0.29307107, 0.0), "btuh": (0.29307107, 0.0), "mbh": (293.07107, 0.0),
              "kbtu/h": (293.07107, 0.0), "ton": (3516.8528, 0.0), "tons": (3516.8528, 0.0), "tr": (3516.8528, 0.0)},
}
PLAUSIBLE = {"temp": (-50.0, 150.0), "air_flow": (-1.0, 1000.0), "water_flow": (-1.0, 2000.0), "power": (-1e7, 1e9)}   # SI, after conversion; outside -> missing
EMPTY_TOKENS = {"", "nan", "null", "none", "n/a", "na", "-", "--"}      # a blank / "no value" marker: missing data, not a data-quality problem
SENTINELS = {-999.0, -9999.0, -999.9, -99999.0, 32767.0, 65535.0}
MEDIAN_RANGE = {("Zone", "temp"): (5.0, 40.0), ("VAV", "t_dis"): (0.0, 60.0), ("AHU", "sat"): (0.0, 45.0), ("Weather", "oat"): (-50.0, 60.0)}   # a median outside this after conversion means the unit label is probably wrong
TS_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M", "%m/%d/%y %H:%M", "%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %I:%M %p",
              "%d-%b-%Y %H:%M", "%Y/%m/%d %H:%M", "%Y/%m/%d %H:%M:%S")


def norm_unit(u: str) -> str:
    return (u or "").strip().lower().replace("°", "").replace(" ", "")


def to_si(dim: str, unit: str) -> tuple[float, float]:
    """(factor, offset) turning a value in `unit` into SI for physical dimension `dim`. Unknown unit: ValueError listing the supported ones."""
    key = norm_unit(unit)
    table = UNITS[dim]
    if key not in table:
        raise ValueError(f"unit {unit!r} not supported for a {dim} point (supported: {', '.join(sorted(table))})")
    return table[key]


# ---------------------------------------------------------------------------------------------- data classes
@dataclass
class PointSpec:
    point_id: str
    equipment_id: str
    equipment_type: str
    signal: str
    unit: str
    logging: str = "interval"       # "interval" (regular samples) | "cov" (change of value: hold the last value)


@dataclass
class Claim:
    """One documented connection, optionally with what a field check found."""
    owner: str
    member: str
    slot: str
    verified: str = "unknown"       # yes (documented connection confirmed) | no (documented connection is wrong) | unknown
    true_owner: str = ""            # for verified == "no": the owner found in the field, when known
    source: str = ""                # design | as_built | bas | other


@dataclass
class PointQA:
    point_id: str
    n_raw: int = 0
    n_valid: int = 0
    n_nonnumeric: int = 0           # text that is not a number ("offline")
    n_sentinel: int = 0             # -999, 32767, inf, ...
    n_empty: int = 0                # blank cells: missing data
    n_out_of_range: int = 0
    n_duplicate_ts: int = 0
    median_dt_min: float = float("nan")
    coverage: float = 0.0           # fraction of hourly bins with a value
    longest_gap_h: int = 0
    median_si: float = float("nan")


@dataclass
class FieldBuilding:
    building_id: str
    t0_local: datetime              # local standard time of hour 0 (local midnight)
    n_hours: int
    equipment: dict[str, dict]      # id -> dict(kind, function, medium)
    points: dict[str, PointSpec]
    claims: list[Claim]
    ev: dict[str, np.ndarray]       # "EQUIPMENT|signal" -> (n_hours,) SI series, NaN = no value
    qa: dict[str, PointQA]
    context: dict
    notes: list[str] = field(default_factory=list)
    active_days: np.ndarray | None = None       # (ceil(n_hours / 24),) bool: days on which most points have data (exports often hold separate chunks of days)

    @property
    def ev_keys(self) -> set[str]:
        return set(self.ev)

    @property
    def active_hours(self) -> np.ndarray:
        if self.active_days is None:
            return np.ones(self.n_hours, bool)
        return np.repeat(self.active_days, 24)[: self.n_hours]

    @property
    def n_chunks(self) -> int:
        """number of separate runs of active days"""
        a = np.ones(-(-self.n_hours // 24), bool) if self.active_days is None else self.active_days
        return int((a[1:] & ~a[:-1]).sum() + a[0]) if len(a) else 0

    def base(self) -> Base:
        """`data.Base` of the DOCUMENTED connections (owner/member of every claim) with the recorded series. Raises ValueError for a claim whose
        equipment types do not fit its slot."""
        nodes = {}
        for eid, e in self.equipment.items():
            kind, fn, med = e["kind"], e.get("function", ""), e.get("medium", "")
            brick = {"Coil": {"heating": "Heating_Coil", "cooling": "Cooling_Coil"}.get(fn, "Coil"), "HWL": "Hot_Water_Loop", "CHWL": "Chilled_Water_Loop"}.get(kind, kind)
            if kind == "HWL":
                med = "hot_water"
            elif kind == "CHWL":
                med = "chilled_water"
            nodes[eid] = {"id": eid, "kind": kind, "brick_type": brick, "medium": med or None}
        edges, slot_edges = [], {}
        for c in self.claims:
            spec = SLOTS[c.slot]
            for who, eid, allowed in (("owner", c.owner, spec["owner"]), ("member", c.member, spec["member"])):
                if eid not in nodes or nodes[eid]["kind"] not in allowed:
                    raise ValueError(f"claim {c.owner}->{c.member} ({c.slot}): {who} {eid!r} is {nodes.get(eid, {}).get('kind', 'unknown')}, slot needs {allowed}")
            edges.append((c.owner, c.member, spec["rel"]) if spec["owner_first"] else (c.member, c.owner, spec["rel"]))
            slot_edges.setdefault(c.slot, []).append((c.owner, c.member))
        return Base(self.building_id, nodes, edges, dict(self.ev), {}, slot_edges)


# ---------------------------------------------------------------------------------------------- readers
def _rows(path: Path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rd = csv.DictReader(fh)
        rd.fieldnames = [(f or "").strip().lower() for f in (rd.fieldnames or [])]
        for r in rd:
            yield {k: (v or "").strip() for k, v in r.items() if k is not None}


def read_points(path: Path) -> list[PointSpec]:
    out, seen = [], set()
    for r in _rows(path):
        pid = r.get("point_id", "")
        if not pid:
            continue
        if pid in seen:
            raise ValueError(f"points.csv: duplicate point_id {pid!r}")
        seen.add(pid)
        out.append(PointSpec(pid, r.get("equipment_id", ""), r.get("equipment_type", ""), r.get("signal", ""), r.get("unit", ""), (r.get("logging") or "interval").lower()))
    return out


def read_equipment(path: Path | None) -> dict[str, dict]:
    if path is None or not path.exists():
        return {}
    return {r["equipment_id"]: dict(kind=r.get("equipment_type", ""), function=r.get("function", "").lower(), medium=r.get("medium", "").lower())
            for r in _rows(path) if r.get("equipment_id")}


def read_claims(path: Path | None) -> list[Claim]:
    if path is None or not path.exists():
        return []
    return [Claim(r["owner_id"], r["member_id"], r["slot"], (r.get("verified") or "unknown").lower(), r.get("true_owner", ""), r.get("source", ""))
            for r in _rows(path) if r.get("owner_id") and r.get("member_id")]


# ---------------------------------------------------------------------------------------------- time
def std_offset_seconds(tz: ZoneInfo | None, year: int) -> int:
    """Standard-time UTC offset of `tz` (the smaller of the January and July offsets, so daylight saving is excluded in either hemisphere)."""
    if tz is None:
        return 0
    return int(min(datetime(year, 1, 1, 12, tzinfo=tz).utcoffset().total_seconds(), datetime(year, 7, 1, 12, tzinfo=tz).utcoffset().total_seconds()))


class TimeParser:
    """Timestamp text -> UTC epoch seconds. The format is detected on the first parsable value and reused; naive stamps are localized with `tz`."""

    def __init__(self, tz: ZoneInfo | None):
        self.tz, self.fmt, self.cache = tz, None, {}
        self.n_ambiguous = self.n_nonexistent = self.n_bad = 0

    def _parse(self, s: str) -> datetime | None:
        if self.fmt is None:
            try:
                return datetime.fromisoformat(s)
            except ValueError:
                pass
            for f in TS_FORMATS:
                try:
                    d = datetime.strptime(s, f)
                    self.fmt = f
                    return d
                except ValueError:
                    continue
            return None
        try:
            return datetime.strptime(s, self.fmt)
        except ValueError:
            try:
                return datetime.fromisoformat(s)
            except ValueError:
                return None

    def __call__(self, s: str) -> float | None:
        s = s.strip()
        if s in self.cache:
            return self.cache[s]
        d = self._parse(s)
        if d is None:
            self.n_bad += 1
            self.cache[s] = None
            return None
        if d.tzinfo is None and self.tz is not None:
            a = d.replace(tzinfo=self.tz, fold=0)
            ts = a.timestamp()
            if datetime.fromtimestamp(ts, self.tz).replace(tzinfo=None) != d:
                self.n_nonexistent += 1                 # spring-forward gap: no such clock time exists
            elif a.utcoffset() != d.replace(tzinfo=self.tz, fold=1).utcoffset():
                self.n_ambiguous += 1                   # fall-back hour: read as the FIRST occurrence (the daylight hour)
        elif d.tzinfo is None:
            ts = d.replace(tzinfo=timezone.utc).timestamp()
        else:
            ts = d.timestamp()
        self.cache[s] = ts
        return ts


def _num(s: str) -> float | None:
    try:
        return float(s)
    except ValueError:
        return None


def read_trends(path: Path, point_ids: set[str], parser: TimeParser) -> tuple[dict[str, tuple[list, list, dict]], list[str]]:
    """{point_id: (epoch seconds list, raw value list, counters)} for the KNOWN points; the second result lists trend columns/ids not in the point list.
    Long format = columns timestamp, point_id, value. Wide format = first column the timestamp, one column per point."""
    data: dict[str, tuple[list, list, dict]] = {}
    unknown: set[str] = set()

    def put(pid, ts, raw):
        if pid not in data:
            data[pid] = ([], [], dict(nonnumeric=0, sentinel=0, empty=0))
        t, v, c = data[pid]
        if raw.strip().lower() in EMPTY_TOKENS:
            c["empty"] += 1
            x = float("nan")
        else:
            x = _num(raw)
            if x is None or x != x:                     # text such as "offline" or "Comm Fail"
                c["nonnumeric"] += 1
                x = float("nan")
            elif x in SENTINELS or abs(x) > 1e9:        # includes inf
                c["sentinel"] += 1
                x = float("nan")
        t.append(ts)
        v.append(x)

    with open(path, newline="", encoding="utf-8-sig") as fh:
        rd = csv.reader(fh)
        head = [h.strip() for h in next(rd)]
        low = [h.lower() for h in head]
        tcol = next((i for i, h in enumerate(low) if h in ("timestamp", "time", "datetime", "date/time", "date")), 0)
        long_form = "point_id" in low and "value" in low
        if long_form:
            pcol, vcol = low.index("point_id"), low.index("value")
            for row in rd:
                if len(row) <= max(tcol, pcol, vcol):
                    continue
                pid = row[pcol].strip()
                if pid not in point_ids:
                    unknown.add(pid)
                    continue
                ts = parser(row[tcol])
                if ts is not None:
                    put(pid, ts, row[vcol].strip())
        else:
            cols = [(i, h) for i, h in enumerate(head) if i != tcol]
            for i, h in cols:
                if h not in point_ids:
                    unknown.add(h)
            keep = [(i, h) for i, h in cols if h in point_ids]
            for row in rd:
                if not row or tcol >= len(row):
                    continue
                ts = parser(row[tcol])
                if ts is None:
                    continue
                for i, h in keep:
                    if i < len(row):
                        put(h, ts, row[i].strip())
    return data, sorted(unknown)


def hourly(times: np.ndarray, values: np.ndarray, T: int, G0: float, off: float, logging: str = "interval",
           min_valid_frac: float = 0.5, max_hold_h: float = 6.0) -> tuple[np.ndarray, float]:
    """Resample one point onto the common hourly grid (hour h covers local-standard seconds [G0 + 3600 h, G0 + 3600 (h + 1)), G0 = local midnight).
    interval: mean of the valid samples in the hour, kept when at least `min_valid_frac` of the expected samples exist.
    cov: sample-and-hold on a 1-minute grid (a held value expires after `max_hold_h` hours), hour = mean of the held minutes, kept when >= 30 are valid.
    Returns (series with NaN = no value, median sampling interval in minutes)."""
    out = np.full(T, np.nan)
    if len(times) == 0:
        return out, float("nan")
    order = np.argsort(times, kind="stable")
    t, v = times[order], values[order]
    ut = np.unique(t)
    dt = float(np.median(np.diff(ut)) / 60.0) if len(ut) > 1 else float("nan")
    loc = t + off - G0
    if logging == "cov":
        minute = np.arange(T * 60) * 60.0
        idx = np.searchsorted(loc, minute, side="right") - 1
        ok = idx >= 0
        idx = np.where(ok, idx, 0)
        held = v[idx]
        age = minute - loc[idx]
        good = ok & np.isfinite(held) & (age <= max_hold_h * 3600.0)
        held = np.where(good, held, 0.0).reshape(T, 60)
        cnt = good.reshape(T, 60).sum(1)
        with np.errstate(invalid="ignore", divide="ignore"):
            m = held.sum(1) / cnt
        out[cnt >= 30] = m[cnt >= 30]
        return out, dt
    h = np.floor(loc / 3600.0).astype(int)
    keep = np.isfinite(v) & (h >= 0) & (h < T)
    cnt = np.bincount(h[keep], minlength=T).astype(float)
    tot = np.bincount(h[keep], weights=v[keep], minlength=T)
    expected = max(1.0, round(60.0 / dt)) if np.isfinite(dt) and dt > 0 else 1.0
    need = max(1.0, np.ceil(min_valid_frac * expected))
    good = cnt >= need
    out[good] = tot[good] / cnt[good]
    return out, dt


def longest_gap(x: np.ndarray) -> int:
    best = run = 0
    for isnan in ~np.isfinite(x):
        run = run + 1 if isnan else 0
        best = max(best, run)
    return best


def active_day_mask(ev: dict[str, np.ndarray], n_hours: int, min_hours: int = 12, min_frac: float = 0.5) -> np.ndarray:
    """A day is ACTIVE when at least `min_frac` of the points that have any data have >= `min_hours` valid hours that day. Coverage and gaps are judged over active
    days only, so an export made of separate chunks (a few weeks in each season) is not penalised for the months in between."""
    nd = -(-n_hours // 24)
    rows = []
    for x in ev.values():
        ok = np.isfinite(x)
        if ok.any():
            pad = np.zeros(nd * 24, bool)
            pad[:n_hours] = ok
            rows.append(pad.reshape(nd, 24).sum(1) >= min_hours)
    if not rows:
        return np.ones(nd, bool)
    act = np.mean(rows, axis=0) >= min_frac
    return act if act.any() else np.ones(nd, bool)


# ---------------------------------------------------------------------------------------------- the loader
def load_export(root: str | Path, building_id: str | None = None) -> FieldBuilding:
    """Read `points.csv`, `trends.csv`, and optionally `equipment.csv`, `connections.csv`, `context.json` from `root` (formats: INTAKE.md)."""
    root = Path(root)
    ctx = json.loads((root / "context.json").read_text()) if (root / "context.json").exists() else {}
    notes: list[str] = []
    tz = None
    if ctx.get("timezone"):
        tz = ZoneInfo(ctx["timezone"])
    else:
        notes.append("no time zone in context.json: clock times are assumed to be one consistent zone; if daylight saving was applied, summer hours may sit one hour off the true diurnal cycle")
    points = {p.point_id: p for p in read_points(root / "points.csv")}
    for p in points.values():
        if p.equipment_type not in EQUIPMENT_TYPES:
            notes.append(f"point {p.point_id}: equipment_type {p.equipment_type!r} is not one of {', '.join(EQUIPMENT_TYPES)} (point ignored)")
        elif p.signal not in SIGNALS[p.equipment_type]:
            notes.append(f"point {p.point_id}: signal {p.signal!r} is not used for {p.equipment_type} (point ignored; used: {', '.join(SIGNALS[p.equipment_type])})")
    usable = {pid: p for pid, p in points.items() if p.equipment_type in EQUIPMENT_TYPES and p.signal in SIGNALS[p.equipment_type]}
    conv = {}
    for pid, p in list(usable.items()):
        dim = SIGNALS[p.equipment_type][p.signal]
        try:
            conv[pid] = (dim, *to_si(dim, p.unit))
        except ValueError as e:
            raise ValueError(f"point {pid}: {e}") from None
    parser = TimeParser(tz)
    raw, unknown = read_trends(root / "trends.csv", set(usable), parser)
    if unknown:
        notes.append(f"{len(unknown)} trend column(s)/id(s) are not in the used points and were ignored, e.g. {', '.join(unknown[:5])}")
    if parser.n_bad:
        notes.append(f"{parser.n_bad} timestamp(s) could not be parsed and were dropped")
    if parser.n_ambiguous:
        notes.append(f"{parser.n_ambiguous} clock time(s) fall in the daylight-saving fall-back hour (read as the first occurrence)")
    if parser.n_nonexistent:
        notes.append(f"{parser.n_nonexistent} clock time(s) fall in the spring-forward gap (no such local time exists)")
    if not raw:
        raise ValueError("no trend data for any used point")

    all_t = np.concatenate([np.asarray(t, float) for t, _, _ in raw.values() if len(t)])
    year = datetime.fromtimestamp(float(all_t.min()), timezone.utc).year
    off = std_offset_seconds(tz, year)
    G0 = np.floor((all_t.min() + off) / 86400.0) * 86400.0
    T = int(np.ceil((all_t.max() + off - G0 + 1e-6) / 3600.0))
    ev, qa = {}, {}
    for pid, (t, v, cnt) in raw.items():
        p = usable[pid]
        dim, fac, ofs = conv[pid]
        t, v = np.asarray(t, float), np.asarray(v, float)
        q = PointQA(pid, n_raw=len(t), n_nonnumeric=cnt["nonnumeric"], n_sentinel=cnt["sentinel"], n_empty=cnt["empty"], n_duplicate_ts=int(len(t) - len(np.unique(t))))
        v = v * fac + ofs
        lo, hi = PLAUSIBLE[dim]
        bad = np.isfinite(v) & ((v < lo) | (v > hi))
        q.n_out_of_range = int(bad.sum())
        v = np.where(bad, np.nan, v)
        q.n_valid = int(np.isfinite(v).sum())
        x, q.median_dt_min = hourly(t, v, T, G0, off, p.logging)
        if np.isfinite(x).any():
            q.median_si = float(np.nanmedian(x))
            rng = MEDIAN_RANGE.get((p.equipment_type, p.signal))
            if rng and not (rng[0] <= q.median_si <= rng[1]):
                notes.append(f"point {pid}: median {q.median_si:.1f} (SI) is outside the usual range {rng} for a {p.equipment_type} {p.signal} -- is the unit {p.unit!r} right?")
        key = f"{p.equipment_id}|{p.signal}"
        if key in ev:
            notes.append(f"point {pid}: a second point already provides {key}; the later one is ignored")
            continue
        ev[key] = x
        qa[pid] = q
    for pid in usable:
        if pid not in raw:
            notes.append(f"point {pid}: listed in points.csv but has no trend data")
    active_days = active_day_mask(ev, T)
    act_h = np.repeat(active_days, 24)[:T]
    key_of_point = {pid: f"{usable[pid].equipment_id}|{usable[pid].signal}" for pid in qa}
    for pid, q in qa.items():
        x = ev[key_of_point[pid]][act_h]
        q.coverage = float(np.isfinite(x).mean()) if len(x) else 0.0
        q.longest_gap_h = longest_gap(x)

    equipment = read_equipment(root / "equipment.csv")
    for p in usable.values():
        e = equipment.setdefault(p.equipment_id, dict(kind=p.equipment_type, function="", medium=""))
        if e["kind"] != p.equipment_type:
            notes.append(f"equipment {p.equipment_id}: points say {p.equipment_type} but equipment.csv says {e['kind']}")
    claims = read_claims(root / "connections.csv")
    for c in claims:
        if c.slot not in SLOTS:
            raise ValueError(f"connections.csv: unknown slot {c.slot!r} (known: {', '.join(SLOTS)})")
        spec = SLOTS[c.slot]
        for eid, allowed in ((c.owner, spec["owner"]), (c.member, spec["member"])):
            if eid not in equipment:
                if len(allowed) == 1:
                    equipment[eid] = dict(kind=allowed[0], function="", medium="")
                    notes.append(f"equipment {eid}: no recorded points; type {allowed[0]} inferred from slot {c.slot}")
                else:
                    raise ValueError(f"connections.csv: equipment {eid!r} has no points and its type is ambiguous ({'/'.join(allowed)}): list it in equipment.csv")
    t0 = datetime.fromtimestamp(float(G0), timezone.utc).replace(tzinfo=None)
    return FieldBuilding(building_id or ctx.get("building_id") or root.name, t0, T, equipment, usable, claims, ev, qa, ctx, notes, active_days)


# ---------------------------------------------------------------------------------------------- example writer (tests, demos)
def write_export(out: str | Path, equipment: dict[str, dict], series: dict[str, np.ndarray], claims: list[Claim], start: datetime, *, units: dict[str, str] | None = None,
                 sample_min: int = 15, tz: str | None = None, ts_format: str = "%m/%d/%Y %H:%M", context: dict | None = None) -> Path:
    """Write SI hourly `series` ("EQUIPMENT|signal" -> array) as a BAS-style export in US units (F, cfm, gpm, BTU/h unless `units` overrides), `sample_min`-minute samples,
    one point per series, wide `trends.csv`. `start` is the local clock time of hour 0. Used by the tests and to make example exports."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    us = {"temp": "degF", "air_flow": "cfm", "water_flow": "gpm", "power": "BTU/h"}
    us.update(units or {})
    pts, cols, T = [], [], len(next(iter(series.values())))
    for key, x in series.items():
        eid, sig = key.split("|")
        kind = equipment[eid]["kind"]
        dim = SIGNALS[kind][sig]
        fac, ofs = to_si(dim, us[dim])
        pid = f"{eid}.{sig}"
        pts.append(dict(point_id=pid, equipment_id=eid, equipment_type=kind, signal=sig, unit=us[dim], logging="interval"))
        cols.append((pid, (np.asarray(x, float) - ofs) / fac))
    with open(out / "points.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, ["point_id", "equipment_id", "equipment_type", "signal", "unit", "logging"])
        w.writeheader()
        w.writerows(pts)
    with open(out / "equipment.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["equipment_id", "equipment_type", "function", "medium"])
        for eid, e in equipment.items():
            w.writerow([eid, e["kind"], e.get("function", ""), e.get("medium", "")])
    per_hour = 60 // sample_min
    with open(out / "trends.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Timestamp"] + [c for c, _ in cols])
        for h in range(T):
            for k in range(per_hour):
                ts = (start + timedelta(hours=h, minutes=k * sample_min)).strftime(ts_format)
                w.writerow([ts] + [("" if not np.isfinite(x[h]) else f"{x[h]:.12g}") for _, x in cols])
    with open(out / "connections.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["owner_id", "member_id", "slot", "verified", "true_owner", "source"])
        for c in claims:
            w.writerow([c.owner, c.member, c.slot, c.verified, c.true_owner, c.source])
    (out / "context.json").write_text(json.dumps({**(context or {}), **({"timezone": tz} if tz else {})}, indent=1))
    return out


def parse_date(s: str | None) -> date | None:
    try:
        return date.fromisoformat(s) if s else None
    except ValueError:
        return None
