"""Guards for wiring the dither campaign into the verdict logic (PREREGISTRATION_DR.md Addendum 15, Part B)."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.dr import campaign_eval as C  # noqa: E402


def _S(n=6, gap=0.6, seed=0, noise=0.05):
    """scores where each zone's true box is `gap` above the rest, plus noise"""
    rng = np.random.default_rng(seed)
    S = 0.2 + noise * rng.normal(size=(n, n))
    S[np.arange(n), np.arange(n)] += gap
    return S, np.arange(n)


def test_fit_kappa_rises_with_the_separation_of_the_scores():
    lo = C.fit_kappa(*map(lambda x: [x], _S(gap=0.15, noise=0.15, seed=1)))[0]
    hi = C.fit_kappa(*map(lambda x: [x], _S(gap=0.6, noise=0.05, seed=1)))[0]
    assert hi >= lo and lo < 200


def test_fit_kappa_handles_buildings_with_different_numbers_of_boxes():
    (S6, t6), (S10, t10), (S12, t12) = _S(n=6, seed=1), _S(n=10, seed=2), _S(n=12, seed=3)
    k, _ = C.fit_kappa([S6, S10, S12], [t6, t10, t12])
    assert k in C.KAPPA_GRID
    k_sep, _ = C.fit_kappa([S6, S10], [t6, t10])                                # the pooled fit is a sum of per-building softmax log-likelihoods
    single = sum(C.log_softmax(k_sep * S)[np.arange(len(t)), t].sum() for S, t in [(S6, t6), (S10, t10)])
    assert np.isfinite(single)


def test_fit_kappa_flags_a_perfectly_separated_training_set_as_unbounded():
    S, t = _S(gap=0.9, noise=0.0)
    k, unbounded = C.fit_kappa([S], [t])
    assert unbounded and k in C.KAPPA_GRID


def test_fit_kappa_prefers_softer_links_when_scores_are_uninformative():
    rng = np.random.default_rng(3)
    S = rng.uniform(0.1, 0.3, size=(40, 8))
    k, capped = C.fit_kappa([S], [rng.integers(0, 8, 40)])
    assert k == C.KAPPA_GRID[0] and not capped


def test_combine_is_a_posterior_and_moves_mass_to_the_candidate_the_campaign_favours():
    post = C.engine_prior(5)
    s_row = np.array([0.1, 0.1, 0.9, 0.1, 0.1])
    out = C.combine(post, np.arange(5), s_row, kappa=10.0)
    assert out.sum() == pytest.approx(1.0) and int(np.argmax(out)) == 2 and out[0] < post[0]
    same = C.combine(post, np.arange(5), np.full(5, 0.4), kappa=10.0)          # uninformative scores leave the belief unchanged
    assert same == pytest.approx(post)


def test_combine_maps_candidates_to_box_columns():
    post = np.array([0.5, 0.25, 0.25])
    box_idx = np.array([4, 0, 2])                                              # candidate 0 = box 4, candidate 1 = box 0, candidate 2 = box 2
    s_row = np.array([0.1, 0.1, 0.1, 0.1, 0.1])
    s_row[2] = 0.9
    out = C.combine(post, box_idx, s_row, kappa=20.0)
    assert int(np.argmax(out)) == 2


def test_engine_prior_matches_the_engines_own_prior():
    p = C.engine_prior(5)
    assert p[0] == 0.5 and p[1:] == pytest.approx(0.125) and p.sum() == pytest.approx(1.0)


def test_verdict_thresholds():
    assert C.verdict(np.array([0.96, 0.04])) == "CONFIRMED"
    assert C.verdict(np.array([0.04, 0.96])) == "REFUTED"
    assert C.verdict(np.array([0.5, 0.5])) == "FLAGGED"


def _rows(spec):
    """spec = [(is_wrong, state, n)]"""
    out, k = [], 0
    for wrong, state, n in spec:
        for _ in range(n):
            out.append(dict(state=state, say_correct=(state == "CONFIRMED"), wrong=wrong, cluster=f"b{k % 4}", localised=(state != "FLAGGED")))
            k += 1
    return out


def test_policy_verdicts_follow_the_frozen_rules():
    good = _rows([(True, "REFUTED", 20), (False, "CONFIRMED", 20)])
    assert C.policy_verdict(good) == "PASSES"
    dishonest = _rows([(True, "REFUTED", 15), (True, "CONFIRMED", 5), (False, "CONFIRMED", 15), (False, "REFUTED", 5)])
    assert C.policy_verdict(dishonest) == "RESOLVES BUT IS DISHONEST"
    partial = _rows([(True, "REFUTED", 10), (True, "FLAGGED", 10), (False, "CONFIRMED", 10), (False, "FLAGGED", 10)])
    assert C.policy_verdict(partial) == "HONEST BUT PARTIAL"
    assert C.policy_verdict(_rows([(True, "FLAGGED", 10), (False, "FLAGGED", 10)])) == "FAILS"
    many_false_alarms = _rows([(True, "REFUTED", 20), (False, "CONFIRMED", 16), (False, "REFUTED", 4)])
    assert C.policy_verdict(many_false_alarms) == "FAILS"                      # accurate in class balance but > 10% false alarms on right docs


def test_overall_needs_both_seasons_for_a_clean_pass():
    assert C.overall({"P1": ("PASSES", {"july": "PASSES", "january": "PASSES"}), "P2": ("FAILS", {})}).startswith("wiring HELPS `vav_zone`")
    assert C.overall({"P1": ("PASSES", {"july": "PASSES", "january": "FAILS"}), "P2": ("FAILS", {})}) == "wiring HELPS IN ONE SEASON ONLY"
    assert C.overall({"P1": ("HONEST BUT PARTIAL", {}), "P2": ("FAILS", {})}) == "wiring does NOT help"


def test_localisation_and_resolved_fraction_and_boot():
    rows = _rows([(True, "REFUTED", 8), (True, "FLAGGED", 4), (False, "CONFIRMED", 8)])
    assert C.resolved_fraction(rows) == pytest.approx(16 / 20)
    assert C.localisation(rows) == pytest.approx(8 / 12)
    lo, hi = C.cluster_boot(rows, C.resolved_fraction, B=100)
    assert lo <= C.resolved_fraction(rows) <= hi


def test_make_row_records_verdict_belief_and_localisation():
    post = np.array([0.02, 0.03, 0.95])                                        # the documented owner (0) is refuted; candidate 2 is the most probable owner
    r = C.make_row(post, truth_j=2, is_wrong=True, cluster="b0", ep="e1", hours=96.0)
    assert r["state"] == "REFUTED" and r["say_correct"] is False and r["localised"] is True and r["wrong"] is True and r["hours"] == 96.0
    r2 = C.make_row(np.array([0.6, 0.4]), truth_j=1, is_wrong=True, cluster="b0")
    assert r2["state"] == "FLAGGED" and r2["say_correct"] is True and r2["localised"] is False
