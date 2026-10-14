"""Mortar (Brick graph + Parquet timeseries) -> the intake format of `intake.py`. Needs rdflib and pyarrow (imported lazily).

Mortar: https://huggingface.co/datasets/gtfierro/mortar (timeseries, one Parquet file per stream under collection=DELTA/uuid=<id>/) and
gtfierro/mortargraphs (Brick models; a point links to its stream by `ref:hasExternalReference/ref:hasTimeseriesId`). Licence: see data_cache/timeseries/LICENSES.md.

What the converter decides, all of it written to `conversion_notes.md` next to the export:
  * WHICH points map to which signal (`POINT_CLASSES`): Brick point class -> (signal). Where one equipment has several candidates the more specific class wins
    (`PREFERENCE`) and the choice is noted.
  * ZONES: the zone a VAV `feeds`. Its temperature is the Zone_Air_Temperature_Sensor attached to that zone or to the VAV that feeds it. So for a zone the point-to-zone
    link comes from the same documentation as the VAV->zone claim; this is stated, not hidden.
  * UNITS are NOT in the data. US customary is ASSUMED (degF, cfm) and range-checked on the exported window; a point whose median is implausible in those units is dropped
    and reported, never converted on a guess.
  * TIME: the Parquet clock is UTC and the buildings are anonymised, so the export is on the UTC clock (`timezone: UTC`); day slices are UTC days.
  * WINDOWS (`pick_windows`): the trends are years long, so the export holds two 42-day windows (starting Jan 15 and Jul 15), each chosen among the available years by DATA
    COVERAGE ONLY (mean fraction of expected samples across the exported points; never by looking at values). One-minute data are averaged to 15 minutes.
  * The ambient temperature is the first AHU outdoor-air sensor that has data, attached to a `Weather` node `ENV`.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

BRICK_NS = "https://brickschema.org/schema/Brick#"
REF_NS = "https://brickschema.org/schema/Brick/ref#"
# Brick point class -> signal, per equipment class; PREFERENCE orders candidates that map to the same signal (most specific first)
POINT_CLASSES = {
    "AHU": {"Supply_Air_Temperature_Sensor": "sat", "Mixed_Air_Temperature_Sensor": "mat", "Supply_Air_Flow_Sensor": "flow", "Air_Flow_Sensor": "flow"},
    "VAV": {"Supply_Air_Flow_Sensor": "flow", "Discharge_Air_Flow_Sensor": "flow", "Air_Flow_Sensor": "flow",
            "Discharge_Air_Temperature_Sensor": "t_dis", "Supply_Air_Temperature_Sensor": "t_dis"},
}
PREFERENCE = ["Supply_Air_Flow_Sensor", "Discharge_Air_Flow_Sensor", "Air_Flow_Sensor", "Discharge_Air_Temperature_Sensor", "Supply_Air_Temperature_Sensor",
              "Mixed_Air_Temperature_Sensor"]
ASSUMED_UNIT = {"temp": "degF", "air_flow": "cfm"}
UNIT_PLAUSIBLE = {"temp": (20.0, 130.0), "air_flow": (5.0, 20000.0)}          # median of the exported window, in the ASSUMED unit; outside -> point dropped
UNIT_PLAUSIBLE_SIGNAL = {"oat": (-20.0, 115.0)}                                # outdoor air can have a cold-winter median below 20 degF
SIGNAL_DIM = {"sat": "temp", "mat": "temp", "t_dis": "temp", "temp": "temp", "oat": "temp", "flow": "air_flow"}
WINDOW_DAYS = 42
WINDOW_STARTS = ((1, 15), (7, 15))
MIN_WINDOW_SCORE = 0.8


@dataclass
class Chosen:
    equipment_id: str
    equipment_type: str
    signal: str
    uuid: str
    brick_class: str
    label: str


@dataclass
class ParsedBuilding:
    building: str
    ahus: list[str]
    vavs: list[str]
    zones: list[str]
    ahu_vav: list[tuple[str, str]]
    vav_zone: list[tuple[str, str]]
    points: dict[str, list[tuple[str, str, str]]]      # node id -> [(brick class, label, uuid)] of its points that have a timeseries
    notes: list[str] = field(default_factory=list)


def _short(x) -> str:
    return str(x).split("#")[-1].split("/")[-1]


def parse_brick(ttl: str | Path, building: str | None = None) -> ParsedBuilding:
    from rdflib import RDF, RDFS, Graph, Namespace
    B, R = Namespace(BRICK_NS), Namespace(REF_NS)
    g = Graph()
    g.parse(str(ttl), format="turtle")
    types = {}
    for s, o in g.subject_objects(RDF.type):
        types.setdefault(s, []).append(_short(o))
    nodes = lambda *cls: {_short(s): s for s, ts in types.items() if any(t in cls for t in ts)}  # noqa: E731    # only the equipment kinds we use: no name clashes with rooms
    ahu_n, vav_n, zone_n = nodes("Air_Handler_Unit", "AHU"), nodes("VAV"), nodes("HVACZone", "HVAC_Zone")     # `AHU` is a second class name for an air handler (bldg30 / smc use only it)

    def has_ts(pt):
        return [str(u) for r in g.objects(pt, R.hasExternalReference) for u in g.objects(r, R.hasTimeseriesId)]

    points = {}
    for name, term in {**ahu_n, **vav_n, **zone_n}.items():
        for pt in g.objects(term, B.hasPoint):
            u = has_ts(pt)
            if u:
                cls = next((t for t in types.get(pt, []) if t != "Point"), "?")
                label = next((str(l) for l in g.objects(pt, RDFS.label)), _short(pt))
                points.setdefault(name, []).append((cls, label, u[0]))

    def feeds(src, dst):
        return sorted((sn, _short(y)) for sn, st in src.items() for y in g.objects(st, B.feeds) if _short(y) in dst and dst[_short(y)] == y)

    return ParsedBuilding(building or Path(ttl).stem.replace("mortar__", ""), sorted(ahu_n), sorted(vav_n), sorted(zone_n), feeds(ahu_n, vav_n), feeds(vav_n, zone_n), points)


def choose_points(pb: ParsedBuilding) -> tuple[list[Chosen], list[str]]:
    """Map the parsed points to intake signals. Returns (chosen, notes)."""
    notes, chosen = [], []

    ambiguous = Counter()

    def pick(eq, kind, table):
        by_signal = {}
        for cls, label, u in sorted(pb.points.get(eq, []), key=lambda p: (PREFERENCE.index(p[0]) if p[0] in PREFERENCE else 99, p[1])):
            sig = table.get(cls)
            if sig:
                by_signal.setdefault(sig, []).append((cls, label, u))
        for sig, cands in by_signal.items():
            cls, label, u = cands[0]
            if len({c[2] for c in cands}) > 1:
                ambiguous[(kind, sig, tuple(c[0] for c in cands))] += 1
            chosen.append(Chosen(eq, kind, sig, u, cls, label))

    for a in pb.ahus:
        pick(a, "AHU", POINT_CLASSES["AHU"])
    for v in pb.vavs:
        pick(v, "VAV", POINT_CLASSES["VAV"])
    for (kind, sig, classes), n in sorted(ambiguous.items()):
        notes.append(f"{n} {kind}(s) had several candidate {sig} points ({', '.join(classes)}); the first class was used (most specific)")
    # zone temperature: a Zone_Air_Temperature_Sensor on the zone itself or on a VAV that feeds it
    feeders = {}
    for v, z in pb.vav_zone:
        feeders.setdefault(z, []).append(v)
    for z in pb.zones:
        cands = [p for src in [z] + feeders.get(z, []) for p in pb.points.get(src, []) if p[0] == "Zone_Air_Temperature_Sensor"]
        if cands:
            cls, label, u = sorted(cands, key=lambda p: p[1])[0]
            if len({c[2] for c in cands}) > 1:
                notes.append(f"{z} temp: {len(cands)} candidate zone-temperature points; used `{label}`")
            chosen.append(Chosen(z, "Zone", "temp", u, cls, label))
    # outdoor temperature: first AHU outdoor-air sensor with data
    for a in pb.ahus:
        oa = [p for p in pb.points.get(a, []) if p[0] == "Outside_Air_Temperature_Sensor"]
        if oa:
            cls, label, u = sorted(oa, key=lambda p: p[1])[0]
            chosen.append(Chosen("ENV", "Weather", "oat", u, cls, label))
            notes.append(f"outdoor temperature taken from {a} `{label}`")
            break
    else:
        notes.append("no AHU outdoor-air temperature point with data: no Weather series (a pool cannot be built without one)")
    return chosen, notes


# ---------------------------------------------------------------------------------------------- streams and windows
@lru_cache(maxsize=4)
def _stream_index(mortar_dir: str) -> dict[str, Path]:
    """uuid -> Parquet file, over every `collection=<name>/uuid=<id>/` folder (the collection is DELTA or a building name, so it cannot be assumed)"""
    return {p.parent.name[len("uuid="):]: p for p in Path(mortar_dir).glob("collection=*/uuid=*/*.parquet")}


def read_stream(mortar_dir: Path, uuid: str) -> tuple[np.ndarray, np.ndarray]:
    """(epoch seconds UTC, values) of one stream, sorted by time."""
    import pyarrow.parquet as pq
    path = _stream_index(str(mortar_dir)).get(uuid)
    if path is None:
        raise FileNotFoundError(f"no parquet for stream {uuid}")
    tbl = pq.read_table(path, columns=["time", "value"])
    t = tbl.column("time").to_numpy().astype("datetime64[ms]").astype(np.int64) / 1000.0
    v = tbl.column("value").to_numpy(zero_copy_only=False).astype(float)
    o = np.argsort(t, kind="stable")
    return t[o], v[o]


def _step(t: np.ndarray) -> float:
    return float(np.median(np.diff(t[: 5000]))) if len(t) > 2 else float("nan")


def window_score(streams: dict, start: float, end: float) -> float:
    """mean over streams of (samples in [start, end)) / (samples expected at the stream's own median step), capped at 1"""
    sc = []
    for t, _ in streams.values():
        step = _step(t)
        if not np.isfinite(step) or step <= 0:
            sc.append(0.0)
            continue
        n = int(np.searchsorted(t, end) - np.searchsorted(t, start))
        sc.append(min(1.0, n / ((end - start) / step)))
    return float(np.mean(sc)) if sc else 0.0


def pick_windows(streams: dict, n_days: int = WINDOW_DAYS, starts=WINDOW_STARTS, min_score: float = MIN_WINDOW_SCORE) -> tuple[list[tuple[float, float, float]], list[str]]:
    """For each (month, day) start, the year whose window has the best data coverage (ties: the later year). Returns ([(start, end, score)], notes). Value-independent."""
    if not streams:
        return [], ["no streams"]
    t_lo = min(t[0] for t, _ in streams.values() if len(t))
    t_hi = max(t[-1] for t, _ in streams.values() if len(t))
    y0, y1 = datetime.fromtimestamp(t_lo, timezone.utc).year, datetime.fromtimestamp(t_hi, timezone.utc).year
    out, notes = [], []
    for m, d in starts:
        best = None
        for y in range(y0, y1 + 1):
            s = datetime(y, m, d, tzinfo=timezone.utc).timestamp()
            e = s + n_days * 86400
            sc = window_score(streams, s, e)
            if best is None or sc >= best[2]:
                best = (s, e, sc)
        if best and best[2] >= min_score:
            out.append(best)
        else:
            notes.append(f"no {m:02d}-{d:02d} window reached coverage {min_score:.0%} (best {best[2] if best else 0:.0%})")
    return out, notes


def to_15min(t: np.ndarray, v: np.ndarray, s: float, e: float) -> tuple[np.ndarray, np.ndarray]:
    """window [s, e) of a stream; streams stepping faster than 5 minutes are averaged into 15-minute bins (bin start stamps), others returned as they are"""
    i, j = np.searchsorted(t, s), np.searchsorted(t, e)
    t, v = t[i:j], v[i:j]
    if len(t) > 2 and _step(t) < 300:
        b = np.floor((t - s) / 900.0).astype(int)
        ok = np.isfinite(v)
        n = np.bincount(b[ok], minlength=int((e - s) // 900))
        tot = np.bincount(b[ok], weights=v[ok], minlength=int((e - s) // 900))
        keep = n > 0
        return s + 900.0 * np.flatnonzero(keep), tot[keep] / n[keep]
    return t, v


# ---------------------------------------------------------------------------------------------- the converter
MAX_SAMPLE = 60      # streams read in full to score candidate windows (deterministic: evenly spaced over the sorted stream list)


def convert_building(ttl: str | Path, mortar_dir: str | Path, out_dir: str | Path, building: str | None = None) -> dict:
    """Write an intake-format export of one Mortar building into `out_dir`; returns a summary dict (also written to conversion_notes.md)."""
    mortar_dir, out_dir = Path(mortar_dir), Path(out_dir)
    pb = parse_brick(ttl, building)
    chosen, notes = choose_points(pb)
    notes = pb.notes + notes
    # pass 1: window coverage from a deterministic sample of the streams (values are never used)
    ordered = sorted(chosen, key=lambda c: (c.equipment_id, c.signal))
    stride = max(1, len(ordered) // MAX_SAMPLE)
    sample = {}
    for c in ordered[::stride]:
        try:
            sample[(c.equipment_id, c.signal)] = read_stream(mortar_dir, c.uuid)
        except FileNotFoundError:
            pass
    if not sample:
        raise FileNotFoundError(f"none of the {len(chosen)} mapped streams of {pb.building} was found under {mortar_dir} (collection=*/uuid=*/): is the download complete?")
    windows, wnotes = pick_windows(sample)
    notes += wnotes + ([f"window coverage was measured on {len(sample)} of {len(chosen)} mapped streams (evenly spaced, sorted by id)"] if len(sample) < len(chosen) else [])
    del sample
    summary = dict(building=pb.building, ahus=len(pb.ahus), vavs=len(pb.vavs), zones=len(pb.zones), mapped=len(chosen), windows=[], dropped=[], notes=notes)
    if not windows:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "conversion_notes.md").write_text(f"# {pb.building}\n\nNo export: " + "; ".join(notes))
        return summary
    # pass 2: each stream is read once, cut to the windows and released
    pieces, missing = {}, []
    for c in chosen:
        try:
            t, v = read_stream(mortar_dir, c.uuid)
        except FileNotFoundError:
            missing.append(c)
            continue
        pieces[(c.equipment_id, c.signal)] = [to_15min(t, v, s, e) for s, e, _ in windows]
    if missing:
        notes.append(f"{len(missing)} mapped point(s) have no stream in the download and were left out: " + ", ".join(f"{c.equipment_id}.{c.signal}" for c in missing[:5]))
    # unit plausibility on the exported windows
    keep = []
    for c in chosen:
        if (c.equipment_id, c.signal) not in pieces:
            continue
        vals = np.concatenate([v for _, v in pieces[(c.equipment_id, c.signal)]])
        vals = vals[np.isfinite(vals)]
        dim = SIGNAL_DIM[c.signal]
        lo, hi = UNIT_PLAUSIBLE_SIGNAL.get(c.signal) or UNIT_PLAUSIBLE[dim]
        if len(vals) == 0:
            summary["dropped"].append(f"{c.equipment_id}.{c.signal} (no values in the chosen windows)")
            continue
        ref = float(np.percentile(vals, 90)) if dim == "air_flow" else float(np.median(vals))       # a flow is judged by its 90th percentile: boxes are closed much of the time
        if dim == "air_flow" and ref == 0.0:
            summary.setdefault("all_zero", []).append(f"{c.equipment_id}.{c.signal}")               # dead or permanently closed: kept, readiness will call it flat
        elif not (lo <= ref <= hi):
            summary["dropped"].append(f"{c.equipment_id}.{c.signal} ({'90th percentile' if dim == 'air_flow' else 'median'} {ref:.3g} outside {lo:g}-{hi:g} {ASSUMED_UNIT[dim]}: unit implausible)")
            continue
        keep.append(c)
    out_dir.mkdir(parents=True, exist_ok=True)
    equip = {}
    for c in keep:
        equip[c.equipment_id] = c.equipment_type
    with open(out_dir / "points.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["point_id", "equipment_id", "equipment_type", "signal", "unit", "logging", "source_id", "brick_class", "label"])
        for c in keep:
            w.writerow([f"{c.equipment_id}.{c.signal}", c.equipment_id, c.equipment_type, c.signal, ASSUMED_UNIT[SIGNAL_DIM[c.signal]], "interval", c.uuid, c.brick_class, c.label])
    with open(out_dir / "trends.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["timestamp", "point_id", "value"])
        for wi in range(len(windows)):
            for c in keep:
                t, v = pieces[(c.equipment_id, c.signal)][wi]
                pid = f"{c.equipment_id}.{c.signal}"
                for ti, vi in zip(t, v):
                    if np.isfinite(vi):
                        w.writerow([datetime.fromtimestamp(ti, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"), pid, f"{vi:.6g}"])
    have = set(equip)
    with open(out_dir / "equipment.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["equipment_id", "equipment_type", "function", "medium"])
        for a in pb.ahus:
            w.writerow([a, "AHU", "", ""])
        for v in pb.vavs:
            w.writerow([v, "VAV", "", ""])
        for z in pb.zones:
            w.writerow([z, "Zone", "", ""])
        if "ENV" in have:
            w.writerow(["ENV", "Weather", "", ""])
    with open(out_dir / "connections.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["owner_id", "member_id", "slot", "verified", "true_owner", "source"])
        for a, v in pb.ahu_vav:
            w.writerow([a, v, "ahu_vav", "unknown", "", "Brick model (Mortar)"])
        for v, z in pb.vav_zone:
            w.writerow([v, z, "vav_zone", "unknown", "", "Brick model (Mortar)"])
    ctx = dict(building_id=f"mortar_{pb.building}", timezone="UTC",
               notes="Mortar (anonymised): timestamps are UTC, local time unknown; units assumed US customary; connections are the Brick model, not field-verified.",
               windows=[dict(start=datetime.fromtimestamp(s, timezone.utc).date().isoformat(), days=WINDOW_DAYS, coverage=round(sc, 3)) for s, e, sc in windows])
    (out_dir / "context.json").write_text(json.dumps(ctx, indent=1))
    summary["windows"] = ctx["windows"]
    summary["exported"] = len(keep)
    by_sig = {}
    for c in keep:
        by_sig[c.signal] = by_sig.get(c.signal, 0) + 1
    summary["by_signal"] = by_sig
    md = [f"# Mortar {pb.building} -> intake export", "", f"- Brick: {len(pb.ahus)} AHU, {len(pb.vavs)} VAV, {len(pb.zones)} zones; {len(pb.ahu_vav)} ahu_vav and {len(pb.vav_zone)} vav_zone documented connections.",
          f"- Exported points: {len(keep)} of {len(chosen)} mapped ({', '.join(f'{k} x{n}' for k, n in sorted(by_sig.items()))}).",
          "- Windows (42 days each, chosen by coverage only): " + ", ".join(f"{w['start']} (coverage {w['coverage']:.0%})" for w in ctx["windows"]),
          "- Assumptions: US customary units (degF, cfm), range-checked; UTC clock; one-minute data averaged to 15 minutes; zone temperature taken from the sensor attached to the zone or to the VAV that feeds it.", ""]
    if summary.get("all_zero"):
        md += [f"- {len(summary['all_zero'])} flow point(s) read exactly 0 for the whole export (dead sensor or permanently closed box); kept, and shown as flat by the readiness report: " + ", ".join(summary["all_zero"][:6]) + (" ..." if len(summary["all_zero"]) > 6 else ""), ""]
    if summary["dropped"]:
        md += ["## Dropped (not exported)", ""] + [f"- {d}" for d in summary["dropped"]] + [""]
    if notes:
        md += ["## Notes", ""] + [f"- {n}" for n in notes] + [""]
    (out_dir / "conversion_notes.md").write_text("\n".join(md))
    return summary
