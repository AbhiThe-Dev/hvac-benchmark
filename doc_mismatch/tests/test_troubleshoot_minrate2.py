"""Tests for Addendum 36: does the live default (min_rate = 0.015) hold up across tiers and cells? No LLM. Simulation only. Mirrors test_troubleshoot_minrate.py (Addendum 35) but this
module (study_minrate2.py) is frozen separately, so its own tests are separate too."""
import numpy as np
import pytest

from docmismatch.troubleshoot.v2 import study_joint as J
from docmismatch.troubleshoot.v2 import study_minrate2 as M


@pytest.fixture(scope="module")
def three_cells():
    cells = list(enumerate(J.all_cells()))[:3]
    return M.compute_cells(cells, n=20, workers=1)


def test_challenger_is_addendum_36s_frozen_value_and_the_live_default_has_since_moved_past_it():
    """`study_minrate2.CHALLENGER` is frozen at 0.015 forever -- it is what Addendum 36's own stored report is about, and must stay reproducible against that report regardless of what the
    live tool's own default becomes later. It was equal to the live default when Addendum 36 was written (2026-09-27); it no longer is (`v2/cli.py` moved the live default to 0.02 on
    2026-09-29, a later, separate, disclosed decision -- see PREREGISTRATION_DR.md's "Further decision taken" note following the min_rate-tuning result)."""
    from docmismatch.troubleshoot.v2 import cli as V2CLI
    from docmismatch.troubleshoot.v2 import study_minrate as M35
    assert M.CHALLENGER == 0.015
    assert M.CHALLENGER != V2CLI.LIVE_MIN_RATE_DEFAULT
    assert M.CHALLENGER != M35.CHALLENGER
    assert M.BASE_MIN_RATE == M35.BASE_MIN_RATE == 0.003


def test_cases_with_only_changes_min_rate():
    base = M.cases_with("T2", M.BASE_MIN_RATE)
    chal = M.cases_with("T2", M.CHALLENGER)
    r = 3
    assert base[r].min_rate == M.BASE_MIN_RATE and chal[r].min_rate == M.CHALLENGER
    assert base[r].settings.tau == chal[r].settings.tau == 0.95
    assert base[r].doc == chal[r].doc and base[r].candidates == chal[r].candidates and base[r].checks == chal[r].checks


def test_run_cell_has_every_tier_and_grid_point():
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
    for out in three_cells:
        for t in M.TIERS:
            for r in M.GRID:
                v = out[(t, r)]
                assert (v["wc"] >= -1e-9).all() and (v["wc"] <= 1 + 1e-9).all(), (out["idx"], t, r)
                assert (v["acc"] >= -1e-9).all() and (v["acc"] <= 1 + 1e-9).all()
                assert (v["conc"] >= -1e-9).all() and (v["conc"] <= 1 + 1e-9).all()


def test_challenger_never_asks_more_than_baseline(three_cells):
    for out in three_cells:
        for t in M.TIERS:
            b, c = out[(t, M.BASE_MIN_RATE)], out[(t, M.CHALLENGER)]
            assert (c["checks"] <= b["checks"] + 1e-9).all()
            assert (c["minutes"] <= b["minutes"] + 1e-9).all()


def test_challenger_never_asks_more_than_addendum_35s_confirmed_value(three_cells):
    """0.015 is a stricter bar than 0.01: it must never do MORE than the 0.01 variant would (a monotonicity sanity check across the two frozen modules)."""
    from docmismatch.troubleshoot.v2 import study_minrate as M35
    for idx, cell in list(enumerate(J.all_cells()))[:3]:
        out35 = M35.run_cell(idx, cell, n=20)
        out36 = M.run_cell(idx, cell, n=20)
        for t in M.TIERS:
            assert (out36[(t, M.CHALLENGER)]["minutes"] <= out35[(t, M35.CHALLENGER)]["minutes"] + 1e-9).all()


def test_compare_against_self_is_a_null_result(three_cells):
    out = three_cells[0]
    v = out[("T2", M.BASE_MIN_RATE)]
    idx = np.arange(len(v["minutes"]))
    boot = np.random.default_rng(0).integers(0, len(idx), (200, len(idx)))
    c = M.compare(v, v, idx, boot)
    assert c["d_min"] == 0.0 and c["d_acc"] == 0.0 and c["d_wc"] == 0.0 and c["label"] == "NEITHER"


def test_analyze_cell_shape(three_cells):
    an = M.analyze_cell(three_cells[0], B=100)
    assert set(an) == {"idx", "cell", "n", "counts", "sum", "cmp"}
    for t in M.TIERS:
        for r in M.GRID:
            for sub in M.SUBSETS:
                assert (t, r, sub) in an["sum"]
        for sub in M.SUBSETS:
            assert (t, M.BASE_MIN_RATE, sub) not in an["cmp"]
            if an["counts"][sub] > 0:
                assert (t, M.CHALLENGER, sub) in an["cmp"]


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
        c = M.compare(base, base, idxa, boot)
        return dict(idx=idx, cell=J.Cell(shared="assumed", map="M0", rel="R0"), n=n, counts={}, sum={}, cmp={("T2", M.CHALLENGER, "all"): c, ("T3", M.CHALLENGER, "all"): c})

    analyses = [flat_cell(i) for i in range(18)]
    assert M.decision(analyses, p6_ok=True) == "NOT CONFIRMED"


def test_gate_g3():
    assert M.gate_g3()[0]


def test_gate_g5_true_and_false_cases(three_cells):
    a = three_cells
    assert M.gate_g5(a, a)[0]
    b = [{**o, ("T2", M.CHALLENGER): dict(o[("T2", M.CHALLENGER)], minutes=o[("T2", M.CHALLENGER)]["minutes"] + 1)} for o in a]
    assert not M.gate_g5(a, b)[0]


def test_check_p6_matches_and_mismatches():
    primary = J.all_cells()[[c.is_primary for c in J.all_cells()].index(True)]
    an = [dict(idx=0, cell=primary, sum={("T2", M.CHALLENGER, "all"): dict(minutes=M.REF_T2_MIN, accuracy=M.REF_T2_ACC), ("T3", M.CHALLENGER, "all"): dict(minutes=M.REF_T3_MIN, accuracy=M.REF_T3_ACC)})]
    ok, _ = M.check_p6(an)
    assert ok
    an_bad = [dict(idx=0, cell=primary, sum={("T2", M.CHALLENGER, "all"): dict(minutes=M.REF_T2_MIN + 10, accuracy=M.REF_T2_ACC), ("T3", M.CHALLENGER, "all"): dict(minutes=M.REF_T3_MIN, accuracy=M.REF_T3_ACC)})]
    ok2, _ = M.check_p6(an_bad)
    assert not ok2
    ok3, detail3 = M.check_p6([dict(idx=0, cell=J.Cell(shared="rare", map="M0", rel="R0"), sum={})])
    assert not ok3 and "not among the cells run" in detail3
