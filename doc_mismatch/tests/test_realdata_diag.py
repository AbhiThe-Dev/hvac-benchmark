"""Guards for the model-free real-data `vav_zone` study (PREREGISTRATION_DR.md Addendum 17)."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _intake_world import make_building  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.dr import diagnosability as D  # noqa: E402
from docmismatch.dr import realdata_diag as R  # noqa: E402
from docmismatch.field_pool import build_field_pool  # noqa: E402

T = 24 * 44


# ---------------------------------------------------------------------------------------------- labels and audit
def test_label_tokens_cover_both_naming_styles_including_alphanumeric_ids():
    assert R.label_token("bldg8.ZONE.AHU01.RM100B.Zone Air Temp") == "RM100B"
    assert R.label_token("1-1-1_ActFlow") == "1-1-1" and R.label_token("2-4-17A_SpaceTemp") == "2-4-17A" and R.label_token("2-B-1_DischargeTemp") == "2-B-1"
    assert R.label_token("Supply Air Temp") is None and R.label_token("") is None


def test_audit_passes_only_when_all_three_labels_share_a_token():
    lab = {("V", "flow"): "1-2-3_ActFlow", ("V", "t_dis"): "1-2-3_DischargeTemp", ("Z", "temp"): "1-2-3_SpaceTemp"}
    assert R.audit_claim("V", "Z", lab)
    assert not R.audit_claim("V", "Z", {**lab, ("Z", "temp"): "1-2-4_SpaceTemp"})                 # disagreeing token
    assert not R.audit_claim("V", "Z", {**lab, ("Z", "temp"): "room temperature"})                # unparsable
    assert not R.audit_claim("V", "Z", {k: v for k, v in lab.items() if k[1] != "flow"})          # missing point
    assert R.audit_claim("V", "Z", {k: v for k, v in lab.items() if k[1] != "t_dis"}, need=("flow",))   # secondary buildings: audited on the points they have


def _labels(disagree=()):
    lab = {}
    for i in (1, 2, 3):
        tok = f"RM{i}"
        lab[(f"VAV-{i}", "flow")] = f"b.ZONE.AHU01.{tok}.Flow"
        lab[(f"VAV-{i}", "t_dis")] = f"b.ZONE.AHU01.{tok}.Dis"
        lab[(f"Zone-{i}", "temp")] = f"b.ZONE.AHU01.{'RM9' if i in disagree else tok}.Temp"
    return lab


def test_analysis_set_drops_failed_audits_and_unusable_series_with_reasons():
    fb = make_building(T=T)
    fb.ev["VAV-3|flow"] = np.full(T, 4.0)                                       # flat flow: not usable
    res = R.analysis_set(fb, _labels(disagree=(2,)))
    assert res["pairs"] == [("VAV-1", "Zone-1")] and res["failed_audit"] == [("VAV-2", "Zone-2")]
    assert "VAV-3|flow flat" in res["failed_series"][("VAV-3", "Zone-3")]
    assert len(R.analysis_set(make_building(T=T), _labels())["pairs"]) == 3


# ---------------------------------------------------------------------------------------------- scores, rank-1 and the permutation null
def _E(seed=0, S=12, O=6, M=6, signal=1.0, nan_frac=0.05):
    rng = np.random.default_rng(seed)
    E = rng.uniform(0.2, 1.5, (S, 3, O, M))
    for m in range(M):
        E[:, :, m, m] -= signal * 0.2                                                    # the true pair is a little more consistent
    E[rng.random(E.shape) < nan_frac] = np.nan
    return E


@pytest.mark.parametrize("seed", [0, 1, 2, 3])
def test_score_matrix_reproduces_the_diagnosability_rank1(seed):
    E = _E(seed)
    E[:, 2, 3, :] = np.nan                                                               # candidate 3 has no channel-2 reading at all: channel 2 must drop out for every member
    truth = np.arange(6)
    cands = [list(range(6)) for _ in range(6)]
    for chans in ((0, 1, 2), (0,), (1, 2)):
        ref = D.rank1_accuracy(E, truth, cands, np.zeros(E.shape[0], int), chans, pooled=True)
        got = R.rank1_from_scores(R.score_matrix(E, chans), truth)
        assert got["acc"] == pytest.approx(ref["acc"], abs=1e-12) and got["chance"] == pytest.approx(ref["chance"]) and got["n_units"] == ref["n_units"]


def test_permutation_p_is_tiny_for_an_informative_score_uniform_ish_for_noise_and_one_for_ties():
    n = 12
    S = np.random.default_rng(0).uniform(0.5, 1.5, (n, n))
    S[np.arange(n), np.arange(n)] = -1.0                                                  # the true candidate is always the lowest
    r = R.perm_pvalue(S, np.arange(n), n_perm=2000, seed=0)
    assert r["acc"] == 1.0 and r["p"] == pytest.approx(1 / 2001)
    noise = np.random.default_rng(1).normal(size=(n, n))
    assert R.perm_pvalue(noise, np.arange(n), n_perm=2000, seed=0)["p"] > 0.01
    ties = np.zeros((n, n))                                                               # every candidate identical: rank-1 is 1/n for ANY assignment
    r2 = R.perm_pvalue(ties, np.arange(n), n_perm=500, seed=0)
    assert r2["acc"] == pytest.approx(1 / n) and r2["p"] == 1.0
    assert R.perm_pvalue(S, np.arange(n), n_perm=300, seed=5) == R.perm_pvalue(S, np.arange(n), n_perm=300, seed=5)     # deterministic


def test_top_k_gives_fractional_credit_for_ties_at_the_boundary():
    S = np.array([[0.0, 1.0, 2.0, 3.0], [1.0, 1.0, 1.0, 1.0], [3.0, 2.0, 1.0, 0.0]])
    assert R.top_k_accuracy(S, np.array([0, 1, 0]), k=1) == pytest.approx((1.0 + 0.25 + 0.0) / 3)
    assert R.top_k_accuracy(S, np.array([0, 1, 0]), k=3) == pytest.approx((1.0 + 0.75 + 0.0) / 3)     # the true candidate of row 3 is ranked 4th
    assert R.top_k_accuracy(S, np.array([0, 1, 3]), k=3) == pytest.approx((1.0 + 0.75 + 1.0) / 3)


# ---------------------------------------------------------------------------------------------- sensitivity control
def _noise_world(n=6, days=10, seed=0):
    """n boxes / zones whose hourly series are independent AR(1) noise, so nothing but an injected coupling can tie a zone to its box (the shared sinusoids of the other
    synthetic world make three boxes ambiguous by construction)."""
    from datetime import datetime

    from docmismatch.intake import Claim, FieldBuilding
    rng = np.random.default_rng(seed)
    T = 24 * days

    def ar(mean, sd, phi=0.8):
        x, e = np.zeros(T), rng.normal(0, 1, T)
        for t in range(1, T):
            x[t] = phi * x[t - 1] + e[t]
        return mean + sd * x / x.std()

    eq, ev, claims = {}, {}, []
    for i in range(n):
        eq[f"VAV-{i}"], eq[f"Zone-{i}"] = dict(kind="VAV", function="", medium=""), dict(kind="Zone", function="", medium="")
        ev[f"VAV-{i}|flow"], ev[f"VAV-{i}|t_dis"], ev[f"Zone-{i}|temp"] = np.maximum(ar(5, 1.5), 0.1), ar(15, 2.0), ar(22, 1.0)
        claims.append(Claim(f"VAV-{i}", f"Zone-{i}", "vav_zone", "unknown"))
    return FieldBuilding("noise", datetime(2021, 1, 4), T, eq, {}, claims, ev, {}, {}), [(f"VAV-{i}", f"Zone-{i}") for i in range(n)]


def test_injection_is_exactly_the_frozen_formula_on_a_copy():
    fb = make_building(T=T)
    pairs = [(f"VAV-{i}", f"Zone-{i}") for i in (1, 2)]
    orig = {k: v.copy() for k, v in fb.ev.items()}
    inj = R.inject_coupling(fb, pairs, 0.5)
    z = lambda x: (x - x.mean()) / x.std()  # noqa: E731
    for v, zn in pairs:
        expect = orig[f"{zn}|temp"] + 0.5 * orig[f"{zn}|temp"].std() * (z(orig[f"{v}|flow"]) + z(orig[f"{v}|t_dis"])) / np.sqrt(2)
        np.testing.assert_allclose(inj.ev[f"{zn}|temp"], expect)
    assert all(np.array_equal(fb.ev[k], orig[k]) for k in orig)                                         # the original building is untouched
    assert np.array_equal(inj.ev["Zone-3|temp"], orig["Zone-3|temp"])                                   # zones outside the analysis set are not modified
    np.testing.assert_array_equal(R.inject_coupling(fb, pairs, 0.0).ev["Zone-1|temp"], orig["Zone-1|temp"])


def test_a_strong_injected_coupling_is_recovered_end_to_end_and_weak_ones_less_so():
    fb, pairs = _noise_world()
    accs = {}
    for a in (0.0, 0.25, 2.0):
        pool = build_field_pool(R.inject_coupling(fb, pairs, a), slice_days="all", mask_uninformative=False, require_oat=False)
        sp = pool.slots["vav_zone"]
        E, truth, _ = R.restrict(sp.E, sp.owners, sp.members, pairs)
        accs[a] = R.rank1_from_scores(R.score_matrix(E), truth)["acc"]
    assert accs[2.0] == 1.0 and accs[0.0] < 0.7 and accs[0.25] <= accs[2.0]                            # with no coupling the accuracy is near chance (1/6)


def test_restrict_reorders_owners_and_members_into_the_analysis_set_order():
    E = np.arange(2 * 3 * 3 * 3, dtype=float).reshape(2, 3, 3, 3)
    sub, truth, cands = R.restrict(np.concatenate([E, np.zeros((2, 1, 3, 3))], axis=1), ["A", "B", "C"], ["a", "b", "c"], [("C", "c"), ("A", "a")])
    assert sub.shape == (2, 3, 2, 2) and list(truth) == [0, 1] and cands == [[0, 1], [0, 1]]
    np.testing.assert_array_equal(sub[:, :, 0, 0], E[:, :, 2, 2]) and np.testing.assert_array_equal(sub[:, :, 1, 0], E[:, :, 0, 2])   # candidate A vs member c


# ---------------------------------------------------------------------------------------------- reading rules
def test_verdict_rules_are_exactly_the_frozen_ones():
    hi, lo, mid = dict(acc=0.7, p=0.0001), dict(acc=0.03, p=0.4), dict(acc=0.2, p=0.002)
    ok = {"G1": True, "G2": True, "G3": True}
    assert R.verdict({"a": hi, "b": hi}, ok) == "PASSIVE vav_zone IDENTIFIES ON REAL DATA"
    assert R.verdict({"a": lo, "b": dict(acc=0.02, p=0.06)}, ok) == "AT CHANCE -- ADDENDUM 11 HOLDS ON REAL DATA"
    assert R.verdict({"a": hi, "b": lo}, ok) == "BUILDING-DEPENDENT OR WEAK"
    assert R.verdict({"a": mid, "b": mid}, ok) == "BUILDING-DEPENDENT OR WEAK"                    # signal but below the 0.50 bar
    assert R.verdict({"a": lo, "b": dict(acc=0.02, p=0.04)}, ok) == "BUILDING-DEPENDENT OR WEAK"    # p between 0.01 and 0.05 in one building is not "at chance"
    assert R.verdict({"a": hi, "b": hi}, {**ok, "G3": False}).startswith("NO VERDICT (gate failed: G3")
    assert R.detected(0.5, 0.0099) and not R.detected(0.4999, 0.001) and not R.detected(0.9, 0.01)
    assert R.min_detectable({0.1: dict(acc=0.1, p=0.3), 0.25: dict(acc=0.6, p=0.001), 0.5: dict(acc=0.9, p=0.001)}) == 0.25
    assert R.min_detectable({0.1: dict(acc=0.1, p=0.3)}) is None
