"""Addendum 43: the decision-tree machine (`troubleshoot/v2/tree.py`) and the study around it (`troubleshoot/v2/study_tree.py`). Plumbing and accounting, not results."""

from __future__ import annotations

import copy

import numpy as np
import pytest

from docmismatch.troubleshoot.v1 import catalogue as K
from docmismatch.troubleshoot.v2 import study_tree as ST
from docmismatch.troubleshoot.v2 import tree as TR
from docmismatch.troubleshoot.v2 import world2 as W
from docmismatch.troubleshoot.v2.study_llm import TableOracle

BLD = W.make_building2()
TIER = ST.PRIMARY_TIER


def cases(tier=TIER, rooms=(1,)):
    cb = ST.cases_for(tier, ST.TAU, ST.MIN_RATE, "mostly_right", BLD)
    return [cb[r] for r in rooms], [W.context_dict(tier, r) for r in rooms]


class Scripted:
    """Answers by a dict {check name: positive?}; anything not listed is negative. `ahu_calls` counts air-handler questions."""

    def __init__(self, pos=(), feeder=None):
        self.pos, self.feeder, self.ahu_calls = set(pos), feeder, 0

    def ask_room(self, i, ck, tgt):
        if ck.kind == "act_observe":
            return "yes" if (self.feeder is not None and tgt == self.feeder) else "no"
        return ck.words[0] if ck.name in self.pos else ck.words[1]

    def ask_ahu(self, a, ck):
        self.ahu_calls += 1
        return ck.words[0] if ck.name in self.pos else ck.words[1]


def chk(names, pos, neg, target="box", **kw):
    return {"op": "check", "check": list(names), "target": target, "pos": pos, "neg": neg, **kw}


CON = lambda c, sure=True: {"op": "conclude", "cause": c, "sure": sure}  # noqa: E731
DONE = {"op": "done"}


# ---------------------------------------------------------------------------------------------- validation
def test_tree_E_is_valid_in_both_forms():
    for dec in (False, True):
        assert TR.validate(TR.tree_E(dec)) == []


@pytest.mark.parametrize("bad", [
    chk(["no_such_check"], CON("low_static"), CON("other")),
    chk(["bas_airflow"], CON("low_static"), None),
    chk(["bas_static"], CON("low_static"), CON("other"), target="box"),                 # an air-handler check aimed at the box
    chk(["bas_airflow"], CON("low_static"), CON("other"), target="ahu"),                # a box check aimed at the air handler
    chk(["bas_airflow"], CON("not_a_cause"), CON("other")),
    chk(["bas_airflow"], {"op": "conclude", "cause": "other", "sure": "yes"}, CON("other")),
    chk(["bas_airflow"], DONE, CON("other")),                                           # `done` outside the preamble
    chk(["bas_airflow"], CON("low_static"), CON("other"), memo_only=True),              # memo_only on a box check
    {"op": "escalate", "guess": "nonsense"},
])
def test_validate_rejects_broken_roots(bad):
    assert TR.validate({"name": "x", "preamble": None, "root": bad})


def test_validate_rejects_a_preamble_that_does_something_else():
    ok = {"name": "x", "root": CON("other"), "preamble": chk(["bas_static"], DONE, DONE, target="ahu")}
    assert TR.validate(ok) == []
    assert TR.validate({**ok, "preamble": chk(["bas_airflow"], DONE, DONE)})
    assert TR.validate({**ok, "preamble": chk(["bas_static"], CON("other"), DONE, target="ahu")})


# ---------------------------------------------------------------------------------------------- the machine
def run(tree, rooms=(1,), tier=TIER, oracle=None):
    cs, ctx = cases(tier, rooms)
    return TR.run_tree({"name": "t", "preamble": None, **tree}, cs, oracle or Scripted(), ctx)


def test_minutes_follow_the_tools_accounting():
    # bas_airflow 2 (at the console), bas_zone 2 (still there), then thermostat: 5 to get to the room + 6.
    t = {"root": chk(["bas_airflow"], CON("other"), chk(["bas_zone"], CON("zone_sensor_setpoint"), chk(["thermostat"], CON("zone_sensor_setpoint"), CON("other"))))}
    r = run(t)
    assert r["minutes"] == pytest.approx(2 + 2 + 5 + 6)
    assert r["n_checks"] == 3 and r["guess"] == [("other",)] and r["concluded"] == [True]


def test_a_check_not_possible_in_the_tier_follows_na_and_defaults_to_neg():
    t = {"root": chk(["bas_airflow"], CON("low_static"), CON("other"), na=CON("zone_sensor_setpoint"))}
    assert run(t, tier="T2")["guess"] == [("zone_sensor_setpoint",)]
    t2 = {"root": chk(["bas_airflow"], CON("low_static"), CON("other"))}
    assert run(t2, tier="T2")["guess"] == [("other",)] and run(t2, tier="T2")["minutes"] == 0.0


def test_first_available_alternative_is_used():
    t = {"root": chk(["bas_static", "ahu_gauge"], CON("low_static"), CON("other"), target="ahu")}
    r_bas, r_phys = run(t, oracle=Scripted(["bas_static"])), run(t, tier="T2", oracle=Scripted(["ahu_gauge"]))
    assert r_bas["trace"][0][1] == "bas_static" and r_bas["minutes"] == 2 and r_bas["guess"] == [("low_static",)]
    assert r_phys["trace"][0][1] == "ahu_gauge" and r_phys["minutes"] == 17 and r_phys["guess"] == [("low_static",)]


def test_air_handler_readings_are_shared_and_family_equivalent():
    pre = chk(["bas_static"], DONE, DONE, target="ahu")
    root = chk(["ahu_gauge", "bas_static"], CON("low_static"), CON("other"), target="ahu")
    o = Scripted(["bas_static", "ahu_gauge"])
    cs, ctx = cases(rooms=(0, 1, 2))                                   # all on AHU-0
    r = TR.run_tree({"name": "t", "preamble": pre, "root": root}, cs, o, ctx)
    assert o.ahu_calls == 1 and r["n_checks"] == 1 and r["guess"] == [("low_static",)] * 3         # read once, in the preamble; ahu_gauge counts as the same quantity
    cs2, ctx2 = cases(rooms=(0, 8))                                    # two complaints, two different air handlers: no preamble, each reads its own
    o2 = Scripted(["bas_static"])
    r2 = TR.run_tree({"name": "t", "preamble": pre, "root": root}, cs2, o2, ctx2)
    assert r2["n_checks"] == 2 and o2.ahu_calls == 2


def test_the_preamble_only_runs_for_air_handlers_with_two_complaints():
    pre = chk(["bas_static"], DONE, DONE, target="ahu")
    t = {"name": "t", "preamble": pre, "root": CON("other")}
    for rooms, n in (((1,), 0), ((1, 2), 1), ((1, 9), 0), ((1, 2, 9, 10), 2)):
        cs, ctx = cases(rooms=rooms)
        assert TR.run_tree(t, cs, Scripted(), ctx)["n_checks"] == n


def test_memo_only_never_does_the_check():
    root = chk(["bas_static"], CON("low_static"), CON("other"), target="ahu", memo_only=True, na=CON("capacity_design"))
    assert run({"root": root})["guess"] == [("capacity_design",)] and run({"root": root})["n_checks"] == 0
    pre = chk(["bas_static"], DONE, DONE, target="ahu")
    cs, ctx = cases(rooms=(1, 2))
    r = TR.run_tree({"name": "t", "preamble": pre, "root": root}, cs, Scripted(["bas_static"]), ctx)
    assert r["guess"] == [("low_static",)] * 2 and r["n_checks"] == 1


def test_a_box_check_is_not_repeated_within_a_complaint():
    t = {"root": chk(["bas_airflow"], chk(["bas_airflow"], CON("low_static"), CON("other")), CON("zone_sensor_setpoint"))}
    r = run(t, oracle=Scripted(["bas_airflow"]))
    assert r["n_checks"] == 1 and r["guess"] == [("low_static",)]


def test_the_check_limit_ends_the_complaint_undeclared(monkeypatch):
    monkeypatch.setattr(TR, "MAX_CHECKS_PER_COMPLAINT", 3)
    names = ["bas_airflow", "bas_zone", "bas_damper", "bas_controller", "thermostat", "flow_hood"]
    node = CON("capacity_design")
    for nm in reversed(names):
        node = chk([nm], node, node)
    r = run({"root": node})
    assert r["n_checks"] == 3 and r["guess"] == [("other",)] and r["concluded"] == [False]
    monkeypatch.setattr(TR, "MAX_CHECKS_PER_COMPLAINT", 12)
    assert run({"root": node})["guess"] == [("capacity_design",)]


def test_escalate_and_unsure_conclusions_are_not_declared():
    assert run({"root": {"op": "escalate", "guess": "flow_sensor"}})["concluded"] == [False]
    assert run({"root": CON("flow_sensor", False)})["concluded"] == [False]
    assert run({"root": CON("flow_sensor", True)})["concluded"] == [True]


def test_find_feeder_names_the_real_box_or_says_unlisted():
    cs, ctx = cases(rooms=(1,))
    cand = [c for c in cs[0].candidates if c != cs[0].doc][1]
    r = TR.run_tree({"name": "t", "preamble": None, "root": {"op": "find_feeder"}}, cs, Scripted(feeder=cand), ctx)
    assert r["guess"] == [("wrong", cand)] and r["concluded"] == [True] and r["n_checks"] >= 2
    r = TR.run_tree({"name": "t", "preamble": None, "root": {"op": "find_feeder"}}, cs, Scripted(), ctx)
    assert r["guess"] == [("unlisted",)] and r["concluded"] == [False] and r["n_checks"] == len(cs[0].candidates) - 1


def test_find_feeder_matches_v0s_walk_and_respects_the_check_limit(monkeypatch):
    from docmismatch.troubleshoot.v1.study_fast_v1 import Doer, walk_alternatives
    cs, ctx = cases(rooms=(1,))
    cand = [c for c in cs[0].candidates if c != cs[0].doc][3]
    for feeder in (cand, None):
        r = TR.run_tree({"name": "t", "preamble": None, "root": {"op": "find_feeder"}}, cs, Scripted(feeder=feeder), ctx)
        d = Doer(cs[0], ctx[0], lambda ck, tgt: Scripted(feeder=feeder).ask_room(0, ck, tgt))
        found = walk_alternatives(cs[0], d)
        assert r["guess"] == [found if found is not None else ("unlisted",)] and r["minutes"] == pytest.approx(d.s.elapsed) and r["n_checks"] == len(d.trace)
    monkeypatch.setattr(TR, "MAX_CHECKS_PER_COMPLAINT", 2)
    r = TR.run_tree({"name": "t", "preamble": None, "root": {"op": "find_feeder"}}, cs, Scripted(feeder=cand), ctx)
    assert r["n_checks"] == 2 and r["guess"] == [("unlisted",)] and r["concluded"] == [False]


def test_location_carries_between_complaints():
    t = {"root": chk(["power_24vac"], CON("no_power"), CON("other"))}
    cs, ctx = cases(rooms=(1, 2))
    r = TR.run_tree({"name": "t", "preamble": None, **t}, cs, Scripted(), ctx)
    assert r["minutes"] == pytest.approx(10 + 10)                    # box 2's complaint pays its own walk: a different box
    t2 = {"root": chk(["bas_airflow"], CON("other"), CON("other"))}
    r2 = TR.run_tree({"name": "t", "preamble": None, **t2}, cs, Scripted(), ctx)
    assert r2["minutes"] == pytest.approx(4)                         # both at the console: no walking between them


def test_tree_E_runs_on_real_visits_and_is_deterministic():
    cb = ST.cases_for(TIER, ST.TAU, ST.MIN_RATE, "mostly_right", BLD)
    ca = W.make_cases(BLD)
    wp = ST.base_worlds()[6][1].params()
    for i in range(30):
        ev = W.draw_event(6, i, wp, ca)
        cs = [cb[r] for r in ev.rooms]
        ctx = [W.context_dict(TIER, r) for r in ev.rooms]
        a = TR.run_tree(TR.tree_E(False), cs, TableOracle(ev, 0.0), ctx)
        b = TR.run_tree(TR.tree_E(False), cs, TableOracle(ev, 0.0), ctx)
        assert a == b and len(a["guess"]) == ev.n and all(g is not None for g in a["guess"])


# ---------------------------------------------------------------------------------------------- the world
def test_neutral_world_is_the_existing_generator_and_table():
    ok, msg = ST.gate_neutral_world()
    assert ok, msg


def test_mixes_shift_mass_the_way_they_say():
    cs, pr = W.local_prior(W.make_cases(BLD)[("T2", 1)], 0.05, 1)
    ix = {c[0]: k for k, c in enumerate(cs)}
    for mix, up, down in (("controls", "controller_config", "actuator_fail"), ("mechanical", "actuator_fail", "controller_config"), ("zone_side", "zone_sensor_setpoint", "actuator_fail")):
        q = ST.mix_prior(cs, pr, mix)
        assert q[ix[up]] > pr[ix[up]] and q[ix[down]] < pr[ix[down]] and q.sum() == pytest.approx(1)
    flat = ST.mix_prior(cs, pr, "flat")
    leaf = [k for k, c in enumerate(cs) if c[0] not in ("wrong", "unlisted") and pr[k] > 0]
    assert np.allclose(flat[leaf], flat[leaf][0])
    assert flat[ix["ahu_fan_off"]] == 0 and flat[ix["low_static"]] == 0       # the upstream causes stay out of the local prior


def test_a_cause_mix_changes_the_events_but_not_the_arrival_process():
    cases_all = W.make_cases(BLD)
    a = ST.World("a", "x")
    b = ST.World("b", "x", mix="mechanical")
    ea = [ST.draw_event_mix(100, i, a, cases_all) for i in range(300)]
    eb = [ST.draw_event_mix(100, i, b, cases_all) for i in range(300)]
    mech = ("actuator_fail", "damper_mech", "no_power")
    assert sum(c[0] in mech for e in eb for c in e.causes) > 2 * sum(c[0] in mech for e in ea for c in e.causes)


def test_noise_touches_only_the_family_it_names():
    bas = ST.world_checks(ST.World("b", "x", bas_noise=0.5))
    base = K.CATALOGUE
    for c, o in zip(bas, base):
        if c.family == "control system":
            assert c != o
        else:
            assert c == o
    fld = ST.world_checks(ST.World("f", "x", field_noise=0.5))
    for c, o in zip(fld, base):
        assert (c == o) == (c.family == "control system")


def test_false_alarms_and_misses_move_the_right_numbers():
    fa = {c.name: c for c in ST.world_checks(ST.World("f", "x", fa_mult=3.0))}
    assert fa["bas_airflow"].bg == pytest.approx(0.15) and fa["bas_airflow"].detects["low_static"] >= 0.5
    hk = {c.name: c for c in ST.world_checks(ST.World("h", "x", hit_keep=0.6))}
    assert hk["bas_airflow"].bg == 0.05 and hk["bas_airflow"].detects["ahu_fan_off"] == pytest.approx(0.05 + 0.6 * (0.92 - 0.05))


def test_jitter_is_deterministic_and_seeded():
    a, b, c = (ST.world_checks(ST.World("j", "x", jitter=1.0, table_seed=s)) for s in (1, 1, 2))
    assert a == b and a != c and a != K.CATALOGUE
    s1 = ST.world_checks(ST.World("s", "x", struct=0.2, table_seed=1))
    assert any(x.detects != y.detects for x, y in zip(s1, K.CATALOGUE) if x.is_reading)


def test_a_stuck_static_sensor_only_affects_the_control_system_read():
    cases_all = W.make_cases(BLD)
    ev = W.draw_event(6, 0, ST.base_worlds()[6][1].params(), cases_all)
    cb = ST.cases_for(TIER, ST.TAU, ST.MIN_RATE, "mostly_right", BLD)
    ck = {c.name: c for c in cb[ev.rooms[0]].checks}
    tc = {c.name: c for c in K.CATALOGUE}
    stuck = StressStuck = ST.StressOracle(ev, tc, 1.0)
    assert stuck.ask_ahu(cb[ev.rooms[0]].ahu, ck["bas_static"]) == "normal"
    assert ST.StressOracle(ev, tc, 0.0).ask_ahu(cb[ev.rooms[0]].ahu, ck["ahu_gauge"]) == TableOracle(ev, 0.0).ask_ahu(cb[ev.rooms[0]].ahu, ck["ahu_gauge"])
    assert stuck.ask_ahu(cb[ev.rooms[0]].ahu, ck["ahu_gauge"]) == TableOracle(ev, 0.0).ask_ahu(cb[ev.rooms[0]].ahu, ck["ahu_gauge"])


# ---------------------------------------------------------------------------------------------- comparisons and verdicts
def arrays(minutes, acc, wc, conc, n=None):
    n = np.full(len(minutes), 2.0) if n is None else n
    return dict(minutes=np.asarray(minutes, float), checks=np.asarray(minutes, float) / 5, acc=np.asarray(acc, float), wc=np.asarray(wc, float), conc=np.asarray(conc, float) / n, n=n,
                correct=np.asarray(acc, float) * n, concluded=np.asarray(conc, float))


def test_material_advantage_bars():
    rng = np.random.default_rng(1)
    n = 400
    base = arrays(60 + rng.normal(0, 3, n), np.full(n, 0.7), np.zeros(n), np.full(n, 2))
    boot = rng.integers(0, n, (300, n))
    idx = np.arange(n)
    faster = arrays(base["minutes"] * 0.8, base["acc"], base["wc"], np.full(n, 2))
    assert ST.compare(faster, base, idx, boot)["mat_time"]
    assert not ST.compare(arrays(base["minutes"] * 0.9, base["acc"], base["wc"], np.full(n, 2)), base, idx, boot)["material"]          # 10% faster is not material
    assert not ST.compare(arrays(base["minutes"] * 0.8, base["acc"] - 0.05, base["wc"], np.full(n, 2)), base, idx, boot)["mat_time"]    # faster but less accurate: not material
    assert ST.compare(arrays(base["minutes"], base["acc"] + 0.06, base["wc"], np.full(n, 2)), base, idx, boot)["mat_acc"]
    assert not ST.compare(arrays(base["minutes"] * 1.3, base["acc"] + 0.06, base["wc"], np.full(n, 2)), base, idx, boot)["mat_acc"]  # bought with 30% more time: a trade, not dominance
    risky = arrays(base["minutes"], base["acc"], np.full(n, 0.05), np.full(n, 2))
    safer = arrays(base["minutes"], base["acc"], np.full(n, 0.0), np.full(n, 2))
    assert ST.compare(safer, risky, idx, boot)["mat_safe"] and not ST.compare(risky, safer, idx, boot)["mat_safe"]
    assert not ST.compare(arrays(base["minutes"] * 1.3, base["acc"], np.full(n, 0.0), np.full(n, 2)), risky, idx, boot)["mat_safe"]       # safer but 30% slower: not material


def test_verdict_states_follow_the_registered_counts():
    assert [ST.gap_state(k) for k in (0, 5, 6, 11, 12, 18)] == ["ALREADY CLOSE", "ALREADY CLOSE", "MIXED", "MIXED", "MATERIAL GAP", "MATERIAL GAP"]
    assert ST.gap_state(2, 9) == "ALREADY CLOSE" and ST.gap_state(3, 9) == "MIXED" and ST.gap_state(6, 9) == "MATERIAL GAP"
    assert ST.stress_state(20, 0, 26) == "SURVIVES" and ST.stress_state(12, 0, 26) == "ERODES" and ST.stress_state(5, 0, 26) == "DOES NOT SURVIVE"
    assert ST.stress_state(20, 9, 26) == "REVERSES" and ST.stress_state(26, 0, 26) == "SURVIVES"


def test_value_model_break_even_and_states():
    rng = np.random.default_rng(2)
    n = 300
    n_c = np.full(n, 2.0)
    tool = dict(minutes=np.full(n, 70.0), wc=np.full(n, 0.0), concluded=np.full(n, 0.0), n=n_c)
    tree = dict(minutes=np.full(n, 50.0), wc=np.full(n, 0.10), concluded=np.full(n, 2.0), n=n_c)       # tree: 20 min faster, declares everything, 0.2 wrong per visit
    boot = rng.integers(0, n, (200, n))
    v = ST.value_compare(tool, tree, np.arange(n), boot)
    # tool costs 70 + 2*cu; tree 50 + 0.2*cw  ->  tool saves 0.2 cw - 20 - 2 cu ; break-even cw at cu = 0 is 100, at cu = 30 is 400
    assert v["grid"][(120.0, 0.0)] == pytest.approx(0.2 * 120 - 20)
    assert v["grid"][(120.0, 30.0)] == pytest.approx(0.2 * 120 - 20 - 2 * 30)                       # the tool leaves both complaints undeclared: 30 minutes each
    assert ST.visit_cost(tree, np.arange(3), 100.0, 7.0).tolist() == [50 + 100 * 0.2 + 0.0] * 3
    assert v["break_even_wrong"][0.0] == pytest.approx(100.0) and v["break_even_wrong"][30.0] == pytest.approx(400.0)
    assert v["state"] == "DEPENDS ON THE COSTS"
    tool2 = dict(tool, minutes=np.full(n, 40.0), concluded=np.full(n, 2.0))
    assert ST.value_compare(tool2, tree, np.arange(n), boot)["state"] == "TOOL AHEAD"
    assert ST.value_compare(tree, tool2, np.arange(n), boot)["state"] == "TOOL BEHIND"


# ---------------------------------------------------------------------------------------------- gates, and a deliberately broken machine
def all_trees():
    return dict(tree_E=TR.tree_E(False), tree_Ed=TR.tree_E(True), tree_L1=TR.tree_E(False), tree_L2=TR.tree_E(True), tree_I1=TR.tree_E(False), tree_I2=TR.tree_E(True))


def test_fair_accounting_gate_passes():
    ok, msg = ST.gate_fair_accounting(all_trees(), n_events=12)
    assert ok, msg


def test_fair_accounting_gate_catches_a_free_step(monkeypatch):
    orig = TR._Visit._do

    def free(self, i, ck):
        d = self.doers[i]
        before = d.s.elapsed
        pos = orig(self, i, ck)
        d.s.elapsed = before                         # nobody is charged
        return pos

    monkeypatch.setattr(TR._Visit, "_do", free)
    ok, _ = ST.gate_fair_accounting(all_trees(), n_events=6)
    assert not ok


def test_fair_accounting_gate_catches_a_doubled_step(monkeypatch):
    orig = TR._Visit._do

    def twice(self, i, ck):
        pos = orig(self, i, ck)
        self.doers[i].s.elapsed += ck.do_min
        return pos

    monkeypatch.setattr(TR._Visit, "_do", twice)
    ok, _ = ST.gate_fair_accounting(all_trees(), n_events=6)
    assert not ok


def test_tree_gate_passes_and_catches_a_broken_tree():
    ok, msg = ST.gate_trees(all_trees())
    assert ok, msg
    bad = all_trees()
    bad["tree_L1"] = {"name": "x", "preamble": None, "root": chk(["bas_airflow"], CON("low_static"), None)}
    assert not ST.gate_trees(bad)[0]


def test_oracle_gate():
    ok, msg = ST.gate_oracle()
    assert ok, msg


def test_arm_results_are_scored_like_the_tool():
    bld = BLD
    cases_all = W.make_cases(bld)
    w = ST.base_worlds()[6][1]
    out = ST.run_world(6, w, 20, all_trees(), tiers=(TIER,))
    for arm in ST.ARMS:
        a = out["arms"][(TIER, arm)]
        assert a["minutes"].shape == (20,) and (a["acc"] >= 0).all() and (a["acc"] <= 1).all() and (a["conc"] <= 1).all()
        assert len(a["guess_flat"]) == int(out["n_compl"].sum())
    assert (out["arms"][(TIER, "no_check")]["minutes"] == 0).all() and (out["arms"][(TIER, "no_check")]["conc"] == 0).all()
    an = ST.analyze_world(out)
    assert (TIER, "tool_joint", "tree_E", "all") in an["cmp"] and (TIER, "tree_E", "tool_joint", "all") in an["cmp"]
    assert (TIER, "tree_E", "all") in an["val"]


def test_verdicts_and_predictions_run_end_to_end_on_a_tiny_study():
    trees = all_trees()
    base = [w for i, w in ST.base_worlds() if w.name == "assumed/M0/R0"]
    base_idx = [i for i, w in ST.base_worlds() if w.name == "assumed/M0/R0"]
    sw = [(i, w) for i, w in ST.stress_worlds() if w.jitter == 1.0 or w.econ]
    assert len(base) == 1 and len(sw) == 3
    rb = ST.compute([(base_idx[0], base[0])], trees, 40, workers=1, frontier_idx=base_idx[0], tiers=(TIER,))
    rs = ST.compute(sw, trees, 40, workers=1, tiers=(TIER,))
    ab, as_ = [ST.analyze_world(r, B=60) for r in rb], [ST.analyze_world(r, B=60) for r in rs]
    v = ST.verdicts(ab, as_)
    for k in ("gap_E", "gap_blind", "gap_informed", "gap_all_trees", "stress_E", "stress_informed", "commercial", "commercial_informed", "value_base_E", "value_stress_E"):
        assert k in v
    assert v["gap_E"][1] in ("ALREADY CLOSE", "MIXED", "MATERIAL GAP")
    p = ST.predictions(ab, as_, v)
    assert set(p) == {f"P{k}" for k in range(1, 15)} and all(isinstance(x[0], bool) for x in p.values())
    assert any(k[1].startswith("tool@") for k in ab[0]["sum"])                                       # the frontier arms were run
    assert ab[0]["val"][(TIER, "tree_E", "all")]["state"] in ("TOOL AHEAD", "DEPENDS ON THE COSTS", "TOOL BEHIND")
