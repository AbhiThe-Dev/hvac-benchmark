"""Smoke tests of the matrix pipeline at a small n (the full run is scripts/02_build_matrix.py)."""
import csv
import json

import pytest

from hotwater_dx import causes as C
from hotwater_dx import checks as K
from hotwater_dx import matrix as MX
from hotwater_dx.report import write_all, write_model_limits


@pytest.fixture(scope="module")
def small(tmp_path_factory):
    saved = dict(MX.THRESHOLDS)
    MX.THRESHOLDS.update(MIN_APPLICABLE=8, GATE_MIN=8)
    w = MX.build_world(n_theta=40, seed=3)
    cells = MX.build_matrix(w)
    pairs = MX.pair_confusion(w)
    inter = MX.interactions(w, n_pairs=20)
    out = tmp_path_factory.mktemp("out")
    write_all(out, w, cells, pairs, inter)
    write_model_limits(out, len(C.INTERACTIONS))
    yield w, cells, out
    MX.THRESHOLDS.clear()
    MX.THRESHOLDS.update(saved)


def test_every_cell_present_once_with_provenance(small):
    w, cells, _ = small
    keys = [(c.cause, c.check) for c in cells]
    assert len(keys) == len(set(keys)) == len(C.CAUSES) * len(K.CHECKS)
    assert all(c.provenance for c in cells) and all(c.cls in MX.TIER for c in cells)


def test_non_physics_checks_are_elicitation_or_declared_null(small):
    _, cells, _ = small
    for c in cells:
        if c.check in ("K04", "K20"):
            assert c.cls in ("NEEDS_ELIC", "DET_NOT_SEEN") and c.provenance == "analyst"


def test_fixture_local_is_invisible_to_plant_level_checks(small):
    _, cells, _ = small
    by = {(c.cause, c.check): c for c in cells}
    for k in ("K01", "K05", "K07", "K08", "K10"):
        assert by[("fixture_branch_local", k)].cls in ("DET_NOT_SEEN", "N/A")
    assert by[("fixture_branch_local", "K16")].cls == "DET_SEEN"


def test_pump_failure_is_seen_by_amps(small):
    _, cells, _ = small
    by = {(x.cause, x.check): x for x in cells}
    assert by[("pump_failed", "K08")].cls == "DET_SEEN"                 # forced on: a dead pump still draws no current
    assert by[("pump_control_fault", "K08")].cls != "DET_SEEN"          # a control fault does not show in the pump itself
    assert by[("pump_control_fault", "K10")].cls == "DET_SEEN"


def test_outputs_exist_carry_the_disclaimer_and_hash(small):
    _, _, out = small
    for name in ("matrix.json", "matrix.csv", "MATRIX_REPORT.md", "uncertain_cells.csv", "pairs_confusion.csv", "pair_interactions.csv", "parameter_leverage.csv", "model_limits.md"):
        assert "NOT FIELD EVIDENCE" in (out / name).read_text(), name
    meta = json.loads((out / "matrix.json").read_text())["meta"]
    assert meta["thresholds_hash"] == MX.thresholds_hash()


def test_same_seed_same_matrix():
    saved = dict(MX.THRESHOLDS)
    MX.THRESHOLDS.update(MIN_APPLICABLE=8, GATE_MIN=8)
    try:
        a = MX.build_matrix(MX.build_world(n_theta=24, seed=9, causes=("crossover", "pump_failed")), tools_alt=False)
        b = MX.build_matrix(MX.build_world(n_theta=24, seed=9, causes=("crossover", "pump_failed")), tools_alt=False)
        assert [(c.cls, round(c.median_z, 6) if c.median_z == c.median_z else 0) for c in a] == [(c.cls, round(c.median_z, 6) if c.median_z == c.median_z else 0) for c in b]
    finally:
        MX.THRESHOLDS.clear()
        MX.THRESHOLDS.update(saved)


def test_uncertain_list_sorted_conflicts_first(small):
    _, _, out = small
    rows = list(csv.reader(open(out / "uncertain_cells.csv")))[2:]
    assert rows and [int(r[0]) for r in rows] == list(range(1, len(rows) + 1))

