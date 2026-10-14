import numpy as np

from hotwater_dx import checks as K
from hotwater_dx import engine as E
from hotwater_dx import tenants as TN


def toy(offset=0.0):
    mean = np.array([[100.0, 0.0], [80.0, 2.0], [90.0, 1.0]]) + offset
    sd = np.array([[2.0, 0.5], [2.0, 0.5], [20.0, 5.0]])
    return E.Likelihoods(["a", "b", "other"], ["K05", "Q1"], mean, sd, {})


def test_soft_evidence_stops_one_wild_tenant_answer_from_eliminating_the_truth():
    lk = toy()
    hard, soft = E.Engine(lk, False), E.Engine(lk, False, q_eps=0.3)
    for e in (hard, soft):
        e.update("K05", 100.0)                         # a physical reading that favours 'a'
        e.update("Q1", 2.0)                            # a tenant answer that favours 'b'
    ph, ps = hard.posterior(), soft.posterior()
    assert ps[0] > ph[0] + 0.05                        # the physical reading keeps more authority under soft evidence
    assert ps[0] > ps[1]


def test_soft_evidence_changes_only_tenant_checks():
    lk = toy()
    plain, soft = E.Engine(lk, False), E.Engine(lk, False, q_eps=0.3)
    assert abs(plain.gain("K05") - soft.gain("K05")) < 1e-12
    assert soft.gain("Q1") < plain.gain("Q1")          # a doubted answer is worth less
    plain.update("K05", 95.0)
    soft.update("K05", 95.0)
    assert np.allclose(plain.posterior(), soft.posterior())


def test_grids_with_and_without_soft_evidence_do_not_share_a_cache_slot():
    lk = toy()
    g1 = E.Engine(lk, False, q_eps=0.3).gain("Q1")
    g0 = E.Engine(lk, False).gain("Q1")
    g1b = E.Engine(lk, False, q_eps=0.3).gain("Q1")
    assert g0 != g1 and g1 == g1b


def test_tenant_unreliability_draws_the_answer_from_the_garbage_source(plant):
    lk = toy()
    far = toy(offset=1000.0)
    ctx = K.Ctx(plant)
    kw = dict(allowed=frozenset({"Q1"}), max_checks=1)
    r0 = E.run_case(lk, ctx, ("a",), np.random.default_rng(3), False, p_tenant=0.0, **kw)
    r1 = E.run_case(lk, ctx, ("a",), np.random.default_rng(3), False, p_tenant=1.0, garbage_lk=far, **kw)
    assert r0.top != r1.top or abs(r0.top_p - r1.top_p) > 1e-9


def test_defaults_leave_the_engine_unchanged(plant):
    lk = toy()
    ctx = K.Ctx(plant)
    a = E.run_case(lk, ctx, ("a",), np.random.default_rng(9), False, max_checks=2)
    b = E.run_case(lk, ctx, ("a",), np.random.default_rng(9), False, p_tenant=0.0, max_checks=2, q_eps=0.0)
    assert (a.top, a.top_p, a.minutes, a.checks) == (b.top, b.top_p, b.minutes, b.checks)


def test_variants_are_defined_and_never_ask_variants_exclude_the_questions():
    for v in TN.VARIANTS:
        TN.variant_config(v)
    assert TN.variant_config("NoQ_A")["allowed"].isdisjoint({"Q1", "Q2", "Q3"})
    assert TN.variant_config("S30_B")["q_eps"] == 0.30 and TN.variant_config("S30_B")["var_inflate"] == 2.0
