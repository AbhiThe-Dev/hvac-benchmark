"""Guards for the fan-off severity mixture of the joint model (`JointSettings.fan_mix`, off by default; live_demo_bldg11/FANMIX_NOTES.md). Arithmetic and defaults only: no test here reads a study result."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot.v2 import joint as Jn, world2 as W  # noqa: E402
from docmismatch.troubleshoot.v2.joint import JointModel, JointSettings  # noqa: E402

CASES = W.make_cases()
MIX = ((0.05, 0.25), (0.15, 0.25), (0.5, 0.25), (0.9, 0.25))


def cases3():
    return [CASES[("T3", r)] for r in (0, 1, 2)]


def test_default_is_untouched():
    js = JointSettings()
    assert js.fan_mix == () and js.states == Jn.STATES
    assert np.array_equal(js.state_prior, JointSettings(low_mix=()).state_prior) and np.allclose(js.affect, [0.0, 0.9, 0.5])
    lm = JointSettings(low_mix=MIX)
    assert lm.states == ("ok", "ahu_fan_off", "low_static", "low_static~1", "low_static~2", "low_static~3")        # the shipped pilot / demo default is what it was


def test_fan_mixture_structure():
    js = JointSettings(low_mix=MIX, fan_mix=MIX)
    assert js.states == ("ok", "ahu_fan_off", "low_static", "low_static~1", "low_static~2", "low_static~3", "ahu_fan_off~1", "ahu_fan_off~2", "ahu_fan_off~3")
    assert js.state_prior.sum() == pytest.approx(1.0)
    assert js.state_prior[1] == pytest.approx(0.03 * 5 / 17 * 0.25) and np.allclose(js.state_prior[6:], 0.03 * 5 / 17 * 0.25) and np.allclose(js.state_prior[2:6], 0.03 * 12 / 17 * 0.25)
    assert np.allclose(js.affect, [0.0, 0.05, 0.05, 0.15, 0.5, 0.9, 0.15, 0.5, 0.9]) and js.p_complain.shape == (9,)
    only_fan = JointSettings(fan_mix=MIX)
    assert only_fan.states == ("ok", "ahu_fan_off", "low_static", "ahu_fan_off~1", "ahu_fan_off~2", "ahu_fan_off~3") and np.allclose(only_fan.affect, [0.0, 0.05, 0.5, 0.15, 0.5, 0.9])
    assert only_fan.state_prior.sum() == pytest.approx(1.0)
    extra = JointSettings(low_mix=MIX, fan_mix=MIX, extra_states=("econ_fault",), extra_affect={"econ_fault": 0.2}, extra_share={"econ_fault": 0.1})
    assert extra.state_prior.sum() == pytest.approx(1.0) and extra.states[-1] == "econ_fault" and len(extra.affect) == len(extra.states) == len(extra.state_prior) == 10


@pytest.mark.parametrize("bad", [((0.5, 0.5), (0.1, 0.4)), ((0.0, 1.0),), ((0.5, 1.5), (0.1, -0.5)), ((1.2, 1.0),)])
def test_fan_mixture_is_validated(bad):
    with pytest.raises(ValueError):
        JointSettings(fan_mix=bad)


def test_one_level_fan_mixture_is_the_default_model():
    for low in ((), MIX):
        a, b = JointModel(cases3(), JointSettings(low_mix=low)), JointModel(cases3(), JointSettings(low_mix=low, fan_mix=((0.9, 1.0),)))
        for x, y in zip(a.marg0, b.marg0):
            assert np.array_equal(x, y)
        assert a.js.states == b.js.states


def test_a_few_complaints_on_a_big_handler_can_now_be_fan_off():
    """4 of 49 rooms complaining: under r_fan = 0.9 a fan-off handler is impossible (every silent room counts against it); the mixture lets the data pick a small share."""
    cs = cases3()
    children = {cs[0].ahu: 49}
    d = JointModel(cs, JointSettings(low_mix=MIX), children=children)
    m = JointModel(cs, JointSettings(low_mix=MIX, fan_mix=MIX), children=children)
    pd, pm = d.ahu_posterior_by_cause(d.initial())[cs[0].ahu], m.ahu_posterior_by_cause(m.initial())[cs[0].ahu]
    assert pd["ahu_fan_off"] < 1e-30 and pm["ahu_fan_off"] > 3e-3
    assert abs(sum(pm.values()) - 1.0) < 1e-9 and list(pm) == ["ok", "ahu_fan_off", "low_static"]
