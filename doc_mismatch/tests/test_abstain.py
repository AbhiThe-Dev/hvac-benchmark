"""Tests for the abstention layer (synthetic records; plus a smoke test of the nested training runs on the cached real pool)."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.active.abstain import (CONFIRMED, LOW_CONFIDENCE, REFUTED, UNRESOLVED_BUDGET, UNRESOLVED_NO_POWER, AbstentionRule, beta_quantile,
                                        episode_features, nested_select)


def traj(stop=3, final=0.97, flips=0, cross=True):
    """never-stopped trajectory: starts at 0.5, ends confident at index `stop` (final=P(doc)), optional side flips before."""
    t = np.full(25, 0.5)
    if not cross:
        t[:] = 0.6
        return t
    t[1:stop] = 0.7
    if flips:
        t[1:1 + flips + 1] = [0.4 if i % 2 == 0 else 0.6 for i in range(flips + 1)]
        stop = max(stop, flips + 3)
    t[stop:] = final
    return t


def rec(slot, wrong, verdict_correct, group, **kw):
    """verdict_correct=True means the trajectory ends >= tau (says 'documentation correct')."""
    t = traj(final=0.97 if verdict_correct else 0.03, **kw)
    return dict(slot=slot, wrong=wrong, traj=t, group=group, policy="active", outer="O", inner="H1")


def synthetic(n=40, good_acc=1.0, bad_acc=0.5, seed=0):
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        wrong = i % 2 == 0
        out.append(rec("good", wrong, verdict_correct=not wrong, group=f"g{i}") if rng.random() < good_acc else rec("good", wrong, verdict_correct=wrong, group=f"g{i}"))
        ok = rng.random() < bad_acc
        out.append(rec("bad", wrong, verdict_correct=(not wrong) if ok else wrong, group=f"b{i}"))
        out.append(dict(rec("void", wrong, True, f"v{i}"), traj=traj(cross=False)) if i % 20 else rec("void", wrong, not wrong, f"v{i}"))
    return out


def test_beta_quantile():
    assert abs(beta_quantile(1, 1, 0.5) - 0.5) < 0.01
    assert beta_quantile(20, 2, 0.5) > beta_quantile(2, 2, 0.5)
    assert beta_quantile(20, 1, 0.2) < beta_quantile(20, 1, 0.8)


def test_episode_features():
    f = episode_features(traj(stop=4, final=0.97), 0.95)
    assert f["crossed"] and f["say_correct"] and f["n"] == 4
    assert not episode_features(traj(cross=False), 0.95)["crossed"]
    assert episode_features(traj(stop=6, flips=3), 0.95)["flips"] >= 3
    assert not episode_features(traj(stop=4, final=0.03), 0.95)["say_correct"]


def test_states_and_reasons():
    r = AbstentionRule(tau=0.95, target=0.8, min_cov=0.2).fit(synthetic())
    assert r.decide("good", traj(final=0.97)).state == CONFIRMED
    assert r.decide("good", traj(final=0.03)).state == REFUTED
    assert r.decide("bad", traj(final=0.97)).state == LOW_CONFIDENCE          # 50% reliable slot: crossing is not enough
    assert r.decide("void", traj(final=0.97)).state == UNRESOLVED_NO_POWER    # reading pool almost never resolves in training
    assert r.decide("good", traj(cross=False)).state == UNRESOLVED_BUDGET
    assert r.decide("never_seen", traj(final=0.97)).state == LOW_CONFIDENCE   # no training evidence -> no confident verdict
    assert r.decide("good", traj(stop=6, flips=3)).state == LOW_CONFIDENCE    # unstable belief before stopping


def test_target_monotone_and_can_decline_everything():
    r = AbstentionRule(tau=0.95).fit(synthetic())
    covered = [sum(r.with_params(target=t).decide(s, traj()).state in (CONFIRMED, REFUTED) for s in ("good", "bad", "void")) for t in (0.0, 0.7, 0.99, 1.01)]
    assert covered == sorted(covered, reverse=True) and covered[-1] == 0


def test_rule_uses_only_slot_and_trajectory():
    """no benchmark observability label, no ground-truth flag and no unit id is needed at decision time"""
    recs = synthetic()
    r = AbstentionRule(tau=0.95).fit(recs)
    d1 = r.decide("good", traj())
    for x in recs:                      # the fitted rule must not depend on any 'obs' field
        x["obs"] = "unobservable"
    r2 = AbstentionRule(tau=0.95).fit(recs)
    assert r2.decide("good", traj()).state == d1.state and r2.cells == r.cells
    import inspect
    assert list(inspect.signature(AbstentionRule.decide).parameters) == ["self", "slot", "traj"]


def test_class_balance_of_reliability():
    """a 4:1 class imbalance in training must not tilt the reliability of a slot that is right 100% on one class and 0% on the other"""
    recs = [rec("s", True, verdict_correct=True, group=f"w{i}") for i in range(40)] + [rec("s", False, verdict_correct=True, group=f"r{i}") for i in range(10)]
    r = AbstentionRule(tau=0.95).fit(recs)
    assert abs(r.cells[("s", True)]["acc"] - 0.5) < 1e-6       # confirms are right on the 10 correct edges and wrong on the 40 wrong ones -> 0.5 balanced


def test_nested_select_declines_when_unreliable_and_accepts_when_reliable():
    bad = []
    for h in ("H1", "H2", "H3"):
        for x in synthetic(seed=hash(h) % 100, good_acc=0.5, bad_acc=0.5):
            bad.append(dict(x, inner=h, group=h + x["group"]))
    sel = nested_select(bad, "active")
    assert sel["cv_cov"] == 0.0     # nothing may be confident when nothing is demonstrably reliable
    good = []
    for h in ("H1", "H2", "H3"):
        for x in synthetic(n=60, good_acc=1.0, bad_acc=1.0):
            good.append(dict(x, inner=h, group=h + x["group"]))
    sel = nested_select(good, "active")
    assert sel["target"] < 1.0 and sel["cv_cov"] > 0.3 and sel["cv_acc"] >= 0.95


def _load_script():
    spec = importlib.util.spec_from_file_location("s17", ROOT / "scripts" / "17_active_abstain.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_no_leakage_across_outer_units():
    """the rule for held-out unit O is a function of inner records with outer == O only"""
    m = _load_script()
    inner = []
    for outer in ("A", "B"):
        for h in ("H1", "H2", "H3"):
            for x in synthetic(seed=len(outer + h)):
                inner.append(dict(x, outer=outer, inner=h, group=outer + h + x["group"]))
    ra = m.fit_rules(inner, ["A"], ["active"], 0.95, goal=0.95)[("A", "active")]
    corrupted = [dict(x, traj=traj(final=0.03 if x["wrong"] else 0.97)) if x["outer"] == "B" else x for x in inner]   # B: make training 'perfect'/flip labels
    ra2 = m.fit_rules(corrupted, ["A"], ["active"], 0.95, goal=0.95)[("A", "active")]
    assert ra.cells == ra2.cells and ra.selection["target"] == ra2.selection["target"]
    assert ra.cov == ra2.cov


def test_annotate_before_after_consistency():
    m = _load_script()
    inner = [dict(x, outer="A", inner=h) for h in ("H1", "H2", "H3") for x in synthetic(seed=1)]
    rules = m.fit_rules(inner, ["A"], ["active"], 0.95, goal=0.95, target=0.8)
    outer = [dict(rec("good", w, not w, f"o{i}"), topo="A", setting="hist", ctx=True, unsupported=False, obs="true", policy="active", ep=f"e{i}") for i, w in enumerate([True, False] * 5)]
    rows = m.annotate(outer, rules, ["active"], 0.95)
    assert len(rows) == 10 and all(r["cb"] and r["okb"] for r in rows)
    assert all((not r["ca"]) or r["cb"] for r in rows)          # abstention can only remove confident answers, never add
    S = m.suff(rows)
    met = m.metrics(S.sum(0))
    assert met["cov_a"] <= met["cov_b"] + 1e-12


REAL_POOL = ROOT.parent / "results" / "docmismatch" / "active" / "pool_real.pkl"


@pytest.mark.skipif(not REAL_POOL.exists(), reason="real pool cache missing")
def test_nested_real_runs_exclude_outer_and_inner_season():
    from docmismatch.active.nested import real_inner
    recs = real_inner(0, 1, policies=("active",), settings=("loso",))
    assert recs and all(r["season"] == 1 and r["outer"] == 0 and r["inner"] == 1 for r in recs)
    # the likelihood behind these runs was fitted with the mask (season != 0) & (season != 1): checked by construction in real_inner
    import inspect
    src = inspect.getsource(real_inner)
    assert "pool.season != outer_season) & (pool.season != inner_season" in src
