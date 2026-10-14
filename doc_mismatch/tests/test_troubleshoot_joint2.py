"""Guards for the group-informing rule and its study (docmismatch.troubleshoot.v2: `bears_on_ahu`, the `group_informing` switch, `tool_ticket_memo2`, `tool_joint2`, study_joint2, scripts/75;
PREREGISTRATION_DR.md Addendum 31). No test here reads a study result: they check code paths, rules and gates on synthetic arrays and on tiny runs whose numbers are never inspected."""
import importlib.util
import pickle
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot.v1 import catalogue as K  # noqa: E402
from docmismatch.troubleshoot.v2 import joint as Jn, policies as P, study_joint as J, study_joint2 as J2, world2 as W  # noqa: E402
from docmismatch.troubleshoot.v2.joint import JointModel, JointSession  # noqa: E402

spec = importlib.util.spec_from_file_location("script75", ROOT / "scripts" / "75_troubleshoot_joint2.py")
S75 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S75)

CASES = W.make_cases()
LOW, FAN = ("low_static",), ("ahu_fan_off",)
PRIMARY = J.Cell(**J.PRIMARY)
HAVE_RAW30 = J2.RAW30.exists()


def cases_for(tier, rooms):
    return [CASES[(tier, r)] for r in rooms]


class Modal(W.Oracle):
    def __init__(self, event, rel_a=0.0):
        super().__init__(event, rel_a, np.random.default_rng(0))
        self.calls = []

    def ask_room(self, i, ck, target):
        self.calls.append(("room", i, ck.name, target))
        return ck.words[0] if self.p_room(i, ck.name, target) >= 0.5 else ck.words[1]

    def ask_ahu(self, a, ck):
        self.calls.append(("ahu", a, ck.name))
        return ck.words[0] if self.p_ahu(a, ck.name) >= 0.5 else ck.words[1]


def state_event(n, state):
    return W.Event(0, 0, {"AHU-0": state, "AHU-1": "ok", "AHU-2": "ok"}, {f"VAV-{b}": f"AHU-{b // 8}" for b in range(24)}, list(range(n)), [(state,)] * n, ["AHU-0"] * n)


# ---------------------------------------------------------------------------------------------- constants and names
def test_the_new_policies_extend_addendum_30s_without_changing_it():
    assert P.POLICIES == ("tool_ticket", "tool_ticket_nb", "tool_ticket_memo", "tool_joint", "tool_joint_la2", "fast_ticket", "fast_parent") and P.LOOKAHEAD_POLICIES == ("tool_joint_la2",)
    assert P.POLICIES2 == ("tool_ticket_memo2", "tool_joint2", "tool_joint2_la2", "tool_joint3") and P.LOOKAHEAD_POLICIES2 == ("tool_joint2_la2",)
    assert [P.POLICY_INDEX[p] for p in P.POLICIES + P.POLICIES2] == list(range(11)) and P.POLICY_INDEX["tool_ticket_memo2"] == 7 and P.POLICY_INDEX["tool_joint2_la2"] == 9 and P.POLICY_INDEX["tool_joint3"] == 10
    assert J.policies_for(PRIMARY) == P.POLICIES and len(J.policies_for(J.Cell("assumed", "M1", "R0"))) == 6


def test_the_follow_up_constants_are_the_registered_ones():
    assert J2.SEED == 31 and J2.N_EPISODES == 1000 and J2.BOOT_B == 1000 and J2.G1_EVENTS == 20 and J.SEED == 30
    assert J2.COMPS2 == dict(H=("tool_joint2", "tool_ticket_memo2"), I=("tool_joint2", "tool_joint"), J=("tool_ticket_memo2", "tool_ticket_memo"), K=("tool_joint2", "fast_parent"),
                             L=("tool_joint2", "tool_ticket"), M=("tool_joint2_la2", "tool_joint2"), N=("tool_joint3", "tool_ticket_memo2"), O=("tool_joint3", "tool_joint2"))
    assert (J2.P1_BAR, J2.P2_BAR, J2.P3_BAR, J2.P4_LABEL, J2.P5_BAR, J2.P6_BAR, J2.P7_BAR, J2.P8_BAR, J2.P10_BAR, J2.P11_BAR) == (0.15, 0.10, 0.10, "IMPROVES", 0.15, 0.01, 0.02, 0.02, 0.05, 0.10)
    assert (J2.UNSAFE_BAR, J2.UNSAFE_CELLS) == (0.02, 2) and Jn.BEARS_ON_AHU == 0.5
    la = [c for c in J.all_cells() if "tool_joint2_la2" in J2.policies_for2(c)]
    assert [(c.shared, c.map, c.rel) for c in la] == [(s, "M0", "R0") for s in ("rare", "assumed", "common")]
    assert all(J2.policies_for2(c)[:2] == ("tool_ticket_memo2", "tool_joint2") and J2.policies_for2(c)[-1] == "tool_joint3" for c in J.all_cells())


# ---------------------------------------------------------------------------------------------- the rule
def test_exactly_one_catalogue_check_bears_on_the_air_handler():
    assert [c.name for c in K.CATALOGUE if Jn.bears_on_ahu(c)] == ["static_at_box"]


def test_the_bearing_rule_and_its_boundaries():
    base = K.BY_NAME["static_at_box"]
    assert Jn.bears_on_ahu(base)
    make = lambda **kw: replace(base, detects={**base.detects, **kw})  # noqa: E731
    assert Jn.bears_on_ahu(make(ahu_fan_off=0.5, low_static=0.5))                                        # exactly 0.5: at least
    # Addendum 37: the rule is "at least one" upstream cause >= 0.5, not "both" (registered there; a no-op for the real catalogue, where static_at_box detects both strongly, but not
    # for this hand-weakened check): weakening ONE of the two still qualifies through the other; only weakening BOTH does not.
    assert Jn.bears_on_ahu(make(ahu_fan_off=0.49)) and Jn.bears_on_ahu(make(low_static=0.49))
    assert not Jn.bears_on_ahu(make(ahu_fan_off=0.49, low_static=0.49))
    assert not Jn.bears_on_ahu(make(damper_mech=0.51)) and Jn.bears_on_ahu(make(damper_mech=0.5))          # another cause at exactly 0.5: at most
    assert not Jn.bears_on_ahu(replace(base, bg=0.51)) and Jn.bears_on_ahu(replace(base, bg=0.5))
    assert not Jn.bears_on_ahu(K.BY_NAME["override_room"]) and not Jn.bears_on_ahu(K.BY_NAME["confirm_acts"])         # v0 checks are not readings
    for name in ("bas_ahu_fan", "bas_static", "ahu_visit", "ahu_gauge"):
        assert not Jn.bears_on_ahu(K.BY_NAME[name])                                                        # an air-handler check already informs the group, by its subject
    assert Jn.bears_on_ahu(replace(K.BY_NAME["bas_static"], subject="box"))                                # the rule is about the responses: the same responses on a box check would qualify
    for name in ("flow_hood", "bas_airflow", "bas_damper", "power_24vac", "manual_damper_test"):
        assert not Jn.bears_on_ahu(K.BY_NAME[name])


def test_a_bearing_reading_informs_the_whole_group_only_with_the_rule_on():
    cs = cases_for("T2", [0, 1, 2])
    off, on = JointModel(cs), JointModel(cs, group_informing=True)
    assert off.group_informing is False and on.group_informing is True
    s0 = off.initial()
    find = lambda m, kind, name, who: next(o for o in m.options(s0, m.all_stats(s0), 2.0, 0.0, 0.0) if o.kind == kind and o.check.name == name and o.who == who)  # noqa: E731
    for positive in (True, False):
        assert on.apply(s0, find(on, "complaint", "static_at_box", 1), positive).informed == {0, 1, 2}
        assert off.apply(s0, find(off, "complaint", "static_at_box", 1), positive).informed == {1}
        assert on.apply(s0, find(on, "complaint", "power_24vac", 1), positive).informed == {1}                # another box reading: only its own complaint
        assert on.apply(s0, find(on, "ahu", "ahu_visit", "AHU-0"), positive).informed == {0, 1, 2} and off.apply(s0, find(off, "ahu", "ahu_visit", "AHU-0"), positive).informed == {0, 1, 2}
    assert on.apply(s0, find(on, "complaint", "static_at_box", 1), None).informed == frozenset()             # unsure informs nobody
    other = JointModel(cases_for("T2", [0, 9]), group_informing=True)
    so = other.initial()
    o = next(x for x in other.options(so, other.all_stats(so), 2.0, 0.0, 0.0) if x.kind == "complaint" and x.who == 0 and x.check.name == "static_at_box")
    assert other.apply(so, o, True).informed == {0}                                                        # a complaint on another air handler is not informed


def test_the_rule_changes_who_is_informed_but_never_the_beliefs():
    cs = cases_for("T2", [0, 1, 2, 3])
    off, on = JointModel(cs), JointModel(cs, group_informing=True)
    so, sn = off.initial(), on.initial()
    for name, who, pos in (("static_at_box", 2, True), ("power_24vac", 0, False), ("static_at_box", 3, False)):
        oo = next(x for x in off.options(so, off.all_stats(so), 2.0, 0.0, 0.0) if x.check.name == name and x.who == who)
        on_ = next(x for x in on.options(sn, on.all_stats(sn), 2.0, 0.0, 0.0) if x.check.name == name and x.who == who)
        so, sn = off.apply(so, oo, pos), on.apply(sn, on_, pos)
    for a, b in zip(off.marginals(so), on.marginals(sn)):
        assert a == pytest.approx(b, abs=1e-12)
    assert on.ahu_posterior(sn)["AHU-0"] == pytest.approx(off.ahu_posterior(so)["AHU-0"], abs=1e-12) and sn.informed == {0, 1, 2, 3} and so.informed == {0, 2, 3}


def test_a_bearing_readings_audience_is_shown_but_its_rate_threshold_stays_the_room_checks():
    cs = cases_for("T2", [0, 1, 2, 3])
    for flag, aud in ((True, 4), (False, 1)):
        m = JointModel(cs, group_informing=flag)
        s = m.initial()
        opts = m.options(s, m.all_stats(s), 0.95, 0.0, 0.0)
        assert {o.audience for o in opts if o.kind == "complaint" and o.check.name == "static_at_box"} == {aud}
        assert {o.audience for o in opts if o.kind == "complaint" and o.check.name != "static_at_box"} == {1}
        o = next(x for x in opts if x.check.name == "static_at_box" and x.who == 0)
        x = o.gain / o.minutes
        assert o.key in [q.key for q in m.options(s, m.all_stats(s), 0.95, x - 1e-9, 0.0)] and o.key not in [q.key for q in m.options(s, m.all_stats(s), 0.95, x + 1e-9, 0.0)]   # unscaled: min_rate itself


def test_the_air_handler_threshold_is_scaled_by_the_audience_unless_switched_off():
    cs = cases_for("T3", [0, 1, 2, 3])
    on, off = JointModel(cs), JointModel(cs, scale_audience=False)
    assert on.scale_audience is True and off.scale_audience is False and JointModel(cs, group_informing=True).scale_audience is True
    s = on.initial()
    a = next(o for o in on.options(s, on.all_stats(s), 0.95, 0.0, 0.0) if o.kind == "ahu" and o.check.name == "bas_ahu_fan")
    x = a.gain / a.minutes
    assert a.audience == 4
    for m, lo, hi in ((on, x / 4, x / 4), (off, x, x)):
        assert a.key in [o.key for o in m.options(s, m.all_stats(s), 0.95, lo - 1e-9, 0.0)] and a.key not in [o.key for o in m.options(s, m.all_stats(s), 0.95, hi + 1e-9, 0.0)]


def test_one_bearing_reading_concludes_the_group_with_the_rule_on_and_only_its_complaint_with_it_off():
    for flag in (True, False):
        sess = JointSession(cases_for("T2", [0, 1, 2, 3]), group_informing=flag)
        o = next(x for x in sess.model.options(sess.state, sess.model.all_stats(sess.state), sess.tau, 0.0, 0.0) if x.check.name == "static_at_box" and x.who == 1)
        sess.report(o.check.words[0], o)
        assert sess.concluded() == ([True] * 4 if flag else [False, True, False, False])
    sess = JointSession(cases_for("T2", [0, 1, 2, 3]), group_informing=True)
    assert JointSession(cases_for("T2", [0]), group_informing=True).model.group_informing and sess.model.group_informing


def test_the_rule_makes_the_joint_tool_read_the_static_once_where_it_used_to_read_it_at_every_box():
    ev = state_event(4, "low_static")
    for flag, expect_fewer in ((False, False), (True, True)):
        orc = Modal(ev)
        r = P.run_joint(cases_for("T2", [0, 1, 2, 3]), orc, group_informing=flag)
        statics = [c for c in orc.calls if c[2] == "static_at_box"]
        assert (len(statics) < 4) is expect_fewer and r["concluded"] == [True] * 4 and r["guess"] == [LOW] * 4
    ctx = [W.context_dict("T2", r) for r in range(4)]
    j2, j = P.run_policy("tool_joint2", cases_for("T2", [0, 1, 2, 3]), Modal(ev), ctx), P.run_policy("tool_joint", cases_for("T2", [0, 1, 2, 3]), Modal(ev), ctx)
    assert j2["minutes"] < j["minutes"] and j2["concluded"] == [True] * 4 and j2["n_checks"] == 1               # one reading of the inlet static speaks for the four
    j3 = P.run_policy("tool_joint3", cases_for("T2", [0, 1, 2, 3]), Modal(ev), ctx)
    assert j3["concluded"] == [True] * 4 and j3["guess"] == [LOW] * 4


# ---------------------------------------------------------------------------------------------- the routine's counterpart
def _spy_sessions():
    log = []

    class Spy(P.PriorSession):
        def __init__(self, case, prior=None):
            super().__init__(case, prior)
            log.append(self)
            self.start = None
        def next_step(self):
            if self.start is None:
                self.start = list(self.log)
            return super().next_step()
    return Spy, log


def test_memo2_carries_an_abnormal_inlet_static_to_the_later_tickets_of_the_same_air_handler_only():
    cs = cases_for("T2", [0, 1, 2, 9])
    ev = W.Event(0, 0, {"AHU-0": "low_static", "AHU-1": "ok", "AHU-2": "ok"}, {f"VAV-{b}": f"AHU-{b // 8}" for b in range(24)}, [0, 1, 2, 9], [LOW, LOW, LOW, ("damper_mech",)], ["AHU-0"] * 3 + ["AHU-1"])
    orig = P.PriorSession
    Spy, log = _spy_sessions()
    P.PriorSession = Spy
    try:
        r = P.run_ticket(cs, Modal(ev), "memo2")
    finally:
        P.PriorSession = orig
    firsts = [s for s in log if any(o.check == "static_at_box" for o in s.log if o.minutes > 0)]
    assert firsts and log[0].start == []                                                                  # nothing to carry into the first ticket
    seeded = [[(o.check, o.target, o.outcome, o.minutes) for o in s.start] for s in log]
    assert seeded[1] and ("static_at_box", "VAV-1", "abnormal", 0.0) in seeded[1] and ("static_at_box", "VAV-2", "abnormal", 0.0) in seeded[2]
    assert not any(x[0] == "static_at_box" for x in seeded[3])                                             # another air handler: nothing carried
    assert r["n_checks"] == sum(1 for s in log for o in s.log if o.minutes > 0)


def test_memo_does_not_carry_it_and_a_normal_reading_is_never_carried():
    cs = cases_for("T2", [0, 1, 2])
    ev = state_event(3, "low_static")
    orig = P.PriorSession
    Spy, log = _spy_sessions()
    P.PriorSession = Spy
    try:
        P.run_ticket(cs, Modal(ev), "memo")
    finally:
        P.PriorSession = orig
    assert not any(o.check == "static_at_box" and o.minutes == 0.0 for s in log for o in s.start)
    healthy = W.Event(0, 0, {"AHU-0": "ok", "AHU-1": "ok", "AHU-2": "ok"}, {f"VAV-{b}": f"AHU-{b // 8}" for b in range(24)}, [0, 1, 2], [("damper_mech",)] * 3, ["AHU-0"] * 3)
    Spy2, log2 = _spy_sessions()
    P.PriorSession = Spy2
    try:
        P.run_ticket(cs, Modal(healthy), "memo2")
    finally:
        P.PriorSession = orig
    assert not any(o.check == "static_at_box" and o.minutes == 0.0 for s in log2 for o in s.start)


def test_memo2_is_cheaper_than_memo_on_a_low_static_visit_and_the_same_elsewhere():
    ev = state_event(4, "low_static")
    cs, ctx = cases_for("T2", [0, 1, 2, 3]), [W.context_dict("T2", r) for r in range(4)]
    a, b = P.run_policy("tool_ticket_memo", cs, Modal(ev), ctx), P.run_policy("tool_ticket_memo2", cs, Modal(ev), ctx)
    assert b["minutes"] < a["minutes"] and b["guess"] == [LOW] * 4
    solo = [cases_for("T2", [5])]
    one = W.Event(0, 0, {"AHU-0": "ok", "AHU-1": "ok", "AHU-2": "ok"}, {f"VAV-{b}": f"AHU-{b // 8}" for b in range(24)}, [5], [("damper_mech",)], ["AHU-0"])
    assert P.run_policy("tool_ticket_memo2", solo[0], Modal(one), [W.context_dict("T2", 5)])["minutes"] == P.run_policy("tool_ticket_memo", solo[0], Modal(one), [W.context_dict("T2", 5)])["minutes"]


def test_the_new_policies_run_are_deterministic_and_accept_only_registered_names():
    ev = W.draw_event(0, 4, W.WorldParams(0.09, 0.0, 0.05, 0.0), CASES)
    cs, ctx = [CASES[("T3", r)] for r in ev.rooms], [W.context_dict("T3", r) for r in ev.rooms]
    for pol in P.POLICIES2:
        a = P.run_policy(pol, cs, W.Oracle(ev, 0.0, np.random.default_rng(5)), ctx)
        b = P.run_policy(pol, cs, W.Oracle(ev, 0.0, np.random.default_rng(5)), ctx)
        assert (a["minutes"], a["guess"], a["n_checks"]) == (b["minutes"], b["guess"], b["n_checks"]) and len(a["guess"]) == ev.n
    with pytest.raises(ValueError):
        P.run_ticket(cs, Modal(ev), "memo3")
    off = P.run_joint(cs, W.Oracle(ev, 0.0, np.random.default_rng(5)))
    assert off["minutes"] == P.run_policy("tool_joint", cs, W.Oracle(ev, 0.0, np.random.default_rng(5)), ctx)["minutes"]           # the switch defaults to off


# ---------------------------------------------------------------------------------------------- merging, analysis, predictions, decision
@pytest.fixture(scope="module")
def tiny():
    cells = J.all_cells()
    a30 = {i: J.run_cell(i, cells[i], 12) for i in (0, 1)}
    a31 = {i: J2.run_cell2(i, cells[i], 12) for i in (0, 1)}
    return a30, a31


def test_a_cell_run_has_the_new_policies_on_the_same_events_and_is_reproducible(tiny):
    a30, a31 = tiny
    for i in (0, 1):
        assert np.array_equal(a31[i]["n_compl"], a30[i]["n_compl"]) and np.array_equal(a31[i]["kind"], a30[i]["kind"]) and a31[i]["tag"] == J.tool_settings_tag()
        assert {k for k in a31[i]["pol"]} == {(t, p) for t in J.TIERS for p in J2.policies_for2(a31[i]["cell"])}
        for v in a31[i]["pol"].values():
            assert len(v["minutes"]) == 12 and np.isfinite(v["minutes"]).all() and (v["correct"] <= a31[i]["n_compl"]).all() and (v["wc"] <= v["concluded"]).all() and len(v["trace"]) == 12
    again = J2.run_cell2(0, J.all_cells()[0], 12)
    assert all(np.array_equal(v["minutes"], a31[0]["pol"][k]["minutes"]) for k, v in again["pol"].items())
    a = J2.compute_cells2([(0, J.all_cells()[0]), (1, J.all_cells()[1])], 5, workers=1)
    b = J2.compute_cells2([(0, J.all_cells()[0]), (1, J.all_cells()[1])], 5, workers=2)
    assert all(all(np.array_equal(x["pol"][k]["minutes"], y["pol"][k]["minutes"]) for k in x["pol"]) for x, y in zip(a, b))


def test_the_answer_streams_are_the_registered_ones(tiny):
    cases = W.make_cases()
    wp = J.all_cells()[0].params()
    ev = W.draw_event(0, 2, wp, cases)
    for ti, tier in enumerate(J.TIERS):
        for pol in ("tool_joint2", "tool_ticket_memo2"):
            cs = [cases[(tier, r)] for r in ev.rooms]
            r = P.run_policy(pol, cs, W.Oracle(ev, wp.rel_a, np.random.default_rng([31, 0, 100 + 10 * ti + P.POLICY_INDEX[pol], 2])), [W.context_dict(tier, x) for x in ev.rooms])
            assert tiny[1][0]["pol"][(tier, pol)]["minutes"][2] == r["minutes"] and tiny[1][0]["pol"][(tier, pol)]["checks"][2] == r["n_checks"]


def test_merging_cuts_addendum_30s_cell_to_the_new_events_and_refuses_a_mismatch(tiny):
    a30, a31 = tiny
    m = J2.merged(a31[0], a30[0])
    assert m["n"] == 12 and {k for k in m["pol"]} == {k for k in a30[0]["pol"]} | {k for k in a31[0]["pol"]}
    short = J2.run_cell2(0, J.all_cells()[0], 5)
    ms = J2.merged(short, a30[0])
    assert ms["n"] == 5 and all(len(v["minutes"]) == 5 for v in ms["pol"].values()) and np.array_equal(ms["pol"][("T2", "tool_joint")]["minutes"], a30[0]["pol"][("T2", "tool_joint")]["minutes"][:5])
    assert len(ms["n_compl"]) == 5 and len(ms["kind"]) == 5
    with pytest.raises(ValueError):
        J2.merged(a31[1], a30[0])
    with pytest.raises(ValueError):
        J2.merged(J2.run_cell2(0, J.all_cells()[0], 20), a30[0])                                            # more events than were stored


def test_analysis_has_every_summary_and_comparison_and_uses_the_new_bootstrap_seed(tiny):
    a30, a31 = tiny
    an = J2.analyze_cell2(J2.merged(a31[0], a30[0]), 40)
    for t in J.TIERS:
        for pol in P.POLICIES + J2.policies_for2(a31[0]["cell"]):
            assert (t, pol, "all") in an["sum"]
        for name in J2.COMPS2:
            assert (t, name, "all") in an["cmp"]
    assert not any(k[1] == "M" for k in J2.analyze_cell2(J2.merged(a31[1], a30[1]), 40)["cmp"])
    res = J2.merged(a31[0], a30[0])
    idx = np.flatnonzero(J.subset_masks(res)["all"])
    boot = np.random.default_rng([31, 0, 99, 0]).integers(0, len(idx), (40, len(idx)))
    d = J.per_event(res, "T2", "tool_joint2")["minutes"] - J.per_event(res, "T2", "tool_ticket_memo2")["minutes"]
    assert an["cmp"][("T2", "H", "all")]["ci_min"] == pytest.approx(J.S.paired_ci(d, boot))


def _cmp(label="NEITHER", time="SAME", acc="SAME", safety="NONE", **kw):
    return dict(label=label, time=time, acc=acc, safety=safety, r_min=kw.get("r_min", 0.0), d_min=kw.get("d_min", 0.0), d_acc=0.0, d_wc=0.0, d_checks=0.0, ci_min=(0, 0), ci_acc=(0, 0), ci_wc=(0, 0),
                break_even="DOMINATES", wrong_cost=0.0, minutes_a=100.0, minutes_b=100.0)


def fake(edit=None):
    out = []
    for i, c in enumerate(J.all_cells()):
        sm, cm = {}, {}
        for t in J.TIERS:
            for pol in P.POLICIES + J2.policies_for2(c):
                if pol == "tool_joint_la2" and not c.has_lookahead:
                    continue
                for sub in J.SUBSETS:
                    sm[(t, pol, sub)] = dict(n=50, minutes=100.0, checks=5.0, accuracy=0.9, accuracy_c=0.9, wrong_confident=0.02, concluded=0.9, complaints=2.0)
            for name, (a, b) in J2.COMPS2.items():
                if a == "tool_joint2_la2" and not c.has_lookahead:
                    continue
                for sub in J.SUBSETS:
                    cm[(t, name, sub)] = _cmp()
        if edit:
            edit(c, sm, cm)
        out.append(dict(idx=i, cell=c, n=100, counts={k: 10 for k in J.SUBSETS}, sum=sm, cmp=cm, mean_complaints=2.0))
    return out


def _all_hold(c, sm, cm):
    if c == PRIMARY:
        cm[("T2", "O", "shared")] = _cmp(r_min=-0.2)
        cm[("T2", "I", "shared")] = _cmp(r_min=-0.3)
        cm[("T2", "J", "shared")] = _cmp(r_min=-0.2)
        cm[("T3", "I", "shared")] = _cmp(r_min=-0.05)
        cm[("T2", "H", "shared")] = _cmp(r_min=0.05)
    if c.has_lookahead:
        for t in J.TIERS:
            cm[(t, "M", "shared")] = _cmp("NEITHER")
    if c == J.Cell("assumed", "M1", "R0"):
        sm[("T2", "tool_joint2", "all")]["wrong_confident"] = 0.03
        sm[("T2", "tool_ticket_memo2", "all")]["wrong_confident"] = 0.02


def holds(an):
    return {k: ok for k, (ok, _) in J2.predictions2(an).items()}


def test_every_prediction_holds_on_the_constructed_analyses_and_each_fails_on_its_own_edit():
    assert holds(fake(_all_hold)) == {f"P{i}": True for i in range(1, 12)}
    def fails(key, fn):
        got = holds(fake(lambda c, sm, cm: (_all_hold(c, sm, cm), fn(c, sm, cm))))
        assert got[key] is False and all(v for k, v in got.items() if k != key), (key, got)
    at = lambda key, val, cell=PRIMARY: (lambda c, sm, cm: cm.__setitem__(key, val) if c == cell else None)  # noqa: E731
    sumat = lambda key, field, val, cell=PRIMARY: (lambda c, sm, cm: sm[key].__setitem__(field, val) if c == cell else None)  # noqa: E731
    fails("P1", at(("T2", "I", "shared"), _cmp(r_min=-0.14)))
    fails("P2", at(("T2", "J", "shared"), _cmp(r_min=-0.09)))
    fails("P3", at(("T3", "I", "shared"), _cmp(r_min=-0.10)))
    fails("P3", at(("T3", "I", "shared"), _cmp(r_min=0.10)))
    fails("P4", at(("T2", "H", "shared"), _cmp("IMPROVES", "FASTER", r_min=-0.14)))
    fails("P5", at(("T2", "H", "shared"), _cmp(r_min=0.15)))
    fails("P5", at(("T2", "H", "shared"), _cmp(r_min=-0.16)))
    fails("P6", sumat(("T3", "tool_joint2", "all"), "wrong_confident", 0.031))
    fails("P7", sumat(("T2", "tool_joint2", "all"), "accuracy", 0.879))
    fails("P8", sumat(("T2", "tool_joint2", "all"), "wrong_confident", 0.05, J.Cell("assumed", "M2", "R0")))
    fails("P9", lambda c, sm, cm: [cm.__setitem__(("T3", "M", "shared"), _cmp("IMPROVES", "FASTER")) for _ in [0]] if c.has_lookahead and c.shared in ("rare", "common") else None)
    fails("P10", sumat(("T2", "tool_joint2", "single"), "minutes", 106.0))
    fails("P11", at(("T2", "O", "shared"), _cmp(r_min=-0.09)))


def test_the_prediction_boundaries_are_the_registered_ones():
    def edit_holds(fn):
        return holds(fake(lambda c, sm, cm: (_all_hold(c, sm, cm), fn(c, sm, cm))))
    assert edit_holds(lambda c, sm, cm: cm.__setitem__(("T2", "I", "shared"), _cmp(r_min=-0.15)) if c == PRIMARY else None)["P1"] is True
    assert edit_holds(lambda c, sm, cm: cm.__setitem__(("T2", "J", "shared"), _cmp(r_min=-0.10)) if c == PRIMARY else None)["P2"] is True
    assert edit_holds(lambda c, sm, cm: sm[("T2", "tool_joint2", "single")].__setitem__("minutes", 105.0) if c == PRIMARY else None)["P10"] is True
    assert edit_holds(lambda c, sm, cm: sm[("T2", "tool_joint2", "all")].__setitem__("wrong_confident", 0.029) if c == PRIMARY else None)["P6"] is True
    assert edit_holds(lambda c, sm, cm: cm.__setitem__(("T2", "O", "shared"), _cmp(r_min=-0.10)) if c == PRIMARY else None)["P11"] is True


def test_the_decision_follows_the_frozen_rules_and_the_safety_qualifier():
    def dec(h2="NEITHER", h3="NEITHER", unsafe=0):
        def edit(c, sm, cm):
            if c == PRIMARY:
                cm[("T2", "H", "shared")], cm[("T3", "H", "shared")] = _cmp(h2), _cmp(h3)
            cells = [J.Cell("assumed", m, "R0") for m in ("M1", "M2")]
            if c in cells and unsafe > 0:
                k = cells.index(c) * 2
                for j, t in enumerate(J.TIERS):
                    if k + j < unsafe:
                        sm[(t, "tool_joint2", "all")]["wrong_confident"] = 0.045
        return J2.decision2(fake(edit))
    assert dec("IMPROVES", "NEITHER") == "JOINT MACHINERY NOW ADDS VALUE" and dec("IMPROVES", "IMPROVES") == "JOINT MACHINERY NOW ADDS VALUE" and dec("IMPROVES", "TRADE") == "JOINT MACHINERY NOW ADDS VALUE"
    assert dec("IMPROVES", "WORSE") == "THE ROUTINE STILL WINS" and dec("WORSE", "NEITHER") == "THE ROUTINE STILL WINS" and dec("WORSE", "IMPROVES") == "THE ROUTINE STILL WINS"
    assert dec("NEITHER", "NEITHER") == "NO EDGE EITHER WAY" and dec("TRADE", "TRADE") == "NO EDGE EITHER WAY" and dec("NEITHER", "IMPROVES") == "NO EDGE EITHER WAY"
    assert dec("IMPROVES", unsafe=1) == "JOINT MACHINERY NOW ADDS VALUE" and dec("IMPROVES", unsafe=2) == "JOINT MACHINERY NOW ADDS VALUE + UNSAFE UNDER MAP FAULTS"
    assert dec("NEITHER", unsafe=4) == "NO EDGE EITHER WAY + UNSAFE UNDER MAP FAULTS"


# ---------------------------------------------------------------------------------------------- gates
@pytest.mark.skipif(not HAVE_RAW30, reason="Addendum 30's raw results are not on disk")
def test_gate_one_reproduces_addendum_30_and_catches_a_drift_or_a_different_event():
    raw30 = pickle.loads(J2.RAW30.read_bytes())
    res = [J2.run_cell2(i, J.all_cells()[i], 8) for i in (0, 1)]
    ok, detail = J2.gate_g1(res, raw30, 6)
    assert ok and "0 differ" in detail and "[]" in detail
    assert J2.gate_g1(res, None)[0] is False
    bad = pickle.loads(pickle.dumps(res))
    bad[0]["n_compl"][1] += 1
    assert J2.gate_g1(bad, raw30, 6)[0] is False
    drift = pickle.loads(pickle.dumps(raw30))
    drift[0]["pol"][("T2", "tool_joint")]["minutes"][2] += 1.0
    assert J2.gate_g1(res, drift, 6)[0] is False
    drift2 = pickle.loads(pickle.dumps(raw30))
    drift2[1]["pol"][("T3", "tool_ticket_memo")]["correct"][0] += 1.0
    assert J2.gate_g1(res, drift2, 6)[0] is False


def test_gate_two_passes_and_fails_when_the_rule_is_wrong(monkeypatch):
    ok, detail = J2.gate_g2(20)
    assert ok and "static_at_box" in detail and "as registered" in detail
    monkeypatch.setattr(J2, "bears_on_ahu", lambda ck: True)
    assert J2.gate_g2(20)[0] is False
    monkeypatch.undo()
    orig = Jn.JointModel.apply

    def leaky(self, s, o, positive, minutes=None):
        n = orig(self, s, o, positive, minutes)
        if positive is not None and o.kind == "complaint" and o.check.name == "power_24vac":
            n.informed = n.informed | set(self.groups[self.ahu[o.who]])                                   # a wrong rule: any box reading informs the group
        return n
    monkeypatch.setattr(Jn.JointModel, "apply", leaky)
    assert J2.gate_g2(20)[0] is False


def test_gate_two_catches_a_rule_that_changes_the_beliefs(monkeypatch):
    orig = Jn.JointModel.group_stats

    def skewed(self, s, a):
        g = orig(self, s, a)
        if self.group_informing:
            g.W = g.W * np.array([1.0, 1.0 + 1e-6, 1.0])
        return g
    monkeypatch.setattr(Jn.JointModel, "group_stats", skewed)
    assert J2.gate_g2(20)[0] is False


def test_gate_three_replays_and_catches_a_tampered_recording(tiny):
    a30, a31 = tiny
    ok, detail = J2.gate_g3([a31[1]])
    assert ok and "40 replayed events" in detail                                                             # 10 events x 2 tiers x 2 policies
    bad = pickle.loads(pickle.dumps(a31[1]))
    for tier in J.TIERS:
        for pol in ("tool_joint2", "tool_ticket_memo2"):
            for tr in bad["pol"][(tier, pol)]["trace"][:10]:
                if tr:
                    last = list(tr[-1])
                    flip = {"normal": "abnormal", "abnormal": "normal", "yes": "no", "no": "yes"}
                    tr[-1] = tuple(last[:-1]) + (flip[last[-1]],)
    assert J2.gate_g3([bad])[0] is False
    assert J2.gate_g3([a31[0]]) == (True, "0 replayed events: 0 differ")


def test_gate_four_and_five_and_six(tiny):
    a30, a31 = tiny
    assert J2.gate_g4([a31[0]], 8)[0] is True
    bad = pickle.loads(pickle.dumps(a31[0]))
    bad["pol"][("T2", "tool_joint2")]["minutes"][3] += 1.0
    assert J2.gate_g4([bad], 8)[0] is False
    ok, detail = J2.gate_g5([a31[0], a31[1]], expected_idx=[0, 1], n=12)
    assert ok and "2 cells" in detail and J2.gate_g5([a31[0], a31[1]])[0] is False and J2.gate_g5([a31[0], a31[1]], expected_idx=[0, 1], n=13)[0] is False
    miss = pickle.loads(pickle.dumps(a31[0]))
    del miss["pol"][("T3", "tool_joint2_la2")]
    assert J2.gate_g5([miss, a31[1]], expected_idx=[0, 1], n=12)[0] is False
    extra = pickle.loads(pickle.dumps(a31[1]))
    extra["pol"][("T2", "tool_joint2_la2")] = extra["pol"][("T2", "tool_joint2")]
    assert J2.gate_g5([a31[0], extra], expected_idx=[0, 1], n=12)[0] is False
    nan = pickle.loads(pickle.dumps(a31[0]))
    nan["pol"][("T2", "tool_joint2")]["minutes"][0] = np.nan
    assert J2.gate_g5([nan, a31[1]], expected_idx=[0, 1], n=12)[0] is False
    assert J2.gate_g6([a31[0], a31[1]], list(a30.values()))[0] is True
    other = pickle.loads(pickle.dumps(a31[0]))
    other["tag"] = (0.0,) * 10
    assert J2.gate_g6([other])[0] is False and J2.gate_g6([a31[0]], [dict(tag=(1,))])[0] is False


# ---------------------------------------------------------------------------------------------- the script
@pytest.mark.skipif(not HAVE_RAW30, reason="Addendum 30's raw results are not on disk")
def test_the_smoke_run_writes_the_report_and_regenerates_from_the_pickle(tmp_path, capsys):
    S75.main(["--smoke", "--out", str(tmp_path), "--workers", "1"])
    out = capsys.readouterr().out
    assert "G1 PASS" in out and "G6 PASS" in out and "FAIL" not in out
    text = (tmp_path / "joint2_report.md").read_text()
    assert "SMOKE RUN" in text and "## Gates" in text and "tool_joint2_la2" in text and "Frozen decision" not in text and "joint2 - ticket_memo2" in text
    for f in ("joint2_raw.pkl", "joint2_analysis.pkl", "joint2_cells.csv"):
        assert (tmp_path / f).exists()
    assert (tmp_path / "joint2_cells.csv").read_text().splitlines()[0].startswith("cell,shared,map,rel,tier,policy,subset")
    S75.main(["--smoke", "--out", str(tmp_path), "--from-pickle"])
    assert "G1 PASS" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        S75.main(["--smoke", "--out", str(tmp_path), "--raw30", str(tmp_path / "missing.pkl")])


def test_the_report_shows_no_result_when_a_gate_fails_and_predictions_only_with_all_cells():
    an = fake(_all_hold)
    text = S75.report(an, {"G1 regression": (False, "broken")}, True, 100, 1.0)
    assert "NO RESULT" in text and "Primary cell" not in text
    full = S75.report(an, {"G1 regression": (True, "ok")}, True, 100, 1.0)
    assert "## Predictions" in full and "| P1 | holds |" in full and "Frozen decision: " in full and "P11" in full
    assert "## Predictions" not in S75.report(an[:2], {"G1 regression": (True, "ok")}, True, 100, 1.0)


# ---------------------------------------------------------------------------------------------- further guards
def test_the_session_passes_both_switches_to_the_model():
    cs = cases_for("T2", [0, 1])
    d = JointSession(cs)
    assert (d.model.group_informing, d.model.scale_audience) == (False, True)
    assert (JointSession(cs, group_informing=True).model.group_informing, JointSession(cs, group_informing=True).model.scale_audience) == (True, True)
    assert (JointSession(cs, scale_audience=False).model.group_informing, JointSession(cs, scale_audience=False).model.scale_audience) == (False, False)
    assert JointSession(cs, lookahead=2, group_informing=True, scale_audience=False).lookahead == 2


def test_each_policy_builds_its_registered_configuration(monkeypatch):
    seen = []
    orig = P.JointSession

    class Spy(orig):
        def __init__(self, cases, js=None, lookahead=1, max_checks=None, group_informing=False, scale_audience=True):
            seen.append((lookahead, group_informing, scale_audience))
            super().__init__(cases, js, lookahead, max_checks, group_informing, scale_audience)
    monkeypatch.setattr(P, "JointSession", Spy)
    cs, ctx = cases_for("T3", [0, 1]), [W.context_dict("T3", r) for r in (0, 1)]
    ev = state_event(2, "low_static")
    want = {"tool_joint": (1, False, True), "tool_joint_la2": (2, False, True), "tool_joint2": (1, True, True), "tool_joint2_la2": (2, True, True), "tool_joint3": (1, True, False)}
    for pol, cfg in want.items():
        seen.clear()
        P.run_policy(pol, cs, Modal(ev), ctx)
        assert seen == [cfg], (pol, seen)
    modes = []
    orig_rt = P.run_ticket
    monkeypatch.setattr(P, "run_ticket", lambda cases, oracle, mode, js=None: (modes.append(mode), orig_rt(cases, oracle, mode, js))[1])
    for pol, mode in (("tool_ticket", "plain"), ("tool_ticket_nb", "nb"), ("tool_ticket_memo", "memo"), ("tool_ticket_memo2", "memo2")):
        modes.clear()
        P.run_policy(pol, cs, Modal(ev), ctx)
        assert modes == [mode]


def test_memo2_never_asks_an_air_handler_twice_and_carries_the_static_to_the_right_air_handler_only():
    cs = cases_for("T3", list(range(7)))
    orc = Modal(state_event(7, "ahu_fan_off"))
    P.run_ticket(cs, orc, "memo2")
    asked = [c[1:] for c in orc.calls if c[0] == "ahu"]
    assert asked and len(asked) == len(set(asked))
    ev = W.Event(0, 0, {"AHU-0": "ok", "AHU-1": "low_static", "AHU-2": "ok"}, {f"VAV-{b}": f"AHU-{b // 8}" for b in range(24)}, [9, 10, 0], [LOW, LOW, ("damper_mech",)], ["AHU-1", "AHU-1", "AHU-0"])
    cs = cases_for("T2", [9, 10, 0])
    orig = P.PriorSession
    Spy, log = _spy_sessions()
    P.PriorSession = Spy
    try:
        P.run_ticket(cs, Modal(ev), "memo2")
    finally:
        P.PriorSession = orig
    starts = [[(o.check, o.target, o.outcome) for o in s.start] for s in log]
    assert starts[0] == [] and ("static_at_box", "VAV-10", "abnormal") in starts[1] and not any(x[0] == "static_at_box" for x in starts[2])


def test_the_prediction_boundaries_for_the_safety_accuracy_and_look_ahead_predictions(monkeypatch):
    monkeypatch.setattr(J2, "P6_BAR", 0.5)
    monkeypatch.setattr(J2, "P7_BAR", 0.25)
    monkeypatch.setattr(J2, "P8_BAR", 0.25)
    def edit(fn):
        return holds(fake(lambda c, sm, cm: (_all_hold(c, sm, cm), fn(c, sm, cm))))
    for t in J.TIERS:
        pass
    got = edit(lambda c, sm, cm: [sm[(t, "tool_joint", "all")].__setitem__("wrong_confident", 0.25) or sm[(t, "tool_joint2", "all")].__setitem__("wrong_confident", 0.75) for t in J.TIERS] if c == PRIMARY else None)
    assert got["P6"] is True                                                                              # exactly the bar above: "at most"
    got = edit(lambda c, sm, cm: [sm[(t, "tool_joint", "all")].__setitem__("accuracy", 0.75) or sm[(t, "tool_joint2", "all")].__setitem__("accuracy", 0.5) for t in J.TIERS] if c == PRIMARY else None)
    assert got["P7"] is True                                                                              # exactly the bar below: "at least"
    def p8(c, sm, cm):
        if c == J.Cell("assumed", "M1", "R0"):
            sm[("T2", "tool_joint2", "all")]["wrong_confident"] = 0.5
            sm[("T2", "tool_ticket_memo2", "all")]["wrong_confident"] = 0.25
    assert edit(p8)["P8"] is False                                                                        # exactly the bar: "less than"


def test_the_look_ahead_prediction_needs_two_of_three_cells_per_tier():
    def with_improves(n_cells):
        def e(c, sm, cm):
            _all_hold(c, sm, cm)
            if c.has_lookahead:
                cells = [J.Cell(s, "M0", "R0") for s in J.LEVELS["shared"]][:n_cells]
                if c in cells:
                    cm[("T2", "M", "shared")] = _cmp("IMPROVES", "FASTER")
        return holds(fake(e))["P9"]
    assert with_improves(0) is True and with_improves(1) is True and with_improves(2) is False


def test_gate_two_catches_a_rule_that_informs_less_or_changes_beliefs_in_ways_the_semantics_checks_do_not_see(monkeypatch):
    orig = Jn.JointModel.apply

    def forgetful(self, s, o, positive, minutes=None):
        n = orig(self, s, o, positive, minutes)
        if self.group_informing and o.check.name not in ("static_at_box", "power_24vac", "ahu_visit"):
            n.informed = s.informed                                                                        # readings that inform nobody, on checks the fixed semantic checks never use
        return n
    monkeypatch.setattr(Jn.JointModel, "apply", forgetful)
    assert J2.gate_g2(60)[0] is False
    monkeypatch.undo()

    def skew(self, s, o, positive, minutes=None):
        n = orig(self, s, o, positive, minutes)
        if self.group_informing and o.kind == "complaint" and positive is not None:
            n.lik[o.who] = n.lik[o.who] ** 2                                                               # the state and the tables stay consistent: only the rule-off comparison sees it
        return n
    monkeypatch.setattr(Jn.JointModel, "apply", skew)
    assert J2.gate_g2(60)[0] is False


def test_gate_four_notices_a_change_in_the_events(tiny):
    a30, a31 = tiny
    bad = pickle.loads(pickle.dumps(a31[0]))
    bad["n_compl"][2] += 1
    assert J2.gate_g4([bad], 8)[0] is False
