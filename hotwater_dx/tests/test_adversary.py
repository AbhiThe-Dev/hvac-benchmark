import numpy as np

from hotwater_dx import adversary as AD
from hotwater_dx import checks as K
from hotwater_dx import engine as E
from hotwater_dx import stress as S
from hotwater_dx.matrix import build_world
from hotwater_dx.params import PARAMS
from hotwater_dx.sensitivity import PHYS


def test_ext_overrides_widen_the_fitted_range_inside_physical_bounds():
    ov = AD.ext_overrides(0.5)
    for p in PARAMS:
        if p.kind == "binary":
            assert p.name not in ov
            continue
        lo, hi = ov[p.name]
        assert PHYS[p.name][0] <= lo <= p.low and p.high <= hi <= PHYS[p.name][1]
    zero = AD.ext_overrides(0.0)
    assert all(abs(zero[p.name][0] - p.low) < 1e-9 and abs(zero[p.name][1] - p.high) < 1e-9 for p in PARAMS if p.kind != "binary" and p.low >= PHYS[p.name][0] and p.high <= PHYS[p.name][1])


def _planted(n=6000, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.random((n, 5))
    inside = (X[:, 0] < 0.3) & (X[:, 1] > 0.6)
    y = (rng.random(n) < np.where(inside, 0.6, 0.05)).astype(float)
    return X, y


def test_prim_recovers_a_planted_box_and_selection_is_compact():
    names = [f"f{i}" for i in range(5)]
    X, y = _planted()
    Xv, yv = _planted(4000, 1)
    tr = AD.prim(X, y, names, list(range(5)), 0.05, 0.05)
    sel = AD.select_box(tr["trajectory"], Xv, yv, names, 0.10, 0.01)
    restricted = set(sel["box"]["lo"]) | set(sel["box"]["hi"])
    assert {"f0", "f1"} <= restricted and len(restricted) <= 3
    assert sel["val_density"] > 0.4 and sel["val_support"] >= 0.10


def test_profile_flags_the_planted_feature_and_not_a_null_one():
    rng = np.random.default_rng(3)
    n_pl, per = 400, 10
    pid = np.repeat(np.arange(n_pl), per)
    theta = rng.random((n_pl, 3))
    X = theta[pid]
    y = (rng.random(len(pid)) < np.where(X[:, 0] > 0.8, 0.5, 0.05)).astype(float)
    rows = {r["feature"]: r for r in AD.profile(X, y, pid, names=("a", "b", "c"), perms=100, seed=1)}
    assert rows["a"]["matters"] and not rows["b"]["matters"] and not rows["c"]["matters"]


def test_tracked_cases_match_the_stress_test_cases():
    spec = S.WORLDS[0]
    w = build_world(n_theta=60, seed=4242)
    base = S.make_cases(w, 99)
    tracked = AD.make_cases_tracked(w, 99)
    assert [(t, th) for t, _, th in base] == [(t, th) for t, _, th, _ in tracked]
    assert all(a[1] is b[1] for a, b in zip(base, tracked) if len(a[0]) == 1)
    assert spec.name == "matched"


def test_garbage_source_defaults_to_the_engine_and_can_be_overridden(plant):
    mean = np.array([[100.0, 0.0], [80.0, 2.0], [90.0, 1.0]])
    sd = np.array([[2.0, 0.5], [2.0, 0.5], [20.0, 5.0]])
    lk = E.Likelihoods(["a", "b", "other"], ["K05", "Q1"], mean, sd, {})
    other = E.Likelihoods(["a", "b", "other"], ["K05", "Q1"], mean + 1000.0, sd, {})
    ctx = K.Ctx(plant)
    kw = dict(p_garbage=1.0, max_checks=1)
    r0 = E.run_case(lk, ctx, ("a",), np.random.default_rng(5), False, **kw)
    r1 = E.run_case(lk, ctx, ("a",), np.random.default_rng(5), False, garbage_lk=lk, **kw)
    r2 = E.run_case(lk, ctx, ("a",), np.random.default_rng(5), False, garbage_lk=other, **kw)
    assert (r0.top, r0.top_p) == (r1.top, r1.top_p)
    assert r2.top_p != r0.top_p or r2.top != r0.top


def test_boot_ci_brackets_the_estimate_and_collapses_on_constants():
    pid = np.repeat(np.arange(50), 4)
    ones = np.ones(len(pid))
    est, lo, hi = AD.boot_ci(pid, [(ones * 0.25, ones, 1.0)], 100, 0)
    assert est == lo == hi == 0.25
    rng = np.random.default_rng(0)
    x = (rng.random(len(pid)) < 0.3).astype(float)
    est, lo, hi = AD.boot_ci(pid, [(x, ones, 1.0)], 200, 0)
    assert lo <= est <= hi and 0.1 < est < 0.5


def test_family_cases_stay_inside_the_declared_family():
    w = AD.family_world(0.5, 777, n=40)
    cs = AD.family_cases(w, 0, 888)
    assert cs and all(len(c.truth) in (1, 2) for c in cs)
    ov = AD.ext_overrides(0.5)
    for c in cs:
        assert all(ov[n][0] - 1e-9 <= c.theta[n] <= ov[n][1] + 1e-9 for n in ov)
        assert OPS_RANGE_OK(c)


def OPS_RANGE_OK(c):
    o = AD.OPS
    return o["noise"][0] <= c.noise <= o["noise"][1] and o["p_skip"][0] <= c.p_skip <= o["p_skip"][1] and o["p_garbage"][0] <= c.p_garbage <= o["p_garbage"][1]
