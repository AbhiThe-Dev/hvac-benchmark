"""Physics sanity tests for the steady-state loop model."""
import math

import numpy as np
import pytest

from hotwater_dx.params import nominal_design
from hotwater_dx.plant import build_plant
from hotwater_dx.sampling import design_matrix
from hotwater_dx.solve import hydraulics, solve


def _plants(n=60, seed=5):
    return [build_plant(d, np.random.default_rng(100 + k)) for k, d in enumerate(design_matrix(n, seed))]


def test_converges_and_balances_over_random_plants():
    for P in _plants():
        for load in (0.0, 1.0):
            s = solve(P, load, True)
            assert s.converged
            assert s.energy_residual < 1e-3, s.energy_residual          # enthalpy in = pipe losses + draws + return flux
            if not P.thermal:
                assert s.flow_residual < 1e-6                           # parallel risers share one head


def test_mass_balance(plant):
    s = solve(plant, 1.0, True)
    assert s.Qs == pytest.approx(sum(s.q) + s.Qd)                       # nothing psi-leaky in a healthy plant


def test_pump_operating_point_lies_on_both_curves(plant):
    s = solve(plant, 0.0, True)
    qd = plant.design_total
    Hd = plant.h_design * plant.pump_oversize
    H0, b = 1.25 * Hd, 0.25 * Hd / (qd * qd)
    assert s.head == pytest.approx(H0 - b * s.Qp ** 2)                  # on the pump curve
    from hotwater_dx.solve import _riser_k
    S = sum(1 / math.sqrt(_riser_k(plant, i, s.T_ret_i[i])) for i in range(plant.n))
    sys_head = plant.k_sm * (s.Qp + s.Qd) ** 2 + plant.k_rm * s.Qp ** 2 + (s.Qp / S) ** 2
    assert s.head == pytest.approx(sys_head, rel=0.02)                   # on the system curve (thermal valves settle to within damping)


def test_closing_a_balancing_valve_starves_that_riser(plant):
    base = solve(plant, 0.0, True)
    Q = plant.copy()
    Q.thermal = False
    Q.cv_mult[3] = 0.1
    s = solve(Q, 0.0, True)
    assert s.q[3] < 0.2 * base.q[3]
    assert all(s.q[i] >= 0.95 * base.q[i] for i in range(3))             # others keep or gain flow
    assert min(s.T_ret_i) < base.T_ret - 5.0                              # and the starved riser base is cold


def test_zero_loss_gives_uniform_temperature(plant):
    Q = plant.copy()
    Q.u_eff = 1e-9
    s = solve(Q, 0.0, True)
    assert max(s.T_E) - min(s.T_E) < 0.01
    assert s.T_ret == pytest.approx(s.Ts, abs=0.05)


def test_total_loss_goes_to_ambient(plant):
    Q = plant.copy()
    Q.u_eff = 50.0
    s = solve(Q, 0.0, True)
    assert abs(min(s.T_E) - Q.t_amb) < 1.0


def test_dead_pump_stagnates_and_cools_exponentially(plant):
    Q = plant.copy()
    Q.pump_head_mult = 0.0
    a, b = solve(Q, 0.0, True, 1.0), solve(Q, 0.0, True, 2.0)
    assert all(x == 0.0 for x in a.q)
    assert b.T_ret < a.T_ret                                              # keeps cooling
    amb, t0 = Q.t_amb, min(Q.t_set_tmv + Q.tmv_drift, a.T_hot_in)
    assert (b.T_ret - amb) == pytest.approx((a.T_ret - amb) ** 2 / (t0 - amb), rel=1e-6)   # exp(-2t) = exp(-t)^2


def test_lower_heater_setpoint_never_raises_temperatures(plant):
    hi = solve(plant, 1.0, True)
    Q = plant.copy()
    Q.t_set_heater -= 20
    lo = solve(Q, 1.0, True)
    assert lo.Ts <= hi.Ts + 1e-9 and lo.T_ret <= hi.T_ret + 1e-9


def test_capacity_loss_hurts_only_under_load(plant):
    Q = plant.copy()
    Q.cap_eff = 0.2
    idle, peak = solve(Q, 0.0, True), solve(Q, 1.0, True)
    base_idle, base_peak = solve(plant, 0.0, True), solve(plant, 1.0, True)
    assert abs(idle.Ts - base_idle.Ts) < 1.0                              # idle load is tiny
    assert peak.Ts < base_peak.Ts - 5.0


def test_crossover_cools_the_return_and_raises_heat_demand(plant):
    base = solve(plant, 0.0, True)
    Q = plant.copy()
    Q.g_x[1] = 0.15
    s = solve(Q, 0.0, True)
    assert s.T_ret < base.T_ret - 1.0
    assert sum(s.c) > 0.1


def test_dead_pump_hydraulics_returns_zero(plant):
    Q = plant.copy()
    Q.pump_head_mult = 0.0
    q, head, tot = hydraulics(Q, 0.0, [100.0] * Q.n)
    assert tot == 0.0 and all(x == 0.0 for x in q)
