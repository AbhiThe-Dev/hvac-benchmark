"""Tests for Addendum 34: the stopping-rule sweep (tau, min_rate) on the routine, no LLM. Simulation only."""
import numpy as np
import pytest

from docmismatch.troubleshoot.v2 import study_stop as ST
from docmismatch.troubleshoot.v2 import study_llm as L


@pytest.fixture(scope="module")
def small():
    _, wp, events = ST.world()
    return events[:60], wp


def test_cases_with_only_changes_tau_and_min_rate():
    base = ST.cases_with()
    variant = ST.cases_with(tau=0.8, min_rate=0.02)
    r = 3
    assert base[r].settings.tau == ST.BASE_TAU and variant[r].settings.tau == 0.8
    assert base[r].min_rate == ST.BASE_MIN_RATE and variant[r].min_rate == 0.02
    assert base[r].doc == variant[r].doc and base[r].candidates == variant[r].candidates and base[r].settings.p_wrong == variant[r].settings.p_wrong
    assert base[r].checks == variant[r].checks


def test_run_variant_uses_identical_answers_across_variants(small):
    events, wp = small
    lo = ST.run_variant(ST.cases_with(tau=0.99), wp, events[:10])       # a strict variant that asks more
    hi = ST.run_variant(ST.cases_with(tau=0.50), wp, events[:10])       # a loose one that stops earlier
    assert (lo["checks"] >= hi["checks"] - 1e-9).all()                  # never fewer checks with a stricter bar
    assert (lo["minutes"] >= hi["minutes"] - 1e-9).all()


def test_lower_tau_never_increases_minutes(small):
    events, wp = small
    a = ST.run_variant(ST.cases_with(tau=0.90), wp, events)
    b = ST.run_variant(ST.cases_with(tau=0.95), wp, events)
    assert a["minutes"].mean() <= b["minutes"].mean() + 1e-9
    assert (a["checks"] <= b["checks"] + 1e-9).all()


def test_a_very_low_tau_still_needs_a_real_observation_per_visit(small):
    """The prior alone never concludes (PriorSession's informed rule, Addendum 30): even at tau=0.01 every visit spends at least one check (never zero), and far fewer than the baseline."""
    events, wp = small
    lo = ST.run_variant(ST.cases_with(tau=0.01), wp, events[:20])
    hi = ST.run_variant(ST.cases_with(), wp, events[:20])
    assert (lo["checks"] >= 1).all()
    assert lo["checks"].sum() < hi["checks"].sum()


def test_min_rate_above_every_gain_stops_at_once(small):
    events, wp = small
    v = ST.run_variant(ST.cases_with(min_rate=1e6), wp, events[:20])
    assert (v["checks"] == 0).all() and (v["minutes"] == 0).all()


def test_summarize_and_compare_against_self_is_a_null_result(small):
    events, wp = small
    v = ST.run_variant(ST.cases_with(), wp, events)
    boot = np.random.default_rng(0).integers(0, len(events), (200, len(events)))
    c = ST.compare(v, v, boot)
    assert c["d_min"] == 0.0 and c["d_acc"] == 0.0 and c["d_wc"] == 0.0 and c["label"] == "NEITHER" and c["time"] == "SAME"


def test_a_slower_stricter_variant_reads_as_worse_or_neither(small):
    events, wp = small
    strict = ST.run_variant(ST.cases_with(tau=0.999), wp, events)
    base = ST.run_variant(ST.cases_with(), wp, events)
    boot = np.random.default_rng(1).integers(0, len(events), (500, len(events)))
    c = ST.compare(strict, base, boot)
    assert c["d_min"] >= 0 and c["label"] in ("WORSE", "NEITHER")


def test_run_sweep_and_analyze_shapes(small):
    events, wp = small
    sweep = ST.run_sweep(events=events, wp=wp, n=len(events))
    assert set(sweep["tau"]) == set(ST.TAU_GRID) and set(sweep["min_rate"]) == set(ST.MIN_RATE_GRID)
    assert sweep["min_rate"][ST.BASE_MIN_RATE] is sweep["tau"][ST.BASE_TAU]           # the shared baseline is not recomputed
    an = ST.analyze(sweep, B=200)
    for axis, grid in (("tau", ST.TAU_GRID), ("min_rate", ST.MIN_RATE_GRID)):
        for k in grid:
            assert set(an[axis][k]) == {"raw", "sum", "cmp"}
    base_cmp = an["tau"][ST.BASE_TAU]["cmp"]
    assert base_cmp["d_min"] == 0.0 and base_cmp["label"] == "NEITHER"


def test_predictions_and_decision_are_internally_consistent(small):
    events, wp = small
    sweep = ST.run_sweep(events=events, wp=wp, n=len(events))
    an = ST.analyze(sweep, B=200)
    p = ST.predictions(an)
    assert set(p) == {f"P{k}" for k in range(1, 6)}
    assert all(isinstance(v[0], (bool, np.bool_)) for v in p.values())
    d = ST.decision(an)
    assert d in ("THE STOPPING RULE LARGELY EXPLAINS IT", "THE STOPPING RULE PARTLY EXPLAINS IT", "THE STOPPING RULE DOES NOT EXPLAIN IT")


def test_decision_is_largely_explains_it_when_a_tau_is_cheap_and_safe():
    """A hand-built sweep where one tau clears the recovery bar within tolerance: decision must be LARGELY, not merely PARTLY."""
    n = 200
    base = dict(minutes=np.full(n, 100.0), checks=np.full(n, 10.0), correct=np.full(n, 80.0), wc=np.zeros(n), concluded=np.full(n, 80.0), n=np.full(n, 1.0))
    good = dict(base, minutes=np.full(n, 90.0))                                       # -10%, no accuracy or safety change
    an = {"tau": {ST.BASE_TAU: {"sum": ST.summarize(base), "cmp": ST.compare(base, base, np.zeros((1, n), int))},
                  0.80: {"sum": ST.summarize(good), "cmp": ST.compare(good, base, np.zeros((1, n), int))}}}
    assert ST.decision(an) == "THE STOPPING RULE LARGELY EXPLAINS IT"


def test_decision_is_does_not_explain_it_when_speed_always_costs_safety():
    n = 200
    base = dict(minutes=np.full(n, 100.0), checks=np.full(n, 10.0), correct=np.full(n, 80.0), wc=np.zeros(n), concluded=np.full(n, 80.0), n=np.full(n, 1.0))
    costly = dict(base, minutes=np.full(n, 90.0), wc=np.full(n, 0.5))                  # -10% minutes, but wrong-and-confident jumps
    an = {"tau": {ST.BASE_TAU: {"sum": ST.summarize(base), "cmp": ST.compare(base, base, np.zeros((1, n), int))},
                  0.80: {"sum": ST.summarize(costly), "cmp": ST.compare(costly, base, np.zeros((1, n), int))}}}
    assert ST.decision(an) == "THE STOPPING RULE DOES NOT EXPLAIN IT"


def test_gate_g3_matches_addendum_33s_answer_table():
    assert ST.gate_g3()[0]


def test_gate_g4_direction_sanity_on_the_real_sweep(small):
    events, wp = small
    sweep = ST.run_sweep(events=events, wp=wp, n=len(events))
    an = ST.analyze(sweep, B=100)
    assert ST.gate_g4(an)[0]


def test_gate_g5_reproducibility(small):
    events, wp = small
    a = ST.run_sweep(events=events, wp=wp, n=len(events))
    b = ST.run_sweep(events=events, wp=wp, n=len(events))
    assert ST.gate_g5(a, b)[0]


def test_world_matches_the_llm_studys_primary_cell():
    """Addendum 34 reuses exactly Addendum 33's primary-cell event stream (same building block, same index)."""
    assert ST.PRIMARY_IDX == L.PRIMARY_IDX
    _, wp1, ev1 = ST.world()
    _, wp2, ev2 = L.world()
    assert wp1 == wp2
    assert [e.kind for e in ev1[:100]] == [e.kind for e in ev2[:100]]
