"""Guards for the sensitivity-map study (PREREGISTRATION_DR.md Addendum 19): the grid, the TRUE-accounting runners, the gates, the classification and map-reading rules."""
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot import model as M  # noqa: E402
from docmismatch.troubleshoot import sim  # noqa: E402
from docmismatch.troubleshoot import study as S  # noqa: E402
from docmismatch.troubleshoot.building import make_case  # noqa: E402

CELLS = S.all_cells()
DEFAULT_CELL = S.Cell(6, 0.15, 0.15, 0.25, "assumed", "assumed")


def truths(real, n, seed=0):
    rng = np.random.default_rng(seed)
    return [sim.sample_truth(real, rng) for _ in range(n)]


# ---------------------------------------------------------------------------------------------- the grid and the world
def test_grid_is_the_pre_registered_486_cells_in_order():
    assert len(CELLS) == 486 == 3 * 3 * 3 * 3 * 2 * 3
    assert CELLS[0] == S.Cell(3, 0.05, 0.05, 0.05, "assumed", "assumed") and CELLS[-1] == S.Cell(10, 0.30, 0.30, 1.0, "degraded", "trace_cheap")
    assert [c.costs for c in CELLS[:3]] == ["assumed", "access_x3", "trace_cheap"] and CELLS[3].rates == "degraded"          # the last factor varies fastest
    assert len(set(CELLS)) == 486
    assert [c.K for c in CELLS if c.assumptions_correct] == [3, 6, 10]
    assert sum(S.departure(c) == 0 for c in CELLS) == 3 * 2 * 3 and sum(S.departure(c) == 3 for c in CELLS) == 3 * 8 * 2 * 3


def test_synthetic_building_and_candidates():
    for K in S.LEVELS["K"]:
        real = make_case(S.make_building(K), S.MEMBER, "vav_zone", S.true_settings(replace(DEFAULT_CELL, K=K, near=0.05)), max_candidates=K)
        assert len(real.candidates) == K and real.candidates[0] == "VAV-0" == real.doc
        n_same = (K + 1) // 2
        assert [real.weights[c] for c in real.candidates] == [1.0] * n_same + [0.05] * (K - n_same)      # ceil(K/2) in the room's area, the rest elsewhere


def test_true_settings_change_only_what_the_cell_names():
    base = M.MENUS["vav_zone"]
    assert S.true_settings(DEFAULT_CELL).menu("vav_zone") == base and S.true_settings(DEFAULT_CELL).p_wrong == 0.15
    deg = {c.name: c for c in S.true_settings(replace(DEFAULT_CELL, rates="degraded")).menu("vav_zone")}
    for c in base:
        if c.name == "override_room":
            assert deg[c.name] == c                                                        # the measured check is untouched
        else:
            assert np.isclose(deg[c.name].tpr, max(c.tpr - 0.15, 0.55)) and np.isclose(deg[c.name].fpr, min(c.fpr + 0.10, 0.45))
            assert deg[c.name].access_min == c.access_min
    x3 = {c.name: c for c in S.true_settings(replace(DEFAULT_CELL, costs="access_x3")).menu("vav_zone")}
    assert all(x3[c.name].access_min == 3 * c.access_min and x3[c.name].do_min == c.do_min and x3[c.name].tpr == c.tpr for c in base)
    cheap = {c.name: c for c in S.true_settings(replace(DEFAULT_CELL, costs="trace_cheap")).menu("vav_zone")}
    assert (cheap["duct_trace"].access_min, cheap["duct_trace"].do_min) == (3, 5) and cheap["override_room"] == base[0]
    t = S.true_settings(replace(DEFAULT_CELL, p_wrong=0.30, p_act=0.05, near=1.0))
    assert (t.p_wrong, t.p_acts_fail, t.other_area_weight) == (0.30, 0.05, 1.0)
    assumed, real, _ = S.make_world(replace(DEFAULT_CELL, p_wrong=0.30, near=1.0, costs="access_x3"))
    assert assumed.settings == M.Settings() and real.settings.p_wrong == 0.30                # the tool's own assumptions never move


# ---------------------------------------------------------------------------------------------- G1 and G2
@pytest.mark.parametrize("strategy", S.TOOL)
def test_g1_runner_matches_sim_when_truth_equals_assumptions(strategy):
    assumed, real, tm = S.make_world(DEFAULT_CELL)
    for seed, truth in enumerate(truths(real, 30)):
        a = S.run_tool(assumed, truth, np.random.default_rng(seed), tm, strategy)
        b = sim.simulate(assumed, truth, strategy, np.random.default_rng(seed))
        assert (a["guess"], a["n_checks"], a["concluded"], a["correct"]) == (b["guess"], b["n_checks"], b["concluded"], b["correct"]) and np.isclose(a["minutes"], b["minutes"])


def test_g1_habit_a_matches_sim_habit():
    assumed, real, tm = S.make_world(DEFAULT_CELL)
    for seed, truth in enumerate(truths(real, 40, 1)):
        a = S.run_habit_A(assumed, truth, np.random.default_rng(seed), tm)
        b = sim.simulate_habit(assumed, truth, np.random.default_rng(seed))
        assert (a["guess"], a["n_checks"]) == (b["guess"], b["n_checks"]) and np.isclose(a["minutes"], b["minutes"])


@pytest.mark.parametrize("policy", S.POLICIES)
def test_g2_true_minutes_are_charged_and_never_change_choices(policy):
    assumed, real, tm1 = S.make_world(DEFAULT_CELL)
    _, _, tm3 = S.make_world(replace(DEFAULT_CELL, costs="access_x3"))
    for seed, truth in enumerate(truths(real, 20, 2)):
        a = S.RUNNERS[policy](assumed, truth, np.random.default_rng(seed), tm1)
        b = S.RUNNERS[policy](assumed, truth, np.random.default_rng(seed), tm3)
        assert a["sequence"] == b["sequence"] and a["guess"] == b["guess"]                    # the same checks in the same order with the same answers
        at, total = None, 0.0
        for name, target in b["sequence"]:
            total += tm3[name].minutes(at, target)
            at = target
        assert np.isclose(total, b["minutes"]) and b["minutes"] > a["minutes"]


def test_answers_come_from_the_true_hit_rates():
    assumed, _, _ = S.make_world(DEFAULT_CELL)
    coin = {c.name: replace(c, tpr=0.5, fpr=0.5) for c in M.MENUS["vav_zone"]}                 # every check is a coin flip in this world
    truth = ("wrong", "VAV-1")
    right = [S.run_habit_A(assumed, truth, np.random.default_rng(s), {c.name: c for c in M.MENUS["vav_zone"]})["correct"] for s in range(300)]
    flip = [S.run_habit_A(assumed, truth, np.random.default_rng(s), coin)["correct"] for s in range(300)]
    assert np.mean(right) > 0.75 > np.mean(flip) + 0.2


# ---------------------------------------------------------------------------------------------- the second habit
def test_habit_b_tries_the_trace_first_in_candidate_order():
    assumed, _, _ = S.make_world(DEFAULT_CELL)
    perfect = {c.name: replace(c, tpr=0.9999, fpr=0.0001) for c in M.MENUS["vav_zone"]}
    run = lambda truth: S.run_habit_B(assumed, truth, np.random.default_rng(0), perfect)  # noqa: E731
    r = run(("doc_acts_fail",))
    assert r["sequence"] == [("duct_trace", "VAV-0"), ("confirm_acts", "VAV-0")] and r["correct"]
    r = run(("doc_other",))
    assert r["sequence"] == [("duct_trace", "VAV-0"), ("confirm_acts", "VAV-0")] and r["correct"]
    r = run(("wrong", "VAV-1"))
    assert r["sequence"] == [("duct_trace", "VAV-0"), ("duct_trace", "VAV-1")] and r["correct"]
    assert run(("wrong", "VAV-5"))["n_checks"] == 6 and run(("wrong", "VAV-5"))["correct"]
    r = run(("unlisted",))
    assert r["n_checks"] == 6 and r["correct"] and all(name == "duct_trace" for name, _ in r["sequence"])


# ---------------------------------------------------------------------------------------------- classification and map reading
def test_classification_rules():
    c = S.classify_pair
    assert c(50, 100, 0.9, 0.9, (-60, -40)) == ("WINS", False)
    assert c(50, 100, 0.9, 0.9, (-60, 5)) == ("NEITHER", False)                            # the interval touches zero
    assert c(95, 100, 0.9, 0.9, (-8, -2)) == ("NEITHER", False)                            # only 5% faster
    assert c(90, 100, 0.5, 0.5, (-15, -5)) == ("WINS", False)                              # exactly 10% faster counts
    assert c(85, 100, 0.85, 0.90, (-20, -10)) == ("NEITHER", True)                         # faster but less accurate: a trade-off, not a win
    assert c(120, 100, 0.9, 0.9, (10, 30)) == ("LOSES", False)
    assert c(120, 100, 0.95, 0.90, (10, 30)) == ("NEITHER", False)                         # slower but more accurate
    assert c(120, 100, 0.9, 0.9, (-5, 30)) == ("NEITHER", False)
    assert S.combine(["WINS", "WINS"]) == "WINS" and S.combine(["WINS", "NEITHER"]) == "NEITHER"
    assert S.combine(["WINS", "LOSES"]) == "LOSES" and S.combine(["NEITHER", "LOSES"]) == "LOSES"


def test_map_reading_thresholds():
    assert S.map_reading(0.60, 0.10) == "HELPS BROADLY" and S.map_reading(0.60, 0.11) == "HELPS IN PART"
    assert S.map_reading(0.19, 0.0) == "DOES NOT HELP" and S.map_reading(0.30, 0.26) == "DOES NOT HELP"
    assert S.map_reading(0.20, 0.25) == "HELPS IN PART" and S.map_reading(0.5, 0.2) == "HELPS IN PART"
    assert S.map_fractions(["WINS", "LOSES", "NEITHER", "WINS"]) == (0.5, 0.25) and S.map_fractions([]) == (0.0, 0.0)


def test_marginals_and_predictions_on_constructed_labels():
    win_if = lambda f: ["WINS" if f(c) else "NEITHER" for c in CELLS]  # noqa: E731
    lab = win_if(lambda c: c.K == 10)
    m = S.marginals(CELLS, lab, "K")
    assert m == {3: (0.0, 0.0, 162), 6: (0.0, 0.0, 162), 10: (1.0, 0.0, 162)}
    p = S.predictions(CELLS, {"entropy": lab, "split_half": lab})
    assert p["P1"]["holds"] and p["P1"]["values"] == (1.0, 0.0) and not p["P2"]["holds"] and not p["P3"]["holds"] and not p["P4"]["holds"]
    p = S.predictions(CELLS, {"entropy": win_if(lambda c: c.p_wrong == 0.30), "split_half": win_if(lambda c: False)})
    assert p["P2"]["holds"] and not p["P1"]["holds"]
    p = S.predictions(CELLS, {"entropy": win_if(lambda c: c.costs == "access_x3"), "split_half": win_if(lambda c: c.rates == "degraded")})
    assert p["P4"]["holds"] and p["P5"]["holds"] and p["P5"]["values"][0] == 1.0 and np.isclose(p["P5"]["values"][1], 1 / 3)      # entropy still wins in a third of the degraded cells
    p = S.predictions(CELLS, {"entropy": win_if(lambda c: S.departure(c) == 0), "split_half": win_if(lambda c: True)})
    assert p["P3"]["holds"] and p["P3"]["values"] == (-1.0, 0.0)                              # entropy falls behind as the truth departs from the tool's prior


def test_paired_bootstrap_interval():
    idx = np.random.default_rng(0).integers(0, 50, (200, 50))
    assert S.paired_ci(np.full(50, -5.0), idx) == (-5.0, -5.0)
    lo, hi = S.paired_ci(np.random.default_rng(1).normal(0, 1, 50), idx)
    assert lo < 0 < hi and S.paired_ci(np.random.default_rng(1).normal(0, 1, 50), idx) == (lo, hi)


# ---------------------------------------------------------------------------------------------- one cell, G3, G4, G5
def test_run_cell_pairs_truths_and_is_reproducible():
    r1, r2 = S.run_cell(0, CELLS[0], n=25), S.run_cell(0, CELLS[0], n=25)
    ref = r1["policy"]["entropy"]["truth_idx"]
    for name in S.POLICIES:
        p = r1["policy"][name]
        assert len(p["minutes"]) == 25 and np.array_equal(p["truth_idx"], ref)             # every policy meets the same 25 truths
        assert all(np.array_equal(p[k], r2["policy"][name][k]) for k in ("minutes", "checks", "concluded", "correct", "guess_idx"))       # G4
    s = S.summarize(r1)
    assert np.isclose(s["entropy"]["entries"], 1 + s["entropy"]["checks"]) and np.isclose(s["habit_A"]["unresolved"], 0.0)
    assert np.isclose(s["entropy"]["unresolved"], 1 - s["entropy"]["concluded"])
    assert S.run_cell(1, CELLS[0], n=25)["policy"]["entropy"]["truth_idx"].tolist() != ref.tolist()          # the seed depends on the cell index


def test_g5_completeness_and_pairing():
    r = S.run_cell(0, CELLS[0], n=10)
    assert S.g5_complete([r], n_cells=1) == (True, "ok")
    assert not S.g5_complete([r], n_cells=2)[0]
    r5 = S.run_cell(5, CELLS[5], n=10)
    assert S.g5_complete([r5], expected_idx=[5]) == (True, "ok") and not S.g5_complete([r5], expected_idx=[4])[0]      # a smoke run names its own cells
    bad = S.run_cell(0, CELLS[0], n=10)
    bad["policy"]["habit_B"]["minutes"][3] = np.nan
    assert not S.g5_complete([bad], n_cells=1)[0]
    bad = S.run_cell(0, CELLS[0], n=10)
    bad["policy"]["random"]["truth_idx"][0] = (bad["policy"]["random"]["truth_idx"][0] + 1) % 5
    assert "truths differ" in S.g5_complete([bad], n_cells=1)[1]
    del bad["policy"]["habit_A"]
    assert not S.g5_complete([bad], n_cells=1)[0]


def test_g3_honesty_in_the_assumptions_correct_cells():
    results = [S.run_cell(i, c) for i, c in enumerate(CELLS) if c.assumptions_correct]
    ok, vals = S.g3_honesty(results)
    assert ok and set(vals) == {3, 6, 10} and all(v >= 0.92 for v in vals.values())        # the stopping rule is 0.95 and the belief is exact here
    assert all(r["policy"]["entropy"]["concluded"].mean() > 0.5 for r in results)
    p = results[1]["policy"]["entropy"]
    broken = dict(results[1], policy={**results[1]["policy"], "entropy": {**p, "correct": np.zeros_like(p["correct"])}})
    assert not S.g3_honesty([broken])[0]                                                   # a tool that is often wrong when confident fails the gate
    none = dict(results[1], policy={**results[1]["policy"], "entropy": {**p, "concluded": np.zeros_like(p["concluded"])}})
    assert not S.g3_honesty([none])[0]
    assert not S.g3_honesty([S.run_cell(0, CELLS[0], n=10)])[0]                            # no assumptions-correct cell present


def test_analysis_of_a_cell_is_consistent_with_its_raw_arrays():
    r = S.run_cell(0, CELLS[0], n=60)
    a = S.analyze_cell(r, B=50)
    assert set(a["label"]) == set(S.TOOL) and all(v in ("WINS", "LOSES", "NEITHER") for v in a["label"].values())
    assert len(a["cmp"]) == len(S.TOOL) * len(S.HABITS)
    c = a["cmp"]["entropy|habit_A"]
    assert np.isclose(c["d_min"], a["summary"]["entropy"]["minutes"] - a["summary"]["habit_A"]["minutes"])
    assert np.isclose(c["r_min"], c["d_min"] / a["summary"]["habit_A"]["minutes"]) and c["ci_min"][0] <= c["d_min"] <= c["ci_min"][1]
    again = S.analyze_cell(r, B=50)
    assert again["cmp"] == a["cmp"]
    both = [a["cmp"][f"entropy|{h}"]["label"] for h in S.HABITS]
    assert a["label"]["entropy"] == S.combine(both)


def test_parallel_cells_match_serial():
    jobs = [(i, CELLS[i]) for i in (0, 100, 485)]
    serial = S.compute_cells(jobs, n=12, workers=1)
    par = S.compute_cells(jobs, n=12, workers=2)
    for a, b in zip(serial, par):
        assert a["idx"] == b["idx"] and a["cell"] == b["cell"]
        for name in S.POLICIES:
            assert all(np.array_equal(a["policy"][name][k], b["policy"][name][k]) for k in ("minutes", "checks", "correct", "truth_idx"))
