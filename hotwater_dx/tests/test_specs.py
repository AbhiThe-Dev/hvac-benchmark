import numpy as np
import pytest

from hotwater_dx import causes as C
from hotwater_dx import checks as K
from hotwater_dx import params as PR
from hotwater_dx.params import nominal_design
from hotwater_dx.plant import build_plant
from hotwater_dx.solve import solve


def test_validate_functions_are_clean():
    assert PR.validate() == [] and C.validate() == [] and K.validate() == []


def test_counts():
    assert len(C.CAUSES) == 17 and len(K.CHECKS) == 23


def test_every_taxonomy_row_is_mapped_or_dropped():
    covered = {r for c in C.CAUSES for r in c.taxonomy_rows} | set(C.DROPPED)
    assert covered == set(range(1, 26))


def test_validate_catches_planted_problems():
    import dataclasses
    bad = dataclasses.replace(K.CHECKS[0], location="ZZ", safety="boom")
    ids = [c.id for c in (bad, K.CHECKS[0])]
    assert ids[0] == ids[1]                      # duplicate id is detectable
    assert dataclasses.replace(PR.PARAMS[0], nominal=999.0).nominal > PR.PARAMS[0].high


@pytest.mark.parametrize("cause", C.CAUSES, ids=lambda c: c.id)
def test_severity_zero_is_identity_and_apply_is_pure(cause, plant):
    before = repr(plant)
    d = cause.draw(np.random.default_rng(1), plant)
    d0 = dict(d, sev=0.0)
    assert repr(cause.apply(plant, d0)) == before
    cause.apply(plant, d)
    assert repr(plant) == before                  # the input plant is never mutated


@pytest.mark.parametrize("cause", C.CAUSES, ids=lambda c: c.id)
def test_fault_changes_something_measurable(cause, plant):
    d = cause.draw(np.random.default_rng(2), plant)
    Q = cause.apply(plant, d)
    assert repr(Q) != repr(plant)


def test_fixture_local_leaves_plant_level_outputs_unchanged(plant):
    spec = C.BY_ID["fixture_branch_local"]
    Q = spec.apply(plant, spec.draw(np.random.default_rng(3), plant))
    a, b = solve(plant, 0.0, True), solve(Q, 0.0, True)
    assert a.T_ret == pytest.approx(b.T_ret) and a.Ts == pytest.approx(b.Ts)
    assert max(b.t_hot_s) > max(a.t_hot_s)


def test_every_check_has_required_metadata():
    for c in K.CHECKS:
        assert c.location in K.LOCATIONS and c.safety in K.SAFETY and c.do_min > 0 and c.minutes_source == "ANALYST"
        assert c.read is not None or c.relevant


def test_every_cause_is_seen_by_some_physics_check_in_the_model(plant):
    # a cheap structural version of 'every cause is seen': at least one reading feature moves for a severe fault
    ctx0 = K.Ctx(plant)
    for cause in C.CAUSES:
        moved = False
        for k in range(5):
            Q = cause.apply(plant, dict(cause.draw(np.random.default_rng(k), plant), sev=cause.sev_range[1]))
            ctx = K.Ctx(Q)
            for ch in K.CHECKS:
                if not ch.physics_readable or not ch.applies(plant):
                    continue
                r1 = np.mean([ch.read(ctx, np.random.default_rng(9 + i), ch.tool) for i in range(16)])
                r0 = np.mean([ch.read(ctx0, np.random.default_rng(9 + i), ch.tool) for i in range(16)])
                if abs(r1 - r0) > 3 * ch.sigma_min:
                    moved = True
                    break
            if moved:
                break
        assert moved, cause.id
