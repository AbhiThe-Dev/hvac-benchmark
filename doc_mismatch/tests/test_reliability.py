import copy
import numpy as np
import pytest

from docmismatch.active import readiness as R
from docmismatch.active.reliability import FEATURES, FI, ReliabilityLayer, pav, prior_balanced_acc


def synth(rng, units=("a", "b", "c", "d"), n_per=300, easy_frac=0.5):
    """synthetic mixed-resolvability set: 'easy' cases (high margin, consistent) are right 99%; 'hard' ones right 60%; slot X is hard only"""
    recs = []
    for u in units:
        for i in range(n_per):
            easy = rng.random() < easy_frac
            wrong = bool(rng.random() < 0.5)
            ok = rng.random() < (0.99 if easy else 0.6)
            f = np.zeros(len(FEATURES))
            f[FI["logit_abs"]] = 6 + rng.normal() if easy else 3 + abs(rng.normal()) * 0.3
            f[FI["agree"]] = 0.95 if easy else 0.6
            f[FI["agree_slices"]] = f[FI["agree"]]
            f[FI["n_owners_info"]] = 5 if easy else 2
            f[FI["gap12"]] = 5 if easy else 1
            f[FI["n"]] = 8; f[FI["n_info"]] = 6
            recs.append(dict(f=f, crossed=True, say_correct=(not wrong) == ok, wrong=wrong, slot="S1" if easy else "S2", unit=u, cluster=f"{u}{i // 4}"))
    return recs


def test_layer_answers_easy_flags_hard():
    rng = np.random.default_rng(0)
    L = ReliabilityLayer(per_slot=False).fit_all(synth(rng))
    assert np.isfinite(L.t_global)
    test = synth(np.random.default_rng(1), units=("z",), n_per=800)
    dec = [L.decide(r) for r in test]
    ans = np.array([d.state != "FLAGGED" for d in dec])
    ok = np.array([r["say_correct"] == (not r["wrong"]) for r in test])
    easy = np.array([r["slot"] == "S1" for r in test])
    assert ans[easy].mean() > 0.7              # resolvable cases are mostly answered (precise, not blanket)
    assert ans[~easy].mean() < 0.15            # unresolvable ones are flagged
    assert ok[ans].mean() > 0.93               # honest accuracy among answered
    assert all(d.reason for d in dec if d.state == "FLAGGED")


def test_all_hard_is_all_flagged():
    rng = np.random.default_rng(2)
    L = ReliabilityLayer().fit_all(synth(rng, easy_frac=0.0))
    dec = [L.decide(r) for r in synth(np.random.default_rng(3), units=("z",), n_per=200, easy_frac=0.0)]
    assert sum(d.state != "FLAGGED" for d in dec) <= 0.03 * len(dec)


def test_isotonic_monotone_and_calibrated():
    rng = np.random.default_rng(4)
    x = rng.random(3000); y = (rng.random(3000) < x).astype(float)
    kx, kv = pav(x, y, np.ones(3000))
    assert np.all(np.diff(kv) >= -1e-12)
    for c in (0.2, 0.5, 0.8):
        assert abs(np.interp(c, kx, kv) - c) < 0.08


def test_prior_balanced_acc_counts_unanswered_in_class_totals():
    wrong = np.array([True] * 10 + [False] * 10)
    ans = np.array([True] * 2 + [False] * 8 + [True] * 10)
    ok = np.ones(20, bool)
    assert prior_balanced_acc(ok, wrong, ans) == 1.0


def test_no_leakage_in_fold_plan():
    plan = R.fold_plan([0, 1, 2], outer=3)
    assert 3 not in plan["outer"]["train"]
    for p in plan["inner"]:
        assert 3 not in p["train"] and p["test"] not in p["train"] and p["test"] != 3
        assert sorted(p["train"] + [p["test"]]) == [0, 1, 2]


def test_layer_ignores_outer_labels():
    """the layer is a function of INNER records only: changing outer labels cannot change its decisions"""
    rng = np.random.default_rng(5)
    inner = synth(rng)
    outer = synth(np.random.default_rng(6), units=("z",), n_per=100)
    L1 = ReliabilityLayer().fit_all(inner)
    d1 = [L1.decide(r).state for r in outer]
    flipped = [dict(r, wrong=not r["wrong"]) for r in outer]
    d2 = [L1.decide(r).state for r in flipped]
    assert d1 == d2
    L2 = ReliabilityLayer().fit_all(inner)
    assert [L2.decide(r).state for r in outer] == d1


def test_frozen_check_refuses_without_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "FROZEN", tmp_path)
    with pytest.raises(SystemExit):
        R.frozen_check()


def test_frozen_check_detects_change(tmp_path, monkeypatch):
    import json, hashlib
    monkeypatch.setattr(R, "FROZEN", tmp_path)
    cfg = tmp_path / "config.json"; cfg.write_text("{}")
    man = dict(code=R.code_manifest(), config_sha256=hashlib.sha256(cfg.read_bytes()).hexdigest())
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    assert R.frozen_check() == {}
    man["code"]["engine.py"] = "0" * 64
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    with pytest.raises(SystemExit):
        R.frozen_check()


def test_slice_effect_reduces_to_baseline_when_omega_zero():
    from docmismatch.active.real_data import load_real_dev, real_episodes
    from docmismatch.active.model import fit_slot_models
    from docmismatch.active.engine import run_episode
    from docmismatch.active import selection as SEL
    p = load_real_dev()
    W = SEL.get("sel_slice")
    mods = fit_slot_models([p], "vav_sat", "oat", [p.season != 0], **W["fitkw"])
    for m in mods.values():
        m.omega = 1e-7
    eps = [e for e in real_episodes(p) if e.slot == "vav_sat"][:6]
    for e in eps:
        sl = np.where(p.group == e.meta["day"])[0]
        a = run_episode(e, mods, sl, "random", tau=2.0, seed=1, **SEL.get("sel")["runkw"])
        b = run_episode(e, mods, sl, "random", tau=2.0, seed=1, **W["runkw"])
        assert np.abs(a.traj - b.traj).max() < 1e-6


def _fast_cfg():
    cfg = copy.deepcopy(R.DEFAULT_CFG)
    cfg.update(policies=["active", "random"], sim_reps=[0], sim_settings=["visit"], calibrate_beta=False)
    return cfg


def test_sealed_real_path_end_to_end_with_dev_stand_in(monkeypatch):
    """the non-rehearsal real-sealed code path (ledgered loader -> fit on all DEV -> score) run with a DEV pool standing in for the sealed one: no sealed file is read"""
    from docmismatch.active import real_data
    calls = []
    monkeypatch.setattr(real_data, "load_real_sealed", lambda reason: (calls.append(reason), real_data.load_real_dev())[1])
    rows, info = R.run_sealed_real(_fast_cfg(), procs=1, layers=("none", "new"))
    assert calls and info["n_outer"] > 0 and {r["layer"] for r in rows} == {"none", "new"}


def test_sealed_sim_path_end_to_end_with_dev_stand_in(monkeypatch):
    man = R.sim_manifest()
    tid = "dev_H" if "dev_H" in man["dev"] else man["dev"][-1]
    cfg = _fast_cfg()
    dev = R.SimKind(cfg)
    cases = [c for c in dev.cases() if c["topology_id"] == tid]
    monkeypatch.setattr(R, "load_sim_sealed", lambda reason, tids=None: ({tid: {0: dev.pools(tid, 0)}}, cases))
    monkeypatch.setattr(R, "sim_manifest", lambda: dict(dev=[t for t in man["dev"] if t != tid], sealed=[tid], source="test"))
    rows, info = R.run_sealed_sim(cfg, procs=1, layers=("none", "new"))
    assert info["n_outer"] > 0 and {r["layer"] for r in rows} == {"none", "new"}
