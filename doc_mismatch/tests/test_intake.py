"""Guards for the field-data intake loader (units, time, resampling, formats, quality checks)."""
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _intake_world import CLAIMS, EQUIPMENT, make_series  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import intake as I  # noqa: E402
from zoneinfo import ZoneInfo  # noqa: E402


def _equipment():
    return {k: {"function": "", "medium": "", **v} for k, v in EQUIPMENT.items()}


def _write(tmp_path, series, **kw):
    kw.setdefault("start", datetime(2021, 1, 4))
    return I.write_export(tmp_path, _equipment(), series, list(CLAIMS), **kw)


# ---------------------------------------------------------------------------------------------- units
def test_unit_conversions_are_exact_and_unknown_units_fail_loudly():
    f, o = I.to_si("temp", "°F")
    assert 68.0 * f + o == pytest.approx(20.0)
    assert I.to_si("temp", "K")[1] == -273.15
    assert 1000.0 * I.to_si("air_flow", "cfm")[0] == pytest.approx(1000 * 0.000471947443 * 1.2)
    assert 10.0 * I.to_si("water_flow", "GPM")[0] == pytest.approx(10 * 0.003785411784 / 60 * 998.0)
    assert I.to_si("power", "kW")[0] == 1000.0 and I.to_si("power", "ton")[0] == pytest.approx(3516.8528)
    with pytest.raises(ValueError, match="psi"):
        I.to_si("temp", "psi")


# ---------------------------------------------------------------------------------------------- time
def test_timestamp_formats_and_timezone_handling():
    tz = ZoneInfo("America/Chicago")
    a = I.TimeParser(tz)("2021-01-04 06:00:00")
    assert datetime.fromtimestamp(a, ZoneInfo("UTC")).hour == 12            # January: CST = UTC-6
    assert I.TimeParser(tz)("01/04/2021 06:00") == a                        # US date format
    assert I.TimeParser(tz)("1/4/2021 6:00 AM") == a                        # 12-hour clock
    assert I.TimeParser(tz)("2021-01-04T12:00:00+00:00") == a               # an explicit offset overrides the site zone
    assert I.TimeParser(tz)("not a time") is None
    assert I.TimeParser(None)("2021-01-04 06:00:00") == datetime(2021, 1, 4, 6).replace(tzinfo=ZoneInfo("UTC")).timestamp()   # no zone: taken as one consistent clock


def test_dst_ambiguous_and_nonexistent_clock_times_are_counted():
    p = I.TimeParser(ZoneInfo("America/Chicago"))
    p("2024-11-03 01:30:00")     # fall back: happens twice
    p("2024-03-10 02:30:00")     # spring forward: never happens
    p("2024-06-01 12:00:00")
    assert p.n_ambiguous == 1 and p.n_nonexistent == 1


def test_grid_is_local_standard_time_even_when_clocks_use_daylight_saving(tmp_path):
    T = 48
    ev = {"ENV|oat": np.arange(T, dtype=float), "Zone-1|temp": np.full(T, 21.0) + np.arange(T) * 0.1}
    eq = {"ENV": dict(kind="Weather"), "Zone-1": dict(kind="Zone")}
    I.write_export(tmp_path, eq, ev, [], datetime(2021, 7, 5, 0, 0), tz="America/Chicago", sample_min=60, units={"temp": "degC"})   # July: clocks are CDT (UTC-5), standard is CST (UTC-6)
    fb = I.load_export(tmp_path)
    x = fb.ev["ENV|oat"]
    # clock 00:00 CDT = 23:00 standard time of the previous day: the first sample sits at hour 23 of the grid, whose hour 0 is standard midnight
    assert np.isnan(x[:23]).all() and x[23] == 0.0 and x[24] == 1.0
    assert fb.t0_local == datetime(2021, 7, 4)


# ---------------------------------------------------------------------------------------------- resampling
def test_interval_resampling_keeps_hours_with_enough_samples():
    t = np.arange(0, 6 * 3600, 900.0)
    v = np.repeat([1., 2., 3., 4., 5., 6.], 4)
    x, dt = I.hourly(t, v, 6, 0.0, 0.0)
    assert dt == 15.0 and list(x) == [1, 2, 3, 4, 5, 6]
    v[[4, 5]] = np.nan          # hour 1 keeps 2 of 4 samples (>= half): kept
    v[[8, 9, 10]] = np.nan      # hour 2 keeps 1 of 4: dropped
    x, _ = I.hourly(t, v, 6, 0.0, 0.0)
    assert x[1] == 2.0 and np.isnan(x[2])


def test_change_of_value_points_hold_the_last_value_until_it_expires():
    x, _ = I.hourly(np.array([0., 5400., 20000.]), np.array([10., 20., 30.]), 8, 0.0, 0.0, "cov", max_hold_h=6.0)
    assert x[0] == 10.0 and x[1] == pytest.approx(15.0) and x[3] == 20.0 and x[7] == 30.0
    y, _ = I.hourly(np.array([0.]), np.array([10.]), 8, 0.0, 0.0, "cov", max_hold_h=6.0)      # a single logged value is held for 6 hours, then it is missing
    assert list(y[:6]) == [10.0] * 6 and np.isnan(y[6:]).all()


def test_duplicate_timestamps_and_sentinels_are_counted_not_used(tmp_path):
    (tmp_path / "points.csv").write_text("point_id,equipment_id,equipment_type,signal,unit\nz,Zone-1,Zone,temp,degC\n")
    rows = ["Timestamp,z"] + [f"2021-01-04 {h:02d}:00,{21 + h * 0.1}" for h in range(24)] + ["2021-01-04 05:00,999.0", "2021-01-04 06:00,-999", "2021-01-04 07:00,offline", "2021-01-04 08:00,", "2021-01-04 09:00,NaN", "2021-01-04 10:00,inf"]
    (tmp_path / "trends.csv").write_text("\n".join(rows))
    fb = I.load_export(tmp_path)
    q = fb.qa["z"]
    assert q.n_sentinel == 2 and q.n_nonnumeric == 1 and q.n_empty == 2 and q.n_out_of_range == 1 and q.n_duplicate_ts == 6     # -999 and inf; "offline"; a blank and NaN are just missing; 999 C is implausible; 6 timestamps repeat
    assert fb.ev["Zone-1|temp"][6] == pytest.approx(21.6)                            # the -999 sentinel row was dropped, the valid row kept


# ---------------------------------------------------------------------------------------------- round trip
def test_round_trip_through_a_bas_style_export_is_lossless(tmp_path):
    ev = make_series(T=24 * 6, seed=1)
    _write(tmp_path, ev)                                             # F / cfm / gpm / BTU/h, 15-minute samples, US date format
    fb = I.load_export(tmp_path)
    assert fb.n_hours == 24 * 6 and set(fb.ev) == set(ev)
    for k in ev:
        np.testing.assert_allclose(fb.ev[k], ev[k], rtol=1e-8, atol=1e-8, err_msg=k)
    assert len(fb.claims) == len(CLAIMS) and fb.claims[7].verified == "no"
    b = fb.base()
    assert set(b.slot_edges) >= {"ahu_vav", "vav_zone", "coil_ahu"} and b.nodes["Coil-1"]["brick_type"] == "Heating_Coil" and b.nodes["Coil-2"]["brick_type"] == "Cooling_Coil"


def test_long_and_wide_formats_give_the_same_series(tmp_path):
    ev = make_series(T=48, seed=2)
    d1, d2 = tmp_path / "wide", tmp_path / "long"
    _write(d1, ev, sample_min=60)
    _write(d2, ev, sample_min=60)
    wide = (d1 / "trends.csv").read_text().splitlines()
    heads = wide[0].split(",")[1:]
    long_rows = ["timestamp,point_id,value"]
    for line in wide[1:]:
        c = line.split(",")
        long_rows += [f"{c[0]},{h},{v}" for h, v in zip(heads, c[1:]) if v != ""]
    (d2 / "trends.csv").write_text("\n".join(long_rows))
    a, b = I.load_export(d1), I.load_export(d2)
    for k in a.ev:
        np.testing.assert_allclose(a.ev[k], b.ev[k])


def test_unknown_columns_missing_points_and_wrong_units_are_reported(tmp_path):
    ev = {"Zone-1|temp": np.full(48, 71.0) + np.arange(48) * 0.1, "ENV|oat": np.arange(48, dtype=float)}
    eq = {"Zone-1": dict(kind="Zone"), "ENV": dict(kind="Weather")}
    I.write_export(tmp_path, eq, ev, [], datetime(2021, 1, 4), sample_min=60, units={"temp": "degC"})       # values are really degF but labelled degC
    pts = (tmp_path / "points.csv").read_text() + "ghost,Zone-9,Zone,temp,degC,interval\ndamper,VAV-1,VAV,damper_pos,%,interval\n"
    (tmp_path / "points.csv").write_text(pts)
    tr = (tmp_path / "trends.csv").read_text().splitlines()
    (tmp_path / "trends.csv").write_text("\n".join([tr[0] + ",extra_column"] + [r + ",1" for r in tr[1:]]))
    notes = " | ".join(I.load_export(tmp_path).notes)
    assert "extra_column" in notes and "ghost" in notes and "damper_pos" in notes and "Zone-1.temp" in notes and "unit" in notes


def test_separate_chunks_are_not_penalised_for_the_months_between_them(tmp_path):
    rows = ["Timestamp,z,o"]
    for day0 in ("2021-01-04", "2021-06-14"):                                     # two 2-day chunks 5 months apart
        for h in range(48):
            d = datetime.fromisoformat(day0) + __import__("datetime").timedelta(hours=h)
            rows.append(f"{d:%Y-%m-%d %H:%M},{21 + 0.1 * (h % 24)},{-5 + 0.5 * (h % 24)}")
    (tmp_path / "trends.csv").write_text("\n".join(rows))
    (tmp_path / "points.csv").write_text("point_id,equipment_id,equipment_type,signal,unit\nz,Zone-1,Zone,temp,degC\no,ENV,Weather,oat,degC\n")
    fb = I.load_export(tmp_path)
    assert fb.n_hours > 24 * 160 and fb.n_chunks == 2 and int(fb.active_hours.sum()) == 96
    assert fb.qa["z"].coverage == 1.0 and fb.qa["z"].longest_gap_h == 0
