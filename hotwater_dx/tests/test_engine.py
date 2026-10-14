import numpy as np
import pytest

from hotwater_dx import checks as K
from hotwater_dx import engine as E
from hotwater_dx import matrix as MX


def toy(sep=True):
    hyps = ["a", "b", "other"]
    checks = ["K05", "Q1", "K13", "K12"]
    mean = np.array([[100.0, 0.0, 1.0, 1.0], [100.0 if not sep else 80.0, 2.0, 1.0, 1.0], [90.0, 1.0, 1.0, 1.0]])
    sd = np.array([[2.0, 0.5, 0.1, 0.1], [2.0, 0.5, 0.1, 0.1], [20.0, 5.0, 0.1, 0.1]])
    return E.Likelihoods(hyps, checks, mean, sd, {"K12": True, "K13": False})


def eng(lk=None, thermal=False, **kw):
    return E.Engine(lk or toy(), thermal, **kw)


def test_prior_sums_to_one_and_respects_masses():
    p = eng().posterior()
    assert p.sum() == pytest.approx(1.0)
    cfg = E.ENGINE_CONFIG
    # no pair hypotheses in the toy: the pair mass is dropped and the rest renormalised
    assert p[2] == pytest.approx(cfg["PRIOR_OTHER"] / (cfg["PRIOR_OTHER"] + cfg["PRIOR_SINGLE"]))
    assert p[0] == pytest.approx(p[1])


def test_update_matches_manual_bayes():
    e = eng(toy())
    p0 = e.posterior()
    e.update("K05", 80.0)
    lk = e.lk
    like = np.exp(-0.5 * ((80.0 - lk.mean[:, 0]) / lk.sd[:, 0]) ** 2) / lk.sd[:, 0]
    want = p0 * like
    want /= want.sum()
    assert e.posterior() == pytest.approx(want)


def test_gain_is_zero_for_an_uninformative_check_and_positive_for_a_separating_one():
    e = eng(toy())
    assert e.gain("K13") < 1e-3                                       # identical likelihoods across hypotheses
    assert e.gain("K05") > 0.5
    ent = -(e.posterior() * np.log2(e.posterior())).sum()
    assert e.gain("K05") <= ent + 1e-6


def test_selection_trades_gain_against_minutes():
    e = eng(toy())
    cid, g, mins = e.next_check()
    assert cid in ("K05", "Q1")
    # a question costs 1 minute, a return-temperature reading costs more; both separate a from b, so the cheap one wins on gain per minute
    assert e.gain("Q1") / e.check_minutes("Q1") >= e.gain("K05") / e.check_minutes("K05") or cid == "K05"


def test_travel_cost_depends_on_where_the_technician_is():
    e = eng(toy())
    e.location = "MR"
    far = e.check_minutes("K16")      # fixture check
    e.location = "FX"
    assert e.check_minutes("K16") < far


def test_valve_type_filters_applicable_checks():
    assert "K12" not in eng(toy(), thermal=False).available() and "K13" in eng(toy(), thermal=False).available()
    assert "K13" not in eng(toy(), thermal=True).available() and "K12" in eng(toy(), thermal=True).available()


def test_done_and_unavailable_checks_are_not_offered_again():
    e = eng(toy())
    e.update("K05", 100.0)
    e.mark_unavailable("Q1")
    assert "K05" not in e.available() and "Q1" not in e.available()
    assert e.minutes > 0


def test_stop_when_confident():
    e = eng(toy(), tau=0.9)
    for _ in range(3):
        e.update("K05", 80.0)
        e.done.clear()
    assert e.top()[0] == "b" and e.stop_reason() == "confident"


def test_marginal_sums_pair_hypotheses():
    lk = toy()
    lk.hyps[2] = "a+b"
    e = eng(lk)
    m = e.marginal()
    assert m["a"] > e.posterior()[0] - 1e-12 and m["b"] > e.posterior()[1] - 1e-12


def test_isolation_checks_can_be_excluded():
    lk = E.Likelihoods(["a", "other"], ["K17", "K05"], np.zeros((2, 2)), np.ones((2, 2)), {})
    assert "K17" in E.Engine(lk, False).available()
    assert "K17" not in E.Engine(lk, False, allow_isolation=False).available()


@pytest.fixture(scope="module")
def small_fit():
    saved = dict(MX.THRESHOLDS)
    MX.THRESHOLDS.update(MIN_APPLICABLE=8, GATE_MIN=8)
    w = MX.build_world(n_theta=50, seed=5)
    lk = E.fit(w)
    yield w, lk
    MX.THRESHOLDS.clear()
    MX.THRESHOLDS.update(saved)


def test_fit_shapes_and_other_is_broad(small_fit):
    w, lk = small_fit
    assert lk.mean.shape == lk.sd.shape == (len(lk.hyps), len(lk.checks)) and lk.hyps[-1] == "other"
    assert (lk.sd[-1] >= lk.sd[:-1].min(axis=0) - 1e-12).all()
    assert len(lk.hyps) == 17 + 11 + 1


def test_a_dead_pump_is_found_quickly_and_reproducibly(small_fit):
    w, lk = small_fit
    j = int(np.where(w.cause_gated["pump_failed"])[0][0])
    a = E.run_case(lk, w.cause_ctx["pump_failed"][j], ("pump_failed",), np.random.default_rng(1), w.plants[j].thermal)
    b = E.run_case(lk, w.cause_ctx["pump_failed"][j], ("pump_failed",), np.random.default_rng(1), w.plants[j].thermal)
    assert (a.top, a.checks) == (b.top, b.checks) and a.hit and a.n_checks <= 8


def test_info_selection_needs_no_more_minutes_than_random_on_average(small_fit):
    w, lk = small_fit
    rng = np.random.default_rng(0)
    cases = []
    for cid in ("pump_failed", "crossover", "balancing_valve_misset", "tmv_starved_fouled", "heater_setpoint_low"):
        for j in np.where(w.cause_gated[cid])[0][:6]:
            cases.append((cid, int(j)))
    def mins(sel):
        return np.mean([E.run_case(lk, w.cause_ctx[c][j], (c,), np.random.default_rng(j), w.plants[j].thermal, selection=sel).minutes for c, j in cases])
    assert mins("info") <= mins("random") * 1.05
