"""Guards for the signal-value study (PREREGISTRATION_DR.md Addendum 18): signal-removal ceilings and the `ahu_vav` substitutes."""
import inspect
import pickle
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.active.pools import DAYS_PER_WINDOW_PICK  # noqa: E402
from docmismatch.dr import diagnosability as D  # noqa: E402
from docmismatch.dr import signal_value as S  # noqa: E402

H = 1008
W = 8


def toy(O=3, per=4, noise=0.0, seed=0, with_reheat=True) -> S.ABuilding:
    """`ahu_vav` world: handler o supplies 10 + 2 o + sin(2 pi h / 24 + o); box j is fed by handler j // per; reheat is on in the first 6 hours of every day (t_dis = t_in + 3 then,
    flow at its minimum); the box's flow above the minimum wiggles with the box index."""
    rng = np.random.default_rng(seed)
    M = O * per
    hrs = np.arange(H)
    sat = np.array([10 + 2.0 * o + np.sin(2 * np.pi * hrs / 24 + o) for o in range(O)])
    truth = np.repeat(np.arange(O), per)
    reheat = np.tile((hrs % 24 < 6).astype(float), (M, 1))
    t_in = sat[truth]
    t_dis = t_in + 3.0 * reheat
    flow = 1.0 + (1 - reheat) * (1.0 + 0.4 * (0.5 + 0.5 * np.sin(2 * np.pi * hrs / 24 + np.arange(M)[:, None])))
    jitter = (lambda a: a + rng.normal(0, noise, a.shape)) if noise else (lambda a: a)
    per_w = lambda a: [jitter(a.copy()) for _ in range(W)]  # noqa: E731
    return S.ABuilding("toy", [f"AHU-{o}" for o in range(O)], [f"VAV-{j}" for j in range(M)], truth, [list(range(O)) for _ in range(M)],
                       per_w(t_in), per_w(t_dis), per_w(flow), per_w(sat), [reheat.copy() for _ in range(W)] if with_reheat else None,
                       [t_in.copy() for _ in range(W)], [t_dis.copy() for _ in range(W)], np.array([2, 4, 8, 12, 20, 24, 16, 6.0]))


# ---------------------------------------------------------------------------------------------- Part A
def test_signal_catalogue_and_remaining_channels():
    assert set(S.signal_catalogue("ahu_vav")) == {("m", "t_in"), ("o", "sat"), ("m", "flow"), ("o", "flow")}
    assert S.remaining_channels("ahu_vav", ("m", "t_in")) == (1, 2) and S.remaining_channels("ahu_vav", ("o", "sat")) == (1, 2)
    assert S.remaining_channels("ahu_vav", ("m", "flow")) == (0,)
    assert S.remaining_channels("branch_coil", ("o", "t_in")) == (1, 2) and S.remaining_channels("branch_coil", ("o", "flow")) == ()
    assert all(S.remaining_channels("coil_ahu", s) == () for s in S.signal_catalogue("coil_ahu"))          # every channel reads all four signals
    assert ("m", "rate_s|rate") in S.signal_catalogue("coil_ahu")


def test_subset_ceiling_is_the_best_subset_and_ignores_nan():
    means = np.full(7, np.nan)
    means[S.SUBSET_INDEX[(0,)]], means[S.SUBSET_INDEX[(1,)]], means[S.SUBSET_INDEX[(0, 1, 2)]] = 0.9, 0.6, 0.7
    assert S.subset_ceiling(means, (0, 1, 2)) == 0.9                        # ch0 alone beats all three
    assert S.subset_ceiling(means, (1, 2)) == 0.6
    assert np.isnan(S.subset_ceiling(means, (2,)))


def test_labels_follow_the_frozen_thresholds():
    assert S.label_value(0.15, False) == "CRITICAL" and S.label_value(0.30, False) == "CRITICAL" and S.label_value(None, True) == "CRITICAL"
    assert S.label_value(0.149, False) == "MODERATE" and S.label_value(0.05, False) == "MODERATE"
    assert S.label_value(0.049, False) == "MINOR" and S.label_value(-0.2, False) == "MINOR"
    assert S.label_value(float("nan"), False) == "UNDEFINED"


def test_part_a_removing_the_informative_channels_signal_is_costly_and_deterministic():
    rng = np.random.default_rng(0)
    A = np.full((6, 7), np.nan)
    for b in range(6):
        A[b, S.SUBSET_INDEX[(0,)]] = 0.95 + rng.normal(0, 0.01)
        A[b, S.SUBSET_INDEX[(1,)]] = 0.55 + rng.normal(0, 0.01)
        A[b, S.SUBSET_INDEX[(2,)]] = 0.40 + rng.normal(0, 0.01)
        A[b, S.SUBSET_INDEX[(0, 1)]] = 0.85
        A[b, S.SUBSET_INDEX[(0, 2)]] = 0.80
        A[b, S.SUBSET_INDEX[(1, 2)]] = 0.50
        A[b, S.SUBSET_INDEX[(0, 1, 2)]] = 0.82
    r = S.part_a_rows("ahu_vav", A, n_boot=100)
    by = {row["signal"]: row for row in r["rows"]}
    assert by[("m", "t_in")]["label"] == "CRITICAL" and by[("m", "t_in")]["value"] > 0.35 and by[("m", "t_in")]["remaining"] == (1, 2)
    assert by[("m", "flow")]["label"] == "MINOR" and abs(by[("m", "flow")]["value"]) < 0.02       # ch0 alone is the ceiling either way
    assert by[("m", "t_in")]["lo"] <= by[("m", "t_in")]["value"] <= by[("m", "t_in")]["hi"]
    r2 = S.part_a_rows("ahu_vav", A, n_boot=100)
    assert [x["lo"] for x in r2["rows"]] == [x["lo"] for x in r["rows"]]
    c = S.part_a_rows("coil_ahu", A, n_boot=20)
    assert all(row["label"] == "CRITICAL" and row["no_channel"] and row["value"] is None for row in c["rows"])


def test_census_parse_and_availability_text():
    md = """## Which connection types could be tested\n\n| ahu_vav | 28 | 2143 | 0 | 0 | 0 | 0 | 0 | 0 |\n\n## Which measurements exist\n\n| equipment | signal | a | b | c | d |
|---|---|---|---|---|---|\n| AHU | sat | 30 | 22 | 38 | 30 |\n| VAV | t_in | 0 | 0 | 0 | 0 |\n| Coil | rate | 0 | 0 | 0 | 0 |\n\n## Next\n\n| AHU | zzz | 1 | 1 | 1 | 1 |\n"""
    c = S.parse_census_measurements(md)
    assert c[("AHU", "sat")] == dict(rec_any=30, rec_80=22, doc_any=38, doc_80=30) and ("AHU", "zzz") not in c and ("ahu_vav", "28") not in c
    assert "30 buildings" in S.census_availability("ahu_vav", ("o", "sat"), c)
    assert "0 buildings" in S.census_availability("ahu_vav", ("m", "t_in"), c) and "0 buildings" in S.census_availability("coil_ahu", ("m", "rate_s|rate"), c)
    assert "no such node" in S.census_availability("loop_branch", ("o", "t_sup"), c)


# ---------------------------------------------------------------------------------------------- Part B: hour selection
def test_hour_selection_reads_only_flow_or_reheat():
    assert list(inspect.signature(S.selected_hours).parameters) == ["variant", "flow", "reheat_truth"]          # no temperature and no candidate series can reach it
    b = toy()
    flow, rh = b.flow[0], b.reheat[0]
    m50, m25, m1 = (S.selected_hours(v, flow, rh) for v in ("V2", "V3", "V1"))
    assert abs(m50.mean() - 0.5) < 0.05 and abs(m25.mean() - 0.25) < 0.05 and (m25 <= m50).all()               # top quartile inside top half
    assert (m1 == (rh == 0)).all() and S.selected_hours("V0", flow, None).all() and S.selected_hours("V4", flow, None).all()
    assert (S.selected_hours("V2", flow, None) == m50).all()                                                   # V2 does not need the reheat series
    with pytest.raises(ValueError):
        S.selected_hours("V1", flow, None)


def test_flow_rules_pick_reheat_off_hours_in_the_toy_world_and_are_blind_to_temperatures():
    b = toy()
    mask = S.selected_hours("V2", b.flow[0], None)
    assert ((b.reheat[0] == 0) | ~mask).all()                                     # every selected hour has the reheat off (here flow is at its minimum when reheating)
    b2 = toy()
    b2.t_dis[0] += 50.0                                                           # changing any temperature cannot change the mask
    assert (S.selected_hours("V2", b2.flow[0], None) == mask).all()


# ---------------------------------------------------------------------------------------------- Part B: error matrices
def test_v0_error_is_the_ch0_pair_error_and_true_pair_is_exact_without_noise():
    b = toy()
    E, win = S.trended_E(b, "V0", np.zeros(len(b.members)))
    assert E.shape == (48, 3, 3, 12) and (win == np.repeat(np.arange(8), 6)).all() and np.isnan(E[:, 1:]).all()
    w, d, o, j = 3, DAYS_PER_WINDOW_PICK[2], 1, 5
    sl = slice(d * 24, (d + 1) * 24)
    assert np.isclose(E[3 * 6 + 2, 0, o, j], np.abs(b.t_in[w][j, sl] - b.sat[w][o, sl]).mean())            # evidence.pair_errors, channel 0
    assert np.allclose(E[np.arange(48), 0, b.truth[j], j], 0.0)                                              # the true handler's error is exactly 0 noise-free


def test_proxies_recover_the_true_handler_only_on_reheat_off_hours():
    b = toy()
    off = np.zeros(len(b.members))
    for v, exact in (("V1", True), ("V2", True), ("V3", True), ("V4", False)):
        E, _ = S.trended_E(b, v, off)
        true_err = np.array([E[:, 0, b.truth[j], j] for j in range(len(b.members))])
        assert (np.allclose(true_err, 0.0) == exact) and (exact or (true_err > 0.5).all()), v               # unfiltered t_dis carries the reheat (0.75 K mean here)


def test_slices_with_fewer_than_six_selected_hours_are_missing_and_a_box_without_any_is_skipped():
    b = toy()
    for w in range(W):
        b.reheat[w][0] = 1.0                                                     # box 0's reheat is always on: no reheat-off hour at all
    b.reheat[0][1, 0:20] = 1.0                                                   # box 1, window 0, first slice: only 4 reheat-off hours
    b.reheat[0][1, 6:24] = 1.0
    E, win = S.trended_E(b, "V1", np.zeros(len(b.members)))
    assert np.isnan(E[:, 0, :, 0]).all()                                         # box 0 never valid
    assert np.isnan(E[0, 0, :, 1]).all() and np.isfinite(E[1, 0, :, 1]).all()    # box 1 loses only the short slice
    r = S.score_groups(E, win, b.truth, b.cands)["all"]
    assert r["n_skipped"] >= 8                                                   # box 0 in each of the 8 windows


def test_a_constant_offset_shifts_the_error_and_can_break_identification():
    b = toy()
    E0, win = S.trended_E(b, "V0", np.zeros(12))
    off = np.full(12, 0.7)
    E1, _ = S.trended_E(b, "V0", off)
    assert np.allclose(E1[:, 0, b.truth[3], 3], 0.7)                             # error to the true handler is exactly |offset|
    assert S.score_groups(E0, win, b.truth, b.cands)["all"]["acc"] == 1.0
    big = np.random.default_rng(1).normal(0, 5.0, 12)
    assert S.score_groups(S.trended_E(b, "V0", big)[0], win, b.truth, b.cands)["all"]["acc"] < 1.0


def test_spot_readings_use_one_standard_day_daytime_distinct_hours_and_are_reproducible():
    b = toy()
    for w in range(W):
        b.t_in[w][:] = np.arange(H)[None] * 1e-3                                 # encode the hour index in the reading; sat = 0
        b.sat[w][:] = 0.0
    off = np.zeros(12)
    E, win = S.spot_E(b, 1, off, np.random.default_rng(3))
    idx = np.rint(E[:, 0, 0, :] * 1e3).astype(int)                               # (windows, boxes): the hour index that was read
    assert E.shape == (8, 3, 3, 12) and (win == np.arange(8)).all()
    assert set(idx.ravel() // 24) <= set(DAYS_PER_WINDOW_PICK) and ((idx % 24 >= 8) & (idx % 24 <= 17)).all()
    E10, _ = S.spot_E(b, 10, off, np.random.default_rng(3))                       # ten distinct hours out of the ten daytime hours: exactly hours 8..17 of one day
    mean_idx = E10[:, 0, 0, :] * 1e3
    d = np.floor(mean_idx / 24).astype(int)
    assert np.allclose(mean_idx, d * 24 + 12.5) and set(d.ravel()) <= set(DAYS_PER_WINDOW_PICK)
    E24, _ = S.spot_E(b, 24, off, np.random.default_rng(3))
    assert np.allclose(E24[:, 0, 0, :] * 1e3, np.floor(E24[:, 0, 0, :] * 1e3 / 24) * 24 + 11.5)                # the whole day (mean hour 11.5)
    Ea, _ = S.spot_E(b, 3, off, np.random.default_rng(9))
    Eb, _ = S.spot_E(b, 3, off, np.random.default_rng(9))
    Ec, _ = S.spot_E(b, 3, off, np.random.default_rng(10))
    assert np.array_equal(Ea, Eb, equal_nan=True) and not np.array_equal(Ea, Ec, equal_nan=True)


def test_noise_free_spot_reading_identifies_and_big_offsets_break_it():
    b = toy()
    r = S.run_variant(b, "S1", 0, 0, offsets=(0.0, 5.0), n_draws=6)
    assert r[0.0]["all"]["acc"] == 1.0 and r[5.0]["all"]["acc"] < 1.0 and abs(r[0.0]["all"]["chance"] - 1 / 3) < 1e-9


def test_run_variant_is_deterministic_and_trended_zero_offset_is_a_single_draw():
    b = toy(noise=0.25, seed=1)
    a = S.run_variant(b, "V2", 1, 2, offsets=(0.0, 0.5), n_draws=4)
    c = S.run_variant(b, "V2", 1, 2, offsets=(0.0, 0.5), n_draws=4)
    assert a == c and set(a[0.0]) == set(S.GROUPS)
    assert S.run_variant(b, "V0", 1, 0, offsets=(0.0,), n_draws=7)[0.0]["all"]["acc"] == S.run_variant(b, "V0", 1, 0, offsets=(0.0,), n_draws=2)[0.0]["all"]["acc"]


# ---------------------------------------------------------------------------------------------- reading rules
def _pooled(v0, v):
    return ({(s, g): v0.get(s, {}).get(g, 0.97) for s in S.OFFSETS for g in S.VERDICT_GROUPS},
            {(s, g): v.get(s, {}).get(g, 0.97) for s in S.OFFSETS for g in S.VERDICT_GROUPS})


def test_works_needs_the_bar_and_the_tolerance():
    assert S.works(0.85, 0.95) and not S.works(0.79, 0.85) and not S.works(0.84, 0.95) and S.works(0.85, 0.95) and not S.works(float("nan"), 0.9)


def test_verdicts_usable_fragile_fails_no_verdict():
    p0, _ = _pooled({}, {})
    # holds up to 1.0 K, breaks at 2.0 -> USABLE, s* = 1.0
    _, pv = _pooled({}, {2.0: {"g0": 0.6, "g2": 0.9}})
    r = S.evaluate_variant(pv, p0)
    assert r["verdict"] == "USABLE" and r["s_star"] == 1.0
    # holds at 0 and 0.25 only -> FRAGILE
    _, pv = _pooled({}, {0.5: {"g0": 0.7}, 1.0: {"g0": 0.7}, 2.0: {"g0": 0.7}})
    r = S.evaluate_variant(pv, p0)
    assert r["verdict"] == "FRAGILE" and r["s_star"] == 0.25
    # fails at zero offset -> FAILS, and a later recovery does not count (s* stops at the first failure)
    _, pv = _pooled({}, {0.0: {"g2": 0.5}})
    r = S.evaluate_variant(pv, p0)
    assert r["verdict"] == "FAILS" and r["s_star"] is None
    _, pv = _pooled({}, {0.25: {"g0": 0.3}})
    assert S.evaluate_variant(pv, p0)["s_star"] == 0.0
    # gate failure or both seasons baseline-limited at zero offset -> NO VERDICT
    assert S.evaluate_variant(pv, p0, gate_ok=False)["verdict"] == "NO VERDICT"
    lim, pv = _pooled({0.0: {"g0": 0.7, "g2": 0.6}}, {})
    assert S.evaluate_variant(pv, lim)["verdict"] == "NO VERDICT"


def test_baseline_limited_season_counts_neither_way_but_all_limited_offsets_do_not_work():
    v0, v = _pooled({0.5: {"g0": 0.75}}, {0.5: {"g0": 0.1}})                     # winter baseline below the bar at 0.5 K: the winter failure is ignored
    r = S.evaluate_variant(v, v0)
    assert r["limited"][0.5] == {"g0": True, "g2": False} and r["works_at"][0.5] and r["verdict"] == "USABLE"
    v0, v = _pooled({1.0: {"g0": 0.7, "g2": 0.7}}, {})                            # both limited at 1.0 K: nothing to vouch for the variant there
    r = S.evaluate_variant(v, v0)
    assert not r["works_at"][1.0] and r["s_star"] == 0.5 and r["verdict"] == "USABLE"


def test_smallest_m_that_works_at_an_offset():
    v0, _ = _pooled({}, {})
    by_m = {1: _pooled({}, {0.5: {"g0": 0.5}})[1], 3: _pooled({}, {})[1], 6: _pooled({}, {})[1]}
    assert S.smallest_m(by_m, v0, 0.5) == 3 and S.smallest_m(by_m, v0, 0.0) == 1
    by_m = {1: _pooled({}, {0.0: {"g0": 0.5}})[1]}
    assert S.smallest_m(by_m, v0, 0.0) is None


# ---------------------------------------------------------------------------------------------- gates and checks
def test_unit_weights_reproduce_rank1_accuracy_exactly_including_nan_and_ties():
    rng = np.random.default_rng(4)
    O, M, n = 4, 7, 12
    E = rng.uniform(0.1, 2.0, (n, 3, O, M))
    E[:, 0, :, 2] = 1.0                                                          # a fully tied member
    E[3:7, 0, 1, 5] = np.nan
    E[:, 0, 2, 4] = np.nan                                                       # one candidate with no reading at all: the unit is skipped
    win = np.repeat(np.arange(3), 4)
    truth = rng.integers(0, O, M)
    cands = [list(range(O)) for _ in range(M)]
    cands[6] = [int(truth[6]), (int(truth[6]) + 1) % O]
    ref = D.rank1_accuracy(E, truth, cands, win, (0,))
    acc, chance = S.acc_from_units(S.unit_weights(E, cands, win), truth)
    assert np.isclose(acc, ref["acc"]) and np.isclose(chance, ref["chance"])


def test_null_control_sits_at_chance_for_a_working_statistic():
    b = toy(noise=0.25, seed=2)
    E, win = S.trended_E(b, "V0", np.zeros(12))
    real = S.acc_from_units(S.unit_weights(E, b.cands, win), b.truth)
    null = S.null_control(S.unit_weights(E, b.cands, win), b.truth, n_perm=100)
    assert real[0] == 1.0 and abs(null["acc"] - null["chance"]) < S.NULL_TOL and null["n_perm"] == 100


def test_oracle_identity_gap_shares_and_season_check():
    b = toy()
    assert S.oracle_identity_gap(b) == 0.0                                       # noise-free t_dis == t_in whenever the reheat is off
    b.t_dis_truth[0] = b.t_dis_truth[0] + 0.2 * (b.reheat[0] == 0)
    assert np.isclose(S.oracle_identity_gap(b), 0.2)
    assert S.oracle_identity_gap(toy(with_reheat=False)) is None
    sh = S.selection_shares(toy(), "V1")
    assert abs(sh["g0"]["hours"] - 0.75) < 1e-9 and sh["g0"]["valid"] == 1.0
    assert abs(S.selection_shares(toy(), "V3")["g2"]["hours"] - 0.25) < 0.05
    assert S.season_check(toy()) is True
    b.oat_window_mean = np.array([20, 20, 8, 8, 10, 10, 8, 8.0])
    assert S.season_check(b) is False


# ---------------------------------------------------------------------------------------------- real simulator (skipped when the cache is not there)
CACHE = ROOT.parent / "results/docmismatch/dr/diagnosability/diagnosability.pkl"


@pytest.mark.skipif(not CACHE.exists(), reason="Addendum 11 cache not present")
def test_v0_reproduces_addendum_11_ch0_on_a_real_training_building():
    from docmismatch.data import load_base
    tid = "dev_F"
    b = S.from_base(tid)
    E, win = S.trended_E(b, "V0", np.zeros(len(b.members)))
    ref = D.build_E(load_base(tid), D.level_evidence(load_base(tid), "legacy", 0), "ahu_vav")
    assert np.allclose(E[:, 0], ref[:, 0], atol=1e-12, equal_nan=True)
    cached = pickle.loads(CACHE.read_bytes())[(tid, "ahu_vav", "legacy")]["rank1_window"]["ch0"]
    got = D.rank1_accuracy(E, b.truth, b.cands, win, (0,))
    assert abs(got["acc"] - cached["acc"]) < 1e-9 and got["n_units"] == cached["n_units"]
