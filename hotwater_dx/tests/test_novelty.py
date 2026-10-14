import numpy as np

from hotwater_dx import novelty as NV
from hotwater_dx.engine import OTHER, Likelihoods
from hotwater_dx.solve import solve


def test_novel_causes_are_neutral_at_zero_severity_and_move_the_outlet(plant):
    for spec in NV.NOVEL:
        d = spec.draw(np.random.default_rng(1), plant)
        same = spec.apply(plant, dict(d, sev=0.0))
        assert solve(same, 1.0).Ts == solve(plant, 1.0).Ts
    unreg = NV.NOVEL[1].apply(plant, {"mode": "supplies_reversed", "sev": 1.0, "f": 0.05})
    assert solve(unreg, 1.0).Ts < solve(plant, 1.0).Ts - 5.0 and solve(unreg, 0.0).Ts < solve(plant, 0.0).Ts - 5.0


def test_below_min_flow_sags_the_outlet_at_idle_and_not_at_a_flow_above_the_minimum(plant):
    low = NV.NOVEL[0].apply(plant, {"mode": "low_flow", "sev": 1.0, "ratio": 3.0})
    idle_h, idle_l = solve(plant, 0.0), solve(low, 0.0)
    assert idle_l.Ts < idle_h.Ts - 3.0
    pk_h, pk_l = solve(plant, 1.0), solve(low, 1.0)
    assert pk_l.Qs > low.tmv_min_flow and abs(pk_l.Ts - pk_h.Ts) < 1e-6


def _lk():
    mean = np.array([[1.0, 0.0], [2.0, 1.0], [3.0, 2.0], [2.5, 1.5], [2.0, 1.0]])
    sd = np.ones_like(mean)
    return Likelihoods(["a", "b", "a+b", "c", OTHER], ["K05", "Q1"], mean, sd, {})


def test_drop_cause_removes_the_cause_and_its_pairs_and_recomputes_other():
    lk = _lk()
    d = NV.drop_cause(lk, "a", 1.5)
    assert d.hyps == ["b", "c", OTHER]
    assert np.allclose(d.mean[-1], d.mean[:-1].mean(axis=0))
    assert np.all(d.sd[-1] > d.sd[:-1].max())
    w = NV.with_other(lk, 3.0)
    assert w.hyps == lk.hyps and np.all(w.sd[-1] > NV.with_other(lk, 1.5).sd[-1])


class R:
    def __init__(self, top, reason):
        self.top, self.reason, self.minutes = top, reason, 10.0


def test_outcome_rates_separate_wrong_family_right_family_other_and_abstain():
    res = [R("pump_failed", "confident"), R("tmv_setpoint_wrong", "confident"), R(OTHER, "confident"), R("crossover", "not_worth_it"), R("tmv_starved_fouled+crossover", "confident")]
    o = NV.outcome_rates(res, "B")
    assert abs(o["wrong_family"] - 1 / 5) < 1e-9 and abs(o["family_ok"] - 2 / 5) < 1e-9 and abs(o["conf_other"] - 1 / 5) < 1e-9 and abs(o["abstain"] - 1 / 5) < 1e-9


def test_variants_resolve_and_a_plain_has_no_soft_evidence():
    for v in NV.CFG["VARIANTS"]:
        cfg, mult = NV.variant_config(v)
        assert mult in (1.5, 3.0)
    assert "q_eps" not in NV.variant_config("A_plain")[0] and NV.variant_config("S30_B")[0]["q_eps"] == 0.30
    assert NV.variant_config("S30_B_po30")[0]["prior_other"] == 0.30
