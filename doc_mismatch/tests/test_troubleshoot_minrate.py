"""Tests for Addendum 35: does the min_rate lead of Addendum 34 hold up across tiers and cells? No LLM. Simulation only."""
import numpy as np
import pytest

from docmismatch.troubleshoot.v2 import study_joint as J
from docmismatch.troubleshoot.v2 import study_minrate as M


@pytest.fixture(scope="module")
def three_cells():
    cells = list(enumerate(J.all_cells()))[:3]
    return M.compute_cells(cells, n=20, workers=1)


def test_cases_with_only_changes_min_rate():
    bld = None
    base = M.cases_with("T2", M.BASE_MIN_RATE)
    chal = M.cases_with("T2", M.CHALLENGER)
    r = 3
    assert base[r].min_rate == M.BASE_MIN_RATE and chal[r].min_rate == M.CHALLENGER
    assert base[r].settings.tau == chal[r].settings.tau == 0.95
    assert base[r].doc == chal[r].doc and base[r].candidates == chal[r].candidates and base[r].checks == chal[r].checks


def test_cases_with_both_tiers_differ_in_data_items():
    t2 = M.cases_with("T2", M.BASE_MIN_RATE)
    t3 = M.cases_with("T3", M.BASE_MIN_RATE)
    assert "bas_access" not in t2[0].items and "bas_access" in t3[0].items


def test_run_cell_has_every_tier_and_grid_point(three_cells):
    idx0, cell0 = 0, J.all_cells()[0]
    out = M.run_cell(idx0, cell0, n=20)
    assert set(out) >= {"idx", "cell", "n", "kind"} | {(t, r) for t in M.TIERS for r in M.GRID}
    assert len(out["kind"]) == 20
    for t in M.TIERS:
        for r in M.GRID:
            v = out[(t, r)]
            assert set(v) == {"minutes", "checks", "correct", "wc", "concluded", "n", "acc", "conc"}
            assert len(v["minutes"]) == 20


def test_wc_and_acc_and_conc_are_rates_not_counts(three_cells):
    """A visit's wc, acc and conc must be in [0, 1] (a rate per complaint), never a raw count > 1."""
    for out in three_cells:
        for t in M.TIERS:
            for r in M.GRID:
                v = out[(t, r)]
                assert (v["wc"] >= -1e-9).all() and (v["wc"] <= 1 + 1e-9).all(), (out["idx"], t, r)
                assert (v["acc"] >= -1e-9).all() and (v["acc"] <= 1 + 1e-9).all()
                assert (v["conc"] >= -1e-9).all() and (v["conc"] <= 1 + 1e-9).all()
                # a visit with several complaints and a nonzero wc must show a fraction, not an integer >= 2
                multi = out["kind"] != "single"
                if multi.any():
                    assert not np.any((v["wc"][multi] > 1 + 1e-9))


def test_challenger_never_asks_more_than_baseline(three_cells):
    for out in three_cells:
        for t in M.TIERS:
            b, c = out[(t, M.BASE_MIN_RATE)], out[(t, M.CHALLENGER)]
            assert (c["checks"] <= b["checks"] + 1e-9).all()
            assert (c["minutes"] <= b["minutes"] + 1e-9).all()


def test_compare_against_self_is_a_null_result(three_cells):
    out = three_cells[0]
    v = out[("T2", M.BASE_MIN_RATE)]
    idx = np.arange(len(v["minutes"]))
    boot = np.random.default_rng(0).integers(0, len(idx), (200, len(idx)))
    c = M.compare(v, v, idx, boot)
    assert c["d_min"] == 0.0 and c["d_acc"] == 0.0 and c["d_wc"] == 0.0 and c["label"] == "NEITHER"


def test_analyze_cell_shape_and_baseline_rows_absent_from_cmp(three_cells):
    an = M.analyze_cell(three_cells[0], B=100)
    assert set(an) == {"idx", "cell", "n", "counts", "sum", "cmp"}
    for t in M.TIERS:
        for r in M.GRID:
            for sub in M.SUBSETS:
                assert (t, r, sub) in an["sum"]
        for sub in M.SUBSETS:
            assert (t, M.BASE_MIN_RATE, sub) not in an["cmp"]                # only the challenger is compared; the baseline is not compared with itself
            if an["counts"][sub] > 0:
                assert (t, M.CHALLENGER, sub) in an["cmp"]                   # a subset with no events at all (e.g. no shared-cause draw in a tiny sample) has no comparison


def test_shares_and_cell_of_delegate_to_study_joint(three_cells):
    analyses = [M.analyze_cell(o, B=100) for o in three_cells]
    sh = M.shares(analyses, ("T2", M.CHALLENGER, "all"))
    assert set(sh) >= {"IMPROVES", "WORSE", "TRADE", "NEITHER", "SAFETY_REGRESSION", "SAFETY_GAIN", "n_cells"}
    assert sh["n_cells"] == 3
    c0 = analyses[0]["cell"]
    got = M.cell_of(analyses, shared=c0.shared, map=c0.map, rel=c0.rel)
    assert got["idx"] == analyses[0]["idx"]


def test_predictions_and_decision_shapes(three_cells):
    analyses = [M.analyze_cell(o, B=100) for o in three_cells]
    p = M.predictions(analyses)
    assert set(p) == {f"P{k}" for k in range(1, 6)}
    assert all(isinstance(v[0], (bool, np.bool_)) for v in p.values())
    assert M.decision(analyses, p6_ok=False).startswith("NO RESULT")
    d = M.decision(analyses, p6_ok=True)
    assert d in ("CONFIRMED", "CONFIRMED, UNSAFE UNDER MAP FAULTS", "NOT CONFIRMED")


def test_decision_is_confirmed_when_every_cell_is_cheap_and_safe():
    n = 200

    def cell(idx, delta_min=0.0, delta_wc=0.0, map_="M0"):
        base = dict(minutes=np.full(n, 100.0), checks=np.full(n, 10.0), correct=np.full(n, 0.8), wc=np.full(n, 0.01), concluded=np.full(n, 0.9), n=np.ones(n))
        base["acc"], base["conc"] = base["correct"], base["concluded"]
        chal = dict(base, minutes=np.full(n, 100.0 + delta_min), wc=np.full(n, 0.01 + delta_wc))
        idxa = np.arange(n)
        boot = np.zeros((1, n), int)
        return dict(idx=idx, cell=J.Cell(shared="assumed", map=map_, rel="R0"), n=n, counts={}, sum={},
                    cmp={("T2", M.CHALLENGER, "all"): M.compare(chal, base, idxa, boot), ("T3", M.CHALLENGER, "all"): M.compare(chal, base, idxa, boot)})

    analyses = [cell(i, delta_min=-10.0) for i in range(18)]
    assert M.decision(analyses, p6_ok=True) == "CONFIRMED"


def test_decision_is_not_confirmed_when_most_cells_are_not_faster():
    n = 200

    def flat_cell(idx):
        base = dict(minutes=np.full(n, 100.0), checks=np.full(n, 10.0), correct=np.full(n, 0.8), wc=np.full(n, 0.01), concluded=np.full(n, 0.9), n=np.ones(n))
        base["acc"], base["conc"] = base["correct"], base["concluded"]
        idxa = np.arange(n)
        boot = np.zeros((1, n), int)
        c = M.compare(base, base, idxa, boot)                                # identical to baseline: NEITHER, not IMPROVES
        return dict(idx=idx, cell=J.Cell(shared="assumed", map="M0", rel="R0"), n=n, counts={}, sum={}, cmp={("T2", M.CHALLENGER, "all"): c, ("T3", M.CHALLENGER, "all"): c})

    analyses = [flat_cell(i) for i in range(18)]
    assert M.decision(analyses, p6_ok=True) == "NOT CONFIRMED"


def test_decision_flags_unsafe_under_map_faults():
    n = 200

    def cell(idx, map_, regress):
        base = dict(minutes=np.full(n, 100.0), checks=np.full(n, 10.0), correct=np.full(n, 0.8), wc=np.full(n, 0.01), concluded=np.full(n, 0.9), n=np.ones(n))
        base["acc"], base["conc"] = base["correct"], base["concluded"]
        chal = dict(base, minutes=np.full(n, 90.0), wc=np.full(n, 0.01 + (0.10 if regress else 0.0)))
        idxa = np.arange(n)
        boot = np.zeros((1, n), int)
        c = M.compare(chal, base, idxa, boot)
        return dict(idx=idx, cell=J.Cell(shared="assumed", map=map_, rel="R0"), n=n, counts={}, sum={}, cmp={("T2", M.CHALLENGER, "all"): c, ("T3", M.CHALLENGER, "all"): c})

    analyses = [cell(i, "M0", regress=False) for i in range(6)] + [cell(i + 6, "M1", regress=True) for i in range(6)] + [cell(i + 12, "M2", regress=True) for i in range(6)]
    assert M.decision(analyses, p6_ok=True) == "CONFIRMED, UNSAFE UNDER MAP FAULTS"


def test_gate_g1_flags_a_deliberate_mismatch():
    """Against the real stored Addendum 30 file (needed for the suite to run at all): a wrong `idx` fails, a wrong `kind` at a real idx fails, a correct one passes."""
    ok_missing, _ = M.gate_g1([dict(idx=-1, kind=np.array(["single"] * 60))], n=50)
    assert not ok_missing
    ok_wrong, detail = M.gate_g1([dict(idx=0, kind=np.array(["shared"] * 60))], n=50)
    assert not ok_wrong and "mismatches" in detail


def test_gate_g3():
    assert M.gate_g3()[0]


def test_gate_g5_true_and_false_cases(three_cells):
    a = three_cells
    assert M.gate_g5(a, a)[0]
    b = [{**o, ("T2", M.CHALLENGER): dict(o[("T2", M.CHALLENGER)], minutes=o[("T2", M.CHALLENGER)]["minutes"] + 1)} for o in a]
    assert not M.gate_g5(a, b)[0]


def test_check_p6_matches_and_mismatches():
    an = [dict(idx=0, cell=J.all_cells()[[c.is_primary for c in J.all_cells()].index(True)], sum={("T2", M.BASE_MIN_RATE, "all"): dict(minutes=100.0), ("T2", M.CHALLENGER, "all"): dict(minutes=70.0)})]
    ok, _ = M.check_p6(an, dict(base_minutes=100.0, chal_minutes=70.1))
    assert ok
    ok2, _ = M.check_p6(an, dict(base_minutes=100.0, chal_minutes=50.0))
    assert not ok2
    ok3, detail3 = M.check_p6(an, None)
    assert not ok3 and "not found" in detail3
