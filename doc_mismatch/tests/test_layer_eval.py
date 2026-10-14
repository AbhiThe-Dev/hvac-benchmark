"""Guards for the layer-evaluation metrics and frozen reading rules (PREREGISTRATION_DR.md Addendum 14)."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.dr import layer_eval as L  # noqa: E402


def _rows(spec, slot="s", cluster_mod=4):
    """spec = [(documentation_is_wrong, state, count), ...]; CONFIRMED means 'the document is right'."""
    out, k = [], 0
    for wrong, state, n in spec:
        for _ in range(n):
            out.append(dict(ep=f"e{k}", slot=slot, wrong=wrong, state=state, say_correct=(state == "CONFIRMED"), cluster=f"c{k % cluster_mod}"))
            k += 1
    return out


def test_summarize_counts_and_class_balancing():
    rows = _rows([(True, "REFUTED", 2), (True, "CONFIRMED", 1), (True, "FLAGGED", 1),      # wrong docs: 2 right, 1 missed fault, 1 abstained
                  (False, "CONFIRMED", 3), (False, "REFUTED", 1)])                          # right docs: 3 right, 1 false alarm
    s = L.summarize(rows)
    assert s["n"] == 8 and s["n_answered"] == 7
    assert s["coverage"] == pytest.approx((3 / 4 + 4 / 4) / 2)
    assert s["acc_answered"] == pytest.approx((2 / 3 + 3 / 4) / 2)
    assert s["wrong_confident"] == pytest.approx(2 / 8)
    assert s["false_alarm"] == pytest.approx(1 / 4)
    assert s["missed_fault"] == pytest.approx(1 / 4)


def test_summarize_handles_empty_and_nothing_answered():
    assert L.summarize([])["n"] == 0
    s = L.summarize(_rows([(True, "FLAGGED", 3), (False, "FLAGGED", 3)]))
    assert s["n_answered"] == 0 and s["coverage"] == 0.0 and np.isnan(s["acc_answered"]) and s["wrong_confident"] == 0.0


def test_retained_is_share_of_the_plain_rules_correct_answers():
    plain = _rows([(True, "REFUTED", 6), (False, "CONFIRMED", 4)])
    layer = _rows([(True, "REFUTED", 3), (False, "FLAGGED", 1), (False, "CONFIRMED", 1)])
    assert L.retained(layer, plain) == pytest.approx(4 / 10)
    assert np.isnan(L.retained(layer, _rows([(True, "CONFIRMED", 3)])))                     # plain got none right


def _plain_bad(n_correct_each=6):
    """a plain rule with a problem: answers every episode, accuracy among answered 0.6 (class-balanced)"""
    return _rows([(True, "REFUTED", n_correct_each), (True, "CONFIRMED", 4), (False, "CONFIRMED", n_correct_each), (False, "REFUTED", 4)])


def test_verdict_fixes_when_honest_and_keeps_value():
    layer = _rows([(True, "REFUTED", 6), (True, "FLAGGED", 4), (False, "CONFIRMED", 6), (False, "FLAGGED", 4)])
    assert L.slot_verdict(_plain_bad(), layer) == "FIXES"


def test_verdict_honest_but_empty_when_it_keeps_too_little_of_the_value():
    plain = _rows([(True, "REFUTED", 40), (True, "CONFIRMED", 10), (False, "CONFIRMED", 40), (False, "REFUTED", 10)])   # 80 correct answers, accuracy 0.8 (a problem)
    layer = _rows([(True, "REFUTED", 6), (True, "FLAGGED", 38), (False, "CONFIRMED", 6), (False, "FLAGGED", 38)])   # 12 correct = 15% retained
    assert L.slot_verdict(plain, layer) == "HONEST BUT EMPTY"


def test_verdict_abstains_when_too_few_answers_to_judge():
    layer = _rows([(True, "REFUTED", 3), (True, "FLAGGED", 7), (False, "CONFIRMED", 3), (False, "FLAGGED", 7)])
    assert L.slot_verdict(_plain_bad(), layer).startswith("ABSTAINS")


def test_verdict_does_not_fix_when_answered_verdicts_are_still_wrong():
    layer = _rows([(True, "REFUTED", 6), (True, "CONFIRMED", 6), (False, "CONFIRMED", 6), (False, "REFUTED", 6)])
    assert L.slot_verdict(_plain_bad(), layer) == "DOES NOT FIX"


def test_verdict_no_problem_when_plain_rule_is_already_honest():
    plain = _rows([(True, "REFUTED", 10), (False, "CONFIRMED", 10)])
    assert L.slot_verdict(plain, plain) == "NO PROBLEM TO FIX"


def test_overall_rules():
    assert L.overall(["FIXES", "FIXES", "DOES NOT FIX"]) == "the layer REMOVES THE OVERCONFIDENCE"
    assert L.overall(["HONEST BUT EMPTY", "ABSTAINS -- too few answers to judge (honest but empty)", "FIXES"]) == "the layer SILENCES RATHER THAN FIXES"
    assert L.overall(["NO PROBLEM TO FIX", "NO PROBLEM TO FIX", "DOES NOT FIX"]).startswith("the overconfidence was mostly an artefact")
    assert L.overall(["DOES NOT FIX", "DOES NOT FIX", "FIXES"]) == "the layer does NOT remove the overconfidence"


def test_boot_interval_brackets_the_point_estimate_and_needs_two_clusters():
    rows = _rows([(True, "REFUTED", 20), (True, "CONFIRMED", 4), (False, "CONFIRMED", 20), (False, "REFUTED", 4)], cluster_mod=6)
    lo, hi = L.boot_acc_answered(rows, B=200, seed=0)
    assert lo <= L.summarize(rows)["acc_answered"] <= hi
    assert np.isnan(L.boot_acc_answered(_rows([(True, "REFUTED", 5)], cluster_mod=1))[0])
