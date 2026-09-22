"""Guards for the real-channel-validity / missing-measurement-recommendation module (PREREGISTRATION_DR.md Addendum 5)."""
import sys
from pathlib import Path

from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.active import engine as E  # noqa: E402
from docmismatch.active import measurement as M  # noqa: E402
from docmismatch.active.engine import Episode, run_episode  # noqa: E402


class FakeModel:
    def __init__(self, mu_m=0.5, sd_m=0.2, mu_x=1.0, sd_x=0.3):
        self.mu_m, self.sd_m, self.mu_x, self.sd_x = mu_m, sd_m, mu_x, sd_x
        self.fit = {"M": SimpleNamespace(tau=0.1), "X": SimpleNamespace(tau=0.1)}
        self.kappa = None
        self.rho = 0.0
        self.omega = 0.0
        self.rho_s = 0.0

    def params(self, ctx):
        n = len(ctx)
        return [np.full(n, self.mu_m), np.full(n, self.sd_m), np.full(n, self.mu_x), np.full(n, self.sd_x), np.full(n, 0.5)]


class FakeSlotPool:
    def __init__(self, E, truth, n_owners=None):
        no = n_owners or E.shape[-2]
        self.members = list(range(E.shape[-1]))
        self.owners = list(range(no))
        self.truth = truth
        self.E = E
        self.owner_class = [("VAV",)] * no
        self.owner_size = np.ones(no)


class FakePool:
    def __init__(self, slots, n_slices, group=None):
        self.slots = slots
        self.ctx = np.zeros((n_slices, 3))
        self.group = group if group is not None else np.arange(n_slices)

    @property
    def n_slices(self):
        return len(self.ctx)


# ---------------------------------------------------------------------------------------------- requirement metadata
def test_vav_zone_channel_1_is_bas_only_channels_0_and_2_need_flow():
    assert M.requires_instrument("vav_zone", 1) is False
    assert M.requires_instrument("vav_zone", 0) is True
    assert M.requires_instrument("vav_zone", 2) is True


def test_describe_requirement_names_a_flow_device_for_vav_zone_0():
    d = M.describe_requirement("vav_zone", 0)
    assert d is not None and "airflow" in d


def test_describe_requirement_is_none_for_bas_only_channel():
    assert M.describe_requirement("vav_zone", 1) is None


# ---------------------------------------------------------------------------------------------- real_channel_validity
def _pool_with_signal(rng, n_slices=200, n_mem=6, mu_m=-0.5, mu_x=0.5, sd=0.2, noise=0.05):
    """A channel whose true-owner readings really do sit near mu_m and false-owner readings near mu_x."""
    truth = np.arange(n_mem)
    E = np.full((n_slices, 1, n_mem, n_mem), np.nan)
    for s in range(n_slices):
        for m in range(n_mem):
            for o in range(n_mem):
                z = mu_m if o == m else mu_x
                E[s, 0, o, m] = np.exp(z + rng.normal(0, noise)) - 0.05
    sp = FakeSlotPool(E, truth)
    group = np.repeat(np.arange(n_slices // 5), 5)[:n_slices]  # 5 slices/day-cluster
    return FakePool({"vav_zone": sp}, n_slices, group=group)


def test_real_channel_validity_confirms_a_channel_with_real_separation():
    rng = np.random.default_rng(0)
    pool = _pool_with_signal(rng, mu_m=-0.5, mu_x=0.8, noise=0.05)
    model = FakeModel(mu_m=-0.5, sd_m=0.2, mu_x=0.8, sd_x=0.2)
    out = M.real_channel_validity(pool, "vav_zone", {0: model}, min_clusters=6, min_rows=30)
    assert out[0].validated
    assert out[0].lb_bal_acc > 0.5


def test_real_channel_validity_flags_a_channel_with_no_real_separation():
    rng = np.random.default_rng(1)
    # true and false owners drawn from the SAME distribution -> no real signal, even though the sim-fit model
    # (mu_m far from mu_x) claims there should be
    n_slices, n_mem = 200, 6
    truth = np.arange(n_mem)
    E = np.full((n_slices, 1, n_mem, n_mem), np.nan)
    for s in range(n_slices):
        for m in range(n_mem):
            for o in range(n_mem):
                E[s, 0, o, m] = np.exp(rng.normal(0.2, 0.3)) - 0.05
    sp = FakeSlotPool(E, truth)
    group = np.repeat(np.arange(n_slices // 5), 5)[:n_slices]
    pool = FakePool({"vav_zone": sp}, n_slices, group=group)
    model = FakeModel(mu_m=-0.5, sd_m=0.2, mu_x=0.8, sd_x=0.2)
    out = M.real_channel_validity(pool, "vav_zone", {0: model}, min_clusters=6, min_rows=30)
    assert not out[0].validated
    assert "does not clear chance" in out[0].reason


def test_real_channel_validity_refuses_with_too_few_days():
    rng = np.random.default_rng(2)
    pool = _pool_with_signal(rng, n_slices=20, mu_m=-0.5, mu_x=0.8, noise=0.05)
    pool.group = np.zeros(pool.n_slices, dtype=int)  # every slice is the SAME day -> 1 cluster
    model = FakeModel(mu_m=-0.5, sd_m=0.2, mu_x=0.8, sd_x=0.2)
    out = M.real_channel_validity(pool, "vav_zone", {0: model}, min_clusters=6, min_rows=30)
    assert not out[0].validated
    assert "too little real evidence" in out[0].reason


# ---------------------------------------------------------------------------------------------- recommend_missing_measurement
def test_recommend_skips_bas_only_and_names_instrument_channels():
    recs = M.recommend_missing_measurement("vav_zone", {0, 1, 2})
    ks = {r.k for r in recs}
    assert ks == {0, 2}   # channel 1 is BAS-only, never recommended
    assert all("temporary airflow" in r.text for r in recs)


def test_recommend_empty_for_no_invalid_channels():
    assert M.recommend_missing_measurement("vav_zone", set()) == []


# ---------------------------------------------------------------------------------------------- Brick-grounded override
def test_requires_instrument_brick_override_true_matches_static_default():
    """No graph given: falls back to the static tier (unchanged from the earlier tests)."""
    assert M.requires_instrument("vav_zone", 0) is True


def test_requires_instrument_brick_override_false_when_building_already_has_the_point():
    from docmismatch.active import brick_bridge as B
    if not B.DEFAULT_CACHE_DIR.exists():
        pytest.skip("data_cache/ not present")
    import networkx as nx
    from hvac_benchmark.graph.networkx_build import TopologyGraph
    g = nx.MultiDiGraph()
    g.add_node("equip", brick_type="VAV", brick_types=["VAV"])
    g.add_node("pt", brick_type="Discharge_Air_Flow_Sensor", brick_types=["Discharge_Air_Flow_Sensor"])
    g.add_edge("equip", "pt", relation="hasPoint")
    tg = TopologyGraph(building_id="fake", config_type="experimental", nx_graph=g, edges_by_relation={"hasPoint": {("equip", "pt")}})
    topos, ontology = B.load_real_topologies()
    assert M.requires_instrument("vav_zone", 0, tg=tg, ontology=ontology, owner_node="equip") is False
    assert M.describe_requirement("vav_zone", 0, tg=tg, ontology=ontology, owner_node="equip") is None


def test_requires_instrument_brick_override_true_on_real_ornl_vav():
    """Cross-check against the real corpus: ORNL VAV boxes really do lack a flow point, so the grounded check
    should agree with (not merely default to) the static heuristic here."""
    from docmismatch.active import brick_bridge as B
    if not B.DEFAULT_CACHE_DIR.exists():
        pytest.skip("data_cache/ not present")
    topos, ontology = B.load_real_topologies()
    tg = topos["rtu_exp"]
    v = B.class_nodes(tg, ontology, "VAV")[0]
    assert M.requires_instrument("vav_zone", 0, tg=tg, ontology=ontology, owner_node=v) is True
    d = M.describe_requirement("vav_zone", 0, tg=tg, ontology=ontology, owner_node=v)
    assert d is not None and "airflow" in d


# ---------------------------------------------------------------------------------------------- engine.run_episode(exclude_k=...)
def _episode_and_pool():
    rng = np.random.default_rng(3)
    n_mem = 4
    truth = np.arange(n_mem)
    E = np.full((30, 2, n_mem, n_mem), np.nan)
    for k in range(2):
        for m in range(n_mem):
            for o in range(n_mem):
                z = -0.5 if o == m else 0.8
                E[:, k, o, m] = np.exp(z + rng.normal(0, 0.05, 30)) - 0.05
    sp = FakeSlotPool(E, truth)
    pool = FakePool({"vav_zone": sp}, 30)
    ep = Episode(pool, "vav_zone", 0, 0, 0, False, "ep|0", "g0", {})
    models = {0: FakeModel(mu_m=-0.5, sd_m=0.2, mu_x=0.8, sd_x=0.2), 1: FakeModel(mu_m=-0.5, sd_m=0.2, mu_x=0.8, sd_x=0.2)}
    return ep, pool, models


def test_exclude_k_removes_the_channel_from_the_action_set():
    ep, pool, models = _episode_and_pool()
    sl = np.arange(pool.n_slices)
    r = run_episode(ep, models, sl, "active", nmax=24, seed=0, exclude_k=frozenset({0}))
    assert r is not None
    assert 0 not in set(r.k_seq.tolist())


def test_exclude_k_default_is_bit_identical_to_no_exclusion():
    ep, pool, models = _episode_and_pool()
    sl = np.arange(pool.n_slices)
    r1 = run_episode(ep, models, sl, "active", nmax=24, seed=0)
    r2 = run_episode(ep, models, sl, "active", nmax=24, seed=0, exclude_k=frozenset())
    assert np.allclose(r1.traj, r2.traj)
    assert r1.order == r2.order


def test_exclude_k_all_channels_returns_none():
    ep, pool, models = _episode_and_pool()
    sl = np.arange(pool.n_slices)
    r = run_episode(ep, models, sl, "active", nmax=24, seed=0, exclude_k=frozenset({0, 1}))
    assert r is None


# ---------------------------------------------------------------------------------------------- explain_result
def test_explain_result_confident_verdict_has_no_recommendations():
    ep, pool, models = _episode_and_pool()
    sl = np.arange(pool.n_slices)
    r = run_episode(ep, models, sl, "active", nmax=24, seed=0)
    assert r.stopped
    status = M.explain_result(r, "vav_zone", {0, 2})
    assert status.verdict in ("CONFIRMED", "REFUTED")
    assert status.reason == "confident"
    assert status.recommendations == []


def test_explain_result_futile_gives_uncertain_verdict_and_a_recommendation():
    from types import SimpleNamespace
    r = SimpleNamespace(stopped=False, futile=True, p_doc=0.55, n_read=9)
    status = M.explain_result(r, "vav_zone", {0, 2})
    assert status.verdict == "UNCERTAIN"
    assert "futile" in status.reason
    assert status.n_read == 9
    assert {rec.k for rec in status.recommendations} == {0, 2}


def test_diagnose_connection_recommends_a_physical_test_on_weak_evidence():
    rng = np.random.default_rng(6)
    n_mem = 6
    truth = np.arange(n_mem)
    E = np.full((80, 1, n_mem, n_mem), np.nan)
    mu_m, mu_x = -0.5, 0.8
    midpoint_e = np.exp((mu_m + mu_x) / 2) - 0.05
    for m in range(n_mem):
        for o in range(n_mem):
            E[:, 0, o, m] = midpoint_e * np.exp(rng.normal(0, 0.02, 80))
    sp = FakeSlotPool(E, truth)
    pool = FakePool({"vav_zone": sp}, 80)
    models = {0: FakeModel(mu_m=mu_m, sd_m=0.2, mu_x=mu_x, sd_x=0.2)}
    validity = {0: M.ChannelValidity("vav_zone", 0, False, 0.52, 0.50, 10, 500, "not validated")}
    status, r = M.diagnose_connection(pool, "vav_zone", 0, 0, models, validity, seed=0)
    assert status.verdict == "UNCERTAIN"
    assert status.physical_recommendation is not None
    assert status.physical_recommendation.owner in {0, 1, 2, 3, 4, 5}
    assert "expected" in status.physical_recommendation.text


def test_diagnose_connection_no_physical_recommendation_when_confident():
    rng = np.random.default_rng(5)
    n_mem = 4
    truth = np.arange(n_mem)
    E = np.full((60, 1, n_mem, n_mem), np.nan)
    for m in range(n_mem):
        for o in range(n_mem):
            z = -2.0 if o == m else 2.0
            E[:, 0, o, m] = np.exp(z + rng.normal(0, 0.1, 60)) - 0.05
    sp = FakeSlotPool(E, truth)
    pool = FakePool({"vav_zone": sp}, 60)
    models = {0: FakeModel(mu_m=-2.0, sd_m=0.15, mu_x=2.0, sd_x=0.15)}
    status, r = M.diagnose_connection(pool, "vav_zone", 0, 0, models, seed=0)
    assert status.verdict == "CONFIRMED"
    assert status.physical_recommendation is None


def test_diagnose_connection_recommends_physical_test_with_zero_sensor_evidence():
    sp = FakeSlotPool(np.full((10, 1, 3, 3), np.nan), np.arange(3))
    pool = FakePool({"vav_zone": sp}, 10)
    # every channel's validity is confidently below-chance -> apply_trust_weights drops the model entirely
    validity = {0: M.ChannelValidity("vav_zone", 0, False, 0.3, 0.25, 30, 500, "below chance")}
    status, r = M.diagnose_connection(pool, "vav_zone", 0, 0, {0: FakeModel()}, validity)
    assert r is None
    assert status.reason == "no usable evidence at all for this slot"
    assert status.physical_recommendation is not None


def test_diagnose_connection_end_to_end_confident_when_only_one_plausible_owner():
    rng = np.random.default_rng(4)
    n_mem = 1
    truth = np.array([0])
    E = np.full((30, 1, 1, 1), 0.5)
    sp = FakeSlotPool(E, truth, n_owners=1)
    pool = FakePool({"vav_zone": sp}, 30)
    models = {0: FakeModel(mu_m=-0.5, sd_m=0.2, mu_x=0.8, sd_x=0.2)}
    status, r = M.diagnose_connection(pool, "vav_zone", 0, 0, models)
    assert status.verdict == "CONFIRMED"
    assert status.n_read == 0
    assert r is None


def test_diagnose_connection_end_to_end_resolves_with_strong_signal():
    rng = np.random.default_rng(5)
    n_mem = 4
    truth = np.arange(n_mem)
    E = np.full((60, 1, n_mem, n_mem), np.nan)
    for m in range(n_mem):
        for o in range(n_mem):
            z = -2.0 if o == m else 2.0
            E[:, 0, o, m] = np.exp(z + rng.normal(0, 0.1, 60)) - 0.05
    sp = FakeSlotPool(E, truth)
    pool = FakePool({"vav_zone": sp}, 60)
    models = {0: FakeModel(mu_m=-2.0, sd_m=0.15, mu_x=2.0, sd_x=0.15)}
    status, r = M.diagnose_connection(pool, "vav_zone", 0, 0, models, seed=0)
    assert status.verdict == "CONFIRMED"
    assert status.reason == "confident"
    assert r.n_read < 24   # futility default window doesn't stall a genuinely converging case


def test_diagnose_connection_end_to_end_uncertain_with_recommendation_on_weak_evidence():
    rng = np.random.default_rng(6)
    n_mem = 6
    truth = np.arange(n_mem)
    E = np.full((80, 1, n_mem, n_mem), np.nan)
    mu_m, mu_x = -0.5, 0.8
    midpoint_e = np.exp((mu_m + mu_x) / 2) - 0.05   # equidistant from both class means in tf-space -> genuinely uninformative
    for m in range(n_mem):
        for o in range(n_mem):
            E[:, 0, o, m] = midpoint_e * np.exp(rng.normal(0, 0.02, 80))
    sp = FakeSlotPool(E, truth)
    pool = FakePool({"vav_zone": sp}, 80)
    models = {0: FakeModel(mu_m=mu_m, sd_m=0.2, mu_x=mu_x, sd_x=0.2)}
    validity = {0: M.ChannelValidity("vav_zone", 0, False, 0.52, 0.50, 10, 500, "not validated")}
    status, r = M.diagnose_connection(pool, "vav_zone", 0, 0, models, validity, seed=0)
    assert status.verdict == "UNCERTAIN"
    assert r.n_read < 24   # futility should cut this short, not grind to the budget
    assert len(status.recommendations) == 1
    assert "airflow" in status.recommendations[0].text


def test_explain_result_exhausted_budget_reason_when_not_futile():
    from types import SimpleNamespace
    r = SimpleNamespace(stopped=False, futile=False, p_doc=0.6, n_read=24)
    status = M.explain_result(r, "vav_zone", {0, 2})
    assert status.verdict == "UNCERTAIN"
    assert "exhausted" in status.reason
