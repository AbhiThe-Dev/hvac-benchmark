"""Guards for the Mortar (Brick + Parquet) -> intake converter, on a small synthetic building written in the same layout."""
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("rdflib")
pytest.importorskip("pyarrow")
import pyarrow as pa  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import intake as I  # noqa: E402
from docmismatch import mortar_adapter as M  # noqa: E402

TTL = """@prefix brick: <https://brickschema.org/schema/Brick#> .
@prefix ref: <https://brickschema.org/schema/Brick/ref#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ns: <urn:t/b1#> .
ns:AHU01 a brick:Air_Handler_Unit ; brick:feeds ns:VAV1, ns:VAV2 ;
  brick:hasPoint ns:oat, ns:sat, ns:mat .
ns:VAV1 a brick:VAV ; brick:feeds ns:Z1 ; brick:hasPoint ns:fl1, ns:fl1g, ns:dt1, ns:zt1 .
ns:VAV2 a brick:VAV ; brick:feeds ns:Z2 ; brick:hasPoint ns:fl2, ns:zt2 .
ns:Z1 a brick:HVACZone . ns:Z2 a brick:HVACZone .
ns:Z1 a brick:Room .
ns:oat a brick:Outside_Air_Temperature_Sensor ; rdfs:label "AHU oat" ; ref:hasExternalReference [ ref:hasTimeseriesId "u-oat" ] .
ns:sat a brick:Supply_Air_Temperature_Sensor ; rdfs:label "AHU sat" ; ref:hasExternalReference [ ref:hasTimeseriesId "u-sat" ] .
ns:mat a brick:Mixed_Air_Temperature_Sensor ; rdfs:label "AHU mat (no data)" .
ns:fl1 a brick:Supply_Air_Flow_Sensor ; rdfs:label "VAV1 flow" ; ref:hasExternalReference [ ref:hasTimeseriesId "u-fl1" ] .
ns:fl1g a brick:Air_Flow_Sensor ; rdfs:label "VAV1 generic flow" ; ref:hasExternalReference [ ref:hasTimeseriesId "u-fl1g" ] .
ns:dt1 a brick:Discharge_Air_Temperature_Sensor ; rdfs:label "VAV1 dat" ; ref:hasExternalReference [ ref:hasTimeseriesId "u-dt1" ] .
ns:zt1 a brick:Zone_Air_Temperature_Sensor ; rdfs:label "VAV1 zone temp" ; ref:hasExternalReference [ ref:hasTimeseriesId "u-zt1" ] .
ns:fl2 a brick:Supply_Air_Flow_Sensor ; rdfs:label "VAV2 flow (kg/s, wrong unit)" ; ref:hasExternalReference [ ref:hasTimeseriesId "u-fl2" ] .
ns:zt2 a brick:Zone_Air_Temperature_Sensor ; rdfs:label "VAV2 zone temp" ; ref:hasExternalReference [ ref:hasTimeseriesId "u-zt2" ] .
"""


def _ts(year, month, day):
    return datetime(year, month, day, tzinfo=timezone.utc).timestamp()


def _write_stream(root: Path, uuid: str, t: np.ndarray, v: np.ndarray, collection: str = "DELTA"):
    d = root / (f"collection={collection}") / f"uuid={uuid}"
    d.mkdir(parents=True, exist_ok=True)
    tbl = pa.table({"value": v, "label": ["x"] * len(t), "uri": ["y"] * len(t),
                    "time": pa.array((t * 1e6).astype("int64"), type=pa.timestamp("us", tz="UTC"))})
    pq.write_table(tbl, d / "part.parquet")


@pytest.fixture()
def mortar(tmp_path):
    (tmp_path / "b1.ttl").write_text(TTL)
    t = np.arange(_ts(2016, 1, 1), _ts(2018, 1, 1), 900.0)
    yr = (t - _ts(2016, 1, 1)) / 86400.0
    season = np.cos(2 * np.pi * (yr - 200) / 365.25)                    # warm in summer
    day = np.sin(2 * np.pi * (t % 86400) / 86400)
    gap = ((t >= _ts(2016, 7, 1)) & (t < _ts(2016, 9, 1))) | ((t >= _ts(2017, 1, 10)) & (t < _ts(2017, 2, 10)))   # no data in summer 2016, nor in most of the 2017 January window
    s = {"u-oat": 55 + 25 * season + 6 * day, "u-sat": 55 + 2 * day, "u-fl1": 400 + 150 * day, "u-fl1g": 390 + 150 * day, "u-dt1": 60 + 8 * day, "u-zt1": 72 + 2 * day,
         "u-fl2": 0.3 + 0.1 * day, "u-zt2": 71 + 2 * day}
    for u, v in s.items():
        keep = ~gap if u != "u-fl2" else np.ones(len(t), bool)
        _write_stream(tmp_path, u, t[keep], v[keep], collection="b1" if u in ("u-zt1", "u-zt2") else "DELTA")     # streams live under DELTA or a building-named collection
    return tmp_path


def test_brick_parsing_and_point_choice(mortar):
    pb = M.parse_brick(mortar / "b1.ttl")
    assert pb.ahus == ["AHU01"] and pb.vavs == ["VAV1", "VAV2"] and pb.zones == ["Z1", "Z2"]         # the Room node named Z1 does not confuse the zone
    assert pb.ahu_vav == [("AHU01", "VAV1"), ("AHU01", "VAV2")] and pb.vav_zone == [("VAV1", "Z1"), ("VAV2", "Z2")]
    chosen, notes = M.choose_points(pb)
    got = {(c.equipment_id, c.signal): c.brick_class for c in chosen}
    assert got[("VAV1", "flow")] == "Supply_Air_Flow_Sensor"                                          # more specific class beats the generic Air_Flow_Sensor
    assert ("AHU01", "mat") not in got                                                                 # a point without a timeseries is not exported
    assert got[("Z1", "temp")] == "Zone_Air_Temperature_Sensor" and got[("ENV", "oat")] == "Outside_Air_Temperature_Sensor"
    assert any("1 VAV(s) had several candidate flow points (Supply_Air_Flow_Sensor, Air_Flow_Sensor)" in n for n in notes)


def test_one_minute_data_are_averaged_into_fifteen_minute_bins():
    t = np.arange(0.0, 3600.0, 60.0)
    tt, vv = M.to_15min(t, np.arange(60.0), 0.0, 3600.0)
    assert len(tt) == 4 and list(tt) == [0, 900, 1800, 2700] and vv[0] == pytest.approx(np.mean(np.arange(15)))
    t2 = np.arange(0.0, 3600.0, 900.0)
    assert list(M.to_15min(t2, np.arange(4.0), 0.0, 3600.0)[1]) == [0, 1, 2, 3]                        # 15-minute data pass through untouched


def test_windows_are_chosen_by_coverage_not_by_values(mortar):
    pb = M.parse_brick(mortar / "b1.ttl")
    chosen, _ = M.choose_points(pb)
    streams = {(c.equipment_id, c.signal): M.read_stream(mortar, c.uuid) for c in chosen if c.uuid != "u-fl2"}
    wins, notes = M.pick_windows(streams)
    starts = [datetime.fromtimestamp(s, timezone.utc).date().isoformat() for s, _, _ in wins]
    assert starts == ["2016-01-15", "2017-07-15"]                     # January: the 2017 window is mostly empty; July: the 2016 window is empty
    assert all(sc >= M.MIN_WINDOW_SCORE for _, _, sc in wins)


def test_equal_coverage_picks_the_later_year_and_thin_coverage_yields_no_window():
    t = np.arange(_ts(2016, 1, 1), _ts(2018, 1, 1), 900.0)
    full = {("a", "temp"): (t, np.ones(len(t)))}
    wins, _ = M.pick_windows(full)
    assert [datetime.fromtimestamp(s, timezone.utc).year for s, _, _ in wins] == [2017, 2017]
    short = t < _ts(2016, 2, 1)                                                                         # data exist for one month only: 17 of the 42 January days, none in July
    wins, notes = M.pick_windows({("a", "temp"): (t[short], np.ones(int(short.sum())))})
    assert wins == [] and len(notes) == 2 and "coverage" in notes[0]


def test_full_conversion_loads_through_the_intake_and_drops_implausible_units(mortar, tmp_path):
    out = tmp_path / "export"
    summary = M.convert_building(mortar / "b1.ttl", mortar, out, building="b1")
    assert any(d.startswith("VAV2.flow") and "unit implausible" in d for d in summary["dropped"])      # 0.3 "cfm" is not plausible: dropped and reported, not converted
    fb = I.load_export(out)
    assert not any(n.startswith("no time zone") for n in fb.notes) and fb.context["timezone"] == "UTC"
    assert set(fb.ev) == {"VAV1|flow", "VAV1|t_dis", "Z1|temp", "Z2|temp", "AHU01|sat", "ENV|oat"}
    assert fb.n_chunks == 2 and len(fb.claims) == 4 and {c.slot for c in fb.claims} == {"ahu_vav", "vav_zone"}
    z = fb.ev["Z1|temp"][fb.active_hours]
    assert np.nanmean(z) == pytest.approx((72 - 32) * 5 / 9, abs=0.2)                                   # degF -> degC by the intake
    assert all(c.verified == "unknown" for c in fb.claims)
    text = (out / "conversion_notes.md").read_text()
    assert "US customary" in text and "coverage" in text


def test_a_download_that_cannot_be_found_fails_loudly(mortar, tmp_path):
    with pytest.raises(FileNotFoundError, match="is the download complete"):
        M.convert_building(mortar / "b1.ttl", tmp_path / "empty", tmp_path / "out", building="b1")


def test_dead_flow_is_kept_and_no_data_is_reported_as_such(mortar, tmp_path):
    t = np.arange(_ts(2016, 1, 1), _ts(2018, 1, 1), 900.0)
    _write_stream(mortar, "u-fl2", t, np.zeros(len(t)))                                                  # a flow stream that is exactly 0 all the time
    _write_stream(mortar, "u-dt1", t[t < _ts(2016, 3, 1)], np.full(int((t < _ts(2016, 3, 1)).sum()), 60.0))    # data only outside the chosen windows for the July one
    out = tmp_path / "export"
    summary = M.convert_building(mortar / "b1.ttl", mortar, out, building="b1")
    assert "VAV2.flow" in summary.get("all_zero", []) and not any(d.startswith("VAV2.flow") for d in summary["dropped"])
    fb = I.load_export(out)
    assert "VAV2|flow" in fb.ev and np.nanmax(fb.ev["VAV2|flow"]) == 0.0


def test_an_air_handler_filed_under_the_alias_class_ahu_is_recognised(tmp_path):
    (tmp_path / "a.ttl").write_text(TTL.replace("brick:Air_Handler_Unit", "brick:AHU"))
    pb = M.parse_brick(tmp_path / "a.ttl")
    assert pb.ahus == ["AHU01"] and pb.ahu_vav == [("AHU01", "VAV1"), ("AHU01", "VAV2")]
    chosen, _ = M.choose_points(pb)
    assert {(c.equipment_id, c.signal) for c in chosen} >= {("AHU01", "sat"), ("ENV", "oat")}
