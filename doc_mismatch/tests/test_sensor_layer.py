import json

import numpy as np
import pytest

from docmismatch.dr import sensor_layer as SL

STATS = SL.STATS_PATH


@pytest.fixture(scope="module")
def stats():
    if not STATS.exists():
        pytest.skip("run scripts/23_sensor_stats.py first")
    return SL.load_stats()


def _truth(n=20000, tags=("A|sat", "A|flow", "A|kw", "A|value", "A|htg")):
    t = np.arange(n)
    base = {"sat": 15 + 5 * np.sin(t / 50.0), "flow": 500 + 100 * np.cos(t / 30.0), "kw": 20 + 10 * np.sin(t / 20.0) ** 2, "value": 18 + 2 * np.sin(t / 70.0), "htg": 300 + 50 * np.sin(t / 40.0)}
    return {tg: base[tg.split("|")[1]].astype(float) for tg in tags}


def test_stats_json_flags_assumed(stats):
    P = stats["profile_inputs"]
    assert P["timestamp"]["jitter_min"]["assumed"] is True
    assert P["drift_K_per_90d"]["linear_sd"]["assumed"] is True
    assert P["dropout"]["field_prior_frac"]["assumed"] is True
    assert P["noise_sd"]["temp"]["assumed"] is False
    assert "long-term (months/years) sensor drift" in P["not_estimable"]


def test_no_sealed_files_named():
    src = open(SL.__file__).read() + open(str(SL.STATS_PATH.parents[3] / "doc_mismatch" / "scripts" / "23_sensor_stats.py")).read()
    assert "assert not f.name.startswith((\"OA_damper\", \"SA_temp_bias\"))" in src


def test_legacy_moments():
    rng = np.random.default_rng(0)
    truth = _truth(200000)
    out = SL.apply(truth, SL.legacy_profile(), rng)
    r = out["A|sat"] - truth["A|sat"]
    assert abs(r.std() - 0.25) < 0.005 and abs(r.mean()) < 0.005
    r = out["A|flow"] / truth["A|flow"] - 1
    assert abs(r.std() - 0.02) < 0.001
    x = truth["A|kw"]
    r = out["A|kw"] - x
    exp_sd = np.sqrt((0.03 * x) ** 2 + (0.002 * (np.abs(x).max() + 1)) ** 2)
    assert abs((r / exp_sd).std() - 1) < 0.02
    # 'value': noise sd 0.30 plus one static offset sd 0.15 per sensor -> across sensors the offset variance shows
    offs = []
    for s in range(400):
        o = SL.apply({"S|value": truth["A|value"][:200]}, SL.legacy_profile(), np.random.default_rng(s))["S|value"]
        offs.append((o - truth["A|value"][:200]).mean())
    assert abs(np.std(offs) - np.hypot(0.15, 0.30 / np.sqrt(200))) < 0.02
    o = SL.apply({"S|value": truth["A|value"]}, SL.legacy_profile(), np.random.default_rng(1))["S|value"]
    assert abs((o - truth["A|value"]).std() - 0.30) < 0.01
    # no missing / stale / quantisation
    assert np.isfinite(out["A|sat"]).all() and len(np.unique(np.round(np.diff(out["A|sat"]), 12))) > 1000


def test_dropout_and_stale_fractions():
    p = SL.SensorProfile(noise_sd={"temp": 0.1, "value": 0, "flow": 0, "power": 0}, dropout_frac=0.08, dropout_run_mean_h=3.0, stale_frac=0.05, stale_run_mean_h=6.0)
    truth = {"A|sat": np.linspace(10, 20, 400000)}
    out, fl = SL.apply_with_flags(truth, p, np.random.default_rng(3), nan_out=True)
    assert abs(np.isnan(out["A|sat"]).mean() - 0.08) < 0.008
    assert abs(fl["A|sat"]["dropout"].mean() - 0.08) < 0.008
    assert abs(fl["A|sat"]["stale"].mean() - 0.05) < 0.008
    # dropout run mean ~3 h (runs may merge, so allow slack)
    m = fl["A|sat"]["dropout"]
    d = np.diff(np.r_[0, m.astype(int), 0])
    lens = np.flatnonzero(d == -1) - np.flatnonzero(d == 1)
    assert 2.5 < lens.mean() < 3.8
    # stale samples are exact repeats of the previous output
    o2, f2 = SL.apply_with_flags(truth, p, np.random.default_rng(3), nan_out=False)
    dr = f2["A|sat"]["dropout"]
    st = f2["A|sat"]["stale"] & ~dr & ~np.r_[False, dr[:-1]]
    idx = np.flatnonzero(st)
    assert len(idx) > 1000
    assert (o2["A|sat"][idx] == o2["A|sat"][idx - 1]).all()


def test_finite_when_not_nan_out(stats):
    for level in ("legacy", "estimated", "wide"):
        for s in range(5):
            rng = np.random.default_rng(s)
            p = SL.draw_profile(stats, rng, level)
            out = SL.apply(_truth(500), p, rng, nan_out=False)
            assert all(np.isfinite(v).all() for v in out.values()), level
    p = SL.draw_profile(stats, np.random.default_rng(9), "wide")
    p.dropout_frac = 0.2
    out = SL.apply(_truth(500), p, np.random.default_rng(1), nan_out=True)
    assert any(np.isnan(v).any() for v in out.values())


def test_determinism(stats):
    for level in ("legacy", "estimated", "wide"):
        a = SL.apply(_truth(300), SL.draw_profile(stats, np.random.default_rng(5), level), np.random.default_rng(6))
        b = SL.apply(_truth(300), SL.draw_profile(stats, np.random.default_rng(5), level), np.random.default_rng(6))
        assert all(np.array_equal(a[k], b[k]) for k in a)
    c = SL.apply(_truth(300), SL.draw_profile(stats, np.random.default_rng(5), "wide"), np.random.default_rng(7))
    assert any(not np.array_equal(a[k], c[k]) for k in a)


def test_drift_magnitude():
    n = 90 * 24
    x = {"A|sat": np.zeros(n)}
    p = SL.SensorProfile(drift_rw_sd={"temp": 1.0, "value": 0, "flow": 0, "power": 0})
    end = [SL.apply(x, p, np.random.default_rng(s))["A|sat"][-1] for s in range(400)]
    assert abs(np.std(end) - 1.0) < 0.12
    p = SL.SensorProfile(drift_lin_sd={"temp": 0.5, "value": 0, "flow": 0, "power": 0})
    y = SL.apply(x, p, np.random.default_rng(2))["A|sat"]
    slope = np.polyfit(np.arange(n), y, 1)[0]
    assert abs(y[-1] - y[0] - slope * (n - 1)) < 1e-9  # exactly linear
    end = [SL.apply(x, p, np.random.default_rng(s))["A|sat"][-1] for s in range(400)]
    assert abs(np.std(end) - 0.5 * (n - 1) / n) < 0.06


def test_quantisation_and_timing():
    p = SL.SensorProfile(quant={"temp": 0.1, "value": 0, "flow": 0, "power": 0})
    x = {"A|sat": np.random.default_rng(0).uniform(10, 20, 1000)}
    y = SL.apply(x, p, np.random.default_rng(1))["A|sat"]
    assert np.allclose(y / 0.1, np.round(y / 0.1)) and np.abs(y - x["A|sat"]).max() <= 0.05 + 1e-9
    # jitter/lag: with a linear truth the interpolated value equals truth at shifted time
    p = SL.SensorProfile(lag_min=30.0)
    ramp = {"A|sat": np.arange(100.0)}
    o, f = SL.apply_with_flags(ramp, p, np.random.default_rng(4))
    assert abs(f["A|sat"]["lag_h"]) <= 0.5 and np.allclose(o["A|sat"][1:-2], ramp["A|sat"][1:-2] + f["A|sat"]["lag_h"])


def test_estimated_and_wide_profiles(stats):
    est = [SL.draw_profile(stats, np.random.default_rng(s), "estimated") for s in range(50)]
    P = stats["profile_inputs"]
    lo, hi = P["noise_sd"]["temp"]["ci95"]
    assert all(lo - 1e-12 <= e.noise_sd["temp"] <= hi + 1e-12 for e in est)
    assert all(e.dropout_frac < 1e-3 and e.stale_frac < 1e-3 and e.subhour_sd["temp"] == 0 for e in est)
    wide = [SL.draw_profile(stats, np.random.default_rng(s), "wide") for s in range(50)]
    assert np.median([w.noise_sd["temp"] for w in wide]) > 0.5 * np.median([e.noise_sd["temp"] for e in est])
    assert np.mean([w.dropout_frac for w in wide]) > 100 * np.mean([e.dropout_frac for e in est])
    assert all(w.assumed and "jitter_min" in " ".join(w.assumed) for w in wide)
    assert SL.draw_profile(stats, np.random.default_rng(0), "legacy").noise_sd["temp"] == 0.25
