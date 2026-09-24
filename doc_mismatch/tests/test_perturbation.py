"""Guards for the setpoint-perturbation identification statistic (PREREGISTRATION_DR.md Addendum 13)."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.dr import perturbation as P  # noqa: E402


def _world(n=4, T=240, gain=0.6, seed=0, decoys=True):
    """Zone m's setpoint drives ONLY box m (negatively on flow, positively on t_dis); every box also carries a shared daily swing plus own noise."""
    rng = np.random.default_rng(seed)
    U = 24 + 1.5 * rng.choice([-1, 1], size=(n, T // 2)).repeat(2, axis=1)
    diurnal = np.sin(2 * np.pi * np.arange(T) / 24)
    flow = 5 + 2 * diurnal + rng.normal(0, 0.3, (n, T))
    tdis = 13 + 0.5 * diurnal + rng.normal(0, 0.2, (n, T))
    for m in range(n):
        flow[m] -= gain * (U[m] - 24)
        tdis[m] += 0.3 * gain * (U[m] - 24) * (0 if decoys and m == 0 else 1)   # box 0 responds on flow only: the max over signals must still find it
    return U, {"flow": flow, "t_dis": tdis}, np.arange(n)


def test_corr_matrix_matches_numpy_and_is_zero_for_constant_rows():
    rng = np.random.default_rng(1)
    U, Y = rng.normal(size=(3, 50)), rng.normal(size=(4, 50))
    C = P.corr_matrix(U, Y)
    assert C[1, 2] == pytest.approx(np.corrcoef(U[1], Y[2])[0, 1])
    Y[0] = 3.0
    assert np.all(P.corr_matrix(U, Y)[:, 0] == 0.0)


def test_identifies_the_driven_box_and_uses_either_signal():
    U, Y, truth = _world()
    assert P.rank1(P.scores(U, Y), truth) == 1.0


def test_more_noise_lowers_accuracy_and_none_is_deterministic():
    U, Y, truth = _world(n=6, T=120, gain=0.15)
    a_none = P.sweep(U, Y, truth, [120], "none", 5, 0)[120]
    a_none2 = P.sweep(U, Y, truth, [120], "none", 5, 99)[120]
    a_harsh = P.sweep(U, Y, truth, [120], "harsh", 30, 0)[120]
    assert a_none == a_none2
    assert a_harsh <= a_none


def test_short_campaign_is_less_reliable_than_long_one():
    U, Y, truth = _world(n=8, T=288, gain=0.25, seed=3)
    acc = P.sweep(U, Y, truth, [12, 288], "legacy", 20, 1)
    assert acc[288] >= acc[12]
    assert acc[288] > 1 / 8 + 0.3            # far above chance with the full campaign


def test_rank1_shares_credit_on_exact_ties():
    S = np.ones((2, 4))
    assert P.rank1(S, np.array([0, 3])) == pytest.approx(0.25)


def test_no_excitation_is_no_better_than_chance():
    rng = np.random.default_rng(5)
    n, T = 8, 240
    U = np.full((n, T), 24.0)                                    # setpoint never moves: corr is 0 everywhere -> all ties
    Y = {"flow": 5 + rng.normal(size=(n, T)), "t_dis": 13 + rng.normal(size=(n, T))}
    assert P.rank1(P.scores(U, Y), np.arange(n)) == pytest.approx(1 / n)


def test_campaign_arrays_drops_the_warmup_hours():
    T, pre = 100, 48
    ev = {"Z-1|sp_cool": np.arange(T, dtype=float), "V-1|flow": np.arange(T) * 2.0, "V-1|t_dis": np.arange(T) * 3.0}
    U, Y = P.campaign_arrays(ev, ["Z-1"], ["V-1"], pre)
    assert U.shape == (1, T - pre) and Y["flow"][0, 0] == pre * 2.0
