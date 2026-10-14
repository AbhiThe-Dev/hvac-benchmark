"""Guards for the technician-style override statistics and their Bernoulli wiring (PREREGISTRATION_DR.md Addendum 16)."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.active.physical import PhysicalTestType  # noqa: E402
from docmismatch.dr import override_eval as O  # noqa: E402


def _temps(n_zones=6, n_days=6, seed=0, ramp=None, hit=None):
    """zone temperatures at 10-minute steps: a shared diurnal drift, per-zone ramps at the test hours, small noise; `hit` = (zone, day, start_hour, dT) adds an override response"""
    rng = np.random.default_rng(seed)
    steps = n_days * 24 * 6
    t = np.arange(steps)
    common = 2.0 * np.sin(2 * np.pi * t / 144)
    T = 22.0 + common[None, :] + 0.02 * rng.normal(size=(n_zones, steps))
    if ramp is not None:                                        # zone-specific change that repeats every day over the (shifted) test window [8, 10)
        for d in range(n_days):
            a = (d * 24 + O.actual_start_hour(9, 'july')) * 6
            T[ramp[0], a:a + 12] += ramp[1]
    if hit is not None:
        z, d, h, dT = hit
        a = (d * 24 + O.actual_start_hour(h, 'july')) * 6
        T[z, a:a + 12] += dT
    return T


def test_plan_covers_every_box_once_one_per_day_and_is_deterministic():
    vavs = [f"VAV-{i}" for i in range(1, 8)]
    plan = O.plan_override_tests(vavs, seed=3, pre_days=2, hours=2)
    assert sorted(p["vav"] for p in plan) == sorted(vavs)
    assert [p["day"] for p in plan] == list(range(2, 9))
    assert all(p["start_hour"] in O.START_HOURS and p["hours"] == 2 for p in plan)
    assert plan == O.plan_override_tests(vavs, seed=3, pre_days=2, hours=2)
    assert [p["vav"] for p in plan] != [p["vav"] for p in O.plan_override_tests(vavs, seed=4, pre_days=2, hours=2)]


def test_schedule_shift_depends_on_the_season():
    assert O.actual_start_hour(9, "july") == 8          # daylight saving: applied an hour early
    assert O.actual_start_hour(9, "january") == 9       # standard time: on the label


def test_january_scores_use_the_unshifted_window():
    T = _temps()
    a = (3 * 24 + 11) * 6
    T[2, a:a + 12] += -2.0                              # a January test labelled 11:00 really starts at 11:00
    assert int(np.argmax(O.test_scores(T, 3, 11, 60, "full_cool", season="january"))) == 2
    assert O.test_scores(T, 3, 11, 60, "full_cool", season="july")[2] < 1.0     # reading it with the July shift would miss most of the response


def test_cooling_test_scores_the_cooled_zone_highest_and_drift_cancels():
    T = _temps(hit=(2, 3, 11, -2.0))
    sc = O.test_scores(T, day=3, start_hour=11, duration_min=60, kind="full_cool")
    assert int(np.argmax(sc)) == 2 and sc[2] == pytest.approx(2.0, abs=0.3)
    assert np.all(np.abs(np.delete(sc, 2)) < 0.3)              # the shared diurnal swing (+-2 K) is common mode


def test_close_test_scores_warming_and_wrong_sign_command_scores_negative():
    T = _temps(hit=(4, 2, 13, +1.5))
    assert int(np.argmax(O.test_scores(T, 2, 13, 60, "close"))) == 4
    assert O.test_scores(T, 2, 13, 60, "full_cool")[4] < 0     # a warming zone is not evidence for a cooling command


def test_the_label_hour_is_not_the_window_a_late_read_would_miss_the_response():
    T = _temps(hit=(1, 3, 11, -2.0))
    on_time = O.test_scores(T, 3, 11, 60, "full_cool")[1]
    late = O.response_scores(T, (3 * 24 + 11) * 6, 60)[1]      # reading at the label hour instead of the shifted one: baseline already contains the response
    assert on_time > 1.5 and late < 0.5


def test_history_correction_removes_a_zone_specific_daily_ramp_that_fools_the_peers_only_score():
    T = _temps(ramp=(0, -2.5))                                 # zone 0 naturally cools 2.5 K every day in the window a test labelled 9:00 covers
    a = (3 * 24 + O.actual_start_hour(9, 'july')) * 6
    T[3, a:a + 12] += -1.5                                     # the tested zone on day 3 additionally cools 1.5 K
    peers = O.test_scores(T, 3, 9, 60, "full_cool")
    hist = O.test_scores(T, 3, 9, 60, "full_cool", history=True)
    assert int(np.argmax(peers)) == 0                          # the peers-only statistic prefers the naturally-cooling zone
    assert int(np.argmax(hist)) == 3 and hist[3] > 1.0 and abs(hist[0]) < 0.3   # the history-corrected one finds the tested zone


def test_noise_lowers_separation_and_is_seeded():
    T = _temps(hit=(2, 3, 11, -0.3))
    clean = O.test_scores(T, 3, 11, 30, "full_cool")
    noisy = [O.test_scores(T, 3, 11, 30, "full_cool", noise_sd=0.5, rng=np.random.default_rng(i)) for i in range(30)]
    assert np.mean([O.top1(x, 2) for x in noisy]) < O.top1(clean, 2)
    assert np.array_equal(O.test_scores(T, 3, 11, 30, "full_cool", 0.5, np.random.default_rng(1)), O.test_scores(T, 3, 11, 30, "full_cool", 0.5, np.random.default_rng(1)))


def test_top1_shares_ties_and_auroc_counts_pairs():
    assert O.top1(np.array([1.0, 1.0, 0.0]), 0) == pytest.approx(0.5)
    assert O.top1(np.array([0.2, 3.0, 0.1]), 1) == 1.0 and O.top1(np.array([0.2, 3.0, 0.1]), 0) == 0.0
    assert O.auroc(np.array([3.0, 1.0, 2.0, 0.0]), 0) == 1.0
    assert O.auroc(np.array([1.0, 1.0, 2.0]), 0) == pytest.approx(0.25)


def test_theta_rule_and_smoothed_rates():
    pos = np.array([2.0, 1.8, 1.5, 0.9, 2.2])
    neg = np.array([0.1, 0.3, 0.6, 0.2, 0.4, 0.9, 0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.2, 0.1, 0.3, 0.4, 0.5])
    th = O.choose_theta(pos, neg)
    assert O.rates_at(pos, neg, th)[1] <= 0.05 and all(O.rates_at(pos, neg, t)[1] > 0.05 for t in O.THETA_GRID if t < th)
    assert O.choose_theta(pos, np.full(10, 9.0)) == O.THETA_GRID[-1]        # nothing separates: the largest threshold
    tpr, fpr = O.measured_rates(np.full(50, 5.0), np.zeros(200), 1.0)
    assert tpr == pytest.approx(51 / 52) and fpr == pytest.approx(1 / 202)  # a perfect training set never yields a certainty


TEST = PhysicalTestType("measured", 0.98, 0.02, 6.0, "test")


def test_sequence_confirms_and_refutes_in_one_test_with_strong_rates():
    post = np.r_[0.5, np.full(5, 0.1)]
    p_yes, log = O.run_physical_sequence(post, lambda j, n: j == 0, TEST)
    assert len(log) == 1 and log[0] == (0, True) and p_yes[0] >= 0.95
    p_no, log = O.run_physical_sequence(post, lambda j, n: False, TEST)
    assert log[0] == (0, False) and p_no[0] <= 0.05 and len(log) == 1


def test_sequence_needs_a_repeat_when_the_rates_are_weaker_and_respects_the_test_cap():
    weak = PhysicalTestType("weak", 0.90, 0.10, 6.0, "weak test")
    post = np.r_[0.5, np.full(5, 0.1)]
    p, log = O.run_physical_sequence(post, lambda j, n: j == 0, weak)
    assert len(log) >= 2 and p[0] >= 0.95                                     # one 'yes' leaves P(doc) = 0.9, a second one crosses
    p2, log2 = O.run_physical_sequence(post, lambda j, n: bool(n % 2 == 0), weak, max_tests=2)
    assert len(log2) <= 2
