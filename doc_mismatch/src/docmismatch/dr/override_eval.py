"""Technician-style single-box override tests (PREREGISTRATION_DR.md Addendum 16). numpy only.

A technician commands ONE VAV box to a distinctive state ("full cooling": damper at maximum airflow, reheat off; or "flow only": airflow forced to maximum, reheat untouched) for a short
window and watches which zone's temperature responds. This module holds the planning of such tests in a simulated run, the response statistic, and the measured operating
characteristics that replace the assumed rates of `active.physical.ACTUATE_OBSERVE` (0.95 / 0.05).
"""

from __future__ import annotations

import numpy as np

from ..active.physical import PhysicalTestType, physical_eig, update_posterior

SCHEDULE_SHIFT_H = {"july": -1, "january": 0}   # a schedule's hour value is applied this many hours EARLY relative to the reported timestamps: -1 in July (daylight saving), 0 in January
                                                # (Addendum 13 found the July shift; Addendum 16's pre-registered code-path check found January has none -- Deviation 1)
DIRECTION = {"full_cool": "cool", "flow_only": "cool", "close": "warm"}   # the way the command pushes the served zone's temperature
STEPS_PER_HOUR = 6                       # the models run (and zone temperatures are reported) every 10 minutes
BASELINE_MIN = 60                        # baseline window before the override
START_HOURS = (9, 11, 13, 15)            # clock hour at which a test starts (occupied hours)
DURATIONS_MIN = (30, 60, 120)            # response windows evaluated (the override itself lasts 120 min)
THETA_GRID = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0)    # K: "visibly responds" thresholds
KAPPA_GRID = (0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 15.0, 20.0, 30.0, 50.0, 75.0, 100.0)   # per kelvin
NOISE_SD = {"none": 0.0, "legacy": 0.25, "harsh": 0.5}   # zone-temperature sensor noise (K), applied per sample


def plan_override_tests(vav_ids: list[str], seed: int, pre_days: int = 2, hours: int = 2) -> list[dict]:
    """One test per box, one box per day after `pre_days` undisturbed days, in a seeded random order with a seeded random start hour.
    Returns [{vav, day (0-based from the run start), start_hour, hours}] in chronological order."""
    rng = np.random.default_rng([seed, 771])
    order = [int(i) for i in rng.permutation(len(vav_ids))]
    starts = rng.choice(START_HOURS, size=len(vav_ids))
    return [dict(vav=vav_ids[b], day=pre_days + i, start_hour=int(starts[i]), hours=hours) for i, b in enumerate(order)]


def response_scores(temps: np.ndarray, start_step: int, duration_min: int, noise_sd: float = 0.0, rng: np.random.Generator | None = None) -> np.ndarray:
    """Per-zone response score of ONE override test. `temps` (zones, steps) are zone temperatures at 10-minute steps; `start_step` is the index of the first step inside the override.
    dT_z = mean(temps over the first `duration_min` minutes of the override) - mean(temps over the `BASELINE_MIN` minutes before it); the median dT over ALL zones is subtracted
    (building-wide drift is common mode); the score is the extra COOLING relative to peers, S_z = -(dT_z - median dT) in kelvin (positive = cooled more than peers)."""
    k, nb = duration_min // 10, BASELINE_MIN // 10
    seg = np.asarray(temps[:, start_step - nb:start_step + k], float)
    if noise_sd > 0:
        seg = seg + (rng or np.random.default_rng(0)).normal(0.0, noise_sd, seg.shape)
    d = seg[:, nb:].mean(axis=1) - seg[:, :nb].mean(axis=1)
    return -(d - np.median(d))


def _window_change(temps: np.ndarray, step0: int, k: int, nb: int) -> np.ndarray:
    return temps[:, step0:step0 + k].mean(axis=1) - temps[:, step0 - nb:step0].mean(axis=1)


def response_scores_history(temps: np.ndarray, day: int, start_hour: int, duration_min: int, noise_sd: float = 0.0, rng: np.random.Generator | None = None,
                            direction: str = "cool") -> np.ndarray:
    """Response score of the override test held on `day` at `start_hour`, corrected with the zones' own BAS trend history (what a technician can compare against).
    A_z(d) = dT_z(d) - median_z dT(d) is a zone's change over the test window relative to its peers (weather and building-wide drift removed) on day d; each zone's own
    typical value for that clock window is the median of A_z(d') over every OTHER day d' of the run (a zone is disturbed on only one of them), which removes the zone-specific
    time-of-day ramp (orientation, internal gains) that a peers-only comparison mistakes for a response. S_z = -(A_z(day) - median_{d' != day} A_z(d')) in kelvin
    (positive = cooled more than usual); for a damper-CLOSE test (`direction="warm"`) the sign flips, so a positive score always means "moved the way the command pushes it".
    Noise (if any) is added once to the whole run so every day sees the same realisation."""
    T = np.asarray(temps, float)
    if noise_sd > 0:
        T = T + (rng or np.random.default_rng(0)).normal(0.0, noise_sd, T.shape)
    k, nb = duration_min // 10, BASELINE_MIN // 10
    n_days = T.shape[1] // (24 * STEPS_PER_HOUR)

    def A(d: int):
        s0 = (d * 24 + start_hour) * STEPS_PER_HOUR
        if s0 - nb < 0 or s0 + k > T.shape[1]:
            return None
        dt = _window_change(T, s0, k, nb)
        return dt - np.median(dt)

    today = A(day)
    refs = [a for d in range(n_days) if d != day for a in [A(d)] if a is not None]
    d = today - np.median(refs, axis=0)
    return d if direction == "warm" else -d


def actual_start_hour(start_hour: int, season: str) -> int:
    """Clock hour at which a test labelled to start at `start_hour` really begins in the simulation, in the given season (July: one hour earlier; January: on the label)."""
    return start_hour + SCHEDULE_SHIFT_H[season]


def test_scores(temps: np.ndarray, day: int, start_hour: int, duration_min: int, kind: str, noise_sd: float = 0.0, rng: np.random.Generator | None = None,
                history: bool = False, season: str = "july") -> np.ndarray:
    """Per-zone response score of one planned test, with the schedule shift applied. Primary (`history=False`): the peers-only statistic of `response_scores`; secondary: the history-corrected one."""
    sign = 1.0 if DIRECTION[kind] == "cool" else -1.0
    h0 = actual_start_hour(start_hour, season)
    if history:
        return response_scores_history(temps, day, h0, duration_min, noise_sd, rng, direction=DIRECTION[kind])
    return sign * response_scores(temps, (day * 24 + h0) * STEPS_PER_HOUR, duration_min, noise_sd, rng)


def top1(scores: np.ndarray, z: int) -> float:
    """1 if zone z has the highest score (exact ties share the credit equally)."""
    tied = np.isclose(scores, scores.max(), atol=1e-12)
    return float(tied[z] / tied.sum())


def auroc(scores: np.ndarray, z: int) -> float:
    """P(score of the served zone > score of another zone), ties half."""
    others = np.delete(scores, z)
    return float(np.mean(scores[z] > others) + 0.5 * np.mean(scores[z] == others))


def rates_at(pos: np.ndarray, neg: np.ndarray, theta: float) -> tuple[float, float]:
    """raw (TPR, FPR) of the rule "responds if S >= theta" over positive (served zone) and negative (other zones) scores"""
    return float(np.mean(np.asarray(pos) >= theta)), float(np.mean(np.asarray(neg) >= theta))


def choose_theta(pos: np.ndarray, neg: np.ndarray, grid=THETA_GRID, target_fpr: float = 0.05) -> float:
    """smallest threshold whose raw FPR is <= target_fpr (the largest threshold if none is)"""
    for th in grid:
        if rates_at(pos, neg, th)[1] <= target_fpr:
            return float(th)
    return float(grid[-1])


def measured_rates(pos: np.ndarray, neg: np.ndarray, theta: float) -> tuple[float, float]:
    """Laplace-smoothed (k + 1) / (n + 2) TPR and FPR, so a perfectly separating training set never yields a certainty"""
    p, n = np.asarray(pos), np.asarray(neg)
    return float((np.sum(p >= theta) + 1) / (len(p) + 2)), float((np.sum(n >= theta) + 1) / (len(n) + 2))


def run_physical_sequence(post: np.ndarray, outcome_fn, test: PhysicalTestType, tau: float = 0.95, max_tests: int = 4, max_repeats: int = 3) -> tuple[np.ndarray, list]:
    """Sequential technician tests on the engine's own Bernoulli machinery. `post` (H,) is the belief over candidate owners (index 0 = documented);
    `outcome_fn(j, n_prev)` returns whether the member responded when candidate j was commanded for the (n_prev + 1)-th time. Each step tests the candidate with the largest
    `physical_eig`; stops at P(doc) >= tau or <= 1 - tau, after `max_tests` tests, or when no test is informative. Returns (final belief, [(candidate, outcome), ...])."""
    post = np.asarray(post, float)
    counts = np.zeros(len(post), int)
    log = []
    for _ in range(max_tests):
        if post[0] >= tau or post[0] <= 1 - tau:
            break
        eig = np.array([physical_eig(post, j, test) if counts[j] < max_repeats else -1.0 for j in range(len(post))])
        if eig.max() <= 0:
            break
        j = int(np.argmax(eig))
        y = bool(outcome_fn(j, int(counts[j])))
        post = update_posterior(post, j, y, test)
        counts[j] += 1
        log.append((j, y))
    return post, log
