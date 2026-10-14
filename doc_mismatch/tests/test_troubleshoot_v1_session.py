"""Guards for the v1 session, simulator and command-line loop (docmismatch.troubleshoot.v1)."""
import contextlib
import io
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot import model as M  # noqa: E402
from docmismatch.troubleshoot.v1 import catalogue as K, causes as C, cli, data as D, engine as E, sim1  # noqa: E402

EX1 = ROOT / "examples" / "troubleshoot_example" / "building_v1.json"
ALL_YES = D.Context(reheat="yes", bas_access="yes", instrument="yes", occupant="yes")


def b1():
    return D.load_building_v1(EX1)


def case1(tier="T1", member="Room-204", **kw):
    return E.make_case_v1(b1(), member, tier, **kw)


def sess(tier="T1", strategy="entropy", **kw):
    return E.Session(case1(tier, **kw), strategy)


def world(truth, **ctx):
    c = dict(reheat="yes", bas_access="no", instrument="yes", occupant="yes")
    c.update(ctx)
    return sim1.World(truth, c)


def prob(s, cause):
    causes, post = s.posterior()
    return float(post[causes.index(cause)])


def run_modal(tier, truth, **kw):
    return sim1.simulate_v1(case1(tier, **kw), world(truth, bas_access="yes" if D.tier_items(tier) >= {"bas_access"} else "no"), modal=True)


# ---------------------------------------------------------------------------------------------- the case
def test_case_construction_and_validation():
    c = case1("T1")
    assert c.docs and c.doc == "VAV-2-04" and c.ahu == "AHU-2" and c.candidates[0] == "VAV-2-04" and len(c.candidates) == 6 and c.entries0 == 1 and c.member_name == "Room 204"
    assert c.min_rate == E.DEFAULT_MIN_RATE == 0.003 and case1("T1", compat_v0=True).min_rate == 0.0 and case1("T1", min_rate=0.0).min_rate == 0.0
    assert case1("T1", airflow="no", feel="too_cold", context=D.Context(reheat="no")).entries0 == 4
    for bad in (dict(airflow="maybe"), dict(feel="grumpy"), dict(min_rate=-1.0), dict(member="Room-999"), dict(member="VAV-2-04"), dict(tier="T9")):
        with pytest.raises(ValueError):
            case1(**bad)
    with pytest.raises(ValueError):
        E.make_case_v1(None, "Room-204", "T1")
    with pytest.raises(ValueError, match="equipment_list"):
        case1({"claims"})
    with pytest.raises(ValueError, match="equipment_list"):
        case1({"attributes"})
    assert case1({"equipment_list", "claims", "bas_access"}).tier == "custom"
    with pytest.raises(ValueError):
        E.Session(case1(), strategy="magic")


def test_t0_keeps_no_building_and_names_the_room_however_it_is_called():
    c = case1("T0")
    assert c.building is None and not c.docs and c.candidates == [E.GENERIC_BOX] and c.doc == E.GENERIC_BOX and c.ahu is None and c.member_name == "Room 204"
    assert case1("T0", member_name="the boardroom").member_name == "the boardroom"
    assert E.make_case_v1(None, None, "T0", member_name="Room 9").member_name == "Room 9" and E.make_case_v1(None, None, "T0").member_name == "this room"
    causes = sess("T0").posterior()[0]
    assert len(causes) == 14 and all(cc[0] in C.BY_ID for cc in causes)


# ---------------------------------------------------------------------------------------------- different data, different recommendations
def test_the_first_recommendation_differs_by_tier():
    r0, r1, r3 = sess("T0").recommend(), sess("T1").recommend(), sess("T3").next_step()
    assert (r0.check.name, r0.target) == ("confirm_acts", E.GENERIC_BOX) and r0.text == "Command the box serving Room 204 and confirm its damper actually moves"
    assert (r1.check.name, r1.target) == ("confirm_acts", "VAV-2-04") and r1.text == "Command box 2-04 and confirm its damper actually moves"
    assert r3.check.name == "bas_static" and r3.minutes == 2 and "AHU2.DSP" in r3.text and "AHU-2" in r3.text and "0.96 to 1.44" in r3.text
    assert r3.avail.state == "offered"


@pytest.mark.parametrize("truth", [("low_static",), ("zone_sensor_setpoint",), ("controller_config",)])
def test_scripted_sessions_at_t0_t1_and_t3_recommend_visibly_different_things(truth):
    r = {t: run_modal(t, truth) for t in ("T0", "T1", "T3")}
    seqs = {t: [c for c, _ in r[t]["sequence"]] for t in r}
    assert len({tuple(s) for s in seqs.values()}) == 3
    assert seqs["T3"][0].startswith("bas_") and not seqs["T0"][0].startswith("bas_") and not seqs["T1"][0].startswith("bas_")
    assert r["T3"]["minutes"] < r["T1"]["minutes"] <= r["T0"]["minutes"] + 1e-9 or r["T3"]["minutes"] < r["T0"]["minutes"]
    assert all(x["correct"] for x in r.values() if x["concluded"])


def test_the_documentation_causes_exist_only_from_t1_up():
    for t, has in (("T0", False), ("T1", True), ("T2", True), ("T3", True)):
        causes = sess(t).posterior()[0]
        assert any(c[0] == "wrong" for c in causes) is has and (("unlisted",) in causes) is has
    with pytest.raises(ValueError, match="documentation"):
        sim1.simulate_v1(case1("T0"), world(("wrong", "VAV-2-05")))


def test_wrong_documented_box_is_found_from_t1_up():
    for t in ("T1", "T2", "T3"):
        r = run_modal(t, ("wrong", "VAV-2-05"))
        assert r["correct"] and r["concluded"] and any(c == "duct_trace" for c, _ in r["sequence"])


# ---------------------------------------------------------------------------------------------- questions
def test_a_fully_declared_context_never_produces_a_question():
    for tier in ("T0", "T1", "T2", "T3"):
        s = sess(tier, context=ALL_YES)
        for _ in range(12):
            step = s.next_step()
            if step is None:
                break
            assert isinstance(step, E.Recommendation)
            s.report(step.check.words[1])


def test_a_question_is_asked_only_when_the_best_check_needs_it_and_never_twice():
    s = sess("T1")
    seen = []
    for _ in range(30):
        step = s.next_step()
        if step is None:
            break
        if isinstance(step, E.Question):
            assert step.key not in [k for k, _ in s.declared] and step.key not in seen
            seen.append(step.key)
            assert step.text == D.QUESTIONS[step.key]
            best_name = step.why.split("'")[1]
            assert D.availability(K.BY_NAME[best_name], s.view(), s._eq(K.BY_NAME[best_name])).ask[0] == step.key
            assert s.pending_question is step and s.pending is None
            s.declare(step.key, "yes")
            assert s.pending_question is None
        else:
            assert s.pending_question is None and s.pending == (step.check.name, step.target)
            s.report(step.check.words[1])
    assert seen and set(seen) <= set(D.CONTEXT_KEYS)
    assert s.entries == s.case.entries0 + len(s.declared) + len(s.log)


def test_recommend_never_asks_and_never_returns_a_check_that_needs_a_declaration():
    s = sess("T1")
    for _ in range(12):
        r = s.recommend()
        if r is None:
            break
        assert r.avail.state in ("offered", "fallback")
        s.report(r.check.words[1])
    assert not s.declared


def test_a_declaration_changes_what_is_offered_and_rescores_the_belief():
    assert ("reheat_fail",) in sess("T2").posterior()[0]                                    # hydronic reheat on file for 2-04
    s2 = sess("T2", member="Room-202")                                                     # documented cooling-only
    assert ("reheat_fail",) not in s2.posterior()[0]
    s2.declare("reheat", "yes")
    assert ("reheat_fail",) in s2.posterior()[0]
    s3 = sess("T1")
    assert ("reheat_fail",) in s3.posterior()[0]
    s3.declare("reheat", "no")
    assert ("reheat_fail",) not in s3.posterior()[0] and s3.entries == 2 and s3.declared == [("reheat", "no")]
    with pytest.raises(ValueError, match="declare 'yes' or 'no'"):
        s3.declare("occupant", "maybe")
    with pytest.raises(KeyError):
        s3.declare("weather", "yes")


def test_declaring_no_control_system_access_removes_the_control_system_reads_even_at_t3():
    s = sess("T3")
    assert any(o.check.name.startswith("bas_") for o in s._options(*s.posterior()))
    s.declare("bas_access", "no")
    assert not any(o.check.name.startswith("bas_") or o.check.name in ("flow_vs_gauge", "k_factor", "max_airflow") for o in s._options(*s.posterior()))


def test_declaring_access_at_t2_offers_the_reads_at_the_no_point_map_price():
    s = sess("T2", context=D.Context(bas_access="yes"))
    opts = {o.check.name: o for o in s._options(*s.posterior())}
    assert opts["bas_airflow"].minutes == 10 and opts["bas_airflow"].avail.state == "fallback" and opts["bas_airflow"].avail.extra_min == 8
    s.report("normal", "bas_airflow")
    assert s.elapsed == 10 and s.log[0].minutes == 10 and s.at == "bas"
    s3 = sess("T3")
    s3.report("normal", "bas_airflow")
    assert s3.elapsed == 2


def test_a_fallback_shows_in_the_recommendation_text():
    s = sess("T2", context=D.Context(bas_access="yes"))
    o = next(o for o in s._options(*s.posterior()) if o.check.name == "bas_airflow")
    rec = s._recommendation(o)
    assert rec.avail.extra_min == 8 and "includes 8 extra minutes because some data is not on file" in rec.why and rec.minutes == 10
    plain = s._recommendation(next(o for o in s._options(*s.posterior()) if o.check.name == "power_24vac"))
    assert "extra minutes" not in plain.why


# ---------------------------------------------------------------------------------------------- observations
def test_the_v0_yes_no_answers_still_work_on_the_v0_checks():
    s = sess("T1")
    s.report("yes", "confirm_acts", "VAV-2-04")
    s.report("no", "override_diffuser", "VAV-2-04")
    assert [(o.check, o.outcome) for o in s.log] == [("confirm_acts", "yes"), ("override_diffuser", "no")]
    assert s.elapsed == 9 + 5 and s.entries == 3
    with pytest.raises(ValueError, match="yes/no"):
        s.report("abnormal", "duct_trace", "VAV-2-04")


def test_reading_checks_take_abnormal_normal_and_accept_yes_no_as_the_same_answers():
    s = sess("T1")
    s.report("abnormal", "power_24vac")
    s.report("normal", "manual_damper_test")
    s.report("yes", "control_signal")
    s.report("no", "damper_linkage")
    assert [o.outcome for o in s.log] == ["abnormal", "normal", "abnormal", "normal"]
    with pytest.raises(ValueError, match="outcome must be"):
        s.report("maybe", "sensing_ports")
    with pytest.raises(ValueError, match="give an outcome"):
        s.report(None, "sensing_ports")


def test_unsure_spends_the_time_and_learns_nothing_and_skip_spends_nothing():
    s = sess("T1")
    p0 = s.posterior()[1].copy()
    s.report("unsure", "power_24vac")
    assert s.elapsed == 10 and s.at == "VAV-2-04" and np.array_equal(s.posterior()[1], p0)
    s.report("skip", "control_signal")
    assert s.elapsed == 10 and s.log[-1].minutes == 0 and np.array_equal(s.posterior()[1], p0)
    s.report("skip", "flow_hood")                                                              # a check in the room, skipped: the technician has not gone there
    assert s.at == "VAV-2-04" and s.elapsed == 10
    offered = {(o.check.name, o.target) for o in s._options(*s.posterior())}
    assert ("power_24vac", "VAV-2-04") not in offered and ("control_signal", "VAV-2-04") not in offered
    assert s.status()["n_checks"] == 1 and s.entries == 4                                      # the location + three answers (one unsure, two skipped)


def test_report_targets_and_duplicates_are_checked():
    s = sess("T1")
    with pytest.raises(RuntimeError):
        s.report("yes")
    with pytest.raises(ValueError, match="cannot be done"):
        s.report("no", "confirm_acts", "VAV-2-05")                                          # only the documented box's actuation is a hypothesis
    with pytest.raises(ValueError, match="cannot be done"):
        s.report("no", "power_24vac", "VAV-2-05")                                           # a reading check is on the documented box
    with pytest.raises(ValueError, match="cannot be done"):
        s.report("no", "override_room", "VAV-9")
    s.report("no", "override_room", "VAV-2-05")                                             # any candidate, for a v0 act-and-watch check
    with pytest.raises(ValueError, match="already recorded"):
        s.report("no", "override_room", "VAV-2-05")
    with pytest.raises(KeyError):
        s.report("no", "not_a_check")
    r = s.recommend()
    s.report(r.check.words[0])                                                              # the pending one
    assert s.log[-1].check == r.check.name


def test_a_pending_recommendation_can_be_overridden_by_what_the_technician_actually_did():
    s = sess("T1")
    r = s.recommend()
    other = "power_24vac" if r.check.name != "power_24vac" else "control_signal"
    s.report("normal", other)
    assert s.log[-1].check == other and s.pending is None


def test_numeric_readings_are_compared_with_the_expected_value():
    s = sess("T2")
    s.report(reading=24.1, check="power_24vac")
    s.report(reading=0.0, check="control_signal")
    s.report(reading=4800, check="k_factor")                                                # documented 5350, 1% tolerance
    assert [(o.outcome, o.reading) for o in s.log] == [("normal", 24.1), ("abnormal", 0.0), ("abnormal", 4800)]
    s2 = sess("T2")
    s2.report(reading=5350, check="k_factor")
    assert s2.log[0].outcome == "normal" and s2.log[0].expected is None
    s2.report(reading=1000, check="flow_hood", expected=1050)                                # technician's own expected value (10%)
    assert s2.log[1].outcome == "normal" and s2.log[1].expected == 1050
    s2.report(reading=500, check="max_airflow")                                              # documented design airflow 1200
    assert s2.log[2].outcome == "abnormal"


def test_a_reading_that_contradicts_the_stated_outcome_or_cannot_be_judged_is_refused():
    s = sess("T1")
    with pytest.raises(ValueError, match="is normal against"):
        s.report("abnormal", "power_24vac", reading=24.0)
    s.report("normal", "power_24vac", reading=24.0)                                          # agreeing is fine
    with pytest.raises(ValueError, match="takes no numeric reading"):
        s.report(reading=3.0, check="sensing_ports")
    with pytest.raises(ValueError, match="nothing to compare"):
        s.report(reading=3.0, check="k_factor")                                              # T1: no documented K-factor and no expected value given
    s.report(reading=3.0, check="k_factor", expected=3.0)
    assert s.log[-1].outcome == "normal"


def test_a_hand_computed_bayes_update():
    s = sess("T1")
    causes, prior = s._prior()
    ck = K.BY_NAME["power_24vac"]
    row = K.p_pos_row(ck, causes, "VAV-2-04", "VAV-2-04")
    s.report("abnormal", "power_24vac")
    post = s.posterior()[1]
    want = prior * row / (prior * row).sum()
    assert np.allclose(post, want)
    i = causes.index(("no_power",))
    assert post[i] > 0.3 and post[i] / prior[i] > 8                                          # one strong abnormal reading makes it the leading suspect
    s.report("normal", "manual_damper_test")
    row2 = K.p_pos_row(K.BY_NAME["manual_damper_test"], causes, "VAV-2-04", "VAV-2-04")
    want2 = want * (1 - row2) / (want * (1 - row2)).sum()
    assert np.allclose(s.posterior()[1], want2)


def test_the_evidence_moves_the_right_causes():
    s = sess("T1")
    base = {c: prob(s, c) for c in [("actuator_fail",), ("damper_mech",), ("no_power",)]}
    s.report("normal", "power_24vac")
    s.report("normal", "control_signal")
    s.report("abnormal", "damper_linkage")
    s.report("normal", "manual_damper_test")
    assert prob(s, ("no_power",)) < base[("no_power",)] and prob(s, ("actuator_fail",)) > base[("actuator_fail",)]
    assert prob(s, ("actuator_fail",)) > prob(s, ("damper_mech",))                           # free rotation by hand points at the actuator, not a stuck damper


def test_symptoms_change_the_first_belief():
    n, y = sess("T1", airflow="no"), sess("T1", airflow="yes")
    assert prob(n, ("actuator_fail",)) > prob(y, ("actuator_fail",)) and prob(n, ("ahu_fan_off",)) > prob(y, ("ahu_fan_off",))
    assert prob(sess("T1", feel="too_cold"), ("reheat_fail",)) > prob(sess("T1"), ("reheat_fail",))


# ---------------------------------------------------------------------------------------------- where the technician is
def test_access_is_charged_only_when_the_technician_is_somewhere_else():
    s = sess("T1", context=ALL_YES)
    opts = lambda: {(o.check.name, o.target): o.minutes for o in s._options(*s.posterior())}  # noqa: E731
    before = opts()
    assert before[("power_24vac", "VAV-2-04")] == 10 and before[("confirm_acts", "VAV-2-04")] == 9
    s.report("yes", "confirm_acts", "VAV-2-04")
    after = opts()
    assert after[("power_24vac", "VAV-2-04")] == 4 and after[("manual_damper_test", "VAV-2-04")] == 8      # same box: no walk
    assert after[("override_room", "VAV-2-05")] == 38 and after[("thermostat", "VAV-2-04")] == 5 + 6                   # the room is elsewhere
    assert after[("flow_hood", "VAV-2-04")] == 5 + 8 and after[("ahu_visit", "VAV-2-04")] == 15 + 4              # the room and the air handler are elsewhere
    s.report("normal", "flow_hood")
    assert s.at == "Room-204" and opts()[("diffuser_duct", "VAV-2-04")] == 10 and opts()[("power_24vac", "VAV-2-04")] == 10


def test_after_a_control_system_read_the_next_box_check_needs_a_walk_and_the_next_read_does_not():
    s = sess("T3", context=ALL_YES)
    s.report("normal", "bas_airflow")
    opts = {o.check.name: o.minutes for o in s._options(*s.posterior())}
    assert s.at == "bas" and opts["bas_damper"] == 2 and opts["power_24vac"] == 10


# ---------------------------------------------------------------------------------------------- stopping
def test_the_bits_per_minute_stop_ends_a_session_that_has_nothing_worth_doing_and_can_be_switched_off():
    def n_checks(min_rate):
        r = sim1.simulate_v1(case1("T1", min_rate=min_rate), world(("low_static",)), modal=True)
        return r["n_checks"], r["concluded"]
    default, off = n_checks(None), n_checks(0.0)
    assert off[0] > default[0]                                                                # without the stop it keeps going on checks that add little
    s = sess("T1")
    assert s.status()["stalled"] is False
    hi = sess("T1", min_rate=1000.0)
    assert hi.next_step() is None and hi.recommend() is None and hi.status()["stalled"] is True and hi.status()["concluded"] is False


def test_a_session_stops_at_tau_and_says_so():
    s = sess("T3", context=ALL_YES)
    for name in ("bas_static", "bas_ahu_fan", "bas_airflow", "static_at_box"):
        s.report("normal" if name == "bas_ahu_fan" else "abnormal", name)
    assert not s.status()["concluded"] and s.next_step() is not None                          # 94.96%: not yet
    s.report("normal", "ahu_visit")
    st = s.status()
    assert st["concluded"] and st["ranked"][0][0] == ("low_static",) and st["conclusion"].startswith("Duct pressure too low upstream") and s.next_step() is None


# ---------------------------------------------------------------------------------------------- equipment the technician finds
def test_add_candidate_rescores_and_uses_the_nearness_rule():
    s = sess("T1", max_candidates=3)
    assert s.candidates == ["VAV-2-04", "VAV-2-05", "VAV-2-06"]
    s.report("no", "override_room", "VAV-2-05")
    s.report("no", "override_room", "VAV-2-06")
    p_unlisted = prob(s, ("unlisted",))
    s.add_candidate("VAV-2-01")
    assert s.candidates[-1] == "VAV-2-01" and s.weights["VAV-2-01"] == 0.25 and s.entries == 4 and ("wrong", "VAV-2-01") in s.posterior()[0]
    assert prob(s, ("unlisted",)) < p_unlisted                                                # the answers already given now also bear on the new candidate
    for bad, exc in (("VAV-2-01", ValueError), ("AHU-1", ValueError), ("VAV-9-99", KeyError)):
        with pytest.raises(exc):
            s.add_candidate(bad)
    with pytest.raises(ValueError, match="no equipment list"):
        sess("T0").add_candidate("VAV-2-01")
    sid = E.Session(case1("T1", max_candidates=3, settings=M.Settings(nearness="id", id_decay=2.0)))
    sid.add_candidate("VAV-2-01")
    from docmismatch.troubleshoot.building import id_ranks, id_weight
    rk = id_ranks(b1().base, "VAV")
    assert sid.weights["VAV-2-01"] == pytest.approx(id_weight(rk["VAV-2-04"], rk["VAV-2-01"], 2.0))


def test_the_session_does_not_change_the_case_it_was_built_from():
    c = case1("T1", max_candidates=3)
    s = E.Session(c)
    s.add_candidate("VAV-2-01")
    s.add_equipment("VAV-2-99")
    assert c.candidates == ["VAV-2-04", "VAV-2-05", "VAV-2-06"] and "VAV-2-99" not in c.weights and "VAV-2-99" not in c.building.base.equipment
    assert E.Session(c).candidates == ["VAV-2-04", "VAV-2-05", "VAV-2-06"]


def test_undocumented_equipment_is_added_logged_and_usable():
    s = sess("T1")
    s.report("no", "override_room", "VAV-2-05")
    s.add_equipment("VAV-2-99", area="Floor 2 West", tag="2-99")
    assert s.candidates[-1] == "VAV-2-99" and s.weights["VAV-2-99"] == 1.0 and s.label("VAV-2-99") == "2-99" and s.entries == 3
    assert ("wrong", "VAV-2-99") in s.posterior()[0]
    (e,) = s.events
    assert e.type == "undocumented_equipment" and e.data == dict(id="VAV-2-99", kind="VAV", area="Floor 2 West", tag="2-99", added_by="technician") and e.n_checks == 1 and e.at_min == s.elapsed
    s.report("yes", "override_room", "VAV-2-99")
    assert s.posterior()[0][int(np.argmax(s.posterior()[1]))] == ("wrong", "VAV-2-99")
    for bad in ("VAV-2-99", "VAV-2-01"):
        with pytest.raises(ValueError, match="already known"):
            s.add_equipment(bad)
    with pytest.raises(ValueError, match="no equipment list"):
        sess("T0").add_equipment("X")


# ---------------------------------------------------------------------------------------------- the discrepancy log
def test_a_concluded_wrong_documented_box_is_logged_once_with_what_was_found():
    s = sess("T1")
    s.report("no", "duct_trace", "VAV-2-04")
    assert s.events == []
    s.report("yes", "duct_trace", "VAV-2-05")                                                  # belief in "fed by 2-05" first reaches 0.95 here
    (e,) = s.events
    assert e.type == "documented_owner_wrong" and e.data["member"] == "Room-204" and e.data["documented"] == "VAV-2-04" and e.data["found"] == "VAV-2-05" and e.data["belief"] >= 0.95
    assert e.data["basis"] == "tool conclusion" and e.n_checks == 2 and e.at_min == s.elapsed == 10 + 15 + 25 and s.status()["ranked"][0][0] == ("wrong", "VAV-2-05")
    s.report("yes", "override_diffuser", "VAV-2-05")
    s.report("no", "power_24vac")
    assert len(s.events) == 1                                                                  # not logged again as the belief grows
    assert "Start a new diagnosis on 2-05" in s.status()["conclusion"] and "2-04" in s.status()["conclusion"]


def test_nothing_is_logged_for_a_hardware_cause_or_an_unfinished_session():
    s = sess("T3", context=ALL_YES)
    for name in ("bas_static", "bas_ahu_fan", "bas_airflow", "static_at_box", "ahu_visit"):
        s.report("normal" if name in ("bas_ahu_fan", "ahu_visit") else "abnormal", name)
    assert s.status()["concluded"] and s.events == []
    assert sess("T1").events == []


def test_a_conclusion_that_nothing_on_the_list_serves_the_room_is_logged_with_no_box():
    s = sess("T1", max_candidates=2, settings=M.Settings(p_wrong=0.6, p_acts_fail=0.05, unlisted_share=0.9))
    s.report("no", "duct_trace", "VAV-2-04")
    s.report("no", "duct_trace", "VAV-2-05")
    s.report("no", "override_room", "VAV-2-05")
    s.report("no", "override_diffuser", "VAV-2-05")
    st = s.status()
    assert st["ranked"][0][0] == ("unlisted",) and st["concluded"]
    (e,) = s.events
    assert e.type == "documented_owner_wrong" and e.data["found"] is None and "not on the list" in st["conclusion"]


def test_a_declared_reheat_that_contradicts_the_documentation_is_logged():
    s = sess("T2", member="Room-202")                                                          # documented cooling-only
    s.declare("reheat", "yes")
    (e,) = s.events
    assert e.type == "documented_attribute_mismatch" and e.data == dict(equipment="VAV-2-02", attribute="reheat", documented="none", found="yes")
    ok = sess("T2", member="Room-202")
    ok.declare("reheat", "no")
    ok.declare("instrument", "yes")
    assert ok.events == [] and sess("T1").declared == []
    t1 = sess("T1")
    t1.declare("reheat", "yes")
    assert t1.events == []                                                                     # nothing documented to contradict


def test_a_nameplate_value_that_differs_from_the_documented_one_is_logged():
    s = sess("T2")
    s.report(reading=4800, check="k_factor", expected=4800)                                    # the nameplate says 4800; the file says 5350
    (e,) = s.events
    assert e.type == "documented_attribute_mismatch" and e.data == dict(equipment="VAV-2-04", attribute="k_factor", documented=5350, found=4800)
    s2 = sess("T2")
    s2.report(reading=5350, check="k_factor", expected=5350)
    assert s2.events == []
    s3 = sess("T2")
    s3.report(reading=5300, check="k_factor")                                                  # no nameplate value given: nothing to compare
    assert s3.events == []


def test_export_is_plain_json():
    s = sess("T2", airflow="no")
    s.report(reading=24.0, check="power_24vac")
    s.declare("instrument", "yes")
    s.add_equipment("VAV-2-99")
    x = json.loads(json.dumps(s.export()))
    assert x["tier"] == "T2" and x["member"] == "Room-204" and x["documented_box"] == "VAV-2-04" and x["airflow"] == "no" and x["declared"] == [["instrument", "yes"]]
    assert x["checks"] == [dict(check="power_24vac", target="VAV-2-04", outcome="normal", minutes=10.0, reading=24.0, expected=None)] and x["events"][0]["type"] == "undocumented_equipment"
    assert x["entries"] == s.entries and len(x["ranked"]) == 5 and x["elapsed"] == 10.0 and x["concluded"] is False
    a = x["assumptions"]
    assert a["validated_on_real_call_outs"] is False and a["tau"] == 0.95 and a["min_rate_bits_per_min"] == E.DEFAULT_MIN_RATE and a["check_reliability"] == E.RELIABILITY_NOTE
    assert "placeholders" in a["check_reliability"] and a["p_wrong"] == 0.15 and a["minutes"] == "placeholders"


def test_status_and_describe():
    s = sess("T1")
    st = s.status()
    assert set(st) == {"ranked", "concluded", "conclusion", "stalled", "elapsed", "n_checks", "entries", "at", "events", "declared"}
    assert [p for _, p in st["ranked"]] == sorted((p for _, p in st["ranked"]), reverse=True) and st["at"] is None and not st["concluded"] and st["conclusion"] is None
    for c in [("actuator_fail",), ("wrong", "VAV-2-05"), ("unlisted",)]:
        assert isinstance(s.describe(c), str) and s.describe(c)
    assert "Actuator failed" in s.describe(("actuator_fail",)) and "fed by 2-05" in s.describe(("wrong", "VAV-2-05"))
    with pytest.raises(ValueError):
        s.describe(("nonsense",))


# ---------------------------------------------------------------------------------------------- the simulator
def test_the_simulator_is_reproducible_and_reports_what_it_should():
    c = case1("T1")
    a = sim1.simulate_v1(c, world(("low_static",)), rng=np.random.default_rng(5))
    b = sim1.simulate_v1(c, world(("low_static",)), rng=np.random.default_rng(5))
    assert a == b
    assert set(a) == {"truth", "guess", "correct", "concluded", "stalled", "minutes", "n_checks", "n_questions", "entries", "sequence", "events", "trace"}
    assert a["entries"] == c.entries0 + a["n_questions"] + a["n_checks"] and len(a["sequence"]) == a["n_checks"] and a["n_checks"] <= 12
    assert len({tuple(sim1.simulate_v1(c, world(("low_static",)), rng=np.random.default_rng(s))["sequence"]) for s in range(10)}) > 1
    assert sim1.simulate_v1(c, world(("low_static",)), max_checks=3, modal=True)["n_checks"] == 3


def test_the_simulator_answers_from_the_true_response_not_the_tools_own():
    c = case1("T1")
    w = sim1.World(("no_power",), true_checks=K.degrade_all(K.CATALOGUE, 0.5))
    assert sim1.p_true(c, w, "power_24vac", "VAV-2-04") == pytest.approx(0.5 + (0.92 - 0.5) * 0.5)
    assert sim1.p_true(c, sim1.World(("no_power",)), "power_24vac", "VAV-2-04") == 0.92
    assert sim1.p_true(c, sim1.World(("wrong", "VAV-2-05")), "override_room", "VAV-2-05") == 0.98
    w2 = sim1.World(("ahu_fan_off",))
    assert sim1.p_true(c, w2, "override_room", "VAV-2-04") == 0.03 and sim1.p_true(c, w2, "bas_ahu_fan", "VAV-2-04") == 0.92


def test_world_validation():
    with pytest.raises(ValueError, match="not a candidate"):
        sim1.check_world(case1("T1", max_candidates=3), sim1.World(("wrong", "VAV-2-01")))
    with pytest.raises(ValueError, match="without reheat"):
        sim1.check_world(case1("T1"), sim1.World(("reheat_fail",), dict(reheat="no")))
    with pytest.raises(ValueError, match="v0's causes"):
        sim1.check_world(case1("T1", compat_v0=True), sim1.World(("low_static",)))
    sim1.check_world(case1("T1"), sim1.World(("reheat_fail",), dict(reheat="yes")))


def test_the_simulated_technician_answers_the_declared_questions_from_the_world():
    r = sim1.simulate_v1(case1("T1"), world(("low_static",), instrument="no", bas_access="no"), modal=True)
    assert r["n_questions"] >= 1
    r2 = sim1.simulate_v1(case1("T1"), world(("low_static",), instrument="yes", bas_access="yes"), modal=True)
    assert any(c.startswith("bas_") for c, _ in r2["sequence"]) or any(c == "static_at_box" for c, _ in r2["sequence"])
    assert not any(c in ("static_at_box", "flow_hood") for c, _ in r["sequence"])


def test_worse_checks_make_the_tool_more_often_confidently_wrong():
    causes = [c.cause for c in C.CAUSES if c.id != "other"]
    def wrong_and_sure(a):
        w = 0
        for i, t in enumerate(causes * 8):
            r = sim1.simulate_v1(case1("T3"), sim1.World(t, dict(reheat="yes", bas_access="yes", instrument="yes", occupant="yes"), K.degrade_all(K.CATALOGUE, a)), rng=np.random.default_rng(i))
            w += r["concluded"] and not r["correct"]
        return w
    assert wrong_and_sure(0.5) > wrong_and_sure(0.0)


def test_with_the_tools_own_model_right_the_answers_it_is_sure_of_are_mostly_right():
    causes = [c.cause for c in C.CAUSES if c.id != "other"]
    concl = corr = 0
    for i, t in enumerate(causes * 6):
        r = sim1.simulate_v1(case1("T3"), sim1.World(t, dict(reheat="yes", bas_access="yes", instrument="yes", occupant="yes")), rng=np.random.default_rng(100 + i))
        concl += r["concluded"]
        corr += r["concluded"] and r["correct"]
    assert concl >= 20 and corr / concl >= 0.85


# ---------------------------------------------------------------------------------------------- the command-line loop
class Script:
    def __init__(self, *answers):
        self.answers, self.prompts = list(answers), []

    def __call__(self, prompt):
        self.prompts.append(prompt)
        if not self.answers:
            raise EOFError
        return self.answers.pop(0)


def run_cli(s, *answers):
    out = []
    inp = Script(*answers)
    st = cli.run(s, inp, out.append)
    return st, "\n".join(out), inp


def test_the_loop_runs_a_whole_simulated_session_at_t3():
    s = sess("T3")
    out = []
    st = cli.run(s, sim1.technician_input(s, world(("low_static",), bas_access="yes"), None, echo=lambda *_: None), out.append)
    text = "\n".join(out)
    assert st["concluded"] and "Likely cause: Duct pressure too low upstream" in text and "control-system point: AHU2.DSP" in text and "Data available: tier T3" in text
    assert "Note: The confidence figures assume every check reads as reliably as the catalogue's rates say" in text                       # the assumption the results are most sensitive to is stated
    _, none_text, _ = run_cli(sess("T1"), "q")
    assert "Note:" not in none_text                                                                            # ... but not when no check was done


def test_the_loop_takes_a_numeric_reading_and_asks_for_the_expected_value_when_there_is_none():
    s = sess("T3")
    _, text, inp = run_cli(s, "0.5", "q")                                                     # bas_static; the documented setpoint gives 0.96-1.44
    assert s.log[0].check == "bas_static" and s.log[0].outcome == "abnormal" and s.log[0].reading == 0.5 and "Stopped." in text
    s = sess("T1")
    s._pending = ("flow_hood", "VAV-2-04")
    rec = E.Recommendation(K.BY_NAME["flow_hood"], "VAV-2-04", "x", 13, 0.5, 0.1, "y", D.Avail("offered"))
    inp = Script("950", "1000")
    assert cli._answer_check(s, rec, inp, lambda *_: None) == "answered" and s.log[0].outcome == "normal" and s.log[0].expected == 1000.0 and "Expected value" in inp.prompts[1]
    s = sess("T1")
    s._pending = ("flow_hood", "VAV-2-04")
    out = []
    inp = Script("abc", "950", "not a number", "950", "1000")
    assert cli._answer_check(s, rec, inp, out.append) == "answered" and any("Please answer" in o for o in out) and any("not a number" in o for o in out)


def test_the_loop_handles_answers_questions_adding_equipment_and_quitting():
    s = sess("T1")
    _, text, _ = run_cli(s, "q")
    assert "Stopped." in text and "belief now" in text and s.log == []
    s = sess("T1")
    _, text, _ = run_cli(s, "y", "q")
    assert text.count("belief now") >= 2                                                       # once after the answer, once when quitting
    s = sess("T1")
    run_cli(s, "y", "u", "s", "n", "q")                                                       # yes, unsure, skip, no (or a question answered n), then quit
    assert len(s.log) + len(s.declared) >= 3
    s = sess("T1")
    _, text, _ = run_cli(s, "+", "VAV-2-04", "q")
    assert "Could not add" in text and "already a candidate" in text
    s = sess("T1", max_candidates=3)
    _, text, _ = run_cli(s, "+", "VAV-2-01", "q")
    assert "Added VAV-2-01" in text and "VAV-2-01" in s.candidates
    s = sess("T1")
    _, text, _ = run_cli(s, "+", "VAV-2-77", "y", "q")
    assert "undocumented" in text and "VAV-2-77" in s.candidates and s.events[0].type == "undocumented_equipment"
    s = sess("T1")
    run_cli(s, "+", "VAV-2-77", "n", "q")
    assert "VAV-2-77" not in s.candidates
    s = sess("T0")
    _, text, _ = run_cli(s, "+", "VAV-2-01", "q")
    assert "Could not add" in text or "no equipment list" in text
    s = sess("T1")
    _, text, _ = run_cli(s)                                                                    # end of input is a quit
    assert "Stopped." in text


def test_the_loop_answers_a_question_and_quits_from_one():
    s = sess("T1", context=D.Context(reheat="yes"))
    q = None
    for _ in range(20):
        step = s.next_step()
        if isinstance(step, E.Question):
            q = step
            break
        s.report(step.check.words[1])
    assert q is not None
    n = len(s.declared)
    _, text, _ = run_cli(s, "s", "q")                                                          # skip = no; then quit at the next prompt
    assert s.declared[n] == (q.key, "no") and "Stopped." in text
    s2 = sess("T1", context=D.Context(reheat="yes"))
    for _ in range(20):
        if isinstance(s2.next_step(), E.Question):
            break
        s2.report(s2.recommend().check.words[1])
    _, text2, _ = run_cli(s2, "q")                                                             # quitting at the question itself declares nothing
    assert "Stopped." in text2 and s2.declared == []


def test_the_loop_prints_the_discrepancies_it_logged():
    s = sess("T1")
    s.add_equipment("VAV-2-88")
    _, text, _ = run_cli(s, "q")
    assert "Discrepancy logged: undocumented_equipment" in text and "VAV-2-88" in text


def test_the_loop_says_when_nothing_is_worth_doing():
    s = sess("T1", min_rate=1000.0)
    _, text, _ = run_cli(s)
    assert "No further check is worth its time." in text


def test_command_line_options(tmp_path):
    def main(*argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cli.main(list(argv))
        return buf.getvalue()
    t0 = main("--demo", "--tier", "T0", "--truth", "low_static", "--room-name", "Room 204")
    t1 = main("--demo", "--tier", "T1", "--truth", "low_static")
    t3 = main("--demo", "--tier", "T3", "--truth", "low_static")
    assert "tier T0" in t0 and "the box serving Room 204" in t0 and "tier T1" in t1 and "tier T3" in t3 and "control-system point" in t3 and "control-system point" not in t1
    assert len({t0, t1, t3}) == 3
    out = main("--demo", "--truth", "zone_sensor_setpoint", "--export", str(tmp_path / "s.json"), "--noise", "--seed", "1")
    assert "tier T3" in out and json.loads((tmp_path / "s.json").read_text())["tier"] == "T3"                     # 'auto' picks the richest tier the file supports
    wrong = main("--demo", "--tier", "T1", "--truth", "wrong:VAV-2-05")
    assert "fed by 2-05" in wrong and "Discrepancy logged: documented_owner_wrong" in wrong
    assert "Command box 2-04 and confirm" in main("--demo", "--tier", "T1", "--compat-v0", "--truth", "doc_other")
    tables = main("--tables")
    for name in ("causes", "catalogue", "readings", "tiers"):
        assert f"<!-- BEGIN:{name} -->" in tables and f"<!-- END:{name} -->" in tables
    assert "reheat=no" not in main("--demo", "--tier", "T2", "--truth", "duct_diffuser", "--context", "reheat=no,instrument=yes", "--member", "Room-205")
    with pytest.raises(SystemExit):
        main("--demo", "--truth", "cosmic_rays")
    with pytest.raises(ValueError):
        main("--demo", "--tier", "T0", "--truth", "wrong:VAV-2-05")
    with pytest.raises(KeyError):
        main("--demo", "--context", "weather=yes")
    assert cli._auto_tier(D.load_building_v1(EX1)) == "T3" and cli._auto_tier(D.load_building_v1(ROOT / "examples" / "troubleshoot_example" / "building.json")) == "T1"
    assert cli._parse_truth("wrong:X") == ("wrong", "X") and cli._parse_truth("unlisted") == ("unlisted",) and cli._parse_truth("doc_other") == ("doc_other",)
    assert cli._parse_context("reheat=no, bas_access=yes") == D.Context(reheat="no", bas_access="yes") and cli._parse_context(None) == D.Context()


def test_zone_checks_use_the_rooms_own_points_and_not_its_boxs():
    s = sess("T3", member="Room-205", context=ALL_YES)                                          # box 2-05 has control-system points in the example file; Room-205 does not
    opts = {o.check.name: o for o in s._options(*s.posterior())}
    assert opts["bas_airflow"].avail.extra_min == 0 and opts["bas_zone"].avail.extra_min == 8
    opts4 = {o.check.name: o for o in sess("T3", context=ALL_YES)._options(*sess("T3", context=ALL_YES).posterior())}
    assert opts4["bas_zone"].avail.extra_min == 0                                               # Room-204 has its temperature point on file


def test_the_first_question_asked_is_the_first_missing_fact():
    s = E.Session(case1("T2", checks=(K.BY_NAME["flow_vs_gauge"],), min_rate=0.0))
    q = s.next_step()
    assert isinstance(q, E.Question) and q.key == "bas_access"
    s.declare("bas_access", "yes")
    q2 = s.next_step()
    assert isinstance(q2, E.Question) and q2.key == "instrument"
    s.declare("instrument", "yes")
    r = s.next_step()
    assert isinstance(r, E.Recommendation) and r.check.name == "flow_vs_gauge" and r.avail.extra_min == 8


def test_a_tie_in_the_most_likely_answer_counts_as_positive():
    c = case1("T3", context=ALL_YES)
    s = E.Session(c)
    rec = s._recommendation(next(o for o in s._options(*s.posterior()) if o.check.name == "bas_airflow"))
    assert sim1.p_true(c, sim1.World(("flow_sensor",)), "bas_airflow", c.doc) == 0.5
    assert sim1.answer(c, sim1.World(("flow_sensor",)), rec, None) == "abnormal"               # exactly one half: positive
    assert sim1.answer(c, sim1.World(("duct_diffuser",)), rec, None) == "normal"


def test_replay_notices_a_question_that_would_not_have_been_asked():
    c = case1("T1")
    r = sim1.simulate_v1(c, world(("low_static",), instrument="yes"), modal=True)
    qi = next(i for i, x in enumerate(r["trace"]) if x[0] == "Q")
    other = "occupant" if r["trace"][qi][1] != "occupant" else "reheat"
    tampered = list(r["trace"])
    tampered[qi] = ("Q", other, r["trace"][qi][2])
    assert sim1.replay(c, r["trace"]) and not sim1.replay(c, tampered)


def test_true_probabilities_are_clipped_like_the_tools_own():
    from dataclasses import replace
    c = case1("T1")
    ck = replace(K.BY_NAME["power_24vac"], detects={"no_power": 1.0}, bg=0.0)
    assert sim1.p_true(c, sim1.World(("no_power",), true_checks=(ck,)), "power_24vac", c.doc) == 1.0 - M.RATE_FLOOR
    assert sim1.p_true(c, sim1.World(("low_static",), true_checks=(ck,)), "power_24vac", c.doc) == M.RATE_FLOOR


def test_the_richest_tier_is_picked_from_what_the_building_file_has():
    b = D.load_building_v1(EX1)
    assert cli._auto_tier(D.Building1(b.base, {}, b.points)) == "T3" and cli._auto_tier(D.Building1(b.base, b.attrs, {})) == "T2" and cli._auto_tier(D.Building1(b.base, {}, {})) == "T1"


def test_answer_keys_for_reading_and_yes_no_checks():
    s = sess("T3")
    run_cli(s, "a", "q")                                                                        # the first check is a reading check
    assert s.log[0].outcome == "abnormal"
    s = sess("T3")
    run_cli(s, "n", "q")
    assert s.log[0].outcome == "normal"
    s = sess("T1")
    run_cli(s, "y", "q")                                                                        # a v0 check: yes
    assert s.log[0].outcome == "yes"
