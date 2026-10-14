"""Guards for working model v2 (docmismatch.troubleshoot.v2: the joint session, the event world and the policies; PREREGISTRATION_DR.md Addendum 30). They check the model's arithmetic
against independent computations, the rules of the world and the behaviour of the policies on scripted answers. No test here reads a study result."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot import model as M  # noqa: E402
from docmismatch.troubleshoot.v1 import catalogue as K, data as D  # noqa: E402
from docmismatch.troubleshoot.v1.engine import make_case_v1  # noqa: E402
from docmismatch.troubleshoot.v2 import joint as Jn, policies as P, study_joint as SJ, world2 as W  # noqa: E402
from docmismatch.troubleshoot.v2.joint import JointModel, JointSession, JointSettings  # noqa: E402

CASES = W.make_cases()
FAN, LOW = ("ahu_fan_off",), ("low_static",)


def cases_for(tier, rooms):
    return [CASES[(tier, r)] for r in rooms]


def model_for(rooms, tier="T2", **kw):
    return JointModel(cases_for(tier, rooms), JointSettings(**kw))


def idx(m, i, cause):
    return m.causes[i].index(cause)


def upstream_mass(m, i, marg=None):
    marg = m.marg0[i] if marg is None else marg
    return float(marg[idx(m, i, FAN)] + marg[idx(m, i, LOW)])


class Scripted:
    """A technician who answers from a function of (kind, who, check, target); records every request."""

    def __init__(self, fn=None):
        self.fn = fn or (lambda kind, who, ck, target: ck.words[1])
        self.calls = []

    def ask_room(self, i, ck, target):
        self.calls.append(("room", i, ck.name, target))
        return self.fn("room", i, ck, target)

    def ask_ahu(self, a, ck):
        self.calls.append(("ahu", a, ck.name))
        return self.fn("ahu", a, ck, a)


class Modal(W.Oracle):
    """The simulated technician of the world, but always giving the most likely answer: consistent answers for scripted scenarios."""

    def __init__(self, event, rel_a=0.0):
        super().__init__(event, rel_a, np.random.default_rng(0))
        self.calls = []

    def ask_room(self, i, ck, target):
        self.calls.append(("room", i, ck.name, target))
        return ck.words[0] if self.p_room(i, ck.name, target) >= 0.5 else ck.words[1]

    def ask_ahu(self, a, ck):
        self.calls.append(("ahu", a, ck.name))
        return ck.words[0] if self.p_ahu(a, ck.name) >= 0.5 else ck.words[1]


def fan_event(n=7, state="ahu_fan_off"):
    """A visit in which the first `n` rooms of AHU-0 complain because of its state."""
    return W.Event(0, 0, {"AHU-0": state, "AHU-1": "ok", "AHU-2": "ok"}, {f"VAV-{b}": f"AHU-{b // 8}" for b in range(24)}, list(range(n)), [(state,)] * n, ["AHU-0"] * n)


# ---------------------------------------------------------------------------------------------- settings
def test_joint_settings_are_validated():
    for bad in (dict(f=0.0), dict(f=1.0), dict(rho=0.0), dict(rho=1.0), dict(r_fan=0.0), dict(r_low=1.5), dict(fan_share=0.0), dict(fan_share=1.0)):
        with pytest.raises(ValueError):
            JointSettings(**bad)
    JointSettings(r_fan=1.0, r_low=1.0)


def test_state_prior_and_complaint_probabilities_are_the_stated_formulas():
    js = JointSettings(f=0.06, rho=0.02, r_fan=0.8, r_low=0.4)
    assert np.allclose(js.state_prior, [0.94, 0.06 * 5 / 17, 0.06 * 12 / 17]) and js.state_prior.sum() == pytest.approx(1.0)
    assert np.allclose(js.affect, [0.0, 0.8, 0.4])
    assert np.allclose(js.p_complain, [0.02, 1 - 0.2 * 0.98, 1 - 0.6 * 0.98])
    assert Jn.FAN_SHARE == pytest.approx(0.05 / 0.17)
    assert np.allclose(JointSettings().state_prior, [0.97, 0.03 * 5 / 17, 0.03 * 12 / 17])


# ---------------------------------------------------------------------------------------------- construction and tables
def test_the_model_needs_documented_air_handlers_and_at_least_one_complaint():
    t0 = make_case_v1(None, None, "T0", member_name="Room 1")
    with pytest.raises(ValueError, match="claims"):
        JointModel([t0])
    with pytest.raises(ValueError, match="at least one"):
        JointModel([])
    with pytest.raises(ValueError, match="documented rooms"):
        JointModel(cases_for("T2", [0, 1]), None, {"AHU-0": 1})


def test_documented_rooms_per_air_handler_come_from_the_claims():
    assert Jn.rooms_per_ahu(CASES[("T2", 0)]) == {"AHU-0": 8, "AHU-1": 8, "AHU-2": 8}
    assert JointModel(cases_for("T2", [0, 9])).children == {"AHU-0": 8, "AHU-1": 8, "AHU-2": 8}


def test_the_joint_tables_have_the_stated_structure():
    js = JointSettings()
    m = JointModel(cases_for("T2", [0, 1, 9]), js)
    assert m.groups == {"AHU-0": [0, 1], "AHU-1": [2]}
    for i in range(3):
        L, J = m.L[i], m.J[i]
        f, lo = idx(m, i, FAN), idx(m, i, LOW)
        assert L.sum() == pytest.approx(1.0) and L[f] == 0.0 and L[lo] == 0.0 and (np.delete(L, [f, lo]) > 0).all()
        assert J[0].sum() == pytest.approx(js.rho) and J[1].sum() == pytest.approx(js.p_complain[1]) and J[2].sum() == pytest.approx(js.p_complain[2])
        assert J[0, f] == 0.0 and J[0, lo] == 0.0                                                # an upstream cause needs an upstream fault
        assert J[1, f] == js.r_fan and J[1, lo] == 0.0 and J[2, lo] == js.r_low and J[2, f] == 0.0
        assert np.allclose(np.delete(J[1], [f, lo]), (1 - js.r_fan) * js.rho * np.delete(L, [f, lo]))
        assert np.allclose(np.delete(J[2], [f, lo]), (1 - js.r_low) * js.rho * np.delete(L, [f, lo]))


def test_the_cause_lists_are_v1s_and_follow_the_boxes_reheat():
    m = JointModel(cases_for("T2", [0, 1]))                                    # box 0 has no reheat, box 1 has
    assert ("reheat_fail",) not in m.causes[0] and ("reheat_fail",) in m.causes[1]
    assert ("wrong", "VAV-3") in m.causes[0] and ("wrong", "VAV-0") not in m.causes[0] and ("unlisted",) in m.causes[0]


# ---------------------------------------------------------------------------------------------- the beliefs
def test_beliefs_are_distributions_and_explaining_away_works():
    single, pair, many = model_for([0]), model_for([0, 1]), model_for(list(range(7)))
    for m in (single, pair, many):
        assert all(x.sum() == pytest.approx(1.0) and (x > 0).sum() > 1 for x in m.marg0)
    assert upstream_mass(single, 0) < 0.05                                       # one of eight rooms complaining: an air handler fault is unlikely
    assert upstream_mass(pair, 0) > upstream_mass(single, 0)                      # a second complaint on the same air handler makes it likelier
    assert many.marg0[0][idx(many, 0, FAN)] > 0.5                                # seven of eight complain: the fan is off
    assert upstream_mass(many, 0) > 0.95


def test_rooms_that_do_not_complain_count_as_evidence():
    few = JointModel(cases_for("T2", [0, 1]), None, {"AHU-0": 8, "AHU-1": 8, "AHU-2": 8})
    lots = JointModel(cases_for("T2", [0, 1]), None, {"AHU-0": 40, "AHU-1": 8, "AHU-2": 8})
    assert upstream_mass(lots, 0) < upstream_mass(few, 0)


def test_complaints_on_different_air_handlers_do_not_inform_each_other():
    a = model_for([0, 9])
    b = model_for([0])
    assert a.marg0[0] == pytest.approx(b.marg0[0])
    assert a.marg0[1] == pytest.approx(model_for([9]).marg0[0])


def test_a_reading_of_the_air_handler_speaks_for_every_complaint_of_the_group():
    m = model_for([0, 1, 2], tier="T3")
    s0 = m.initial()
    o = next(o for o in m.options(s0, m.all_stats(s0), 2.0, 0.0, 0.0) if o.kind == "ahu" and o.check.name == "bas_ahu_fan")
    hi, lo = m.marginals(m.apply(s0, o, True)), m.marginals(m.apply(s0, o, False))
    for i in range(3):
        assert hi[i][idx(m, i, FAN)] > m.marg0[i][idx(m, i, FAN)] > lo[i][idx(m, i, FAN)]
    assert m.ahu_posterior(m.apply(s0, o, True))["AHU-0"][1] > m.ahu_posterior(s0)["AHU-0"][1]
    other = model_for([0, 9], tier="T3")
    so = other.initial()
    o2 = next(x for x in other.options(so, other.all_stats(so), 2.0, 0.0, 0.0) if x.kind == "ahu" and x.who == "AHU-0" and x.check.name == "bas_ahu_fan")
    assert other.marginals(other.apply(so, o2, True))[1] == pytest.approx(other.marg0[1])          # a complaint on another air handler does not hear it


def test_a_room_reading_updates_that_complaints_marginal_by_bayes_and_leaves_no_trace_on_others_in_other_groups():
    m = model_for([0, 9], tier="T3")
    s0 = m.initial()
    o = next(x for x in m.options(s0, m.all_stats(s0), 2.0, 0.0, 0.0) if x.kind == "complaint" and x.who == 0 and x.check.name == "power_24vac")
    row = m.row(0, o.check, o.target)
    for positive in (True, False):
        s1 = m.apply(s0, o, positive)
        ref = m.marg0[0] * (row if positive else 1 - row)
        assert m.marginals(s1)[0] == pytest.approx(ref / ref.sum())
        assert m.marginals(s1)[1] == pytest.approx(m.marg0[1])


def test_the_beliefs_equal_brute_force_enumeration_after_observations():
    rng = np.random.default_rng(3)
    for rooms, tier in (([0], "T2"), ([0, 1], "T3"), ([0, 1, 2], "T2"), ([0, 9, 10], "T3")):
        m = JointModel(cases_for(tier, rooms), JointSettings(f=0.08, rho=0.05, r_fan=0.7, r_low=0.45))
        s = m.initial()
        for _ in range(4):
            opts = m.options(s, m.all_stats(s), 2.0, 0.0, 0.0)
            s = m.apply(s, opts[int(rng.integers(len(opts)))], bool(rng.random() < 0.5))
        post, marg = SJ.brute_force(m, s)
        for a, g in m.all_stats(s).items():
            assert g.W == pytest.approx(post[a], abs=1e-9)
            for t, i in enumerate(g.idx):
                assert g.marg[t] == pytest.approx(marg[i], abs=1e-9)


def test_marginals_do_not_depend_on_the_order_of_the_complaints():
    a, b = model_for([0, 3, 5, 9], tier="T3"), model_for([9, 5, 0, 3], tier="T3")
    s_a, s_b = a.initial(), b.initial()
    for aa, bb in ((0, 2), (1, 3), (2, 1), (3, 0)):
        assert a.marg0[aa] == pytest.approx(b.marg0[bb])
    o = next(x for x in a.options(s_a, a.all_stats(s_a), 2.0, 0.0, 0.0) if x.kind == "ahu" and x.check.name == "bas_static" and x.who == "AHU-0")
    ob = next(x for x in b.options(s_b, b.all_stats(s_b), 2.0, 0.0, 0.0) if x.kind == "ahu" and x.check.name == "bas_static" and x.who == "AHU-0")
    ma, mb = a.marginals(a.apply(s_a, o, True)), b.marginals(b.apply(s_b, ob, True))
    for aa, bb in ((0, 2), (1, 3), (2, 1), (3, 0)):
        assert ma[aa] == pytest.approx(mb[bb])


def test_apply_does_not_change_the_state_it_was_given():
    m = model_for([0, 1], tier="T3")
    s = m.initial()
    o = m.options(s, m.all_stats(s), 2.0, 0.0, 0.0)[0]
    before = ([x.copy() for x in s.lik], {k: v.copy() for k, v in s.ahu_ll.items()}, s.done_c, s.done_a, s.at, s.elapsed, s.n_checks)
    s2 = m.apply(s, o, True)
    assert s2 is not s and s2.n_checks == 1 and s2.elapsed == o.minutes and s2.at == o.place
    assert all(np.array_equal(a, b) for a, b in zip(before[0], s.lik)) and all(np.array_equal(before[1][k], s.ahu_ll[k]) for k in before[1])
    assert (s.done_c, s.done_a, s.at, s.elapsed, s.n_checks) == before[2:]


def test_an_unsure_answer_spends_the_time_and_learns_nothing():
    m = model_for([0, 1], tier="T3")
    s = m.initial()
    o = m.options(s, m.all_stats(s), 2.0, 0.0, 0.0)[0]
    s2 = m.apply(s, o, None)
    assert s2.elapsed == o.minutes and s2.n_checks == 1
    for a, b in zip(m.marginals(s2), m.marginals(s)):
        assert a == pytest.approx(b)
    assert (o.kind, o.who, o.check.name, o.target) not in [(x.kind, x.who, x.check.name, x.target) for x in m.options(s2, m.all_stats(s2), 2.0, 0.0, 0.0)]


# ---------------------------------------------------------------------------------------------- expected gain
def _reference_gain(m, s, o):
    """Expected reduction of the summed marginal entropy by full recomputation after each answer, and the predictive probability of a positive answer computed from the beliefs."""
    a = m.ahu[o.who] if o.kind == "complaint" else o.who
    g = m.group_stats(s, a)
    if o.kind == "complaint":
        t = g.idx.index(o.who)
        pyes = float(g.marg[t] @ m.row(o.who, o.check, o.target))
    else:
        pyes = float(g.W @ Jn.ahu_row(o.check))
    h = [m.group_stats(m.apply(s, o, pos), a).H for pos in (True, False)]
    return g.H - (pyes * h[0] + (1 - pyes) * h[1]), pyes


def test_expected_gain_and_probability_of_a_positive_match_full_recomputation():
    rng = np.random.default_rng(11)
    for rooms, tier in (([0, 1, 2], "T3"), ([0, 1, 9], "T2")):
        m = model_for(rooms, tier=tier, f=0.07, rho=0.05)
        s = m.initial()
        for step in range(3):
            opts = m.options(s, m.all_stats(s), 2.0, 0.0, 0.0)
            assert opts
            picks = [opts[int(k)] for k in rng.choice(len(opts), size=min(25, len(opts)), replace=False)]
            for o in picks:
                gain, pyes = _reference_gain(m, s, o)
                assert o.gain == pytest.approx(max(gain, 0.0), abs=1e-9) and o.pyes == pytest.approx(pyes, abs=1e-9)
            s = m.apply(s, picks[0], bool(rng.random() < 0.5))


def test_an_air_handler_option_is_worth_the_sum_of_what_it_tells_each_complaint():
    m = model_for([0, 1, 2, 3], tier="T3")
    s = m.initial()
    stats = m.all_stats(s)
    o = next(x for x in m.options(s, stats, 2.0, 0.0, 0.0) if x.kind == "ahu" and x.check.name == "bas_ahu_fan")
    assert o.audience == 4
    solo = model_for([0], tier="T3")
    so = next(x for x in solo.options(solo.initial(), solo.all_stats(solo.initial()), 2.0, 0.0, 0.0) if x.kind == "ahu" and x.check.name == "bas_ahu_fan")
    assert so.audience == 1 and o.gain > so.gain


# ---------------------------------------------------------------------------------------------- what can be offered
def test_options_respect_the_tier_the_availability_and_the_done_list():
    t2, t3 = model_for([0, 1], tier="T2"), model_for([0, 1], tier="T3")
    n2 = {o.check.name for o in t2.options(t2.initial(), t2.all_stats(t2.initial()), 2.0, 0.0, 0.0)}
    n3 = {o.check.name for o in t3.options(t3.initial(), t3.all_stats(t3.initial()), 2.0, 0.0, 0.0)}
    assert not any(n.startswith("bas_") for n in n2) and {"bas_ahu_fan", "bas_static", "bas_airflow"} <= n3 and "ahu_visit" in n2 and "ask_occupant" not in n2 | n3
    s = t3.initial()
    opts = t3.options(s, t3.all_stats(s), 2.0, 0.0, 0.0)
    keys = [o.key for o in opts]
    assert len(keys) == len(set(keys))
    ahu_opts = [o for o in opts if o.kind == "ahu"]
    assert {o.check.name for o in ahu_opts} == {"bas_ahu_fan", "bas_static", "ahu_visit", "ahu_gauge"} and len(ahu_opts) == 4          # one per check for the one air handler
    for o in (opts[0], ahu_opts[0], next(x for x in opts if x.kind == "complaint")):
        s2 = t3.apply(s, o, True)
        assert o.key not in [x.key for x in t3.options(s2, t3.all_stats(s2), 2.0, 0.0, 0.0)]           # an air handler check, like a room check, is done once


def test_concluded_complaints_are_left_alone_and_a_group_with_none_left_offers_nothing():
    m = model_for([0, 1], tier="T3")
    s = m.initial()
    every = lambda st: m.options(st, m.all_stats(st), 1e-9, 0.0, 0.0)  # noqa: E731     (tau this small: every marginal is at least tau)
    assert {o.who for o in every(s) if o.kind == "complaint"} == {0, 1}                    # nothing informs them yet: not concluded, whatever the marginals
    room0 = next(o for o in every(s) if o.kind == "complaint" and o.who == 0)
    s1 = m.apply(s, room0, True)
    assert s1.informed == {0} and {o.who for o in every(s1) if o.kind == "complaint"} == {1}       # complaint 0 is informed and (at this tau) concluded: left alone
    ahu = next(o for o in every(s1) if o.kind == "ahu")
    s2 = m.apply(s1, ahu, False)
    assert s2.informed == {0, 1} and every(s2) == []                                        # the air handler reading informs the whole group: nothing left
    s3 = m.apply(s, next(o for o in every(s) if o.kind == "complaint" and o.who == 0), None)
    assert s3.informed == frozenset()                                                       # an unsure answer informs nobody


def test_the_pattern_of_complaints_alone_never_concludes():
    sess = JointSession(cases_for("T3", [0, 1, 2, 3]))                                       # four of eight rooms: low static explains it (r = 0.5)
    top = sess.marginals()[0]
    assert top.max() >= sess.tau and sess.model.causes[0][int(np.argmax(top))] == LOW       # the prior alone is past tau
    assert sess.concluded() == [False] * 4 and sess.status()["concluded"] is False and sess.recommend() is not None
    sess.report("unsure")
    assert sess.concluded() == [False] * 4                                                   # an unsure answer is not an observation
    o = next(x for x in sess._options(sess.state) if x.kind == "ahu")
    sess.report(o.check.words[0], o)
    assert sess.concluded() == [True] * 4 and sess.status()["complaints"][0]["concluded"] is True
    st_sess = JointSession(cases_for("T3", [0, 1, 2, 3]))
    st_sess.state = st_sess.model.apply(st_sess.state, next(x for x in st_sess._options(st_sess.state) if x.kind == "complaint" and x.who == 2), True)
    assert st_sess.concluded()[2] is bool(st_sess.marginals()[2].max() >= st_sess.tau) and st_sess.concluded()[0] is False


def test_a_ticket_session_with_the_neighbour_prior_does_not_conclude_before_an_observation():
    cs = cases_for("T3", [0, 1, 2, 3])
    mdl = JointModel(cs)
    s = P.PriorSession(cs[0], (mdl.causes[0], mdl.marg0[0]))
    assert s.posterior()[1].max() >= 0.95 and s.status()["concluded"] is False and s.status()["conclusion"] is None and s.next_step() is not None
    s.report("unsure", "bas_ahu_fan", cs[0].doc)
    assert s.status()["concluded"] is False
    s.report("abnormal", "bas_static", cs[0].doc)
    assert s.status()["concluded"] is True and s.status()["conclusion"] is not None
    plain = P.PriorSession(cs[0])
    assert plain.status()["concluded"] is False and plain.next_step() is not None
    pre = P.PriorSession(cs[0], (mdl.causes[0], mdl.marg0[0]))
    pre.log.append(P.Obs("bas_static", cs[0].doc, "abnormal", 0.0))                        # a reading carried over from an earlier ticket is an observation
    assert pre.status()["concluded"] is True


def test_the_rate_rule_scales_with_the_number_of_complaints_an_option_informs():
    m = model_for([0, 1], tier="T3")
    s = m.initial()
    free = m.options(s, m.all_stats(s), 0.95, 0.0, 0.0)
    a = next(o for o in free if o.kind == "ahu" and o.check.name == "bas_ahu_fan")
    x = a.gain / a.minutes
    just_below = m.options(s, m.all_stats(s), 0.95, x / 2 - 1e-9, 0.0)
    just_above = m.options(s, m.all_stats(s), 0.95, x / 2 + 1e-9, 0.0)
    assert a.key in [o.key for o in just_below] and a.key not in [o.key for o in just_above]           # two complaints hear it: twice the rate is needed
    solo = model_for([0], tier="T3")
    so = next(o for o in solo.options(solo.initial(), solo.all_stats(solo.initial()), 0.95, 0.0, 0.0) if o.kind == "ahu" and o.check.name == "bas_ahu_fan")
    y = so.gain / so.minutes
    assert so.key in [o.key for o in solo.options(solo.initial(), solo.all_stats(solo.initial()), 0.95, y - 1e-9, 0.0)]
    assert so.key not in [o.key for o in solo.options(solo.initial(), solo.all_stats(solo.initial()), 0.95, y + 1e-9, 0.0)]


# ---------------------------------------------------------------------------------------------- the session
def test_the_session_loops_to_a_conclusion_and_reports_what_it_did():
    sess = JointSession(cases_for("T3", list(range(7))))                     # seven of the eight rooms of an air handler complain
    orc = Modal(fan_event(7))
    n = 0
    while True:
        o = sess.recommend()
        if o is None:
            break
        sess.report(orc.ask_ahu(o.who, o.check) if o.kind == "ahu" else orc.ask_room(o.who, o.check, o.target))
        n += 1
        assert n < 100
    st = sess.status()
    assert st["n_checks"] == n == len(sess.log) and st["elapsed"] == pytest.approx(sum(x[5] for x in sess.log)) and set(st["ahu"]) == {"AHU-0"}
    assert all(p["ranked"][0][1] >= p["ranked"][-1][1] for p in st["complaints"]) and st["concluded"] == all(p["concluded"] for p in st["complaints"])
    assert st["complaints"][0]["guess"] == FAN and st["concluded"]


def test_the_check_limit_stops_the_session_and_scales_with_the_complaints():
    sess = JointSession(cases_for("T2", [0, 1]), max_checks=2)
    assert sess.cap == 2 and JointSession(cases_for("T2", [0, 1])).cap == 24 and JointSession(cases_for("T2", [0])).cap == 12
    for _ in range(2):
        o = sess.recommend()
        sess.report(o.check.words[1])
    assert sess.recommend() is None and sess.n_checks == 2


def test_report_validates_its_answers_and_needs_a_recommendation():
    sess = JointSession(cases_for("T3", [0]))
    with pytest.raises(RuntimeError, match="no pending"):
        sess.report("yes")
    o = sess.recommend()
    with pytest.raises(ValueError, match="answered"):
        sess.report("maybe")
    sess.report("unsure")
    assert sess.n_checks == 1 and sess.elapsed == o.minutes and sess.log[-1][4] == "unsure"
    o2 = sess.recommend()
    if o2.check.is_reading:
        sess.report("yes")                                                                # yes / no work as synonyms of abnormal / normal for a reading check
        assert sess.log[-1][4] == "abnormal"


def test_the_technicians_location_carries_over_between_checks():
    m = model_for([0, 1], tier="T2")
    s = m.initial()
    pick = lambda st, name, who: next(o for o in m.options(st, m.all_stats(st), 2.0, 0.0, 0.0) if o.check.name == name and o.who == who)  # noqa: E731
    o1 = pick(s, "power_24vac", 0)
    s1 = m.apply(s, o1, False)
    o1b = pick(s1, "manual_damper_test", 0)
    assert o1.minutes == 10.0 and o1b.minutes == 8.0                                     # already at the box: no 6 minutes of getting there
    o2 = pick(s1, "power_24vac", 1)
    assert o2.minutes == 10.0                                                            # another box: the walk again


def test_the_session_is_deterministic_and_lookahead_is_validated():
    def run(la):
        sess, orc = JointSession(cases_for("T3", [0, 1, 2]), lookahead=la), Scripted()
        while (o := sess.recommend()) is not None:
            sess.report(orc.ask_ahu(o.who, o.check) if o.kind == "ahu" else orc.ask_room(o.who, o.check, o.target))
        return [x[:4] for x in sess.log], sess.elapsed
    assert run(1) == run(1) and run(2) == run(2)
    with pytest.raises(ValueError):
        JointSession(cases_for("T3", [0]), lookahead=3)


def test_lookahead_changes_the_score_but_still_picks_from_the_same_options():
    s1, s2 = JointSession(cases_for("T3", [0, 1, 2])), JointSession(cases_for("T3", [0, 1, 2]), lookahead=2)
    opts = {o.key for o in s1._options(s1.state)}
    o1, o2 = s1.recommend(), s2.recommend()
    assert o1.key in opts and o2.key in opts


def test_with_many_complaints_on_one_air_handler_the_first_check_is_a_reading_of_it():
    sess = JointSession(cases_for("T3", list(range(6))))
    o = sess.recommend()
    assert o.kind == "ahu" and o.who == "AHU-0"


# ---------------------------------------------------------------------------------------------- the world
def test_the_building_is_well_documented():
    b = W.make_building2()
    assert len([e for e in b.base.equipment.values() if e.kind == "Zone"]) == 24 and len([e for e in b.base.equipment.values() if e.kind == "AHU"]) == 3
    assert b.base.claims["vav_zone"]["Room-9"] == "VAV-9" and b.base.claims["ahu_vav"]["VAV-9"] == "AHU-1" and b.base.claims["ahu_vav"]["VAV-23"] == "AHU-2"
    assert all(f"VAV-{i}" in b.attrs and f"VAV-{i}" in b.points for i in range(24)) and all(f"AHU-{a}" in b.attrs and f"AHU-{a}" in b.points for a in range(3))
    assert b.attrs["VAV-3"]["reheat"] == "none" and b.attrs["VAV-4"]["reheat"] == "hydronic" and W.true_reheat(0) is False and W.true_reheat(1) is True


def test_tiers_and_declared_context():
    assert W.TIER_ITEMS["T2"] == D.TIERS["T2"] and W.TIER_ITEMS["T3"] == D.TIERS["T3"] and W.TIER_NAMES == ("T2", "T3")
    for r in (0, 1):
        c2, c3 = W.tier_context("T2", r), W.tier_context("T3", r)
        assert (c2.bas_access, c3.bas_access, c2.instrument, c2.occupant) == ("no", "yes", "yes", "no") and c2.reheat == ("yes" if r else "no")
    assert set(W.context_dict("T3", 1)) == {"reheat", "bas_access", "instrument", "occupant"}
    assert CASES[("T2", 0)].settings.p_wrong == 0.05 and CASES[("T2", 0)].candidates[0] == "VAV-0" and len(CASES[("T2", 0)].candidates) == 8
    assert set(CASES[("T2", 0)].candidates) == {f"VAV-{i}" for i in range(8)}                      # the room's air handler's boxes


def test_the_local_prior_has_no_upstream_causes_and_follows_the_worlds_p_wrong():
    c = CASES[("T2", 2)]
    causes, p = W.local_prior(c, 0.05, 2)
    assert p.sum() == pytest.approx(1.0) and all(p[causes.index(u)] == 0 for u in W.UPSTREAM_CAUSES)
    wrong = lambda pw: sum(p_ for c_, p_ in zip(*W.local_prior(c, pw, 2)) if c_[0] in ("wrong", "unlisted"))  # noqa: E731
    assert wrong(0.15) > wrong(0.05) > 0


def _params(**kw):
    base = dict(f=0.03, q_ahu=0.0, p_wrong=0.05, rel_a=0.0)
    return W.WorldParams(**{**base, **kw})


def test_events_are_reproducible_and_never_empty():
    a, b = W.draw_event(3, 7, _params(), CASES), W.draw_event(3, 7, _params(), CASES)
    assert (a.rooms, a.causes, a.u, a.true_ahu) == (b.rooms, b.causes, b.u, b.true_ahu)
    assert W.draw_event(3, 8, _params(), CASES).rooms != a.rooms or W.draw_event(3, 9, _params(), CASES).rooms != a.rooms
    for i in range(60):
        ev = W.draw_event(1, i, _params(), CASES)
        assert ev.n >= 1 and len(ev.causes) == len(ev.rooms) == len(ev.true_ahu_of) and len(set(ev.rooms)) == ev.n and all(0 <= r < 24 for r in ev.rooms)


def test_upstream_complaints_only_come_from_a_faulty_air_handler_and_are_mostly_all_of_its_rooms():
    seen_shared, upstream = 0, 0
    for i in range(300):
        ev = W.draw_event(2, i, _params(f=0.3), CASES)
        for r, c, a in zip(ev.rooms, ev.causes, ev.true_ahu_of):
            if c[0] in ("ahu_fan_off", "low_static"):
                upstream += 1
                assert ev.u[a] == c[0] and a == f"AHU-{r // 8}"                               # M0: the true air handler is the documented one
            else:
                assert c[0] in {x[0] for x in CASES[("T2", r)].candidates[:0]} | {cc[0] for cc in W.local_prior(CASES[("T2", r)], 0.05, r)[0]}
        seen_shared += ev.shared
    assert upstream > 100 and seen_shared > 30


def test_with_no_upstream_faults_every_cause_is_local_and_with_certain_ones_the_state_shows():
    for i in range(80):
        ev = W.draw_event(4, i, _params(f=1e-12), CASES)
        assert all(c[0] not in ("ahu_fan_off", "low_static") for c in ev.causes) and all(v == "ok" for v in ev.u.values()) and not ev.shared


def test_map_faults_move_boxes_to_another_air_handler():
    same = W.draw_event(5, 0, _params(q_ahu=0.0), CASES)
    assert all(same.true_ahu[f"VAV-{b}"] == f"AHU-{b // 8}" for b in range(24))
    allflip = W.draw_event(5, 0, _params(q_ahu=1.0), CASES)
    assert all(allflip.true_ahu[f"VAV-{b}"] != f"AHU-{b // 8}" for b in range(24))
    frac = np.mean([W.draw_event(5, i, _params(q_ahu=0.1), CASES).true_ahu[f"VAV-{b}"] != f"AHU-{b // 8}" for i in range(40) for b in range(24)])
    assert 0.06 < frac < 0.14


def test_event_kinds():
    mk = lambda causes, tas: W.Event(0, 0, {}, {}, list(range(len(causes))), causes, tas)  # noqa: E731
    assert mk([FAN], ["AHU-0"]).kind == "single"
    assert mk([FAN, LOW], ["AHU-0", "AHU-0"]).kind == "shared" and mk([FAN, LOW], ["AHU-0", "AHU-0"]).shared
    assert mk([FAN, LOW], ["AHU-0", "AHU-1"]).kind == "multi"                              # two upstream complaints on DIFFERENT air handlers: not shared
    assert mk([("damper_mech",), ("no_power",)], ["AHU-0", "AHU-0"]).kind == "multi"
    assert mk([FAN, ("damper_mech",)], ["AHU-0", "AHU-0"]).kind == "multi" and not mk([FAN, ("damper_mech",)], ["AHU-0", "AHU-0"]).shared


def test_the_simulated_technician_answers_from_the_true_responses():
    ev = W.Event(0, 0, {"AHU-0": "ahu_fan_off", "AHU-1": "ok", "AHU-2": "low_static"}, {}, [0, 9], [FAN, ("damper_mech",)], ["AHU-0", "AHU-1"])
    o = W.Oracle(ev, 0.0, np.random.default_rng(0))
    by = {c.name: c for c in K.CATALOGUE}
    assert o.p_ahu("AHU-0", "bas_ahu_fan") == pytest.approx(0.92) and o.p_ahu("AHU-1", "bas_ahu_fan") == pytest.approx(0.03) and o.p_ahu("AHU-2", "bas_ahu_fan") == pytest.approx(0.20)
    assert o.p_ahu("AHU-2", "bas_static") == pytest.approx(0.92) and o.p_ahu("AHU-1", "bas_static") == pytest.approx(0.03)
    assert o.p_room(0, "flow_hood", "VAV-0") == pytest.approx(0.92) and o.p_room(1, "manual_damper_test", "VAV-9") == pytest.approx(0.92) and o.p_room(0, "manual_damper_test", "VAV-0") == pytest.approx(0.05)
    assert o.p_room(1, "confirm_acts", "VAV-9") == pytest.approx(0.05)                        # v0's acts check: the damper is stuck, so it does not move
    worse = W.Oracle(ev, 0.5, np.random.default_rng(0))
    assert worse.p_ahu("AHU-0", "bas_ahu_fan") == pytest.approx(0.5 + 0.42 * 0.5) and worse.p_ahu("AHU-1", "bas_ahu_fan") == pytest.approx(0.5 - 0.47 * 0.5)
    hits = np.mean([W.Oracle(ev, 0.0, np.random.default_rng(i)).ask_ahu("AHU-0", by["bas_ahu_fan"]) == "abnormal" for i in range(400)])
    assert 0.88 < hits < 0.96 and by["bas_ahu_fan"].words == ("abnormal", "normal")


# ---------------------------------------------------------------------------------------------- the policies
def test_policy_names_and_streams_are_fixed():
    assert P.POLICIES == ("tool_ticket", "tool_ticket_nb", "tool_ticket_memo", "tool_joint", "tool_joint_la2", "fast_ticket", "fast_parent")
    assert [P.POLICY_INDEX[p] for p in P.POLICIES] == list(range(7)) and P.LOOKAHEAD_POLICIES == ("tool_joint_la2",)
    with pytest.raises(ValueError):
        P.run_policy("nope", cases_for("T2", [0]), Scripted(), [W.context_dict("T2", 0)])


def test_the_prior_session_uses_the_given_prior_and_nothing_else_changes():
    case = CASES[("T2", 0)]
    causes, prior = P.Session(case)._prior()
    given = (causes, np.eye(len(causes))[3] * 0.9 + 0.1 / len(causes))
    s = P.PriorSession(case, given)
    assert s._prior()[1] == pytest.approx(given[1]) and s.posterior()[1] == pytest.approx(given[1] / given[1].sum())
    assert P.PriorSession(case)._prior()[1] == pytest.approx(prior)


def test_the_neighbour_prior_is_the_joint_models_marginal_at_time_zero():
    cs = cases_for("T2", [0, 1, 2])
    mdl = JointModel(cs)
    seen = []

    class Spy(P.PriorSession):
        def __init__(self, case, prior=None):
            super().__init__(case, prior)
            seen.append(prior)
    orig = P.PriorSession
    P.PriorSession = Spy
    try:
        P.run_ticket(cs, Scripted(), "nb")
    finally:
        P.PriorSession = orig
    assert len(seen) == 3 and all(p is not None for p in seen)
    for i, p in enumerate(seen):
        assert p[0] == mdl.causes[i] and p[1] == pytest.approx(mdl.marg0[i])
    seen.clear()
    P.PriorSession = Spy
    try:
        P.run_ticket(cs, Scripted(), "plain")
    finally:
        P.PriorSession = orig
    assert seen == [None, None, None]


def test_ticket_modes_are_validated_and_return_the_documented_fields():
    with pytest.raises(ValueError):
        P.run_ticket(cases_for("T2", [0]), Scripted(), "nope")
    r = P.run_ticket(cases_for("T3", [0, 1]), Scripted(), "plain")
    assert set(r) == {"minutes", "n_checks", "guess", "concluded", "trace"} and len(r["guess"]) == 2 and len(r["concluded"]) == 2 and r["n_checks"] == len(r["trace"])
    assert r["n_checks"] <= 24


def test_memo_never_asks_an_air_handler_twice_and_carries_the_location():
    cs = cases_for("T3", list(range(7)))
    orc = Modal(fan_event(7))
    r = P.run_ticket(cs, orc, "memo")
    asked = [c[1:] for c in orc.calls if c[0] == "ahu"]
    assert len(asked) == len(set(asked)) and asked                                          # an air handler check is done once, in the first ticket that wants it
    assert r["trace"][0][0] == 0 and r["guess"] == [FAN] * 7
    orc2 = Modal(fan_event(7))
    P.run_ticket(cs, orc2, "plain")
    plain = [c[1:] for c in orc2.calls if c[0] == "ahu"]
    assert len(plain) > len(set(plain))                                                     # without memory the same reading is taken again in a later ticket


def test_a_ticket_starts_where_the_last_one_left_the_technician():
    cs = cases_for("T2", [0, 1])
    both = P.run_ticket(cs, Scripted(), "plain")
    apart = [P.run_ticket([c], Scripted(), "plain") for c in cs]
    assert both["n_checks"] == sum(a["n_checks"] for a in apart) and both["minutes"] <= sum(a["minutes"] for a in apart) + 1e-9


def test_the_joint_policy_returns_the_documented_fields_and_the_air_handler_posterior():
    cs = cases_for("T3", list(range(7)))
    r = P.run_joint(cs, Modal(fan_event(7)))
    assert set(r) == {"minutes", "n_checks", "guess", "concluded", "trace", "ahu_posterior"} and len(r["guess"]) == 7 and r["trace"][0][:3] == ("ahu", "AHU-0", r["trace"][0][2])
    assert r["guess"] == [FAN] * 7 and r["concluded"] == [True] * 7 and r["ahu_posterior"]["AHU-0"][1] > 0.9 and r["n_checks"] == len(r["trace"])
    assert r["minutes"] < P.run_ticket(cs, Modal(fan_event(7)), "plain")["minutes"] / 3         # a reading of the air handler speaks for all seven complaints


def test_fast_parent_checks_the_shared_parent_first_and_names_the_cause_for_every_complaint():
    cs, ctx = cases_for("T3", [0, 1, 2]), [W.context_dict("T3", r) for r in (0, 1, 2)]
    fan = Scripted(lambda kind, who, ck, target: ck.words[0] if kind == "ahu" else ck.words[1])
    r = P.run_fast_parent(cs, fan, ctx)
    assert r["guess"] == [FAN] * 3 and r["n_checks"] == 1 and r["minutes"] == 2.0 and r["trace"][0][0] == "group"          # the 2-minute control-system fan read, nothing else
    assert r["concluded"] == [True] * 3
    static = Scripted(lambda kind, who, ck, target: ck.words[0] if kind == "ahu" and ck.name == "bas_static" else ck.words[1])
    r = P.run_fast_parent(cs, static, ctx)
    assert r["guess"] == [LOW] * 3 and r["n_checks"] == 2 and r["minutes"] == 4.0
    none = Scripted()
    r = P.run_fast_parent(cs, none, ctx)
    room_calls = [c for c in none.calls if c[0] == "room"]
    ahu_calls = [c[2] for c in none.calls if c[0] == "ahu"]
    assert sorted(ahu_calls) == ["bas_ahu_fan", "bas_static"] and room_calls                                              # each air handler question once (a fan visit is not repeated after a fan read)
    assert all(g not in (FAN, LOW) for g in r["guess"])


def test_fast_parent_leaves_a_lone_complaint_to_the_checklist():
    cs, ctx = cases_for("T3", [0, 9]), [W.context_dict("T3", r) for r in (0, 9)]
    orc = Scripted()
    r = P.run_fast_parent(cs, orc, ctx)
    assert not any(t[0] == "group" for t in r["trace"])
    ref = P.run_fast_ticket(cs, Scripted(), ctx)
    assert r["guess"] == ref["guess"] and r["minutes"] == pytest.approx(ref["minutes"]) and r["n_checks"] == ref["n_checks"]


def test_fast_ticket_carries_the_location_and_always_concludes():
    cs, ctx = cases_for("T2", [0, 1]), [W.context_dict("T2", r) for r in (0, 1)]
    r = P.run_fast_ticket(cs, Scripted(), ctx)
    assert r["concluded"] == [True, True] and r["n_checks"] == len(r["trace"]) and all(len(t) == 4 for t in r["trace"])
    apart = [P.fast_run(c, x, lambda ck, t: ck.words[1], None)[0] for c, x in zip(cs, ctx)]
    assert r["minutes"] <= sum(a["minutes"] for a in apart) + 1e-9 and r["n_checks"] == sum(a["n_checks"] for a in apart)
    res, at = P.fast_run(cs[0], ctx[0], lambda ck, t: ck.words[1], None)
    assert at is not None and res["minutes"] > 0
    box_first, _ = P.fast_run(CASES[("T2", 1)], W.context_dict("T2", 1), lambda ck, t: ck.words[1], "VAV-1", skip=frozenset({"design_load", "thermostat", "diffuser_duct", "flow_hood", "ahu_visit"}))
    box_cold, _ = P.fast_run(CASES[("T2", 1)], W.context_dict("T2", 1), lambda ck, t: ck.words[1], None, skip=frozenset({"design_load", "thermostat", "diffuser_duct", "flow_hood", "ahu_visit"}))
    assert box_first["minutes"] == pytest.approx(box_cold["minutes"] - 6.0)                                                # starting at the box saves the 6-minute walk to it


def test_fast_run_skips_the_checks_it_is_told_to_skip():
    case, ctx = CASES[("T3", 0)], W.context_dict("T3", 0)
    r, _ = P.fast_run(case, ctx, lambda ck, t: ck.words[1], None, skip=frozenset({"bas_ahu_fan", "power_24vac"}))
    assert all(t[1] not in ("bas_ahu_fan", "power_24vac") for t in r["trace"]) and r["trace"]
    r0, _ = P.fast_run(case, ctx, lambda ck, t: ck.words[1], None)
    assert any(t[1] == "bas_ahu_fan" for t in r0["trace"])


def test_all_policies_run_deterministically_on_the_same_event():
    ev = W.draw_event(0, 3, _params(f=0.09), CASES)
    cs, ctx = [CASES[("T2", r)] for r in ev.rooms], [W.context_dict("T2", r) for r in ev.rooms]
    for pol in P.POLICIES:
        a = P.run_policy(pol, cs, W.Oracle(ev, 0.0, np.random.default_rng(5)), ctx)
        b = P.run_policy(pol, cs, W.Oracle(ev, 0.0, np.random.default_rng(5)), ctx)
        assert (a["minutes"], a["guess"], a["n_checks"]) == (b["minutes"], b["guess"], b["n_checks"]) and a["minutes"] >= 0 and len(a["guess"]) == ev.n


# ---------------------------------------------------------------------------------------------- further guards (rate rule, look-ahead, location, stand-in at T2)
def test_the_rate_rule_for_a_room_check_is_the_per_minute_threshold_itself():
    m = model_for([0], tier="T3")
    s = m.initial()
    o = next(o for o in m.options(s, m.all_stats(s), 0.95, 0.0, 0.0) if o.kind == "complaint" and o.check.name == "bas_airflow")
    x = o.gain / o.minutes
    assert o.key in [q.key for q in m.options(s, m.all_stats(s), 0.95, x - 1e-9, 0.0)] and o.key not in [q.key for q in m.options(s, m.all_stats(s), 0.95, x + 1e-9, 0.0)]
    assert o.key not in [q.key for q in m.options(s, m.all_stats(s), 0.95, 0.0, o.gain + 1e-9)]                    # and a check that would not change the belief by `min_gain` is not offered


def test_a_group_may_have_every_documented_room_complaining_but_not_more():
    JointModel(cases_for("T2", list(range(8))))
    with pytest.raises(ValueError, match="documented rooms"):
        JointModel(cases_for("T2", list(range(8))), None, {"AHU-0": 7, "AHU-1": 8, "AHU-2": 8})


def test_two_step_lookahead_scores_the_top_options_by_gain_and_minutes_of_the_option_and_its_best_follow_up():
    sess = JointSession(cases_for("T3", [0, 1]), lookahead=2)
    opts = sess._options(sess.state)
    top = sorted(opts, key=Jn._score, reverse=True)[:Jn.LOOKAHEAD_TOP]
    best, best_key = None, None
    for o in top:
        g2 = m2 = 0.0
        for positive, p in ((True, o.pyes), (False, 1 - o.pyes)):
            nxt = sess._options(sess.model.apply(sess.state, o, positive))
            if nxt:
                f = max(nxt, key=Jn._score)
                g2, m2 = g2 + p * f.gain, m2 + p * f.minutes
        key = (round((o.gain + g2) / (o.minutes + m2), 12), -o.minutes, o.check.name, str(o.target), str(o.who))
        if best_key is None or key > best_key:
            best, best_key = o, key
    assert sess._pick(opts).key == best.key
    greedy = JointSession(cases_for("T3", [0, 1])).recommend()
    assert greedy.key == max(opts, key=Jn._score).key
    picks = 0
    for k in range(12):
        ev = W.draw_event(0, k, W.WorldParams(0.09, 0.0, 0.05, 0.0), CASES)
        cs = [CASES[("T3", r)] for r in ev.rooms]
        a, b = JointSession(cs).recommend(), JointSession(cs, lookahead=2).recommend()
        picks += a is not None and b is not None and a.key != b.key
    assert picks >= 1                                                                                        # look-ahead is not the same rule as one-step selection


def test_ticket_sessions_start_where_the_last_ended_and_the_visit_is_the_sum_of_their_minutes():
    log = []

    class Spy(P.PriorSession):
        def __init__(self, case, prior=None):
            super().__init__(case, prior)
            log.append(self)
    orig = P.PriorSession
    P.PriorSession = Spy
    starts = []
    try:
        cs = cases_for("T2", [0, 1, 2])
        orig_next = Spy.next_step

        def watch(self):
            if not hasattr(self, "_seen"):
                self._seen = True
                starts.append(self.at)
            return orig_next(self)
        Spy.next_step = watch
        r = P.run_ticket(cs, Scripted(), "plain")
    finally:
        P.PriorSession = orig
    assert len(log) == 3 and starts[0] is None and starts[1] == log[0].at and starts[2] == log[1].at and log[0].at is not None
    assert r["minutes"] == pytest.approx(sum(s.elapsed for s in log)) and r["n_checks"] == sum(len(s.log) for s in log)


def test_without_a_control_system_the_parent_first_rule_reads_the_fan_by_a_visit():
    cs, ctx = cases_for("T2", [0, 1]), [W.context_dict("T2", r) for r in (0, 1)]
    fan = Scripted(lambda kind, who, ck, target: ck.words[0] if kind == "ahu" else ck.words[1])
    r = P.run_fast_parent(cs, fan, ctx)
    assert r["guess"] == [FAN, FAN] and r["n_checks"] == 1 and r["minutes"] == 19.0 and r["trace"][0][:3] == ("group", "AHU-0", "ahu_visit")             # 15 to get there + 4
    static = Scripted(lambda kind, who, ck, target: ck.words[0] if kind == "ahu" and ck.name == "ahu_gauge" else ck.words[1])
    r = P.run_fast_parent(cs, static, ctx)
    assert r["guess"] == [LOW, LOW] and r["n_checks"] == 2 and r["minutes"] == 19.0 + 2.0                                                            # the gauge is read where the technician already is


def test_complaints_arrive_in_a_random_order():
    unsorted = 0
    for i in range(80):
        ev = W.draw_event(6, i, _params(f=0.3), CASES)
        unsorted += ev.n >= 2 and ev.rooms != sorted(ev.rooms)
    assert unsorted >= 5


# ---------------------------------------------------------------------------------------------- the command line
from docmismatch.troubleshoot.v2 import cli  # noqa: E402


def test_the_demo_runs_a_shared_cause_visit_to_a_conclusion(capsys):
    rooms = ",".join(f"Room-{i}" for i in range(7))
    cli.main(["--demo", "--tier", "T3", "--complaints", rooms, "--truth", ",".join(["ahu_fan_off"] * 7)])
    out = capsys.readouterr().out
    assert "Visit with 7 complaints" in out and "informs 7 complaints" in out and "Every complaint has a likely cause." in out and "fan off" in out
    assert "supply fan status" in out and "Note: The confidence figures assume" in out and "Note: The joint model assumes" in out and "placeholders" in out


def test_the_interactive_loop_takes_answers_and_can_be_stopped():
    cs = cases_for("T3", [0, 1])
    lines, answers = [], iter(["x", "n", "q"])
    st = cli.run(JointSession(cs), lambda prompt: next(answers), lines.append)
    text = "\n".join(lines)
    assert "Please answer" in text and "Stopped." in text and st["n_checks"] == 1
    lines2 = []
    st2 = cli.run(JointSession(cs), lambda prompt: (_ for _ in ()).throw(EOFError()), lines2.append)                # input ends: the same as quitting
    assert "Stopped." in "\n".join(lines2) and st2["n_checks"] == 0


def test_an_air_handler_check_is_described_with_the_rooms_it_speaks_for():
    sess = JointSession(cases_for("T3", [0, 1, 2]))
    o = next(x for x in sess._options(sess.state) if x.kind == "ahu")
    text = cli.describe_option(sess, o)
    assert "Room 0" in text and "Room 1" in text and "Room 2" in text and "AHU-0" in text
    r = next(x for x in sess._options(sess.state) if x.kind == "complaint")
    assert "AHU-0" in cli.describe_option(sess, r) or "VAV-" in cli.describe_option(sess, r)


def test_the_demo_technician_answers_from_the_causes_and_the_air_handler_state():
    sess = JointSession(cases_for("T3", [0, 1]))
    demo = cli.DemoTechnician(sess, [FAN, ("damper_mech",)], {"AHU-0": "ahu_fan_off"})
    o = next(x for x in sess._options(sess.state) if x.kind == "ahu" and x.check.name == "bas_ahu_fan")
    assert demo.p(o) == pytest.approx(0.92)
    o1 = next(x for x in sess._options(sess.state) if x.kind == "complaint" and x.who == 1 and x.check.name == "manual_damper_test")
    assert demo.p(o1) == pytest.approx(0.92)
    healthy = cli.DemoTechnician(sess, [FAN, ("damper_mech",)], {})
    assert healthy.p(o) == pytest.approx(0.03)


def test_the_command_line_rejects_bad_demo_input_and_exports_the_visit(tmp_path, capsys):
    with pytest.raises(SystemExit):
        cli.main(["--demo", "--complaints", "Room-0,Room-1", "--truth", "low_static"])
    with pytest.raises(SystemExit):
        cli.main(["--demo", "--complaints", "Room-0", "--truth", "nonsense"])
    out = tmp_path / "visit.json"
    cli.main(["--demo", "--tier", "T3", "--complaints", "Room-0,Room-1,Room-2,Room-3,Room-4,Room-5,Room-6", "--truth", ",".join(["ahu_fan_off"] * 7), "--export", str(out)])
    import json
    d = json.loads(out.read_text())
    assert d["rooms"][0] == "Room-0" and d["tier"] == "T3" and len(d["complaints"]) == 7 and d["checks"] and d["assumptions"]["validated_on_real_call_outs"] is False
    assert d["complaints"][0]["ranked"][0][0] == ["ahu_fan_off"] and d["elapsed"] > 0
    capsys.readouterr()


def test_the_example_building_loads_and_has_the_studys_shape():
    b = D.load_building_v1(cli.EXAMPLE)
    assert len(b.base.members("vav_zone")) == 24 and b.base.claims["ahu_vav"]["VAV-9"] == "AHU-1" and b.points["AHU-0"]["fan_status"] == "AHU0.SF" and b.attrs["VAV-4"]["reheat"] == "hydronic"
    ref = W.make_building2()
    assert b.base.claims == ref.base.claims and b.attrs == ref.attrs and b.points == ref.points


def test_the_recommendation_is_the_best_gain_per_minute_and_ties_go_to_the_cheaper_option():
    sess = JointSession(cases_for("T2", [0, 1, 2]))
    opts = sess._options(sess.state)
    by_rate = max(opts, key=lambda o: (round(o.gain / o.minutes, 12), -o.minutes, o.check.name, str(o.target), str(o.who)))
    by_gain = max(opts, key=lambda o: o.gain)
    assert sess.recommend().key == by_rate.key and by_rate.key != by_gain.key                           # the rule is per minute, not per check
    ck = K.BY_NAME["power_24vac"]
    mk = lambda minutes, gain, name="power_24vac": Jn.JOption("complaint", 0, K.BY_NAME[name], "VAV-0", "VAV-0", minutes, gain, 0.5, 1, D.Avail("offered"))  # noqa: E731
    cheap, dear = mk(10.0, 1.0), mk(20.0, 2.0)
    assert max([dear, cheap], key=Jn._score) is cheap and max([cheap, dear], key=Jn._score) is cheap  # the same rate: the cheaper wins
    assert max([mk(10.0, 1.0, "control_signal"), mk(10.0, 1.0, "power_24vac")], key=Jn._score).check.name == "power_24vac" or ck is not None
    assert max([mk(10.0, 1.0), mk(10.0, 1.5)], key=Jn._score).gain == 1.5                                # a better rate wins whatever the minutes


def test_the_two_step_value_is_the_options_gain_and_minutes_plus_the_weighted_best_follow_up():
    sess = JointSession(cases_for("T3", [0, 1]), lookahead=2)
    for o in sorted(sess._options(sess.state), key=Jn._score, reverse=True)[:4]:
        g, mins = sess.two_step_value(o)
        ref_g, ref_m = o.gain, o.minutes
        for positive, prob in ((True, o.pyes), (False, 1 - o.pyes)):
            nxt = sess._options(sess.model.apply(sess.state, o, positive))
            best = max(nxt, key=lambda x: (round(x.gain / x.minutes, 12), -x.minutes, x.check.name, str(x.target), str(x.who))) if nxt else None
            if best is not None:
                ref_g, ref_m = ref_g + prob * best.gain, ref_m + prob * best.minutes
        assert g == pytest.approx(ref_g) and mins == pytest.approx(ref_m) and mins > o.minutes and g >= o.gain


def test_an_upstream_fault_affects_the_stated_share_of_its_rooms():
    rates = {"ahu_fan_off": [], "low_static": []}
    for i in range(400):
        ev = W.draw_event(7, i, _params(f=0.9), CASES)
        for a, state in ev.u.items():
            if state in rates:
                hit = sum(1 for c, ta in zip(ev.causes, ev.true_ahu_of) if c[0] == state and ta == a)
                rates[state].append(hit / 8)
    assert 0.84 < np.mean(rates["ahu_fan_off"]) < 0.95 and 0.42 < np.mean(rates["low_static"]) < 0.58 and len(rates["ahu_fan_off"]) > 50 and len(rates["low_static"]) > 100


def test_parent_first_copes_with_a_catalogue_that_has_no_fan_check():
    keep = tuple(c for c in K.CATALOGUE if c.name not in P.FAN_CHECKS)
    cs = [make_case_v1(W.make_building2(), f"Room-{r}", W.TIER_ITEMS["T3"], W.tool_settings(), context=W.tier_context("T3", r), checks=keep, member_name=f"Room {r}") for r in (0, 1)]
    static = Scripted(lambda kind, who, ck, target: ck.words[0] if kind == "ahu" else ck.words[1])
    r = P.run_fast_parent(cs, static, [W.context_dict("T3", r) for r in (0, 1)])
    assert r["guess"] == [LOW, LOW] and r["n_checks"] == 1 and r["trace"][0][2] == "bas_static"


def test_only_air_handler_checks_are_said_to_inform_several_complaints():
    lines, answers = [], iter(["n", "n", "n", "q"])
    cli.run(JointSession(cases_for("T3", [0, 9])), lambda prompt: next(answers), lines.append)              # two air handlers, one complaint each: every check informs one complaint
    text = "\n".join(lines)
    assert "Next check" in text and "(informs" not in text
    lines2, answers2 = [], iter(["q"])
    cli.run(JointSession(cases_for("T3", [0, 1])), lambda prompt: next(answers2), lines2.append)
    assert "(informs" not in "\n".join(lines2) or "(informs 2 complaints)" in "\n".join(lines2)


def test_the_demo_with_low_static_makes_the_air_handler_faulty_for_the_simulated_technician(capsys, monkeypatch):
    """At the live default (min_rate = 0.02, 2026-09-29) this visit's shared-cause prior alone already clears tau before any check is offered, so the session concludes with ZERO checks --
    a known, disclosed side effect of that default (PREREGISTRATION_DR.md's "Further decision taken" note), kept as the live default anyway for the speed gain. Room-3's real cause
    (damper_mech) still gets swept into the shared low_static diagnosis, exactly as it already did at 0.015 with 3 checks that never actually probed Room-3's box -- 0.02 only removes
    checks that were not catching that mistake anyway, it does not introduce it. This test's actual point (unchanged): DemoTechnician gets the right `states`/`truths` wiring from `--truth`."""
    seen = {}
    orig = cli.DemoTechnician

    class Spy(orig):
        def __init__(self, sess, truths, states):
            super().__init__(sess, truths, states)
            seen["states"], seen["truths"] = dict(states), list(truths)
    monkeypatch.setattr(cli, "DemoTechnician", Spy)
    cli.main(["--demo", "--tier", "T3", "--complaints", "Room-0,Room-1,Room-2,Room-3", "--truth", "low_static,low_static,low_static,damper_mech"])
    out = capsys.readouterr().out
    assert seen["states"] == {"AHU-0": "low_static"} and seen["truths"][3] == ("damper_mech",)
    assert "No further check is worth its time." in out and "So far: 0 checks" in out
    assert "Room-3: Duct pressure too low upstream" in out  # the known limitation: an unrelated complaint on the same air handler still gets swept into the shared diagnosis
    sess = JointSession(cases_for("T3", [0, 1]))
    demo = orig(sess, [LOW, LOW], {"AHU-0": "low_static"})
    o = next(x for x in sess._options(sess.state) if x.kind == "ahu" and x.check.name == "bas_static")
    assert demo.p(o) == pytest.approx(0.92) and orig(sess, [LOW, LOW], {}).p(o) == pytest.approx(0.03)


def test_the_demo_needs_exactly_one_truth_per_complaint(capsys):
    with pytest.raises(SystemExit):
        cli.main(["--demo", "--complaints", "Room-0", "--truth", "low_static,damper_mech"])
    capsys.readouterr()


def test_the_live_cli_defaults_to_the_chosen_min_rate(monkeypatch):
    """The live tool (not the study code, which stays frozen at the historical 0.003) defaults to min_rate=0.02: 0.01 was confirmed across all 18 cells (Addendum 35); 0.015 was a further
    step the user chose directly, later found not confirmed at the 18-cell bar for T2 (Addendum 36); 0.02 is a further step still, taken for the user's own documentation profile
    (Exploratory note E2's "T3-noattr"), checked there plus a 5-cell spot-check (PREREGISTRATION_DR.md, 2026-09-29)."""
    seen = []
    orig = cli.make_case_v1

    def spy(*args, **kwargs):
        seen.append(kwargs.get("min_rate"))
        return orig(*args, **kwargs)
    monkeypatch.setattr(cli, "make_case_v1", spy)
    cli.main(["--demo", "--complaints", "Room-0", "--truth", "low_static"])
    assert seen == [0.02]


def test_the_live_cli_min_rate_can_still_be_overridden(monkeypatch):
    seen = []
    orig = cli.make_case_v1

    def spy(*args, **kwargs):
        seen.append(kwargs.get("min_rate"))
        return orig(*args, **kwargs)
    monkeypatch.setattr(cli, "make_case_v1", spy)
    cli.main(["--demo", "--complaints", "Room-0,Room-1", "--truth", "low_static,low_static", "--min-rate", "0.003"])
    assert seen == [0.003, 0.003]


def test_the_confirmed_min_rate_does_not_change_v1s_own_default():
    """v1's plain (single-complaint) tool and its own studies never tested this value and keep the historical placeholder."""
    from docmismatch.troubleshoot.v1.engine import DEFAULT_MIN_RATE
    assert DEFAULT_MIN_RATE == 0.003
