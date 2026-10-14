"""Guards for the real-layout study (PREREGISTRATION_DR.md Addendum 20): layout extraction, candidate regimes, worlds, the cell runner, the secondary label, predictions and gates."""
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
from docmismatch.troubleshoot import study_real as SR  # noqa: E402
from docmismatch.troubleshoot.building import make_case  # noqa: E402

DATA = ROOT.parent / "data_cache"
HAVE_DATA = (DATA / "mortar__bldg8.ttl").exists()


def fake_census(name="b1"):
    """AHU-A feeds V1-V3, AHU-B feeds V4-V5, V6 has no handler; Z1..Z6 <- V1..V6; Z7 is documented under two boxes (V7, V8)."""
    kinds = {f"V{i}": "VAV" for i in range(1, 9)} | {f"Z{i}": "Zone" for i in range(1, 8)} | {"AHU-A": "AHU", "AHU-B": "AHU"}
    vz = [(f"V{i}", f"Z{i}") for i in range(1, 7)] + [("V7", "Z7"), ("V8", "Z7")]
    av = [("AHU-A", f"V{i}") for i in (1, 2, 3)] + [("AHU-B", "V4"), ("AHU-B", "V5"), ("AHU-A", "V7"), ("AHU-B", "V7"), ("AHU-B", "V8")]
    return C.BrickCensus(name, kinds, {}, {"vav_zone": vz, "ahu_vav": av, "coil_vav": [], "coil_ahu": []})


def layout():
    return R.layout_from_census(fake_census())


# ---------------------------------------------------------------------------------------------- layout extraction
def test_layout_from_documentation():
    b, meta = layout()
    assert (meta.rooms, meta.boxes, meta.handlers, meta.boxes_without_handler, meta.rooms_with_several_boxes) == (7, 8, 2, 1, 1)
    e = b.equipment
    assert e["V1"].area == "AHU-A" and e["V4"].area == "AHU-B" and e["V6"].area is None and e["V7"].area == "AHU-A"      # several handlers: the lowest identifier
    assert e["Z1"].area == "AHU-A" and e["Z6"].area is None and e["Z7"].kind == "Zone" and e["AHU-A"].kind == "AHU"
    assert b.claims["vav_zone"]["Z7"] == "V7"                                                # documented under V7 and V8: the first in identifier order
    assert b.claims["ahu_vav"]["V7"] == "AHU-A" and "V6" not in b.claims["ahu_vav"]
    assert [k for k, v in e.items() if v.kind == "VAV"] == [f"V{i}" for i in range(1, 9)]      # boxes come first, in identifier order
    assert R.building_number("bldg10") == 10 and R.building_number("bldg2") == 2


def test_candidate_regimes_on_a_layout():
    b, _ = layout()
    c = make_case(b, "Z1", "vav_zone", M.Settings(), max_candidates=8)
    assert c.candidates == ["V1", "V2", "V3", "V7", "V4", "V5", "V6", "V8"]                    # documented, then the rest of its handler, then the other handlers
    assert [c.weights[x] for x in c.candidates] == [1, 1, 1, 1, 0.25, 0.25, 0.25, 0.25]
    assert make_case(b, "Z1", "vav_zone", M.Settings(), max_candidates=3).candidates == ["V1", "V2", "V3"]
    nohandler = make_case(b, "Z6", "vav_zone", M.Settings(), max_candidates=8)                  # no area for the documented box: flat weights
    assert nohandler.candidates[0] == "V6" and set(nohandler.weights.values()) == {1.0}
    assert R.layout_problems("b1", b, fake_census(), {"R": 3, "R8": 8}) == []


def test_layout_problems_are_detected():
    b, _ = layout()
    bc = fake_census()
    del b.claims["vav_zone"]["Z2"]
    assert any("rooms differ" in p for p in R.layout_problems("b1", b, bc))
    b2, _ = layout()
    b2.claims["vav_zone"]["Z2"] = "V-not-there"
    assert any("not documented" in p for p in R.layout_problems("b1", b2, bc))
    b3, _ = layout()
    b3.equipment.pop("V5")
    assert any("box count" in p or "not documented" in p for p in R.layout_problems("b1", b3, bc))


def test_eligibility_reads_documented_rooms_in_numeric_order(tmp_path):
    def ttl(n):
        vs = ", ".join(f"ns:V{i}" for i in range(n))
        body = "\n".join(f"ns:V{i} a brick:VAV ; brick:feeds ns:Z{i} . ns:Z{i} a brick:HVACZone ." for i in range(n))
        return ("@prefix brick: <https://brickschema.org/schema/Brick#> .\n@prefix ns: <urn:t/c#> .\n" f"ns:AHU01 a brick:Air_Handler_Unit ; brick:feeds {vs} .\n{body}\n")
    for name, n in (("bldg10", 13), ("bldg2", 12), ("bldg3", 11), ("bldg1", 2)):
        (tmp_path / f"mortar__{name}.ttl").write_text(ttl(n))
    assert R.eligible(tmp_path) == ["bldg2", "bldg10"]                                        # numeric order, and 12 rooms is enough
    b, meta = R.load_layout(tmp_path / "mortar__bldg10.ttl", "bldg10")
    assert (meta.rooms, meta.boxes, meta.handlers) == (13, 13, 1) and len(b.claims["vav_zone"]) == 13


@pytest.mark.skipif(not HAVE_DATA, reason="Mortar Brick files not present")
def test_the_frozen_building_list_and_layout_fidelity_on_the_real_files():
    assert tuple(R.eligible(DATA)) == R.FROZEN_BUILDINGS and len(R.FROZEN_BUILDINGS) == 25
    for name in R.FROZEN_BUILDINGS:
        bc = C.parse_census(DATA / f"mortar__{name}.ttl", name)
        b, meta = R.layout_from_census(bc)
        assert R.layout_problems(name, b, bc) == [], name
        assert meta.rooms >= 12 and meta.rooms_with_several_boxes == 0
    facts = {n: R.load_layout(DATA / f"mortar__{n}.ttl", n)[1] for n in ("bldg8", "bldg11", "bldg30", "bldg5")}
    assert (facts["bldg8"].rooms, facts["bldg8"].handlers) == (24, 1) and (facts["bldg11"].rooms, facts["bldg11"].handlers) == (394, 9)
    assert (facts["bldg30"].rooms, facts["bldg30"].handlers) == (99, 2) and facts["bldg5"].boxes_without_handler == 4


# ---------------------------------------------------------------------------------------------- worlds, cells, runner
def test_worlds_regimes_and_cell_order():
    assert SR.REGIMES == {"R_narrow": 8, "R_wide": 40} and list(SR.WORLDS) == ["W_default", "W_documented", "W_stress"]
    d, doc, st = (S.true_settings(SR.WORLDS[w]) for w in SR.WORLDS)
    assert (d.p_wrong, d.p_acts_fail) == (0.15, 0.15) and d.menu("vav_zone") == M.MENUS["vav_zone"]
    assert (doc.p_wrong, doc.p_acts_fail) == (0.05, 0.15) and doc.menu("vav_zone") == M.MENUS["vav_zone"]
    assert (st.p_wrong, st.p_acts_fail) == (0.30, 0.30) and st.menu("vav_zone")[0] == M.MENUS["vav_zone"][0] and st.menu("vav_zone")[2].tpr < 0.9
    cells = SR.all_real_cells(list(R.FROZEN_BUILDINGS))
    assert len(cells) == 150 and cells[0] == SR.RealCell("W_default", "R_narrow", "bldg2") and cells[-1] == SR.RealCell("W_stress", "R_wide", "bldg44")
    assert cells[25].regime == "R_wide" and cells[50].world == "W_documented" and cells[24].building == "bldg44"


def test_cell_runner_pairs_truths_is_prefix_stable_and_reproducible():
    b, _ = layout()
    spec = SR.RealCell("W_default", "R_narrow", "b1")
    r = SR.run_real_cell(3, spec, b, n=25)
    for name in S.POLICIES:
        p = r["policy"][name]
        assert len(p["minutes"]) == 25 and np.array_equal(p["truth_idx"], r["policy"]["entropy"]["truth_idx"])
        assert ((p["guess_idx"] == p["truth_idx"]) == p["correct"]).all()                    # indices refer to the same per-room cause list
    assert r["rooms"] == 7 and set(r["K"]) <= {8.0} and np.isfinite(r["policy"]["habit_B"]["minutes"]).all()
    again, short = SR.run_real_cell(3, spec, b, n=25), SR.run_real_cell(3, spec, b, n=10)
    for name in S.POLICIES:
        for k in ("minutes", "checks", "correct", "concluded", "guess_idx", "truth_idx"):
            assert np.array_equal(r["policy"][name][k], again["policy"][name][k]) and np.array_equal(r["policy"][name][k][:10], short["policy"][name][k])
    assert S.g5_complete([r], expected_idx=[3]) == (True, "ok")


def test_parallel_matches_serial():
    b, _ = layout()
    jobs = [(1, SR.RealCell("W_default", "R_narrow", "b1"), b), (2, SR.RealCell("W_stress", "R_wide", "b1"), b)]
    ser, par = SR.compute_real_cells(jobs, n=12, workers=1), SR.compute_real_cells(jobs, n=12, workers=2)
    for a, c in zip(ser, par):
        assert a["idx"] == c["idx"] and all(np.array_equal(a["policy"][n]["minutes"], c["policy"][n]["minutes"]) for n in S.POLICIES)


@pytest.mark.skipif(not HAVE_DATA, reason="Mortar Brick files not present")
def test_candidate_counts_on_a_real_building():
    b, _ = R.load_layout(DATA / "mortar__bldg8.ttl", "bldg8")                              # 24 rooms, 24 boxes, one handler
    narrow = SR.run_real_cell(0, SR.RealCell("W_default", "R_narrow", "bldg8"), b, n=20)
    wide = SR.run_real_cell(1, SR.RealCell("W_default", "R_wide", "bldg8"), b, n=20)
    assert set(narrow["K"]) == {8.0} and set(wide["K"]) == {24.0} and narrow["rooms"] == 24


# ---------------------------------------------------------------------------------------------- gates
def test_g1_and_g2_on_a_real_layout():
    b, _ = layout()
    assert SR.gate_g1_real(b, n=15)[0] and SR.gate_g2_real(b, n=10)[0]


def test_g3_honesty_real():
    def cell(world, regime, acc, conc=0.9):
        n = 100
        correct = np.zeros(n, bool)
        correct[: int(acc * n)] = True
        return dict(cell=SR.RealCell(world, regime, "b"), policy={"entropy": dict(correct=correct, concluded=np.ones(n, bool) if conc == 1 else np.arange(n) < int(conc * n))})
    ok, vals = SR.g3_honesty_real([cell("W_default", "R_narrow", 0.97, 1), cell("W_default", "R_wide", 0.95, 1), cell("W_stress", "R_wide", 0.5, 1)])
    assert ok and vals["R_narrow"] == 0.97 and vals["R_wide"] == 0.95                          # only W_default counts
    assert not SR.g3_honesty_real([cell("W_default", "R_narrow", 0.97, 1), cell("W_default", "R_wide", 0.80, 1)])[0]
    assert not SR.g3_honesty_real([cell("W_default", "R_narrow", 0.97, 1)])[0]                 # a regime with no cells cannot pass
    assert not SR.g3_honesty_real([])[0]


# ---------------------------------------------------------------------------------------------- secondary label, groups, predictions
def test_secondary_label():
    e = lambda label, r, d, ci: dict(label=label, r_min=r, d_acc=d, ci_acc=ci)  # noqa: E731
    assert SR.secondary_label(e("WINS", -0.3, 0.0, (-0.1, 0.1))) == "WINS" and SR.secondary_label(e("LOSES", 0.3, -0.1, (-0.2, 0.0))) == "LOSES"
    assert SR.secondary_label(e("NEITHER", 0.65, 0.18, (0.15, 0.21))) == "BUYS ACCURACY"
    assert SR.secondary_label(e("NEITHER", 0.09, 0.18, (0.15, 0.21))) == "NEITHER"           # not slower by 10%
    assert SR.secondary_label(e("NEITHER", 0.65, 0.04, (0.01, 0.07))) == "NEITHER"           # not 5 points more accurate
    assert SR.secondary_label(e("NEITHER", 0.65, 0.18, (-0.01, 0.30))) == "NEITHER"          # the interval touches zero


def fake_analyses(entropy_label=lambda w, r: "NEITHER", vs_b=lambda w, r: "NEITHER", wrong_conf=lambda w, r: 0.03, acc=lambda w, r: (0.9, 0.7)):
    out = []
    for i, c in enumerate(SR.all_real_cells(["b1", "b2"])):
        w, r = c.world, c.regime
        summ = {p: dict(wrong_confident=0.0, accuracy=0.8, minutes=30.0) for p in S.POLICIES}
        summ["entropy"] = dict(wrong_confident=wrong_conf(w, r), accuracy=acc(w, r)[0], minutes=40.0)
        summ["habit_A"] = dict(wrong_confident=0.0, accuracy=acc(w, r)[1], minutes=20.0)
        cmp_ = {f"{t}|{h}": dict(label="NEITHER") for t in S.TOOL for h in S.HABITS}
        cmp_["entropy|habit_B"] = dict(label=vs_b(w, r))
        out.append(dict(idx=i, cell=c, summary=summ, cmp=cmp_, label={"entropy": entropy_label(w, r), "split_half": "NEITHER", "random": "NEITHER"}))
    return out


def test_groups_and_readings():
    a = fake_analyses(entropy_label=lambda w, r: "WINS" if w == "W_documented" else "NEITHER")
    g = SR.groups(a)
    assert len(g) == 6 and all(len(v) == 2 for v in g.values())
    assert SR.group_reading(g[("W_documented", "R_wide")], "entropy") == (1.0, 0.0, "HELPS BROADLY")
    assert SR.group_reading(g[("W_default", "R_wide")], "entropy") == (0.0, 0.0, "DOES NOT HELP")


def test_predictions_follow_their_registered_definitions():
    p = SR.real_predictions(fake_analyses(vs_b=lambda w, r: "WINS" if (w == "W_documented" and r == "R_wide") else "NEITHER",
                                          wrong_conf=lambda w, r: 0.08 if w == "W_stress" else 0.02))
    assert p["P1"]["holds"] and p["P2"]["holds"] and p["P3"]["holds"] and p["P4"]["holds"] and p["P5"]["holds"]
    assert not SR.real_predictions(fake_analyses(entropy_label=lambda w, r: "WINS" if (w, r) == ("W_stress", "R_narrow") else "NEITHER"))["P1"]["holds"]    # one group with a win
    assert not SR.real_predictions(fake_analyses())["P2"]["holds"]                                                    # no world differs
    assert not SR.real_predictions(fake_analyses(vs_b=lambda w, r: "WINS" if r == "R_narrow" else "NEITHER"))["P3"]["holds"]
    assert not SR.real_predictions(fake_analyses(wrong_conf=lambda w, r: 0.05))["P4"]["holds"]                     # equal is not higher
    assert not SR.real_predictions(fake_analyses(acc=lambda w, r: (0.6, 0.7) if (w, r) == ("W_default", "R_wide") else (0.9, 0.7)))["P5"]["holds"]
