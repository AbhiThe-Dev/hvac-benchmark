"""Guards for the technician-guided troubleshooting working model (docmismatch.troubleshoot)."""
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot import Settings, Session, load_building, make_case  # noqa: E402
from docmismatch.troubleshoot import cli, model as M, sim  # noqa: E402

EXAMPLE = ROOT / "examples" / "troubleshoot_example" / "building.json"


def building():
    return load_building(EXAMPLE)


def case(**kw):
    kw.setdefault("member", "Room-204")
    return make_case(building(), **kw)


def near_perfect() -> Settings:
    s = Settings()
    return replace(s, menus={k: tuple(replace(c, tpr=0.9999, fpr=0.0001) for c in v) for k, v in s.menus.items()})


# ---------------------------------------------------------------------------------------------- priors and truth rules
def test_prior_is_a_distribution_that_follows_the_settings():
    s = Settings(p_wrong=0.2, unlisted_share=0.1, p_acts_fail=0.1)
    causes, p = M.make_prior("vav_zone", ["D", "A", "B"], "D", s)
    assert causes == [("doc_other",), ("doc_acts_fail",), ("wrong", "A"), ("wrong", "B"), ("unlisted",)]
    assert np.allclose(p, [0.7, 0.1, 0.09, 0.09, 0.02]) and np.isclose(p.sum(), 1.0)
    p_no = M.make_prior("vav_zone", ["D", "A", "B"], "D", s, airflow="no")[1]
    p_yes = M.make_prior("vav_zone", ["D", "A", "B"], "D", s, airflow="yes")[1]
    assert p_no[1] > p[1] > p_yes[1]                                                   # "no air at the diffuser" makes an acts-fail box more likely
    w = M.make_prior("vav_zone", ["D", "A", "B"], "D", s, weights={"A": 1.0, "B": 0.25})[1]
    assert w[2] > w[3]                                                                 # nearness prior
    only = M.make_prior("vav_zone", ["D"], "D", s)
    assert only[0][-1] == ("unlisted",) and np.isclose(only[1][-1], 0.2)               # no alternatives listed: all the "wrong" mass is "unlisted"
    assert M.make_prior("ahu_vav", ["D", "A"], "D", s)[0] == [("doc_ok",), ("wrong", "A"), ("unlisted",)]
    with pytest.raises(ValueError):
        M.make_prior("loop_branch", ["D"], "D", s)
    with pytest.raises(ValueError):
        Settings(p_wrong=0.7, p_acts_fail=0.5)
    with pytest.raises(ValueError):
        Settings(tau=1.0)


def test_truth_rules_for_both_connection_types():
    T = M.truth
    assert T("vav_zone", "act_observe", "D", ("doc_other",), "D") and not T("vav_zone", "act_observe", "D", ("doc_acts_fail",), "D")     # a box that does not act shows no response
    assert T("vav_zone", "act_observe", "A", ("wrong", "A"), "D") and not T("vav_zone", "act_observe", "A", ("wrong", "B"), "D")
    assert T("vav_zone", "trace", "D", ("doc_acts_fail",), "D") and T("vav_zone", "trace", "D", ("doc_other",), "D") and not T("vav_zone", "trace", "D", ("unlisted",), "D")
    assert not T("vav_zone", "acts", "D", ("doc_acts_fail",), "D") and T("vav_zone", "acts", "D", ("wrong", "A"), "D")
    assert T("ahu_vav", "act_observe", "D", ("doc_ok",), "D") and T("ahu_vav", "trace", "B", ("wrong", "B"), "D") and not T("ahu_vav", "trace", "B", ("doc_ok",), "D")
    with pytest.raises(ValueError):
        T("vav_zone", "nonsense", "D", ("doc_other",), "D")


# ---------------------------------------------------------------------------------------------- belief update and selection
def test_bayes_update_and_information_gain_match_hand_calculation():
    assert np.allclose(M.update(np.array([0.5, 0.5]), np.array([0.9, 0.1]), "yes"), [0.9, 0.1])
    assert np.allclose(M.update(np.array([0.5, 0.5]), np.array([0.9, 0.1]), "no"), [0.1, 0.9])
    post = np.array([0.3, 0.7])
    assert np.array_equal(M.update(post, np.zeros(2), "yes"), post)                    # an impossible answer leaves the belief alone instead of dividing by zero
    g, pyes = M.expected_gain(np.array([0.5, 0.5]), np.array([1.0, 0.0]))
    assert np.isclose(g, 1.0) and np.isclose(pyes, 0.5)                                # a perfect coin-flip splitter is worth one bit
    assert M.expected_gain(np.array([0.5, 0.5]), np.array([0.3, 0.3]))[0] == 0.0       # a check that cannot tell the causes apart is worth nothing
    assert M.expected_gain(np.array([0.9, 0.1]), np.array([0.8, 0.2]))[0] > 0


def test_selection_rules():
    ck = M.MENUS["vav_zone"][0]
    mk = lambda gain, minutes, pyes: M.Option(ck, "T", minutes, np.array([0.0]), gain, pyes)  # noqa: E731
    slow_big, quick_small = mk(1.0, 10, 0.5), mk(0.5, 2, 0.5)
    assert M.select("entropy", [slow_big, quick_small]) is quick_small                 # 0.25 bits per minute beats 0.1
    assert M.select("entropy", [mk(1.0, 10, 0.5), mk(0.5, 20, 0.5)]).gain == 1.0
    lopsided, balanced = mk(0.9, 5, 0.95), mk(0.5, 5, 0.5)
    assert M.select("split_half", [lopsided, balanced]) is balanced                    # closest to a coin flip, not the biggest claimed gain
    assert M.select("entropy", [mk(0.0, 1, 0.5), mk(1e-9, 1, 0.5)]) is None           # nothing informative left
    r = M.select("random", [slow_big, quick_small], rng=np.random.default_rng(1))
    assert r in (slow_big, quick_small)
    with pytest.raises(ValueError):
        M.select("magic", [slow_big])


def test_minutes_include_access_only_when_the_technician_is_elsewhere():
    ck = M.MENUS["vav_zone"][1]                                                        # override_diffuser: access 6, do 2, wait 3
    assert ck.minutes(None, "X") == 11 and ck.minutes("Y", "X") == 11 and ck.minutes("X", "X") == 5


# ---------------------------------------------------------------------------------------------- the session
def test_first_check_is_the_standard_one_and_prior_is_normalised():
    s = Session(case())
    rec = s.recommend()
    assert rec.check.name == "confirm_acts" and rec.target == "VAV-2-04" and rec.minutes == 9
    causes, post = s.posterior()
    assert np.isclose(post.sum(), 1.0) and causes[int(post.argmax())] == ("doc_other",)
    assert "2-04" in rec.text and "Room 204" not in rec.text                           # the acts-check names the box, not the room


def test_location_awareness_makes_checks_at_the_current_place_cheaper():
    s = Session(case())
    before = {(o.check.name, o.target): o.minutes for o in s._options(*s.posterior())}
    s.report("yes", "confirm_acts", "VAV-2-04")
    after = {(o.check.name, o.target): o.minutes for o in s._options(*s.posterior())}
    assert s.at == "VAV-2-04" and s.elapsed == 9
    assert after[("duct_trace", "VAV-2-04")] == before[("duct_trace", "VAV-2-04")] - 10        # no access cost at the box already reached
    assert after[("duct_trace", "VAV-2-05")] == before[("duct_trace", "VAV-2-05")]


def test_no_check_is_offered_twice_and_everything_is_eventually_exhausted():
    s = Session(case())
    seen = []
    while True:
        rec = s.recommend()
        if rec is None:
            break
        seen.append((rec.check.name, rec.target))
        s.report("unsure")
    assert len(seen) == len(set(seen)) == 6 * 3 + 1                                    # three checks on each of six candidates, plus confirm_acts on the documented box
    assert s.status()["stalled"] and not s.status()["concluded"]


def test_answers_have_the_right_effects():
    s = Session(case())
    _, p0 = s.posterior()
    e0 = s.entries
    s.report("skip", "duct_trace", "VAV-2-05")
    assert s.elapsed == 0 and s.entries == e0 + 1 and np.array_equal(s.posterior()[1], p0)     # skipped: no time, no evidence
    s.report("unsure", "duct_trace", "VAV-2-06")
    assert s.elapsed == 25 and np.array_equal(s.posterior()[1], p0)                           # unsure: the time is spent, nothing learned
    s.report("no", "override_room", "VAV-2-04")
    causes, p1 = s.posterior()
    assert p1[causes.index(("doc_other",))] < p0[causes.index(("doc_other",))]
    assert s.status()["n_checks"] == 2 and s.entries == e0 + 3
    rec = s.recommend()
    assert (rec.check.name, rec.target) not in [("duct_trace", "VAV-2-05"), ("duct_trace", "VAV-2-06"), ("override_room", "VAV-2-04")]      # skipped or done: not offered again


def test_bad_reports_are_rejected():
    s = Session(case())
    with pytest.raises(RuntimeError):
        s.report("yes")                                                                # nothing pending
    s.recommend()
    with pytest.raises(ValueError):
        s.report("maybe")
    with pytest.raises(ValueError):
        s.report("yes", "confirm_acts", "VAV-2-05")                                    # that check exists only for the documented box
    with pytest.raises(ValueError):
        s.report("yes", "duct_trace", "VAV-9-99")
    with pytest.raises(KeyError):
        s.report("yes", "no_such_check", "VAV-2-04")
    s.report("yes", "duct_trace", "VAV-2-04")
    with pytest.raises(ValueError):
        s.report("yes", "duct_trace", "VAV-2-04")                                      # already recorded
    with pytest.raises(ValueError):
        Session(case(), strategy="magic")


def test_conclusions_read_in_plain_language():
    s = Session(case())
    for ck in ("override_room", "override_diffuser", "duct_trace"):
        s.report("yes", ck, "VAV-2-05")
    st = s.status()
    assert st["concluded"] and st["ranked"][0][0] == ("wrong", "VAV-2-05")
    assert "2-04" in st["conclusion"] and "not the feeder" in st["conclusion"] and "2-05" in st["conclusion"]
    assert s.recommend() is None
    t = Session(case())
    t.report("no", "confirm_acts", "VAV-2-04")
    t.report("yes", "duct_trace", "VAV-2-04")
    assert t.status()["ranked"][0][0] == ("doc_acts_fail",) and "actuator" in t.describe(("doc_acts_fail",))
    assert "outside this tool's scope" in t.describe(("doc_other",))
    assert "None of the listed" in t.describe(("unlisted",))


def test_adding_equipment_rescored_earlier_answers():
    c = case(max_candidates=3)                                                          # 2-04, 2-05, 2-06: the east-side boxes are not on the list
    s = Session(c)
    for t in ("VAV-2-04", "VAV-2-05", "VAV-2-06"):
        s.report("no", "override_diffuser", t)                                          # nothing on the list makes the room respond
    causes, before = s.posterior()
    assert ("wrong", "VAV-2-01") not in causes and causes[int(before.argmax())] in (("unlisted",), ("doc_acts_fail",))
    n = s.entries
    s.add_candidate("VAV-2-01")
    causes2, after = s.posterior()
    assert ("wrong", "VAV-2-01") in causes2 and s.entries == n + 1
    assert after[causes2.index(("wrong", "VAV-2-01"))] > 0.05                           # the new candidate is credited with the earlier "no" on all the others
    assert c.weights["VAV-2-01"] == c.settings.other_area_weight                       # it sits on the other side of the floor
    with pytest.raises(KeyError):
        s.add_candidate("VAV-9-99")
    with pytest.raises(ValueError):
        s.add_candidate("Room-201")                                                     # not a box
    with pytest.raises(ValueError):
        s.add_candidate("VAV-2-01")                                                     # already there


def test_entries_count_what_the_technician_typed():
    assert Session(case()).entries == 1 and Session(case(airflow="no")).entries == 2
    s = Session(case(airflow="no"))
    s.recommend()
    s.report("yes")
    assert s.entries == 3


def test_ahu_vav_slot():
    c = case(member="VAV-2-04", slot="ahu_vav")
    assert c.candidates == ["AHU-2", "AHU-1"] and c.doc == "AHU-2"
    s = Session(c)
    causes, _ = s.posterior()
    assert causes == [("doc_ok",), ("wrong", "AHU-1"), ("unlisted",)]
    assert s.recommend().check.name in ("shutdown_watch", "duct_trace")
    out = sim.simulate(make_case(building(), "VAV-2-04", "ahu_vav", near_perfect()), ("wrong", "AHU-1"), rng=np.random.default_rng(0))
    assert out["concluded"] and out["correct"]


def test_settings_are_editable_and_immutable():
    s = Settings()
    s2 = s.with_check("vav_zone", "duct_trace", access_min=0, do_min=1)
    assert s2.menu("vav_zone")[2].minutes(None, "X") == 1 and s.menu("vav_zone")[2].minutes(None, "X") == 25
    with pytest.raises(KeyError):
        s.with_check("vav_zone", "nope", access_min=1)
    cheap = Session(make_case(building(), "Room-204", settings=s2.with_check("vav_zone", "override_diffuser", access_min=100, wait_min=100)))
    cheap.report("yes", "confirm_acts", "VAV-2-04")
    assert cheap.recommend().check.name in ("duct_trace", "override_room")              # a check made very expensive is not the pick


def test_drawings_rating_changes_only_the_prior_that_the_documented_feeder_is_wrong():
    base = Settings()
    assert base.with_drawings("mixed") == base                                           # the default rating is the default: leaving it unset changes nothing
    assert set(M.DRAWINGS) == {"mostly_right", "mixed", "poor"} and M.DRAWINGS["mixed"] == base.p_wrong
    for level, p in M.DRAWINGS.items():
        s = base.with_drawings(level)
        assert s == replace(base, p_wrong=p) and s.p_acts_fail == base.p_acts_fail and s.menus == base.menus and s.tau == base.tau
    prior = {lv: M.make_prior("vav_zone", ["D", "A", "B"], "D", base.with_drawings(lv))[1] for lv in M.DRAWINGS}
    assert prior["mostly_right"][0] > prior["mixed"][0] > prior["poor"][0]              # more mass on "the documented box is right" as the rating improves
    assert prior["mostly_right"][2:].sum() < prior["mixed"][2:].sum() < prior["poor"][2:].sum()
    assert all(np.isclose(p.sum(), 1.0) for p in prior.values())
    assert np.allclose(prior["mixed"], M.make_prior("vav_zone", ["D", "A", "B"], "D", base)[1])
    with pytest.raises(ValueError):
        base.with_drawings("excellent")
    assert base.p_wrong == 0.15                                                            # the original is untouched


def test_cli_drawings_option_reaches_the_case(monkeypatch, capsys):
    seen = []
    real_make_case = cli.make_case
    monkeypatch.setattr(cli, "make_case", lambda *a, **k: (seen.append(a[3]), real_make_case(*a, **k))[1])
    cli.main(["--demo", "--drawings", "mostly_right"])
    cli.main(["--demo"])
    assert "[demo]" in capsys.readouterr().out
    assert [x.p_wrong for x in seen] == [M.DRAWINGS["mostly_right"], M.DRAWINGS["mixed"]]   # unset = the default prior
    with pytest.raises(SystemExit):
        cli.main(["--demo", "--drawings", "excellent"])


# ---------------------------------------------------------------------------------------------- building input
def test_building_loader_and_candidate_rules(tmp_path):
    b = building()
    c = make_case(b, "Room-204")
    assert c.doc == "VAV-2-04" and c.candidates[:3] == ["VAV-2-04", "VAV-2-05", "VAV-2-06"] and len(c.candidates) == 6     # same floor side first, then the rest
    assert [c.weights[x] for x in c.candidates] == [1, 1, 1, 0.25, 0.25, 0.25]
    assert c.member_name == "Room 204" and b.label("VAV-2-04") == "2-04"
    assert len(make_case(b, "Room-204", max_candidates=2).candidates) == 2
    with pytest.raises(ValueError):
        make_case(b, "Room-999")
    with pytest.raises(ValueError):
        make_case(b, "VAV-2-04")                                                        # a box has no vav_zone claim
    with pytest.raises(ValueError):
        make_case(b, "Room-204", slot="loop_branch")
    with pytest.raises(ValueError):
        make_case(b, "Room-204", airflow="maybe")
    bad = json.loads(EXAMPLE.read_text())
    bad["claims"]["vav_zone"]["Room-204"] = "VAV-9-99"
    (tmp_path / "bad.json").write_text(json.dumps(bad))
    with pytest.raises(ValueError):
        load_building(tmp_path / "bad.json")
    dup = json.loads(EXAMPLE.read_text())
    dup["equipment"].append(dup["equipment"][0])
    (tmp_path / "dup.json").write_text(json.dumps(dup))
    with pytest.raises(ValueError):
        load_building(tmp_path / "dup.json")
    no_area = json.loads(EXAMPLE.read_text())
    for e in no_area["equipment"]:
        e.pop("area")
    (tmp_path / "na.json").write_text(json.dumps(no_area))
    cn = make_case(load_building(tmp_path / "na.json"), "Room-204")
    assert set(cn.weights.values()) == {1.0}                                            # unknown areas: no nearness prior at all


# ---------------------------------------------------------------------------------------------- the simulated technician and the habit stand-in
def test_simulation_is_reproducible_and_solves_the_case_when_checks_are_reliable():
    c = make_case(building(), "Room-204", settings=near_perfect())
    for truth in (("wrong", "VAV-2-05"), ("wrong", "VAV-2-02"), ("doc_acts_fail",), ("doc_other",), ("unlisted",)):
        out = sim.simulate(c, truth, rng=np.random.default_rng(0))
        if truth == ("unlisted",):
            assert out["stalled"] or out["concluded"]                                   # nothing on the list fits; it may or may not reach tau within the checks available
        else:
            assert out["concluded"] and out["correct"], truth
    a = sim.simulate(case(), ("wrong", "VAV-2-05"), rng=np.random.default_rng(5))
    b = sim.simulate(case(), ("wrong", "VAV-2-05"), rng=np.random.default_rng(5))
    assert a == b and a["entries"] == 1 + a["n_checks"]
    with pytest.raises(ValueError):
        sim.simulate(case(), ("wrong", "VAV-9-99"))


def test_wrong_assumed_rates_are_visible_in_the_simulator():
    c = case()
    true = Settings().with_check("vav_zone", "override_diffuser", tpr=0.55, fpr=0.45)
    wrong_rates = [sim.simulate(c, ("wrong", "VAV-2-05"), rng=np.random.default_rng(s), true_settings=true)["correct"] for s in range(40)]
    right_rates = [sim.simulate(c, ("wrong", "VAV-2-05"), rng=np.random.default_rng(s))["correct"] for s in range(40)]
    assert sum(wrong_rates) <= sum(right_rates)                                         # a diffuser check that is nearly a coin flip cannot help


def test_sampled_truths_follow_the_prior():
    c = case()
    causes, prior = M.make_prior(c.slot, c.candidates, c.doc, c.settings, c.airflow, c.weights)
    rng = np.random.default_rng(0)
    draws = [sim.sample_truth(c, rng) for _ in range(4000)]
    for i, cause in enumerate(causes):
        f = draws.count(cause) / 4000
        assert abs(f - prior[i]) < 4 * np.sqrt(prior[i] * (1 - prior[i]) / 4000) + 1e-3, cause


def test_habit_stand_in_orders_its_checks_as_documented():
    c = make_case(building(), "Room-204", settings=near_perfect())
    h = lambda truth: sim.simulate_habit(c, truth, rng=np.random.default_rng(0))  # noqa: E731
    assert h(("doc_acts_fail",))["n_checks"] == 1 and h(("doc_acts_fail",))["correct"]     # box does not move: found immediately
    assert h(("doc_other",))["n_checks"] == 2 and h(("doc_other",))["correct"]             # acts, then the room responds
    assert h(("wrong", "VAV-2-05"))["n_checks"] == 3 and h(("wrong", "VAV-2-05"))["correct"]
    assert h(("wrong", "VAV-2-06"))["n_checks"] == 4
    assert h(("unlisted",))["correct"] and h(("unlisted",))["n_checks"] == 1 + len(c.candidates)
    ahu = make_case(building(), "VAV-2-04", "ahu_vav", near_perfect())
    assert sim.simulate_habit(ahu, ("doc_ok",), rng=np.random.default_rng(0))["n_checks"] == 1


@pytest.mark.parametrize("strategy", M.STRATEGIES)
def test_every_strategy_runs_a_session_to_an_end(strategy):
    out = sim.simulate(case(), ("wrong", "VAV-2-06"), strategy=strategy, rng=np.random.default_rng(2))
    assert out["n_checks"] >= 1 and out["minutes"] > 0 and out["guess"] is not None


# ---------------------------------------------------------------------------------------------- the command-line loop
def test_cli_scripted_session_reaches_a_conclusion():
    c = make_case(building(), "Room-204", settings=near_perfect())
    s = Session(c)
    lines = []
    st = cli.run(s, sim.technician_input(s, ("wrong", "VAV-2-05"), np.random.default_rng(0), echo=lambda *_: None), out=lines.append)
    text = "\n".join(lines)
    assert st["concluded"] and "Likely cause" in text and "2-05" in text and "entries typed" in text


def test_cli_quit_add_and_bad_input():
    s = Session(make_case(building(), "Room-204", max_candidates=3))
    answers = iter(["hello", "a", "VAV-9-99", "a", "VAV-2-01", "q"])
    lines = []
    st = cli.run(s, lambda prompt: next(answers), out=lines.append)
    text = "\n".join(lines)
    assert "Please answer" in text and "Could not add" in text and "Added VAV-2-01" in text and "Stopped." in text
    assert "VAV-2-01" in s.case.candidates and not st["concluded"]
    eof = Session(case())
    lines2 = []
    cli.run(eof, lambda prompt: (_ for _ in ()).throw(EOFError()), out=lines2.append)
    assert "Stopped." in "\n".join(lines2)


def test_cli_main_demo_runs(capsys):
    cli.main(["--demo"])
    out = capsys.readouterr().out
    assert "[demo]" in out and ("Likely cause" in out or "No further check" in out)
