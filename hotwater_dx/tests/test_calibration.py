"""Consistency of the model with published anchors (research_notes/.../quantitative_evidence.md). 'Consistent with', never 'validated'."""
import math

import numpy as np
import pytest

from hotwater_dx.plant import CP_PER_FT, build_plant
from hotwater_dx.sampling import design_matrix
from hotwater_dx.solve import solve

APARTMENTS = 32     # 4 risers x ~8 apartments: an assumption used only to express loss per apartment


def _healthy(n=150):
    return [build_plant(d, np.random.default_rng(300 + k)) for k, d in enumerate(design_matrix(n, 11))]


def test_loop_loss_per_apartment_in_the_etcc_band():
    # SOURCE ETCC: 24.1-99.9 W per apartment, mean 62.5
    w = []
    for P in _healthy():
        s = solve(P, 0.0, True)
        w.append(500.0 * s.Qs * (s.Ts - s.T_cm) * 0.29307 / APARTMENTS)
    w = np.array(w)
    # The model runs high against the ETCC mean (62.5 W): median ~85 W. We assert only what we can defend: most plants inside the measured band and the
    # median inside it too. model_limits.md reports the high bias; it is not tuned away because the apartment count per riser is itself an assumption.
    assert np.mean((w >= 24) & (w <= 100)) >= 0.65
    assert 40 <= np.median(w) <= 100


def test_balanced_riser_tops_within_the_pge_spread():
    # SOURCE PGE24: balanced risers within 2-5 F of each other
    spread = [max(s.T_E) - min(s.T_E) for s in (solve(P, 0.0, True) for P in _healthy())]
    assert np.percentile(spread, 95) <= 5.0
    assert np.median(spread) >= 0.5


def test_riser_below_a_tenth_gpm_cannot_balance(plant):
    # SOURCE PGE24: below 0.1 gpm/riser none could balance
    Q = plant.copy()
    Q.thermal = False
    Q.cv_mult[2] = 0.05
    s = solve(Q, 0.0, True)
    assert s.q[2] < 0.1
    assert max(s.T_ret_i) - min(s.T_ret_i) > 5.0


def test_stagnation_cooldown_matches_lab_and_trade_figures():
    tau_bare = CP_PER_FT / 0.5                       # bare 1/2-3/4 in copper, ~0.5 Btu/h/ft/F (PHYSICS)
    t_hiller = tau_bare * math.log((135 - 68) / (105 - 68)) * 60
    assert t_hiller < 25.0                           # SNIPPET HILLER: 135 -> 105 F in under 25 min
    t_bare = tau_bare * math.log((140 - 68) / (122 - 68)) * 60
    assert 5.0 <= t_bare <= 15.0                     # SOURCE BED15: bare pipe 60 -> 50 C within ~10 min (lab)
    tau_ins = CP_PER_FT / 0.162                      # insulated: nominal u_ins * ua_mult
    t_ins = tau_ins * math.log((140 - 68) / (122 - 68)) * 60
    assert 15.0 <= t_ins <= 45.0                     # SOURCE BED15: insulated pipe 60 -> 50 C within ~30 min (lab), +-50%


def test_principal_return_masks_a_starved_subordinate_riser(plant):
    # SOURCE BED15: a fine principal return can hide starved subordinate loops
    base = solve(plant, 0.0, True)
    Q = plant.copy()
    Q.thermal = False
    Q.cv_mult[3] = 0.05
    s = solve(Q, 0.0, True)
    assert abs(s.T_ret - base.T_ret) < 6.0
    assert min(s.T_ret_i) < s.T_ret - 8.0


def test_design_flow_identity():
    # SOURCE CALEFFI: Btu/h = 500 * gpm * dT, so commissioned flow reproduces the design dT
    P = _healthy(1)[0]
    s = solve(P, 0.0, True)
    assert 3.0 <= s.Ts - s.T_ret <= 14.0
