"""Guards for graded numeric readings (v1/graded.py, off by default; live_demo_bldg11/READINGS_NOTES.md): the arithmetic, the agreement with the yes/no model, and that the default is untouched.
No test here reads a study result."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot.v1 import catalogue as K, data as D, engine as E, graded as G  # noqa: E402

EX1 = ROOT / "examples" / "troubleshoot_example" / "building_v1.json"
CTX = D.Context(reheat="yes", bas_access="yes", instrument="yes", occupant="yes")


def case(graded, tier="T2"):
    return E.make_case_v1(D.load_building_v1(EX1), "Room-204", tier, context=CTX, graded=graded)


@pytest.mark.parametrize("p,bg", [(0.92, 0.03), (0.75, 0.05), (0.5, 0.04), (0.2, 0.05), (0.05, 0.05), (0.02, 0.05)])
def test_the_shape_reproduces_the_catalogue_rate(p, bg):
    """P(z > 1) under the graded model is the rate the yes/no model uses: that is the only thing that ties it to the catalogue."""
    m, s = G.row_shape(p, bg)
    assert G.tail(m, s) == pytest.approx(p, abs=1e-6)
    assert (m == 0.0) == (p <= bg)
    zs = np.linspace(0.0, 1.0, 4001)
    inside = np.trapezoid(np.exp([G.log_density(z, m, s) for z in zs]), zs)            # the density over the 'normal' band is the rate the yes/no model gives 'normal'
    assert inside == pytest.approx(1.0 - p, abs=1e-5)


def test_a_reading_far_outside_is_stronger_evidence_than_one_just_outside():
    bg, row = 0.03, np.array([0.92, 0.03, 0.03])                                       # cause 0 is the one the check sees
    near, far, inside = (G.likelihood(z, row, bg) for z in (1.05, 3.0, 0.2))
    assert far[0] / far[1] > near[0] / near[1] > 1.0
    assert inside[0] / inside[1] < 1.0                                                  # a reading near the expected value points away from the seen cause
    assert G.likelihood(1.05, row, bg)[1] == pytest.approx(G.likelihood(1.05, row, bg)[2])   # two causes with the same rate stay tied


def test_a_check_that_does_not_see_the_cause_gives_no_graded_evidence():
    row = np.array([0.04, 0.04])
    like = G.likelihood(2.5, row, 0.04)
    assert like[0] == pytest.approx(like[1])


def test_z_needs_a_two_sided_band():
    assert G.z_of(110.0, (90.0, 110.0)) == pytest.approx(1.0) and G.z_of(100.0, (90.0, 110.0)) == 0.0
    assert G.z_of(5.0, (2.0, np.inf)) is None and G.z_of(5.0, None) is None and G.z_of(5.0, (3.0, 3.0)) is None


def test_default_is_byte_identical_to_the_yes_no_path():
    base, flagged = E.Session(case(False)), E.Session(case(False))
    base.report(reading=24.1, check="power_24vac")
    flagged.report("normal", check="power_24vac")
    a, b = base.posterior()[1], flagged.posterior()[1]
    assert np.array_equal(a, b)
    assert E.make_case_v1(D.load_building_v1(EX1), "Room-204", "T2").graded is False


def test_graded_session_uses_the_magnitude_and_the_default_ignores_it():
    far_s, near_s = E.Session(case(True)), E.Session(case(True))
    far_d, near_d = E.Session(case(False)), E.Session(case(False))
    for s, v in ((far_s, 0.0), (near_s, 21.5), (far_d, 0.0), (near_d, 21.5)):       # 24 V +/- 2: 21.5 is just outside (z 1.25), 0 V is far outside (z 12)
        s.report(reading=v, check="power_24vac")
    assert np.array_equal(far_d.posterior()[1], near_d.posterior()[1])                  # yes/no: both 'abnormal', identical
    assert not np.allclose(far_s.posterior()[1], near_s.posterior()[1])                 # graded: the far one says more
    causes, p_far = far_s.posterior()
    _, p_near = near_s.posterior()
    i = causes.index(("no_power",))
    assert p_far[i] > p_near[i] > 0.0                                                   # no_power is what 0 V points at, more so the further off it is


def test_one_sided_and_unjudged_readings_stay_yes_no_when_graded_is_on():
    s, d = E.Session(case(True)), E.Session(case(False))
    for x in (s, d):
        x.report(reading=0.5, check="control_signal")                                  # a minimum (> 2 V): no two-sided band
    assert np.array_equal(s.posterior()[1], d.posterior()[1])
    s.report("abnormal", check="bas_static")                                           # no number: yes/no
    d.report("abnormal", check="bas_static")
    assert np.array_equal(s.posterior()[1], d.posterior()[1])
