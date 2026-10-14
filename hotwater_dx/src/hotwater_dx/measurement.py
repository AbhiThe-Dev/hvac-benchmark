"""Measurement-error models: what a technician's instrument reports for a true value.

Every error term is ANALYST unless a source is named. These turn "the model says the return is 98 F" into "the clamp reads 95-101 F", which is what
decides whether a check separates a cause from normal. A reading error includes the per-visit instrument bias, so repeated draws are independent visits.
"""
from __future__ import annotations

import numpy as np

NOISE = {"scale": 1.0}   # stress tests scale every instrument error; 1.0 reproduces the frozen matrix

# tool -> description. Pitfalls from research_notes/.../check_catalogue.md section 3 (bare-copper IR, contact quality, stagnation).
TEMP_TOOLS = {
    "probe": "immersion or well-seated contact probe",
    "clamp": "pipe-clamp thermocouple: +-4 F as shipped, ~+-1 F after field calibration (SNIPPET FIELDPIECE); contact loss reads toward ambient",
    "bas": "BAS or controller sensor on the pipe, calibrated",
    "ir": "infrared thermometer on bare copper: low emissivity reads toward the surroundings",
    "logger": "clip-on logger (HOBO-class, ~+-0.2 C)",
}


def _instrument(tool: str, rng: np.random.Generator):
    """Per-visit instrument state: contact loss kappa and bias (clamp), emissivity (IR). Shared by readings taken with the same instrument."""
    if tool == "clamp":
        return rng.uniform(0.02, 0.12), rng.normal(0.0, 1.5 * NOISE["scale"])
    if tool == "ir":
        return rng.uniform(0.05, 0.30), 0.0
    return 0.0, 0.0


def _read(T: float, tool: str, t_amb: float, inst, rng: np.random.Generator) -> float:
    a, b = inst
    if tool == "probe":
        return T + rng.normal(0.0, 0.5 * NOISE["scale"])
    if tool == "clamp":
        return T - a * (T - t_amb) + b + rng.normal(0.0, 0.5 * NOISE["scale"])
    if tool == "bas":
        return T + rng.normal(0.0, 0.4 * NOISE["scale"])
    if tool == "ir":
        return a * T + (1.0 - a) * t_amb + rng.normal(0.0, 1.0 * NOISE["scale"])
    if tool == "logger":
        return T + rng.normal(0.0, 0.35 * NOISE["scale"])
    raise ValueError(tool)


def temp(T: float, tool: str, t_amb: float, rng: np.random.Generator) -> float:
    return _read(T, tool, t_amb, _instrument(tool, rng), rng)


def temp_pair(T1: float, T2: float, tool: str, t_amb: float, rng: np.random.Generator):
    """Two readings with the same instrument in one visit: contact loss and bias are shared, so a *difference* is less noisy than two independent readings."""
    inst = _instrument(tool, rng)
    return _read(T1, tool, t_amb, inst, rng), _read(T2, tool, t_amb, inst, rng)


def gauge(p: float, rng: np.random.Generator, sigma: float = 1.0) -> float:
    """Pressure gauge, ~+-2% of a 0-100 psi scale."""
    return p + rng.normal(0.0, sigma * NOISE["scale"])


def amps(ratio: float, rng: np.random.Generator) -> float:
    return ratio * (1.0 + rng.normal(0.0, 0.03 * NOISE["scale"])) + rng.normal(0.0, 0.02 * NOISE["scale"])


def stopwatch(t_s: float, rng: np.random.Generator) -> float:
    return t_s + rng.normal(0.0, 2.0 * NOISE["scale"]) + rng.normal(0.0, 3.0 * NOISE["scale"])   # reaction time + judging when the water is hot


def flip(value: float, rng: np.random.Generator, p: float = 0.1) -> float:
    """A readout or observation that is misread with probability p (binary checks)."""
    return 1.0 - value if rng.random() < p else value
