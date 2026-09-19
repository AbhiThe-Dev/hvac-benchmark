"""Structured `feeds` belief for terminal-unit / zone targets.

Candidate parents of the same target are coupled through a cardinality
prior `exp(-lambda*(k-1)**2)` over `k`, the number of parents simultaneously
active (peaked at exactly one parent by default, but zero or several are
both permitted). Marginals, joint entropy, and expected information gain
are all computed exactly through a cardinality dynamic program in O(m^2)
time (m = number of candidate parents for one target) -- no enumeration of
the 2^m assignment space is needed for production use. A brute-force
enumeration path is kept only as an exactness cross-check for tests on tiny
groups.

The key property that makes this tractable: because each test's noisy
observation is a direct query of one specific edge, its likelihood factors
through that edge's own latent state only. Sequential Bayesian updates to a
single edge's *independent* posterior therefore commute with the joint
cardinality-coupled prior -- updating edge i's independent posterior via
`bayes.update` and re-deriving the joint from the updated per-edge
posteriors gives the exact structured joint posterior. This lets every
policy in the structured experiment reuse the same per-edge update logic
used in the independent-edge experiment, isolating *selection* differences
from *inference* differences as required by the plan.

Derivation of the O(m^2) entropy formula (verified against brute-force
enumeration in tests): for x in {0,1}^m,

    P(x) = w(k(x)) * prod_i q_i^x_i (1-q_i)^(1-x_i) / Z,   k(x) = sum_i x_i

so log P(x) = log w(k(x)) - log Z + sum_i [x_i log q_i + (1-x_i) log(1-q_i)].
Taking -E[...] over x and using linearity of expectation on the sum (each
term depends on a single x_i, so E[x_i log q_i + ...] = m_i log q_i + ...
where m_i is that edge's marginal):

    H(X) = -E[log w(K)] + log Z - sum_i [m_i log q_i + (1-m_i) log(1-q_i)]

Both E[log w(K)] (via the cardinality distribution P(K=k) = dp[k]*w(k)/Z)
and log Z are O(m) once the O(m^2) cardinality DP and leave-one-out
marginals are in hand.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .bayes import update as bayes_update

ENUMERATION_CAP_DEFAULT = 20
_EPS = 1e-300


def cardinality_weight(k: np.ndarray | int, lam: float) -> np.ndarray | float:
    return np.exp(-lam * (np.asarray(k, dtype=float) - 1) ** 2)


def cardinality_dp(qs: np.ndarray) -> np.ndarray:
    """dp[k] = P(exactly k of the independent Bernoulli(q_i) are 1), ignoring
    the cardinality reweighting -- a standard product-of-Bernoullis
    convolution, O(m^2) for m edges."""
    m = len(qs)
    dp = np.zeros(m + 1)
    dp[0] = 1.0
    for q in qs:
        shifted = np.zeros(m + 1)
        shifted[1:] = dp[:-1]
        dp = dp * (1 - q) + shifted * q
    return dp


@dataclass(frozen=True)
class StructuredBelief:
    """Per-target structured belief over a fixed list of candidate parent
    edges, indexed 0..m-1 in a caller-chosen stable order."""

    qs: tuple[float, ...]  # current independent posterior per edge
    lam: float
    enumeration_cap: int = ENUMERATION_CAP_DEFAULT

    def with_observation(self, edge_index: int, observed: bool, fp_rate: float, fn_rate: float) -> "StructuredBelief":
        new_qs = list(self.qs)
        new_qs[edge_index] = bayes_update(new_qs[edge_index], observed, fp_rate, fn_rate)
        return StructuredBelief(tuple(new_qs), self.lam, self.enumeration_cap)

    def _dp_and_marginals(self) -> tuple[np.ndarray, np.ndarray, float, np.ndarray]:
        """Returns (dp, k_weights, Z, marginals) computed once and shared by
        `marginals()` and `joint_entropy()`."""
        qs = np.asarray(self.qs)
        m = len(qs)
        dp = cardinality_dp(qs)
        k = np.arange(m + 1)
        w = cardinality_weight(k, self.lam)
        z = float(np.sum(dp * w))

        marginals = np.zeros(m)
        for j in range(m):
            q_j = qs[j]
            others = np.delete(qs, j)
            dp_minus_j = cardinality_dp(others)
            k_prime = np.arange(len(dp_minus_j))
            w_k = cardinality_weight(k_prime, self.lam)
            w_k1 = cardinality_weight(k_prime + 1, self.lam)
            num1 = q_j * np.sum(dp_minus_j * w_k1)
            num0 = (1 - q_j) * np.sum(dp_minus_j * w_k)
            denom = num0 + num1
            marginals[j] = num1 / denom if denom > 0 else q_j
        return dp, w, z, marginals

    def marginals(self) -> np.ndarray:
        """Exact per-edge marginal P(x_i=1) via leave-one-out cardinality DP."""
        if len(self.qs) == 0:
            return np.zeros(0)
        _, _, _, marginals = self._dp_and_marginals()
        return marginals

    def joint_entropy(self) -> float:
        """O(m^2) exact joint Shannon entropy (see module docstring)."""
        qs = np.asarray(self.qs)
        m = len(qs)
        if m == 0:
            return 0.0
        dp, w, z, marginals = self._dp_and_marginals()
        if z <= 0:
            return 0.0
        pk = dp * w / z
        nonzero_w = w > 0
        e_log_w = float(np.sum(pk[nonzero_w] * np.log2(w[nonzero_w])))
        log_z = float(np.log2(z))

        cross_term = 0.0
        for m_i, q_i in zip(marginals, qs):
            if q_i > 0:
                cross_term += m_i * np.log2(q_i)
            if q_i < 1:
                cross_term += (1 - m_i) * np.log2(1 - q_i)

        h = -e_log_w + log_z - cross_term
        return max(0.0, h)

    def expected_information_gain(self, edge_index: int, fp_rate: float, fn_rate: float) -> float:
        """Exact reduction in joint entropy from one more test of edge
        `edge_index`, accounting for how that observation shifts belief
        about every coupled sibling parent, not just the tested edge."""
        h0 = self.joint_entropy()
        marginal_j = self.marginals()[edge_index]
        p_obs_true = marginal_j * (1 - fn_rate) + (1 - marginal_j) * fp_rate
        p_obs_false = 1 - p_obs_true

        belief_true = self.with_observation(edge_index, True, fp_rate, fn_rate)
        belief_false = self.with_observation(edge_index, False, fp_rate, fn_rate)

        expected_remaining = p_obs_true * belief_true.joint_entropy() + p_obs_false * belief_false.joint_entropy()
        return h0 - expected_remaining

    def joint_entropy_by_enumeration(self) -> float:
        """Brute-force 2^m cross-check, used only in tests on tiny groups."""
        qs = np.asarray(self.qs)
        m = len(qs)
        if m == 0:
            return 0.0
        if m > self.enumeration_cap:
            raise ValueError(f"enumeration cap exceeded: {m} > {self.enumeration_cap}")
        idx = np.arange(2**m)
        bits = (idx[:, None] >> np.arange(m)[None, :]) & 1
        per_bit = np.where(bits == 1, qs[None, :], 1 - qs[None, :])
        unnorm = per_bit.prod(axis=1)
        k = bits.sum(axis=1)
        w = cardinality_weight(k, self.lam)
        unnorm = unnorm * w
        z = unnorm.sum()
        probs = unnorm / z if z > 0 else unnorm
        nonzero = probs[probs > 0]
        return float(-np.sum(nonzero * np.log2(nonzero)))


def independent_marginal_check(qs: tuple[float, ...]) -> np.ndarray:
    """At lambda=0 the cardinality weight is uniform over k, so the
    structured marginal must equal the raw independent posterior. Used only
    in tests as a cross-check."""
    return np.asarray(qs)
