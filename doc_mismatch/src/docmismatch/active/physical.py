"""Physical/manual verification actions: a technician's direct, non-sensor test (trace the duct/conduit from
the member back to a candidate, or command a candidate's damper/reheat/valve and watch whether the member
responds) as a first-class action alongside sensor channel readings.

Addresses a gap this session concluded the algorithm never modeled at all, not weakly: every existing action
(`engine._Actions`) comes from `SlotPool.E`, populated purely from sensor time-series statistics; `channel_cost`
only ever distinguishes "already logged" from "needs a new SENSOR," never "needs a person to go look." Nothing
anywhere represented a non-sensor observation.

Modelled as a simple, near-deterministic BERNOULLI experiment, deliberately NOT shoehorned into the Gaussian
`ChannelModel` machinery: a physical test is fundamentally a one-shot, (usually) highly decisive observation with
none of the sensor-channel complications (context-dependent likelihood, pair random effects from repeated reads
of the same stream) that motivate the Gaussian model's complexity in the first place. Testing candidate j: does
the member visibly respond?
  P(yes | j is the true owner)     = true_positive_rate  (near 1, but not exactly -- faulty equipment, an
                                      observation window that's too short, etc.)
  P(yes | j is NOT the true owner) = false_positive_rate (near 0, but not exactly -- cross-talk between
                                      adjacent zones, coincidental timing, etc.)
Both rates and the cost are ASSUMPTIONS, explicitly named as such -- matching `engine.channel_cost`'s own
"qualitative tiers, NOT measured" honesty -- until a real field study calibrates them. Costs are set relative to
`engine.channel_cost`'s sensor tiers (BAS-only=1.0, needs-an-instrument=rho, default 3.0): a physical test needs
a technician to physically travel to and manipulate equipment, so it is priced well above either sensor tier.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _hbin(p: float) -> float:
    p = float(np.clip(p, 1e-12, 1 - 1e-12))
    return -(p * np.log2(p) + (1 - p) * np.log2(1 - p))


@dataclass(frozen=True)
class PhysicalTestType:
    name: str
    true_positive_rate: float
    false_positive_rate: float
    cost: float
    description: str


# Assumptions, never measured -- see module docstring.
DUCT_TRACE = PhysicalTestType("duct_trace", 0.98, 0.02, 12.0,
                               "physically trace the duct/conduit from the member back to the candidate equipment")
ACTUATE_OBSERVE = PhysicalTestType("actuate_observe", 0.95, 0.05, 6.0,
                                    "command the candidate's damper/reheat/valve to a distinctive state and watch whether the member responds")
PHYSICAL_TEST_TYPES: tuple[PhysicalTestType, ...] = (DUCT_TRACE, ACTUATE_OBSERVE)


def update_posterior(post: np.ndarray, j_test: int, outcome: bool, test: PhysicalTestType) -> np.ndarray:
    """Bayesian update after a physical test targeting hypothesis index `j_test` (a position into `post`, same
    indexing as `hyps`). The outcome is conditionally independent of WHICH alternative is true, given only
    whether j_test itself is the truth -- a physical test distinguishes "j_test" from "everything else," not one
    wrong candidate from another, exactly like tracing a duct either leads to this box or it doesn't."""
    post = np.asarray(post, float)
    idx = np.arange(len(post))
    if outcome:
        lik = np.where(idx == j_test, test.true_positive_rate, test.false_positive_rate)
    else:
        lik = np.where(idx == j_test, 1 - test.true_positive_rate, 1 - test.false_positive_rate)
    p = post * lik
    return p / p.sum()


def physical_eig(post: np.ndarray, j_test: int, test: PhysicalTestType) -> float:
    """Expected information gain (bits) on the DECISION variable P(doc correct) = post[0] -- the same quantity
    and units `engine.run_episode`'s own EIG tracks for sensor readings, so the two are directly comparable."""
    post = np.asarray(post, float)
    p_yes = post[j_test] * test.true_positive_rate + (1 - post[j_test]) * test.false_positive_rate
    h_yes = _hbin(update_posterior(post, j_test, True, test)[0])
    h_no = _hbin(update_posterior(post, j_test, False, test)[0])
    h0 = _hbin(post[0])
    return max(0.0, h0 - (p_yes * h_yes + (1 - p_yes) * h_no))


@dataclass
class PhysicalRecommendation:
    owner: int          # the candidate's actual id (from `hyps`, NOT a position index into `post`)
    test: PhysicalTestType
    eig: float          # expected bits gained
    eig_per_cost: float

    @property
    def text(self) -> str:
        return f"{self.test.description} (candidate {self.owner}) -- expected {self.eig:.2f} bits for a one-time cost of {self.test.cost:g}"


def best_physical_test(post: np.ndarray, hyps: list[int], test_types=PHYSICAL_TEST_TYPES) -> PhysicalRecommendation | None:
    """Across every candidate hypothesis and every physical test TYPE, the one with the best EIG per unit cost."""
    post = np.asarray(post, float)
    best = None
    for pos, owner in enumerate(hyps):
        for t in test_types:
            g = physical_eig(post, pos, t)
            score = g / t.cost
            if best is None or score > best.eig_per_cost:
                best = PhysicalRecommendation(owner, t, g, score)
    return best
