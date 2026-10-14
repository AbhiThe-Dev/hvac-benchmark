"""Tests for Addendum 42: more reliable answers than the tool assumes. No LLM. Simulation only."""
import numpy as np
import pytest

from docmismatch.troubleshoot.v1 import catalogue as K
from docmismatch.troubleshoot.v2 import study_joint as J
from docmismatch.troubleshoot.v2 import study_rel as R
from docmismatch.troubleshoot.v2 import study_tau as T
from docmismatch.troubleshoot.v2 import world2 as W

TIER, POL = R.PRIMARY_TIER, R.PRIMARY_POLICY


def test_registered_constants():
    assert R.B_LEVELS == (0.0, 0.5, 1.0) and R.TAU_GRID == (0.95, 0.90, 0.85, 0.80, 0.75) and R.N_CELLS == 9 and len(R.CELLS) == 9
    assert all(c.rel == "R0" for _, c in R.CELLS) and [i for i, _ in R.CELLS] == [0, 2, 4, 6, 8, 10, 12, 14, 16]
    assert (R.UNSAFE_MIN, R.IMPROVES_MIN, R.WORSE_MAX, R.NO_EFFECT_MIN) == (2, 8, 0, 8) and R.SEED == 42
    assert R.TIERS == T.TIERS and R.POLICIES == T.POLICIES


# ---------------------------------------------------------------------------------------------- the sharpening
def test_toward_certain_values():
    assert R.toward_certain(0.75, 0.5) == pytest.approx(0.875)
    assert R.toward_certain(0.92, 0.5) == pytest.approx(0.96)
    assert R.toward_certain(0.05, 0.5) == pytest.approx(0.025)
    assert R.toward_certain(0.5, 0.9) == 0.5
    assert R.toward_certain(0.75, 1.0) == 1.0 and R.toward_certain(0.2, 1.0) == 0.0
    assert R.toward_certain(0.75, 0.0) == 0.75


def test_toward_certain_is_the_mirror_of_degrade():
    # degrade moves toward 0.5; sharpening moves away from it, so degrading then sharpening never returns the original except at 0 and 1: just check the directions
    for p in (0.03, 0.2, 0.35, 0.6, 0.75, 0.92):
        d = K._toward_half(p, 0.25)
        s = R.toward_certain(p, 0.25)
        assert abs(d - 0.5) < abs(p - 0.5) < abs(s - 0.5)


def test_sharpen_identity_range_and_direction_for_every_check():
    for c in K.CATALOGUE:
        assert R.sharpen(c, 0.0) is c
        for b in (0.5, 1.0):
            s = R.sharpen(c, b)
            pairs = ([(c.detects[k], s.detects[k]) for k in c.detects] + [(c.bg, s.bg)]) if c.is_reading else [(c.v0.tpr, s.v0.tpr), (c.v0.fpr, s.v0.fpr)] + [(c.overrides[k], s.overrides[k]) for k in c.overrides]
            for p, q in pairs:
                assert 0.0 <= q <= 1.0
                assert (p > 0.5 and q >= p) or (p < 0.5 and q <= p) or (p == 0.5 and q == p)
                if b == 1.0 and p != 0.5:
                    assert q in (0.0, 1.0)


def test_sharpen_rejects_b_out_of_range():
    with pytest.raises(ValueError):
        R.sharpen(K.CATALOGUE[0], 1.5)
    with pytest.raises(ValueError):
        R.sharpen(K.CATALOGUE[0], -0.1)


def test_gates_g3_g4_pass():
    assert R.gate_g4()[0]
    assert R.gate_g3()[0]


# ---------------------------------------------------------------------------------------------- the oracle and the variants
def _event(idx=0, i=0):
    cell = J.all_cells()[idx]
    return W.draw_event(idx, i, cell.params(), W.make_cases(W.make_building2())), cell


def test_sharp_oracle_uses_the_sharpened_rates():
    ev, _ = _event()
    base = R.SharpOracle(ev, 0.0)
    sharp = R.SharpOracle(ev, 1.0)
    # for every room and check the sharpened hit probability is at least as far from 0.5 as the assumed one, on the same side
    for i in range(len(ev.rooms)):
        for name, ck in sharp.tc.items():
            p0 = base.p_room(i, name, f"VAV-{ev.rooms[i]}")
            p1 = sharp.p_room(i, name, f"VAV-{ev.rooms[i]}")
            assert (p0 >= 0.5 and p1 >= p0 - 1e-12) or (p0 < 0.5 and p1 <= p0 + 1e-12)


def test_b_zero_variant_equals_the_tau_study_variant():
    cell = J.all_cells()[0]
    wp, bld = cell.params(), W.make_building2()
    ca = W.make_cases(bld)
    events = [W.draw_event(0, i, wp, ca) for i in range(12)]
    for pol in R.POLICIES:
        mine = R.run_variant(TIER, 0.95, pol, events, wp, bld, 0.0)
        theirs = T.run_variant(TIER, 0.95, T.MIN_RATE, pol, events, wp, bld)
        for k in ("minutes", "checks", "acc", "wc"):
            assert np.array_equal(mine[k], theirs[k]), (pol, k)


def test_more_reliable_answers_do_not_hurt_accuracy_on_average():
    cell = J.all_cells()[0]
    wp, bld = cell.params(), W.make_building2()
    ca = W.make_cases(bld)
    events = [W.draw_event(0, i, wp, ca) for i in range(40)]
    a0 = R.run_variant(TIER, 0.95, POL, events, wp, bld, 0.0)["acc"].mean()
    a1 = R.run_variant(TIER, 0.95, POL, events, wp, bld, 1.0)["acc"].mean()
    assert a1 >= a0


def test_detail_records_truth_and_guess():
    cell = J.all_cells()[0]
    wp, bld = cell.params(), W.make_building2()
    ca = W.make_cases(bld)
    events = [W.draw_event(0, i, wp, ca) for i in range(8)]
    v = R.run_variant(TIER, 0.95, POL, events, wp, bld, 0.0, detail=True)
    assert len(v["detail"]) == int(sum(e.n for e in events))
    t, g, c = v["detail"][0]
    assert isinstance(t, tuple) and isinstance(g, tuple) and isinstance(c, bool)


def test_compute_cells_is_deterministic_and_worker_independent():
    cells = R.CELLS[:2]
    a = R.compute_cells(cells, n=8, workers=1)
    b = R.compute_cells(cells, n=8, workers=2)
    assert R.gate_g5(a, b)[0]


# ---------------------------------------------------------------------------------------------- labels and predictions on synthetic cells
def _analyses(spec):
    """spec(i) -> (label, safety, time, d_min) for the ('tau', b=1.0, TIER, POL, 0.85, all) comparison; every other comparison is NEITHER/NONE."""
    out = []
    for i, (idx, c) in enumerate(R.CELLS):
        cmp_ = {}
        for b in R.B_LEVELS:
            for tier in R.TIERS:
                for pol in R.POLICIES:
                    for tau in R.LEVELS:
                        cmp_[("tau", b, tier, pol, tau, "all")] = dict(label="NEITHER", safety="NONE", time="SAME", d_min=0.0)
                    if b:
                        for tau in R.TAU_GRID:
                            cmp_[("rel", b, tier, pol, tau, "all")] = dict(label="IMPROVES", safety="NONE", time="FASTER", d_min=-3.0, d_acc=0.1 * b, d_wc=-0.001, r_min=-0.1 * b)
        lab, saf, tim, dm = spec(i)
        cmp_[("tau", 1.0, TIER, POL, 0.85, "all")] = dict(label=lab, safety=saf, time=tim, d_min=dm)
        summ = {}
        for b in R.B_LEVELS:
            for tier in R.TIERS:
                for pol in R.POLICIES:
                    for tau in R.TAU_GRID:
                        for sub in R.SUBSETS:
                            summ[(b, tier, pol, tau, sub)] = dict(minutes=60.0 * (1 - 0.15 * b), checks=10.0, accuracy=0.7 + 0.12 * b, wrong_confident=0.02 - 0.01 * b, concluded=0.5)
        out.append(dict(idx=idx, cell=c, cmp=cmp_, sum=summ, counts={s: 100 for s in R.SUBSETS}))
    return out


IMP = ("IMPROVES", "NONE", "FASTER", -5.0)


def test_level_label_rules():
    assert R.level_label(_analyses(lambda i: IMP), 1.0, TIER, POL, 0.85) == "PASSES"
    assert R.level_label(_analyses(lambda i: ("IMPROVES", "REGRESSION", "FASTER", -5.0) if i < 2 else IMP), 1.0, TIER, POL, 0.85) == "UNSAFE"
    assert R.level_label(_analyses(lambda i: ("IMPROVES", "REGRESSION", "FASTER", -5.0) if i < 1 else IMP), 1.0, TIER, POL, 0.85) == "PASSES"
    assert R.level_label(_analyses(lambda i: ("NEITHER", "NONE", "SAME", 0.0) if i < 2 else IMP), 1.0, TIER, POL, 0.85) == "TRADES"      # 7 IMPROVES of 9: below the bar of 8
    assert R.level_label(_analyses(lambda i: ("WORSE", "NONE", "SLOWER", 5.0) if i < 1 else IMP), 1.0, TIER, POL, 0.85) == "TRADES"      # a single WORSE blocks a pass
    assert R.level_label(_analyses(lambda i: ("NEITHER", "NONE", "SAME", 0.0)), 1.0, TIER, POL, 0.85) == "NO EFFECT"


def test_label_needs_nine_cells():
    with pytest.raises(ValueError):
        R.level_label(_analyses(lambda i: IMP)[:4], 1.0, TIER, POL, 0.85)


def test_lowest_passing():
    a = _analyses(lambda i: IMP)
    assert R.lowest_passing(a, 1.0) == 0.85            # the only level that improves in this synthetic world
    assert R.lowest_passing(a, 0.5) is None


def test_predictions_on_a_synthetic_world():
    p = R.predictions(_analyses(lambda i: IMP))
    assert set(p) == {f"P{k}" for k in range(1, 9)}
    assert p["P1"][0] is True and p["P2"][0] is True and p["P3"][0] is True and p["P4"][0] is True and p["P5"][0] is True      # 0.70 -> 0.82 accuracy and 60 -> 51 minutes at b = 1.0 in the synthetic world
    assert p["P6"][0] is True                                                                                                  # no safety regression at b = 1.0, tau 0.85
    assert p["P7"][0] is False                                                                                                 # none at b = 0.5 either, so P7 (>= 2 expected) fails
    assert p["P8"][0] is False                                                                                                 # equal gains in the synthetic world


# ---------------------------------------------------------------------------------------------- tests added after a mutation check found the first versions too weak
def test_sharp_oracle_is_strictly_sharper_somewhere_and_a_strong_check_nears_certainty():
    ev, _ = _event()
    base, sharp = R.SharpOracle(ev, 0.0), R.SharpOracle(ev, 1.0)
    diffs = [(base.p_room(i, n, f"VAV-{ev.rooms[i]}"), sharp.p_room(i, n, f"VAV-{ev.rooms[i]}")) for i in range(len(ev.rooms)) for n in sharp.tc]
    assert sum(1 for p0, p1 in diffs if abs(p1 - p0) > 1e-9) > 20
    assert any(0.5 < p0 < 0.99 and p1 > 0.99 for p0, p1 in diffs)
    half = R.SharpOracle(ev, 0.5)
    assert any(p0 < half.p_room(i, n, f"VAV-{ev.rooms[i]}") < p1 for i in range(len(ev.rooms)) for n in sharp.tc
               for p0, p1 in [(base.p_room(i, n, f"VAV-{ev.rooms[i]}"), sharp.p_room(i, n, f"VAV-{ev.rooms[i]}"))] if p1 - p0 > 0.05)


def test_lowest_passing_is_the_lowest_of_several_passing_levels():
    a = _analyses(lambda i: IMP)
    for x in a:
        for tau in (0.80, 0.90):
            x["cmp"][("tau", 1.0, TIER, POL, tau, "all")] = dict(label="IMPROVES", safety="NONE", time="FASTER", d_min=-5.0)
    assert R.level_label(a, 1.0, TIER, POL, 0.90) == "PASSES" and R.level_label(a, 1.0, TIER, POL, 0.80) == "PASSES" and R.level_label(a, 1.0, TIER, POL, 0.85) == "PASSES"
    assert R.lowest_passing(a, 1.0) == 0.80


def test_p1_needs_a_rise_of_ten_points():
    a = _analyses(lambda i: IMP)
    for x in a:                                                    # accuracy 0.70 at b = 0, 0.77 at b = 1.0: a 7-point rise
        x["sum"][(1.0, TIER, POL, 0.95, "all")]["accuracy"] = 0.77
    assert R.predictions(a)["P1"][0] is False
    for x in a:
        x["sum"][(1.0, TIER, POL, 0.95, "all")]["accuracy"] = 0.81
    assert R.predictions(a)["P1"][0] is True
