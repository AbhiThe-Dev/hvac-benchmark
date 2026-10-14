"""Guards for the id-proximity study (PREREGISTRATION_DR.md Addendum 24): natural order, id-near lists, exact coverage, the Part A metrics, the adjacency worlds, the runner, predictions and gates."""
import sys
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("rdflib")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import census as C  # noqa: E402
from docmismatch.troubleshoot import idproximity as ID  # noqa: E402
from docmismatch.troubleshoot import model as M  # noqa: E402
from docmismatch.troubleshoot import realmaps as R  # noqa: E402
from docmismatch.troubleshoot import study_minimum as SM  # noqa: E402

DATA = ROOT.parent / "data_cache"
HAVE_DATA = (DATA / "mortar__bldg8.ttl").exists()


def make_layout(n=20, per=5, prefix="VAV", pad=2, handled=None):
    """Boxes `prefix`01..; handler blocks of `per` boxes (AHU-A, AHU-B, ...); zone Zi <- box i. `handled` (a set of box numbers) limits which boxes have a documented handler."""
    nums = list(range(1, n + 1))
    box = {i: f"{prefix}{i:0{pad}d}" for i in nums}
    kinds = {box[i]: "VAV" for i in nums} | {f"Z{i:0{pad}d}": "Zone" for i in nums} | {f"AHU-{chr(65 + h)}": "AHU" for h in range((n + per - 1) // per)}
    vz = [(box[i], f"Z{i:0{pad}d}") for i in nums]
    av = [(f"AHU-{chr(65 + (i - 1) // per)}", box[i]) for i in nums if handled is None or i in handled]
    return R.layout_from_census(C.BrickCensus("b1", kinds, {}, {"vav_zone": vz, "ahu_vav": av, "coil_vav": [], "coil_ahu": []}))[0]


# ---------------------------------------------------------------------------------------------- natural order and id-near lists
def test_natural_order_compares_digit_runs_as_numbers():
    ids = ["VAVRM10", "VAVRM9", "VAVRM2", "VAVRM2A", "vavrm3"]
    assert sorted(ids, key=lambda b: (ID.natural_key(b), b)) == ["VAVRM2", "VAVRM2A", "vavrm3", "VAVRM9", "VAVRM10"]
    assert sorted(ids)[0] == "VAVRM10"                                                                                            # the plain order would put 10 before 2
    assert ID.natural_key("VAV-2-04") < ID.natural_key("VAV-2-10") < ID.natural_key("VAV-10-01")


def test_boxes_are_ranked_in_natural_order_and_zones_are_ignored():
    b = make_layout(n=12, prefix="V", pad=1)                                                                                       # V1 ... V12: the plain equipment order is V1, V10, V11, V12, V2, ...
    assert [e.id for e in b.equipment.values() if e.kind == "VAV"][:4] == ["V1", "V10", "V11", "V12"]
    assert ID.boxes_in_id_order(b) == [f"V{i}" for i in range(1, 13)] and ID.ranks(b)["V10"] == 9


def test_id_near_list_by_hand():
    b = make_layout(n=10)
    assert ID.id_near_list(b, "VAV05", 4) == ["VAV05", "VAV04", "VAV06", "VAV03"]                                                # ties: the lower rank first
    assert ID.id_near_list(b, "VAV01", 4) == ["VAV01", "VAV02", "VAV03", "VAV04"] and ID.id_near_list(b, "VAV10", 3) == ["VAV10", "VAV09", "VAV08"]
    assert len(ID.id_near_list(b, "VAV05", 100)) == 10 and set(ID.id_near_list(b, "VAV05", 100)) == set(ID.boxes_in_id_order(b))
    for doc in ID.boxes_in_id_order(b):
        for k in (1, 2, 5, 10, 50):
            assert ID.id_near_list(b, doc, k) == ID.brute_force_near(b, doc, k) and ID.id_near_list(b, doc, k)[0] == doc


def test_the_three_levels_of_information():
    b = make_layout(n=20, per=5)
    m, i, g = (ID.assumed_case(b, "Z10", "K8", lv) for lv in ID.LEVELS)
    assert m.candidates == ["VAV10", "VAV01", "VAV02", "VAV03", "VAV04", "VAV05", "VAV06", "VAV07"] and set(m.weights.values()) == {1.0}                                      # Addendum 23's list
    assert i.candidates == ["VAV10", "VAV09", "VAV11", "VAV08", "VAV12", "VAV07", "VAV13", "VAV06"] and set(i.weights.values()) == {1.0}
    assert g.candidates == ["VAV10", "VAV06", "VAV07", "VAV08", "VAV09", "VAV01", "VAV02", "VAV03"] and [g.weights[c] for c in g.candidates] == [1, 1, 1, 1, 1, .25, .25, .25]
    assert m.settings == i.settings == g.settings == M.Settings() and i.doc == m.doc == "VAV10" and i.member == "Z10"
    assert len(ID.assumed_case(b, "Z10", "K40", "idnear").candidates) == 20
    with pytest.raises(ValueError):
        ID.assumed_case(b, "Z10", "K8", "everything")


# ---------------------------------------------------------------------------------------------- worlds and exact coverage
def test_world_weights():
    b = make_layout(n=6, per=3, prefix="V", pad=1)                                                                                 # V1-V3 on AHU-A, V4-V6 on AHU-B
    loc = ID.world_weights(b, "Z6", "local")
    assert loc == {"V4": 1.0, "V5": 1.0, "V1": 0.25, "V2": 0.25, "V3": 0.25} and set(ID.world_weights(b, "Z6", "anywhere").values()) == {1.0}
    lam2 = ID.world_weights(b, "Z6", "idlocal2")
    assert set(lam2) == {"V1", "V2", "V3", "V4", "V5"} and np.isclose(lam2["V5"], np.exp(-0.5)) and np.isclose(lam2["V1"], np.exp(-2.5)) and np.isclose(ID.world_weights(b, "Z6", "idlocal8")["V4"], np.exp(-2 / 8))
    with pytest.raises(ValueError):
        ID.world_weights(b, "Z6", "nowhere")


def test_exact_coverage_by_hand(monkeypatch):
    monkeypatch.setitem(SM.CAPS, "K8", 3)                                                                                           # lists of 3 boxes in a building of 6
    b = make_layout(n=6, per=3, prefix="V", pad=1)
    z6 = {lv: ID.assumed_case(b, "Z6", "K8", lv).candidates for lv in ID.LEVELS}
    assert z6 == {"min": ["V6", "V1", "V2"], "idnear": ["V6", "V5", "V4"], "grouped": ["V6", "V4", "V5"]}
    cover = lambda w, lv: sum(ID.world_weights(b, "Z6", w)[c] for c in z6[lv][1:]) / sum(ID.world_weights(b, "Z6", w).values())  # noqa: E731
    assert np.isclose(cover("local", "min"), 0.5 / 2.75) and np.isclose(cover("local", "idnear"), 2 / 2.75) and np.isclose(cover("local", "grouped"), 2 / 2.75)
    assert np.isclose(cover("anywhere", "min"), 0.4) and np.isclose(cover("anywhere", "idnear"), 0.4)
    s = sum(np.exp(-d / 2) for d in (1, 2, 3, 4, 5))                                                                                # the five other boxes of Z6, at rank distances 1..5
    assert np.isclose(cover("idlocal2", "idnear"), (np.exp(-0.5) + np.exp(-1)) / s) and np.isclose(cover("idlocal2", "min"), (np.exp(-2.5) + np.exp(-2)) / s)
    table = ID.coverage_table(b)                                                                                                    # mean over the six rooms, by an independent loop
    for lv in ID.LEVELS:
        vals = []
        for d in range(1, 7):
            same = [j for j in range(1, 7) if j != d and (j - 1) // 3 == (d - 1) // 3]
            other = [j for j in range(1, 7) if j != d and j not in same]
            w = {j: 1.0 for j in same} | {j: 0.25 for j in other}
            first = [j for j in range(1, 7) if j != d][:2]
            near = sorted((j for j in range(1, 7) if j != d), key=lambda j: (abs(j - d), j))[:2]
            group = (same + other)[:2]
            lst = {"min": first, "idnear": near, "grouped": group}[lv]
            vals.append(sum(w[j] for j in lst) / sum(w.values()))
        assert np.isclose(table[("local", "K8", lv)], np.mean(vals))
    assert ID.expected_off_list(1.0) == 0 and np.isclose(ID.expected_off_list(0.0), 0.135) and np.isclose(ID.expected_off_list(0.5), 0.0675)


def test_exact_coverage_matches_the_drawn_episodes():
    b = make_layout(n=20, per=5)
    table = ID.coverage_table(b)
    for world in ("local", "anywhere", "idlocal2"):
        spec = ID.IdCell(world, "K8", "b1")
        picks = ID.draw_picks(5, spec, b, 6000)
        for lv in ID.LEVELS:
            sim_off = np.mean([SM.is_off_list(t, ID.assumed_case(b, room, "K8", lv).candidates) for room, t in picks])
            assert abs(sim_off - ID.expected_off_list(table[(world, "K8", lv)])) < 0.012, (world, lv)                                # a 6000-draw estimate of a share near 0.1


def test_coverage_is_one_when_the_list_holds_every_box():
    b = make_layout(n=6, per=3)
    table = ID.coverage_table(b)
    assert all(np.isclose(v, 1.0) for (w, c, lv), v in table.items() if c == "K40")                                                 # a 40-box list in a 6-box building
    assert all(0 <= v <= 1 for v in table.values())


# ---------------------------------------------------------------------------------------------- Part A
def test_name_consistency():
    pairs = [("VAVRM108", "RM108"), ("VAVRM01_1", "RM01_1"), ("VAV-2-04", "Room-204"), ("vavrm9", "RM9")]
    assert ID.name_consistency(pairs) == (3, 4) and ID.name_consistency([]) == (0, 0) and ID.name_consistency([("VAV1", "VAV1")]) == (1, 1)


def test_handler_lift_by_hand():
    blocks = ID.handler_lift(make_layout(n=12, per=6), k=4)                                                                          # AHU-A: 01-06, AHU-B: 07-12
    assert np.isclose(blocks["s_id"], 32 / 36) and np.isclose(blocks["s_first"], 0.5) and np.isclose(blocks["base"], 5 / 11) and np.isclose(blocks["lift"], (32 / 36) / (5 / 11))
    assert blocks["n_handled"] == 12 and blocks["n_handlers"] == 2 and not blocks["full"]
    unpadded = ID.handler_lift(make_layout(n=12, per=6, prefix="V", pad=1), k=4)                                                      # the plain order is V1, V10, V11, V12, V2, ...: the first-K list changes, the id list does not
    assert np.isclose(unpadded["s_id"], 32 / 36) and np.isclose(unpadded["s_first"], 17 / 36)
    kinds = {f"VAV{i:02d}": "VAV" for i in range(1, 13)} | {f"Z{i:02d}": "Zone" for i in range(1, 13)} | {"AHU-A": "AHU", "AHU-B": "AHU"}
    vz = [(f"VAV{i:02d}", f"Z{i:02d}") for i in range(1, 13)]
    av = [("AHU-A" if i % 2 else "AHU-B", f"VAV{i:02d}") for i in range(1, 13)]                                                     # the handlers alternate along the id order
    lay = R.layout_from_census(C.BrickCensus("alt", kinds, {}, {"vav_zone": vz, "ahu_vav": av, "coil_vav": [], "coil_ahu": []}))[0]
    a = ID.handler_lift(lay, k=4)
    assert np.isclose(a["s_id"], 1 / 3) and a["lift"] < 1 and a["s_id"] < a["base"]
    assert ID.handler_lift(make_layout(n=12, per=12)) is None                                                                         # one handler: no contrast
    part = ID.handler_lift(make_layout(n=12, per=6, handled=set(range(1, 9))), k=4)                                                   # boxes without a handler are left out
    assert part["n_handled"] == 8 and part["n_handlers"] == 2
    assert ID.handler_lift(make_layout(n=6, per=3), k=8)["full"]                                                                      # a list that holds every box is 'full'


# ---------------------------------------------------------------------------------------------- the runner
def run(world="idlocal2", cap="K8", n=40, idx=2, layout=None):
    return ID.run_id_cell(idx, ID.IdCell(world, cap, "b1"), layout or make_layout(), n=n)


def test_cells_and_policies():
    cells = ID.all_id_cells(list(R.FROZEN_BUILDINGS))
    assert len(cells) == 200 and cells[0] == ID.IdCell("local", "K8", "bldg2") and cells[100] == ID.IdCell("idlocal2", "K8", "bldg2") and cells[-1] == ID.IdCell("idlocal8", "K40", "bldg44")
    assert cells[:100] == [ID.IdCell(c.world, c.cap, c.building) for c in SM.all_min_cells(list(R.FROZEN_BUILDINGS))]                # the first 100 are Addendum 23's cells
    assert ID.POLICIES == ("entropy@min", "entropy@idnear", "entropy@grouped") and ID.SEED == SM.SEED == 23 and ID.DECAY == {"idlocal2": 2.0, "idlocal8": 8.0}


def test_the_first_two_worlds_draw_addendum_23s_episodes():
    b = make_layout()
    for world in ("local", "anywhere"):
        assert ID.draw_picks(3, ID.IdCell(world, "K8", "b1"), b, 50) == SM.draw_picks(3, SM.MinCell(world, "K8", "b1"), b, 50)


def test_adjacency_worlds_put_wrong_feeders_next_door():
    b = make_layout(n=20)
    rk = ID.ranks(b)
    dist = lambda w: np.mean([abs(rk[t[1]] - rk[b.claims["vav_zone"][room]]) for room, t in ID.draw_picks(1, ID.IdCell(w, "K8", "b1"), b, 6000) if t[0] == "wrong"])  # noqa: E731
    d2, d8, dany = dist("idlocal2"), dist("idlocal8"), dist("anywhere")
    assert d2 < 3.3 and d2 < d8 < dany                                                                                                  # lambda 2 hugs the documented box, 8 is looser, uniform is widest


def test_runner_shapes_pairing_determinism_and_prefix():
    r = run()
    assert set(r["policy"]) == set(ID.POLICIES) and r["n"] == 40 and r["boxes"] == 20 and len(r["room_idx"]) == 40
    for p in r["policy"].values():
        assert np.isfinite(p["minutes"]).all() and (p["correct"] == (p["guess_idx"] == p["truth_idx"])).all() and p["truth_idx"].min() >= 0 and (p["off_list"] <= (r["truth_kind"] == "wrong")).all()
    again = run()
    assert all(np.array_equal(r["policy"][p][k], again["policy"][p][k]) for p in ID.POLICIES for k in ("minutes", "guess_idx", "checks", "off_list"))
    small, big = run(n=10), run(n=25)
    assert all(np.array_equal(small["policy"][p][k], big["policy"][p][k][:10]) for p in ID.POLICIES for k in ("minutes", "checks", "guess_idx", "truth_idx", "off_list", "named"))
    assert ID.g5_complete_id([r], n_cells=1, expected_idx=[2])[0]


def test_id_neighbours_recover_adjacent_room_errors_by_construction():
    r = run(world="idlocal2", n=300)
    off = {lv: r["policy"][f"entropy@{lv}"]["off_list"].mean() for lv in ID.LEVELS}
    assert off["idnear"] < 0.5 * off["min"] and off["idnear"] < off["grouped"]                                                      # the world that favours the id list, and it does
    anyw = run(world="anywhere", n=300)
    off_a = [anyw["policy"][f"entropy@{lv}"]["off_list"].mean() for lv in ID.LEVELS]
    assert max(off_a) - min(off_a) < 0.06                                                                                           # uniform errors: no list covers more than another in expectation


def test_min_and_grouped_levels_reproduce_addendum_23():
    b = make_layout()
    mine = [ID.run_id_cell(i, ID.IdCell(w, c, "b1"), b, n=40) for i, (w, c) in enumerate([("local", "K8"), ("anywhere", "K40")])]
    a23 = [SM.run_min_cell(i, SM.MinCell(w, c, "b1"), b, n=40) for i, (w, c) in enumerate([("local", "K8"), ("anywhere", "K40")])]
    assert ID.gate_g1_a23(mine, a23)[0] and ID.gate_g1_a23(mine, a23)[1].startswith("2 cells")


# ---------------------------------------------------------------------------------------------- analysis and predictions
def test_analysis_labels_and_keys():
    a = ID.analyze_id_cell(run(world="idlocal2", n=200), B=100)
    assert set(a["cmp"]) == {"idnear", "grouped"} and set(a["summary"]) == set(ID.POLICIES) and "actionable" in a["summary"]["entropy@min"] and a["cmp"]["idnear"]["label"] in ("IMPROVES", "WORSE", "TRADE", "NEITHER")
    same = ID.analyze_id_cell(run(world="anywhere", n=60), B=50)
    assert set(same["cmp"]["idnear"]) >= {"d_min", "d_acc", "d_act", "d_off", "label"}


def fake_inputs(override=None):
    """part_a, cov and analyses for three buildings, set by hand so that all six predictions hold."""
    o = override or {}
    part_a = {b: dict(consistent=o.get("consistent", 10), total=10, lift=dict(s_id=0.8, s_first=0.4, base=0.3, lift=2.6, n_handled=30, n_handlers=3, full=False)) for b in ("a", "b", "c")}
    part_a["d"] = dict(consistent=10, total=10, lift=dict(s_id=0.1, s_first=0.9, base=0.5, lift=0.2, n_handled=6, n_handlers=2, full=True))            # a full-list building does not count
    values = {("local", "K8"): (0.10, 0.105, 0.11), ("local", "K40"): (0.60, 0.62, 0.62), ("anywhere", "K8"): (0.10, 0.10, 0.10), ("anywhere", "K40"): (0.6, 0.6, 0.6),
              ("idlocal2", "K8"): (0.10, 0.90, 0.10), ("idlocal2", "K40"): (0.6, 0.95, 0.6), ("idlocal8", "K8"): (0.1, 0.5, 0.1), ("idlocal8", "K40"): (0.6, 0.8, 0.6)}
    cov, analyses = {}, []
    for (w, c), vals in {**values, **o.get("cov", {})}.items():
        for b in ("a", "b"):
            for lv, v in zip(ID.LEVELS, vals):
                cov[(b, w, c, lv)] = v
            act = o.get("act", {}).get((w, c), (0.86, 0.88, 0.88) if w != "anywhere" else (0.86, 0.86, 0.86))
            analyses.append(dict(cell=ID.IdCell(w, c, b), summary={f"entropy@{lv}": dict(actionable=a, off_list=0.1) for lv, a in zip(ID.LEVELS, act)}))
    if "lifts" in o:
        for b, lf in zip(("a", "b", "c"), o["lifts"]):
            part_a[b]["lift"] = dict(part_a[b]["lift"], **lf)
    return analyses, part_a, cov


def test_predictions_hold_and_fail_one_at_a_time():
    an, pa, cov = fake_inputs()
    pr = ID.id_predictions(an, pa, cov)
    assert all(v["holds"] for v in pr.values()) and set(pr) == {"P1", "P2", "P3", "P4", "P5", "P6"} and pr["P2"]["values"][2] == 3
    assert not ID.id_predictions(*fake_inputs({"consistent": 8}))["P1"]["holds"] and ID.id_predictions(*fake_inputs({"consistent": 9}))["P1"]["holds"]
    assert not ID.id_predictions(*fake_inputs({"lifts": [dict(s_id=0.3), dict(s_id=0.3), {}]}))["P2"]["holds"]                          # id beats first in only one of three
    assert not ID.id_predictions(*fake_inputs({"lifts": [dict(lift=1.2), dict(lift=1.2), dict(lift=1.2)]}))["P2"]["holds"]              # lift below 1.5
    assert not ID.id_predictions(*fake_inputs({"lifts": [dict(s_id=0.3), {}, {}]}))["P2"]["holds"]                                       # two of three is 0.67 < 0.70
    assert not ID.id_predictions(*fake_inputs({"cov": {("local", "K40"): (0.6, 0.6, 0.62)}}))["P3"]["holds"]                             # idnear must be strictly above min
    assert not ID.id_predictions(*fake_inputs({"cov": {("local", "K8"): (0.1, 0.12, 0.11)}}))["P3"]["holds"]                            # grouped must be at least idnear
    assert not ID.id_predictions(*fake_inputs({"cov": {("local", "K8"): (0.10, 0.20, 0.30)}}))["P4"]["holds"]                            # off-list shares 0.027 apart
    assert not ID.id_predictions(*fake_inputs({"cov": {("idlocal2", "K8"): (0.10, 0.50, 0.10)}}))["P5"]["holds"]
    assert not ID.id_predictions(*fake_inputs({"act": {("idlocal8", "K40"): (0.88, 0.88, 0.88)}}))["P6"]["holds"]                       # equal is not above


def test_p2_counts_only_buildings_with_more_than_eight_handled_boxes():
    an, pa, cov = fake_inputs()
    real = lambda beats: dict(consistent=10, total=10, lift=dict(s_id=0.8 if beats else 0.2, s_first=0.4, base=0.3, lift=2.6, n_handled=30, n_handlers=3, full=False))  # noqa: E731
    full = dict(consistent=10, total=10, lift=dict(s_id=0.1, s_first=0.9, base=0.5, lift=0.2, n_handled=6, n_handlers=2, full=True))
    part = {f"r{i}": real(i < 7) for i in range(10)} | {"f1": full, "f2": full, "none": dict(consistent=10, total=10, lift=None)}
    pr = ID.id_predictions(an, part, cov)["P2"]
    assert pr["holds"] and pr["values"][2] == 10 and np.isclose(pr["values"][0], 0.7)                                                       # 7 of the 10 real buildings; the two full ones are left out


# ---------------------------------------------------------------------------------------------- gates
def test_g1_gate_passes_and_catches_a_wrong_list(monkeypatch):
    b = make_layout()
    assert ID.gate_g1_idnear(b)[0]
    monkeypatch.setattr(ID, "id_near_list", lambda layout, doc, k: [doc] + [x for x in ID.boxes_in_id_order(layout) if x != doc][::-1][: k - 1])
    ok, msg = ID.gate_g1_idnear(b)
    assert not ok and "wrong" in msg


def test_g1_addendum_23_gate_catches_a_difference():
    b = make_layout()
    mine = [ID.run_id_cell(0, ID.IdCell("local", "K8", "b1"), b, n=30)]
    a23 = [SM.run_min_cell(0, SM.MinCell("local", "K8", "b1"), b, n=30)]
    assert ID.gate_g1_a23(mine, a23)[0]
    bad = [SM.run_min_cell(0, SM.MinCell("local", "K8", "b1"), b, n=30)]
    bad[0]["policy"]["entropy@grouped"]["minutes"] = bad[0]["policy"]["entropy@grouped"]["minutes"] + 1.0
    assert not ID.gate_g1_a23(mine, bad)[0]
    other = [SM.run_min_cell(0, SM.MinCell("anywhere", "K8", "b1"), b, n=30)]
    assert not ID.gate_g1_a23(mine, other)[0] and not ID.gate_g1_a23(mine, [])[0]                                                   # a different cell, or nothing to compare with


def test_coverage_gate_recomputes_the_off_list_flags():
    b = make_layout()
    layouts = {"b1": b}
    results = [run(world=w, cap=c, n=60, idx=i) for i, (w, c) in enumerate([("local", "K8"), ("idlocal2", "K8"), ("idlocal8", "K40")])]
    assert ID.gate_g3_coverage(results, layouts)[0]
    p = results[1]["policy"]["entropy@idnear"]
    p["off_list"] = ~p["off_list"]
    assert not ID.gate_g3_coverage(results, layouts)[0]
    small = make_layout(n=6, per=3)
    ok = run(world="anywhere", cap="K8", n=60, idx=0, layout=small)
    assert ok["policy"]["entropy@min"]["off_list"].sum() == 0 and ID.gate_g3_coverage([ok], {"b1": small})[0]
    ok["policy"]["entropy@idnear"]["off_list"] = ok["policy"]["entropy@idnear"]["off_list"].copy()
    ok["policy"]["entropy@idnear"]["off_list"][0] = True
    assert not ID.gate_g3_coverage([ok], {"b1": small})[0]


def test_exact_against_simulated_gate():
    cov = {(b, w, c, lv): 0.5 for b in ("a", "b") for w in ID.WORLDS for c in ID.CAPS for lv in ID.LEVELS}
    exact = ID.expected_off_list(0.5)                                                                                                # 0.0675
    n = 1000

    def fake_a23(share):
        out = []
        for w in ("local", "anywhere"):
            for c in ID.CAPS:
                k = int(round(share * n))
                off = np.arange(n) < k
                out.append(dict(cell=SM.MinCell(w, c, "a"), policy={"entropy@min": dict(off_list=off), "entropy@grouped": dict(off_list=off)}))
        return out

    assert ID.gate_g3_exact(cov, fake_a23(exact))[0]
    assert ID.gate_g3_exact(cov, fake_a23(exact + 0.005))[0] and not ID.gate_g3_exact(cov, fake_a23(exact + 0.02))[0] and not ID.gate_g3_exact(cov, [])[0]


def test_completeness_gate():
    r = run(n=12, idx=0)
    assert ID.g5_complete_id([r], n_cells=1)[0] and not ID.g5_complete_id([r], n_cells=2)[0] and not ID.g5_complete_id([], n_cells=1)[0]
    broken = run(n=12, idx=0)
    broken["policy"]["entropy@idnear"]["minutes"] = broken["policy"]["entropy@idnear"]["minutes"].copy()
    broken["policy"]["entropy@idnear"]["minutes"][0] = np.nan
    assert not ID.g5_complete_id([broken], n_cells=1)[0]
    missing = run(n=12, idx=0)
    del missing["policy"]["entropy@grouped"]
    assert not ID.g5_complete_id([missing], n_cells=1)[0]
    stray = run(world="local", n=40, idx=0)
    stray["policy"]["entropy@min"]["off_list"] = ~(stray["truth_kind"] == "wrong") | stray["policy"]["entropy@min"]["off_list"]
    assert not ID.g5_complete_id([stray], n_cells=1)[0]


# ---------------------------------------------------------------------------------------------- real data
@pytest.mark.skipif(not HAVE_DATA, reason="Mortar Brick files not cached")
def test_runs_on_a_real_layout():
    bc = C.parse_census(DATA / "mortar__bldg8.ttl", "bldg8")
    b, meta = R.layout_from_census(bc)
    cons, tot = ID.name_consistency(bc.pairs["vav_zone"])
    assert 0 < tot and 0 <= cons <= tot
    lift = ID.handler_lift(b)
    assert lift is None or (np.isfinite(lift["lift"]) and 0 <= lift["s_id"] <= 1)
    table = ID.coverage_table(b)
    assert len(table) == len(ID.WORLDS) * len(ID.CAPS) * len(ID.LEVELS) and all(0 <= v <= 1 for v in table.values())
    res = ID.run_id_cell(0, ID.IdCell("idlocal2", "K8", "bldg8"), b, n=8)
    assert ID.g5_complete_id([res], n_cells=1)[0] and ID.gate_g1_idnear(b)[0] and ID.gate_g3_coverage([res], {"bldg8": b})[0] and res["boxes"] == meta.boxes
