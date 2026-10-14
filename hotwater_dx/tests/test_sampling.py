import numpy as np

from hotwater_dx.params import PARAMS
from hotwater_dx.sampling import design_matrix, lhs_unit, substream


def test_lhs_has_one_point_per_stratum():
    u = lhs_unit(50, 7, np.random.default_rng(0))
    for j in range(7):
        assert sorted((u[:, j] * 50).astype(int)) == list(range(50))


def test_design_matrix_is_reproducible_and_in_range():
    a, b = design_matrix(40, 3), design_matrix(40, 3)
    assert a == b
    for d in a:
        for p in PARAMS:
            assert p.low <= d[p.name] <= p.high


def test_substreams_are_independent_of_call_order():
    x = substream(1, 2, 3).random()
    substream(1, 9, 9).random()
    assert substream(1, 2, 3).random() == x
