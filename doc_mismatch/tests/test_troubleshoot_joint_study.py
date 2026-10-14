"""Guards for the joint-session study code (docmismatch.troubleshoot.v2.study_joint, scripts/74; PREREGISTRATION_DR.md Addendum 30). No test here reads a study result: they check code paths,
rules and gates on synthetic arrays and on tiny runs whose numbers are never inspected."""
import importlib.util
import pickle
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot import study_rating as SG  # noqa: E402
from docmismatch.troubleshoot.v2 import joint as Jn, policies as P, study_joint as J, world2 as W  # noqa: E402

spec = importlib.util.spec_from_file_location("script74", ROOT / "scripts" / "74_troubleshoot_joint.py")
S74 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S74)

PRIMARY = J.Cell(**J.PRIMARY)


# ---------------------------------------------------------------------------------------------- the grid and the constants
def test_the_grid_has_eighteen_cells_in_the_stated_order_and_one_primary():
    cells = J.all_cells()
    assert len(cells) == 18 and len(set(cells)) == 18 and sum(c.is_primary for c in cells) == 1
    assert [(c.shared, c.map, c.rel) for c in cells[:3]] == [("rare", "M0", "R0"), ("rare", "M0", "R1"), ("rare", "M1", "R0")]                # the last factor varies fastest
    assert [c.shared for c in cells] == ["rare"] * 6 + ["assumed"] * 6 + ["common"] * 6 and cells[6 + 0] == PRIMARY
    assert J.LEVELS == dict(shared=("rare", "assumed", "common"), map=("M0", "M1", "M2"), rel=("R0", "R1"))


def test_the_world_factors_are_the_frozen_ones():
    assert J.F_OF == dict(rare=0.01, assumed=0.03, common=0.09) and J.MAP_OF == dict(M0=(0.0, 0.05), M1=(0.10, 0.05), M2=(0.10, 0.15)) and J.REL_A == dict(R0=0.0, R1=0.25)
    p = J.Cell("common", "M2", "R1").params()
    assert (p.f, p.q_ahu, p.p_wrong, p.rel_a) == (0.09, 0.10, 0.15, 0.25)
    assert PRIMARY.params() == W.WorldParams(0.03, 0.0, 0.05, 0.0)
    assert J.TIERS == ("T2", "T3") and J.SUBSETS == ("all", "shared", "multi", "single") and J.SEED == 30 and J.BOOT_B == 1000 and J.N_EPISODES == 1000 and J.TRACE_EVENTS == 12


def test_look_ahead_runs_only_in_the_three_cells_with_map_m0_and_rel_r0():
    la = [c for c in J.all_cells() if c.has_lookahead]
    assert [(c.shared, c.map, c.rel) for c in la] == [(s, "M0", "R0") for s in ("rare", "assumed", "common")]
    for c in J.all_cells():
        pols = J.policies_for(c)
        assert (("tool_joint_la2" in pols) == c.has_lookahead) and len(pols) == (7 if c.has_lookahead else 6) and pols == tuple(p for p in P.POLICIES if p in pols)


def test_the_comparisons_are_the_frozen_ones():
    assert J.COMPS == dict(A=("tool_joint", "tool_ticket"), B=("tool_joint", "tool_ticket_memo"), C=("tool_ticket_memo", "tool_ticket"), D=("tool_ticket_nb", "tool_ticket"),
                           E=("tool_joint", "fast_parent"), F=("tool_joint", "fast_ticket"), G=("tool_joint_la2", "tool_joint"))
    assert (J.SHARE_BAR, J.P2_BAR, J.P3_BAR, J.P5_BAR, J.P6_MIN, J.P6_ACC, J.P7_MIN, J.P7_ACC, J.P8_BAR, J.P9_BAR, J.UNSAFE_BAR, J.UNSAFE_CELLS) == (0.15, 0.10, 0.0, 0.01, 0.05, 0.10, 0.03, 0.02, 0.05, 0.03, 0.02, 2)


def test_the_tools_assumptions_are_the_frozen_ones_and_the_same_everywhere():
    assert J.tool_settings_tag() == (0.05, 0.15, 0.10, 0.95, 1e-6, 0.03, 5 / 17, 0.03, 0.9, 0.5)
    assert W.SEED == 30 and (W.N_AHU, W.PER_AHU, W.RHO, W.R_AFFECT) == (3, 8, 0.03, {"ahu_fan_off": 0.9, "low_static": 0.5}) and W.TOOL_RATING == "mostly_right"
    assert Jn.MAX_CHECKS_PER_COMPLAINT == 12 and Jn.LOOKAHEAD_TOP == 6


# ---------------------------------------------------------------------------------------------- scoring
def test_score_counts_exact_correct_confident_wrong_and_concluded():
    ev = W.Event(0, 0, {}, {}, [0, 1, 2, 3], [("a",), ("b",), ("c",), ("d",)], ["AHU-0"] * 4)
    res = dict(guess=[("a",), ("x",), ("c",), ("y",)], concluded=[True, True, False, False])
    assert J.score(res, ev) == (2, 1, 2)                                       # correct: a, c; concluded and wrong: x; concluded: a, x


# ---------------------------------------------------------------------------------------------- tiny runs
@pytest.fixture(scope="module")
def tiny():
    cells = J.all_cells()
    return {0: J.run_cell(0, cells[0], 12), 1: J.run_cell(1, cells[1], 12)}


def test_a_cell_run_has_every_policy_at_both_tiers_on_identical_events(tiny):
    r = tiny[0]
    assert r["n"] == 12 and len(r["n_compl"]) == 12 and (r["n_compl"] >= 1).all() and set(r["kind"]) <= {"single", "shared", "multi"}
    assert {k for k in r["pol"]} == {(t, p) for t in J.TIERS for p in P.POLICIES}                         # cell 0 has the look-ahead
    assert {k for k in tiny[1]["pol"]} == {(t, p) for t in J.TIERS for p in P.POLICIES if p != "tool_joint_la2"}
    for v in r["pol"].values():
        assert len(v["minutes"]) == 12 and np.isfinite(v["minutes"]).all() and (v["minutes"] >= 0).all() and (v["correct"] <= r["n_compl"]).all() and (v["wc"] <= v["concluded"]).all()
        assert len(v["trace"]) == 12 and len(v["guess"]) == 12                                              # fewer events than TRACE_EVENTS: all of them
    assert r["tag"] == J.tool_settings_tag()


def test_a_cell_run_is_reproducible_and_independent_of_the_number_of_workers(tiny):
    again = J.run_cell(0, J.all_cells()[0], 12)
    for k, v in tiny[0]["pol"].items():
        assert np.array_equal(v["minutes"], again["pol"][k]["minutes"]) and np.array_equal(v["correct"], again["pol"][k]["correct"])
    a = J.compute_cells([(0, J.all_cells()[0]), (1, J.all_cells()[1])], 6, workers=1)
    b = J.compute_cells([(0, J.all_cells()[0]), (1, J.all_cells()[1])], 6, workers=2)
    for x, y in zip(a, b):
        assert x["idx"] == y["idx"] and all(np.array_equal(x["pol"][k]["minutes"], y["pol"][k]["minutes"]) for k in x["pol"]) and np.array_equal(x["n_compl"], y["n_compl"])


def test_the_first_events_of_a_prefix_run_are_the_same_events(tiny):
    short = J.run_cell(0, J.all_cells()[0], 5)
    assert np.array_equal(short["n_compl"], tiny[0]["n_compl"][:5])
    for k, v in short["pol"].items():
        assert np.array_equal(v["minutes"], tiny[0]["pol"][k]["minutes"][:5])


def test_analysis_has_every_summary_and_comparison(tiny):
    a = J.analyze_cell(tiny[0], 50)
    assert a["idx"] == 0 and a["n"] == 12 and sum(a["counts"][s] for s in ("shared", "multi", "single")) == 12 and a["counts"]["all"] == 12
    for t in J.TIERS:
        for pol in P.POLICIES:
            assert (t, pol, "all") in a["sum"] and a["sum"][(t, pol, "all")]["n"] == 12
        for name in J.COMPS:
            assert (t, name, "all") in a["cmp"]
    a1 = J.analyze_cell(tiny[1], 50)
    assert not any(k[1] == "G" for k in a1["cmp"]) and not any(k[1] == "tool_joint_la2" for k in a1["sum"])
    e = a["cmp"][("T2", "B", "all")]
    assert set(e) >= {"d_min", "r_min", "d_acc", "d_wc", "d_checks", "ci_min", "ci_acc", "ci_wc", "time", "acc", "label", "safety", "break_even", "wrong_cost"}


# ---------------------------------------------------------------------------------------------- summaries and comparisons on synthetic arrays
def _res(minutes_a, minutes_b, correct_a, correct_b, n_compl, wc_a=None, wc_b=None, kind=None):
    n = len(n_compl)
    z = np.zeros(n)
    mk = lambda m, c, w: dict(minutes=np.array(m, float), checks=np.ones(n), correct=np.array(c, float), wc=np.array(w if w is not None else z, float), concluded=np.array(n_compl, float), trace=[], guess=[])  # noqa: E731
    return dict(idx=0, cell=PRIMARY, n=n, n_compl=np.array(n_compl), kind=np.array(kind if kind is not None else ["single"] * n), pol={("T2", "tool_joint"): mk(minutes_a, correct_a, wc_a), ("T2", "tool_ticket"): mk(minutes_b, correct_b, wc_b)})


def test_per_event_and_summary_arithmetic():
    r = _res([10, 30], [20, 20], [1, 1], [2, 0], [1, 2], wc_a=[0, 1])
    v = J.per_event(r, "T2", "tool_joint")
    assert np.allclose(v["acc"], [1.0, 0.5]) and np.allclose(v["wc"], [0.0, 0.5]) and np.allclose(v["conc"], [1.0, 1.0]) and np.allclose(v["n"], [1, 2])
    s = J.summarize(v, np.array([True, True]))
    assert s["n"] == 2 and s["minutes"] == 20 and s["accuracy"] == pytest.approx(0.75) and s["accuracy_c"] == pytest.approx(2 / 3) and s["wrong_confident"] == pytest.approx(0.25) and s["complaints"] == 1.5
    assert J.summarize(v, np.array([False, False])) == dict(n=0) and J.summarize(v, np.array([True, False]))["minutes"] == 10


def test_a_comparison_is_first_minus_second_with_the_frozen_labels():
    n = 60
    rng = np.random.default_rng(1)
    base = 100 + rng.normal(0, 3, n)
    r = _res(base * 0.7, base, np.ones(n), np.ones(n), [1] * n)
    boot = np.random.default_rng(2).integers(0, n, (200, n))
    e = J.compare(r, "T2", "tool_joint", "tool_ticket", np.arange(n), boot)
    assert e["r_min"] == pytest.approx(-0.3, abs=1e-9) and e["d_min"] == pytest.approx(-0.3 * base.mean()) and e["time"] == "FASTER" and e["acc"] == "SAME" and e["label"] == "IMPROVES" and e["safety"] == "NONE"
    assert e["break_even"] == "DOMINATES" and e["minutes_a"] < e["minutes_b"]
    slow = J.compare(_res(base * 1.3, base, np.ones(n), np.ones(n), [1] * n), "T2", "tool_joint", "tool_ticket", np.arange(n), boot)
    assert slow["time"] == "SLOWER" and slow["label"] == "WORSE"
    trade = J.compare(_res(base * 1.3, base, np.ones(n), np.zeros(n), [1] * n), "T2", "tool_joint", "tool_ticket", np.arange(n), boot)
    assert trade["time"] == "SLOWER" and trade["acc"] == "MORE" and trade["label"] == "TRADE" and trade["break_even"] == "SLOWER-MORE" and trade["wrong_cost"] == pytest.approx(0.3 * base.mean())
    unsafe = J.compare(_res(base, base, np.ones(n), np.ones(n), [1] * n, wc_a=np.ones(n)), "T2", "tool_joint", "tool_ticket", np.arange(n), boot)
    assert unsafe["safety"] == "REGRESSION" and unsafe["d_wc"] == 1.0


def test_subset_masks_partition_the_events():
    r = _res([1] * 5, [1] * 5, [1] * 5, [1] * 5, [1, 2, 2, 3, 1], kind=["single", "shared", "multi", "shared", "single"])
    m = J.subset_masks(r)
    assert m["all"].all() and list(m["shared"]) == [False, True, False, True, False] and list(m["multi"]) == [False, False, True, False, False] and list(m["single"]) == [True, False, False, False, True]
    assert (m["shared"] | m["multi"] | m["single"]).all() and not (m["shared"] & m["multi"]).any()


def _cmp(label="NEITHER", time="SAME", acc="SAME", safety="NONE", **kw):
    return dict(label=label, time=time, acc=acc, safety=safety, r_min=kw.get("r_min", 0.0), d_min=kw.get("d_min", 0.0), d_acc=0.0, d_wc=0.0, d_checks=0.0, ci_min=(0, 0), ci_acc=(0, 0), ci_wc=(0, 0),
                break_even="DOMINATES", wrong_cost=0.0, minutes_a=100.0, minutes_b=100.0)


def test_shares_count_labels_the_two_kinds_of_trade_and_safety():
    an = [dict(cmp={("T2", "B", "all"): _cmp(*args, **kw)}) for args, kw in (
        (("IMPROVES", "FASTER", "SAME"), {}), (("WORSE", "SLOWER", "SAME"), {}), (("TRADE", "FASTER", "LESS"), dict(safety="REGRESSION")), (("TRADE", "SLOWER", "MORE"), dict(safety="GAIN")), (("NEITHER",), {}))]
    sh = J.shares(an, ("T2", "B", "all"))
    assert (sh["IMPROVES"], sh["WORSE"], sh["TRADE"], sh["NEITHER"]) == (0.2, 0.2, 0.4, 0.2) and sh["FASTER_LESS"] == 0.2 and sh["SLOWER_MORE"] == 0.2
    assert sh["SAFETY_REGRESSION"] == 0.2 and sh["SAFETY_GAIN"] == 0.2 and sh["n_cells"] == 5
    assert J.shares(an, ("T3", "B", "all"))["n_cells"] == 0


def test_cell_lookup_needs_exactly_one_match():
    an = [dict(cell=c) for c in J.all_cells()]
    assert J.cell_of(an, **J.PRIMARY)["cell"] == PRIMARY and J.cell_of(an, shared="rare", map="M2", rel="R1")["cell"] == J.Cell("rare", "M2", "R1")
    with pytest.raises(KeyError):
        J.cell_of(an, shared="rare")
    with pytest.raises(KeyError):
        J.cell_of(an[:1], shared="common")


# ---------------------------------------------------------------------------------------------- predictions and decision on synthetic analyses
def fake_analyses(edit=None):
    """18 cells, every policy summary and comparison neutral (100 minutes, accuracy 0.90, wrong-and-confident 0.02, no difference); `edit(cell, sum, cmp)` may change them."""
    out = []
    for i, c in enumerate(J.all_cells()):
        sm, cm = {}, {}
        for t in J.TIERS:
            for pol in J.policies_for(c):
                for sub in J.SUBSETS:
                    sm[(t, pol, sub)] = dict(n=50, minutes=100.0, checks=5.0, accuracy=0.9, accuracy_c=0.9, wrong_confident=0.02, concluded=0.9, complaints=2.0)
            for name, (a, b) in J.COMPS.items():
                if a in P.LOOKAHEAD_POLICIES and not c.has_lookahead:
                    continue
                for sub in J.SUBSETS:
                    cm[(t, name, sub)] = _cmp()
        if edit:
            edit(c, sm, cm)
        out.append(dict(idx=i, cell=c, n=100, counts={k: 10 for k in J.SUBSETS}, sum=sm, cmp=cm, mean_complaints=2.0))
    return out


def holds(an):
    return {k: ok for k, (ok, _) in J.joint_predictions(an).items()}


def edit_primary(fn):
    return lambda c, sm, cm: fn(sm, cm) if c == PRIMARY else None


def _p_ok(sm, cm):
    """Edits under which every prediction holds."""
    cm[("T2", "A", "shared")] = _cmp(r_min=-0.4, d_min=-40.0, time="FASTER")
    cm[("T3", "A", "shared")] = _cmp(r_min=-0.1, d_min=-5.0)
    cm[("T2", "B", "shared")] = _cmp(r_min=-0.05)
    cm[("T2", "D", "all")] = _cmp(r_min=-0.1)
    sm[("T2", "fast_parent", "all")]["minutes"] = 90.0
    sm[("T2", "fast_parent", "all")]["accuracy"] = 0.7


def _all_hold(c, sm, cm):
    if c == PRIMARY:
        _p_ok(sm, cm)
    if c == J.Cell("assumed", "M1", "R0"):
        sm[("T2", "tool_joint", "all")]["wrong_confident"] = 0.05
        sm[("T2", "tool_ticket_memo", "all")]["wrong_confident"] = 0.03
    if c.has_lookahead:
        pass
    if c == J.Cell("rare", "M0", "R0"):
        for t in J.TIERS:
            sm[(t, "tool_ticket_memo", "all")]["minutes"] = 101.0


def test_every_prediction_holds_on_the_constructed_analyses_and_each_fails_on_its_own_edit():
    base = holds(fake_analyses(_all_hold))
    assert base == {f"P{i}": True for i in range(1, 10)}, base
    def fails(key, fn):
        an = fake_analyses(lambda c, sm, cm: (_all_hold(c, sm, cm), fn(c, sm, cm)))
        got = holds(an)
        assert got[key] is False and all(v for k, v in got.items() if k != key), (key, got)
    fails("P1", lambda c, sm, cm: cm.__setitem__(("T2", "A", "shared"), _cmp(r_min=-0.14, d_min=-40.0)) if c == PRIMARY else None)                         # only 14% fewer minutes
    fails("P1", lambda c, sm, cm: cm.__setitem__(("T2", "A", "shared"), _cmp(r_min=-0.4, d_min=-40.0, acc="LESS")) if c == PRIMARY else None)                # not LESS accurate
    fails("P2", lambda c, sm, cm: cm.__setitem__(("T2", "B", "shared"), _cmp(r_min=-0.10)) if c == PRIMARY else None)                                       # exactly 10% fewer is not less than 10%
    fails("P3", lambda c, sm, cm: cm.__setitem__(("T2", "D", "all"), _cmp(r_min=0.0)) if c == PRIMARY else None)
    fails("P4", lambda c, sm, cm: cm.__setitem__(("T3", "A", "shared"), _cmp(r_min=-0.1, d_min=-40.0)) if c == PRIMARY else None)                          # equal savings at both tiers
    fails("P5", lambda c, sm, cm: sm[("T2", "tool_joint", "all")].__setitem__("wrong_confident", 0.025) if c == J.Cell("assumed", "M1", "R0") else None)     # +0.005 only
    fails("P5", lambda c, sm, cm: sm[("T2", "tool_ticket_memo", "all")].__setitem__("wrong_confident", 0.06) if c == J.Cell("assumed", "M1", "R0") else None)  # memo worse than joint in M1
    fails("P6", lambda c, sm, cm: sm[("T2", "fast_parent", "all")].__setitem__("minutes", 96.0) if c == PRIMARY else None)                                  # only 4% faster
    fails("P6", lambda c, sm, cm: sm[("T2", "fast_parent", "all")].__setitem__("accuracy", 0.85) if c == PRIMARY else None)                                 # only 0.05 less accurate
    fails("P7", lambda c, sm, cm: sm[("T3", "tool_joint_la2", "all")].__setitem__("minutes", 103.5) if c == J.Cell("common", "M0", "R0") else None)          # 3.5% apart
    fails("P7", lambda c, sm, cm: sm[("T2", "tool_joint_la2", "all")].__setitem__("accuracy", 0.93) if c == J.Cell("rare", "M0", "R0") else None)            # 0.03 apart
    fails("P8", lambda c, sm, cm: sm[("T3", "tool_ticket_nb", "single")].__setitem__("minutes", 90.0) if c == PRIMARY else None)                            # 10% apart
    fails("P9", lambda c, sm, cm: sm[("T2", "tool_ticket_memo", "all")].__setitem__("minutes", 104.0) if c == J.Cell("rare", "M0", "R0") else None)        # joint 3.8% ahead of memo


def test_the_decision_follows_the_frozen_rules_and_the_safety_qualifier():
    def dec(b2="NEITHER", b3="NEITHER", c2="NEITHER", unsafe=0):
        def edit(c, sm, cm):
            if c == PRIMARY:
                cm[("T2", "B", "shared")], cm[("T3", "B", "shared")], cm[("T2", "C", "shared")] = _cmp(b2), _cmp(b3), _cmp(c2)
            cells = [J.Cell("assumed", m, "R0") for m in ("M1", "M2")]
            if c in cells and unsafe > 0:
                k = cells.index(c) * 2
                for j, t in enumerate(J.TIERS):
                    if k + j < unsafe:
                        sm[(t, "tool_joint", "all")]["wrong_confident"] = 0.045                                # 0.025 above ticket_memo's 0.02
        return J.decision(fake_analyses(edit))
    assert dec("IMPROVES", "NEITHER") == "JOINT MACHINERY ADDS VALUE" and dec("IMPROVES", "IMPROVES") == "JOINT MACHINERY ADDS VALUE"
    assert dec("IMPROVES", "WORSE", c2="IMPROVES") == "THE ROUTINE CAPTURES IT"                                # T3 worse than the routine: not "adds value"; the routine still improves on tickets
    assert dec("NEITHER", c2="IMPROVES") == "THE ROUTINE CAPTURES IT" and dec("WORSE", c2="IMPROVES") == "THE ROUTINE CAPTURES IT"
    assert dec("NEITHER") == "NO GAIN FROM SHARING" and dec("IMPROVES", "WORSE") == "NO GAIN FROM SHARING"
    assert dec("IMPROVES", unsafe=1) == "JOINT MACHINERY ADDS VALUE" and dec("IMPROVES", unsafe=2) == "JOINT MACHINERY ADDS VALUE + UNSAFE UNDER MAP FAULTS"
    assert dec("NEITHER", unsafe=4) == "NO GAIN FROM SHARING + UNSAFE UNDER MAP FAULTS"


# ---------------------------------------------------------------------------------------------- gates
def test_gate_one_passes_on_the_real_model_and_fails_on_a_broken_one(monkeypatch):
    ok, detail = J.gate_g1(30)
    assert ok and "brute-force" in detail
    orig = J.JointModel.group_stats

    def broken(self, s, a):
        g = orig(self, s, a)
        g.W = np.array([g.W[0], g.W[2], g.W[1]])                                                          # states swapped
        return g
    monkeypatch.setattr(J.JointModel, "group_stats", broken)
    assert J.gate_g1(30)[0] is False


def test_gate_two_passes_and_fails_when_the_ticket_policy_drifts_from_v1(monkeypatch):
    ok, detail = J.gate_g2(5)
    assert ok and "37" in detail
    orig = P.run_ticket

    def drift(cases, oracle, mode, js=None):
        r = orig(cases, oracle, mode, js)
        r["minutes"] += 1.0
        return r
    monkeypatch.setattr(P, "run_ticket", drift)
    assert J.gate_g2(5)[0] is False


def test_gate_three_replays_and_catches_a_tampered_recording(tiny):
    ok, detail = J.gate_g3([tiny[1]])
    assert ok and "60 replayed events" in detail                                                             # 10 events x 2 tiers x 3 policies
    bad = pickle.loads(pickle.dumps(tiny[1]))
    for tier in J.TIERS:
        for pol in ("tool_joint", "tool_ticket_memo", "fast_parent"):
            for tr in bad["pol"][(tier, pol)]["trace"][:10]:
                if tr:
                    last = list(tr[-1])
                    tr[-1] = tuple(last[:-1]) + ("normal" if last[-1] != "normal" else "abnormal",) if last[-1] in ("normal", "abnormal") else tuple(last[:-1]) + ("yes" if last[-1] == "no" else "no",)
    assert J.gate_g3([bad])[0] is False
    assert J.gate_g3([tiny[0]]) == (True, "0 replayed events: 0 differ")                                       # no R1 cell: nothing to replay


def test_gate_four_reproduces_the_first_events_and_catches_a_change(tiny):
    ok, detail = J.gate_g4([tiny[0]], 8)
    assert ok
    bad = pickle.loads(pickle.dumps(tiny[0]))
    bad["pol"][("T2", "tool_joint")]["minutes"][3] += 1.0
    assert J.gate_g4([bad], 8)[0] is False
    bad2 = pickle.loads(pickle.dumps(tiny[0]))
    bad2["n_compl"][2] += 1
    assert J.gate_g4([bad2], 8)[0] is False


def test_gate_five_needs_every_cell_policy_tier_and_finite_numbers(tiny):
    ok, detail = J.gate_g5([tiny[0], tiny[1]], expected_idx=[0, 1], n=12)
    assert ok and "2 cells" in detail
    assert J.gate_g5([tiny[0], tiny[1]])[0] is False                                                          # 18 cells expected
    assert J.gate_g5([tiny[0], tiny[1]], expected_idx=[0, 1], n=13)[0] is False
    miss = pickle.loads(pickle.dumps(tiny[0]))
    del miss["pol"][("T3", "fast_parent")]
    assert J.gate_g5([miss, tiny[1]], expected_idx=[0, 1], n=12)[0] is False
    nan = pickle.loads(pickle.dumps(tiny[0]))
    nan["pol"][("T2", "tool_joint")]["minutes"][0] = np.nan
    assert J.gate_g5([nan, tiny[1]], expected_idx=[0, 1], n=12)[0] is False
    neg = pickle.loads(pickle.dumps(tiny[0]))
    neg["pol"][("T2", "tool_joint")]["minutes"][0] = -1.0
    assert J.gate_g5([neg, tiny[1]], expected_idx=[0, 1], n=12)[0] is False
    extra = pickle.loads(pickle.dumps(tiny[1]))
    extra["pol"][("T2", "tool_joint_la2")] = extra["pol"][("T2", "tool_joint")]                             # look-ahead where it should not be
    assert J.gate_g5([tiny[0], extra], expected_idx=[0, 1], n=12)[0] is False


def _kinds(share, n=100):
    k = np.array(["shared"] * int(round(share * n)) + ["single"] * (n - int(round(share * n))))
    return k


def _fake_result(cell, share, tag=None):
    return dict(idx=0, cell=cell, kind=_kinds(share), tag=tag or J.tool_settings_tag())


def test_gate_six_needs_shared_events_to_rise_with_f_and_the_same_settings_everywhere():
    ok, detail = J.gate_g6([_fake_result(J.Cell(s, "M0", "R0"), sh) for s, sh in (("rare", 0.05), ("assumed", 0.15), ("common", 0.4))])
    assert ok and "rare 5%" in detail and "common 40%" in detail
    assert J.gate_g6([_fake_result(J.Cell(s, "M0", "R0"), sh) for s, sh in (("rare", 0.05), ("assumed", 0.05), ("common", 0.4))])[0] is False           # not strictly rising
    assert J.gate_g6([_fake_result(J.Cell(s, "M0", "R0"), sh) for s, sh in (("rare", 0.2), ("assumed", 0.15), ("common", 0.4))])[0] is False
    assert J.gate_g6([_fake_result(J.Cell("rare", "M0", "R0"), 0.1), _fake_result(J.Cell("assumed", "M0", "R0"), 0.05)])[0] is True                         # a pair of levels only: nothing to check
    mixed = [_fake_result(J.Cell("rare", "M0", "R0"), 0.05), _fake_result(J.Cell("assumed", "M0", "R0"), 0.15, tag=(0.0,) * 10)]
    assert J.gate_g6(mixed)[0] is False


# ---------------------------------------------------------------------------------------------- the script
def test_the_smoke_run_writes_the_report_and_regenerates_from_the_pickle(tmp_path, capsys):
    S74.main(["--smoke", "--out", str(tmp_path), "--workers", "1"])
    out = capsys.readouterr().out
    assert "G1 PASS" in out and "G6 PASS" in out and "FAIL" not in out
    text = (tmp_path / "joint_report.md").read_text()
    assert "SMOKE RUN" in text and "## Gates" in text and "## Every comparison over the cells" in text and "tool_joint_la2" in text and "Frozen decision" not in text
    for f in ("joint_raw.pkl", "joint_analysis.pkl", "joint_cells.csv"):
        assert (tmp_path / f).exists()
    lines = (tmp_path / "joint_cells.csv").read_text().splitlines()
    assert lines[0].startswith("cell,shared,map,rel,tier,policy,subset") and len(lines) > 40
    S74.main(["--smoke", "--out", str(tmp_path), "--from-pickle"])
    assert "G1 PASS" in capsys.readouterr().out


def test_the_report_shows_no_result_when_a_gate_fails(tiny):
    an = [J.analyze_cell(tiny[0], 20)]
    text = S74.report([tiny[0]], an, {"G1 exactness": (False, "broken")}, True, 12, 1.0)
    assert "NO RESULT" in text and "Primary cell" not in text
    text2 = S74.report([tiny[0]], an, {"G1 exactness": (False, "broken")}, False, 12, 1.0)
    assert "SMOKE RUN" in text2 and "NO RESULT" not in text2


def test_the_report_prints_predictions_and_the_decision_only_with_all_cells():
    an = fake_analyses(_all_hold)
    text = S74.report([], an, {"G1 exactness": (True, "ok")}, True, 100, 1.0)
    assert "## Predictions" in text and "| P1 | holds |" in text and "Frozen decision: " in text and "P9" in text
    partial = S74.report([], an[:2], {"G1 exactness": (True, "ok")}, True, 100, 1.0)
    assert "## Predictions" not in partial


# ---------------------------------------------------------------------------------------------- further guards (frozen streams, bootstrap seed, tolerance)
def test_the_stored_episodes_come_from_the_frozen_streams(tiny):
    cases = W.make_cases()
    wp = J.all_cells()[0].params()
    ev = W.draw_event(0, 2, wp, cases)
    for ti, tier in enumerate(J.TIERS):
        for pol in ("tool_ticket", "tool_joint", "fast_parent"):
            cs = [cases[(tier, r)] for r in ev.rooms]
            r = P.run_policy(pol, cs, W.Oracle(ev, wp.rel_a, np.random.default_rng([30, 0, 100 + 10 * ti + P.POLICY_INDEX[pol], 2])), [W.context_dict(tier, x) for x in ev.rooms])
            assert tiny[0]["pol"][(tier, pol)]["minutes"][2] == r["minutes"] and tiny[0]["pol"][(tier, pol)]["checks"][2] == r["n_checks"]
    assert tiny[0]["n_compl"][2] == ev.n and tiny[0]["kind"][2] == ev.kind


def test_the_bootstrap_uses_the_frozen_seed_and_shape(tiny):
    a = J.analyze_cell(tiny[0], 60)
    for si, sub in enumerate(J.SUBSETS):
        idx = np.flatnonzero(J.subset_masks(tiny[0])[sub])
        if not len(idx):
            assert ("T2", "A", sub) not in a["cmp"]
            continue
        boot = np.random.default_rng([30, 0, 99, si]).integers(0, len(idx), (60, len(idx)))
        d = J.per_event(tiny[0], "T2", "tool_joint")["minutes"][idx] - J.per_event(tiny[0], "T2", "tool_ticket")["minutes"][idx]
        assert a["cmp"][("T2", "A", sub)]["ci_min"] == pytest.approx(J.S.paired_ci(d, boot))


def test_gate_one_also_catches_a_tiny_error(monkeypatch):
    orig = J.JointModel.group_stats

    def slightly_off(self, s, a):
        g = orig(self, s, a)
        g.W = g.W * np.array([1.0, 1.0 + 1e-6, 1.0])
        return g
    monkeypatch.setattr(J.JointModel, "group_stats", slightly_off)
    assert J.gate_g1(30)[0] is False


def test_the_prediction_boundaries_are_the_registered_ones():
    def with_edit(fn):
        return holds(fake_analyses(lambda c, sm, cm: (_all_hold(c, sm, cm), fn(c, sm, cm))))
    at = lambda key, val: (lambda c, sm, cm: cm.__setitem__(key, val) if c == PRIMARY else None)  # noqa: E731
    assert with_edit(at(("T2", "A", "shared"), _cmp(r_min=-0.15, d_min=-40.0)))["P1"] is True                                   # exactly 15% fewer: "at least"
    assert with_edit(lambda c, sm, cm: sm[("T2", "fast_parent", "all")].__setitem__("minutes", 95.0) if c == PRIMARY else None)["P6"] is True    # exactly 5% fewer: "at least"
    assert with_edit(lambda c, sm, cm: sm[("T3", "tool_ticket_nb", "single")].__setitem__("minutes", 105.0) if c == PRIMARY else None)["P8"] is True     # exactly 5% apart: within
    assert with_edit(lambda c, sm, cm: sm[("T2", "tool_joint_la2", "all")].__setitem__("minutes", 102.9) if c == J.Cell("rare", "M0", "R0") else None)["P7"] is True
