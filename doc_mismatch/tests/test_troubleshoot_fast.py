"""Guards for the tool-against-stand-ins study (PREREGISTRATION_DR.md Addendum 26): cells, policies and lists, the habits on the id-near list, the runner, the analysis, predictions and gates."""
import sys
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("rdflib")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import census as C  # noqa: E402
from docmismatch.troubleshoot import idproximity as ID  # noqa: E402
from docmismatch.troubleshoot import realmaps as R  # noqa: E402
from docmismatch.troubleshoot import study as S  # noqa: E402
from docmismatch.troubleshoot import study_fast as FA  # noqa: E402
from docmismatch.troubleshoot import study_idweight as IW  # noqa: E402
from docmismatch.troubleshoot import study_minimum as SM  # noqa: E402

DATA = ROOT.parent / "data_cache"
HAVE_DATA = (DATA / "mortar__bldg8.ttl").exists()


def make_layout(n=20, per=5):
    """Boxes VAV01..; handler blocks of `per` boxes; zone Zi <- box i."""
    nums = list(range(1, n + 1))
    kinds = {f"VAV{i:02d}": "VAV" for i in nums} | {f"Z{i:02d}": "Zone" for i in nums} | {f"AHU-{chr(65 + h)}": "AHU" for h in range((n + per - 1) // per)}
    vz = [(f"VAV{i:02d}", f"Z{i:02d}") for i in nums]
    av = [(f"AHU-{chr(65 + (i - 1) // per)}", f"VAV{i:02d}") for i in nums]
    return R.layout_from_census(C.BrickCensus("b1", kinds, {}, {"vav_zone": vz, "ahu_vav": av, "coil_vav": [], "coil_ahu": []}))[0]


# ---------------------------------------------------------------------------------------------- cells, policies, lists
def test_cells_policies_and_pairs():
    cells = FA.all_fast_cells(list(R.FROZEN_BUILDINGS))
    assert len(cells) == 250 and cells == IW.all_idw_cells(list(R.FROZEN_BUILDINGS)) and FA.SEED == IW.SEED == SM.SEED == 23
    assert FA.POLICIES == ("entropy@min", "entropy@idw4", "habit_A@min", "habit_A@idnear", "habit_B@min", "habit_B@idnear") and FA.STREAM == {"entropy": 0, "habit_A": 1, "habit_B": 2} == SM.STREAM
    assert FA.PAIRS[0] == ("entropy@idw4", "habit_A@idnear") and FA.PAIRS[1] == ("entropy@idw4", "habit_B@idnear") and len(FA.PAIRS) == 6
    assert (FA.TOOL, FA.FAST, FA.SLOW) == ("entropy@idw4", "habit_A@idnear", "habit_B@idnear") and set(FA.COMBOS) == {"same information", "arbitrary list", "tool with ids, technician without"}
    assert FA.GAINS == (("habit_A@idnear", "habit_A@min"), ("habit_B@idnear", "habit_B@min")) and set(FA.WORLDS) == set(IW.WORLDS)


def test_the_habits_on_the_id_list_see_exactly_the_tools_candidates():
    b = make_layout()
    tool, habit = FA.assumed_case(b, "Z10", "K8", "idw4"), FA.assumed_case(b, "Z10", "K8", "idnear")
    assert tool.candidates == habit.candidates == ID.id_near_list(b, "VAV10", 8) and tool.settings.nearness == "id" and set(habit.weights.values()) == {1.0}
    assert FA.assumed_case(b, "Z10", "K8", "min").candidates == SM.assumed_case(b, "Z10", "K8", "min").candidates


def test_the_habits_read_the_order_and_never_the_weights(monkeypatch):
    b = make_layout()
    assert FA.gate_habits_ignore_weights(b)[0]
    original = S.run_habit_B

    def sneaky(case, truth, rng, true_menu):
        out = original(case, truth, rng, true_menu)
        if any(w != 1.0 for w in case.weights.values()):
            out["minutes"] += 1.0
        return out

    monkeypatch.setitem(S.RUNNERS, "habit_B", sneaky)
    ok, msg = FA.gate_habits_ignore_weights(b)
    assert not ok and "habit_B" in msg


# ---------------------------------------------------------------------------------------------- the runner
def run(world="idlocal2", cap="K8", n=40, idx=2, layout=None):
    return FA.run_fast_cell(idx, FA.FastCell(world, cap, "b1"), layout or make_layout(), n=n)


def test_runner_shapes_pairing_determinism_and_prefix():
    r = run()
    assert set(r["policy"]) == set(FA.POLICIES) and r["n"] == 40
    for p in r["policy"].values():
        assert np.isfinite(p["minutes"]).all() and (p["correct"] == (p["guess_idx"] == p["truth_idx"])).all() and p["truth_idx"].min() >= 0 and (p["off_list"] <= (r["truth_kind"] == "wrong")).all()
    again = run()
    assert all(np.array_equal(r["policy"][p][k], again["policy"][p][k]) for p in FA.POLICIES for k in ("minutes", "guess_idx", "checks", "off_list"))
    small, big = run(n=10), run(n=25)
    assert all(np.array_equal(small["policy"][p][k], big["policy"][p][k][:10]) for p in FA.POLICIES for k in ("minutes", "checks", "guess_idx", "truth_idx", "off_list", "named"))
    assert FA.g5_complete_fast([r], n_cells=1, expected_idx=[2])[0]
    assert np.array_equal(r["policy"]["entropy@idw4"]["off_list"], r["policy"]["habit_A@idnear"]["off_list"])                     # the same list, so the same episodes are off it


def test_the_tool_reproduces_addendum_25_and_the_habits_addendum_23():
    b = make_layout()
    mine = [FA.run_fast_cell(i, FA.FastCell(w, c, "b1"), b, n=30) for i, (w, c) in enumerate([("local", "K8"), ("anywhere", "K40")])]
    a25 = [IW.run_idw_cell(i, IW.IdwCell(w, c, "b1"), b, n=30) for i, (w, c) in enumerate([("local", "K8"), ("anywhere", "K40")])]
    a23 = [SM.run_min_cell(i, SM.MinCell(w, c, "b1"), b, n=30) for i, (w, c) in enumerate([("local", "K8"), ("anywhere", "K40")])]
    assert FA.gate_g1_a25(mine, a25) == (True, "2 cells reproduce Addendum 25 exactly") and FA.gate_g1_a23(mine, a23) == (True, "2 cells reproduce Addendum 23 exactly")
    a25[0]["policy"]["entropy@idw4"]["minutes"] = a25[0]["policy"]["entropy@idw4"]["minutes"] + 1.0
    assert not FA.gate_g1_a25(mine, a25)[0]
    a23[1]["policy"]["habit_A@min"]["guess_idx"] = (a23[1]["policy"]["habit_A@min"]["guess_idx"] + 1) % 5
    assert not FA.gate_g1_a23(mine, a23)[0] and not FA.gate_g1_a23(mine, [])[0] and not FA.gate_g1_a25(mine, [])[0]


def test_the_id_list_helps_the_fast_stand_in_in_an_adjacency_world():
    r = FA.run_fast_cell(1, FA.FastCell("idlocal2", "K8", "b1"), make_layout(n=30, per=5), n=250)
    act = lambda p: float((r["policy"][p]["correct"] & r["policy"][p]["named"]).mean())  # noqa: E731
    mins = lambda p: float(r["policy"][p]["minutes"].mean())  # noqa: E731
    assert act("habit_A@idnear") > act("habit_A@min") + 0.03 and mins("habit_A@idnear") < mins("habit_A@min")                        # by construction of the world, and it must show
    assert act("entropy@idw4") > act("entropy@min")


# ---------------------------------------------------------------------------------------------- analysis
def fake_result(n=300, seed=0, base=100.0, spec=None):
    """Six policies set by hand: `spec[policy] = (minutes factor, accuracy)`; the rest use (1.0, 0.9). All policies share their random numbers, so a difference is exactly the shift."""
    rng = np.random.default_rng(seed)
    spec = spec or {}
    truth = rng.integers(0, 4, n)
    u, v, w = rng.random(n), rng.random(n), rng.random(n)
    pol = {}
    for name in FA.POLICIES:
        f, acc = spec.get(name, (1.0, 0.9))
        correct = v < acc
        pol[name] = dict(truth_idx=truth, guess_idx=np.where(correct, truth, (truth + 1) % 4), minutes=base * f * (0.9 + 0.2 * u), checks=np.full(n, 3.0), concluded=np.ones(n, bool), correct=correct,
                         off_list=w < 0.1, named=w > 0.2)
    return dict(idx=3, cell=FA.FastCell("local", "K8", "b1"), n=n, policy=pol)


def test_analysis_labels_hand_built_differences():
    a = FA.analyze_fast_cell(fake_result(spec={"entropy@idw4": (0.7, 0.9), "habit_A@idnear": (1.0, 0.9)}), B=200)
    assert a["cmp"]["entropy@idw4|habit_A@idnear"]["label"] == "WINS" and a["cmp"]["entropy@idw4|habit_A@idnear"]["secondary"] == "WINS"
    lose = FA.analyze_fast_cell(fake_result(spec={"entropy@idw4": (1.4, 0.9)}), B=200)["cmp"]["entropy@idw4|habit_A@idnear"]
    assert lose["label"] == "LOSES" and lose["r_min"] > 0.3
    buy = FA.analyze_fast_cell(fake_result(spec={"entropy@idw4": (1.4, 0.97), "habit_A@idnear": (1.0, 0.8)}), B=300)["cmp"]["entropy@idw4|habit_A@idnear"]
    assert buy["label"] == "NEITHER" and buy["secondary"] == "BUYS ACCURACY" and buy["d_acc"] > 0.1                                # slower but clearly more accurate
    same = FA.analyze_fast_cell(fake_result(), B=100)
    assert set(same["cmp"]) == {f"{t}|{h}" for t, h in FA.PAIRS} and set(same["combo"]) == set(FA.COMBOS) and set(same["gain"]) == {f"{a}|{b}" for a, b in FA.GAINS}
    assert all(same["cmp"][k]["label"] == "NEITHER" for k in same["cmp"]) and all(v == "NEITHER" for v in same["combo"].values())


def test_each_pair_uses_the_policies_it_names():
    r = fake_result(spec={"habit_A@min": (0.5, 0.9), "habit_A@idnear": (2.0, 0.9)})
    c = FA.analyze_fast_cell(r, B=100)["cmp"]
    assert np.isclose(c["entropy@idw4|habit_A@idnear"]["r_min"], -0.5) and np.isclose(c["entropy@idw4|habit_A@min"]["r_min"], 1.0)             # the tool against a slow and against a fast habit
    assert np.isclose(c["entropy@min|habit_A@min"]["r_min"], 1.0)


def test_combination_against_both_habits_and_the_gains():
    r = fake_result(spec={"entropy@idw4": (0.7, 0.9), "habit_A@idnear": (1.0, 0.9), "habit_B@idnear": (0.5, 0.9), "habit_A@min": (1.3, 0.8)})
    a = FA.analyze_fast_cell(r, B=100)
    assert a["combo"]["same information"] == "LOSES" and a["combo"]["arbitrary list"] == "NEITHER"                                     # wins against A, loses against B: LOSES; nothing to separate min from min
    assert a["cmp"]["entropy@idw4|habit_A@idnear"]["label"] == "WINS" and a["cmp"]["entropy@idw4|habit_B@idnear"]["label"] == "LOSES"
    g = a["gain"]["habit_A@idnear|habit_A@min"]
    assert g["d_min"] < 0 and g["d_acc"] > 0 and np.isclose(g["d_act"], np.mean((r["policy"]["habit_A@idnear"]["correct"] & r["policy"]["habit_A@idnear"]["named"]).astype(float)
                                                                                - (r["policy"]["habit_A@min"]["correct"] & r["policy"]["habit_A@min"]["named"]).astype(float)))


# ---------------------------------------------------------------------------------------------- predictions
DEFAULT = {"entropy@min": dict(minutes=38, accuracy=0.95, actionable=0.86, wrong_confident=0.02), "entropy@idw4": dict(minutes=36, accuracy=0.95, actionable=0.90, wrong_confident=0.02),
           "habit_A@min": dict(minutes=25, accuracy=0.80, actionable=0.75, wrong_confident=0.20), "habit_A@idnear": dict(minutes=22, accuracy=0.85, actionable=0.80, wrong_confident=0.14),
           "habit_B@min": dict(minutes=60, accuracy=0.92, actionable=0.82, wrong_confident=0.08), "habit_B@idnear": dict(minutes=55, accuracy=0.93, actionable=0.85, wrong_confident=0.07)}


def fake_analyses(over=None, buildings=("a", "b")):
    """Analyses with group means set by hand so that P1-P5 all hold; `over[(world, cap, policy, key)]` replaces one value."""
    over, out = over or {}, []
    for w in FA.WORLDS:
        for c in FA.CAPS:
            summ = {p: dict(v) for p, v in DEFAULT.items()}
            if w == "idlocal2":
                summ["habit_A@idnear"]["actionable"] = 0.86                                                                              # +0.11 over habit_A@min
            for (ww, cc, pol, key), val in over.items():
                if (ww, cc) == (w, c):
                    summ[pol][key] = val
            for b in buildings:
                out.append(dict(cell=FA.FastCell(w, c, b), summary=summ))
    return out


def test_predictions_hold_and_fail_one_at_a_time():
    pr = FA.fast_predictions(fake_analyses())
    assert all(v["holds"] for v in pr.values()) and set(pr) == {"P1", "P2", "P3", "P4", "P5"}
    assert not FA.fast_predictions(fake_analyses({("local", "K8", "habit_A@idnear", "minutes"): 36}))["P1"]["holds"]                    # equal is not faster
    assert not FA.fast_predictions(fake_analyses({("anywhere", "K40", "habit_A@idnear", "minutes"): 40}))["P1"]["holds"]
    assert not FA.fast_predictions(fake_analyses({("idlocal8", "K40", "habit_A@idnear", "accuracy"): 0.95}))["P2"]["holds"]
    assert not FA.fast_predictions(fake_analyses({("local", "K8", "habit_A@idnear", "wrong_confident"): 0.06}))["P3"]["holds"]          # only 0.04 above the tool
    assert FA.fast_predictions(fake_analyses({("local", "K8", "habit_A@idnear", "wrong_confident"): 0.075}))["P3"]["holds"]
    assert not FA.fast_predictions(fake_analyses({("idlocal4", "K40", "habit_B@idnear", "minutes"): 30}))["P4"]["holds"]
    assert not FA.fast_predictions(fake_analyses({("idlocal2", "K8", "habit_A@idnear", "actionable"): 0.77}))["P5"]["holds"]              # 0.02 above habit_A@min only
    assert FA.fast_predictions(fake_analyses({("idlocal2", "K8", "habit_A@idnear", "actionable"): 0.79}))["P5"]["holds"]
    assert not FA.fast_predictions(fake_analyses({("idlocal2", "K40", "habit_A@min", "actionable"): 0.9}))["P5"]["holds"]


# ---------------------------------------------------------------------------------------------- gates
def test_coverage_gate_recomputes_the_off_list_flags_against_each_policys_own_list():
    b = make_layout()
    layouts = {"b1": b}
    results = [run(world=w, cap=c, n=60, idx=i) for i, (w, c) in enumerate([("local", "K8"), ("idlocal2", "K8"), ("anywhere", "K40")])]
    assert FA.gate_g3(results, layouts)[0]
    p = results[1]["policy"]["habit_A@idnear"]
    p["off_list"] = ~p["off_list"]
    assert not FA.gate_g3(results, layouts)[0]
    swap = [run(world="idlocal2", cap="K8", n=60, idx=1)]
    swap[0]["policy"]["habit_A@idnear"]["off_list"] = swap[0]["policy"]["habit_A@min"]["off_list"]                                       # a habit given the other list's flags
    if not np.array_equal(swap[0]["policy"]["habit_A@min"]["off_list"], swap[0]["policy"]["entropy@idw4"]["off_list"]):
        assert not FA.gate_g3(swap, layouts)[0]
    small = make_layout(n=6, per=3)
    ok = run(world="anywhere", cap="K8", n=60, idx=0, layout=small)
    assert all(p["off_list"].sum() == 0 for p in ok["policy"].values()) and FA.gate_g3([ok], {"b1": small})[0]
    ok["policy"]["habit_B@min"]["off_list"] = ok["policy"]["habit_B@min"]["off_list"].copy()
    ok["policy"]["habit_B@min"]["off_list"][0] = True
    assert not FA.gate_g3([ok], {"b1": small})[0]


def test_completeness_gate():
    r = run(n=12, idx=0)
    assert FA.g5_complete_fast([r], n_cells=1)[0] and not FA.g5_complete_fast([r], n_cells=2)[0] and not FA.g5_complete_fast([], n_cells=1)[0]
    broken = run(n=12, idx=0)
    broken["policy"]["habit_A@idnear"]["minutes"] = broken["policy"]["habit_A@idnear"]["minutes"].copy()
    broken["policy"]["habit_A@idnear"]["minutes"][0] = np.nan
    assert not FA.g5_complete_fast([broken], n_cells=1)[0]
    missing = run(n=12, idx=0)
    del missing["policy"]["habit_B@idnear"]
    assert not FA.g5_complete_fast([missing], n_cells=1)[0]
    stray = run(world="local", n=40, idx=0)
    stray["policy"]["entropy@min"]["off_list"] = ~(stray["truth_kind"] == "wrong") | stray["policy"]["entropy@min"]["off_list"]
    assert not FA.g5_complete_fast([stray], n_cells=1)[0]


# ---------------------------------------------------------------------------------------------- real data
@pytest.mark.skipif(not HAVE_DATA, reason="Mortar Brick files not cached")
def test_runs_on_a_real_layout():
    b, meta = R.load_layout(DATA / "mortar__bldg8.ttl", "bldg8")
    res = FA.run_fast_cell(0, FA.FastCell("idlocal4", "K40", "bldg8"), b, n=8)
    assert FA.g5_complete_fast([res], n_cells=1)[0] and FA.gate_habits_ignore_weights(b)[0] and FA.gate_g3([res], {"bldg8": b})[0] and res["boxes"] == meta.boxes
    a = FA.analyze_fast_cell(res, B=50)
    assert set(a["combo"]) == set(FA.COMBOS)
