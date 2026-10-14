"""Tests for Addendum 41: does lowering the conclusion threshold `tau` cut checks without costing accuracy or safety? No LLM. Simulation only."""
import dataclasses

import numpy as np
import pytest

from docmismatch.troubleshoot.v2 import study_joint as J
from docmismatch.troubleshoot.v2 import study_minrate as MR
from docmismatch.troubleshoot.v2 import study_tau as T
from docmismatch.troubleshoot.v2 import world2 as W

TIER, POL = T.PRIMARY_TIER, T.PRIMARY_POLICY


# ---------------------------------------------------------------------------------------------- frozen constants
def test_registered_constants():
    assert T.TAU_GRID == (0.95, 0.90, 0.85, 0.80, 0.75) and T.BASE_TAU == 0.95 and T.LEVELS == (0.90, 0.85, 0.80, 0.75)
    assert T.MIN_RATE == 0.02 and T.TIERS == ("T3-noattr", "T3") and T.POLICIES == ("tool_joint", "tool_ticket_memo2")
    assert (T.PRIMARY_TIER, T.PRIMARY_POLICY) == ("T3-noattr", "tool_joint")
    assert (T.IMPROVES_CELLS, T.WORSE_MAX, T.UNSAFE_CELLS_MIN, T.NO_EFFECT_CELLS) == (15, 1, 3, 15)
    assert (T.R1_IMPROVES_MIN, T.R1_WORSE_MAX, T.R1_SAFETY_MAX) == (8, 0, 1) and T.N_CELLS == 18
    assert len(J.all_cells()) == 18 and sum(c.rel == "R1" for c in J.all_cells()) == 9


# ---------------------------------------------------------------------------------------------- the case variants
def test_cases_with_changes_only_tau():
    base, low = T.cases_with(TIER, 0.95), T.cases_with(TIER, 0.80)
    r = 3
    assert base[r].settings.tau == 0.95 and low[r].settings.tau == 0.80
    assert base[r].min_rate == low[r].min_rate == T.MIN_RATE
    assert dataclasses.replace(low[r].settings, tau=0.95) == base[r].settings
    assert base[r].doc == low[r].doc and base[r].candidates == low[r].candidates and base[r].checks == low[r].checks


def test_tau_is_what_the_session_uses():
    from docmismatch.troubleshoot.v2.joint import JointSession
    low = T.cases_with(TIER, 0.75)
    assert JointSession([low[0]]).tau == 0.75
    assert JointSession([T.cases_with(TIER, 0.95)[0]]).tau == 0.95


def test_baseline_variant_is_identical_to_the_existing_minrate_study():
    cell = J.all_cells()[0]
    wp, bld = cell.params(), W.make_building2()
    cases_all = W.make_cases(bld)
    events = [W.draw_event(0, i, wp, cases_all) for i in range(15)]
    mine = T.run_variant(T.E.EXT_ARM, T.BASE_TAU, T.MIN_RATE, "tool_ticket_memo2", events, wp, bld)
    old = MR.run_variant_events(T.E.EXT_ARM, T.MIN_RATE, events, wp, bld)
    for k in ("minutes", "checks", "acc", "wc"):
        assert np.array_equal(mine[k], old[k]), k


def test_lowering_tau_does_not_add_checks_on_average():
    cell = J.all_cells()[0]
    wp, bld = cell.params(), W.make_building2()
    cases_all = W.make_cases(bld)
    events = [W.draw_event(0, i, wp, cases_all) for i in range(30)]
    hi = T.run_variant(TIER, 0.95, T.MIN_RATE, POL, events, wp, bld)
    lo = T.run_variant(TIER, 0.75, T.MIN_RATE, POL, events, wp, bld)
    assert lo["checks"].mean() <= hi["checks"].mean() and lo["minutes"].mean() <= hi["minutes"].mean()


def test_compute_cells_is_deterministic_and_worker_independent():
    cells = list(enumerate(J.all_cells()))[:2]
    a = T.compute_cells(cells, n=12, workers=1)
    b = T.compute_cells(cells, n=12, workers=2)
    ok, _ = T.gate_g6(a, b)
    assert ok


# ---------------------------------------------------------------------------------------------- level labels on synthetic cells
def _analyses(spec):
    """spec(cell) -> (label, safety, time, d_min) for the (TIER, POL, tau 0.80, all) comparison; every other level is NEITHER."""
    out = []
    for i, c in enumerate(J.all_cells()):
        lab, saf, tim, dm = spec(c, i)
        cmp_ = {(t, p, tau, "all"): dict(label="NEITHER", safety="NONE", time="SAME", d_min=0.0) for t in T.TIERS for p in T.POLICIES for tau in T.LEVELS}
        cmp_[(TIER, POL, 0.80, "all")] = dict(label=lab, safety=saf, time=tim, d_min=dm)
        summ = {(t, p, tau, "all"): dict(minutes=50.0, checks=8.0, accuracy=0.8, wrong_confident=0.0, concluded=0.5) for t in T.TIERS for p in T.POLICIES for tau in T.TAU_GRID}
        out.append(dict(idx=i, cell=c, cmp=cmp_, sum=summ))
    return out


IMP = ("IMPROVES", "NONE", "FASTER", -5.0)


def test_all_improve_passes():
    assert T.level_label(_analyses(lambda c, i: IMP), TIER, POL, 0.80) == "PASSES"


def test_three_safety_regressions_anywhere_is_unsafe_even_if_everything_improves():
    a = _analyses(lambda c, i: ("IMPROVES", "REGRESSION", "FASTER", -5.0) if i < 3 else IMP)
    assert T.level_label(a, TIER, POL, 0.80) == "UNSAFE"


def test_two_safety_regressions_in_r1_cells_fails_the_stress_check_only():
    r1 = [i for i, c in enumerate(J.all_cells()) if c.rel == "R1"][:2]
    a = _analyses(lambda c, i: ("IMPROVES", "REGRESSION", "FASTER", -5.0) if i in r1 else IMP)
    assert T.level_label(a, TIER, POL, 0.80) == "PASSES ONLY WHERE CHECKS ARE AS RELIABLE AS ASSUMED"


def test_two_safety_regressions_in_r0_cells_still_passes():
    r0 = [i for i, c in enumerate(J.all_cells()) if c.rel == "R0"][:2]
    a = _analyses(lambda c, i: ("IMPROVES", "REGRESSION", "FASTER", -5.0) if i in r0 else IMP)
    assert T.level_label(a, TIER, POL, 0.80) == "PASSES"


def test_improving_in_only_seven_r1_cells_fails_the_stress_check():
    r1 = [i for i, c in enumerate(J.all_cells()) if c.rel == "R1"]
    neither = ("NEITHER", "NONE", "SAME", 0.0)
    eight = _analyses(lambda c, i: neither if i == r1[0] else IMP)           # 17 IMPROVES overall, 8 of the 9 R1 cells: passes
    seven = _analyses(lambda c, i: neither if i in r1[:2] else IMP)          # 16 IMPROVES overall, 7 of the 9 R1 cells: fails the stress check
    assert T.level_label(eight, TIER, POL, 0.80) == "PASSES"
    assert T.level_label(seven, TIER, POL, 0.80) == "PASSES ONLY WHERE CHECKS ARE AS RELIABLE AS ASSUMED"


def test_a_worse_cell_beyond_the_bar_blocks_a_pass():
    a = _analyses(lambda c, i: ("WORSE", "NONE", "SLOWER", 5.0) if i < 2 else IMP)
    assert T.level_label(a, TIER, POL, 0.80) == "TRADES"
    b = _analyses(lambda c, i: ("WORSE", "NONE", "SLOWER", 5.0) if i < 1 else IMP)
    assert T.level_label(b, TIER, POL, 0.80) == "PASSES"


def test_no_effect_and_trades():
    no = _analyses(lambda c, i: ("NEITHER", "NONE", "SAME", 0.0) if i < 15 else IMP)
    assert T.level_label(no, TIER, POL, 0.80) == "NO EFFECT"
    tr = _analyses(lambda c, i: IMP if i < 10 else ("TRADE", "NONE", "FASTER", -5.0))
    assert T.level_label(tr, TIER, POL, 0.80) == "TRADES"


def test_label_needs_all_18_cells():
    with pytest.raises(ValueError):
        T.level_label(_analyses(lambda c, i: IMP)[:5], TIER, POL, 0.80)


# ---------------------------------------------------------------------------------------------- overall outcome and predictions
def _labels(**by_tau):
    base = {(t, p, tau): "TRADES" for t in T.TIERS for p in T.POLICIES for tau in T.LEVELS}
    for tau, lab in by_tau.items():
        base[(TIER, POL, float(tau.replace("t", "")) / 100)] = lab
    return base


def test_outcome_rules():
    assert T.outcome(_labels(t90="PASSES", t85="TRADES")) == ("A LOWER THRESHOLD IS SAFE TO OFFER", 0.90)
    assert T.outcome(_labels(t85="PASSES", t80="PASSES")) == ("A LOWER THRESHOLD IS SAFE TO OFFER", 0.80)       # the lowest passing level
    assert T.outcome(_labels(t80="PASSES ONLY WHERE CHECKS ARE AS RELIABLE AS ASSUMED"))[0] == "ONLY WHERE CHECKS ARE AS RELIABLE AS ASSUMED"
    assert T.outcome(_labels(t85="PASSES ONLY WHERE CHECKS ARE AS RELIABLE AS ASSUMED", t90="PASSES"))[1] == 0.90
    assert T.outcome(_labels()) == ("NO LEVEL BELOW 0.95 PASSES", None)
    # the routine and T3 are reported, not decisive
    other = _labels()
    other[("T3", "tool_ticket_memo2", 0.80)] = "PASSES"
    assert T.outcome(other)[0] == "NO LEVEL BELOW 0.95 PASSES"


def test_predictions_on_a_synthetic_world():
    a = _analyses(lambda c, i: IMP)
    p = T.predictions(a)
    assert set(p) == {"P1", "P2", "P3", "P4", "P5", "P6", "P8"}
    assert p["P1"][0] is True and p["P2"][0] is True          # 0.90 is NEITHER everywhere here; 0.80 FASTER in 18
    assert p["P3"][0] is False and p["P4"][0] is False        # 0.80 PASSES here, so P3 and P4 fail
    assert p["P6"][0] is True                                 # no regressions at all


def test_p5_uses_the_cell_mean_wrong_and_confident_rise():
    a = _analyses(lambda c, i: IMP)
    for x in a:
        x["sum"][(TIER, POL, 0.75, "all")]["wrong_confident"] = 0.03
    assert T.predictions(a)["P5"][0] is True
    for x in a:
        x["sum"][(TIER, POL, 0.75, "all")]["wrong_confident"] = 0.01
    assert T.predictions(a)["P5"][0] is False


# ---------------------------------------------------------------------------------------------- the script's registered reference table
def test_script_reference_table_matches_the_registration():
    import importlib.util
    from pathlib import Path
    s = importlib.util.spec_from_file_location("s91", Path(__file__).resolve().parents[1] / "scripts" / "91_tau_sweep.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    assert m.REF["cold_morning"][0.80] == (4, "3.23", "100%") and m.REF["ep160"][0.80] == (5, "3.75", "99%")
    assert [m.REF["cold_morning"][t][0] for t in T.TAU_GRID] == [6, 6, 5, 4, 3] and [m.REF["ep160"][t][0] for t in T.TAU_GRID] == [7, 7, 7, 5, 5]
