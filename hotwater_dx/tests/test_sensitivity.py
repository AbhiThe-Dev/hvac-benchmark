import numpy as np

from hotwater_dx import checks as K
from hotwater_dx import engine as E
from hotwater_dx import sensitivity as SN
from hotwater_dx import stress as S


def toy():
    mean = np.array([[100.0, 0.0], [80.0, 2.0], [90.0, 1.0]])
    sd = np.array([[2.0, 0.5], [2.0, 0.5], [20.0, 5.0]])
    return E.Likelihoods(["a", "b", "other"], ["K05", "Q1"], mean, sd, {})


def test_prior_vec_shifts_prior_mass_to_the_named_cause():
    lk = toy()
    p = E.Engine(lk, False, prior_vec={"a": 0.9, "b": 0.1}).posterior()
    assert p[0] > 8 * p[1]
    assert abs(p.sum() - 1.0) < 1e-12


def test_default_prior_is_unchanged_by_the_new_option():
    lk = toy()
    assert np.allclose(E.Engine(lk, False).posterior(), E.Engine(lk, False, prior_vec=None).posterior())


def test_believed_minutes_change_selection_but_not_true_minutes():
    lk = toy()
    e = E.Engine(lk, False, assumed_minutes={"Q1": 1e4})
    assert e.next_check()[0] == "K05"                    # the engine believes the question is hugely expensive
    e2 = E.Engine(lk, False, assumed_minutes={"Q1": 1e4})
    e2.update("Q1", 0.0)
    assert e2.minutes == K.BY_ID["Q1"].do_min + E.travel("DOOR", "INT")   # but the clock charges the true minutes


def test_allowed_restricts_the_toolkit():
    e = E.Engine(toy(), False, allowed=frozenset({"Q1"}))
    assert e.available() == ["Q1"]


def test_tiers_are_cumulative_and_cover_every_engine_check():
    t = SN.tiers()
    assert all(a[1] < b[1] for a, b in zip(t, t[1:]))
    assert t[-1][1] == frozenset(E.ENGINE_CHECKS)


def test_matter_score_scales_with_effect_and_noise_floor():
    floor = {"top1": 0.0, "wrong_conf": 0.0, "minutes_rel": 0.0}
    d = {"d_top1": -0.08, "d_wrong_conf": 0.0, "d_minutes_rel": 0.0}
    assert SN._score(d, floor) == 2.0
    assert SN._score(d, {"top1": 0.04, "wrong_conf": 0.0, "minutes_rel": 0.0}) == 1.0     # noise floor doubles the bar


def test_config_hash_stable():
    assert SN.config_hash() == SN.config_hash()
