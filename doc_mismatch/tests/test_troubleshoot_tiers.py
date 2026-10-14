"""Guards for the data-tier study code (docmismatch.troubleshoot.v1.study_tiers, scripts/71; PREREGISTRATION_DR.md Addendum 27). No test here reads a study result: they check code
paths, rules and gates on synthetic arrays and on tiny runs whose numbers are never inspected."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot import study_rating as SG  # noqa: E402
from docmismatch.troubleshoot.v1 import catalogue as K, causes as C, data as D, sim1, study_tiers as T  # noqa: E402

spec = importlib.util.spec_from_file_location("script71", ROOT / "scripts" / "71_troubleshoot_tiers.py")
S71 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S71)

PRIMARY = T.Cell(**T.PRIMARY)


# ---------------------------------------------------------------------------------------------- the grid and the arms
def test_the_grid_has_twelve_cells_in_the_stated_order_and_one_primary():
    cells = T.all_cells()
    assert len(cells) == 12 and cells[0] == PRIMARY and cells[0].is_primary and sum(c.is_primary for c in cells) == 1
    assert [(c.rel, c.mix, c.cover) for c in cells[:3]] == [("R0", "assumed", "full"), ("R0", "assumed", "half"), ("R0", "shifted", "full")]        # last factor fastest
    assert [c.rel for c in cells] == ["R0"] * 4 + ["R1"] * 4 + ["R2"] * 4 and len(set(cells)) == 12
    assert T.REL_A == {"R0": 0.0, "R1": 0.25, "R2": 0.5}


def test_the_arms_are_the_frozen_ones():
    assert T.ARM_NAMES == ("T0", "T1", "T2", "T2+access", "T3")
    assert T.ARMS["T0"] == D.TIERS["T0"] and T.ARMS["T1"] == D.TIERS["T1"] and T.ARMS["T2"] == D.TIERS["T2"] and T.ARMS["T3"] == D.TIERS["T3"]
    assert T.ARMS["T2+access"] == D.TIERS["T2"] | {"bas_access"} and "point_map" not in T.ARMS["T2+access"]
    assert T.PAIRS == (("T1", "T0"), ("T2", "T1"), ("T2+access", "T2"), ("T3", "T2+access"), ("T3", "T2"), ("T3", "T0")) and T.ADJACENT == T.PAIRS[:4]
    assert all(T.ARMS[b] < T.ARMS[a] for a, b in T.PAIRS)                                                     # in every comparison the first arm has strictly more data than the second
    assert all(T.ARMS[T.ARM_NAMES[i]] < T.ARMS[T.ARM_NAMES[i + 1]] for i in range(4))


def test_the_cause_index_covers_every_possible_truth_and_guess():
    assert len(T.ALL_CAUSES) == 14 + T.N_BOXES + 1 == len(T.CAUSE_INDEX)
    assert T.is_hardware(("low_static",)) and not T.is_hardware(("wrong", "VAV-1")) and not T.is_hardware(("unlisted",))
    assert T.group_of(("low_static",)) == "upstream" and T.group_of(("wrong", "VAV-1")) == "documentation" and T.group_of(("unlisted",)) == "documentation"


def test_the_shifted_mix_reverses_the_shares_within_each_lump():
    sh = T.shifted_shares()
    assert set(sh) == set(C.DEFAULT_SHARES)
    for lump in C.LUMPS:
        ids = [c.id for c in C.CAUSES if c.lump == lump]
        assert sum(sh[i] for i in ids) == pytest.approx(1.0) and sorted(sh[i] for i in ids) == sorted(C.DEFAULT_SHARES[i] for i in ids)
    assert sh["actuator_fail"] == C.DEFAULT_SHARES["signal_fault"] and sh["signal_fault"] == C.DEFAULT_SHARES["actuator_fail"]
    assert sh["zone_sensor_setpoint"] == C.DEFAULT_SHARES["ahu_fan_off"] and sh["ahu_fan_off"] == C.DEFAULT_SHARES["zone_sensor_setpoint"]
    s, shares = T.true_world_settings("shifted")
    assert (s.p_wrong, s.p_acts_fail) == (0.05, 0.30) and shares == sh
    s, shares = T.true_world_settings("assumed")
    assert (s.p_wrong, s.p_acts_fail) == (0.15, 0.15) and shares == C.DEFAULT_SHARES
    with pytest.raises(ValueError):
        T.true_world_settings("chaotic")


def test_the_synthetic_building():
    full, half = T.make_building1("full"), T.make_building1("half")
    assert len(full.base.equipment) == 2 + 16 and full.base.claims["vav_zone"]["Room-3"] == "VAV-3" and full.base.claims["ahu_vav"]["VAV-5"] == "AHU-1" and full.base.claims["ahu_vav"]["VAV-2"] == "AHU-0"
    assert set(full.attrs) == {f"VAV-{i}" for i in range(8)} | {"AHU-0", "AHU-1"} and set(half.attrs) == {f"VAV-{i}" for i in range(4)} | {"AHU-0"}
    assert set(full.points) == {f"VAV-{i}" for i in range(8)} | {f"Room-{i}" for i in range(8)} | {"AHU-0", "AHU-1"} and set(half.points) == {f"VAV-{i}" for i in range(4)} | {f"Room-{i}" for i in range(4)} | {"AHU-0"}
    for i in range(8):
        assert (full.attrs[f"VAV-{i}"]["reheat"] != "none") == T.true_reheat(i)                    # the documented attributes are always right
    assert [T.true_reheat(i) for i in range(4)] == [False, True, True, False]
    with pytest.raises(ValueError):
        T.make_building1("some")


def test_the_frozen_constants_are_the_ones_written_down_in_addendum_27():
    assert (T.SEED, T.N_EPISODES, T.BOOT_B, T.MAX_CHECKS, T.N_BOXES) == (27, 500, 1000, 12, 8)
    assert (T.P_INSTRUMENT, T.P_OCCUPANT, T.G3_MIN, T.G3_MIN_N) == (0.7, 0.7, 0.90, 30)
    assert (T.HELPS_SHARE, T.COST_MAX, T.HURTS_SHARE) == (0.75, 0.10, 0.25)
    assert T.PRIMARY == dict(rel="R0", mix="assumed", cover="full") and T.LEVELS == dict(rel=("R0", "R1", "R2"), mix=("assumed", "shifted"), cover=("full", "half"))
    assert (SG.TIME_R, SG.ACC_TOL, SG.SAFE_TOL) == (0.05, 0.02, 0.02)                                          # the labels are Addendum 21's, unmodified


# ---------------------------------------------------------------------------------------------- the draws
def cases(cover="full"):
    return T.make_cases(cover)


def test_the_draws_of_an_episode_do_not_depend_on_n_the_arm_or_the_other_episodes():
    cs = cases()
    a = [T.draw_episode(0, i, "assumed", cs) for i in range(30)]
    b = [T.draw_episode(0, i, "assumed", cs) for i in reversed(range(30))][::-1]
    assert a == b
    assert T.draw_episode(0, 3, "assumed", cs) != T.draw_episode(1, 3, "assumed", cs) or T.draw_episode(0, 4, "assumed", cs) != T.draw_episode(1, 4, "assumed", cs)


def test_the_draw_stream_is_the_frozen_one_and_no_arm_shares_it():
    cs = cases()
    for idx, i in ((0, 0), (5, 17), (11, 250)):
        rng = np.random.default_rng([27, idx, 0, i])
        assert T.draw_episode(idx, i, "assumed", cs)["room"] == int(rng.integers(8))


def test_an_arms_outcome_stream_is_the_frozen_one():
    cell = T.all_cells()[3]
    res = T.run_cell(3, cell, 3)
    cs, tc = T.make_cases(cell.cover), K.degrade_all(K.CATALOGUE, T.REL_A[cell.rel])
    for i in range(3):
        e = T.draw_episode(3, i, cell.mix, cs)
        for ai, arm in enumerate(T.ARM_NAMES):
            if arm == "T0" and not T.is_hardware(e["truth"]):
                continue
            r = sim1.simulate_v1(cs[(arm, e["room"])], T.world_for(e, arm, tc), "entropy", np.random.default_rng([27, 3, 1 + ai, i]), 12)
            assert res["arm"][arm]["minutes"][i] == r["minutes"] and res["arm"][arm]["sequence"][i] == tuple(c for c, _ in r["sequence"])


def test_the_true_causes_are_possible_and_follow_the_true_mix():
    cs = cases()
    for mix, p_doc in (("assumed", 0.15), ("shifted", 0.05)):
        eps = [T.draw_episode(3, i, mix, cs) for i in range(3000)]
        assert all(e["truth"] != ("reheat_fail",) or T.true_reheat(e["room"]) for e in eps)                # no reheat fault on a box without reheat
        assert all(e["truth"][0] != "wrong" or e["truth"][1] != f"VAV-{e['room']}" for e in eps)
        doc = np.mean([not T.is_hardware(e["truth"]) for e in eps])
        assert abs(doc - p_doc) < 0.025
        freq = lambda cid: sum(e["truth"] == (cid,) for e in eps)  # noqa: E731
        if mix == "shifted":
            assert freq("signal_fault") > 2 * freq("actuator_fail") and freq("ahu_fan_off") > freq("zone_sensor_setpoint") * 0 + 30
        else:
            assert freq("actuator_fail") > 2 * freq("signal_fault") and freq("zone_sensor_setpoint") > freq("ahu_fan_off")
    inst = np.mean([T.draw_episode(3, i, "assumed", cs)["instrument"] for i in range(3000)])
    occ = np.mean([T.draw_episode(3, i, "assumed", cs)["occupant"] for i in range(3000)])
    assert abs(inst - T.P_INSTRUMENT) < 0.03 and abs(occ - T.P_OCCUPANT) < 0.03


def test_the_world_of_an_episode_follows_the_arm_and_the_room():
    ep = dict(room=1, truth=("low_static",), instrument=True, occupant=False)
    for arm in T.ARM_NAMES:
        w = T.world_for(ep, arm, None)
        assert w.context == dict(reheat="yes", bas_access="yes" if arm in ("T2+access", "T3") else "no", instrument="yes", occupant="no") and w.truth == ("low_static",)
    assert T.world_for(dict(room=0, truth=("low_static",), instrument=False, occupant=True), "T1", None).context["reheat"] == "no"
    tc = K.degrade_all(K.CATALOGUE, 0.5)
    assert T.world_for(ep, "T1", tc).true_checks is tc


# ---------------------------------------------------------------------------------------------- one cell
@pytest.fixture(scope="module")
def tiny():
    return T.run_cell(0, PRIMARY, 12)


def test_a_cell_has_the_documented_structure(tiny):
    r = tiny
    assert r["n"] == 12 and set(r["arm"]) == set(T.ARM_NAMES) and len(r["truth_idx"]) == len(r["room"]) == 12
    hw = T.hw_mask(r)
    assert np.array_equal(r["arm"]["T0"]["valid"], hw)
    for arm in T.ARM_NAMES[1:]:
        assert r["arm"][arm]["valid"].all()
    for arm, a in r["arm"].items():
        for k, v in a.items():
            assert len(v) == 12, (arm, k)
        assert np.isfinite(a["minutes"][a["valid"]]).all() and (a["guess_idx"][a["valid"]] >= 0).all()
        for seq, trace in zip(a["sequence"], a["trace"]):
            assert tuple(x[1] for x in trace if x[0] == "C") == seq


def test_a_cell_is_reproducible_and_prefix_stable(tiny):
    again = T.run_cell(0, PRIMARY, 12)
    small = T.run_cell(0, PRIMARY, 7)
    same = lambda x, y: np.array_equal(x, y, equal_nan=True) if x.dtype.kind == "f" else np.array_equal(x, y)  # noqa: E731
    for arm in T.ARM_NAMES:
        for k in ("minutes", "correct", "guess_idx", "valid", "concluded"):
            assert same(tiny["arm"][arm][k], again["arm"][arm][k])
            assert same(tiny["arm"][arm][k][:7], small["arm"][arm][k])
        assert tiny["arm"][arm]["sequence"][:7] == small["arm"][arm]["sequence"]
    assert np.array_equal(tiny["truth_idx"][:7], small["truth_idx"]) and np.array_equal(tiny["room"][:7], small["room"])


def test_arms_without_control_system_access_never_read_the_control_system(tiny):
    for arm in ("T0", "T1", "T2"):
        assert not any(c.startswith("bas_") or c in ("flow_vs_gauge", "k_factor", "max_airflow") for seq in tiny["arm"][arm]["sequence"] for c in seq)
    for arm in ("T0", "T1"):
        assert "design_load" not in {c for seq in tiny["arm"][arm]["sequence"] for c in seq}


def test_the_cell_seeds_differ_between_cells():
    a, b = T.run_cell(0, PRIMARY, 10), T.run_cell(1, T.all_cells()[1], 10)
    assert not np.array_equal(a["truth_idx"], b["truth_idx"]) or not np.array_equal(a["room"], b["room"])


def test_worlds_apart_cells_use_the_reliability_they_name():
    r2 = T.run_cell(8, T.Cell("R2", "assumed", "full"), 10)
    assert r2["cell"].rel == "R2" and r2["arm"]["T1"]["minutes"].shape == (10,)


def test_compute_cells_does_not_depend_on_the_number_of_workers():
    jobs = list(enumerate(T.all_cells()))[:2]
    a, b = T.compute_cells(jobs, 6, workers=1), T.compute_cells(jobs, 6, workers=2)
    for x, y in zip(a, b):
        assert x["idx"] == y["idx"] and np.array_equal(x["truth_idx"], y["truth_idx"])
        for arm in T.ARM_NAMES:
            assert np.array_equal(x["arm"][arm]["minutes"], y["arm"][arm]["minutes"], equal_nan=True) and x["arm"][arm]["sequence"] == y["arm"][arm]["sequence"]


# ---------------------------------------------------------------------------------------------- synthetic arrays for the rules
def fake_res(n=60, n_hw=48, seed=0, idx=0, cell=PRIMARY):
    rng = np.random.default_rng(seed)
    truth = np.array([T.CAUSE_INDEX[("actuator_fail",)]] * n_hw + [T.CAUSE_INDEX[("wrong", "VAV-1")]] * (n - n_hw))
    def arm(minutes=50.0, correct=True, concluded=True):
        return dict(valid=np.ones(n, bool), minutes=minutes + rng.normal(0, 1.0, n), checks=np.full(n, 5.0), questions=np.full(n, 1.0), entries=np.full(n, 7.0), concluded=np.full(n, concluded),
                    stalled=np.zeros(n, bool), correct=np.full(n, correct), guess_idx=np.zeros(n, int), group_ok=np.ones(n, bool), sequence=[()] * n, trace=[[]] * n)
    res = dict(idx=idx, cell=cell, n=n, room=np.zeros(n, int), truth_idx=truth, instrument=np.ones(n, bool), occupant=np.ones(n, bool), arm={a: arm() for a in T.ARM_NAMES})
    res["arm"]["T0"]["valid"] = T.hw_mask(res)
    res["arm"]["T0"]["minutes"][~res["arm"]["T0"]["valid"]] = np.nan
    return res


def label(res, rich="T3", poor="T2", B=300):
    a = T.analyze_cell(res, B)
    return a["cmp"][f"{rich}|{poor}" if (rich, poor) in T.PAIRS else "T3|T2"]


def test_labels_follow_addendum_21s_frozen_rules_with_the_richer_arm_as_the_subject():
    r = fake_res()
    assert label(r)["label"] == "NEITHER"                                                                   # identical arms
    r["arm"]["T3"]["minutes"] = r["arm"]["T2"]["minutes"] * 0.7
    c = label(r)
    assert c["label"] == "IMPROVES" and c["time"] == "FASTER" and c["acc"] == "SAME" and c["d_min"] < 0 and c["r_min"] == pytest.approx(-0.3, abs=0.02)
    r["arm"]["T3"]["minutes"] = r["arm"]["T2"]["minutes"] * 1.3
    assert label(r)["label"] == "WORSE" and label(r)["time"] == "SLOWER"
    r["arm"]["T3"]["minutes"] = r["arm"]["T2"]["minutes"] * 0.7
    r["arm"]["T3"]["correct"] = np.zeros(60, bool)
    r["arm"]["T3"]["correct"][:30] = True                                                                  # accuracy 0.5 against 1.0, on hardware episodes at least
    c = label(r)
    assert c["label"] == "TRADE" and c["acc"] == "LESS"
    r["arm"]["T3"]["minutes"] = r["arm"]["T2"]["minutes"] * 1.3
    r["arm"]["T3"]["correct"] = np.ones(60, bool)
    r["arm"]["T2"]["correct"] = np.zeros(60, bool)
    assert label(r)["label"] == "TRADE" and label(r)["acc"] == "MORE"                                          # slower AND more accurate: TRADE


def test_a_slower_but_more_accurate_arm_is_a_trade_and_is_counted_as_such():
    r = fake_res(n=200, n_hw=160)
    r["arm"]["T2"]["correct"] = np.zeros(200, bool)
    r["arm"]["T2"]["correct"][:100] = True
    r["arm"]["T3"]["minutes"] = r["arm"]["T2"]["minutes"] * 1.3
    a = T.analyze_cell(r, 300)
    c = a["cmp"]["T3|T2"]
    assert (c["time"], c["acc"], c["label"]) == ("SLOWER", "MORE", "TRADE") and "secondary" not in c
    sh = T.step_shares([a], ("T3", "T2"))
    assert sh["TRADE"] == 1.0 and sh["SLOWER_MORE"] == 1.0 and sh["FASTER_LESS"] == 0.0 and sh["COST"] == 1.0
    r2 = fake_res(n=200, n_hw=160)
    r2["arm"]["T3"]["minutes"] = r2["arm"]["T2"]["minutes"] * 0.7
    r2["arm"]["T3"]["correct"] = np.zeros(200, bool)
    r2["arm"]["T3"]["correct"][:100] = True
    sh2 = T.step_shares([T.analyze_cell(r2, 300)], ("T3", "T2"))
    assert sh2["TRADE"] == 1.0 and sh2["FASTER_LESS"] == 1.0 and sh2["SLOWER_MORE"] == 0.0


def test_safety_flags_and_the_extra_wrong_and_confident_rate():
    r = fake_res(n=200, n_hw=160)
    r["arm"]["T3"]["correct"] = np.zeros(200, bool)
    r["arm"]["T3"]["correct"][:120] = True                                                                  # 40 of 160 hardware episodes are now wrong and confident
    c = T.analyze_cell(r, 300)["cmp"]["T3|T2"]
    assert c["safety"] == "REGRESSION" and c["d_wc"] > 0.2
    r2 = fake_res(n=200, n_hw=160)
    r2["arm"]["T2"]["correct"] = np.zeros(200, bool)
    assert T.analyze_cell(r2, 300)["cmp"]["T3|T2"]["safety"] == "GAIN"


def test_the_comparison_uses_only_the_hardware_episodes_and_t0_is_never_asked_about_documentation():
    r = fake_res()
    r["arm"]["T3"]["minutes"][~T.hw_mask(r)] = 1e6                                                          # huge numbers on the documentation episodes must not matter
    assert label(r)["d_min"] == pytest.approx(0.0, abs=1.0)
    a = T.analyze_cell(r, 100)
    assert a["n_hw"] == 48 and a["hw"]["T0"]["n"] == 48 and a["doc"]["T0"] == dict(n=0) and a["doc"]["T1"]["n"] == 12


def test_summaries_partition_how_sessions_end():
    r = fake_res()
    a = r["arm"]["T3"]
    a["concluded"][:20] = False
    a["stalled"][:12] = True
    s = T.summarize_arm(r, "T3", T.hw_mask(r))
    assert s["concluded"] + s["stopped"] + s["limit"] == pytest.approx(1.0) and s["stopped"] == pytest.approx(12 / 48) and s["limit"] == pytest.approx(8 / 48) and s["n"] == 48
    r["arm"]["T3"]["concluded"][:] = False
    assert np.isnan(T.summarize_arm(r, "T3", T.hw_mask(r))["acc_concluded"])
    assert T.summarize_arm(r, "T0", ~T.hw_mask(r)) == dict(n=0)
    r["arm"]["T3"]["correct"][:] = True
    r["arm"]["T3"]["concluded"][:] = True
    r["arm"]["T3"]["correct"][:5] = False
    s = T.summarize_arm(r, "T3", T.hw_mask(r))
    assert s["wrong_confident"] == pytest.approx(5 / 48) and s["accuracy"] == pytest.approx(43 / 48) and s["acc_concluded"] == pytest.approx(43 / 48)


def test_step_shares_and_readings_at_their_exact_boundaries():
    def analyses(labels):
        out = []
        for lab in labels:
            out.append(dict(cmp={"T3|T2": dict(label=lab, time="SAME", acc="SAME", safety="NONE")}))
        return out
    sh = T.step_shares(analyses(["IMPROVES"] * 9 + ["NEITHER"] * 3), ("T3", "T2"))
    assert sh["IMPROVES"] == 0.75 and sh["NEITHER"] == 0.25 and sh["COST"] == 0 and T.step_reading(sh) == "HELPS"
    assert T.step_reading(T.step_shares(analyses(["IMPROVES"] * 8 + ["NEITHER"] * 4), ("T3", "T2"))) == "MIXED"
    assert T.step_reading(T.step_shares(analyses(["IMPROVES"] * 10 + ["TRADE"] * 1 + ["NEITHER"] * 1), ("T3", "T2"))) == "HELPS"                                # 1/12 costs <= 10%
    assert T.step_reading(T.step_shares(analyses(["IMPROVES"] * 9 + ["WORSE"] * 2 + ["NEITHER"]), ("T3", "T2"))) == "MIXED"                                   # 2/12 > 10% but <= 25%
    assert T.step_reading(T.step_shares(analyses(["IMPROVES"] * 5 + ["WORSE"] * 3 + ["NEITHER"] * 4), ("T3", "T2"))) == "MIXED"                               # 3/12 = 25% is not more than 25%
    assert T.step_reading(T.step_shares(analyses(["IMPROVES"] * 5 + ["WORSE"] * 2 + ["TRADE"] * 2 + ["NEITHER"] * 3), ("T3", "T2"))) == "HURTS"           # 4/12 > 25%
    assert T.step_shares(analyses([]), ("T3", "T2"))["IMPROVES"] == 0.0


def test_cell_of_finds_exactly_one_cell():
    an = [dict(cell=c) for c in T.all_cells()]
    assert T.cell_of(an, **T.PRIMARY)["cell"] == PRIMARY and T.cell_of(an, rel="R2", mix="shifted", cover="half")["cell"] == T.Cell("R2", "shifted", "half")
    with pytest.raises(ValueError):
        T.cell_of(an, rel="R0")


# ---------------------------------------------------------------------------------------------- predictions
def fake_analyses(over=None):
    """A grid of fake analyses in which every prediction holds; `over` = {(cell factors as a tuple of pairs, arm, field): value} edits to the matching cells."""
    out = []
    base = dict(minutes=50.0, accuracy=0.9, wrong_confident=0.02, n=100)
    for cell in T.all_cells():
        hw = {a: dict(base) for a in T.ARM_NAMES}
        hw["T0"]["minutes"], hw["T1"]["minutes"], hw["T2"]["minutes"], hw["T2+access"]["minutes"], hw["T3"]["minutes"] = 100.0, 104.0, 100.0, 80.0, 60.0
        if cell.rel == "R2":
            for a in T.ARM_NAMES:
                hw[a]["wrong_confident"] = 0.05 + (0.03 if a == "T3" else 0.0)
        if cell.mix == "shifted":
            for a in T.ARM_NAMES:
                hw[a]["accuracy"] = 0.8
        if cell.cover == "half":
            hw["T3"]["minutes"] = 70.0
        out.append(dict(cell=cell, hw=hw, doc={"T1": dict(n=10, accuracy=0.7)}))
    for (key, arm, field), v in (over or {}).items():
        for a in out:
            if all(getattr(a["cell"], k) == val for k, val in key):
                a["hw"][arm][field] = v
    return out


def test_every_prediction_can_hold_and_can_fail_and_reads_the_named_cells():
    p = T.tier_predictions(fake_analyses())
    assert set(p) == {f"P{i}" for i in range(1, 10)} and all(v["holds"] for v in p.values()), {k: v for k, v in p.items() if not v["holds"]}
    P = lambda o: T.tier_predictions(fake_analyses(o))  # noqa: E731
    prim = tuple(sorted(T.PRIMARY.items()))
    assert not P({(prim, "T3", "minutes"): 76.0})["P1"]["holds"] and P({(prim, "T3", "minutes"): 75.0})["P1"]["holds"]
    assert not P({(prim, "T3", "minutes"): 73.0})["P2"]["holds"] and P({(prim, "T3", "minutes"): 72.0})["P2"]["holds"]
    assert P({(prim, "T2", "minutes"): 114.0})["P3"]["holds"] and not P({(prim, "T2", "minutes"): 115.0})["P3"]["holds"]                     # T1 is 104: within 10% is 93.6 to 114.4
    assert P({(prim, "T2", "minutes"): 94.0})["P3"]["holds"] and not P({(prim, "T2", "minutes"): 93.0})["P3"]["holds"]
    assert not P({(prim, "T2", "accuracy"): 0.85})["P3"]["holds"] and P({(prim, "T2", "accuracy"): 0.95})["P3"]["holds"]
    assert not P({(prim, "T1", "minutes"): 99.0})["P4"]["holds"] and P({(prim, "T1", "minutes"): 100.0})["P4"]["holds"]
    r2 = (("rel", "R2"), ("mix", "assumed"), ("cover", "full"))
    assert not P({(r2, "T0", "wrong_confident"): 0.02})["P5"]["holds"]                                         # every arm must get worse, not most
    assert not P({(r2, "T3", "wrong_confident"): 0.04})["P6"]["holds"] and not P({(r2, "T1", "wrong_confident"): 0.09})["P6"]["holds"]
    assert P({(r2, "T3", "wrong_confident"): 0.05})["P6"]["holds"]                                                # equal increases: "at least as large" holds
    half = (("rel", "R0"), ("mix", "assumed"), ("cover", "half"))
    assert not P({(half, "T3", "minutes"): 60.0})["P7"]["holds"]                                                # the gap must be strictly smaller at half coverage: 20 vs 20
    sh = (("rel", "R0"), ("mix", "shifted"), ("cover", "full"))
    assert not P({(sh, "T2", "accuracy"): 0.9})["P8"]["holds"]
    an = fake_analyses()
    for a in an:
        a["doc"] = {"T1": dict(n=0)}
    assert not T.tier_predictions(an)["P9"]["holds"]
    for a in an:
        a["doc"] = {"T1": dict(n=10, accuracy=0.49)}
    assert not T.tier_predictions(an)["P9"]["holds"]


# ---------------------------------------------------------------------------------------------- gates
@pytest.fixture(scope="module")
def stress():
    return [T.run_cell(8, T.Cell("R2", "assumed", "full"), 8), T.run_cell(9, T.Cell("R2", "assumed", "half"), 8)]


def test_g1_passes_on_the_real_code_path_and_fails_if_either_half_drifts(monkeypatch):
    ok, msg = T.gate_g1(6)
    assert ok, msg
    real_cell = T.run_cell
    def drifted(idx, cell, n=T.N_EPISODES):
        r = real_cell(idx, cell, n)
        r["arm"]["T1"]["minutes"] = r["arm"]["T1"]["minutes"] + 1.0                                          # the runner adds an accounting of its own
        return r
    monkeypatch.setattr(T, "run_cell", drifted)
    ok, msg = T.gate_g1(4)
    assert not ok and "differs from a direct" in msg
    monkeypatch.setattr(T, "run_cell", real_cell)
    real_sim = T.sim.simulate
    monkeypatch.setattr(T.sim, "simulate", lambda *a, **k: {**real_sim(*a, **k), "n_checks": real_sim(*a, **k)["n_checks"] + 1})
    ok, msg = T.gate_g1(4)
    assert not ok and "v0-equivalent tree differ" in msg


def test_g2_hand_summed_minutes_and_the_replay_from_answers_alone(stress):
    ok, msg = T.gate_g2(stress, 4)
    assert ok and "replay identically" in msg
    n_checked = int(msg.split("; ")[1].split(" ")[0])
    assert n_checked > 0
    bad = [dict(r, arm={a: dict(v) for a, v in r["arm"].items()}) for r in stress]
    for r in bad:
        a = r["arm"]["T3"]
        i = int(np.flatnonzero(a["valid"])[0])
        tr = [list(x) for x in a["trace"][i]]
        j = next(k for k, x in enumerate(tr) if x[0] == "C")
        tr[j][1] = "power_24vac" if tr[j][1] != "power_24vac" else "control_signal"
        a["trace"] = list(a["trace"])
        a["trace"][i] = [tuple(x) for x in tr]
    ok, msg = T.gate_g2(bad, 4)
    assert not ok and "different checks" in msg
    assert T.gate_g2(None)[0] and "0 degraded" in T.gate_g2(None)[1]                                           # part (a) alone, when there are no results to replay


def test_replay_needs_only_the_answers():
    case = T.make_cases("full")[("T3", 0)]
    w = sim1.World(("low_static",), dict(reheat="no", bas_access="yes", instrument="yes", occupant="yes"))
    r = sim1.simulate_v1(case, w, rng=np.random.default_rng(1))
    assert sim1.replay(case, r["trace"])
    first = next(i for i, x in enumerate(r["trace"]) if x[0] == "C")
    other = "power_24vac" if r["trace"][first][1] != "power_24vac" else "control_signal"
    tampered = list(r["trace"])
    tampered[first] = ("C", other, r["trace"][first][2], r["trace"][first][3])
    assert not sim1.replay(case, tampered)                                                                    # a different check than the tool would have recommended
    assert not sim1.replay(case, [("Q", "occupant", "yes")] + r["trace"])                                     # a question the tool would not have asked
    assert sim1.replay(case, [])


def synthetic_g3(n_conc=40, acc=1.0, cover=("full", "half"), rel="R0", mix="assumed"):
    out = []
    for i, cv in enumerate(cover):
        r = fake_res(n=200, n_hw=200, idx=i, cell=T.Cell(rel, mix, cv))
        for arm in T.ARM_NAMES:
            a = r["arm"][arm]
            a["concluded"] = np.arange(200) < n_conc
            a["correct"] = np.arange(200) < int(round(acc * n_conc))
        out.append(r)
    return out


def test_g3_honesty_gate_thresholds():
    assert T.gate_g3(synthetic_g3())[0]
    assert T.gate_g3(synthetic_g3(acc=0.9))[0] and not T.gate_g3(synthetic_g3(acc=0.87))[0]
    assert T.gate_g3(synthetic_g3(n_conc=30))[0] and not T.gate_g3(synthetic_g3(n_conc=29))[0]                  # too few conclusions to say anything: fails
    _, vals = T.gate_g3(synthetic_g3())
    assert set(vals) == {(c, a) for c in ("full", "half") for a in T.ARM_NAMES}
    assert not T.gate_g3(synthetic_g3(rel="R1"))[0]                                                              # only R0 / assumed cells count: none present -> no evidence
    assert not T.gate_g3(synthetic_g3(mix="shifted"))[0]
    r = synthetic_g3()
    r[0]["arm"]["T2"]["concluded"][:] = False
    assert not T.gate_g3(r)[0]


def test_g4_reproducibility(tiny):
    ok, msg = T.gate_g4([tiny], 8)
    assert ok, msg
    bad = dict(tiny, arm={a: {k: (list(v) if isinstance(v, list) else v.copy()) for k, v in d.items()} for a, d in tiny["arm"].items()})
    bad["arm"]["T2"]["minutes"][0] += 1.0
    ok, msg = T.gate_g4([bad], 8)
    assert not ok and "T2" in msg and "minutes" in msg
    bad2 = dict(tiny, arm={a: {k: (list(v) if isinstance(v, list) else v.copy()) for k, v in d.items()} for a, d in tiny["arm"].items()})
    bad2["arm"]["T3"]["sequence"][1] = ("power_24vac",)
    assert not T.gate_g4([bad2], 8)[0]


def test_g5_completeness_and_pairing(tiny):
    good = [dict(tiny, idx=i) for i in range(12)]
    assert T.gate_g5(good)[0]
    assert not T.gate_g5(good[:11])[0] and not T.gate_g5(good + [dict(tiny, idx=12)])[0]
    ok, msg = T.gate_g5([tiny], expected_idx=[0])
    assert ok, msg
    assert not T.gate_g5([tiny], expected_idx=[3])[0]
    def mut(f):
        r = dict(tiny, arm={a: {k: (list(v) if isinstance(v, list) else v.copy()) for k, v in d.items()} for a, d in tiny["arm"].items()})
        f(r)
        return T.gate_g5([r], expected_idx=[0])
    assert not mut(lambda r: r["arm"].pop("T3"))[0]
    assert not mut(lambda r: r["arm"]["T0"].__setitem__("valid", np.ones(r["n"], bool)))[0]                      # T0 must be valid exactly on the hardware episodes
    assert not mut(lambda r: r["arm"]["T1"].__setitem__("valid", np.zeros(r["n"], bool)))[0]
    assert not mut(lambda r: r["arm"]["T2"]["minutes"].__setitem__(0, np.nan))[0]
    assert not mut(lambda r: r["arm"]["T3"]["guess_idx"].__setitem__(0, -1))[0]
    assert not mut(lambda r: r["arm"]["T3"].__setitem__("minutes", r["arm"]["T3"]["minutes"][:-1]))[0]


def test_g6_availability_passes_on_real_sequences_and_catches_an_impossible_check(tiny):
    ok, msg = T.gate_g6([tiny])
    assert ok, msg
    def edited(arm=None, i=None, seq=None, **arrays):
        r = dict(tiny, arm={a: {k: (list(v) if isinstance(v, list) else v.copy()) for k, v in d.items()} for a, d in tiny["arm"].items()}, **{k: v.copy() for k, v in arrays.items()})
        if arm is not None:
            r["arm"][arm]["sequence"][i] = seq
        return r
    hw = int(np.flatnonzero(T.hw_mask(tiny))[0])
    assert not T.gate_g6([edited("T0", hw, ("bas_airflow",))])[0]                                                 # no control-system access at T0
    assert not T.gate_g6([edited("T2", 0, ("bas_static",))])[0]                                                   # ... nor at T2
    assert not T.gate_g6([edited("T1", 0, ("design_load",))])[0]                                                  # no design values at T1
    no_gauge = tiny["instrument"].copy()
    no_gauge[0] = False
    assert not T.gate_g6([edited("T3", 0, ("static_at_box",), instrument=no_gauge)])[0]                            # a gauge check needs a gauge
    assert T.gate_g6([edited("T3", 0, ("static_at_box",), instrument=np.where(np.arange(tiny["n"]) == 0, True, tiny["instrument"]))])[0]
    no_reheat_room = tiny["room"].copy()
    no_reheat_room[0] = 0                                                                                          # box 0 has no reheat
    assert not T.gate_g6([edited("T3", 0, ("reheat_coil",), room=no_reheat_room)])[0]
    with_reheat_room = tiny["room"].copy()
    with_reheat_room[0] = 1
    assert T.gate_g6([edited("T3", 0, ("reheat_coil",), room=with_reheat_room)])[0]
    no_occ = tiny["occupant"].copy()
    no_occ[0] = False
    assert not T.gate_g6([edited("T1", 0, ("ask_occupant",), occupant=no_occ)])[0]
    assert T.gate_g6([edited("T3", 0, ("power_24vac", "control_signal"))])[0]                                      # physical checks are available anywhere


# ---------------------------------------------------------------------------------------------- the script
def test_the_script_runs_end_to_end_on_a_smoke_size_and_writes_what_it_says(tmp_path):
    S71.main(["--smoke", "--out", str(tmp_path), "--workers", "1"])
    for f in ("tiers_report.md", "tiers_cells.csv", "tiers_raw.pkl", "tiers_analysis.pkl"):
        assert (tmp_path / f).exists() and (tmp_path / f).stat().st_size > 0
    text = (tmp_path / "tiers_report.md").read_text()
    for g in ("G1 code path", "G2 accounting", "G3 honesty", "G4 reproducibility", "G5 completeness and pairing", "G6 availability"):
        assert g in text
    assert "SMOKE RUN" in text and "## The primary cell" in text and "## Each step up" in text and "## Predictions" not in text                # predictions need all 12 cells
    rows = (tmp_path / "tiers_cells.csv").read_text().splitlines()
    assert rows[0].startswith("cell,rel,mix,cover,subset,arm,n,minutes") and len(rows) == 1 + 2 * 2 * len(T.ARM_NAMES)
    S71.main(["--smoke", "--out", str(tmp_path), "--from-pickle"])
    assert (tmp_path / "tiers_report.md").read_text().split("Run time")[0] == text.split("Run time")[0]


def test_the_report_refuses_to_show_numbers_when_an_enforced_gate_fails(tmp_path):
    res = T.compute_cells(list(enumerate(T.all_cells()))[:1], 6, workers=1)
    an = [T.analyze_cell(r, 50) for r in res]
    gates = {"G1 code path": (True, "x"), "G3 honesty": (False, "y")}
    txt = S71.report(res, an, gates, True, 6, 1.0)
    assert "NO RESULT (a gate failed)" in txt and "## The primary cell" not in txt
    assert "## The primary cell" in S71.report(res, an, gates, False, 6, 1.0) and "SMOKE RUN" in S71.report(res, an, gates, False, 6, 1.0)
    assert S71.pct(0.256) == "26%" and S71.pct(None) == "n/a" and S71.pct(float("nan")) == "n/a" and S71.fmt(dict(n=0), "minutes") == "n/a" and S71.fmt(dict(n=3, minutes=41.6), "minutes") == "42"


def test_the_bootstrap_uses_the_frozen_seed():
    r = fake_res(idx=4, cell=T.all_cells()[4])
    r["arm"]["T3"]["minutes"] = r["arm"]["T2"]["minutes"] * 0.7
    a = T.analyze_cell(r, 200)
    idx_hw = np.flatnonzero(T.hw_mask(r))
    boot = np.random.default_rng([27, 4, 99]).integers(0, len(idx_hw), (200, len(idx_hw)))
    d = r["arm"]["T3"]["minutes"][idx_hw] - r["arm"]["T2"]["minutes"][idx_hw]
    assert a["cmp"]["T3|T2"]["ci_min"] == T.S.paired_ci(d, boot)


def test_the_branch_accuracy_is_recomputed_from_the_guess_and_the_truth(tiny):
    for arm in T.ARM_NAMES:
        a = tiny["arm"][arm]
        for i in np.flatnonzero(a["valid"]):
            want = T.group_of(T.ALL_CAUSES[a["guess_idx"][i]]) == T.group_of(T.ALL_CAUSES[tiny["truth_idx"][i]])
            assert bool(a["group_ok"][i]) == want
            assert bool(a["correct"][i]) == (a["guess_idx"][i] == tiny["truth_idx"][i])
            assert a["group_ok"][i] or not a["correct"][i]                                                  # an exact answer is in the right branch


def test_g2_replay_looks_only_at_the_degraded_cells(tiny):
    bad = dict(tiny, arm={a: {k: (list(v) if isinstance(v, list) else v.copy()) for k, v in d.items()} for a, d in tiny["arm"].items()})
    i = int(np.flatnonzero(bad["arm"]["T3"]["valid"])[0])
    tr = [list(x) for x in bad["arm"]["T3"]["trace"][i]]
    j = next(k for k, x in enumerate(tr) if x[0] == "C")
    tr[j][1] = "power_24vac" if tr[j][1] != "power_24vac" else "control_signal"
    bad["arm"]["T3"]["trace"][i] = [tuple(x) for x in tr]
    ok, msg = T.gate_g2([bad], 4)                                                                       # tiny is an R0 cell: not replayed (registered: R1 and R2 only)
    assert ok and "0 degraded" in msg


def test_the_script_exits_nonzero_and_shows_no_numbers_when_a_gate_fails(tmp_path, monkeypatch):
    real = T.compute_cells
    monkeypatch.setattr(T, "compute_cells", lambda cells, n, workers: real(cells[:1], 6, 1))            # one cell only: G5 (completeness) must fail
    with pytest.raises(SystemExit) as e:
        S71.main(["--out", str(tmp_path)])
    assert e.value.code == 1
    text = (tmp_path / "tiers_report.md").read_text()
    assert "NO RESULT (a gate failed)" in text and "## The primary cell" not in text and "G5 completeness and pairing | FAIL" in text
