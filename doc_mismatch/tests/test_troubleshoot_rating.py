"""Guards for the drawings-rating study (PREREGISTRATION_DR.md Addendum 21): worlds and cells, the frozen labels, scenario readings, break-even arithmetic, predictions, gates, and the runner."""
import sys
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
from docmismatch.troubleshoot import study_rating as SG  # noqa: E402

DATA = ROOT.parent / "data_cache"
HAVE_DATA = (DATA / "mortar__bldg8.ttl").exists()
PRIMARY_KEYS = [(w, r) for w in SG.PRIMARY for r in SG.RATINGS]


def fake_layout():
    """AHU-A feeds V1-V3, AHU-B feeds V4-V5, V6 has no handler; Z1..Z6 <- V1..V6."""
    kinds = {f"V{i}": "VAV" for i in range(1, 7)} | {f"Z{i}": "Zone" for i in range(1, 7)} | {"AHU-A": "AHU", "AHU-B": "AHU"}
    vz = [(f"V{i}", f"Z{i}") for i in range(1, 7)]
    av = [("AHU-A", f"V{i}") for i in (1, 2, 3)] + [("AHU-B", "V4"), ("AHU-B", "V5")]
    return R.layout_from_census(C.BrickCensus("b1", kinds, {}, {"vav_zone": vz, "ahu_vav": av, "coil_vav": [], "coil_ahu": []}))[0]


# ---------------------------------------------------------------------------------------------- worlds and cells
def test_worlds_ratings_and_cell_order():
    assert list(SG.WORLDS) == ["p05", "p10", "p15", "p22", "p30"] and [c.p_wrong for c in SG.WORLDS.values()] == [0.05, 0.10, 0.15, 0.22, 0.30]
    assert all((c.p_act, c.near, c.rates, c.costs) == (0.15, 0.25, "assumed", "assumed") for c in SG.WORLDS.values())     # only the prior varies
    assert SG.RATINGS == ("mostly_right", "mixed", "poor") and SG.BASE == "mixed" and SG.MATCHED == {"p05": "mostly_right", "p15": "mixed", "p30": "poor"}
    assert [M.DRAWINGS[SG.MATCHED[w]] for w in SG.PRIMARY] == [SG.WORLDS[w].p_wrong for w in SG.PRIMARY]                  # 'matched' really matches
    cells = SG.all_rating_cells(list(R.FROZEN_BUILDINGS))
    assert len(cells) == 250 and cells[0] == SG.RatingCell("p05", "R_narrow", "bldg2") and cells[24] == SG.RatingCell("p05", "R_narrow", "bldg44")
    assert cells[25] == SG.RatingCell("p05", "R_wide", "bldg2") and cells[50] == SG.RatingCell("p10", "R_narrow", "bldg2") and cells[-1] == SG.RatingCell("p30", "R_wide", "bldg44")
    assert SG.POLICIES == ("entropy@mostly_right", "entropy@mixed", "entropy@poor", "habit_A", "habit_B")
    assert set(SG.SCENARIOS.values()) <= set(PRIMARY_KEYS) and set(SG.MATCHED_SCENARIOS) == {"S1", "S2"} and all(SG.SCENARIOS[s][1] == SG.MATCHED[SG.SCENARIOS[s][0]] for s in SG.MATCHED_SCENARIOS)


def test_assumed_case_carries_the_rating_and_the_real_case_the_world():
    b = fake_layout()
    for r in SG.RATINGS:
        assert SG.assumed_case(b, "Z1", "R_narrow", r).settings.p_wrong == M.DRAWINGS[r]
    assert SG.real_case(b, "Z1", "p30", "R_wide").settings.p_wrong == 0.30
    assert SG.assumed_case(b, "Z1", "R_narrow", "poor").candidates == SG.assumed_case(b, "Z1", "R_narrow", "mostly_right").candidates          # only the prior differs


# ---------------------------------------------------------------------------------------------- frozen labels
@pytest.mark.parametrize("r_min,ci,expected", [(-0.05, (-9.0, -1.0), "FASTER"), (-0.049, (-9.0, -1.0), "SAME"), (-0.20, (-9.0, 0.0), "SAME"), (-0.20, (-9.0, 0.5), "SAME"),
                                               (0.05, (1.0, 9.0), "SLOWER"), (0.30, (0.0, 9.0), "SAME"), (0.0, (-1.0, 1.0), "SAME")])
def test_time_state(r_min, ci, expected):
    assert SG.time_state(r_min, ci) == expected


@pytest.mark.parametrize("d,ci,expected", [(0.02, (0.001, 0.04), "MORE"), (0.019, (0.001, 0.04), "SAME"), (0.05, (0.0, 0.1), "SAME"), (-0.02, (-0.04, -0.001), "LESS"),
                                           (-0.03, (-0.06, 0.0), "SAME"), (0.0, (-0.01, 0.01), "SAME")])
def test_accuracy_state(d, ci, expected):
    assert SG.acc_state(d, ci) == expected


def test_label_truth_table():
    table = {("FASTER", "SAME"): "IMPROVES", ("FASTER", "MORE"): "IMPROVES", ("SAME", "MORE"): "IMPROVES", ("SLOWER", "SAME"): "WORSE", ("SLOWER", "LESS"): "WORSE", ("SAME", "LESS"): "WORSE",
             ("FASTER", "LESS"): "TRADE", ("SLOWER", "MORE"): "TRADE", ("SAME", "SAME"): "NEITHER"}
    assert len(table) == 9
    for (t, a), want in table.items():
        assert SG.label(t, a) == want, (t, a)


@pytest.mark.parametrize("d,ci,expected", [(0.02, (0.001, 0.05), "REGRESSION"), (0.02, (0.0, 0.05), "NONE"), (0.019, (0.001, 0.05), "NONE"), (-0.02, (-0.05, -0.001), "GAIN"),
                                           (-0.02, (-0.05, 0.0), "NONE"), (0.0, (-0.01, 0.01), "NONE")])
def test_safety_flag(d, ci, expected):
    assert SG.safety_flag(d, ci) == expected


# ---------------------------------------------------------------------------------------------- the runner and the analysis
def run(world="p30", regime="R_narrow", n=40, idx=7):
    return SG.run_rating_cell(idx, SG.RatingCell(world, regime, "b1"), fake_layout(), n=n)


def test_runner_shapes_pairing_and_determinism():
    r = run()
    assert set(r["policy"]) == set(SG.POLICIES) and r["n"] == 40 and len(r["K"]) == 40
    ref = r["policy"][SG.POLICIES[0]]["truth_idx"]
    for name, p in r["policy"].items():
        assert np.array_equal(p["truth_idx"], ref) and np.isfinite(p["minutes"]).all() and len(p["minutes"]) == 40
        assert p["guess_idx"].min() >= 0 and (p["correct"] == (p["guess_idx"] == p["truth_idx"])).all()
    again = run()
    assert all(np.array_equal(r["policy"][p][k], again["policy"][p][k]) for p in SG.POLICIES for k in ("minutes", "guess_idx", "checks"))
    assert SG.g5_complete_rating([r], n_cells=1, expected_idx=[7])[0]


def test_episodes_are_a_prefix_of_longer_runs():
    small, big = run(n=10), run(n=25)
    assert all(np.array_equal(small["policy"][p][k], big["policy"][p][k][:10]) for p in SG.POLICIES for k in ("minutes", "checks", "guess_idx", "truth_idx", "concluded"))


def test_the_rating_changes_the_tool_and_only_the_tool():
    r = run(world="p30", n=200)
    mr, mx, po = (r["policy"][SG.tool_name(x)] for x in SG.RATINGS)
    assert not (np.array_equal(mr["minutes"], po["minutes"]) and np.array_equal(mr["guess_idx"], po["guess_idx"]))          # different priors act differently
    assert np.array_equal(mx["truth_idx"], mr["truth_idx"])                                                                    # ...on the same episodes
    assert SG.gate_habits_independent(fake_layout())[0]                                                                       # the habits never read the rating


def test_the_three_ratings_share_their_random_draws(monkeypatch):
    monkeypatch.setitem(M.DRAWINGS, "mostly_right", 0.15)                                                                      # two ratings with the same prior...
    r = run(world="p30", n=60)
    a, b = r["policy"]["entropy@mostly_right"], r["policy"]["entropy@mixed"]
    assert all(np.array_equal(a[k], b[k]) for k in ("minutes", "guess_idx", "checks", "concluded"))                            # ...must give identical episodes (common random numbers)
    assert not all(np.array_equal(r["policy"]["entropy@poor"][k], b[k]) for k in ("minutes", "guess_idx", "checks"))            # while a different prior does not


def test_default_rating_reproduces_the_tool_as_it_was(monkeypatch):
    b = fake_layout()
    assert SG.gate_g1_default_off(b)[0]
    monkeypatch.setitem(M.DRAWINGS, "mixed", 0.20)                                                                            # a broken default is caught
    ok, msg = SG.gate_g1_default_off(b)
    assert not ok and "with_drawings" in msg


def test_habit_independence_gate_catches_a_habit_that_reads_the_prior(monkeypatch):
    b = fake_layout()
    original = S.run_habit_B

    def sneaky(case, truth, rng, true_menu):
        out = original(case, truth, rng, true_menu)
        if case.settings.p_wrong > 0.2:
            out["minutes"] += 1.0
        return out

    monkeypatch.setitem(S.RUNNERS, "habit_B", sneaky)
    assert not SG.gate_habits_independent(b)[0]


def fake_result(n=300, seed=0, base=100.0, shifts=None):
    """Cell result with five policies whose minutes and correctness are set by hand: `shifts[rating] = (minutes factor, accuracy)`; the habits and unlisted ratings use (1.0, 0.9).
    Every policy shares the same random numbers, so a difference is exactly the shift (paired)."""
    rng = np.random.default_rng(seed)
    shifts = shifts or {}
    truth = rng.integers(0, 4, n)
    u, v = rng.random(n), rng.random(n)
    pol = {}
    for name in SG.POLICIES:
        f, acc = shifts.get(name.split("@")[1] if "@" in name else "", (1.0, 0.9))
        correct = v < acc
        pol[name] = dict(truth_idx=truth, guess_idx=np.where(correct, truth, (truth + 1) % 4), minutes=base * f * (0.9 + 0.2 * u), checks=np.full(n, 3.0), concluded=np.ones(n, bool), correct=correct)
    return dict(idx=3, cell=SG.RatingCell("p15", "R_narrow", "b1"), n=n, policy=pol)


def test_analysis_labels_hand_built_differences():
    same = SG.analyze_rating_cell(fake_result(), B=200)
    for r in ("mostly_right", "poor"):
        c = same["cmp"][r]
        assert c["label"] == "NEITHER" and c["d_min"] == 0 and c["d_acc"] == 0 and c["d_wc"] == 0 and c["safety"] == "NONE"
    fast = SG.analyze_rating_cell(fake_result(shifts={"mostly_right": (0.7, 0.9)}), B=200)["cmp"]["mostly_right"]
    assert fast["label"] == "IMPROVES" and fast["time"] == "FASTER" and fast["r_min"] < -0.25 and fast["d_min"] < 0
    trade = SG.analyze_rating_cell(fake_result(shifts={"mostly_right": (0.7, 0.75)}), B=300)["cmp"]["mostly_right"]
    assert trade["label"] == "TRADE" and trade["time"] == "FASTER" and trade["acc"] == "LESS"
    slow = SG.analyze_rating_cell(fake_result(shifts={"poor": (1.4, 0.9)}), B=200)["cmp"]["poor"]
    assert slow["label"] == "WORSE" and slow["time"] == "SLOWER"
    acc = SG.analyze_rating_cell(fake_result(shifts={"poor": (1.0, 0.99)}), B=300)["cmp"]["poor"]
    assert acc["label"] == "IMPROVES" and acc["acc"] == "MORE" and acc["d_acc"] > 0.05


def test_analysis_context_labels_against_the_habits():
    a = SG.analyze_rating_cell(fake_result(), B=100)
    assert set(a["ctx"]) >= {f"{r}|{h}" for r in SG.RATINGS for h in SG.HABITS} | set(SG.RATINGS)
    assert all(a["ctx"][r] in ("WINS", "LOSES", "NEITHER") for r in SG.RATINGS) and a["ctx"]["mixed|habit_A"]["secondary"] in ("WINS", "LOSES", "NEITHER", "BUYS ACCURACY")


# ---------------------------------------------------------------------------------------------- scenarios, break-even, predictions
def fake_cell(world, regime, building, per_rating):
    """An analysis with hand-set paired results: per_rating[rating] = dict(d_min, d_acc, d_wc, label, safety)."""
    cmp_ = {}
    for r in SG.RATINGS:
        if r != SG.BASE:
            d = dict(d_min=0.0, d_acc=0.0, d_wc=0.0, d_checks=0.0, label="NEITHER", safety="NONE") | per_rating.get(r, {})
            cmp_[r] = d
    return dict(idx=0, cell=SG.RatingCell(world, regime, building), cmp=cmp_, summary={SG.tool_name(SG.BASE): dict(minutes=100.0)})


def fake_analyses(spec, buildings=("a", "b", "c", "d")):
    """spec[(world, rating, regime or None)] -> dict for that scenario's cells."""
    out = []
    for w in SG.WORLDS:
        for reg in SG.REGIMES:
            for b in buildings:
                per = {}
                for r in SG.RATINGS:
                    per[r] = spec.get((w, r, reg), spec.get((w, r, None), {}))
                out.append(fake_cell(w, reg, b, per))
    return out


def test_fractions_and_readings():
    cells = [fake_cell("p05", "R_narrow", str(i), {"mostly_right": dict(label=lab, safety=sf)}) for i, (lab, sf) in enumerate(
        [("IMPROVES", "NONE")] * 6 + [("WORSE", "NONE")] + [("TRADE", "NONE")] + [("NEITHER", "REGRESSION")] + [("NEITHER", "GAIN")])]
    fr = SG.fractions(cells, "mostly_right")
    assert fr["IMPROVES"] == 0.6 and fr["WORSE"] == 0.1 and fr["TRADE"] == 0.1 and fr["NEITHER"] == 0.2
    assert fr["SAFETY_REGRESSION"] == 0.1 and fr["SAFETY_GAIN"] == 0.1 and np.isclose(fr["COST"], 0.3)                     # WORSE + TRADE + the regression
    assert SG.matched_reading(fr) == "HELPS BROADLY" and SG.matched_reading(dict(fr, IMPROVES=0.59)) == "HELPS IN PART" and SG.matched_reading(dict(fr, IMPROVES=0.19)) == "DOES NOT HELP"
    assert SG.matched_reading(dict(fr, WORSE=0.26)) == "DOES NOT HELP" and SG.matched_reading(dict(fr, IMPROVES=0.9, WORSE=0.11)) == "HELPS IN PART"
    assert SG.harm_reading(dict(fr, COST=0.10)) == "HARMLESS" and SG.harm_reading(dict(fr, COST=0.11)) == "COSTS SOMETHING" and SG.harm_reading(dict(fr, COST=0.26)) == "HARMFUL"
    assert SG.harm_reading(dict(fr, COST=0.25)) == "COSTS SOMETHING"


def test_mean_delta_and_the_default_rating_is_zero():
    cells = [fake_cell("p30", "R_wide", str(i), {"poor": dict(d_min=-2.0 * (i + 1), d_acc=0.01 * i, d_wc=-0.01)}) for i in range(4)]
    d = SG.mean_delta(cells, "poor")
    assert np.isclose(d["d_min"], -5.0) and np.isclose(d["d_acc"], 0.015) and np.isclose(d["d_wc"], -0.01)
    assert SG.mean_delta(cells, SG.BASE) == {k: 0.0 for k in SG.METRICS}


def hand_delta():
    """d_min only: p05 (mostly_right -10, poor +20), p15 (mostly_right +6, poor +9), p30 (mostly_right +30, poor -4); the default rating is 0 everywhere."""
    z = {k: 0.0 for k in SG.METRICS}
    d = {(w, r): dict(z) for w in SG.PRIMARY for r in SG.RATINGS}
    d[("p05", "mostly_right")]["d_min"], d[("p05", "poor")]["d_min"] = -10.0, 20.0
    d[("p15", "mostly_right")]["d_min"], d[("p15", "poor")]["d_min"] = 6.0, 9.0
    d[("p30", "mostly_right")]["d_min"], d[("p30", "poor")]["d_min"] = 30.0, -4.0
    return d


def test_expected_change_against_a_hand_calculation():
    d = hand_delta()
    for q in (1 / 3, 0.5, 0.7, 1.0):
        assert np.isclose(SG.expected_change(d, q)["d_min"], (32.5 - 46.5 * q) / 3)                                            # worked by hand: (10-20q + 7.5(1-q) + 15-19q) / 3
    assert np.isclose(SG.expected_change(d, 1.0)["d_min"], (-10 + 0 - 4) / 3)                                                  # a perfect rating: the mean of the matched deltas
    assert SG.expected_change(d, 0.7)["d_acc"] == 0.0


def test_break_even_and_the_favourable_range():
    d = hand_delta()
    b = SG.break_even(d, "d_min")
    assert b["q_star"] == 0.70 and b["q_max"] == 1.0 and b["at_one"]                                                            # 32.5 / 46.5 = 0.6989
    assert SG.break_even(d)["q_star"] == 0.70                                                                                   # only minutes move, so the joint answer is minutes'
    assert SG.break_even(d, "d_acc")["q_star"] == 1 / 3                                                                        # accuracy never moves: favourable from the start
    for w in SG.PRIMARY:                                                                                                       # a technician who only ever mis-rates: no q is favourable
        for r in SG.RATINGS:
            d[(w, r)]["d_min"] = 5.0 if r != SG.MATCHED[w] else 1.0
    none = SG.break_even(d, "d_min")
    assert none == dict(q_star=None, q_max=None, at_one=False)
    e = hand_delta()
    e[("p30", "poor")]["d_wc"] = 0.5                                                                                             # the perfect rating hurts safety: not favourable at q = 1
    assert not SG.break_even(e)["at_one"]


def test_decision_rule():
    ok = {"S1": "HELPS BROADLY", "S2": "HELPS IN PART"}
    be = {reg: dict(q_star=0.7, q_max=1.0, at_one=True) for reg in SG.REGIMES}
    assert SG.decision(ok, be) == "WORTH OFFERING"
    assert SG.decision(dict(ok, S2="DOES NOT HELP"), be) == "NOT WORTH OFFERING AS BUILT"
    assert SG.decision(ok, dict(be, R_wide=dict(q_star=0.76, q_max=1.0, at_one=True))) == "NOT WORTH OFFERING AS BUILT"
    assert SG.decision(ok, dict(be, R_wide=dict(q_star=None, q_max=None, at_one=False))) == "NOT WORTH OFFERING AS BUILT"
    assert SG.decision(ok, dict(be, R_narrow=dict(q_star=0.5, q_max=0.9, at_one=False))) == "NOT WORTH OFFERING AS BUILT"


GOOD = {("p05", "mostly_right", None): dict(d_min=-5.0, d_acc=0.0), ("p30", "poor", None): dict(d_wc=-0.03, d_acc=0.01), ("p30", "mostly_right", None): dict(d_wc=0.05),
        ("p05", "poor", None): dict(d_min=8.0)}


def test_predictions_hold_and_fail_one_at_a_time():
    pr = SG.rating_predictions(fake_analyses(GOOD))
    assert all(v["holds"] for v in pr.values()) and set(pr) == {"P1", "P2", "P3", "P4", "P5"}
    cases = {"P1": {("p05", "mostly_right", "R_wide"): dict(d_min=1.0, d_acc=0.0)}, "P2": {("p30", "poor", "R_narrow"): dict(d_wc=0.0, d_acc=0.01)}, "P3": {("p30", "mostly_right", "R_wide"): dict(d_wc=0.019)},
             "P4": {("p05", "poor", "R_narrow"): dict(d_min=-1.0)}, "P1b": {("p05", "mostly_right", None): dict(d_min=-5.0, d_acc=-0.02)}}
    for name, override in cases.items():
        got = SG.rating_predictions(fake_analyses(GOOD | override))
        assert not got[name[:2]]["holds"], name
    p5 = SG.rating_predictions(fake_analyses(GOOD | {("p30", "mostly_right", None): dict(d_wc=0.5)}))                          # over-sure ratings cost too much safety at q = 0.7
    assert not p5["P5"]["holds"] and p5["P3"]["holds"]


def test_predictions_read_the_scenarios_they_name():
    spec = {("p15", "mostly_right", None): dict(d_min=-99.0), ("p10", "mostly_right", None): dict(d_min=-99.0)}                   # S3 and a secondary world must not leak into S1
    pr = SG.rating_predictions(fake_analyses(GOOD | spec))
    assert pr["P1"]["values"]["R_narrow"][0] == -5.0


# ---------------------------------------------------------------------------------------------- gates
def test_honesty_gate_reads_the_matched_rating():
    def res(world, regime, acc_by_rating):
        pol = {}
        for name in SG.POLICIES:
            acc = acc_by_rating.get(name.split("@")[1] if "@" in name else "", 0.5)
            n = 100
            c = np.arange(n) < int(acc * n)
            pol[name] = dict(concluded=np.ones(n, bool), correct=c, minutes=np.ones(n), truth_idx=np.zeros(n, int), guess_idx=np.zeros(n, int), checks=np.ones(n))
        return dict(cell=SG.RatingCell(world, regime, "b"), policy=pol, n=100, idx=0)

    good = [res(w, r, {SG.MATCHED[w]: 0.96}) for w in SG.PRIMARY for r in SG.REGIMES]
    ok, vals = SG.g3_honesty_rating(good)
    assert ok and len(vals) == 6 and all(np.isclose(v, 0.96) for v in vals.values())
    bad = [res(w, r, {SG.MATCHED[w]: 0.96}) for w in SG.PRIMARY for r in SG.REGIMES if (w, r) != ("p30", "R_wide")] + [res("p30", "R_wide", {"poor": 0.90, "mixed": 0.99})]
    assert not SG.g3_honesty_rating(bad)[0]                                                                                    # only the matched rating counts, and every group must pass
    assert not SG.g3_honesty_rating([])[0]


def test_completeness_gate():
    r = run(n=12, idx=0)
    assert SG.g5_complete_rating([r], n_cells=1)[0]
    assert not SG.g5_complete_rating([r], n_cells=2)[0] and not SG.g5_complete_rating([], n_cells=1)[0]
    broken = run(n=12, idx=0)
    broken["policy"]["habit_A"]["minutes"] = broken["policy"]["habit_A"]["minutes"].copy()
    broken["policy"]["habit_A"]["minutes"][0] = np.nan
    assert not SG.g5_complete_rating([broken], n_cells=1)[0]
    swapped = run(n=12, idx=0)
    swapped["policy"]["entropy@poor"]["truth_idx"] = (swapped["policy"]["entropy@poor"]["truth_idx"] + 1) % 5
    assert not SG.g5_complete_rating([swapped], n_cells=1)[0]
    missing = run(n=12, idx=0)
    del missing["policy"]["habit_B"]
    assert not SG.g5_complete_rating([missing], n_cells=1)[0]


# ---------------------------------------------------------------------------------------------- real data
@pytest.mark.skipif(not HAVE_DATA, reason="Mortar Brick files not cached")
def test_runs_on_a_real_layout_and_is_paired_and_finite():
    b, _ = R.load_layout(DATA / "mortar__bldg8.ttl", "bldg8")
    res = SG.run_rating_cell(0, SG.RatingCell("p15", "R_wide", "bldg8"), b, n=8)
    assert SG.g5_complete_rating([res], n_cells=1)[0] and SG.gate_g1_default_off(b)[0] and SG.gate_habits_independent(b)[0]
    a = SG.analyze_rating_cell(res, B=50)
    assert set(a["cmp"]) == {"mostly_right", "poor"}
