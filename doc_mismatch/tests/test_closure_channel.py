"""Guards for the set-level conservation channel (PREREGISTRATION_DR.md Addendum 9): does candidate owner `o`'s own
measured flow/heat still balance once member `m` is added to `o`'s other TRUE members? `loop_branch` only."""
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.evidence import closure_channel  # noqa: E402
from docmismatch.active.model import fit_slot_models  # noqa: E402

N = 24


def _series(val: float) -> np.ndarray:
    return np.full(N, val)


def _base(edges: list[tuple[str, str]]):
    return SimpleNamespace(slot_edges={"loop_branch": edges})


def _loop_branch_world():
    """L1 truly supplies B1 (flow=6) and B2 (flow=4), t_sup/t_ret = 60/50 -> heat = 10*CP_WATER*10.
    B1 and B2's own heat (t_in/t_out = 60/50) sum to exactly L1's heat -- a physically closed set.
    L2 truly supplies only B3 (flow=2.5, t_in/t_out = 55/45); L2 itself flow=3, t_sup/t_ret=55/45."""
    ev = {}
    ev["L1|flow"], ev["L1|t_sup"], ev["L1|t_ret"] = _series(10.0), _series(60.0), _series(50.0)
    ev["B1|flow"], ev["B1|t_in"], ev["B1|t_out"] = _series(6.0), _series(60.0), _series(50.0)
    ev["B2|flow"], ev["B2|t_in"], ev["B2|t_out"] = _series(4.0), _series(60.0), _series(50.0)
    ev["L2|flow"], ev["L2|t_sup"], ev["L2|t_ret"] = _series(3.0), _series(55.0), _series(45.0)
    ev["B3|flow"], ev["B3|t_in"], ev["B3|t_out"] = _series(2.5), _series(55.0), _series(45.0)
    base = _base([("L1", "B1"), ("L1", "B2"), ("L2", "B3")])
    return base, ev


# ---------------------------------------------------------------------------------------------- scope / masking
def test_nan_for_every_slot_other_than_loop_branch():
    base, ev = _loop_branch_world()
    assert np.isnan(closure_channel(base, ev, "ahu_vav", "L1", "B1", slice(None)))
    assert np.isnan(closure_channel(base, ev, "vav_zone", "L1", "B1", slice(None)))


def test_masked_nan_when_owner_flow_is_constant_within_noise():
    base, ev = _loop_branch_world()   # L1|flow is exactly constant -> not "informative" under the default gate
    assert np.isnan(closure_channel(base, ev, "loop_branch", "L1", "B1", slice(None)))   # mask_uninformative=True (default)


# ---------------------------------------------------------------------------------------------- physics correctness (masking bypassed to isolate the computation)
def test_true_owner_with_its_true_set_gives_a_near_zero_residual():
    base, ev = _loop_branch_world()
    r = closure_channel(base, ev, "loop_branch", "L1", "B1", slice(None), mask_uninformative=False)
    assert r == pytest.approx(0.0, abs=1e-6)


def test_wrong_owner_forcing_the_member_in_breaks_its_balance():
    base, ev = _loop_branch_world()
    # L2 truly supplies only B3; testing whether L2 ALSO supplies B1 (it does not) should badly break L2's balance
    r_wrong = closure_channel(base, ev, "loop_branch", "L2", "B1", slice(None), mask_uninformative=False)
    r_true = closure_channel(base, ev, "loop_branch", "L1", "B1", slice(None), mask_uninformative=False)
    assert r_wrong > r_true + 0.5


def test_owner_with_no_other_true_members_still_computable():
    """A candidate with zero other true members: `others` is empty, `closure_residual` runs on `[m]` alone --
    must not raise, and must return a finite, non-negative relative mismatch."""
    base, ev = _loop_branch_world()
    # L3 has no true members at all -- absent from base.slot_edges entirely
    ev["L3|flow"], ev["L3|t_sup"], ev["L3|t_ret"] = _series(1.0), _series(90.0), _series(20.0)
    r = closure_channel(base, ev, "loop_branch", "L3", "B1", slice(None), mask_uninformative=False)
    assert np.isfinite(r) and r >= 0.0


# ---------------------------------------------------------------------------------------------- fit_slot_models: opt-in, not default
def test_channel_3_is_opt_in_only_not_fit_by_default():
    """Addendum 9's frozen result is NEGATIVE (does not improve loop_branch resolution) -- so, unlike this
    codebase's other opt-in mechanisms which are toggled by a runtime kwarg passed through, this one must stay
    OUT of what any existing caller gets by not asking, not just "off by default in theory"."""
    from docmismatch.dr.pools import load_pool
    p = load_pool("vav_2ahu_2loops", 0, "legacy")
    default = fit_slot_models([p], "loop_branch", True)
    assert set(default) == {0, 1, 2}
    opt_in = fit_slot_models([p], "loop_branch", True, max_channel=3)
    assert set(opt_in) == {0, 1, 2, 3}
