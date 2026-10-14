"""Guards for working model v1 (docmismatch.troubleshoot.v1): the cause tree, the check catalogue, the data tiers and availability, and that v0 is untouched."""
import contextlib
import io
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot import Session as SessionV0, cli as cli_v0, load_building, make_case, model as M  # noqa: E402
from docmismatch.troubleshoot import sim as sim_v0  # noqa: E402
from docmismatch.troubleshoot.v1 import catalogue as K, causes as C, data as D, engine as E, sim1  # noqa: E402

EX0 = ROOT / "examples" / "troubleshoot_example" / "building.json"
EX1 = ROOT / "examples" / "troubleshoot_example" / "building_v1.json"
GOLD = json.loads((Path(__file__).parent / "troubleshoot_v0_golden.json").read_text())


def b1():
    return D.load_building_v1(EX1)


def case1(tier="T1", member="Room-204", **kw):
    return E.make_case_v1(b1(), member, tier, **kw)


# ---------------------------------------------------------------------------------------------- v0 is untouched
def test_v0_demo_output_is_byte_for_byte_what_it_was_before_v1_existed():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cli_v0.main(["--demo"])
    assert buf.getvalue() == GOLD["demo"]


@pytest.mark.parametrize("key,airflow,strategy", [("none", None, "entropy"), ("no", "no", "entropy"), ("yes", "yes", "split_half")])
def test_v0_scripted_sessions_match_the_golden_transcripts(key, airflow, strategy):
    g = GOLD["scripts"][key]
    s = SessionV0(make_case(load_building(EX0), "Room-204", airflow=airflow), strategy)
    for name, target, minutes, gain, p_yes, answer in g["steps"]:
        r = s.recommend()
        assert (r.check.name, r.target) == (name, target)
        assert (round(r.minutes, 6), round(r.gain, 6), round(r.p_yes, 6)) == (minutes, gain, p_yes)
        s.report(answer)
    causes, post = s.posterior()
    assert [[list(c), round(float(p), 6)] for c, p in zip(causes, post)] == g["posterior"]
    assert (s.elapsed, s.entries) == (g["elapsed"], g["entries"])


def test_equal_scores_are_broken_in_favour_of_the_cheaper_check():
    """v1 selects with v0's rule; nothing in v0's own tests pinned the tie-break (found by breaking v0 on purpose)."""
    ck = M.MENUS["vav_zone"][0]
    mk = lambda gain, minutes: M.Option(ck, "T", minutes, np.array([0.0]), gain, 0.5)  # noqa: E731
    slow, cheap = mk(1.0, 10), mk(0.5, 5)                                                # both 0.1 bits per minute
    assert M.select("entropy", [slow, cheap]) is cheap and M.select("entropy", [cheap, slow]) is cheap


def test_importing_v1_does_not_change_v0_defaults():
    assert [(c.name, c.tpr, c.fpr, c.access_min, c.do_min, c.wait_min) for c in M.MENUS["vav_zone"]] == [
        ("override_room", 0.98, 0.03, 6, 2, 30), ("override_diffuser", 0.90, 0.10, 6, 2, 3), ("duct_trace", 0.98, 0.02, 10, 15, 0), ("confirm_acts", 0.95, 0.05, 6, 3, 0)]
    s = M.Settings()
    assert (s.p_wrong, s.p_acts_fail, s.unlisted_share, s.tau, s.min_gain, s.nearness) == (0.15, 0.15, 0.10, 0.95, 1e-6, "area")


def test_the_v0_example_file_still_loads_in_both_and_the_v1_file_still_loads_in_v0():
    assert D.load_building_v1(EX0).attrs == {} and D.load_building_v1(EX0).points == {}
    b = load_building(EX1)                                                          # v0's loader ignores the new keys
    assert b.claims["vav_zone"]["Room-204"] == "VAV-2-04" and len(b.equipment) == 14


# ---------------------------------------------------------------------------------------------- the v0-equivalent tree reproduces v0
@pytest.mark.parametrize("key,airflow,strategy", [("none", None, "entropy"), ("no", "no", "entropy"), ("yes", "yes", "split_half")])
def test_compat_v0_session_reproduces_the_golden_v0_transcripts(key, airflow, strategy):
    g = GOLD["scripts"][key]
    s = E.Session(case1("T1", airflow=airflow, compat_v0=True), strategy)
    for name, target, minutes, gain, p_yes, answer in g["steps"]:
        r = s.recommend()
        assert (r.check.name, r.target) == (name, target)
        assert (round(r.minutes, 6), round(r.gain, 6), round(r.p_yes, 6)) == (minutes, gain, p_yes)
        s.report(answer)
    causes, post = s.posterior()
    assert [[list(c), round(float(p), 6)] for c, p in zip(causes, post)] == g["posterior"]
    assert (s.elapsed, s.entries) == (g["elapsed"], g["entries"])


def test_compat_v0_episodes_equal_v0_episodes_on_the_same_seeds():
    b0 = load_building(EX0)
    for strategy in ("entropy", "split_half"):
        for member in ("Room-204", "Room-201"):
            c0, c1 = make_case(b0, member), case1("T1", member, compat_v0=True)
            causes = M.make_prior("vav_zone", c0.candidates, c0.doc, c0.settings, None, c0.weights)[0]
            for seed, truth in enumerate(causes * 2):
                r0 = sim_v0.simulate(c0, truth, strategy, np.random.default_rng(seed))
                r1 = sim1.simulate_v1(c1, sim1.World(truth), strategy, np.random.default_rng(seed))
                assert (r1["truth"], r1["guess"], r1["n_checks"], r1["concluded"]) == (r0["truth"], r0["guess"], r0["n_checks"], r0["concluded"])
                assert r1["minutes"] == pytest.approx(r0["minutes"]) and r1["entries"] == r0["entries"]


def test_compat_v0_rejects_what_v0_does_not_have():
    with pytest.raises(ValueError):
        case1("T0", compat_v0=True)
    with pytest.raises(ValueError):
        case1("T1", compat_v0=True, feel="too_cold")
    with pytest.raises(ValueError):
        case1("T1", compat_v0=True, context=D.Context(reheat="no"))


# ---------------------------------------------------------------------------------------------- the cause tree
def test_the_tree_covers_every_branch_the_task_started_from():
    groups = {c.group for c in C.CAUSES} | {"documentation"}
    assert groups == set(C.GROUPS)
    assert {"documentation", "box_mechanical", "power_and_signal", "controls", "sensing", "zone_inputs", "upstream", "reheat", "distribution", "capacity", "other"} == groups
    ids = [c.id for c in C.CAUSES]
    assert len(ids) == len(set(ids)) == 14
    for must in ("actuator_fail", "damper_mech", "no_power", "signal_fault", "controller_comms", "controller_config", "flow_sensor", "zone_sensor_setpoint", "ahu_fan_off", "low_static",
                 "reheat_fail", "duct_diffuser", "capacity_design", "other"):
        assert must in ids
    assert all(c.refs or c.id == "other" for c in C.CAUSES)                        # every cause but the residual points at where the guides describe it


def test_leaf_shares_sum_to_one_within_each_v0_lump():
    for lump in (C.OTHER, C.ACTS_FAIL):
        assert sum(c.share for c in C.CAUSES if c.lump == lump) == pytest.approx(1.0)
    assert {c.id for c in C.CAUSES if c.lump == C.ACTS_FAIL} == {"actuator_fail", "damper_mech", "no_power", "signal_fault", "controller_comms"}


def test_v0_tag_collapses_causes():
    assert C.v0_tag(("actuator_fail",)) == (C.ACTS_FAIL,) and C.v0_tag(("low_static",)) == (C.OTHER,)
    assert C.v0_tag(("wrong", "X")) == ("wrong", "X") and C.v0_tag(("unlisted",)) == ("unlisted",) and C.v0_tag((C.OTHER,)) == (C.OTHER,)


@pytest.mark.parametrize("settings,weights", [(M.Settings(), None), (M.Settings(p_wrong=0.3, p_acts_fail=0.1, unlisted_share=0.2), {"A": 1.0, "B": 0.25, "C": 0.05}),
                                              (M.Settings(p_wrong=0.05, p_acts_fail=0.4), {"A": 0.3, "B": 1.0, "C": 1.0})])
def test_the_v1_prior_is_a_refinement_of_v0s_prior(settings, weights):
    cands = ["D", "A", "B", "C"]
    causes, p = C.make_prior_v1(cands, "D", settings, weights=weights)
    lumps = {}
    for c, x in zip(causes, p):
        lumps[C.v0_tag(c)] = lumps.get(C.v0_tag(c), 0.0) + x
    c0, p0 = M.make_prior("vav_zone", cands, "D", settings, weights=weights)
    for c, x in zip(c0, p0):
        assert lumps[c] == pytest.approx(x)
    assert np.isclose(p.sum(), 1.0) and len(causes) == 14 + 3 + 1


def test_removing_a_leaf_hands_its_mass_to_its_lump_mates():
    s = M.Settings()
    _, full = C.make_prior_v1(["D", "A"], "D", s)
    causes, p = C.make_prior_v1(["D", "A"], "D", s, reheat=False, pressure_independent=False)
    assert ("reheat_fail",) not in causes and ("flow_sensor",) not in causes and len(causes) == len(C.CAUSES) - 2 + 2
    other = sum(x for c, x in zip(causes, p) if c[0] in C.BY_ID and C.BY_ID[c[0]].lump == C.OTHER)
    assert other == pytest.approx(1 - s.p_wrong - s.p_acts_fail)                     # the lump keeps v0's mass
    i = causes.index(("zone_sensor_setpoint",))
    assert p[i] > full[[c for c in C.leaf_causes()].index(C.BY_ID["zone_sensor_setpoint"])]
    assert C.leaf_causes(None)[-4].id == "reheat_fail" or ("reheat_fail" in [c.id for c in C.leaf_causes(None)])   # unknown reheat keeps the cause


def test_without_the_claims_there_are_no_documentation_causes_and_the_hardware_odds_do_not_change():
    s = M.Settings()
    c1, p1 = C.make_prior_v1(["D", "A"], "D", s, docs=True)
    c0, p0 = C.make_prior_v1(["D"], "D", s, docs=False)
    assert all(c[0] not in ("wrong", "unlisted") for c in c0) and len(c0) == 14
    leaves1 = np.array([x for c, x in zip(c1, p1) if c[0] in C.BY_ID])
    assert np.allclose(leaves1 / leaves1.sum(), p0)


def test_symptom_multipliers():
    s = M.Settings()
    _, base = C.make_prior_v1(["D", "A"], "D", s)
    causes, no = C.make_prior_v1(["D", "A"], "D", s, airflow="no")
    _, yes = C.make_prior_v1(["D", "A"], "D", s, airflow="yes")
    _, unsure = C.make_prior_v1(["D", "A"], "D", s, airflow="unsure", feel="unsure")
    assert np.allclose(unsure, base)
    for cid in C.AIRFLOW_SET:
        i = causes.index((cid,))
        assert no[i] > base[i] > yes[i]
    i = causes.index(("low_static",))
    assert no[i] < base[i] and yes[i] > base[i]                                     # the rest lose share when no-air causes gain it
    ratio = no[causes.index(("actuator_fail",))] / no[causes.index(("damper_mech",))]
    assert ratio == pytest.approx(base[causes.index(("actuator_fail",))] / base[causes.index(("damper_mech",))])
    _, cold = C.make_prior_v1(["D", "A"], "D", s, feel="too_cold")
    _, hot = C.make_prior_v1(["D", "A"], "D", s, feel="too_hot")
    assert cold[causes.index(("reheat_fail",))] > base[causes.index(("reheat_fail",))] and hot[causes.index(("capacity_design",))] > base[causes.index(("capacity_design",))]
    assert hot[causes.index(("reheat_fail",))] < base[causes.index(("reheat_fail",))] or np.isclose(hot[causes.index(("reheat_fail",))], base[causes.index(("reheat_fail",))], rtol=0.5)


def test_cause_text():
    assert C.cause_text(("no_power",)) == "Actuator has no 24 VAC" and C.cause_text(("wrong", "X")) == "Documented box is wrong" and C.cause_text((C.OTHER,)) == "Box acts; cause elsewhere"
    assert C.cause_text(("unlisted",)) == "Fed by something not on the list" and C.cause_text((C.ACTS_FAIL,)) == "Box does not act when commanded"


# ---------------------------------------------------------------------------------------------- the catalogue
def test_catalogue_is_sound_and_has_the_four_v0_checks_unchanged():
    assert K.validate() == []
    assert len(K.CATALOGUE) == len({c.name for c in K.CATALOGUE}) == 30
    for v0 in M.MENUS["vav_zone"]:
        c = K.BY_NAME[v0.name]
        assert c.v0 is v0 and c.kind == v0.kind and (c.access_min, c.do_min, c.wait_min) == (v0.access_min, v0.do_min, v0.wait_min) and c.doc_only == v0.doc_only
        assert c.text == v0.text.replace("box {t}", "{box}")
    assert tuple(c.name for c in K.v0_menu()) == K.V0_NAMES == ("override_room", "override_diffuser", "duct_trace", "confirm_acts")
    assert "measured in simulation" in K.BY_NAME["override_room"].source and all(c.source == "PLACEHOLDER" for c in K.CATALOGUE if c.is_reading)


def test_validate_catches_a_broken_catalogue():
    from dataclasses import replace
    good = K.BY_NAME["power_24vac"]
    assert K.validate((replace(good, bg=1.2),)) and K.validate((replace(good, detects={"nope": 0.5}),)) and K.validate((replace(good, place="moon"),))
    assert K.validate((replace(good, access_min=0, do_min=0, wait_min=0),)) and K.validate((replace(good, do_min=-1),))
    assert K.validate((replace(K.BY_NAME["confirm_acts"], v0=None),)) and K.validate((replace(good, v0=K.BY_NAME["confirm_acts"].v0),))
    assert K.validate((replace(K.BY_NAME["override_room"], overrides={"nope": 0.5}),))


@pytest.mark.parametrize("name", K.V0_NAMES)
def test_v0_checks_respond_exactly_as_in_v0_wherever_the_cause_is_a_v0_cause(name):
    ck, v0 = K.BY_NAME[name], next(c for c in M.MENUS["vav_zone"] if c.name == name)
    causes = [("doc_other",), ("doc_acts_fail",), ("wrong", "A"), ("wrong", "B"), ("unlisted",)]
    for target in (["D"] if v0.doc_only else ["D", "A", "B"]):
        assert np.array_equal(K.p_pos_row(ck, causes, target, "D"), M.p_yes("vav_zone", v0, target, causes, "D"))


@pytest.mark.parametrize("name", K.V0_NAMES)
def test_refined_causes_behave_like_their_lump_except_where_declared(name):
    ck = K.BY_NAME[name]
    for spec in C.CAUSES:
        lump = (spec.lump,)
        for target in ("D", "A"):
            expect = K.p_pos(ck, lump, target, "D")
            got = K.p_pos(ck, spec.cause, target, "D")
            if target == "D" and spec.id in ck.overrides:
                assert got == ck.overrides[spec.id] != expect
            else:
                assert got == expect
    assert set(K.BY_NAME["duct_trace"].overrides) == set() == set(K.BY_NAME["confirm_acts"].overrides)


def test_overrides_encode_the_physics_they_claim():
    o = K.BY_NAME["override_room"].overrides
    assert o["ahu_fan_off"] < o["low_static"] < o["controller_config"] < 0.98            # no air at all responds least
    assert K.p_pos(K.BY_NAME["override_room"], ("ahu_fan_off",), "D", "D") < 0.05         # a box override cannot make the room respond with the fan off
    assert K.p_pos(K.BY_NAME["override_room"], ("ahu_fan_off",), "A", "D") == 0.03        # on another box the answer is v0's false-alarm rate


def test_every_cause_but_the_residual_is_seen_by_at_least_one_check_and_nothing_sees_a_cause_it_should_not():
    for spec in C.CAUSES:
        if spec.id == "other":
            continue
        assert any(c.detects.get(spec.id, 0) >= 0.5 for c in K.CATALOGUE if c.is_reading), spec.id
    assert K.BY_NAME["manual_damper_test"].detects == {"damper_mech": 0.92}              # a dead actuator turns freely: this is what tells it from a stuck damper
    assert K.p_pos(K.BY_NAME["manual_damper_test"], ("actuator_fail",), "D", "D") == K.BG
    assert K.p_pos(K.BY_NAME["power_24vac"], ("wrong", "A"), "D", "D") == 0.03 and K.p_pos(K.BY_NAME["power_24vac"], ("unlisted",), "D", "D") == 0.03


def test_reading_check_rows_and_words():
    ck = K.BY_NAME["power_24vac"]
    causes = [("no_power",), ("low_static",), ("wrong", "A")]
    assert np.allclose(K.p_pos_row(ck, causes, "D", "D"), [0.92, 0.03, 0.03])
    assert ck.words == ("abnormal", "normal") and K.BY_NAME["confirm_acts"].words == ("yes", "no")
    assert np.all(K.p_pos_row(K.degrade(ck, 1.0), causes, "D", "D") == 0.5)


def test_levels_and_lv():
    assert K.lv(a="strong", b=0.3) == {"a": 0.92, "b": 0.3} and K.LV["strong"] > K.LV["good"] > K.LV["partial"] > K.LV["weak"] > K.BG
    with pytest.raises(KeyError):
        K.lv(a="huge")


def test_degrade_moves_every_probability_toward_one_half_and_keeps_order():
    a = 0.3
    for c in K.CATALOGUE:
        d = K.degrade(c, a)
        assert K.degrade(c, 0.0) == c
        if c.is_reading:
            assert d.bg == pytest.approx(0.5 + (c.bg - 0.5) * 0.7)
            for k, v in c.detects.items():
                assert d.detects[k] == pytest.approx(0.5 + (v - 0.5) * 0.7) and (abs(d.detects[k] - 0.5) < abs(v - 0.5) or v == 0.5)
        else:
            assert d.v0.tpr == pytest.approx(0.5 + (c.v0.tpr - 0.5) * 0.7) and d.v0.fpr == pytest.approx(0.5 + (c.v0.fpr - 0.5) * 0.7) and d.v0.tpr > d.v0.fpr
            assert all(d.overrides[k] == pytest.approx(0.5 + (v - 0.5) * 0.7) for k, v in c.overrides.items())
        assert (d.name, d.access_min, d.do_min, d.wait_min, d.needs) == (c.name, c.access_min, c.do_min, c.wait_min, c.needs)   # only reliability changes
    assert K.degrade_all(K.CATALOGUE, 0.0) == K.CATALOGUE
    with pytest.raises(ValueError):
        K.degrade(K.CATALOGUE[0], 1.5)


def test_minutes_are_access_only_when_elsewhere_plus_fallback():
    ck = K.BY_NAME["power_24vac"]                                                         # 6 + 4 + 0
    assert ck.minutes(None, "D") == 10 and ck.minutes("X", "D") == 10 and ck.minutes("D", "D") == 4 and ck.minutes("X", "D", 3.0) == 13
    assert K.BY_NAME["override_room"].minutes(None, "D") == 38 == K.BY_NAME["override_room"].v0.minutes(None, "D")


def test_reading_spec_bands():
    p = K.BY_NAME["power_24vac"].reading
    assert p.band({}) == (22.0, 26.0)
    assert [p.classify(v, {}) for v in (22.0, 24.0, 26.0, 21.9, 26.1, 0.0)] == ["normal", "normal", "normal", "abnormal", "abnormal", "abnormal"]
    s = K.BY_NAME["control_signal"].reading
    assert s.band({}) == (2.0, np.inf) and s.classify(2.0, {}) == "normal" and s.classify(1.99, {}) == "abnormal" and s.classify(9.0, {}) == "normal"
    k = K.BY_NAME["k_factor"].reading
    assert k.band({"k_factor": 1000}) == (990.0, 1010.0) and k.classify(1009, {"k_factor": 1000}) == "normal" and k.classify(1011, {"k_factor": 1000}) == "abnormal"
    assert k.band({"k_factor": 1000}, expected=2000) == (1980.0, 2020.0)              # the technician's own expected value wins
    assert k.band({}) is None
    with pytest.raises(ValueError):
        k.classify(1000, {})


@pytest.mark.parametrize("d,low", [(None, 0.25), (4, 0.25), (6, 0.25), (8, 0.30), (10, 0.30), (12, 0.35), (14, 0.35), (16, 0.40), (24, 0.40)])
def test_minimum_static_by_inlet_size(d, low):
    assert K.static_min_inwc({} if d is None else {"inlet_diameter_in": d}) == low
    spec = K.BY_NAME["static_at_box"].reading
    attrs = {} if d is None else {"inlet_diameter_in": d}
    assert spec.classify(low, attrs) == "normal" and spec.classify(low - 0.01, attrs) == "abnormal"


def test_reading_spec_describe():
    assert "22 to 26" in K.BY_NAME["power_24vac"].reading.describe({}) and "at least 2" in K.BY_NAME["control_signal"].reading.describe({})
    assert "no expected value" in K.BY_NAME["k_factor"].reading.describe({}) and "normal is 990 to 1010" in K.BY_NAME["k_factor"].reading.describe({"k_factor": 1000})


# ---------------------------------------------------------------------------------------------- data tiers
def test_tiers_are_the_ones_the_task_defines():
    assert D.TIERS["T0"] == frozenset()
    assert D.TIERS["T1"] == {"equipment_list", "claims"}
    assert D.TIERS["T2"] == D.TIERS["T1"] | {"attributes"}
    assert D.TIERS["T3"] == D.TIERS["T2"] | {"bas_access", "point_map"}
    assert D.TIERS["T4"] == D.TIERS["T3"] | {"trends"}
    assert all(D.TIERS[a] < D.TIERS[b] for a, b in zip(["T0", "T1", "T2", "T3"], ["T1", "T2", "T3", "T4"]))
    assert D.tier_items({"equipment_list", "bas_access"}) == {"equipment_list", "bas_access"}
    with pytest.raises(ValueError):
        D.tier_items("T9")
    with pytest.raises(ValueError):
        D.tier_items({"telepathy"})


def test_no_check_uses_trends():
    assert not any(n.item == "trends" for c in K.CATALOGUE for n in c.needs)


def test_v1_building_file_loads_attributes_and_points():
    b = b1()
    assert b.attrs["VAV-2-04"]["k_factor"] == 5350 and "VAV-2-06" not in b.attrs and b.attrs["AHU-2"]["static_setpoint_inwc"] == 1.2
    assert b.point("AHU-2", "fan_status") == "AHU2.SF_STS" and b.point("VAV-2-06", "airflow") is None and b.point("Room-204", "temperature") == "AHU2.V204.ZN_T"
    assert b.label("VAV-2-04") == "2-04" and b.name.startswith("Example office")


def test_bad_building_files_are_refused(tmp_path):
    d = json.loads(EX1.read_text())
    def write(mut):
        x = json.loads(json.dumps(d))
        mut(x)
        p = tmp_path / "b.json"
        p.write_text(json.dumps(x))
        return p
    with pytest.raises(ValueError, match="unknown attribute"):
        D.load_building_v1(write(lambda x: x["equipment"][2]["attributes"].update(colour="red")))
    with pytest.raises(ValueError, match="must be one of"):
        D.load_building_v1(write(lambda x: x["equipment"][2]["attributes"].update(reheat="steam")))
    with pytest.raises(ValueError, match="positive number"):
        D.load_building_v1(write(lambda x: x["equipment"][2]["attributes"].update(k_factor=-5)))
    with pytest.raises(ValueError, match="positive number"):
        D.load_building_v1(write(lambda x: x["equipment"][2]["attributes"].update(k_factor=True)))
    with pytest.raises(ValueError, match="positive number"):
        D.load_building_v1(write(lambda x: x["equipment"][2]["attributes"].update(k_factor=0)))                  # zero is not a K-factor either
    with pytest.raises(ValueError, match="not in the equipment list"):
        D.load_building_v1(write(lambda x: x["control_system"]["points"].update({"VAV-9-99": {"airflow": "X"}})))


def test_context_declares_and_validates():
    c = D.Context()
    d = c.declare("bas_access", "yes")
    assert c.bas_access is None and d.bas_access == "yes" and d.declare("bas_access", "no").bas_access == "no"
    with pytest.raises(KeyError):
        c.declare("shoe_size", "yes")
    with pytest.raises(ValueError):
        c.declare("reheat", "maybe")
    assert set(D.QUESTIONS) == set(D.CONTEXT_KEYS) and set(D.ASK_KEY.values()) == set(D.CONTEXT_KEYS)


def view(tier="T3", ctx=None):
    return D.DataView(D.tier_items(tier), b1() if tier != "T0" else None, ctx or D.Context())


def avail(name, tier, ctx=None, eq="VAV-2-04"):
    return D.availability(K.BY_NAME[name], view(tier, ctx), eq)


def test_a_control_system_read_is_two_minutes_with_a_point_map_ten_without_and_unavailable_without_access():
    ck = K.BY_NAME["bas_airflow"]
    a3 = avail("bas_airflow", "T3")
    assert a3.state == "offered" and a3.extra_min == 0 and ck.minutes(None, "bas", a3.extra_min) == 2
    a3n = avail("bas_airflow", "T3", eq="VAV-2-06")                                        # T3, but this box has no points on file
    assert a3n.state == "fallback" and a3n.extra_min == 8 and ck.minutes(None, "bas", a3n.extra_min) == 10
    a2y = avail("bas_airflow", "T2", D.Context(bas_access="yes"))                           # the technician can get in, there is no point map
    assert a2y.state == "fallback" and ck.minutes(None, "bas", a2y.extra_min) == 10
    a2 = avail("bas_airflow", "T2")
    assert a2.state == "askable" and a2.ask == ("bas_access",)
    assert avail("bas_airflow", "T2", D.Context(bas_access="no")).state == "unavailable"
    assert avail("bas_airflow", "T3", D.Context(bas_access="no")).state == "unavailable"     # a declaration beats the tier
    assert avail("bas_airflow", "T0").state == "askable"


def test_control_system_reads_of_the_air_handler_also_need_to_know_which_handler():
    assert avail("bas_static", "T3", eq="AHU-2").extra_min == 0
    a = D.availability(K.BY_NAME["bas_static"], view("T0", D.Context(bas_access="yes")), None)
    assert a.state == "fallback" and a.extra_min == 8 + 4                                   # no point map, and the claims (which handler) are not on file


def test_walk_there_air_handler_checks_cost_ten_more_without_the_claims():
    assert avail("ahu_visit", "T1", eq="AHU-2").extra_min == 0
    a = D.availability(K.BY_NAME["ahu_visit"], view("T0"), None)
    assert a.state == "fallback" and a.extra_min == 10


def test_a_check_that_needs_design_values_is_unavailable_without_them():
    assert avail("design_load", "T1").state == "unavailable" and avail("design_load", "T0").state == "unavailable"
    assert avail("design_load", "T2").state == "offered"
    assert avail("design_load", "T2", eq="VAV-2-06").state == "unavailable"                 # a T2 building whose file has nothing on that box


def test_attribute_fallbacks():
    assert avail("max_airflow", "T3").extra_min == 0                                       # design airflow on file, point map on file
    a = avail("max_airflow", "T3", eq="VAV-2-06")
    assert a.extra_min == 4 + 8                                                             # no point map (+4), no design value (+8: look it up)
    assert avail("k_factor", "T3").extra_min == 0 and avail("k_factor", "T3", eq="VAV-2-06").extra_min == 4 + 4
    assert avail("static_at_box", "T2", D.Context(instrument="yes")).extra_min == 0
    assert avail("static_at_box", "T1", D.Context(instrument="yes")).extra_min == 2         # inlet size not on file: read it off the box


def test_instrument_and_occupant_are_needed_and_asked_for():
    for name in ("static_at_box", "flow_hood", "flow_vs_gauge"):
        ctx = D.Context(bas_access="yes")
        assert avail(name, "T3", ctx).state == "askable" and "instrument" in avail(name, "T3", ctx).ask
        assert avail(name, "T3", D.Context(instrument="no")).state == "unavailable"
    assert avail("flow_hood", "T3", D.Context(instrument="yes")).state == "offered"
    assert avail("ask_occupant", "T1").ask == ("occupant",) and avail("ask_occupant", "T1", D.Context(occupant="no")).state == "unavailable"
    assert avail("ask_occupant", "T1", D.Context(occupant="yes")).state == "offered"
    assert avail("flow_vs_gauge", "T2").ask == ("bas_access", "instrument")                 # both must be declared, in that order


def test_reheat_checks_follow_the_documented_or_declared_reheat():
    assert avail("reheat_coil", "T2", eq="VAV-2-04").state == "offered"                      # hydronic on file
    assert avail("reheat_coil", "T2", eq="VAV-2-02").state == "unavailable"                  # documented cooling-only
    assert avail("reheat_coil", "T2", D.Context(reheat="yes"), eq="VAV-2-02").state == "offered"          # ... but the technician says it has one
    assert avail("reheat_coil", "T2", D.Context(reheat="no"), eq="VAV-2-04").state == "unavailable"
    assert avail("reheat_coil", "T1").state == "askable" and avail("reheat_coil", "T1").ask == ("reheat",)
    assert avail("reheat_coil", "T1", D.Context(reheat="yes")).state == "offered"
    assert avail("reheat_coil", "T2", eq="VAV-2-06").state == "askable"                      # no attributes for this box: ask


def test_pressure_dependent_boxes_have_no_flow_sensor_checks():
    b = b1()
    b.attrs["VAV-2-04"]["pressure_independent"] = False
    v = D.DataView(D.TIERS["T2"], b, D.Context())
    assert D.availability(K.BY_NAME["sensing_ports"], v, "VAV-2-04").state == "unavailable"
    assert D.availability(K.BY_NAME["sensing_ports"], v, "VAV-2-05").state == "offered"


def test_dataview_have():
    v = view("T2")
    assert v.have("claims") and v.have("attributes") and not v.have("point_map", "VAV-2-04") and not v.have("trends")
    assert v.have("attr:k_factor", "VAV-2-04") and not v.have("attr:k_factor", "VAV-2-06") and not view("T1").have("attr:k_factor", "VAV-2-04")
    assert v.have("bas_access") is None and D.DataView(D.TIERS["T3"], b1(), D.Context()).have("bas_access") is True     # not on the tier, not declared: unknown
    assert D.DataView(D.TIERS["T2"], b1(), D.Context(bas_access="yes")).have("bas_access") is True
    assert D.DataView(D.TIERS["T3"], b1(), D.Context(bas_access="no")).have("bas_access") is False
    with pytest.raises(KeyError):
        v.have("mind_reading")
    assert view("T1").have("feature:pressure_independent", "VAV-2-04") is True
