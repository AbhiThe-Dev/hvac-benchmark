"""Guards for the id-distance weighting (PREREGISTRATION_DR.md Addendum 25): the tool's `nearness = "id"` option (settings, candidate list, weights, the technician-added candidate, the CLI) and
the study (cells, levels, the extra world, the runner, analysis, predictions, decision, gates)."""
import sys
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("rdflib")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import census as C  # noqa: E402
from docmismatch.troubleshoot import Session, cli, make_case  # noqa: E402
from docmismatch.troubleshoot import building as B  # noqa: E402
from docmismatch.troubleshoot import idproximity as ID  # noqa: E402
from docmismatch.troubleshoot import model as M  # noqa: E402
from docmismatch.troubleshoot import realmaps as R  # noqa: E402
from docmismatch.troubleshoot import study_idweight as IW  # noqa: E402
from docmismatch.troubleshoot import study_minimum as SM  # noqa: E402

DATA = ROOT.parent / "data_cache"
HAVE_DATA = (DATA / "mortar__bldg8.ttl").exists()


def make_layout(n=20, per=5, prefix="VAV", pad=2):
    """Boxes `prefix`01..; handler blocks of `per` boxes; zone Zi <- box i."""
    nums = list(range(1, n + 1))
    box = {i: f"{prefix}{i:0{pad}d}" for i in nums}
    kinds = {box[i]: "VAV" for i in nums} | {f"Z{i:0{pad}d}": "Zone" for i in nums} | {f"AHU-{chr(65 + h)}": "AHU" for h in range((n + per - 1) // per)}
    vz = [(box[i], f"Z{i:0{pad}d}") for i in nums]
    av = [(f"AHU-{chr(65 + (i - 1) // per)}", box[i]) for i in nums]
    return R.layout_from_census(C.BrickCensus("b1", kinds, {}, {"vav_zone": vz, "ahu_vav": av, "coil_vav": [], "coil_ahu": []}))[0]


# ---------------------------------------------------------------------------------------------- the option: settings and candidates
def test_settings_default_to_the_existing_behaviour_and_are_validated():
    s = M.Settings()
    assert s.nearness == "area" and s.id_decay == 4.0 and s.with_drawings("poor").nearness == "area"
    assert M.Settings(nearness="id", id_decay=2.0).with_drawings("mostly_right").id_decay == 2.0 and M.Settings(nearness="id").with_drawings("poor").nearness == "id"
    with pytest.raises(ValueError):
        M.Settings(nearness="location")
    for bad in (0, -1.0):
        with pytest.raises(ValueError):
            M.Settings(id_decay=bad)


def test_natural_order_and_ranks_agree_with_the_idproximity_module():
    for layout in (make_layout(n=12, prefix="V", pad=1), make_layout(n=15), make_layout(n=6, per=2)):
        assert B.id_ranks(layout, "VAV") == ID.ranks(layout)
    lay = make_layout(n=12, prefix="V", pad=1)
    assert sorted(B.id_ranks(lay, "VAV"), key=B.id_ranks(lay, "VAV").get) == [f"V{i}" for i in range(1, 13)] and B.natural_key("V2") < B.natural_key("V10")
    assert B.id_ranks(make_layout(n=15), "AHU") == {"AHU-A": 0, "AHU-B": 1, "AHU-C": 2}


def test_candidates_in_id_mode_by_hand():
    b = make_layout(n=10)
    cands, w = B.candidates_for(b, "vav_zone", "VAV05", 4, M.Settings(nearness="id", id_decay=4.0))
    assert cands == ["VAV05", "VAV04", "VAV06", "VAV03"] and w["VAV05"] == 1.0
    assert np.isclose(w["VAV04"], np.exp(-0.25)) and np.isclose(w["VAV06"], np.exp(-0.25)) and np.isclose(w["VAV03"], np.exp(-0.5))
    cands2, w2 = B.candidates_for(b, "vav_zone", "VAV01", 100, M.Settings(nearness="id", id_decay=2.0))
    assert cands2 == ["VAV01"] + [f"VAV{i:02d}" for i in range(2, 11)] and np.isclose(w2["VAV10"], np.exp(-9 / 2))
    ahu, wa = B.candidates_for(make_layout(n=20), "ahu_vav", "AHU-B", 3, M.Settings(nearness="id"))                                   # the second connection type works the same way
    assert ahu == ["AHU-B", "AHU-A", "AHU-C"] and np.isclose(wa["AHU-C"], np.exp(-0.25))


def test_default_and_area_mode_are_unchanged():
    b = make_layout()
    for room in sorted(b.claims["vav_zone"]):
        plain, area = make_case(b, room, "vav_zone", None, max_candidates=8), make_case(b, room, "vav_zone", M.Settings(nearness="area"), max_candidates=8)
        assert (plain.candidates, plain.weights) == (area.candidates, area.weights)
    assert make_case(b, "Z10", "vav_zone", M.Settings(), max_candidates=8).candidates == ["VAV10", "VAV06", "VAV07", "VAV08", "VAV09", "VAV01", "VAV02", "VAV03"]        # same air handler first
    idc = make_case(b, "Z10", "vav_zone", M.Settings(nearness="id"), max_candidates=8)
    assert idc.candidates == ["VAV10", "VAV09", "VAV11", "VAV08", "VAV12", "VAV07", "VAV13", "VAV06"] and idc.doc == "VAV10" and idc.settings.nearness == "id"


def test_the_prior_follows_id_distance():
    b = make_layout()
    case = make_case(b, "Z10", "vav_zone", M.Settings(nearness="id", id_decay=2.0), max_candidates=8)
    causes, p = M.make_prior("vav_zone", case.candidates, case.doc, case.settings, None, case.weights)
    wrong = {c[1]: p[i] for i, c in enumerate(causes) if c[0] == "wrong"}
    assert wrong["VAV09"] == pytest.approx(wrong["VAV11"]) and wrong["VAV09"] > wrong["VAV08"] > wrong["VAV07"] > wrong["VAV06"] and np.isclose(p.sum(), 1.0)
    flat = make_case(b, "Z10", "vav_zone", M.Settings(nearness="id", id_decay=1e9), max_candidates=8)                                  # a huge decay is the equal-weight list
    fp = M.make_prior("vav_zone", flat.candidates, flat.doc, flat.settings, None, flat.weights)[1]
    assert np.allclose(sorted(fp[2:-1]), fp[2], atol=1e-6)


def test_a_candidate_the_technician_adds_gets_the_same_kind_of_weight():
    b = make_layout()
    s = Session(make_case(b, "Z05", "vav_zone", M.Settings(nearness="id", id_decay=4.0), max_candidates=4))
    s.add_candidate("VAV15")
    assert np.isclose(s.case.weights["VAV15"], np.exp(-10 / 4)) and "VAV15" in s.case.candidates
    a = Session(make_case(b, "Z05", "vav_zone", M.Settings(), max_candidates=4))                                                          # area mode: unchanged rule (1 in the area, else 0.25)
    a.add_candidate("VAV15")
    assert a.case.weights["VAV15"] == 0.25


def test_an_id_mode_session_suspects_the_nearest_candidate_first():
    b = make_layout()
    for decay, flat in ((2.0, False), (1e9, True)):
        s = Session(make_case(b, "Z10", "vav_zone", M.Settings(nearness="id", id_decay=decay), max_candidates=8))
        for check in ("override_room", "override_diffuser", "duct_trace"):
            s.report("no", check, "VAV10")                                                                                              # the documented box is not what feeds the room ...
        s.report("yes", "confirm_acts", "VAV10")                                                                                        # ... although it does move
        ranked = s.status()["ranked"]
        top, second = ranked[0], ranked[1]
        assert top[0][0] == "wrong" and second[0][0] == "wrong"
        if flat:
            assert np.isclose(top[1], ranked[4][1], atol=1e-3)                                                                          # equal weights: a near tie between candidates
        else:
            assert {top[0][1], second[0][1]} == {"VAV09", "VAV11"} and top[1] > 1.5 * ranked[4][1]                                       # the two nearest carry the most belief
            assert s.recommend().target in ("VAV09", "VAV11")


def test_cli_options_reach_the_case(monkeypatch, capsys):
    seen = []
    real = cli.make_case
    monkeypatch.setattr(cli, "make_case", lambda *a, **k: (seen.append(a[3]), real(*a, **k))[1])
    cli.main(["--demo"])
    cli.main(["--demo", "--nearness", "id", "--id-decay", "2.5", "--drawings", "mostly_right"])
    assert "[demo]" in capsys.readouterr().out
    assert [(x.nearness, x.id_decay, x.p_wrong) for x in seen] == [("area", 4.0, 0.15), ("id", 2.5, 0.05)]
    with pytest.raises(SystemExit):
        cli.main(["--demo", "--nearness", "location"])


# ---------------------------------------------------------------------------------------------- the study: cells, levels, worlds
def test_cells_levels_and_worlds():
    cells = IW.all_idw_cells(list(R.FROZEN_BUILDINGS))
    assert len(cells) == 250 and cells[-1] == IW.IdwCell("idlocal4", "K40", "bldg44") and cells[200] == IW.IdwCell("idlocal4", "K8", "bldg2")
    assert [IW.IdwCell(c.world, c.cap, c.building) for c in ID.all_id_cells(list(R.FROZEN_BUILDINGS))] == cells[:200]                    # the first 200 are Addendum 24's cells
    assert IW.LEVELS == ("min", "idnear", "idw2", "idw4", "idw8", "grouped") and IW.PRIMARY == "idw4" and IW.TOOL_DECAY == {"idw2": 2.0, "idw4": 4.0, "idw8": 8.0}
    assert IW.SEED == SM.SEED == ID.SEED == 23 and set(IW.ADJACENCY) == {"idlocal2", "idlocal4", "idlocal8"} and IW.DECAY["idlocal4"] == 4.0
    assert IW.PAIRS[0] == ("idnear", "min") and ("idw4", "idnear") in IW.PAIRS and len(IW.PAIRS) == 6


def test_the_id_levels_use_the_tools_own_option():
    b = make_layout()
    for lv, lam in IW.TOOL_DECAY.items():
        case = IW.assumed_case(b, "Z10", "K8", lv)
        assert case.settings.nearness == "id" and case.settings.id_decay == lam and case.candidates == ID.id_near_list(b, "VAV10", 8)
        assert np.isclose(case.weights["VAV08"], np.exp(-2 / lam))
    assert set(IW.assumed_case(b, "Z10", "K8", "idnear").weights.values()) == {1.0} and IW.assumed_case(b, "Z10", "K8", "idnear").settings == M.Settings()
    assert IW.assumed_case(b, "Z10", "K8", "min").candidates == SM.assumed_case(b, "Z10", "K8", "min").candidates
    assert IW.assumed_case(b, "Z10", "K8", "grouped").candidates == SM.assumed_case(b, "Z10", "K8", "grouped").candidates


def test_draws_of_the_first_four_worlds_are_addendum_24s_and_idlocal4_sits_between():
    b = make_layout()
    for world in ("local", "anywhere", "idlocal2", "idlocal8"):
        assert IW.draw_picks(3, IW.IdwCell(world, "K8", "b1"), b, 60) == ID.draw_picks(3, ID.IdCell(world, "K8", "b1"), b, 60), world
    rk = ID.ranks(b)
    dist = lambda w: np.mean([abs(rk[t[1]] - rk[b.claims["vav_zone"][room]]) for room, t in IW.draw_picks(1, IW.IdwCell(w, "K8", "b1"), b, 6000) if t[0] == "wrong"])  # noqa: E731
    assert dist("idlocal2") < dist("idlocal4") < dist("idlocal8") < dist("anywhere")
    assert IW.world_weights(b, "Z10", "idlocal4")["VAV12"] == pytest.approx(np.exp(-0.5))


# ---------------------------------------------------------------------------------------------- the runner
def run(world="idlocal2", cap="K8", n=40, idx=2, layout=None):
    return IW.run_idw_cell(idx, IW.IdwCell(world, cap, "b1"), layout or make_layout(), n=n)


def test_runner_shapes_pairing_determinism_and_prefix():
    r = run()
    assert set(r["policy"]) == set(IW.POLICIES) and r["n"] == 40 and r["boxes"] == 20
    for p in r["policy"].values():
        assert np.isfinite(p["minutes"]).all() and (p["correct"] == (p["guess_idx"] == p["truth_idx"])).all() and p["truth_idx"].min() >= 0 and (p["off_list"] <= (r["truth_kind"] == "wrong")).all()
    again = run()
    assert all(np.array_equal(r["policy"][p][k], again["policy"][p][k]) for p in IW.POLICIES for k in ("minutes", "guess_idx", "checks", "off_list"))
    small, big = run(n=10), run(n=25)
    assert all(np.array_equal(small["policy"][p][k], big["policy"][p][k][:10]) for p in IW.POLICIES for k in ("minutes", "checks", "guess_idx", "truth_idx", "off_list", "named"))
    assert IW.g5_complete_idw([r], n_cells=1, expected_idx=[2])[0]
    lists = [r["policy"][f"entropy@{lv}"]["off_list"] for lv in ("idnear", "idw2", "idw4", "idw8")]
    assert all(np.array_equal(lists[0], x) for x in lists[1:])                                                                          # the same list, so the same off-list episodes


def test_levels_share_outcome_streams(monkeypatch):
    monkeypatch.setitem(IW.TOOL_DECAY, "idw2", 4.0)                                                                                     # two levels with the same decay ...
    r = run(world="idlocal4", n=60)
    a, b = r["policy"]["entropy@idw2"], r["policy"]["entropy@idw4"]
    assert all(np.array_equal(a[k], b[k]) for k in ("minutes", "guess_idx", "checks", "concluded"))                                    # ... must give identical episodes
    assert not all(np.array_equal(r["policy"]["entropy@idw8"][k], b[k]) for k in ("minutes", "guess_idx", "checks"))


def test_min_idnear_and_grouped_reproduce_addendum_24():
    b = make_layout()
    mine = [IW.run_idw_cell(i, IW.IdwCell(w, c, "b1"), b, n=40) for i, (w, c) in enumerate([("local", "K8"), ("idlocal2", "K40")])]
    a24 = [ID.run_id_cell(i, ID.IdCell(w, c, "b1"), b, n=40) for i, (w, c) in enumerate([("local", "K8"), ("idlocal2", "K40")])]
    assert IW.gate_g1_a24(mine, a24) == (True, "2 cells reproduce Addendum 24 exactly")


def test_weighting_lets_the_tool_find_a_near_feeder_in_a_long_list():
    b = make_layout(n=30, per=5)
    r = IW.run_idw_cell(1, IW.IdwCell("idlocal2", "K40", "b1"), b, n=250)
    act = {lv: float((r["policy"][f"entropy@{lv}"]["correct"] & r["policy"][f"entropy@{lv}"]["named"]).mean()) for lv in IW.LEVELS}
    unres = {lv: float((~r["policy"][f"entropy@{lv}"]["concluded"]).mean()) for lv in IW.LEVELS}
    assert act["idw4"] > act["idnear"] + 0.03 and unres["idw4"] < unres["idnear"]                                                        # the point of the option (by construction of the world)
    assert act["idw2"] > act["idnear"]


# ---------------------------------------------------------------------------------------------- analysis, predictions, decision
def test_analysis_keys_and_labels():
    a = IW.analyze_idw_cell(run(world="idlocal4", n=120), B_=60)
    assert set(a["cmp"]) == {f"{t}|{b}" for t, b in IW.PAIRS} and set(a["summary"]) == set(IW.POLICIES) and "checks" in a["summary"]["entropy@idw4"]
    assert all(v["label"] in ("IMPROVES", "WORSE", "TRADE", "NEITHER") for v in a["cmp"].values())
    same = IW.analyze_idw_cell(run(world="anywhere", n=60), B_=50)
    assert same["cmp"]["idw2|idnear"]["d_off"] == 0                                                                                     # the same list: no difference in what is off it


LEVEL_DEFAULT = dict(min=(0.86, 0.02), idnear=(0.86, 0.02), idw2=(0.86, 0.02), idw4=(0.86, 0.02), idw8=(0.86, 0.02), grouped=(0.87, 0.02))       # (actionable, wrong-and-confident)


def fake_analyses(over=None, buildings=("a", "b")):
    """Analyses with hand-set group means so that P1-P6 all hold; `over[(world, cap, level)] = (actionable, wrong_confident)` replaces a group's values."""
    over, out = over or {}, []
    for w in IW.WORLDS:
        for c in IW.CAPS:
            vals = dict(LEVEL_DEFAULT)
            if w in IW.ADJACENCY and c == "K40":
                vals.update(idw2=(0.92, 0.02), idw4=(0.94, 0.02), idw8=(0.90, 0.02), idnear=(0.87, 0.02), min=(0.87, 0.02))
            vals.update({lv: v for (ww, cc, lv), v in over.items() if (ww, cc) == (w, c)})
            for b in buildings:
                out.append(dict(cell=IW.IdwCell(w, c, b), summary={f"entropy@{lv}": dict(actionable=a, wrong_confident=wc) for lv, (a, wc) in vals.items()}))
    return out


def test_predictions_hold_and_fail_one_at_a_time():
    pr = IW.idw_predictions(fake_analyses())
    assert all(v["holds"] for v in pr.values()) and set(pr) == {"P1", "P2", "P3", "P4", "P5", "P6"}
    assert not IW.idw_predictions(fake_analyses({("idlocal8", "K40", "idw4"): (0.87, 0.02)}))["P1"]["holds"]                             # equal is not above
    assert not IW.idw_predictions(fake_analyses({("idlocal2", "K40", "idw4"): (0.90, 0.02)}))["P2"]["holds"]                             # 0.03 above min only
    assert IW.idw_predictions(fake_analyses({("idlocal2", "K40", "idw4"): (0.91, 0.02)}))["P2"]["holds"]
    assert not IW.idw_predictions(fake_analyses({("anywhere", "K8", "idw4"): (0.84, 0.02)}))["P3"]["holds"]                              # 0.02 below min
    assert not IW.idw_predictions(fake_analyses({("anywhere", "K40", "idw4"): (0.86, 0.035)}))["P3"]["holds"]                            # confident-wrong up by 0.015
    assert IW.idw_predictions(fake_analyses({("anywhere", "K40", "idw4"): (0.86, 0.029)}))["P3"]["holds"]
    assert not IW.idw_predictions(fake_analyses({("local", "K40", "idw4"): (0.85, 0.02)}))["P4"]["holds"]                                # 0.01 below idnear
    assert IW.idw_predictions(fake_analyses({("local", "K40", "idw4"): (0.856, 0.02)}))["P4"]["holds"]
    assert not IW.idw_predictions(fake_analyses({("idlocal4", "K40", "idw2"): (0.87, 0.02)}))["P5"]["holds"]
    assert not IW.idw_predictions(fake_analyses({("idlocal4", "K40", "idw8"): (0.86, 0.02)}))["P5"]["holds"]
    assert not IW.idw_predictions(fake_analyses({("local", "K8", "idw4"): (0.86, 0.04)}))["P6"]["holds"]                                # confident-wrong 0.02 above idnear


def test_decision_rule():
    pr = IW.idw_predictions(fake_analyses())
    assert IW.decision(pr) == "WORTH KEEPING AS AN OPTION"
    for k in ("P1", "P3", "P6"):
        assert IW.decision({**pr, k: dict(pr[k], holds=False)}) == "NOT WORTH KEEPING", k
    for k in ("P2", "P4", "P5"):
        assert IW.decision({**pr, k: dict(pr[k], holds=False)}) == "WORTH KEEPING AS AN OPTION", k                                        # no verdict


# ---------------------------------------------------------------------------------------------- gates
def test_g1_gate_passes_and_catches_a_wrong_weight_or_list(monkeypatch):
    b = make_layout()
    assert IW.gate_g1_idw(b)[0]
    with monkeypatch.context() as m:
        m.setattr(B, "id_weight", lambda rd, ro, decay: 1.0)
        ok, msg = IW.gate_g1_idw(b)
        assert not ok and "weights" in msg
    with monkeypatch.context() as m:
        m.setattr(ID, "id_near_list", lambda layout, doc, k: [doc] + [x for x in ID.boxes_in_id_order(layout) if x != doc][::-1][: k - 1])
        ok, msg = IW.gate_g1_idw(b)
        assert not ok and "id-near" in msg


def test_g1_addendum_24_gate_catches_a_difference():
    b = make_layout()
    mine = [IW.run_idw_cell(0, IW.IdwCell("idlocal2", "K8", "b1"), b, n=30)]
    a24 = [ID.run_id_cell(0, ID.IdCell("idlocal2", "K8", "b1"), b, n=30)]
    assert IW.gate_g1_a24(mine, a24)[0]
    a24[0]["policy"]["entropy@idnear"]["minutes"] = a24[0]["policy"]["entropy@idnear"]["minutes"] + 1.0
    assert not IW.gate_g1_a24(mine, a24)[0] and not IW.gate_g1_a24(mine, [])[0]
    other = [ID.run_id_cell(0, ID.IdCell("anywhere", "K8", "b1"), b, n=30)]
    assert not IW.gate_g1_a24(mine, other)[0]


def test_g3_gate_recomputes_flags_and_checks_the_world_ordering(monkeypatch):
    b = make_layout(n=30)
    layouts = {"b1": b}
    worlds = ("idlocal2", "idlocal4", "idlocal8", "anywhere")
    results = [IW.run_idw_cell(i, IW.IdwCell(w, "K8", "b1"), b, n=200) for i, w in enumerate(worlds)]
    ok, msg = IW.gate_g3(results, layouts)
    assert ok and "idlocal2" in msg
    p = results[0]["policy"]["entropy@idw4"]
    p["off_list"] = ~p["off_list"]
    assert not IW.gate_g3(results, layouts)[0]
    p["off_list"] = ~p["off_list"]
    monkeypatch.setitem(IW.DECAY, "idlocal4", 40.0)                                                                                      # an adjacency world that is not ordered by distance
    assert not IW.gate_g3([IW.run_idw_cell(i, IW.IdwCell(w, "K8", "b1"), b, n=200) for i, w in enumerate(worlds)], layouts)[0]
    small = make_layout(n=6, per=3)
    ok_r = IW.run_idw_cell(0, IW.IdwCell("anywhere", "K8", "b1"), small, n=60)
    assert ok_r["policy"]["entropy@min"]["off_list"].sum() == 0


def test_completeness_gate():
    r = run(n=12, idx=0)
    assert IW.g5_complete_idw([r], n_cells=1)[0] and not IW.g5_complete_idw([r], n_cells=2)[0] and not IW.g5_complete_idw([], n_cells=1)[0]
    broken = run(n=12, idx=0)
    broken["policy"]["entropy@idw4"]["minutes"] = broken["policy"]["entropy@idw4"]["minutes"].copy()
    broken["policy"]["entropy@idw4"]["minutes"][0] = np.nan
    assert not IW.g5_complete_idw([broken], n_cells=1)[0]
    missing = run(n=12, idx=0)
    del missing["policy"]["entropy@idw8"]
    assert not IW.g5_complete_idw([missing], n_cells=1)[0]
    stray = run(world="local", n=40, idx=0)
    stray["policy"]["entropy@min"]["off_list"] = ~(stray["truth_kind"] == "wrong") | stray["policy"]["entropy@min"]["off_list"]
    assert not IW.g5_complete_idw([stray], n_cells=1)[0]


# ---------------------------------------------------------------------------------------------- real data
@pytest.mark.skipif(not HAVE_DATA, reason="Mortar Brick files not cached")
def test_runs_on_a_real_layout():
    b, meta = R.load_layout(DATA / "mortar__bldg8.ttl", "bldg8")
    res = IW.run_idw_cell(0, IW.IdwCell("idlocal4", "K40", "bldg8"), b, n=8)
    assert IW.g5_complete_idw([res], n_cells=1)[0] and IW.gate_g1_idw(b)[0] and res["boxes"] == meta.boxes
    assert IW.gate_g3([res], {"bldg8": b})[0] is False                                                                                  # one cell cannot order four worlds: a clean False, not a crash
