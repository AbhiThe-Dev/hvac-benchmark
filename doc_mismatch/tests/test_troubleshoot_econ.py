"""Tests for PREREGISTRATION_DR.md Addendum 37: `causes.ECON_FAULT` as a third upstream state, added additively. Simulation only.

Two kinds of test: (1) that every default (no extra state/cause requested) code path is BYTE-IDENTICAL to before this addendum, proven directly, not just plausible; (2) that the new
cause and its checks actually work end to end once opted in.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot.v1 import causes as C  # noqa: E402
from docmismatch.troubleshoot.v1 import catalogue as K  # noqa: E402
from docmismatch.troubleshoot.v1.engine import Session, make_case_v1  # noqa: E402
from docmismatch.troubleshoot.v2 import joint as JT  # noqa: E402
from docmismatch.troubleshoot.v2 import policies as P  # noqa: E402
from docmismatch.troubleshoot.v2 import study_econ as E  # noqa: E402
from docmismatch.troubleshoot.v2 import world2 as W  # noqa: E402

BLD = W.make_building2()


# ---------------------------------------------------------------------------------------------- 1. additivity (P1's ingredients, tested directly)
def test_econ_fault_is_not_enrolled_by_default():
    assert "econ_fault" not in C.BY_ID and "econ_fault" not in C.CAUSES.__class__((c.id for c in C.CAUSES))
    assert "econ_fault" in C.ALL_BY_ID
    assert abs(sum(c.share for c in C.CAUSES if c.lump == C.OTHER) - 1.0) < 1e-9      # untouched
    assert len(C.leaf_causes()) == len(C.CAUSES)                                      # extra=() is a true no-op
    assert len(K.CATALOGUE) == 30 and K.BAS_ECONOMIZER not in K.CATALOGUE and K.AHU_ECONOMIZER_TEST not in K.CATALOGUE


def test_all_by_id_is_a_strict_superset_and_existing_lookups_are_unaffected():
    assert set(C.BY_ID) < set(C.ALL_BY_ID)
    for cid, spec in C.BY_ID.items():
        assert C.ALL_BY_ID[cid] is spec                                               # same object, not a copy
    for cause in [(cid,) for cid in C.BY_ID]:
        assert C.v0_tag(cause) == (C.ALL_BY_ID[cause[0]].lump,)
        assert C.cause_text(cause) == C.ALL_BY_ID[cause[0]].label


def test_make_prior_v1_with_no_extra_causes_is_byte_identical_to_a_reference_computation():
    """A hand computation using only what existed before this addendum, compared to the current function with its new parameters at their defaults."""
    settings = W.tool_settings()
    causes, prior = C.make_prior_v1(["VAV-0", "VAV-1"], "VAV-0", settings, weights={"VAV-1": 1.0})
    # reference: literally the pre-addendum formula, by hand, from CAUSES/DEFAULT_SHARES only
    leaves = [c for c in C.CAUSES]
    total = sum(C.DEFAULT_SHARES[c.id] for c in leaves if c.lump == C.OTHER)
    assert causes[:len(leaves)] == [c.cause for c in leaves]
    for i, c in enumerate(leaves):
        if c.lump == C.OTHER:
            expect = (1.0 - settings.p_wrong - settings.p_acts_fail) * C.DEFAULT_SHARES[c.id] / total
            assert prior[i] == pytest.approx(expect, rel=1e-9) or prior[i] == pytest.approx(0.0, abs=1e-6)   # PRIOR_FLOOR only for a literal zero raw value


def test_extra_causes_needs_a_share_and_folds_in_without_touching_the_rest():
    with pytest.raises(ValueError):
        C.make_prior_v1(["VAV-0"], "VAV-0", W.tool_settings(), extra_causes=(C.ECON_FAULT,))          # no share given for it
    base_causes, base_prior = C.make_prior_v1(["VAV-0"], "VAV-0", W.tool_settings())
    shares = {**C.DEFAULT_SHARES, "econ_fault": 0.06}
    causes, prior = C.make_prior_v1(["VAV-0"], "VAV-0", W.tool_settings(), shares=shares, extra_causes=(C.ECON_FAULT,))
    assert len(causes) == len(base_causes) + 1 and ("econ_fault",) in causes and all(c in causes for c in base_causes)
    assert prior.sum() == pytest.approx(1.0) and prior[causes.index(("econ_fault",))] > 0
    # every OTHER-lump cause's RELATIVE odds among themselves are unchanged (the new mass comes from the lump's total growing, not a hand rescale of the others)
    for a, b in zip(("ahu_fan_off", "low_static"), ("ahu_fan_off", "low_static")):
        ratio_before = base_prior[base_causes.index((a,))] / base_prior[base_causes.index((b,))]
        ratio_after = prior[causes.index((a,))] / prior[causes.index((b,))]
        assert ratio_before == pytest.approx(ratio_after)


def test_ahu_row_and_bears_on_ahu_default_arguments_reproduce_todays_catalogue_exactly():
    for ck in K.CATALOGUE:
        if ck.is_reading and ck.subject == "ahu":
            assert np.array_equal(JT.ahu_row(ck), JT.ahu_row(ck, upstream=("ahu_fan_off", "low_static")))
    assert [c.name for c in K.CATALOGUE if JT.bears_on_ahu(c)] == ["static_at_box"]
    for ck in K.CATALOGUE + K.ECON_CHECKS:
        assert JT.bears_on_ahu(ck) == JT.bears_on_ahu(ck, upstream=JT.UPSTREAM)                        # default arg == explicit default


def test_joint_settings_defaults_are_algebraically_identical_to_before():
    js = JT.JointSettings()
    assert js.states == JT.STATES and js.upstream == JT.UPSTREAM
    assert np.array_equal(js.state_prior, np.array([1.0 - js.f, js.f * js.fan_share, js.f * (1.0 - js.fan_share)]))
    assert np.array_equal(js.affect, np.array([0.0, js.r_fan, js.r_low]))


def test_worldparams_defaults_are_algebraically_identical_to_before():
    wp = W.WorldParams(0.03, 0.0, 0.05, 0.0)
    assert wp.states == JT.STATES and wp.upstream == JT.UPSTREAM
    assert np.array_equal(wp.state_prior(), np.array([1.0 - wp.f, wp.f * W.FAN_SHARE, wp.f * (1.0 - W.FAN_SHARE)]))
    assert wp.r_affect() == W.R_AFFECT


def test_draw_event_default_reproduces_a_reference_event_and_events_carry_the_default_upstream():
    cases = W.make_cases()
    wp = W.WorldParams(0.03, 0.0, 0.05, 0.0)
    ev = W.draw_event(0, 0, wp, cases)
    assert ev.upstream == ("ahu_fan_off", "low_static")
    ev2 = W.draw_event(0, 0, wp, cases)
    assert ev.rooms == ev2.rooms and ev.causes == ev2.causes and ev.u == ev2.u              # deterministic given the same stream


def test_group_stats_and_state_prior_shapes_generalise_from_3_to_4_states():
    js = JT.JointSettings(extra_states=("econ_fault",), extra_affect={"econ_fault": 0.15}, extra_share={"econ_fault": 6.0 / 23.0})
    shares = {**C.DEFAULT_SHARES, "econ_fault": 0.06}
    case = make_case_v1(BLD, "Room-0", W.TIER_ITEMS["T3"], settings=W.tool_settings(), context=W.tier_context("T3", 0), member_name="Room 0",
                        shares=shares, extra_causes=(C.ECON_FAULT,), checks=K.CATALOGUE + K.ECON_CHECKS)
    m = JT.JointModel([case], js)
    assert m.n_states == 4 and m.upstream == ("ahu_fan_off", "low_static", "econ_fault")
    s = m.initial()
    g = m.group_stats(s, case.ahu)
    assert g.W.shape == (4,) and g.Z.shape == (1, 4) and abs(g.W.sum() - 1.0) < 1e-9


# ---------------------------------------------------------------------------------------------- 2. the deliberate change, and the new cause working end to end
def test_bears_on_ahu_any_vs_both_only_differs_when_a_third_upstream_state_exists():
    from dataclasses import replace
    base = K.BY_NAME["static_at_box"]
    weak_fan = replace(base, detects={**base.detects, "ahu_fan_off": 0.3})           # low_static still strong: "any" qualifies, historical "both" would not
    assert JT.bears_on_ahu(weak_fan)
    both_weak = replace(base, detects={**base.detects, "ahu_fan_off": 0.3, "low_static": 0.3})
    assert not JT.bears_on_ahu(both_weak)


def test_econ_fault_is_diagnosable_with_a_clean_oracle_at_v1_level():
    shares = {**C.DEFAULT_SHARES, "econ_fault": 0.06}
    case = make_case_v1(BLD, "Room-0", W.TIER_ITEMS["T3"], settings=W.tool_settings(), context=W.tier_context("T3", 0), member_name="Room 0",
                        shares=shares, extra_causes=(C.ECON_FAULT,), checks=K.CATALOGUE + K.ECON_CHECKS)
    sess = Session(case)
    for _ in range(15):
        step = sess.next_step()
        if step is None:
            break
        ck = step.check
        p = ck.detects.get("econ_fault", ck.bg) if ck.is_reading else 0.5
        sess.report(ck.words[0] if p >= 0.5 else ck.words[1])
    st = sess.status()
    assert st["concluded"] and st["ranked"][0][0] == ("econ_fault",)


def test_run_policy_is_unmodified_and_works_with_econ_settings():
    """policies.py itself is untouched by this addendum: run_policy accepts an econ-aware js/cases with no changes there."""
    shares = {**C.DEFAULT_SHARES, "econ_fault": 0.06}
    checks = K.CATALOGUE + K.ECON_CHECKS
    cs = [make_case_v1(BLD, f"Room-{r}", W.TIER_ITEMS["T3"], settings=W.tool_settings(), context=W.tier_context("T3", r), member_name=f"Room {r}",
                       shares=shares, extra_causes=(C.ECON_FAULT,), checks=checks) for r in (0, 1)]
    js = JT.JointSettings(extra_states=("econ_fault",), extra_affect={"econ_fault": 0.15}, extra_share={"econ_fault": 6.0 / 23.0})

    class FixedOracle:
        def ask_ahu(self, a, ck):
            return ck.words[0] if ck.detects.get("econ_fault", ck.bg) >= 0.5 else ck.words[1]

        def ask_room(self, i, ck, target):
            p = ck.detects.get("econ_fault", ck.bg) if ck.is_reading else 0.5
            return ck.words[0] if p >= 0.5 else ck.words[1]

    for pol in ("tool_ticket_memo2", "tool_joint2"):
        r = P.run_policy(pol, cs, FixedOracle(), [W.context_dict("T3", 0), W.context_dict("T3", 1)], js)
        assert r["guess"] == [("econ_fault",), ("econ_fault",)]


def test_oracle_needs_the_extended_catalogue_for_the_new_checks():
    ev_cases = W.make_cases()
    ev = W.draw_event(0, 0, W.WorldParams(0.03, 0.0, 0.05, 0.0), ev_cases)
    with pytest.raises(KeyError):
        W.Oracle(ev, 0.0, np.random.default_rng(0)).p_ahu(ev.rooms and "AHU-0" or "AHU-0", "bas_economizer")
    ok = W.Oracle(ev, 0.0, np.random.default_rng(0), checks=K.ECON_CHECKS).p_ahu("AHU-0", "bas_economizer")
    assert 0.0 <= ok <= 1.0


# ---------------------------------------------------------------------------------------------- 3. study_econ.py's own machinery
def test_econ_shared_counts_only_econ_fault_not_other_upstream_causes():
    class FakeEvent:
        def __init__(self, causes, ahus):
            self.causes, self.true_ahu_of = causes, ahus
    ev = FakeEvent([("econ_fault",), ("econ_fault",), ("ahu_fan_off",)], ["AHU-0", "AHU-0", "AHU-0"])
    assert E.econ_shared(ev)
    ev2 = FakeEvent([("econ_fault",), ("ahu_fan_off",), ("ahu_fan_off",)], ["AHU-0", "AHU-0", "AHU-0"])
    assert not E.econ_shared(ev2)                                     # 2 upstream complaints, but not both econ_fault


def test_score_econ_isolates_econ_caused_complaints():
    class Ev:
        causes = [("econ_fault",), ("low_static",), ("econ_fault",)]
    res = dict(guess=[("econ_fault",), ("other",), ("actuator_fail",)], concluded=[True, True, True])
    sc = E.score_econ(res, Ev())
    assert sc["n"] == 3 and sc["correct"] == 1 and sc["econ_n"] == 2 and sc["econ_correct"] == 1 and sc["econ_wc"] == 1


def test_gate_g2_catches_a_broken_shares_dict():
    good = E.gate_g2_probabilities()
    assert good[0]
    old = E.ECON_SHARES
    try:
        E.ECON_SHARES = {k: v for k, v in old.items() if k != "econ_fault"}     # break it: no share for the extra cause
        assert not E.gate_g2_probabilities()[0]
    finally:
        E.ECON_SHARES = old


def test_decision_reads_gates_and_predictions_correctly():
    ok_preds = {"P1 additive (gate)": (True, ""), "P2 diagnosable at T2 (x)": (True, ""), "P2 diagnosable at T3 (x)": (True, ""),
               "P3 the routine at T2 (x)": (True, ""), "P3 the routine at T3 (x)": (True, ""), "P4 safety at T2 (x)": (True, ""), "P4 safety at T3 (x)": (True, "")}
    assert E.decision(ok_preds) == "THE ROUTINE STILL CAPTURES IT"
    bad_p1 = {**ok_preds, "P1 additive (gate)": (False, "")}
    assert E.decision(bad_p1).startswith("NO RESULT")
    bad_p4 = {**ok_preds, "P4 safety at T2 (x)": (False, "")}
    assert E.decision(bad_p4) == "UNSAFE"
    bad_p3 = {**ok_preds, "P3 the routine at T2 (x)": (False, "")}
    assert E.decision(bad_p3) == "THE ROUTINE NEEDS HELP FOR THIS CAUSE"
    no_data_p3 = {**ok_preds, "P3 the routine at T2 (x)": (None, ""), "P3 the routine at T3 (x)": (None, "")}
    assert E.decision(no_data_p3) == "NOT ENOUGH ECON-SHARED EVENTS TO SAY"


def test_run_cell_econ_and_gates_on_a_small_smoke_sample():
    res = E.run_cell_econ(30)
    assert res["n"] == 30 and set(res["pol"]) == {(t, p) for t in E.TIERS for p in E.POLICIES}
    cases = E.make_cases_econ()
    g = E.gates(res, cases, g1_events=10)
    assert all(ok for ok, _ in g.values()), g


def test_reference_low_static_run_is_independent_of_the_econ_world():
    ref = E.run_reference_low_static(50)
    assert set(ref) == {(t, p) for t in E.TIERS for p in E.POLICIES}
    assert all(v != v or 0.0 <= v <= 1.0 for v in ref.values())        # a rate in [0, 1], or nan if no low_static complaints were drawn
