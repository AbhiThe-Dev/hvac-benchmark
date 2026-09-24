"""Guards for the model-free diagnosability ladder (PREREGISTRATION_DR.md Addendum 11)."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.dr import diagnosability as D  # noqa: E402


# ---------------------------------------------------------------------------------------------- auroc / dprime
def test_auroc_perfect_reversed_and_chance():
    assert D.auroc_x_above_m(np.array([0.0, 0.1]), np.array([1.0, 2.0])) == 1.0
    assert D.auroc_x_above_m(np.array([1.0, 2.0]), np.array([0.0, 0.1])) == 0.0
    rng = np.random.default_rng(0)
    a = D.auroc_x_above_m(rng.normal(size=4000), rng.normal(size=4000))
    assert a == pytest.approx(0.5, abs=0.03)


def test_auroc_all_ties_is_exactly_half():
    assert D.auroc_x_above_m(np.zeros(5), np.zeros(7)) == 0.5


def test_auroc_empty_class_is_nan():
    assert np.isnan(D.auroc_x_above_m(np.array([]), np.array([1.0])))


def test_dprime_sign_and_scale():
    ym = np.array([0.0, 2.0, 0.0, 2.0])      # mean 1, sd ~1.155
    yx = ym + 2.3094                          # shifted by 2 sd
    assert D.dprime(ym, yx) == pytest.approx(2.0, abs=0.01)
    assert D.dprime(yx, ym) < 0
    assert np.isnan(D.dprime(np.zeros(3), np.zeros(3)))


# ---------------------------------------------------------------------------------------------- class_rows / rank1
def _world(sep: float, n_slices=12, n_mem=5, seed=0):
    """E[s, ch, o, m]: true pair error small, alternatives larger by `sep` (in log space), plus noise."""
    rng = np.random.default_rng(seed)
    E = np.full((n_slices, 3, n_mem, n_mem), np.nan)
    for m in range(n_mem):
        for o in range(n_mem):
            base = 0.2 if o == m else 0.2 * np.exp(sep)
            E[:, :, o, m] = base * np.exp(rng.normal(0, 0.1, (n_slices, 3)))
    truth = np.arange(n_mem)
    cands = [list(range(n_mem)) for _ in range(n_mem)]
    group = np.repeat(np.arange(3), n_slices // 3)
    return E, truth, cands, group


def test_class_rows_split_true_vs_alternative():
    E, truth, cands, _ = _world(1.0, n_slices=6, n_mem=4)
    ym, yx = D.class_rows(E, truth, cands, 0)
    assert len(ym) == 4 * 6 and len(yx) == 4 * 3 * 6
    assert ym.mean() < yx.mean()


def test_rank1_is_perfect_when_separated_and_near_chance_when_not():
    E, truth, cands, group = _world(2.0)
    hi = D.rank1_accuracy(E, truth, cands, group, (0, 1, 2))
    assert hi["acc"] == 1.0 and hi["chance"] == pytest.approx(0.2)
    E0, truth, cands, group = _world(0.0, n_slices=12, n_mem=5, seed=3)
    lo = D.rank1_accuracy(E0, truth, cands, group, (0, 1, 2), pooled=True)
    assert lo["acc"] == pytest.approx(0.2, abs=0.25)   # 5 units, coin-flip territory; guards "not spuriously ~1"
    assert lo["acc"] < 1.0


def test_rank1_all_tied_counts_expected_value_not_index_order():
    E = np.full((6, 3, 4, 4), 0.5)          # every pair identical: no information
    truth = np.arange(4)
    cands = [list(range(4))] * 4
    r = D.rank1_accuracy(E, truth, cands, np.zeros(6, dtype=int), (1,))
    assert r["acc"] == pytest.approx(0.25)


def test_rank1_skips_units_with_a_wholly_missing_candidate():
    E, truth, cands, group = _world(2.0, n_slices=6, n_mem=3)
    E[:, :, 1, 0] = np.nan                  # candidate 1 has no reading at all for member 0
    r = D.rank1_accuracy(E, truth, cands, group, (0,), pooled=True)
    assert r["n_skipped"] == 1 and r["n_units"] == 2


def test_boot_mean_drops_nan_and_reports_n():
    r = D.boot_mean([0.5, 0.7, float("nan")], B=50)
    assert r["n"] == 2 and r["est"] == pytest.approx(0.6)
    assert np.isnan(D.boot_mean([float("nan")])["est"])


# ---------------------------------------------------------------------------------------------- consistency with the real pool builder
def test_legacy_builder_reproduces_the_cached_legacy_pool():
    from docmismatch.data import load_base
    from docmismatch.dr.pools import load_pool
    base = load_base("dev_F")
    p = load_pool("dev_F", 0, "legacy")
    slot = "loop_branch"
    E = D.build_E(base, D.level_evidence(base, "legacy", 0), slot)
    ref = p.slots[slot].E[:, :3]
    # the pool applies channel masking (NaN where a channel's inputs are constant); the ladder does not -- so wherever the pool is finite the values must match
    fin = np.isfinite(ref)
    assert fin.any() and np.allclose(E[fin], ref[fin], equal_nan=False)
