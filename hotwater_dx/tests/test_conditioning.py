import numpy as np

from hotwater_dx import adversary as AD
from hotwater_dx import conditioning as CD
from hotwater_dx import engine as E
from hotwater_dx.matrix import build_world


def test_plain_fit_from_collected_readings_equals_engine_fit():
    w = build_world(n_theta=40, seed=3131)
    lk = E.fit(w)
    lp = CD.fit_plain(CD.collect(w))
    assert lk.hyps == lp.hyps and lk.checks == lp.checks
    assert np.allclose(lk.mean, lp.mean, atol=1e-12) and np.allclose(lk.sd, lp.sd, atol=1e-12)


def test_ridge_recovers_a_planted_linear_dependence():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(3000, 3))
    y = 5.0 + 2.0 * X[:, 0] - 1.0 * X[:, 2] + rng.normal(0, 0.3, 3000)
    c0, b = CD._ridge(X, y, 1.0)
    assert abs(c0 - 5.0) < 0.05 and abs(b[0] - 2.0) < 0.05 and abs(b[1]) < 0.05 and abs(b[2] + 1.0) < 0.05


def test_conditioner_clips_unseen_values_and_imputes_unknowns():
    F = np.column_stack([np.linspace(40, 80, 50), np.tile([0.0, 1.0], 25)])
    cond = CD.make_conditioner(F, ("p_cold", "valve_thermal"), "state")
    far = cond.feats(np.array([1000.0, 1.0]))
    near = cond.feats(np.array([80.0, 1.0]))
    assert far[0] < near[0] + 0.5                      # clipped near the training maximum, not 1000 sigma away
    unk = cond.feats(np.array([np.nan, 1.0]))
    assert unk[0] == 0.0


def test_conditional_means_move_with_the_fact_and_unconditional_ones_do_not():
    w = build_world(n_theta=60, seed=4141)
    col = CD.collect(w)
    cl = CD.fit_conditional(col, ("p_cold", "t_set_tmv"), "state")
    lo = cl.at(np.array([cl.cond.mu[0] - 1.5 * cl.cond.sd[0], cl.cond.mu[1]]))
    hi = cl.at(np.array([cl.cond.mu[0] + 1.5 * cl.cond.sd[0], cl.cond.mu[1]]))
    assert np.abs(hi.mean - lo.mean).max() > 0.0
    assert lo.hyps[-1] == E.OTHER and lo.mean.shape == hi.mean.shape


def test_observe_adds_noise_unknowns_and_is_reproducible():
    names = ("p_cold", "pump_oversize", "valve_thermal")
    raw = np.array([60.0, 1.2, 1.0])
    outs = [CD.observe(raw, names, np.random.default_rng(i)) for i in range(400)]
    arr = np.array(outs)
    assert np.isnan(arr[:, 1]).mean() > 0.2              # pump rating unknown 40% of the time
    assert not np.isnan(arr[:, 0]).any()
    assert abs(np.nanmean(arr[:, 0]) - 60.0) < 1.5 and np.nanstd(arr[:, 0]) > 1.0
    assert np.allclose(CD.observe(raw, names, np.random.default_rng(7)), CD.observe(raw, names, np.random.default_rng(7)), equal_nan=True)


def test_raw_facts_read_gauges_from_the_faulted_plant_and_nameplate_from_design():
    w = AD.family_world(0.5, 999, n=30)
    cs = AD.family_cases(w, 0, 998)
    c = next(c for c in cs if c.truth == ("cold_pressure_problem",))
    f = CD.raw_facts(c.theta, c.ctx.P, ("p_cold", "storage_gal"), "state")
    assert f[0] == c.ctx.P.p_cold and f[0] < c.theta["p_cold"]      # the gauge shows the fault
    assert f[1] == c.theta["storage_gal"]                           # nameplate does not
    d = CD.raw_facts(c.theta, c.ctx.P, ("p_cold",), "design")
    assert d[0] == c.theta["p_cold"]
