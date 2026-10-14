"""Guards for two additive features: the severity mixture of the joint model (`JointSettings.low_mix`, off by default) and `Session.shortlist` (live_demo_bldg11/MIX_PROTOCOL.md). They check
the arithmetic and that the defaults are untouched. No test here reads a study result."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot.v1.engine import Session, make_case_v1  # noqa: E402
from docmismatch.troubleshoot.v2 import joint as Jn, world2 as W  # noqa: E402
from docmismatch.troubleshoot.v2.joint import JointModel, JointSettings  # noqa: E402

CASES = W.make_cases()
MIX = ((0.05, 0.25), (0.15, 0.25), (0.5, 0.25), (0.9, 0.25))


def cases3():
    return [CASES[("T3", r)] for r in (0, 1, 2)]


def test_defaults_are_untouched():
    js = JointSettings()
    assert js.low_mix == () and js.states == Jn.STATES and js.upstream == Jn.UPSTREAM
    assert np.allclose(js.state_prior, [0.97, 0.03 * 5 / 17, 0.03 * 12 / 17]) and np.allclose(js.affect, [0.0, 0.9, 0.5])
    assert Jn.base_state("low_static") == "low_static" and Jn.base_state("econ_fault") == "econ_fault"


def test_mixture_structure():
    js = JointSettings(low_mix=MIX)
    assert js.states == ("ok", "ahu_fan_off", "low_static", "low_static~1", "low_static~2", "low_static~3")
    assert js.state_prior.sum() == pytest.approx(1.0)
    assert np.allclose(js.state_prior[2:], 0.03 * (12 / 17) * 0.25) and js.state_prior[1] == pytest.approx(0.03 * 5 / 17)
    assert np.allclose(js.affect, [0.0, 0.9, 0.05, 0.15, 0.5, 0.9])
    assert js.p_complain.shape == (6,)
    with_extra = JointSettings(low_mix=MIX, extra_states=("econ_fault",), extra_affect={"econ_fault": 0.2}, extra_share={"econ_fault": 0.1})
    assert with_extra.state_prior.sum() == pytest.approx(1.0) and with_extra.states[-1] == "econ_fault" and len(with_extra.affect) == 7


@pytest.mark.parametrize("bad", [((0.5, 0.5), (0.1, 0.4)), ((0.0, 1.0),), ((0.5, 1.5), (0.1, -0.5)), ((1.2, 1.0),)])
def test_mixture_is_validated(bad):
    with pytest.raises(ValueError):
        JointSettings(low_mix=bad)


def test_one_level_mixture_is_the_default_model():
    a, b = JointModel(cases3(), JointSettings()), JointModel(cases3(), JointSettings(low_mix=((0.5, 1.0),)))
    for x, y in zip(a.marg0, b.marg0):
        assert np.array_equal(x, y)
    assert a.js.states == b.js.states


def test_the_mixture_reads_a_few_complaints_on_a_big_handler():
    """4 of 49 rooms complaining: under r_low = 0.5 every silent room counts against a shared fault; the mixture lets the data pick a small share."""
    cs = cases3()
    children = {cs[0].ahu: 49}
    d = JointModel(cs, JointSettings(), children=children).ahu_posterior_by_cause(JointModel(cs, JointSettings(), children=children).initial())[cs[0].ahu]
    mm = JointModel(cs, JointSettings(low_mix=MIX), children=children)
    m = mm.ahu_posterior_by_cause(mm.initial())[cs[0].ahu]
    assert d["low_static"] < 1e-9 and m["low_static"] > 3e-3
    assert abs(sum(m.values()) - 1.0) < 1e-9 and list(m) == ["ok", "ahu_fan_off", "low_static"]


def test_by_cause_posterior_follows_a_reading():
    cs = cases3()
    mm = JointModel(cs, JointSettings(low_mix=MIX), children={cs[0].ahu: 49})
    before = mm.ahu_posterior_by_cause(mm.initial())[cs[0].ahu]["low_static"]
    sess = Jn.JointSession(cs, JointSettings(low_mix=MIX))
    from docmismatch.troubleshoot.v1 import catalogue as K
    ck = K.BY_NAME["bas_static"]
    opt = next(o for o in sess.model.options(sess.state, sess.model.all_stats(sess.state), 0.95, 0.0) if o.kind == "ahu" and o.check.name == ck.name)
    after = sess.model.apply(sess.state, opt, True)
    assert sess.model.ahu_posterior_by_cause(after)[cs[0].ahu]["low_static"] > sess.model.ahu_posterior_by_cause(sess.state)[cs[0].ahu]["low_static"]
    assert before > 0


# ---------------------------------------------------------------------------------------------- the short list
def test_shortlist_is_ordered_and_changes_nothing():
    s = Session(CASES[("T3", 0)])
    n_log, elapsed, pending = len(s.log), s.elapsed, s.pending
    out = s.shortlist(2)
    assert len(out["candidates"]) == 2 and out["candidates"][0][1] >= out["candidates"][1][1]
    assert out["mass"] == pytest.approx(sum(p for _, p in out["candidates"])) and 0 < out["mass"] <= 1.0
    assert out["next"] is not None and out["next"].gain > 0 and out["next"].minutes > 0
    assert (len(s.log), s.elapsed, s.pending) == (n_log, elapsed, pending)
    assert s.shortlist(3)["candidates"][:2] == out["candidates"]


def test_shortlist_offers_a_check_even_when_the_tool_would_stop():
    bld = W.make_building2()
    case = make_case_v1(bld, "Room-0", W.TIER_ITEMS["T3"], settings=W.tool_settings(), context=W.tier_context("T3", 0), member_name="Room 0", min_rate=50.0)
    s = Session(case)
    assert s.recommend() is None                      # nothing clears a bar of 50 bits per minute
    assert s.shortlist(2)["next"] is not None         # but the best remaining check can still be named
