"""Guards for the one-way switch study (PREREGISTRATION_DR.md Addendum 22): stress worlds and cells, the switch states, the runner, the analysis, expected change and break-even arithmetic, the
decision rule, predictions and gates."""
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("rdflib")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import census as C  # noqa: E402
from docmismatch.troubleshoot import model as M  # noqa: E402
from docmismatch.troubleshoot import realmaps as R  # noqa: E402
from docmismatch.troubleshoot import study as S  # noqa: E402
from docmismatch.troubleshoot import study_switch as SW  # noqa: E402

DATA = ROOT.parent / "data_cache"
HAVE_DATA = (DATA / "mortar__bldg8.ttl").exists()


def fake_layout():
    """AHU-A feeds V1-V3, AHU-B feeds V4-V5, V6 has no handler; Z1..Z6 <- V1..V6."""
    kinds = {f"V{i}": "VAV" for i in range(1, 7)} | {f"Z{i}": "Zone" for i in range(1, 7)} | {"AHU-A": "AHU", "AHU-B": "AHU"}
    vz = [(f"V{i}", f"Z{i}") for i in range(1, 7)]
    av = [("AHU-A", f"V{i}") for i in (1, 2, 3)] + [("AHU-B", "V4"), ("AHU-B", "V5")]
    return R.layout_from_census(C.BrickCensus("b1", kinds, {}, {"vav_zone": vz, "ahu_vav": av, "coil_vav": [], "coil_ahu": []}))[0]


# ---------------------------------------------------------------------------------------------- states, worlds, cells
def test_switch_states_are_the_settings_they_are_defined_as():
    base = M.Settings()
    assert SW.settings_for("off") == base and SW.settings_for("on") == base.with_drawings("mostly_right")
    assert [SW.settings_for(s).p_wrong for s in ("on", "on_mild", "off")] == [0.05, 0.10, 0.15] and SW.STATES == ("off", "on", "on_mild") and SW.BASE == "off"
    for s in ("on", "on_mild"):
        assert SW.settings_for(s) == replace(base, p_wrong=SW.settings_for(s).p_wrong)                                            # only the prior differs
    with pytest.raises(ValueError):
        SW.settings_for("maybe")
    assert SW.POLICIES == ("entropy@off", "entropy@on", "entropy@on_mild", "habit_A", "habit_B")


def test_stress_worlds_change_only_what_they_say():
    assert SW.world_cell("X0", "p15") == S.Cell(0, 0.15, 0.15, 0.25, "assumed", "assumed") and SW.world_cell("X1", "p05") == S.Cell(0, 0.05, 0.30, 0.25, "assumed", "assumed")
    assert SW.world_cell("X2", "p30") == S.Cell(0, 0.30, 0.15, 0.25, "degraded", "assumed") and SW.world_cell("X3", "p30") == S.Cell(0, 0.30, 0.30, 0.25, "degraded", "assumed")
    ok, deg = S.true_settings(SW.world_cell("X0", "p15")), S.true_settings(SW.world_cell("X2", "p15"))
    room = {c.name: c for c in ok.menu("vav_zone")}["override_room"]
    assert {c.name: c for c in deg.menu("vav_zone")}["override_room"] == room                                                      # override_room is not degraded
    t_ok, t_deg = {c.name: c for c in ok.menu("vav_zone")}["duct_trace"], {c.name: c for c in deg.menu("vav_zone")}["duct_trace"]
    assert (t_deg.tpr, t_deg.fpr) == (pytest.approx(t_ok.tpr - 0.15), pytest.approx(t_ok.fpr + 0.10)) and t_deg.access_min == t_ok.access_min
    assert S.true_settings(SW.world_cell("X1", "p15")).p_acts_fail == 0.30 and S.true_settings(SW.world_cell("X3", "p30")).p_wrong == 0.30
    b = fake_layout()
    assert SW.assumed_case(b, "Z1", "R_narrow", "on").settings.p_wrong == 0.05 and SW.assumed_case(b, "Z1", "R_narrow", "on").settings.p_acts_fail == 0.15       # the tool's assumptions never change
    real = SW.real_case(b, "Z1", "X3", "p30", "R_wide")
    assert (real.settings.p_wrong, real.settings.p_acts_fail) == (0.30, 0.30)


def test_cell_order_and_count():
    cells = SW.all_switch_cells(list(R.FROZEN_BUILDINGS))
    assert len(cells) == 600 and cells[0] == SW.SwitchCell("X0", "p05", "R_narrow", "bldg2") and cells[24] == SW.SwitchCell("X0", "p05", "R_narrow", "bldg44")
    assert cells[25] == SW.SwitchCell("X0", "p05", "R_wide", "bldg2") and cells[50] == SW.SwitchCell("X0", "p15", "R_narrow", "bldg2") and cells[150] == SW.SwitchCell("X1", "p05", "R_narrow", "bldg2")
    assert cells[-1] == SW.SwitchCell("X3", "p30", "R_wide", "bldg44") and len({c for c in cells}) == 600


# ---------------------------------------------------------------------------------------------- the runner
def run(condition="X3", world="p30", regime="R_narrow", n=40, idx=5):
    return SW.run_switch_cell(idx, SW.SwitchCell(condition, world, regime, "b1"), fake_layout(), n=n)


def test_runner_shapes_pairing_determinism_and_prefix():
    r = run()
    assert set(r["policy"]) == set(SW.POLICIES) and r["n"] == 40 and len(r["K"]) == 40
    ref = r["policy"][SW.POLICIES[0]]["truth_idx"]
    for name, p in r["policy"].items():
        assert np.array_equal(p["truth_idx"], ref) and np.isfinite(p["minutes"]).all() and (p["correct"] == (p["guess_idx"] == p["truth_idx"])).all()
    again = run()
    assert all(np.array_equal(r["policy"][p][k], again["policy"][p][k]) for p in SW.POLICIES for k in ("minutes", "guess_idx", "checks"))
    small, big = run(n=10), run(n=25)
    assert all(np.array_equal(small["policy"][p][k], big["policy"][p][k][:10]) for p in SW.POLICIES for k in ("minutes", "checks", "guess_idx", "truth_idx", "concluded"))
    assert SW.g5_complete_switch([r], n_cells=1, expected_idx=[5])[0]


def test_the_state_changes_the_tool_and_only_the_tool():
    r = run(condition="X0", world="p30", n=200)
    off, on = r["policy"]["entropy@off"], r["policy"]["entropy@on"]
    assert not (np.array_equal(off["minutes"], on["minutes"]) and np.array_equal(off["guess_idx"], on["guess_idx"]))
    assert np.array_equal(off["truth_idx"], on["truth_idx"]) and SW.gate_habits_independent(fake_layout())[0]


def test_the_states_share_their_random_draws(monkeypatch):
    monkeypatch.setitem(SW.LEVELS, "on_mild", 0.15)                                                                              # on_mild with the default prior...
    r = run(condition="X2", world="p15", n=60)
    a, b = r["policy"]["entropy@on_mild"], r["policy"]["entropy@off"]
    assert all(np.array_equal(a[k], b[k]) for k in ("minutes", "guess_idx", "checks", "concluded"))                              # ...must give identical episodes (common random numbers)
    assert not all(np.array_equal(r["policy"]["entropy@on"][k], b[k]) for k in ("minutes", "guess_idx", "checks"))


def test_the_condition_reaches_the_simulated_technician():
    x0, x3 = run(condition="X0", world="p15", n=300), run(condition="X3", world="p15", n=300)
    acc = lambda r: float(r["policy"]["entropy@off"]["correct"].mean())  # noqa: E731
    assert np.array_equal(x0["policy"]["entropy@off"]["truth_idx"] != -1, x3["policy"]["entropy@off"]["truth_idx"] != -1)
    assert acc(x3) < acc(x0)                                                                                                     # degraded checks and more failing actuators make answers worse


# ---------------------------------------------------------------------------------------------- analysis of one cell
def fake_result(n=300, seed=0, base=100.0, shifts=None):
    """Cell result with five policies set by hand: `shifts[state] = (minutes factor, accuracy)`; the habits and unlisted states use (1.0, 0.9). All policies share the same random numbers, so a
    difference is exactly the shift (paired)."""
    rng = np.random.default_rng(seed)
    shifts = shifts or {}
    truth = rng.integers(0, 4, n)
    u, v = rng.random(n), rng.random(n)
    pol = {}
    for name in SW.POLICIES:
        f, acc = shifts.get(name.split("@")[1] if "@" in name else "", (1.0, 0.9))
        correct = v < acc
        pol[name] = dict(truth_idx=truth, guess_idx=np.where(correct, truth, (truth + 1) % 4), minutes=base * f * (0.9 + 0.2 * u), checks=np.full(n, 3.0), concluded=np.ones(n, bool), correct=correct)
    return dict(idx=3, cell=SW.SwitchCell("X0", "p15", "R_narrow", "b1"), n=n, policy=pol)


def test_analysis_labels_hand_built_differences():
    same = SW.analyze_switch_cell(fake_result(), B=200)
    assert set(same["cmp"]) == {"on", "on_mild"}
    for st in ("on", "on_mild"):
        c = same["cmp"][st]
        assert c["label"] == "NEITHER" and c["d_min"] == 0 and c["d_acc"] == 0 and c["d_wc"] == 0 and c["safety"] == "NONE"
    fast = SW.analyze_switch_cell(fake_result(shifts={"on": (0.7, 0.9)}), B=200)["cmp"]["on"]
    assert fast["label"] == "IMPROVES" and fast["time"] == "FASTER" and fast["r_min"] < -0.25
    trade = SW.analyze_switch_cell(fake_result(shifts={"on": (0.7, 0.75)}), B=300)["cmp"]["on"]
    assert trade["label"] == "TRADE" and trade["acc"] == "LESS" and trade["safety"] == "REGRESSION"                              # faster but less accurate: more confident wrong answers too
    slow = SW.analyze_switch_cell(fake_result(shifts={"on_mild": (1.4, 0.9)}), B=200)["cmp"]["on_mild"]
    assert slow["label"] == "WORSE" and slow["time"] == "SLOWER"
    only_mild = SW.analyze_switch_cell(fake_result(shifts={"on_mild": (0.7, 0.9)}), B=200)["cmp"]
    assert only_mild["on"]["label"] == "NEITHER" and only_mild["on_mild"]["label"] == "IMPROVES"                                 # each state is compared on its own
    base_shift = SW.analyze_switch_cell(fake_result(shifts={"off": (2.0, 0.9)}), B=200)["cmp"]["on"]
    assert base_shift["time"] == "FASTER"                                                                                       # the baseline is `off`


def test_analysis_context_labels_against_the_habits():
    a = SW.analyze_switch_cell(fake_result(), B=100)
    assert set(a["ctx"]) >= {f"{s}|{h}" for s in SW.STATES for h in SW.HABITS} | set(SW.STATES)
    assert all(a["ctx"][s] in ("WINS", "LOSES", "NEITHER") for s in SW.STATES)


# ---------------------------------------------------------------------------------------------- groups, expected change, break-even, decision
def hand_by_world():
    return {"p05": dict(d_min=-3.0, d_acc=-0.001, d_wc=0.002, d_checks=-0.2), "p15": dict(d_min=-2.0, d_acc=-0.003, d_wc=0.006, d_checks=-0.2), "p30": dict(d_min=-4.0, d_acc=-0.008, d_wc=0.013, d_checks=-0.3)}


def test_expected_change_against_a_hand_calculation():
    d = hand_by_world()
    e = SW.expected_change(d, 1.0, 1.0, SW.MIXES["equal"])
    assert np.isclose(e["d_min"], -3.0) and np.isclose(e["d_acc"], -0.004) and np.isclose(e["d_wc"], 0.007)                     # (sum of the three worlds) / 3
    t = SW.expected_change(d, 0.5, 0.25, SW.MIXES["tilted"])
    assert np.isclose(t["d_min"], 0.6 * 0.5 * -3 + 0.3 * 0.25 * -2 + 0.1 * 0.25 * -4) and np.isclose(t["d_min"], -1.15) and np.isclose(t["d_wc"], 0.001375)
    assert all(v == 0 for v in SW.expected_change(d, 0.0, 0.0, SW.MIXES["equal"]).values())                                      # never switched on: no change
    only_right = SW.expected_change(d, 1.0, 0.0, SW.MIXES["tilted"])
    assert np.isclose(only_right["d_min"], -1.8) and np.isclose(only_right["d_wc"], 0.0012)                                       # flipped on only where it is right
    assert SW.MIXES["equal"] == (1 / 3, 1 / 3, 1 / 3) and np.isclose(sum(SW.MIXES["tilted"]), 1.0) and np.isclose(sum(SW.MIXES["equal"]), 1.0)


def test_favourable_budgets_are_exact():
    z = dict(d_min=0.0, d_acc=0.0, d_wc=0.0, d_checks=0.0)
    assert SW.favourable(z) and SW.favourable(dict(z, d_acc=-0.01, d_wc=0.01)) and not SW.favourable(dict(z, d_acc=-0.0101)) and not SW.favourable(dict(z, d_wc=0.0101))
    assert not SW.favourable(dict(z, d_min=0.001)) and SW.favourable(dict(z, d_min=-5.0))


def test_break_even_false_alarm_rate():
    d = hand_by_world()
    assert SW.break_even_f(d, 1.0, SW.MIXES["equal"]) == 1.0 and SW.break_even_f(d, 0.5, SW.MIXES["tilted"]) == 1.0
    d["p30"]["d_wc"] = 0.05                                                                                                       # (0.002 + f x 0.056) / 3 <= 0.01  <=>  f <= 0.5
    assert SW.break_even_f(d, 1.0, SW.MIXES["equal"]) == 0.5
    d["p30"]["d_wc"] = 0.061                                                                                                      # f <= 0.4179
    assert SW.break_even_f(d, 1.0, SW.MIXES["equal"]) == 0.41
    tilted = SW.break_even_f(d, 1.0, SW.MIXES["tilted"])                                                                          # fewer bad buildings in the tilted mix: more false alarms tolerated
    assert tilted > 0.41
    bad = hand_by_world()
    bad["p05"]["d_min"] = 1.0                                                                                                      # not favourable even at f = 0 (the switch is only ever on where it is right)
    assert SW.break_even_f(bad, 1.0, SW.MIXES["equal"]) is None
    late = hand_by_world()
    late["p05"]["d_min"], late["p15"]["d_min"], late["p30"]["d_min"] = 1.0, -10.0, -10.0                                          # favourable only from some f up: the contiguous rule still says None
    assert SW.break_even_f(late, 1.0, SW.MIXES["equal"]) is None
    assert SW.break_even_f(hand_by_world(), 0.0, SW.MIXES["equal"]) == 1.0                                                        # s = 0 and f varying still only helps where the switch is on


def good_readings():
    return {(c, w): ("HELPS BROADLY" if w == "p05" else "HARMLESS") for c in SW.CONDITIONS for w in SW.WORLDS}


def good_fstar(value=1.0):
    return {(c, reg, m, s): value for c in SW.CONDITIONS for reg in SW.REGIMES for m in SW.MIXES for s in SW.S_LEVELS}


def test_decision_rule():
    r, f = good_readings(), good_fstar()
    dec, q, c = SW.decide(r, f)
    assert dec == "WORTH OFFERING" and q and all(c.values())
    assert SW.decide((r | {("X2", "p30"): "HARMFUL"}), f)[0] == "CONDITIONAL ON RELIABLE CHECKS"
    assert SW.decide((r | {("X3", "p15"): "HARMFUL"}), f)[0] == "CONDITIONAL ON RELIABLE CHECKS"
    assert SW.decide((r | {("X1", "p30"): "HARMFUL"}), f)[0] == "NOT WORTH OFFERING"                                          # a failure in X0 or X1 is not conditional
    assert SW.decide((r | {("X0", "p15"): "HARMFUL"}), f)[0] == "NOT WORTH OFFERING"
    assert SW.decide((r | {("X0", "p05"): "DOES NOT HELP"}), f)[0] == "NOT WORTH OFFERING" and SW.decide((r | {("X0", "p05"): "HELPS IN PART"}), f)[0] == "WORTH OFFERING"
    assert SW.decide((r | {("X2", "p30"): "COSTS SOMETHING"}), f)[0] == "WORTH OFFERING"                                      # only HARMFUL fails a condition
    assert SW.decide((r | {("X0", "p15"): "HARMFUL"}), f)[1]                                                                 # Q is about the 5%-wrong group only
    low = (f | {("X3", "R_wide", "tilted", 1.0): 0.49})
    assert SW.decide(r, low)[0] == "CONDITIONAL ON RELIABLE CHECKS" and SW.decide(r, (f | {("X3", "R_wide", "tilted", 1.0): 0.5}))[0] == "WORTH OFFERING"
    assert SW.decide(r, (f | {("X2", "R_narrow", "equal", 1.0): None}))[0] == "CONDITIONAL ON RELIABLE CHECKS"
    assert SW.decide(r, (f | {("X1", "R_narrow", "equal", 0.5): 0.0}))[0] == "WORTH OFFERING"                                # only s = 1.0 counts


def fake_cell(condition, world, regime, building, on, on_mild=None):
    on_mild = on if on_mild is None else on_mild
    d = dict(d_min=0.0, d_acc=0.0, d_wc=0.0, d_checks=0.0, label="NEITHER", safety="NONE")
    return dict(idx=0, cell=SW.SwitchCell(condition, world, regime, building), cmp={"on": d | on, "on_mild": d | on_mild}, summary={SW.tool_name(SW.BASE): dict(minutes=100.0)})


def fake_analyses(spec, buildings=("a", "b", "c", "d")):
    """spec(condition, world, regime, state) -> overrides for the paired results of that state in that group."""
    return [fake_cell(c, w, reg, b, spec(c, w, reg, "on"), spec(c, w, reg, "on_mild")) for c in SW.CONDITIONS for w in SW.WORLDS for reg in SW.REGIMES for b in buildings]


TYPICAL = {"p05": dict(d_min=-3.0, d_acc=-0.001, d_wc=0.002), "p15": dict(d_min=-2.7, d_acc=-0.003, d_wc=0.006), "p30": dict(d_min=-3.3, d_acc=-0.008, d_wc=0.013)}


def good_spec(c, w, reg, state):
    """A world in which the switch is fine when checks are reliable and harmful at 30% wrong when they are not (decision: CONDITIONAL)."""
    d = dict(TYPICAL[w], label="IMPROVES")
    if c in ("X2", "X3") and w == "p30":
        d = dict(d, d_wc=0.04, label="WORSE")
    return {k: (v / 2 if state == "on_mild" and k.startswith("d_") else v) for k, v in d.items()}


def test_group_readings_and_break_even_table_from_cells():
    an = fake_analyses(good_spec)
    r = SW.group_readings(an)
    assert r[("X0", "p05")] == "HELPS BROADLY" and r[("X0", "p30")] == "HARMLESS" and r[("X2", "p30")] == "HARMFUL" and r[("X3", "p30")] == "HARMFUL" and r[("X1", "p15")] == "HARMLESS"
    f = SW.break_even_table(an)
    assert len(f) == 4 * 2 * 2 * 2 and f[("X0", "R_narrow", "equal", 1.0)] == 1.0 and f[("X2", "R_wide", "equal", 1.0)] == 0.60                # (0.002 + f x 0.046) / 3 <= 0.01  <=>  f <= 0.6087
    assert f[("X2", "R_wide", "tilted", 1.0)] > f[("X2", "R_wide", "equal", 1.0)]
    dec, q, c = SW.decide(r, f)
    assert dec == "CONDITIONAL ON RELIABLE CHECKS" and q and c == {"X0": True, "X1": True, "X2": False, "X3": False}
    assert SW.mean_delta(SW.group_cells(an, "X0", "p05", "R_wide"), "on")["d_min"] == -3.0 and SW.mean_delta(SW.group_cells(an, "X0", "p05"), SW.BASE) == {k: 0.0 for k in SW.METRICS}
    assert len(SW.group_cells(an, "X2", "p30")) == 8 and len(SW.group_cells(an, "X2", "p30", "R_narrow")) == 4


def test_predictions_hold_and_fail_one_at_a_time():
    def spec_with(override):
        def spec(c, w, reg, state):
            hit = override.get((c, w, reg, state))
            return hit if hit is not None else good_spec(c, w, reg, state)
        return spec

    pr = SW.switch_predictions(fake_analyses(good_spec))
    assert all(v["holds"] for v in pr.values()) and set(pr) == {"P1", "P2", "P3", "P4", "P5"}
    p1 = SW.switch_predictions(fake_analyses(spec_with({("X0", "p05", "R_wide", "on"): dict(TYPICAL["p05"], d_min=0.5, label="IMPROVES")})))
    assert not p1["P1"]["holds"] and not p1["P3"]["holds"]
    p1b = SW.switch_predictions(fake_analyses(spec_with({("X0", "p05", "R_narrow", "on"): dict(TYPICAL["p05"], d_acc=-0.02, label="IMPROVES")})))
    assert not p1b["P1"]["holds"] and p1b["P3"]["holds"]
    p2 = SW.switch_predictions(fake_analyses(spec_with({("X2", "p30", "R_narrow", "on"): dict(d_min=-3.3, d_acc=-0.008, d_wc=0.01, label="WORSE")})))
    assert not p2["P2"]["holds"]
    p3 = SW.switch_predictions(fake_analyses(spec_with({("X1", "p15", "R_narrow", "on"): dict(TYPICAL["p15"], d_min=0.0, label="IMPROVES")})))
    assert not p3["P3"]["holds"]                                                                                                   # zero is not "lower"
    p4 = SW.switch_predictions(fake_analyses(spec_with({("X1", "p05", "R_wide", "on_mild"): dict(TYPICAL["p05"], d_min=-5.0, label="IMPROVES")})))
    assert not p4["P4"]["holds"] and p4["P1"]["holds"]                                                                             # a bigger saving than `on`
    p4b = SW.switch_predictions(fake_analyses(spec_with({("X3", "p30", "R_narrow", "on_mild"): dict(TYPICAL["p30"], d_wc=0.05, label="WORSE")})))
    assert not p4b["P4"]["holds"]                                                                                                  # a bigger safety cost than `on`
    ok_everywhere = lambda c, w, reg, state: {k: (v / 2 if state == "on_mild" and k.startswith("d_") else v) for k, v in dict(TYPICAL[w], label="IMPROVES").items()}  # noqa: E731
    p5 = SW.switch_predictions(fake_analyses(ok_everywhere))
    assert not p5["P5"]["holds"] and p5["P5"]["values"] == "WORTH OFFERING"


# ---------------------------------------------------------------------------------------------- gates
def test_g1_switch_gate_passes_and_catches_broken_definitions(monkeypatch):
    b = fake_layout()
    assert SW.gate_g1_switch(b)[0]
    with monkeypatch.context() as m:
        m.setitem(SW.LEVELS, "on_mild", 0.20)                                                                                      # a moved secondary level breaks the frozen 0.05 < 0.10 < 0.15
        ok, msg = SW.gate_g1_switch(b)
        assert not ok and "levels" in msg
    with monkeypatch.context() as m:
        m.setitem(M.DRAWINGS, "mostly_right", 0.06)
        ok, msg = SW.gate_g1_switch(b)
        assert not ok and "levels" in msg
    with monkeypatch.context() as m:
        m.setattr(SW, "settings_for", lambda s: replace(M.Settings(), p_wrong=0.16) if s == "off" else M.Settings().with_drawings("mostly_right"))
        assert not SW.gate_g1_switch(b)[0]


def test_habit_independence_gate_catches_a_habit_that_reads_the_prior(monkeypatch):
    original = S.run_habit_B

    def sneaky(case, truth, rng, true_menu):
        out = original(case, truth, rng, true_menu)
        if case.settings.p_wrong < 0.1:
            out["minutes"] += 1.0
        return out

    monkeypatch.setitem(S.RUNNERS, "habit_B", sneaky)
    assert not SW.gate_habits_independent(fake_layout())[0]


def result_stub(condition, world, regime, acc):
    """`acc` is the accuracy of the policy the honesty gate must read in that group (`off` at 15% wrong, `on` at 5% wrong); every other policy gets 0.5."""
    n = 100
    read = {"p15": "entropy@off", "p05": "entropy@on"}.get(world)
    pol = {name: dict(concluded=np.ones(n, bool), correct=np.arange(n) < int((acc if name == read else 0.5) * n), minutes=np.ones(n), truth_idx=np.zeros(n, int), guess_idx=np.zeros(n, int),
                      checks=np.ones(n)) for name in SW.POLICIES}
    return dict(cell=SW.SwitchCell(condition, world, regime, "b"), policy=pol, n=n, idx=0)


def test_honesty_gate_reads_the_right_groups():
    good = [result_stub("X0", w, r, 0.96) for w in ("p05", "p15") for r in SW.REGIMES] + [result_stub("X2", "p15", r, 0.5) for r in SW.REGIMES]                    # stressed groups are ignored
    ok, vals = SW.g3_honesty_switch(good)
    assert ok and len(vals) == 4 and all(np.isclose(v, 0.96) for v in vals.values())
    bad = [result_stub("X0", w, r, 0.96) for w in ("p05", "p15") for r in SW.REGIMES if (w, r) != ("p15", "R_wide")] + [result_stub("X0", "p15", "R_wide", 0.90)]
    assert not SW.g3_honesty_switch(bad)[0] and not SW.g3_honesty_switch([])[0]
    only_missing = [result_stub("X0", "p05", r, 0.96) for r in SW.REGIMES]
    assert not SW.g3_honesty_switch(only_missing)[0]                                                                                # the 15%-wrong groups are missing: nan, not a pass


def test_completeness_gate():
    r = run(n=12, idx=0)
    assert SW.g5_complete_switch([r], n_cells=1)[0] and not SW.g5_complete_switch([r], n_cells=2)[0] and not SW.g5_complete_switch([], n_cells=1)[0]
    broken = run(n=12, idx=0)
    broken["policy"]["habit_A"]["minutes"] = broken["policy"]["habit_A"]["minutes"].copy()
    broken["policy"]["habit_A"]["minutes"][0] = np.nan
    assert not SW.g5_complete_switch([broken], n_cells=1)[0]
    swapped = run(n=12, idx=0)
    swapped["policy"]["entropy@on"]["truth_idx"] = (swapped["policy"]["entropy@on"]["truth_idx"] + 1) % 5
    assert not SW.g5_complete_switch([swapped], n_cells=1)[0]
    missing = run(n=12, idx=0)
    del missing["policy"]["habit_B"]
    assert not SW.g5_complete_switch([missing], n_cells=1)[0]


# ---------------------------------------------------------------------------------------------- real data
@pytest.mark.skipif(not HAVE_DATA, reason="Mortar Brick files not cached")
def test_runs_on_a_real_layout_and_is_paired_and_finite():
    b, _ = R.load_layout(DATA / "mortar__bldg8.ttl", "bldg8")
    res = SW.run_switch_cell(0, SW.SwitchCell("X3", "p30", "R_wide", "bldg8"), b, n=8)
    assert SW.g5_complete_switch([res], n_cells=1)[0] and SW.gate_g1_switch(b)[0] and SW.gate_habits_independent(b)[0]
    a = SW.analyze_switch_cell(res, B=50)
    assert set(a["cmp"]) == {"on", "on_mild"}
