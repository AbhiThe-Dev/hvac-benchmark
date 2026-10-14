"""Guards for the minimum-data study (PREREGISTRATION_DR.md Addendum 23): the two levels of information, drawing the truth over the whole building, the off-list mapping, the runner, the analysis,
predictions and gates."""
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
from docmismatch.troubleshoot import study_minimum as SM  # noqa: E402
from docmismatch.troubleshoot.building import make_case  # noqa: E402

DATA = ROOT.parent / "data_cache"
HAVE_DATA = (DATA / "mortar__bldg8.ttl").exists()


def fake_layout(n=20, per=5):
    """`n` boxes V01.. on n/per air handlers (AHU-A feeds V01-V05, AHU-B V06-V10, ...); zone Zi <- Vi."""
    ids = [f"{i:02d}" for i in range(1, n + 1)]
    kinds = {f"V{i}": "VAV" for i in ids} | {f"Z{i}": "Zone" for i in ids} | {f"AHU-{chr(65 + h)}": "AHU" for h in range((n + per - 1) // per)}
    vz = [(f"V{i}", f"Z{i}") for i in ids]
    av = [(f"AHU-{chr(65 + k // per)}", f"V{i}") for k, i in enumerate(ids)]
    return R.layout_from_census(C.BrickCensus("b1", kinds, {}, {"vav_zone": vz, "ahu_vav": av, "coil_vav": [], "coil_ahu": []}))[0]


# ---------------------------------------------------------------------------------------------- cells, worlds, levels
def test_cells_worlds_and_policies():
    cells = SM.all_min_cells(list(R.FROZEN_BUILDINGS))
    assert len(cells) == 100 and cells[0] == SM.MinCell("local", "K8", "bldg2") and cells[24] == SM.MinCell("local", "K8", "bldg44") and cells[25] == SM.MinCell("local", "K40", "bldg2")
    assert cells[50] == SM.MinCell("anywhere", "K8", "bldg2") and cells[-1] == SM.MinCell("anywhere", "K40", "bldg44") and len(set(cells)) == 100
    assert SM.CAPS == {"K8": 8, "K40": 40} and SM.WORLD_NEAR == {"local": 0.25, "anywhere": 1.0}
    assert SM.POLICIES == ("entropy@min", "entropy@grouped", "habit_A@min", "habit_A@grouped", "habit_B@min", "habit_B@grouped") and SM.STREAM == {"entropy": 0, "habit_A": 1, "habit_B": 2}
    assert SM.world_cell("local") == S.Cell(0, 0.15, 0.15, 0.25, "assumed", "assumed") and SM.world_cell("anywhere") == S.Cell(0, 0.15, 0.15, 1.0, "assumed", "assumed")
    assert S.true_settings(SM.world_cell("anywhere")).other_area_weight == 1.0 and S.true_settings(SM.world_cell("local")).other_area_weight == 0.25


def test_the_two_levels_of_information():
    b = fake_layout()
    flat = SM.strip_areas(b)
    assert all(e.area is None for e in flat.equipment.values()) and all(e.area is not None for e in b.equipment.values() if e.kind in ("VAV", "Zone"))          # the original is untouched
    assert flat.claims == b.claims and flat.claims is not b.claims and set(flat.equipment) == set(b.equipment)
    m, g = SM.assumed_case(b, "Z07", "K8", "min"), SM.assumed_case(b, "Z07", "K8", "grouped")
    assert m.candidates == ["V07", "V01", "V02", "V03", "V04", "V05", "V06", "V08"] and set(m.weights.values()) == {1.0}                                                 # identifier order, all equal
    assert g.candidates == ["V07", "V06", "V08", "V09", "V10", "V01", "V02", "V03"] and [g.weights[c] for c in g.candidates] == [1, 1, 1, 1, 1, 0.25, 0.25, 0.25]      # same handler first
    assert m.settings == g.settings == M.Settings()                                                                                                                       # the tool's own assumptions never change
    assert len(SM.assumed_case(b, "Z07", "K40", "min").candidates) == 20 and SM.n_boxes(b) == 20
    with pytest.raises(ValueError):
        SM.level_layout(b, "everything")


# ---------------------------------------------------------------------------------------------- the truth over the whole building
def test_truth_is_drawn_over_every_box_and_locality_follows_the_world():
    b = fake_layout()
    local = SM.draw_picks(1, SM.MinCell("local", "K8", "b1"), b, 4000)
    anywhere = SM.draw_picks(1, SM.MinCell("anywhere", "K8", "b1"), b, 4000)
    kinds = lambda picks: {t[0] for _, t in picks}  # noqa: E731
    assert kinds(local) == {"doc_other", "doc_acts_fail", "wrong", "unlisted"}
    same = lambda picks: np.mean([b.equipment[t[1]].area == b.equipment[b.claims["vav_zone"][room]].area for room, t in picks if t[0] == "wrong"])  # noqa: E731
    assert 0.42 < same(local) < 0.62 and 0.12 < same(anywhere) < 0.30                                                          # 4 x 1 vs 15 x 0.25 -> 0.52 ; 4 of 19 boxes -> 0.21
    far = {t[1] for _, t in anywhere if t[0] == "wrong"}
    assert len(far) == 20 and far <= set(b.equipment)                                                                          # every box can be the feeder, not only the first 8
    frac = lambda picks, k: np.mean([t[0] == k for _, t in picks])  # noqa: E731
    assert 0.66 < frac(local, "doc_other") < 0.74 and 0.12 < frac(local, "doc_acts_fail") < 0.18 and 0.11 < frac(local, "wrong") < 0.16 and 0.005 < frac(local, "unlisted") < 0.03


def test_off_list_means_a_wrong_feeder_the_list_does_not_contain():
    assert SM.is_off_list(("wrong", "V19"), ["V01", "V02"]) and not SM.is_off_list(("wrong", "V02"), ["V01", "V02"])
    assert not SM.is_off_list(("unlisted",), ["V01"]) and not SM.is_off_list(("doc_other",), ["V01"]) and not SM.is_off_list(("doc_acts_fail",), ["V01"])
    b = fake_layout()
    picks = SM.draw_picks(2, SM.MinCell("anywhere", "K8", "b1"), b, 500)
    n_min = sum(SM.is_off_list(t, SM.assumed_case(b, r, "K8", "min").candidates) for r, t in picks)
    assert 0.06 < n_min / 500 < 0.14                                                                                           # about 0.135 x (1 - 7/19)
    assert sum(SM.is_off_list(t, SM.assumed_case(b, r, "K40", "min").candidates) for r, t in picks) == 0                      # a list that covers the building leaves nothing off it


# ---------------------------------------------------------------------------------------------- the runner
def run(world="anywhere", cap="K8", n=40, idx=4, layout=None):
    return SM.run_min_cell(idx, SM.MinCell(world, cap, "b1"), layout or fake_layout(), n=n)


def test_runner_shapes_pairing_determinism_and_prefix():
    r = run()
    assert set(r["policy"]) == set(SM.POLICIES) and r["n"] == 40 and r["boxes"] == 20 and len(r["room_idx"]) == 40 and len(r["truth_kind"]) == 40
    for name, p in r["policy"].items():
        assert np.isfinite(p["minutes"]).all() and (p["correct"] == (p["guess_idx"] == p["truth_idx"])).all() and p["truth_idx"].min() >= 0
        assert (p["off_list"] <= (r["truth_kind"] == "wrong")).all()
    again = run()
    assert all(np.array_equal(r["policy"][p][k], again["policy"][p][k]) for p in SM.POLICIES for k in ("minutes", "guess_idx", "checks", "off_list"))
    small, big = run(n=10), run(n=25)
    assert all(np.array_equal(small["policy"][p][k], big["policy"][p][k][:10]) for p in SM.POLICIES for k in ("minutes", "checks", "guess_idx", "truth_idx", "off_list", "named"))
    assert SM.g5_complete_min([r], n_cells=1, expected_idx=[4])[0]


def test_off_list_truths_are_answered_as_unlisted_and_are_never_actionable():
    b = fake_layout()
    r = run(n=300, layout=b)
    p = r["policy"]["entropy@min"]
    assert p["off_list"].any()
    n_causes = len(M.make_prior("vav_zone", SM.assumed_case(b, "Z01", "K8", "min").candidates, "V01", M.Settings(), None, None)[0])
    assert (p["truth_idx"][p["off_list"]] == n_causes - 1).all()                                                               # "unlisted" is the last cause
    for name, q in r["policy"].items():
        assert not (q["correct"] & q["named"] & q["off_list"]).any()                                                           # an off-list truth is only ever "answered" by saying unlisted


def test_levels_are_identical_when_there_is_nothing_to_group_by():
    b = fake_layout()
    assert SM.gate_g1_min(b)[0]
    flat = SM.one_area(b)
    assert {e.area for e in flat.equipment.values()} == {"A"}
    a = SM.run_min_cell(3, SM.MinCell("local", "K8", "b1"), flat, n=60)
    for k in SM.KINDS:
        for key in ("minutes", "guess_idx", "checks"):
            assert np.array_equal(a["policy"][f"{k}@min"][key], a["policy"][f"{k}@grouped"][key])                          # same candidate order, same weights, same draws
    r = run(world="local", n=200)
    assert not np.array_equal(r["policy"]["entropy@min"]["minutes"], r["policy"]["entropy@grouped"]["minutes"])         # with areas the levels do differ


def test_the_two_levels_share_outcome_streams(monkeypatch):
    monkeypatch.setattr(SM, "strip_areas", lambda b: b)                                                                        # min == grouped: the arrays must then be identical
    r = run(world="local", n=60)
    for k in SM.KINDS:
        assert all(np.array_equal(r["policy"][f"{k}@min"][key], r["policy"][f"{k}@grouped"][key]) for key in ("minutes", "guess_idx", "checks"))


# ---------------------------------------------------------------------------------------------- analysis of one cell
def fake_result(n=300, seed=0, base=100.0, tool=None, habit_f=None):
    """Cell result with six policies set by hand: `tool[level] = (minutes factor, accuracy, off-list share)` for entropy; the habits use fixed values. Policies share their random numbers, so a
    difference is exactly the shift (paired)."""
    rng = np.random.default_rng(seed)
    tool, habit_f = tool or {}, habit_f or {}
    u, v, w = rng.random(n), rng.random(n), rng.random(n)
    pol = {}
    for name in SM.POLICIES:
        kind, level = name.split("@")
        f, acc, off = tool.get(level, (1.0, 0.9, 0.1)) if kind == "entropy" else (habit_f.get(level, 1.0), 0.8, 0.1)
        correct = v < acc
        named = w > 0.2
        pol[name] = dict(truth_idx=np.zeros(n, int), guess_idx=np.where(correct, 0, 1), minutes=base * f * (0.9 + 0.2 * u), checks=np.full(n, 3.0), concluded=np.ones(n, bool), correct=correct,
                         off_list=w < off, named=named)
    return dict(idx=3, cell=SM.MinCell("local", "K8", "b1"), n=n, policy=pol)


def test_summary_adds_the_actionable_and_off_list_rates():
    r = fake_result(tool={"min": (1.0, 0.9, 0.1)})
    s = SM.summarize_min(r)["entropy@min"]
    p = r["policy"]["entropy@min"]
    assert np.isclose(s["actionable"], (p["correct"] & p["named"]).mean()) and np.isclose(s["off_list"], p["off_list"].mean()) and np.isclose(s["accuracy"], p["correct"].mean())
    assert s["actionable"] < s["accuracy"]                                                                                     # actionable is a subset of correct


def test_grouped_against_min_labels_and_context():
    same = SM.analyze_min_cell(fake_result(tool={"min": (1.0, 0.9, 0.1), "grouped": (1.0, 0.9, 0.1)}), B=200)["grp"]
    assert same["label"] == "NEITHER" and same["d_min"] == 0 and same["d_acc"] == 0 and same["d_off"] == 0
    fast = SM.analyze_min_cell(fake_result(tool={"min": (1.0, 0.9, 0.1), "grouped": (0.7, 0.9, 0.05)}), B=200)["grp"]
    assert fast["label"] == "IMPROVES" and fast["time"] == "FASTER" and fast["d_min"] < 0 and fast["d_off"] < 0                 # grouping is the treatment: faster than min
    slow = SM.analyze_min_cell(fake_result(tool={"min": (1.0, 0.9, 0.1), "grouped": (1.5, 0.9, 0.1)}), B=200)["grp"]
    assert slow["label"] == "WORSE" and slow["time"] == "SLOWER"
    acc = SM.analyze_min_cell(fake_result(tool={"min": (1.0, 0.7, 0.1), "grouped": (1.0, 0.95, 0.1)}), B=300)["grp"]
    assert acc["label"] == "IMPROVES" and acc["acc"] == "MORE" and acc["d_acc"] > 0.2
    ctx = SM.analyze_min_cell(fake_result(habit_f={"min": 2.0, "grouped": 0.5}), B=100)["ctx"]
    assert np.isclose(ctx["min|habit_A"]["r_min"], -0.5) and np.isclose(ctx["grouped|habit_A"]["r_min"], 1.0)                  # each level is compared with the habits at the SAME level
    a = SM.analyze_min_cell(fake_result(), B=100)
    assert set(a["ctx"]) >= {"min", "grouped", "min|habit_A", "min|habit_B", "grouped|habit_A", "grouped|habit_B"} and all(a["ctx"][lv] in ("WINS", "LOSES", "NEITHER") for lv in SM.LEVELS)


# ---------------------------------------------------------------------------------------------- predictions
def fake_analysis(world, cap, building, values):
    """values[policy] = dict(minutes, accuracy, off_list)."""
    return dict(idx=0, cell=SM.MinCell(world, cap, building), summary=values)


def good_values(world, cap):
    off_min = {("local", "K8"): 0.10, ("local", "K40"): 0.06, ("anywhere", "K8"): 0.12, ("anywhere", "K40"): 0.06}[(world, cap)]
    grouped_off, grouped_min = (0.02, 40.0) if world == "local" else (off_min, 46.0)
    return {"entropy@min": dict(minutes=50.0 if world == "local" else 45.0, accuracy=0.90, off_list=off_min), "entropy@grouped": dict(minutes=grouped_min, accuracy=0.92, off_list=grouped_off),
            "habit_A@min": dict(minutes=30.0, accuracy=0.80, off_list=off_min), "habit_B@min": dict(minutes=80.0, accuracy=0.88, off_list=off_min)}


def fake_analyses(override=None, buildings=("a", "b", "c")):
    override = override or {}
    out = []
    for w in SM.WORLDS:
        for c in SM.CAPS:
            for b in buildings:
                v = {p: dict(d) for p, d in good_values(w, c).items()}
                for (pol, key), val in override.get((w, c), {}).items():
                    v[pol][key] = val
                out.append(fake_analysis(w, c, b, v))
    return out


def test_predictions_hold_and_fail_one_at_a_time():
    pr = SM.min_predictions(fake_analyses())
    assert all(v["holds"] for v in pr.values()) and set(pr) == {"P1", "P2", "P3", "P4", "P5"}
    fails = {"P1": {("local", "K40"): {("entropy@min", "off_list"): 0.01}}, "P1b": {("local", "K8"): {("entropy@min", "minutes"): 39.0}},
             "P2": {("anywhere", "K8"): {("entropy@min", "minutes"): 60.0}}, "P2b": {("anywhere", "K40"): {("entropy@min", "off_list"): 0.09}},
             "P3": {("anywhere", "K8"): {("entropy@min", "off_list"): 0.07}}, "P3b": {("anywhere", "K40"): {("entropy@min", "off_list"): 0.12}},
             "P4": {("local", "K40"): {("habit_A@min", "accuracy"): 0.90}}, "P5": {("anywhere", "K40"): {("habit_B@min", "minutes"): 45.0}}}
    for name, override in fails.items():
        got = SM.min_predictions(fake_analyses(override))
        assert not got[name[:2]]["holds"], name
    edges = SM.min_predictions(fake_analyses({("anywhere", "K8"): {("entropy@min", "minutes"): 50.5}}))                                      # +9.8% of 46.0 is still inside
    assert edges["P2"]["holds"]
    assert not SM.min_predictions(fake_analyses({("anywhere", "K8"): {("entropy@min", "minutes"): 50.7}}))["P2"]["holds"]
    assert not SM.min_predictions(fake_analyses({("anywhere", "K8"): {("entropy@min", "off_list"): 0.08, ("entropy@grouped", "off_list"): 0.0}}))["P2"]["holds"]              # 0.08 apart


# ---------------------------------------------------------------------------------------------- gates
def test_coverage_gate_recomputes_the_off_list_flags():
    b = fake_layout()
    layouts = {"b1": b}
    results = [run(world=w, cap=c, n=60, idx=i) for i, (w, c) in enumerate([("local", "K8"), ("anywhere", "K8"), ("anywhere", "K40")])]
    assert SM.gate_g3_coverage(results, layouts)[0]
    bad = [run(world="anywhere", cap="K8", n=60, idx=1)]
    p = bad[0]["policy"]["entropy@grouped"]
    p["off_list"] = ~p["off_list"]                                                                                                # a flipped flag is caught
    assert not SM.gate_g3_coverage(bad, layouts)[0]
    small = fake_layout(n=6, per=3)                                                                                              # a building with fewer boxes than K: nothing can be off the list
    ok = run(world="anywhere", cap="K8", n=60, idx=2, layout=small)
    assert ok["policy"]["entropy@min"]["off_list"].sum() == 0 and SM.gate_g3_coverage([ok], {"b1": small})[0]
    ok["policy"]["habit_A@min"]["off_list"] = ok["policy"]["habit_A@min"]["off_list"].copy()
    ok["policy"]["habit_A@min"]["off_list"][0] = True
    assert not SM.gate_g3_coverage([ok], {"b1": small})[0]
    neg = run(world="local", cap="K8", n=30, idx=0)
    neg["policy"]["entropy@min"]["truth_idx"] = neg["policy"]["entropy@min"]["truth_idx"].copy()
    neg["policy"]["entropy@min"]["truth_idx"][0] = -1
    assert not SM.gate_g3_coverage([neg], layouts)[0]


def test_completeness_gate():
    r = run(n=12, idx=0)
    assert SM.g5_complete_min([r], n_cells=1)[0] and not SM.g5_complete_min([r], n_cells=2)[0] and not SM.g5_complete_min([], n_cells=1)[0]
    broken = run(n=12, idx=0)
    broken["policy"]["habit_A@min"]["minutes"] = broken["policy"]["habit_A@min"]["minutes"].copy()
    broken["policy"]["habit_A@min"]["minutes"][0] = np.nan
    assert not SM.g5_complete_min([broken], n_cells=1)[0]
    missing = run(n=12, idx=0)
    del missing["policy"]["habit_B@grouped"]
    assert not SM.g5_complete_min([missing], n_cells=1)[0]
    short = run(n=12, idx=0)
    short["room_idx"] = short["room_idx"][:-1]
    assert not SM.g5_complete_min([short], n_cells=1)[0]
    stray = run(world="local", n=40, idx=0)
    stray["policy"]["entropy@min"]["off_list"] = ~(stray["truth_kind"] == "wrong") | stray["policy"]["entropy@min"]["off_list"]                                          # off-list on a non-wrong truth
    assert not SM.g5_complete_min([stray], n_cells=1)[0]


def test_g1_gate_catches_a_level_that_carries_a_different_prior(monkeypatch):
    real = SM.assumed_case

    def other_prior(layout, room, cap, level):
        case = real(layout, room, cap, level)
        return make_case(SM.level_layout(layout, level), room, "vav_zone", M.Settings(p_wrong=0.30) if level == "grouped" else M.Settings(), max_candidates=len(case.candidates))

    monkeypatch.setattr(SM, "assumed_case", other_prior)
    assert not SM.gate_g1_min(fake_layout())[0]                                                                                # with no grouping information the two levels must agree


def test_g1_gate_catches_a_habit_that_reads_the_areas(monkeypatch):
    original = S.run_habit_A

    def sneaky(case, truth, rng, true_menu):
        out = original(case, truth, rng, true_menu)
        if any(e.area is not None for e in case.building.equipment.values()):
            out["minutes"] += 1.0
        return out

    monkeypatch.setitem(S.RUNNERS, "habit_A", sneaky)
    assert not SM.gate_g1_min(fake_layout())[0]                                                                                # the levels differ only by the areas, so a habit that reads them is caught


# ---------------------------------------------------------------------------------------------- real data
@pytest.mark.skipif(not HAVE_DATA, reason="Mortar Brick files not cached")
def test_runs_on_a_real_layout_and_covers_its_boxes():
    b, meta = R.load_layout(DATA / "mortar__bldg8.ttl", "bldg8")
    res = SM.run_min_cell(0, SM.MinCell("anywhere", "K8", "bldg8"), b, n=10)
    assert SM.g5_complete_min([res], n_cells=1)[0] and SM.gate_g3_coverage([res], {"bldg8": b})[0] and SM.gate_g1_min(b)[0] and res["boxes"] == meta.boxes
    a = SM.analyze_min_cell(res, B=50)
    assert set(a["grp"]) >= {"label", "d_min", "d_off"}
