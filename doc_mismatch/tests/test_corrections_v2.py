"""Tests for the v2 corrections and the real-data module."""
import numpy as np

from docmismatch import real_frp as R
from docmismatch.classify import CaseData, regime_support, row_keep, unsupported_positive, _stats
from docmismatch.evaluate import CAL_QUANTILE, _cal_threshold
from docmismatch.evidence import make_evidence, pair_errors
from docmismatch.features import FEATURE_NAMES, case_rows

IA, IC = FEATURE_NAMES.index("has_par_alt"), FEATURE_NAMES.index("has_child_alt")


def test_constant_terminal_channels_are_missing_not_scored(bases):
    """Topology B's constant-volume terminals: flow is one value all year, so flow-based channels must be NaN."""
    b = bases["sys03_psz_ac"]
    ev = make_evidence(b, 2, 5)
    o, m = b.slot_edges["vav_zone"][0]
    e = pair_errors(b, ev, "vav_zone", o, m, ctx=__import__("docmismatch.evidence", fromlist=["x"]).make_context(b, ev))
    assert np.isnan(e[0]) and np.isnan(e[2]), "flow-based channels of a constant-flow VAV must be missing"
    assert not np.isnan(e[1]), "the discharge-temperature channel still varies and must stay valid"
    a = bases["sys07_vav_reheat"]
    ea = make_evidence(a, 2, 5)
    oa, ma = a.slot_edges["ahu_vav"][0]
    assert not np.isnan(pair_errors(a, ea, "ahu_vav", oa, ma)[1]), "a genuinely varying flow must not be masked"


def test_missing_flags_reach_the_features(cases, bases):
    c = next(c for c in cases if c["topology_id"] == "sys03_psz_ac" and c["label"] == 0)
    rows = case_rows(bases["sys03_psz_ac"], c)
    i = FEATURE_NAMES.index("ch0_missing")
    assert any(r["kind"] == "edge" and r["slot"] == "vav_zone" and r["x"][i] == 1.0 for r in rows)


def _cd(slot, ia, ic, n, pos_rows=()):
    X = np.zeros((n, len(FEATURE_NAMES)), np.float32)
    X[:, IA], X[:, IC] = ia, ic
    y = np.zeros(n, np.float32)
    for p in pos_rows:
        y[p] = 1.0
    return CaseData({}, X, y, ["edge"] * n, [slot] * n, None, None)


def test_regime_support_drops_unseen_regimes_in_both_directions():
    train = {"a": _cd("loop_branch", 0, 1, 40), "b": _cd("vav_zone", 1, 1, 40)}
    sup = regime_support(["a", "b"], train)
    assert ("loop_branch", 0, 1) in sup and ("loop_branch", 1, 1) not in sup
    test_with_alt = _cd("loop_branch", 1, 1, 5, pos_rows=(2,))       # C-like: loop membership has alternatives, training never did
    test_no_alt = _cd("vav_zone", 0, 0, 5, pos_rows=(1,))            # A-like: no alternatives, training always had some
    assert len(row_keep(test_with_alt, sup)) == 0 and unsupported_positive(test_with_alt, sup)
    assert len(row_keep(test_no_alt, sup)) == 0 and unsupported_positive(test_no_alt, sup)
    assert not unsupported_positive(_cd("vav_zone", 1, 1, 5, pos_rows=(1,)), sup)


def test_standardization_cannot_explode():
    """v1 floored sd at 1e-3, so a training-constant column that is non-zero at test became ~1000 sigma."""
    cds = [type("R", (), {"X": np.zeros((50, 3), np.float32)})()]
    mu, sd = _stats(cds, [0, 1, 2])
    assert (sd >= 0.1).all()


def test_calibration_threshold_is_a_high_quantile_of_many_clean_scores():
    sc = {f"c{i}": float(i) for i in range(100)}
    thr = _cal_threshold(sc, list(sc))
    assert 88 <= thr <= 91 and CAL_QUANTILE == 0.90


def test_real_stats_are_nan_aware():
    a = np.array([1.0, 2.0, 3.0] + [np.nan] * 200)
    assert np.isnan(R.pcorr(a, a)), "fewer than MIN_VALID pairwise-valid bins must give NaN, not a number"
    x = np.arange(100.0)
    y = x.copy(); y[::3] = np.nan
    assert abs(R.pcorr(x, y) - 1.0) < 1e-9, "gaps must be dropped pairwise"
    assert not R.informative(np.full(100, 5.0), 1.0) and not R.informative(np.full(100, np.nan), 1.0)


def test_real_events_are_degree_preserving_swaps():
    ev = R.all_events()
    assert len(ev) == 4 * 45 and len({e.id for e in ev}) == len(ev)
    S = {s: np.zeros((10, 10)) for s in R.SLOTS}
    S["vav_zone"][0, 1] = S["vav_zone"][1, 0] = 5.0      # only the swapped (wrong) edges look suspicious
    e = R.Event("vav_zone", 0, 1)
    assert R.doc_score(S, e) == 5.0 and R.doc_score(S, None) == 0.0
