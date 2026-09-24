"""Guards for the caution-check metrics (PREREGISTRATION_DR.md Addendum 12)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.dr import caution_eval as C  # noqa: E402


def _r(ep, wrong, crossed, correct=True, n=5):
    return dict(ep=ep, wrong=wrong, crossed=crossed, correct=correct, n=n)


def test_summarize_counts_resolution_and_balances_accuracy_over_classes():
    rows = [_r("a", True, True, True), _r("b", True, True, False), _r("c", True, False),      # wrong episodes: 2 resolved, 1 right of 2
            _r("d", False, True, True), _r("e", False, False)]                                # right episodes: 1 resolved, all correct
    s = C.summarize(rows)
    assert s["n"] == 5 and s["n_resolved"] == 3
    assert s["resolved"] == pytest.approx(0.6)
    assert s["acc_resolved"] == pytest.approx((0.5 + 1.0) / 2)                                 # class-balanced, not pooled (2/3)
    assert s["wrong_confident"] == pytest.approx(1 / 5)


def test_summarize_handles_no_resolved_and_empty():
    s = C.summarize([_r("a", True, False)])
    assert s["resolved"] == 0.0 and s["acc_resolved"] != s["acc_resolved"]                    # NaN accuracy, not 0
    assert C.summarize([])["n"] == 0


def test_flips_are_matched_on_episode_id():
    base = [_r("a", True, False), _r("b", True, True, True), _r("c", True, True, False), _r("z", True, True)]
    other = [_r("a", True, True), _r("b", True, False), _r("c", True, True, True), _r("new", True, True)]
    f = C.flips(base, other)
    assert f == dict(gained=1, lost=1, correct_to_wrong=0, wrong_to_correct=1, common=3)


def test_verdict_rule():
    base = dict(resolved=0.40, acc_resolved=0.95)
    assert C.verdict(base, dict(resolved=0.55, acc_resolved=0.93)) == "WORTH PURSUING"
    assert C.verdict(base, dict(resolved=0.55, acc_resolved=0.80)).startswith("REJECTED")
    assert C.verdict(base, dict(resolved=0.45, acc_resolved=0.99)) == "INERT"
