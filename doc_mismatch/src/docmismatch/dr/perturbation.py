"""Zone-to-box identification from a setpoint-perturbation campaign (PREREGISTRATION_DR.md Addendum 13). numpy only; no fitting.

Every zone m was driven with its own pseudo-random setpoint pattern u_m(t) (the LOGGED setpoint is the input). Candidate box o is scored by how strongly its
actuator signals follow u_m:  S(m, o) = max over signals |corr(u_m, signal_o)|;  predicted box = argmax_o S(m, o).
"""

from __future__ import annotations

import numpy as np

SIGNALS = ("flow", "t_dis")
NOISE = {"none": None, "legacy": dict(flow=("mul", 0.02), t_dis=("add", 0.25), reheat=("mul", 0.02)),
         "harsh": dict(flow=("mul", 0.10), t_dis=("add", 1.0), reheat=("mul", 0.10))}   # reheat (Addendum 15 signal-set sweep) gets flow's multiplicative noise


def make_codes(n_zones: int, n_blocks: int, seed: int, dropout: float = 0.0) -> np.ndarray:
    """(n_zones, n_blocks) independent +-1 campaign codes. With `dropout` > 0 (Addendum 15), each zone-block independently ignores the campaign with that probability
    (code 0 = the zone sits at its base setpoint, a crude BAS / occupant override). The dropout mask comes from a SEPARATE stream and is applied after the codes are
    drawn, so the +-1 codes are identical to those of the dropout-free campaign with the same seed, and dropout = 0 is bit-identical to the original generator."""
    codes = np.random.default_rng(seed).choice([-1, 1], size=(n_zones, n_blocks)).astype(int)
    if dropout > 0:
        keep = np.random.default_rng([seed, 991]).random((n_zones, n_blocks)) >= dropout
        codes = codes * keep
    return codes


def corr_matrix(U: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """(M, O) Pearson correlation of every input row of U (M, T) with every response row of Y (O, T); zero-variance rows give 0."""
    Uc = U - U.mean(axis=1, keepdims=True)
    Yc = Y - Y.mean(axis=1, keepdims=True)
    num = Uc @ Yc.T
    den = np.sqrt((Uc ** 2).sum(axis=1))[:, None] * np.sqrt((Yc ** 2).sum(axis=1))[None, :]
    return np.divide(num, den, out=np.zeros_like(num), where=den > 1e-12)


def scores(U: np.ndarray, resp: dict[str, np.ndarray]) -> np.ndarray:
    """S[m, o] = max over the response signals of |corr(u_m, signal_o)|."""
    return np.max([np.abs(corr_matrix(U, Y)) for Y in resp.values()], axis=0)


def rank1(S: np.ndarray, truth: np.ndarray) -> float:
    """Mean over zones of P(argmax_o S[m, o] == truth[m]); exact ties share the credit equally (expected value under random tie-breaking)."""
    hit = []
    for m in range(S.shape[0]):
        tied = np.isclose(S[m], S[m].max(), atol=1e-12)
        hit.append(tied[truth[m]] / tied.sum())
    return float(np.mean(hit))


def add_noise(Y: dict[str, np.ndarray], level: str, rng: np.random.Generator) -> dict[str, np.ndarray]:
    spec = NOISE[level]
    if spec is None:
        return Y
    out = {}
    for sig, y in Y.items():
        kind, sd = spec[sig]
        out[sig] = y * rng.normal(1.0, sd, y.shape) if kind == "mul" else y + rng.normal(0.0, sd, y.shape)
    return out


def campaign_arrays(ev: dict, zones: list[str], vavs: list[str], pre: int, signals: tuple = SIGNALS) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """(U (M, T) logged setpoints, {signal: (O, T)}) restricted to the campaign hours (drops the `pre` undithered warm-up hours). `signals` = the box signals the building logs."""
    U = np.stack([ev[f"{z}|sp_cool"][pre:] for z in zones])
    Y = {s: np.stack([ev[f"{v}|{s}"][pre:] for v in vavs]) for s in signals}
    return U, Y


def sweep(U: np.ndarray, Y: dict[str, np.ndarray], truth: np.ndarray, lengths: list[int], level: str, n_draws: int, seed: int) -> dict[int, float]:
    """rank-1 accuracy for each campaign length L (first L hours), averaged over `n_draws` independent noise draws."""
    rng = np.random.default_rng(seed)
    acc = {L: [] for L in lengths}
    for _ in range(1 if NOISE[level] is None else n_draws):
        Yn = add_noise(Y, level, rng)
        for L in lengths:
            acc[L].append(rank1(scores(U[:, :L], {k: v[:, :L] for k, v in Yn.items()}), truth))
    return {L: float(np.mean(v)) for L, v in acc.items()}
