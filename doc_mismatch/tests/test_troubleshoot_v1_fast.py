"""Guards for the v1-versus-fast-stand-in study code (docmismatch.troubleshoot.v1.study_fast_v1, scripts/72; PREREGISTRATION_DR.md Addendum 28). No test reads a study result: they check code
paths, rules and gates on scripted transcripts, synthetic arrays and tiny runs whose numbers are never inspected."""
import importlib.util
import pickle
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot import model as M, sim  # noqa: E402
from docmismatch.troubleshoot import building as B0  # noqa: E402
from docmismatch.troubleshoot.v1 import catalogue as K, causes as C, data as D, engine as E, sim1, study_fast_v1 as F, study_tiers as T  # noqa: E402

spec = importlib.util.spec_from_file_location("script72", ROOT / "scripts" / "72_troubleshoot_v1_fast.py")
S72 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S72)

PRIMARY = T.Cell(**T.PRIMARY)
CASES = T.make_cases("full")
CTX = dict(reheat="no", bas_access="no", instrument="yes", occupant="yes")          # room 0: no reheat
CTX3 = dict(reheat="yes", bas_access="yes", instrument="yes", occupant="yes")       # room 1: reheat


def script(positive=(), default_positive=False):
    """An `ask` that answers positive (abnormal / yes) for the named checks and negative for the rest, and records what it was asked."""
    asked = []

    def ask(ck, target):
        asked.append((ck.name, target))
        pos = ck.name in positive or default_positive
        return ck.words[0] if pos else ck.words[1]
    ask.asked = asked
    return ask


# ---------------------------------------------------------------------------------------------- frozen constants and the checklist
def test_the_frozen_constants():
    assert (F.SEED, F.N_EPISODES, F.BOOT_B, F.SINGLE_P, F.CONFIRM_P) == (28, 500, 1000, 0.75, 0.5)
    assert F.POLICIES == ("habit_A", "fast_list", "fast_confirm") and F.EXACT_STANDS == ("fast_list", "fast_confirm") and F.SUBSETS == ("hw", "doc") and F.LEVELS == ("exact", "v0")
    assert F.LUMPS == (("doc_other",), ("doc_acts_fail",)) and len(F.GUESS_CAUSES) == len(T.ALL_CAUSES) + 2 and F.GUESS_INDEX[("doc_acts_fail",)] == len(T.ALL_CAUSES) + 1


def test_the_checklist_is_the_reading_checks_that_name_exactly_one_cause():
    named = {c.name: F.single_cause(c) for c in K.CATALOGUE if F.single_cause(c)}
    assert named == {"bas_ahu_fan": ("ahu_fan_off",), "bas_controller": ("controller_comms",), "bas_zone": ("zone_sensor_setpoint",), "bas_reheat": ("reheat_fail",), "power_24vac": ("no_power",),
                     "control_signal": ("signal_fault",), "manual_damper_test": ("damper_mech",), "damper_linkage": ("damper_mech",), "controller_leds": ("controller_comms",),
                     "sensing_ports": ("flow_sensor",), "flow_vs_gauge": ("flow_sensor",), "reheat_coil": ("reheat_fail",), "ahu_visit": ("ahu_fan_off",), "diffuser_duct": ("duct_diffuser",),
                     "thermostat": ("zone_sensor_setpoint",), "design_load": ("capacity_design",)}
    for name in ("bas_static", "bas_airflow", "bas_damper", "static_at_box", "flow_hood", "ask_occupant", "k_factor", "max_airflow", "ahu_gauge", "bas_hunting"):
        assert F.single_cause(K.BY_NAME[name]) is None                              # two causes at 0.75 or more, or none: not on the checklist
    assert all(K.BY_NAME[n].is_reading for n in named) and F.single_cause(K.BY_NAME["override_room"]) is None
    assert all(cause[0] in C.BY_ID for cause in named.values())


def doer(arm, room, ctx):
    return F.Doer(CASES[(arm, room)], ctx, script())


def test_the_available_checklist_follows_the_arm_and_the_worlds_facts_cheapest_first():
    names = lambda arm, room, ctx: [n for _, n, ck in F.available_readings(CASES[(arm, room)], doer(arm, room, ctx)) if F.single_cause(ck)]  # noqa: E731
    t2 = names("T2", 0, CTX)
    assert t2 == ["design_load", "controller_leds", "power_24vac", "thermostat", "control_signal", "manual_damper_test", "damper_linkage", "sensing_ports", "diffuser_duct", "ahu_visit"]   # no reheat, no BAS
    t1 = names("T1", 0, CTX)
    assert "design_load" not in t1 and t1[0] == "controller_leds"                                         # no design values at T1
    t0 = names("T0", 0, CTX)
    assert "design_load" not in t0 and "ahu_visit" in t0 and t0.index("ahu_visit") == len(t0) - 1        # +10 to find the air handler: the most expensive
    t3 = names("T3", 1, CTX3)
    assert t3[:4] == ["bas_ahu_fan", "bas_controller", "bas_reheat", "bas_zone"] and "reheat_coil" in t3 and "flow_vs_gauge" in t3     # 2-minute reads first, ties by name
    t2a = names("T2+access", 1, CTX3)
    assert t2a[0] == "design_load" and "bas_ahu_fan" in t2a and t2a.index("bas_ahu_fan") > t2a.index("controller_leds")               # a read costs 10 without the point map
    no_gauge = names("T3", 1, dict(CTX3, instrument="no", occupant="no", reheat="no"))
    assert not {"flow_vs_gauge", "reheat_coil", "bas_reheat"} & set(no_gauge)
    costs = [c for c, _, _ in F.available_readings(CASES[("T3", 1)], doer("T3", 1, CTX3))]
    assert costs == sorted(costs)
    assert all(ck.is_reading for _, _, ck in F.available_readings(CASES[("T3", 1)], doer("T3", 1, CTX3)))       # the four v0 checks are never on it


# ---------------------------------------------------------------------------------------------- fast_list, fast_confirm, habit_A
def test_fast_list_stops_at_the_first_abnormal_reading_and_names_its_cause():
    ask = script(positive=("power_24vac",))
    r = F.run_fast(CASES[("T2", 0)], CTX, ask)
    assert r["guess"] == ("no_power",) and r["sequence"] == ("design_load", "controller_leds", "power_24vac") and r["minutes"] == 6 + 9 + 4 and r["n_checks"] == 3 and r["entries"] == 4
    assert ask.asked == [("design_load", "VAV-0"), ("controller_leds", "VAV-0"), ("power_24vac", "VAV-0")]
    assert [t[3] for t in r["trace"]] == ["normal", "normal", "abnormal"] and r["trace"][0][:3] == ("C", "design_load", "VAV-0")
    r3 = F.run_fast(CASES[("T3", 1)], CTX3, script(positive=("bas_ahu_fan",)))
    assert r3["guess"] == ("ahu_fan_off",) and r3["minutes"] == 2 and r3["sequence"] == ("bas_ahu_fan",)


def test_a_finding_of_a_check_that_sees_several_causes_is_not_concluded_on_by_the_checklist():
    ask = script(positive=("bas_airflow", "static_at_box", "flow_hood"))                           # abnormal, but none of them names one cause: they are not on the list
    r = F.run_fast(CASES[("T3", 1)], CTX3, ask)
    assert not {"bas_airflow", "static_at_box", "flow_hood"} & set(r["sequence"])


def test_when_the_whole_list_is_normal_the_alternative_boxes_are_walked_and_a_yes_names_the_box():
    case = CASES[("T1", 0)]
    ask = script(positive=("override_diffuser",))
    r = F.run_fast(case, CTX, ask)
    assert r["guess"] == ("wrong", case.candidates[1]) and r["sequence"][-1] == "override_diffuser" and r["trace"][-1][2] == case.candidates[1]
    assert all(t[1] != "override_diffuser" or t[2] != case.doc for t in r["trace"])                 # the documented box is not walked: the list has just cleared it
    listed = [t for t in r["trace"] if t[1] not in ("override_room", "override_diffuser")]
    assert len(listed) == 9 and all(t[3] == "normal" for t in listed)                               # the whole T1 list, no design_load
    ask2 = script(positive=())
    r2 = F.run_fast(case, CTX, ask2)
    assert r2["guess"] == ("other",) and [t[2] for t in r2["trace"] if t[1] == "override_diffuser"] == case.candidates[1:]
    # minutes are the tool's accounting: recomputed here from the trace
    at, total = None, 0.0
    s = E.Session(case)
    s.ctx = D.Context(**CTX)
    for _, name, target, _w in r2["trace"]:
        ck = K.BY_NAME[name]
        extra = D.availability(ck, s.view(), s._eq(ck)).extra_min
        place = {"target": target, "box": case.doc, "room": case.member, "ahu": case.ahu, "bas": "bas"}[ck.place]
        total += ck.minutes(at, place, extra)
        at = place
    assert r2["minutes"] == pytest.approx(total)


def test_at_t0_a_normal_list_ends_in_other_with_no_walk():
    r = F.run_fast(CASES[("T0", 0)], CTX, script())
    assert r["guess"] == ("other",) and all(t[1] not in ("override_room", "override_diffuser") for t in r["trace"])
    assert F.walk_alternatives(CASES[("T0", 0)], doer("T0", 0, CTX)) is None


def test_fast_confirm_needs_a_second_check_that_sees_the_same_cause():
    case = CASES[("T2", 0)]
    confirmers = [c.name for c in case.checks if c.is_reading and c.detects.get("no_power", 0) >= 0.5]
    assert confirmers == ["bas_airflow", "bas_damper", "power_24vac", "flow_hood"]                  # bas_* are unavailable at T2, leaving the flow hood
    r = F.run_fast(case, CTX, script(positive=("power_24vac", "flow_hood")), confirm=True)
    assert r["guess"] == ("no_power",) and r["sequence"] == ("design_load", "controller_leds", "power_24vac", "flow_hood")
    assert r["minutes"] == 6 + 9 + 4 + (5 + 8)                                                        # the hood is in the room: 5 to get there, 8 to do
    r = F.run_fast(case, dict(CTX, instrument="no"), script(positive=("power_24vac",)), confirm=True)
    assert r["guess"] == ("no_power",) and r["sequence"][-1] == "power_24vac"                        # no gauge: no second check exists, so the reading stands


def test_a_finding_that_is_not_confirmed_is_discarded_and_the_list_goes_on():
    case = CASES[("T2", 0)]
    r = F.run_fast(case, CTX, script(positive=("power_24vac",)), confirm=True)                       # the hood says normal
    seq = r["sequence"]
    assert seq[:4] == ("design_load", "controller_leds", "power_24vac", "flow_hood") and seq[4] == "thermostat" and r["guess"] == ("other",)
    assert len(set((t[1], t[2]) for t in r["trace"])) == len(r["trace"])                              # nothing is done twice
    case3 = CASES[("T3", 1)]
    r3 = F.run_fast(case3, CTX3, script(positive=("bas_ahu_fan", "ahu_visit")), confirm=True)        # both fan findings are refuted by their confirmations
    assert r3["sequence"][:2] == ("bas_ahu_fan", "bas_airflow") and "ahu_visit" in r3["sequence"] and r3["guess"] == ("other",)
    assert r3["trace"][r3["sequence"].index("ahu_visit") + 1][1] == "bas_damper"                      # the cheapest not-yet-done check that sees a fan fault at 0.5 or more (ties by name)
    r4 = F.run_fast(case3, CTX3, script(positive=("bas_ahu_fan", "bas_airflow")), confirm=True)
    assert r4["guess"] == ("ahu_fan_off",) and r4["sequence"] == ("bas_ahu_fan", "bas_airflow") and r4["minutes"] == 4
    pairs = [(t[1], t[2]) for t in r3["trace"]]
    assert len(pairs) == len(set(pairs))                                                              # the same check name may repeat on other boxes (the walk), never the same pair


def test_a_discarded_finding_lets_the_list_reach_the_next_finding():
    case = CASES[("T3", 1)]
    positive = {"bas_ahu_fan", "bas_zone", "thermostat"}                                              # the fan finding has no supporting check; the zone finding is supported by the thermostat
    r = F.run_fast(case, CTX3, lambda ck, target: ck.words[0] if ck.name in positive else ck.words[1], confirm=True)
    seq = list(r["sequence"])
    assert seq[0] == "bas_ahu_fan" and seq[1] == "bas_airflow" and "bas_zone" in seq and seq[-1] == "thermostat"
    assert r["guess"] == ("zone_sensor_setpoint",) and len(seq) == len(set(seq))


def test_habit_A_on_the_v0_equivalent_tree_is_v0s_habit_exactly():
    b = T.make_building1("full")
    for room in (0, 5):
        c0 = B0.make_case(b.base, f"Room-{room}", max_candidates=8)
        c1 = E.make_case_v1(b, f"Room-{room}", "T1", compat_v0=True, max_candidates=8)
        causes = M.make_prior("vav_zone", c0.candidates, c0.doc, c0.settings, None, c0.weights)[0]
        for seed in range(3):
            for k, truth in enumerate(causes):
                r0 = sim.simulate_habit(c0, truth, np.random.default_rng(100 * seed + k))
                w = sim1.World(truth)
                r1 = F.run_habit_A(c1, w.context, F.ask_from_world(c1, w, np.random.default_rng(100 * seed + k)))
                assert (r0["guess"], r0["n_checks"], r0["entries"]) == (r1["guess"], r1["n_checks"], r1["entries"]) and r0["minutes"] == pytest.approx(r1["minutes"])


def test_habit_A_scripted_paths():
    case = CASES[("T1", 0)]
    r = F.run_habit_A(case, CTX, script())                                                         # the box does not move
    assert r["guess"] == ("doc_acts_fail",) and r["sequence"] == ("confirm_acts",)
    r = F.run_habit_A(case, CTX, script(positive=("confirm_acts", "override_room", "override_diffuser")))
    assert r["guess"] == ("doc_other",) and r["sequence"] == ("confirm_acts", "override_diffuser") and r["trace"][1][2] == case.doc     # the cheaper observer first: after the box, the diffuser (5) beats the room (32)
    r = F.run_habit_A(case, CTX, script(positive=("confirm_acts",)))
    assert r["guess"] == ("unlisted",) and len(r["trace"]) == 1 + len(case.candidates)              # every candidate, the documented box included, then unlisted

    def ask(ck, target):
        return ck.words[0] if (ck.name == "confirm_acts" or target == case.candidates[2]) else ck.words[1]
    r = F.run_habit_A(case, CTX, ask)
    assert r["guess"] == ("wrong", case.candidates[2]) and [t[2] for t in r["trace"][1:]] == case.candidates[:3]
    r0 = F.run_habit_A(CASES[("T0", 0)], CTX, script(positive=("confirm_acts",)))
    assert r0["guess"] == ("unlisted",) and len(r0["trace"]) == 2                                   # T0: the one generic box


def test_a_stand_in_cannot_do_the_same_check_twice_and_is_charged_like_the_tool():
    d = doer("T2", 0, CTX)
    d.do(K.BY_NAME["power_24vac"], "VAV-0")
    with pytest.raises(ValueError, match="already done"):
        d.do(K.BY_NAME["power_24vac"], "VAV-0")
    assert d.s.elapsed == 10 and d.s.at == "VAV-0"
    d.do(K.BY_NAME["control_signal"], "VAV-0")
    assert d.s.elapsed == 10 + 6 and d.result(("other",))["entries"] == 3
    assert F.run_policy("fast_list", CASES[("T1", 0)], sim1.World(("other",), CTX), script())["guess"] == ("other",)
    with pytest.raises(ValueError, match="unknown stand-in"):
        F.run_policy("magic", CASES[("T1", 0)], sim1.World(("other",), CTX), script())


def test_replay_needs_only_the_recorded_answers_and_notices_any_difference():
    case = CASES[("T3", 1)]
    w = sim1.World(("low_static",), CTX3, K.degrade_all(K.CATALOGUE, 0.5))
    for pol in F.POLICIES:
        r = F.run_policy(pol, case, w, F.ask_from_world(case, w, np.random.default_rng(3)))
        assert F.replay(pol, case, CTX3, r["trace"]) and r["trace"]
        bad = [list(x) for x in r["trace"]]
        bad[0][1] = "power_24vac" if bad[0][1] != "power_24vac" else "control_signal"
        assert not F.replay(pol, case, CTX3, bad) and not F.replay(pol, case, CTX3, r["trace"][:-1] or [("C", "zzz", "x", "normal")])
    ask = F.ask_from_trace([("C", "power_24vac", "VAV-0", "normal")])
    assert ask(K.BY_NAME["power_24vac"], "VAV-0") == "normal"
    with pytest.raises(ValueError):
        ask(K.BY_NAME["power_24vac"], "VAV-0")                                                      # nothing left to answer with
    wrong = F.ask_from_trace([("C", "power_24vac", "VAV-0", "normal")])
    with pytest.raises(ValueError, match="asked for something else"):
        wrong(K.BY_NAME["control_signal"], "VAV-0")                                                 # not the next recorded check
    with pytest.raises(ValueError, match="asked for something else"):
        F.ask_from_trace([("C", "power_24vac", "VAV-0", "normal")])(K.BY_NAME["power_24vac"], "VAV-1")   # nor the same check on another box


# ---------------------------------------------------------------------------------------------- the runner
@pytest.fixture(scope="module")
def tiny():
    return F.run_cell(0, PRIMARY, 10)


def test_the_tool_in_the_runner_is_addendum_27s_exactly(tiny):
    base = T.run_cell(0, PRIMARY, 10)
    for arm in T.ARM_NAMES:
        for k in ("minutes", "checks", "guess_idx", "correct", "concluded", "valid"):
            x, y = tiny["base"]["arm"][arm][k], base["arm"][arm][k]
            assert np.array_equal(x, y, equal_nan=True) if x.dtype.kind == "f" else np.array_equal(x, y)


def test_a_cell_has_every_policy_and_arm_and_is_paired_with_the_tool(tiny):
    assert set(tiny["pol"]) == set(F.POLICIES) and tiny["n"] == 10
    hw = T.hw_mask(tiny["base"])
    for pol in F.POLICIES:
        for arm in T.ARM_NAMES:
            a = tiny["pol"][pol][arm]
            assert np.array_equal(a["valid"], hw if arm == "T0" else np.ones(10, bool)) and all(len(v) == 10 for v in a.values())
            assert np.isfinite(a["minutes"][a["valid"]]).all() and (a["guess_idx"][a["valid"]] >= 0).all() and (a["guess_idx"][~a["valid"]] == -1).all()
    h = tiny["pol"]["habit_A"]
    for arm in ("T2", "T2+access", "T3"):
        assert np.array_equal(h[arm]["guess_idx"], h["T1"]["guess_idx"]) and np.array_equal(h[arm]["minutes"], h["T1"]["minutes"]) and h[arm]["trace"] == h["T1"]["trace"]


def test_the_stand_ins_streams_are_the_frozen_ones_and_a_cell_is_reproducible(tiny):
    cell = PRIMARY
    cases, tc = T.make_cases(cell.cover), K.degrade_all(K.CATALOGUE, T.REL_A[cell.rel])
    e = T.draw_episode(0, 2, cell.mix, cases)
    for pi, pol in enumerate(F.POLICIES):
        for arm in ("T1", "T3"):
            case, w = cases[(arm, e["room"])], T.world_for(e, arm, tc)
            r = F.run_policy(pol, case, w, F.ask_from_world(case, w, np.random.default_rng([28, 0, pi, 2])))
            assert tiny["pol"][pol][arm]["minutes"][2] == r["minutes"] and tiny["pol"][pol][arm]["trace"][2] == r["trace"]
    again, small = F.run_cell(0, PRIMARY, 10), F.run_cell(0, PRIMARY, 6)
    for pol in F.POLICIES:
        for arm in T.ARM_NAMES:
            assert again["pol"][pol][arm]["trace"] == tiny["pol"][pol][arm]["trace"] and small["pol"][pol][arm]["trace"] == tiny["pol"][pol][arm]["trace"][:6]


def test_compute_cells_does_not_depend_on_the_number_of_workers():
    jobs = list(enumerate(T.all_cells()))[:2]
    a, b = F.compute_cells(jobs, 4, workers=1), F.compute_cells(jobs, 4, workers=2)
    for x, y in zip(a, b):
        for pol in F.POLICIES:
            for arm in T.ARM_NAMES:
                assert x["pol"][pol][arm]["trace"] == y["pol"][pol][arm]["trace"]


# ---------------------------------------------------------------------------------------------- levels and summaries
def fake(n=40, n_hw=32):
    """A hand-built result: causes 0..n_hw-1 are actuator_fail, the rest wrong(VAV-1); every policy identical and fully right, minutes 50, 5 checks, 7 entries, tool concluded."""
    truth = np.array([T.CAUSE_INDEX[("actuator_fail",)]] * n_hw + [T.CAUSE_INDEX[("wrong", "VAV-1")]] * (n - n_hw))
    rng = np.random.default_rng(0)

    def tool():
        return dict(valid=np.ones(n, bool), minutes=50.0 + rng.normal(0, 1, n), checks=np.full(n, 5.0), questions=np.full(n, 1.0), entries=np.full(n, 7.0), concluded=np.ones(n, bool),
                    stalled=np.zeros(n, bool), correct=np.ones(n, bool), guess_idx=truth.copy(), group_ok=np.ones(n, bool), sequence=[()] * n, trace=[[]] * n)

    def stand():
        return dict(valid=np.ones(n, bool), minutes=50.0 + rng.normal(0, 1, n), checks=np.full(n, 5.0), entries=np.full(n, 6.0), guess_idx=np.array([F.GUESS_INDEX[T.ALL_CAUSES[t]] for t in truth]),
                    sequence=[()] * n, trace=[[]] * n)
    base = dict(idx=0, cell=PRIMARY, n=n, room=np.zeros(n, int), truth_idx=truth, instrument=np.ones(n, bool), occupant=np.ones(n, bool), arm={a: tool() for a in T.ARM_NAMES})
    res = dict(idx=0, cell=PRIMARY, n=n, base=base, pol={p: {a: stand() for a in T.ARM_NAMES} for p in F.POLICIES})
    for d in (base["arm"]["T0"], *(res["pol"][p]["T0"] for p in F.POLICIES)):
        d["valid"] = T.hw_mask(base).copy()
        d["minutes"] = np.where(d["valid"], d["minutes"], np.nan)
    return res


def gi(cause):
    return F.GUESS_INDEX[cause]


def test_the_two_levels_of_a_guess():
    res = fake()
    st = res["pol"]["fast_list"]["T1"]
    st["guess_idx"][0] = gi(("damper_mech",))                                                       # truth actuator_fail: same lump (the box does not act), different cause
    st["guess_idx"][1] = gi(("low_static",))                                                        # a different lump
    st["guess_idx"][2] = gi(("doc_acts_fail",))                                                      # a lump as a guess: right at v0's level only
    st["guess_idx"][3] = gi(("unlisted",))
    st["guess_idx"][35] = gi(("wrong", "VAV-1"))                                                     # the truth of episode 35 is wrong(VAV-1): right at both
    st["guess_idx"][36] = gi(("wrong", "VAV-2"))                                                     # the wrong box: wrong at both
    v = F.episode_view(res, "fast_list", "T1")
    assert [bool(v["exact"][i]) for i in (0, 1, 2, 3, 35, 36)] == [False, False, False, False, True, False]
    assert [bool(v["v0"][i]) for i in (0, 1, 2, 3, 35, 36)] == [True, False, True, False, True, False]
    assert v["concluded"].all() and v["questions"].sum() == 0
    tool = res["base"]["arm"]["T3"]
    tool["guess_idx"][0] = T.CAUSE_INDEX[("controller_comms",)]                                      # acts-fail lump = the truth's lump
    tool["guess_idx"][1] = T.CAUSE_INDEX[("ahu_fan_off",)]
    tool["concluded"][1] = False
    tv = F.episode_view(res, "tool", "T3")
    assert (bool(tv["exact"][0]), bool(tv["v0"][0]), bool(tv["v0"][1]), bool(tv["concluded"][1]), tv["questions"][0]) == (False, True, False, False, 1.0)
    t0 = F.episode_view(res, "tool", "T0")
    assert not t0["valid"][35] and not t0["exact"][35] and not t0["concluded"][35]


def test_summaries_count_the_tools_confident_errors_but_all_of_a_stand_ins_errors():
    res = fake()
    tool, st = res["base"]["arm"]["T3"], res["pol"]["fast_list"]["T3"]
    tool["guess_idx"][:4] = T.CAUSE_INDEX[("low_static",)]                                          # 4 wrong; two of them concluded, two not
    tool["concluded"][2:4] = False
    st["guess_idx"][:4] = gi(("low_static",))
    hw = T.hw_mask(res["base"])
    a, b = F.summarize(F.episode_view(res, "tool", "T3"), hw, "exact"), F.summarize(F.episode_view(res, "fast_list", "T3"), hw, "exact")
    assert a["n"] == b["n"] == 32 and a["accuracy"] == b["accuracy"] == pytest.approx(28 / 32)
    assert a["wrong_confident"] == pytest.approx(2 / 32) and b["wrong_confident"] == pytest.approx(4 / 32) and a["concluded"] == pytest.approx(30 / 32) and b["concluded"] == 1.0
    assert a["per_correct"] == pytest.approx(a["minutes"] / a["accuracy"]) and a["entries"] == 7.0 and b["entries"] == 6.0 and a["checks"] == 5.0
    assert F.summarize(F.episode_view(res, "tool", "T0"), ~hw, "exact") == dict(n=0)
    doc = F.summarize(F.episode_view(res, "tool", "T3"), ~hw, "v0")
    assert doc["n"] == 8 and doc["accuracy"] == 1.0


@pytest.mark.parametrize("m_t,a_t,m_s,a_s,kind,val", [(40, 0.9, 50, 0.8, "DOMINATES", 0.0), (50, 0.8, 50, 0.8, "DOMINATES", 0.0), (60, 0.7, 50, 0.8, "DOMINATED", float("inf")),
                                                    (50, 0.7, 50, 0.8, "DOMINATED", float("inf")), (50, 0.8, 50, 0.7, "DOMINATES", 0.0),
                                                    (60, 0.9, 40, 0.8, "SLOWER-MORE", 200.0), (30, 0.7, 40, 0.9, "FASTER-LESS", 50.0)])
def test_break_even_wrong_diagnosis_cost(m_t, a_t, m_s, a_s, kind, val):
    k, v = F.break_even(m_t, a_t, m_s, a_s)
    assert k == kind and v == pytest.approx(val)
    assert k in F.WRONG_COST_KINDS


def analyse(res, B=300):
    return F.analyze_cell(res, B)


def test_comparisons_are_tool_minus_stand_in_with_addendum_21s_labels():
    res = fake(n=80, n_hw=64)
    for arm in T.ARM_NAMES:
        for p in F.POLICIES:
            res["pol"][p][arm]["minutes"] = np.where(res["pol"][p][arm]["valid"], 30.0 + np.random.default_rng(1).normal(0, 1, 80), np.nan)
    hw = T.hw_mask(res["base"])
    an = analyse(res)
    e = an["cmp"][("T3", "fast_list", "hw", "exact")]
    assert e["d_min"] == pytest.approx(20, abs=1.5) and e["time"] == "SLOWER" and e["acc"] == "SAME" and e["label"] == "WORSE" and e["r_min"] == pytest.approx(0.67, abs=0.05)
    assert e["break_even"] == "DOMINATED"
    res["pol"]["fast_list"]["T3"]["guess_idx"][:40] = gi(("low_static",))                            # the stand-in is now wrong on half the hardware episodes: the tool is slower but more accurate
    an = analyse(res)
    e = an["cmp"][("T3", "fast_list", "hw", "exact")]
    assert (e["time"], e["acc"], e["label"]) == ("SLOWER", "MORE", "TRADE") and e["d_acc"] == pytest.approx(40 / 64) and e["break_even"] == "SLOWER-MORE"
    assert e["wrong_cost"] == pytest.approx(e["d_min"] / e["d_acc"], rel=0.05)
    assert e["safety"] == "GAIN" and e["d_wc"] < 0                                                    # the stand-in's errors are all confident, the tool's are not
    sh = F.shares([an], ("T3", "fast_list", "hw", "exact"))
    assert sh["TRADE"] == 1.0 and sh["SLOWER_MORE"] == 1.0 and sh["FASTER_LESS"] == 0.0 and sh["SAFETY_GAIN"] == 1.0 and sh["n_cells"] == 1
    res["base"]["arm"]["T3"]["minutes"] = res["pol"]["fast_list"]["T3"]["minutes"] * 0.5
    res["base"]["arm"]["T3"]["correct"][:40] = False
    res["base"]["arm"]["T3"]["guess_idx"][:40] = T.CAUSE_INDEX[("low_static",)]
    res["pol"]["fast_list"]["T3"]["guess_idx"][:40] = F.GUESS_INDEX[("actuator_fail",)]
    e = analyse(res)["cmp"][("T3", "fast_list", "hw", "exact")]
    assert (e["time"], e["acc"]) == ("FASTER", "LESS") and e["break_even"] == "FASTER-LESS"
    assert F.shares([analyse(res)], ("T3", "fast_list", "hw", "exact"))["FASTER_LESS"] == 1.0
    assert hw.sum() == 64


def test_the_analysis_has_the_registered_comparisons_and_the_frozen_bootstrap(tiny):
    an = F.analyze_cell(tiny, 100)
    assert an["n_hw"] + an["n_doc"] == 10
    keys = set(an["cmp"])
    subsets = ["hw"] + (["doc"] if an["n_doc"] else [])
    assert keys == {(arm, s, sub, lv) for sub in subsets for arm in T.ARM_NAMES if not (arm == "T0" and sub == "doc") for s, lv in F.combos()}
    assert ("T0", "habit_A", "doc", "v0") not in keys and ("T1", "habit_A", "hw", "exact") not in keys and ("T1", "habit_A", "hw", "v0") in keys
    assert F.combos() == [("fast_list", "exact"), ("fast_confirm", "exact"), ("habit_A", "v0"), ("fast_list", "v0"), ("fast_confirm", "v0")]
    for arm in T.ARM_NAMES:
        assert ("baseline", arm, "hw", "v0") in an["sum"] and ("habit_A", arm, "hw", "exact") not in an["sum"] and ("tool", arm, "hw", "exact") in an["sum"]
    res = fake(n=40, n_hw=32)
    res["idx"] = 4
    res["pol"]["fast_list"]["T3"]["minutes"] = res["pol"]["fast_list"]["T3"]["minutes"] * 0.7
    a2 = F.analyze_cell(res, 200)
    idx = np.flatnonzero(T.hw_mask(res["base"]))
    boot = np.random.default_rng([28, 4, 99, 0]).integers(0, len(idx), (200, len(idx)))
    d = res["base"]["arm"]["T3"]["minutes"][idx] - res["pol"]["fast_list"]["T3"]["minutes"][idx]
    assert a2["cmp"][("T3", "fast_list", "hw", "exact")]["ci_min"] == F.S.paired_ci(d, boot)
    didx = np.flatnonzero(~T.hw_mask(res["base"]))
    dboot = np.random.default_rng([28, 4, 99, 1]).integers(0, len(didx), (200, len(didx)))
    dd = res["base"]["arm"]["T3"]["minutes"][didx] - res["pol"]["fast_list"]["T3"]["minutes"][didx]
    assert a2["cmp"][("T3", "fast_list", "doc", "exact")]["ci_min"] == F.S.paired_ci(dd, dboot)


def test_the_constant_guess_baseline_is_the_share_of_episodes_whose_lump_is_the_box_acts():
    res = fake()
    res["base"]["truth_idx"][:24] = T.CAUSE_INDEX[("low_static",)]                                  # 24 of the 32 hardware episodes are in the lump 'the box acts, cause elsewhere'; the other 8 are actuator_fail
    an = F.analyze_cell(res, 50)
    assert an["sum"][("baseline", "T3", "hw", "v0")]["accuracy"] == pytest.approx(24 / 32) and an["sum"][("baseline", "T3", "doc", "v0")]["accuracy"] == 0.0
    none_doc = fake(n=20, n_hw=20)                                                                   # no documentation-wrong episode at all: the baseline is undefined, not zero
    b = F.analyze_cell(none_doc, 50)["sum"][("baseline", "T3", "doc", "v0")]
    assert b["n"] == 0 and np.isnan(b["accuracy"])


# ---------------------------------------------------------------------------------------------- predictions
def fake_analyses(over=None):
    """Analyses in which every prediction holds; `over` = {(cell factors, policy, arm, subset, level, field): value}."""
    out = []
    for cell in T.all_cells():
        s = {}
        for arm in T.ARM_NAMES:
            for sub in F.SUBSETS:
                for lv in F.LEVELS:
                    s[("tool", arm, sub, lv)] = dict(n=50, minutes=60.0, accuracy=0.80, wrong_confident=0.02, concluded=0.4)
                    for p in F.EXACT_STANDS + ("habit_A",):
                        s[(p, arm, sub, lv)] = dict(n=50, minutes=40.0, accuracy=0.60, wrong_confident=0.40, concluded=1.0)
                    s[("fast_confirm", arm, sub, lv)].update(minutes=45.0, accuracy=0.65)
        if cell.rel == "R2":
            for k, v in s.items():
                if k[0] == "tool":
                    v["accuracy"] = 0.62
        for arm in ("T3",):
            s[("tool", arm, "hw", "exact")]["minutes"] = 44.0                                        # ratio 1.1 at T3 against 1.5 at T0
        out.append(dict(cell=cell, sum=s))
    for (key, p, arm, sub, lv, field), v in (over or {}).items():
        for a in out:
            if all(getattr(a["cell"], k) == val for k, val in key):
                a["sum"][(p, arm, sub, lv)][field] = v
    return out


def test_every_prediction_holds_on_the_ideal_data_and_fails_when_its_condition_does():
    pr = F.fast_predictions(fake_analyses())
    assert set(pr) == {f"P{i}" for i in range(1, 10)} and all(v["holds"] for v in pr.values()), {k: v for k, v in pr.items() if not v["holds"]}
    P = lambda o: F.fast_predictions(fake_analyses(o))  # noqa: E731
    prim = tuple(sorted(T.PRIMARY.items()))
    r2 = (("rel", "R2"), ("mix", "assumed"), ("cover", "full"))
    assert not P({(prim, "fast_list", "T2+access", "hw", "exact", "minutes"): 60.0})["P1"]["holds"] and P({(prim, "fast_list", "T3", "hw", "exact", "minutes"): 90.0})["P1"]["holds"]     # T3 is not part of P1
    assert not P({(prim, "tool", "T1", "hw", "exact", "accuracy"): 0.60})["P2"]["holds"] and not P({(prim, "tool", "T3", "hw", "exact", "wrong_confident"): 0.40})["P3"]["holds"]
    assert not P({(prim, "fast_confirm", "T2", "hw", "exact", "minutes"): 40.0})["P4"]["holds"] and not P({(prim, "fast_confirm", "T2", "hw", "exact", "accuracy"): 0.59})["P4"]["holds"]
    assert P({(prim, "fast_confirm", "T2", "hw", "exact", "accuracy"): 0.60})["P4"]["holds"]                                                     # "at least as accurate"
    assert not P({(prim, "tool", "T0", "hw", "exact", "accuracy"): 0.65})["P5"]["holds"]
    assert not P({(prim, "tool", "T3", "hw", "v0", "accuracy"): 0.60})["P6"]["holds"] and P({(prim, "tool", "T0", "hw", "v0", "accuracy"): 0.10})["P6"]["holds"]                  # T0 is not part of P6
    assert not P({(r2, "tool", "T1", "hw", "exact", "accuracy"): 0.80})["P7"]["holds"]
    assert not P({(prim, "tool", "T3", "hw", "exact", "minutes"): 90.0})["P8"]["holds"]
    assert not P({(prim, "tool", "T2", "doc", "exact", "accuracy"): 0.60})["P9"]["holds"]
    an = fake_analyses()
    for a in an:
        a["sum"][("tool", "T1", "doc", "exact")] = dict(n=0, accuracy=0.9, minutes=1.0)
    assert not F.fast_predictions(an)["P9"]["holds"]


# ---------------------------------------------------------------------------------------------- gates
def test_g1_passes_on_the_real_code_and_compares_with_addendum_27s_raw_results(tmp_path, tiny):
    ok, msg = F.gate_g1([tiny], None)
    assert ok and "SKIPPED" in msg and "20 episodes" in msg
    raw = tmp_path / "raw.pkl"
    raw.write_bytes(pickle.dumps([T.run_cell(0, PRIMARY, 10)]))
    ok, msg = F.gate_g1([tiny], raw)
    assert ok and "equal Addendum 27's raw file in all 1 cells" in msg
    ok, msg = F.gate_g1([tiny], tmp_path / "missing.pkl")
    assert ok and "SKIPPED" in msg
    old = T.run_cell(0, PRIMARY, 10)
    old["arm"]["T2"]["minutes"] = old["arm"]["T2"]["minutes"] + 1.0
    raw.write_bytes(pickle.dumps([old]))
    ok, msg = F.gate_g1([tiny], raw)
    assert not ok and "minutes" in msg and "T2" in msg
    old = T.run_cell(0, PRIMARY, 10)
    old["arm"]["T3"]["sequence"][0] = ("power_24vac",)
    raw.write_bytes(pickle.dumps([old]))
    assert not F.gate_g1([tiny], raw)[0]
    raw.write_bytes(pickle.dumps([T.run_cell(1, T.all_cells()[1], 10)]))
    assert not F.gate_g1([tiny], raw)[0]


def test_g1_catches_a_habit_that_is_not_v0s(monkeypatch):
    real = F.run_habit_A

    def drifted(case, ctx, ask):
        r = real(case, ctx, ask)
        r["minutes"] += 1.0
        return r
    monkeypatch.setattr(F, "run_habit_A", drifted)
    ok, msg = F.gate_g1([], None)
    assert not ok and "differs from v0's simulate_habit" in msg


@pytest.fixture(scope="module")
def stress():
    return [F.run_cell(8, T.Cell("R2", "assumed", "full"), 6), F.run_cell(9, T.Cell("R2", "assumed", "half"), 6)]


def test_g2_hand_summed_minutes_and_the_replay(stress, monkeypatch):
    ok, msg = F.gate_g2(stress, 3)
    assert ok and "replay identically" in msg and int(msg.split("; ")[1].split(" ")[0]) > 0
    ok, msg = F.gate_g2(None)
    assert ok and "0 degraded" in msg
    r0 = F.run_cell(0, PRIMARY, 6)
    assert F.gate_g2([r0], 6)[1].split("; ")[1].startswith("0 degraded")                              # as-assumed cells are not replayed
    monkeypatch.setattr(F, "SINGLE_P", 0.9)                                                          # a different checklist changes the hand-summed transcript
    ok, msg = F.gate_g2(None)
    assert not ok and "transcript" in msg


def test_g2_replay_fails_on_a_tampered_trace(stress):
    bad = [dict(r, pol={p: {a: dict(v) for a, v in d.items()} for p, d in r["pol"].items()}) for r in stress]
    a = bad[0]["pol"]["fast_confirm"]["T2"]
    i = int(np.flatnonzero(a["valid"])[0])
    tr = [list(x) for x in a["trace"][i]]
    tr[0][1] = "power_24vac" if tr[0][1] != "power_24vac" else "control_signal"
    a["trace"] = list(a["trace"])
    a["trace"][i] = [tuple(x) for x in tr]
    ok, msg = F.gate_g2(bad, 6)
    assert not ok and "different checks" in msg


def edited(res, pol, arm, i, trace=None, **arrays):
    r = dict(res, pol={p: {a: {k: (list(v) if isinstance(v, list) else v.copy()) for k, v in d.items()} for a, d in dd.items()} for p, dd in res["pol"].items()},
             base=dict(res["base"], **{k: v.copy() for k, v in arrays.items()}))
    if trace is not None:
        r["pol"][pol][arm]["trace"][i] = trace
    return r


def test_g3_availability_and_no_repeats(tiny):
    ok, msg = F.gate_g3([tiny])
    assert ok, msg
    hw = int(np.flatnonzero(T.hw_mask(tiny["base"]))[0])
    assert not F.gate_g3([edited(tiny, "fast_list", "T0", hw, [("C", "bas_airflow", "the box", "normal")])])[0]                   # no control-system access at T0
    assert not F.gate_g3([edited(tiny, "fast_list", "T1", 0, [("C", "design_load", "VAV-0", "normal")])])[0]                        # no design values at T1
    assert not F.gate_g3([edited(tiny, "habit_A", "T3", 0, [("C", "power_24vac", "VAV-0", "normal"), ("C", "power_24vac", "VAV-0", "normal")])])[0]   # twice
    no_gauge = tiny["base"]["instrument"].copy()
    no_gauge[0] = False
    assert not F.gate_g3([edited(tiny, "fast_confirm", "T3", 0, [("C", "static_at_box", "VAV-0", "normal")], instrument=no_gauge)])[0]
    ok_gauge = tiny["base"]["instrument"].copy()
    ok_gauge[0] = True
    assert F.gate_g3([edited(tiny, "fast_confirm", "T3", 0, [("C", "static_at_box", "VAV-0", "normal")], instrument=ok_gauge)])[0]
    room = tiny["base"]["room"].copy()
    room[0] = 0
    assert not F.gate_g3([edited(tiny, "fast_list", "T3", 0, [("C", "reheat_coil", "VAV-0", "normal")], room=room)])[0]                # box 0 has no reheat


def test_g4_reproducibility(tiny):
    ok, msg = F.gate_g4([tiny], 10)
    assert ok, msg
    bad = edited(tiny, "fast_list", "T2", 0)
    bad["pol"]["fast_list"]["T2"]["minutes"][0] += 1.0
    ok, msg = F.gate_g4([bad], 10)
    assert not ok and "fast_list T2" in msg and "minutes" in msg
    bad2 = edited(tiny, "habit_A", "T1", 0)
    bad2["pol"]["habit_A"]["T1"]["trace"][0] = [("C", "no_such_check", "nowhere", "yes")]
    assert not F.gate_g4([bad2], 10)[0]


def test_g5_completeness_and_pairing(tiny):
    good = [dict(tiny, idx=i) for i in range(12)]
    assert F.gate_g5(good)[0] and F.gate_g5([tiny], expected_idx=[0])[0]
    assert not F.gate_g5(good[:11])[0] and not F.gate_g5([tiny], expected_idx=[2])[0]

    def mut(f):
        r = edited(tiny, "habit_A", "T1", 0)
        f(r)
        return F.gate_g5([r], expected_idx=[0])
    assert not mut(lambda r: r["pol"].pop("fast_confirm"))[0]
    assert not mut(lambda r: r["pol"]["fast_list"].pop("T3"))[0]
    assert not mut(lambda r: r["pol"]["fast_list"]["T0"].__setitem__("valid", np.ones(r["n"], bool)))[0]
    assert not mut(lambda r: r["pol"]["fast_list"]["T2"].__setitem__("valid", np.zeros(r["n"], bool)))[0]                              # valid differs from the tool's, nothing else wrong
    assert not mut(lambda r: r["pol"]["fast_list"]["T2"]["minutes"].__setitem__(0, np.nan))[0]
    assert not mut(lambda r: r["pol"]["fast_list"]["T2"].__setitem__("minutes", r["pol"]["fast_list"]["T2"]["minutes"][:-1]))[0]
    assert not mut(lambda r: r["pol"]["fast_confirm"]["T3"]["guess_idx"].__setitem__(0, -1))[0]
    assert not mut(lambda r: r["pol"]["habit_A"]["T2+access"]["minutes"].__setitem__(1, 999.0))[0]
    assert not mut(lambda r: r["pol"]["habit_A"]["T3"]["guess_idx"].__setitem__(1, (r["pol"]["habit_A"]["T3"]["guess_idx"][1] + 1) % 5))[0]


# ---------------------------------------------------------------------------------------------- the script
def test_the_script_runs_on_a_smoke_size_and_regenerates_its_report(tmp_path):
    S72.main(["--smoke", "--out", str(tmp_path), "--workers", "1"])
    for f in ("fast_report.md", "fast_cells.csv", "fast_raw.pkl", "fast_analysis.pkl"):
        assert (tmp_path / f).exists() and (tmp_path / f).stat().st_size > 0
    text = (tmp_path / "fast_report.md").read_text()
    for g in ("G1 code path", "G2 accounting", "G3 availability", "G4 reproducibility", "G5 completeness and pairing"):
        assert g in text
    assert "SMOKE RUN" in text and "ALL MY CONSTRUCTIONS" in text and "## Primary cell" in text and "break-even" in text and "## Predictions" not in text
    rows = (tmp_path / "fast_cells.csv").read_text().splitlines()
    assert rows[0].startswith("cell,rel,mix,cover,policy,arm,subset,level,n,minutes") and len(rows) > 100
    S72.main(["--smoke", "--out", str(tmp_path), "--from-pickle"])
    assert (tmp_path / "fast_report.md").read_text().split("Run time")[0] == text.split("Run time")[0]


def test_the_script_exits_nonzero_and_shows_no_numbers_when_a_gate_fails(tmp_path, monkeypatch):
    real = F.compute_cells
    raw = tmp_path / "addendum27_raw.pkl"
    raw.write_bytes(pickle.dumps([T.run_cell(0, PRIMARY, 6)]))
    monkeypatch.setattr(F, "RAW27", raw)                                                             # a non-smoke run compares the tool with Addendum 27's raw file
    monkeypatch.setattr(F, "compute_cells", lambda cells, n, workers: real(cells[:1], 6, 1))
    with pytest.raises(SystemExit) as e:
        S72.main(["--out", str(tmp_path)])
    assert e.value.code == 1
    text = (tmp_path / "fast_report.md").read_text()
    assert "NO RESULT (a gate failed)" in text and "## Primary cell" not in text and "G5 completeness and pairing | FAIL" in text
    assert "equal Addendum 27's raw file in all 1 cells" in text and "SKIPPED" not in text


def test_report_helpers():
    assert S72.pct(0.256) == "26%" and S72.pct(None) == "n/a" and S72.pct(float("nan")) == "n/a" and S72.num(dict(n=0), "minutes") == "n/a" and S72.num(dict(n=2, minutes=41.6), "minutes") == "42"
    assert S72.num(dict(n=2, x=0.256), "x", "pct") == "26%" and S72.num(dict(n=2, x=3.14), "x", "num") == "3.1"
    assert "tool ahead on both" in S72.wcost(dict(break_even="DOMINATES", wrong_cost=0.0)) and "stand-in ahead on both" in S72.wcost(dict(break_even="DOMINATED", wrong_cost=float("inf")))
    assert "tool wins above" in S72.wcost(dict(break_even="SLOWER-MORE", wrong_cost=120.4)) and "120 min" in S72.wcost(dict(break_even="SLOWER-MORE", wrong_cost=120.4))
    assert "tool wins below" in S72.wcost(dict(break_even="FASTER-LESS", wrong_cost=50.0))
